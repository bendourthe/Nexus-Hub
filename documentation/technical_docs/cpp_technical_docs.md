# C++ Technical Documentation

## Objective
Create comprehensive technical documentation that captures architecture decisions, system design, data flows, integration points, and development workflows for developers and technical stakeholders.

## Output Directory Structure

All outputs should be saved in organized directories:

```
documentation/technical_docs/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `documentation/technical_docs/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Architecture Documentation
- [ ] System architecture overview with diagrams
- [ ] Component responsibilities clearly defined
- [ ] Technology stack documented with rationale
- [ ] Architectural patterns explained
- [ ] Performance and memory considerations
- [ ] Security architecture documented

### Design Decisions
- [ ] Key technical decisions documented with rationale
- [ ] Alternative approaches considered
- [ ] Trade-offs and constraints explained
- [ ] Decision timeline and context
- [ ] Impact assessment of decisions

### Module Organization
- [ ] Directory/namespace structure explained
- [ ] Module dependencies mapped
- [ ] Public vs private interfaces defined
- [ ] Header organization documented
- [ ] Code organization principles

### Data Flow
- [ ] Data flow diagrams created
- [ ] RAII patterns documented
- [ ] Move semantics usage explained
- [ ] Data transformation pipelines
- [ ] Error handling patterns

### Integration Points
- [ ] External library integrations documented
- [ ] API interfaces
- [ ] Third-party dependencies
- [ ] System interfaces
- [ ] Protocol implementations

### Development Workflow
- [ ] Development environment setup
- [ ] Build system documentation
- [ ] Testing strategy
- [ ] Debugging approaches
- [ ] Release process

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Technical Documentation Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="documentation/technical_docs"
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

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please create comprehensive technical documentation for this C++ project following this protocol:

## Phase 1: Architecture Analysis

```markdown
# System Architecture

## Overview

[Project Name] is a [library/application/framework] written in C++[17/20/23] that [high-level purpose].

## Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Standard | C++ | 17/20/23 | Modern features, performance |
| Build System | CMake/Bazel/Meson | Latest | Cross-platform, dependency management |
| Testing | Google Test/Catch2 | Latest | Comprehensive test framework |
| Documentation | Doxygen | Latest | API documentation |
| Package Manager | Conan/vcpkg | Latest | Dependency management |

## Project Structure

```
project/
├── include/                    # Public headers
│   └── mylib/
│       ├── mylib.hpp          # Main public API
│       ├── types.hpp          # Public types
│       └── exceptions.hpp     # Exception types
│
├── src/                       # Implementation
│   ├── core/
│   │   ├── engine.cpp
│   │   └── engine.hpp         # Private header
│   ├── utils/
│   │   └── helpers.cpp
│   └── platform/
│       ├── linux.cpp
│       └── windows.cpp
│
├── tests/                     # Test suite
│   ├── unit/
│   │   └── test_engine.cpp
│   └── integration/
│       └── test_api.cpp
│
├── examples/                  # Example programs
├── docs/                      # Documentation
├── CMakeLists.txt            # Build configuration
└── conanfile.txt             # Dependencies
```

## Core Module Implementation

### Public API (include/mylib/mylib.hpp)
```cpp
#pragma once

#include <memory>
#include <string>
#include <optional>
#include <expected> // C++23

namespace mylib {

/**
 * @brief Configuration for the library
 */
struct Config {
    size_t buffer_size = 1024;
    bool enable_logging = false;
};

/**
 * @brief Main library class
 */
class Engine {
public:
    /**
     * @brief Construct engine with configuration
     * @param config Configuration options
     * @throws std::invalid_argument if config is invalid
     */
    explicit Engine(const Config& config);

    // Rule of Five
    ~Engine();
    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;
    Engine(Engine&&) noexcept;
    Engine& operator=(Engine&&) noexcept;

    /**
     * @brief Process input data
     * @param input Input string
     * @return Result or error
     */
    std::expected<std::string, Error> process(std::string_view input);

    /**
     * @brief Get current status
     */
    [[nodiscard]] Status get_status() const noexcept;

private:
    class Impl;  // Pimpl idiom
    std::unique_ptr<Impl> impl_;
};

} // namespace mylib
```

### Implementation (src/core/engine.cpp)
```cpp
#include "mylib/mylib.hpp"
#include "engine.hpp"  // Private header

#include <algorithm>
#include <stdexcept>

namespace mylib {

// Pimpl implementation
class Engine::Impl {
public:
    explicit Impl(const Config& config)
        : config_(config)
        , buffer_(config.buffer_size)
    {
        if (config.buffer_size == 0) {
            throw std::invalid_argument("Buffer size must be > 0");
        }
    }

    std::expected<std::string, Error> process(std::string_view input) {
        if (input.empty()) {
            return std::unexpected(Error::InvalidInput);
        }

        // Process with RAII resource management
        auto resource = acquire_resource();
        if (!resource) {
            return std::unexpected(Error::ResourceUnavailable);
        }

        std::string result;
        result.reserve(input.size());
        std::transform(input.begin(), input.end(),
                      std::back_inserter(result),
                      [](char c) { return std::toupper(c); });

        return result;
    }

    [[nodiscard]] Status get_status() const noexcept {
        return status_;
    }

private:
    Config config_;
    std::vector<char> buffer_;
    Status status_ = Status::Ready;

    std::unique_ptr<Resource> acquire_resource() {
        // RAII resource acquisition
        return std::make_unique<Resource>();
    }
};

// Engine implementation
Engine::Engine(const Config& config)
    : impl_(std::make_unique<Impl>(config))
{
}

Engine::~Engine() = default;

Engine::Engine(Engine&&) noexcept = default;
Engine& Engine::operator=(Engine&&) noexcept = default;

std::expected<std::string, Error> Engine::process(std::string_view input) {
    return impl_->process(input);
}

Status Engine::get_status() const noexcept {
    return impl_->get_status();
}

} // namespace mylib
```

## Modern C++ Patterns

### RAII (Resource Acquisition Is Initialization)
```cpp
class FileHandle {
public:
    explicit FileHandle(const std::string& filename)
        : file_(std::fopen(filename.c_str(), "r"))
    {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }

    ~FileHandle() {
        if (file_) {
            std::fclose(file_);
        }
    }

    // Delete copy, allow move
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;
    FileHandle(FileHandle&& other) noexcept : file_(other.file_) {
        other.file_ = nullptr;
    }

    FILE* get() const noexcept { return file_; }

private:
    FILE* file_;
};

// Usage
void process_file(const std::string& filename) {
    FileHandle file(filename);  // Automatically closes on scope exit
    // Use file.get()
} // File automatically closed here
```

### Smart Pointers
```cpp
class DataProcessor {
public:
    // Factory method returning unique_ptr
    static std::unique_ptr<DataProcessor> create(const Config& config) {
        return std::make_unique<DataProcessor>(config);
    }

    // Shared ownership with shared_ptr
    std::shared_ptr<Cache> get_cache() const {
        return cache_;
    }

    // Weak reference with weak_ptr
    void set_parent(std::shared_ptr<Parent> parent) {
        parent_ = parent;  // Doesn't increase ref count
    }

private:
    std::shared_ptr<Cache> cache_;
    std::weak_ptr<Parent> parent_;
};
```

### Move Semantics
```cpp
class LargeObject {
public:
    // Constructor
    LargeObject(size_t size) : data_(new char[size]), size_(size) {}

    // Destructor
    ~LargeObject() { delete[] data_; }

    // Move constructor
    LargeObject(LargeObject&& other) noexcept
        : data_(other.data_), size_(other.size_)
    {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    // Move assignment
    LargeObject& operator=(LargeObject&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    // Delete copy operations
    LargeObject(const LargeObject&) = delete;
    LargeObject& operator=(const LargeObject&) = delete;

private:
    char* data_;
    size_t size_;
};

// Usage
LargeObject obj1(1000);
LargeObject obj2 = std::move(obj1);  // Move, not copy
```

### Templates and Concepts (C++20)
```cpp
// Concept definition
template<typename T>
concept Serializable = requires(T t, std::ostream& os) {
    { t.serialize(os) } -> std::same_as<void>;
};

// Template class with concept constraint
template<Serializable T>
class Container {
public:
    void add(T item) {
        items_.push_back(std::move(item));
    }

    void save(std::ostream& os) const {
        for (const auto& item : items_) {
            item.serialize(os);
        }
    }

private:
    std::vector<T> items_;
};
```

## Error Handling

### Exceptions
```cpp
// Custom exception hierarchy
class LibraryException : public std::exception {
public:
    explicit LibraryException(std::string message)
        : message_(std::move(message)) {}

    const char* what() const noexcept override {
        return message_.c_str();
    }

private:
    std::string message_;
};

class InvalidArgumentException : public LibraryException {
    using LibraryException::LibraryException;
};

// Usage
void process(const std::string& input) {
    if (input.empty()) {
        throw InvalidArgumentException("Input cannot be empty");
    }
    // Process...
}
```

### std::expected (C++23) / std::optional
```cpp
// Using std::expected for error handling without exceptions
enum class Error {
    InvalidInput,
    NetworkError,
    Timeout
};

std::expected<int, Error> parse_int(std::string_view str) {
    if (str.empty()) {
        return std::unexpected(Error::InvalidInput);
    }

    try {
        return std::stoi(std::string(str));
    } catch (...) {
        return std::unexpected(Error::InvalidInput);
    }
}

// Using std::optional for nullable returns
std::optional<User> find_user(int id) {
    auto it = users_.find(id);
    if (it == users_.end()) {
        return std::nullopt;
    }
    return it->second;
}

// Usage
if (auto user = find_user(42)) {
    std::cout << user->name << '\n';
} else {
    std::cout << "User not found\n";
}
```

## Testing

### Google Test
```cpp
#include <gtest/gtest.h>
#include "mylib/mylib.hpp"

class EngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        config_ = mylib::Config{.buffer_size = 1024};
    }

    mylib::Config config_;
};

TEST_F(EngineTest, ConstructorSuccess) {
    ASSERT_NO_THROW(mylib::Engine engine(config_));
}

TEST_F(EngineTest, ProcessValidInput) {
    mylib::Engine engine(config_);
    auto result = engine.process("hello");

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, "HELLO");
}

TEST_F(EngineTest, ProcessEmptyInputReturnsError) {
    mylib::Engine engine(config_);
    auto result = engine.process("");

    ASSERT_FALSE(result.has_value());
    EXPECT_EQ(result.error(), mylib::Error::InvalidInput);
}

// Parameterized test
class ProcessTest : public ::testing::TestWithParam<std::pair<std::string, std::string>> {};

TEST_P(ProcessTest, TransformsCorrectly) {
    auto [input, expected] = GetParam();
    mylib::Engine engine({});

    auto result = engine.process(input);
    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(*result, expected);
}

INSTANTIATE_TEST_SUITE_P(
    InputCases,
    ProcessTest,
    ::testing::Values(
        std::make_pair("hello", "HELLO"),
        std::make_pair("world", "WORLD"),
        std::make_pair("test", "TEST")
    )
);
```

## Build System (CMake)

```cmake
cmake_minimum_required(VERSION 3.20)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Compiler warnings
if(MSVC)
    add_compile_options(/W4 /WX)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Library
add_library(mylib
    src/core/engine.cpp
    src/utils/helpers.cpp
)

target_include_directories(mylib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
    PRIVATE
        src
)

# Dependencies (using Conan)
find_package(fmt REQUIRED)
target_link_libraries(mylib PUBLIC fmt::fmt)

# Tests
option(BUILD_TESTS "Build tests" ON)
if(BUILD_TESTS)
    enable_testing()
    find_package(GTest REQUIRED)

    add_executable(mylib_tests
        tests/unit/test_engine.cpp
    )
    target_link_libraries(mylib_tests PRIVATE mylib GTest::gtest_main)

    include(GoogleTest)
    gtest_discover_tests(mylib_tests)
endif()

# Install
install(TARGETS mylib
    EXPORT mylibTargets
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY include/ DESTINATION include)
```

## Development Workflow

```bash
# Build
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build .

# Run tests
ctest --output-on-failure

# Install dependencies (Conan)
conan install .. --build=missing

# Static analysis
clang-tidy src/*.cpp -- -std=c++20 -Iinclude

# Format code
clang-format -i src/*.cpp include/**/*.hpp

# Memory check
valgrind --leak-check=full ./mylib_tests

# Coverage
cmake .. -DCMAKE_BUILD_TYPE=Coverage
make coverage
```
```

---

## Best Practices

1. **Modern C++ Features**
   - Use smart pointers (unique_ptr, shared_ptr)
   - Apply RAII for resource management
   - Leverage move semantics
   - Use auto and structured bindings
   - Prefer algorithms over raw loops

2. **Rule of Five/Zero**
   - Implement all or none: destructor, copy constructor, copy assignment, move constructor, move assignment
   - Or use = default/= delete appropriately

3. **Const Correctness**
   - Mark methods const when they don't modify state
   - Use const& for read-only parameters
   - Use constexpr for compile-time constants

4. **Template Best Practices**
   - Use concepts (C++20) for constraints
   - Avoid template bloat
   - Prefer type deduction
   - Document template requirements

5. **Error Handling**
   - Use exceptions for exceptional cases
   - Use std::expected/std::optional for expected failures
   - Don't throw from destructors
   - Use noexcept where appropriate

---

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/technical_docs/generated_docs
mkdir -p ${OUTPUT_DIR}/technical_docs/templates
mkdir -p ${OUTPUT_DIR}/technical_docs/assets
mkdir -p ${OUTPUT_DIR}/technical_docs/exports
```

**Save files as follows**:


- Templates → `documentation/technical_docs/templates/`

- Assets → `documentation/technical_docs/assets/`

- Exports → `documentation/technical_docs/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

~~~

## Output Format Specifications

The technical documentation should:
- Provide architecture overview focused on modern C++ features
- Document RAII and smart pointer usage
- Show proper move semantics implementation
- Document template and concept usage
- Address exception safety and error handling
- Include comprehensive testing approach
- Target C++ developers with modern standards knowledge
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
