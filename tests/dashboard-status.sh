#!/bin/bash

# Dashboard Status Check Script
# Quick overview of system metrics and dashboard access

echo "🎯 Moderation System Dashboard Status"
echo "====================================="

# Check if services are running
echo ""
echo "🏥 Service Health:"
services=("mcp-server:8000" "chat-simulator:8002" "lightweight-filter:8001" "decision-handler:8003")
all_healthy=true

for service in "${services[@]}"; do
    service_name=${service%:*}
    port=${service#*:}
    if curl -s -f "http://localhost:$port/health" > /dev/null; then
        echo "   ✅ $service_name"
    else
        echo "   ❌ $service_name - Not responding"
        all_healthy=false
    fi
done

# Get current metrics
echo ""
echo "📊 Current Metrics:"
total=$(curl -s "http://localhost:9090/api/v1/query?query=sum(chat_messages_total)" | jq -r '.data.result[0].value[1] // "0"')
echo "   📈 Total Messages: $total"

if [ "$total" -gt 0 ]; then
    echo "   🔍 Message Breakdown:"
    curl -s "http://localhost:9090/api/v1/query?query=chat_messages_total" | jq -r '.data.result[] | "      \(.metric.decision): \(.value[1])"' | sort
fi

# Dashboard links
echo ""
echo "📊 Dashboard Access:"
echo "   🌐 Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "   📈 Overview: http://localhost:3000/d/moderation-overview"
echo "   🔴 Real-time: http://localhost:3000/d/moderation-realtime"
echo "   🔍 Filter Analysis: http://localhost:3000/d/moderation-filter"
echo "   ⚡ Performance: http://localhost:3000/d/moderation-performance"

# Quick actions
echo ""
echo "🚀 Quick Actions:"
echo "   Generate test data: ./tests/generate-test-data.sh"
echo "   Send single message: curl -X POST http://localhost:8002/api/send-message -H 'Content-Type: application/json' -d '{\"message\":\"Test message\",\"user_id\":\"test\",\"username\":\"Test\",\"channel_id\":\"general\"}'"

if [ "$all_healthy" = true ]; then
    echo ""
    echo "✅ All systems operational! Your dashboards are ready to use."
else
    echo ""
    echo "⚠️  Some services are not responding. Check docker-compose logs."
fi
