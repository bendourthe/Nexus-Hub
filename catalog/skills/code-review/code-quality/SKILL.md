---
name: code-quality
description: Evaluate code style, maintainability, complexity metrics, SOLID principles, dead code removal candidates, and adherence to best practices. Use for code quality assessment, technical debt identification, maintainability improvement, or as Phase 2 of comprehensive code review.
---

# Code Review - Code Quality

Evaluate code quality, maintainability, SOLID adherence, and dead code candidates. This skill is **Phase 2** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Assess code maintainability
- Identify technical debt
- Review coding standards compliance
- Measure code complexity
- Find code smells and anti-patterns
- Evaluate SOLID principle adherence
- Identify dead code removal candidates

**Trigger phrases**: "code quality", "code review", "technical debt", "code smells", "maintainability", "complexity", "best practices", "clean code", "SOLID", "dead code"

## What This Skill Does

### Quality Dimensions

| Dimension | Focus Areas |
|-----------|-------------|
| **Readability** | Naming, formatting, comments |
| **Maintainability** | Modularity, coupling, cohesion |
| **Complexity** | Cyclomatic complexity, nesting |
| **Consistency** | Style guide adherence |
| **Best Practices** | Language idioms, patterns |
| **SOLID Compliance** | SRP, OCP, LSP, ISP, DIP |
| **Dead Code** | Unused functions, unreachable branches |

### Severity Classification

| Level | Alias | Description |
|-------|-------|-------------|
| **P0** | CRITICAL | Blocking issues requiring immediate fix |
| **P1** | HIGH | Significant issues affecting quality |
| **P2** | MEDIUM | Improvements recommended |
| **P3** | LOW | Minor enhancements |

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

### Step 2: SOLID Analysis

Reference: `references/solid-checklist.md`

Work through each SOLID principle using its diagnostic question:

| Principle | Diagnostic Question |
|-----------|-------------------|
| **SRP** | "What is the single reason this module would change?" |
| **OCP** | "Can I add a new variant without touching existing code?" |
| **LSP** | "Can I substitute any subclass without the caller knowing?" |
| **ISP** | "Do all implementers use all methods?" |
| **DIP** | "Can I swap the implementation without changing business logic?" |

For each violation found:
1. State the principle violated
2. Quote the specific code location (`file:line`)
3. Explain the concrete impact (not theoretical)
4. Propose an incremental fix with rationale for *why* it improves cohesion/coupling
5. Classify severity (P0 through P3)

### Step 3: Review Code Structure

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

Reference: `references/code-quality-checklist.md` (Error Handling section)

### Step 4: Identify Code Smells

Reference: `references/solid-checklist.md` (Common Code Smells table)

Detect these smells with their thresholds:

| Smell | Threshold / Indicator |
|-------|----------------------|
| **Long Method** | >30 lines |
| **Large Class** | >500 lines |
| **Feature Envy** | Method uses another class's data more than its own |
| **Data Clumps** | Same group of fields/parameters appear together repeatedly |
| **Primitive Obsession** | Primitives instead of small domain objects |
| **Shotgun Surgery** | One change requires edits in many unrelated files |
| **Divergent Change** | One module changes for multiple unrelated reasons |
| **Duplicate Code** | Copy-paste patterns across files |
| **Dead Code** | Unused functions, variables, imports |
| **Speculative Generality** | Abstractions for features that don't exist |
| **Magic Numbers/Strings** | Unexplained literal values in logic |
| **Deep Nesting** | >3 levels of indentation |

### Step 5: Dead Code Removal Candidates

Reference: `references/removal-plan.md`

1. **Identify candidates**: Scan for unused functions, unreachable branches, commented-out code, feature-flagged-off code
2. **Categorize each** as:
   - **Safe to remove now**: No callers, no dynamic references, clear evidence
   - **Defer with plan**: External consumers, reflection usage, or active experiment
3. **Fill in the removal plan template** for each candidate
4. **Run the pre-removal checklist** (7 items) for "safe to remove now" candidates

### Step 6: Apply Refactor Heuristics

When proposing fixes, follow these 7 heuristics:

1. Split by responsibility, not by size
2. Introduce abstraction only when needed (wait for second use case)
3. Keep refactors incremental
4. Preserve behavior first (add tests before restructuring)
5. Name things by intent
6. Prefer composition over inheritance
7. Make illegal states unrepresentable

### Step 7: Document Findings

```markdown
## Code Quality Finding

**File**: [path/to/file.py:42]
**Severity**: P1 (HIGH)
**Category**: [SOLID Violation / Code Smell / Dead Code]
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

- [ ] Static analysis run
- [ ] SOLID diagnostic questions applied to each module
- [ ] Naming conventions reviewed
- [ ] Function complexity checked
- [ ] Error handling assessed
- [ ] Code smells detected (full list)
- [ ] Dead code candidates identified and categorized
- [ ] Removal plan created for dead code
- [ ] Refactor proposals follow the 7 heuristics
- [ ] Findings documented with severity

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `security-review` - Security analysis (Phase 3)
- `performance-review` - Performance analysis (Phase 4)
- `testing-review` - Test assessment (Phase 5)
- `final-report` - Consolidated report (Phase 6)

---

**Version**: 2.0.0
**Last Updated**: February 2026
**Based on**: DevAI-Hub code review methodology + code-review-expert


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
