# Development Guide

## Overview

This guide covers setting up the development environment, coding standards, testing procedures, and contribution guidelines for the Real-Time Moderation System.

## Development Environment Setup

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose**
- **Git**
- **Make** (optional, for convenience commands)
- **Node.js 18+** (for frontend development, if applicable)

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd moderation-system
   ```

2. **Setup Python Environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

3. **Setup Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Start Development Services**
   ```bash
   make dev-setup
   make up
   ```

## Project Structure

```
moderation-system/
├── services/                 # Microservices
│   ├── mcp-server/          # Model Context Protocol Server
│   ├── chat-simulator/      # Chat simulation service
│   ├── lightweight-filter/  # Preprocessing filter
│   ├── decision-handler/    # Policy enforcement
│   └── metrics-evaluator/   # Monitoring service
├── shared/                  # Shared libraries and templates
├── deployment/              # Docker and K8s configurations
├── monitoring/              # Observability configurations
├── tests/                   # Test suites
├── docs/                    # Documentation
└── scripts/                 # Utility scripts
```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with some modifications:

```python
# Line length: 88 characters (Black default)
# Use type hints for all functions
def process_message(message: str, user_id: str) -> Dict[str, Any]:
    """Process a chat message for moderation.
    
    Args:
        message: The chat message to process
        user_id: Unique identifier for the user
        
    Returns:
        Dictionary containing moderation results
        
    Raises:
        ValidationError: If message format is invalid
    """
    pass

# Use dataclasses for data structures
@dataclass
class ModerationResult:
    decision: str
    confidence: float
    reasoning: Optional[str] = None
```

### Code Formatting

We use **Black** for code formatting and **isort** for import sorting:

```bash
# Format code
make format

# Check formatting
make lint
```

### Configuration Files

- **YAML**: Use 2-space indentation
- **JSON**: Use 2-space indentation
- **Environment Variables**: Use UPPER_CASE with underscores

## Development Workflow

### Feature Development

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Develop and Test**
   ```bash
   # Run tests continuously during development
   pytest --watch
   
   # Run specific service tests
   pytest tests/test_mcp_server.py -v
   ```

3. **Code Quality Checks**
   ```bash
   make lint      # Run linting
   make test      # Run all tests
   make security-scan  # Security checks
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new moderation template"
   ```

### Commit Message Convention

We use **Conventional Commits**:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(mcp-server): add harassment detection template
fix(filter): resolve rate limiting edge case
docs: update API documentation
test(simulator): add WebSocket connection tests
```

## Testing

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_mcp_server.py
│   ├── test_filter.py
│   └── test_simulator.py
├── integration/             # Integration tests
│   ├── test_pipeline.py
│   └── test_api_integration.py
├── load/                    # Load tests
│   └── test_performance.py
└── e2e/                     # End-to-end tests
    └── test_full_pipeline.py
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/load/ -v

# Run with coverage
pytest --cov=services --cov-report=html

# Run tests in parallel
pytest -n auto
```

### Writing Tests

#### Unit Test Example

```python
import pytest
from unittest.mock import AsyncMock, patch
from services.mcp_server.app.main import MCPServer, ModerationRequest

@pytest.fixture
def mcp_server():
    return MCPServer()

@pytest.fixture
def sample_request():
    return ModerationRequest(
        message="Hello world",
        user_id="user_123",
        channel_id="general"
    )

@pytest.mark.asyncio
async def test_process_moderation_request(mcp_server, sample_request):
    """Test basic moderation request processing."""
    with patch.object(mcp_server.llm_client, 'generate_response') as mock_llm:
        mock_llm.return_value = {
            "content": '{"decision": "Non-Toxic", "confidence": 0.95}',
            "duration": 0.1
        }
        
        result = await mcp_server.process_moderation_request(sample_request)
        
        assert result.decision == "Non-Toxic"
        assert result.confidence == 0.95
        assert result.processing_time_ms > 0
```

#### Integration Test Example

```python
import pytest
import httpx
from testcontainers import DockerComposeContainer

@pytest.fixture(scope="session")
def docker_services():
    """Start services using docker-compose for integration tests."""
    with DockerComposeContainer(".", compose_file_name="docker-compose.test.yml") as compose:
        yield compose

@pytest.mark.asyncio
async def test_full_moderation_pipeline(docker_services):
    """Test complete moderation pipeline."""
    async with httpx.AsyncClient() as client:
        # Send message to filter
        filter_response = await client.post(
            "http://localhost:8001/filter",
            json={
                "user_id": "test_user",
                "username": "TestUser",
                "channel_id": "test",
                "message": "This is a test message",
                "timestamp": "2024-01-01T12:00:00Z"
            }
        )
        assert filter_response.status_code == 200
        
        # Send to MCP server if filter allows
        if filter_response.json()["should_process"]:
            mcp_response = await client.post(
                "http://localhost:8000/moderate",
                json={
                    "message": "This is a test message",
                    "user_id": "test_user",
                    "channel_id": "test"
                }
            )
            assert mcp_response.status_code == 200
```

### Load Testing

```python
# tests/load/test_performance.py
import asyncio
import time
from locust import HttpUser, task, between

class ModerationUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def moderate_normal_message(self):
        """Test normal message moderation."""
        self.client.post("/moderate", json={
            "message": "Hello everyone!",
            "user_id": f"user_{self.user_id}",
            "channel_id": "general"
        })
    
    @task(1)
    def moderate_toxic_message(self):
        """Test toxic message moderation."""
        self.client.post("/moderate", json={
            "message": "You are terrible at this game",
            "user_id": f"user_{self.user_id}",
            "channel_id": "gaming"
        })

# Run load test
# locust -f tests/load/test_performance.py --host=http://localhost:8000
```

## Debugging

### Local Debugging

1. **Service Logs**
   ```bash
   # View all logs
   make logs
   
   # View specific service logs
   docker-compose logs -f mcp-server
   docker-compose logs -f chat-simulator
   ```

2. **Debug Mode**
   ```bash
   # Set debug environment
   export DEBUG=true
   export LOG_LEVEL=DEBUG
   
   # Run service in debug mode
   cd services/mcp-server
   python -m uvicorn app.main:app --reload --log-level debug
   ```

3. **Interactive Debugging**
   ```python
   # Add breakpoints in code
   import pdb; pdb.set_trace()
   
   # Or use ipdb for better experience
   import ipdb; ipdb.set_trace()
   ```

### Performance Profiling

```python
# Profile specific functions
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    result = expensive_function()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
    
    return result
```

## Database Development

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Database Testing

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def db_container():
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture
def db_session(db_container):
    engine = create_engine(db_container.get_connection_url())
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
```

## Monitoring and Observability

### Adding Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active WebSocket connections')

# Use in code
@REQUEST_DURATION.time()
def process_request():
    REQUEST_COUNT.labels(method='POST', endpoint='/moderate').inc()
    # Process request
    pass
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

# Log with context
logger.info(
    "Processing moderation request",
    user_id=user_id,
    message_length=len(message),
    template_name=template_name,
    processing_time_ms=processing_time
)
```

## Configuration Management

### Environment-Specific Configs

```python
# config.py
import os
from typing import Optional

class Settings:
    # LLM Configuration
    llm_endpoint: str = os.getenv("LLM_ENDPOINT", "http://localhost:8080")
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "30.0"))
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    
    # Feature Flags
    enable_filter: bool = os.getenv("ENABLE_FILTER", "true").lower() == "true"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Template Development

```yaml
# shared/templates/new_template.yaml
new_template:
  name: "new_template"
  version: "1.0"
  description: "Description of the new template"
  safety_level: "medium"
  expected_output: "json"
  prompt: |
    Your prompt template here with variables like {chat_message}
    
    Respond with JSON:
    {
      "decision": "[Category]",
      "confidence": 0.95,
      "reasoning": "explanation"
    }
```

## Deployment and CI/CD

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    - name: Run tests
      run: |
        pytest --cov=services --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Troubleshooting Common Issues

### Import Errors
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Docker Issues
```bash
# Clean up Docker resources
make clean

# Rebuild without cache
docker-compose build --no-cache
```

### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec postgres psql -U postgres -d moderation_db -c "SELECT 1;"
```

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Update documentation
7. Submit pull request

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

This development guide provides comprehensive information for contributing to and maintaining the Real-Time Moderation System.
