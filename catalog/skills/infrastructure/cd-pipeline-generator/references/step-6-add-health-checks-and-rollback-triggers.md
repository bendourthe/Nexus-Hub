### Step 6: Add Health Checks and Rollback Triggers

**Post-Deployment Health Verification Script** (`scripts/verify-deployment.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

ENDPOINT="${1:?Usage: verify-deployment.sh <endpoint> <namespace> <deployment>}"
NAMESPACE="${2:?Missing namespace}"
DEPLOYMENT="${3:?Missing deployment}"
MAX_RETRIES="${4:-20}"
RETRY_INTERVAL="${5:-15}"

echo "Verifying deployment: $DEPLOYMENT in $NAMESPACE"
echo "Health endpoint: $ENDPOINT"

# Phase 1: Kubernetes rollout status
echo "--- Phase 1: Rollout Status ---"
if ! kubectl rollout status "deployment/$DEPLOYMENT" -n "$NAMESPACE" --timeout=300s; then
  echo "FAIL: Rollout did not complete"
  kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE"
  exit 1
fi

# Phase 2: HTTP health checks
echo "--- Phase 2: HTTP Health Checks ---"
CONSECUTIVE_SUCCESS=0
REQUIRED_SUCCESSES=3

for i in $(seq 1 "$MAX_RETRIES"); do
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$ENDPOINT/health" || echo "000")

  if [ "$HTTP_STATUS" = "200" ]; then
    CONSECUTIVE_SUCCESS=$((CONSECUTIVE_SUCCESS + 1))
    echo "Health check passed ($CONSECUTIVE_SUCCESS/$REQUIRED_SUCCESSES) [attempt $i]"
    if [ "$CONSECUTIVE_SUCCESS" -ge "$REQUIRED_SUCCESSES" ]; then
      echo "Health verification complete"
      break
    fi
  else
    CONSECUTIVE_SUCCESS=0
    echo "Health check returned $HTTP_STATUS [attempt $i/$MAX_RETRIES]"
  fi

  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "FAIL: Health checks did not pass after $MAX_RETRIES attempts"
    echo "Initiating automatic rollback"
    kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE"
    exit 1
  fi

  sleep "$RETRY_INTERVAL"
done

# Phase 3: Readiness probe verification
echo "--- Phase 3: Pod Readiness ---"
READY_PODS=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.status.readyReplicas}')
DESIRED_PODS=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.spec.replicas}')

if [ "$READY_PODS" != "$DESIRED_PODS" ]; then
  echo "FAIL: Only $READY_PODS/$DESIRED_PODS pods ready"
  kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE"
  exit 1
fi

echo "SUCCESS: All $READY_PODS/$DESIRED_PODS pods ready and healthy"
```

**GitHub Actions Rollback Job**:

```yaml
  rollback:
    if: failure() && needs.deploy-production.result == 'failure'
    needs: [deploy-production, verify-production]
    runs-on: ubuntu-latest
    steps:
      - name: Rollback deployment
        run: |
          kubectl rollout undo deployment/myapp -n production
          kubectl rollout status deployment/myapp -n production --timeout=300s

      - name: Notify rollback
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Production deployment rolled back",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Production Rollback* triggered for `${{ github.sha }}`\nPrevious version restored. <${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View run>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_DEPLOY_WEBHOOK }}
```
