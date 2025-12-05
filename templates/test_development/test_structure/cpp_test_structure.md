---
template_id: cpp_test_structure
template_name: Test Structure Setup - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: test_development
phase: test_structure
phase_number: 1
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
related_templates:

  - test_development/unit_tests/cpp_unit_tests.md
tools:

  - google test

  - catch2

  - boost.test
tags:

  - test-development

  - testing

  - cpp
---
# C++ Test Structure & Infrastructure

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                   ► │ ● CURRENT
│ Phase 2: Unit Tests                                ► │ [NEXT]
│ Phase 3: Test Cases Development                          ► │ 
│ Phase 4: Mocks & Fixtures                                ► │ 
│ Phase 5: Performance Testing                             ► │ 
│ Phase 6: Code Coverage                                   ► │ 
│ Phase 7: Maintenance & CI/CD                             ► │ 
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** None - This is the starting phase
**Next Step:** Phase 2 (Unit Tests)

---


## Objective
Design and implement a robust test infrastructure with optimal framework configuration, logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices using GoogleTest, Catch2, or Boost.Test frameworks.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/test_structure/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/test_structure/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Test Framework Setup

- [ ] Test framework selected (GoogleTest/Catch2/Boost.Test)

- [ ] Build system configured (CMake/Make)

- [ ] Framework dependencies installed

- [ ] Test discovery configured

- [ ] Coverage tools configured (gcov/lcov)

### Directory Structure

- [ ] Standard test layout implemented

- [ ] Test type separation organized

- [ ] Naming conventions documented

- [ ] Test data directories created

- [ ] Header organization established

### Fixture Infrastructure

- [ ] Test fixtures defined

- [ ] Setup/teardown methods established

- [ ] Parameterized tests configured

- [ ] Fixture documentation added

- [ ] Common fixtures centralized

### Test Utilities

- [ ] Custom matchers created

- [ ] Test data builders implemented

- [ ] Helper classes defined

- [ ] Mock utilities established

- [ ] Helper documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Test Infrastructure Setup

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/test_structure"
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

Please design and implement a comprehensive test infrastructure for this C++ project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Framework Selection & Configuration

1. **Test Framework Analysis**

   - **Current State**: Document existing test setup if any

   - **Framework Recommendations**:

     - **GoogleTest** (recommended): Industry standard, Google-backed, feature-rich

     - **Catch2**: Header-only option, BDD-style, modern C++

     - **Boost.Test**: Part of Boost, well-integrated if already using Boost

     - **doctest**: Fast compile times, header-only, similar to Catch2

   - **Rationale**: Justify framework choice based on project needs

2. **Install Test Framework**

   **GoogleTest** (recommended):
   ```bash
   # Using package manager
   # Ubuntu/Debian
   sudo apt-get install libgtest-dev

   # macOS
   brew install googletest

   # Or as Git submodule
   git submodule add <REPO_URL> third_party/googletest
   git submodule update --init --recursive

   # Or with CMake FetchContent (recommended)
   # See CMakeLists.txt below
   ```

   **Catch2**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install catch2

   # macOS
   brew install catch2

   # Or as Git submodule
   git submodule add <REPO_URL> third_party/catch2

   # Or single header (v2.x)
   wget https://raw.githubusercontent.com/catchorg/Catch2/v2.x/single_include/catch2/catch.hpp \
       -O third_party/catch.hpp
   ```

   **GoogleMock** (mocking framework):
   ```bash
   # Included with GoogleTest
   # No separate installation needed
   ```

3. **CMake Build Configuration**

   **CMakeLists.txt** (root):
   ```cmake
   cmake_minimum_required(VERSION 3.15)
   project(MyApp CXX)

   set(CMAKE_CXX_STANDARD 17)
   set(CMAKE_CXX_STANDARD_REQUIRED ON)
   set(CMAKE_CXX_EXTENSIONS OFF)

   # Compiler flags
   set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Werror -pedantic")
   set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0 --coverage")
   set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -DNDEBUG")

   # Enable testing
   enable_testing()
   include(CTest)

   # Fetch GoogleTest
   include(FetchContent)
   FetchContent_Declare(
       googletest
       GIT_REPOSITORY https://github.com/google/googletest.git
       GIT_TAG v1.14.0
   )
   # For Windows: Prevent overriding the parent project's compiler/linker settings
   set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
   FetchContent_MakeAvailable(googletest)

   # Include directories
   include_directories(${CMAKE_SOURCE_DIR}/include)
   include_directories(${CMAKE_SOURCE_DIR}/src)

   # Add source library
   add_subdirectory(src)

   # Add tests
   add_subdirectory(tests)

   # Code coverage target
   if(CMAKE_BUILD_TYPE STREQUAL "Debug")
       find_program(LCOV lcov REQUIRED)
       find_program(GENHTML genhtml REQUIRED)

       add_custom_target(coverage
           COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/coverage
           COMMAND ${LCOV} --directory . --zerocounters
           COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure
           COMMAND ${LCOV} --directory . --capture --output-file coverage.info
           COMMAND ${LCOV} --remove coverage.info '/usr/*' '*/tests/*' '*/third_party/*' --output-file coverage.info
           COMMAND ${GENHTML} coverage.info --output-directory ${CMAKE_BINARY_DIR}/coverage
           WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
           COMMENT "Generating code coverage report"
       )
   endif()
   ```

   **tests/CMakeLists.txt**:
   ```cmake
   include(GoogleTest)

   # Test utilities library
   add_library(test_utils STATIC
       helpers/TestUtils.cpp
       helpers/CustomMatchers.cpp
       fixtures/TestFixtures.cpp
   )
   target_include_directories(test_utils PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
   target_link_libraries(test_utils
       PUBLIC
           GTest::gtest
           GTest::gmock
   )

   # Function to add a test executable
   function(add_gtest TEST_NAME)
       add_executable(${TEST_NAME} ${ARGN})
       target_link_libraries(${TEST_NAME}
           PRIVATE
               myapp_lib
               test_utils
               GTest::gtest_main
               GTest::gmock
       )
       gtest_discover_tests(${TEST_NAME})
   endfunction()

   # Unit tests
   add_gtest(test_user unit/UserTest.cpp)
   add_gtest(test_order unit/OrderTest.cpp)
   add_gtest(test_database unit/DatabaseTest.cpp)

   # Integration tests
   add_gtest(test_integration integration/IntegrationTest.cpp)

   # E2E tests
   add_gtest(test_e2e e2e/E2ETest.cpp)
   ```

4. **Alternative: Catch2 Configuration**

   **CMakeLists.txt** (with Catch2):
   ```cmake
   # Fetch Catch2
   FetchContent_Declare(
       Catch2
       GIT_REPOSITORY https://github.com/catchorg/Catch2.git
       GIT_TAG v3.4.0
   )
   FetchContent_MakeAvailable(Catch2)

   # Add test
   add_executable(tests
       unit/UserTest.cpp
       unit/OrderTest.cpp
   )
   target_link_libraries(tests PRIVATE Catch2::Catch2WithMain myapp_lib)

   include(CTest)
   include(Catch)
   catch_discover_tests(tests)
   ```

## Phase 2: Directory Structure Design

1. **Standard C++ Test Layout**

   Implement this recommended structure:
   ```
   myproject/
   ├── include/
   │   ├── myapp/
   │   │   ├── User.hpp
   │   │   ├── Order.hpp
   │   │   └── Database.hpp
   │
   ├── src/
   │   ├── User.cpp
   │   ├── Order.cpp
   │   └── Database.cpp
   │
   ├── tests/
   │   ├── unit/
   │   │   ├── UserTest.cpp
   │   │   ├── OrderTest.cpp
   │   │   └── DatabaseTest.cpp
   │   │
   │   ├── integration/
   │   │   ├── IntegrationTest.cpp
   │   │   └── ApiIntegrationTest.cpp
   │   │
   │   ├── e2e/
   │   │   ├── E2ETest.cpp
   │   │   └── WorkflowTest.cpp
   │   │
   │   ├── fixtures/
   │   │   ├── TestFixtures.hpp
   │   │   ├── TestFixtures.cpp
   │   │   ├── DatabaseFixture.hpp
   │   │   └── DatabaseFixture.cpp
   │   │
   │   ├── helpers/
   │   │   ├── TestUtils.hpp
   │   │   ├── TestUtils.cpp
   │   │   ├── CustomMatchers.hpp
   │   │   ├── CustomMatchers.cpp
   │   │   ├── Builders.hpp
   │   │   └── Builders.cpp
   │   │
   │   ├── mocks/
   │   │   ├── MockDatabase.hpp
   │   │   ├── MockLogger.hpp
   │   │   └── MockRepository.hpp
   │   │
   │   ├── data/
   │   │   ├── test_data.json
   │   │   ├── sample_users.csv
   │   │   └── config.yaml
   │   │
   │   └── CMakeLists.txt
   │
   ├── third_party/
   │   └── googletest/
   │
   ├── CMakeLists.txt
   └── README.md
   ```

2. **IDE Integration: VS Code Configuration**

   For seamless test development, building, and debugging in VS Code, set up workspace configuration:

   **Quick Setup**:
   ```bash
   # Copy VS Code configurations from AI Templates
   mkdir -p .vscode
   cp templates/test_development/vscode_config/*.json .vscode/
   ```

   **What This Provides**:

   - **One-Click Build**: `Ctrl+Shift+B` to build tests

   - **One-Click Test Run**: Command Palette → "Tasks: Run Test Task"

   - **Seamless Debugging**: Set breakpoints, press `F5` to debug tests

   - **IntelliSense**: Auto-completion for Google Test macros

   - **Test Explorer**: Visual test runner with play/debug buttons

   **Required VS Code Extensions**:

   - CMake Tools (`twxs.cmake`)

   - C/C++ Extension Pack (`ms-vscode.cpptools-extension-pack`)

   - Test Explorer UI (`hbenl.vscode-test-explorer`)

   - GitHub Copilot (`GitHub.copilot`) - For AI-assisted test generation

   **Configuration Files**:

   - `.vscode/tasks.json` - Build and test tasks

   - `.vscode/launch.json` - Debugging configurations

   - `.vscode/settings.json` - CMake Tools and IntelliSense settings

   - `.vscode/c_cpp_properties.json` - Platform-specific includes

   See **[VS Code Configuration Guide](../vscode_config/README.md)** for detailed setup instructions.

   **GitHub Copilot Integration**:

   Once VS Code is configured, use GitHub Copilot to generate tests:

   1. Open Copilot Chat (`Ctrl+Shift+I`)

   2. Paste prompt template from [cpp_unit_tests.md](../unit_tests/cpp_unit_tests.md)

   3. Copilot generates comprehensive Google Test suite

   4. Build and run with keyboard shortcuts

   See **[Complete Workflow Guide](../GOOGLE_TEST_VSCODE_WORKFLOW.md)** for step-by-step instructions (10 minutes from clone to test run).

   **Alternative IDEs**:

   - **CLion**: Native CMake integration, built-in Google Test runner

   - **Visual Studio**: Test Explorer with Google Test adapter

   - **Qt Creator**: CMake support, test integration plugin

3. **Naming Conventions**

   **File Naming**:

   - Test file: `<ClassName>Test.cpp`

   - Test case: `TEST(TestSuiteName, TestCaseName)`

   - Fixture class: `<Name>Fixture` or `<Name>Test`

   - Mock class: `Mock<ClassName>`

   **GoogleTest Example**:
   ```cpp
   // tests/unit/UserTest.cpp
   #include <gtest/gtest.h>
   #include <gmock/gmock.h>
   #include "myapp/User.hpp"
   #include "mocks/MockDatabase.hpp"
   #include "helpers/Builders.hpp"

   using ::testing::Return;
   using ::testing::_;
   using namespace myapp;

   // Simple test (no fixture)
   TEST(UserTest, CreateUser_WithValidData_ReturnsSuccess) {
       // Arrange
       User user("John", "john@test.com");

       // Act
       bool result = user.isValid();

       // Assert
       EXPECT_TRUE(result);
       EXPECT_EQ("John", user.getName());
       EXPECT_EQ("john@test.com", user.getEmail());
   }

   TEST(UserTest, CreateUser_WithEmptyName_ThrowsException) {
       // Act & Assert
       EXPECT_THROW({
           User user("", "john@test.com");
       }, std::invalid_argument);
   }

   // Test fixture for shared setup
   class UserTest : public ::testing::Test {
   protected:
       void SetUp() override {
           // Runs before each test
           mockDb = std::make_unique<MockDatabase>();
           user = std::make_unique<User>("John", "john@test.com");
       }

       void TearDown() override {
           // Runs after each test
           user.reset();
           mockDb.reset();
       }

       std::unique_ptr<MockDatabase> mockDb;
       std::unique_ptr<User> user;
   };

   TEST_F(UserTest, Save_ValidUser_CallsDatabase) {
       // Arrange
       EXPECT_CALL(*mockDb, save(_))
           .Times(1)
           .WillOnce(Return(true));

       // Act
       bool result = user->save(*mockDb);

       // Assert
       EXPECT_TRUE(result);
   }

   // Parameterized test
   class EmailValidationTest : public ::testing::TestWithParam<std::pair<std::string, bool>> {
   };

   TEST_P(EmailValidationTest, ValidateEmail) {
       auto [email, expected] = GetParam();
       EXPECT_EQ(expected, User::isValidEmail(email));
   }

   INSTANTIATE_TEST_SUITE_P(
       EmailTests,
       EmailValidationTest,
       ::testing::Values(
           std::make_pair("test@example.com", true),
           std::make_pair("invalid", false),
           std::make_pair("", false),
           std::make_pair("@example.com", false)
       )
   );
   ```

   **Catch2 Example**:
   ```cpp
   // tests/unit/UserTest.cpp
   #include <catch2/catch_test_macros.hpp>
   #include "myapp/User.hpp"

   using namespace myapp;

   TEST_CASE("User creation", "[user]") {
       SECTION("Valid user data") {
           User user("John", "john@test.com");

           REQUIRE(user.isValid());
           REQUIRE(user.getName() == "John");
           REQUIRE(user.getEmail() == "john@test.com");
       }

       SECTION("Empty name throws exception") {
           REQUIRE_THROWS_AS(
               User("", "john@test.com"),
               std::invalid_argument
           );
       }
   }

   TEST_CASE("Email validation", "[user][validation]") {
       REQUIRE(User::isValidEmail("test@example.com"));
       REQUIRE_FALSE(User::isValidEmail("invalid"));
       REQUIRE_FALSE(User::isValidEmail(""));
   }

   // Parameterized test
   TEMPLATE_TEST_CASE("Container operations", "[template]",
                      std::vector<int>, std::list<int>) {
       TestType container;
       container.push_back(1);
       container.push_back(2);

       REQUIRE(container.size() == 2);
   }
   ```

3. **Test Type Organization**

   **Unit Tests** (`tests/unit/`):

   - Test individual classes in isolation

   - Fast execution (<10ms per test)

   - Heavy use of mocks

   - No external dependencies

   **Integration Tests** (`tests/integration/`):

   - Test multiple components together

   - Real implementations

   - May use test databases

   - Moderate execution time

   **E2E Tests** (`tests/e2e/`):

   - Test complete workflows

   - Full system integration

   - Slowest execution

   - Minimal mocking

## Phase 3: Fixture Infrastructure

1. **Test Fixture Base Classes** (`tests/fixtures/TestFixtures.hpp`):

   ```cpp
   #ifndef TEST_FIXTURES_HPP
   #define TEST_FIXTURES_HPP

   #include <gtest/gtest.h>
   #include <memory>
   #include "myapp/Database.hpp"

   namespace myapp::test {

   // Base fixture for database tests
   class DatabaseFixture : public ::testing::Test {
   protected:
       void SetUp() override {
           db = std::make_unique<Database>(":memory:");
           db->connect();
           db->createSchema();
       }

       void TearDown() override {
           if (db && db->isConnected()) {
               db->disconnect();
           }
           db.reset();
       }

       void seedTestData() {
           // Insert test data
           db->execute("INSERT INTO users (name, email) VALUES ('Alice', 'alice@test.com')");
           db->execute("INSERT INTO users (name, email) VALUES ('Bob', 'bob@test.com')");
       }

       void clearTestData() {
           db->execute("DELETE FROM orders");
           db->execute("DELETE FROM users");
       }

       std::unique_ptr<Database> db;
   };

   // Fixture with environment setup
   class EnvironmentFixture : public ::testing::Test {
   protected:
       static void SetUpTestSuite() {
           // Runs once before all tests in suite
           std::cout << "Setting up test environment\n";
       }

       static void TearDownTestSuite() {
           // Runs once after all tests in suite
           std::cout << "Tearing down test environment\n";
       }

       void SetUp() override {
           // Runs before each test
       }

       void TearDown() override {
           // Runs after each test
       }
   };

   } // namespace myapp::test

   #endif // TEST_FIXTURES_HPP
   ```

2. **Google Mock Integration** (`tests/mocks/MockDatabase.hpp`):

   ```cpp
   #ifndef MOCK_DATABASE_HPP
   #define MOCK_DATABASE_HPP

   #include <gmock/gmock.h>
   #include "myapp/Database.hpp"

   namespace myapp::test {

   class MockDatabase : public Database {
   public:
       MOCK_METHOD(bool, connect, (), (override));
       MOCK_METHOD(bool, disconnect, (), (override));
       MOCK_METHOD(bool, isConnected, (), (const, override));
       MOCK_METHOD(std::optional<User>, findUserById, (int id), (override));
       MOCK_METHOD(bool, save, (const User& user), (override));
       MOCK_METHOD(bool, deleteUser, (int id), (override));
       MOCK_METHOD(std::vector<User>, findAll, (), (override));
   };

   // Mock for interface/abstract class
   class MockLogger {
   public:
       MOCK_METHOD(void, log, (const std::string& message), ());
       MOCK_METHOD(void, error, (const std::string& message), ());
       MOCK_METHOD(void, warn, (const std::string& message), ());
       MOCK_METHOD(void, info, (const std::string& message), ());
   };

   } // namespace myapp::test

   #endif // MOCK_DATABASE_HPP
   ```

   **Using Mocks**:
   ```cpp
   TEST(UserServiceTest, CreateUser_Success_CallsDatabase) {
       // Arrange
       MockDatabase mockDb;
       UserService service(mockDb);
       User user("John", "john@test.com");

       EXPECT_CALL(mockDb, save(::testing::_))
           .Times(1)
           .WillOnce(::testing::Return(true));

       // Act
       bool result = service.createUser(user);

       // Assert
       EXPECT_TRUE(result);
   }

   TEST(UserServiceTest, FindUser_CallsDatabaseAndReturnsUser) {
       MockDatabase mockDb;
       UserService service(mockDb);

       User expectedUser("John", "john@test.com");
       EXPECT_CALL(mockDb, findUserById(1))
           .WillOnce(::testing::Return(expectedUser));

       auto result = service.findUser(1);

       ASSERT_TRUE(result.has_value());
       EXPECT_EQ("John", result->getName());
   }
   ```

3. **Parameterized Test Fixtures**:

   ```cpp
   class UserValidationTest : public ::testing::TestWithParam<
       std::tuple<std::string, std::string, bool>> {
   protected:
       void SetUp() override {
           auto [name, email, shouldBeValid] = GetParam();
           expectedValid = shouldBeValid;
       }

       bool expectedValid;
   };

   TEST_P(UserValidationTest, ValidateUserData) {
       auto [name, email, shouldBeValid] = GetParam();

       if (shouldBeValid) {
           EXPECT_NO_THROW({
               User user(name, email);
               EXPECT_TRUE(user.isValid());
           });
       } else {
           EXPECT_THROW({
               User user(name, email);
           }, std::invalid_argument);
       }
   }

   INSTANTIATE_TEST_SUITE_P(
       ValidationTests,
       UserValidationTest,
       ::testing::Values(
           std::make_tuple("John", "john@test.com", true),
           std::make_tuple("", "john@test.com", false),
           std::make_tuple("John", "", false),
           std::make_tuple("John", "invalid", false)
       )
   );
   ```

## Phase 4: Test Utilities & Helpers

1. **Custom Matchers** (`tests/helpers/CustomMatchers.hpp`):

   ```cpp
   #ifndef CUSTOM_MATCHERS_HPP
   #define CUSTOM_MATCHERS_HPP

   #include <gmock/gmock.h>
   #include <string>
   #include <chrono>

   namespace myapp::test {

   // Matcher for string contains
   MATCHER_P(ContainsSubstring, substring, "") {
       return arg.find(substring) != std::string::npos;
   }

   // Matcher for email validation
   MATCHER(IsValidEmail, "") {
       const std::string& email = arg;
       return email.find('@') != std::string::npos &&
              email.find('.') != std::string::npos;
   }

   // Matcher for time range
   MATCHER_P2(IsTimeBetween, start, end, "") {
       return arg >= start && arg <= end;
   }

   // Matcher for container size
   MATCHER_P(HasSize, size, "") {
       return arg.size() == static_cast<size_t>(size);
   }

   // Matcher for pointer not null
   MATCHER(IsNotNull, "") {
       return arg != nullptr;
   }

   // Custom matcher example
   class IsRecentTimeMatcher {
   public:
       using is_gtest_matcher = void;

       explicit IsRecentTimeMatcher(std::chrono::seconds maxAge)
           : maxAge_(maxAge) {}

       bool MatchAndExplain(const std::chrono::system_clock::time_point& time,
                          ::testing::MatchResultListener* listener) const {
           auto now = std::chrono::system_clock::now();
           auto age = now - time;

           if (age > maxAge_) {
               *listener << "time is too old (age: "
                        << std::chrono::duration_cast<std::chrono::seconds>(age).count()
                        << "s)";
               return false;
           }
           return true;
       }

       void DescribeTo(std::ostream* os) const {
           *os << "is within the last "
               << maxAge_.count() << " seconds";
       }

       void DescribeNegationTo(std::ostream* os) const {
           *os << "is not within the last "
               << maxAge_.count() << " seconds";
       }

   private:
       std::chrono::seconds maxAge_;
   };

   inline ::testing::PolymorphicMatcher<IsRecentTimeMatcher>
   IsRecent(std::chrono::seconds maxAge = std::chrono::seconds(60)) {
       return ::testing::MakePolymorphicMatcher(IsRecentTimeMatcher(maxAge));
   }

   } // namespace myapp::test

   #endif // CUSTOM_MATCHERS_HPP
   ```

2. **Test Data Builders** (`tests/helpers/Builders.hpp`):

   ```cpp
   #ifndef BUILDERS_HPP
   #define BUILDERS_HPP

   #include "myapp/User.hpp"
   #include "myapp/Order.hpp"
   #include <memory>
   #include <string>

   namespace myapp::test {

   class UserBuilder {
   public:
       UserBuilder()
           : id_(1)
           , name_("Test User")
           , email_("test@example.com")
           , isActive_(true)
           , createdAt_(std::chrono::system_clock::now()) {}

       UserBuilder& withId(int id) {
           id_ = id;
           return *this;
       }

       UserBuilder& withName(const std::string& name) {
           name_ = name;
           return *this;
       }

       UserBuilder& withEmail(const std::string& email) {
           email_ = email;
           return *this;
       }

       UserBuilder& inactive() {
           isActive_ = false;
           return *this;
       }

       UserBuilder& createdAt(std::chrono::system_clock::time_point time) {
           createdAt_ = time;
           return *this;
       }

       User build() const {
           User user(name_, email_);
           user.setId(id_);
           user.setActive(isActive_);
           user.setCreatedAt(createdAt_);
           return user;
       }

       std::unique_ptr<User> buildPtr() const {
           return std::make_unique<User>(build());
       }

   private:
       int id_;
       std::string name_;
       std::string email_;
       bool isActive_;
       std::chrono::system_clock::time_point createdAt_;
   };

   class OrderBuilder {
   public:
       OrderBuilder()
           : id_(1)
           , userId_(1)
           , amount_(100.0)
           , status_(OrderStatus::Pending) {}

       OrderBuilder& withId(int id) {
           id_ = id;
           return *this;
       }

       OrderBuilder& withUserId(int userId) {
           userId_ = userId;
           return *this;
       }

       OrderBuilder& withAmount(double amount) {
           amount_ = amount;
           return *this;
       }

       OrderBuilder& completed() {
           status_ = OrderStatus::Completed;
           return *this;
       }

       Order build() const {
           return Order(id_, userId_, amount_, status_);
       }

   private:
       int id_;
       int userId_;
       double amount_;
       OrderStatus status_;
   };

   } // namespace myapp::test

   #endif // BUILDERS_HPP
   ```

3. **Test Utilities** (`tests/helpers/TestUtils.hpp`):

   ```cpp
   #ifndef TEST_UTILS_HPP
   #define TEST_UTILS_HPP

   #include <string>
   #include <vector>
   #include <filesystem>
   #include <fstream>

   namespace myapp::test {

   class TestUtils {
   public:
       // File operations
       static std::string readFile(const std::filesystem::path& path) {
           std::ifstream file(path);
           return std::string(
               std::istreambuf_iterator<char>(file),
               std::istreambuf_iterator<char>()
           );
       }

       static void writeFile(const std::filesystem::path& path,
                            const std::string& content) {
           std::ofstream file(path);
           file << content;
       }

       static void deleteFile(const std::filesystem::path& path) {
           std::filesystem::remove(path);
       }

       // Random data generation
       static int randomInt(int min, int max) {
           static std::random_device rd;
           static std::mt19937 gen(rd());
           std::uniform_int_distribution<> dis(min, max);
           return dis(gen);
       }

       static std::string randomString(size_t length) {
           static const char chars[] =
               "abcdefghijklmnopqrstuvwxyz"
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789";
           std::string result;
           result.reserve(length);
           for (size_t i = 0; i < length; ++i) {
               result += chars[randomInt(0, sizeof(chars) - 2)];
           }
           return result;
       }

       // Container helpers
       template<typename T>
       static std::vector<T> createVector(std::initializer_list<T> items) {
           return std::vector<T>(items);
       }

       // Timing helpers
       template<typename Func>
       static auto measureTime(Func&& func) {
           auto start = std::chrono::high_resolution_clock::now();
           func();
           auto end = std::chrono::high_resolution_clock::now();
           return std::chrono::duration_cast<std::chrono::milliseconds>(
               end - start
           );
       }
   };

   } // namespace myapp::test

   #endif // TEST_UTILS_HPP
   ```

## Phase 5: Test Discovery & Execution

1. **Run Tests with CMake/CTest**

   ```bash
   # Configure
   mkdir build && cd build
   cmake -DCMAKE_BUILD_TYPE=Debug ..

   # Build
   cmake --build .

   # Run all tests
   ctest

   # Run with verbose output
   ctest --verbose

   # Run specific test
   ctest -R UserTest

   # Run tests matching pattern
   ctest -R "User.*"

   # Generate coverage
   cmake --build . --target coverage

   # View coverage report
   open coverage/index.html  # macOS
   xdg-open coverage/index.html  # Linux
   ```

2. **Run Tests with GoogleTest Directly**

   ```bash
   # Run all tests
   ./build/test_user

   # Run specific test
   ./build/test_user --gtest_filter=UserTest.CreateUser*

   # Run with detailed output
   ./build/test_user --gtest_verbose

   # List all tests
   ./build/test_user --gtest_list_tests

   # Run tests in random order
   ./build/test_user --gtest_shuffle

   # Repeat tests
   ./build/test_user --gtest_repeat=10
   ```

3. **Test Runner Script** (`run_tests.sh`):

   ```bash
   #!/bin/bash
   set -e

   BUILD_DIR="build"

   echo "========================================="
   echo "C++ Test Suite Runner"
   echo "========================================="

   # Create and configure
   mkdir -p $BUILD_DIR
   cd $BUILD_DIR
   cmake -DCMAKE_BUILD_TYPE=Debug ..

   # Build
   echo "Building..."
   cmake --build . -j$(nproc)

   # Run tests
   echo ""
   echo "Running tests..."
   ctest --output-on-failure --verbose

   # Generate coverage
   echo ""
   echo "Generating coverage..."
   cmake --build . --target coverage

   echo ""
   echo "========================================="
   echo "Tests complete!"
   echo "Coverage report: $BUILD_DIR/coverage/index.html"
   echo "========================================="
   ```

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

Replace `{phase_name}` with the specific phase (test_structure, test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

## Output Format

Please provide a comprehensive test infrastructure design with the following structure:

### Infrastructure Summary

- **Test Framework**: [GoogleTest/Catch2/Boost.Test with justification]

- **Build System**: [CMake version]

- **C++ Standard**: [C++11/14/17/20/23]

- **Total Test Files**: [count]

- **Test Organization**: [structure description]

- **Mock Strategy**: [GoogleMock/other]

- **Utility Modules**: [list of helper modules]

### Project Structure
```
[Complete directory tree with all test folders and key files]
```

### Build Configuration

- **CMakeLists.txt**: [Key settings configured]

- **Test discovery**: [Approach used]

- **Compiler flags**: [Debug/Release settings]

### Test Infrastructure
**Fixtures**:

- [FixtureName]: [purpose and usage]

**Mocks**:

- [MockName]: [purpose and usage]

**Builders**:

- [BuilderName]: [purpose and usage]

### Test Utilities
**Custom Matchers** (`tests/helpers/CustomMatchers.hpp`):

- [MatcherName]: [purpose]

**Test Builders** (`tests/helpers/Builders.hpp`):

- [BuilderName]: [purpose]

**Utilities** (`tests/helpers/TestUtils.hpp`):

- [UtilName]: [purpose]

### Test Execution Commands
```bash
# Build and run all tests
mkdir build && cd build
cmake .. && cmake --build . && ctest

# Run specific test
./build/test_user

# Run with filter
./build/test_user --gtest_filter=UserTest.*

# Generate coverage
cmake --build . --target coverage

# Clean
rm -rf build
```

### Testing Conventions Established
1. **File Naming**: [convention]

2. **Test Naming**: [convention]

3. **Fixture Usage**: [patterns]

4. **Mock Usage**: [when and how]

5. **Test Data**: [organization]

### Next Steps

- [ ] Implement actual test cases

- [ ] Add project-specific fixtures

- [ ] Configure CI/CD (GitHub Actions, GitLab CI)

- [ ] Set up coverage reporting (codecov)

- [ ] Document testing guidelines

- [ ] Add benchmark tests

- [ ] Set up sanitizers (ASan, UBSan, TSan)

### Best Practices Implemented

- Modern C++ features (smart pointers, RAII)

- Clear separation of test types

- Reusable test fixtures and builders

- GoogleMock for comprehensive mocking

- Custom matchers for readable assertions

- Coverage measurement integrated

- Parameterized tests for multiple scenarios

### Maintenance Recommendations

- Run tests before committing

- Keep tests isolated and fast

- Use smart pointers for automatic cleanup

- Update mocks when interfaces change

- Review coverage regularly

- Run with sanitizers in CI

- Benchmark performance-critical code
~~~

## Output Format

The AI assistant should deliver:

1. **Test infrastructure design document** with complete directory structure

2. **CMake configuration files** with GoogleTest integration

3. **Test fixture classes** with proper RAII

4. **Mock implementations** using GoogleMock

5. **Test utility libraries** with custom matchers

6. **Test builder classes** for data generation

7. **Test runner scripts** for automation

8. **Documentation** of conventions and best practices

9. **Execution commands** for common scenarios
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
