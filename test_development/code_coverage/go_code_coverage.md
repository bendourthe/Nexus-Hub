# Go Code Coverage Analysis

## Objective
Implement comprehensive code coverage measurement using Go's built-in coverage tools, analyze coverage gaps, establish coverage goals (80%+ target), create systematic improvement strategies, integrate coverage into CI/CD, and maintain high-quality test coverage for Go projects.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/code_coverage/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/code_coverage/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Coverage Setup
- [ ] Go test coverage tools configured
- [ ] Coverage profile generation enabled
- [ ] HTML report generation configured
- [ ] CI/CD coverage reporting set up
- [ ] Coverage thresholds defined

### Coverage Analysis
- [ ] Current coverage baseline measured
- [ ] Coverage gaps identified and prioritized
- [ ] Critical paths coverage verified
- [ ] Edge cases coverage assessed
- [ ] Untested code documented

### Coverage Goals
- [ ] Target coverage defined (80%+ recommended)
- [ ] Coverage thresholds set by package
- [ ] Critical path coverage requirements established
- [ ] Coverage improvement plan created
- [ ] Timeline for improvements defined

### Coverage Integration
- [ ] Coverage gates in CI/CD configured
- [ ] Coverage reports automated
- [ ] Coverage trends tracked
- [ ] Coverage regression prevention enabled
- [ ] Team coverage standards documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Code Coverage Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/code_coverage"
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

Please implement comprehensive code coverage measurement and improvement for this Go project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Coverage Setup and Configuration

### Built-in Go Coverage Tools

Go has built-in coverage tools that work out of the box. No additional installation required.

**Basic coverage commands**:
```bash
# Run tests with coverage
go test -cover ./...

# Generate coverage profile
go test -coverprofile=coverage.out ./...

# Generate HTML coverage report
go tool cover -html=coverage.out -o ${OUTPUT_DIR}/exports/coverage.html

# View coverage in terminal
go tool cover -func=coverage.out

# Generate coverage report sorted by coverage
go tool cover -func=coverage.out | sort -k3 -n
```

### Create Coverage Configuration Script

**scripts/coverage.sh**:
```bash
#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
COVERAGE_DIR="coverage"
COVERAGE_PROFILE="${COVERAGE_DIR}/coverage.out"
COVERAGE_HTML="${COVERAGE_DIR}/coverage.html"
COVERAGE_JSON="${COVERAGE_DIR}/coverage.json"
MIN_COVERAGE=80.0

# Create coverage directory
mkdir -p ${COVERAGE_DIR}

echo "Running tests with coverage..."
go test -v -coverprofile=${COVERAGE_PROFILE} -covermode=atomic ./...

if [ ! -f ${COVERAGE_PROFILE} ]; then
    echo -e "${RED}✗ Coverage profile not generated${NC}"
    exit 1
fi

# Generate HTML report
echo "Generating HTML report..."
go tool cover -html=${COVERAGE_PROFILE} -o ${COVERAGE_HTML}

# Calculate total coverage
TOTAL_COVERAGE=$(go tool cover -func=${COVERAGE_PROFILE} | \
    grep total | \
    awk '{print $3}' | \
    sed 's/%//')

echo ""
echo "================================"
echo "Coverage Summary"
echo "================================"
go tool cover -func=${COVERAGE_PROFILE}

echo ""
echo "================================"
echo "Coverage by Package"
echo "================================"

# Group coverage by package
go tool cover -func=${COVERAGE_PROFILE} | \
    grep -v "total:" | \
    awk '{
        split($1, parts, ":");
        pkg = parts[1];
        coverage[pkg] += $3;
        count[pkg]++;
    } END {
        for (pkg in coverage) {
            printf "%-50s %6.2f%%\n", pkg, coverage[pkg]/count[pkg];
        }
    }' | sort -t% -k2 -n

echo ""
echo "Total Coverage: ${TOTAL_COVERAGE}%"

# Check threshold
if (( $(echo "$TOTAL_COVERAGE < $MIN_COVERAGE" | bc -l) )); then
    echo -e "${RED}✗ Coverage ${TOTAL_COVERAGE}% is below threshold ${MIN_COVERAGE}%${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Coverage ${TOTAL_COVERAGE}% meets threshold ${MIN_COVERAGE}%${NC}"
fi

echo ""
echo "HTML report: ${COVERAGE_HTML}"
```

Make executable:
```bash
chmod +x scripts/coverage.sh
```

### Advanced Coverage Options

**Coverage modes**:
```bash
# Set coverage mode (default: set)
go test -covermode=set ./...      # Binary coverage (covered or not)
go test -covermode=count ./...    # Count how many times each statement is executed
go test -covermode=atomic ./...   # Like count, but correct in concurrent programs
```

**Coverage for specific packages**:
```bash
# Test only specific package
go test -cover ./pkg/service

# Exclude vendor and generated code
go test -cover $(go list ./... | grep -v /vendor/ | grep -v /mock)
```

**Coverage with build tags**:
```bash
# Test with specific build tags
go test -cover -tags=integration ./...
```

### Create Makefile for Coverage

**Makefile**:
```makefile
.PHONY: test coverage coverage-html coverage-func coverage-check

# Run tests
test:
	go test -v ./...

# Generate coverage profile
coverage:
	mkdir -p coverage
	go test -v -coverprofile=coverage/coverage.out -covermode=atomic ./...
	go tool cover -func=coverage/coverage.out

# Generate HTML coverage report
coverage-html: coverage
	go tool cover -html=coverage/coverage.out -o coverage/coverage.html
	@echo "Coverage report: coverage/coverage.html"

# Show coverage by function
coverage-func: coverage
	go tool cover -func=coverage/coverage.out | sort -k3 -n

# Check coverage threshold
coverage-check: coverage
	@COVERAGE=$$(go tool cover -func=coverage/coverage.out | \
		grep total | awk '{print $$3}' | sed 's/%//'); \
	echo "Total coverage: $$COVERAGE%"; \
	if [ $$(echo "$$COVERAGE < 80.0" | bc) -eq 1 ]; then \
		echo "✗ Coverage $$COVERAGE% is below threshold 80%"; \
		exit 1; \
	else \
		echo "✓ Coverage $$COVERAGE% meets threshold 80%"; \
	fi

# Generate coverage badge
coverage-badge: coverage
	@COVERAGE=$$(go tool cover -func=coverage/coverage.out | \
		grep total | awk '{print $$3}' | sed 's/%//'); \
	COLOR=$$(if [ $$(echo "$$COVERAGE >= 80" | bc) -eq 1 ]; then echo "brightgreen"; \
		elif [ $$(echo "$$COVERAGE >= 60" | bc) -eq 1 ]; then echo "yellow"; \
		else echo "red"; fi); \
	curl -s "https://img.shields.io/badge/coverage-$$COVERAGE%25-$$COLOR" > coverage/badge.svg
```

## Phase 2: Measure Current Coverage

### Run Coverage Analysis

```bash
# Run tests with coverage
make coverage

# Generate HTML report
make coverage-html

# View in browser
open coverage/coverage.html  # macOS
xdg-open coverage/coverage.html  # Linux
start coverage/coverage.html  # Windows (Git Bash)
```

### Analyze Coverage Report

**Terminal output example**:
```
github.com/myorg/myapp/pkg/auth/auth.go:15:    Login           78.3%
github.com/myorg/myapp/pkg/auth/auth.go:35:    Logout          92.0%
github.com/myorg/myapp/pkg/auth/token.go:10:   GenerateToken   85.7%
github.com/myorg/myapp/pkg/service/user.go:20: CreateUser      67.4%
github.com/myorg/myapp/pkg/service/user.go:45: UpdateUser      72.1%
github.com/myorg/myapp/pkg/service/user.go:70: DeleteUser      88.9%
github.com/myorg/myapp/pkg/util/helper.go:10:  FormatDate      95.0%
total:                                         (statements)    78.9%
```

### Identify Coverage Gaps

**Create coverage gap analyzer**:

```go
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

// CoverageGap represents a file with insufficient coverage
type CoverageGap struct {
	File     string
	Function string
	Coverage float64
	Priority string
}

// AnalyzeCoverageGaps identifies and prioritizes coverage gaps
func AnalyzeCoverageGaps(coverageFile string) error {
	file, err := os.Open(coverageFile)
	if err != nil {
		return fmt.Errorf("failed to open coverage file: %w", err)
	}
	defer file.Close()

	var gaps []CoverageGap
	scanner := bufio.NewScanner(file)
	re := regexp.MustCompile(`^(.+?):(\d+):\s+(\w+)\s+([\d.]+)%$`)

	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "total:") {
			continue
		}

		matches := re.FindStringSubmatch(line)
		if len(matches) != 5 {
			continue
		}

		coverage, _ := strconv.ParseFloat(matches[4], 64)
		if coverage < 80.0 {
			priority := "MEDIUM"
			if coverage < 50.0 {
				priority = "HIGH"
			} else if coverage < 70.0 {
				priority = "MEDIUM"
			} else {
				priority = "LOW"
			}

			gaps = append(gaps, CoverageGap{
				File:     matches[1],
				Function: matches[3],
				Coverage: coverage,
				Priority: priority,
			})
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("error scanning coverage file: %w", err)
	}

	// Sort by coverage (lowest first)
	sort.Slice(gaps, func(i, j int) bool {
		return gaps[i].Coverage < gaps[j].Coverage
	})

	// Print results
	fmt.Println(strings.Repeat("=", 100))
	fmt.Println("Coverage Gap Analysis")
	fmt.Println(strings.Repeat("=", 100))
	fmt.Printf("%-60s %-20s %10s %10s\n", "File", "Function", "Coverage", "Priority")
	fmt.Println(strings.Repeat("-", 100))

	for _, gap := range gaps {
		fmt.Printf("%-60s %-20s %9.1f%% %10s\n",
			gap.File, gap.Function, gap.Coverage, gap.Priority)
	}

	fmt.Printf("\nTotal functions needing improvement: %d\n", len(gaps))

	return nil
}

func main() {
	if err := AnalyzeCoverageGaps("coverage/coverage.out"); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
```

Run analysis:
```bash
# Generate coverage function report
go tool cover -func=coverage/coverage.out > coverage/coverage-func.txt

# Analyze gaps
go run scripts/analyze_coverage.go
```

## Phase 3: Prioritize Coverage Improvements

### Coverage Improvement Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **Critical** | Core business logic <50% coverage | Immediate test creation |
| **High** | Public functions <70% coverage | Test in current sprint |
| **Medium** | Utilities <80% coverage | Test in next sprint |
| **Low** | Internal helpers <80% coverage | Test when modified |

### Identify Critical Paths

```go
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
)

// CriticalPath represents a critical code path
type CriticalPath struct {
	File     string
	Function string
	Line     int
	Reason   string
}

// AnalyzeCriticalPaths identifies critical code paths requiring coverage
func AnalyzeCriticalPaths(rootDir string) error {
	var critical []CriticalPath

	err := filepath.Walk(rootDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		// Skip test files, vendor, and hidden directories
		if info.IsDir() && (info.Name() == "vendor" || strings.HasPrefix(info.Name(), ".")) {
			return filepath.SkipDir
		}

		if !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
			return nil
		}

		fset := token.NewFileSet()
		node, err := parser.ParseFile(fset, path, nil, parser.ParseComments)
		if err != nil {
			return err
		}

		// Analyze functions
		ast.Inspect(node, func(n ast.Node) bool {
			fn, ok := n.(*ast.FuncDecl)
			if !ok {
				return true
			}

			// Exported functions are critical
			if fn.Name.IsExported() {
				critical = append(critical, CriticalPath{
					File:     path,
					Function: fn.Name.Name,
					Line:     fset.Position(fn.Pos()).Line,
					Reason:   "Public API",
				})
			}

			// Functions with error handling are critical
			hasErrorHandling := false
			ast.Inspect(fn.Body, func(n ast.Node) bool {
				if _, ok := n.(*ast.DeferStmt); ok {
					hasErrorHandling = true
					return false
				}
				return true
			})

			if hasErrorHandling {
				critical = append(critical, CriticalPath{
					File:     path,
					Function: fn.Name.Name,
					Line:     fset.Position(fn.Pos()).Line,
					Reason:   "Error handling",
				})
			}

			return true
		})

		return nil
	})

	if err != nil {
		return err
	}

	// Group by file
	fileMap := make(map[string][]CriticalPath)
	for _, cp := range critical {
		fileMap[cp.File] = append(fileMap[cp.File], cp)
	}

	// Print results
	for file, paths := range fileMap {
		fmt.Printf("\n%s:\n", file)
		for _, cp := range paths {
			fmt.Printf("  Line %d: %s (%s)\n", cp.Line, cp.Function, cp.Reason)
		}
	}

	return nil
}

func main() {
	if err := AnalyzeCriticalPaths("./pkg"); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
```

## Phase 4: Systematic Coverage Improvement

### Strategy 1: Fill Happy Path Coverage

```go
/**
 * Add tests for basic functionality of uncovered code.
 *
 * Focus on main execution paths first.
 */

// Uncovered function
package discount

type CustomerType int

const (
	Premium CustomerType = iota
	Regular
	Guest
)

func CalculateDiscount(price float64, customerType CustomerType) float64 {
	switch customerType {
	case Premium:
		return price * 0.20
	case Regular:
		return price * 0.10
	default:
		return 0
	}
}

// Add basic coverage tests
package discount

import "testing"

func TestCalculateDiscount_Premium(t *testing.T) {
	discount := CalculateDiscount(100.0, Premium)
	expected := 20.0
	if discount != expected {
		t.Errorf("CalculateDiscount(100.0, Premium) = %v; want %v", discount, expected)
	}
}

func TestCalculateDiscount_Regular(t *testing.T) {
	discount := CalculateDiscount(100.0, Regular)
	expected := 10.0
	if discount != expected {
		t.Errorf("CalculateDiscount(100.0, Regular) = %v; want %v", discount, expected)
	}
}

func TestCalculateDiscount_Guest(t *testing.T) {
	discount := CalculateDiscount(100.0, Guest)
	expected := 0.0
	if discount != expected {
		t.Errorf("CalculateDiscount(100.0, Guest) = %v; want %v", discount, expected)
	}
}
```

### Strategy 2: Cover Edge Cases

```go
/**
 * Add tests for boundary conditions and edge cases.
 */

package discount

import "testing"

func TestCalculateDiscount_EdgeCases(t *testing.T) {
	tests := []struct {
		name         string
		price        float64
		customerType CustomerType
		want         float64
	}{
		{"zero price", 0.0, Premium, 0.0},
		{"negative price", -100.0, Premium, -20.0},
		{"very large price", 1000000.0, Premium, 200000.0},
		{"small decimal", 0.01, Premium, 0.002},
		{"invalid customer type", 100.0, CustomerType(99), 0.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CalculateDiscount(tt.price, tt.customerType)
			if got != tt.want {
				t.Errorf("CalculateDiscount(%v, %v) = %v; want %v",
					tt.price, tt.customerType, got, tt.want)
			}
		})
	}
}
```

### Strategy 3: Cover Error Paths

```go
/**
 * Add tests for error handling and exceptional conditions.
 */

// Function with error handling
package service

import (
	"errors"
	"fmt"
)

type User struct {
	ID   int64
	Name string
}

var ErrUserNotFound = errors.New("user not found")

type UserRepository interface {
	FindByID(id int64) (*User, error)
}

type UserService struct {
	repo UserRepository
}

func (s *UserService) LoadUserData(userID int64) (*User, error) {
	user, err := s.repo.FindByID(userID)
	if err != nil {
		if errors.Is(err, ErrUserNotFound) {
			return nil, nil
		}
		return nil, fmt.Errorf("failed to load user: %w", err)
	}

	return user, nil
}

// Tests covering error paths
package service

import (
	"errors"
	"testing"
)

type mockRepository struct {
	user *User
	err  error
}

func (m *mockRepository) FindByID(id int64) (*User, error) {
	return m.user, m.err
}

func TestUserService_LoadUserData_Success(t *testing.T) {
	expectedUser := &User{ID: 123, Name: "John Doe"}
	repo := &mockRepository{user: expectedUser}
	service := &UserService{repo: repo}

	user, err := service.LoadUserData(123)

	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if user != expectedUser {
		t.Errorf("LoadUserData() = %v; want %v", user, expectedUser)
	}
}

func TestUserService_LoadUserData_NotFound(t *testing.T) {
	repo := &mockRepository{err: ErrUserNotFound}
	service := &UserService{repo: repo}

	user, err := service.LoadUserData(999)

	if err != nil {
		t.Errorf("unexpected error: %v", err)
	}
	if user != nil {
		t.Errorf("LoadUserData() = %v; want nil", user)
	}
}

func TestUserService_LoadUserData_DatabaseError(t *testing.T) {
	dbErr := errors.New("database connection failed")
	repo := &mockRepository{err: dbErr}
	service := &UserService{repo: repo}

	user, err := service.LoadUserData(123)

	if err == nil {
		t.Error("expected error, got nil")
	}
	if user != nil {
		t.Errorf("LoadUserData() = %v; want nil", user)
	}
	if !errors.Is(err, dbErr) {
		t.Errorf("error does not wrap database error: %v", err)
	}
}
```

### Strategy 4: Cover Branch Conditions

```go
/**
 * Ensure all branches of conditional logic are tested.
 */

package shipping

type Destination int

const (
	Domestic Destination = iota
	International
	Remote
)

func CalculateShippingCost(weight float64, destination Destination, express bool) float64 {
	baseCost := weight * 2.5

	switch destination {
	case International:
		baseCost *= 3
	case Remote:
		baseCost *= 1.5
	}

	if express {
		baseCost *= 2
	}

	return baseCost
}

// Tests covering all branches
package shipping

import "testing"

func TestCalculateShippingCost_AllBranches(t *testing.T) {
	tests := []struct {
		name        string
		weight      float64
		destination Destination
		express     bool
		want        float64
	}{
		{"domestic standard", 10.0, Domestic, false, 25.0},
		{"domestic express", 10.0, Domestic, true, 50.0},
		{"international standard", 10.0, International, false, 75.0},
		{"international express", 10.0, International, true, 150.0},
		{"remote standard", 10.0, Remote, false, 37.5},
		{"remote express", 10.0, Remote, true, 75.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CalculateShippingCost(tt.weight, tt.destination, tt.express)
			if got != tt.want {
				t.Errorf("CalculateShippingCost() = %v; want %v", got, tt.want)
			}
		})
	}
}
```

## Phase 5: Coverage Reporting and Tracking

### Generate Comprehensive Reports

```bash
# Generate all report types
make coverage
make coverage-html

# Generate coverage badge
make coverage-badge

# Reports generated:
# - coverage/coverage.out (profile)
# - coverage/coverage.html (browsable HTML)
# - coverage/coverage-func.txt (function report)
# - coverage/badge.svg (badge)
```

### Coverage Badge

```markdown
# Add to README.md
![Coverage](coverage/badge.svg)
```

### Track Coverage Over Time

```go
package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"regexp"
	"time"
)

// CoverageRecord represents a historical coverage record
type CoverageRecord struct {
	Date     time.Time `json:"date"`
	Coverage float64   `json:"coverage"`
}

// RecordCoverage tracks coverage metrics over time
func RecordCoverage() error {
	// Read current coverage
	file, err := os.Open("coverage/coverage-func.txt")
	if err != nil {
		return fmt.Errorf("failed to open coverage file: %w", err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var coverage float64

	re := regexp.MustCompile(`total:.*\(statements\)\s+([\d.]+)%`)
	for scanner.Scan() {
		matches := re.FindStringSubmatch(scanner.Text())
		if len(matches) == 2 {
			fmt.Sscanf(matches[1], "%f", &coverage)
			break
		}
	}

	// Load history
	var history []CoverageRecord
	if data, err := os.ReadFile("coverage-history.json"); err == nil {
		json.Unmarshal(data, &history)
	}

	// Add current record
	history = append(history, CoverageRecord{
		Date:     time.Now(),
		Coverage: coverage,
	})

	// Save history
	data, err := json.MarshalIndent(history, "", "  ")
	if err != nil {
		return err
	}

	if err := os.WriteFile("coverage-history.json", data, 0644); err != nil {
		return err
	}

	fmt.Printf("Coverage recorded: %.1f%%\n", coverage)
	return nil
}

func main() {
	if err := RecordCoverage(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
```

### Coverage Diff for PRs

```go
package main

import (
	"encoding/json"
	"fmt"
	"os"
)

// CompareCoverage shows coverage changes in pull request
func CompareCoverage(basePath, currentPath string) error {
	var base, current CoverageRecord

	// Load base coverage
	baseData, err := os.ReadFile(basePath)
	if err != nil {
		return err
	}
	if err := json.Unmarshal(baseData, &base); err != nil {
		return err
	}

	// Load current coverage
	currentData, err := os.ReadFile(currentPath)
	if err != nil {
		return err
	}
	if err := json.Unmarshal(currentData, &current); err != nil {
		return err
	}

	diff := current.Coverage - base.Coverage

	fmt.Println("================================================================================")
	fmt.Println("Coverage Diff")
	fmt.Println("================================================================================")
	fmt.Printf("Base coverage:    %.2f%%\n", base.Coverage)
	fmt.Printf("Current coverage: %.2f%%\n", current.Coverage)
	fmt.Printf("Difference:       %+.2f%%\n", diff)

	if diff < -0.5 {
		fmt.Printf("\n❌ Coverage decreased by %.2f%%\n", -diff)
		os.Exit(1)
	} else if diff < 0 {
		fmt.Printf("\n⚠️ Coverage decreased slightly by %.2f%%\n", -diff)
	} else {
		fmt.Println("\n✅ Coverage maintained or improved")
	}

	return nil
}

func main() {
	if len(os.Args) < 3 {
		fmt.Fprintf(os.Stderr, "Usage: %s <base_coverage.json> <current_coverage.json>\n", os.Args[0])
		os.Exit(1)
	}

	if err := CompareCoverage(os.Args[1], os.Args[2]); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
```

## Phase 6: Coverage in CI/CD

### GitHub Actions Coverage Integration

```yaml
# .github/workflows/coverage.yml
name: Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Run tests with coverage
        run: |
          go test -v -coverprofile=coverage.out -covermode=atomic ./...
          go tool cover -func=coverage.out > ${OUTPUT_DIR}/exports/coverage-func.txt

      - name: Generate coverage report
        run: |
          go tool cover -html=coverage.out -o ${OUTPUT_DIR}/exports/coverage.html

      - name: Check coverage threshold
        run: |
          COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
          echo "Total coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 80.0" | bc -l) )); then
            echo "✗ Coverage ${COVERAGE}% is below threshold 80%"
            exit 1
          else
            echo "✓ Coverage ${COVERAGE}% meets threshold 80%"
          fi

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.out
          fail_ci_if_error: true

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: |
            coverage.out
            coverage.html
            coverage-func.txt
```

### Coverage Regression Prevention

```yaml
# Add to existing workflow
- name: Check for coverage regression
  run: |
    # Download base coverage from main branch
    git fetch origin main
    COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print $3}' | sed 's/%//')
    echo "{\"date\":\"$(date -Iseconds)\",\"coverage\":$COVERAGE}" > ${OUTPUT_DIR}/exports/current-coverage.json

    git show origin/main:coverage-history.json > ${OUTPUT_DIR}/exports/base-coverage.json || echo '[]' > ${OUTPUT_DIR}/exports/base-coverage.json

    # Compare with current
    go run scripts/coverage_diff.go base-coverage.json current-coverage.json
```

## Output Format

Please provide a comprehensive coverage analysis with the following structure:

### Coverage Summary
- **Overall Coverage**: [percentage]
- **Total Statements**: [count]
- **Covered Statements**: [count]
- **Missed Statements**: [count]

### Coverage by Package
| Package | Coverage | Statements | Priority |
|---------|----------|------------|----------|
| pkg/service | 76.3% | 231/304 | High |
| pkg/auth | 89.1% | 178/200 | Low |
| pkg/repository | 87.5% | 156/179 | Medium |
| pkg/util | 93.3% | 245/263 | Low |

### Critical Coverage Gaps
1. **pkg/service/user.go** (67% coverage)
   - **Missing**: Error handling paths (lines 45-67)
   - **Priority**: Critical - core business logic
   - **Action**: Add error scenario tests

2. **pkg/auth/token.go** (78% coverage)
   - **Missing**: Edge cases in token validation
   - **Priority**: High - security-critical
   - **Action**: Add boundary condition tests

### Coverage Improvement Plan
**Sprint 1** (Target: 75% → 80%):
- [ ] Add error handling tests for service package
- [ ] Cover authentication edge cases
- [ ] Test repository error scenarios

**Sprint 2** (Target: 80% → 85%):
- [ ] Add table-driven tests for all branches
- [ ] Test validation logic thoroughly
- [ ] Cover concurrent operations

**Sprint 3** (Target: 85% → 90%):
- [ ] Add context cancellation tests
- [ ] Cover all error types
- [ ] Test goroutine error handling

### Coverage Reports Generated
- **Coverage Profile**: `coverage/coverage.out`
- **HTML Report**: `coverage/coverage.html`
- **Function Report**: `coverage/coverage-func.txt`
- **Badge**: `coverage/badge.svg`

### Coverage Thresholds
- **Minimum Overall**: 80%
- **Critical Packages**: 90%
- **New Code**: 100%
- **CI/CD Gate**: Fail if <80%

### Best Practices Implemented
- [ ] Coverage measured on every test run
- [ ] HTML reports for detailed analysis
- [ ] Coverage tracked over time
- [ ] Regression prevention in CI/CD
- [ ] Critical paths prioritized
- [ ] Team coverage goals established

### Next Steps
- [ ] Fix identified coverage gaps
- [ ] Set up coverage dashboard
- [ ] Schedule coverage review meetings
- [ ] Document coverage standards
- [ ] Integrate coverage diff in PRs
- [ ] Track coverage trends monthly

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

~~~

## Output Format

The AI assistant should deliver:

1. **Complete coverage configuration** (Makefile, scripts, or build configuration)
2. **Current coverage analysis** with gaps identified
3. **Prioritized improvement plan** with specific actions
4. **Test implementations** to fill critical gaps (using testing package and table-driven tests)
5. **Coverage reporting infrastructure** (HTML, function reports, badges)
6. **CI/CD integration** with coverage gates
7. **Coverage tracking utilities** for trends
8. **Coverage diff tools** for PR reviews
9. **Team documentation** on coverage standards
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
