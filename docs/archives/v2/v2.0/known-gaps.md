# Known Gaps -- v2.0.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/archives/v2/v2.0/plans/nexus-hub-rename.md](plans/nexus-hub-rename.md)
**Status**: finalized
**Last updated**: 2026-05-20 (Phase 8 post-tag asset integration; DF-004 closed with the nexus_hub_banner / nexus_hub_primary / nexus_monochrome PNG assets dropped into `assets/` by the user from another machine, the README hero now renders the banner via `<img src="assets/nexus_hub_banner.png">` and the "How Nexus-Hub fits with Nexus" section shows the two sibling brand marks side-by-side, and `LICENSE-ASSETS.md` is authored at repo root. One remaining open item is DF-005 (`README_zh.md` v1.0.0 historical block, intentional deferral from Phase 6).)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 1 | 4 |
| BG -- Bug or unresolved test failure | 0 | 1 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 0 | 2 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **1** | **7** |

> Post-tag asset integration closes DF-004: the user landed the five Nexus / Nexus-Hub brand PNGs into `assets/` from another machine (`nexus_hub_banner.png` 1983 x 793, `nexus_hub_primary.png` 919 x 919, `nexus_primary.png` 607 x 596, `nexus_monochrome.png` 507 x 477, `nexus_monochrome_full.png` 620 x 596), and a follow-up commit on main rewrites the README hero to render `nexus_hub_banner.png`, adds a side-by-side `nexus_hub_primary` + `nexus_primary` visual to the "How Nexus-Hub fits with Nexus" section, and authors `LICENSE-ASSETS.md` at repo root documenting the inventory, licensing, and brand-usage guidance. Phase 8 sub-task 8.3 had already closed WN-001 and WN-002 in the tagged b1f2e67 commit. The only remaining open item is DF-005 (`README_zh.md` v1.0.0 historical block), an intentional deferral from Phase 6 that is non-blocking for the v2.0.0 release.

## Open Items

### DF-005 -- `README_zh.md` v1.0.0 historical block preserves the old "DevAI-Hub" name intentionally

**Source phase**: Phase 6, sub-task 6.3 (nested-READMEs sync).
**Plan reference**: [docs/archives/v2/v2.0/plans/nexus-hub-rename.md](plans/nexus-hub-rename.md) sub-task 6.3 and Phase 6.4 stability gate step 1 ("matches are allowed only inside an explicit 'renamed from' / migration callout block"). [docs/archives/v2/v2.0/rename-decisions.md](rename-decisions.md) version-semantics rule -- historical CHANGELOG-style content is preserved as-is to reflect the release as it happened.
**Reason**: `README_zh.md` is a Chinese-language snapshot of the v1.0.0 README (no v1.1+ content was ever translated). Its "v1.0.0 更新内容" block is a historical release-notes snapshot describing the v1.0.0 release when the project was still named DevAI-Hub. The Phase 6 sync renamed the H1 (DevAI Hub -> Nexus-Hub), the immediate tagline, the three live-prose sentences ("DevAI-Hub 提供两个", "**DevAI Hub** 是一套", "安装 DevAI-Hub 工具包"), and added an explicit `> v2.0.0 起原 DevAI-Hub 已重命名为 Nexus-Hub` notice at the top. The 5 remaining `DevAI-Hub` references inside the v1.0.0 historical block are intentional under the same policy that keeps `CHANGELOG.md` historical blocks unchanged.
**Suggested next step**: No action for v2.0.0. If a future release retranslates `README_zh.md` from scratch to align with the new English README, the historical block migrates to a separate `docs/archive/v1/v1.0/RELEASE_NOTES_zh.md` (the same shape v0.x history follows). Until then, the explicit rename notice at the top satisfies the Phase 6.4 callout rule.

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| DF-001 | `data/skills.json` and `data/SKILL_INDEX.md` regeneration deferred until after Phase 5 | Phase 5 sub-task 5.1 (sweep) + BG-001 (parked follow-up) | The Phase 5.1 catalog sweep removed every DevAI string from `catalog/`, which was the precondition DF-001 named. The downstream re-run of `make build-catalog` is parked behind BG-001 because the builder source itself still carries DevAI literals; the data/ files manually edited in Phase 2 remain the source-of-truth until the builder is renamed in Phase 7. |
| DF-002 | End-to-end installer smoke deferred to Phase 4 close | Phase 4 sub-task 4.1 | The three `extensions/nexus-*` directories now exist on disk, so the installer's MCP-server install branch is no longer skipped. The cross-platform installer dry-run prescribed by plan sub-task 8.2 is still owed and will be captured to `docs/archive/v2/v2.0/installer-smoke-post.txt` during Phase 8.2; the *Phase 4* deferral specifically is closed. |
| DF-003 | `scripts/devai_mcp_benchmark.py` rename pulled into Phase 3 ahead of plan | Phase 4 sub-task 4.1 + 4.3 | The extension package rename in Phase 4.1 unblocks `python scripts/nexus_mcp_benchmark.py --help`, which now runs end-to-end (verified at Phase 4.3 close). The `scripts/Install-DevAI-Permissions.ps1` -> `scripts/Install-Nexus-Hub-Permissions.ps1` rename in 4.3 closes the rest of the Phase 4.3 scope. |
| BG-001 | Hardcoded DevAI literals in `infrastructure/tools/build_skills_catalog.py` regressed `data/` on regeneration | Phase 7 sub-task 7.1 follow-up | Fixed in the same commit as the Phase 7 doc / config / devlog / gitignore sync. Four hardcoded literals updated: two `https://github.com/bendourthe/DevAI-Hub` -> `https://github.com/bendourthe/Nexus-Hub`, one `# DevAI-Hub Skill Index` H1 -> `# Nexus-Hub Skill Index`, one `'description': 'Comprehensive catalog of DevAI-Hub skills ...'` -> `'... Nexus-Hub skills ...'`. The builder is now safe to re-run via `make build-catalog`. |
| WN-001 | Pre-existing 4 framework-specialist orphan-bundle warnings (carried since v1.1.5) | v2.0.0 Phase 8 sub-task 8.3 | Closed by adding a `## References` section above `## Related Skills` in `fastapi-expert/SKILL.md`, `nextjs-expert/SKILL.md`, and `react-expert/SKILL.md`, linking the 4 orphan files (`dependency-injection-patterns.md`, `data-fetching-patterns.md`, `performance-patterns.md`, `testing-recipes.md`) with one-line topic summaries. Post-fix `python scripts/validate_skills.py --bundles-only` reports 0 errors / 0 warnings (was 0 errors / 4 warnings). |
| WN-002 | `make` and `shellcheck` unavailable on Windows; cp1252 default codec breaks inline `python -c json.load` | v2.0.0 Phase 8 sub-task 8.3 | Closed by patching the four inline `python -c "import json; d = json.load(open(...))"` invocations in the `validate` target of `Makefile` to pass `encoding='utf-8'`, plus writing `docs/dev-environment-windows.md` to document Scoop install paths for `make` and `shellcheck` and how to set `PYTHONUTF8=1` either persistently or per-session. `make validate` now succeeds on Windows once Scoop has installed `make`. |
| DF-004 | Nexus / Nexus-Hub brand PNG assets deferred at Phase 6 because the sibling Nexus repo was not on the dev machine | v2.0.0 post-tag asset integration (this commit) | User landed five PNGs into `assets/` from another machine: `nexus_hub_banner.png` (1983 x 793, wide banner with wordmark for the README hero), `nexus_hub_primary.png` (919 x 919, square brand mark), `nexus_primary.png` (607 x 596, sibling Nexus brand mark for side-by-side visualizations), `nexus_monochrome.png` (507 x 477, shared monochrome mark), `nexus_monochrome_full.png` (620 x 596, shared monochrome mark with full square frame). README hero rewritten to render `<img src="assets/nexus_hub_banner.png" width="640">` replacing the prior text-only `<strong>Nexus-Hub</strong>` block; "How Nexus-Hub fits with Nexus" section gains a side-by-side `nexus_hub_primary` + `nexus_primary` visual (120 px each) to make the two-project relationship instantly recognizable. `LICENSE-ASSETS.md` authored at repo root with the full asset inventory table, license terms (same as the rest of the repo, internal-only sibling reuse), and brand-usage guidance (when to use banner vs square vs monochrome, when to use the Nexus vs Nexus-Hub variant). |

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 2 (per-phase append), swept by `/wrap-up-session` Phase 4 step 4b (catch-all from live conversation), and finalized by `/update-version` at the v2.0.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
