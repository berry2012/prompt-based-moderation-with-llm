# Deployment Guide

## Overview

This guide covers deploying the Real-Time Moderation System in various environments, from local development to production Kubernetes clusters.

## Prerequisites

### Local Development
- Docker & Docker Compose
- Python 3.11+
- Make (optional, for convenience commands)

### Production Deployment
- Kubernetes cluster (EKS recommended)
- kubectl configured
- Helm 3.x (optional)
- Container registry access
- PostgreSQL database
- Redis instance

## Local Development Deployment

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository>
   cd moderation-system
   cp .env.example .env
   ```

2. **Configure Environment**
   Edit `.env` file with your settings:
   ```bash
   # Update with your DeepSeek LLM endpoint
   LLM_ENDPOINT=http://your-deepseek-llm:8080/v1/chat/completions
   
   # Database settings
   DATABASE_URL=postgresql://postgres:password@postgres:5432/moderation_db
   
   # Notification webhook (optional)
   NOTIFICATION_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

3. **Start Services**
   ```bash
   make demo
   # OR manually:
   make build
   make up
   ```

4. **Verify Deployment**
   ```bash
   # Check service health
   curl http://localhost:8000/health  # MCP Server
   curl http://localhost:8001/health  # Lightweight Filter
   curl http://localhost:8002/health  # Chat Simulator
   
   # View logs
   make logs
   ```

### Access Points
- **MCP Server**: http://localhost:8000
- **Chat Simulator**: http://localhost:8002
- **Lightweight Filter**: http://localhost:8001
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## Production Kubernetes Deployment

### 1. Prepare Your EKS Cluster

Since you already have an EKS cluster with DeepSeek LLM deployed:

```bash
# Verify cluster access
kubectl get nodes

# Check your custom nodepool
kubectl get nodes -l role=custom-workload
```

### 2. Build and Push Container Images

```bash
# Build images
make build

# Tag for your registry
docker tag moderation-system/mcp-server:latest YOUR_REGISTRY/mcp-server:v1.0.0
docker tag moderation-system/chat-simulator:latest YOUR_REGISTRY/chat-simulator:v1.0.0
docker tag moderation-system/lightweight-filter:latest YOUR_REGISTRY/lightweight-filter:v1.0.0

# Push to registry
docker push YOUR_REGISTRY/mcp-server:v1.0.0
docker push YOUR_REGISTRY/chat-simulator:v1.0.0
docker push YOUR_REGISTRY/lightweight-filter:v1.0.0
```

### 3. Configure Kubernetes Manifests

Update the Kubernetes manifests with your specific configuration:

```bash
# Create namespace
kubectl create namespace moderation-system

# Create secrets
kubectl create secret generic moderation-secrets \
  --from-literal=postgres-password=YOUR_PASSWORD \
  --from-literal=llm-api-key=YOUR_API_KEY \
  -n moderation-system

# Create configmap for templates
kubectl create configmap prompt-templates \
  --from-file=shared/templates/ \
  -n moderation-system
```

### 4. Deploy to Your Custom Nodepool

Update the deployment manifests to use your custom nodepool:

```yaml
# In deployment/kubernetes/deployments/mcp-server.yaml
spec:
  template:
    spec:
      nodeSelector:
        role: custom-workload
      tolerations:
      - key: dedicated
        operator: Equal
        value: custom-workload
        effect: NoSchedule
```

### 5. Deploy Services

```bash
# Deploy all components
kubectl apply -f deployment/kubernetes/

# Wait for deployments
kubectl wait --for=condition=available --timeout=300s deployment --all -n moderation-system

# Check status
kubectl get pods -n moderation-system
```

### 6. Configure Load Balancer

```bash
# Get external IP for chat simulator (if using LoadBalancer)
kubectl get svc chat-simulator-service -n moderation-system

# Or setup ingress
kubectl apply -f deployment/kubernetes/ingress/
```

## Helm Deployment (Alternative)

### 1. Install with Helm

```bash
# Add custom values
cat > values-production.yaml << EOF
image:
  registry: YOUR_REGISTRY
  tag: v1.0.0

llm:
  endpoint: http://deepseek-llm-service:8080/v1/chat/completions

database:
  host: your-postgres-host
  password: your-password

nodeSelector:
  role: custom-workload

tolerations:
- key: dedicated
  operator: Equal
  value: custom-workload
  effect: NoSchedule
EOF

# Deploy
helm install moderation-system ./deployment/helm \
  -f values-production.yaml \
  -n moderation-system \
  --create-namespace
```

## Database Setup

### PostgreSQL Configuration

```sql
-- Create database and user
CREATE DATABASE moderation_db;
CREATE USER moderation_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE moderation_db TO moderation_user;

-- Connect to moderation_db and create tables
\c moderation_db;

-- Tables will be created automatically by the application
-- Or run migrations manually:
-- kubectl exec -it deployment/decision-handler -n moderation-system -- python -m alembic upgrade head
```

### Redis Configuration

```bash
# If using managed Redis (ElastiCache)
REDIS_URL=redis://your-elasticache-endpoint:6379/0

# Or deploy Redis in cluster
kubectl apply -f - << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: moderation-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
EOF
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'moderation-system'
    kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
        - moderation-system
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
```

### Grafana Dashboards

```bash
# Import dashboards
kubectl create configmap grafana-dashboards \
  --from-file=monitoring/grafana/dashboards/ \
  -n moderation-system
```

## Security Configuration

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: moderation-network-policy
  namespace: moderation-system
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: moderation-system
```

### RBAC

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: moderation-service-account
  namespace: moderation-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: moderation-role
  namespace: moderation-system
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
```

## Scaling Configuration

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mcp-server-hpa
  namespace: moderation-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mcp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Backup and Recovery

### Database Backup

```bash
# Create backup job
kubectl create job --from=cronjob/postgres-backup postgres-backup-manual -n moderation-system

# Manual backup
kubectl exec -it postgres-0 -n moderation-system -- pg_dump -U postgres moderation_db > backup.sql
```

### Configuration Backup

```bash
# Backup all configurations
kubectl get all,configmap,secret -n moderation-system -o yaml > moderation-system-backup.yaml
```

## Troubleshooting

### Common Issues

1. **LLM Connection Issues**
   ```bash
   # Check LLM service connectivity
   kubectl exec -it deployment/mcp-server -n moderation-system -- curl http://deepseek-llm-service:8080/health
   ```

2. **Database Connection Issues**
   ```bash
   # Check database connectivity
   kubectl exec -it deployment/decision-handler -n moderation-system -- pg_isready -h postgres-service -p 5432
   ```

3. **Pod Scheduling Issues**
   ```bash
   # Check node selector and tolerations
   kubectl describe pod <pod-name> -n moderation-system
   ```

### Logs and Debugging

```bash
# View logs
kubectl logs -f deployment/mcp-server -n moderation-system
kubectl logs -f deployment/chat-simulator -n moderation-system

# Debug pod issues
kubectl describe pod <pod-name> -n moderation-system
kubectl exec -it <pod-name> -n moderation-system -- /bin/bash
```

## Performance Tuning

### Resource Limits

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Connection Pooling

```python
# Database connection pool settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

## Maintenance

### Rolling Updates

```bash
# Update image
kubectl set image deployment/mcp-server mcp-server=YOUR_REGISTRY/mcp-server:v1.1.0 -n moderation-system

# Check rollout status
kubectl rollout status deployment/mcp-server -n moderation-system
```

### Health Checks

```bash
# Automated health check script
#!/bin/bash
NAMESPACE="moderation-system"
SERVICES=("mcp-server" "chat-simulator" "lightweight-filter")

for service in "${SERVICES[@]}"; do
  kubectl exec deployment/$service -n $NAMESPACE -- curl -f http://localhost:8000/health
done
```

This deployment guide provides comprehensive instructions for deploying the moderation system in your existing EKS environment with the custom nodepool configuration.
