---
title: Go Code Style
category: go
priority: high
---

# Go Code Style Rules

## Formatting and Linting

- Run `gofmt` (or `goimports`) before every commit. CI must reject unformatted code.
- Use `golangci-lint` with at minimum: `errcheck`, `gosimple`, `govet`, `staticcheck`, `unused`, `revive`.
- Keep `.golangci.yml` in the repo root. Do not disable linters inline without a comment.

## Naming Conventions

- Package names: short, lowercase, no underscores (e.g., `auth`, `httputil`, not `http_util`).
- Exported identifiers: `PascalCase`. Unexported: `camelCase`.
- Acronyms: treat as a word -- `userID`, `httpURL`, `APIKey` (consistent casing, not `userID` and `HTTPurl`).
- Error variables: name them `ErrFoo` for sentinel errors; error types end in `Error` (e.g., `type ValidationError struct`).
- Interfaces with one method: name as `<Method>er` (e.g., `Reader`, `Stringer`, `Closer`).

## Code Organization

- Keep functions under 40 lines. Split at logical boundaries; each function should have one clear purpose.
- Interfaces belong in the package that *uses* them, not the package that implements them (Go proverb).
- Avoid `init()` functions. Use explicit initialization in `main()` or constructors.
- Group related declarations: `const` blocks, `type` blocks, `var` blocks -- in that order.
- Use `_` for unused loop variables; never shadow the blank identifier.

## Error Handling

- Check every error. Never ignore errors with `_` unless there is an explicit comment explaining why.
- Return errors as the last return value: `func Foo() (Result, error)`.
- Wrap errors with context using `fmt.Errorf("doing X: %w", err)` to preserve the chain.
- Use `errors.Is` and `errors.As` for inspection; never string-match error messages.
- Do not panic in library code. Panic only in `main()` for unrecoverable startup failures.

## Concurrency

- Pass `context.Context` as the first parameter to every function that does I/O or blocks.
- Always cancel contexts: `ctx, cancel := context.WithCancel(ctx); defer cancel()`.
- Document whether a type is safe for concurrent use (or not) in its doc comment.
- Prefer channels for signaling; prefer mutexes for shared state. Do not mix without a clear reason.
