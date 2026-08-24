### Step 2: Design the Observability Stack

Observability requires three pillars (metrics, logs, traces) working together with correlation so that operators can move from alert to root cause in minutes rather than hours.

**Observability Architecture**:

```
                    ┌─────────────────────────────────────────────┐
                    │              Grafana Dashboards              │
                    │         (Unified view of all signals)        │
                    └───────┬──────────┬──────────┬───────────────┘
                            │          │          │
                    ┌───────▼───┐ ┌────▼────┐ ┌───▼──────────┐
                    │Prometheus │ │  Loki   │ │    Tempo      │
                    │ (Metrics) │ │ (Logs)  │ │  (Traces)     │
                    └───────▲───┘ └────▲────┘ └───▲──────────┘
                            │          │          │
                    ┌───────┴──────────┴──────────┴───────────┐
                    │         OpenTelemetry Collector           │
                    │   (Receives, processes, exports all       │
                    │    telemetry with unified pipeline)       │
                    └───────▲──────────▲──────────▲───────────┘
                            │          │          │
                   ┌────────┴──┐ ┌─────┴────┐ ┌──┴─────────┐
                   │ Service A │ │ Service B│ │ Service C  │
                   │ (OTel SDK)│ │(OTel SDK)│ │(OTel SDK)  │
                   └───────────┘ └──────────┘ └────────────┘
```

**OpenTelemetry Collector Configuration**:

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318
  prometheus:
    config:
      scrape_configs:
        - job_name: 'kubernetes-pods'
          kubernetes_sd_configs:
            - role: pod
          relabel_configs:
            - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
              action: keep
              regex: true

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128
  attributes:
    actions:
      - key: environment
        value: production
        action: upsert
      - key: cluster
        value: us-east-1-prod
        action: upsert
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors-always
        type: status_code
        status_code: { status_codes: [ERROR] }
      - name: slow-requests
        type: latency
        latency: { threshold_ms: 1000 }
      - name: probabilistic-sample
        type: probabilistic
        probabilistic: { sampling_percentage: 10 }

exporters:
  prometheusremotewrite:
    endpoint: "http://prometheus:9090/api/v1/write"
  loki:
    endpoint: "http://loki:3100/loki/api/v1/push"
  otlp/tempo:
    endpoint: "tempo:4317"
    tls:
      insecure: true

service:
  pipelines:
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch]
      exporters: [prometheusremotewrite]
    logs:
      receivers: [otlp]
      processors: [memory_limiter, attributes, batch]
      exporters: [loki]
    traces:
      receivers: [otlp]
      processors: [memory_limiter, tail_sampling, batch]
      exporters: [otlp/tempo]
```

**Structured Logging Standard**:

```json
{
  "timestamp": "2026-03-20T14:23:01.123Z",
  "level": "ERROR",
  "service": "checkout-api",
  "trace_id": "abc123def456",
  "span_id": "789ghi012",
  "correlation_id": "order-98765",
  "message": "Payment processing failed",
  "error": {
    "type": "PaymentGatewayTimeout",
    "message": "Upstream timeout after 5000ms",
    "stack": "..."
  },
  "context": {
    "user_id": "u-12345",
    "order_id": "ord-98765",
    "payment_method": "credit_card",
    "amount_cents": 4999
  },
  "http": {
    "method": "POST",
    "path": "/api/v1/checkout",
    "status_code": 504,
    "duration_ms": 5023
  }
}
```

**Grafana Dashboard as Code**:

```json
{
  "dashboard": {
    "title": "Service SLO Dashboard",
    "panels": [
      {
        "title": "Error Budget Remaining (30d)",
        "type": "gauge",
        "targets": [{
          "expr": "slo:error_budget_remaining:ratio{service=\"checkout-api\"} * 100",
          "legendFormat": "Budget %"
        }],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "color": "red", "value": 0 },
                { "color": "orange", "value": 25 },
                { "color": "yellow", "value": 50 },
                { "color": "green", "value": 75 }
              ]
            },
            "min": 0, "max": 100, "unit": "percent"
          }
        }
      },
      {
        "title": "Request Rate and Errors",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"checkout-api\"}[5m]))",
            "legendFormat": "Total RPS"
          },
          {
            "expr": "sum(rate(http_requests_total{service=\"checkout-api\", code=~\"5..\"}[5m]))",
            "legendFormat": "Error RPS"
          }
        ]
      },
      {
        "title": "Latency Distribution",
        "type": "heatmap",
        "targets": [{
          "expr": "sum(rate(http_request_duration_seconds_bucket{service=\"checkout-api\"}[5m])) by (le)",
          "legendFormat": "{{le}}"
        }]
      }
    ]
  }
}
```
