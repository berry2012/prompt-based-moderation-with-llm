#!/bin/bash

# Setup script for Chat Simulator WebUI
set -e

echo "🌐 Setting up Chat Simulator WebUI"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the moderation-system root directory"
    exit 1
fi

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

# Ensure static directory exists
echo "📁 Setting up static files..."
mkdir -p services/chat-simulator/static

# Check if static files exist
if [ ! -f "services/chat-simulator/static/index.html" ]; then
    echo "❌ WebUI static files not found. Please ensure index.html and script.js are in services/chat-simulator/static/"
    exit 1
fi

echo "✅ Static files found"

# Build the chat simulator with WebUI
echo "🔨 Building chat simulator with WebUI..."
docker-compose build chat-simulator

if [ $? -ne 0 ]; then
    echo "❌ Failed to build chat simulator"
    exit 1
fi

echo "✅ Chat simulator built successfully"

# Start the chat simulator
echo "🚀 Starting chat simulator..."
docker-compose up -d chat-simulator

# Wait for service to be ready
echo "⏳ Waiting for chat simulator to be ready..."
sleep 10

# Test the service
echo "🧪 Testing chat simulator endpoints..."

endpoints=(
    "http://localhost:8002/health:Health Check"
    "http://localhost:8002/:WebUI"
)

all_healthy=true

for endpoint_info in "${endpoints[@]}"; do
    IFS=':' read -r url name <<< "$endpoint_info"
    if curl -s --connect-timeout 10 "$url" > /dev/null; then
        echo "✅ $name is accessible at $url"
    else
        echo "❌ $name is not accessible at $url"
        all_healthy=false
    fi
done

if [ "$all_healthy" = true ]; then
    echo ""
    echo "🎉 Chat Simulator WebUI Setup Complete!"
    echo "======================================"
    echo ""
    echo "🌐 Access the WebUI at: http://localhost:8002"
    echo ""
    echo "🎯 Features available:"
    echo "   • Interactive chat interface"
    echo "   • Real-time message moderation"
    echo "   • Voice recording support (browser dependent)"
    echo "   • Message type testing (normal, toxic, spam, PII)"
    echo "   • Live statistics and monitoring"
    echo "   • WebSocket real-time updates"
    echo ""
    echo "🔧 API Endpoints:"
    echo "   • WebUI: http://localhost:8002/"
    echo "   • Health: http://localhost:8002/health"
    echo "   • WebSocket: ws://localhost:8002/ws"
    echo "   • Send Message: POST http://localhost:8002/api/send-message"
    echo "   • Single Test: POST http://localhost:8002/simulate/single"
    echo "   • Start Simulation: POST http://localhost:8002/simulate/start"
    echo "   • Stop Simulation: POST http://localhost:8002/simulate/stop"
    echo ""
    echo "📊 Usage Instructions:"
    echo "   1. Open http://localhost:8002 in your browser"
    echo "   2. Click 'Start Simulation' for automated chat"
    echo "   3. Type messages in the input field to test moderation"
    echo "   4. Use voice recording button for audio input (simulated)"
    echo "   5. Select different message types for testing"
    echo "   6. Monitor real-time statistics in the side panel"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "   • Check logs: docker-compose logs -f chat-simulator"
    echo "   • Restart service: docker-compose restart chat-simulator"
    echo "   • Rebuild: docker-compose build chat-simulator"
    echo ""
    
    # Open browser automatically (macOS)
    if command -v open &> /dev/null; then
        echo "🌐 Opening WebUI in browser..."
        open http://localhost:8002
    fi
    
else
    echo ""
    echo "⚠️  Setup completed with some issues"
    echo "Please check the logs: docker-compose logs -f chat-simulator"
fi

echo ""
echo "📝 Next Steps:"
echo "   • Ensure your MCP server is running for full functionality"
echo "   • Start the lightweight filter for complete moderation pipeline"
echo "   • Check Grafana dashboards for monitoring: http://localhost:3000"
echo ""
