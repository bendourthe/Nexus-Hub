---
template_id: cpp_unit_tests
template_name: Unit Tests - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: test_development
phase: unit_tests
phase_number: 2
difficulty: intermediate
estimated_time_hours: 3-6
prerequisites:

  - test_development/test_structure/cpp_test_structure.md
related_templates:

  - test_development/test_cases/cpp_test_cases.md
tools:

  - google test

  - catch2

  - boost.test
tags:

  - test-development

  - testing

  - cpp
---
# C++ Unit Tests - Comprehensive Implementation Guide

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

Develop comprehensive unit testing strategy for C++ applications using Google Test and Catch2 frameworks, focusing on test isolation, RAII testing, template testing, and thorough coverage following modern C++ best practices and FIRST principles.

---

## Output Directory Structure

```
${OUTPUT_DIR}/
├── templates/           # Reusable test templates
├── assets/             # Diagrams and visualizations
└── exports/            # Final documentation
```

---

## Implementation Checklist

### Test Foundation
- [ ] Google Test and Catch2 comparison

- [ ] Test project structure (CMake)

- [ ] Modern C++ features in tests

- [ ] Mock framework (Google Mock)

### Test Patterns
- [ ] Function and method tests

- [ ] Class tests with RAII

- [ ] Template tests

- [ ] Exception tests

- [ ] Move semantics tests

### Test Quality
- [ ] Memory safety verification

- [ ] Valgrind/AddressSanitizer

- [ ] Coverage analysis

- [ ] Edge cases covered

---

## 🤖 GitHub Copilot Agent Mode Integration

### Quick Start: Clone → Generate Tests → Run

This section enables you to use GitHub Copilot to automatically generate comprehensive Google Test unit tests for your C++ codebase.

#### Step 1: Clone & Open in VS Code

```bash
git clone <your-repo>
cd <your-repo>
code .  # Opens VS Code
```

#### Step 2: Set Up VS Code Configuration

1. **Install Required Extensions**:

   - CMake Tools (`twxs.cmake`)

   - C/C++ Extension Pack (`ms-vscode.cpptools-extension-pack`)

   - Test Explorer UI (`hbenl.vscode-test-explorer`)

   - GitHub Copilot (`GitHub.copilot`)

2. **Copy VS Code Configuration**:
   ```bash
   mkdir -p .vscode
   cp templates/test_development/vscode_config/*.json .vscode/
   ```

   See [VS Code Config Documentation](../vscode_config/README.md) for details.

3. **Reload VS Code**: `Ctrl+Shift+P` → "Developer: Reload Window"

#### Step 3: Generate Tests with GitHub Copilot

1. **Open GitHub Copilot Chat**: `Ctrl+Shift+I` (or `Cmd+Shift+I` on Mac)

2. **Copy the Prompt Template section below** (starting at "## Prompt Template")

3. **Paste into Copilot Chat** - Copilot will generate comprehensive unit tests

4. **Review and Accept** the generated tests

#### Step 4: Build & Run Tests

- **Build**: `Ctrl+Shift+B` (or Command Palette → "CMake: Build")

- **Run Tests**: Command Palette → "Tasks: Run Test Task" → "Run All Tests"

- **Debug Tests**: Set breakpoints → Press `F5`

---

### Iterative Test Generation Pattern

Use these follow-up prompts with Copilot to refine your tests:

**1. Add Parametrized Tests**:
```
Add parametrized tests for <ClassName>::<method> using TEST_P.
Test boundary values: [<val1>, <val2>, <val3>]
```

**2. Create Mocks**:
```
Create Google Mock for <InterfaceName>.
Generate tests verifying <ClassName> calls methods correctly.
Use EXPECT_CALL with matchers (Eq, NotNull, _).
```

**3. Add Exception Tests**:
```
Add tests verifying <ClassName>::<method> throws <ExceptionType> when <condition>
```

**4. Improve Coverage**:
```
Generate tests for uncovered lines in <FileName>.
Focus on edge cases and error handling.
```

---

### Copilot Best Practices

**✅ DO:**

- Start with a single class/component

- Request specific test patterns (fixtures, mocks, parametrized)

- Ask for both happy path and error cases

- Request CMake integration updates

- Ask Copilot to explain test logic

**❌ DON'T:**

- Generate tests for entire codebase at once (too broad)

- Skip fixture setup for stateful classes

- Generate tests without understanding the code

- Ignore compilation errors (fix incrementally)

---

### Complete Workflow Documentation

For detailed step-by-step instructions, see:

- **[Complete Workflow Guide](../GOOGLE_TEST_VSCODE_WORKFLOW.md)** - End-to-end setup (10 minutes)

- **[Copilot Quick Reference](COPILOT_QUICK_REFERENCE.md)** - One-line prompts and examples

- **[VS Code Configuration](../vscode_config/README.md)** - Detailed config explanations

**Estimated Time**: 10 minutes from clone to first test run

---

## Prompt Template

~~~markdown
# C++ Unit Testing Implementation - Comprehensive Guide

## Context
Generate comprehensive guidance for implementing unit tests in C++ using Google Test and Catch2 frameworks with modern C++ examples.

## CRITICAL: Output Directory Setup

```bash
mkdir -p ${OUTPUT_DIR}/templates ${OUTPUT_DIR}/assets ${OUTPUT_DIR}/exports
```

---

## Phase 1: C++ Testing Fundamentals

### 1.1 FIRST Principles

**Fast** - Tests execute quickly

- Use mock objects

- Avoid file I/O

- Test pure functions

**Independent** - No shared state

- RAII handles cleanup

- Each test creates own objects

- Use test fixtures

**Repeatable** - Deterministic

- Mock time/random

- Control dependencies

- Initialize all state

**Self-validating** - Clear assertions

- Use framework macros

- Fluent assertions

- Descriptive messages

**Timely** - Written with code

- TDD practices

- High coverage

**AAA Pattern:**
```cpp
TEST(CalculatorTest, CalculateDiscount_WithValidRate_ReturnsDiscountedPrice) {
    // Arrange
    Calculator calculator;
    double price = 100.0;
    double discountRate = 0.20;

    // Act
    double result = calculator.calculateDiscount(price, discountRate);

    // Assert
    EXPECT_DOUBLE_EQ(80.0, result);
}
```

### 1.2 Framework Comparison

**Google Test:**

- Industry standard

- Rich assertion macros

- Test fixtures

- Google Mock integration

- Mature ecosystem

**Catch2:**

- Header-only

- BDD-style syntax

- Self-contained

- Modern C++ features

- Lighter weight

---

## Phase 2: Project Organization

### 2.1 CMake Project Structure

```
project/
├── include/
│   └── myproject/
│       ├── calculator.hpp
│       └── user.hpp
├── src/
│   ├── calculator.cpp
│   └── user.cpp
├── tests/
│   ├── calculator_test.cpp
│   ├── user_test.cpp
│   └── CMakeLists.txt
├── CMakeLists.txt
└── README.md
```

### 2.2 CMake Configuration

**Root CMakeLists.txt:**
```cmake
cmake_minimum_required(VERSION 3.14)
project(MyProject VERSION 1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Enable testing
enable_testing()

# Add Google Test
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
FetchContent_MakeAvailable(googletest)

# Source library
add_library(myproject_lib
    src/calculator.cpp
    src/user.cpp
)
target_include_directories(myproject_lib PUBLIC include)

# Tests
add_subdirectory(tests)
```

**tests/CMakeLists.txt:**
```cmake
add_executable(unit_tests
    calculator_test.cpp
    user_test.cpp
)

target_link_libraries(unit_tests
    PRIVATE
    myproject_lib
    gtest_main
    gmock
)

include(GoogleTest)
gtest_discover_tests(unit_tests)
```

### 2.3 Test Naming Conventions

**File Naming:**

- `<class>_test.cpp`

- Examples: `calculator_test.cpp`, `user_test.cpp`

**Test Naming:**

- `TEST(TestSuiteName, TestName)`

- `TEST_F(TestFixture, TestName)`

- Use descriptive names

```cpp
TEST(CalculatorTest, CalculateDiscount_WithValidRate_ReturnsCorrectValue)
TEST(CalculatorTest, CalculateDiscount_WithNegativePrice_ThrowsException)
TEST(UserTest, Constructor_WithValidEmail_CreatesUser)
```

---

## Phase 3: Testing Different Components

### 3.1 Testing Functions and Methods

**Example (calculator.hpp):**
```cpp
#pragma once
#include <stdexcept>

class Calculator {
public:
    double calculateDiscount(double price, double discountRate) {
        if (price < 0.0) {
            throw std::invalid_argument("Price cannot be negative");
        }
        if (discountRate < 0.0 || discountRate > 1.0) {
            throw std::invalid_argument("Discount rate must be between 0 and 1");
        }
        return price * (1.0 - discountRate);
    }
};
```

**Tests (calculator_test.cpp):**
```cpp
#include <gtest/gtest.h>
#include "myproject/calculator.hpp"

class CalculatorTest : public ::testing::Test {
protected:
    Calculator calculator;
};

TEST_F(CalculatorTest, CalculateDiscount_WithNoDiscount_ReturnsOriginalPrice) {
    double result = calculator.calculateDiscount(100.0, 0.0);
    EXPECT_DOUBLE_EQ(100.0, result);
}

TEST_F(CalculatorTest, CalculateDiscount_WithFullDiscount_ReturnsZero) {
    double result = calculator.calculateDiscount(100.0, 1.0);
    EXPECT_DOUBLE_EQ(0.0, result);
}

TEST_F(CalculatorTest, CalculateDiscount_WithTwentyPercent_ReturnsEighty) {
    double result = calculator.calculateDiscount(100.0, 0.20);
    EXPECT_DOUBLE_EQ(80.0, result);
}

TEST_F(CalculatorTest, CalculateDiscount_WithNegativePrice_ThrowsException) {
    EXPECT_THROW(
        calculator.calculateDiscount(-100.0, 0.20),
        std::invalid_argument
    );
}

TEST_F(CalculatorTest, CalculateDiscount_WithInvalidRate_ThrowsException) {
    EXPECT_THROW(
        calculator.calculateDiscount(100.0, 1.5),
        std::invalid_argument
    );
}

// Parameterized tests
using DiscountParams = std::tuple<double, double, double>;

class ParameterizedCalculatorTest : public ::testing::TestWithParam<DiscountParams> {};

TEST_P(ParameterizedCalculatorTest, CalculateDiscount_VariousCombinations) {
    Calculator calculator;
    auto [price, rate, expected] = GetParam();

    double result = calculator.calculateDiscount(price, rate);

    EXPECT_NEAR(expected, result, 0.01);
}

INSTANTIATE_TEST_SUITE_P(
    DiscountCalculations,
    ParameterizedCalculatorTest,
    ::testing::Values(
        std::make_tuple(100.0, 0.10, 90.0),
        std::make_tuple(50.0, 0.20, 40.0),
        std::make_tuple(200.0, 0.25, 150.0),
        std::make_tuple(75.0, 0.333, 50.025)
    )
);
```

### 3.2 Testing Classes with RAII

**Example (user.hpp):**
```cpp
#pragma once
#include <string>
#include <memory>
#include <stdexcept>
#include <regex>

class User {
private:
    std::string name_;
    std::string email_;
    int age_;
    bool active_;

    static bool isValidEmail(const std::string& email) {
        static const std::regex pattern(R"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})");
        return std::regex_match(email, pattern);
    }

public:
    User(std::string name, std::string email, int age)
        : name_(std::move(name)), email_(std::move(email)), age_(age), active_(true) {

        if (name_.empty()) {
            throw std::invalid_argument("Name cannot be empty");
        }
        if (!isValidEmail(email_)) {
            throw std::invalid_argument("Invalid email format");
        }
        if (age_ < 0) {
            throw std::invalid_argument("Age cannot be negative");
        }
    }

    const std::string& getName() const { return name_; }
    const std::string& getEmail() const { return email_; }
    int getAge() const { return age_; }
    bool isActive() const { return active_; }

    void deactivate() { active_ = false; }
    void activate() { active_ = true; }
};
```

**Tests (user_test.cpp):**
```cpp
#include <gtest/gtest.h>
#include "myproject/user.hpp"

class UserTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup before each test
    }

    void TearDown() override {
        // Cleanup after each test
    }
};

TEST_F(UserTest, Constructor_WithValidInputs_CreatesUser) {
    User user("John Doe", "john@example.com", 30);

    EXPECT_EQ("John Doe", user.getName());
    EXPECT_EQ("john@example.com", user.getEmail());
    EXPECT_EQ(30, user.getAge());
    EXPECT_TRUE(user.isActive());
}

TEST_F(UserTest, Constructor_WithEmptyName_ThrowsException) {
    EXPECT_THROW(
        User("", "john@example.com", 30),
        std::invalid_argument
    );
}

TEST_F(UserTest, Constructor_WithInvalidEmail_ThrowsException) {
    EXPECT_THROW(
        User("John", "invalid-email", 30),
        std::invalid_argument
    );
}

TEST_F(UserTest, Constructor_WithNegativeAge_ThrowsException) {
    EXPECT_THROW(
        User("John", "john@example.com", -5),
        std::invalid_argument
    );
}

TEST_F(UserTest, Deactivate_SetsActiveToFalse) {
    User user("John", "john@example.com", 30);
    user.deactivate();

    EXPECT_FALSE(user.isActive());
}

TEST_F(UserTest, Activate_AfterDeactivate_SetsActiveToTrue) {
    User user("John", "john@example.com", 30);
    user.deactivate();
    user.activate();

    EXPECT_TRUE(user.isActive());
}

// Testing move semantics
TEST_F(UserTest, MoveConstructor_TransfersOwnership) {
    User user1("John", "john@example.com", 30);
    User user2(std::move(user1));

    EXPECT_EQ("John", user2.getName());
    // user1 is in valid but unspecified state after move
}
```

### 3.3 Testing Templates

**Example (container.hpp):**
```cpp
#pragma once
#include <vector>
#include <algorithm>
#include <stdexcept>

template<typename T>
class Container {
private:
    std::vector<T> items_;

public:
    void add(const T& item) {
        items_.push_back(item);
    }

    void add(T&& item) {
        items_.emplace_back(std::move(item));
    }

    size_t size() const {
        return items_.size();
    }

    bool empty() const {
        return items_.empty();
    }

    const T& at(size_t index) const {
        if (index >= items_.size()) {
            throw std::out_of_range("Index out of range");
        }
        return items_[index];
    }

    void clear() {
        items_.clear();
    }

    std::vector<T> filter(std::function<bool(const T&)> predicate) const {
        std::vector<T> result;
        std::copy_if(items_.begin(), items_.end(),
                     std::back_inserter(result), predicate);
        return result;
    }
};
```

**Tests:**
```cpp
#include <gtest/gtest.h>
#include "myproject/container.hpp"

TEST(ContainerTest, Add_AddsItemToContainer) {
    Container<int> container;
    container.add(42);

    EXPECT_EQ(1, container.size());
    EXPECT_EQ(42, container.at(0));
}

TEST(ContainerTest, Empty_InitiallyReturnsTrue) {
    Container<std::string> container;

    EXPECT_TRUE(container.empty());
}

TEST(ContainerTest, Empty_AfterAddingItem_ReturnsFalse) {
    Container<std::string> container;
    container.add("test");

    EXPECT_FALSE(container.empty());
}

TEST(ContainerTest, At_WithValidIndex_ReturnsItem) {
    Container<int> container;
    container.add(10);
    container.add(20);

    EXPECT_EQ(10, container.at(0));
    EXPECT_EQ(20, container.at(1));
}

TEST(ContainerTest, At_WithInvalidIndex_ThrowsException) {
    Container<int> container;
    container.add(42);

    EXPECT_THROW(container.at(10), std::out_of_range);
}

TEST(ContainerTest, Clear_EmptiesContainer) {
    Container<int> container;
    container.add(1);
    container.add(2);
    container.clear();

    EXPECT_TRUE(container.empty());
    EXPECT_EQ(0, container.size());
}

TEST(ContainerTest, Filter_WithPredicate_ReturnsFilteredItems) {
    Container<int> container;
    container.add(1);
    container.add(2);
    container.add(3);
    container.add(4);

    auto even = container.filter([](int n) { return n % 2 == 0; });

    ASSERT_EQ(2, even.size());
    EXPECT_EQ(2, even[0]);
    EXPECT_EQ(4, even[1]);
}

// Template instantiation with different types
TEST(ContainerTest, WorksWithStrings) {
    Container<std::string> container;
    container.add("hello");
    container.add("world");

    EXPECT_EQ(2, container.size());
    EXPECT_EQ("hello", container.at(0));
}

TEST(ContainerTest, WorksWithCustomTypes) {
    struct Point {
        int x, y;
        bool operator==(const Point& other) const {
            return x == other.x && y == other.y;
        }
    };

    Container<Point> container;
    container.add(Point{1, 2});
    container.add(Point{3, 4});

    EXPECT_EQ(2, container.size());
    EXPECT_EQ(Point{1, 2}, container.at(0));
}
```

### 3.4 Testing with Google Mock

**Example (user_repository.hpp):**
```cpp
#pragma once
#include "user.hpp"
#include <memory>
#include <optional>

class UserRepository {
public:
    virtual ~UserRepository() = default;
    virtual std::optional<User> findById(int id) = 0;
    virtual void save(const User& user) = 0;
    virtual void remove(int id) = 0;
};

class UserService {
private:
    std::shared_ptr<UserRepository> repository_;

public:
    explicit UserService(std::shared_ptr<UserRepository> repository)
        : repository_(std::move(repository)) {}

    std::optional<User> getUser(int id) {
        if (id <= 0) {
            throw std::invalid_argument("Invalid user ID");
        }
        return repository_->findById(id);
    }

    void activateUser(int id) {
        auto user = repository_->findById(id);
        if (user) {
            user->activate();
            repository_->save(*user);
        }
    }
};
```

**Tests with Mocks:**
```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "myproject/user_repository.hpp"

using ::testing::Return;
using ::testing::_;
using ::testing::NiceMock;

class MockUserRepository : public UserRepository {
public:
    MOCK_METHOD(std::optional<User>, findById, (int id), (override));
    MOCK_METHOD(void, save, (const User& user), (override));
    MOCK_METHOD(void, remove, (int id), (override));
};

class UserServiceTest : public ::testing::Test {
protected:
    std::shared_ptr<MockUserRepository> mockRepository;
    std::unique_ptr<UserService> service;

    void SetUp() override {
        mockRepository = std::make_shared<NiceMock<MockUserRepository>>();
        service = std::make_unique<UserService>(mockRepository);
    }
};

TEST_F(UserServiceTest, GetUser_WithValidId_CallsRepository) {
    User expectedUser("John", "john@example.com", 30);
    EXPECT_CALL(*mockRepository, findById(1))
        .WillOnce(Return(std::make_optional(expectedUser)));

    auto user = service->getUser(1);

    ASSERT_TRUE(user.has_value());
    EXPECT_EQ("John", user->getName());
}

TEST_F(UserServiceTest, GetUser_WithInvalidId_ThrowsException) {
    EXPECT_THROW(service->getUser(0), std::invalid_argument);
}

TEST_F(UserServiceTest, ActivateUser_WithExistingUser_ActivatesAndSaves) {
    User user("John", "john@example.com", 30);
    user.deactivate();

    EXPECT_CALL(*mockRepository, findById(1))
        .WillOnce(Return(std::make_optional(user)));
    EXPECT_CALL(*mockRepository, save(_))
        .Times(1);

    service->activateUser(1);
}

TEST_F(UserServiceTest, ActivateUser_WithNonExistentUser_DoesNotSave) {
    EXPECT_CALL(*mockRepository, findById(999))
        .WillOnce(Return(std::nullopt));
    EXPECT_CALL(*mockRepository, save(_))
        .Times(0);

    service->activateUser(999);
}
```

### 3.5 Testing Exception Safety

```cpp
#include <gtest/gtest.h>
#include <vector>
#include <stdexcept>

class Resource {
public:
    explicit Resource(bool shouldThrow = false) {
        if (shouldThrow) {
            throw std::runtime_error("Construction failed");
        }
        data_ = std::make_unique<std::vector<int>>(100);
    }

private:
    std::unique_ptr<std::vector<int>> data_;
};

TEST(ExceptionSafetyTest, Constructor_ThrowingInInitialization_NoLeak) {
    // AddressSanitizer would detect leaks
    EXPECT_THROW(Resource(true), std::runtime_error);
}

TEST(ExceptionSafetyTest, StrongExceptionGuarantee_RollsBackOnFailure) {
    std::vector<int> vec = {1, 2, 3};

    EXPECT_THROW({
        vec.reserve(vec.max_size() + 1); // Will throw
    }, std::length_error);

    // Vector should be unchanged
    EXPECT_EQ(3, vec.size());
    EXPECT_EQ(std::vector<int>({1, 2, 3}), vec);
}
```

---

## Phase 4: Advanced Testing

### 4.1 Using Catch2 (Alternative)

```cpp
#define CATCH_CONFIG_MAIN
#include <catch2/catch.hpp>
#include "myproject/calculator.hpp"

TEST_CASE("Calculator discount calculations", "[calculator]") {
    Calculator calculator;

    SECTION("No discount returns original price") {
        REQUIRE(calculator.calculateDiscount(100.0, 0.0) == 100.0);
    }

    SECTION("Full discount returns zero") {
        REQUIRE(calculator.calculateDiscount(100.0, 1.0) == 0.0);
    }

    SECTION("20% discount calculates correctly") {
        REQUIRE(calculator.calculateDiscount(100.0, 0.20) == Approx(80.0));
    }

    SECTION("Negative price throws exception") {
        REQUIRE_THROWS_AS(
            calculator.calculateDiscount(-100.0, 0.20),
            std::invalid_argument
        );
    }
}

SCENARIO("User activation workflow", "[user]") {
    GIVEN("A newly created user") {
        User user("John", "john@example.com", 30);

        REQUIRE(user.isActive() == true);

        WHEN("The user is deactivated") {
            user.deactivate();

            THEN("The user should be inactive") {
                REQUIRE(user.isActive() == false);
            }

            AND_WHEN("The user is activated again") {
                user.activate();

                THEN("The user should be active") {
                    REQUIRE(user.isActive() == true);
                }
            }
        }
    }
}
```

### 4.2 Memory Safety with AddressSanitizer

**CMakeLists.txt:**
```cmake
if(CMAKE_BUILD_TYPE MATCHES Debug)
    target_compile_options(unit_tests PRIVATE
        -fsanitize=address
        -fsanitize=undefined
        -fno-omit-frame-pointer
    )
    target_link_options(unit_tests PRIVATE
        -fsanitize=address
        -fsanitize=undefined
    )
endif()
```

**Run tests:**
```bash
cmake -DCMAKE_BUILD_TYPE=Debug ..
make
./unit_tests
```

### 4.3 Code Coverage

**CMakeLists.txt:**
```cmake
option(CODE_COVERAGE "Enable coverage reporting" OFF)

if(CODE_COVERAGE)
    target_compile_options(unit_tests PRIVATE --coverage)
    target_link_options(unit_tests PRIVATE --coverage)
endif()
```

**Generate coverage:**
```bash
cmake -DCODE_COVERAGE=ON ..
make
./unit_tests
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

### 4.4 Google Test Assertions

```cpp
// Basic assertions
EXPECT_TRUE(condition);
EXPECT_FALSE(condition);
ASSERT_TRUE(condition);  // Fatal failure

// Equality
EXPECT_EQ(expected, actual);
EXPECT_NE(val1, val2);
EXPECT_LT(val1, val2);
EXPECT_LE(val1, val2);
EXPECT_GT(val1, val2);
EXPECT_GE(val1, val2);

// Floating point
EXPECT_FLOAT_EQ(expected, actual);
EXPECT_DOUBLE_EQ(expected, actual);
EXPECT_NEAR(val1, val2, abs_error);

// String
EXPECT_STREQ(str1, str2);
EXPECT_STRNE(str1, str2);
EXPECT_STRCASEEQ(str1, str2);

// Exceptions
EXPECT_THROW(statement, exception_type);
EXPECT_NO_THROW(statement);
EXPECT_ANY_THROW(statement);

// Predicates
EXPECT_PRED1(pred, val);
EXPECT_PRED2(pred, val1, val2);
```

---

## Phase 5: Best Practices

### 5.1 Test Organization

```cpp
// Use test fixtures for setup/teardown
class DatabaseTest : public ::testing::Test {
protected:
    void SetUp() override {
        db = std::make_unique<Database>("test.db");
    }

    void TearDown() override {
        db->close();
    }

    std::unique_ptr<Database> db;
};

// Group related tests
TEST_F(DatabaseTest, Insert_AddsRecord) { }
TEST_F(DatabaseTest, Query_ReturnsResults) { }

// Use descriptive names
TEST(VectorTest, PushBack_IncreasesSize) { }
TEST(VectorTest, PopBack_OnEmptyVector_ThrowsException) { }
```

### 5.2 Maintenance Checklist

- [ ] All tests pass independently

- [ ] RAII used properly

- [ ] No memory leaks (AddressSanitizer clean)

- [ ] Exception safety verified

- [ ] Move semantics tested

- [ ] Templates tested with multiple types

- [ ] Mocks used appropriately

- [ ] >80% code coverage

- [ ] No undefined behavior

- [ ] Clear test names

---

## Output Deliverables

### 1. Implementation Guide (20-30 pages)
`${OUTPUT_DIR}/exports/unit_test_implementation_guide.md`

### 2. Test Examples (50+ tests)
`${OUTPUT_DIR}/exports/unit_test_examples.md`

### 3. Templates
`${OUTPUT_DIR}/templates/`:

- `test_template.cpp`

- `fixture_template.cpp`

- `mock_template.cpp`

- `CMakeLists.txt`

### 4. Guides
- RAII testing guide

- Template testing guide

- Mock usage guide (GMock)

- Memory safety guide

- Coverage guide

- Quality checklist

---

## Verification Checklist

- [ ] All deliverables created

- [ ] 20-30 page guide

- [ ] 50+ test examples

- [ ] Google Test covered

- [ ] Catch2 examples included

- [ ] Template testing

- [ ] RAII patterns

- [ ] Move semantics

- [ ] GMock patterns

- [ ] Modern C++ (C++17+)

---
~~~

End of prompt template.

---

## Additional Notes

- Build: `cmake -B build && cmake --build build`

- Run tests: `./build/unit_tests`

- With ASan: `cmake -DCMAKE_BUILD_TYPE=Debug -B build`

- Coverage: `cmake -DCODE_COVERAGE=ON -B build`

- Valgrind: `valgrind --leak-check=full ./build/unit_tests`

---

**Status:** Template ready. Copy the prompt into your AI assistant for comprehensive C++ unit testing guidance.
