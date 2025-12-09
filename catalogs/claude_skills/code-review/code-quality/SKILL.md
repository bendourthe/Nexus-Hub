---
name: code-quality
description: Evaluate code style, maintainability, complexity metrics, and adherence to best practices. Use for code quality assessment, technical debt identification, maintainability improvement, or as Phase 2 of comprehensive code review.
---

# Code Review - Code Quality

Evaluate code quality, maintainability, and adherence to best practices. This skill is **Phase 2** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Assess code maintainability
- Identify technical debt
- Review coding standards compliance
- Measure code complexity
- Find code smells and anti-patterns
- Evaluate naming conventions

**Trigger phrases**: "code quality", "code review", "technical debt", "code smells", "maintainability", "complexity", "best practices", "clean code"

## What This Skill Does

### Quality Dimensions

| Dimension | Focus Areas |
|-----------|-------------|
| **Readability** | Naming, formatting, comments |
| **Maintainability** | Modularity, coupling, cohesion |
| **Complexity** | Cyclomatic complexity, nesting |
| **Consistency** | Style guide adherence |
| **Best Practices** | Language idioms, patterns |

### Severity Classification

- **CRITICAL**: Blocking issues requiring immediate fix
- **HIGH**: Significant issues affecting quality
- **MEDIUM**: Improvements recommended
- **LOW**: Minor enhancements

## Instructions

### Step 1: Run Static Analysis

```bash
# Python
ruff check .
pylint src/
mypy src/
radon cc . -a -nb

# JavaScript
eslint src/
tsc --noEmit

# Java
mvn checkstyle:check
mvn pmd:pmd
```

### Step 2: Review Code Structure

1. **Naming Conventions**
   - Classes: PascalCase
   - Functions: snake_case or camelCase
   - Constants: UPPER_CASE

2. **Function Design**
   - Single responsibility
   - Appropriate length (<50 lines)
   - Clear parameters

3. **Error Handling**
   - Explicit exception handling
   - Meaningful error messages
   - Proper cleanup

### Step 3: Identify Code Smells

Common code smells to detect:
- **Long Method**: Functions >50 lines
- **Large Class**: Classes >500 lines
- **Duplicate Code**: Copy-paste patterns
- **Dead Code**: Unused functions/imports
- **Magic Numbers**: Unexplained literals
- **Deep Nesting**: >3 levels

### Step 4: Document Findings

```markdown
## Code Quality Finding

**File**: [path/to/file.py:42]
**Severity**: HIGH
**Issue**: [Description]
**Impact**: [Why it matters]

### Current Code
```python
[problematic code]
```

### Recommended Fix
```python
[improved code]
```

**Effort**: [Low/Medium/High]
```

## Quality Checklist

- [ ] Naming conventions reviewed
- [ ] Function complexity checked
- [ ] Error handling assessed
- [ ] Code duplication identified
- [ ] Dead code detected
- [ ] Style guide compliance verified
- [ ] Findings documented with severity

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `security-review` - Security analysis (Phase 3)
- `final-report` - Consolidated report (Phase 6)

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_review/code_quality/
