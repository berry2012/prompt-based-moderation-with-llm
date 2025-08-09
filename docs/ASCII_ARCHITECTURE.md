# ASCII System Architecture Diagram

## Main Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           REAL-TIME MODERATION SYSTEM                               │
└─────────────────────────────────────────────────────────────────────────────────────┘

INPUT LAYER
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chat Messages │    │   Voice Input   │    │  System Events  │
│   • Text Chat   │    │   • Whisper STT │    │   • Webhooks    │
│   • User Data   │    │   • Audio Stream│    │   • API Calls   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
PROCESSING LAYER                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐               │
│  │   Chat          │───▶│  Lightweight     │───▶│   MCP Server    │               │
│  │   Simulator     │    │  Filter          │    │  (Model Context │               │
│  │                 │    │                  │    │   Protocol)     │               │
│  │ • Message Gen   │    │ • Keyword Filter │    │ • Prompt Mgmt   │               │
│  │ • WebSocket     │    │ • Rate Limiting  │    │ • LLM Interface │               │
│  │ • Whisper STT   │    │ • PII Detection  │    │ • Validation    │               │
│  │ • User Sim      │    │ • Profanity      │    │ • Security      │               │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘               │
│           │                       │                       │                        │
│           │              ┌────────▼────────┐             │                        │
│           │              │  Filter Results │             │                        │
│           │              │ • should_process │             │                        │
│           │              │ • confidence    │             │                        │
│           │              │ • matched_patterns│            │                        │
│           │              │ • processing_time │            │                        │
│           │              └─────────────────┘             │                        │
│           │                                              │                        │
│           └──────────────────────────────────────────────┼────────────────────────┘
│                                                          │
│  ┌─────────────────┐    ┌──────────────────┐             │
│  │   DeepSeek LLM  │◀───│  Prompt Template │◀────────────┘
│  │   Endpoint      │    │  System          │
│  │                 │    │                  │
│  │ • Chat API      │    │ • 7 Templates   │
│  │ • JSON Response │    │ • Versioning    │
│  │ • Error Handling│    │ • YAML Config   │
│  │ • Retry Logic   │    │ • Variable Sub  │
│  └─────────────────┘    └──────────────────┘
│           │                       │
│           ▼                       ▼
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  │  LLM Response   │───▶│  Moderation      │───▶│  Decision       │
│  │                 │    │  Decision        │    │  Handler        │
│  │ • decision      │    │                  │    │                 │
│  │ • confidence    │    │ • Toxic/Non-Toxic│    │ • Policy Engine │
│  │ • reasoning     │    │ • Confidence     │    │ • Action Exec   │
│  │ • processing_time│    │ • Categories     │    │ • User History  │
│  │ • template_ver  │    │ • Metadata       │    │ • Escalation    │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘
└─────────────────────────────────────────────────────────────────────────────────────┘
                                                           │
DECISION & ACTION LAYER                                    │
┌─────────────────────────────────────────────────────────┼─────────────────────────────┐
│  ┌─────────────────┐    ┌──────────────────┐             │                            │
│  │   Policy        │    │  Action          │◀────────────┘                            │
│  │   Engine        │───▶│  Execution       │                                          │
│  │                 │    │                  │                                          │
│  │ • Rules Config  │    │ • Allow/Log      │                                          │
│  │ • User History  │    │ • Flag/Escalate  │                                          │
│  │ • Repeat Check  │    │ • Ban/Timeout    │                                          │
│  │ • Severity Calc │    │ • Notifications  │                                          │
│  └─────────────────┘    └──────────────────┘                                          │
│                                   │                                                   │
│  ┌─────────────────┐    ┌──────────▼──────┐    ┌─────────────────┐                  │
│  │   Database      │◀───│  Transaction    │───▶│  Notification   │                  │
│  │   Storage       │    │  Manager        │    │  Service        │                  │
│  │                 │    │                 │    │                 │                  │
│  │ • PostgreSQL    │    │ • ACID Comply   │    │ • Slack/Teams   │                  │
│  │ • User History  │    │ • Rollback      │    │ • Email Alerts  │                  │
│  │ • Decisions     │    │ • Consistency   │    │ • Webhooks      │                  │
│  │ • Violations    │    │ • Audit Trail   │    │ • Dashboard     │                  │
│  │ • Audit Logs    │    │ • Backup        │    │ • Mobile Push   │                  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                   │
OBSERVABILITY & MONITORING LAYER   │
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┐    ┌──────────────────┐◀─────────────────────────────────────┐  │
│  │   Metrics       │───▶│  Prometheus      │                                      │  │
│  │   Collection    │    │  Server          │                                      │  │
│  │                 │    │                  │                                      │  │
│  │ • Request Count │    │ • Time Series DB │                                      │  │
│  │ • Latency       │    │ • Alerting       │                                      │  │
│  │ • Error Rate    │    │ • Retention      │                                      │  │
│  │ • Throughput    │    │ • Scraping       │                                      │  │
│  └─────────────────┘    └──────────────────┘                                      │  │
│                                   │                                               │  │
│  ┌─────────────────┐    ┌──────────▼──────┐    ┌─────────────────┐              │  │
│  │   Distributed   │───▶│  Jaeger         │───▶│  Grafana        │              │  │
│  │   Tracing       │    │  Collector      │    │  Dashboards     │              │  │
│  │                 │    │                 │    │                 │              │  │
│  │ • Request Spans │    │ • Trace Storage │    │ • Visualization │              │  │
│  │ • Service Map   │    │ • Query API     │    │ • Alerting      │              │  │
│  │ • Performance   │    │ • Sampling      │    │ • Reporting     │              │  │
│  │ • Dependencies  │    │ • Retention     │    │ • User Mgmt     │              │  │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘              │  │
│                                                                                  │  │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐             │  │
│  │   Structured    │───▶│  Log Aggregation │───▶│  Search &       │             │  │
│  │   Logging       │    │  (Optional ELK)  │    │  Analysis       │             │  │
│  │                 │    │                  │    │                 │             │  │
│  │ • JSON Format   │    │ • Elasticsearch  │    │ • Kibana        │             │  │
│  │ • Correlation   │    │ • Logstash       │    │ • Log Search    │             │  │
│  │ • Context       │    │ • Beats          │    │ • Dashboards    │             │  │
│  │ • Sampling      │    │ • Retention      │    │ • Alerting      │             │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘             │  │
│                                                                                  │  │
│  All Services ──────────────────────────────────────────────────────────────────┘  │
│  Export Metrics, Traces, and Logs                                                  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Service Communication Matrix

```
┌─────────────────┬─────────────────┬─────────────────┬─────────────────┬─────────────────┐
│     SERVICE     │  CHAT SIMULATOR │ LIGHTWEIGHT FLT │   MCP SERVER    │ DECISION HANDLER│
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Chat Simulator  │       -         │   HTTP POST     │       -         │       -         │
│                 │                 │   /filter       │                 │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Lightweight Flt │   WebSocket     │       -         │   HTTP POST     │       -         │
│                 │   /ws           │                 │   /moderate     │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ MCP Server      │   HTTP Response │   HTTP Response │       -         │   HTTP POST     │
│                 │                 │                 │                 │   /decide       │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Decision Handler│       -         │       -         │   HTTP Response │       -         │
│                 │                 │                 │                 │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ DeepSeek LLM    │       -         │       -         │   HTTP POST     │       -         │
│                 │                 │                 │ /v1/chat/compl  │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ PostgreSQL      │       -         │       -         │       -         │   SQL Queries   │
│                 │                 │                 │                 │   Connection    │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Redis           │       -         │   Rate Limiting │       -         │   Cache Access  │
│                 │                 │   Cache         │                 │                 │
├─────────────────┼─────────────────┼─────────────────┼─────────────────┼─────────────────┤
│ Prometheus      │   /metrics      │   /metrics      │   /metrics      │   /metrics      │
│                 │   Scraping      │   Scraping      │   Scraping      │   Scraping      │
└─────────────────┴─────────────────┴─────────────────┴─────────────────┴─────────────────┘
```

## Kubernetes Deployment Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              EKS CLUSTER                                            │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        CUSTOM NODEPOOL                                         │ │
│  │                    (role=custom-workload)                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │ │
│  │  │ MCP Server  │  │ Chat        │  │ Lightweight │  │ Decision    │           │ │
│  │  │             │  │ Simulator   │  │ Filter      │  │ Handler     │           │ │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │           │ │
│  │  │ │ Pod 1   │ │  │ │ Pod 1   │ │  │ │ Pod 1   │ │  │ │ Pod 1   │ │           │ │
│  │  │ │ Pod 2   │ │  │ └─────────┘ │  │ │ Pod 2   │ │  │ │ Pod 2   │ │           │ │
│  │  │ │ Pod 3   │ │  │             │  │ └─────────┘ │  │ └─────────┘ │           │ │
│  │  │ └─────────┘ │  │             │  │             │  │             │           │ │
│  │  │ HPA: 2-10   │  │ Replicas: 1 │  │ Replicas: 2 │  │ Replicas: 2 │           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │ │
│  │         │                 │                 │                 │               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │ │
│  │  │ Service     │  │ Service     │  │ Service     │  │ Service     │           │ │
│  │  │ ClusterIP   │  │ LoadBalancer│  │ ClusterIP   │  │ ClusterIP   │           │ │
│  │  │ :8000       │  │ :8002       │  │ :8001       │  │ :8003       │           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │ │
│  │                                                                               │ │
│  │  Tolerations: dedicated=custom-workload:NoSchedule                            │ │
│  │  Disruption Budget: Max Unavailable 1, Time Window: 4pm-5pm GMT              │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        DEFAULT NODEPOOL                                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │ │
│  │  │ PostgreSQL  │  │ Redis       │  │ Prometheus  │  │ Grafana     │           │ │
│  │  │ StatefulSet │  │ Deployment  │  │ Deployment  │  │ Deployment  │           │ │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │           │ │
│  │  │ │ Pod 1   │ │  │ │ Pod 1   │ │  │ │ Pod 1   │ │  │ │ Pod 1   │ │           │ │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │           │ │
│  │  │ Replicas: 1 │  │ Replicas: 1 │  │ Replicas: 1 │  │ Replicas: 1 │           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │ │
│  │         │                 │                 │                 │               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │ │
│  │  │ Service     │  │ Service     │  │ Service     │  │ Service     │           │ │
│  │  │ ClusterIP   │  │ ClusterIP   │  │ ClusterIP   │  │ LoadBalancer│           │ │
│  │  │ :5432       │  │ :6379       │  │ :9090       │  │ :3000       │           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │ │
│  │                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                           │ │
│  │  │ DeepSeek    │  │ Metrics     │  │ Jaeger      │                           │ │
│  │  │ LLM         │  │ Evaluator   │  │ Tracing     │                           │ │
│  │  │ (Existing)  │  │ Deployment  │  │ Deployment  │                           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                           │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        PERSISTENT STORAGE                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │ │
│  │  │ PostgreSQL  │  │ Prometheus  │  │ Grafana     │  │ Jaeger      │           │ │
│  │  │ PVC         │  │ PVC         │  │ PVC         │  │ PVC         │           │ │
│  │  │ 10Gi        │  │ 20Gi        │  │ 5Gi         │  │ 10Gi        │           │ │
│  │  │ ReadWriteOnce│  │ ReadWriteOnce│  │ ReadWriteOnce│  │ ReadWriteOnce│           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                        NETWORK & SECURITY                                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │ │
│  │  │ ALB Ingress │  │ Network     │  │ Pod Security│  │ RBAC        │           │ │
│  │  │ Controller  │  │ Policies    │  │ Policies    │  │ Policies    │           │ │
│  │  │             │  │             │  │             │  │             │           │ │
│  │  │ • SSL Term  │  │ • Pod-to-Pod│  │ • Non-root  │  │ • Service   │           │ │
│  │  │ • Path Route│  │ • Namespace │  │ • Read-only │  │   Accounts  │           │ │
│  │  │ • Health    │  │ • Egress    │  │ • Capabilities│  │ • Roles     │           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │ │
│  │                                                                               │ │
│  │  ┌─────────────┐  ┌─────────────┐                                             │ │
│  │  │ Secrets     │  │ ConfigMaps  │                                             │ │
│  │  │ Management  │  │ Management  │                                             │ │
│  │  │             │  │             │                                             │ │
│  │  │ • Encrypted │  │ • Templates │                                             │ │
│  │  │ • Rotation  │  │ • Config    │                                             │ │
│  │  │ • Access    │  │ • Env Vars  │                                             │ │
│  │  └─────────────┘  └─────────────┘                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Performance & Scaling Metrics

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            PERFORMANCE TARGETS                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  Component Latency Targets:                                                        │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐         │
│  │ Lightweight     │ MCP Server      │ Decision        │ End-to-End      │         │
│  │ Filter          │ (excl. LLM)     │ Handler         │ Pipeline        │         │
│  │                 │                 │                 │                 │         │
│  │    < 10ms       │    < 200ms      │    < 50ms       │    < 500ms      │         │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘         │
│                                                                                     │
│  Throughput Capacity:                                                              │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐         │
│  │ Messages/Second │ Concurrent      │ LLM Requests    │ Database        │         │
│  │                 │ Users           │                 │ Connections     │         │
│  │                 │                 │                 │                 │         │
│  │    1,000+       │    10,000+      │    100 conc     │    50 per svc   │         │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘         │
│                                                                                     │
│  Scaling Strategy:                                                                 │
│  • Horizontal Pod Autoscaler (HPA) based on CPU/Memory                            │
│  • Custom metrics: Queue depth, Response time, Error rate                         │
│  • Load balancing: Round-robin with health checks                                 │
│  • Database: Connection pooling, Read replicas for queries                        │
│  • Cache: Redis for rate limiting and session data                                │
│                                                                                     │
│  Resource Allocation:                                                              │
│  ┌─────────────────┬─────────────────┬─────────────────┬─────────────────┐         │
│  │ Service         │ CPU Request     │ Memory Request  │ Replicas        │         │
│  ├─────────────────┼─────────────────┼─────────────────┼─────────────────┤         │
│  │ MCP Server      │ 250m            │ 256Mi           │ 2-10 (HPA)      │         │
│  │ Chat Simulator  │ 100m            │ 128Mi           │ 1               │         │
│  │ Light Filter    │ 100m            │ 128Mi           │ 2               │         │
│  │ Decision Handler│ 200m            │ 256Mi           │ 2               │         │
│  │ PostgreSQL      │ 500m            │ 512Mi           │ 1               │         │
│  │ Redis           │ 100m            │ 128Mi           │ 1               │         │
│  └─────────────────┴─────────────────┴─────────────────┴─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────────────┘
```
