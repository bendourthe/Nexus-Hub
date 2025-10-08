# Code Cleanup & Refactoring Review

## Objective
Eliminate dead code, duplication, and legacy patterns so the codebase remains lean, maintainable, and aligned with current architecture decisions.

## Review Checklist

### Dead Code & Drift
- [ ] Unused modules, packages, and entry points identified
- [ ] Dormant feature flags, experiments, or toggles catalogued
- [ ] Deprecated APIs and endpoints mapped to replacement timeline
- [ ] Obsolete configuration values or environment variables removed
- [ ] Unreachable code paths confirmed with coverage/profiling evidence

### Duplication & Consolidation
- [ ] Near-duplicate functions or classes grouped with merge candidates
- [ ] Copy-pasted logic replaced with shared utilities or templates
- [ ] Repeated SQL queries or API calls centralized
- [ ] Configuration defaults unified across services
- [ ] DRY violations documented with recommended abstractions

### Refactoring Readiness
- [ ] Local complexity hotspots captured (cyclomatic, cognitive metrics)
- [ ] Large functions/modules broken into manageable units
- [ ] Legacy construction patterns replaced with modern equivalents
- [ ] Naming aligns with domain language and architecture boundaries
- [ ] Deprecation notices or migration guides drafted where needed

### Regression Safety
- [ ] Critical behaviours covered by unit/integration tests
- [ ] Cleanup changes gated by feature flags or staged rollout plans
- [ ] Observatory signals (logs, metrics, traces) updated
- [ ] Stakeholders notified of breaking removals
- [ ] Rollback strategy documented

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
Please help me run a comprehensive code cleanup and refactoring review for my Python project.

**Project Context:**
- Repository name: [YOUR_REPO]
- Primary domain: [SERVICE / LIBRARY / DATA PIPELINE]
- Critical modules: [LIST]
- Feature flag framework: [None / LaunchDarkly / Custom]
- Known legacy hotspots or incidents: [DETAILS]

---

## Dead Code Assessment

1. Map unused assets:
  - List modules, entry points, and feature flags with zero references
  - Surface deprecated APIs still deployed but unreferenced
  - Identify obsolete configuration values or environment variables

2. Validate removal safety:
  - Cross-check candidates against coverage reports
  - Confirm scheduled jobs, integrations, or CLI tools do not rely on them
  - Highlight any telemetry gaps that need additional verification

## Duplication Review

1. Detect near-duplicate logic:
  - Compare helper functions, SQL queries, serializers, and validation routines
  - Inspect test utilities vs production helpers for overlap

2. Recommend consolidation steps:
  - Extract shared utilities or services where appropriate
  - Parameterize behaviour instead of branching copies
  - Note teams or owners needed for coordination

## Refactoring & Modernization Plan

1. Score refactor candidates (Risk, Impact, Effort) and organize into:
  - Quick wins (≤ 1 day)
  - Near-term refactors (1–2 sprints)
  - Strategic rewrites (multi-iteration)

2. Document modernization guidance:
  - Replace outdated patterns (class-based singletons, global state, etc.)
  - Align naming with domain language and architecture seams
  - Outline migration steps for any public APIs

## Regression Safety & Verification

1. Confirm safeguards:
  - Tests covering affected behaviour (unit/integration)
  - Feature flags or canary plans for risky removals
  - Monitoring or logging updates required post-cleanup

2. Prepare final report detailing:
  - Dead code removal backlog with ownership
  - Duplication hotspots and suggested consolidation path
  - Refactor roadmap with Risk/Impact/Effort notes
  - Test or telemetry gaps that must close before changes ship
  - Follow-up actions for automation (static analysis, coverage diff checks)
~~~

## Expected Outcomes

### Pass Criteria
- Dead code candidates validated with references, coverage, or telemetry
- Duplicate logic mapped to concrete consolidation actions
- Refactoring tasks prioritized with risk mitigation notes
- Regression safeguards (tests, rollout plans) documented
- Stakeholders aligned on timeline and responsibilities

### High-Priority Issues to Flag
- Unused code paths executing in production (e.g., scheduled jobs)
- Critical modules lacking test coverage before cleanup
- Hidden coupling preventing safe removal (shared globals, side effects)
- Deprecated APIs exposed publicly without sunset plan
- Copy/paste security-sensitive logic (auth, encryption) diverging over time

### Recommended Next Steps
- Schedule refactor work into backlog with defined owners
- Automate dead code detection in CI (coverage diff, static analysis)
- Track cleanup metrics (files removed, duplication %, bundle size)
- Share findings with architecture guild and incident response teams
