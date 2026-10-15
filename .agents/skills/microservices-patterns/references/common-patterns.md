## Common Patterns

### Pattern 1: Transactional Outbox

Ensure events are published atomically with database writes (no dual-write problem):

```sql
-- Same transaction as the business write
BEGIN;

INSERT INTO orders (id, customer_id, status, total)
VALUES ('order-123', 'cust-456', 'placed', 4999);

INSERT INTO outbox_events (id, aggregate_type, aggregate_id, event_type, payload)
VALUES (
    'evt-789',
    'Order',
    'order-123',
    'order.placed',
    '{"orderId":"order-123","customerId":"cust-456","total":4999}'
);

COMMIT;

-- Separate poller process reads outbox and publishes to Kafka
-- After successful publish, marks the event as dispatched
```

### Pattern 2: Service Mesh with Istio

Offload resilience, security, and observability to the infrastructure:

```yaml
# istio/virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service
spec:
  hosts:
    - order-service
  http:
    - route:
        - destination:
            host: order-service
            subset: v2
          weight: 90
        - destination:
            host: order-service
            subset: v1
          weight: 10
      retries:
        attempts: 3
        perTryTimeout: 2s
        retryOn: 5xx,reset,connect-failure
      timeout: 10s
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: order-service
spec:
  host: order-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 10s
      baseEjectionTime: 30s
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
```

### Pattern 3: Health Check Aggregation

Each service exposes health, and the gateway aggregates:

```python
# health/check.py
import asyncio
import httpx

async def check_health() -> dict:
    """Deep health check that verifies all dependencies."""
    checks = {}

    # Database check
    try:
        await db.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Kafka check
    try:
        await kafka_producer.send("health-check", b"ping")
        checks["kafka"] = {"status": "healthy"}
    except Exception as e:
        checks["kafka"] = {"status": "unhealthy", "error": str(e)}

    # Downstream service check
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(
                "http://payment-service:8080/health"
            )
            resp.raise_for_status()
            checks["payment-service"] = {"status": "healthy"}
    except Exception as e:
        checks["payment-service"] = {
            "status": "degraded", "error": str(e)
        }

    overall = "healthy"
    if any(c["status"] == "unhealthy" for c in checks.values()):
        overall = "unhealthy"
    elif any(c["status"] == "degraded" for c in checks.values()):
        overall = "degraded"

    return {
        "status": overall,
        "service": "order-service",
        "version": "1.4.2",
        "checks": checks,
    }
```
