---
name: setup-test-infrastructure
description: Establish comprehensive testing frameworks and directory structure across all languages
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Testing
tags: [testing, infrastructure, framework, setup, pytest, jest, junit, xunit, go-testing, unity, googletest]
priority: MEDIUM
based_on: Test Development Templates - Test Structure
---

# Setup Test Infrastructure

Establish robust testing frameworks with optimal configuration, logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices across Python, JavaScript, Java, C#, Go, C, and C++ projects.

## When to Use This Skill

Use this skill when:
- Starting a new project that needs testing infrastructure
- Modernizing legacy test setups
- Standar dizing testing across team projects
- Setting up testing for microservices
- Migrating between test frameworks
- Establishing testing best practices
- Creating reusable test templates

**This skill is essential for**:
- Projects without existing test infrastructure
- Teams adopting testing standards
- Codebases with inconsistent test organization
- Applications requiring multiple test types (unit/integration/e2e)

## What This Skill Does

This skill helps you:
1. **Select and configure** appropriate testing frameworks for your language
2. **Design directory structures** that scale with your project
3. **Set up test discovery** and execution workflows
4. **Configure fixtures** and test utilities
5. **Establish naming conventions** and best practices
6. **Enable parallel test execution** for performance
7. **Integrate coverage tools** from the start

## Prerequisites

### Language-Specific Requirements

**Python**:
- Python 3.9+
- pip package manager
- Virtual environment tool

**JavaScript/TypeScript**:
- Node.js 18+
- npm or yarn package manager

**Java**:
- JDK 11+
- Maven or Gradle build tool

**C#**:
- .NET 6.0+
- dotnet CLI

**Go**:
- Go 1.19+
- go modules enabled

**C**:
- GCC or Clang compiler
- Make or CMake build system

**C++**:
- C++17 compatible compiler
- CMake 3.14+

### Recommended Knowledge
- Basic testing concepts (unit, integration, e2e)
- Command-line operations
- Package management for your language
- Build tool configuration

## Instructions

### Step 1: Choose Testing Framework

Select the appropriate framework for your language:

**Python**:
- **pytest** (Recommended): Modern, powerful, great plugins
- **unittest**: Standard library, class-based, verbose
- **nose2**: Legacy, less maintained

**JavaScript/TypeScript**:
- **Jest** (Recommended): Feature-rich, zero-config, fast
- **Vitest**: Modern, Vite-compatible, fast
- **Mocha**: Flexible, requires configuration
- **Jasmine**: Behavior-driven, no dependencies

**Java**:
- **JUnit 5** (Recommended): Modern, powerful, extensible
- **TestNG**: Advanced features, parallel execution
- **Spock**: Groovy-based, expressive

**C#**:
- **xUnit** (Recommended): Modern, clean, parallel
- **NUnit**: Mature, feature-rich
- **MSTest**: Microsoft's framework, Visual Studio integration

**Go**:
- **testing** (Standard): Built-in, simple, effective
- **testify**: Assertions and mocking
- **ginkgo**: BDD-style

**C**:
- **Unity** (Recommended): Lightweight, embedded-friendly
- **Check**: Unit testing, test fixtures
- **CUnit**: Comprehensive, complex setup

**C++**:
- **Google Test** (Recommended): Industry standard, mature
- **Catch2**: Header-only, modern C++
- **Boost.Test**: Part of Boost, comprehensive

### Step 2: Install Testing Framework

**Python (pytest)**:
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install testing stack
pip install pytest>=7.4.0
pip install pytest-cov>=4.1.0        # Coverage
pip install pytest-xdist>=3.3.0      # Parallel execution
pip install pytest-mock>=3.11.0      # Enhanced mocking
pip install pytest-timeout>=2.1.0    # Test timeouts
pip install pytest-asyncio>=0.21.0   # Async support (if needed)

# Save dependencies
pip freeze > requirements-test.txt
```

**JavaScript (Jest)**:
```bash
# Initialize project if needed
npm init -y

# Install Jest and related tools
npm install --save-dev jest@29.x
npm install --save-dev @types/jest  # For TypeScript
npm install --save-dev ts-jest       # TypeScript support
npm install --save-dev @testing-library/jest-dom  # DOM matchers

# Add to package.json scripts
# "test": "jest",
# "test:watch": "jest --watch",
# "test:coverage": "jest --coverage"
```

**Java (JUnit 5 with Maven)**:
```xml
<!-- Add to pom.xml -->
<dependencies>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.0</version>
        <scope>test</scope>
    </dependency>
    <dependency>
        <groupId>org.mockito</groupId>
        <artifactId>mockito-core</artifactId>
        <version>5.5.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.1.2</version>
        </plugin>
    </plugins>
</build>
```

**C# (xUnit)**:
```bash
# Create test project
dotnet new xunit -n MyProject.Tests

# Add test dependencies
dotnet add package xunit
dotnet add package xunit.runner.visualstudio
dotnet add package Microsoft.NET.Test.Sdk
dotnet add package Moq  # For mocking
dotnet add package FluentAssertions  # Better assertions

# Add reference to main project
dotnet add reference ../MyProject/MyProject.csproj
```

**Go (testing + testify)**:
```bash
# Initialize module if needed
go mod init myproject

# Install testify for assertions and mocking
go get github.com/stretchr/testify
```

**C (Unity)**:
```bash
# Clone Unity test framework
git clone https://github.com/ThrowTheSwitch/Unity.git test/Unity

# Or add as submodule
git submodule add https://github.com/ThrowTheSwitch/Unity.git test/Unity
```

**C++ (Google Test with CMake)**:
```cmake
# Add to CMakeLists.txt
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/v1.14.0.zip
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

enable_testing()
```

### Step 3: Create Directory Structure

Implement a standard test layout for your language:

**Python Structure**:
```
project_root/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Root fixtures
│   │
│   ├── unit/                    # Unit tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_core.py
│   │   └── test_utils.py
│   │
│   ├── integration/             # Integration tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_api_integration.py
│   │
│   ├── e2e/                     # End-to-end tests
│   │   ├── __init__.py
│   │   └── test_workflows.py
│   │
│   ├── fixtures/                # Shared fixtures
│   │   ├── __init__.py
│   │   └── common_fixtures.py
│   │
│   ├── helpers/                 # Test utilities
│   │   ├── __init__.py
│   │   ├── assertions.py
│   │   └── factories.py
│   │
│   ├── data/                    # Test data
│   │   └── sample_data.json
│   │
│   └── resources/               # Test resources
│       └── test_file.txt
│
├── pytest.ini                   # pytest configuration
└── requirements-test.txt        # Test dependencies
```

**JavaScript Structure**:
```
project_root/
├── src/
│   ├── core.js
│   └── utils.js
│
├── tests/
│   ├── unit/
│   │   ├── core.test.js
│   │   └── utils.test.js
│   │
│   ├── integration/
│   │   └── api.test.js
│   │
│   ├── e2e/
│   │   └── workflows.test.js
│   │
│   ├── fixtures/
│   │   └── commonFixtures.js
│   │
│   ├── helpers/
│   │   ├── testUtils.js
│   │   └── factories.js
│   │
│   ├── data/
│   │   └── sampleData.json
│   │
│   └── setup.js                 # Global test setup
│
├── jest.config.js               # Jest configuration
└── package.json
```

**Java Structure (Maven)**:
```
project_root/
├── src/
│   ├── main/
│   │   └── java/
│   │       └── com/example/
│   │           ├── Core.java
│   │           └── Utils.java
│   │
│   └── test/
│       ├── java/
│       │   └── com/example/
│       │       ├── unit/
│       │       │   ├── CoreTest.java
│       │       │   └── UtilsTest.java
│       │       │
│       │       ├── integration/
│       │       │   └── ApiIntegrationTest.java
│       │       │
│       │       └── fixtures/
│       │           └── TestDataFactory.java
│       │
│       └── resources/
│           └── test-data.json
│
└── pom.xml
```

**C# Structure**:
```
solution_root/
├── MyProject/
│   ├── Core.cs
│   └── Utils.cs
│
├── MyProject.Tests/
│   ├── Unit/
│   │   ├── CoreTests.cs
│   │   └── UtilsTests.cs
│   │
│   ├── Integration/
│   │   └── ApiIntegrationTests.cs
│   │
│   ├── Fixtures/
│   │   └── TestDataFactory.cs
│   │
│   ├── Helpers/
│   │   └── TestUtilities.cs
│   │
│   └── TestData/
│       └── sample-data.json
│
└── MyProject.sln
```

**Go Structure**:
```
project_root/
├── cmd/
│   └── app/
│       └── main.go
│
├── internal/
│   ├── core/
│   │   ├── core.go
│   │   └── core_test.go        # Tests alongside code
│   │
│   └── utils/
│       ├── utils.go
│       └── utils_test.go
│
├── test/
│   ├── integration/
│   │   └── api_test.go
│   │
│   ├── e2e/
│   │   └── workflow_test.go
│   │
│   ├── fixtures/
│   │   └── fixtures.go
│   │
│   └── testdata/
│       └── sample.json
│
└── go.mod
```

**C Structure**:
```
project_root/
├── src/
│   ├── core.c
│   ├── core.h
│   ├── utils.c
│   └── utils.h
│
├── test/
│   ├── Unity/                   # Unity framework
│   │   ├── unity.c
│   │   └── unity.h
│   │
│   ├── unit/
│   │   ├── test_core.c
│   │   └── test_utils.c
│   │
│   ├── integration/
│   │   └── test_integration.c
│   │
│   ├── fixtures/
│   │   ├── test_fixtures.c
│   │   └── test_fixtures.h
│   │
│   └── test_runner.c            # Main test runner
│
├── CMakeLists.txt               # Build configuration
└── Makefile
```

**C++ Structure**:
```
project_root/
├── src/
│   ├── core.cpp
│   ├── core.hpp
│   ├── utils.cpp
│   └── utils.hpp
│
├── tests/
│   ├── unit/
│   │   ├── test_core.cpp
│   │   └── test_utils.cpp
│   │
│   ├── integration/
│   │   └── test_integration.cpp
│   │
│   ├── fixtures/
│   │   ├── test_fixtures.hpp
│   │   └── test_fixtures.cpp
│   │
│   ├── helpers/
│   │   └── test_helpers.hpp
│   │
│   └── data/
│       └── test_data.json
│
├── CMakeLists.txt
└── test_main.cpp                # Test entry point
```

### Step 4: Configure Testing Framework

Create configuration files for your framework:

**Python (pytest.ini)**:
```ini
[pytest]
# Test discovery
python_files = test_*.py *_test.py
python_classes = Test* *Tests
python_functions = test_*

# Test paths
testpaths = tests

# Output options
addopts =
    -v                          # Verbose output
    --strict-markers            # Enforce marker registration
    --tb=short                  # Shorter traceback format
    -ra                         # Show summary of all outcomes
    --cov=src                   # Coverage for src directory
    --cov-report=html           # HTML coverage report
    --cov-report=term-missing   # Terminal with missing lines
    --cov-fail-under=80         # Fail if coverage below 80%

# Markers
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Tests that take significant time
    smoke: Quick smoke tests

# Coverage
[coverage:run]
source = src
omit =
    */tests/*
    */test_*.py
    */__init__.py

[coverage:report]
precision = 2
show_missing = True
```

**JavaScript (jest.config.js)**:
```javascript
module.exports = {
  // Test environment
  testEnvironment: 'node',  // or 'jsdom' for browser tests

  // Test patterns
  testMatch: [
    '**/__tests__/**/*.js',
    '**/?(*.)+(spec|test).js'
  ],

  // Coverage
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/**/*.test.js',
    '!**/node_modules/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  coverageDirectory: 'coverage',

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],

  // Module paths
  moduleDirectories: ['node_modules', 'src'],

  // Transform files
  transform: {
    '^.+\\.jsx?$': 'babel-jest',
    '^.+\\.tsx?$': 'ts-jest'
  },

  // Test timeout
  testTimeout: 10000,

  // Parallel execution
  maxWorkers: '50%'
};
```

**Java (pom.xml - Surefire plugin)**:
```xml
<plugin>
    <groupId>org.apache.maven.plugins</groupId>
    <artifactId>maven-surefire-plugin</artifactId>
    <version>3.1.2</version>
    <configuration>
        <!-- Test patterns -->
        <includes>
            <include>**/*Test.java</include>
            <include>**/*Tests.java</include>
        </includes>

        <!-- Parallel execution -->
        <parallel>methods</parallel>
        <threadCount>4</threadCount>

        <!-- System properties -->
        <systemPropertyVariables>
            <test.env>test</test.env>
        </systemPropertyVariables>

        <!-- Fail fast -->
        <skipAfterFailureCount>1</skipAfterFailureCount>
    </configuration>
</plugin>
```

**C# (xUnit - in .csproj)**:
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <IsPackable>false</IsPackable>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="xunit" Version="2.5.0" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.0" />
    <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.7.0" />
    <PackageReference Include="Moq" Version="4.20.0" />
    <PackageReference Include="FluentAssertions" Version="6.12.0" />
  </ItemGroup>

  <ItemGroup>
    <ProjectReference Include="..\MyProject\MyProject.csproj" />
  </ItemGroup>
</Project>
```

**Go (test configuration)**:
```go
// test/config_test.go
package test

import (
    "os"
    "testing"
)

// TestMain runs before all tests
func TestMain(m *testing.M) {
    // Setup
    os.Setenv("TEST_ENV", "test")

    // Run tests
    code := m.Run()

    // Teardown
    os.Exit(code)
}
```

**C (CMakeLists.txt)**:
```cmake
cmake_minimum_required(VERSION 3.14)
project(MyProject)

# Enable testing
enable_testing()

# Add Unity framework
add_subdirectory(test/Unity)

# Test executable
add_executable(test_runner
    test/unit/test_core.c
    test/unit/test_utils.c
    test/test_runner.c
    src/core.c
    src/utils.c
)

target_include_directories(test_runner PRIVATE
    src
    test/Unity
)

target_link_libraries(test_runner unity)

# Add test
add_test(NAME AllTests COMMAND test_runner)
```

**C++ (CMakeLists.txt)**:
```cmake
cmake_minimum_required(VERSION 3.14)
project(MyProject)

# Fetch Google Test
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/v1.14.0.zip
)
FetchContent_MakeAvailable(googletest)

enable_testing()

# Test executable
add_executable(unit_tests
    tests/unit/test_core.cpp
    tests/unit/test_utils.cpp
    src/core.cpp
    src/utils.cpp
)

target_include_directories(unit_tests PRIVATE
    src
    tests/fixtures
)

target_link_libraries(unit_tests
    GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(unit_tests)
```

### Step 5: Create Test Utilities

Implement shared test utilities for each language:

**Python (tests/helpers/assertions.py)**:
```python
"""Custom assertion helpers."""

def assert_valid_email(email: str):
    """Assert that a string is a valid email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    assert re.match(pattern, email), f"Invalid email format: {email}"

def assert_datetime_recent(dt, max_seconds=60):
    """Assert that a datetime is within the last N seconds."""
    from datetime import datetime, timedelta
    now = datetime.now()
    delta = now - dt
    assert delta < timedelta(seconds=max_seconds), \
        f"Datetime {dt} is not recent"
```

**JavaScript (tests/helpers/testUtils.js)**:
```javascript
/**

 * Test utility functions
 */

export function createMockUser(overrides = {}) {
  return {
    id: 1,
    username: 'testuser',
    email: 'test@example.com',
    ...overrides
  };
}

export function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function assertEmailFormat(email) {
  const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  expect(email).toMatch(pattern);
}
```

**Java (TestDataFactory.java)**:
```java
package com.example.fixtures;

import java.util.concurrent.atomic.AtomicInteger;

public class TestDataFactory {
    private static final AtomicInteger counter = new AtomicInteger(0);

    public static User createUser() {
        int id = counter.incrementAndGet();
        return new User(
            id,
            "user_" + id,
            "user" + id + "@test.com"
        );
    }

    public static User createUser(String username) {
        int id = counter.incrementAndGet();
        return new User(id, username, username + "@test.com");
    }

    public static void reset() {
        counter.set(0);
    }
}
```

**C# (TestUtilities.cs)**:
```csharp
namespace MyProject.Tests.Helpers
{
    public static class TestUtilities
    {
        private static int _counter = 0;

        public static User CreateUser(string username = null)
        {
            _counter++;
            return new User
            {
                Id = _counter,
                Username = username ?? $"user_{_counter}",
                Email = $"user{_counter}@test.com"
            };
        }

        public static void Reset()
        {
            _counter = 0;
        }

        public static void AssertValidEmail(string email)
        {
            var pattern = @"^[^@\s]+@[^@\s]+\.[^@\s]+$";
            Assert.Matches(pattern, email);
        }
    }
}
```

**Go (fixtures/fixtures.go)**:
```go
package fixtures

import "sync/atomic"

var counter int64

type User struct {
    ID       int64
    Username string
    Email    string
}

func CreateUser() User {
    id := atomic.AddInt64(&counter, 1)
    return User{
        ID:       id,
        Username: fmt.Sprintf("user_%d", id),
        Email:    fmt.Sprintf("user%d@test.com", id),
    }
}

func CreateUserWithUsername(username string) User {
    id := atomic.AddInt64(&counter, 1)
    return User{
        ID:       id,
        Username: username,
        Email:    fmt.Sprintf("%s@test.com", username),
    }
}

func Reset() {
    atomic.StoreInt64(&counter, 0)
}
```

**C (test_fixtures.c)**:
```c
#include "test_fixtures.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

static int counter = 0;

User* create_test_user(void) {
    counter++;
    User* user = malloc(sizeof(User));
    user->id = counter;
    sprintf(user->username, "user_%d", counter);
    sprintf(user->email, "user%d@test.com", counter);
    return user;
}

void free_test_user(User* user) {
    free(user);
}

void reset_counter(void) {
    counter = 0;
}
```

**C++ (test_fixtures.hpp)**:
```cpp
#pragma once
#include <string>
#include <memory>

namespace TestFixtures {

class UserFactory {
private:
    static int counter;

public:
    static std::unique_ptr<User> createUser() {
        counter++;
        return std::make_unique<User>(
            counter,
            "user_" + std::to_string(counter),
            "user" + std::to_string(counter) + "@test.com"
        );
    }

    static std::unique_ptr<User> createUser(const std::string& username) {
        counter++;
        return std::make_unique<User>(
            counter,
            username,
            username + "@test.com"
        );
    }

    static void reset() {
        counter = 0;
    }
};

}  // namespace TestFixtures
```

### Step 6: Set Up Test Execution

Configure how tests are run:

**Python**:
```bash
# Run all tests
pytest

# Run specific test types
pytest tests/unit
pytest -m unit
pytest -m "unit and not slow"

# Run with coverage
pytest --cov=src --cov-report=html

# Run in parallel
pytest -n auto

# Run and stop at first failure
pytest -x

# Run verbose
pytest -v -s
```

**JavaScript**:
```bash
# Run all tests
npm test

# Run in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage

# Run specific test
npm test -- core.test.js

# Run in debug mode
node --inspect-brk node_modules/.bin/jest --runInBand
```

**Java**:
```bash
# Run all tests
mvn test

# Run specific test class
mvn test -Dtest=CoreTest

# Run with coverage
mvn test jacoco:report

# Run in parallel
mvn test -DforkCount=4
```

**C#**:
```bash
# Run all tests
dotnet test

# Run specific test
dotnet test --filter "FullyQualifiedName~CoreTests"

# Run with coverage
dotnet test /p:CollectCoverage=true

# Run verbose
dotnet test --logger "console;verbosity=detailed"
```

**Go**:
```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run specific package
go test ./internal/core

# Run with race detection
go test -race ./...

# Run verbose
go test -v ./...

# Run specific test
go test -run TestCore ./internal/core
```

**C**:
```bash
# Build and run tests
mkdir build && cd build
cmake ..
make
ctest

# Run with verbose output
ctest --verbose

# Run specific test
ctest -R TestCore
```

**C++**:
```bash
# Build and run tests
mkdir build && cd build
cmake ..
cmake --build .
ctest

# Run with Google Test options
./unit_tests --gtest_filter=CoreTest.*

# Run with output
./unit_tests --gtest_print_time=1
```

## Common Patterns

### Pattern 1: Test Naming Convention

**Python**:
```python
# Format: test_[unit]_[scenario]_[expected_behavior]
def test_user_creation_with_valid_data_succeeds():
    pass

def test_user_creation_with_invalid_email_raises_error():
    pass
```

**JavaScript**:
```javascript
// Format: describe what, test scenario
describe('User creation', () => {
  test('succeeds with valid data', () => {});
  test('fails with invalid email', () => {});
});
```

**Java**:
```java
// Format: methodName_scenario_expectedBehavior
@Test
public void createUser_withValidData_succeeds() {}

@Test
public void createUser_withInvalidEmail_throwsException() {}
```

### Pattern 2: Arrange-Act-Assert (AAA)

**Python**:
```python
def test_user_registration():
    # Arrange: Set up test data
    user_data = {"username": "alice", "email": "alice@test.com"}

    # Act: Execute functionality
    result = register_user(user_data)

    # Assert: Verify behavior
    assert result.success
    assert result.user.username == "alice"
```

**JavaScript**:
```javascript
test('user registration', () => {
  // Arrange
  const userData = { username: 'alice', email: 'alice@test.com' };

  // Act
  const result = registerUser(userData);

  // Assert
  expect(result.success).toBe(true);
  expect(result.user.username).toBe('alice');
});
```

### Pattern 3: Test Fixtures

**Python**:
```python
import pytest

@pytest.fixture
def user_data():
    """Provide sample user data."""
    return {"username": "testuser", "email": "test@test.com"}

def test_user_creation(user_data):
    """Test using fixture."""
    user = create_user(**user_data)
    assert user.username == user_data["username"]
```

**JavaScript**:
```javascript
describe('User tests', () => {
  let userData;

  beforeEach(() => {
    // Setup fixture before each test
    userData = { username: 'testuser', email: 'test@test.com' };
  });

  test('creates user', () => {
    const user = createUser(userData);
    expect(user.username).toBe(userData.username);
  });
});
```

## Success Criteria

- [ ] Testing framework installed and configured
- [ ] Directory structure follows language conventions
- [ ] Test discovery works correctly
- [ ] Configuration files created
- [ ] Test utilities implemented
- [ ] Naming conventions documented
- [ ] Test execution commands verified
- [ ] Coverage measurement enabled
- [ ] Parallel execution configured (if applicable)
- [ ] Documentation created for team

## Related Skills

- [`test-driven-development`](../test-driven-development/SKILL.md) - Write tests first, then code
- [`generate-test-cases`](../generate-test-cases/SKILL.md) - Create comprehensive test cases
- [`create-mocks-fixtures`](../create-mocks-fixtures/SKILL.md) - Implement mocking and fixtures
- [`analyze-code-coverage`](../analyze-code-coverage/SKILL.md) - Measure and improve coverage
- [`setup-ci-cd-testing`](../setup-ci-cd-testing/SKILL.md) - Integrate tests into CI/CD

## Additional Resources

### Framework Documentation
- **Python**: [pytest](https://docs.pytest.org/), [unittest](https://docs.python.org/3/library/unittest.html)
- **JavaScript**: [Jest](https://jestjs.io/), [Vitest](https://vitest.dev/)
- **Java**: [JUnit 5](https://junit.org/junit5/), [TestNG](https://testng.org/)
- **C#**: [xUnit](https://xunit.net/), [NUnit](https://nunit.org/)
- **Go**: [testing](https://pkg.go.dev/testing), [testify](https://github.com/stretchr/testify)
- **C**: [Unity](https://github.com/ThrowTheSwitch/Unity), [Check](https://libcheck.github.io/check/)
- **C++**: [Google Test](https://google.github.io/googletest/), [Catch2](https://github.com/catchorg/Catch2)

### Best Practices
- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Testing Best Practices](https://testingjavascript.com/)
- [Unit Testing Principles](https://www.artofunittesting.com/)

---

**Version**: 1.0.0
**Last Updated**: January 2025
**Based on**: Test Development Templates - Test Structure
