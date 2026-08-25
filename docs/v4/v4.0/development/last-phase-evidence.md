# Last-phase evidence - v4.0

This file is the fail-closed last-phase pack for the v4.0 version directory. Each section quotes a proving command or scan. An empty finding is not a pass unless the scan that produced it is quoted.

Two plans ship into v4.0, so the file carries one part per plan. An earlier plan's evidence is a record of what that release knew about itself and is never rewritten to look tidy.

- [Part 1 - agent-communication-overhaul](#part-1---agent-communication-overhaul)
- [Part 2 - cost-effective-ci-cd](#part-2---cost-effective-ci-cd)

---

# Part 1 - agent-communication-overhaul

**Date**: 2026-08-25
**Plan**: `docs/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md`
**`is_final_phase`**: true (Phase 5 of 5; Phases 1-4 have session histories and commits `c4150db0`, `3e2dacb3`, `494411c7`, `beaa00b9`)

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

---

# Part 2 - cost-effective-ci-cd

**Date**: 2026-08-25
**Plan**: `docs/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md`
**`is_final_phase`**: true (Phase 8 of 8)
**Prior phases**: `f3954c3f` (1), `d22f8386` (2), `2908e36a` (3), `80c5b5be` (4), `05e6a03c` (5), `c9ccefe1` (6), `12ed626c` (7), each with a session history under `development/history/`

---

## Architecture refactor

Full ownership map, detector output, and the near-miss finding: [`ci-cd-final-audit.md`](ci-cd-final-audit.md) section 2.

**Empty-directory scan** (walk over the repository, excluding `.git`, `__pycache__`, `node_modules`, `.pytest_cache`, `reports`):

```text
./.antigravitycli
./.claude/worktrees
./docs/v3/v3.17/development/history
./docs/v3/v3.18/development
./docs/v3/v3.19/development
./extensions/nexus-code-search/benchmarks/.work/corpus/.nexus/code-index
./extensions/nexus-code-search/benchmarks/.work/run-10k3cjf4/corpus/tests
./extensions/nexus-code-search/benchmarks/.work/run-nleyqgk5/corpus/tests
```

All eight are pre-existing and none was created by this plan. Git does not track empty directories, so none appears in the diff. Two are gitignored runtime artifacts; the three under `docs/v3/` are residue from prior archival passes and belong to a `[[docs-layout-refactor]]` run. Cleaning them here would be the adjacent-code cleanup the boundaries rule forbids.

**Orphaned bundle files**:

```text
python scripts/validate_skills.py --bundles-only
Scanned 325 skills under catalog\skills (bundle audit)
RESULT: PASS (0 errors, 64 warnings)
```

Warning count moved 67 (branch point) to 64. The reduction is real: the `cicd-architect` rewrite dropped three, and each of the four bodies that crossed the 500-line soft cap during the plan was relieved by moving content to a Tier 3 reference rather than by raising a threshold.

**Duplicated command lists**: none remaining. `ci.yml` re-declared the Makefile validator sequence as 31 steps; it now calls one profile, and `test_ci_does_not_re_declare_the_validator_list` fails on any direct `run: python scripts/<name>.py`.

**Diff shape**: 33 files added, 0 deleted.

---

## Known-gaps reconciliation

`docs/v4/v4.0/known-gaps.md`, section `## v4.0.0 - cost-effective-ci-cd`.

| Category | Open | Resolved |
|---|---|---|
| Not implemented | 0 | 0 |
| Deferred | 2 | 0 |
| Bugs / regressions | 0 | 1 |
| Warnings | 1 | 0 |
| Missing tests | 0 | 1 |
| Quality-gate gaps | 0 | 0 |

Open: **DF-1** artifact upload deferred (needs an `actions/upload-artifact` SHA fetched from the vendor; the summary reaches `$GITHUB_STEP_SUMMARY` with no action at all in the meantime). **DF-2** the `full` profile has not completed end to end on this host. **WN-1** the new event topology has not run against real GitHub.

Resolved: **MT-1** all 23 strict-xfail assertions, closed across Phases 2 and 5 with no assertion edited or weakened. **BG-1** the redaction ordering defect that left the tail of a longer secret intact.

The other v4.0 plan's section was reviewed and left unchanged: its one open item, DF-1 on byte-locking the seven non-lockstep templates, is untouched by this plan. Older `docs/v3/v3.*/known-gaps.md` files whose Status is not `finalized` are historical records of their own cycle, not live queues.

---

## Living docs architecture

`docs/v4/v4.0/development/` gained six documents this plan: the lifecycle contract, the harness audit, the workflow audit, the profile guide, the settings runbook, and the final audit. `docs/decisions/implemented/policy/` gained one record (the doc-budget ceiling raise, with five rejected alternatives).

```text
python scripts/check_docs_conventions.py     OK
python scripts/validate_decision_records.py  23 decision record(s) OK
python scripts/check_doc_colocation.py       OK: no co-location mismatches under docs/v3, docs/v4
```

No `docs/testing/` or `docs/validation/` was invented. `docs/handbooks/markdown/` still holds only a `.gitkeep`, which is the state v3.21 DF-1 records; generating an atlas from no authored content would produce a fake walkthrough, so it stays open there.

---

## Git-tree hygiene

```text
python scripts/check_release_preconditions.py --branches --repo-settings

Branch hygiene (merged into origin/develop)
  4 merged branch(es) are cleanup candidates:
    - origin/backmerge/v3.21.0
    - origin/feat/v3.21.0-plan-implement-lifecycle
    - origin/feat/v3.21.0-release
    - origin/feat/v4.0.0-agent-communication-overhaul
  (10 branch(es) with an open PR were excluded)
  1 branch(es) survive a CLOSED, unmerged PR:
    - origin/backmerge/v3.20.0
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  NOTE: the repository description disagrees with README.md:
    - skills: description says 324, README.md declares 325
```

Report only; nothing deleted. The description drift is pre-existing (it dates from the v4.0.0 agent-communication-overhaul skill addition), is not a version-carrying surface `check_version_sync.py` can see, and is fixed by hand in the GitHub UI.

---

## CI/CD coverage

The terminal pipeline comparison against all 23 canonical fields: [`ci-cd-final-audit.md`](ci-cd-final-audit.md) section 3.

**Verdict: 22 PASS, 1 PARTIAL, 0 FAIL.** The PARTIAL is field 20 (reports published), recorded as DF-1 with an owner and a next step.

Section 4 of that document states what the comparison could NOT establish, which is the part a comparison listing only its passes would hide.

---

## Cross-installer parity

```text
python scripts/check_installer_parity.py     OK
python -m pytest catalog/hooks/tests/test_installer_smoke.py tests/workflows -q
117 passed, 9 skipped
```

`scripts/ci/` needs no installer registration and no `DEV_ONLY_SCRIPTS` entry: the installer copies `scripts/*.py` by explicit name and the smoke test globs that directory non-recursively, so a subdirectory is outside both. The smoke suite passing unchanged is the proof rather than the claim.

---

## Goal-vs-codebase review

**Plan Goal, restated**: make cost-effective, repository-native, end-of-plan CI/CD the default lifecycle for every project and agentic platform using Nexus-Hub, while migrating Nexus-Hub's own workflows to the same contract.

Inspected as if the phases had not been implemented here. The Goal has two halves.

**Half one, the distributed default.** Satisfied.

| Claim | Artifact |
|---|---|
| Generated plans encode the lifecycle | `implementation-plan/SKILL.md` per-phase prompt records CI impact, requires one local commit, forbids push; the exit checklist carries three lifecycle items |
| The executor enforces it | `implement-phase-runbook.md` 8.10 is commit-only in every mode; 9F owns the single publication |
| It reaches every platform | the block is in all 12 substantive templates, body-identical, and `tests/integrations/test_lifecycle_block_rendering.py` asserts it survives rendering to each read path, inheritance included |
| Release waits for green integration | `/update release` integration gate; `version-upgrade` Step 0 |
| One skill owns the policy | `cicd-architect` 790 to 275 lines, ten steps, two Tier 3 references; the other two CI/CD skills declare conformance in their bodies |

**Half two, Nexus-Hub's own migration.** Satisfied, with one honest limit.

| Claim | Artifact |
|---|---|
| Repository-native profiles exist | `scripts/ci/`, five profiles, 85 tests |
| Workflows delegate rather than duplicate | `ci.yml` 1056 to 566 lines; a test forbids the duplication returning |
| Full platform validation before merge | Windows and macOS legs moved from `push` to `pull_request` |
| No duplicate post-merge suite | `ci.yml` has no `push` trigger; a repo-wide test holds the property |
| Required checks always resolve | `ci-required` with `if: always()` and an allowlist verdict; 10 contexts verified produced unconditionally |

**The limit**: the topology has been proven statically, not observed running. That is WN-1, and the plan's own publication is its first real-world test. Recording it rather than claiming the Goal landed in full is the point of this section.

**No unresolved miss.** Both halves are satisfied; the two deferrals and one warning each carry an owner and a next step in the known-gaps file.

---

## Human/manual testing suggestions

Automated tests cover what is checkable from the repository. These need a human and a real GitHub:

1. **Open a docs-only pull request** and confirm every required context REPORTS (success or skipped) rather than staying Pending. This is the v3.17.5 defect class and the single most valuable manual check here.
2. **Merge it** and confirm `post-merge.yml` ran while `ci.yml` did NOT. If `ci.yml` runs, the push trigger came back.
3. **Confirm no run was triggered** by an ordinary feature-branch push.
4. **After the next release tag**, confirm `release.yml` ran and `ci.yml` did not.
5. **Read the billing page** and record per-runner-class minutes for the period, so the projected saving becomes a measured one. Derive weights from the live per-unit price, not a remembered multiplier.
6. **Verify branch protection** on `main` and `develop` per runbook section 1. That is what makes `post-merge.yml` mean what its comment says.
7. **Run `make ci-full` to completion** on a machine with the six extension packages installed, and record the wall-clock (DF-2).

Full checklist: [`github-ci-settings-runbook.md`](github-ci-settings-runbook.md) section 8.

---

## Full-suite testing and stabilization

Local gate. This is the complete gate that must pass BEFORE publication, so it is local by construction.

```text
python scripts/ci/run.py --profile fast --reports-dir reports
PASS: 12 passed, 0 failed, 0 skipped, 0 advisory in 8.0s

python scripts/ci/run.py --profile release --reports-dir reports
PASS: 3 passed, 0 failed, 0 skipped, 0 advisory in 5.9s

python scripts/ci/run.py --profile platform --only shell-lint,powershell-parse
PASS: 1 passed, 0 failed, 0 skipped, 0 advisory in 0.6s
  (shell-lint SKIP: no command in this group runs on windows)

python -m pytest tests -q                    (see the run recorded below)
python -m pytest tests/ci -q                  85 passed
python -m pytest tests/workflows -q           97 passed, 13 skipped
python -m pytest tests/validators/test_ci_workflow_contract.py -q     49 passed
python -m pytest tests/validators/test_ci_changes_classifier.py -q    23 passed
python -m pytest tests/integrations/test_lifecycle_block_rendering.py -q
                                              17 passed, 1 skipped

python scripts/validate_workflow_security.py             PASS (11 workflows)
python scripts/check_required_check_coverage.py          PASS (10 contexts, 2 branches)
python scripts/check_base_template_parity.py             PASS
python scripts/validate_doc_budgets.py                   PASS
python scripts/check_registry_entries.py --check --strict PASS
python scripts/check_agentskills_conformance.py          PASS (325 skills)
python scripts/run_trigger_evals.py --gate               PASS (0 routing failures)
python scripts/validate_skills.py --bundles-only         PASS (0 errors, 64 warnings)
python scripts/validate_unicode_safety.py --strict       PASS
python scripts/check_docs_conventions.py                 PASS
python scripts/validate_decision_records.py              PASS (23 records)
python scripts/check_doc_colocation.py                   PASS
python scripts/check_installer_parity.py                 PASS
```

### The eight failures this gate found, and what they were

The first full `tests/validators` run after Phase 7 reported 8 failures out of 1263. All eight were the SAME class, and none was a defect in the shipped behavior: each test asserted that a guard is wired into CI by grepping `ci.yml` for a literal `scripts/<name>.py`, and the workflow now calls a profile instead.

The tempting fix was the wrong one, and worth naming: re-adding literal `run:` lines to the workflow would have made every grep pass and would have reintroduced the duplicated command list the engine exists to remove.

Fixed instead with `tests/validators/_ci_reachability.py`, one shared helper that answers "would a CI job run this script?" by resolving through the live profile definitions. Six tests now call `assert_wired_into_ci(...)`, whose failure message names the correct remedy and explicitly warns against the wrong one. The seventh (`test_push_event_uses_before_sha`) asserted classifier behavior for a push event `ci.yml` can no longer receive; it now asserts the fail-closed fall-through, plus a new companion test that the premise still holds.

### What was NOT run

`scripts/ci/run.py --profile full` as a single aggregated invocation, and the `windows-hooks` group of the `platform` profile. Both are DF-2, with what IS verified in their place: every constituent group of `full` passed individually, and the `platform` profile's other two groups passed.

---

## Publication and integration

To be completed by sub-task 8.6 after the branch is published. Required-check results and the merge SHA are recorded here.

**Status at the time of writing**: eight phase commits on `feat/v4.0.0-cost-effective-ci-cd`, no push, no remote CI run for this plan.

---

## Release handoff status

**BLOCKED, correctly.** `/update release` starts only after the integration result is green and merged.

The instruction for this session ends at "merge branch to develop". Tagging, the version bump, the changelog, and the GitHub Release are NOT authorized by it and are not performed. That is the lifecycle working as designed: the plan's final phase hands a green, merged `develop` to a release flow that runs separately and behind its own confirmation gates.
