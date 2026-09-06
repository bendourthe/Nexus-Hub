### Step 3: Standardize Deployment Pipelines

Shared pipeline templates reduce duplication, enforce organizational standards, and give every team a reliable deployment experience without reinventing CI/CD from scratch. The platform team owns and versions these templates.

**Shared GitHub Actions Reusable Workflow**:

```yaml
# .github/workflows/deploy-service.yml (in the shared workflows repo)
name: Deploy Service
on:
  workflow_call:
    inputs:
      service-name:
        required: true
        type: string
      environment:
        required: true
        type: string
        description: "Target environment (dev, staging, production)"
      image-tag:
        required: true
        type: string
      deployment-strategy:
        required: false
        type: string
        default: "rolling"
        description: "rolling, blue-green, or canary"
    secrets:
      KUBE_CONFIG:
        required: true
      SLACK_WEBHOOK:
        required: false

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Validate Kubernetes manifests
        run: |
          kubectl kustomize deploy/overlays/${{ inputs.environment }} | \
            kubeval --strict --kubernetes-version 1.29.0
      - name: Policy check with OPA
        uses: open-policy-agent/opa-github-action@v2
        with:
          input: deploy/overlays/${{ inputs.environment }}
          policy: policies/

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/setup-kubectl@v3

      - name: Rolling deployment
        if: inputs.deployment-strategy == 'rolling'
        run: |
          kubectl set image deployment/${{ inputs.service-name }} \
            app=${{ inputs.image-tag }} \
            --namespace=${{ inputs.service-name }}
          kubectl rollout status deployment/${{ inputs.service-name }} \
            --namespace=${{ inputs.service-name }} \
            --timeout=300s

      - name: Canary deployment
        if: inputs.deployment-strategy == 'canary'
        run: |
          # Deploy canary with 10% traffic
          kubectl apply -f - <<EOF
          apiVersion: flagger.app/v1beta1
          kind: Canary
          metadata:
            name: ${{ inputs.service-name }}
            namespace: ${{ inputs.service-name }}
          spec:
            targetRef:
              apiVersion: apps/v1
              kind: Deployment
              name: ${{ inputs.service-name }}
            progressDeadlineSeconds: 600
            analysis:
              interval: 60s
              threshold: 5
              maxWeight: 50
              stepWeight: 10
              metrics:
                - name: request-success-rate
                  thresholdRange:
                    min: 99
                  interval: 60s
                - name: request-duration
                  thresholdRange:
                    max: 500
                  interval: 60s
          EOF

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "Deploy ${{ inputs.service-name }} to ${{ inputs.environment }}: ${{ job.status }}"
            }
```

**Consuming the Shared Workflow (in a service repo)**:

```yaml
# .github/workflows/deploy.yml (in each service repo)
name: Deploy
on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      image-tag: ${{ steps.build.outputs.tag }}
    steps:
      - uses: actions/checkout@v4
      - name: Build and push
        id: build
        run: |
          TAG="${GITHUB_SHA::8}"
          docker build -t myregistry/${{ github.event.repository.name }}:${TAG} .
          docker push myregistry/${{ github.event.repository.name }}:${TAG}
          echo "tag=myregistry/${{ github.event.repository.name }}:${TAG}" >> "$GITHUB_OUTPUT"

  deploy-staging:
    needs: build
    uses: myorg/platform-workflows/.github/workflows/deploy-service.yml@v2
    with:
      service-name: ${{ github.event.repository.name }}
      environment: staging
      image-tag: ${{ needs.build.outputs.image-tag }}
      deployment-strategy: rolling
    secrets:
      KUBE_CONFIG: ${{ secrets.STAGING_KUBE_CONFIG }}
      SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}

  deploy-production:
    needs: deploy-staging
    uses: myorg/platform-workflows/.github/workflows/deploy-service.yml@v2
    with:
      service-name: ${{ github.event.repository.name }}
      environment: production
      image-tag: ${{ needs.build.outputs.image-tag }}
      deployment-strategy: canary
    secrets:
      KUBE_CONFIG: ${{ secrets.PROD_KUBE_CONFIG }}
      SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
```

**Deployment Strategy Comparison**:

| Strategy | Risk | Rollback Speed | Complexity | Best For |
|----------|------|---------------|------------|----------|
| **Rolling** | Medium | Minutes | Low | Stateless services, non-critical |
| **Blue-Green** | Low | Seconds | Medium | Stateful services, zero-downtime |
| **Canary** | Lowest | Seconds | High | High-traffic, user-facing services |
| **Recreate** | High | Minutes | Lowest | Dev/test, batch workloads |
