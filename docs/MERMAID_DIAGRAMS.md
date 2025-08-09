# System Architecture - Mermaid Diagrams

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph "Real-Time Moderation System"
        CS[Chat Simulator<br/>• WebSocket<br/>• Message Gen<br/>• Whisper STT]
        LF[Lightweight Filter<br/>• Keyword Filter<br/>• Rate Limiting<br/>• PII Detection]
        MCP[MCP Server<br/>• Prompt Management<br/>• LLM Interface<br/>• Validation]
        PTS[Prompt Template System<br/>• 7 Templates<br/>• Versioning<br/>• YAML Config]
        DLM[DeepSeek LLM<br/>• Chat API<br/>• JSON Response<br/>• Error Handling]
        DH[Decision Handler<br/>• Policy Engine<br/>• Action Execution<br/>• User History]
        DB[(Database Storage<br/>• PostgreSQL<br/>• User History<br/>• Decisions)]
        ME[Metrics & Evaluation<br/>• Prometheus<br/>• Performance<br/>• Accuracy]
        
        CS -->|HTTP POST /filter| LF
        LF -->|should_process=true| MCP
        LF -->|should_process=false| ME
        MCP -->|Template Request| PTS
        MCP -->|LLM Request| DLM
        DLM -->|Response| MCP
        MCP -->|Moderation Result| DH
        DH -->|Store Decision| DB
        DH -->|Action Execution| ME
        CS -.->|WebSocket| ME
        DB -.->|Query History| DH
    end
```

## 2. Data Flow Pipeline

```mermaid
sequenceDiagram
    participant CS as Chat Simulator
    participant LF as Lightweight Filter
    participant MCP as MCP Server
    participant PTS as Prompt Templates
    participant LLM as DeepSeek LLM
    participant DH as Decision Handler
    participant DB as Database
    participant ME as Metrics

    CS->>LF: POST /filter (message, user_id, channel_id)
    LF->>LF: Apply keyword filters, rate limiting, PII check
    
    alt Message should be processed
        LF->>MCP: Filter passed - process message
        MCP->>PTS: Get prompt template
        PTS->>MCP: Return formatted prompt
        MCP->>LLM: POST /v1/chat/completions
        LLM->>MCP: Moderation decision + confidence
        MCP->>DH: POST /decide (decision, confidence, reasoning)
        DH->>DB: Store decision and user history
        DH->>DH: Execute policy action (allow/flag/ban)
        DH->>ME: Log metrics and performance data
        DH->>CS: Return final decision
    else Message blocked by filter
        LF->>ME: Log filter decision
        LF->>CS: Return blocked status
    end

    ME->>ME: Update dashboards and alerts
```

## 3. Service Communication Architecture

```mermaid
graph LR
    subgraph "External Services"
        LLM[DeepSeek LLM<br/>Endpoint]
        SLACK[Slack/Teams<br/>Webhooks]
    end
    
    subgraph "Core Services"
        CS[Chat Simulator<br/>:8002]
        LF[Lightweight Filter<br/>:8001]
        MCP[MCP Server<br/>:8000]
        DH[Decision Handler<br/>:8003]
        ME[Metrics Evaluator<br/>:8004]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Database)]
        RD[(Redis<br/>Cache)]
    end
    
    subgraph "Monitoring"
        PR[Prometheus<br/>:9090]
        GR[Grafana<br/>:3000]
        JG[Jaeger<br/>:16686]
    end
    
    CS -->|HTTP/WebSocket| LF
    LF -->|HTTP| MCP
    MCP -->|HTTP| LLM
    MCP -->|HTTP| DH
    DH -->|SQL| PG
    DH -->|Cache| RD
    DH -->|Webhook| SLACK
    
    CS -->|Metrics| PR
    LF -->|Metrics| PR
    MCP -->|Metrics| PR
    DH -->|Metrics| PR
    ME -->|Metrics| PR
    
    PR -->|Query| GR
    CS -->|Traces| JG
    MCP -->|Traces| JG
    DH -->|Traces| JG
```

## 4. Kubernetes Deployment Architecture

```mermaid
graph TB
    subgraph "EKS Cluster"
        subgraph "Custom Nodepool (role=custom-workload)"
            subgraph "Moderation Services"
                MCP_POD[MCP Server Pods<br/>3 replicas<br/>HPA enabled]
                CS_POD[Chat Simulator Pod<br/>1 replica<br/>LoadBalancer]
                LF_POD[Lightweight Filter Pods<br/>2 replicas<br/>ClusterIP]
                DH_POD[Decision Handler Pods<br/>2 replicas<br/>ClusterIP]
            end
            
            subgraph "Services"
                MCP_SVC[mcp-server-service<br/>ClusterIP:8000]
                CS_SVC[chat-simulator-service<br/>LoadBalancer:8002]
                LF_SVC[lightweight-filter-service<br/>ClusterIP:8001]
                DH_SVC[decision-handler-service<br/>ClusterIP:8003]
            end
        end
        
        subgraph "Default Nodepool"
            subgraph "Infrastructure Services"
                PG_POD[PostgreSQL<br/>StatefulSet<br/>1 replica]
                RD_POD[Redis<br/>Deployment<br/>1 replica]
                PR_POD[Prometheus<br/>Deployment<br/>1 replica]
                GR_POD[Grafana<br/>Deployment<br/>1 replica]
                LLM_POD[DeepSeek LLM<br/>Existing Deployment]
                ME_POD[Metrics Evaluator<br/>Deployment<br/>1 replica]
            end
        end
        
        subgraph "Storage"
            PG_PVC[PostgreSQL PVC<br/>10Gi]
            PR_PVC[Prometheus PVC<br/>20Gi]
            GR_PVC[Grafana PVC<br/>5Gi]
        end
        
        subgraph "Network & Security"
            ING[ALB Ingress<br/>Controller]
            NP[Network Policies]
            PSP[Pod Security<br/>Policies]
        end
    end
    
    MCP_POD --> MCP_SVC
    CS_POD --> CS_SVC
    LF_POD --> LF_SVC
    DH_POD --> DH_SVC
    
    PG_POD --> PG_PVC
    PR_POD --> PR_PVC
    GR_POD --> GR_PVC
    
    ING --> CS_SVC
    ING --> GR_POD
```

## 5. Error Handling and Resilience

```mermaid
graph TD
    subgraph "Circuit Breaker Pattern"
        REQ[Request to LLM]
        CB{Circuit Breaker<br/>State?}
        CLOSED[Closed<br/>Normal Operation]
        OPEN[Open<br/>Fast Fail]
        HALF[Half-Open<br/>Test Request]
        FALLBACK[Fallback Response<br/>Cached/Default]
        
        REQ --> CB
        CB -->|Healthy| CLOSED
        CB -->|Failing| OPEN
        CB -->|Testing| HALF
        OPEN --> FALLBACK
        HALF -->|Success| CLOSED
        HALF -->|Failure| OPEN
    end
    
    subgraph "Retry Strategy"
        FAIL[Request Failed]
        RETRY1[Retry 1<br/>Wait 1s]
        RETRY2[Retry 2<br/>Wait 2s]
        RETRY3[Retry 3<br/>Wait 4s]
        SUCCESS[Success]
        FINAL_FAIL[Final Failure]
        
        FAIL --> RETRY1
        RETRY1 -->|Fail| RETRY2
        RETRY1 -->|Success| SUCCESS
        RETRY2 -->|Fail| RETRY3
        RETRY2 -->|Success| SUCCESS
        RETRY3 -->|Fail| FINAL_FAIL
        RETRY3 -->|Success| SUCCESS
    end
    
    subgraph "Health Checks"
        K8S[Kubernetes Probes]
        LIVENESS[Liveness Probe<br/>/health]
        READINESS[Readiness Probe<br/>/health]
        UNHEALTHY[Unhealthy Pod]
        RESTART[Pod Restart]
        
        K8S --> LIVENESS
        K8S --> READINESS
        LIVENESS -->|Fail| UNHEALTHY
        READINESS -->|Fail| UNHEALTHY
        UNHEALTHY --> RESTART
    end
```

## 6. Monitoring and Observability Flow

```mermaid
graph LR
    subgraph "Application Services"
        APP1[MCP Server]
        APP2[Chat Simulator]
        APP3[Lightweight Filter]
        APP4[Decision Handler]
    end
    
    subgraph "Metrics Collection"
        PROM[Prometheus<br/>Server]
        METRICS[/metrics endpoints]
    end
    
    subgraph "Visualization"
        GRAF[Grafana<br/>Dashboards]
        ALERT[Alert Manager]
    end
    
    subgraph "Tracing"
        JAEGER[Jaeger<br/>Collector]
        TRACES[Distributed<br/>Traces]
    end
    
    subgraph "Logging"
        LOGS[Structured<br/>Logs]
        ELK[ELK Stack<br/>Optional]
    end
    
    APP1 -->|Expose| METRICS
    APP2 -->|Expose| METRICS
    APP3 -->|Expose| METRICS
    APP4 -->|Expose| METRICS
    
    METRICS -->|Scrape| PROM
    PROM -->|Query| GRAF
    PROM -->|Alerts| ALERT
    
    APP1 -->|Send Spans| JAEGER
    APP2 -->|Send Spans| JAEGER
    APP3 -->|Send Spans| JAEGER
    APP4 -->|Send Spans| JAEGER
    JAEGER --> TRACES
    
    APP1 -->|JSON Logs| LOGS
    APP2 -->|JSON Logs| LOGS
    APP3 -->|JSON Logs| LOGS
    APP4 -->|JSON Logs| LOGS
    LOGS -.->|Optional| ELK
```

## 7. Security Architecture

```mermaid
graph TB
    subgraph "Network Security"
        ING[Ingress Controller<br/>TLS Termination]
        NP[Network Policies<br/>Pod-to-Pod Rules]
        SG[Security Groups<br/>Node-level Rules]
    end
    
    subgraph "Authentication & Authorization"
        API_KEY[API Key<br/>Authentication]
        RBAC[Kubernetes RBAC<br/>Service Accounts]
        IAM[AWS IAM Roles<br/>Pod Identity]
    end
    
    subgraph "Data Protection"
        SECRETS[Kubernetes Secrets<br/>Encrypted at Rest]
        PII_FILTER[PII Detection<br/>& Redaction]
        AUDIT[Audit Logging<br/>All Decisions]
    end
    
    subgraph "Input Validation"
        PROMPT_INJ[Prompt Injection<br/>Protection]
        RATE_LIMIT[Rate Limiting<br/>Per User/Global]
        INPUT_VAL[Input Validation<br/>Schema Checks]
    end
    
    ING --> API_KEY
    API_KEY --> RBAC
    RBAC --> IAM
    
    NP --> SG
    SECRETS --> PII_FILTER
    PII_FILTER --> AUDIT
    
    PROMPT_INJ --> RATE_LIMIT
    RATE_LIMIT --> INPUT_VAL
```

These Mermaid diagrams provide interactive, visual representations of the system architecture that can be rendered in GitHub, documentation sites, and other platforms that support Mermaid syntax.
