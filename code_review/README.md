# Code Review Templates

Create consistent, AI-assisted code reviews with this seven-step workflow. Every review module links directly to a copy-ready prompt so you can move from discovery to final report without losing momentum.

---

## Quick navigation

- [Quick start](#quick-start)
- [Review overview](#review-overview)
- [Choose your review depth](#choose-your-review-depth)
- [Review details](#review-details)
- [Best practices](#best-practices)
- [Support](#support)

---

## Quick start

1. Open the [review overview](#review-overview) and choose the modules you need.
2. Click the prompt link for your language (currently Python) and paste it into your coding assistant.
3. Gather evidence as you work—note file paths, line numbers, severity, and remediation ideas.
4. Close with the [final report prompt](final_report/python_final_report.md) to consolidate findings and decisions.

**Tip:** Run modules sequentially the first time you audit a codebase. On later passes you can jump directly to the focus areas that matter most.

---

## Review overview

| Step | Focus | Primary outcome | Prompt |
| --- | --- | --- | --- |
| 1 | Context analysis | Review scope, architecture map | [Python](context_analysis/python_context_analysis.md) |
| 2 | Code quality | Style, maintainability, documentation feedback | [Python](code_quality/python_code_quality.md) |
| 3 | Code cleanup | Dead-code removal, duplication audit, refactor plan | [Python](code_cleanup/python_cleanup.md) |
| 4 | Security | Vulnerability assessment with severity tags | [Python](security_review/python_security_review.md) |
| 5 | Performance | Bottleneck and optimization findings | [Python](performance_review/python_performance_review.md) |
| 6 | Testing | Coverage and quality gaps with remediation plan | [Python](testing_review/python_testing_review.md) |
| 7 | Final report | Executive summary, go/no-go decision, roadmap | [Python](final_report/python_final_report.md) |

**Estimated effort:** 1–18 hours depending on how many modules you complete and the size of the codebase.

---

## Choose your review depth

| Mode | Who it’s for | Recommended modules | Time |
| --- | --- | --- | --- |
| ⚡ Quick scan | Hotfixes and small PRs | 1 → 2 → 7 | ~1–2 h |
| 🧹 Cleanup sprint | Legacy stabilization, tidy-up cycles | 1 → 2 → 3 → 7 | ~2–3 h |
| 🎯 Standard review | Feature work and medium releases | 1 → 2 → 3 → 4 → 7 | ~3–5 h |
| 🔍 Comprehensive audit | Major releases, new projects, pre-production | 1 → 2 → 3 → 4 → 5 → 6 → 7 | ~10–18 h |

Mix and match modules when you need targeted insight (e.g., security-only deep dives or testing-focused assessments).

---

## Review details

### Context analysis
**Objective:** Understand the product goals, architecture, dependencies, and review boundaries.

- Clarify documentation quality and architectural fit.
- Identify high-risk areas that deserve extra scrutiny.
- Capture review assumptions and planned checkpoints.

**Python template:** [Context analysis prompt](context_analysis/python_context_analysis.md)

### Code quality
**Objective:** Evaluate readability, maintainability, and adherence to standards.

- Inspect naming, structure, modularity, and documentation.
- Highlight complexity hotspots and refactoring opportunities.
- Record strengths alongside improvement ideas.

**Python template:** [Code quality prompt](code_quality/python_code_quality.md)

### Code cleanup
**Objective:** Eliminate dead code, duplication, and drift from current architecture.

- Locate unused modules, dormant flags, and abandoned experiments.
- Consolidate duplicate logic and modernize legacy patterns.
- Prioritize refactoring tasks with risk, impact, and ownership.

**Python template:** [Code cleanup prompt](code_cleanup/python_cleanup.md)

### Security review
**Objective:** Surface vulnerabilities, insecure defaults, and threat vectors.

- Validate input handling, authentication, and authorization paths.
- Assess dependency risk (packages, versions, SBOM items).
- Provide severity-labelled findings with mitigation guidance.

**Python template:** [Security review prompt](security_review/python_security_review.md)

### Performance review
**Objective:** Measure efficiency and headroom for growth.

- Look for algorithmic bottlenecks and resource leaks.
- Evaluate caching, concurrency, and scalability strategies.
- Recommend profiling experiments or production safeguards.

**Python template:** [Performance review prompt](performance_review/python_performance_review.md)

### Testing review
**Objective:** Assess test depth, reliability, and automation coverage.

- Inspect unit, integration, and end-to-end suites.
- Confirm edge cases, error handling, fixtures, and mocks.
- Outline coverage gaps with prioritized remediation steps.

**Python template:** [Testing review prompt](testing_review/python_testing_review.md)

### Final report
**Objective:** Summarize review outcomes and chart the remediation roadmap.

- Assign a health score and deployment recommendation.
- Consolidate findings by severity and owning team.
- Propose follow-up actions with estimated effort.

**Python template:** [Final report prompt](final_report/python_final_report.md)

---

## Best practices

- **Stay sequential on the first pass.** Each module sets context for the next and reduces redundant digging.
- **Cite evidence.** Annotate findings with file paths, line numbers, and screenshots when helpful.
- **Balance critique and praise.** Recognize good patterns to reinforce team habits.
- **Validate with humans.** Treat AI-generated insights as drafts—verify anything high-severity before escalating.
- **Track remediation.** Create tickets, owners, and due dates for every actionable item.

---

## Support

- **Language coverage:** Python prompts are ready today; JavaScript, Java, C#, Go, and Rust variants are planned for a future release.
- **Need a bird’s-eye view?** Start at the repository [root README](../README.md) for directory-wide guidance.
- **Questions or ideas?** Open an issue or share feedback with your review lead so the templates can keep improving.

*Last updated: October 2025*
*Current Templates: Python (7 modules complete)*

[↑ Back to Repository Root](../README.md)
# Code Review Templates# Code Review Templates# Code Review Templates# Code Review Templates# Code Review Templates# Code Review Templates

Comprehensive templates for conducting thorough, consistent code reviews across different programming languages and frameworks.

## 🎯 OverviewComprehensive templates for conducting thorough, consistent code reviews across different programming languages and frameworks.

These templates provide structured, AI-assisted code review workflows with:
# Code Review Templates

Create consistent, AI-assisted code reviews with this six-step workflow. Every phase links directly to a copy-ready prompt so you can move from preparation to final report without hunting through files.

---

## Quick navigation

- [Quick start](#quick-start)
- [Review overview](#phase-overview)
- [Choose your review depth](#choose-your-review-depth)
- [Review details](#phase-details)
- [Best practices](#best-practices)
- [Support](#support)

---

## Quick start

1. Open the [review overview](#phase-overview) and choose the phases you need.
2. Click the prompt link for your language (currently Python) and copy it into your AI assistant.
3. Gather evidence as you review—note file paths, line numbers, and severity.
4. Close with the [final report prompt](final_report/python_final_report.md) to consolidate findings.

**Tip:** Run phases in order the first time through a codebase. On subsequent passes you can jump straight to the phases that matter most.

---

## Review overview

| Phase | Focus | Primary outcome | Prompt |
| --- | --- | --- | --- |
| 1 | Context analysis | Review scope, architecture map | [Python](context_analysis/python_context_analysis.md) |
| 2 | Code quality | Style, maintainability, documentation feedback | [Python](code_quality/python_code_quality.md) |
| 3 | Security | Vulnerability assessment with severity tags | [Python](security_review/python_security_review.md) |
| 4 | Performance | Bottleneck and optimization findings | [Python](performance_review/python_performance_review.md) |
| 5 | Testing | Coverage and quality gaps with remediation plan | [Python](testing_review/python_testing_review.md) |
| 6 | Final report | Executive summary, go/no-go decision, roadmap | [Python](final_report/python_final_report.md) |

**Estimated effort:** 1–16 hours depending on how many phases you complete and the size of the codebase.

---

## Choose your review depth

| Mode | Who it’s for | Phases to run | Time |
| --- | --- | --- | --- |
| ⚡ Quick scan | Hotfixes and small PRs | 1 → 2 → 6 | ~1–2 h |
| 🎯 Standard review | Feature work and medium releases | 1 → 2 → 3 → 6 | ~3–4 h |
| 🔍 Comprehensive audit | Major releases, new projects, pre-production | 1 → 2 → 3 → 4 → 5 → 6 | ~9–16 h |

Mix and match phases when you need targeted insight (e.g., security-only deep dives or testing-focused assessments).

---

## Review details

### Context analysis
**Objective:** Understand the product goals, architecture, dependencies, and review boundaries.

- Clarify documentation quality and architectural fit.
- Identify high-risk areas that deserve extra scrutiny.
- Capture review assumptions and planned checkpoints.

*Python project:** [Context analysis prompt template](context_analysis/python_context_analysis.md)

### Code quality
**Objective:** Evaluate readability, maintainability, and adherence to standards.

- Check naming, structure, modularity, and documentation.
- Highlight complexity hotspots and refactoring opportunities.
- Record strengths alongside improvement ideas.

**Python project:** [Code quality review prompt template](code_quality/python_code_quality.md)

### Security review
**Objective:** Surface vulnerabilities, insecure defaults, and threat models.

- Validate input handling, authentication, and authorization paths.
- Assess dependency risk (packages, versions, SBOM items).
- Provide severity-labelled findings with mitigation guidance.

**Python project:** [Security review promtp template](security_review/python_security_review.md)

### Performance review
**Objective:** Measure efficiency and headroom for growth.

- Look for algorithmic bottlenecks and resource leaks.
- Evaluate caching, concurrency, and scalability strategies.
- Recommend profiling experiments or production safeguards.

**Python project:** [Performance review prompt template](performance_review/python_performance_review.md)

### Testing review
**Objective:** Assess test depth, reliability, and automation coverage.

- Inspect unit, integration, and end-to-end suites.
- Confirm edge cases, error handling, fixtures, and mocks.
- Outline coverage gaps with prioritized remediation steps.

**Python project:** [Testing review prompt template](testing_review/python_testing_review.md)

### Final report
**Objective:** Summarize review outcomes and chart the remediation roadmap.

- Assign a health score and deployment recommendation.
- Consolidate findings by severity and owning team.
- Propose follow-up actions with estimated effort.

**Python project:** [Final report prompt template](final_report/python_final_report.md)

---

## Best practices

- **Stay sequential on first pass.** Each phase sets context for the next and reduces redundant digging.
- **Cite evidence.** Annotate findings with file paths, line numbers, and screenshots when needed.
- **Balance critique and praise.** Recognize good patterns to reinforce team habits.
- **Validate with humans.** Treat AI-generated insights as drafts—verify anything high-severity before escalating.
- **Track remediation.** Create tickets, owners, and due dates for every actionable item.

---

## Support

- **Language coverage:** Python prompts are ready today; JavaScript, Java, C#, Go, and Rust variants are planned for a future release.
- **Need a bird’s-eye view?** Start at the repository [root README](../README.md) for directory-wide guidance.
- **Questions or ideas?** Open an issue or share feedback with your review lead so the templates can keep improving.

*Last updated: October 2025*
*Current Templates: Python (6 phases complete)*

[↑ Back to Repository Root](../README.md)
