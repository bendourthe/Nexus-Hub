# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: Go 1.21+
- **Framework**: Standard library / Gin / Echo / Fiber
- **Testing**: go test + testify
- **Build**: go build / goreleaser
- **Code Quality**: golangci-lint, go vet, staticcheck

## Project Structure
```
project-name/
├── cmd/                              - Application entry points
│   └── app/
│       └── main.go                   - Main entry point
├── internal/                         - Private application code
│   ├── config/                       - Configuration
│   ├── handler/                      - HTTP handlers
│   ├── service/                      - Core application logic
│   ├── repository/                   - Data access
│   ├── model/                        - Domain models
│   └── middleware/                   - HTTP middleware
├── pkg/                              - Public library code
│   └── util/                         - Shared utilities
├── api/                              - API definitions (OpenAPI, proto)
├── tests/                            - Additional test utilities
│   └── temp/                         - Temporary tests
├── scripts/                          - Build and deployment scripts
├── docs/                             - Documentation
├── go.mod                            - Module definition
├── go.sum                            - Dependency checksums
├── Makefile                          - Build automation
├── CHANGELOG.md                      - Version history
├── README.md                         - Project documentation
└── DEVLOG.md                         - Development log
```

## Key Files
- `go.mod` - Module definition and dependencies
- `go.sum` - Dependency checksums
- `Makefile` - Build automation
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Development
go run cmd/app/main.go
go run .

# Testing
go test ./...
go test -v ./...
go test -cover ./...
go test -race ./...

# Build
go build -o bin/app cmd/app/main.go
go build ./...

# Code Quality
golangci-lint run
go vet ./...
go fmt ./...
goimports -w .
```

## Quick Reference

### Task Types → Focus Areas
| Task Type | Skills Activated |
|-----------|------------------|
| Bug Fix | interaction-principles, code-standards, quality-checklist |
| New Feature | project-setup, workflow-methodology, testing-framework |
| Refactoring | code-standards, implementation-patterns |
| Documentation | documentation-standards |
| Version/Git | version-control |

### Efficiency Modes
- **Quick Mode** (simple fixes): Minimal docs, focus on core fix
- **Full Mode** (new projects): Complete project layout, comprehensive testing

## Context References
- Architecture: @.claude/context/architecture.md
- Decisions: @.claude/memory/decisions.md

## Critical Rules

**NEVER:**
- Auto-modify version numbers (ask first)
- Suggest git commands unless explicitly requested
- Create separate markdown files (use DEVLOG.md)
- Run commands in chat (request user to run in terminal)

**ALWAYS:**
- Ask clarifying questions before proceeding
- Explain reasoning and teach concepts
- Use iterative testing with tests/temp/
- Document progress in DEVLOG.md
- Follow Go idioms (accept interfaces, return structs)
- Follow the quality checklist before delivering code
- Handle errors explicitly (no panic in library code)
