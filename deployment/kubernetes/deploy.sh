#!/bin/bash

# Moderation System Kubernetes Deployment Script
# This script deploys the complete moderation system to your EKS cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="moderation-system"
DEEPSEEK_NAMESPACE="deepseek"
REGISTRY="your-registry"  # Replace with your container registry
VERSION="latest"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    print_success "kubectl is available"
}

# Function to check if cluster is accessible
check_cluster() {
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    print_success "Connected to Kubernetes cluster"
}

# Function to check if DeepSeek namespace exists
check_deepseek() {
    if ! kubectl get namespace $DEEPSEEK_NAMESPACE &> /dev/null; then
        print_warning "DeepSeek namespace '$DEEPSEEK_NAMESPACE' not found"
        print_warning "Make sure your DeepSeek LLM is deployed first"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "DeepSeek namespace found"
    fi
}

# Function to create namespace
create_namespace() {
    print_status "Creating namespace and RBAC..."
    kubectl apply -f 00-namespace.yaml
    print_success "Namespace and RBAC created"
}

# Function to create secrets
create_secrets() {
    print_status "Creating secrets..."
    
    # Check if secrets already exist
    if kubectl get secret moderation-secrets -n $NAMESPACE &> /dev/null; then
        print_warning "Secrets already exist. Skipping creation."
        print_warning "To update secrets, delete them first: kubectl delete secret moderation-secrets -n $NAMESPACE"
    else
        kubectl apply -f secrets/
        print_success "Secrets created"
    fi
}

# Function to create configmaps
create_configmaps() {
    print_status "Creating configmaps..."
    kubectl apply -f configmaps/
    print_success "Configmaps created"
}

# Function to deploy infrastructure services
deploy_infrastructure() {
    print_status "Deploying infrastructure services (PostgreSQL, Redis)..."
    kubectl apply -f deployments/postgres.yaml
    kubectl apply -f deployments/redis.yaml
    
    print_status "Waiting for infrastructure services to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/postgres -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/redis -n $NAMESPACE
    print_success "Infrastructure services deployed"
}

# Function to deploy application services
deploy_applications() {
    print_status "Deploying application services..."
    
    # Update image references
    sed -i.bak "s|your-registry|$REGISTRY|g" deployments/mcp-server.yaml
    sed -i.bak "s|your-registry|$REGISTRY|g" deployments/lightweight-filter.yaml
    sed -i.bak "s|your-registry|$REGISTRY|g" deployments/chat-simulator.yaml
    sed -i.bak "s|your-registry|$REGISTRY|g" deployments/decision-handler.yaml
    
    kubectl apply -f deployments/mcp-server.yaml
    kubectl apply -f deployments/lightweight-filter.yaml
    kubectl apply -f deployments/chat-simulator.yaml
    kubectl apply -f deployments/decision-handler.yaml
    
    print_status "Waiting for application services to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/mcp-server -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/lightweight-filter -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/chat-simulator -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/decision-handler -n $NAMESPACE
    
    print_success "Application services deployed"
}

# Function to create services
create_services() {
    print_status "Creating services..."
    kubectl apply -f services/
    print_success "Services created"
}

# Function to deploy monitoring
deploy_monitoring() {
    print_status "Deploying monitoring stack..."
    kubectl apply -f deployments/monitoring.yaml
    
    print_status "Waiting for monitoring services to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/prometheus -n $NAMESPACE
    kubectl wait --for=condition=available --timeout=300s deployment/grafana -n $NAMESPACE
    
    print_success "Monitoring stack deployed"
}

# Function to create HPA
create_hpa() {
    print_status "Creating Horizontal Pod Autoscalers..."
    kubectl apply -f deployments/hpa.yaml
    print_success "HPA created"
}

# Function to create ingress
create_ingress() {
    print_status "Creating ingress..."
    print_warning "Please update the domain names in ingress/ingress.yaml before applying"
    read -p "Apply ingress configuration? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl apply -f ingress/
        print_success "Ingress created"
    else
        print_warning "Skipping ingress creation"
    fi
}

# Function to create network policies
create_network_policies() {
    print_status "Creating network policies..."
    kubectl apply -f network-policies.yaml
    print_success "Network policies created"
}

# Function to show deployment status
show_status() {
    print_status "Deployment Status:"
    echo
    kubectl get pods -n $NAMESPACE
    echo
    kubectl get services -n $NAMESPACE
    echo
    kubectl get ingress -n $NAMESPACE
    echo
    
    print_status "External Access Points:"
    CHAT_SIMULATOR_LB=$(kubectl get service chat-simulator-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending...")
    GRAFANA_LB=$(kubectl get service grafana-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "Pending...")
    
    echo "Chat Simulator: http://$CHAT_SIMULATOR_LB:8002"
    echo "Grafana: http://$GRAFANA_LB:3000 (admin/admin)"
    echo
    
    print_status "Internal Service Endpoints:"
    echo "MCP Server: http://mcp-server-service.$NAMESPACE.svc.cluster.local:8000"
    echo "Lightweight Filter: http://lightweight-filter-service.$NAMESPACE.svc.cluster.local:8001"
    echo "Decision Handler: http://decision-handler-service.$NAMESPACE.svc.cluster.local:8003"
    echo "PostgreSQL: postgres-service.$NAMESPACE.svc.cluster.local:5432"
    echo "Redis: redis-service.$NAMESPACE.svc.cluster.local:6379"
    echo "Prometheus: http://prometheus-service.$NAMESPACE.svc.cluster.local:9090"
}

# Function to run health checks
health_check() {
    print_status "Running health checks..."
    
    # Check if all pods are running
    NOT_RUNNING=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running --no-headers 2>/dev/null | wc -l)
    if [ $NOT_RUNNING -eq 0 ]; then
        print_success "All pods are running"
    else
        print_warning "$NOT_RUNNING pods are not running"
        kubectl get pods -n $NAMESPACE --field-selector=status.phase!=Running
    fi
    
    # Check service endpoints
    print_status "Checking service health endpoints..."
    
    # Port forward and check health endpoints
    kubectl port-forward -n $NAMESPACE service/mcp-server-service 8000:8000 &
    PF_PID=$!
    sleep 5
    
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "MCP Server health check passed"
    else
        print_warning "MCP Server health check failed"
    fi
    
    kill $PF_PID 2>/dev/null || true
}

# Main deployment function
main() {
    print_status "Starting Moderation System deployment..."
    
    # Pre-flight checks
    check_kubectl
    check_cluster
    check_deepseek
    
    # Deployment steps
    create_namespace
    create_secrets
    create_configmaps
    deploy_infrastructure
    create_services
    deploy_applications
    deploy_monitoring
    create_hpa
    create_network_policies
    create_ingress
    
    # Post-deployment
    show_status
    health_check
    
    print_success "Deployment completed successfully!"
    print_status "Next steps:"
    echo "1. Update your container images and push to registry"
    echo "2. Update secrets with your actual values"
    echo "3. Configure your domain names in ingress"
    echo "4. Set up SSL certificates"
    echo "5. Configure monitoring alerts"
}

# Script options
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    "clean")
        print_warning "This will delete the entire moderation system!"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kubectl delete namespace $NAMESPACE
            print_success "Moderation system deleted"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|status|health|clean}"
        echo "  deploy - Deploy the complete system"
        echo "  status - Show deployment status"
        echo "  health - Run health checks"
        echo "  clean  - Delete the entire system"
        exit 1
        ;;
esac
