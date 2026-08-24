### Step 4: Configure Environment Promotion

Define the promotion chain with appropriate gates at each stage:

**GitHub Actions Environment Promotion**:

```yaml
jobs:
  deploy-dev:
    runs-on: ubuntu-latest
    environment:
      name: dev
      url: https://dev.example.com
    steps:
      - name: Deploy to dev
        uses: ./.github/actions/deploy
        with:
          environment: dev
          image_tag: ${{ needs.build.outputs.image_tag }}
          kubeconfig: ${{ secrets.KUBE_CONFIG_DEV }}

  verify-dev:
    needs: deploy-dev
    runs-on: ubuntu-latest
    steps:
      - name: Run integration tests
        run: |
          npm run test:integration -- --base-url=https://dev.example.com

      - name: Run E2E tests
        run: |
          npm run test:e2e -- --base-url=https://dev.example.com

  deploy-staging:
    needs: verify-dev
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - name: Deploy to staging
        uses: ./.github/actions/deploy
        with:
          environment: staging
          image_tag: ${{ needs.build.outputs.image_tag }}
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

  verify-staging:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - name: Run performance tests
        run: |
          k6 run tests/performance/load-test.js \
            --env BASE_URL=https://staging.example.com \
            --out json=results.json

      - name: Check performance thresholds
        run: |
          python scripts/check_perf_thresholds.py results.json \
            --p95-latency 200 \
            --error-rate 0.01

  deploy-production:
    needs: verify-staging
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.example.com
    steps:
      - name: Deploy to production
        uses: ./.github/actions/deploy
        with:
          environment: production
          image_tag: ${{ needs.build.outputs.image_tag }}
          kubeconfig: ${{ secrets.KUBE_CONFIG_PROD }}
          strategy: blue-green
```

**Reusable Deploy Composite Action** (`.github/actions/deploy/action.yml`):

```yaml
name: "Deploy"
description: "Deploy application to a Kubernetes environment"

inputs:
  environment:
    description: "Target environment"
    required: true
  image_tag:
    description: "Container image tag to deploy"
    required: true
  kubeconfig:
    description: "Base64-encoded kubeconfig"
    required: true
  strategy:
    description: "Deployment strategy"
    required: false
    default: "rolling"

runs:
  using: "composite"
  steps:
    - name: Set up kubectl
      uses: azure/setup-kubectl@v4
      with:
        version: "v1.29.0"

    - name: Configure cluster access
      shell: bash
      run: |
        echo "${{ inputs.kubeconfig }}" | base64 -d > /tmp/kubeconfig
        echo "KUBECONFIG=/tmp/kubeconfig" >> "$GITHUB_ENV"

    - name: Apply manifests
      shell: bash
      run: |
        kustomize build "k8s/overlays/${{ inputs.environment }}" | \
          envsubst | kubectl apply -f -
      env:
        IMAGE_TAG: ${{ inputs.image_tag }}

    - name: Wait for rollout
      shell: bash
      run: |
        kubectl rollout status deployment/myapp \
          -n "app-${{ inputs.environment }}" \
          --timeout=300s

    - name: Verify deployment health
      shell: bash
      run: |
        RETRIES=12
        for i in $(seq 1 $RETRIES); do
          STATUS=$(kubectl get deployment myapp \
            -n "app-${{ inputs.environment }}" \
            -o jsonpath='{.status.conditions[?(@.type=="Available")].status}')
          if [ "$STATUS" = "True" ]; then
            echo "Deployment healthy"
            exit 0
          fi
          echo "Waiting for deployment health (attempt $i/$RETRIES)"
          sleep 10
        done
        echo "Deployment health check timed out"
        exit 1
```
