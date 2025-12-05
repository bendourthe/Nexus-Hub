---
template_id: c_test_structure
template_name: Test Structure Setup - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: test_development
phase: test_structure
phase_number: 1
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
related_templates:

  - test_development/unit_tests/c_unit_tests.md
tools:

  - unity
  - cmocka
  - check
tags:

  - test-development
  - testing
  - c
---
# C Test Structure & Infrastructure

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
Design and implement a robust test infrastructure with optimal framework configuration, logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices using Unity, CUnit, or Check frameworks.

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

- [ ] Test framework selected (Unity/CUnit/Check)

- [ ] Build system configured (CMake/Make)

- [ ] Framework libraries compiled

- [ ] Test runner scripts created

- [ ] Coverage tools configured (gcov/lcov)

### Directory Structure

- [ ] Standard test layout implemented

- [ ] Test type separation organized

- [ ] Naming conventions documented

- [ ] Test data directories created

- [ ] Header organization established

### Fixture Infrastructure

- [ ] Setup/teardown functions established

- [ ] Test fixtures defined

- [ ] Mock functions implemented

- [ ] Fixture documentation added

- [ ] Common fixtures centralized

### Test Utilities

- [ ] Custom assertion macros created

- [ ] Test data generators implemented

- [ ] Helper functions defined

- [ ] Mock utilities established

- [ ] Helper documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Test Infrastructure Setup

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

Please design and implement a comprehensive test infrastructure for this C project following this protocol:

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
     - **Unity** (recommended): Lightweight, portable, embedded-friendly
     - **CUnit**: Full-featured, good documentation, heavier
     - **Check**: Fork-safe, supports fixtures, more complex
     - **MinUnit**: Minimal, single-header, very simple
   - **Rationale**: Justify framework choice based on project needs

2. **Install Test Framework**

   **Unity Framework** (recommended):
   ```bash
   # Clone Unity
   git clone <REPO_URL> third_party/unity

   # Or add as submodule
   git submodule add <REPO_URL> third_party/unity
   git submodule update --init --recursive
   ```

   **CUnit**:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install libcunit1 libcunit1-dev

   # On macOS
   brew install cunit

   # From source
   wget https://sourceforge.net/projects/cunit/files/latest/download
   tar xzf CUnit-2.1-3.tar.gz
   cd CUnit-2.1-3
   ./configure
   make
   sudo make install
   ```

   **Check Framework**:
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install check

   # On macOS
   brew install check

   # From source
   git clone <REPO_URL>
   cd check
   mkdir build && cd build
   cmake ..
   make
   sudo make install
   ```

3. **CMake Build Configuration**

   **CMakeLists.txt** (root):
   ```cmake
   cmake_minimum_required(VERSION 3.15)
   project(MyApp C)

   set(CMAKE_C_STANDARD 11)
   set(CMAKE_C_STANDARD_REQUIRED ON)

   # Compiler flags
   set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Werror")
   set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} -g -O0 -coverage")
   set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3")

   # Enable testing
   enable_testing()

   # Source directories
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
           COMMAND ${LCOV} --remove coverage.info '/usr/*' '*/tests/*' --output-file coverage.info
           COMMAND ${GENHTML} coverage.info --output-directory ${CMAKE_BINARY_DIR}/coverage
           WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
           COMMENT "Generating code coverage report"
       )
   endif()
   ```

   **tests/CMakeLists.txt**:
   ```cmake
   # Unity framework
   add_library(unity STATIC
       ${CMAKE_SOURCE_DIR}/third_party/unity/src/unity.c
   )
   target_include_directories(unity PUBLIC
       ${CMAKE_SOURCE_DIR}/third_party/unity/src
   )

   # Test utilities library
   add_library(test_utils STATIC
       helpers/test_utils.c
       helpers/mock_helpers.c
       fixtures/test_fixtures.c
   )
   target_include_directories(test_utils PUBLIC
       ${CMAKE_SOURCE_DIR}/tests
   )
   target_link_libraries(test_utils unity)

   # Macro to add test executable
   function(add_unit_test TEST_NAME)
       add_executable(${TEST_NAME} unit/${TEST_NAME}.c)
       target_link_libraries(${TEST_NAME}
           myapp_lib
           test_utils
           unity
       )
       add_test(NAME ${TEST_NAME} COMMAND ${TEST_NAME})
   endfunction()

   # Add unit tests
   add_unit_test(test_user)
   add_unit_test(test_order)
   add_unit_test(test_database)

   # Integration tests
   add_executable(test_integration integration/test_integration.c)
   target_link_libraries(test_integration myapp_lib test_utils unity)
   add_test(NAME test_integration COMMAND test_integration)
   ```

4. **Makefile Configuration** (alternative to CMake):

   ```makefile
   CC = gcc
   CFLAGS = -Wall -Wextra -Werror -std=c11 -Iinclude -Isrc
   CFLAGS_DEBUG = $(CFLAGS) -g -O0 -coverage
   CFLAGS_TEST = $(CFLAGS_DEBUG) -Ithird_party/unity/src -Itests

   # Source files
   SOURCES = $(wildcard src/*.c)
   OBJECTS = $(SOURCES:.c=.o)

   # Test files
   TEST_SOURCES = $(wildcard tests/unit/*.c)
   TEST_RUNNERS = $(TEST_SOURCES:.c=_runner)

   # Unity framework
   UNITY_SRC = third_party/unity/src/unity.c
   UNITY_OBJ = third_party/unity/src/unity.o

   .PHONY: all test clean coverage

   all: myapp

   myapp: $(OBJECTS)
   	$(CC) $(CFLAGS) -o $@ $^

   # Build Unity
   $(UNITY_OBJ): $(UNITY_SRC)
   	$(CC) $(CFLAGS_TEST) -c -o $@ $<

   # Build test runners
   %_runner: %.c $(OBJECTS) $(UNITY_OBJ) tests/helpers/*.c tests/fixtures/*.c
   	$(CC) $(CFLAGS_TEST) -o $@ $^ -lm

   # Run all tests
   test: $(TEST_RUNNERS)
   	@echo "Running unit tests..."
   	@for test in $(TEST_RUNNERS); do \
   		echo "Running $$test..."; \
   		./$$test || exit 1; \
   	done

   # Coverage report
   coverage: test
   	lcov --directory . --capture --output-file coverage.info
   	lcov --remove coverage.info '/usr/*' 'tests/*' --output-file coverage.info
   	genhtml coverage.info --output-directory coverage_report
   	@echo "Coverage report generated in coverage_report/index.html"

   clean:
   	rm -f $(OBJECTS) $(UNITY_OBJ) $(TEST_RUNNERS)
   	rm -f *.gcda *.gcno *.gcov coverage.info
   	rm -rf coverage_report
   ```

## Phase 2: Directory Structure Design

1. **Standard C Test Layout**

   Implement this recommended structure:
   ```
   myproject/
   ├── include/
   │   ├── user.h
   │   ├── order.h
   │   └── database.h
   │
   ├── src/
   │   ├── user.c
   │   ├── order.c
   │   └── database.c
   │
   ├── tests/
   │   ├── unit/
   │   │   ├── test_user.c
   │   │   ├── test_order.c
   │   │   └── test_database.c
   │   │
   │   ├── integration/
   │   │   ├── test_integration.c
   │   │   └── test_system.c
   │   │
   │   ├── fixtures/
   │   │   ├── test_fixtures.h
   │   │   ├── test_fixtures.c
   │   │   ├── database_fixtures.h
   │   │   └── database_fixtures.c
   │   │
   │   ├── helpers/
   │   │   ├── test_utils.h
   │   │   ├── test_utils.c
   │   │   ├── mock_helpers.h
   │   │   ├── mock_helpers.c
   │   │   ├── assertions.h
   │   │   └── assertions.c
   │   │
   │   ├── mocks/
   │   │   ├── mock_database.h
   │   │   ├── mock_database.c
   │   │   ├── mock_logger.h
   │   │   └── mock_logger.c
   │   │
   │   ├── data/
   │   │   ├── test_data.json
   │   │   ├── sample_users.csv
   │   │   └── config.txt
   │   │
   │   └── CMakeLists.txt
   │
   ├── third_party/
   │   └── unity/
   │       └── src/
   │           ├── unity.h
   │           └── unity.c
   │
   ├── CMakeLists.txt
   ├── Makefile
   └── README.md
   ```

2. **Naming Conventions**

   **File Naming**:
   - Test file: `test_<module>.c`
   - Test function: `test_<function>_<scenario>`
   - Fixture file: `<module>_fixtures.c`
   - Mock file: `mock_<module>.c`

   **Unity Test Example**:
   ```c
   // tests/unit/test_user.c
   #include "unity.h"
   #include "user.h"
   #include "test_utils.h"

   void setUp(void) {
       // Runs before each test
   }

   void tearDown(void) {
       // Runs after each test
   }

   void test_create_user_with_valid_data_returns_success(void) {
       // Arrange
       User user = {0};
       user.id = 1;
       strcpy(user.name, "John Doe");
       strcpy(user.email, "john@test.com");

       // Act
       int result = create_user(&user);

       // Assert
       TEST_ASSERT_EQUAL(0, result);
       TEST_ASSERT_NOT_NULL(user.name);
       TEST_ASSERT_EQUAL_STRING("John Doe", user.name);
   }

   void test_create_user_with_null_pointer_returns_error(void) {
       // Act
       int result = create_user(NULL);

       // Assert
       TEST_ASSERT_EQUAL(-1, result);
   }

   void test_validate_email_with_valid_email_returns_true(void) {
       // Arrange
       const char* email = "test@example.com";

       // Act
       bool result = validate_email(email);

       // Assert
       TEST_ASSERT_TRUE(result);
   }

   int main(void) {
       UNITY_BEGIN();

       RUN_TEST(test_create_user_with_valid_data_returns_success);
       RUN_TEST(test_create_user_with_null_pointer_returns_error);
       RUN_TEST(test_validate_email_with_valid_email_returns_true);

       return UNITY_END();
   }
   ```

   **CUnit Test Example**:
   ```c
   // tests/unit/test_user.c
   #include <CUnit/CUnit.h>
   #include <CUnit/Basic.h>
   #include "user.h"

   int init_suite(void) {
       // Suite initialization
       return 0;
   }

   int clean_suite(void) {
       // Suite cleanup
       return 0;
   }

   void test_create_user(void) {
       User user = {1, "John", "john@test.com"};
       int result = create_user(&user);

       CU_ASSERT_EQUAL(result, 0);
       CU_ASSERT_STRING_EQUAL(user.name, "John");
   }

   void test_validate_email(void) {
       CU_ASSERT_TRUE(validate_email("test@example.com"));
       CU_ASSERT_FALSE(validate_email("invalid"));
   }

   int main(void) {
       CU_pSuite suite = NULL;

       if (CU_initialize_registry() != CUE_SUCCESS) {
           return CU_get_error();
       }

       suite = CU_add_suite("User Suite", init_suite, clean_suite);
       if (suite == NULL) {
           CU_cleanup_registry();
           return CU_get_error();
       }

       if ((CU_add_test(suite, "test_create_user", test_create_user) == NULL) ||
           (CU_add_test(suite, "test_validate_email", test_validate_email) == NULL)) {
           CU_cleanup_registry();
           return CU_get_error();
       }

       CU_basic_set_mode(CU_BRM_VERBOSE);
       CU_basic_run_tests();
       int failures = CU_get_number_of_failures();
       CU_cleanup_registry();

       return failures;
   }
   ```

3. **Test Type Organization**

   **Unit Tests** (`tests/unit/`):
   - Test individual functions in isolation
   - Fast execution
   - Heavy use of mocks
   - No external dependencies

   **Integration Tests** (`tests/integration/`):
   - Test multiple modules together
   - Real implementations
   - May use test databases
   - Slower execution

## Phase 3: Fixture Infrastructure

1. **Test Fixtures Header** (`tests/fixtures/test_fixtures.h`):

   ```c
   #ifndef TEST_FIXTURES_H
   #define TEST_FIXTURES_H

   #include "user.h"
   #include "order.h"
   #include "database.h"

   // User fixtures
   User* create_test_user(int id, const char* name, const char* email);
   void free_test_user(User* user);
   User** create_test_user_array(int count);
   void free_test_user_array(User** users, int count);

   // Order fixtures
   Order* create_test_order(int id, int user_id, double amount);
   void free_test_order(Order* order);

   // Database fixtures
   Database* create_test_database(void);
   void destroy_test_database(Database* db);
   void seed_test_data(Database* db);
   void clear_test_data(Database* db);

   #endif // TEST_FIXTURES_H
   ```

2. **Test Fixtures Implementation** (`tests/fixtures/test_fixtures.c`):

   ```c
   #include "test_fixtures.h"
   #include <stdlib.h>
   #include <string.h>

   User* create_test_user(int id, const char* name, const char* email) {
       User* user = (User*)malloc(sizeof(User));
       if (!user) return NULL;

       user->id = id;
       strncpy(user->name, name, sizeof(user->name) - 1);
       user->name[sizeof(user->name) - 1] = '\0';
       strncpy(user->email, email, sizeof(user->email) - 1);
       user->email[sizeof(user->email) - 1] = '\0';
       user->created_at = time(NULL);
       user->is_active = true;

       return user;
   }

   void free_test_user(User* user) {
       if (user) {
           free(user);
       }
   }

   User** create_test_user_array(int count) {
       User** users = (User**)malloc(sizeof(User*) * count);
       if (!users) return NULL;

       for (int i = 0; i < count; i++) {
           char name[50], email[100];
           snprintf(name, sizeof(name), "User%d", i);
           snprintf(email, sizeof(email), "user%d@test.com", i);
           users[i] = create_test_user(i + 1, name, email);
       }

       return users;
   }

   void free_test_user_array(User** users, int count) {
       if (users) {
           for (int i = 0; i < count; i++) {
               free_test_user(users[i]);
           }
           free(users);
       }
   }

   Database* create_test_database(void) {
       Database* db = (Database*)malloc(sizeof(Database));
       if (!db) return NULL;

       // Initialize with test configuration
       db->connection = NULL;
       strcpy(db->connection_string, ":memory:");
       db->is_connected = false;

       // Connect and setup schema
       database_connect(db);
       database_create_schema(db);

       return db;
   }

   void destroy_test_database(Database* db) {
       if (db) {
           database_disconnect(db);
           free(db);
       }
   }

   void seed_test_data(Database* db) {
       if (!db) return;

       // Insert test users
       User* user1 = create_test_user(1, "Alice", "alice@test.com");
       User* user2 = create_test_user(2, "Bob", "bob@test.com");

       database_insert_user(db, user1);
       database_insert_user(db, user2);

       free_test_user(user1);
       free_test_user(user2);
   }

   void clear_test_data(Database* db) {
       if (!db) return;

       database_execute(db, "DELETE FROM orders");
       database_execute(db, "DELETE FROM users");
   }
   ```

3. **Setup/Teardown Pattern**:

   ```c
   // Global test state
   static Database* g_test_db = NULL;
   static User* g_test_user = NULL;

   void setUp(void) {
       // Runs before each test
       g_test_db = create_test_database();
       g_test_user = create_test_user(1, "Test User", "test@test.com");
   }

   void tearDown(void) {
       // Runs after each test
       destroy_test_database(g_test_db);
       free_test_user(g_test_user);
       g_test_db = NULL;
       g_test_user = NULL;
   }
   ```

4. **Mock Implementation** (`tests/mocks/mock_database.c`):

   ```c
   // tests/mocks/mock_database.h
   #ifndef MOCK_DATABASE_H
   #define MOCK_DATABASE_H

   #include "database.h"
   #include <stdbool.h>

   typedef struct {
       int connect_called;
       int disconnect_called;
       int query_called;
       int execute_called;
       int expected_return;
       void* expected_data;
       bool should_fail;
   } MockDatabase;

   MockDatabase* mock_database_create(void);
   void mock_database_destroy(MockDatabase* mock);
   void mock_database_reset(MockDatabase* mock);
   void mock_database_set_return(MockDatabase* mock, int return_value);
   void mock_database_set_should_fail(MockDatabase* mock, bool fail);

   // Override real functions (link test with mock instead of real implementation)
   int database_connect(Database* db);
   int database_disconnect(Database* db);
   int database_query(Database* db, const char* sql, void* result);

   #endif // MOCK_DATABASE_H

   // tests/mocks/mock_database.c
   #include "mock_database.h"
   #include <stdlib.h>
   #include <string.h>

   static MockDatabase* g_mock = NULL;

   MockDatabase* mock_database_create(void) {
       MockDatabase* mock = (MockDatabase*)calloc(1, sizeof(MockDatabase));
       g_mock = mock;
       return mock;
   }

   void mock_database_destroy(MockDatabase* mock) {
       if (mock) {
           free(mock->expected_data);
           free(mock);
       }
       g_mock = NULL;
   }

   void mock_database_reset(MockDatabase* mock) {
       if (mock) {
           memset(mock, 0, sizeof(MockDatabase));
       }
   }

   void mock_database_set_return(MockDatabase* mock, int return_value) {
       if (mock) {
           mock->expected_return = return_value;
       }
   }

   void mock_database_set_should_fail(MockDatabase* mock, bool fail) {
       if (mock) {
           mock->should_fail = fail;
       }
   }

   // Mock implementations
   int database_connect(Database* db) {
       if (g_mock) {
           g_mock->connect_called++;
           if (g_mock->should_fail) {
               return -1;
           }
           db->is_connected = true;
           return g_mock->expected_return;
       }
       return -1;
   }

   int database_disconnect(Database* db) {
       if (g_mock) {
           g_mock->disconnect_called++;
           db->is_connected = false;
           return 0;
       }
       return -1;
   }

   int database_query(Database* db, const char* sql, void* result) {
       if (g_mock) {
           g_mock->query_called++;
           if (g_mock->should_fail) {
               return -1;
           }
           if (g_mock->expected_data && result) {
               memcpy(result, g_mock->expected_data, sizeof(User)); // Example
           }
           return g_mock->expected_return;
       }
       return -1;
   }
   ```

## Phase 4: Test Utilities & Helpers

1. **Custom Assertions** (`tests/helpers/assertions.h`):

   ```c
   #ifndef ASSERTIONS_H
   #define ASSERTIONS_H

   #include "unity.h"
   #include <stdbool.h>
   #include <time.h>

   // String assertions
   void assert_string_contains(const char* haystack, const char* needle, int line);
   void assert_string_starts_with(const char* str, const char* prefix, int line);
   void assert_string_ends_with(const char* str, const char* suffix, int line);

   // Numeric assertions
   void assert_in_range(int value, int min, int max, int line);
   void assert_close_to(double actual, double expected, double tolerance, int line);

   // Time assertions
   void assert_time_recent(time_t timestamp, int max_seconds, int line);

   // Pointer assertions
   void assert_all_not_null(void** pointers, int count, int line);

   // Macros for convenience
   #define ASSERT_STRING_CONTAINS(haystack, needle) \
       assert_string_contains(haystack, needle, __LINE__)

   #define ASSERT_STRING_STARTS_WITH(str, prefix) \
       assert_string_starts_with(str, prefix, __LINE__)

   #define ASSERT_IN_RANGE(value, min, max) \
       assert_in_range(value, min, max, __LINE__)

   #define ASSERT_CLOSE_TO(actual, expected, tolerance) \
       assert_close_to(actual, expected, tolerance, __LINE__)

   #define ASSERT_TIME_RECENT(timestamp, max_seconds) \
       assert_time_recent(timestamp, max_seconds, __LINE__)

   #endif // ASSERTIONS_H
   ```

   **Implementation** (`tests/helpers/assertions.c`):
   ```c
   #include "assertions.h"
   #include <string.h>
   #include <stdio.h>
   #include <math.h>

   void assert_string_contains(const char* haystack, const char* needle, int line) {
       if (!haystack || !needle || !strstr(haystack, needle)) {
           char msg[256];
           snprintf(msg, sizeof(msg),
               "Expected '%s' to contain '%s'", haystack, needle);
           UNITY_TEST_FAIL(line, msg);
       }
   }

   void assert_string_starts_with(const char* str, const char* prefix, int line) {
       if (!str || !prefix || strncmp(str, prefix, strlen(prefix)) != 0) {
           char msg[256];
           snprintf(msg, sizeof(msg),
               "Expected '%s' to start with '%s'", str, prefix);
           UNITY_TEST_FAIL(line, msg);
       }
   }

   void assert_in_range(int value, int min, int max, int line) {
       if (value < min || value > max) {
           char msg[256];
           snprintf(msg, sizeof(msg),
               "Expected %d to be in range [%d, %d]", value, min, max);
           UNITY_TEST_FAIL(line, msg);
       }
   }

   void assert_close_to(double actual, double expected, double tolerance, int line) {
       if (fabs(actual - expected) > tolerance) {
           char msg[256];
           snprintf(msg, sizeof(msg),
               "Expected %.6f to be close to %.6f (tolerance: %.6f)",
               actual, expected, tolerance);
           UNITY_TEST_FAIL(line, msg);
       }
   }

   void assert_time_recent(time_t timestamp, int max_seconds, int line) {
       time_t now = time(NULL);
       int diff = (int)difftime(now, timestamp);
       if (diff < 0 || diff > max_seconds) {
           char msg[256];
           snprintf(msg, sizeof(msg),
               "Timestamp is not recent (age: %d seconds, max: %d)",
               diff, max_seconds);
           UNITY_TEST_FAIL(line, msg);
       }
   }
   ```

2. **Test Utilities** (`tests/helpers/test_utils.h`):

   ```c
   #ifndef TEST_UTILS_H
   #define TEST_UTILS_H

   #include <stdio.h>
   #include <stdbool.h>

   // File utilities
   char* read_test_file(const char* filename);
   bool write_test_file(const char* filename, const char* content);
   void delete_test_file(const char* filename);

   // String utilities
   char* string_duplicate(const char* str);
   bool strings_equal_ignore_case(const char* str1, const char* str2);

   // Array utilities
   int* create_int_array(int size, int start_value);
   void free_int_array(int* array);

   // Random data generation
   int random_int(int min, int max);
   char* random_string(int length);
   double random_double(double min, double max);

   // Memory tracking
   void reset_allocation_counter(void);
   int get_allocation_count(void);
   int get_free_count(void);

   #endif // TEST_UTILS_H
   ```

3. **Test Runner Script** (`run_tests.sh`):

   ```bash
   #!/bin/bash
   set -e

   BUILD_DIR="build"
   TEST_RESULTS="test_results.txt"

   echo "========================================="
   echo "Running Test Suite"
   echo "========================================="

   # Create build directory
   mkdir -p $BUILD_DIR
   cd $BUILD_DIR

   # Configure and build
   cmake -DCMAKE_BUILD_TYPE=Debug ..
   make

   # Run tests
   echo ""
   echo "Executing tests..."
   ctest --output-on-failure --verbose | tee ../$TEST_RESULTS

   # Generate coverage
   echo ""
   echo "Generating coverage report..."
   make coverage

   # Summary
   echo ""
   echo "========================================="
   echo "Test Summary"
   echo "========================================="
   ctest --output-on-failure | tail -n 5

   echo ""
   echo "Coverage report: $BUILD_DIR/coverage/index.html"
   ```

## Phase 5: Test Discovery & Execution

1. **Run Tests with CMake**

   ```bash
   # Configure
   mkdir build && cd build
   cmake -DCMAKE_BUILD_TYPE=Debug ..

   # Build
   make

   # Run all tests
   ctest

   # Run with verbose output
   ctest --verbose

   # Run specific test
   ctest -R test_user

   # Generate coverage
   make coverage

   # View coverage report
   open coverage/index.html  # macOS
   xdg-open coverage/index.html  # Linux
   ```

2. **Run Tests with Make**

   ```bash
   # Build and run tests
   make test

   # Run specific test
   ./tests/unit/test_user_runner

   # Generate coverage
   make coverage

   # Clean
   make clean
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

- **Test Framework**: [Unity/CUnit/Check with justification]

- **Build System**: [CMake/Make]

- **C Standard**: [C99/C11/C17]

- **Total Test Files**: [count]

- **Test Organization**: [structure description]

- **Mock Strategy**: [approach description]

- **Utility Modules**: [list of helper modules]

### Directory Structure
```
[Complete directory tree with all test folders and key files]
```

### Build Configuration

- **CMakeLists.txt**: [Key settings]

- **Makefile**: [Key targets]

- **Compiler flags**: [Debug/Release settings]

### Test Infrastructure
**Setup/Teardown**:

- [Approach]: [description]

**Fixtures**:

- [FixtureName]: [purpose and usage]

**Mocks**:

- [MockName]: [purpose and usage]

### Test Utilities
**Assertion Helpers** (`tests/helpers/assertions.h`):

- [HelperName]: [purpose]

**Test Utils** (`tests/helpers/test_utils.h`):

- [UtilName]: [purpose]

### Test Execution Commands
```bash
# Build and run all tests
mkdir build && cd build
cmake .. && make && ctest

# Or with Make
make test

# Run specific test
./build/tests/unit/test_user

# Generate coverage
make coverage

# Clean
make clean
```

### Testing Conventions Established
1. **File Naming**: [convention]
2. **Test Function Naming**: [convention]
3. **Assertion Usage**: [patterns]
4. **Mock Usage**: [when and how]
5. **Test Data**: [organization]

### Next Steps

- [ ] Implement actual test cases

- [ ] Add project-specific fixtures

- [ ] Configure CI/CD integration

- [ ] Set up coverage reporting

- [ ] Document testing guidelines

- [ ] Create more mock implementations

- [ ] Add memory leak detection (valgrind)

### Best Practices Implemented

- Clear separation of test types

- Reusable test fixtures

- Comprehensive mocking support

- Custom assertions for readability

- Coverage measurement integrated

- Memory management helpers

- Proper setup/teardown patterns

### Maintenance Recommendations

- Run tests before committing

- Monitor memory leaks with valgrind

- Keep tests isolated and fast

- Update mocks when interfaces change

- Review coverage regularly

- Document complex test scenarios
~~~

## Output Format

The AI assistant should deliver:

1. **Test infrastructure design document** with complete directory structure
2. **Build configuration files** (CMakeLists.txt or Makefile)
3. **Test fixture implementations** with setup/teardown
4. **Mock implementations** for external dependencies
5. **Test utility libraries** with custom assertions
6. **Test runner scripts** for automation
7. **Documentation** of conventions and best practices
8. **Execution commands** for common scenarios
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
