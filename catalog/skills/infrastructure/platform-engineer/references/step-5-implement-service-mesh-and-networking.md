### Step 5: Implement Service Mesh and Networking

A service mesh provides a uniform layer for service-to-service communication, handling traffic management, security (mutual TLS), and observability without requiring application code changes. The platform team configures and operates the mesh so development teams get these capabilities for free.

**Istio Service Mesh Configuration**:

```yaml
# istio/peer-authentication.yaml
# Enforce mutual TLS across the mesh
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
---
# istio/virtual-service.yaml
# Traffic management with canary routing
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: payment-service
  namespace: payments
spec:
  hosts:
    - payment-service
  http:
    - match:
        - headers:
            x-canary:
              exact: "true"
      route:
        - destination:
            host: payment-service
            subset: canary
          weight: 100
    - route:
        - destination:
            host: payment-service
            subset: stable
          weight: 95
        - destination:
            host: payment-service
            subset: canary
          weight: 5
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: payment-service
  namespace: payments
spec:
  host: payment-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: DEFAULT
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutive5xxErrors: 3
      interval: 30s
      baseEjectionTime: 60s
      maxEjectionPercent: 50
  subsets:
    - name: stable
      labels:
        version: stable
    - name: canary
      labels:
        version: canary
```

**API Gateway Pattern with Ingress**:

```yaml
# gateway/ingress-gateway.yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: platform-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: SIMPLE
        credentialName: platform-tls-cert
      hosts:
        - "api.example.com"
        - "*.internal.example.com"
---
# Rate limiting configuration
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit
  namespace: istio-system
spec:
  workloadSelector:
    labels:
      istio: ingressgateway
  configPatches:
    - applyTo: HTTP_FILTER
      match:
        context: GATEWAY
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
                tokens_per_fill: 100
                fill_interval: 1s
```

**Service Discovery Pattern**:

```
                    ┌──────────────────────────────────┐
                    │        Platform Gateway           │
                    │   (TLS termination, rate limit)   │
                    └───────────────┬──────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
     ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
     │  order-service   │  │ payment-service │  │  user-service   │
     │  (Envoy sidecar) │  │ (Envoy sidecar) │  │ (Envoy sidecar) │
     └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
              │                     │                     │
              │    mTLS encrypted   │    mTLS encrypted   │
              │    service-to-service communication       │
              │                     │                     │
     ┌────────▼─────────────────────▼─────────────────────▼────────┐
     │                    Kubernetes DNS                            │
     │  order-service.orders.svc.cluster.local                     │
     │  payment-service.payments.svc.cluster.local                 │
     └─────────────────────────────────────────────────────────────┘
```
