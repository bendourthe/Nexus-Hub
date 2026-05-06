# Claude Skills Collection

**Production-ready Claude Skills for software development, testing, compliance, and documentation**

---

## Overview

This directory contains a comprehensive collection of Claude Skills designed for use with:
- **Claude Code** (CLI) - Place in `.claude/skills/` in your project
- **Claude.ai** - Import as ZIP files via the Skills UI
- **Claude API** - Reference via Skills API

These skills mirror and extend the templates in [`templates/`](../templates/), converted to the official Claude Skills format for automated discovery and activation.

---

## Quick Start

### Using with Claude Code (Recommended)

1. **Copy skill folder to your project:**
   ```bash
   # Copy a single skill
   cp -r catalog/skills/tests-generation/unit-tests/ .claude/skills/

   # Or copy an entire category
   cp -r catalog/skills/tests-generation/ .claude/skills/
   ```

2. **Use the skill:**
   ```
   "Generate unit tests for my Python authentication module"
   ```
   Claude will automatically discover and use the appropriate skill.

### Using with Claude.ai

1. **ZIP a skill folder:**
   ```bash
   cd catalog/skills/tests-generation
   zip -r unit-tests.zip unit-tests/
   ```

2. **Import in Claude.ai:**
   - Go to Settings > Skills
   - Click "Upload Custom Skill"
   - Select the ZIP file

### Using with Claude API

Reference skills programmatically via the [Skills API](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/skills).

---

## Skill Categories

### [AI Development](ai-development/) (6 skills)

AI agent architecture, RAG pipelines, prompt engineering, and multi-provider integration.

| Skill | Description |
|-------|-------------|
| `ai-agent-development` | Agent architecture, tool use, memory systems, multi-agent orchestration |
| `ai-billing-safeguards` | Spending caps and billing safeguards for autonomous AI agents |
| `claude-agent-sdk` | Claude Agent SDK integration in TypeScript with retry logic and audit logging |
| `multi-provider-ai` | Route LLM requests across Anthropic, AWS Bedrock, Vertex AI, OpenRouter |
| `prompt-engineering` | Prompt design, chain-of-thought, few-shot learning, evaluation |
| `rag-implementation` | RAG pipelines: chunking, embeddings, vector stores, retrieval optimization |

### [Architecture](architecture/) (6 skills)

System design, domain-driven design, and distributed architecture patterns.

| Skill | Description |
|-------|-------------|
| `api-design` | REST, GraphQL, gRPC design with versioning, pagination, error handling |
| `architecture-design` | System decomposition, ADRs, trade-off evaluation |
| `component-boundary-identifier` | Module boundary detection for microservice extraction |
| `ddd-strategic-design` | Bounded contexts, aggregates, domain events |
| `event-driven-architecture` | Event sourcing, CQRS, message brokers, schema design |
| `microservices-patterns` | Service decomposition, inter-service communication, resilience |

### [Bug Fixing](bug-fixing/) (5 skills)

Bug localization, patch generation, and regression analysis.

| Skill | Description |
|-------|-------------|
| `bug-localization` | Stack traces, error logs, spectrum-based fault localization, bisection |
| `bug-reproduction-test-generator` | Minimal reproduction tests from bug reports |
| `bug-to-patch-generator` | Code patches from bug reports, error messages, failing tests |
| `regression-root-cause-analyzer` | Root causes via diff analysis, git bisect, test correlation |
| `semantic-bug-detector` | Logic errors, race conditions, off-by-one, null safety issues |

### [Business & Product](business-product/) (4 skills)

Product management, business analysis, and professional technical writing.

| Skill | Description |
|-------|-------------|
| `business-analyst` | Requirements elicitation, process modeling, gap analysis |
| `product-manager` | Product framing, prioritization, scope control |
| `scrum-master` | Sprint planning, retrospectives, velocity tracking, agile coaching |
| `technical-writer` | Audience-appropriate documentation, style guides |

### [Code Cleanup](code-cleanup/) (8 skills)

Language-specific dead code removal and modernization.

| Skill | Language | Focus Areas |
|-------|----------|-------------|
| `c-cleanup` | C | Memory leaks, MISRA, dead code |
| `cpp-cleanup` | C++ | Modern C++, RAII, smart pointers |
| `csharp-cleanup` | C# | Async patterns, LINQ |
| `go-cleanup` | Go | gofmt, error handling |
| `java-cleanup` | Java | Dead code, deprecated APIs |
| `javascript-cleanup` | JavaScript/TypeScript | ESLint, unused exports |
| `project-layout-refactor` | Any | Repository root audit, file moves, reference fixes |
| `python-cleanup` | Python | PEP 8, type hints, dead code |

### [Code Review](code-review/) (9 skills)

Systematic code review methodology with specialized analyzers.

| Skill | Description |
|-------|-------------|
| `behavior-preservation-checker` | Verify refactoring preserves existing behavior |
| `code-quality` | Style, maintainability, complexity, SOLID principles |
| `code-smell-detector` | Martin Fowler's catalog with severity scoring |
| `context-analysis` | Project structure, architecture, dependencies (Phase 1) |
| `final-report` | Consolidated 4-section review report (Phase 6) |
| `intent-based-review` | Review AI-generated code via acceptance criteria |
| `performance-review` | Bottlenecks, resource usage, caching strategies (Phase 4) |
| `security-review` | OWASP Top 10, race conditions, supply chain (Phase 3) |
| `testing-review` | Coverage, test quality, strategy effectiveness (Phase 5) |

### [Compliance](compliance/) (9 skills)

Enterprise compliance frameworks and AI governance.

| Skill | Framework | Use Case |
|-------|-----------|----------|
| `ai-agent-governance` | 4 Pillars Framework | Agentic AI |
| `ccpa-compliance` | CCPA | California privacy |
| `gdpr-compliance` | GDPR | EU data protection |
| `iso27001-compliance` | ISO 27001:2022 | Information security |
| `iso42001-ai-governance` | ISO 42001:2023 | AI management |
| `nist-ai-rmf` | NIST AI RMF | US federal AI |
| `pci-dss-compliance` | PCI-DSS v4.0 | Payment processing |
| `soc2-compliance` | SOC 2 Type II | Enterprise SaaS |
| `traceability-matrix-generator` | Audit readiness | Requirement-to-code traceability |

### [Developer Experience](developer-experience/) (21 skills)

Refactoring, legacy modernization, tooling, and productivity patterns.

| Skill | Description |
|-------|-------------|
| `ai-output-evaluation` | LLM-as-judge quality evaluation with rubrics |
| `ambiguity-detector` | Detect ambiguous or contradictory requirements |
| `analysis-logic` | Structured analytical reasoning and data presentation |
| `async-patterns` | Promises, futures, channels, actors, structured concurrency |
| `code-optimizer` | Algorithmic complexity, memory usage, caching, concurrency |
| `code-translation` | Translate code between languages preserving logic and style |
| `context-optimization` | Minimize token usage in AI coding sessions |
| `creative-generation` | Image prompts, slide decks, brainstorming |
| `dead-code-eliminator` | Find and remove unreachable functions, unused imports |
| `dependency-manager` | Safe dependency upgrades, breaking changes, lock files |
| `deprecated-api-updater` | Detect and update deprecated API calls |
| `design-pattern-suggestor` | GoF and modern design patterns with implementation guides |
| `error-explanation-generator` | Plain-language error and stack trace explanations |
| `framework-migration-assistant` | Guide framework migrations with coexistence patterns |
| `graphql-development` | Schema design, resolvers, N+1 prevention, subscriptions |
| `legacy-modernizer` | Strangler Fig pattern, incremental modernization |
| `refactoring-expert` | Martin Fowler's catalog, safe behavior-preserving changes |
| `requirement-enhancer` | Quality, completeness, and testability of requirements |
| `technical-debt-analyzer` | SQALE methodology, interest calculation, remediation planning |
| `tool-design` | MCP servers, slash commands, function schemas for agents |
| `writing-editing` | Professional writing and editing for docs and prose |

### [Documentation](documentation/) (6 skills)

Comprehensive documentation generation.

| Skill | Description | Output |
|-------|-------------|--------|
| `api-documentation` | OpenAPI/Swagger, endpoint descriptions | API reference |
| `docstrings` | Function/class documentation | JSDoc, PyDoc, etc. |
| `sbom-generation` | Software Bill of Materials | SBOM files |
| `strategic-comments` | High-value code comments | Inline comments |
| `technical-documentation` | Architecture, ADRs | Design docs |
| `user-documentation` | README, tutorials, guides | Markdown docs |

### [Framework Specialists](framework-specialists/) (6 skills)

Deep expertise for specific web frameworks.

| Skill | Framework | Focus |
|-------|-----------|-------|
| `astro-expert` | Astro | Content collections, island architecture, multi-framework integration |
| `fastapi-expert` | FastAPI | Async APIs, Pydantic, dependency injection |
| `nextjs-expert` | Next.js | App Router, Server Components, SSR/SSG |
| `react-expert` | React | Hooks, state management, performance |
| `svelte-expert` | Svelte | Runes, SvelteKit routing, SSR, form actions |
| `vue-expert` | Vue 3 | Composition API, Pinia, Vue Router, optimization |

### [Infrastructure](infrastructure/) (16 skills)

Cloud, containers, CI/CD, observability, and reliability engineering.

| Skill | Description |
|-------|-------------|
| `azure-infra-engineer` | Azure resources, Bicep/Terraform, AD, AKS, networking |
| `cd-pipeline-generator` | GitHub Actions, GitLab CI, Jenkins, ArgoCD deployments |
| `cicd-architect` | CI/CD pipeline design, deployment strategies |
| `cloud-architect` | Multi-cloud (AWS, Azure, GCP), Well-Architected Framework |
| `config-consistency-checker` | Configuration drift detection across environments |
| `containerization` | Dockerfile optimization, multi-stage builds, Compose |
| `data-pipeline-design` | ETL/ELT, streaming, data validation, orchestration |
| `database-design` | Schema modeling, indexing, migrations, query optimization |
| `kubernetes-expert` | K8s orchestration, Helm charts, RBAC, troubleshooting |
| `network-engineer` | VPCs, subnets, DNS, load balancing, firewalls |
| `observability-setup` | Structured logging, metrics, tracing, OpenTelemetry |
| `platform-engineer` | Internal developer platforms, golden paths, self-service |
| `release-notes-writer` | Professional release notes from git history and PRs |
| `rollback-strategy-advisor` | Rollback strategies, incident response, deployment runbooks |
| `sre-engineer` | SLOs/SLIs, incident response, capacity planning |
| `terraform-specialist` | IaC with Terraform/OpenTofu, multi-environment setups |

### [Language Specialists](language-specialists/) (10 skills)

Deep language-specific expertise for production systems.

| Skill | Language | Model Hint | Permissions |
|-------|----------|------------|-------------|
| `cpp-expert` | C++ | high-reasoning | write |
| `csharp-expert` | C# | high-reasoning | write |
| `go-expert` | Go | high-reasoning | write |
| `java-expert` | Java | high-reasoning | write |
| `javascript-expert` | JavaScript | high-reasoning | write |
| `powershell-expert` | PowerShell | high-reasoning | write |
| `python-expert` | Python | high-reasoning | write |
| `rust-expert` | Rust | high-reasoning | write |
| `sql-expert` | SQL | balanced | read-only |
| `typescript-expert` | TypeScript | high-reasoning | write |

### [Orchestration](orchestration/) (14 skills)

Context management, task coordination, multi-agent workflows, and quality gates.

| Skill | Description |
|-------|-------------|
| `adversarial-verifier` | Stress-test implementations with adversarial inputs |
| `agent-access-policy` | File-level access controls for AI coding agents |
| `competitive-generation` | Run multiple agents in parallel, select best output |
| `context-compression` | Minimize tokens per task in long sessions |
| `context-degradation` | Detect and mitigate context quality decay |
| `context-manager` | Context window management across large codebases |
| `cross-model-orchestrator` | Coordinate Claude, Codex, Gemini, Copilot in workflows |
| `error-coordinator` | Cross-agent error resolution and recovery |
| `multi-agent-coordinator` | Concurrent subagent execution with role separation |
| `prompt-token-optimization` | Minimize token consumption, maximize context usage |
| `quality-gate-definitions` | GO/NO-GO gates for multi-phase workflows |
| `task-coordinator` | Multi-step task decomposition and dependency tracking |
| `temporal-orchestration` | Durable AI agent pipelines using Temporal workflows |
| `workflow-orchestrator` | End-to-end workflow chaining with quality gates |

### [Project Setup](project-setup/) (4 skills)

Project initialization and configuration.

| Skill | Language | Creates |
|-------|----------|---------|
| `init-csharp-project` | C# | .csproj, xUnit, NuGet |
| `init-java-project` | Java | Maven/Gradle, JUnit |
| `init-javascript-project` | JavaScript/TS | package.json, ESLint, Jest |
| `init-python-project` | Python | pyproject.toml, tests, CI |

### [Research](research/) (1 skill)

Trend research and competitive analysis.

| Skill | Description |
|-------|-------------|
| `trend-research` | Research Reddit, X, and the web for 30-day trends |

### [Security](security/) (7 skills)

Security-focused development practices and vulnerability analysis.

| Skill | Description |
|-------|-------------|
| `authentication-patterns` | OAuth 2.0, OIDC, JWT, session management, MFA, passkeys |
| `cve-reachability-analyzer` | Trace call paths to determine if a CVE affects your app |
| `dependency-security-audit` | CVE scanning, license issues, SBOM generation |
| `exploitability-analyzer` | CVSS scoring, attack path analysis, compensating controls |
| `licensing-compliance` | License audit, compatibility, compliance reports |
| `pre-commit-checklist` | Linting, formatting, type checks, security scans |
| `security-patch-advisor` | Patches for XSS, SQLi, SSRF, CSRF, misconfigurations |

### [Specialized Domains](specialized-domains/) (9 skills)

Domain-specific engineering expertise.

| Skill | Description |
|-------|-------------|
| `android-development` | Kotlin, Jetpack Compose, Material Design 3, modern Android architecture |
| `docx-generation` | Professional Word documents with templates, styles, multi-library support |
| `fintech-engineer` | Payment processing, ledger systems, PCI-DSS, fraud detection |
| `gif-sticker-maker` | Animated GIFs and stickers with AI generation, video processing, frame animation |
| `glsl-shader-development` | GLSL shaders for visual effects, ray marching, procedural generation, 3D graphics |
| `ios-development` | Swift, SwiftUI, UIKit, modern Apple platform patterns |
| `pdf-document-generation` | Professional PDF documents with layout design, typography, multi-library support |
| `pptx-generation` | Professional PowerPoint presentations with slide design, charts, multi-library support |
| `xlsx-generation` | Excel spreadsheets with formulas, charts, multi-library support |

### [Testing](testing/) (2 skills)

Testing methodology and automation (distinct from test generation).

| Skill | Description |
|-------|-------------|
| `domain-contract-validator` | Business rule assertions via contract and schema testing |
| `e2e-testing-automation` | Playwright, Cypress, Selenium with page objects and CI |

### [Tests Generation](tests-generation/) (17 skills)

Complete testing methodology from unit tests to mutation testing and edge-case generation.

| Skill | Description | Languages |
|-------|-------------|-----------|
| `bdd-acceptance-tests` | Executable BDD tests from Given/When/Then criteria | Python, JS |
| `cicd-integration` | Test automation in CI/CD with quality gates | All 7 |
| `code-coverage` | Coverage analysis, 80%+ target | All 7 |
| `directed-test-input-generator` | Targeted inputs to reach specific code paths | All 7 |
| `edge-case-generator` | Boundary conditions, empty inputs, overflow, null | All 7 |
| `flaky-test-detector` | Timing dependencies, shared state, ordering issues | All 7 |
| `fuzzing-input-generator` | Mutation-based, grammar-based, coverage-guided fuzzing | All 7 |
| `integration-test-generator` | API boundaries, databases, message queues, testcontainers | All 7 |
| `metamorphic-test-generator` | Transformation invariants for systems without oracles | All 7 |
| `mocks-fixtures` | Test doubles, factories, fixtures | All 7 |
| `mutation-testing` | Test quality validation | All 7 |
| `performance-testing` | Load, stress, benchmark testing | All 7 |
| `property-based-test-generator` | QuickCheck/Hypothesis-style invariant testing | All 7 |
| `test-cases` | Integration and E2E test scenarios | All 7 |
| `test-structure` | Framework setup, directories, configuration | All 7 |
| `test-suite-prioritizer` | Order tests for faster CI feedback | All 7 |
| `unit-tests` | FIRST principles, AAA pattern, isolation | All 7 |

### [Workflow](workflow/) (14 skills)

Development process, methodology, and session management.

| Skill | Description |
|-------|-------------|
| `code-commit-workflow` | Conventional commits, atomic changes, meaningful messages |
| `conflict-analyzer` | Three-way merge analysis, conflict classification, resolution |
| `create-custom-command` | Create slash commands for Claude Code |
| `cross-project-comparison` | Gap analysis against external knowledge sources |
| `debug-with-logs` | Strategic logging and log-based debugging |
| `devlog-generation` | Development logs from git history and artifacts |
| `documentation-consistency` | Verify docs are up-to-date, check broken links |
| `filesystem-context-patterns` | Filesystem as context management tool for AI sessions |
| `git-bisect-assistant` | Efficient bug-finding with git bisect |
| `plan-before-code` | Exploration and planning before implementation |
| `research-plan-implement` | Structured RPI workflow with GO/NO-GO gates |
| `session-history` | Standalone session history documents capturing steps and next steps |
| `test-driven-development` | TDD workflow: write tests first, then code |
| `version-upgrade` | Version bump, changelog, documentation updates |

---

## Supported Languages

All multi-language skills support:

- **Python** - pytest, Django, Flask, FastAPI
- **JavaScript/TypeScript** - Jest, Node.js, React, Vue
- **Java** - JUnit 5, Spring Boot, Maven/Gradle
- **C#** - xUnit, .NET Core, ASP.NET
- **Go** - testing package, Gin, Echo
- **C** - Unity, CUnit, embedded systems
- **C++** - GoogleTest, Catch2, modern C++

---

## Skill Format

Each skill follows the [official Claude Skills specification](https://code.claude.com/docs/en/skills):

```
skill-name/
└── SKILL.md          # Required: Instructions and metadata
```

### SKILL.md Structure

```yaml
---
name: skill-name
description: What the skill does AND when to use it (max 1024 chars)
allowed-tools: Read, Write, Glob, Grep, Bash  # Optional restrictions
---

# Skill Title

## When to Use This Skill
[Trigger conditions and use cases]

## What This Skill Does
[Detailed functionality]

## Instructions
[Step-by-step guidance with code examples]

## Quality Checklist
[Verification items]

## Related Skills
[Cross-references]
```

### SKILL.md Frontmatter Fields

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `name` | Yes | string | Unique skill identifier (kebab-case) |
| `description` | Yes | string (max 1024 chars) | What the skill does AND when to use it |
| `allowed-tools` | No | comma-separated tool names | Restrict which tools the skill may use |

### Catalog-Level Fields (skills.json only)

These advisory fields are stored in `data/skills.json` entries, not in SKILL.md frontmatter (Claude Code does not support custom frontmatter attributes).

| Field | Values | Description |
|-------|--------|-------------|
| `model_hint` | `high-reasoning` / `fast-scan` / `balanced` | Advisory model selection. `high-reasoning` for architecture, security audits, complex design. `fast-scan` for quick scanning, synthesis, lightweight research. `balanced` (default) for general tasks. |
| `reasoning_effort` | `high` / `medium` / `low` | Advisory reasoning calibration. Does not override platform settings. |
| `permissions` | `read-only` / `write` | Recommended permission level. `read-only` for review, audit, and research skills. `write` for implementation skills. Informational only; actual permissions managed by the platform. |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Skills | 187 |
| Categories | 22 |
| Languages | 7 |
| Avg. Lines/Skill | 400-800 |

### By Category

| Category | Skills |
|----------|--------|
| AI Development | 6 |
| Architecture | 6 |
| Bug Fixing | 5 |
| Business & Product | 4 |
| Code Cleanup | 8 |
| Code Review | 9 |
| Compliance | 9 |
| Developer Experience | 21 |
| Documentation | 6 |
| Framework Specialists | 6 |
| Infrastructure | 16 |
| Language Specialists | 10 |
| Orchestration | 14 |
| Project Setup | 4 |
| Research | 1 |
| Security | 7 |
| Specialized Domains | 9 |
| Testing | 2 |
| Tests Generation | 17 |
| Workflow | 14 |

---

## Creating Custom Skills

### From Templates

1. Choose a template from [`templates/`](../../templates/)
2. Extract key sections:
   - Objective → Description
   - Instructions → Step-by-step
   - Checklists → Quality Checklist
3. Add YAML frontmatter
4. Include trigger phrases in description

### Best Practices

1. **Description is critical** - Include WHAT and WHEN
2. **Be specific** - One capability per skill
3. **Include triggers** - Words users would say
4. **Cross-reference** - Link related skills
5. **Test activation** - Verify skill triggers correctly

---

## Related Resources

- [Claude Skills Documentation](https://code.claude.com/docs/en/skills)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- [Source Templates](../templates/)
- [Language Templates](../templates/ai-instructions/CLAUDE_MD/)
- [Guides](../guides/)

---

## Version

- **Collection Version**: 1.1.2
- **Last Updated**: May 2026
- **Author**: Benjamin Dourthe

---

## License

These skills are provided under the same license as the parent DevAI-Hub repository. See [LICENSE](../../LICENSE) for details.
