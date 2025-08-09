"""
Decision Handler - Policy Enforcement and Action Execution
Handles moderation decisions and executes appropriate actions
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
import asyncpg
from prometheus_client import Counter, Histogram, generate_latest
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
DECISION_COUNT = Counter('decisions_total', 'Total decisions processed', ['action', 'severity'])
DECISION_DURATION = Histogram('decision_processing_seconds', 'Decision processing time')
ACTION_COUNT = Counter('actions_executed_total', 'Total actions executed', ['action_type'])

class ModerationDecision(BaseModel):
    user_id: str = Field(..., description="User ID")
    channel_id: str = Field(..., description="Channel ID")
    message_id: Optional[str] = Field(None, description="Message ID")
    decision: str = Field(..., description="Moderation decision")
    confidence: float = Field(..., description="Confidence score")
    reasoning: Optional[str] = Field(None, description="Reasoning for decision")
    severity: str = Field(default="medium", description="Severity level")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ActionResponse(BaseModel):
    action_taken: str = Field(..., description="Action that was taken")
    success: bool = Field(..., description="Whether action was successful")
    details: Optional[str] = Field(None, description="Additional details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class DecisionHandler:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/moderation_db")
        self.webhook_url = os.getenv("NOTIFICATION_WEBHOOK_URL", "")
        self.db_pool = None
        
        # Action thresholds
        self.action_thresholds = {
            "warn": 0.3,
            "timeout": 0.6,
            "kick": 0.8,
            "ban": 0.9
        }
        
        # Severity mapping
        self.severity_actions = {
            "low": ["warn"],
            "medium": ["warn", "timeout"],
            "high": ["timeout", "kick"],
            "critical": ["kick", "ban"]
        }

    async def initialize_db(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(self.database_url)
            await self.create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    async def create_tables(self):
        """Create necessary database tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS moderation_decisions (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    channel_id VARCHAR(255) NOT NULL,
                    message_id VARCHAR(255),
                    decision VARCHAR(100) NOT NULL,
                    confidence FLOAT NOT NULL,
                    reasoning TEXT,
                    severity VARCHAR(50) NOT NULL,
                    action_taken VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_violations (
                    id SERIAL PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    violation_count INTEGER DEFAULT 1,
                    last_violation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_score FLOAT DEFAULT 0.0,
                    status VARCHAR(50) DEFAULT 'active'
                );
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_violations_user_id 
                ON user_violations(user_id);
            """)

    async def determine_action(self, decision: ModerationDecision) -> str:
        """Determine what action to take based on decision and user history"""
        
        # Get user violation history
        user_history = await self.get_user_history(decision.user_id)
        
        # Calculate action based on confidence and history
        base_action = self._get_base_action(decision.confidence, decision.severity)
        
        # Escalate based on user history
        if user_history:
            violation_count = user_history.get('violation_count', 0)
            if violation_count > 5:
                base_action = self._escalate_action(base_action)
        
        return base_action

    def _get_base_action(self, confidence: float, severity: str) -> str:
        """Get base action based on confidence and severity"""
        available_actions = self.severity_actions.get(severity, ["warn"])
        
        for action in ["ban", "kick", "timeout", "warn"]:
            if action in available_actions and confidence >= self.action_thresholds.get(action, 1.0):
                return action
        
        return "warn"

    def _escalate_action(self, base_action: str) -> str:
        """Escalate action based on user history"""
        escalation_map = {
            "warn": "timeout",
            "timeout": "kick",
            "kick": "ban",
            "ban": "ban"
        }
        return escalation_map.get(base_action, base_action)

    async def get_user_history(self, user_id: str) -> Optional[Dict]:
        """Get user violation history"""
        if not self.db_pool:
            return None
            
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT violation_count, total_score, last_violation, status
                FROM user_violations 
                WHERE user_id = $1
            """, user_id)
            
            if result:
                return dict(result)
        return None

    async def update_user_history(self, user_id: str, confidence: float):
        """Update user violation history"""
        if not self.db_pool:
            return
            
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_violations (user_id, violation_count, total_score, last_violation)
                VALUES ($1, 1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    violation_count = user_violations.violation_count + 1,
                    total_score = user_violations.total_score + $2,
                    last_violation = CURRENT_TIMESTAMP
            """, user_id, confidence)

    async def execute_action(self, action: str, decision: ModerationDecision) -> ActionResponse:
        """Execute the determined action"""
        
        try:
            if action == "warn":
                return await self._execute_warn(decision)
            elif action == "timeout":
                return await self._execute_timeout(decision)
            elif action == "kick":
                return await self._execute_kick(decision)
            elif action == "ban":
                return await self._execute_ban(decision)
            else:
                return ActionResponse(
                    action_taken="none",
                    success=True,
                    details="No action required"
                )
        except Exception as e:
            logger.error(f"Failed to execute action {action}: {e}")
            return ActionResponse(
                action_taken=action,
                success=False,
                details=f"Action failed: {str(e)}"
            )

    async def _execute_warn(self, decision: ModerationDecision) -> ActionResponse:
        """Execute warning action"""
        # In a real implementation, this would send a warning to the user
        logger.info(f"Warning user {decision.user_id} in channel {decision.channel_id}")
        
        # Send notification if webhook is configured
        if self.webhook_url:
            await self._send_notification(f"⚠️ User {decision.user_id} warned for: {decision.reasoning}")
        
        return ActionResponse(
            action_taken="warn",
            success=True,
            details=f"User warned for: {decision.reasoning}"
        )

    async def _execute_timeout(self, decision: ModerationDecision) -> ActionResponse:
        """Execute timeout action"""
        timeout_duration = 300  # 5 minutes
        logger.info(f"Timing out user {decision.user_id} for {timeout_duration} seconds")
        
        if self.webhook_url:
            await self._send_notification(f"⏰ User {decision.user_id} timed out for 5 minutes: {decision.reasoning}")
        
        return ActionResponse(
            action_taken="timeout",
            success=True,
            details=f"User timed out for {timeout_duration} seconds"
        )

    async def _execute_kick(self, decision: ModerationDecision) -> ActionResponse:
        """Execute kick action"""
        logger.info(f"Kicking user {decision.user_id} from channel {decision.channel_id}")
        
        if self.webhook_url:
            await self._send_notification(f"👢 User {decision.user_id} kicked: {decision.reasoning}")
        
        return ActionResponse(
            action_taken="kick",
            success=True,
            details=f"User kicked from channel"
        )

    async def _execute_ban(self, decision: ModerationDecision) -> ActionResponse:
        """Execute ban action"""
        logger.info(f"Banning user {decision.user_id}")
        
        if self.webhook_url:
            await self._send_notification(f"🔨 User {decision.user_id} banned: {decision.reasoning}")
        
        return ActionResponse(
            action_taken="ban",
            success=True,
            details=f"User permanently banned"
        )

    async def _send_notification(self, message: str):
        """Send notification to webhook"""
        if not self.webhook_url:
            return
            
        try:
            async with httpx.AsyncClient() as client:
                payload = {"text": message}
                await client.post(self.webhook_url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def record_decision(self, decision: ModerationDecision, action: str):
        """Record decision in database"""
        if not self.db_pool:
            return
            
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO moderation_decisions 
                (user_id, channel_id, message_id, decision, confidence, reasoning, severity, action_taken, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            decision.user_id, decision.channel_id, decision.message_id,
            decision.decision, decision.confidence, decision.reasoning,
            decision.severity, action, json.dumps(decision.metadata))

# Initialize FastAPI app
app = FastAPI(
    title="Decision Handler",
    description="Policy enforcement and action execution for moderation system",
    version="1.0.0"
)

# Initialize decision handler
decision_handler = DecisionHandler()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await decision_handler.initialize_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connected": decision_handler.db_pool is not None
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    from fastapi import Response
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/process", response_model=ActionResponse)
async def process_decision(decision: ModerationDecision, background_tasks: BackgroundTasks):
    """Process a moderation decision and execute appropriate action"""
    
    with DECISION_DURATION.time():
        try:
            # Determine action to take
            action = await decision_handler.determine_action(decision)
            
            # Execute the action
            response = await decision_handler.execute_action(action, decision)
            
            # Record decision and update user history in background
            background_tasks.add_task(decision_handler.record_decision, decision, action)
            if decision.confidence > 0.5:  # Only count as violation if confidence is high
                background_tasks.add_task(decision_handler.update_user_history, decision.user_id, decision.confidence)
            
            # Update metrics
            DECISION_COUNT.labels(action=action, severity=decision.severity).inc()
            ACTION_COUNT.labels(action_type=action).inc()
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing decision: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/history")
async def get_user_violations(user_id: str):
    """Get user violation history"""
    history = await decision_handler.get_user_history(user_id)
    if not history:
        return {"user_id": user_id, "violations": 0, "status": "clean"}
    
    return {
        "user_id": user_id,
        "violation_count": history.get("violation_count", 0),
        "total_score": history.get("total_score", 0.0),
        "last_violation": history.get("last_violation"),
        "status": history.get("status", "active")
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
