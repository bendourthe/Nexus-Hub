# Dead Code Removal Plan Template

Reference template for identifying, categorizing, and safely removing dead code. Used by the `code-quality` skill during Phase 2 of code review.

---

## Priority Levels

| Priority | Scope | Timeline |
|----------|-------|----------|
| **P0** | Security risk, blocking issue, or actively confusing | Immediate |
| **P1** | Significant maintenance burden, measurable impact | Current sprint |
| **P2** | Minor dead code, low impact | Backlog |

---

## Safe to Remove Now

Use this table for code that can be deleted in the current review with confidence.

| Field | Description |
|-------|-------------|
| **Location** | File path and line range |
| **What** | Brief description of the dead code |
| **Rationale** | Why it is dead (unreachable, unused, feature-flagged off with no plan to enable) |
| **Evidence** | How you verified it is unused (grep results, call graph analysis, coverage data) |
| **Impact** | What changes when it is removed (nothing, reduced bundle size, simplified API) |
| **Deletion steps** | Ordered steps to remove safely (delete function, remove import, update tests) |
| **Verification** | How to confirm nothing broke (run tests, check build, verify no runtime errors) |

### Template

```markdown
### [Dead Code Title]

| Field | Value |
|-------|-------|
| Location | `src/utils/legacy.py:42-87` |
| What | `format_legacy_date()` function |
| Rationale | No callers found in codebase; replaced by `format_date()` in v2.1 |
| Evidence | `grep -r "format_legacy_date" .` returns only the definition |
| Impact | None; function is not imported anywhere |
| Deletion steps | 1. Delete function 2. Remove from `__init__.py` exports 3. Delete test |
| Verification | `pytest`, `mypy`, build passes |
```

---

## Defer Removal (Requires Planning)

Use this table for code that cannot be safely removed right now but should be tracked for future removal.

| Field | Description |
|-------|-------------|
| **Location** | File path and line range |
| **What** | Brief description |
| **Why defer** | What prevents immediate removal (external consumers, runtime reflection, feature flag with active experiment) |
| **Preconditions** | What must be true before removal is safe |
| **Breaking changes** | What would break if removed today |
| **Migration plan** | Steps to move consumers off this code |
| **Timeline** | Target date or milestone for removal |
| **Owner** | Who is responsible for executing the removal |
| **Validation** | How to confirm removal is safe when preconditions are met |
| **Rollback plan** | How to restore if removal causes issues |

### Template

```markdown
### [Deferred Removal Title]

| Field | Value |
|-------|-------|
| Location | `src/api/v1/endpoints.py` |
| What | Entire v1 API module |
| Why defer | 3 external clients still using v1; deprecation notice sent |
| Preconditions | All clients migrated to v2 (tracked in JIRA-1234) |
| Breaking changes | v1 API consumers would get 404 |
| Migration plan | 1. Monitor v1 usage metrics 2. Contact remaining clients 3. Set sunset date 4. Remove |
| Timeline | After Q2 migration deadline |
| Owner | API team lead |
| Validation | v1 request count drops to 0 for 30 consecutive days |
| Rollback | Re-deploy previous version with v1 module intact |
```

---

## Pre-Removal Checklist

Before removing any code, verify all of the following:

- [ ] **Codebase reference search**: No remaining callers found (`grep`, IDE "find usages", `rg`)
- [ ] **Dynamic/reflection usage check**: Code is not accessed via reflection, dynamic import, string-based lookup, or configuration
- [ ] **External consumer verification**: No external packages, services, or clients depend on this code
- [ ] **Feature flag telemetry**: If feature-flagged, confirm the flag has been off for a sufficient period with no plans to re-enable
- [ ] **Test updates**: Related tests are updated or removed alongside the dead code
- [ ] **Documentation updates**: References in docs, README, API docs, and comments are removed
- [ ] **Team notification**: Team is informed of the removal (especially for shared/library code)

---

## Usage

During code quality review (Phase 2):

1. **Identify candidates**: Scan for unused functions, unreachable branches, commented-out code, feature-flagged-off code
2. **Categorize**: For each candidate, determine "safe to remove now" vs "defer with plan"
3. **Fill in the appropriate template** with evidence and steps
4. **Include in the final report** under the "Removal/Iteration Plan" section
5. **Classify severity**: P0 if the dead code poses a security or confusion risk, P2-P3 for routine cleanup
