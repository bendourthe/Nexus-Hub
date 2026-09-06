# Session History - Docs Lifecycle and Retention Phase 4: History Retention Policy

**Date**: 2026-08-21
**Branch**: `feat/docs-lifecycle-retention`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.0-docs-lifecycle-retention.md`](../../plans/v3.18.0-docs-lifecycle-retention.md)
**Phase**: 4 - History retention policy
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12, pytest; GNU Make unavailable, so `make` targets were executed as their constituent commands
**Outcome**: Per-version documentation has a written, linked lifecycle and an advisory checker that reports drift without blocking a release. Two plan corrections were needed: the archive path the plan specified is a legacy layout the project migrated away from, and Phase 3's ceiling left no room for the pointer this phase adds.

## 1. Starting State

- **Starting commit**: `154bbe38` (Phase 3: AGENTS.md ratchet-down, MT-1 closed)
- **Worktree**: clean
- **`AGENTS.md`**: 7,742 words against an 8,150 ceiling, 408 words of headroom (5%)
- **The problem**: `docs/v3/` held 440 Markdown files across 21 minor-version directories with no rule for when any of them stopped being current. `docs/solutions/` had `solution-refresh` and `docs/decisions/` had its own lifecycle; nothing covered `development/`, which is where the volume actually is.

The plan recorded `strong / medium`, which matches the session model. No routing delta.

## 2. Two Plan Corrections

**The archive path.** The plan specifies `docs/archive/versions/v<MAJOR>/` "per the existing docs-layout-refactor archive convention". That is not the existing convention. `docs-layout-refactor` documents `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/` as canonical and explicitly names `docs/archive/versions/v<MAJOR>/v<SEMVER>/` as the **old three-level layout** that a canonicalization pass migrates away from. The repo confirms it: `docs/archive/` contains `v0`, `v1`, `v2` and no `versions/` directory at all.

Writing the plan's literal path would have introduced a second archive layout while a canonicalization pass exists to remove exactly that. The canonical path was used, and the deviation is recorded in the decision record's Consequences.

**The AGENTS.md budget.** The plan says to add the pointer "within the Phase 3 budget". It did not fit. Phase 3 set the ceiling to 8,150, the minimum that clears the policy's 5% headroom floor at 7,742 words, which left effectively zero room for a Phase 4 addition that Phase 3 knew was coming. Adding the pointer took AGENTS.md to 7,832 and headroom back to 4%, reported `<- tight`.

That was a Phase 3 mistake, not a Phase 4 one, and it had two possible fixes: raise a ceiling set the same day, or relocate more content. Section 5 covers the choice.

## 3. The Policy

`docs/policy/docs-retention.md` defines four states:

1. **ACTIVE** - the current minor's directory is unrestricted. It is the working directory of the project and retention pressure there is counterproductive.
2. **CONSOLIDATE at release** - `development/history/` files stay exactly where they are; the release's DEVLOG index line becomes the single entry point. The policy states explicitly that this consolidates *navigation*, not content, because "consolidate" invites a merge and a merged summary destroys the per-phase troubleshooting detail that makes the history worth keeping.
3. **ARCHIVE at two minors behind** - the `development/` subtree moves to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/development/`. Two minors, not one, because a patch release routinely revisits the previous release's decisions, so one minor would move content out from under work in progress.
4. **EXEMPT** - `docs/solutions/`, `docs/decisions/`, `docs/incidents/`, and the living `docs/policy/`, `docs/specs/`, `docs/git/`.

Within an aging version, **only `development/` is swept**. This is the part most likely to be got wrong later, so the policy states the reason: a plan is the durable statement of intent that the DEVLOG index links directly, and a known-gaps file is read forward by the next version's plan to decide what carries over. Archiving either would break the index or the planning loop.

The decision record carries seven rejected alternatives. Two are worth repeating here:

- **A per-file TTL** was rejected as arbitrary. Age in days is not the signal; distance from the current version is. A TTL would archive the previous release's history while it is still the most-consulted content in the tree.
- **Deleting old history** was rejected on concrete evidence from this repository. The per-phase histories hold the troubleshooting record, and this project has already re-diagnosed a hazard from scratch that it had documented two minor versions earlier (the Windows `bash`-resolves-to-WSL-stub PATH shadowing, documented in v3.15.6 and rediscovered in v3.17.6). Deleting that record makes the repeat certain rather than merely likely.

## 4. The Checker

`scripts/check_docs_retention.py` reports and **always exits 0**. The advisory choice is deliberate and the reasoning is in both the script docstring and the policy: archiving repairs references across the repo, so it belongs in a reviewed propose-then-apply pass rather than a per-commit validator; and a hard gate would block an unrelated release the moment a minor aged out, which is a real cost preventing no harm, since nothing breaks when history sits in place a version longer than the rule prefers.

Implementation notes worth carrying:

- The current version is read from `.claude-plugin/plugin.json`, the same source `check_version_sync.py` treats as canonical, so the two cannot disagree about what "current" means.
- An **older major** is wholly historical, so the two-minor distance does not apply to it; a **future** major (`docs/v4/`) is planning rather than history and is never reported. Both cases have tests, because both are easy to get wrong in opposite directions.
- Sorting is numeric, not lexicographic. A plain sort puts `v3.10` between `v3.1` and `v3.2`, which reads as a bug in a report a human is meant to act on.
- Every degradation path (absent `docs/`, unreadable `plugin.json`, malformed JSON, unreadable version directory) returns 0 with a note.

Against this repo it reports **16 versions, 306 files** outstanding. That backlog is the one-time cost of having had no rule; the first archive pass is Phase 5 work.

`tests/validators/test_check_docs_retention.py` covers 15 cases, including a `test_nothing_is_moved_or_deleted` that snapshots the fixture tree before and after. That is the property which makes the checker safe to wire into `make validate` at all, so it is asserted rather than assumed.

## 5. Relocating Model Routing Instead of Re-Raising the Ceiling

Given the budget problem from section 2, the options were to raise the ceiling from 8,150 or to relocate more content.

Relocating won. Raising a ceiling set the same day would make the ratchet a formality: the doc-budgets policy is a ratchet precisely so that the easy response to a breach is to move content, not to move the line. So `## Model Routing in the Plan/Implement Loop` (367 words) moved to `docs/policy/model-routing-in-plan-and-implement.md`. It is a block Phase 3 listed as a candidate and deferred only for margin, it has no external citation by heading name (checked), and it is command and skill behavior rather than always-loaded instruction text, which the relocated file now states in a scope-boundary note against `[[model-routing]]` and `platform-defaults-levers.md`.

Result: AGENTS.md at 7,527 words, 623 words of headroom (8%), ceiling unchanged at 8,150. Total relocated across Phases 3 and 4 is 2,578 words.

## 6. Cross-Links

The plan requires the policy be linked from `AGENTS.md` and cross-linked from three skills. Each cross-link states the *relationship* rather than merely naming the file, because a bare "see also" line is the kind of link that gets skipped:

- `known-gaps-tracker`: that `known-gaps.md` is explicitly exempt, and why (read forward by the next plan).
- `session-history`: the lifecycle of the files it writes (stay at release, archive two minors behind).
- `docs-layout-refactor`: that it **executes** the rule the checker only reports.

## 7. Verification

| Check | Result |
|---|---|
| `check_docs_retention.py` against this repo | exit 0, 16 versions / 306 files reported, destinations named |
| `test_check_docs_retention.py` | 15 passed |
| `validate_doc_budgets.py --list` | AGENTS.md 7,527 / 8,150, +623 (8%), no tight marker |
| `validate_doc_budgets.py` (gate) | PASS, 8 budgeted docs within ceiling |
| `validate_decision_records.py` | PASS, 12 records |
| Link check across all 7 edited/created files | 0 broken (the 3 reported in `docs-layout-refactor` are pre-existing `foo.md` illustrative examples in a table; that file's diff is one line) |
| `validate_skills.py --bundles-only` | PASS, 273 skills |
| `run_trigger_evals.py --gate` | PASS |
| `check_registry_entries.py --check --strict`, `check_base_template_parity.py`, `check_doc_colocation.py`, `validate_unicode_safety.py --strict` | PASS |
| `pytest tests/validators tests/skills catalog/hooks/tests` | see below |
| Installer smoke allowlist | `check_docs_retention.py` added to `DEV_ONLY_SCRIPTS`, so the no-installer-copy rule is asserted rather than assumed |

## 8. Ending State

- **Files added**: `docs/policy/docs-retention.md`, `docs/policy/model-routing-in-plan-and-implement.md`, `docs/decisions/implemented/policy/2026-08-18-docs-retention-policy.md`, `scripts/check_docs_retention.py`, `tests/validators/test_check_docs_retention.py`, this history file
- **Files modified**: `AGENTS.md`, `Makefile`, `catalog/hooks/tests/test_installer_smoke.py`, the three cross-linked SKILL.md files, `CHANGELOG.md`, `docs/todos.md`
- **Catalog counts**: unchanged at 273 skills, 18 commands, 31 hooks, 23 agents
- **Stability gate**: met. The policy exists and is linked from `AGENTS.md` and the three skills; the advisory validator reports violations without failing; the budget gate and tests pass.

## 9. Next Steps

Phase 5 is the terminal phase: architecture refactor, known-gaps reconciliation, CI/CD, and cross-installer parity, then the `/update release` handoff. Carried in:

1. **The first retention archive pass** (16 versions, 306 files) is the plan's own named Phase 5 candidate. Propose-then-apply, with reference repair; nothing deleted.
2. The `docs/DEVLOG.md` ceiling question: the 150-line limit currently lives only in a test constant, not in `docs/policy/doc-budgets.json` beside the other ratchets.
3. From Phase 3: the anchor-link blind spot (a checker treating `#` as always same-page cannot see an anchor orphaned by relocation), and the deferred MCP decision-tree relocation with its parity-guard reason.
4. From Phase 2: the SKIP-clause / routing-scorer tension, including the 40 allowlisted collisions.
5. From Phase 1: the bare-`tar` PATH failure in `test_ps_standalone_extracts_and_hands_off`, and the stray empty `Microsoft/Windows/PowerShell` directory.
