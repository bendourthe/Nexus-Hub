---
template_id: cpp_code_coverage
template_name: Code Coverage - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: test_development
phase: code_coverage
phase_number: 6
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites:

  - test_development/performance_testing/cpp_performance_testing.md
related_templates:

  - test_development/maintenance_cicd/cpp_maintenance_cicd.md
tools:

  - google test
  - catch2
  - boost.test
tags:

  - test-development
  - cpp
---
# C++ Code Coverage Analysis

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
Implement comprehensive code coverage measurement using gcov/lcov and llvm-cov, analyze coverage gaps, establish coverage goals (80%+ target), create systematic improvement strategies, integrate coverage into CI/CD, and maintain high-quality test coverage for C++ projects.

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

- [ ] gcov/lcov or llvm-cov installed and configured

- [ ] Compilation flags configured for coverage

- [ ] HTML report generation configured

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
# C++ Code Coverage Implementation

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

Please implement comprehensive code coverage measurement and improvement for this C++ project following this protocol:

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
# GCC gcov/lcov
sudo apt-get install g++ gcov lcov

# LLVM/Clang llvm-cov
sudo apt-get install clang llvm
```

**macOS**:
```bash
# Using Homebrew
brew install lcov llvm
```

**RHEL/CentOS**:
```bash
sudo yum install gcc-c++ lcov
```

### Configure CMake for Coverage (GCC/gcov)

**CMakeLists.txt with gcov support**:
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyApp CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")

# Coverage option
option(ENABLE_COVERAGE "Enable coverage reporting" OFF)

if(ENABLE_COVERAGE)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} --coverage -fprofile-arcs -ftest-arcs")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage -lgcov")
        message(STATUS "Coverage enabled (GCC/gcov)")
    elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
        set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fprofile-instr-generate -fcoverage-mapping")
        set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -fprofile-instr-generate")
        message(STATUS "Coverage enabled (Clang/llvm-cov)")
    endif()
endif()

# Source files
file(GLOB_RECURSE SOURCES "src/*.cpp")
list(REMOVE_ITEM SOURCES "${CMAKE_CURRENT_SOURCE_DIR}/src/main.cpp")

# Main executable
add_executable(myapp src/main.cpp ${SOURCES})

# Test executable with Google Test
enable_testing()
find_package(GTest REQUIRED)
file(GLOB_RECURSE TEST_SOURCES "tests/*.cpp")
add_executable(test_runner ${TEST_SOURCES} ${SOURCES})
target_link_libraries(test_runner GTest::GTest GTest::Main)
add_test(NAME UnitTests COMMAND test_runner)

# Coverage targets for GCC
if(ENABLE_COVERAGE AND CMAKE_CXX_COMPILER_ID MATCHES "GNU")
    add_custom_target(coverage
        COMMAND ${CMAKE_CTEST_COMMAND}
        COMMAND lcov --capture --directory . --output-file coverage.info
        COMMAND lcov --remove coverage.info '/usr/*' '*/tests/*' '*/googletest/*' --output-file coverage.info
        COMMAND genhtml coverage.info --output-directory coverage/html
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMENT "Generating coverage report (gcov)"
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

# Coverage targets for Clang
if(ENABLE_COVERAGE AND CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    add_custom_target(coverage
        COMMAND LLVM_PROFILE_FILE=test_runner.profraw ${CMAKE_CTEST_COMMAND}
        COMMAND llvm-profdata merge -sparse test_runner.profraw -o test_runner.profdata
        COMMAND llvm-cov show test_runner -instr-profile=test_runner.profdata -format=html -output-dir=coverage/html
        COMMAND llvm-cov report test_runner -instr-profile=test_runner.profdata
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
        COMMENT "Generating coverage report (llvm-cov)"
    )

    add_custom_target(coverage-check
        COMMAND bash -c "COVERAGE=$$(llvm-cov report test_runner -instr-profile=test_runner.profdata | grep TOTAL | awk '{print $$NF}' | sed 's/%//'); \
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

# Using GCC
cmake -DENABLE_COVERAGE=ON -DCMAKE_CXX_COMPILER=g++ ..

# Using Clang
cmake -DENABLE_COVERAGE=ON -DCMAKE_CXX_COMPILER=clang++ ..

make
make test
make coverage
```

### Alternative: Makefile Configuration

**Makefile with coverage support**:
```makefile
# Compiler settings
CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -g
LDFLAGS =

# Coverage flags
COVERAGE_CXXFLAGS = --coverage -fprofile-arcs -ftest-arcs
COVERAGE_LDFLAGS = --coverage -lgcov

# Directories
SRC_DIR = src
TEST_DIR = tests
BUILD_DIR = build
COVERAGE_DIR = coverage

# Source files
SRCS = $(wildcard $(SRC_DIR)/*.cpp)
OBJS = $(SRCS:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
TEST_SRCS = $(wildcard $(TEST_DIR)/*.cpp)
TEST_OBJS = $(TEST_SRCS:$(TEST_DIR)/%.cpp=$(BUILD_DIR)/%.o)

# Targets
TARGET = myapp
TEST_TARGET = test_runner

# Google Test
GTEST_FLAGS = -lgtest -lgtest_main -pthread

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

coverage: CXXFLAGS += $(COVERAGE_CXXFLAGS)
coverage: LDFLAGS += $(COVERAGE_LDFLAGS)
coverage: clean $(TEST_TARGET)
	./$(TEST_TARGET)
	@echo "Generating coverage report..."
	lcov --capture --directory . --output-file $(COVERAGE_DIR)/coverage.info
	lcov --remove $(COVERAGE_DIR)/coverage.info '/usr/*' '*/tests/*' '*/googletest/*' --output-file $(COVERAGE_DIR)/coverage.info
	genhtml $(COVERAGE_DIR)/coverage.info --output-directory $(COVERAGE_DIR)/html
	@echo "Coverage report: $(COVERAGE_DIR)/html/index.html"

$(TEST_TARGET): CXXFLAGS += $(COVERAGE_CXXFLAGS)
$(TEST_TARGET): LDFLAGS += $(COVERAGE_LDFLAGS) $(GTEST_FLAGS)
$(TEST_TARGET): $(filter-out $(BUILD_DIR)/main.o, $(OBJS)) $(TEST_OBJS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -o $@ $^

$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(BUILD_DIR)/%.o: $(TEST_DIR)/%.cpp
	@mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -I$(SRC_DIR) -c $< -o $@

test: $(TEST_TARGET)
	./$(TEST_TARGET)

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

clean:
	rm -rf $(BUILD_DIR) $(TARGET) $(TEST_TARGET)
	rm -f *.gcda *.gcno *.gcov
	find . -name "*.gcda" -delete
	find . -name "*.gcno" -delete

clean-coverage:
	rm -rf $(COVERAGE_DIR)
	rm -f *.gcda *.gcno *.gcov *.profraw *.profdata
	find . -name "*.gcda" -delete
	find . -name "*.gcno" -delete

.PHONY: all test coverage coverage-check clean clean-coverage
```

### Coverage Script

**scripts/coverage.sh**:
```bash
#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

COVERAGE_DIR="coverage"
MIN_COVERAGE=80.0

echo "Building with coverage instrumentation..."
cd build || (mkdir build && cd build)
cmake -DENABLE_COVERAGE=ON ..
make
make test

echo ""
echo "Generating coverage report..."
make coverage

echo ""
echo "========================================"
echo "Coverage Summary"
echo "========================================"
lcov --summary ${COVERAGE_DIR}/coverage.info

TOTAL_COVERAGE=$(lcov --summary ${COVERAGE_DIR}/coverage.info 2>&1 | \
    grep "lines" | awk '{print $2}' | sed 's/%//')

echo ""
echo "Total Line Coverage: ${TOTAL_COVERAGE}%"

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
# Using CMake
mkdir build && cd build
cmake -DENABLE_COVERAGE=ON ..
make
make test
make coverage

# Using Makefile
make coverage

# Using script
chmod +x scripts/coverage.sh
./scripts/coverage.sh

# View HTML report
open coverage/html/index.html  # macOS
xdg-open coverage/html/index.html  # Linux
```

### Analyze Coverage Report

**Terminal output example (gcov/lcov)**:
```
Reading tracefile coverage.info
Summary coverage rate:
  lines......: 76.3% (231 of 304 lines)
  functions..: 81.2% (43 of 53 functions)
  branches...: 68.4% (45 of 66 branches)

File 'src/auth.cpp'
  Lines executed: 78.26% of 46
  Functions executed: 85.71% of 7
  Branches executed: 70.00% of 20

File 'src/service.cpp'
  Lines executed: 67.42% of 89
  Functions executed: 70.59% of 17
  Branches executed: 55.56% of 27
```

**Terminal output example (llvm-cov)**:
```
Filename                      Regions    Missed Regions     Cover   Functions  Missed Functions  Executed       Lines      Missed Lines     Cover
----------------------------------------------------------------------------------------------------------------------------------------------------------
src/auth.cpp                       42                 9    78.57%          12                 2    83.33%          89                19    78.65%
src/service.cpp                    67                23    65.67%          21                 6    71.43%         156                51    67.31%
src/util.cpp                       28                 2    92.86%           8                 0   100.00%          67                 5    92.54%
----------------------------------------------------------------------------------------------------------------------------------------------------------
TOTAL                             137                34    75.18%          41                 8    80.49%         312                75    75.96%
```

### Identify Coverage Gaps

**Create coverage gap analyzer**:

```cpp
// scripts/analyze_coverage.cpp
#include <iostream>
#include <fstream>
#include <vector>
#include <algorithm>
#include <regex>
#include <string>

struct CoverageGap {
    std::string filename;
    double line_coverage;
    double function_coverage;
    double branch_coverage;
    std::string priority;

    double avg_coverage() const {
        return (line_coverage + function_coverage + branch_coverage) / 3.0;
    }
};

std::string determine_priority(double avg) {
    if (avg < 50.0) return "HIGH";
    if (avg < 70.0) return "MEDIUM";
    return "LOW";
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <lcov_list_output.txt>\n";
        return 1;
    }

    std::ifstream file(argv[1]);
    if (!file) {
        std::cerr << "Error: Cannot open file " << argv[1] << "\n";
        return 1;
    }

    std::vector<CoverageGap> gaps;
    std::string line;
    std::regex pattern(R"(^\s*(.+?\.cpp)\s+(\d+\.\d+)%)");

    while (std::getline(file, line)) {
        std::smatch matches;
        if (std::regex_search(line, matches, pattern)) {
            double coverage = std::stod(matches[2].str());
            if (coverage < 80.0) {
                CoverageGap gap;
                gap.filename = matches[1].str();
                gap.line_coverage = coverage;
                gap.function_coverage = coverage;  // Simplified
                gap.branch_coverage = coverage;    // Simplified
                gap.priority = determine_priority(gap.avg_coverage());
                gaps.push_back(gap);
            }
        }
    }

    std::sort(gaps.begin(), gaps.end(),
        [](const CoverageGap& a, const CoverageGap& b) {
            return a.avg_coverage() < b.avg_coverage();
        });

    std::cout << std::string(100, '=') << "\n";
    std::cout << "Coverage Gap Analysis\n";
    std::cout << std::string(100, '=') << "\n";
    std::cout << std::left << std::setw(40) << "File"
              << std::right << std::setw(10) << "Lines"
              << std::setw(12) << "Functions"
              << std::setw(10) << "Branches"
              << std::setw(12) << "Priority" << "\n";
    std::cout << std::string(100, '-') << "\n";

    for (const auto& gap : gaps) {
        std::cout << std::left << std::setw(40) << gap.filename
                  << std::right << std::setw(9) << std::fixed << std::setprecision(1)
                  << gap.line_coverage << "%"
                  << std::setw(11) << gap.function_coverage << "%"
                  << std::setw(9) << gap.branch_coverage << "%"
                  << std::setw(12) << gap.priority << "\n";
    }

    std::cout << "\nTotal files needing improvement: " << gaps.size() << "\n";

    return 0;
}
```

Compile and run:
```bash
g++ -std=c++17 -o analyze_coverage scripts/analyze_coverage.cpp
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

```cpp
/**

 * Add tests for basic functionality of uncovered code.
 *

 * Focus on main execution paths first.
 */

// src/discount.h
#pragma once

enum class CustomerType {
    Premium,
    Regular,
    Guest
};

class DiscountCalculator {
public:
    double calculateDiscount(double price, CustomerType customerType) const;
};

// src/discount.cpp
#include "discount.h"

double DiscountCalculator::calculateDiscount(double price, CustomerType customerType) const {
    switch (customerType) {
        case CustomerType::Premium:
            return price * 0.20;
        case CustomerType::Regular:
            return price * 0.10;
        default:
            return 0.0;
    }
}

// tests/test_discount.cpp
#include <gtest/gtest.h>
#include "../src/discount.h"

class DiscountCalculatorTest : public ::testing::Test {
protected:
    DiscountCalculator calculator;
};

TEST_F(DiscountCalculatorTest, CalculateDiscount_Premium) {
    double discount = calculator.calculateDiscount(100.0, CustomerType::Premium);
    EXPECT_DOUBLE_EQ(20.0, discount);
}

TEST_F(DiscountCalculatorTest, CalculateDiscount_Regular) {
    double discount = calculator.calculateDiscount(100.0, CustomerType::Regular);
    EXPECT_DOUBLE_EQ(10.0, discount);
}

TEST_F(DiscountCalculatorTest, CalculateDiscount_Guest) {
    double discount = calculator.calculateDiscount(100.0, CustomerType::Guest);
    EXPECT_DOUBLE_EQ(0.0, discount);
}
```

### Strategy 2: Cover Edge Cases

```cpp
/**

 * Add tests for boundary conditions and edge cases.
 */

// tests/test_discount_edge_cases.cpp
#include <gtest/gtest.h>
#include <limits>
#include "../src/discount.h"

class DiscountCalculatorEdgeCasesTest : public ::testing::Test {
protected:
    DiscountCalculator calculator;
};

TEST_F(DiscountCalculatorEdgeCasesTest, ZeroPrice) {
    double discount = calculator.calculateDiscount(0.0, CustomerType::Premium);
    EXPECT_DOUBLE_EQ(0.0, discount);
}

TEST_F(DiscountCalculatorEdgeCasesTest, NegativePrice) {
    double discount = calculator.calculateDiscount(-100.0, CustomerType::Premium);
    EXPECT_DOUBLE_EQ(-20.0, discount); // Or should throw?
}

TEST_F(DiscountCalculatorEdgeCasesTest, VeryLargePrice) {
    double discount = calculator.calculateDiscount(1000000.0, CustomerType::Premium);
    EXPECT_DOUBLE_EQ(200000.0, discount);
}

TEST_F(DiscountCalculatorEdgeCasesTest, SmallDecimal) {
    double discount = calculator.calculateDiscount(0.01, CustomerType::Premium);
    EXPECT_NEAR(0.002, discount, 0.0001);
}

TEST_F(DiscountCalculatorEdgeCasesTest, MaxDouble) {
    double discount = calculator.calculateDiscount(
        std::numeric_limits<double>::max(),
        CustomerType::Premium
    );
    EXPECT_GT(discount, 0.0);
}

// Parameterized test for multiple values
class DiscountCalculatorParamTest :
    public ::testing::TestWithParam<std::tuple<double, CustomerType, double>> {
protected:
    DiscountCalculator calculator;
};

TEST_P(DiscountCalculatorParamTest, VariousPrices) {
    auto [price, type, expected] = GetParam();
    double discount = calculator.calculateDiscount(price, type);
    EXPECT_DOUBLE_EQ(expected, discount);
}

INSTANTIATE_TEST_SUITE_P(
    EdgeCases,
    DiscountCalculatorParamTest,
    ::testing::Values(
        std::make_tuple(0.01, CustomerType::Premium, 0.002),
        std::make_tuple(10.0, CustomerType::Premium, 2.0),
        std::make_tuple(99.99, CustomerType::Premium, 19.998),
        std::make_tuple(1000.0, CustomerType::Regular, 100.0),
        std::make_tuple(100.0, CustomerType::Guest, 0.0)
    )
);
```

### Strategy 3: Cover Error Paths

```cpp
/**

 * Add tests for error handling and exceptional conditions.
 */

// src/user_service.h
#pragma once
#include <string>
#include <optional>
#include <stdexcept>

class User {
public:
    long id;
    std::string name;
};

class UserNotFoundException : public std::runtime_error {
public:
    explicit UserNotFoundException(const std::string& msg)
        : std::runtime_error(msg) {}
};

class DatabaseException : public std::runtime_error {
public:
    explicit DatabaseException(const std::string& msg)
        : std::runtime_error(msg) {}
};

class IUserRepository {
public:
    virtual ~IUserRepository() = default;
    virtual std::optional<User> findById(long userId) = 0;
};

class UserService {
private:
    IUserRepository* repository;

public:
    explicit UserService(IUserRepository* repo) : repository(repo) {}
    std::optional<User> loadUserData(long userId);
};

// src/user_service.cpp
#include "user_service.h"
#include <iostream>

std::optional<User> UserService::loadUserData(long userId) {
    try {
        auto user = repository->findById(userId);

        if (!user) {
            throw UserNotFoundException("User not found: " + std::to_string(userId));
        }

        return user;

    } catch (const DatabaseException& e) {
        std::cerr << "Database error loading user: " << userId << " - " << e.what() << "\n";
        throw;
    } catch (const UserNotFoundException& e) {
        std::cerr << "User not found: " << userId << "\n";
        return std::nullopt;
    }
}

// tests/test_user_service.cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>
#include "../src/user_service.h"

class MockUserRepository : public IUserRepository {
public:
    MOCK_METHOD(std::optional<User>, findById, (long userId), (override));
};

class UserServiceTest : public ::testing::Test {
protected:
    MockUserRepository mockRepo;
    UserService service{&mockRepo};
};

TEST_F(UserServiceTest, LoadUserData_Success) {
    User expectedUser{123, "John Doe"};
    EXPECT_CALL(mockRepo, findById(123))
        .WillOnce(::testing::Return(expectedUser));

    auto user = service.loadUserData(123);

    ASSERT_TRUE(user.has_value());
    EXPECT_EQ(123, user->id);
    EXPECT_EQ("John Doe", user->name);
}

TEST_F(UserServiceTest, LoadUserData_NotFound) {
    EXPECT_CALL(mockRepo, findById(999))
        .WillOnce(::testing::Return(std::nullopt));

    auto user = service.loadUserData(999);

    EXPECT_FALSE(user.has_value());
}

TEST_F(UserServiceTest, LoadUserData_DatabaseError) {
    EXPECT_CALL(mockRepo, findById(123))
        .WillOnce(::testing::Throw(DatabaseException("Connection failed")));

    EXPECT_THROW(service.loadUserData(123), DatabaseException);
}
```

### Strategy 4: Cover Branch Conditions

```cpp
/**

 * Ensure all branches of conditional logic are tested.
 */

// src/shipping.h
#pragma once

enum class Destination {
    Domestic,
    International,
    Remote
};

class ShippingCalculator {
public:
    double calculateShippingCost(double weight, Destination destination, bool express) const;
};

// src/shipping.cpp
#include "shipping.h"

double ShippingCalculator::calculateShippingCost(
        double weight,
        Destination destination,
        bool express) const {

    double baseCost = weight * 2.5;

    switch (destination) {
        case Destination::International:
            baseCost *= 3.0;
            break;
        case Destination::Remote:
            baseCost *= 1.5;
            break;
        default:
            break;
    }

    if (express) {
        baseCost *= 2.0;
    }

    return baseCost;
}

// tests/test_shipping.cpp
#include <gtest/gtest.h>
#include "../src/shipping.h"

class ShippingCalculatorBranchTest :
    public ::testing::TestWithParam<std::tuple<Destination, bool, double>> {
protected:
    ShippingCalculator calculator;
};

TEST_P(ShippingCalculatorBranchTest, AllBranches) {
    auto [destination, express, expected] = GetParam();
    double cost = calculator.calculateShippingCost(10.0, destination, express);
    EXPECT_DOUBLE_EQ(expected, cost);
}

INSTANTIATE_TEST_SUITE_P(
    AllCombinations,
    ShippingCalculatorBranchTest,
    ::testing::Values(
        std::make_tuple(Destination::Domestic, false, 25.0),
        std::make_tuple(Destination::Domestic, true, 50.0),
        std::make_tuple(Destination::International, false, 75.0),
        std::make_tuple(Destination::International, true, 150.0),
        std::make_tuple(Destination::Remote, false, 37.5),
        std::make_tuple(Destination::Remote, true, 75.0)
    )
);
```

## Phase 5: Coverage Reporting and Tracking

### Generate Comprehensive Reports

```bash
# Using CMake
cd build
make coverage

# Using Makefile
make coverage

# Reports generated:
# GCC/gcov:
# - coverage/coverage.info (LCOV format)
# - coverage/html/index.html (browsable HTML)

# Clang/llvm-cov:
# - test_runner.profdata (profile data)
# - coverage/html/index.html (browsable HTML)
```

### Coverage Badge

```bash
# For GCC/gcov
COVERAGE=$(lcov --summary coverage/coverage.info 2>&1 | \
    grep "lines" | awk '{print $2}' | sed 's/%//')

# For Clang/llvm-cov
COVERAGE=$(llvm-cov report test_runner -instr-profile=test_runner.profdata | \
    grep TOTAL | awk '{print $NF}' | sed 's/%//')

# Generate badge
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

```cpp
// scripts/track_coverage.cpp
#include <iostream>
#include <fstream>
#include <string>
#include <chrono>
#include <iomanip>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <coverage_percentage>\n";
        return 1;
    }

    double coverage = std::stod(argv[1]);

    std::ofstream file("coverage-history.csv", std::ios::app);
    if (!file) {
        std::cerr << "Error: Cannot open coverage-history.csv\n";
        return 1;
    }

    auto now = std::chrono::system_clock::now();
    auto time = std::chrono::system_clock::to_time_t(now);

    file << std::put_time(std::localtime(&time), "%Y-%m-%d %H:%M:%S")
         << "," << std::fixed << std::setprecision(2) << coverage << "\n";

    std::cout << "Coverage recorded: " << coverage << "%\n";

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
          sudo apt-get install -y g++ lcov libgtest-dev cmake

      - name: Build Google Test
        run: |
          cd /usr/src/gtest
          sudo cmake CMakeLists.txt
          sudo make
          sudo cp lib/*.a /usr/lib

      - name: Build with coverage
        run: |
          mkdir build && cd build
          cmake -DENABLE_COVERAGE=ON ..
          make
          make test
          make coverage

      - name: Check coverage threshold
        run: |
          cd build
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
          files: ./build/coverage/coverage.info
          fail_ci_if_error: true

      - name: Archive coverage report
        uses: actions/upload-artifact@v3
        with:
          name: coverage-report
          path: build/coverage/html/
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
| src/service.cpp | 67% | 71% | 56% | Critical |
| src/auth.cpp | 78% | 86% | 70% | High |
| src/util.cpp | 93% | 90% | 88% | Low |

### Critical Coverage Gaps
1. **src/service.cpp** (67% line coverage)
   - **Missing**: Error handling paths, exception handling
   - **Priority**: Critical - core business logic
   - **Action**: Add exception and error scenario tests

2. **src/auth.cpp** (78% line coverage)
   - **Missing**: Edge cases in authentication, boundary conditions
   - **Priority**: High - security-critical
   - **Action**: Add boundary condition and security tests

### Coverage Improvement Plan
**Sprint 1** (Target: 75% → 80%):

- [ ] Add exception handling tests with Google Mock

- [ ] Cover authentication edge cases

- [ ] Test all error code paths

**Sprint 2** (Target: 80% → 85%):

- [ ] Add parameterized tests for branches

- [ ] Test input validation thoroughly

- [ ] Cover all switch/case statements

**Sprint 3** (Target: 85% → 90%):

- [ ] Add move semantics and RAII tests

- [ ] Cover template instantiations

- [ ] Test all operator overloads

### Coverage Reports Generated

- **LCOV Info**: `coverage/coverage.info` (GCC)

- **Profile Data**: `test_runner.profdata` (Clang)

- **HTML Report**: `coverage/html/index.html`

- **Badge**: `coverage/badge.svg`

### Coverage Thresholds

- **Minimum Overall**: 80%

- **Critical Modules**: 90%

- **New Code**: 100%

- **CI/CD Gate**: Fail if <80%

### Best Practices Implemented

- [ ] Coverage measured with Google Test

- [ ] HTML reports for detailed analysis

- [ ] Coverage tracked over time

- [ ] Regression prevention in CI/CD

- [ ] Critical paths prioritized

- [ ] Mock objects for dependencies

- [ ] Parameterized tests for branches

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

1. **Complete coverage configuration** (CMakeLists.txt or Makefile)
2. **Current coverage analysis** with gaps identified
3. **Prioritized improvement plan** with specific actions
4. **Test implementations** to fill critical gaps (Google Test/Google Mock)
5. **Coverage reporting infrastructure** (LCOV or llvm-cov, HTML)
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
