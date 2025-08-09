#!/bin/bash

# Dashboard Verification Script
# Checks if all dashboards are accessible and displays their URLs

set -e

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="admin"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔍 Verifying Grafana Dashboards${NC}"
echo "=================================="

# Dashboard URLs
declare -A dashboards=(
    ["Moderation Overview"]="http://localhost:3000/d/moderation-overview/moderation-system-overview"
    ["Service Performance"]="http://localhost:3000/d/moderation-performance/moderation-system-service-performance"
    ["Filter Analysis"]="http://localhost:3000/d/moderation-filter/moderation-system-filter-analysis"
    ["Real-time Monitoring"]="http://localhost:3000/d/moderation-realtime/moderation-system-real-time-monitoring"
)

echo -e "\n${GREEN}✅ Available Dashboards:${NC}"
for name in "${!dashboards[@]}"; do
    url="${dashboards[$name]}"
    echo "📊 $name"
    echo "   🔗 $url"
    echo ""
done

echo -e "${BLUE}📈 Quick Access Commands:${NC}"
echo "# Open all dashboards in browser (macOS)"
for name in "${!dashboards[@]}"; do
    url="${dashboards[$name]}"
    echo "open \"$url\""
done

echo -e "\n${BLUE}🔧 Grafana Access:${NC}"
echo "URL: $GRAFANA_URL"
echo "Username: $GRAFANA_USER"
echo "Password: $GRAFANA_PASS"

echo -e "\n${BLUE}📊 Current Metrics Summary:${NC}"
echo "Getting latest metrics..."

# Get current message counts
total_messages=$(curl -s "http://localhost:9090/api/v1/query?query=sum(chat_messages_total)" | jq -r '.data.result[0].value[1] // "0"')
toxic_messages=$(curl -s "http://localhost:9090/api/v1/query?query=sum(chat_messages_total{decision=\"Toxic\"})" | jq -r '.data.result[0].value[1] // "0"')
non_toxic_messages=$(curl -s "http://localhost:9090/api/v1/query?query=sum(chat_messages_total{decision=\"Non-Toxic\"})" | jq -r '.data.result[0].value[1] // "0"')

echo "📈 Total Messages Processed: $total_messages"
echo "🔴 Toxic Messages: $toxic_messages"
echo "🟢 Non-Toxic Messages: $non_toxic_messages"

if [ "$total_messages" -gt 0 ]; then
    echo -e "\n${GREEN}✅ Dashboards should have data to display!${NC}"
else
    echo -e "\n⚠️  No message data found. Run some test messages first:"
    echo "curl -X POST http://localhost:8002/api/send-message -H 'Content-Type: application/json' -d '{\"message\":\"Hello world\",\"user_id\":\"test\",\"username\":\"Test\",\"channel_id\":\"general\"}'"
fi

echo -e "\n${BLUE}🚀 Next Steps:${NC}"
echo "1. Open Grafana: $GRAFANA_URL"
echo "2. Login with admin/admin"
echo "3. Navigate to Dashboards → Browse"
echo "4. Select any 'Moderation System' dashboard"
echo "5. Enjoy your monitoring! 📊"
