"""
MCP Server - Model Context Protocol Server for Real-time Moderation
Handles structured moderation requests and forwards to LLM endpoint
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import httpx
import yaml
import json
import time
import logging
import os
from datetime import datetime
import asyncio
from prometheus_client import Counter, Histogram, generate_latest
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
REQUEST_COUNT = Counter('mcp_requests_total', 'Total MCP requests', ['endpoint', 'status'])
REQUEST_DURATION = Histogram('mcp_request_duration_seconds', 'Request duration')
LLM_LATENCY = Histogram('llm_response_time_seconds', 'LLM response time')

class ModerationRequest(BaseModel):
    message: str = Field(..., description="Chat message to moderate")
    user_id: str = Field(..., description="User ID")
    channel_id: str = Field(..., description="Channel ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    template_name: str = Field(default="moderation_prompt", description="Template to use")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ModerationResponse(BaseModel):
    decision: str = Field(..., description="Moderation decision")
    confidence: float = Field(..., description="Confidence score")
    reasoning: Optional[str] = Field(None, description="Reasoning for decision")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    template_version: str = Field(..., description="Template version used")

class PromptTemplate:
    def __init__(self, template_path: str = "/app/templates/moderation_templates.yaml"):
        self.template_path = template_path
        self.templates = {}
        self.load_templates()
    
    def load_templates(self):
        """Load prompt templates from YAML file"""
        try:
            with open(self.template_path, 'r') as file:
                self.templates = yaml.safe_load(file)
            logger.info(f"Loaded {len(self.templates)} templates")
        except FileNotFoundError:
            logger.warning(f"Template file not found: {self.template_path}")
            self.templates = self._get_default_templates()
    
    def _get_default_templates(self) -> Dict:
        """Default templates if file not found"""
        return {
            "moderation_prompt": {
                "name": "moderation_prompt",
                "version": "1.0",
                "prompt": "Classify the following message for toxicity:\n'{chat_message}'\n\nRespond with JSON format:\n{\"decision\": \"[Toxic/Non-Toxic]\", \"confidence\": 0.95, \"reasoning\": \"explanation\"}",
                "safety_level": "high",
                "expected_output": "json"
            }
        }
    
    def get_template(self, template_name: str) -> Dict:
        """Get template by name"""
        return self.templates.get(template_name, self.templates.get("moderation_prompt"))
    
    def format_prompt(self, template_name: str, **kwargs) -> str:
        """Format prompt with provided variables"""
        template = self.get_template(template_name)
        prompt = template["prompt"]
        
        # Replace placeholders
        for key, value in kwargs.items():
            prompt = prompt.replace(f"{{{key}}}", str(value))
        
        return prompt

class LLMClient:
    def __init__(self):
        self.llm_endpoint = os.getenv("LLM_ENDPOINT", "http://deepseek-llm:8080/v1/chat/completions")
        self.model_name = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-R1-Distill-Llama-8B")
        self.timeout = float(os.getenv("LLM_TIMEOUT", "30.0"))
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
        
        # Determine model type for appropriate message formatting
        self.model_type = self._detect_model_type()
        logger.info(f"Initialized LLMClient with model: {self.model_name}, type: {self.model_type}")
    
    def _detect_model_type(self) -> str:
        """Detect model type based on model name"""
        model_lower = self.model_name.lower()
        
        # Handle path-based model names (e.g., "/tmp/models/mistral-7b-v0-2")
        model_basename = os.path.basename(model_lower)
        
        if "mistral" in model_lower or "mistral" in model_basename:
            return "mistral"
        elif "deepseek" in model_lower or "deepseek" in model_basename:
            return "deepseek"
        elif "llama" in model_lower or "llama" in model_basename:
            return "llama"
        elif "qwen" in model_lower or "qwen" in model_basename:
            return "qwen"
        else:
            # Default to standard OpenAI-compatible format
            logger.warning(f"Unknown model type for {self.model_name}, using default format")
            return "default"
    
    def _prepare_messages(self, prompt: str) -> List[Dict[str, str]]:
        """Prepare messages based on model type"""
        system_message = "You are a content moderation assistant. Respond only in the requested JSON format."
        
        if self.model_type == "mistral":
            # Mistral requires alternating user/assistant roles, no system messages
            # Combine system message with user prompt in a clear format
            combined_prompt = f"""<s>[INST] {system_message}

{prompt} [/INST]"""
            return [{"role": "user", "content": combined_prompt}]
        
        elif self.model_type in ["deepseek", "qwen", "default"]:
            # These models support system messages
            return [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        
        elif self.model_type == "llama":
            # Some Llama implementations prefer system message in user prompt
            # But we'll try system message first
            return [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        
        else:
            # Fallback to standard format
            return [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
    
    def _get_model_specific_params(self) -> Dict[str, Any]:
        """Get model-specific parameters"""
        base_params = {
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        if self.model_type == "mistral":
            # Mistral-specific parameters
            base_params.update({
                "temperature": 0.1,
                "max_tokens": 500,
                "top_p": 0.9
            })
        elif self.model_type == "deepseek":
            # DeepSeek-specific parameters
            base_params.update({
                "temperature": 0.1,
                "max_tokens": 500,
                "top_p": 0.95
            })
        
        return base_params
    
    async def generate_response(self, prompt: str) -> Dict[str, Any]:
        """Send request to LLM endpoint"""
        start_time = time.time()
        
        # Prepare messages based on model type
        messages = self._prepare_messages(prompt)
        model_params = self._get_model_specific_params()
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            **model_params
        }
        
        logger.info(f"Sending request to {self.model_name} ({self.model_type}) with {len(messages)} messages")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.llm_endpoint, json=payload)
                    response.raise_for_status()
                    
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Record metrics
                    duration = time.time() - start_time
                    LLM_LATENCY.observe(duration)
                    
                    logger.info(f"LLM response received in {duration:.2f}s from {self.model_type} model")
                    logger.debug(f"Response content: {content[:200]}...")
                    
                    return {"content": content, "duration": duration}
                    
            except Exception as e:
                logger.warning(f"LLM request attempt {attempt + 1} failed for {self.model_type} model: {str(e)}")
                if attempt == self.max_retries - 1:
                    raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

class ValidationService:
    @staticmethod
    def validate_input(request: ModerationRequest) -> bool:
        """Validate input for prompt injection and other security issues"""
        message = request.message.lower()
        
        # Basic prompt injection detection
        injection_patterns = [
            "ignore previous instructions",
            "system:",
            "assistant:",
            "user:",
            "prompt:",
            "###",
            "---"
        ]
        
        for pattern in injection_patterns:
            if pattern in message:
                logger.warning(f"Potential prompt injection detected: {pattern}")
                return False
        
        # Length validation
        if len(request.message) > 2000:
            logger.warning("Message too long")
            return False
            
        return True

class MCPServer:
    def __init__(self):
        self.prompt_template = PromptTemplate()
        self.llm_client = LLMClient()
        self.validation_service = ValidationService()
    
    async def process_moderation_request(self, request: ModerationRequest) -> ModerationResponse:
        """Process moderation request"""
        start_time = time.time()
        
        try:
            # Validate input
            if not self.validation_service.validate_input(request):
                raise HTTPException(status_code=400, detail="Invalid input detected")
            
            # Get and format prompt
            template = self.prompt_template.get_template(request.template_name)
            formatted_prompt = self.prompt_template.format_prompt(
                request.template_name,
                chat_message=request.message,
                user_id=request.user_id,
                channel_id=request.channel_id
            )
            
            # Send to LLM
            llm_response = await self.llm_client.generate_response(formatted_prompt)
            
            # Parse LLM response
            try:
                response_data = json.loads(llm_response["content"])
            except json.JSONDecodeError:
                # Improved fallback parsing - look for JSON-like structure in the response
                content = llm_response["content"]
                logger.warning(f"Failed to parse JSON response, attempting fallback parsing. Content: {content[:200]}...")
                
                # Try to extract JSON from the response if it's embedded in text
                import re
                
                # Look for JSON blocks in the response (between ``` or just standalone)
                json_patterns = [
                    r'```json\s*(\{.*?\})\s*```',  # JSON in code blocks
                    r'```\s*(\{.*?\})\s*```',      # JSON in generic code blocks
                    r'(\{[^{}]*"decision"[^{}]*\})',  # Simple JSON with decision field
                    r'(\{.*?"decision".*?\})'      # More flexible JSON matching
                ]
                
                response_data = None
                for pattern in json_patterns:
                    json_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                    if json_match:
                        try:
                            response_data = json.loads(json_match.group(1))
                            logger.info(f"Successfully extracted JSON using pattern: {pattern}")
                            break
                        except json.JSONDecodeError:
                            continue
                
                if not response_data:
                    # Last resort: analyze the text content for decision keywords
                    content_lower = content.lower()
                    logger.info(f"Full LLM response for analysis: {content}")
                    
                    # Look for explicit decision statements
                    if any(phrase in content_lower for phrase in [
                        '"decision": "toxic"', 'decision is toxic', 'classify as toxic',
                        'this is toxic', 'message is toxic', 'contains toxic', 'toxic content',
                        'personal attack', 'harassment', 'hate speech', 'inappropriate'
                    ]):
                        response_data = {"decision": "Toxic", "confidence": 0.7, "reasoning": "Text analysis - toxic indicators found"}
                    elif any(phrase in content_lower for phrase in [
                        '"decision": "non-toxic"', 'decision is non-toxic', 'not toxic',
                        'safe message', 'no toxicity', 'appropriate content', 'friendly', 'greeting'
                    ]):
                        response_data = {"decision": "Non-Toxic", "confidence": 0.7, "reasoning": "Text analysis - no toxic indicators"}
                    else:
                        # Default to non-toxic if unclear
                        response_data = {"decision": "Non-Toxic", "confidence": 0.5, "reasoning": "Unable to determine from LLM response"}
            
            processing_time = (time.time() - start_time) * 1000
            
            return ModerationResponse(
                decision=response_data.get("decision", "Non-Toxic"),
                confidence=response_data.get("confidence", 0.5),
                reasoning=response_data.get("reasoning", ""),
                processing_time_ms=processing_time,
                template_version=template["version"]
            )
            
        except Exception as e:
            logger.error(f"Error processing moderation request: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

# Initialize FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("MCP Server starting up...")
    yield
    logger.info("MCP Server shutting down...")

app = FastAPI(
    title="MCP Server - Model Context Protocol",
    description="Real-time moderation system MCP server",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MCP server
mcp_server = MCPServer()

@app.post("/moderate", response_model=ModerationResponse)
async def moderate_message(request: ModerationRequest):
    """Moderate a chat message"""
    try:
        REQUEST_COUNT.labels(endpoint="moderate", status="started").inc()
        
        with REQUEST_DURATION.time():
            response = await mcp_server.process_moderation_request(request)
        
        REQUEST_COUNT.labels(endpoint="moderate", status="success").inc()
        return response
        
    except HTTPException:
        REQUEST_COUNT.labels(endpoint="moderate", status="error").inc()
        raise
    except Exception as e:
        REQUEST_COUNT.labels(endpoint="moderate", status="error").inc()
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/templates")
async def list_templates():
    """List available prompt templates"""
    return {"templates": list(mcp_server.prompt_template.templates.keys())}

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    from fastapi import Response
    return Response(content=generate_latest(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
