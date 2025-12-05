---
name: cleanup-c
description: Remove dead code, fix memory leaks, and apply C best practices for improved maintainability and safety
version: 1.0.0
author: Benjamin Dourthe
language: C
category: Code Cleanup
priority: MEDIUM
tags: [c, cleanup, refactoring, memory-safety, dead-code, embedded, misra]
template_source: code_cleanup/c_cleanup.md
---

# C Code Cleanup

Systematically identify and remove dead code, fix memory issues, and apply C best practices to maintain a lean, safe, and maintainable codebase.

## When to Use This Skill

Use this skill when you need to:

- Remove unused includes, functions, variables, and types

- Fix memory leaks and buffer overflows

- Consolidate duplicate code

- Apply C best practices (const correctness, static functions, error handling)

- Clean up printf statements and commented code

- Optimize include organization

- Prepare codebase for embedded systems deployment

- Address MISRA-C or CERT-C violations

## What This Skill Does

This skill performs comprehensive C code cleanup:

### 1. Dead Code Detection
- **Unused #include Directives**: Identifies and removes unused headers

- **Unused Functions**: Finds static functions never called

- **Unused Variables**: Identifies variables assigned but never used

- **Unused Macros**: Detects #define macros that are never used

- **Unused Types**: Finds typedef/struct definitions never used

- **Unreachable Code**: Finds code after return statements

- **Empty Blocks**: Detects empty functions or unnecessary code

### 2. Memory Safety
- **Memory Leaks**: Ensures all malloc() has corresponding free()

- **Double Free**: Checks for potential double-free vulnerabilities

- **Use After Free**: Identifies potential use-after-free issues

- **Buffer Overflows**: Reviews array access and unsafe string functions

- **NULL Pointer Checks**: Adds missing NULL checks after malloc()

- **Resource Cleanup**: Ensures file handles, sockets are properly closed

### 3. Duplicate Code Consolidation
- **Exact Duplicates**: Finds identical code blocks

- **Near Duplicates**: Detects similar code with minor variations

- **Duplicate Logic**: Identifies functionally equivalent implementations

- **Consolidation Strategy**: Recommends refactoring approach

### 4. C Best Practices
- **Const Correctness**: Adds const to parameters and variables

- **Static Functions**: Marks internal functions as static

- **Function Prototypes**: Ensures all functions have prototypes

- **Avoid Global Variables**: Minimizes global state

- **Error Handling**: Checks return values

- **Initialization**: Initializes all variables at declaration

- **Array Bounds**: Ensures array accesses are within bounds

- **String Safety**: Replaces strcpy/strcat with safer alternatives

### 5. Debug Statement Cleanup
- **Print Statements**: Removes debug printf()

- **Commented Code**: Cleans up old commented-out code

- **TODO Comments**: Catalogs and prioritizes TODO items

- **Debug Macros**: Reviews DEBUG-only code sections

### 6. Include Organization
- **Organize Includes**: Sorts includes in standard order

- **Include Guards**: Ensures proper include guards in headers

- **Forward Declarations**: Uses forward declarations to reduce dependencies

## Prerequisites

- C codebase to clean up

- Version control (git) for safe cleanup

- Test suite (recommended)

- Backup of codebase

- C compiler (gcc, clang) and build system (Make, CMake)

## Instructions

### Step 1: Prepare for Cleanup

1. **Commit Current State**:
   ```bash
   git add .
   git commit -m "Pre-cleanup snapshot"
   ```

2. **Create Cleanup Branch**:
   ```bash
   git checkout -b code-cleanup
   ```

3. **Run Existing Tests**:
   ```bash
   make test
   # or
   ./run_tests
   ```

4. **Run Static Analysis**:
   ```bash
   cppcheck --enable=all --inconclusive .
   clang-tidy *.c
   ```

5. **Create Output Directory**:
   ```bash
   mkdir -p cleanup_report/{templates,assets,exports}
   ```

### Step 2: Invoke the Cleanup Skill

Tell Claude Code to use this skill:

```
"Use the cleanup-c skill to analyze and clean up this C codebase.
Focus on:

1. Removing all unused includes, functions, and variables

2. Fixing memory leaks and buffer overflows

3. Consolidating duplicate code

4. Applying C best practices (const correctness, static functions)

5. Removing printf statements

6. Organizing includes properly

7. Addressing static analysis warnings

Save all reports to cleanup_report/ directory."
```

### Step 3: Review Cleanup Plan

Claude Code will generate a comprehensive cleanup plan including:

1. **Dead Code Candidates** - List of unused code

2. **Memory Safety Issues** - Leaks, overflows, null pointer issues

3. **Duplication Report** - Duplicate code locations

4. **Best Practices** - Areas needing improvement

5. **Static Analysis Findings** - cppcheck, clang-tidy warnings

6. **Risk Assessment** - Impact analysis

7. **Implementation Plan** - Ordered steps

**Review the plan before proceeding with changes!**

### Step 4: Execute Cleanup in Phases

**Phase 1: Low-Risk Cleanup**

- Remove unused includes

- Clean printf statements

- Remove commented code

- Organize includes

**Phase 2: Memory Safety**

- Fix memory leaks

- Add NULL checks

- Fix buffer overflows

- Replace unsafe string functions

**Phase 3: Structural Changes**

- Consolidate duplicates

- Remove dead functions

- Simplify complex code

- Extract constants

**Phase 4: Best Practices**

- Apply const correctness

- Mark static functions

- Add function prototypes

- Check error returns

**Phase 5: Verification**

- Run tests after each phase

- Run static analysis

- Test on target hardware (embedded)

- Document any issues

**Phase 6: Multi-Pass Protocol**

- First pass: Apply cleanup

- Verification pass: Check for missed opportunities

- Repeat until complete

- Track statistics

### Step 5: Test After Cleanup

1. **Build**:
   ```bash
   make clean
   make all
   ```

2. **Run Tests**:
   ```bash
   make test
   ./run_tests
   ```

3. **Static Analysis**:
   ```bash
   cppcheck --enable=all --inconclusive .
   clang-tidy *.c
   ```

4. **Memory Analysis** (if using Valgrind):
   ```bash
   valgrind --leak-check=full ./your_program
   ```

5. **Target Hardware** (embedded):
   ```bash
   # Flash and test on actual hardware
   ```

### Step 6: Review and Commit

1. **Review Changes**:
   ```bash
   git diff
   ```

2. **Stage and Commit**:
   ```bash
   git add .
   git commit -m "Remove unused includes and functions"

   git add .
   git commit -m "Fix memory leaks and add NULL checks"

   git add .
   git commit -m "Apply const correctness and static functions"
   ```

3. **Merge to Main**:
   ```bash
   git checkout main
   git merge code-cleanup
   git push
   ```

## Cleanup Categories and Examples

### Category 1: Unused Includes
**Before:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "database.h"
#include "network.h"

int main(void) {
    printf("Hello\n");
    return 0;
}
```

**After:**
```c
#include <stdio.h>

int main(void) {
    printf("Hello\n");
    return 0;
}
```

### Category 2: Memory Leaks
**Before:**
```c
char* read_file(const char* path) {
    FILE* f = fopen(path, "r");
    if (!f) return NULL;

    char* buffer = malloc(1024);
    fread(buffer, 1, 1024, f);
    // Missing fclose(f) - file handle leak
    return buffer;
    // Caller must free buffer - easy to forget
}
```

**After:**
```c
int read_file(const char* path, char* buffer, size_t size) {
    FILE* f = fopen(path, "r");
    if (!f) return -1;

    size_t read = fread(buffer, 1, size, f);
    fclose(f);

    return (int)read;
}
// Caller provides buffer, clear responsibility
```

### Category 3: Buffer Overflows
**Before:**
```c
void copy_string(char* dest, const char* src) {
    strcpy(dest, src);  // Unsafe - no bounds checking
}

void process_input(const char* input) {
    char buffer[64];
    sprintf(buffer, "Processing: %s", input);  // Unsafe
}
```

**After:**
```c
void copy_string(char* dest, size_t dest_size, const char* src) {
    strncpy(dest, src, dest_size - 1);
    dest[dest_size - 1] = '\0';  // Ensure null termination
}

void process_input(const char* input) {
    char buffer[64];
    snprintf(buffer, sizeof(buffer), "Processing: %s", input);
}
```

### Category 4: NULL Pointer Checks
**Before:**
```c
struct user* create_user(const char* name) {
    struct user* u = malloc(sizeof(struct user));
    strcpy(u->name, name);  // Crash if malloc failed
    return u;
}
```

**After:**
```c
struct user* create_user(const char* name) {
    struct user* u = malloc(sizeof(struct user));
    if (!u) {
        return NULL;
    }

    strncpy(u->name, name, sizeof(u->name) - 1);
    u->name[sizeof(u->name) - 1] = '\0';
    return u;
}
```

### Category 5: Const Correctness
**Before:**
```c
int calculate_total(int* items, int count) {
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += items[i];
    }
    return total;
}
```

**After:**
```c
int calculate_total(const int* items, int count) {
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += items[i];
    }
    return total;
}
```

### Category 6: Static Functions
**Before:**
```c
// file.c
void internal_helper(int x) {  // Visible in other files
    // internal logic
}

void public_api(int x) {
    internal_helper(x);
}
```

**After:**
```c
// file.c
static void internal_helper(int x) {  // File-scoped
    // internal logic
}

void public_api(int x) {
    internal_helper(x);
}
```

### Category 7: Error Handling
**Before:**
```c
void process_file(const char* path) {
    FILE* f = fopen(path, "r");
    char buffer[256];
    fgets(buffer, sizeof(buffer), f);  // No check if fopen succeeded
    printf("%s\n", buffer);
    fclose(f);
}
```

**After:**
```c
int process_file(const char* path) {
    FILE* f = fopen(path, "r");
    if (!f) {
        return -1;
    }

    char buffer[256];
    if (fgets(buffer, sizeof(buffer), f) != NULL) {
        printf("%s\n", buffer);
    }

    fclose(f);
    return 0;
}
```

### Category 8: Duplicate Code Consolidation
**Before:**
```c
int validate_user(struct user* u) {
    if (!u) return 0;
    if (!u->name[0]) return 0;
    if (!u->email[0]) return 0;
    if (!strchr(u->email, '@')) return 0;
    return 1;
}

int validate_admin(struct admin* a) {
    if (!a) return 0;
    if (!a->name[0]) return 0;
    if (!a->email[0]) return 0;
    if (!strchr(a->email, '@')) return 0;
    return 1;
}
```

**After:**
```c
struct account {
    char name[64];
    char email[128];
};

int validate_account(const struct account* acc) {
    if (!acc) return 0;
    if (!acc->name[0]) return 0;
    if (!acc->email[0]) return 0;
    if (!strchr(acc->email, '@')) return 0;
    return 1;
}
```

## Output Structure

```
cleanup_report/
├── templates/
│   ├── cleanup_checklist.md
│   ├── c_best_practices.md
│   └── misra_c_guide.md
├── assets/
│   ├── duplication_graph.png
│   ├── memory_leak_report.png
│   └── complexity_heatmap.png
└── exports/
    ├── cleanup_report.md
    ├── dead_code_list.md
    ├── memory_safety_issues.md
    ├── duplication_analysis.md
    ├── static_analysis_findings.md
    └── risk_assessment.md
```

## Safety Measures

1. **Version Control Required**

2. **Test Coverage**

3. **Incremental Approach**

4. **Risk Assessment**

5. **Documentation**

## Success Criteria

- [ ] All unused includes removed

- [ ] No printf debugging statements

- [ ] No commented-out code

- [ ] All memory leaks fixed

- [ ] NULL checks added

- [ ] Buffer overflows fixed

- [ ] Const correctness applied

- [ ] Static functions marked

- [ ] All tests passing

- [ ] Static analysis passes

- [ ] Code builds successfully

- [ ] Cleanup documented

## Tools and Libraries

### Static Analysis
- **cppcheck**: C/C++ static analyzer

- **clang-tidy**: Clang-based linter

- **Coverity**: Commercial static analysis

- **PC-lint**: Commercial linter

### Memory Analysis
- **Valgrind**: Memory error detector

- **AddressSanitizer**: Google memory error detector

- **MemorySanitizer**: Uninitialized memory detector

```bash
# Install tools
sudo apt-get install cppcheck valgrind clang-tidy

# Run analysis
cppcheck --enable=all --inconclusive .
clang-tidy *.c
valgrind --leak-check=full ./program

# Compile with sanitizers
gcc -fsanitize=address -g program.c
./a.out
```

## Additional Resources

- [MISRA C Guidelines](https://www.misra.org.uk/)

- [CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c)

- [The C Programming Language (K&R)](https://en.wikipedia.org/wiki/The_C_Programming_Language)

- [Embedded C Best Practices](https://barrgroup.com/embedded-systems/books/embedded-c-coding-standard)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - code_cleanup/c_cleanup.md
