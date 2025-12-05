---
template_id: java_context_analysis
template_name: Context Analysis - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: code_review
phase: context_analysis
phase_number: 1
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites: []
related_templates:

  - code_review/code_quality/java_code_quality.md
tools:

  - junit (5.11.3)

  - maven

  - gradle
tags:

  - code-review

  - java
---
# Java Context Analysis

## Objective
Establish comprehensive understanding of the Java project before conducting detailed code review. This phase gathers context about purpose, architecture, build system, dependencies, and current state to inform all subsequent review activities.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/context_analysis/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/context_analysis/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Analysis Checklist

### Project Understanding

- [ ] Project purpose and target audience identified

- [ ] Core features and use cases documented

- [ ] Development stage assessed (prototype, production, legacy)

- [ ] Key stakeholders and maintainers identified

- [ ] Project documentation reviewed (README, docs/)

### Architecture & Structure

- [ ] Entry points and main classes mapped

- [ ] Package organization evaluated

- [ ] Design patterns identified (MVC, factory, singleton, etc.)

- [ ] Spring Boot/Jakarta EE architecture assessed

- [ ] Configuration management approach documented

- [ ] Multi-module structure analyzed (if applicable)

### Dependency Analysis

- [ ] Maven/Gradle dependencies listed with versions

- [ ] Direct and transitive dependencies identified

- [ ] Outdated libraries detected

- [ ] Security vulnerabilities in dependencies checked

- [ ] License compatibility verified

### Build & Deployment

- [ ] Build tool documented (Maven, Gradle, Ant)

- [ ] Build lifecycle and plugins reviewed

- [ ] Test execution approach understood

- [ ] CI/CD pipelines identified (Jenkins, GitHub Actions, GitLab CI)

- [ ] Deployment targets documented (JAR, WAR, container, cloud)

- [ ] Environment configuration reviewed

### Codebase Metrics

- [ ] Lines of code measured (total, per package)

- [ ] Cyclomatic complexity assessed

- [ ] Package coupling and cohesion evaluated

- [ ] Code duplication percentage calculated

- [ ] JavaDoc coverage analyzed

## Severity Classification

Use this framework to classify and prioritize all findings from the code review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**

- Security vulnerabilities (SQL injection, XSS, authentication bypass)

- Resource leaks (unclosed connections, file handles, memory leaks)

- Data loss risks (destructive operations without validation)

- Thread safety violations (race conditions, deadlocks)

- Compliance violations (GDPR, HIPAA, PCI-DSS)

**Action Required:**

- Block deployment until fixed

- Require hotfix within 24 hours

- Add tests to prevent regression

- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**

- Incorrect business logic (wrong calculations, flawed algorithms)

- Performance bottlenecks (O(n²) algorithms, missing indexes, inefficient queries)

- Memory inefficiency (loading large datasets into memory unnecessarily)

- Breaking API changes without deprecation

- Missing critical error handling (network errors, API failures not caught)

**Action Required:**

- Schedule fix in current sprint

- Cannot release without resolution

- Update documentation

- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**

- High complexity (cyclomatic complexity >10, functions >100 lines)

- Code duplication (>10 lines duplicated across modules)

- Poor naming (unclear variable/function names, inconsistent conventions)

- Missing tests (<80% coverage on critical paths)

- Incomplete error messages (no context for debugging)

**Action Required:**

- Add to backlog

- Prioritize in next sprint planning

- Consider during refactoring opportunities

- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**

- Style violations (linting warnings, formatting issues)

- Minor performance optimizations (in non-critical code paths)

- Missing documentation on helper functions

- Verbose code that could be more concise

- Debug statements left in code

**Action Required:**

- Fix opportunistically during other work

- Batch with other low-priority changes

- Good for new contributors

- Can be deferred indefinitely

---

## Severity Assignment Guidelines

**When to Escalate Severity:**

- Issue affects **production environment** → escalate one level

- Issue affects **customer-facing features** → escalate one level

- Issue has **no workaround** → escalate one level

- Issue appears in **multiple locations** → escalate one level

**When to De-escalate Severity:**

- Issue only in **test/development code** → de-escalate one level

- Issue has **easy workaround** → de-escalate one level

- Issue is **isolated to single module** → de-escalate one level

- Issue **rarely executed** (edge case) → de-escalate one level

**Examples:**

- Memory leak in production API: **HIGH → CRITICAL** (production + customer-facing)

- Style violation in test file: **LOW → Ignore** (test code + style only)

- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix (with code example if applicable)

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/services/userService:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**

- Response time degrades with user count (currently 500ms for 10k users)

- High memory usage (50MB+ per request)

- Poor scalability (can't handle >100k users)

**Recommendation:**
Move filtering to database with indexed query:

- Add database index on search fields

- Use database LIKE/ILIKE queries

- Implement pagination (limit results to 50)

- Add caching for common searches

**Effort:** 3 hours (2 hours implementation + 1 hour testing)

**Priority:** Must fix before next release (performance SLA violation)
```

---


## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Project Context Analysis

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/context_analysis"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**

- All generated files should be saved with the `${OUTPUT_DIR}/` prefix

- Examples:

  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`

  - Template files → `${OUTPUT_DIR}/templates/template.yaml`

  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Analysis Protocol

Please perform a comprehensive context analysis of this Java project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**

   - Read and summarize README.md and primary documentation

   - Determine project purpose, target audience, and key features

   - Identify development stage (prototype/production/legacy)

   - List primary maintainers and stakeholders

   - Identify Java version and runtime requirements

2. **Map Repository Structure**

   - Identify source directories (src/main/java, src/test/java)

   - Locate resource directories (src/main/resources)

   - Find configuration files (pom.xml, build.gradle, application.properties)

   - Document documentation locations (docs/, JavaDoc)

   - Identify multi-module structure if present

## Phase 2: Architecture Understanding

1. **Entry Points & Core Components**

   - Identify main entry points (main classes, @SpringBootApplication)

   - Map core business logic packages

   - Document public API surface (REST endpoints, public methods)

   - Identify internal vs external interfaces

   - Review package structure and naming conventions

2. **Design Patterns & Architecture**

   - Identify architectural style (monolithic, microservices, layered)

   - Document design patterns in use (factory, builder, strategy, etc.)

   - Map data flow through the application

   - Identify Spring Framework usage (if applicable)

   - Review dependency injection patterns

   - Assess DTO/entity/model organization

3. **Framework & Technology Stack**

   - Identify frameworks (Spring Boot, Jakarta EE, Quarkus, Micronaut)

   - Document persistence layer (JPA, Hibernate, MyBatis, JDBC)

   - Identify web framework (Spring MVC, JAX-RS)

   - Check for reactive programming (WebFlux, RxJava)

   - Document security framework (Spring Security, Shiro)

4. **Module Dependencies**

   - Create dependency graph between internal modules

   - Identify circular dependencies

   - Assess package coupling (tight/loose)

   - Evaluate separation of concerns

## Phase 3: Build System Analysis

1. **Maven Project Analysis**
   ```bash
   # For Maven projects

   # Display project information
   mvn help:effective-pom

   # Show dependency tree
   mvn dependency:tree

   # Check for dependency conflicts
   mvn dependency:analyze

   # List plugins
   mvn help:effective-settings
   ```

2. **Gradle Project Analysis**
   ```bash
   # For Gradle projects

   # Show dependencies
   ./gradlew dependencies

   # Check for dependency updates
   ./gradlew dependencyUpdates

   # Build scan
   ./gradlew build --scan
   ```

3. **Build Configuration Review**

   - Java version and compiler settings

   - Build plugins and their configurations

   - Resource filtering and profiles

   - Packaging type (JAR, WAR, EAR)

   - Custom build steps or scripts

## Phase 4: Dependency Analysis

1. **Dependency Inventory**

   - List all dependencies from pom.xml or build.gradle

   - Separate compile vs runtime vs test dependencies

   - Document dependency versions and scopes

   - Identify BOM (Bill of Materials) usage

   - Check for dependency version management

2. **Dependency Health Check**
   ```bash
   # Check for outdated dependencies (Maven)
   mvn versions:display-dependency-updates

   # Check for security vulnerabilities (Maven)
   mvn org.owasp:dependency-check-maven:check

   # For Gradle
   ./gradlew dependencyCheckAnalyze
   ```

3. **Common Dependencies Review**

   - Spring Boot starter dependencies

   - Logging frameworks (SLF4J, Logback, Log4j2)

   - Testing frameworks (JUnit 5, TestNG, Mockito)

   - Database drivers (PostgreSQL, MySQL, Oracle)

   - Utility libraries (Apache Commons, Guava)

   - JSON/XML processing (Jackson, GSON, JAXB)

4. **License & Compatibility**

   - List licenses for all dependencies

   - Flag potential license conflicts

   - Identify deprecated or unmaintained libraries

## Phase 5: Configuration Management

1. **Application Configuration**

   - Review application.properties or application.yml

   - Check for profile-specific configurations

   - Identify externalized configuration

   - Review environment variable usage

   - Assess secrets management approach

2. **Spring Boot Configuration** (if applicable)

   - Review @Configuration classes

   - Check @Bean definitions

   - Assess property binding (@ConfigurationProperties)

   - Review autoconfiguration exclusions

   - Check actuator endpoints configuration

3. **Database Configuration**

   - Data source configuration

   - JPA/Hibernate settings

   - Connection pooling (HikariCP, Tomcat)

   - Migration tools (Flyway, Liquibase)

   - Schema management approach

## Phase 6: Testing Infrastructure

1. **Test Structure Analysis**
   ```
   src/test/
   ├── java/
   │   ├── [package]/unit/       # Unit tests
   │   ├── [package]/integration/ # Integration tests
   │   └── [package]/e2e/        # End-to-end tests
   └── resources/
       └── test-data/            # Test fixtures
   ```

2. **Testing Framework Review**

   - Identify testing framework (JUnit 4/5, TestNG)

   - Check for test runner configuration

   - Review test lifecycle annotations

   - Assess test organization patterns

   - Document test naming conventions

3. **Test Support Libraries**

   - Mocking frameworks (Mockito, EasyMock, PowerMock)

   - Spring Test support (@SpringBootTest, @DataJpaTest)

   - Test containers for integration tests

   - AssertJ or Hamcrest for assertions

   - REST testing (RestAssured, MockMvc)

## Phase 7: CI/CD Pipeline

1. **Build Automation**

   - Locate CI/CD configuration (.github/workflows, Jenkinsfile, .gitlab-ci.yml)

   - Document build stages (compile, test, package, deploy)

   - Review automated quality checks

   - Identify deployment automation

   - Check for artifact repository integration

2. **Quality Gates**

   - Code coverage requirements

   - Static analysis integration (SonarQube, Checkstyle)

   - Security scanning (OWASP, Snyk)

   - Performance testing

   - Deployment approval processes

## Phase 8: Codebase Metrics

1. **Size & Complexity Metrics**
   ```bash
   # Lines of code (using cloc)
   cloc src/main/java

   # Cyclomatic complexity (using PMD)
   mvn pmd:check

   # Code duplication (using PMD CPD)
   mvn pmd:cpd-check
   ```

2. **Quality Indicators**

   - Calculate code-to-comment ratio

   - Measure average method length

   - Identify large classes (>500 lines)

   - Count TODO/FIXME/XXX comments

   - Assess package organization depth

3. **Static Analysis Tools**

   - Run Checkstyle for style violations

   - Execute PMD for code quality issues

   - Use SpotBugs for bug detection

   - Run SonarQube analysis (if available)

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary

- **Project Name**: [name]

- **Purpose**: [1-2 sentence description]

- **Stage**: [prototype/production/legacy]

- **Java Version**: [version]

- **Build Tool**: [Maven/Gradle/Ant]

- **Architecture**: [architectural style]

- **Framework**: [Spring Boot/Jakarta EE/Plain Java/etc.]

### Project Structure
```
project/
├── src/main/java/          # Main source code
│   └── com/example/
│       ├── config/         # Configuration classes
│       ├── controller/     # REST controllers
│       ├── service/        # Business logic
│       ├── repository/     # Data access
│       └── model/          # Domain models
├── src/test/java/          # Test code
├── src/main/resources/     # Configuration files
├── pom.xml or build.gradle # Build configuration
└── README.md
```

### Architecture Overview

- **Design Patterns**: [patterns identified]

- **Framework Stack**: [Spring Boot, JPA, etc.]

- **Layering**: [controller → service → repository pattern]

- **Key Dependencies**: [critical external libraries]

- **Configuration Approach**: [properties, YAML, annotations]

### Technology Stack
| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Java Runtime | [JDK version] | [version] | Runtime environment |
| Framework | [Spring Boot/etc.] | [version] | Application framework |
| Persistence | [JPA/Hibernate] | [version] | Data access |
| Build Tool | [Maven/Gradle] | [version] | Build automation |
| Web Server | [Tomcat/Undertow/Jetty] | [version] | Servlet container |

### Dependency Summary
| Dependency | Version | Purpose | Status | Security |
|------------|---------|---------|--------|----------|
| [group:artifact] | [version] | [usage] | [current/outdated] | [safe/vulnerable] |

### Build & Deployment

- **Build Tool**: [Maven/Gradle and version]

- **Build Lifecycle**: [key phases and goals]

- **Test Execution**: [mvn test / gradle test]

- **Packaging**: [JAR/WAR, executable jar]

- **CI/CD**: [platform and key workflows]

- **Deployment**: [target environments - Docker, K8s, Cloud]

### Codebase Metrics

- **Total Lines**: [number] (excluding tests)

- **Packages**: [count]

- **Classes**: [count]

- **Methods**: [count]

- **Average Complexity**: [cyclomatic complexity score]

- **Duplication**: [percentage]

- **JavaDoc Coverage**: [percentage]

### Configuration Summary

- **Profile Management**: [dev, test, prod profiles]

- **Property Sources**: [application.properties, environment variables]

- **Secrets Management**: [approach used]

- **Database Configuration**: [datasource, connection pool]

- **Logging Configuration**: [framework and levels]

### Key Findings
1. **Strengths**: [positive observations]

2. **Concerns**: [potential issues to investigate]

3. **Dependencies**: [outdated or vulnerable packages]

4. **Build Issues**: [any build warnings or concerns]

5. **Documentation**: [gaps or areas needing improvement]

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

- [ ] Assess Spring Boot best practices (if applicable)

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/context_analysis/analysis_scripts
mkdir -p ${OUTPUT_DIR}/context_analysis/supporting_data
```

**Save files as follows**:

- Main report → `review/context_analysis/context_analysis_report.md`

- Findings data → `review/context_analysis/context_analysis_findings.json`

- Analysis scripts → `review/context_analysis/analysis_scripts/`

- Supporting data → `review/context_analysis/supporting_data/`

## Notes

- Save this context report - it will inform all subsequent review phases

- Flag any critical issues discovered during context gathering

- Update vulnerable dependencies before detailed code review

- Use this as baseline for measuring improvement over time

- Pay special attention to Spring Boot autoconfiguration and custom configurations
~~~
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**

- [ ] All directories created successfully

- [ ] All files saved in correct subdirectories

- [ ] No files created in repository root

- [ ] Directory structure matches expected layout
