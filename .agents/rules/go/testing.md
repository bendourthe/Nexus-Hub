---
title: Go Testing Standards
category: go
priority: high
---

# Go Testing Standards

## Framework and Structure

- Use the standard `testing` package plus `github.com/stretchr/testify` (`assert`, `require`) for assertions.
- Use `github.com/stretchr/testify/mock` for interface mocking or generate mocks with `mockery`.
- Organize: unit tests alongside source (`foo_test.go`); integration tests in `tests/integration/`; E2E in `tests/e2e/`.
- Use `cargo nextest` equivalent: `go test -race -count=1 ./...`.

## Table-Driven Tests

- Always use table-driven tests for functions with multiple input/output combinations:

```go
func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 1, 2, 3},
        {"negative", -1, -2, -3},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            assert.Equal(t, tt.expected, Add(tt.a, tt.b))
        })
    }
}
```

## Test Isolation

- Never share mutable state between test cases. Initialize fresh values in each subtest.
- Use `t.Parallel()` in tests that are safe to run concurrently; this reduces total test suite time.
- Use `t.TempDir()` for temporary files; the testing package cleans them up automatically.
- Use `t.Setenv()` to modify environment variables in tests; it restores the original value after.

## Benchmarks and Integration

- Benchmark hot-path functions with `func BenchmarkFoo(b *testing.B)` and include them in CI.
- Tag integration tests with `//go:build integration` and run separately: `go test -tags=integration ./...`.
- Use `testcontainers-go` for tests that require a real database or service.

## Coverage

- Target 80% line coverage: `go test -coverprofile=coverage.out ./... && go tool cover -func=coverage.out`.
- Gate CI: `go test -cover -covermode=atomic ./... | grep -v "^ok"` should produce no output below threshold.
