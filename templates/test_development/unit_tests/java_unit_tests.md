---
template_id: java_unit_tests
template_name: Unit Tests - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: test_development
phase: unit_tests
phase_number: 2
difficulty: intermediate
estimated_time_hours: 3-6
prerequisites:
  - test_development/test_structure/java_test_structure.md
related_templates:
  - test_development/test_cases/java_test_cases.md
tools:
  - junit (5.11.3)
  - maven
  - gradle
tags:
  - test-development
  - testing
  - java
---
# Java Unit Tests - Comprehensive Implementation Guide

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                             ► │ ● CURRENT
│ Phase 3: Test Cases Development                    ► │ [NEXT]
│ Phase 4: Mocks & Fixtures                                ► │ 
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 1 (Test Structure Setup) should be completed first
**Next Step:** Phase 3 (Test Cases Development)

---


## Objective

Develop a comprehensive unit testing strategy for Java applications using JUnit 5 framework, focusing on test isolation, fast execution, and thorough coverage of individual components following FIRST principles and AAA patterns.

---

## Output Directory Structure

All generated files should be saved to the following directory structure:

```
${OUTPUT_DIR}/
├── templates/           # Reusable test templates and helper scripts
├── assets/             # Diagrams, visualizations, and reference images
└── exports/            # Final documentation and reports
```

---

## Implementation Checklist

### Test Foundation
- [ ] JUnit 5 framework overview completed
- [ ] Test directory structure established (src/test/java)
- [ ] Naming conventions documented
- [ ] Maven/Gradle test configuration created
- [ ] Test base classes and utilities created

### Test Patterns
- [ ] Pure method tests implemented
- [ ] Class and interface tests created
- [ ] Exception testing patterns established
- [ ] Parametrized test examples created
- [ ] Nested test examples documented

### Test Quality
- [ ] Test independence verified
- [ ] Execution time profiled (<1s per test)
- [ ] Mock usage patterns documented (Mockito)
- [ ] Edge case coverage completed
- [ ] Anti-patterns guide created

### Documentation
- [ ] Unit test implementation guide completed (20-30 pages)
- [ ] 50+ example test methods documented
- [ ] Test quality checklist created
- [ ] Code review guidelines established

---

## Prompt Template

Copy the prompt below into your AI assistant to generate comprehensive unit testing guidance:

~~~markdown
# Java Unit Testing Implementation - Comprehensive Guide

## Context
I need comprehensive guidance for implementing unit tests in a Java application using JUnit 5 as the primary framework. Generate a complete implementation guide covering principles, patterns, and practical examples.

## CRITICAL: Output Directory Setup

Before starting, create this exact directory structure:

```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

Replace `${OUTPUT_DIR}` with your desired output location (e.g., `unit_tests_java_output`).

---

## Repository Information

To include accurate repository information in documentation:

```bash
git config --get remote.origin.url
```

---

## Phase 1: Unit Testing Fundamentals

### 1.1 What Makes a Good Unit Test

Provide detailed explanation of:

**FIRST Principles:**
- **Fast** - Unit tests should execute in milliseconds (target: <100ms per test)
  - Why speed matters for developer productivity
  - How to identify slow tests using JUnit's `@Timeout` annotation
  - Techniques to optimize test execution time
  - Avoiding unnecessary I/O operations and database calls

- **Independent** - Tests must not depend on each other or shared state
  - How to verify test independence
  - Running tests in random order
  - Avoiding test pollution with proper cleanup
  - Using `@BeforeEach` and `@AfterEach` for isolation
  - Understanding test execution lifecycle

- **Repeatable** - Same results every time, in any environment
  - Dealing with time-dependent code using `Clock` abstraction
  - Handling randomness with controlled seeds
  - Environment isolation techniques
  - Using test doubles for external dependencies

- **Self-validating** - Clear pass/fail without manual inspection
  - Writing clear assertions with JUnit assertions
  - Meaningful error messages with custom assertion messages
  - Using AssertJ for fluent assertions
  - Avoiding System.out.println debugging in tests

- **Timely** - Written before or alongside production code
  - Test-Driven Development (TDD) with Java
  - Benefits of early test writing
  - Maintaining test coverage during refactoring
  - Using Maven/Gradle test goals for continuous testing

**AAA Pattern (Arrange-Act-Assert):**
```java
@Test
void calculateDiscount_withValidInputs_returnsDiscountedPrice() {
    // Arrange - Set up test data and preconditions
    double originalPrice = 100.0;
    double discountRate = 0.20;
    PriceCalculator calculator = new PriceCalculator();

    // Act - Execute the method being tested
    double finalPrice = calculator.calculateDiscount(originalPrice, discountRate);

    // Assert - Verify the expected outcome
    assertEquals(80.0, finalPrice, 0.001);
    assertEquals(20.0, calculator.getLastDiscount(), 0.001);
}
```

Explain:
- Why separating these phases improves readability
- How to handle tests with complex setup
- When to use helper methods or `@BeforeEach` for arrangement
- Dealing with multiple assertions (when appropriate)
- Using private helper methods for test utilities

### 1.2 Unit vs Integration vs E2E Testing

Create a comparison table:

| Aspect | Unit Test | Integration Test | E2E Test |
|--------|-----------|------------------|----------|
| **Scope** | Single method/class | Multiple classes/modules | Entire application |
| **Dependencies** | Mocked/stubbed | Real (some mocked) | Real |
| **Speed** | <100ms | <1s | Seconds to minutes |
| **Isolation** | Complete | Partial | None |
| **Failure Reason** | Specific method | Component interaction | System behavior |
| **Maintenance** | Easy | Moderate | Complex |
| **Cost** | Low | Medium | High |
| **Framework** | JUnit 5 | JUnit 5 + TestContainers | Selenium, RestAssured |

Provide guidance on:
- When to write unit tests vs integration tests
- The testing pyramid concept (70% unit, 20% integration, 10% E2E)
- How to identify if a test is truly a unit test
- Converting integration tests to unit tests
- Java-specific testing challenges (null handling, checked exceptions)

### 1.3 Common Unit Test Anti-Patterns

Document these anti-patterns with examples:

**Anti-Pattern 1: Testing Implementation Instead of Behavior**
```java
// BAD - Tests implementation details
@Test
void testSortUsesQuickSort() {
    Sorter sorter = new Sorter();
    List<Integer> result = sorter.sort(Arrays.asList(3, 1, 2));
    assertEquals("quicksort", sorter.getAlgorithmUsed()); // Implementation detail
}

// GOOD - Tests behavior
@Test
void sort_returnsAscendingOrder() {
    Sorter sorter = new Sorter();
    List<Integer> result = sorter.sort(Arrays.asList(3, 1, 2));
    assertEquals(Arrays.asList(1, 2, 3), result); // Behavior
}
```

**Anti-Pattern 2: Multiple Unrelated Assertions**
```java
// BAD - Tests multiple unrelated concerns
@Test
void testUserOperations() {
    User user = new User("John", "john@example.com");
    assertEquals("John", user.getName());
    assertEquals("john@example.com", user.getEmail());
    assertNotNull(user.getCreatedAt());
    assertTrue(user.validateEmail());
    assertEquals("John", user.toMap().get("name"));
}

// GOOD - Separate tests for separate concerns
@Test
void constructor_setsName() {
    User user = new User("John", "john@example.com");
    assertEquals("John", user.getName());
}

@Test
void constructor_setsEmail() {
    User user = new User("John", "john@example.com");
    assertEquals("john@example.com", user.getEmail());
}

@Test
void validateEmail_withValidFormat_returnsTrue() {
    User user = new User("John", "john@example.com");
    assertTrue(user.validateEmail());
}
```

**Anti-Pattern 3: Slow Tests**
```java
// BAD - Slow test with unnecessary delays
@Test
void processData_withDelay() throws InterruptedException {
    DataProcessor processor = new DataProcessor();
    Thread.sleep(1000); // Unnecessary delay
    List<Integer> result = processor.process(Arrays.asList(1, 2, 3));
    assertEquals(Arrays.asList(2, 4, 6), result);
}

// GOOD - Fast test with no delays
@Test
void processData_doublesEachElement() {
    DataProcessor processor = new DataProcessor();
    List<Integer> result = processor.process(Arrays.asList(1, 2, 3));
    assertEquals(Arrays.asList(2, 4, 6), result);
}
```

**Anti-Pattern 4: Test Interdependencies**
```java
// BAD - Tests depend on execution order
class UserWorkflowTest {
    private User user;

    @Test
    @Order(1)
    void test1_createUser() {
        user = new User("John");
        assertEquals("John", user.getName());
    }

    @Test
    @Order(2)
    void test2_updateUser() {
        user.setName("Jane"); // Depends on test1
        assertEquals("Jane", user.getName());
    }
}

// GOOD - Independent tests
class UserWorkflowTest {
    @Test
    void createUser_setsName() {
        User user = new User("John");
        assertEquals("John", user.getName());
    }

    @Test
    void setName_updatesUserName() {
        User user = new User("John"); // Create fresh instance
        user.setName("Jane");
        assertEquals("Jane", user.getName());
    }
}
```

**Anti-Pattern 5: Excessive Mocking**
```java
// BAD - Mocking too much, testing mock behavior
@Test
void calculateTotal_withExcessiveMocks() {
    Calculator mockCalculator = Mockito.mock(Calculator.class);
    when(mockCalculator.add(anyInt(), anyInt())).thenReturn(10);
    when(mockCalculator.multiply(anyInt(), anyInt())).thenReturn(20);

    Service service = new Service(mockCalculator);
    service.calculateTotal(Arrays.asList(1, 2, 3));

    verify(mockCalculator).add(anyInt(), anyInt()); // Testing mock, not real code
}

// GOOD - Test real logic, mock only external dependencies
@Test
void calculateTotal_sumsAllElements() {
    Calculator calculator = new Calculator(); // Real calculator
    Service service = new Service(calculator);
    int result = service.calculateTotal(Arrays.asList(1, 2, 3));
    assertEquals(6, result); // Testing real behavior
}
```

**Anti-Pattern 6: Unclear Test Names**
```java
// BAD - Unclear what is being tested
@Test void testUser1() {}
@Test void testEdgeCase() {}
@Test void testFoo() {}

// GOOD - Clear, descriptive names
@Test void constructor_withValidEmail_succeeds() {}
@Test void divide_byZero_throwsArithmeticException() {}
@Test void findUser_withEmptyList_returnsNull() {}
```

Provide guidance for identifying and fixing each anti-pattern.

---

## Phase 2: Test Organization and Structure

### 2.1 Directory Structure for Unit Tests

Recommend this Maven structure:

```
project/
├── src/
│   ├── main/
│   │   └── java/
│   │       └── com/
│   │           └── example/
│   │               ├── Calculator.java
│   │               ├── User.java
│   │               └── service/
│   │                   ├── PaymentService.java
│   │                   └── NotificationService.java
│   └── test/
│       └── java/
│           └── com/
│               └── example/
│                   ├── CalculatorTest.java
│                   ├── UserTest.java
│                   └── service/
│                       ├── PaymentServiceTest.java
│                       └── NotificationServiceTest.java
├── pom.xml
└── build.gradle
```

Explain:
- Why mirror the source structure in test directory
- Benefits of separating unit/integration tests (using annotations or packages)
- When to deviate from this structure
- How Maven/Gradle discover and run tests
- Using test resource directories for test data

### 2.2 Test Naming Conventions

Provide detailed naming guidelines:

**Class Naming:**
- `<ClassName>Test` - Standard pattern
- Examples: `CalculatorTest`, `UserServiceTest`
- Use the exact name of the class being tested with "Test" suffix

**Method Naming Patterns:**

Pattern 1: `methodName_stateUnderTest_expectedBehavior`
```java
@Test
void calculateDiscount_withValidRate_returnsDiscountedPrice() {}

@Test
void divide_byZero_throwsArithmeticException() {}

@Test
void findUser_withEmptyList_returnsNull() {}
```

Pattern 2: `should<ExpectedBehavior>When<StateUnderTest>`
```java
@Test
void shouldReturnDiscountedPriceWhenValidRateProvided() {}

@Test
void shouldThrowExceptionWhenDividingByZero() {}

@Test
void shouldReturnNullWhenListIsEmpty() {}
```

Pattern 3: Given-When-Then (BDD style)
```java
@Test
void givenValidUser_whenSaving_thenSucceeds() {}

@Test
void givenInvalidEmail_whenCreatingUser_thenThrowsException() {}
```

**Why This Matters:**
- Test names serve as documentation
- Failed tests clearly indicate what went wrong
- No need to read test code to understand purpose
- Test names appear in reports and CI logs
- Helps with test organization and maintenance

### 2.3 JUnit 5 Annotations

Provide comprehensive annotation guide:

```java
import org.junit.jupiter.api.*;

/**
 * Example test class demonstrating JUnit 5 annotations
 */
class LifecycleTest {

    @BeforeAll
    static void setupAll() {
        // Runs once before all tests in this class
        // Must be static
        // Use for expensive setup (database connections, etc.)
        System.out.println("@BeforeAll");
    }

    @BeforeEach
    void setup() {
        // Runs before each test method
        // Use for creating fresh test objects
        System.out.println("@BeforeEach");
    }

    @Test
    void testMethod1() {
        // Regular test method
        System.out.println("Test 1");
    }

    @Test
    void testMethod2() {
        // Another test method
        System.out.println("Test 2");
    }

    @AfterEach
    void tearDown() {
        // Runs after each test method
        // Use for cleanup (closing resources, etc.)
        System.out.println("@AfterEach");
    }

    @AfterAll
    static void tearDownAll() {
        // Runs once after all tests in this class
        // Must be static
        // Use for cleanup of expensive resources
        System.out.println("@AfterAll");
    }

    @Disabled("Not yet implemented")
    @Test
    void disabledTest() {
        // This test will be skipped
    }

    @Test
    @Timeout(value = 100, unit = TimeUnit.MILLISECONDS)
    void testWithTimeout() {
        // Fails if execution takes longer than 100ms
    }

    @Tag("fast")
    @Test
    void fastTest() {
        // Can be filtered using tags
    }

    @Tag("slow")
    @Test
    void slowTest() {
        // Can be filtered using tags
    }
}
```

### 2.4 Maven Configuration

Provide comprehensive `pom.xml` example:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <groupId>com.example</groupId>
    <artifactId>unit-tests-example</artifactId>
    <version>1.0.0</version>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>

        <!-- Dependency versions -->
        <junit.version>5.10.0</junit.version>
        <mockito.version>5.5.0</mockito.version>
        <assertj.version>3.24.2</assertj.version>
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

        <!-- AssertJ for fluent assertions -->
        <dependency>
            <groupId>org.assertj</groupId>
            <artifactId>assertj-core</artifactId>
            <version>${assertj.version}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <!-- Maven Surefire Plugin for running tests -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.1.2</version>
                <configuration>
                    <!-- Run tests in parallel -->
                    <parallel>methods</parallel>
                    <threadCount>4</threadCount>

                    <!-- Include/exclude tests by tags -->
                    <groups>fast</groups>
                    <excludedGroups>slow</excludedGroups>
                </configuration>
            </plugin>

            <!-- JaCoCo for code coverage -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>0.8.10</version>
                <executions>
                    <execution>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>check</id>
                        <goals>
                            <goal>check</goal>
                        </goals>
                        <configuration>
                            <rules>
                                <rule>
                                    <element>PACKAGE</element>
                                    <limits>
                                        <limit>
                                            <counter>LINE</counter>
                                            <value>COVEREDRATIO</value>
                                            <minimum>0.80</minimum>
                                        </limit>
                                    </limits>
                                </rule>
                            </rules>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
</project>
```

Alternative Gradle configuration (`build.gradle`):

```groovy
plugins {
    id 'java'
    id 'jacoco'
}

group = 'com.example'
version = '1.0.0'

sourceCompatibility = '17'
targetCompatibility = '17'

repositories {
    mavenCentral()
}

dependencies {
    // JUnit 5
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'

    // Mockito
    testImplementation 'org.mockito:mockito-core:5.5.0'
    testImplementation 'org.mockito:mockito-junit-jupiter:5.5.0'

    // AssertJ
    testImplementation 'org.assertj:assertj-core:3.24.2'
}

test {
    useJUnitPlatform()

    // Run tests in parallel
    maxParallelForks = Runtime.runtime.availableProcessors()

    // Filter tests by tags
    useJUnitPlatform {
        includeTags 'fast'
        excludeTags 'slow'
    }

    // Test logging
    testLogging {
        events "passed", "skipped", "failed"
        exceptionFormat "full"
    }
}

jacoco {
    toolVersion = "0.8.10"
}

jacocoTestReport {
    dependsOn test
    reports {
        html.required = true
        xml.required = true
        csv.required = false
    }
}

jacocoTestCoverageVerification {
    violationRules {
        rule {
            limit {
                minimum = 0.80
            }
        }
    }
}

check.dependsOn jacocoTestCoverageVerification
```

---

## Phase 3: Testing Different Component Types

### 3.1 Testing Pure Methods

Pure methods (no side effects, deterministic) are easiest to test.

**Example Class:**
```java
package com.example;

/**
 * Calculator for price discount calculations
 */
public class Calculator {

    /**
     * Calculate discounted price
     * @param price Original price
     * @param discountRate Discount rate (0.0 to 1.0)
     * @return Final price after discount
     * @throws IllegalArgumentException if price is negative or discount rate is invalid
     */
    public double calculateDiscount(double price, double discountRate) {
        if (price < 0) {
            throw new IllegalArgumentException("Price cannot be negative");
        }
        if (discountRate < 0 || discountRate > 1) {
            throw new IllegalArgumentException("Discount rate must be between 0 and 1");
        }

        return price * (1 - discountRate);
    }
}
```

**Comprehensive Tests:**
```java
package com.example;

import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @Nested
    @DisplayName("calculateDiscount with valid inputs")
    class ValidInputTests {

        @Test
        @DisplayName("no discount returns original price")
        void noDiscount_returnsOriginalPrice() {
            double result = calculator.calculateDiscount(100.0, 0.0);
            assertEquals(100.0, result, 0.001);
        }

        @Test
        @DisplayName("full discount returns zero")
        void fullDiscount_returnsZero() {
            double result = calculator.calculateDiscount(100.0, 1.0);
            assertEquals(0.0, result, 0.001);
        }

        @Test
        @DisplayName("20% discount calculates correctly")
        void twentyPercentDiscount_calculatesCorrectly() {
            double result = calculator.calculateDiscount(100.0, 0.20);
            assertEquals(80.0, result, 0.001);
        }

        @Test
        @DisplayName("50% discount calculates correctly")
        void fiftyPercentDiscount_calculatesCorrectly() {
            double result = calculator.calculateDiscount(200.0, 0.50);
            assertEquals(100.0, result, 0.001);
        }

        @Test
        @DisplayName("small price with discount")
        void smallPriceWithDiscount_calculatesCorrectly() {
            double result = calculator.calculateDiscount(5.0, 0.10);
            assertEquals(4.5, result, 0.001);
        }

        @Test
        @DisplayName("large price with discount")
        void largePriceWithDiscount_calculatesCorrectly() {
            double result = calculator.calculateDiscount(10000.0, 0.15);
            assertEquals(8500.0, result, 0.001);
        }

        @Test
        @DisplayName("zero price returns zero")
        void zeroPrice_returnsZero() {
            double result = calculator.calculateDiscount(0.0, 0.50);
            assertEquals(0.0, result, 0.001);
        }
    }

    @Nested
    @DisplayName("calculateDiscount with invalid inputs")
    class InvalidInputTests {

        @Test
        @DisplayName("negative price throws IllegalArgumentException")
        void negativePrice_throwsException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> calculator.calculateDiscount(-100.0, 0.20)
            );
            assertEquals("Price cannot be negative", exception.getMessage());
        }

        @Test
        @DisplayName("discount rate below zero throws exception")
        void discountRateBelowZero_throwsException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> calculator.calculateDiscount(100.0, -0.10)
            );
            assertTrue(exception.getMessage().contains("between 0 and 1"));
        }

        @Test
        @DisplayName("discount rate above one throws exception")
        void discountRateAboveOne_throwsException() {
            assertThrows(
                IllegalArgumentException.class,
                () -> calculator.calculateDiscount(100.0, 1.5)
            );
        }
    }

    @Nested
    @DisplayName("calculateDiscount edge cases")
    class EdgeCaseTests {

        @ParameterizedTest(name = "price={0}, discount={1}, expected={2}")
        @CsvSource({
            "100.0, 0.10, 90.0",
            "50.0, 0.20, 40.0",
            "200.0, 0.25, 150.0",
            "75.0, 0.333, 50.025"
        })
        void variousDiscountCombinations(double price, double discount, double expected) {
            double result = calculator.calculateDiscount(price, discount);
            assertEquals(expected, result, 0.01);
        }
    }
}
```

**Key Principles:**
- Test happy path (normal inputs)
- Test edge cases (boundaries: 0%, 100%, 0 price)
- Test error conditions (negative price, invalid discount)
- Use delta for floating-point comparison
- Use `@ParameterizedTest` for multiple similar cases
- Use `@Nested` classes to group related tests
- Use `@DisplayName` for readable test names

### 3.2 Testing Classes with State

**Example Class:**
```java
package com.example;

import java.time.LocalDateTime;
import java.util.regex.Pattern;

/**
 * Represents a user in the system
 */
public class User {
    private static final Pattern EMAIL_PATTERN =
        Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$");

    private String name;
    private String email;
    private Integer age;
    private LocalDateTime createdAt;
    private boolean active;

    /**
     * Create a new user
     * @param name User name
     * @param email User email
     * @param age User age (optional)
     * @throws IllegalArgumentException if validation fails
     */
    public User(String name, String email, Integer age) {
        if (name == null || name.isEmpty()) {
            throw new IllegalArgumentException("Name cannot be empty");
        }
        if (!isValidEmail(email)) {
            throw new IllegalArgumentException("Invalid email format");
        }
        if (age != null && age < 0) {
            throw new IllegalArgumentException("Age cannot be negative");
        }

        this.name = name;
        this.email = email;
        this.age = age;
        this.createdAt = LocalDateTime.now();
        this.active = true;
    }

    public User(String name, String email) {
        this(name, email, null);
    }

    public String getName() {
        return name;
    }

    public String getEmail() {
        return email;
    }

    public Integer getAge() {
        return age;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public boolean isActive() {
        return active;
    }

    public void deactivate() {
        this.active = false;
    }

    public void activate() {
        this.active = true;
    }

    private boolean isValidEmail(String email) {
        return email != null && EMAIL_PATTERN.matcher(email).matches();
    }
}
```

**Comprehensive Tests:**
```java
package com.example;

import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

import java.time.LocalDateTime;

import static org.junit.jupiter.api.Assertions.*;

class UserTest {

    @Nested
    @DisplayName("Constructor tests")
    class ConstructorTests {

        @Test
        @DisplayName("constructor with all parameters sets all fields")
        void constructor_withAllParameters_setsAllFields() {
            User user = new User("John Doe", "john@example.com", 30);

            assertEquals("John Doe", user.getName());
            assertEquals("john@example.com", user.getEmail());
            assertEquals(30, user.getAge());
            assertTrue(user.isActive());
        }

        @Test
        @DisplayName("constructor without age sets age to null")
        void constructor_withoutAge_setsAgeToNull() {
            User user = new User("Jane Doe", "jane@example.com");

            assertEquals("Jane Doe", user.getName());
            assertEquals("jane@example.com", user.getEmail());
            assertNull(user.getAge());
        }

        @Test
        @DisplayName("constructor sets createdAt timestamp")
        void constructor_setsCreatedAtTimestamp() {
            LocalDateTime before = LocalDateTime.now();
            User user = new User("John", "john@example.com");
            LocalDateTime after = LocalDateTime.now();

            assertNotNull(user.getCreatedAt());
            assertTrue(user.getCreatedAt().isAfter(before.minusSeconds(1)));
            assertTrue(user.getCreatedAt().isBefore(after.plusSeconds(1)));
        }

        @Test
        @DisplayName("constructor with empty name throws exception")
        void constructor_withEmptyName_throwsException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> new User("", "john@example.com")
            );
            assertEquals("Name cannot be empty", exception.getMessage());
        }

        @Test
        @DisplayName("constructor with null name throws exception")
        void constructor_withNullName_throwsException() {
            assertThrows(
                IllegalArgumentException.class,
                () -> new User(null, "john@example.com")
            );
        }

        @Test
        @DisplayName("constructor with invalid email throws exception")
        void constructor_withInvalidEmail_throwsException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> new User("John", "invalid-email")
            );
            assertEquals("Invalid email format", exception.getMessage());
        }

        @Test
        @DisplayName("constructor with negative age throws exception")
        void constructor_withNegativeAge_throwsException() {
            assertThrows(
                IllegalArgumentException.class,
                () -> new User("John", "john@example.com", -5)
            );
        }

        @ParameterizedTest(name = "valid email: {0}")
        @ValueSource(strings = {
            "user@example.com",
            "first.last@example.com",
            "user+tag@example.co.uk",
            "user123@subdomain.example.com"
        })
        void constructor_withValidEmailFormats_succeeds(String email) {
            User user = new User("John", email);
            assertEquals(email, user.getEmail());
        }

        @ParameterizedTest(name = "invalid email: {0}")
        @ValueSource(strings = {
            "invalid",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com"
        })
        void constructor_withInvalidEmailFormats_throwsException(String email) {
            assertThrows(
                IllegalArgumentException.class,
                () -> new User("John", email)
            );
        }
    }

    @Nested
    @DisplayName("Activation methods tests")
    class ActivationTests {

        private User user;

        @BeforeEach
        void setUp() {
            user = new User("John", "john@example.com");
        }

        @Test
        @DisplayName("deactivate sets isActive to false")
        void deactivate_setsIsActiveToFalse() {
            user.deactivate();
            assertFalse(user.isActive());
        }

        @Test
        @DisplayName("activate sets isActive to true")
        void activate_setsIsActiveToTrue() {
            user.deactivate();
            user.activate();
            assertTrue(user.isActive());
        }

        @Test
        @DisplayName("multiple deactivations keep user inactive")
        void multipleDeactivations_keepUserInactive() {
            user.deactivate();
            user.deactivate();
            assertFalse(user.isActive());
        }

        @Test
        @DisplayName("multiple activations keep user active")
        void multipleActivations_keepUserActive() {
            user.activate();
            user.activate();
            assertTrue(user.isActive());
        }
    }

    @Nested
    @DisplayName("Property tests")
    class PropertyTests {

        @Test
        @DisplayName("getName returns correct value")
        void getName_returnsCorrectValue() {
            User user = new User("John", "john@example.com");
            assertEquals("John", user.getName());
        }

        @Test
        @DisplayName("getEmail returns correct value")
        void getEmail_returnsCorrectValue() {
            User user = new User("John", "john@example.com");
            assertEquals("john@example.com", user.getEmail());
        }

        @Test
        @DisplayName("getAge returns correct value when set")
        void getAge_returnsCorrectValue_whenSet() {
            User user = new User("John", "john@example.com", 25);
            assertEquals(25, user.getAge());
        }

        @Test
        @DisplayName("getAge returns null when not set")
        void getAge_returnsNull_whenNotSet() {
            User user = new User("John", "john@example.com");
            assertNull(user.getAge());
        }

        @Test
        @DisplayName("isActive returns true initially")
        void isActive_returnsTrue_initially() {
            User user = new User("John", "john@example.com");
            assertTrue(user.isActive());
        }
    }
}
```

**Key Principles:**
- Group related tests with `@Nested` classes
- Use `@BeforeEach` for common setup
- Test each method independently
- Test state changes
- Test both valid and invalid inputs
- Verify exception messages
- Use parametrized tests for multiple similar cases
- Use descriptive display names

### 3.3 Testing Interfaces and Abstract Classes

**Example Interface and Implementation:**
```java
package com.example;

import java.util.List;

/**
 * Data processor interface
 */
public interface DataProcessor {
    List<Integer> process(List<Integer> data);
    String getProcessorName();
}

/**
 * Concrete implementation that doubles each element
 */
public class DoublingProcessor implements DataProcessor {

    @Override
    public List<Integer> process(List<Integer> data) {
        if (data == null) {
            throw new IllegalArgumentException("Data cannot be null");
        }
        return data.stream()
            .map(n -> n * 2)
            .toList();
    }

    @Override
    public String getProcessorName() {
        return "Doubling Processor";
    }
}

/**
 * Abstract base class for processors
 */
public abstract class BaseProcessor implements DataProcessor {
    protected int callCount = 0;

    @Override
    public List<Integer> process(List<Integer> data) {
        callCount++;
        return processInternal(data);
    }

    protected abstract List<Integer> processInternal(List<Integer> data);

    public int getCallCount() {
        return callCount;
    }
}
```

**Comprehensive Tests:**
```java
package com.example;

import org.junit.jupiter.api.*;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class DoublingProcessorTest {

    private DoublingProcessor processor;

    @BeforeEach
    void setUp() {
        processor = new DoublingProcessor();
    }

    @Nested
    @DisplayName("process method tests")
    class ProcessMethodTests {

        @Test
        @DisplayName("process doubles each element")
        void process_doublesEachElement() {
            List<Integer> input = Arrays.asList(1, 2, 3);
            List<Integer> result = processor.process(input);
            assertEquals(Arrays.asList(2, 4, 6), result);
        }

        @Test
        @DisplayName("process handles empty list")
        void process_handlesEmptyList() {
            List<Integer> result = processor.process(Collections.emptyList());
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("process handles single element")
        void process_handlesSingleElement() {
            List<Integer> result = processor.process(Collections.singletonList(5));
            assertEquals(Collections.singletonList(10), result);
        }

        @Test
        @DisplayName("process handles negative numbers")
        void process_handlesNegativeNumbers() {
            List<Integer> result = processor.process(Arrays.asList(-1, -2, -3));
            assertEquals(Arrays.asList(-2, -4, -6), result);
        }

        @Test
        @DisplayName("process handles zero")
        void process_handlesZero() {
            List<Integer> result = processor.process(Arrays.asList(0, 1, 0));
            assertEquals(Arrays.asList(0, 2, 0), result);
        }

        @Test
        @DisplayName("process with null throws exception")
        void process_withNull_throwsException() {
            assertThrows(
                IllegalArgumentException.class,
                () -> processor.process(null)
            );
        }
    }

    @Test
    @DisplayName("getProcessorName returns correct name")
    void getProcessorName_returnsCorrectName() {
        assertEquals("Doubling Processor", processor.getProcessorName());
    }

    @Test
    @DisplayName("processor implements DataProcessor interface")
    void processorImplementsDataProcessorInterface() {
        assertTrue(processor instanceof DataProcessor);
    }
}

/**
 * Test base processor using concrete implementation
 */
class BaseProcessorTest {

    private static class TestProcessor extends BaseProcessor {
        @Override
        protected List<Integer> processInternal(List<Integer> data) {
            return data.stream().map(n -> n + 1).toList();
        }

        @Override
        public String getProcessorName() {
            return "Test Processor";
        }
    }

    private TestProcessor processor;

    @BeforeEach
    void setUp() {
        processor = new TestProcessor();
    }

    @Test
    @DisplayName("process increments call count")
    void process_incrementsCallCount() {
        assertEquals(0, processor.getCallCount());

        processor.process(Arrays.asList(1, 2, 3));
        assertEquals(1, processor.getCallCount());

        processor.process(Arrays.asList(4, 5));
        assertEquals(2, processor.getCallCount());
    }

    @Test
    @DisplayName("processInternal is called by process")
    void processInternal_isCalledByProcess() {
        List<Integer> result = processor.process(Arrays.asList(1, 2, 3));
        assertEquals(Arrays.asList(2, 3, 4), result);
    }
}
```

**Key Principles:**
- Test concrete implementations of interfaces
- Test abstract class behavior using concrete subclass
- Verify interface contract is fulfilled
- Test inherited behavior
- Use inner test classes for concrete implementations

### 3.4 Testing Exception Handling

**Example Class:**
```java
package com.example;

/**
 * Validator with multiple exception types
 */
public class Validator {

    public void validateAge(int age) {
        if (age < 0) {
            throw new IllegalArgumentException("Age cannot be negative");
        }
        if (age > 150) {
            throw new IllegalArgumentException("Age cannot exceed 150");
        }
    }

    public void validateEmail(String email) {
        if (email == null) {
            throw new NullPointerException("Email cannot be null");
        }
        if (email.isEmpty()) {
            throw new IllegalArgumentException("Email cannot be empty");
        }
        if (!email.contains("@")) {
            throw new IllegalArgumentException("Email must contain @");
        }
    }

    public void validatePositive(int number) throws Exception {
        if (number <= 0) {
            throw new Exception("Number must be positive");
        }
    }
}
```

**Comprehensive Tests:**
```java
package com.example;

import org.junit.jupiter.api.*;

import static org.junit.jupiter.api.Assertions.*;

class ValidatorTest {

    private Validator validator;

    @BeforeEach
    void setUp() {
        validator = new Validator();
    }

    @Nested
    @DisplayName("validateAge tests")
    class ValidateAgeTests {

        @Test
        @DisplayName("valid age does not throw exception")
        void validateAge_withValidAge_doesNotThrow() {
            assertDoesNotThrow(() -> validator.validateAge(25));
        }

        @Test
        @DisplayName("negative age throws IllegalArgumentException")
        void validateAge_withNegativeAge_throwsException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> validator.validateAge(-1)
            );
            assertEquals("Age cannot be negative", exception.getMessage());
        }

        @Test
        @DisplayName("age exceeding 150 throws IllegalArgumentException")
        void validateAge_withAgeOver150_throwsException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> validator.validateAge(151)
            );
            assertTrue(exception.getMessage().contains("150"));
        }

        @Test
        @DisplayName("boundary age 0 does not throw")
        void validateAge_withZero_doesNotThrow() {
            assertDoesNotThrow(() -> validator.validateAge(0));
        }

        @Test
        @DisplayName("boundary age 150 does not throw")
        void validateAge_with150_doesNotThrow() {
            assertDoesNotThrow(() -> validator.validateAge(150));
        }
    }

    @Nested
    @DisplayName("validateEmail tests")
    class ValidateEmailTests {

        @Test
        @DisplayName("valid email does not throw exception")
        void validateEmail_withValidEmail_doesNotThrow() {
            assertDoesNotThrow(() -> validator.validateEmail("user@example.com"));
        }

        @Test
        @DisplayName("null email throws NullPointerException")
        void validateEmail_withNull_throwsNullPointerException() {
            NullPointerException exception = assertThrows(
                NullPointerException.class,
                () -> validator.validateEmail(null)
            );
            assertEquals("Email cannot be null", exception.getMessage());
        }

        @Test
        @DisplayName("empty email throws IllegalArgumentException")
        void validateEmail_withEmptyString_throwsIllegalArgumentException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> validator.validateEmail("")
            );
            assertEquals("Email cannot be empty", exception.getMessage());
        }

        @Test
        @DisplayName("email without @ throws IllegalArgumentException")
        void validateEmail_withoutAtSign_throwsException() {
            IllegalArgumentException exception = assertThrows(
                IllegalArgumentException.class,
                () -> validator.validateEmail("invalid.email.com")
            );
            assertTrue(exception.getMessage().contains("@"));
        }
    }

    @Nested
    @DisplayName("validatePositive tests")
    class ValidatePositiveTests {

        @Test
        @DisplayName("positive number does not throw exception")
        void validatePositive_withPositiveNumber_doesNotThrow() {
            assertDoesNotThrow(() -> validator.validatePositive(5));
        }

        @Test
        @DisplayName("zero throws Exception")
        void validatePositive_withZero_throwsException() {
            Exception exception = assertThrows(
                Exception.class,
                () -> validator.validatePositive(0)
            );
            assertEquals("Number must be positive", exception.getMessage());
        }

        @Test
        @DisplayName("negative number throws Exception")
        void validatePositive_withNegativeNumber_throwsException() {
            assertThrows(
                Exception.class,
                () -> validator.validatePositive(-5)
            );
        }
    }

    @Test
    @DisplayName("multiple validations can be chained")
    void multipleValidations_canBeChained() {
        assertAll(
            () -> assertDoesNotThrow(() -> validator.validateAge(25)),
            () -> assertDoesNotThrow(() -> validator.validateEmail("test@example.com")),
            () -> assertDoesNotThrow(() -> validator.validatePositive(10))
        );
    }
}
```

**Key Principles:**
- Use `assertThrows()` to verify exceptions are thrown
- Check exception type and message
- Use `assertDoesNotThrow()` for valid inputs
- Test different exception types
- Test exception messages contain useful information
- Use `assertAll()` for grouped assertions

### 3.5 Testing Collections and Streams

**Example Class:**
```java
package com.example;

import java.util.*;
import java.util.stream.Collectors;

/**
 * Collection utilities
 */
public class CollectionUtils {

    public static List<Integer> filterEven(List<Integer> numbers) {
        if (numbers == null) {
            return Collections.emptyList();
        }
        return numbers.stream()
            .filter(n -> n % 2 == 0)
            .collect(Collectors.toList());
    }

    public static Map<String, Integer> groupByLength(List<String> strings) {
        if (strings == null) {
            return Collections.emptyMap();
        }
        return strings.stream()
            .collect(Collectors.groupingBy(
                String::length,
                Collectors.collectingAndThen(Collectors.counting(), Long::intValue)
            ));
    }

    public static <T> List<T> removeDuplicates(List<T> list) {
        if (list == null) {
            return Collections.emptyList();
        }
        return new ArrayList<>(new LinkedHashSet<>(list));
    }

    public static OptionalDouble average(List<Integer> numbers) {
        if (numbers == null || numbers.isEmpty()) {
            return OptionalDouble.empty();
        }
        return numbers.stream()
            .mapToInt(Integer::intValue)
            .average();
    }
}
```

**Comprehensive Tests:**
```java
package com.example;

import org.junit.jupiter.api.*;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class CollectionUtilsTest {

    @Nested
    @DisplayName("filterEven tests")
    class FilterEvenTests {

        @Test
        @DisplayName("filters even numbers correctly")
        void filterEven_filtersEvenNumbers() {
            List<Integer> input = Arrays.asList(1, 2, 3, 4, 5, 6);
            List<Integer> result = CollectionUtils.filterEven(input);
            assertEquals(Arrays.asList(2, 4, 6), result);
        }

        @Test
        @DisplayName("returns empty list when no even numbers")
        void filterEven_withNoEvenNumbers_returnsEmptyList() {
            List<Integer> input = Arrays.asList(1, 3, 5, 7);
            List<Integer> result = CollectionUtils.filterEven(input);
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("returns empty list for empty input")
        void filterEven_withEmptyList_returnsEmptyList() {
            List<Integer> result = CollectionUtils.filterEven(Collections.emptyList());
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("returns empty list for null input")
        void filterEven_withNull_returnsEmptyList() {
            List<Integer> result = CollectionUtils.filterEven(null);
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("handles negative numbers")
        void filterEven_withNegativeNumbers_filtersCorrectly() {
            List<Integer> input = Arrays.asList(-2, -1, 0, 1, 2);
            List<Integer> result = CollectionUtils.filterEven(input);
            assertEquals(Arrays.asList(-2, 0, 2), result);
        }
    }

    @Nested
    @DisplayName("groupByLength tests")
    class GroupByLengthTests {

        @Test
        @DisplayName("groups strings by length")
        void groupByLength_groupsStringsByLength() {
            List<String> input = Arrays.asList("a", "bb", "ccc", "dd", "e");
            Map<String, Integer> result = CollectionUtils.groupByLength(input);

            assertEquals(2, result.get(1)); // "a", "e"
            assertEquals(2, result.get(2)); // "bb", "dd"
            assertEquals(1, result.get(3)); // "ccc"
        }

        @Test
        @DisplayName("returns empty map for empty list")
        void groupByLength_withEmptyList_returnsEmptyMap() {
            Map<String, Integer> result = CollectionUtils.groupByLength(Collections.emptyList());
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("returns empty map for null")
        void groupByLength_withNull_returnsEmptyMap() {
            Map<String, Integer> result = CollectionUtils.groupByLength(null);
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("handles single group")
        void groupByLength_withSameLength_createsSingleGroup() {
            List<String> input = Arrays.asList("aa", "bb", "cc");
            Map<String, Integer> result = CollectionUtils.groupByLength(input);

            assertEquals(1, result.size());
            assertEquals(3, result.get(2));
        }
    }

    @Nested
    @DisplayName("removeDuplicates tests")
    class RemoveDuplicatesTests {

        @Test
        @DisplayName("removes duplicate integers")
        void removeDuplicates_removesDuplicateIntegers() {
            List<Integer> input = Arrays.asList(1, 2, 2, 3, 3, 3, 4);
            List<Integer> result = CollectionUtils.removeDuplicates(input);
            assertEquals(Arrays.asList(1, 2, 3, 4), result);
        }

        @Test
        @DisplayName("preserves order of first occurrence")
        void removeDuplicates_preservesOrder() {
            List<String> input = Arrays.asList("c", "a", "b", "a", "c");
            List<String> result = CollectionUtils.removeDuplicates(input);
            assertEquals(Arrays.asList("c", "a", "b"), result);
        }

        @Test
        @DisplayName("returns empty list for empty input")
        void removeDuplicates_withEmptyList_returnsEmptyList() {
            List<Integer> result = CollectionUtils.removeDuplicates(Collections.emptyList());
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("returns empty list for null input")
        void removeDuplicates_withNull_returnsEmptyList() {
            List<Integer> result = CollectionUtils.removeDuplicates(null);
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("handles list with no duplicates")
        void removeDuplicates_withNoDuplicates_returnsSameList() {
            List<Integer> input = Arrays.asList(1, 2, 3, 4);
            List<Integer> result = CollectionUtils.removeDuplicates(input);
            assertEquals(input, result);
        }
    }

    @Nested
    @DisplayName("average tests")
    class AverageTests {

        @Test
        @DisplayName("calculates average correctly")
        void average_calculatesCorrectly() {
            List<Integer> input = Arrays.asList(10, 20, 30);
            OptionalDouble result = CollectionUtils.average(input);

            assertTrue(result.isPresent());
            assertEquals(20.0, result.getAsDouble(), 0.001);
        }

        @Test
        @DisplayName("returns empty for empty list")
        void average_withEmptyList_returnsEmpty() {
            OptionalDouble result = CollectionUtils.average(Collections.emptyList());
            assertFalse(result.isPresent());
        }

        @Test
        @DisplayName("returns empty for null")
        void average_withNull_returnsEmpty() {
            OptionalDouble result = CollectionUtils.average(null);
            assertFalse(result.isPresent());
        }

        @Test
        @DisplayName("handles single element")
        void average_withSingleElement_returnsThatElement() {
            List<Integer> input = Collections.singletonList(42);
            OptionalDouble result = CollectionUtils.average(input);

            assertTrue(result.isPresent());
            assertEquals(42.0, result.getAsDouble(), 0.001);
        }

        @Test
        @DisplayName("handles negative numbers")
        void average_withNegativeNumbers_calculatesCorrectly() {
            List<Integer> input = Arrays.asList(-10, 0, 10);
            OptionalDouble result = CollectionUtils.average(input);

            assertTrue(result.isPresent());
            assertEquals(0.0, result.getAsDouble(), 0.001);
        }
    }
}
```

**Key Principles:**
- Test stream operations thoroughly
- Test empty collections
- Test null inputs
- Test collection transformations
- Verify order preservation when important
- Test Optional handling

---

## Phase 4: Edge Cases and Error Handling

### 4.1 Boundary Value Testing

Test values at the edges of valid ranges:

```java
class BoundaryValueTest {

    @Test
    @DisplayName("minimum boundary (0)")
    void validateScore_withMinimumBoundary() {
        assertTrue(validateScore(0));
    }

    @Test
    @DisplayName("below minimum boundary (-1)")
    void validateScore_belowMinimumBoundary() {
        assertFalse(validateScore(-1));
    }

    @Test
    @DisplayName("maximum boundary (100)")
    void validateScore_withMaximumBoundary() {
        assertTrue(validateScore(100));
    }

    @Test
    @DisplayName("above maximum boundary (101)")
    void validateScore_aboveMaximumBoundary() {
        assertFalse(validateScore(101));
    }

    @Test
    @DisplayName("just inside minimum (1)")
    void validateScore_justInsideMinimum() {
        assertTrue(validateScore(1));
    }

    @Test
    @DisplayName("just inside maximum (99)")
    void validateScore_justInsideMaximum() {
        assertTrue(validateScore(99));
    }
}
```

### 4.2 Null Handling

Test behavior with null values:

```java
class NullHandlingTest {

    @Test
    @DisplayName("function with null argument returns null")
    void process_withNull_returnsNull() {
        assertNull(process(null));
    }

    @Test
    @DisplayName("function with null throws NullPointerException")
    void process_withNull_throwsNullPointerException() {
        assertThrows(NullPointerException.class, () -> process(null));
    }

    @Test
    @DisplayName("optional returns empty for null")
    void findUser_withNull_returnsEmptyOptional() {
        Optional<User> result = findUser(null);
        assertFalse(result.isPresent());
    }

    @Test
    @DisplayName("collection methods handle null gracefully")
    void collectionsHandleNullGracefully() {
        List<String> result = filterStrings(null);
        assertNotNull(result);
        assertTrue(result.isEmpty());
    }
}
```

### 4.3 Empty Collections

Test behavior with empty collections:

```java
class EmptyCollectionTest {

    @Test
    @DisplayName("empty list returns zero sum")
    void sum_withEmptyList_returnsZero() {
        assertEquals(0, sum(Collections.emptyList()));
    }

    @Test
    @DisplayName("empty map returns empty result")
    void process_withEmptyMap_returnsEmptyMap() {
        assertTrue(processMap(Collections.emptyMap()).isEmpty());
    }

    @Test
    @DisplayName("empty string throws IllegalArgumentException")
    void parse_withEmptyString_throwsException() {
        assertThrows(IllegalArgumentException.class, () -> parse(""));
    }

    @Test
    @DisplayName("empty set returns false")
    void hasElements_withEmptySet_returnsFalse() {
        assertFalse(hasElements(Collections.emptySet()));
    }
}
```

### 4.4 Testing with Mockito

**Example Service with Dependencies:**
```java
package com.example;

public interface UserRepository {
    User findById(Long id);
    void save(User user);
}

public class UserService {
    private final UserRepository repository;

    public UserService(UserRepository repository) {
        this.repository = repository;
    }

    public User getUserById(Long id) {
        if (id == null) {
            throw new IllegalArgumentException("ID cannot be null");
        }
        return repository.findById(id);
    }

    public void activateUser(Long id) {
        User user = repository.findById(id);
        if (user != null) {
            user.activate();
            repository.save(user);
        }
    }
}
```

**Comprehensive Tests with Mockito:**
```java
package com.example;

import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.*;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class UserServiceTest {

    @Mock
    private UserRepository repository;

    @InjectMocks
    private UserService service;

    @Test
    @DisplayName("getUserById calls repository with correct ID")
    void getUserById_callsRepositoryWithCorrectId() {
        User user = new User("John", "john@example.com");
        when(repository.findById(1L)).thenReturn(user);

        User result = service.getUserById(1L);

        assertEquals(user, result);
        verify(repository).findById(1L);
    }

    @Test
    @DisplayName("getUserById with null ID throws exception")
    void getUserById_withNullId_throwsException() {
        assertThrows(
            IllegalArgumentException.class,
            () -> service.getUserById(null)
        );

        verify(repository, never()).findById(any());
    }

    @Test
    @DisplayName("activateUser activates and saves user")
    void activateUser_activatesAndSavesUser() {
        User user = new User("John", "john@example.com");
        user.deactivate();
        when(repository.findById(1L)).thenReturn(user);

        service.activateUser(1L);

        assertTrue(user.isActive());
        verify(repository).findById(1L);
        verify(repository).save(user);
    }

    @Test
    @DisplayName("activateUser with non-existent user does nothing")
    void activateUser_withNonExistentUser_doesNothing() {
        when(repository.findById(999L)).thenReturn(null);

        service.activateUser(999L);

        verify(repository).findById(999L);
        verify(repository, never()).save(any());
    }

    @Test
    @DisplayName("repository is called correct number of times")
    void repositoryIsCalledCorrectNumberOfTimes() {
        when(repository.findById(anyLong())).thenReturn(null);

        service.getUserById(1L);
        service.getUserById(2L);
        service.getUserById(3L);

        verify(repository, times(3)).findById(anyLong());
    }

    @Test
    @DisplayName("uses argument captor to verify saved user")
    void usesArgumentCaptorToVerifySavedUser() {
        User user = new User("John", "john@example.com");
        when(repository.findById(1L)).thenReturn(user);

        service.activateUser(1L);

        ArgumentCaptor<User> userCaptor = ArgumentCaptor.forClass(User.class);
        verify(repository).save(userCaptor.capture());

        User savedUser = userCaptor.getValue();
        assertTrue(savedUser.isActive());
        assertEquals("John", savedUser.getName());
    }
}
```

**Key Principles:**
- Use `@ExtendWith(MockitoExtension.class)` for Mockito integration
- Use `@Mock` for mock objects
- Use `@InjectMocks` for the class under test
- Use `when().thenReturn()` for stubbing
- Use `verify()` to check method calls
- Use `ArgumentCaptor` for verifying arguments
- Use `never()`, `times()`, `atLeast()` for call verification

---

## Phase 5: Test Quality and Maintenance

### 5.1 AssertJ Fluent Assertions

**Example using AssertJ:**
```java
import static org.assertj.core.api.Assertions.*;

class AssertJExamplesTest {

    @Test
    @DisplayName("AssertJ basic assertions")
    void assertJBasicAssertions() {
        String name = "John";
        assertThat(name)
            .isNotNull()
            .isEqualTo("John")
            .startsWith("J")
            .endsWith("n")
            .hasSize(4);
    }

    @Test
    @DisplayName("AssertJ collection assertions")
    void assertJCollectionAssertions() {
        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

        assertThat(numbers)
            .isNotEmpty()
            .hasSize(5)
            .contains(3)
            .doesNotContain(6)
            .startsWith(1)
            .endsWith(5)
            .containsExactly(1, 2, 3, 4, 5)
            .containsExactlyInAnyOrder(5, 4, 3, 2, 1);
    }

    @Test
    @DisplayName("AssertJ exception assertions")
    void assertJExceptionAssertions() {
        assertThatThrownBy(() -> divide(10, 0))
            .isInstanceOf(ArithmeticException.class)
            .hasMessage("/ by zero")
            .hasNoCause();
    }

    @Test
    @DisplayName("AssertJ extracting fields")
    void assertJExtractingFields() {
        List<User> users = Arrays.asList(
            new User("John", "john@example.com"),
            new User("Jane", "jane@example.com")
        );

        assertThat(users)
            .extracting(User::getName)
            .containsExactly("John", "Jane");
    }

    @Test
    @DisplayName("AssertJ soft assertions")
    void assertJSoftAssertions() {
        SoftAssertions softly = new SoftAssertions();

        User user = new User("John", "john@example.com", 25);

        softly.assertThat(user.getName()).isEqualTo("John");
        softly.assertThat(user.getEmail()).isEqualTo("john@example.com");
        softly.assertThat(user.getAge()).isEqualTo(25);

        softly.assertAll(); // All assertions are checked
    }
}
```

### 5.2 Test Coverage with JaCoCo

**Running Coverage:**
```bash
# Run tests with coverage
mvn clean test

# Generate coverage report
mvn jacoco:report

# Check coverage thresholds
mvn jacoco:check

# View HTML report
open target/site/jacoco/index.html
```

### 5.3 Test Maintenance Checklist

Create a maintenance checklist:

- [ ] All tests pass independently
- [ ] Tests can run in any order
- [ ] Each test has clear, descriptive name
- [ ] Tests execute in <100ms each
- [ ] No duplicate setup code (use `@BeforeEach`)
- [ ] No test logic complexity (loops, conditionals)
- [ ] Clear assertions with helpful messages
- [ ] Tests are properly documented with `@DisplayName`
- [ ] Mocks are used appropriately (not excessively)
- [ ] Edge cases are covered
- [ ] Error conditions are tested
- [ ] Tests follow AAA pattern
- [ ] Test coverage is >80% for critical code
- [ ] No System.out.println statements in tests
- [ ] Proper use of `@Nested` for test organization
- [ ] Exception handling is tested thoroughly

---

## Output Format

Generate the following deliverables:

### 1. Unit Test Implementation Guide (20-30 pages)
Comprehensive document saved to `${OUTPUT_DIR}/exports/unit_test_implementation_guide.md` covering:
- FIRST principles detailed explanation
- AAA pattern with examples
- Unit vs Integration vs E2E comparison
- Test organization strategies
- JUnit 5 framework features
- Common anti-patterns and solutions

### 2. Test Examples Collection
File saved to `${OUTPUT_DIR}/exports/unit_test_examples.md` containing:
- 50+ example test methods
- Pure method tests
- Class and interface tests
- Exception handling tests
- Collection and stream tests
- Mockito examples
- Edge case examples

### 3. Test Templates
Files saved to `${OUTPUT_DIR}/templates/`:
- `UnitTestTemplate.java` - Basic test template
- `ClassTestTemplate.java` - Class testing template
- `MockitoTestTemplate.java` - Mockito patterns template
- `ParameterizedTestTemplate.java` - Parametrized test template
- `pom.xml` - Complete Maven configuration
- `build.gradle` - Complete Gradle configuration

### 4. Configuration Files
Files saved to `${OUTPUT_DIR}/templates/`:
- `pom.xml` - Complete Maven configuration with JUnit 5, Mockito, AssertJ, JaCoCo
- `build.gradle` - Complete Gradle configuration
- `junit-platform.properties` - JUnit configuration
- `mockito-extensions/` - Mockito extensions

### 5. Visual Assets
Files saved to `${OUTPUT_DIR}/assets/`:
- `first_principles_diagram.png` - Visual representation of FIRST principles
- `aaa_pattern_visualization.png` - AAA pattern flowchart
- `test_pyramid.png` - Testing pyramid diagram
- `test_organization_structure.png` - Maven directory structure diagram
- `junit5_lifecycle.png` - JUnit 5 test lifecycle diagram

### 6. Anti-Patterns Guide
File saved to `${OUTPUT_DIR}/exports/anti_patterns_guide.md`:
- Common anti-patterns with examples
- How to identify each anti-pattern
- Refactoring strategies
- Before/after examples
- Java-specific anti-patterns

### 7. Unit Test Quality Checklist
File saved to `${OUTPUT_DIR}/exports/unit_test_quality_checklist.md`:
- Test independence checklist
- Performance checklist
- Code quality checklist
- Maintenance checklist
- Review guidelines

### 8. Mockito Guide
File saved to `${OUTPUT_DIR}/exports/mockito_guide.md`:
- When to use mocks vs stubs
- Mockito annotation patterns
- Stubbing strategies
- Verification examples
- Mock cleanup best practices
- ArgumentCaptor usage

---

## File Output Instructions

**Critical:** Organize all generated files according to this structure:

```
${OUTPUT_DIR}/
├── templates/
│   ├── UnitTestTemplate.java
│   ├── ClassTestTemplate.java
│   ├── MockitoTestTemplate.java
│   ├── ParameterizedTestTemplate.java
│   ├── pom.xml
│   ├── build.gradle
│   └── junit-platform.properties
├── assets/
│   ├── first_principles_diagram.png
│   ├── aaa_pattern_visualization.png
│   ├── test_pyramid.png
│   ├── test_organization_structure.png
│   └── junit5_lifecycle.png
└── exports/
    ├── unit_test_implementation_guide.md (20-30 pages)
    ├── unit_test_examples.md (50+ tests)
    ├── anti_patterns_guide.md
    ├── unit_test_quality_checklist.md
    └── mockito_guide.md
```

**Directory Creation:**
Before generating content, ensure directories exist:
```bash
mkdir -p ${OUTPUT_DIR}/templates ${OUTPUT_DIR}/assets ${OUTPUT_DIR}/exports
```

---

## Verification Checklist

After generating all content, verify:

- [ ] All 8+ deliverables are created
- [ ] Files are saved to correct directories (templates/, assets/, exports/)
- [ ] Implementation guide is 20-30 pages
- [ ] 50+ test examples are included
- [ ] FIRST principles are thoroughly explained
- [ ] AAA pattern is demonstrated in all examples
- [ ] Common anti-patterns are documented
- [ ] JUnit 5 annotations and features are covered
- [ ] Configuration files are complete and usable (Maven and Gradle)
- [ ] Visual diagrams are included (or placeholders)
- [ ] All code examples are syntactically correct
- [ ] Repository information is included where applicable
- [ ] Quality checklist is comprehensive
- [ ] Mockito usage is thoroughly documented
- [ ] AssertJ fluent assertions are covered

---
~~~

End of prompt template.

---

## Additional Notes

- Install dependencies: Add to `pom.xml` or `build.gradle`
- Run tests: `mvn test` or `gradle test`
- Check coverage: `mvn jacoco:report` or `gradle jacocoTestReport`
- Run specific test: `mvn test -Dtest=CalculatorTest`
- Run with tag: `mvn test -Dgroups=fast`
- Debug tests: Use IDE debugger or `mvnDebug test`

---

**Status:** Template ready for use. Copy the prompt section above into your AI assistant to generate comprehensive Java unit testing guidance.
