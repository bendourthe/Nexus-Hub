### Step 3: Implement Deployment Strategies

#### Blue-Green Deployment

Blue-green uses two identical environments. Traffic switches atomically from the current (blue) to the new (green) after verification.

**GitHub Actions (Kubernetes)**:

```yaml
  deploy-green:
    runs-on: ubuntu-latest
    environment:
      name: production-green
      url: https://green.example.com
    steps:
      - name: Configure kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: "v1.29.0"

      - name: Deploy green environment
        run: |
          # Deploy to the inactive color
          ACTIVE_COLOR=$(kubectl get svc myapp-active -n production \
            -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "blue")

          if [ "$ACTIVE_COLOR" = "blue" ]; then
            TARGET_COLOR="green"
          else
            TARGET_COLOR="blue"
          fi

          echo "Active: $ACTIVE_COLOR, Deploying to: $TARGET_COLOR"
          echo "TARGET_COLOR=$TARGET_COLOR" >> "$GITHUB_ENV"

          kubectl set image deployment/myapp-${TARGET_COLOR} \
            app=${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
            -n production

          kubectl rollout status deployment/myapp-${TARGET_COLOR} \
            -n production --timeout=300s

      - name: Run smoke tests against green
        run: |
          GREEN_URL="http://myapp-${TARGET_COLOR}.production.svc.cluster.local:8080"
          for i in $(seq 1 10); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$GREEN_URL/health")
            if [ "$STATUS" = "200" ]; then
              echo "Health check passed (attempt $i)"
              break
            fi
            if [ "$i" -eq 10 ]; then
              echo "Health check failed after 10 attempts"
              exit 1
            fi
            sleep 5
          done

      - name: Switch traffic to green
        run: |
          kubectl patch svc myapp-active -n production \
            -p "{\"spec\":{\"selector\":{\"color\":\"${TARGET_COLOR}\"}}}"
          echo "Traffic switched to $TARGET_COLOR"

      - name: Verify live traffic
        run: |
          sleep 10
          LIVE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://app.example.com/health")
          if [ "$LIVE_STATUS" != "200" ]; then
            echo "Live verification failed, initiating rollback"
            ROLLBACK_COLOR=$( [ "$TARGET_COLOR" = "green" ] && echo "blue" || echo "green" )
            kubectl patch svc myapp-active -n production \
              -p "{\"spec\":{\"selector\":{\"color\":\"${ROLLBACK_COLOR}\"}}}"
            exit 1
          fi
```

#### Canary Deployment

Canary gradually shifts traffic to the new version, monitoring metrics at each step before proceeding.

**GitHub Actions (with Flagger on Kubernetes)**:

```yaml
  deploy-canary:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    steps:
      - name: Update canary image
        run: |
          kubectl set image deployment/myapp \
            app=${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG} \
            -n production

      - name: Monitor canary progression
        run: |
          # Flagger manages the canary automatically; we poll for completion
          TIMEOUT=600
          INTERVAL=15
          ELAPSED=0

          while [ $ELAPSED -lt $TIMEOUT ]; do
            STATUS=$(kubectl get canary myapp -n production \
              -o jsonpath='{.status.phase}')

            case "$STATUS" in
              "Succeeded")
                echo "Canary promotion succeeded"
                exit 0
                ;;
              "Failed")
                echo "Canary promotion failed, automatic rollback triggered"
                exit 1
                ;;
              "Progressing")
                WEIGHT=$(kubectl get canary myapp -n production \
                  -o jsonpath='{.status.canaryWeight}')
                echo "Canary progressing: ${WEIGHT}% traffic"
                ;;
            esac

            sleep $INTERVAL
            ELAPSED=$((ELAPSED + INTERVAL))
          done

          echo "Canary timed out after ${TIMEOUT}s"
          exit 1
```

**Flagger Canary Resource**:

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: myapp
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  service:
    port: 8080
    targetPort: 8080
  analysis:
    interval: 30s
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
        interval: 30s
      - name: request-duration
        thresholdRange:
          max: 500
        interval: 30s
    webhooks:
      - name: smoke-test
        type: pre-rollout
        url: http://flagger-loadtester.test/
        timeout: 60s
        metadata:
          type: bash
          cmd: "curl -s http://myapp-canary.production:8080/health | grep ok"
```

#### Rolling Update

Rolling update replaces pods incrementally, maintaining availability throughout the process.

**Kubernetes Deployment Configuration**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
  namespace: production
spec:
  replicas: 6
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 2
      maxUnavailable: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
        version: "${IMAGE_TAG}"
    spec:
      terminationGracePeriodSeconds: 60
      containers:
        - name: app
          image: ghcr.io/org/app:latest
          ports:
            - containerPort: 8080
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
            failureThreshold: 5
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 15"]
```
