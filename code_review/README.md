# Code Review

## 📋 Overview

This section provides comprehensive code review templates that enable systematic analysis of codebases across multiple dimensions: context understanding, code quality, security vulnerabilities, performance optimization, testing adequacy, and final consolidated reporting.

## 🎯 Objectives

- Understand project context, architecture, and dependencies before diving into code

- Evaluate code quality, maintainability, and adherence to best practices

- Identify security vulnerabilities and compliance gaps

- Detect performance bottlenecks and optimization opportunities

- Assess test coverage, quality, and effectiveness

- Generate actionable, prioritized recommendations with clear remediation paths

## 📂 Available Templates

### Supported Languages

Templates are available for the following languages:

- **Python** - General-purpose, data science, web development

- **JavaScript/TypeScript** - Web, Node.js, React, Angular, Vue

- **Java** - Enterprise, Spring Boot, Android

- **C#** - .NET, ASP.NET Core, Unity

- **Go** - Microservices, cloud-native

- **C** - Embedded systems, firmware, RTOS

- **C++** - Performance-critical, embedded, modern C++

### Review Phases

Each language has templates for all 6 review phases:

| Phase | Focus Areas | Available Languages |
|-------|-------------|---------------------|
| **[Context Analysis](context_analysis/)** | Project understanding, architecture mapping, dependency analysis | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Code Quality](code_quality/)** | Style compliance, maintainability metrics, complexity analysis | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Security Review](security_review/)** | Vulnerability scanning, OWASP Top 10, secrets detection | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Performance Review](performance_review/)** | Profiling, bottleneck identification, optimization | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Testing Review](testing_review/)** | Test coverage analysis, test quality evaluation | Python, JavaScript, Java, C#, Go, C, C++ |
| **[Final Report](final_report/)** | Consolidated findings with prioritized action items | Python, JavaScript, Java, C#, Go, C, C++ |

## ✅ Success Criteria

- [ ] Complete context understanding documented

- [ ] Code quality issues identified and categorized by severity

- [ ] Security vulnerabilities mapped with remediation steps

- [ ] Performance bottlenecks profiled with optimization recommendations

- [ ] Test coverage gaps identified with improvement plan

- [ ] Final report delivered with prioritized, actionable recommendations

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
