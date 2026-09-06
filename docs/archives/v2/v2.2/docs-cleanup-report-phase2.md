# Docs cleanup audit -- v2.2.0 Phase 2 close

**Mode**: audit-only (no files moved)
**Generated**: 2026-05-21 (Phase 2 / T014 close)
**Scope**: `docs/archive/v2/v2.2/` and adjacent version directories

This audit ran as sub-step 8.5 of `/implement-phase` for v2.2.0 Phase 2. No files were moved; the report is informational and feeds the final-phase release-readiness workflow.

## Summary

| Category | Count |
|---|---|
| Cat 1 -- delete | 0 |
| Cat 2 -- archive | 0 |
| Cat 3 -- stale-flag | 1 |
| Cat 4 -- active | 5 (under `docs/archive/v2/v2.2/`) |

## Cat 3 -- stale-flag

| File | Reason | Suggested action |
|---|---|---|
| `docs/archive/v2/v2.2/comparison-antigravity-sdk-python.md` | Pre-existing untracked comparison report from an earlier session (timestamped 2026-05-21 00:00:00Z, before Phase 2 work). Not referenced from the v2.2.0 plan or known-gaps.md; appears to be exploratory work from the v2.1.0 -> v2.2.0 planning window. | Either (a) reference it from the v2.2.0 RELEASE_NOTES / plan / known-gaps if the findings are still relevant, or (b) move to `docs/archive/versions/v2/v2.2.0/comparison-antigravity-sdk-python.md` at v2.2.0 release. Decision deferred to the Phase 6 release-prep step. |

## Cat 4 -- active (under `docs/archive/v2/v2.2/`)

| File | Owner phase |
|---|---|
| `docs/archive/v2/v2.2/antigravity-cli-probe.md` | Phase 2 / T007 (new this phase) |
| `docs/archive/v2/v2.2/antigravity-cli-commands-schema.md` | Phase 2 / T012 (new this phase) |
| `docs/archive/v2/v2.2/known-gaps.md` | Phase 1 (created), Phase 2 (appended) |
| `docs/archive/v2/v2.2/plans/codegraph-and-antigravity.md` | Phase 0 (plan source-of-truth) |
| `docs/archive/v2/v2.2/development/history/` | (history files added per phase by `/generate-session-history`) |

## No files cleaned up this phase

The audit surfaced one Cat 3 candidate (`comparison-antigravity-sdk-python.md`); the default behavior of the audit step is to leave it in place. The user can revisit it during the v2.2.0 final-phase release-readiness workflow or run `/refactor-docs --apply` manually.

## References

- `/refactor-docs` audit-only mode is invoked by `/implement-phase` Phase 8 sub-step 8.5
- Style guide: [catalog/style-guides/markdown.md](../../catalog/style-guides/markdown.md)
- Plan: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md)
