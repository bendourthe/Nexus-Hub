# Code Cleanup & Refactoring Review - C#

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on C#/.NET-specific issues including unused using directives, code smells, and modern C# patterns.

## Output Directory Structure

All outputs should be saved in organized directories:

```
cleanup/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `cleanup/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Dead Code & Drift

- [ ] Unused classes, interfaces, and methods identified

- [ ] Dormant feature flags, experiments, or toggles catalogued

- [ ] Deprecated APIs and endpoints mapped to replacement timeline

- [ ] Obsolete configuration values or app settings removed

- [ ] Unreachable code paths confirmed with coverage/profiling evidence

- [ ] Unused NuGet packages identified

### Duplication & Consolidation

- [ ] Near-duplicate classes or methods grouped with merge candidates

- [ ] Copy-pasted logic replaced with shared utilities or base classes

- [ ] Repeated database queries or API calls centralized

- [ ] Configuration defaults unified across projects

- [ ] DRY violations documented with recommended abstractions

- [ ] Duplicate model classes or DTOs consolidated

### Refactoring Readiness

- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)

- [ ] Large classes/methods broken into manageable units

- [ ] Legacy construction patterns replaced with modern C# equivalents

- [ ] Naming aligns with domain language and architecture boundaries

- [ ] Deprecation notices or migration guides drafted where needed

- [ ] Anonymous delegates replaced with lambda expressions where appropriate

### Regression Safety

- [ ] Critical behaviours covered by unit/integration tests

- [ ] Cleanup changes gated by feature flags or staged rollout plans

- [ ] Observatory signals (logs, metrics, traces) updated

- [ ] Stakeholders notified of breaking removals

- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Codebase Cleanup Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="cleanup"
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

Please perform a comprehensive, systematic cleanup of my C# codebase following this protocol:

## Phase 1: Analysis & Safety Check

Before making ANY changes, please:

1. **Analyze the complete codebase structure**
   - Identify all .cs files in the solution
   - Map dependencies between projects, namespaces, and classes
   - Identify public APIs that must be preserved
   - Check .csproj files for unused NuGet package references

2. **Generate a detailed cleanup report** listing:
   - Unused using directives
   - Unused fields, properties, methods, and classes
   - Debug Console.WriteLine() or Debug.WriteLine() statements
   - Empty lines within method bodies
   - Inline and meta-commentary comments
   - Dead code after returns or in unreachable branches
   - Legacy patterns (old-style properties, delegates, null checks)
   - Code smells (god classes, long methods, feature envy)
   - ReSharper/Rider warnings and suggestions
   - Estimated impact and risk level for each category

3. **Present findings and wait for my approval** before proceeding

## Phase 2: Cleanup Tasks

After I approve, systematically clean the following:

### Critical Removals

- **Unused using directives**: Remove any using statements not referenced in the file
  - Use Visual Studio/Rider's "Remove Unused Usings" feature as reference
  - Keep System usings that are implicitly used

- **Unused fields**: Remove private fields that are assigned but never read

- **Unused properties**: Remove private/internal properties that are never accessed

- **Unused methods**: Remove private methods that are never called
  - PRESERVE public and protected methods (may be part of public API or used by subclasses)

- **Unused parameters**: Remove parameters that are defined but never used
  - Consider marking with discard `_` if parameter is required by interface/delegate

- **Unused local variables**: Remove variables that are assigned but never used

- **Empty methods**: Remove empty method bodies or replace with NotImplementedException

- **Empty lines within methods**: Remove excessive blank lines inside method bodies
  - KEEP empty lines between logical code sections and between methods

### Comment Cleanup

- **Inline comments**: Remove same-line comments unless they explain complex logic

- **Meta-commentary**: Remove comments about code changes (e.g., "Changed from X to Y", "Added this because...")

- **Commented-out code**: Remove old code blocks that are commented out

- **TODO comments**: Flag or remove stale TODO comments

- **Auto-generated comments**: Remove default XML comments that provide no value

- PRESERVE comments that explain:
  - Why a particular approach was chosen
  - Business logic or domain-specific rules
  - Complex algorithms or non-obvious implementations
  - Workarounds for known issues/bugs in dependencies
  - XML documentation for public APIs

### Debugging & Development Artifacts

- **Console statements**: Remove Console.WriteLine() and Console.Write() used for debugging
  - PRESERVE intentional console output in console applications

- **Debug statements**: Remove Debug.WriteLine() and Debug.Write() statements

- **Conditional compilation**: Review and clean up #if DEBUG blocks

- **Test-only code**: Remove code marked as temporary test scaffolding

### Additional Cleanup Opportunities

#### Code Quality

- **Redundant code**: Identify and consolidate duplicate methods or logic blocks

- **Dead code after returns**: Remove unreachable code after return statements

- **Unnecessary else**: Simplify if-return patterns that don't need else blocks

- **Trailing whitespace**: Remove whitespace at end of lines

- **Redundant modifiers**: Remove redundant private modifiers (default for class members)

- **Empty catch blocks**: Flag or properly handle empty catch blocks

- **Redundant initializations**: Remove explicit initialization to default values (null, 0, false)

- **Unnecessary string.Empty**: Use "" instead of string.Empty where appropriate

- **Redundant ToString()**: Remove unnecessary .ToString() calls

#### Using Directives Organization

- **Organize usings**: Sort using directives in standard order:
  1. System namespaces (alphabetically)
  2. Third-party namespaces (alphabetically)
  3. Internal namespaces (alphabetically)

- **Place usings inside namespace**: Consider moving using directives inside namespace (C# 10+)

- **Global usings**: Move commonly used usings to global usings (C# 10+)

#### Code Modernization (C# 6+)

- **Null-conditional operators**: Use `?.` instead of null checks

- **Null-coalescing operators**: Use `??` instead of ternary operators for null defaults

- **String interpolation**: Replace string.Format() with $"" interpolation

- **Expression-bodied members**: Use `=>` for simple methods, properties, and constructors

- **Auto-property initializers**: Initialize properties inline instead of in constructors

- **nameof operator**: Use nameof() instead of magic strings

- **Pattern matching**: Use pattern matching with is/switch expressions

- **Tuple literals**: Use tuples instead of out parameters or custom classes

#### Code Modernization (C# 7+)

- **Out variables**: Declare out variables inline (C# 7.0)

- **Discards**: Use `_` for unused out parameters or tuple elements (C# 7.0)

- **Local functions**: Extract nested functionality into local functions (C# 7.0)

- **Throw expressions**: Use throw in expression contexts (C# 7.0)

- **Default literal**: Use `default` instead of `default(T)` (C# 7.1)

- **Inferred tuple names**: Simplify tuple member names (C# 7.1)

#### Code Modernization (C# 8+)

- **Nullable reference types**: Enable and address nullable warnings (C# 8.0)

- **Switch expressions**: Replace switch statements with expressions (C# 8.0)

- **Property patterns**: Use property patterns in pattern matching (C# 8.0)

- **Using declarations**: Replace using statements with declarations (C# 8.0)

- **Null-coalescing assignment**: Use `??=` operator (C# 8.0)

- **Static local functions**: Mark local functions as static where appropriate (C# 8.0)

- **Indices and ranges**: Use `^` and `..` for array/collection access (C# 8.0)

#### Code Modernization (C# 9+)

- **Records**: Replace simple POCOs with records (C# 9.0)

- **Init-only properties**: Use init instead of set for immutable properties (C# 9.0)

- **Top-level statements**: Simplify Program.cs with top-level statements (C# 9.0)

- **Target-typed new**: Use `new()` instead of repeating type (C# 9.0)

- **Covariant returns**: Take advantage of more specific return types (C# 9.0)

#### Code Modernization (C# 10+)

- **Global usings**: Move common usings to global usings (C# 10.0)

- **File-scoped namespaces**: Remove namespace braces (C# 10.0)

- **Record structs**: Use record structs for value types (C# 10.0)

- **Interpolated string handlers**: Use improved string interpolation (C# 10.0)

#### Code Modernization (C# 11+)

- **Raw string literals**: Use raw string literals for multi-line strings (C# 11.0)

- **Required members**: Use required keyword for mandatory properties (C# 11.0)

- **UTF-8 string literals**: Use UTF-8 literals where appropriate (C# 11.0)

#### Code Smells

- **Long methods**: Flag methods exceeding 50 lines for potential extraction

- **Long parameter lists**: Suggest parameter objects for methods with >4 parameters

- **God classes**: Identify classes with too many responsibilities

- **Feature envy**: Identify methods that use more data from other classes

- **Data clumps**: Identify groups of parameters that appear together

- **Primitive obsession**: Suggest value objects for primitive types with behavior

- **Inappropriate intimacy**: Identify classes that access each other's internals too much

#### .NET/Build Configuration

- **Unused NuGet packages**: Identify packages not referenced in code

- **Package conflicts**: Check for version conflicts or duplicate packages

- **Target framework**: Verify project targets appropriate .NET version

- **Project references**: Remove unused project references

## Phase 3: Verification Protocol

After cleanup, you MUST:

1. **Provide summary** of all changes made, organized by category
2. **Highlight any edge cases** or decisions that required judgment
3. **Request that I run tests and build** to verify nothing broke:
   ```bash
   dotnet clean
   dotnet build
   dotnet test
   dotnet format --verify-no-changes  # Check formatting
   ```
4. **Document cleanup** in CHANGELOG.md or development log:
   ```markdown
   ### Code Cleanup - [Date]
   - Removed [X] unused using directives
   - Removed [Y] unused methods
   - Removed [Z] Console.WriteLine statements
   - Modernized [N] legacy patterns
   - Additional improvements: [summary]
   ```

## Critical Safety Rules

**DO NOT:**

- Remove any public or protected methods, classes, or properties (may be used externally or by subclasses)

- Remove XML documentation comments

- Remove attributes (could be used by reflection or frameworks)

- Remove empty lines between methods, classes, or major code sections

- Remove comments that explain business logic or complex algorithms

- Remove constants or configuration values even if seemingly unused

- Remove intentional logging statements using proper frameworks (ILogger)

- Change method signatures or public APIs

- Remove serialization-related members (could be used by serializers)

- Make multiple sweeping changes at once - work systematically by category

**ALWAYS:**

- Work on one class at a time or in small logical groups

- Explain any removal that might be ambiguous

- Preserve code functionality - cleanup should never change behavior

- Ask for confirmation if uncertain about removing something

- Track what was removed in case rollback is needed

- Run code analysis tools after changes to verify correctness

- Preserve backward compatibility for public APIs

- Consider reflection/serialization usage that might reference seemingly unused members

- Consider ASP.NET Core DI requirements for public constructors and methods

## Output Format
Present cleanup in this structure:

- **Cleanup Report - [Category]**

- **File:** Path\To\File.cs

- **Removals:**
  - Line X: Unused using System.Collections
  - Lines X-Y: Unused private method MethodName()
  - Line Z: Console.WriteLine() debugging statement
  - Line N: Inline comment removed

- **Rationale:** [Brief explanation of why these were removed]

## Summary Statistics

- **Total files processed:** X

- **Unused usings removed:** Y

- **Unused methods removed:** Z

- **Debug statements removed:** N

- **Lines removed:** M

- **Code reduction:** X%

- **Modernization changes:** P

- **Code smells addressed:** Q

**Overall Impact:** [Low/Medium/High risk assessment]

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/backup
mkdir -p ${OUTPUT_DIR}/scripts
mkdir -p ${OUTPUT_DIR}/analysis
```

**Save files as follows**:

- Cleanup report → `cleanup/cleanup_report.md`

- Cleanup history → `cleanup/cleanup_history.md`

- Backups → `cleanup/backup/`

- Scripts → `cleanup/scripts/`

- Analysis → `cleanup/analysis/`

## Optional Advanced Cleanup (Requires Extra Review)
If you'd like an even more thorough cleanup, also consider:

- **XML documentation**: Flag public APIs missing XML documentation

- **Naming convention audit**: Ensure PascalCase/camelCase usage is consistent

- **Complexity analysis**: Flag overly complex methods (cyclomatic complexity > 10)

- **Performance patterns**: Identify inefficient patterns (boxing, unnecessary allocations)

- **Immutability**: Suggest making classes/properties immutable where appropriate

- **Thread safety**: Review and flag potential concurrency issues

- **Exception handling**: Review exception handling patterns and suggest improvements

- **Async/await**: Ensure proper async patterns (ConfigureAwait, cancellation tokens)

- **SOLID principles**: Review adherence to SOLID principles

- **Dependency injection**: Review DI patterns and lifetime management

- **Nullable annotations**: Add nullable reference type annotations throughout

These require more careful review and may involve refactoring beyond simple cleanup.
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
