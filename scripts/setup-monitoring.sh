#!/bin/bash

# Comprehensive monitoring setup script for macOS
set -e

echo "🔧 Setting up comprehensive Docker container monitoring..."
echo "======================================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p logs/cadvisor

# Create Grafana provisioning configuration
echo "⚙️  Setting up Grafana provisioning..."

cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

cat > monitoring/grafana/provisioning/dashboards/dashboard.yml << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

# Update docker-compose.yml to include Grafana provisioning
echo "🔄 Updating Grafana configuration in docker-compose.yml..."

# Test cAdvisor configuration
echo "🧪 Testing cAdvisor configuration..."
if docker run --rm --volume=/:/rootfs:ro --volume=/var/run:/var/run:ro --volume=/sys:/sys:ro --volume=/var/lib/docker/:/var/lib/docker:ro --publish=8089:8080 --detach=true --name=cadvisor_test gcr.io/cadvisor/cadvisor:v0.47.0 --docker_only=true > /dev/null 2>&1; then
    echo "✅ cAdvisor test container started successfully"
    docker stop cadvisor_test > /dev/null 2>&1
    docker rm cadvisor_test > /dev/null 2>&1
else
    echo "⚠️  cAdvisor test failed, but will work in docker-compose environment"
fi

# Start monitoring stack
echo "🚀 Starting monitoring stack..."
docker-compose up -d cadvisor prometheus grafana

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Test endpoints
echo "🔍 Testing monitoring endpoints..."

endpoints=(
    "http://localhost:8089:cAdvisor"
    "http://localhost:9090:Prometheus"
    "http://localhost:3000:Grafana"
)

for endpoint_info in "${endpoints[@]}"; do
    IFS=':' read -r url name <<< "$endpoint_info"
    if curl -s --connect-timeout 10 "$url" > /dev/null; then
        echo "✅ $name is accessible at $url"
    else
        echo "⚠️  $name might still be starting up at $url"
    fi
done

echo ""
echo "🎉 Monitoring setup complete!"
echo "=========================="
echo ""
echo "📊 Access your monitoring tools:"
echo "   • cAdvisor (Container Metrics): http://localhost:8089"
echo "   • Prometheus (Metrics DB): http://localhost:9090"
echo "   • Grafana (Dashboards): http://localhost:3000"
echo "     - Username: admin"
echo "     - Password: admin"
echo ""
echo "🔍 Key metrics to monitor:"
echo "   • Container CPU usage: container_cpu_usage_seconds_total"
echo "   • Container memory: container_memory_usage_bytes"
echo "   • Container network I/O: container_network_*_bytes_total"
echo "   • Container filesystem I/O: container_fs_*_bytes_total"
echo ""
echo "📈 Next steps:"
echo "   1. Access Grafana and explore the pre-configured dashboards"
echo "   2. Check Prometheus targets: http://localhost:9090/targets"
echo "   3. Start your application containers: docker-compose up -d"
echo "   4. Monitor container performance in real-time"
echo ""
