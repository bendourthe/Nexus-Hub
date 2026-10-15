### Step 5: Plan Capacity and Scaling

Capacity planning combines load testing, resource modeling, and autoscaling configuration to ensure services handle current traffic with headroom for growth while avoiding wasteful over-provisioning.

**Load Testing Methodology with k6**:

```javascript
// load-test.js - Staged load test with SLO validation
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const latencyP99 = new Trend('latency_p99');

export const options = {
  stages: [
    { duration: '5m',  target: 100 },   // Ramp up to baseline
    { duration: '10m', target: 100 },   // Sustain baseline
    { duration: '5m',  target: 300 },   // Ramp to 3x baseline
    { duration: '10m', target: 300 },   // Sustain 3x
    { duration: '5m',  target: 500 },   // Ramp to 5x (stress)
    { duration: '10m', target: 500 },   // Sustain stress
    { duration: '5m',  target: 0 },     // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(99)<500'],    // 99th percentile < 500ms
    'errors':            ['rate<0.001'],    // Error rate < 0.1%
    'http_req_failed':   ['rate<0.001'],
  },
};

export default function () {
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Load-Test': 'true',
    },
    timeout: '10s',
  };

  // Simulate realistic user journey
  const responses = http.batch([
    ['GET',  'https://api.example.com/products',        null, params],
    ['GET',  'https://api.example.com/cart',             null, params],
    ['POST', 'https://api.example.com/cart/items',
      JSON.stringify({ product_id: 'prod-123', qty: 1 }), params],
  ]);

  responses.forEach((res) => {
    check(res, {
      'status is 2xx': (r) => r.status >= 200 && r.status < 300,
      'latency < 500ms': (r) => r.timings.duration < 500,
    });
    errorRate.add(res.status >= 500);
    latencyP99.add(res.timings.duration);
  });

  sleep(1);
}
```

**Kubernetes Autoscaling Configuration**:

```yaml
# hpa.yaml - Horizontal Pod Autoscaler with custom metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: checkout-api
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: checkout-api
  minReplicas: 3
  maxReplicas: 50
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50           # Scale up by at most 50% at a time
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10           # Scale down slowly to avoid flapping
          periodSeconds: 120
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "100"
---
# vpa.yaml - Vertical Pod Autoscaler for right-sizing
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: checkout-api-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: checkout-api
  updatePolicy:
    updateMode: "Off"       # Recommendation-only mode initially
  resourcePolicy:
    containerPolicies:
      - containerName: checkout-api
        minAllowed:
          cpu: 100m
          memory: 128Mi
        maxAllowed:
          cpu: 4
          memory: 8Gi
```

**Resource Quotas and Limits**:

```yaml
# resource-quota.yaml - Namespace resource governance
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    pods: "500"
    services: "50"
    persistentvolumeclaims: "100"
---
# limit-range.yaml - Default container resource bounds
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: production
spec:
  limits:
    - default:
        cpu: 500m
        memory: 512Mi
      defaultRequest:
        cpu: 100m
        memory: 128Mi
      type: Container
```

**Capacity Model Spreadsheet Format**:

```
Service: checkout-api
Current baseline: 1,000 RPS
Current instances: 5 (c5.xlarge equivalent)
Per-instance capacity: ~250 RPS at p99 < 500ms

Growth forecast:
  3 months:  1,500 RPS (+50%)  -> 6 instances + 2 headroom = 8
  6 months:  2,200 RPS (+120%) -> 9 instances + 3 headroom = 12
  12 months: 3,500 RPS (+250%) -> 14 instances + 4 headroom = 18

Cost projection (on-demand):
  Current:   5 x $0.17/hr  = $612/month
  3 months:  8 x $0.17/hr  = $979/month
  6 months:  12 x $0.17/hr = $1,468/month
  12 months: 18 x $0.17/hr = $2,203/month

Savings with reserved (1yr, no upfront):
  12 months: 18 x $0.11/hr = $1,426/month (35% savings)
```
