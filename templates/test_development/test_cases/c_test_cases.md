---
template_id: c_test_cases
template_name: Test Cases Development - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: test_development
phase: test_cases
phase_number: 3
difficulty: intermediate
estimated_time_hours: 4-8
prerequisites:

  - test_development/unit_tests/c_unit_tests.md
related_templates:

  - test_development/mocks_fixtures/c_mocks_fixtures.md
tools:

  - unity

  - cmocka

  - check
tags:

  - test-development

  - testing

  - c
---
# C Test Case Development

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
Develop comprehensive, well-structured test cases that validate functionality, cover edge cases, handle error conditions, and provide clear documentation of expected behavior using Unity, CUnit, or similar C testing frameworks.

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

- [ ] Memory leaks checked

### Test Quality

- [ ] Tests follow AAA pattern (Arrange-Act-Assert)

- [ ] Test names clearly describe what is tested

- [ ] Tests are isolated and independent

- [ ] Tests execute quickly (<1s for unit tests)

- [ ] Assertions are specific and meaningful

- [ ] No test interdependencies

- [ ] Proper cleanup in tearDown functions

### Test Organization

- [ ] Tests grouped logically by feature/module

- [ ] Related tests organized in test suites

- [ ] Setup and teardown properly implemented

- [ ] Test documentation provided

- [ ] Memory allocation/deallocation verified

- [ ] Valgrind or similar tool used for memory checks

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Test Case Development

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

Please develop comprehensive test cases for this C code following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Test Case Planning

1. **Analyze Code to Test**

   - Identify all public functions

   - Document expected behavior

   - List input parameters and types

   - Define expected outputs

   - Note side effects (memory allocation, file I/O, system calls)

   - Identify error conditions and return codes

2. **Identify Test Scenarios**

   **Happy Path**:

   - Normal operation with valid inputs

   - Expected use cases

   - Successful execution flows

   - Valid pointer operations

   **Edge Cases**:

   - Boundary values (0, -1, INT_MAX, INT_MIN)

   - Empty strings and NULL pointers

   - Buffer boundaries

   - Large data sets

   - Special characters in strings

   **Error Conditions**:

   - Invalid inputs

   - NULL pointer handling

   - Buffer overflow scenarios

   - Memory allocation failures

   - File operation errors

   - Invalid return codes

3. **Create Test Case Matrix**

   | Scenario | Input | Expected Output | Test Type | Priority |
   |----------|-------|-----------------|-----------|----------|
   | [description] | [values] | [result] | [unit/integration] | [high/med/low] |

## Phase 2: Unit Test Implementation (Unity Framework)

### AAA Pattern (Arrange-Act-Assert)

Follow this structure for clear, maintainable tests:

```c
#include "unity.h"
#include "user_service.h"
#include <string.h>
#include <stdlib.h>

/**

 * @file test_user_service.c

 * @brief Unit tests for user_service module.
 *

 * Tests cover user creation, validation, and retrieval operations.
 */

// Test fixture variables
static user_t *test_user;
static user_service_t *service;

/**

 * @brief Setup function called before each test.
 */
void setUp(void)
{
    service = user_service_create();
    test_user = NULL;
}

/**

 * @brief Teardown function called after each test.
 */
void tearDown(void)
{
    if (test_user != NULL) {
        user_destroy(test_user);
        test_user = NULL;
    }
    if (service != NULL) {
        user_service_destroy(service);
        service = NULL;
    }
}

/**

 * @brief Test creating user with valid data returns user ID.
 */
void test_create_user_with_valid_data_returns_user_id(void)
{
    // Arrange - Set up test data
    const char *name = "Alice";
    const char *email = "alice@example.com";
    int age = 30;
    int expected_id = 123;

    // Act - Execute the function being tested
    int actual_id = user_service_create_user(service, name, email, age);

    // Assert - Verify the result matches expectations
    TEST_ASSERT_EQUAL_INT(expected_id, actual_id);
    TEST_ASSERT_NOT_NULL(service);
}

/**

 * @brief Test creating user with invalid email returns error code.
 */
void test_create_user_with_invalid_email_returns_error(void)
{
    // Arrange
    const char *name = "Bob";
    const char *invalid_email = "not-an-email";
    int age = 25;

    // Act
    int result = user_service_create_user(service, name, invalid_email, age);

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_INVALID_EMAIL, result);
}

/**

 * @brief Test creating user with NULL name returns error code.
 */
void test_create_user_with_null_name_returns_error(void)
{
    // Arrange
    const char *name = NULL;
    const char *email = "test@example.com";
    int age = 20;

    // Act
    int result = user_service_create_user(service, name, email, age);

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_NULL_POINTER, result);
}

/**

 * @brief Test creating user with negative age returns error code.
 */
void test_create_user_with_negative_age_returns_error(void)
{
    // Arrange
    const char *name = "Charlie";
    const char *email = "charlie@example.com";
    int age = -5;

    // Act
    int result = user_service_create_user(service, name, email, age);

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_INVALID_AGE, result);
}

/**

 * @brief Main test runner.
 */
int main(void)
{
    UNITY_BEGIN();

    RUN_TEST(test_create_user_with_valid_data_returns_user_id);
    RUN_TEST(test_create_user_with_invalid_email_returns_error);
    RUN_TEST(test_create_user_with_null_name_returns_error);
    RUN_TEST(test_create_user_with_negative_age_returns_error);

    return UNITY_END();
}
```

### Test Naming Conventions

Use descriptive names that explain what is tested:

**Pattern**: `test_<function>_<condition>_<expected_result>`

**Examples**:
```c
// Good test names
void test_add_user_with_valid_data_returns_user_id(void);
void test_add_user_with_duplicate_email_returns_error(void);
void test_get_user_with_nonexistent_id_returns_null(void);
void test_update_user_with_invalid_age_returns_error(void);

// Poor test names (avoid these)
void test_add_user(void);              // Too generic
void test_1(void);                     // Non-descriptive
void test_error(void);                 // Unclear what error
void test_edge_case(void);             // Vague
```

### Testing Different Scenarios

**1. Testing Return Values**:
```c
void test_calculate_total_with_numbers_returns_sum(void)
{
    // Arrange
    double items[] = {10.0, 20.0, 30.0};
    int count = 3;

    // Act
    double result = calculate_total(items, count);

    // Assert
    TEST_ASSERT_EQUAL_DOUBLE(60.0, result);
}

void test_calculate_total_with_empty_array_returns_zero(void)
{
    // Arrange
    double items[] = {};
    int count = 0;

    // Act
    double result = calculate_total(items, count);

    // Assert
    TEST_ASSERT_EQUAL_DOUBLE(0.0, result);
}

void test_calculate_total_with_negative_values_returns_correct_sum(void)
{
    // Arrange
    double items[] = {10.0, -5.0, 15.0};
    int count = 3;

    // Act
    double result = calculate_total(items, count);

    // Assert
    TEST_ASSERT_EQUAL_DOUBLE(20.0, result);
}
```

**2. Testing Error Codes**:
```c
void test_divide_by_zero_returns_error_code(void)
{
    // Arrange
    int a = 10;
    int b = 0;
    int result;

    // Act
    int status = divide(a, b, &result);

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_DIVISION_BY_ZERO, status);
}

void test_parse_date_with_invalid_format_returns_error(void)
{
    // Arrange
    const char *invalid_date = "not-a-date";
    date_t result;

    // Act
    int status = parse_date(invalid_date, &result);

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_INVALID_FORMAT, status);
}

void test_open_file_with_invalid_path_returns_null(void)
{
    // Arrange
    const char *invalid_path = "/nonexistent/path/file.txt";

    // Act
    FILE *file = open_file(invalid_path, "r");

    // Assert
    TEST_ASSERT_NULL(file);
}
```

**3. Testing String Operations**:
```c
void test_string_copy_copies_correctly(void)
{
    // Arrange
    const char *source = "Hello, World!";
    char dest[50];

    // Act
    int result = safe_string_copy(dest, source, sizeof(dest));

    // Assert
    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_STRING(source, dest);
}

void test_string_copy_truncates_when_buffer_too_small(void)
{
    // Arrange
    const char *source = "This is a very long string";
    char dest[10];

    // Act
    int result = safe_string_copy(dest, source, sizeof(dest));

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_BUFFER_OVERFLOW, result);
    TEST_ASSERT_EQUAL_size_t(sizeof(dest) - 1, strlen(dest));
}

void test_string_concat_appends_correctly(void)
{
    // Arrange
    char dest[50] = "Hello";
    const char *source = " World";

    // Act
    int result = safe_string_concat(dest, source, sizeof(dest));

    // Assert
    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_STRING("Hello World", dest);
}
```

**4. Testing Memory Operations**:
```c
void test_buffer_create_allocates_memory(void)
{
    // Arrange
    size_t size = 1024;

    // Act
    buffer_t *buffer = buffer_create(size);

    // Assert
    TEST_ASSERT_NOT_NULL(buffer);
    TEST_ASSERT_NOT_NULL(buffer->data);
    TEST_ASSERT_EQUAL_size_t(size, buffer->size);

    // Cleanup
    buffer_destroy(buffer);
}

void test_buffer_create_with_zero_size_returns_null(void)
{
    // Arrange
    size_t size = 0;

    // Act
    buffer_t *buffer = buffer_create(size);

    // Assert
    TEST_ASSERT_NULL(buffer);
}

void test_array_resize_preserves_data(void)
{
    // Arrange
    int *array = malloc(5 * sizeof(int));
    for (int i = 0; i < 5; i++) {
        array[i] = i;
    }

    // Act
    int *resized = array_resize(array, 5, 10);

    // Assert
    TEST_ASSERT_NOT_NULL(resized);
    for (int i = 0; i < 5; i++) {
        TEST_ASSERT_EQUAL_INT(i, resized[i]);
    }

    // Cleanup
    free(resized);
}
```

**5. Testing State Changes**:
```c
void test_user_login_updates_status_to_active(void)
{
    // Arrange
    user_t *user = user_create("alice", "password");
    user->status = STATUS_INACTIVE;

    // Act
    int result = user_login(user, "password");

    // Assert
    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_INT(STATUS_ACTIVE, user->status);
    TEST_ASSERT_NOT_EQUAL(0, user->last_login);

    // Cleanup
    user_destroy(user);
}

void test_queue_enqueue_increases_size(void)
{
    // Arrange
    queue_t *queue = queue_create(10);
    int value = 42;

    // Act
    int result = queue_enqueue(queue, value);

    // Assert
    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_INT(1, queue_size(queue));

    // Cleanup
    queue_destroy(queue);
}
```

### Testing Edge Cases and Boundaries

```c
void test_process_value_with_minimum_valid_value(void)
{
    // Arrange
    int input = 0;

    // Act
    int result = process_value(input);

    // Assert
    TEST_ASSERT_EQUAL_INT(expected_min, result);
}

void test_process_value_with_maximum_valid_value(void)
{
    // Arrange
    int input = 100;

    // Act
    int result = process_value(input);

    // Assert
    TEST_ASSERT_EQUAL_INT(expected_max, result);
}

void test_process_value_below_minimum_returns_error(void)
{
    // Arrange
    int input = -1;
    int result;

    // Act
    int status = process_value_safe(input, &result);

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_OUT_OF_RANGE, status);
}

void test_process_value_above_maximum_returns_error(void)
{
    // Arrange
    int input = 101;
    int result;

    // Act
    int status = process_value_safe(input, &result);

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_OUT_OF_RANGE, status);
}

void test_buffer_operations_at_boundaries(void)
{
    // Arrange
    char buffer[10];

    // Test empty buffer
    TEST_ASSERT_EQUAL_INT(0, buffer_length(buffer, 0));

    // Test full buffer
    memset(buffer, 'A', sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';
    TEST_ASSERT_EQUAL_INT(9, buffer_length(buffer, sizeof(buffer)));
}

void test_null_pointer_handling(void)
{
    // Test NULL pointer returns error
    TEST_ASSERT_EQUAL_INT(ERROR_NULL_POINTER, process_string(NULL));

    // Test NULL with length returns error
    TEST_ASSERT_EQUAL_INT(ERROR_NULL_POINTER,
                          safe_string_copy(NULL, "test", 10));

    // Test copying to NULL returns error
    char buffer[10];
    TEST_ASSERT_EQUAL_INT(ERROR_NULL_POINTER,
                          safe_string_copy(buffer, NULL, sizeof(buffer)));
}
```

### Testing with CUnit Framework

```c
#include <CUnit/CUnit.h>
#include <CUnit/Basic.h>
#include "my_module.h"

// Test suite initialization
int init_suite(void)
{
    return 0;
}

// Test suite cleanup
int clean_suite(void)
{
    return 0;
}

// Test cases
void test_add_positive_numbers(void)
{
    CU_ASSERT_EQUAL(add(2, 3), 5);
    CU_ASSERT_EQUAL(add(10, 20), 30);
}

void test_add_negative_numbers(void)
{
    CU_ASSERT_EQUAL(add(-2, -3), -5);
    CU_ASSERT_EQUAL(add(-10, 5), -5);
}

void test_add_zero(void)
{
    CU_ASSERT_EQUAL(add(0, 0), 0);
    CU_ASSERT_EQUAL(add(5, 0), 5);
    CU_ASSERT_EQUAL(add(0, 5), 5);
}

int main(void)
{
    CU_pSuite suite = NULL;

    // Initialize CUnit registry
    if (CUE_SUCCESS != CU_initialize_registry()) {
        return CU_get_error();
    }

    // Add suite to registry
    suite = CU_add_suite("Math_Operations_Suite", init_suite, clean_suite);
    if (NULL == suite) {
        CU_cleanup_registry();
        return CU_get_error();
    }

    // Add tests to suite
    if ((NULL == CU_add_test(suite, "test_add_positive_numbers", test_add_positive_numbers)) ||
        (NULL == CU_add_test(suite, "test_add_negative_numbers", test_add_negative_numbers)) ||
        (NULL == CU_add_test(suite, "test_add_zero", test_add_zero)))
    {
        CU_cleanup_registry();
        return CU_get_error();
    }

    // Run tests
    CU_basic_set_mode(CU_BRM_VERBOSE);
    CU_basic_run_tests();

    int failures = CU_get_number_of_tests_failed();

    CU_cleanup_registry();

    return failures;
}
```

## Phase 3: Integration Test Implementation

Integration tests verify multiple components working together:

```c
/**

 * @file test_user_integration.c

 * @brief Integration tests for user registration workflow.
 *

 * Tests the complete user registration process including

 * validation, database storage, and notification.
 */

#include "unity.h"
#include "user_service.h"
#include "database.h"
#include "email_service.h"

static database_t *db;
static user_service_t *service;
static email_service_t *email_svc;

void setUp(void)
{
    // Setup test database
    db = database_create(":memory:");
    TEST_ASSERT_NOT_NULL(db);

    int result = database_init_schema(db);
    TEST_ASSERT_EQUAL_INT(0, result);

    // Setup services
    email_svc = email_service_create_test();
    service = user_service_create(db, email_svc);
}

void tearDown(void)
{
    if (service) user_service_destroy(service);
    if (email_svc) email_service_destroy(email_svc);
    if (db) database_destroy(db);
}

void test_register_user_creates_db_entry_and_sends_email(void)
{
    // Arrange
    const char *username = "newuser";
    const char *email = "newuser@example.com";
    const char *password = "SecurePass123!";

    // Act
    int user_id = user_service_register(service, username, email, password);

    // Assert - Verify database entry
    TEST_ASSERT_GREATER_THAN(0, user_id);

    user_t *user = database_get_user(db, user_id);
    TEST_ASSERT_NOT_NULL(user);
    TEST_ASSERT_EQUAL_STRING(username, user->username);
    TEST_ASSERT_EQUAL_STRING(email, user->email);
    TEST_ASSERT_NOT_EQUAL_STRING(password, user->password); // Should be hashed

    // Assert - Verify email sent
    int email_count = email_service_get_sent_count(email_svc);
    TEST_ASSERT_EQUAL_INT(1, email_count);

    // Cleanup
    user_destroy(user);
}

void test_register_duplicate_username_returns_error(void)
{
    // Arrange - Create existing user
    user_service_register(service, "alice", "alice@example.com", "Pass123!");

    // Act - Try to create duplicate
    int result = user_service_register(service, "alice", "different@example.com", "Pass123!");

    // Assert
    TEST_ASSERT_EQUAL_INT(ERROR_DUPLICATE_USERNAME, result);
}
```

## Phase 4: Memory Testing

Use Valgrind or similar tools to detect memory issues:

```c
/**

 * @brief Test for memory leaks in user creation.
 *

 * Run with: valgrind --leak-check=full ./test_program
 */
void test_user_create_and_destroy_no_memory_leak(void)
{
    // Arrange & Act
    user_t *user = user_create("Alice", "alice@example.com");
    TEST_ASSERT_NOT_NULL(user);

    // Assert - Verify user was created properly
    TEST_ASSERT_EQUAL_STRING("Alice", user->name);
    TEST_ASSERT_EQUAL_STRING("alice@example.com", user->email);

    // Cleanup
    user_destroy(user);
    // Valgrind should report no memory leaks
}

void test_repeated_allocations_no_memory_leak(void)
{
    // Create and destroy multiple users
    for (int i = 0; i < 1000; i++) {
        char name[20];
        snprintf(name, sizeof(name), "User%d", i);

        user_t *user = user_create(name, "test@example.com");
        TEST_ASSERT_NOT_NULL(user);

        user_destroy(user);
    }
    // Valgrind should report no memory leaks
}
```

## Phase 5: Test Best Practices

### 1. Test Independence

```c
// GOOD - Tests are independent
void setUp(void)
{
    // Fresh state for each test
    service = user_service_create();
}

void tearDown(void)
{
    // Clean up after each test
    if (service) {
        user_service_destroy(service);
        service = NULL;
    }
}

void test_create_user(void)
{
    int id = user_service_create_user(service, "alice", "alice@example.com", 30);
    TEST_ASSERT_GREATER_THAN(0, id);
}

void test_delete_user(void)
{
    // Independent - creates its own user
    int id = user_service_create_user(service, "bob", "bob@example.com", 25);
    int result = user_service_delete_user(service, id);
    TEST_ASSERT_EQUAL_INT(0, result);
}

// BAD - Tests depend on each other
static int global_user_id; // Shared state!

void test_01_create_user(void)
{
    global_user_id = user_service_create_user(service, "alice", "alice@example.com", 30);
}

void test_02_delete_user(void)
{
    // Depends on test_01 running first
    user_service_delete_user(service, global_user_id);
}
```

### 2. Clear Assertions

```c
// GOOD - Specific, clear assertions
void test_create_user_returns_valid_user(void)
{
    user_t *user = user_create("Alice", "alice@example.com", 30);

    TEST_ASSERT_NOT_NULL(user);
    TEST_ASSERT_EQUAL_STRING("Alice", user->name);
    TEST_ASSERT_EQUAL_STRING("alice@example.com", user->email);
    TEST_ASSERT_EQUAL_INT(30, user->age);
    TEST_ASSERT_NOT_EQUAL(0, user->created_at);
    TEST_ASSERT_TRUE(user->is_active);

    user_destroy(user);
}

// BAD - Vague or missing assertions
void test_create_user(void)
{
    user_t *user = user_create("Alice", "alice@example.com", 30);
    TEST_ASSERT_NOT_NULL(user); // Too vague - what about user?
    TEST_ASSERT_NOT_NULL(user->name); // Checks existence, not value
    user_destroy(user);
}
```

### 3. Proper Resource Management

```c
// GOOD - Proper cleanup
void test_file_operations(void)
{
    FILE *file = fopen("test.txt", "w");
    TEST_ASSERT_NOT_NULL(file);

    int result = fprintf(file, "test data");
    TEST_ASSERT_GREATER_THAN(0, result);

    fclose(file); // Always close resources
    remove("test.txt"); // Clean up test files
}

// GOOD - Handle allocation failures
void test_handles_malloc_failure(void)
{
    // Simulate allocation failure if possible
    buffer_t *buffer = buffer_create(SIZE_MAX);
    TEST_ASSERT_NULL(buffer); // Should handle gracefully
}
```

## Output Format

Please provide comprehensive test cases with the following structure:

### Test Coverage Summary

- **Total Test Cases**: [count]

- **Unit Tests**: [count]

- **Integration Tests**: [count]

- **Test Types**:

  - Happy path: [count]

  - Edge cases: [count]

  - Error conditions: [count]

  - Memory tests: [count]

### Test Case Implementation

For each module/function:

**Module**: `[module_name]`
**Test File**: `test_[module_name].c`

**Test Cases**:

1. `test_function_with_valid_input_returns_expected_result`

   - **Scenario**: [description]

   - **Input**: [test data]

   - **Expected**: [result]

   - **Type**: [unit/integration]

2. `test_function_with_invalid_input_returns_error`

   - **Scenario**: [description]

   - **Input**: [test data]

   - **Expected**: [error code]

   - **Type**: [unit/integration]

### Test Execution Results
```bash
# Run tests
make test

# Run with Valgrind
make test-valgrind

# Expected output
Running tests...
test_create_user_with_valid_data_returns_user_id ... PASS
test_create_user_with_invalid_email_returns_error ... PASS
...
25 Tests 0 Failures 0 Ignored
OK
```

### Coverage Gaps Identified

- [ ] [Function]: Missing tests for [scenario]

- [ ] [Function]: Need edge case tests for [condition]

- [ ] [Function]: Error handling not tested

- [ ] [Function]: Memory leak potential not tested

### Test Quality Metrics

- **Average test execution time**: [milliseconds]

- **Tests following AAA pattern**: [percentage]

- **Tests with clear names**: [percentage]

- **Independent tests**: [percentage]

- **Memory leaks detected**: [count]

### Next Steps

- [ ] Implement remaining test cases for coverage gaps

- [ ] Add memory leak detection for all allocation paths

- [ ] Set up continuous integration

- [ ] Configure code coverage reporting

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

3. **Integration tests** for workflows

4. **Memory leak tests** with Valgrind

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
