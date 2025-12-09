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
