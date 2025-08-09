"""
Chat Simulator - Simulates streaming chat environment with WebUI
Generates realistic chat messages and sends them to the moderation pipeline
Includes web interface for interactive chat simulation
"""

import asyncio
import json
import random
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import httpx
import os
from dataclasses import dataclass, asdict
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
MESSAGES_TOTAL = Counter('chat_messages_total', 'Total number of chat messages processed', ['message_type', 'decision'])
MESSAGE_PROCESSING_TIME = Histogram('chat_message_processing_seconds', 'Time spent processing chat messages')
ACTIVE_CONNECTIONS = Gauge('chat_active_websocket_connections', 'Number of active WebSocket connections')
MODERATION_REQUESTS = Counter('chat_moderation_requests_total', 'Total moderation requests', ['status'])
FILTER_REQUESTS = Counter('chat_filter_requests_total', 'Total filter requests', ['status'])

@dataclass
class ChatMessage:
    user_id: str
    username: str
    channel_id: str
    message: str
    timestamp: datetime
    message_type: str = "text"  # text, audio, system
    metadata: Dict[str, Any] = None
    
    def to_dict(self):
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

class UserMessage(BaseModel):
    message: str
    user_id: str = "user_web"
    username: str = "WebUser"
    channel_id: str = "web-chat"
    metadata: Dict[str, Any] = None

class MessageGenerator:
    def __init__(self, sample_data_path: str = "/app/data/sample_messages.json"):
        self.sample_data_path = sample_data_path
        self.sample_messages = self.load_sample_messages()
        self.user_pool = self.generate_user_pool()
        self.channels = ["general", "gaming", "tech-talk", "random", "support"]
        
    def load_sample_messages(self) -> Dict[str, List[str]]:
        """Load sample messages from JSON file"""
        try:
            with open(self.sample_data_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"Sample data file not found: {self.sample_data_path}")
            return self.get_default_messages()
    
    def get_default_messages(self) -> Dict[str, List[str]]:
        """Default messages if file not found"""
        return {
            "normal": [
                "Hey everyone! How's it going?",
                "Just finished a great game session",
                "Anyone know about the new update?",
                "Thanks for the help earlier!",
                "Good morning chat!",
                "What's everyone up to today?",
                "That was an amazing stream!",
                "Can someone help me with this issue?",
                "Love this community ❤️",
                "See you all later!",
                "Great discussion today!",
                "Looking forward to the next event",
                "This feature is really useful",
                "Thanks for sharing that link",
                "Hope everyone has a good day!"
            ],
            "toxic": [
                "You're absolutely terrible at this game",
                "This is the worst stream ever",
                "Nobody cares about your opinion",
                "Stop being such a noob",
                "This chat is full of idiots",
                "You should just quit playing",
                "What a waste of time this is",
                "Everyone here is so stupid",
                "This content is garbage",
                "You're all pathetic losers"
            ],
            "spam": [
                "🎉 FREE MONEY HERE: bit.ly/fake-link 🎉",
                "CLICK HERE FOR AMAZING DEALS!!!",
                "💰💰💰 CRYPTO INVESTMENT OPPORTUNITY 💰💰💰",
                "Follow my channel for exclusive content!",
                "BUY MY COURSE FOR ONLY $99.99",
                "🚀 MAKE $1000 A DAY FROM HOME 🚀",
                "LIMITED TIME OFFER - ACT NOW!!!",
                "FREE GIFT CARDS - CLICK HERE NOW",
                "EARN MONEY FAST WITH THIS TRICK",
                "SUBSCRIBE TO MY CHANNEL FOR PRIZES"
            ],
            "pii": [
                "My email is john.doe@email.com if you want to contact me",
                "Call me at 555-123-4567",
                "I live at 123 Main Street, Anytown USA",
                "My credit card number is 4532-1234-5678-9012",
                "You can reach me at jane.smith@company.com",
                "My phone is (555) 987-6543",
                "I'm at 456 Oak Avenue, Springfield",
                "My SSN is 123-45-6789 for verification"
            ]
        }
    
    def generate_user_pool(self) -> List[Dict[str, str]]:
        """Generate a pool of simulated users"""
        usernames = [
            "GamerPro123", "ChatMaster", "StreamFan", "TechGuru", "RandomUser",
            "NightOwl", "CoffeeAddict", "BookWorm", "MusicLover", "Traveler",
            "Foodie", "Artist", "Developer", "Student", "Teacher",
            "SportsFan", "MovieBuff", "Photographer", "Chef", "Musician"
        ]
        
        return [
            {
                "user_id": f"user_{i:04d}",
                "username": username,
                "reputation": random.choice(["new", "regular", "trusted", "moderator"]),
                "activity_level": random.choice(["low", "medium", "high"])
            }
            for i, username in enumerate(usernames)
        ]
    
    def generate_message(self, message_type: str = None) -> ChatMessage:
        """Generate a random chat message"""
        if message_type is None:
            # Weight distribution: 70% normal, 15% toxic, 10% spam, 5% pii
            message_type = random.choices(
                ["normal", "toxic", "spam", "pii"],
                weights=[70, 15, 10, 5]
            )[0]
        
        user = random.choice(self.user_pool)
        channel = random.choice(self.channels)
        message_text = random.choice(self.sample_messages[message_type])
        
        # Add some variation to messages
        if random.random() < 0.3:  # 30% chance to add emoji or variation
            variations = ["!", "?", " 😊", " 👍", " 🔥", " ❤️", " 🎮", " 💯"]
            message_text += random.choice(variations)
        
        return ChatMessage(
            user_id=user["user_id"],
            username=user["username"],
            channel_id=channel,
            message=message_text,
            timestamp=datetime.utcnow(),
            metadata={
                "reputation": user["reputation"],
                "activity_level": user["activity_level"]
            }
        )
    
    def create_user_message(self, user_message: UserMessage) -> ChatMessage:
        """Create a ChatMessage from user input"""
        return ChatMessage(
            user_id=user_message.user_id,
            username=user_message.username,
            channel_id=user_message.channel_id,
            message=user_message.message,
            timestamp=datetime.utcnow(),
            metadata=user_message.metadata or {}
        )

class ModerationClient:
    def __init__(self):
        self.mcp_endpoint = os.getenv("MCP_ENDPOINT", "http://mcp-server:8000")
        self.filter_endpoint = os.getenv("FILTER_ENDPOINT", "http://lightweight-filter:8001")
        self.timeout = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    
    async def send_to_filter(self, message: ChatMessage) -> Dict[str, Any]:
        """Send message to lightweight filter first"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.filter_endpoint}/filter",
                    json=message.to_dict()
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Filter request failed: {str(e)}")
            return {"should_process": True, "filter_decision": "pass"}
    
    async def send_to_mcp(self, message: ChatMessage) -> Dict[str, Any]:
        """Send message to MCP server for moderation"""
        try:
            payload = {
                "message": message.message,
                "user_id": message.user_id,
                "channel_id": message.channel_id,
                "timestamp": message.timestamp.isoformat(),
                "template_name": "moderation_prompt",
                "metadata": message.metadata or {}
            }
            
            timeout_config = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout_config) as client:
                response = await client.post(
                    f"{self.mcp_endpoint}/moderate",
                    json=payload
                )
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as e:
            logger.error(f"MCP request timeout: {str(e)}")
            return {"decision": "Error", "confidence": 0.0, "reasoning": f"Request timeout: {str(e)}"}
        except httpx.HTTPStatusError as e:
            logger.error(f"MCP request HTTP error: {e.response.status_code} - {e.response.text}")
            return {"decision": "Error", "confidence": 0.0, "reasoning": f"HTTP error: {e.response.status_code}"}
        except Exception as e:
            logger.error(f"MCP request failed: {type(e).__name__}: {str(e)}")
            return {"decision": "Error", "confidence": 0.0, "reasoning": f"{type(e).__name__}: {str(e)}"}

class ChatSimulator:
    def __init__(self):
        self.message_generator = MessageGenerator()
        self.moderation_client = ModerationClient()
        self.active_connections: List[WebSocket] = []
        self.simulation_active = False
        self.message_interval = float(os.getenv("MESSAGE_INTERVAL", "2.0"))  # seconds
        
    async def add_connection(self, websocket: WebSocket):
        """Add WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        ACTIVE_CONNECTIONS.set(len(self.active_connections))
        logger.info(f"New connection added. Total: {len(self.active_connections)}")
    
    def remove_connection(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            ACTIVE_CONNECTIONS.set(len(self.active_connections))
            logger.info(f"Connection removed. Total: {len(self.active_connections)}")
    
    async def broadcast_message(self, data: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.remove_connection(connection)
    
    async def process_message(self, message: ChatMessage) -> Dict[str, Any]:
        """Process a single message through the moderation pipeline"""
        start_time = time.time()
        
        # Step 1: Lightweight filter (optional)
        filter_result = await self.moderation_client.send_to_filter(message)
        FILTER_REQUESTS.labels(status="success" if filter_result else "error").inc()
        
        moderation_result = None
        if filter_result.get("should_process", True):
            # Step 2: MCP server moderation
            moderation_result = await self.moderation_client.send_to_mcp(message)
            MODERATION_REQUESTS.labels(status="success" if moderation_result.get("decision") != "Error" else "error").inc()
        
        processing_time = (time.time() - start_time) * 1000
        MESSAGE_PROCESSING_TIME.observe(processing_time / 1000)  # Convert to seconds for Prometheus
        
        # Track message metrics
        message_type = getattr(message, 'message_type', 'unknown')
        decision = moderation_result.get("decision", "unknown") if moderation_result else "filtered"
        MESSAGES_TOTAL.labels(message_type=message_type, decision=decision).inc()
        
        return {
            "type": "chat_message",
            "message": message.to_dict(),
            "filter_result": filter_result,
            "moderation_result": moderation_result,
            "processing_time_ms": processing_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def simulate_chat_stream(self):
        """Main simulation loop"""
        logger.info("Starting chat simulation...")
        self.simulation_active = True
        
        while self.simulation_active:
            try:
                # Generate message
                message = self.message_generator.generate_message()
                
                # Process message
                result = await self.process_message(message)
                
                # Broadcast to connected clients
                await self.broadcast_message(result)
                
                # Log the interaction
                moderation_result = result.get("moderation_result")
                decision = moderation_result.get('decision', 'N/A') if moderation_result else 'Filtered'
                processing_time = result.get("processing_time_ms", 0)
                
                logger.info(
                    f"Message from {message.username}: '{message.message[:50]}...' "
                    f"-> {decision} ({processing_time:.1f}ms)"
                )
                
                # Wait before next message
                await asyncio.sleep(self.message_interval)
                
            except Exception as e:
                logger.error(f"Error in simulation loop: {str(e)}")
                await asyncio.sleep(1)
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.simulation_active = False
        logger.info("Chat simulation stopped")

# FastAPI app for the simulator
app = FastAPI(
    title="Chat Simulator with WebUI", 
    version="1.0.0",
    description="Interactive chat simulator with real-time moderation and web interface"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize simulator
simulator = ChatSimulator()

# Mount static files
app.mount("/static", StaticFiles(directory="/app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """Serve the main web interface"""
    try:
        with open("/app/static/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Web interface not found</h1><p>Please ensure static files are properly mounted.</p>",
            status_code=404
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time chat simulation"""
    await simulator.add_connection(websocket)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            command = json.loads(data)
            
            if command.get("action") == "start_simulation":
                if not simulator.simulation_active:
                    asyncio.create_task(simulator.simulate_chat_stream())
                    await websocket.send_json({"type": "status", "message": "Simulation started"})
            elif command.get("action") == "stop_simulation":
                simulator.stop_simulation()
                await websocket.send_json({"type": "status", "message": "Simulation stopped"})
                
    except WebSocketDisconnect:
        simulator.remove_connection(websocket)

@app.post("/api/send-message")
async def send_user_message(user_message: UserMessage):
    """Send a user message through the moderation pipeline"""
    try:
        # Create ChatMessage from user input
        message = simulator.message_generator.create_user_message(user_message)
        
        # Process through moderation pipeline
        result = await simulator.process_message(message)
        
        # Broadcast to connected clients
        await simulator.broadcast_message(result)
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        logger.error(f"Error processing user message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/single")
async def simulate_single_message(message_type: str = "normal"):
    """Generate and process a single message"""
    try:
        message = simulator.message_generator.generate_message(message_type)
        result = await simulator.process_message(message)
        
        return {
            "message": result["message"],
            "filter_result": result["filter_result"],
            "moderation_result": result["moderation_result"],
            "processing_time_ms": result["processing_time_ms"]
        }
    except Exception as e:
        logger.error(f"Error generating single message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate/start")
async def start_simulation():
    """Start continuous chat simulation"""
    if not simulator.simulation_active:
        asyncio.create_task(simulator.simulate_chat_stream())
        return {"status": "Simulation started"}
    return {"status": "Simulation already running"}

@app.post("/simulate/stop")
async def stop_simulation():
    """Stop chat simulation"""
    simulator.stop_simulation()
    return {"status": "Simulation stopped"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "simulation_active": simulator.simulation_active,
        "connected_clients": len(simulator.active_connections),
        "endpoints": {
            "web_interface": "/",
            "websocket": "/ws",
            "api": "/api/send-message",
            "simulate": "/simulate/*"
        }
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/api/stats")
async def get_stats():
    """Get current simulation statistics"""
    return {
        "simulation_active": simulator.simulation_active,
        "connected_clients": len(simulator.active_connections),
        "message_interval": simulator.message_interval,
        "available_message_types": list(simulator.message_generator.sample_messages.keys()),
        "user_pool_size": len(simulator.message_generator.user_pool),
        "channels": simulator.message_generator.channels
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
