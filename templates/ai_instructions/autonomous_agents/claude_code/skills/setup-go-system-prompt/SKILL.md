---
name: setup-go-system-prompt
description: Configure comprehensive Go development system prompt for Claude Code with idiomatic Go practices, standards, and workflows
version: 1.0.0
author: Benjamin Dourthe
language: Go
category: Configuration
priority: HIGH
tags: [go, golang, setup, system-prompt, configuration, standards, idiomatic]
---

# Setup Go System Prompt

Configure Claude Code with comprehensive Go development standards, idiomatic Go practices, and workflows optimized for production-quality Go code generation.

## When to Use This Skill

Use this skill when you need to:

- Set up a new Go project with Claude Code

- Configure Claude Code for Go development (Go 1.21+)

- Apply comprehensive Go development standards and idioms

- Establish consistent coding practices across Go projects

- Optimize Claude Code for Go-specific workflows (goroutines, channels, interfaces)

## What This Skill Does

This skill helps you configure Claude Code with:

1. **Go Development Standards**

   - Idiomatic Go code patterns and conventions

   - gofmt and goimports formatting

   - Error handling best practices (return errors, not panic)

   - Naming conventions (PascalCase exports, camelCase unexported)

2. **Project Architecture Guidelines**

   - Standard project structure (cmd/, internal/, pkg/)

   - go.mod and go.sum management

   - Configuration patterns (YAML, environment variables)

   - Documentation structure (README, CHANGELOG, godoc)

3. **Concurrency Patterns**

   - Goroutines and channel usage

   - Worker pool patterns

   - Context for cancellation and timeouts

   - sync package primitives (Mutex, WaitGroup, Once)

4. **Testing Framework**

   - Go testing package patterns

   - Table-driven tests

   - testify/assert for assertions

   - Benchmark and example tests

5. **Code Quality Standards**

   - Interface design (small, focused interfaces)

   - Error wrapping with fmt.Errorf and %w

   - HTTP handler patterns (Gin framework)

   - Repository and service layer patterns

6. **Development Tools**

   - go build, go test, go run commands

   - golangci-lint for comprehensive linting

   - gofmt and goimports for formatting

   - go vet for static analysis

   - go mod tidy for dependency management

## Prerequisites

- Claude Code installed and configured

- Go 1.21+ installed

- Basic understanding of Go development

- Project directory created (or ready to create new project)

## Instructions

### Step 1: Choose System Prompt Version

Decide between two versions based on your needs:

**Comprehensive Version (~40k tokens)**

- Best for: Enterprise microservices, production APIs, complex Go applications

- Features: Complete architectural guidance, extensive concurrency patterns, detailed error handling

- Token count: ~40,000 tokens

- File: `agent_prompts/autonomous_agents/claude_code/go/CLAUDE_comprehensive_40k.md`

- Includes: Full HTTP handler patterns, repository layer, middleware, database integration

**Condensed Version (~20k tokens)**

- Best for: CLI tools, quick utilities, smaller Go services, prototyping

- Features: Essential Go idioms, core best practices, streamlined workflow

- Token count: ~20,000 tokens

- File: `agent_prompts/autonomous_agents/claude_code/go/CLAUDE_condensed_20k.md`

- Includes: Core patterns, essential standards, rapid development focus

### Step 2: Configure Claude Code

There are two methods to configure Claude Code with the Go system prompt:

#### Method A: Project-Level CLAUDE.md (Recommended)

1. Navigate to your Go project root directory

2. Copy the chosen system prompt file to `CLAUDE.md`:
   ```bash
   # For comprehensive version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/go/CLAUDE_comprehensive_40k.md ./CLAUDE.md

   # For condensed version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/go/CLAUDE_condensed_20k.md ./CLAUDE.md
   ```
3. Claude Code will automatically detect and load this file

#### Method B: Session-Based Configuration

Start Claude Code with the system prompt:
```bash
# For comprehensive version
claude --system-prompt ./path/to/CLAUDE_comprehensive_40k.md

# For condensed version
claude --system-prompt ./path/to/CLAUDE_condensed_20k.md
```

### Step 3: Verify Configuration

Test that the system prompt is active by asking Claude Code to:

1. **Create a simple Go function** and observe if it follows Go idioms:
   ```
   "Create a function that processes user data with proper error handling"
   ```

   Expected behavior:

   - Returns error instead of panicking

   - Uses error wrapping with fmt.Errorf

   - Proper naming conventions (PascalCase for exported)

   - Includes godoc comments

   - No blank lines inside functions

2. **Request project structure** and verify it matches Go standards:
   ```
   "Show me the recommended project structure for a Go microservice API"
   ```

   Expected behavior:

   - Includes cmd/, internal/, pkg/ directories

   - Shows go.mod and Makefile

   - Includes config/ for configuration

   - Shows handler/, service/, repository/ layers

   - Includes CHANGELOG.md, README.md

3. **Ask about concurrency** and confirm it knows Go patterns:
   ```
   "How should I implement concurrent processing of user records?"
   ```

   Expected behavior:

   - Mentions goroutines and channels

   - Discusses worker pool pattern

   - Explains context for cancellation

   - Shows proper channel closing with defer

   - Discusses sync.WaitGroup usage

4. **Request testing patterns** and verify Go testing knowledge:
   ```
   "How should I structure tests for this service?"
   ```

   Expected behavior:

   - Mentions table-driven tests

   - Describes _test.go file naming

   - Explains testify/assert usage

   - Shows TestMain for setup/teardown

   - Discusses test coverage with go test -cover

### Step 4: Initialize Go Module (If New Project)

If starting a new project, verify Claude Code guides you correctly:

```
"Set up a new Go microservice project for user management"
```

Expected behavior:

1. Guides you to run `go mod init <module-path>`

2. Creates standard directory structure

3. Creates main.go in cmd/api/

4. Creates Makefile with build, test, run targets

5. Creates .gitignore with Go-specific entries

6. Sets up CHANGELOG.md starting at version 0.1.0

### Step 5: Customize for Your Organization (Optional)

If you need to add organization-specific Go standards:

1. Open the CLAUDE.md file in your project

2. Add a new section at the end:
   ```markdown
   # Organization-Specific Go Standards

   ## Additional Requirements
   - [Your custom module path prefix]

   - [Internal package guidelines]

   - [Deployment patterns]

   - [Monitoring/logging standards]
   ```
3. Save and restart Claude Code session

### Step 6: Commit to Version Control

Add the CLAUDE.md to your repository so team members have consistent configuration:

```bash
git add CLAUDE.md
git commit -m "Add Claude Code Go system prompt configuration"
git push
```

## Key Features of the Go System Prompt

### 1. Idiomatic Go Code Patterns
Automatically follows Go conventions:

- **Exported vs unexported**: PascalCase for exported, camelCase for internal

- **Error handling**: Always return errors, never panic in library code

- **Error wrapping**: Use fmt.Errorf with %w for error chains

- **Interface design**: Small, focused interfaces (Reader, Writer patterns)

- **Constructor pattern**: NewXxx functions that return pointers

### 2. Project Structure
Standard Go project layout:
```
project/
├── cmd/api/main.go          # Entry point
├── internal/                # Private application code
│   ├── handler/             # HTTP handlers
│   ├── service/             # Business logic
│   ├── repository/          # Data access
│   └── model/               # Domain models
├── pkg/                     # Public libraries
├── config/                  # Configuration
├── go.mod                   # Module definition
└── Makefile                 # Build automation
```

### 3. Concurrency Patterns
Proper use of Go's concurrency primitives:

- **Goroutines**: Lightweight concurrent execution

- **Channels**: Communication between goroutines

- **Select**: Multiplexing channel operations

- **Context**: Cancellation and timeout propagation

- **sync package**: Mutex, WaitGroup, Once patterns

- **Worker pools**: Controlled concurrent processing

### 4. Error Handling
Go-idiomatic error handling:

- Return errors, don't panic (except for programmer errors)

- Custom error types implementing error interface

- Error wrapping with fmt.Errorf("context: %w", err)

- errors.Is and errors.As for error checking

- Sentinel errors for common cases

### 5. Testing Patterns
Go testing best practices:

- Table-driven tests for multiple scenarios

- Subtests with t.Run for organization

- testify/assert for readable assertions

- Mock interfaces for dependencies

- Benchmark tests for performance

- Example tests for documentation

### 6. HTTP Handler Patterns (Gin)
Standard handler structure:

- Constructor injection of dependencies

- Context propagation from request

- Proper HTTP status codes

- JSON response formatting

- Error logging with structured logging (zap)

- Validation and request binding

### 7. Code Quality Tools
Integration with Go ecosystem:

- **gofmt**: Standard code formatting

- **goimports**: Import organization and management

- **go vet**: Static analysis for common mistakes

- **golangci-lint**: Comprehensive linter suite

- **go test -cover**: Code coverage analysis

- **go mod tidy**: Dependency cleanup

## Common Configuration Issues

### Issue: System Prompt Not Loading
**Solution**: Verify CLAUDE.md is in the project root directory and restart Claude Code session

### Issue: Token Limit Warnings
**Solution**: Switch from comprehensive (~40k) to condensed (~20k) version

### Issue: Go Module Path Confusion
**Solution**: Explicitly state your module path (e.g., "Use module path github.com/company/project")

### Issue: Standards Not Being Followed
**Solution**: Explicitly reference the standard in your request:
```
"Following the error handling standard in CLAUDE.md, add proper error wrapping to this function"
```

### Issue: Need Different Standards for Subproject
**Solution**: Create a project-specific CLAUDE.md in the subproject directory with overrides

## Success Criteria

After completing this skill, you should have:

- [ ] Claude Code configured with Go system prompt (CLAUDE.md in project root)

- [ ] Verified configuration by testing function generation with error handling

- [ ] Confirmed project structure knowledge (cmd/, internal/, pkg/)

- [ ] Validated concurrency pattern understanding (goroutines, channels, context)

- [ ] Confirmed testing framework knowledge (table-driven tests, testify)

- [ ] Verified HTTP handler pattern knowledge (Gin framework)

- [ ] Optionally customized for organization-specific Go standards

- [ ] Committed CLAUDE.md to version control for team consistency

## Go Version Compatibility

This system prompt is optimized for:

- **Go 1.21+**: Primary target with latest features

- **Go 1.22**: Full support for enhanced routing, range over functions

- **Backwards compatible**: Works with Go 1.18+ (generics support)

Key features used:

- Error wrapping with %w (Go 1.13+)

- Embedded interfaces (Go 1.14+)

- Type parameters/generics (Go 1.18+)

- Context-aware HTTP handlers (all versions)

## Related Skills

- `init-go-project`: Initialize new Go project following system prompt standards

- `setup-go-testing`: Establish testing framework with table-driven tests

- `go-code-review`: Review Go code quality against configured standards

- `generate-go-interfaces`: Generate idiomatic Go interfaces

- `go-concurrency-patterns`: Implement goroutines and channels correctly

## Additional Resources

- [Effective Go](https://go.dev/doc/effective_go) - Official Go best practices

- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments) - Common review feedback

- [Go Proverbs](https://go-proverbs.github.io/) - Simple programming values

- [Uber Go Style Guide](https://github.com/uber-go/guide/blob/master/style.md) - Production Go style guide

- [Standard Go Project Layout](https://github.com/golang-standards/project-layout) - Project structure reference

- [testify Documentation](https://github.com/stretchr/testify) - Testing assertions

- [Gin Web Framework](https://gin-gonic.com/docs/) - HTTP framework guide

- [golangci-lint](https://golangci-lint.run/) - Comprehensive linter

## Go-Specific Best Practices Enforced

### 1. Error Handling
```go
// ✅ Return errors
func GetUser(id int) (*User, error) {
    if id <= 0 {
        return nil, fmt.Errorf("invalid ID: %d", id)
    }
    return user, nil
}

// ✅ Error wrapping
if err != nil {
    return fmt.Errorf("processing user: %w", err)
}

// ❌ Avoid panic (except programmer errors)
if err != nil {
    panic(err) // Bad practice
}
```

### 2. Interface Design
```go
// ✅ Small, focused interfaces
type Reader interface {
    Read(p []byte) (n int, err error)
}

// ✅ Accept interfaces, return structs
func NewService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}
```

### 3. Concurrency
```go
// ✅ Use channels for communication
results := make(chan Result)
go func() {
    defer close(results)
    results <- processData()
}()

// ✅ Context for cancellation
func Fetch(ctx context.Context) error {
    select {
    case <-ctx.Done():
        return ctx.Err()
    case result := <-results:
        return nil
    }
}
```

### 4. Testing
```go
// ✅ Table-driven tests
func TestCalculate(t *testing.T) {
    tests := []struct {
        name     string
        input    int
        expected int
    }{
        {"positive", 5, 25},
        {"zero", 0, 0},
        {"negative", -5, 25},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := Calculate(tt.input)
            assert.Equal(t, tt.expected, result)
        })
    }
}
```

### 5. Project Organization
```go
// ✅ Proper layer separation
// cmd/api/main.go - Entry point
// internal/handler/ - HTTP handlers
// internal/service/ - Business logic
// internal/repository/ - Data access
// internal/model/ - Domain models
// pkg/ - Reusable packages
```

## Command Reference

Common Go commands Claude Code will reference:

```bash
# Module management
go mod init github.com/user/project
go mod tidy
go mod download

# Building
go build -o bin/app cmd/api/main.go
go build ./...

# Testing
go test ./...
go test -v ./...
go test -cover ./...
go test -bench=. ./...

# Code quality
gofmt -w .
goimports -w .
go vet ./...
golangci-lint run

# Running
go run cmd/api/main.go

# Dependencies
go get github.com/gin-gonic/gin@v1.10.0
go get -u ./...
go list -m all
```

## Troubleshooting

### Claude Code suggests non-idiomatic patterns
**Solution**: Remind Claude Code: "Follow Go idioms from CLAUDE.md, particularly error handling"

### Generated code has blank lines in functions
**Solution**: "Remove blank lines inside function bodies per Go standards"

### Panic used instead of error returns
**Solution**: "Convert panics to error returns following idiomatic Go error handling"

### Interfaces too large
**Solution**: "Break this interface into smaller, focused interfaces per Go best practices"

### Missing context propagation
**Solution**: "Add context.Context parameter following the context standard"

## Advanced Go Patterns Covered

### Dependency Injection Pattern
The system prompt teaches proper dependency injection:

```go
// Constructor injection
type UserService struct {
    repo   UserRepository
    cache  CacheService
    logger *zap.Logger
}

func NewUserService(repo UserRepository, cache CacheService, logger *zap.Logger) *UserService {
    return &UserService{
        repo:   repo,
        cache:  cache,
        logger: logger,
    }
}
```

**Benefits**:

- Testability through interface mocking

- Loose coupling between components

- Clear dependencies at construction time

- No hidden global state

### Repository Pattern
Standard data access layer:

```go
type UserRepository interface {
    GetByID(ctx context.Context, id int) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id int) error
    List(ctx context.Context, filter Filter) ([]*User, error)
}

type postgresUserRepository struct {
    db *sql.DB
}

func NewPostgresUserRepository(db *sql.DB) UserRepository {
    return &postgresUserRepository{db: db}
}
```

### Service Layer Pattern
Business logic separation:

```go
type UserService struct {
    repo   UserRepository
    logger *zap.Logger
}

func (s *UserService) CreateUser(ctx context.Context, req CreateUserRequest) (*User, error) {
    // Validation
    if err := req.Validate(); err != nil {
        return nil, fmt.Errorf("invalid request: %w", err)
    }

    // Business logic
    user := &User{
        Name:  req.Name,
        Email: req.Email,
    }

    // Repository call
    if err := s.repo.Create(ctx, user); err != nil {
        s.logger.Error("failed to create user", zap.Error(err))
        return nil, fmt.Errorf("creating user: %w", err)
    }

    return user, nil
}
```

### Middleware Pattern
HTTP middleware for cross-cutting concerns:

```go
// Logging middleware
func LoggingMiddleware(logger *zap.Logger) gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()
        path := c.Request.URL.Path

        c.Next()

        logger.Info("request completed",
            zap.String("method", c.Request.Method),
            zap.String("path", path),
            zap.Int("status", c.Writer.Status()),
            zap.Duration("latency", time.Since(start)),
        )
    }
}

// Authentication middleware
func AuthMiddleware(authService AuthService) gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(401, gin.H{"error": "unauthorized"})
            return
        }

        user, err := authService.ValidateToken(c.Request.Context(), token)
        if err != nil {
            c.AbortWithStatusJSON(401, gin.H{"error": "invalid token"})
            return
        }

        c.Set("user", user)
        c.Next()
    }
}
```

### Configuration Management
Environment-based configuration:

```go
type Config struct {
    Server   ServerConfig
    Database DatabaseConfig
    Redis    RedisConfig
    Logger   LoggerConfig
}

type ServerConfig struct {
    Port         int           `yaml:"port" env:"SERVER_PORT" env-default:"8080"`
    ReadTimeout  time.Duration `yaml:"read_timeout" env:"SERVER_READ_TIMEOUT" env-default:"10s"`
    WriteTimeout time.Duration `yaml:"write_timeout" env:"SERVER_WRITE_TIMEOUT" env-default:"10s"`
}

func LoadConfig(path string) (*Config, error) {
    var cfg Config

    // Read YAML file
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("reading config file: %w", err)
    }

    // Parse YAML
    if err := yaml.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parsing config: %w", err)
    }

    // Override with environment variables
    if err := env.Parse(&cfg); err != nil {
        return nil, fmt.Errorf("parsing environment: %w", err)
    }

    return &cfg, nil
}
```

## Database Integration Patterns

### Connection Pool Management
```go
func NewPostgresDB(cfg DatabaseConfig) (*sql.DB, error) {
    dsn := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s",
        cfg.Host, cfg.Port, cfg.User, cfg.Password, cfg.DBName, cfg.SSLMode)

    db, err := sql.Open("postgres", dsn)
    if err != nil {
        return nil, fmt.Errorf("opening database: %w", err)
    }

    // Connection pool settings
    db.SetMaxOpenConns(cfg.MaxOpenConns)
    db.SetMaxIdleConns(cfg.MaxIdleConns)
    db.SetConnMaxLifetime(cfg.ConnMaxLifetime)

    // Verify connection
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    if err := db.PingContext(ctx); err != nil {
        return nil, fmt.Errorf("pinging database: %w", err)
    }

    return db, nil
}
```

### Transaction Management
```go
func (r *postgresUserRepository) CreateWithAddress(ctx context.Context, user *User, address *Address) error {
    tx, err := r.db.BeginTx(ctx, nil)
    if err != nil {
        return fmt.Errorf("beginning transaction: %w", err)
    }
    defer tx.Rollback()

    // Insert user
    var userID int
    err = tx.QueryRowContext(ctx,
        "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING id",
        user.Name, user.Email,
    ).Scan(&userID)
    if err != nil {
        return fmt.Errorf("inserting user: %w", err)
    }

    // Insert address
    _, err = tx.ExecContext(ctx,
        "INSERT INTO addresses (user_id, street, city) VALUES ($1, $2, $3)",
        userID, address.Street, address.City,
    )
    if err != nil {
        return fmt.Errorf("inserting address: %w", err)
    }

    if err := tx.Commit(); err != nil {
        return fmt.Errorf("committing transaction: %w", err)
    }

    user.ID = userID
    return nil
}
```

## Performance Optimization Patterns

### Caching Strategy
```go
type CachedUserRepository struct {
    repo  UserRepository
    cache *redis.Client
    ttl   time.Duration
}

func (r *CachedUserRepository) GetByID(ctx context.Context, id int) (*User, error) {
    // Try cache first
    cacheKey := fmt.Sprintf("user:%d", id)
    cached, err := r.cache.Get(ctx, cacheKey).Result()
    if err == nil {
        var user User
        if err := json.Unmarshal([]byte(cached), &user); err == nil {
            return &user, nil
        }
    }

    // Cache miss - fetch from repository
    user, err := r.repo.GetByID(ctx, id)
    if err != nil {
        return nil, err
    }

    // Store in cache
    data, _ := json.Marshal(user)
    r.cache.Set(ctx, cacheKey, data, r.ttl)

    return user, nil
}
```

### Connection Pooling with sync.Pool
```go
var bufferPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func ProcessData(data []byte) ([]byte, error) {
    buf := bufferPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufferPool.Put(buf)
    }()

    // Process data using pooled buffer
    buf.Write(data)
    // ... processing logic ...

    return buf.Bytes(), nil
}
```

### Rate Limiting
```go
type RateLimiter struct {
    limiter *rate.Limiter
}

func NewRateLimiter(requestsPerSecond int) *RateLimiter {
    return &RateLimiter{
        limiter: rate.NewLimiter(rate.Limit(requestsPerSecond), requestsPerSecond),
    }
}

func (rl *RateLimiter) Middleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        if !rl.limiter.Allow() {
            c.AbortWithStatusJSON(429, gin.H{"error": "rate limit exceeded"})
            return
        }
        c.Next()
    }
}
```

## Graceful Shutdown Pattern

```go
func main() {
    // Create server
    srv := &http.Server{
        Addr:    ":8080",
        Handler: setupRouter(),
    }

    // Start server in goroutine
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("listen: %s\n", err)
        }
    }()

    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    log.Println("Shutting down server...")

    // Graceful shutdown with timeout
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Server forced to shutdown:", err)
    }

    log.Println("Server exiting")
}
```

## Validation Patterns

### Struct Validation
```go
type CreateUserRequest struct {
    Name  string `json:"name" binding:"required,min=2,max=100"`
    Email string `json:"email" binding:"required,email"`
    Age   int    `json:"age" binding:"required,min=18,max=120"`
}

func (r *CreateUserRequest) Validate() error {
    if r.Name == "" {
        return fmt.Errorf("name is required")
    }
    if len(r.Name) < 2 || len(r.Name) > 100 {
        return fmt.Errorf("name must be between 2 and 100 characters")
    }
    if !isValidEmail(r.Email) {
        return fmt.Errorf("invalid email format")
    }
    if r.Age < 18 || r.Age > 120 {
        return fmt.Errorf("age must be between 18 and 120")
    }
    return nil
}
```

## Logging Best Practices

### Structured Logging with Zap
```go
func setupLogger() (*zap.Logger, error) {
    cfg := zap.NewProductionConfig()
    cfg.OutputPaths = []string{"stdout", "logs/app.log"}
    cfg.EncoderConfig.TimeKey = "timestamp"
    cfg.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

    logger, err := cfg.Build()
    if err != nil {
        return nil, fmt.Errorf("building logger: %w", err)
    }

    return logger, nil
}

// Usage in handlers
func (h *UserHandler) GetUser(c *gin.Context) {
    id, _ := strconv.Atoi(c.Param("id"))

    h.logger.Info("fetching user",
        zap.Int("user_id", id),
        zap.String("request_id", c.GetString("request_id")),
    )

    user, err := h.service.GetByID(c.Request.Context(), id)
    if err != nil {
        h.logger.Error("failed to get user",
            zap.Error(err),
            zap.Int("user_id", id),
        )
        c.JSON(500, gin.H{"error": "internal server error"})
        return
    }

    c.JSON(200, user)
}
```

## Security Best Practices

### Input Sanitization
```go
func SanitizeString(input string) string {
    // Remove null bytes
    input = strings.ReplaceAll(input, "\x00", "")

    // Trim whitespace
    input = strings.TrimSpace(input)

    // Limit length
    if len(input) > 1000 {
        input = input[:1000]
    }

    return input
}
```

### SQL Injection Prevention
```go
// ✅ Use parameterized queries
func (r *postgresUserRepository) GetByEmail(ctx context.Context, email string) (*User, error) {
    var user User
    err := r.db.QueryRowContext(ctx,
        "SELECT id, name, email FROM users WHERE email = $1",
        email,
    ).Scan(&user.ID, &user.Name, &user.Email)

    if err == sql.ErrNoRows {
        return nil, ErrNotFound
    }
    if err != nil {
        return nil, fmt.Errorf("querying user: %w", err)
    }

    return &user, nil
}

// ❌ Never concatenate user input
// query := fmt.Sprintf("SELECT * FROM users WHERE email = '%s'", email) // DANGEROUS
```

### Authentication with JWT
```go
type AuthService struct {
    secretKey []byte
}

func (s *AuthService) GenerateToken(userID int) (string, error) {
    claims := jwt.MapClaims{
        "user_id": userID,
        "exp":     time.Now().Add(24 * time.Hour).Unix(),
        "iat":     time.Now().Unix(),
    }

    token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return token.SignedString(s.secretKey)
}

func (s *AuthService) ValidateToken(tokenString string) (int, error) {
    token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
        if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
            return nil, fmt.Errorf("unexpected signing method: %v", token.Header["alg"])
        }
        return s.secretKey, nil
    })

    if err != nil {
        return 0, fmt.Errorf("parsing token: %w", err)
    }

    if claims, ok := token.Claims.(jwt.MapClaims); ok && token.Valid {
        userID := int(claims["user_id"].(float64))
        return userID, nil
    }

    return 0, fmt.Errorf("invalid token")
}
```

## Comparison with Python System Prompt

Key differences Claude Code will understand:

| Aspect | Python | Go |
|--------|--------|-----|
| Error Handling | Exceptions (try/except) | Return values (error interface) |
| Concurrency | asyncio, threads | Goroutines, channels |
| Package Management | pip, requirements.txt | go mod, go.sum |
| Testing | pytest, unittest | testing package, testify |
| Formatting | Black, 88 chars | gofmt, automatic |
| Type System | Type hints (optional) | Static typing (required) |
| Project Layout | src/, tests/ | cmd/, internal/, pkg/ |
| Dependency Injection | Often implicit | Explicit constructors |

## Migration Guide

For teams transitioning from Python to Go with Claude Code:

### From Python Classes to Go Structs
```python
# Python
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_user(self, user_id: int) -> User:
        return self.repo.get_by_id(user_id)
```

```go
// Go equivalent
type UserService struct {
    repo UserRepository
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

func (s *UserService) GetUser(ctx context.Context, userID int) (*User, error) {
    return s.repo.GetByID(ctx, userID)
}
```

### From Python async/await to Go goroutines
```python
# Python
async def fetch_users(user_ids: List[int]) -> List[User]:
    tasks = [fetch_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)
```

```go
// Go equivalent
func FetchUsers(ctx context.Context, userIDs []int) ([]*User, error) {
    var wg sync.WaitGroup
    users := make([]*User, len(userIDs))
    errs := make([]error, len(userIDs))

    for i, uid := range userIDs {
        wg.Add(1)
        go func(idx int, userID int) {
            defer wg.Done()
            user, err := fetchUser(ctx, userID)
            users[idx] = user
            errs[idx] = err
        }(i, uid)
    }

    wg.Wait()

    for _, err := range errs {
        if err != nil {
            return nil, err
        }
    }

    return users, nil
}
```

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5
**Go Version**: 1.21+
**Author**: Benjamin Dourthe (benjamin@adonamed.com)
