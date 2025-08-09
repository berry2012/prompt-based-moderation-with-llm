# Real-Time Moderation System - Directory Structure

```
moderation-system/
├── README.md
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── Makefile
│
├── services/
│   ├── mcp-server/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── request_models.py
│   │   │   │   └── response_models.py
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── prompt_service.py
│   │   │   │   ├── llm_client.py
│   │   │   │   └── validation_service.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   └── routes.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       ├── logging.py
│   │   │       └── metrics.py
│   │   └── tests/
│   │
│   ├── chat-simulator/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── simulator.py
│   │   │   ├── whisper_client.py
│   │   │   └── message_generator.py
│   │   └── data/
│   │       └── sample_messages.json
│   │
│   ├── lightweight-filter/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── filters/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── keyword_filter.py
│   │   │   │   └── profanity_filter.py
│   │   │   └── config/
│   │   │       ├── banned_words.txt
│   │   │       └── filter_config.yaml
│   │   └── tests/
│   │
│   ├── decision-handler/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── handlers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── policy_engine.py
│   │   │   │   └── action_executor.py
│   │   │   └── storage/
│   │   │       ├── __init__.py
│   │   │       └── database.py
│   │   └── migrations/
│   │
│   └── metrics-evaluator/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── collectors/
│       │   │   ├── __init__.py
│       │   │   ├── performance_collector.py
│       │   │   └── accuracy_collector.py
│       │   └── exporters/
│       │       ├── __init__.py
│       │       ├── prometheus_exporter.py
│       │       └── json_exporter.py
│       └── dashboards/
│           └── grafana_dashboard.json
│
├── shared/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── common_models.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── http_client.py
│   │   └── config.py
│   └── templates/
│       ├── moderation_templates.yaml
│       └── template_schema.json
│
├── deployment/
│   ├── docker/
│   │   └── docker-compose.override.yml
│   ├── kubernetes/
│   │   ├── namespace.yaml
│   │   ├── configmaps/
│   │   ├── secrets/
│   │   ├── deployments/
│   │   ├── services/
│   │   └── ingress/
│   └── helm/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── monitoring/
│   ├── prometheus/
│   │   └── prometheus.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   └── provisioning/
│   └── jaeger/
│       └── jaeger-config.yaml
│
└── tests/
    ├── integration/
    ├── load/
    └── e2e/
```
