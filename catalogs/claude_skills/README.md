# Claude Skills Collection

**Production-ready Claude Skills for software development, testing, compliance, and documentation**

---

## Overview

This directory contains a comprehensive collection of Claude Skills designed for use with:
- **Claude Code** (CLI) - Place in `.claude/skills/` in your project
- **Claude.ai** - Import as ZIP files via the Skills UI
- **Claude API** - Reference via Skills API

These skills mirror and extend the templates in [`templates/`](../../templates/), converted to the official Claude Skills format for automated discovery and activation.

---

## Quick Start

### Using with Claude Code (Recommended)

1. **Copy skill folder to your project:**
   ```bash
   # Copy a single skill
   cp -r catalogs/claude_skills/tests-generation/unit-tests/ .claude/skills/

   # Or copy an entire category
   cp -r catalogs/claude_skills/tests-generation/ .claude/skills/
   ```

2. **Use the skill:**
   ```
   "Generate unit tests for my Python authentication module"
   ```
   Claude will automatically discover and use the appropriate skill.

### Using with Claude.ai

1. **ZIP a skill folder:**
   ```bash
   cd catalogs/claude_skills/tests-generation
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

### [Tests Generation](tests-generation/) (8 skills)

Complete 8-phase testing methodology from infrastructure to mutation testing.

| Skill | Description | Languages |
|-------|-------------|-----------|
| `test-structure` | Set up test framework, directories, configuration | All 7 |
| `unit-tests` | FIRST principles, AAA pattern, isolation | All 7 |
| `test-cases` | Integration and E2E test scenarios | All 7 |
| `mocks-fixtures` | Test doubles, factories, fixtures | All 7 |
| `performance-testing` | Load, stress, benchmark testing | All 7 |
| `cicd-integration` | Test automation, quality gates | All 7 |
| `code-coverage` | Coverage analysis, 80%+ target | All 7 |
| `mutation-testing` | Test quality validation | All 7 |

### [Code Review](code-review/) (6 skills)

Systematic 6-phase code review methodology.

| Skill | Description | Time |
|-------|-------------|------|
| `context-analysis` | Project structure, architecture, dependencies | 2-3 hrs |
| `code-quality` | Style, maintainability, complexity | 2-3 hrs |
| `security-review` | Vulnerabilities, OWASP Top 10 | 2-3 hrs |
| `performance-review` | Bottlenecks, optimization | 2-3 hrs |
| `testing-review` | Coverage, test quality | 2 hrs |
| `final-report` | Consolidated findings, action plan | 1 hr |

### [Code Cleanup](code-cleanup/) (7 skills)

Language-specific dead code removal and modernization.

| Skill | Language | Focus Areas |
|-------|----------|-------------|
| `python-cleanup` | Python | PEP 8, type hints, dead code |
| `javascript-cleanup` | JavaScript/TypeScript | ESLint, unused exports |
| `java-cleanup` | Java | Dead code, deprecated APIs |
| `csharp-cleanup` | C# | Async patterns, LINQ |
| `go-cleanup` | Go | gofmt, error handling |
| `c-cleanup` | C | Memory leaks, MISRA |
| `cpp-cleanup` | C++ | Modern C++, RAII |

### [Documentation](documentation/) (6 skills)

Comprehensive documentation generation.

| Skill | Description | Output |
|-------|-------------|--------|
| `docstrings` | Function/class documentation | JSDoc, PyDoc, etc. |
| `strategic-comments` | High-value code comments | Inline comments |
| `user-documentation` | README, tutorials, guides | Markdown docs |
| `technical-documentation` | Architecture, ADRs | Design docs |
| `api-documentation` | OpenAPI, endpoints | API reference |
| `sbom-generation` | Software Bill of Materials | SBOM files |

### [Compliance](compliance/) (8 skills)

Enterprise compliance frameworks and AI governance.

| Skill | Framework | Use Case |
|-------|-----------|----------|
| `soc2-compliance` | SOC 2 Type II | Enterprise SaaS |
| `iso27001-compliance` | ISO 27001:2022 | Information security |
| `iso42001-ai-governance` | ISO 42001:2023 | AI management |
| `nist-ai-rmf` | NIST AI RMF | US federal AI |
| `pci-dss-compliance` | PCI-DSS v4.0 | Payment processing |
| `gdpr-compliance` | GDPR | EU data protection |
| `ccpa-compliance` | CCPA | California privacy |
| `ai-agent-governance` | 4 Pillars Framework | Agentic AI |

### [Project Setup](project-setup/) (4 skills)

Project initialization and configuration.

| Skill | Language | Creates |
|-------|----------|---------|
| `init-python-project` | Python | pyproject.toml, tests, CI |
| `init-javascript-project` | JavaScript/TS | package.json, ESLint, Jest |
| `init-java-project` | Java | Maven/Gradle, JUnit |
| `init-csharp-project` | C# | .csproj, xUnit, NuGet |

### [Workflow](workflow/) (5 skills)

Development process and methodology.

| Skill | Description | Priority |
|-------|-------------|----------|
| `plan-before-code` | Planning methodology | CRITICAL |
| `test-driven-development` | TDD workflow | CRITICAL |
| `code-commit-workflow` | Git commit process | HIGH |
| `debug-with-logs` | Strategic debugging | MEDIUM |
| `create-custom-command` | Slash command creation | MEDIUM |

### [Security](security/) (3 skills)

Security-focused development practices.

| Skill | Description | Frequency |
|-------|-------------|-----------|
| `dependency-security-audit` | CVE scanning, vulnerabilities | Weekly |
| `pre-commit-checklist` | Pre-commit validation | Every commit |
| `licensing-compliance` | License checking | Monthly |

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

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Skills | 47 |
| Categories | 8 |
| Languages | 7 |
| Avg. Lines/Skill | 400-800 |

### By Category

| Category | Skills | Priority |
|----------|--------|----------|
| Tests Generation | 8 | HIGH |
| Code Review | 6 | HIGH |
| Code Cleanup | 7 | MEDIUM |
| Documentation | 6 | MEDIUM |
| Compliance | 8 | HIGH |
| Project Setup | 4 | MEDIUM |
| Workflow | 5 | CRITICAL/HIGH |
| Security | 3 | HIGH |

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
- [Source Templates](../../templates/)
- [Language Templates](../../templates/ai_instructions/agentic_systems/claude_code/)
- [Guides](../../guides/)

---

## Version

- **Collection Version**: 1.0.0
- **Last Updated**: December 2025
- **Source**: AI Templates v0.3.x
- **Author**: Benjamin Dourthe

---

## License

These skills are provided under the same license as the parent AI Templates repository. See [LICENSE](../../LICENSE) for details.
