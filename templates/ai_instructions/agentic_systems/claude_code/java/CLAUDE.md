# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: Java 17+ (LTS)
- **Framework**: Spring Boot 3.x
- **Build Tool**: Maven / Gradle
- **Testing**: JUnit 5 + Mockito
- **Database**: PostgreSQL / MySQL (if applicable)
- **Code Quality**: Checkstyle, SpotBugs

## Project Structure
```
src/
├── main/
│   ├── java/com/company/project/
│   │   ├── Application.java         - Main entry point
│   │   ├── config/                   - Configuration classes
│   │   ├── controller/               - REST controllers
│   │   ├── service/                  - Core application logic
│   │   ├── repository/               - Data access
│   │   ├── model/                    - Domain entities & DTOs
│   │   ├── exception/                - Custom exceptions
│   │   └── util/                     - Utility classes
│   └── resources/
│       ├── application.yml           - Main configuration
│       └── db/migration/             - Database migrations
└── test/
    ├── java/                         - Test classes
    └── temp/                         - Temporary tests (auto-deleted)
target/                               - Compiled output
docs/                                 - Documentation
```

## Key Files
- `pom.xml` - Maven dependencies and configuration
- `application.yml` - Spring Boot configuration
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Development
mvn spring-boot:run
./mvnw spring-boot:run

# Testing
mvn test
mvn verify
mvn test -Dtest=SpecificTest

# Build
mvn clean install
mvn clean package -DskipTests

# Code Quality
mvn checkstyle:check
mvn spotbugs:check
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
- **Full Mode** (new projects): Complete Spring Boot architecture, comprehensive testing

## Context References
- Architecture: @.claude/context/architecture.md
- Decisions: @.claude/memory/decisions.md

## Critical Rules

**NEVER:**
- Auto-modify version numbers in pom.xml (ask first)
- Suggest git commands unless explicitly requested
- Create separate markdown files (use DEVLOG.md)
- Run commands in chat (request user to run in terminal)

**ALWAYS:**
- Ask clarifying questions before proceeding
- Explain reasoning and teach concepts
- Use iterative testing with src/test/java/ temp tests
- Document progress in DEVLOG.md
- Follow Spring Boot best practices
- Follow the quality checklist before delivering code
