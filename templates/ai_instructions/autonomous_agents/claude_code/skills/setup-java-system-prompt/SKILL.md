---
name: setup-java-system-prompt
description: Configure comprehensive Java development system prompt for Claude Code with Spring Boot, Maven/Gradle, testing frameworks, and enterprise best practices
version: 1.0.0
author: Benjamin Dourthe
language: Java
category: Configuration
priority: HIGH
tags: [java, spring-boot, setup, system-prompt, configuration, standards, maven, gradle, junit]
---

# Setup Java System Prompt

Configure Claude Code with comprehensive Java development standards, best practices, and workflows optimized for enterprise-quality Spring Boot application development.

## When to Use This Skill

Use this skill when you need to:
- Set up a new Java/Spring Boot project with Claude Code
- Configure Claude Code for Java enterprise development
- Apply comprehensive Java development standards
- Establish consistent coding practices across Java projects
- Optimize Claude Code for Spring Boot and microservices workflows
- Configure testing frameworks (JUnit 5, TestNG, Mockito)
- Set up code quality tools (Checkstyle, SpotBugs, SonarQube)

## What This Skill Does

This skill helps you configure Claude Code with:

### 1. Java Development Standards
- Java 17+ features and best practices
- Spring Boot 3.x conventions and patterns
- Code formatting standards (120 char lines)
- Import organization (java → javax → spring → third-party → local)
- Naming conventions and package structure
- Lombok best practices and annotation usage

### 2. Project Architecture Guidelines
- Standard Spring Boot project structure (controller/service/repository layers)
- Maven/Gradle configuration and dependency management
- Multi-module project organization
- Configuration management (application.yml/properties)
- Documentation structure (README, CHANGELOG, DEVLOG)
- Docker and containerization setup

### 3. Testing Framework
- JUnit 5 and TestNG patterns
- Integration testing with @SpringBootTest
- Mockito for unit testing
- Test output formatting requirements
- Test containers for database testing
- Performance and load testing strategies

### 4. Development Workflow
- Task breakdown methodology for complex features
- Iterative testing protocol
- Quality gates and code review checklists
- CI/CD pipeline integration
- Version control best practices

### 5. Code Quality Standards
- JavaDoc templates (detailed and summary)
- Logging best practices (SLF4J/Logback)
- Exception handling patterns
- Security considerations (OWASP guidelines)
- Performance optimization techniques
- Code quality tools configuration (Checkstyle, SpotBugs)

### 6. Spring Boot Specific
- RESTful API design patterns
- Dependency injection and IoC best practices
- Spring Data JPA patterns and optimizations
- Spring Security configuration
- Actuator endpoints and monitoring
- Application profiling (dev, test, prod)

## Prerequisites

- Claude Code installed and configured
- Java 17+ JDK installed
- Maven 3.8+ or Gradle 8+ installed
- Basic understanding of Java and Spring Boot development
- IDE configured (IntelliJ IDEA, Eclipse, or VS Code)
- Docker installed (optional, for containerization)

## Instructions

### Step 1: Choose System Prompt Version

Decide between two versions based on your needs:

**Comprehensive Version (~40k tokens)**
- Best for: Enterprise applications, microservices, complex Spring Boot projects
- Features: Complete architectural guidance, extensive Spring patterns, detailed security practices
- Token count: ~40,000 tokens
- File: `agent_prompts/autonomous_agents/claude_code/java/CLAUDE_comprehensive_40k.md`
- Includes: Advanced Spring Security, reactive programming, cloud-native patterns

**Condensed Version (~20k tokens)**
- Best for: Quick development, simple REST APIs, smaller projects
- Features: Essential Spring Boot guidelines, core best practices, streamlined workflow
- Token count: ~20,000 tokens
- File: `agent_prompts/autonomous_agents/claude_code/java/CLAUDE_condensed_20k.md`
- Includes: Standard Spring Boot patterns, basic testing, simplified configuration

### Step 2: Configure Claude Code

There are two methods to configure Claude Code with the Java system prompt:

#### Method A: Project-Level CLAUDE.md (Recommended)

1. Navigate to your project root directory
2. Copy the chosen system prompt file to `CLAUDE.md`:
   ```bash
   # For comprehensive version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/java/CLAUDE_comprehensive_40k.md ./CLAUDE.md

   # For condensed version
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/java/CLAUDE_condensed_20k.md ./CLAUDE.md
   ```
3. Claude Code will automatically detect and load this file

#### Method B: Session-Based Configuration

Start Claude Code with the system prompt:
```bash
# For comprehensive version
claude --system-prompt ./path/to/CLAUDE_comprehensive_40k.md

# For condensed version
claude --system-prompt ./path/to/CLAUDE_condensed_20k.md
```

### Step 3: Verify Configuration

Test that the system prompt is active by asking Claude Code to:

#### 1. Create a Spring Boot REST Controller

```
"Create a REST controller for managing user entities with CRUD operations"
```

Expected behavior:
- Uses @RestController and @RequestMapping annotations
- Follows REST conventions (GET, POST, PUT, DELETE)
- Includes proper exception handling with @ControllerAdvice
- Has comprehensive JavaDoc comments
- Uses constructor-based dependency injection
- Includes input validation with @Valid
- Returns ResponseEntity with proper HTTP status codes

#### 2. Request Project Structure

```
"Show me the recommended project structure for a Spring Boot microservice"
```

Expected behavior:
- Follows standard layered architecture (controller/service/repository)
- Includes config/, model/, dto/, exception/ packages
- Shows pom.xml or build.gradle structure
- Includes application.yml configuration
- Documents Docker and docker-compose.yml setup
- Shows test directory structure

#### 3. Ask About Testing Strategy

```
"How should I structure my tests for this Spring Boot application?"
```

Expected behavior:
- Explains unit tests vs integration tests
- Mentions @SpringBootTest for integration testing
- Describes MockMvc for controller testing
- Explains @MockBean for mocking dependencies
- Shows test naming conventions
- Includes test output formatting requirements

### Step 4: Configure Code Quality Tools

After setting up the system prompt, configure quality tools:

#### Checkstyle Configuration

1. Create `checkstyle.xml` in project root (Claude Code will provide template)
2. Add Checkstyle plugin to pom.xml or build.gradle
3. Configure in IDE for real-time checking

#### SpotBugs Configuration

1. Add SpotBugs plugin to build configuration
2. Configure exclusion filters if needed
3. Integrate with CI pipeline

#### SonarQube Integration

1. Set up SonarQube server or use SonarCloud
2. Add Sonar plugin to build configuration
3. Configure quality gates and code coverage thresholds

### Step 5: Customize for Your Organization (Optional)

If you need to add organization-specific standards:

1. Open the CLAUDE.md file in your project
2. Add a new section at the end:
   ```markdown
   # Organization-Specific Standards

   ## Additional Requirements
   - [Your custom coding standards]
   - [Internal library preferences]
   - [Compliance requirements (GDPR, HIPAA, etc.)]
   - [Company-specific Spring Boot configurations]
   - [Internal API design patterns]
   ```
3. Save and restart Claude Code session

### Step 6: Commit to Version Control

Add the CLAUDE.md to your repository so team members have consistent configuration:

```bash
git add CLAUDE.md
git commit -m "Add Claude Code Java system prompt configuration"
git push
```

## Key Features of the Java System Prompt

### 1. Import Organization
Automatically organizes imports in the correct order:

1. **Java standard library** (java.*)
2. **Java extensions** (javax.*)
3. **Spring framework** (org.springframework.*)
4. **Third-party libraries** (alphabetically sorted)
5. **Local application imports** (com.company.*)

Example:
```java
// Java standard library
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

// Java extensions
import javax.validation.Valid;

// Spring framework
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

// Third-party libraries
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

// Local application
import com.company.project.dto.UserDTO;
import com.company.project.service.UserService;
```

### 2. Code Standards
- **Line length**: 120 characters (Java standard)
- **Methods**: One blank line between methods
- **Classes**: Package declaration, imports, then class
- **Comments**: JavaDoc for public APIs, inline comments for complex logic
- **Naming**: PascalCase for classes, camelCase for methods/variables, UPPER_CASE for constants
- **No change-tracking comments**: Prevents "changed value" style comments

### 3. Spring Boot Patterns

#### Controller Layer
```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Slf4j
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUserById(@PathVariable Long id) {
        log.debug("Fetching user with id: {}", id);
        return userService.findById(id)
            .map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
}
```

#### Service Layer
```java
@Service
@RequiredArgsConstructor
@Transactional
@Slf4j
public class UserService {

    private final UserRepository userRepository;

    public Optional<UserDTO> findById(Long id) {
        log.debug("Finding user by id: {}", id);
        return userRepository.findById(id)
            .map(this::mapToDTO);
    }
}
```

#### Repository Layer
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    List<User> findByActiveTrue();
}
```

### 4. Testing Framework

#### Unit Testing with JUnit 5 and Mockito
```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserService userService;

    @Test
    @DisplayName("Should find user by ID successfully")
    void shouldFindUserById() {
        // Given
        User user = new User(1L, "test@example.com");
        when(userRepository.findById(1L)).thenReturn(Optional.of(user));

        // When
        Optional<UserDTO> result = userService.findById(1L);

        // Then
        assertThat(result).isPresent();
        assertThat(result.get().getEmail()).isEqualTo("test@example.com");
        verify(userRepository).findById(1L);
    }
}
```

#### Integration Testing with @SpringBootTest
```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureTestDatabase
@Transactional
class UserControllerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @Test
    @DisplayName("Should create user and return 201 Created")
    void shouldCreateUser() {
        // Given
        UserDTO userDTO = new UserDTO("test@example.com", "John Doe");

        // When
        ResponseEntity<UserDTO> response = restTemplate.postForEntity(
            "/api/users", userDTO, UserDTO.class);

        // Then
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody().getEmail()).isEqualTo("test@example.com");
    }
}
```

### 5. Documentation Standards

#### JavaDoc Templates

**Complex Methods**:
```java
/**

 * Processes user registration with email verification.
 *

 * <p>This method handles the complete user registration flow including:
 * <ul>
 *   <li>Email validation and uniqueness check</li>
 *   <li>Password encryption using BCrypt</li>
 *   <li>Verification token generation and email dispatch</li>
 * </ul>
 *

 * @param registrationRequest the user registration data containing email and password
 * @return UserDTO containing the newly created user information
 * @throws EmailAlreadyExistsException if the email is already registered
 * @throws InvalidPasswordException if the password doesn't meet security requirements
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @since 1.0.0
 */
public UserDTO registerUser(RegistrationRequest registrationRequest) {
    // Implementation
}
```

**Simple Methods**:
```java
/**

 * Retrieves all active users.
 *

 * @return list of active users
 */
public List<UserDTO> findActiveUsers() {
    // Implementation
}
```

#### README.md Structure
```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features/changes]

## Overview
[2-3 sentence description of the Spring Boot application]

## Features
- RESTful API with OpenAPI/Swagger documentation
- Spring Security with JWT authentication
- MySQL/PostgreSQL database with Spring Data JPA
- Docker containerization support
- Comprehensive test coverage (unit + integration)

## Technology Stack
- Java 17+
- Spring Boot 3.x
- Spring Data JPA
- Spring Security
- Maven/Gradle
- MySQL/PostgreSQL
- Docker
- JUnit 5 + Mockito

## Installation

### Prerequisites
- Java 17 or higher
- Maven 3.8+ or Gradle 8+
- MySQL/PostgreSQL (or Docker)
- Docker (optional)

### Setup
    ```bash
    git clone <REPO_URL>
    cd [project-name]

    # Using Maven
    mvn clean install
    mvn spring-boot:run

    # Using Gradle
    ./gradlew build
    ./gradlew bootRun

    # Using Docker
    docker-compose up -d
    ```

## Configuration
- Copy `application-example.yml` to `application-dev.yml`
- Configure database connection settings
- Update JWT secret and token expiration

## API Documentation
- Swagger UI: http://localhost:8080/swagger-ui.html
- OpenAPI JSON: http://localhost:8080/v3/api-docs

## Testing
    ```bash
    # Run all tests
    mvn test

    # Run with coverage
    mvn clean test jacoco:report

    # Integration tests only
    mvn test -Dgroups="integration"
    ```

## Deployment
[Docker, Kubernetes, or cloud deployment instructions]
```

### 6. Maven/Gradle Configuration

#### pom.xml Template (Maven)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
        <relativePath/>
    </parent>

    <groupId>com.company</groupId>
    <artifactId>project-name</artifactId>
    <version>0.1.0</version>
    <name>Project Name</name>
    <description>Project description</description>

    <properties>
        <java.version>17</java.version>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>

    <dependencies>
        <!-- Spring Boot Starters -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```

### 7. Development Workflow

#### Iterative Testing Protocol
**CRITICAL: Test-Driven Development for Java**

When implementing new features or fixing bugs:

1. **Create Temporary Test Classes** in `src/test/java/temp/`
   - Name descriptively: `UserRegistrationTest.java`
   - Write comprehensive test cases
   - Include edge cases and error conditions

2. **Implement Solution**
   - Write or modify Spring Boot components
   - Follow layered architecture (controller → service → repository)
   - Document approach in DEVLOG.md

3. **Run Tests and Iterate**
   ```bash
   mvn test -Dtest=UserRegistrationTest
   ```
   - If tests FAIL: analyze, document iteration, modify implementation
   - If tests PASS: verify completeness, proceed to cleanup

4. **Clean Up Temporary Tests**
   - Delete all classes in `src/test/java/temp/`
   - Move valuable test cases to permanent test suites
   - Document final solution in DEVLOG.md

### 8. Code Quality Tools

#### Checkstyle Configuration
- Line length: 120 characters
- Indentation: 4 spaces
- No wildcard imports
- JavaDoc required for public methods

#### SpotBugs Rules
- Detect null pointer issues
- Find resource leaks
- Identify security vulnerabilities
- Check concurrency problems

#### SonarQube Quality Gates
- Code coverage: ≥80%
- Duplicated lines: ≤3%
- Maintainability rating: A
- Security rating: A
- No critical or blocker issues

## Common Configuration Issues

### Issue: System Prompt Not Loading
**Solution**: Verify CLAUDE.md is in the project root directory and restart Claude Code session

### Issue: Token Limit Warnings
**Solution**: Switch from comprehensive (~40k) to condensed (~20k) version

### Issue: Standards Not Being Followed
**Solution**: Explicitly reference the standard in your request:
```
"Following the Spring Boot REST controller pattern in CLAUDE.md, create a user management controller"
```

### Issue: Need Different Standards for Microservice
**Solution**: Create a service-specific CLAUDE.md in the microservice directory with overrides

### Issue: Lombok Not Working
**Solution**: Ensure Lombok plugin is installed in IDE and annotation processing is enabled

### Issue: Tests Not Finding Application Context
**Solution**: Verify @SpringBootTest annotation and test class location follows package structure

## Success Criteria

After completing this skill, you should have:

- [ ] Claude Code configured with Java system prompt (CLAUDE.md in project root)
- [ ] Verified configuration by testing REST controller generation
- [ ] Confirmed Spring Boot project structure knowledge
- [ ] Validated testing framework understanding (JUnit 5, Mockito)
- [ ] Code quality tools configured (Checkstyle, SpotBugs)
- [ ] Maven/Gradle build working correctly
- [ ] Test suite executing successfully
- [ ] Optionally customized for organization-specific needs
- [ ] Committed CLAUDE.md to version control for team consistency
- [ ] Documentation complete (README, CHANGELOG, DEVLOG)

## Validation Checklist

Use this checklist to verify proper configuration:

### Code Generation Quality
- [ ] Generated controllers use proper REST annotations
- [ ] Service classes use @Service and dependency injection
- [ ] Repository interfaces extend JpaRepository correctly
- [ ] DTOs include validation annotations
- [ ] Exception handling follows @ControllerAdvice pattern

### Testing Quality
- [ ] Unit tests use @ExtendWith(MockitoExtension.class)
- [ ] Integration tests use @SpringBootTest
- [ ] Test methods have @DisplayName annotations
- [ ] Assertions use AssertJ fluent API
- [ ] Tests follow Given-When-Then structure

### Documentation Quality
- [ ] Classes have JavaDoc with purpose and author
- [ ] Public methods have parameter and return descriptions
- [ ] README includes setup and configuration instructions
- [ ] API endpoints documented with Swagger/OpenAPI
- [ ] DEVLOG tracks development progress

### Code Quality
- [ ] Imports organized correctly (java → javax → spring → third-party → local)
- [ ] No wildcard imports
- [ ] Line length ≤120 characters
- [ ] Proper exception handling (no empty catch blocks)
- [ ] Logging uses SLF4J with appropriate levels

## Related Skills

- `generate-javadoc`: Use after setup to document existing Java code
- `setup-test-infrastructure`: Establish JUnit 5 testing framework following system prompt standards
- `code-review-quality`: Review Java code quality against configured standards
- `cleanup-java`: Clean up Java code following configured standards
- `setup-spring-security`: Configure Spring Security with JWT authentication
- `setup-docker`: Create Docker and docker-compose configuration

## Additional Resources

- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
- [Java SE 17 Documentation](https://docs.oracle.com/en/java/javase/17/)
- [Spring Data JPA Documentation](https://spring.io/projects/spring-data-jpa)
- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [Mockito Documentation](https://javadoc.io/doc/org.mockito/mockito-core/latest/org/mockito/Mockito.html)
- [Checkstyle Configuration](https://checkstyle.sourceforge.io/)
- [SpotBugs Manual](https://spotbugs.github.io/)
- [Project Lombok Documentation](https://projectlombok.org/)
- [Spring Boot Best Practices](https://spring.io/guides)

## Troubleshooting Guide

### Build Issues

**Problem**: Maven dependencies not resolving
```bash
# Solution
mvn clean install -U
mvn dependency:purge-local-repository
```

**Problem**: Lombok annotations not working
```bash
# Solution
# 1. Install Lombok plugin in IDE
# 2. Enable annotation processing in IDE settings
# 3. Verify Lombok dependency in pom.xml
```

### Test Issues

**Problem**: Integration tests failing with "No qualifying bean"
```bash
# Solution
# 1. Ensure @SpringBootTest annotation is present
# 2. Check that test class is in same package or subpackage as @SpringBootApplication
# 3. Verify component scanning configuration
```

**Problem**: Tests timeout or run slowly
```bash
# Solution
# 1. Use @MockBean instead of real beans where possible
# 2. Consider @WebMvcTest for controller tests instead of @SpringBootTest
# 3. Use test containers for database tests efficiently
```

### Runtime Issues

**Problem**: Application fails to start - "Port already in use"
```bash
# Solution
# 1. Change port in application.yml: server.port=8081
# 2. Or kill process using port 8080
```

**Problem**: Database connection fails
```bash
# Solution
# 1. Verify database is running (docker-compose up -d db)
# 2. Check connection settings in application.yml
# 3. Ensure database schema exists
```

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5
**Compatible with**: Java 17+, Spring Boot 3.x, Maven 3.8+, Gradle 8+
