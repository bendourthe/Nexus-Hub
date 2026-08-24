### Step 2: Generate the Pipeline Skeleton

Start with the platform-appropriate file structure:

**GitHub Actions** (`.github/workflows/deploy.yml`):

```yaml
name: Continuous Deployment

on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        type: choice
        options:
          - dev
          - staging
          - production
      skip_approval:
        description: "Skip manual approval (dev only)"
        required: false
        type: boolean
        default: false

permissions:
  contents: read
  packages: read
  deployments: write
  id-token: write

concurrency:
  group: deploy-${{ inputs.environment || 'dev' }}
  cancel-in-progress: false

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

**GitLab CI** (`.gitlab-ci.yml` deployment stages):

```yaml
stages:
  - build
  - test
  - publish
  - deploy-dev
  - verify-dev
  - deploy-staging
  - verify-staging
  - approve-production
  - deploy-production
  - verify-production
  - rollback

variables:
  REGISTRY: $CI_REGISTRY
  IMAGE_TAG: $CI_COMMIT_SHORT_SHA
  KUBE_NAMESPACE_DEV: app-dev
  KUBE_NAMESPACE_STAGING: app-staging
  KUBE_NAMESPACE_PROD: app-prod
```

**Jenkins** (`Jenkinsfile`):

```groovy
pipeline {
    agent any

    parameters {
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'production'], description: 'Target deployment environment')
        booleanParam(name: 'SKIP_APPROVAL', defaultValue: false, description: 'Skip manual approval for dev')
        string(name: 'IMAGE_TAG', defaultValue: '', description: 'Override image tag (defaults to build number)')
    }

    environment {
        REGISTRY = 'ghcr.io'
        IMAGE_NAME = 'org/app'
        IMAGE_TAG = "${params.IMAGE_TAG ?: env.BUILD_NUMBER}"
        KUBECONFIG = credentials('kubeconfig')
    }

    options {
        disableConcurrentBuilds()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Validate') {
            steps {
                script {
                    echo "Deploying ${IMAGE_NAME}:${IMAGE_TAG} to ${params.ENVIRONMENT}"
                }
            }
        }
    }
}
```

**ArgoCD** (`argocd/application.yaml`):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-production
  namespace: argocd
  annotations:
    notifications.argoproj.io/subscribe.on-sync-succeeded.slack: deployments
    notifications.argoproj.io/subscribe.on-sync-failed.slack: deployments
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/org/app-manifests.git
    targetRevision: main
    path: overlays/production
    kustomize:
      images:
        - ghcr.io/org/app
  destination:
    server: https://kubernetes.default.svc
    namespace: app-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 3
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 1m
  revisionHistoryLimit: 10
```
