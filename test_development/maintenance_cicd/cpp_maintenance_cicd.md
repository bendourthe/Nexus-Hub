# C++ Test Maintenance & CI/CD Integration

## Objective
Establish comprehensive test automation infrastructure, integrate tests into CI/CD pipelines, implement quality gates, manage test maintenance, handle flaky tests, optimize test execution, and ensure sustainable testing practices for C++ projects using CMake and modern testing frameworks.

## Implementation Checklist

### CI/CD Configuration
- [ ] GitHub Actions/GitLab CI pipeline configured
- [ ] Test stages defined (unit, integration, performance)
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
- [ ] Linting (clang-tidy, cpplint)
- [ ] Static analysis (cppcheck)
- [ ] Fast test subset execution
- [ ] Commit hooks configured

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Test Maintenance & CI/CD Implementation

Please implement comprehensive test automation and maintenance infrastructure for this C++ project following this protocol:

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
  BUILD_TYPE: Release

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
          find src tests -name '*.cpp' -o -name '*.h' -o -name '*.hpp' | \
            xargs clang-format -n -Werror

      - name: Run cppcheck
        run: |
          cppcheck --enable=all --error-exitcode=1 \
            --suppress=missingIncludeSystem \
            --std=c++17 src/

      - name: Run clang-tidy
        run: |
          cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
          find src -name '*.cpp' | xargs clang-tidy -p build

  unit-tests:
    name: Unit Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        compiler: [gcc, clang]
        build_type: [Debug, Release]
        exclude:
          - os: windows-latest
            compiler: clang

    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies (Ubuntu)
        if: matrix.os == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential cmake ninja-build \
            libgtest-dev libgmock-dev gcovr lcov valgrind

      - name: Install dependencies (macOS)
        if: matrix.os == 'macos-latest'
        run: |
          brew install cmake ninja googletest gcovr lcov

      - name: Install dependencies (Windows)
        if: matrix.os == 'windows-latest'
        run: |
          choco install cmake ninja

      - name: Configure CMake
        run: |
          cmake -B build -G Ninja \
            -DCMAKE_BUILD_TYPE=${{ matrix.build_type }} \
            -DENABLE_COVERAGE=ON \
            -DENABLE_TESTING=ON \
            -DBUILD_TESTS=ON

      - name: Build
        run: cmake --build build --config ${{ matrix.build_type }}

      - name: Run tests
        working-directory: build
        run: ctest --output-on-failure --verbose -C ${{ matrix.build_type }}

      - name: Generate coverage report
        if: matrix.os == 'ubuntu-latest' && matrix.build_type == 'Debug'
        working-directory: build
        run: |
          gcovr -r .. --xml -o coverage.xml

      - name: Upload coverage to Codecov
        if: matrix.os == 'ubuntu-latest' && matrix.build_type == 'Debug'
        uses: codecov/codecov-action@v3
        with:
          files: ./build/coverage.xml
          flags: unit-tests
          name: codecov-${{ matrix.os }}-${{ matrix.compiler }}

      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results-${{ matrix.os }}-${{ matrix.compiler }}-${{ matrix.build_type }}
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
          sudo apt-get install -y valgrind cmake ninja-build libgtest-dev

      - name: Configure CMake
        run: |
          cmake -B build -G Ninja \
            -DCMAKE_BUILD_TYPE=Debug \
            -DENABLE_TESTING=ON

      - name: Build
        run: cmake --build build

      - name: Run tests with Valgrind
        working-directory: build
        run: ctest --output-on-failure -T memcheck

      - name: Check for memory leaks
        working-directory: build
        run: |
          if grep -q "definitely lost:" Testing/Temporary/MemoryChecker.*.log; then
            echo "Memory leaks detected!"
            cat Testing/Temporary/MemoryChecker.*.log
            exit 1
          fi

  sanitizer-tests:
    name: Sanitizer Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        sanitizer: [address, undefined, thread]

    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y build-essential cmake ninja-build libgtest-dev

      - name: Configure with sanitizer
        run: |
          cmake -B build -G Ninja \
            -DCMAKE_BUILD_TYPE=Debug \
            -DENABLE_TESTING=ON \
            -DSANITIZER=${{ matrix.sanitizer }}

      - name: Build
        run: cmake --build build

      - name: Run tests
        working-directory: build
        run: ctest --output-on-failure --verbose

  benchmark:
    name: Benchmark Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y cmake ninja-build libbenchmark-dev

      - name: Configure CMake
        run: |
          cmake -B build -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DBUILD_BENCHMARKS=ON

      - name: Build
        run: cmake --build build

      - name: Run benchmarks
        working-directory: build
        run: ctest -L benchmark --output-on-failure

      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: build/benchmark-results.json

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

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Install dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y cmake ninja-build libgtest-dev libpq-dev

      - name: Configure CMake
        run: |
          cmake -B build -G Ninja \
            -DCMAKE_BUILD_TYPE=Release \
            -DENABLE_TESTING=ON

      - name: Build
        run: cmake --build build

      - name: Run integration tests
        working-directory: build
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379
        run: ctest -L integration --output-on-failure

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install scan-build
        run: |
          sudo apt-get update
          sudo apt-get install -y clang clang-tools cmake ninja-build

      - name: Run scan-build
        run: |
          scan-build cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
          scan-build -o scan-results cmake --build build

      - name: Upload scan results
        uses: actions/upload-artifact@v3
        with:
          name: security-scan-results
          path: scan-results/

  quality-gate:
    name: Quality Gate
    runs-on: ubuntu-latest
    needs: [lint, unit-tests, memory-tests, sanitizer-tests, integration-tests, security]
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
  BUILD_TYPE: Release

cache:
  paths:
    - build/

before_script:
  - apt-get update -qq
  - apt-get install -y -qq build-essential cmake ninja-build libgtest-dev gcovr

lint:
  stage: lint
  image: ubuntu:22.04
  script:
    - apt-get install -y -qq clang-format cppcheck
    - find src tests -name '*.cpp' -o -name '*.h' -o -name '*.hpp' | xargs clang-format -n -Werror
    - cppcheck --enable=all --error-exitcode=1 --suppress=missingIncludeSystem --std=c++17 src/

unit-tests:
  stage: test
  image: ubuntu:22.04
  script:
    - cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON -DENABLE_TESTING=ON
    - cmake --build build
    - cd build && ctest --output-on-failure
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
    - apt-get install -y -qq valgrind
    - cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug -DENABLE_TESTING=ON
    - cmake --build build
    - cd build && ctest -T memcheck --output-on-failure
  artifacts:
    paths:
      - build/Testing/Temporary/MemoryChecker.*.log

benchmark:
  stage: test
  image: ubuntu:22.04
  script:
    - apt-get install -y -qq libbenchmark-dev
    - cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_BENCHMARKS=ON
    - cmake --build build
    - cd build && ctest -L benchmark --output-on-failure
  artifacts:
    paths:
      - build/benchmark-results.json

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
project(MyProject CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Options
option(ENABLE_TESTING "Enable testing" ON)
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)
option(BUILD_BENCHMARKS "Build benchmark tests" OFF)
option(SANITIZER "Build with sanitizer (address, undefined, thread)" "")

# Compiler flags
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra -Werror -pedantic")

if(ENABLE_COVERAGE)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --coverage -fprofile-arcs -ftest-coverage")
    set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")
endif()

if(SANITIZER)
    if(SANITIZER STREQUAL "address")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=address -fno-omit-frame-pointer")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=address")
    elseif(SANITIZER STREQUAL "undefined")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=undefined")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=undefined")
    elseif(SANITIZER STREQUAL "thread")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fsanitize=thread")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fsanitize=thread")
    endif()
endif()

# Source files
add_subdirectory(src)

# Testing
if(ENABLE_TESTING)
    enable_testing()
    find_package(GTest REQUIRED)
    add_subdirectory(tests)
endif()

# Benchmarks
if(BUILD_BENCHMARKS)
    find_package(benchmark REQUIRED)
    add_subdirectory(benchmarks)
endif()
```

**Create `tests/CMakeLists.txt`**:

```cmake
include(GoogleTest)

# Helper function to add tests
function(add_unit_test test_name)
    add_executable(${test_name} ${ARGN})
    target_link_libraries(${test_name} PRIVATE
        GTest::gtest
        GTest::gtest_main
        GTest::gmock
        myproject_lib
    )

    # Discover tests
    gtest_discover_tests(${test_name}
        PROPERTIES
            LABELS "unit"
    )

    # Add valgrind memcheck
    add_test(NAME ${test_name}_memcheck
        COMMAND valgrind --leak-check=full --error-exitcode=1 ./${test_name}
    )
    set_tests_properties(${test_name}_memcheck PROPERTIES
        LABELS "memcheck"
    )
endfunction()

# Add tests
add_unit_test(math_test math_test.cpp)
add_unit_test(string_test string_test.cpp)

# Integration tests
add_executable(database_integration_test database_integration_test.cpp)
target_link_libraries(database_integration_test PRIVATE
    GTest::gtest
    GTest::gtest_main
    myproject_lib
)
gtest_discover_tests(database_integration_test
    PROPERTIES
        LABELS "integration"
)
```

### Test Framework Example

```cpp
// tests/math_test.cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "math_utils.h"

using namespace testing;

/**
 * Math Utilities Test Suite
 *
 * Purpose:
 *   Validate mathematical operations and utility functions.
 *
 * Coverage:
 *   - Basic arithmetic operations
 *   - Edge cases (overflow, underflow, division by zero)
 *   - Floating-point precision
 *   - Vector operations
 *
 * Maintenance Notes:
 *   - Update tests when adding new math functions
 *   - Check for numerical stability
 *   - Consider performance implications
 *
 * Last Review: 2024-01-15
 * Reviewed By: alice@example.com
 */

class MathTest : public Test {
protected:
    void SetUp() override {
        // Test setup
    }

    void TearDown() override {
        // Test cleanup
    }
};

TEST_F(MathTest, AdditionWorks) {
    EXPECT_EQ(add(2, 3), 5);
    EXPECT_EQ(add(-1, 1), 0);
}

TEST_F(MathTest, DivisionByZeroThrows) {
    EXPECT_THROW(divide(10, 0), std::invalid_argument);
}

// Parameterized test
class AdditionTest : public TestWithParam<std::tuple<int, int, int>> {};

TEST_P(AdditionTest, ParameterizedAddition) {
    auto [a, b, expected] = GetParam();
    EXPECT_EQ(add(a, b), expected);
}

INSTANTIATE_TEST_SUITE_P(
    MathTests,
    AdditionTest,
    Values(
        std::make_tuple(1, 2, 3),
        std::make_tuple(-1, 1, 0),
        std::make_tuple(0, 0, 0)
    )
);
```

### Performance Regression Gate

```cpp
// tests/benchmark/performance_gate.cpp
#include <benchmark/benchmark.h>
#include <fstream>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

constexpr char BASELINE_FILE[] = "tests/benchmark/baseline.json";
constexpr double REGRESSION_THRESHOLD = 0.10; // 10%

class PerformanceGate {
private:
    json benchmarks_;
    json baseline_;

    void loadBaseline() {
        std::ifstream file(BASELINE_FILE);
        if (file.good()) {
            file >> baseline_;
        }
    }

    void saveBaseline() {
        std::ofstream file(BASELINE_FILE);
        file << benchmarks_.dump(2);
    }

public:
    PerformanceGate() {
        loadBaseline();
    }

    void recordBenchmark(const std::string& name, double nsPerOp) {
        benchmarks_[name] = nsPerOp;
    }

    void checkRegressions() {
        if (baseline_.empty()) {
            saveBaseline();
            std::cout << "📊 Baseline performance metrics saved\n";
            return;
        }

        bool hasRegressions = false;

        for (auto& [name, current] : benchmarks_.items()) {
            if (baseline_.contains(name)) {
                double baseline = baseline_[name];
                double currentVal = current;
                double regression = (currentVal - baseline) / baseline;

                if (regression > REGRESSION_THRESHOLD) {
                    hasRegressions = true;
                    std::cout << "  " << name << ": "
                             << (regression * 100) << "% slower\n";
                    std::cout << "    Baseline: " << baseline << "ns, "
                             << "Current: " << currentVal << "ns\n";
                }
            }
        }

        if (hasRegressions) {
            throw std::runtime_error("❌ Performance Regression Detected");
        }

        std::cout << "✅ Performance Gate Passed: No regressions detected\n";
    }
};

// Benchmark example
static void BM_StringCompare(benchmark::State& state) {
    std::string s1 = "test string";
    std::string s2 = "test string";

    for (auto _ : state) {
        benchmark::DoNotOptimize(s1.compare(s2));
    }
}
BENCHMARK(BM_StringCompare);

BENCHMARK_MAIN();
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
        name: Format C++ code
        entry: clang-format -i
        language: system
        files: \.(cpp|hpp|h|cc)$
        pass_filenames: true

      - id: clang-tidy
        name: Run clang-tidy
        entry: bash -c 'clang-tidy -p build'
        language: system
        files: \.cpp$
        pass_filenames: true

      - id: cppcheck
        name: Run cppcheck
        entry: cppcheck
        language: system
        files: \.cpp$
        args: ['--enable=all', '--error-exitcode=1', '--suppress=missingIncludeSystem', '--std=c++17']
        pass_filenames: true

      - id: cmake-build
        name: Build with CMake
        entry: bash -c 'cmake -B build -G Ninja && cmake --build build'
        language: system
        pass_filenames: false
        always_run: true

      - id: fast-tests
        name: Run fast tests
        entry: bash -c 'cd build && ctest -L unit --output-on-failure'
        language: system
        pass_filenames: false
        always_run: true
```

### clang-format Configuration

**Create `.clang-format`**:

```yaml
---
Language: Cpp
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
PointerAlignment: Left
AccessModifierOffset: -4
NamespaceIndentation: None
BreakBeforeBraces: Attach
AllowShortIfStatementsOnASingleLine: Never
AllowShortFunctionsOnASingleLine: None
AlignConsecutiveDeclarations: true
AlignConsecutiveAssignments: true
```

### clang-tidy Configuration

**Create `.clang-tidy`**:

```yaml
---
Checks: '*,
        -fuchsia-*,
        -google-readability-todo,
        -llvm-header-guard'
WarningsAsErrors: '*'
HeaderFilterRegex: '.*'
FormatStyle: file
CheckOptions:
  - key: readability-identifier-naming.ClassCase
    value: CamelCase
  - key: readability-identifier-naming.FunctionCase
    value: camelCase
  - key: readability-identifier-naming.VariableCase
    value: camelCase
  - key: readability-identifier-naming.ConstantCase
    value: UPPER_CASE
```

## Phase 4: Test Parallelization

### CTest Parallel Execution

```bash
# Run tests in parallel
ctest -j$(nproc)

# Or in CMakeLists.txt
set(CTEST_PARALLEL_LEVEL 4)
```

### Google Test Parallelization

```cpp
// tests/parallel_test.cpp
#include <gtest/gtest.h>

// Tests run in parallel by default with ctest -j

TEST(ParallelTest, Test1) {
    // This runs in parallel with Test2
}

TEST(ParallelTest, Test2) {
    // This runs in parallel with Test1
}

// For non-thread-safe tests
class SerialTest : public ::testing::Test {};

TEST_F(SerialTest, DatabaseMigration) {
    // Mark as serial in CMakeLists.txt
}
```

### Configure Serial Tests

```cmake
# In CMakeLists.txt
set_tests_properties(database_migration_test PROPERTIES
    RUN_SERIAL TRUE
)

# Or use resource locks
set_tests_properties(
    database_test_1
    database_test_2
    PROPERTIES RESOURCE_LOCK database
)
```

## Phase 5: Flaky Test Management

### Retry Mechanism

```cpp
// tests/utils/retry_test.h
#ifndef RETRY_TEST_H
#define RETRY_TEST_H

#include <gtest/gtest.h>
#include <chrono>
#include <thread>

template<typename Func>
void retryTest(Func&& testFunc, int maxRetries = 3, int delayMs = 1000) {
    for (int attempt = 1; attempt <= maxRetries; ++attempt) {
        try {
            testFunc();
            return; // Success
        } catch (const std::exception& e) {
            if (attempt == maxRetries) {
                throw; // Final attempt failed
            }
            std::cout << "Test failed (attempt " << attempt << "/" << maxRetries
                     << "), retrying...\n";
            std::this_thread::sleep_for(std::chrono::milliseconds(delayMs));
        }
    }
}

// Usage macro
#define TEST_WITH_RETRY(test_suite, test_name) \
    TEST(test_suite, test_name) { \
        retryTest([]() {

#define END_RETRY_TEST \
        }, 3, 2000); \
    }

#endif // RETRY_TEST_H
```

```cpp
// Usage
#include "utils/retry_test.h"

TEST_WITH_RETRY(FlakyTests, ExternalAPICall) {
    auto response = callExternalAPI();
    EXPECT_EQ(response.statusCode, 200);
}
END_RETRY_TEST
```

### Track Flaky Tests

```cpp
// tests/utils/flaky_tracker.h
#ifndef FLAKY_TRACKER_H
#define FLAKY_TRACKER_H

#include <string>
#include <map>
#include <fstream>
#include <nlohmann/json.hpp>

class FlakyTestTracker {
private:
    static constexpr char FLAKY_LOG_FILE[] = "tests/flaky-tests.json";

    struct FlakyTestInfo {
        int count = 0;
        std::string lastSeen;

        NLOHMANN_DEFINE_TYPE_INTRUSIVE(FlakyTestInfo, count, lastSeen)
    };

    std::map<std::string, FlakyTestInfo> flakyTests_;

    void loadLog() {
        std::ifstream file(FLAKY_LOG_FILE);
        if (file.good()) {
            nlohmann::json j;
            file >> j;
            flakyTests_ = j.get<std::map<std::string, FlakyTestInfo>>();
        }
    }

public:
    FlakyTestTracker() {
        loadLog();
    }

    void recordFlaky(const std::string& testName) {
        auto& info = flakyTests_[testName];
        info.count++;
        info.lastSeen = getCurrentTime();
    }

    void saveLog() {
        std::ofstream file(FLAKY_LOG_FILE);
        nlohmann::json j = flakyTests_;
        file << j.dump(2);
    }

    void report() {
        if (flakyTests_.empty()) {
            return;
        }

        std::cout << "\n⚠️  Top Flaky Tests:\n";
        for (const auto& [name, info] : flakyTests_) {
            std::cout << "  " << name << ": " << info.count << " failures\n";
        }
    }

private:
    static std::string getCurrentTime() {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        return std::ctime(&time_t);
    }
};

#endif // FLAKY_TRACKER_H
```

## Phase 6: Test Maintenance Practices

### Monitor Test Execution Time

```cpp
// tests/utils/slow_test_detector.h
#ifndef SLOW_TEST_DETECTOR_H
#define SLOW_TEST_DETECTOR_H

#include <gtest/gtest.h>
#include <chrono>
#include <vector>
#include <algorithm>

class SlowTestDetector : public ::testing::TestEventListener {
private:
    struct SlowTest {
        std::string name;
        double duration;
    };

    static constexpr double SLOW_TEST_THRESHOLD_SEC = 1.0;
    std::vector<SlowTest> slowTests_;
    std::chrono::time_point<std::chrono::high_resolution_clock> startTime_;

public:
    void OnTestStart(const ::testing::TestInfo& test_info) override {
        startTime_ = std::chrono::high_resolution_clock::now();
    }

    void OnTestEnd(const ::testing::TestInfo& test_info) override {
        auto endTime = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration<double>(endTime - startTime_).count();

        if (duration > SLOW_TEST_THRESHOLD_SEC) {
            slowTests_.push_back({
                std::string(test_info.test_suite_name()) + "." + test_info.name(),
                duration
            });

            std::cout << "\n⚠️  Slow test: " << test_info.name()
                     << " (" << duration << "s)\n";
        }
    }

    void OnTestProgramEnd(const ::testing::UnitTest& /*unit_test*/) override {
        if (slowTests_.empty()) {
            return;
        }

        // Sort by duration descending
        std::sort(slowTests_.begin(), slowTests_.end(),
                 [](const SlowTest& a, const SlowTest& b) {
                     return a.duration > b.duration;
                 });

        std::cout << "\n============================================================\n";
        std::cout << "Slow Tests Detected:\n";

        size_t limit = std::min(slowTests_.size(), size_t(10));
        for (size_t i = 0; i < limit; ++i) {
            std::cout << "  " << slowTests_[i].duration << "s: "
                     << slowTests_[i].name << "\n";
        }

        std::cout << "============================================================\n";
    }

    // Implement empty overrides for other events
    void OnTestProgramStart(const ::testing::UnitTest&) override {}
    void OnTestIterationStart(const ::testing::UnitTest&, int) override {}
    void OnEnvironmentsSetUpStart(const ::testing::UnitTest&) override {}
    void OnEnvironmentsSetUpEnd(const ::testing::UnitTest&) override {}
    void OnTestCaseStart(const ::testing::TestCase&) override {}
    void OnTestSuiteStart(const ::testing::TestSuite&) override {}
    void OnTestPartResult(const ::testing::TestPartResult&) override {}
    void OnTestSuiteEnd(const ::testing::TestSuite&) override {}
    void OnTestCaseEnd(const ::testing::TestCase&) override {}
    void OnEnvironmentsTearDownStart(const ::testing::UnitTest&) override {}
    void OnEnvironmentsTearDownEnd(const ::testing::UnitTest&) override {}
    void OnTestIterationEnd(const ::testing::UnitTest&, int) override {}
};

#endif // SLOW_TEST_DETECTOR_H
```

Register in test main:

```cpp
// tests/main.cpp
#include <gtest/gtest.h>
#include "utils/slow_test_detector.h"

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);

    // Add slow test detector
    ::testing::TestEventListeners& listeners =
        ::testing::UnitTest::GetInstance()->listeners();
    listeners.Append(new SlowTestDetector());

    return RUN_ALL_TESTS();
}
```

## Phase 7: Test Result Reporting

### Custom Test Reporter

```cpp
// tests/utils/custom_reporter.h
#ifndef CUSTOM_REPORTER_H
#define CUSTOM_REPORTER_H

#include <gtest/gtest.h>
#include <nlohmann/json.hpp>
#include <fstream>

class CustomTestReporter : public ::testing::TestEventListener {
private:
    nlohmann::json report_;
    std::chrono::time_point<std::chrono::system_clock> startTime_;
    int totalTests_ = 0;
    int passedTests_ = 0;
    int failedTests_ = 0;

public:
    void OnTestProgramStart(const ::testing::UnitTest&) override {
        startTime_ = std::chrono::system_clock::now();
        report_["timestamp"] = std::chrono::system_clock::to_time_t(startTime_);
    }

    void OnTestEnd(const ::testing::TestInfo& test_info) override {
        totalTests_++;

        nlohmann::json result;
        result["name"] = std::string(test_info.test_suite_name()) + "." + test_info.name();
        result["status"] = test_info.result()->Passed() ? "passed" : "failed";
        result["duration"] = test_info.result()->elapsed_time();

        if (!test_info.result()->Passed()) {
            failedTests_++;
            result["failure_message"] = test_info.result()->GetTestPartResult(0).message();
        } else {
            passedTests_++;
        }

        report_["results"].push_back(result);
    }

    void OnTestProgramEnd(const ::testing::UnitTest&) override {
        auto endTime = std::chrono::system_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
            endTime - startTime_
        ).count();

        report_["summary"]["total"] = totalTests_;
        report_["summary"]["passed"] = passedTests_;
        report_["summary"]["failed"] = failedTests_;
        report_["summary"]["duration"] = duration;

        std::ofstream file("test-report.json");
        file << report_.dump(2);

        std::cout << "\n📊 Custom test report saved to: test-report.json\n";
    }

    // Empty overrides
    void OnTestIterationStart(const ::testing::UnitTest&, int) override {}
    void OnEnvironmentsSetUpStart(const ::testing::UnitTest&) override {}
    void OnEnvironmentsSetUpEnd(const ::testing::UnitTest&) override {}
    void OnTestCaseStart(const ::testing::TestCase&) override {}
    void OnTestSuiteStart(const ::testing::TestSuite&) override {}
    void OnTestStart(const ::testing::TestInfo&) override {}
    void OnTestPartResult(const ::testing::TestPartResult&) override {}
    void OnTestSuiteEnd(const ::testing::TestSuite&) override {}
    void OnTestCaseEnd(const ::testing::TestCase&) override {}
    void OnEnvironmentsTearDownStart(const ::testing::UnitTest&) override {}
    void OnEnvironmentsTearDownEnd(const ::testing::UnitTest&) override {}
    void OnTestIterationEnd(const ::testing::UnitTest&, int) override {}
};

#endif // CUSTOM_REPORTER_H
```

## Output Format

Please provide a comprehensive CI/CD and maintenance implementation with the following structure:

### CI/CD Configuration Summary
- **Platform**: [GitHub Actions/GitLab CI/Jenkins]
- **Pipeline Stages**: [list stages]
- **Parallel Execution**: [enabled/disabled, worker count]
- **Test Types Automated**: [unit, integration, benchmark]
- **Quality Gates**: [list gates]

### Quality Gate Configuration
| Gate | Threshold | Current | Status |
|------|-----------|---------|--------|
| Code Coverage | 80% | [value] | ✅/❌ |
| Test Pass Rate | 100% | [value] | ✅/❌ |
| Performance | <10% regression | [value] | ✅/❌ |
| Memory Leaks | 0 | [value] | ✅/❌ |

### Pre-commit Hooks Configured
- [ ] Code formatting (clang-format)
- [ ] Linting (clang-tidy, cppcheck)
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
- [ ] Flaky tests tracked and fixed
- [ ] Test maintenance schedule established

### Next Steps
- [ ] Monitor and optimize slow tests
- [ ] Fix identified flaky tests
- [ ] Review and update obsolete tests
- [ ] Enhance test documentation
- [ ] Set up test result dashboard
- [ ] Schedule regular test maintenance reviews
~~~

## Output Format

The AI assistant should deliver:

1. **Complete CI/CD pipeline configuration** (GitHub Actions or GitLab CI)
2. **Quality gate implementation** with thresholds (CMake, gcovr, Google Test)
3. **Pre-commit hook configuration** with all checks
4. **Test parallelization setup** for faster execution (CTest)
5. **Flaky test detection and tracking** system
6. **Test maintenance procedures** and documentation
7. **Test reporting infrastructure** with dashboards
8. **Execution metrics and monitoring** setup
