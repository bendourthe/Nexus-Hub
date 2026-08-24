### Step 5: Implement Blue-Green Switchback

Blue-green switchback is the fastest rollback mechanism because the previous version is still running and receiving no traffic. The rollback simply switches the load balancer back.

**Blue-Green Switchback Script** (`scripts/rollback-blue-green.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${1:?Usage: rollback-blue-green.sh <namespace> <service_name>}"
SERVICE="${2:?Missing service name}"

echo "=== Blue-Green Switchback ==="

# Determine current active color
ACTIVE_COLOR=$(kubectl get svc "$SERVICE" -n "$NAMESPACE" \
  -o jsonpath='{.spec.selector.color}')

if [ "$ACTIVE_COLOR" = "blue" ]; then
  TARGET_COLOR="green"
elif [ "$ACTIVE_COLOR" = "green" ]; then
  TARGET_COLOR="blue"
else
  echo "ERROR: Cannot determine active color (found: '$ACTIVE_COLOR')"
  echo "Expected 'blue' or 'green' in service selector"
  exit 1
fi

echo "Current active: $ACTIVE_COLOR"
echo "Switching to:   $TARGET_COLOR"

# Verify target deployment is healthy before switching
TARGET_READY=$(kubectl get deployment "${SERVICE}-${TARGET_COLOR}" -n "$NAMESPACE" \
  -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
TARGET_DESIRED=$(kubectl get deployment "${SERVICE}-${TARGET_COLOR}" -n "$NAMESPACE" \
  -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")

if [ "$TARGET_READY" != "$TARGET_DESIRED" ] || [ "$TARGET_READY" = "0" ]; then
  echo "WARNING: Target deployment ${SERVICE}-${TARGET_COLOR} has $TARGET_READY/$TARGET_DESIRED ready pods"
  echo "Scaling up target deployment..."
  kubectl scale deployment "${SERVICE}-${TARGET_COLOR}" -n "$NAMESPACE" \
    --replicas="$TARGET_DESIRED"
  kubectl rollout status deployment "${SERVICE}-${TARGET_COLOR}" -n "$NAMESPACE" \
    --timeout=300s
fi

# Switch traffic
echo "Switching traffic..."
kubectl patch svc "$SERVICE" -n "$NAMESPACE" \
  -p "{\"spec\":{\"selector\":{\"color\":\"${TARGET_COLOR}\"}}}"

# Verify switchback
sleep 5
NEW_ACTIVE=$(kubectl get svc "$SERVICE" -n "$NAMESPACE" \
  -o jsonpath='{.spec.selector.color}')

if [ "$NEW_ACTIVE" = "$TARGET_COLOR" ]; then
  echo ""
  echo "=== Switchback Complete ==="
  echo "Traffic now routed to: $TARGET_COLOR"
  echo "Previous version ($ACTIVE_COLOR) is still running but receiving no traffic"
  echo ""
  echo "Next steps:"
  echo "  1. Verify application behavior"
  echo "  2. Monitor error rates for 15 minutes"
  echo "  3. Once stable, optionally scale down $ACTIVE_COLOR deployment"
else
  echo "ERROR: Traffic switch verification failed"
  echo "Expected active: $TARGET_COLOR, Got: $NEW_ACTIVE"
  exit 1
fi
```
