# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: C11/C17/C23
- **Compiler**: GCC / Clang / MSVC
- **Build System**: CMake / Make / Meson
- **Testing**: Unity Test / CMocka / Check
- **Code Quality**: cppcheck, clang-tidy, Valgrind
- **Documentation**: Doxygen

## Project Structure
```
project-name/
├── src/                              - Source files
│   ├── main.c                        - Main entry point
│   ├── core/                         - Core application logic
│   │   ├── module.c
│   │   └── module.h
│   └── utils/                        - Utility functions
│       ├── utils.c
│       └── utils.h
├── include/                          - Public headers
│   └── project/
│       └── api.h                     - Public API
├── tests/                            - Test files
│   ├── test_main.c                   - Test runner
│   ├── test_module.c                 - Module tests
│   └── temp/                         - Temporary tests
├── lib/                              - Third-party libraries
├── build/                            - Build output (generated)
├── docs/                             - Documentation
├── CMakeLists.txt                    - CMake configuration
├── Makefile                          - Make configuration
├── CHANGELOG.md                      - Version history
├── README.md                         - Project documentation
└── DEVLOG.md                         - Development log
```

## Key Files
- `CMakeLists.txt` - CMake configuration
- `Makefile` - Make configuration
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Build with CMake
mkdir -p build && cd build
cmake ..
cmake --build .

# Build with Make
make
make clean
make debug

# Testing
./build/tests/test_runner
make test
ctest --output-on-failure

# Code Quality
cppcheck --enable=all src/
clang-tidy src/*.c -- -I include/
valgrind --leak-check=full ./build/app
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
- **Full Mode** (new projects): Complete project layout, comprehensive testing

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
- Check for memory leaks with Valgrind
- Handle all error conditions
- Follow the quality checklist before delivering code
- Use const correctness
- Avoid undefined behavior
