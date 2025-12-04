---
template_id: cpp_cleanup
template_name: Code Cleanup - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: ai-templates
phase: code_cleanup
difficulty: intermediate
estimated_time_hours: 2-4
prerequisites: []
tools:
  - google test
  - catch2
  - boost.test
tags:
  - ai-templates
  - refactoring
  - cpp
---
# Code Cleanup & Refactoring Review - C++

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on C++-specific issues including unused code, memory management, and modern C++ patterns.

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

- [ ] Unused classes, functions, and variables identified

- [ ] Dormant feature flags, experiments, or compile-time toggles catalogued

- [ ] Deprecated APIs and interfaces mapped to replacement timeline

- [ ] Obsolete configuration values or compile flags removed

- [ ] Unreachable code paths confirmed with coverage/profiling evidence

- [ ] Unused static libraries or object files identified

### Duplication & Consolidation

- [ ] Near-duplicate classes or functions grouped with merge candidates

- [ ] Copy-pasted logic replaced with shared utilities or templates

- [ ] Repeated initialization patterns centralized

- [ ] Configuration defaults unified across modules

- [ ] DRY violations documented with recommended abstractions

- [ ] Duplicate class definitions or template specializations consolidated

### Refactoring Readiness

- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)

- [ ] Large functions/classes broken into manageable units

- [ ] Legacy patterns replaced with modern C++ equivalents

- [ ] Naming aligns with domain language and architecture boundaries

- [ ] Deprecation notices or migration guides drafted where needed

- [ ] Code follows consistent style (Google Style, LLVM, or project standards)

### Regression Safety

- [ ] Critical behaviours covered by unit/integration tests

- [ ] Cleanup changes validated with sanitizers (ASan, UBSan, TSan)

- [ ] Memory usage verified

- [ ] Stakeholders notified of breaking removals

- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Codebase Cleanup Request

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

Please perform a comprehensive, systematic cleanup of my C++ codebase following this protocol:

## Phase 1: Analysis & Safety Check

Before making ANY changes, please:

1. **Analyze the complete codebase structure**
   - Identify all .cpp, .cc, .cxx, .h, .hpp files in the project
   - Map dependencies between modules and namespaces
   - Identify public APIs that must be preserved
   - Review build system (CMakeLists.txt, Makefile) for unused files

2. **Generate a detailed cleanup report** listing:
   - Unused #include directives
   - Unused variables, functions, classes, and templates
   - Debug std::cout or logging statements
   - Empty lines within function bodies
   - Inline and meta-commentary comments
   - Dead code after returns or in unreachable branches
   - Memory leaks or RAII violations
   - Static analysis findings (clang-tidy, cppcheck, PVS-Studio)
   - Raw pointers that could use smart pointers
   - Estimated impact and risk level for each category

3. **Present findings and wait for my approval** before proceeding

## Phase 2: Cleanup Tasks

After I approve, systematically clean the following:

### Multi-Pass Cleanup Protocol

**CRITICAL: Perform multiple passes through the entire codebase to ensure completeness**

1. **First Pass**: Apply all cleanup tasks systematically across the codebase
   - Work through all .cpp, .cc, .cxx, .h, .hpp files in the project
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
  - Be cautious: some headers may be needed for template instantiation
  - Check for transitive dependencies before removing

- **Unused variables**: Remove variables that are assigned but never read

- **Unused functions**: Remove static/private functions that are never called
  - PRESERVE public functions (may be called from other modules)

- **Unused classes**: Remove private/internal classes that are never instantiated

- **Unused templates**: Remove template functions/classes that are never instantiated

- **Unused namespaces**: Remove namespace definitions that are empty or unused

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
  - Thread safety or exception safety considerations
  - Template specialization rationale
  - Performance considerations or optimization notes
  - Function/class documentation (Doxygen-style comments)

### Debugging & Development Artifacts

- **Debug output**: Remove std::cout, std::cerr, printf() used for debugging
  - PRESERVE intentional output or error messages

- **Test-only code**: Remove code marked as temporary test scaffolding

- **Debug macros**: Remove or clean up DEBUG-only code sections

### Additional Cleanup Opportunities

#### Code Quality

- **Redundant code**: Identify and consolidate duplicate functions or logic blocks

- **Dead code after returns**: Remove unreachable code after return statements

- **Unnecessary else**: Simplify if-return patterns that don't need else blocks

- **Trailing whitespace**: Remove whitespace at end of lines

- **Redundant nullptr checks**: Remove checks that can never be true

- **Redundant type casts**: Remove unnecessary static_cast or C-style casts

- **Magic numbers**: Replace with named constants or constexpr

#### Include Organization

- **Organize includes**: Sort include directives in standard order:
  1. Corresponding header file (for .cpp files)
  2. C++ standard library headers (<vector>, <string>, etc.)
  3. C standard library headers (<cstdio>, <cstring>, etc.)
  4. Third-party library headers
  5. Project headers

- **Include guards**: Replace include guards with #pragma once where appropriate

- **Forward declarations**: Use forward declarations to reduce header dependencies

- **Minimize includes in headers**: Move includes to .cpp files where possible

#### Memory Management

- **Smart pointers**: Replace raw pointers with std::unique_ptr or std::shared_ptr

- **RAII violations**: Ensure resources are managed by RAII objects

- **Manual delete**: Replace manual new/delete with smart pointers or containers

- **Memory leaks**: Ensure proper resource cleanup

- **Double delete**: Check for potential double-delete vulnerabilities

- **Move semantics**: Ensure proper move constructors and move assignment operators

#### Modern C++ Practices (C++11)

- **Auto keyword**: Use auto for complex types where it improves readability

- **Range-based for**: Replace traditional loops with range-based for where appropriate

- **nullptr**: Replace NULL and 0 with nullptr

- **Override**: Add override keyword to virtual function overrides

- **Final**: Add final to classes and functions that shouldn't be inherited/overridden

- **Default/delete**: Use = default and = delete for special member functions

- **Uniform initialization**: Use brace initialization {} consistently

- **Lambdas**: Replace functors with lambdas where appropriate

- **Smart pointers**: Use std::unique_ptr and std::shared_ptr

- **Move semantics**: Implement move constructors and assignment operators

#### Modern C++ Practices (C++14)

- **Make functions**: Use std::make_unique and std::make_shared

- **Return type deduction**: Use auto return types where appropriate

- **Generic lambdas**: Use auto parameters in lambdas

- **Binary literals**: Use 0b prefix for binary literals

- **Digit separators**: Use ' for readability in numeric literals

#### Modern C++ Practices (C++17)

- **Structured bindings**: Use auto [a, b] = pair instead of std::tie

- **If/switch with initializers**: Use if (init; condition) pattern

- **std::optional**: Replace nullable pointers with std::optional

- **std::variant**: Replace unions with std::variant

- **std::string_view**: Replace const std::string& with std::string_view for read-only strings

- **Filesystem library**: Use std::filesystem for file operations

- **Inline variables**: Use inline for variables in headers (C++17)

- **Fold expressions**: Simplify variadic template operations

#### Modern C++ Practices (C++20)

- **Concepts**: Use concepts to constrain templates

- **Ranges**: Use ranges library for more expressive algorithms

- **Coroutines**: Consider coroutines for async operations

- **Three-way comparison**: Implement operator<=> for comparison

- **Modules**: Consider migrating to modules (if supported)

- **constexpr improvements**: Use more constexpr for compile-time computation

#### Code Style & Best Practices

- **Const correctness**: Add const to methods and parameters where appropriate

- **Member initialization**: Use member initializer lists in constructors

- **Explicit constructors**: Mark single-argument constructors as explicit

- **Virtual destructors**: Ensure base classes have virtual destructors

- **Rule of Five/Zero**: Follow rule of five (or zero) for special member functions

- **Namespace usage**: Avoid using namespace in headers

- **STL algorithms**: Replace manual loops with STL algorithms where clearer

- **Exception safety**: Ensure code provides proper exception guarantees

#### Static Analysis Findings

- **clang-tidy warnings**: Address all warnings from clang-tidy

- **cppcheck**: Fix issues reported by cppcheck

- **PVS-Studio**: Address findings from PVS-Studio

- **Clang Static Analyzer**: Fix issues from static analyzer

- **Address Sanitizer**: Fix issues found by ASan

- **Undefined Behavior Sanitizer**: Fix issues found by UBSan

- **Thread Sanitizer**: Fix race conditions found by TSan

#### Build System

- **Unused source files**: Remove .cpp files not included in build

- **Unused libraries**: Remove libraries not linked

- **Compiler flags**: Review and clean up compiler flags

- **Dependencies**: Update dependency lists in CMakeLists.txt

#### Useless Variables and Properties

Identify and remove variables, properties, and configuration that serve no functional purpose:

- **Ignored Style Properties**: In custom-painted Qt widgets
  - Properties defined in QSS/stylesheets that are completely ignored by custom paintEvent()
  - Style settings overridden by manual QPainter drawing
  - Widget properties that have no effect due to custom rendering

- **Dead Configuration Values**: Settings that are defined but never used
  - Unused member variables in classes
  - Configuration structs with unused fields
  - Constants that are never referenced

- **Redundant Constants**: Values that duplicate other constants
  - Multiple constexpr with identical values
  - Constants that duplicate framework defaults

**Detection Example: Qt Custom Widget**

```cpp
// BEFORE - Useless stylesheet properties
class BadProgressBar : public QProgressBar {
public:
    BadProgressBar(QWidget *parent = nullptr) : QProgressBar(parent) {
        // ❌ All these CSS properties are IGNORED by custom paintEvent
        setStyleSheet(R"(
            QProgressBar {
                border: 1px solid #d0d0d0;      /* IGNORED */
                border-radius: 12px;             /* IGNORED */
                background-color: #e5e7eb;       /* IGNORED */
            }
        )");
    }

protected:
    void paintEvent(QPaintEvent *event) override {
        QPainter painter(this);
        // Custom painting bypasses stylesheet completely
        painter.fillRect(rect(), QColor("#f0f0f0"));
    }
};

// AFTER - Using constants
class GoodProgressBar : public QProgressBar {
public:
    // ✅ Visual properties as clear class constants
    static constexpr int BORDER_RADIUS = 12;
    static inline const QColor BORDER_COLOR{0xd0, 0xd0, 0xd0};
    static inline const QColor BACKGROUND_COLOR{0xe5, 0xe7, 0xeb};

    GoodProgressBar(QWidget *parent = nullptr) : QProgressBar(parent) {
        // Only non-visual stylesheet properties
        setStyleSheet("QProgressBar { background: transparent; }");
    }

protected:
    void paintEvent(QPaintEvent *event) override {
        QPainter painter(this);
        // Use the constants in actual drawing code
        painter.setBrush(BACKGROUND_COLOR);
        painter.setPen(BORDER_COLOR);
        painter.drawRoundedRect(rect(), BORDER_RADIUS, BORDER_RADIUS);
    }
};
```

**Why This Matters:**
1. **Clarity**: Visual config is at class top, easy to find
2. **Maintainability**: Constants are easy to modify
3. **Compile-time**: constexpr enables compile-time optimization
4. **IDE Support**: Better autocomplete and refactoring

**Detection Strategy:**
1. Find classes that override paintEvent(), paint(), or render()
2. Check for setStyleSheet() or Qt property setters
3. Verify those properties are used in paint method
4. Extract values to static constexpr, remove useless stylesheet
5. Add comment explaining minimal stylesheet

## Phase 3: Verification Protocol

After cleanup, you MUST:

1. **Provide summary** of all changes made, organized by category
2. **Highlight any edge cases** or decisions that required judgment
3. **Request that I run tests and tools** to verify nothing broke:
   ```bash
   # Build
   mkdir build && cd build
   cmake -DCMAKE_BUILD_TYPE=Debug ..
   cmake --build .

   # Static analysis
   clang-tidy ../*.cpp -checks='*'
   cppcheck --enable=all --inconclusive ..

   # Run tests
   ctest
   ./run_tests

   # Sanitizers
   cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_ASAN=ON ..
   cmake --build .
   ./run_tests

   # Memory leaks (if using Valgrind)
   valgrind --leak-check=full ./your_program
   ```
4. **Document cleanup** in CHANGELOG.md or development log:
   ```markdown
   ### Code Cleanup - [Date]
   - Removed [X] unused includes
   - Removed [Y] unused functions
   - Fixed [Z] memory leaks
   - Modernized [N] legacy patterns
   - Additional improvements: [summary]
   ```

## Critical Safety Rules

**DO NOT:**

- Remove any public functions, classes, or templates (may be used externally)

- Remove function/class documentation comments

- Remove empty lines between functions or major code sections

- Remove comments that explain business logic or complex algorithms

- Remove constants or variables even if seemingly unused (may be used via extern)

- Remove virtual destructors from base classes

- Change function signatures or public APIs

- Remove explicit template instantiations that may be needed

- Make multiple sweeping changes at once - work systematically by category

**ALWAYS:**

- Work on one file at a time or in small logical groups

- Explain any removal that might be ambiguous

- Preserve code functionality - cleanup should never change behavior

- Ask for confirmation if uncertain about removing something

- Track what was removed in case rollback is needed

- Run static analysis tools after changes

- Test with sanitizers (ASan, UBSan, TSan)

- Preserve backward compatibility for public APIs

- Be extremely careful with memory management changes

- Consider template instantiation in other translation units

- Maintain exception safety guarantees

## Output Format
Present cleanup in this structure:

- **Cleanup Report - [Category]**

- **File:** path/to/file.cpp

- **Removals:**
  - Line X: Unused #include <string>
  - Lines X-Y: Unused function functionName()
  - Line Z: Debug std::cout statement
  - Line N: Inline comment removed

- **Rationale:** [Brief explanation of why these were removed]

## Summary Statistics

- **Total files processed:** X

- **Unused includes removed:** Y

- **Unused functions removed:** Z

- **Debug statements removed:** N

- **Raw pointers converted:** M

- **Lines removed:** L

- **Code reduction:** X%

- **Modernization changes:** P

- **Static analysis issues fixed:** Q

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

- **Documentation**: Flag functions/classes missing Doxygen-style comments

- **Naming convention audit**: Ensure consistent naming conventions

- **Complexity analysis**: Flag overly complex functions (cyclomatic complexity > 10)

- **Exception safety review**: Ensure proper exception safety guarantees

- **Thread safety review**: Review multi-threaded code for race conditions

- **Performance optimization**: Identify inefficient patterns (unnecessary copies, etc.)

- **API design review**: Review public API design for clarity and safety

- **Template metaprogramming**: Review template code for clarity and compile times

- **ABI compatibility**: Review changes for ABI impact if maintaining binary compatibility

- **Move semantics**: Ensure all types properly support move operations

- **constexpr opportunities**: Identify functions that could be constexpr

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
