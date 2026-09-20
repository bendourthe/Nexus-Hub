# Session history - v4.11.0 Phase 1

Renumber note, 2026-09-14: this historical cache-track evidence was authored under v4.11.0; its current plan is v4.11.1. Historical test results and phase dates remain unchanged.

**Plan**: [v4.11.0-adoption-cache-and-diagram-quality](../../../../../releases/v4/v4.11/plans/v4.11.1-adoption-cache-and-diagram-quality.md)
**Phase**: 1 - Cache accounting and baseline
**Date**: 2026-09-10
**Branch**: `feat/v4.11.0-cache-and-diagram`
**Evidence**: [phase-1-cache-accounting.md](../../../../../releases/v4/v4.11/development/phase-1-cache-accounting.md)

## Context

This plan occupied the v4.12.0 slot when it was written. The maintainer swapped it with the sole-contributor attribution plan before implementation began, so the cache and diagram work ships first as v4.11.0 and the attribution rewrite moves to v4.12.0. The swap is published separately as PR #195; this branch is stacked on it.

## Subtasks completed

- **T001** - Recorded the existing-owner baseline, the test and installer boundary, and the reproduced 900% defect. Confirmed the cache telemetry fields have exactly one consumer in the repository, so the correction has no downstream caller to migrate.
- **T002** - Corrected the cache-share example to sum all three input buckets, added explicit unknown handling for missing and untrustworthy telemetry, and removed the implication that a token proportion is money saved.
- **T003** - Added the regression, ran lint, format, the native fast profile, and the real Windows installer boundary; recorded limitations and CI impact.

## Files changed

- `catalog/skills/ai-development/prompt-engineering/references/step-8-optimize-cost-and-latency.md` - corrected example, worked-outcomes table, two explanatory paragraphs.
- `tests/skills/test_cache_share_example.py` - new; 18 tests executing the shipped snippet.
- `docs/releases/v4/v4.11/development/phase-1-cache-accounting.md` - new; phase evidence.

## Test results

18 new tests pass. Lint clean after one automatic reformat. Native `fast` profile: 13 passed, 0 failed. Real Windows installer smoke: PASS, with the redirect verified against the real profile's modification time.

## Deviations

None. No `# DEVIATION:` marker was introduced.

## Plan delta

**Disposition: No delta.**

Evidence: Phase 1 as written matched the codebase. T001's named inputs all existed at the stated paths. The defect reproduced exactly as the comparison described it, at the predicted magnitude. The plan's assumption that `tests/skills/` is already collected by the full profile was checked against `scripts/ci/profiles.py` and holds, so the anticipated coverage question resolved without a profile edit. The plan's allowance for host-unavailable installer evidence was needed for the Linux and macOS legs and used as written.

One judgement the plan left open was resolved rather than deviated from: T002 says to "preserve legitimate optional zero fields only when the documented usage schema supplies that default". The implementation treats `input_tokens` as required and the two cache buckets as optional-defaulting-to-zero, which distinguishes a supported no-cache response from missing telemetry as D1 requires.

Consequence for remaining phases: none. Phase 2 extends the same file and can rely on `cache_read_share` existing as the single accounting entry point. Phase 3's separate reference is unaffected. Phases 4-6 are untouched by this finding.

## CI/CD

No pipeline file was changed. One new test path, already covered by the existing `TESTS` group. Nothing carried forward to the Phase 6 terminal reconciliation.

## Next steps

Phase 2 (T004-T006) adds the cache-stability checklist to the same owner and connects the SDK and token-optimization owners by handoff link. It requires refreshing official prompt-caching, effort, cache-diagnostics and mid-conversation-system-message sources with fetch dates.
