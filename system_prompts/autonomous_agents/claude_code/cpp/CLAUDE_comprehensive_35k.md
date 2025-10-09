# CLAUDE.md - C++ Development System Instructions
*Comprehensive system prompt for Claude Code - Optimized for Modern C++ development*

---

# Quick Start for Common Tasks

## Section Usage Map
- **Bug Fix**: Sections 1, 3, 9
- **New Feature**: Sections 1-5, 7
- **Refactoring**: Sections 3, 6, 9
- **Project Setup**: All sections

## Task-Specific Quick Reference
- **Fix a function**: Focus sections 3, 9
- **New project**: Use sections 2, 4, 5
- **Code review**: Apply sections 3, 10
- **Modern C++ refactoring**: Sections 3, 11

## Context-Aware Behavior
- **For applications**: Use modern C++ features, STL containers
- **For libraries**: Clear API boundaries, header-only when appropriate
- **For performance**: Profile first, optimize second, use move semantics

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation
- Minimal testing setup
- Focus on core functionality

### Full Mode (for new projects)
- Complete architecture with CMake
- Comprehensive testing with GoogleTest or Catch2
- Full Doxygen documentation

## Claude Code Terminal Commands
- **Build**: `cmake --build build`
- **Test**: `ctest --test-dir build`
- **Format**: `clang-format -i src/**/*.cpp`
- **Analysis**: `clang-tidy src/**/*.cpp`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding
- Never make assumptions about missing requirements
- Frame questions to gather specific technical requirements
- Clarify C++ standard version (C++11, 14, 17, 20, 23)
- Determine performance and safety requirements

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work
- Explain implementation details, reasoning, and modern C++ idioms
- Enable learning through understanding, not copy-paste
- Reference C++ Core Guidelines and standard library documentation
- Explain RAII, move semantics, perfect forwarding, and template metaprogramming

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions
- Analyze problems independently for safety and performance
- Compare alternatives (STL vs custom, raw pointers vs smart pointers)
- Clearly explain reasoning and trade-offs
- Recommend modern C++ solutions over C-style code

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity
- **Code Modification**: Edit originals, don't create '_enhanced' versions
- **Codebase Cleanup**: Remove obsolete code and deprecated patterns
- **Refactoring**: Use modern C++ features, eliminate manual memory management

### Quality Assurance
- Review code for: quality, efficiency, best practices, exception safety, const-correctness
- Check for: memory leaks, resource leaks, undefined behavior, race conditions
- Verify: RAII compliance, exception safety guarantees, move semantics
- If already optimal, confirm briefly with reasoning


# 2. Project Architecture
---

## Standard C++ Application Structure

```
project_name/
├── include/                       # Public headers
│   └── project_name/              # Namespace headers
│       ├── api.hpp                # Public API
│       ├── types.hpp              # Public types
│       └── config.hpp             # Configuration
├── src/                           # Source implementation
│   ├── main.cpp                   # Entry point
│   ├── core/                      # Core logic
│   │   ├── buffer.cpp
│   │   ├── buffer.hpp
│   │   └── utils.cpp
│   └── platform/                  # Platform-specific
├── tests/                         # Testing suite
│   ├── test_buffer.cpp
│   ├── test_utils.cpp
│   └── CMakeLists.txt
├── third_party/                   # External dependencies
├── cmake/                         # CMake modules
│   └── FindGoogleTest.cmake
├── build/                         # Build output (gitignored)
├── docs/                          # Documentation
│   └── Doxyfile                   # Doxygen config
├── scripts/                       # Build scripts
├── CMakeLists.txt                 # Main CMake
├── .clang-format                  # Formatting rules
├── .clang-tidy                    # Static analysis
├── CHANGELOG.md                   # Version history
├── README.md                      # Documentation
├── DEVLOG.md                      # Development log
├── LICENSE                        # License
└── .gitignore                     # Git ignore
```

## Header-Only Library Structure

```
library_name/
├── include/
│   └── library_name/
│       ├── library_name.hpp       # Main header (includes all)
│       ├── core/
│       │   ├── buffer.hpp
│       │   └── utils.hpp
│       └── detail/                # Implementation details
│           └── buffer_impl.hpp
├── tests/
├── examples/
│   └── example_basic.cpp
├── CMakeLists.txt
└── README.md
```

## Project Initialization Sequence

1. **Create directory structure** as outlined above
2. **Create `CMakeLists.txt`** with modern CMake (3.15+)
3. **Create `.gitignore`** for build/, IDE files
4. **Create `CHANGELOG.md`** starting with version 0.1.0
5. **Create `README.md`** with build instructions
6. **Create `DEVLOG.md`** with initial task list
7. **Set up formatting**: Create `.clang-format`
8. **Set up analysis**: Create `.clang-tidy`
9. **Initialize headers**: Proper include guards or `#pragma once`

## CMakeLists.txt Template

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
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src
)

# Executable
add_executable(myproject_app src/main.cpp)
target_link_libraries(myproject_app PRIVATE myproject)

# Testing
if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()

# Installation
install(TARGETS myproject myproject_app
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
    RUNTIME DESTINATION bin
)

install(DIRECTORY include/ DESTINATION include)
```

## Tests CMakeLists.txt

```cmake
# Find GoogleTest
find_package(GTest REQUIRED)

# Test executable
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

# Discover tests
include(GoogleTest)
gtest_discover_tests(unit_tests)
```

## .clang-format Template

```yaml
---
Language: Cpp
BasedOnStyle: Google
IndentWidth: 4
TabWidth: 4
UseTab: Never
ColumnLimit: 100
PointerAlignment: Left
DerivePointerAlignment: false
AlignConsecutiveMacros: true
AlignConsecutiveAssignments: false
AlignConsecutiveDeclarations: false
AlignTrailingComments: true
AllowShortFunctionsOnASingleLine: Empty
AllowShortIfStatementsOnASingleLine: Never
AllowShortLoopsOnASingleLine: false
BreakBeforeBraces: Attach
IndentCaseLabels: false
SpaceBeforeParens: ControlStatements
Standard: c++17
```

## .clang-tidy Template

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
FormatStyle: file
```


# 3. Code Standards
---

## Modern C++ Style Guidelines

### Include Organization

**Order (blank line between sections):**

1. **Corresponding header** (for .cpp files)
2. **C++ standard library headers** (alphabetically)
3. **Third-party library headers** (alphabetically)
4. **Project headers** (alphabetically)

**Example:**
```cpp
// In buffer.cpp
#include "project_name/buffer.hpp"  // Corresponding header first

#include <algorithm>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include <fmt/format.h>
#include <spdlog/spdlog.h>

#include "project_name/types.hpp"
#include "project_name/utils.hpp"
```

**Header Guards:**
```cpp
#ifndef PROJECT_NAME_BUFFER_HPP
#define PROJECT_NAME_BUFFER_HPP

// Header content

#endif  // PROJECT_NAME_BUFFER_HPP

// Or use #pragma once (modern, widely supported)
#pragma once

// Header content
```

### Naming Conventions

**Files:**
- Headers: `.hpp` (or `.h` for C compatibility)
- Source: `.cpp`
- Templates: `.hpp` (implementation in header)

**Naming Styles:**
```cpp
// Classes and Types: PascalCase
class BufferManager { };
struct ConfigData { };
enum class LogLevel { };
using StringMap = std::map<std::string, std::string>;

// Functions and Methods: camelCase
void processData();
int calculateTotal();

// Variables: camelCase
int itemCount = 0;
std::string userName;

// Constants: kPascalCase (Google style) or SCREAMING_SNAKE_CASE
constexpr int kMaxBufferSize = 1024;
constexpr int MAX_CONNECTIONS = 100;

// Member variables: trailing underscore (class members)
class MyClass {
private:
    int count_;
    std::string name_;
};

// Namespace: lowercase
namespace project_name {
namespace detail {
}  // namespace detail
}  // namespace project_name
```

### Modern C++ Features

**Use Smart Pointers:**
```cpp
// Prefer unique_ptr for ownership
auto buffer = std::make_unique<Buffer>(1024);

// Use shared_ptr for shared ownership
auto config = std::make_shared<Config>();

// Avoid raw owning pointers
Buffer* buf = new Buffer(1024);  // DON'T: manual management
delete buf;

// Raw non-owning pointers are OK for observation
void processBuffer(const Buffer* buf);  // OK: non-owning
```

**RAII for Resource Management:**
```cpp
// Good: RAII handles cleanup automatically
class File {
public:
    explicit File(const std::string& path)
        : file_(std::fopen(path.c_str(), "r")) {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }

    ~File() {
        if (file_) {
            std::fclose(file_);
        }
    }

    // Delete copy, allow move
    File(const File&) = delete;
    File& operator=(const File&) = delete;
    File(File&& other) noexcept : file_(other.file_) {
        other.file_ = nullptr;
    }

    FILE* get() const { return file_; }

private:
    FILE* file_;
};

// Usage: automatic cleanup
{
    File f("data.txt");
    // Use f
}  // Automatic cleanup
```

**Use Auto Appropriately:**
```cpp
// Good uses of auto
auto value = computeValue();                    // When type is obvious
auto it = container.begin();                    // Iterator types
auto lambda = [](int x) { return x * 2; };     // Lambda types
auto ptr = std::make_unique<Widget>();          // Smart pointers

// Avoid when it obscures type
auto x = getValue();  // What type is x?
int x = getValue();   // Clear

// Use const auto& for non-mutating iterations
for (const auto& item : container) {
    // item is const reference
}

// Use auto& for mutating iterations
for (auto& item : container) {
    item.modify();
}
```

**Range-Based For Loops:**
```cpp
std::vector<int> numbers = {1, 2, 3, 4, 5};

// Prefer range-based for over index-based
for (const auto& num : numbers) {
    std::cout << num << '\n';
}

// Instead of:
for (size_t i = 0; i < numbers.size(); ++i) {
    std::cout << numbers[i] << '\n';
}

// With structured bindings (C++17)
std::map<std::string, int> scores;
for (const auto& [name, score] : scores) {
    std::cout << name << ": " << score << '\n';
}
```

**Move Semantics:**
```cpp
class Buffer {
public:
    // Constructor
    Buffer(size_t size) : data_(new char[size]), size_(size) {}

    // Destructor
    ~Buffer() { delete[] data_; }

    // Copy constructor (deep copy)
    Buffer(const Buffer& other)
        : data_(new char[other.size_]), size_(other.size_) {
        std::copy(other.data_, other.data_ + size_, data_);
    }

    // Copy assignment
    Buffer& operator=(const Buffer& other) {
        if (this != &other) {
            Buffer temp(other);
            swap(temp);
        }
        return *this;
    }

    // Move constructor (transfer ownership)
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

    void swap(Buffer& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
    }

private:
    char* data_;
    size_t size_;
};

// Usage: move avoids copy
Buffer createBuffer() {
    return Buffer(1024);  // Move, not copy
}

Buffer buf = createBuffer();  // Move construction
```

**Const Correctness:**
```cpp
class DataProcessor {
public:
    // Const member function: doesn't modify object
    size_t getSize() const { return data_.size(); }
    bool isEmpty() const { return data_.empty(); }

    // Non-const: modifies object
    void addData(const std::string& data) { data_.push_back(data); }
    void clear() { data_.clear(); }

    // Const and non-const overloads
    const std::string& getData(size_t index) const { return data_[index]; }
    std::string& getData(size_t index) { return data_[index]; }

private:
    std::vector<std::string> data_;
};

// Function parameters: const references for read-only
void processData(const std::vector<int>& data);

// Return const value types (usually unnecessary in modern C++)
// Return by value for move semantics
std::vector<int> getData();  // Returns by value, moved
```

**Template Basics:**
```cpp
// Function template
template <typename T>
T max(T a, T b) {
    return (a > b) ? a : b;
}

// Class template
template <typename T>
class Stack {
public:
    void push(const T& item) { data_.push_back(item); }
    void push(T&& item) { data_.push_back(std::move(item)); }
    T pop() {
        T item = std::move(data_.back());
        data_.pop_back();
        return item;
    }
    bool empty() const { return data_.empty(); }

private:
    std::vector<T> data_;
};

// Template specialization
template <>
class Stack<bool> {
    // Specialized implementation for bool
};

// Variadic templates (C++11)
template <typename... Args>
void print(Args&&... args) {
    (std::cout << ... << args) << '\n';  // Fold expression (C++17)
}
```

**Lambda Expressions:**
```cpp
// Basic lambda
auto add = [](int a, int b) { return a + b; };

// Capture by value
int multiplier = 5;
auto multiply = [multiplier](int x) { return x * multiplier; };

// Capture by reference
int sum = 0;
auto accumulate = [&sum](int x) { sum += x; };

// Capture everything by reference
auto lambda1 = [&]() { /* can modify all locals */ };

// Capture everything by value
auto lambda2 = [=]() { /* read-only access to all locals */ };

// Generic lambda (C++14)
auto generic = [](auto x, auto y) { return x + y; };

// Using lambdas with STL algorithms
std::vector<int> numbers = {1, 2, 3, 4, 5};
auto result = std::count_if(numbers.begin(), numbers.end(),
                            [](int n) { return n % 2 == 0; });

// Sort with lambda
std::sort(numbers.begin(), numbers.end(),
          [](int a, int b) { return a > b; });  // Descending
```

### Error Handling and Exceptions

**Exception Safety Guarantees:**
```cpp
class Buffer {
public:
    // Basic guarantee: if exception occurs, object is in valid state
    void resize(size_t newSize) {
        auto newData = std::make_unique<char[]>(newSize);
        // If allocation fails, exception thrown, object unchanged
        std::copy(data_.get(), data_.get() + std::min(size_, newSize),
                  newData.get());
        data_ = std::move(newData);
        size_ = newSize;
    }

    // Strong guarantee: commit or rollback (copy-and-swap idiom)
    Buffer& operator=(const Buffer& other) {
        Buffer temp(other);  // If copy fails, this is unchanged
        swap(temp);          // noexcept swap
        return *this;
    }

    // No-throw guarantee: marked noexcept
    void swap(Buffer& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
    }

private:
    std::unique_ptr<char[]> data_;
    size_t size_;
};
```

**RAII for Exception Safety:**
```cpp
// Good: RAII ensures cleanup even with exceptions
void processFile(const std::string& filename) {
    std::ifstream file(filename);  // RAII: automatic close
    if (!file) {
        throw std::runtime_error("Cannot open file");
    }

    std::vector<std::string> lines;  // RAII: automatic cleanup
    std::string line;

    while (std::getline(file, line)) {
        lines.push_back(line);
        // If exception thrown, file and lines are cleaned up automatically
    }

    processLines(lines);  // May throw
    // Automatic cleanup on normal or exceptional exit
}

// Custom RAII wrapper
class Lock {
public:
    explicit Lock(std::mutex& m) : mutex_(m) { mutex_.lock(); }
    ~Lock() { mutex_.unlock(); }

    Lock(const Lock&) = delete;
    Lock& operator=(const Lock&) = delete;

private:
    std::mutex& mutex_;
};

// Use std::lock_guard instead of custom Lock
void threadSafeOperation() {
    std::lock_guard<std::mutex> lock(mutex_);
    // Critical section
}  // Automatic unlock
```

**Exception Specifications:**
```cpp
// Mark noexcept when function doesn't throw
void swap(Buffer& a, Buffer& b) noexcept {
    std::swap(a, b);
}

// Conditional noexcept
template <typename T>
class Container {
    void swap(Container& other) noexcept(noexcept(std::swap(data_, other.data_))) {
        std::swap(data_, other.data_);
    }
private:
    T data_;
};

// Throw appropriate exception types
void validateInput(int value) {
    if (value < 0) {
        throw std::invalid_argument("Value must be non-negative");
    }
    if (value > 100) {
        throw std::out_of_range("Value exceeds maximum");
    }
}

// Catch specific exceptions
try {
    processData();
} catch (const std::invalid_argument& e) {
    std::cerr << "Invalid argument: " << e.what() << '\n';
} catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << '\n';
} catch (...) {
    std::cerr << "Unknown error\n";
    throw;  // Re-throw
}
```


# 4. Documentation Standards
---

## Doxygen Documentation

### File Headers

```cpp
/**
 * @file buffer.hpp
 * @brief Dynamic buffer with automatic growth
 *
 * Provides a type-safe dynamic buffer with RAII semantics,
 * automatic memory management, and exception safety.
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @date 2025-01-01
 * @version 0.1.0
 */
```

### Class Documentation

```cpp
/**
 * @class Buffer
 * @brief Dynamic byte buffer with automatic growth
 *
 * Thread-safe when used with external synchronization.
 * Provides strong exception safety guarantee for all operations.
 *
 * Example usage:
 * @code
 * Buffer buf(1024);
 * buf.append(data, size);
 * const auto* ptr = buf.data();
 * @endcode
 *
 * @note Move-only type (copying disabled for performance)
 * @warning Not thread-safe without external synchronization
 */
class Buffer {
public:
    /**
     * @brief Construct buffer with specified capacity
     *
     * @param[in] initialCapacity Initial capacity in bytes
     * @throws std::bad_alloc If allocation fails
     *
     * @post Buffer is empty but has reserved capacity
     */
    explicit Buffer(size_t initialCapacity);

    /**
     * @brief Append data to buffer
     *
     * Automatically grows buffer if needed. Provides strong
     * exception safety guarantee.
     *
     * @param[in] data Pointer to data to append
     * @param[in] size Number of bytes to append
     * @throws std::invalid_argument If data is null and size > 0
     * @throws std::bad_alloc If reallocation fails
     *
     * @pre data must be valid for size bytes
     * @post Buffer size increased by size bytes
     */
    void append(const uint8_t* data, size_t size);

    /**
     * @brief Get current buffer size
     * @return Size in bytes
     * @note noexcept guarantee
     */
    [[nodiscard]] size_t size() const noexcept;

    /**
     * @brief Get raw data pointer
     * @return Pointer to data (const)
     * @note Pointer valid until next non-const operation
     */
    [[nodiscard]] const uint8_t* data() const noexcept;

private:
    std::vector<uint8_t> data_;  ///< Internal storage
};
```

### Function Documentation

```cpp
/**
 * @brief Parse configuration file
 *
 * Reads configuration from INI-style file and returns
 * structured data. Supports comments and blank lines.
 *
 * @param[in] filename Path to configuration file
 * @return Configuration data
 * @throws std::runtime_error If file cannot be opened
 * @throws std::invalid_argument If parse error occurs
 *
 * @note Thread-safe
 * @see ConfigData, saveConfig()
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */
ConfigData parseConfig(const std::string& filename);

/**
 * @brief Calculate checksum of data
 * @param[in] data Data span
 * @return 32-bit checksum
 * @note Constexpr for compile-time evaluation
 */
[[nodiscard]] constexpr uint32_t checksum(std::span<const uint8_t> data) noexcept;
```

### Template Documentation

```cpp
/**
 * @brief Generic container adapter
 *
 * @tparam T Element type (must be movable)
 * @tparam Container Underlying container type
 *
 * @invariant Container is always in valid state
 */
template <typename T, typename Container = std::vector<T>>
class Stack {
    static_assert(std::is_move_constructible_v<T>,
                  "T must be move constructible");
public:
    /**
     * @brief Push element onto stack
     * @param[in] value Element to push
     */
    void push(T value) {
        container_.push_back(std::move(value));
    }
};
```

## README.md Structure

```markdown
# [Project Name] - v[X.Y.Z]

## What's New in vX.Y.Z
- [Key features/changes]

## Overview
[2-3 sentence description]

## Features
- Modern C++17 with optional C++20 features
- Header-only/compiled library
- Exception-safe with RAII
- Comprehensive test coverage
- Cross-platform (Windows, Linux, macOS)

## Requirements

### Build Dependencies
- CMake 3.15+
- C++17 compliant compiler:
  - GCC 9.0+
  - Clang 10.0+
  - MSVC 2019+
- GoogleTest (for testing)

### Optional Dependencies
- Doxygen (for documentation)
- clang-format (for formatting)
- clang-tidy (for static analysis)

## Building

### Linux/macOS
    ```bash
    git clone [repo-url]
    cd [project-name]
    mkdir build && cd build
    cmake ..
    cmake --build .
    ```

### Windows (Visual Studio)
    ```bash
    mkdir build && cd build
    cmake .. -G "Visual Studio 16 2019"
    cmake --build . --config Release
    ```

### Build Options
    ```bash
    cmake .. -DBUILD_TESTING=OFF   # Disable tests
    cmake .. -DCMAKE_BUILD_TYPE=Debug
    ```

## Installation
    ```bash
    cmake --install . --prefix /usr/local
    ```

## Usage

### Basic Example
    ```cpp
    #include <project_name/buffer.hpp>

    int main() {
        project_name::Buffer buf(1024);
        const std::string data = "Hello";
        buf.append(reinterpret_cast<const uint8_t*>(data.data()),
                   data.size());
        return 0;
    }
    ```

### CMake Integration
    ```cmake
    find_package(ProjectName REQUIRED)
    target_link_libraries(your_target PRIVATE ProjectName::ProjectName)
    ```

## Testing
    ```bash
    cd build
    ctest --output-on-failure
    ```

## Documentation
    ```bash
    cd docs
    doxygen Doxyfile
    ```

## License
[License information]

## Contributing
See CONTRIBUTING.md

## Authors
- Benjamin Dourthe (benjamin@adonamed.com)
```

## CHANGELOG.md Structure

```markdown
# Changelog

Format based on [Keep a Changelog](https://keepachangelog.com/).
Versioning follows [Semantic Versioning](https://semver.org/).

## [Unreleased]
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [0.2.0] - 2025-01-15

### Added
- Move semantics for Buffer class
- noexcept specifications on performance-critical functions
- Constexpr support for compile-time operations

### Changed
- Migrated to C++17 from C++14
- Replaced raw pointers with smart pointers
- Updated exception messages for clarity

### Fixed
- Memory leak in Buffer::resize()
- Race condition in Config::load()

## [0.1.0] - 2025-01-01

### Added
- Initial release
- Buffer class with RAII
- Config parser
- Comprehensive test suite
- CMake build system
- Doxygen documentation
```

## DEVLOG.md Structure

```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Implement move semantics for all classes
- [ ] Add thread safety documentation

### Medium Priority
- [ ] Migrate to C++20 concepts
- [ ] Add performance benchmarks

### Low Priority
- [ ] Header-only mode
- [ ] Module support (C++20)

## Development History

### Project Architecture
- **Initial Design**: RAII-based resource management throughout
- **C++ Standard**: C++17 baseline, C++20 features optional
- **Exception Strategy**: Strong exception safety for all operations
- **Memory Management**: Smart pointers, no manual memory management
- **Testing**: GoogleTest for unit tests, Catch2 considered

### Implementation Challenges

#### Challenge 1: Exception Safety in Buffer::resize()
- **Problem**: Reallocation could leave buffer in invalid state
- **Solution**: Allocate new buffer first, then swap (commit or rollback)
- **Trade-offs**: Temporary memory overhead vs. exception safety
- **Code Pattern**: Copy-and-swap idiom
- **Lessons**: Always design for exception safety from start

#### Challenge 2: Move Semantics Performance
- **Problem**: Unnecessary copies in return values
- **Solution**: Implemented move constructors and move assignment
- **Trade-offs**: More code vs. significant performance gain
- **Measurements**: 10x performance improvement for large objects
- **Lessons**: Profile before and after to verify improvements

#### Challenge 3: Template Compilation Times
- **Problem**: Heavy template usage caused slow compilation
- **Solution**: Extern templates, forward declarations, pImpl idiom
- **Trade-offs**: Code complexity vs. compile time
- **Results**: 40% reduction in compilation time
- **Lessons**: Measure compilation times, use appropriate patterns

### Technical Decisions

#### Smart Pointers over Raw Pointers
- **Decision**: Use std::unique_ptr and std::shared_ptr exclusively
- **Rationale**: Automatic memory management, exception safety
- **Alternatives Considered**: Raw pointers with manual management
- **Why Not**: Too error-prone, no RAII benefits
- **Impact**: Zero memory leaks, simplified code

#### GoogleTest over Catch2
- **Decision**: GoogleTest for testing framework
- **Rationale**: More features, better CMake integration, industry standard
- **Alternatives**: Catch2, Boost.Test, custom framework
- **Why GoogleTest**: Mature, well-documented, used by Google
- **Impact**: Comprehensive testing, good developer experience

#### C++17 as Baseline
- **Decision**: Require C++17, use C++20 features conditionally
- **Rationale**: Balance modern features with compiler support
- **C++17 Features Used**: structured bindings, if constexpr, std::optional
- **C++20 Features**: Concepts (optional), ranges (optional)
- **Compiler Support**: GCC 9+, Clang 10+, MSVC 2019+

## Performance Notes

### Buffer Performance
- **Small allocations (<1KB)**: ~50ns per append
- **Large allocations (>1MB)**: ~2μs per append
- **Growth strategy**: 1.5x geometric growth
- **Memory overhead**: <10% for typical workloads

### Optimization Techniques Applied
- Move semantics for all large objects
- Reserve capacity upfront when size known
- Small string optimization for short strings
- Cache-friendly data layouts

## Troubleshooting History

### Issue 1: Segmentation Fault in Buffer Destructor
- **Symptoms**: Crash on program exit
- **Root Cause**: Double-free due to broken move constructor
- **Resolution**: Fixed move constructor to nullify source pointer
- **Prevention**: Added comprehensive move semantics tests
- **Test Added**: test_buffer_move_semantics

### Issue 2: Memory Leak Reported by Valgrind
- **Symptoms**: Memory leak in exception path
- **Root Cause**: Exception thrown before smart pointer assignment
- **Resolution**: Changed allocation order, use RAII wrapper
- **Prevention**: Run all tests under Valgrind in CI
- **Pattern**: RAII for all resource acquisition

### Issue 3: Compilation Error with GCC 9
- **Symptoms**: Template deduction failure
- **Root Cause**: Missing template argument deduction guides
- **Resolution**: Added deduction guides for all class templates
- **Prevention**: Test with multiple compiler versions
- **Compilers Tested**: GCC 9-13, Clang 10-16, MSVC 2019-2022
```


# 5. Testing Framework
---

## GoogleTest Framework

### Test Structure

```cpp
/**
 * @file test_buffer.cpp
 * @brief Unit tests for Buffer class
 *
 * Comprehensive test coverage for Buffer including
 * normal operations, edge cases, move semantics,
 * and exception safety.
 */

#include <gtest/gtest.h>
#include <project_name/buffer.hpp>

#include <algorithm>
#include <memory>
#include <stdexcept>
#include <vector>

using namespace project_name;

/* ========================================================================
 * Test Fixture
 * ======================================================================== */

class BufferTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize test environment
    }

    void TearDown() override {
        // Clean up after each test
    }

    // Helper methods
    std::vector<uint8_t> createTestData(size_t size) {
        std::vector<uint8_t> data(size);
        std::iota(data.begin(), data.end(), 0);
        return data;
    }
};

/* ========================================================================
 * Basic Functionality Tests
 * ======================================================================== */

TEST_F(BufferTest, ConstructorCreatesEmptyBuffer) {
    Buffer buf(1024);

    EXPECT_EQ(buf.size(), 0);
    EXPECT_GE(buf.capacity(), 1024);
    EXPECT_TRUE(buf.empty());
}

TEST_F(BufferTest, AppendIncreasesSize) {
    Buffer buf(16);
    const auto data = createTestData(5);

    buf.append(data.data(), data.size());

    EXPECT_EQ(buf.size(), 5);
    EXPECT_FALSE(buf.empty());
}

TEST_F(BufferTest, AppendPreservesData) {
    Buffer buf(16);
    const std::string testData = "Hello, World!";

    buf.append(reinterpret_cast<const uint8_t*>(testData.data()),
               testData.size());

    EXPECT_EQ(buf.size(), testData.size());
    EXPECT_EQ(std::memcmp(buf.data(), testData.data(), testData.size()), 0);
}

/* ========================================================================
 * Edge Case Tests
 * ======================================================================== */

TEST_F(BufferTest, AppendToEmptyBuffer) {
    Buffer buf(0);
    const auto data = createTestData(10);

    EXPECT_NO_THROW(buf.append(data.data(), data.size()));
    EXPECT_EQ(buf.size(), 10);
}

TEST_F(BufferTest, AppendZeroBytes) {
    Buffer buf(16);
    const auto data = createTestData(5);

    buf.append(data.data(), 0);

    EXPECT_EQ(buf.size(), 0);
    EXPECT_TRUE(buf.empty());
}

TEST_F(BufferTest, AppendCausesReallocation) {
    Buffer buf(4);  // Small initial capacity
    const auto data = createTestData(100);

    EXPECT_NO_THROW(buf.append(data.data(), data.size()));
    EXPECT_EQ(buf.size(), 100);
    EXPECT_GE(buf.capacity(), 100);
}

/* ========================================================================
 * Exception Safety Tests
 * ======================================================================== */

TEST_F(BufferTest, AppendNullPointerThrows) {
    Buffer buf(16);

    EXPECT_THROW(buf.append(nullptr, 10), std::invalid_argument);
    EXPECT_EQ(buf.size(), 0);  // Buffer unchanged
}

TEST_F(BufferTest, ConstructorWithZeroSizeNoThrow) {
    EXPECT_NO_THROW(Buffer buf(0));
}

TEST_F(BufferTest, ExceptionLeavesBufferValid) {
    Buffer buf(16);
    const auto data = createTestData(5);
    buf.append(data.data(), data.size());

    const size_t sizeBefore = buf.size();

    try {
        buf.append(nullptr, 10);  // Should throw
    } catch (const std::invalid_argument&) {
        // Expected
    }

    EXPECT_EQ(buf.size(), sizeBefore);  // Size unchanged
}

/* ========================================================================
 * Move Semantics Tests
 * ======================================================================== */

TEST_F(BufferTest, MoveConstructorTransfersOwnership) {
    Buffer buf1(16);
    const auto data = createTestData(10);
    buf1.append(data.data(), data.size());

    const auto* originalData = buf1.data();

    Buffer buf2(std::move(buf1));

    EXPECT_EQ(buf2.size(), 10);
    EXPECT_EQ(buf2.data(), originalData);
    // buf1 is in moved-from state (valid but unspecified)
}

TEST_F(BufferTest, MoveAssignmentTransfersOwnership) {
    Buffer buf1(16);
    const auto data = createTestData(10);
    buf1.append(data.data(), data.size());

    Buffer buf2(32);

    buf2 = std::move(buf1);

    EXPECT_EQ(buf2.size(), 10);
}

TEST_F(BufferTest, MoveToSelfIsNoOp) {
    Buffer buf(16);
    const auto data = createTestData(10);
    buf.append(data.data(), data.size());

    const size_t sizeBefore = buf.size();

    // Move to self (should handle gracefully)
    buf = std::move(buf);

    EXPECT_EQ(buf.size(), sizeBefore);
}

/* ========================================================================
 * Performance Tests
 * ======================================================================== */

TEST_F(BufferTest, LargeAppendPerformance) {
    Buffer buf(1024);
    const size_t largeSize = 10 * 1024 * 1024;  // 10 MB
    auto largeData = createTestData(largeSize);

    const auto start = std::chrono::high_resolution_clock::now();

    buf.append(largeData.data(), largeData.size());

    const auto end = std::chrono::high_resolution_clock::now();
    const auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end - start);

    EXPECT_EQ(buf.size(), largeSize);
    EXPECT_LT(duration.count(), 100);  // Should complete in <100ms
}

TEST_F(BufferTest, MultipleAppendsPerformance) {
    Buffer buf(16);
    const auto data = createTestData(100);
    const int iterations = 10000;

    const auto start = std::chrono::high_resolution_clock::now();

    for (int i = 0; i < iterations; ++i) {
        buf.append(data.data(), data.size());
    }

    const auto end = std::chrono::high_resolution_clock::now();
    const auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(
        end - start);

    EXPECT_EQ(buf.size(), data.size() * iterations);
    EXPECT_LT(duration.count(), 1000);  // Should complete in <1 second
}

/* ========================================================================
 * Parameterized Tests
 * ======================================================================== */

class BufferSizeTest : public ::testing::TestWithParam<size_t> {};

TEST_P(BufferSizeTest, VariousSizes) {
    const size_t size = GetParam();
    Buffer buf(size);

    EXPECT_GE(buf.capacity(), size);
    EXPECT_EQ(buf.size(), 0);
}

INSTANTIATE_TEST_SUITE_P(
    SizeRange,
    BufferSizeTest,
    ::testing::Values(0, 1, 10, 100, 1000, 10000, 100000)
);

/* ========================================================================
 * Death Tests (for assertions in debug mode)
 * ======================================================================== */

#ifndef NDEBUG
TEST(BufferDeathTest, AccessOutOfBoundsAsserts) {
    Buffer buf(16);

    EXPECT_DEATH(buf[100], ".*");  // Should assert in debug mode
}
#endif

/* ========================================================================
 * Main Function
 * ======================================================================== */

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```

### Test Output Format

```
[==========] Running 23 tests from 2 test suites.
[----------] Global test environment set-up.
[----------] 20 tests from BufferTest
[ RUN      ] BufferTest.ConstructorCreatesEmptyBuffer
[       OK ] BufferTest.ConstructorCreatesEmptyBuffer (0 ms)
[ RUN      ] BufferTest.AppendIncreasesSize
[       OK ] BufferTest.AppendIncreasesSize (0 ms)
[ RUN      ] BufferTest.MoveConstructorTransfersOwnership
[       OK ] BufferTest.MoveConstructorTransfersOwnership (0 ms)
[----------] 20 tests from BufferTest (15 ms total)

[----------] 3 tests from BufferSizeTest/SizeRange
[ RUN      ] BufferSizeTest/SizeRange.VariousSizes/0
[       OK ] BufferSizeTest/SizeRange.VariousSizes/0 (0 ms)
[----------] 3 tests from BufferSizeTest/SizeRange (2 ms total)

[----------] Global test environment tear-down
[==========] 23 tests from 2 test suites ran. (17 ms total)
[  PASSED  ] 23 tests.
```

## Test Configuration with CMake

```cmake
# In tests/CMakeLists.txt

find_package(GTest REQUIRED)

# Test executable
add_executable(unit_tests
    test_buffer.cpp
    test_config.cpp
    test_utils.cpp
)

target_link_libraries(unit_tests
    PRIVATE
        myproject
        GTest::GTest
        GTest::Main
)

# Set compile options for tests
target_compile_options(unit_tests PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Werror -Wpedantic>
)

# Enable code coverage (GCC/Clang)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(unit_tests PRIVATE --coverage)
    target_link_options(unit_tests PRIVATE --coverage)
endif()

# Discover tests for CTest
include(GoogleTest)
gtest_discover_tests(unit_tests
    PROPERTIES
        LABELS "unit"
        TIMEOUT 30
)

# Add custom test target
add_custom_target(run_tests
    COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure
    DEPENDS unit_tests
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)
```


# 6. Development Workflow
---

## Task Breakdown Methodology

### When to Use Task Breakdown
**Apply systematic breakdown for:**
- Projects estimated >30 minutes
- Multi-module applications
- Library development
- Template-heavy code
- Performance-critical systems
- Cross-platform projects

### Analysis Phase
**Always start with:**
1. **Requirements**: Identify modules, dependencies, C++ standard requirements
2. **Complexity**: Determine scope, performance goals, memory constraints
3. **Prerequisites**: List compiler versions, build tools, third-party libraries
4. **Risk**: Identify template complexity, compilation time, portability issues
5. **Success Metrics**: Define measurable outcomes (performance, compilation time, test coverage)

### Task Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope including C++ version and key features]

### Prerequisites
- C++17 compliant compiler (GCC 9+, Clang 10+, MSVC 2019+)
- CMake 3.15+
- GoogleTest (for testing)
- Optional: Doxygen, clang-format, clang-tidy

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Headers, source files, tests]
**Time**: [15-45 min]
**Dependencies**: [Previous tasks]
**C++ Features**: [Smart pointers, templates, RAII, etc.]

**Prompt**:
    ```
    [Step-by-step instructions]
    [Expected structure with modern C++ idioms]
    [Standards to follow (Core Guidelines)]
    [Success criteria]

    Complete and pause. Confirm before proceeding.
    ```
```

### Subtask Principles
- **Self-Contained**: Independent compilation and testing
- **Modern C++**: Use C++17+ features, avoid C-style code
- **RAII-Based**: All resources managed automatically
- **Exception-Safe**: Strong or basic exception safety guarantee
- **Move-Enabled**: Support move semantics for efficiency
- **Const-Correct**: Proper const usage throughout
- **Testable**: Unit tests for all public APIs

### Quality Gates
- [ ] Functionality verified
- [ ] Modern C++ idioms used
- [ ] RAII for all resources
- [ ] Exception safety verified
- [ ] Move semantics implemented
- [ ] Const correctness checked
- [ ] Documentation complete (Doxygen)
- [ ] Unit tests with >80% coverage
- [ ] Compiles with -Wall -Wextra -Werror
- [ ] No warnings from clang-tidy
- [ ] Formatted with clang-format
- [ ] Performance benchmarked if critical
- [ ] Cross-platform compatibility verified


# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Example:
```
Please run in your terminal:

1. Configure build:
   mkdir build && cd build
   cmake ..

2. Build project:
   cmake --build .

3. Run tests:
   ctest --output-on-failure

4. Share any errors or warnings for assistance.
```

**Never Say:**
- "Let me run this command"
- "I'll execute this"
- "Running the compilation"

**Always Say:**
- "Please run this in your terminal"
- "Execute after verifying prerequisites"
- "Run and share results"

## CMake Commands

```bash
# Configuration
mkdir build && cd build
cmake ..
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake .. -DCMAKE_CXX_COMPILER=clang++
cmake .. -DBUILD_TESTING=OFF

# Build
cmake --build .
cmake --build . --config Release
cmake --build . --target myproject
cmake --build . --parallel 8

# Testing
ctest
ctest --output-on-failure
ctest -R BufferTest        # Run tests matching regex
ctest -j 8                 # Parallel testing

# Installation
cmake --install . --prefix /usr/local

# Clean
cmake --build . --target clean
rm -rf build  # Full clean
```

## Compiler Commands (Manual Build)

```bash
# GCC
g++ -std=c++17 -Wall -Wextra -Werror -O2 -Iinclude \
    src/main.cpp src/buffer.cpp -o myapp

# Clang
clang++ -std=c++17 -Wall -Wextra -Werror -O2 -Iinclude \
        -stdlib=libc++ src/main.cpp -o myapp

# MSVC
cl /std:c++17 /W4 /WX /EHsc /O2 /Iinclude \
   src/main.cpp src/buffer.cpp /Fe:myapp.exe

# Debug build
g++ -std=c++17 -Wall -Wextra -g -O0 -fsanitize=address \
    src/main.cpp -o myapp_debug

# With sanitizers
clang++ -std=c++17 -Wall -Wextra -g -O0 \
        -fsanitize=address -fsanitize=undefined \
        src/main.cpp -o myapp_debug
```

## Formatting and Analysis

```bash
# Format code
clang-format -i src/**/*.cpp include/**/*.hpp

# Check formatting
clang-format --dry-run --Werror src/**/*.cpp

# Static analysis
clang-tidy src/*.cpp -- -std=c++17 -Iinclude

# Run clang-tidy with fixes
clang-tidy -fix src/*.cpp -- -std=c++17 -Iinclude

# cppcheck
cppcheck --enable=all --std=c++17 --suppress=missingIncludeSystem src/
```

## Debugging and Profiling

```bash
# GDB
gdb ./build/myapp
(gdb) run
(gdb) break main
(gdb) continue
(gdb) print variable
(gdb) backtrace

# Valgrind (memory errors)
valgrind --leak-check=full ./build/myapp

# Valgrind (thread safety)
valgrind --tool=helgrind ./build/myapp

# Address Sanitizer
export ASAN_OPTIONS=check_initialization_order=1:detect_stack_use_after_return=1
./build/myapp_asan

# Performance profiling (Linux)
perf record ./build/myapp
perf report

# Google's perf tools
LD_PRELOAD=/usr/lib/libprofiler.so CPUPROFILE=prof.out ./myapp
google-pprof --text ./myapp prof.out
```


# 8. Version Control
---

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:
- Modify CHANGELOG.md versions
- Update CMakeLists.txt version
- Change README.md versions
- Update Doxygen version
- Create tags/releases

### Version Protocol

1. **Assess**:
   ```
   Changes might warrant version update from X.Y.Z:
   - [List changes]
   - [Categorize as patch/minor/major]
   - [Note API/ABI changes]
   - [Breaking changes to templates]
   ```

2. **Request**:
   ```
   Should I update to [version]?
   Note: This requires updates to:
   - CHANGELOG.md
   - CMakeLists.txt (project VERSION)
   - README.md

   Or handle manually?
   ```

3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning for C++ Libraries

- **Patch (Z+1)**: Bug fixes, no API/ABI changes
  - Internal implementation changes
  - Performance improvements
  - Documentation updates

- **Minor (Y+1.0)**: New features, backward-compatible API additions
  - New functions/classes
  - New template specializations
  - Optional parameters with defaults
  - Backward-compatible ABI changes

- **Major (X+1.0.0)**: Breaking changes
  - Removed functions/classes
  - Changed function signatures
  - Changed template parameters
  - ABI-breaking changes
  - Changed exception specifications
  - Changed const-ness

Example:
```
Changes include:
- Added Buffer::reserve() method (minor - new API)
- Fixed memory leak in Buffer::~Buffer() (patch)
- Changed Buffer::append() to take std::span (major - breaking API)
- Changed internal implementation (no version change if private)

Suggested: 1.2.0 → 2.0.0 (major bump due to breaking API change)
```

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**

Never suggest:
- `git add/commit/push`
- `git branch/merge`
- `git tag` or releases
- `git init`
- `git submodule`

### When Git Help IS Requested

```
Since you requested Git help:

1. Check status: git status
2. Stage: git add src/ include/ tests/ CMakeLists.txt
3. Commit: git commit -m "Add Buffer class with RAII"
4. Push: git push origin main

Verify before running:
- Correct branch: git branch
- No uncommitted changes: git status
- Tests pass: cmake --build build && ctest --test-dir build
- No warnings: cmake --build build 2>&1 | grep warning
- Formatted: clang-format --dry-run --Werror src/**/*.cpp
```

### Repository Setup

For new projects:
- Include .gitignore for build/, IDE files, .cache/
- Include .clang-format and .clang-tidy
- Never auto-init repository
- Let user control version control

```
Project created with .gitignore and build configuration.

When ready for version control:
git init
git add .
git commit -m "Initial C++ project setup"

Need Git workflow guidance?
```

### .gitignore for C++ Projects

```gitignore
# Build directories
build/
cmake-build-*/
out/

# Compiled files
*.o
*.obj
*.a
*.lib
*.so
*.dll
*.dylib
*.exe

# CMake
CMakeCache.txt
CMakeFiles/
cmake_install.cmake
CTestTestfile.cmake

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Clang
.clangd/
.cache/
compile_commands.json

# Documentation
docs/html/
docs/latex/

# Coverage
*.gcda
*.gcno
*.gcov
coverage/
```

## DEVLOG.md Updates

Safe to update without permission:
- Task lists
- Development history
- Implementation challenges
- Technical decisions
- Performance notes
- Troubleshooting history

Never include:
- Commit hashes
- Git workflow assumptions
- Version control strategies

Example:
```markdown
### Implementation Challenges

#### Challenge 4: Template Compilation Time
- **Problem**: Heavy template usage caused 5-minute builds
- **Solution**: Extern templates, forward declarations, reduced dependencies
- **Implementation**:
  - Used extern template declarations in headers
  - Explicit instantiations in .cpp files
  - Reduced header includes with forward declarations
- **Trade-offs**: More boilerplate vs. faster compilation
- **Results**: Reduced compilation time from 5 minutes to 1.5 minutes
- **Lessons**: Measure compilation times, extern templates effective for large projects
```


# 9. Implementation Examples
---

## Common Interaction Patterns

### Raw Pointer to Smart Pointer Conversion

**User Request:**
```
"Can you modernize this code with smart pointers?"
```

**Response:**

```cpp
/* Original (C-style with raw pointers) */
class DataProcessor {
public:
    DataProcessor(int size) {
        buffer = new char[size];
        bufferSize = size;
    }

    ~DataProcessor() {
        delete[] buffer;
    }

    void process(const char* data) {
        // Process data
    }

private:
    char* buffer;
    int bufferSize;
};

/* Modern C++ version with smart pointers and RAII */
class DataProcessor {
public:
    explicit DataProcessor(size_t size)
        : buffer_(std::make_unique<char[]>(size)), size_(size) {
        // Initialization complete - no manual cleanup needed
    }

    // Destructor automatically generated - smart pointer handles cleanup
    ~DataProcessor() = default;

    // Move-only type (copying large buffers is expensive)
    DataProcessor(DataProcessor&&) noexcept = default;
    DataProcessor& operator=(DataProcessor&&) noexcept = default;

    // Explicitly delete copy operations
    DataProcessor(const DataProcessor&) = delete;
    DataProcessor& operator=(const DataProcessor&) = delete;

    void process(std::string_view data) {
        // Process data - modern string_view avoids copies
    }

    [[nodiscard]] size_t size() const noexcept {
        return size_;
    }

private:
    std::unique_ptr<char[]> buffer_;  // Automatic cleanup
    size_t size_;
};
```

**Explanation:**
```
**Key Improvements:**

1. **Smart Pointers**: std::unique_ptr automatically manages memory
   - No manual delete needed
   - Exception-safe (cleanup happens even if exception thrown)
   - Move-only semantics prevent accidental copies

2. **RAII**: Resource Acquisition Is Initialization
   - Constructor acquires resource (allocates memory)
   - Destructor releases resource (automatic via unique_ptr)
   - No possibility of forgetting cleanup

3. **Modern C++ Features**:
   - explicit constructor (prevents implicit conversions)
   - noexcept specifications (optimization, interface clarity)
   - [[nodiscard]] attribute (warns if return value ignored)
   - std::string_view (non-owning string reference)
   - = default (compiler-generated special members)
   - = delete (explicitly disabled operations)

4. **Exception Safety**: Strong guarantee
   - If make_unique fails, no object is created
   - No partial construction possible
   - Automatic cleanup on exception

5. **Type Safety**:
   - size_t instead of int (correct type for sizes)
   - Explicit size tracking
   - Const correctness

**Performance**: No overhead compared to manual management, but safer.
```

### Legacy Code Refactoring to Modern C++

**User Request:**
```
"How can I improve this code?"
[Legacy C++ code with manual memory management]
```

**Response:**

```cpp
/* Legacy Code (C++03 style) */
class ConnectionPool {
public:
    ConnectionPool(int maxConnections) {
        this->maxConnections = maxConnections;
        connections = new Connection*[maxConnections];
        for (int i = 0; i < maxConnections; i++) {
            connections[i] = NULL;
        }
    }

    ~ConnectionPool() {
        for (int i = 0; i < maxConnections; i++) {
            if (connections[i] != NULL) {
                delete connections[i];
            }
        }
        delete[] connections;
    }

    Connection* acquire() {
        for (int i = 0; i < maxConnections; i++) {
            if (connections[i] == NULL) {
                connections[i] = new Connection();
                return connections[i];
            }
        }
        return NULL;
    }

    void release(Connection* conn) {
        for (int i = 0; i < maxConnections; i++) {
            if (connections[i] == conn) {
                delete conn;
                connections[i] = NULL;
                break;
            }
        }
    }

private:
    Connection** connections;
    int maxConnections;
};

/* Modern C++ Version (C++17) */
class ConnectionPool {
public:
    explicit ConnectionPool(size_t maxConnections)
        : maxConnections_(maxConnections) {
        connections_.reserve(maxConnections);
    }

    // Automatic cleanup via vector<unique_ptr>
    ~ConnectionPool() = default;

    // Non-copyable, movable
    ConnectionPool(const ConnectionPool&) = delete;
    ConnectionPool& operator=(const ConnectionPool&) = delete;
    ConnectionPool(ConnectionPool&&) noexcept = default;
    ConnectionPool& operator=(ConnectionPool&&) noexcept = default;

    /**
     * @brief Acquire connection from pool
     * @return Connection or nullptr if pool full
     * @note Returns raw pointer for observation (pool retains ownership)
     */
    [[nodiscard]] Connection* acquire() {
        // Find available slot
        auto it = std::find_if(connections_.begin(), connections_.end(),
                               [](const auto& conn) { return conn == nullptr; });

        if (it != connections_.end()) {
            *it = std::make_unique<Connection>();
            return it->get();
        }

        // Pool full - could extend or return nullptr
        if (connections_.size() < maxConnections_) {
            auto& conn = connections_.emplace_back(std::make_unique<Connection>());
            return conn.get();
        }

        return nullptr;  // Pool at capacity
    }

    /**
     * @brief Release connection back to pool
     * @param conn Connection to release (must be from this pool)
     */
    void release(Connection* conn) {
        auto it = std::find_if(connections_.begin(), connections_.end(),
                               [conn](const auto& c) { return c.get() == conn; });

        if (it != connections_.end()) {
            it->reset();  // Destroys connection, sets unique_ptr to nullptr
        }
    }

    [[nodiscard]] size_t size() const noexcept {
        return connections_.size();
    }

    [[nodiscard]] size_t capacity() const noexcept {
        return maxConnections_;
    }

private:
    std::vector<std::unique_ptr<Connection>> connections_;
    size_t maxConnections_;
};

/* Even Better: Use std::optional for return value */
class ConnectionPoolV2 {
public:
    explicit ConnectionPoolV2(size_t maxConnections)
        : maxConnections_(maxConnections) {
        connections_.reserve(maxConnections);
    }

    /**
     * @brief Acquire connection from pool
     * @return Connection handle or std::nullopt if pool full
     */
    [[nodiscard]] std::optional<ConnectionHandle> acquire() {
        // Implementation using RAII handle that auto-releases
    }

private:
    std::vector<std::unique_ptr<Connection>> connections_;
    size_t maxConnections_;
};
```

**Explanation:**
```
**Major Improvements:**

1. **Memory Safety**:
   - vector<unique_ptr> instead of raw pointer array
   - Automatic cleanup, no manual delete needed
   - No possibility of memory leaks
   - Exception-safe throughout

2. **Modern C++ Idioms**:
   - STL algorithms (find_if) instead of manual loops
   - Lambdas for concise predicates
   - auto type deduction
   - Range-based for loops (if needed)

3. **Type Safety**:
   - size_t for sizes (correct type)
   - nullptr instead of NULL
   - explicit constructors
   - Strong type safety

4. **Const Correctness**:
   - Const member functions for non-mutating operations
   - noexcept specifications

5. **Resource Management**:
   - RAII throughout
   - Move semantics enabled
   - Copy disabled (expensive, often wrong for resources)

6. **API Improvements**:
   - Returns nullptr instead of NULL (type-safe)
   - Consider std::optional for clearer semantics
   - Consider RAII handle for auto-release (ConnectionHandle)

**Alternative Design**: Use shared_ptr for shared ownership, or
implement RAII handle class that auto-releases on destruction.
```

## Decision Trees

### Memory Management Strategy

```
Question: How should I manage this resource?

Known lifetime?
├─ Yes → Stack allocation (automatic)
│  └─ Use object directly: MyClass obj;
│
└─ No → Heap allocation
   │
   ├─ Single owner? → unique_ptr
   │  └─ auto ptr = std::make_unique<MyClass>();
   │
   ├─ Shared ownership? → shared_ptr
   │  └─ auto ptr = std::make_shared<MyClass>();
   │
   ├─ Optional value? → std::optional
   │  └─ std::optional<MyClass> maybe;
   │
   └─ Need observation only? → Raw pointer or reference
      ├─ void observe(const MyClass* obj);  // Can be nullptr
      └─ void observe(const MyClass& obj);  // Never null
```

### Error Handling Strategy

```
Question: How should I handle errors?

Programming error (bug)?
└─ Assert or throw std::logic_error
   └─ assert(ptr != nullptr);

Recoverable error?
├─ Expected common case? → Return std::optional or std::expected
│  └─ std::optional<Value> getValue();
│
├─ Rare, exceptional case? → Throw exception
│  ├─ Invalid argument → std::invalid_argument
│  ├─ Out of range → std::out_of_range
│  ├─ Resource issue → std::runtime_error
│  └─ Custom domain error → Custom exception class
│
└─ Performance-critical path? → Return error code or bool
   └─ bool tryOperation(Result* out);
```

### Template vs Non-Template

```
Question: Should this be a template?

Type-independent algorithm?
└─ Yes → Template
   └─ template <typename T> T max(T a, T b);

Used with multiple types?
├─ Yes → Template
│  └─ template <typename T> class Stack { };
│
└─ No → Concrete type
   └─ class StringBuffer { };

Performance-critical with known types?
└─ Explicit instantiation or non-template
   └─ class IntVector { };  // Optimized for int
```


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] **Functionality**: Solves problem completely
- [ ] **Modern C++**: Uses C++17+ features appropriately
- [ ] **RAII**: All resources managed automatically
- [ ] **Smart Pointers**: unique_ptr/shared_ptr instead of raw owning pointers
- [ ] **Exception Safety**: Basic or strong guarantee
- [ ] **Move Semantics**: Implemented for large objects
- [ ] **Const Correctness**: Proper const usage
- [ ] **noexcept**: Specified where appropriate
- [ ] **Rule of Zero/Five**: Properly implemented or defaulted
- [ ] **STL Usage**: Prefer STL over custom implementations
- [ ] **Type Safety**: No C-style casts, use static_cast/dynamic_cast
- [ ] **Documentation**: Doxygen comments for public API
- [ ] **Testing**: Unit tests with good coverage
- [ ] **Compilation**: No warnings with -Wall -Wextra -Werror
- [ ] **Static Analysis**: Clean clang-tidy
- [ ] **Formatting**: Consistent with clang-format

## Before Delivering Project Structure
- [ ] **CMake Build**: Modern CMake (3.15+)
- [ ] **C++ Standard**: Specified (C++17, C++20, etc.)
- [ ] **Directory Structure**: Follows conventions
- [ ] **Testing**: GoogleTest or Catch2 integrated
- [ ] **Documentation**: README, CHANGELOG, DEVLOG, Doxygen
- [ ] **Formatting Config**: .clang-format included
- [ ] **Analysis Config**: .clang-tidy included
- [ ] **Git Ignore**: Proper .gitignore
- [ ] **Version Consistency**: Matches across files
- [ ] **Cross-Platform**: Handles Windows/Linux/macOS
- [ ] **Dependencies**: Clearly documented
- [ ] **License**: LICENSE file included

## Modern C++ Checklist
- [ ] **Smart Pointers**: No manual memory management
- [ ] **RAII**: No naked new/delete
- [ ] **Auto**: Used appropriately
- [ ] **Range-For**: Prefer over index loops
- [ ] **Lambdas**: Used for local functionality
- [ ] **Structured Bindings**: Used for tuple/pair returns (C++17)
- [ ] **std::optional**: For optional return values
- [ ] **std::string_view**: For string parameters
- [ ] **std::span**: For array parameters (C++20)
- [ ] **Concepts**: For template constraints (C++20)

## Performance Considerations
- [ ] **Move Semantics**: Enabled for large objects
- [ ] **Perfect Forwarding**: Used in templates
- [ ] **RVO/NRVO**: Return by value for move-enabled types
- [ ] **Reserve**: Called for containers with known size
- [ ] **Emplace**: Used instead of push for construction
- [ ] **Algorithms**: STL algorithms for operations
- [ ] **Compilation Time**: Monitored for templates
- [ ] **Benchmarks**: Performance-critical code measured

## Exception Safety
- [ ] **RAII**: Resources cleaned up automatically
- [ ] **noexcept**: Move operations marked noexcept
- [ ] **Strong Guarantee**: Copy-and-swap for assignments
- [ ] **Basic Guarantee**: Valid state after exception
- [ ] **No Leaks**: Resources not leaked on exception path

---

# 11. Modern C++ Specific Patterns
---

## C++17 Features

### Structured Bindings

```cpp
// Tuple decomposition
std::tuple<int, std::string, double> getData();
auto [id, name, value] = getData();

// Pair decomposition
std::map<std::string, int> scores;
for (const auto& [key, value] : scores) {
    std::cout << key << ": " << value << '\n';
}

// Struct decomposition
struct Point { int x; int y; };
Point p{10, 20};
auto [px, py] = p;
```

### std::optional

```cpp
// Optional return values
std::optional<std::string> findUser(int id) {
    if (/* not found */) {
        return std::nullopt;
    }
    return userName;
}

// Usage
if (auto user = findUser(42); user.has_value()) {
    std::cout << "Found: " << *user << '\n';
}

// Or with value_or
std::string name = findUser(42).value_or("Unknown");
```

### std::string_view

```cpp
// Non-owning string reference (no copies)
void processString(std::string_view sv) {
    // sv is a view, no allocation
    std::cout << sv << '\n';
}

// Usage
std::string str = "Hello";
processString(str);           // OK
processString("World");       // OK, no temp std::string
processString(str.substr(0, 3));  // OK, no copy

// Warning: lifetime issues
std::string_view dangerous() {
    std::string temp = "temporary";
    return temp;  // WRONG: temp destroyed, view dangles
}
```

### std::variant

```cpp
// Type-safe union
using Value = std::variant<int, double, std::string>;

Value v = 42;
v = 3.14;
v = "hello";

// Visit with lambda
std::visit([](auto&& arg) {
    using T = std::decay_t<decltype(arg)>;
    if constexpr (std::is_same_v<T, int>) {
        std::cout << "int: " << arg << '\n';
    } else if constexpr (std::is_same_v<T, double>) {
        std::cout << "double: " << arg << '\n';
    } else {
        std::cout << "string: " << arg << '\n';
    }
}, v);

// Get value
if (auto* p = std::get_if<int>(&v)) {
    std::cout << "Value: " << *p << '\n';
}
```

### if/switch with initializer

```cpp
// if with initializer
if (auto it = map.find(key); it != map.end()) {
    // it is in scope
    process(it->second);
}

// switch with initializer
switch (auto value = getValue(); value) {
    case 1: /* ... */ break;
    case 2: /* ... */ break;
}
```

## C++20 Features

### Concepts

```cpp
// Define concepts
template <typename T>
concept Numeric = std::is_arithmetic_v<T>;

template <typename T>
concept Addable = requires(T a, T b) {
    { a + b } -> std::convertible_to<T>;
};

// Use concepts
template <Numeric T>
T add(T a, T b) {
    return a + b;
}

// Or as requires clause
template <typename T>
requires Numeric<T>
T multiply(T a, T b) {
    return a * b;
}

// Abbreviated function template
auto divide(Numeric auto a, Numeric auto b) {
    return a / b;
}
```

### Ranges

```cpp
#include <ranges>

std::vector<int> numbers = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10};

// Filter even numbers, square them, take first 3
auto result = numbers
    | std::views::filter([](int n) { return n % 2 == 0; })
    | std::views::transform([](int n) { return n * n; })
    | std::views::take(3);

// Lazy evaluation - only computed when accessed
for (int value : result) {
    std::cout << value << '\n';  // 4, 16, 36
}

// Or collect to container
std::vector<int> vec(result.begin(), result.end());
```

### std::span

```cpp
// Non-owning view of contiguous sequence
void processData(std::span<const int> data) {
    for (int value : data) {
        // Process
    }
}

// Works with any contiguous container
std::vector<int> vec = {1, 2, 3, 4, 5};
std::array<int, 5> arr = {1, 2, 3, 4, 5};
int carray[] = {1, 2, 3, 4, 5};

processData(vec);    // OK
processData(arr);    // OK
processData(carray); // OK

// Subspans
std::span<int> s(vec);
auto first3 = s.subspan(0, 3);
auto last2 = s.subspan(3);
```

### Coroutines (Advanced)

```cpp
// Generator using coroutines
#include <coroutine>

template <typename T>
struct Generator {
    struct promise_type {
        T current_value;

        auto get_return_object() {
            return Generator{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        auto initial_suspend() { return std::suspend_always{}; }
        auto final_suspend() noexcept { return std::suspend_always{}; }
        void return_void() {}
        void unhandled_exception() { std::terminate(); }

        auto yield_value(T value) {
            current_value = value;
            return std::suspend_always{};
        }
    };

    std::coroutine_handle<promise_type> coro;

    Generator(std::coroutine_handle<promise_type> h) : coro(h) {}
    ~Generator() { if (coro) coro.destroy(); }

    bool next() {
        coro.resume();
        return !coro.done();
    }

    T value() { return coro.promise().current_value; }
};

// Usage
Generator<int> fibonacci() {
    int a = 0, b = 1;
    while (true) {
        co_yield a;
        auto tmp = a;
        a = b;
        b = tmp + b;
    }
}

// Use generator
auto gen = fibonacci();
for (int i = 0; i < 10; ++i) {
    gen.next();
    std::cout << gen.value() << '\n';
}
```

## Performance Patterns

### Perfect Forwarding

```cpp
template <typename T>
class Factory {
public:
    // Perfect forwarding to constructor
    template <typename... Args>
    static std::unique_ptr<T> create(Args&&... args) {
        return std::make_unique<T>(std::forward<Args>(args)...);
    }
};

// Universal reference + std::forward preserves value category
template <typename T>
void wrapper(T&& arg) {
    actualFunction(std::forward<T>(arg));
}
```

### Copy Elision and RVO

```cpp
// Return value optimization (RVO)
Widget createWidget() {
    return Widget{};  // No copy, Widget constructed in return slot
}

// Named RVO (NRVO)
Widget createConfiguredWidget() {
    Widget w;
    w.configure();
    return w;  // Typically elided, may not be guaranteed
}

// C++17 guaranteed copy elision
Widget w = createWidget();  // Guaranteed no copy

// Move when RVO doesn't apply
Widget moveExample() {
    Widget w;
    if (condition) {
        return w;  // RVO may apply
    }
    Widget other;
    return other;  // RVO doesn't apply (multiple return paths)
                   // But move is automatic (implicit move)
}
```

### Small String Optimization (SSO)

```cpp
// Most std::string implementations use SSO
// Small strings (typically ≤15-23 chars) stored inline, no heap allocation

std::string small = "Short";      // No allocation
std::string large = "Very long string that exceeds SSO threshold";  // Heap allocation

// Design classes with SSO in mind
class SmallString {
    static constexpr size_t kMaxInline = 23;

    union {
        char inline_[kMaxInline + 1];
        struct {
            char* ptr;
            size_t size;
            size_t capacity;
        } heap_;
    };
    bool isInline_;
};
```

---

**End of C++ Development System Instructions**
