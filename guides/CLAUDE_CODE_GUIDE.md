# Claude Code Guide

**Complete guide for autonomous development with Claude Code**

[← Back to Main](../README.md)

---

## Table of Contents

- [Introduction](#introduction)
- [Part 1: Setting Up CLAUDE.md](#part-1-setting-up-claudemd)
- [Part 2: Claude Code Skills](#part-2-claude-code-skills)
- [Part 3: Using Templates with Claude Code](#part-3-using-templates-with-claude-code)
- [Part 4: Generate Code Documentation](#part-4-generate-code-documentation)
- [Part 5: Generate Tests](#part-5-generate-tests)
- [Part 6: Code Review](#part-6-code-review)
- [Part 7: Compliance & Governance](#part-7-compliance--governance)
- [Part 8: Codebase Cleanup](#part-8-codebase-cleanup)
- [Complete Autonomous Workflow Example](#complete-autonomous-workflow-example)
- [Getting Started Checklist](#getting-started-checklist)
- [Additional Resources](#additional-resources)

---

<a name="introduction"></a>
## Introduction

This guide shows you how to use Claude Code—an autonomous AI coding agent—with the AI Templates repository for maximum development productivity. Unlike manual coding assistants (GitHub Copilot, Cursor), Claude Code can execute multi-step workflows autonomously, making complex decisions and performing tasks end-to-end.

**What Makes Claude Code Different:**
- **Autonomous Execution**: Handles multi-phase workflows without constant supervision

- **Tool Integration**: Directly executes bash commands, reads/writes files, runs tests

- **Decision Making**: Analyzes results and decides next steps automatically

- **Skills System**: 48+ specialized capabilities for common development tasks

- **Multi-Step Planning**: Breaks down complex tasks and executes them systematically

**Who This Is For:**
- Developers wanting autonomous code generation and refactoring

- Teams looking to accelerate development with AI agents

- Projects requiring comprehensive testing, documentation, or reviews

- Engineers building with Claude Code's Agent SDK

**Time Investment:**
- Initial setup: 15-30 minutes

- Per-template usage: Autonomous execution (minimal supervision needed)

---

<a name="part-1-setting-up-claudemd"></a>
## Part 1: Setting Up CLAUDE.md

### Overview

Claude Code reads instructions from a `CLAUDE.md` file (or `.claude/CLAUDE.md`) in your project root. This file tells Claude about your project's architecture, coding standards, testing requirements, and development workflow.

**Why CLAUDE.md Matters:**
- Claude makes better decisions with project context

- Autonomous operations follow your standards automatically

- Reduces need for clarifications during execution

- Enables truly autonomous multi-step workflows

### 1.1 What to Include

Effective CLAUDE.md files should contain:

**1. Project Overview**
- Project name, description, and purpose

- Technology stack and frameworks

- Architecture pattern (microservices, monolith, etc.)

- Key dependencies

**2. Project Architecture**
- Directory structure and organization

- Module/package layout

- Configuration file locations

- Data flow and component relationships

**3. Coding Standards**
- Code style and formatting (Black, ESLint, etc.)

- Import organization rules

- Naming conventions

- Documentation requirements (docstring format)

- Type hints/annotations policy

**4. Testing Requirements**
- Testing framework (pytest, Jest, JUnit, etc.)

- Test file organization

- Coverage requirements (typically 80%+)

- Test patterns (AAA, FIRST principles)

- Mocking strategies

**5. Development Workflow**
- Branch naming conventions

- Commit message format

- Pull request process

- CI/CD pipeline expectations

- Code review guidelines

**6. Command Reference**
- Virtual environment setup

- Dependency installation

- Running tests

- Building/deploying

- Common development tasks

**7. Quality Gates**
- Linting and formatting tools

- Static analysis requirements

- Security scanning tools

- Performance benchmarks

- Documentation completeness

### 1.2 Structure Guidelines

**Recommended CLAUDE.md Structure:**

```markdown
# [Project Name] - Development Instructions

## Quick Start for Common Tasks
- Bug Fix: Sections X, Y

- New Feature: Sections A-D

- Refactoring: Sections C, F

## 1. General Behavior
- Core principles

- Clarification protocol

- Teaching approach

- Quality assurance

## 2. Project Architecture
- Directory structure

- Module organization

- Data models

- External integrations

## 3. Code Standards
- Formatting rules

- Import organization

- Naming conventions

- Function design

## 4. Documentation Standards
- Docstring templates

- README structure

- CHANGELOG format

- DEVLOG structure

## 5. Testing Framework
- Test structure

- Test implementation

- Test output format

- Running tests

## 6. Development Workflow
- Task breakdown

- Git practices

- Command preferences

- Version control

## 7. Quality Checklist
- Before delivering code

- Before delivering project
```

### 1.3 Token Considerations

Claude Code can handle larger context than chat-based assistants:

| Context Type | Token Limit | Recommended |
|--------------|-------------|-------------|
| CLAUDE.md (Comprehensive) | 40,000 | For complex projects |
| CLAUDE.md (Condensed) | 20,000 | For simple projects |
| Skills (per skill) | 5,000-10,000 | Specialized tasks |
| Total Project Context | 200,000+ | Full codebase visibility |

**Comprehensive (40k tokens):**
- Full examples and detailed explanations

- Multiple code samples

- Complete templates

- Best for: Production codebases, team projects

**Condensed (20k tokens):**
- Essential rules and patterns

- Minimal examples

- Reference format

- Best for: Personal projects, prototypes

### 1.4 Available Templates

Pre-built CLAUDE.md templates for all supported languages:

**Location:** `templates/ai_instructions/agentic_systems/claude_code/`

**Available Templates:**
- [Python](../templates/ai_instructions/agentic_systems/claude_code/python/) - Modular skills-based template

- [JavaScript/TypeScript](../templates/ai_instructions/agentic_systems/claude_code/javascript/) - Full stack, Node.js

- [Java](../templates/ai_instructions/agentic_systems/claude_code/java/) - Enterprise, Spring Boot

- [C#](../templates/ai_instructions/agentic_systems/claude_code/csharp/) - .NET Core, ASP.NET

- [Go](../templates/ai_instructions/agentic_systems/claude_code/go/) - Cloud-native, microservices

- [C](../templates/ai_instructions/agentic_systems/claude_code/c/) - Embedded, firmware

- [C++](../templates/ai_instructions/agentic_systems/claude_code/cpp/) - Modern C++17/20

**Setup Steps:**

1. **Copy template to project:**
   ```bash
   cp -r templates/ai_instructions/agentic_systems/claude_code/python/* your-project/
   ```

2. **Customize for your project:**
   - Update project name and description

   - Modify directory structure if different

   - Add project-specific conventions

   - Include domain knowledge

   - Document custom commands

3. **Commit to version control:**
   ```bash
   git add CLAUDE.md
   git commit -m "chore: Add Claude Code configuration"
   ```

### 1.5 Best Practices

✅ **Do:**
- Keep CLAUDE.md up-to-date with project evolution

- Version control the file (track changes)

- Document project-specific quirks and gotchas

- Include concrete examples from your codebase

- Reference actual file paths and locations

- Test instructions with Claude Code

❌ **Avoid:**
- Vague or ambiguous instructions

- Outdated patterns or deprecated practices

- Conflicting guidelines

- Copy-pasting without customization

- Overly verbose (respect token limits)

- Including secrets or credentials

**Maintenance:**
- Review CLAUDE.md quarterly

- Update when architecture changes

- Revise when adopting new tools/frameworks

- Gather team feedback on clarity

- Document new patterns as they emerge

---

<a name="part-2-claude-code-skills"></a>
## Part 2: Claude Code Skills

### 2.1 What are Skills?

Claude Code Skills are specialized workflows packaged as markdown files that provide task-specific expertise. Think of them as "superpowers" that Claude can activate on-demand.

**Key Characteristics:**
- **Token-Efficient**: Only brief description loaded initially, full details on-demand

- **Autonomous**: Claude executes the skill end-to-end without supervision

- **Reusable**: Use same skill across multiple projects

- **Composable**: Combine skills for complex workflows

- **Specialized**: Each skill focuses on one specific task domain

**Skills vs CLAUDE.md:**
- **CLAUDE.md**: General project context and coding standards

- **Skills**: Specific task workflows (e.g., "generate tests", "review security")

### 2.2 Installing Skills

Skills are installed in your project's `.claude/skills/` directory.

**Method 1: Manual Installation**
```bash
# Create skills directory
mkdir -p .claude/skills

# Copy skill from catalogs
cp -r catalogs/claude_skills/code-review/code-review-security .claude/skills/

# Claude Code automatically detects it
```

**Method 2: Installation Script (if available)**
```bash
# Install by priority
python tools/install_skill.py --priority CRITICAL

# Install by category
python tools/install_skill.py --category "Code Review"

# Install specific skill
python tools/install_skill.py --skill generate-docstrings

# List available skills
python tools/install_skill.py --list
```

**Commit Skills to Git:**
```bash
git add .claude/skills/
git commit -m "chore: Add Claude Code skills"
```

Your team members get the same skills when they clone!

### 2.3 Using Skills

**Direct Invocation:**
```
"Use the code-review-security skill to analyze the authentication module"

"Apply the cleanup-python skill to remove dead code"

"Execute the generate-docstrings skill for all public APIs"
```

**Skill Composition:**
```
"Use plan-before-code skill to design the feature, then use test-driven-development skill to implement it"

"Run code-review-context-analysis, then code-review-security, then code-review-final-report"
```

**Autonomous Decision:**
Claude Code may automatically select appropriate skills based on context:
```
User: "I need comprehensive testing for this module"
Claude: "I'll use the setup-test-infrastructure skill followed by generate-test-cases skill..."
```

### 2.4 Available Skills (48 Total)

#### System Configuration (7 skills)
- **setup-python-system-prompt** - Configure Python development environment

- **setup-javascript-system-prompt** - Configure JavaScript/TypeScript environment

- **setup-java-system-prompt** - Configure Java development environment

- **setup-csharp-system-prompt** - Configure C# development environment

- **setup-go-system-prompt** - Configure Go development environment

- **setup-c-system-prompt** - Configure C development environment

- **setup-cpp-system-prompt** - Configure C++ development environment

#### Code Review (6 skills)
- **code-review-context-analysis** - Understand project structure and architecture

- **code-review-quality** - Evaluate maintainability and best practices

- **code-review-security** - Identify OWASP Top 10 vulnerabilities

- **code-review-performance** - Detect bottlenecks and optimization opportunities

- **code-review-testing** - Assess test coverage and quality

- **code-review-final-report** - Generate consolidated severity-classified report

#### Code Cleanup (7 skills)
- **cleanup-python** - Remove dead code, modernize Python idioms

- **cleanup-javascript** - Clean unused imports, modernize to ES6+

- **cleanup-java** - Remove unused code, apply streams/lambdas

- **cleanup-csharp** - Clean usings, apply modern C# features

- **cleanup-go** - Apply idiomatic Go patterns

- **cleanup-c** - Detect memory leaks, apply MISRA-C/CERT-C

- **cleanup-cpp** - Modernize to C++17/20, apply RAII

#### Documentation (6 skills)
- **generate-docstrings** - Comprehensive docstrings for public interfaces

- **add-strategic-comments** - Strategic comments explaining complex logic

- **create-user-documentation** - README, installation guides, tutorials

- **create-technical-docs** - Architecture, ADRs, design decisions

- **generate-api-docs** - Complete API reference documentation

- **generate-sbom** - Software Bill of Materials for compliance

#### Test Development (6 skills)
- **setup-test-infrastructure** - Establish test frameworks and structure

- **generate-test-cases** - Create unit, integration, and e2e tests

- **create-mocks-fixtures** - Implement mocking strategies

- **performance-testing** - Create load tests, stress tests, benchmarks

- **setup-ci-cd-testing** - Integrate tests into CI/CD pipelines

- **analyze-code-coverage** - Achieve 80%+ coverage target

#### Workflow (3 skills)
- **plan-before-code** (CRITICAL) - Design before implementing

- **test-driven-development** (CRITICAL) - TDD workflow

- **refactor-safely** (CRITICAL) - Safe refactoring with tests

**Full catalog:** [catalogs/claude_skills/](../catalogs/claude_skills/)

### 2.5 Skill Categories

Skills are organized by focus area:

| Category | Skills | Use Case |
|----------|--------|----------|
| **Workflow** | 3 CRITICAL | Essential development patterns |
| **System Configuration** | 7 | Project-specific setup |
| **Code Review** | 6 | Quality, security, performance analysis |
| **Code Cleanup** | 7 | Technical debt reduction |
| **Documentation** | 6 | API docs, README, SBOM |
| **Testing** | 6 | Test generation and coverage |

**Recommended Installation Order:**
1. **Workflow skills** (CRITICAL) - Foundation
2. **System configuration** for your language
3. **Code review** skills for quality assurance
4. **Documentation** or **Testing** based on immediate needs
5. **Code cleanup** for maintenance

---

<a name="part-3-using-templates-with-claude-code"></a>
## Part 3: Using Templates with Claude Code

### 3.1 Template Integration

Claude Code uses templates from this repository autonomously:

**How It Works:**
1. **You provide task:** "Generate comprehensive tests for this module"
2. **Claude selects template:** Chooses appropriate phase from tests_generation/
3. **Claude executes autonomously:** Reads code, generates tests, runs verification
4. **Claude reports results:** Shows test coverage, identifies gaps, suggests improvements

**Autonomous vs Manual:**
- **Manual (Copilot/ChatGPT):** You copy template prompt, paste, review output, iterate

- **Autonomous (Claude Code):** Claude reads template, executes workflow, verifies quality, reports findings

### 3.2 Autonomous Workflows

Claude Code handles multi-step processes automatically:

**Example: Generate Documentation**
```
User: "Document this entire codebase comprehensively"

Claude executes autonomously:
1. Reads templates/documentation_generation/ templates
2. Scans codebase to understand structure
3. Generates docstrings for all public functions
4. Adds strategic comments to complex logic
5. Creates README with installation instructions
6. Generates API documentation
7. Creates SBOM for dependencies
8. Verifies all documentation is consistent
9. Commits changes with descriptive message

Reports: "Comprehensive documentation complete. Added 847 docstrings, README, API docs, and SBOM."
```

**Example: Complete Code Review**
```
User: "Perform comprehensive security and quality review"

Claude executes autonomously:
1. Phase 1: Analyzes project context
2. Phase 2: Evaluates code quality
3. Phase 3: Performs security scan (OWASP Top 10)
4. Phase 4: Identifies performance bottlenecks
5. Phase 5: Assesses test coverage
6. Phase 6: Generates final consolidated report
7. Creates GitHub issues for CRITICAL/HIGH findings
8. Prioritizes remediation roadmap

Reports: "Review complete. Found 1 CRITICAL, 5 HIGH, 12 MEDIUM, 18 LOW issues. Remediation plan created."
```

### 3.3 Multi-Step Decision Trees

Claude Code follows decision trees autonomously:

**Example: Test Generation Decision Tree**
```
Claude's autonomous decisions:
1. Check if test framework exists
   - No → Execute Phase 1 (Test Structure)

   - Yes → Skip to Phase 2

2. Generate unit tests (Phase 2)
   - Verify tests pass

   - Check coverage

3. Coverage < 80%?
   - Yes → Execute Phase 6 (Coverage Analysis)

   - No → Continue

4. Identify untested modules
   - Generate additional tests

   - Re-run coverage

5. Coverage ≥ 80%?
   - Yes → Execute Phase 7 (CI/CD Integration)

   - No → Repeat step 4

6. Setup CI/CD pipeline
   - Create .github/workflows/test.yml

   - Verify pipeline runs successfully

7. Execute Phase 8 (Mutation Testing)
   - Run mutmut/Stryker

   - Report mutation score

Result: Complete test suite with 82% coverage, CI/CD integrated, mutation score 85%
```

### 3.4 Best Practices

✅ **When to Intervene:**
- Claude asks clarifying questions (ambiguous requirements)

- Critical decisions affect architecture

- Security-sensitive changes

- Production deployment steps

✅ **When to Let Claude Work:**
- Multi-phase template execution

- Test generation and verification

- Documentation generation

- Code cleanup and refactoring

- Non-destructive analysis (reviews)

✅ **Verification Checkpoints:**
- Review final results after autonomous execution

- Run tests to verify no regressions

- Check git diff for unintended changes

- Validate quality metrics (coverage, mutation score)

✅ **Iterative Refinement:**
```
"The generated tests look good, but I need additional edge case coverage for the authentication module"

"Documentation is comprehensive, but add more examples for the payment API"

"Code cleanup removed too much - restore the user_preferences module"
```

**Claude Code will autonomously refine based on feedback**

---

<a name="part-4-generate-code-documentation"></a>
## Part 4: Generate Code Documentation

### 4.1 Available Templates (Same as CODING_ASSISTANT_GUIDE)

Six documentation types, fully supported by Claude Code autonomous execution:

1. **Docstrings** - Function/class-level documentation
2. **Comments** - Strategic inline explanations
3. **User Documentation** - README, installation guides, tutorials
4. **Technical Documentation** - Architecture, ADRs, design decisions
5. **API Documentation** - Complete API reference
6. **SBOM** - Software Bill of Materials for compliance

**Templates:** [templates/documentation_generation/](../templates/documentation_generation/)

### 4.2 Recommended Order with Autonomous Execution

**Claude Code Autonomous Workflow:**

**Phase 1: Code-Level Documentation (1-2 hours autonomous)**
```
User: "Generate comprehensive code-level documentation"

Claude autonomously:
1. Scans all source files
2. Identifies public functions/classes
3. Generates docstrings following language conventions
4. Adds strategic comments to complex logic
5. Verifies docstring format correctness
6. Commits changes

Time: 1-2 hours (vs 2-4 hours manual)
```

**Phase 2: User-Facing Documentation (1-2 hours autonomous)**
```
User: "Create professional user documentation"

Claude autonomously:
1. Analyzes project structure
2. Generates README with:
   - Project description

   - Installation instructions

   - Usage examples

   - Troubleshooting
3. Creates quick start guide
4. Verifies all examples work
5. Commits documentation

Time: 1-2 hours (vs 3-4 hours manual)
```

**Phase 3: Developer Documentation (2-4 hours autonomous)**
```
User: "Document architecture and API"

Claude autonomously:
1. Analyzes codebase architecture
2. Generates architecture documentation
3. Creates design decision records (ADRs)
4. Generates API documentation with examples
5. Verifies all endpoints documented
6. Commits documentation

Time: 2-4 hours (vs 4-8 hours manual)
```

**Phase 4: Compliance (30 min - 1 hour autonomous)**
```
User: "Generate SBOM for compliance"

Claude autonomously:
1. Scans dependencies
2. Generates SPDX/CycloneDX format
3. Includes licenses and versions
4. Checks for known vulnerabilities
5. Exports in multiple formats
6. Commits SBOM

Time: 30 min - 1 hour (vs 2-3 hours manual)
```

### 4.3 What to Expect (Autonomous Execution)

#### Automated Generation

**Claude Code handles:**
- Reading entire codebase

- Identifying documentation gaps

- Generating appropriate documentation

- Following language-specific conventions

- Verifying consistency across files

- Running quality checks

**Autonomous Quality Checks:**
- Docstrings follow format (Google/NumPy/JSDoc/JavaDoc)

- All public interfaces documented

- Examples are syntactically correct

- Links in documentation are valid

- Cross-references work correctly

- No placeholder text remains

**Time Comparison:**

| Task | Manual | Autonomous (Claude Code) |
|------|--------|--------------------------|
| Docstrings | 2-3 hours | 30-60 min |
| Comments | 1-2 hours | 20-30 min |
| User Docs | 3-4 hours | 1-2 hours |
| Technical Docs | 4-6 hours | 2-3 hours |
| API Docs | 4-8 hours | 2-4 hours |
| SBOM | 2-3 hours | 30 min - 1 hour |

### 4.4 Verification Steps (Claude Code + Manual)

**Claude Code's Self-Verification:**
1. ✅ Runs syntax check on generated documentation
2. ✅ Validates code examples execute correctly
3. ✅ Checks docstring format compliance
4. ✅ Verifies cross-references and links
5. ✅ Ensures no placeholder text
6. ✅ Tests API documentation examples

**Your Manual Review:**
- [ ] Technical accuracy (Claude can't verify domain logic)

- [ ] Examples reflect actual use cases

- [ ] Tone and style match project voice

- [ ] Security-sensitive info not exposed

- [ ] Confidential details properly redacted

**Iterative Refinement:**
```
"Documentation looks great, but add more examples for the payment processing API"

"The README needs a troubleshooting section for common Docker issues"

"API docs should include authentication examples for all endpoints"
```

Claude Code will autonomously refine based on specific feedback.

---

<a name="part-5-generate-tests"></a>
## Part 5: Generate Tests

### 4.1 8-Phase Testing Methodology with Claude Code Automation

Claude Code executes the 8-phase testing methodology autonomously:

| Phase | Claude Code Automation | Time Saved |
|-------|------------------------|------------|
| **1. Test Structure** | Fully autonomous setup | 50% faster |
| **2. Unit Tests** | Auto-generates 20-30 tests/module | 60% faster |
| **3. Test Cases** | Auto-generates integration tests | 50% faster |
| **4. Mocks & Fixtures** | Auto-creates test doubles | 60% faster |
| **5. Performance Testing** | Auto-generates benchmarks | 70% faster |
| **6. Code Coverage** | Auto-analyzes gaps, generates tests | 80% faster |
| **7. CI/CD Integration** | Auto-creates pipeline configs | 70% faster |
| **8. Validation** | Auto-runs mutation testing | 50% faster |

**Total Time:** 10-20 hours (vs 25-43 hours manual)

### 5.2 Template Usage (Autonomous Phase Execution)

**Scenario 1: New Project (No Tests) - Fully Autonomous**
```
User: "Set up complete testing infrastructure and generate comprehensive tests"

Claude executes autonomously:
1. Phase 1: Creates test directory structure, installs pytest/Jest/JUnit
2. Phase 2: Generates unit tests for all modules (FIRST principles, AAA pattern)
3. Phase 3: Generates integration tests for workflows
4. Phase 4: Creates mocks for external dependencies
5. Phase 6: Runs coverage analysis (target: 80%+)
6. Generates additional tests for uncovered code
7. Phase 7: Creates .github/workflows/test.yml CI/CD pipeline
8. Phase 8: Runs mutation testing, reports quality score
9. Commits all tests with descriptive messages

Reports: "Complete test suite generated. 147 tests, 82% coverage, 85% mutation score, CI/CD configured."

Time: 10-15 hours autonomous (vs 25-30 hours manual)
```

**Scenario 2: Existing Project - Autonomous Gap Filling**
```
User: "Improve test coverage to 80%+"

Claude executes autonomously:
1. Phase 6: Analyzes current coverage (finds: 58%)
2. Identifies untested modules and functions
3. Phase 2: Generates unit tests for gaps
4. Re-runs coverage (now: 76%)
5. Identifies remaining gaps (error handling paths)
6. Generates additional tests
7. Re-runs coverage (now: 82%)
8. Phase 7: Ensures CI enforces 80% threshold
9. Phase 8: Validates test quality via mutation testing

Reports: "Coverage improved from 58% to 82%. Added 43 tests covering previously untested modules."

Time: 4-6 hours autonomous (vs 10-15 hours manual)
```

### 5.3 Expected Outcomes (Autonomous Test Suite)

**Quality Metrics (Autonomously Verified):**
- ✅ FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)

- ✅ AAA pattern (Arrange-Act-Assert)

- ✅ 80%+ code coverage

- ✅ >80% mutation score

- ✅ <5 minutes total test execution

- ✅ No flaky tests (verified via multiple runs)

**Autonomous Anti-Pattern Detection:**
Claude Code automatically avoids:
- ❌ Test interdependence

- ❌ Hidden dependencies

- ❌ Magic numbers

- ❌ Over-mocking

- ❌ Assertion roulette

- ❌ Test duplication

**Comprehensive Test Suite:**
- Unit tests for all public interfaces

- Integration tests for workflows

- Mocks for external dependencies

- Performance benchmarks

- CI/CD automation

- Mutation testing validation

### 5.4 Verification (Automated Test Runs)

**Claude Code Automatically:**
1. ✅ Runs generated tests to verify they pass
2. ✅ Measures code coverage
3. ✅ Runs multiple times to detect flakiness
4. ✅ Executes mutation testing
5. ✅ Verifies CI/CD pipeline works
6. ✅ Generates coverage reports

**Your Manual Verification:**
- [ ] Review test logic for correctness

- [ ] Verify edge cases are appropriate

- [ ] Confirm mocks represent reality

- [ ] Check performance benchmarks are realistic

**Autonomous Reporting:**
```
Test Suite Summary:
- Total Tests: 147

- Pass Rate: 100%

- Coverage: 82%

- Mutation Score: 85%

- Execution Time: 3.2s

- Flakiness: 0%

- CI/CD: Configured and passing

Recommendations:
- Consider adding property-based tests for data validation

- Performance tests could benefit from load testing under concurrent users
```

---

<a name="part-6-code-review"></a>
## Part 6: Code Review

### 6.1 6-Phase Review with Autonomous Analysis

Claude Code executes the complete 6-phase methodology autonomously:

| Phase | Claude Code Automation | Time Saved |
|-------|------------------------|------------|
| **1. Context Analysis** | Fully autonomous mapping | 40% faster |
| **2. Code Quality** | Auto-detects issues by severity | 50% faster |
| **3. Security Review** | Auto-scans OWASP Top 10 | 60% faster |
| **4. Performance Review** | Auto-profiles bottlenecks | 70% faster |
| **5. Testing Review** | Auto-assesses coverage gaps | 60% faster |
| **6. Final Report** | Auto-generates consolidated report | 80% faster |

**Total Time:** 6-10 hours (vs 10-15 hours manual)

### 6.2 Template Usage (Parallel Phase Execution Where Possible)

**Comprehensive Review - Autonomous Execution:**
```
User: "Perform comprehensive code review with security focus"

Claude executes autonomously:
1. Phase 1: Context Analysis (2 hours)
   - Maps project architecture

   - Identifies technology stack

   - Documents dependencies

   - Locates key modules

2. Phase 2: Code Quality (2 hours)
   - Analyzes cyclomatic complexity

   - Detects code smells

   - Identifies refactoring opportunities

   - Categorizes by severity

3. Phases 3 & 4: Security + Performance (parallel, 3 hours total)
   Phase 3 (Security):
   - Scans for SQL injection

   - Checks for XSS vulnerabilities

   - Validates input sanitization

   - Detects hardcoded secrets

   - Maps auth/authz issues

   Phase 4 (Performance):
   - Profiles algorithmic complexity

   - Detects N+1 queries

   - Identifies memory leaks

   - Finds caching opportunities

4. Phase 5: Testing Review (1.5 hours)
   - Measures coverage

   - Evaluates test quality

   - Identifies missing scenarios

5. Phase 6: Final Report (30 min)
   - Consolidates all findings

   - Classifies by severity (CRITICAL/HIGH/MEDIUM/LOW)

   - Generates remediation roadmap

   - Estimates fix times

   - Creates GitHub issues for CRITICAL/HIGH

Reports: "Review complete. 1 CRITICAL (SQL injection), 5 HIGH, 12 MEDIUM, 18 LOW. Remediation plan: 16 hours. Issues created."

Time: 6-8 hours autonomous (vs 10-15 hours manual)
```

### 6.3 Interpreting Results (Automated Severity Classification)

**Claude Code Automatically:**
- Classifies findings by severity (CRITICAL/HIGH/MEDIUM/LOW)

- Provides file locations and line numbers

- Shows before/after code examples

- Estimates remediation time

- Links to relevant documentation (OWASP, CVEs)

- Prioritizes by risk and impact

**Autonomous Prioritization:**
```
Remediation Priority Queue:

CRITICAL (Immediate - This Week):
1. SQL Injection in UserController.login() [2h fix, 1h test]
   Location: src/controllers/UserController.java:45
   Risk: Database compromise, data breach
   Fix: Use parameterized queries

HIGH (This Month):
2. Hardcoded API credentials [1h fix, 30m test]
   Location: src/config/api.py:12
   Risk: Credentials exposed in git history
   Fix: Move to environment variables

3. Missing rate limiting on public API [2h fix, 1h test]
   Location: src/api/routes.py:78-145
   Risk: DoS attacks, resource exhaustion
   Fix: Implement slowapi rate limiter

... [continues with MEDIUM and LOW]

Total Estimated Remediation: 16 hours
Recommended Order: CRITICAL first, then HIGH, then MEDIUM
```

### 6.4 Acting on Findings (Automated Remediation Options)

**Claude Code Can Autonomously:**
1. **Create GitHub Issues:**
   ```
   "Create GitHub issues for all CRITICAL and HIGH findings"

   Claude creates:
   - Issue #42: [CRITICAL] SQL Injection in UserController

   - Issue #43: [HIGH] Hardcoded API credentials

   - Issue #44: [HIGH] Missing rate limiting

   - All with detailed descriptions, code examples, remediation steps
   ```

2. **Suggest Fixes:**
   ```
   "Show me how to fix the SQL injection vulnerability"

   Claude shows:
   # Before (vulnerable):
   query = f"SELECT * FROM users WHERE id = {user_id}"
   cursor.execute(query)

   # After (secure):
   cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

   # Test:
   def test_sql_injection_prevented():
       malicious_input = "1; DROP TABLE users; --"
       result = user_service.get_user(malicious_input)
       # Verify no SQL injection occurred
   ```

3. **Auto-Fix Low-Risk Issues:**
   ```
   "Auto-fix all LOW severity code style violations"

   Claude autonomously:
   - Fixes import organization

   - Removes unused variables

   - Applies consistent formatting

   - Commits changes

   - Runs tests to verify no regressions
   ```

4. **Implement Fixes (with approval):**
   ```
   "Implement the fix for CRITICAL-001 (SQL injection)"

   Claude autonomously:
   1. Creates branch fix/sql-injection-user-controller
   2. Implements parameterized queries
   3. Adds input validation
   4. Creates security test
   5. Runs all tests (pass)
   6. Commits with detailed message
   7. Creates pull request

   Reports: "Fix implemented and tested. PR created: #123"
   ```

---

<a name="part-7-compliance--governance"></a>
## Part 7: Compliance & Governance

### 7.1 Overview with Autonomous Execution

Claude Code autonomously implements compliance frameworks, security governance, and regulatory requirements:

| Framework | Claude Code Automation | Time Saved |
|-----------|------------------------|------------|
| **SOC 2 Type II** | Auto-generates controls, evidence collection | 60% faster |
| **ISO 27001** | Auto-maps 114 controls to codebase | 60% faster |
| **NIST AI RMF** | Auto-implements AI risk management | 70% faster |
| **GDPR/CCPA** | Auto-generates privacy controls | 60% faster |
| **AI Agent Governance** | Auto-implements 4 Pillars Framework | 70% faster |
| **Incident Response** | Auto-creates IR plans and breach protocols | 50% faster |

**Total Time:** 30-60 hours (vs 80-120 hours manual) for comprehensive governance

### 7.2 Available Templates (96 Total)

**Location:** [templates/compliance_governance/](../templates/compliance_governance/)

#### Compliance Frameworks (28 templates)
- **SOC 2 Type II** - Trust Services Criteria for SaaS/Cloud providers
- **ISO 27001:2022** - Information Security Management Systems (114 controls)
- **ISO 42001:2023** - AI Management Systems (NEW for 2025)
- **NIST AI RMF 1.0** - AI Risk Management Framework
- **PCI-DSS v4.0** - Payment Card Industry Data Security Standard

**Templates:** [compliance_frameworks/](../templates/compliance_governance/compliance_frameworks/)

#### Risk Management (14 templates)
- **Risk Assessment** - Systematic threat identification and mitigation
- **Threat Modeling** - STRIDE methodology, attack surface analysis

**Templates:** [risk_management/](../templates/compliance_governance/risk_management/)

#### Governance Policies (14 templates)
- **Security Policies** - Comprehensive security policy documentation
- **Access Control** - RBAC implementation, least privilege

**Templates:** [governance_policies/](../templates/compliance_governance/governance_policies/)

#### Privacy Protection (14 templates)
- **GDPR Compliance** - EU General Data Protection Regulation
- **CCPA Compliance** - California Consumer Privacy Act

**Templates:** [privacy_protection/](../templates/compliance_governance/privacy_protection/)

#### Incident Response (14 templates)
- **Incident Response Plans** - NIST SP 800-61 6-phase lifecycle
- **Breach Protocols** - GDPR 72-hour notification compliance

**Templates:** [incident_response/](../templates/compliance_governance/incident_response/)

#### AI Agent Governance (14 templates)
- **Lifecycle Management** - Separation of duties, CI/CD for AI
- **Agent Observability** - OTel tracing, audit logging
- **Agent Security** - Least privilege for agents
- **Agent Risk Controls** - Guardrails, PII detection

**Templates:** [ai_agent_governance/](../templates/compliance_governance/ai_agent_governance/)

### 7.3 The Four Pillars of AI Agent Governance

Modern AI systems require governance beyond traditional software. The **4 Pillars Framework** provides the foundation:

#### 1. 🔄 Lifecycle Management (Separation of Duties)
**Definition**: Multiple teams manage data/model changes through dev/staging/prod with version control

**Autonomous Implementation:**
```
User: "Implement lifecycle management for our AI agent system"

Claude executes autonomously:
1. Sets up Git with model registries
2. Creates dev/staging/prod environments
3. Configures CI/CD pipelines for AI
4. Implements deployment orchestration (blue-green, canary)
5. Adds change management workflows with approval gates
6. Creates rollback procedures
7. Adds feature flags for gradual rollout
8. Documents promotion workflows
9. Commits all configurations

Time: 6-8 hours autonomous (vs 12-16 hours manual)
```

#### 2. ⚠️ Risk Management (Defense in Depth)
**Definition**: Multiple overlapping defense layers (PII detection, guardrails, compliance controls, monitoring)

**Autonomous Implementation:**
```
User: "Implement defense-in-depth risk management for AI"

Claude executes autonomously:
1. Adds data quality monitoring (schema validation, drift detection)
2. Implements PII detection and redaction
3. Creates guardrails (input validation, output filtering)
4. Adds compliance controls (audit trails, retention policies)
5. Implements model validation (bias detection, performance monitoring)
6. Creates layered security checks
7. Documents risk mitigation strategies
8. Commits all controls

Time: 6-8 hours autonomous (vs 12-16 hours manual)
```

#### 3. 🔒 Security (Least Privilege Access)
**Definition**: Agents and users receive only minimum required permissions

**Autonomous Implementation:**
```
User: "Implement least privilege security for AI agents"

Claude executes autonomously:
1. Configures OAuth 2.0, SSO (SAML, OIDC), MFA
2. Sets up secrets management (key vaults, credential rotation)
3. Implements RBAC with group permissions
4. Adds data protection (TLS/SSL, encryption at rest)
5. Configures network security (private networks, firewalls)
6. Creates zero-trust architecture
7. Documents access control policies
8. Commits all security configurations

Time: 4-6 hours autonomous (vs 8-12 hours manual)
```

#### 4. 🔍 Observability (Audit Everything)
**Definition**: Comprehensive logs of all system interactions for complete traceability

**Autonomous Implementation:**
```
User: "Implement comprehensive observability for AI agents"

Claude executes autonomously:
1. Sets up OTel (OpenTelemetry) tracing
2. Implements audit logging for all agent actions
3. Adds application and inference logging
4. Creates performance monitoring and cost dashboards
5. Implements data and model lineage tracking
6. Adds drift detection and anomaly alerting
7. Creates compliance reporting dashboards
8. Documents observability architecture
9. Commits all monitoring configurations

Time: 6-8 hours autonomous (vs 12-16 hours manual)
```

### 7.4 Autonomous Compliance Implementation

**Comprehensive SOC 2 + AI Governance Example:**

```
User: "Implement SOC 2 Type II compliance with AI agent governance"

Claude executes fully autonomously over 24-30 hours:

=== Phase 1: SOC 2 Framework (8-10 hours) ===
✅ Analyzes Trust Services Criteria (Security, Availability, Confidentiality)
✅ Maps 114 controls to codebase
✅ Implements security controls (CC6.x)
✅ Adds logical access controls (CC6.1)
✅ Implements encryption (CC6.7)
✅ Creates audit logging (CC7.2)
✅ Documents control implementations
✅ Generates evidence collection procedures
✅ Creates policy templates
✅ Commits: "feat: Implement SOC 2 Type II controls"

=== Phase 2: AI Agent Governance (12-16 hours) ===
✅ Implements Pillar 1: Lifecycle Management
   - Git + model registries
   - CI/CD pipelines
   - Deployment orchestration
✅ Implements Pillar 2: Risk Management
   - PII detection
   - Guardrails
   - Compliance controls
✅ Implements Pillar 3: Security
   - OAuth 2.0, RBAC
   - Secrets management
   - Data encryption
✅ Implements Pillar 4: Observability
   - OTel tracing
   - Audit logging
   - Lineage tracking
✅ Commits: "feat: Implement 4 Pillars AI Agent Governance"

=== Phase 3: Documentation & Verification (4-6 hours) ===
✅ Generates comprehensive documentation
✅ Creates audit preparation checklists
✅ Documents evidence collection procedures
✅ Creates compliance dashboards
✅ Verifies all controls operational
✅ Runs compliance validation tests
✅ Generates final compliance report

Reports: "SOC 2 + AI Governance implementation complete. All controls operational, evidence collection automated, audit-ready documentation generated."

Time: 24-30 hours autonomous (vs 50-70 hours manual)
```

### 7.5 Integration with Security & Testing

**Compliance integrates with existing templates:**

```
Compliance Frameworks → Code Review (Security Phase)
  ↓                         ↓
Maps controls         Validates implementation
to code              ↓
  ↓                  Generates findings
Implements        ↓
controls          Creates remediation plan
  ↓
Tests Generation → Compliance Tests
  ↓                   ↓
Generates        Validates controls work
compliance       ↓
tests            Achieves 80%+ coverage
```

**Autonomous Integration Example:**

```
User: "Ensure our application is SOC 2 compliant and secure"

Claude executes autonomously:
1. Phase 1: Runs security review (6-10 hours)
   - Identifies OWASP Top 10 vulnerabilities
   - Finds 2 CRITICAL, 5 HIGH issues
2. Phase 2: Fixes critical issues (4-6 hours)
   - Implements parameterized queries
   - Adds input validation
   - Removes hardcoded secrets
3. Phase 3: Implements SOC 2 controls (8-10 hours)
   - Maps controls to codebase
   - Implements missing controls
   - Documents evidence collection
4. Phase 4: Generates compliance tests (6-8 hours)
   - Creates security tests for all controls
   - Achieves 85% coverage
   - Integrates into CI/CD
5. Phase 5: Verification (2-3 hours)
   - All tests pass
   - All controls operational
   - Audit documentation complete

Reports: "Application is SOC 2 compliant and secure. All CRITICAL/HIGH vulnerabilities fixed, controls implemented, tests passing, audit-ready."

Total Time: 26-37 hours autonomous (vs 60-80 hours manual)
```

### 7.6 Quick Start Recommendations

**For Traditional SaaS:**
```
User: "Implement compliance for our SaaS application"

Recommended: SOC 2 + ISO 27001
Time: 12-16 hours autonomous
Claude implements: Trust Services Criteria + ISMS
```

**For AI/ML Systems:**
```
User: "Implement compliance for our AI/ML platform"

Recommended: NIST AI RMF + ISO 42001 + 4 Pillars AI Governance
Time: 18-24 hours autonomous
Claude implements: AI risk management + AI management system + agent governance
```

**For Payment Processing:**
```
User: "Implement compliance for payment processing"

Recommended: PCI-DSS + SOC 2
Time: 15-18 hours autonomous
Claude implements: Payment security + trust services
```

**For EU Markets:**
```
User: "Implement compliance for EU operations"

Recommended: GDPR + ISO 27001
Time: 12-16 hours autonomous
Claude implements: Privacy protection + information security
```

### 7.7 Expected Outcomes

**Autonomous Compliance Achievements:**
- ✅ All framework controls implemented
- ✅ Evidence collection automated
- ✅ Policy documentation generated
- ✅ Audit preparation checklists created
- ✅ Compliance tests passing at 85%+
- ✅ Continuous monitoring operational
- ✅ Audit-ready documentation complete

**Business Impact:**
- 📈 Pass SOC 2 audits on first attempt
- 📈 Accelerate enterprise sales cycles
- 📈 Meet regulatory requirements (GDPR, CCPA)
- 📈 Reduce audit preparation time by 60%
- 📈 Demonstrate trustworthy AI deployment

---

<a name="part-8-codebase-cleanup"></a>
## Part 8: Codebase Cleanup

### 8.1 Process Overview with Safety Checks

Claude Code executes cleanup with comprehensive safety checks:

**Autonomous Safety Protocol:**
1. ✅ Runs full test suite before any changes
2. ✅ Creates backup branch automatically
3. ✅ Makes incremental changes in passes
4. ✅ Runs tests after each pass
5. ✅ Reverts automatically if tests fail
6. ✅ Verifies code coverage maintained
7. ✅ Checks performance hasn't degraded

**Multi-Pass Autonomous Cleanup:**
```
User: "Clean up this codebase - remove dead code and technical debt"

Claude executes autonomously:

Pass 1: Analysis (30 min)
- Scans for unused imports: 147 found

- Identifies unused functions: 23 found

- Detects duplicate code: 8 blocks found

- Finds debug statements: 45 found

- Risk assessment: LOW risk

Pass 2: Low-Risk Cleanup (1 hour)
- Removes 147 unused imports

- Deletes 45 debug print statements

- Formats code consistently

- Runs tests: ALL PASS ✅

- Coverage: 82% (maintained) ✅

- Commits changes

Pass 3: Medium-Risk Cleanup (2 hours)
- Removes 23 unused functions

- Consolidates 8 duplicate code blocks

- Updates deprecated API calls

- Runs tests: ALL PASS ✅

- Coverage: 82% (maintained) ✅

- Commits changes

Pass 4: Verification (30 min)
- Runs full test suite

- Verifies code coverage ≥ 80%

- Checks build succeeds

- Runs linters (no new warnings)

- Manual smoke test recommended

Reports: "Cleanup complete. Removed 215 lines of dead code, reduced duplication by 87%. Tests pass, coverage maintained at 82%."

Time: 4-5 hours autonomous (vs 8-10 hours manual)
```

### 8.2 Autonomous Cleanup (What Claude Code Handles Automatically)

**Fully Autonomous:**
- ✅ Unused import removal

- ✅ Debug statement deletion

- ✅ Code formatting

- ✅ Import organization

- ✅ Simple refactoring (obvious improvements)

- ✅ Duplicate code consolidation

- ✅ Deprecated API updates

**Requires Approval:**
- ⚠️ Deleting functions (asks if truly unused)

- ⚠️ Major refactoring (shows plan first)

- ⚠️ Architecture changes

- ⚠️ Breaking API changes

**Example Autonomous Decision:**
```
Claude: "I've identified 23 unused functions. 15 are clearly unused (no callers). 8 have ambiguous usage patterns.

For the 15 clear cases, I'll remove them automatically.
For the 8 ambiguous cases, would you like me to:
1. Show you each one for manual review
2. Mark them as @deprecated for now
3. Leave them unchanged

Which would you prefer?"
```

### 8.3 Post-Cleanup Verification (Automated Test Runs)

**Claude Code Automatically:**
1. ✅ Runs full test suite after each cleanup pass
2. ✅ Verifies all tests still pass
3. ✅ Checks code coverage maintained (80%+)
4. ✅ Runs linters and static analysis
5. ✅ Builds project to verify no breakage
6. ✅ Runs performance benchmarks
7. ✅ Generates diff review summary

**Autonomous Rollback:**
```
If tests fail:
Claude: "Tests failed after removing UserPreferences module. Reverting changes..."
[Automatically reverts last commit]
Claude: "Rollback complete. UserPreferences module appears to be used indirectly. Manual review needed."
```

**Success Report:**
```
Cleanup Verification Report:
✅ All 147 tests pass
✅ Code coverage: 82% (maintained)
✅ Build: SUCCESS
✅ Linters: 0 new warnings
✅ Performance: No regressions
✅ Reduced lines of code: 8,432 → 8,217 (215 lines removed)
✅ Reduced duplication: 12% → 3%
✅ Reduced complexity: Average cyclomatic 8.4 → 6.2

Changes committed to branch: cleanup/remove-dead-code
Ready for review and merge.
```

**Manual Verification (Recommended):**
- [ ] Review git diff for unintended changes

- [ ] Smoke test critical user flows

- [ ] Verify application starts correctly

- [ ] Check logs for unexpected errors

---

<a name="complete-autonomous-workflow-example"></a>
## 🎓 Complete Autonomous Workflow Example

**Scenario:** Python web API - undocumented, untested, security issues, technical debt

**Goal:** Production-ready codebase autonomously transformed by Claude Code

### Autonomous Execution (Total: 16-20 hours vs 32 hours manual)

```
User: "Transform this codebase to production quality: comprehensive documentation, 80%+ test coverage, fix security issues, remove technical debt"

Claude executes fully autonomously over 16-20 hours:

=== Phase 1: Configuration (5 min) ===
✅ Creates CLAUDE.md with Python best practices
✅ Configures project structure
✅ Installs Claude Code skills

=== Phase 2: Documentation (2-3 hours) ===
✅ Generates docstrings for 127 functions
✅ Adds strategic comments to complex logic
✅ Creates comprehensive README
✅ Generates API documentation
✅ Creates SBOM for dependencies
✅ Commits: "docs: Add comprehensive documentation"

=== Phase 3: Test Generation (6-8 hours) ===
✅ Sets up pytest infrastructure
✅ Generates 147 unit tests (FIRST principles, AAA pattern)
✅ Creates integration tests for APIs
✅ Generates mocks for external services
✅ Achieves 82% code coverage
✅ Sets up .github/workflows/test.yml CI/CD
✅ Runs mutation testing (85% mutation score)
✅ Commits: "test: Add comprehensive test suite with 82% coverage"

=== Phase 4: Code Review (4-5 hours) ===
✅ Phase 1: Analyzes project architecture
✅ Phase 2: Evaluates code quality (finds 26 issues)
✅ Phase 3: Security scan (finds 1 CRITICAL, 2 HIGH)
✅ Phase 4: Performance analysis (finds 3 N+1 queries)
✅ Phase 5: Testing review
✅ Phase 6: Generates consolidated report
✅ Creates GitHub issues for CRITICAL/HIGH findings

=== Phase 5: Security Fixes (2-3 hours) ===
✅ Fixes SQL injection (CRITICAL)
✅ Removes hardcoded secrets → environment variables
✅ Adds rate limiting to public endpoints
✅ Adds security tests
✅ All tests pass
✅ Commits: "fix: Address critical security vulnerabilities"

=== Phase 6: Codebase Cleanup (2-3 hours) ===
✅ Removes 147 unused imports
✅ Deletes 23 unused functions
✅ Consolidates 8 duplicate code blocks
✅ Removes 45 debug statements
✅ Formats code with Black
✅ Tests pass, coverage maintained 82%
✅ Commits: "refactor: Clean up codebase"

=== Phase 7: Verification (30 min) ===
✅ Runs complete test suite: ALL PASS
✅ Coverage: 82%
✅ Mutation score: 85%
✅ CI/CD pipeline: PASSING
✅ Security scan: No CRITICAL/HIGH issues
✅ Performance benchmarks: No regressions
✅ Creates pull request with summary

Final Report:
───────────────────────────────────────
Production Transformation Complete

Before:
❌ No documentation
❌ No tests
❌ 1 CRITICAL + 2 HIGH security issues
❌ 215 lines of dead code

After:
✅ Comprehensive documentation (docstrings, README, API docs, SBOM)
✅ 147 tests, 82% coverage, 85% mutation score
✅ All CRITICAL/HIGH security issues fixed
✅ Clean, maintainable codebase
✅ CI/CD pipeline configured and passing

Time Investment: 16-20 hours autonomous
(vs 32 hours manual)

Pull Request: #123
"Production-Ready: Documentation, Tests, Security Fixes, Cleanup"
───────────────────────────────────────
```

**Human Involvement Required:**
- Initial instruction: "Transform to production quality"

- Approval for security fixes (review sensitive changes)

- Final pull request review and merge

- Deployment to staging/production

**Total Human Time:** ~2 hours (vs 32 hours doing it manually)

---

<a name="getting-started-checklist"></a>
## 🚀 Getting Started Checklist

**5-Minute Setup:**
- [ ] Copy CLAUDE_comprehensive_40k.md to your project as CLAUDE.md

- [ ] Customize CLAUDE.md for your project

- [ ] Install CRITICAL workflow skills

- [ ] Install language-specific skills

- [ ] Commit CLAUDE.md and .claude/skills/ to git

**Start Building:**
```
"Use plan-before-code skill to design a user authentication system"

"Generate comprehensive tests with 80%+ coverage"

"Perform security review focusing on OWASP Top 10"

"Document the entire codebase with docstrings and API docs"

"Clean up technical debt and remove dead code"
```

**Claude Code handles the rest autonomously!**

---

<a name="additional-resources"></a>
## 📚 Additional Resources

**Essential Reading:**
- [CLAUDE.md Templates](../templates/ai_instructions/agentic_systems/claude_code/)

- [Skills Catalog](../catalogs/claude_skills/)

- [Claude Code Project Setup Guide](CLAUDE_CODE_PROJECT_SETUP.md)

**Template Directories:**
- [Documentation Templates](../templates/documentation_generation/)

- [Testing Templates](../templates/tests_generation/)

- [Code Review Templates](../templates/code_review/)

- [Cleanup Templates](../templates/code_cleanup/)

**Compare Approaches:**
- [Coding Assistant Guide](CODING_ASSISTANT_GUIDE.md) - Manual workflows (Copilot, ChatGPT)

- This guide - Autonomous workflows (Claude Code)

---

[← Back to Main](../README.md) | [← Coding Assistant Guide](CODING_ASSISTANT_GUIDE.md)
