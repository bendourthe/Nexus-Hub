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

### Task Types → Skills Activated
| Task Type | Core Skills | Specialist Skills |
|-----------|-------------|-------------------|
| Bug Fix | code-standards, quality-checklist | context-manager, refactoring-expert |
| New Feature | workflow-methodology, testing-framework | task-coordinator, workflow-orchestrator |
| Refactoring | code-standards, implementation-patterns | refactoring-expert, legacy-modernizer |
| Documentation | documentation-standards | api-documentation, technical-documentation |
| Testing | unit-tests, test-cases | performance-testing, mutation-testing |
| Infrastructure | cicd-integration | kubernetes-expert, terraform-specialist, cicd-architect |
| Database | code-standards | sql-expert |
| Dependencies | security | dependency-manager, dependency-security-audit |
| Go Development | code-standards | go-expert |

### Workflow Skills (for complex tasks)
- **task-coordinator** - Break down multi-step implementations
- **context-manager** - Navigate large codebases
- **workflow-orchestrator** - Chain skills with quality gates
- **go-expert** - Deep Go expertise for concurrency and idioms

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
