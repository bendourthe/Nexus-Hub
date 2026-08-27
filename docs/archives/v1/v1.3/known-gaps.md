# Known Gaps -- v1.3.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/archives/v1/v1.3/plans/adoption-pm-claude-skills.md](plans/adoption-pm-claude-skills.md)
**Status**: finalized
**Last updated**: 2026-05-19 (v1.3.0 -> v1.4.0 bump; Phase 6 close; CHANGELOG [1.4.0] block published; version literals bumped in 5 surface files)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 0 | 0 |
| DF -- Deferred (intentionally) | 0 | 0 |
| BG -- Bug or unresolved test failure | 0 | 0 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 2 | 0 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **2** | **0** |

> Status `finalized` at v1.3.0 -> v1.4.0 bump. The 2 open WN items are carry-overs (WN-001 is a long-standing framework-specialists hygiene task; WN-002 is a Windows-dev-environment workaround note). Neither blocks the v1.4.0 release. Both will be re-evaluated when authoring the next plan under v1.4.0+ via `/generate-plan` Step 0.6.

## Open Items

### WN-001 -- Pre-existing orphan-bundle warnings carried from v1.1.5

**Source phase**: Phase 1, sub-task 1.2 (baseline validator run).
**Plan reference**: [docs/archives/v1/v1.3/plans/adoption-pm-claude-skills.md](plans/adoption-pm-claude-skills.md) lines 65-74 (sub-task 1.2 "the 4 pre-existing per-skill bundled-resources orphan warnings ... will be tolerated as carry-over").
**Reason**: `python scripts/validate_skills.py --bundles-only` emits 4 warnings on the framework-specialist bundle: `fastapi-expert/references/dependency-injection-patterns.md`, `nextjs-expert/references/data-fetching-patterns.md`, `react-expert/references/performance-patterns.md`, and `react-expert/references/testing-recipes.md`. None of these references are linked from their parent SKILL.md or from any other `references/*.md` in the same skill. These warnings have carried forward across v1.1.5, v1.2.x, and v1.3.0 (per CHANGELOG.md line 41 they were re-confirmed at v1.3.0 close). The Phase 1 baseline statement in this plan explicitly tolerates them as carry-over.
**Suggested next step**: Either (a) wire each orphan file's content into the parent SKILL.md as a "see references/<file>.md for ..." link, satisfying the A13 reference-rule audit, or (b) inline the content directly into the parent SKILL.md if it is short enough and delete the references file, or (c) leave as carry-over with explicit "expected baseline" annotation in the v1.4.0 plan baseline section. Owner: not Phase 1 of `adoption-pm-claude-skills` -- this is a framework-specialist hygiene task. Track for a future v1.x.x cleanup phase.

### WN-002 -- `make` and `shellcheck` unavailable on Windows dev machine; cp1252 default codec breaks inline `python -c json.load`

**Source phase**: Phase 1, sub-task 1.2 (baseline validator run).
**Plan reference**: [docs/archives/v1/v1.3/plans/adoption-pm-claude-skills.md](plans/adoption-pm-claude-skills.md) lines 65-74 (sub-task 1.2 prescribed `make validate`, `make lint`, `make test`).
**Reason**: The plan's literal commands (`make validate` / `make lint` / `make test`) cannot execute on the user's Windows 11 + PowerShell + Git Bash environment because `make` is not installed and `shellcheck` is not on PATH. The Makefile's `make validate` target uses inline `python -c "import json; d = json.load(open('data/skills.json'))"` which fails on Windows because the Python store distribution defaults to cp1252 for `open()`; `data/skills.json` contains UTF-8 multibyte characters (byte 0x9d at offset 4119, which is undefined in cp1252). The MakefileTargets succeed on Linux/macOS CI because POSIX default `LANG` / `LC_ALL` is UTF-8. On Windows, the equivalent commands must be invoked with explicit `encoding='utf-8'` (verified: all four data JSON files parse cleanly when `open(path, encoding='utf-8')` is used).
**Workaround applied in Phase 1**: All validators were re-run with explicit UTF-8 encoding and via direct Python invocation (`python scripts/validate_skills.py --bundles-only`, `python -m pytest catalog/hooks/tests -q`, per-extension `python -m pytest -q`). Results: 0 errors, 4 expected WN-001 warnings; ShellCheck-equivalent skipped (no shellcheck on this host -- matches the Makefile's "shellcheck not installed -- skipping" branch); MCP suites 37+36(1s)+23 passed; hook tests **366 passed, 3 skipped** (exact baseline match per CHANGELOG.md:40).
**Suggested next step**: Two paths. (a) Patch the Makefile inline commands to pass `encoding='utf-8'` (defensive, single-line change in `Makefile` rule 7-10). (b) Document the Windows dev-environment prerequisites (`scoop install make` or `choco install make`, `scoop install shellcheck`, ensure `PYTHONUTF8=1` in environment) in a `docs/dev-environment-windows.md` so any contributor on Windows can run `make` directly. Owner: a future hygiene phase or cross-OS-CI work (related to the open v1.1.5 DF-003 / QG-001 cumulative cluster on cross-OS installer smoke). Not a blocker for v1.3.0 / v1.4.0 work because the underlying validators all pass when invoked correctly.

## Resolved

_No items resolved in this version yet._

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 2 (per-phase append), swept by `/wrap-up-session` Phase 4 step 4b (catch-all from live conversation), and finalized by `/update-version` at the v1.3.0 -> v1.4.0 bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward to v1.4.0+.
