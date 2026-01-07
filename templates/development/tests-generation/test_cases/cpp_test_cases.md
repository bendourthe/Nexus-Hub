---
template_id: cpp_test_cases
template_name: Test Cases Development - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: tests_generation
phase: test_cases
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-8
prerequisites:

  - tests_generation/unit_tests/cpp_unit_tests.md
related_templates:

  - tests_generation/mocks_fixtures/cpp_mocks_fixtures.md
tools:

  - google test

  - catch2

  - boost.test
tags:

  - test-development

  - testing

  - cpp
---
# C++ Test Case Development

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
Develop comprehensive, well-structured test cases that validate functionality, cover edge cases, handle error conditions, and provide clear documentation of expected behavior using GoogleTest, Catch2, or similar modern C++ testing frameworks.

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

- [ ] RAII and resource management tested

### Test Quality

- [ ] Tests follow AAA pattern (Arrange-Act-Assert)

- [ ] Test names clearly describe what is tested

- [ ] Tests are isolated and independent

- [ ] Tests execute quickly (<1s for unit tests)

- [ ] Assertions are specific and meaningful

- [ ] No test interdependencies

- [ ] Proper use of test fixtures

### Test Organization

- [ ] Tests grouped logically by feature/class

- [ ] Related tests organized in test fixtures

- [ ] Parametrized tests used for multiple scenarios

- [ ] Setup and teardown properly implemented

- [ ] Test documentation provided

- [ ] Mocks and fakes used appropriately

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Test Case Development

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

Please develop comprehensive test cases for this C++ code following this protocol:

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

   - Note side effects (memory allocation, file I/O, external calls)

   - Identify exceptions that should be thrown

2. **Identify Test Scenarios**

   **Happy Path**:

   - Normal operation with valid inputs

   - Expected use cases

   - Successful execution flows

   - Valid object state transitions

   - Move semantics and copy operations

   **Edge Cases**:

   - Boundary values (0, -1, std::numeric_limits)

   - Empty containers

   - nullptr and empty smart pointers

   - Large data sets

   - Special characters in strings

   - Move-only types

   **Error Conditions**:

   - Invalid inputs

   - Missing required parameters

   - Exception scenarios

   - Resource allocation failures

   - Thread safety issues

   - RAII violations

3. **Create Test Case Matrix**

   | Scenario | Input | Expected Output | Test Type | Priority |
   |----------|-------|-----------------|-----------|----------|
   | [description] | [values] | [result] | [unit/integration] | [high/med/low] |

## Phase 2: Unit Test Implementation (GoogleTest)

### AAA Pattern (Arrange-Act-Assert)

Follow this structure for clear, maintainable tests:

```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "user_service.h"
#include <memory>
#include <string>

/**

 * @file user_service_test.cpp

 * @brief Unit tests for UserService class.
 *

 * Tests cover user creation, validation, and retrieval operations.
 */

using ::testing::Return;
using ::testing::_;
using ::testing::Throw;

// Mock repository for testing
class MockUserRepository : public IUserRepository {
public:
    MOCK_METHOD(int, Save, (const User& user), (override));
    MOCK_METHOD(std::optional<User>, GetById, (int id), (const, override));
    MOCK_METHOD(void, Delete, (int id), (override));
};

// Test fixture for UserService tests
class UserServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        mockRepository = std::make_shared<MockUserRepository>();
        mockEmailService = std::make_shared<MockEmailService>();
        userService = std::make_unique<UserService>(mockRepository, mockEmailService);
    }

    void TearDown() override {
        // Cleanup happens automatically with smart pointers
    }

    std::shared_ptr<MockUserRepository> mockRepository;
    std::shared_ptr<MockEmailService> mockEmailService;
    std::unique_ptr<UserService> userService;
};

/**

 * @brief Test creating user with valid data returns user ID.
 */
TEST_F(UserServiceTest, CreateUser_WithValidData_ReturnsUserId) {
    // Arrange - Set up test data and mocks
    User user{"Alice", "alice@example.com", 30};
    const int expectedUserId = 123;

    EXPECT_CALL(*mockRepository, Save(_))
        .WillOnce(Return(expectedUserId));

    EXPECT_CALL(*mockEmailService, SendWelcomeEmail("alice@example.com"))
        .WillOnce(Return(true));

    // Act - Execute the method being tested
    int actualUserId = userService->CreateUser(user);

    // Assert - Verify the result matches expectations
    EXPECT_EQ(expectedUserId, actualUserId);
}

/**

 * @brief Test creating user with invalid email throws exception.
 */
TEST_F(UserServiceTest, CreateUser_WithInvalidEmail_ThrowsException) {
    // Arrange
    User user{"Bob", "not-an-email", 25};

    // Act & Assert - Use EXPECT_THROW for exception testing
    EXPECT_THROW({
        userService->CreateUser(user);
    }, std::invalid_argument);
}

/**

 * @brief Test creating user with empty name throws exception.
 */
TEST_F(UserServiceTest, CreateUser_WithEmptyName_ThrowsException) {
    // Arrange
    User user{"", "charlie@example.com", 20};

    // Act & Assert
    EXPECT_THROW({
        userService->CreateUser(user);
    }, std::invalid_argument);
}

/**

 * @brief Test creating user with negative age throws exception.
 */
TEST_F(UserServiceTest, CreateUser_WithNegativeAge_ThrowsException) {
    // Arrange
    User user{"Dave", "dave@example.com", -5};

    // Act & Assert
    EXPECT_THROW({
        userService->CreateUser(user);
    }, std::out_of_range);
}
```

### Test Naming Conventions

Use descriptive names that explain what is tested:

**Pattern**: `TestFixture_MethodName_Condition_ExpectedResult`

**Examples**:
```cpp
// Good test names
TEST_F(UserServiceTest, AddUser_WithValidData_ReturnsUserId) {}

TEST_F(UserServiceTest, AddUser_WithDuplicateEmail_ThrowsException) {}

TEST_F(UserServiceTest, GetUser_WithNonexistentId_ReturnsEmptyOptional) {}

TEST_F(UserServiceTest, UpdateUser_WithInvalidAge_ThrowsException) {}

// Poor test names (avoid these)
TEST_F(UserServiceTest, TestAddUser) {}        // Too generic
TEST_F(UserServiceTest, Test1) {}              // Non-descriptive
TEST_F(UserServiceTest, TestError) {}          // Unclear what error
TEST_F(UserServiceTest, TestEdgeCase) {}       // Vague
```

### Testing Different Scenarios

**1. Testing Return Values**:
```cpp
class CalculatorTest : public ::testing::Test {
protected:
    Calculator calculator;
};

TEST_F(CalculatorTest, CalculateTotal_WithNumbers_ReturnsSum) {
    // Arrange
    std::vector<double> items{10.0, 20.0, 30.0};

    // Act
    double result = calculator.CalculateTotal(items);

    // Assert
    EXPECT_DOUBLE_EQ(60.0, result);
}

TEST_F(CalculatorTest, CalculateTotal_WithEmptyVector_ReturnsZero) {
    // Arrange
    std::vector<double> items;

    // Act
    double result = calculator.CalculateTotal(items);

    // Assert
    EXPECT_DOUBLE_EQ(0.0, result);
}

TEST_F(CalculatorTest, CalculateTotal_WithNegativeValues_ReturnsCorrectSum) {
    // Arrange
    std::vector<double> items{10.0, -5.0, 15.0};

    // Act
    double result = calculator.CalculateTotal(items);

    // Assert
    EXPECT_DOUBLE_EQ(20.0, result);
}
```

**2. Testing Exceptions**:
```cpp
TEST(MathOperationsTest, Divide_ByZero_ThrowsException) {
    // Arrange
    MathOperations math;

    // Act & Assert
    EXPECT_THROW({
        math.Divide(10, 0);
    }, std::invalid_argument);
}

TEST(DateParserTest, Parse_WithInvalidFormat_ThrowsExceptionWithMessage) {
    // Arrange
    DateParser parser;

    // Act & Assert
    try {
        parser.Parse("not-a-date");
        FAIL() << "Expected std::invalid_argument";
    } catch (const std::invalid_argument& e) {
        EXPECT_THAT(e.what(), ::testing::HasSubstr("Invalid date format"));
    }
}

TEST(DataProcessorTest, Process_WithNullPointer_ThrowsException) {
    // Arrange
    DataProcessor processor;

    // Act & Assert
    EXPECT_THROW({
        processor.Process(nullptr);
    }, std::invalid_argument);
}
```

**3. Testing with Mocks**:
```cpp
TEST_F(OrderServiceTest, CreateOrder_WithValidData_SavesAndUpdatesInventory) {
    // Arrange
    Order order;
    order.AddItem(OrderItem{1, 5});

    EXPECT_CALL(*mockOrderRepository, Save(_))
        .WillOnce(Return(123));

    EXPECT_CALL(*mockInventoryService, DecrementStock(1, 5))
        .WillOnce(Return(true));

    // Act
    int orderId = orderService->CreateOrder(order);

    // Assert
    EXPECT_EQ(123, orderId);
}

TEST_F(EmailServiceTest, SendEmail_Success_InvokesSmtpClient) {
    // Arrange
    Email email{"test@example.com", "Subject", "Body"};

    EXPECT_CALL(*mockSmtpClient, Send(_))
        .WillOnce(Return(true));

    // Act
    bool result = emailService->Send(email);

    // Assert
    EXPECT_TRUE(result);
}
```

**4. Testing State Changes**:
```cpp
TEST(UserTest, Login_WithValidCredentials_UpdatesStatusToActive) {
    // Arrange
    User user{"alice", "hashed_password"};
    user.SetStatus(UserStatus::Inactive);

    // Act
    user.Login("correct_password");

    // Assert
    EXPECT_EQ(UserStatus::Active, user.GetStatus());
    EXPECT_NE(std::chrono::system_clock::time_point{}, user.GetLastLogin());
}

TEST(OrderTest, Cancel_Success_RestoresInventory) {
    // Arrange
    Inventory inventory;
    inventory.AddStock(1, 100);

    Order order;
    order.AddItem(OrderItem{1, 5});
    inventory.ReserveStock(1, 5);

    // Act
    order.Cancel();
    inventory.ReleaseReservation(1, 5);

    // Assert
    EXPECT_EQ(100, inventory.GetAvailableStock(1));
}
```

**5. Testing Move Semantics and RAII**:
```cpp
TEST(ResourceTest, MoveConstructor_TransfersOwnership) {
    // Arrange
    Resource resource1{"test_resource"};
    ASSERT_TRUE(resource1.IsValid());

    // Act - Move construct
    Resource resource2{std::move(resource1)};

    // Assert
    EXPECT_TRUE(resource2.IsValid());
    EXPECT_FALSE(resource1.IsValid()); // Moved-from object in valid but unspecified state
}

TEST(UniqueBufferTest, Destructor_ReleasesMemory) {
    // Arrange
    size_t* counter = new size_t{0};

    {
        // Act - Create buffer in scope
        UniqueBuffer buffer{1024, [counter]() { (*counter)++; }};
        EXPECT_EQ(0, *counter);
    } // Destructor called here

    // Assert - Verify destructor was called
    EXPECT_EQ(1, *counter);
    delete counter;
}
```

### Parametrized Tests

Test multiple scenarios efficiently:

```cpp
class ValidationTest : public ::testing::TestWithParam<std::pair<int, std::string>> {
};

TEST_P(ValidationTest, NumberToWord_ConvertsCorrectly) {
    // Arrange
    auto [input, expected] = GetParam();

    // Act
    std::string result = NumberToWord(input);

    // Assert
    EXPECT_EQ(expected, result);
}

INSTANTIATE_TEST_SUITE_P(
    NumberConversions,
    ValidationTest,
    ::testing::Values(
        std::make_pair(0, "zero"),
        std::make_pair(1, "one"),
        std::make_pair(5, "five"),
        std::make_pair(10, "ten")
    )
);

class EmailValidationTest : public ::testing::TestWithParam<std::string> {
};

TEST_P(EmailValidationTest, ValidateEmail_WithInvalidFormats_ThrowsException) {
    // Arrange
    std::string invalidEmail = GetParam();

    // Act & Assert
    EXPECT_THROW({
        ValidateEmail(invalidEmail);
    }, std::invalid_argument);
}

INSTANTIATE_TEST_SUITE_P(
    InvalidEmails,
    EmailValidationTest,
    ::testing::Values(
        "",
        "not-an-email",
        "@example.com",
        "user@",
        "user @example.com"
    )
);

class AgeCheckTest : public ::testing::TestWithParam<std::pair<int, bool>> {
};

TEST_P(AgeCheckTest, IsAdult_WithVariousAges_ReturnsExpectedResult) {
    // Arrange
    auto [age, expected] = GetParam();

    // Act
    bool result = IsAdult(age);

    // Assert
    EXPECT_EQ(expected, result);
}

INSTANTIATE_TEST_SUITE_P(
    AgeChecks,
    AgeCheckTest,
    ::testing::Values(
        std::make_pair(17, false),
        std::make_pair(18, true),
        std::make_pair(21, true),
        std::make_pair(100, true)
    )
);
```

### Testing Edge Cases and Boundaries

```cpp
class BoundaryTest : public ::testing::Test {
protected:
    ValueProcessor processor;
};

TEST_F(BoundaryTest, ProcessValue_WithMinimum_ReturnsExpectedResult) {
    // Act
    int result = processor.ProcessValue(0);

    // Assert
    EXPECT_EQ(expectedMin, result);
}

TEST_F(BoundaryTest, ProcessValue_WithMaximum_ReturnsExpectedResult) {
    // Act
    int result = processor.ProcessValue(100);

    // Assert
    EXPECT_EQ(expectedMax, result);
}

TEST_F(BoundaryTest, ProcessValue_BelowMinimum_ThrowsException) {
    // Act & Assert
    EXPECT_THROW({
        processor.ProcessValue(-1);
    }, std::out_of_range);
}

TEST_F(BoundaryTest, ProcessValue_AboveMaximum_ThrowsException) {
    // Act & Assert
    EXPECT_THROW({
        processor.ProcessValue(101);
    }, std::out_of_range);
}

TEST(CollectionTest, ProcessCollection_WithEmptyVector_ReturnsEmptyVector) {
    // Arrange
    std::vector<int> emptyVec;
    CollectionProcessor processor;

    // Act
    auto result = processor.ProcessCollection(emptyVec);

    // Assert
    EXPECT_TRUE(result.empty());
}

TEST(CollectionTest, ProcessCollection_WithSingleElement_ProcessesCorrectly) {
    // Arrange
    std::vector<int> singleElement{1};
    CollectionProcessor processor;

    // Act
    auto result = processor.ProcessCollection(singleElement);

    // Assert
    EXPECT_EQ(1, result.size());
}

TEST(CollectionTest, ProcessCollection_WithLargeVector_CompletesInReasonableTime) {
    // Arrange
    std::vector<int> largeVec(10000);
    std::iota(largeVec.begin(), largeVec.end(), 0);
    CollectionProcessor processor;

    // Act
    auto start = std::chrono::high_resolution_clock::now();
    auto result = processor.ProcessCollection(largeVec);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // Assert
    EXPECT_EQ(10000, result.size());
    EXPECT_LT(duration.count(), 1000); // Should complete in less than 1 second
}

TEST(PointerTest, ProcessValue_WithNullptr_ThrowsException) {
    // Arrange
    Processor processor;

    // Act & Assert
    EXPECT_THROW({
        processor.ProcessValue(nullptr);
    }, std::invalid_argument);
}
```

### Testing with Catch2 Framework

```cpp
#include <catch2/catch_test_macros.hpp>
#include "calculator.h"

TEST_CASE("Calculator operations", "[calculator]") {
    Calculator calc;

    SECTION("Addition with positive numbers") {
        REQUIRE(calc.Add(2, 3) == 5);
        REQUIRE(calc.Add(10, 20) == 30);
    }

    SECTION("Addition with negative numbers") {
        REQUIRE(calc.Add(-2, -3) == -5);
        REQUIRE(calc.Add(-10, 5) == -5);
    }

    SECTION("Division by zero throws") {
        REQUIRE_THROWS_AS(calc.Divide(10, 0), std::invalid_argument);
    }
}

TEST_CASE("User creation", "[user]") {
    SECTION("Valid user data") {
        User user{"Alice", "alice@example.com", 30};

        REQUIRE(user.GetName() == "Alice");
        REQUIRE(user.GetEmail() == "alice@example.com");
        REQUIRE(user.GetAge() == 30);
    }

    SECTION("Invalid email throws") {
        REQUIRE_THROWS_AS(
            User("Bob", "not-an-email", 25),
            std::invalid_argument
        );
    }
}
```

## Phase 3: Integration Test Implementation

Integration tests verify multiple components working together:

```cpp
#include <gtest/gtest.h>
#include "user_service.h"
#include "database.h"
#include "email_service.h"
#include <memory>

/**

 * @file user_integration_test.cpp

 * @brief Integration tests for user registration workflow.
 *

 * Tests the complete user registration process including

 * validation, database storage, and email notification.
 */

class UserRegistrationIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup test database
        database = std::make_shared<Database>(":memory:");
        database->InitSchema();

        // Setup services
        emailService = std::make_shared<TestEmailService>();
        userRepository = std::make_shared<UserRepository>(database);
        userService = std::make_unique<UserService>(userRepository, emailService);
    }

    void TearDown() override {
        database->Clear();
    }

    std::shared_ptr<Database> database;
    std::shared_ptr<TestEmailService> emailService;
    std::shared_ptr<UserRepository> userRepository;
    std::unique_ptr<UserService> userService;
};

TEST_F(UserRegistrationIntegrationTest, RegisterUser_WithValidData_CreatesEntryAndSendsEmail) {
    // Arrange
    UserRegistrationRequest request{
        .username = "newuser",
        .email = "newuser@example.com",
        .password = "SecurePass123!"
    };

    // Act
    int userId = userService->RegisterUser(request);

    // Assert - Verify database entry
    EXPECT_GT(userId, 0);

    auto user = userRepository->GetById(userId);
    ASSERT_TRUE(user.has_value());
    EXPECT_EQ("newuser", user->GetUsername());
    EXPECT_EQ("newuser@example.com", user->GetEmail());
    EXPECT_NE("SecurePass123!", user->GetPassword()); // Should be hashed

    // Assert - Verify email sent
    const auto& sentEmails = emailService->GetSentEmails();
    EXPECT_EQ(1, sentEmails.size());
    EXPECT_EQ("newuser@example.com", sentEmails[0].to);
    EXPECT_THAT(sentEmails[0].subject, ::testing::HasSubstr("Welcome"));
}

TEST_F(UserRegistrationIntegrationTest, RegisterUser_WithDuplicateUsername_ThrowsException) {
    // Arrange - Create existing user
    UserRegistrationRequest firstRequest{
        .username = "alice",
        .email = "alice@example.com",
        .password = "Pass123!"
    };
    userService->RegisterUser(firstRequest);

    // Try to create duplicate
    UserRegistrationRequest duplicateRequest{
        .username = "alice",
        .email = "different@example.com",
        .password = "Pass123!"
    };

    // Act & Assert
    EXPECT_THROW({
        userService->RegisterUser(duplicateRequest);
    }, DuplicateUsernameException);
}
```

### REST API Integration Tests

```cpp
#include <gtest/gtest.h>
#include <httplib.h>
#include "api_server.h"

class UserApiIntegrationTest : public ::testing::Test {
protected:
    void SetUp() override {
        server = std::make_unique<ApiServer>(8080);
        server->Start();

        client = std::make_unique<httplib::Client>("localhost", 8080);
    }

    void TearDown() override {
        server->Stop();
    }

    std::unique_ptr<ApiServer> server;
    std::unique_ptr<httplib::Client> client;
};

TEST_F(UserApiIntegrationTest, CreateUser_WithValidData_Returns201) {
    // Arrange
    std::string userData = R"({
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!"
    })";

    // Act
    auto response = client->Post("/api/users", userData, "application/json");

    // Assert
    ASSERT_TRUE(response);
    EXPECT_EQ(201, response->status);

    // Parse response body
    auto json = nlohmann::json::parse(response->body);
    EXPECT_TRUE(json.contains("id"));
    EXPECT_EQ("testuser", json["username"]);
}

TEST_F(UserApiIntegrationTest, GetUser_WithExistingId_ReturnsUserData) {
    // Arrange - Create user first
    int userId = CreateTestUser("alice", "alice@example.com");

    // Act
    auto response = client->Get("/api/users/" + std::to_string(userId));

    // Assert
    ASSERT_TRUE(response);
    EXPECT_EQ(200, response->status);

    auto json = nlohmann::json::parse(response->body);
    EXPECT_EQ(userId, json["id"]);
    EXPECT_EQ("alice", json["username"]);
}
```

## Phase 4: Performance and Benchmark Tests

```cpp
#include <benchmark/benchmark.h>
#include "calculator.h"

static void BM_CalculateTotal(benchmark::State& state) {
    Calculator calc;
    std::vector<double> items(state.range(0));
    std::iota(items.begin(), items.end(), 0.0);

    for (auto _ : state) {
        benchmark::DoNotOptimize(calc.CalculateTotal(items));
    }

    state.SetComplexityN(state.range(0));
}

BENCHMARK(BM_CalculateTotal)
    ->Range(8, 8<<10)
    ->Complexity();

static void BM_UserServiceCreateUser(benchmark::State& state) {
    auto mockRepo = std::make_shared<MockUserRepository>();
    auto service = std::make_unique<UserService>(mockRepo);
    User user{"BenchUser", "bench@example.com", 30};

    for (auto _ : state) {
        service->CreateUser(user);
    }
}

BENCHMARK(BM_UserServiceCreateUser);

BENCHMARK_MAIN();
```

## Phase 5: Test Best Practices

### 1. Test Independence

```cpp
// GOOD - Tests are independent
class UserServiceTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Fresh instance for each test
        mockRepository = std::make_shared<MockUserRepository>();
        userService = std::make_unique<UserService>(mockRepository);
    }
};

TEST_F(UserServiceTest, CreateUser_Success) {
    User user{"alice", "alice@example.com", 30};
    EXPECT_CALL(*mockRepository, Save(_)).WillOnce(Return(123));

    int id = userService->CreateUser(user);
    EXPECT_GT(id, 0);
}

TEST_F(UserServiceTest, DeleteUser_Success) {
    // Independent - doesn't rely on previous test
    EXPECT_CALL(*mockRepository, Delete(123)).WillOnce(Return());

    EXPECT_NO_THROW(userService->DeleteUser(123));
}

// BAD - Tests depend on each other
class UserServiceTest : public ::testing::Test {
    int sharedUserId; // Shared state!
};

TEST_F(UserServiceTest, Test1_CreateUser) {
    User user{"alice", "alice@example.com", 30};
    sharedUserId = userService->CreateUser(user); // Setting shared state
}

TEST_F(UserServiceTest, Test2_DeleteUser) {
    userService->DeleteUser(sharedUserId); // Depends on Test1
}
```

### 2. Clear Assertions

```cpp
// GOOD - Specific, clear assertions
TEST_F(UserServiceTest, CreateUser_WithValidData_ReturnsUserWithCorrectProperties) {
    User user{"Alice", "alice@example.com", 30};

    EXPECT_CALL(*mockRepository, Save(_)).WillOnce(Return(123));

    int userId = userService->CreateUser(user);

    EXPECT_EQ(123, userId);

    // Verify mock was called correctly
    EXPECT_CALL(*mockRepository, GetById(123))
        .WillOnce(Return(std::make_optional(user)));

    auto retrievedUser = userService->GetUser(123);
    ASSERT_TRUE(retrievedUser.has_value());
    EXPECT_EQ("Alice", retrievedUser->GetUsername());
    EXPECT_EQ("alice@example.com", retrievedUser->GetEmail());
    EXPECT_EQ(30, retrievedUser->GetAge());
}

// BAD - Vague or missing assertions
TEST_F(UserServiceTest, CreateUser_Success) {
    User user{"Alice", "alice@example.com", 30};
    int userId = userService->CreateUser(user);
    EXPECT_GT(userId, 0); // Too vague - what about the user?
}
```

## Output Format

Please provide comprehensive test cases with the following structure:

### Test Coverage Summary

- **Total Test Cases**: [count]

- **Unit Tests**: [count]

- **Integration Tests**: [count]

- **Benchmark Tests**: [count]

- **Test Types**:

  - Happy path: [count]

  - Edge cases: [count]

  - Error conditions: [count]

### Test Case Implementation

For each class/module:

**Class**: `[ClassName]`
**Test File**: `test_[class_name].cpp`

**Test Cases**:

1. `MethodName_WithValidData_ReturnsExpectedResult`

   - **Scenario**: [description]

   - **Input**: [test data]

   - **Expected**: [result]

   - **Type**: [unit/integration]

2. `MethodName_WithInvalidInput_ThrowsException`

   - **Scenario**: [description]

   - **Input**: [test data]

   - **Expected**: [exception type]

   - **Type**: [unit/integration]

### Test Execution Results
```bash
# Run tests
./build/test_runner

# Run with Google Test
./build/test_runner --gtest_filter=*

# Run benchmarks
./build/benchmark_runner

# Expected output
[==========] Running 25 tests from 5 test suites.
[----------] Global test environment set-up.
[----------] 5 tests from UserServiceTest
[ RUN      ] UserServiceTest.CreateUser_WithValidData_ReturnsUserId
[       OK ] UserServiceTest.CreateUser_WithValidData_ReturnsUserId (0 ms)
...
[==========] 25 tests from 5 test suites ran. (123 ms total)
[  PASSED  ] 25 tests.
```

### Coverage Gaps Identified

- [ ] [Method]: Missing tests for [scenario]

- [ ] [Method]: Need edge case tests for [condition]

- [ ] [Method]: Exception handling not tested

- [ ] [Method]: Move semantics not tested

### Test Quality Metrics

- **Average test execution time**: [milliseconds]

- **Tests following AAA pattern**: [percentage]

- **Tests with clear names**: [percentage]

- **Independent tests**: [percentage]

- **Mock usage**: [appropriate/excessive]

### Next Steps

- [ ] Implement remaining test cases for coverage gaps

- [ ] Add performance benchmarks for critical methods

- [ ] Set up integration tests with test containers

- [ ] Configure CI/CD pipeline with CMake

- [ ] Review and refactor slow tests

- [ ] Add memory sanitizer tests

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

4. **Integration and benchmark tests** for workflows

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
