# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: C++17/C++20/C++23
- **Compiler**: GCC 12+ / Clang 15+ / MSVC 2022
- **Build System**: CMake 3.20+
- **Package Manager**: vcpkg / Conan
- **Testing**: Google Test / Catch2 / doctest
- **Code Quality**: clang-tidy, cppcheck, sanitizers
- **Documentation**: Doxygen

## Project Structure
```
project-name/
├── src/                              - Source files
│   ├── main.cpp                      - Main entry point
│   ├── core/                         - Core application logic
│   │   ├── module.cpp
│   │   └── module.hpp
│   └── utils/                        - Utility classes
│       ├── utils.cpp
│       └── utils.hpp
├── include/                          - Public headers
│   └── project/
│       └── api.hpp                   - Public API
├── tests/                            - Test files
│   ├── main_test.cpp                 - Test main
│   ├── module_test.cpp               - Module tests
│   └── temp/                         - Temporary tests
├── lib/                              - Third-party libraries
├── build/                            - Build output (generated)
├── docs/                             - Documentation
├── cmake/                            - CMake modules
├── CMakeLists.txt                    - CMake configuration
├── CMakePresets.json                 - CMake presets
├── vcpkg.json                        - vcpkg manifest
├── CHANGELOG.md                      - Version history
├── README.md                         - Project documentation
└── DEVLOG.md                         - Development log
```

## Key Files
- `CMakeLists.txt` - CMake configuration
- `CMakePresets.json` - CMake presets
- `vcpkg.json` - vcpkg manifest for dependencies
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Build with CMake
cmake -B build -S . -DCMAKE_BUILD_TYPE=Release
cmake --build build

# Build with presets
cmake --preset=release
cmake --build --preset=release

# Testing
ctest --test-dir build --output-on-failure
./build/tests/project_tests

# Code Quality
clang-tidy src/*.cpp -- -I include/
cppcheck --enable=all --std=c++20 src/
cmake --build build --target clang-format

# Sanitizers
cmake -B build -DCMAKE_CXX_FLAGS="-fsanitize=address,undefined"
```

## Quick Reference

### Task Types → Skills Activated
| Task Type | Core Skills | Specialist Skills |
|-----------|-------------|-------------------|
| Bug Fix | code-standards, quality-checklist | context-manager, refactoring-expert |
| New Feature | workflow-methodology, testing-framework | task-coordinator, workflow-orchestrator |
| Refactoring | code-standards, implementation-patterns | refactoring-expert, legacy-modernizer |
| Documentation | documentation-standards | api-documentation, technical-documentation |
| Testing | unit-tests, test-cases | performance-testing, mutation-testing |
| Infrastructure | cicd-integration | kubernetes-expert, terraform-specialist, cicd-architect |
| Database | code-standards | sql-expert |
| Dependencies | security | dependency-manager, dependency-security-audit |

### Workflow Skills (for complex tasks)
- **task-coordinator** - Break down multi-step implementations
- **context-manager** - Navigate large codebases
- **workflow-orchestrator** - Chain skills with quality gates

### Efficiency Modes
- **Quick Mode** (simple fixes): Minimal docs, focus on core fix
- **Full Mode** (new projects): Complete modern C++ project, comprehensive testing

## Context References
- Architecture: @.claude/context/architecture.md
- Decisions: @.claude/memory/decisions.md

## Critical Rules

**NEVER:**
- Auto-modify version numbers (ask first)
- Suggest git commands unless explicitly requested
- Create separate markdown files (use DEVLOG.md)
- Run commands in chat (request user to run in terminal)

**ALWAYS:**
- Ask clarifying questions before proceeding
- Explain reasoning and teach concepts
- Use iterative testing with tests/temp/
- Document progress in DEVLOG.md
- Follow the quality checklist before delivering code
- Prefer RAII and smart pointers over raw pointers
- Use const and constexpr appropriately
- Avoid undefined behavior
- Use modern C++ idioms (range-based for, auto, etc.)
