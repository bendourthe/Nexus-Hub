---
template_id: go_technical_docs
template_name: Technical Docs - Go
version: 1.0.0
last_updated: 2025-12-03
language: Go
category: documentation
phase: technical_docs
difficulty: beginner
estimated_time_hours: 4-6
prerequisites: []
tools:
  - go test (1.23+)
  - testify
tags:
  - documentation
  - documentation
  - go
---
# Go Technical Documentation

## Objective
Create comprehensive technical documentation that captures architecture decisions, system design, data flows, integration points, and development workflows for developers and technical stakeholders.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/technical_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/technical_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Architecture Documentation

- [ ] System architecture overview with diagrams

- [ ] Component responsibilities clearly defined

- [ ] Technology stack documented with rationale

- [ ] Architectural patterns explained

- [ ] Scalability and performance considerations

- [ ] Security architecture documented

### Design Decisions

- [ ] Key technical decisions documented with rationale

- [ ] Alternative approaches considered

- [ ] Trade-offs and constraints explained

- [ ] Decision timeline and context

- [ ] Impact assessment of decisions

### Module Organization

- [ ] Package structure explained

- [ ] Module dependencies mapped

- [ ] Exported vs unexported interfaces defined

- [ ] Import structure documented

- [ ] Code organization principles

### Data Flow

- [ ] Data flow diagrams created

- [ ] Goroutine patterns documented

- [ ] Channel usage explained

- [ ] Data transformation pipelines

- [ ] Error handling patterns

### Integration Points

- [ ] External API integrations documented

- [ ] Database schemas and migrations

- [ ] Message queue/event systems

- [ ] Third-party service dependencies

- [ ] Authentication/authorization flows

### Development Workflow

- [ ] Development environment setup

- [ ] Build and deployment process

- [ ] Testing strategy

- [ ] CI/CD pipeline documentation

- [ ] Release process

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Technical Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/technical_docs"
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

Please create comprehensive technical documentation for this Go project following this protocol:

## Phase 1: Architecture Analysis

```markdown
# System Architecture

## Overview

[Project Name] is built as a [service/library/CLI tool] using Go [version] that [high-level purpose].

## Architecture Style

- **Pattern**: [Layered/Hexagonal/Clean Architecture/Microservices]

- **Framework**: [Gin/Echo/Chi/Standard Library/gRPC]

- **Deployment**: [Binary/Container/Kubernetes/Lambda]

- **Concurrency**: [Goroutines pattern description]

- **Communication**: [REST/gRPC/Message Queue]

## Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Runtime | Go | 1.21+ | Performance, simplicity, concurrency |
| HTTP Framework | Gin/Echo/Chi | Latest | Fast routing, middleware support |
| Database | PostgreSQL/MongoDB | Latest | [Why chosen] |
| ORM | GORM/sqlx | Latest | Type safety, query builder |
| Testing | Standard testing | Built-in | Native support, table-driven tests |
| API Docs | Swag | Latest | OpenAPI/Swagger generation |

## Package Structure

```
project/
├── cmd/                    # Application entrypoints
│   ├── api/
│   │   └── main.go        # API server main
│   └── worker/
│       └── main.go        # Background worker main
│
├── internal/              # Private application code
│   ├── api/              # API handlers
│   │   ├── handler/
│   │   │   ├── user.go
│   │   │   └── product.go
│   │   ├── middleware/
│   │   │   ├── auth.go
│   │   │   └── logging.go
│   │   └── router.go
│   │
│   ├── service/          # Business logic
│   │   ├── user.go
│   │   ├── product.go
│   │   └── auth.go
│   │
│   ├── repository/       # Data access
│   │   ├── user.go
│   │   ├── product.go
│   │   └── postgres.go
│   │
│   ├── domain/           # Domain models
│   │   ├── user.go
│   │   └── product.go
│   │
│   └── infrastructure/   # External integrations
│       ├── database/
│       ├── cache/
│       └── queue/
│
├── pkg/                  # Public libraries
│   ├── errors/
│   ├── logger/
│   └── validator/
│
├── config/               # Configuration
├── migrations/           # Database migrations
└── scripts/             # Build/deployment scripts
```

## Data Flow Example

```go
// 1. Handler layer
type UserHandler struct {
    userService *service.UserService
    logger      *logger.Logger
}

func (h *UserHandler) CreateUser(c *gin.Context) {
    var req dto.CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    user, err := h.userService.CreateUser(c.Request.Context(), &req)
    if err != nil {
        h.handleError(c, err)
        return
    }

    c.JSON(http.StatusCreated, user)
}

// 2. Service layer
type UserService struct {
    userRepo   repository.UserRepository
    emailQueue queue.EmailQueue
}

func (s *UserService) CreateUser(ctx context.Context, req *dto.CreateUserRequest) (*domain.User, error) {
    // Validate business rules
    exists, err := s.userRepo.ExistsByEmail(ctx, req.Email)
    if err != nil {
        return nil, fmt.Errorf("check email existence: %w", err)
    }
    if exists {
        return nil, errors.NewDuplicateError("email already exists")
    }

    // Create domain entity
    user := &domain.User{
        Email:        req.Email,
        Name:         req.Name,
        PasswordHash: hashPassword(req.Password),
        CreatedAt:    time.Now(),
    }

    // Persist
    if err := s.userRepo.Create(ctx, user); err != nil {
        return nil, fmt.Errorf("create user: %w", err)
    }

    // Async: send welcome email
    go s.emailQueue.SendWelcomeEmail(user.Email)

    return user, nil
}

// 3. Repository layer
type UserRepository interface {
    Create(ctx context.Context, user *domain.User) error
    ExistsByEmail(ctx context.Context, email string) (bool, error)
    FindByID(ctx context.Context, id int64) (*domain.User, error)
}

type userRepository struct {
    db *sql.DB
}

func (r *userRepository) Create(ctx context.Context, user *domain.User) error {
    query := `
        INSERT INTO users (email, name, password_hash, created_at)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    `
    err := r.db.QueryRowContext(ctx, query,
        user.Email, user.Name, user.PasswordHash, user.CreatedAt,
    ).Scan(&user.ID)

    if err != nil {
        return fmt.Errorf("insert user: %w", err)
    }
    return nil
}

// 4. Domain entity
type User struct {
    ID           int64     `json:"id"`
    Email        string    `json:"email"`
    Name         string    `json:"name"`
    PasswordHash string    `json:"-"`
    IsActive     bool      `json:"is_active"`
    CreatedAt    time.Time `json:"created_at"`
    UpdatedAt    *time.Time `json:"updated_at,omitempty"`
}
```

## Concurrency Patterns

```go
// Worker pool pattern
func processJobs(ctx context.Context, jobs <-chan Job, results chan<- Result) {
    const numWorkers = 10
    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    return
                default:
                    result := processJob(job)
                    results <- result
                }
            }
        }()
    }

    wg.Wait()
    close(results)
}

// Context-aware HTTP client
func (c *ExternalAPIClient) GetResource(ctx context.Context, id string) (*Resource, error) {
    req, err := http.NewRequestWithContext(ctx, "GET",
        fmt.Sprintf("%s/resource/%s", c.baseURL, id), nil)
    if err != nil {
        return nil, err
    }

    req.Header.Set("Authorization", "Bearer "+c.apiKey)

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("http request: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("unexpected status: %d", resp.StatusCode)
    }

    var resource Resource
    if err := json.NewDecoder(resp.Body).Decode(&resource); err != nil {
        return nil, fmt.Errorf("decode response: %w", err)
    }

    return &resource, nil
}
```

## Error Handling

```go
// Custom error types
type AppError struct {
    Code    string
    Message string
    Err     error
}

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("%s: %v", e.Message, e.Err)
    }
    return e.Message
}

func (e *AppError) Unwrap() error {
    return e.Err
}

// Error handling middleware
func ErrorHandlerMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()

        if len(c.Errors) > 0 {
            err := c.Errors.Last().Err

            var appErr *AppError
            if errors.As(err, &appErr) {
                c.JSON(http.StatusBadRequest, gin.H{
                    "error": appErr.Code,
                    "message": appErr.Message,
                })
                return
            }

            c.JSON(http.StatusInternalServerError, gin.H{
                "error": "internal_error",
                "message": "An unexpected error occurred",
            })
        }
    }
}
```

## Testing Strategy

```go
// Table-driven test
func TestUserService_CreateUser(t *testing.T) {
    tests := []struct {
        name    string
        req     *dto.CreateUserRequest
        setup   func(*mock.MockUserRepository)
        wantErr bool
    }{
        {
            name: "success",
            req: &dto.CreateUserRequest{
                Email: "test@example.com",
                Name:  "Test User",
            },
            setup: func(m *mock.MockUserRepository) {
                m.EXPECT().ExistsByEmail(gomock.Any(), "test@example.com").Return(false, nil)
                m.EXPECT().Create(gomock.Any(), gomock.Any()).Return(nil)
            },
            wantErr: false,
        },
        {
            name: "duplicate email",
            req: &dto.CreateUserRequest{
                Email: "test@example.com",
            },
            setup: func(m *mock.MockUserRepository) {
                m.EXPECT().ExistsByEmail(gomock.Any(), "test@example.com").Return(true, nil)
            },
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            ctrl := gomock.NewController(t)
            defer ctrl.Finish()

            mockRepo := mock.NewMockUserRepository(ctrl)
            if tt.setup != nil {
                tt.setup(mockRepo)
            }

            svc := service.NewUserService(mockRepo, nil)
            _, err := svc.CreateUser(context.Background(), tt.req)

            if (err != nil) != tt.wantErr {
                t.Errorf("CreateUser() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}

// Integration test
func TestUserHandler_Integration(t *testing.T) {
    // Setup test database
    db := setupTestDB(t)
    defer db.Close()

    // Create server
    router := setupRouter(db)
    server := httptest.NewServer(router)
    defer server.Close()

    // Test request
    req := dto.CreateUserRequest{
        Email: "test@example.com",
        Name:  "Test User",
    }
    body, _ := json.Marshal(req)

    resp, err := http.Post(
        server.URL+"/api/v1/users",
        "application/json",
        bytes.NewReader(body),
    )
    require.NoError(t, err)
    defer resp.Body.Close()

    assert.Equal(t, http.StatusCreated, resp.StatusCode)
}
```

## Development Workflow

```bash
# Setup
go mod download

# Run migrations
migrate -path migrations -database "postgres://..." up

# Run application
go run cmd/api/main.go

# Run tests
go test ./...

# Run tests with coverage
go test -cover ./...

# Run specific test
go test -run TestUserService_CreateUser ./internal/service

# Build
go build -o bin/api cmd/api/main.go

# Run linter
golangci-lint run

# Format code
go fmt ./...
goimports -w .
```

## CI/CD Pipeline

```yaml
# GitHub Actions
name: Go CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Download dependencies
        run: go mod download

      - name: Run tests
        run: go test -v -race -coverprofile=coverage.out ./...

      - name: Run linter
        uses: golangci/golangci-lint-action@v3

      - name: Build
        run: go build -v ./cmd/...
```
```

---

## Best Practices

1. **Follow Go Conventions**
   - Use `gofmt` and `goimports`
   - Follow effective Go guidelines
   - Use `golangci-lint` for linting
   - Package names: short, lowercase, no underscores

2. **Error Handling**
   - Return errors, don't panic
   - Wrap errors with context (`fmt.Errorf` with `%w`)
   - Check all errors
   - Use custom error types when needed

3. **Concurrency**
   - Use channels for communication
   - Always use `context.Context` for cancellation
   - Avoid goroutine leaks
   - Use `sync.WaitGroup` for coordination

4. **Testing**
   - Write table-driven tests
   - Use interfaces for mocking
   - Test edge cases
   - Use `testify` for assertions

5. **Project Structure**
   - Use `internal/` for private code
   - Use `pkg/` for reusable libraries
   - Keep `main.go` in `cmd/`
   - Follow standard Go project layout

---

## Output Format Specifications

The technical documentation should:

- Provide high-level architecture overview

- Document Go-specific patterns (goroutines, channels)

- Map package organization clearly

- Show concurrency and error handling patterns

- Document all external integrations

- Follow Go idioms and best practices

- Target Go developers

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
