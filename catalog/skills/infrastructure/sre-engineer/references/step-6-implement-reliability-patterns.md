### Step 6: Implement Reliability Patterns

Reliability patterns prevent cascading failures, manage load during degraded conditions, and validate system resilience through controlled experiments.

**Circuit Breaker Pattern (Envoy Sidecar)**:

```yaml
# envoy-circuit-breaker.yaml - Istio DestinationRule
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: payment-service
  namespace: production
spec:
  host: payment-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 5s
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 10
        maxRetries: 3
    outlierDetection:
      consecutive5xxErrors: 5       # Trip after 5 consecutive 5xx
      interval: 10s                 # Check every 10 seconds
      baseEjectionTime: 30s         # Eject for 30 seconds minimum
      maxEjectionPercent: 50        # Never eject more than 50% of hosts
      minHealthPercent: 30          # Disable ejection below 30% healthy
```

**Retry with Exponential Backoff (Application Level)**:

```python
import random
import time
import logging
from functools import wraps
from typing import TypeVar, Callable, Any

logger = logging.getLogger(__name__)
T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator implementing retry with exponential backoff and jitter."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            "All %d retries exhausted for %s: %s",
                            max_retries, func.__name__, e,
                        )
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    total_delay = delay + jitter
                    logger.warning(
                        "Attempt %d/%d for %s failed (%s), retrying in %.1fs",
                        attempt + 1, max_retries, func.__name__, e, total_delay,
                    )
                    time.sleep(total_delay)
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator


@retry_with_backoff(max_retries=3, base_delay=0.5, retryable_exceptions=(TimeoutError, ConnectionError))
def call_payment_gateway(order_id: str, amount_cents: int) -> dict[str, Any]:
    """Call external payment gateway with automatic retry."""
    # Implementation here
    ...
```

**Graceful Degradation Configuration**:

```yaml
# feature-flags.yaml - Degradation levels
degradation_levels:
  normal:
    recommendations: enabled
    search_autocomplete: enabled
    analytics_tracking: enabled
    image_quality: high

  level_1:  # Shed non-essential features
    recommendations: disabled
    search_autocomplete: enabled
    analytics_tracking: async_only
    image_quality: medium
    trigger: "error_budget_remaining < 50%"

  level_2:  # Protect core functionality
    recommendations: disabled
    search_autocomplete: disabled
    analytics_tracking: disabled
    image_quality: low
    trigger: "error_budget_remaining < 25% OR p99_latency > 2s"

  level_3:  # Emergency mode
    recommendations: disabled
    search_autocomplete: disabled
    analytics_tracking: disabled
    image_quality: disabled
    static_content_only: true
    trigger: "error_budget_exhausted OR SEV1_active"
```

**Chaos Engineering Experiment (LitmusChaos)**:

```yaml
# chaos-experiment.yaml - Pod kill experiment
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: checkout-pod-kill
  namespace: production
spec:
  appinfo:
    appns: production
    applabel: "app=checkout-api"
    appkind: deployment
  engineState: active
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "60"            # Kill pods for 60 seconds
            - name: CHAOS_INTERVAL
              value: "10"            # Kill a pod every 10 seconds
            - name: FORCE
              value: "false"         # Graceful termination
            - name: PODS_AFFECTED_PERC
              value: "30"            # Affect 30% of pods
        probe:
          - name: "slo-check"
            type: "promProbe"
            mode: "Continuous"
            runProperties:
              probeTimeout: 5
              interval: 10
              retry: 3
            promProbe/inputs:
              endpoint: "http://prometheus:9090"
              query: |
                sum(rate(http_requests_total{service="checkout-api", code!~"5.."}[1m]))
                / sum(rate(http_requests_total{service="checkout-api"}[1m]))
              comparator:
                type: "float"
                criteria: ">="
                value: "0.999"       # SLO must hold during chaos
---
# chaos-schedule.yaml - Run weekly in staging
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosSchedule
metadata:
  name: weekly-resilience-test
  namespace: staging
spec:
  schedule:
    repeat:
      timeRange:
        startTime: "2026-01-01T09:00:00Z"
      properties:
        minChaosInterval: "168h"     # Weekly
      workDays:
        includedDays: "Tue"
  engineTemplateSpec:
    appinfo:
      appns: staging
      applabel: "app=checkout-api"
      appkind: deployment
    experiments:
      - name: pod-delete
      - name: pod-network-latency
      - name: pod-cpu-hog
```

**Load Shedding with Priority Queues**:

```yaml
# envoy-rate-limit.yaml - Priority-based rate limiting
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: checkout-rate-limit
  namespace: production
spec:
  workloadSelector:
    labels:
      app: checkout-api
  configPatches:
    - applyTo: HTTP_FILTER
      match:
        context: SIDECAR_INBOUND
        listener:
          filterChain:
            filter:
              name: envoy.filters.network.http_connection_manager
      patch:
        operation: INSERT_BEFORE
        value:
          name: envoy.filters.http.local_ratelimit
          typed_config:
            "@type": type.googleapis.com/udpa.type.v1.TypedStruct
            type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
            value:
              stat_prefix: http_local_rate_limiter
              token_bucket:
                max_tokens: 1000
                tokens_per_fill: 1000
                fill_interval: 1s
              filter_enabled:
                runtime_key: local_rate_limit_enabled
                default_value:
                  numerator: 100
                  denominator: HUNDRED
```
