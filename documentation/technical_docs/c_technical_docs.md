# C Technical Documentation

## Objective
Create comprehensive technical documentation that captures architecture decisions, system design, data flows, integration points, and development workflows for developers and technical stakeholders.

## Output Directory Structure

All documentation outputs should be saved in organized directories:

```
documentation/
└── technical_docs/
    ├── generated_docs/
    ├── templates/
    ├── assets/
    └── exports/
```

**Directory Setup**:

- Create `documentation/technical_docs/` directory in repository root if it doesn't exist

- All documentation files, templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `generated_docs/` - Generated documentation files (HTML, MD, PDF)

- `templates/` - Documentation templates and examples

- `assets/` - Images, diagrams, supplementary files

- `exports/` - Published documentation, release artifacts

## Implementation Checklist

### Architecture Documentation
- [ ] System architecture overview with diagrams
- [ ] Module responsibilities clearly defined
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
- [ ] Directory/file structure explained
- [ ] Module dependencies mapped
- [ ] Public vs static interfaces defined
- [ ] Header organization documented
- [ ] Code organization principles

### Data Flow
- [ ] Data flow diagrams created
- [ ] Memory management documented
- [ ] Function call flows explained
- [ ] Data transformation pipelines
- [ ] Error handling patterns

### Integration Points
- [ ] External library integrations documented
- [ ] System call interfaces
- [ ] IPC mechanisms
- [ ] Hardware interfaces (if applicable)
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
# C Technical Documentation Request

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

Please create comprehensive technical documentation for this C project following this protocol:

## Phase 1: Architecture Analysis

```markdown
# System Architecture

## Overview

[Project Name] is a [system/library/embedded application] written in C[version] that [high-level purpose].

## Architecture Style

- **Pattern**: [Modular/Layered/Event-Driven/Pipeline]
- **Target Platform**: [Linux/Windows/Embedded/Cross-platform]
- **Build System**: [Make/CMake/Autotools/Meson]
- **Memory Management**: [Manual/Pool-based/Custom allocator]
- **Threading**: [Single-threaded/POSIX threads/Platform-specific]

## Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Compiler | GCC/Clang | 11+/15+ | C11/C17 support, optimization |
| Build System | Make/CMake | Latest | Portability, dependency management |
| Testing | Check/Unity | Latest | Unit testing framework |
| Documentation | Doxygen | Latest | API documentation generation |
| Static Analysis | cppcheck/clang-tidy | Latest | Code quality, bug detection |

## Project Structure

```
project/
├── include/              # Public headers
│   ├── mylib.h          # Main public API
│   └── mylib_types.h    # Public type definitions
│
├── src/                 # Source files
│   ├── core/            # Core functionality
│   │   ├── engine.c
│   │   ├── engine.h     # Private header
│   │   └── utils.c
│   ├── io/              # I/O operations
│   │   ├── file_io.c
│   │   └── network.c
│   └── platform/        # Platform-specific code
│       ├── linux.c
│       └── windows.c
│
├── tests/               # Test suite
│   ├── test_core.c
│   └── test_io.c
│
├── docs/                # Documentation
├── examples/            # Example programs
├── CMakeLists.txt       # Build configuration
└── README.md
```

## Module Organization

### Core Module (`src/core/`)
**Purpose**: Core business logic
**Responsibilities**:
- Main algorithms
- Data structure management
- Business rule enforcement

**Public API** (include/mylib.h):
```c
/* Initialize the library */
int mylib_init(mylib_config_t *config);

/* Process data */
int mylib_process(const char *input, char **output);

/* Cleanup resources */
void mylib_cleanup(void);
```

**Private Implementation** (src/core/engine.c):
```c
#include "engine.h"
#include <stdlib.h>
#include <string.h>

/* Private state structure */
typedef struct {
    int initialized;
    void *internal_data;
} engine_state_t;

static engine_state_t g_state = {0};

/* Private helper function */
static int validate_input(const char *input) {
    if (input == NULL || *input == '\0') {
        return -1;
    }
    return 0;
}

/* Public API implementation */
int mylib_init(mylib_config_t *config) {
    if (g_state.initialized) {
        return -1; /* Already initialized */
    }

    g_state.internal_data = malloc(config->buffer_size);
    if (g_state.internal_data == NULL) {
        return -1; /* Allocation failed */
    }

    g_state.initialized = 1;
    return 0;
}

int mylib_process(const char *input, char **output) {
    if (!g_state.initialized) {
        return -1; /* Not initialized */
    }

    if (validate_input(input) != 0) {
        return -1; /* Invalid input */
    }

    /* Processing logic */
    size_t len = strlen(input);
    *output = malloc(len + 1);
    if (*output == NULL) {
        return -1;
    }

    strcpy(*output, input);
    return 0;
}

void mylib_cleanup(void) {
    if (g_state.initialized) {
        free(g_state.internal_data);
        g_state.internal_data = NULL;
        g_state.initialized = 0;
    }
}
```

## Memory Management

### Allocation Strategy
```c
/* Object creation with error handling */
my_object_t* my_object_create(size_t capacity) {
    my_object_t *obj = malloc(sizeof(my_object_t));
    if (obj == NULL) {
        return NULL;
    }

    obj->data = malloc(capacity);
    if (obj->data == NULL) {
        free(obj);
        return NULL;
    }

    obj->capacity = capacity;
    obj->size = 0;
    return obj;
}

/* Object destruction */
void my_object_destroy(my_object_t *obj) {
    if (obj != NULL) {
        free(obj->data);
        free(obj);
    }
}
```

### Memory Pool Pattern
```c
typedef struct memory_pool {
    void *memory;
    size_t block_size;
    size_t block_count;
    size_t used_count;
    void **free_blocks;
} memory_pool_t;

memory_pool_t* pool_create(size_t block_size, size_t block_count) {
    memory_pool_t *pool = malloc(sizeof(memory_pool_t));
    if (pool == NULL) return NULL;

    pool->memory = malloc(block_size * block_count);
    if (pool->memory == NULL) {
        free(pool);
        return NULL;
    }

    pool->block_size = block_size;
    pool->block_count = block_count;
    pool->used_count = 0;

    /* Initialize free list */
    pool->free_blocks = malloc(sizeof(void*) * block_count);
    for (size_t i = 0; i < block_count; i++) {
        pool->free_blocks[i] = (char*)pool->memory + (i * block_size);
    }

    return pool;
}

void* pool_alloc(memory_pool_t *pool) {
    if (pool->used_count >= pool->block_count) {
        return NULL; /* Pool exhausted */
    }
    return pool->free_blocks[pool->used_count++];
}

void pool_free(memory_pool_t *pool, void *ptr) {
    if (pool->used_count > 0) {
        pool->free_blocks[--pool->used_count] = ptr;
    }
}

void pool_destroy(memory_pool_t *pool) {
    if (pool != NULL) {
        free(pool->memory);
        free(pool->free_blocks);
        free(pool);
    }
}
```

## Error Handling

### Error Code Pattern
```c
/* Error codes */
typedef enum {
    MYLIB_OK = 0,
    MYLIB_ERR_INVALID_ARG = -1,
    MYLIB_ERR_NO_MEMORY = -2,
    MYLIB_ERR_NOT_INIT = -3,
    MYLIB_ERR_IO = -4
} mylib_error_t;

/* Get error message */
const char* mylib_strerror(int error_code) {
    switch (error_code) {
        case MYLIB_OK:
            return "Success";
        case MYLIB_ERR_INVALID_ARG:
            return "Invalid argument";
        case MYLIB_ERR_NO_MEMORY:
            return "Out of memory";
        case MYLIB_ERR_NOT_INIT:
            return "Library not initialized";
        case MYLIB_ERR_IO:
            return "I/O error";
        default:
            return "Unknown error";
    }
}

/* Usage example */
int result = mylib_process(input, &output);
if (result != MYLIB_OK) {
    fprintf(stderr, "Error: %s\n", mylib_strerror(result));
    return 1;
}
```

## Threading (POSIX)

```c
#include <pthread.h>

typedef struct {
    pthread_t thread;
    int running;
    void *data;
} worker_t;

void* worker_function(void *arg) {
    worker_t *worker = (worker_t*)arg;

    while (worker->running) {
        /* Process work */
        process_data(worker->data);

        /* Sleep to avoid busy-waiting */
        usleep(100000); /* 100ms */
    }

    return NULL;
}

int worker_start(worker_t *worker) {
    worker->running = 1;
    return pthread_create(&worker->thread, NULL, worker_function, worker);
}

void worker_stop(worker_t *worker) {
    worker->running = 0;
    pthread_join(worker->thread, NULL);
}
```

## Testing Strategy

### Unit Testing (Check framework)
```c
#include <check.h>

START_TEST(test_mylib_init_success)
{
    mylib_config_t config = {.buffer_size = 1024};
    int result = mylib_init(&config);
    ck_assert_int_eq(result, 0);
    mylib_cleanup();
}
END_TEST

START_TEST(test_mylib_process_invalid_input)
{
    char *output = NULL;
    int result = mylib_process(NULL, &output);
    ck_assert_int_eq(result, -1);
}
END_TEST

Suite* mylib_suite(void)
{
    Suite *s;
    TCase *tc_core;

    s = suite_create("MyLib");
    tc_core = tcase_create("Core");

    tcase_add_test(tc_core, test_mylib_init_success);
    tcase_add_test(tc_core, test_mylib_process_invalid_input);
    suite_add_tcase(s, tc_core);

    return s;
}

int main(void)
{
    int number_failed;
    Suite *s;
    SRunner *sr;

    s = mylib_suite();
    sr = srunner_create(s);

    srunner_run_all(sr, CK_NORMAL);
    number_failed = srunner_ntests_failed(sr);
    srunner_free(sr);

    return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}
```

## Build System

### CMakeLists.txt
```cmake
cmake_minimum_required(VERSION 3.15)
project(MyProject C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Compiler flags
if(CMAKE_C_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# Library
add_library(mylib STATIC
    src/core/engine.c
    src/core/utils.c
    src/io/file_io.c
)

target_include_directories(mylib
    PUBLIC include
    PRIVATE src
)

# Tests
enable_testing()
find_package(Check REQUIRED)

add_executable(test_mylib tests/test_core.c)
target_link_libraries(test_mylib mylib Check::check)
add_test(NAME test_mylib COMMAND test_mylib)

# Example
add_executable(example examples/example.c)
target_link_libraries(example mylib)
```

### Makefile (alternative)
```makefile
CC = gcc
CFLAGS = -std=c11 -Wall -Wextra -Wpedantic -Werror -O2
INCLUDES = -Iinclude -Isrc
LDFLAGS = -lpthread

SRC = $(wildcard src/**/*.c src/*.c)
OBJ = $(SRC:.c=.o)

TARGET = libmylib.a

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJ)
	ar rcs $@ $^

%.o: %.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

test: $(TARGET)
	$(CC) $(CFLAGS) $(INCLUDES) tests/test_core.c -o test_runner -L. -lmylib -lcheck
	./test_runner

clean:
	rm -f $(OBJ) $(TARGET) test_runner
```

## Development Workflow

```bash
# Build
mkdir build && cd build
cmake ..
make

# Run tests
make test

# Static analysis
cppcheck --enable=all --suppress=missingInclude src/

# Memory leak detection (Valgrind)
valgrind --leak-check=full ./test_runner

# Code coverage
gcc -fprofile-arcs -ftest-coverage src/*.c tests/*.c -o test_coverage
./test_coverage
gcov src/*.c
```

## Documentation (Doxygen)

```c
/**
 * @file mylib.h
 * @brief Main API for MyLib
 * @author John Doe
 * @date 2024-01-16
 */

/**
 * @brief Initialize the library
 *
 * This function must be called before any other library functions.
 *
 * @param config Configuration structure
 * @return 0 on success, negative error code on failure
 *
 * @see mylib_cleanup()
 */
int mylib_init(mylib_config_t *config);
```
```

---

## Best Practices

1. **Memory Safety**
   - Always check malloc/calloc return values
   - Free in reverse order of allocation
   - Set pointers to NULL after freeing
   - Use valgrind to detect leaks

2. **Error Handling**
   - Return error codes from functions
   - Use errno for system call errors
   - Provide descriptive error messages
   - Clean up on error paths

3. **Code Quality**
   - Follow consistent naming conventions
   - Keep functions small and focused
   - Use static for internal linkage
   - Document with Doxygen comments

4. **Platform Portability**
   - Use standard C library when possible
   - Abstract platform-specific code
   - Test on multiple platforms
   - Use feature detection in build system

5. **Security**
   - Validate all inputs
   - Use safe string functions (strncpy, snprintf)
   - Avoid buffer overflows
   - Initialize all variables

---

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p documentation/technical_docs/generated_docs
mkdir -p documentation/technical_docs/templates
mkdir -p documentation/technical_docs/assets
mkdir -p documentation/technical_docs/exports
```

**Save files as follows**:

- Generated docs → `documentation/technical_docs/generated_docs/`

- Templates → `documentation/technical_docs/templates/`

- Assets → `documentation/technical_docs/assets/`

- Exports → `documentation/technical_docs/exports/`

Replace `{phase_name}` with the specific phase (docstrings, comments, user_docs, technical_docs, api_docs, or sbom).

~~~

## Output Format Specifications

The technical documentation should:
- Provide architecture overview focused on C-specific concerns
- Document memory management strategies
- Show clear error handling patterns
- Document build system configuration
- Address portability and platform-specific code
- Include comprehensive testing approach
- Target C developers
