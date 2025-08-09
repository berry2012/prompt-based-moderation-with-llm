# API Documentation

## Overview

The Real-Time Moderation System provides REST APIs for all components. Each service exposes standardized endpoints for health checks, metrics, and core functionality.

## Base URLs

- **MCP Server**: `http://localhost:8000`
- **Lightweight Filter**: `http://localhost:8001`
- **Chat Simulator**: `http://localhost:8002`
- **Decision Handler**: `http://localhost:8003`
- **Metrics Evaluator**: `http://localhost:8004`

## Authentication

Currently, the system uses API key authentication for production deployments:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8000/moderate
```

## MCP Server API

### POST /moderate

Processes a chat message for moderation using the configured LLM.

**Request:**
```json
{
  "message": "Hey everyone, how's it going?",
  "user_id": "user_123",
  "channel_id": "general",
  "timestamp": "2024-01-01T12:00:00Z",
  "template_name": "moderation_prompt",
  "metadata": {
    "user_reputation": "trusted",
    "channel_type": "public"
  }
}
```

**Response:**
```json
{
  "decision": "Non-Toxic",
  "confidence": 0.95,
  "reasoning": "Message contains friendly greeting with no harmful content",
  "processing_time_ms": 245.7,
  "template_version": "1.0"
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid input or prompt injection detected
- `503`: LLM service unavailable
- `500`: Internal server error

### GET /templates

Lists available prompt templates.

**Response:**
```json
{
  "templates": [
    "moderation_prompt",
    "harassment_detection", 
    "spam_detection",
    "pii_detection",
    "content_policy",
    "multilingual_moderation",
    "context_aware_moderation"
  ]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### GET /metrics

Prometheus metrics endpoint (returns plain text metrics).

## Lightweight Filter API

### POST /filter

Pre-filters a message before LLM processing.

**Request:**
```json
{
  "user_id": "user_123",
  "username": "ChatUser",
  "channel_id": "general",
  "message": "This is a test message",
  "timestamp": "2024-01-01T12:00:00Z",
  "message_type": "text",
  "metadata": {}
}
```

**Response:**
```json
{
  "should_process": true,
  "filter_decision": "pass",
  "confidence": 0.9,
  "matched_patterns": [],
  "processing_time_ms": 5.2,
  "filter_type": "combined"
}
```

### GET /config

Returns current filter configuration.

**Response:**
```json
{
  "enabled_filters": {
    "keywords": true,
    "profanity": true,
    "rate_limit": true
  },
  "banned_words_count": 25,
  "profanity_words_count": 50,
  "rate_limit_window": 60,
  "max_messages_per_window": 10
}
```

### POST /config/toggle/{filter_name}

Enable or disable a specific filter.

**Parameters:**
- `filter_name`: keywords, profanity, or rate_limit
- `enabled`: boolean (query parameter)

**Example:**
```bash
curl -X POST "http://localhost:8001/config/toggle/profanity?enabled=false"
```

## Chat Simulator API

### WebSocket /ws

Real-time chat simulation endpoint.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8002/ws');

// Start simulation
ws.send(JSON.stringify({
  "action": "start_simulation"
}));

// Stop simulation  
ws.send(JSON.stringify({
  "action": "stop_simulation"
}));
```

**Message Format:**
```json
{
  "type": "chat_message",
  "message": {
    "user_id": "user_0001",
    "username": "GamerPro123",
    "channel_id": "gaming",
    "message": "Great game session!",
    "timestamp": "2024-01-01T12:00:00Z",
    "message_type": "text",
    "metadata": {
      "reputation": "trusted",
      "activity_level": "high"
    }
  },
  "filter_result": {
    "should_process": true,
    "filter_decision": "pass",
    "confidence": 0.9
  },
  "moderation_result": {
    "decision": "Non-Toxic",
    "confidence": 0.95,
    "reasoning": "Positive gaming content"
  },
  "processing_time_ms": 156.3,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### POST /simulate/single

Generate and process a single message.

**Parameters:**
- `message_type`: normal, toxic, spam, pii, harassment, misinformation

**Example:**
```bash
curl -X POST "http://localhost:8002/simulate/single?message_type=normal"
```

### POST /simulate/start

Start continuous chat simulation.

### POST /simulate/stop

Stop chat simulation.

## Decision Handler API

### POST /decide

Process moderation decision and execute policy actions.

**Request:**
```json
{
  "message_id": "msg_123",
  "user_id": "user_123",
  "username": "ChatUser",
  "channel_id": "general",
  "original_message": "This is toxic content",
  "llm_decision": "Toxic",
  "confidence": 0.95,
  "reasoning": "Contains hate speech",
  "filter_results": {
    "matched_patterns": ["hate"]
  },
  "metadata": {}
}
```

**Response:**
```json
{
  "action_taken": "flag",
  "severity": "high",
  "message": "Message flagged for moderator review",
  "should_notify_moderators": true,
  "processing_time_ms": 45.2
}
```

### GET /user/{user_id}/history

Get user's moderation history.

**Parameters:**
- `limit`: Number of records to return (default: 50)

**Response:**
```json
{
  "user_id": "user_123",
  "history": [
    {
      "message_id": "msg_123",
      "original_message": "Previous message",
      "llm_decision": "Non-Toxic",
      "action_taken": "allow",
      "timestamp": "2024-01-01T11:00:00Z"
    }
  ]
}
```

## Error Handling

All APIs use standard HTTP status codes and return errors in this format:

```json
{
  "detail": "Error message description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

- **Per User**: 60 requests per minute
- **Global**: 1000 requests per minute per service
- **Headers**: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Monitoring Endpoints

All services expose:
- `/health` - Health check
- `/metrics` - Prometheus metrics
- `/stats` - Service-specific statistics

## SDK Examples

### Python
```python
import httpx

async def moderate_message(message: str, user_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/moderate",
            json={
                "message": message,
                "user_id": user_id,
                "channel_id": "general"
            }
        )
        return response.json()
```

### JavaScript
```javascript
async function moderateMessage(message, userId) {
  const response = await fetch('http://localhost:8000/moderate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: message,
      user_id: userId,
      channel_id: 'general'
    })
  });
  return await response.json();
}
```

### cURL
```bash
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello everyone!",
    "user_id": "user_123",
    "channel_id": "general"
  }'
```
