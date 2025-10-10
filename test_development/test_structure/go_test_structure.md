# Go Test Structure & Infrastructure

## Objective
Design and implement a robust test infrastructure with optimal framework configuration, logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices using Go's native testing package.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/test_structure/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/test_structure/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Test Framework Setup

- [ ] Go modules initialized

- [ ] Testing dependencies installed (testify, gomock, etc.)

- [ ] Test discovery patterns established

- [ ] Build tags configured

- [ ] Coverage tools configured

### Directory Structure

- [ ] Standard Go test layout implemented

- [ ] Test type separation organized

- [ ] Naming conventions documented

- [ ] Testdata directories created

- [ ] Internal test packages configured

### Fixture Infrastructure

- [ ] Test setup/teardown functions established

- [ ] Test helpers defined

- [ ] Table-driven test patterns implemented

- [ ] Mock interfaces generated

- [ ] Common fixtures centralized

### Test Utilities

- [ ] Assertion helpers created

- [ ] Test data builders implemented

- [ ] Helper functions defined

- [ ] Custom matchers established

- [ ] Helper documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Test Infrastructure Setup

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/test_structure"
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

Please design and implement a comprehensive test infrastructure for this Go project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Framework Selection & Configuration

1. **Test Framework Analysis**
   - **Current State**: Document existing test setup if any
   - **Framework Approach**:
     - **testing package** (standard library): Native, no dependencies, simple
     - **testify**: Assertions and mocking, most popular third-party
     - **ginkgo/gomega**: BDD-style, more verbose
   - **Rationale**: Go's testing package is sufficient for most cases, with testify for enhanced assertions

2. **Install Core Testing Dependencies**

   **Initialize Go module**:
   ```bash
   go mod init github.com/username/myapp
   ```

   **Install testing libraries**:
   ```bash
   # Testify - assertions and mocking
   go get github.com/stretchr/testify@latest

   # Gomock - mock generation
   go install github.com/golang/mock/mockgen@latest

   # Additional useful libraries
   go get github.com/DATA-DOG/go-sqlmock@latest         # SQL mocking
   go get github.com/jarcoal/httpmock@latest            # HTTP mocking
   go get github.com/golang/mock/gomock@latest          # Mock framework
   go get github.com/google/go-cmp/cmp@latest           # Deep comparison
   go get github.com/stretchr/testify/suite@latest      # Test suites
   ```

3. **Project Configuration**

   **go.mod example**:
   ```go
   module <REPO_URL>

   go 1.21

   require (
       github.com/stretchr/testify v1.8.4
       github.com/golang/mock v1.6.0
   )

   require (
       github.com/davecgh/go-spew v1.1.1 // indirect
       github.com/pmezard/go-difflib v1.0.0 // indirect
       gopkg.in/yaml.v3 v3.0.1 // indirect
   )
   ```

4. **Makefile for Test Commands**:

   ```makefile
   .PHONY: test test-unit test-integration test-coverage test-race test-verbose clean

   # Run all tests
   test:
   	go test ./...

   # Run unit tests only
   test-unit:
   	go test -short ./...

   # Run integration tests only
   test-integration:
   	go test -run Integration ./...

   # Run tests with coverage
   test-coverage:
   	go test -coverprofile=coverage.out ./...
   	go tool cover -html=coverage.out -o ${OUTPUT_DIR}/exports/coverage.html

   # Run tests with race detector
   test-race:
   	go test -race ./...

   # Run tests with verbose output
   test-verbose:
   	go test -v ./...

   # Run tests with benchmarks
   bench:
   	go test -bench=. -benchmem ./...

   # Generate mocks
   mocks:
   	go generate ./...

   # Clean test artifacts
   clean:
   	rm -f coverage.out coverage.html
   	find . -name "mock_*.go" -delete
   ```

5. **VS Code Configuration** (.vscode/settings.json):

   ```json
   {
       "go.testFlags": ["-v"],
       "go.coverOnSave": true,
       "go.coverageDecorator": {
           "type": "gutter",
           "coveredHighlightColor": "rgba(64,128,64,0.5)",
           "uncoveredHighlightColor": "rgba(128,64,64,0.5)"
       },
       "go.testTimeout": "30s"
   }
   ```

## Phase 2: Directory Structure Design

1. **Standard Go Test Layout**

   Implement this recommended structure:
   ```
   myapp/
   ├── cmd/
   │   └── server/
   │       ├── main.go
   │       └── main_test.go                  # Integration test for binary
   │
   ├── internal/
   │   ├── user/
   │   │   ├── user.go
   │   │   ├── user_test.go                  # Unit tests (same package)
   │   │   ├── user_internal_test.go         # Internal tests (package_test)
   │   │   ├── repository.go
   │   │   ├── repository_test.go
   │   │   ├── service.go
   │   │   ├── service_test.go
   │   │   └── testdata/                     # Test fixtures
   │   │       ├── users.json
   │   │       └── users.golden
   │   │
   │   ├── order/
   │   │   ├── order.go
   │   │   ├── order_test.go
   │   │   ├── service.go
   │   │   ├── service_test.go
   │   │   └── testdata/
   │   │       └── orders.json
   │   │
   │   └── database/
   │       ├── database.go
   │       ├── database_test.go
   │       └── migrations/
   │           └── testdata/
   │               └── test_schema.sql
   │
   ├── pkg/
   │   └── validator/
   │       ├── validator.go
   │       └── validator_test.go
   │
   ├── test/                                 # Integration and E2E tests
   │   ├── integration/
   │   │   ├── user_integration_test.go
   │   │   ├── order_integration_test.go
   │   │   └── setup_test.go                 # Shared test setup
   │   │
   │   ├── e2e/
   │   │   ├── workflows_test.go
   │   │   └── setup_test.go
   │   │
   │   ├── fixtures/
   │   │   ├── database.go                   # Database test fixtures
   │   │   ├── http.go                       # HTTP test fixtures
   │   │   └── mocks.go                      # Common mocks
   │   │
   │   ├── testdata/                         # Shared test data
   │   │   ├── config.yaml
   │   │   └── sample_data.json
   │   │
   │   └── helpers/
   │       ├── assertions.go                 # Custom assertions
   │       ├── builders.go                   # Test data builders
   │       └── database.go                   # Database test helpers
   │
   ├── mocks/                                # Generated mocks (via mockgen)
   │   ├── mock_repository.go
   │   └── mock_service.go
   │
   ├── go.mod
   ├── go.sum
   ├── Makefile
   └── .golangci.yml                         # Linter configuration
   ```

2. **Naming Conventions**

   **File Naming**:
   - Test file: `<source_file>_test.go`
   - Test function: `Test<FunctionName>`
   - Benchmark: `Benchmark<FunctionName>`
   - Example: `Example<FunctionName>`

   **Standard Unit Test Example**:
   ```go
   // internal/user/service_test.go
   package user

   import (
       "testing"

       "github.com/stretchr/testify/assert"
       "github.com/stretchr/testify/require"
   )

   func TestCreateUser(t *testing.T) {
       // Arrange
       repo := &mockRepository{}
       service := NewService(repo)
       user := &User{Name: "John", Email: "john@test.com"}

       // Act
       result, err := service.CreateUser(user)

       // Assert
       require.NoError(t, err)
       assert.NotNil(t, result)
       assert.Equal(t, "John", result.Name)
   }
   ```

   **Table-Driven Test Example**:
   ```go
   func TestValidateEmail(t *testing.T) {
       tests := []struct {
           name    string
           email   string
           wantErr bool
       }{
           {
               name:    "valid email",
               email:   "user@example.com",
               wantErr: false,
           },
           {
               name:    "missing @",
               email:   "userexample.com",
               wantErr: true,
           },
           {
               name:    "empty email",
               email:   "",
               wantErr: true,
           },
       }

       for _, tt := range tests {
           t.Run(tt.name, func(t *testing.T) {
               err := ValidateEmail(tt.email)
               if tt.wantErr {
                   assert.Error(t, err)
               } else {
                   assert.NoError(t, err)
               }
           })
       }
   }
   ```

   **Subtests and Parallel Execution**:
   ```go
   func TestUserService(t *testing.T) {
       t.Run("CreateUser", func(t *testing.T) {
           t.Parallel()
           // Test implementation
       })

       t.Run("GetUser", func(t *testing.T) {
           t.Parallel()
           // Test implementation
       })

       t.Run("DeleteUser", func(t *testing.T) {
           t.Parallel()
           // Test implementation
       })
   }
   ```

3. **Test Type Organization**

   **Unit Tests** (in package directories):
   - Test files alongside source: `user.go` → `user_test.go`
   - Use `-short` flag to run only unit tests
   - Fast execution (<10ms per test)
   - Heavy use of mocking

   **Integration Tests** (`test/integration/`):
   - Test multiple components together
   - No `-short` flag (longer running)
   - Real dependencies (test database, etc.)
   - Use build tags if needed: `//go:build integration`

   **E2E Tests** (`test/e2e/`):
   - Test complete workflows
   - Full system with real dependencies
   - Use build tags: `//go:build e2e`

## Phase 3: Fixture Infrastructure

1. **Test Setup and Teardown**

   **TestMain for package-level setup**:
   ```go
   // internal/user/user_test.go
   package user

   import (
       "os"
       "testing"
   )

   func TestMain(m *testing.M) {
       // Setup: runs before all tests in package
       setup()

       // Run tests
       code := m.Run()

       // Teardown: runs after all tests
       teardown()

       os.Exit(code)
   }

   func setup() {
       // Initialize test database, load fixtures, etc.
   }

   func teardown() {
       // Clean up resources
   }
   ```

   **Setup/teardown helpers**:
   ```go
   // test/helpers/database.go
   package helpers

   import (
       "database/sql"
       "testing"

       _ "github.com/lib/pq"
   )

   // SetupTestDB creates a test database and returns cleanup function
   func SetupTestDB(t *testing.T) (*sql.DB, func()) {
       t.Helper()

       db, err := sql.Open("postgres", "postgres://localhost/testdb?sslmode=disable")
       if err != nil {
           t.Fatalf("Failed to connect to test database: %v", err)
       }

       // Run migrations
       if err := runMigrations(db); err != nil {
           t.Fatalf("Failed to run migrations: %v", err)
       }

       cleanup := func() {
           db.Exec("DROP SCHEMA public CASCADE")
           db.Exec("CREATE SCHEMA public")
           db.Close()
       }

       return db, cleanup
   }
   ```

2. **Test Fixtures**

   **Database fixtures**:
   ```go
   // test/fixtures/database.go
   package fixtures

   import (
       "database/sql"
       "testing"
   )

   type DBFixture struct {
       DB *sql.DB
   }

   func NewDBFixture(t *testing.T) *DBFixture {
       t.Helper()

       db, err := sql.Open("postgres", testDBURL)
       if err != nil {
           t.Fatalf("Failed to open database: %v", err)
       }

       t.Cleanup(func() {
           db.Close()
       })

       return &DBFixture{DB: db}
   }

   func (f *DBFixture) SeedUsers(t *testing.T, users ...*User) {
       t.Helper()

       for _, user := range users {
           _, err := f.DB.Exec(
               "INSERT INTO users (name, email) VALUES ($1, $2)",
               user.Name, user.Email,
           )
           if err != nil {
               t.Fatalf("Failed to seed user: %v", err)
           }
       }
   }

   func (f *DBFixture) Clear(t *testing.T) {
       t.Helper()

       tables := []string{"orders", "users"}
       for _, table := range tables {
           _, err := f.DB.Exec("TRUNCATE TABLE " + table + " CASCADE")
           if err != nil {
               t.Fatalf("Failed to truncate %s: %v", table, err)
           }
       }
   }
   ```

   **HTTP test fixtures**:
   ```go
   // test/fixtures/http.go
   package fixtures

   import (
       "net/http"
       "net/http/httptest"
       "testing"
   )

   type HTTPFixture struct {
       Server *httptest.Server
       Client *http.Client
   }

   func NewHTTPFixture(t *testing.T, handler http.Handler) *HTTPFixture {
       t.Helper()

       server := httptest.NewServer(handler)

       t.Cleanup(func() {
           server.Close()
       })

       return &HTTPFixture{
           Server: server,
           Client: server.Client(),
       }
   }

   func (f *HTTPFixture) GetURL(path string) string {
       return f.Server.URL + path
   }
   ```

3. **Mock Generation with mockgen**

   **Interface definition**:
   ```go
   // internal/user/repository.go
   package user

   //go:generate mockgen -destination=../../mocks/mock_repository.go -package=mocks <REPO_URL>/internal/user Repository

   type Repository interface {
       Create(user *User) error
       GetByID(id int) (*User, error)
       Update(user *User) error
       Delete(id int) error
   }
   ```

   **Generate mocks**:
   ```bash
   go generate ./...
   ```

   **Using generated mocks**:
   ```go
   // internal/user/service_test.go
   package user

   import (
       "testing"

       "github.com/golang/mock/gomock"
       "github.com/stretchr/testify/assert"
       "<REPO_URL>/mocks"
   )

   func TestCreateUser(t *testing.T) {
       ctrl := gomock.NewController(t)
       defer ctrl.Finish()

       mockRepo := mocks.NewMockRepository(ctrl)
       service := NewService(mockRepo)

       user := &User{Name: "John"}

       mockRepo.EXPECT().
           Create(gomock.Any()).
           Return(nil).
           Times(1)

       err := service.CreateUser(user)
       assert.NoError(t, err)
   }
   ```

4. **Testify Suite Pattern**

   ```go
   // internal/user/service_suite_test.go
   package user

   import (
       "testing"

       "github.com/stretchr/testify/suite"
   )

   type ServiceTestSuite struct {
       suite.Suite
       service    *Service
       mockRepo   *mockRepository
   }

   func (s *ServiceTestSuite) SetupSuite() {
       // Runs once before all tests
   }

   func (s *ServiceTestSuite) TearDownSuite() {
       // Runs once after all tests
   }

   func (s *ServiceTestSuite) SetupTest() {
       // Runs before each test
       s.mockRepo = &mockRepository{}
       s.service = NewService(s.mockRepo)
   }

   func (s *ServiceTestSuite) TearDownTest() {
       // Runs after each test
   }

   func (s *ServiceTestSuite) TestCreateUser() {
       user := &User{Name: "John"}
       result, err := s.service.CreateUser(user)

       s.NoError(err)
       s.NotNil(result)
       s.Equal("John", result.Name)
   }

   func TestServiceTestSuite(t *testing.T) {
       suite.Run(t, new(ServiceTestSuite))
   }
   ```

## Phase 4: Test Utilities & Helpers

1. **Custom Assertions** (`test/helpers/assertions.go`):

   ```go
   package helpers

   import (
       "regexp"
       "testing"
       "time"
   )

   func AssertValidEmail(t *testing.T, email string) {
       t.Helper()

       pattern := `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
       matched, err := regexp.MatchString(pattern, email)
       if err != nil || !matched {
           t.Errorf("Invalid email format: %s", email)
       }
   }

   func AssertTimeRecent(t *testing.T, ts time.Time, maxAge time.Duration) {
       t.Helper()

       age := time.Since(ts)
       if age > maxAge {
           t.Errorf("Time %v is not recent (age: %v, max: %v)", ts, age, maxAge)
       }
   }

   func AssertJSONEqual(t *testing.T, expected, actual string) {
       t.Helper()

       var expectedJSON, actualJSON interface{}
       if err := json.Unmarshal([]byte(expected), &expectedJSON); err != nil {
           t.Fatalf("Invalid expected JSON: %v", err)
       }
       if err := json.Unmarshal([]byte(actual), &actualJSON); err != nil {
           t.Fatalf("Invalid actual JSON: %v", err)
       }

       if diff := cmp.Diff(expectedJSON, actualJSON); diff != "" {
           t.Errorf("JSON mismatch (-want +got):\n%s", diff)
       }
   }
   ```

2. **Test Data Builders** (`test/helpers/builders.go`):

   ```go
   package helpers

   import "time"

   type UserBuilder struct {
       id        int
       name      string
       email     string
       createdAt time.Time
       active    bool
   }

   func NewUserBuilder() *UserBuilder {
       return &UserBuilder{
           id:        1,
           name:      "Test User",
           email:     "test@example.com",
           createdAt: time.Now(),
           active:    true,
       }
   }

   func (b *UserBuilder) WithID(id int) *UserBuilder {
       b.id = id
       return b
   }

   func (b *UserBuilder) WithName(name string) *UserBuilder {
       b.name = name
       return b
   }

   func (b *UserBuilder) WithEmail(email string) *UserBuilder {
       b.email = email
       return b
   }

   func (b *UserBuilder) Inactive() *UserBuilder {
       b.active = false
       return b
   }

   func (b *UserBuilder) Build() *User {
       return &User{
           ID:        b.id,
           Name:      b.name,
           Email:     b.email,
           CreatedAt: b.createdAt,
           Active:    b.active,
       }
   }

   // Usage in tests:
   // user := NewUserBuilder().WithName("John").WithEmail("john@test.com").Build()
   ```

3. **Golden File Testing**:

   ```go
   // test/helpers/golden.go
   package helpers

   import (
       "flag"
       "os"
       "path/filepath"
       "testing"
   )

   var update = flag.Bool("update", false, "update golden files")

   func CompareGolden(t *testing.T, actual []byte, goldenFile string) {
       t.Helper()

       goldenPath := filepath.Join("testdata", goldenFile)

       if *update {
           if err := os.WriteFile(goldenPath, actual, 0644); err != nil {
               t.Fatalf("Failed to update golden file: %v", err)
           }
           return
       }

       expected, err := os.ReadFile(goldenPath)
       if err != nil {
           t.Fatalf("Failed to read golden file: %v", err)
       }

       if diff := cmp.Diff(string(expected), string(actual)); diff != "" {
           t.Errorf("Output mismatch (-want +got):\n%s", diff)
       }
   }

   // Usage:
   // go test -update  # Update golden files
   // go test          # Compare against golden files
   ```

4. **Test Helpers**:

   ```go
   // test/helpers/helpers.go
   package helpers

   import (
       "encoding/json"
       "io"
       "net/http"
       "net/http/httptest"
       "strings"
       "testing"
   )

   func MakeRequest(t *testing.T, handler http.Handler, method, path string, body interface{}) *httptest.ResponseRecorder {
       t.Helper()

       var bodyReader io.Reader
       if body != nil {
           data, err := json.Marshal(body)
           if err != nil {
               t.Fatalf("Failed to marshal request body: %v", err)
           }
           bodyReader = strings.NewReader(string(data))
       }

       req := httptest.NewRequest(method, path, bodyReader)
       if body != nil {
           req.Header.Set("Content-Type", "application/json")
       }

       rec := httptest.NewRecorder()
       handler.ServeHTTP(rec, req)

       return rec
   }

   func ParseResponse(t *testing.T, resp *httptest.ResponseRecorder, v interface{}) {
       t.Helper()

       if err := json.NewDecoder(resp.Body).Decode(v); err != nil {
           t.Fatalf("Failed to decode response: %v", err)
       }
   }
   ```

## Phase 5: Test Discovery & Execution

1. **Run Tests**

   ```bash
   # Run all tests
   go test ./...

   # Run tests in specific package
   go test ./internal/user

   # Run specific test
   go test -run TestCreateUser ./internal/user

   # Run tests matching pattern
   go test -run User ./...

   # Run unit tests only (with -short flag)
   go test -short ./...

   # Run tests with coverage
   go test -cover ./...
   go test -coverprofile=coverage.out ./...
   go tool cover -html=coverage.out

   # Run tests with race detector
   go test -race ./...

   # Run tests in parallel
   go test -parallel 4 ./...

   # Run tests with verbose output
   go test -v ./...

   # Run integration tests (with build tag)
   go test -tags=integration ./test/integration

   # Run benchmarks
   go test -bench=. ./...
   go test -bench=. -benchmem ./...
   ```

2. **Build Tags for Test Types**:

   ```go
   // test/integration/user_integration_test.go
   //go:build integration

   package integration

   import "testing"

   func TestUserIntegration(t *testing.T) {
       if testing.Short() {
           t.Skip("Skipping integration test in short mode")
       }
       // Test implementation
   }
   ```

   ```bash
   # Run integration tests
   go test -tags=integration ./test/integration

   # Run without integration tests
   go test ./...
   ```

3. **Test Script** (scripts/test.sh):

   ```bash
   #!/bin/bash
   set -e

   echo "Running unit tests..."
   go test -short -race -coverprofile=coverage.txt -covermode=atomic ./...

   echo "Running integration tests..."
   go test -tags=integration ./test/integration/...

   echo "Generating coverage report..."
   go tool cover -html=coverage.txt -o ${OUTPUT_DIR}/exports/coverage.html

   echo "Running linters..."
   golangci-lint run

   echo "All tests passed!"
   ```

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

Replace `{phase_name}` with the specific phase (test_structure, test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

## Output Format

Please provide a comprehensive test infrastructure design with the following structure:

### Infrastructure Summary

- **Test Framework**: [testing package + libraries used]

- **Go Version**: [version]

- **Total Packages**: [count]

- **Test Organization**: [structure description]

- **Mock Strategy**: [approach description]

- **Utility Packages**: [list of helper packages]

### Project Structure
```
[Complete directory tree with all packages and key files]
```

### Dependencies Installed
**Testing Libraries**:

- [package]: [version] - [purpose]

**Mocking Frameworks**:

- [package]: [version] - [purpose]

**Assertion Libraries**:

- [package]: [version] - [purpose]

### Test Infrastructure
**Setup Functions**:

- [TestMain usage]: [description]

- [Setup helpers]: [description]

**Fixtures**:

- [FixtureName]: [purpose and usage]

**Mocks**:

- [Mock generation approach]: [description]

### Test Utilities
**Assertion Helpers** (`test/helpers/assertions.go`):

- [HelperName]: [purpose]

**Test Builders** (`test/helpers/builders.go`):

- [BuilderName]: [purpose]

**Other Helpers**:

- [HelperName]: [purpose]

### Test Execution Commands
```bash
# Run all tests
go test ./...
make test

# Run unit tests
go test -short ./...
make test-unit

# Run integration tests
go test -tags=integration ./test/integration
make test-integration

# Run with coverage
go test -coverprofile=coverage.out ./...
make test-coverage

# Run with race detector
go test -race ./...
make test-race

# Run benchmarks
go test -bench=. -benchmem ./...
make bench

# Generate mocks
go generate ./...
make mocks
```

### Testing Conventions Established
1. **File Naming**: [convention]
2. **Test Function Naming**: [convention]
3. **Table-Driven Tests**: [pattern]
4. **Subtest Usage**: [when to use]
5. **Test Data**: [testdata directories, golden files]

### Next Steps

- [ ] Implement actual test cases

- [ ] Add project-specific fixtures

- [ ] Configure CI/CD (GitHub Actions, GitLab CI)

- [ ] Set up coverage reporting (codecov, coveralls)

- [ ] Document testing guidelines

- [ ] Create benchmark suite

- [ ] Set up fuzzing tests

### Best Practices Implemented

- Table-driven tests for multiple scenarios

- Helper functions marked with t.Helper()

- Parallel test execution where safe

- Clear test organization by type

- Reusable test fixtures and builders

- Mock generation automation

- Coverage measurement integrated

### Maintenance Recommendations

- Run tests before committing

- Keep tests fast and isolated

- Use t.Helper() in helper functions

- Cleanup resources with t.Cleanup()

- Update golden files when needed

- Monitor test execution time

- Review and update mocks regularly
~~~

## Output Format

The AI assistant should deliver:

1. **Test infrastructure design document** with complete project structure
2. **Test helper packages** with reusable utilities
3. **Fixture implementations** for common test scenarios
4. **Mock generation setup** with go:generate directives
5. **Makefile** for easy test execution
6. **Documentation** of conventions and best practices
7. **Execution commands** for common test scenarios
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
