#!/bin/bash

# Script to enable Docker daemon metrics on macOS
# This script helps configure Docker Desktop to expose metrics

echo "🐳 Docker Metrics Configuration for macOS"
echo "=========================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"

# Check Docker Desktop version
DOCKER_VERSION=$(docker --version)
echo "📋 $DOCKER_VERSION"

echo ""
echo "📝 To enable Docker daemon metrics on macOS:"
echo ""
echo "1. Open Docker Desktop"
echo "2. Go to Settings (gear icon)"
echo "3. Navigate to 'Docker Engine' tab"
echo "4. Add the following configuration to the JSON:"
echo ""
echo '{'
echo '  "metrics-addr": "0.0.0.0:9323",'
echo '  "experimental": false'
echo '}'
echo ""
echo "5. Click 'Apply & Restart'"
echo ""
echo "🔍 Alternative: You can also run Docker with metrics enabled:"
echo "   dockerd --metrics-addr=0.0.0.0:9323"
echo ""
echo "⚠️  Note: On macOS, Docker Desktop runs in a VM, so direct daemon"
echo "   configuration might be limited. cAdvisor will provide comprehensive"
echo "   container metrics regardless of daemon metrics availability."
echo ""

# Test if metrics endpoint is available
echo "🧪 Testing Docker metrics endpoint..."
if curl -s --connect-timeout 5 http://localhost:9323/metrics >/dev/null 2>&1; then
    echo "✅ Docker daemon metrics are available at http://localhost:9323/metrics"
else
    echo "⚠️  Docker daemon metrics not available. This is normal on macOS."
    echo "   cAdvisor will provide all necessary container metrics."
fi

echo ""
echo "🚀 Starting containers with cAdvisor monitoring..."
echo "   Run: docker-compose up -d"
echo ""
echo "📊 Access points after startup:"
echo "   - cAdvisor: http://localhost:8089"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000"
echo ""
