---
name: cleanup-go
description: Remove dead code, consolidate duplicates, and apply idiomatic Go patterns for improved maintainability
version: 1.0.0
author: Benjamin Dourthe
language: Go
category: Code Cleanup
priority: MEDIUM
tags: [go, golang, cleanup, refactoring, idiomatic, dead-code, goroutines]
template_source: code_cleanup/go_cleanup.md
---

# Go Code Cleanup

Systematically identify and remove dead code, consolidate duplicate logic, and apply idiomatic Go patterns to maintain a lean, current, and maintainable codebase.

## When to Use This Skill

Use this skill when you need to:
- Remove unused imports, functions, variables, and types
- Consolidate duplicate code and near-duplicate implementations
- Apply idiomatic Go patterns (error handling, goroutines, defer)
- Clean up fmt.Println statements and commented code
- Optimize import organization and code structure
- Prepare codebase for new features or refactoring
- Reduce technical debt before major releases
- Remove unused module dependencies

## What This Skill Does

This skill performs comprehensive Go code cleanup:

### 1. Dead Code Detection
- **Unused Imports**: Identifies and removes unused import statements
- **Unused Functions**: Finds private (lowercase) functions never called
- **Unused Variables**: Identifies variables assigned but never used
- **Unused Constants**: Detects constants that are never referenced
- **Unused Types**: Finds private types (structs, interfaces) never used
- **Unreachable Code**: Finds code after return statements
- **Empty Blocks**: Detects empty functions or unnecessary code

### 2. Duplicate Code Consolidation
- **Exact Duplicates**: Finds identical code blocks for consolidation
- **Near Duplicates**: Detects similar code with minor variations
- **Duplicate Logic**: Identifies functionally equivalent implementations
- **Copy-Paste Detection**: Finds code copied across packages
- **Consolidation Strategy**: Recommends refactoring approach

### 3. Idiomatic Go Patterns
- **Error Handling**: Ensures errors are checked immediately
- **Named Returns**: Removes unnecessary named returns
- **Receiver Names**: Uses consistent receiver names (1-2 chars)
- **Context Parameter**: Ensures context.Context is first parameter
- **Interface Placement**: Moves interfaces to consumer packages
- **Accept Interfaces, Return Structs**: Follows this principle
- **Small Interfaces**: Prefers small, focused interfaces
- **Range Loops**: Uses appropriate range patterns

### 4. Debug Statement Cleanup
- **Print Statements**: Removes debug fmt.Println()
- **Commented Code**: Cleans up old commented-out code
- **TODO Comments**: Catalogs and prioritizes TODO items
- **Temporary Variables**: Identifies debug-only variables

### 5. Import Organization
- **Standard Library**: Groups Go standard library imports
- **External Packages**: Organizes third-party dependencies
- **Internal Packages**: Structures internal imports
- **Unused Removal**: Eliminates unnecessary imports
- **Dot Imports**: Replaces dot imports with explicit imports

### 6. Code Simplification
- **Redundant Nil Checks**: Removes unnecessary nil checks
- **Unnecessary Else**: Simplifies if-return patterns
- **Trailing Whitespace**: Removes whitespace at end of lines
- **Redundant Type Conversions**: Removes unnecessary conversions

## Prerequisites

- Go codebase to clean up
- Version control (git) for safe cleanup with rollback capability
- Test suite for regression verification (recommended)
- Backup of codebase or committed state
- Go toolchain installed

## Instructions

### Step 1: Prepare for Cleanup

1. **Commit Current State**:
   ```bash
   git add .
   git commit -m "Pre-cleanup snapshot"
   ```

2. **Create Cleanup Branch**:
   ```bash
   git checkout -b code-cleanup
   ```

3. **Run Existing Tests**:
   ```bash
   go test ./...
   ```

4. **Run Go Tools**:
   ```bash
   go fmt ./...
   go vet ./...
   staticcheck ./...
   ```

5. **Create Output Directory**:
   ```bash
   mkdir -p cleanup_report/{templates,assets,exports}
   ```

### Step 2: Invoke the Cleanup Skill

Tell Claude Code to use this skill:

```
"Use the cleanup-go skill to analyze and clean up this Go codebase.
Focus on:

1. Removing all unused imports, functions, and variables
2. Consolidating duplicate code
3. Applying idiomatic Go patterns
4. Removing fmt.Println statements
5. Organizing imports properly
6. Running go mod tidy to clean dependencies

Save all reports to cleanup_report/ directory."
```

### Step 3: Review Cleanup Plan

Claude Code will generate a comprehensive cleanup plan including:

1. **Dead Code Candidates** - List of unused code with usage analysis
2. **Duplication Report** - Duplicate code locations
3. **Idiomatic Go Opportunities** - Non-idiomatic patterns to fix
4. **go vet Warnings** - Static analysis findings
5. **Risk Assessment** - Impact analysis for each operation
6. **Implementation Plan** - Ordered steps with dependencies

**Review the plan before proceeding with changes!**

### Step 4: Execute Cleanup in Phases

**Phase 1: Low-Risk Cleanup**
- Remove unused imports
- Clean fmt.Println statements
- Remove commented code
- Organize imports

**Phase 2: Idiomatic Go Patterns**
- Fix error handling
- Apply proper receiver names
- Use context.Context correctly
- Apply range loop patterns
- Use make with capacity

**Phase 3: Structural Changes**
- Consolidate duplicates
- Remove dead functions
- Simplify complex code
- Extract constants

**Phase 4: Verification**
- Run tests after each phase
- Run go vet, staticcheck
- Verify no functionality changes
- Document any issues

**Phase 5: Multi-Pass Protocol**
- First pass: Apply cleanup across all files
- Verification pass: Check for missed opportunities
- Repeat until complete
- Track statistics for each pass

### Step 5: Test After Cleanup

1. **Run Full Test Suite**:
   ```bash
   go test ./...
   go test -race ./...  # Check for race conditions
   ```

2. **Run Go Tools**:
   ```bash
   go fmt ./...
   goimports -w .
   go vet ./...
   staticcheck ./...
   ```

3. **Build Verification**:
   ```bash
   go build ./...
   ```

4. **Module Cleanup**:
   ```bash
   go mod tidy
   go mod verify
   ```

### Step 6: Review and Commit

1. **Review Changes**:
   ```bash
   git diff
   ```

2. **Stage and Commit**:
   ```bash
   git add .
   git commit -m "Remove unused imports and functions"

   git add .
   git commit -m "Apply idiomatic Go patterns"

   git add .
   git commit -m "Consolidate duplicate validation logic"
   ```

3. **Merge to Main**:
   ```bash
   git checkout main
   git merge code-cleanup
   git push
   ```

## Cleanup Categories and Examples

### Category 1: Unused Imports
**Before:**
```go
package main

import (
    "fmt"
    "os"
    "strings"
    "time"
    "github.com/pkg/errors"
)

func main() {
    data := "hello"
    fmt.Println(data)
}
```

**After:**
```go
package main

import "fmt"

func main() {
    data := "hello"
    fmt.Println(data)
}
```

### Category 2: Debug Statements
**Before:**
```go
func CalculateTotal(items []Item) float64 {
    fmt.Println("DEBUG: items =", items)
    total := 0.0
    for _, item := range items {
        total += item.Price
    }
    fmt.Println("DEBUG: total =", total)
    return total
}
```

**After:**
```go
func CalculateTotal(items []Item) float64 {
    total := 0.0
    for _, item := range items {
        total += item.Price
    }
    return total
}
```

### Category 3: Idiomatic Error Handling
**Before:**
```go
func ReadFile(path string) (string, error) {
    data, err := os.ReadFile(path)
    if err == nil {
        return string(data), nil
    }
    return "", err
}
```

**After:**
```go
func ReadFile(path string) (string, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return "", err
    }
    return string(data), nil
}
```

### Category 4: Receiver Names and Context
**Before:**
```go
type UserService struct {
    db *Database
}

func (userService *UserService) GetUser(userId int) (*User, error) {
    return userService.db.FindUser(userId)
}

func (us *UserService) ProcessUser(user *User) error {
    // Inconsistent receiver name
    return us.db.Save(user)
}
```

**After:**
```go
type UserService struct {
    db *Database
}

func (s *UserService) GetUser(ctx context.Context, userID int) (*User, error) {
    return s.db.FindUser(ctx, userID)
}

func (s *UserService) ProcessUser(ctx context.Context, user *User) error {
    return s.db.Save(ctx, user)
}
```

### Category 5: Avoid Named Returns in Long Functions
**Before:**
```go
func ComplexCalculation(a, b int) (result int, err error) {
    // 50+ lines of code
    // ...
    return  // Naked return in long function
}
```

**After:**
```go
func ComplexCalculation(a, b int) (int, error) {
    // 50+ lines of code
    // ...
    return result, nil  // Explicit return
}
```

### Category 6: Range Loop Patterns
**Before:**
```go
// Only need value
for i, v := range items {
    _ = i
    Process(v)
}

// Only need index
for i, v := range items {
    _ = v
    fmt.Println(i)
}
```

**After:**
```go
// Only need value
for _, v := range items {
    Process(v)
}

// Only need index
for i := range items {
    fmt.Println(i)
}
```

### Category 7: Make with Capacity
**Before:**
```go
func ProcessItems(items []Item) []Result {
    results := []Result{}
    for _, item := range items {
        results = append(results, Process(item))
    }
    return results
}
```

**After:**
```go
func ProcessItems(items []Item) []Result {
    results := make([]Result, 0, len(items))
    for _, item := range items {
        results = append(results, Process(item))
    }
    return results
}
```

### Category 8: Duplicate Code Consolidation
**Before:**
```go
func ValidateUser(user *User) error {
    if user.Name == "" {
        return errors.New("name required")
    }
    if user.Email == "" {
        return errors.New("email required")
    }
    if !strings.Contains(user.Email, "@") {
        return errors.New("invalid email")
    }
    return nil
}

func ValidateAdmin(admin *Admin) error {
    if admin.Name == "" {
        return errors.New("name required")
    }
    if admin.Email == "" {
        return errors.New("email required")
    }
    if !strings.Contains(admin.Email, "@") {
        return errors.New("invalid email")
    }
    return nil
}
```

**After:**
```go
type Account interface {
    GetName() string
    GetEmail() string
}

func ValidateAccount(acc Account) error {
    if acc.GetName() == "" {
        return errors.New("name required")
    }
    if acc.GetEmail() == "" {
        return errors.New("email required")
    }
    if !strings.Contains(acc.GetEmail(), "@") {
        return errors.New("invalid email")
    }
    return nil
}
```

## Output Structure

```
cleanup_report/
├── templates/
│   ├── cleanup_checklist.md
│   ├── idiomatic_go_guide.md
│   └── golangci_lint_config.yaml
├── assets/
│   ├── duplication_graph.png
│   └── complexity_heatmap.png
└── exports/
    ├── cleanup_report.md
    ├── dead_code_list.md
    ├── duplication_analysis.md
    ├── idiomatic_patterns.md
    ├── go_vet_warnings.md
    └── risk_assessment.md
```

## Safety Measures

1. **Version Control Required**
2. **Test Coverage**
3. **Incremental Approach**
4. **Risk Assessment**
5. **Documentation**

## Success Criteria

- [ ] All unused imports removed
- [ ] No fmt.Println debugging statements
- [ ] No commented-out code
- [ ] Duplicate code consolidated
- [ ] Idiomatic Go patterns applied
- [ ] Imports organized properly
- [ ] All tests passing
- [ ] go vet passes
- [ ] staticcheck passes
- [ ] go mod tidy run
- [ ] Cleanup documented

## Tools and Libraries

### Static Analysis
- **go vet**: Built-in static analysis
- **staticcheck**: Advanced static analysis
- **golangci-lint**: Meta-linter
- **gosec**: Security analysis

### Formatting
- **gofmt**: Official formatter
- **goimports**: Import organizer

### Dependency Management
- **go mod tidy**: Dependency cleanup

```bash
# Install tools
go install honnef.co/go/tools/cmd/staticcheck@latest
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run tools
go fmt ./...
goimports -w .
go vet ./...
staticcheck ./...
golangci-lint run
go mod tidy
```

## Additional Resources

- [Effective Go](https://golang.org/doc/effective_go)
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- [Idiomatic Go](https://dmitri.shuralyov.com/idiomatic-go)
- [Go Proverbs](https://go-proverbs.github.io/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - code_cleanup/go_cleanup.md
