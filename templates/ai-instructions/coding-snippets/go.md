## Go Conventions

**Tooling**:
- **Format**: `gofmt` (or `goimports`)
- **Linting**: `golangci-lint` with standard presets
- **Modules**: Go Modules (`go mod`)

**Naming**: `CamelCase` for exported, `camelCase` for unexported. Keep names short and concise.

**Code Patterns**:
- Handle errors explicitly (`if err != nil`); wrap with context (`fmt.Errorf("doing X: %w", err)`)
- `defer` for resource cleanup
- `filepath.Join` for path construction
- `New[Type]` constructor functions (e.g., `NewClient`)
- Small interfaces defined at the consumer side
- `context` for cancellation and timeouts
- Comments start with the function/type name (e.g., `// ServeHTTP handles...`)

**Testing**: Built-in `testing` package with table-driven tests.

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name string
        a, b, want int
    }{
        {"positive", 1, 2, 3},
        {"negative", -1, -1, -2},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            if got := Add(tt.a, tt.b); got != tt.want {
                t.Errorf("Add() = %v, want %v", got, tt.want)
            }
        })
    }
}
```
