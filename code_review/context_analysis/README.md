# Context Analysis

## 📋 Overview

Context analysis is the critical first phase of code review. Before evaluating code quality, security, or performance, it's essential to understand the project's purpose, architecture, dependencies, and current state. This phase establishes the foundation for all subsequent review activities.

## 🎯 Objectives

- Map project structure, entry points, and module organization

- Understand architecture patterns and design decisions

- Identify all dependencies and their versions

- Document build/deployment workflows

- Establish baseline metrics for codebase complexity

## 📂 Available Templates

| Language | Template File |
|----------|---------------|
| **Python** | [python_context_analysis.md](python_context_analysis.md) |
| **JavaScript/TypeScript** | [javascript_context_analysis.md](javascript_context_analysis.md) |
| **Java** | [java_context_analysis.md](java_context_analysis.md) |
| **C#** | [csharp_context_analysis.md](csharp_context_analysis.md) |
| **Go** | [go_context_analysis.md](go_context_analysis.md) |
| **C** | [c_context_analysis.md](c_context_analysis.md) |
| **C++** | [cpp_context_analysis.md](cpp_context_analysis.md) |

## ✅ Success Criteria

- [ ] Project purpose and scope documented

- [ ] Architecture and design patterns identified

- [ ] Dependency tree mapped with version information

- [ ] Build and deployment process understood

- [ ] Codebase metrics baseline established

- [ ] Key stakeholders and documentation located

---

[← Back to Code Review](../README.md)
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
