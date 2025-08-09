#!/bin/bash

# Validation script for Docker container monitoring setup
set -e

echo "🔍 Validating Docker Container Monitoring Setup"
echo "=============================================="

# Function to check if a service is responding
check_service() {
    local url=$1
    local name=$2
    local timeout=${3:-10}
    
    if curl -s --connect-timeout $timeout "$url" > /dev/null 2>&1; then
        echo "✅ $name is responding at $url"
        return 0
    else
        echo "❌ $name is not responding at $url"
        return 1
    fi
}

# Function to check if a service has metrics
check_metrics() {
    local url=$1
    local name=$2
    
    if curl -s --connect-timeout 10 "$url" | grep -q "container_"; then
        echo "✅ $name is exposing container metrics"
        return 0
    else
        echo "⚠️  $name metrics may not be ready yet"
        return 1
    fi
}

# Check if Docker is running
echo "🐳 Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running"
    exit 1
fi
echo "✅ Docker is running"

# Check if containers are running
echo ""
echo "📦 Checking container status..."
containers=("cadvisor" "prometheus" "grafana")
for container in "${containers[@]}"; do
    if docker-compose ps | grep -q "$container.*Up"; then
        echo "✅ $container container is running"
    else
        echo "❌ $container container is not running"
        echo "   Try: docker-compose up -d $container"
    fi
done

# Check service endpoints
echo ""
echo "🌐 Checking service endpoints..."
check_service "http://localhost:8089/metrics" "cAdvisor"
check_service "http://localhost:9090/-/healthy" "Prometheus"
check_service "http://localhost:3000/api/health" "Grafana"

# Check metrics availability
echo ""
echo "📊 Checking metrics availability..."
check_metrics "http://localhost:8089/metrics" "cAdvisor"

# Check Prometheus targets
echo ""
echo "🎯 Checking Prometheus targets..."
if curl -s "http://localhost:9090/api/v1/targets" | grep -q "cadvisor"; then
    echo "✅ Prometheus is scraping cAdvisor"
else
    echo "⚠️  Prometheus may not be scraping cAdvisor yet"
fi

# Check for specific container metrics
echo ""
echo "🔍 Checking for container metrics..."
metrics_to_check=(
    "container_cpu_usage_seconds_total"
    "container_memory_usage_bytes"
    "container_network_receive_bytes_total"
    "container_fs_reads_bytes_total"
)

for metric in "${metrics_to_check[@]}"; do
    if curl -s "http://localhost:8089/metrics" | grep -q "$metric"; then
        echo "✅ $metric is available"
    else
        echo "⚠️  $metric not found"
    fi
done

# Check Grafana datasource
echo ""
echo "📈 Checking Grafana configuration..."
if curl -s -u admin:admin "http://localhost:3000/api/datasources" | grep -q "Prometheus"; then
    echo "✅ Grafana has Prometheus datasource configured"
else
    echo "⚠️  Grafana Prometheus datasource may not be configured"
fi

echo ""
echo "🎉 Validation complete!"
echo "====================="
echo ""
echo "📋 Summary of access points:"
echo "   • cAdvisor: http://localhost:8089"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "🔧 Useful commands:"
echo "   • View container logs: docker-compose logs -f [service]"
echo "   • Restart services: docker-compose restart [service]"
echo "   • View metrics: curl http://localhost:8089/metrics"
echo ""
echo "📊 Key Prometheus queries to try:"
echo "   • Container CPU: rate(container_cpu_usage_seconds_total[5m]) * 100"
echo "   • Container Memory: container_memory_usage_bytes"
echo "   • Container Network: rate(container_network_receive_bytes_total[5m])"
echo ""
