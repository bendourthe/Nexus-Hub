# Java Context Analysis

## Objective
Establish comprehensive understanding of the Java project before conducting detailed code review. This phase gathers context about purpose, architecture, build system, dependencies, and current state to inform all subsequent review activities.

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

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Project Context Analysis

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

## Notes
- Save this context report - it will inform all subsequent review phases
- Flag any critical issues discovered during context gathering
- Update vulnerable dependencies before detailed code review
- Use this as baseline for measuring improvement over time
- Pay special attention to Spring Boot autoconfiguration and custom configurations
~~~
