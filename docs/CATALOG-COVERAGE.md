# Nexus-Hub Catalog Coverage Matrix

**Version**: 1.0.0
**Generated**: 2026-04-27
**Skills Total**: 187 across 22 categories

This matrix maps Nexus-Hub's skill catalog against user roles, AI platforms, and use case categories to help you find the right skills for your context. Inspired by [Shannon's COVERAGE.md](https://github.com/KeygraphHQ/shannon) pattern.

---

## v1.0.0 Release Additions

**Internal MCP servers (2 new)** - both zero outbound calls, zero API keys:
- [`nexus-code-search`](../extensions/nexus-code-search/) - local code search with keyword retrieval, content-hash incremental indexing, symlink-safe walker. Tools: `index_codebase`, `search_code`, `clear_index`, `get_indexing_status`. Dense / hybrid retrieval planned for v1.1.0.
- [`nexus-web-fetch`](../extensions/nexus-web-fetch/) - HTTP fetch + `readability-lxml` extraction with per-hop SSRF guard, DNS pinning, manual redirect re-validation. Tool: `fetch_url(url, render_js, extract_mode)`.

**New skills (3)**:
- `code-semantic-search` (ai-development) - specialized sibling of `rag-implementation` for code corpora; pairs with `nexus-code-search`.
- `ui-component-generation` (developer-experience) - LLM-native replacement for external component-generation services.
- `local-docs-lookup` (research) - 7-step grounding sequence for library / API questions; partial replacement for `context7`-class MCPs.

**Policy and governance**:
- New [MCP Registry Policy](../AGENTS.md#mcp-registry-policy) section in `AGENTS.md` with reverse-engineering-first decision tree + 5-question audit checklist. Distributed diff-identical to all 7 platform-instruction surfaces.
- New [Reverse-Engineering Matrix](v1.0.0/mcp-reverse-engineering-matrix.md) at `docs/policy/mcp-reverse-engineering-matrix.md` - authoritative classification of every MCP shipped or considered (18 rows).

**Command extensions**:
- [`/compare-project`](../catalog/commands/compare-project.md) gained a mandatory **Section 9: Security and Risk Assessment** with four subsections (threat model, per-item risk, RE viability, recommendation ordering). The `/generate-plan` chain always passes `reverse-engineer-first=true`.

**New commands (1)**:
- [`/run-deep-review`](../catalog/commands/run-deep-review.md) - 12-phase pre-release deep-review orchestrator. Chains known-gaps collection, health gates (with 80% line-coverage threshold), dependency scan, docs / git / CI/CD / release-readiness hygiene, project validators, `/analyze-codebase`, `/run-security-audit`, `/run-penetration-test --depth=deep`, and `/review-codebase`, then synthesizes everything into a single P0/P1/P2/P3-ranked report with a GO / GO-WITH-CONDITIONS / NO-GO verdict. Phase 4 covers CI/CD workflow file audit, CI run history, branch protection, version-bump consistency, tag hygiene, and pending draft releases. Ends with `/generate-plan` to produce a remediation roadmap. All artifacts land under `docs/<next-version>/review/`. Run before cutting a major or minor release.

**Removed (BREAKING)**:
- 4 third-party MCP registry entries dropped: `context7`, `exa-web-search`, `firecrawl`, `magic-ui`. Users who relied on these can re-add them to their own `.claude/settings.json`; Nexus-Hub no longer ships the snippets.

**Tooling**:
- New `make benchmark` target + `scripts/nexus_mcp_benchmark.py` exercising all 3 internal MCPs with a no-network guard.
- Style-guide companion files relocated to `catalog/style-guides/` so they no longer surface as slash commands.

**Skill content de-branding**:
- `rag-implementation` skill stripped of external-source attribution (zilliztech / claude-context, voyage-code-3, SWE-bench metrics) while preserving the technical patterns. Concrete references now point at the internal `nexus-code-search` MCP.

---

## v0.9.7 Release Additions

**New skills (3)**:
- `business-logic-abuse` (Security) - domain-aware invariant-violation audit covering race conditions, TOCTOU, double-spending, workflow bypass, idempotency, check-sequence abuse.
- `advanced-attack-patterns` (Security) - state desynchronization, cache poisoning, replay attacks, and timing side channels beyond password comparison.
- `deep-research-compilation` (Specialized Domains) - compile multiple research reports across 7 input formats into a single unified document with deduplicated citations; emits .docx / .pdf / .md.

**New commands (1)**:
- `/compile-deep-research` (+ companion `catalog/style-guides/compile-deep-research.md`) - 9-phase command that drives the deep-research-compilation skill. Agent-driven per invocation: the agent inspects the user-selected template, builds a style profile, synthesizes content, and writes a throwaway python-docx generator tailored to that template - no persistent generator script. The style guide is reference content located outside `catalog/commands/` so it does not surface as a slash command.

**New AI agent instruction set (5 files)**:
- `AGENTS.md` extended with "Installer-Aware Changes (Cross-Platform)" section; `CLAUDE.md` and `GEMINI.md` use `@AGENTS.md` import; `.github/copilot-instructions.md` inlines the summary (Copilot cannot import); `.cursor/rules/nexus-hub.mdc` uses `alwaysApply: true`.

**New bundled template (1)**:
- `templates/documentation/branded-report-template.docx` - styled Word template (teal Consolas title, Calibri Light small-caps headings, auto-TOC, hanging-indent references) that ships alongside the existing generic template.

**New guides (2)**:
- [guides/reference/SESSION_LIFECYCLE_DECISIONS.md](../guides/reference/SESSION_LIFECYCLE_DECISIONS.md) - five-branch decision tree (continue / `/rewind` / `/clear` / `/compact` / delegate to subagent).
- [docs/archives/v0/v0.9/opus-4-7-migration.md](archives/v0/v0.9/opus-4-7-migration.md) - operator migration guide with TL;DR, four must-do items, and a 13-row cross-reference table indexing every Opus 4.6 -> 4.7 behavioral delta.

**New checklists (1)**:
- [catalog/checklists/file-upload-security.md](../catalog/checklists/file-upload-security.md) - defense checklist against polyglot files, MIME confusion, archive path traversal, zip bombs, and unsafe upload serving.

**Extended skills** (content additions; skill count unchanged):
- `prompt-engineering` - Effort-Level Strategy section (all 5 tiers + decision table + anti-patterns); Opus 4.7 Practices section (positive examples, explicit tool-invocation, adaptive thinking, first-turn checklists).
- `ai-agent-development` - Anti-Patterns (Opus 4.7) table (fixed thinking budgets, excessive tool-calling, `max` on extended runs).
- `multi-agent-coordinator` - Step 0 delegation gate ("will I need this tool output again?"), Pattern A explicit fan-out callout with three worked prompt templates.
- `context-compression` - Proactive steering subsection with six `/compact focus on X, drop Y` directives.
- `context-degradation` - 1M-token window calibration table (Green/Yellow/Orange/Red at 100k/300k/500k boundaries).
- `session-history` - "Summarize from here (mid-session handoff)" operating mode with paste-ready template.
- `security-patch-advisor` - Related Resources footer cross-linking to the file-upload-security checklist and the two new security skills.

**Extended commands**:
- `/run-penetration-test` - optional 6th hunter (Business Logic & Advanced Attacks) gated behind `--depth=deep`; Attack Paths renamed to "Attack Paths / Chains"; new Secure Design Recommendations subsection; WSTG Coverage Matrix expanded with BUSL, cache poisoning, replay, and timing rows; hunter agents use shipped default `high` effort level.

**Configuration change (operator-facing)**:
- Installer default `effortLevel` reduced from `xhigh` to `high` (`catalog/hooks/settings.json`, `scripts/installer.ps1`). Full details in [CHANGELOG.md](../CHANGELOG.md) and [docs/archives/v0/v0.9/opus-4-7-migration.md](archives/v0/v0.9/opus-4-7-migration.md).

---

## How to Read This Matrix

- **Role Bundles**: Pre-selected sets of skills for specific professional roles. Install a bundle for a curated starting point.
- **Category Coverage**: All skills by category, with AI platform compatibility and primary use cases.
- **Platform Compatibility**: All skills work with Claude Code. Skills marked with platform icons also work with other AI assistants.

**Platform icons**: `C` = Claude Code, `G` = Gemini, `K` = Copilot, `X` = Codex

---

## Role Bundles (Pre-Selected Skill Sets)

| Bundle | Skills | Primary Use Case |
|--------|--------|-----------------|
| **Core Developer** (10) | plan-before-code, test-driven-development, code-commit-workflow, debug-with-logs, refactoring-expert, unit-tests, code-quality, add-strategic-comments, pre-commit-checklist, research-plan-implement | Daily development workflow across any stack |
| **Frontend Engineer** (8) | react-expert, nextjs-expert, cleanup-javascript, e2e-testing-automation, api-design, authentication-patterns, async-patterns, graphql-development | React/Next.js frontend and full-stack |
| **Backend Engineer** (8) | api-design, fastapi-expert, database-design, authentication-patterns, microservices-patterns, async-patterns, performance-review, dependency-security-audit | APIs, databases, server-side systems |
| **AI Engineer** (12) | ai-agent-development, claude-agent-sdk, rag-implementation, prompt-engineering, tool-design, ai-output-evaluation, data-pipeline-design, cross-model-orchestrator, prompt-token-optimization, multi-provider-ai, ai-billing-safeguards, agent-access-policy | AI agents, LLM apps, RAG pipelines |
| **Software Architect** (9) | architecture-design, ddd-strategic-design, microservices-patterns, event-driven-architecture, api-design, component-boundary-identifier, database-design, observability-setup, technical-debt-analyzer | System design, architecture decisions |
| **DevOps Engineer** (12) | cicd-architect, cloud-architect, kubernetes-expert, terraform-specialist, containerization, ai-docker-orchestration, cd-pipeline-generator, rollback-strategy-advisor, observability-setup, config-consistency-checker, dependency-manager, temporal-orchestration | Infrastructure, CI/CD, cloud platforms |
| **Security Specialist** (13) | dependency-security-audit, pre-commit-checklist, licensing-compliance-check, exploitability-analyzer, security-patch-advisor, cve-reachability-analyzer, authentication-patterns, ai-billing-safeguards, agent-access-policy, secret-detection, threat-modeling, input-validation, security-headers | Security auditing, vulnerability assessment |
| **Compliance Auditor** (9) | gdpr-compliance, ccpa-compliance, soc2-compliance, iso27001-compliance, pci-dss-compliance, iso42001-ai-governance, nist-ai-rmf, ai-agent-governance, traceability-matrix-generator | Regulatory compliance, audit evidence |
| **QA Engineer** (16) | generate-test-cases, setup-test-infrastructure, unit-tests, test-cases, mocks-fixtures, mutation-testing, performance-testing, code-coverage, cicd-integration, edge-case-generator, flaky-test-detector, integration-test-generator, property-based-test-generator, e2e-testing-automation, test-suite-prioritizer, fuzzing-input-generator | Comprehensive test coverage |
| **Bug Hunter** (9) | bug-localization, bug-to-patch-generator, regression-root-cause-analyzer, bug-reproduction-test-generator, semantic-bug-detector, debug-with-logs, flaky-test-detector, exploitability-analyzer, git-bisect-assistant | Bug finding, root cause analysis |
| **Tech Lead** (18) | architecture-design, code-review-quality, code-review-security, technical-debt-analyzer, plan-before-code, release-notes-writer, version-upgrade, documentation-consistency, cicd-architect, team-review-workflow, conflict-analyzer, quality-gate-definitions, research-plan-implement, devlog-generation, code-commit-workflow, refactoring-expert, dependency-manager, ai-agent-governance | Technical leadership, team coordination |

---

## Category Coverage

### AI Development (5 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| ai-agent-development | ReAct, planning, memory, orchestration, guardrails, evaluation | Building Python AI agents | C G K X |
| claude-agent-sdk | TypeScript SDK integration -- retry, multi-provider, spending caps, audit logging | Production Claude Agent SDK in Node.js | C G K X |
| prompt-engineering | System prompts, few-shot, chain-of-thought, temperature, structured output | LLM prompt design | C G K X |
| rag-implementation | Vector stores, chunking, embedding, retrieval, reranking | Retrieval-augmented generation | C G K X |
| multi-provider-ai | Provider selection, env config, unified client, fallback routing for Anthropic/Bedrock/Vertex/OpenRouter | Multi-cloud LLM deployment | C G K X |

### Architecture (6 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| architecture-design | System design patterns, trade-off analysis, ADRs | New system design |  C G K X |
| api-design | REST, GraphQL, gRPC design principles, versioning, contract-first | API contract design | C G K X |
| ddd-strategic-design | Bounded contexts, aggregates, domain events, ubiquitous language | Complex domain modeling | C G K X |
| microservices-patterns | Service decomposition, inter-service communication, fault tolerance | Microservices architecture | C G K X |
| event-driven-architecture | Event sourcing, CQRS, message brokers, saga patterns | Event-driven systems | C G K X |
| component-boundary-identifier | Identify cohesion/coupling issues, propose boundary refactors | Legacy system decomposition | C G K X |

### Bug Fixing (5 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| bug-localization | Narrow bug scope using logs, stack traces, bisect | First-pass bug investigation | C G K X |
| bug-to-patch-generator | Generate minimal fix from reproduction case | Automated patch generation | C G K X |
| regression-root-cause-analyzer | Identify what change introduced a regression | Regression investigation | C G K X |
| bug-reproduction-test-generator | Write a test that captures the bug before fixing | Test-first bug fixing | C G K X |
| semantic-bug-detector | Identify logic errors that don't surface as syntax errors | Code review augmentation | C G K X |

### Code Cleanup (8 skills) -- `C` `G` `K` `X`

| Skill | Description | Language | Platforms |
|-------|-------------|----------|-----------|
| cleanup-c | Dead code, memory leaks, MISRA C, safety | C | C G K X |
| cleanup-cpp | Modern C++17/20, RAII, smart pointers | C++ | C G K X |
| cleanup-csharp | .NET idioms, LINQ, async/await, nullable | C# | C G K X |
| cleanup-go | Idiomatic Go, goroutine safety, error handling | Go | C G K X |
| cleanup-java | Java 17+, streams, records, null safety | Java | C G K X |
| cleanup-javascript | ES2022+, async/await, module system | JavaScript | C G K X |
| cleanup-python | PEP 8, type hints, dataclasses, pathlib | Python | C G K X |
| cleanup-typescript | Strict TS, generics, discriminated unions | TypeScript | C G K X |

### Code Review (8 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| code-review-context-analysis | Understand change scope before reviewing | Pre-review context gathering | C G K X |
| code-review-quality | Readability, maintainability, design patterns | Quality review | C G K X |
| code-review-security | OWASP Top 10, injection, auth, secrets | Security-focused review | C G K X |
| code-review-performance | Algorithmic complexity, DB queries, caching | Performance review | C G K X |
| code-review-testing | Test coverage, test quality, edge cases | Testing review | C G K X |
| code-review-final-report | Synthesize review findings into actionable report | Review conclusion | C G K X |
| code-smell-detector | Identify code smell patterns (God class, shotgun surgery, etc.) | Technical debt discovery | C G K X |
| behavior-preservation-checker | Verify refactoring doesn't change observable behavior | Refactoring safety | C G K X |

### Compliance (9 skills) -- `C` `G` `K` `X`

| Skill | Description | Regulation | Platforms |
|-------|-------------|-----------|-----------|
| gdpr-compliance | Data subject rights, consent, DPA | GDPR (EU) | C G K X |
| ccpa-compliance | Consumer rights, opt-out, data categories | CCPA (California) | C G K X |
| soc2-compliance | Trust service criteria, control evidence | SOC 2 Type II | C G K X |
| iso27001-compliance | ISMS controls, risk assessment, annex A | ISO 27001 | C G K X |
| pci-dss-compliance | Card data protection, network segmentation | PCI-DSS | C G K X |
| iso42001-ai-governance | AI management system requirements | ISO 42001 | C G K X |
| nist-ai-rmf | AI risk framework: Map, Measure, Manage, Govern | NIST AI RMF | C G K X |
| ai-agent-governance | Autonomous agent access control, audit trails | AI governance | C G K X |
| traceability-matrix-generator | Requirement-to-implementation-to-test traceability | Compliance audits | C G K X |

### Developer Experience (18 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| dependency-manager | Upgrade strategy, compatibility, breaking change detection | Dependency maintenance | C G K X |
| legacy-modernizer | Incremental modernization path for legacy codebases | Legacy migration | C G K X |
| refactoring-expert | Safe, behavior-preserving refactoring patterns | Code quality improvement | C G K X |
| tool-design | Designing functions and APIs for LLM consumption | Agent tool design | C G K X |
| ai-output-evaluation | Scoring LLM outputs for quality, accuracy, safety | LLM quality assurance | C G K X |
| writing-editing | Technical writing, documentation quality | Content improvement | C G K X |
| analysis-logic | Structured reasoning and analytical frameworks | Complex analysis | C G K X |
| creative-generation | Creative problem solving, ideation | Design/brainstorming | C G K X |
| technical-debt-analyzer | Quantify and prioritize technical debt | Debt management | C G K X |
| dead-code-eliminator | Find and safely remove unreachable code | Codebase cleanup | C G K X |
| error-explanation-generator | Generate user-friendly error messages | UX improvement | C G K X |
| design-pattern-suggestor | Recommend appropriate design patterns | Architecture guidance | C G K X |
| code-translation | Translate code between languages | Language migration | C G K X |
| code-optimizer | Performance optimization without behavior changes | Performance improvement | C G K X |
| ambiguity-detector | Surface ambiguous requirements before coding | Requirements quality | C G K X |
| deprecated-api-updater | Replace deprecated API calls with current equivalents | API migration | C G K X |
| framework-migration-assistant | Guide migration between framework versions | Major upgrades | C G K X |
| requirement-enhancer | Improve requirement clarity and completeness | Requirements engineering | C G K X |

### Documentation (7 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| add-strategic-comments | High-value comments explaining "why" not "what" | Code documentation | C G K X |
| create-technical-docs | Architecture guides, runbooks, decision records | Technical documentation | C G K X |
| create-user-documentation | End-user guides, tutorials, FAQs | User documentation | C G K X |
| generate-api-docs | OpenAPI specs, SDK reference, endpoint documentation | API documentation | C G K X |
| generate-docstrings | Language-specific docstring generation | Inline documentation | C G K X |
| generate-sbom | Software Bill of Materials (SPDX, CycloneDX) | Supply chain security | C G K X |
| generate-report | Convert Markdown to Word (.docx) or PowerPoint (.pptx) | Report generation | C G K X |

### Framework Specialists (3 skills) -- `C` `G` `K` `X`

| Skill | Description | Framework | Platforms |
|-------|-------------|-----------|-----------|
| react-expert | Hooks, state management, performance, patterns | React | C G K X |
| nextjs-expert | App Router, SSR/SSG, API routes, deployment | Next.js | C G K X |
| fastapi-expert | Async routes, Pydantic, dependency injection, OpenAPI | FastAPI | C G K X |

### Infrastructure (13 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| cicd-architect | CI/CD pipeline design, quality gates, deployment strategies | CI/CD setup | C G K X |
| cloud-architect | Multi-cloud patterns, cost optimization, resilience | Cloud design | C G K X |
| kubernetes-expert | Pod design, RBAC, Helm, resource management | Kubernetes | C G K X |
| terraform-specialist | Infrastructure as code, state management, modules | IaC | C G K X |
| database-design | Schema design, indexing, normalization, migrations | Database architecture | C G K X |
| data-pipeline-design | ETL/ELT, streaming, batch processing, lineage | Data engineering | C G K X |
| observability-setup | Logging, metrics, tracing, alerting | Production monitoring | C G K X |
| containerization | Docker, image optimization, security hardening | Container setup | C G K X |
| ai-docker-orchestration | Docker Compose for multi-agent AI systems -- Temporal workers, LLM API key injection, health checks | AI system containerization | C G K X |
| cd-pipeline-generator | Deployment pipeline code generation | CD automation | C G K X |
| rollback-strategy-advisor | Rollback procedures for deployments and migrations | Incident recovery | C G K X |
| config-consistency-checker | Validate configuration consistency across environments | Config management | C G K X |
| temporal-orchestration | Durable workflow orchestration for parallel AI agent pipelines using Temporal | AI agent pipelines | C G K X |

### Language Specialists (3 skills) -- `C` `G` `K` `X`

| Skill | Description | Language | Platforms |
|-------|-------------|----------|-----------|
| go-expert | Goroutines, channels, interfaces, Go modules | Go | C G K X |
| rust-expert | Ownership, lifetimes, traits, async Rust | Rust | C G K X |
| sql-expert | Query optimization, window functions, indexing, CTEs | SQL | C G K X |

### Orchestration (10 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| context-manager | Managing context budgets in long agent sessions | Context optimization | C G K X |
| task-coordinator | Breaking down complex tasks into subtasks | Task decomposition | C G K X |
| workflow-orchestrator | End-to-end multi-skill workflow execution with quality gates | Multi-phase workflows | C G K X |
| temporal-orchestration | Durable, parallel, fault-tolerant AI agent pipelines using Temporal | Production agent orchestration | C G K X |
| context-degradation | Handle graceful degradation as context fills | Long session management | C G K X |
| context-compression | Compress context without losing critical information | Token budget management | C G K X |
| cross-model-orchestrator | Route tasks across different LLM providers and models | Multi-model workflows | C G K X |
| prompt-token-optimization | Reduce prompt token usage while preserving quality | Cost optimization | C G K X |
| quality-gate-definitions | Define measurable quality gates for workflows | Quality assurance | C G K X |
| ai-billing-safeguards | Spending cap enforcement, hard budget stops, cost attribution for autonomous agents | AI cost management | C G K X |

### Project Initialization (4 skills) -- `C` `G` `K` `X`

| Skill | Description | Language | Platforms |
|-------|-------------|----------|-----------|
| init-csharp-project | .NET project structure, tooling, conventions | C# | C G K X |
| init-java-project | Maven/Gradle, Spring Boot starter, conventions | Java | C G K X |
| init-javascript-project | Node.js, npm/yarn, ESLint, Prettier setup | JavaScript | C G K X |
| init-python-project | pyproject.toml, virtual env, tooling setup | Python | C G K X |

### Research (1 skill) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| trend-research | Technology trend analysis and synthesis | Technology evaluation | C G K X |

### Security (9 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| dependency-security-audit | CVE scanning, transitive dependency risks | Supply chain security | C G K X |
| pre-commit-checklist | Security checks before committing code | Commit-time security | C G K X |
| licensing-compliance-check | OSS license compatibility and obligations | License compliance | C G K X |
| exploitability-analyzer | Assess exploitability of identified vulnerabilities | Vulnerability triage | C G K X |
| security-patch-advisor | Recommend and apply security patches | Patch management | C G K X |
| cve-reachability-analyzer | Determine if a CVE affects reachable code paths | Risk assessment | C G K X |
| authentication-patterns | OAuth 2.0, JWT, session management, MFA patterns | Auth implementation | C G K X |
| business-logic-abuse | Race conditions, TOCTOU, double-spending, workflow bypass, idempotency, check-sequence abuse | Domain-aware deep audits (powers `/run-penetration-test --depth=deep`) | C G K X |
| advanced-attack-patterns | State desynchronization, cache poisoning, replay attacks, timing side channels | Architecture-level attack classes beyond baseline OWASP | C G K X |

### Testing -- Tests Generation (8 skills) -- `C` `G` `K` `X`

| Skill | Description | Languages | Platforms |
|-------|-------------|----------|-----------|
| test-structure | Testing infrastructure setup and scaffolding | Python, JS, TS, Java, C#, Go, C, C++ | C G K X |
| unit-tests | Unit test generation (FIRST principles, AAA) | Python, JS, TS, Java, C#, Go, C, C++ | C G K X |
| test-cases | Integration and E2E test scenarios | Python, JS, TS, Java, C#, Go, C, C++ | C G K X |
| mocks-fixtures | Mocks, stubs, fakes, data factories | Python, JS, TS, Java, C#, Go, C, C++ | C G K X |
| performance-testing | Load, stress, benchmark testing | Python, JS, TS, Java, C#, Go, C, C++ | C G K X |
| cicd-integration | Test automation in CI/CD pipelines | All | C G K X |
| code-coverage | Coverage analysis and gap identification | Python, JS, TS, Java, C#, Go, C, C++ | C G K X |
| mutation-testing | Test quality validation via mutation | Python, JS, TS, Java, C#, Go, C, C++ | C G K X |

### Testing -- Advanced Testing (17 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| edge-case-generator | Identify and test boundary conditions | Thorough test coverage | C G K X |
| flaky-test-detector | Find and fix non-deterministic tests | Test reliability | C G K X |
| integration-test-generator | Service boundary and API integration tests | Integration testing | C G K X |
| property-based-test-generator | Property-based / generative testing | Mathematical correctness | C G K X |
| fuzzing-input-generator | Security and reliability fuzzing inputs | Security testing | C G K X |
| metamorphic-test-generator | Metamorphic relation test cases | ML model testing | C G K X |
| directed-test-input-generator | Targeted inputs for specific code paths | Coverage-directed testing | C G K X |
| test-suite-prioritizer | Rank tests by risk and change impact | CI optimization | C G K X |
| e2e-testing-automation | Browser and system E2E automation | Full system validation | C G K X |
| generate-test-cases | Complete test case generation for any scenario | Comprehensive coverage | C G K X |
| setup-test-infrastructure | Test environment and framework configuration | Test infra setup | C G K X |
| unit-tests | Comprehensive unit test suites | Full unit coverage | C G K X |
| mocks-fixtures | Test doubles and fixture management | Test isolation | C G K X |
| performance-testing | Performance and load testing | Performance validation | C G K X |
| cicd-integration | CI/CD test pipeline configuration | Automated testing | C G K X |
| code-coverage | Coverage measurement and improvement | Coverage goals | C G K X |
| mutation-testing | Test suite quality measurement | Test quality | C G K X |

### Workflow (14 skills) -- `C` `G` `K` `X`

| Skill | Description | Primary Use Case | Platforms |
|-------|-------------|-----------------|-----------|
| code-commit-workflow | Complete commit workflow from staging to PR | Git workflow | C G K X |
| plan-before-code | Structured planning before implementation | Development planning | C G K X |
| debug-with-logs | Systematic debugging using structured logging | Bug investigation | C G K X |
| test-driven-development | TDD cycle: red-green-refactor | Quality development | C G K X |
| create-custom-command | Build new slash commands for Claude Code | Claude Code extension | C |
| filesystem-context-patterns | Efficient file and context management patterns | Context optimization | C G K X |
| documentation-consistency | Keep docs in sync with code changes | Documentation quality | C G K X |
| version-upgrade | Semantic versioning, changelog, release process | Release management | C G K X |
| devlog-generation | Generate structured development logs from git history | Development history | C G K X |
| conflict-analyzer | Resolve merge conflicts with context understanding | Git conflict resolution | C G K X |
| git-bisect-assistant | Use git bisect to find regression-introducing commits | Regression hunting | C G K X |
| release-notes-writer | User-facing release notes from commits/PRs | Release communication | C G K X |
| check-usage | Claude Code usage monitoring and model switching | Cost management | C |
| research-plan-implement | Structured research → plan → implement workflow | Complex feature development | C G K X |

---

## Coverage by Use Case

| Use Case | Skills Available | Bundle |
|----------|-----------------|--------|
| AI Agent Development | ai-agent-development, claude-agent-sdk, prompt-engineering, rag-implementation, multi-provider-ai, ai-billing-safeguards, tool-design, ai-output-evaluation, temporal-orchestration, cross-model-orchestrator | AI Engineer |
| Security Auditing | dependency-security-audit, exploitability-analyzer, cve-reachability-analyzer, security-patch-advisor, authentication-patterns, code-review-security, pre-commit-checklist | Security Specialist |
| Regulatory Compliance | gdpr-compliance, ccpa-compliance, soc2-compliance, iso27001-compliance, pci-dss-compliance, iso42001-ai-governance, nist-ai-rmf, ai-agent-governance, traceability-matrix-generator | Compliance Auditor |
| Infrastructure / DevOps | cicd-architect, cloud-architect, kubernetes-expert, terraform-specialist, containerization, ai-docker-orchestration, observability-setup, cd-pipeline-generator | DevOps Engineer |
| Testing & Quality | Full testing category (25 skills) | QA Engineer |
| Code Quality | cleanup-* (8), code-review-* (8), refactoring-expert, technical-debt-analyzer, dead-code-eliminator, code-smell-detector | Core Developer / Tech Lead |
| Documentation | add-strategic-comments, create-technical-docs, create-user-documentation, generate-api-docs, generate-docstrings, generate-sbom, generate-report | Any role |
| Debugging | bug-localization, bug-to-patch-generator, regression-root-cause-analyzer, bug-reproduction-test-generator, semantic-bug-detector, debug-with-logs, git-bisect-assistant | Bug Hunter |

---

## Coverage Gaps (Known)

The following capability areas are not yet covered by the catalog:

| Gap | Category | Priority | Notes |
|-----|----------|----------|-------|
| MCP server development | AI Development | P2 | Guide exists (`guides/reference/MCP_DEVELOPMENT_SERVERS.md`); dedicated skill planned |
| Docker AI orchestration | Infrastructure | P2 | `containerization` skill is generic; AI-workload patterns planned |
| Sample report outputs | Documentation | P2 | No example outputs for report-generating skills |
| Strict TypeScript tsconfig | Developer Experience | P3 | `typescript.md` template covers basics; strict config patterns planned |
| OpenAI SDK integration | AI Development | P3 | Currently Claude/Anthropic-focused; other SDK skills not planned |
| Business logic security testing | Security | N/A | Requires domain-specific pentest tooling (out of scope) |

---

*Last updated: 2026-03-11 | Source of truth: `data/skills.json` and `data/bundles.json`*
