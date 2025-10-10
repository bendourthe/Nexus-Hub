# C Test Maintenance & CI/CD Integration

## Objective
Establish comprehensive test automation infrastructure, integrate tests into CI/CD pipelines, implement quality gates, manage test maintenance, handle flaky tests, optimize test execution, and ensure sustainable testing practices for C projects using Make/CMake.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── maintenance_cicd/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:

- Create `tests/{phase}/` directory in repository root if it doesn't exist

- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:

- `test_files/` - Actual test implementation files

- `test_data/` - Test fixtures, mock data, sample inputs

- `test_reports/` - Test execution reports, coverage reports, performance results

- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### CI/CD Configuration
- [ ] GitHub Actions/GitLab CI pipeline configured
- [ ] Test stages defined (unit, integration, memory)
- [ ] Parallel execution enabled
- [ ] Test result reporting set up
- [ ] Artifact storage configured

### Quality Gates
- [ ] Code coverage threshold enforced (80%+)
- [ ] Test pass rate requirement set (100%)
- [ ] Memory leak detection enabled
- [ ] Static analysis integrated
- [ ] Deployment gates configured

### Test Maintenance
- [ ] Flaky test detection implemented
- [ ] Test execution time monitoring enabled
- [ ] Obsolete test cleanup process established
- [ ] Test documentation maintained
- [ ] Test data management automated

### Pre-commit Hooks
- [ ] Code formatting checks (clang-format)
- [ ] Linting (cppcheck)
- [ ] Static analysis (clang-tidy, scan-build)
- [ ] Fast test subset execution
- [ ] Commit hooks configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Test Maintenance & CI/CD Implementation

Please implement comprehensive test automation and maintenance infrastructure for this C project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.



## Phase 1: CI/CD Pipeline Configuration

### GitHub Actions Setup

**Create `.github/workflows/tests.yml`**:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  CC: gcc
  CXX: g++

jobs:
  lint:
    name: Lint and Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install tools
        run: |
          sudo apt-get update
          sudo apt-get install -y clang-format clang-tidy cppcheck

      - name: Check formatting
        run: |
          find src tests -name '*.c' -o -name '*.h' | xargs clang-format -n -Werror

      - name: Run cppcheck
        run: |
          cppcheck --enable=all --error-exitcode=1 --suppress=missingIncludeSystem src/

      - name: Run clang-tidy
        run: |
          find src -name '*.c' | xargs clang-tidy -checks='*' --warnings-as-errors='*'

  unit-tests:
    name: Unit Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        compiler: [gcc, clang]

    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies (Ubuntu)
        if: matrix.os == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential cmake gcovr lcov valgrind

      - name: Install dependencies (macOS)
        if: matrix.os == 'macos-latest'
        run: |
          brew install cmake gcovr lcov

      - name: Install dependencies (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          choco install cmake

      - name: Configure with CMake
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON -DENABLE_TESTING=ON

      - name: Build
        run: |
          cmake --build build --config Debug

      - name: Run unit tests
        run: |
          cd build
          ctest --output-on-failure --verbose -R "^test_"

      - name: Generate coverage report
        if: matrix.os == 'ubuntu-latest'
        run: |
          cd build
          gcovr -r .. --xml -o coverage.xml

      - name: Upload coverage to Codecov
        if: matrix.os == 'ubuntu-latest'
        uses: codecov/codecov-action@v3
        with:
          files: ./build/coverage.xml
          flags: unit-tests
          name: codecov-${{ matrix.os }}-${{ matrix.compiler }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.compiler }}
          path: |
            build/Testing/
            build/coverage.xml

  memory-tests:
    name: Memory Leak Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
      - uses: actions/checkout@v3

      - name: Install Valgrind
        run: |
          sudo apt-get update
          sudo apt-get install -y valgrind cmake

      - name: Configure with CMake
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_TESTING=ON

      - name: Build
        run: |
          cmake --build build --config Debug

      - name: Run tests with Valgrind
        run: |
          cd build
          ctest --output-on-failure --verbose -T memcheck

      - name: Check for memory leaks
        run: |
          if grep -q "definitely lost:" build/Testing/Temporary/MemoryChecker.*.log; then
            echo "Memory leaks detected!"
            cat build/Testing/Temporary/MemoryChecker.*.log
            exit 1
          fi

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: unit-tests

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential cmake libpq-dev

      - name: Configure with CMake
        run: |
          cmake -B build -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTING=ON

      - name: Build
        run: |
          cmake --build build --config Release

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
        run: |
          cd build
          ctest --output-on-failure --verbose -R "^integration_"

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install scan-build
        run: |
          sudo apt-get update
          sudo apt-get install -y clang clang-tools cmake

      - name: Run scan-build
        run: |
          scan-build cmake -B build -DCMAKE_BUILD_TYPE=Debug
          scan-build -o scan-results cmake --build build

      - name: Upload scan results
        uses: actions/upload-artifact@v3
        with:
          name: security-scan-results
          path: scan-results/

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, memory-tests, integration-tests, security]
    steps:
      - name: Quality gate passed
        run: echo "All quality checks passed!"
```

### GitLab CI Configuration

**Create `.gitlab-ci.yml`**:

```yaml
stages:
  - lint
  - test
  - quality
  - deploy

variables:
  CC: gcc
  CXX: g++

cache:
  paths:
    - build/

before_script:
  - apt-get update -qq
  - apt-get install -y -qq build-essential cmake gcovr valgrind

lint:
  stage: lint
  image: ubuntu:22.04
  script:
    - apt-get install -y -qq clang-format cppcheck
    - find src tests -name '*.c' -o -name '*.h' | xargs clang-format -n -Werror
    - cppcheck --enable=all --error-exitcode=1 --suppress=missingIncludeSystem src/

unit-tests:
  stage: test
  image: ubuntu:22.04
  script:
    - cmake -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON -DENABLE_TESTING=ON
    - cmake --build build
    - cd build && ctest --output-on-failure -R "^test_"
    - gcovr -r .. --xml -o coverage.xml
  coverage: '/lines: \d+\.\d+%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: build/coverage.xml
    paths:
      - build/coverage.xml
      - build/Testing/

memory-tests:
  stage: test
  image: ubuntu:22.04
  script:
    - cmake -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_TESTING=ON
    - cmake --build build
    - cd build && ctest --output-on-failure -T memcheck
  artifacts:
    paths:
      - build/Testing/Temporary/MemoryChecker.*.log

quality-gate:
  stage: quality
  image: ubuntu:22.04
  script:
    - apt-get install -y -qq python3-lxml
    - python3 scripts/check_coverage.py build/coverage.xml 80
  needs:
    - unit-tests
```

## Phase 2: Quality Gates Configuration

### CMake Configuration

**Create `CMakeLists.txt`**:

```cmake
cmake_minimum_required(VERSION 3.14)
project(MyProject C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Options
option(ENABLE_TESTING "Enable testing" ON)
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)
option(ENABLE_SANITIZERS "Enable sanitizers" OFF)

# Compiler flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Werror -pedantic")

if(ENABLE_COVERAGE)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --coverage -fprofile-arcs -ftest-coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
endif()

if(ENABLE_SANITIZERS)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fsanitize=address -fsanitize=undefined")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=address -fsanitize=undefined")
endif()

# Source files
add_subdirectory(src)

# Testing
if(ENABLE_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()
```

**Create `tests/CMakeLists.txt`**:

```cmake
# Test framework (using Unity or custom framework)
add_library(test_framework STATIC
    framework/unity.c
    framework/test_runner.c
)

target_include_directories(test_framework PUBLIC
    ${CMAKE_SOURCE_DIR}/src
    framework
)

# Helper function to add tests
function(add_unit_test test_name)
    add_executable(${test_name} ${ARGN})
    target_link_libraries(${test_name} PRIVATE test_framework)
    add_test(NAME ${test_name} COMMAND ${test_name})

    # Add valgrind memcheck
    add_test(NAME ${test_name}_memcheck
        COMMAND valgrind --leak-check=full --error-exitcode=1 ./${test_name}
    )
    set_tests_properties(${test_name}_memcheck PROPERTIES
        LABELS "memcheck"
    )
endfunction()

# Add tests
add_unit_test(test_math test_math.c)
add_unit_test(test_string test_string.c)
add_unit_test(integration_database integration_database.c)
```

### Coverage Script

**Create `scripts/check_coverage.py`**:

```python
#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET

def check_coverage(coverage_file, threshold):
    """Check if coverage meets threshold."""
    tree = ET.parse(coverage_file)
    root = tree.getroot()

    # Parse Cobertura format
    line_rate = float(root.attrib['line-rate'])
    branch_rate = float(root.attrib['branch-rate'])

    line_coverage = line_rate * 100
    branch_coverage = branch_rate * 100

    print(f"Line Coverage: {line_coverage:.2f}%")
    print(f"Branch Coverage: {branch_coverage:.2f}%")

    if line_coverage < threshold:
        print(f"❌ Line coverage {line_coverage:.2f}% is below threshold {threshold}%")
        sys.exit(1)

    if branch_coverage < threshold:
        print(f"❌ Branch coverage {branch_coverage:.2f}% is below threshold {threshold}%")
        sys.exit(1)

    print(f"✅ Coverage meets threshold {threshold}%")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: check_coverage.py <coverage.xml> <threshold>")
        sys.exit(1)

    coverage_file = sys.argv[1]
    threshold = float(sys.argv[2])

    check_coverage(coverage_file, threshold)
```

### Test Framework

**Create `tests/framework/test_runner.h`**:

```c
#ifndef TEST_RUNNER_H
#define TEST_RUNNER_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

typedef struct {
    const char *name;
    void (*test_func)(void);
} TestCase;

typedef struct {
    int total;
    int passed;
    int failed;
    double duration;
} TestResults;

extern TestResults g_test_results;

#define TEST(name) void test_##name(void)
#define RUN_TEST(name) run_test(#name, test_##name)

void test_setup(void);
void test_teardown(void);
void run_test(const char *name, void (*test_func)(void));
void print_results(void);

// Assertions
#define ASSERT_TRUE(condition) \
    do { \
        if (!(condition)) { \
            fprintf(stderr, "ASSERTION FAILED: %s:%d: %s\n", \
                    __FILE__, __LINE__, #condition); \
            exit(1); \
        } \
    } while(0)

#define ASSERT_FALSE(condition) ASSERT_TRUE(!(condition))

#define ASSERT_EQUAL(expected, actual) \
    do { \
        if ((expected) != (actual)) { \
            fprintf(stderr, "ASSERTION FAILED: %s:%d: Expected %d, got %d\n", \
                    __FILE__, __LINE__, (int)(expected), (int)(actual)); \
            exit(1); \
        } \
    } while(0)

#define ASSERT_STR_EQUAL(expected, actual) \
    do { \
        if (strcmp((expected), (actual)) != 0) { \
            fprintf(stderr, "ASSERTION FAILED: %s:%d: Expected '%s', got '%s'\n", \
                    __FILE__, __LINE__, (expected), (actual)); \
            exit(1); \
        } \
    } while(0)

#endif /* TEST_RUNNER_H */
```

**Create `tests/framework/test_runner.c`**:

```c
#include "test_runner.h"

TestResults g_test_results = {0, 0, 0, 0.0};

void test_setup(void) {
    // Override in tests if needed
}

void test_teardown(void) {
    // Override in tests if needed
}

void run_test(const char *name, void (*test_func)(void)) {
    clock_t start = clock();

    printf("Running: %s... ", name);
    fflush(stdout);

    test_setup();

    int result = 0;
    if (fork() == 0) {
        // Child process runs the test
        test_func();
        exit(0);
    } else {
        // Parent process waits
        int status;
        wait(&status);
        result = WEXITSTATUS(status);
    }

    test_teardown();

    clock_t end = clock();
    double duration = (double)(end - start) / CLOCKS_PER_SEC;

    g_test_results.total++;

    if (result == 0) {
        printf("✅ PASSED (%.3fs)\n", duration);
        g_test_results.passed++;
    } else {
        printf("❌ FAILED (%.3fs)\n", duration);
        g_test_results.failed++;
    }

    g_test_results.duration += duration;
}

void print_results(void) {
    printf("\n");
    printf("============================================================\n");
    printf("Test Results\n");
    printf("============================================================\n");
    printf("Total:    %d\n", g_test_results.total);
    printf("Passed:   %d\n", g_test_results.passed);
    printf("Failed:   %d\n", g_test_results.failed);
    printf("Duration: %.3fs\n", g_test_results.duration);
    printf("============================================================\n");

    double pass_rate = g_test_results.total > 0
        ? (double)g_test_results.passed / g_test_results.total * 100
        : 0;

    printf("Pass Rate: %.1f%%\n", pass_rate);

    if (pass_rate < 100) {
        printf("⚠️  WARNING: Not all tests passed\n");
    } else {
        printf("✅ Quality Gate Passed: All tests passed\n");
    }

    if (g_test_results.failed > 0) {
        printf("\n❌ Quality Gate Failed: Some tests did not pass\n");
        exit(1);
    }
}
```

## Phase 3: Pre-commit Hooks

### Install Pre-commit Framework

```bash
pip install pre-commit
```

**Create `.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: local
    hooks:
      - id: clang-format
        name: Format C code
        entry: clang-format -i
        language: system
        files: \.(c|h)$
        pass_filenames: true

      - id: cppcheck
        name: Run cppcheck
        entry: cppcheck
        language: system
        files: \.c$
        args: ['--enable=all', '--error-exitcode=1', '--suppress=missingIncludeSystem']
        pass_filenames: true

      - id: cmake-build
        name: Build with CMake
        entry: bash -c 'cmake -B build && cmake --build build'
        language: system
        pass_filenames: false
        always_run: true

      - id: fast-tests
        name: Run fast tests
        entry: bash -c 'cd build && ctest -L fast --output-on-failure'
        language: system
        pass_filenames: false
        always_run: true
```

### clang-format Configuration

**Create `.clang-format`**:

```yaml
---
BasedOnStyle: LLVM
IndentWidth: 4
ColumnLimit: 100
UseTab: Never
BreakBeforeBraces: Linux
AllowShortIfStatementsOnASingleLine: false
IndentCaseLabels: false
AlignConsecutiveDeclarations: true
AlignConsecutiveAssignments: true
PointerAlignment: Right
```

### Install Hooks

```bash
# Install the git hook scripts
pre-commit install

# Run against all files
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## Phase 4: Test Parallelization

### CTest Parallel Execution

```bash
# Run tests in parallel
ctest -j$(nproc)

# Or specify number of jobs
ctest -j4
```

### Configure in CMakeLists.txt

```cmake
# Enable parallel testing
set(CTEST_PARALLEL_LEVEL 4)

# Set test properties
set_tests_properties(test_math PROPERTIES
    LABELS "fast"
    TIMEOUT 5
)

set_tests_properties(integration_database PROPERTIES
    LABELS "slow;integration"
    TIMEOUT 30
)
```

### Handle Non-Thread-Safe Tests

```cmake
# Mark tests that must run serially
set_tests_properties(test_database_migration PROPERTIES
    RUN_SERIAL TRUE
)

# Or use resource locks
set_tests_properties(test_database_1 test_database_2 PROPERTIES
    RESOURCE_LOCK database
)
```

## Phase 5: Flaky Test Management

### Retry Mechanism

```c
// tests/framework/retry.h
#ifndef TEST_RETRY_H
#define TEST_RETRY_H

#include <unistd.h>

#define MAX_RETRIES 3
#define RETRY_DELAY_SEC 1

#define TEST_WITH_RETRY(test_func) \
    do { \
        int _retry_count = 0; \
        int _test_passed = 0; \
        \
        while (_retry_count < MAX_RETRIES && !_test_passed) { \
            if (fork() == 0) { \
                test_func(); \
                exit(0); \
            } else { \
                int status; \
                wait(&status); \
                if (WEXITSTATUS(status) == 0) { \
                    _test_passed = 1; \
                } else { \
                    _retry_count++; \
                    if (_retry_count < MAX_RETRIES) { \
                        printf("Test failed (attempt %d/%d), retrying...\n", \
                               _retry_count, MAX_RETRIES); \
                        sleep(RETRY_DELAY_SEC); \
                    } \
                } \
            } \
        } \
        \
        if (!_test_passed) { \
            fprintf(stderr, "Test failed after %d attempts\n", MAX_RETRIES); \
            exit(1); \
        } \
    } while(0)

#endif /* TEST_RETRY_H */
```

### Track Flaky Tests

```c
// tests/framework/flaky_tracker.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define FLAKY_LOG_FILE "tests/flaky-tests.log"

typedef struct {
    char name[256];
    int count;
    time_t last_seen;
} FlakyTest;

void record_flaky_test(const char *test_name) {
    FILE *fp = fopen(FLAKY_LOG_FILE, "a");
    if (fp == NULL) {
        return;
    }

    time_t now = time(NULL);
    fprintf(fp, "%ld,%s\n", now, test_name);
    fclose(fp);
}

void print_flaky_report(void) {
    FILE *fp = fopen(FLAKY_LOG_FILE, "r");
    if (fp == NULL) {
        return;
    }

    printf("\n⚠️  Flaky Tests Detected:\n");

    char line[512];
    while (fgets(line, sizeof(line), fp) != NULL) {
        char *comma = strchr(line, ',');
        if (comma != NULL) {
            *comma = '\0';
            time_t timestamp = atol(line);
            char *test_name = comma + 1;

            // Remove newline
            char *newline = strchr(test_name, '\n');
            if (newline != NULL) {
                *newline = '\0';
            }

            char time_str[64];
            strftime(time_str, sizeof(time_str), "%Y-%m-%d %H:%M:%S",
                     localtime(&timestamp));

            printf("  %s: %s\n", test_name, time_str);
        }
    }

    fclose(fp);
}
```

## Phase 6: Test Maintenance Practices

### Monitor Test Execution Time

```c
// tests/framework/slow_test_detector.h
#ifndef SLOW_TEST_DETECTOR_H
#define SLOW_TEST_DETECTOR_H

#include <stdio.h>
#include <time.h>

#define SLOW_TEST_THRESHOLD_SEC 1.0

typedef struct {
    char name[256];
    double duration;
} SlowTest;

extern SlowTest g_slow_tests[100];
extern int g_slow_test_count;

void check_slow_test(const char *name, clock_t start, clock_t end);
void print_slow_test_report(void);

#endif /* SLOW_TEST_DETECTOR_H */
```

```c
// tests/framework/slow_test_detector.c
#include "slow_test_detector.h"
#include <string.h>

SlowTest g_slow_tests[100];
int g_slow_test_count = 0;

void check_slow_test(const char *name, clock_t start, clock_t end) {
    double duration = (double)(end - start) / CLOCKS_PER_SEC;

    if (duration > SLOW_TEST_THRESHOLD_SEC) {
        if (g_slow_test_count < 100) {
            strncpy(g_slow_tests[g_slow_test_count].name, name, 255);
            g_slow_tests[g_slow_test_count].duration = duration;
            g_slow_test_count++;
        }

        printf("\n⚠️  Slow test: %s (%.2fs)\n", name, duration);
    }
}

void print_slow_test_report(void) {
    if (g_slow_test_count == 0) {
        return;
    }

    printf("\n============================================================\n");
    printf("Slow Tests Detected:\n");

    // Sort by duration (bubble sort for simplicity)
    for (int i = 0; i < g_slow_test_count - 1; i++) {
        for (int j = 0; j < g_slow_test_count - i - 1; j++) {
            if (g_slow_tests[j].duration < g_slow_tests[j + 1].duration) {
                SlowTest temp = g_slow_tests[j];
                g_slow_tests[j] = g_slow_tests[j + 1];
                g_slow_tests[j + 1] = temp;
            }
        }
    }

    int limit = g_slow_test_count < 10 ? g_slow_test_count : 10;
    for (int i = 0; i < limit; i++) {
        printf("  %.2fs: %s\n", g_slow_tests[i].duration, g_slow_tests[i].name);
    }

    printf("============================================================\n");
}
```

### Document Test Purpose

```c
/*
 * User Authentication Test Suite
 *
 * Purpose:
 *   Validate user login, logout, and session management functionality.
 *
 * Coverage:
 *   - Valid credential login
 *   - Invalid credential handling
 *   - Session token generation and validation
 *   - Password reset process
 *
 * Maintenance Notes:
 *   - Update test_valid_login() if authentication logic changes
 *   - Tests use in-memory database for speed
 *   - External API calls are mocked
 *
 * Dependencies:
 *   - auth.h
 *   - user.h
 *   - jwt.h
 *
 * Last Review: 2024-01-15
 * Reviewed By: alice@example.com
 */

#include "test_runner.h"
#include "auth.h"

TEST(valid_login) {
    // Test implementation
}
```

## Phase 7: Test Result Reporting

### JUnit XML Report

**Create `scripts/ctest_to_junit.py`**:

```python
#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import sys
import os

def convert_ctest_to_junit(ctest_xml, junit_xml):
    """Convert CTest XML to JUnit format."""
    tree = ET.parse(ctest_xml)
    root = tree.getroot()

    # Create JUnit root
    testsuite = ET.Element('testsuite')
    testsuite.set('name', 'CTest')

    for test in root.findall('.//Test'):
        testcase = ET.SubElement(testsuite, 'testcase')
        testcase.set('name', test.find('Name').text)
        testcase.set('time', test.find('Results/NamedMeasurement[@name="Execution Time"]/Value').text)

        status = test.get('Status')
        if status == 'failed':
            failure = ET.SubElement(testcase, 'failure')
            failure.text = test.find('Results/Measurement/Value').text

    # Write JUnit XML
    tree = ET.ElementTree(testsuite)
    tree.write(junit_xml, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: ctest_to_junit.py <ctest.xml> <junit.xml>")
        sys.exit(1)

    convert_ctest_to_junit(sys.argv[1], sys.argv[2])
```

### Generate Reports

```bash
# Run tests with CTest
cd build
ctest --output-junit test-results.xml

# Generate coverage report
gcovr -r .. --html --html-details -o coverage.html

# Generate lcov report
lcov --capture --directory . --output-file coverage.info
genhtml coverage.info --output-directory coverage-html
```

## Output Format

Please provide a comprehensive CI/CD and maintenance implementation with the following structure:

### CI/CD Configuration Summary
- **Platform**: [GitHub Actions/GitLab CI/Jenkins]
- **Pipeline Stages**: [list stages]
- **Parallel Execution**: [enabled/disabled, worker count]
- **Test Types Automated**: [unit, integration, memory]
- **Quality Gates**: [list gates]

### Quality Gate Configuration
| Gate | Threshold | Current | Status |
|------|-----------|---------|--------|
| Code Coverage | 80% | [value] | ✅/❌ |
| Test Pass Rate | 100% | [value] | ✅/❌ |
| Memory Leaks | 0 | [value] | ✅/❌ |

### Pre-commit Hooks Configured
- [ ] Code formatting (clang-format)
- [ ] Static analysis (cppcheck, clang-tidy)
- [ ] Build verification
- [ ] Fast test execution
- [ ] Coverage check

### Test Maintenance Status
**Slow Tests Identified**:
| Test | Duration | Recommendation |
|------|----------|----------------|
| [test_name] | [time] | [optimization] |

**Flaky Tests**:
| Test | Failure Rate | Action |
|------|--------------|--------|
| [test_name] | [rate] | [fix planned] |

### Test Execution Metrics
- **Total Tests**: [count]
- **Average Execution Time**: [duration]
- **Parallel Workers**: [count]
- **Tests per Second**: [rate]
- **Coverage**: [percentage]

### CI/CD Pipeline Visualization
```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌────────┐
│  Lint   │────▶│   Unit   │────▶│Integration │────▶│ Deploy │
└─────────┘     │  Tests   │     │   Tests    │     └────────┘
                └──────────┘     └────────────┘
                     │                 │
                     ▼                 ▼
                ┌─────────┐       ┌─────────┐
                │Coverage │       │ Memory  │
                │  Gate   │       │  Check  │
                └─────────┘       └─────────┘
```

### Best Practices Implemented
- [ ] All tests automated in CI/CD
- [ ] Quality gates prevent regressions
- [ ] Pre-commit hooks catch issues early
- [ ] Parallel execution for speed
- [ ] Memory leak detection enabled
- [ ] Test maintenance schedule established

### Next Steps
- [ ] Monitor and optimize slow tests
- [ ] Fix identified flaky tests
- [ ] Review and update obsolete tests
- [ ] Enhance test documentation
- [ ] Set up test result dashboard
- [ ] Schedule regular test maintenance reviews

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

1. **Complete CI/CD pipeline configuration** (GitHub Actions or GitLab CI)
2. **Quality gate implementation** with thresholds (CMake, gcovr)
3. **Pre-commit hook configuration** with all checks
4. **Test parallelization setup** for faster execution (CTest)
5. **Flaky test detection and tracking** system
6. **Test maintenance procedures** and documentation
7. **Test reporting infrastructure** with dashboards
8. **Execution metrics and monitoring** setup
