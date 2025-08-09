"""
Metrics Evaluator - Comprehensive Monitoring and Evaluation
Collects, analyzes, and reports on system performance and accuracy
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
import asyncpg
import httpx
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Metrics
EVALUATION_COUNT = Counter('evaluations_total', 'Total evaluations performed')
ACCURACY_GAUGE = Gauge('system_accuracy', 'Current system accuracy')
LATENCY_GAUGE = Gauge('average_latency_seconds', 'Average system latency')
THROUGHPUT_GAUGE = Gauge('messages_per_second', 'Messages processed per second')

class SystemMetrics(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_messages: int = Field(..., description="Total messages processed")
    accuracy: float = Field(..., description="System accuracy percentage")
    average_latency: float = Field(..., description="Average latency in seconds")
    throughput: float = Field(..., description="Messages per second")
    error_rate: float = Field(..., description="Error rate percentage")
    
class AccuracyReport(BaseModel):
    period: str = Field(..., description="Time period for report")
    total_decisions: int = Field(..., description="Total decisions made")
    correct_decisions: int = Field(..., description="Correct decisions")
    false_positives: int = Field(..., description="False positive count")
    false_negatives: int = Field(..., description="False negative count")
    accuracy: float = Field(..., description="Overall accuracy")
    precision: float = Field(..., description="Precision score")
    recall: float = Field(..., description="Recall score")
    f1_score: float = Field(..., description="F1 score")

class PerformanceReport(BaseModel):
    period: str = Field(..., description="Time period for report")
    avg_latency: float = Field(..., description="Average latency")
    p95_latency: float = Field(..., description="95th percentile latency")
    p99_latency: float = Field(..., description="99th percentile latency")
    throughput: float = Field(..., description="Average throughput")
    error_rate: float = Field(..., description="Error rate")
    uptime: float = Field(..., description="System uptime percentage")

class MetricsEvaluator:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@postgres:5432/moderation_db")
        self.prometheus_url = os.getenv("PROMETHEUS_ENDPOINT", "http://prometheus:9090")
        self.db_pool = None
        
        # Evaluation thresholds
        self.accuracy_threshold = 0.85
        self.latency_threshold = 5.0  # seconds
        self.error_rate_threshold = 0.05  # 5%

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
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_messages INTEGER NOT NULL,
                    accuracy FLOAT NOT NULL,
                    average_latency FLOAT NOT NULL,
                    throughput FLOAT NOT NULL,
                    error_rate FLOAT NOT NULL,
                    metadata JSONB
                );
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS accuracy_evaluations (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    decision_id INTEGER,
                    predicted_label VARCHAR(100),
                    actual_label VARCHAR(100),
                    confidence FLOAT,
                    is_correct BOOLEAN,
                    evaluation_type VARCHAR(50)
                );
            """)

    async def collect_prometheus_metrics(self) -> Dict[str, float]:
        """Collect metrics from Prometheus"""
        try:
            async with httpx.AsyncClient() as client:
                # Query various metrics from Prometheus
                queries = {
                    "total_requests": "sum(rate(mcp_requests_total[5m]))",
                    "avg_latency": "avg(mcp_request_duration_seconds)",
                    "error_rate": "sum(rate(mcp_requests_total{status!=\"200\"}[5m])) / sum(rate(mcp_requests_total[5m]))",
                    "throughput": "sum(rate(mcp_requests_total[1m]))"
                }
                
                metrics = {}
                for name, query in queries.items():
                    response = await client.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={"query": query},
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("data", {}).get("result"):
                            value = float(data["data"]["result"][0]["value"][1])
                            metrics[name] = value
                        else:
                            metrics[name] = 0.0
                    else:
                        metrics[name] = 0.0
                
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to collect Prometheus metrics: {e}")
            return {
                "total_requests": 0.0,
                "avg_latency": 0.0,
                "error_rate": 0.0,
                "throughput": 0.0
            }

    async def calculate_accuracy(self, period_hours: int = 24) -> Dict[str, float]:
        """Calculate system accuracy over specified period"""
        if not self.db_pool:
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}
        
        try:
            async with self.db_pool.acquire() as conn:
                # Get decisions from the last period
                result = await conn.fetch("""
                    SELECT decision, confidence, reasoning
                    FROM moderation_decisions 
                    WHERE timestamp > NOW() - INTERVAL '%s hours'
                """, period_hours)
                
                if not result:
                    return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}
                
                # Simple accuracy calculation based on confidence
                # In a real system, you'd have ground truth labels
                total_decisions = len(result)
                high_confidence_decisions = sum(1 for r in result if r['confidence'] > 0.8)
                
                # Mock accuracy calculation
                accuracy = high_confidence_decisions / total_decisions if total_decisions > 0 else 0.0
                precision = accuracy * 0.95  # Mock precision
                recall = accuracy * 0.90     # Mock recall
                f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
                
                return {
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score
                }
                
        except Exception as e:
            logger.error(f"Failed to calculate accuracy: {e}")
            return {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1_score": 0.0}

    async def generate_system_metrics(self) -> SystemMetrics:
        """Generate comprehensive system metrics"""
        
        # Collect Prometheus metrics
        prom_metrics = await self.collect_prometheus_metrics()
        
        # Calculate accuracy
        accuracy_metrics = await self.calculate_accuracy()
        
        # Get total message count from database
        total_messages = await self.get_total_message_count()
        
        metrics = SystemMetrics(
            total_messages=total_messages,
            accuracy=accuracy_metrics["accuracy"],
            average_latency=prom_metrics["avg_latency"],
            throughput=prom_metrics["throughput"],
            error_rate=prom_metrics["error_rate"]
        )
        
        # Update Prometheus gauges
        ACCURACY_GAUGE.set(metrics.accuracy)
        LATENCY_GAUGE.set(metrics.average_latency)
        THROUGHPUT_GAUGE.set(metrics.throughput)
        
        return metrics

    async def get_total_message_count(self) -> int:
        """Get total number of processed messages"""
        if not self.db_pool:
            return 0
            
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM moderation_decisions")
                return result or 0
        except Exception as e:
            logger.error(f"Failed to get message count: {e}")
            return 0

    async def generate_accuracy_report(self, period_hours: int = 24) -> AccuracyReport:
        """Generate detailed accuracy report"""
        
        accuracy_metrics = await self.calculate_accuracy(period_hours)
        
        # Mock data for demonstration
        total_decisions = await self.get_total_message_count()
        correct_decisions = int(total_decisions * accuracy_metrics["accuracy"])
        false_positives = int(total_decisions * 0.05)  # Mock 5% false positives
        false_negatives = int(total_decisions * 0.03)  # Mock 3% false negatives
        
        return AccuracyReport(
            period=f"{period_hours} hours",
            total_decisions=total_decisions,
            correct_decisions=correct_decisions,
            false_positives=false_positives,
            false_negatives=false_negatives,
            accuracy=accuracy_metrics["accuracy"],
            precision=accuracy_metrics["precision"],
            recall=accuracy_metrics["recall"],
            f1_score=accuracy_metrics["f1_score"]
        )

    async def generate_performance_report(self, period_hours: int = 24) -> PerformanceReport:
        """Generate detailed performance report"""
        
        prom_metrics = await self.collect_prometheus_metrics()
        
        return PerformanceReport(
            period=f"{period_hours} hours",
            avg_latency=prom_metrics["avg_latency"],
            p95_latency=prom_metrics["avg_latency"] * 1.5,  # Mock P95
            p99_latency=prom_metrics["avg_latency"] * 2.0,  # Mock P99
            throughput=prom_metrics["throughput"],
            error_rate=prom_metrics["error_rate"],
            uptime=0.999  # Mock 99.9% uptime
        )

    async def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health and generate alerts if needed"""
        
        metrics = await self.generate_system_metrics()
        
        health_status = {
            "overall_status": "healthy",
            "alerts": [],
            "metrics": metrics.dict()
        }
        
        # Check accuracy threshold
        if metrics.accuracy < self.accuracy_threshold:
            health_status["alerts"].append({
                "type": "accuracy_low",
                "message": f"System accuracy ({metrics.accuracy:.2%}) below threshold ({self.accuracy_threshold:.2%})",
                "severity": "warning"
            })
            health_status["overall_status"] = "degraded"
        
        # Check latency threshold
        if metrics.average_latency > self.latency_threshold:
            health_status["alerts"].append({
                "type": "latency_high",
                "message": f"Average latency ({metrics.average_latency:.2f}s) above threshold ({self.latency_threshold}s)",
                "severity": "warning"
            })
            health_status["overall_status"] = "degraded"
        
        # Check error rate threshold
        if metrics.error_rate > self.error_rate_threshold:
            health_status["alerts"].append({
                "type": "error_rate_high",
                "message": f"Error rate ({metrics.error_rate:.2%}) above threshold ({self.error_rate_threshold:.2%})",
                "severity": "critical"
            })
            health_status["overall_status"] = "unhealthy"
        
        return health_status

    async def store_metrics(self, metrics: SystemMetrics):
        """Store metrics in database"""
        if not self.db_pool:
            return
            
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO system_metrics 
                    (total_messages, accuracy, average_latency, throughput, error_rate)
                    VALUES ($1, $2, $3, $4, $5)
                """, 
                metrics.total_messages, metrics.accuracy, metrics.average_latency,
                metrics.throughput, metrics.error_rate)
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="Metrics Evaluator",
    description="Comprehensive monitoring and evaluation for moderation system",
    version="1.0.0"
)

# Initialize metrics evaluator
metrics_evaluator = MetricsEvaluator()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await metrics_evaluator.initialize_db()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database_connected": metrics_evaluator.db_pool is not None
    }

@app.get("/metrics/system", response_model=SystemMetrics)
async def get_system_metrics():
    """Get current system metrics"""
    try:
        metrics = await metrics_evaluator.generate_system_metrics()
        
        # Store metrics for historical tracking
        await metrics_evaluator.store_metrics(metrics)
        
        EVALUATION_COUNT.inc()
        return metrics
        
    except Exception as e:
        logger.error(f"Error generating system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/accuracy", response_model=AccuracyReport)
async def get_accuracy_report(period_hours: int = 24):
    """Get accuracy report for specified period"""
    try:
        report = await metrics_evaluator.generate_accuracy_report(period_hours)
        return report
        
    except Exception as e:
        logger.error(f"Error generating accuracy report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/performance", response_model=PerformanceReport)
async def get_performance_report(period_hours: int = 24):
    """Get performance report for specified period"""
    try:
        report = await metrics_evaluator.generate_performance_report(period_hours)
        return report
        
    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/system")
async def get_system_health():
    """Get comprehensive system health check"""
    try:
        health = await metrics_evaluator.check_system_health()
        return health
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
