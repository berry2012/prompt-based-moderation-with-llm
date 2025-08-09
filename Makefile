# Moderation System Makefile

.PHONY: help build up down logs clean test lint format deploy-k8s

# Default target
help:
	@echo "Available commands:"
	@echo "  build          - Build all Docker images"
	@echo "  up             - Start all services with Docker Compose"
	@echo "  down           - Stop all services"
	@echo "  logs           - Show logs from all services"
	@echo "  clean          - Clean up Docker resources"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linting"
	@echo "  format         - Format code"
	@echo "  deploy-k8s     - Deploy to Kubernetes"
	@echo "  monitor        - Open monitoring dashboards"

# Docker Compose commands
build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started. Access points:"
	@echo "  - MCP Server: http://localhost:8000"
	@echo "  - Lightweight Filter: http://localhost:8001"
	@echo "  - Chat Simulator: http://localhost:8002"
	@echo "  - Decision Handler: http://localhost:8003"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"

down:
	@echo "Stopping services..."
	docker-compose down

logs:
	docker-compose logs -f

clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

# Development commands
test:
	@echo "Running tests..."
	python -m pytest tests/ -v

lint:
	@echo "Running linting..."
	flake8 services/
	black --check services/
	isort --check-only services/

format:
	@echo "Formatting code..."
	black services/
	isort services/

# Kubernetes deployment
deploy-k8s:
	@echo "Deploying to Kubernetes..."
	kubectl apply -f deployment/kubernetes/
	@echo "Waiting for deployments to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment --all -n moderation-system

# Monitoring
monitor:
	@echo "Opening monitoring dashboards..."
	@echo "Grafana: http://localhost:3000"
	@echo "Prometheus: http://localhost:9090"
	@echo "Jaeger: http://localhost:16686"

# Development setup
dev-setup:
	@echo "Setting up development environment..."
	python -m venv venv
	source venv/bin/activate && pip install -r requirements.txt
	cp .env.example .env
	@echo "Development environment ready!"

# Load testing
load-test:
	@echo "Running load tests..."
	python tests/load/load_test.py

# Database operations
db-migrate:
	@echo "Running database migrations..."
	docker-compose exec decision-handler python -m alembic upgrade head

db-reset:
	@echo "Resetting database..."
	docker-compose exec postgres psql -U postgres -d moderation_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) db-migrate

# Backup and restore
backup:
	@echo "Creating backup..."
	docker-compose exec postgres pg_dump -U postgres moderation_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore:
	@echo "Restoring from backup..."
	@read -p "Enter backup file name: " backup_file; \
	docker-compose exec -T postgres psql -U postgres moderation_db < $$backup_file

# Security scanning
security-scan:
	@echo "Running security scans..."
	docker run --rm -v $(PWD):/app securecodewarrior/docker-security-scanner /app

# Performance monitoring
perf-monitor:
	@echo "Starting performance monitoring..."
	docker-compose exec prometheus curl -X POST http://localhost:9090/-/reload

# Quick start for demo
demo:
	@echo "Starting demo environment..."
	$(MAKE) build
	$(MAKE) up
	sleep 10
	@echo "Starting chat simulation..."
	curl -X POST http://localhost:8002/simulate/start
	@echo "Demo is running! Check Grafana at http://localhost:3000"

# Stop demo
demo-stop:
	curl -X POST http://localhost:8002/simulate/stop
	$(MAKE) down
