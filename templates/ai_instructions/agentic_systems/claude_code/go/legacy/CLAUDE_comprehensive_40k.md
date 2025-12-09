---
template_id: CLAUDE_comprehensive_40k
template_name: Go - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: claude_code
phase: go
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tools:

  - unity

  - cmocka

  - check
tags:

  - claude-code

  - c
---
# CLAUDE.md - Go Development System Instructions
*Comprehensive system prompt for Claude Code - Optimized for Go development*

---

# Quick Start for Common Tasks

## Section Usage Map
- **Bug Fix**: Sections 1, 3, 9

- **New Feature**: Sections 1-5, 7

- **Refactoring**: Sections 3, 6, 9

- **Project Setup**: All sections

## Task-Specific Quick Reference
- **Fix a function**: Focus sections 3, 9

- **New project**: Use sections 2, 4, 5

- **Code review**: Apply sections 3, 10

## Context-Aware Behavior
- **For utilities**: Minimal structure

- **For microservices**: Full project architecture

- **For debugging**: Focus on problem-solving

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation

- Minimal testing setup

- Focus on core functionality

### Full Mode (for new projects)
- Complete project architecture

- Comprehensive testing

- Full documentation

## Claude Code Terminal Commands
- **Run tests**: `claude run go test ./...`

- **Build project**: `claude run go build`

- **Run application**: `claude run go run main.go`

- **Format code**: `claude run gofmt -w .`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding

- Never make assumptions about missing requirements

- Frame questions to gather specific technical requirements

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work

- Explain implementation details, reasoning, and coding concepts

- Enable learning through understanding, not copy-paste

- Reference Go documentation and effective Go practices

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions

- Analyze problems independently

- Compare alternatives and recommend best solution

- Clearly explain reasoning and trade-offs

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity

- **Code Modification**: Edit originals, don't create '_enhanced' versions

- **Codebase Cleanup**: Remove obsolete functions

- **Refactoring**: Consolidate duplicate logic

### Quality Assurance
- Review code for: quality, efficiency, best practices, security, performance

- If already optimal, confirm briefly with reasoning

### System Prompt Adherence
- Periodically review these instructions during long conversations

- Maintain consistency with all standards and workflows


# 2. Project Architecture
---

## Standard Go Project Structure

```
project-name/
├── cmd/
│   └── api/
│       └── main.go                   # Application entry point
├── internal/
│   ├── handler/                      # HTTP handlers
│   │   ├── user_handler.go
│   │   └── handler_test.go
│   ├── service/                      # Business logic
│   │   ├── user_service.go
│   │   └── service_test.go
│   ├── repository/                   # Data access
│   │   ├── user_repository.go
│   │   └── repository_test.go
│   ├── model/                        # Domain models
│   │   └── user.go
│   └── middleware/                   # HTTP middleware
│       └── auth.go
├── pkg/                              # Public packages
│   └── logger/
│       └── logger.go
├── config/                           # Configuration files
│   ├── config.go
│   └── config.yaml
├── migrations/                       # Database migrations
│   └── 001_create_users.sql
├── scripts/                          # Build and deploy scripts
│   └── build.sh
├── go.mod                            # Module definition
├── go.sum                            # Dependency checksums
├── CHANGELOG.md                      # Version history
├── README.md                         # Project documentation
├── .gitignore                        # Git ignore rules
└── Makefile                          # Build automation
```

## Project Initialization Sequence

1. **Initialize module**: `go mod init <MODULE_PATH>` (e.g., `example.com/username/project-name` or your repository domain)

2. **Create directory structure** as outlined above

3. **Create `main.go`** in cmd/api/

4. **Create `config.yaml`** with application settings

5. **Create `.gitignore`** (binaries, vendor/, .env)

6. **Create `CHANGELOG.md`** starting with version 0.1.0

7. **Create `README.md`** with setup instructions

8. **Create `Makefile`** for common tasks

9. **Set up database migrations**

## go.mod Template
```go
module <MODULE_PATH>

go 1.22

require (
    github.com/gin-gonic/gin v1.10.0
    github.com/lib/pq v1.10.9
    github.com/stretchr/testify v1.9.0
    go.uber.org/zap v1.27.0
)
```

**Note**: Replace `<MODULE_PATH>` with your module path (e.g., `example.com/company/project-name` or your repository path)

## Makefile Template
```makefile
.PHONY: build test run clean

build:
\tgo build -o bin/api cmd/api/main.go

test:
\tgo test -v -cover ./...

run:
\tgo run cmd/api/main.go

clean:
\trm -rf bin/

lint:
\tgolangci-lint run

fmt:
\tgofmt -w .
\tgoimports -w .
```


# 3. Code Standards
---

## Go Style Guidelines

### Naming Conventions
```go
// Exported types, functions: PascalCase
type UserService struct {}
func NewUserService() *UserService {}

// Unexported: camelCase
type userRepository struct {}
func getUserByID(id int) *User {}

// Constants: PascalCase or UPPER_SNAKE (context-dependent)
const MaxRetries = 3
const DEFAULT_PORT = 8080

// Interfaces: -er suffix for single-method
type Reader interface {
    Read(p []byte) (n int, err error)
}

// Package names: lowercase, single word
package userservice
```

### File Structure
```go
// 1. Package declaration
package handler

// 2. Imports (grouped: stdlib, external, internal)
import (
    "context"
    "encoding/json"
    "net/http"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"

    "<MODULE_PATH>/internal/model"
    "<MODULE_PATH>/internal/service"
)

// 3. Constants
const (
    DefaultPageSize = 20
    MaxPageSize     = 100
)

// 4. Types
type UserHandler struct {
    service service.UserService
    logger  *zap.Logger
}

// 5. Constructor
func NewUserHandler(service service.UserService, logger *zap.Logger) *UserHandler {
    return &UserHandler{
        service: service,
        logger:  logger,
    }
}

// 6. Methods
func (h *UserHandler) GetUser(c *gin.Context) {
    // Implementation
}
```

### Error Handling
```go
// ✅ Good - Return errors, don't panic
func GetUser(id int) (*User, error) {
    if id <= 0 {
        return nil, fmt.Errorf("invalid user ID: %d", id)
    }

    user, err := repository.FindByID(id)
    if err != nil {
        return nil, fmt.Errorf("failed to get user: %w", err)
    }

    return user, nil
}

// ✅ Good - Custom error types
type NotFoundError struct {
    Resource string
    ID       int
}

func (e *NotFoundError) Error() string {
    return fmt.Sprintf("%s with ID %d not found", e.Resource, e.ID)
}

// ✅ Good - Error wrapping
if err != nil {
    return fmt.Errorf("processing user %d: %w", userID, err)
}

// ❌ Avoid - Ignoring errors
user, _ := GetUser(id) // Bad practice
```

### Concurrency Patterns
```go
// ✅ Good - Use channels for communication
func ProcessUsers(users []User) <-chan Result {
    results := make(chan Result)

    go func() {
        defer close(results)
        for _, user := range users {
            result := processUser(user)
            results <- result
        }
    }()

    return results
}

// ✅ Good - Worker pool pattern
func WorkerPool(jobs <-chan Job, results chan<- Result, numWorkers int) {
    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                results <- processJob(job)
            }
        }()
    }

    go func() {
        wg.Wait()
        close(results)
    }()
}

// ✅ Good - Context for cancellation
func FetchData(ctx context.Context, url string) ([]byte, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    return io.ReadAll(resp.Body)
}
```

### Interface Design
```go
// ✅ Good - Small, focused interfaces
type UserGetter interface {
    GetByID(ctx context.Context, id int) (*User, error)
}

type UserCreator interface {
    Create(ctx context.Context, user *User) error
}

type UserRepository interface {
    UserGetter
    UserCreator
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id int) error
}

// ✅ Good - Accept interfaces, return structs
func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}
```

### HTTP Handler Patterns (Gin)
```go
type UserHandler struct {
    service *service.UserService
    logger  *zap.Logger
}

func NewUserHandler(service *service.UserService, logger *zap.Logger) *UserHandler {
    return &UserHandler{
        service: service,
        logger:  logger,
    }
}

// GET /users/:id
func (h *UserHandler) GetUser(c *gin.Context) {
    id, err := strconv.Atoi(c.Param("id"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "invalid user ID"})
        return
    }

    user, err := h.service.GetByID(c.Request.Context(), id)
    if err != nil {
        if errors.Is(err, service.ErrNotFound) {
            c.JSON(http.StatusNotFound, gin.H{"error": "user not found"})
            return
        }
        h.logger.Error("failed to get user", zap.Error(err), zap.Int("id", id))
        c.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
        return
    }

    c.JSON(http.StatusOK, user)
}

// POST /users
func (h *UserHandler) CreateUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user := &model.User{
        Name:  req.Name,
        Email: req.Email,
    }

    if err := h.service.Create(c.Request.Context(), user); err != nil {
        if errors.Is(err, service.ErrDuplicateEmail) {
            c.JSON(http.StatusConflict, gin.H{"error": "email already exists"})
            return
        }
        h.logger.Error("failed to create user", zap.Error(err))
        c.JSON(http.StatusInternalServerError, gin.H{"error": "internal server error"})
        return
    }

    c.JSON(http.StatusCreated, user)
}
```

### Service Layer
```go
type UserService struct {
    repo   UserRepository
    logger *zap.Logger
}

func NewUserService(repo UserRepository, logger *zap.Logger) *UserService {
    return &UserService{
        repo:   repo,
        logger: logger,
    }
}

func (s *UserService) GetByID(ctx context.Context, id int) (*model.User, error) {
    s.logger.Debug("fetching user", zap.Int("id", id))

    user, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("failed to get user: %w", err)
    }

    return user, nil
}

func (s *UserService) Create(ctx context.Context, user *model.User) error {
    // Validation
    if err := s.validateUser(user); err != nil {
        return fmt.Errorf("validation failed: %w", err)
    }

    // Check for duplicate email
    exists, err := s.repo.ExistsByEmail(ctx, user.Email)
    if err != nil {
        return fmt.Errorf("failed to check email: %w", err)
    }
    if exists {
        return ErrDuplicateEmail
    }

    // Create user
    if err := s.repo.Create(ctx, user); err != nil {
        return fmt.Errorf("failed to create user: %w", err)
    }

    s.logger.Info("user created", zap.Int("id", user.ID))
    return nil
}

func (s *UserService) validateUser(user *model.User) error {
    if user.Name == "" {
        return errors.New("name is required")
    }
    if user.Email == "" {
        return errors.New("email is required")
    }
    return nil
}
```

### Repository Pattern
```go
type UserRepository interface {
    GetByID(ctx context.Context, id int) (*model.User, error)
    GetByEmail(ctx context.Context, email string) (*model.User, error)
    ExistsByEmail(ctx context.Context, email string) (bool, error)
    Create(ctx context.Context, user *model.User) error
    Update(ctx context.Context, user *model.User) error
    Delete(ctx context.Context, id int) error
}

type userRepository struct {
    db *sql.DB
}

func NewUserRepository(db *sql.DB) UserRepository {
    return &userRepository{db: db}
}

func (r *userRepository) GetByID(ctx context.Context, id int) (*model.User, error) {
    query := `SELECT id, name, email, created_at FROM users WHERE id = $1`

    var user model.User
    err := r.db.QueryRowContext(ctx, query, id).Scan(
        &user.ID,
        &user.Name,
        &user.Email,
        &user.CreatedAt,
    )
    if err != nil {
        if err == sql.ErrNoRows {
            return nil, ErrNotFound
        }
        return nil, fmt.Errorf("query failed: %w", err)
    }

    return &user, nil
}

func (r *userRepository) Create(ctx context.Context, user *model.User) error {
    query := `
        INSERT INTO users (name, email, created_at)
        VALUES ($1, $2, $3)
        RETURNING id
    `

    err := r.db.QueryRowContext(
        ctx,
        query,
        user.Name,
        user.Email,
        time.Now(),
    ).Scan(&user.ID)

    if err != nil {
        return fmt.Errorf("insert failed: %w", err)
    }

    return nil
}
```

### Model Definition
```go
package model

import "time"

type User struct {
    ID        int       `json:"id"`
    Name      string    `json:"name" binding:"required"`
    Email     string    `json:"email" binding:"required,email"`
    Role      UserRole  `json:"role"`
    IsActive  bool      `json:"is_active"`
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at,omitempty"`
}

type UserRole string

const (
    RoleUser  UserRole = "user"
    RoleAdmin UserRole = "admin"
)

type CreateUserRequest struct {
    Name  string `json:"name" binding:"required"`
    Email string `json:"email" binding:"required,email"`
}

type UpdateUserRequest struct {
    Name  string `json:"name,omitempty"`
    Email string `json:"email,omitempty,email"`
}
```


# 4. Documentation Standards
---

## Go Doc Comments

### Package Documentation
```go
// Package userservice provides user management functionality.
//
// This package implements the business logic for user operations,
// including creation, retrieval, updates, and deletion.
package userservice
```

### Function Documentation
```go
// GetUser retrieves a user by ID.
//
// It returns an error if the user is not found or if a database error occurs.
// The error will be wrapped with context information.
//
// Example:
//
//     user, err := service.GetUser(ctx, 123)
//     if err != nil {
//         log.Fatal(err)
//     }
//     fmt.Println(user.Name)
func GetUser(ctx context.Context, id int) (*User, error) {
    // Implementation
}
```

### Type Documentation
```go
// UserService handles user-related business logic.
//
// It coordinates between the HTTP handlers and the data repository,
// applying business rules and validation.
type UserService struct {
    repo   UserRepository
    logger *zap.Logger
}
```

## README.md Structure
```markdown
# [Project Name]

## Overview
[2-3 sentence description]

## Features
- [Core capabilities]

## Requirements
- Go 1.22 or higher

- PostgreSQL 15+

## Installation

    ```bash
    git clone <REPO_URL>
    cd [project-name]
    go mod download
    ```

**Note**: Your repository URL is stored in `.git/config`. To retrieve it:

```bash
git config --get remote.origin.url
```

## Configuration

Create a `config.yaml` file:

    ```yaml
    server:
      port: 8080
    database:
      host: localhost
      port: 5432
      name: mydb
    ```

## Usage

    ```bash
    go run cmd/api/main.go
    ```

## Testing

    ```bash
    go test ./...
    go test -cover ./...
    ```

## Building

    ```bash
    make build
    ```
```

## CHANGELOG.md Structure
```markdown
# Changelog

## [Unreleased]

### Added
### Changed
### Fixed

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Improvements

### Fixed
- Bug fixes
```


# 5. Testing Framework
---

## Test Structure

1. **Unit Tests**: Test functions in isolation

2. **Integration Tests**: Test with real database

3. **Table-Driven Tests**: Test multiple scenarios

4. **Benchmark Tests**: Performance testing

## Testing Template

```go
package service_test

import (
    "context"
    "errors"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"

    "<MODULE_PATH>/internal/model"
    "<MODULE_PATH>/internal/service"
)

// Mock repository
type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) GetByID(ctx context.Context, id int) (*model.User, error) {
    args := m.Called(ctx, id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*model.User), args.Error(1)
}

func TestUserService_GetByID(t *testing.T) {
    tests := []struct {
        name    string
        userID  int
        setup   func(*MockUserRepository)
        want    *model.User
        wantErr bool
    }{
        {
            name:   "success - user found",
            userID: 1,
            setup: func(m *MockUserRepository) {
                m.On("GetByID", mock.Anything, 1).
                    Return(&model.User{ID: 1, Name: "John Doe"}, nil)
            },
            want:    &model.User{ID: 1, Name: "John Doe"},
            wantErr: false,
        },
        {
            name:   "error - user not found",
            userID: 999,
            setup: func(m *MockUserRepository) {
                m.On("GetByID", mock.Anything, 999).
                    Return(nil, service.ErrNotFound)
            },
            want:    nil,
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Setup
            mockRepo := new(MockUserRepository)
            tt.setup(mockRepo)

            svc := service.NewUserService(mockRepo, nil)

            // Execute
            got, err := svc.GetByID(context.Background(), tt.userID)

            // Assert
            if tt.wantErr {
                require.Error(t, err)
                assert.Nil(t, got)
            } else {
                require.NoError(t, err)
                assert.Equal(t, tt.want, got)
            }

            mockRepo.AssertExpectations(t)
        })
    }
}

func TestUserService_Create(t *testing.T) {
    t.Run("success", func(t *testing.T) {
        mockRepo := new(MockUserRepository)
        mockRepo.On("ExistsByEmail", mock.Anything, "john@example.com").
            Return(false, nil)
        mockRepo.On("Create", mock.Anything, mock.AnythingOfType("*model.User")).
            Return(nil)

        svc := service.NewUserService(mockRepo, nil)

        user := &model.User{
            Name:  "John Doe",
            Email: "john@example.com",
        }

        err := svc.Create(context.Background(), user)

        require.NoError(t, err)
        mockRepo.AssertExpectations(t)
    })

    t.Run("duplicate email", func(t *testing.T) {
        mockRepo := new(MockUserRepository)
        mockRepo.On("ExistsByEmail", mock.Anything, "john@example.com").
            Return(true, nil)

        svc := service.NewUserService(mockRepo, nil)

        user := &model.User{
            Name:  "John Doe",
            Email: "john@example.com",
        }

        err := svc.Create(context.Background(), user)

        require.Error(t, err)
        assert.True(t, errors.Is(err, service.ErrDuplicateEmail))
    })
}

// Benchmark test
func BenchmarkUserService_GetByID(b *testing.B) {
    mockRepo := new(MockUserRepository)
    mockRepo.On("GetByID", mock.Anything, 1).
        Return(&model.User{ID: 1, Name: "John Doe"}, nil)

    svc := service.NewUserService(mockRepo, nil)
    ctx := context.Background()

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = svc.GetByID(ctx, 1)
    }
}
```

## Integration Tests
```go
// +build integration

package repository_test

import (
    "context"
    "database/sql"
    "testing"

    _ "github.com/lib/pq"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"

    "<MODULE_PATH>/internal/model"
    "<MODULE_PATH>/internal/repository"
)

func setupTestDB(t *testing.T) *sql.DB {
    db, err := sql.Open("postgres", "postgres://localhost/testdb?sslmode=disable")
    require.NoError(t, err)

    // Clean up
    _, err = db.Exec("TRUNCATE TABLE users CASCADE")
    require.NoError(t, err)

    return db
}

func TestUserRepository_Create(t *testing.T) {
    db := setupTestDB(t)
    defer db.Close()

    repo := repository.NewUserRepository(db)

    user := &model.User{
        Name:  "John Doe",
        Email: "john@example.com",
    }

    err := repo.Create(context.Background(), user)

    require.NoError(t, err)
    assert.NotZero(t, user.ID)
}
```


# 6. Development Workflow
---

## Task Breakdown

### When to Use
- Projects >30 minutes

- Multi-component applications

- Complex features

- Integration tasks

### Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope]

### Prerequisites
- Go 1.22+ installed

- PostgreSQL configured

- Make installed

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Outputs]
**Time**: [15-45 min]

**Prompt**:
```
[Instructions]
[Success criteria]

Complete and pause.
```
```

### Quality Gates
- [ ] Code compiles

- [ ] Tests passing

- [ ] gofmt applied

- [ ] golangci-lint clean


## Iterative Testing Protocol

**When implementing features or fixing bugs:**

1. **Create temp tests** in `tests/temp/` (e.g., `temp_feature_validation_test.go`)

2. **Write challenging tests** with edge cases

3. **Implement solution** following code standards

4. **Run tests and iterate**:

   - If FAIL: Document in DEVLOG.md, modify code, repeat

   - If PASS: Proceed to cleanup

5. **Delete temp tests** after successful implementation

6. **Document process** in DEVLOG.md with iteration count

**Benefits**: Ensures solutions work, documents problem-solving, prevents premature success claims, maintains clean repository



# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Pattern:
```
Please run in your terminal:

1. Build:
   go build -o bin/api cmd/api/main.go

2. Test:
   go test ./...

3. Share any errors.
```

## Go Commands

```bash
# Build
go build -o bin/api cmd/api/main.go
go build ./...

# Testing
go test ./...
go test -v ./...
go test -cover ./...
go test -race ./...

# Run
go run cmd/api/main.go

# Formatting
gofmt -w .
goimports -w .

# Linting
golangci-lint run

# Dependencies
go mod tidy
go mod download
go mod verify

# Tools
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```


# 8. Version Control
---

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:

- Modify CHANGELOG.md versions

- Update version constants

- Change README.md versions

- Create tags/releases

### Version Protocol

1. **Assess**: "Changes might warrant version update"

2. **Request**: "Should I update to [version]?"

3. **Wait**: Never proceed without "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes

- **Minor (Y+1.0)**: New features

- **Major (X+1.0.0)**: Breaking changes

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**


# 9. Implementation Examples
---

## Code Fix Request

**Structure:**

1. Analyze issue

2. Implement fix

3. Explain improvements

4. Provide integration steps

## Project Planning

**Structure:**

1. Break down components

2. Recommend architecture

3. Create subtask breakdown

4. Provide implementation guidance


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] Compiles without errors

- [ ] Follows Go conventions

- [ ] godoc comments present

- [ ] Proper error handling

- [ ] No golangci-lint warnings

- [ ] Tests included

- [ ] Context properly used

- [ ] Concurrent code safe

- [ ] Performance considered

- [ ] Security checked

## Before Delivering Project
- [ ] Standard Go structure

- [ ] go.mod configured

- [ ] Makefile present

- [ ] All config files

- [ ] Documentation complete

- [ ] Tests passing

---
