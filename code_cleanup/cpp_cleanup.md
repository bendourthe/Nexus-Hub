# Code Cleanup & Refactoring Review - C++

## Objective
Identify and eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions. Focus on C++-specific issues including unused code, memory management, and modern C++ patterns.

## Output Directory Structure

All cleanup outputs should be saved in organized directories:

```
cleanup/
├── cleanup_report.md
├── cleanup_history.md
├── backup/
├── scripts/
└── analysis/
```

**Directory Setup**:

- Create `cleanup/` directory in repository root if it doesn't exist

- All cleanup reports, history, backups, scripts, and analysis go in this directory

**Expected Outputs**:

- `cleanup_report.md` - Detailed report of all cleanup actions performed

- `cleanup_history.md` - Historical log of cleanup sessions with timestamps

- `backup/` - Backup copies of files before cleanup modifications

- `scripts/` - Automated cleanup scripts generated or used

- `analysis/` - Analysis data, metrics, and diagnostic outputs

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
mkdir -p cleanup/backup
mkdir -p cleanup/scripts
mkdir -p cleanup/analysis
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
