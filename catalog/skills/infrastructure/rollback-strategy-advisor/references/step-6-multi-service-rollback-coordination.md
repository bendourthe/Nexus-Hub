### Step 6: Multi-Service Rollback Coordination

When multiple services are deployed together, rollback must respect dependency order to avoid breaking API contracts.

**Dependency-Aware Rollback Script** (`scripts/rollback-coordinated.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${1:?Usage: rollback-coordinated.sh <namespace> <manifest_file>}"
MANIFEST="${2:?Missing rollback manifest file}"

echo "=== Coordinated Multi-Service Rollback ==="
echo "Manifest: $MANIFEST"
echo ""

# Manifest format (YAML):
# rollback_order:
#   - name: frontend
#     deployment: frontend
#     revision: 42
#   - name: api-gateway
#     deployment: api-gateway
#     revision: 38
#   - name: user-service
#     deployment: user-service
#     revision: 55

# Parse rollback order (reverse of deployment order)
SERVICES=$(yq eval '.rollback_order[].name' "$MANIFEST")
TOTAL=$(echo "$SERVICES" | wc -l)
CURRENT=0

for SERVICE in $SERVICES; do
  CURRENT=$((CURRENT + 1))
  DEPLOYMENT=$(yq eval ".rollback_order[] | select(.name == \"$SERVICE\") | .deployment" "$MANIFEST")
  REVISION=$(yq eval ".rollback_order[] | select(.name == \"$SERVICE\") | .revision" "$MANIFEST")

  echo "[$CURRENT/$TOTAL] Rolling back $SERVICE (deployment: $DEPLOYMENT, revision: $REVISION)"

  kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE" --to-revision="$REVISION"
  kubectl rollout status "deployment/$DEPLOYMENT" -n "$NAMESPACE" --timeout=300s

  # Verify this service is healthy before proceeding to the next
  READY=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
    -o jsonpath='{.status.readyReplicas}')
  DESIRED=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
    -o jsonpath='{.spec.replicas}')

  if [ "$READY" != "$DESIRED" ]; then
    echo "CRITICAL: $SERVICE rollback unhealthy ($READY/$DESIRED ready)"
    echo "Halting coordinated rollback at step $CURRENT/$TOTAL"
    echo "Manual intervention required for remaining services"
    exit 1
  fi

  echo "$SERVICE rolled back successfully ($READY/$DESIRED ready)"
  echo ""
done

echo "=== Coordinated Rollback Complete ==="
echo "All $TOTAL services rolled back successfully"
```

**Rollback Manifest Example** (`rollback-manifest.yaml`):

```yaml
rollback_order:
  # Roll back in reverse dependency order:
  # frontend depends on api-gateway depends on user-service
  # So roll back frontend first, then api-gateway, then user-service
  - name: frontend
    deployment: frontend
    revision: 42
    health_endpoint: /health
  - name: api-gateway
    deployment: api-gateway
    revision: 38
    health_endpoint: /health
  - name: user-service
    deployment: user-service
    revision: 55
    health_endpoint: /health
```
