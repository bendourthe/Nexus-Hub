# C Unit Tests - Comprehensive Implementation Guide

## Objective

Develop comprehensive unit testing strategy for C applications using Unity and Check frameworks, focusing on test isolation, memory management, pointer testing, and thorough coverage following C best practices and FIRST principles.

---

## Output Directory Structure

```
{OUTPUT_DIR}/
├── templates/           # Reusable test templates
├── assets/             # Diagrams and visualizations
└── exports/            # Final documentation
```

---

## Implementation Checklist

### Test Foundation
- [ ] Unity and Check framework overview
- [ ] Test project structure
- [ ] Build system configuration (Make/CMake)
- [ ] Memory testing strategies

### Test Patterns
- [ ] Function tests
- [ ] Struct tests
- [ ] Pointer and memory tests
- [ ] File I/O tests
- [ ] Error handling tests

### Test Quality
- [ ] Memory leak detection
- [ ] Valgrind integration
- [ ] Coverage analysis (gcov)
- [ ] Edge cases covered

---

## Prompt Template

```markdown
# C Unit Testing Implementation - Comprehensive Guide

## Context
Generate comprehensive guidance for implementing unit tests in C using Unity or Check framework with detailed examples following C best practices.

## CRITICAL: Output Directory Setup

```bash
mkdir -p {OUTPUT_DIR}/templates {OUTPUT_DIR}/assets {OUTPUT_DIR}/exports
```

---

## Phase 1: C Testing Fundamentals

### 1.1 FIRST Principles in C

**Fast** - Tests execute quickly
- Avoid file I/O in unit tests
- Use memory-based operations
- Mock external dependencies

**Independent** - No shared state
- Clean up all allocated memory
- Reset global variables
- Use setUp/tearDown functions

**Repeatable** - Deterministic results
- Initialize all variables
- Don't rely on undefined behavior
- Control randomness

**Self-validating** - Clear assertions
- Use framework assertion macros
- Provide descriptive messages
- Check all error conditions

**Timely** - Written with code
- Test during development
- Maintain test coverage

**Arrange-Act-Assert Pattern:**
```c
void test_calculate_discount(void) {
    /* Arrange */
    double price = 100.0;
    double discount_rate = 0.20;
    double expected = 80.0;

    /* Act */
    double result = calculate_discount(price, discount_rate);

    /* Assert */
    TEST_ASSERT_EQUAL_DOUBLE(expected, result);
}
```

### 1.2 Framework Comparison

**Unity Framework:**
- Lightweight, portable
- No dynamic memory allocation
- Embedded systems friendly
- Simple setup

**Check Framework:**
- Fork-based isolation
- Memory leak detection
- XML/TAP output
- More features, heavier

---

## Phase 2: Project Organization

### 2.1 Directory Structure

```
project/
├── src/
│   ├── calculator.c
│   ├── calculator.h
│   ├── user.c
│   └── user.h
├── tests/
│   ├── test_calculator.c
│   ├── test_user.c
│   ├── test_runner.c
│   └── unity/
│       ├── unity.c
│       └── unity.h
├── Makefile
└── CMakeLists.txt
```

### 2.2 Unity Setup

**unity.h Integration:**
```c
#include "unity.h"

void setUp(void) {
    /* Setup code before each test */
}

void tearDown(void) {
    /* Cleanup code after each test */
}

int main(void) {
    UNITY_BEGIN();

    RUN_TEST(test_calculate_discount);
    RUN_TEST(test_invalid_discount_rate);

    return UNITY_END();
}
```

### 2.3 Makefile Configuration

```makefile
CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -I./src -I./tests/unity
LDFLAGS = -lm

SRC_FILES = src/calculator.c src/user.c
TEST_FILES = tests/test_calculator.c tests/test_user.c
UNITY_FILES = tests/unity/unity.c

OBJECTS = $(SRC_FILES:.c=.o) $(TEST_FILES:.c=.o) $(UNITY_FILES:.c=.o)

test: $(OBJECTS)
	$(CC) $(CFLAGS) -o test_runner tests/test_runner.c $(OBJECTS) $(LDFLAGS)
	./test_runner

clean:
	rm -f $(OBJECTS) test_runner

coverage:
	$(CC) $(CFLAGS) --coverage -o test_runner $(SRC_FILES) $(TEST_FILES) $(UNITY_FILES) tests/test_runner.c $(LDFLAGS)
	./test_runner
	gcov $(SRC_FILES)
	lcov --capture --directory . --output-file coverage.info
	genhtml coverage.info --output-directory coverage_html

.PHONY: test clean coverage
```

---

## Phase 3: Testing Different Components

### 3.1 Testing Pure Functions

**Example (calculator.h):**
```c
#ifndef CALCULATOR_H
#define CALCULATOR_H

#include <stddef.h>

typedef enum {
    CALC_SUCCESS = 0,
    CALC_ERROR_NEGATIVE_PRICE,
    CALC_ERROR_INVALID_RATE
} calc_error_t;

calc_error_t calculate_discount(double price, double discount_rate, double *result);

#endif /* CALCULATOR_H */
```

**Implementation (calculator.c):**
```c
#include "calculator.h"

calc_error_t calculate_discount(double price, double discount_rate, double *result) {
    if (result == NULL) {
        return CALC_ERROR_INVALID_RATE;
    }

    if (price < 0.0) {
        return CALC_ERROR_NEGATIVE_PRICE;
    }

    if (discount_rate < 0.0 || discount_rate > 1.0) {
        return CALC_ERROR_INVALID_RATE;
    }

    *result = price * (1.0 - discount_rate);
    return CALC_SUCCESS;
}
```

**Tests (test_calculator.c):**
```c
#include "unity.h"
#include "calculator.h"

void setUp(void) {
    /* Setup before each test */
}

void tearDown(void) {
    /* Cleanup after each test */
}

void test_calculate_discount_no_discount(void) {
    double result;
    calc_error_t error = calculate_discount(100.0, 0.0, &result);

    TEST_ASSERT_EQUAL(CALC_SUCCESS, error);
    TEST_ASSERT_EQUAL_DOUBLE(100.0, result);
}

void test_calculate_discount_full_discount(void) {
    double result;
    calc_error_t error = calculate_discount(100.0, 1.0, &result);

    TEST_ASSERT_EQUAL(CALC_SUCCESS, error);
    TEST_ASSERT_EQUAL_DOUBLE(0.0, result);
}

void test_calculate_discount_twenty_percent(void) {
    double result;
    calc_error_t error = calculate_discount(100.0, 0.20, &result);

    TEST_ASSERT_EQUAL(CALC_SUCCESS, error);
    TEST_ASSERT_DOUBLE_WITHIN(0.001, 80.0, result);
}

void test_calculate_discount_negative_price(void) {
    double result;
    calc_error_t error = calculate_discount(-100.0, 0.20, &result);

    TEST_ASSERT_EQUAL(CALC_ERROR_NEGATIVE_PRICE, error);
}

void test_calculate_discount_invalid_rate_below_zero(void) {
    double result;
    calc_error_t error = calculate_discount(100.0, -0.10, &result);

    TEST_ASSERT_EQUAL(CALC_ERROR_INVALID_RATE, error);
}

void test_calculate_discount_invalid_rate_above_one(void) {
    double result;
    calc_error_t error = calculate_discount(100.0, 1.5, &result);

    TEST_ASSERT_EQUAL(CALC_ERROR_INVALID_RATE, error);
}

void test_calculate_discount_null_result_pointer(void) {
    calc_error_t error = calculate_discount(100.0, 0.20, NULL);

    TEST_ASSERT_EQUAL(CALC_ERROR_INVALID_RATE, error);
}
```

### 3.2 Testing Structs and Memory Management

**Example (user.h):**
```c
#ifndef USER_H
#define USER_H

#include <stdbool.h>
#include <time.h>

typedef enum {
    USER_SUCCESS = 0,
    USER_ERROR_NULL_POINTER,
    USER_ERROR_INVALID_NAME,
    USER_ERROR_INVALID_EMAIL,
    USER_ERROR_INVALID_AGE,
    USER_ERROR_MEMORY
} user_error_t;

typedef struct {
    char *name;
    char *email;
    int age;
    time_t created_at;
    bool active;
} user_t;

user_error_t user_create(const char *name, const char *email, int age, user_t **user);
void user_destroy(user_t *user);
void user_activate(user_t *user);
void user_deactivate(user_t *user);

#endif /* USER_H */
```

**Implementation (user.c):**
```c
#include "user.h"
#include <stdlib.h>
#include <string.h>

static bool is_valid_email(const char *email) {
    if (email == NULL || strlen(email) == 0) {
        return false;
    }
    return strchr(email, '@') != NULL;
}

user_error_t user_create(const char *name, const char *email, int age, user_t **user) {
    if (user == NULL) {
        return USER_ERROR_NULL_POINTER;
    }

    if (name == NULL || strlen(name) == 0) {
        return USER_ERROR_INVALID_NAME;
    }

    if (!is_valid_email(email)) {
        return USER_ERROR_INVALID_EMAIL;
    }

    if (age < 0) {
        return USER_ERROR_INVALID_AGE;
    }

    *user = (user_t *)malloc(sizeof(user_t));
    if (*user == NULL) {
        return USER_ERROR_MEMORY;
    }

    (*user)->name = strdup(name);
    (*user)->email = strdup(email);

    if ((*user)->name == NULL || (*user)->email == NULL) {
        free((*user)->name);
        free((*user)->email);
        free(*user);
        return USER_ERROR_MEMORY;
    }

    (*user)->age = age;
    (*user)->created_at = time(NULL);
    (*user)->active = true;

    return USER_SUCCESS;
}

void user_destroy(user_t *user) {
    if (user != NULL) {
        free(user->name);
        free(user->email);
        free(user);
    }
}

void user_activate(user_t *user) {
    if (user != NULL) {
        user->active = true;
    }
}

void user_deactivate(user_t *user) {
    if (user != NULL) {
        user->active = false;
    }
}
```

**Tests (test_user.c):**
```c
#include "unity.h"
#include "user.h"
#include <string.h>

static user_t *test_user = NULL;

void setUp(void) {
    test_user = NULL;
}

void tearDown(void) {
    if (test_user != NULL) {
        user_destroy(test_user);
        test_user = NULL;
    }
}

void test_user_create_with_valid_inputs(void) {
    user_error_t error = user_create("John Doe", "john@example.com", 30, &test_user);

    TEST_ASSERT_EQUAL(USER_SUCCESS, error);
    TEST_ASSERT_NOT_NULL(test_user);
    TEST_ASSERT_EQUAL_STRING("John Doe", test_user->name);
    TEST_ASSERT_EQUAL_STRING("john@example.com", test_user->email);
    TEST_ASSERT_EQUAL_INT(30, test_user->age);
    TEST_ASSERT_TRUE(test_user->active);
}

void test_user_create_with_empty_name(void) {
    user_error_t error = user_create("", "john@example.com", 30, &test_user);

    TEST_ASSERT_EQUAL(USER_ERROR_INVALID_NAME, error);
    TEST_ASSERT_NULL(test_user);
}

void test_user_create_with_null_name(void) {
    user_error_t error = user_create(NULL, "john@example.com", 30, &test_user);

    TEST_ASSERT_EQUAL(USER_ERROR_INVALID_NAME, error);
    TEST_ASSERT_NULL(test_user);
}

void test_user_create_with_invalid_email(void) {
    user_error_t error = user_create("John", "invalid-email", 30, &test_user);

    TEST_ASSERT_EQUAL(USER_ERROR_INVALID_EMAIL, error);
    TEST_ASSERT_NULL(test_user);
}

void test_user_create_with_negative_age(void) {
    user_error_t error = user_create("John", "john@example.com", -5, &test_user);

    TEST_ASSERT_EQUAL(USER_ERROR_INVALID_AGE, error);
    TEST_ASSERT_NULL(test_user);
}

void test_user_create_with_null_output_pointer(void) {
    user_error_t error = user_create("John", "john@example.com", 30, NULL);

    TEST_ASSERT_EQUAL(USER_ERROR_NULL_POINTER, error);
}

void test_user_activate_and_deactivate(void) {
    user_create("John", "john@example.com", 30, &test_user);

    TEST_ASSERT_TRUE(test_user->active);

    user_deactivate(test_user);
    TEST_ASSERT_FALSE(test_user->active);

    user_activate(test_user);
    TEST_ASSERT_TRUE(test_user->active);
}

void test_user_destroy_with_null(void) {
    /* Should not crash */
    user_destroy(NULL);
    TEST_PASS();
}
```

### 3.3 Testing Arrays and Pointers

**Example (array_utils.h):**
```c
#ifndef ARRAY_UTILS_H
#define ARRAY_UTILS_H

#include <stddef.h>

int sum_array(const int *arr, size_t size);
void double_array(int *arr, size_t size);
int *create_range(int start, int end, size_t *out_size);
void free_range(int *arr);

#endif /* ARRAY_UTILS_H */
```

**Tests:**
```c
#include "unity.h"
#include "array_utils.h"
#include <stdlib.h>

void test_sum_array_with_positive_numbers(void) {
    int arr[] = {1, 2, 3, 4, 5};
    int result = sum_array(arr, 5);

    TEST_ASSERT_EQUAL_INT(15, result);
}

void test_sum_array_with_empty_array(void) {
    int result = sum_array(NULL, 0);

    TEST_ASSERT_EQUAL_INT(0, result);
}

void test_double_array_modifies_in_place(void) {
    int arr[] = {1, 2, 3};
    int expected[] = {2, 4, 6};

    double_array(arr, 3);

    TEST_ASSERT_EQUAL_INT_ARRAY(expected, arr, 3);
}

void test_create_range_allocates_correct_array(void) {
    size_t size;
    int *arr = create_range(1, 5, &size);

    TEST_ASSERT_NOT_NULL(arr);
    TEST_ASSERT_EQUAL_size_t(5, size);
    TEST_ASSERT_EQUAL_INT(1, arr[0]);
    TEST_ASSERT_EQUAL_INT(5, arr[4]);

    free_range(arr);
}

void test_create_range_with_null_size_pointer(void) {
    int *arr = create_range(1, 5, NULL);

    TEST_ASSERT_NULL(arr);
}
```

### 3.4 Testing Function Pointers and Callbacks

**Example:**
```c
typedef int (*comparator_fn)(const void *a, const void *b);

void sort_array(int *arr, size_t size, comparator_fn compare);

int ascending(const void *a, const void *b) {
    return (*(int *)a - *(int *)b);
}

int descending(const void *a, const void *b) {
    return (*(int *)b - *(int *)a);
}
```

**Tests:**
```c
void test_sort_array_ascending(void) {
    int arr[] = {3, 1, 4, 1, 5};
    int expected[] = {1, 1, 3, 4, 5};

    sort_array(arr, 5, ascending);

    TEST_ASSERT_EQUAL_INT_ARRAY(expected, arr, 5);
}

void test_sort_array_descending(void) {
    int arr[] = {3, 1, 4, 1, 5};
    int expected[] = {5, 4, 3, 1, 1};

    sort_array(arr, 5, descending);

    TEST_ASSERT_EQUAL_INT_ARRAY(expected, arr, 5);
}
```

---

## Phase 4: Advanced Testing

### 4.1 Memory Leak Detection with Valgrind

**Run with Valgrind:**
```bash
valgrind --leak-check=full --show-leak-kinds=all ./test_runner
```

**Example output:**
```
==12345== HEAP SUMMARY:
==12345==     in use at exit: 0 bytes in 0 blocks
==12345==   total heap usage: 100 allocs, 100 frees, 10,000 bytes allocated
==12345==
==12345== All heap blocks were freed -- no leaks are possible
```

### 4.2 Static Analysis

**Using cppcheck:**
```bash
cppcheck --enable=all --inconclusive --std=c99 src/
```

**Using clang static analyzer:**
```bash
scan-build make
```

### 4.3 Code Coverage

**Generate coverage with gcov:**
```bash
gcc -fprofile-arcs -ftest-coverage -o test_runner src/*.c tests/*.c
./test_runner
gcov src/calculator.c
```

**Generate HTML report with lcov:**
```bash
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage_html
```

### 4.4 Unity Assertions Reference

```c
/* Basic assertions */
TEST_ASSERT_TRUE(condition);
TEST_ASSERT_FALSE(condition);
TEST_ASSERT(condition);

/* Equality assertions */
TEST_ASSERT_EQUAL(expected, actual);
TEST_ASSERT_EQUAL_INT(expected, actual);
TEST_ASSERT_EQUAL_UINT(expected, actual);
TEST_ASSERT_EQUAL_HEX(expected, actual);

/* Floating point */
TEST_ASSERT_EQUAL_FLOAT(expected, actual);
TEST_ASSERT_EQUAL_DOUBLE(expected, actual);
TEST_ASSERT_FLOAT_WITHIN(delta, expected, actual);
TEST_ASSERT_DOUBLE_WITHIN(delta, expected, actual);

/* String assertions */
TEST_ASSERT_EQUAL_STRING(expected, actual);
TEST_ASSERT_EQUAL_STRING_LEN(expected, actual, len);

/* Pointer assertions */
TEST_ASSERT_NULL(pointer);
TEST_ASSERT_NOT_NULL(pointer);
TEST_ASSERT_EQUAL_PTR(expected, actual);

/* Array assertions */
TEST_ASSERT_EQUAL_INT_ARRAY(expected, actual, num_elements);
TEST_ASSERT_EQUAL_MEMORY(expected, actual, len);

/* Bitwise assertions */
TEST_ASSERT_BITS(mask, expected, actual);
TEST_ASSERT_BITS_HIGH(mask, actual);
TEST_ASSERT_BITS_LOW(mask, actual);

/* Custom messages */
TEST_ASSERT_MESSAGE(condition, message);
TEST_ASSERT_EQUAL_INT_MESSAGE(expected, actual, message);
```

---

## Phase 5: Best Practices

### 5.1 Common Pitfalls

**Pitfall: Memory Leaks**
```c
/* BAD - Memory leak */
void test_leak(void) {
    char *str = malloc(100);
    strcpy(str, "test");
    TEST_ASSERT_EQUAL_STRING("test", str);
    /* Missing free(str) */
}

/* GOOD - Proper cleanup */
void test_no_leak(void) {
    char *str = malloc(100);
    strcpy(str, "test");
    TEST_ASSERT_EQUAL_STRING("test", str);
    free(str);
}
```

**Pitfall: Buffer Overflows**
```c
/* BAD - Buffer overflow */
void test_overflow(void) {
    char buffer[10];
    strcpy(buffer, "This is too long"); /* Overflow! */
}

/* GOOD - Safe operations */
void test_safe(void) {
    char buffer[10];
    strncpy(buffer, "This is too long", sizeof(buffer) - 1);
    buffer[sizeof(buffer) - 1] = '\0';
}
```

**Pitfall: Uninitialized Variables**
```c
/* BAD - Undefined behavior */
void test_uninitialized(void) {
    int value; /* Uninitialized */
    TEST_ASSERT_EQUAL(0, value); /* Undefined behavior */
}

/* GOOD - Initialize variables */
void test_initialized(void) {
    int value = 0;
    TEST_ASSERT_EQUAL(0, value);
}
```

### 5.2 Test Maintenance Checklist

- [ ] All allocated memory freed
- [ ] No buffer overflows
- [ ] All variables initialized
- [ ] Pointers checked for NULL
- [ ] Error conditions tested
- [ ] Valgrind clean run
- [ ] No compiler warnings
- [ ] >80% code coverage
- [ ] Clear test names
- [ ] setUp/tearDown used properly

---

## Output Deliverables

### 1. Implementation Guide (20-30 pages)
`{OUTPUT_DIR}/exports/unit_test_implementation_guide.md`

### 2. Test Examples (50+ tests)
`{OUTPUT_DIR}/exports/unit_test_examples.md`

### 3. Templates
`{OUTPUT_DIR}/templates/`:
- `test_template.c`
- `test_runner_template.c`
- `Makefile`
- `CMakeLists.txt`

### 4. Guides
- Memory management guide
- Valgrind usage guide
- Coverage guide
- Anti-patterns guide
- Quality checklist

---

## Verification Checklist

- [ ] All deliverables created
- [ ] 20-30 page guide
- [ ] 50+ test examples
- [ ] Unity framework covered
- [ ] Memory testing patterns
- [ ] Pointer testing examples
- [ ] Valgrind integration
- [ ] Build configurations

---
```

End of prompt template.

---

## Additional Notes

- Compile: `gcc -o test test.c src.c unity.c`
- Run tests: `./test`
- With Valgrind: `valgrind --leak-check=full ./test`
- Coverage: `gcc --coverage -o test test.c src.c`
- Generate report: `gcov src.c && lcov`

---

**Status:** Template ready. Copy the prompt into your AI assistant for comprehensive C unit testing guidance.
