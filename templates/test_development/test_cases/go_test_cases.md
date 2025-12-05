---
template_id: go_test_cases
template_name: Test Cases Development - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: test_development
phase: test_cases
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-8
prerequisites:

  - test_development/unit_tests/go_unit_tests.md
related_templates:

  - test_development/mocks_fixtures/go_mocks_fixtures.md
tools:

  - go test (1.23+)

  - testify
tags:

  - test-development

  - testing

  - go
---
# Go Test Case Development

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                 ► │ ● CURRENT
│ Phase 4: Mocks & Fixtures                          ► │ [NEXT]
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 2 (Unit Tests) should be completed first
**Next Step:** Phase 4 (Mocks & Fixtures)

---


## Objective
Develop comprehensive, well-structured test cases that validate functionality, cover edge cases, handle error conditions, and provide clear documentation of expected behavior using Go's testing package and table-driven test patterns.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/test_cases/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/test_cases/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Test Coverage

- [ ] Happy path scenarios tested

- [ ] Edge cases and boundaries covered

- [ ] Error conditions validated

- [ ] Input validation tested

- [ ] State transitions verified

- [ ] Regression tests added for bugs

- [ ] Concurrent operations tested

### Test Quality

- [ ] Tests follow table-driven test pattern where appropriate

- [ ] Test names clearly describe what is tested

- [ ] Tests are isolated and independent

- [ ] Tests execute quickly (<1s for unit tests)

- [ ] Assertions are specific and meaningful

- [ ] No test interdependencies

- [ ] Proper use of t.Helper() for test helpers

### Test Organization

- [ ] Tests grouped logically by feature/package

- [ ] Related tests organized using subtests

- [ ] Table-driven tests used for multiple scenarios

- [ ] Setup and teardown properly implemented

- [ ] Test documentation provided

- [ ] Benchmarks included for performance-critical code

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Test Case Development

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/test_cases"
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

Please develop comprehensive test cases for this Go code following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Test Case Planning

1. **Analyze Code to Test**

   - Identify all exported functions and methods

   - Document expected behavior

   - List input parameters and types

   - Define expected outputs

   - Note side effects (database, files, network calls)

   - Identify errors that should be returned

2. **Identify Test Scenarios**

   **Happy Path**:

   - Normal operation with valid inputs

   - Expected use cases

   - Successful execution flows

   - Valid state transitions

   **Edge Cases**:

   - Boundary values (0, -1, math.MaxInt, math.MinInt)

   - Empty slices, maps, and strings

   - Nil pointers and interfaces

   - Large data sets

   - Special characters in strings

   - Concurrent access scenarios

   **Error Conditions**:

   - Invalid inputs

   - Missing required parameters

   - Type assertion failures

   - Context cancellation

   - Timeout scenarios

   - External dependency failures

3. **Create Test Case Matrix**

   | Scenario | Input | Expected Output | Test Type | Priority |
   |----------|-------|-----------------|-----------|----------|
   | [description] | [values] | [result] | [unit/integration] | [high/med/low] |

## Phase 2: Unit Test Implementation

### Table-Driven Test Pattern

Follow Go's idiomatic table-driven test pattern:

```go
package user

import (
    "errors"
    "testing"
)

// TestCreateUser tests user creation with various inputs.
func TestCreateUser(t *testing.T) {
    tests := []struct {
        name    string
        input   User
        want    int
        wantErr bool
        errMsg  string
    }{
        {
            name: "valid user",
            input: User{
                Name:  "Alice",
                Email: "alice@example.com",
                Age:   30,
            },
            want:    123,
            wantErr: false,
        },
        {
            name: "invalid email",
            input: User{
                Name:  "Bob",
                Email: "not-an-email",
                Age:   25,
            },
            want:    0,
            wantErr: true,
            errMsg:  "invalid email format",
        },
        {
            name: "empty name",
            input: User{
                Name:  "",
                Email: "charlie@example.com",
                Age:   20,
            },
            want:    0,
            wantErr: true,
            errMsg:  "name cannot be empty",
        },
        {
            name: "negative age",
            input: User{
                Name:  "Dave",
                Email: "dave@example.com",
                Age:   -5,
            },
            want:    0,
            wantErr: true,
            errMsg:  "age must be positive",
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Arrange
            service := NewUserService()

            // Act
            got, err := service.CreateUser(tt.input)

            // Assert
            if (err != nil) != tt.wantErr {
                t.Errorf("CreateUser() error = %v, wantErr %v", err, tt.wantErr)
                return
            }

            if tt.wantErr && err != nil {
                if err.Error() != tt.errMsg {
                    t.Errorf("CreateUser() error message = %v, want %v", err.Error(), tt.errMsg)
                }
                return
            }

            if got != tt.want {
                t.Errorf("CreateUser() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

### Test Naming Conventions

Use descriptive names that explain what is tested:

**Pattern**: `Test<FunctionName>_<Condition>_<ExpectedResult>` or use table-driven tests with descriptive test case names

**Examples**:
```go
// Good test names
func TestAddUser_ValidData_ReturnsUserID(t *testing.T) {}

func TestAddUser_DuplicateEmail_ReturnsError(t *testing.T) {}

func TestGetUser_NonexistentID_ReturnsNil(t *testing.T) {}

func TestUpdateUser_InvalidAge_ReturnsError(t *testing.T) {}

// Table-driven test with descriptive case names
tests := []struct {
    name string
    // ...
}{
    {name: "valid input returns success"},
    {name: "empty string returns error"},
    {name: "nil pointer returns error"},
}

// Poor test names (avoid these)
func TestAddUser(t *testing.T) {}        // Too generic
func Test1(t *testing.T) {}              // Non-descriptive
func TestError(t *testing.T) {}          // Unclear what error
func TestEdgeCase(t *testing.T) {}       // Vague
```

### Testing Different Scenarios

**1. Testing Return Values**:
```go
func TestCalculateTotal(t *testing.T) {
    tests := []struct {
        name  string
        items []float64
        want  float64
    }{
        {
            name:  "sum of positive numbers",
            items: []float64{10.0, 20.0, 30.0},
            want:  60.0,
        },
        {
            name:  "empty slice",
            items: []float64{},
            want:  0.0,
        },
        {
            name:  "negative values",
            items: []float64{10.0, -5.0, 15.0},
            want:  20.0,
        },
        {
            name:  "single value",
            items: []float64{42.5},
            want:  42.5,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := CalculateTotal(tt.items)
            if got != tt.want {
                t.Errorf("CalculateTotal() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

**2. Testing Errors**:
```go
func TestDivide(t *testing.T) {
    tests := []struct {
        name    string
        a, b    int
        want    int
        wantErr bool
    }{
        {
            name:    "valid division",
            a:       10,
            b:       2,
            want:    5,
            wantErr: false,
        },
        {
            name:    "division by zero",
            a:       10,
            b:       0,
            want:    0,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Divide(tt.a, tt.b)
            if (err != nil) != tt.wantErr {
                t.Errorf("Divide() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !tt.wantErr && got != tt.want {
                t.Errorf("Divide() = %v, want %v", got, tt.want)
            }
        })
    }
}

func TestParseDate_InvalidFormat_ReturnsError(t *testing.T) {
    _, err := ParseDate("not-a-date")
    if err == nil {
        t.Error("ParseDate() expected error, got nil")
    }

    expectedMsg := "invalid date format"
    if err.Error() != expectedMsg {
        t.Errorf("ParseDate() error = %q, want %q", err.Error(), expectedMsg)
    }
}
```

**3. Testing with Mocks/Interfaces**:
```go
// Define mock
type mockRepository struct {
    saveFunc func(User) (int, error)
}

func (m *mockRepository) Save(u User) (int, error) {
    if m.saveFunc != nil {
        return m.saveFunc(u)
    }
    return 0, nil
}

func TestUserService_CreateUser(t *testing.T) {
    tests := []struct {
        name     string
        user     User
        mockSave func(User) (int, error)
        want     int
        wantErr  bool
    }{
        {
            name: "successful creation",
            user: User{Name: "Alice", Email: "alice@example.com"},
            mockSave: func(u User) (int, error) {
                return 123, nil
            },
            want:    123,
            wantErr: false,
        },
        {
            name: "repository error",
            user: User{Name: "Bob", Email: "bob@example.com"},
            mockSave: func(u User) (int, error) {
                return 0, errors.New("database error")
            },
            want:    0,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Arrange
            mockRepo := &mockRepository{saveFunc: tt.mockSave}
            service := NewUserService(mockRepo)

            // Act
            got, err := service.CreateUser(tt.user)

            // Assert
            if (err != nil) != tt.wantErr {
                t.Errorf("CreateUser() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if got != tt.want {
                t.Errorf("CreateUser() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

**4. Testing State Changes**:
```go
func TestUser_Login(t *testing.T) {
    // Arrange
    user := &User{
        Username: "alice",
        Password: "hashed_password",
        Status:   StatusInactive,
    }

    // Act
    err := user.Login("correct_password")

    // Assert
    if err != nil {
        t.Errorf("Login() unexpected error: %v", err)
    }
    if user.Status != StatusActive {
        t.Errorf("Status = %v, want %v", user.Status, StatusActive)
    }
    if user.LastLogin.IsZero() {
        t.Error("LastLogin should be set")
    }
}

func TestOrder_Cancel_RestoresInventory(t *testing.T) {
    // Arrange
    inventory := NewInventory()
    inventory.AddStock(1, 100)

    order := &Order{}
    order.AddItem(OrderItem{ProductID: 1, Quantity: 5})
    inventory.ReserveStock(1, 5)

    initialStock := inventory.GetAvailableStock(1)

    // Act
    order.Cancel()
    inventory.ReleaseReservation(1, 5)

    // Assert
    finalStock := inventory.GetAvailableStock(1)
    if finalStock != 100 {
        t.Errorf("Stock after cancel = %d, want %d", finalStock, 100)
    }
}
```

**5. Testing Concurrent Operations**:
```go
func TestCounter_Concurrent_Increments(t *testing.T) {
    counter := NewCounter()
    iterations := 1000
    goroutines := 10

    // Use WaitGroup to coordinate goroutines
    var wg sync.WaitGroup
    wg.Add(goroutines)

    for i := 0; i < goroutines; i++ {
        go func() {
            defer wg.Done()
            for j := 0; j < iterations; j++ {
                counter.Increment()
            }
        }()
    }

    wg.Wait()

    want := goroutines * iterations
    got := counter.Value()
    if got != want {
        t.Errorf("Counter.Value() = %d, want %d", got, want)
    }
}
```

### Testing Edge Cases and Boundaries

```go
func TestProcessValue_BoundaryConditions(t *testing.T) {
    tests := []struct {
        name    string
        input   int
        want    int
        wantErr bool
    }{
        {
            name:    "minimum valid value",
            input:   0,
            want:    0,
            wantErr: false,
        },
        {
            name:    "maximum valid value",
            input:   100,
            want:    100,
            wantErr: false,
        },
        {
            name:    "below minimum",
            input:   -1,
            want:    0,
            wantErr: true,
        },
        {
            name:    "above maximum",
            input:   101,
            want:    0,
            wantErr: true,
        },
        {
            name:    "max int value",
            input:   math.MaxInt,
            want:    0,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ProcessValue(tt.input)
            if (err != nil) != tt.wantErr {
                t.Errorf("ProcessValue() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if !tt.wantErr && got != tt.want {
                t.Errorf("ProcessValue() = %v, want %v", got, tt.want)
            }
        })
    }
}

func TestProcessCollection_EdgeCases(t *testing.T) {
    tests := []struct {
        name  string
        input []int
        want  []int
    }{
        {
            name:  "empty slice",
            input: []int{},
            want:  []int{},
        },
        {
            name:  "nil slice",
            input: nil,
            want:  []int{},
        },
        {
            name:  "single element",
            input: []int{1},
            want:  []int{1},
        },
        {
            name:  "large slice",
            input: make([]int, 10000),
            want:  make([]int, 10000),
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got := ProcessCollection(tt.input)
            if len(got) != len(tt.want) {
                t.Errorf("ProcessCollection() length = %v, want %v", len(got), len(tt.want))
            }
        })
    }
}

func TestValidateEmail_InvalidFormats(t *testing.T) {
    invalidEmails := []struct {
        name  string
        email string
    }{
        {name: "empty string", email: ""},
        {name: "no @ symbol", email: "not-an-email"},
        {name: "missing local part", email: "@example.com"},
        {name: "missing domain", email: "user@"},
        {name: "space in email", email: "user @example.com"},
        {name: "multiple @ symbols", email: "user@@example.com"},
    }

    for _, tt := range invalidEmails {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateEmail(tt.email)
            if err == nil {
                t.Errorf("ValidateEmail(%q) expected error, got nil", tt.email)
            }
        })
    }
}
```

### Testing with Context

```go
func TestFetchUser_WithContext(t *testing.T) {
    tests := []struct {
        name    string
        setup   func() context.Context
        userID  int
        wantErr bool
    }{
        {
            name: "successful fetch",
            setup: func() context.Context {
                return context.Background()
            },
            userID:  1,
            wantErr: false,
        },
        {
            name: "context canceled",
            setup: func() context.Context {
                ctx, cancel := context.WithCancel(context.Background())
                cancel() // Cancel immediately
                return ctx
            },
            userID:  1,
            wantErr: true,
        },
        {
            name: "context timeout",
            setup: func() context.Context {
                ctx, cancel := context.WithTimeout(context.Background(), 1*time.Nanosecond)
                defer cancel()
                time.Sleep(2 * time.Nanosecond) // Force timeout
                return ctx
            },
            userID:  1,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            ctx := tt.setup()
            _, err := FetchUser(ctx, tt.userID)
            if (err != nil) != tt.wantErr {
                t.Errorf("FetchUser() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

### Helper Functions

```go
// createTestUser is a helper function for creating test users.
func createTestUser(t *testing.T, name, email string) *User {
    t.Helper() // Marks this as a helper function

    user := &User{
        Name:  name,
        Email: email,
        Age:   30,
    }
    return user
}

// assertEqual is a helper for asserting equality.
func assertEqual(t *testing.T, got, want interface{}) {
    t.Helper()

    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}

// assertError checks if an error occurred when expected.
func assertError(t *testing.T, err error, wantErr bool) {
    t.Helper()

    if (err != nil) != wantErr {
        t.Errorf("error = %v, wantErr %v", err, wantErr)
    }
}
```

## Phase 3: Integration Test Implementation

Integration tests verify multiple components working together:

```go
package integration

import (
    "database/sql"
    "testing"

    _ "github.com/mattn/go-sqlite3"
)

// TestUserRegistration_Integration tests the complete user registration workflow.
func TestUserRegistration_Integration(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping integration test")
    }

    // Setup test database
    db, err := sql.Open("sqlite3", ":memory:")
    if err != nil {
        t.Fatalf("Failed to open database: %v", err)
    }
    defer db.Close()

    // Initialize schema
    if err := setupSchema(db); err != nil {
        t.Fatalf("Failed to setup schema: %v", err)
    }

    // Create services
    userRepo := NewUserRepository(db)
    emailService := &testEmailService{sent: make([]Email, 0)}
    userService := NewUserService(userRepo, emailService)

    tests := []struct {
        name           string
        username       string
        email          string
        wantErr        bool
        checkDB        bool
        checkEmail     bool
    }{
        {
            name:       "successful registration",
            username:   "alice",
            email:      "alice@example.com",
            wantErr:    false,
            checkDB:    true,
            checkEmail: true,
        },
        {
            name:     "duplicate username",
            username: "alice",
            email:    "different@example.com",
            wantErr:  true,
            checkDB:  false,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Act
            userID, err := userService.RegisterUser(tt.username, tt.email)

            // Assert
            if (err != nil) != tt.wantErr {
                t.Errorf("RegisterUser() error = %v, wantErr %v", err, tt.wantErr)
                return
            }

            if tt.checkDB {
                // Verify database entry
                user, err := userRepo.GetByID(userID)
                if err != nil {
                    t.Errorf("Failed to retrieve user: %v", err)
                }
                if user.Username != tt.username {
                    t.Errorf("Username = %v, want %v", user.Username, tt.username)
                }
            }

            if tt.checkEmail {
                // Verify email was sent
                if len(emailService.sent) == 0 {
                    t.Error("No email was sent")
                }
            }
        })
    }
}
```

### HTTP API Integration Tests

```go
func TestUserAPI_Integration(t *testing.T) {
    // Setup test server
    server := setupTestServer(t)
    defer server.Close()

    tests := []struct {
        name       string
        method     string
        path       string
        body       string
        wantStatus int
        wantBody   string
    }{
        {
            name:       "create user",
            method:     "POST",
            path:       "/api/users",
            body:       `{"username":"testuser","email":"test@example.com"}`,
            wantStatus: http.StatusCreated,
            wantBody:   `"username":"testuser"`,
        },
        {
            name:       "get user",
            method:     "GET",
            path:       "/api/users/1",
            body:       "",
            wantStatus: http.StatusOK,
            wantBody:   `"id":1`,
        },
        {
            name:       "invalid request",
            method:     "POST",
            path:       "/api/users",
            body:       `{"invalid":"data"}`,
            wantStatus: http.StatusBadRequest,
            wantBody:   `"error"`,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Create request
            var body io.Reader
            if tt.body != "" {
                body = strings.NewReader(tt.body)
            }
            req, err := http.NewRequest(tt.method, server.URL+tt.path, body)
            if err != nil {
                t.Fatalf("Failed to create request: %v", err)
            }

            // Execute request
            resp, err := http.DefaultClient.Do(req)
            if err != nil {
                t.Fatalf("Request failed: %v", err)
            }
            defer resp.Body.Close()

            // Assert status code
            if resp.StatusCode != tt.wantStatus {
                t.Errorf("Status = %d, want %d", resp.StatusCode, tt.wantStatus)
            }

            // Assert body contains expected content
            bodyBytes, _ := io.ReadAll(resp.Body)
            if !strings.Contains(string(bodyBytes), tt.wantBody) {
                t.Errorf("Body does not contain %q, got %q", tt.wantBody, string(bodyBytes))
            }
        })
    }
}
```

## Phase 4: Benchmarking

Add benchmarks for performance-critical code:

```go
func BenchmarkCalculateTotal(b *testing.B) {
    items := make([]float64, 1000)
    for i := range items {
        items[i] = float64(i)
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        CalculateTotal(items)
    }
}

func BenchmarkUserService_CreateUser(b *testing.B) {
    service := NewUserService()
    user := User{
        Name:  "BenchUser",
        Email: "bench@example.com",
        Age:   30,
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        service.CreateUser(user)
    }
}

// Table-driven benchmark
func BenchmarkProcessCollection(b *testing.B) {
    sizes := []int{10, 100, 1000, 10000}

    for _, size := range sizes {
        b.Run(fmt.Sprintf("size_%d", size), func(b *testing.B) {
            input := make([]int, size)
            b.ResetTimer()
            for i := 0; i < b.N; i++ {
                ProcessCollection(input)
            }
        })
    }
}
```

## Phase 5: Test Best Practices

### 1. Test Independence

```go
// GOOD - Tests are independent
func TestUserService_CreateUser(t *testing.T) {
    t.Run("creates user successfully", func(t *testing.T) {
        service := NewUserService() // Fresh instance
        user, err := service.CreateUser("alice", "alice@example.com")
        if err != nil {
            t.Errorf("unexpected error: %v", err)
        }
        if user.ID == 0 {
            t.Error("expected non-zero ID")
        }
    })

    t.Run("returns error for duplicate", func(t *testing.T) {
        service := NewUserService() // Fresh instance
        service.CreateUser("bob", "bob@example.com")
        _, err := service.CreateUser("bob", "bob2@example.com")
        if err == nil {
            t.Error("expected error for duplicate username")
        }
    })
}

// BAD - Tests depend on each other
func TestUserService_Sequence(t *testing.T) {
    service := NewUserService() // Shared instance
    var userID int

    t.Run("create", func(t *testing.T) {
        user, _ := service.CreateUser("alice", "alice@example.com")
        userID = user.ID // Sharing state
    })

    t.Run("delete", func(t *testing.T) {
        err := service.DeleteUser(userID) // Depends on previous test
        if err != nil {
            t.Error("failed to delete")
        }
    })
}
```

### 2. Clear Assertions

```go
// GOOD - Specific, clear assertions
func TestCreateUser_ValidData_ReturnsUser(t *testing.T) {
    user, err := CreateUser("alice", "alice@example.com", 30)

    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if user.Username != "alice" {
        t.Errorf("Username = %q, want %q", user.Username, "alice")
    }
    if user.Email != "alice@example.com" {
        t.Errorf("Email = %q, want %q", user.Email, "alice@example.com")
    }
    if user.Age != 30 {
        t.Errorf("Age = %d, want %d", user.Age, 30)
    }
    if user.CreatedAt.IsZero() {
        t.Error("CreatedAt should be set")
    }
}

// BAD - Vague or missing assertions
func TestCreateUser(t *testing.T) {
    user, err := CreateUser("alice", "alice@example.com", 30)
    if user == nil {
        t.Error("user is nil") // Too vague
    }
    if user.Username == "" {
        t.Error("username is empty") // Checks existence, not value
    }
}
```

### 3. Using testdata Directory

```go
// Place test fixtures in testdata directory
func TestLoadConfig(t *testing.T) {
    config, err := LoadConfig("testdata/valid_config.json")
    if err != nil {
        t.Fatalf("LoadConfig() error = %v", err)
    }

    if config.Port != 8080 {
        t.Errorf("Port = %d, want 8080", config.Port)
    }
}
```

## Output Format

Please provide comprehensive test cases with the following structure:

### Test Coverage Summary

- **Total Test Cases**: [count]

- **Unit Tests**: [count]

- **Integration Tests**: [count]

- **Benchmarks**: [count]

- **Test Types**:

  - Happy path: [count]

  - Edge cases: [count]

  - Error conditions: [count]

  - Concurrent operations: [count]

### Test Case Implementation

For each package/function:

**Package**: `[package_name]`
**Test File**: `[package_name]_test.go`

**Test Cases**:

1. `TestFunctionName_Condition_ExpectedResult`

   - **Scenario**: [description]

   - **Input**: [test data]

   - **Expected**: [result]

   - **Type**: [unit/integration/benchmark]

2. `TestFunctionName_InvalidInput_ReturnsError`

   - **Scenario**: [description]

   - **Input**: [test data]

   - **Expected**: [error]

   - **Type**: [unit/integration]

### Test Execution Results
```bash
# Run tests
go test ./...

# Run with coverage
go test -cover ./...

# Run benchmarks
go test -bench=. ./...

# Expected output
PASS
coverage: 85.2% of statements
ok      myapp/user    0.123s
```

### Coverage Gaps Identified

- [ ] [Function]: Missing tests for [scenario]

- [ ] [Function]: Need edge case tests for [condition]

- [ ] [Function]: Error handling not tested

- [ ] [Function]: Concurrent access not tested

### Test Quality Metrics

- **Average test execution time**: [milliseconds]

- **Table-driven tests**: [count]

- **Tests with clear names**: [percentage]

- **Independent tests**: [percentage]

### Next Steps

- [ ] Implement remaining test cases for coverage gaps

- [ ] Add benchmarks for performance-critical functions

- [ ] Set up integration tests with test containers

- [ ] Configure CI/CD pipeline

- [ ] Review and refactor slow tests

- [ ] Add race detector tests (-race flag)

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

1. **Test case matrix** documenting all scenarios

2. **Complete test implementations** with table-driven pattern

3. **Integration tests** for workflows

4. **Benchmarks** for performance-critical code

5. **Test coverage report** showing gaps

6. **Execution instructions** for running tests

7. **Quality metrics** and improvement suggestions
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
