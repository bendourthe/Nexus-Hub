# Java Test Structure & Infrastructure

## Objective
Design and implement a robust test infrastructure with optimal framework configuration (JUnit 5, Maven/Gradle), logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices in Java projects.

## Implementation Checklist

### Test Framework Setup
- [ ] JUnit 5 (Jupiter) configured
- [ ] Maven or Gradle build configuration
- [ ] Test dependencies added (AssertJ, Mockito)
- [ ] Test discovery rules established
- [ ] Parallel execution configured

### Directory Structure
- [ ] Maven/Gradle standard layout implemented
- [ ] Test type separation (unit/integration/e2e) organized
- [ ] Naming conventions documented
- [ ] Resource directories created
- [ ] Test categories configured

### Fixture Infrastructure
- [ ] @BeforeEach/@AfterEach hooks established
- [ ] @BeforeAll/@AfterAll class-level setup
- [ ] Test instance lifecycle configured
- [ ] Extension model utilized
- [ ] Common fixtures centralized

### Test Utilities
- [ ] Custom assertions created
- [ ] Test data builders implemented
- [ ] Object mothers defined
- [ ] Helper classes established
- [ ] Utility documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Test Infrastructure Setup

Please design and implement a comprehensive test infrastructure for this Java project following this protocol:

## Phase 1: Framework Selection & Configuration

1. **Test Framework**: JUnit 5 (Jupiter)
   - Modern, extensible architecture
   - Rich assertion library
   - Excellent IDE integration
   - Parallel test execution

2. **Install Dependencies**

   **Maven** (`pom.xml`):
   ```xml
   <properties>
       <junit.version>5.10.1</junit.version>
       <mockito.version>5.7.0</mockito.version>
       <assertj.version>3.24.2</assertj.version>
       <maven.surefire.version>3.2.2</maven.surefire.version>
   </properties>

   <dependencies>
       <!-- JUnit 5 -->
       <dependency>
           <groupId>org.junit.jupiter</groupId>
           <artifactId>junit-jupiter</artifactId>
           <version>${junit.version}</version>
           <scope>test</scope>
       </dependency>

       <!-- Mockito -->
       <dependency>
           <groupId>org.mockito</groupId>
           <artifactId>mockito-core</artifactId>
           <version>${mockito.version}</version>
           <scope>test</scope>
       </dependency>
       <dependency>
           <groupId>org.mockito</groupId>
           <artifactId>mockito-junit-jupiter</artifactId>
           <version>${mockito.version}</version>
           <scope>test</scope>
       </dependency>

       <!-- AssertJ -->
       <dependency>
           <groupId>org.assertj</groupId>
           <artifactId>assertj-core</artifactId>
           <version>${assertj.version}</version>
           <scope>test</scope>
       </dependency>
   </dependencies>

   <build>
       <plugins>
           <plugin>
               <groupId>org.apache.maven.plugins</groupId>
               <artifactId>maven-surefire-plugin</artifactId>
               <version>${maven.surefire.version}</version>
               <configuration>
                   <includes>
                       <include>**/*Test.java</include>
                       <include>**/*Tests.java</include>
                   </includes>
                   <parallel>methods</parallel>
                   <threadCount>4</threadCount>
               </configuration>
           </plugin>
       </plugins>
   </build>
   ```

   **Gradle** (`build.gradle`):
   ```groovy
   dependencies {
       testImplementation 'org.junit.jupiter:junit-jupiter:5.10.1'
       testImplementation 'org.mockito:mockito-core:5.7.0'
       testImplementation 'org.mockito:mockito-junit-jupiter:5.7.0'
       testImplementation 'org.assertj:assertj-core:3.24.2'
       testImplementation 'org.testcontainers:junit-jupiter:1.19.3'
   }

   test {
       useJUnitPlatform()
       maxParallelForks = Runtime.runtime.availableProcessors().intdiv(2) ?: 1
       testLogging {
           events "passed", "skipped", "failed"
           exceptionFormat "full"
       }
   }
   ```

3. **JUnit Configuration** (`junit-platform.properties`):
   ```properties
   # Parallel execution
   junit.jupiter.execution.parallel.enabled=true
   junit.jupiter.execution.parallel.mode.default=concurrent
   junit.jupiter.execution.parallel.config.strategy=dynamic
   junit.jupiter.execution.parallel.config.dynamic.factor=0.5

   # Display names
   junit.jupiter.displayname.generator.default=\
     org.junit.jupiter.api.DisplayNameGenerator$ReplaceUnderscores

   # Test instance lifecycle
   junit.jupiter.testinstance.lifecycle.default=per_method
   ```

## Phase 2: Directory Structure Design

**Maven Standard Layout**:
```
project/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/myapp/
│   │   │       ├── domain/
│   │   │       │   ├── User.java
│   │   │       │   └── Product.java
│   │   │       ├── service/
│   │   │       │   ├── UserService.java
│   │   │       │   └── ProductService.java
│   │   │       ├── repository/
│   │   │       │   ├── UserRepository.java
│   │   │       │   └── ProductRepository.java
│   │   │       └── util/
│   │   │           └── Validators.java
│   │   └── resources/
│   │       └── application.properties
│   │
│   └── test/
│       ├── java/
│       │   └── com/example/myapp/
│       │       ├── unit/                      # Unit tests
│       │       │   ├── service/
│       │       │   │   ├── UserServiceTest.java
│       │       │   │   └── ProductServiceTest.java
│       │       │   └── util/
│       │       │       └── ValidatorsTest.java
│       │       │
│       │       ├── integration/               # Integration tests
│       │       │   ├── repository/
│       │       │   │   ├── UserRepositoryIT.java
│       │       │   │   └── ProductRepositoryIT.java
│       │       │   └── api/
│       │       │       └── UserControllerIT.java
│       │       │
│       │       ├── e2e/                       # End-to-end tests
│       │       │   └── UserWorkflowE2ETest.java
│       │       │
│       │       ├── fixtures/                  # Test fixtures
│       │       │   ├── UserFixtures.java
│       │       │   └── ProductFixtures.java
│       │       │
│       │       ├── builders/                  # Test data builders
│       │       │   ├── UserBuilder.java
│       │       │   └── ProductBuilder.java
│       │       │
│       │       ├── helpers/                   # Test utilities
│       │       │   ├── CustomAssertions.java
│       │       │   └── TestDataGenerator.java
│       │       │
│       │       └── config/                    # Test configuration
│       │           └── TestConfig.java
│       │
│       └── resources/
│           ├── application-test.properties
│           ├── test-data.sql
│           └── fixtures/
│               └── sample-data.json
│
├── pom.xml
└── junit-platform.properties
```

## Phase 3: Test Infrastructure Implementation

1. **Base Test Classes**

   ```java
   // AbstractUnitTest.java
   package com.example.myapp;

   import org.junit.jupiter.api.BeforeEach;
   import org.junit.jupiter.api.extension.ExtendWith;
   import org.mockito.junit.jupiter.MockitoExtension;

   /**
    * Base class for unit tests with Mockito support.
    */
   @ExtendWith(MockitoExtension.class)
   public abstract class AbstractUnitTest {

       @BeforeEach
       void setUpBase() {
           // Common setup for all unit tests
       }
   }
   ```

   ```java
   // AbstractIntegrationTest.java
   package com.example.myapp;

   import org.junit.jupiter.api.Tag;
   import org.springframework.boot.test.context.SpringBootTest;
   import org.springframework.test.context.ActiveProfiles;

   /**
    * Base class for integration tests with Spring context.
    */
   @SpringBootTest
   @ActiveProfiles("test")
   @Tag("integration")
   public abstract class AbstractIntegrationTest {

       // Common integration test setup
   }
   ```

2. **Test Fixtures**

   ```java
   // UserFixtures.java
   package com.example.myapp.fixtures;

   import com.example.myapp.domain.User;
   import java.time.LocalDateTime;
   import java.util.concurrent.atomic.AtomicLong;

   /**
    * Provides test fixtures for User domain.
    */
   public class UserFixtures {

       private static final AtomicLong ID_GENERATOR = new AtomicLong(1);

       public static User createUser() {
           return createUser("testuser");
       }

       public static User createUser(String username) {
           long id = ID_GENERATOR.getAndIncrement();
           return User.builder()
                   .id(id)
                   .username(username)
                   .email(username + "@example.com")
                   .firstName("Test")
                   .lastName("User")
                   .active(true)
                   .createdAt(LocalDateTime.now())
                   .build();
       }

       public static User createInactiveUser() {
           return createUser("inactive")
                   .toBuilder()
                   .active(false)
                   .build();
       }
   }
   ```

3. **Builder Pattern**

   ```java
   // UserBuilder.java
   package com.example.myapp.builders;

   import com.example.myapp.domain.User;
   import java.time.LocalDateTime;

   /**
    * Test data builder for User objects.
    */
   public class UserBuilder {

       private Long id = 1L;
       private String username = "testuser";
       private String email = "test@example.com";
       private String firstName = "Test";
       private String lastName = "User";
       private boolean active = true;
       private LocalDateTime createdAt = LocalDateTime.now();

       public UserBuilder withId(Long id) {
           this.id = id;
           return this;
       }

       public UserBuilder withUsername(String username) {
           this.username = username;
           return this;
       }

       public UserBuilder withEmail(String email) {
           this.email = email;
           return this;
       }

       public UserBuilder inactive() {
           this.active = false;
           return this;
       }

       public User build() {
           return User.builder()
                   .id(id)
                   .username(username)
                   .email(email)
                   .firstName(firstName)
                   .lastName(lastName)
                   .active(active)
                   .createdAt(createdAt)
                   .build();
       }

       public static UserBuilder aUser() {
           return new UserBuilder();
       }
   }

   // Usage:
   // User admin = aUser().withUsername("admin").inactive().build();
   ```

4. **Custom Assertions**

   ```java
   // CustomAssertions.java
   package com.example.myapp.helpers;

   import com.example.myapp.domain.User;
   import org.assertj.core.api.AbstractAssert;

   /**
    * Custom AssertJ assertions for domain objects.
    */
   public class UserAssert extends AbstractAssert<UserAssert, User> {

       protected UserAssert(User user) {
           super(user, UserAssert.class);
       }

       public static UserAssert assertThat(User user) {
           return new UserAssert(user);
       }

       public UserAssert hasUsername(String username) {
           isNotNull();
           if (!actual.getUsername().equals(username)) {
               failWithMessage("Expected username to be <%s> but was <%s>",
                       username, actual.getUsername());
           }
           return this;
       }

       public UserAssert isActive() {
           isNotNull();
           if (!actual.isActive()) {
               failWithMessage("Expected user to be active but was not");
           }
           return this;
       }

       public UserAssert hasValidEmail() {
           isNotNull();
           String email = actual.getEmail();
           if (!email.matches("^[A-Za-z0-9+_.-]+@(.+)$")) {
               failWithMessage("Expected valid email but was <%s>", email);
           }
           return this;
       }
   }

   // Usage:
   // assertThat(user).hasUsername("alice").isActive().hasValidEmail();
   ```

5. **JUnit 5 Extensions**

   ```java
   // TimingExtension.java
   package com.example.myapp.helpers;

   import org.junit.jupiter.api.extension.*;
   import java.util.logging.Logger;

   /**
    * JUnit extension to measure test execution time.
    */
   public class TimingExtension implements
           BeforeTestExecutionCallback,
           AfterTestExecutionCallback {

       private static final Logger logger = Logger.getLogger(TimingExtension.class.getName());

       private static final String START_TIME = "start time";

       @Override
       public void beforeTestExecution(ExtensionContext context) {
           getStore(context).put(START_TIME, System.currentTimeMillis());
       }

       @Override
       public void afterTestExecution(ExtensionContext context) {
           long startTime = getStore(context).remove(START_TIME, long.class);
           long duration = System.currentTimeMillis() - startTime;

           logger.info(String.format("Test %s took %d ms",
                   context.getDisplayName(), duration));
       }

       private ExtensionContext.Store getStore(ExtensionContext context) {
           return context.getStore(ExtensionContext.Namespace.create(
                   getClass(), context.getRequiredTestMethod()));
       }
   }

   // Usage:
   // @ExtendWith(TimingExtension.class)
   // class MyTest { ... }
   ```

## Phase 4: Test Execution

1. **Maven Commands**

   ```bash
   # Run all tests
   mvn test

   # Run specific test class
   mvn test -Dtest=UserServiceTest

   # Run specific test method
   mvn test -Dtest=UserServiceTest#shouldCreateUser

   # Run tests matching pattern
   mvn test -Dtest="*ServiceTest"

   # Run integration tests only
   mvn verify -P integration-tests

   # Skip tests
   mvn install -DskipTests
   ```

2. **Gradle Commands**

   ```bash
   # Run all tests
   ./gradlew test

   # Run specific test class
   ./gradlew test --tests UserServiceTest

   # Run tests matching pattern
   ./gradlew test --tests '*Service*'

   # Run integration tests
   ./gradlew integrationTest

   # Generate test report
   ./gradlew test jacocoTestReport
   ```

## Output Format

### Infrastructure Summary
- **Test Framework**: JUnit 5 (Jupiter)
- **Build Tool**: Maven/Gradle
- **Total Test Categories**: Unit, Integration, E2E
- **Parallel Execution**: Enabled
- **Mock Framework**: Mockito
- **Assertion Library**: AssertJ

### Configuration Files
- **pom.xml** or **build.gradle**: Dependencies and plugins
- **junit-platform.properties**: JUnit configuration
- **Base test classes**: AbstractUnitTest, AbstractIntegrationTest

### Fixtures and Builders
- **UserFixtures**: Standard user test data
- **UserBuilder**: Fluent builder for complex scenarios
- **Custom Assertions**: Domain-specific assertions

### Test Execution
```bash
mvn test              # All tests
mvn test -Dtest=*IT   # Integration tests
./gradlew test        # Gradle tests
```

### Best Practices
- Clear separation of test types
- Reusable fixtures and builders
- Custom assertions for readability
- Parallel execution for speed
- Proper test lifecycle management
~~~

## Output Format

The AI assistant should deliver comprehensive Java test infrastructure with JUnit 5, proper Maven/Gradle configuration, test fixtures, builders, custom assertions, and execution strategies.
