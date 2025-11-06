# Go Reward Hacking - Test Quality Validation Guide

## Objective

Validate the integrity and robustness of Go test suites by detecting test quality issues, identifying "reward hacking" patterns where tests pass without truly validating functionality, and ensuring comprehensive, meaningful test coverage through mutation testing using go-mutesting and comprehensive quality analysis.

---

## Output Directory Structure

All generated files should be saved to the following directory structure:

```
{OUTPUT_DIR}/
├── templates/           # Detection scripts and automation tools
│   ├── tautological_detector.go
│   ├── mutation_test_runner.sh
│   ├── quality_calculator.go
│   ├── coverage_analyzer.go
│   └── continuous_monitoring.sh
├── assets/             # Visualizations and charts
│   ├── mutation_coverage_heatmap.png
│   ├── test_quality_scorecard.png
│   ├── phase_validation_matrix.png
│   ├── remediation_timeline.png
│   └── quality_trends_dashboard.png
└── exports/            # Reports and documentation
    ├── test_quality_report.md (25-35 pages)
    ├── mutation_testing_results.md
    ├── test_quality_scorecard.md
    ├── phase_by_phase_validation.md
    ├── remediation_action_plan.md
    ├── continuous_monitoring_setup.md
    └── weak_test_examples.md
```

---

## Implementation Checklist

### Prerequisites Verification
- [ ] All 7 previous testing phases completed
- [ ] Test structure output collected
- [ ] Unit test results available
- [ ] Integration test outputs gathered
- [ ] Mock and fixture implementations documented
- [ ] Performance test results compiled
- [ ] CI/CD pipeline logs obtained
- [ ] Code coverage reports generated

### Mutation Testing Setup
- [ ] go-mutesting installed
- [ ] Mutation testing baseline established
- [ ] Mutation score thresholds defined
- [ ] Test execution environment prepared

### Quality Analysis
- [ ] Tautological test detection script created
- [ ] Weak assertion analyzer implemented
- [ ] Over-mocking detection configured
- [ ] Coverage integrity validator developed
- [ ] Test independence checker deployed

### Reporting
- [ ] Comprehensive test quality report generated (25-35 pages)
- [ ] Mutation testing results documented
- [ ] Phase-by-phase validation completed
- [ ] Remediation action plan created
- [ ] Continuous monitoring configured

---

## Prompt Template

Copy the prompt below into your AI assistant to generate comprehensive reward hacking validation:

```markdown
# Go Test Quality Validation - Reward Hacking Detection

## Context
I need comprehensive test quality validation for a Go application. All 7 previous testing phases (Test Structure, Unit Tests, Test Cases, Mocks & Fixtures, Performance Testing, Maintenance & CI/CD, Code Coverage) are complete. Generate a thorough analysis detecting reward hacking patterns, validating test effectiveness through mutation testing, and providing actionable remediation guidance.

## CRITICAL: Output Directory Setup

Before starting, create this exact directory structure:

```bash
mkdir -p {OUTPUT_DIR}/templates
mkdir -p {OUTPUT_DIR}/assets
mkdir -p {OUTPUT_DIR}/exports
```

Replace `{OUTPUT_DIR}` with your desired output location (e.g., `go_reward_hacking_output`).

---

## Repository Information

To include accurate repository information in documentation:

```bash
git config --get remote.origin.url
```

---

## Phase 1: Unit Test Quality Audit

**Validates:** Phase 2 (Unit Tests)

### 1.1 Tautological Test Detection

Analyze all unit tests for patterns that always pass:

**Detection Criteria:**
- Tests with no assertions
- Tests with trivial assertions (true checks, nil checks only)
- Tests that only check types without validating behavior
- Tests with mocked return values used directly in assertions

**Create:** `{OUTPUT_DIR}/templates/tautological_detector.go`

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

// TautologicalDetector analyzes Go tests for weak patterns
type TautologicalDetector struct {
	issues      []Issue
	currentFile string
}

// Issue represents a detected test quality issue
type Issue struct {
	File     string
	Test     string
	Line     int
	Severity string
	Issue    string
	Pattern  string
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "Usage: go run tautological_detector.go <test-directory>")
		os.Exit(1)
	}

	testDir := os.Args[1]
	detector := &TautologicalDetector{}

	if err := detector.scanDirectory(testDir); err != nil {
		fmt.Fprintf(os.Stderr, "Error scanning directory: %v\n", err)
		os.Exit(1)
	}

	if err := detector.generateReport("tautological_tests_report.md"); err != nil {
		fmt.Fprintf(os.Stderr, "Error generating report: %v\n", err)
		os.Exit(1)
	}

	criticalCount := 0
	for _, issue := range detector.issues {
		if issue.Severity == "CRITICAL" {
			criticalCount++
		}
	}

	if criticalCount > 0 {
		fmt.Fprintf(os.Stderr, "\n❌ CRITICAL: %d tests with no assertions found\n", criticalCount)
		os.Exit(1)
	} else {
		fmt.Println("\n✅ No critical tautological tests detected")
	}
}

func (d *TautologicalDetector) scanDirectory(dir string) error {
	return filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(path, "_test.go") {
			if err := d.analyzeFile(path); err != nil {
				fmt.Fprintf(os.Stderr, "Error analyzing %s: %v\n", path, err)
			}
		}

		return nil
	})
}

func (d *TautologicalDetector) analyzeFile(filePath string) error {
	d.currentFile = filePath

	fset := token.NewFileSet()
	node, err := parser.ParseFile(fset, filePath, nil, parser.ParseComments)
	if err != nil {
		return err
	}

	ast.Inspect(node, func(n ast.Node) bool {
		fn, ok := n.(*ast.FuncDecl)
		if !ok {
			return true
		}

		// Check if function is a test (starts with Test)
		if !strings.HasPrefix(fn.Name.Name, "Test") {
			return true
		}

		testName := fn.Name.Name
		line := fset.Position(fn.Pos()).Line

		analysis := d.analyzeAssertions(fn)

		if analysis.assertionCount == 0 {
			d.issues = append(d.issues, Issue{
				File:     d.currentFile,
				Test:     testName,
				Line:     line,
				Severity: "CRITICAL",
				Issue:    "No assertions found - execution-only test",
				Pattern:  "TAUTOLOGICAL",
			})
		} else if analysis.isTrivial {
			d.issues = append(d.issues, Issue{
				File:     d.currentFile,
				Test:     testName,
				Line:     line,
				Severity: "HIGH",
				Issue:    fmt.Sprintf("Trivial assertion: %s", analysis.reason),
				Pattern:  "WEAK_ASSERTION",
			})
		} else if analysis.isTypeOnly {
			d.issues = append(d.issues, Issue{
				File:     d.currentFile,
				Test:     testName,
				Line:     line,
				Severity: "HIGH",
				Issue:    "Type-only validation without behavior check",
				Pattern:  "TYPE_ONLY",
			})
		}

		return true
	})

	return nil
}

type assertionAnalysis struct {
	assertionCount int
	isTrivial      bool
	isTypeOnly     bool
	reason         string
}

func (d *TautologicalDetector) analyzeAssertions(fn *ast.FuncDecl) *assertionAnalysis {
	analysis := &assertionAnalysis{}

	ast.Inspect(fn, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}

		// Check for testing assertions
		if sel, ok := call.Fun.(*ast.SelectorExpr); ok {
			methodName := sel.Sel.Name

			// Common assertion patterns in Go
			assertionMethods := []string{
				"Error", "Errorf", "Fatal", "Fatalf",
				"Equal", "NotEqual", "True", "False",
				"Nil", "NotNil", "Empty", "NotEmpty",
			}

			isAssertion := false
			for _, method := range assertionMethods {
				if methodName == method {
					isAssertion = true
					break
				}
			}

			if isAssertion {
				analysis.assertionCount++

				// Check for trivial assertions
				if methodName == "True" && len(call.Args) > 1 {
					if lit, ok := call.Args[1].(*ast.Ident); ok {
						if lit.Name == "true" {
							analysis.isTrivial = true
							analysis.reason = "t.True(true)"
						}
					}
				}

				if methodName == "NotNil" && analysis.assertionCount == 1 {
					analysis.isTrivial = true
					analysis.reason = "t.NotNil() only"
				}

				// Check for type-only assertions
				if methodName == "IsType" {
					analysis.isTypeOnly = true
				}
			}
		}

		return true
	})

	return analysis
}

func (d *TautologicalDetector) generateReport(outputPath string) error {
	var critical, high []Issue

	for _, issue := range d.issues {
		if issue.Severity == "CRITICAL" {
			critical = append(critical, issue)
		} else if issue.Severity == "HIGH" {
			high = append(high, issue)
		}
	}

	var report strings.Builder

	report.WriteString("# Tautological Test Detection Report\n\n")
	report.WriteString("## Summary\n")
	report.WriteString(fmt.Sprintf("- **Total Issues:** %d\n", len(d.issues)))
	report.WriteString(fmt.Sprintf("- **Critical:** %d\n", len(critical)))
	report.WriteString(fmt.Sprintf("- **High:** %d\n\n", len(high)))

	report.WriteString("## Critical Issues (No Assertions)\n\n")
	for _, issue := range critical {
		report.WriteString(fmt.Sprintf("### %s:%d - %s\n", issue.File, issue.Line, issue.Test))
		report.WriteString(fmt.Sprintf("- **Pattern:** %s\n", issue.Pattern))
		report.WriteString(fmt.Sprintf("- **Issue:** %s\n\n", issue.Issue))
	}

	report.WriteString("\n## High Severity Issues (Weak Assertions)\n\n")
	for _, issue := range high {
		report.WriteString(fmt.Sprintf("### %s:%d - %s\n", issue.File, issue.Line, issue.Test))
		report.WriteString(fmt.Sprintf("- **Pattern:** %s\n", issue.Pattern))
		report.WriteString(fmt.Sprintf("- **Issue:** %s\n\n", issue.Issue))
	}

	return os.WriteFile(outputPath, []byte(report.String()), 0644)
}
```

**Run Detection:**
```bash
go run {OUTPUT_DIR}/templates/tautological_detector.go ./
```

### 1.2 Test Isolation Verification

**Validates:** Phase 2 (Unit Tests) - Test Independence

Verify that unit tests can run in any order without failures:

**Create:** `{OUTPUT_DIR}/templates/isolation_verifier.go`

```go
package main

import (
	"fmt"
	"math/rand"
	"os"
	"os/exec"
	"strings"
	"time"
)

type IsolationVerifier struct {
	testCommand string
	results     []testResult
}

type testResult struct {
	passed bool
	output string
}

type isolationAnalysis struct {
	totalIterations  int
	passedCount      int
	failedCount      int
	isolationScore   float64
	failedIterations []int
}

func main() {
	iterations := 10
	if len(os.Args) > 1 {
		fmt.Sscanf(os.Args[1], "%d", &iterations)
	}

	verifier := &IsolationVerifier{
		testCommand: "go test -v ./...",
	}

	analysis := verifier.verifyIsolation(iterations)
	verifier.generateReport(analysis, "test_isolation_report.md")

	if analysis.isolationScore < 100.0 {
		fmt.Fprintf(os.Stderr, "\n❌ ISOLATION ISSUES: %.1f%% failure rate\n",
			100-analysis.isolationScore)
		os.Exit(1)
	} else {
		fmt.Println("\n✅ Perfect test isolation verified")
	}
}

func (v *IsolationVerifier) verifyIsolation(iterations int) *isolationAnalysis {
	fmt.Printf("Running tests in %d random orders...\n", iterations)

	rand.Seed(time.Now().UnixNano())

	for i := 0; i < iterations; i++ {
		fmt.Printf("  Iteration %d/%d...", i+1, iterations)

		result := v.runTests()
		v.results = append(v.results, result)

		if result.passed {
			fmt.Println(" ✅")
		} else {
			fmt.Println(" ❌")
		}
	}

	return v.analyzeResults(iterations)
}

func (v *IsolationVerifier) runTests() testResult {
	// Add randomization flag to shuffle test order
	cmd := exec.Command("sh", "-c", v.testCommand+" -shuffle=on")

	output, err := cmd.CombinedOutput()

	return testResult{
		passed: err == nil,
		output: string(output),
	}
}

func (v *IsolationVerifier) analyzeResults(iterations int) *isolationAnalysis {
	passedCount := 0
	var failedIterations []int

	for i, result := range v.results {
		if result.passed {
			passedCount++
		} else {
			failedIterations = append(failedIterations, i+1)
		}
	}

	failedCount := iterations - passedCount
	isolationScore := (float64(passedCount) / float64(iterations)) * 100

	return &isolationAnalysis{
		totalIterations:  iterations,
		passedCount:      passedCount,
		failedCount:      failedCount,
		isolationScore:   isolationScore,
		failedIterations: failedIterations,
	}
}

func (v *IsolationVerifier) generateReport(analysis *isolationAnalysis, outputPath string) error {
	var report strings.Builder

	report.WriteString("# Test Isolation Verification Report\n\n")
	report.WriteString("## Summary\n")
	report.WriteString(fmt.Sprintf("- **Total Iterations:** %d\n", analysis.totalIterations))

	if analysis.isolationScore == 100 {
		report.WriteString("- **All Passed:** ✅ YES\n")
	} else {
		report.WriteString("- **All Passed:** ❌ NO\n")
	}

	report.WriteString(fmt.Sprintf("- **Failed Iterations:** %d\n", analysis.failedCount))
	report.WriteString(fmt.Sprintf("- **Isolation Score:** %.1f%%\n\n", analysis.isolationScore))

	if analysis.isolationScore == 100 {
		report.WriteString("## ✅ Perfect Isolation\n\n")
		report.WriteString("All tests passed in every random order. Tests are properly isolated.\n\n")
	} else {
		report.WriteString("## ❌ Isolation Issues Detected\n\n")
		report.WriteString(fmt.Sprintf("Tests failed in %d out of %d random orders.\n\n",
			analysis.failedCount, analysis.totalIterations))

		report.WriteString("### Failed Iterations\n\n")
		for _, iter := range analysis.failedIterations {
			report.WriteString(fmt.Sprintf("- Iteration %d\n", iter))
		}

		report.WriteString("\n### Recommended Actions\n\n")
		report.WriteString("1. **Review setup/cleanup** - Use t.Cleanup() for proper resource cleanup\n")
		report.WriteString("2. **Check for shared state** - Avoid package-level variables in tests\n")
		report.WriteString("3. **Verify mock cleanup** - Reset mocks between tests\n")
		report.WriteString("4. **Run tests with -shuffle** - Use -shuffle=on flag regularly\n")
		report.WriteString("5. **Use t.Parallel()** - Identify race conditions with parallel tests\n\n")
	}

	return os.WriteFile(outputPath, []byte(report.String()), 0644)
}
```

**Run Isolation Verification:**
```bash
go run {OUTPUT_DIR}/templates/isolation_verifier.go 20
```

### 1.3 Over-Mocking Detection

**Validates:** Phase 2 (Unit Tests) - Mock Usage Patterns

Detect excessive mocking that prevents real code validation:

**Analysis focuses on:**
- Interface mock implementations
- testify/mock usage patterns
- gomock usage patterns
- Excessive mock setup

---

## Phase 2: Mutation Testing with go-mutesting

**Validates:** Phase 7 (Code Coverage)

### 2.1 go-mutesting Setup

**Install go-mutesting:**

```bash
go install github.com/zimmski/go-mutesting/cmd/go-mutesting@latest
```

**Run Mutation Testing:**

```bash
# Run on entire project
go-mutesting ./...

# Run on specific package
go-mutesting ./pkg/calculator

# Generate detailed report
go-mutesting --verbose ./... > mutation_report.txt

# Run with specific mutators
go-mutesting --mutator branch --mutator expression ./...
```

### 2.2 go-mutesting Mutation Score Analysis

**Interpret Results:**

```
================================================================================
Mutation Testing Results
================================================================================

Files mutated: 25
Mutants generated: 250
Mutants tested: 250

Results:
- PASSED (mutant killed): 205 (82%)
- FAILED (mutant survived): 35 (14%)
- TIMEOUT: 8 (3%)
- SKIPPED: 2 (1%)

Mutation Score: 82%
================================================================================
```

**Severity Classification:**

- **FAILED/Survived (Critical):** Mutations not caught by tests
- **SKIPPED (Critical):** Code not covered by tests
- **TIMEOUT (Medium):** Tests too slow or infinite loops
- **PASSED/Killed (Good):** Tests successfully caught mutations

### 2.3 Analyzing Survived Mutations

Example survived mutation analysis:

```markdown
### Mutation #42: SURVIVED

**File:** calculator.go:15
**Mutator:** CONDITIONAL_BOUNDARY
**Original:** `if discount < 0.0`
**Mutated:** `if discount <= 0.0`
**Status:** SURVIVED ❌

#### Why This Is Critical
Boundary condition changed but tests still pass.
This indicates missing edge case testing.

#### Current Weak Test
```go
func TestCalculateDiscount(t *testing.T) {
	result := CalculateDiscount(100.0, 0.1)
	if result == 0 {
		t.Error("Expected non-zero result") // ❌ Too weak!
	}
}
```

#### Strong Test That Would Catch This
```go
func TestCalculateDiscount(t *testing.T) {
	tests := []struct {
		name     string
		price    float64
		discount float64
		want     float64
	}{
		{"Normal discount", 100.0, 0.1, 90.0},
		{"No discount", 100.0, 0.0, 100.0},
		{"Half discount", 100.0, 0.5, 50.0},
		{"Zero price", 0.0, 0.1, 0.0},
		{"Full discount", 100.0, 1.0, 0.0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CalculateDiscount(tt.price, tt.discount)
			if math.Abs(got-tt.want) > 0.01 {
				t.Errorf("CalculateDiscount(%v, %v) = %v, want %v",
					tt.price, tt.discount, got, tt.want)
			}
		})
	}
}
```
```

### 2.4 Mutation Coverage Heatmap

Module-level mutation score visualization:

```
Package                    | Mutation Score | Status
---------------------------|----------------|--------
example.com/core/calc      | 95%           | ✅ Excellent
example.com/core/valid     | 85%           | ✅ Good
example.com/api/handler    | 65%           | ⚠️ Needs Improvement
example.com/util/format    | 45%           | ❌ Critical
```

---

## Phase 3: Integration & E2E Test Quality

**Validates:** Phase 3 (Test Cases)

### 3.1 Real Dependency Validation

**Weak Integration Test (Over-Mocked):**
```go
func TestUserWorkflow_Weak(t *testing.T) {
	// Everything mocked - NOT an integration test!
	mockRepo := &MockUserRepository{}
	mockEmail := &MockEmailService{}
	mockValidator := &MockValidator{}

	mockRepo.On("FindByID", 1).Return(&User{ID: 1}, nil)
	mockValidator.On("Validate", mock.Anything).Return(true)
	mockEmail.On("Send", mock.Anything).Return(nil)

	service := NewUserService(mockRepo, mockEmail, mockValidator)

	// Only validates mock interactions
	err := service.ProcessUser(context.Background(), 1)
	assert.NoError(t, err)
}
```

**Strong Integration Test:**
```go
func TestUserWorkflowIntegration_Strong(t *testing.T) {
	// Use real test database
	db := setupTestDB(t)
	defer db.Close()

	// Create real user in database
	user := &User{
		Email: "test@example.com",
		Name:  "Test User",
	}
	err := db.Create(user).Error
	require.NoError(t, err)

	// Only mock external email service
	mockEmail := &MockEmailService{}
	mockEmail.On("Send", mock.MatchedBy(func(email *Email) bool {
		return email.To == "test@example.com" &&
			strings.Contains(email.Subject, "Processing Complete")
	})).Return(nil)

	// Use real repository and validator
	repo := NewUserRepository(db)
	validator := NewUserValidator()
	service := NewUserService(repo, mockEmail, validator)

	// Test real workflow
	ctx := context.Background()
	err = service.ProcessUser(ctx, user.ID)
	require.NoError(t, err)

	// Validate real database changes
	var processed User
	err = db.First(&processed, user.ID).Error
	require.NoError(t, err)
	assert.True(t, processed.IsProcessed)
	assert.NotNil(t, processed.ProcessedAt)

	// Verify email was sent
	mockEmail.AssertExpectations(t)
}
```

### 3.2 Table-Driven Test Validation

Verify proper use of Go's table-driven test pattern:

**Strong Table-Driven Test:**
```go
func TestCalculator(t *testing.T) {
	tests := []struct {
		name    string
		a, b    int
		want    int
		wantErr bool
	}{
		{"positive numbers", 10, 5, 15, false},
		{"negative numbers", -10, -5, -15, false},
		{"mixed signs", 10, -5, 5, false},
		{"zero values", 0, 0, 0, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := Add(tt.a, tt.b)

			if (err != nil) != tt.wantErr {
				t.Errorf("Add() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if got != tt.want {
				t.Errorf("Add() = %v, want %v", got, tt.want)
			}
		})
	}
}
```

---

## Phase 4: CI/CD Pipeline Validation

**Validates:** Phase 6 (Maintenance & CI/CD)

### 4.1 Flaky Test Detection

**Go test with -count flag:**

```bash
# Run tests multiple times
go test -count=100 ./...

# Run specific test multiple times
go test -count=100 -run TestFlaky ./...

# With race detector
go test -race -count=50 ./...
```

---

## Phase 5: Continuous Monitoring Setup

**Create:** `{OUTPUT_DIR}/templates/continuous_monitoring.sh`

```bash
#!/bin/bash
# Continuous Test Quality Monitoring Setup for Go

set -e

echo "Setting up continuous test quality monitoring..."

# Create monitoring directory
mkdir -p test_quality_monitoring

# Create daily mutation testing job
cat > test_quality_monitoring/daily_mutation_test.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="mutation_reports/$DATE"
mkdir -p "$OUTPUT_DIR"

echo "Running go-mutesting mutation testing..."
go-mutesting --verbose ./... > "$OUTPUT_DIR/mutation_report.txt"

# Extract mutation score
KILLED=$(grep "PASSED" "$OUTPUT_DIR/mutation_report.txt" | wc -l)
TOTAL=$(grep -E "(PASSED|FAILED)" "$OUTPUT_DIR/mutation_report.txt" | wc -l)
SCORE=$(echo "scale=2; $KILLED * 100 / $TOTAL" | bc)

echo "Mutation Score: $SCORE%" > "$OUTPUT_DIR/score.txt"

# Alert if score drops below threshold
THRESHOLD=80
if (( $(echo "$SCORE < $THRESHOLD" | bc -l) )); then
    echo "⚠️  ALERT: Mutation score $SCORE below threshold $THRESHOLD"
fi
EOF

chmod +x test_quality_monitoring/daily_mutation_test.sh

# Create weekly quality report
cat > test_quality_monitoring/weekly_quality_report.sh <<'EOF'
#!/bin/bash
DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="quality_reports/$DATE"
mkdir -p "$OUTPUT_DIR"

echo "Running comprehensive quality analysis..."

go run templates/tautological_detector.go ./ > "$OUTPUT_DIR/tautological.txt"
go run templates/isolation_verifier.go 20 > "$OUTPUT_DIR/isolation.txt"

# Coverage analysis
go test -coverprofile="$OUTPUT_DIR/coverage.out" ./...
go tool cover -html="$OUTPUT_DIR/coverage.out" -o "$OUTPUT_DIR/coverage.html"

echo "✅ Weekly quality report generated in $OUTPUT_DIR"
EOF

chmod +x test_quality_monitoring/weekly_quality_report.sh

echo "✅ Continuous monitoring setup complete!"
```

---

## Weak vs. Strong Test Examples

### Example 1: Table-Driven Tests

**❌ Weak (Repetitive):**
```go
func TestAdd1(t *testing.T) {
	result := Add(2, 3)
	if result != 5 {
		t.Errorf("Expected 5, got %d", result)
	}
}

func TestAdd2(t *testing.T) {
	result := Add(-2, 3)
	if result != 1 {
		t.Errorf("Expected 1, got %d", result)
	}
}

func TestAdd3(t *testing.T) {
	result := Add(0, 0)
	if result != 0 {
		t.Errorf("Expected 0, got %d", result)
	}
}
```

**✅ Strong (Table-Driven):**
```go
func TestAdd(t *testing.T) {
	tests := []struct {
		name string
		a, b int
		want int
	}{
		{"positive numbers", 2, 3, 5},
		{"negative and positive", -2, 3, 1},
		{"both zero", 0, 0, 0},
		{"both negative", -5, -3, -8},
		{"large numbers", 1000000, 2000000, 3000000},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := Add(tt.a, tt.b)
			if got != tt.want {
				t.Errorf("Add(%d, %d) = %d, want %d",
					tt.a, tt.b, got, tt.want)
			}
		})
	}
}
```

### Example 2: Context and Cleanup

**❌ Weak (No Cleanup):**
```go
func TestDatabaseOperation(t *testing.T) {
	db := setupTestDB()
	// No cleanup - resource leak!

	user := &User{Name: "Test"}
	db.Create(user)

	assert.NotNil(t, user.ID)
}
```

**✅ Strong (Proper Cleanup):**
```go
func TestDatabaseOperation(t *testing.T) {
	db := setupTestDB(t)
	t.Cleanup(func() {
		db.Close()
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	t.Cleanup(cancel)

	user := &User{Name: "Test"}
	err := db.WithContext(ctx).Create(user).Error
	require.NoError(t, err)
	assert.NotEqual(t, 0, user.ID)
}
```

### Example 3: Error Testing

**❌ Weak (Generic Error Check):**
```go
func TestDivideError(t *testing.T) {
	_, err := Divide(10, 0)
	if err == nil {
		t.Error("Expected error for division by zero")
	}
}
```

**✅ Strong (Specific Error Validation):**
```go
func TestDivideErrors(t *testing.T) {
	tests := []struct {
		name      string
		a, b      float64
		wantErr   bool
		errString string
	}{
		{
			name:      "division by zero",
			a:         10,
			b:         0,
			wantErr:   true,
			errString: "division by zero",
		},
		{
			name:      "NaN input",
			a:         math.NaN(),
			b:         5,
			wantErr:   true,
			errString: "invalid input: NaN",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := Divide(tt.a, tt.b)

			if tt.wantErr {
				require.Error(t, err)
				assert.Contains(t, err.Error(), tt.errString)
			} else {
				require.NoError(t, err)
			}
		})
	}
}
```

[Continue with 12+ more examples...]

---

## Validation Matrix

| Phase | What We Validate | Detection Method | Severity Threshold |
|-------|------------------|------------------|-------------------|
| **Test Structure** (Phase 1) | Go test discovery, build tags | go test -list | Critical if >10% tests not discovered |
| **Unit Tests** (Phase 2) | Test isolation, table-driven patterns | AST parsing, go test -shuffle | Critical if >5% execution-only tests |
| **Test Cases** (Phase 3) | Integration coverage, real dependencies | Interface analysis | High if >30% integration tests mocked |
| **Mocks & Fixtures** (Phase 4) | Mock usage, testify patterns | Mock call analysis | High if >70% dependencies mocked |
| **Performance Testing** (Phase 5) | Benchmark tests | go test -bench analysis | Medium if no benchmarks |
| **Maintenance & CI/CD** (Phase 6) | Pipeline reliability, flaky tests | go test -count logs | Critical if >2% flaky tests |
| **Code Coverage** (Phase 7) | go test -cover + go-mutesting | Mutation reports | Critical if mutation score <60% |

---

## Success Criteria

After completing this reward hacking validation phase:

- [ ] Overall test quality score >80/100
- [ ] go-mutesting mutation score >80% across all packages
- [ ] Zero critical reward hacking incidents
- [ ] <5% high severity issues
- [ ] 100% test independence verified (go test -shuffle)
- [ ] <2% flaky test rate
- [ ] Continuous monitoring configured with go-mutesting
- [ ] Team trained on table-driven test patterns
- [ ] CI/CD quality gates active
- [ ] Regular audit schedule established

---

**This template validates all 7 previous testing phases and provides comprehensive test quality assurance for Go applications using the testing package, testify, and go-mutesting mutation testing.**
