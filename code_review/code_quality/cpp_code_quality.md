# C++ Code Quality Review

## Objective
Systematically evaluate code maintainability, readability, and adherence to modern C++ best practices and the C++ Core Guidelines. Identify technical debt, complexity hotspots, and areas requiring refactoring to improve long-term codebase health.

## Output Directory Structure

All review outputs should be saved in organized directories:

```
review/
└── code_quality/
    ├── code_quality_report.md
    ├── code_quality_findings.json
    ├── analysis_scripts/
    └── supporting_data/
```

**Directory Setup**:
- Create `review/` directory in repository root if it doesn't exist
- Create `review/code_quality/` subdirectory for this review phase
- All reports, scripts, and data files go in the phase-specific directory

**Expected Outputs**:
- `code_quality_report.md` - Main findings and recommendations
- `code_quality_findings.json` - Structured data for tooling integration
- `analysis_scripts/` - Any scripts generated during analysis
- `supporting_data/` - Raw data, logs, profiling results, scan outputs

## Review Checklist

### Coding Standards
- [ ] C++ Core Guidelines compliance verified
- [ ] clang-format configuration applied consistently
- [ ] Naming conventions follow project standards
- [ ] Header guards or #pragma once usage consistent
- [ ] Include order follows convention (own, project, third-party, system)

### Modern C++ Usage
- [ ] Smart pointers used instead of raw owning pointers
- [ ] RAII principles applied consistently
- [ ] Move semantics utilized appropriately
- [ ] constexpr used for compile-time computation
- [ ] auto used appropriately (not excessively)
- [ ] Range-based for loops preferred over index-based

### Code Complexity
- [ ] Functions under 50 lines (flagged if exceeded)
- [ ] Cyclomatic complexity under 10 per function
- [ ] Nesting depth under 4 levels
- [ ] Class size reasonable (<500 lines)
- [ ] Template complexity manageable

### Design & Architecture
- [ ] SOLID principles followed
- [ ] DRY principle applied (no significant duplication)
- [ ] Separation of concerns maintained
- [ ] Appropriate use of design patterns (RAII, PIMPL, factory, etc.)
- [ ] Proper abstraction levels

### Code Smells
- [ ] Long parameter lists identified (>5 parameters)
- [ ] God classes identified
- [ ] Feature envy detected
- [ ] Raw owning pointers flagged
- [ ] Dead code marked for removal
- [ ] Macro abuse identified

### Error Handling
- [ ] Exception safety guarantees documented
- [ ] RAII used for resource management
- [ ] noexcept specified appropriately
- [ ] Error handling strategy consistent
- [ ] No resource leaks

### Maintainability
- [ ] Code self-documenting with clear names
- [ ] Comments explain "why" not "what"
- [ ] Magic numbers replaced with named constants
- [ ] Configuration externalized
- [ ] Platform-specific code isolated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# C++ Code Quality Review

Please perform a comprehensive code quality review of this C++ project following this protocol:

## Phase 1: Automated Quality Checks

1. **clang-tidy Analysis**
   ```bash
   # Run clang-tidy with common checks
   clang-tidy src/**/*.cpp -checks='*,-fuchsia-*,-google-*,-llvm-*' -- -std=c++17

   # Or use run-clang-tidy for entire project
   run-clang-tidy -checks='modernize-*,performance-*,readability-*,bugprone-*' src/

   # Generate compilation database first if needed
   cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON .
   ```

2. **cppcheck Static Analysis**
   ```bash
   # Run cppcheck with comprehensive checks
   cppcheck --enable=all --suppress=missingIncludeSystem src/ include/

   # With specific focus areas
   cppcheck --enable=warning,style,performance,portability src/
   ```

3. **clang-format Consistency Check**
   ```bash
   # Check formatting without modifying
   find src/ include/ -name "*.cpp" -o -name "*.hpp" | xargs clang-format --dry-run -Werror

   # Or with git
   git diff -U0 --no-color HEAD^ | clang-format-diff -p1
   ```

4. **C++ Core Guidelines Check**
   ```bash
   # Run clang-tidy with C++ Core Guidelines checks
   clang-tidy -checks='cppcoreguidelines-*' src/*.cpp
   ```

## Phase 2: Modern C++ Feature Review

1. **Smart Pointer Usage**
   ```cpp
   // Search for raw pointer issues
   // Bad patterns to find:
   Widget* ptr = new Widget();  // Raw owning pointer
   delete ptr;                  // Manual delete

   // Good patterns to verify:
   auto ptr = std::make_unique<Widget>();
   std::shared_ptr<Widget> shared = std::make_shared<Widget>();

   // Check for:
   - Raw new/delete usage
   - Missing RAII wrappers
   - Ownership ambiguity
   - Memory leak potential
   ```

2. **Move Semantics**
   ```cpp
   // Check for proper move semantics usage
   // Good:
   std::vector<Widget> widgets = std::move(temp_widgets);
   return std::move(local_resource);  // For move-only types

   // Check for:
   - Copy where move would be more efficient
   - Missing move constructors/assignment operators
   - Unnecessary std::move on temporaries
   - std::move on const objects (ineffective)
   ```

3. **constexpr and const Correctness**
   ```cpp
   // Verify constexpr usage for compile-time computation
   constexpr int compute() { return 42; }

   // Check for:
   - Missing const on methods that don't modify state
   - Missing constexpr on functions that could be compile-time
   - Mutable variables that should be const
   - const correctness in APIs
   ```

4. **Auto Usage**
   ```cpp
   // Check for appropriate auto usage
   // Good:
   auto it = container.begin();
   auto result = expensive_function();

   // Questionable:
   auto x = 5;  // Type obscured
   auto& y = getSomeRef();  // Unclear if reference

   // Flag:
   - Overuse obscuring types
   - Missing explicit reference/pointer indicators
   ```

5. **Range-Based For Loops**
   ```cpp
   // Prefer range-based for over index-based
   // Good:
   for (const auto& item : container) {
       process(item);
   }

   // Check for:
   - Index-based loops that could be range-based
   - Missing const in range-for loops
   - Unnecessary copies in range-for loops
   ```

## Phase 3: Complexity Analysis

1. **Function-Level Complexity**
   ```bash
   # Calculate cyclomatic complexity with lizard
   lizard -l cpp -C 10 src/

   # Or use pmccabe
   pmccabe src/**/*.cpp | sort -nr | head -20
   ```

2. **Identify Complexity Hotspots**
   - List functions with complexity >10
   - Flag functions longer than 50 lines
   - Identify deeply nested code (>4 levels)
   - Document complex conditional logic
   - Review template metaprogramming complexity

3. **Header Dependency Analysis**
   ```bash
   # Analyze header inclusion complexity
   # Use include-what-you-use
   include-what-you-use src/module.cpp

   # Check for circular dependencies
   cinclude2dot --src src/ --include include/ | dot -Tpng -o deps.png
   ```

4. **Template Complexity**
   - Assess template parameter complexity
   - Review template specialization usage
   - Check for excessive SFINAE
   - Evaluate template instantiation burden
   - Consider concepts usage (C++20)

## Phase 4: Design Quality Review

1. **RAII Compliance**
   ```cpp
   // Verify RAII for all resource management
   // Good:
   class ResourceWrapper {
       Resource* resource;
   public:
       ResourceWrapper() : resource(acquire()) {}
       ~ResourceWrapper() { release(resource); }
       ResourceWrapper(const ResourceWrapper&) = delete;
       ResourceWrapper& operator=(const ResourceWrapper&) = delete;
   };

   // Check for:
   - Resources not wrapped in RAII classes
   - Manual resource management
   - Missing destructors
   - Resource leaks in exception paths
   ```

2. **Rule of Zero/Three/Five**
   ```cpp
   // Verify adherence to Rule of Zero/Three/Five
   // Rule of Zero: Don't declare special members if you don't need to
   class SimpleClass {
       std::string name;
       std::vector<int> data;
       // Compiler-generated special members are fine
   };

   // Rule of Five: If you declare any, declare all
   class ResourceHolder {
       ~ResourceHolder();
       ResourceHolder(const ResourceHolder&);
       ResourceHolder& operator=(const ResourceHolder&);
       ResourceHolder(ResourceHolder&&) noexcept;
       ResourceHolder& operator=(ResourceHolder&&) noexcept;
   };

   // Check for:
   - Incomplete special member functions
   - Missing noexcept on move operations
   - Violation of Rule of Zero
   ```

3. **SOLID Principles**
   - **Single Responsibility**: Check if classes have one clear purpose
   - **Open/Closed**: Evaluate extensibility without modification
   - **Liskov Substitution**: Review inheritance hierarchies
   - **Interface Segregation**: Check for lean interfaces
   - **Dependency Inversion**: Assess dependency on abstractions

4. **DRY Violations**
   ```bash
   # Check for code duplication using CPD
   cpd --minimum-tokens 50 --files src/ --language cpp

   # Or use simian
   simian src/**/*.cpp
   ```
   - Identify duplicated logic
   - Find near-duplicate functions
   - Document consolidation opportunities

5. **Design Patterns**
   - Identify patterns in use (RAII, PIMPL, factory, observer, etc.)
   - Assess pattern appropriateness
   - Flag pattern misuse or over-engineering
   - Suggest beneficial pattern applications

## Phase 5: Code Smell Detection

1. **Common C++ Code Smells**
   - **Long Parameter Lists**: Functions with >5 parameters
   - **Long Methods**: Methods exceeding 50 lines
   - **Large Classes**: Classes with >500 lines or >30 methods
   - **God Objects**: Classes doing too much
   - **Feature Envy**: Methods using data from other classes excessively
   - **Shotgun Surgery**: Changes require modifications across many files

2. **C++ Specific Anti-Patterns**
   ```cpp
   // Raw owning pointers
   Widget* widget = new Widget();  // BAD

   // Manual memory management
   delete widget;  // BAD

   // C-style casts
   int x = (int)doubleValue;  // BAD - use static_cast

   // Naked new/delete
   int* array = new int[100];  // BAD - use std::vector or std::array
   delete[] array;

   // NULL instead of nullptr
   void* ptr = NULL;  // BAD - use nullptr

   // Macros over constexpr
   #define MAX_SIZE 100  // BAD - use constexpr int MAX_SIZE = 100;

   // Using namespace in headers
   using namespace std;  // BAD - especially in headers

   // Raw string manipulation
   char buffer[100];
   strcpy(buffer, str);  // BAD - use std::string

   // Ignoring return values
   func();  // If func() returns [[nodiscard]], this is an error
   ```

3. **Resource Management Issues**
   - Memory leaks
   - Double-free vulnerabilities
   - Use-after-free
   - Resource leaks (files, sockets, locks)
   - Missing exception safety

## Phase 6: Error Handling & Safety

1. **Exception Safety Review**
   ```cpp
   // Verify exception safety guarantees
   // Basic guarantee: No resource leaks, valid state
   // Strong guarantee: Operation succeeds or state unchanged
   // No-throw guarantee: Operation never throws

   // Check for:
   - Functions that should be noexcept
   - Exception specifications documented
   - RAII used for exception safety
   - Strong exception safety where needed
   - No resource leaks in exceptional paths
   ```

2. **noexcept Usage**
   ```cpp
   // Verify noexcept specifications
   // Should be noexcept:
   - Destructors
   - Move constructors
   - Move assignment operators
   - Swap functions
   - Simple accessors

   // Check for:
   - Missing noexcept where appropriate
   - Incorrect noexcept (function can actually throw)
   - noexcept(true) vs noexcept(false) usage
   ```

3. **Resource Management**
   - Verify RAII wrappers for all resources
   - Check for proper cleanup in all code paths
   - Review exception safety guarantees
   - Identify potential resource leaks

## Phase 7: Documentation Quality

1. **API Documentation**
   ```cpp
   // Check for Doxygen/documentation comments
   /**
    * @brief Brief description
    * @param param1 Description of param1
    * @param param2 Description of param2
    * @return Description of return value
    * @throws std::runtime_error if condition occurs
    */
   int function(int param1, int param2);

   // Verify:
   - Public API fully documented
   - Parameters documented
   - Return values documented
   - Exceptions documented
   - Pre/post conditions specified
   ```

2. **Comment Quality**
   - Evaluate comment necessity and clarity
   - Flag commented-out code for removal
   - Check for TODO/FIXME/HACK/XXX comments
   - Verify comments explain "why" not "what"

3. **Header Documentation**
   - Check file-level documentation
   - Verify namespace documentation
   - Review class-level documentation
   - Assess module documentation

## Phase 8: Build System Quality

1. **CMake Quality**
   ```cmake
   # Check for modern CMake practices
   # Good:
   target_compile_features(mylib PUBLIC cxx_std_17)
   target_include_directories(mylib PUBLIC include/)
   target_link_libraries(mylib PRIVATE dependency)

   # Bad:
   include_directories(include/)  # Global, not target-specific
   link_libraries(dependency)     # Global
   ```

2. **Compilation Warnings**
   ```cmake
   # Verify strict warning flags
   # GCC/Clang:
   -Wall -Wextra -Wpedantic -Werror
   -Wshadow -Wnon-virtual-dtor -Wold-style-cast
   -Wcast-align -Wunused -Woverloaded-virtual
   -Wpedantic -Wconversion -Wsign-conversion

   # MSVC:
   /W4 /WX
   ```

## Output Format

Please provide a comprehensive quality report with the following structure:

### Executive Summary
- **Overall Quality Score**: [A-F grade]
- **C++ Modernization**: [Excellent/Good/Fair/Poor]
- **Average Complexity**: [cyclomatic complexity]
- **Critical Issues**: [count]
- **Technical Debt**: [estimated hours to address]

### Coding Standards Compliance
- **clang-tidy Issues**: [count and severity]
- **cppcheck Warnings**: [count]
- **C++ Core Guidelines**: [compliance percentage]
- **Most Common Issues**:
  1. [Issue type] - [count] occurrences
  2. [Issue type] - [count] occurrences

### Modern C++ Assessment
- **Smart Pointer Usage**: [Excellent/Good/Fair/Poor]
- **RAII Compliance**: [percentage of resources using RAII]
- **Move Semantics**: [appropriate/underutilized/misused]
- **constexpr Usage**: [good/could improve/not used]
- **Legacy Patterns**: [count and locations of C++03-style code]

**Legacy Code Locations**:
| Location | Pattern | Modern Alternative | Priority |
|----------|---------|-------------------|----------|
| [file:line] | [raw new/delete] | [unique_ptr] | [High] |

### Complexity Analysis
**High Complexity Functions** (Cyclomatic Complexity >10):
| Function | File | Complexity | Lines | Recommendation |
|----------|------|------------|-------|----------------|
| [name] | [path] | [score] | [count] | [refactor suggestion] |

**Large Files/Classes** (>500 lines):
| File | Lines | Classes | Functions | Recommendation |
|------|-------|---------|-----------|----------------|
| [path] | [count] | [count] | [count] | [split suggestion] |

**Template Complexity Issues**:
| Template | Location | Issue | Recommendation |
|----------|----------|-------|----------------|
| [name] | [file:line] | [description] | [simplification] |

### Design Quality Issues
1. **SOLID Violations**:
   - [Principle]: [specific examples and impact]

2. **RAII Violations**:
   - [Location]: [resource not wrapped in RAII]
   - **Fix**: [suggested RAII wrapper]

3. **DRY Violations**:
   - [Location]: [description of duplication]
   - **Consolidation Opportunity**: [suggestion]

4. **Rule of Five/Zero Issues**:
   | Class | Issue | Fix |
   |-------|-------|-----|
   | [name] | [incomplete special members] | [what to add] |

### Code Smells Identified
| Smell Type | Location | Severity | Description | Remediation |
|------------|----------|----------|-------------|-------------|
| [type] | [file:line] | [High/Med/Low] | [details] | [suggestion] |

### C++ Specific Issues
**Raw Pointer Usage**:
| Location | Context | Risk | Modern Alternative |
|----------|---------|------|-------------------|
| [file:line] | [owning/observing] | [High/Med/Low] | [unique_ptr/raw non-owning] |

**Memory Management Issues**:
- Manual new/delete: [count and locations]
- Missing RAII wrappers: [count]
- Potential memory leaks: [locations]
- Use-after-free risks: [locations]

**Exception Safety Issues**:
- Missing noexcept: [count and locations]
- Resource leaks in exception paths: [locations]
- Incomplete exception safety: [locations]

### Error Handling Assessment
- **Exception Safety Guarantees**: [documented/undocumented]
- **noexcept Compliance**: [percentage of functions with appropriate noexcept]
- **Resource Cleanup**: [RAII-based/manual]
- **Error Propagation**: [exceptions/error codes/mixed]

### Documentation Score
- **API Documentation**: [percentage of public API documented]
- **Doxygen Coverage**: [percentage]
- **Comment Quality**: [Good/Fair/Poor]
- **Areas Needing Documentation**: [list]

### Technical Debt Summary
**Priority 1 (Critical)**: [Estimated hours]
- [Issue description and location]

**Priority 2 (High)**: [Estimated hours]
- [Issue description and location]

**Priority 3 (Medium)**: [Estimated hours]
- [Issue description and location]

**Priority 4 (Low)**: [Estimated hours]
- [Issue description and location]

### Refactoring Recommendations
1. **Immediate Actions** (within 1 sprint):
   - Replace raw pointers with smart pointers in [module]
   - Apply RAII to resource management in [component]
   - Fix Rule of Five violations in [classes]

2. **Short-term Goals** (1-2 months):
   - Reduce cyclomatic complexity in [functions]
   - Modernize C++03 patterns to C++17/20
   - Improve exception safety guarantees

3. **Long-term Initiatives** (3-6 months):
   - Refactor god classes
   - Reduce header dependencies
   - Adopt C++20 concepts/ranges

### Positive Patterns
Acknowledge what's done well:
- Excellent RAII usage in [module]
- Effective use of move semantics
- Clean template design in [component]

### Next Steps
- [ ] Address critical memory management issues
- [ ] Run clang-tidy and fix high-priority warnings
- [ ] Implement automated quality gates (clang-tidy, cppcheck)
- [ ] Plan refactoring sprints for high-priority technical debt
- [ ] Establish team C++ coding standards documentation
- [ ] Set up pre-commit hooks for formatting and linting

## Automation Recommendations
Suggest tools and configuration for continuous quality monitoring:
```yaml
# Example .clang-tidy
Checks: 'modernize-*,performance-*,readability-*,bugprone-*,cppcoreguidelines-*'
WarningsAsErrors: '*'
HeaderFilterRegex: '.*'
CheckOptions:
  - key: modernize-use-nullptr.NullMacros
    value: 'NULL'

# Example .clang-format
BasedOnStyle: LLVM
IndentWidth: 4
ColumnLimit: 100
PointerAlignment: Left

# Example pre-commit hook
repos:
  - repo: local
    hooks:
      - id: clang-format
        name: clang-format
        entry: clang-format --dry-run -Werror
        language: system
        files: \.(cpp|hpp|h)$
      - id: clang-tidy
        name: clang-tidy
        entry: clang-tidy
        language: system
        files: \.(cpp)$
```
~~~
