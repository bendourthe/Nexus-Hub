# Go Testing Review

## Objective
Systematically assess test suite quality, coverage, and effectiveness. Identify testing gaps, unreliable tests, and opportunities to improve confidence in code correctness and regression prevention.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/testing_review/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/testing_review/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Test Coverage

- [ ] Line coverage measured (target: 80%+)

- [ ] Branch coverage assessed

- [ ] Critical paths fully tested

- [ ] Edge cases and error conditions covered

- [ ] Coverage gaps identified and prioritized

### Test Quality

- [ ] Tests follow AAA pattern (Arrange, Act, Assert)

- [ ] Test names clearly describe what is being tested

- [ ] Tests are independent and isolated

- [ ] Assertions are specific and meaningful

- [ ] Test data is representative and comprehensive

### Test Organization

- [ ] Test files located alongside source (*_test.go)

- [ ] Test helpers and fixtures well-organized

- [ ] Table-driven tests used appropriately

- [ ] Benchmark tests present for critical operations

- [ ] Example tests provided for documentation

### Test Types Coverage

- [ ] Unit tests present for core logic

- [ ] Integration tests cover component interactions

- [ ] End-to-end tests validate critical user flows

- [ ] Benchmark tests for performance-critical code

- [ ] Fuzz tests for input validation

### Test Reliability

- [ ] Flaky tests identified

- [ ] Tests run independently (no order dependency)

- [ ] External dependencies properly mocked

- [ ] Test data properly managed

- [ ] Tests run consistently in different environments

### CI/CD Integration

- [ ] Tests run automatically on commits/PRs

- [ ] Test failures block merges

- [ ] Coverage reports generated

- [ ] Test execution time reasonable

- [ ] Parallel test execution configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Testing Review

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/testing_review"
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

Please perform a comprehensive testing review of this Go project following this protocol:

## Phase 1: Test Coverage Analysis

1. **Measure Current Coverage**
   ```bash
   # Run tests with coverage
   go test ./... -cover

   # Generate detailed coverage report
   go test ./... -coverprofile=coverage.out
   go tool cover -html=coverage.out -o ${OUTPUT_DIR}/exports/coverage.html

   # Coverage by package
   go test ./... -coverprofile=coverage.out
   go tool cover -func=coverage.out

   # Coverage with branch analysis
   go test ./... -covermode=count -coverprofile=coverage.out
   ```

2. **Coverage Analysis**
   - Overall coverage percentage
   - Package-by-package coverage breakdown
   - Identify packages with <60% coverage
   - Find critical paths with inadequate coverage
   - Document untested code sections

3. **Coverage Gaps**
   ```bash
   # Find uncovered lines
   go tool cover -func=coverage.out | grep -E '0.0%|[0-5][0-9].[0-9]%'

   # Generate coverage differential (with previous run)
   diff coverage_old.out coverage_new.out
   ```

## Phase 2: Test Suite Inventory

1. **Test Count and Organization**
   ```bash
   # List all tests
   go test ./... -list=.

   # Count tests by package
   go test ./... -v | grep -c "PASS"

   # Find test files
   find . -name "*_test.go" | wc -l
   ```

2. **Test Type Distribution**
   - **Unit Tests**: Count and coverage
   - **Integration Tests**: Count and scope (often in separate build tags)
   - **Benchmark Tests**: Count and critical paths covered
   - **Example Tests**: Count and documentation quality
   - **Fuzz Tests**: Presence and coverage

3. **Test Structure Assessment**
   ```
   project/
   ├── pkg/
   │   ├── module.go
   │   ├── module_test.go      # Unit tests
   │   └── module_bench_test.go # Benchmarks
   ├── internal/
   │   └── service/
   │       ├── service.go
   │       ├── service_test.go
   │       └── testdata/        # Test fixtures
   └── integration_test.go     # Integration tests
   ```

## Phase 3: Test Quality Assessment

1. **Test Pattern Review**
   ```go
   // Good test structure (AAA pattern)
   func TestCreateUser(t *testing.T) {
       // Arrange
       username := "testuser"
       email := "test@example.com"

       // Act
       user, err := CreateUser(username, email)

       // Assert
       if err != nil {
           t.Fatalf("unexpected error: %v", err)
       }
       if user.Username != username {
           t.Errorf("got username %q, want %q", user.Username, username)
       }
   }

   // Check for anti-patterns:
   // - Multiple unrelated test cases in one function
   // - Testing implementation details instead of behavior
   // - Unclear test purpose
   // - Missing or weak assertions
   // - Overly complex setup
   ```

2. **Test Naming Review**
   ```go
   // Good: Descriptive test names
   func TestCreateUser_WithValidData_ReturnsUser(t *testing.T) {}
   func TestCreateUser_WithDuplicateEmail_ReturnsError(t *testing.T) {}
   func TestCreateUser_WithEmptyUsername_ReturnsError(t *testing.T) {}

   // Bad: Vague test names
   func TestUser(t *testing.T) {}  // What about user?
   func Test1(t *testing.T) {}     // What is being tested?
   ```

3. **Table-Driven Tests**
   ```go
   // Evaluate table-driven test usage
   func TestValidateEmail(t *testing.T) {
       tests := []struct {
           name    string
           input   string
           want    bool
           wantErr bool
       }{
           {"valid email", "user@example.com", true, false},
           {"missing @", "userexample.com", false, true},
           {"empty string", "", false, true},
       }

       for _, tt := range tests {
           t.Run(tt.name, func(t *testing.T) {
               got, err := ValidateEmail(tt.input)
               if (err != nil) != tt.wantErr {
                   t.Errorf("ValidateEmail() error = %v, wantErr %v", err, tt.wantErr)
                   return
               }
               if got != tt.want {
                   t.Errorf("ValidateEmail() = %v, want %v", got, tt.want)
               }
           })
       }
   }
   ```

4. **Assertion Quality**
   ```go
   // Good: Specific assertions
   if got != want {
       t.Errorf("got %v, want %v", got, want)
   }

   // Using testify for better assertions
   assert.Equal(t, expected, actual)
   assert.Error(t, err)
   require.NotNil(t, result) // Fails immediately

   // Bad: Weak assertions
   if result == nil {
       t.Error("result is nil")  // Too vague
   }
   ```

## Phase 4: Test Independence & Reliability

1. **Test Isolation Check**
   ```bash
   # Run tests in random order
   go test -shuffle=on ./...

   # Run specific test alone
   go test -run=TestSpecificFunction

   # Run tests multiple times
   go test -count=10 ./...
   ```

2. **Parallel Test Analysis**
   ```go
   // Check for proper parallel test usage
   func TestParallel(t *testing.T) {
       t.Parallel() // Mark test as parallel

       // Ensure no shared state
   }

   // Run parallel tests
   go test -parallel 4 ./...
   ```

3. **Common Flakiness Sources**
   - Tests dependent on external services (not mocked)
   - Time-based tests (time.Now(), sleep)
   - Tests with race conditions
   - Tests dependent on test execution order
   - Tests using random data without seeding
   - Tests dependent on file system state
   - Network timeouts without appropriate handling

4. **Mocking & Test Doubles**
   ```go
   // Check for proper interface mocking
   type UserService interface {
       GetUser(id string) (*User, error)
   }

   // Mock implementation for tests
   type mockUserService struct {
       getUser func(id string) (*User, error)
   }

   func (m *mockUserService) GetUser(id string) (*User, error) {
       if m.getUser != nil {
           return m.getUser(id)
       }
       return nil, errors.New("not implemented")
   }

   // Using gomock (generate mocks)
   //go:generate mockgen -destination=mocks/user_service.go -package=mocks . UserService
   ```

## Phase 5: Test Coverage Gaps Analysis

1. **Critical Path Identification**
   - Authentication and authorization flows
   - Data validation and processing
   - Business logic and calculations
   - Error handling and recovery
   - API handlers
   - Database operations

2. **Untested Code Categories**
   ```bash
   # Identify untested code
   go tool cover -func=coverage.out | awk '$3 < 60 {print $1, $3}'

   # Focus on:
   - Critical business logic without tests
   - Error handling paths not covered
   - Edge cases not tested
   - New code without tests
   - Complex functions without tests
   ```

3. **Missing Test Types**
   - [ ] Happy path scenarios
   - [ ] Error conditions and error types
   - [ ] Boundary values (min, max, zero, negative)
   - [ ] Invalid input handling
   - [ ] Concurrent access scenarios
   - [ ] Context cancellation handling

## Phase 6: Advanced Testing Techniques

1. **Benchmark Tests**
   ```go
   func BenchmarkFunction(b *testing.B) {
       // Setup
       data := generateTestData()

       b.ResetTimer()
       for i := 0; i < b.N; i++ {
           function(data)
       }
   }

   // Run benchmarks
   go test -bench=. -benchmem
   go test -bench=BenchmarkSpecific -count=5
   ```

2. **Fuzz Testing (Go 1.18+)**
   ```go
   func FuzzParseInput(f *testing.F) {
       // Seed corpus
       f.Add("valid input")
       f.Add("edge case")

       f.Fuzz(func(t *testing.T, input string) {
           // Should not panic
           result, err := ParseInput(input)
           if err != nil {
               return
           }
           // Verify invariants
           if result != nil {
               // Additional checks
           }
       })
   }

   // Run fuzzing
   go test -fuzz=FuzzParseInput -fuzztime=30s
   ```

3. **Example Tests**
   ```go
   // Example tests serve as documentation
   func ExampleFunction() {
       result := Function("input")
       fmt.Println(result)
       // Output: expected output
   }

   // Check example test coverage
   go test -v | grep -c "Example"
   ```

4. **Race Detection**
   ```bash
   # Run tests with race detector
   go test -race ./...

   # Build with race detector
   go build -race

   # Integration with CI
   # Always run tests with -race in CI/CD
   ```

## Phase 7: Test Maintainability

1. **Test Code Quality**
   ```bash
   # Run linters on test code
   staticcheck ./...
   golint ./...
   ```
   - Tests follow same quality standards as production code
   - Tests are readable and well-documented
   - Tests avoid duplication (use helpers)
   - Tests use appropriate test fixtures

2. **Test Helpers & Utilities**
   ```go
   // Good: Reusable test helpers
   func createTestUser(t *testing.T, username string) *User {
       t.Helper() // Mark as helper

       user, err := CreateUser(username, "test@example.com")
       if err != nil {
           t.Fatalf("failed to create test user: %v", err)
       }
       return user
   }

   // Setup/Teardown patterns
   func setupTest(t *testing.T) func() {
       // Setup code
       return func() {
           // Teardown code
       }
   }

   func TestWithSetup(t *testing.T) {
       cleanup := setupTest(t)
       defer cleanup()

       // Test code
   }
   ```

3. **Test Data Management**
   ```go
   // Use testdata directory for fixtures
   // project/
   //   ├── module.go
   //   ├── module_test.go
   //   └── testdata/
   //       ├── input.json
   //       └── expected.json

   func loadTestData(t *testing.T, filename string) []byte {
       t.Helper()
       data, err := os.ReadFile(filepath.Join("testdata", filename))
       if err != nil {
           t.Fatalf("failed to load test data: %v", err)
       }
       return data
   }
   ```

## Phase 8: CI/CD Integration Review

1. **Test Automation Assessment**
   ```yaml
   # Example GitHub Actions
   name: Tests
   on: [push, pull_request]
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-go@v4
           with:
             go-version: '1.21'
         - name: Run tests
           run: |
             go test -v -race -coverprofile=coverage.out ./...
             go tool cover -func=coverage.out
         - name: Upload coverage
           uses: codecov/codecov-action@v3
           with:
             file: ./coverage.out
   ```

2. **Quality Gates**
   - [ ] Tests run on every commit/PR
   - [ ] Coverage thresholds enforced
   - [ ] Test failures block merges
   - [ ] Race detector always enabled
   - [ ] Benchmark regression detection

3. **Test Execution Performance**
   ```bash
   # Measure test execution time
   go test -v ./... | grep -E "PASS|FAIL"

   # Identify slow tests
   go test -v ./... 2>&1 | grep -E "--- PASS|--- FAIL" | sort -k3 -r

   # Run tests with timeout
   go test -timeout=30s ./...
   ```

## Output Format

Please provide a comprehensive testing report with the following structure:

### Executive Summary

- **Overall Test Health**: [Excellent/Good/Fair/Poor]

- **Test Coverage**: [percentage]

- **Critical Gaps**: [count and brief description]

- **Test Quality**: [High/Medium/Low]

- **Reliability**: [Stable/Some Flakiness/Unreliable]

### Coverage Metrics

- **Line Coverage**: [%]

- **Package Count**: [total]

- **Tested Packages**: [count with >80% coverage]

- **Untested Packages**: [count with <60% coverage]

**Coverage by Package**:
| Package | Line Coverage | Critical | Untested Lines | Priority |
|---------|---------------|----------|----------------|----------|
| [name] | [%] | [Yes/No] | [count] | [High/Med/Low] |

### Test Suite Inventory

- **Total Tests**: [count]

- **Unit Tests**: [count]

- **Benchmark Tests**: [count]

- **Example Tests**: [count]

- **Fuzz Tests**: [count]

### Critical Coverage Gaps (Priority 1)
| Package/Function | Current Coverage | Risk Level | Impact | Recommendation |
|------------------|------------------|------------|--------|----------------|
| [name] | [%] | [High/Med/Low] | [description] | [test types needed] |

### Test Quality Issues
**Test Smell Detections**:
| Issue | Location | Description | Fix |
|-------|----------|-------------|-----|
| [smell type] | [file:line] | [details] | [recommendation] |

**Common Issues**:

- [ ] Tests with unclear names: [count]

- [ ] Tests with weak assertions: [count]

- [ ] Tests with complex setup: [count]

- [ ] Tests not using t.Helper(): [count]

- [ ] Tests not using table-driven pattern where appropriate: [count]

### Test Reliability Assessment
**Flaky Tests Detected**: [count]
| Test Name | Failure Rate | Root Cause | Fix |
|-----------|--------------|------------|-----|
| [test] | [%] | [reason] | [solution] |

**Race Conditions**: [count from -race]
| Location | Description | Severity |
|----------|-------------|----------|
| [file:line] | [details] | [High/Med/Low] |

### Test Execution Performance

- **Total Execution Time**: [seconds]

- **Slowest Tests**:
  | Test | Duration | Category | Optimization |
  |------|----------|----------|--------------|
  | [name] | [seconds] | [unit/integration] | [suggestion] |

### Missing Test Types

- [ ] **Edge Cases**: [specific gaps]

- [ ] **Error Conditions**: [uncovered error paths]

- [ ] **Boundary Values**: [missing boundary tests]

- [ ] **Integration Points**: [untested interactions]

- [ ] **Benchmarks**: [performance-critical code without benchmarks]

- [ ] **Fuzz Tests**: [input validation without fuzzing]

### Go-Specific Test Patterns
**Best Practices Compliance**:

- [ ] Table-driven tests used appropriately: [Yes/No/Partial]

- [ ] Test helpers marked with t.Helper(): [%]

- [ ] Parallel tests marked with t.Parallel(): [%]

- [ ] Example tests for documentation: [count]

- [ ] Testdata directory used: [Yes/No]

### CI/CD Integration

- **Automated Test Execution**: [Yes/No/Partial]

- **Coverage Reporting**: [Yes/No]

- **Quality Gates**: [Enforced/Not Enforced]

- **Race Detector Enabled**: [Yes/No]

- **Test Parallelization**: [Yes/No]

**Issues**:

- [List of CI/CD testing gaps or issues]

### Recommendations

**Immediate Actions** (Priority 1 - this week):
1. **[Action]**
   - **Rationale**: [why important]
   - **Implementation**: [how to do it]
   - **Effort**: [hours/days]

**Short-term Goals** (Priority 2 - this month):
[List of medium-priority testing improvements]

**Long-term Initiatives** (Priority 3 - this quarter):
[List of strategic testing enhancements]

### Testing Best Practices Implementation
```go
// Recommended test patterns

// 1. Use subtests with t.Run
func TestFeature(t *testing.T) {
    t.Run("subtest1", func(t *testing.T) {
        t.Parallel()
        // test code
    })
    t.Run("subtest2", func(t *testing.T) {
        t.Parallel()
        // test code
    })
}

// 2. Use testify for better assertions (optional)
import "github.com/stretchr/testify/assert"

assert.Equal(t, expected, actual)
assert.NoError(t, err)
require.NotNil(t, result) // Stops test on failure

// 3. Use gomock for interface mocking
//go:generate mockgen -destination=mocks/service.go -package=mocks . Service

// 4. Use golden files for complex outputs
import "github.com/sebdah/goldie/v2"

g := goldie.New(t)
g.Assert(t, "testname", []byte(actualOutput))
```

### Test Coverage Improvement Plan
**Target: [X]% coverage (from current [Y]%)**

**Phase 1** (Week 1-2):

- Add tests for [critical packages]

- Expected coverage gain: +[X]%

**Phase 2** (Week 3-4):

- Add integration tests for [components]

- Expected coverage gain: +[X]%

**Phase 3** (Month 2):

- Add edge case and error condition tests

- Expected coverage gain: +[X]%

### Quality Gates Recommendation
```makefile
# Makefile test targets
.PHONY: test
test:
	go test -v -race -coverprofile=coverage.out ./...
	go tool cover -func=coverage.out

.PHONY: test-coverage
test-coverage: test
	go tool cover -html=coverage.out

.PHONY: test-integration
test-integration:
	go test -v -tags=integration ./...

.PHONY: bench
bench:
	go test -bench=. -benchmem ./...
```

### Next Steps

- [ ] Address critical coverage gaps (Priority 1 items)

- [ ] Fix or investigate flaky tests

- [ ] Implement table-driven tests where appropriate

- [ ] Set up coverage monitoring in CI/CD

- [ ] Add benchmark tests for critical paths

- [ ] Enable race detector in CI/CD

- [ ] Establish team testing guidelines

- [ ] Configure coverage thresholds

## Notes

- Focus on testing critical business logic first

- Aim for meaningful tests, not just coverage percentage

- Use table-driven tests for multiple similar scenarios

- Always run tests with -race in development and CI

- Keep tests fast and reliable

- Treat test code with same quality standards as production code

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/testing_review/analysis_scripts
mkdir -p ${OUTPUT_DIR}/testing_review/supporting_data
```

**Save files as follows**:

- Main report → `review/testing_review/testing_review_report.md`

- Findings data → `review/testing_review/testing_review_findings.json`

- Analysis scripts → `review/testing_review/analysis_scripts/`

- Supporting data → `review/testing_review/supporting_data/`
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
