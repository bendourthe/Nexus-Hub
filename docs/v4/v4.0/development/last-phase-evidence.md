# Last-phase evidence - v4.0.0 agent-communication-overhaul

**Date**: 2026-08-25
**Plan**: `docs/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md`
**`is_final_phase`**: true (Phase 5 of 5; Phases 1-4 have session histories and commits `c4150db0`, `3e2dacb3`, `494411c7`, `beaa00b9`)

This file is the fail-closed last-phase pack. Each section quotes a proving command or scan. An empty finding is not a pass unless the scan that produced it is quoted.

---

## Architecture refactor

**Detectors**: `[[project-refactor]]` empty-dir / duplicate / orphan / structure (propose-then-apply); `[[docs-layout-refactor]]` layout + retention.

**Empty-directory scan** (`find catalog scripts templates data docs tests extensions -type d -empty`):

```text
docs/v3/v3.17/development/history
docs/v3/v3.18/development
docs/v3/v3.19/development
extensions/nexus-code-search/benchmarks/.work/corpus/.nexus/code-index
extensions/nexus-code-search/benchmarks/.work/run-10k3cjf4/corpus/tests
extensions/nexus-code-search/benchmarks/.work/run-nleyqgk5/corpus/tests
```

**Disposition, all six left deliberately.** The three `extensions/nexus-code-search/benchmarks/.work/...` directories are gitignored benchmark scratch (`extensions/nexus-code-search/benchmarks/.gitignore:1:.work/`), so they never ship. The three `docs/v3/...` directories are prior versions' scaffolding whose content was archived to `docs/archive/v3/v3.17`, `.../v3.18`, and `.../v3.19` (all three archive counterparts confirmed present). Git does not track empty directories, so none of them appear in a clone or a release archive. This follows the disposition v3.16 recorded for the same class of directory rather than inventing a new one.

**Tracked-cache scan**: `git ls-files | grep -c "__pycache__\|\.pyc$"` returns `0`.

**Docs retention** (`python scripts/check_docs_retention.py`):

```text
  docs retention: nothing due for archival (current v3.21, threshold 2 minors)
```

**Docs co-location** (`python scripts/check_doc_colocation.py`, run inside the `validate` chain): passes. The v4.0 tree this version adds (`docs/v4/v4.0/development/history/`, `docs/v4/v4.0/known-gaps.md`, this file) follows the canonical `plans/ + development/ + known-gaps.md` layout.

**Deviation markers introduced this version**: `grep -rn "# DEVIATION:"` over every file this plan added or edited returns `0`.

**Evidenced no-op**: no file was moved, renamed, deleted, or merged this phase. The version's new files all landed in canonical locations on first write, so there was no layout debt to repair.

---

## Known-gaps reconciliation

**This version** (`docs/v4/v4.0/known-gaps.md`): created and finalized this phase. 2 open (DF-1 parity roster scope, MT-1 no runtime contract check), 4 resolved (BG-1 statistics drift, DF-2 stale dashboard carried from v3.21, MT-2 CI test-coverage fail-open, and the DF-2 carry itself).

**Two gaps were found and closed during this phase rather than merely recorded**, which is the point of running the detectors instead of asserting the result:

1. **BG-1**: registering the new skill left `data/skills.json`'s `statistics` block at 324/40 while the entries array held 325/41. `make validate` passed; only `tests/validators/test_registry_consistency.py` caught it, three tests failing at once. Fixed by recomputing both figures from the entries rather than incrementing by hand.
2. **MT-2**: `ci.yml` enumerated test directories by name, so `tests/test_removed_autonomy_surface.py` was never run by CI at all. Fixed, and the property is now asserted by a test.

**Other files with remaining Open Items (not skipped because they are another version)**:

- `docs/v3/v3.21/known-gaps.md` DF-1 (product atlas HTML): reviewed, deliberately left open. `docs/handbooks/markdown/` still contains only `.gitkeep`, so generating an atlas would produce a fake walkthrough. Disposition unchanged from v3.21.
- `docs/v3/v3.21/known-gaps.md` DF-2 (stale `docs/todos.md`): **resolved this phase**, recorded under Resolved in the v4.0 file.
- `docs/v3/v3.20/known-gaps.md` (DF-1, DF-2, WN-3): reviewed, out of this plan's scope, left in place.
- Older `docs/v3/v3.*/known-gaps.md` files with non-`finalized` Status lines are historical records of their own cycles. They were read, not rewritten. Editing a closed version's record so the status line looks tidy would destroy the account of what that release actually knew about itself, which is the only thing those files are for.

---

## Living docs architecture

**Scan** (do not invent `docs/testing/` or `docs/validation/`; do not invent a fake atlas HTML):

```text
docs/handbooks: exists=True is_dir=True
docs/handbooks/README.md: exists=True is_dir=False
docs/handbooks/markdown: exists=True is_dir=True
docs/handbooks/html: exists=True is_dir=True
docs/decisions: exists=True is_dir=True
docs/README.md: exists=True is_dir=False
docs/DEVLOG.md: exists=True is_dir=False
docs/todos.md: exists=True is_dir=False
docs/testing: exists=False is_dir=False
docs/validation: exists=False is_dir=False
handbooks markdown children: ['.gitkeep']
atlas/companion html count: 0
decisions md files: 22
```

**Evidenced no-op / recorded gap**: atlas HTML count is 0 by design, carried as v3.21 DF-1. `docs/testing/` and `docs/validation/` are absent and were not invented; this repository's tests live in `tests/` and its validators in `scripts/`, both already documented.

**Changed this phase**: `docs/decisions/` grew from 21 to 22 markdown files with `implemented/policy/2026-08-18-agent-communication-contract.md`. `docs/todos.md` was refreshed to the active branch and plan (v3.21 DF-2 resolved).

---

## Git-tree hygiene

**Working tree** (`git status --short | wc -l`): 7 files pending, all of them this phase's own additions and edits, staged in the Phase 5 commit.

**Branch**: `feat/v4.0.0-agent-communication-overhaul`, cut from `develop` at `f4eccd87`. Phase work is isolated on the feature branch per the develop-plus-main model; nothing was committed directly to `main`.

**Commit sequence**: one commit per phase, each carrying its own session history and changelog entry. Phase 2's commit was rewritten once before push because a `git add -A` had swept Phase 3 files into it; the phases were split back apart before either was published.

---

## CI/CD coverage

**Coverage of this plan's changes.** `ci.yml` triggers unconditionally and classifies paths inside the workflow with a fail-closed detector job (`relevant=true` unless every changed path is ignorable documentation prose). Every path this plan touched (`catalog/`, `templates/`, `data/`, `scripts/`, `tests/`, `.github/`) is non-docs, so every job runs. The new validator work is covered two ways: `scripts/check_base_template_parity.py` runs inside the `validate` job's chain, and the two new test files run in the `tests` job.

**Gap found and fixed** (MT-2 above). Before this phase, the `tests` job enumerated test directories by name across four steps:

```text
pytest tests/integrations tests/installer
pytest tests/validators
pytest tests/skills
pytest tests/plans tests/workflows
```

Anything outside those names was never executed in CI. `tests/test_removed_autonomy_surface.py` lives at the root of `tests/` and matched none of them. The workflow's own comment already recorded that `tests/plans/` had shipped in exactly this state in v3.15.8, so this is a repeated fail-open, not a one-off.

Replaced with a single step:

```text
pytest tests
```

This also makes a green local `make test` mean the same thing as a green CI run, since the Makefile already ran the whole tree.

**Property now asserted**, so the enumeration cannot return by accident: `tests/workflows/test_ci_runs_every_repo_test.py` (4 tests, passing) checks that every test file and every test directory under `tests/` is reachable from some pytest target in `ci.yml`, and that the `catalog/hooks/tests/` suite is still run. It asserts coverage, not step wording, so CI can be reorganized freely.

**Required-check integrity** (`python scripts/check_required_check_coverage.py`):

```text
Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally.
```

No required status check was added, renamed, or removed, so `docs/policy/required-checks.json` needed no edit. The v3.17.6 rule (filter at job level with `if:`, never at workflow level with `paths:`) is unaffected: this change edits a step inside an already-unconditional job.

**Action-minute impact**: neutral to slightly negative in cost. Four `pytest` process starts collapse into one, which saves a few seconds of interpreter and collection startup, while the newly-covered root-level test file adds its own runtime. No job was added, no matrix widened, and the existing optimizations (concurrency `cancel-in-progress`, pip caching keyed on manifests, the changes-detector gating, Windows and macOS legs restricted to non-PR events) were left untouched because they are already correct. Claiming a real reduction here would be inventing one.

---

## Cross-installer parity

`python scripts/check_installer_parity.py`:

```text
installer parity: PASS
```

This plan adds no installer edit, and none is required. `catalog/style-guides/` and `catalog/skills/` are both copied recursively by `scripts/installer.sh` and `scripts/installer.ps1`, so the new style guide lands at `~/.nexus-hub/style-guides/agent-communication.md` and the new skill lands in every platform's skills directory through the existing distribution. `scripts/check_base_template_parity.py` is a repo-internal guard already listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py`, so it correctly has no copy step and no `.ps1` sibling.

`python scripts/verify_platform_contracts.py` and `python scripts/check_platform_contract_freshness.py` both pass inside the `validate` chain; the contract is stamped for v3.21.0 and will need re-stamping to v4.0.0 at the release step, which `/update release` owns.

---

## Goal-vs-codebase review

The plan's Goal: *any agent with Nexus-Hub installed communicates in a consistent, concise, plain-language way across every supported platform: readable end-of-task reports, copy-paste commands with no unfilled placeholders, guided step-by-step instructions that repeat the remaining steps after an error, and docs deep-links instead of inline technical detail.*

Reviewed against the tree rather than against the plan's own phase list:

| Goal clause | Evidence in the codebase | Verdict |
|---|---|---|
| Consistent across every supported platform | 12 of 12 substantive templates carry `## Communication Contract` (grep count: 12). Body identity across all 12 asserted by test. The 4 surface-note stubs are excluded by design and asserted to stay clean. | Met |
| Readable end-of-task reports | Completed / Verified / Open / Next defined in the style guide (section 5), condensed in the skill, present in all 12 templates via the amended `End-of-Task Summary` block, and prescribed at the three highest-traffic report producers (`implement-phase` runbook, `/plan`, `/update release`). | Met |
| Copy-paste commands with no unfilled placeholders | REPLACE rule present in the style guide, the skill, and the reference file (all three confirmed by grep), plus the template bullet. Three worked cases in `references/response-contract.md`. | Met, with MT-1 recorded: nothing checks a real response at runtime. |
| Guided steps that repeat the remaining steps after an error | The renumber-from-1 rule appears in the style guide (2 mentions), the skill (4), and every template (1 each), with a worked error-recovery example in both the guide and the reference file. | Met |
| Docs deep-links instead of inline detail | Section 6 of the guide, folded into template bullet 1, and practised by the design itself: the 93-word template section links the full contract rather than restating it. | Met |
| Plain language for a non-engineer | Section 2 of the guide plus a plain-language substitution table in the reference file. The `implement-phase` completion report and both user-choice handoffs now require a plain-language consequence line. | Met |

**Miss found**: none against the Goal. Two gaps found against the wider tree (BG-1, MT-2) were fixed rather than deferred. Two limits are recorded honestly rather than claimed as met: DF-1 (release gate byte-locks 5 of 12, tests cover all 12) and MT-1 (the contract is unenforced at runtime by design, per the decision record).

**Scope discipline**: the `docs/todos.md` refresh and the `ci.yml` test-step change are the only edits outside the plan's named files. Both trace to explicit duties of this phase (known-gaps reconciliation, CI/CD coverage) and to the user's instruction to address remaining known gaps and update CI/CD.

---

## Human/manual testing suggestions

These need a human and were deferred to this final phase per the last-phase contract.

1. **Run the installer into a throwaway profile** and confirm `~/.nexus-hub/style-guides/agent-communication.md` exists and that `agent-communication` appears in each platform's skills directory. The recursive copy is exercised by `test_installer_smoke.py`, but an end-to-end run on a real profile is the only thing that proves the user-visible result.
2. **Trigger the skill in a live session** with each of the five positive eval phrasings and confirm it loads rather than routing to `writing-editing` or `anti-slop-editing`. The trigger evals score description vocabulary offline; they do not prove live routing.
3. **Read one real end-of-task report** produced after this install and audit it against the guide's own Verification checklist. This is the only test of whether the contract changes behavior, which is the entire point of the version.
4. **Paste one command block** from a real response into a terminal without editing it. If it runs, the placeholder rule is working; if it fails on a template token, MT-1 is why.

---

## Full-suite testing and stabilization

`python scripts/...` validate chain (the `make validate` target, run line by line because `make` is not installed on this host):

```text
  skills.json OK -- 325 skills
  bundles.json OK -- 15 bundles
  workflows.json OK -- 18 workflows
RESULT: PASS (0 errors, 65 warnings)      [orphan-bundle audit]
RESULT: PASS (0 errors, 325 skills scanned)   [agentskills.io conformance]
RESULT: PASS (0 un-allowlisted collisions, 37 allowlisted; 0 routing failures across 67 skill(s) with cases)
Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally.
  platform-defaults OK -- 13 platform(s), all derived artifacts in sync
Compression accuracy gate PASSED (CCR 100.0%, signatures 100.0%, reduction 45.8%).
All catalogs valid.
```

Targeted gates:

```text
base-template parity: 5 of 5 lockstep templates present
  8 budgeted doc(s) within ceiling
installer parity: PASS
```

Doc budgets after the rollout (`python scripts/validate_doc_budgets.py --list`), showing no ceiling was raised:

```text
templates/ai-instructions/base-claude.md       1358     1410  +52 (4%)
templates/ai-instructions/base-codex.md        1007     1020  +13 (1%)
templates/ai-instructions/base-cursor.md        976      990  +14 (1%)
templates/ai-instructions/base-gemini.md        997     1010  +13 (1%)
templates/ai-instructions/base-opencode.md      976      990  +14 (1%)
```

Full test suite (`make test` equivalent: six extension suites plus the whole `tests/` tree), run uncontended:

```text
43 passed in 7.97s                    [nexus-skill-server]
368 passed, 1 skipped in 41.77s       [nexus-code-search]
29 passed in 4.70s                    [nexus-web-fetch]
89 passed in 4.24s                    [nexus-skill-scanner]
237 passed in 3.30s                   [nexus-context-compressor]
51 passed, 1 skipped in 32.26s        [nexus-memory]
3059 passed, 32 skipped in 3653.56s (1:00:53)   [tests/]
```

Zero failures. Four defects were found and fixed during this phase before this run (BG-1 statistics drift, BG-2 prose count surfaces, MT-2 CI coverage, and one text-fossil test); each is recorded in `docs/v4/v4.0/known-gaps.md`.

**One failure was investigated and dismissed as an artifact, not silently ignored.** `tests/installer/test_selection_parity.py::test_bash_filtered_install_matches_the_resolver` failed once while three pytest processes were competing for this host. It passes in isolation (112s) and passes in this uncontended full run. The test spawns the real bash installer under a timeout, so CPU starvation is a plausible and sufficient explanation. Recorded here rather than omitted, because a failure that is explained away without evidence is indistinguishable from one that was ignored.

**Version sync**: `python scripts/check_version_sync.py` reports a clean tree at 3.21.0 across all surfaces. The bump to 4.0.0 is `/update release`'s job and was deliberately not performed here.

---

## Release handoff status

**No release is cut from this phase. This is a maintainer decision, recorded here as taken.**

Three plans target v4.0.0:

- `docs/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md` (this one, complete)
- `docs/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md` (not started)
- `docs/v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md` (not started)

Cutting v4.0.0 now would spend a major-version number, which cannot be reclaimed, on one of the three plans it was scoped to carry. The alternatives (ship as v3.22.0 on the 3.x line, or ship as v4.0.0 and retarget the other two plans) were presented to the maintainer with their consequences on 2026-08-25.

**Decision taken**: push the feature branch and stop. No merge into `develop`, no merge into `main`, no version bump, no tag, no GitHub Release. `scripts/check_version_sync.py` therefore stays clean at 3.21.0 by design, not by omission. The `/update release` handoff is deliberately not invoked; the numbering decision is deferred, and the work waits on the branch until it is made.

**What a future release will still need to do**, so it is not rediscovered later:

- Re-stamp `docs/policy/platform-read-contracts.json` (`meta.verified_for_version` and `last_verified`) to whatever version is chosen, via `[[platform-contract-verification]]`. `scripts/check_platform_contract_freshness.py` fails the moment the version is bumped past the stamped value, so this is a hard gate, not a courtesy.
- Reconcile the plan's `**Target version**` line if the number chosen is not v4.0.0.
- Run the capability-usage gate. This release changes no opt-in capability, installer flag, or host surface, so the gate is satisfied by an explicit no-change declaration rather than by per-surface documentation.
