### Step 6: Design Service Mesh Networking

**Service Mesh Architecture**:

```
                    ┌──────────────────────────────────────────────┐
                    │              Control Plane                    │
                    │   ┌─────────┐  ┌──────────┐  ┌──────────┐  │
                    │   │  Istiod │  │  Cert    │  │  Config  │  │
                    │   │ (Pilot) │  │  Manager │  │  Store   │  │
                    │   └────┬────┘  └─────┬────┘  └────┬─────┘  │
                    └────────┼─────────────┼────────────┼─────────┘
                             │  xDS API    │  mTLS      │
                    ┌────────┼─────────────┼────────────┼─────────┐
                    │        │  Data Plane  │            │         │
                    │  ┌─────▼───────────────────────────▼──────┐  │
                    │  │  Pod A                                 │  │
                    │  │  ┌─────────┐    ┌──────────────────┐   │  │
                    │  │  │  App    │◄──►│  Envoy Sidecar   │   │  │
                    │  │  │Container│    │  (L7 Proxy)      │   │  │
                    │  │  └─────────┘    └────────┬─────────┘   │  │
                    │  └──────────────────────────┼─────────────┘  │
                    │                             │ mTLS           │
                    │  ┌──────────────────────────▼─────────────┐  │
                    │  │  Pod B                                 │  │
                    │  │  ┌─────────┐    ┌──────────────────┐   │  │
                    │  │  │  App    │◄──►│  Envoy Sidecar   │   │  │
                    │  │  │Container│    │  (L7 Proxy)      │   │  │
                    │  │  └─────────┘    └──────────────────┘   │  │
                    │  └────────────────────────────────────────┘  │
                    └──────────────────────────────────────────────┘
```

**Sidecar vs Ambient Mesh**:

| Aspect | Sidecar (Traditional) | Ambient Mesh (Istio 1.18+) |
|--------|----------------------|---------------------------|
| **Proxy** | One Envoy per pod | Shared ztunnel (L4) + optional waypoint (L7) |
| **Resource cost** | High (memory per sidecar) | Lower (shared infrastructure) |
| **mTLS** | Per-pod termination | ztunnel handles L4 mTLS |
| **L7 features** | Always available | Only when waypoint proxy deployed |
| **Adoption** | Requires pod restart for injection | No restart needed |

**Traffic Splitting for Canary Releases**:

```yaml
# Istio VirtualService: 90/10 traffic split
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api-service
spec:
  hosts:
    - api.internal.local
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: api-service
            subset: canary
    - route:
        - destination:
            host: api-service
            subset: stable
          weight: 90
        - destination:
            host: api-service
            subset: canary
          weight: 10
      retries:
        attempts: 3
        perTryTimeout: 2s
        retryOn: 5xx,reset,connect-failure
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api-service
spec:
  host: api-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: DEFAULT
        maxRequestsPerConnection: 1000
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: stable
      labels:
        version: v1
    - name: canary
      labels:
        version: v2
```

**Fault Injection for Resilience Testing**:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: payment-service
spec:
  hosts:
    - payment.internal.local
  http:
    - fault:
        delay:
          percentage:
            value: 10
          fixedDelay: 3s
        abort:
          percentage:
            value: 5
          httpStatus: 503
      route:
        - destination:
            host: payment-service
```

This injects a 3-second delay into 10% of requests and returns HTTP 503 for 5% of requests, allowing you to verify that upstream services handle degraded dependencies gracefully with timeouts, retries, and circuit breakers.

**Observability with Distributed Tracing**: Deploy Jaeger or Zipkin alongside the service mesh. Envoy automatically generates trace spans for each request hop. Ensure your application code propagates trace headers (`x-request-id`, `x-b3-traceid`, `x-b3-spanid`, `traceparent`) so that spans are stitched into complete traces across services.
