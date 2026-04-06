---
name: cicd-architect
description: CI/CD pipeline expertise for automated build, test, and deployment workflows. Use when setting up GitHub Actions, GitLab CI, Jenkins, or other CI/CD systems, implementing deployment strategies, or optimizing pipeline performance.
summary_l0: "Design CI/CD pipelines with GitHub Actions, GitLab CI, and deployment strategies"
overview_l1: "This skill provides specialized expertise in Continuous Integration and Continuous Deployment pipelines, covering workflow automation, deployment strategies, security scanning integration, and operational best practices for reliable software delivery. Use it when setting up GitHub Actions, GitLab CI, Jenkins, or other CI/CD systems, implementing deployment strategies (blue-green, canary, rolling), optimizing pipeline performance, integrating security scanning, or automating release processes. Key capabilities include pipeline design and optimization, multi-platform CI/CD configuration, deployment strategy implementation, security scan integration, artifact management, caching strategies, and pipeline monitoring. The expected output is production-ready CI/CD pipeline configurations with deployment strategies, security gates, and monitoring. Trigger phrases: CI/CD pipeline, GitHub Actions, GitLab CI, Jenkins, deployment strategy, build pipeline, automated deployment."
---

# CI/CD Architect

Specialized expertise in Continuous Integration and Continuous Deployment pipelines, providing guidance on workflow automation, deployment strategies, security scanning integration, and operational best practices for reliable software delivery.

## When to Use This Skill

Use this skill for:

- Setting up CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- Implementing deployment strategies (blue-green, canary, rolling)
- Configuring automated testing in pipelines
- Integrating security scanning (SAST, DAST, dependency scanning)
- Optimizing pipeline performance and costs
- Managing artifacts and releases
- Setting up environment promotions
- Troubleshooting pipeline failures

**Trigger phrases**: "CI/CD", "pipeline", "github actions", "gitlab ci", "jenkins", "deployment automation", "continuous integration", "continuous deployment", "build pipeline"

## What This Skill Does

Provides production-ready CI/CD patterns including:

- **Pipeline Design**: Multi-stage workflows, parallel execution, conditional jobs
- **Testing Integration**: Unit, integration, E2E test automation
- **Security**: SAST, DAST, secrets scanning, supply chain security
- **Deployment**: Multiple strategies with rollback capabilities
- **Artifacts**: Build caching, artifact management, container registries
- **Monitoring**: Pipeline observability, failure notifications

## Instructions

### Step 1: Design Pipeline Architecture

**Pipeline Stages (Recommended Order)**:

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Build  │───▶│  Test   │───▶│  Scan   │───▶│ Package │───▶│ Deploy  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  Compile       Unit Tests      SAST         Container       Staging
  Lint          Integration     DAST         Registry        Production
  Format        E2E             Deps         Artifacts       Rollback
```

### Step 2: Implement GitHub Actions Pipeline

**Complete CI/CD Workflow**:

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  release:
    types: [published]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============================================
  # BUILD & TEST
  # ============================================
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for versioning

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint code
        run: npm run lint

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          fail_ci_if_error: true

      - name: Build application
        run: npm run build

      - name: Determine version
        id: version
        run: |
          if [[ "${{ github.event_name }}" == "release" ]]; then
            echo "version=${{ github.event.release.tag_name }}" >> $GITHUB_OUTPUT
          else
            echo "version=sha-$(git rev-parse --short HEAD)" >> $GITHUB_OUTPUT
          fi

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7

  # ============================================
  # INTEGRATION TESTS
  # ============================================
  integration-tests:
    needs: build
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgres://postgres:testpass@localhost:5432/testdb

  # ============================================
  # SECURITY SCANNING
  # ============================================
  security-scan:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Run SAST scan (CodeQL)
        uses: github/codeql-action/init@v3
        with:
          languages: javascript

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3

      - name: Run dependency scan
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

      - name: Run secrets scan
        uses: trufflesecurity/trufflehog@main
        with:
          extra_args: --only-verified

  # ============================================
  # BUILD & PUSH CONTAINER
  # ============================================
  container:
    needs: [build, integration-tests, security-scan]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Download build artifacts
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha,prefix=sha-

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Run container scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

  # ============================================
  # DEPLOY TO STAGING
  # ============================================
  deploy-staging:
    needs: container
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

      - name: Deploy to staging
        run: |
          kubectl set image deployment/app \
            app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }} \
            -n staging

      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/app -n staging --timeout=300s

      - name: Run smoke tests
        run: |
          curl -f https://staging.example.com/health || exit 1

  # ============================================
  # DEPLOY TO PRODUCTION
  # ============================================
  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.event_name == 'release'
    environment:
      name: production
      url: https://example.com

    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PROD }}

      - name: Deploy canary (10%)
        run: |
          kubectl apply -f k8s/canary-deployment.yaml -n production
          kubectl set image deployment/app-canary \
            app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.event.release.tag_name }} \
            -n production

      - name: Monitor canary (5 min)
        run: |
          sleep 300
          ERROR_RATE=$(kubectl top pod -l app=app-canary -n production | awk 'NR>1 {print $3}')
          if (( $(echo "$ERROR_RATE > 1" | bc -l) )); then
            echo "Canary error rate too high, rolling back"
            kubectl delete -f k8s/canary-deployment.yaml -n production
            exit 1
          fi

      - name: Promote to full deployment
        run: |
          kubectl set image deployment/app \
            app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.event.release.tag_name }} \
            -n production
          kubectl rollout status deployment/app -n production --timeout=600s
          kubectl delete -f k8s/canary-deployment.yaml -n production

      - name: Create deployment record
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.repos.createDeployment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              ref: context.sha,
              environment: 'production',
              auto_merge: false,
              required_contexts: []
            });
```

### Step 3: Implement GitLab CI Pipeline

**Complete GitLab CI Configuration**:

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - security
  - package
  - deploy

variables:
  DOCKER_TLS_CERTDIR: "/certs"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# ============================================
# BUILD STAGE
# ============================================
build:
  stage: build
  image: node:20-alpine
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
      - .npm/
  script:
    - npm ci --cache .npm --prefer-offline
    - npm run lint
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 day

# ============================================
# TEST STAGE
# ============================================
unit-tests:
  stage: test
  image: node:20-alpine
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
  script:
    - npm ci
    - npm run test:unit -- --coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration-tests:
  stage: test
  image: node:20-alpine
  services:
    - postgres:15
  variables:
    POSTGRES_DB: testdb
    POSTGRES_PASSWORD: testpass
    DATABASE_URL: "postgres://postgres:testpass@postgres:5432/testdb"
  script:
    - npm ci
    - npm run test:integration

# ============================================
# SECURITY STAGE
# ============================================
sast:
  stage: security
  include:
    - template: Security/SAST.gitlab-ci.yml

dependency_scanning:
  stage: security
  include:
    - template: Security/Dependency-Scanning.gitlab-ci.yml

secret_detection:
  stage: security
  include:
    - template: Security/Secret-Detection.gitlab-ci.yml

# ============================================
# PACKAGE STAGE
# ============================================
build-container:
  stage: package
  image: docker:24
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_TAG

container_scanning:
  stage: package
  needs: [build-container]
  include:
    - template: Security/Container-Scanning.gitlab-ci.yml

# ============================================
# DEPLOY STAGE
# ============================================
deploy-staging:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - kubectl config set-cluster staging --server=$KUBE_SERVER_STAGING
    - kubectl set image deployment/app app=$IMAGE_TAG -n staging
    - kubectl rollout status deployment/app -n staging
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-production:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://example.com
  script:
    - kubectl config set-cluster prod --server=$KUBE_SERVER_PROD
    - kubectl set image deployment/app app=$IMAGE_TAG -n production
    - kubectl rollout status deployment/app -n production
  rules:
    - if: $CI_COMMIT_TAG
  when: manual
```

### Step 4: Implement Deployment Strategies

**Blue-Green Deployment**:

```yaml
# GitHub Actions blue-green deployment
deploy-blue-green:
  runs-on: ubuntu-latest
  steps:
    - name: Determine active color
      id: color
      run: |
        ACTIVE=$(kubectl get svc app -n production -o jsonpath='{.spec.selector.color}')
        if [ "$ACTIVE" == "blue" ]; then
          echo "deploy=green" >> $GITHUB_OUTPUT
          echo "active=blue" >> $GITHUB_OUTPUT
        else
          echo "deploy=green" >> $GITHUB_OUTPUT
          echo "active=blue" >> $GITHUB_OUTPUT
        fi

    - name: Deploy to inactive environment
      run: |
        kubectl set image deployment/app-${{ steps.color.outputs.deploy }} \
          app=${{ env.IMAGE }} -n production
        kubectl rollout status deployment/app-${{ steps.color.outputs.deploy }} -n production

    - name: Run smoke tests on new version
      run: |
        kubectl port-forward svc/app-${{ steps.color.outputs.deploy }} 8080:80 &
        sleep 5
        curl -f http://localhost:8080/health

    - name: Switch traffic
      run: |
        kubectl patch svc app -n production \
          -p '{"spec":{"selector":{"color":"${{ steps.color.outputs.deploy }}"}}}'

    - name: Verify switch
      run: |
        sleep 10
        curl -f https://example.com/health
```

**Canary Deployment**:

```yaml
# Kubernetes canary manifests
# k8s/canary-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-canary
spec:
  replicas: 1  # Small subset
  selector:
    matchLabels:
      app: myapp
      track: canary
  template:
    metadata:
      labels:
        app: myapp
        track: canary
    spec:
      containers:
      - name: app
        image: app:new-version
---
# Istio VirtualService for traffic splitting
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: app-vs
spec:
  hosts:
  - app
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: app-canary
  - route:
    - destination:
        host: app-stable
      weight: 90
    - destination:
        host: app-canary
      weight: 10
```

### Step 5: Pipeline Optimization

**Caching Strategies**:

```yaml
# GitHub Actions - Efficient caching
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.npm
      node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

# Docker layer caching
- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Parallel Execution**:

```yaml
# Run independent jobs in parallel
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - run: npm run lint

  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: npm test

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - run: npm audit

  # This job waits for all parallel jobs
  build:
    needs: [lint, unit-tests, security-scan]
    runs-on: ubuntu-latest
    steps:
      - run: npm run build
```

**Matrix Builds**:

```yaml
test:
  strategy:
    matrix:
      node-version: [18, 20, 22]
      os: [ubuntu-latest, windows-latest]
    fail-fast: false
  runs-on: ${{ matrix.os }}
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ matrix.node-version }}
    - run: npm test
```

## Best Practices

- **Fail fast** - Run quick checks (lint, format) before slow tests
- **Cache aggressively** - Dependencies, build outputs, Docker layers
- **Use artifacts** - Pass build outputs between jobs instead of rebuilding
- **Pin action versions** - Use SHA or major version tags
- **Separate concerns** - One job per logical task
- **Use environments** - Protect production with approvals
- **Implement rollbacks** - Always have a rollback mechanism
- **Monitor pipelines** - Track duration, failure rates, flakiness
- **Secure secrets** - Never log secrets, use secret managers
- **Test the pipeline** - Have pipeline tests in CI

## Common Patterns

### Pattern 1: Reusable Workflows

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      image-tag:
        required: true
        type: string
    secrets:
      KUBE_CONFIG:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Deploy
        run: |
          kubectl set image deployment/app app=${{ inputs.image-tag }}
```

### Pattern 2: Path-Based Triggers

```yaml
on:
  push:
    paths:
      - 'src/**'
      - 'package*.json'
      - 'Dockerfile'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Pattern 3: Conditional Deployments

```yaml
deploy:
  if: |
    github.event_name == 'push' &&
    github.ref == 'refs/heads/main' &&
    !contains(github.event.head_commit.message, '[skip deploy]')
```

## Quality Checklist

- [ ] Pipeline runs on both PRs and main branch
- [ ] Tests run before deployment
- [ ] Security scanning integrated (SAST, dependencies)
- [ ] Container images scanned for vulnerabilities
- [ ] Secrets stored securely (not in code)
- [ ] Caching configured for dependencies
- [ ] Deployment requires approval for production
- [ ] Rollback mechanism documented and tested
- [ ] Pipeline notifications configured
- [ ] Branch protection rules enabled

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Manual deployments are fine for our team size" | Manual deployments introduce human error at the exact moment of highest stress (production incidents); documented post-mortems at GitHub, GitLab, and Cloudflare cite manual deployment steps as contributing factors in outages that automated pipelines would have prevented. |
| "We'll add rollback capability later when we have an incident" | Rollback procedures that are not tested before an incident are unreliable during an incident; runbooks executed for the first time under pressure have a high failure rate due to untested assumptions and outdated steps. |
| "Secrets in CI environment variables are secure enough without a vault" | CI environment variables are visible to any job in the same repository (including PRs from forks), are logged in misconfigured pipelines, and are included in debugging artifacts; a secrets manager with scoped access prevents all three failure modes. |
| "We don't need branch protection because the team is disciplined" | Branch protection rules enforce the same guarantees automatically for all team members including temporary contractors, bots, and accounts with compromised credentials — discipline cannot substitute for policy enforcement. |
| "Caching makes the pipeline too complex to maintain" | Uncached pipelines that reinstall all dependencies on every run have 3-10x longer cycle times; longer cycle times correlate directly with reduced commit frequency and larger, harder-to-review changesets. |
| "Approval gates for production are just ceremony" | Automated deployment without a production approval gate has caused mass incidents (Knight Capital 2012, Facebook 2021) where a bad deploy propagated to all regions before any human could intervene. |

## Verification

- [ ] Pipeline executes on every push to the main branch and on every pull request without manual intervention
- [ ] Secrets are stored in a dedicated secrets manager (not in repository environment variables or source code)
- [ ] Rollback mechanism is documented and has been tested by executing it in a staging environment
- [ ] Branch protection rules are enabled: direct push to main is blocked and at least one status check is required
- [ ] Dependency caching is configured and verified: consecutive runs with no dependency changes complete faster than the first run
- [ ] Production deployment requires explicit approval from at least one team member before proceeding

## Related Skills

- `kubernetes-expert` - Kubernetes deployment targets
- `terraform-specialist` - Infrastructure provisioning in pipelines
- `security-review` - Pipeline security assessment
- `test-structure` - Test automation strategies

---

**Version**: 1.0.0
**Last Updated**: January 2026
**Based on**: awesome-claude-code-subagents patterns, CI/CD best practices


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
