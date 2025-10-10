# Go Mocks & Fixtures

## Objective
Design and implement effective mocking strategies and fixture management using testify/mock and httptest to isolate components, manage test data efficiently, control external dependencies, and create maintainable, fast-running tests.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── mocks_fixtures/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:

- Create `tests/{phase}/` directory in repository root if it doesn't exist

- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:

- `test_files/` - Actual test implementation files

- `test_data/` - Test fixtures, mock data, sample inputs

- `test_reports/` - Test execution reports, coverage reports, performance results

- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Fixture Setup
- [ ] Setup/teardown functions configured appropriately
- [ ] Test data builders created for flexible data generation
- [ ] Fixture factories implemented with realistic data
- [ ] Cleanup and reset logic automated (defer statements)
- [ ] Fixtures documented with clear purposes

### Mocking Strategy
- [ ] External dependencies identified for mocking
- [ ] Interfaces defined for mockable components
- [ ] Mock implementations created with testify/mock
- [ ] Assertion methods used appropriately
- [ ] Over-mocking avoided

### Test Data Management
- [ ] Test data factories implemented
- [ ] Realistic test data patterns established
- [ ] Data builders for complex structs created
- [ ] Test data isolated per test
- [ ] Data cleanup automated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Mocks & Fixtures Implementation

Please implement comprehensive mocking and fixture strategies for this Go project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Fixture Architecture Design

### Understanding Go Testing Patterns

Go uses simple functions for fixtures and setup/teardown:

**Basic Setup/Teardown**:
```go
package users_test

import (
    "testing"
)

type testFixture struct {
    db      *Database
    service *UserService
}

func setupTest(t *testing.T) *testFixture {
    t.Helper()

    db := NewDatabase("test_db")
    service := NewUserService(db)

    return &testFixture{
        db:      db,
        service: service,
    }
}

func (f *testFixture) teardown() {
    f.db.ClearTestData()
    f.db.Close()
}

func TestUserCreation(t *testing.T) {
    f := setupTest(t)
    defer f.teardown()

    user := &User{
        Username: "testuser",
        Email:    "test@example.com",
    }

    result, err := f.service.CreateUser(user)
    if err != nil {
        t.Fatalf("failed to create user: %v", err)
    }

    if result.Username != "testuser" {
        t.Errorf("expected username 'testuser', got '%s'", result.Username)
    }
}
```

### Fixture Scopes

Choose appropriate scope for efficiency and isolation:

**1. Package-Level Setup (TestMain)**:
```go
package users_test

import (
    "os"
    "testing"
)

var testDB *Database

func TestMain(m *testing.M) {
    // Setup - runs once before all tests
    testDB = setupDatabase()

    // Run all tests
    code := m.Run()

    // Teardown - runs once after all tests
    teardownDatabase(testDB)

    os.Exit(code)
}

func setupDatabase() *Database {
    db, err := NewDatabase("test_db")
    if err != nil {
        panic(err)
    }
    db.Migrate()
    return db
}

func teardownDatabase(db *Database) {
    db.DropTables()
    db.Close()
}

func TestInsertUser(t *testing.T) {
    // Use shared testDB
    user := &User{Username: "alice"}
    err := testDB.Insert(user)
    if err != nil {
        t.Fatalf("insert failed: %v", err)
    }
}
```

**2. Test-Level Setup with defer**:
```go
func TestUserRepository(t *testing.T) {
    // Setup
    db := setupTestDB(t)
    defer db.Close()  // Cleanup

    repo := NewUserRepository(db)

    // Test
    user := &User{Username: "alice"}
    err := repo.Save(user)
    if err != nil {
        t.Fatalf("save failed: %v", err)
    }
}
```

**3. Subtests with Shared Setup**:
```go
func TestUserService(t *testing.T) {
    // Shared setup
    db := setupTestDB(t)
    defer db.Close()

    service := NewUserService(db)

    t.Run("CreateUser", func(t *testing.T) {
        user := &User{Username: "alice"}
        result, err := service.CreateUser(user)
        if err != nil {
            t.Fatalf("CreateUser failed: %v", err)
        }
        if result.Username != "alice" {
            t.Errorf("expected 'alice', got '%s'", result.Username)
        }
    })

    t.Run("GetUser", func(t *testing.T) {
        result, err := service.GetUser(1)
        if err != nil {
            t.Fatalf("GetUser failed: %v", err)
        }
        if result == nil {
            t.Error("expected user, got nil")
        }
    })
}
```

**4. Table-Driven Tests with Fixtures**:
```go
func TestUserValidation(t *testing.T) {
    tests := []struct {
        name    string
        user    *User
        wantErr bool
    }{
        {
            name:    "valid user",
            user:    &User{Username: "alice", Email: "alice@test.com"},
            wantErr: false,
        },
        {
            name:    "missing email",
            user:    &User{Username: "bob"},
            wantErr: true,
        },
        {
            name:    "invalid email",
            user:    &User{Username: "charlie", Email: "invalid"},
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := ValidateUser(tt.user)
            if (err != nil) != tt.wantErr {
                t.Errorf("ValidateUser() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

### Fixture Factories

Create factories for flexible test data generation:

```go
// testutil/factories.go
package testutil

import (
    "sync/atomic"
    "time"
)

type UserFactory struct {
    idCounter int64
}

func NewUserFactory() *UserFactory {
    return &UserFactory{}
}

func (f *UserFactory) Create(opts ...func(*User)) *User {
    id := atomic.AddInt64(&f.idCounter, 1)

    user := &User{
        ID:        id,
        Username:  fmt.Sprintf("user_%d", id),
        Email:     fmt.Sprintf("user%d@test.com", id),
        Age:       25,
        Active:    true,
        CreatedAt: time.Now(),
    }

    // Apply options
    for _, opt := range opts {
        opt(user)
    }

    return user
}

func (f *UserFactory) CreateBatch(count int, opts ...func(*User)) []*User {
    users := make([]*User, count)
    for i := 0; i < count; i++ {
        users[i] = f.Create(opts...)
    }
    return users
}

func (f *UserFactory) Reset() {
    atomic.StoreInt64(&f.idCounter, 0)
}

// Option functions for customization
func WithUsername(username string) func(*User) {
    return func(u *User) {
        u.Username = username
    }
}

func WithEmail(email string) func(*User) {
    return func(u *User) {
        u.Email = email
    }
}

func WithAge(age int) func(*User) {
    return func(u *User) {
        u.Age = age
    }
}

func WithInactive() func(*User) {
    return func(u *User) {
        u.Active = false
    }
}

// Usage in tests
func TestUserOperations(t *testing.T) {
    factory := NewUserFactory()

    t.Run("create with defaults", func(t *testing.T) {
        user1 := factory.Create()
        user2 := factory.Create()

        if user1.Username != "user_1" {
            t.Errorf("expected 'user_1', got '%s'", user1.Username)
        }
        if user2.Username != "user_2" {
            t.Errorf("expected 'user_2', got '%s'", user2.Username)
        }
    })

    t.Run("create with custom data", func(t *testing.T) {
        user := factory.Create(
            WithUsername("alice"),
            WithEmail("alice@example.com"),
            WithAge(30),
        )

        if user.Username != "alice" {
            t.Errorf("expected 'alice', got '%s'", user.Username)
        }
        if user.Age != 30 {
            t.Errorf("expected 30, got %d", user.Age)
        }
    })

    t.Run("create batch", func(t *testing.T) {
        users := factory.CreateBatch(5, WithInactive())

        if len(users) != 5 {
            t.Errorf("expected 5 users, got %d", len(users))
        }
        for _, u := range users {
            if u.Active {
                t.Error("expected inactive user")
            }
        }
    })
}
```

### Builder Pattern for Complex Structs

```go
// testutil/builders.go
package testutil

import "math/big"

type OrderBuilder struct {
    order Order
}

func NewOrderBuilder() *OrderBuilder {
    return &OrderBuilder{
        order: Order{
            Items:  []OrderItem{},
            Status: StatusPending,
            Total:  big.NewFloat(0),
        },
    }
}

func (b *OrderBuilder) WithID(id int64) *OrderBuilder {
    b.order.ID = id
    return b
}

func (b *OrderBuilder) ForUser(userID int64) *OrderBuilder {
    b.order.UserID = userID
    return b
}

func (b *OrderBuilder) AddItem(productID int64, quantity int, price float64) *OrderBuilder {
    item := OrderItem{
        ProductID: productID,
        Quantity:  quantity,
        Price:     big.NewFloat(price),
    }
    b.order.Items = append(b.order.Items, item)

    // Update total
    itemTotal := big.NewFloat(price * float64(quantity))
    b.order.Total.Add(b.order.Total, itemTotal)

    return b
}

func (b *OrderBuilder) WithStatus(status OrderStatus) *OrderBuilder {
    b.order.Status = status
    return b
}

func (b *OrderBuilder) WithShippingAddress(address Address) *OrderBuilder {
    b.order.ShippingAddress = address
    return b
}

func (b *OrderBuilder) Build() Order {
    return b.order
}

// Usage
func TestOrderProcessing(t *testing.T) {
    address := Address{
        Street: "123 Main St",
        City:   "Boston",
        State:  "MA",
    }

    order := NewOrderBuilder().
        WithID(1).
        ForUser(100).
        AddItem(1, 2, 10.00).
        AddItem(2, 1, 15.00).
        WithStatus(StatusConfirmed).
        WithShippingAddress(address).
        Build()

    expected := big.NewFloat(35.00)
    if order.Total.Cmp(expected) != 0 {
        t.Errorf("expected total %v, got %v", expected, order.Total)
    }

    if len(order.Items) != 2 {
        t.Errorf("expected 2 items, got %d", len(order.Items))
    }
}
```

## Phase 2: Mocking with Testify

### Understanding testify/mock

testify is the most popular Go testing toolkit:

```bash
go get github.com/stretchr/testify
```

**Define Interface**:
```go
// repository.go
package users

type UserRepository interface {
    Save(user *User) error
    FindByID(id int64) (*User, error)
    FindAll() ([]*User, error)
    Delete(id int64) error
}
```

**Generate Mock**:
```go
// Use mockery to generate mocks (optional)
// mockery --name=UserRepository

// Or create manually
// mocks/user_repository.go
package mocks

import (
    "github.com/stretchr/testify/mock"
)

type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) Save(user *User) error {
    args := m.Called(user)
    return args.Error(0)
}

func (m *MockUserRepository) FindByID(id int64) (*User, error) {
    args := m.Called(id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*User), args.Error(1)
}

func (m *MockUserRepository) FindAll() ([]*User, error) {
    args := m.Called()
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).([]*User), args.Error(1)
}

func (m *MockUserRepository) Delete(id int64) error {
    args := m.Called(id)
    return args.Error(0)
}
```

**Using Mocks in Tests**:
```go
package users_test

import (
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "example.com/mocks"
)

func TestUserService_CreateUser(t *testing.T) {
    // Create mock
    mockRepo := new(mocks.MockUserRepository)
    service := NewUserService(mockRepo)

    user := &User{Username: "alice", Email: "alice@test.com"}

    // Set expectations
    mockRepo.On("Save", user).Return(nil)

    // Execute
    err := service.CreateUser(user)

    // Assert
    assert.NoError(t, err)
    mockRepo.AssertExpectations(t)
}

func TestUserService_GetUser(t *testing.T) {
    mockRepo := new(mocks.MockUserRepository)
    service := NewUserService(mockRepo)

    expectedUser := &User{ID: 1, Username: "alice"}

    // Set expectations with return values
    mockRepo.On("FindByID", int64(1)).Return(expectedUser, nil)

    // Execute
    result, err := service.GetUser(1)

    // Assert
    assert.NoError(t, err)
    assert.Equal(t, "alice", result.Username)
    mockRepo.AssertExpectations(t)
}
```

### When to Mock vs Use Real Objects

**Use Mocks For**:
- External APIs and services
- Database operations in unit tests
- File system operations
- Network requests
- Time-dependent operations
- Random number generation

**Use Real Objects For**:
- Pure functions
- Simple structs
- Business logic
- Integration tests
- Critical paths

```go
// GOOD - Mock external API
func TestFetchUserData(t *testing.T) {
    mockAPI := new(mocks.MockExternalAPI)
    service := NewUserService(mockAPI)

    mockAPI.On("GetUser", int64(1)).Return(&User{ID: 1, Username: "alice"}, nil)

    result, err := service.FetchFromAPI(1)

    assert.NoError(t, err)
    assert.Equal(t, "alice", result.Username)
}

// GOOD - Use real function
func TestCalculateTotal(t *testing.T) {
    items := []float64{10, 20, 30}
    result := CalculateTotal(items)
    assert.Equal(t, 60.0, result)
}

// BAD - Over-mocking
func TestCalculateTotal(t *testing.T) {
    mockCalc := new(mocks.MockCalculator)
    mockCalc.On("Sum", mock.Anything).Return(60.0)
    // Testing mock behavior, not real code
}
```

### Mock Configuration

**Argument Matchers**:
```go
// Any argument
mockRepo.On("Save", mock.Anything).Return(nil)

// Specific type
mockRepo.On("Save", mock.AnythingOfType("*User")).Return(nil)

// Custom matcher
mockRepo.On("Save", mock.MatchedBy(func(u *User) bool {
    return u.Age > 18
})).Return(nil)

// Multiple return values
mockRepo.On("FindByID", int64(1)).Return(&User{ID: 1}, nil)

// Return error
mockRepo.On("Save", mock.Anything).Return(errors.New("save failed"))

// Different returns per call
mockAPI.On("FetchStatus").Return("pending").Once()
mockAPI.On("FetchStatus").Return("complete").Once()
```

**Verification**:
```go
// Verify method was called
mockRepo.AssertCalled(t, "Save", user)

// Verify call count
mockRepo.AssertNumberOfCalls(t, "FindByID", 2)

// Verify not called
mockRepo.AssertNotCalled(t, "Delete", mock.Anything)

// Verify all expectations met
mockRepo.AssertExpectations(t)
```

## Phase 3: Mocking HTTP with httptest

### Understanding httptest Package

Go's standard library provides httptest for mocking HTTP:

**Mock HTTP Server**:
```go
package api_test

import (
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestAPIClient_GetUser(t *testing.T) {
    // Create test server
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Verify request
        if r.URL.Path != "/api/users/1" {
            t.Errorf("expected path '/api/users/1', got '%s'", r.URL.Path)
        }
        if r.Method != http.MethodGet {
            t.Errorf("expected GET, got '%s'", r.Method)
        }

        // Send response
        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(http.StatusOK)
        w.Write([]byte(`{"id":1,"username":"alice"}`))
    }))
    defer server.Close()

    // Use test server URL
    client := NewAPIClient(server.URL)
    user, err := client.GetUser(1)

    if err != nil {
        t.Fatalf("GetUser failed: %v", err)
    }
    if user.Username != "alice" {
        t.Errorf("expected 'alice', got '%s'", user.Username)
    }
}

func TestAPIClient_CreateUser(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.Method != http.MethodPost {
            t.Errorf("expected POST, got '%s'", r.Method)
        }

        // Verify request body
        var user User
        json.NewDecoder(r.Body).Decode(&user)
        if user.Username != "alice" {
            t.Errorf("expected username 'alice', got '%s'", user.Username)
        }

        w.WriteHeader(http.StatusCreated)
        w.Write([]byte(`{"id":1,"username":"alice"}`))
    }))
    defer server.Close()

    client := NewAPIClient(server.URL)
    newUser := &User{Username: "alice"}
    result, err := client.CreateUser(newUser)

    if err != nil {
        t.Fatalf("CreateUser failed: %v", err)
    }
    if result.ID != 1 {
        t.Errorf("expected ID 1, got %d", result.ID)
    }
}
```

**Mock HTTP Recorder**:
```go
func TestUserHandler_GetUser(t *testing.T) {
    // Create mock repository
    mockRepo := new(mocks.MockUserRepository)
    handler := NewUserHandler(mockRepo)

    expectedUser := &User{ID: 1, Username: "alice"}
    mockRepo.On("FindByID", int64(1)).Return(expectedUser, nil)

    // Create test request
    req := httptest.NewRequest(http.MethodGet, "/users/1", nil)

    // Create response recorder
    rr := httptest.NewRecorder()

    // Call handler
    handler.GetUser(rr, req)

    // Check status code
    if rr.Code != http.StatusOK {
        t.Errorf("expected status 200, got %d", rr.Code)
    }

    // Check response body
    var user User
    json.NewDecoder(rr.Body).Decode(&user)
    if user.Username != "alice" {
        t.Errorf("expected 'alice', got '%s'", user.Username)
    }

    mockRepo.AssertExpectations(t)
}
```

## Phase 4: Additional Mocking Techniques

### Mocking Time

```go
// Define time provider interface
type TimeProvider interface {
    Now() time.Time
}

// Real implementation
type RealTimeProvider struct{}

func (p *RealTimeProvider) Now() time.Time {
    return time.Now()
}

// Mock for tests
type MockTimeProvider struct {
    CurrentTime time.Time
}

func (p *MockTimeProvider) Now() time.Time {
    return p.CurrentTime
}

// Usage in tests
func TestTimestampGeneration(t *testing.T) {
    mockTime := &MockTimeProvider{
        CurrentTime: time.Date(2024, 1, 15, 12, 0, 0, 0, time.UTC),
    }

    service := NewTimestampService(mockTime)
    timestamp := service.GenerateTimestamp()

    expected := "2024-01-15T12:00:00Z"
    if timestamp != expected {
        t.Errorf("expected '%s', got '%s'", expected, timestamp)
    }
}
```

### Mocking File System

```go
// Define file system interface
type FileSystem interface {
    ReadFile(path string) ([]byte, error)
    WriteFile(path string, data []byte) error
}

// Mock implementation
type MockFileSystem struct {
    mock.Mock
}

func (m *MockFileSystem) ReadFile(path string) ([]byte, error) {
    args := m.Called(path)
    return args.Get(0).([]byte), args.Error(1)
}

func (m *MockFileSystem) WriteFile(path string, data []byte) error {
    args := m.Called(path, data)
    return args.Error(0)
}

// Usage
func TestReadConfig(t *testing.T) {
    mockFS := new(MockFileSystem)
    service := NewFileService(mockFS)

    mockFS.On("ReadFile", "config.txt").Return([]byte("setting=value"), nil)

    config, err := service.ReadConfig("config.txt")

    assert.NoError(t, err)
    assert.Equal(t, "value", config["setting"])
    mockFS.AssertExpectations(t)
}
```

### Mocking Database with sqlmock

```bash
go get github.com/DATA-DOG/go-sqlmock
```

```go
package database_test

import (
    "testing"

    "github.com/DATA-DOG/go-sqlmock"
)

func TestUserRepository_FindByID(t *testing.T) {
    db, mock, err := sqlmock.New()
    if err != nil {
        t.Fatalf("failed to create mock: %v", err)
    }
    defer db.Close()

    repo := NewUserRepository(db)

    // Set expectations
    rows := sqlmock.NewRows([]string{"id", "username", "email"}).
        AddRow(1, "alice", "alice@test.com")

    mock.ExpectQuery("SELECT (.+) FROM users WHERE id = ?").
        WithArgs(1).
        WillReturnRows(rows)

    // Execute
    user, err := repo.FindByID(1)

    // Assert
    if err != nil {
        t.Fatalf("FindByID failed: %v", err)
    }
    if user.Username != "alice" {
        t.Errorf("expected 'alice', got '%s'", user.Username)
    }

    // Verify all expectations met
    if err := mock.ExpectationsWereMet(); err != nil {
        t.Errorf("unmet expectations: %v", err)
    }
}
```

## Output Format

Please provide a comprehensive mocks and fixtures implementation with the following structure:

### Fixture Architecture
**Package-Level Setup** (TestMain):
- [fixture_name]: [purpose, setup, teardown]

**Test-Level Setup**:
- [fixture_name]: [purpose, when to use]

**Fixture Factories**:
- [factory_name]: [creates what, option functions]

### Mocking Strategy
**External Dependencies to Mock**:
| Dependency | Mocking Approach | Tool (testify/httptest) | Reason |
|------------|------------------|-------------------------|--------|
| [API/Service] | [mock/stub] | [tool] | [justification] |

**Mock Configurations**:
```go
// Example mock setup
mockRepo := new(mocks.MockUserRepository)
mockRepo.On("FindByID", int64(1)).Return(&User{ID: 1}, nil)
```

### Test Data Factories
**Factory Functions**:
- UserFactory: [option functions for customization]
- OrderFactory: [option functions for customization]

**Builder Structs**:
- [builder_name]: [purpose, fluent methods]

### Usage Examples
```go
// Example test using fixtures and mocks
func TestUserRegistration(t *testing.T) {
    mockEmail := new(mocks.MockEmailService)
    service := NewUserService(mockEmail)
    factory := NewUserFactory()

    user := factory.Create(WithUsername("alice"))
    mockEmail.On("SendWelcome", user).Return(nil)

    err := service.RegisterUser(user)

    assert.NoError(t, err)
    mockEmail.AssertExpectations(t)
}
```

### Best Practices Implemented
- [ ] Setup uses helper functions with t.Helper()
- [ ] Cleanup uses defer for guaranteed execution
- [ ] Mocks are interface-based
- [ ] Test data factories use option pattern
- [ ] Table-driven tests for multiple cases
- [ ] httptest used for HTTP mocking

### Common Pitfalls Avoided
- Not using interfaces for mocking
- Forgetting defer for cleanup
- Complex test setup that obscures intent
- Over-mocking simple functions
- Not calling AssertExpectations

### Next Steps
- [ ] Implement remaining fixtures for integration tests
- [ ] Add factories for all domain types
- [ ] Document fixture usage for team
- [ ] Set up mockery for automatic mock generation
- [ ] Review mock coverage and necessity

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

1. **Comprehensive fixture setup** using Go testing patterns
2. **Mock configurations** for external dependencies
3. **Test data factories** using option pattern
4. **Builder patterns** for complex structs
5. **Usage documentation** with examples
6. **Best practices guide** for testify and httptest
7. **Fixture and mock catalog** for easy reference
