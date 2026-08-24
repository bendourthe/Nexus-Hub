### Step 7: Test with GoogleTest and GMock

**Basic Tests and Fixtures**:

```cpp
#include <gtest/gtest.h>

// Simple test
TEST(MathTest, Addition) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_DOUBLE_EQ(divide(10.0, 3.0), 3.3333333333333335);
}

// EXPECT continues on failure; ASSERT aborts the test
TEST(ParserTest, ParseValidInput) {
    auto result = parse("42");
    ASSERT_TRUE(result.has_value()) << "parse returned nullopt";  // Aborts if false
    EXPECT_EQ(result.value(), 42);  // Only runs if ASSERT passed
}

// Test fixture: shared setup and teardown
class DatabaseTest : public ::testing::Test {
protected:
    void SetUp() override {
        db_ = std::make_unique<Database>(":memory:");
        db_->execute("CREATE TABLE users (id INT, name TEXT)");
    }
    void TearDown() override { db_.reset(); }

    std::unique_ptr<Database> db_;
};

TEST_F(DatabaseTest, InsertAndQuery) {
    db_->execute("INSERT INTO users VALUES (1, 'Alice')");
    auto rows = db_->query("SELECT name FROM users WHERE id = 1");
    ASSERT_EQ(rows.size(), 1u);
    EXPECT_EQ(rows[0]["name"], "Alice");
}

TEST_F(DatabaseTest, EmptyTableReturnsNoRows) {
    auto rows = db_->query("SELECT * FROM users");
    EXPECT_TRUE(rows.empty());
}
```

**Parameterized Tests**:

```cpp
// Value-parameterized tests
class FizzBuzzTest : public ::testing::TestWithParam<std::pair<int, std::string>> {};

TEST_P(FizzBuzzTest, ProducesCorrectOutput) {
    auto [input, expected] = GetParam();
    EXPECT_EQ(fizzbuzz(input), expected);
}

INSTANTIATE_TEST_SUITE_P(
    FizzBuzzCases,
    FizzBuzzTest,
    ::testing::Values(
        std::pair{1, "1"},
        std::pair{3, "Fizz"},
        std::pair{5, "Buzz"},
        std::pair{15, "FizzBuzz"}
    )
);

// Type-parameterized tests for generic code
template <typename T>
class StackTest : public ::testing::Test {
protected:
    Stack<T> stack_;
};

using StackTypes = ::testing::Types<int, double, std::string>;
TYPED_TEST_SUITE(StackTest, StackTypes);

TYPED_TEST(StackTest, PushAndPop) {
    TypeParam value{};  // Default-constructed value of the type under test
    this->stack_.push(value);
    EXPECT_FALSE(this->stack_.empty());
    EXPECT_EQ(this->stack_.pop(), value);
    EXPECT_TRUE(this->stack_.empty());
}
```

**Death Tests and GMock**:

```cpp
// Death tests verify that code terminates as expected
TEST(ContractTest, NullPointerAborts) {
    EXPECT_DEATH(dereference(nullptr), "");  // Expects termination
}

TEST(ContractTest, OutOfRangeThrows) {
    std::vector<int> v{1, 2, 3};
    EXPECT_THROW(v.at(10), std::out_of_range);
    EXPECT_NO_THROW(v.at(0));
}

// GMock for interface mocking
#include <gmock/gmock.h>

class Logger {
public:
    virtual ~Logger() = default;
    virtual void log(const std::string& message) = 0;
    virtual int count() const = 0;
};

class MockLogger : public Logger {
public:
    MOCK_METHOD(void, log, (const std::string& message), (override));
    MOCK_METHOD(int, count, (), (const, override));
};

TEST(ServiceTest, LogsOnStartup) {
    MockLogger logger;
    EXPECT_CALL(logger, log(::testing::HasSubstr("started")))
        .Times(1);
    EXPECT_CALL(logger, count())
        .WillOnce(::testing::Return(1));

    Service service(logger);
    service.start();

    EXPECT_EQ(logger.count(), 1);
}
```

**CMake Integration and Sanitizers**:

```cmake
# CMakeLists.txt
cmake_minimum_required(VERSION 3.20)
project(my_project LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Fetch GoogleTest
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG        v1.14.0
)
FetchContent_MakeAvailable(googletest)

# Library under test
add_library(mylib src/math.cpp src/parser.cpp)
target_include_directories(mylib PUBLIC include/)

# Test executable
add_executable(tests tests/math_test.cpp tests/parser_test.cpp)
target_link_libraries(tests PRIVATE mylib GTest::gtest_main GTest::gmock)

# Register with CTest
include(GoogleTest)
gtest_discover_tests(tests)

# Sanitizer build type (run with: cmake -DCMAKE_BUILD_TYPE=Sanitize ..)
if(CMAKE_BUILD_TYPE STREQUAL "Sanitize")
    target_compile_options(tests PRIVATE -fsanitize=address,undefined -fno-omit-frame-pointer)
    target_link_options(tests PRIVATE -fsanitize=address,undefined)
endif()
```

```bash
# Build and run tests with sanitizers enabled
cmake -B build -DCMAKE_BUILD_TYPE=Sanitize
cmake --build build
ctest --test-dir build --output-on-failure
```
