---
name: code-review-context-analysis
description: Establish comprehensive understanding of project structure, architecture, dependencies, and current state before conducting detailed code review
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Code Review
tags: [code-review, context, architecture, workflow, phase-1]
priority: HIGH
based_on: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
---

# Code Review Context Analysis

Establish comprehensive understanding of the project before conducting detailed code review. This skill is **Phase 1** of the complete code review workflow, gathering context about project purpose, architecture, dependencies, and current state to inform all subsequent review activities.

## When to Use This Skill

Use this skill as the **first phase** of any comprehensive code review:

- ✅ Beginning a code review for a new project or codebase
- ✅ Onboarding to an unfamiliar codebase
- ✅ Before proposing major architectural changes
- ✅ Pre-acquisition technical due diligence
- ✅ Audit preparation and compliance assessment
- ✅ Legacy codebase evaluation for modernization
- ✅ Security audit preparation
- ✅ Performance optimization planning

**This skill is essential when**:
- You need to understand project architecture and design decisions
- You're identifying technical debt and maintenance burden
- You want to assess development maturity and practices
- You need to map dependencies and potential security risks
- You're planning follow-up review phases

## What This Skill Does

This skill implements **Phase 1: Context Analysis** of the six-phase code review workflow:

### Phase 1: Context Analysis (This Skill)
Understand the project landscape, architecture, and development practices

### Subsequent Phases
- Phase 2: [Code Quality Review](../code-review-quality/SKILL.md)
- Phase 3: [Security Review](../code-review-security/SKILL.md)
- Phase 4: [Performance Review](../code-review-performance/SKILL.md)
- Phase 5: [Testing Review](../code-review-testing/SKILL.md)
- Phase 6: [Final Report](../code-review-final-report/SKILL.md)

## Why Context Analysis Matters

**Without Context Analysis**:
```
Reviewer: *jumps directly into code review*
Reviewer: *flags architectural pattern as "bad practice"*
Result:

- ❌ Misunderstanding of design decisions
- ❌ Inappropriate recommendations
- ❌ Missing critical dependencies
- ❌ Overlooking project-specific constraints
- ❌ Inefficient review process
- ❌ Poor prioritization of findings
```

**With Context Analysis**:
```
Reviewer: *understands architecture and constraints*
Reviewer: *identifies patterns and their rationale*
Reviewer: *reviews code within proper context*
Result:

- ✅ Informed, relevant recommendations
- ✅ Proper understanding of tradeoffs
- ✅ Comprehensive dependency mapping
- ✅ Awareness of project constraints
- ✅ Efficient, focused review process
- ✅ Well-prioritized, actionable findings
```

## Benefits of Context Analysis

### Better Review Quality
- **Informed Decisions**: Understand why code is structured as it is
- **Relevant Recommendations**: Suggestions fit project constraints and goals
- **Comprehensive Coverage**: Don't miss critical areas or dependencies
- **Proper Prioritization**: Focus on actual risks and issues

### Efficiency
- **Focused Review**: Know where to look for specific issues
- **Avoid Distractions**: Skip reviewing known, acceptable patterns
- **Faster Analysis**: Understanding architecture speeds up code review
- **Better Planning**: Allocate time appropriately across codebase

### Stakeholder Value
- **Business Alignment**: Recommendations align with project goals
- **Cost Awareness**: Understand development and maintenance costs
- **Risk Assessment**: Identify and quantify technical risks
- **Strategic Guidance**: Provide long-term technical direction

## Prerequisites

### Required
- Access to source code repository
- Repository structure and organization details
- Build and configuration files
- Documentation (README, architecture docs, etc.)

### Recommended
- Access to development team for clarifications
- Historical context (git history, past decisions)
- Deployment and infrastructure information
- Issue tracking and project management tools access

### Knowledge
- Understanding of common architectural patterns
- Familiarity with dependency management
- Basic knowledge of security best practices
- Understanding of software metrics and complexity

## Instructions

### Step 1: Repository Discovery

**Understand the project structure and organization:**

1. **Clone and Explore Repository**
   ```bash
   # Clone the repository
   git clone <REPO_URL>
   cd <project-directory>

   # Get repository structure overview
   tree -L 3 -I 'node_modules|venv|.venv|__pycache__|target|build'

   # Or use ls for basic overview
   ls -la
   ```

2. **Identify Key Files and Directories**

   **For Python projects**, look for:
   - `src/` or `app/` - Main source code
   - `tests/` - Test suite
   - `pyproject.toml`, `setup.py`, `setup.cfg` - Build configuration
   - `requirements.txt`, `Pipfile`, `poetry.lock` - Dependencies
   - `README.md`, `CHANGELOG.md` - Documentation
   - `.github/`, `.gitlab-ci.yml` - CI/CD configuration

   **For JavaScript projects**, look for:
   - `src/` or `lib/` - Main source code
   - `tests/` or `__tests__/` - Test suite
   - `package.json`, `tsconfig.json` - Configuration
   - `node_modules/` - Dependency directory
   - `.github/workflows/`, `.circleci/` - CI/CD

   **For Java projects**, look for:
   - `src/main/java/` - Main source code
   - `src/test/java/` - Test suite
   - `pom.xml`, `build.gradle` - Build configuration
   - `target/` or `build/` - Build outputs

   **For Go projects**, look for:
   - Root package files - Main source code
   - `*_test.go` - Test files
   - `go.mod`, `go.sum` - Dependency management
   - `cmd/` - Application entry points
   - `pkg/` - Library code

   **For C/C++ projects**, look for:
   - `src/` - Source files
   - `include/` - Header files
   - `tests/` or `test/` - Test suite
   - `CMakeLists.txt`, `Makefile` - Build configuration
   - `lib/` or `vendor/` - External libraries

   **For C# projects**, look for:
   - `*.sln` - Solution file
   - `*.csproj` - Project files
   - Source and test directories
   - `packages.config`, `*.nuspec` - Dependencies

3. **Read Primary Documentation**
   ```bash
   # Review key documentation files
   cat README.md
   cat CONTRIBUTING.md
   cat CHANGELOG.md
   cat docs/architecture.md  # if exists
   ```

### Step 2: Architecture Understanding

**Map the application architecture and design patterns:**

1. **Identify Entry Points**

   **Python**:
   ```python
   # Look for main entry points
   # Common locations: main.py, __main__.py, app.py, cli.py

   # Example Python application entry point
   if __name__ == "__main__":
       app = create_app()
       app.run()
   ```

   **JavaScript/TypeScript**:
   ```javascript
   // Look for entry points
   // Common locations: index.js, main.js, app.js, server.js

   // Example Node.js entry point
   const express = require('express');
   const app = express();
   app.listen(3000, () => console.log('Server running'));
   ```

   **Java**:
   ```java
   // Look for classes with main() method
   // Common locations: Main.java, Application.java

   public class Application {
       public static void main(String[] args) {
           SpringApplication.run(Application.class, args);
       }
   }
   ```

   **Go**:
   ```go
   // Look for main package and main() function
   // Common locations: cmd/app/main.go, main.go

   package main

   func main() {
       app := NewApplication()
       app.Run()
   }
   ```

   **C/C++**:
   ```c
   // Look for main() function
   // Common locations: main.c, main.cpp, app.c

   int main(int argc, char *argv[]) {
       init_application();
       return run_application();
   }
   ```

   **C#**:
   ```csharp
   // Look for Main() method or Program.cs
   // Common locations: Program.cs

   public class Program {
       public static void Main(string[] args) {
           CreateHostBuilder(args).Build().Run();
       }
   }
   ```

2. **Identify Architectural Patterns**

   Common patterns to look for:
   - **Monolithic**: Single deployable application
   - **Modular**: Organized into logical modules/packages
   - **Microservices**: Multiple independent services
   - **MVC**: Model-View-Controller separation
   - **Layered**: Presentation, Business, Data layers
   - **Repository Pattern**: Data access abstraction
   - **Factory Pattern**: Object creation abstraction
   - **Singleton Pattern**: Single instance management
   - **Observer Pattern**: Event-driven architecture
   - **Strategy Pattern**: Algorithm encapsulation

3. **Map Module Dependencies**

   **Python** - Analyze imports:
   ```python
   # Check for circular dependencies
   import sys
   import importlib.util

   # Look at import patterns
   # Internal: from src.core import module
   # External: import pandas, import numpy
   ```

   **JavaScript** - Analyze requires/imports:
   ```javascript
   // CommonJS
   const module = require('./module');

   // ES6 modules
   import { function } from './module';
   ```

   **Java** - Analyze package structure:
   ```java
   // Package organization
   com.company.project.domain
   com.company.project.service
   com.company.project.repository
   ```

### Step 3: Dependency Analysis

**Analyze external dependencies and their health:**

1. **Extract Dependency List**

   **Python**:
   ```bash
   # From requirements.txt
   cat requirements.txt

   # From pyproject.toml
   grep -A 20 "\[project.dependencies\]" pyproject.toml

   # From Pipfile
   cat Pipfile
   ```

   **JavaScript**:
   ```bash
   # From package.json
   cat package.json | jq '.dependencies'
   cat package.json | jq '.devDependencies'
   ```

   **Java**:
   ```bash
   # From pom.xml
   grep -A 5 "<dependency>" pom.xml

   # From build.gradle
   grep "implementation\|api\|compile" build.gradle
   ```

   **Go**:
   ```bash
   # From go.mod
   cat go.mod | grep "require"
   ```

   **C#**:
   ```bash
   # From .csproj
   grep "PackageReference" *.csproj
   ```

2. **Check for Outdated Dependencies**

   **Python**:
   ```bash
   pip list --outdated
   ```

   **JavaScript**:
   ```bash
   npm outdated
   # or
   yarn outdated
   ```

   **Java**:
   ```bash
   mvn versions:display-dependency-updates
   # or
   gradle dependencyUpdates
   ```

   **Go**:
   ```bash
   go list -u -m all
   ```

3. **Security Vulnerability Scan**

   **Python**:
   ```bash
   pip install pip-audit
   pip-audit

   # or
   pip install safety
   safety check
   ```

   **JavaScript**:
   ```bash
   npm audit
   # or
   yarn audit
   ```

   **Java**:
   ```bash
   mvn dependency-check:check
   ```

   **Go**:
   ```bash
   go install golang.org/x/vuln/cmd/govulncheck@latest
   govulncheck ./...
   ```

### Step 4: Build and Deployment Analysis

**Understand how the application is built and deployed:**

1. **Build System Review**

   **Python**:
   ```bash
   # Check build configuration
   cat pyproject.toml
   cat setup.py

   # Test build process
   python -m pip install -e .
   ```

   **JavaScript**:
   ```bash
   # Check build scripts
   cat package.json | jq '.scripts'

   # Test build
   npm install
   npm run build
   ```

   **Java**:
   ```bash
   # Maven build
   mvn clean install

   # Gradle build
   gradle build
   ```

   **Go**:
   ```bash
   # Go build
   go build ./...
   go test ./...
   ```

   **C/C++**:
   ```bash
   # CMake build
   cmake .
   make

   # Make build
   make all
   ```

   **C#**:
   ```bash
   # .NET build
   dotnet build
   dotnet test
   ```

2. **CI/CD Configuration**

   Look for:
   - GitHub Actions: `.github/workflows/*.yml`
   - GitLab CI: `.gitlab-ci.yml`
   - CircleCI: `.circleci/config.yml`
   - Jenkins: `Jenkinsfile`
   - Travis CI: `.travis.yml`

   Review what's automated:
   - Builds
   - Tests
   - Linting/code quality checks
   - Security scans
   - Deployments

3. **Environment Configuration**

   Look for:
   - Environment variables (`.env.example`)
   - Configuration files (`config.yaml`, `settings.py`)
   - Secrets management approach
   - Multi-environment support (dev/staging/prod)

### Step 5: Codebase Metrics Collection

**Gather quantitative metrics about the codebase:**

1. **Lines of Code**

   **All languages**:
   ```bash
   # Using cloc (recommended - install first)
   cloc .

   # Or basic counting
   find . -name "*.py" | xargs wc -l  # Python
   find . -name "*.js" | xargs wc -l   # JavaScript
   find . -name "*.java" | xargs wc -l # Java
   find . -name "*.go" | xargs wc -l   # Go
   find . -name "*.c" -o -name "*.h" | xargs wc -l  # C
   find . -name "*.cpp" -o -name "*.hpp" | xargs wc -l  # C++
   find . -name "*.cs" | xargs wc -l   # C#
   ```

2. **Complexity Metrics**

   **Python**:
   ```bash
   pip install radon
   radon cc . -a -nb  # Cyclomatic complexity
   radon mi . -nb     # Maintainability index
   ```

   **JavaScript**:
   ```bash
   npm install -g complexity-report
   cr src/**/*.js
   ```

   **Java**:
   ```bash
   # Use PMD or Checkstyle
   mvn pmd:pmd
   ```

   **Go**:
   ```bash
   go install github.com/fzipp/gocyclo/cmd/gocyclo@latest
   gocyclo -over 15 .
   ```

3. **Code Duplication**

   **Python**:
   ```bash
   pylint --disable=all --enable=duplicate-code .
   ```

   **JavaScript**:
   ```bash
   npm install -g jscpd
   jscpd src/
   ```

   **Java**:
   ```bash
   mvn pmd:cpd
   ```

### Step 6: Documentation Assessment

**Evaluate documentation quality and completeness:**

1. **Code Documentation**

   **Python**:
   ```bash
   # Check docstring coverage
   pip install interrogate
   interrogate . -v
   ```

   **JavaScript**:
   ```bash
   # Check JSDoc coverage
   npm install -g documentation
   documentation lint src/**/*.js
   ```

2. **Project Documentation**

   Check for:
   - README.md completeness
   - CONTRIBUTING.md presence
   - CHANGELOG.md or release notes
   - Architecture documentation
   - API documentation
   - Setup and installation guides
   - Troubleshooting guides

### Step 7: Generate Context Report

**Compile findings into a structured report:**

Create a report with the following structure:

```markdown
# Code Review Context Analysis Report

**Project**: [Name]
**Date**: [Date]
**Reviewer**: [Name]

## Executive Summary

- **Project Purpose**: [Brief description]
- **Development Stage**: [Prototype/Production/Legacy]
- **Primary Language**: [Language]
- **Architecture Style**: [Pattern]
- **Team Size**: [Estimated from contributors]
- **Age**: [First commit to last commit timespan]

## Project Structure

### Directory Organization
[Tree structure of key directories]

### Key Components
- Entry Points: [List main entry points]
- Core Modules: [List critical modules]
- External Interfaces: [APIs, CLI, GUI]

## Architecture Analysis

### Design Patterns
[List identified patterns and their locations]

### Module Dependencies
[Description of internal dependencies and coupling]

### Technology Stack
- **Language**: [Version]
- **Framework**: [Name and version]
- **Database**: [Type and version]
- **Key Libraries**: [Major dependencies]

## Dependency Health

### Summary
- Total Dependencies: [Count]
- Outdated: [Count]
- With Known Vulnerabilities: [Count]
- License Issues: [Count]

### Critical Dependencies
| Package | Version | Status | Security | Recommendation |
|---------|---------|--------|----------|----------------|
| [name]  | [ver]   | [status] | [safe/vuln] | [action] |

## Build & Deployment

### Build System
[Tool and configuration]

### CI/CD Integration
[Platform and pipeline description]

### Testing Automation
[Framework and coverage]

## Codebase Metrics

- **Total Lines**: [Number]
- **Source Code**: [Number] ([%])
- **Comments**: [Number] ([%])
- **Average Complexity**: [Score]
- **Maintainability Index**: [Score]
- **Duplication**: [%]

### Complexity Hotspots
| File | Complexity | Lines | Recommendation |
|------|------------|-------|----------------|
| [file] | [score] | [count] | [suggestion] |

## Documentation Quality

- **Code Documentation**: [Good/Fair/Poor]
- **Project Documentation**: [Comprehensive/Adequate/Lacking]
- **API Documentation**: [Present/Absent]
- **Gaps Identified**: [List major gaps]

## Key Findings

### Strengths
1. [Positive observation]
2. [Positive observation]
3. [Positive observation]

### Concerns
1. [Issue to investigate]
2. [Issue to investigate]
3. [Issue to investigate]

### Dependencies
- Outdated packages: [List critical ones]
- Vulnerable packages: [List with CVEs]

## Recommendations for Review Focus

Based on context analysis, prioritize:

1. **[Area]** - [Reason and expected findings]
2. **[Area]** - [Reason and expected findings]
3. **[Area]** - [Reason and expected findings]

## Next Steps

- [ ] Proceed with [Phase 2: Code Quality Review](../code-review-quality/SKILL.md)
- [ ] Address critical dependency vulnerabilities
- [ ] Conduct [Phase 3: Security Review](../code-review-security/SKILL.md)
- [ ] Perform [Phase 4: Performance Analysis](../code-review-performance/SKILL.md)
- [ ] Execute [Phase 5: Testing Review](../code-review-testing/SKILL.md)
- [ ] Generate [Phase 6: Final Report](../code-review-final-report/SKILL.md)
```

## Multi-Language Support

This skill supports comprehensive context analysis for:

- **Python** - Django, Flask, FastAPI applications
- **JavaScript/TypeScript** - Node.js, React, Angular, Vue applications
- **Java** - Spring Boot, Jakarta EE applications
- **Go** - Standard library, Gin, Echo applications
- **C** - System programming, embedded applications
- **C++** - Modern C++, Qt, Boost applications
- **C#** - .NET Core, ASP.NET applications

Each language has specific tools and patterns for dependency analysis, metrics collection, and documentation assessment.

## Common Pitfalls and Solutions

### Pitfall 1: Skipping Context Analysis

**Problem**: Jumping directly into code review without understanding context.

**Solution**: Always start with context analysis - it saves time and improves review quality.

### Pitfall 2: Surface-Level Analysis

**Problem**: Only reviewing README without understanding actual architecture.

**Solution**: Trace code execution paths and map actual dependencies.

### Pitfall 3: Ignoring Git History

**Problem**: Missing important historical context and decisions.

**Solution**: Review git log, major commits, and contributor patterns.

### Pitfall 4: Not Identifying Technical Debt

**Problem**: Failing to quantify maintenance burden.

**Solution**: Use metrics tools and analyze complexity hotspots.

## Success Criteria

- [ ] Complete understanding of project purpose and architecture
- [ ] All dependencies identified and health-checked
- [ ] Build and deployment processes documented
- [ ] Codebase metrics collected and analyzed
- [ ] Documentation quality assessed
- [ ] Key strengths and concerns identified
- [ ] Focus areas for subsequent reviews determined
- [ ] Context report generated and shared
- [ ] Team ready to proceed with detailed code review phases

## Related Skills

### Code Review Workflow (6-Phase Process)
1. [`code-review-context-analysis`](./SKILL.md) - **This skill** - Understand project landscape
2. [`code-review-quality`](../code-review-quality/SKILL.md) - Assess maintainability and technical debt
3. [`code-review-security`](../code-review-security/SKILL.md) - Identify vulnerabilities and risks
4. [`code-review-performance`](../code-review-performance/SKILL.md) - Find bottlenecks and optimization opportunities
5. [`code-review-testing`](../code-review-testing/SKILL.md) - Evaluate test coverage and quality
6. [`code-review-final-report`](../code-review-final-report/SKILL.md) - Consolidate findings and create action plan

### Supporting Skills
- [`plan-before-code`](../plan-before-code/SKILL.md) - Planning methodology
- [`test-driven-development`](../test-driven-development/SKILL.md) - TDD workflow

## Additional Resources

### Context Analysis Tools
- **Python**: radon, interrogate, pip-audit, safety
- **JavaScript**: complexity-report, npm-audit, documentation
- **Java**: PMD, Checkstyle, OWASP Dependency-Check
- **Go**: gocyclo, govulncheck, staticcheck
- **Multi-language**: cloc, SonarQube, CodeClimate

### Architecture Documentation
- [C4 Model](https://c4model.com/) - Software architecture diagrams
- [Arc42](https://arc42.org/) - Architecture documentation template
- [Structurizr](https://structurizr.com/) - Architecture as code

### Metrics and Analysis
- [Sonar](https://www.sonarsource.com/) - Code quality and security
- [CodeClimate](https://codeclimate.com/) - Maintainability analysis
- [LGTM](https://lgtm.com/) - Automated code review

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: AI Templates Code Review Workflow, Anthropic Claude Code Best Practices 2025
**Template Source**: `code_review/context_analysis/*.md`
