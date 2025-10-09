# C# Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to C# best practices. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── code_quality/
    ├── code_quality_report.md
    ├── code_quality_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:
- Create `review/` directory in repository root if it doesn't exist
- Create `review/code_quality/` subdirectory for this review phase
- All reports, scripts, and data files go in the phase-specific directory

**Expected Outputs**:
- `code_quality_report.md` - Main findings and recommendations
- `code_quality_findings.json` - Structured data for tooling integration
- `analysis_scripts/` - Any scripts generated during analysis
- `supporting_data/` - Raw data, logs, profiling results, scan outputs

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

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Code Quality Review

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
~~~
