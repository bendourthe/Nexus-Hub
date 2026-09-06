---
title: Go Security Rules
category: go
priority: critical
---

# Go Security Rules

## Input Validation and SQL

- Validate all external inputs (HTTP, gRPC, CLI) using a validation library (e.g., `github.com/go-playground/validator`).
- Use parameterized queries exclusively. Never build SQL strings with `fmt.Sprintf` or string concatenation.
- `database/sql`: always use `?` or `$N` placeholders. With `sqlx` or `pgx`: use named parameters.
- Sanitize file paths with `filepath.Clean` and verify they stay within an expected root.

## Authentication and Secrets

- Load secrets from environment variables using `os.Getenv` -- never hardcode in source.
- Use `golang.org/x/crypto/bcrypt` for password hashing. Never use MD5 or SHA-1 for passwords.
- Verify JWT signatures with a well-maintained library (e.g., `github.com/golang-jwt/jwt`). Always validate `exp`, `iss`, and `aud` claims.
- Rotate secrets immediately if committed; use `git filter-repo` (not `git filter-branch`) to purge history.

## HTTP Security

- Set security headers on all HTTP responses: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy`.
- Always set timeouts on HTTP servers and clients: `ReadTimeout`, `WriteTimeout`, `IdleTimeout` on `http.Server`; `Timeout` on `http.Client`.
- Validate and whitelist URLs before making outbound HTTP requests to prevent SSRF.

## Dependency Security

- Run `govulncheck ./...` in CI to detect known vulnerabilities in dependencies.
- Pin Go module versions in `go.sum`. Review `go mod tidy` diffs carefully -- unexpected additions are a red flag.
- Audit new dependencies before adding them, especially those that use `unsafe` or `cgo`.

## Concurrency Safety

- Use `sync.Mutex` or `sync/atomic` for shared state. Never access shared variables from multiple goroutines without synchronization.
- Run tests with `-race`: `go test -race ./...`. The race detector must produce zero warnings in CI.
- Close channels from the sender side, never the receiver. Document channel ownership in comments.
