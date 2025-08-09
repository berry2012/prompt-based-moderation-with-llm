# System Architecture Diagram

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           Real-Time Moderation System                               │
│                                                                                     │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐               │
│  │   Chat          │    │  Lightweight     │    │   MCP Server    │               │
│  │   Simulator     │───▶│  Filter          │───▶│  (Model Context │               │
│  │                 │    │  (Optional)      │    │   Protocol)     │               │
│  │ • WebSocket     │    │ • Keyword Filter │    │ • Prompt Mgmt   │               │
│  │ • Message Gen   │    │ • Rate Limiting  │    │ • LLM Interface │               │
│  │ • Whisper STT   │    │ • PII Detection  │    │ • Validation    │               │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘               │
│           │                       │                       │                        │
│           │              ┌────────▼────────┐             │                        │
│           │              │  Filter Results │             │                        │
│           │              │ • should_process │             │                        │
│           │              │ • confidence    │             │                        │
│           │              │ • matched_patterns│            │                        │
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
│  └─────────────────┘    └──────────────────┘    └─────────────────┘
│                                                           │
│  ┌─────────────────┐    ┌──────────────────┐             │
│  │   Database      │◀───│  Action          │◀────────────┘
│  │   Storage       │    │  Execution       │
│  │                 │    │                  │
│  │ • PostgreSQL    │    │ • Allow/Log      │
│  │ • User History  │    │ • Flag/Escalate  │
│  │ • Decisions     │    │ • Ban/Timeout    │
│  │ • Violations    │    │ • Notifications  │
│  └─────────────────┘    └──────────────────┘
│                                   │
│  ┌─────────────────┐    ┌──────────────────┐
│  │   Metrics &     │◀───│  Logging &       │◀─────────────────────┐
│  │   Evaluation    │    │  Monitoring      │                      │
│  │                 │    │                  │                      │
│  │ • Prometheus    │    │ • Structured     │                      │
│  │ • Performance   │    │ • Grafana        │                      │
│  │ • Accuracy      │    │ • Jaeger Tracing │                      │
│  │ • Cost Tracking │    │ • Health Checks  │                      │
│  └─────────────────┘    └──────────────────┘                      │
│                                   │                               │
│                                   └───────────────────────────────┘
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Component Interaction Flow

### 1. Message Processing Pipeline

```
┌─────────────┐
│ Chat Message│
│ Generated   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Lightweight │────▶│ Should      │────▶│ MCP Server  │
│ Filter      │     │ Process?    │     │ Processing  │
│ • Keywords  │     │             │     │             │
│ • Rate Limit│     │ Yes/No      │     │ • Template  │
│ • PII Check │     │             │     │ • LLM Call  │
└─────────────┘     └─────────────┘     │ • Validation│
       │                   │            └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Filter      │     │ Block/Skip  │     │ Moderation  │
│ Results     │     │ Message     │     │ Result      │
│ Logged      │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ Decision    │
                                        │ Handler     │
                                        │ • Policy    │
                                        │ • Action    │
                                        └─────────────┘
```

### 2. Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Data Flow Layers                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Input Layer                                                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ Text Chat   │  │ Voice Chat  │  │ System      │  │ Webhook     │           │
│  │ Messages    │  │ (Whisper)   │  │ Events      │  │ Events      │           │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘           │
│         │                 │                 │                 │               │
│         └─────────────────┼─────────────────┼─────────────────┘               │
│                           │                 │                                 │
│  Processing Layer         │                 │                                 │
│  ┌─────────────────────────▼─────────────────▼─────────────────┐               │
│  │                 Message Normalization                      │               │
│  │  • Text cleaning  • Language detection  • Format validation│               │
│  └─────────────────────────┬───────────────────────────────────┘               │
│                           │                                                   │
│  ┌─────────────────────────▼─────────────────┐                                │
│  │            Lightweight Filter             │                                │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐  │                                │
│  │  │Keywords │ │Rate     │ │PII Pattern  │  │                                │
│  │  │Filter   │ │Limiting │ │Detection    │  │                                │
│  │  └─────────┘ └─────────┘ └─────────────┘  │                                │
│  └─────────────────────────┬───────────────────┘                              │
│                           │                                                   │
│  ┌─────────────────────────▼─────────────────┐                                │
│  │              MCP Server                   │                                │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐  │                                │
│  │  │Template │ │LLM      │ │Response     │  │                                │
│  │  │Selection│ │Request  │ │Parsing      │  │                                │
│  │  └─────────┘ └─────────┘ └─────────────┘  │                                │
│  └─────────────────────────┬───────────────────┘                              │
│                           │                                                   │
│  Decision Layer           │                                                   │
│  ┌─────────────────────────▼─────────────────┐                                │
│  │            Decision Handler               │                                │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────┐  │                                │
│  │  │Policy   │ │User     │ │Action       │  │                                │
│  │  │Engine   │ │History  │ │Execution    │  │                                │
│  │  └─────────┘ └─────────┘ └─────────────┘  │                                │
│  └─────────────────────────┬───────────────────┘                              │
│                           │                                                   │
│  Storage Layer            │                                                   │
│  ┌─────────────────────────▼─────────────────┐                                │
│  │  ┌─────────────┐  ┌─────────────────────┐ │                                │
│  │  │ PostgreSQL  │  │      Redis          │ │                                │
│  │  │ • Decisions │  │ • Rate Limiting     │ │                                │
│  │  │ • History   │  │ • Session Cache     │ │                                │
│  │  │ • Users     │  │ • Temp Storage      │ │                                │
│  │  └─────────────┘  └─────────────────────┘ │                                │
│  └─────────────────────────┬───────────────────┘                              │
│                           │                                                   │
│  Observability Layer      │                                                   │
│  ┌─────────────────────────▼─────────────────┐                                │
│  │  ┌─────────────┐  ┌─────────────────────┐ │                                │
│  │  │ Prometheus  │  │      Grafana        │ │                                │
│  │  │ • Metrics   │  │ • Dashboards        │ │                                │
│  │  │ • Alerts    │  │ • Visualization     │ │                                │
│  │  └─────────────┘  └─────────────────────┘ │                                │
│  │  ┌─────────────┐  ┌─────────────────────┐ │                                │
│  │  │ Jaeger      │  │   Structured        │ │                                │
│  │  │ • Tracing   │  │   Logging           │ │                                │
│  │  │ • Spans     │  │ • JSON Format       │ │                                │
│  │  └─────────────┘  └─────────────────────┘ │                                │
│  └─────────────────────────────────────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Service Communication Patterns

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Service Communication Matrix                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Synchronous HTTP/REST Communication                                           │
│  ┌─────────────┐    HTTP POST     ┌─────────────┐    HTTP POST     ┌─────────┐ │
│  │ Chat        │ ──────────────▶  │ Lightweight │ ──────────────▶  │ MCP     │ │
│  │ Simulator   │    /filter       │ Filter      │    /moderate     │ Server  │ │
│  └─────────────┘                  └─────────────┘                  └─────────┘ │
│         │                                │                              │       │
│         │                                │         HTTP POST            │       │
│         │                                └──────────────────────────────┼───┐   │
│         │                                         /decide               │   │   │
│         │                                                               │   │   │
│         │        WebSocket                ┌─────────────┐               │   │   │
│         └────────────────────────────────▶│ Decision    │◀──────────────┘   │   │
│                  Real-time               │ Handler     │                   │   │
│                                          └─────────────┘                   │   │
│                                                 │                          │   │
│  Asynchronous Communication                     │                          │   │
│  ┌─────────────┐    Async Calls   ┌─────────────▼─────────────┐             │   │
│  │ Notification│◀─────────────────│ Background Tasks          │             │   │
│  │ Service     │   Webhooks       │ • Database Updates        │             │   │
│  │ (Slack/     │                  │ • Metric Collection       │             │   │
│  │  Teams)     │                  │ • Audit Logging           │             │   │
│  └─────────────┘                  └───────────────────────────┘             │   │
│                                                                             │   │
│  External Service Integration                                               │   │
│  ┌─────────────┐    HTTP POST     ┌─────────────────────────────────────────┼───┘
│  │ DeepSeek    │◀─────────────────│ LLM Client                              │
│  │ LLM         │  /v1/chat/       │ • Retry Logic                           │
│  │ Endpoint    │  completions     │ • Timeout Handling                      │
│  └─────────────┘                  │ • Response Parsing                      │
│                                   └─────────────────────────────────────────┘
│                                                                                 │
│  Database Connections                                                           │
│  ┌─────────────┐    Connection    ┌─────────────┐    Connection    ┌─────────┐ │
│  │ Decision    │    Pool          │ PostgreSQL  │    Pool          │ Metrics │ │
│  │ Handler     │◀────────────────▶│ Database    │◀────────────────▶│ Service │ │
│  └─────────────┘                  └─────────────┘                  └─────────┘ │
│                                                                                 │
│  Monitoring & Observability                                                    │
│  ┌─────────────┐    Metrics       ┌─────────────┐    Queries       ┌─────────┐ │
│  │ All         │    Export        │ Prometheus  │    PromQL        │ Grafana │ │
│  │ Services    │─────────────────▶│ Server      │─────────────────▶│ Dashbrd │ │
│  └─────────────┘                  └─────────────┘                  └─────────┘ │
│         │                                                                       │
│         │        Trace Data       ┌─────────────┐                              │
│         └────────────────────────▶│ Jaeger      │                              │
│                 OpenTelemetry     │ Collector   │                              │
│                                   └─────────────┘                              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Deployment Architecture on EKS

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    EKS Cluster Deployment Architecture                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Custom Nodepool                                     │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ MCP Server  │  │ Chat        │  │ Lightweight │  │ Decision    │       │ │
│  │  │ Pod         │  │ Simulator   │  │ Filter      │  │ Handler     │       │ │
│  │  │ (3 replicas)│  │ Pod         │  │ Pod         │  │ Pod         │       │ │
│  │  │             │  │ (1 replica) │  │ (2 replicas)│  │ (2 replicas)│       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  │         │                 │                 │                 │           │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ Service     │  │ Service     │  │ Service     │  │ Service     │       │ │
│  │  │ ClusterIP   │  │ LoadBalancer│  │ ClusterIP   │  │ ClusterIP   │       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  │                                                                           │ │
│  │  Node Selector: role=custom-workload                                      │ │
│  │  Tolerations: dedicated=custom-workload:NoSchedule                        │ │
│  │  Disruption Budget: 4pm-5pm British time                                  │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Default Nodepool                                    │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ PostgreSQL  │  │ Redis       │  │ Prometheus  │  │ Grafana     │       │ │
│  │  │ StatefulSet │  │ Deployment  │  │ Deployment  │  │ Deployment  │       │ │
│  │  │ (1 replica) │  │ (1 replica) │  │ (1 replica) │  │ (1 replica) │       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  │         │                 │                 │                 │           │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │ │
│  │  │ Service     │  │ Service     │  │ Service     │  │ Service     │       │ │
│  │  │ ClusterIP   │  │ ClusterIP   │  │ ClusterIP   │  │ LoadBalancer│       │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │ │
│  │                                                                           │ │
│  │  ┌─────────────┐  ┌─────────────┐                                         │ │
│  │  │ DeepSeek    │  │ Metrics     │                                         │ │
│  │  │ LLM         │  │ Evaluator   │                                         │ │
│  │  │ (Existing)  │  │ Pod         │                                         │ │
│  │  └─────────────┘  └─────────────┘                                         │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Persistent Storage                                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │ │
│  │  │ PostgreSQL  │  │ Prometheus  │  │ Grafana     │                        │ │
│  │  │ PVC         │  │ PVC         │  │ PVC         │                        │ │
│  │  │ 10Gi        │  │ 20Gi        │  │ 5Gi         │                        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                        │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        Network & Security                                  │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                        │ │
│  │  │ Ingress     │  │ Network     │  │ Pod Security│                        │ │
│  │  │ Controller  │  │ Policies    │  │ Policies    │                        │ │
│  │  │ (ALB)       │  │             │  │             │                        │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                        │ │
│  │                                                                           │ │
│  │  ┌─────────────┐  ┌─────────────┐                                         │ │
│  │  │ Secrets     │  │ ConfigMaps  │                                         │ │
│  │  │ Management  │  │ Management  │                                         │ │
│  │  │             │  │             │                                         │ │
│  │  └─────────────┘  └─────────────┘                                         │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 5. Error Handling and Resilience Patterns

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        Error Handling & Resilience                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Circuit Breaker Pattern                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                        │
│  │ MCP Server  │───▶│ Circuit     │───▶│ DeepSeek    │                        │
│  │             │    │ Breaker     │    │ LLM         │                        │
│  │             │    │ • Closed    │    │             │                        │
│  │             │    │ • Open      │    │             │                        │
│  │             │    │ • Half-Open │    │             │                        │
│  └─────────────┘    └─────────────┘    └─────────────┘                        │
│                             │                                                  │
│                             ▼                                                  │
│                    ┌─────────────┐                                            │
│                    │ Fallback    │                                            │
│                    │ Response    │                                            │
│                    │ • Cached    │                                            │
│                    │ • Default   │                                            │
│                    └─────────────┘                                            │
│                                                                                 │
│  Retry with Exponential Backoff                                               │
│  ┌─────────────┐                                                              │
│  │ Request     │                                                              │
│  │ Failed      │                                                              │
│  └──────┬──────┘                                                              │
│         │                                                                     │
│         ▼                                                                     │
│  ┌─────────────┐    Wait 1s     ┌─────────────┐    Wait 2s     ┌───────────┐ │
│  │ Retry 1     │───────────────▶│ Retry 2     │───────────────▶│ Retry 3   │ │
│  │             │                │             │                │           │ │
│  └─────────────┘                └─────────────┘                └───────────┘ │
│         │                               │                             │       │
│         ▼                               ▼                             ▼       │
│  ┌─────────────┐                ┌─────────────┐                ┌───────────┐ │
│  │ Success/    │                │ Success/    │                │ Final     │ │
│  │ Continue    │                │ Continue    │                │ Failure   │ │
│  └─────────────┘                └─────────────┘                └───────────┘ │
│                                                                                 │
│  Health Check & Auto-Recovery                                                  │
│  ┌─────────────┐    Health      ┌─────────────┐    Restart     ┌───────────┐ │
│  │ Kubernetes  │    Checks      │ Unhealthy   │    Pod         │ New Pod   │ │
│  │ Probe       │───────────────▶│ Pod         │───────────────▶│ Started   │ │
│  │ • Liveness  │    Failed      │             │                │           │ │
│  │ • Readiness │                │             │                │           │ │
│  └─────────────┘                └─────────────┘                └───────────┘ │
│                                                                                 │
│  Data Consistency & Transactions                                               │
│  ┌─────────────┐    Begin Tx    ┌─────────────┐    Commit/     ┌───────────┐ │
│  │ Decision    │───────────────▶│ Database    │    Rollback    │ Audit     │ │
│  │ Handler     │                │ Transaction │───────────────▶│ Log       │ │
│  │             │                │             │                │           │ │
│  └─────────────┘                └─────────────┘                └───────────┘ │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Performance and Scaling Characteristics

### Latency Targets
- **Lightweight Filter**: < 10ms
- **MCP Server**: < 200ms (excluding LLM)
- **Decision Handler**: < 50ms
- **End-to-end Pipeline**: < 500ms (including LLM)

### Throughput Capacity
- **Messages per Second**: 1,000+
- **Concurrent Users**: 10,000+
- **LLM Requests**: 100 concurrent
- **Database Connections**: 50 per service

### Scaling Strategy
- **Horizontal Pod Autoscaler**: CPU/Memory based
- **Custom Metrics**: Queue depth, response time
- **Load Balancing**: Round-robin with health checks
- **Database**: Connection pooling, read replicas

This architecture diagram provides a comprehensive view of the system's structure, data flow, service interactions, and deployment strategy specifically designed for your EKS cluster with custom nodepool configuration.
