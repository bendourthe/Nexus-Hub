# Claude Skills Catalog

**Complete listing of all skills with descriptions and metadata**

---

## Tests Generation Skills

### test-structure
**Path**: `tests-generation/test-structure/`
**Description**: Set up testing infrastructure including framework selection, directory organization, configuration files, and initial test scaffolding. Use when starting a new project, adding tests to an existing codebase, or restructuring test organization for Python, JavaScript, Java, C#, Go, C, or C++.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: HIGH

### unit-tests
**Path**: `tests-generation/unit-tests/`
**Description**: Generate comprehensive unit tests following FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely) and AAA pattern (Arrange-Act-Assert). Use when creating tests, improving test coverage, writing test suites, or implementing TDD.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: HIGH

### test-cases
**Path**: `tests-generation/test-cases/`
**Description**: Create integration and end-to-end test scenarios covering workflows, API interactions, and system boundaries. Use when testing component interactions, API endpoints, database operations, or full system flows.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: HIGH

### mocks-fixtures
**Path**: `tests-generation/mocks-fixtures/`
**Description**: Build test doubles (mocks, stubs, spies, fakes), data factories, and fixtures for test isolation. Use when tests need external dependency isolation, consistent test data, or complex setup scenarios.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: MEDIUM

### performance-testing
**Path**: `tests-generation/performance-testing/`
**Description**: Implement load testing, stress testing, benchmarking, and performance validation. Use when validating system performance, identifying bottlenecks, or establishing performance baselines.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: MEDIUM

### cicd-integration
**Path**: `tests-generation/cicd-integration/`
**Description**: Configure test automation in CI/CD pipelines with quality gates, parallel execution, and reporting. Use when setting up GitHub Actions, GitLab CI, Jenkins, or other CI/CD systems for automated testing.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: HIGH

### code-coverage
**Path**: `tests-generation/code-coverage/`
**Description**: Analyze test coverage, identify gaps, and implement strategies for achieving 80%+ coverage targets. Use when measuring test effectiveness, identifying untested code paths, or meeting coverage requirements.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: MEDIUM

### mutation-testing
**Path**: `tests-generation/mutation-testing/`
**Description**: Validate test quality through mutation testing to detect weak tests and reward hacking patterns. Use when verifying test suite effectiveness, improving test quality, or detecting false-positive tests.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: MEDIUM

---

## Code Review Skills

### context-analysis
**Path**: `code-review/context-analysis/`
**Description**: Establish comprehensive understanding of project structure, architecture, dependencies, and current state before conducting detailed code review. Use as the first phase of any code review or when onboarding to a new codebase.
**Languages**: Multi-language
**Priority**: HIGH

### code-quality
**Path**: `code-review/code-quality/`
**Description**: Evaluate code style, maintainability, complexity metrics, and adherence to best practices. Use for code quality assessment, technical debt identification, or maintainability improvement.
**Languages**: Multi-language
**Priority**: HIGH

### security-review
**Path**: `code-review/security-review/`
**Description**: Identify security vulnerabilities, OWASP Top 10 issues, supply chain risks, and compliance gaps. Use for security audits, penetration test preparation, or vulnerability assessment.
**Languages**: Multi-language
**Priority**: CRITICAL

### performance-review
**Path**: `code-review/performance-review/`
**Description**: Profile performance, detect bottlenecks, analyze resource usage, and recommend optimizations. Use when addressing performance issues, optimizing hot paths, or reducing resource consumption.
**Languages**: Multi-language
**Priority**: HIGH

### testing-review
**Path**: `code-review/testing-review/`
**Description**: Assess test coverage, test quality, testing strategy effectiveness, and identify coverage gaps. Use when evaluating test suites, improving test strategy, or preparing for releases.
**Languages**: Multi-language
**Priority**: HIGH

### final-report
**Path**: `code-review/final-report/`
**Description**: Consolidate all review findings into a prioritized report with severity classifications and actionable remediation plan. Use as the final phase of comprehensive code review.
**Languages**: Multi-language
**Priority**: HIGH

---

## Code Cleanup Skills

### python-cleanup
**Path**: `code-cleanup/python-cleanup/`
**Description**: Remove dead code, fix PEP 8 violations, add type hints, and modernize Python codebases. Use when cleaning up Python projects, removing unused imports, or upgrading legacy Python code.
**Language**: Python
**Priority**: MEDIUM

### javascript-cleanup
**Path**: `code-cleanup/javascript-cleanup/`
**Description**: Remove unused exports, fix ESLint issues, modernize to ES6+, and clean up JavaScript/TypeScript codebases. Use when cleaning up JS/TS projects or modernizing legacy JavaScript.
**Language**: JavaScript/TypeScript
**Priority**: MEDIUM

### java-cleanup
**Path**: `code-cleanup/java-cleanup/`
**Description**: Remove dead code, update deprecated APIs, apply modern Java patterns, and clean up Java codebases. Use when cleaning up Java projects or modernizing legacy Java code.
**Language**: Java
**Priority**: MEDIUM

### csharp-cleanup
**Path**: `code-cleanup/csharp-cleanup/`
**Description**: Modernize async patterns, optimize LINQ usage, update .NET APIs, and clean up C# codebases. Use when cleaning up C# projects or modernizing legacy .NET code.
**Language**: C#
**Priority**: MEDIUM

### go-cleanup
**Path**: `code-cleanup/go-cleanup/`
**Description**: Apply gofmt, remove unused packages, improve error handling, and clean up Go codebases. Use when cleaning up Go projects or applying Go best practices.
**Language**: Go
**Priority**: MEDIUM

### c-cleanup
**Path**: `code-cleanup/c-cleanup/`
**Description**: Fix memory leaks, apply MISRA guidelines, remove dead code, and clean up C codebases. Use when cleaning up C projects, embedded systems, or addressing memory safety.
**Language**: C
**Priority**: MEDIUM

### cpp-cleanup
**Path**: `code-cleanup/cpp-cleanup/`
**Description**: Modernize to C++17/20, apply RAII patterns, use smart pointers, and clean up C++ codebases. Use when cleaning up C++ projects or modernizing legacy C++ code.
**Language**: C++
**Priority**: MEDIUM

---

## Documentation Skills

### docstrings
**Path**: `documentation/docstrings/`
**Description**: Generate comprehensive function, class, and module docstrings following language conventions (JSDoc, PyDoc, JavaDoc, XML docs, godoc, Doxygen). Use when documenting APIs, adding inline documentation, or improving code discoverability.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: MEDIUM

### strategic-comments
**Path**: `documentation/strategic-comments/`
**Description**: Add high-value comments explaining complex logic, business rules, design decisions, and non-obvious implementations. Use when clarifying code intent, documenting workarounds, or explaining algorithms.
**Languages**: Python, JavaScript, Java, C#, Go, C, C++
**Priority**: MEDIUM

### user-documentation
**Path**: `documentation/user-documentation/`
**Description**: Create README files, installation guides, tutorials, quick starts, and user-facing documentation. Use when creating project documentation, onboarding guides, or user manuals.
**Languages**: Multi-language
**Priority**: HIGH

### technical-documentation
**Path**: `documentation/technical-documentation/`
**Description**: Generate architecture documentation, ADRs (Architecture Decision Records), design documents, and technical specifications. Use when documenting system design, architectural decisions, or technical workflows.
**Languages**: Multi-language
**Priority**: HIGH

### api-documentation
**Path**: `documentation/api-documentation/`
**Description**: Create OpenAPI/Swagger specifications, API reference documentation, endpoint descriptions, and usage examples. Use when documenting REST APIs, GraphQL schemas, or service interfaces.
**Languages**: Multi-language
**Priority**: HIGH

### sbom-generation
**Path**: `documentation/sbom-generation/`
**Description**: Generate Software Bill of Materials (SBOM) for compliance with NTIA, EU CRA, and other regulatory requirements. Use when preparing for audits, compliance reporting, or supply chain transparency.
**Languages**: Multi-language
**Priority**: HIGH

---

## Compliance Skills

### soc2-compliance
**Path**: `compliance/soc2-compliance/`
**Description**: Implement SOC 2 Type II controls covering Trust Services Criteria (Security, Availability, Confidentiality, Processing Integrity, Privacy). Use when preparing for SOC 2 audits, implementing controls, or documenting compliance.
**Framework**: SOC 2 Type II
**Priority**: HIGH

### iso27001-compliance
**Path**: `compliance/iso27001-compliance/`
**Description**: Implement ISO 27001:2022 Information Security Management System controls (114 controls across 14 domains). Use when establishing ISMS, preparing for ISO certification, or implementing security controls.
**Framework**: ISO 27001:2022
**Priority**: HIGH

### iso42001-ai-governance
**Path**: `compliance/iso42001-ai-governance/`
**Description**: Implement ISO 42001:2023 AI Management System requirements for responsible AI development and deployment. Use when governing AI systems, implementing AI ethics, or preparing for AI-specific audits.
**Framework**: ISO 42001:2023
**Priority**: HIGH

### nist-ai-rmf
**Path**: `compliance/nist-ai-rmf/`
**Description**: Implement NIST AI Risk Management Framework (Govern, Map, Measure, Manage) for AI system risk management. Use when deploying AI in US federal contexts or implementing AI risk controls.
**Framework**: NIST AI RMF 1.0
**Priority**: HIGH

### pci-dss-compliance
**Path**: `compliance/pci-dss-compliance/`
**Description**: Implement PCI-DSS v4.0 requirements for payment card data security. Use when handling payment card data, preparing for PCI audits, or securing payment systems.
**Framework**: PCI-DSS v4.0
**Priority**: CRITICAL

### gdpr-compliance
**Path**: `compliance/gdpr-compliance/`
**Description**: Implement GDPR requirements for EU data protection including data subject rights, consent management, and breach notification. Use when handling EU personal data or preparing for GDPR compliance.
**Framework**: GDPR
**Priority**: HIGH

### ccpa-compliance
**Path**: `compliance/ccpa-compliance/`
**Description**: Implement CCPA/CPRA requirements for California consumer privacy including opt-out rights and data disclosure. Use when handling California resident data or preparing for CCPA compliance.
**Framework**: CCPA/CPRA
**Priority**: MEDIUM

### ai-agent-governance
**Path**: `compliance/ai-agent-governance/`
**Description**: Implement the 4 Pillars Framework for AI agent governance (Lifecycle Management, Risk Management, Security, Observability). Use when deploying agentic AI systems, implementing AI guardrails, or establishing AI monitoring.
**Framework**: 4 Pillars Framework
**Priority**: CRITICAL

---

## Project Setup Skills

### init-python-project
**Path**: `project-setup/init-python-project/`
**Description**: Initialize a Python project with pyproject.toml, pytest configuration, virtual environment, and CI/CD setup. Use when starting new Python projects or standardizing project structure.
**Language**: Python
**Priority**: MEDIUM

### init-javascript-project
**Path**: `project-setup/init-javascript-project/`
**Description**: Initialize a JavaScript/TypeScript project with package.json, ESLint, Prettier, Jest, and CI/CD setup. Use when starting new JS/TS projects or standardizing project structure.
**Language**: JavaScript/TypeScript
**Priority**: MEDIUM

### init-java-project
**Path**: `project-setup/init-java-project/`
**Description**: Initialize a Java project with Maven or Gradle, JUnit 5, code coverage, and CI/CD setup. Use when starting new Java projects or standardizing project structure.
**Language**: Java
**Priority**: MEDIUM

### init-csharp-project
**Path**: `project-setup/init-csharp-project/`
**Description**: Initialize a C#/.NET project with .csproj configuration, xUnit, NuGet packages, and CI/CD setup. Use when starting new C# projects or standardizing project structure.
**Language**: C#
**Priority**: MEDIUM

---

## Workflow Skills

### plan-before-code
**Path**: `workflow/plan-before-code/`
**Description**: Apply structured planning methodology before writing code including requirements analysis, design decisions, and implementation strategy. Use before starting any significant development task.
**Languages**: Multi-language
**Priority**: CRITICAL

### test-driven-development
**Path**: `workflow/test-driven-development/`
**Description**: Implement Test-Driven Development (TDD) workflow with red-green-refactor cycle. Use when developing new features, fixing bugs, or improving code quality through tests-first approach.
**Languages**: Multi-language
**Priority**: CRITICAL

### code-commit-workflow
**Path**: `workflow/code-commit-workflow/`
**Description**: Follow structured Git commit workflow with conventional commits, meaningful messages, and proper staging. Use when committing code changes, preparing pull requests, or maintaining clean git history.
**Languages**: Multi-language
**Priority**: HIGH

### debug-with-logs
**Path**: `workflow/debug-with-logs/`
**Description**: Apply strategic debugging using structured logging, breakpoints, and systematic issue isolation. Use when debugging issues, investigating bugs, or adding diagnostic logging.
**Languages**: Multi-language
**Priority**: MEDIUM

### create-custom-command
**Path**: `workflow/create-custom-command/`
**Description**: Create custom Claude Code slash commands for repetitive tasks and team workflows. Use when automating common operations or standardizing team practices.
**Languages**: Multi-language
**Priority**: MEDIUM

---

## Security Skills

### dependency-security-audit
**Path**: `security/dependency-security-audit/`
**Description**: Scan dependencies for CVEs, vulnerabilities, and security issues using language-specific tools (pip-audit, npm audit, etc.). Use weekly or before releases to identify vulnerable dependencies.
**Languages**: Python, JavaScript, Java, C#, Go
**Priority**: HIGH

### pre-commit-checklist
**Path**: `security/pre-commit-checklist/`
**Description**: Validate code before committing including secrets detection, linting, formatting, and security checks. Use before every commit to prevent security issues and maintain code quality.
**Languages**: Multi-language
**Priority**: HIGH

### licensing-compliance
**Path**: `security/licensing-compliance/`
**Description**: Check dependency licenses for compliance with project requirements and legal constraints. Use monthly or when adding new dependencies to verify license compatibility.
**Languages**: Multi-language
**Priority**: MEDIUM

---

## Infrastructure Skills

### kubernetes-expert
**Path**: `infrastructure/kubernetes-expert/`
**Description**: Deep Kubernetes expertise for container orchestration, deployment patterns, and cluster management. Use when deploying to K8s, writing Helm charts, configuring RBAC, troubleshooting pods, or optimizing cluster resources.
**Technologies**: Kubernetes, Helm, kubectl
**Priority**: HIGH

### terraform-specialist
**Path**: `infrastructure/terraform-specialist/`
**Description**: Infrastructure as Code expertise with Terraform/OpenTofu for cloud provisioning. Use when writing Terraform modules, managing state, configuring multi-environment setups, or implementing IaC best practices for AWS, Azure, or GCP.
**Technologies**: Terraform, OpenTofu, HCL
**Priority**: HIGH

### cicd-architect
**Path**: `infrastructure/cicd-architect/`
**Description**: CI/CD pipeline expertise for automated build, test, and deployment workflows. Use when setting up GitHub Actions, GitLab CI, Jenkins, or other CI/CD systems, implementing deployment strategies, or optimizing pipeline performance.
**Technologies**: GitHub Actions, GitLab CI, Jenkins
**Priority**: HIGH

### cloud-architect
**Path**: `infrastructure/cloud-architect/`
**Description**: Multi-cloud architecture expertise for AWS, Azure, and GCP. Use when designing cloud infrastructure, implementing Well-Architected Framework principles, optimizing costs, or building highly available and secure cloud solutions.
**Technologies**: AWS, Azure, GCP
**Priority**: HIGH

---

## Orchestration Skills

### task-coordinator
**Path**: `orchestration/task-coordinator/`
**Description**: Coordinate complex multi-step tasks by breaking them down into manageable subtasks with dependency tracking. Use when implementing large features, coordinating parallel work streams, or managing complex workflows that span multiple files or components.
**Languages**: Multi-language
**Priority**: MEDIUM

### context-manager
**Path**: `orchestration/context-manager/`
**Description**: Manage and maintain context across large codebases and complex multi-file changes. Use when working on changes that span many files, navigating unfamiliar codebases, or synthesizing information from multiple sources to make informed decisions.
**Languages**: Multi-language
**Priority**: MEDIUM

### workflow-orchestrator
**Path**: `orchestration/workflow-orchestrator/`
**Description**: Design and execute end-to-end workflows by chaining multiple skills and managing quality gates between phases. Use for complete feature implementations, full testing cycles, comprehensive code reviews, or any multi-phase development process.
**Languages**: Multi-language
**Priority**: MEDIUM

---

## Developer Experience Skills

### refactoring-expert
**Path**: `developer-experience/refactoring-expert/`
**Description**: Safe code refactoring using proven patterns from Martin Fowler's catalog. Use when restructuring code, extracting methods/classes, simplifying conditionals, improving naming, or reducing technical debt without changing behavior.
**Languages**: Multi-language
**Priority**: MEDIUM

### legacy-modernizer
**Path**: `developer-experience/legacy-modernizer/`
**Description**: Modernize legacy codebases using proven migration strategies like Strangler Fig pattern. Use when upgrading frameworks, migrating to new architectures, replacing deprecated APIs, or incrementally modernizing old code without full rewrites.
**Languages**: Multi-language
**Priority**: MEDIUM

### dependency-manager
**Path**: `developer-experience/dependency-manager/`
**Description**: Manage and upgrade project dependencies safely. Use when upgrading packages, handling breaking changes, managing lock files, patching vulnerabilities, or auditing dependency health across your projects.
**Languages**: Multi-language
**Priority**: MEDIUM

---

## Language Specialist Skills

### rust-expert
**Path**: `language-specialists/rust-expert/`
**Description**: Deep Rust expertise for systems programming with ownership, borrowing, and lifetimes. Use when writing Rust code, understanding ownership errors, implementing traits, working with async/await, or optimizing performance-critical code.
**Language**: Rust
**Priority**: MEDIUM

### go-expert
**Path**: `language-specialists/go-expert/`
**Description**: Deep Go expertise for concurrent systems programming. Use when writing Go code, implementing goroutines and channels, designing interfaces, handling errors idiomatically, or optimizing Go applications for performance.
**Language**: Go
**Priority**: MEDIUM

### sql-expert
**Path**: `language-specialists/sql-expert/`
**Description**: Deep SQL expertise for query optimization and database design. Use when writing complex queries, optimizing slow queries, designing schemas, understanding execution plans, or working with PostgreSQL, MySQL, or SQL Server specific features.
**Languages**: SQL, PostgreSQL, MySQL, SQL Server
**Priority**: MEDIUM

---

## Summary Statistics

| Category | Count | Avg Priority |
|----------|-------|--------------|
| Tests Generation | 8 | HIGH |
| Code Review | 6 | HIGH |
| Code Cleanup | 7 | MEDIUM |
| Documentation | 6 | MEDIUM-HIGH |
| Compliance | 8 | HIGH |
| Project Setup | 4 | MEDIUM |
| Workflow | 5 | HIGH |
| Security | 3 | HIGH |
| Infrastructure | 4 | HIGH |
| Orchestration | 3 | MEDIUM |
| Developer Experience | 3 | MEDIUM |
| Language Specialists | 3 | MEDIUM |
| **Total** | **60** | **HIGH** |

---

## Version

- **Catalog Version**: 1.1.0
- **Last Updated**: January 2026
