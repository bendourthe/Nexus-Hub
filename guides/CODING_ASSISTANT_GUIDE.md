# Coding Assistant Guide

**Complete guide for using AI Templates with GitHub Copilot, Cursor, Windsurf, ChatGPT, and Claude**

[← Back to Main](../README.md)

---

## Table of Contents

- [Introduction](#introduction)
- [Part 1: Setting Up Your Coding Assistant](#part-1-setting-up-your-coding-assistant)
- [Part 2: Understanding Templates](#part-2-understanding-templates)
- [Part 3: Generate Code Documentation](#part-3-generate-code-documentation)
- [Part 4: Generate Tests](#part-4-generate-tests)
- [Part 5: Code Review](#part-5-code-review)
- [Part 6: Compliance & Governance](#part-6-compliance--governance)
- [Part 7: Codebase Cleanup](#part-7-codebase-cleanup)
- [Complete Workflow Example](#complete-workflow-example)
- [Next Steps](#next-steps)

---

## Introduction

This guide helps you maximize AI-assisted development using the comprehensive template collection in this repository. Whether you're using GitHub Copilot, Cursor, Windsurf, ChatGPT, or Claude, you'll learn how to:

- Configure your coding assistant with optimal instructions

- Use templates to generate documentation, tests, reviews, and cleanup

- Follow best practices for verification and quality assurance

- Build comprehensive, production-ready codebases with AI assistance

**Who This Is For:**
- Developers using GitHub Copilot in VS Code or IDEs

- Cursor users wanting structured AI workflows

- Windsurf users (via Cascade configuration)

- ChatGPT/Claude users for code assistance

**Time Investment:**
- Initial setup: 15-30 minutes

- Per-template usage: 1-12 hours depending on task complexity

---

## Part 1: Setting Up Your Coding Assistant

### Overview

AI coding assistants work best when given clear, comprehensive instructions about your project's coding standards, architecture, and requirements. This section shows you how to configure each assistant for optimal results.

### 1.1 GitHub Copilot Setup

**Location:** `.github/copilot-instructions.md`

GitHub Copilot reads instructions from a `.github/copilot-instructions.md` file in your repository root.

**Setup Steps:**

1. Create the `.github` directory in your project root:
   ```bash
   mkdir .github
   ```

2. Choose a template from `templates/ai_instructions/coding_assistants/`:
   - **Comprehensive (35k tokens):** Full instructions with detailed examples

   - **Condensed (15k tokens):** Essential instructions for token efficiency

3. Copy your language-specific template:
   ```bash
   # Example for Python
   cp templates/ai_instructions/coding_assistants/python/GLOBAL_comprehensive_40k.md .github/copilot-instructions.md
   ```

4. Customize for your project (see Section 1.4)

**Available Templates:**
- [Python](../templates/ai_instructions/coding_assistants/python/) - pytest, type hints, Black formatting

- [JavaScript/TypeScript](../templates/ai_instructions/coding_assistants/javascript/) - Jest, ESLint, modern ES6+

- [Java](../templates/ai_instructions/coding_assistants/java/) - JUnit 5, Spring Boot, Maven/Gradle

- [C#](../templates/ai_instructions/coding_assistants/csharp/) - xUnit, .NET Core, C# 10+

- [Go](../templates/ai_instructions/coding_assistants/go/) - testing package, idiomatic Go

- [C](../templates/ai_instructions/coding_assistants/c/) - Unity/CUnit, embedded systems, MISRA-C

- [C++](../templates/ai_instructions/coding_assistants/cpp/) - GoogleTest, modern C++17/20

### 1.2 Cursor Setup

**Location:** Settings → Rules & Memories → User Rules

Cursor uses a global "User Rules" configuration that applies across all projects.

**Setup Steps:**

1. Open Cursor
2. Go to Settings (Ctrl+, or Cmd+,)
3. Navigate to **Rules & Memories** → **User Rules**
4. Copy content from your chosen template:
   ```
   templates/ai_instructions/coding_assistants/[language]/GLOBAL_comprehensive_40k.md
   ```
5. Paste into User Rules text area
6. Click Save

**Project-Specific Instructions:**

For project-specific overrides, create `.cursorrules` file in project root:
```bash
cp templates/ai_instructions/coding_assistants/python/GLOBAL_comprehensive_40k.md .cursorrules
```

### 1.3 Windsurf Setup

**Location:** Cascade → `global_windsurf.md`

Windsurf uses Cascade's global configuration system.

**Setup Steps:**

1. Open Windsurf
2. Access Cascade settings
3. Create/edit `global_windsurf.md`
4. Copy content from your chosen template:
   ```
   templates/ai_instructions/coding_assistants/[language]/GLOBAL_comprehensive_40k.md
   ```
5. Save configuration

**Note:** Windsurf configuration paths may vary by version. Consult Windsurf documentation for exact file location.

### 1.4 What AI Instructions Should Contain

Effective AI instructions should cover these key areas:

**1. Coding Standards**
- Code style and formatting (line length, indentation, naming conventions)

- Import organization rules

- Comment and documentation requirements

- Language-specific idioms and best practices

**2. Project Structure**
- Directory organization

- Module/package structure

- File naming conventions

- Configuration file locations

**3. Testing Requirements**
- Testing framework (pytest, Jest, JUnit, etc.)

- Test file organization and naming

- Coverage requirements (typically 80%+)

- Test patterns (AAA, FIRST principles)

**4. Development Workflow**
- Git commit message format

- Branch naming conventions

- Code review expectations

- CI/CD integration requirements

**5. Language-Specific Preferences**
- Type hints/annotations usage

- Error handling patterns

- Async/await conventions

- Performance considerations

**6. Security Guidelines**
- Input validation requirements

- Authentication/authorization patterns

- Secrets management

- Common vulnerability prevention (OWASP Top 10)

### 1.5 Structure and Best Practices

**Organization:**

Structure your instructions in clear, hierarchical sections:

```markdown
# [Language] Development Instructions

## 1. General Behavior
- Core principles

- Clarification protocol

- Quality standards

## 2. Project Architecture
- Directory structure

- Module organization

- Dependencies

## 3. Code Standards
- Formatting rules

- Naming conventions

- Best practices

## 4. Documentation
- Docstring format

- Comment guidelines

- README structure

## 5. Testing
- Framework setup

- Test patterns

- Coverage targets

## 6. Development Workflow
- Git practices

- Command preferences

- Version control
```

**Token Limits:**

Different assistants have different token limits for instructions:

| Assistant | Recommended Limit | Template Type |
|-----------|------------------|---------------|
| GitHub Copilot | 35,000 tokens | Comprehensive |
| Cursor | 35,000 tokens | Comprehensive |
| Windsurf | 35,000 tokens | Comprehensive |
| ChatGPT (context) | 15,000 tokens | Condensed |
| Claude (context) | 15,000 tokens | Condensed |

**Comprehensive vs Condensed:**

- **Comprehensive (35-40k tokens):**

  - Full examples and detailed explanations

  - Multiple code samples per concept

  - Complete templates and patterns

  - Best for: IDE-integrated assistants (Copilot, Cursor, Windsurf)

- **Condensed (15-20k tokens):**

  - Essential rules and patterns

  - Minimal examples

  - Reference-style format

  - Best for: Chat-based assistants (ChatGPT, Claude)

**Best Practices:**

✅ **Do:**
- Keep instructions up-to-date with project evolution

- Version control your instruction files (`.github/copilot-instructions.md`, `.cursorrules`)

- Customize templates for project-specific needs

- Include concrete examples

- Use clear, imperative language

- Test instructions with actual AI queries

❌ **Avoid:**
- Vague or ambiguous rules

- Contradictory guidelines

- Outdated patterns or deprecated practices

- Excessive verbosity (respect token limits)

- Copy-pasting without customization

---

## Part 2: Understanding Templates

### 2.1 How Templates Work

Templates in this repository follow a simple, effective workflow:

1. **Choose a template** based on your task (documentation, testing, review, cleanup)
2. **Copy the prompt** from the template file
3. **Paste into your AI assistant** (Copilot Chat, ChatGPT, Claude, etc.)
4. **Follow the AI's guidance** through the multi-step process
5. **Verify outputs** using provided checklists
6. **Iterate as needed** to refine results

**Template Anatomy:**

Each template contains:
- **Objective:** What the template accomplishes

- **Time Estimate:** Expected duration

- **Prerequisites:** What you need before starting

- **Success Criteria:** How to know you're done

- **Prompt Template:** The actual prompt to copy/paste

- **Verification Steps:** Quality checks after completion

### 2.2 Template Categories Overview

This repository contains **178 templates** across 5 main categories:

#### 1. AI Instructions Configuration

**Purpose:** Set up your coding assistant with optimal instructions

**Available:**
- 7 languages × 2 formats (comprehensive/condensed) = 14 templates

- Covers: Copilot, Cursor, Windsurf configurations

**When to Use:**
- Starting a new project

- Onboarding new team members

- Updating coding standards

**Location:** [templates/ai_instructions/coding_assistants/](../templates/ai_instructions/coding_assistants/)

#### 2. Documentation Generation

**Purpose:** Create docstrings, API docs, README files, and technical documentation

**Available:**
- 6 doc types × 7 languages = 42 templates

- Types: Docstrings, Comments, User Docs, Technical Docs, API Docs, SBOM

**When to Use:**
- After writing new code (add docstrings)

- Preparing for release (user documentation)

- Onboarding new developers (technical docs)

- Compliance requirements (SBOM)

**Location:** [templates/documentation_generation/](../templates/documentation_generation/)

#### 3. Tests Generation

**Purpose:** Create comprehensive test suites with unit, integration, and validation tests

**Available:**
- 8 testing phases × 7 languages = 56 templates

- Phases: Structure, Unit Tests, Test Cases, Mocks, Performance, Coverage, CI/CD, Validation

**When to Use:**
- Adding tests to existing code

- Starting TDD workflow

- Improving test coverage

- Setting up CI/CD pipelines

**Location:** [templates/tests_generation/](../templates/tests_generation/)

#### 4. Code Review

**Purpose:** Get systematic feedback on quality, security, performance, and testing

**Available:**
- 6 review phases × 7 languages = 42 templates

- Phases: Context, Quality, Security, Performance, Testing, Final Report

**When to Use:**
- Before merging major features

- Periodic code health checks

- Pre-release audits

- Security reviews

**Location:** [templates/code_review/](../templates/code_review/)

#### 5. Codebase Cleanup

**Purpose:** Remove dead code, duplication, and legacy patterns

**Available:**
- 7 language-specific cleanup templates

**When to Use:**
- After major refactoring

- Before starting new features

- Reducing technical debt

- Improving maintainability

**Location:** [templates/code_cleanup/](../templates/code_cleanup/)

### 2.3 When to Use Each Category

**Decision Tree:**

```
What do you need?

├─ Setting up AI assistant for first time?
│  └─ Use: AI Instructions Configuration

├─ Code is undocumented?
│  └─ Use: Documentation Generation (start with Docstrings)

├─ Code has no/few tests?
│  └─ Use: Tests Generation (start with Unit Tests if framework exists)

├─ Need quality/security feedback?
│  └─ Use: Code Review (run all 6 phases for comprehensive review)

└─ Codebase has technical debt?
   └─ Use: Codebase Cleanup
```

**Typical Workflow:**

For a complete project setup, follow this order:

1. **AI Instructions** (15-30 min) - Configure your assistant
2. **Documentation Generation** (4-8 hours) - Document existing code
3. **Tests Generation** (6-12 hours) - Build test suite
4. **Code Review** (4-12 hours) - Identify issues
5. **Codebase Cleanup** (4-8 hours) - Remove technical debt
6. **Repeat 2-5** as project evolves

---

## Part 3: Generate Code Documentation

### 3.1 Available Templates

Six documentation types available for all 7 languages (Python, JavaScript, Java, C#, Go, C, C++):

#### 1. Docstrings

**Purpose:** Generate function/class-level documentation

**What You Get:**
- Comprehensive docstrings for all public interfaces

- Parameter descriptions with types

- Return value documentation

- Exception/error documentation

- Usage examples

**Best For:** Code-level documentation visible in IDEs

**Templates:** [templates/documentation_generation/docstrings/](../templates/documentation_generation/docstrings/)

#### 2. Comments

**Purpose:** Add strategic inline comments explaining complex logic

**What You Get:**
- Comments explaining "why" not "what"

- Complex algorithm explanations

- Business logic clarifications

- Edge case documentation

**Best For:** Maintainability and knowledge transfer

**Templates:** [templates/documentation_generation/comments/](../templates/documentation_generation/comments/)

#### 3. User Documentation

**Purpose:** Create README, installation guides, and tutorials

**What You Get:**
- Professional README with badges and examples

- Installation/setup instructions

- Quick start guides

- Usage tutorials

- Troubleshooting sections

**Best For:** External users and new team members

**Templates:** [templates/documentation_generation/user_docs/](../templates/documentation_generation/user_docs/)

#### 4. Technical Documentation

**Purpose:** Document architecture, design decisions, and codebase structure

**What You Get:**
- Architecture diagrams and descriptions

- Design decision records (ADRs)

- Component interaction maps

- Codebase walkthrough

- Development guidelines

**Best For:** Developer onboarding and long-term maintenance

**Templates:** [templates/documentation_generation/technical_docs/](../templates/documentation_generation/technical_docs/)

#### 5. API Documentation

**Purpose:** Generate complete API reference documentation

**What You Get:**
- Endpoint documentation (REST/GraphQL)

- Request/response examples

- Authentication requirements

- Error handling documentation

- Rate limiting and pagination

- OpenAPI/Swagger specs (REST)

- gRPC proto documentation

**Best For:** API consumers and integration developers

**Templates:** [templates/documentation_generation/api_docs/](../templates/documentation_generation/api_docs/)

#### 6. SBOM (Software Bill of Materials)

**Purpose:** Generate compliance-ready dependency documentation

**What You Get:**
- Complete dependency inventory

- Version tracking

- License information

- Security vulnerability tracking

- NTIA minimum elements compliance

- EU Cyber Resilience Act (CRA) compliance

**Best For:** Security audits, compliance, supply chain management

**Templates:** [templates/documentation_generation/sbom/](../templates/documentation_generation/sbom/)

### 3.2 Recommended Order

Follow this sequence for comprehensive documentation:

**Phase 1: Code-Level Documentation (2-4 hours)**
1. **Docstrings** (2-3 hours) - Document all public interfaces
2. **Comments** (1-2 hours) - Explain complex logic

**Phase 2: User-Facing Documentation (3-4 hours)**
3. **User Documentation** (3-4 hours) - README, installation, tutorials

**Phase 3: Developer Documentation (4-8 hours)**
4. **Technical Documentation** (4-6 hours) - Architecture and design decisions
5. **API Documentation** (4-8 hours) - Complete API reference (if applicable)

**Phase 4: Compliance (2-3 hours)**
6. **SBOM** (2-3 hours) - Dependency and compliance documentation

**Quick Documentation (2-4 hours):**
If time is limited, focus on:
- Docstrings (essential for IDE support)

- User Documentation (critical for adoption)

**Comprehensive Documentation (12-16 hours):**
Complete all 6 types for production-ready, enterprise-grade documentation.

### 3.3 What to Expect

#### Time Estimates

| Documentation Type | AI Generation Time | Review/Refinement | Total |
|-------------------|-------------------|-------------------|-------|
| Docstrings | 30-60 min | 1-2 hours | 2-3 hours |
| Comments | 20-30 min | 30-60 min | 1-2 hours |
| User Documentation | 1-2 hours | 1-2 hours | 3-4 hours |
| Technical Documentation | 2-3 hours | 2-3 hours | 4-6 hours |
| API Documentation | 2-3 hours | 2-5 hours | 4-8 hours |
| SBOM | 30-60 min | 1-2 hours | 2-3 hours |

#### Output Formats

**Docstrings:**
- Inline code documentation in language-native format

- Python: Google/NumPy/Sphinx style

- JavaScript: JSDoc format

- Java: JavaDoc format

- C#: XML documentation comments

- Go: Godoc format

- C/C++: Doxygen format

**User/Technical/API Documentation:**
- Markdown files (.md)

- Can be converted to HTML/PDF if needed

- Often includes diagrams (Mermaid, PlantUML)

**SBOM:**
- SPDX format (.spdx)

- CycloneDX format (.cdx.json)

- CSV format for spreadsheet import

#### Customization Needs

You'll need to customize:

✏️ **Project-Specific Details:**
- Project name, version, description

- Repository URLs and links

- Team/organization information

- License information

✏️ **Technical Specifications:**
- Actual API endpoints and parameters

- Real authentication mechanisms

- Accurate performance characteristics

- Correct dependency versions

✏️ **Usage Examples:**
- Verify code examples work

- Add project-specific examples

- Include common use cases

- Test all sample code

### 3.4 Verification Steps

After generating documentation, verify quality using these checklists:

#### Docstrings Verification

- [ ] All public functions/classes documented

- [ ] All parameters described with types

- [ ] Return values clearly specified

- [ ] Exceptions/errors documented

- [ ] Examples included where helpful

- [ ] Formatting follows language conventions

- [ ] No generic placeholder text remains

- [ ] IDE tooltips display correctly

#### Comments Verification

- [ ] Comments explain "why" not "what"

- [ ] Complex algorithms have explanations

- [ ] No obvious/redundant comments

- [ ] Business logic clarified

- [ ] Edge cases documented

- [ ] TODO/FIXME items are actionable

- [ ] Comments are up-to-date with code

#### User Documentation Verification

- [ ] README is comprehensive and professional

- [ ] Installation instructions are complete

- [ ] All prerequisites listed

- [ ] Examples work as written

- [ ] Troubleshooting section covers common issues

- [ ] Links are valid and working

- [ ] Badges/shields are accurate

- [ ] Contact/support information current

#### Technical Documentation Verification

- [ ] Architecture accurately reflects codebase

- [ ] Design decisions are explained

- [ ] Component interactions documented

- [ ] Diagrams are clear and accurate

- [ ] Development setup is complete

- [ ] Coding standards documented

- [ ] Key abstractions explained

- [ ] Technical debt acknowledged

#### API Documentation Verification

- [ ] All endpoints documented

- [ ] Request/response examples valid

- [ ] Authentication clearly explained

- [ ] Error responses documented

- [ ] Rate limits specified

- [ ] Versioning strategy clear

- [ ] OpenAPI/Swagger spec validates

- [ ] Examples can be executed

#### SBOM Verification

- [ ] All dependencies listed

- [ ] Versions are accurate

- [ ] Licenses identified correctly

- [ ] Transitive dependencies included

- [ ] Security vulnerabilities noted

- [ ] NTIA minimum elements present

- [ ] Format validates (SPDX/CycloneDX)

- [ ] Regular update process defined

#### General Documentation Quality

✅ **Test Documentation:**
```bash
# Check all links work
markdown-link-check docs/**/*.md

# Spell check
aspell check docs/*.md

# Test code examples
# Extract and run all code blocks
```

✅ **Review for Accuracy:**
- Technical details are correct

- Examples execute without errors

- Information is current and up-to-date

- No broken links or references

✅ **Ensure Consistency:**
- Terminology used consistently

- Formatting style uniform

- Version numbers match

- Cross-references work

✅ **Validate Completeness:**
- No "TODO" or "[Description here]" placeholders

- All sections filled out

- Examples provided where needed

- Edge cases covered

---

## Part 4: Generate Tests

### 4.1 8-Phase Testing Methodology

This repository provides a comprehensive 8-phase testing methodology that builds production-ready test suites from infrastructure to validation.

#### Phase Overview

| Phase | Purpose | Time Estimate | When to Use |
|-------|---------|---------------|-------------|
| **1. Test Structure** | Set up testing framework and infrastructure | 2-4 hours | New projects, no test framework exists |
| **2. Unit Tests** | Create isolated, fast component tests | 3-6 hours | ⭐ START HERE if framework exists |
| **3. Test Cases** | Build integration and E2E test scenarios | 4-8 hours | After unit tests, for workflow validation |
| **4. Mocks & Fixtures** | Implement test doubles and data factories | 3-5 hours | When tests need external dependencies |
| **5. Performance Testing** | Add load, stress, and benchmark tests | 4-6 hours | Performance-critical applications |
| **6. Code Coverage** | Measure and improve coverage to 80%+ | 2-3 hours | After substantial test suite exists |
| **7. CI/CD Integration** | Automate tests in pipelines | 3-5 hours | Before production deployment |
| **8. Validation** | Mutation testing and quality validation | 4-6 hours | Final phase - validates test effectiveness |

**Total Time:** 25-43 hours for complete 8-phase implementation

#### Phase 1: Test Structure

**Objective:** Establish testing infrastructure

**What You Get:**
- Testing framework installation (pytest, Jest, JUnit, etc.)

- Directory structure (`tests/`, `__tests__/`, etc.)

- Configuration files (pytest.ini, jest.config.js, etc.)

- Test utilities and helpers

- Initial test runner setup

**Skip This Phase If:** You already have a working test framework

**Templates:** [templates/tests_generation/test_structure/](../templates/tests_generation/test_structure/)

#### Phase 2: Unit Tests ⭐ Most Popular

**Objective:** Create fast, isolated component tests

**What You Get:**
- FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)

- AAA pattern (Arrange-Act-Assert)

- 20-30 example tests per language

- Test isolation best practices

- Fast execution (<1s per test)

**Start Here If:** You already have a test framework

**Templates:** [templates/tests_generation/unit_tests/](../templates/tests_generation/unit_tests/)

**Special:** [C++ Google Test + VS Code + Copilot Workflow](../templates/tests_generation/GOOGLE_TEST_VSCODE_WORKFLOW.md) - 10-minute automated setup!

#### Phase 3: Test Cases

**Objective:** Integration and end-to-end test scenarios

**What You Get:**
- Multi-component integration tests

- End-to-end workflow tests

- API/database integration tests

- User journey scenarios

- Cross-module interaction tests

**Templates:** [templates/tests_generation/test_cases/](../templates/tests_generation/test_cases/)

#### Phase 4: Mocks & Fixtures

**Objective:** Test isolation through test doubles

**What You Get:**
- Mocking strategies (unittest.mock, Mockito, etc.)

- Test data factories

- Fixture management

- Stub and spy patterns

- External dependency isolation

**Templates:** [templates/tests_generation/mocks_fixtures/](../templates/tests_generation/mocks_fixtures/)

#### Phase 5: Performance Testing

**Objective:** Validate performance under load

**What You Get:**
- Load testing scenarios

- Stress testing suites

- Benchmark tests

- Performance regression tests

- Profiling integration

**Templates:** [templates/tests_generation/performance_testing/](../templates/tests_generation/performance_testing/)

#### Phase 6: Code Coverage

**Objective:** Measure and improve test coverage

**What You Get:**
- Coverage tool setup (coverage.py, Istanbul, JaCoCo, etc.)

- Coverage reports and visualization

- Gap identification

- 80%+ coverage roadmap

- Coverage enforcement in CI

**Templates:** [templates/tests_generation/code_coverage/](../templates/tests_generation/code_coverage/)

#### Phase 7: CI/CD Integration

**Objective:** Automate testing in pipelines

**What You Get:**
- CI configuration (GitHub Actions, GitLab CI, Jenkins, etc.)

- Automated test execution

- Quality gates

- Test parallelization

- Result reporting and notifications

**Templates:** [templates/tests_generation/maintenance_cicd/](../templates/tests_generation/maintenance_cicd/)

#### Phase 8: Validation (Final Phase)

**Objective:** Validate test quality through mutation testing

**What You Get:**
- Mutation testing setup (mutmut, Stryker, PIT, etc.)

- Weak test detection

- Test effectiveness scoring (>80% mutation score)

- Reward hacking pattern detection

- Test quality improvement recommendations

**Run This Last:** After all other testing phases complete

**Templates:** [templates/tests_generation/reward_hacking/](../templates/tests_generation/reward_hacking/)

### 4.2 Template Usage

#### When to Use Each Phase

**Scenario 1: New Project (No Tests)**
```
Start → Phase 1 (Structure) → Phase 2 (Unit Tests) → Phase 3 (Integration) →
        Phase 6 (Coverage) → Phase 7 (CI/CD) → Phase 8 (Validation)

Time: 18-28 hours
Skip: Phases 4-5 unless needed
```

**Scenario 2: Existing Project (Some Tests)**
```
Start → Phase 2 (Unit Tests) → Phase 6 (Coverage) →
        Identify Gaps → Phase 3/4 as needed → Phase 8 (Validation)

Time: 9-15 hours
```

**Scenario 3: Performance-Critical Application**
```
Start → Phase 1/2 → Phase 3 → Phase 5 (Performance) →
        Phase 6 (Coverage) → Phase 7 (CI/CD) → Phase 8 (Validation)

Time: 22-34 hours
```

**Scenario 4: Quick Test Boost**
```
Start → Phase 2 (Unit Tests) → Phase 6 (Coverage) → Done

Time: 5-9 hours
Focus on 80% coverage target
```

#### How Phases Build on Each Other

**Dependencies:**

```
Phase 1 (Structure)
    ↓
Phase 2 (Unit Tests) ← Most Important
    ↓
Phase 3 (Integration Tests)
    ↓
Phase 4 (Mocks) ← Use when Phase 3 needs external dependencies
    ↓
Phase 5 (Performance) ← Optional for performance-critical apps
    ↓
Phase 6 (Coverage) ← Measures effectiveness of Phases 2-5
    ↓
Phase 7 (CI/CD) ← Automates Phases 2-6
    ↓
Phase 8 (Validation) ← Validates quality of entire test suite
```

**Key Relationships:**

- **Phase 2 (Unit Tests)** is the foundation - prioritize this

- **Phase 4 (Mocks)** enhances Phase 2-3 by isolating dependencies

- **Phase 6 (Coverage)** identifies gaps in Phases 2-3

- **Phase 7 (CI/CD)** automates execution of all previous phases

- **Phase 8 (Validation)** validates effectiveness of entire suite

### 4.3 Expected Outcomes

#### FIRST Principles

All generated unit tests follow FIRST principles:

- **Fast:** Tests run in <1 second each

- **Independent:** No test depends on another

- **Repeatable:** Same results every run

- **Self-validating:** Clear pass/fail with no manual checking

- **Timely:** Written close to production code

#### AAA Pattern

Tests follow Arrange-Act-Assert structure:

```python
def test_user_registration():
    # Arrange: Set up test data and dependencies
    user_data = {"email": "test@example.com", "password": "secure123"}
    user_service = UserService()

    # Act: Execute the operation being tested
    result = user_service.register_user(user_data)

    # Assert: Verify expected outcomes
    assert result.success is True
    assert result.user_id is not None
    assert result.email == "test@example.com"
```

#### 80%+ Code Coverage

**Target:** Achieve and maintain 80%+ code coverage

**What Gets Covered:**
- All critical business logic

- Edge cases and error handling

- Public API interfaces

- Integration points

- Configuration and setup code

**What Can Skip:**
- Trivial getters/setters

- Generated code

- Third-party library wrappers

- Deprecated code scheduled for removal

#### Test Metrics

**Quantity:**
- Unit Tests: 20-30 tests per 500 LOC

- Integration Tests: 5-10 tests per major feature

- E2E Tests: 3-5 tests per user workflow

**Quality:**
- Mutation Score: >80% (Phase 8)

- Test Execution Time: <5 minutes total for unit tests

- Flakiness: <1% false positive rate

- Maintainability: Tests are readable and well-documented

#### Anti-Patterns Avoided

Generated tests avoid common anti-patterns:

❌ **Test Interdependence:** Tests don't rely on execution order
❌ **Hidden Dependencies:** No global state or singletons
❌ **Magic Numbers:** All test data is clearly explained
❌ **Over-Mocking:** Only mock external dependencies
❌ **Assertion Roulette:** Clear, specific assertions
❌ **Test Duplication:** DRY principles apply to tests too

### 4.4 Verification

#### Running Tests

**Python:**
```bash
# Run all tests
pytest tests/

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_user_service.py -v
```

**JavaScript:**
```bash
# Run all tests
npm test

# With coverage
npm run test:coverage

# Watch mode
npm test -- --watch
```

**Java:**
```bash
# Maven
mvn test

# Gradle
./gradlew test

# With coverage
mvn test jacoco:report
```

**C#:**
```bash
# .NET
dotnet test

# With coverage
dotnet test /p:CollectCoverage=true

# Specific test
dotnet test --filter "FullyQualifiedName~UserServiceTests"
```

**Go:**
```bash
# Run all tests
go test ./...

# With coverage
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out

# Verbose
go test ./... -v
```

**C:**
```bash
# Unity framework
ruby test/test_runner.rb

# CUnit
./test_runner

# With coverage (gcov)
gcc -fprofile-arcs -ftest-coverage src/*.c tests/*.c
./test_runner
gcov src/*.c
```

**C++:**
```bash
# GoogleTest
./build/test_runner

# With coverage (lcov)
./build/test_runner
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html

# VS Code: Press Ctrl+Shift+B (build), then F5 (debug tests)
```

#### Code Coverage Verification

**Check Coverage Thresholds:**

```bash
# Python (pytest-cov)
pytest tests/ --cov=src --cov-fail-under=80

# JavaScript (Jest)
npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'

# Java (JaCoCo)
mvn verify # Fails if coverage < 80% (configured in pom.xml)

# C# (Coverlet)
dotnet test /p:Threshold=80 /p:ThresholdType=line

# Go
go test ./... -coverprofile=coverage.out
go tool cover -func=coverage.out | grep total # Should show >80%
```

**Coverage Report Review:**

- [ ] Overall coverage meets 80%+ threshold

- [ ] Critical business logic has 90%+ coverage

- [ ] All public APIs covered

- [ ] Edge cases and error paths tested

- [ ] No untested code in critical sections

#### Test Quality Validation

**Mutation Testing (Phase 8):**

```bash
# Python (mutmut)
mutmut run
mutmut results # Should show >80% killed mutations

# JavaScript (Stryker)
npx stryker run # Should achieve >80% mutation score

# Java (PIT)
mvn org.pitest:pitest-maven:mutationCoverage

# C# (Stryker.NET)
dotnet stryker
```

**Quality Checklist:**

- [ ] Mutation score >80%

- [ ] No surviving mutations in critical code

- [ ] Tests fail when code changes incorrectly

- [ ] Tests pass consistently (no flakiness)

- [ ] Tests are readable and maintainable

- [ ] Test names clearly describe what's being tested

- [ ] Failure messages are informative

#### CI/CD Integration Verification

**Pipeline Checks:**

- [ ] Tests run automatically on every commit

- [ ] Tests run on multiple environments (OS, language versions)

- [ ] Coverage reports generated and published

- [ ] Quality gates prevent merging if tests fail

- [ ] Test results visible in PR/MR comments

- [ ] Performance tests run on scheduled basis

- [ ] Notifications sent on test failures

**Pipeline Configuration Files:**

- GitHub Actions: `.github/workflows/test.yml`

- GitLab CI: `.gitlab-ci.yml`

- Jenkins: `Jenkinsfile`

- Travis CI: `.travis.yml`

#### C++ Google Test + VS Code + Copilot Workflow (Special)

**NEW in v0.3.0:** Streamlined C++ testing with 10-minute setup!

**Features:**
- ✅ One-click build (Ctrl+Shift+B) and test execution

- ✅ Seamless debugging with breakpoints (F5)

- ✅ GitHub Copilot auto-generates 15+ comprehensive tests

- ✅ Automated code coverage reports

- ✅ Complete VS Code integration (tasks, debugging, IntelliSense)

**Quick Start:**

1. **Read the Guide:** [GOOGLE_TEST_VSCODE_WORKFLOW.md](../templates/tests_generation/GOOGLE_TEST_VSCODE_WORKFLOW.md)

2. **Follow 10 Steps:**
   - Setup (Steps 1-4): Install tools, clone repo, build - 5 min

   - Generate Tests (Steps 5-7): Use Copilot prompts - 3 min

   - Verify (Steps 8-10): Run tests, check coverage - 2 min

3. **Use Quick Reference:** [COPILOT_QUICK_REFERENCE.md](../templates/tests_generation/unit_tests/COPILOT_QUICK_REFERENCE.md)

**One-Line Copilot Prompts:**

```
Generate comprehensive GoogleTest unit tests for [ClassName] following AAA pattern with FIRST principles, testing all public methods including edge cases, error handling, and boundary conditions

Generate GoogleTest fixtures and helper functions to support testing [ClassName], including setup/teardown, test data builders, and common assertions
```

**Perfect For:** C++ developers using VS Code + GitHub Copilot who want instant, professional test generation

---

## Part 5: Code Review

### 5.1 6-Phase Review Methodology

This repository provides a systematic 6-phase code review methodology that analyzes your codebase from context to final report.

#### Phase Overview

| Phase | Purpose | Time Estimate | Output |
|-------|---------|---------------|--------|
| **1. Context Analysis** | Understand project structure and architecture | 2-3 hours | Architecture map, dependency analysis |
| **2. Code Quality** | Evaluate maintainability and best practices | 2-3 hours | Quality issues by severity |
| **3. Security Review** | Identify vulnerabilities and risks | 2-3 hours | OWASP Top 10 findings |
| **4. Performance Review** | Detect bottlenecks and optimization opportunities | 2-3 hours | Performance issues and fixes |
| **5. Testing Review** | Assess test coverage and quality | 2 hours | Test gaps and improvements |
| **6. Final Report** | Consolidated findings with action plan | 1 hour | Prioritized remediation roadmap |

**Total Time:** 10-15 hours for comprehensive 6-phase review

**Quick Review (4 hours):** Run only Phases 1-2 for basic analysis

#### Phase 1: Context Analysis (START HERE)

**Objective:** Understand the project before reviewing code

**What You Get:**
- Project structure overview

- Architecture pattern identification

- Technology stack analysis

- Dependency mapping

- Build/deployment process understanding

- Key abstractions and patterns

**Why First:** Context prevents misunderstandings in later phases

**Templates:** [templates/code_review/context_analysis/](../templates/code_review/context_analysis/)

#### Phase 2: Code Quality

**Objective:** Evaluate maintainability and coding standards

**What You Get:**
- Code style violations

- Complexity analysis (cyclomatic complexity)

- Code smells and anti-patterns

- Naming convention issues

- Documentation gaps

- Refactoring opportunities

**Templates:** [templates/code_review/code_quality/](../templates/code_review/code_quality/)

#### Phase 3: Security Review

**Objective:** Identify security vulnerabilities

**What You Get:**
- OWASP Top 10 vulnerability scan

- Input validation issues

- Authentication/authorization gaps

- Data exposure risks

- Dependency vulnerabilities

- Security misconfigurations

- Secrets in code detection

**Templates:** [templates/code_review/security_review/](../templates/code_review/security_review/)

#### Phase 4: Performance Review

**Objective:** Find performance bottlenecks

**What You Get:**
- Algorithmic complexity issues (O(n²) → O(n))

- Memory leaks and inefficiencies

- Database query optimization

- Caching opportunities

- Resource management issues

- Profiling recommendations

**Templates:** [templates/code_review/performance_review/](../templates/code_review/performance_review/)

#### Phase 5: Testing Review

**Objective:** Assess test coverage and quality

**What You Get:**
- Test coverage analysis

- Test quality evaluation (FIRST principles)

- Missing test scenarios

- Flaky test identification

- Test maintenance issues

- Testing strategy recommendations

**Templates:** [templates/code_review/testing_review/](../templates/code_review/testing_review/)

#### Phase 6: Final Report (FINISH HERE)

**Objective:** Consolidated findings with actionable plan

**What You Get:**
- Executive summary

- All findings categorized by severity (CRITICAL/HIGH/MEDIUM/LOW)

- Specific file locations and line numbers

- Before/after code examples

- Prioritized action plan

- Time estimates for remediation

- Risk assessment

**Run This Last:** After completing all previous phases

**Templates:** [templates/code_review/final_report/](../templates/code_review/final_report/)

### 5.2 Template Usage

#### Phase Dependencies

Phases build on each other:

```
Phase 1 (Context Analysis) ← ALWAYS START HERE
    ↓
Phase 2 (Code Quality)
    ↓
Phase 3 (Security Review) ← Can run in parallel with Phase 4
    ↓
Phase 4 (Performance Review) ← Can run in parallel with Phase 3
    ↓
Phase 5 (Testing Review)
    ↓
Phase 6 (Final Report) ← ALWAYS FINISH HERE
```

#### Time Estimates Per Phase

**Phase 1: Context Analysis (2-3 hours)**
- Small project (<5k LOC): 1-2 hours

- Medium project (5k-20k LOC): 2-3 hours

- Large project (>20k LOC): 3-4 hours

**Phase 2: Code Quality (2-3 hours)**
- Varies by code quality and size

- More technical debt = longer analysis

**Phase 3: Security Review (2-3 hours)**
- Web applications: 3-4 hours (more attack surface)

- Libraries/CLI tools: 1-2 hours

**Phase 4: Performance Review (2-3 hours)**
- Performance-critical apps: 3-4 hours

- Standard applications: 2-3 hours

**Phase 5: Testing Review (2 hours)**
- Consistent across project sizes

- More if test suite is large and complex

**Phase 6: Final Report (1 hour)**
- Mostly consolidation and prioritization

- Time-consistent across projects

#### Review Strategies

**Strategy 1: Comprehensive Review (10-12 hours)**
```
Use Case: Pre-release audit, major refactor, new team onboarding
Phases: Run all 6 phases sequentially
Time: 10-15 hours
Best For: Critical codebases, production deployments
```

**Strategy 2: Quick Review (4 hours)**
```
Use Case: Rapid assessment, pull request review
Phases: 1 (Context) + 2 (Quality)
Time: 4-6 hours
Best For: Feature branches, quick health checks
```

**Strategy 3: Security-Focused (6 hours)**
```
Use Case: Security audit, compliance requirement
Phases: 1 (Context) + 3 (Security) + 6 (Report)
Time: 5-7 hours
Best For: Security reviews, penetration testing prep
```

**Strategy 4: Performance-Focused (6 hours)**
```
Use Case: Performance issues, optimization project
Phases: 1 (Context) + 4 (Performance) + 6 (Report)
Time: 5-7 hours
Best For: Performance bottlenecks, scalability concerns
```

**Strategy 5: Test Coverage Review (5 hours)**
```
Use Case: Improve test suite
Phases: 1 (Context) + 5 (Testing) + 6 (Report)
Time: 4-6 hours
Best For: Test quality improvements, coverage gaps
```

### 5.3 Interpreting Results

#### Severity Classification

All findings are classified by severity:

**🔴 CRITICAL (Immediate Action Required)**
- Security vulnerabilities with active exploits

- Data loss risks

- Authentication/authorization bypasses

- Production-breaking bugs

- Critical performance issues (app unusable)

**Example:**
```
CRITICAL: SQL Injection in UserController.login()
Location: src/controllers/UserController.java:45
Risk: Attackers can access all user data, modify database
Remediation: Use parameterized queries (2 hours)
```

**🟠 HIGH (Fix Within 1 Week)**
- Security vulnerabilities without known exploits

- Major performance bottlenecks

- Data integrity issues

- Significant code quality problems

- Missing critical tests

**Example:**
```
HIGH: Hardcoded API credentials in config
Location: src/config/api.py:12
Risk: Credentials exposed in version control
Remediation: Move to environment variables (1 hour)
```

**🟡 MEDIUM (Fix Within 1 Month)**
- Minor security issues

- Moderate performance issues

- Code maintainability problems

- Incomplete documentation

- Test coverage gaps

**Example:**
```
MEDIUM: N+1 query in UserService.getOrders()
Location: src/services/UserService.js:89
Impact: Slow response time with many orders
Remediation: Add join or eager loading (3 hours)
```

**🟢 LOW (Fix When Convenient)**
- Code style violations

- Minor refactoring opportunities

- Documentation improvements

- Nice-to-have optimizations

**Example:**
```
LOW: Complex function exceeds 50 lines
Location: src/utils/parser.py:123-189
Impact: Reduced readability
Remediation: Split into smaller functions (2 hours)
```

#### Finding Format

Each finding includes:

**1. Severity Level:** CRITICAL/HIGH/MEDIUM/LOW

**2. Issue Title:** Brief description

**3. Location:** Exact file path and line numbers
```
File: src/services/UserService.java
Lines: 45-52
```

**4. Description:** What the problem is and why it matters

**5. Code Example:** Before and after
```python
# Before (vulnerable)
query = f"SELECT * FROM users WHERE id = {user_id}"
cursor.execute(query)

# After (secure)
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

**6. Impact:** Consequences of not fixing

**7. Remediation:** Specific steps to fix
- Exact changes needed

- Estimated time

- Testing requirements

**8. References:** Links to documentation, CVEs, best practices

#### Prioritization

**Recommended Fix Order:**

1. **CRITICAL issues first** (immediate action)
   - Security vulnerabilities

   - Data loss risks

   - Production-breaking bugs

2. **HIGH issues within 1 week**
   - Major security concerns

   - Significant performance bottlenecks

   - Data integrity risks

3. **MEDIUM issues within 1 month**
   - Code quality problems

   - Moderate performance issues

   - Test coverage gaps

4. **LOW issues when convenient**
   - Code style

   - Documentation

   - Minor refactoring

**Risk-Based Prioritization:**

Consider these factors:

- **Exploitability:** How easy is it to exploit? (Security)

- **Impact:** What's the worst-case outcome?

- **Likelihood:** How often does this code execute?

- **Visibility:** Is this public-facing or internal?

- **Compliance:** Does this violate regulations?

### 5.4 Acting on Findings

#### Remediation Strategies

**1. Create Remediation Plan**

From Final Report, extract:
- All CRITICAL/HIGH findings

- Estimated time for each

- Dependencies between fixes

- Testing requirements

**Example Plan:**
```markdown
## Remediation Roadmap

### Sprint 1 (Critical - Week 1)
- [ ] Fix SQL injection in UserController (2h) → Test (1h)

- [ ] Remove hardcoded credentials (1h) → Test (30m)

- [ ] Patch authentication bypass (3h) → Security test (2h)

### Sprint 2 (High - Week 2)
- [ ] Add input validation to API endpoints (4h) → Test (2h)

- [ ] Fix N+1 query in OrderService (3h) → Performance test (1h)

- [ ] Implement rate limiting (2h) → Load test (1h)

### Sprint 3 (Medium - Week 3-4)
- [ ] Improve test coverage to 80% (8h)

- [ ] Refactor complex functions (4h) → Test (2h)

- [ ] Add missing documentation (4h)
```

**2. Assign Ownership**

- Assign each finding to specific developer

- Set deadlines based on severity

- Track progress in issue tracker

**3. Implement Fixes**

**Best Practices:**
- Fix one issue per commit (clear history)

- Write tests before fixing (TDD approach)

- Have fixes reviewed by another developer

- Update documentation if behavior changes

- Add regression tests

**Example Workflow:**
```bash
# 1. Create branch for fix
git checkout -b fix/sql-injection-user-controller

# 2. Write test that demonstrates vulnerability
# tests/security/test_sql_injection.py

# 3. Implement fix
# src/controllers/UserController.java

# 4. Verify test now passes
npm test tests/security/

# 5. Commit with clear message
git commit -m "fix: Prevent SQL injection in UserController.login()

- Replace string concatenation with parameterized query

- Add input validation for user_id parameter

- Add security test coverage

Fixes: CRITICAL-001 (Security Review Phase 3)"

# 6. Push and create pull request
git push origin fix/sql-injection-user-controller
```

**4. Verify Fixes**

After implementing fixes:

- [ ] Original issue is resolved

- [ ] No new issues introduced (regression testing)

- [ ] Tests pass (unit, integration, security)

- [ ] Performance hasn't degraded

- [ ] Documentation updated

- [ ] Code review approved

**5. Track Progress**

Use Final Report as baseline:

- Create issues in tracker (GitHub Issues, Jira, etc.)

- Label by severity (critical, high, medium, low)

- Assign to milestones/sprints

- Update status as fixes are implemented

- Re-run affected review phases to verify

**Example Issue:**
```markdown
Title: [CRITICAL] SQL Injection in UserController.login()

Labels: security, critical, code-review
Milestone: Sprint 1
Assignee: @developer

Description:
Code Review Phase 3 identified SQL injection vulnerability.

**Location:** src/controllers/UserController.java:45
**Severity:** CRITICAL
**Estimated Fix Time:** 2 hours
**Testing Time:** 1 hour

**Remediation:**
Replace string concatenation with parameterized query.
See: https://owasp.org/www-community/attacks/SQL_Injection

**Acceptance Criteria:**
- [ ] Parameterized query implemented

- [ ] Input validation added

- [ ] Security test passes

- [ ] Code review approved
```

#### Re-Review After Fixes

After implementing fixes, consider re-running phases:

**Partial Re-Review (2-4 hours):**
- Re-run phases where fixes were made

- Verify issues resolved

- Check for regressions

**Example:**
```
Fixed security issues? → Re-run Phase 3 (Security Review)
Fixed performance issues? → Re-run Phase 4 (Performance Review)
```

**Full Re-Review (10-15 hours):**
- After major refactoring

- Before production release

- Quarterly code health checks

---

## Part 6: Compliance & Governance

### 6.1 Overview and Business Value

Compliance & Governance templates help implement regulatory frameworks, security governance, and risk management for production systems.

**Available Frameworks (96 templates):**
- **SOC 2 Type II** - Trust Services Criteria for enterprise customers
- **ISO 27001:2022** - Information Security Management Systems (114 controls)
- **ISO 42001:2023** - AI Management Systems (NEW for 2025)
- **NIST AI RMF 1.0** - AI Risk Management Framework
- **PCI-DSS v4.0** - Payment Card Industry Data Security Standard
- **GDPR/CCPA** - Privacy protection regulations
- **AI Agent Governance** - 4 Pillars Framework for agentic AI
- **Incident Response** - NIST SP 800-61 6-phase lifecycle

**Time Investment:** 6-12 hours per framework (manual with AI assistance)

**Location:** [templates/compliance_governance/](../templates/compliance_governance/)

### 6.2 When to Use Compliance Templates

**For Traditional SaaS:**
- **SOC 2 + ISO 27001** - Enterprise trust and security
- **Use Case**: Enterprise sales require SOC 2 reports
- **Time**: 12-20 hours per framework

**For AI/ML Systems:**
- **NIST AI RMF + ISO 42001 + AI Agent Governance** - AI-specific compliance
- **Use Case**: Demonstrate trustworthy AI deployment
- **Time**: 18-30 hours for complete AI governance

**For Payment Processing:**
- **PCI-DSS + SOC 2** - Payment security + trust
- **Use Case**: Processing credit card payments
- **Time**: 15-25 hours

**For EU Markets:**
- **GDPR + ISO 27001** - Privacy + information security
- **Use Case**: Serving EU customers
- **Time**: 12-20 hours

### 6.3 The Four Pillars of AI Agent Governance

Modern AI systems require specialized governance. The **4 Pillars Framework** addresses unique AI risks:

#### Pillar 1: 🔄 Lifecycle Management (Separation of Duties)
**Definition**: Multiple teams manage data/model changes through dev/staging/prod environments

**What You'll Implement:**
- Git + model registries for version control
- CI/CD pipelines for AI deployments
- Blue-green and canary deployment strategies
- Approval gates and rollback procedures
- Feature flags for gradual rollout

**Templates:** [ai_agent_governance/lifecycle_management/](../templates/compliance_governance/ai_agent_governance/)

#### Pillar 2: ⚠️ Risk Management (Defense in Depth)
**Definition**: Multiple overlapping defense layers (PII detection, guardrails, compliance controls)

**What You'll Implement:**
- Data quality monitoring (schema validation, drift detection)
- PII detection and automatic redaction
- Input/output guardrails
- Compliance controls (audit trails, retention policies)
- Model validation (bias detection, performance monitoring)

**Templates:** [ai_agent_governance/agent_risk_controls/](../templates/compliance_governance/ai_agent_governance/)

#### Pillar 3: 🔒 Security (Least Privilege Access)
**Definition**: Agents and users receive only minimum required permissions

**What You'll Implement:**
- OAuth 2.0, SSO (SAML, OIDC), multi-factor authentication
- Secrets management (key vaults, credential rotation)
- RBAC with group permissions
- Data encryption (TLS/SSL, encryption at rest)
- Network security (private networks, firewalls)

**Templates:** [ai_agent_governance/agent_security/](../templates/compliance_governance/ai_agent_governance/)

#### Pillar 4: 🔍 Observability (Audit Everything)
**Definition**: Comprehensive logs of all system interactions for complete traceability

**What You'll Implement:**
- OTel (OpenTelemetry) tracing standard
- Audit logging for all agent actions
- Performance monitoring and cost dashboards
- Data and model lineage tracking
- Anomaly detection and alerting

**Templates:** [ai_agent_governance/agent_observability/](../templates/compliance_governance/ai_agent_governance/)

### 6.4 Template Usage

#### Step 1: Choose Your Framework

**Decision Tree:**
```
What type of system?

├─ Traditional SaaS → SOC 2 + ISO 27001
├─ AI/ML Platform → NIST AI RMF + ISO 42001 + 4 Pillars
├─ Payment Processing → PCI-DSS + SOC 2
└─ EU Market → GDPR + ISO 27001
```

#### Step 2: Follow Template Structure

Each compliance template includes:

1. **Overview** - Framework purpose, scope, business value
2. **Compliance Requirements** - Control objectives, evidence needs
3. **Code-Level Implementation** - Language-specific security patterns
4. **Documentation Requirements** - Policy templates, evidence artifacts
5. **Risk Assessment** - Threat modeling, risk scoring
6. **Audit Preparation** - Evidence gathering, gap analysis
7. **Continuous Monitoring** - Ongoing compliance, alerting
8. **Cross-References** - Links to security_review, tests_generation

#### Step 3: Implement Controls

**Example: SOC 2 Implementation (8-12 hours)**

```
1. Use Template (2 hours)
   - Open templates/compliance_governance/compliance_frameworks/python_soc2_compliance.md
   - Copy prompt template into your AI assistant
   - Provide your codebase context

2. Implement Security Controls (4-6 hours)
   - Map Trust Services Criteria to your code
   - Implement missing controls (encryption, access control, logging)
   - Add security tests

3. Generate Documentation (2-3 hours)
   - Create policy templates
   - Document evidence collection procedures
   - Generate audit checklists

4. Continuous Monitoring (1-2 hours)
   - Set up automated compliance checks
   - Configure alerting for violations
   - Integrate into CI/CD
```

### 6.5 Integration with Existing Templates

**Compliance builds on security and testing:**

```
Security Review (Part 5)
  ↓
Identify vulnerabilities → Fix → Implement Controls
  ↓
Compliance Frameworks (Part 6)
  ↓
Map controls to code → Document → Audit Prep
  ↓
Tests Generation (Part 4)
  ↓
Generate compliance tests → 85%+ coverage → CI/CD
```

**Example Workflow:**

```
1. Run Security Review (Phase 3)
   - Find: 2 CRITICAL, 5 HIGH security issues
   - Time: 2-3 hours

2. Fix Critical Issues
   - SQL injection, hardcoded secrets
   - Time: 4-6 hours

3. Implement SOC 2 Controls
   - Map to Trust Services Criteria
   - Implement missing controls
   - Time: 8-12 hours

4. Generate Compliance Tests
   - Create security tests for all controls
   - Achieve 85%+ coverage
   - Time: 6-8 hours

5. Audit Preparation
   - Document evidence collection
   - Create audit checklist
   - Time: 2-3 hours

Total Time: 22-32 hours for SOC 2-compliant, auditable codebase
```

### 6.6 Expected Outcomes

**After Implementing Compliance Templates:**

✅ **Technical Achievements:**
- All framework controls implemented in code
- Security tests passing at 85%+ coverage
- Automated evidence collection operational
- Continuous compliance monitoring active
- Audit-ready documentation generated

✅ **Business Benefits:**
- Pass SOC 2/ISO 27001 audits on first attempt
- Accelerate enterprise sales cycles (trust badges)
- Meet regulatory requirements (GDPR, CCPA, PCI-DSS)
- Reduce audit preparation time by 50-60%
- Demonstrate trustworthy AI deployment (for AI systems)

✅ **Risk Management:**
- Defense-in-depth security implemented
- PII detection and redaction operational
- Incident response plans documented
- Breach notification procedures ready (GDPR 72-hour compliance)

### 6.7 Verification Steps

**After Completing Compliance Implementation:**

- [ ] All framework controls mapped to codebase
- [ ] Security controls implemented and tested
- [ ] Policy documentation generated
- [ ] Evidence collection procedures documented
- [ ] Audit preparation checklist complete
- [ ] Continuous monitoring operational
- [ ] CI/CD includes compliance checks
- [ ] Compliance tests passing at 85%+
- [ ] No CRITICAL/HIGH security findings remaining

**Audit Readiness Checklist:**

- [ ] Control implementation evidence collected
- [ ] Policy documentation reviewed by legal/compliance
- [ ] Access logs demonstrate least privilege
- [ ] Encryption verified for data at rest and in transit
- [ ] Incident response plan tested
- [ ] Vendor risk assessments complete
- [ ] Security training documented
- [ ] Third-party audit scheduled

### 6.8 Resources and Tools

**Official Framework Documentation:**
- [SOC 2 Trust Services Criteria](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/trustdataintegrity.html)
- [ISO 27001:2022 Standard](https://www.iso.org/standard/27001)
- [ISO 42001:2023 AI Management](https://www.iso.org/standard/81230.html)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [PCI-DSS v4.0 Requirements](https://www.pcisecuritystandards.org/document_library)
- [GDPR Official Text](https://gdpr-info.eu/)
- [CCPA Official Text](https://oag.ca.gov/privacy/ccpa)

**Compliance Automation Tools:**
- **Drata, Vanta, Secureframe** - SOC 2/ISO 27001 automation
- **OneTrust, BigID** - Privacy compliance (GDPR/CCPA)
- **OpenTelemetry, MLflow** - AI observability
- **Open Policy Agent (OPA)** - Policy as code

---

## Part 7: Codebase Cleanup

### 7.1 Process Overview

Codebase cleanup systematically removes technical debt: dead code, duplication, and outdated patterns.

**Objective:** Lean, maintainable codebase with reduced complexity

**Time Estimate:** 4-8 hours depending on codebase size and debt level

**Risk Level:** Moderate (changes can introduce regressions)

**Prerequisites:**
- Comprehensive test suite (80%+ coverage recommended)

- Version control (Git)

- Backup/branch for rollback

- Time for thorough testing after cleanup

#### Multi-Pass Validation

Cleanup follows an iterative, safe approach:

**Pass 1: Analysis (1-2 hours)**
1. Identify dead code candidates
2. Find duplicate logic
3. Detect outdated patterns
4. Catalog refactoring opportunities
5. Assess risk and effort

**Pass 2: Low-Risk Cleanup (1-2 hours)**
1. Remove unused imports
2. Delete commented-out code
3. Remove debug print statements
4. Fix formatting inconsistencies
5. Run tests → Verify no regressions

**Pass 3: Medium-Risk Cleanup (2-3 hours)**
1. Remove unused functions/classes
2. Consolidate duplicate code
3. Simplify complex conditionals
4. Update deprecated API usage
5. Run tests → Verify no regressions

**Pass 4: High-Risk Refactoring (2-4 hours)**
1. Modernize legacy patterns
2. Refactor complex modules
3. Update architecture patterns
4. Run tests → Verify no regressions
5. Manual verification of critical paths

#### Stopping Criteria

Stop cleanup when:

✅ **Goals Met:**
- All dead code removed

- Duplication reduced to acceptable levels (<5%)

- No critical outdated patterns remain

- Tests still pass at 80%+ coverage

⚠️ **Risk Threshold Reached:**
- Further changes require architectural redesign

- Test coverage drops below 80%

- Changes introduce flaky tests

- Time budget exceeded

🛑 **Safety Concerns:**
- Tests start failing

- Critical functionality affected

- Unable to verify changes safely

### 6.2 Template Usage

#### Language-Specific Cleanup Templates

Each language has a tailored cleanup template:

**Python:** [templates/code_cleanup/python_cleanup.md](../templates/code_cleanup/python_cleanup.md)
- Unused imports (isort, autoflake)

- Empty lines and whitespace

- Debug print statements

- Type hint improvements

- Modern Python idioms (f-strings, dataclasses, etc.)

**JavaScript/TypeScript:** [templates/code_cleanup/javascript_cleanup.md](../templates/code_cleanup/javascript_cleanup.md)
- Unused imports/exports

- console.log debugging

- ES6+ modernization (let/const, arrow functions, async/await)

- TypeScript type improvements

- npm dependency cleanup

**Java:** [templates/code_cleanup/java_cleanup.md](../templates/code_cleanup/java_cleanup.md)
- Unused imports/methods

- System.out debugging

- Lambda and Stream API opportunities

- Modern Java features (records, pattern matching)

- Maven/Gradle dependency cleanup

**C#:** [templates/code_cleanup/csharp_cleanup.md](../templates/code_cleanup/csharp_cleanup.md)
- Unused usings

- Console.WriteLine debugging

- Modern C# features (records, pattern matching, nullable types)

- LINQ improvements

- NuGet package cleanup

**Go:** [templates/code_cleanup/go_cleanup.md](../templates/code_cleanup/go_cleanup.md)
- Unused imports

- fmt.Println debugging

- Idiomatic Go patterns

- go vet and staticcheck findings

- Module cleanup

**C:** [templates/code_cleanup/c_cleanup.md](../templates/code_cleanup/c_cleanup.md)
- Unused includes

- Memory leaks (Valgrind)

- Buffer overflows

- MISRA-C / CERT-C compliance

- Embedded systems patterns

**C++:** [templates/code_cleanup/cpp_cleanup.md](../templates/code_cleanup/cpp_cleanup.md)
- Unused includes

- Raw pointers → Smart pointers

- Manual memory management → RAII

- Modern C++ features (C++11/14/17/20)

- Static analysis (clang-tidy)

#### What Gets Removed

**Dead Code:**
- Unused functions, classes, variables

- Unreachable code paths

- Commented-out code

- Deprecated feature flags

- Old migration code

**Duplication:**
- Copy-pasted functions with minor variations

- Repeated logic across modules

- Duplicate test setups

- Similar utility functions

**Outdated Patterns:**
- Deprecated API usage

- Legacy coding styles

- Old language features (before modernization)

- Obsolete architecture patterns

- Manual implementations of standard library features

**Debug/Development Artifacts:**
- Print/console debugging statements

- Temporary test code

- Development-only configurations

- Commented-out debug code

- TODO comments for completed tasks

**Import/Dependency Cleanup:**
- Unused imports/includes

- Redundant dependencies

- Outdated package versions

- Transitive dependencies no longer needed

### 6.3 Post-Cleanup Verification

#### Essential Verification Steps

**1. Run All Tests**

```bash
# Python
pytest tests/ --cov=src --cov-report=term --cov-fail-under=80

# JavaScript
npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'

# Java
mvn test

# C#
dotnet test

# Go
go test ./... -cover

# C
./test_runner && gcov src/*.c

# C++
./build/test_runner
```

**Verification:**
- [ ] All tests pass

- [ ] No new test failures

- [ ] Test coverage maintained at 80%+

- [ ] No flaky tests introduced

**2. Manual Verification of Critical Paths**

Test critical functionality manually:

- [ ] Application starts successfully

- [ ] User login/authentication works

- [ ] Core business operations function

- [ ] Data persistence operates correctly

- [ ] External integrations still work

**3. Code Review the Changes**

```bash
# Review diff before committing
git diff

# Or use a diff tool
git difftool
```

**Check for:**
- [ ] No unintended deletions

- [ ] Refactoring logic is correct

- [ ] No commented-out code remains

- [ ] Imports/includes still valid

- [ ] No broken references

**4. Run Static Analysis**

```bash
# Python
flake8 src/
mypy src/
pylint src/

# JavaScript
npm run lint
npm run type-check

# Java
mvn checkstyle:check
mvn spotbugs:check

# C#
dotnet format --verify-no-changes
dotnet build /p:TreatWarningsAsErrors=true

# Go
go vet ./...
staticcheck ./...
golangci-lint run

# C
cppcheck --enable=all src/
splint src/*.c

# C++
clang-tidy src/*.cpp
cppcheck --enable=all src/
```

**Verification:**
- [ ] No new warnings introduced

- [ ] Code quality metrics improved or stable

- [ ] No new code smells

**5. Performance Verification**

```bash
# Python
python -m pytest tests/ --benchmark-only

# JavaScript
npm run benchmark

# Java
mvn clean test -Pbenchmark

# C#
dotnet run --configuration Release --project Benchmarks

# Go
go test -bench=. ./...

# C/C++
# Run profiling tools (gprof, valgrind, perf)
```

**Verification:**
- [ ] Performance hasn't degraded

- [ ] No new memory leaks

- [ ] Response times stable or improved

**6. Build Verification**

```bash
# Python
python -m build

# JavaScript
npm run build

# Java
mvn clean package

# C#
dotnet build --configuration Release

# Go
go build ./...

# C
make clean && make

# C++
cmake --build build --config Release
```

**Verification:**
- [ ] Project builds successfully

- [ ] No new build warnings/errors

- [ ] Build artifacts generated correctly

- [ ] Dependencies resolved properly

#### Cleanup Success Criteria

✅ **Code Quality Improved:**
- Dead code removed

- Duplication reduced (<5% similar code)

- Modern patterns adopted

- Code complexity reduced

✅ **Functionality Preserved:**
- All tests pass

- Code coverage maintained (80%+)

- No regressions in critical paths

- Application behavior unchanged

✅ **Safety Maintained:**
- Git history preserved (no force pushes)

- Rollback possible via Git

- Changes reviewed and approved

- CI/CD pipeline passes

#### If Issues Arise

**If Tests Fail:**
```bash
# Identify failing test
pytest tests/ -v

# Revert specific change
git log --oneline
git revert <commit-hash>

# Or rollback entire cleanup
git reset --hard <before-cleanup-commit>
```

**If Performance Degrades:**
```bash
# Profile to identify regression
python -m cProfile -o profile.stats src/main.py
python -m pstats profile.stats

# Revert offending change
git log -p | grep -A 10 "performance-critical-function"
git revert <commit-hash>
```

**If Build Breaks:**
```bash
# Check what changed
git diff HEAD~1 HEAD

# Test each change individually
git bisect start
git bisect bad HEAD
git bisect good <last-working-commit>
```

#### Post-Cleanup Maintenance

**Update Documentation:**
- [ ] Update README if structure changed

- [ ] Revise architecture docs if patterns updated

- [ ] Update CHANGELOG.md with cleanup notes

- [ ] Document any breaking changes

**Communicate Changes:**
- [ ] Notify team of major refactoring

- [ ] Update onboarding docs if structure changed

- [ ] Add migration guide if API changed

**Monitor Production:**
- [ ] Watch error rates post-deploy

- [ ] Monitor performance metrics

- [ ] Check logs for unexpected issues

- [ ] Have rollback plan ready

---

## 🎓 Complete Workflow Example

**Scenario:** Python web API with undocumented code, no tests, security concerns, and technical debt

**Goal:** Production-ready codebase with documentation, tests, and clean code

### Step 1: Configure AI Assistant (30 minutes)

```bash
# Setup GitHub Copilot
mkdir .github
cp templates/ai_instructions/coding_assistants/python/GLOBAL_comprehensive_40k.md .github/copilot-instructions.md

# Customize for project
nano .github/copilot-instructions.md
# - Update project name
# - Add FastAPI/Flask specific patterns
# - Configure pytest settings
# - Add API-specific security guidelines

# Commit configuration
git add .github/copilot-instructions.md
git commit -m "chore: Add GitHub Copilot instructions"
```

### Step 2: Generate Documentation (6 hours)

**2.1 Docstrings (2 hours)**
```
1. Open templates/documentation_generation/docstrings/python_docstrings.md
2. Copy "Prompt Template" section
3. Paste into GitHub Copilot Chat
4. Review generated docstrings
5. Commit: git commit -m "docs: Add docstrings to all public functions"
```

**2.2 Comments (1 hour)**
```
1. Use templates/documentation_generation/comments/python_comments.md
2. Add strategic comments to complex logic
3. Commit: git commit -m "docs: Add explanatory comments"
```

**2.3 README (3 hours)**
```
1. Use templates/documentation_generation/user_docs/python_user_docs.md
2. Generate comprehensive README with:
   - Installation instructions

   - API examples

   - Configuration guide
3. Commit: git commit -m "docs: Add comprehensive README"
```

### Step 3: Generate Tests (10 hours)

**3.1 Test Structure (2 hours)**
```bash
# Use Phase 1 template
# templates/tests_generation/test_structure/python_test_structure.md

# Generated structure:
tests/
├── conftest.py
├── test_config.py
└── unit/
    ├── test_auth.py
    ├── test_users.py
    └── test_orders.py

# Install dependencies
pip install pytest pytest-cov pytest-mock

# Verify setup
pytest tests/ --collect-only
```

**3.2 Unit Tests (4 hours)**
```bash
# Use Phase 2 template
# templates/tests_generation/unit_tests/python_unit_tests.md

# Generate tests for:
# - Authentication service
# - User CRUD operations
# - Order processing logic

# Run tests
pytest tests/unit/ -v

# Check coverage
pytest tests/unit/ --cov=src --cov-report=html
open htmlcov/index.html
```

**3.3 Coverage Analysis (2 hours)**
```bash
# Use Phase 6 template
# templates/tests_generation/code_coverage/python_code_coverage.md

# Current coverage: 65%
# Identify gaps in:
# - Error handling paths
# - Edge cases
# - Integration points

# Generate additional tests for gaps
# Re-run coverage: Now 82%
```

**3.4 CI/CD Integration (2 hours)**
```yaml
# Use Phase 7 template
# templates/tests_generation/maintenance_cicd/python_maintenance_cicd.md

# Create .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]

      - run: pytest tests/ --cov=src --cov-report=xml

      - uses: codecov/codecov-action@v3
```

**Commit:**
```bash
git add tests/ .github/workflows/test.yml
git commit -m "test: Add comprehensive test suite with 82% coverage"
```

### Step 4: Code Review (8 hours)

**4.1 Context Analysis (2 hours)**
```
Template: templates/code_review/context_analysis/python_context_analysis.md

Findings:
- FastAPI application with PostgreSQL

- JWT authentication

- Microservice architecture

- Key modules: auth, users, orders, payments
```

**4.2 Code Quality (2 hours)**
```
Template: templates/code_review/code_quality/python_code_quality.md

Findings:
- 3 HIGH: Complex functions (>50 lines)

- 5 MEDIUM: Missing type hints

- 8 LOW: Code style violations
```

**4.3 Security Review (3 hours)**
```
Template: templates/code_review/security_review/python_security_review.md

Findings:
- 1 CRITICAL: SQL injection in search endpoint

- 2 HIGH: Hardcoded API keys

- 3 MEDIUM: Missing rate limiting

- 4 LOW: Debug mode enabled
```

**4.4 Final Report (1 hour)**
```
Template: templates/code_review/final_report/python_final_report.md

Consolidated Report:
- 1 CRITICAL issue (fix immediately)

- 5 HIGH issues (fix this week)

- 8 MEDIUM issues (fix this month)

- 12 LOW issues (fix when convenient)

Estimated remediation time: 16 hours
```

### Step 5: Fix Critical Issues (4 hours)

**5.1 Fix SQL Injection (2 hours)**
```python
# Before
query = f"SELECT * FROM users WHERE name LIKE '%{search_term}%'"

# After
query = "SELECT * FROM users WHERE name LIKE :search_pattern"
result = db.execute(text(query), {"search_pattern": f"%{search_term}%"})

# Add test
def test_search_prevents_sql_injection():
    malicious_input = "'; DROP TABLE users; --"
    response = client.get(f"/search?q={malicious_input}")
    assert response.status_code == 200
    # Verify no SQL injection occurred
```

**5.2 Remove Hardcoded Secrets (1 hour)**
```python
# Before
API_KEY = "sk_live_abc123xyz"

# After
import os
API_KEY = os.getenv("STRIPE_API_KEY")
if not API_KEY:
    raise ValueError("STRIPE_API_KEY environment variable required")

# Update .env.example
# STRIPE_API_KEY=your_key_here
```

**5.3 Add Rate Limiting (1 hour)**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/search")
@limiter.limit("10/minute")
async def search(q: str):
    ...
```

**Commit:**
```bash
git add src/
git commit -m "fix: Address critical security vulnerabilities

- Prevent SQL injection in search endpoint

- Move API keys to environment variables

- Add rate limiting to public endpoints

Fixes: CRITICAL-001, HIGH-001, MEDIUM-003"
```

### Step 6: Codebase Cleanup (4 hours)

**6.1 Run Cleanup Template**
```
Template: templates/code_cleanup/python_cleanup.md

Analysis:
- 147 unused imports

- 23 unused functions

- 8 large duplicated code blocks

- 45 debug print statements
```

**6.2 Automated Cleanup**
```bash
# Remove unused imports
autoflake --remove-all-unused-imports --in-place --recursive src/

# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Run tests
pytest tests/ -v
# All pass ✅
```

**6.3 Manual Cleanup**
```python
# Remove duplicate email validation
# Before: 3 copies across auth.py, users.py, orders.py
# After: 1 shared utility in utils/validation.py

def validate_email(email: str) -> bool:
    """Validate email format using RFC 5322."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

**6.4 Verification**
```bash
# Run full test suite
pytest tests/ --cov=src --cov-report=term
# Coverage: 82% (maintained) ✅

# Run linters
flake8 src/
mypy src/
# No new issues ✅

# Manual smoke test
python src/main.py
# Application starts ✅
curl http://localhost:8000/health
# {"status": "healthy"} ✅
```

**Commit:**
```bash
git add src/ tests/
git commit -m "refactor: Clean up codebase

- Remove 147 unused imports

- Delete 23 unused functions

- Consolidate duplicate validation logic

- Remove debug print statements

Tests pass, coverage maintained at 82%"
```

### Step 7: Final Verification (1 hour)

**7.1 Run Complete Test Suite**
```bash
# Local tests
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80
# PASSED ✅ Coverage: 82%

# Push to trigger CI
git push origin feature/production-ready

# Watch CI pipeline
# ✅ Tests pass
# ✅ Coverage 82%
# ✅ Linting passes
# ✅ Security scan passes
```

**7.2 Manual QA**
```bash
# Start application
docker-compose up

# Test critical paths:
# 1. User registration ✅
# 2. Login ✅
# 3. Create order ✅
# 4. Payment processing ✅
# 5. Search functionality ✅ (now SQL-injection safe)
```

**7.3 Create Pull Request**
```markdown
## Production-Ready: Documentation, Tests, Security Fixes, Cleanup

### Summary
Complete overhaul bringing codebase to production quality standards.

### Changes
- ✅ Comprehensive documentation (docstrings, README, API docs)

- ✅ 82% test coverage (unit tests + CI/CD)

- ✅ Fixed CRITICAL SQL injection vulnerability

- ✅ Removed hardcoded credentials

- ✅ Added rate limiting

- ✅ Code cleanup (removed dead code, duplication)

### Testing
- All 147 tests pass

- Coverage: 82% (target: 80%)

- Manual QA: All critical paths verified

- CI pipeline: All checks pass

### Security
- SQL injection fixed (CRITICAL-001)

- Secrets moved to environment variables (HIGH-001)

- Rate limiting added (MEDIUM-003)

### Time Investment
- Documentation: 6 hours

- Tests: 10 hours

- Code review: 8 hours

- Security fixes: 4 hours

- Cleanup: 4 hours

- **Total: 32 hours**

### Next Steps
- Deploy to staging for final validation

- Monitor error rates and performance

- Address remaining MEDIUM/LOW issues in next sprint
```

### Result

**Before:**
- ❌ No documentation

- ❌ No tests

- ❌ Critical security vulnerabilities

- ❌ Significant technical debt

**After:**
- ✅ Comprehensive documentation

- ✅ 82% test coverage with CI/CD

- ✅ Critical vulnerabilities fixed

- ✅ Clean, maintainable codebase

- ✅ Production-ready

**Time Investment:** 32 hours (4 developer-days)

---

## 🚀 Next Steps

### Continue Learning

**Explore Advanced Topics:**
- Multi-language projects (polyglot codebases)

- Microservices testing strategies

- Advanced security testing (penetration testing)

- Performance profiling and optimization

- DevOps and infrastructure as code

### Contribute Back

Found these templates useful? Consider contributing:

- Report issues or suggest improvements

- Share your custom templates

- Contribute language-specific examples

- Improve documentation

See: [Contributing Guide](CONTRIBUTING.md)

### Stay Updated

This repository is actively maintained:

- ⭐ Star the repository for updates

- 📢 Watch for new templates and features

- 📝 Check CHANGELOG.md for recent updates

### Get Help

**Questions?**
- Check [README.md](../README.md) for overview

- See [Claude Code Guide](CLAUDE_CODE_GUIDE.md) for autonomous workflows

- Review template-specific documentation

### Share Your Success

Built something great with these templates? We'd love to hear about it!

---

[← Back to Main](../README.md) | [Claude Code Guide →](CLAUDE_CODE_GUIDE.md)
