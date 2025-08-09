# Moderation System Monitoring

This directory contains comprehensive monitoring and observability configurations for the Real-Time Moderation System.

## 📊 **Grafana Dashboards**

### **Available Dashboards**

#### **1. Moderation System - Overview**
- **URL**: http://localhost:3000/d/moderation-overview/moderation-system-overview
- **Purpose**: High-level system overview and key metrics
- **Panels**:
  - Message Processing Rate
  - Total Messages Processed
  - Message Classification Distribution (Pie Chart)
  - Processing Latency (95th Percentile)
  - Processing Latency Percentiles (50th, 95th, 99th)
  - Filter Processing Rate
  - Active WebSocket Connections

#### **2. Service Performance**
- **URL**: http://localhost:3000/d/moderation-performance/moderation-system-service-performance
- **Purpose**: Detailed service performance and resource utilization
- **Panels**:
  - Service CPU Usage
  - Service Memory Usage
  - Request Rates by Service
  - Service Response Times (95th Percentile)
  - Python Garbage Collection
  - Open File Descriptors

#### **3. Filter Analysis**
- **URL**: http://localhost:3000/d/moderation-filter/moderation-system-filter-analysis
- **Purpose**: Lightweight filter performance and effectiveness
- **Panels**:
  - Filter Decision Distribution
  - Filter Processing Time (95th Percentile)
  - Filter Processing Rate Over Time
  - Pattern Match Rate
  - Filter Statistics Summary
  - Filter Effectiveness

#### **4. Real-time Monitoring**
- **URL**: http://localhost:3000/d/moderation-realtime/moderation-system-real-time-monitoring
- **Purpose**: Live monitoring with 1-second refresh rate
- **Panels**:
  - Total Messages (Stat)
  - Toxic Messages (Stat)
  - Active Connections (Stat)
  - Processing Time (Stat)
  - Real-time Message Processing Rate
  - Real-time Processing Latency
  - Request Success/Error Rate
  - Live Message Statistics

## 🚀 **Quick Setup**

### **1. Import Dashboards**
```bash
# Navigate to monitoring directory
cd monitoring

# Run the import script
./import-dashboards.sh
```

### **2. Access Grafana**
- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin

### **3. View Dashboards**
- Navigate to **Dashboards** → **Browse**
- Look for dashboards tagged with "moderation"

## 📈 **Key Metrics Explained**

### **Message Processing Metrics**
- `chat_messages_total`: Total number of messages processed by decision type
- `chat_message_processing_seconds`: Histogram of message processing times
- `chat_active_websocket_connections`: Number of active WebSocket connections

### **Filter Metrics**
- `filter_requests_total`: Total filter requests by decision and filter type
- `filter_processing_seconds`: Histogram of filter processing times
- `filter_pattern_matches_total`: Pattern matches by type

### **Service Health Metrics**
- `chat_moderation_requests_total`: MCP server request counts by status
- `chat_filter_requests_total`: Filter service request counts by status
- Standard Python metrics (CPU, memory, GC, etc.)

## 🔍 **Useful Queries**

### **Message Processing Rate**
```promql
rate(chat_messages_total[5m])
```

### **Processing Latency (95th Percentile)**
```promql
histogram_quantile(0.95, rate(chat_message_processing_seconds_bucket[5m]))
```

### **Filter Effectiveness**
```promql
rate(filter_requests_total{decision="flagged"}[5m]) / rate(filter_requests_total[5m]) * 100
```

### **Error Rate**
```promql
rate(chat_moderation_requests_total{status="error"}[5m]) / rate(chat_moderation_requests_total[5m]) * 100
```

## 🚨 **Alerting**

### **Recommended Alerts**

#### **High Processing Latency**
```promql
histogram_quantile(0.95, rate(chat_message_processing_seconds_bucket[5m])) > 15
```

#### **High Error Rate**
```promql
rate(chat_moderation_requests_total{status="error"}[5m]) / rate(chat_moderation_requests_total[5m]) > 0.05
```

#### **Service Down**
```promql
up{job=~"mcp-server|chat-simulator|lightweight-filter|decision-handler"} == 0
```

## 🛠️ **Customization**

### **Adding New Panels**
1. Open Grafana dashboard
2. Click "Add Panel"
3. Use Prometheus queries from the metrics available
4. Configure visualization type and options

### **Modifying Existing Dashboards**
1. Open dashboard in edit mode
2. Click on panel to edit
3. Modify queries, visualization, or settings
4. Save dashboard

### **Creating New Dashboards**
1. Create new dashboard in Grafana
2. Add panels with relevant metrics
3. Export as JSON
4. Save to `dashboards/` directory
5. Update import script if needed

## 📊 **Dashboard Features**

### **Auto-Refresh**
- **Overview**: 5 seconds
- **Performance**: 5 seconds
- **Filter Analysis**: 5 seconds
- **Real-time**: 1 second

### **Time Ranges**
- **Default**: Last 1 hour
- **Real-time**: Last 5 minutes
- **Customizable**: Use time picker for custom ranges

### **Variables and Templating**
- Dashboards are designed to work without variables for simplicity
- Can be extended with service/instance variables if needed

## 🔧 **Troubleshooting**

### **Dashboard Import Issues**
```bash
# Check Grafana accessibility
curl http://localhost:3000/api/health

# Check if jq is installed
which jq

# Re-run import with verbose output
./import-dashboards.sh
```

### **Missing Data**
1. Verify Prometheus is scraping targets:
   - Visit http://localhost:9090/targets
   - Ensure all services show as "UP"

2. Check service metrics endpoints:
   ```bash
   curl http://localhost:8000/metrics  # MCP Server
   curl http://localhost:8001/metrics  # Lightweight Filter
   curl http://localhost:8002/metrics  # Chat Simulator
   curl http://localhost:8003/metrics  # Decision Handler
   ```

3. Verify Prometheus datasource in Grafana:
   - Go to Configuration → Data Sources
   - Test Prometheus connection

### **Performance Issues**
- Reduce refresh rates if Grafana becomes slow
- Limit time ranges for heavy queries
- Use recording rules for complex queries

## 📁 **Directory Structure**

```
monitoring/
├── dashboards/                    # Grafana dashboard JSON files
│   ├── moderation-overview.json   # Main overview dashboard
│   ├── service-performance.json   # Service performance metrics
│   ├── filter-analysis.json       # Filter effectiveness analysis
│   └── realtime-monitoring.json   # Real-time monitoring
├── import-dashboards.sh           # Dashboard import script
└── README.md                      # This file
```

## 🎯 **Best Practices**

### **Dashboard Design**
- Use consistent color schemes (red for errors, green for success)
- Include units in panel titles and axes
- Group related metrics together
- Use appropriate visualization types for data

### **Query Optimization**
- Use appropriate time ranges for rate() functions
- Avoid overly complex queries that impact performance
- Use recording rules for frequently used complex queries

### **Monitoring Strategy**
- Monitor both technical metrics (latency, errors) and business metrics (message counts, classifications)
- Set up alerts for critical issues
- Review dashboards regularly and update as needed

## 🔗 **Related Documentation**

- [Prometheus Configuration](../docker-compose.yml)
- [Service Metrics Implementation](../services/)
- [System Architecture](../README.md)
- [Deployment Guide](../deployment/)

## 📞 **Support**

For issues with monitoring setup:
1. Check service logs: `docker-compose logs [service-name]`
2. Verify metrics endpoints are accessible
3. Check Prometheus targets status
4. Review Grafana datasource configuration
