---
template_id: csharp_code_quality
template_name: Code Quality - C#
version: 1.0.0
last_updated: 2025-12-03
language: C#
category: code_review
phase: code_quality
phase_number: 2
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites:

  - code_review/context_analysis/csharp_context_analysis.md
related_templates:

  - code_review/security_review/csharp_security_review.md
tools:

  - NUnit (4.2.2)

  - xUnit

  - MSTest
tags:

  - code-review

  - c#
---
# C# Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to C# best practices. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/code_quality/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/code_quality/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Coding Standards

- [ ] .NET naming conventions followed (PascalCase, camelCase)

- [ ] StyleCop or Roslyn analyzer rules compliance

- [ ] XML documentation on public APIs

- [ ] Nullable reference types used appropriately

- [ ] Async/await patterns followed correctly

### Code Complexity

- [ ] Methods under 50 lines (flagged if exceeded)

- [ ] Cyclomatic complexity under 10 per method

- [ ] Nesting depth under 4 levels

- [ ] Class size reasonable (<300 lines)

- [ ] Assembly cohesion evaluated

### Design & Architecture

- [ ] SOLID principles followed

- [ ] DRY principle applied (no significant duplication)

- [ ] Separation of concerns maintained

- [ ] Appropriate use of design patterns

- [ ] Dependency injection used properly

### Code Smells

- [ ] Long parameter lists identified (>5 parameters)

- [ ] Feature envy detected

- [ ] Shotgun surgery patterns flagged

- [ ] God classes identified

- [ ] Dead code marked for removal

### Error Handling

- [ ] Exceptions caught at appropriate level

- [ ] Specific exceptions used (not catch(Exception))

- [ ] Exception messages informative

- [ ] Using statements for IDisposable resources

- [ ] Logging appropriate for debugging

### Maintainability

- [ ] Code self-documenting with clear names

- [ ] Comments explain "why" not "what"

- [ ] Magic numbers replaced with named constants

- [ ] Configuration externalized

- [ ] Hardcoded values eliminated

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
# C# Code Quality Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/code_quality"
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

## Review Protocol

Please perform a comprehensive code quality review of this C# project following this protocol:

## Phase 1: Coding Standards Assessment

1. **Analyzer Compliance Check**
   ```powershell
   # Enable all analyzers
   dotnet build /p:EnforceCodeStyleInBuild=true /p:TreatWarningsAsErrors=true

   # Run with specific analyzer level
   dotnet build /p:AnalysisLevel=latest

   # Check for StyleCop violations
   # Add StyleCop.Analyzers NuGet package
   dotnet build
   ```

2. **Style Violations Analysis**

   - Document most common violations

   - Identify patterns of non-compliance

   - Assess consistency across projects

   - Flag formatting inconsistencies

3. **Naming Convention Review**

   - Verify public members use PascalCase

   - Check private fields use _camelCase or camelCase

   - Confirm interfaces start with 'I'

   - Verify async methods end with 'Async'

   - Identify unclear or abbreviated names

## Phase 2: Complexity Analysis

1. **Method-Level Complexity**
   ```powershell
   # Use Visual Studio Code Metrics
   # Or third-party tools like NDepend, CodeMaid

   # Enable in project file for warnings:
   # <CodeAnalysisTreatWarningsAsErrors>true</CodeAnalysisTreatWarningsAsErrors>
   ```

2. **Identify Complexity Hotspots**

   - List methods with complexity >10

   - Flag methods longer than 50 lines

   - Identify deeply nested code (>4 levels)

   - Document complex LINQ queries

   - Review switch expressions and pattern matching

3. **Assembly-Level Analysis**

   - Assess project size and cohesion

   - Identify projects with too many responsibilities

   - Check coupling between projects

   - Evaluate namespace organization

## Phase 3: Design Quality Review

1. **SOLID Principles**

   - **Single Responsibility**: Check if classes have one clear purpose

   - **Open/Closed**: Evaluate extensibility without modification

   - **Liskov Substitution**: Review inheritance hierarchies

   - **Interface Segregation**: Check for lean interfaces

   - **Dependency Inversion**: Assess dependency on abstractions

2. **DRY Violations**

   - Identify duplicated logic

   - Find near-duplicate methods

   - Document consolidation opportunities

   - Review code generation opportunities

3. **Design Patterns**

   - Identify patterns in use (Repository, Factory, Strategy, etc.)

   - Assess pattern appropriateness

   - Flag pattern misuse or over-engineering

   - Suggest beneficial pattern applications

## Phase 4: Code Smell Detection

1. **Common C# Code Smells**

   - **Long Parameter Lists**: Methods with >5 parameters

   - **Long Methods**: Methods exceeding 50 lines

   - **Large Classes**: Classes with >300 lines or >20 methods

   - **Data Clumps**: Same groups of data appearing together

   - **Feature Envy**: Methods using data from other classes excessively

   - **Primitive Obsession**: Using primitives instead of value objects

2. **Anti-Patterns**

   - God objects/classes

   - Circular dependencies

   - Lava flow (dead/obsolete code)

   - Copy-paste programming

   - Magic numbers and strings

   - Improper use of static classes

3. **C#-Specific Issues**

   - Not using 'using' statements for IDisposable

   - Catching Exception instead of specific exceptions

   - Not using async/await properly

   - Blocking on async code (.Result, .Wait())

   - String concatenation in loops (use StringBuilder)

   - Boxing/unboxing performance issues

## Phase 5: Error Handling & Robustness

1. **Exception Handling Review**

   - Check for broad exception catching

   - Verify appropriate exception types used

   - Assess error message quality

   - Review exception propagation strategy

   - Check for exception filters when appropriate

2. **Resource Management**

   - Verify use of 'using' statements

   - Check for proper async disposal (IAsyncDisposable)

   - Review memory management patterns

   - Identify potential resource leaks

3. **Defensive Programming**

   - Input validation assessed (guard clauses)

   - Boundary condition handling reviewed

   - Null-checking with nullable reference types

   - Edge case coverage evaluated

## Phase 6: Documentation Quality

1. **XML Documentation Coverage**
   ```powershell
   # Enable XML documentation
   # In .csproj: <GenerateDocumentationFile>true</GenerateDocumentationFile>

   # Check for missing documentation warnings
   dotnet build /p:GenerateDocumentationFile=true
   ```
   - Measure public API documentation coverage

   - Assess documentation completeness

   - Verify parameter documentation

   - Check return value documentation

2. **Comment Quality**

   - Evaluate comment necessity and clarity

   - Flag commented-out code for removal

   - Check for TODO/FIXME/HACK comments

   - Verify comments explain "why" not "what"

3. **Nullable Reference Types**

   - Check nullable context enabled

   - Verify nullable annotations on public APIs

   - Review null-forgiving operator (!) usage

   - Check for proper null checking

## Phase 7: Modern C# Features

1. **Language Feature Usage**

   - Pattern matching usage

   - Record types for DTOs

   - Init-only properties

   - Top-level statements appropriateness

   - File-scoped namespaces

   - Global using statements

2. **Async/Await Patterns**
   ```csharp
   // Check for anti-patterns:
   // Bad: Blocking async code
   var result = SomeAsyncMethod().Result; // DON'T

   // Bad: Unnecessary async/await
   async Task<string> GetData() => await File.ReadAllTextAsync(...); // Remove async/await

   // Good: Proper async pattern
   public async Task<User> GetUserAsync(int id)
   {
       var user = await _repository.GetByIdAsync(id);
       return user;
   }
   ```

3. **LINQ Usage**

   - Check for inefficient LINQ queries

   - Review deferred execution understanding

   - Identify multiple enumeration issues

   - Assess query complexity

## Output Format

Please provide a comprehensive quality report with the following structure:

### Executive Summary

- **Overall Quality Score**: [A-F grade]

- **Maintainability Index**: [score if available]

- **Average Complexity**: [cyclomatic complexity]

- **Critical Issues**: [count]

- **Technical Debt**: [estimated hours to address]

### Coding Standards Compliance

- **Analyzer Warnings**: [count by severity]

- **Most Common Issues**:

  1. [Issue type] - [count] occurrences

  2. [Issue type] - [count] occurrences

- **Consistency Score**: [percentage]

### Complexity Analysis
**High Complexity Methods** (Cyclomatic Complexity >10):
| Method | File | Complexity | Lines | Recommendation |
|--------|------|------------|-------|----------------|
| [name] | [path] | [score] | [count] | [refactor suggestion] |

**Large Files/Classes** (>300 lines):
| Class | Lines | Methods | Properties | Recommendation |
|-------|-------|---------|------------|----------------|
| [path] | [count] | [count] | [count] | [split suggestion] |

### Design Quality Issues
1. **SOLID Violations**:

   - [Principle]: [specific examples and impact]

2. **DRY Violations**:

   - [Location]: [description of duplication]

   - **Consolidation Opportunity**: [suggestion]

3. **Missing Patterns**:

   - [Location]: [beneficial pattern suggestion]

### Code Smells Identified
| Smell Type | Location | Severity | Description | Remediation |
|------------|----------|----------|-------------|-------------|
| [type] | [file:line] | [High/Med/Low] | [details] | [suggestion] |

### Error Handling Assessment

- **Broad Exception Catching**: [count and locations]

- **Missing Resource Cleanup**: [locations]

- **Inadequate Input Validation**: [locations]

- **Poor Error Messages**: [examples]

### Documentation Score

- **XML Documentation Coverage**: [percentage]

- **Nullable Annotation Coverage**: [percentage]

- **Comment Quality**: [Good/Fair/Poor]

- **Areas Needing Documentation**: [list]

### Modern C# Feature Usage

- **Nullable Reference Types**: [enabled/disabled, usage quality]

- **Pattern Matching**: [usage assessment]

- **Record Types**: [appropriate usage]

- **Async/Await**: [proper implementation or issues found]

### Technical Debt Summary
**Priority 1 (Critical)**: [Estimated hours]

- [Issue description and location]

**Priority 2 (High)**: [Estimated hours]

- [Issue description and location]

**Priority 3 (Medium)**: [Estimated hours]

- [Issue description and location]

**Priority 4 (Low)**: [Estimated hours]

- [Issue description and location]

### Refactoring Recommendations
1. **Immediate Actions** (within 1 sprint):

   - [Specific refactoring with location and rationale]

2. **Short-term Goals** (1-2 months):

   - [Improvement initiative with expected impact]

3. **Long-term Initiatives** (3-6 months):

   - [Strategic refactoring with business justification]

### Positive Patterns
Acknowledge what's done well:

- [Good practice observed and locations]

- [Effective pattern usage examples]

### Next Steps

- [ ] Address critical complexity hotspots

- [ ] Implement automated quality gates (.editorconfig, analyzers)

- [ ] Plan refactoring sprints for high-priority technical debt

- [ ] Establish team coding standards documentation

- [ ] Configure analyzer rules in Directory.Build.props

## Automation Recommendations
Suggest tools and configuration for continuous quality monitoring:
```xml
<!-- Directory.Build.props -->
<Project>
  <PropertyGroup>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>
    <EnableNETAnalyzers>true</EnableNETAnalyzers>
    <AnalysisLevel>latest</AnalysisLevel>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="StyleCop.Analyzers" Version="1.2.0-beta.435" PrivateAssets="all" />
    <PackageReference Include="Roslynator.Analyzers" Version="4.5.0" PrivateAssets="all" />
    <PackageReference Include="SonarAnalyzer.CSharp" Version="9.12.0" PrivateAssets="all" />
  </ItemGroup>
</Project>
```

```ini
# .editorconfig
root = true

[*.cs]
# Naming conventions
dotnet_naming_rule.interfaces_should_be_pascal_case_with_prefix.severity = warning
dotnet_naming_rule.interfaces_should_be_pascal_case_with_prefix.symbols = interface
dotnet_naming_rule.interfaces_should_be_pascal_case_with_prefix.style = pascal_case_with_i_prefix

# Code style rules
csharp_prefer_braces = true:warning
csharp_prefer_simple_using_statement = true:suggestion
```

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/code_quality/analysis_scripts
mkdir -p ${OUTPUT_DIR}/code_quality/supporting_data
```

**Save files as follows**:

- Main report → `review/code_quality/code_quality_report.md`

- Findings data → `review/code_quality/code_quality_findings.json`

- Analysis scripts → `review/code_quality/analysis_scripts/`

- Supporting data → `review/code_quality/supporting_data/`
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
