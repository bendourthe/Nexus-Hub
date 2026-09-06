### Step 1: Design the Internal Developer Platform

An internal developer platform (IDP) is a self-service layer that abstracts away infrastructure complexity and provides development teams with golden paths for common workflows. The platform team operates as a product team, treating developers as customers and iterating on the platform based on feedback and usage data.

**Platform Team Topology**:

| Role | Responsibility |
|------|---------------|
| **Platform Product Manager** | Roadmap, developer interviews, prioritization |
| **Platform Engineer** | Core platform services, APIs, automation |
| **Developer Advocate** | Documentation, onboarding, feedback loops |
| **SRE/Reliability** | Platform SLOs, incident response, capacity |
| **Security Champion** | Policy authoring, compliance, threat modeling |

**Golden Path Principles**:

- A golden path is an opinionated, supported, and well-documented way to accomplish a common task (deploying a service, provisioning a database, setting up monitoring)
- Golden paths are recommendations, not mandates. Teams can deviate when they have a valid reason, but the golden path should cover 80% of use cases
- Every golden path includes: a template or scaffold, automated validation, documentation, and an owner who maintains it
- Measure golden path adoption to understand where the platform delivers value and where gaps exist

**Backstage Service Catalog Configuration**:

```yaml
# catalog-info.yaml - Backstage entity descriptor
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: payment-service
  description: Handles payment processing and billing
  annotations:
    backstage.io/techdocs-ref: dir:.
    github.com/project-slug: myorg/payment-service
    pagerduty.com/service-id: P1234ABC
    grafana/dashboard-selector: "payment-service"
    sonarqube.org/project-key: myorg_payment-service
  tags:
    - python
    - grpc
    - tier-1
  links:
    - url: https://grafana.internal/d/payment-svc
      title: Grafana Dashboard
    - url: https://runbooks.internal/payment-service
      title: Runbook
spec:
  type: service
  lifecycle: production
  owner: team-payments
  system: billing-platform
  dependsOn:
    - component:default/user-service
    - resource:default/payments-db
  providesApis:
    - payment-api
  consumesApis:
    - user-api
    - notification-api
---
apiVersion: backstage.io/v1alpha1
kind: API
metadata:
  name: payment-api
  description: Payment processing API
spec:
  type: grpc
  lifecycle: production
  owner: team-payments
  system: billing-platform
  definition:
    $text: ./proto/payment.proto
```

**Backstage Software Template for New Services**:

```yaml
# template.yaml - Backstage scaffolder template
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: create-microservice
  title: Create a New Microservice
  description: Scaffolds a production-ready microservice with CI/CD, monitoring, and docs
  tags:
    - recommended
    - golden-path
spec:
  owner: team-platform
  type: service
  parameters:
    - title: Service Details
      required:
        - name
        - owner
        - language
      properties:
        name:
          title: Service Name
          type: string
          pattern: "^[a-z][a-z0-9-]*$"
          ui:autofocus: true
        owner:
          title: Owning Team
          type: string
          ui:field: OwnerPicker
          ui:options:
            allowedKinds: [Group]
        language:
          title: Language
          type: string
          enum: [go, python, typescript]
          default: go
        description:
          title: Description
          type: string
    - title: Infrastructure
      properties:
        database:
          title: Database
          type: string
          enum: [none, postgresql, redis, both]
          default: none
        exposePublicly:
          title: Expose via public API gateway
          type: boolean
          default: false
  steps:
    - id: fetch-template
      name: Fetch service template
      action: fetch:template
      input:
        url: ./skeleton/${{ parameters.language }}
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          description: ${{ parameters.description }}
          database: ${{ parameters.database }}
    - id: create-repo
      name: Create GitHub repository
      action: publish:github
      input:
        repoUrl: github.com?owner=myorg&repo=${{ parameters.name }}
        defaultBranch: main
        protectDefaultBranch: true
        requireCodeOwnerReviews: true
    - id: register-catalog
      name: Register in Backstage catalog
      action: catalog:register
      input:
        repoContentsUrl: ${{ steps['create-repo'].output.repoContentsUrl }}
        catalogInfoPath: /catalog-info.yaml
  output:
    links:
      - title: Repository
        url: ${{ steps['create-repo'].output.remoteUrl }}
      - title: Service in Catalog
        icon: catalog
        entityRef: ${{ steps['register-catalog'].output.entityRef }}
```

**Platform as a Product Mindset**:

- Conduct regular developer interviews and surveys to understand pain points
- Maintain a public platform roadmap visible to all engineering teams
- Track Net Promoter Score (NPS) for the platform quarterly
- Publish a platform changelog and announce new capabilities proactively
- Treat breaking changes with the same rigor as public API changes (deprecation notices, migration guides, support windows)
