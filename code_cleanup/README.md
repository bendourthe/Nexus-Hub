# Code Cleanup

## 📋 Overview

This section targets the detection and removal of dead code, duplication, and drift so the codebase stays lean, current, and maintainable.

## 🎯 Objectives

- Identify and remove unused modules, functions, and feature flags.
- Consolidate duplicated logic and near-duplicate implementations.
- Modernize legacy patterns that conflict with current architecture.
- Document refactoring opportunities with risk and effort estimates.
- Verify that cleanup preserves behaviour through focused regression checks.

## 📂 Available Templates

### General Purpose Languages

| Language | Template | Key Focus Areas |
|----------|----------|-----------------|
| **Python** | [python_cleanup.md](python_cleanup.md) | Unused imports/functions, empty lines, debug statements, import organization, code simplification |
| **JavaScript/TypeScript** | [javascript_cleanup.md](javascript_cleanup.md) | Unused imports/exports, console.log statements, ES6+ modernization, TypeScript types, npm dependencies |
| **Java** | [java_cleanup.md](java_cleanup.md) | Unused imports/methods, System.out debugging, code smells, lambdas/streams, Maven/Gradle cleanup |
| **C#** | [csharp_cleanup.md](csharp_cleanup.md) | Unused usings, Console statements, modern C# features, nullable types, NuGet packages, ReSharper patterns |
| **Go** | [go_cleanup.md](go_cleanup.md) | Unused imports, fmt.Println debugging, idiomatic patterns, go vet/staticcheck findings, module cleanup |

### Systems Programming Languages

| Language | Template | Key Focus Areas |
|----------|----------|-----------------|
| **C** | [c_cleanup.md](c_cleanup.md) | Unused includes, memory leaks, buffer overflows, embedded systems patterns, MISRA-C/CERT-C compliance |
| **C++** | [cpp_cleanup.md](cpp_cleanup.md) | Unused includes, smart pointers, RAII, modern C++ features (C++11/14/17/20), static analysis, sanitizers |


## ✅ Success Criteria

- [ ] Dead code candidates identified and removed
- [ ] Duplicate logic catalogued with consolidation plan
- [ ] Legacy patterns flagged with modernization strategy
- [ ] Refactor tasks sized with risk/impact notes
- [ ] Regression safeguards defined (tests, toggles, rollout plan)

---

[← Back to AI Templates](../README.md)
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
