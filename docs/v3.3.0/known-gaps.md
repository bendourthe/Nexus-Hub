# Known Gaps -- v3.3.0

**Status**: v3.3.0 `adoption-loop-engineering` was RELEASED to `main` (tag `v3.3.0`); the release reconciled the headline counts 251 -> 252 (resolving WN-v33-3). A follow-up **v3.3.1 patch** (branch `fix/loop-engineering-gaps`) then resolved the two residual gaps plus a broader cross-link cleanup: WN-v33-4 (allowlisted the 3 remaining pushy-description skills so the strict `--allow-existing` pass is clean) and BG-v33-1 (removed the dangling `[[generate-session-history]]` wikilink), and -- expanded by maintainer request -- swept ALL 12 catalog-wide dangling `[[old-command]]` wikilinks (the v3.2.0-flagged command-reference residual, in its `[[wikilink]]` form) across ~10 skills, rewriting each to the current `/command` plain-text reference (or, for `typescript-cleanup`, repointing to the real `[[javascript-cleanup]]` skill). The catalog-wide dangling-wikilink audit is now clean (0 unresolved).
**Last updated**: 2026-06-11 (v3.3.1 patch: gap cleanup + dangling-wikilink sweep)

This file tracks per-phase unfinished work, intentional deferrals, bugs, missing tests, warnings, and bypassed quality gates for v3.3.0. The next version's `/plan` ingests the open items here. Category prefixes: `NI` (not implemented / skipped subtask), `DF` (intentionally deferred), `BG` (bug), `MT` (missing test), `WN` (warning / suppressed rule), `QG` (quality gate bypassed).

## Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 0 | 1 |
| BG | 0 | 1 |
| MT | 0 | 0 |
| WN | 2 | 2 |
| QG | 0 | 0 |
| **Total** | **2** | **4** |

## Open Items

| ID | Category | Source phase | Plan reference | Reason | Suggested next step | Severity |
|---|---|---|---|---|---|---|
| WN-v33-1 | WN | adoption-loop-engineering Phase 1; re-confirmed Phase 4 / v3.3.1 | T1.5, T4.5 (Testing and Stabilization) | Local Windows verification is partially emulated: `make` is not on PATH, so `make validate` and `make scan` were run by invoking the underlying validators and the scanner directly. The full direct chain (10 validate steps + the skill-security scan) passed green in Phase 4 and again for the v3.3.1 patch. | Confirm CI `validate` and `scan` are green on the ubuntu runner. No code change expected; alternatively set a writable temp directory for local sandboxed runs. | Low (direct validator/scanner equivalents passed) |
| WN-v33-2 | WN | adoption-loop-engineering Phase 1 | T1.5 (Testing and Stabilization) | Two benign, pre-existing global-audit warnings outside this work: the `demo-capture` orphan `.pyc` is a LOCAL-ONLY artifact (gitignored at `.gitignore:60` `__pycache__/`, never committed, so it cannot appear on a clean CI checkout), and `git-branching-workflow` has a 169-word `overview_l1` soft-limit warning. Neither fails any gate. | Optionally reword `git-branching-workflow`'s `overview_l1` under 150 words in a future content pass; the `.pyc` needs no repo action. | Low (local-only artifact + soft warning; no gate impact) |

## Resolved

| ID | Category | Source phase | Resolved in | Note |
|---|---|---|---|---|
| DF-v33-1 | DF | adoption-loop-engineering Phase 1 | Phase 4 (T4.1) | Added `catalog/skills/workflow/loop-engineering/SKILL.md` to `scripts/validate_skills.allowlist.json` without shortening the description. The strict `--allow-existing` pass now demotes the 496-char description to a warning for this file (warning count moved 1365 -> 1366), and the description is unchanged per the AGENTS.md pushy-description mandate. |
| WN-v33-3 | WN | adoption-loop-engineering Phase 1 | v3.3.0 release | The develop-to-main v3.3.0 release reconciled every headline count-prose surface 251 -> 252: README (x3), AGENTS.md (x2), `data/SKILL_INDEX.md` Total label, `data/marketplace.json` plugin description, and `.claude-plugin/plugin.json` description. `check_version_sync.py` green at 3.3.0; machine-readable registries already agreed at 252. |
| WN-v33-4 | WN | adoption-loop-engineering Phase 4 | v3.3.1 (patch) | Added the 3 remaining pushy-description skills (`ai-attack-patterns`, `pentest-reporting`, `git-branching-workflow`) to `scripts/validate_skills.allowlist.json`. The strict `scripts/validate_skills.py --allow-existing` pass is now CLEAN (0 errors). Descriptions unchanged per the pushy-description mandate. |
| BG-v33-1 | BG | adoption-loop-engineering Phase 4 | v3.3.1 (patch) | Removed the dangling `[[generate-session-history]]` wikilink from BOTH `session-teach-back/SKILL.md` and `session-query/SKILL.md` (the real skill is `session-history`). Expanded by maintainer request into a full catalog-wide dangling-wikilink sweep: all 12 distinct dangling `[[old-command]]` wikilinks (the v3.2.0 command-reference residual, in `[[wikilink]]` form) across ~10 skills were rewritten to the current `/command` plain-text reference (`/plan`, `/review full`, `/review security`, `/review pentest`, `/spec analyze`, `/skills create`, `/update refactor`, `/memory`, `/research deep`), with `[[typescript-cleanup]]` repointed to the real `[[javascript-cleanup]]` and the illustrative `[[links]]` placeholder de-linked. The catalog-wide dangling-wikilink audit is now clean (0 unresolved). NOTE: this resolves the `[[wikilink]]`-form residual only; plain-text old-command mentions in prose remain a separate, larger modernization task. |
