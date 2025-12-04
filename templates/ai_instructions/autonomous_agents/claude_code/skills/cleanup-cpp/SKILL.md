---
name: cleanup-cpp
description: Remove dead code, apply modern C++ patterns, and improve memory management for maintainability
version: 1.0.0
author: Benjamin Dourthe
language: C++
category: Code Cleanup
priority: MEDIUM
tags: [cpp, c++, cleanup, refactoring, modernization, smart-pointers, raii, move-semantics]
template_source: code_cleanup/cpp_cleanup.md
---

# C++ Code Cleanup

Systematically identify and remove dead code, apply modern C++ patterns (C++17/20), and modernize memory management to maintain a lean, safe, and maintainable codebase.

## When to Use This Skill

Use this skill when you need to:
- Remove unused includes, functions, classes, and templates
- Replace raw pointers with smart pointers
- Apply RAII and move semantics
- Consolidate duplicate code
- Modernize to C++11/14/17/20 features
- Clean up debug statements and commented code
- Optimize include organization
- Address static analysis warnings

## What This Skill Does

This skill performs comprehensive C++ code cleanup:

### 1. Dead Code Detection
- **Unused #include Directives**: Identifies and removes unused headers
- **Unused Functions**: Finds static/private functions never called
- **Unused Classes**: Detects classes never instantiated
- **Unused Templates**: Finds template functions/classes never instantiated
- **Unreachable Code**: Finds code after return statements
- **Empty Blocks**: Detects empty methods or unnecessary code

### 2. Memory Management
- **Smart Pointers**: Replaces raw pointers with unique_ptr/shared_ptr
- **RAII Violations**: Ensures resources managed by RAII
- **Manual Delete**: Replaces new/delete with smart pointers
- **Memory Leaks**: Ensures proper resource cleanup
- **Move Semantics**: Ensures proper move constructors/assignment

### 3. Duplicate Code Consolidation
- **Exact Duplicates**: Finds identical code blocks
- **Near Duplicates**: Detects similar code with minor variations
- **Duplicate Logic**: Identifies functionally equivalent implementations
- **Consolidation Strategy**: Recommends refactoring approach

### 4. Modern C++ (C++11)
- **Auto Keyword**: Uses auto for complex types
- **Range-based For**: Replaces traditional loops
- **nullptr**: Replaces NULL and 0
- **Override**: Adds override to virtual functions
- **Lambdas**: Replaces functors
- **Smart Pointers**: Uses unique_ptr/shared_ptr
- **Move Semantics**: Implements move operations

### 5. Modern C++ (C++14/17/20)
- **Make Functions**: Uses make_unique/make_shared (C++14)
- **Structured Bindings**: Uses auto [a, b] = pair (C++17)
- **If/Switch Initializers**: Uses if (init; condition) (C++17)
- **Optional/Variant**: Replaces nullable pointers (C++17)
- **String View**: Uses string_view for read-only strings (C++17)
- **Filesystem**: Uses std::filesystem (C++17)
- **Concepts**: Uses concepts for templates (C++20)
- **Ranges**: Uses ranges library (C++20)
- **Three-way Comparison**: Uses operator<=> (C++20)

### 6. Debug Statement Cleanup
- **Print Statements**: Removes debug std::cout
- **Commented Code**: Cleans up old commented-out code
- **TODO Comments**: Catalogs and prioritizes TODO items

### 7. Include Organization
- **Organize Includes**: Sorts includes in standard order
- **Include Guards**: Replaces with #pragma once
- **Forward Declarations**: Uses to reduce dependencies

## Prerequisites

- C++ codebase to clean up
- Version control (git)
- Test suite (recommended)
- C++ compiler (gcc, clang, MSVC)
- CMake or Make build system

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
   mkdir build && cd build
   cmake ..
   cmake --build .
   ctest
   ```

4. **Run Static Analysis**:
   ```bash
   clang-tidy ../*.cpp
   cppcheck --enable=all ..
   ```

5. **Create Output Directory**:
   ```bash
   mkdir -p cleanup_report/{templates,assets,exports}
   ```

### Step 2: Invoke the Cleanup Skill

Tell Claude Code to use this skill:

```
"Use the cleanup-cpp skill to analyze and clean up this C++ codebase.
Focus on:
1. Removing all unused includes, functions, and classes
2. Replacing raw pointers with smart pointers
3. Applying RAII and move semantics
4. Modernizing to C++17/20 patterns
5. Consolidating duplicate code
6. Removing debug statements
7. Organizing includes properly

Save all reports to cleanup_report/ directory."
```

### Step 3: Review Cleanup Plan

Claude Code will generate a comprehensive cleanup plan including:

1. **Dead Code Candidates** - List of unused code
2. **Memory Management Issues** - Raw pointers to convert
3. **Duplication Report** - Duplicate code locations
4. **Modernization Opportunities** - Legacy patterns to update
5. **Static Analysis Findings** - clang-tidy, cppcheck warnings
6. **Risk Assessment** - Impact analysis
7. **Implementation Plan** - Ordered steps

**Review the plan before proceeding with changes!**

### Step 4: Execute Cleanup in Phases

**Phase 1: Low-Risk Cleanup**
- Remove unused includes
- Clean debug statements
- Remove commented code
- Organize includes

**Phase 2: Memory Management**
- Replace raw pointers with smart pointers
- Apply RAII patterns
- Implement move semantics
- Fix memory leaks

**Phase 3: Modernization**
- Apply auto keyword
- Use range-based for loops
- Add override/final
- Use lambdas
- Apply nullptr

**Phase 4: Advanced Modernization (C++17/20)**
- Structured bindings
- Optional/Variant
- String view
- Filesystem library
- Concepts (C++20)

**Phase 5: Structural Changes**
- Consolidate duplicates
- Remove dead functions
- Simplify complex code
- Extract constants

**Phase 6: Verification**
- Run tests after each phase
- Run sanitizers (ASan, UBSan)
- Verify no functionality changes
- Document any issues

**Phase 7: Multi-Pass Protocol**
- First pass: Apply cleanup
- Verification pass: Check for missed opportunities
- Repeat until complete
- Track statistics

### Step 5: Test After Cleanup

1. **Build**:
   ```bash
   mkdir build && cd build
   cmake -DCMAKE_BUILD_TYPE=Debug ..
   cmake --build .
   ```

2. **Run Tests**:
   ```bash
   ctest
   ```

3. **Static Analysis**:
   ```bash
   clang-tidy ../*.cpp
   cppcheck --enable=all ..
   ```

4. **Sanitizers**:
   ```bash
   cmake -DENABLE_ASAN=ON ..
   cmake --build .
   ./run_tests
   ```

5. **Memory Leaks**:
   ```bash
   valgrind --leak-check=full ./program
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
   git commit -m "Replace raw pointers with smart pointers"

   git add .
   git commit -m "Modernize to C++17 features"
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
```cpp
#include <iostream>
#include <vector>
#include <string>
#include <memory>
#include <algorithm>
#include "database.h"
#include "network.h"

class SimpleClass {
public:
    void print() { std::cout << "Hello\n"; }
};
```

**After:**
```cpp
#include <iostream>

class SimpleClass {
public:
    void print() { std::cout << "Hello\n"; }
};
```

### Category 2: Smart Pointers
**Before:**
```cpp
class DataManager {
    int* data;
public:
    DataManager() : data(new int[100]) {}

    ~DataManager() {
        delete[] data;  // Manual memory management
    }
};

void process() {
    Widget* w = new Widget();
    w->doSomething();
    delete w;  // Easy to forget or miss on exception
}
```

**After:**
```cpp
class DataManager {
    std::unique_ptr<int[]> data;
public:
    DataManager() : data(std::make_unique<int[]>(100)) {}
    // No destructor needed - RAII handles cleanup
};

void process() {
    auto w = std::make_unique<Widget>();
    w->doSomething();
    // Automatic cleanup when scope exits
}
```

### Category 3: Range-based For and Auto
**Before:**
```cpp
std::vector<std::string> names;
for (std::vector<std::string>::iterator it = names.begin();
     it != names.end(); ++it) {
    std::cout << *it << "\n";
}

std::map<std::string, int> counts;
for (std::map<std::string, int>::const_iterator it = counts.begin();
     it != counts.end(); ++it) {
    std::cout << it->first << ": " << it->second << "\n";
}
```

**After:**
```cpp
std::vector<std::string> names;
for (const auto& name : names) {
    std::cout << name << "\n";
}

std::map<std::string, int> counts;
for (const auto& [key, value] : counts) {  // C++17 structured bindings
    std::cout << key << ": " << value << "\n";
}
```

### Category 4: Lambdas
**Before:**
```cpp
class IsEven {
public:
    bool operator()(int x) const {
        return x % 2 == 0;
    }
};

void filter_evens(std::vector<int>& numbers) {
    auto it = std::remove_if(numbers.begin(), numbers.end(),
                             std::not1(IsEven()));
    numbers.erase(it, numbers.end());
}
```

**After:**
```cpp
void filter_evens(std::vector<int>& numbers) {
    auto it = std::remove_if(numbers.begin(), numbers.end(),
                             [](int x) { return x % 2 != 0; });
    numbers.erase(it, numbers.end());
}
```

### Category 5: Optional and Variant (C++17)
**Before:**
```cpp
std::string* find_user(int id) {
    // Returns nullptr if not found
    User* user = database.find(id);
    if (user) {
        return new std::string(user->name);
    }
    return nullptr;
}

void process() {
    std::string* name = find_user(42);
    if (name) {
        std::cout << *name << "\n";
        delete name;  // Easy to forget
    }
}
```

**After (C++17):**
```cpp
std::optional<std::string> find_user(int id) {
    if (auto* user = database.find(id)) {
        return user->name;
    }
    return std::nullopt;
}

void process() {
    if (auto name = find_user(42)) {
        std::cout << *name << "\n";
    }
}
```

### Category 6: String View (C++17)
**Before:**
```cpp
void process_string(const std::string& str) {
    std::cout << str.substr(0, 5);  // Creates copy
}

void use_strings() {
    std::string s = "Hello World";
    process_string(s);  // OK
    process_string("Literal");  // Creates temporary std::string
}
```

**After (C++17):**
```cpp
void process_string(std::string_view str) {
    std::cout << str.substr(0, 5);  // No copy
}

void use_strings() {
    std::string s = "Hello World";
    process_string(s);  // OK
    process_string("Literal");  // No temporary, direct view
}
```

### Category 7: Useless Variables (Qt Example)
**Before:**
```cpp
// Qt widget with ignored stylesheet
class BadProgressBar : public QProgressBar {
public:
    BadProgressBar(QWidget *parent = nullptr) : QProgressBar(parent) {
        // All these CSS properties are IGNORED by custom paintEvent
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
        painter.fillRect(rect(), QColor("#f0f0f0"));  // Hardcoded
    }
};
```

**After:**
```cpp
class GoodProgressBar : public QProgressBar {
public:
    static constexpr int BORDER_RADIUS = 12;
    static inline const QColor BORDER_COLOR{0xd0, 0xd0, 0xd0};
    static inline const QColor BACKGROUND_COLOR{0xe5, 0xe7, 0xeb};

    GoodProgressBar(QWidget *parent = nullptr) : QProgressBar(parent) {
        setStyleSheet("QProgressBar { background: transparent; }");
    }

protected:
    void paintEvent(QPaintEvent *event) override {
        QPainter painter(this);
        painter.setBrush(BACKGROUND_COLOR);
        painter.setPen(BORDER_COLOR);
        painter.drawRoundedRect(rect(), BORDER_RADIUS, BORDER_RADIUS);
    }
};
```

### Category 8: Duplicate Code Consolidation
**Before:**
```cpp
bool validateUser(const User& user) {
    if (user.name.empty()) return false;
    if (user.email.empty()) return false;
    if (user.email.find('@') == std::string::npos) return false;
    return true;
}

bool validateAdmin(const Admin& admin) {
    if (admin.name.empty()) return false;
    if (admin.email.empty()) return false;
    if (admin.email.find('@') == std::string::npos) return false;
    return true;
}
```

**After:**
```cpp
struct Account {
    std::string name;
    std::string email;
};

bool validateAccount(const Account& account) {
    if (account.name.empty()) return false;
    if (account.email.empty()) return false;
    if (account.email.find('@') == std::string::npos) return false;
    return true;
}

// User and Admin inherit from or contain Account
```

## Output Structure

```
cleanup_report/
├── templates/
│   ├── cleanup_checklist.md
│   ├── modern_cpp_guide.md
│   └── cmake_sanitizers.txt
├── assets/
│   ├── duplication_graph.png
│   ├── memory_analysis.png
│   └── complexity_heatmap.png
└── exports/
    ├── cleanup_report.md
    ├── dead_code_list.md
    ├── memory_management_issues.md
    ├── duplication_analysis.md
    ├── modernization_plan.md
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
- [ ] Raw pointers replaced with smart pointers
- [ ] RAII applied throughout
- [ ] Move semantics implemented
- [ ] Modern C++ patterns applied
- [ ] No debug statements
- [ ] No commented-out code
- [ ] All tests passing
- [ ] Sanitizers pass
- [ ] Code builds successfully
- [ ] Cleanup documented

## Tools and Libraries

### Static Analysis
- **clang-tidy**: Clang-based linter
- **cppcheck**: C++ static analyzer
- **PVS-Studio**: Commercial analyzer

### Memory Analysis
- **Valgrind**: Memory error detector
- **AddressSanitizer**: Google memory error detector
- **UndefinedBehaviorSanitizer**: UB detector
- **ThreadSanitizer**: Race condition detector

```bash
# Install tools
sudo apt-get install clang-tidy cppcheck valgrind

# Run analysis
clang-tidy *.cpp -checks='*'
cppcheck --enable=all .

# Compile with sanitizers
cmake -DCMAKE_CXX_FLAGS="-fsanitize=address -g" ..
cmake --build .
./program
```

## Additional Resources

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
- [Effective Modern C++ by Scott Meyers](https://www.oreilly.com/library/view/effective-modern-c/9781491908419/)
- [Modern C++ Design](https://en.wikipedia.org/wiki/Modern_C%2B%2B_Design)
- [cppreference.com](https://en.cppreference.com/)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: ai_templates v0.2.5 - code_cleanup/cpp_cleanup.md
