#!/bin/bash

# Demo script for Chat Simulator WebUI
set -e

echo "🎬 Chat Simulator WebUI Demo"
echo "============================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the moderation-system root directory"
    exit 1
fi

echo "🚀 Starting comprehensive demo..."

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo "⏳ Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s --connect-timeout 5 "$url" > /dev/null 2>&1; then
            echo "✅ $name is ready"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $name failed to start within expected time"
    return 1
}

# Start all required services
echo "🔧 Starting required services..."
docker-compose up -d mcp-server lightweight-filter chat-simulator

# Wait for services to be ready
wait_for_service "http://localhost:8000/health" "MCP Server"
wait_for_service "http://localhost:8001/health" "Lightweight Filter"
wait_for_service "http://localhost:8002/health" "Chat Simulator"

echo ""
echo "🎯 Demo Features Available:"
echo "=========================="

# Test API endpoints
echo ""
echo "📡 Testing API Endpoints:"
echo "------------------------"

# Test health endpoint
echo "🔍 Health Check:"
curl -s http://localhost:8002/health | jq '.' || echo "Health check response received"

# Test single message generation
echo ""
echo "🔍 Testing Single Message Generation:"
for msg_type in normal toxic spam pii; do
    echo "   Testing $msg_type message..."
    response=$(curl -s -X POST "http://localhost:8002/simulate/single?message_type=$msg_type")
    if [ $? -eq 0 ]; then
        echo "   ✅ $msg_type message generated successfully"
    else
        echo "   ❌ Failed to generate $msg_type message"
    fi
done

# Test user message API
echo ""
echo "🔍 Testing User Message API:"
curl -s -X POST "http://localhost:8002/api/send-message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from the demo script!",
    "user_id": "demo_user",
    "username": "DemoUser",
    "channel_id": "demo-channel"
  }' > /dev/null

if [ $? -eq 0 ]; then
    echo "   ✅ User message API working"
else
    echo "   ❌ User message API failed"
fi

echo ""
echo "🌐 WebUI Features:"
echo "=================="
echo "✅ Real-time chat interface"
echo "✅ WebSocket live updates"
echo "✅ Interactive message sending"
echo "✅ Voice recording interface (browser-dependent)"
echo "✅ Message type testing (Normal, Toxic, Spam, PII)"
echo "✅ Live statistics dashboard"
echo "✅ Responsive design (mobile-friendly)"
echo "✅ Real-time moderation results"
echo "✅ Processing time monitoring"
echo "✅ Connection status indicators"

echo ""
echo "🎮 Interactive Demo:"
echo "==================="
echo "1. 🌐 Open WebUI: http://localhost:8002"
echo "2. 🔄 Click 'Start Simulation' for automated chat"
echo "3. 💬 Type messages in the input field"
echo "4. 🎤 Try voice recording (if supported)"
echo "5. 🧪 Test different message types"
echo "6. 📊 Monitor real-time statistics"
echo "7. 🔍 Watch moderation decisions"

echo ""
echo "📊 Monitoring & Analytics:"
echo "========================="
echo "• Real-time message processing statistics"
echo "• Moderation decision tracking"
echo "• Processing time analysis"
echo "• Connection status monitoring"
echo "• Message type distribution"

echo ""
echo "🔧 Technical Features:"
echo "====================="
echo "• WebSocket real-time communication"
echo "• RESTful API endpoints"
echo "• Responsive web design"
echo "• Audio recording simulation"
echo "• Real-time data visualization"
echo "• Cross-browser compatibility"

# Start a brief simulation
echo ""
echo "🎬 Starting Brief Demo Simulation..."
echo "===================================="

# Start simulation
curl -s -X POST "http://localhost:8002/simulate/start" > /dev/null
echo "✅ Simulation started"

# Let it run for a few seconds
echo "⏳ Running simulation for 10 seconds..."
sleep 10

# Stop simulation
curl -s -X POST "http://localhost:8002/simulate/stop" > /dev/null
echo "✅ Simulation stopped"

echo ""
echo "🎉 Demo Complete!"
echo "================"
echo ""
echo "🌐 Access Points:"
echo "   • WebUI: http://localhost:8002"
echo "   • API Docs: http://localhost:8002/docs (if available)"
echo "   • Health Check: http://localhost:8002/health"
echo ""
echo "📱 Mobile Access:"
echo "   • The WebUI is fully responsive"
echo "   • Access from any device on your network"
echo "   • Touch-friendly interface"
echo ""
echo "🔧 Development:"
echo "   • View logs: docker-compose logs -f chat-simulator"
echo "   • Restart: docker-compose restart chat-simulator"
echo "   • Rebuild: docker-compose build chat-simulator"
echo ""
echo "🎯 Use Cases:"
echo "   • Content moderation testing"
echo "   • Real-time chat simulation"
echo "   • AI model evaluation"
echo "   • User experience testing"
echo "   • Performance monitoring"
echo ""

# Open browser automatically (macOS)
if command -v open &> /dev/null; then
    echo "🌐 Opening WebUI in browser..."
    open http://localhost:8002
elif command -v xdg-open &> /dev/null; then
    echo "🌐 Opening WebUI in browser..."
    xdg-open http://localhost:8002
else
    echo "🌐 Please open http://localhost:8002 in your browser"
fi

echo ""
echo "💡 Pro Tips:"
echo "   • Use different message types to test moderation accuracy"
echo "   • Monitor processing times to optimize performance"
echo "   • Try the voice recording feature in supported browsers"
echo "   • Check the statistics panel for insights"
echo "   • Use the WebSocket connection for real-time updates"
echo ""
echo "🎊 Enjoy exploring the Chat Simulator WebUI!"
