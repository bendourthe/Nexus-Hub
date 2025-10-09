# Go API Documentation

## Objective
Create complete, accurate API documentation for Go-based REST/gRPC APIs that enables developers to understand and integrate successfully.

## Implementation Checklist

### Endpoint Documentation
- [ ] All endpoints with HTTP methods documented
- [ ] Request/response structs with JSON tags
- [ ] Path, query, body parameters specified
- [ ] Status codes and meanings explained

### Authentication
- [ ] Authentication methods documented
- [ ] JWT/API key handling explained
- [ ] Middleware implementation shown

### Request/Response
- [ ] Struct definitions with validation tags
- [ ] JSON encoding/decoding examples
- [ ] Error response structures

### Error Handling
- [ ] Error types documented
- [ ] HTTP status mappings shown
- [ ] Common error scenarios covered

### Examples
- [ ] net/http client examples
- [ ] Third-party client examples (resty, etc.)
- [ ] Complete integration examples

## Prompt Template

~~~markdown
# Go API Documentation Request

## Phase 1: API Server Implementation

### Gin Framework API
```go
package main

import (
    "github.com/gin-gonic/gin"
    "net/http"
)

type CreateUserRequest struct {
    Email    string `json:"email" binding:"required,email"`
    Name     string `json:"name" binding:"required"`
    Password string `json:"password" binding:"required,min=8"`
}

type UserResponse struct {
    ID        int64  `json:"id"`
    Email     string `json:"email"`
    Name      string `json:"name"`
    CreatedAt string `json:"created_at"`
}

type ErrorResponse struct {
    Error   string      `json:"error"`
    Message string      `json:"message"`
    Details interface{} `json:"details,omitempty"`
}

func main() {
    r := gin.Default()

    api := r.Group("/api/v1")
    {
        users := api.Group("/users")
        {
            users.GET("", listUsers)
            users.POST("", createUser)
            users.GET("/:id", getUser)
            users.PUT("/:id", updateUser)
            users.DELETE("/:id", deleteUser)
        }
    }

    r.Run(":8080")
}

func listUsers(c *gin.Context) {
    page := c.DefaultQuery("page", "1")
    limit := c.DefaultQuery("limit", "20")

    // Business logic here
    users := []UserResponse{
        {ID: 1, Email: "user@example.com", Name: "User"},
    }

    c.JSON(http.StatusOK, gin.H{
        "data": users,
        "pagination": gin.H{
            "page":  page,
            "limit": limit,
        },
    })
}

func createUser(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, ErrorResponse{
            Error:   "validation_error",
            Message: "Invalid request data",
            Details: err.Error(),
        })
        return
    }

    // Business logic
    user := UserResponse{
        ID:    1,
        Email: req.Email,
        Name:  req.Name,
    }

    c.JSON(http.StatusCreated, user)
}
```

## Phase 2: Go Client Examples

### net/http Client
```go
package main

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "time"
)

type APIClient struct {
    baseURL    string
    apiKey     string
    httpClient *http.Client
}

func NewAPIClient(baseURL, apiKey string) *APIClient {
    return &APIClient{
        baseURL: baseURL,
        apiKey:  apiKey,
        httpClient: &http.Client{
            Timeout: 30 * time.Second,
        },
    }
}

func (c *APIClient) ListUsers(ctx context.Context, page, limit int) ([]UserResponse, error) {
    url := fmt.Sprintf("%s/api/v1/users?page=%d&limit=%d", c.baseURL, page, limit)

    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, fmt.Errorf("create request: %w", err)
    }

    req.Header.Set("Authorization", "Bearer "+c.apiKey)
    req.Header.Set("Content-Type", "application/json")

    resp, err := c.httpClient.Do(req)
    if err != nil {
        return nil, fmt.Errorf("http request: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return nil, c.handleError(resp)
    }

    var result struct {
        Data []UserResponse `json:"data"`
    }
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, fmt.Errorf("decode response: %w", err)
    }

    return result.Data, nil
}

func (c *APIClient) CreateUser(ctx context.Context, req CreateUserRequest) (*UserResponse, error) {
    body, err := json.Marshal(req)
    if err != nil {
        return nil, fmt.Errorf("marshal request: %w", err)
    }

    httpReq, err := http.NewRequestWithContext(ctx, "POST",
        c.baseURL+"/api/v1/users", bytes.NewReader(body))
    if err != nil {
        return nil, fmt.Errorf("create request: %w", err)
    }

    httpReq.Header.Set("Authorization", "Bearer "+c.apiKey)
    httpReq.Header.Set("Content-Type", "application/json")

    resp, err := c.httpClient.Do(httpReq)
    if err != nil {
        return nil, fmt.Errorf("http request: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusCreated {
        return nil, c.handleError(resp)
    }

    var user UserResponse
    if err := json.NewDecoder(resp.Body).Decode(&user); err != nil {
        return nil, fmt.Errorf("decode response: %w", err)
    }

    return &user, nil
}

func (c *APIClient) handleError(resp *http.Response) error {
    body, _ := io.ReadAll(resp.Body)

    var errResp ErrorResponse
    if err := json.Unmarshal(body, &errResp); err != nil {
        return fmt.Errorf("status %d: %s", resp.StatusCode, string(body))
    }

    return fmt.Errorf("API error (%d): %s", resp.StatusCode, errResp.Message)
}
```

### Resty Client
```go
import "github.com/go-resty/resty/v2"

type RestyAPIClient struct {
    client *resty.Client
}

func NewRestyAPIClient(baseURL, apiKey string) *RestyAPIClient {
    client := resty.New()
    client.SetBaseURL(baseURL)
    client.SetHeader("Authorization", "Bearer "+apiKey)
    client.SetTimeout(30 * time.Second)
    client.SetRetryCount(3)
    client.SetRetryWaitTime(1 * time.Second)

    return &RestyAPIClient{client: client}
}

func (c *RestyAPIClient) ListUsers(page, limit int) ([]UserResponse, error) {
    var result struct {
        Data []UserResponse `json:"data"`
    }

    resp, err := c.client.R().
        SetQueryParams(map[string]string{
            "page":  fmt.Sprintf("%d", page),
            "limit": fmt.Sprintf("%d", limit),
        }).
        SetResult(&result).
        SetError(&ErrorResponse{}).
        Get("/api/v1/users")

    if err != nil {
        return nil, err
    }

    if resp.IsError() {
        errResp := resp.Error().(*ErrorResponse)
        return nil, fmt.Errorf("API error: %s", errResp.Message)
    }

    return result.Data, nil
}

func (c *RestyAPIClient) CreateUser(req CreateUserRequest) (*UserResponse, error) {
    var user UserResponse
    var errResp ErrorResponse

    resp, err := c.client.R().
        SetBody(req).
        SetResult(&user).
        SetError(&errResp).
        Post("/api/v1/users")

    if err != nil {
        return nil, err
    }

    if resp.IsError() {
        return nil, fmt.Errorf("API error: %s", errResp.Message)
    }

    return &user, nil
}
```

## Phase 3: Authentication Middleware

```go
func AuthMiddleware(apiKey string) gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.JSON(http.StatusUnauthorized, ErrorResponse{
                Error:   "unauthorized",
                Message: "Missing authorization header",
            })
            c.Abort()
            return
        }

        // Validate token (simplified)
        if token != "Bearer "+apiKey {
            c.JSON(http.StatusUnauthorized, ErrorResponse{
                Error:   "unauthorized",
                Message: "Invalid token",
            })
            c.Abort()
            return
        }

        c.Next()
    }
}

// Usage
api := r.Group("/api/v1", AuthMiddleware(apiKey))
```

## Phase 4: Error Handling

```go
type AppError struct {
    Code       string      `json:"code"`
    Message    string      `json:"message"`
    StatusCode int         `json:"-"`
    Details    interface{} `json:"details,omitempty"`
}

func (e *AppError) Error() string {
    return e.Message
}

func NewBadRequestError(message string, details interface{}) *AppError {
    return &AppError{
        Code:       "bad_request",
        Message:    message,
        StatusCode: http.StatusBadRequest,
        Details:    details,
    }
}

func NewNotFoundError(message string) *AppError {
    return &AppError{
        Code:       "not_found",
        Message:    message,
        StatusCode: http.StatusNotFound,
    }
}

// Error handler middleware
func ErrorHandler() gin.HandlerFunc {
    return func(c *gin.Context) {
        c.Next()

        if len(c.Errors) > 0 {
            err := c.Errors.Last().Err

            var appErr *AppError
            if errors.As(err, &appErr) {
                c.JSON(appErr.StatusCode, appErr)
                return
            }

            c.JSON(http.StatusInternalServerError, ErrorResponse{
                Error:   "internal_error",
                Message: "An unexpected error occurred",
            })
        }
    }
}
```

## Phase 5: Testing

```go
func TestCreateUser(t *testing.T) {
    gin.SetMode(gin.TestMode)
    router := setupRouter()

    req := CreateUserRequest{
        Email:    "test@example.com",
        Name:     "Test User",
        Password: "password123",
    }
    body, _ := json.Marshal(req)

    w := httptest.NewRecorder()
    httpReq, _ := http.NewRequest("POST", "/api/v1/users", bytes.NewReader(body))
    httpReq.Header.Set("Content-Type", "application/json")

    router.ServeHTTP(w, httpReq)

    assert.Equal(t, http.StatusCreated, w.Code)

    var user UserResponse
    err := json.Unmarshal(w.Body.Bytes(), &user)
    assert.NoError(t, err)
    assert.Equal(t, req.Email, user.Email)
}
```
```

---

## Best Practices

1. **Use Standard Library**: net/http is robust, frameworks optional
2. **Context**: Always use context.Context for cancellation
3. **Error Handling**: Return errors, don't panic
4. **JSON Tags**: Use json:"name" tags consistently
5. **Validation**: Use validator package for struct validation
6. **Testing**: Use httptest for API testing
7. **Documentation**: Use godoc comments
8. **Middleware**: Use middleware for cross-cutting concerns

---
~~~

## Output Format Specifications

The API documentation should:
- Show idiomatic Go patterns
- Include context-aware examples
- Demonstrate proper error handling
- Show both standard library and framework approaches
- Include comprehensive testing examples
- Target Go developers
