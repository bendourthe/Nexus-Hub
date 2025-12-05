---
template_id: go_unit_tests
template_name: Unit Tests - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: test_development
phase: unit_tests
phase_number: 2
difficulty: intermediate
estimated_time_hours: 3-6
prerequisites:

  - test_development/test_structure/go_test_structure.md
related_templates:

  - test_development/test_cases/go_test_cases.md
tools:

  - go test (1.23+)
  - testify
tags:

  - test-development
  - testing
  - go
---
# Go Unit Tests - Comprehensive Implementation Guide

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                             ► │ ● CURRENT
│ Phase 3: Test Cases Development                    ► │ [NEXT]
│ Phase 4: Mocks & Fixtures                                ► │ 
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 1 (Test Structure Setup) should be completed first
**Next Step:** Phase 3 (Test Cases Development)

---


## Objective

Develop comprehensive unit testing strategy for Go applications using the built-in testing package, focusing on test isolation, fast execution, table-driven tests, and thorough coverage following Go idioms and FIRST principles.

---

## Output Directory Structure

```
${OUTPUT_DIR}/
├── templates/           # Reusable test templates
├── assets/             # Diagrams and visualizations
└── exports/            # Final documentation
```

---

## Implementation Checklist

### Test Foundation
- [ ] testing package overview
- [ ] Test file structure (_test.go)
- [ ] Table-driven test patterns
- [ ] Benchmark tests
- [ ] Example tests

### Test Patterns
- [ ] Function tests
- [ ] Method tests (receivers)
- [ ] Interface tests
- [ ] Goroutine tests
- [ ] Error handling tests

### Test Quality
- [ ] Test independence verified
- [ ] Subtests with t.Run()
- [ ] Mock patterns documented
- [ ] Coverage analysis

---

## Prompt Template

~~~markdown
# Go Unit Testing Implementation - Comprehensive Guide

## Context
Generate comprehensive guidance for implementing unit tests in Go using the built-in testing package with detailed examples following Go idioms.

## CRITICAL: Output Directory Setup

```bash
mkdir -p ${OUTPUT_DIR}/templates ${OUTPUT_DIR}/assets ${OUTPUT_DIR}/exports
```

---

## Phase 1: Go Testing Fundamentals

### 1.1 FIRST Principles in Go

**Fast** - Tests execute in milliseconds
- Use `go test -short` for quick tests
- Avoid I/O in unit tests
- Use mocks for external dependencies

**Independent** - No shared state
- Each test function is independent
- Use setup/teardown within test functions
- Avoid package-level variables

**Repeatable** - Deterministic results
- Mock time-dependent code
- Control randomness with fixed seeds
- Isolate from environment

**Self-validating** - Clear pass/fail
- Use descriptive error messages
- Use testing.T methods effectively

**Timely** - Written with code
- Follow TDD practices
- Maintain coverage >80%

**Arrange-Act-Assert Pattern:**
```go
func TestCalculateDiscount(t *testing.T) {
    // Arrange
    price := 100.0
    discountRate := 0.20
    calculator := NewPriceCalculator()

    // Act
    result := calculator.CalculateDiscount(price, discountRate)

    // Assert
    expected := 80.0
    if result != expected {
        t.Errorf("CalculateDiscount(%v, %v) = %v; want %v", price, discountRate, result, expected)
    }
}
```

### 1.2 Go Testing Conventions

**File Naming:**
- Test files: `<file>_test.go`
- Examples: `calculator_test.go`, `user_test.go`

**Function Naming:**
- `Test<Name>(t *testing.T)` - Unit tests
- `Benchmark<Name>(b *testing.B)` - Benchmarks
- `Example<Name>()` - Example functions

**Package:**
```go
// Same package (white-box testing)
package calculator

// Different package (black-box testing)
package calculator_test
```

---

## Phase 2: Test Organization

### 2.1 Project Structure

```
myproject/
├── calculator.go
├── calculator_test.go
├── user.go
├── user_test.go
└── services/
    ├── payment.go
    └── payment_test.go
```

### 2.2 Table-Driven Tests

**Pattern:**
```go
func TestCalculateDiscount(t *testing.T) {
    tests := []struct {
        name         string
        price        float64
        discountRate float64
        want         float64
        wantErr      bool
    }{
        {
            name:         "no discount",
            price:        100.0,
            discountRate: 0.0,
            want:         100.0,
            wantErr:      false,
        },
        {
            name:         "full discount",
            price:        100.0,
            discountRate: 1.0,
            want:         0.0,
            wantErr:      false,
        },
        {
            name:         "20% discount",
            price:        100.0,
            discountRate: 0.20,
            want:         80.0,
            wantErr:      false,
        },
        {
            name:         "negative price",
            price:        -100.0,
            discountRate: 0.20,
            want:         0.0,
            wantErr:      true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := CalculateDiscount(tt.price, tt.discountRate)
            if (err != nil) != tt.wantErr {
                t.Errorf("CalculateDiscount() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if got != tt.want {
                t.Errorf("CalculateDiscount() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

---

## Phase 3: Testing Different Components

### 3.1 Testing Functions

**Example:**
```go
package calculator

import "errors"

func CalculateDiscount(price, discountRate float64) (float64, error) {
    if price < 0 {
        return 0, errors.New("price cannot be negative")
    }
    if discountRate < 0 || discountRate > 1 {
        return 0, errors.New("discount rate must be between 0 and 1")
    }
    return price * (1 - discountRate), nil
}
```

**Comprehensive Tests:**
```go
package calculator_test

import (
    "testing"
    "myproject/calculator"
)

func TestCalculateDiscount(t *testing.T) {
    t.Run("valid inputs", func(t *testing.T) {
        tests := []struct {
            price    float64
            discount float64
            want     float64
        }{
            {100.0, 0.0, 100.0},
            {100.0, 1.0, 0.0},
            {100.0, 0.20, 80.0},
            {50.0, 0.10, 45.0},
        }

        for _, tt := range tests {
            got, err := calculator.CalculateDiscount(tt.price, tt.discount)
            if err != nil {
                t.Errorf("unexpected error: %v", err)
            }
            if got != tt.want {
                t.Errorf("CalculateDiscount(%v, %v) = %v; want %v",
                    tt.price, tt.discount, got, tt.want)
            }
        }
    })

    t.Run("invalid inputs", func(t *testing.T) {
        tests := []struct {
            name     string
            price    float64
            discount float64
        }{
            {"negative price", -100.0, 0.20},
            {"discount below zero", 100.0, -0.10},
            {"discount above one", 100.0, 1.5},
        }

        for _, tt := range tests {
            t.Run(tt.name, func(t *testing.T) {
                _, err := calculator.CalculateDiscount(tt.price, tt.discount)
                if err == nil {
                    t.Error("expected error, got nil")
                }
            })
        }
    })
}
```

### 3.2 Testing Structs and Methods

**Example:**
```go
package user

import (
    "errors"
    "time"
)

type User struct {
    Name      string
    Email     string
    Age       *int
    CreatedAt time.Time
    Active    bool
}

func NewUser(name, email string, age *int) (*User, error) {
    if name == "" {
        return nil, errors.New("name cannot be empty")
    }
    if email == "" || !contains(email, "@") {
        return nil, errors.New("invalid email format")
    }
    if age != nil && *age < 0 {
        return nil, errors.New("age cannot be negative")
    }

    return &User{
        Name:      name,
        Email:     email,
        Age:       age,
        CreatedAt: time.Now(),
        Active:    true,
    }, nil
}

func (u *User) Deactivate() {
    u.Active = false
}

func (u *User) Activate() {
    u.Active = true
}

func contains(s, substr string) bool {
    return len(s) > 0 && len(substr) > 0 && s != "" && substr != ""
}
```

**Tests:**
```go
package user_test

import (
    "testing"
    "myproject/user"
)

func TestNewUser(t *testing.T) {
    t.Run("valid inputs", func(t *testing.T) {
        age := 30
        u, err := user.NewUser("John Doe", "john@example.com", &age)

        if err != nil {
            t.Fatalf("unexpected error: %v", err)
        }
        if u.Name != "John Doe" {
            t.Errorf("Name = %v; want John Doe", u.Name)
        }
        if u.Email != "john@example.com" {
            t.Errorf("Email = %v; want john@example.com", u.Email)
        }
        if u.Age == nil || *u.Age != 30 {
            t.Errorf("Age = %v; want 30", u.Age)
        }
        if !u.Active {
            t.Error("Active should be true for new user")
        }
    })

    t.Run("without age", func(t *testing.T) {
        u, err := user.NewUser("Jane", "jane@example.com", nil)

        if err != nil {
            t.Fatalf("unexpected error: %v", err)
        }
        if u.Age != nil {
            t.Errorf("Age should be nil, got %v", u.Age)
        }
    })

    t.Run("invalid inputs", func(t *testing.T) {
        tests := []struct {
            name  string
            uname string
            email string
            age   *int
        }{
            {"empty name", "", "test@example.com", nil},
            {"empty email", "John", "", nil},
            {"invalid email", "John", "invalid", nil},
            {"negative age", "John", "john@example.com", intPtr(-5)},
        }

        for _, tt := range tests {
            t.Run(tt.name, func(t *testing.T) {
                _, err := user.NewUser(tt.uname, tt.email, tt.age)
                if err == nil {
                    t.Error("expected error, got nil")
                }
            })
        }
    })
}

func TestUser_ActivationMethods(t *testing.T) {
    u, _ := user.NewUser("John", "john@example.com", nil)

    t.Run("deactivate", func(t *testing.T) {
        u.Deactivate()
        if u.Active {
            t.Error("user should be inactive after Deactivate()")
        }
    })

    t.Run("activate", func(t *testing.T) {
        u.Activate()
        if !u.Active {
            t.Error("user should be active after Activate()")
        }
    })
}

func intPtr(i int) *int {
    return &i
}
```

### 3.3 Testing Interfaces

**Example:**
```go
package processor

type DataProcessor interface {
    Process(data []int) []int
    Name() string
}

type DoublingProcessor struct{}

func (d *DoublingProcessor) Process(data []int) []int {
    result := make([]int, len(data))
    for i, v := range data {
        result[i] = v * 2
    }
    return result
}

func (d *DoublingProcessor) Name() string {
    return "Doubling Processor"
}
```

**Tests:**
```go
func TestDoublingProcessor_Process(t *testing.T) {
    processor := &processor.DoublingProcessor{}

    tests := []struct {
        name  string
        input []int
        want  []int
    }{
        {"doubles each element", []int{1, 2, 3}, []int{2, 4, 6}},
        {"handles empty slice", []int{}, []int{}},
        {"handles single element", []int{5}, []int{10}},
        {"handles negative numbers", []int{-1, -2}, []int{-2, -4}},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := processor.Process(tt.input)
            if !equal(got, tt.want) {
                t.Errorf("Process(%v) = %v; want %v", tt.input, got, tt.want)
            }
        })
    }
}

func TestDoublingProcessor_ImplementsInterface(t *testing.T) {
    var _ processor.DataProcessor = &processor.DoublingProcessor{}
}

func equal(a, b []int) bool {
    if len(a) != len(b) {
        return false
    }
    for i := range a {
        if a[i] != b[i] {
            return false
        }
    }
    return true
}
```

### 3.4 Testing Goroutines

**Example:**
```go
package concurrent

import "sync"

func ProcessConcurrently(data []int) []int {
    result := make([]int, len(data))
    var wg sync.WaitGroup

    for i, v := range data {
        wg.Add(1)
        go func(index, value int) {
            defer wg.Done()
            result[index] = value * 2
        }(i, v)
    }

    wg.Wait()
    return result
}

func SendToChannel(values []int) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch)
        for _, v := range values {
            ch <- v
        }
    }()
    return ch
}
```

**Tests:**
```go
func TestProcessConcurrently(t *testing.T) {
    input := []int{1, 2, 3, 4, 5}
    expected := []int{2, 4, 6, 8, 10}

    result := concurrent.ProcessConcurrently(input)

    if !equal(result, expected) {
        t.Errorf("ProcessConcurrently(%v) = %v; want %v", input, result, expected)
    }
}

func TestSendToChannel(t *testing.T) {
    values := []int{1, 2, 3}
    ch := concurrent.SendToChannel(values)

    var received []int
    for v := range ch {
        received = append(received, v)
    }

    if !equal(received, values) {
        t.Errorf("received %v; want %v", received, values)
    }
}

func TestConcurrentAccess(t *testing.T) {
    counter := 0
    var mu sync.Mutex
    var wg sync.WaitGroup

    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            mu.Lock()
            counter++
            mu.Unlock()
        }()
    }

    wg.Wait()

    if counter != 100 {
        t.Errorf("counter = %d; want 100", counter)
    }
}
```

### 3.5 Testing Errors

**Example:**
```go
package validation

import (
    "errors"
    "fmt"
)

var (
    ErrNegativeValue = errors.New("value cannot be negative")
    ErrOutOfRange    = errors.New("value out of range")
)

type ValidationError struct {
    Field string
    Value interface{}
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for field %s with value %v", e.Field, e.Value)
}

func ValidateAge(age int) error {
    if age < 0 {
        return ErrNegativeValue
    }
    if age > 150 {
        return ErrOutOfRange
    }
    return nil
}

func ValidateUser(name string, age int) error {
    if name == "" {
        return &ValidationError{Field: "name", Value: name}
    }
    return ValidateAge(age)
}
```

**Tests:**
```go
func TestValidateAge(t *testing.T) {
    tests := []struct {
        name    string
        age     int
        wantErr error
    }{
        {"valid age", 25, nil},
        {"zero age", 0, nil},
        {"negative age", -1, validation.ErrNegativeValue},
        {"age over 150", 151, validation.ErrOutOfRange},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := validation.ValidateAge(tt.age)
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("ValidateAge(%d) error = %v; want %v", tt.age, err, tt.wantErr)
            }
        })
    }
}

func TestValidateUser(t *testing.T) {
    t.Run("empty name returns ValidationError", func(t *testing.T) {
        err := validation.ValidateUser("", 25)
        if err == nil {
            t.Fatal("expected error, got nil")
        }

        var validationErr *validation.ValidationError
        if !errors.As(err, &validationErr) {
            t.Errorf("expected *ValidationError, got %T", err)
        }
        if validationErr.Field != "name" {
            t.Errorf("expected field 'name', got %s", validationErr.Field)
        }
    })

    t.Run("invalid age returns age error", func(t *testing.T) {
        err := validation.ValidateUser("John", -5)
        if !errors.Is(err, validation.ErrNegativeValue) {
            t.Errorf("expected ErrNegativeValue, got %v", err)
        }
    })
}
```

---

## Phase 4: Advanced Testing

### 4.1 Benchmarks

```go
func BenchmarkCalculateDiscount(b *testing.B) {
    for i := 0; i < b.N; i++ {
        calculator.CalculateDiscount(100.0, 0.20)
    }
}

func BenchmarkProcessConcurrently(b *testing.B) {
    data := make([]int, 1000)
    for i := range data {
        data[i] = i
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ProcessConcurrently(data)
    }
}
```

**Run benchmarks:**
```bash
go test -bench=.
go test -bench=. -benchmem
go test -bench=BenchmarkCalculate
```

### 4.2 Examples

```go
func ExampleCalculateDiscount() {
    result, _ := calculator.CalculateDiscount(100.0, 0.20)
    fmt.Printf("%.2f\n", result)
    // Output: 80.00
}

func ExampleUser_Deactivate() {
    u, _ := user.NewUser("John", "john@example.com", nil)
    u.Deactivate()
    fmt.Println(u.Active)
    // Output: false
}
```

### 4.3 Test Helpers

```go
func TestMain(m *testing.M) {
    // Setup
    setup()

    // Run tests
    code := m.Run()

    // Teardown
    teardown()

    os.Exit(code)
}

func setup() {
    // Initialize test environment
}

func teardown() {
    // Clean up
}
```

### 4.4 Coverage

```bash
# Run tests with coverage
go test -cover

# Generate coverage profile
go test -coverprofile=coverage.out

# View coverage in browser
go tool cover -html=coverage.out

# Show coverage per function
go tool cover -func=coverage.out
```

---

## Phase 5: Test Quality

### 5.1 Test Flags

```bash
# Run short tests only
go test -short

# Verbose output
go test -v

# Run specific test
go test -run TestCalculate

# Run tests in specific package
go test ./calculator

# Run all tests recursively
go test ./...

# Parallel execution
go test -parallel 4

# Fail fast
go test -failfast

# Run with race detector
go test -race
```

### 5.2 Maintenance Checklist

- [ ] All tests pass independently
- [ ] Tests use table-driven patterns
- [ ] Subtests with t.Run()
- [ ] Fast execution
- [ ] No code duplication
- [ ] Clear error messages
- [ ] Edge cases covered
- [ ] >80% coverage

---

## Output Deliverables

### 1. Implementation Guide (20-30 pages)
`${OUTPUT_DIR}/exports/unit_test_implementation_guide.md`

### 2. Test Examples (50+ tests)
`${OUTPUT_DIR}/exports/unit_test_examples.md`

### 3. Templates
`${OUTPUT_DIR}/templates/`:

- `test_template.go`
- `table_test_template.go`
- `benchmark_template.go`
- `interface_test_template.go`

### 4. Guides
- Anti-patterns guide
- Quality checklist
- Coverage guide
- Benchmark guide

---

## Verification Checklist

- [ ] All deliverables created
- [ ] 20-30 page guide
- [ ] 50+ examples
- [ ] Table-driven patterns
- [ ] Interface testing
- [ ] Goroutine testing
- [ ] Benchmark examples
- [ ] Coverage analysis

---
~~~

End of prompt template.

---

## Additional Notes

- Run tests: `go test`
- With coverage: `go test -cover`
- Benchmarks: `go test -bench=.`
- Race detection: `go test -race`
- Verbose: `go test -v`

---

**Status:** Template ready. Copy the prompt into your AI assistant for comprehensive Go unit testing guidance.
