# Google Test + GitHub Copilot: Quick Reference

This guide provides ready-to-use prompts for generating comprehensive Google Test unit tests using GitHub Copilot Agent mode. Copy/paste these prompts directly into Copilot Chat for instant test generation.

---

## One-Line Prompts for Common Tasks

### Basic Test Generation
```
Generate Google Test unit tests for <ClassName> with FIRST principles and AAA pattern
```

**Example**:
```
Generate Google Test unit tests for Calculator with FIRST principles and AAA pattern
```

---

### Fixture-Based Tests
```
Create TEST_F fixture for <ClassName> with SetUp/TearDown. Test <method1>, <method2>, <method3>
```

**Example**:
```
Create TEST_F fixture for UserManager with SetUp/TearDown. Test createUser, deleteUser, updateUser
```

---

### Parametrized Tests
```
Generate TEST_P parametrized tests for <FunctionName> with values [val1, val2, val3]. Test edge cases
```

**Example**:
```
Generate TEST_P parametrized tests for validateAge with values [0, 17, 18, 65, 120, 121]. Test edge cases
```

---

### Mock Generation
```
Create Google Mock for <InterfaceName>. Generate tests with EXPECT_CALL for <ConcreteClass>
```

**Example**:
```
Create Google Mock for DatabaseConnection. Generate tests with EXPECT_CALL for UserRepository
```

---

### CMake Integration
```
Update tests/CMakeLists.txt to add test_<module>.cpp using add_gtest helper function
```

**Example**:
```
Update tests/CMakeLists.txt to add test_calculator.cpp using add_gtest helper function
```

---

### Exception Testing
```
Add tests verifying <ClassName>::<method> throws <ExceptionType> when <condition>
```

**Example**:
```
Add tests verifying Calculator::divide throws std::invalid_argument when divisor is zero
```

---

### Coverage Analysis
```
Generate tests to improve code coverage for <FileName>. Focus on uncovered branches
```

**Example**:
```
Generate tests to improve code coverage for UserValidator.cpp. Focus on uncovered branches
```

---

## Detailed Prompt Templates

### 1. Comprehensive Test Suite Generation

**Prompt**:
```
Generate comprehensive Google Test unit tests for <ClassName>.

Requirements:
- Use TEST() for stateless functions, TEST_F for stateful classes
- Follow AAA pattern (Arrange-Act-Assert)
- Include test cases for:
  * Happy path scenarios
  * Boundary values
  * Edge cases (empty, null, negative, overflow)
  * Error conditions
- Use appropriate assertions:
  * EXPECT_EQ / ASSERT_EQ for equality
  * EXPECT_THROW / ASSERT_THROW for exceptions
  * EXPECT_TRUE / ASSERT_TRUE for boolean checks
  * EXPECT_NEAR for floating-point comparisons (tolerance 0.0001)
- Follow FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)

Generate at least 15 comprehensive tests covering all public methods.

File location: tests/unit/<ClassName>Test.cpp
```

**Fill in**: Replace `<ClassName>` with your target class.

---

### 2. Fixture-Based Testing with Setup/Teardown

**Prompt**:
```
Create TEST_F fixture for <ClassName> with proper SetUp and TearDown.

Requirements:
- Define <ClassName>TestFixture class inheriting from ::testing::Test
- In SetUp():
  * Initialize test objects
  * Set up mock dependencies
  * Prepare test data
- In TearDown():
  * Clean up resources
  * Reset state
  * Release memory
- Create tests for: <method1>, <method2>, <method3>
- Each test should be independent and repeatable
- Use fixture member variables to share common setup

Generate fixture class and at least 10 tests.
```

**Fill in**: Replace `<ClassName>`, `<method1>`, `<method2>`, `<method3>`.

---

### 3. Parametrized Testing with Multiple Inputs

**Prompt**:
```
Generate TEST_P parametrized tests for <FunctionName>.

Requirements:
- Create test fixture: <FunctionName>ParamTest inheriting from ::testing::TestWithParam<<InputType>>
- Implement TEST_P with GetParam() to retrieve test values
- Use INSTANTIATE_TEST_SUITE_P with ::testing::Values() or ::testing::ValuesIn()
- Test these input values: [<val1>, <val2>, <val3>, ...]
- Include boundary values: minimum, maximum, zero, negative
- Test edge cases: empty, null, overflow, underflow
- Verify output for each input case

Generate parametrized fixture and test cases.
```

**Fill in**: Replace `<FunctionName>`, `<InputType>`, and values.

---

### 4. Google Mock Interface Testing

**Prompt**:
```
Create Google Mock for <InterfaceName> interface and generate tests for <ConcreteClass>.

Requirements:
- Define Mock<InterfaceName> class with MOCK_METHOD macros
- Mock all virtual methods from <InterfaceName>
- Create tests verifying <ConcreteClass> interactions:
  * Use EXPECT_CALL to set expectations
  * Verify method calls with correct arguments
  * Use matchers: Eq(), NotNull(), _, Gt(), Lt(), etc.
  * Verify call counts: Times(1), AtLeast(1), AtMost(3)
  * Set return values: WillOnce(Return(...)), WillRepeatedly(Return(...))
- Test both success and failure scenarios
- Verify exception propagation

Generate mock class and at least 8 tests.
```

**Fill in**: Replace `<InterfaceName>` and `<ConcreteClass>`.

---

### 5. Exception and Error Handling Tests

**Prompt**:
```
Add comprehensive exception handling tests for <ClassName>.

Requirements:
- Test each method that can throw exceptions
- Use EXPECT_THROW(<expression>, <ExceptionType>)
- Verify exception messages when applicable
- Test error conditions:
  * Invalid input (null, empty, negative)
  * Out-of-range values
  * Resource unavailable (file, network, database)
  * State violations (calling methods in wrong order)
- Use EXPECT_NO_THROW for methods that should never throw
- Test exception safety (resources cleaned up after throw)

Generate at least 10 exception tests.
```

**Fill in**: Replace `<ClassName>`.

---

### 6. CMake Test Integration

**Prompt**:
```
Update tests/CMakeLists.txt to integrate test_<module>.cpp with Google Test.

Requirements:
- Use add_gtest() helper function if available, or add_executable + target_link_libraries
- Link against:
  * GTest::gtest_main (provides main function)
  * GTest::gmock (for mocking)
  * Project library being tested
- Set include directories: ${CMAKE_SOURCE_DIR}/include
- Use gtest_discover_tests() for automatic test discovery by CTest
- Add to existing test suite structure

Example:
```cmake
add_gtest(test_<module>
    unit/<ModuleName>Test.cpp
)
```

Generate CMake configuration.
```

**Fill in**: Replace `<module>` and `<ModuleName>`.

---

## Conversation Flow Examples

These examples show iterative test generation with Copilot. Start broad, then refine with follow-up prompts.

### Example 1: New Class Testing (Calculator)

**Round 1 - Foundation**:
```
You: Generate unit tests for Calculator class (add, subtract, multiply, divide methods)
```

**Copilot generates**: Basic tests with happy path scenarios.

**Round 2 - Edge Cases**:
```
You: Add edge case tests for divide-by-zero and floating-point precision
```

**Copilot adds**:
```cpp
TEST(CalculatorTest, DivideByZeroThrowsException) {
    EXPECT_THROW(Calculator::divide(10.0, 0.0), std::invalid_argument);
}

TEST(CalculatorTest, FloatingPointPrecision) {
    double result = Calculator::divide(1.0, 3.0);
    EXPECT_NEAR(result, 0.333333, 0.0001);
}
```

**Round 3 - Parametrization**:
```
You: Create parametrized tests for all arithmetic operations with boundary values
```

**Copilot generates**: TEST_P with value sets for INT_MIN, INT_MAX, 0, positive, negative.

---

### Example 2: Integration Testing with Mocks (UserService)

**Round 1 - Mock Creation**:
```
You: Create Google Mock for DatabaseConnection interface
```

**Copilot generates**:
```cpp
class MockDatabaseConnection : public DatabaseConnection {
public:
    MOCK_METHOD(bool, connect, (), (override));
    MOCK_METHOD(void, disconnect, (), (override));
    MOCK_METHOD(bool, execute, (const std::string& query), (override));
};
```

**Round 2 - Basic Interaction Tests**:
```
You: Generate tests for UserService verifying it calls database.execute() exactly once when saving user
```

**Copilot generates**:
```cpp
TEST(UserServiceTest, SaveUserCallsDatabaseOnce) {
    MockDatabaseConnection mockDb;
    UserService service(&mockDb);

    EXPECT_CALL(mockDb, execute(_))
        .Times(1)
        .WillOnce(Return(true));

    User user("John", "john@example.com");
    service.save(user);
}
```

**Round 3 - Error Handling**:
```
You: Add test verifying UserService handles database exceptions correctly
```

**Copilot generates**:
```cpp
TEST(UserServiceTest, SaveUserHandlesDatabaseException) {
    MockDatabaseConnection mockDb;
    UserService service(&mockDb);

    EXPECT_CALL(mockDb, execute(_))
        .WillOnce(Throw(std::runtime_error("Connection failed")));

    User user("John", "john@example.com");
    EXPECT_THROW(service.save(user), std::runtime_error);
}
```

---

### Example 3: Refactoring Existing Tests

**Round 1 - Identify Duplication**:
```
You: Review CalculatorTest.cpp and identify duplicated setup code
```

**Copilot identifies**: Repeated Calculator object creation.

**Round 2 - Extract Fixture**:
```
You: Refactor tests to use TEST_F with shared fixture. Move Calculator initialization to SetUp()
```

**Copilot refactors**:
```cpp
class CalculatorTestFixture : public ::testing::Test {
protected:
    void SetUp() override {
        calculator = std::make_unique<Calculator>();
    }

    std::unique_ptr<Calculator> calculator;
};

TEST_F(CalculatorTestFixture, AddPositiveNumbers) {
    EXPECT_EQ(calculator->add(5, 3), 8);
}
```

**Round 3 - Optimize**:
```
You: Add helper methods to fixture for common operations (createTestData, assertCalculation)
```

---

## CMake Template for New Test Files

When Copilot generates a new test file, immediately update CMakeLists.txt:

### Standard Template

**Prompt**:
```
Update tests/CMakeLists.txt to add test_calculator.cpp
```

**Expected Output**:
```cmake
add_gtest(test_calculator unit/CalculatorTest.cpp)
```

### Full CMakeLists.txt Structure

If starting from scratch:

**Prompt**:
```
Create tests/CMakeLists.txt for Google Test project with modules: calculator, user, validator
```

**Expected Output**:
```cmake
include(GoogleTest)

function(add_gtest TEST_NAME)
    cmake_parse_arguments(ARG "" "" "SOURCES" ${ARGN})

    add_executable(${TEST_NAME} ${ARG_SOURCES})

    target_include_directories(${TEST_NAME} PRIVATE
        ${CMAKE_SOURCE_DIR}/include
    )

    target_link_libraries(${TEST_NAME} PRIVATE
        myproject_lib
        GTest::gtest_main
        GTest::gmock
    )

    gtest_discover_tests(${TEST_NAME}
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        PROPERTIES LABELS "unit"
    )
endfunction()

# Unit Tests
add_gtest(test_calculator unit/CalculatorTest.cpp)
add_gtest(test_user unit/UserTest.cpp)
add_gtest(test_validator unit/ValidatorTest.cpp)
```

---

## Debugging Copilot-Generated Tests

### Compilation Errors

**If tests don't compile**:
```
Fix compilation errors in test_calculator.cpp. Show all required include statements and namespace declarations
```

**Common Issues Copilot Will Fix**:
- Missing `#include <gtest/gtest.h>` or `#include <gmock/gmock.h>`
- Incorrect namespace (`testing::` vs `::testing::`)
- Missing forward declarations
- Type mismatches in EXPECT_EQ

---

### Test Failures

**If tests fail unexpectedly**:
```
Debug failing test CalculatorTest.DivideByZero. Add diagnostic logging showing actual vs expected values and explain why the test might be failing
```

**Copilot Will Add**:
```cpp
TEST(CalculatorTest, DivideByZero) {
    double result = 0.0;
    try {
        result = Calculator::divide(10.0, 0.0);
        std::cout << "ERROR: Expected exception but got result: " << result << std::endl;
        FAIL() << "Expected std::invalid_argument exception";
    } catch (const std::invalid_argument& e) {
        std::cout << "SUCCESS: Caught expected exception: " << e.what() << std::endl;
        SUCCEED();
    }
}
```

---

### Performance Issues

**If tests are slow**:
```
Optimize test_calculator.cpp. Replace real file I/O with mocks. Aim for <1ms per test. Profile and identify slow tests
```

**Copilot Will**:
- Replace file operations with mocks
- Remove unnecessary sleep/wait calls
- Use in-memory data structures
- Simplify complex setup

---

## Advanced Patterns

### 1. Memory Safety Verification

**Prompt**:
```
Add AddressSanitizer and UndefinedBehaviorSanitizer flags to CMakeLists.txt for test_calculator. Enable for Debug builds only
```

**Expected Output**:
```cmake
if(CMAKE_BUILD_TYPE MATCHES Debug)
    target_compile_options(test_calculator PRIVATE
        -fsanitize=address
        -fsanitize=undefined
        -fno-omit-frame-pointer
    )
    target_link_options(test_calculator PRIVATE
        -fsanitize=address
        -fsanitize=undefined
    )
endif()
```

---

### 2. Coverage-Driven Test Generation

**Workflow**:
```bash
# Step 1: Generate coverage report
cmake --build build --target coverage
open build/coverage/index.html

# Step 2: Identify uncovered lines (e.g., Calculator.cpp lines 45-52)

# Step 3: Prompt Copilot
Generate tests for Calculator.cpp lines 45-52 (multiply method edge cases). Cover:
- Multiplication by zero
- Negative number multiplication
- Overflow detection for INT_MAX * 2
```

**Copilot generates** tests specifically targeting those uncovered lines.

---

### 3. Property-Based Testing Patterns

**Prompt**:
```
Generate property-based tests for Calculator::add verifying:
- Commutativity: a + b == b + a
- Associativity: (a + b) + c == a + (b + c)
- Identity: a + 0 == a
Use parametrized tests with random values
```

**Expected Output**:
```cpp
class CalculatorPropertyTest : public ::testing::TestWithParam<std::tuple<int, int, int>> {};

TEST_P(CalculatorPropertyTest, AdditionCommutativity) {
    auto [a, b, c] = GetParam();
    EXPECT_EQ(Calculator::add(a, b), Calculator::add(b, a));
}

TEST_P(CalculatorPropertyTest, AdditionAssociativity) {
    auto [a, b, c] = GetParam();
    int left = Calculator::add(Calculator::add(a, b), c);
    int right = Calculator::add(a, Calculator::add(b, c));
    EXPECT_EQ(left, right);
}

INSTANTIATE_TEST_SUITE_P(
    PropertyTests,
    CalculatorPropertyTest,
    ::testing::Values(
        std::make_tuple(1, 2, 3),
        std::make_tuple(-5, 10, -3),
        std::make_tuple(0, 0, 0),
        std::make_tuple(100, -100, 50)
    )
);
```

---

### 4. Performance Regression Testing

**Prompt**:
```
Add Google Benchmark tests for Calculator::multiply. Measure throughput with 1M iterations. Set baseline performance threshold at 5ms
```

**Note**: Requires Google Benchmark library in addition to Google Test.

---

## Best Practices for Copilot Interaction

### ✅ DO:
1. **Start specific**: Target one class/method at a time
2. **Request patterns**: Ask for TEST_F, TEST_P, or MOCK_METHOD explicitly
3. **Specify assertions**: Request EXPECT_EQ, EXPECT_THROW, EXPECT_NEAR by name
4. **Iterate**: Build tests incrementally (basic → edge cases → mocks)
5. **Ask for explanations**: "Explain the test logic for CalculatorTest::DivideByZero"
6. **Request CMake updates**: Always ask Copilot to update CMakeLists.txt
7. **Verify coverage**: Ask Copilot to identify uncovered code paths

### ❌ DON'T:
1. **Don't go too broad**: "Generate tests for entire codebase" (too vague)
2. **Don't skip fixtures**: For stateful classes, always use TEST_F
3. **Don't trust blindly**: Review generated tests for correctness
4. **Don't ignore warnings**: Fix compilation errors immediately
5. **Don't over-mock**: Mock external dependencies, not internal logic
6. **Don't forget edge cases**: Explicitly request boundary value testing
7. **Don't neglect CMake**: Tests won't run without proper CMakeLists.txt

---

## Quick Keyboard Shortcuts

### VS Code + Copilot
```
Ctrl+Shift+I (Cmd+Shift+I on Mac)  → Open Copilot Chat
Ctrl+Enter                          → Submit prompt to Copilot
Ctrl+Shift+B                        → Build tests
F5                                  → Debug tests
Ctrl+Shift+P → "Tasks: Run Test"    → Run all tests
```

### Google Test CLI
```bash
./test_calculator                              # Run all tests
./test_calculator --gtest_filter=Calculator.*  # Run specific suite
./test_calculator --gtest_repeat=10            # Run 10 times
./test_calculator --gtest_shuffle              # Randomize order
./test_calculator --gtest_list_tests           # List all tests
```

---

## Integration with Workflow

This quick reference is designed to work with:

1. **VS Code Configuration**: Use `.vscode/` configs for one-click build/test
2. **Full Workflow Guide**: See [GOOGLE_TEST_VSCODE_WORKFLOW.md](../GOOGLE_TEST_VSCODE_WORKFLOW.md)
3. **Comprehensive Templates**: See [cpp_unit_tests.md](cpp_unit_tests.md) for detailed methodology

---

## Summary

**Fastest Path to Tests**:
1. Open Copilot Chat (`Ctrl+Shift+I`)
2. Paste: `Generate Google Test unit tests for <YourClass> with FIRST principles and AAA pattern`
3. Review and accept generated code
4. Build (`Ctrl+Shift+B`)
5. Run tests (Command Palette → "Tasks: Run Test Task")
6. Iterate with follow-up prompts for edge cases and mocks

**Estimated Time**: 5-10 minutes from prompt to running tests.

---

*For questions or issues, see troubleshooting in [VS Code Config README](../vscode_config/README.md) or [workflow guide](../GOOGLE_TEST_VSCODE_WORKFLOW.md).*
