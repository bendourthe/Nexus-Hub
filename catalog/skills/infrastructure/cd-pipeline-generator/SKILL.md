---
name: cd-pipeline-generator
description: Generates continuous deployment pipelines for GitHub Actions, GitLab CI, Jenkins, and ArgoCD with deployment strategies, environment promotion, and rollback triggers. Use when creating CD pipelines, configuring deployment gates, or implementing blue-green and canary deployments.
summary_l0: "Generate CD pipelines with deployment strategies, environment promotion, and rollback"
overview_l1: "This skill generates production-grade continuous deployment pipelines across major CI/CD platforms, producing complete, ready-to-use configurations with industry-standard deployment strategies. Use it when creating CD pipelines for GitHub Actions, GitLab CI, Jenkins, or ArgoCD, configuring deployment gates and environment promotion, implementing blue-green or canary deployments, setting up automated rollback triggers, managing secrets in deployment pipelines, or configuring health checks. Key capabilities include platform-specific pipeline generation, deployment strategy implementation (blue-green, canary, rolling), environment promotion workflows, secret management integration, health check configuration, automated rollback trigger setup, and deployment gate enforcement. The expected output is complete, platform-idiomatic CD pipeline configurations with deployment strategies, rollback procedures, and monitoring integration. Trigger phrases: CD pipeline, continuous deployment, blue-green deployment, canary deployment, deployment gate, environment promotion, rollback trigger, ArgoCD, deployment pipeline."
---

# CD Pipeline Generator

Specialized skill for generating production-grade continuous deployment pipelines across major CI/CD platforms. This skill produces complete, ready-to-use pipeline configurations that implement industry-standard deployment strategies, environment promotion workflows, secret management, health checks, and automated rollback triggers. Rather than providing generic templates, it tailors each pipeline to the target platform's idioms and best practices while maintaining consistent deployment safety guarantees.

## When to Use This Skill

Use this skill for:

- Generating a new continuous deployment pipeline from scratch for any major platform
- Converting an existing CI-only pipeline into a full CI/CD workflow with deployment stages
- Implementing blue-green, canary, or rolling deployment strategies in pipeline configuration
- Setting up environment promotion chains (dev, staging, production) with approval gates
- Configuring secret injection and credential management within deployment pipelines
- Adding health check verification and automated rollback triggers to existing pipelines
- Creating multi-environment deployment matrices for microservice architectures
- Integrating ArgoCD GitOps workflows with existing CI pipelines

**Trigger phrases**: "deployment pipeline", "CD pipeline", "continuous deployment", "deploy to production", "blue-green deployment", "canary deployment", "rolling update pipeline", "environment promotion", "deployment gates", "ArgoCD pipeline", "GitOps deployment", "deploy workflow"

## What This Skill Does

This skill follows a structured methodology to produce deployment pipelines:

1. **Platform Assessment**: Identifies the target CI/CD platform and its native deployment primitives (GitHub Environments, GitLab environments, Jenkins stages, ArgoCD Application resources).

2. **Strategy Selection**: Matches the deployment strategy (blue-green, canary, rolling) to the infrastructure target (Kubernetes, cloud VMs, serverless, static hosting) and produces the appropriate configuration.

3. **Environment Chain Design**: Builds a promotion workflow where artifacts flow through dev, staging, and production with configurable gates (manual approval, automated tests, metric thresholds) at each transition.

4. **Secret Integration**: Wires platform-native secret stores (GitHub Secrets, GitLab CI variables, Jenkins credentials, Kubernetes Secrets, Vault) into the pipeline without exposing values in logs or artifacts.

5. **Health Verification**: Adds post-deployment health checks (HTTP probes, smoke tests, metric queries) that feed into automated rollback decisions.

6. **Rollback Configuration**: Implements automatic rollback triggers based on health check failures, error rate thresholds, or manual intervention, ensuring every deployment can be reversed safely.

7. **Output Generation**: Produces complete pipeline files with inline comments explaining each decision, plus a companion README section documenting how to operate the pipeline.

## Lifecycle Conformance (mandatory)

This skill generates deployment stages. It does NOT define the CI/CD lifecycle, the trigger topology, the runner policy, the required-check design, or the report schema. Those are owned once, by `[[cicd-architect]]`, and this skill invokes and conforms to that canonical policy rather than restating it.

Invoke `[[cicd-architect]]` first whenever the surrounding pipeline does not yet exist or has not been reconciled against the canonical contract. Then generate deployment under these five constraints, none of which is negotiable:

1. **Deploy only from a protected event or an approved dispatch.** Valid deployment triggers are a protected release-branch update, a release tag, or an explicit human-approved dispatch. An ordinary feature-branch push must never reach a deployment stage, and neither must an unmerged pull request.

2. **Consume the `release` profile's artifact; never rebuild.** The artifact that reaches production is the exact digest the release profile produced and the integration gate validated. A per-environment rebuild produces a binary nobody tested and silently defeats the whole gate.

3. **Never generate validation-on-every-push defaults.** Deployment pipelines inherit the event separation in `[[cicd-architect]]` Step 4. If the generated file needs a validation step at all, it calls a profile.

4. **Reference every third-party action or plugin immutably.** Use a full commit SHA with a readable version comment, plus an explicit note on how and when to update it. A floating tag is an unreviewed code change running with deployment credentials, which is the highest-privilege context in the repository.

5. **Concurrency protects deployments rather than cancelling them.** Superseded pull-request validation cancels; an in-flight deployment does not. Use a distinct concurrency group per environment with cancellation disabled, so two deployments to one environment serialize instead of racing.

Approval, health check, rollback, promotion, and secret-injection mechanics remain this skill's own responsibility and are unchanged by the above.

## Instructions

### Step 1: Gather Deployment Requirements

Before generating any pipeline configuration, collect the following information:

```
Canonical lifecycle:    [reconciled via cicd-architect | NOT YET -- run it first]
Release artifact:       [digest produced by the `release` profile]
Target Platform:        [GitHub Actions | GitLab CI | Jenkins | ArgoCD]
Infrastructure Target:  [Kubernetes | AWS ECS | Azure App Service | GCP Cloud Run | VMs | Static]
Deployment Strategy:    [Blue-Green | Canary | Rolling | Recreate]
Environments:           [dev | staging | production] (list all)
Approval Gates:         [manual | automated | metric-based] per environment
Container Registry:     [GHCR | ECR | GCR | ACR | DockerHub | self-hosted]
Secret Store:           [platform-native | HashiCorp Vault | AWS Secrets Manager | Azure Key Vault]
Health Check Type:      [HTTP probe | smoke test | metric query | all]
Rollback Trigger:       [health check failure | error rate | latency | manual]
```

### Step 2: Generate the Pipeline Skeleton

Full walkthrough: [step-2-generate-the-pipeline-skeleton.md](references/step-2-generate-the-pipeline-skeleton.md) (load this step when you reach it).

### Step 3: Implement Deployment Strategies

Full walkthrough: [step-3-implement-deployment-strategies.md](references/step-3-implement-deployment-strategies.md) (load this step when you reach it).

### Step 4: Configure Environment Promotion

Full walkthrough: [step-4-configure-environment-promotion.md](references/step-4-configure-environment-promotion.md) (load this step when you reach it).

### Step 5: Configure Secret Management

Full walkthrough: [step-5-configure-secret-management.md](references/step-5-configure-secret-management.md) (load this step when you reach it).

### Step 6: Add Health Checks and Rollback Triggers

Full walkthrough: [step-6-add-health-checks-and-rollback-triggers.md](references/step-6-add-health-checks-and-rollback-triggers.md) (load this step when you reach it).

### Step 7: Add Deployment Gates

Full walkthrough: [step-7-add-deployment-gates.md](references/step-7-add-deployment-gates.md) (load this step when you reach it).

## Best Practices

- **Immutable artifacts**: Build the container image once in CI and promote the same digest through every environment. Never rebuild for production.

- **Environment parity**: Keep dev, staging, and production as similar as possible. Differences in configuration should be limited to environment-specific values (URLs, replica counts, resource limits), not structural changes.

- **Concurrency control**: Use concurrency groups to prevent multiple deployments to the same environment from running simultaneously. This avoids race conditions and partial deployments.

- **Deployment metadata**: Tag every deployment with the git SHA, build number, and timestamp. Store this metadata in Kubernetes labels, cloud resource tags, or a deployment tracking system so you can always trace a running version back to its source.

- **Gradual rollout for production**: Even when using rolling updates, consider deploying to a subset of production infrastructure first (a single region or availability zone) before expanding globally.

- **Secret rotation compatibility**: Design pipelines so secrets are fetched at deploy time, not baked into images. This allows secret rotation without redeployment.

- **Timeout configuration**: Set explicit timeouts on every deployment step. A deployment that hangs indefinitely is worse than one that fails fast and triggers a rollback.

- **Notification integration**: Send deployment status notifications to the team's communication channel. Include the environment, version, deployer, and a link to the pipeline run.

- **Audit trail**: Log every deployment event (who approved it, when it started, when it completed, whether it succeeded or failed) to an immutable audit log for compliance and incident investigation.

- **Dry-run support**: Include a dry-run mode in your pipeline that shows what would be deployed without making changes. This is valuable for pre-deployment review and debugging.

## Common Pitfalls

- **Rebuilding artifacts per environment**: If you build a new container image for each environment, you are not deploying the same artifact you tested. This defeats the purpose of environment promotion and introduces risk.

- **Missing rollback path**: Every deployment strategy must have a tested rollback mechanism. If you have never practiced a rollback, it will fail when you need it most. Include rollback steps in your deployment runbook and test them regularly.

- **Hardcoded secrets in pipeline files**: Never place secrets directly in workflow files, even in private repositories. Use the platform's native secret management and inject values at runtime.

- **No concurrency control**: Without concurrency groups, two developers merging to main in quick succession can trigger overlapping deployments. The result is unpredictable: half-deployed versions, failed health checks, and confused rollback state.

- **Ignoring deployment timeouts**: A missing timeout means a stuck deployment blocks the pipeline indefinitely. Always set `--timeout` on `kubectl rollout status` and equivalent commands on other platforms.

- **Skipping health checks for speed**: Removing post-deployment verification to "speed up the pipeline" is a false economy. A broken deployment that reaches production undetected costs far more time than a 60-second health check.

- **Environment-specific logic in application code**: If your application contains `if (env === 'production')` branches, you are not testing in staging what runs in production. Use configuration injection, not code branches.

- **Manual deployment steps**: Any step that requires a human to run a command, copy a file, or click a button outside the pipeline is a step that will eventually be forgotten or done incorrectly. Automate everything except deliberate approval gates.

- **Overly broad rollback triggers**: Rolling back on any single failed health check can cause unnecessary rollbacks during transient issues. Use consecutive failure thresholds (for example, 3 failures in a row) to avoid false positives.

- **Neglecting pipeline maintenance**: Pipelines are code. They need testing, version control, and periodic review. Treat your deployment pipeline with the same rigor as your application code.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll rebuild the image for production so it has the prod config baked in" | A rebuilt image is not the artifact that passed staging tests; environment-specific config belongs in injected configuration, and promoting the exact same digest is the only way the pipeline actually verifies what ships. |
| "We'll add the rollback job later, deploys rarely fail" | The first failed production deploy with no tested rollback path is an outage with no fast exit; the rollback job and a documented, practiced procedure must ship with the pipeline, not after the incident. |
| "Health checks slow the pipeline, I'll skip them to ship faster" | A broken deploy that reaches users undetected costs far more than a 60-second health gate; skipping verification trades a small known delay for an unbounded incident. |
| "Putting the secret directly in the workflow file is fine, the repo is private" | Secrets in pipeline files leak through logs, forks, and history even in private repos; platform-native secret stores injected at deploy time are the only safe path. |

## Verification

- [ ] The same image digest built in CI is promoted through every environment (no per-environment rebuild).
- [ ] The pipeline includes post-deployment health verification that gates promotion and triggers rollback on failure.
- [ ] A tested rollback path exists for the chosen strategy (blue-green traffic switch, canary abort, or `kubectl rollout undo`).
- [ ] No secrets are hardcoded in pipeline files; they are injected at runtime from a secret store.
- [ ] Concurrency control prevents overlapping deployments to the same environment, and every deploy step has an explicit timeout.

## Related Skills

- [[cicd-architect]] -- the canonical lifecycle, trigger topology, runner policy, required-check design, and report schema this skill conforms to; invoke it before generating deployment into an unreconciled pipeline
- [[rollback-strategy-advisor]] -- designs the rollback procedure the pipeline's rollback job executes
- [[kubernetes-expert]] -- the deployment target for blue-green, canary, and rolling strategies
- [[runbook-writer]] -- documents the operational procedure for running and recovering the pipeline
