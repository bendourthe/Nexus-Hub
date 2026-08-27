# Session History -- v3.1.0 adoption-claude-red Phase 5: Ask-First offensive-security category decision

**Date**: 2026-06-08
**Plan**: [`docs/releases/v3/v3.1/plans/adoption-claude-red.md`](../../plans/adoption-claude-red.md)
**Phase**: 5 of 5 -- Ask-First category decision (final phase)
**Branch**: `feat/adoption-claude-red` (continued from Phase 4 tip)
**Outcome**: complete; both sub-tasks (T012-T013) closed. All catalog gates green; the only test failures are 3 pre-existing Windows-host ENV bash-installer tests (CI-green, documented WN-v31cr-6). As the final phase, this triggers the release-readiness workflow; the v3.1.0 version bump / tag is held for the develop->main release (owned by `/update version`), since v3.1.0 also includes the in-progress dynamic-workflows sub-plan.

## Goal

Produce the Ask-First maintainer decision artifact required by the AGENTS.md "Creating a new skill category" boundary: a memo weighing whether to open a standalone `offensive-security` category for the deferred content (`offensive-cloud` plus the wireless / exploit-dev / fuzzing / IoT / mobile / AD / recon specialist groups), with an explicit recommendation and a binary GO/NO-GO checklist -- and explicitly NOT creating the category or any specialist skill. Then close the plan: run full validation across the catalog and add the CHANGELOG `[Unreleased]` entry summarizing the whole claude-red adoption (the two new skills, the scanner allowlist, the web/auth fold-ins, the deferred category decision).

## Pre-implementation analysis (before any edit)

- **Source of truth for the memo**: [`comparison-claude-red.md`](../../comparison-claude-red.md) Sections 9.4 (recommendation ordering -- tier 3 "Ask-First scope decision"), 10 (category taxonomy -- offensive content fits neither `security` AppSec nor `security-operations` defensive ops, arguing for a third category), and 13 (risks + the recommended-against weaponization group). The comparison's standing recommendation is DEFER unless maintainers deliberately choose to become offensive-capable, so the memo's recommendation is inherited but re-justified per-factor so a maintainer can disagree on the merits.
- **Scope discipline**: the T012 prompt scopes the category question to `offensive-cloud` + the specialist groups. The detection-evasion / weaponization group (N2 in the plan's NOT-adopted appendix) is recommended against regardless of whether the category exists, so the memo keeps it out of every GO path rather than folding it into the decision.
- **Dual-branch release reality**: per the roadmap and `known-gaps WN-v31cr-3`, v3.1.0 is two parallel feature branches off `develop` (`feat/adoption-claude-red` + `feat/adoption-dynamic-workflows`); the release node depends on both, and the roadmap states the version bump/tag is a develop->main action owned by `/update version`, "not now". This shaped two decisions: the CHANGELOG entry is scoped to claude-red (not a grand version paragraph) to merge cleanly, and the final-phase release-readiness workflow holds the actual version bump/tag for the release.
- **Validation tooling**: `make` is absent on the Windows dev host (WN-v31cr-2), so `make validate` / `make scan` / `make test` are emulated by invoking each validator and the scanner directly, exactly as Phases 1-4 did.

## Subtasks completed

1. **T012 -- author the decision memo.** Created `docs/v3/v3.1/offensive-security-category-decision.md`. Structure: a TL;DR DEFER recommendation; "What is being decided" (the narrow binary question, the current two-category taxonomy, the out-of-scope weaponization group); a five-factor analysis (brand/positioning, maintenance burden, scanner-collision load, dual-use governance, the AGENTS.md Ask-First requirement); a three-option table (DEFER / open now / reject permanently) with pros/cons; a recommendation rationale (DEFER dominates on every factor except domain completeness, which a coding catalog does not need; DEFER over reject preserves optionality at no cost; if a future GO, ship a separately-governed bundle rather than scatter into `security`); a binary GO/NO-GO checklist (NO-GO/DEFER boxes checked as the current state, GO boxes enumerating every precondition); and an appendix inventorying the ~30 deferred skills. No category and no skill were created.
2. **T013 -- validation + CHANGELOG.** Emulated the full gate (all catalog gates green -- see Test results) and added a CHANGELOG `[Unreleased]` entry: a scoped summary paragraph plus Added (the two Phase 1 skills + the Phase 2 scanner allowlist), Changed (the Phase 3 web AppSec fold-in, the Phase 4 auth fold-in, the 248->250 catalog growth), and Deferred (the category decision) sections, with the weaponization group and the generation-as-service CI optimizer noted out of scope.

## Registry re-registration

None. Phase 5 adds no skill and changes no skill metadata -- it produces a `docs/` memo and a root CHANGELOG entry. `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` are untouched; the catalog stays at 250 skills.

## Key decisions

- **DEFER, not reject.** Permanent rejection would foreclose a future the maintainers might want; DEFER keeps the now-proven fold-in pattern available at no cost. The memo records this explicitly so the decision is revisitable.
- **CHANGELOG scoped to claude-red, no grand version paragraph.** The `[Unreleased]` section is shared with the dynamic-workflows branch; a monolithic version summary would conflict on merge, whereas section-based Added/Changed/Deferred bullets concatenate cleanly. The reconciliation is the same one already tracked for the gap log (WN-v31cr-3).
- **Held the v3.1.0 version bump / tag.** The user opted into the full final-phase release-readiness workflow, but the actual version-carrying bump and tag are a develop->main action owned by `/update version` and require both v3.1.0 sub-plans to land. Running them on this feature branch would be premature (the roadmap is explicit on this), so the release-readiness workflow prepares/audits without cutting the tag.
- **ENV test failure recorded, not chased.** The 3 failing bash-installer tests are a Windows-host `shutil.which("bash")`->WSL artifact, proven by a clean Git Bash run and the passing PowerShell siblings; fixing the v2.4.0 test harness is out of scope for this Markdown-only adoption phase, so it is logged as WN-v31cr-6 with CI as the authoritative gate.

## Test results

- Catalog scanner gate (`scan_skill_security.py catalog/skills catalog/mcp-configs --fail-on high`): **exit 0** -- no HIGH/CRITICAL; the only tail finding is the pre-existing LOW MCP moving-ref entry (`@supabase/mcp-server-supabase@latest`), no regression.
- Scanner package suite: **87 passed** (`python -m pytest extensions/nexus-skill-scanner -q`).
- Repo-level `tests/` suite: **400 passed, 3 failed in 594s**. All 3 failures are in `tests/installer/test_branch_flag.py` (`test_bash_branch_check_probe_resolves_cache_path`, `test_bash_branch_check_neutralizes_traversal`, `test_bash_branch_requires_value`), each returning exit 127 because pytest's `shutil.which("bash")` resolves to `C:\windows\system32\bash.EXE` (WSL launcher), which cannot execute `scripts/installer.sh` at its OneDrive-spaced Windows path. Verified non-regression: `bash scripts/installer.sh --branch feature/login --check` under Git Bash returns **exit 0** with the asserted output (`branches/feature-login`, branch echoed); the two PowerShell sibling tests and both static-surface tests pass; the three pass on the CI ubuntu runner. `scripts/installer.sh` is untouched this phase (Markdown-only change).
- `make validate` emulated: JSON catalogs valid (250 skills, 15 bundles, 17 workflows, templates, marketplace all load); `validate_skills.py --bundles-only` and `--quality` exit 0; `validate_no_personal_paths.py`, `validate_unicode_safety.py`, `scan_supply_chain_iocs.py`, `validate_workflow_security.py`, `validate_solution_frontmatter.py`, and `check_version_sync.py` all exit 0.
- ASCII safety: the memo is ASCII-clean; the CHANGELOG `[Unreleased]` block I added is ASCII-clean (the 210 non-ASCII chars elsewhere in CHANGELOG.md are pre-existing in the v3.0.0-and-earlier entries).

## CI/CD edits

- None. The memo lives in `docs/` (auto-distributed, no installer edit) and the CHANGELOG is a root doc; no new script, env var, or dependency, so 0 workflows touched. The CI `validate` job loads `skills.json` and runs the scanner gate over `catalog/skills` (unchanged content); the `tests` job runs the validator + scanner suites on ubuntu, where the 3 bash-installer tests pass under real Linux bash.

## Deviations

- None from the plan (T012-T013 implemented as written). The only judgment calls -- scoping the CHANGELOG to claude-red and holding the version bump/tag for the develop->main release -- are mandated by the roadmap's dual-branch release model, not deviations from the Phase 5 task prompts.

## Troubleshooting / environment notes

- `make` / `shellcheck` remain unavailable on the Windows dev host (WN-v31cr-2), so the gate was emulated by invoking validators and the scanner directly; `make lint` is N/A (Markdown-only phase, no shell surface).
- A PowerShell range-operator gotcha (`1..0` reverses to `@(1,0)`) caused a first attempt to pass each single-token validator its own name as an argument (argparse exit 2); re-running each validator individually showed all exit 0.
- The repo `tests/` suite is slow (~10 min) because the installer tests shell out per case; re-running just `test_branch_flag.py` (2.85s) isolated the 3 ENV failures and the 4 passing siblings.

## Known gaps

See [`docs/releases/v3/v3.1/known-gaps.md`](../../known-gaps.md). 1 new open item this phase (WN-v31cr-6: 3 bash-installer tests fail on the Windows host due to the WSL `bash.EXE` path-resolution artifact; CI-green; Related: WN-v31cr-2), 0 resolved. Carried forward: WN-v31cr-1 through -5. Total 6 WN open. Per WN-v31cr-3 this gap log merges with the dynamic-workflows gap log at develop-integration.

## Next steps

- **Release-readiness workflow (this run, full Phase 9 per user opt-in)**: 9A resolve known gaps + scan in-code markers; 9B verify test/CI surface (catalog gates green; the ENV bash-installer failures are CI-covered); 9C docs + project refactor audits (audit-only); 9D standard `/update-*` checks; 9E prepare-only -- the v3.1.0 version bump and tag are HELD for the develop->main release (both sub-plans must land first; owned by `/update version`).
- **Version release (later, not this branch)**: when both `feat/adoption-claude-red` and `feat/adoption-dynamic-workflows` merge into `develop`, reconcile the two gap logs (WN-v31cr-3), merge to `main`, and cut `v3.1.0` via `/update version`.
- **Maintainer decision (open)**: the `offensive-security` category memo awaits sign-off; no category or skill is created until a GO decision is recorded and every GO precondition is met.
