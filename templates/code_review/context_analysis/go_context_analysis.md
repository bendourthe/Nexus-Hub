---
template_id: go_context_analysis
template_name: Context Analysis - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: code_review
phase: context_analysis
phase_number: 1
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites: []
related_templates:

  - code_review/code_quality/go_code_quality.md
tools:

  - go test (1.23+)
  - testify
tags:

  - code-review
  - go
---
# Go Context Analysis

## Objective
Establish comprehensive understanding of the Go project before conducting detailed code review. This phase gathers context about purpose, architecture, dependencies, and current state to inform all subsequent review activities.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/context_analysis/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/context_analysis/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Analysis Checklist

### Project Understanding

- [ ] Project purpose and target audience identified

- [ ] Core features and use cases documented

- [ ] Development stage assessed (prototype, production, legacy)

- [ ] Key stakeholders and maintainers identified

- [ ] Project documentation reviewed (README, CONTRIBUTING, docs/)

### Architecture & Structure

- [ ] Entry points and main packages mapped

- [ ] Package organization evaluated

- [ ] Design patterns identified (factory, adapter, middleware, etc.)

- [ ] Configuration management approach documented

- [ ] Environment-specific settings catalogued

### Dependency Analysis

- [ ] Direct dependencies listed with versions (go.mod)

- [ ] Indirect dependencies reviewed

- [ ] Outdated packages identified

- [ ] Security vulnerabilities in dependencies checked

- [ ] License compatibility verified

### Build & Deployment

- [ ] Build process documented (Makefile, build scripts)

- [ ] Test execution approach understood

- [ ] CI/CD pipelines identified (GitHub Actions, GitLab CI, Jenkins)

- [ ] Deployment targets documented (containers, binaries, serverless)

- [ ] Environment variables and secrets management reviewed

### Codebase Metrics

- [ ] Lines of code measured (total, per package)

- [ ] Cyclomatic complexity assessed

- [ ] Package coupling and cohesion evaluated

- [ ] Code duplication percentage calculated

- [ ] Comment density analyzed

## Severity Classification

Use this framework to classify and prioritize all findings from the code review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**
- Security vulnerabilities (SQL injection, XSS, authentication bypass)
- Resource leaks (unclosed connections, file handles, memory leaks)
- Data loss risks (destructive operations without validation)
- Thread safety violations (race conditions, deadlocks)
- Compliance violations (GDPR, HIPAA, PCI-DSS)

**Action Required:**
- Block deployment until fixed
- Require hotfix within 24 hours
- Add tests to prevent regression
- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**
- Incorrect business logic (wrong calculations, flawed algorithms)
- Performance bottlenecks (O(n²) algorithms, missing indexes, inefficient queries)
- Memory inefficiency (loading large datasets into memory unnecessarily)
- Breaking API changes without deprecation
- Missing critical error handling (network errors, API failures not caught)

**Action Required:**
- Schedule fix in current sprint
- Cannot release without resolution
- Update documentation
- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**
- High complexity (cyclomatic complexity >10, functions >100 lines)
- Code duplication (>10 lines duplicated across modules)
- Poor naming (unclear variable/function names, inconsistent conventions)
- Missing tests (<80% coverage on critical paths)
- Incomplete error messages (no context for debugging)

**Action Required:**
- Add to backlog
- Prioritize in next sprint planning
- Consider during refactoring opportunities
- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**
- Style violations (linting warnings, formatting issues)
- Minor performance optimizations (in non-critical code paths)
- Missing documentation on helper functions
- Verbose code that could be more concise
- Debug statements left in code

**Action Required:**
- Fix opportunistically during other work
- Batch with other low-priority changes
- Good for new contributors
- Can be deferred indefinitely

---

## Severity Assignment Guidelines

**When to Escalate Severity:**
- Issue affects **production environment** → escalate one level
- Issue affects **customer-facing features** → escalate one level
- Issue has **no workaround** → escalate one level
- Issue appears in **multiple locations** → escalate one level

**When to De-escalate Severity:**
- Issue only in **test/development code** → de-escalate one level
- Issue has **easy workaround** → de-escalate one level
- Issue is **isolated to single module** → de-escalate one level
- Issue **rarely executed** (edge case) → de-escalate one level

**Examples:**
- Memory leak in production API: **HIGH → CRITICAL** (production + customer-facing)
- Style violation in test file: **LOW → Ignore** (test code + style only)
- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix (with code example if applicable)

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/services/userService:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**
- Response time degrades with user count (currently 500ms for 10k users)
- High memory usage (50MB+ per request)
- Poor scalability (can't handle >100k users)

**Recommendation:**
Move filtering to database with indexed query:

- Add database index on search fields
- Use database LIKE/ILIKE queries
- Implement pagination (limit results to 50)
- Add caching for common searches

**Effort:** 3 hours (2 hours implementation + 1 hour testing)

**Priority:** Must fix before next release (performance SLA violation)
```

---


## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Project Context Analysis

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/context_analysis"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Analysis Protocol

Please perform a comprehensive context analysis of this Go project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose, target audience, and key features
   - Identify development stage (prototype/production/legacy)
   - List primary maintainers and stakeholders

2. **Map Repository Structure**
   - Identify all source directories (cmd/, internal/, pkg/, etc.)
   - Locate test files (*_test.go)
   - Find configuration files (go.mod, go.sum, Makefile, etc.)
   - Document documentation locations (docs/, wiki, external)

## Phase 2: Architecture Understanding

1. **Entry Points & Core Packages**
   - Identify main entry points (cmd/*/main.go)
   - Map core business logic packages
   - Document public API surface (exported types/functions)
   - Identify internal vs external interfaces

2. **Design Patterns & Architecture**
   - Identify architectural style (monolithic, modular, microservices)
   - Document design patterns in use (factory, builder, strategy, etc.)
   - Map data flow through the application
   - Identify configuration and settings management approach

3. **Package Dependencies**
   - Create dependency graph between internal packages
   - Identify circular dependencies
   - Assess package coupling (tight/loose)
   - Evaluate separation of concerns

## Phase 3: Dependency Analysis

1. **Dependency Inventory**
   ```bash
   # List all dependencies
   go list -m all

   # View dependency graph
   go mod graph

   # Check for tidy dependencies
   go mod tidy -v
   ```

2. **Dependency Health Check**
   ```bash
   # Check for outdated packages
   go list -u -m all

   # Check for security vulnerabilities
   govulncheck ./...
   # or
   nancy go.sum
   ```

3. **License & Compatibility**
   - List licenses for all dependencies
   - Flag potential license conflicts
   - Identify deprecated or unmaintained packages

## Phase 4: Build & Deployment

1. **Build System**
   - Document build configuration (Makefile, build scripts, mage)
   - Identify build tools and flags
   - Review build tags and conditional compilation
   - Check for cross-compilation requirements

2. **Test Infrastructure**
   - Identify testing approaches (standard testing, testify, etc.)
   - Document test execution commands
   - Review test organization (unit, integration, e2e)
   - Assess benchmark test coverage

3. **CI/CD Pipeline**
   - Locate CI/CD configuration (.github/workflows, .gitlab-ci.yml, etc.)
   - Document automated checks (linting, testing, security scans)
   - Review deployment automation
   - Identify quality gates and merge requirements

4. **Environment Management**
   - Document environment variables and configuration
   - Review secrets management approach
   - Identify environment-specific settings (dev/staging/prod)
   - Check for .env files or configuration packages

## Phase 5: Codebase Metrics

1. **Size & Complexity Metrics**
   ```bash
   # Lines of code
   find . -name "*.go" -not -path "*/vendor/*" | xargs wc -l

   # Cyclomatic complexity
   gocyclo -over 10 .

   # Code statistics
   gocloc .
   ```

2. **Quality Indicators**
   - Calculate code-to-comment ratio
   - Measure average function length
   - Identify large files (>500 lines)
   - Count TODO/FIXME/HACK comments

3. **Duplication Analysis**
   ```bash
   # Check for code duplication
   dupl -threshold 50 .
   ```

## Phase 6: Documentation Review

1. **Code Documentation**
   - Assess godoc comment coverage (packages, types, functions)
   - Review godoc format compliance
   - Check exported identifier documentation
   - Evaluate inline comment quality

2. **Project Documentation**
   - Review README completeness
   - Check for CONTRIBUTING.md
   - Assess CHANGELOG.md or release notes
   - Review architecture documentation

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary

- **Project Name**: [name]

- **Purpose**: [1-2 sentence description]

- **Stage**: [prototype/production/legacy]

- **Go Version**: [version requirements]

- **Architecture**: [architectural style]

### Project Structure
```
project/
├── cmd/                       # Command-line applications
│   └── [app]/
│       └── main.go
├── internal/                  # Private application code
│   └── [packages]/
├── pkg/                       # Public library code
│   └── [packages]/
├── api/                       # API definitions (proto, OpenAPI)
├── configs/                   # Configuration files
├── scripts/                   # Build and utility scripts
├── test/                      # Additional test data/helpers
├── go.mod                     # Module definition
├── go.sum                     # Dependency checksums
├── Makefile                   # Build automation
└── README.md
```

### Architecture Overview

- **Design Patterns**: [patterns identified]

- **Package Organization**: [brief description]

- **Key Dependencies**: [critical external packages]

- **Configuration Approach**: [how settings are managed]

### Dependency Summary
| Package | Version | Purpose | Status | Security |
|---------|---------|---------|--------|----------|
| [name] | [version] | [usage] | [current/outdated] | [safe/vulnerable] |

### Build & Deployment

- **Build System**: [tool and configuration]

- **Test Framework**: [standard library/testify/other]

- **CI/CD**: [platform and key workflows]

- **Deployment**: [target environments]

### Codebase Metrics

- **Total Lines**: [number] (excluding tests and vendor)

- **Average Complexity**: [gocyclo score]

- **Packages**: [count]

- **Duplication**: [percentage]

- **Documentation**: [godoc coverage %]

### Go-Specific Observations

- **Go Version**: [required version from go.mod]

- **Module Path**: [module name]

- **Replace Directives**: [if any, list them]

- **Build Tags**: [if used, list common tags]

- **CGO Usage**: [yes/no and where]

### Key Findings
1. **Strengths**: [positive observations]
2. **Concerns**: [potential issues to investigate]
3. **Dependencies**: [outdated or vulnerable packages]
4. **Documentation**: [gaps or areas needing improvement]

### Recommendations for Review Focus
Based on this context, the following review areas should be prioritized:

1. [Area 1] - [reason]
2. [Area 2] - [reason]
3. [Area 3] - [reason]

### Next Steps

- [ ] Proceed with code quality review

- [ ] Conduct security audit (especially if vulnerable dependencies found)

- [ ] Perform performance analysis

- [ ] Review test coverage and quality

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/context_analysis/analysis_scripts
mkdir -p ${OUTPUT_DIR}/context_analysis/supporting_data
```

**Save files as follows**:

- Main report → `review/context_analysis/context_analysis_report.md`

- Findings data → `review/context_analysis/context_analysis_findings.json`

- Analysis scripts → `review/context_analysis/analysis_scripts/`

- Supporting data → `review/context_analysis/supporting_data/`

## Notes

- Save this context report - it will inform all subsequent review phases

- Flag any critical issues discovered during context gathering

- Update dependency vulnerabilities before detailed code review

- Use this as baseline for measuring improvement over time
~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
