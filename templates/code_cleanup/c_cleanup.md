---
template_id: c_cleanup
template_name: Code Cleanup - C
version: 1.0.0
last_updated: 2025-12-03
language: C
category: ai-templates
phase: code_cleanup
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tools:

  - unity
  - cmocka
  - check
tags:

  - ai-templates
  - refactoring
  - c
---
# Code Cleanup & Refactoring Review - C

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on C-specific issues including unused code, memory leaks, and embedded systems best practices.

## Output Directory Structure

All outputs should be saved in organized directories:

```
cleanup/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `cleanup/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Review Checklist

### Dead Code & Drift

- [ ] Unused functions, variables, and macros identified

- [ ] Dormant feature flags, experiments, or compile-time toggles catalogued

- [ ] Deprecated APIs and interfaces mapped to replacement timeline

- [ ] Obsolete configuration values or compile flags removed

- [ ] Unreachable code paths confirmed with coverage/profiling evidence

- [ ] Unused static libraries or object files identified

### Duplication & Consolidation

- [ ] Near-duplicate functions grouped with merge candidates

- [ ] Copy-pasted logic replaced with shared functions or macros

- [ ] Repeated initialization patterns centralized

- [ ] Configuration defaults unified across modules

- [ ] DRY violations documented with recommended abstractions

- [ ] Duplicate struct definitions or typedefs consolidated

### Refactoring Readiness

- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)

- [ ] Large functions broken into manageable units

- [ ] Legacy patterns replaced with modern C equivalents

- [ ] Naming aligns with domain language and module boundaries

- [ ] Deprecation notices or migration guides drafted where needed

- [ ] Code follows consistent style (MISRA-C, CERT-C, or project standards)

### Regression Safety

- [ ] Critical behaviours covered by unit/integration tests

- [ ] Cleanup changes validated on target hardware (for embedded systems)

- [ ] Memory usage verified (stack, heap, static)

- [ ] Stakeholders notified of breaking removals

- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C Codebase Cleanup Request

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="cleanup"
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

Please perform a comprehensive, systematic cleanup of my C codebase following this protocol:

## Phase 1: Analysis & Safety Check

Before making ANY changes, please:

1. **Analyze the complete codebase structure**
   - Identify all .c and .h files in the project
   - Map dependencies between modules
   - Identify public APIs that must be preserved
   - Review build system (Makefile, CMakeLists.txt) for unused files

2. **Generate a detailed cleanup report** listing:
   - Unused #include directives
   - Unused variables, functions, and types
   - Debug printf() or logging statements
   - Empty lines within function bodies
   - Inline and meta-commentary comments
   - Dead code after returns or in unreachable branches
   - Memory leaks or missing free() calls
   - Static analysis findings (cppcheck, clang-tidy, Coverity)
   - MISRA-C or CERT-C violations
   - Estimated impact and risk level for each category

3. **Present findings and wait for my approval** before proceeding

## Phase 2: Cleanup Tasks

After I approve, systematically clean the following:

### Multi-Pass Cleanup Protocol

**CRITICAL: Perform multiple passes through the entire codebase to ensure completeness**

1. **First Pass**: Apply all cleanup tasks systematically across the codebase
   - Work through all .c and .h files in the project
   - Apply all requested cleanup operations
   - Track which files were modified

2. **Verification Pass**: Review the entire codebase again
   - Check for any files that were missed in the first pass
   - Verify all cleanup patterns were applied consistently
   - Identify any edge cases or exceptions that need attention

3. **Repeat Until Complete**: Continue additional passes if needed
   - If files were found that needed cleanup in the verification pass, perform another full pass
   - Repeat until a complete pass finds no additional cleanup opportunities
   - Track the number of passes required to achieve complete cleanup

4. **Pass Tracking**: Maintain detailed statistics for each pass
   - Number of files processed per pass
   - Number of files cleaned per pass
   - Percentage of codebase cleaned per pass
   - Types of issues found per pass

#### When to Stop Multi-Pass Cleanup

Stop when **ONE** of these conditions is met:

1. ✅ **Zero-change pass** (RECOMMENDED STOPPING POINT)
   - Entire verification pass finds nothing to clean
   - All files reviewed, no modifications made
   - This is the ideal completion state

2. ✅ **Diminishing returns threshold**
   - <5% additional files cleaned per pass
   - Calculate: `(files_cleaned_this_pass / total_files) < 0.05`
   - Example: If 150 total files and pass cleans <8 files, stop

3. ✅ **Pass limit reached**
   - Maximum 3 passes completed
   - Log incomplete work if stopping at this point
   - Document remaining issues for future cleanup

4. ✅ **Time limit reached**
   - 8 hours of cleanup time exceeded
   - Document progress and remaining work
   - Schedule follow-up cleanup session if needed

**NEVER stop without at least 2 passes (initial + verification).**

#### Progress Tracking

Create `${OUTPUT_DIR}/cleanup/progress.md` after each pass:

```markdown
# Cleanup Progress Log

## Pass 1 - Initial Cleanup
- **Date**: 2025-12-03
- **Start Time**: 10:00 AM
- **End Time**: 1:00 PM
- **Duration**: 3 hours
- **Files Analyzed**: 150
- **Files Cleaned**: 45 (30.0%)
- **Issues Found**: 234
  - Unused #includes: 67
  - Unused variables: 89
  - Empty lines: 45
  - Inline comments: 33
- **Issues Resolved**: 234 (100%)

## Pass 2 - Verification
- **Date**: 2025-12-03
- **Start Time**: 2:00 PM
- **End Time**: 3:00 PM
- **Duration**: 1 hour
- **Files Analyzed**: 150
- **Files Cleaned**: 8 (5.3%)
- **Issues Found**: 12
  - Unused #includes: 5
  - Empty lines: 7
- **Issues Resolved**: 12 (100%)

## Decision: STOP - Diminishing returns threshold met
- **Condition Met**: Files cleaned in Pass 2 (5.3%) < threshold (5%)
- **Total Passes**: 2
- **Total Time**: 4 hours
- **Total Files Cleaned**: 53/150 (35.3%)
- **Overall Status**: ✅ Cleanup complete
```

#### Multi-Pass Decision Matrix

Use this matrix to decide whether to continue or stop:

| Files Cleaned This Pass | Total Files | Percentage | Action |
|------------------------|-------------|------------|---------|
| 0 | Any | 0% | **STOP** - Zero-change pass (ideal completion) |
| 1-7 | 150 | <5% | **STOP** - Diminishing returns |
| 8-15 | 150 | 5-10% | **CONTINUE** - Still worthwhile |
| 16+ | 150 | >10% | **CONTINUE** - Significant cleanup remaining |

**Time-based stopping:**
- After 8 hours total cleanup time, **STOP** regardless of percentage
- Document remaining work for future cleanup session

**Pass-based stopping:**
- After 3 passes, **STOP** and document incomplete work
- Consider if issues are edge cases or systematic problems

### Critical Removals

- **Unused #include directives**: Remove headers not referenced in the file
  - Be cautious: some headers may be needed for type definitions
  - Check for transitive dependencies before removing

- **Unused variables**: Remove variables that are assigned but never read
  - Check for volatile variables used for hardware access

- **Unused functions**: Remove static functions that are never called
  - PRESERVE non-static functions (may be called from other modules)

- **Unused macros**: Remove #define macros that are never used

- **Unused typedef/struct**: Remove type definitions that are never used

- **Empty lines within functions**: Remove excessive blank lines inside function bodies
  - KEEP empty lines between logical code sections and between functions

### Comment Cleanup

- **Inline comments**: Remove same-line comments unless they explain complex logic

- **Meta-commentary**: Remove comments about code changes (version control handles this)

- **Commented-out code**: Remove old code blocks that are commented out

- **TODO comments**: Flag or remove stale TODO comments

- PRESERVE comments that explain:
  - Why a particular approach was chosen
  - Business logic or domain-specific rules
  - Complex algorithms or non-obvious implementations
  - Hardware-specific workarounds or timing requirements
  - Thread safety or interrupt safety considerations
  - Memory layout requirements or alignment constraints
  - Function documentation (Doxygen-style comments)

### Debugging & Development Artifacts

- **Debug print statements**: Remove printf() and fprintf(stderr, ...) used for debugging
  - PRESERVE intentional output or error messages

- **Test-only code**: Remove code marked as temporary test scaffolding

- **Debug macros**: Remove or clean up DEBUG-only code sections

### Additional Cleanup Opportunities

#### Code Quality

- **Redundant code**: Identify and consolidate duplicate functions or logic blocks

- **Dead code after returns**: Remove unreachable code after return statements

- **Unnecessary else**: Simplify if-return patterns that don't need else blocks

- **Trailing whitespace**: Remove whitespace at end of lines

- **Redundant NULL checks**: Remove checks that can never be true

- **Redundant type casts**: Remove unnecessary type casts

- **Magic numbers**: Replace with named constants or #define macros

#### Include Organization

- **Organize includes**: Sort include directives in standard order:
  1. Corresponding header file (for .c files)
  2. System headers (<stdio.h>, <stdlib.h>, etc.)
  3. Third-party library headers
  4. Project headers

- **Include guards**: Ensure all headers have proper include guards

- **Forward declarations**: Use forward declarations to reduce header dependencies

#### Memory Management

- **Memory leaks**: Ensure all malloc() has corresponding free()

- **Double free**: Check for potential double-free vulnerabilities

- **Use after free**: Identify potential use-after-free issues

- **Buffer overflows**: Review array access and strcpy/sprintf usage

- **NULL pointer checks**: Add missing NULL checks after malloc()

- **Resource cleanup**: Ensure file handles, sockets are properly closed

#### C Best Practices

- **const correctness**: Add const to function parameters and variables where appropriate

- **Static functions**: Mark internal functions as static to limit scope

- **Function prototypes**: Ensure all functions have prototypes in headers or at file top

- **Avoid global variables**: Minimize global state, prefer passing parameters

- **Error handling**: Check return values from all functions that can fail

- **Initialization**: Initialize all variables at declaration

- **Array bounds**: Ensure all array accesses are within bounds

- **String safety**: Replace strcpy/strcat with safer alternatives (strncpy, strncat, snprintf)

#### Modern C Features (C99+)

- **Inline functions**: Use inline for small, frequently-called functions (C99)

- **Variable declarations**: Declare variables closer to use point (C99)

- **Bool type**: Use stdbool.h for boolean types (C99)

- **Fixed-width integers**: Use stdint.h types (int32_t, uint8_t, etc.) (C99)

- **Compound literals**: Use for inline struct initialization (C99)

- **Designated initializers**: Use for clear struct initialization (C99)

#### Embedded Systems Considerations

- **Stack usage**: Review stack usage in embedded contexts

- **Heap usage**: Minimize or eliminate dynamic allocation in constrained environments

- **Volatile**: Ensure volatile is used for hardware registers and interrupt-shared data

- **Packed structs**: Review __attribute__((packed)) usage for hardware interfaces

- **Alignment**: Ensure proper alignment for DMA buffers and hardware access

- **Interrupt safety**: Review interrupt handler code for safety

- **Static memory**: Prefer static memory allocation over dynamic in embedded systems

#### Static Analysis Findings

- **cppcheck warnings**: Address all warnings from cppcheck

- **clang-tidy**: Fix issues reported by clang-tidy

- **Coverity**: Address findings from Coverity Scan

- **MISRA-C**: Fix MISRA-C violations (if applicable)

- **CERT-C**: Fix CERT-C secure coding violations

- **PC-lint/Flexelint**: Address findings from commercial linters

#### Build System

- **Unused source files**: Remove .c files not included in build

- **Unused libraries**: Remove libraries not linked

- **Compiler flags**: Review and clean up compiler flags

- **Dependencies**: Update dependency lists in Makefile/CMakeLists.txt

## Phase 3: Verification Protocol

After cleanup, you MUST:

1. **Provide summary** of all changes made, organized by category
2. **Highlight any edge cases** or decisions that required judgment
3. **Request that I run tests and tools** to verify nothing broke:
   ```bash
   # Build
   make clean
   make all

   # Static analysis
   cppcheck --enable=all --inconclusive .
   clang-tidy *.c

   # Run tests
   make test
   ./run_tests

   # Check for memory issues (if using Valgrind)
   valgrind --leak-check=full ./your_program

   # For embedded: verify on target hardware
   # Flash and test on actual hardware
   ```
4. **Document cleanup** in CHANGELOG.md or development log:
   ```markdown
   ### Code Cleanup - [Date]
   - Removed [X] unused includes
   - Removed [Y] unused functions
   - Fixed [Z] memory leaks
   - Removed [N] printf statements
   - Additional improvements: [summary]
   ```

## Critical Safety Rules

**DO NOT:**

- Remove any non-static functions (may be called from other modules)

- Remove function documentation comments

- Remove empty lines between functions or major code sections

- Remove comments that explain business logic or complex algorithms

- Remove constants or variables even if seemingly unused (may be used via extern)

- Remove volatile qualifiers from hardware registers or interrupt-shared data

- Remove struct packing attributes needed for hardware interfaces

- Change function signatures or public APIs

- Remove interrupt handlers or callback functions

- Make multiple sweeping changes at once - work systematically by category

**ALWAYS:**

- Work on one file at a time or in small logical groups

- Explain any removal that might be ambiguous

- Preserve code functionality - cleanup should never change behavior

- Ask for confirmation if uncertain about removing something

- Track what was removed in case rollback is needed

- Run static analysis tools after changes

- Test on target hardware for embedded systems

- Preserve backward compatibility for public APIs

- Be extremely careful with memory management changes

- Consider interrupt context and thread safety

## Output Format
Present cleanup in this structure:

- **Cleanup Report - [Category]**

- **File:** path/to/file.c

- **Removals:**
  - Line X: Unused #include <string.h>
  - Lines X-Y: Unused static function function_name()
  - Line Z: Debug printf() statement
  - Line N: Inline comment removed

- **Rationale:** [Brief explanation of why these were removed]

## Summary Statistics

- **Total files processed:** X

- **Unused includes removed:** Y

- **Unused functions removed:** Z

- **Debug statements removed:** N

- **Memory leaks fixed:** M

- **Lines removed:** L

- **Code reduction:** X%

- **Static analysis issues fixed:** P

**Overall Impact:** [Low/Medium/High risk assessment]

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/backup
mkdir -p ${OUTPUT_DIR}/scripts
mkdir -p ${OUTPUT_DIR}/analysis
```

**Save files as follows**:

- Cleanup report → `cleanup/cleanup_report.md`

- Cleanup history → `cleanup/cleanup_history.md`

- Backups → `cleanup/backup/`

- Scripts → `cleanup/scripts/`

- Analysis → `cleanup/analysis/`

## Optional Advanced Cleanup (Requires Extra Review)
If you'd like an even more thorough cleanup, also consider:

- **Function documentation**: Flag functions missing Doxygen-style comments

- **Naming convention audit**: Ensure consistent naming conventions

- **Complexity analysis**: Flag overly complex functions (cyclomatic complexity > 10)

- **Error handling review**: Ensure consistent error handling patterns

- **Thread safety review**: Review multi-threaded code for race conditions

- **Performance optimization**: Identify inefficient patterns

- **Security audit**: Review for buffer overflows, format string vulnerabilities

- **Porting considerations**: Flag non-portable code if cross-platform support is needed

- **Unit test coverage**: Ensure critical code has unit test coverage

- **API design review**: Review public API design for clarity and safety

These require more careful review and may involve refactoring beyond simple cleanup.
~~~
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
