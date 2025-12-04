---
template_id: csharp_context_analysis
template_name: Context Analysis - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: code_review
phase: context_analysis
phase_number: 1
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites: []
related_templates:
  - code_review/code_quality/csharp_code_quality.md
tools:
  - NUnit (4.2.2)
  - xUnit
  - MSTest
tags:
  - code-review
  - c#
---
# C# Context Analysis

## Objective
Establish comprehensive understanding of the .NET project before conducting detailed code review. This phase gathers context about purpose, architecture, dependencies, and current state to inform all subsequent review activities.

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

- [ ] Project documentation reviewed (README, docs/, XML documentation)

### Architecture & Structure

- [ ] Entry points and main assemblies mapped

- [ ] Solution and project organization evaluated

- [ ] Design patterns identified (MVVM, Repository, Factory, etc.)

- [ ] Configuration management approach documented (appsettings.json, Configuration API)

- [ ] Dependency injection container usage reviewed

### Dependency Analysis

- [ ] NuGet package dependencies listed with versions

- [ ] Development vs production dependencies separated

- [ ] Outdated packages identified

- [ ] Security vulnerabilities in packages checked

- [ ] License compatibility verified

### Build & Deployment

- [ ] Build process documented (.csproj, .sln, MSBuild)

- [ ] Test execution approach understood

- [ ] CI/CD pipelines identified (Azure DevOps, GitHub Actions, Jenkins)

- [ ] Deployment targets documented (IIS, Docker, Azure, AWS)

- [ ] Environment variables and secrets management reviewed

### Codebase Metrics

- [ ] Lines of code measured (total, per project)

- [ ] Cyclomatic complexity assessed

- [ ] Assembly coupling and cohesion evaluated

- [ ] Code duplication percentage calculated

- [ ] XML documentation coverage analyzed

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
# C# Project Context Analysis

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

Please perform a comprehensive context analysis of this C# project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose, target audience, and key features
   - Identify development stage (prototype/production/legacy)
   - List primary maintainers and stakeholders

2. **Map Repository Structure**
   - Identify solution file(s) (.sln)
   - Locate all project files (.csproj)
   - Find test projects (*.Tests, *.UnitTests, *.IntegrationTests)
   - Document configuration files (appsettings.json, web.config, app.config)
   - Locate documentation (docs/, README.md, XML doc comments)

## Phase 2: Architecture Understanding

1. **Entry Points & Core Projects**
   - Identify application entry points (Program.cs, Startup.cs, Main methods)
   - Map core business logic projects
   - Document public API surface
   - Identify project dependencies and references

2. **Design Patterns & Architecture**
   - Identify architectural style (N-tier, Clean Architecture, CQRS, etc.)
   - Document design patterns in use (Factory, Repository, Strategy, etc.)
   - Map data flow through the application
   - Identify configuration management approach (IConfiguration, Options pattern)
   - Review dependency injection setup (IServiceCollection)

3. **Project Dependencies**
   - Create dependency graph between projects
   - Identify circular dependencies
   - Assess project coupling (tight/loose)
   - Evaluate separation of concerns

## Phase 3: Dependency Analysis

1. **NuGet Package Inventory**
   - List all NuGet packages from all .csproj files
   - Document .NET/ASP.NET Core version(s)
   - Identify framework dependencies
   - Separate development packages (test frameworks, analyzers)

2. **Dependency Health Check**
   ```powershell
   # Check for outdated packages
   dotnet list package --outdated

   # Check for vulnerable packages
   dotnet list package --vulnerable

   # Check for deprecated packages
   dotnet list package --deprecated
   ```

3. **License & Compatibility**
   - List licenses for all NuGet packages
   - Flag potential license conflicts
   - Identify deprecated or unmaintained packages
   - Check .NET version compatibility

## Phase 4: Build & Deployment

1. **Build System**
   - Document build configuration (.csproj, Directory.Build.props)
   - Identify target frameworks (net8.0, net6.0, netstandard2.0, etc.)
   - Review project properties (nullable references, LangVersion)
   - Check for custom MSBuild targets or props files

2. **Test Infrastructure**
   - Identify testing frameworks (NUnit, xUnit, MSTest)
   - Document test execution commands
   - Review test configuration files (runsettings, test.csproj)
   - Assess test organization and structure

3. **CI/CD Pipeline**
   - Locate CI/CD configuration (.github/workflows, azure-pipelines.yml, etc.)
   - Document automated checks (build, test, code analysis)
   - Review deployment automation
   - Identify quality gates and merge requirements

4. **Environment Management**
   - Document configuration sources (appsettings.json, environment variables, Azure Key Vault)
   - Review secrets management approach
   - Identify environment-specific settings (Development/Staging/Production)
   - Check for user secrets (dotnet user-secrets)

## Phase 5: Codebase Metrics

1. **Size & Complexity Metrics**
   ```powershell
   # Lines of code (using Visual Studio Metrics)
   # Or third-party tools like dotnet-counters, NDepend

   # Enable code metrics in project file:
   # <GenerateDocumentationFile>true</GenerateDocumentationFile>
   # <EnableNETAnalyzers>true</EnableNETAnalyzers>
   # <AnalysisLevel>latest</AnalysisLevel>
   ```

2. **Quality Indicators**
   - Calculate code-to-comment ratio
   - Measure average method length
   - Identify large files (>500 lines)
   - Count TODO/FIXME/HACK comments
   - Review XML documentation coverage

3. **Code Analysis Results**
   ```powershell
   # Run built-in analyzers
   dotnet build /p:TreatWarningsAsErrors=true

   # Run security analyzers
   # Add SecurityCodeScan.VS2019 NuGet package
   ```

## Phase 6: Documentation Review

1. **Code Documentation**
   - Assess XML documentation coverage (public APIs)
   - Review documentation format and consistency
   - Check for nullable reference annotations
   - Evaluate inline comment quality

2. **Project Documentation**
   - Review README completeness
   - Check for CONTRIBUTING.md
   - Assess CHANGELOG.md or release notes
   - Review architecture documentation (ADRs)

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary

- **Project Name**: [name]

- **Purpose**: [1-2 sentence description]

- **Stage**: [prototype/production/legacy]

- **.NET Version**: [target framework(s)]

- **Architecture**: [architectural style]

- **Project Type**: [Web API, Console, Desktop, Class Library, etc.]

### Solution Structure
```
SolutionName/
├── src/
│   ├── ProjectName.Domain/          # Business entities
│   ├── ProjectName.Application/     # Use cases/services
│   ├── ProjectName.Infrastructure/  # Data access, external services
│   └── ProjectName.API/             # Web API or entry point
├── tests/
│   ├── ProjectName.UnitTests/
│   └── ProjectName.IntegrationTests/
├── docs/
├── SolutionName.sln
└── Directory.Build.props
```

### Architecture Overview

- **Design Patterns**: [patterns identified]

- **Project Organization**: [brief description]

- **Key Dependencies**: [critical NuGet packages]

- **Configuration Approach**: [how settings are managed]

- **DI Container**: [built-in, Autofac, etc.]

### Dependency Summary
| Package | Version | Purpose | Status | Security |
|---------|---------|---------|--------|----------|
| [name] | [version] | [usage] | [current/outdated] | [safe/vulnerable] |

### Build & Deployment

- **Build System**: [MSBuild, SDK-style project]

- **Target Framework(s)**: [net8.0, net6.0, etc.]

- **Test Framework**: [xUnit, NUnit, MSTest]

- **CI/CD**: [platform and key workflows]

- **Deployment**: [target environments - IIS, Docker, Azure App Service, etc.]

### Codebase Metrics

- **Total Projects**: [count]

- **Total Lines**: [number] (excluding tests)

- **Analyzer Warnings**: [count by severity]

- **XML Documentation**: [coverage percentage]

- **Nullable Context**: [enabled/disabled]

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

- Update vulnerable dependencies before detailed code review

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
