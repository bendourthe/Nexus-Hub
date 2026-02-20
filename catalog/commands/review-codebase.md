---
description: Perform a comprehensive senior-level review of the entire codebase, producing structured findings, a remediation roadmap, restructuring recommendations, and a full test coverage analysis.
---

# Review Codebase Command

Perform a senior-engineer and technical-lead-level review of this codebase. The goal is not just to find bugs, but to produce a complete picture of the codebase's health, and a prioritized roadmap for making it more correct, secure, maintainable, and well-tested.

This command combines deep code review with architectural analysis and test pipeline auditing. The output is a consultant-grade deliverable saved to `/docs/<version>/review.md`.

---

## Review Mode

Determine the review scope based on the user's request:

- **Full Codebase** (default): All 8 phases across the entire codebase.
- **Git Changes**: If the user mentions "changes", "diff", "PR", "commit", or "what I changed", scope the review to current git changes. Begin with:
```bash
git status -sb
git diff --stat
git diff
```

**Edge case handling:**
- No changes detected: Inform the user and ask if they want staged changes (`git diff --cached`) or a specific commit range.
- Large diff (>500 lines): Summarize by file first, then review in batches grouped by module or feature area.
- Mixed concerns: Group findings by logical feature area, not file order.

---

## Severity Classification

All findings use the P0-P3 scale consistently across all phases.

| Level | Alias | Description | Required Action |
|-------|-------|-------------|-----------------|
| P0 | CRITICAL | Security vulnerability, data loss risk, correctness bug | Must fix immediately; blocks merge/release |
| P1 | HIGH | Logic error, significant SOLID violation, performance regression, missing critical test coverage | Should fix before merge or release |
| P2 | MEDIUM | Code smell, maintainability concern, redundancy, suboptimal structure | Fix in this sprint or create a tracked follow-up |
| P3 | LOW | Style, naming, minor suggestion, opportunistic improvement | Optional; address if effort is low |

Restructuring and simplification recommendations use the same scale, where severity reflects the risk or drag cost of *not* acting rather than a defect severity.

---

## Pre-Analysis: Collect Before Writing

Before writing any section of the report, complete all 8 phases of analysis. Collect all findings into an internal working set first, then write the report in a single pass. This prevents early sections from contradicting later discoveries.

**Exclude from all analysis:**
- `node_modules/`, `vendor/`, `.venv/`, `dist/`, `build/`, `out/`
- Generated files (headers like `// generated`, `# auto-generated`)
- Binary files and lock files (`package-lock.json`, `yarn.lock`, `poetry.lock`)
- The `/docs` directory itself

---

## Analysis Caching

If `docs/<version>/analysis.md` already exists (produced by the `analyze-codebase` command), read it as Phase 1 context rather than re-running the analysis from scratch. Note in the report header that a cached analysis was used and state its timestamp. If it does not exist, run the full analysis as Phase 1.

---

## 8-Phase Review Process

### Phase 1: Context Analysis

Map the codebase before making any judgments. Findings from this phase inform all subsequent phases.

- Identify project type, purpose, and target users.
- Map the architecture: entry points, major components, data flow, integration points.
- Identify the technology stack (language, frameworks, key dependencies, infrastructure).
- Note the organizational pattern of the codebase (layered, feature-based, domain-driven, etc.).
- In git-changes mode: identify which critical paths (auth, payments, data writes, external calls) are touched by the changes.

Output: an internal context map used to ground all subsequent findings.

---

### Phase 2: Code Quality, SOLID, and Dead Code

Evaluate the internal quality of the codebase at the module and function level.

**Readability and maintainability:**
- Function and variable naming (descriptive vs. cryptic).
- Function length and single-responsibility adherence.
- Nesting depth and cognitive complexity.
- Comment quality (explaining *why*, not *what*).
- Consistent error handling patterns.

**SOLID diagnostic (evaluate each module):**
- Single Responsibility: does this class/module have more than one reason to change?
- Open/Closed: is behavior extended via new code, or by modifying existing code?
- Liskov Substitution: do subtypes behave correctly in place of their supertypes?
- Interface Segregation: are interfaces lean, or do implementers depend on methods they don't use?
- Dependency Inversion: do high-level modules depend on abstractions, not concretions?

**Code smells to detect:**
Long methods, feature envy, data clumps, primitive obsession, shotgun surgery, duplicate logic, deep nesting, magic numbers/strings, speculative generality, inappropriate intimacy between modules.

**Dead code identification:**
- Unreachable code paths.
- Unused exports, functions, variables, and imports.
- Commented-out code blocks.
- Feature flags that are permanently enabled or disabled.
- Classify each candidate as: safe-delete-now or defer-with-plan (with rationale).

**`TODO`/`FIXME`/`HACK` audit:**
Enumerate all such comments. For each, assess whether it represents tracked work, forgotten debt, or an active workaround that should be formalized.

---

### Phase 3: Security Review

Scan across all 10 security domains. For each finding, document both exploitability and impact.

1. **Input/Output Safety**: XSS, SQL/command injection, SSRF, path traversal, unsafe deserialization.
2. **Authentication and Authorization**: missing auth guards, tenant isolation gaps, privilege escalation, IDOR.
3. **JWT and Token Security**: algorithm confusion, missing expiry, insecure storage, missing revocation.
4. **Secrets and PII**: hardcoded credentials, secrets in logs or error messages, PII exposure in responses or storage.
5. **Supply Chain and Dependencies**: known vulnerable packages (check against CVE/advisory data), unpinned versions, overly broad dependency trees.
6. **CORS and Security Headers**: misconfigured CORS, missing CSP, HSTS, X-Frame-Options, referrer policy.
7. **Runtime Risks**: unbounded loops, missing timeouts, ReDoS-vulnerable regex patterns, uncaught exceptions in critical paths.
8. **Cryptography**: weak algorithms, hardcoded salts/IVs, improper key management.
9. **Race Conditions**: shared mutable state, TOCTOU vulnerabilities, database concurrency gaps, distributed system coordination issues.
10. **Data Integrity**: missing validation at trust boundaries, inconsistent state transitions, lack of idempotency where required.

---

### Phase 4: Performance Review

Identify performance risks and anti-patterns.

- **Hot path analysis**: CPU-intensive operations, synchronous I/O blocking async contexts, large payload processing.
- **Database and query patterns**: N+1 queries, missing indexes (inferred from query patterns), unbounded result sets, missing pagination.
- **Caching**: presence and correctness of caching strategy, TTL appropriateness, cache invalidation correctness, stampede risk, key collision potential.
- **Memory**: unbounded collections, large object retention, missing cleanup in long-running processes.
- **Concurrency**: blocking operations in async contexts, thread pool exhaustion risk, missing backpressure.
- **Build and bundle**: unnecessary dependencies inflating bundle size, tree-shaking gaps (for frontend codebases).

---

### Phase 5: Testing Audit

This phase goes beyond coverage metrics. The goal is to determine whether the test suite would actually catch regressions, and to produce a clear map of what is tested and what is not.

#### 5a. Test Inventory

- Enumerate all test files and classify each by type: unit, integration, end-to-end, contract, snapshot, performance, smoke.
- Map each test file to the production module or feature it covers.
- Note the test runner, assertion library, mocking framework, and any test utilities in use.
- Identify any test infrastructure (fixtures, factories, test databases, mock servers).

#### 5b. Coverage Analysis

- Assess line, branch, and function coverage where data is available. If not available, infer from test inventory.
- Identify which modules, features, and critical paths have no corresponding tests.
- Assess test type balance against the standard heuristic: ~70% unit, ~20% integration, ~10% E2E. Note deviations and whether they are appropriate for the project type.

#### 5c. Test Quality Assessment

Evaluate whether existing tests are actually useful, not just present.

- **AAA pattern**: are tests structured as Arrange, Act, Assert?
- **Naming**: does the test name describe the scenario and expected outcome?
- **Isolation**: do tests have hidden dependencies on each other, global state, or execution order?
- **Assertions**: are assertions specific, or do tests pass trivially (e.g., asserting a function returns something truthy)?
- **Mocking discipline**: are mocks testing implementation details rather than behavior?
- **Flakiness**: are there tests that are conditionally skipped, sleep-based, or known to be unreliable?
- **Speed**: are slow tests separable from the fast test suite?

#### 5d. Feature-to-Test Mapping

Produce a table mapping every significant feature or user-facing capability to its test coverage status.

| Feature / Capability | Unit Tests | Integration Tests | E2E Tests | Coverage Assessment |
|----------------------|------------|-------------------|-----------|---------------------|
| [Feature name] | Yes / Partial / No | Yes / Partial / No | Yes / Partial / No | Adequate / Gap / Critical Gap |

#### 5e. Use Case and Edge Case Coverage Matrix

For each major workflow or critical path identified in Phase 1, assess whether the following scenario types are covered:

| Workflow | Happy Path | Invalid Input | Auth Failure | Boundary Conditions | External Failure | Concurrent Access |
|----------|------------|---------------|--------------|---------------------|-----------------|-------------------|
| [Workflow] | ... | ... | ... | ... | ... | ... |

Identify edge cases that are present in the code (e.g., null checks, fallback logic, retry handlers) but have no corresponding test exercising that path.

#### 5f. IQ/OQ/PQ Validation Assessment

Evaluate whether the test suite supports formal validation requirements. This is particularly relevant for regulated industries (medical devices, industrial systems, life sciences), but the framing is useful for any production system.

- **IQ (Installation Qualification)**: Is there evidence that the system installs and initializes correctly in a target environment? (Smoke tests, deployment verification scripts, environment validation.)
- **OQ (Operational Qualification)**: Is there evidence that the system operates correctly across its defined operating conditions? (Functional tests against requirements, boundary value tests, failure mode tests.)
- **PQ (Performance Qualification)**: Is there evidence that the system performs correctly under realistic production conditions? (Load tests, stress tests, performance benchmarks, long-running stability tests.)

For each qualification level, assess: present and adequate, partially present, or absent. Note what would be required to close the gap.

#### 5g. Traceability Matrix

Produce a requirements-to-test traceability matrix covering the features and workflows identified in Phase 1. If formal requirements documents are not present, derive requirements from the README, API surface, and observable behavior.

| Requirement / Capability | Source | Test ID(s) | Test Type | Status |
|--------------------------|--------|------------|-----------|--------|
| [Requirement] | README / API / Inferred | [test file:line or test name] | Unit / Integration / E2E | Covered / Partial / Not Covered |

#### 5h. Recommended Test Pipeline

Based on all of the above, describe what a complete, standardized test and validation pipeline would look like for this codebase. Include:

- The recommended test types and their purpose.
- The recommended execution order (fast unit tests first, slow E2E last).
- What should gate a PR merge vs. what runs on a nightly schedule.
- Any test infrastructure gaps that need to be built before certain test types are feasible.

---

### Phase 6: Restructuring and Architecture Opportunities

Evaluate whether the codebase's current structure is the right structure, not just whether the current structure is implemented correctly.

This phase produces recommendations for structural changes that would reduce complexity, improve navigability, align with established patterns, or eliminate architectural debt. Each recommendation must explain the current state, the proposed state, the expected benefit, and the estimated effort (low / medium / high).

#### 6a. Architectural Pattern Alignment

- Does the current architecture match what the project actually needs? (Example: a simple CRUD API that has been over-engineered with unnecessary abstraction layers, or conversely, a complex domain that is under-structured.)
- Are there established architectural patterns (Clean Architecture, Hexagonal, CQRS, MVC, etc.) that would fit better than the current approach?
- Are there architectural seams that would make future scaling or change easier if introduced now?

#### 6b. Module and Boundary Analysis

- Are module boundaries drawn at the right level of abstraction? Are concerns correctly separated?
- Are there modules that have grown beyond their original scope and should be split?
- Are there modules that are so thin they add indirection without value and should be merged or eliminated?
- Are cross-cutting concerns (logging, error handling, auth, validation) handled consistently, or scattered?

#### 6c. Dependency and Coupling Analysis

- Which modules are imported by many others (high fan-in)? Is this appropriate, or does it indicate a god module?
- Which modules have many dependencies (high fan-out)? Do they have too many responsibilities?
- Are there circular dependencies? If so, what restructuring would break the cycle cleanly?
- Are framework or infrastructure concerns leaking into domain logic?

#### 6d. Redundancy and Consolidation Opportunities

- Are there duplicate abstractions serving the same purpose? (Two HTTP client wrappers, two logging utilities, two config loaders.)
- Are there parallel structures that diverged from a common origin and should be reunified?
- Are there vendored or copied implementations of things now available as well-maintained libraries?

#### 6e. Third-Party Platform and Tooling Review

- Are all current third-party platforms and services actively used and earning their integration cost?
- Are there platforms that could be replaced by a simpler in-house solution, or by a different platform that would reduce operational burden?
- Are there tools in the development or build pipeline that are redundant, outdated, or replaceable by tools already present in the stack?
- Are there licensing, cost, or maintenance concerns with any current dependency or platform?

#### 6f. Workflow and Developer Experience

- Is the local development setup straightforward? Are there unnecessary manual steps?
- Is the CI/CD pipeline efficient? Are there slow steps that could be parallelized or cached?
- Are there repeated manual processes that should be scripted or automated?
- Is the project's documentation sufficient for a new contributor to become productive?

---

### Phase 7: Simplification and Optimization Opportunities

Identify where the codebase can be made smaller, faster, or clearer without sacrificing correctness, features, or functionality. Every recommendation in this phase must preserve observable behavior.

#### 7a. Over-Engineering and Unnecessary Abstraction

- Abstractions that exist in anticipation of requirements that have not materialized (YAGNI violations).
- Design patterns applied where simpler code would be equally correct and more readable.
- Configuration systems or plugin architectures more complex than the project's actual variability requires.

#### 7b. Code Volume Reduction

- Logic that can be replaced by a standard library function or a well-established utility already in the dependency tree.
- Verbose implementations of things expressible more concisely with modern language features.
- Hand-rolled implementations of functionality available in already-imported dependencies.

#### 7c. Dependency Rationalization

- Dependencies that are imported for a single utility function and could be replaced by a few lines of inline code.
- Overlapping dependencies that serve similar purposes (two date libraries, two HTTP clients).
- Development dependencies that have leaked into the production dependency list.
- Dependencies that are no longer used at all.

#### 7d. Build and Bundle Optimization

- Unnecessary build steps or transformations.
- Assets or files included in production output that serve no production purpose.
- Opportunities to reduce build time through better caching, parallelism, or scope reduction.

#### 7e. Configuration and Environment Simplification

- Configuration values duplicated across environments that could share a base.
- Feature flags or environment switches that are no longer conditional in practice.
- Deployment configuration more complex than the system's actual operational requirements.

---

### Phase 8: Final Report

Consolidate all findings from all 8 phases into the unified output format below.

---

## Output: Report Structure

Write the report to `<project_root>/docs/<version>/review.md`.

Determine the version using the same priority order as the `analyze-codebase` command: CHANGELOG first, then `package.json`, `pyproject.toml`, `Cargo.toml`, or equivalent manifest. If no version is determinable, use `vUnknown`.

If the file already exists, overwrite it and note the regeneration timestamp in the front matter.

---
```markdown
# Codebase Review: <project name>

**Version**: <version>
**Review Date**: <date>
**Regenerated**: <timestamp> *(only if previously existed)*
**Analysis Source**: Cached from analysis.md (<timestamp>) / Generated fresh
**Reviewer**: Claude Code — review-codebase command
**Review Mode**: Full Codebase / Git Changes
**Files Reviewed**: <count>
**Overall Verdict**: APPROVE / REQUEST_CHANGES / COMMENT

---

## Section 1: Codebase Overview

[From Phase 1. 3-5 paragraphs covering: what the project does, who it serves, its architectural style, technology stack summary, and current state. A reader should be oriented before reading a single finding.]

---

## Section 2: Executive Summary

### Verdict

| Severity | Count |
|----------|-------|
| P0 (Critical) | _ |
| P1 (High) | _ |
| P2 (Medium) | _ |
| P3 (Low) | _ |
| **Total** | _ |

**Verdict rationale**: [1-2 sentences explaining the verdict based on the finding distribution.]

### Critical Issues (P0)

| # | Phase | Location | Issue |
|---|-------|----------|-------|
| 1 | Security | `src/auth/token.ts:42` | JWT algorithm not validated — accepts `none` |
| ... | | | |

### Areas Requiring Most Attention

[Functional groupings showing which areas of the codebase have the highest concentration of issues, with finding counts per area.]

### Restructuring Priority

[3-5 sentence summary of the highest-value structural changes identified in Phase 6, before the detailed section.]

### Simplification Potential

[3-5 sentence summary of the most impactful simplification opportunities from Phase 7.]

### Test Pipeline Gap Summary

[3-5 sentence summary of the most critical test coverage gaps and what the test suite currently cannot catch.]

### Roadmap

**Immediate (P0, fix now):** [List]
**Short-term (P1, before next release):** [List]
**Medium-term (P2, this quarter):** [List]
**Backlog (P3 + strategic restructuring):** [List]

---

## Section 3: Detailed Findings

### 3.1 Code Quality and SOLID

[Findings from Phase 2, grouped by feature area, ordered P0 to P3 within each group.]

[For each finding:]

**[SEVERITY] [Short title]**
- **Location**: `path/to/file.ts:line`
- **Issue**: What is wrong and why it matters.
- **Recommendation**: Specific, actionable fix. Include a before/after code snippet where it aids clarity.

[Dead code removal plan as a table:]

| Item | Location | Classification | Rationale |
|------|----------|----------------|-----------|
| `unusedHelper()` | `src/utils/helpers.ts:88` | Safe-delete-now | No references found anywhere in codebase |
| `legacyAdapter` | `src/adapters/legacy.ts` | Defer-with-plan | Referenced in one deprecated flow still in use |

[TODO/FIXME/HACK audit as a table:]

| Comment | Location | Assessment |
|---------|----------|------------|
| `// TODO: handle error case` | `src/api/handler.ts:201` | Untracked debt — no corresponding issue found |

---

### 3.2 Security

[Findings from Phase 3, ordered P0 to P3.]

[For each finding:]

**[SEVERITY] [Short title]**
- **Location**: `path/to/file.ts:line`
- **Domain**: [One of the 10 security domains]
- **Exploitability**: [Low / Medium / High] — [brief rationale]
- **Impact**: [brief description of what an attacker could achieve]
- **Recommendation**: Specific remediation steps.

---

### 3.3 Performance

[Findings from Phase 4, ordered P0 to P3.]

**[SEVERITY] [Short title]**
- **Location**: `path/to/file.ts:line`
- **Pattern**: [e.g., N+1 query, unbounded collection, blocking I/O]
- **Impact**: [Estimated or observed cost: latency, memory, throughput]
- **Recommendation**: Specific fix with expected improvement.

---

### 3.4 Testing Audit

#### Current Test Inventory

| Test File | Type | Module Covered | Quality Assessment |
|-----------|------|----------------|--------------------|
| `tests/unit/auth.test.ts` | Unit | `src/auth/` | Good — AAA pattern, specific assertions |
| `tests/e2e/login.spec.ts` | E2E | Login flow | Flaky — sleep-based timing |

#### Feature-to-Test Mapping

[Table from Phase 5d]

#### Use Case and Edge Case Coverage Matrix

[Table from Phase 5e]

#### IQ/OQ/PQ Validation Assessment

| Qualification Level | Status | Gap Description |
|--------------------|--------|-----------------|
| IQ (Installation) | Absent | No smoke tests or environment validation scripts |
| OQ (Operational) | Partial | Functional tests exist for happy paths only |
| PQ (Performance) | Absent | No load or stability tests |

#### Traceability Matrix

[Table from Phase 5g]

#### Test Quality Findings

[Specific findings on test quality issues, formatted as the other finding sections.]

#### Recommended Test Pipeline

[From Phase 5h. Prose description of the complete recommended pipeline with a table showing test type, purpose, execution trigger, and estimated run time.]

| Test Type | Purpose | Triggers On | Estimated Duration |
|-----------|---------|-------------|-------------------|
| Unit | Logic correctness | Every commit | < 2 min |
| Integration | Module interaction | Every PR | < 10 min |
| E2E | User flow correctness | Pre-merge to main | < 30 min |
| Performance | Regression detection | Nightly | < 60 min |
| Smoke | Deployment verification | Post-deploy | < 5 min |

---

### 3.5 Restructuring Opportunities

[Findings from Phase 6. Each recommendation follows this format:]

**[SEVERITY] [Short title]**
- **Current state**: Description of what exists now, with file references.
- **Proposed state**: What the restructured version would look like. Include a simplified before/after diagram (Mermaid if the change is structural) where it aids clarity.
- **Expected benefit**: Specific, concrete improvement (reduced coupling, eliminated duplication, improved navigability, etc.).
- **Estimated effort**: Low (< 1 day) / Medium (1-3 days) / High (> 3 days)
- **Risk**: Any risk introduced by the restructuring and how to mitigate it.

[Group findings under sub-headings matching Phases 6a-6f: Architecture, Module Boundaries, Dependency Coupling, Redundancy, Third-Party Tooling, Developer Workflow.]

---

### 3.6 Simplification and Optimization Opportunities

[Findings from Phase 7. Same format as 3.5, grouped under sub-headings matching Phases 7a-7e.]

---

## Section 4: Findings by Priority

[All findings from Sections 3.1 through 3.6, regrouped into a single flat list by severity. Useful as a work queue.]

### P0 — Critical

| # | Phase | Location | Title |
|---|-------|----------|-------|
| 1 | Security | `src/auth/token.ts:42` | JWT algorithm not validated |

### P1 — High

[Same table format]

### P2 — Medium

[Same table format]

### P3 — Low

[Same table format]

---

## Section 5: Export

*Available on request via Next Steps option 7.*

---

## Next Steps

Found X issues (P0: _, P1: _, P2: _, P3: _) plus Y restructuring recommendations and Z simplification opportunities.

**How would you like to proceed?**

1. **Fix all** — Implement all suggested fixes across all severity levels
2. **Fix P0/P1 only** — Address critical and high-priority issues
3. **Fix specific items** — Tell me which issues to address by number
4. **Apply restructuring recommendations** — Implement structural changes (will be done incrementally with confirmation at each step)
5. **Apply simplification recommendations** — Implement simplification opportunities
6. **Build out the test pipeline** — Implement missing tests according to the recommended pipeline
7. **Export report** — Generate Markdown and Word (.docx) versions of this report
8. **No changes** — Review complete, no implementation needed
```

---

## Quality Checks

Before writing the report file, verify:

- [ ] All 8 phases were completed before writing began.
- [ ] Every finding cites at least one specific file path.
- [ ] The feature-to-test mapping covers every significant feature identified in Phase 1.
- [ ] The traceability matrix references real test names or files, not hypothetical ones.
- [ ] Every restructuring recommendation includes a concrete expected benefit and effort estimate.
- [ ] Every simplification recommendation explicitly confirms that the change preserves observable behavior.
- [ ] IQ/OQ/PQ assessment reflects what was actually found, not what is typical.
- [ ] Sections with no findings state explicitly what was checked, what was not found, and any residual risks or recommended follow-up tests.
- [ ] The version string matches the changelog or manifest exactly.
- [ ] Generated, vendored, and build artifact paths were excluded.

---

## Overall Verdict Criteria

- **APPROVE**: No P0 or P1 findings. Code is ready to merge/ship.
- **REQUEST_CHANGES**: Any P0 or P1 findings exist that should be resolved.
- **COMMENT**: No blocking issues, but P2/P3 suggestions are worth considering.

---

## Review-First Paradigm

Do not implement any changes until the user explicitly selects an option from the Next Steps menu. Present the complete report first, then wait.

---

## Iterative Refinement

After producing the report, perform up to 3 internal review passes:

1. **Completeness**: Are there phases with thin findings that warrant deeper investigation?
2. **Accuracy**: Do any findings rely on assumptions that should be flagged?
3. **Actionability**: Is every recommendation specific enough that a developer could act on it without follow-up questions?

Stop when confident the result is thorough, or when 3 passes are complete.
