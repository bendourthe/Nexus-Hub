# docs/ cleanup audit -- Phase 6 (v2.2.0)

Audit-only pass produced at the end of /implement-phase 6 (the final phase of v2.2.0). No files were moved or deleted.

## Findings

| Path | Category | Notes |
|---|---|---|
| docs/archive/v2/v2.2/RELEASE_NOTES.md | 4 (active) | New artifact authored in Phase 6 (T036). Canonical v2.2.0 user-facing narrative. |
| docs/archive/v2/v2.2/installer-smoke-post.txt | 4 (active) | New artifact authored in Phase 6 (T038). Cross-OS smoke results: Windows PASS; macOS / Linux deferred. |
| docs/archive/v2/v2.2/known-gaps.md | 4 (active) | Updated for Phase 6 close (T039); status now reads "finalized for v2.2.0 release". |
| docs/archive/v2/v2.2/docs-cleanup-report-phase6.md | 4 (active) | This file. |
| CHANGELOG.md | 4 (active) | `## [2.2.0] - 2026-05-22` block added (T037); `## [Unreleased]` reset to `(none)`. |
| AGENTS.md | 4 (active) | Catalog count rebaselined to 206 / 40 / 22 / 10 (T039). |
| .claude-plugin/plugin.json, data/marketplace.json, scripts/installer.{sh,ps1} | 4 (active) | Version strings bumped 2.1.1 -> 2.2.0 (T039). |
| docs/archive/v2/v2.2/eval-baseline.md | 4 (active) | Re-verified during T038 (baseline reproduces 100% recall / 63.3% precision byte-for-byte). |
| docs/archive/v2/v2.2/docs-cleanup-report-phase2.md | 3 (stale-flag candidate) | Prior-phase audit-only report. Leave in place. |
| docs/archive/v2/v2.2/docs-cleanup-report-phase4.md | 3 (stale-flag candidate) | Same as above for Phase 4. |
| docs/archive/v2/v2.2/docs-cleanup-report-phase5.md | 3 (stale-flag candidate) | Same as above for Phase 5. |
| docs/archive/v2/v2.2/development/history/ | 4 (active) | Will receive a Phase 6 session-history entry in sub-step 8.8. |

## Summary

Cat 1: 0   Cat 2: 0   Cat 3: 3 (prior-phase reports, informational only)   Cat 4: 8 (active)

## Layout canonicalization status

`docs/archive/v2/v2.2/` is currently in the **legacy flat layout** (`docs/<vSEMVER>/`). The canonical v2.1.1+ layout is `docs/versions/v<MAJOR>/v<SEMVER>/`. v2.2.0 deliberately preserves the legacy flat layout because:

1. v2.2.0 work was scoped to CodeGraph adoption + Antigravity CLI transition; a path migration would expand scope.
2. `/refactor-docs --canonicalize-layout` is available in v2.1.1+ and can be run as a standalone cleanup at any time without requiring a version bump.
3. Mid-version path churn (canonicalizing during v2.2.0) would create reference-update churn across every plan / report / RELEASE_NOTES file. Better to do it cleanly at the v2.2.0 -> v2.3.0 boundary if desired.

The legacy flat layout is preserved by design; no migration is required for v2.2.0 release.

## Action required this phase

None. All Cat 4 files are intentional v2.2.0 artifacts; Cat 3 files are prior-phase historical record and will be archived alongside the rest of v2.2.0 docs at the eventual version bump per the v2.1.0 precedent.
