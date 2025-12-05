# Code Review Templates

**Comprehensive 6-phase code review methodology for systematic codebase analysis**

[← Back to Main](../../README.md) | [Quick Start Guide](../../QUICKSTART.md) | [All Guides](../../guides/)

---

## 🚀 Quick Start

**New to code reviews?** Use this flowchart:

```
What do you need?
├─ Quick review (4 hours) → Run Phases 1-2 only
├─ Security audit only → Jump to Phase 3
├─ Performance issues → Jump to Phase 4
└─ Complete review (10-12 hours) → Run all 6 phases in order
```

**Copy & Paste Templates:**
1. Choose your language below
2. Click the phase you want to start with
3. Scroll to "## Prompt Template" in that file
4. Copy the entire prompt
5. Paste into GitHub Copilot / ChatGPT / Claude

---

## 📋 Overview

This section provides comprehensive code review templates that enable systematic analysis across multiple dimensions: context understanding, code quality, security vulnerabilities, performance optimization, testing adequacy, and final consolidated reporting.

**What You'll Get:**
- ✅ Severity-classified findings (CRITICAL, HIGH, MEDIUM, LOW)
- ✅ Specific file locations and line numbers
- ✅ Code examples showing issues and fixes
- ✅ Prioritized action plan
- ✅ Time estimates for remediation

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

### 6-Phase Review Methodology

Each phase builds on the previous one. Run them in order for best results.

---

### Phase 1: Context Analysis (2-3 hours) - START HERE

**What it does:** Understand the project structure, architecture, dependencies, and tech stack

**Templates:**
- [Python](context_analysis/python_context_analysis.md)
- [JavaScript](context_analysis/javascript_context_analysis.md)
- [Java](context_analysis/java_context_analysis.md)
- [C#](context_analysis/csharp_context_analysis.md)
- [Go](context_analysis/go_context_analysis.md)
- [C](context_analysis/c_context_analysis.md)
- [C++](context_analysis/cpp_context_analysis.md)

---

### Phase 2: Code Quality (2-3 hours)

**What it does:** Evaluate code style, maintainability, complexity, and best practices

**Templates:**
- [Python](code_quality/python_code_quality.md)
- [JavaScript](code_quality/javascript_code_quality.md)
- [Java](code_quality/java_code_quality.md)
- [C#](code_quality/csharp_code_quality.md)
- [Go](code_quality/go_code_quality.md)
- [C](code_quality/c_code_quality.md)
- [C++](code_quality/cpp_code_quality.md)

---

### Phase 3: Security Review (2-3 hours)

**What it does:** Identify vulnerabilities, security risks, OWASP Top 10, supply chain security

**Templates:**
- [Python](security_review/python_security_review.md)
- [JavaScript](security_review/javascript_security_review.md)
- [Java](security_review/java_security_review.md)
- [C#](security_review/csharp_security_review.md)
- [Go](security_review/go_security_review.md)
- [C](security_review/c_security_review.md)
- [C++](security_review/cpp_security_review.md)

---

### Phase 4: Performance Review (2-3 hours)

**What it does:** Profile performance, identify bottlenecks, recommend optimizations

**Templates:**
- [Python](performance_review/python_performance_review.md)
- [JavaScript](performance_review/javascript_performance_review.md)
- [Java](performance_review/java_performance_review.md)
- [C#](performance_review/csharp_performance_review.md)
- [Go](performance_review/go_performance_review.md)
- [C](performance_review/c_performance_review.md)
- [C++](performance_review/cpp_performance_review.md)

---

### Phase 5: Testing Review (2 hours)

**What it does:** Analyze test coverage, test quality, testing strategy

**Templates:**
- [Python](testing_review/python_testing_review.md)
- [JavaScript](testing_review/javascript_testing_review.md)
- [Java](testing_review/java_testing_review.md)
- [C#](testing_review/csharp_testing_review.md)
- [Go](testing_review/go_testing_review.md)
- [C](testing_review/c_testing_review.md)
- [C++](testing_review/cpp_testing_review.md)

---

### Phase 6: Final Report (1 hour) - FINISH HERE

**What it does:** Consolidate all findings with severity classification and action plan

**Templates:**
- [Python](final_report/python_final_report.md)
- [JavaScript](final_report/javascript_final_report.md)
- [Java](final_report/java_final_report.md)
- [C#](final_report/csharp_final_report.md)
- [Go](final_report/go_final_report.md)
- [C](final_report/c_final_report.md)
- [C++](final_report/cpp_final_report.md)

---

### Review Strategies

**Quick Review (4 hours):**
Run only Phases 1-2 for basic context and quality check

**Security-Focused (6 hours):**
Run Phases 1, 3, and 6 for security audit

**Performance-Focused (6 hours):**
Run Phases 1, 4, and 6 for performance optimization

**Comprehensive Review (10-12 hours):**
Run all 6 phases in order for complete analysis

## ✅ Success Criteria

- [ ] Complete context understanding documented

- [ ] Code quality issues identified and categorized by severity

- [ ] Security vulnerabilities mapped with remediation steps

- [ ] Performance bottlenecks profiled with optimization recommendations

- [ ] Test coverage gaps identified with improvement plan

- [ ] Final report delivered with prioritized, actionable recommendations

---

[← Back to AI Templates](../../README.md)
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
