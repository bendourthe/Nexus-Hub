# CLAUDE.md - Java Development System Instructions
*Condensed system prompt for Claude Code - Optimized for Java development*

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


# 2. Project Architecture
---

## Standard Spring Boot Application Structure

```
project-name/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/company/project/
│   │   │       ├── Application.java
│   │   │       ├── config/
│   │   │       ├── controller/
│   │   │       ├── service/
│   │   │       ├── repository/
│   │   │       ├── model/
│   │   │       ├── exception/
│   │   │       └── util/
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       └── db/migration/
│   └── test/
│       └── java/
│           └── com/company/project/
├── target/
├── pom.xml
├── CHANGELOG.md
├── README.md
└── .gitignore
```

## Project Initialization Sequence

1. **Generate project**: Use Spring Initializr (start.spring.io)
2. **Select dependencies**: Web, JPA, Database, Security
3. **Create directory structure** as outlined above
4. **Configure application.yml** with settings
5. **Create `.gitignore`** (target/, .idea/, *.iml)
6. **Create `CHANGELOG.md`** starting with version 0.1.0
7. **Create `README.md`** with setup instructions
8. **Set up database migrations** (Flyway or Liquibase)

## pom.xml Template
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>

    <groupId>com.company</groupId>
    <artifactId>project-name</artifactId>
    <version>0.1.0</version>
    <name>Project Name</name>

    <properties>
        <java.version>17</java.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
```


# 3. Code Standards
---

## Naming Conventions
```java
// Classes: PascalCase
public class UserService { }

// Methods: camelCase
public User getUserById(Long id) { }

// Constants: UPPER_SNAKE_CASE
private static final int MAX_RETRY_ATTEMPTS = 3;

// Packages: lowercase
package com.company.project.service;
```

## Class Structure Order
1. Static constants
2. Instance fields
3. Constructors
4. Public methods
5. Protected methods
6. Private methods
7. Static utility methods

## Import Organization
1. Java standard library
2. Third-party libraries (alphabetically)
3. Application imports (alphabetically)

## Modern Java Features

### Records
```java
public record UserDTO(
    Long id,
    String name,
    String email
) {
    public UserDTO {
        if (name == null || name.isBlank()) {
            throw new IllegalArgumentException("Name required");
        }
    }
}
```

### Pattern Matching
```java
if (shape instanceof Circle c) {
    return Math.PI * c.radius() * c.radius();
}

String status = switch (user.getRole()) {
    case ADMIN -> "Administrator";
    case USER -> "Regular User";
    default -> throw new IllegalArgumentException();
};
```

### Stream API
```java
return users.stream()
    .filter(User::isActive)
    .map(this::mapToDTO)
    .collect(Collectors.toList());
```

### Optional
```java
public Optional<User> findByEmail(String email) {
    return userRepository.findByEmail(email);
}

String city = userRepository.findById(id)
    .map(User::getAddress)
    .map(Address::getCity)
    .orElse("Unknown");
```

## Spring Boot Annotations

### Controller
```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<UserDTO> getUser(@PathVariable Long id) {
        return ResponseEntity.ok(userService.findById(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserDTO createUser(@Valid @RequestBody CreateUserRequest request) {
        return userService.create(request);
    }
}
```

### Service
```java
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
@Slf4j
public class UserServiceImpl implements UserService {

    private final UserRepository userRepository;

    @Override
    public UserDTO findById(Long id) {
        return userRepository.findById(id)
            .map(this::mapToDTO)
            .orElseThrow(() -> new UserNotFoundException(id));
    }

    @Override
    @Transactional
    public UserDTO create(CreateUserRequest request) {
        User user = User.builder()
            .name(request.name())
            .email(request.email())
            .build();
        return mapToDTO(userRepository.save(user));
    }
}
```

### Repository
```java
@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    @Query("SELECT u FROM User u WHERE u.active = true")
    List<User> findActiveUsers();
}
```

### Entity
```java
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(nullable = false, unique = true)
    private String email;

    @Enumerated(EnumType.STRING)
    private Role role;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
    }
}
```


# 4. Documentation Standards
---

## JavaDoc Templates

### Complex Methods
```java
/**
 * Processes user data with validation.
 *
 * @param request the user creation request
 * @param options additional options, may be null
 * @return the created user DTO
 * @throws ValidationException if data is invalid
 * @throws DuplicateEmailException if email exists
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */
public UserDTO processUserData(CreateUserRequest request, Options options) {
    // Implementation
}
```

### Simple Methods
```java
/**
 * Calculates total price with tax.
 *
 * @param items list of item prices
 * @return total price with tax
 */
public double calculateTotal(List<Double> items) {
    return items.stream().mapToDouble(Double::doubleValue).sum() * 1.1;
}
```

## README.md Structure
```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features]

## Overview
[2-3 sentence description]

## Technologies
- Java 17
- Spring Boot 3.2
- PostgreSQL
- Maven

## Installation

### Prerequisites
- Java 17+
- Maven 3.6+
- PostgreSQL 13+

### Setup
    ```bash
    git clone [repo-url]
    cd [project-name]
    mvn clean install
    ```

## Usage
    ```bash
    mvn spring-boot:run
    ```

## Testing
    ```bash
    mvn test
    ```
```

## CHANGELOG.md Structure
```markdown
# Changelog

## [Unreleased]
### Added
### Changed
### Fixed

## [X.Y.Z] - YYYY-MM-DD
### Added
- New features
### Changed
- Improvements
### Fixed
- Bug fixes
```


# 5. Testing Framework
---

## Test Structure

1. **Unit Tests**: Test methods in isolation
2. **Integration Tests**: Test with database
3. **Controller Tests**: Test REST endpoints
4. **E2E Tests**: Test complete flows

## JUnit 5 Test Template

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository userRepository;

    @InjectMocks
    private UserServiceImpl userService;

    private User testUser;

    @BeforeEach
    void setUp() {
        testUser = User.builder()
            .id(1L)
            .name("John Doe")
            .email("john@example.com")
            .build();
    }

    @Nested
    @DisplayName("findById()")
    class FindById {

        @Test
        @DisplayName("should return user when found")
        void shouldReturnUserWhenFound() {
            // Given
            when(userRepository.findById(1L))
                .thenReturn(Optional.of(testUser));

            // When
            UserDTO result = userService.findById(1L);

            // Then
            assertThat(result).isNotNull();
            assertThat(result.id()).isEqualTo(1L);
        }

        @Test
        @DisplayName("should throw when not found")
        void shouldThrowWhenNotFound() {
            // Given
            when(userRepository.findById(999L))
                .thenReturn(Optional.empty());

            // When/Then
            assertThatThrownBy(() -> userService.findById(999L))
                .isInstanceOf(UserNotFoundException.class);
        }
    }
}
```

## Integration Testing
```java
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldCreateUserAndReturn201() throws Exception {
        CreateUserRequest request = new CreateUserRequest(
            "Jane Doe",
            "jane@example.com"
        );

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.name").value("Jane Doe"));
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
[Scope]

### Prerequisites
- Java 17+
- Maven configured
- Database setup

### Subtask X: [Title]
**Objective**: [Goal]
**Time**: [15-45 min]

**Prompt**:
```
[Instructions]
Complete and pause.
```
```

### Quality Gates
- [ ] Code compiles
- [ ] Tests passing
- [ ] No warnings
- [ ] JavaDoc complete


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

3. Share any errors.
```

## Maven Commands

```bash
# Build
mvn clean install
mvn compile

# Testing
mvn test
mvn verify

# Run
mvn spring-boot:run

# Code quality
mvn checkstyle:check
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

1. **Assess**: "Changes might warrant version update"
2. **Request**: "Should I update to [version]?"
3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, docs
- **Minor (Y+1.0)**: New features
- **Major (X+1.0.0)**: Breaking changes

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**

Never suggest:
- `git add/commit/push`
- `git branch/merge`
- `git tag`
- `git init`

Only when requested:
```
Since you requested Git help:

1. Stage: git add src/
2. Commit: git commit -m "Add [feature]"
3. Push: git push origin [branch]
```


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
- [ ] Exception handling
- [ ] No code smells
- [ ] Tests included
- [ ] Performance considered
- [ ] Security checked

## Before Delivering Project
- [ ] Standard Spring Boot structure
- [ ] Maven configured
- [ ] Database migrations
- [ ] All config files
- [ ] Documentation complete
- [ ] Tests passing

---
