# CLAUDE.md - Java Development System Instructions
*Comprehensive system prompt for Claude Code - Optimized for Java/Spring Boot development*

---

# Quick Start for Common Tasks

## Section Usage Map
- **Bug Fix**: Sections 1, 3, 9
- **New Feature**: Sections 1-5, 7
- **Refactoring**: Sections 3, 6, 9
- **Project Setup**: All sections

## Task-Specific Quick Reference
- **Fix a method**: Focus sections 3, 9
- **New project**: Use sections 2, 4, 5
- **Code review**: Apply sections 3, 10

## Context-Aware Behavior
- **For utilities**: Minimal structure
- **For microservices**: Full Spring Boot architecture
- **For debugging**: Focus on problem-solving

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation
- Minimal testing setup
- Focus on core functionality

### Full Mode (for new projects)
- Complete Spring Boot architecture
- Comprehensive testing
- Full documentation

## Claude Code Terminal Commands
- **Run tests**: `claude run mvn test`
- **Build project**: `claude run mvn clean install`
- **Start application**: `claude run mvn spring-boot:run`
- **New project**: `claude init [project-name]`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding
- Never make assumptions about missing requirements
- Frame questions to gather specific technical requirements

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work
- Explain implementation details, reasoning, and coding concepts
- Enable learning through understanding, not copy-paste
- Reference documentation for non-obvious concepts

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions
- Analyze problems independently
- Compare alternatives and recommend best solution
- Clearly explain reasoning and trade-offs

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity
- **Code Modification**: Edit originals, don't create '_enhanced' versions
- **Codebase Cleanup**: Remove obsolete methods
- **Refactoring**: Consolidate duplicate logic

### Quality Assurance
- Review code for: quality, efficiency, best practices, security, performance
- If already optimal, confirm briefly with reasoning

### System Prompt Adherence
- **Periodically review these instructions** throughout long conversations
- Ensure compliance with all coding standards and workflows
- Reference specific sections when needed to maintain consistency
- If uncertain about a standard, explicitly consult the relevant section


# 2. Project Architecture
---

## Standard Spring Boot Application Structure

```
project-name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/company/project/
│   │   │       ├── Application.java          # Main entry point
│   │   │       ├── config/                   # Configuration classes
│   │   │       │   ├── SecurityConfig.java
│   │   │       │   ├── DatabaseConfig.java
│   │   │       │   └── WebConfig.java
│   │   │       ├── controller/               # REST controllers
│   │   │       │   └── UserController.java
│   │   │       ├── service/                  # Business logic
│   │   │       │   ├── UserService.java
│   │   │       │   └── impl/
│   │   │       │       └── UserServiceImpl.java
│   │   │       ├── repository/               # Data access
│   │   │       │   └── UserRepository.java
│   │   │       ├── model/                    # Domain entities
│   │   │       │   ├── entity/
│   │   │       │   │   └── User.java
│   │   │       │   └── dto/                  # Data Transfer Objects
│   │   │       │       ├── UserDTO.java
│   │   │       │       └── CreateUserRequest.java
│   │   │       ├── exception/                # Custom exceptions
│   │   │       │   ├── UserNotFoundException.java
│   │   │       │   └── GlobalExceptionHandler.java
│   │   │       └── util/                     # Utility classes
│   │   │           └── ValidationUtil.java
│   │   └── resources/
│   │       ├── application.yml               # Main configuration
│   │       ├── application-dev.yml           # Dev profile
│   │       ├── application-prod.yml          # Prod profile
│   │       ├── db/
│   │       │   └── migration/                # Flyway migrations
│   │       │       └── V1__init.sql
│   │       └── static/                       # Static resources
│   └── test/
│       ├── java/
│       │   └── com/company/project/
│       │       ├── controller/               # Controller tests
│       │       ├── service/                  # Service tests
│       │       ├── repository/               # Repository tests
│       │       └── integration/              # Integration tests
│       └── resources/
│           └── application-test.yml
├── target/                                   # Compiled output
├── .mvn/                                     # Maven wrapper
├── mvnw, mvnw.cmd                            # Maven wrapper scripts
├── pom.xml                                   # Maven configuration
├── CHANGELOG.md                              # Version history
├── README.md                                 # Project documentation
├── DEVLOG.md                                 # Development log
└── .gitignore                                # Git ignore rules
```

## Project Initialization Sequence

1. **Generate project**: Use Spring Initializr (start.spring.io) or `spring init`
2. **Select dependencies**: Web, JPA, Database, Security, etc.
3. **Create directory structure** as outlined above
4. **Configure application.yml** with database and server settings
5. **Create `.gitignore`** (target/, .idea/, *.iml, etc.)
6. **Create `CHANGELOG.md`** starting with version 0.1.0
7. **Create `README.md`** with setup instructions
8. **Create `DEVLOG.md`** with initial task list
9. **Set up database migrations** (Flyway or Liquibase)

## pom.xml Template (Maven)
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
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>

        <!-- Database -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Utilities -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>

        <!-- Testing -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

## application.yml Template
```yaml
spring:
  application:
    name: project-name

  datasource:
    url: jdbc:postgresql://localhost:5432/dbname
    username: ${DB_USERNAME:postgres}
    password: ${DB_PASSWORD:password}
    driver-class-name: org.postgresql.Driver

  jpa:
    hibernate:
      ddl-auto: validate
    show-sql: false
    properties:
      hibernate:
        format_sql: true
        dialect: org.hibernate.dialect.PostgreSQLDialect

  flyway:
    enabled: true
    locations: classpath:db/migration

server:
  port: 8080
  servlet:
    context-path: /api

logging:
  level:
    root: INFO
    com.company.project: DEBUG
```


# 3. Code Standards
---

## Java Style Guidelines

### Naming Conventions
```java
// Classes and Interfaces: PascalCase
public class UserService { }
public interface UserRepository { }

// Methods and variables: camelCase
public User getUserById(Long id) { }
private String userName;

// Constants: UPPER_SNAKE_CASE
public static final int MAX_RETRY_ATTEMPTS = 3;
private static final String DEFAULT_ERROR_MESSAGE = "Operation failed";

// Packages: lowercase with dots
package com.company.project.service.impl;

// Generics: Single uppercase letter or PascalCase
public class Repository<T, ID> { }
public class ResponseWrapper<TData> { }
```

### Class Structure Order
```java
public class UserService {
    // 1. Static constants
    private static final Logger log = LoggerFactory.getLogger(UserService.class);
    private static final int MAX_USERS = 1000;

    // 2. Instance fields (dependencies first, then state)
    private final UserRepository userRepository;
    private final EmailService emailService;
    private Map<Long, User> cache;

    // 3. Constructors
    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
        this.cache = new HashMap<>();
    }

    // 4. Public methods
    public User findById(Long id) {
        return userRepository.findById(id)
            .orElseThrow(() -> new UserNotFoundException(id));
    }

    // 5. Protected methods
    protected void clearCache() {
        cache.clear();
    }

    // 6. Private methods
    private void validateUser(User user) {
        if (user.getEmail() == null || user.getEmail().isEmpty()) {
            throw new ValidationException("Email is required");
        }
    }

    // 7. Static utility methods
    private static String formatUserName(String firstName, String lastName) {
        return String.format("%s %s", firstName, lastName);
    }
}
```

### Import Organization
```java
// 1. Java standard library
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

// 2. Third-party libraries (alphabetically by package)
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

// 3. Application imports (alphabetically by package)
import com.company.project.exception.UserNotFoundException;
import com.company.project.model.entity.User;
import com.company.project.repository.UserRepository;
```



### Comment Guidelines

**Placement and Style:**
- **Above code blocks**: Comments explain why, not just what
- **No inline comments**: Avoid same-line comments unless extremely clear
- **No meta-commentary**: Don't document editing history
- **No change tracking**: Never add comments like "changed value to 12" or "updated parameter"
- **JavaDoc for public APIs**: Use JavaDoc for all public methods and classes
- **Descriptive**: Focus on logic, decision reasoning, and non-obvious behavior

**Prohibited Comment Patterns:**
```java
// BAD: Don't document changes
int result = calculate(12);  // Changed from 10 to 12
String value = newValue;  // Updated to use newValue instead of oldValue

// GOOD: Explain reasoning
int result = calculate(12);  // Use 12 to match API rate limit threshold
String value = newValue;  // Cache invalidation requires fresh value
```

**Examples:**
```java
// Use binary search for O(log n) performance on sorted data
// This is critical for large datasets (>10k items)
int result = Collections.binarySearch(sortedList, target);

// Cache results to avoid expensive database queries during batch processing
// Database has 100 query/minute limit, caching prevents exceeding it
if (!cache.containsKey(key)) {
    cache.put(key, expensiveDatabaseQuery(key));
}

// Implement exponential backoff for rate-limited APIs
// Start with 1 second, double each retry up to 32 seconds max
for (int attempt = 0; attempt < maxRetries; attempt++) {
    int waitTime = Math.min((int) Math.pow(2, attempt), 32);
    Thread.sleep(waitTime * 1000);
}
```


### Modern Java Features (Java 17+)

#### Records (Java 14+)
```java
// ✅ Good - Use records for DTOs
public record UserDTO(
    Long id,
    String name,
    String email,
    LocalDateTime createdAt
) {
    // Compact constructor for validation
    public UserDTO {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name cannot be blank");
        }
    }

    // Additional methods if needed
    public String displayName() {
        return name.toUpperCase();
    }
}
```

#### Pattern Matching (Java 16+)
```java
// ✅ Good - Pattern matching for instanceof
public double calculateArea(Shape shape) {
    if (shape instanceof Circle c) {
        return Math.PI * c.radius() * c.radius();
    } else if (shape instanceof Rectangle r) {
        return r.width() * r.height();
    }
    throw new IllegalArgumentException("Unknown shape");
}

// ✅ Good - Switch expressions (Java 14+)
public String getUserStatus(User user) {
    return switch (user.getRole()) {
        case ADMIN -> "Administrator";
        case USER -> "Regular User";
        case GUEST -> "Guest";
        default -> throw new IllegalArgumentException("Unknown role");
    };
}
```

#### Stream API
```java
// ✅ Good - Functional approach with streams
public List<UserDTO> getActiveUsers() {
    return userRepository.findAll().stream()
        .filter(User::isActive)
        .filter(user -> user.getLastLogin().isAfter(LocalDateTime.now().minusDays(30)))
        .map(this::mapToDTO)
        .sorted(Comparator.comparing(UserDTO::name))
        .collect(Collectors.toList());
}

// ✅ Good - Parallel streams for CPU-intensive operations
public Map<String, Long> getUserCountByRole() {
    return userRepository.findAll().parallelStream()
        .collect(Collectors.groupingBy(
            user -> user.getRole().name(),
            Collectors.counting()
        ));
}
```

#### Optional
```java
// ✅ Good - Return Optional for nullable results
public Optional<User> findUserByEmail(String email) {
    return userRepository.findByEmail(email);
}

// ✅ Good - Optional chaining
public String getUserCity(Long userId) {
    return userRepository.findById(userId)
        .map(User::getAddress)
        .map(Address::getCity)
        .orElse("Unknown");
}

// ❌ Avoid - Don't use Optional for fields or parameters
private Optional<String> userName; // Bad
public void setName(Optional<String> name) { } // Bad
```

### Spring Boot Annotations

#### Controller Layer
```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
@Validated
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUserById(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserDTO createUser(@Valid @RequestBody CreateUserRequest request) {
        return userService.create(request);
    }

    @PutMapping("/{id}")
    public ResponseEntity<UserDTO> updateUser(
        @PathVariable Long id,
        @Valid @RequestBody UpdateUserRequest request
    ) {
        return ResponseEntity.ok(userService.update(id, request));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}
```

#### Service Layer
```java
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
@Slf4j
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public UserDTO findById(Long id) {
        log.debug("Finding user by id: {}", id);
        return userRepository.findById(id)
            .map(this::mapToDTO)
            .orElseThrow(() -> new UserNotFoundException(id));
    }

    @Override
    @Transactional
    public UserDTO create(CreateUserRequest request) {
        log.info("Creating new user with email: {}", request.email());

        validateUniqueEmail(request.email());

        User user = User.builder()
            .name(request.name())
            .email(request.email())
            .password(passwordEncoder.encode(request.password()))
            .role(Role.USER)
            .build();

        User saved = userRepository.save(user);
        return mapToDTO(saved);
    }

    private void validateUniqueEmail(String email) {
        if (userRepository.existsByEmail(email)) {
            throw new DuplicateEmailException(email);
        }
    }
}
```

#### Repository Layer
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    List<User> findByRole(Role role);

    @Query("SELECT u FROM User u WHERE u.active = true AND u.lastLogin > :date")
    List<User> findActiveUsersSince(@Param("date") LocalDateTime date);

    @Modifying
    @Query("UPDATE User u SET u.active = false WHERE u.id = :id")
    void deactivateUser(@Param("id") Long id);
}
```

### Entity Design
```java
@Entity
@Table(name = "users", indexes = {
    @Index(name = "idx_user_email", columnList = "email"),
    @Index(name = "idx_user_role", columnList = "role")
})
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, unique = true, length = 255)
    private String email;

    @Column(nullable = false)
    private String password;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Role role;

    @Column(name = "active", nullable = false)
    private Boolean active = true;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
```


# 4. Documentation Standards
---

## JavaDoc Templates

### Complex Methods
```java
/**
 * Processes user data with validation and transformation.
 *
 * <p>This method performs the following operations:
 * <ul>
 *   <li>Validates input data according to business rules</li>
 *   <li>Transforms data to the internal format</li>
 *   <li>Saves to database with transactional guarantees</li>
 * </ul>
 *
 * @param request the user creation request containing name, email, and password
 * @param options additional processing options, may be null
 * @return the created user data transfer object with generated ID
 * @throws ValidationException if the request data is invalid
 * @throws DuplicateEmailException if the email already exists
 * @throws DatabaseException if database operation fails
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @since 1.0
 * @see UserDTO
 * @see CreateUserRequest
 */
public UserDTO processUserData(CreateUserRequest request, ProcessOptions options)
    throws ValidationException, DuplicateEmailException, DatabaseException {
    // Implementation
}
```

### Simple Methods
```java
/**
 * Calculates the total price including tax.
 *
 * @param items list of item prices
 * @return total price with tax applied
 */
public double calculateTotal(List<Double> items) {
    return items.stream().mapToDouble(Double::doubleValue).sum() * 1.1;
}
```

### Class Documentation
```java
/**
 * Service layer for user management operations.
 *
 * <p>This service handles all business logic related to user entities,
 * including CRUD operations, validation, and business rules enforcement.
 *
 * <p>All methods in this service are transactional unless otherwise specified.
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @version 1.0
 * @since 0.1.0
 */
@Service
@Transactional
public class UserService {
    // Implementation
}
```

## README.md Structure
```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features/changes]

## Overview
[2-3 sentence description]

## Features
- [Core capabilities]

## Technologies
- Java 17
- Spring Boot 3.2
- PostgreSQL
- Maven

## Installation

### Prerequisites
- Java 17 or higher
- Maven 3.6+
- PostgreSQL 13+

### Setup
    ```bash
    git clone <REPO_URL>
    cd [project-name]
    mvn clean install
    ```

**Note**: Your repository URL is stored in `.git/config`. To retrieve it:

```bash
git config --get remote.origin.url
```

### Configuration
Create `application-local.yml`:
    ```yaml
    spring:
      datasource:
        url: jdbc:postgresql://localhost:5432/mydb
        username: postgres
        password: password
    ```

## Usage
    ```bash
    mvn spring-boot:run
    ```

## Testing
    ```bash
    mvn test
    mvn verify  # Integration tests
    ```

## API Documentation
After starting the application, visit:
- Swagger UI: http://localhost:8080/swagger-ui.html
- API Docs: http://localhost:8080/v3/api-docs
```

## CHANGELOG.md Structure
```markdown
# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]
### Added
### Changed
### Fixed
### Removed

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Improvements

### Fixed
- Bug fixes

### Removed
- Deprecated items
```


# 5. Testing Framework
---

## Test Structure

1. **Unit Tests**: Test individual methods in isolation
2. **Integration Tests**: Test database and external dependencies
3. **Controller Tests**: Test REST endpoints with MockMvc
4. **End-to-End Tests**: Test complete user flows

## JUnit 5 Test Template

```java
/**
 * Test suite for UserService.
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @Mock
    private PasswordEncoder passwordEncoder;

    @InjectMocks
    private UserServiceImpl userService;

    private User testUser;
    private CreateUserRequest createRequest;

    @BeforeEach
    void setUp() {
        testUser = User.builder()
            .id(1L)
            .name("John Doe")
            .email("john@example.com")
            .role(Role.USER)
            .active(true)
            .build();

        createRequest = new CreateUserRequest("John Doe", "john@example.com", "password");
    }

    @Nested
    @DisplayName("findById()")
    class FindById {

        @Test
        @DisplayName("should return user when found")
        void shouldReturnUserWhenFound() {
            // Given
            when(userRepository.findById(1L)).thenReturn(Optional.of(testUser));

            // When
            UserDTO result = userService.findById(1L);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.id()).isEqualTo(1L);
            assertThat(result.name()).isEqualTo("John Doe");
            verify(userRepository).findById(1L);
        }

        @Test
        @DisplayName("should throw exception when user not found")
        void shouldThrowExceptionWhenUserNotFound() {
            // Given
            when(userRepository.findById(999L)).thenReturn(Optional.empty());

            // When/Then
            assertThatThrownBy(() -> userService.findById(999L))
                .isInstanceOf(UserNotFoundException.class)
                .hasMessage("User not found with id: 999");
        }
    }

    @Nested
    @DisplayName("create()")
    class Create {

        @Test
        @DisplayName("should create user successfully")
        void shouldCreateUserSuccessfully() {
            // Given
            when(userRepository.existsByEmail(anyString())).thenReturn(false);
            when(passwordEncoder.encode(anyString())).thenReturn("encodedPassword");
            when(userRepository.save(any(User.class))).thenReturn(testUser);

            // When
            UserDTO result = userService.create(createRequest);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.email()).isEqualTo("john@example.com");
            verify(userRepository).save(any(User.class));
        }

        @Test
        @DisplayName("should throw exception for duplicate email")
        void shouldThrowExceptionForDuplicateEmail() {
            // Given
            when(userRepository.existsByEmail("john@example.com")).thenReturn(true);

            // When/Then
            assertThatThrownBy(() -> userService.create(createRequest))
                .isInstanceOf(DuplicateEmailException.class);
            verify(userRepository, never()).save(any(User.class));
        }
    }

    @Test
    @DisplayName("should handle batch operations efficiently")
    @Timeout(value = 2, unit = TimeUnit.SECONDS)
    void shouldHandleBatchOperationsEfficiently() {
        // Test performance-critical operations
    }

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "invalid-email", "@example.com"})
    @DisplayName("should reject invalid email formats")
    void shouldRejectInvalidEmailFormats(String invalidEmail) {
        createRequest = new CreateUserRequest("John Doe", invalidEmail, "password");

        assertThatThrownBy(() -> userService.create(createRequest))
            .isInstanceOf(ValidationException.class);
    }
}
```

## Integration Testing
```java
@SpringBootTest
@AutoConfigureMockMvc
@Sql(scripts = "/test-data.sql", executionPhase = Sql.ExecutionPhase.BEFORE_TEST_METHOD)
@Sql(scripts = "/cleanup.sql", executionPhase = Sql.ExecutionPhase.AFTER_TEST_METHOD)
class UserControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    @DisplayName("should create user and return 201")
    void shouldCreateUserAndReturn201() throws Exception {
        CreateUserRequest request = new CreateUserRequest(
            "Jane Doe",
            "jane@example.com",
            "password123"
        );

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("Jane Doe"))
            .andExpect(jsonPath("$.email").value("jane@example.com"))
            .andExpect(jsonPath("$.id").exists());
    }
}
```


# 6. Development Workflow
---

## Task Breakdown

### When to Use
- Projects >30 minutes
- Multi-component applications
- Complex features
- Integration tasks

### Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope]

### Prerequisites
- Java 17+ installed
- Maven configured
- Database setup

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Outputs]
**Time**: [15-45 min]

**Prompt**:
```
[Instructions]
[Success criteria]

Complete and pause. Confirm before proceeding.
```
```

### Quality Gates
- [ ] Code compiles
- [ ] Tests passing
- [ ] No SonarLint warnings
- [ ] JavaDoc complete

## Iterative Testing Protocol

**CRITICAL: Test-Driven Problem Solving**

When implementing new features, fixing bugs, or troubleshooting issues, follow this iterative protocol:

### 1. Create Temporary Test Scripts
- Create test files in `src/test/java/temp/` directory
- Name descriptively: `TempFeatureValidationTest.java`, `TempBugReproductionTest.java`
- Write challenging tests that thoroughly validate the solution
- Include edge cases and error conditions

### 2. Implement Solution
- Write or modify code to address the issue
- Follow all code standards and best practices
- Document approach in DEVLOG.md

### 3. Run Tests and Iterate
- Execute the temporary test script using Maven/Gradle
- If tests FAIL:
  - Analyze failure reasons
  - Document iteration in DEVLOG.md
  - Modify implementation
  - Repeat until tests pass
- If tests PASS:
  - Verify solution completeness
  - Proceed to cleanup

### 4. Clean Up Temporary Tests
- **Delete all files** in `src/test/java/temp/` after successful implementation
- Move any valuable test cases to permanent test suites if needed
- Document final solution in DEVLOG.md

### Example Workflow
```markdown
## DEVLOG.md Entry

### Feature: User Authentication
**Iteration 1**: Created src/test/java/temp/TempAuthValidationTest.java
- Tests failed: Password validation too weak
- Solution: Enhanced regex pattern in ValidationUtil

**Iteration 2**: Re-ran tests
- Tests failed: Edge case with special characters
- Solution: Added character escaping in password encoder

**Iteration 3**: Final run
- All tests passed ✅
- Deleted src/test/java/temp/TempAuthValidationTest.java
- Moved 3 test cases to src/test/java/service/UserServiceTest.java
```

**Benefits:**
- Ensures solutions actually work before claiming completion
- Documents the problem-solving process
- Prevents premature declarations of success
- Creates robust, well-tested code
- Maintains clean repository (no temporary test clutter)





# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Pattern:
```
Please run in your terminal:

1. Clean and install:
   mvn clean install

2. Run tests:
   mvn test

3. Share any errors for assistance.
```

## Maven Commands

```bash
# Build
mvn clean install
mvn clean package
mvn compile

# Testing
mvn test
mvn verify  # Includes integration tests
mvn test -Dtest=UserServiceTest

# Run application
mvn spring-boot:run
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# Code quality
mvn checkstyle:check
mvn pmd:check
mvn spotbugs:check

# Dependencies
mvn dependency:tree
mvn versions:display-dependency-updates
```

## Gradle Commands (if used)

```bash
# Build
./gradlew build
./gradlew clean build

# Testing
./gradlew test
./gradlew integrationTest

# Run
./gradlew bootRun
```


# 8. Version Control
---

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:
- Modify CHANGELOG.md versions
- Update pom.xml version
- Change README.md versions
- Create tags/releases

### Version Protocol

1. **Assess**: "Changes might warrant version update from X.Y.Z"
2. **Request**: "Should I update to [version]? Or handle manually?"
3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, docs
- **Minor (Y+1.0)**: New features
- **Major (X+1.0.0)**: Breaking changes

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**


# 9. Implementation Examples
---

## Code Fix Request

**Structure:**
1. Analyze issue
2. Implement fix
3. Explain improvements
4. Provide integration steps

## Project Planning

**Structure:**
1. Break down components
2. Recommend architecture
3. Create subtask breakdown
4. Provide implementation guidance


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] Compiles without errors
- [ ] Follows Java conventions
- [ ] JavaDoc present
- [ ] Proper exception handling
- [ ] No code smells
- [ ] Tests included
- [ ] Performance considered
- [ ] Security checked

## Before Delivering Project
- [ ] Standard Spring Boot structure
- [ ] Maven/Gradle configured
- [ ] Database migrations setup
- [ ] All config files present
- [ ] Documentation complete
- [ ] Tests passing

---
