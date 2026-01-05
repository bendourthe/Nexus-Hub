# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: C# 12 / .NET 8+
- **Framework**: ASP.NET Core / .NET MAUI / WPF
- **IDE**: Visual Studio 2022 / Rider / VS Code
- **Testing**: xUnit / NUnit + Moq
- **ORM**: Entity Framework Core (if applicable)
- **Code Quality**: StyleCop, SonarAnalyzer

## Project Structure
```
ProjectName/
├── src/
│   ├── ProjectName.Api/              - Web API project
│   │   ├── Controllers/              - API controllers
│   │   ├── Models/                   - Request/Response models
│   │   ├── Services/                 - Business logic
│   │   └── Program.cs                - Entry point
│   ├── ProjectName.Core/             - Core domain logic
│   │   ├── Entities/                 - Domain entities
│   │   ├── Interfaces/               - Abstractions
│   │   └── Services/                 - Core application logic
│   └── ProjectName.Infrastructure/   - Data access & external
│       ├── Data/                     - EF DbContext
│       └── Repositories/             - Data repositories
├── tests/
│   ├── ProjectName.UnitTests/        - Unit tests
│   └── ProjectName.IntegrationTests/ - Integration tests
├── docs/                             - Documentation
├── ProjectName.sln                   - Solution file
└── Directory.Build.props             - Common MSBuild props
```

## Key Files
- `ProjectName.sln` - Solution file
- `*.csproj` - Project files with dependencies
- `appsettings.json` - Application configuration
- `Directory.Build.props` - Shared MSBuild properties
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Development
dotnet run --project src/ProjectName.Api
dotnet watch run --project src/ProjectName.Api

# Testing
dotnet test
dotnet test --filter "Category=Unit"
dotnet test --collect:"XPlat Code Coverage"

# Build
dotnet build
dotnet publish -c Release

# Code Quality
dotnet format
dotnet build /p:TreatWarningsAsErrors=true
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

### Workflow Skills (for complex tasks)
- **task-coordinator** - Break down multi-step implementations
- **context-manager** - Navigate large codebases
- **workflow-orchestrator** - Chain skills with quality gates

### Efficiency Modes
- **Quick Mode** (simple fixes): Minimal docs, focus on core fix
- **Full Mode** (new projects): Complete Clean Architecture, comprehensive testing

## Context References
- Architecture: @.claude/context/architecture.md
- Decisions: @.claude/memory/decisions.md

## Critical Rules

**NEVER:**
- Auto-modify version numbers in .csproj files (ask first)
- Suggest git commands unless explicitly requested
- Create separate markdown files (use DEVLOG.md)
- Run commands in chat (request user to run in terminal)

**ALWAYS:**
- Ask clarifying questions before proceeding
- Explain reasoning and teach concepts
- Use iterative testing with temp test classes
- Document progress in DEVLOG.md
- Follow .NET naming conventions (PascalCase)
- Follow the quality checklist before delivering code
