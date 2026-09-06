### Step 1: Define SLOs, SLIs, and Error Budgets

Service-level objectives are the foundation of SRE practice. Every production service needs clearly defined SLIs that measure user-facing behavior, SLOs that set reliability targets, and error budgets that balance reliability investment against feature velocity.

**SLI Categories and Measurement**:

| SLI Type | What It Measures | Example Metric |
|----------|-----------------|----------------|
| **Availability** | Proportion of successful requests | `successful_requests / total_requests` |
| **Latency** | Proportion of requests faster than threshold | `requests_under_300ms / total_requests` |
| **Throughput** | Proportion of time system handles expected load | `minutes_above_baseline / total_minutes` |
| **Correctness** | Proportion of responses returning correct data | `correct_responses / total_responses` |
| **Freshness** | Proportion of data updated within threshold | `fresh_records / total_records` |

**SLO Specification Document**:

```yaml
# slo-spec.yaml - Service Level Objective specification
service: checkout-api
team: platform-payments
version: "1.2"

slis:
  - name: availability
    description: "Proportion of non-5xx responses to total requests"
    query: |
      sum(rate(http_requests_total{service="checkout-api", code!~"5.."}[5m]))
      /
      sum(rate(http_requests_total{service="checkout-api"}[5m]))
    unit: ratio

  - name: latency_p99
    description: "Proportion of requests completing under 500ms"
    query: |
      sum(rate(http_request_duration_seconds_bucket{service="checkout-api", le="0.5"}[5m]))
      /
      sum(rate(http_request_duration_seconds_count{service="checkout-api"}[5m]))
    unit: ratio

slos:
  - name: checkout-availability
    sli: availability
    target: 0.999          # 99.9% - allows ~8.7 hours downtime per year
    window: 30d            # rolling 30-day window
    alerting:
      burn_rate_short: 14.4  # 2% budget consumed in 1 hour
      burn_rate_long: 6.0    # 5% budget consumed in 6 hours

  - name: checkout-latency
    sli: latency_p99
    target: 0.99           # 99% of requests under 500ms
    window: 30d
    alerting:
      burn_rate_short: 14.4
      burn_rate_long: 6.0

error_budget_policy:
  actions:
    - condition: "budget_remaining > 50%"
      action: "Normal feature development velocity"
    - condition: "budget_remaining > 25%"
      action: "Prioritize reliability work alongside features"
    - condition: "budget_remaining > 0%"
      action: "Halt feature launches; focus on reliability"
    - condition: "budget_remaining <= 0%"
      action: "Freeze all changes; incident-level response"
```

**Burn Rate Alerting with Prometheus**:

```yaml
# prometheus-rules.yaml - Multi-window burn rate alerts
groups:
  - name: slo-alerts
    rules:
      # Fast burn: 2% of 30-day budget consumed in 1 hour
      - alert: CheckoutHighErrorBurnRate
        expr: |
          (
            1 - (sum(rate(http_requests_total{service="checkout-api", code!~"5.."}[1h]))
            / sum(rate(http_requests_total{service="checkout-api"}[1h])))
          )
          /
          (1 - 0.999) > 14.4
          AND
          (
            1 - (sum(rate(http_requests_total{service="checkout-api", code!~"5.."}[5m]))
            / sum(rate(http_requests_total{service="checkout-api"}[5m])))
          )
          /
          (1 - 0.999) > 14.4
        for: 2m
        labels:
          severity: critical
          team: platform-payments
        annotations:
          summary: "Checkout API burning error budget rapidly"
          description: "Burn rate {{ $value }}x over 1h window. Budget will exhaust in {{ printf \"%.1f\" (div 100 $value) }} hours."
          runbook: "https://runbooks.internal/checkout-api/high-error-rate"

      # Slow burn: 5% of 30-day budget consumed in 6 hours
      - alert: CheckoutSlowErrorBurnRate
        expr: |
          (
            1 - (sum(rate(http_requests_total{service="checkout-api", code!~"5.."}[6h]))
            / sum(rate(http_requests_total{service="checkout-api"}[6h])))
          )
          /
          (1 - 0.999) > 6.0
          AND
          (
            1 - (sum(rate(http_requests_total{service="checkout-api", code!~"5.."}[30m]))
            / sum(rate(http_requests_total{service="checkout-api"}[30m])))
          )
          /
          (1 - 0.999) > 6.0
        for: 5m
        labels:
          severity: warning
          team: platform-payments
        annotations:
          summary: "Checkout API burning error budget steadily"
          runbook: "https://runbooks.internal/checkout-api/slow-burn"

      # Error budget remaining gauge
      - record: slo:error_budget_remaining:ratio
        expr: |
          1 - (
            (1 - (sum_over_time((sum(rate(http_requests_total{service="checkout-api", code!~"5.."}[5m]))[30d:5m]))
            / sum_over_time((sum(rate(http_requests_total{service="checkout-api"}[5m]))[30d:5m]))))
            /
            (1 - 0.999)
          )
```

**Error Budget Calculation**:

```
Error budget (30 days) = 1 - SLO target
For 99.9% SLO:  error budget = 0.1% = 43.2 minutes of total downtime
For 99.95% SLO: error budget = 0.05% = 21.6 minutes of total downtime
For 99.99% SLO: error budget = 0.01% = 4.32 minutes of total downtime

Budget consumed = (actual_bad_minutes / allowed_bad_minutes) * 100
Budget remaining = 100% - budget_consumed
```
