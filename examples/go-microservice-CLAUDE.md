# Go Microservice

A Go microservice exposing a REST or gRPC API. Structured as a standard Go module with clean architecture layering (handler → service → repository). Deployed as a minimal Docker image.

## Tech Stack
- **Language**: Go 1.22+
- **Package Manager**: Go modules (go.mod / go.sum)
- **Build**: `go build` / `Makefile`
- **Test**: `go test` with `testify`
- **Lint/Format**: `golangci-lint`, `gofmt` / `goimports`

## Project Layout
```
cmd/
  server/
    main.go           # Entry point; wires dependencies
internal/
  handler/            # HTTP/gRPC handlers (thin layer)
  service/            # Business logic
  repository/         # Data access (interfaces + implementations)
  model/              # Domain types
  middleware/         # Auth, logging, tracing
pkg/                  # Exported, reusable packages
config/               # Config loading (env vars via envconfig or viper)
migrations/           # SQL migrations (golang-migrate)
Dockerfile
Makefile
go.mod
go.sum
```

## Key Commands
```bash
# Build
go build ./cmd/server/...

# Run tests
go test ./... -race -count=1

# Lint
golangci-lint run ./...

# Format
goimports -w .

# Docker build
docker build -t myservice:dev .

# Run locally
go run cmd/server/main.go
```

## Non-Obvious Tooling
- Use `golang-migrate` for database migrations; never run raw SQL in application startup
- Dependency injection via constructor functions (not a DI framework) — keep `main.go` as the composition root
- Use `context.Context` as the first parameter of every function that does I/O
- `golangci-lint` config lives in `.golangci.yml`; do not disable linters without a comment explaining why
- Structured logging via `slog` (stdlib, Go 1.21+) — no `fmt.Println` in production paths

## Go Conventions
- Interfaces belong in the package that *uses* them, not the package that implements them
- Return errors explicitly; never panic in library code
- Table-driven tests with `t.Run` subtests are the standard pattern
- Keep functions under 40 lines where possible; split at logical boundaries
- All exported functions and types must have Go doc comments
- Use `errors.Is` / `errors.As` for error inspection; never string-match error messages
- HTTP handlers must respect `r.Context()` cancellation for all downstream calls
- Configuration must come from environment variables only; no config files in production

## Communication Style
- Place punctuation outside quotation marks (logical punctuation)
- No em-dashes; use parentheses, commas, or separate sentences
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Critical Rules
- Verify work before marking complete
- Find root causes; no temporary fixes
- Destructive git commands require user confirmation
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- **MANDATORY: Every Bash/shell command approval MUST be preceded by a one-sentence plain-language explanation** of what the command does and what its impact will be. This applies to ALL commands regardless of complexity. No exceptions.
- Ask clarifying questions before coding if requirements are ambiguous

## Output Minimization
- Prefer `go test -q`; report only FAIL lines and counts
- Summarize golangci-lint output; report only issue counts and file:line references

## Context References
- Skills: `.claude/skills/` (auto-activated by task context)
- Architecture: `.claude/context/architecture.md`
- Decisions: `.claude/memory/decisions.md`
- Rules: `.claude/rules/go/` (Go-specific coding standards)
- Agents: `.claude/agents/` (specialized subagents for code review, TDD, security)
