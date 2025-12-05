---
name: setup-c-system-prompt
description: Configure comprehensive C development system prompt for Claude Code with embedded systems focus, MISRA-C standards, and memory safety best practices
version: 1.0.0
author: Benjamin Dourthe
language: C
category: Configuration
tags: [c, setup, system-prompt, configuration, embedded, standards, misra]
priority: HIGH
---

# Setup C System Prompt

Configure Claude Code with comprehensive C development standards, embedded systems best practices, and safety-critical development workflows optimized for production-quality C code generation.

## When to Use This Skill

Use this skill when you need to:

- Set up a new C project with Claude Code

- Configure Claude Code for C development (application or embedded systems)

- Apply comprehensive C development standards (C11/C17/C23)

- Establish consistent coding practices for C projects

- Optimize Claude Code for embedded systems development

- Implement MISRA-C or CERT-C compliance requirements

- Develop safety-critical or real-time systems

## What This Skill Does

This skill helps you configure Claude Code with:

1. **C Development Standards**

   - C11/C17/C23 standards compliance

   - MISRA-C and CERT-C guidelines

   - Memory safety and pointer discipline

   - Include organization and header guards

   - Function design and naming conventions

2. **Project Architecture Guidelines**

   - Standard C application structure (src/, include/, tests/)

   - Embedded systems structure (HAL, drivers, RTOS integration)

   - Makefile-based build system

   - Static analysis configuration (.clang-format, .clang-tidy)

   - Documentation structure (README, CHANGELOG, DEVLOG, Doxygen)

3. **Memory Safety and Security**

   - Buffer overflow prevention

   - Integer overflow checking

   - Pointer safety patterns

   - Resource management (RAII-like patterns in C)

   - Bounds checking and validation

4. **Testing Framework**

   - Unity test framework integration

   - Test structure and patterns

   - Valgrind memory checking

   - Address sanitizer usage

   - Coverage analysis

5. **Embedded Systems Support**

   - Hardware abstraction layer (HAL) patterns

   - RTOS integration (FreeRTOS, bare metal)

   - Interrupt service routines (ISR) best practices

   - Memory optimization techniques

   - Linker script guidance

6. **Development Workflow**

   - Task breakdown methodology

   - Iterative testing protocol

   - Quality gates and checklists

   - Version control best practices

   - Static analysis integration

## Prerequisites

- Claude Code installed and configured

- C compiler installed:

  - GCC 9.0+ or Clang 10.0+ (Linux/macOS)

  - MinGW-w64 or MSVC (Windows)

- Make or CMake build system

- Basic understanding of C development

- Project directory created (or ready to create new project)

- Optional: Cross-compiler for embedded targets

## Instructions

### Step 1: Choose System Prompt Version

Decide between two versions based on your needs:

**Comprehensive Version (~40k tokens)**

- Best for: Complex projects, embedded systems, safety-critical applications

- Features: Complete architectural guidance, MISRA-C compliance, embedded patterns, HAL design

- Token count: ~40,000 tokens

- Use cases: Production firmware, device drivers, safety-critical systems, RTOS applications

- File: `agent_prompts/autonomous_agents/claude_code/c/CLAUDE_comprehensive_40k.md`

**Condensed Version (~20k tokens)**

- Best for: Quick development, CLI tools, prototyping, learning projects

- Features: Essential guidelines, core best practices, streamlined workflow

- Token count: ~20,000 tokens

- Use cases: Utility programs, tools, simple applications, proof-of-concepts

- File: `agent_prompts/autonomous_agents/claude_code/c/CLAUDE_condensed_20k.md`

### Step 2: Configure Claude Code

There are two methods to configure Claude Code with the C system prompt:

#### Method A: Project-Level CLAUDE.md (Recommended)

1. Navigate to your project root directory

2. Copy the chosen system prompt file to `CLAUDE.md`:
   ```bash
   # For comprehensive version (embedded/production)
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/c/CLAUDE_comprehensive_40k.md ./CLAUDE.md

   # For condensed version (tools/prototypes)
   cp path/to/ai_templates/agent_prompts/autonomous_agents/claude_code/c/CLAUDE_condensed_20k.md ./CLAUDE.md
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

1. **Create a simple C function** and observe if it follows the standards:
   ```
   "Create a function that safely copies a string with bounds checking"
   ```

   Expected behavior:

   - Proper header guards or inclusion

   - Doxygen-style documentation

   - Input validation (null pointer checks)

   - Bounds checking (strncpy or memcpy with size)

   - Return error codes (errno-style)

   - No inline comments unless essential

2. **Request project structure** and verify it matches standards:
   ```
   "Show me the recommended project structure for an embedded C application with FreeRTOS"
   ```

   Expected behavior:

   - Includes include/, src/, tests/ directories

   - Shows HAL, drivers, RTOS structure

   - Includes Makefile or CMakeLists.txt

   - Shows linker scripts for embedded targets

   - Includes CHANGELOG.md, README.md, DEVLOG.md

3. **Ask about testing** and confirm it knows the framework:
   ```
   "How should I structure my unit tests for this C project?"
   ```

   Expected behavior:

   - Mentions Unity test framework

   - Describes test structure and patterns

   - Explains Valgrind for memory checking

   - Discusses address sanitizer usage

   - Mentions coverage analysis tools

4. **Verify memory safety awareness**:
   ```
   "Review this code for memory safety issues: [paste code with buffer overflow]"
   ```

   Expected behavior:

   - Identifies buffer overflow vulnerability

   - Suggests bounds checking

   - Recommends safe string functions

   - Proposes input validation

   - Explains security implications

### Step 4: Configure Build System

Set up your build system with the appropriate configuration:

#### For Standard Applications (Makefile):

```makefile
# Copy Makefile template from system prompt
# Includes: debug/release builds, testing, static analysis, Valgrind

CC = gcc
CFLAGS = -Wall -Wextra -Werror -std=c11 -pedantic
CFLAGS += -O2 -g
CFLAGS += -Iinclude

# Add sanitizers for development
CFLAGS_DEBUG = $(CFLAGS) -O0 -fsanitize=address -fsanitize=undefined
```

#### For Embedded Systems:

```makefile
# Cross-compilation settings
CC = arm-none-eabi-gcc
CFLAGS = -Wall -Wextra -Werror -std=c11
CFLAGS += -mcpu=cortex-m4 -mthumb
CFLAGS += -Os -ffunction-sections -fdata-sections
LDFLAGS = -Tlinker/flash.ld -Wl,--gc-sections
```

### Step 5: Set Up Static Analysis

Configure formatting and analysis tools:

1. **Create `.clang-format`** for consistent formatting:
   ```yaml
   ---
   Language: Cpp
   BasedOnStyle: LLVM
   IndentWidth: 4
   ColumnLimit: 100
   PointerAlignment: Right
   BreakBeforeBraces: Linux
   ```

2. **Create `.clang-tidy`** for static analysis:
   ```yaml
   ---
   Checks: >
     -*,
     bugprone-*,
     cert-*,
     clang-analyzer-*,
     readability-*
   ```

3. **Run analysis** regularly:
   ```bash
   # Format code
   clang-format -i src/*.c include/*.h

   # Static analysis
   clang-tidy src/*.c -- -Iinclude
   cppcheck --enable=all --suppress=missingIncludeSystem src/
   ```

### Step 6: Customize for Your Requirements (Optional)

If you need to add organization-specific standards or embedded platform details:

1. Open the CLAUDE.md file in your project

2. Add a new section at the end:
   ```markdown
   # Organization-Specific Standards

   ## Additional Requirements
   - [MISRA-C compliance level]

   - [Coding standard deviations]

   - [Platform-specific constraints]

   - [Memory budgets (RAM/ROM)]

   - [Real-time requirements]

   - [Safety certification level]
   ```
3. Save and restart Claude Code session

### Step 7: Initialize Test Framework

Set up Unity testing framework:

```bash
# Option 1: Git submodule
git submodule add https://github.com/ThrowTheSwitch/Unity.git tests/unity

# Option 2: Copy Unity files
# Download unity.c and unity.h to tests/ directory
```

Create test Makefile:
```makefile
# tests/Makefile
include ../Makefile.common

TEST_SOURCES = $(wildcard test_*.c)
TEST_BINS = $(TEST_SOURCES:.c=)

test: $(TEST_BINS)
	@for test in $(TEST_BINS); do ./$$test; done

test_%: test_%.c ../src/%.o unity/unity.o
	$(CC) $(CFLAGS) -I../include -Iunity $^ -o $@
```

### Step 8: Commit to Version Control

Add the CLAUDE.md and configuration files to your repository:

```bash
git add CLAUDE.md .clang-format .clang-tidy Makefile
git commit -m "Add Claude Code C system prompt configuration"
git push
```

## Key Features of the C System Prompt

### 1. Include Organization
Automatically organizes includes in the correct order:

1. System headers (alphabetically sorted)

2. Third-party library headers (alphabetically sorted)

3. Project headers (alphabetically sorted)

**Example:**
```c
/* System headers */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Third-party headers */
#include <unity.h>

/* Project headers */
#include "project_name/api.h"
#include "project_name/types.h"
```

### 2. Header Guards
Consistent header guard pattern:
```c
#ifndef PROJECT_NAME_MODULE_H
#define PROJECT_NAME_MODULE_H

/* Header content */

#endif /* PROJECT_NAME_MODULE_H */
```

### 3. Memory Safety Patterns
**Buffer Overflow Prevention:**
```c
/* Use bounds-checked functions */
strncpy(dest, src, sizeof(dest) - 1);
dest[sizeof(dest) - 1] = '\0';

snprintf(buffer, sizeof(buffer), "Value: %d", value);
```

**Pointer Validation:**
```c
/* Always validate pointers */
if (ptr == NULL) {
    return -EINVAL;
}
```

**Integer Overflow Checking:**
```c
/* Check before allocation */
if (count > SIZE_MAX / sizeof(item_t)) {
    return -EOVERFLOW;
}
size_t total = count * sizeof(item_t);
```

### 4. Error Handling
**errno-style return codes:**
```c
#define SUCCESS 0
#define ERROR_INVALID_ARG -EINVAL
#define ERROR_NO_MEMORY -ENOMEM

int function(const char *input, result_t *output) {
    if (input == NULL || output == NULL) {
        return -EINVAL;
    }
    /* Implementation */
    return SUCCESS;
}
```

**goto cleanup pattern:**
```c
int complex_operation(void) {
    int result = -1;
    char *buffer = NULL;
    FILE *fp = NULL;

    buffer = malloc(SIZE);
    if (buffer == NULL) {
        result = -ENOMEM;
        goto cleanup;
    }

    fp = fopen("file.txt", "r");
    if (fp == NULL) {
        result = -errno;
        goto cleanup;
    }

    /* Main logic */
    result = 0;

cleanup:
    if (fp) fclose(fp);
    free(buffer);
    return result;
}
```

### 5. Naming Conventions
- **Functions**: `projectname_module_action()` (namespace prefix)

- **Types**: `snake_case_t` suffix

- **Constants**: `UPPER_CASE` with module prefix

- **Variables**: `snake_case`

- **Private functions**: `static` with descriptive names

### 6. Doxygen Documentation
**Function documentation:**
```c
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

### 7. Embedded Systems Support
**HAL Pattern:**
```c
/* Hardware abstraction layer interface */
typedef enum {
    GPIO_PORT_A = 0,
    GPIO_PORT_B,
    GPIO_PORT_C
} gpio_port_t;

int gpio_init(gpio_port_t port, uint8_t pin);
void gpio_set(gpio_port_t port, uint8_t pin);
void gpio_clear(gpio_port_t port, uint8_t pin);
int gpio_read(gpio_port_t port, uint8_t pin);
```

**ISR Best Practices:**
```c
/* Keep ISR minimal and fast */
void UART_RX_IRQHandler(void) {
    uint8_t data = UART->DR;
    rx_buffer[rx_write_idx] = data;
    rx_write_idx = (rx_write_idx + 1) % RX_BUFFER_SIZE;
}
```

**Memory Optimization:**
```c
/* Use packed structs */
typedef struct __attribute__((packed)) {
    uint8_t status;
    uint16_t value;
    uint8_t flags;
} sensor_data_t;  /* 4 bytes instead of 8 */

/* Place constants in ROM */
const char * const error_messages[] = {
    "Success",
    "Error"
};
```

### 8. Testing Framework
**Unity test structure:**
```c
#include "unity.h"
#include "module_under_test.h"

void setUp(void) {
    /* Initialize before each test */
}

void tearDown(void) {
    /* Clean up after each test */
}

void test_function_returns_zero_on_success(void) {
    int result = function_under_test(valid_input);
    TEST_ASSERT_EQUAL_INT(0, result);
}

void test_function_returns_error_on_null_input(void) {
    int result = function_under_test(NULL);
    TEST_ASSERT_EQUAL_INT(-EINVAL, result);
}

int main(void) {
    UNITY_BEGIN();
    RUN_TEST(test_function_returns_zero_on_success);
    RUN_TEST(test_function_returns_error_on_null_input);
    return UNITY_END();
}
```

**Valgrind integration:**
```bash
# Check for memory leaks
valgrind --leak-check=full ./build/bin/test_runner

# Check for memory errors
valgrind --tool=memcheck --track-origins=yes ./build/bin/test_runner
```

### 9. Static Analysis Integration
**Makefile target for analysis:**
```makefile
analysis:
	cppcheck --enable=all --suppress=missingIncludeSystem src/
	clang-tidy $(SOURCES) -- $(CFLAGS)
	# MISRA-C checking if tool available
	# cppcheck --addon=misra.py src/
```

### 10. Development Workflow
**Iterative testing protocol:**

1. Create temp tests in `tests/temp/`

2. Write challenging tests with edge cases

3. Implement solution

4. Run tests and iterate until passing

5. Delete temp tests, move valuable tests to permanent suite

6. Document in DEVLOG.md

## Common Configuration Issues

### Issue: System Prompt Not Loading
**Solution**: Verify CLAUDE.md is in the project root directory and restart Claude Code session

### Issue: Token Limit Warnings
**Solution**: Switch from comprehensive (~40k) to condensed (~20k) version

### Issue: MISRA-C Compliance Not Mentioned
**Solution**: Comprehensive version includes MISRA-C; add organization-specific deviations to CLAUDE.md

### Issue: Embedded Features Not Recognized
**Solution**:

- Use comprehensive version for embedded projects

- Specify target platform in questions: "How do I implement I2C HAL for STM32?"

### Issue: Build System Not Matching Standards
**Solution**: Reference Makefile template in system prompt, customize for your toolchain

### Issue: Static Analysis Warnings Inconsistent
**Solution**:

- Create `.clang-tidy` configuration in project root

- Run with: `clang-tidy src/*.c -- -Iinclude -std=c11`

- Add suppression for false positives

## Success Criteria

After completing this skill, you should have:

- [ ] Claude Code configured with C system prompt (CLAUDE.md in project root)

- [ ] Verified configuration by testing function generation (with memory safety)

- [ ] Confirmed project structure knowledge (standard or embedded)

- [ ] Validated testing framework understanding (Unity)

- [ ] Verified memory safety awareness (buffer overflow detection)

- [ ] Set up build system (Makefile or CMake)

- [ ] Configured static analysis tools (.clang-format, .clang-tidy)

- [ ] Initialized test framework (Unity)

- [ ] Optionally customized for organization-specific needs

- [ ] Committed CLAUDE.md and configurations to version control

## Related Skills

- `generate-c-documentation`: Generate Doxygen documentation for C code

- `setup-embedded-toolchain`: Configure cross-compilation toolchain

- `implement-hal-layer`: Create hardware abstraction layer

- `misra-compliance-check`: Verify MISRA-C compliance

- `optimize-embedded-memory`: Reduce RAM/ROM usage

- `code-review-c-safety`: Review C code for safety issues

## Additional Resources

### Standards and Guidelines
- [C11 Standard (ISO/IEC 9899:2011)](http://www.open-std.org/jtc1/sc22/wg14/)

- [MISRA-C:2012 Guidelines](https://www.misra.org.uk/)

- [CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c/SEI+CERT+C+Coding+Standard)

- [Linux Kernel Coding Style](https://www.kernel.org/doc/html/latest/process/coding-style.html)

### Tools
- [Unity Test Framework](https://github.com/ThrowTheSwitch/Unity)

- [Valgrind Memory Analyzer](https://valgrind.org/)

- [Cppcheck Static Analyzer](http://cppcheck.sourceforge.net/)

- [Clang Static Analyzer](https://clang-analyzer.llvm.org/)

- [Address Sanitizer](https://github.com/google/sanitizers)

### Embedded Development
- [FreeRTOS](https://www.freertos.org/)

- [ARM CMSIS](https://developer.arm.com/tools-and-software/embedded/cmsis)

- [GNU ARM Embedded Toolchain](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm)

- [OpenOCD](http://openocd.org/)

### Books and References
- "The C Programming Language" by Kernighan and Ritchie

- "Expert C Programming" by Peter van der Linden

- "Embedded C Coding Standard" by Michael Barr

- "Making Embedded Systems" by Elecia White

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5
**C Standards**: C11, C17, C23
**Compliance**: MISRA-C:2012, CERT-C
