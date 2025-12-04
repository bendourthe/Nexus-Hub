---
template_id: cpp_context_analysis
template_name: Context Analysis - Cpp
version: 1.0.0
last_updated: 2025-12-03
language: Cpp
category: code_review
phase: context_analysis
phase_number: 1
difficulty: intermediate
estimated_time_hours: 2-3
prerequisites: []
related_templates:
  - code_review/code_quality/cpp_code_quality.md
tools:
  - google test
  - catch2
  - boost.test
tags:
  - code-review
  - cpp
---
# C++ Context Analysis

## Objective
Establish comprehensive understanding of the C++ project before conducting detailed code review. This phase gathers context about purpose, architecture, build system, dependencies, and current state to inform all subsequent review activities.

## Output Directory Structure

All outputs should be saved in organized directories:

```
review/context_analysis/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `review/context_analysis/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Analysis Checklist

### Project Understanding

- [ ] Project purpose and target audience identified

- [ ] Core features and use cases documented

- [ ] Development stage assessed (prototype, production, legacy)

- [ ] Key stakeholders and maintainers identified

- [ ] Project documentation reviewed (README, docs/, wiki)

### Architecture & Structure

- [ ] Entry points and main modules mapped

- [ ] Header/source organization evaluated

- [ ] Design patterns identified (RAII, PIMPL, factory, singleton, etc.)

- [ ] Configuration management approach documented

- [ ] Build configuration and variants catalogued

### Build System Analysis

- [ ] Build system identified (CMake, Meson, Bazel, Make, etc.)

- [ ] Build configurations documented (Debug, Release, RelWithDebInfo)

- [ ] Compiler versions and flags reviewed

- [ ] Platform targets identified (Windows, Linux, macOS, embedded)

- [ ] Build dependencies and toolchain requirements documented

### Dependency Analysis

- [ ] Direct dependencies listed with versions

- [ ] Dependency manager identified (vcpkg, Conan, system packages, git submodules)

- [ ] Header-only libraries documented

- [ ] Outdated packages identified

- [ ] License compatibility verified

### C++ Standard & Features

- [ ] C++ standard version identified (C++11, C++14, C++17, C++20, C++23)

- [ ] Compiler compatibility requirements documented

- [ ] Modern C++ feature adoption assessed

- [ ] Legacy code patterns identified

- [ ] Platform-specific code isolated

### Codebase Metrics

- [ ] Lines of code measured (total, per module)

- [ ] Cyclomatic complexity assessed

- [ ] Module coupling and cohesion evaluated

- [ ] Header dependencies analyzed

- [ ] Comment density analyzed

## Severity Classification

Use this framework to classify and prioritize all findings from the code review.

### CRITICAL (Fix Immediately)

**Definition:** Issues that create immediate risks to system stability, data integrity, or compliance.

**Examples:**
- Security vulnerabilities (SQL injection, XSS, authentication bypass)
- Resource leaks (unclosed connections, file handles, memory leaks)
- Data loss risks (destructive operations without validation)
- Thread safety violations (race conditions, deadlocks)
- Compliance violations (GDPR, HIPAA, PCI-DSS)

**Action Required:**
- Block deployment until fixed
- Require hotfix within 24 hours
- Add tests to prevent regression
- Document root cause and fix

---

### HIGH (Fix Before Next Release)

**Definition:** Issues that significantly impact maintainability, performance, or correctness but don't cause immediate failures.

**Examples:**
- Incorrect business logic (wrong calculations, flawed algorithms)
- Performance bottlenecks (O(n²) algorithms, missing indexes, inefficient queries)
- Memory inefficiency (loading large datasets into memory unnecessarily)
- Breaking API changes without deprecation
- Missing critical error handling (network errors, API failures not caught)

**Action Required:**
- Schedule fix in current sprint
- Cannot release without resolution
- Update documentation
- Performance test after fix

---

### MEDIUM (Fix in Next Cycle)

**Definition:** Code smells and technical debt that reduce maintainability but don't affect correctness.

**Examples:**
- High complexity (cyclomatic complexity >10, functions >100 lines)
- Code duplication (>10 lines duplicated across modules)
- Poor naming (unclear variable/function names, inconsistent conventions)
- Missing tests (<80% coverage on critical paths)
- Incomplete error messages (no context for debugging)

**Action Required:**
- Add to backlog
- Prioritize in next sprint planning
- Consider during refactoring opportunities
- Track technical debt metrics

---

### LOW (Nice to Have)

**Definition:** Style inconsistencies and minor optimizations that don't impact functionality.

**Examples:**
- Style violations (linting warnings, formatting issues)
- Minor performance optimizations (in non-critical code paths)
- Missing documentation on helper functions
- Verbose code that could be more concise
- Debug statements left in code

**Action Required:**
- Fix opportunistically during other work
- Batch with other low-priority changes
- Good for new contributors
- Can be deferred indefinitely

---

## Severity Assignment Guidelines

**When to Escalate Severity:**
- Issue affects **production environment** → escalate one level
- Issue affects **customer-facing features** → escalate one level
- Issue has **no workaround** → escalate one level
- Issue appears in **multiple locations** → escalate one level

**When to De-escalate Severity:**
- Issue only in **test/development code** → de-escalate one level
- Issue has **easy workaround** → de-escalate one level
- Issue is **isolated to single module** → de-escalate one level
- Issue **rarely executed** (edge case) → de-escalate one level

**Examples:**
- Memory leak in production API: **HIGH → CRITICAL** (production + customer-facing)
- Style violation in test file: **LOW → Ignore** (test code + style only)
- Duplicated logic across 15 modules: **MEDIUM → HIGH** (multiple locations)

---

## Reporting Format

For each finding, include:

**1. Severity Level:** [CRITICAL/HIGH/MEDIUM/LOW]

**2. Location:** File path and line numbers

**3. Issue Description:** What's wrong and why it matters

**4. Impact:** Specific consequences of not fixing

**5. Recommendation:** How to fix (with code example if applicable)

**6. Effort Estimate:** Time to fix (hours/days)

**Example Finding:**
```markdown
### HIGH: Performance Bottleneck in User Search

**Location:** `src/services/userService:145-167`

**Issue:** The user search function loads all users into memory and performs linear search on every request.

**Impact:**
- Response time degrades with user count (currently 500ms for 10k users)
- High memory usage (50MB+ per request)
- Poor scalability (can't handle >100k users)

**Recommendation:**
Move filtering to database with indexed query:
- Add database index on search fields
- Use database LIKE/ILIKE queries
- Implement pagination (limit results to 50)
- Add caching for common searches

**Effort:** 3 hours (2 hours implementation + 1 hour testing)

**Priority:** Must fix before next release (performance SLA violation)
```

---


## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Project Context Analysis

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="review/context_analysis"
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

## Analysis Protocol

Please perform a comprehensive context analysis of this C++ project following this protocol:

## Phase 1: Project Discovery

1. **Identify Project Fundamentals**
   - Read and summarize README.md and primary documentation
   - Determine project purpose, target audience, and key features
   - Identify development stage (prototype/production/legacy)
   - List primary maintainers and stakeholders

2. **Map Repository Structure**
   - Identify source directories (src/, lib/, include/, etc.)
   - Locate header directories (public vs private headers)
   - Find test directories and test frameworks used
   - Document build configuration files (CMakeLists.txt, Makefile, meson.build, etc.)
   - Locate documentation (docs/, Doxygen configs, external)

## Phase 2: Build System Understanding

1. **Build System Analysis**
   ```bash
   # For CMake projects
   # Identify CMake version requirement
   grep -i "cmake_minimum_required" CMakeLists.txt

   # Find build targets
   grep -E "add_(executable|library)" CMakeLists.txt

   # For Conan dependencies
   cat conanfile.txt
   # or
   cat conanfile.py

   # For vcpkg dependencies
   cat vcpkg.json
   ```

2. **Compiler & Toolchain**
   - Identify supported compilers (GCC, Clang, MSVC, Intel)
   - Document compiler version requirements
   - Review compiler flags and warnings
   - Identify platform-specific requirements
   - Check for cross-compilation support

3. **Build Configurations**
   - Debug configuration settings
   - Release configuration optimizations
   - RelWithDebInfo settings
   - Custom build types
   - Sanitizer builds (ASan, TSan, UBSan, MSan)

## Phase 3: Architecture Understanding

1. **Entry Points & Core Modules**
   - Identify main entry points (main.cpp, library exports)
   - Map core business logic modules
   - Document public API surface
   - Identify internal vs external interfaces
   - Review namespace organization

2. **Design Patterns & Architecture**
   - Identify architectural style (monolithic, modular, plugin-based)
   - Document design patterns in use (RAII, PIMPL, factory, observer, etc.)
   - Map data flow through the application
   - Identify configuration management approach
   - Review error handling strategy

3. **Module Dependencies**
   - Create dependency graph between modules
   - Identify circular dependencies (header and link-time)
   - Assess module coupling (tight/loose)
   - Evaluate separation of concerns
   - Review header inclusion patterns

4. **Memory Management Strategy**
   - Identify smart pointer usage (unique_ptr, shared_ptr, weak_ptr)
   - Review raw pointer usage patterns
   - Check for custom allocators
   - Assess RAII adherence
   - Identify manual memory management

## Phase 4: Dependency Analysis

1. **Dependency Inventory**
   ```bash
   # For vcpkg
   vcpkg list

   # For Conan
   conan search "*" --remote=all

   # For system packages
   # Check CMakeLists.txt for find_package() calls
   grep "find_package" CMakeLists.txt

   # For git submodules
   git submodule status
   ```

2. **Dependency Categories**
   - Standard library version (C++11/14/17/20/23)
   - Boost libraries (and which modules)
   - System libraries (pthread, dl, etc.)
   - Third-party libraries
   - Header-only libraries
   - Test frameworks (GoogleTest, Catch2, Doctest)

3. **Dependency Health Check**
   - Check for outdated dependencies
   - Identify deprecated libraries
   - Review license compatibility
   - Assess security vulnerabilities (CVEs)
   - Check for unmaintained packages

## Phase 5: C++ Standard & Features

1. **Standard Version Assessment**
   ```cpp
   // Check for C++ standard requirements
   // In CMakeLists.txt:
   // set(CMAKE_CXX_STANDARD 17)
   // target_compile_features(target PUBLIC cxx_std_17)
   ```

2. **Modern C++ Feature Adoption**
   - Auto type deduction usage
   - Range-based for loops
   - Lambda expressions
   - Move semantics and rvalue references
   - Smart pointers (unique_ptr, shared_ptr)
   - constexpr usage
   - std::optional, std::variant, std::any
   - Structured bindings (C++17)
   - Concepts (C++20)
   - Coroutines (C++20)
   - Ranges (C++20)
   - Modules (C++20)

3. **Legacy Code Identification**
   - Raw pointer usage (new/delete)
   - Manual memory management
   - C-style arrays
   - Null pointer issues (NULL vs nullptr)
   - C-style casts
   - Raw owning pointers
   - Macros over constexpr/templates

## Phase 6: Testing & Quality Infrastructure

1. **Test Framework**
   - Identify testing framework (GoogleTest, Catch2, Doctest, Boost.Test)
   - Document test execution approach
   - Review test configuration files
   - Assess test organization and structure

2. **Static Analysis**
   ```bash
   # Check for static analysis configuration
   # clang-tidy
   cat .clang-tidy

   # cppcheck configuration
   cat cppcheck.cfg

   # clang-format
   cat .clang-format
   ```

3. **CI/CD Pipeline**
   - Locate CI/CD configuration (.github/workflows, .gitlab-ci.yml, etc.)
   - Document automated checks (linting, testing, sanitizers)
   - Review deployment automation
   - Identify quality gates and merge requirements

4. **Code Coverage**
   - Check for coverage tools (gcov, lcov, llvm-cov)
   - Review coverage configuration
   - Identify coverage reporting setup

## Phase 7: Codebase Metrics

1. **Size & Complexity Metrics**
   ```bash
   # Lines of code (excluding tests)
   find src/ -name "*.cpp" -o -name "*.hpp" | xargs wc -l

   # Count header files
   find include/ -name "*.h" -o -name "*.hpp" | wc -l

   # Cyclomatic complexity (using lizard or pmccabe)
   lizard src/ -l cpp
   ```

2. **Quality Indicators**
   - Calculate code-to-comment ratio
   - Measure average function/method length
   - Identify large files (>1000 lines)
   - Count TODO/FIXME/HACK/XXX comments
   - Assess header inclusion complexity

3. **Compilation Metrics**
   - Measure clean build time
   - Assess incremental build performance
   - Identify slow-to-compile headers
   - Review precompiled header usage

## Phase 8: Documentation Review

1. **Code Documentation**
   - Assess API documentation coverage (Doxygen, Sphinx)
   - Review comment format and consistency
   - Check header documentation completeness
   - Evaluate inline comment quality
   - Review namespace/module documentation

2. **Project Documentation**
   - Review README completeness
   - Check for CONTRIBUTING.md
   - Assess CHANGELOG.md or release notes
   - Review architecture documentation
   - Check build instructions

## Output Format

Please provide a comprehensive context report with the following structure:

### Executive Summary

- **Project Name**: [name]

- **Purpose**: [1-2 sentence description]

- **Stage**: [prototype/production/legacy]

- **C++ Standard**: [C++11/14/17/20/23]

- **Build System**: [CMake/Meson/Bazel/Make]

- **Architecture**: [architectural style]

### Project Structure
```
project/
├── include/              # Public headers
├── src/                  # Implementation files
├── lib/                  # Internal libraries
├── tests/                # Test suite
├── docs/                 # Documentation
├── cmake/                # CMake modules
├── CMakeLists.txt        # Build configuration
├── conanfile.txt         # Conan dependencies
├── vcpkg.json            # vcpkg dependencies
├── .clang-format         # Code formatting
├── .clang-tidy           # Static analysis
└── README.md
```

### Build System Overview

- **Build Tool**: [CMake version, Meson version, etc.]

- **Dependency Manager**: [vcpkg, Conan, system packages, submodules]

- **Compiler Support**: [GCC 9+, Clang 10+, MSVC 2019+, etc.]

- **Platform Targets**: [Linux, Windows, macOS, embedded]

- **Build Configurations**: [Debug, Release, custom]

### Architecture Overview

- **Design Patterns**: [RAII, PIMPL, factory, singleton, observer, etc.]

- **Module Organization**: [brief description]

- **Memory Management**: [smart pointers, RAII, custom allocators]

- **Error Handling**: [exceptions, error codes, std::expected]

- **Key Dependencies**: [critical external libraries]

- **Configuration Approach**: [how settings are managed]

### C++ Standard & Features

- **Standard Version**: [C++17, C++20, etc.]

- **Modern Features Used**: [list of C++11/14/17/20 features]

- **Legacy Patterns**: [areas using older C++ patterns]

- **Compiler Extensions**: [GCC-specific, MSVC-specific, etc.]

- **Platform Abstractions**: [cross-platform strategy]

### Dependency Summary
| Package | Version | Purpose | Manager | Status | License |
|---------|---------|---------|---------|--------|---------|
| [name] | [version] | [usage] | [vcpkg/Conan] | [current/outdated] | [license] |

### Testing Infrastructure

- **Test Framework**: [GoogleTest, Catch2, Doctest]

- **Test Organization**: [unit, integration, e2e]

- **Coverage Tools**: [gcov, lcov, llvm-cov]

- **Sanitizers**: [ASan, TSan, UBSan, MSan]

- **CI/CD**: [platform and key workflows]

### Codebase Metrics

- **Total Lines**: [number] (excluding tests)

- **Source Files**: [.cpp count]

- **Header Files**: [.h/.hpp count]

- **Average Complexity**: [cyclomatic complexity score]

- **Documentation**: [Doxygen coverage %]

- **Build Time**: [clean build duration]

### Key Findings
1. **Strengths**: [positive observations]
   - Modern C++ features adoption
   - Good RAII usage
   - Comprehensive testing

2. **Concerns**: [potential issues to investigate]
   - Memory management patterns
   - Header dependency complexity
   - Build system issues

3. **Dependencies**: [outdated or vulnerable packages]

4. **Documentation**: [gaps or areas needing improvement]

### Recommendations for Review Focus
Based on this context, the following review areas should be prioritized:
1. **Memory Safety** - [reason based on findings]
2. **Performance** - [reason based on findings]
3. **Code Quality** - [reason based on findings]
4. **Testing** - [reason based on findings]

### Next Steps

- [ ] Proceed with code quality review

- [ ] Conduct security audit (memory safety, sanitizers)

- [ ] Perform performance analysis

- [ ] Review test coverage and quality

- [ ] Analyze build system optimization opportunities

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p ${OUTPUT_DIR}/context_analysis/analysis_scripts
mkdir -p ${OUTPUT_DIR}/context_analysis/supporting_data
```

**Save files as follows**:

- Main report → `review/context_analysis/context_analysis_report.md`

- Findings data → `review/context_analysis/context_analysis_findings.json`

- Analysis scripts → `review/context_analysis/analysis_scripts/`

- Supporting data → `review/context_analysis/supporting_data/`

## Notes

- Save this context report - it will inform all subsequent review phases

- Flag any critical issues discovered during context gathering

- Update vulnerable dependencies before detailed code review

- Use this as baseline for measuring improvement over time

- Consider running sanitizers (ASan, UBSan) during context phase
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
