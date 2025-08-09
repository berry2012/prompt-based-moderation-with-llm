# Real-Time Moderation System Architecture

## System Overview

This is a comprehensive real-time moderation system for streaming chat applications using Large Language Models. The system is designed to be modular, scalable, and deployable on Kubernetes with your existing DeepSeek LLM deployment.

## Architecture Components

### 1. MCP Server (Model Context Protocol Server)
**Port: 8000**

The core component that handles structured moderation requests and interfaces with your DeepSeek LLM.

**Key Features:**
- REST API for moderation requests
- Prompt template management with versioning
- Input validation and prompt injection protection
- Observability hooks (metrics, logging, tracing)
- Configurable retry logic and timeouts

**API Endpoints:**
```
POST /moderate - Process moderation request
GET /health - Health check
GET /templates - List available prompt templates
GET /metrics - Prometheus metrics
```

**Request/Response Format:**
```json
// Request
{
  "message": "Chat message to moderate",
  "user_id": "user_123",
  "channel_id": "general",
  "timestamp": "2024-01-01T12:00:00Z",
  "template_name": "moderation_prompt",
  "metadata": {}
}

// Response
{
  "decision": "Toxic/Non-Toxic",
  "confidence": 0.95,
  "reasoning": "Contains hate speech",
  "processing_time_ms": 150.5,
  "template_version": "1.0"
}
```

### 2. Prompt Template System

YAML-based template management system with multiple specialized templates:

- **moderation_prompt**: General toxicity classification
- **harassment_detection**: Specialized harassment detection
- **spam_detection**: Spam and promotional content
- **pii_detection**: Personal information detection
- **content_policy**: Platform policy enforcement
- **multilingual_moderation**: Multi-language support
- **context_aware_moderation**: Conversation context analysis

### 3. Chat Simulator
**Port: 8002**

Simulates realistic streaming chat environment for testing and demonstration.

**Features:**
- WebSocket support for real-time simulation
- Configurable message intervals
- Multiple message types (normal, toxic, spam, PII)
- Whisper integration for speech-to-text
- Real-time metrics and monitoring

**API Endpoints:**
```
WebSocket /ws - Real-time chat simulation
POST /simulate/single - Generate single message
POST /simulate/start - Start continuous simulation
POST /simulate/stop - Stop simulation
GET /health - Health check
```

### 4. Lightweight Filter
**Port: 8001**

Fast preprocessing filter that reduces LLM API calls through keyword-based filtering.

**Features:**
- Keyword-based filtering
- Profanity detection
- Rate limiting per user
- PII pattern matching
- Configurable filter rules
- Toggle-able filters for A/B testing

**Filter Types:**
- Banned words filter
- Toxic pattern matching
- Spam detection patterns
- PII regex patterns
- Rate limiting

### 5. Decision Handler
**Port: 8003**

Processes LLM decisions and applies policy logic with configurable actions.

**Actions Supported:**
- **Allow**: Message passes through
- **Log**: Log for review
- **Flag**: Flag for moderator attention
- **Escalate**: Escalate to senior moderators
- **Ban**: Ban user from platform
- **Timeout**: Temporary user timeout

**Features:**
- Policy engine with configurable rules
- User history tracking
- Repeat offender detection
- Automated escalation rules
- Database persistence
- Notification system integration

### 6. Metrics & Evaluation Module
**Port: 8004**

Comprehensive monitoring and evaluation system.

**Metrics Collected:**
- Processing latency per component
- Message throughput
- LLM response times
- Accuracy metrics (when ground truth available)
- Cost per inference
- Error rates and retry counts

**Monitoring Stack:**
- Prometheus for metrics collection
- Grafana for visualization
- Jaeger for distributed tracing
- Custom dashboards for moderation insights

## Data Flow

```
Chat Message → Lightweight Filter → MCP Server → DeepSeek LLM
                     ↓                    ↓
              Decision Handler ← LLM Response
                     ↓
              Action Execution + Database Storage
                     ↓
              Metrics Collection + Notifications
```

## Deployment Architecture

### Docker Compose (Local Development)
```bash
# Start entire system
make up

# Access points:
# - MCP Server: http://localhost:8000
# - Chat Simulator: http://localhost:8002  
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

### Kubernetes (Production)
```bash
# Deploy to your EKS cluster
kubectl apply -f deployment/kubernetes/

# Components deployed:
# - All microservices with HPA
# - PostgreSQL for persistence
# - Redis for caching
# - Prometheus + Grafana monitoring
# - Network policies for security
```

## Configuration

### Environment Variables

**MCP Server:**
```bash
LLM_ENDPOINT=http://deepseek-llm:8080/v1/chat/completions
LLM_TIMEOUT=30.0
LLM_MAX_RETRIES=3
LOG_LEVEL=INFO
```

**Chat Simulator:**
```bash
MCP_ENDPOINT=http://mcp-server:8000
FILTER_ENDPOINT=http://lightweight-filter:8001
MESSAGE_INTERVAL=2.0
WHISPER_MODEL_SIZE=base
```

**Decision Handler:**
```bash
DATABASE_URL=postgresql://postgres:password@postgres:5432/moderation_db
NOTIFICATION_WEBHOOK_URL=https://your-webhook-url
```

## API Contracts

### MCP Server API

#### POST /moderate
Processes a chat message for moderation.

**Request:**
```json
{
  "message": "string (required)",
  "user_id": "string (required)", 
  "channel_id": "string (required)",
  "timestamp": "ISO 8601 datetime",
  "template_name": "string (default: moderation_prompt)",
  "metadata": "object (optional)"
}
```

**Response:**
```json
{
  "decision": "string",
  "confidence": "float (0-1)",
  "reasoning": "string",
  "processing_time_ms": "float",
  "template_version": "string"
}
```

### Lightweight Filter API

#### POST /filter
Pre-filters a message before LLM processing.

**Request:**
```json
{
  "user_id": "string",
  "username": "string",
  "channel_id": "string", 
  "message": "string",
  "timestamp": "string",
  "message_type": "string",
  "metadata": "object"
}
```

**Response:**
```json
{
  "should_process": "boolean",
  "filter_decision": "string",
  "confidence": "float",
  "matched_patterns": ["string"],
  "processing_time_ms": "float",
  "filter_type": "string"
}
```

### Decision Handler API

#### POST /decide
Processes moderation decision and executes policy actions.

**Request:**
```json
{
  "message_id": "string",
  "user_id": "string",
  "username": "string",
  "channel_id": "string",
  "original_message": "string",
  "llm_decision": "string", 
  "confidence": "float",
  "reasoning": "string",
  "filter_results": "object",
  "metadata": "object"
}
```

**Response:**
```json
{
  "action_taken": "allow|log|flag|escalate|ban|timeout",
  "severity": "low|medium|high|critical",
  "message": "string",
  "should_notify_moderators": "boolean",
  "processing_time_ms": "float"
}
```

## Performance Characteristics

### Latency Targets
- Lightweight Filter: < 10ms
- MCP Server: < 200ms (excluding LLM)
- Decision Handler: < 50ms
- End-to-end: < 500ms (including LLM)

### Throughput
- Designed for 1000+ messages/second
- Horizontal scaling via Kubernetes HPA
- Load balancing across multiple replicas

### Resource Requirements

**Minimum (Development):**
- CPU: 4 cores
- Memory: 8GB RAM
- Storage: 20GB

**Production (Recommended):**
- CPU: 16+ cores
- Memory: 32GB+ RAM  
- Storage: 100GB+ SSD
- GPU: For DeepSeek LLM (already deployed)

## Security Considerations

1. **Input Validation**: All inputs validated for prompt injection
2. **Rate Limiting**: Per-user and global rate limits
3. **Network Policies**: Kubernetes network segmentation
4. **Secrets Management**: Kubernetes secrets for sensitive data
5. **Audit Logging**: All decisions logged with full context
6. **Data Privacy**: PII detection and handling

## Monitoring and Alerting

### Key Metrics
- Message processing rate
- Error rates by component
- LLM response latency
- Decision accuracy (when ground truth available)
- Resource utilization

### Alerts
- High error rates
- Latency spikes
- Resource exhaustion
- Failed deployments
- Security incidents

## Integration with Your EKS Cluster

Since you already have DeepSeek LLM deployed, you'll need to:

1. **Update LLM endpoint** in configuration
2. **Deploy to your custom nodepool** using node selectors
3. **Configure networking** to reach your LLM service
4. **Set up monitoring** integration with existing tools
5. **Configure disruption budgets** for your 4pm maintenance window

## Getting Started

1. **Clone and configure:**
   ```bash
   git clone <repository>
   cd moderation-system
   cp .env.example .env
   # Edit .env with your LLM endpoint
   ```

2. **Local development:**
   ```bash
   make dev-setup
   make demo
   ```

3. **Production deployment:**
   ```bash
   # Update kubernetes manifests with your cluster details
   make deploy-k8s
   ```

4. **Monitor the system:**
   ```bash
   make monitor
   ```

This architecture provides a production-ready, scalable moderation system that integrates seamlessly with your existing Kubernetes infrastructure and DeepSeek LLM deployment.


