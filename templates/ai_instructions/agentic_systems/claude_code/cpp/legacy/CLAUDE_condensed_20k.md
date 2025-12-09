---
template_id: CLAUDE_condensed_20k
template_name: Cpp - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: claude_code
phase: cpp
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tools:

  - unity

  - cmocka

  - check
tags:

  - claude-code

  - c
---
# CLAUDE.md - C++ Development System Instructions
*Condensed system prompt for Claude Code - Optimized for Modern C++ development*

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

- **Modernize code**: Section 11

## Context-Aware Behavior
- **For applications**: Use modern C++ features, STL

- **For libraries**: Clear API, header-only when appropriate

- **For performance**: Profile first, optimize second

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation

- Minimal testing setup

- Focus on core functionality

### Full Mode (for new projects)
- Complete architecture with CMake

- Comprehensive testing

- Full documentation

## Claude Code Terminal Commands
- **Build**: `cmake --build build`

- **Test**: `ctest --test-dir build`

- **Format**: `clang-format -i src/**/*.cpp`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding

- Never make assumptions about missing requirements

- Frame questions to gather specific technical requirements

- Clarify C++ standard version (C++11, 14, 17, 20, 23)

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work

- Explain implementation details, reasoning, and modern C++ idioms

- Enable learning through understanding, not copy-paste

- Reference C++ Core Guidelines

- Explain RAII, move semantics, templates

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions

- Analyze problems independently

- Compare alternatives (STL vs custom, smart vs raw pointers)

- Clearly explain reasoning and trade-offs

- Recommend modern C++ over C-style code

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity

- **Code Modification**: Edit originals, don't create '_enhanced' versions

- **Codebase Cleanup**: Remove obsolete code

- **Refactoring**: Use modern C++ features

### Quality Assurance
- Review code for: quality, efficiency, best practices, exception safety, const-correctness

- If already optimal, confirm briefly with reasoning


# 2. Project Architecture
---

## Standard C++ Application Structure

```
project_name/
├── include/                       # Public headers
│   └── project_name/
│       ├── api.hpp
│       └── types.hpp
├── src/                           # Source implementation
│   ├── main.cpp
│   └── core/
├── tests/                         # Testing suite
│   ├── test_buffer.cpp
│   └── CMakeLists.txt
├── build/                         # Build output (gitignored)
├── docs/                          # Documentation
├── CMakeLists.txt
├── .clang-format
├── .clang-tidy
├── CHANGELOG.md
├── README.md
├── DEVLOG.md
└── .gitignore
```

## CMakeLists.txt Template

```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Werror -pedantic)
endif()

add_library(myproject
    src/core/buffer.cpp
    src/core/utils.cpp
)

target_include_directories(myproject
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
)

add_executable(myproject_app src/main.cpp)
target_link_libraries(myproject_app PRIVATE myproject)

if(BUILD_TESTING)
    enable_testing()
    add_subdirectory(tests)
endif()
```

## Tests CMakeLists.txt

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


# 3. Code Standards
---

## Include Organization

Order (blank line between):

1. Corresponding header (for .cpp files)

2. C++ standard library (alphabetically)

3. Third-party libraries (alphabetically)

4. Project headers (alphabetically)

```cpp
#include "project_name/buffer.hpp"

#include <algorithm>
#include <memory>
#include <vector>

#include <fmt/format.h>

#include "project_name/types.hpp"
#include "project_name/utils.hpp"
```

## Naming Conventions

```cpp
// Classes and Types: PascalCase
class BufferManager { };
struct ConfigData { };
enum class LogLevel { };

// Functions: camelCase
void processData();
int calculateTotal();

// Variables: camelCase
int itemCount = 0;
std::string userName;

// Constants: kPascalCase or UPPER_CASE
constexpr int kMaxSize = 1024;

// Member variables: trailing underscore
class MyClass {
private:
    int count_;
    std::string name_;
};

// Namespace: lowercase
namespace project_name { }
```

## Modern C++ Features

**Smart Pointers:**
```cpp
// Prefer unique_ptr for ownership
auto buffer = std::make_unique<Buffer>(1024);

// Use shared_ptr for shared ownership
auto config = std::make_shared<Config>();

// Raw non-owning pointers OK for observation
void process(const Buffer* buf);  // Non-owning
```

**RAII:**
```cpp
class File {
public:
    explicit File(const std::string& path)
        : file_(std::fopen(path.c_str(), "r")) {
        if (!file_) throw std::runtime_error("Failed to open");
    }

    ~File() {
        if (file_) std::fclose(file_);
    }

    File(const File&) = delete;
    File& operator=(const File&) = delete;
    File(File&& other) noexcept : file_(other.file_) {
        other.file_ = nullptr;
    }

private:
    FILE* file_;
};
```

**Auto and Range-For:**
```cpp
// Use auto appropriately
auto value = computeValue();
auto ptr = std::make_unique<Widget>();

// Range-based for
for (const auto& item : container) {
    // item is const reference
}

// Structured bindings (C++17)
for (const auto& [key, value] : map) {
    std::cout << key << ": " << value << '\n';
}
```

**Move Semantics:**
```cpp
class Buffer {
public:
    Buffer(size_t size) : data_(new char[size]), size_(size) {}
    ~Buffer() { delete[] data_; }

    // Copy
    Buffer(const Buffer& other)
        : data_(new char[other.size_]), size_(other.size_) {
        std::copy(other.data_, other.data_ + size_, data_);
    }

    // Move
    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

private:
    char* data_;
    size_t size_;
};
```

**Const Correctness:**
```cpp
class Data {
public:
    size_t size() const { return data_.size(); }  // Const method
    void add(const std::string& s) { data_.push_back(s); }

    // Const and non-const overloads
    const std::string& get(size_t i) const { return data_[i]; }
    std::string& get(size_t i) { return data_[i]; }

private:
    std::vector<std::string> data_;
};

// Parameters: const ref for read-only
void process(const std::vector<int>& data);
```

**Templates:**
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
    void push(T item) { data_.push_back(std::move(item)); }
    T pop() {
        T item = std::move(data_.back());
        data_.pop_back();
        return item;
    }
private:
    std::vector<T> data_;
};

// Generic lambda (C++14)
auto add = [](auto a, auto b) { return a + b; };
```

**Lambdas:**
```cpp
// Basic lambda
auto add = [](int a, int b) { return a + b; };

// Capture by value
int multiplier = 5;
auto multiply = [multiplier](int x) { return x * multiplier; };

// Capture by reference
int sum = 0;
auto accumulate = [&sum](int x) { sum += x; };

// With STL algorithms
std::sort(vec.begin(), vec.end(),
          [](int a, int b) { return a > b; });
```

## Exception Safety

```cpp
class Buffer {
public:
    // Strong guarantee: copy-and-swap
    Buffer& operator=(const Buffer& other) {
        Buffer temp(other);
        swap(temp);
        return *this;
    }

    // noexcept for moves
    Buffer(Buffer&&) noexcept = default;
    Buffer& operator=(Buffer&&) noexcept = default;

    void swap(Buffer& other) noexcept {
        std::swap(data_, other.data_);
    }

private:
    std::vector<uint8_t> data_;
};

// RAII ensures cleanup
void processFile(const std::string& file) {
    std::ifstream f(file);  // RAII: auto close
    if (!f) throw std::runtime_error("Cannot open");

    // Process - exceptions handled by RAII
}

// Use lock_guard
void threadSafe() {
    std::lock_guard<std::mutex> lock(mutex_);
    // Automatic unlock
}
```


# 4. Documentation Standards
---

## Doxygen Comments

```cpp
/**

 * @file buffer.hpp

 * @brief Dynamic buffer with automatic growth

 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */

/**

 * @class Buffer

 * @brief Dynamic byte buffer with RAII
 *

 * Example:

 * @code

 * Buffer buf(1024);

 * buf.append(data, size);

 * @endcode
 */
class Buffer {
public:
    /**

     * @brief Construct buffer

     * @param[in] capacity Initial capacity

     * @throws std::bad_alloc If allocation fails
     */
    explicit Buffer(size_t capacity);

    /**

     * @brief Get size

     * @return Size in bytes
     */
    [[nodiscard]] size_t size() const noexcept;
};

/**

 * @brief Parse configuration

 * @param[in] filename Path to file

 * @return Configuration data

 * @throws std::runtime_error On error
 */
ConfigData parseConfig(const std::string& filename);
```

## README.md Structure

```markdown
# [Project Name] - v[X.Y.Z]

## Overview
[2-3 sentence description]

## Features
- Modern C++17

- Exception-safe with RAII

- Comprehensive tests

## Requirements
- CMake 3.15+

- C++17 compiler (GCC 9+, Clang 10+, MSVC 2019+)

- GoogleTest

## Building
    ```bash
    mkdir build && cd build
    cmake ..
    cmake --build .
    ```

## Usage
    ```cpp
    #include <project_name/buffer.hpp>

    Buffer buf(1024);
    buf.append(data, size);
    ```

## Testing
    ```bash
    ctest --test-dir build
    ```
```

## CHANGELOG.md

```markdown
# Changelog

## [Unreleased]

### Comment Guidelines

**Placement and Style:**

- **Above code blocks**: Comments explain why, not just what

- **No inline comments**: Avoid same-line comments unless extremely clear

- **No meta-commentary**: Don't document editing history

- **No change tracking**: Never add comments like "changed value to 12" or "updated parameter"

- **Descriptive**: Focus on logic, decision reasoning, and non-obvious behavior

**Prohibited Comment Patterns:**
```cpp
// BAD: Don't document changes
int result = calculate(12);  // Changed from 10 to 12
std::string value = newValue;  // Updated to use newValue instead of oldValue

// GOOD: Explain reasoning
int result = calculate(12);  // Use 12 to match API rate limit threshold
std::string value = newValue;  // Cache invalidation requires fresh value
```


### Added
### Changed
### Fixed

## [0.1.0] - 2025-01-01
### Added
- Initial release

- Buffer class with RAII

- CMake build system
```

## DEVLOG.md

```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Implement move semantics

### Medium Priority
- [ ] Add benchmarks

## Development History

### Implementation Challenges
- **Challenge X**: [Problem]

  - *Solution*: [Resolution]

  - *Trade-offs*: [Considerations]
```


# 5. Testing Framework
---

## GoogleTest

```cpp
#include <gtest/gtest.h>
#include "project_name/buffer.hpp"

class BufferTest : public ::testing::Test {
protected:
    void SetUp() override { }
    void TearDown() override { }
};

TEST_F(BufferTest, ConstructorCreatesEmpty) {
    Buffer buf(1024);
    EXPECT_EQ(buf.size(), 0);
    EXPECT_GE(buf.capacity(), 1024);
}

TEST_F(BufferTest, AppendIncreasesSize) {
    Buffer buf(16);
    std::vector<uint8_t> data = {1, 2, 3};

    buf.append(data.data(), data.size());

    EXPECT_EQ(buf.size(), 3);
}

TEST_F(BufferTest, AppendNullThrows) {
    Buffer buf(16);
    EXPECT_THROW(buf.append(nullptr, 10), std::invalid_argument);
}

TEST_F(BufferTest, MoveConstructor) {
    Buffer buf1(16);
    buf1.append(data, 10);

    Buffer buf2(std::move(buf1));

    EXPECT_EQ(buf2.size(), 10);
}

// Parameterized tests
class BufferSizeTest : public ::testing::TestWithParam<size_t> {};

TEST_P(BufferSizeTest, VariousSizes) {
    size_t size = GetParam();
    Buffer buf(size);
    EXPECT_GE(buf.capacity(), size);
}

INSTANTIATE_TEST_SUITE_P(
    SizeRange,
    BufferSizeTest,
    ::testing::Values(0, 1, 10, 100, 1000)
);

int main(int argc, char** argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
```


# 6. Development Workflow
---

## Task Breakdown

### When to Use
- Projects >30 minutes

- Multi-module applications

- Library development

- Template-heavy code

### Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope with C++ version]

### Prerequisites
- C++17 compiler

- CMake 3.15+

- GoogleTest

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Files]
**Time**: [15-45 min]
**C++ Features**: [Smart pointers, RAII, templates]

**Prompt**:
    ```
    [Instructions]
    [Modern C++ idioms]
    [Success criteria]
    ```
```

### Quality Gates
- [ ] Functionality verified

- [ ] Modern C++ used

- [ ] RAII implemented

- [ ] Exception safety

- [ ] Move semantics

- [ ] Documentation

- [ ] Tests with >80% coverage

- [ ] No compiler warnings

- [ ] clang-tidy clean


## Iterative Testing Protocol

**When implementing features or fixing bugs:**

1. **Create temp tests** in `tests/temp/` (e.g., `test_feature_validation.cpp`)

2. **Write challenging tests** with edge cases

3. **Implement solution** following code standards

4. **Run tests and iterate**:

   - If FAIL: Document in DEVLOG.md, modify code, repeat

   - If PASS: Proceed to cleanup

5. **Delete temp tests** after successful implementation

6. **Document process** in DEVLOG.md with iteration count

**Benefits**: Ensures solutions work, documents problem-solving, prevents premature success claims, maintains clean repository



# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Pattern:
```
Please run in your terminal:

1. Configure:
   mkdir build && cd build
   cmake ..

2. Build:
   cmake --build .

3. Test:
   ctest --output-on-failure
```

## CMake Commands

```bash
# Configure
cmake -B build
cmake -B build -DCMAKE_BUILD_TYPE=Debug

# Build
cmake --build build
cmake --build build --parallel 8

# Test
ctest --test-dir build
ctest --test-dir build --output-on-failure

# Install
cmake --install build --prefix /usr/local
```

## Compiler Commands

```bash
# GCC
g++ -std=c++17 -Wall -Wextra -Werror -O2 main.cpp -o app

# Clang
clang++ -std=c++17 -Wall -Wextra -Werror main.cpp -o app

# With sanitizers
g++ -std=c++17 -g -fsanitize=address,undefined main.cpp -o app
```

## Tools

```bash
# Format
clang-format -i src/**/*.cpp

# Analysis
clang-tidy src/*.cpp -- -std=c++17

# Valgrind
valgrind --leak-check=full ./build/app
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

### Version Protocol

1. **Assess**: "Changes might warrant update from X.Y.Z"

2. **Request**: "Should I update to [version]?"

3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, no API changes

- **Minor (Y+1.0)**: New features, backward-compatible

- **Major (X+1.0.0)**: Breaking changes

## Git Operations

### Restrictions
**CRITICAL: Never suggest Git commands unless explicitly requested.**

Only when requested:
```
Since you requested Git help:

1. Stage: git add src/ include/ CMakeLists.txt

2. Commit: git commit -m "Add Buffer class"

3. Push: git push origin main
```

### DEVLOG.md Updates
Safe to update without permission:

- Task lists

- Development history

- Challenges/solutions


# 9. Implementation Examples
---

## Modernize Code

```cpp
/* Legacy (C-style) */
class Data {
public:
    Data(int size) {
        buffer = new char[size];
        this->size = size;
    }
    ~Data() { delete[] buffer; }
private:
    char* buffer;
    int size;
};

/* Modern C++ */
class Data {
public:
    explicit Data(size_t size)
        : buffer_(std::make_unique<char[]>(size)), size_(size) { }

    ~Data() = default;  // Automatic cleanup

    Data(Data&&) noexcept = default;
    Data& operator=(Data&&) noexcept = default;

    Data(const Data&) = delete;
    Data& operator=(const Data&) = delete;

private:
    std::unique_ptr<char[]> buffer_;
    size_t size_;
};
```

## Smart Pointers

```cpp
// Ownership
auto ptr = std::make_unique<Widget>();

// Shared ownership
auto shared = std::make_shared<Config>();

// Observation (non-owning)
void observe(const Widget* w);
void observe(const Widget& w);
```

## Decision Trees

### Memory Management
```
Known lifetime? → Stack allocation
Single owner? → unique_ptr
Shared ownership? → shared_ptr
Optional? → std::optional
```

### Error Handling
```
Expected common? → std::optional
Rare exceptional? → throw exception
Performance-critical? → error code/bool
```


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] Solves problem

- [ ] Modern C++ (C++17+)

- [ ] RAII for resources

- [ ] Smart pointers (no raw owning pointers)

- [ ] Exception safety

- [ ] Move semantics

- [ ] Const correctness

- [ ] noexcept where appropriate

- [ ] Documentation

- [ ] Tests

- [ ] No warnings (-Wall -Wextra)

- [ ] clang-tidy clean

## Before Delivering Project
- [ ] CMake build (3.15+)

- [ ] C++ standard specified

- [ ] Testing integrated

- [ ] Documentation

- [ ] .clang-format

- [ ] .clang-tidy

- [ ] .gitignore

- [ ] Cross-platform

## Modern C++ Checklist
- [ ] Smart pointers (no new/delete)

- [ ] RAII throughout

- [ ] Auto where appropriate

- [ ] Range-for loops

- [ ] Lambdas for local functions

- [ ] std::optional for optional values

- [ ] std::string_view for strings

---

# 11. Modern C++ Patterns
---

## C++17 Features

```cpp
// Structured bindings
auto [id, name, value] = getData();

for (const auto& [key, value] : map) {
    std::cout << key << ": " << value << '\n';
}

// std::optional
std::optional<User> findUser(int id) {
    if (/* not found */) return std::nullopt;
    return user;
}

if (auto user = findUser(42); user.has_value()) {
    std::cout << *user << '\n';
}

// std::string_view
void process(std::string_view sv) {
    // No copies
}

// if with initializer
if (auto it = map.find(key); it != map.end()) {
    use(it->second);
}
```

## C++20 Features

```cpp
// Concepts
template <typename T>
concept Numeric = std::is_arithmetic_v<T>;

template <Numeric T>
T add(T a, T b) { return a + b; }

// Ranges
auto result = numbers
    | std::views::filter([](int n) { return n % 2 == 0; })
    | std::views::transform([](int n) { return n * n; });

// std::span
void process(std::span<const int> data) {
    for (int value : data) { /* ... */ }
}
```

## Performance

```cpp
// Perfect forwarding
template <typename... Args>
auto create(Args&&... args) {
    return std::make_unique<T>(std::forward<Args>(args)...);
}

// Move semantics
Widget createWidget() {
    return Widget{};  // No copy
}

// Reserve for known sizes
std::vector<int> vec;
vec.reserve(1000);  // Avoid reallocations
```

---
