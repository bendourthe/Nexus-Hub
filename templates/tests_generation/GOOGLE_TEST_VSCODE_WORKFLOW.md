# Complete Workflow: Google Test + VS Code + GitHub Copilot

This guide provides a complete end-to-end workflow for setting up C++ unit testing with Google Test, integrated with VS Code and GitHub Copilot for automated test generation. Follow these steps to go from project initialization to comprehensive test coverage in ~10 minutes.

---

## Table of Contents

1. [Prerequisites](#prerequisites)

2. [Workflow Step-by-Step](#workflow-step-by-step)

3. [Troubleshooting](#troubleshooting)

4. [Next Steps](#next-steps)

---

## Prerequisites

### Required Tools

| Tool | Purpose | Minimum Version |
|------|---------|----------------|
| VS Code | IDE | Latest |
| CMake | Build system | 3.15+ |
| Ninja | Build generator | Latest |
| C++ Compiler | Code compilation | GCC 7+, Clang 5+, MSVC 2019+ |
| Git | Version control | 2.0+ |

### VS Code Extensions

Install these extensions for full functionality:

**Essential**:

- **CMake Tools** (`twxs.cmake`) - CMake integration

- **C/C++** (`ms-vscode.cpptools`) - C++ language support and IntelliSense

- **C/C++ Extension Pack** (`ms-vscode.cpptools-extension-pack`) - Complete C++ toolkit

**Recommended**:

- **Test Explorer UI** (`hbenl.vscode-test-explorer`) - Graphical test runner interface

- **C++ TestMate** (`matepek.vscode-catch2-test-adapter`) - Google Test integration for Test Explorer

- **GitHub Copilot** (`GitHub.copilot`) - AI-powered code generation

**Optional**:

- **clangd** (`llvm-vs-code-extensions.vscode-clangd`) - Alternative IntelliSense engine

- **CodeLLDB** (`vadimcn.vscode-lldb`) - Advanced LLVM debugger for Mac/Linux

- **CMake** (`twxs.cmake`) - CMake language support and syntax highlighting

### Installation Commands

#### Linux (Ubuntu/Debian)
```bash
# Update package list
sudo apt-get update

# Install build tools
sudo apt-get install build-essential cmake ninja-build git

# Verify installations
gcc --version      # Should be 7.0+
cmake --version    # Should be 3.15+
ninja --version    # Should show version
```

#### macOS
```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install build tools
brew install cmake ninja

# Install Xcode Command Line Tools (includes clang)
xcode-select --install

# Verify installations
clang++ --version
cmake --version
ninja --version
```

#### Windows
```powershell
# Install Chocolatey if not present (run as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install build tools
choco install cmake ninja git visualstudio2022buildtools

# Verify installations (restart terminal first)
cmake --version
ninja --version
cl.exe    # Should show MSVC compiler
```

### Install VS Code Extensions

**Option 1: Via VS Code UI**

1. Open VS Code

2. Press `Ctrl+Shift+X` (Extensions view)

3. Search for and install each extension listed above

**Option 2: Via Command Line**
```bash
code --install-extension twxs.cmake
code --install-extension ms-vscode.cpptools
code --install-extension ms-vscode.cpptools-extension-pack
code --install-extension hbenl.vscode-test-explorer
code --install-extension matepek.vscode-catch2-test-adapter
code --install-extension GitHub.copilot
```

---

## Workflow Step-by-Step

### Step 1: Create New C++ Project

#### 1.1 Initialize Project Directory

```bash
# Create and enter project directory
mkdir myproject && cd myproject

# Initialize Git repository
git init
```

#### 1.2 Create Directory Structure

```bash
# Create standard C++ project structure
mkdir -p include/myapp
mkdir -p src
mkdir -p tests/unit
mkdir -p tests/integration
```

**Expected Structure**:
```
myproject/
├── include/
│   └── myapp/
│       └── Calculator.hpp
├── src/
│   ├── CMakeLists.txt
│   └── Calculator.cpp
├── tests/
│   ├── CMakeLists.txt
│   └── unit/
│       └── CalculatorTest.cpp
├── .gitignore
└── CMakeLists.txt
```

#### 1.3 Create .gitignore

```bash
cat > .gitignore << 'EOF'
# Build directories
build/
cmake-build-*/

# IDE directories
.vscode/
.idea/

# Compiled files
*.o
*.a
*.so
*.exe

# CMake
CMakeCache.txt
CMakeFiles/
compile_commands.json

# Coverage
*.gcov
*.gcda
*.gcno
coverage/

# OS files
.DS_Store
Thumbs.db
EOF
```

---

### Step 2: Initialize CMake Project

#### 2.1 Root CMakeLists.txt

Create `CMakeLists.txt` in project root:

```cmake
cmake_minimum_required(VERSION 3.15)
project(MyApp VERSION 1.0.0 LANGUAGES CXX)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile commands for IntelliSense
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Fetch Google Test using FetchContent (no system installation needed)
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)

# Force shared CRT on Windows
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)

# Make Google Test available
FetchContent_MakeAvailable(googletest)

# Enable testing
enable_testing()
include(CTest)

# Add subdirectories
add_subdirectory(src)
add_subdirectory(tests)
```

**Key Points**:

- **FetchContent**: Downloads Google Test automatically (no manual installation)

- **v1.14.0**: Latest stable Google Test version

- **CMAKE_EXPORT_COMPILE_COMMANDS**: Required for VS Code IntelliSense

- **enable_testing()**: Activates CTest integration

#### 2.2 Source Directory CMakeLists.txt

Create `src/CMakeLists.txt`:

```cmake
# Create library from source files
add_library(myapp_lib
    Calculator.cpp
)

# Specify include directories
target_include_directories(myapp_lib PUBLIC
    ${CMAKE_SOURCE_DIR}/include
)

# Optional: Create executable if needed
# add_executable(myapp main.cpp)
# target_link_libraries(myapp PRIVATE myapp_lib)
```

#### 2.3 Tests Directory CMakeLists.txt

Create `tests/CMakeLists.txt`:

```cmake
include(GoogleTest)

# Helper function to create test executables
function(add_gtest TEST_NAME)
    # Parse arguments (supports multiple source files)
    cmake_parse_arguments(ARG "" "" "SOURCES" ${ARGN})

    # If no SOURCES specified, use ARGN directly
    if(NOT ARG_SOURCES)
        set(ARG_SOURCES ${ARGN})
    endif()

    # Create test executable
    add_executable(${TEST_NAME} ${ARG_SOURCES})

    # Include project headers
    target_include_directories(${TEST_NAME} PRIVATE
        ${CMAKE_SOURCE_DIR}/include
    )

    # Link against libraries
    target_link_libraries(${TEST_NAME} PRIVATE
        myapp_lib              # Project library
        GTest::gtest_main      # Google Test main function
        GTest::gmock           # Google Mock
    )

    # Discover tests automatically
    gtest_discover_tests(${TEST_NAME}
        WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
        PROPERTIES LABELS "unit"
    )
endfunction()

# Add test executables
add_gtest(test_calculator unit/CalculatorTest.cpp)
```

**Key Points**:

- **add_gtest()**: Reusable function for adding tests

- **gtest_discover_tests()**: Automatically finds all TEST() macros

- **GTest::gtest_main**: Provides main() function (no need to write it)

- **GTest::gmock**: Required for mocking capabilities

---

### Step 3: Copy VS Code Configuration

#### 3.1 Copy Configuration Files

```bash
# Copy .vscode configurations from AI Templates repository
mkdir -p .vscode
cp path/to/ai-templates/templates/tests_generation/vscode_config/*.json .vscode/
```

**Or create manually**:

- [tasks.json](vscode_config/tasks.json) - Build and test tasks

- [launch.json](vscode_config/launch.json) - Debugging configurations

- [settings.json](vscode_config/settings.json) - CMake Tools and IntelliSense

- [c_cpp_properties.json](vscode_config/c_cpp_properties.json) - Platform-specific includes

See [VS Code Config README](vscode_config/README.md) for detailed explanations.

#### 3.2 Verify Configuration

Your `.vscode/` directory should contain:
```
.vscode/
├── tasks.json
├── launch.json
├── settings.json
└── c_cpp_properties.json
```

---

### Step 4: Open in VS Code

#### 4.1 Open Project

```bash
# Open project in VS Code
code .
```

**VS Code will automatically**:

1. Detect CMake project

2. Prompt: "Would you like to configure this project?" → Click **Yes**

3. Prompt: "Select a kit" → Choose your compiler (e.g., **GCC 11.4.0**)

#### 4.2 Verify Setup

**Check Bottom Status Bar**:

- Should show: `[Ninja] Debug` (build type)

- CMake icon should be clickable

- Kit should show your selected compiler

**Check Output Panel**:

- Press `Ctrl+Shift+U` (View Output)

- Select "CMake/Build" from dropdown

- Should show: "Configuring done" and "Generating done"

**Verify Build Directory**:
```bash
ls build/
# Should contain: CMakeCache.txt, compile_commands.json, _deps/googletest-src/
```

---

### Step 5: Generate Tests with GitHub Copilot

#### 5.1 Write Initial Class

Create `include/myapp/Calculator.hpp`:

```cpp
#pragma once

class Calculator {
public:
    static int add(int a, int b);
    static int subtract(int a, int b);
    static int multiply(int a, int b);
    static double divide(double a, double b);
};
```

Create `src/Calculator.cpp`:

```cpp
#include "myapp/Calculator.hpp"
#include <stdexcept>

int Calculator::add(int a, int b) {
    return a + b;
}

int Calculator::subtract(int a, int b) {
    return a - b;
}

int Calculator::multiply(int a, int b) {
    return a * b;
}

double Calculator::divide(double a, double b) {
    if (b == 0.0) {
        throw std::invalid_argument("Division by zero");
    }
    return a / b;
}
```

#### 5.2 Open GitHub Copilot Chat

**Keyboard Shortcut**:

- **Windows/Linux**: `Ctrl+Shift+I`

- **Mac**: `Cmd+Shift+I`

**Alternative**:

- Click Copilot icon in Activity Bar (left sidebar)

- Select "Open Chat"

#### 5.3 Paste Comprehensive Test Generation Prompt

**Copy/Paste This Prompt**:

```
Generate comprehensive Google Test unit tests for the Calculator class.

Requirements:

- Use TEST() macro for simple function tests (no fixtures needed for stateless functions)

- Follow AAA pattern (Arrange-Act-Assert) in every test

- Include these test cases:

  * add(): Test positive numbers, negative numbers, zero, boundary values (INT_MAX, INT_MIN)

  * subtract(): Test positive results, negative results, zero, boundary values

  * multiply(): Test positive, negative, zero, overflow scenarios

  * divide(): Test positive division, negative division, floating-point precision, divide-by-zero exception

- Use appropriate assertions:

  * EXPECT_EQ for integer comparisons

  * EXPECT_THROW(expression, std::invalid_argument) for exception testing

  * EXPECT_NEAR(actual, expected, tolerance) for floating-point comparisons (tolerance 0.0001)

- Follow FIRST principles (Fast, Independent, Repeatable, Self-validating, Timely)

- Each test should be independent and not rely on execution order

File location: tests/unit/CalculatorTest.cpp

Example test structure:
```cpp
TEST(CalculatorTest, AddPositiveNumbers) {
    // Arrange
    int a = 5;
    int b = 3;

    // Act
    int result = Calculator::add(a, b);

    // Assert
    EXPECT_EQ(result, 8);
}
```

Generate at least 15 comprehensive tests covering all public methods and edge cases.
```

#### 5.4 Review Generated Tests

Copilot will generate `CalculatorTest.cpp` with approximately:

- 15-20 test cases

- Proper includes (`#include <gtest/gtest.h>`, `#include "myapp/Calculator.hpp"`)

- Correct Google Test syntax

- AAA pattern structure

- Boundary value tests

- Exception tests

**Example Output**:
```cpp
#include <gtest/gtest.h>
#include "myapp/Calculator.hpp"
#include <limits>

TEST(CalculatorTest, AddPositiveNumbers) {
    EXPECT_EQ(Calculator::add(5, 3), 8);
}

TEST(CalculatorTest, AddNegativeNumbers) {
    EXPECT_EQ(Calculator::add(-5, -3), -8);
}

TEST(CalculatorTest, DivideByZeroThrowsException) {
    EXPECT_THROW(Calculator::divide(10.0, 0.0), std::invalid_argument);
}

TEST(CalculatorTest, DivideFloatingPointPrecision) {
    double result = Calculator::divide(1.0, 3.0);
    EXPECT_NEAR(result, 0.333333, 0.0001);
}

// ... 11+ more tests
```

#### 5.5 Accept and Save

1. Review generated code in Copilot chat window

2. Click **"Insert at Cursor"** or **"Copy"**

3. Create `tests/unit/CalculatorTest.cpp` if not already created

4. Paste code

5. Save file (`Ctrl+S`)

---

### Step 6: Build Tests

#### Option A: VS Code Command Palette (Recommended)

1. Press `Ctrl+Shift+P`

2. Type "CMake: Build"

3. Press Enter

**Expected Output**:
```
[build] [2/2] Linking CXX executable test_calculator
[build] Build finished with exit code 0
```

#### Option B: Keyboard Shortcut

1. Press `Ctrl+Shift+B`

2. Select **"CMake: Build Tests"** (should be default)

#### Option C: Terminal

```bash
cmake --build build
```

#### Verify Build Success

Check `build/` directory:
```bash
ls build/test_*
# Should show: test_calculator (or test_calculator.exe on Windows)
```

---

### Step 7: Run Tests

#### Option A: VS Code Tasks (Recommended)

1. Press `Ctrl+Shift+P`

2. Type "Tasks: Run Test Task"

3. Select **"Run All Tests"**

**Expected Output**:
```
[ctest] Test project C:/Users/username/myproject/build
[ctest]     Start 1: CalculatorTest.AddPositiveNumbers
[ctest] 1/15 Test  #1: CalculatorTest.AddPositiveNumbers ............   Passed    0.01 sec
[ctest]     Start 2: CalculatorTest.AddNegativeNumbers
[ctest] 2/15 Test  #2: CalculatorTest.AddNegativeNumbers ............   Passed    0.01 sec
[ctest] ...
[ctest] 100% tests passed, 0 tests failed out of 15
[ctest]
[ctest] Total Test time (real) =   0.15 sec
```

#### Option B: Terminal

```bash
cd build
ctest --output-on-failure
```

**Alternative with Verbose Output**:
```bash
ctest --verbose
```

#### Option C: Test Explorer UI

1. Open Test Explorer view (beaker icon in Activity Bar)

2. Tests should automatically appear in tree view

3. Click play button (▶) to run all tests

4. Click individual test to run specific test

---

### Step 8: Debug Failing Tests

#### 8.1 Set Breakpoints

1. Open `tests/unit/CalculatorTest.cpp`

2. Click in the gutter (left of line numbers) on the line where you want to pause

3. Red dot should appear (breakpoint)

#### 8.2 Start Debugging

**Method 1: F5 Keyboard Shortcut**

1. Press `F5`

2. VS Code prompts: "Select configuration"

3. Choose **"Debug Current Test Binary"**

4. Enter test binary name (e.g., "calculator")

5. Enter GTest filter (e.g., "*" for all or "CalculatorTest.Divide*" for specific)

**Method 2: Debug from Test Explorer**

1. Right-click test in Test Explorer

2. Select "Debug Test"

**Method 3: Launch Configuration**

1. Press `Ctrl+Shift+D` (Debug view)

2. Select "Debug Current Test Binary" from dropdown

3. Click green play button

#### 8.3 Debug Controls

**Keyboard Shortcuts**:

- `F5` - Continue execution

- `F10` - Step Over (execute current line)

- `F11` - Step Into (enter function call)

- `Shift+F11` - Step Out (exit current function)

- `Ctrl+Shift+F5` - Restart debugging

- `Shift+F5` - Stop debugging

**Debug Panel Features**:

- **Variables**: Inspect local variables and parameters

- **Watch**: Monitor specific expressions

- **Call Stack**: View function call hierarchy

- **Breakpoints**: Manage all breakpoints

#### 8.4 Debugging Specific Test

If you want to debug only `CalculatorTest.DivideByZero`:

**Option 1: GTest Filter**

1. Start debugging (F5)

2. Enter filter: `CalculatorTest.DivideByZero`

**Option 2: Run from Command Line**
```bash
./build/test_calculator --gtest_filter=CalculatorTest.DivideByZero
```

---

### Step 9: Generate Additional Tests Iteratively

Use Copilot to incrementally improve test coverage.

#### 9.1 Add Parametrized Tests

**Prompt Copilot**:
```
Add parametrized tests for Calculator::add using TEST_P and INSTANTIATE_TEST_SUITE_P.
Test these value pairs:

- (1, 2) → 3

- (0, 0) → 0

- (-5, 5) → 0

- (INT_MAX, 0) → INT_MAX

- (-1, -1) → -2

Use std::tuple<int, int, int> where the third value is expected result.
```

**Copilot Generates**:
```cpp
class CalculatorAddParamTest : public ::testing::TestWithParam<std::tuple<int, int, int>> {};

TEST_P(CalculatorAddParamTest, AddParametrized) {
    auto [a, b, expected] = GetParam();
    int result = Calculator::add(a, b);
    EXPECT_EQ(result, expected);
}

INSTANTIATE_TEST_SUITE_P(
    AddTests,
    CalculatorAddParamTest,
    ::testing::Values(
        std::make_tuple(1, 2, 3),
        std::make_tuple(0, 0, 0),
        std::make_tuple(-5, 5, 0),
        std::make_tuple(std::numeric_limits<int>::max(), 0, std::numeric_limits<int>::max()),
        std::make_tuple(-1, -1, -2)
    )
);
```

#### 9.2 Add Fixture-Based Tests

If Calculator becomes stateful (e.g., memory feature), prompt:

```
Refactor tests to use TEST_F with CalculatorTestFixture.
Move Calculator initialization to SetUp() method.
Add member variable: std::unique_ptr<Calculator> calculator_.
Convert existing TEST() to TEST_F.
```

#### 9.3 Add Mock Integration

For a class that depends on Calculator:

**Prompt**:
```
Create Google Mock for Calculator interface.
Assume Calculator is now an interface with virtual methods.
Generate MockCalculator class with MOCK_METHOD macros.
Create tests for ScientificCalculator class that uses Calculator.
Verify ScientificCalculator calls Calculator::add correctly using EXPECT_CALL.
```

---

### Step 10: Generate Code Coverage Report

#### 10.1 Enable Coverage in CMake

Update root `CMakeLists.txt` to add coverage support:

```cmake
# Add after project() declaration
option(ENABLE_COVERAGE "Enable code coverage" OFF)

if(ENABLE_COVERAGE AND CMAKE_BUILD_TYPE MATCHES Debug)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
        add_compile_options(--coverage -fprofile-arcs -ftest-coverage)
        add_link_options(--coverage)
    endif()
endif()
```

Add coverage target in `tests/CMakeLists.txt`:

```cmake
# Add at end of file
if(ENABLE_COVERAGE)
    find_program(LCOV lcov)
    find_program(GENHTML genhtml)

    if(LCOV AND GENHTML)
        add_custom_target(coverage
            COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/coverage
            COMMAND ${LCOV} --capture --directory . --output-file coverage.info
            COMMAND ${LCOV} --remove coverage.info '/usr/*' '*/googletest/*' --output-file coverage.info
            COMMAND ${GENHTML} coverage.info --output-directory ${CMAKE_BINARY_DIR}/coverage
            WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
            COMMENT "Generating code coverage report"
        )
    endif()
endif()
```

#### 10.2 Build with Coverage

```bash
# Reconfigure with coverage enabled
cmake -B build -DCMAKE_BUILD_TYPE=Debug -DENABLE_COVERAGE=ON

# Build tests
cmake --build build

# Run tests to generate coverage data
cd build
ctest

# Generate coverage report
cmake --build . --target coverage
```

#### 10.3 View Coverage Report

**Linux/Mac**:
```bash
open build/coverage/index.html
```

**Windows**:
```bash
start build/coverage/index.html
```

#### 10.4 Generate More Tests for Uncovered Code

After viewing coverage report, identify uncovered lines (e.g., Calculator.cpp lines 42-48).

**Prompt Copilot**:
```
Generate tests for Calculator.cpp lines 42-48 (multiply method edge cases).
Coverage report shows these lines are uncovered. Add tests for:

- Multiplication resulting in zero

- Negative number multiplication

- Overflow detection (INT_MAX * 2 should be handled)

Use parametrized tests if appropriate.
```

---

## Troubleshooting

### Issue 1: CMake Configuration Fails

**Symptom**:
```
CMake Error: Could not create named generator Ninja
```

**Solution**:
```bash
# Verify Ninja is installed
ninja --version

# If not installed:
# Linux: sudo apt-get install ninja-build
# Mac: brew install ninja
# Windows: choco install ninja

# Clean build directory and retry
rm -rf build/
cmake -B build -G Ninja
```

---

### Issue 2: Google Test Not Found

**Symptom**:
```
CMake Error: Could not find googletest
```

**Solution**:

CMake FetchContent should download automatically. If it fails:

```bash
# Clear CMake cache
rm -rf build/_deps/

# Reconfigure (will re-download)
cmake -B build

# If still fails, check internet connection or use manual download:
cd build
git clone https://github.com/google/googletest.git _deps/googletest-src
```

---

### Issue 3: IntelliSense Shows Errors for Google Test Headers

**Symptom**:
Red squiggly lines under `#include <gtest/gtest.h>`

**Solution**:

1. Ensure CMake has run at least once:
   ```bash
   cmake -B build
   ```

2. Verify `build/_deps/googletest-src/` exists:
   ```bash
   ls build/_deps/googletest-src/googletest/include/gtest/
   ```

3. Check `c_cpp_properties.json` has correct paths:
   ```json
   "includePath": [
       "${workspaceFolder}/build/_deps/googletest-src/googletest/include"
   ]
   ```

4. Reload VS Code window:

   - Press `Ctrl+Shift+P`

   - Type "Developer: Reload Window"

   - Press Enter

5. If still not working, manually set include path:

   - Open Command Palette: `Ctrl+Shift+P`

   - Type "C/C++: Edit Configurations (JSON)"

   - Add Google Test paths to `includePath`

---

### Issue 4: Tests Don't Appear in Test Explorer

**Symptom**:
Test Explorer is empty after building

**Solution**:

1. Install required extensions:
   ```bash
   code --install-extension hbenl.vscode-test-explorer
   code --install-extension matepek.vscode-catch2-test-adapter
   ```

2. Build tests first:
   ```bash
   cmake --build build
   ```

3. Update `.vscode/settings.json`:
   ```json
   "testMate.cpp.test.advancedExecutables": [
       {
           "pattern": "build/test_*",
           "cwd": "${workspaceFolder}",
           "env": {}
       }
   ]
   ```

4. Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"

5. Manually refresh Test Explorer:

   - Click beaker icon (Test Explorer)

   - Click refresh icon at top

---

### Issue 5: Debugger Doesn't Start

**Symptom**:
Pressing F5 shows error: "Unable to start debugging"

**Solution**:

**Linux**:
```bash
# Install GDB
sudo apt-get install gdb

# Verify
gdb --version
```

**Mac**:
```bash
# Install Xcode Command Line Tools (includes lldb)
xcode-select --install

# Update launch.json to use lldb instead of gdb
# Change "MIMode": "gdb" to "MIMode": "lldb"
```

**Windows**:
```powershell
# Install Visual Studio Build Tools (includes MSVC debugger)
choco install visualstudio2022buildtools

# Update launch.json for Windows:
# Change "type": "cppdbg" to "type": "cppvsdbg"
# Change "program" path to include ".exe"
```

**Verify Test Binary Exists**:
```bash
ls build/test_*
# Should show test executables
```

---

### Issue 6: Build Fails with "Ninja not found"

**Symptom**:
```
CMake Error: CMake was unable to find a build program corresponding to "Ninja"
```

**Solution**:

**Option 1: Install Ninja**
```bash
# Linux: sudo apt-get install ninja-build
# Mac: brew install ninja
# Windows: choco install ninja
```

**Option 2: Change Generator**

Update `tasks.json` and `.vscode/settings.json`:

```json
// tasks.json
"-G", "Unix Makefiles"  // Instead of Ninja (Linux/Mac)
"-G", "Visual Studio 17 2022"  // Instead of Ninja (Windows)

// settings.json
"cmake.generator": "Unix Makefiles"  // Instead of Ninja
```

---

### Issue 7: Copilot Generates Invalid Code

**Symptom**:
Tests don't compile after generation

**Solution**:

**Prompt Copilot to Fix**:
```
Fix compilation errors in test_calculator.cpp.
Show all required include statements.
Ensure namespace declarations are correct (use ::testing:: not testing::).
```

**Common Issues Copilot Will Fix**:

- Missing `#include <gtest/gtest.h>` or `#include <gmock/gmock.h>`

- Incorrect namespace (`testing::Test` should be `::testing::Test`)

- Missing `#include <limits>` for `std::numeric_limits`

- Missing `#include <stdexcept>` for `std::invalid_argument`

- Type mismatches in EXPECT_EQ (e.g., comparing `int` with `double`)

---

### Issue 8: Tests Pass Locally But Fail in CI

**Symptom**:
Tests pass on your machine but fail in GitHub Actions or other CI

**Common Causes**:

1. **Timing Issues**: Tests depend on execution speed

   - **Solution**: Add timeouts or use mocks for time-dependent code

2. **File System Paths**: Hard-coded absolute paths

   - **Solution**: Use `CMAKE_SOURCE_DIR` or relative paths

3. **Random Test Order**: Tests depend on execution order

   - **Solution**: Make tests independent (FIRST principles)

4. **Environment Variables**: Missing env vars in CI

   - **Solution**: Set env vars in CI config or use defaults in code

5. **Compiler Differences**: Different compilers in CI

   - **Solution**: Test locally with same compiler (e.g., use Docker)

**Debug in CI**:
```yaml
# .github/workflows/test.yml
- name: Run tests with verbose output
  run: |
    cd build
    ctest --verbose --output-on-failure
```

---

## Next Steps

### Expand Testing

1. **Integration Tests**: Add `tests/integration/` directory
   ```
   Prompt Copilot: "Create integration tests for Calculator with FileManager.
   Test saving and loading calculation history to file."
   ```

2. **Performance Tests**: Add benchmarks
   ```
   Prompt Copilot: "Add Google Benchmark tests for Calculator::multiply.
   Measure throughput with 1 million iterations."
   ```

3. **Fuzz Testing**: Add fuzzing for edge cases
   ```bash
   # Using libFuzzer
   clang++ -fsanitize=fuzzer,address -g CalculatorFuzz.cpp -o fuzz_calculator
   ./fuzz_calculator
   ```

---

### CI/CD Integration

1. **GitHub Actions**: Copy workflow from templates
   ```bash
   mkdir -p .github/workflows
   cp path/to/ai-templates/templates/tests_generation/maintenance_cicd/.github/workflows/cpp-tests.yml .github/workflows/
   ```

2. **Pre-Commit Hooks**: Run tests before commit
   ```bash
   # .git/hooks/pre-commit
   #!/bin/bash
   cmake --build build && cd build && ctest --output-on-failure
   ```

3. **Coverage Reporting**: Integrate with Codecov or Coveralls
   ```yaml
   # .github/workflows/test.yml
   - name: Upload coverage
     uses: codecov/codecov-action@v3
     with:
       files: build/coverage.info
   ```

---

### Advanced Testing Patterns

1. **Fixture Hierarchies**: Complex setup with inheritance
   ```
   Prompt Copilot: "Create fixture hierarchy for Calculator tests.
   Base fixture: CalculatorTestBase with common setup.
   Derived fixtures: BasicArithmeticTests, AdvancedOperationsTests."
   ```

2. **Custom Matchers**: Domain-specific assertions
   ```
   Prompt Copilot: "Create custom Google Test matcher for Calculator results.
   Matcher should verify result is within 1% tolerance."
   ```

3. **Death Tests**: Verify program crashes correctly
   ```
   Prompt Copilot: "Add death tests for Calculator using EXPECT_DEATH.
   Verify assertion fires when adding INT_MAX + 1."
   ```

4. **Thread Safety Tests**: Concurrent execution
   ```
   Prompt Copilot: "Add thread safety tests for Calculator.
   Use std::thread to call add() from multiple threads simultaneously.
   Verify thread-safe behavior."
   ```

---

### Documentation

1. **Generate Test Documentation**
   ```
   Prompt Copilot: "Create README.md for tests/ directory.
   Document test structure, how to run tests, and how to add new tests."
   ```

2. **Code Coverage Badge**: Add to README
   ```markdown
   ![Coverage](https://img.shields.io/codecov/c/github/username/myproject)
   ```

---

## Summary

**Complete Workflow Timeline**:

| Step | Task | Time |
|------|------|------|
| 1 | Create project structure | 2 min |
| 2 | Set up CMake configuration | 3 min |
| 3 | Copy VS Code configs | 1 min |
| 4 | Open in VS Code | 1 min |
| 5 | Generate tests with Copilot | 2 min |
| 6 | Build tests | 1 min |
| 7 | Run tests | 30 sec |
| 8 | Debug failures (if any) | Variable |
| 9 | Iterate with Copilot | Ongoing |
| 10 | Generate coverage | 2 min |

**Total Time (First Run)**: ~10-12 minutes

**Total Time (Subsequent Runs)**: ~5 minutes (steps 5-7)

---

## Additional Resources

- [CMake Documentation](https://cmake.org/documentation/)

- [Google Test Primer](https://google.github.io/googletest/primer.html)

- [Google Mock for Dummies](https://google.github.io/googletest/gmock_for_dummies.html)

- [VS Code C++ Documentation](https://code.visualstudio.com/docs/languages/cpp)

- [VS Code Debugging](https://code.visualstudio.com/docs/editor/debugging)

- [CMake Tools Extension](https://vector-of-bool.github.io/docs/vscode-cmake-tools/)

- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)

---

## Integration with Other Templates

This workflow integrates with:

- **[cpp_unit_tests.md](unit_tests/cpp_unit_tests.md)**: Comprehensive unit testing methodology

- **[COPILOT_QUICK_REFERENCE.md](unit_tests/COPILOT_QUICK_REFERENCE.md)**: One-line prompts for Copilot

- **[VS Code Config README](vscode_config/README.md)**: Detailed config explanations

- **[cpp_test_structure.md](test_structure/cpp_test_structure.md)**: Test project architecture

- **[cpp_mocks_fixtures.md](mocks_fixtures/cpp_mocks_fixtures.md)**: Advanced mocking patterns

---

*For issues or questions, see [Troubleshooting](#troubleshooting) section or consult the individual template documentation.*
