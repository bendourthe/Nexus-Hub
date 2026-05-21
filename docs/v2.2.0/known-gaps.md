# Known Gaps -- v2.2.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md)
**Status**: in-progress (Phases 1-2 closed; Phases 3-6 pending)
**Last updated**: 2026-05-21 (Phase 2 close -- Gemini-to-Antigravity CLI transition landed ahead of the 2026-06-18 sunset: `Antigravity20Integration` now covers both desktop and CLI surfaces (single class, dual coverage in `display_name`); new `antigravity-cli-diff-review` hook ships in both `.sh` and `.ps1` form; `--enterprise` / `-Enterprise` flag gates the standalone Gemini CLI install path with a sunset warning surfaced in the default flow; six per-surface Google instruction templates split out from the shared `base-google-shared.md`; 121 integration + installer tests passed; 16 new test cases added across `test_antigravity.py`, `test_antigravity_commands.py`, and `test_enterprise_flag.py`; `make lint` and per-skill bundle audit clean.)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 1 | 0 |
| BG -- Bug or unresolved test failure | 0 | 0 |
| MT -- Missing tests / coverage gap | 1 | 0 |
| WN -- Warning or suppressed lint rule | 4 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **6** | **0** |

## Open Items

| ID | Title | Category | Source phase | Plan reference | Reason | Suggested next step |
|---|---|---|---|---|---|---|
| DF-001 | Byte-identical parity migration of the original 4 platforms into the integration registry | DF | Carried forward from v2.1.0/known-gaps.md DF-001 | [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) Phase 3 sub-tasks 3.6 and 3.7 | The v2.1.0 plan deferred byte-identical parity tests covering the original 4 platforms (Claude / Gemini / Codex / Copilot) plus Cursor / OpenCode. The plan's Phase 3 in v2.2.0 (sub-tasks T020 / T021) takes the work over, leveraging the new `WriteResult` vocabulary delivered in Phase 1 to assert per-file equivalence. | Phase 3 will write `tests/integrations/test_parity_with_legacy_installer.py` then refactor `installer.sh` / `installer.ps1` to delegate the original platforms to the registry runner. |
| MT-1 | `Copilot` and `Cursor` retain bespoke install paths that bypass the new shared-mode marker write | MT | Phase 1 | [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) Phase 1 sub-task 1.4 | Phase 1.4 routed `MarkdownIntegration._write_instruction` through `merge_marker_section`. Copilot's `install_workspace` uses its own legacy `## Nexus-Hub Harness` append-after-heading pattern and was left untouched to minimize surface change; Cursor's AGENTS.md write was updated to use marker-merge but the `.mdc` rules pipeline still writes raw files. Both subclasses set `instruction_mode = "shared"` for documentation but the attribute is informational on them. | Phase 3's parameterized contract suite (sub-task 3.5) will discover any per-integration drift; the natural follow-up is to refactor Copilot's marker logic to use `merge_marker_section` directly so the legacy `## Nexus-Hub Harness` header is migrated alongside the v2.1 `## Nexus-Hub` legacy header. |
| WN-1 | `pathspec` `GitWildMatchPattern` deprecation warning in `nexus-code-search` tests | WN | Phase 1.6 test review (pre-existing) | n/a (pre-existing) | The Phase 1.6 stabilization run surfaced 52 `DeprecationWarning: GitWildMatchPattern ('gitwildmatch') is deprecated` warnings from the `nexus-code-search` test suite. These predate Phase 1 (the warning lives in `pathspec/pattern.py:125`) but were not previously tracked. Tests pass; no functional impact. | Track as v2.3.0 cleanup; pin the `pathspec` API to `gitignore` mode when next touching `extensions/nexus-code-search`. |
| WN-2 | Antigravity CLI binary name unverified on a live VM | WN | Phase 2 sub-task 2.1 (T007) | [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) Phase 2 sub-task 2.1 (T007) | The Antigravity CLI install-path probe ran as a static analysis (no live VM was available at authoring time on 2026-05-21). The probe inferred the binary name `antigravity` from the parallel Gemini CLI / Antigravity product naming, but this was not confirmed empirically. The new `antigravity-cli-diff-review.sh/.ps1` hook and the AGENTS.md sunset notice hardcode `antigravity` as the PATH name. | Once Google ships the Antigravity CLI to a verifiable user channel (announced for 2026-06-18 sunset cutover), re-run the probe on a live install, update [docs/v2.2.0/antigravity-cli-probe.md](antigravity-cli-probe.md) section 1, and rename the hook scripts + AGENTS.md references if Google ships a different binary name. |
| WN-3 | Antigravity CLI workflow file format unverified on a live VM | WN | Phase 2 sub-task 2.6 (T012) | [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) Phase 2 sub-task 2.6 (T012) | The TOML-vs-Markdown commands schema analysis concluded that Antigravity CLI inherits Antigravity 2.0 desktop's Markdown workflow format (verbatim `.md` files under `~/.agent/workflows/`), not Gemini CLI's `.toml` schema. The conclusion is supported by the documented Antigravity 2.0 desktop behavior and the 2026-05-21 Google announcement of a shared backend, but it was not verified empirically against a live Antigravity CLI install. | Verify on the same live VM as WN-2; if the CLI ships a different format (e.g., custom JSON manifest), add a `_write_antigravity_commands` helper variant to `scripts/lib/integrations/antigravity.py` and re-open T012. |
| WN-4 | Antigravity CLI workflow front-matter / name-derivation schema unverified | WN | Phase 2 sub-task 2.6 (T012) | [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) Phase 2 sub-task 2.6 (T012) section 6 | Whether the Antigravity CLI honors YAML frontmatter in workflow files, and the exact rule it uses to derive the workflow name (filename vs. first H1), are not empirically confirmed. The current Antigravity 2.0 + CLI install path mirrors `catalog/commands/*.md` verbatim, so any future schema rejection by Antigravity CLI would surface as a runtime warning rather than as an install error. | Same live-VM verification as WN-2 / WN-3. If frontmatter is rejected, add a strip pass to `SkillsIntegration._mirror_catalog` (or a dedicated Antigravity helper). |

## Resolved

(none yet -- Phase 1 close)

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 8.4 (per-phase append), swept by `/wrap-up-session` Phase 6 (catch-all from live conversation), and finalized by `/update-version` at the v2.2.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
