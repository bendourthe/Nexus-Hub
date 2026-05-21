# Known Gaps -- v2.2.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md)
**Status**: in-progress (Phase 1 closed; Phases 2-6 pending)
**Last updated**: 2026-05-21 (Phase 1 close -- Installer foundation refactor landed: `WriteResult` action vocabulary, marker-delimited instruction-file merges, MCP `initialize` server-instructions on the three internal MCP servers. 105 + 43 + 42 + 29 = 219 tests passed; smoke install verified byte-identical reinstall surfaces `unchanged` on every action; smoke install verified user content above and below the marker block survives a reinstall.)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 1 | 0 |
| BG -- Bug or unresolved test failure | 0 | 0 |
| MT -- Missing tests / coverage gap | 1 | 0 |
| WN -- Warning or suppressed lint rule | 1 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **2** | **0** |

## Open Items

| ID | Title | Category | Source phase | Plan reference | Reason | Suggested next step |
|---|---|---|---|---|---|---|
| DF-001 | Byte-identical parity migration of the original 4 platforms into the integration registry | DF | Carried forward from v2.1.0/known-gaps.md DF-001 | [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) Phase 3 sub-tasks 3.6 and 3.7 | The v2.1.0 plan deferred byte-identical parity tests covering the original 4 platforms (Claude / Gemini / Codex / Copilot) plus Cursor / OpenCode. The plan's Phase 3 in v2.2.0 (sub-tasks T020 / T021) takes the work over, leveraging the new `WriteResult` vocabulary delivered in Phase 1 to assert per-file equivalence. | Phase 3 will write `tests/integrations/test_parity_with_legacy_installer.py` then refactor `installer.sh` / `installer.ps1` to delegate the original platforms to the registry runner. |
| MT-1 | `Copilot` and `Cursor` retain bespoke install paths that bypass the new shared-mode marker write | MT | Phase 1 | [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) Phase 1 sub-task 1.4 | Phase 1.4 routed `MarkdownIntegration._write_instruction` through `merge_marker_section`. Copilot's `install_workspace` uses its own legacy `## Nexus-Hub Harness` append-after-heading pattern and was left untouched to minimize surface change; Cursor's AGENTS.md write was updated to use marker-merge but the `.mdc` rules pipeline still writes raw files. Both subclasses set `instruction_mode = "shared"` for documentation but the attribute is informational on them. | Phase 3's parameterized contract suite (sub-task 3.5) will discover any per-integration drift; the natural follow-up is to refactor Copilot's marker logic to use `merge_marker_section` directly so the legacy `## Nexus-Hub Harness` header is migrated alongside the v2.1 `## Nexus-Hub` legacy header. |
| WN-1 | `pathspec` `GitWildMatchPattern` deprecation warning in `nexus-code-search` tests | WN | Phase 1.6 test review (pre-existing) | n/a (pre-existing) | The Phase 1.6 stabilization run surfaced 52 `DeprecationWarning: GitWildMatchPattern ('gitwildmatch') is deprecated` warnings from the `nexus-code-search` test suite. These predate Phase 1 (the warning lives in `pathspec/pattern.py:125`) but were not previously tracked. Tests pass; no functional impact. | Track as v2.3.0 cleanup; pin the `pathspec` API to `gitignore` mode when next touching `extensions/nexus-code-search`. |

## Resolved

(none yet -- Phase 1 close)

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 8.4 (per-phase append), swept by `/wrap-up-session` Phase 6 (catch-all from live conversation), and finalized by `/update-version` at the v2.2.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
