# Code Cleanup & Refactoring Review - Go

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on Go-specific issues including unused imports, dead code, and idiomatic Go patterns.

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

- [ ] Unused packages, functions, and variables identified

- [ ] Dormant feature flags, experiments, or toggles catalogued

- [ ] Deprecated APIs and endpoints mapped to replacement timeline

- [ ] Obsolete configuration values or environment variables removed

- [ ] Unreachable code paths confirmed with coverage/profiling evidence

- [ ] Unused module dependencies identified in go.mod

### Duplication & Consolidation

- [ ] Near-duplicate functions or structs grouped with merge candidates

- [ ] Copy-pasted logic replaced with shared utilities or packages

- [ ] Repeated database queries or API calls centralized

- [ ] Configuration defaults unified across services

- [ ] DRY violations documented with recommended abstractions

- [ ] Duplicate struct definitions or interfaces consolidated

### Refactoring Readiness

- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)

- [ ] Large functions broken into manageable units

- [ ] Legacy construction patterns replaced with idiomatic Go equivalents

- [ ] Naming aligns with domain language and architecture boundaries

- [ ] Deprecation notices or migration guides drafted where needed

- [ ] Code follows Go conventions (effective Go, code review comments)

### Regression Safety

- [ ] Critical behaviours covered by unit/integration tests

- [ ] Cleanup changes gated by feature flags or staged rollout plans

- [ ] Observatory signals (logs, metrics, traces) updated

- [ ] Stakeholders notified of breaking removals

- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Codebase Cleanup Request

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

Please perform a comprehensive, systematic cleanup of my Go codebase following this protocol:

## Phase 1: Analysis & Safety Check

Before making ANY changes, please:

1. **Analyze the complete codebase structure**
   - Identify all .go files in the project
   - Map dependencies between packages
   - Identify exported APIs that must be preserved
   - Check go.mod for unused module dependencies

2. **Generate a detailed cleanup report** listing:
   - Unused imports
   - Unused variables, constants, functions, and types
   - Debug fmt.Println() or log statements
   - Empty lines within function bodies
   - Inline and meta-commentary comments
   - Dead code after returns or in unreachable branches
   - Non-idiomatic Go patterns
   - go vet warnings
   - staticcheck findings
   - Estimated impact and risk level for each category

3. **Present findings and wait for my approval** before proceeding

## Phase 2: Cleanup Tasks

After I approve, systematically clean the following:

### Critical Removals

- **Unused imports**: Remove any imports not referenced in the code
  - Go compiler will catch these, but clean them proactively
  - Use goimports or gopls to organize imports

- **Unused variables**: Remove variables that are assigned but never read
  - Replace with `_` (blank identifier) if value must be received

- **Unused constants**: Remove constants that are defined but never used

- **Unused functions**: Remove private (lowercase) functions that are never called
  - PRESERVE exported (uppercase) functions even if seemingly unused (may be part of public API)

- **Unused types**: Remove private types (structs, interfaces) that are never used

- **Unused parameters**: Replace unused parameters with `_`
  - Keep parameter names if they clarify the function signature

- **Empty lines within functions**: Remove excessive blank lines inside function bodies
  - KEEP empty lines between logical code sections and between functions

### Comment Cleanup

- **Inline comments**: Remove same-line comments unless they explain complex logic

- **Meta-commentary**: Remove comments about code changes (e.g., "Changed from X to Y")

- **Commented-out code**: Remove old code blocks that are commented out

- **TODO comments**: Flag or remove stale TODO comments

- PRESERVE comments that explain:
  - Why a particular approach was chosen
  - Business logic or domain-specific rules
  - Complex algorithms or non-obvious implementations
  - Workarounds for known issues/bugs in dependencies
  - Package documentation (package-level comments)
  - Exported function/type documentation

### Debugging & Development Artifacts

- **Debug print statements**: Remove fmt.Println(), fmt.Printf() used for debugging
  - PRESERVE intentional output in CLI tools or intentional logging

- **Debug log statements**: Review and clean up temporary log.Println() statements

- **Test-only code**: Remove code marked as temporary test scaffolding

### Additional Cleanup Opportunities

#### Code Quality

- **Redundant code**: Identify and consolidate duplicate functions or logic blocks

- **Dead code after returns**: Remove unreachable code after return statements

- **Unnecessary else**: Simplify if-return patterns that don't need else blocks

- **Trailing whitespace**: Remove whitespace at end of lines

- **Redundant nil checks**: Remove checks that can never be true

- **Empty structs**: Review usage of empty struct{} for set/signal patterns

- **Redundant type conversions**: Remove unnecessary type conversions

#### Import Organization

- **Organize imports**: Use goimports or gopls to organize imports in standard order:
  1. Standard library packages (alphabetically)
  2. Blank line
  3. External packages (alphabetically)
  4. Blank line
  5. Internal packages (alphabetically)

- **Group related imports**: Keep related imports together when it improves clarity

- **Dot imports**: Replace dot imports (import . "pkg") with explicit imports

#### Idiomatic Go Patterns

- **Error handling**: Ensure errors are checked immediately after function calls

- **Named returns**: Remove named returns unless they significantly improve clarity

- **Receiver names**: Use consistent, short receiver names (1-2 chars)

- **Context parameter**: Ensure context.Context is first parameter in functions

- **Interface definitions**: Move interfaces to consumer packages, not producer packages

- **Accept interfaces, return structs**: Follow this principle for function signatures

- **Small interfaces**: Prefer small, focused interfaces over large ones

- **Avoid naked returns**: Don't use naked returns in long functions

- **Range loops**: Use appropriate range loop patterns (value, index-value, index-only)

- **Make with capacity**: Use make with capacity for slices when size is known

- **String concatenation**: Use strings.Builder for building strings in loops

#### Modern Go Features (Go 1.18+)

- **Generics**: Consider using generics for type-safe container functions (Go 1.18+)

- **Error wrapping**: Use %w verb with fmt.Errorf for error wrapping

- **Time format constants**: Use time.RFC3339 and other constants instead of magic strings

- **Build tags**: Update old-style build tags to new //go:build format (Go 1.17+)

#### Go Tooling Findings

- **go vet warnings**: Address all warnings from go vet

- **staticcheck**: Fix issues reported by staticcheck

- **golangci-lint**: Address findings from golangci-lint

- **ineffassign**: Remove ineffectual assignments

- **errcheck**: Ensure all errors are checked

- **gosec**: Address security issues found by gosec

#### Code Organization

- **Package organization**: Ensure packages have clear, single responsibilities

- **File naming**: Use conventional Go file naming (lowercase, underscores)

- **Test files**: Ensure test files are properly named (*_test.go)

- **Internal packages**: Use internal/ for truly internal packages

- **Cmd structure**: Follow standard cmd/ structure for commands

#### Performance Patterns

- **Preallocate slices**: Use make with capacity when size is known

- **Avoid unnecessary allocations**: Reuse buffers and objects where appropriate

- **String operations**: Use strings.Builder instead of concatenation in loops

- **Empty slice vs nil**: Use nil for empty slices instead of make([]T, 0)

- **Map initialization**: Preallocate maps with known size

#### Module Management

- **Unused dependencies**: Run `go mod tidy` to remove unused dependencies

- **Vendor folder**: Update vendor/ if using vendoring

- **Go version**: Ensure go.mod specifies appropriate Go version

- **Replace directives**: Review and clean up replace directives in go.mod

## Phase 3: Verification Protocol

After cleanup, you MUST:

1. **Provide summary** of all changes made, organized by category
2. **Highlight any edge cases** or decisions that required judgment
3. **Request that I run tests and tools** to verify nothing broke:
   ```bash
   go fmt ./...
   goimports -w .
   go vet ./...
   staticcheck ./...
   go test ./...
   go build ./...
   go mod tidy
   go mod verify
   ```
4. **Document cleanup** in CHANGELOG.md or development log:
   ```markdown
   ### Code Cleanup - [Date]
   - Removed [X] unused imports
   - Removed [Y] unused functions
   - Removed [Z] fmt.Println statements
   - Addressed [N] go vet warnings
   - Additional improvements: [summary]
   ```

## Critical Safety Rules

**DO NOT:**

- Remove any exported (uppercase) functions, types, or variables (may be used externally)

- Remove package documentation comments

- Remove empty lines between functions or major code sections

- Remove comments that explain business logic or complex algorithms

- Remove constants or variables even if seemingly unused (may be used via reflection)

- Remove intentional logging statements using proper logging packages

- Change function signatures or exported APIs

- Remove struct tags (may be used by JSON/XML encoders, ORMs, etc.)

- Make multiple sweeping changes at once - work systematically by category

**ALWAYS:**

- Work on one package at a time or in small logical groups

- Explain any removal that might be ambiguous

- Preserve code functionality - cleanup should never change behavior

- Ask for confirmation if uncertain about removing something

- Track what was removed in case rollback is needed

- Run go fmt, go vet, and go test after changes

- Preserve backward compatibility for exported APIs

- Consider reflection usage that might reference seemingly unused items

- Run gofmt with -s flag for additional simplifications

## Output Format
Present cleanup in this structure:

- **Cleanup Report - [Category]**

- **File:** path/to/file.go

- **Removals:**
  - Line X: Unused import "fmt"
  - Lines X-Y: Unused function functionName()
  - Line Z: Debug fmt.Println() statement
  - Line N: Inline comment removed

- **Rationale:** [Brief explanation of why these were removed]

## Summary Statistics

- **Total files processed:** X

- **Unused imports removed:** Y

- **Unused functions removed:** Z

- **Debug statements removed:** N

- **Lines removed:** M

- **Code reduction:** X%

- **go vet warnings fixed:** P

- **staticcheck issues fixed:** Q

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

- **Package documentation**: Flag packages missing package documentation

- **Exported API documentation**: Flag exported functions/types missing doc comments

- **Naming convention audit**: Ensure Go naming conventions are followed

- **Complexity analysis**: Flag overly complex functions (cyclomatic complexity > 10)

- **Error handling review**: Ensure consistent error handling patterns

- **Concurrency patterns**: Review goroutine usage and synchronization

- **Race conditions**: Run tests with -race flag to detect race conditions

- **Memory profiling**: Profile for unnecessary allocations

- **Benchmark coverage**: Ensure performance-critical code has benchmarks

- **Interface segregation**: Review interface definitions for proper granularity

- **Dependency injection**: Review dependency management patterns

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
