"""
Lightweight Filter - Fast preprocessing filter for chat messages
Performs keyword-based filtering before expensive LLM calls
"""

import re
import time
import logging
from typing import List, Dict, Set, Any, Optional
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from datetime import datetime
import os
import yaml
import json
from prometheus_client import Counter, Histogram, generate_latest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
FILTER_REQUESTS_TOTAL = Counter('filter_requests_total', 'Total filter requests', ['decision', 'filter_type'])
FILTER_PROCESSING_TIME = Histogram('filter_processing_seconds', 'Time spent processing filter requests')
PATTERN_MATCHES = Counter('filter_pattern_matches_total', 'Pattern matches by type', ['pattern_type'])

class FilterRequest(BaseModel):
    user_id: str
    username: str
    channel_id: str
    message: str
    timestamp: str
    message_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None

class FilterResponse(BaseModel):
    should_process: bool = Field(..., description="Whether to send to LLM")
    filter_decision: str = Field(..., description="Filter decision")
    confidence: float = Field(..., description="Confidence score")
    matched_patterns: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(..., description="Processing time")
    filter_type: str = Field(..., description="Type of filter that triggered")

class KeywordFilter:
    def __init__(self, config_path: str = "/app/config/filter_config.yaml"):
        self.config_path = config_path
        self.banned_words: Set[str] = set()
        self.toxic_patterns: List[re.Pattern] = []
        self.spam_patterns: List[re.Pattern] = []
        self.pii_patterns: List[re.Pattern] = []
        self.whitelist_words: Set[str] = set()
        self.load_config()
    
    def load_config(self):
        """Load filter configuration"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                self._load_banned_words(config.get('banned_words', []))
                self._load_patterns(config.get('patterns', {}))
                self._load_whitelist(config.get('whitelist', []))
                logger.info("Filter configuration loaded successfully")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}")
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration if file not found"""
        # Basic banned words
        self.banned_words = {
            "spam", "scam", "fake", "bot", "hack", "cheat",
            "idiot", "stupid", "moron", "loser", "noob"
        }
        
        # Basic patterns
        self.toxic_patterns = [
            re.compile(r'\b(kill\s+yourself|kys)\b', re.IGNORECASE),
            re.compile(r'\b(go\s+die|die\s+in\s+a\s+fire)\b', re.IGNORECASE),
            re.compile(r'\b(hate\s+you|you\s+suck)\b', re.IGNORECASE),
        ]
        
        self.spam_patterns = [
            re.compile(r'(bit\.ly|tinyurl|t\.co)/\w+', re.IGNORECASE),
            re.compile(r'(free\s+money|click\s+here|buy\s+now)', re.IGNORECASE),
            re.compile(r'💰{2,}|🎉{2,}|‼️{2,}', re.IGNORECASE),
        ]
        
        self.pii_patterns = [
            re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),  # Email
            re.compile(r'\b\d{3}-\d{3}-\d{4}\b'),  # Phone number
            re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),  # Credit card
            re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),  # SSN
        ]
    
    def _load_banned_words(self, words: List[str]):
        """Load banned words list"""
        self.banned_words = set(word.lower() for word in words)
    
    def _load_patterns(self, patterns: Dict[str, List[str]]):
        """Load regex patterns"""
        for pattern_type, pattern_list in patterns.items():
            compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in pattern_list]
            
            if pattern_type == "toxic":
                self.toxic_patterns = compiled_patterns
            elif pattern_type == "spam":
                self.spam_patterns = compiled_patterns
            elif pattern_type == "pii":
                self.pii_patterns = compiled_patterns
    
    def _load_whitelist(self, words: List[str]):
        """Load whitelist words that override bans"""
        self.whitelist_words = set(word.lower() for word in words)
    
    def check_banned_words(self, message: str) -> tuple[bool, List[str]]:
        """Check for banned words"""
        words = re.findall(r'\b\w+\b', message.lower())
        matched = []
        
        for word in words:
            if word in self.banned_words and word not in self.whitelist_words:
                matched.append(word)
        
        return len(matched) > 0, matched
    
    def check_patterns(self, message: str, patterns: List[re.Pattern]) -> tuple[bool, List[str]]:
        """Check message against regex patterns"""
        matched = []
        for pattern in patterns:
            matches = pattern.findall(message)
            if matches:
                matched.extend(matches if isinstance(matches[0], str) else [str(m) for m in matches])
        
        return len(matched) > 0, matched
    
    def filter_message(self, message: str) -> Dict[str, Any]:
        """Apply all filters to message"""
        start_time = time.time()
        
        # Check banned words
        has_banned, banned_matches = self.check_banned_words(message)
        
        # Check toxic patterns
        has_toxic, toxic_matches = self.check_patterns(message, self.toxic_patterns)
        
        # Check spam patterns
        has_spam, spam_matches = self.check_patterns(message, self.spam_patterns)
        
        # Check PII patterns
        has_pii, pii_matches = self.check_patterns(message, self.pii_patterns)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Determine overall result
        all_matches = banned_matches + toxic_matches + spam_matches + pii_matches
        
        if has_pii:
            decision = "block_pii"
            confidence = 0.95
            should_process = False
        elif has_toxic or has_banned:
            decision = "likely_toxic"
            confidence = 0.8
            should_process = True  # Still send to LLM for confirmation
        elif has_spam:
            decision = "likely_spam"
            confidence = 0.7
            should_process = True
        else:
            decision = "pass"
            confidence = 0.6
            should_process = True
        
        return {
            "should_process": should_process,
            "filter_decision": decision,
            "confidence": confidence,
            "matched_patterns": all_matches,
            "processing_time_ms": processing_time,
            "details": {
                "banned_words": banned_matches,
                "toxic_patterns": toxic_matches,
                "spam_patterns": spam_matches,
                "pii_patterns": pii_matches
            }
        }

class ProfanityFilter:
    def __init__(self, profanity_file: str = "/app/config/banned_words.txt"):
        self.profanity_file = profanity_file
        self.profanity_words: Set[str] = set()
        self.load_profanity_list()
    
    def load_profanity_list(self):
        """Load profanity word list from file"""
        try:
            with open(self.profanity_file, 'r') as file:
                self.profanity_words = set(word.strip().lower() for word in file.readlines())
            logger.info(f"Loaded {len(self.profanity_words)} profanity words")
        except FileNotFoundError:
            logger.warning(f"Profanity file not found: {self.profanity_file}")
            self.profanity_words = {"damn", "hell", "crap", "stupid", "idiot"}
    
    def contains_profanity(self, message: str) -> tuple[bool, List[str]]:
        """Check if message contains profanity"""
        words = re.findall(r'\b\w+\b', message.lower())
        found_profanity = []
        
        for word in words:
            if word in self.profanity_words:
                found_profanity.append(word)
        
        return len(found_profanity) > 0, found_profanity

class RateLimitFilter:
    def __init__(self):
        self.user_message_counts: Dict[str, List[float]] = {}
        self.rate_limit_window = 60  # seconds
        self.max_messages_per_window = 10
    
    def is_rate_limited(self, user_id: str) -> bool:
        """Check if user is rate limited"""
        current_time = time.time()
        
        if user_id not in self.user_message_counts:
            self.user_message_counts[user_id] = []
        
        # Remove old timestamps
        self.user_message_counts[user_id] = [
            timestamp for timestamp in self.user_message_counts[user_id]
            if current_time - timestamp < self.rate_limit_window
        ]
        
        # Add current timestamp
        self.user_message_counts[user_id].append(current_time)
        
        # Check if rate limited
        return len(self.user_message_counts[user_id]) > self.max_messages_per_window

class LightweightFilter:
    def __init__(self):
        self.keyword_filter = KeywordFilter()
        self.profanity_filter = ProfanityFilter()
        self.rate_limit_filter = RateLimitFilter()
        self.enabled_filters = {
            "keywords": True,
            "profanity": True,
            "rate_limit": True
        }
    
    def process_message(self, request: FilterRequest) -> FilterResponse:
        """Process message through all enabled filters"""
        start_time = time.time()
        
        # Check rate limiting first
        if self.enabled_filters["rate_limit"]:
            if self.rate_limit_filter.is_rate_limited(request.user_id):
                return FilterResponse(
                    should_process=False,
                    filter_decision="rate_limited",
                    confidence=1.0,
                    matched_patterns=["rate_limit_exceeded"],
                    processing_time_ms=(time.time() - start_time) * 1000,
                    filter_type="rate_limit"
                )
        
        # Apply keyword filter
        if self.enabled_filters["keywords"]:
            keyword_result = self.keyword_filter.filter_message(request.message)
            
            # If keyword filter blocks, return immediately
            if not keyword_result["should_process"]:
                return FilterResponse(
                    should_process=False,
                    filter_decision=keyword_result["filter_decision"],
                    confidence=keyword_result["confidence"],
                    matched_patterns=keyword_result["matched_patterns"],
                    processing_time_ms=keyword_result["processing_time_ms"],
                    filter_type="keyword"
                )
        
        # Apply profanity filter
        profanity_matches = []
        if self.enabled_filters["profanity"]:
            has_profanity, profanity_matches = self.profanity_filter.contains_profanity(request.message)
        
        # Combine results
        all_matches = keyword_result.get("matched_patterns", []) + profanity_matches
        
        # Final decision
        if keyword_result.get("filter_decision") == "likely_toxic" or profanity_matches:
            decision = "flagged"
            confidence = max(keyword_result.get("confidence", 0.5), 0.7 if profanity_matches else 0.0)
        else:
            decision = "pass"
            confidence = 0.9
        
        processing_time = (time.time() - start_time) * 1000
        
        return FilterResponse(
            should_process=True,
            filter_decision=decision,
            confidence=confidence,
            matched_patterns=all_matches,
            processing_time_ms=processing_time,
            filter_type="combined"
        )

# FastAPI app
app = FastAPI(
    title="Lightweight Filter",
    description="Fast preprocessing filter for chat moderation",
    version="1.0.0"
)

# Initialize filter
lightweight_filter = LightweightFilter()

@app.post("/filter", response_model=FilterResponse)
async def filter_message(request: FilterRequest):
    """Filter a chat message"""
    try:
        with FILTER_PROCESSING_TIME.time():
            result = lightweight_filter.process_message(request)
        
        # Track metrics
        FILTER_REQUESTS_TOTAL.labels(decision=result.filter_decision, filter_type=result.filter_type).inc()
        for pattern in result.matched_patterns:
            PATTERN_MATCHES.labels(pattern_type="keyword").inc()
        
        # Log the filtering result
        logger.info(
            f"Filtered message from {request.username}: "
            f"'{request.message[:50]}...' -> {result.filter_decision} "
            f"({result.processing_time_ms:.1f}ms)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error filtering message: {str(e)}")
        FILTER_REQUESTS_TOTAL.labels(decision="error", filter_type="unknown").inc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_filter_config():
    """Get current filter configuration"""
    return {
        "enabled_filters": lightweight_filter.enabled_filters,
        "banned_words_count": len(lightweight_filter.keyword_filter.banned_words),
        "profanity_words_count": len(lightweight_filter.profanity_filter.profanity_words),
        "rate_limit_window": lightweight_filter.rate_limit_filter.rate_limit_window,
        "max_messages_per_window": lightweight_filter.rate_limit_filter.max_messages_per_window
    }

@app.post("/config/toggle/{filter_name}")
async def toggle_filter(filter_name: str, enabled: bool):
    """Enable or disable a specific filter"""
    if filter_name in lightweight_filter.enabled_filters:
        lightweight_filter.enabled_filters[filter_name] = enabled
        return {"message": f"Filter '{filter_name}' {'enabled' if enabled else 'disabled'}"}
    else:
        raise HTTPException(status_code=404, detail=f"Filter '{filter_name}' not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "filters_enabled": lightweight_filter.enabled_filters,
        "timestamp": datetime.utcnow()
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/stats")
async def get_stats():
    """Get filter statistics"""
    return {
        "active_users": len(lightweight_filter.rate_limit_filter.user_message_counts),
        "total_banned_words": len(lightweight_filter.keyword_filter.banned_words),
        "total_profanity_words": len(lightweight_filter.profanity_filter.profanity_words),
        "enabled_filters": lightweight_filter.enabled_filters
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
