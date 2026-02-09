---
description: Perform a comprehensive code review of the entire codebase or current git changes.
---

# Run Code Review Command

Perform a senior-engineer-level code review with structured findings, severity classification, and actionable remediation.

## Review Mode

Determine the review mode based on the user's request:

- **Full Codebase** (default): Review the entire codebase across all 6 phases
- **Git Changes**: If the user mentions "changes", "diff", "PR", "commit", or "what I changed", scope the review to current git changes only

For Git Changes mode, begin with a preflight step:
```bash
git status -sb
git diff --stat
git diff
```

### Edge Case Handling

- **No changes detected** (git mode): Inform the user and ask if they want to review staged changes (`git diff --cached`) or a specific commit range
- **Large diff (>500 lines)**: Summarize changes by file first, then review in batches grouped by module or feature area
- **Mixed concerns**: Group findings by logical feature, not just file order

## Severity Classification

All findings use the P0-P3 scale consistently:

| Level | Alias | Description | Required Action |
|-------|-------|-------------|-----------------|
| **P0** | CRITICAL | Security vulnerability, data loss risk, correctness bug | Must block merge / fix immediately |
| **P1** | HIGH | Logic error, significant SOLID violation, performance regression | Should fix before merge/release |
| **P2** | MEDIUM | Code smell, maintainability concern, minor violation | Fix in this PR/sprint or create follow-up |
| **P3** | LOW | Style, naming, minor suggestion | Optional improvement |

## 6-Phase Review Process

Execute each phase in order. Reference the corresponding skill and checklist for detailed guidance.

### Phase 1: Context Analysis
**Skill**: `context-analysis`

- Map project structure, entry points, architecture patterns
- Identify dependencies and their health
- In git-changes mode: scope changed files, identify critical paths (auth, payments, data writes, network)
- Output: Context Analysis Report

### Phase 2: Code Quality + SOLID + Dead Code
**Skill**: `code-quality`
**References**: `references/solid-checklist.md`, `references/code-quality-checklist.md`, `references/removal-plan.md`

- Evaluate readability, maintainability, complexity
- Run SOLID diagnostic questions against each module
- Detect code smells (long methods, feature envy, data clumps, primitive obsession, shotgun surgery, duplicate code, deep nesting, magic numbers, dead code, speculative generality)
- Identify dead code removal candidates (safe-delete-now vs defer-with-plan)
- Apply 7 refactor heuristics when proposing fixes
- Output: Code Quality Report with SOLID findings and removal plan

### Phase 3: Security Review (10 Domains)
**Skill**: `security-review`
**Reference**: `references/security-checklist.md`

Scan across all 10 security domains:
1. Input/Output Safety (XSS, injection, SSRF, path traversal)
2. AuthN/AuthZ (tenant checks, auth guards, IDOR)
3. JWT & Token Security
4. Secrets and PII
5. Supply Chain & Dependencies
6. CORS & Security Headers
7. Runtime Risks (unbounded loops, missing timeouts, ReDoS)
8. Cryptography
9. Race Conditions (shared state, TOCTOU, database concurrency, distributed systems)
10. Data Integrity

For each finding, document both **exploitability** and **impact**.
- Output: Security Findings Report

### Phase 4: Performance Review
**Skill**: `performance-review`
**Reference**: `references/code-quality-checklist.md` (performance section)

- Profile hot paths (CPU, memory, I/O)
- Detect anti-patterns (N+1 queries, missing cache, sync I/O, string concatenation in loops)
- Analyze caching strategy (TTL, invalidation, key collisions, stampede risk)
- Check boundary conditions that affect performance (unbounded collections, large payloads)
- Output: Performance Report

### Phase 5: Testing Review
**Skill**: `testing-review`

- Measure coverage (line, branch, function)
- Assess test quality (AAA pattern, naming, isolation, speed)
- Evaluate test type balance (unit 70%, integration 20%, E2E 10%)
- Identify coverage gaps in critical paths
- In git-changes mode: focus on whether changed code has adequate test coverage
- Output: Testing Report

### Phase 6: Final Report
**Skill**: `final-report`

Consolidate all findings into the unified output format (see below).

## Output Format

The final report follows a 4-section structure. See `final-report` skill for the full template. Summary:

```markdown
# Code Review Report

**Project**: [Name]
**Review Date**: [Date]
**Mode**: [Full Codebase / Git Changes]
**Files Reviewed**: [Count]
**Overall Verdict**: [APPROVE / REQUEST_CHANGES / COMMENT]

---

# Section 1: Codebase Overview
[High-level description: what the codebase does, purpose, target users, core architecture]

# Section 2: Executive Summary
- **Verdict** with statistics table (P0/P1/P2/P3 counts)
- **Critical Fixes** - All P0 items as brief one-liners in a table
- **Functional Groupings** - Which areas need the most work, with finding counts
- **Redundancy & Trimming** - What can be safely removed
- **Roadmap Perspective** - Short-term quick wins and long-term improvements

# Section 3: Detailed Report
- **Phase 1 (By Feature)** - Findings grouped into logical feature areas (e.g., Authentication, Error Handling, CI/CD). Within each group, ordered critical to low.
- **Phase 2 (By Priority)** - Same findings regrouped as P0/P1/P2/P3 tables across all features.

# Section 4: Export
Offered via Next Steps menu option 5.

---

## Next Steps

Found X issues (P0: _, P1: _, P2: _, P3: _).

**How would you like to proceed?**
1. **Fix all** - I'll implement all suggested fixes across all severity levels
2. **Fix P0/P1 only** - Address the critical and high priority issues
3. **Fix specific items** - Tell me which issues to fix by number
4. **No changes** - Review complete, no implementation needed
5. **Export report** - Generate Markdown and Word (.docx) versions of this report
```

### Inline Comment Format

For file-specific findings, use:
```
::code-comment{file="path/to/file.ts" line="42" severity="P1"}
Description of the issue and suggested fix.
::
```

### Clean Review Protocol

If no issues are found in a phase, explicitly state:
- What was checked
- Any areas not covered (and why)
- Residual risks or recommended follow-up tests

### Overall Verdict

- **APPROVE**: No P0 or P1 findings. Code is ready to merge/ship.
- **REQUEST_CHANGES**: P0 or P1 findings exist that should be resolved.
- **COMMENT**: No blocking issues, but P2/P3 suggestions are worth considering.

## Review-First Paradigm

**CRITICAL**: Do NOT implement any changes until the user explicitly confirms which fixes to apply. Present findings first, then wait for the user's selection from the Next Steps menu.

## Iterative Refinement (Loop)

This is an iterative process. Perform the following refinement loop up to **3 times** (or as specified by the user):

1. **Analyze**: Review the generated output for completeness and accuracy
2. **Refine**: Fix any gaps, add missing findings, improve clarity
3. **Stop**: When confident the result is thorough, or maximum iterations reached

---

> After presenting the final report, end with the Next Steps menu above.
