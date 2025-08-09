# Real-Time Moderation System

A comprehensive real-time moderation system for streaming chat applications using Large Language Models, designed to integrate with your existing DeepSeek LLM deployment on Kubernetes.

## 🏗️ Architecture Overview

This system provides modular, scalable content moderation with the following components:

- **MCP Server**: Model Context Protocol server for LLM interactions
- **Lightweight Filter**: Fast preprocessing to reduce LLM costs
- **Chat Simulator**: Realistic chat simulation for testing
- **Decision Handler**: Policy enforcement and action execution
- **Metrics Evaluator**: Comprehensive monitoring and evaluation

### System Architecture Diagrams

- **[Detailed Architecture Diagram](docs/ARCHITECTURE_DIAGRAM.md)** - Comprehensive system design with data flows
- **[Mermaid Diagrams](docs/MERMAID_DIAGRAMS.md)** - Interactive diagrams for GitHub/web rendering
- **[ASCII Architecture](docs/ASCII_ARCHITECTURE.md)** - Text-based diagrams for quick reference

## 🚀 Quick Start

### 🚀 Local Implementation Steps

### **Prerequisites**
```bash
# Install Docker and Docker Compose
# macOS (using Homebrew)
brew install docker docker-compose

# Verify installations
docker --version
docker-compose --version
```

### **Phase 1: Project Setup**

#### **1. Clone and Navigate to Project**
```bash
# Navigate to your project directory
cd /path/to/moderation-system

# Verify project structure
ls -la
```

#### **2. Configure Environment Variables**
```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your DeepSeek LLM endpoint
nano .env
```

Update `.env` with your actual DeepSeek endpoint:
```bash
# LLM Configuration - Replace with your actual DeepSeek endpoint
LLM_ENDPOINT=http://your-deepseek-endpoint.com/v1/chat/completions
LLM_TIMEOUT=30.0
LLM_MAX_RETRIES=3

# Service Configuration (Docker internal networking)
MCP_ENDPOINT=http://mcp-server:8000
FILTER_ENDPOINT=http://lightweight-filter:8001
DECISION_ENDPOINT=http://decision-handler:8003

# Database Configuration
DATABASE_URL=postgresql://postgres:password@postgres:5432/moderation_db
REDIS_URL=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
DEBUG=true

# Feature Flags
ENABLE_LIGHTWEIGHT_FILTER=true
ENABLE_WHISPER=false
ENABLE_METRICS=true
```

### **Phase 2: Test External Dependencies**

#### **3. Verify DeepSeek LLM Connection**
```bash
# Test your DeepSeek endpoint and get available models
curl -s "http://your-deepseek-endpoint.com/v1/models" | jq '.'

# Test chat completions with the correct model name
curl -X POST "http://your-deepseek-endpoint.com/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-ai/DeepSeek-R1-Distill-Llama-8B",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, respond with: {\"status\": \"working\"}"}
    ],
    "temperature": 0.1,
    "max_tokens": 50
  }'
```

### **Phase 3: Build and Deploy System**

#### **4. Build All Services**
```bash
# Build all Docker images
docker-compose build

# Or build specific services
docker-compose build mcp-server
docker-compose build lightweight-filter
docker-compose build chat-simulator
```

#### **5. Start Infrastructure Services**
```bash
# Start database and monitoring services
docker-compose up -d postgres redis prometheus grafana

# Wait for services to initialize
sleep 30

# Verify infrastructure is running
docker-compose ps
```

#### **6. Start Core Moderation Services**
```bash
# Start the moderation pipeline
docker-compose up -d mcp-server lightweight-filter decision-handler metrics-evaluator

# Check service health
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8001/health  # Lightweight Filter
curl http://localhost:8003/health  # Decision Handler
```

#### **7. Start Chat Simulator with WebUI**
```bash
# Start the chat simulator
docker-compose up -d chat-simulator

# Verify it's running
curl http://localhost:8002/health

# Check all services are running
docker-compose ps
```

### **Phase 4: System Testing**

#### **8. Test Individual Components**
```bash
# Test MCP Server moderation
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{
    "message": "You are the worst human being, you make me sick to my stomach.",
    "user_id": "test_user",
    "channel_id": "general"
  }'

# Test Chat Simulator API
curl -X POST http://localhost:8002/api/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello everyone, how are you doing today?",
    "user_id": "test_user",
    "username": "TestUser",
    "channel_id": "general"
  }' | jq .
```

#### **9. Access System Interfaces**
```bash
# Open WebUI and monitoring dashboards
open http://localhost:8002    # Chat Simulator WebUI
open http://localhost:3000    # Grafana (admin/admin)
open http://localhost:9090    # Prometheus
```

### **Phase 5: End-to-End Validation**

#### **10. Test Message Types**
```bash
# Test different message types through the API
# Normal message
curl -X POST http://localhost:8002/api/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello everyone, how are you doing today?",
    "user_id": "normal_user",
    "username": "NormalUser",
    "channel_id": "general"
  }' | jq '.result.moderation_result'

# Toxic message
curl -X POST http://localhost:8002/api/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "You are the worst human being, you make me sick to my stomach.",
    "user_id": "toxic_user",
    "username": "ToxicUser",
    "channel_id": "general"
  }' | jq '.result.moderation_result'
```

#### **11. WebUI Interactive Testing**
1. Navigate to http://localhost:8002
2. Type messages in the chat interface
3. Observe real-time moderation results
4. Check statistics: Total Messages, Approved, Flagged
5. Test voice recording feature (simulated)

### **Phase 6: Monitoring and Debugging**

#### **12. Monitor System Health**
```bash
# View service logs
docker-compose logs -f mcp-server
docker-compose logs -f chat-simulator
docker-compose logs -f lightweight-filter

# Check resource usage
docker stats

# View all service status
docker-compose ps
```

#### **13. Debug Issues**
```bash
# Access container shells for debugging
docker-compose exec mcp-server /bin/bash
docker-compose exec chat-simulator /bin/bash

# Check database connectivity
docker-compose exec postgres psql -U postgres -d moderation_db

# Restart specific services if needed
docker-compose restart mcp-server
docker-compose restart chat-simulator
```

### **Phase 7: Performance Validation**

#### **14. Load Testing**
```bash
# Test multiple concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8002/api/send-message \
    -H "Content-Type: application/json" \
    -d "{
      \"message\": \"Test message $i\",
      \"user_id\": \"load_test_$i\",
      \"username\": \"LoadTest$i\",
      \"channel_id\": \"test\"
    }" &
done
wait
```

#### **15. Monitor Performance Metrics**
- **Grafana Dashboard**: http://localhost:3000
  - Request rates and response times
  - Error rates and success rates
  - Resource utilization
- **Prometheus Metrics**: http://localhost:9090
  - Raw metrics and queries
  - Service health indicators

## 🎯 Quick Start Summary

For the fastest setup:

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your DeepSeek endpoint

# 2. Build and start all services
docker-compose build
docker-compose up -d

# 3. Wait for services to initialize
sleep 60

# 4. Test the system
curl http://localhost:8002/health

# 5. Access WebUI
open http://localhost:8002
```

## 🔍 Troubleshooting

```bash
# If services fail to start
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# If DeepSeek connection fails
curl -v http://your-deepseek-endpoint.com/v1/models

# If moderation requests timeout
# Check MCP server logs and increase timeout in .env:
# REQUEST_TIMEOUT=30.0

# Clean restart
docker-compose down -v
docker-compose build
docker-compose up -d
```

## 📊 Expected Results

After successful deployment:
- **All services healthy**: `docker-compose ps` shows all services as "Up"
- **WebUI accessible**: http://localhost:8002 loads the chat interface
- **Moderation working**: Toxic messages flagged, normal messages approved
- **Real-time stats**: WebUI shows accurate message counts and processing times
- **Monitoring active**: Grafana dashboards display system metrics

## 🌐 Interactive WebUI

The Chat Simulator now includes a comprehensive web interface for interactive testing and monitoring:

### **WebUI Features:**
- **Real-time Chat Interface**: Interactive chat simulation with live moderation
- **Voice Recording**: Browser-based audio input (simulated transcription)
- **Message Type Testing**: Test Normal, Toxic, Spam, and PII content
- **Live Statistics**: Real-time monitoring of moderation performance
- **WebSocket Updates**: Live message streaming and status updates
- **Responsive Design**: Mobile-friendly interface for any device
- **Processing Analytics**: Monitor response times and accuracy

### **Quick WebUI Setup:**
```bash
# WebUI is automatically available after starting chat-simulator
docker-compose up -d chat-simulator

# Access WebUI
open http://localhost:8002
```

### **WebUI Access Points:**
- **Main Interface**: http://localhost:8002
- **WebSocket**: ws://localhost:8002/ws
- **API Endpoint**: http://localhost:8002/api/send-message
- **Health Check**: http://localhost:8002/health

## 📊 Access Points

- **Chat Simulator WebUI**: http://localhost:8002
- **MCP Server**: http://localhost:8000
- **Lightweight Filter**: http://localhost:8001
- **Decision Handler**: http://localhost:8003
- **Metrics Evaluator**: http://localhost:8004
- **Grafana Dashboard**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

## 🔧 Configuration

Copy the example environment file and customize:
```bash
cp .env.example .env
```

Key configurations:
- `LLM_ENDPOINT`: Your DeepSeek LLM endpoint
- `LLM_TIMEOUT`: Request timeout (default: 30.0 seconds)
- `REQUEST_TIMEOUT`: HTTP client timeout (default: 30.0 seconds)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

## 📁 Directory Structure

```
moderation-system/
├── services/           # Microservices
├── shared/            # Shared libraries and templates
├── deployment/        # Docker and Kubernetes configs
├── monitoring/        # Prometheus, Grafana, Jaeger
├── tests/            # Integration and load tests
├── docs/             # Complete documentation
└── logs/             # Application logs
```

## 🎯 Performance

- **Latency**: 7-10 seconds per message (LLM processing time)
- **Throughput**: Configurable based on LLM capacity
- **Accuracy**: 95% confidence on toxic content detection
- **Cost Optimization**: ~60% reduction in LLM calls via lightweight filtering

## 📖 Documentation

- [System Architecture](SYSTEM_ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Architecture Diagrams](docs/ARCHITECTURE_DIAGRAM.md)

## 🔒 Security

- Input validation and prompt injection protection
- Rate limiting and abuse prevention
- Network policies and secrets management
- Comprehensive audit logging

## 📈 Monitoring

- Real-time metrics and alerting
- Performance dashboards via Grafana
- Accuracy evaluation and tracking
- Resource usage monitoring

## 🎨 Generate Architecture Diagrams

To generate visual architecture diagrams:

```bash
# Install matplotlib if not already installed
pip install matplotlib

# Generate diagrams
cd scripts
python generate_architecture_diagram.py
```

This will create PNG and PDF versions of the architecture diagrams in `docs/images/`.

## ☁️ Amazon EKS Deployment Architecture

For production deployments, the Real-Time Moderation System can be deployed on Amazon EKS (Elastic Kubernetes Service) for scalability, high availability, and enterprise-grade operations.

> **📁 Complete Kubernetes manifests and deployment scripts are available in the `deployment/kubernetes/` directory. See `deployment/kubernetes/README.md` for detailed instructions.**


## Clean Up

**To clean up the docker deployment run the following shell command:**

```bash
cd moderation-system && docker-compose down

echo "🔍 Checking for remaining containers..."
docker ps -a | grep moderation-system || echo "✅ No moderation-system containers found"

echo ""
echo "🔍 Checking for remaining networks..."
docker network ls | grep moderation || echo "✅ No moderation networks found"

echo ""
echo "🔍 Checking for any orphaned containers..."
docker ps -a --filter "status=exited" | grep -E "(mcp-server|chat-simulator|lightweight-filter|decision-handler|prometheus|grafana)" || echo "✅ No orphaned containers found"

docker network rm moderation-system_default 2>/dev/null || echo "Network already removed or in use"

echo ""
echo "🧹 Final cleanup check..."
docker network ls | grep moderation || echo "✅ All moderation networks cleaned up"
docker image prune -a  # Remove all unused images
docker system prune -a  # Complete Docker cleanup
```

### ** To Restart Later:**

```bash
cd moderation-system
docker-compose up -d
```

### **🏗️ EKS Architecture Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                        Amazon EKS Cluster                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Namespace:    │  │   Namespace:    │  │   Namespace:    │ │
│  │   moderation    │  │   monitoring    │  │   ingress       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Application     │  │ Monitoring      │  │ Load Balancer   │
│ Services        │  │ Stack           │  │ & Ingress       │
│                 │  │                 │  │                 │
│ • MCP Server    │  │ • Prometheus    │  │ • ALB           │
│ • Chat Sim      │  │ • Grafana       │  │ • WAF           │
│ • Filter        │  │ • Jaeger        │  │ • CloudFront    │
│ • Decision      │  │ • AlertManager  │  │ • Route53       │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### **🚀 EKS Deployment Prerequisites**

#### **1. AWS CLI and Tools Setup**
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Verify installations
aws --version
kubectl version --client
eksctl version
helm version
```

#### **2. AWS Configuration**
```bash
# Configure AWS credentials
aws configure
# AWS Access Key ID: [Your Access Key]
# AWS Secret Access Key: [Your Secret Key]
# Default region name: us-west-2
# Default output format: json

# Verify AWS access
aws sts get-caller-identity
```

### **🏗️ EKS Cluster Creation**

#### **3. Create EKS Cluster**
```bash
# Create cluster configuration
cat > cluster-config.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig

metadata:
  name: moderation-system-cluster
  region: us-west-2
  version: "1.28"

nodeGroups:
  - name: moderation-workers
    instanceType: m5.large
    desiredCapacity: 3
    minSize: 2
    maxSize: 10
    volumeSize: 50
    ssh:
      allow: true
    iam:
      withAddonPolicies:
        autoScaler: true
        cloudWatch: true
        ebs: true
        efs: true
        albIngress: true

addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
  - name: aws-ebs-csi-driver

cloudWatch:
  clusterLogging:
    enable: ["api", "audit", "authenticator", "controllerManager", "scheduler"]
EOF

# Create the cluster (takes 15-20 minutes)
eksctl create cluster -f cluster-config.yaml

# Update kubeconfig
aws eks update-kubeconfig --region us-west-2 --name moderation-system-cluster

# Verify cluster
kubectl get nodes
```

#### **4. Install Essential Add-ons**
```bash
# Install AWS Load Balancer Controller
curl -O https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.2/docs/install/iam_policy.json

aws iam create-policy \
    --policy-name AWSLoadBalancerControllerIAMPolicy \
    --policy-document file://iam_policy.json

eksctl create iamserviceaccount \
  --cluster=moderation-system-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --role-name AmazonEKSLoadBalancerControllerRole \
  --attach-policy-arn=arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):policy/AWSLoadBalancerControllerIAMPolicy \
  --approve

helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=moderation-system-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Install Cluster Autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

kubectl -n kube-system annotate deployment.apps/cluster-autoscaler \
  cluster-autoscaler.kubernetes.io/safe-to-evict="false"

kubectl -n kube-system edit deployment.apps/cluster-autoscaler
# Add: --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/moderation-system-cluster
```

### **🗂️ Kubernetes Deployment Structure**

The system includes comprehensive Kubernetes manifests in the `deployment/kubernetes/` directory:

```
deployment/kubernetes/
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
├── deploy.sh                      # Automated deployment script
└── README.md                      # Detailed deployment guide
```

#### **5. Deploy Using Automated Script**
```bash
# Navigate to kubernetes directory
cd deployment/kubernetes

# Review and update configuration
# Edit configmaps/moderation-config.yaml with your DeepSeek endpoint
# Edit secrets/moderation-secrets.yaml with your credentials

# Run automated deployment
./deploy.sh deploy

# Check deployment status
./deploy.sh status

# Run health checks
./deploy.sh health
```

#### **6. Manual Deployment (Alternative)**
```bash
# Create namespace and RBAC
kubectl apply -f 00-namespace.yaml

# Create secrets (update with your values first)
kubectl create secret generic moderation-secrets \
  --from-literal=postgres-password=YOUR_PASSWORD \
  --from-literal=postgres-user=postgres \
  --from-literal=api-key=YOUR_API_KEY \
  -n moderation-system

# Create configuration
kubectl apply -f configmaps/

# Deploy infrastructure
kubectl apply -f deployments/postgres.yaml
kubectl apply -f deployments/redis.yaml

# Deploy application services
kubectl apply -f deployments/mcp-server.yaml
kubectl apply -f deployments/lightweight-filter.yaml
kubectl apply -f deployments/chat-simulator.yaml
kubectl apply -f deployments/decision-handler.yaml

# Create services
kubectl apply -f services/services.yaml

# Deploy monitoring
kubectl apply -f deployments/monitoring.yaml

# Create HPA and network policies
kubectl apply -f deployments/hpa.yaml
kubectl apply -f network-policies.yaml

# Create ingress (optional)
kubectl apply -f ingress/ingress.yaml
```

### **📊 Monitoring Stack Deployment**

#### **7. Deploy Prometheus and Grafana**
```bash
# Deploy monitoring stack using existing manifests
kubectl apply -f deployments/monitoring.yaml

# Or install via Helm for more advanced configuration
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install Prometheus with custom values
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=50Gi
```

### **🔒 Security and Compliance**

#### **8. Network Policies and Security**
```bash
# Apply network policies from deployment manifests
kubectl apply -f network-policies.yaml

# The network policies include:
# - Ingress rules for ALB and monitoring access
# - Egress rules for external LLM and database connections
# - Inter-service communication within the namespace
# - Isolation from other namespaces
```

For detailed security configuration, see the complete network policies in `deployment/kubernetes/network-policies.yaml`.

### **🚀 Deployment and Validation**

#### **9. Build and Push Container Images**
```bash
# Create ECR repositories
aws ecr create-repository --repository-name moderation-system/mcp-server
aws ecr create-repository --repository-name moderation-system/chat-simulator
aws ecr create-repository --repository-name moderation-system/lightweight-filter

# Get ECR login token
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-west-2.amazonaws.com

# Build and push images
docker build -t ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/moderation-system/mcp-server:latest ./services/mcp-server
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/moderation-system/mcp-server:latest

docker build -t ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/moderation-system/chat-simulator:latest ./services/chat-simulator
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/moderation-system/chat-simulator:latest

docker build -t ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/moderation-system/lightweight-filter:latest ./services/lightweight-filter
docker push ACCOUNT.dkr.ecr.us-west-2.amazonaws.com/moderation-system/lightweight-filter:latest
```

#### **10. Deploy and Test**
```bash
# Navigate to deployment directory
cd deployment/kubernetes

# Update container registry in deployment files
sed -i 's|your-registry|ACCOUNT.dkr.ecr.us-west-2.amazonaws.com|g' deployments/*.yaml

# Deploy all services using the automated script
./deploy.sh deploy

# Check deployment status
./deploy.sh status

# Run health checks
./deploy.sh health

# Test the deployment
kubectl port-forward -n moderation-system svc/chat-simulator-service 8002:8002 &
curl http://localhost:8002/health

# Test moderation endpoint
kubectl port-forward -n moderation-system svc/mcp-server-service 8000:8000 &
curl -X POST http://localhost:8000/moderate \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello world",
    "user_id": "test_user",
    "channel_id": "general"
  }'
```

### **📈 Production Operations**

#### **11. Monitoring and Alerting**
```bash
# Access Grafana dashboard
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Create custom alerts using the monitoring configuration
kubectl apply -f deployments/monitoring.yaml

# The monitoring stack includes pre-configured alerts for:
# - High error rates
# - High latency  
# - LLM service down
# - Database connection failures
```

#### **12. Scaling and Performance**
```bash
# Manual scaling
kubectl scale deployment mcp-server --replicas=5 -n moderation-system

# Check HPA status (configured in deployments/hpa.yaml)
kubectl get hpa -n moderation-system

# Load testing
kubectl run load-test --image=busybox --rm -it --restart=Never -- /bin/sh
# Inside the pod:
for i in $(seq 1 1000); do
  wget -qO- --post-data='{"message":"test","user_id":"load_test","channel_id":"test"}' \
    --header='Content-Type: application/json' \
    http://mcp-server:8000/moderate
done
```

For detailed deployment instructions, troubleshooting, and configuration options, see the complete guide in `deployment/kubernetes/README.md`.

### **🔧 EKS Management Commands**

```bash
# Cluster management
eksctl get cluster
eksctl get nodegroup --cluster moderation-system-cluster

# Update cluster
eksctl update cluster --name moderation-system-cluster

# Add new node group
eksctl create nodegroup \
  --cluster moderation-system-cluster \
  --name gpu-workers \
  --instance-types g4dn.xlarge \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 5

# Delete cluster (when done)
eksctl delete cluster --name moderation-system-cluster
```

### **💰 Cost Optimization**

- **Use Spot Instances**: Configure node groups with spot instances for non-critical workloads
- **Right-size Resources**: Monitor and adjust CPU/memory requests and limits
- **Cluster Autoscaler**: Automatically scale nodes based on demand
- **Scheduled Scaling**: Scale down during off-hours
- **Reserved Instances**: Use RIs for predictable workloads

### **🎯 EKS Benefits**

- **High Availability**: Multi-AZ deployment with automatic failover
- **Scalability**: Auto-scaling based on demand
- **Security**: IAM integration, network policies, and encryption
- **Monitoring**: Comprehensive observability with CloudWatch and Prometheus
- **Cost Management**: Efficient resource utilization and spot instances
- **Compliance**: SOC, PCI, and other compliance certifications

This EKS deployment provides a production-ready, scalable, and highly available moderation system suitable for enterprise workloads.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details
