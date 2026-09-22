# Last-phase evidence - v4.10.0 plan-queue continuity

Fail-closed evidence for Phase 6 (T017-T026) of the [v4.10.0 plan-queue continuity plan](../plans/v4.10.0-plan-queue-continuity.md). One section per duty, each quoting its proving command or scan. A missing section, or an unresolved Goal-review or deep-pass finding without a recorded known gap, blocks the `/update release` handoff.

## Architecture refactor - v4.10.0

Scanned this plan's surface for empty directories, duplicates, orphans, and structural complexity.

```text
$ find docs/releases/v4/v4.10 -type d -empty
(no output)

$ python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 65 warnings)
```

Files this plan adds, all at their canonical locations:

```text
catalog/skills/workflow/plan-queue-assessment/SKILL.md
docs/releases/v4/v4.10/development/history/phase-{1..5}-*.md
docs/releases/v4/v4.10/development/phase-{1..5}-*.md
scripts/enumerate_plan_queue.py
tests/validators/test_enumerate_plan_queue.py
tests/validators/test_plan_renumber_references.py
```

**Finding: none.** No empty directory, no duplicate, no orphaned bundled resource. The new skill directory carries only `SKILL.md`, so it has no bundled subdirectory to orphan. The 65 warnings are the pre-existing grandfathered soft-cap set plus one transient; none names a file this plan touched.

No refactor was proposed, so no confirmation was required and nothing moved.

## Known-gaps reconciliation - v4.10.0

Created [`docs/releases/v4/v4.10/known-gaps.md`](../known-gaps.md) with **4 open items** (1 DF, 2 WN, 1 MT) and 3 resolved.

Open: DF-1 skill registration is documented as three files but four carry counts; WN-1 the residual check scans Markdown only; WN-2 the fast profile does not reach `tests/validators/`; MT-1 the GitHub repository description still says 336.

Other still-open ledgers were enumerated:

```text
$ ls docs/releases/*/*/known-gaps.md
docs/releases/v4/v4.1/known-gaps.md
docs/releases/v4/v4.10/known-gaps.md
docs/releases/v4/v4.8/known-gaps.md
docs/releases/v4/v4.9/known-gaps.md
```

The v4.9 ledger's WN-2 (vendor over-verification advice versus `verification-before-completion`) was re-checked against this plan's four added assessment steps, as the plan required. **Verdict: the steps do not become that gap's redundant self-check**, because every one of them is required to write an artifact rather than assert a check occurred. That requirement is stated in the skill, in all four consuming surfaces, and in the plan's own execution contract. WN-2's status is unchanged; this plan does not close it.

## Living docs architecture - v4.10.0

Checked the living surfaces against this plan's changes.

- `README.md` - three live catalog counts updated 336 to 337; two counts inside `## What's New in v4.9.0` deliberately left at 336, because they describe what shipped in that release and updating them would falsify a historical claim.
- `AGENTS.md` - two catalog counts updated. Its registration instructions are **not** updated; that gap is recorded as DF-1 rather than fixed silently, because widening it is outside this plan's scope.
- `docs/todos.md` - dashboard rows and the queued-work entry track 16/26 through Phase 5.
- `docs/decisions/` - a decision record for the queue-ordering policy is required by this duty and is written as part of it (see below).
- No `docs/testing/` or `docs/validation/` tree was invented.

## Git-tree hygiene - v4.10.0

```text
$ python scripts/check_release_preconditions.py --branches --repo-settings
  ... 12 merged remote branches listed ...
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  NOTE: the repository description disagrees with README.md:
    - skills: description says 336, README.md declares 337
```

Report only; no branch was deleted. The description drift is recorded as MT-1: it is a GitHub setting, not a file in this branch, and changing it silently on the maintainer's behalf is outside a code branch's authority.

## CI/CD coverage - v4.10.0

Terminal reconciliation against the canonical contract.

```text
$ python scripts/check_installer_parity.py
installer parity: PASS

$ python scripts/check_required_check_coverage.py
Required-check coverage: OK -- 10 declared context(s) across 2 branch(es),
every one produced unconditionally.

$ python -m pytest catalog/hooks/tests/test_installer_smoke.py -q
33 passed
```

| Field | Result |
|---|---|
| Provider detected | GitHub Actions |
| New commands | None. `enumerate_plan_queue.py` is maintainer tooling, declared in `DEV_ONLY_SCRIPTS`, and the installer-smoke suite proves the declaration is consistent. |
| New dependencies | None. Stdlib only. |
| New environment variables | None. |
| New test paths | Two, under `tests/validators/`, already collected by the `TESTS` group's `pytest tests` step. Verified by inspection at `scripts/ci/profiles.py:227`, not assumed. This closes the v4.9 QG-1 pattern for these paths. |
| New artifacts | None. |
| Installer parity | PASS, hard gate. |
| Required-check coverage | OK. Every required context is produced unconditionally, so none can sit Pending forever. |
| Pipeline files changed | **None.** CI/CD was not this plan's deliverable, and no difference against the contract required one. |

**One difference recorded rather than applied**: the `fast` profile does not reach `tests/validators/`, which is why a Phase 2 registry defect survived three phase gates. Adding a narrow `registry-consistency` step would close it. That is a pipeline change with its own cost and approval, so it is recorded as WN-2 rather than applied inside a content plan.

## Tier 3 deep pass - v4.10.0

**Blast radius**: this plan adds one executable script consumed by four documentation surfaces, plus two test modules. The runnable surface is small and deterministic; the documentation surface is large. Verdict: **run**, exercising the real end-to-end path rather than a synthetic fixture.

End-to-end exercise against the live repository:

```text
1. Enumerate the live queue
   $ python scripts/enumerate_plan_queue.py --root .
   v4.9.1      31     0  interactive-handbooks-and-presentation-default
   v4.10.0     10    16  plan-queue-continuity
   v4.11.0     25     0  adoption-cache-and-diagram-quality
   v4.12.0     23     0  sole-contributor-attribution  ?
   v4.13.0     34     0  adoption-evidence-driven-agent-improvement
   exit 0

2. Machine form is consumable
   99 plans; keys: done_tasks, error, note, open_tasks, path, slug, status,
   touched, version

3. Residual check, positive control (a version never renumbered)
   $ ... --check-residual v4.6.0
   reports README.md:396, a live rollback example -> correctly flagged as a
   reference that WOULD need repair if v4.6.0 were renumbered

4. Residual check, negative control (the current live version)
   $ ... --check-residual v4.10.0
   reports docs/todos.md:39 and :41 -> correctly finds real references
```

Cross-phase interaction checked: the Phase 5 `--check-residual` mode shares the Phase 1 scanner and did not disturb it (21 enumeration tests still pass alongside the 12 renumber tests).

**Findings from the deep pass**: one. The Phase 1 evidence asserted **101** plan files; the script's own count is **99**. The figure was written without being computed. Corrected in the Phase 1 evidence and session history, with the correction itself recorded so the original error is visible rather than erased. No other finding; nothing left unresolved at budget end.

## Goal-vs-codebase review - v4.10.0

**Plan Goal, restated**: make a comparison, a plan, an implementation phase, and a release each account for the OTHER plans queued around them, so a plan authored against one codebase state is re-validated before it is executed against a later one, and so queue order is a reasoned decision rather than an accident of allocation order.

Inspected as if the phases had not been implemented by this agent.

| ID | Satisfied by | Verdict |
|---|---|---|
| D1 | `scripts/enumerate_plan_queue.py`; reports version, slug, status, counts, touched paths; numeric sort and whole-tree scan pinned by tests; unreadable plan listed with exit 1 | **Met** |
| D2 | `plan-queue-assessment` Step 3 verdict table requiring named evidence; unreadable and undeclared both map to explicit unknown | **Met** |
| D3 | `cross-project-comparison` Step 6.6 with a required report section and a checklist line; `implementation-plan` `## Queued predecessors` with a checklist line | **Met** |
| D4 | Re-assessment in the implement-phase runbook at plan entry and every phase entry, feeding the existing Plan-delta disposition; explicit no-drift result required | **Met** |
| D5 | `update.md` governance step 5a, reporting-only, self-gating, forbidding a silent renumber | **Met** |
| D6 | Ranking rule with the class rule and refresh requirement in the skill; applied to the real queue in Phase 2 evidence with v4.9.1 last; renumber procedure propose-then-apply; `--check-residual` failing on one survivor, 12 tests | **Met** |
| D7 | This file | **Met** |

**Honest qualifications, not waivers.**

1. **D3 restructured existing diligence rather than catching a miss.** Applied retrospectively to the v4.11.0 artifacts, both findings the new sections would produce were already reached by hand in prose. The claim that survives is narrower than "catches what a careful author misses": a checklist line is checkable and prose is not.
2. **D4 found no drift on its one real run.** The step produced the right answer on a genuine boundary and wrote it down. It has not yet caught anything.
3. **D6's second ranking axis is a judgement, by design.** Parallel compatibility is computed; impact-on-harness is recorded reasoning. The plan says so and the skill says so, but a reader expecting a computed ranking will not get one.
4. **The plan cannot rank itself.** Its own placement at v4.10.0 was a maintainer decision, stated in the plan's Grounding section. The capability does not bootstrap.

**No gap requires a new known-gaps entry beyond the four already recorded.** Every D is met by a real artifact; the qualifications above bound the strength of the claim rather than leaving a criterion unsatisfied.

## Human/manual testing suggestions - v4.10.0

This plan's central axis cannot be verified automatically, because it encodes a judgement.

1. **Does the ranking match your priority intuition?** Read the ranking in the Phase 2 evidence. The rule put v4.10.0 first, v4.11.0 second, v4.13.0 third, v4.12.0 fourth, v4.9.1 last. A wrong answer looks like: a plan you consider urgent sitting at position 4 or 5 with a reason you do not accept. If that happens, the class rule or the impact axis needs revising, not the individual placement.
2. **Would you approve the renumber proposal as written?** Read the renumber procedure in the skill. A wrong answer looks like: a step you would not run unattended, or a missing step you know from experience is needed. Two such gaps were already found by replaying real renumbers; a third would suggest the replay method is too narrow.
3. **Is `--check-residual`'s historical-note exemption too generous?** It exempts any line matching `renumbered|renamed|was swapped|at authoring time|formerly`. A wrong answer looks like: a genuinely stale reference passing because the line happens to contain one of those words. Try it against a line you know is stale.
4. **Run `/compare` or `/plan` once and read the new section.** The wiring was verified by reading and by a one-owner grep, not by an end-to-end command run. The first real invocation is the honest test.

## Full-suite testing and stabilization - v4.10.0

Two complete runs of the native full profile, each about 85 minutes on this Windows host.

**Run 1, before the registry fixes:**

```text
$ python -u scripts/ci/run.py --profile full --reports-dir reports
FAIL: 41 passed, 3 failed, 0 skipped, 0 advisory in 5304.7s
  [FAIL] check_registry_entries (0.2s)
  [FAIL] stamp_guide_counts (1.2s)
  [FAIL] repo-tests (3908.5s)   -> 16 failing tests
```

**Run 2, after the fixes:**

```text
$ python -u scripts/ci/run.py --profile full --reports-dir reports
FAIL: 43 passed, 1 failed, 0 skipped, 0 advisory in 4997.2s
  [FAIL] repo-tests (3738.8s)   -> 11 failing tests
```

### The 16 failures, attributed

| Group | Count | Attribution |
|---|---:|---|
| `test_target_manifest.py` | 11 | **Pre-existing on `develop`** |
| `check_registry_entries` | 2 | This plan; fixed |
| Guide counts (`stamp_guide_counts`, `test_guide_counts`, `test_nexus_hub_guide`) | 2 | This plan; fixed |
| `test_selective_install` reachability | 1 | This plan; fixed |

**This plan's contribution to the remaining failure set is zero.** The five defects it introduced are fixed and their gates now pass.

### Proof that the 11 are pre-existing

`origin/develop` was checked out over the working tree and the module re-run with none of this plan's changes present:

```text
$ git checkout origin/develop -- .
$ python -m pytest tests/skills/test_target_manifest.py -q
11 failed, 42 passed, 2 skipped in 13.26s
```

Same 11 tests, same module. The working tree was restored and verified afterwards. Recorded as WN-3.

### The five defects this plan introduced, and what caught each

Worth stating plainly, because four of the five came from following a documented instruction that is incomplete:

1. `data/skills.json` `statistics` block not updated - caught by `test_registry_consistency.py` in Phase 5.
2. `path` field missing its trailing slash - caught by `check_registry_entries`.
3. `size` field an int where a dict is required - caught by `check_registry_entries`.
4. Skill absent from `data/bundles.json`, so unreachable by any install profile except `full` - caught by `test_selective_install.py`.
5. Generated guide still stamped 336 skills - caught by `stamp_guide_counts --check`.

**Not one was caught by the per-phase `fast` profile.** Defects 1 through 4 are all the same root cause, recorded as DF-1: `AGENTS.md` names three registration files and there are five, and `check_registry_entries.py --emit <skill>` would have prevented three of them by printing a correct entry.

## Publication and integration - v4.10.0

Approved and published 2026-09-11. One push, one integration pull request, as the lifecycle requires.

- **Branch**: `feat/v4.10.0-plan-queue-continuity`, 6 commits, 6 ahead / 0 behind `origin/develop` at push time (clean fast-forward, no rebase or merge needed).
- **Pull request**: [#198](https://github.com/bendourthe/Nexus-Hub/pull/198) into `develop`.
- **Result**: 23 checks passed, 0 failed, 1 skipped. The aggregate required context `ci-required` passed.

| Check | Result |
|---|---|
| `ci-required` (aggregate required context) | pass 2s |
| `tests` | pass 11m11s |
| `tests-windows` | pass 17m19s |
| `validate` | pass 46s |
| `guide-render` | pass 7m11s |
| `bootstrap-windows` | pass 4m16s |
| `bootstrap` (macos, ubuntu) | pass 1m50s, 2m9s |
| `installer-smoke` (macos, ubuntu, windows) | pass 15s, 12s, 38s |
| `install-smoke` (macos, ubuntu, windows) | pass 12s, 12s, 29s |
| `shellcheck` | pass 26s |
| `colocation`, `changes`, `detect`, `verify` | pass |
| `CodeQL`, `Analyze` (python, javascript-typescript) | pass 4s, 1m37s, 1m21s |
| `render` | skipping (no renderable change in this diff) |

**The `tests-windows` pass settles WN-3.** The 11 `tests/skills/test_target_manifest.py` failures recorded above are confirmed to be a property of the development host, not of the code: GitHub's Windows runner ships a git whose executable is a single-link regular file, so `resolve_trusted_git` admits it and all 11 ran green. A fixture fix that makes a local run on an affected host honest rather than red exists on `fix/target-manifest-git-trust-skip` and lands separately; it changes no product code and relaxes no security gate.

Post-merge work is deliberately minimal. `/update release` starts only after this pull request is green and merged.

# Last-phase evidence - v4.10.1 eval isolation and adaptive compaction

**Recorded**: 2026-09-22

This section preserves the v4.10.0 record above and records the final ten duties for the v4.10.1 adoption plan. Results are scoped to the named commands and hosts; historical failures remain visible rather than being rewritten as passes.

## Architecture refactor

The read-only structure scan reported:

```text
tracked_files=5767
obsolete_name_candidates=9
deep_non_doc_paths=110
duplicate_blob_groups=120
filesystem_empty_dirs=9
```

The nine obsolete-name candidates are the owned `scripts/lib/integrations/legacy.py` compatibility module and the explicitly marked `templates/ai-instructions/legacy/` subtree. Deep non-doc paths group under code-search evaluation/fixture trees, bundled reference trees, scanner data, and test fixtures; their nesting follows the owning package or skill. Duplicate blobs are dominated by archived snapshots, fixtures, and intentionally mirrored reference assets. The empty-directory walk emitted Windows long-path read errors inside retained v4.9 benchmark attempts, so its count is advisory; no tracked empty directory can be removed by Git, and the visible `.tmp` directory is runtime-only. No move or deletion passed the reference-repair and behavior-preservation threshold, so the sufficient refactor result is no structural mutation.

## Known-gaps reconciliation

All canonical `docs/releases/v4/v4.*/known-gaps.md` ledgers from v4.0 through v4.13 were inspected. Finalized ledgers remain historical. Stale release states in v4.9 and v4.13 were corrected, and the current ledgers were reconciled as follows:

- v4.10: DF-1, WN-2, and MT-1 are resolved. EV-1 and EV-2 remain honest vendor-CLI limitations because Gemini and OpenCode publish no complete configuration-isolation flag. WN-1 is a Markdown-only residual scan, WN-4 is a deliberately display-only bar, and MT-2 requires a real extension host.

- v4.11: WN-1 is resolved by the pre-version handbook refresh rule. SEC-1 received focused remediation for all eight CodeQL findings; 138 affected tests pass with nine host-specific skips, but the remote alert state remains pending until CodeQL analyzes the integrated revision. MT-5, MT-9, MT-10, and the recorded native-authoring gate remain bounded feature or manual-validation limitations rather than hidden closure claims.

- v4.12: WN-1 and WN-3 are resolved. WN-2 is the separately owned CI report/tool-lock enhancement, WN-4 retains the original unreproduced Windows failure, QG-1 is an immutable GitHub PR-ref limitation, QG-2 still lacks a public Code-sidebar account-name confirmation, QG-3 still lacks a completed authorized independent review, and DF-1 is dated after 2026-11-01. QG-4 is evaluated by the final full-profile run below without rewriting its original timeout receipt.

- v4.13: the ledger now records the merged and released 34-task result. WN-6 is resolved by PR #230's passing Ubuntu job and a direct WSL2 Ubuntu exercise that refused a symlink target without overwrite and disclosed a redirected ancestor. WN-2 through WN-5 are bounded source-availability and measurement-protocol findings with explicit future triggers; none is unfinished release implementation.

The release set therefore has no unowned implementation task. Remaining entries are named external, dated, manual-host, or deliberately deferred product limitations and stay visible for the next applicable owner.

## Living docs architecture

The living documentation roots remain purpose-based: handbooks under `docs/handbooks/`, decisions under `docs/decisions/`, and the active dashboard at `docs/todos.md`. No `docs/testing/` or `docs/validation/` tree was invented. `docs/README.md` and `docs/DEVLOG.md` remain the living index and development log.

The three required decision records exist and each carries `## Alternatives considered`: compaction gate conditions, eval CLI isolation, and the rejected authorship-provenance taxonomy. The decision validator reports `47 decision record(s) OK`.

Both mapped handbooks were regenerated after their declared adapter input changed. Their HTML remained byte-identical (`overview` SHA-256 `d061c7bf54f5a86aa9fb04ff46bc2aae412321c7bf9a9b06c1c845e6ec8be7ca`; `distribution` SHA-256 `8463c66d85d0d354374b89ceb2a10ddf8c9fe5138a866ad13606776d763cc557`), their evidence manifests bind the current adapter hash, and the full handbook gate reports both documents `verified` with `status: pass`. The overview browser matrix contains 200 tested states with zero failures.

## Git-tree hygiene

```text
$ python scripts/check_release_preconditions.py --branches --repo-settings
Branch hygiene (merged into origin/develop)
  1 merged branch(es) are cleanup candidates:
    - origin/fix/pre-push-new-branch-range
  (2 branch(es) with an open PR were excluded)
  2 branch(es) survive a CLOSED, unmerged PR:
    - origin/feat/guide-foundations-ml-integration
    - origin/fix/target-manifest-git-trust-skip
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  OK: repository description agrees with README.md
```

Deletion is deferred until after integration and patch-equivalence checks. The two open-PR branches are excluded by policy and will not be deleted by this cleanup.

## CI/CD coverage

Provider detection found GitHub Actions. The existing pipeline comparison produced the following field-by-field result:

| Contract field | Evidence and disposition |
|---|---|
| Repository-native profiles | `scripts/ci/run.py` and `scripts/ci/profiles.py` own fast and full local profiles; the fast profile now invokes strict registry consistency directly. |
| Event separation | Pull-request validation is in `ci.yml`; post-merge smoke/provenance is in `post-merge.yml`; release publication is tag/release scoped. |
| Runner selection | Ubuntu owns the full repository suite; PowerShell 5.1 and Windows-specific coverage remain explicit; macOS and Windows installer smokes cover host delivery. |
| Aggregate required check | `ci-required` resolves unconditionally. `check_required_check_coverage.py` reports 10 declared contexts across two branches, every one produced unconditionally. Phase 5 did not change the required-check set. |
| Permissions and immutable actions | Workflow validation passes; jobs use least-privilege permissions and actions are pinned to full commit SHAs. |
| Caching and concurrency | Existing browser cache and workflow concurrency policies remain scoped to the owning jobs and refs. |
| Path scoping | The Phase 5 real-host plugin job uses a job-level change filter rather than changing workflow triggers or required contexts. |
| Artifact retention and structured reports | Existing specialized jobs retain their artifacts; complete JUnit/coverage bundling and tool locks remain the owned v4.12 WN-2 enhancement rather than being silently claimed here. |
| Deployment boundaries | Release assets, attestations, and publication remain outside pull-request validation. |
| Failure recovery | The v4.13 prerequisite fixes make launch errors and timeouts name their command and terminate descendant process trees while preserving partial output. |
| Installer parity | `check_installer_parity.py` reports `installer parity: PASS`; multiple installers are checked against the same distributed surfaces and fallbacks. |

The Phase 5 job is job-level filtered, has a 15-minute timeout, `contents: read`, a scratch `CLAUDE_CONFIG_DIR`, a real plugin install/list assertion, and aggregation through the existing `ci-required` context. `validate_workflow_security.py`, installer parity, and required-check coverage pass locally.

## Tier 3 deep pass

Blast radius is repository-wide documentation, CI profile behavior, skill delivery, eval-runner policy, and retained handbook evidence, so Tier 3 was required. The plan artifact inventory and observed boundary exercises are:

| Artifact family | Boundary exercised | Result |
|---|---|---|
| Compaction retention and fire/suppress rubric | Eight executable rubric contracts plus negative mutations | 8 passed; evidence elimination remains prohibited |
| Eval CLI adapter and optimizer | Four-runner branch parity, model pinning, Claude/Codex isolation, fail-closed Gemini/OpenCode limits | 60 eval-loop tests pass; EV-1 and EV-2 remain recorded limitations |
| Runtime entry points | Repository instruction contract | 4 entry-point tests pass |
| Real-host plugin load | Scratch host validation, install, enable, and list | Host validation passed; Phase 5 workflow contract passed in 169 tests with 17 skips |
| Release comparator and blinding | Group-resume rule, headroom gate, HMAC blinding, rubric-only verdict | 60 eval-loop tests and bundle validation pass |
| Registry and living handbooks | Aggregate counts, install reachability, 200 browser states, mapped-input freshness | 90 focused registry/CI tests pass; handbook gate passes for both outputs |
| CodeQL backlog remediation | Test modes, cleanup assertion, adapter import graph | 138 affected tests pass with nine host skips; hosted scan pending |

The global repair budget was used on one observable handbook defect chain:

1. The first overview render reported 50 stage font-floor failures.
2. Scaling the duplicate figure captions removed those failures but exposed 20 caption-ceiling failures.
3. Hiding the duplicate slide-mode figcaption, while preserving its reading-view counterpart and visible slide heading, produced 0 failures across 200 states.

No fourth repair was needed. Later adapter remediation invalidated both handbook input hashes but did not change either HTML byte stream; both manifests were refreshed and the full gate returned `status: pass`.

Plan sufficiency audit: the plan named the correct owners, observable artifacts, failure boundaries, and terminal gates. The only disproved assumptions were already recorded rather than smoothed: Gemini/OpenCode lack complete isolation flags, and the existing handbook captions could not satisfy both stage and caption size constraints while duplicating the heading. No missing task was required to make the three Goal clauses true.

Terminal Tier 3 result: bounded pass. Every produced artifact was exercised at its real boundary or through its owning executable contract. Remaining findings are present in their known-gaps ledgers with owners and next steps; no unrecorded blocking finding remains.

## Goal-vs-codebase review

Plan Goal: adopt the selected eval-isolation and adaptive-compaction controls, prove real host loading, and make eval promotion deterministic without overstating unsupported provider isolation.

1. Every eval arm uses the same runner family, pins its model, and excludes operator configuration where the CLI documents a complete mechanism. Claude uses explicit setting-source isolation and Codex uses a disposable home/config boundary. Gemini and OpenCode fail closed behind the recorded EV-1 and EV-2 limitations instead of pretending partial flags isolate all configuration.

2. `.github/workflows/ci.yml` installs and enables the plugin in a scratch Claude host configuration, lists the installed plugin, and reports through the existing aggregate gate. The manifest derives its live 23-agent roster and local host validation passed.

3. The shipped `context-compression` `overview_l1` and rubric state both fire and suppress conditions. Required decisions, failures, evidence, unresolved threads, and provenance are retained; eliminating evidence is no longer classed as discardable.

All three clauses have code, docs, and executable evidence. No Goal clause is missing. Provider limitations are explicit known gaps, so this is a bounded pass rather than an unsupported universal-isolation claim.

## Human/manual testing suggestions

1. Run one real paired eval under the new isolation on a machine with Nexus-Hub installed globally and confirm the baseline response no longer displays catalog-skill behavior. Automated tests prove flag construction and clean homes, but cannot prove what the operator's installed model process chooses to say.

2. Open the weekly bars in a real VS Code extension host and confirm both bars align, resize, and announce their values. The current MT-2 ledger owns this host-rendering check.

3. Recheck the public GitHub Code sidebar contributor list while authenticated and record count plus account names. API and Insights evidence show the sole human contributor, but the unauthenticated page did not expose the account list needed to close v4.12 QG-2.

4. Revisit Gemini and OpenCode only when their official CLI documentation publishes a complete all-configuration isolation mechanism; do not infer one from partial flags.

## Full-suite testing and stabilization

The original failure receipts remain part of the qualification record:

1. The inherited monolithic Windows repository suite timed out at 4,500.8 seconds. That full-profile attempt ended `47 passed, 1 failed, 0 skipped, 0 advisory in 6018.8s`; the timeout had reached about 60 percent and named no owning test family.
2. The first ownership split retained every repository test but grouped installer, integration, and plan tests together. That diagnostic run ended `51 passed, 1 failed, 0 skipped, 0 advisory in 7436.1s`; only `repo-tests-runtime` timed out at 2,700.7 seconds.
3. Separating installer, integration, and plan owners proved installer and plan tests, but the still-monolithic integration directory timed out at 1,800.7 seconds around 56 percent. Explicit concern-based integration groups then passed focused runs of 107 tests; 187 tests with two skips; 162 tests with one skip; 54 tests; 103 tests; and 144 tests with two skips.
4. One full attempt crossed a host suspend/resume boundary and failed a hook parity case after Python calculated a negative remaining subprocess timeout. The exact case then passed in 1.95 seconds. Later full runs used a process-scoped Windows execution-state guard so the machine could not sleep; no power-plan setting was changed.
5. The first explicit-file full run exposed an older directory-only CI coverage assertion. Its file-level companion already proved every test file was covered. The directory guard now treats an explicit descendant file as reaching its parent while a new empty directory still fails; both owning coverage modules pass 69 tests.

No timeout was raised. `scripts/ci/profiles.py` now partitions repository tests at stable ownership boundaries, and `tests/ci/test_ci_engine.py` proves every collected test file appears exactly once with bounded commands. The terminal one-command run on the corrected revision passed:

```text
$ python scripts/ci/run.py --profile full
PASS: 59 passed, 0 failed, 0 skipped, 0 advisory in 7208.2s
```

Focused stabilization also passed: registry and CI consumers, 90 tests; workflow/CI consumers, 359 tests with 17 skips; CodeQL remediation, 138 tests with nine host skips; CI engine and repository-coverage owners, 69 tests; decision records, 47 OK; docs conventions; both handbook freshness/verification gates; and the fast profile, 16 commands with zero failures.

## Publication and integration

Pending. Resolved model: develop plus main, with `develop` as the protected integration target. Remote: `origin` (`bendourthe/Nexus-Hub`). Source branch: `feat/v4.10.1-eval-isolation-and-compaction`. The user's instruction to finish, merge, and clean the v4.0-v4.13 work authorizes the plan's first publication and integration after the local full gate passes. Required checks and the post-merge run will be recorded here from terminal GitHub results.
