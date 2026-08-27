# Known Gaps - v4.0

**Project**: Nexus-Hub
**Status**: in-progress
**Last updated**: 2026-08-26

## v4.0.0 - agent-communication-overhaul

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 1 | 1 |
| Bugs / regressions (BG) | 0 | 3 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 2 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Not Implemented

None.

#### Deferred

##### DF-1 - The non-lockstep seven templates are not byte-locked by the release gate

- **Source phase**: Phase 3 - Instruction-template rollout and parity gate
- **Plan reference**: `docs/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md` (sub-task 3.3 failure modes)
- **Reason**: `scripts/check_base_template_parity.py` has a five-file roster by design. The guardrails five, `base-google-shared.md`, and `generic-instructions.md` legitimately differ from the lockstep five elsewhere in the file, so widening the roster would produce false failures on content that is correct. The contract section itself has no valid per-platform variation, so drift there IS checkable, and `tests/validators/test_communication_contract_rollout.py::test_contract_body_is_identical_across_every_substantive_template` checks it across all 12. That is stronger than the plan anticipated (it compares bodies, not just headings), but it runs in the pytest suite rather than in the `make validate` chain, so a drift is caught at test time rather than at release-gate time.
- **Suggested next step**: If the validator chain should own this, extract the body-identity comparison into a small repo-internal script under `scripts/` and add it to the `validate` target, leaving the parity gate's five-file roster untouched. The test already contains the comparison logic, so this is a move, not a rewrite.

#### Bugs / Regressions

None open.

#### Warnings

##### WN-2 - A concurrent branch adds a thirteenth instruction template that will need the lifecycle block

- **Source phase**: Phase 8 - Architecture refactor, known-gaps reconciliation, and CI/CD
- **What was observed**: during Phase 8 the working tree acquired unrelated in-progress work from a concurrent session (a `pi` platform integration and a `grill` command), including an untracked `templates/ai-instructions/base-pi.md`. That file is NOT on `develop` and is not part of this plan; only files tracing to this plan were staged, and this plan's eight commits contain none of it.
- **Why it is recorded here**: `tests/skills/test_cicd_lifecycle_contract.py::test_template_roster_matches_the_directory` failed against that dirty worktree, which is the guard working exactly as designed - a new template must be classified or it silently escapes the lifecycle rollout. The failure does not exist on `develop`, where the file is absent.
- **What the other branch must do when it lands**: classify `base-pi.md` in the roster (substantive or surface-note stub) and, if substantive, add the `## Plan Lifecycle and CI/CD` block body-identical to the other twelve. The assertion message names both obligations.
- **Suggested next step**: none for this plan. This is a note for whoever merges the `pi` integration, so the failure reads as an expected checklist item rather than a mystery.


None.

#### Missing Tests / Coverage Gaps

##### MT-1 - No runtime check that a response actually follows the contract

- **Source phase**: Phase 1 - Communication contract and decision record
- **Plan reference**: `docs/v4/v4.0/plans/v4.0.0-agent-communication-overhaul.md` (Phase 1 design; recorded in the decision record's Consequences)
- **Reason**: Prose tone is not machine-checkable at `PreToolUse` time. The tests in this version prove that the contract is PRESENT and IDENTICAL everywhere it should be; nothing proves that a given response OBEYED it. This was considered and rejected as a hook gate in `docs/decisions/implemented/policy/2026-08-18-agent-communication-contract.md`; the gap is recorded here so it is visible rather than implied.
- **Suggested next step**: The mechanically checkable subset is narrow but real: a response containing a fenced command block with an unflagged `<...>`, `[...]`, or ALL-CAPS template token is detectable by pattern. If a future version wants partial enforcement, that single rule is the one worth automating; the rest stays advisory.

##### MT-3 - Nothing locally enforces the CI Python floor

- **Source phase**: Phase 5 - Architecture refactor, known-gaps reconciliation, and CI/CD
- **Reason**: CI runs Python 3.11.16; this workstation runs 3.12.10. Syntax accepted by the newer interpreter and rejected by the older one passes every local gate and fails in CI at import time, taking out a whole job rather than one test. This is not hypothetical: it happened on this branch (BG-3 below). No local check, hook, or validator asserts that repository Python parses under the CI version.
- **Suggested next step**: A cheap guard exists. `ast.parse(src, feature_version=(3, 11))` over the repository's `.py` files detects exactly this class in well under a second and needs no extra dependency, no second interpreter, and no outbound call. It would fit the `validate` chain beside the other repo-internal guards. Declaring the floor in one place (it is currently implicit in the CI `setup-python` version) is the prerequisite.

#### Quality-Gate Gaps

None.

### Resolved Items

##### BG-1 (resolved) - `data/skills.json` statistics block drifted on skill registration

- **Source phase**: Phase 2 - agent-communication skill
- **What happened**: Registering the new skill per the plan's "hand-edit exactly three files" instruction left `data/skills.json`'s `statistics.total_skills` at 324 and `statistics.categories["developer-experience"]` at 40, while the entries array held 325 and 41. `make validate` passed; the drift surfaced only when `tests/validators/test_registry_consistency.py` ran, three tests failing at once.
- **Resolution**: Recomputed both `statistics.total_skills` and the full per-category count map from the entries themselves rather than incrementing by hand, so the two can no longer disagree. All 9 registry-consistency tests pass.
- **Note for future skill registration**: the real count is six surfaces, not the three the skill-authoring instructions name. Each was found by a different gate, and three of the six were found only after the phase that was supposed to have finished registration:
    1. `data/SKILL_INDEX.md` (row plus the total line).
    2. `data/skills.json` entries array.
    3. `data/skills.json` `statistics` block (`total_skills` and the per-category map). Caught by `tests/validators/test_registry_consistency.py`, which runs only in pytest.
    4. `data/marketplace.json` category `skill_count`.
    5. `data/marketplace.json` `plugin.description` prose count. Caught by `tests/skills/test_org_authoring_surface.py`.
    6. `data/bundles.json` module or bundle membership. Caught by the reachability check in `scripts/check_registry_entries.py`, the only one of the three late-found surfaces that fails inside `make validate`.

  `.claude-plugin/plugin.json` also carries the count in prose and was updated in the same pass, though no gate currently asserts it, which is itself worth noting: it is the one count surface that could go stale silently.

##### BG-2 (resolved) - Two prose skill counts were left stale by registration

- **Source phase**: Phase 2 - agent-communication skill
- **What happened**: `data/marketplace.json`'s `plugin.description` and `.claude-plugin/plugin.json`'s `description` both state the catalog size in prose and both still read "324 curated skills" after the entry count moved to 325. The first was caught by `tests/skills/test_org_authoring_surface.py`; the second is asserted by no gate at all and was found only by grepping for the stale number once the first failure pointed at prose counts.
- **Resolution**: Both bumped to 325 in the same pass.
- **Residual risk**: `.claude-plugin/plugin.json`'s count has no gate. It will go stale on the next skill addition unless someone remembers it or a check is added. Recorded rather than fixed, because adding a seventh count assertion is a separate decision from this version's scope.

##### BG-3 (resolved) - A Python 3.12-only f-string broke CI on 3.11

- **Source phase**: Phase 5 - Architecture refactor, known-gaps reconciliation, and CI/CD
- **What happened**: The replacement assertion written for the text-fossil test used a multi-line expression inside an f-string replacement field. PEP 701 allowed that in Python 3.12; on 3.11 it is a `SyntaxError`. The local suite (3.12.10) passed all 3059 tests. CI (3.11.16) failed at collection, and because the error is at import rather than assertion time, it took out the entire `verify` job, one of the five required checks, rather than a single test.
- **Resolution**: Rewrote the assertion as a plain list comprehension plus a concatenated message, valid from 3.9 onward. Then parsed every Python file this branch touched with `ast.parse(..., feature_version=(3, 9))` to confirm no other file carried newer-only syntax; all five parse clean.
- **Why it is worth recording**: a green local run proved nothing about the interpreter that actually gates the merge. The generalizable gap (nothing enforces the CI Python floor locally) is MT-3 above.

##### DF-2 (resolved) - `docs/todos.md` described an old feature branch

- **Carried from**: `docs/v3/v3.21/known-gaps.md` DF-2
- **Resolution**: Refreshed `docs/todos.md` against the active branch and plan, taking the first of the two options its own suggested next step offered. The 269-line accretion of completed per-version sections and stale `[IN PROGRESS]` markers from released minors was replaced by a current-state dashboard, plus pointers to the per-version known-gaps files and the changelog, which are already authoritative for history. A "Maintaining this file" note states the replace-rather-than-append rule so the accretion does not restart.

##### MT-2 (resolved) - CI never ran part of the repo test suite

- **Source phase**: Phase 5 - Architecture refactor, known-gaps reconciliation, and CI/CD
- **What happened**: `ci.yml` enumerated test directories by name across four steps. Any test outside those names existed, passed locally, and guarded nothing in CI. `tests/test_removed_autonomy_surface.py` sits at the root of `tests/` and was covered by no step at all. The workflow's own comment already recorded that `tests/plans/` had shipped in the same state in v3.15.8, so this was a known-and-repeated fail-open, not a surprise.
- **Resolution**: Replaced the four enumerated steps with one `python -m pytest tests -v`, which also matches what `make test` runs locally, so a green local run and a green CI run now mean the same thing. Added `tests/workflows/test_ci_runs_every_repo_test.py`, which asserts the property (every test file and directory under `tests/` is reachable from some ci.yml pytest target) rather than the wording of a step, so CI can be reorganized freely but cannot silently drop coverage again.

### Carried From Prior Versions

- **v3.21 DF-1** (product atlas HTML) remains open and stays in `docs/v3/v3.21/known-gaps.md`. It was reviewed this phase and deliberately not resolved: `docs/handbooks/markdown/` still holds only a `.gitkeep`, and generating an atlas from no authored content would produce a fake walkthrough. The honest disposition is unchanged from v3.21.
- **v3.20 items** (DF-1 invocation levers, DF-2 marketplace form, WN-3 personal-paths scan) were reviewed and remain out of this plan's scope. They stay in `docs/v3/v3.20/known-gaps.md`.
- Older `docs/v3/v3.*/known-gaps.md` files whose Status line is not `finalized` are historical records of their own cycle, not live work queues. They were not rewritten, because editing a closed version's record to look tidy destroys the account of what that release actually knew about itself.

## v4.0.0 - cost-effective-ci-cd

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 2 | 0 |
| Bugs / regressions (BG) | 0 | 1 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - Report artifacts are published to the run summary, not uploaded

- **Source phase**: Phase 7 - Nexus-Hub workflow migration
- **Plan reference**: `docs/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md` (T049)
- **Reason**: The lifecycle contract section 6 asks for detailed reports uploaded with `if: always()` and a short explicit retention period. Uploading requires `actions/upload-artifact`, and every third-party action in this repository is pinned to a full 40-character commit SHA. That SHA has to be FETCHED from the vendor; it cannot be recalled or inferred. Nexus-Hub has made exactly this mistake before, in the opposite direction: the `.kimi/agent.yaml` companion shipped in v3.15.0 was fabricated rather than found, and had to be dropped. Writing a plausible-looking SHA would break every run at once, and writing a floating `@v4` tag would violate the pinning rule the same phase asserts.
- **What ships instead**: every lifecycle workflow appends `reports/summary.md` to `$GITHUB_STEP_SUMMARY` with `if: always()`, using no action at all. That satisfies the human-readable half of section 6 on every result, including a failure. The machine-readable artifacts (JUnit, `summary.json`, `metadata/environment.json`) are still WRITTEN by every run; they are simply not uploaded, so they are available inside the job and not after it.
- **Suggested next step**: fetch the current `actions/upload-artifact` release SHA from the vendor, add one upload step per lifecycle workflow with `if: always()` and `retention-days: 7`, and remove the exemption. `scripts/validate_workflow_security.py` already fails an `upload-artifact` step that omits `retention-days`, so the guard is in place before the feature is.

##### DF-2 - The `full` profile has not been run end to end on this host

- **Source phase**: Phase 6 and Phase 7
- **Reason**: `python scripts/ci/run.py --profile full` was started and had not completed after roughly 50 minutes on this workstation. The profile runs the whole `catalog/hooks/tests` tree, the whole `tests/` tree, and six extension suites in sequence; `tests/skills` plus `tests/validators` alone take 9.5 minutes, and the extension suites require their packages to be pip-installed. The per-command timeouts (1800s for hooks, 3600s for the repo suite, 900s per extension) bound the worst case at roughly 2.5 hours, so it is slow rather than hung.
- **What IS verified**: the `fast` profile (12 commands, 8.0s, PASS), the `release` profile (3 commands, 5.9s, PASS), and every constituent group of `full` run individually - `tests/skills` plus `tests/validators` (1825 passed), `tests/ci` (85 passed), `tests/workflows` (97 passed), and the whole validator chain via `make validate`. What is NOT verified is the single aggregated invocation and its exit status across all groups.
- **Root cause, narrowed in Phase 8**: the suite is not hung, it is slow for a specific and fixable reason. `tests/skills/test_presentify_*` makes repeated `subprocess.run(..., timeout=60)` calls that reach their full 60-second timeout on this workstation while completing in milliseconds on the CI runner. Several of those in sequence dominate the wall-clock. Reproduced in a clean isolated `git worktree`, so it is an environment property rather than concurrent-session interference or a defect in this plan's changes: CI runs the same suite to completion in about 8 minutes.
- **Consequence, stated plainly**: on this workstation the authoritative complete-suite run is CI, not the local gate. That is the honest reason the four wiring failures in PR #124 were found remotely rather than locally, and it cost three round trips.
- **Suggested next step**: find why those subprocess calls saturate their timeout here (a missing interpreter-resolution, a Windows path issue, or a genuinely absent dependency) rather than raising the timeout, which would only make the suite slower. Then run `make ci-full` to completion on a machine where the six extension packages are installed and record the measured wall-clock in the profile guide, so the quick-reference durations stop being estimates. If the aggregate stays impractical locally, that is a finding about the profile's shape and argues for splitting `full` by group.

#### Warnings

##### WN-1 - The new event topology has not been exercised against real GitHub

- **Source phase**: Phase 7 - Nexus-Hub workflow migration
- **Reason**: Every assertion about the new topology is static: YAML parsing, trigger inspection, and contract tests. Nothing has yet observed GitHub actually running `ci.yml` on a pull request, `post-merge.yml` on a merge, and `release.yml` on a tag, or confirmed that the five required contexts still resolve. That evidence can only come from the plan's own publication in Phase 8, which is the first real-world test of the change.
- **Suggested next step**: Phase 8 sub-task 8.6 monitors the integration pull request. The runbook's section 8 checklist is the wider verification, and three of its items (a docs-only PR resolving every context, `post-merge.yml` running while `ci.yml` does not, `release.yml` running on the tag while `ci.yml` does not) can only be ticked after the merge and the release.

### Resolved Items

##### BG-1 (resolved) - Redaction left the tail of a longer secret intact

- **Source phase**: Phase 6 - Repository-native CI engine
- **What happened**: `scripts/ci/reporting.py`'s `redact()` sorted its values longest-first only on the path where it computed them itself. A caller supplying an explicit list got them in the order given, so redacting a short value that is a PREFIX of a longer one first left the longer one's tail intact: a secret became `[REDACTED]-extended-tail`.
- **Why it mattered**: that is worse than not redacting at all, because it READS as a successful redaction. A reviewer scanning a report for leaked values would see the marker and move on.
- **Resolution**: sorting now happens inside `redact()` regardless of where the list came from, with the reasoning in a comment: a caller supplying its own list has no reason to know the ordering matters. Caught by `test_redaction_prefers_the_longest_value_first`, written before the fix.

### Resolved Items

##### MT-1 (resolved) - Twenty-three lifecycle assertions were expected-red until their owning phase landed

- **Source phase**: Phase 1 - Canonical lifecycle contract and baseline audit
- **Plan reference**: `docs/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md` (T004)
- **What happened**: `tests/skills/test_cicd_lifecycle_contract.py` encoded the contract's seven non-negotiable statements in full at Phase 1, but the surfaces satisfying statements 4 and 6 did not exist until Phases 2 and 5. The plan asked for failing-first tests and forbade weakening them; leaving them plainly red would have made every intermediate phase commit ship a red suite, which trains a reader to ignore red.
- **Mitigation used**: each not-yet-true assertion carried `pytest.mark.xfail(strict=True)` naming its owning phase. Strict xfail is self-closing: when the owning phase lands, the test passes, pytest reports an unexpected pass, and the run FAILS until the marker is removed.
- **Resolution**: all 23 markers are gone - 9 removed in Phase 2, 14 in Phase 5. Not one assertion was edited to make it pass and none was weakened. The file now reports 54 passed, 0 xfailed.
- **Worth keeping**: the mechanism earned its keep twice. In Phase 1 a strict xfail XPASSed and caught a WRONG audit row (both CI/CD skills already linked `cicd-architect`, in a Related Skills footer); the assertion was tightened to require a body-level conformance statement rather than deleted. In Phase 2 nine markers came off at once, which was the phase's own completion signal.

## v4.0.0 - docs-lifespan-tree-and-enforcement

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 4 | 1 |
| Warnings (WN) | 1 | 0 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Bugs / Regressions

##### BG-1 - nexus-memory config initialization can expose an empty file to a concurrent reader

- **Source phase**: Phase 4 - Executable guards and anti-regression tests
- **What was observed**: the first full `make test` equivalent failed once in `extensions/nexus-memory/tests/test_store.py::test_multiprocess_concurrent_append`. One of four worker processes entered `load_config` while another process was writing the shared JSON config and received `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.
- **Reproduction status**: the exact test passed twice immediately afterward, the complete `nexus-memory` suite then passed with 51 passes and 1 skip, and the final repository suite passed with 3,354 passes and 37 skips. The failure is intermittent but the traceback demonstrates a real unprotected read/write seam.
- **Suggested next step**: in the post-Phase-7 known-gaps pass, make config creation atomic or retry a bounded transient empty read, add a deterministic concurrency regression test, and rerun the full extension suite.

##### BG-2 - global integration runner ignores the explicit target root for home-relative destinations

- **Source phase**: Phase 5 - Distribution to every platform class
- **What was observed**: `runner.py install --scope global --target <throwaway>` documents the target as the global home root, but `SkillsIntegration.install_global` resolves configured destinations from `Path.home()` instead of `ctx.target_root`. A Phase 5 proof run therefore refreshed managed Codex and Copilot surfaces under the real user profile while writing only its manifest and summary under the throwaway target.
- **Immediate containment**: the newly inserted `Documentation Layout` block was removed from the user-level Codex `AGENTS.md`, preserving the existing managed markers and surrounding content. The remaining touched files were installer-owned generated surfaces; the run manifest records each action and checksum at `%TEMP%/nexus-phase5-20260826-a7f34c/.nexus-hub/install-manifest.json`.
- **Reproduction status**: deterministic. The run summary names `%USERPROFILE%\.codex\AGENTS.md` even though the supplied target was `%TEMP%/nexus-phase5-20260826-a7f34c`. The base implementation uses `(Path.home() / rel).resolve()` for global instruction destinations.
- **Suggested next step**: in the user-requested post-Phase-7 known-gaps pass, make every global integration resolve through the explicit target root, add a regression test proving an isolated target cannot touch the process home, and verify the documented default still resolves to the actual home when `--target` is omitted.

##### BG-3 - `link-baseline diff` is not move-aware, so its own gate cannot report zero on a whole-tree move

- **Source phase**: Phase 6 - Dogfood migration of Nexus-Hub's own tree
- **Plan reference**: `docs/releases/v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md` (6.3)
- **What was observed**: `cmd_diff` is a plain set difference over `(source, link, resolved_target)` tuples. A file that MOVES changes its `source` key, so every pre-existing broken link inside it is reported as `newly_broken` while its old tuple is reported as `fixed`. On this migration the raw diff read 873 `newly_broken` / 638 `fixed` when the true count of links broken BY the move was 444, and 0 after repair.
- **Why it matters**: the plan's acceptance gate is "zero `newly_broken`". As shipped, that gate is unreachable for the exact operation it was built to prove, and a maintainer reading the raw number would either block a correct migration or learn to ignore the gate.
- **How Phase 6 proved the property instead**: the before-baseline was normalized into post-move coordinates through the rename map, then compared on `(source, resolved_target)` pairs. That comparison reports 0 `newly_broken`, 59 `fixed`, 774 `unchanged`. The normalization script and its output are recorded in the phase session history.
- **Suggested next step**: add an optional `--rename-map <tsv>` to `link-baseline diff` that applies the same normalization internally, so the shipped gate reports the true number without an external script. Cover it with a test that moves a fixture tree containing one pre-existing broken link and asserts `newly_broken == 0`.

##### BG-4 - `old-version-docs-guard` treats the highest version directory as the active version

- **Source phase**: Phase 6 - Dogfood migration of Nexus-Hub's own tree
- **Plan reference**: `docs/releases/v4/v4.0/plans/v4.0.0-docs-lifespan-tree-and-enforcement.md` (6.3, "prove the Phase 4 guard live rather than only in fixtures")
- **What was observed**: active-version detection selects the newest `docs/releases/v*/v*/` directory on disk. This repository keeps directories for roadmapped future work (`v4.1`, `v4.2`), so the guard resolves active as `v4.2`. Writing to `docs/releases/v4/v4.0/known-gaps.md` - the version actually being built - emits `Writing to historical version v4.0 ... (active is v4.2)`, while writing to a future directory stays silent.
- **Reproduction status**: deterministic via the `.ps1` sibling. Pre-existing rather than migration-caused: `docs/v4/v4.1/` and `docs/v4/v4.2/` are both present in the pre-move inventory, so the guard has mis-detected in this repository since those directories were created. Phase 6 is simply the first run against the real tree instead of fixtures.
- **Suggested next step**: source the active version from a declared surface rather than from directory maximum, and treat a directory newer than the declared version as planned-future (silent) rather than as active. Add a fixture with a future-version directory asserting the current version does not warn.

##### BG-5 - bash hooks silently no-op on this workstation because `jq` is absent

- **Source phase**: Phase 6 - Dogfood migration of Nexus-Hub's own tree
- **What was observed**: `catalog/hooks/old-version-docs-guard.sh` gates its entire path-extraction step on `command -v jq`. No `jq` is installed on this host, so the hook exits 0 with no output for every payload, including ones it should warn on. The guard could only be exercised through its `.ps1` sibling, which parses with `ConvertFrom-Json` and needs no external binary.
- **Relationship to existing gaps**: same fail-open class as the previously recorded secret-scan `jq` gap carried from a prior version. Recorded separately because it was observed on a different hook and because it blocked a specific Phase 6 verification step (bash-side exit-code parity could not be demonstrated on this host).
- **The test suite hides it rather than catching it**: `catalog/hooks/tests/test_old_version_docs_guard.py` skips every Bash-leg case with `jq is required by the Bash hook`. On this workstation that suite reports `22 passed, 27 skipped` - green - while the entire Bash half of the sibling-parity contract goes unexercised. A skip standing in for an absent dependency is indistinguishable in the summary line from a passing assertion.
- **Suggested next step**: give the bash hooks a `python3 -c` JSON fallback when `jq` is missing, or state the dependency loudly at install time. A hook whose failure mode is silence is indistinguishable from a hook that passed. Separately, make the absent-`jq` case an explicit xfail or a loud warning rather than a silent skip, so a host that cannot exercise the Bash leg says so.

##### BG-6 - two dead documentation links predate the migration and remain unresolved

- **Source phase**: Phase 6 - Dogfood migration of Nexus-Hub's own tree
- **What was observed**: `docs/releases/v3/v3.18/development/github-drawdown-ledger.md` and `docs/releases/v3/v3.2/comparison-loop-engineering.md` are referenced but exist nowhere in the repository. Both appear in the pre-move baseline, so neither was caused by this migration. The referring link text was updated to the new container so it no longer names a directory that no longer exists; the targets themselves were not invented.
- **Suggested next step**: decide per link whether the target should be restored from history or the reference removed. Do not create a placeholder file to silence the checker.


#### Warnings

##### WN-1 - three extension suites cannot run to a meaningful result on this workstation

- **Source phase**: Phase 6 - Dogfood migration of Nexus-Hub's own tree
- **What was observed**: running the six `make test` extension suites gives `nexus-skill-server` 43 passed, `nexus-skill-scanner` 89 passed, and `nexus-memory` 51 passed / 1 skipped, but `nexus-code-search` fails collection with `ModuleNotFoundError: No module named 'nexus_code_search.config'`, `nexus-web-fetch` reports 3 collection errors, and `nexus-context-compressor` reports 3 failed / 234 passed.
- **Confirmed not caused by this migration**: the three compressor failures all assert `'regex' == 'ast'`, and `import tree_sitter_javascript` raises `ModuleNotFoundError` on this host, so the compressor is correctly falling back to its regex backend. `nexus_code_search.__file__` is `None`, meaning the name resolves to an empty namespace package rather than an installed distribution. This plan's only edits inside `extensions/nexus-context-compressor` are docstring and comment path references, which cannot affect language-backend selection.
- **Relationship to existing gaps**: the same environment class as the carried DF-2, which already records that the extension suites need their packages pip-installed. Recorded separately because the specific missing pieces are now identified rather than assumed.
- **Suggested next step**: install the missing language grammar and the two extension packages in the development environment, then re-run the six suites and record the result. Until then, CI is the authoritative run for these three suites, which is the same conclusion DF-2 reached for the aggregate profile.

### Resolved Items

##### Resolved - `canonicalize-layout` never migrated the archive container it documented

- **Source phase**: Phase 6 - Dogfood migration of Nexus-Hub's own tree
- **What was observed**: `docs-layout-refactor/SKILL.md` step 5 states that an approved `--canonicalize-layout` pass migrates legacy singular `docs/archive/` sources to `docs/archives/`, and plan step 6.2 depends on it. `cmd_canonicalize_layout` only ever enumerated active version directories, so the archive container was silently left behind. The path parser already understood both containers, which is why the drift was invisible to every prior test.
- **Resolution**: `_legacy_archive_container` now contributes the container rename to the same migration list, so it inherits the existing collision refusal and appears in the emitted records with layout `archive-container`. Three tests cover the migration, the collision refusal, and idempotency on an already-canonical tree.
