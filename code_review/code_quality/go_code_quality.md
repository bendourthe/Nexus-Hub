# Go Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to Go best practices. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

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
- [ ] gofmt compliance verified
- [ ] golint/staticcheck recommendations reviewed
- [ ] Import organization follows standard order
- [ ] Exported identifiers have documentation
- [ ] Consistent naming conventions (MixedCaps, camelCase)

### Code Complexity
- [ ] Functions under 50 lines (flagged if exceeded)
- [ ] Cyclomatic complexity under 10 per function
- [ ] Nesting depth under 4 levels
- [ ] File size reasonable (<500 lines)
- [ ] Package cohesion evaluated

### Design & Architecture
- [ ] SOLID principles followed (where applicable)
- [ ] DRY principle applied (no significant duplication)
- [ ] Separation of concerns maintained
- [ ] Appropriate use of interfaces
- [ ] Dependency injection where beneficial

### Code Smells
- [ ] Long parameter lists identified (>5 parameters)
- [ ] God packages or types identified
- [ ] Dead code marked for removal
- [ ] Magic numbers replaced with constants
- [ ] Global state usage minimized

### Error Handling
- [ ] Errors always checked and handled
- [ ] Error wrapping provides context
- [ ] Sentinel errors properly defined
- [ ] Resources properly cleaned up (defer)
- [ ] Panic/recover usage appropriate

### Maintainability
- [ ] Code self-documenting with clear names
- [ ] Comments explain "why" not "what"
- [ ] Configuration externalized
- [ ] Hardcoded values eliminated
- [ ] Appropriate use of goroutines and channels

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Code Quality Review

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

Please perform a comprehensive code quality review of this Go project following this protocol:

## Phase 1: Coding Standards Assessment

1. **Format & Style Check**
   ```bash
   # Run gofmt to check formatting
   gofmt -l .

   # Run goimports for import organization
   goimports -l .

   # Run golint
   golint ./...

   # Run staticcheck (comprehensive static analyzer)
   staticcheck ./...

   # Run go vet
   go vet ./...
   ```

2. **Style Violations Analysis**
   - Document most common violations
   - Identify patterns of non-compliance
   - Assess consistency across packages
   - Flag formatting inconsistencies

3. **Naming Convention Review**
   - Verify function names are descriptive and use MixedCaps
   - Check unexported names use camelCase
   - Confirm constants and variables follow conventions
   - Identify unclear or abbreviated names
   - Review package names (short, concise, lowercase)

## Phase 2: Complexity Analysis

1. **Function-Level Complexity**
   ```bash
   # Calculate cyclomatic complexity
   gocyclo -over 10 .

   # Identify complex functions
   gocyclo -top 20 .

   # Generate complexity report
   gocognit -over 15 .
   ```

2. **Identify Complexity Hotspots**
   - List functions with complexity >10
   - Flag functions longer than 50 lines
   - Identify deeply nested code (>4 levels)
   - Document complex conditional logic

3. **Package-Level Analysis**
   - Assess package size and cohesion
   - Identify packages with too many responsibilities
   - Check coupling between packages
   - Evaluate package organization (cmd/, internal/, pkg/)

## Phase 3: Design Quality Review

1. **Go Idioms & Best Practices**
   - **Accept interfaces, return structs**: Check function signatures
   - **Small interfaces**: Review interface size (1-3 methods ideal)
   - **Composition over inheritance**: Assess struct embedding
   - **Handle errors explicitly**: No ignored errors
   - **Make zero value useful**: Evaluate struct design

2. **DRY Violations**
   ```bash
   # Check for code duplication
   dupl -threshold 50 .
   ```
   - Identify duplicated logic
   - Find near-duplicate functions
   - Document consolidation opportunities

3. **Interface Design**
   - Identify interfaces in use
   - Assess interface size (prefer small interfaces)
   - Check for interface pollution
   - Evaluate interface segregation
   - Review acceptance of interfaces vs concrete types

## Phase 4: Code Smell Detection

1. **Common Go Code Smells**
   - **Long Parameter Lists**: Functions with >5 parameters
   - **Long Functions**: Functions exceeding 50 lines
   - **Large Files**: Files with >500 lines
   - **God Packages**: Packages with >20 exported types
   - **Primitive Obsession**: Overuse of basic types instead of custom types

2. **Anti-Patterns**
   - Global state and package-level variables
   - Goroutine leaks
   - Channel misuse
   - Context misuse
   - Improper error handling

3. **Go-Specific Issues**
   ```bash
   # Run comprehensive checks
   go vet ./...
   staticcheck ./...
   ```
   - Receiver naming inconsistency
   - Value vs pointer receivers inconsistency
   - Incorrect use of `defer` in loops
   - Copying mutexes
   - Inappropriate use of `init()`
   - Empty else blocks
   - Unnecessary conversions

## Phase 5: Error Handling & Robustness

1. **Error Handling Review**
   ```go
   // Good: Explicit error handling
   if err := doSomething(); err != nil {
       return fmt.Errorf("failed to do something: %w", err)
   }

   // Bad: Ignored errors
   doSomething() // ERROR: ignoring return value

   // Bad: Generic error handling
   if err != nil {
       return err // No context
   }
   ```

2. **Error Wrapping & Context**
   - Verify use of error wrapping (`%w` in fmt.Errorf)
   - Check for appropriate error context
   - Review sentinel error definitions
   - Assess custom error types

3. **Resource Management**
   - Verify use of `defer` for cleanup
   - Check for goroutine leaks
   - Review channel closing patterns
   - Identify potential resource leaks
   - Assess context cancellation handling

## Phase 6: Concurrency Review

1. **Goroutine Usage**
   ```go
   // Check for:
   - Goroutine leaks (goroutines never terminate)
   - Missing synchronization
   - Race conditions
   - Improper use of WaitGroups
   - Context not propagated
   ```

2. **Channel Patterns**
   ```go
   // Good patterns:
   - Producer-consumer patterns
   - Fan-out/fan-in patterns
   - Pipeline patterns

   // Bad patterns:
   - Sending to closed channels
   - Not closing channels when done
   - Unbuffered channels causing deadlocks
   ```

3. **Race Condition Detection**
   ```bash
   # Run tests with race detector
   go test -race ./...

   # Build with race detector
   go build -race
   ```

## Phase 7: Documentation Quality

1. **Godoc Coverage**
   ```bash
   # Check documentation coverage
   go doc -all [package]

   # View godoc locally
   godoc -http=:6060
   ```
   - Measure package/type/function documentation presence
   - Assess documentation completeness
   - Verify exported identifiers are documented
   - Check for package-level documentation

2. **Comment Quality**
   - Evaluate comment necessity and clarity
   - Flag commented-out code for removal
   - Check for TODO/FIXME/HACK comments
   - Verify comments explain "why" not "what"

3. **Documentation Standards**
   ```go
   // Good: Complete documentation
   // Package foo provides utilities for handling foo operations.
   // It includes support for foo creation, validation, and transformation.
   package foo

   // Foo represents a foo entity with associated metadata.
   type Foo struct {
       // ID is the unique identifier for this foo.
       ID string
   }

   // New creates a new Foo with the given ID.
   // It returns an error if the ID is empty or invalid.
   func New(id string) (*Foo, error) {
       // implementation
   }
   ```

## Output Format

Please provide a comprehensive quality report with the following structure:

### Executive Summary
- **Overall Quality Score**: [A-F grade]
- **Average Complexity**: [gocyclo score]
- **Critical Issues**: [count]
- **Technical Debt**: [estimated hours to address]

### Coding Standards Compliance
- **gofmt Violations**: [count of unformatted files]
- **golint/staticcheck Issues**: [count and severity]
- **Most Common Issues**:
  1. [Issue type] - [count] occurrences
  2. [Issue type] - [count] occurrences
- **Consistency Score**: [percentage]

### Complexity Analysis
**High Complexity Functions** (Cyclomatic Complexity >10):
| Function | File | Complexity | Lines | Recommendation |
|----------|------|------------|-------|----------------|
| [name] | [path] | [score] | [count] | [refactor suggestion] |

**Large Files** (>500 lines):
| File | Lines | Types | Functions | Recommendation |
|------|-------|-------|-----------|----------------|
| [path] | [count] | [count] | [count] | [split suggestion] |

### Design Quality Issues
1. **Go Idiom Violations**:
   - [Specific examples and impact]

2. **DRY Violations**:
   - [Location]: [description of duplication]
   - **Consolidation Opportunity**: [suggestion]

3. **Interface Design Issues**:
   - [Location]: [interface quality concern]

### Code Smells Identified
| Smell Type | Location | Severity | Description | Remediation |
|------------|----------|----------|-------------|-------------|
| [type] | [file:line] | [High/Med/Low] | [details] | [suggestion] |

### Error Handling Assessment
- **Ignored Errors**: [count and locations]
- **Missing Error Context**: [locations]
- **Improper Error Wrapping**: [locations]
- **Panic/Recover Usage**: [appropriate/inappropriate]

### Concurrency Issues
- **Potential Race Conditions**: [count and locations]
- **Goroutine Leaks**: [count and locations]
- **Channel Misuse**: [locations]
- **Race Detector Findings**: [summary from `go test -race`]

### Documentation Score
- **Godoc Coverage**: [percentage of exported identifiers]
- **Package Documentation**: [Good/Fair/Poor]
- **Comment Quality**: [Good/Fair/Poor]
- **Areas Needing Documentation**: [list]

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
- [ ] Fix all `go vet` and `staticcheck` issues
- [ ] Implement automated quality gates (linting, formatting)
- [ ] Plan refactoring sprints for high-priority technical debt
- [ ] Establish team coding standards documentation
- [ ] Set up pre-commit hooks for style enforcement

## Automation Recommendations
Suggest tools and configuration for continuous quality monitoring:
```yaml
# Example .golangci.yml
linters:
  enable:
    - gofmt
    - goimports
    - golint
    - staticcheck
    - errcheck
    - gosec
    - gocyclo
    - dupl
    - goconst
    - misspell

linters-settings:
  gocyclo:
    min-complexity: 10
  dupl:
    threshold: 100
```

```makefile
# Example Makefile targets
.PHONY: lint
lint:
	golangci-lint run ./...

.PHONY: fmt
fmt:
	gofmt -s -w .
	goimports -w .

.PHONY: vet
vet:
	go vet ./...
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
