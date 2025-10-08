# C# Context Analysis

## Objective
Establish comprehensive understanding of the .NET project before conducting detailed code review. This phase gathers context about purpose, architecture, dependencies, and current state to inform all subsequent review activities.

## Analysis Checklist

### Project Understanding
- [ ] Project purpose and target audience identified
- [ ] Core features and use cases documented
- [ ] Development stage assessed (prototype, production, legacy)
- [ ] Key stakeholders and maintainers identified
- [ ] Project documentation reviewed (README, docs/, XML documentation)

### Architecture & Structure
- [ ] Entry points and main assemblies mapped
- [ ] Solution and project organization evaluated
- [ ] Design patterns identified (MVVM, Repository, Factory, etc.)
- [ ] Configuration management approach documented (appsettings.json, Configuration API)
- [ ] Dependency injection container usage reviewed

### Dependency Analysis
- [ ] NuGet package dependencies listed with versions
- [ ] Development vs production dependencies separated
- [ ] Outdated packages identified
- [ ] Security vulnerabilities in packages checked
- [ ] License compatibility verified

### Build & Deployment
- [ ] Build process documented (.csproj, .sln, MSBuild)
- [ ] Test execution approach understood
- [ ] CI/CD pipelines identified (Azure DevOps, GitHub Actions, Jenkins)
- [ ] Deployment targets documented (IIS, Docker, Azure, AWS)
- [ ] Environment variables and secrets management reviewed

### Codebase Metrics
- [ ] Lines of code measured (total, per project)
- [ ] Cyclomatic complexity assessed
- [ ] Assembly coupling and cohesion evaluated
- [ ] Code duplication percentage calculated
- [ ] XML documentation coverage analyzed

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C# Project Context Analysis

Please perform a comprehensive context analysis of this C# project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose, target audience, and key features
   - Identify development stage (prototype/production/legacy)
   - List primary maintainers and stakeholders

2. **Map Repository Structure**
   - Identify solution file(s) (.sln)
   - Locate all project files (.csproj)
   - Find test projects (*.Tests, *.UnitTests, *.IntegrationTests)
   - Document configuration files (appsettings.json, web.config, app.config)
   - Locate documentation (docs/, README.md, XML doc comments)

## Phase 2: Architecture Understanding

1. **Entry Points & Core Projects**
   - Identify application entry points (Program.cs, Startup.cs, Main methods)
   - Map core business logic projects
   - Document public API surface
   - Identify project dependencies and references

2. **Design Patterns & Architecture**
   - Identify architectural style (N-tier, Clean Architecture, CQRS, etc.)
   - Document design patterns in use (Factory, Repository, Strategy, etc.)
   - Map data flow through the application
   - Identify configuration management approach (IConfiguration, Options pattern)
   - Review dependency injection setup (IServiceCollection)

3. **Project Dependencies**
   - Create dependency graph between projects
   - Identify circular dependencies
   - Assess project coupling (tight/loose)
   - Evaluate separation of concerns

## Phase 3: Dependency Analysis

1. **NuGet Package Inventory**
   - List all NuGet packages from all .csproj files
   - Document .NET/ASP.NET Core version(s)
   - Identify framework dependencies
   - Separate development packages (test frameworks, analyzers)

2. **Dependency Health Check**
   ```powershell
   # Check for outdated packages
   dotnet list package --outdated

   # Check for vulnerable packages
   dotnet list package --vulnerable

   # Check for deprecated packages
   dotnet list package --deprecated
   ```

3. **License & Compatibility**
   - List licenses for all NuGet packages
   - Flag potential license conflicts
   - Identify deprecated or unmaintained packages
   - Check .NET version compatibility

## Phase 4: Build & Deployment

1. **Build System**
   - Document build configuration (.csproj, Directory.Build.props)
   - Identify target frameworks (net8.0, net6.0, netstandard2.0, etc.)
   - Review project properties (nullable references, LangVersion)
   - Check for custom MSBuild targets or props files

2. **Test Infrastructure**
   - Identify testing frameworks (NUnit, xUnit, MSTest)
   - Document test execution commands
   - Review test configuration files (runsettings, test.csproj)
   - Assess test organization and structure

3. **CI/CD Pipeline**
   - Locate CI/CD configuration (.github/workflows, azure-pipelines.yml, etc.)
   - Document automated checks (build, test, code analysis)
   - Review deployment automation
   - Identify quality gates and merge requirements

4. **Environment Management**
   - Document configuration sources (appsettings.json, environment variables, Azure Key Vault)
   - Review secrets management approach
   - Identify environment-specific settings (Development/Staging/Production)
   - Check for user secrets (dotnet user-secrets)

## Phase 5: Codebase Metrics

1. **Size & Complexity Metrics**
   ```powershell
   # Lines of code (using Visual Studio Metrics)
   # Or third-party tools like dotnet-counters, NDepend

   # Enable code metrics in project file:
   # <GenerateDocumentationFile>true</GenerateDocumentationFile>
   # <EnableNETAnalyzers>true</EnableNETAnalyzers>
   # <AnalysisLevel>latest</AnalysisLevel>
   ```

2. **Quality Indicators**
   - Calculate code-to-comment ratio
   - Measure average method length
   - Identify large files (>500 lines)
   - Count TODO/FIXME/HACK comments
   - Review XML documentation coverage

3. **Code Analysis Results**
   ```powershell
   # Run built-in analyzers
   dotnet build /p:TreatWarningsAsErrors=true

   # Run security analyzers
   # Add SecurityCodeScan.VS2019 NuGet package
   ```

## Phase 6: Documentation Review

1. **Code Documentation**
   - Assess XML documentation coverage (public APIs)
   - Review documentation format and consistency
   - Check for nullable reference annotations
   - Evaluate inline comment quality

2. **Project Documentation**
   - Review README completeness
   - Check for CONTRIBUTING.md
   - Assess CHANGELOG.md or release notes
   - Review architecture documentation (ADRs)

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary
- **Project Name**: [name]
- **Purpose**: [1-2 sentence description]
- **Stage**: [prototype/production/legacy]
- **.NET Version**: [target framework(s)]
- **Architecture**: [architectural style]
- **Project Type**: [Web API, Console, Desktop, Class Library, etc.]

### Solution Structure
```
SolutionName/
├── src/
│   ├── ProjectName.Domain/          # Business entities
│   ├── ProjectName.Application/     # Use cases/services
│   ├── ProjectName.Infrastructure/  # Data access, external services
│   └── ProjectName.API/             # Web API or entry point
├── tests/
│   ├── ProjectName.UnitTests/
│   └── ProjectName.IntegrationTests/
├── docs/
├── SolutionName.sln
└── Directory.Build.props
```

### Architecture Overview
- **Design Patterns**: [patterns identified]
- **Project Organization**: [brief description]
- **Key Dependencies**: [critical NuGet packages]
- **Configuration Approach**: [how settings are managed]
- **DI Container**: [built-in, Autofac, etc.]

### Dependency Summary
| Package | Version | Purpose | Status | Security |
|---------|---------|---------|--------|----------|
| [name] | [version] | [usage] | [current/outdated] | [safe/vulnerable] |

### Build & Deployment
- **Build System**: [MSBuild, SDK-style project]
- **Target Framework(s)**: [net8.0, net6.0, etc.]
- **Test Framework**: [xUnit, NUnit, MSTest]
- **CI/CD**: [platform and key workflows]
- **Deployment**: [target environments - IIS, Docker, Azure App Service, etc.]

### Codebase Metrics
- **Total Projects**: [count]
- **Total Lines**: [number] (excluding tests)
- **Analyzer Warnings**: [count by severity]
- **XML Documentation**: [coverage percentage]
- **Nullable Context**: [enabled/disabled]

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
- Update vulnerable dependencies before detailed code review
- Use this as baseline for measuring improvement over time
~~~
