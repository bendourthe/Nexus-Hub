### Step 2: Implement Immediate Rollback

Immediate rollback applies to stateless code changes where the previous version can replace the current version without data concerns.

**Kubernetes Rollback Script** (`scripts/rollback-immediate.sh`):

```bash
#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${1:?Usage: rollback-immediate.sh <namespace> <deployment> [revision]}"
DEPLOYMENT="${2:?Missing deployment name}"
REVISION="${3:-}"
TIMEOUT="${4:-300s}"

echo "=== Immediate Rollback ==="
echo "Namespace:  $NAMESPACE"
echo "Deployment: $DEPLOYMENT"
echo "Revision:   ${REVISION:-previous}"
echo ""

# Step 1: Record current state for audit trail
CURRENT_IMAGE=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.spec.template.spec.containers[0].image}')
CURRENT_REVISION=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.metadata.annotations.deployment\.kubernetes\.io/revision}')

echo "Current image:    $CURRENT_IMAGE"
echo "Current revision: $CURRENT_REVISION"
echo ""

# Step 2: List available revisions
echo "Available rollback targets:"
kubectl rollout history "deployment/$DEPLOYMENT" -n "$NAMESPACE"
echo ""

# Step 3: Execute rollback
if [ -n "$REVISION" ]; then
  echo "Rolling back to revision $REVISION..."
  kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE" --to-revision="$REVISION"
else
  echo "Rolling back to previous revision..."
  kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE"
fi

# Step 4: Wait for rollout completion
echo "Waiting for rollout to complete (timeout: $TIMEOUT)..."
if ! kubectl rollout status "deployment/$DEPLOYMENT" -n "$NAMESPACE" --timeout="$TIMEOUT"; then
  echo "CRITICAL: Rollback itself failed to complete"
  echo "Manual intervention required"
  kubectl describe "deployment/$DEPLOYMENT" -n "$NAMESPACE"
  exit 2
fi

# Step 5: Verify rollback
NEW_IMAGE=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.spec.template.spec.containers[0].image}')
READY=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.status.readyReplicas}')
DESIRED=$(kubectl get deployment "$DEPLOYMENT" -n "$NAMESPACE" \
  -o jsonpath='{.spec.replicas}')

echo ""
echo "=== Rollback Complete ==="
echo "Previous image: $CURRENT_IMAGE"
echo "Restored image: $NEW_IMAGE"
echo "Ready pods:     $READY/$DESIRED"

if [ "$READY" != "$DESIRED" ]; then
  echo "WARNING: Not all pods are ready after rollback"
  exit 1
fi

echo "Rollback verified successfully"
```

**GitHub Actions Rollback Workflow** (`.github/workflows/rollback.yml`):

```yaml
name: Production Rollback

on:
  workflow_dispatch:
    inputs:
      environment:
        description: "Environment to roll back"
        required: true
        type: choice
        options:
          - production
          - staging
      revision:
        description: "Target revision (leave empty for previous)"
        required: false
        type: string
      reason:
        description: "Reason for rollback"
        required: true
        type: string

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Record rollback initiation
        run: |
          echo "## Rollback Record" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Environment**: ${{ inputs.environment }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Initiated by**: ${{ github.actor }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Reason**: ${{ inputs.reason }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- **Timestamp**: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$GITHUB_STEP_SUMMARY"

      - name: Configure kubectl
        uses: azure/setup-kubectl@v4

      - name: Execute rollback
        run: |
          bash scripts/rollback-immediate.sh \
            "app-${{ inputs.environment }}" \
            "myapp" \
            "${{ inputs.revision }}"

      - name: Run smoke tests
        run: |
          bash scripts/verify-deployment.sh \
            "https://${{ inputs.environment == 'production' && 'app' || inputs.environment }}.example.com" \
            "app-${{ inputs.environment }}" \
            "myapp"

      - name: Notify team
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Rollback ${{ job.status }}: ${{ inputs.environment }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Rollback ${{ job.status }}*\n*Environment*: ${{ inputs.environment }}\n*Reason*: ${{ inputs.reason }}\n*Initiated by*: ${{ github.actor }}\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View details>"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_INCIDENTS_WEBHOOK }}
```
