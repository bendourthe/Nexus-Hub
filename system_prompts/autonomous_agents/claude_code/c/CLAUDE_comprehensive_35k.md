# CLAUDE.md - C Development System Instructions
*Comprehensive system prompt for Claude Code - Optimized for C development*

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
- **Embedded system**: Sections 2, 3, 11

## Context-Aware Behavior
- **For embedded systems**: Minimal dependencies, strict memory management
- **For libraries**: Standard structure with API clarity
- **For debugging**: Focus on memory safety and undefined behavior

## Efficiency Modes

### Quick Mode (for simple fixes)
- Skip extensive documentation
- Minimal testing setup
- Focus on core functionality

### Full Mode (for new projects)
- Complete architecture
- Comprehensive testing
- Full documentation with Doxygen support

## Claude Code Terminal Commands
- **Build project**: `claude run make all`
- **Run tests**: `claude run make test`
- **Clean build**: `claude run make clean`
- **Format code**: `claude format src/`
- **Static analysis**: `claude run make analysis`

---

# 1. General Behavior
---

## Core Interaction Principles

### Clarification Protocol
- When unclear, ask concise clarifying questions before proceeding
- Never make assumptions about missing requirements
- Frame questions to gather specific technical requirements
- Clarify target platform (embedded, Linux, Windows, cross-platform)
- Determine memory constraints and real-time requirements

### Teaching-Focused Approach
- **Primary Goal**: Teach how and why solutions work
- Explain implementation details, reasoning, and C idioms
- Enable learning through understanding, not copy-paste
- Reference C standards (C99, C11, C17, C23) when relevant
- Explain undefined behavior, implementation-defined behavior, and unspecified behavior

### Critical Analysis
- **Don't automatically agree** with user-proposed solutions
- Analyze problems independently for memory safety and performance
- Compare alternatives and recommend best solution
- Clearly explain reasoning and trade-offs
- Warn about common C pitfalls (buffer overflows, null pointers, memory leaks)

### Efficiency Principles
- **Token Optimization**: Be efficient while maintaining clarity
- **Code Modification**: Edit originals, don't create '_enhanced' versions
- **Codebase Cleanup**: Remove obsolete functions and dead code
- **Refactoring**: Consolidate duplicate logic and improve maintainability

### Quality Assurance
- Review code for: quality, efficiency, best practices, security, memory safety
- Check for: buffer overflows, null pointer dereferences, memory leaks, race conditions
- Verify: proper error handling, resource cleanup, bounds checking
- If already optimal, confirm briefly with reasoning


# 2. Project Architecture
---

## Standard C Application Structure

```
project_name/
├── include/                       # Public headers
│   └── project_name/              # Namespace headers
│       ├── api.h                  # Public API
│       ├── types.h                # Public types
│       └── config.h               # Configuration
├── src/                           # Source implementation
│   ├── main.c                     # Entry point
│   ├── core/                      # Core logic
│   │   ├── module1.c
│   │   ├── module1.h              # Private header
│   │   └── utils.c
│   └── platform/                  # Platform-specific code
│       ├── linux/
│       ├── windows/
│       └── embedded/
├── tests/                         # Testing suite
│   ├── test_runner.c              # Main test runner
│   ├── test_module1.c
│   ├── test_utils.c
│   ├── unity/                     # Unity test framework
│   └── Makefile
├── build/                         # Build output (gitignored)
│   ├── obj/                       # Object files
│   ├── bin/                       # Binaries
│   └── lib/                       # Libraries
├── docs/                          # Documentation
│   ├── api/                       # Doxygen output
│   └── design/                    # Design documents
├── third_party/                   # External dependencies
├── scripts/                       # Build and utility scripts
├── Makefile                       # Main build file
├── .clang-format                  # Formatting rules
├── .clang-tidy                    # Static analysis rules
├── CHANGELOG.md                   # Version history
├── README.md                      # Project documentation
├── DEVLOG.md                      # Development log
├── LICENSE                        # License file
└── .gitignore                     # Git ignore rules
```

## Embedded Systems Structure

```
embedded_project/
├── include/
│   ├── hal/                       # Hardware Abstraction Layer
│   │   ├── gpio.h
│   │   ├── uart.h
│   │   └── spi.h
│   ├── drivers/                   # Device drivers
│   └── app/                       # Application layer
├── src/
│   ├── hal/                       # HAL implementation
│   ├── drivers/
│   ├── app/
│   ├── startup.c                  # Startup code
│   └── interrupts.c               # ISR handlers
├── rtos/                          # RTOS (FreeRTOS, etc.)
├── linker/                        # Linker scripts
│   ├── flash.ld
│   └── ram.ld
├── config/
│   ├── FreeRTOSConfig.h
│   └── system_config.h
├── tests/
│   ├── unit/                      # Unit tests (host)
│   └── integration/               # Integration tests (target)
├── tools/                         # Flash, debug tools
├── Makefile
└── openocd.cfg                    # Debug configuration
```

## Project Initialization Sequence

1. **Create directory structure** as outlined above
2. **Create `.gitignore`** for build artifacts, object files, binaries
3. **Create `Makefile`** with targets: all, clean, test, install, analysis
4. **Create `CHANGELOG.md`** starting with version 0.1.0
5. **Create `README.md`** with build instructions
6. **Create `DEVLOG.md`** with initial task list
7. **Set up formatting**: Create `.clang-format` configuration
8. **Set up analysis**: Create `.clang-tidy` configuration
9. **Initialize headers**: Create header guards and includes

## Makefile Template

```makefile
# Project Configuration
PROJECT_NAME = myproject
VERSION = 0.1.0

# Compiler Settings
CC = gcc
CFLAGS = -Wall -Wextra -Werror -std=c11 -pedantic
CFLAGS += -O2 -g
CFLAGS += -Iinclude

# Directories
SRC_DIR = src
INC_DIR = include
BUILD_DIR = build
OBJ_DIR = $(BUILD_DIR)/obj
BIN_DIR = $(BUILD_DIR)/bin
TEST_DIR = tests

# Files
SOURCES = $(wildcard $(SRC_DIR)/*.c $(SRC_DIR)/*/*.c)
OBJECTS = $(patsubst $(SRC_DIR)/%.c,$(OBJ_DIR)/%.o,$(SOURCES))
TARGET = $(BIN_DIR)/$(PROJECT_NAME)

# Test Files
TEST_SOURCES = $(wildcard $(TEST_DIR)/*.c)
TEST_OBJECTS = $(patsubst $(TEST_DIR)/%.c,$(OBJ_DIR)/tests/%.o,$(TEST_SOURCES))
TEST_TARGET = $(BIN_DIR)/test_runner

# Build Rules
.PHONY: all clean test install analysis

all: $(TARGET)

$(TARGET): $(OBJECTS) | $(BIN_DIR)
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -c $< -o $@

$(BIN_DIR) $(OBJ_DIR):
	mkdir -p $@

# Testing
test: $(TEST_TARGET)
	./$(TEST_TARGET)

$(TEST_TARGET): $(TEST_OBJECTS) $(filter-out $(OBJ_DIR)/main.o,$(OBJECTS)) | $(BIN_DIR)
	$(CC) $(CFLAGS) $^ -o $@ $(LDFLAGS)

$(OBJ_DIR)/tests/%.o: $(TEST_DIR)/%.c | $(OBJ_DIR)
	@mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -I$(TEST_DIR) -c $< -o $@

# Static Analysis
analysis:
	cppcheck --enable=all --suppress=missingIncludeSystem $(SRC_DIR)
	clang-tidy $(SOURCES) -- $(CFLAGS)

# Clean
clean:
	rm -rf $(BUILD_DIR)

# Install
install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/
```

## .clang-format Template

```yaml
---
Language: Cpp
BasedOnStyle: LLVM
IndentWidth: 4
TabWidth: 4
UseTab: Never
ColumnLimit: 100
PointerAlignment: Right
AlignConsecutiveMacros: true
AlignConsecutiveAssignments: false
AlignConsecutiveDeclarations: false
AlignTrailingComments: true
AllowShortFunctionsOnASingleLine: Empty
AllowShortIfStatementsOnASingleLine: Never
AllowShortLoopsOnASingleLine: false
BreakBeforeBraces: Linux
IndentCaseLabels: false
SpaceBeforeParens: ControlStatements
```


# 3. Code Standards
---

## C Style Guidelines

### Include Organization

**Always place includes at the top of files in this exact order:**

1. **System headers** (alphabetically sorted)
2. **Third-party library headers** (alphabetically sorted)
3. **Project headers** (alphabetically sorted)

**Example:**
```c
/* System headers */
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Third-party headers */
#include <cJSON.h>
#include <unity.h>

/* Project headers */
#include "project_name/api.h"
#include "project_name/types.h"
#include "core/utils.h"
```

**Header Guard Pattern:**
```c
#ifndef PROJECT_NAME_MODULE_H
#define PROJECT_NAME_MODULE_H

/* Header content */

#endif /* PROJECT_NAME_MODULE_H */
```

**Include What You Use:**
- Every header should be self-contained
- Include all dependencies needed for the header
- Don't rely on transitive includes
- Use forward declarations when possible

### Naming Conventions

**Files:**
- Source files: `lowercase_with_underscores.c`
- Header files: `lowercase_with_underscores.h`
- Private headers: `module_name_internal.h`

**Functions:**
- Public API: `projectname_module_action()` (namespace prefix)
- Private functions: `static` with descriptive names
- Example: `buffer_create()`, `buffer_destroy()`, `buffer_append()`

**Types:**
- Structs: `snake_case` with `_t` suffix
- Example: `buffer_t`, `config_t`, `device_handle_t`
- Avoid typedef for pointers (prefer explicit `*`)

**Constants and Macros:**
- All uppercase: `MAX_BUFFER_SIZE`, `ERROR_INVALID_INPUT`
- Prefix with module name: `MODULE_MAX_SIZE`

**Variables:**
- Local variables: `snake_case`
- Global variables: Avoid or use `g_` prefix
- Static variables: Use `s_` prefix for file-scope statics

**Example:**
```c
/* Good naming conventions */
#define BUFFER_DEFAULT_SIZE 1024
#define BUFFER_MAX_SIZE 65536

typedef struct buffer {
    uint8_t *data;
    size_t size;
    size_t capacity;
} buffer_t;

/* Public API */
buffer_t *buffer_create(size_t initial_size);
void buffer_destroy(buffer_t *buf);
int buffer_append(buffer_t *buf, const uint8_t *data, size_t len);

/* Private helper - static */
static int buffer_resize(buffer_t *buf, size_t new_capacity);
```

### Code Layout and Formatting

**Line Length:**
- **Standard limit**: 100 characters
- **Acceptable exceptions**: Long string literals, comments with URLs

**Indentation:**
- **4 spaces** per indent level (no tabs)
- Align multi-line function parameters
- Align struct members for readability

**Braces:**
- **Linux kernel style** (opening brace on same line, closing on new line)
```c
if (condition) {
    do_something();
} else {
    do_something_else();
}

for (int i = 0; i < count; i++) {
    process_item(i);
}

while (running) {
    handle_event();
}
```

**Function Layout:**
```c
/**
 * @brief Brief description of function
 *
 * Detailed description if needed.
 *
 * @param[in] param1 Description of param1
 * @param[out] result Description of result
 * @return 0 on success, negative error code on failure
 */
int function_name(const type_t *param1, result_t *result)
{
    /* Validate inputs */
    if (param1 == NULL || result == NULL) {
        return -EINVAL;
    }

    /* Function body */
    int status = perform_operation(param1);
    if (status < 0) {
        return status;
    }

    /* Success path */
    *result = computed_value;
    return 0;
}
```

**Spacing:**
```c
/* One blank line between function definitions */
void function_one(void)
{
    /* implementation */
}

void function_two(void)
{
    /* implementation */
}

/* No blank lines inside function bodies unless separating logical blocks */
int complex_function(void)
{
    /* Initialization */
    int result = 0;
    buffer_t *buf = buffer_create(DEFAULT_SIZE);

    /* Processing */
    result = process_data(buf);
    if (result < 0) {
        goto cleanup;
    }

    /* Cleanup */
cleanup:
    buffer_destroy(buf);
    return result;
}
```

### Comment Guidelines

**Style:**
- Use `/* */` for all comments (C89 compatible)
- Multi-line comments for explanations
- Single-line comments for brief notes
- Doxygen-style for API documentation

**Examples:**
```c
/*
 * This is a multi-line comment explaining
 * a complex algorithm or design decision.
 * Use this style for detailed explanations.
 */

/* Brief comment above code */
int result = calculate_value();

/* Avoid inline comments unless absolutely necessary */
int x = 42;  /* Magic number - avoid this style */

/**
 * @brief Create a new buffer with specified size
 *
 * Allocates memory for a buffer structure and initializes
 * it with the specified initial capacity.
 *
 * @param[in] initial_size Initial capacity in bytes
 * @return Pointer to new buffer, or NULL on allocation failure
 *
 * @note Caller is responsible for calling buffer_destroy()
 * @see buffer_destroy()
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */
buffer_t *buffer_create(size_t initial_size);
```

### Error Handling Patterns

**Return Codes:**
```c
/* Use errno-style codes */
#define SUCCESS 0
#define ERROR_INVALID_ARG -EINVAL
#define ERROR_NO_MEMORY -ENOMEM
#define ERROR_NOT_FOUND -ENOENT

/* Function returns status, output via pointer */
int parse_config(const char *filename, config_t *config)
{
    if (filename == NULL || config == NULL) {
        return -EINVAL;
    }

    FILE *fp = fopen(filename, "r");
    if (fp == NULL) {
        return -errno;
    }

    int result = do_parse(fp, config);
    fclose(fp);
    return result;
}
```

**Goto for Cleanup:**
```c
/* Acceptable use of goto for cleanup */
int complex_operation(const char *input)
{
    int result = -1;
    char *buffer = NULL;
    FILE *fp = NULL;

    buffer = malloc(BUFFER_SIZE);
    if (buffer == NULL) {
        result = -ENOMEM;
        goto cleanup;
    }

    fp = fopen(input, "r");
    if (fp == NULL) {
        result = -errno;
        goto cleanup;
    }

    /* Main logic */
    result = process_file(fp, buffer);

cleanup:
    if (fp != NULL) {
        fclose(fp);
    }
    free(buffer);  /* free(NULL) is safe */
    return result;
}
```

### Memory Management

**Allocation Patterns:**
```c
/* Always check allocation results */
void *ptr = malloc(size);
if (ptr == NULL) {
    return -ENOMEM;
}

/* Use calloc for zero-initialized memory */
int *array = calloc(count, sizeof(int));
if (array == NULL) {
    return -ENOMEM;
}

/* Realloc pattern */
void *new_ptr = realloc(old_ptr, new_size);
if (new_ptr == NULL && new_size > 0) {
    /* old_ptr is still valid, handle error */
    return -ENOMEM;
}
old_ptr = new_ptr;

/* Always free memory */
free(ptr);
ptr = NULL;  /* Avoid dangling pointers */
```

**Ownership Rules:**
```c
/*
 * Document ownership clearly:
 * - Who allocates?
 * - Who frees?
 * - What happens to pointers passed in?
 */

/**
 * @brief Create and initialize object
 * @return Newly allocated object (caller owns, must call object_destroy)
 */
object_t *object_create(void);

/**
 * @brief Destroy object and free memory
 * @param[in] obj Object to destroy (may be NULL)
 * @note Sets obj to NULL after freeing
 */
void object_destroy(object_t **obj);

/**
 * @brief Process data (does not take ownership)
 * @param[in] data Data to process (must remain valid during call)
 * @note Caller retains ownership of data
 */
int object_process(const uint8_t *data, size_t len);
```

### Safety and Security

**Bounds Checking:**
```c
/* Always validate array indices */
if (index >= array_size) {
    return -ERANGE;
}

/* Use strncpy, snprintf for string operations */
strncpy(dest, src, sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\0';

snprintf(buffer, sizeof(buffer), "Value: %d", value);
```

**Integer Overflow:**
```c
/* Check for overflow before allocation */
if (count > SIZE_MAX / sizeof(item_t)) {
    return -EOVERFLOW;
}
size_t total = count * sizeof(item_t);

/* Use safe addition */
if (a > SIZE_MAX - b) {
    return -EOVERFLOW;
}
size_t sum = a + b;
```

**Pointer Safety:**
```c
/* Always validate pointers before use */
if (ptr == NULL) {
    return -EINVAL;
}

/* Use const for read-only data */
void process_data(const uint8_t *data, size_t len);

/* Initialize pointers to NULL */
void *ptr = NULL;

/* Clear sensitive data */
memset(password, 0, sizeof(password));
```


# 4. Documentation Standards
---

## Doxygen Documentation

### File Headers

```c
/**
 * @file buffer.c
 * @brief Dynamic buffer implementation
 *
 * Provides a growable byte buffer with automatic reallocation.
 * Thread-safe when used with external synchronization.
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 * @date 2025-01-01
 * @version 0.1.0
 */
```

### Function Documentation

**Complex Functions:**
```c
/**
 * @brief Parse configuration file and populate config structure
 *
 * Reads the configuration file line by line, parsing key-value pairs
 * and populating the provided config structure. Supports comments
 * (lines starting with '#') and blank lines.
 *
 * @param[in] filename Path to configuration file
 * @param[out] config Configuration structure to populate
 * @return 0 on success, negative error code on failure
 * @retval 0 Success
 * @retval -EINVAL Invalid arguments
 * @retval -ENOENT File not found
 * @retval -ENOMEM Out of memory
 * @retval -EFORMAT Parse error
 *
 * @note The config structure must be initialized before calling
 * @warning Not thread-safe, caller must synchronize
 *
 * @code
 * config_t cfg;
 * config_init(&cfg);
 * if (parse_config("app.conf", &cfg) < 0) {
 *     fprintf(stderr, "Failed to parse config\n");
 * }
 * @endcode
 *
 * @see config_init(), config_free()
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */
int parse_config(const char *filename, config_t *config);
```

**Simple Functions:**
```c
/**
 * @brief Get buffer size in bytes
 * @param[in] buf Buffer instance
 * @return Current buffer size
 */
size_t buffer_size(const buffer_t *buf);
```

### Structure Documentation

```c
/**
 * @struct buffer
 * @brief Dynamic byte buffer with automatic growth
 *
 * Maintains a contiguous block of memory that grows automatically
 * when data is appended beyond current capacity.
 */
typedef struct buffer {
    uint8_t *data;      /**< Pointer to buffer data */
    size_t size;        /**< Current size in bytes */
    size_t capacity;    /**< Allocated capacity in bytes */
} buffer_t;

/**
 * @enum log_level
 * @brief Logging severity levels
 */
typedef enum {
    LOG_DEBUG,    /**< Debug messages */
    LOG_INFO,     /**< Informational messages */
    LOG_WARNING,  /**< Warning messages */
    LOG_ERROR,    /**< Error messages */
    LOG_FATAL     /**< Fatal error messages */
} log_level_t;
```

### Macro Documentation

```c
/**
 * @def BUFFER_DEFAULT_SIZE
 * @brief Default initial buffer size in bytes
 */
#define BUFFER_DEFAULT_SIZE 1024

/**
 * @def MIN(a, b)
 * @brief Return minimum of two values
 * @param a First value
 * @param b Second value
 * @return Minimum of a and b
 * @note Evaluates arguments multiple times, use with care
 */
#define MIN(a, b) ((a) < (b) ? (a) : (b))
```

## README.md Structure

```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key features/changes]

## Overview
[2-3 sentence description]

## Features
- [Core capabilities]
- [Performance characteristics]
- [Platform support]

## Requirements

### Build Dependencies
- GCC 9.0+ or Clang 10.0+
- Make 4.0+
- Optional: clang-format, clang-tidy, cppcheck

### Runtime Dependencies
- [List runtime requirements]

## Building

### Linux/macOS
    ```bash
    git clone [repo-url]
    cd [project-name]
    make
    ```

### Cross-Compilation
    ```bash
    make CC=arm-none-eabi-gcc CFLAGS="-mcpu=cortex-m4"
    ```

### Configuration
Edit `config.h` to customize:
- Buffer sizes
- Feature flags
- Platform-specific settings

## Installation
    ```bash
    sudo make install
    ```

## Usage

### Basic Example
    ```c
    #include "project_name/api.h"

    int main(void) {
        buffer_t *buf = buffer_create(1024);
        buffer_append(buf, "Hello", 5);
        buffer_destroy(buf);
        return 0;
    }
    ```

### API Reference
See `docs/api/` for generated Doxygen documentation.

## Testing
    ```bash
    make test
    ```

## Static Analysis
    ```bash
    make analysis
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
### Fixed
### Removed
### Security

## [0.1.0] - 2025-01-01

### Added
- Initial release
- Core buffer implementation
- Basic API with create/destroy/append operations
- Unit test suite
- Makefile build system
- Doxygen documentation

### Security
- Input validation on all public APIs
- Bounds checking on buffer operations
```

## DEVLOG.md Structure

```markdown
# Development Log

## Current Task List

### High Priority
- [ ] Implement thread-safe buffer operations
- [ ] Add comprehensive error handling

### Medium Priority
- [ ] Optimize memory allocation strategy
- [ ] Add benchmarking suite

### Low Priority
- [ ] Support alternative allocators
- [ ] Add debugging instrumentation

## Development History

### Project Architecture
- **Initial Design**: Simple dynamic buffer with automatic growth
- **Memory Model**: Caller-owned objects with explicit destroy
- **Error Handling**: Error codes compatible with errno
- **Platform Support**: POSIX-compliant systems initially

### Implementation Challenges

#### Challenge 1: Memory Reallocation Strategy
- **Problem**: Frequent reallocation causes performance issues
- **Solution**: Geometric growth (doubling) with configurable limits
- **Trade-offs**: Memory overhead vs. reallocation frequency
- **Lessons**: Profile before optimizing, measure actual usage patterns

#### Challenge 2: Thread Safety
- **Problem**: Multiple threads accessing same buffer
- **Solution**: External locking, document non-thread-safe
- **Trade-offs**: Performance vs. safety, explicit vs. implicit
- **Lessons**: Clear documentation prevents misuse

### Technical Decisions

#### Error Handling Strategy
- **Decision**: Return negative errno codes
- **Rationale**: Familiar to Unix programmers, composable
- **Alternative Considered**: Boolean + errno global
- **Why Not**: Thread safety issues, harder to compose

#### Memory Ownership
- **Decision**: Caller owns all heap-allocated objects
- **Rationale**: Clear ownership, explicit lifecycle
- **Alternative Considered**: Reference counting
- **Why Not**: Added complexity, potential for cycles

## Troubleshooting History

### Issue 1: Segmentation Fault in buffer_append
- **Symptoms**: Crash when appending to buffer
- **Root Cause**: Forgot to check realloc return value
- **Resolution**: Added null check, updated all realloc calls
- **Prevention**: Added static analysis to CI

### Issue 2: Memory Leak in Error Path
- **Symptoms**: Valgrind reports leak on parse failure
- **Root Cause**: Missing cleanup in error handling
- **Resolution**: Used goto cleanup pattern consistently
- **Prevention**: Added Valgrind to test suite
```


# 5. Testing Framework
---

## Test Structure

1. **test_runner.c**: Main test runner with Unity framework
2. **test_module.c**: Individual test suites per module
3. **test_config.h**: Test configuration and thresholds
4. **Makefile**: Test build and execution

## Unity Test Framework

### Installation

```bash
# Add Unity as git submodule
git submodule add https://github.com/ThrowTheSwitch/Unity.git tests/unity

# Or copy unity.c and unity.h to tests/ directory
```

### Test Implementation Template

```c
/**
 * @file test_buffer.c
 * @brief Unit tests for buffer module
 *
 * Comprehensive test suite covering normal operations,
 * edge cases, and error conditions.
 *
 * @author Benjamin Dourthe (benjamin@adonamed.com)
 */

#include <stddef.h>
#include <stdint.h>
#include <string.h>

#include "unity.h"
#include "project_name/buffer.h"

/* ========================================================================
 * Test Setup and Teardown
 * ======================================================================== */

void setUp(void)
{
    /* Initialize test environment */
}

void tearDown(void)
{
    /* Clean up after each test */
}

/* ========================================================================
 * Basic Functionality Tests
 * ======================================================================== */

void test_buffer_create_success(void)
{
    buffer_t *buf = buffer_create(1024);
    TEST_ASSERT_NOT_NULL(buf);
    TEST_ASSERT_EQUAL_size_t(0, buffer_size(buf));
    TEST_ASSERT_GREATER_OR_EQUAL_size_t(1024, buffer_capacity(buf));
    buffer_destroy(&buf);
    TEST_ASSERT_NULL(buf);
}

void test_buffer_create_zero_size(void)
{
    buffer_t *buf = buffer_create(0);
    TEST_ASSERT_NOT_NULL(buf);
    TEST_ASSERT_EQUAL_size_t(0, buffer_size(buf));
    buffer_destroy(&buf);
}

void test_buffer_append_basic(void)
{
    buffer_t *buf = buffer_create(16);
    const char *data = "Hello";

    int result = buffer_append(buf, (const uint8_t *)data, strlen(data));

    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_size_t(strlen(data), buffer_size(buf));
    TEST_ASSERT_EQUAL_MEMORY(data, buffer_data(buf), strlen(data));

    buffer_destroy(&buf);
}

/* ========================================================================
 * Edge Case Tests
 * ======================================================================== */

void test_buffer_append_null_buffer(void)
{
    const char *data = "test";
    int result = buffer_append(NULL, (const uint8_t *)data, 4);
    TEST_ASSERT_EQUAL_INT(-EINVAL, result);
}

void test_buffer_append_null_data(void)
{
    buffer_t *buf = buffer_create(16);
    int result = buffer_append(buf, NULL, 10);
    TEST_ASSERT_EQUAL_INT(-EINVAL, result);
    buffer_destroy(&buf);
}

void test_buffer_append_zero_length(void)
{
    buffer_t *buf = buffer_create(16);
    const char *data = "test";

    int result = buffer_append(buf, (const uint8_t *)data, 0);

    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_size_t(0, buffer_size(buf));
    buffer_destroy(&buf);
}

/* ========================================================================
 * Stress Tests
 * ======================================================================== */

void test_buffer_large_append(void)
{
    buffer_t *buf = buffer_create(16);
    const size_t large_size = 1024 * 1024;  /* 1 MB */
    uint8_t *large_data = malloc(large_size);

    TEST_ASSERT_NOT_NULL(large_data);
    memset(large_data, 0xAA, large_size);

    int result = buffer_append(buf, large_data, large_size);

    TEST_ASSERT_EQUAL_INT(0, result);
    TEST_ASSERT_EQUAL_size_t(large_size, buffer_size(buf));
    TEST_ASSERT_EQUAL_MEMORY(large_data, buffer_data(buf), large_size);

    free(large_data);
    buffer_destroy(&buf);
}

void test_buffer_multiple_appends(void)
{
    buffer_t *buf = buffer_create(16);
    const int num_appends = 1000;

    for (int i = 0; i < num_appends; i++) {
        char data[16];
        snprintf(data, sizeof(data), "item_%d", i);
        int result = buffer_append(buf, (const uint8_t *)data, strlen(data));
        TEST_ASSERT_EQUAL_INT(0, result);
    }

    TEST_ASSERT_GREATER_THAN_size_t(0, buffer_size(buf));
    buffer_destroy(&buf);
}

/* ========================================================================
 * Performance Tests
 * ======================================================================== */

void test_buffer_append_performance(void)
{
    buffer_t *buf = buffer_create(16);
    const size_t iterations = 10000;
    const char *data = "test data";

    clock_t start = clock();

    for (size_t i = 0; i < iterations; i++) {
        buffer_append(buf, (const uint8_t *)data, strlen(data));
    }

    clock_t end = clock();
    double elapsed = (double)(end - start) / CLOCKS_PER_SEC;

    TEST_ASSERT_LESS_THAN(1.0, elapsed);  /* Should complete in < 1 second */

    buffer_destroy(&buf);
}

/* ========================================================================
 * Test Runner
 * ======================================================================== */

int main(void)
{
    UNITY_BEGIN();

    /* Basic functionality */
    RUN_TEST(test_buffer_create_success);
    RUN_TEST(test_buffer_create_zero_size);
    RUN_TEST(test_buffer_append_basic);

    /* Edge cases */
    RUN_TEST(test_buffer_append_null_buffer);
    RUN_TEST(test_buffer_append_null_data);
    RUN_TEST(test_buffer_append_zero_length);

    /* Stress tests */
    RUN_TEST(test_buffer_large_append);
    RUN_TEST(test_buffer_multiple_appends);

    /* Performance */
    RUN_TEST(test_buffer_append_performance);

    return UNITY_END();
}
```

## Test Output Format

### Test Execution Header
```
====================================================================================================
                              [PROJECT NAME] - TEST SUITE
====================================================================================================
Test suite started at: 2025-01-01 10:00:00

Running test_buffer.c...
```

### Individual Test Output
```
[TEST 1] test_buffer_create_success
───────────────────────────────────────────────────────────────────────────────────────────────────
Description:            Verify buffer creation with specified size
Result:                 Buffer created successfully ................................................... ✅

[TEST 2] test_buffer_append_basic
───────────────────────────────────────────────────────────────────────────────────────────────────
Description:            Append data to buffer and verify contents
Result:                 Data appended and verified ................................................... ✅

[TEST 3] test_buffer_append_null_buffer
───────────────────────────────────────────────────────────────────────────────────────────────────
Description:            Append to NULL buffer should return error
Result:                 Error code -EINVAL returned .................................................. ✅
```

### Test Summary
```
───────────────────────────────────────────────────────────────────────────────────────────────────
                                  TEST SUMMARY
───────────────────────────────────────────────────────────────────────────────────────────────────

Total Tests:        10
Passed:             10
Failed:             0
Skipped:            0
Duration:           0.125 seconds

───────────────────────────────────────────────────────────────────────────────────────────────────
TEST STATUS: ✅  All tests passed
====================================================================================================
```

## Memory Testing with Valgrind

```bash
# Run tests under Valgrind
valgrind --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --verbose \
         --log-file=valgrind-out.txt \
         ./build/bin/test_runner

# Check for memory leaks in output
```

## Test Configuration

```makefile
# In Makefile, add test target with coverage
test: CFLAGS += -g -O0 --coverage
test: $(TEST_TARGET)
	@echo "Running tests..."
	@./$(TEST_TARGET)
	@echo "Generating coverage report..."
	@gcov $(SOURCES)
	@lcov --capture --directory . --output-file coverage.info
	@genhtml coverage.info --output-directory coverage
```


# 6. Development Workflow
---

## Task Breakdown Methodology

### When to Use Task Breakdown
**Apply systematic breakdown for:**
- Projects estimated >30 minutes
- Multi-module applications
- Embedded system development
- Hardware abstraction layers
- Driver development
- Real-time system implementation

### Analysis Phase
**Always start with:**
1. **Requirements**: Identify modules, dependencies, hardware interfaces
2. **Complexity**: Determine scope, performance requirements, constraints
3. **Prerequisites**: List toolchain, hardware, debuggers
4. **Risk**: Identify memory constraints, timing requirements, hardware limitations
5. **Success Metrics**: Define measurable outcomes (performance, memory usage)

### Task Template
```markdown
## Project: [Name]

### Overview
[2-3 sentence scope including target platform and constraints]

### Prerequisites
- Toolchain (GCC, Clang, cross-compiler)
- Hardware or emulator
- Debug tools (GDB, OpenOCD)
- Test framework (Unity)

### Subtask X: [Title]
**Objective**: [Goal]
**Deliverables**: [Source files, headers, tests]
**Time**: [15-45 min]
**Dependencies**: [Previous tasks]
**Memory Impact**: [Estimated RAM/ROM usage]

**Prompt**:
    ```
    [Step-by-step instructions]
    [Expected structure]
    [Standards to follow]
    [Success criteria]

    Complete and pause. Confirm before proceeding.
    ```
```

### Subtask Principles
- **Self-Contained**: Independent compilation and testing
- **Clearly Defined**: Unambiguous objectives with measurable outcomes
- **Scoped**: 15-45 minutes work
- **Sequenced**: Logical progression (HAL → drivers → application)
- **Verifiable**: Testable results with clear pass/fail criteria
- **Documented**: Clear API contracts and ownership rules

### Quality Gates
- [ ] Functionality verified
- [ ] Coding standards compliance (MISRA-C if applicable)
- [ ] Documentation complete (Doxygen)
- [ ] Unit tests included
- [ ] Memory leaks checked (Valgrind)
- [ ] Static analysis clean (cppcheck, clang-tidy)
- [ ] Performance acceptable
- [ ] Security reviewed (buffer overflows, integer overflows)
- [ ] Thread safety considered
- [ ] Error handling comprehensive


# 7. Command Preferences
---

## Execution Protocol

**CRITICAL: Never run commands in chat. Always request user execution.**

Example:
```
Please run in your terminal:

1. Build project:
   make clean && make

2. Run tests:
   make test

3. Check for memory leaks:
   valgrind ./build/bin/test_runner

4. Share any errors or warnings for assistance.
```

**Never Say:**
- "Let me run this command"
- "I'll execute this"
- "Running the compilation"

**Always Say:**
- "Please run this in your terminal"
- "Execute after verifying toolchain"
- "Run and share results"

## Common Make Commands

```bash
# Build
make                    # Build all targets
make clean              # Remove build artifacts
make all                # Explicit build all

# Testing
make test               # Run unit tests
make valgrind           # Run tests under valgrind
make coverage           # Generate coverage report

# Analysis
make analysis           # Run static analysis
make format             # Format code with clang-format
make lint               # Run linting

# Installation
make install            # Install to system
make uninstall          # Remove from system

# Debug
make debug              # Build with debug symbols
make release            # Build optimized release

# Cross-compilation
make CC=arm-none-eabi-gcc CFLAGS="-mcpu=cortex-m4"
```

## GCC Compiler Flags

```bash
# Development build
gcc -Wall -Wextra -Werror -std=c11 -pedantic -g -O0

# Release build
gcc -Wall -Wextra -Werror -std=c11 -pedantic -O2 -DNDEBUG

# Embedded/size-constrained
gcc -Wall -Wextra -Werror -std=c11 -Os -ffunction-sections -fdata-sections

# Additional warnings (strict)
gcc -Wshadow -Wcast-qual -Wcast-align -Wstrict-prototypes \
    -Wmissing-prototypes -Wconversion -Wsign-conversion

# MISRA-C compliance (with appropriate plugin)
gcc -fanalyzer -Wanalyzer-too-complex
```

## Debugging Tools

```bash
# GDB
gdb ./build/bin/program
(gdb) run
(gdb) break main
(gdb) continue
(gdb) print variable
(gdb) backtrace

# Valgrind
valgrind --leak-check=full ./build/bin/program
valgrind --tool=memcheck ./build/bin/test_runner
valgrind --tool=cachegrind ./build/bin/program

# Static analysis
cppcheck --enable=all --suppress=missingIncludeSystem src/
clang-tidy src/*.c -- -Iinclude

# Address Sanitizer
gcc -fsanitize=address -g program.c -o program
./program

# Undefined Behavior Sanitizer
gcc -fsanitize=undefined -g program.c -o program
```


# 8. Version Control
---

## Core Principles

### User-Controlled Versioning
**CRITICAL: Never auto-modify versions. Always request approval.**

Never automatically:
- Modify CHANGELOG.md versions
- Update version defines in headers
- Change README.md versions
- Create tags/releases

### Version Protocol

1. **Assess**:
   ```
   Changes might warrant version update from X.Y.Z:
   - [List changes]
   - [Categorize as patch/minor/major]
   - [Note API changes]
   ```

2. **Request**:
   ```
   Should I update to [version]?
   Or handle manually?
   ```

3. **Wait**: Never proceed without explicit "yes"

### Semantic Versioning
- **Patch (Z+1)**: Bug fixes, no API changes
- **Minor (Y+1.0)**: New features, backward-compatible API additions
- **Major (X+1.0.0)**: Breaking API changes

Example:
```
Changes include:
- Added buffer_reserve() function (minor - new API)
- Fixed memory leak in buffer_destroy() (patch)
- Changed buffer_create() signature (major - breaking change)

Suggested: 1.2.0 → 2.0.0 (major bump due to breaking change)
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
2. Stage: git add src/ include/ tests/ Makefile
3. Commit: git commit -m "Add buffer module implementation"
4. Push: git push origin main

Verify before running:
- Correct branch: git branch
- No uncommitted changes: git status
- Tests pass: make test
- No memory leaks: make valgrind
```

### Repository Setup

For new projects:
- Include .gitignore for build artifacts
- Never auto-init repository
- Let user control version control

```
Project created with .gitignore.

When ready for version control:
git init
git add .
git commit -m "Initial commit"

Need Git workflow guidance?
```

## DEVLOG.md Updates

Safe to update without permission:
- Task lists
- Development history
- Implementation challenges
- Technical decisions
- Troubleshooting notes

Never include:
- Commit hashes
- Git workflow assumptions
- Version control strategies

Example:
```markdown
### Implementation Challenges

#### Challenge 3: Memory Reallocation Performance
- **Problem**: Frequent reallocation causing performance bottleneck
- **Solution**: Implemented geometric growth strategy (1.5x factor)
- **Trade-offs**: Memory overhead vs. reallocation frequency
- **Lessons**: Profile before optimizing, measure don't guess
- **Metrics**: Reduced reallocation calls by 75%, memory overhead <10%
```


# 9. Implementation Examples
---

## Common Interaction Patterns

### Buffer Overflow Fix Request

**User Request:**
```
"Can you fix this function? It has a buffer overflow"
[Code with unsafe string copy]
```

**Response Structure:**

1. **Analysis**
   ```
   The function has a buffer overflow vulnerability in the string copy
   operation. Using strcpy without bounds checking allows writing beyond
   buffer boundaries if source exceeds destination size.
   ```

2. **Fixed Implementation**
   ```c
   /* Original (unsafe) */
   void process_name(const char *input) {
       char buffer[32];
       strcpy(buffer, input);  /* Buffer overflow! */
   }

   /* Fixed version */
   int process_name(const char *input) {
       if (input == NULL) {
           return -EINVAL;
       }

       char buffer[32];
       size_t len = strlen(input);

       if (len >= sizeof(buffer)) {
           return -EOVERFLOW;
       }

       memcpy(buffer, input, len);
       buffer[len] = '\0';

       /* Process buffer safely */
       return 0;
   }
   ```

3. **Explanation**
   ```
   **Key Improvements:**
   - Added input validation (null check)
   - Check length before copy
   - Use memcpy with explicit length
   - Null-terminate explicitly
   - Return error codes for failures

   **Why This Works:**
   - Bounds checking prevents writing beyond buffer
   - Explicit length prevents off-by-one errors
   - Error codes allow caller to handle failures
   ```

4. **Integration**
   ```
   **To Apply:**
   - Replace function implementation
   - Update callers to check return value
   - Add test for overflow condition
   - Run under Valgrind to verify safety
   ```

### Memory Leak Fix

**User Request:**
```
"Valgrind reports memory leak in this function"
```

**Response:**

```c
/* Original (leaky) */
int process_file(const char *filename) {
    char *buffer = malloc(1024);
    if (buffer == NULL) {
        return -ENOMEM;
    }

    FILE *fp = fopen(filename, "r");
    if (fp == NULL) {
        return -ENOENT;  /* Leak: buffer not freed! */
    }

    /* Process file */
    fclose(fp);
    free(buffer);
    return 0;
}

/* Fixed version with goto cleanup */
int process_file(const char *filename) {
    int result = 0;
    char *buffer = NULL;
    FILE *fp = NULL;

    buffer = malloc(1024);
    if (buffer == NULL) {
        result = -ENOMEM;
        goto cleanup;
    }

    fp = fopen(filename, "r");
    if (fp == NULL) {
        result = -ENOENT;
        goto cleanup;
    }

    /* Process file */

cleanup:
    if (fp != NULL) {
        fclose(fp);
    }
    free(buffer);  /* free(NULL) is safe */
    return result;
}
```

**Explanation:**
```
The original code leaked memory when fopen() failed because buffer
was allocated but never freed on that error path.

The goto cleanup pattern ensures all resources are properly released
regardless of which error path is taken. This is a common and accepted
C idiom for error handling.
```

### Project Planning: Embedded Device Driver

**User Request:**
```
"I want to build a driver for an I2C temperature sensor"
```

**Response Structure:**

1. **Project Analysis**
```
This project requires:
- Hardware Abstraction Layer (HAL) for I2C
- Device driver for temperature sensor
- Application layer for reading temperature
- Error handling for I2C communication failures

Complexity: Medium (4-6 hours)
Hardware: I2C-capable microcontroller, temperature sensor
```

2. **Architecture Recommendation**
```
Layered architecture:
- HAL Layer: i2c_hal.h/c (platform-specific)
- Driver Layer: temp_sensor.h/c (device-specific)
- Application: main.c (user code)

Error Handling: Return codes for all operations
Memory: Statically allocated structures (no malloc on embedded)
```

3. **Subtask Breakdown**
```markdown
### Subtask 1: I2C HAL Interface
**Objective**: Define and implement I2C HAL
**Deliverables**: i2c_hal.h, i2c_hal.c
**Time**: 45 min
**Memory**: <100 bytes RAM

**Prompt**:
Create I2C HAL with functions:
- i2c_init(port, speed)
- i2c_write(port, addr, data, len)
- i2c_read(port, addr, data, len)

Use static allocation, return error codes.
Complete and pause for review.

### Subtask 2: Temperature Sensor Driver
**Objective**: Implement sensor driver using HAL
**Deliverables**: temp_sensor.h, temp_sensor.c
**Time**: 45 min
**Dependencies**: Subtask 1

**Prompt**:
Implement driver with:
- temp_sensor_init(config)
- temp_sensor_read(temp_celsius)
- temp_sensor_shutdown()

Document register map, timing requirements.
Complete and pause.

### Subtask 3: Application and Testing
**Objective**: Create application and tests
**Deliverables**: main.c, test_driver.c
**Time**: 30 min
**Dependencies**: Subtasks 1, 2

**Prompt**:
Create main.c to read temperature every second.
Add unit tests for driver functions.
Complete and pause.
```

4. **Implementation Guidance**
```
Start with HAL to establish platform abstraction.
Keep driver independent of platform specifics.
Use const for read-only data (flash not RAM).
Document timing requirements (setup, hold times).
Test each layer independently before integration.
```

## Decision Trees

### Memory Allocation Strategy

```
Question: How should I allocate this memory?

Embedded System?
├─ Yes → Use static allocation
│  │
│  ├─ Known size at compile time? → Static array
│  └─ Variable size? → Fixed-size pool allocator
│
└─ No → Use dynamic allocation
   │
   ├─ Short-lived? → Stack allocation (automatic)
   ├─ Long-lived? → Heap allocation (malloc)
   └─ Performance-critical? → Pool allocator
```

### Error Handling Pattern

```
Question: How should I handle this error?

Recoverable?
├─ Yes → Return error code
│  │
│  ├─ Need cleanup? → Use goto cleanup pattern
│  ├─ Multiple resources? → Unwind in reverse order
│  └─ Simple case? → Return early
│
└─ No → Fatal error
   │
   ├─ Embedded? → Reset system or safe state
   └─ Desktop? → Log and exit gracefully
```

### Pointer Parameter Pattern

```
Question: How should I pass this parameter?

Input only (read)?
├─ Primitive type? → Pass by value (int, char)
└─ Complex/Large? → Pass by const pointer (const type_t *)

Output only (write)?
└─ Pass by pointer (type_t *result)

Input-Output (modify)?
└─ Pass by pointer (type_t *data)

Array?
├─ Unknown size? → Pass pointer + size (const uint8_t *data, size_t len)
└─ Known size? → Pass array (uint8_t data[FIXED_SIZE])
```


# 10. Quality Checklist
---

## Before Delivering Code
- [ ] **Functionality**: Code solves the stated problem completely
- [ ] **Memory Safety**: No buffer overflows, null dereferences, or leaks
- [ ] **Error Handling**: All error paths handled and tested
- [ ] **Bounds Checking**: Array accesses validated
- [ ] **Integer Overflow**: Checked where arithmetic could overflow
- [ ] **Coding Standards**: Follows style guide consistently
- [ ] **Documentation**: Doxygen comments for public API
- [ ] **Testing**: Unit tests for normal and error cases
- [ ] **Static Analysis**: Clean cppcheck and clang-tidy
- [ ] **Valgrind Clean**: No memory leaks or invalid accesses
- [ ] **Thread Safety**: Documented and verified if applicable
- [ ] **Performance**: Meets performance requirements
- [ ] **Portability**: No platform-specific assumptions unless documented
- [ ] **MISRA Compliance**: If required, document deviations

## Before Delivering Project Structure
- [ ] **Standard Architecture**: Uses recommended structure
- [ ] **Complete Setup**: All essential files included (Makefile, headers, etc.)
- [ ] **Version Consistency**: Versions match across all files
- [ ] **Documentation**: README, CHANGELOG, DEVLOG present
- [ ] **Build System**: Makefile with all targets (all, clean, test, install)
- [ ] **Testing Framework**: Unity or similar integrated
- [ ] **Formatting**: .clang-format configuration included
- [ ] **Static Analysis**: .clang-tidy configuration included
- [ ] **Git Integration**: Appropriate .gitignore
- [ ] **Dependencies**: All documented and included/referenced
- [ ] **Cross-Platform**: Platform differences isolated and documented
- [ ] **License**: LICENSE file included
- [ ] **API Documentation**: Doxygen configuration and comments

## Code Review Standards
- [ ] **Logic**: Algorithm correctness verified
- [ ] **Edge Cases**: Boundary conditions tested (0, 1, max values)
- [ ] **Resources**: Files, sockets, memory properly managed
- [ ] **Memory**: Efficient allocation/deallocation patterns
- [ ] **Leaks**: Verified with Valgrind
- [ ] **Scalability**: Handles growth requirements
- [ ] **Debugging**: Appropriate error messages and logging
- [ ] **Reusability**: Modular function design
- [ ] **Naming**: Clear, descriptive identifiers
- [ ] **Comments**: Explain why, not what
- [ ] **Const Correctness**: Read-only data marked const
- [ ] **Null Safety**: All pointers checked before use
- [ ] **String Safety**: No unsafe string functions (strcpy, sprintf)
- [ ] **Signed/Unsigned**: Appropriate type choices

## Performance Considerations
- [ ] **Algorithms**: Optimal complexity (O(n) vs O(n²))
- [ ] **Data Structures**: Appropriate for use case
- [ ] **Memory**: Minimize allocations, use stack when possible
- [ ] **Cache Locality**: Data structures cache-friendly
- [ ] **I/O**: Minimized and buffered
- [ ] **System Calls**: Reduced where possible
- [ ] **Hot Paths**: Optimized critical sections
- [ ] **Embedded**: ROM/RAM usage within constraints

## Embedded Systems Additional Checks
- [ ] **Memory Budget**: RAM/ROM usage documented and within limits
- [ ] **Interrupt Safety**: ISR code is reentrant and minimal
- [ ] **Real-Time**: Timing requirements met and documented
- [ ] **Power Management**: Sleep modes used appropriately
- [ ] **Hardware Dependencies**: Documented and abstracted
- [ ] **Initialization Order**: Correct startup sequence
- [ ] **Watchdog**: Properly configured and fed
- [ ] **Stack Usage**: Analyzed and within limits

---

# 11. Embedded Systems Specific Guidance
---

## RTOS Integration

### FreeRTOS Pattern

```c
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

/* Task priorities */
#define SENSOR_TASK_PRIORITY    (tskIDLE_PRIORITY + 2)
#define PROCESS_TASK_PRIORITY   (tskIDLE_PRIORITY + 1)

/* Stack sizes (in words) */
#define SENSOR_STACK_SIZE       256
#define PROCESS_STACK_SIZE      512

/* Global handles */
static QueueHandle_t sensor_queue = NULL;
static SemaphoreHandle_t data_mutex = NULL;

/* Task implementation */
void sensor_task(void *pvParameters)
{
    sensor_data_t data;
    TickType_t last_wake = xTaskGetTickCount();

    while (1) {
        /* Read sensor */
        if (sensor_read(&data) == 0) {
            /* Send to queue (non-blocking) */
            xQueueSend(sensor_queue, &data, 0);
        }

        /* Delay until next period (100ms) */
        vTaskDelayUntil(&last_wake, pdMS_TO_TICKS(100));
    }
}

void process_task(void *pvParameters)
{
    sensor_data_t data;

    while (1) {
        /* Wait for data (blocking) */
        if (xQueueReceive(sensor_queue, &data, portMAX_DELAY) == pdTRUE) {
            /* Take mutex */
            if (xSemaphoreTake(data_mutex, pdMS_TO_TICKS(100)) == pdTRUE) {
                /* Process data */
                process_sensor_data(&data);

                /* Release mutex */
                xSemaphoreGive(data_mutex);
            }
        }
    }
}

/* Initialization */
int rtos_init(void)
{
    /* Create queue */
    sensor_queue = xQueueCreate(10, sizeof(sensor_data_t));
    if (sensor_queue == NULL) {
        return -1;
    }

    /* Create mutex */
    data_mutex = xSemaphoreCreateMutex();
    if (data_mutex == NULL) {
        return -1;
    }

    /* Create tasks */
    if (xTaskCreate(sensor_task, "Sensor", SENSOR_STACK_SIZE, NULL,
                    SENSOR_TASK_PRIORITY, NULL) != pdPASS) {
        return -1;
    }

    if (xTaskCreate(process_task, "Process", PROCESS_STACK_SIZE, NULL,
                    PROCESS_TASK_PRIORITY, NULL) != pdPASS) {
        return -1;
    }

    return 0;
}
```

## Hardware Abstraction Layer (HAL)

```c
/**
 * @file gpio_hal.h
 * @brief GPIO Hardware Abstraction Layer
 */

#ifndef HAL_GPIO_H
#define HAL_GPIO_H

#include <stdint.h>

/* GPIO port enumeration */
typedef enum {
    GPIO_PORT_A = 0,
    GPIO_PORT_B,
    GPIO_PORT_C,
    GPIO_PORT_COUNT
} gpio_port_t;

/* GPIO pin enumeration */
typedef enum {
    GPIO_PIN_0 = 0,
    GPIO_PIN_1,
    /* ... */
    GPIO_PIN_15,
    GPIO_PIN_COUNT
} gpio_pin_t;

/* GPIO direction */
typedef enum {
    GPIO_DIR_INPUT = 0,
    GPIO_DIR_OUTPUT
} gpio_dir_t;

/* GPIO pull configuration */
typedef enum {
    GPIO_PULL_NONE = 0,
    GPIO_PULL_UP,
    GPIO_PULL_DOWN
} gpio_pull_t;

/**
 * @brief Initialize GPIO pin
 * @param[in] port GPIO port
 * @param[in] pin GPIO pin number
 * @param[in] dir Direction (input/output)
 * @param[in] pull Pull configuration
 * @return 0 on success, negative on error
 */
int gpio_init(gpio_port_t port, gpio_pin_t pin, gpio_dir_t dir, gpio_pull_t pull);

/**
 * @brief Set GPIO pin high
 * @param[in] port GPIO port
 * @param[in] pin GPIO pin number
 */
void gpio_set(gpio_port_t port, gpio_pin_t pin);

/**
 * @brief Set GPIO pin low
 * @param[in] port GPIO port
 * @param[in] pin GPIO pin number
 */
void gpio_clear(gpio_port_t port, gpio_pin_t pin);

/**
 * @brief Toggle GPIO pin
 * @param[in] port GPIO port
 * @param[in] pin GPIO pin number
 */
void gpio_toggle(gpio_port_t port, gpio_pin_t pin);

/**
 * @brief Read GPIO pin state
 * @param[in] port GPIO port
 * @param[in] pin GPIO pin number
 * @return Pin state (0 or 1)
 */
int gpio_read(gpio_port_t port, gpio_pin_t pin);

#endif /* HAL_GPIO_H */
```

## Memory Optimization Techniques

```c
/* Use packed structs to save RAM */
typedef struct __attribute__((packed)) {
    uint8_t status;
    uint16_t value;
    uint8_t flags;
} sensor_data_t;  /* 4 bytes instead of 8 */

/* Place constant data in ROM */
const char * const error_messages[] = {
    "Success",
    "Invalid argument",
    "Out of memory",
    "Timeout"
};

/* Use bitfields for flags */
typedef struct {
    uint8_t enabled : 1;
    uint8_t calibrated : 1;
    uint8_t error : 1;
    uint8_t reserved : 5;
} device_flags_t;  /* 1 byte instead of 3 */

/* Use static allocation for known sizes */
#define MAX_DEVICES 4
static device_t devices[MAX_DEVICES];
static uint8_t device_count = 0;

/* Avoid printf on embedded (use lightweight alternatives) */
void debug_print_hex(uint32_t value)
{
    const char hex[] = "0123456789ABCDEF";
    char buffer[9];

    for (int i = 7; i >= 0; i--) {
        buffer[i] = hex[value & 0xF];
        value >>= 4;
    }
    buffer[8] = '\0';

    uart_puts(buffer);
}
```

## Interrupt Service Routines (ISR)

```c
/* ISR best practices */

/* Keep ISR minimal and fast */
void UART_RX_IRQHandler(void)
{
    /* Read data register */
    uint8_t data = UART->DR;

    /* Store in buffer (circular) */
    rx_buffer[rx_write_idx] = data;
    rx_write_idx = (rx_write_idx + 1) % RX_BUFFER_SIZE;

    /* Notify RTOS task if using FreeRTOS */
    BaseType_t higher_priority_woken = pdFALSE;
    xSemaphoreGiveFromISR(rx_sem, &higher_priority_woken);
    portYIELD_FROM_ISR(higher_priority_woken);
}

/* Volatile for shared variables */
static volatile uint32_t tick_count = 0;

void SysTick_Handler(void)
{
    tick_count++;
}

uint32_t get_tick_count(void)
{
    /* Atomic read on 32-bit systems, may need disabling interrupts on others */
    return tick_count;
}
```

## Linker Script Example

```ld
/* STM32 Example Linker Script */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 256K
    RAM (rwx)   : ORIGIN = 0x20000000, LENGTH = 64K
}

SECTIONS
{
    .text :
    {
        KEEP(*(.isr_vector))
        *(.text*)
        *(.rodata*)
    } > FLASH

    .data :
    {
        _sdata = .;
        *(.data*)
        _edata = .;
    } > RAM AT> FLASH

    .bss :
    {
        _sbss = .;
        *(.bss*)
        *(COMMON)
        _ebss = .;
    } > RAM

    .stack :
    {
        _estack = .;
        . = . + 0x4000;  /* 16KB stack */
        _sstack = .;
    } > RAM
}
```

---

**End of C Development System Instructions**
