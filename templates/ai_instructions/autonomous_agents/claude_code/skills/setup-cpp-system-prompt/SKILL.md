---
name: setup-cpp-system-prompt
description: Configure comprehensive C++ development system prompt for Claude Code with modern C++ features, RAII, smart pointers, and exception safety best practices
version: 1.0.0
author: Benjamin Dourthe
language: C++
category: Configuration
tags: [cpp, c++, setup, system-prompt, configuration, modern-cpp, standards, raii]
priority: HIGH
---

# Setup C++ System Prompt

Configure Claude Code with comprehensive modern C++ development standards, best practices, and workflows optimized for production-quality C++ code generation with C++17/C++20 features.

## When to Use This Skill

Use this skill when you need to:
- Set up a new C++ project with Claude Code
- Configure Claude Code for modern C++ development (C++17/C++20/C++23)
- Apply comprehensive C++ development standards and Core Guidelines
- Establish consistent coding practices for C++ projects
- Optimize Claude Code for C++ library development
- Implement RAII, smart pointers, and exception safety
- Develop high-performance C++ applications
- Create header-only or template-heavy libraries

## What This Skill Does

This skill helps you configure Claude Code with:

1. **Modern C++ Standards**
   - C++17/C++20/C++23 features (structured bindings, concepts, ranges)
   - Smart pointer usage (unique_ptr, shared_ptr, weak_ptr)
   - RAII resource management patterns
   - Move semantics and perfect forwarding
   - Exception safety guarantees
   - Const correctness and type safety

2. **Project Architecture Guidelines**
   - Standard C++ application structure (include/, src/, tests/)
   - Header-only library structure
   - CMake-based build system (modern CMake 3.15+)
   - Static analysis configuration (.clang-format, .clang-tidy)
   - Documentation structure (README, CHANGELOG, DEVLOG, Doxygen)

3. **Memory and Resource Safety**
   - Automatic resource management (RAII)
   - Smart pointers instead of raw owning pointers
   - Exception safety (basic, strong, no-throw guarantees)
   - Move semantics for efficiency
   - No manual memory management (no naked new/delete)

4. **Testing Framework**
   - GoogleTest integration (gtest, gmock)
   - Catch2 as alternative
   - Test structure and patterns
   - Parameterized tests
   - Death tests and fixtures
   - Performance benchmarking

5. **Template Programming**
   - Template best practices
   - Concepts for constraints (C++20)
   - SFINAE and type traits
   - Perfect forwarding
   - Variadic templates
   - Template specialization

6. **Development Workflow**
   - Task breakdown methodology
   - Iterative testing protocol
   - Quality gates and checklists
   - Version control best practices
   - Static analysis integration

## Prerequisites

- Claude Code installed and configured
- C++ compiler installed:
  - GCC 9.0+ or Clang 10.0+ (C++17 support)
  - GCC 11+ or Clang 13+ (C++20 support)
  - MSVC 2019+ (Windows)
- CMake 3.15+ for build system
- Basic understanding of C++ development
- Project directory created (or ready to create new project)
- Optional: GoogleTest, Doxygen, clang-tidy

## Instructions

### Step 1: Choose System Prompt Version

Decide between two versions based on your needs:

**Comprehensive Version (~40k tokens)**
- Best for: Complex projects, libraries, template-heavy code, performance-critical applications
- Features: Complete architectural guidance, modern C++ patterns, template metaprogramming, STL best practices
- Token count: ~40,000 tokens
- Use cases: Production libraries, high-performance systems, template libraries, frameworks
- File: `agent_prompts/autonomous_agents/claude_code/cpp/CLAUDE_comprehensive_40k.md`

**Condensed Version (~20k tokens)**
- Best for: Quick development, CLI tools, prototyping, learning projects
- Features: Essential modern C++ guidelines, core best practices, streamlined workflow
- Token count: ~20,000 tokens
- Use cases: Utility programs, tools, applications, proof-of-concepts
- File: `agent_prompts/autonomous_agents/claude_code/cpp/CLAUDE_condensed_20k.md`

### Step 2: Configure Claude Code

There are two methods to configure Claude Code with the C++ system prompt:

#### Method A: Project-Level CLAUDE.md (Recommended)

1. Navigate to your project root directory
2. Copy the chosen system prompt file to `CLAUDE.md`:
   ```bash
   # For comprehensive version (libraries/production)
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/cpp/CLAUDE_comprehensive_40k.md ./CLAUDE.md

   # For condensed version (tools/prototypes)
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/cpp/CLAUDE_condensed_20k.md ./CLAUDE.md
   ```
3. Claude Code will automatically detect and load this file

#### Method B: Session-Based Configuration

Start Claude Code with the system prompt:
```bash
# For comprehensive version
claude --system-prompt ./path/to/CLAUDE_comprehensive_40k.md

# For condensed version
claude --system-prompt ./path/to/CLAUDE_condensed_20k.md
```

### Step 3: Verify Configuration

Test that the system prompt is active by asking Claude Code to:

1. **Create a modern C++ class** and observe if it follows standards:
   ```
   "Create a Buffer class with RAII and move semantics"
   ```

   Expected behavior:
   - Uses smart pointers (std::unique_ptr, std::vector)
   - Implements move constructor and move assignment
   - Rule of Zero or Rule of Five properly implemented
   - No manual memory management (no naked new/delete)
   - Exception-safe design
   - Const correctness
   - noexcept specifications on move operations

2. **Request project structure** and verify it matches standards:
   ```
   "Show me the recommended project structure for a modern C++ library"
   ```

   Expected behavior:
   - Includes include/, src/, tests/ directories
   - Shows CMakeLists.txt structure
   - Includes .clang-format and .clang-tidy
   - Shows test integration (GoogleTest)
   - Includes CHANGELOG.md, README.md, DEVLOG.md

3. **Ask about testing** and confirm it knows the framework:
   ```
   "How should I structure my unit tests for this C++ project?"
   ```

   Expected behavior:
   - Mentions GoogleTest or Catch2
   - Describes test fixtures and parameterized tests
   - Explains test structure and naming
   - Discusses CMake integration with CTest
   - Mentions coverage and sanitizers

4. **Verify modern C++ awareness**:
   ```
   "Refactor this code to use modern C++ features: [paste legacy C++03 code]"
   ```

   Expected behavior:
   - Replaces raw pointers with smart pointers
   - Uses auto where appropriate
   - Applies range-based for loops
   - Implements move semantics
   - Uses nullptr instead of NULL
   - Applies const correctness
   - Uses std::string_view for parameters

### Step 4: Configure CMake Build System

Create modern CMake configuration:

#### CMakeLists.txt (Project Root):
```cmake
cmake_minimum_required(VERSION 3.15)

project(MyProject VERSION 0.1.0 LANGUAGES CXX)

# C++ Standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler Warnings
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Werror -pedantic)
endif()

# Options
option(BUILD_TESTING "Build tests" ON)
option(BUILD_EXAMPLES "Build examples" ON)

# Main library
add_library(myproject
    src/core/buffer.cpp
    src/core/utils.cpp
)

target_include_directories(myproject
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

# Testing
if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()
```

#### tests/CMakeLists.txt:
```cmake
find_package(GTest REQUIRED)

add_executable(unit_tests
    test_buffer.cpp
    test_utils.cpp
)

target_link_libraries(unit_tests
    PRIVATE
        myproject
        GTest::GTest
        GTest::Main
)

include(GoogleTest)
gtest_discover_tests(unit_tests)
```

### Step 5: Set Up Static Analysis

Configure formatting and analysis tools:

1. **Create `.clang-format`** for consistent formatting:
   ```yaml
   ---
   Language: Cpp
   BasedOnStyle: Google
   IndentWidth: 4
   ColumnLimit: 100
   PointerAlignment: Left
   BreakBeforeBraces: Attach
   Standard: c++17
   ```

2. **Create `.clang-tidy`** for static analysis:
   ```yaml
   ---
   Checks: >
     -*,
     bugprone-*,
     cppcoreguidelines-*,
     modernize-*,
     performance-*,
     readability-*,
     -modernize-use-trailing-return-type
   WarningsAsErrors: '*'
   HeaderFilterRegex: '.*'
   ```

3. **Run analysis** regularly:
   ```bash
   # Format code
   clang-format -i src/**/*.cpp include/**/*.hpp

   # Static analysis
   clang-tidy src/**/*.cpp -- -std=c++17 -Iinclude

   # Build with sanitizers
   cmake -DCMAKE_CXX_FLAGS="-fsanitize=address -fsanitize=undefined" ..
   ```

### Step 6: Customize for Your Requirements (Optional)

If you need to add organization-specific standards or C++ version constraints:

1. Open the CLAUDE.md file in your project
2. Add a new section at the end:
   ```markdown
   # Organization-Specific Standards

   ## Additional Requirements
   - [C++ standard version (C++17, C++20, C++23)]
   - [Compiler support matrix]
   - [Third-party library restrictions]
   - [Performance requirements]
   - [Platform support (Windows, Linux, macOS)]
   - [Exception policy (exceptions allowed/forbidden)]
   - [RTTI policy (enabled/disabled)]
   ```
3. Save and restart Claude Code session

### Step 7: Initialize Test Framework

Set up GoogleTest:

```bash
# Option 1: CMake FetchContent (recommended)
# Add to CMakeLists.txt:
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.14.0
)
FetchContent_MakeAvailable(googletest)

# Option 2: System package
sudo apt-get install libgtest-dev  # Debian/Ubuntu
brew install googletest             # macOS

# Option 3: Git submodule
git submodule add https://github.com/google/googletest.git third_party/googletest
```

Build and run tests:
```bash
mkdir build && cd build
cmake ..
cmake --build .
ctest --output-on-failure
```

### Step 8: Commit to Version Control

Add the CLAUDE.md and configuration files to your repository:

```bash
git add CLAUDE.md .clang-format .clang-tidy CMakeLists.txt
git commit -m "Add Claude Code C++ system prompt configuration"
git push
```

## Key Features of the C++ System Prompt

### 1. Include Organization
Automatically organizes includes in the correct order:
1. Corresponding header (for .cpp files)
2. C++ standard library headers (alphabetically)
3. Third-party library headers (alphabetically)
4. Project headers (alphabetically)

**Example:**
```cpp
#include "project_name/buffer.hpp"  // Corresponding header

#include <algorithm>
#include <memory>
#include <string>
#include <vector>

#include <fmt/format.h>
#include <spdlog/spdlog.h>

#include "project_name/types.hpp"
#include "project_name/utils.hpp"
```

### 2. Smart Pointers and RAII
**Automatic resource management:**
```cpp
// Good: Smart pointers
auto buffer = std::make_unique<Buffer>(1024);
auto config = std::make_shared<Config>();

// Bad: Manual memory management
Buffer* buf = new Buffer(1024);  // DON'T
delete buf;

// RAII for file handles
class File {
public:
    explicit File(const std::string& path)
        : file_(std::fopen(path.c_str(), "r")) {
        if (!file_) {
            throw std::runtime_error("Cannot open file");
        }
    }

    ~File() {
        if (file_) std::fclose(file_);
    }

    File(const File&) = delete;
    File& operator=(const File&) = delete;
    File(File&&) noexcept = default;

private:
    FILE* file_;
};
```

### 3. Move Semantics
**Efficient resource transfer:**
```cpp
class Buffer {
public:
    Buffer(size_t size) : data_(new char[size]), size_(size) {}
    ~Buffer() { delete[] data_; }

    // Move constructor
    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    // Move assignment
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    // Copy operations
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

private:
    char* data_;
    size_t size_;
};
```

### 4. Exception Safety
**Strong exception guarantee:**
```cpp
class Container {
public:
    // Strong guarantee: commit or rollback
    Container& operator=(const Container& other) {
        Container temp(other);  // If copy fails, this is unchanged
        swap(temp);             // noexcept swap
        return *this;
    }

    void swap(Container& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
    }

private:
    std::vector<int> data_;
    size_t size_;
};
```

### 5. Modern C++ Features

**C++17 Features:**
```cpp
// Structured bindings
auto [id, name, value] = getData();

// if with initializer
if (auto it = map.find(key); it != map.end()) {
    process(it->second);
}

// std::optional
std::optional<std::string> findUser(int id);

// std::string_view (no copies)
void processString(std::string_view sv);
```

**C++20 Features:**
```cpp
// Concepts
template <typename T>
concept Numeric = std::is_arithmetic_v<T>;

template <Numeric T>
T add(T a, T b) { return a + b; }

// Ranges
auto result = numbers
    | std::views::filter([](int n) { return n % 2 == 0; })
    | std::views::transform([](int n) { return n * n; })
    | std::views::take(3);

// std::span (non-owning view)
void processData(std::span<const int> data);
```

### 6. Const Correctness
**Proper const usage:**
```cpp
class DataProcessor {
public:
    // Const member function
    size_t getSize() const { return data_.size(); }

    // Non-const
    void addData(const std::string& data) { data_.push_back(data); }

    // Const and non-const overloads
    const std::string& getData(size_t index) const { return data_[index]; }
    std::string& getData(size_t index) { return data_[index]; }

private:
    std::vector<std::string> data_;
};

// Function parameters: const references for read-only
void processData(const std::vector<int>& data);
```

### 7. Lambda Expressions
**Concise local functionality:**
```cpp
// Basic lambda
auto add = [](int a, int b) { return a + b; };

// Capture by value
int multiplier = 5;
auto multiply = [multiplier](int x) { return x * multiplier; };

// Capture by reference
int sum = 0;
auto accumulate = [&sum](int x) { sum += x; };

// Generic lambda (C++14)
auto generic = [](auto x, auto y) { return x + y; };

// With STL algorithms
std::vector<int> numbers = {1, 2, 3, 4, 5};
auto evenCount = std::count_if(numbers.begin(), numbers.end(),
                                [](int n) { return n % 2 == 0; });
```

### 8. Doxygen Documentation
**Class documentation:**
```cpp
/**
 * @class Buffer
 * @brief Dynamic byte buffer with automatic growth
 *
 * Thread-safe when used with external synchronization.
 * Provides strong exception safety guarantee.
 *
 * Example:
 * @code
 * Buffer buf(1024);
 * buf.append(data, size);
 * @endcode
 *
 * @note Move-only type (copying disabled)
 * @warning Not thread-safe without external synchronization
 */
class Buffer {
public:
    /**
     * @brief Construct buffer with specified capacity
     * @param[in] initialCapacity Initial capacity in bytes
     * @throws std::bad_alloc If allocation fails
     */
    explicit Buffer(size_t initialCapacity);

    /**
     * @brief Append data to buffer
     * @param[in] data Pointer to data
     * @param[in] size Number of bytes
     * @throws std::invalid_argument If data is null and size > 0
     */
    void append(const uint8_t* data, size_t size);
};
```

### 9. Testing with GoogleTest
**Test structure:**
```cpp
#include <gtest/gtest.h>
#include "buffer.hpp"

class BufferTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize test environment
    }

    void TearDown() override {
        // Clean up
    }
};

TEST_F(BufferTest, ConstructorCreatesEmptyBuffer) {
    Buffer buf(1024);

    EXPECT_EQ(buf.size(), 0);
    EXPECT_GE(buf.capacity(), 1024);
    EXPECT_TRUE(buf.empty());
}

TEST_F(BufferTest, MoveConstructorTransfersOwnership) {
    Buffer buf1(16);
    buf1.append(data, size);

    Buffer buf2(std::move(buf1));

    EXPECT_EQ(buf2.size(), size);
}

// Parameterized tests
class BufferSizeTest : public ::testing::TestWithParam<size_t> {};

TEST_P(BufferSizeTest, VariousSizes) {
    const size_t size = GetParam();
    Buffer buf(size);
    EXPECT_GE(buf.capacity(), size);
}

INSTANTIATE_TEST_SUITE_P(SizeRange, BufferSizeTest,
    ::testing::Values(0, 1, 10, 100, 1000));
```

### 10. CMake Integration
**Modern CMake patterns:**
```cmake
# Target-based design
add_library(mylib src/lib.cpp)

target_include_directories(mylib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

target_compile_features(mylib PUBLIC cxx_std_17)

# Link libraries
target_link_libraries(myapp PRIVATE mylib)

# Testing
enable_testing()
add_test(NAME MyTest COMMAND unit_tests)
```

## Common Configuration Issues

### Issue: System Prompt Not Loading
**Solution**: Verify CLAUDE.md is in the project root directory and restart Claude Code session

### Issue: Token Limit Warnings
**Solution**: Switch from comprehensive (~40k) to condensed (~20k) version

### Issue: C++17 Features Not Recognized
**Solution**: Verify comprehensive version is loaded; mention C++ standard explicitly: "Using C++17, create a class with structured bindings"

### Issue: Smart Pointers Not Being Suggested
**Solution**:
- Comprehensive version emphasizes smart pointers
- Explicitly request: "Refactor this code to use smart pointers instead of raw pointers"

### Issue: CMake Build Failures
**Solution**:
- Verify CMake 3.15+ installed: `cmake --version`
- Check C++ compiler supports C++17: `g++ --version` or `clang++ --version`
- Ensure GoogleTest is available

### Issue: Static Analysis Errors
**Solution**:
- Create `.clang-tidy` in project root
- Run: `clang-tidy src/*.cpp -- -std=c++17 -Iinclude`
- Suppress false positives in config file

## Success Criteria

After completing this skill, you should have:

- [ ] Claude Code configured with C++ system prompt (CLAUDE.md in project root)
- [ ] Verified configuration by testing class generation (with RAII and move semantics)
- [ ] Confirmed project structure knowledge (CMake-based)
- [ ] Validated testing framework understanding (GoogleTest)
- [ ] Verified modern C++ awareness (smart pointers, move semantics)
- [ ] Set up CMake build system
- [ ] Configured static analysis tools (.clang-format, .clang-tidy)
- [ ] Initialized test framework (GoogleTest or Catch2)
- [ ] Verified compilation with no warnings (-Wall -Wextra -Werror)
- [ ] Optionally customized for organization-specific needs
- [ ] Committed CLAUDE.md and configurations to version control

## Related Skills

- `generate-cpp-documentation`: Generate Doxygen documentation for C++ code
- `refactor-to-modern-cpp`: Convert legacy C++ to modern C++17/C++20
- `implement-move-semantics`: Add move constructors and move assignment
- `template-library-design`: Create header-only template libraries
- `cpp-performance-optimization`: Optimize C++ code for performance
- `exception-safety-review`: Review and improve exception safety

## Additional Resources

### Standards and Guidelines
- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [C++17 Standard](https://en.cppreference.com/w/cpp/17)
- [C++20 Standard](https://en.cppreference.com/w/cpp/20)
- [Effective Modern C++](https://www.aristeia.com/EMC++.html) by Scott Meyers

### Tools
- [GoogleTest](https://github.com/google/googletest)
- [Catch2](https://github.com/catchorg/Catch2)
- [CMake](https://cmake.org/)
- [Clang-Tidy](https://clang.llvm.org/extra/clang-tidy/)
- [Clang-Format](https://clang.llvm.org/docs/ClangFormat.html)
- [Compiler Explorer](https://godbolt.org/)

### Libraries
- [Abseil](https://abseil.io/) - Google's C++ library
- [Boost](https://www.boost.org/) - Comprehensive C++ libraries
- [fmt](https://fmt.dev/) - Modern formatting library
- [spdlog](https://github.com/gabime/spdlog) - Fast logging library
- [{fmt}](https://github.com/fmtlib/fmt) - Formatting library

### Books and References
- "Effective Modern C++" by Scott Meyers
- "C++ Concurrency in Action" by Anthony Williams
- "Professional CMake" by Craig Scott
- "C++ Templates: The Complete Guide" by Vandevoorde, Josuttis, Gregor

### Online Resources
- [cppreference.com](https://en.cppreference.com/) - C++ reference
- [C++ Weekly](https://www.youtube.com/c/lefticus1) by Jason Turner
- [CppCon YouTube Channel](https://www.youtube.com/user/CppCon)
- [ModernesCpp.com](https://www.modernescpp.com/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5
**C++ Standards**: C++17, C++20, C++23
**Compliance**: C++ Core Guidelines
