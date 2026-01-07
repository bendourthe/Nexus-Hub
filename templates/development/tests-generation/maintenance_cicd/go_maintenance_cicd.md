---
template_id: go_maintenance_cicd
template_name: Maintenance & CI/CD - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: tests_generation
phase: maintenance_cicd
phase_number: 7
difficulty: intermediate
estimated_time_hours: 3-5
prerequisites:

  - tests_generation/code_coverage/go_code_coverage.md
related_templates:

  - tests_generation/reward_hacking/go_reward_hacking.md
tools:

  - go test (1.23+)

  - testify
tags:

  - test-development

  - go
---
# Go Test Maintenance & CI/CD Integration

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                   ► │ [COMPLETE]
│ Phase 6: Code Coverage                         ► │ [COMPLETE]
│ Phase 7: Maintenance & CI/CD                    ► │ ● CURRENT
│ Phase 8: Reward Hacking Validation                 ► │ [NEXT]
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 6 (Code Coverage) should be completed first
**Next Step:** Phase 8 (Reward Hacking Validation)

---


## Objective
Establish comprehensive test automation infrastructure, integrate tests into CI/CD pipelines, implement quality gates, manage test maintenance, handle flaky tests, optimize test execution, and ensure sustainable testing practices for Go projects.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/maintenance_cicd/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/maintenance_cicd/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### CI/CD Configuration

- [ ] GitHub Actions/GitLab CI pipeline configured

- [ ] Test stages defined (unit, integration, e2e)

- [ ] Parallel execution enabled

- [ ] Test result reporting set up

- [ ] Artifact storage configured

### Quality Gates

- [ ] Code coverage threshold enforced (80%+)

- [ ] Test pass rate requirement set (100%)

- [ ] Performance regression checks enabled

- [ ] Security scanning integrated

- [ ] Deployment gates configured

### Test Maintenance

- [ ] Flaky test detection implemented

- [ ] Test execution time monitoring enabled

- [ ] Obsolete test cleanup process established

- [ ] Test documentation maintained

- [ ] Test data management automated

### Pre-commit Hooks

- [ ] Code formatting checks (gofmt, gofumpt)

- [ ] Linting (golangci-lint)

- [ ] Static analysis (go vet, staticcheck)

- [ ] Fast test subset execution

- [ ] Commit hooks configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Test Maintenance & CI/CD Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/maintenance_cicd"
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

Please implement comprehensive test automation and maintenance infrastructure for this Go project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: CI/CD Pipeline Configuration

### GitHub Actions Setup

**Create `.github/workflows/tests.yml`**:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  GO_VERSION: '1.21'

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}
          cache: true

      - name: Check formatting
        run: |
          if [ "$(gofmt -s -l . | wc -l)" -gt 0 ]; then
            echo "Code is not formatted. Run: gofmt -s -w ."
            gofmt -s -l .
            exit 1
          fi

      - name: Install golangci-lint
        run: |
          curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin v1.55.2

      - name: Run golangci-lint
        run: golangci-lint run --timeout 5m

      - name: Run go vet
        run: go vet ./...

      - name: Install staticcheck
        run: go install honnef.co/go/tools/cmd/staticcheck@latest

      - name: Run staticcheck
        run: staticcheck ./...

  unit-tests:
    name: Unit Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        go-version: ['1.20', '1.21', '1.22']

    steps:

      - uses: actions/checkout@v3

      - name: Set up Go ${{ matrix.go-version }}
        uses: actions/setup-go@v4
        with:
          go-version: ${{ matrix.go-version }}
          cache: true

      - name: Download dependencies
        run: go mod download

      - name: Run unit tests
        run: |
          go test -v -race -coverprofile=coverage.txt -covermode=atomic \
            -run="^Test[^Integration]" ./...

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.txt
          flags: unit-tests
          name: codecov-${{ matrix.os }}-${{ matrix.go-version }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.go-version }}
          path: |
            coverage.txt
            test-report.json

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:

          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:

          - 6379:6379

    steps:

      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}
          cache: true

      - name: Download dependencies
        run: go mod download

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb?sslmode=disable
          REDIS_URL: redis://localhost:6379
        run: |
          go test -v -race -coverprofile=coverage.txt -covermode=atomic \
            -run="TestIntegration" ./...

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.txt
          flags: integration-tests

  benchmark:
    name: Benchmark Tests
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}
          cache: true

      - name: Run benchmarks
        run: |
          go test -bench=. -benchmem -run=^$ ./... | tee benchmark.txt

      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark.txt

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:

      - uses: actions/checkout@v3

      - name: Set up Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}
          cache: true

      - name: Run gosec security scanner
        run: |
          go install github.com/securego/gosec/v2/cmd/gosec@latest
          gosec -fmt json -out gosec-report.json ./...

      - name: Run govulncheck
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          govulncheck ./...

      - name: Upload security reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: gosec-report.json

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, integration-tests, security]
    steps:

      - name: Quality gate passed
        run: echo "All quality checks passed!"
```

### GitLab CI Configuration

**Create `.gitlab-ci.yml`**:

```yaml
stages:

  - lint

  - test

  - quality

  - deploy

variables:
  GO_VERSION: "1.21"
  GOPATH: "$CI_PROJECT_DIR/.go"

cache:
  paths:

    - .go/pkg/mod/

before_script:

  - mkdir -p .go

  - go mod download

lint:
  stage: lint
  image: golang:${GO_VERSION}
  script:

    - gofmt -l .

    - test -z "$(gofmt -l .)"

    - go vet ./...

    - curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s v1.55.2

    - ./bin/golangci-lint run --timeout 5m

unit-tests:
  stage: test
  image: golang:${GO_VERSION}
  script:

    - go test -v -race -coverprofile=coverage.txt -covermode=atomic -run="^Test[^Integration]" ./...

    - go tool cover -func=coverage.txt
  coverage: '/total:\s+\(statements\)\s+(\d+\.\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.txt
    paths:

      - coverage.txt

integration-tests:
  stage: test
  image: golang:${GO_VERSION}
  services:

    - postgres:14

    - redis:7
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: testpass
    DATABASE_URL: postgresql://postgres:testpass@postgres:5432/testdb?sslmode=disable
  script:

    - go test -v -race -coverprofile=coverage.txt -covermode=atomic -run="TestIntegration" ./...
  artifacts:
    paths:

      - coverage.txt

quality-gate:
  stage: quality
  image: golang:${GO_VERSION}
  script:

    - go tool cover -func=coverage.txt | grep total | awk '{if ($3+0 < 80.0) exit 1}'
  needs:

    - unit-tests

    - integration-tests
```

## Phase 2: Quality Gates Configuration

### Coverage Configuration

**Create `.coveragerc` or use go tool cover**:

```bash
# Check coverage threshold
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total | \
  awk '{if ($3+0 < 80.0) {print "Coverage below 80%: " $3; exit 1}}'
```

**Create `scripts/check_coverage.sh`**:

```bash
#!/bin/bash
set -e

THRESHOLD=80.0
COVERAGE_FILE="coverage.out"

# Run tests with coverage
go test -coverprofile=$COVERAGE_FILE ./...

# Calculate coverage
COVERAGE=$(go tool cover -func=$COVERAGE_FILE | grep total | awk '{print $3}' | sed 's/%//')

echo "Coverage: ${COVERAGE}%"

# Check threshold
if (( $(echo "$COVERAGE < $THRESHOLD" | bc -l) )); then
    echo "❌ Coverage $COVERAGE% is below threshold $THRESHOLD%"
    exit 1
fi

echo "✅ Coverage $COVERAGE% meets threshold $THRESHOLD%"
```

### Test Pass Rate Gate

```go
// tests/quality_gate.go
package tests

import (
    "fmt"
    "os"
    "testing"
)

var (
    totalTests  int
    passedTests int
    failedTests int
)

// QualityGateReporter tracks test results
type QualityGateReporter struct{}

// RecordResult records test outcome
func (q *QualityGateReporter) RecordResult(t *testing.T, passed bool) {
    totalTests++
    if passed {
        passedTests++
    } else {
        failedTests++
    }
}

// Report prints quality gate summary
func (q *QualityGateReporter) Report() {
    passRate := 0.0
    if totalTests > 0 {
        passRate = float64(passedTests) / float64(totalTests) * 100
    }

    fmt.Println("\n" + "============================================================")
    fmt.Printf("Test Pass Rate: %.1f%% (%d/%d)\n", passRate, passedTests, totalTests)
    fmt.Println("============================================================")

    if passRate < 100 {
        fmt.Println("⚠️  WARNING: Not all tests passed")
        fmt.Printf("Failed tests: %d\n", failedTests)
    } else {
        fmt.Println("✅ Quality Gate Passed: All tests passed")
    }

    if failedTests > 0 {
        fmt.Println("\n❌ Quality Gate Failed: Some tests did not pass")
        fmt.Println("All tests must pass before merge.")
        os.Exit(1)
    }
}
```

### Performance Regression Gate

```go
// tests/benchmark/performance_gate.go
package benchmark

import (
    "encoding/json"
    "fmt"
    "os"
    "testing"
)

const (
    baselineFile        = "tests/benchmark/baseline.json"
    regressionThreshold = 0.10 // 10%
)

// PerformanceGate tracks benchmark performance
type PerformanceGate struct {
    benchmarks map[string]int64
    baseline   map[string]int64
}

// NewPerformanceGate creates a new performance gate
func NewPerformanceGate() *PerformanceGate {
    pg := &PerformanceGate{
        benchmarks: make(map[string]int64),
        baseline:   make(map[string]int64),
    }
    pg.loadBaseline()
    return pg
}

func (pg *PerformanceGate) loadBaseline() {
    data, err := os.ReadFile(baselineFile)
    if err != nil {
        return // No baseline yet
    }
    json.Unmarshal(data, &pg.baseline)
}

// RecordBenchmark records a benchmark result
func (pg *PerformanceGate) RecordBenchmark(name string, nsPerOp int64) {
    pg.benchmarks[name] = nsPerOp
}

// CheckRegressions checks for performance regressions
func (pg *PerformanceGate) CheckRegressions(t *testing.T) {
    if len(pg.baseline) == 0 {
        pg.saveBaseline()
        fmt.Println("📊 Baseline performance metrics saved")
        return
    }

    hasRegressions := false
    for name, current := range pg.benchmarks {
        if baseline, ok := pg.baseline[name]; ok {
            regression := float64(current-baseline) / float64(baseline)

            if regression > regressionThreshold {
                hasRegressions = true
                fmt.Printf("  %s: %.1f%% slower\n", name, regression*100)
                fmt.Printf("    Baseline: %dns, Current: %dns\n", baseline, current)
            }
        }
    }

    if hasRegressions {
        t.Fatal("❌ Performance Regression Detected")
    }

    fmt.Println("✅ Performance Gate Passed: No regressions detected")
}

func (pg *PerformanceGate) saveBaseline() {
    data, _ := json.MarshalIndent(pg.benchmarks, "", "  ")
    os.WriteFile(baselineFile, data, 0644)
}
```

## Phase 3: Pre-commit Hooks

### Install Pre-commit Framework

```bash
pip install pre-commit
```

**Create `.pre-commit-config.yaml`**:

```yaml
repos:

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:

      - id: trailing-whitespace

      - id: end-of-file-fixer

      - id: check-yaml

      - id: check-added-large-files
        args: ['--maxkb=1000']

      - id: check-merge-conflict

      - id: detect-private-key

  - repo: local
    hooks:

      - id: go-fmt
        name: Format Go code
        entry: gofmt -s -w
        language: system
        files: \.go$
        pass_filenames: true

      - id: go-imports
        name: Fix Go imports
        entry: goimports -w
        language: system
        files: \.go$
        pass_filenames: true

      - id: go-vet
        name: Run go vet
        entry: go vet
        language: system
        files: \.go$
        pass_filenames: false
        args: ['./...']

      - id: golangci-lint
        name: Run golangci-lint
        entry: golangci-lint run
        language: system
        files: \.go$
        pass_filenames: false
        args: ['--timeout', '5m']

      - id: go-test-fast
        name: Run fast tests
        entry: go test
        language: system
        pass_filenames: false
        args: ['-short', './...']
        always_run: true
```

### Install Hooks

```bash
# Install the git hook scripts
pre-commit install

# Run against all files (optional)
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate
```

### golangci-lint Configuration

**Create `.golangci.yml`**:

```yaml
run:
  timeout: 5m
  tests: true

linters:
  enable:

    - gofmt

    - goimports

    - govet

    - staticcheck

    - errcheck

    - gosimple

    - ineffassign

    - unused

    - typecheck

    - gosec

    - misspell

    - unconvert

    - unparam

    - gocyclo

    - goconst

    - gocritic

linters-settings:
  gocyclo:
    min-complexity: 15
  goconst:
    min-len: 3
    min-occurrences: 3
  gosec:
    severity: medium
  errcheck:
    check-type-assertions: true
    check-blank: true

issues:
  exclude-rules:

    - path: _test\.go
      linters:

        - gosec

        - errcheck
```

## Phase 4: Test Parallelization

### Enable Parallel Test Execution

```go
// Run tests in parallel
func TestParallelExample(t *testing.T) {
    t.Parallel() // Enable parallel execution

    tests := []struct {
        name string
        input int
        want int
    }{
        {"case1", 1, 2},
        {"case2", 2, 4},
        {"case3", 3, 6},
    }

    for _, tt := range tests {
        tt := tt // Capture range variable
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel() // Each subtest runs in parallel

            got := tt.input * 2
            if got != tt.want {
                t.Errorf("got %d, want %d", got, tt.want)
            }
        })
    }
}
```

### Control Parallelism

```bash
# Set max parallel tests
go test -parallel 4 ./...

# Use short mode for fast tests
go test -short ./...
```

### Handle Non-Thread-Safe Tests

```go
// tests/integration/database_test.go
package integration

import (
    "sync"
    "testing"
)

// Use a global lock for serial execution
var dbLock sync.Mutex

func TestDatabaseMigration001(t *testing.T) {
    dbLock.Lock()
    defer dbLock.Unlock()

    // Test implementation
}

func TestDatabaseMigration002(t *testing.T) {
    dbLock.Lock()
    defer dbLock.Unlock()

    // Test implementation
}
```

## Phase 5: Flaky Test Management

### Retry Mechanism

```go
// tests/retry.go
package tests

import (
    "testing"
    "time"
)

// RetryTest retries a test function multiple times
func RetryTest(t *testing.T, maxRetries int, delay time.Duration, testFn func(t *testing.T)) {
    t.Helper()

    for attempt := 1; attempt <= maxRetries; attempt++ {
        // Create a sub-test for each attempt
        passed := t.Run("", testFn)

        if passed {
            return
        }

        if attempt < maxRetries {
            t.Logf("Test failed (attempt %d/%d), retrying...", attempt, maxRetries)
            time.Sleep(delay)
        }
    }

    t.Fatalf("Test failed after %d attempts", maxRetries)
}

// Usage
func TestFlakyExternalAPI(t *testing.T) {
    RetryTest(t, 3, 2*time.Second, func(t *testing.T) {
        // Test implementation
        resp := callExternalAPI()
        if resp.StatusCode != 200 {
            t.Errorf("expected 200, got %d", resp.StatusCode)
        }
    })
}
```

### Track Flaky Tests

```go
// tests/flaky_tracker.go
package tests

import (
    "encoding/json"
    "fmt"
    "os"
    "sync"
    "time"
)

const flakyLogFile = "tests/flaky-tests.json"

// FlakyTestInfo stores information about flaky tests
type FlakyTestInfo struct {
    Count    int       `json:"count"`
    LastSeen time.Time `json:"last_seen"`
}

// FlakyTestTracker tracks flaky test occurrences
type FlakyTestTracker struct {
    mu         sync.Mutex
    flakyTests map[string]*FlakyTestInfo
}

// NewFlakyTestTracker creates a new tracker
func NewFlakyTestTracker() *FlakyTestTracker {
    tracker := &FlakyTestTracker{
        flakyTests: make(map[string]*FlakyTestInfo),
    }
    tracker.loadLog()
    return tracker
}

func (ft *FlakyTestTracker) loadLog() {
    data, err := os.ReadFile(flakyLogFile)
    if err != nil {
        return // No log yet
    }
    json.Unmarshal(data, &ft.flakyTests)
}

// RecordFlaky records a flaky test occurrence
func (ft *FlakyTestTracker) RecordFlaky(testName string) {
    ft.mu.Lock()
    defer ft.mu.Unlock()

    if _, exists := ft.flakyTests[testName]; !exists {
        ft.flakyTests[testName] = &FlakyTestInfo{}
    }

    ft.flakyTests[testName].Count++
    ft.flakyTests[testName].LastSeen = time.Now()
}

// SaveLog saves the flaky test log
func (ft *FlakyTestTracker) SaveLog() error {
    ft.mu.Lock()
    defer ft.mu.Unlock()

    data, err := json.MarshalIndent(ft.flakyTests, "", "  ")
    if err != nil {
        return err
    }

    return os.WriteFile(flakyLogFile, data, 0644)
}

// Report prints flaky test report
func (ft *FlakyTestTracker) Report() {
    ft.mu.Lock()
    defer ft.mu.Unlock()

    if len(ft.flakyTests) == 0 {
        return
    }

    fmt.Println("\n⚠️  Top Flaky Tests:")
    for test, info := range ft.flakyTests {
        fmt.Printf("  %s: %d failures\n", test, info.Count)
    }
}
```

## Phase 6: Test Maintenance Practices

### Monitor Test Execution Time

```go
// tests/slow_test_detector.go
package tests

import (
    "fmt"
    "sort"
    "sync"
    "testing"
    "time"
)

const slowTestThreshold = 1 * time.Second

// SlowTest represents a slow test
type SlowTest struct {
    Name     string
    Duration time.Duration
}

// SlowTestDetector tracks slow tests
type SlowTestDetector struct {
    mu        sync.Mutex
    slowTests []SlowTest
}

// NewSlowTestDetector creates a new detector
func NewSlowTestDetector() *SlowTestDetector {
    return &SlowTestDetector{
        slowTests: make([]SlowTest, 0),
    }
}

// CheckTest checks if a test is slow
func (std *SlowTestDetector) CheckTest(t *testing.T, start time.Time) {
    duration := time.Since(start)

    if duration > slowTestThreshold {
        std.mu.Lock()
        defer std.mu.Unlock()

        std.slowTests = append(std.slowTests, SlowTest{
            Name:     t.Name(),
            Duration: duration,
        })

        fmt.Printf("\n⚠️  Slow test: %s (%.2fs)\n", t.Name(), duration.Seconds())
    }
}

// Report prints slow test report
func (std *SlowTestDetector) Report() {
    std.mu.Lock()
    defer std.mu.Unlock()

    if len(std.slowTests) == 0 {
        return
    }

    // Sort by duration descending
    sort.Slice(std.slowTests, func(i, j int) bool {
        return std.slowTests[i].Duration > std.slowTests[j].Duration
    })

    fmt.Println("\n" + "============================================================")
    fmt.Println("Slow Tests Detected:")

    limit := 10
    if len(std.slowTests) < limit {
        limit = len(std.slowTests)
    }

    for i := 0; i < limit; i++ {
        test := std.slowTests[i]
        fmt.Printf("  %.2fs: %s\n", test.Duration.Seconds(), test.Name)
    }

    fmt.Println("============================================================")
}

// Usage in tests
func TestWithSlowDetection(t *testing.T) {
    detector := NewSlowTestDetector()
    defer detector.Report()

    start := time.Now()
    defer detector.CheckTest(t, start)

    // Test implementation
}
```

### Document Test Purpose

```go
// tests/auth/authentication_test.go
package auth

/*
User Authentication Test Suite

Purpose:
  Validate user login, logout, and session management functionality.

Coverage:

  - Valid credential login

  - Invalid credential handling

  - Session token generation and validation

  - Multi-factor authentication flow

  - Password reset process

Maintenance Notes:

  - Update TestValidLogin() if authentication logic changes

  - mockEmailService fixture required for password reset tests

  - Tests use in-memory database for speed

  - External API calls are mocked

Dependencies:

  - auth.Service

  - user.Repository

  - jwt.TokenProvider

Last Review: 2024-01-15
Reviewed By: alice@example.com
*/

import (
    "testing"
)

func TestUserAuthentication(t *testing.T) {
    // Test implementation
}
```

## Phase 7: Test Result Reporting

### JSON Test Report

```go
// tests/reporter.go
package tests

import (
    "encoding/json"
    "fmt"
    "os"
    "testing"
    "time"
)

// TestResult represents a single test result
type TestResult struct {
    Name           string        `json:"name"`
    Status         string        `json:"status"`
    Duration       time.Duration `json:"duration"`
    FailureMessage string        `json:"failure_message,omitempty"`
}

// TestReport represents the complete test report
type TestReport struct {
    Timestamp time.Time `json:"timestamp"`
    Summary   struct {
        Total    int           `json:"total"`
        Passed   int           `json:"passed"`
        Failed   int           `json:"failed"`
        Duration time.Duration `json:"duration"`
    } `json:"summary"`
    Results []TestResult `json:"results"`
}

// CustomTestReporter generates custom test reports
type CustomTestReporter struct {
    report TestReport
    start  time.Time
}

// NewCustomTestReporter creates a new reporter
func NewCustomTestReporter() *CustomTestReporter {
    reporter := &CustomTestReporter{
        start: time.Now(),
    }
    reporter.report.Timestamp = time.Now()
    reporter.report.Results = make([]TestResult, 0)
    return reporter
}

// RecordResult records a test result
func (ctr *CustomTestReporter) RecordResult(name, status string, duration time.Duration, failureMessage string) {
    ctr.report.Summary.Total++

    if status == "passed" {
        ctr.report.Summary.Passed++
    } else {
        ctr.report.Summary.Failed++
    }

    ctr.report.Results = append(ctr.report.Results, TestResult{
        Name:           name,
        Status:         status,
        Duration:       duration,
        FailureMessage: failureMessage,
    })
}

// GenerateReport generates and saves the report
func (ctr *CustomTestReporter) GenerateReport(outputPath string) error {
    ctr.report.Summary.Duration = time.Since(ctr.start)

    data, err := json.MarshalIndent(ctr.report, "", "  ")
    if err != nil {
        return err
    }

    if err := os.WriteFile(outputPath, data, 0644); err != nil {
        return err
    }

    fmt.Printf("\n📊 Custom test report saved to: %s\n", outputPath)
    return nil
}
```

### Coverage Report

```bash
# Generate HTML coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out -o ${OUTPUT_DIR}/exports/coverage.html

# Generate function coverage report
go tool cover -func=coverage.out

# Generate detailed report
go tool cover -func=coverage.out | sort -k3 -n
```

## Output Format

Please provide a comprehensive CI/CD and maintenance implementation with the following structure:

### CI/CD Configuration Summary

- **Platform**: [GitHub Actions/GitLab CI/Jenkins]

- **Pipeline Stages**: [list stages]

- **Parallel Execution**: [enabled/disabled, worker count]

- **Test Types Automated**: [unit, integration, benchmark]

- **Quality Gates**: [list gates]

### Quality Gate Configuration
| Gate | Threshold | Current | Status |
|------|-----------|---------|--------|
| Code Coverage | 80% | [value] | ✅/❌ |
| Test Pass Rate | 100% | [value] | ✅/❌ |
| Performance | <10% regression | [value] | ✅/❌ |

### Pre-commit Hooks Configured

- [ ] Code formatting (gofmt, gofumpt)

- [ ] Import organization (goimports)

- [ ] Linting (golangci-lint)

- [ ] Static analysis (go vet, staticcheck)

- [ ] Fast test execution

- [ ] Coverage check

### Test Maintenance Status
**Slow Tests Identified**:
| Test | Duration | Recommendation |
|------|----------|----------------|
| [test_name] | [time] | [optimization] |

**Flaky Tests**:
| Test | Failure Rate | Action |
|------|--------------|--------|
| [test_name] | [rate] | [fix planned] |

### Test Execution Metrics

- **Total Tests**: [count]

- **Average Execution Time**: [duration]

- **Parallel Workers**: [count]

- **Tests per Second**: [rate]

- **Coverage**: [percentage]

### CI/CD Pipeline Visualization
```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
│  Lint   │────▶│   Unit   │────▶│Integration │────▶│ Deploy │
└─────────┘     │  Tests   │     │   Tests    │     └────────┘
                └──────────┘     └────────────┘
                     │                 │
                     ▼                 ▼
                ┌─────────┐       ┌─────────┐
                │Coverage │       │Security │
                │  Gate   │       │  Scan   │
                └─────────┘       └─────────┘
```

### Best Practices Implemented

- [ ] All tests automated in CI/CD

- [ ] Quality gates prevent regressions

- [ ] Pre-commit hooks catch issues early

- [ ] Parallel execution for speed

- [ ] Flaky tests tracked and fixed

- [ ] Test maintenance schedule established

### Next Steps

- [ ] Monitor and optimize slow tests

- [ ] Fix identified flaky tests

- [ ] Review and update obsolete tests

- [ ] Enhance test documentation

- [ ] Set up test result dashboard

- [ ] Schedule regular test maintenance reviews

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

1. **Complete CI/CD pipeline configuration** (GitHub Actions or GitLab CI)

2. **Quality gate implementation** with thresholds (go test, go tool cover)

3. **Pre-commit hook configuration** with all checks

4. **Test parallelization setup** for faster execution

5. **Flaky test detection and tracking** system

6. **Test maintenance procedures** and documentation

7. **Test reporting infrastructure** with dashboards

8. **Execution metrics and monitoring** setup
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
