---
template_id: java_test_cases
template_name: Test Cases Development - Java
version: 1.0.0
last_updated: 2025-12-03
language: Java
category: test_development
phase: test_cases
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-8
prerequisites:
  - test_development/unit_tests/java_unit_tests.md
related_templates:
  - test_development/mocks_fixtures/java_mocks_fixtures.md
tools:
  - junit (5.11.3)
  - maven
  - gradle
tags:
  - test-development
  - testing
  - java
---
# Java Test Case Development

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                 ► │ ● CURRENT
│ Phase 4: Mocks & Fixtures                          ► │ [NEXT]
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 2 (Unit Tests) should be completed first
**Next Step:** Phase 4 (Mocks & Fixtures)

---


## Objective
Develop comprehensive, well-structured test cases that validate functionality, cover edge cases, handle error conditions, and provide clear documentation of expected behavior using JUnit 5 and modern Java testing practices.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/test_cases/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/test_cases/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Test Coverage

- [ ] Happy path scenarios tested

- [ ] Edge cases and boundaries covered

- [ ] Error conditions validated

- [ ] Input validation tested

- [ ] State transitions verified

- [ ] Regression tests added for bugs

- [ ] Exception handling validated

### Test Quality

- [ ] Tests follow AAA pattern (Arrange-Act-Assert)

- [ ] Test names clearly describe what is tested

- [ ] Tests are isolated and independent

- [ ] Tests execute quickly (<1s for unit tests)

- [ ] Assertions are specific and meaningful

- [ ] No test interdependencies

- [ ] Proper use of @BeforeEach/@AfterEach

### Test Organization

- [ ] Tests grouped logically by feature/class

- [ ] Related tests organized in test classes

- [ ] Parametrized tests used for multiple scenarios

- [ ] Setup and teardown properly implemented

- [ ] Test documentation provided with JavaDoc

- [ ] Test fixtures properly managed

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Java Test Case Development

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/test_cases"
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

Please develop comprehensive test cases for this Java code following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Test Case Planning

1. **Analyze Code to Test**
   - Identify all public methods and classes
   - Document expected behavior
   - List input parameters and types
   - Define expected outputs
   - Note side effects (database, files, external services)
   - Identify exceptions that should be thrown

2. **Identify Test Scenarios**

   **Happy Path**:
   - Normal operation with valid inputs
   - Expected use cases
   - Successful execution flows
   - Valid object state transitions

   **Edge Cases**:
   - Boundary values (Integer.MAX_VALUE, Integer.MIN_VALUE, 0)
   - Empty collections (empty List, Set, Map)
   - Null values
   - Large data sets
   - Special characters in strings
   - Concurrent access scenarios

   **Error Conditions**:
   - Invalid inputs
   - Missing required parameters
   - IllegalArgumentException scenarios
   - NullPointerException scenarios
   - Business rule violations
   - External dependency failures

3. **Create Test Case Matrix**

   | Scenario | Input | Expected Output | Test Type | Priority |
   |----------|-------|-----------------|-----------|----------|
   | [description] | [values] | [result] | [unit/integration] | [high/med/low] |

## Phase 2: Unit Test Implementation (JUnit 5)

### AAA Pattern (Arrange-Act-Assert)

Follow this structure for clear, maintainable tests:

```java
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.junit.jupiter.params.provider.CsvSource;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for UserService class.
 *
 * Tests cover user creation, validation, and retrieval operations.
 */
class UserServiceTest {

    private UserService userService;

    @Mock
    private UserRepository userRepository;

    @Mock
    private EmailService emailService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        userService = new UserService(userRepository, emailService);
    }

    @AfterEach
    void tearDown() {
        // Clean up resources if needed
    }

    @Test
    @DisplayName("Should create user with valid data and return user ID")
    void createUser_WithValidData_ReturnsUserId() {
        // Arrange - Set up test data and mocks
        User user = new User("Alice", "alice@example.com", 30);
        Long expectedUserId = 123L;
        when(userRepository.save(any(User.class))).thenReturn(expectedUserId);

        // Act - Execute the method being tested
        Long actualUserId = userService.createUser(user);

        // Assert - Verify the result matches expectations
        assertNotNull(actualUserId);
        assertEquals(expectedUserId, actualUserId);
        verify(userRepository).save(user);
        verify(emailService).sendWelcomeEmail(user.getEmail());
    }

    @Test
    @DisplayName("Should throw IllegalArgumentException when email is invalid")
    void createUser_WithInvalidEmail_ThrowsException() {
        // Arrange
        User user = new User("Bob", "not-an-email", 25);

        // Act & Assert - Use assertThrows for exception testing
        IllegalArgumentException exception = assertThrows(
            IllegalArgumentException.class,
            () -> userService.createUser(user)
        );

        assertTrue(exception.getMessage().contains("Invalid email format"));
        verify(userRepository, never()).save(any());
    }

    @Test
    @DisplayName("Should use default age when age is not provided")
    void createUser_WithoutAge_UsesDefaultAge() {
        // Arrange
        User user = new User("Charlie", "charlie@example.com");
        int expectedDefaultAge = 18;

        // Act
        userService.createUser(user);

        // Assert
        assertEquals(expectedDefaultAge, user.getAge());
    }
}
```

### Test Naming Conventions

Use descriptive names that explain what is tested:

**Pattern**: `methodName_Condition_ExpectedResult`

**Examples**:
```java
// Good test names
@Test
void addUser_WithValidData_ReturnsUserId() {}

@Test
void addUser_WithDuplicateEmail_ThrowsValidationException() {}

@Test
void getUser_WithNonexistentId_ReturnsEmpty() {}

@Test
void updateUser_WithInvalidAge_ThrowsIllegalArgumentException() {}

// Poor test names (avoid these)
@Test
void testAddUser() {}              // Too generic

@Test
void test1() {}                    // Non-descriptive

@Test
void testError() {}                // Unclear what error

@Test
void testEdgeCase() {}             // Vague
```

### Testing Different Scenarios

**1. Testing Return Values**:
```java
class CalculatorTest {

    private Calculator calculator;

    @BeforeEach
    void setUp() {
        calculator = new Calculator();
    }

    @Test
    @DisplayName("Should return correct sum for array of numbers")
    void calculateTotal_WithNumbers_ReturnsSum() {
        double[] items = {10.0, 20.0, 30.0};
        double result = calculator.calculateTotal(items);
        assertEquals(60.0, result, 0.001);
    }

    @Test
    @DisplayName("Should return zero for empty array")
    void calculateTotal_WithEmptyArray_ReturnsZero() {
        double[] items = {};
        assertEquals(0.0, calculator.calculateTotal(items), 0.001);
    }

    @Test
    @DisplayName("Should handle negative values correctly")
    void calculateTotal_WithNegativeValues_ReturnsCorrectSum() {
        double[] items = {10.0, -5.0, 15.0};
        assertEquals(20.0, calculator.calculateTotal(items), 0.001);
    }
}
```

**2. Testing Exceptions**:
```java
class MathOperationsTest {

    @Test
    @DisplayName("Should throw ArithmeticException when dividing by zero")
    void divide_ByZero_ThrowsArithmeticException() {
        MathOperations math = new MathOperations();

        assertThrows(ArithmeticException.class, () -> {
            math.divide(10, 0);
        });
    }

    @Test
    @DisplayName("Should throw IllegalArgumentException with specific message")
    void parseDate_WithInvalidFormat_ThrowsExceptionWithMessage() {
        DateParser parser = new DateParser();

        IllegalArgumentException exception = assertThrows(
            IllegalArgumentException.class,
            () -> parser.parse("not-a-date")
        );

        assertTrue(exception.getMessage().contains("Invalid date format"));
    }
}
```

**3. Testing Side Effects and Mocks**:
```java
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private InventoryService inventoryService;

    private OrderService orderService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        orderService = new OrderService(orderRepository, inventoryService);
    }

    @Test
    @DisplayName("Should save order and update inventory")
    void createOrder_WithValidData_SavesAndUpdatesInventory() {
        // Arrange
        Order order = new Order();
        order.addItem(new OrderItem(1L, 5));

        when(orderRepository.save(any(Order.class))).thenReturn(order);

        // Act
        orderService.createOrder(order);

        // Assert
        verify(orderRepository).save(order);
        verify(inventoryService).decrementStock(1L, 5);
    }

    @Test
    @DisplayName("Should send email notification after order creation")
    void createOrder_Success_SendsNotification() {
        // Arrange
        Order order = new Order();
        order.setCustomerEmail("customer@example.com");

        // Act
        orderService.createOrder(order);

        // Assert
        verify(emailService).sendOrderConfirmation(
            eq("customer@example.com"),
            any(Order.class)
        );
    }
}
```

**4. Testing State Changes**:
```java
class UserAccountTest {

    @Test
    @DisplayName("Should update status to active after login")
    void login_WithValidCredentials_UpdatesStatusToActive() {
        // Arrange
        User user = new User("alice", "password");
        user.setStatus(UserStatus.INACTIVE);

        // Act
        user.login("password");

        // Assert
        assertEquals(UserStatus.ACTIVE, user.getStatus());
        assertNotNull(user.getLastLoginTime());
    }

    @Test
    @DisplayName("Should restore inventory when order is cancelled")
    void cancelOrder_Success_RestoresInventory() {
        // Arrange
        Inventory inventory = new Inventory();
        inventory.addStock(1L, 100);
        Order order = new Order();
        order.addItem(new OrderItem(1L, 5));
        inventory.reserveStock(1L, 5);

        // Act
        order.cancel();
        inventory.releaseReservation(1L, 5);

        // Assert
        assertEquals(100, inventory.getAvailableStock(1L));
    }
}
```

### Parametrized Tests

Test multiple scenarios efficiently:

```java
class ValidationTest {

    @ParameterizedTest
    @ValueSource(ints = {0, 1, 5, 10})
    @DisplayName("Should convert numbers to words correctly")
    void numberToWord_WithValidNumbers_ConvertsCorrectly(int number) {
        String result = NumberConverter.toWord(number);
        assertNotNull(result);
        assertFalse(result.isEmpty());
    }

    @ParameterizedTest
    @CsvSource({
        "0, zero",
        "1, one",
        "5, five",
        "10, ten"
    })
    @DisplayName("Should map numbers to expected words")
    void numberToWord_WithInput_ReturnsExpectedWord(int input, String expected) {
        assertEquals(expected, NumberConverter.toWord(input));
    }

    @ParameterizedTest
    @ValueSource(strings = {"", "not-an-email", "@example.com", "user@", "user @example.com"})
    @DisplayName("Should reject invalid email formats")
    void validateEmail_WithInvalidFormats_ThrowsException(String email) {
        assertThrows(IllegalArgumentException.class, () -> {
            EmailValidator.validate(email);
        });
    }

    @ParameterizedTest
    @CsvSource({
        "17, false",
        "18, true",
        "21, true",
        "100, true"
    })
    @DisplayName("Should check age threshold correctly")
    void isAdult_WithVariousAges_ReturnsExpectedResult(int age, boolean expected) {
        assertEquals(expected, AgeChecker.isAdult(age));
    }
}
```

### Testing Edge Cases and Boundaries

```java
class BoundaryTest {

    @Nested
    @DisplayName("Boundary Conditions")
    class BoundaryConditions {

        @Test
        @DisplayName("Should handle minimum valid value")
        void processValue_WithMinimum_ReturnsExpectedResult() {
            assertEquals(expectedMin, processor.processValue(0));
        }

        @Test
        @DisplayName("Should handle maximum valid value")
        void processValue_WithMaximum_ReturnsExpectedResult() {
            assertEquals(expectedMax, processor.processValue(100));
        }

        @Test
        @DisplayName("Should throw exception for value below minimum")
        void processValue_BelowMinimum_ThrowsException() {
            assertThrows(IllegalArgumentException.class, () -> {
                processor.processValue(-1);
            });
        }

        @Test
        @DisplayName("Should throw exception for value above maximum")
        void processValue_AboveMaximum_ThrowsException() {
            assertThrows(IllegalArgumentException.class, () -> {
                processor.processValue(101);
            });
        }
    }

    @Nested
    @DisplayName("Collection Edge Cases")
    class CollectionEdgeCases {

        @Test
        @DisplayName("Should handle empty list")
        void processCollection_WithEmptyList_ReturnsEmptyList() {
            List<Integer> result = processor.processCollection(Collections.emptyList());
            assertTrue(result.isEmpty());
        }

        @Test
        @DisplayName("Should handle single element list")
        void processCollection_WithSingleElement_ProcessesCorrectly() {
            List<Integer> input = List.of(1);
            List<Integer> result = processor.processCollection(input);
            assertEquals(1, result.size());
        }

        @Test
        @DisplayName("Should handle large collections efficiently")
        void processCollection_WithLargeList_CompletesInReasonableTime() {
            List<Integer> largeList = IntStream.range(0, 10000)
                .boxed()
                .collect(Collectors.toList());

            assertTimeout(Duration.ofSeconds(1), () -> {
                List<Integer> result = processor.processCollection(largeList);
                assertEquals(10000, result.size());
            });
        }

        @Test
        @DisplayName("Should handle null value")
        void processValue_WithNull_ThrowsNullPointerException() {
            assertThrows(NullPointerException.class, () -> {
                processor.processValue(null);
            });
        }
    }
}
```

## Phase 3: Integration Test Implementation

Integration tests verify multiple components working together:

```java
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

/**
 * Integration tests for user registration workflow.
 *
 * Tests the complete user registration process including
 * validation, database storage, and email notification.
 */
@SpringBootTest
@Transactional
class UserRegistrationIntegrationTest {

    @Autowired
    private UserService userService;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private TestEmailService emailService;

    @BeforeEach
    void setUp() {
        userRepository.deleteAll();
        emailService.clearSentEmails();
    }

    @Test
    @DisplayName("Should create database entry and send welcome email")
    void registerUser_WithValidData_CreatesEntryAndSendsEmail() {
        // Arrange
        UserRegistrationRequest request = UserRegistrationRequest.builder()
            .username("newuser")
            .email("newuser@example.com")
            .password("SecurePass123!")
            .build();

        // Act
        Long userId = userService.registerUser(request);

        // Assert - Verify database entry
        User user = userRepository.findById(userId).orElseThrow();
        assertNotNull(user);
        assertEquals("newuser", user.getUsername());
        assertEquals("newuser@example.com", user.getEmail());
        assertNotEquals("SecurePass123!", user.getPassword()); // Should be hashed

        // Assert - Verify email sent
        List<Email> sentEmails = emailService.getSentEmails();
        assertEquals(1, sentEmails.size());
        Email welcomeEmail = sentEmails.get(0);
        assertEquals("newuser@example.com", welcomeEmail.getTo());
        assertTrue(welcomeEmail.getSubject().contains("Welcome"));
    }

    @Test
    @DisplayName("Should rollback transaction when email fails")
    void registerUser_WhenEmailFails_RollsBackTransaction() {
        // Arrange
        emailService.setFailOnSend(true);
        UserRegistrationRequest request = UserRegistrationRequest.builder()
            .username("testuser")
            .email("test@example.com")
            .password("Pass123!")
            .build();

        // Act & Assert
        assertThrows(EmailSendException.class, () -> {
            userService.registerUser(request);
        });

        // Verify no user was created
        assertTrue(userRepository.findByEmail("test@example.com").isEmpty());
    }

    @Test
    @DisplayName("Should throw exception when username is duplicate")
    void registerUser_WithDuplicateUsername_ThrowsException() {
        // Arrange - Create existing user
        UserRegistrationRequest firstRequest = UserRegistrationRequest.builder()
            .username("alice")
            .email("alice@example.com")
            .password("Pass123!")
            .build();
        userService.registerUser(firstRequest);

        // Try to create duplicate
        UserRegistrationRequest duplicateRequest = UserRegistrationRequest.builder()
            .username("alice")
            .email("different@example.com")
            .password("Pass123!")
            .build();

        // Act & Assert
        assertThrows(DuplicateUsernameException.class, () -> {
            userService.registerUser(duplicateRequest);
        });
    }
}
```

### REST API Integration Tests

```java
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.hamcrest.Matchers.*;

@SpringBootTest
@AutoConfigureMockMvc
class UserApiIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @DisplayName("POST /api/users should create user and return 201")
    void createUser_WithValidData_Returns201() throws Exception {
        String userJson = """
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "SecurePass123!"
            }
            """;

        mockMvc.perform(post("/api/users")
                .contentType(MediaType.APPLICATION_JSON)
                .content(userJson))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").exists())
            .andExpect(jsonPath("$.username").value("testuser"))
            .andExpect(jsonPath("$.email").value("test@example.com"));
    }

    @Test
    @DisplayName("GET /api/users/{id} should return user data")
    void getUser_WithExistingId_ReturnsUserData() throws Exception {
        // Arrange - Create user first
        Long userId = createTestUser("alice", "alice@example.com");

        // Act & Assert
        mockMvc.perform(get("/api/users/" + userId))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(userId))
            .andExpect(jsonPath("$.username").value("alice"));
    }

    @Test
    @DisplayName("PUT /api/users/{id} with invalid data should return 400")
    void updateUser_WithInvalidData_Returns400() throws Exception {
        Long userId = createTestUser("bob", "bob@example.com");

        String invalidJson = """
            {
                "email": "not-an-email"
            }
            """;

        mockMvc.perform(put("/api/users/" + userId)
                .contentType(MediaType.APPLICATION_JSON)
                .content(invalidJson))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.error").exists());
    }
}
```

## Phase 4: End-to-End Test Implementation

E2E tests validate complete workflows:

```java
/**
 * End-to-end tests for e-commerce checkout flow.
 *
 * Tests the complete user journey from adding items to cart
 * through payment and order confirmation.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class CheckoutWorkflowE2ETest {

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private OrderRepository orderRepository;

    private User testUser;
    private Product testProduct;

    @BeforeEach
    void setUp() {
        // Set up test data
        testUser = createTestUser();
        testProduct = createTestProduct();
    }

    @Test
    @DisplayName("Should complete full purchase workflow successfully")
    void completePurchase_FromCartToConfirmation_Success() {
        // Login
        String authToken = loginUser(testUser);

        // Add product to cart
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(authToken);
        HttpEntity<CartItemRequest> cartRequest = new HttpEntity<>(
            new CartItemRequest(testProduct.getId(), 1),
            headers
        );

        ResponseEntity<CartResponse> cartResponse = restTemplate.postForEntity(
            "/api/cart/items",
            cartRequest,
            CartResponse.class
        );
        assertEquals(HttpStatus.OK, cartResponse.getStatusCode());
        assertEquals(1, cartResponse.getBody().getItemCount());

        // Create order
        HttpEntity<Void> orderRequest = new HttpEntity<>(headers);
        ResponseEntity<OrderResponse> orderResponse = restTemplate.postForEntity(
            "/api/orders",
            orderRequest,
            OrderResponse.class
        );
        assertEquals(HttpStatus.CREATED, orderResponse.getStatusCode());

        Long orderId = orderResponse.getBody().getId();
        assertNotNull(orderId);

        // Verify order in database
        Order order = orderRepository.findById(orderId).orElseThrow();
        assertEquals(testUser.getId(), order.getUserId());
        assertEquals(OrderStatus.PENDING, order.getStatus());
        assertEquals(1, order.getItems().size());
    }
}
```

## Phase 5: Test Best Practices

### 1. Test Independence

```java
// GOOD - Tests are independent
class UserServiceTest {

    @BeforeEach
    void setUp() {
        userRepository.deleteAll(); // Clean state for each test
    }

    @Test
    void createUser_Success() {
        User user = userService.createUser("alice", "alice@example.com");
        assertNotNull(user.getId());
    }

    @Test
    void deleteUser_Success() {
        User user = userService.createUser("bob", "bob@example.com");
        userService.deleteUser(user.getId());
        assertTrue(userService.findById(user.getId()).isEmpty());
    }
}

// BAD - Tests depend on each other
class UserServiceTest {
    private Long userId; // Shared state!

    @Test
    void test1_CreateUser() {
        User user = userService.createUser("alice", "alice@example.com");
        userId = user.getId(); // Setting shared state
    }

    @Test
    void test2_DeleteUser() {
        userService.deleteUser(userId); // Depends on test1
    }
}
```

### 2. Clear Assertions

```java
// GOOD - Specific, clear assertions
@Test
void createUser_WithValidData_ReturnsUserWithCorrectProperties() {
    User user = userService.createUser("alice", "alice@example.com", 30);

    assertEquals("alice", user.getUsername());
    assertEquals("alice@example.com", user.getEmail());
    assertEquals(30, user.getAge());
    assertNotNull(user.getCreatedAt());
    assertTrue(user.isActive());
}

// BAD - Vague or missing assertions
@Test
void createUser_Success() {
    User user = userService.createUser("alice", "alice@example.com", 30);
    assertNotNull(user); // Too vague
    assertNotNull(user.getUsername()); // Checks existence, not value
}
```

## Output Format

Please provide comprehensive test cases with the following structure:

### Test Coverage Summary

- **Total Test Cases**: [count]

- **Unit Tests**: [count]

- **Integration Tests**: [count]

- **E2E Tests**: [count]

- **Test Types**:
  - Happy path: [count]
  - Edge cases: [count]
  - Error conditions: [count]

### Test Case Implementation

For each class/module:

**Class**: `[ClassName]`
**Test File**: `src/test/java/com/example/[ClassName]Test.java`

**Test Cases**:
1. `methodName_WithValidData_ReturnsExpectedResult`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [result]
   - **Type**: [unit/integration/e2e]

2. `methodName_WithInvalidInput_ThrowsException`
   - **Scenario**: [description]
   - **Input**: [test data]
   - **Expected**: [exception type]
   - **Type**: [unit/integration/e2e]

### Test Execution Results
```bash
# Run tests
mvn test

# Run with coverage
mvn test jacoco:report

# Expected output
[INFO] Tests run: 15, Failures: 0, Errors: 0, Skipped: 0
```

### Coverage Gaps Identified

- [ ] [Method]: Missing tests for [scenario]

- [ ] [Method]: Need edge case tests for [condition]

- [ ] [Method]: Exception handling not tested

### Test Quality Metrics

- **Average test execution time**: [milliseconds]

- **Tests following AAA pattern**: [percentage]

- **Tests with clear names**: [percentage]

- **Independent tests**: [percentage]

- **Mock usage**: [appropriate/excessive]

### Next Steps

- [ ] Implement remaining test cases for coverage gaps

- [ ] Add performance tests for critical methods

- [ ] Set up test containers for integration tests

- [ ] Configure CI/CD pipeline

- [ ] Review and refactor slow tests

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).
~~~

## Output Format

The AI assistant should deliver:

1. **Test case matrix** documenting all scenarios
2. **Complete test implementations** with clear AAA structure
3. **Parametrized tests** for multiple scenarios
4. **Integration and E2E tests** for workflows
5. **Test coverage report** showing gaps
6. **Execution instructions** for running tests
7. **Quality metrics** and improvement suggestions
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
