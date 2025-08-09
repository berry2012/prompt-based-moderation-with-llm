# Kubernetes Deployment

This directory contains all the Kubernetes manifests and deployment scripts for the Real-Time Moderation System.

## 📁 Directory Structure

```
kubernetes/
├── 00-namespace.yaml              # Namespace and RBAC
├── configmaps/                    # Application configuration
│   ├── moderation-config.yaml     # Main app config
│   └── monitoring-config.yaml     # Prometheus/Grafana config
├── secrets/                       # Sensitive configuration
│   └── moderation-secrets.yaml    # Secrets template
├── deployments/                   # Application deployments
│   ├── postgres.yaml              # PostgreSQL database
│   ├── redis.yaml                 # Redis cache
│   ├── mcp-server.yaml            # MCP Server
│   ├── lightweight-filter.yaml    # Lightweight Filter
│   ├── chat-simulator.yaml        # Chat Simulator
│   ├── decision-handler.yaml      # Decision Handler
│   ├── monitoring.yaml            # Prometheus & Grafana
│   └── hpa.yaml                   # Horizontal Pod Autoscaler
├── services/                      # Kubernetes services
│   └── services.yaml              # All service definitions
├── ingress/                       # Ingress configuration
│   └── ingress.yaml               # ALB ingress
├── network-policies.yaml          # Network security policies
├── deploy.sh                      # Deployment script
├── deepseek/                      # Your DeepSeek LLM manifests
│   ├── deepseek-deployment.yaml   # DeepSeek deployment
│   └── gpu-nodepool.yaml          # GPU nodepool config
└── README.md                      # This file
```

## 🚀 Quick Deployment

### Prerequisites

1. **EKS Cluster**: Your existing EKS cluster with custom nodepool
2. **kubectl**: Configured to access your cluster
3. **Container Images**: Built and pushed to your registry
4. **DeepSeek LLM**: Already deployed in `deepseek` namespace

### Deploy Everything

```bash
# Navigate to kubernetes directory
cd deployment/kubernetes

# Run the deployment script
./deploy.sh deploy
```

### Check Status

```bash
# Check deployment status
./deploy.sh status

# Run health checks
./deploy.sh health
```

## 🔧 Manual Deployment Steps

If you prefer to deploy manually:

### 1. Create Namespace and RBAC

```bash
kubectl apply -f 00-namespace.yaml
```

### 2. Create Secrets

**Important**: Update the secrets with your actual values first!

```bash
# Edit secrets with your values
kubectl create secret generic moderation-secrets \
  --from-literal=postgres-password=YOUR_PASSWORD \
  --from-literal=postgres-user=postgres \
  --from-literal=api-key=YOUR_API_KEY \
  --from-literal=notification-webhook=YOUR_WEBHOOK_URL \
  -n moderation-system

# Or apply the template (update base64 values first)
kubectl apply -f secrets/moderation-secrets.yaml
```

### 3. Create ConfigMaps

```bash
kubectl apply -f configmaps/
```

### 4. Deploy Infrastructure

```bash
# Deploy PostgreSQL and Redis
kubectl apply -f deployments/postgres.yaml
kubectl apply -f deployments/redis.yaml

# Wait for them to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres -n moderation-system
kubectl wait --for=condition=available --timeout=300s deployment/redis -n moderation-system
```

### 5. Deploy Application Services

**Update image references first:**

```bash
# Update image registry in deployment files
sed -i 's|your-registry|YOUR_ACTUAL_REGISTRY|g' deployments/*.yaml
```

```bash
# Deploy application services
kubectl apply -f deployments/mcp-server.yaml
kubectl apply -f deployments/lightweight-filter.yaml
kubectl apply -f deployments/chat-simulator.yaml
kubectl apply -f deployments/decision-handler.yaml

# Wait for deployments
kubectl wait --for=condition=available --timeout=300s deployment --all -n moderation-system
```

### 6. Create Services

```bash
kubectl apply -f services/services.yaml
```

### 7. Deploy Monitoring

```bash
kubectl apply -f deployments/monitoring.yaml
```

### 8. Create HPA and Network Policies

```bash
kubectl apply -f deployments/hpa.yaml
kubectl apply -f network-policies.yaml
```

### 9. Create Ingress (Optional)

Update domain names in `ingress/ingress.yaml` first:

```bash
kubectl apply -f ingress/ingress.yaml
```

## 🔍 Verification

### Check Pod Status

```bash
kubectl get pods -n moderation-system
```

### Check Services

```bash
kubectl get services -n moderation-system
```

### Check Ingress

```bash
kubectl get ingress -n moderation-system
```

### View Logs

```bash
# View logs for specific service
kubectl logs -f deployment/mcp-server -n moderation-system

# View logs for all services
kubectl logs -f -l app.kubernetes.io/name=moderation-system -n moderation-system
```

## 🌐 Access Points

### External Access (LoadBalancer)

```bash
# Get external IPs
kubectl get services -n moderation-system -o wide

# Chat Simulator
CHAT_SIMULATOR_IP=$(kubectl get service chat-simulator-service -n moderation-system -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Chat Simulator: http://$CHAT_SIMULATOR_IP:8002"

# Grafana
GRAFANA_IP=$(kubectl get service grafana-service -n moderation-system -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "Grafana: http://$GRAFANA_IP:3000"
```

### Internal Access (Port Forward)

```bash
# MCP Server
kubectl port-forward service/mcp-server-service 8000:8000 -n moderation-system

# Lightweight Filter
kubectl port-forward service/lightweight-filter-service 8001:8001 -n moderation-system

# Decision Handler
kubectl port-forward service/decision-handler-service 8003:8003 -n moderation-system

# Prometheus
kubectl port-forward service/prometheus-service 9090:9090 -n moderation-system
```

## 🔧 Configuration

### Update Container Images

1. Build and push your images:
   ```bash
   docker build -t your-registry/mcp-server:v1.0.0 services/mcp-server/
   docker push your-registry/mcp-server:v1.0.0
   ```

2. Update deployment files:
   ```bash
   kubectl set image deployment/mcp-server mcp-server=your-registry/mcp-server:v1.0.0 -n moderation-system
   ```

### Update Secrets

```bash
# Update database password
kubectl patch secret moderation-secrets -n moderation-system -p='{"data":{"postgres-password":"'$(echo -n "new-password" | base64)'"}}'

# Update DeepSeek endpoint
kubectl patch secret deepseek-connection -n moderation-system -p='{"stringData":{"llm-endpoint":"http://new-endpoint/v1/chat/completions"}}'
```

### Update Configuration

```bash
# Update config map
kubectl patch configmap moderation-config -n moderation-system -p='{"data":{"log-level":"DEBUG"}}'

# Restart deployments to pick up changes
kubectl rollout restart deployment/mcp-server -n moderation-system
```

## 📊 Monitoring

### Grafana Dashboards

1. Access Grafana: http://GRAFANA_IP:3000
2. Login: admin/admin
3. Navigate to Dashboards → Moderation System Dashboard

### Prometheus Metrics

Access Prometheus: http://PROMETHEUS_IP:9090

Key metrics to monitor:
- `mcp_requests_total` - Request count by endpoint and status
- `mcp_request_duration_seconds` - Request latency
- `llm_response_time_seconds` - LLM response time

### Alerts

The system includes pre-configured alerts for:
- High error rates
- High latency
- LLM service down
- Database connection failures

## 🔒 Security

### Network Policies

Network policies are configured to:
- Allow communication within the moderation-system namespace
- Allow communication with DeepSeek LLM in deepseek namespace
- Restrict database access to decision-handler only
- Allow ingress from ALB controller

### RBAC

Service accounts have minimal required permissions:
- Read access to pods, services, configmaps
- No cluster-wide permissions

### Secrets Management

- All sensitive data stored in Kubernetes secrets
- Secrets are base64 encoded (not encrypted by default)
- Consider using AWS Secrets Manager or External Secrets Operator for production

## 🚨 Troubleshooting

### Common Issues

1. **Pods not starting**:
   ```bash
   kubectl describe pod POD_NAME -n moderation-system
   kubectl logs POD_NAME -n moderation-system
   ```

2. **Service not accessible**:
   ```bash
   kubectl get endpoints -n moderation-system
   kubectl describe service SERVICE_NAME -n moderation-system
   ```

3. **DeepSeek connection issues**:
   ```bash
   # Test connectivity from MCP server pod
   kubectl exec -it deployment/mcp-server -n moderation-system -- curl http://deepseek-svc.deepseek.svc.cluster.local/health
   ```

4. **Database connection issues**:
   ```bash
   # Check PostgreSQL logs
   kubectl logs deployment/postgres -n moderation-system
   
   # Test connection
   kubectl exec -it deployment/postgres -n moderation-system -- psql -U postgres -d moderation_db -c "SELECT 1;"
   ```

### Scaling Issues

```bash
# Check HPA status
kubectl get hpa -n moderation-system

# Check resource usage
kubectl top pods -n moderation-system
kubectl top nodes
```

### Performance Issues

```bash
# Check resource limits
kubectl describe pod POD_NAME -n moderation-system

# Check metrics
kubectl port-forward service/prometheus-service 9090:9090 -n moderation-system
# Then visit http://localhost:9090
```

## 🧹 Cleanup

### Delete Everything

```bash
./deploy.sh clean
```

### Delete Specific Components

```bash
# Delete application deployments only
kubectl delete deployment --all -n moderation-system

# Delete services
kubectl delete service --all -n moderation-system

# Delete the entire namespace
kubectl delete namespace moderation-system
```

## 🔄 Updates and Maintenance

### Rolling Updates

```bash
# Update image version
kubectl set image deployment/mcp-server mcp-server=your-registry/mcp-server:v1.1.0 -n moderation-system

# Check rollout status
kubectl rollout status deployment/mcp-server -n moderation-system

# Rollback if needed
kubectl rollout undo deployment/mcp-server -n moderation-system
```

### Backup

```bash
# Backup database
kubectl exec deployment/postgres -n moderation-system -- pg_dump -U postgres moderation_db > backup.sql

# Backup configurations
kubectl get all,configmap,secret -n moderation-system -o yaml > moderation-system-backup.yaml
```

This deployment is specifically configured to work with your existing EKS cluster setup, including the custom nodepool with `owner: "data-engineer"` node selector and the DeepSeek LLM deployment in the `deepseek` namespace.
