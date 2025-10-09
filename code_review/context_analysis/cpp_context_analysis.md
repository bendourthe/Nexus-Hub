# C++ Context Analysis

## Objective
Establish comprehensive understanding of the C++ project before conducting detailed code review. This phase gathers context about purpose, architecture, build system, dependencies, and current state to inform all subsequent review activities.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── context_analysis/
    ├── context_analysis_report.md
    ├── context_analysis_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:
- Create `review/` directory in repository root if it doesn't exist
- Create `review/context_analysis/` subdirectory for this review phase
- All reports, scripts, and data files go in the phase-specific directory

**Expected Outputs**:
- `context_analysis_report.md` - Main findings and recommendations
- `context_analysis_findings.json` - Structured data for tooling integration
- `analysis_scripts/` - Any scripts generated during analysis
- `supporting_data/` - Raw data, logs, profiling results, scan outputs

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

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Project Context Analysis

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

## Notes
- Save this context report - it will inform all subsequent review phases
- Flag any critical issues discovered during context gathering
- Update vulnerable dependencies before detailed code review
- Use this as baseline for measuring improvement over time
- Consider running sanitizers (ASan, UBSan) during context phase
~~~
