---
name: platform-engineer
description: Platform engineering expertise for building internal developer platforms and self-service infrastructure. Use when designing developer portals, creating golden paths, building platform APIs, standardizing deployment pipelines, or implementing infrastructure-as-code at scale.
summary_l0: "Build internal developer platforms with self-service infrastructure and golden paths"
overview_l1: "This skill provides specialized expertise in platform engineering, covering internal developer platforms, self-service infrastructure, standardized pipelines, developer experience metrics, service mesh networking, secrets management, and platform governance. Use it when designing developer portals, creating golden paths for common workflows, building platform APIs, standardizing deployment pipelines, implementing infrastructure-as-code at scale, or measuring developer productivity. Key capabilities include internal developer platform design, self-service infrastructure provisioning, golden path creation for common workflows, platform API development, standardized pipeline templates, developer experience metric tracking, service catalog management, and platform governance policies. The expected output is platform architecture with self-service interfaces, golden path templates, platform APIs, and governance documentation. Trigger phrases: platform engineering, internal developer platform, golden path, self-service infrastructure, developer portal, platform API, developer productivity, infrastructure at scale."
---

# Platform Engineer

Specialized expertise in platform engineering, covering internal developer platforms, self-service infrastructure, standardized pipelines, developer experience metrics, service mesh networking, secrets management, and platform governance. This skill provides production-ready patterns for teams building platforms that treat infrastructure as a product.

## When to Use This Skill

Use this skill for:

- Designing internal developer platforms (IDPs) and developer portals
- Creating golden paths and paved roads for development teams
- Building self-service infrastructure provisioning workflows
- Standardizing CI/CD pipelines across an organization
- Measuring and improving developer experience (DevEx)
- Implementing service mesh and internal networking patterns
- Managing secrets, configuration, and environment promotion
- Enforcing platform governance through policy-as-code

**Trigger phrases**: "platform engineering", "internal developer platform", "golden path", "self-service infrastructure", "developer portal", "Backstage", "platform team", "paved road", "developer experience", "DORA metrics", "service catalog", "policy-as-code"

## What This Skill Does

Provides production-ready platform engineering patterns including:

- **IDP Design**: Platform team topology, service catalogs, Backstage/Port configuration
- **Self-Service Infra**: Terraform modules as products, Crossplane compositions, portal-driven provisioning
- **Pipeline Standards**: Template CI/CD pipelines, shared actions/templates, progressive rollout strategies
- **DevEx Metrics**: DORA measurement, cognitive load assessment, adoption tracking
- **Service Mesh**: Traffic management, mutual TLS, service discovery, API gateway integration
- **Secrets Management**: Vault integration, external-secrets-operator, sealed secrets, config promotion
- **Governance**: OPA/Kyverno policies, cost tagging, resource quotas, compliance automation

## Instructions

### Step 1: Design the Internal Developer Platform

Full walkthrough: [step-1-design-the-internal-developer-platform.md](references/step-1-design-the-internal-developer-platform.md) (load this step when you reach it).

### Step 2: Build Self-Service Infrastructure

Full walkthrough: [step-2-build-self-service-infrastructure.md](references/step-2-build-self-service-infrastructure.md) (load this step when you reach it).

### Step 3: Standardize Deployment Pipelines

Full walkthrough: [step-3-standardize-deployment-pipelines.md](references/step-3-standardize-deployment-pipelines.md) (load this step when you reach it).

### Step 4: Measure Developer Experience

Full walkthrough: [step-4-measure-developer-experience.md](references/step-4-measure-developer-experience.md) (load this step when you reach it).

### Step 5: Implement Service Mesh and Networking

Full walkthrough: [step-5-implement-service-mesh-and-networking.md](references/step-5-implement-service-mesh-and-networking.md) (load this step when you reach it).

### Step 6: Manage Secrets and Configuration

Full walkthrough: [step-6-manage-secrets-and-configuration.md](references/step-6-manage-secrets-and-configuration.md) (load this step when you reach it).

### Step 7: Enforce Platform Governance and Guardrails

Full walkthrough: [step-7-enforce-platform-governance-and-guardrails.md](references/step-7-enforce-platform-governance-and-guardrails.md) (load this step when you reach it).

## Best Practices

- **Treat the platform as a product**: Conduct user research, maintain a roadmap, measure adoption, and iterate
- **Start small and iterate**: Launch with one golden path (for example, deploying a stateless service) and expand based on demand
- **Document everything**: Golden paths without documentation are invisible paths that nobody walks
- **Measure what matters**: Combine DORA metrics with qualitative developer surveys for a complete picture
- **Enforce guardrails, not gates**: Policies should block unsafe actions automatically rather than requiring manual approval queues
- **Version your platform APIs**: Terraform modules, pipeline templates, and Crossplane compositions all need semantic versioning
- **Build escape hatches**: Allow teams to deviate from golden paths with an explicit opt-out process so the platform does not become a blocker
- **Automate compliance**: Use policy-as-code to shift compliance left rather than relying on post-deployment audits
- **Own your SLOs**: The platform team must have SLOs for its own services (pipeline uptime, provisioning latency, catalog freshness)
- **Invest in onboarding**: A 30-minute "first deploy" experience for new engineers is the best advertisement for the platform

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll build the platform and teams will adopt it because it's mandated" | A platform with no measured adoption becomes shelfware that teams route around; treating the platform as a product (with DevEx metrics and an opt-in golden path that is genuinely faster) is what drives real usage. |
| "Self-service means giving teams raw Terraform and cloud credentials" | Raw access without paved-road guardrails recreates the inconsistency the platform was meant to remove and hands every team root-level blast radius; golden paths and policy-as-code constrain the self-service surface. |
| "One golden path can cover every team's workflow" | A single rigid path forces teams with legitimately different needs off the platform entirely; golden paths must cover the common case while leaving a documented escape hatch for the exceptions. |
| "Governance can be a wiki page of guidelines" | Guidelines that are not enforced as policy-as-code drift the moment they are inconvenient; the enforcement (OPA, admission control, pipeline gates) is what makes governance real rather than aspirational. |

## Verification

- [ ] The platform exposes a self-service interface (portal or API), not raw cloud credentials handed to teams.
- [ ] At least one golden path is documented with a defined escape hatch for teams whose needs differ.
- [ ] Adoption and DevEx are measured (DORA metrics or equivalent), not assumed from a mandate.
- [ ] Governance rules are enforced as policy-as-code in the provisioning or pipeline path, not only documented.
- [ ] Secrets are managed through a dedicated system (Vault, external-secrets-operator), not embedded in templates.

## Related Skills

- [[cloud-architect]] -- cloud infrastructure design and Well-Architected Framework
- [[terraform-specialist]] -- deep Terraform module development and state management
- [[kubernetes-expert]] -- container orchestration and cluster operations
- [[cicd-architect]] -- advanced CI/CD pipeline design and optimization
- [[security-review]] -- security assessment and threat modeling

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Team Topologies platform team patterns, CNCF platform engineering maturity model, DORA research


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
