---
name: final-report
description: Consolidate all review findings into a prioritized report with severity classifications and actionable remediation plan. Use as the final phase of comprehensive code review to deliver actionable recommendations.
---

# Code Review - Final Report

Consolidate all review findings into a comprehensive, actionable report. This skill is **Phase 6** of the 6-phase code review methodology.

## When to Use This Skill

Use this skill when you need to:

- Complete a comprehensive code review
- Consolidate findings from multiple phases
- Create prioritized action plan
- Deliver executive summary
- Document remediation roadmap

**Trigger phrases**: "final report", "code review report", "consolidate findings", "review summary", "action plan", "remediation plan"

## What This Skill Does

### Report Components

1. **Executive Summary**
   - Overall assessment
   - Critical findings count
   - Risk level

2. **Findings by Phase**
   - Context analysis
   - Code quality
   - Security
   - Performance
   - Testing

3. **Prioritized Action Plan**
   - Immediate (CRITICAL)
   - Short-term (HIGH)
   - Medium-term (MEDIUM)
   - Long-term (LOW)

4. **Metrics Dashboard**
   - Coverage
   - Complexity
   - Vulnerabilities

## Report Template

```markdown
# Code Review Final Report

**Project**: [Name]
**Version**: [Version]
**Review Date**: [Date]
**Reviewer**: [Name]

---

## Executive Summary

### Overall Assessment
[Overall health: Good/Fair/Needs Attention/Critical]

### Key Statistics
| Metric | Value | Status |
|--------|-------|--------|
| Critical Issues | [N] | [Status] |
| High Issues | [N] | [Status] |
| Code Coverage | [%] | [Status] |
| Security Score | [Score] | [Status] |

### Risk Level
[Low/Medium/High/Critical] - [Brief justification]

---

## Findings Summary

### By Severity
| Severity | Count | Action Required |
|----------|-------|-----------------|
| CRITICAL | [N] | Immediate |
| HIGH | [N] | Within 1 week |
| MEDIUM | [N] | Within 1 month |
| LOW | [N] | Backlog |

### By Category
| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | [N] | [N] | [N] | [N] |
| Performance | [N] | [N] | [N] | [N] |
| Quality | [N] | [N] | [N] | [N] |
| Testing | [N] | [N] | [N] | [N] |

---

## Critical Findings (Immediate Action)

### 1. [Finding Title]
**File**: [path:line]
**Severity**: CRITICAL
**Category**: Security

**Issue**: [Description]

**Impact**: [Business/technical impact]

**Remediation**:
```code
[Fix code]
```

**Effort**: [Hours/Days]

---

## High Priority Findings

### 1. [Finding Title]
[Similar structure to critical]

---

## Prioritized Action Plan

### Phase 1: Immediate (0-7 days)
- [ ] Fix SQL injection in auth module
- [ ] Update vulnerable dependencies
- [ ] [Other critical items]

### Phase 2: Short-term (1-4 weeks)
- [ ] Improve error handling
- [ ] Add missing unit tests
- [ ] [Other high items]

### Phase 3: Medium-term (1-3 months)
- [ ] Refactor complex modules
- [ ] Improve documentation
- [ ] [Other medium items]

### Phase 4: Long-term (Backlog)
- [ ] Code style improvements
- [ ] Minor optimizations
- [ ] [Other low items]

---

## Recommendations

### Security
1. [Recommendation]
2. [Recommendation]

### Performance
1. [Recommendation]
2. [Recommendation]

### Quality
1. [Recommendation]
2. [Recommendation]

---

## Appendices

### A. Tools Used
- Static Analysis: [Tools]
- Security Scan: [Tools]
- Coverage: [Tools]

### B. Methodology
[Brief description of review methodology]

### C. Detailed Findings
[Link to detailed findings document]
```

## Quality Checklist

- [ ] All phase findings consolidated
- [ ] Severity consistently classified
- [ ] Action plan prioritized
- [ ] Executive summary clear
- [ ] Remediation steps actionable
- [ ] Effort estimates included
- [ ] Report professionally formatted

## Related Skills

- `context-analysis` - Context understanding (Phase 1)
- `code-quality` - Code quality review (Phase 2)
- `security-review` - Security analysis (Phase 3)
- `performance-review` - Performance analysis (Phase 4)
- `testing-review` - Test assessment (Phase 5)

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: AI Templates code_review/final_report/


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
