---
name: final-report
description: Consolidate all review findings into a prioritized report with P0-P3 severity, overall verdict (APPROVE/REQUEST_CHANGES/COMMENT), and actionable next steps menu. Use as the final phase of comprehensive code review.
---

# Code Review - Final Report

Consolidate all review findings into a comprehensive, actionable report with a clear verdict and next steps. This skill is **Phase 6** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Complete a comprehensive code review
- Consolidate findings from multiple phases
- Create prioritized action plan
- Deliver executive summary with verdict
- Document remediation roadmap
- Present next steps for user confirmation

**Trigger phrases**: "final report", "code review report", "consolidate findings", "review summary", "action plan", "remediation plan"

## What This Skill Does

### Report Components

1. **Executive Summary with Verdict**
   - Overall assessment (APPROVE / REQUEST_CHANGES / COMMENT)
   - Finding counts by severity
   - Risk level

2. **Findings by Phase**
   - Context analysis
   - Code quality + SOLID + dead code
   - Security (10 domains)
   - Performance
   - Testing

3. **Prioritized Action Plan**
   - Immediate (P0)
   - Short-term (P1)
   - Medium-term (P2)
   - Backlog (P3)

4. **Next Steps Confirmation**
   - User chooses how to proceed
   - No changes implemented without confirmation

## Overall Verdict

Assign one of three verdicts (mirroring GitHub PR review states):

| Verdict | When to Use |
|---------|-------------|
| **APPROVE** | No P0 or P1 findings. Code is ready to merge/ship. |
| **REQUEST_CHANGES** | P0 or P1 findings exist that should be resolved before proceeding. |
| **COMMENT** | No blocking issues, but P2/P3 suggestions are worth considering. |

## Inline Comment Format

For file-specific findings throughout the report, use this format:

```
::code-comment{file="path/to/file.ts" line="42" severity="P1"}
Description of the issue and suggested fix.
::
```

## Clean Review Protocol

If no issues are found in a phase (or overall), explicitly state:
- **What was checked**: List the specific areas, domains, and checklists applied
- **Areas not covered**: Any limitations or areas outside the review scope (and why)
- **Residual risks**: Potential concerns that could not be verified through static review alone
- **Recommended follow-up**: Suggested dynamic tests, load tests, or manual verification

## Report Template

```markdown
# Code Review Final Report

**Project**: [Name]
**Version**: [Version]
**Review Date**: [Date]
**Reviewer**: [Name]
**Mode**: [Full Codebase / Git Changes]

---

## Executive Summary

### Overall Verdict: [APPROVE / REQUEST_CHANGES / COMMENT]

### Key Statistics
| Metric | Value | Status |
|--------|-------|--------|
| P0 (Critical) Issues | [N] | [Status] |
| P1 (High) Issues | [N] | [Status] |
| P2 (Medium) Issues | [N] | [Status] |
| P3 (Low) Issues | [N] | [Status] |
| Code Coverage | [%] | [Status] |
| Security Score | [Score] | [Status] |

### Risk Level
[Low/Medium/High/Critical] - [Brief justification]

---

## Findings Summary

### By Severity
| Severity | Count | Action Required |
|----------|-------|-----------------|
| P0 (Critical) | [N] | Must fix immediately |
| P1 (High) | [N] | Fix before merge/release |
| P2 (Medium) | [N] | Fix in sprint or create follow-up |
| P3 (Low) | [N] | Optional / backlog |

### By Category
| Category | P0 | P1 | P2 | P3 |
|----------|----|----|----|----|
| Security | [N] | [N] | [N] | [N] |
| Performance | [N] | [N] | [N] | [N] |
| Code Quality | [N] | [N] | [N] | [N] |
| SOLID | [N] | [N] | [N] | [N] |
| Testing | [N] | [N] | [N] | [N] |
| Dead Code | [N] | [N] | [N] | [N] |

---

## P0 - Critical Findings (Must Fix)

### 1. [Finding Title]
**File**: [path:line]
**Severity**: P0 (CRITICAL)
**Category**: [Security / Performance / Quality / SOLID / Testing]

**Issue**: [Description]

**Exploitability/Impact**: [Assessment]

**Remediation**:
\`\`\`code
[Fix code]
\`\`\`

**Effort**: [Low/Medium/High]

---

## P1 - High Priority Findings

### 1. [Finding Title]
[Similar structure to P0]

---

## P2 - Medium Priority Findings

### 1. [Finding Title]
[Similar structure]

---

## P3 - Low Priority Findings

### 1. [Finding Title]
[Similar structure]

---

## Removal/Iteration Plan

(If dead code candidates were identified in Phase 2)

### Safe to Remove Now
[Table from removal-plan.md template]

### Defer Removal
[Table from removal-plan.md template]

---

## Prioritized Action Plan

### Immediate (0-7 days) - P0 items
- [ ] [Item with file reference]

### Short-term (1-4 weeks) - P1 items
- [ ] [Item with file reference]

### Medium-term (1-3 months) - P2 items
- [ ] [Item with file reference]

### Backlog - P3 items
- [ ] [Item with file reference]

---

## Recommendations

### Security
1. [Recommendation]

### Performance
1. [Recommendation]

### Quality
1. [Recommendation]

### Testing
1. [Recommendation]

---

## Appendices

### A. Tools Used
- Static Analysis: [Tools]
- Security Scan: [Tools]
- Coverage: [Tools]

### B. Methodology
6-phase code review: Context Analysis, Code Quality + SOLID, Security (10 domains), Performance, Testing, Final Report

### C. Reference Checklists Applied
- SOLID Checklist (references/solid-checklist.md)
- Security Checklist (references/security-checklist.md)
- Code Quality Checklist (references/code-quality-checklist.md)
- Removal Plan (references/removal-plan.md)
```

---

## Next Steps Confirmation

**CRITICAL**: Do NOT implement any changes until the user explicitly confirms which fixes to apply.

After presenting the report, always end with:

```markdown
---

## Next Steps

Found X issues (P0: _, P1: _, P2: _, P3: _).

**How would you like to proceed?**
1. **Fix all** - I'll implement all suggested fixes
2. **Fix P0/P1 only** - Address critical and high priority issues
3. **Fix specific items** - Tell me which issues to fix
4. **No changes** - Review complete, no implementation needed
```

Wait for the user's selection before taking any action.

## Quality Checklist

- [ ] All phase findings consolidated
- [ ] Severity consistently classified (P0-P3)
- [ ] Overall verdict assigned (APPROVE / REQUEST_CHANGES / COMMENT)
- [ ] Action plan prioritized by severity
- [ ] Executive summary clear and accurate
- [ ] Remediation steps actionable with code examples
- [ ] Effort estimates included
- [ ] Report professionally formatted
- [ ] Clean review protocol followed (if no issues found)
- [ ] Next steps menu presented
- [ ] No changes implemented without user confirmation

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `code-quality` - Code quality + SOLID + dead code review (Phase 2)
- `security-review` - Security analysis, 10-domain model (Phase 3)
- `performance-review` - Performance analysis (Phase 4)
- `testing-review` - Test assessment (Phase 5)

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
