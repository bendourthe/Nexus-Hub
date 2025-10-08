# Go Context Analysis

## Objective
Establish comprehensive understanding of the Go project before conducting detailed code review. This phase gathers context about purpose, architecture, dependencies, and current state to inform all subsequent review activities.

## Analysis Checklist

### Project Understanding
- [ ] Project purpose and target audience identified
- [ ] Core features and use cases documented
- [ ] Development stage assessed (prototype, production, legacy)
- [ ] Key stakeholders and maintainers identified
- [ ] Project documentation reviewed (README, CONTRIBUTING, docs/)

### Architecture & Structure
- [ ] Entry points and main packages mapped
- [ ] Package organization evaluated
- [ ] Design patterns identified (factory, adapter, middleware, etc.)
- [ ] Configuration management approach documented
- [ ] Environment-specific settings catalogued

### Dependency Analysis
- [ ] Direct dependencies listed with versions (go.mod)
- [ ] Indirect dependencies reviewed
- [ ] Outdated packages identified
- [ ] Security vulnerabilities in dependencies checked
- [ ] License compatibility verified

### Build & Deployment
- [ ] Build process documented (Makefile, build scripts)
- [ ] Test execution approach understood
- [ ] CI/CD pipelines identified (GitHub Actions, GitLab CI, Jenkins)
- [ ] Deployment targets documented (containers, binaries, serverless)
- [ ] Environment variables and secrets management reviewed

### Codebase Metrics
- [ ] Lines of code measured (total, per package)
- [ ] Cyclomatic complexity assessed
- [ ] Package coupling and cohesion evaluated
- [ ] Code duplication percentage calculated
- [ ] Comment density analyzed

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Go Project Context Analysis

Please perform a comprehensive context analysis of this Go project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose, target audience, and key features
   - Identify development stage (prototype/production/legacy)
   - List primary maintainers and stakeholders

2. **Map Repository Structure**
   - Identify all source directories (cmd/, internal/, pkg/, etc.)
   - Locate test files (*_test.go)
   - Find configuration files (go.mod, go.sum, Makefile, etc.)
   - Document documentation locations (docs/, wiki, external)

## Phase 2: Architecture Understanding

1. **Entry Points & Core Packages**
   - Identify main entry points (cmd/*/main.go)
   - Map core business logic packages
   - Document public API surface (exported types/functions)
   - Identify internal vs external interfaces

2. **Design Patterns & Architecture**
   - Identify architectural style (monolithic, modular, microservices)
   - Document design patterns in use (factory, builder, strategy, etc.)
   - Map data flow through the application
   - Identify configuration and settings management approach

3. **Package Dependencies**
   - Create dependency graph between internal packages
   - Identify circular dependencies
   - Assess package coupling (tight/loose)
   - Evaluate separation of concerns

## Phase 3: Dependency Analysis

1. **Dependency Inventory**
   ```bash
   # List all dependencies
   go list -m all

   # View dependency graph
   go mod graph

   # Check for tidy dependencies
   go mod tidy -v
   ```

2. **Dependency Health Check**
   ```bash
   # Check for outdated packages
   go list -u -m all

   # Check for security vulnerabilities
   govulncheck ./...
   # or
   nancy go.sum
   ```

3. **License & Compatibility**
   - List licenses for all dependencies
   - Flag potential license conflicts
   - Identify deprecated or unmaintained packages

## Phase 4: Build & Deployment

1. **Build System**
   - Document build configuration (Makefile, build scripts, mage)
   - Identify build tools and flags
   - Review build tags and conditional compilation
   - Check for cross-compilation requirements

2. **Test Infrastructure**
   - Identify testing approaches (standard testing, testify, etc.)
   - Document test execution commands
   - Review test organization (unit, integration, e2e)
   - Assess benchmark test coverage

3. **CI/CD Pipeline**
   - Locate CI/CD configuration (.github/workflows, .gitlab-ci.yml, etc.)
   - Document automated checks (linting, testing, security scans)
   - Review deployment automation
   - Identify quality gates and merge requirements

4. **Environment Management**
   - Document environment variables and configuration
   - Review secrets management approach
   - Identify environment-specific settings (dev/staging/prod)
   - Check for .env files or configuration packages

## Phase 5: Codebase Metrics

1. **Size & Complexity Metrics**
   ```bash
   # Lines of code
   find . -name "*.go" -not -path "*/vendor/*" | xargs wc -l

   # Cyclomatic complexity
   gocyclo -over 10 .

   # Code statistics
   gocloc .
   ```

2. **Quality Indicators**
   - Calculate code-to-comment ratio
   - Measure average function length
   - Identify large files (>500 lines)
   - Count TODO/FIXME/HACK comments

3. **Duplication Analysis**
   ```bash
   # Check for code duplication
   dupl -threshold 50 .
   ```

## Phase 6: Documentation Review

1. **Code Documentation**
   - Assess godoc comment coverage (packages, types, functions)
   - Review godoc format compliance
   - Check exported identifier documentation
   - Evaluate inline comment quality

2. **Project Documentation**
   - Review README completeness
   - Check for CONTRIBUTING.md
   - Assess CHANGELOG.md or release notes
   - Review architecture documentation

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary
- **Project Name**: [name]
- **Purpose**: [1-2 sentence description]
- **Stage**: [prototype/production/legacy]
- **Go Version**: [version requirements]
- **Architecture**: [architectural style]

### Project Structure
```
project/
├── cmd/                       # Command-line applications
│   └── [app]/
│       └── main.go
├── internal/                  # Private application code
│   └── [packages]/
├── pkg/                       # Public library code
│   └── [packages]/
├── api/                       # API definitions (proto, OpenAPI)
├── configs/                   # Configuration files
├── scripts/                   # Build and utility scripts
├── test/                      # Additional test data/helpers
├── go.mod                     # Module definition
├── go.sum                     # Dependency checksums
├── Makefile                   # Build automation
└── README.md
```

### Architecture Overview
- **Design Patterns**: [patterns identified]
- **Package Organization**: [brief description]
- **Key Dependencies**: [critical external packages]
- **Configuration Approach**: [how settings are managed]

### Dependency Summary
| Package | Version | Purpose | Status | Security |
|---------|---------|---------|--------|----------|
| [name] | [version] | [usage] | [current/outdated] | [safe/vulnerable] |

### Build & Deployment
- **Build System**: [tool and configuration]
- **Test Framework**: [standard library/testify/other]
- **CI/CD**: [platform and key workflows]
- **Deployment**: [target environments]

### Codebase Metrics
- **Total Lines**: [number] (excluding tests and vendor)
- **Average Complexity**: [gocyclo score]
- **Packages**: [count]
- **Duplication**: [percentage]
- **Documentation**: [godoc coverage %]

### Go-Specific Observations
- **Go Version**: [required version from go.mod]
- **Module Path**: [module name]
- **Replace Directives**: [if any, list them]
- **Build Tags**: [if used, list common tags]
- **CGO Usage**: [yes/no and where]

### Key Findings
1. **Strengths**: [positive observations]
2. **Concerns**: [potential issues to investigate]
3. **Dependencies**: [outdated or vulnerable packages]
4. **Documentation**: [gaps or areas needing improvement]

### Recommendations for Review Focus
Based on this context, the following review areas should be prioritized:
1. [Area 1] - [reason]
2. [Area 2] - [reason]
3. [Area 3] - [reason]

### Next Steps
- [ ] Proceed with code quality review
- [ ] Conduct security audit (especially if vulnerable dependencies found)
- [ ] Perform performance analysis
- [ ] Review test coverage and quality

## Notes
- Save this context report - it will inform all subsequent review phases
- Flag any critical issues discovered during context gathering
- Update dependency vulnerabilities before detailed code review
- Use this as baseline for measuring improvement over time
~~~
