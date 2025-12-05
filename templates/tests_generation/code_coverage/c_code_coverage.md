---
template_id: c_code_coverage
template_name: Code Coverage - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: tests_generation
phase: code_coverage
phase_number: 6
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites:

  - tests_generation/performance_testing/c_performance_testing.md
related_templates:

  - tests_generation/maintenance_cicd/c_maintenance_cicd.md
tools:

  - unity

  - cmocka

  - check
tags:

  - test-development

  - c
---
# C Code Coverage Analysis

## Your Position in the 8-Phase Testing Methodology

```
┌─────────────────────────────────────────────────────────┐
│ Phase 1: Test Structure Setup                  ► │ [COMPLETE]
│ Phase 2: Unit Tests                            ► │ [COMPLETE]
│ Phase 3: Test Cases Development                ► │ [COMPLETE]
│ Phase 4: Mocks & Fixtures                      ► │ [COMPLETE]
│ Phase 5: Performance Testing                   ► │ [COMPLETE]
│ Phase 6: Code Coverage                          ► │ ● CURRENT
│ Phase 7: Maintenance & CI/CD                       ► │ [NEXT]
│ Phase 8: Reward Hacking Validation                       ► │ 
└─────────────────────────────────────────────────────────┘
```

**Prerequisites:** Phase 5 (Performance Testing) should be completed first
**Next Step:** Phase 7 (Maintenance & CI/CD)

---


## Objective
Implement comprehensive code coverage measurement using gcov/lcov, analyze coverage gaps, establish coverage goals (80%+ target), create systematic improvement strategies, integrate coverage into CI/CD, and maintain high-quality test coverage for C projects.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/code_coverage/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/code_coverage/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Coverage Setup

- [ ] gcov/lcov installed and configured

- [ ] Compilation flags configured for coverage

- [ ] HTML report generation configured (lcov + genhtml)

- [ ] CI/CD coverage reporting set up

- [ ] Coverage thresholds defined

### Coverage Analysis

- [ ] Current coverage baseline measured

- [ ] Coverage gaps identified and prioritized

- [ ] Critical paths coverage verified

- [ ] Edge cases coverage assessed

- [ ] Untested code documented

### Coverage Goals

- [ ] Target coverage defined (80%+ recommended)

- [ ] Coverage thresholds set by module

- [ ] Critical path coverage requirements established

- [ ] Coverage improvement plan created

- [ ] Timeline for improvements defined

### Coverage Integration

- [ ] Coverage gates in CI/CD configured

- [ ] Coverage reports automated

- [ ] Coverage trends tracked

- [ ] Coverage regression prevention enabled

- [ ] Team coverage standards documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Code Coverage Implementation

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/code_coverage"
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

Please implement comprehensive code coverage measurement and improvement for this C project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: Coverage Setup and Configuration

### Install Coverage Tools

**Ubuntu/Debian**:
```bash
sudo apt-get install gcov lcov
```

**macOS**:
```bash
brew install lcov
```

**RHEL/CentOS**:
```bash
sudo yum install gcc lcov
```

### Configure Makefile for Coverage

**Basic Makefile with coverage support**:
```makefile
# Compiler settings
CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -g
LDFLAGS =

# Coverage flags
COVERAGE_CFLAGS = --coverage -fprofile-arcs -ftest-arcs
COVERAGE_LDFLAGS = --coverage -lgcov

# Directories
SRC_DIR = src
TEST_DIR = tests
BUILD_DIR = build
COVERAGE_DIR = coverage

# Source files
SRCS = $(wildcard $(SRC_DIR)/*.c)
OBJS = $(SRCS:$(SRC_DIR)/%.c=$(BUILD_DIR)/%.o)
TEST_SRCS = $(wildcard $(TEST_DIR)/*.c)
TEST_OBJS = $(TEST_SRCS:$(TEST_DIR)/%.c=$(BUILD_DIR)/%.o)

# Targets
TARGET = myapp
TEST_TARGET = test_runner

# Default target
all: $(TARGET)

# Build main application
$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

# Build with coverage instrumentation
coverage: CFLAGS += $(COVERAGE_CFLAGS)
coverage: LDFLAGS += $(COVERAGE_LDFLAGS)
coverage: clean $(TEST_TARGET)
	./$(TEST_TARGET)
	@echo "Generating coverage report..."
	lcov --capture --directory . --output-file $(COVERAGE_DIR)/coverage.info
	lcov --remove $(COVERAGE_DIR)/coverage.info '/usr/*' '*/tests/*' --output-file $(COVERAGE_DIR)/coverage.info
	genhtml $(COVERAGE_DIR)/coverage.info --output-directory $(COVERAGE_DIR)/html
	@echo "Coverage report generated: $(COVERAGE_DIR)/html/index.html"

# Build test runner
$(TEST_TARGET): CFLAGS += $(COVERAGE_CFLAGS)
$(TEST_TARGET): LDFLAGS += $(COVERAGE_LDFLAGS)
$(TEST_TARGET): $(filter-out $(BUILD_DIR)/main.o, $(OBJS)) $(TEST_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^

# Compile source files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Compile test files
$(BUILD_DIR)/%.o: $(TEST_DIR)/%.c
	@mkdir -p $(BUILD_DIR)
	$(CC) $(CFLAGS) -I$(SRC_DIR) -c $< -o $@

# Run tests
test: $(TEST_TARGET)
	./$(TEST_TARGET)

# Check coverage threshold
coverage-check: coverage
	@COVERAGE=$$(lcov --summary $(COVERAGE_DIR)/coverage.info 2>&1 | \
		grep "lines" | awk '{print $$2}' | sed 's/%//'); \
	echo "Line coverage: $$COVERAGE%"; \
	if [ $$(echo "$$COVERAGE < 80.0" | bc) -eq 1 ]; then \
		echo "✗ Coverage $$COVERAGE% is below threshold 80%"; \
		exit 1; \
	else \
		echo "✓ Coverage $$COVERAGE% meets threshold 80%"; \
	fi

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(TARGET) $(TEST_TARGET)
	rm -f *.gcda *.gcno *.gcov
	find . -name "*.gcda" -delete
	find . -name "*.gcno" -delete

# Clean coverage data
clean-coverage:
	rm -rf $(COVERAGE_DIR)
	rm -f *.gcda *.gcno *.gcov
	find . -name "*.gcda" -delete
	find . -name "*.gcno" -delete

.PHONY: all test coverage coverage-check clean clean-coverage
```

### CMake Configuration for Coverage

**CMakeLists.txt with coverage support**:
```cmake
cmake_minimum_required(VERSION 3.10)
project(MyApp C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra")

# Coverage option
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --coverage -fprofile-arcs -ftest-arcs")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage -lgcov")
    message(STATUS "Coverage reporting enabled")
endif()

# Source files
file(GLOB SOURCES "src/*.c")
list(REMOVE_ITEM SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src/main.c")

# Main executable
add_executable(myapp src/main.c ${SOURCES})

# Test executable
enable_testing()
file(GLOB TEST_SOURCES "tests/*.c")
add_executable(test_runner ${TEST_SOURCES} ${SOURCES})
add_test(NAME UnitTests COMMAND test_runner)

# Coverage target
if(ENABLE_COVERAGE)
    add_custom_target(coverage
        COMMAND ${CMAKE_CTEST_COMMAND}
        COMMAND lcov --capture --directory . --output-file coverage.info
        COMMAND lcov --remove coverage.info '/usr/*' '*/tests/*' --output-file coverage.info
        COMMAND genhtml coverage.info --output-directory coverage/html
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMENT "Generating coverage report"
    )

    add_custom_target(coverage-check
        COMMAND bash -c "COVERAGE=$$(lcov --summary coverage.info 2>&1 | grep 'lines' | awk '{print $$2}' | sed 's/%//'); \
            echo \"Line coverage: $$COVERAGE%\"; \
            if [ $$(echo \"$$COVERAGE < 80.0\" | bc) -eq 1 ]; then \
                echo \"✗ Coverage $$COVERAGE% is below threshold 80%\"; \
                exit 1; \
            else \
                echo \"✓ Coverage $$COVERAGE% meets threshold 80%\"; \
            fi"
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        DEPENDS coverage
        COMMENT "Checking coverage threshold"
    )
endif()
```

Build with coverage:
```bash
mkdir build && cd build
cmake -DENABLE_COVERAGE=ON ..
make
make test
make coverage
```

### Coverage Shell Script

**scripts/coverage.sh**:
```bash
#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
COVERAGE_DIR="coverage"
MIN_COVERAGE=80.0

echo "Building with coverage instrumentation..."
make clean
make coverage

echo ""
echo "========================================"
echo "Coverage Summary"
echo "========================================"
lcov --summary ${COVERAGE_DIR}/coverage.info

echo ""
echo "========================================"
echo "Coverage by File"
echo "========================================"
lcov --list ${COVERAGE_DIR}/coverage.info | grep -E "\.c$"

# Extract total line coverage
TOTAL_COVERAGE=$(lcov --summary ${COVERAGE_DIR}/coverage.info 2>&1 | \
    grep "lines" | \
    awk '{print $2}' | \
    sed 's/%//')

echo ""
echo "Total Line Coverage: ${TOTAL_COVERAGE}%"

# Check threshold
if (( $(echo "$TOTAL_COVERAGE < $MIN_COVERAGE" | bc -l) )); then
    echo -e "${RED}✗ Coverage ${TOTAL_COVERAGE}% is below threshold ${MIN_COVERAGE}%${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Coverage ${TOTAL_COVERAGE}% meets threshold ${MIN_COVERAGE}%${NC}"
fi

echo ""
echo "HTML report: ${COVERAGE_DIR}/html/index.html"
```

## Phase 2: Measure Current Coverage

### Run Coverage Analysis

```bash
# Using Makefile
make coverage

# Using CMake
cd build
cmake -DENABLE_COVERAGE=ON ..
make
make test
make coverage

# Using script
chmod +x scripts/coverage.sh
./scripts/coverage.sh

# View HTML report
open coverage/html/index.html  # macOS
xdg-open coverage/html/index.html  # Linux
```

### Analyze Coverage Report

**Terminal output example**:
```
Reading tracefile coverage.info
Summary coverage rate:
  lines......: 76.3% (231 of 304 lines)
  functions..: 81.2% (43 of 53 functions)
  branches...: 68.4% (45 of 66 branches)

File 'src/auth.c'
  Lines executed: 78.26% of 46
  Functions executed: 85.71% of 7
  Branches executed: 70.00% of 20

File 'src/service.c'
  Lines executed: 67.42% of 89
  Functions executed: 70.59% of 17
  Branches executed: 55.56% of 27
```

### Identify Coverage Gaps

**Create coverage gap analyzer script**:

```c
// scripts/analyze_coverage.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    char filename[256];
    float line_coverage;
    float function_coverage;
    float branch_coverage;
    char priority[16];
} CoverageGap;

int compare_coverage(const void *a, const void *b) {
    CoverageGap *gap_a = (CoverageGap *)a;
    CoverageGap *gap_b = (CoverageGap *)b;
    if (gap_a->line_coverage < gap_b->line_coverage) return -1;
    if (gap_a->line_coverage > gap_b->line_coverage) return 1;
    return 0;
}

void determine_priority(CoverageGap *gap) {
    float avg = (gap->line_coverage + gap->function_coverage + gap->branch_coverage) / 3.0;
    if (avg < 50.0) {
        strcpy(gap->priority, "HIGH");
    } else if (avg < 70.0) {
        strcpy(gap->priority, "MEDIUM");
    } else {
        strcpy(gap->priority, "LOW");
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <lcov_list_output.txt>\n", argv[0]);
        return 1;
    }

    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open file %s\n", argv[1]);
        return 1;
    }

    CoverageGap gaps[100];
    int gap_count = 0;
    char line[512];

    while (fgets(line, sizeof(line), fp)) {
        CoverageGap gap;
        float coverage;

        if (sscanf(line, " %s %f%%", gap.filename, &coverage) == 2) {
            if (strstr(gap.filename, ".c") && coverage < 80.0) {
                gap.line_coverage = coverage;
                gap.function_coverage = coverage;  // Simplified
                gap.branch_coverage = coverage;    // Simplified
                determine_priority(&gap);
                gaps[gap_count++] = gap;
            }
        }
    }
    fclose(fp);

    qsort(gaps, gap_count, sizeof(CoverageGap), compare_coverage);

    printf("================================================================================\n");
    printf("Coverage Gap Analysis\n");
    printf("================================================================================\n");
    printf("%-40s %10s %10s %10s %10s\n",
        "File", "Lines", "Functions", "Branches", "Priority");
    printf("--------------------------------------------------------------------------------\n");

    for (int i = 0; i < gap_count; i++) {
        printf("%-40s %9.1f%% %9.1f%% %9.1f%% %10s\n",
            gaps[i].filename,
            gaps[i].line_coverage,
            gaps[i].function_coverage,
            gaps[i].branch_coverage,
            gaps[i].priority);
    }

    printf("\nTotal files needing improvement: %d\n", gap_count);

    return 0;
}
```

Compile and run:
```bash
gcc -o analyze_coverage scripts/analyze_coverage.c
lcov --list coverage/coverage.info > ${OUTPUT_DIR}/exports/coverage_list.txt
./analyze_coverage coverage_list.txt
```

## Phase 3: Prioritize Coverage Improvements

### Coverage Improvement Matrix

| Priority | Criteria | Action |
|----------|----------|--------|
| **Critical** | Core business logic <50% coverage | Immediate test creation |
| **High** | Public APIs <70% coverage | Test in current sprint |
| **Medium** | Utilities <80% coverage | Test in next sprint |
| **Low** | Internal helpers <80% coverage | Test when modified |

## Phase 4: Systematic Coverage Improvement

### Strategy 1: Fill Happy Path Coverage

```c
/**

 * Add tests for basic functionality of uncovered code.
 *

 * Focus on main execution paths first.
 */

// src/discount.h
typedef enum {
    CUSTOMER_PREMIUM,
    CUSTOMER_REGULAR,
    CUSTOMER_GUEST
} CustomerType;

double calculate_discount(double price, CustomerType customer_type);

// src/discount.c
#include "discount.h"

double calculate_discount(double price, CustomerType customer_type) {
    switch (customer_type) {
        case CUSTOMER_PREMIUM:
            return price * 0.20;
        case CUSTOMER_REGULAR:
            return price * 0.10;
        default:
            return 0.0;
    }
}

// tests/test_discount.c
#include <stdio.h>
#include <assert.h>
#include <math.h>
#include "../src/discount.h"

#define EPSILON 0.0001

void test_calculate_discount_premium() {
    double discount = calculate_discount(100.0, CUSTOMER_PREMIUM);
    assert(fabs(discount - 20.0) < EPSILON);
    printf("✓ test_calculate_discount_premium passed\n");
}

void test_calculate_discount_regular() {
    double discount = calculate_discount(100.0, CUSTOMER_REGULAR);
    assert(fabs(discount - 10.0) < EPSILON);
    printf("✓ test_calculate_discount_regular passed\n");
}

void test_calculate_discount_guest() {
    double discount = calculate_discount(100.0, CUSTOMER_GUEST);
    assert(fabs(discount - 0.0) < EPSILON);
    printf("✓ test_calculate_discount_guest passed\n");
}

int main() {
    printf("Running discount calculator tests...\n");
    test_calculate_discount_premium();
    test_calculate_discount_regular();
    test_calculate_discount_guest();
    printf("All tests passed!\n");
    return 0;
}
```

### Strategy 2: Cover Edge Cases

```c
/**

 * Add tests for boundary conditions and edge cases.
 */

// tests/test_discount_edge_cases.c
#include <stdio.h>
#include <assert.h>
#include <math.h>
#include <float.h>
#include "../src/discount.h"

#define EPSILON 0.0001

void test_zero_price() {
    double discount = calculate_discount(0.0, CUSTOMER_PREMIUM);
    assert(fabs(discount - 0.0) < EPSILON);
    printf("✓ test_zero_price passed\n");
}

void test_negative_price() {
    double discount = calculate_discount(-100.0, CUSTOMER_PREMIUM);
    assert(fabs(discount - (-20.0)) < EPSILON);
    printf("✓ test_negative_price passed\n");
}

void test_very_large_price() {
    double discount = calculate_discount(1000000.0, CUSTOMER_PREMIUM);
    assert(fabs(discount - 200000.0) < EPSILON);
    printf("✓ test_very_large_price passed\n");
}

void test_small_decimal() {
    double discount = calculate_discount(0.01, CUSTOMER_PREMIUM);
    assert(discount >= 0.0);
    printf("✓ test_small_decimal passed\n");
}

void test_max_double() {
    double discount = calculate_discount(DBL_MAX, CUSTOMER_PREMIUM);
    assert(discount > 0.0 || discount == INFINITY);
    printf("✓ test_max_double passed\n");
}

void test_invalid_customer_type() {
    double discount = calculate_discount(100.0, (CustomerType)99);
    assert(fabs(discount - 0.0) < EPSILON);
    printf("✓ test_invalid_customer_type passed\n");
}

int main() {
    printf("Running edge case tests...\n");
    test_zero_price();
    test_negative_price();
    test_very_large_price();
    test_small_decimal();
    test_max_double();
    test_invalid_customer_type();
    printf("All edge case tests passed!\n");
    return 0;
}
```

### Strategy 3: Cover Error Paths

```c
/**

 * Add tests for error handling and exceptional conditions.
 */

// src/user_service.h
typedef struct {
    long id;
    char name[100];
} User;

typedef enum {
    SUCCESS = 0,
    ERR_NOT_FOUND = -1,
    ERR_DATABASE = -2,
    ERR_INVALID_INPUT = -3
} ErrorCode;

ErrorCode load_user_data(long user_id, User *user);

// src/user_service.c
#include "user_service.h"
#include <string.h>
#include <stdio.h>

// Simulated database
extern ErrorCode db_find_user(long user_id, User *user);

ErrorCode load_user_data(long user_id, User *user) {
    if (!user || user_id <= 0) {
        fprintf(stderr, "Invalid input\n");
        return ERR_INVALID_INPUT;
    }

    ErrorCode result = db_find_user(user_id, user);

    if (result == ERR_DATABASE) {
        fprintf(stderr, "Database error loading user: %ld\n", user_id);
        return ERR_DATABASE;
    }

    if (result == ERR_NOT_FOUND) {
        fprintf(stderr, "User not found: %ld\n", user_id);
        return ERR_NOT_FOUND;
    }

    return SUCCESS;
}

// tests/test_user_service.c
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include "../src/user_service.h"

// Mock database
static ErrorCode mock_result = SUCCESS;
static User mock_user = {123, "John Doe"};

ErrorCode db_find_user(long user_id, User *user) {
    if (mock_result == SUCCESS) {
        *user = mock_user;
    }
    return mock_result;
}

void test_load_user_success() {
    mock_result = SUCCESS;
    User user;
    ErrorCode result = load_user_data(123, &user);
    assert(result == SUCCESS);
    assert(user.id == 123);
    assert(strcmp(user.name, "John Doe") == 0);
    printf("✓ test_load_user_success passed\n");
}

void test_load_user_not_found() {
    mock_result = ERR_NOT_FOUND;
    User user;
    ErrorCode result = load_user_data(999, &user);
    assert(result == ERR_NOT_FOUND);
    printf("✓ test_load_user_not_found passed\n");
}

void test_load_user_database_error() {
    mock_result = ERR_DATABASE;
    User user;
    ErrorCode result = load_user_data(123, &user);
    assert(result == ERR_DATABASE);
    printf("✓ test_load_user_database_error passed\n");
}

void test_load_user_null_pointer() {
    ErrorCode result = load_user_data(123, NULL);
    assert(result == ERR_INVALID_INPUT);
    printf("✓ test_load_user_null_pointer passed\n");
}

void test_load_user_invalid_id() {
    User user;
    ErrorCode result = load_user_data(-1, &user);
    assert(result == ERR_INVALID_INPUT);
    printf("✓ test_load_user_invalid_id passed\n");
}

int main() {
    printf("Running user service error handling tests...\n");
    test_load_user_success();
    test_load_user_not_found();
    test_load_user_database_error();
    test_load_user_null_pointer();
    test_load_user_invalid_id();
    printf("All error handling tests passed!\n");
    return 0;
}
```

### Strategy 4: Cover Branch Conditions

```c
/**

 * Ensure all branches of conditional logic are tested.
 */

// src/shipping.h
typedef enum {
    DEST_DOMESTIC,
    DEST_INTERNATIONAL,
    DEST_REMOTE
} Destination;

double calculate_shipping_cost(double weight, Destination destination, int express);

// src/shipping.c
#include "shipping.h"

double calculate_shipping_cost(double weight, Destination destination, int express) {
    double base_cost = weight * 2.5;

    switch (destination) {
        case DEST_INTERNATIONAL:
            base_cost *= 3.0;
            break;
        case DEST_REMOTE:
            base_cost *= 1.5;
            break;
        default:
            break;
    }

    if (express) {
        base_cost *= 2.0;
    }

    return base_cost;
}

// tests/test_shipping.c
#include <stdio.h>
#include <assert.h>
#include <math.h>
#include "../src/shipping.h"

#define EPSILON 0.01

typedef struct {
    const char *name;
    Destination destination;
    int express;
    double expected;
} TestCase;

void test_all_branches() {
    TestCase tests[] = {
        {"domestic standard", DEST_DOMESTIC, 0, 25.0},
        {"domestic express", DEST_DOMESTIC, 1, 50.0},
        {"international standard", DEST_INTERNATIONAL, 0, 75.0},
        {"international express", DEST_INTERNATIONAL, 1, 150.0},
        {"remote standard", DEST_REMOTE, 0, 37.5},
        {"remote express", DEST_REMOTE, 1, 75.0}
    };

    int num_tests = sizeof(tests) / sizeof(tests[0]);

    for (int i = 0; i < num_tests; i++) {
        double cost = calculate_shipping_cost(10.0, tests[i].destination, tests[i].express);
        assert(fabs(cost - tests[i].expected) < EPSILON);
        printf("✓ test_%s passed (%.2f)\n", tests[i].name, cost);
    }
}

int main() {
    printf("Running shipping calculator branch tests...\n");
    test_all_branches();
    printf("All branch tests passed!\n");
    return 0;
}
```

## Phase 5: Coverage Reporting and Tracking

### Generate Comprehensive Reports

```bash
# Generate coverage with all formats
make coverage

# Generate text summary
lcov --summary coverage/coverage.info

# Generate detailed function report
lcov --list coverage/coverage.info

# Reports generated:
# - coverage/coverage.info (LCOV format)
# - coverage/html/index.html (browsable HTML)
# - coverage/html/index-sort-f.html (sorted by filename)
# - coverage/html/index-sort-l.html (sorted by line coverage)
```

### Coverage Badge

```bash
# Extract coverage percentage
COVERAGE=$(lcov --summary coverage/coverage.info 2>&1 | \
    grep "lines" | awk '{print $2}' | sed 's/%//')

# Generate badge using shields.io
if [ $(echo "$COVERAGE >= 80" | bc) -eq 1 ]; then
    COLOR="brightgreen"
elif [ $(echo "$COVERAGE >= 60" | bc) -eq 1 ]; then
    COLOR="yellow"
else
    COLOR="red"
fi

curl -s "https://img.shields.io/badge/coverage-${COVERAGE}%25-${COLOR}" > coverage/badge.svg
```

### Track Coverage Over Time

```c
// scripts/track_coverage.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

typedef struct {
    char date[32];
    float coverage;
} CoverageRecord;

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <coverage_percentage>\n", argv[0]);
        return 1;
    }

    float coverage = atof(argv[1]);

    // Read existing history
    FILE *fp = fopen("coverage-history.txt", "a+");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open coverage-history.txt\n");
        return 1;
    }

    // Get current timestamp
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    char timestamp[32];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", t);

    // Append record
    fprintf(fp, "%s,%.2f\n", timestamp, coverage);
    fclose(fp);

    printf("Coverage recorded: %.2f%% at %s\n", coverage, timestamp);

    return 0;
}
```

## Phase 6: Coverage in CI/CD

### GitHub Actions Coverage Integration

```yaml
# .github/workflows/coverage.yml
name: Coverage

on: [push, pull_request]

jobs:
  coverage:
    runs-on: ubuntu-latest

    steps:

      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y gcc lcov

      - name: Build with coverage
        run: |
          make clean
          make coverage

      - name: Check coverage threshold
        run: |
          COVERAGE=$(lcov --summary coverage/coverage.info 2>&1 | \
            grep "lines" | awk '{print $2}' | sed 's/%//')
          echo "Line coverage: ${COVERAGE}%"
          if (( $(echo "$COVERAGE < 80.0" | bc -l) )); then
            echo "✗ Coverage ${COVERAGE}% is below threshold 80%"
            exit 1
          else
            echo "✓ Coverage ${COVERAGE}% meets threshold 80%"
          fi

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage.info
          fail_ci_if_error: true

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: coverage/html/
```

## Output Format

Please provide a comprehensive coverage analysis with the following structure:

### Coverage Summary

- **Overall Coverage**: [percentage]

- **Line Coverage**: [percentage]

- **Function Coverage**: [percentage]

- **Branch Coverage**: [percentage]

### Coverage by File
| File | Lines | Functions | Branches | Priority |
|------|-------|-----------|----------|----------|
| src/service.c | 67% | 71% | 56% | Critical |
| src/auth.c | 78% | 86% | 70% | High |
| src/util.c | 93% | 90% | 88% | Low |

### Critical Coverage Gaps
1. **src/service.c** (67% line coverage)

   - **Missing**: Error handling paths

   - **Priority**: Critical - core business logic

   - **Action**: Add error scenario tests

2. **src/auth.c** (78% line coverage)

   - **Missing**: Edge cases in authentication

   - **Priority**: High - security-critical

   - **Action**: Add boundary condition tests

### Coverage Improvement Plan
**Sprint 1** (Target: 75% → 80%):

- [ ] Add error handling tests

- [ ] Cover authentication edge cases

- [ ] Test error code paths

**Sprint 2** (Target: 80% → 85%):

- [ ] Add branch coverage tests

- [ ] Test input validation

- [ ] Cover all switch cases

**Sprint 3** (Target: 85% → 90%):

- [ ] Add stress tests

- [ ] Cover memory allocation failures

- [ ] Test all error codes

### Coverage Reports Generated

- **LCOV Info**: `coverage/coverage.info`

- **HTML Report**: `coverage/html/index.html`

- **Badge**: `coverage/badge.svg`

### Coverage Thresholds

- **Minimum Overall**: 80%

- **Critical Modules**: 90%

- **New Code**: 100%

- **CI/CD Gate**: Fail if <80%

### Best Practices Implemented

- [ ] Coverage measured on every test run

- [ ] HTML reports for detailed analysis

- [ ] Coverage tracked over time

- [ ] Regression prevention in CI/CD

- [ ] Critical paths prioritized

- [ ] Team coverage goals established

### Next Steps

- [ ] Fix identified coverage gaps

- [ ] Set up coverage dashboard

- [ ] Schedule coverage review meetings

- [ ] Document coverage standards

- [ ] Integrate coverage diff in PRs

- [ ] Track coverage trends monthly

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

1. **Complete coverage configuration** (Makefile or CMakeLists.txt)

2. **Current coverage analysis** with gaps identified

3. **Prioritized improvement plan** with specific actions

4. **Test implementations** to fill critical gaps

5. **Coverage reporting infrastructure** (LCOV, HTML)

6. **CI/CD integration** with coverage gates

7. **Coverage tracking utilities** for trends

8. **Coverage diff tools** for PR reviews

9. **Team documentation** on coverage standards
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
