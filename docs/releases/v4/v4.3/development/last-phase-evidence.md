# Last-Phase Evidence - v4.3.0 Agentic Verification Discipline

**Date**: 2026-08-30
**Plan**: `docs/releases/v4/v4.3/plans/v4.3.0-agentic-verification-discipline.md`
**Phase**: 5 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
**Branch**: `feat/v4.2.2-guide-cinematic-rebuild`
**v4.3 feature base**: `8ace852a8cc9ff8c0ff56ea58fdfaf5d8e9a7f02`
**Cumulative PR integration base**: `38a63ddccf89b279c4306d384002a42482ec4482`
**Deep-pass starting revision**: `0381fa82697317f22b02cd27918e9a0889345efd`

This is a live final-phase record. A section marked PENDING is incomplete and cannot support a completion claim.

## Architecture refactor

The Phase 5 structure scan covered tracked root files, version-named artifacts outside `docs/`, empty directories, deep paths, single-child directory chains, and duplicate content.

```text
version-named tracked artifacts outside docs/: 0
empty directories: 10, all ignored/generated work areas
duplicate-content groups: 7, all intentional independent consumers or package-local resources
architecture moves proposed: 0
architecture deletions proposed: 0
```

The duplicate groups were the five independently installed base instruction templates, three separately imported extension `updateWatcher.ts` modules, two guide pose examples, local skill-owned code-quality checklists, per-package TypeScript configs, package-local warning icons, and package-local license copies. Consolidating any group would couple independent installation or package boundaries without removing a user-visible defect.

The empty directories are ignored host or generated work areas: `.antigravitycli`, `.claude/worktrees`, `extensions/nexus-code-search/benchmarks/.work/` descendants, and `Microsoft/Windows`. No tracked content depends on them, and no repository artifact was deleted.

The durable architectural choice is recorded at `docs/decisions/implemented/process/2026-08-29-require-tiered-functional-evidence-before-completion.md`. `python scripts/validate_decision_records.py` passed 26 decision records. The decision keeps the four-tier ladder, named ownership handoffs, and one global three-cycle Tier 3 fix budget outside the release-only evidence tree.

## Known-gaps reconciliation

Every `known-gaps.md` ledger was inspected. Exactly three ledgers have `**Status**: in-progress`: v4.1, v4.2, and v4.3. Older ledgers retain their append-only finalized, released, or custom lifecycle states and were not rewritten.

- v4.1.0 DF-1, WN-1, and QG-1 plus v4.1.1 DF-1 remain owned by `docs/releases/v4/v4.1/known-gaps.md`; that ledger explicitly says not to absorb them. The prompting freshness advisory for this phase returned `UNKNOWN` because no live roster was supplied, so it writes nothing and remains covered by v4.1.0 DF-1 rather than becoming a duplicate v4.3 item.

- v4.2.3 DF-1 remains open because the Unicode validator still excludes `.html` and does not identify every wrong-script glyph. The detector and responsive hook do not change that validator.

- v4.2.3 DF-2 remains open because no five-person workshop cohort was available. Automated detector evidence is not a substitute for participants.

- v4.2.3 MT-1 remains open because the guide render harness still has no automated functional test. The new detector tests its own CLI, not `tests/guides/tools/render_guide.py`.

- v4.3 WN-1 records the live repository description advertising 328 skills while README and the catalog advertise 329. Its owner is the release publication flow; the next step is an authorized remote description update followed by `python scripts/check_release_preconditions.py --branches --repo-settings`.

- The CI approval decision is closed and its outcome is reconciled into the ledger. The three declined-or-deferred CI differences are recorded as v4.3 DF-1 (inline validators outside profiles), DF-2 (pip caches not keyed by manifests), and DF-3 (report profile does not aggregate or publish), and the UI-only settings remainder is WN-2. `docs/releases/v4/v4.3/known-gaps.md` now carries 4 open DF, 3 open WN, and 3 resolved BG items.

## Living docs architecture

`python scripts/check_docs_conventions.py --root` passed independently for the v4.2, v4.3, and untracked v4.4 release trees. The active v4.3 artifacts remain under `docs/releases/v4/v4.3/`; the reusable policy decision is under `docs/decisions/implemented/process/`; and `docs/todos.md` remains the one living progress dashboard.

`docs/handbooks/README.md` says not to invent an atlas when no handbook Markdown pages exist, so handbook generation is an evidenced no-op. `docs/DEVLOG.md` remains unchanged because `/update release`, not an unreleased implementation phase, owns the release index. No `docs/testing/` or `docs/validation/` tree was invented.

The whole-doc lifespan scanner still reports inherited historical language from the v4.0 layout migration and older release records. Current v4.2, v4.3, and v4.4 convention checks pass, so historical evidence was not moved or rewritten to silence a broad text heuristic.

## Git-tree hygiene

```text
$ python -B scripts/check_release_preconditions.py --branches --repo-settings
10 merged remote branches are cleanup candidates
12 open-PR branches were excluded
1 branch survives a closed, unmerged PR: origin/backmerge/v3.20.0
reporting only - nothing was deleted
delete_branch_on_merge is enabled
repository description mismatch: remote 328 skills; README 329 skills
```

The ten cleanup candidates are pre-existing `backmerge/v4.*` and `feat/v4.*` branches already merged into `origin/develop`. No remote branch was deleted. The current feature branch remains `feat/v4.2.2-guide-cinematic-rebuild`, and PR #146 targets `develop`; whether to retain or rename the stale branch name remains an explicit publication decision.

## CI/CD coverage

GitHub Actions is the detected provider. The initial read-only 23-field comparison found 15 PASS and 8 FAIL results. The user then approved bundles A, B, and F and explicitly deferred bundles C, D, and E. The reconciled disposition is 19 PASS and 4 DEFERRED; no repository setting was mutated.

| Contract field | Result | Evidence or disposition |
|---|---|---|
| Provider detected | PASS | Eleven local workflow files; live GitHub inventory includes the dynamic Dependabot workflow. |
| Repository-native profiles | PASS | `fast`, `full`, `platform`, `report`, and `release` resolve on Linux, macOS, and Windows. |
| No duplicated validator bodies | DEFERRED - DF-1 | Large inline validation lists remain outside profiles. The next CI/CD lifecycle plan owns incremental migration. |
| Feature-branch push runs nothing | PASS | Push triggers are protected branches, version tags, or explicit release events. |
| Integration gate complete | PASS | PR and merge-group paths cover full, platform, and real installer legs. |
| No duplicate post-merge suite | PASS | Bundle A removed the protected-branch push trigger; browser-free PR proof and the weekly rendered deep check remain. |
| Post-merge minimal | PASS | Presentify no longer performs a Chromium install or rendered suite after each protected-branch merge. |
| Release separated | PASS | `release.yml` is tag/manual only and runs the release profile. |
| Aggregate required check | PASS | Bundle B makes required `verify` evaluate with `always()` and fail explicitly when `detect` is not successful. |
| No per-leg required context | PASS | Required contexts are bare stable names. |
| Required checks have no workflow-level path filter | PASS | Path scoping is at job level and required workflows cover both protected branches. |
| Runner selection | PASS | Public-hosted latest runners only; zero self-hosted runners. |
| Expensive legs pre-merge | PASS | Windows and macOS bootstrap and installer matrices run on pull requests. |
| Immutable references | PASS | Every action reference is a 40-character SHA with a version comment. |
| Least privilege | PASS | Workflows default to `contents: read`; CodeQL adds only job-scoped security-event write access. |
| Caching | DEFERRED - DF-2 | Several pip cache keys follow workflow files instead of dependency manifests. The next CI/CD lifecycle plan owns manifests and deterministic cache keys. |
| Concurrency | PASS | Validation cancels superseded refs; post-merge and release deliberately do not. |
| Untrusted forks | PASS | No `pull_request_target`, secrets, or self-hosted execution; first-time contributor approval is enabled. |
| Reports produced | DEFERRED - DF-3 | The report profile remains empty; DF-3 owns the report schema and aggregation work. |
| Reports published | DEFERRED - DF-3 | Detailed reports are not uploaded; DF-3 owns unconditional bounded-retention publication. |
| Deployment boundary | PASS | CI does not deploy or publish; release readiness is isolated. |
| Failure recovery | PASS | Red checks must be classified, reproduced locally, narrowly fixed, and re-gated; blind reruns are forbidden. |
| Platform settings and runbook | PASS with WN-2 | Bundle F corrected the VSIX artifact statement and added dated API evidence. Default retention, merge-queue state, and runner-class billing remain explicit UI-only checks under WN-2. |

T021-specific coverage is green: the new skill, detector, deep-pass resource, HTML rule, paired hook, registration, and `tests/verification/` are collected by existing profiles. CI does not install Playwright or Chromium on pull requests; renderer-dependent tests skip cleanly when `NEXUS_REQUIRE_RENDER` is unset and run in the weekly scheduled renderer. `python scripts/check_installer_parity.py`, the required-check guard, and the workflow-security validator passed. The workflow suite passed 97 tests with 13 environment skips, and the real installer/postcondition suite passed 20 tests before the approved stabilization. Platform-contract verification is recorded separately after the approved coupled bundle completes.

Independent review found that the artifact-retention validator operated at whole-file substring scope, so one bounded upload could hide a second unbounded upload. A proving regression failed before correction. The validator now inspects each parsed `actions/upload-artifact` step, requires a positive integer or explicit nonblank GitHub expression in that step's `with.retention-days`, covers quoted action syntax, and returns an explicit cannot-validate exit 2 when PyYAML is unavailable rather than emitting a false policy finding. The final validator plus Presentify focused set passed 21 tests. The live workflow-security scan exited 0, and required-check coverage reported all 10 declared contexts across both protected branches as unconditionally produced.

The final independent CI/workflow verdict is APPROVE with no remaining actionable finding. `actionlint` is unavailable on this host, so no independent GitHub-expression linter result is claimed; repository YAML parsing, workflow policy tests, required-context coverage, and the full local gate remain the executable evidence.

Bundle decisions are complete. The approved platform-contract bundle is verified on the final tree: `python scripts/verify_platform_contracts.py --quiet` exits 0 and `python scripts/check_platform_contract_freshness.py` reports `[contract-freshness] OK: contract verified for v4.1.2 (last_verified 2026-08-30)`. The `platform-contracts` group is one of the ten groups in the green `full` profile quoted under `## Full-suite testing and stabilization`.

## Tier 3 deep pass

### Blast-radius verdict

- **Verdict**: run.
- **Positive triggers**: the v4.3 diff changes a public detector CLI, hook payload behavior, distributed rules and skills, installer upgrade behavior, plugin and registry metadata, plan-generation contracts, phase-gate contracts, and final release workflow behavior.
- **Diff scope**: 64 committed v4.3 paths at the Phase 5 start, including catalog content, hooks, scripts, installers, registries, tests, and release evidence.
- **Ambiguity check**: none; multiple explicit run triggers apply.

### Feature inventory

| Feature | Source | Real boundary | Representative observation | Status |
|---|---|---|---|---|
| Four-tier verification contract and blast-radius economy | T001-T002 | Release contract consumed by workflow skills | Cross-links and lifecycle contract tests load the named tiers and owners | exercised |
| Visual-defect detector CLI and proving fixtures | T003-T004 | `detect_visual_defects.py <html> --viewports ...` | Clean fixture exits 0, broken fixture exits 1, real guide exits 0 after two bounded fixes | exercised |
| Responsive-layout rule | T005 | Installed `catalog/rules/html/responsive-layout.md` | Installer postconditions find the rule; HTML-producing surfaces cite it | exercised |
| Paired responsive guard and registration | T006-T007 | Bash and PowerShell stdin JSON hooks | Six-case supported-host matrix has matching exits and signals | exercised |
| Functional-verification skill and deep-pass resource | T008-T010 | Plugin/registry resolution and agent skill load | Registry path, `SKILL.md`, deep-pass reference, detector script, and plugin testing root all resolve | exercised |
| Tier 1, Tier 2, and Tier 3 phase lifecycle wiring | T012 | Installed `implement-phase` contract | Lifecycle suite proves five-part gate, plan delta, fail-closed final duty, and ordering | exercised |
| Verification expectations in generated plans | T013 | `implementation-plan` templates | Contract suite proves per-phase exercise expectations and final deep-pass placement | exercised |
| Ownership-safe cross-links and HTML producer guidance | T014 | Distributed skill and command bodies | Cross-link suite proves named handoffs without duplicated policy | exercised |
| Dual-installer managed-hook convergence | T015 | Native installer passes against scratch settings | Three-pass upgrade, idempotence, wrong-host repair, preserved user settings, and artifact postconditions pass | exercised |
| Completion-evidence recognition and final claim discipline | T014 | `verification-before-completion` and final-phase contracts | Contract suite requires observed behavior and fail-closed evidence | exercised |
| Independent adversarial verifier | T022 | `ADVERSARIAL-REPORT.md` | Scoped APPROVE after three confirmed detector findings were corrected and independently retested | exercised |
| Code-vs-plan convergence and Goal-vs-plan sufficiency | T022-T023 | Approved plan against current tree | Preliminary REQUEST CHANGES: BG-1 through BG-3 block completion | blocked |

### Functional exercise - visual detector CLI

- **Revision**: `0381fa82697317f22b02cd27918e9a0889345efd` plus Phase 5 detector visibility and guide legibility fixes.
- **Artifact and boundary**: CLI at `catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py`.
- **Command or action**: `python .../detect_visual_defects.py <target> --viewports 420 900 1440`.
- **Input**: `clean.html`, `horizontal-overflow.html`, and `guides/website/nexus-hub-guide.html`.
- **Expected contract**: clean and remediated real page exit 0 with JSON `status: pass`; broken fixture exit 1 with JSON `status: fail` and three `horizontal-overflow` findings.
- **Observed output or state**: clean `exit=0 status=pass gate_findings=0`; broken `exit=1 status=fail gate_findings=3`; final guide `exit=0 status=pass gate_findings=0` across three viewports.
- **Comparison**: matches after three global fix-and-rerun cycles.
- **Evidence path**: this section plus `tests/verification/test_visual_defect_detector.py` and the named fixtures.

Initial real-guide execution produced 28 high findings: 6 parent-padding escapes, 16 text overlaps, and 6 font-floor violations. Cycle 1 added a regression proving that Chromium exposes nonzero geometry for descendants of a closed `details`, then fixed the detector's shared visibility predicate; the detector suite passed 18 tests and the real page fell to 6 genuine findings. Cycle 2 raised only the two visible page-navigation labels from 10.5 px to the 12 px floor; the guide detector passed all three viewports and the guide suite passed 73 tests with 1 expected skip. The independent verifier then found three bypass or false-negative cases: non-finite numeric controls, fixed text caps expressed through CSS custom properties including linked local CSS, and visible `aria-hidden` pixels excluded from geometry checks. Cycle 3 rejected non-finite values, resolved custom-property chains, inspected browser-linked local CSS through bounded reads without weakening Chromium file isolation, and kept aria-hidden pixels in geometry checks while excluding decorative text only from semantic legibility rules. The corrected detector suite passed 26 tests, the real guide remained clean across all three viewports, and the directly impacted skill plus detector contract suite passed 40 tests.

### Functional exercise - paired responsive guard

- **Revision**: `0381fa82697317f22b02cd27918e9a0889345efd` plus the current Phase 5 tree.
- **Artifact and boundary**: `catalog/hooks/html-responsive-guard.sh` under Git Bash and `html-responsive-guard.ps1` under Windows PowerShell 5.1.
- **Input**: legitimate container CSS, blocked text cap, malformed JSON, irrelevant path, disabled hook, and literal `$(whoami)` text in path and content.
- **Expected contract**: equivalent exit and stderr signals; allowed/malformed/irrelevant/disabled exit 0; blocked and hostile fixed text caps exit 2 without evaluating input.
- **Observed output or state**: all six cases matched on both hosts; blocked cases emitted the guard marker; hostile text remained literal; no stdout or evaluated command output appeared.
- **Comparison**: matches.
- **Environment note**: an initial run through `C:\Windows\System32\bash.exe` did not forward the disable variable and was rejected as an environmental false result. The repository explicitly excludes that WSL launcher and resolves Git Bash; the authoritative rerun used `C:\Program Files\Git\bin\bash.exe`.

### Functional exercise - skill, templates, and installers

- **Registry resolution**: `REGISTRY_PATH=catalog/skills/testing/functional-verification/ SKILL_EXISTS=True DEEP_PASS_EXISTS=True DETECTOR_EXISTS=True PLUGIN_TESTING_ROOT=True`.
- **Lifecycle and template command**: `python -m pytest -q tests/skills/test_functional_verification_crosslinks.py tests/skills/test_implement_driver_modes.py tests/skills/test_implement_lifecycle_contract.py tests/skills/test_installer_parity_lifecycle.py tests/skills/test_last_phase_fail_closed.py tests/skills/test_plan_lifecycle_contract.py`.
- **Lifecycle and template result**: 105 passed.
- **Installer command**: `python -m pytest -q tests/installer/test_managed_hook_upgrade.py tests/installer/test_installer_smoke_postconditions.py`.
- **Installer result**: 20 passed in 27.97 seconds; exit 0.
- **Observed install state**: the skill body, detector, deep-pass reference, HTML rule, host-correct hook file, and one host-correct Write/Edit registration reach scratch destinations; repeated installs are idempotent and a wrong-host managed registration is repaired without removing user settings.

### Rendered-surface delegates

The v4.3 product surface is a CLI detector, a hook, distributed Markdown contracts, and installer behavior, not a new browser UI. Browser DevTools, accessibility, hallmark-design, and interface-review are therefore not applicable to the v4.3 surface. A real local HTML page was used as detector input; the detector observed its geometry but this plan did not redesign that page. The two visible legibility findings caused by the new gate were fixed and re-exercised.

### Adversarial verifier

`docs/releases/v4/v4.3/development/ADVERSARIAL-REPORT.md` records the independent result and ends `APPROVE`. Fresh receipts were 26 detector tests passed; clean CLI exit 0 with zero findings over 420, 900, and 1440 px; the custom-property fixture exited 1 with exactly three high findings across embedded, inline, and linked local CSS; the aria-hidden fixture exited 1 with exactly one horizontal-overflow and no font-floor finding; non-finite tolerance exited 2; responsive-hook parity passed 47 tests; and installer postconditions passed 20 tests. AF-1, AF-2, and AF-3 are all marked FIXED, with zero remaining scoped finding.

### Implementation convergence

The preliminary independent review returned `REQUEST CHANGES` with three HIGH product-Goal gaps, now recorded as v4.3 BG-1 through BG-3. Both hook siblings allow `max-width: var(--measure)` when `--measure` resolves to a fixed `60ch`, so the hook and detector disagree. The POSIX hook exits 0 when Python is absent even though the selector-free install contract permits that environment. The POSIX installer copies hook files but skips existing-settings registration when jq is absent, leaving the discipline inert after an otherwise successful upgrade. T023 remains incomplete until the user authorizes a bounded stabilization, the findings are corrected or explicitly deferred, and a fresh independent reviewer inspects the resulting final tree.

### Goal-vs-plan sufficiency audit

| Question | Answer | Evidence | Change needed now | Owner |
|---|---|---|---|---|
| What did implementation teach that the plan did not know? | Chromium can expose measurable geometry for hidden descendants of closed disclosures, so display, visibility, opacity, and dimensions alone are not a complete rendered predicate. | Initial real-guide detector result and the new closed-disclosure regression. | Added semantic `details` state to the detector predicate. | v4.3 implementation |
| What plan assumption turned out false? | A first detector pass over a real page was assumed to separate rendered defects from hidden content; it produced 22 hidden-content false findings. | Initial 28 findings, cycle 1 rerun with 6 remaining. | Fixed in cycle 1 and reran all detector tests. | v4.3 implementation |
| What would a reader of the Goal expect that no phase delivered? | The write-time hook should enforce the same fixed-cap rule as the detector, remain visibly fail-closed when its parser is unavailable, and become active on POSIX existing-settings upgrades without jq. | Independent review against the hook siblings, `scripts/installer.sh`, the responsive rule, T007, and T015. | Resolve or explicitly defer BG-1 through BG-3; all three currently block the Goal review. | v4.3 Phase 5 stabilization |
| What did the maintainer ask for that no task captured? | The plan captured the expected outcomes, but its proving matrix did not include CSS-variable hook inputs, no-Python hook runtime, or no-jq POSIX existing-settings upgrade branches. | Existing Phase 2 and Phase 4 test matrices plus independent convergence probes. | Add these cases to the paired-hook and real-installer regressions if the bounded stabilization is authorized. | v4.3 Phase 5 stabilization |

`fix_rerun_cycles_used=3` of the global maximum 3. No cycle remains. Dogfooding also exposed ambiguity about corrections made before the full initial inventory was complete; `references/deep-pass.md` now states that evidence collection is cycle zero but every tree-changing correction caused by the pass consumes a cycle, and a focused contract test enforces that no pre-counter repair window exists.

The required quality-gate disposition at cycle exhaustion is split by scope. The corrected detector-surface testing gate is **PASS**: all required focused regressions pass, the real guide has zero findings, and the adversarial verdict is APPROVE. The overall Phase 5 gate is **NO-GO (blocking)** because independent convergence found BG-1 through BG-3 after the third cycle; those residual findings were given to `known-gaps-tracker`. The gate also remains incomplete until the CI and platform-contract approval decisions are resolved and the fresh full local gate passes. No required criterion was disabled or waived.

## Goal-vs-codebase review

Reviewed by a session that did not implement Phases 1-4 and did not author any artifact under review. The tree was inspected directly; prior-phase checkboxes were not consulted as evidence.

**Goal restated**: Nexus-Hub stops verifying only artifacts and starts verifying behaviour. A tiered verification ladder ships in the catalog: cheap deterministic checks at every phase gate including a functional smoke of what that phase actually built, a recorded plan-delta note so the plan is questioned as it is executed, and a fail-closed deep pass before release that dynamically exercises every feature the plan produced, checks rendered output for visual defects with a real detector, runs an adversarial pass, and audits whether the plan itself was complete -- all scaled to blast radius. Every consuming project inherits it on install.

| Goal clause | Verdict | Artifact evidence |
|---|---|---|
| The ladder exists as a contract | PASS | `docs/releases/v4/v4.3/development/verification-ladder.md` states the tier boundaries, triggers, and costs as a written contract rather than prose guidance. |
| Tier 1's functional smoke is in the gate | PASS | `catalog/skills/workflow/implement-phase/SKILL.md:69` makes the GO/NO-GO gate five-part: the fifth part is a proportional real-boundary functional smoke whose expected and observed behavior must match through `[[functional-verification]]`, or the bypass is recorded as a gap. |
| Tier 2's plan-delta note is in the post-phase sequence | PASS | Step 8.4 in `catalog/skills/workflow/implement-phase/references/implement-phase-runbook.md:72` always writes one `## Plan delta` disposition (No delta / Wrong / Incomplete / False assumption) with evidence and the consequence for remaining phases; `No delta` is an explicit written result, not an omitted section. |
| Tier 3 is a fail-closed final-phase duty | PASS | `catalog/skills/workflow/implement-phase/SKILL.md:39` and `:44` place the deep pass in the final-phase duty set, block the `/update release` handoff while the evidence file is missing or a deep-pass or Goal-review miss is unresolved, and allow omission only through a recorded `QG` or `DF` gap. |
| The detector runs and gates | PASS | `catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py` executes against real pages; `tests/verification/test_visual_defect_detector.py` plus the `tests/verification/fixtures/visual/` proving fixtures gate it, and renderer-dependent cases skip cleanly when `NEXUS_REQUIRE_RENDER` is unset so no CI browser download is required. |
| The rule and hook ship and fire | PASS | `catalog/rules/html/responsive-layout.md` ships the rule; `catalog/hooks/html-responsive-guard.sh` and its required `.ps1` sibling ship the enforcement; `catalog/hooks/settings.json:101` and `:126` register the hook on the write paths so it fires without being remembered. |
| Blast-radius scaling is objective | PASS | `catalog/skills/testing/functional-verification/references/deep-pass.md:17-30` decides depth from the final diff against the integration base using five enumerated triggers, defaults ambiguous classification to `run`, and permits `no-op` only for release evidence or living prose that changes no command, contract, generated output, or user workflow. |
| Every artifact reaches a real install | PASS | The rule, hook pair, skill, bundled detector script, and deep-pass reference all sit inside the recursively copied `catalog/rules/`, `catalog/hooks/`, and `catalog/skills/` trees, so no installer name-list edit was required; `configs/installer-parity.json` records the one POSIX-only settings-write helper with its reason. `python -m pytest tests/installer/test_verify_read_paths.py tests/skills/test_functional_verification_crosslinks.py` passed 38 tests in 1.15s, proving destination read-paths and skill cross-links resolve. |

**Gaps found**: none that leave a Goal clause unsatisfied. Every clause is satisfied by a shipped artifact rather than by a plan checkbox. The four deferred CI items (DF-1 through DF-3, WN-2) and the three warnings recorded in `docs/releases/v4/v4.3/known-gaps.md` are outside the Goal text and remain owned by that ledger; none of them removes a Goal clause from the catalog.

**Scope note honestly recorded**: this review verifies that the discipline is present, wired, and executable. It does not and cannot verify that the discipline is *pleasant* to run or that a stranger can follow the deep-pass runbook unaided; both are human questions and are listed under `## Human/manual testing suggestions` rather than claimed here.

## Human/manual testing suggestions

Automated tests cannot settle these four user-level questions:

1. Install this release into a real scratch project and confirm the rule, hook, skill, detector, and deep-pass reference arrive and the hook fires through the actual assistant host.
2. Run one small real plan end to end under the five-part phase gate and final deep pass; judge whether the per-phase cost feels proportionate rather than annoying.
3. Edit legitimate responsive CSS in a real project and confirm the hook permits container and media bounds while blocking only fixed text caps.
4. Give the deep-pass runbook to someone who did not author it and record whether they can complete the inventory, delegates, four-question sufficiency audit, and global cycle counter without clarification.

These are suggestions, not claimed executions. No fake participant, usability result, or live-host observation is recorded.

## Full-suite testing and stabilization

Phase 4 established a fresh baseline of 3,588 passed and 38 skipped in 3,172.97 seconds. That result predates the Phase 5 detector and guide corrections and therefore does not close T025.

The gate was run twice. The FIRST run was RED and reopened the phase, which is recorded here rather than replaced, because a gate that only ever reports its final green state cannot be audited.

Run 1 (pre-repair), `python scripts/ci/run.py --profile full`:

```
6 failed, 3665 passed, 47 skipped in 2828.07s (0:47:08)
FAIL: 41 passed, 1 failed, 0 skipped, 0 advisory in 3733.5s
PROFILE_EXIT=1
```

The six failures were regressions from this branch's uncommitted platform work, not inherited flakiness: a detached worktree at `HEAD` ran the same three affected files and passed 29 of 29. Three root causes were isolated and fixed test-first (Copilot opt-in gate ordering; a Windows 8.3 short-name path comparison that made managed writes silent no-ops; and a vendor-verified instruction-path move applied to one adapter but not the other). The residual limitation is recorded as DF-5. Full narrative: `history/2026-08-30_v4.3.0-agentic-verification-discipline-phase-5-stabilization.md`.

Targeted re-verification across every previously failing file plus the ownership suite:

```
89 passed, 2 skipped in 132.72s (0:02:12)
```

The two skips are the pre-existing privilege-gated native-symlink cases; both of their ownership branches also have privilege-independent deterministic coverage.

Run 2 (post-repair), `python scripts/ci/run.py --profile full`:

```
profile: full   platform: windows
- catalog-parse / hygiene / catalog / security / workflows
- platform-contracts / docs / version / tests / extension-tests
PASS: 42 passed, 0 failed, 0 skipped, 0 advisory in 3575.1s
PROFILE_EXIT=0
```

`python scripts/ci/run.py --profile fast`:

```
PASS: 12 passed, 0 failed, 0 skipped, 0 advisory in 99.2s
FAST_EXIT=0
```

`python scripts/ci/run.py --profile platform`:

```
- shell-lint: SKIP (no command in this group runs on windows)
- powershell-parse
- windows-hooks
PASS: 3 passed, 0 failed, 0 skipped, 0 advisory in 729.9s
PLATFORM_EXIT=0
```

The `shell-lint` group is skipped by design on a Windows host; ShellCheck is the Linux leg of the platform profile and is covered by the integration pipeline, not claimed here.

Reporting limitation stated honestly: both full runs used `--quiet`, which reports group-level results. The per-test counts quoted for run 1 come from the failure summary the runner printed on failure; run 2's green result is quoted at the group level, which is the level the gate itself decides at. The targeted 89-test count above is the per-test evidence for the repaired surfaces.

## Publication and integration

**Branch-name decision (recorded, not deferred)**: the branch stays `feat/v4.2.2-guide-cinematic-rebuild`. The plan required either a proposed rename or a recorded reason; the maintainer chose to keep it. Reason: PR [#146](https://github.com/bendourthe/Nexus-Hub/pull/146) already exists against this ref and is referenced from the plan and this evidence file. Renaming rewrites the remote ref at the final step and risks detaching the existing pull request, which is real risk for a cosmetic gain. The name under-describes the branch contents (it carries v4.2.2, v4.2.3, and v4.3.0); the pull-request title and body carry that description instead.

**Commit scope decision**: the untracked `docs/releases/v4/v4.4/plans/v4.4.0-guide-depth-and-training-rebuild.md` is included in the Phase 5 commit. Sub-task 5.1 explicitly scoped this branch as carrying "a v4.4.0 plan authored but unimplemented" and required the docs tree to be coherent across all four versions; `check_docs_conventions.py` already passes on that tree. Committing it makes the tracked tree match what this evidence file describes.

**Authorization**: the maintainer authorized ONE push updating PR #146 and the required-check wait. Merge is NOT authorized and requires a separate explicit approval after the checks reach a terminal state.

### Push 1 - commit 89bf4e40 (RED)

The branch was pushed once (`971096fa..89bf4e40`, clean fast-forward) and PR #146 was retitled and rewritten to describe both the guide and the harness capability. Required-check results:

| Check | Result |
|---|---|
| `validate` | pass (37s) |
| `shellcheck` | pass (19s) |
| `verify` | pass (1m38s) |
| `colocation` | pass (7s) |
| `ci-required` | **fail** (2s, aggregate) |
| `tests` | **fail** (11m31s) |
| `tests-windows` | **fail** (10m39s, 1 failed / 247 passed) |
| `install-smoke` (ubuntu, macos, windows) | **fail** |
| CodeQL, `Analyze` (js/py), `bootstrap` (3 OS), `installer-smoke` (3 OS), `changes`, `detect` | pass |
| `render` | skipping (browser-free PR path, by design) |

A red required check REOPENED the phase. Each failure was reproduced locally before any fix, and nothing was re-run blind.

**Why a green local gate did not predict this.** Three of the four causes are host- or environment-dependent and are unreachable from a single Windows developer host: a Windows-only `stat` constant, a Windows `st_nlink` value that differs between hosts, and CI assertion strings exercised only by the real installer smoke. This is the case FOR the PR being the plan's first remote validation, not an argument against the local gate.

1. **`tests` (Linux).** `test_owned_junction_detection_supports_python_without_path_is_junction` read `stat.IO_REPARSE_TAG_MOUNT_POINT` at class-definition time. That constant is Windows-only, so on Linux the test was an unconditional `AttributeError` rather than a check of the reparse-tag fallback branch. It now pins the documented tag value and exercises the branch on every host.

2. **`tests-windows`.** `test_copilot_canonical_authoritative_child_may_allow` expected `allow` and received `deny`. The Copilot permission bridge required `st_nlink == 1` exactly; Windows populates `st_nlink` only when the stat call opens a handle, so a host taking the fast path reports `0` and EVERY authoritative rewrite was denied. Reproduced locally by simulating `st_nlink = 0` (a failing-first regression test), then fixed by testing `> 1`, which is the predicate that actually detects a hard link and the one `_owned._is_link_like` already uses. Hard-link and junction protection re-verified: 17 passed, 2 skipped.

3. **`install-smoke` (all three OS).** `ci.yml` asserted the literal `"Codex / ChatGPT -- skills:ok"`, but the verify label became `"Codex / ChatGPT -- ~/.agents/skills:ok"` when Codex skills moved to the shared `.agents` ladder. Confirmed against live `runner.py verify` output on this host.

4. **A second stale assertion the CI never reached.** The smoke's expectation loop exits on first mismatch, so fixing cause 3 immediately exposed `"Gemini IDE -- skills:ok, workflows:ok"`. The current verified read contract records Gemini Code Assist as MATCH ONLY for the documented `GEMINI.md` instruction hierarchy, with IDE-specific workflow, skill, agent, rule-directory, and hook discovery UNVERIFIED and "excluded from the enforced install check" (`docs/policy/platform-read-contracts.md`). The assertion was stale, not the product; it is now `"Gemini IDE -- GEMINI.md:ok"`. The contract was checked BEFORE the assertion was edited, specifically so a test was not rewritten to match broken output.

Causes 3 and 4 are edits to `.github/workflows/ci.yml`. That is in scope: terminal CI/CD reconciliation is this phase's stated deliverable (sub-task 5.5), not opportunistic pipeline work.

**Local re-verification before any re-push.** CI's exact install-smoke assertion loop was replayed against a throwaway `HOME` on this host and all five expectations matched. The full local gate was then re-run:

```
PASS: 42 passed, 0 failed, 0 skipped, 0 advisory in 2956.7s
PROFILE_EXIT=0
```

```
PASS: 12 passed, 0 failed, 0 skipped, 0 advisory in 18.3s   (fast)
FAST_EXIT=0
```

### Push 2 - stabilization

Commit `2248cc6e` was pushed after approval. Three of the four causes were confirmed fixed remotely; one was not.

| Check | Push 1 | Push 2 |
|---|---|---|
| `tests` (Linux) | fail | **pass** |
| `install-smoke` (ubuntu / macos / windows) | fail | **pass** |
| `validate`, `shellcheck`, `verify`, `colocation`, CodeQL, `bootstrap`, `installer-smoke` | pass | pass |
| `tests-windows` | fail | **fail** (1 failed / 248 passed) |
| `ci-required` | fail | fail (aggregate) |

**A wrong diagnosis, corrected.** The Push 1 analysis attributed the `tests-windows` failure to the `st_nlink == 1` predicate. That was wrong, and the fix based on it did not change the result. The decisive evidence was reading which branch emits the observed message rather than reasoning further about the test:

| Condition | Bridge output |
|---|---|
| child `returncode != 0` | `{"permissionDecision": "deny", "permissionDecisionReason": "Nexus-Hub guard denied the tool call."}` |
| authority denied | `{"modifiedArgs": {"command": "git status"}}` |
| authority granted | `{"permissionDecision": "allow", ...}` |

CI's observed output matched the first row exactly and the second row not at all, so permission authority was never involved. The `st_nlink` change was therefore **reverted** along with the regression test written for it: its motivating hypothesis was disproven, and loosening a security predicate without evidence is not justified by tidiness.

**The actual cause, and why it is a user-facing bug.** The child exited non-zero with an EMPTY stderr and the default reason. A missing interpreter raises `OSError` and surfaces a `hook-compat:` reason instead, so `bash` was found, ran, exited non-zero, and wrote nothing to stderr. That is the signature of the Windows WSL launcher stub at `C:\Windows\System32\bash.exe`, which prints its "no installed distributions" notice to STDOUT. `tests/conftest.py` already documents this exact hazard for the test suite; the bridge had no equivalent protection.

The consequence reaches users, not only CI. On a Windows host whose PATH `bash` is that stub, EVERY guarded tool call would be denied with no diagnostic, which reads as a broken agent rather than a missing interpreter. The guard failed closed, which is correct, but for a reason no user could act on.

`_resolve_bash_command` now rewrites a BARE `bash` to a verified absolute Git Bash on Windows. Its boundaries are deliberate and tested: an absolute interpreter the caller chose is never second-guessed; a host with no Git Bash keeps the original command so PATH resolution still applies; POSIX is untouched; and the rewrite happens at the execution site ONLY, so `_copilot_permission_authoritative` still inspects the original command and its binding is unchanged. Five focused tests cover those boundaries.

Local gate after the correction:

```
PASS: 42 passed, 0 failed, 0 skipped, 0 advisory in 2796.0s
PROFILE_EXIT=0
```

`tests/integrations/test_copilot_hermes_native.py`: 64 passed, 2 skipped.

### Push 3 - interpreter resolution

Commit `185e8937` was pushed after approval. `tests-windows` **passed**, confirming the WSL-stub diagnosis and the interpreter resolver. `tests` (Linux) failed on a defect in the TEST written during that round, not in the product: it patched `os.name` to `"nt"`, and `pathlib.Path()` selects `WindowsPath` from `os.name` at call time, so every later `Path(...)` raised `NotImplementedError` on Linux instead of taking the branch under test. The bridge now exposes a `_windows_host()` indirection so the Windows branch is exercisable on any host without hijacking `Path` class selection.

### The blind spot behind three red rounds, and its closure

Three of the four causes across two red rounds shared one property: they were invisible to a green local suite because they depended on how the HOST resolves or provides something, not on the code under test. That is a gap in the gate itself, and it was closed in this release rather than deferred, because a verification release that ships a known hole in its own verification is self-defeating.

The exposure is larger than the bridge. Nexus-Hub registers hooks as `bash <script>` and the assistant HOST performs that launch. On a Windows host whose PATH `bash` is the WSL launcher stub, EVERY Nexus-Hub bash hook is silently inert, and Nexus-Hub cannot rewrite how the host invokes them. So the fix has two halves: repair what we control, and make what we do not control visible.

1. **End-to-end regression test.** `test_guard_survives_a_wsl_stub_first_on_path` places a stub `bash` (talks on stdout, exits non-zero, silent on stderr) first on PATH and asserts the guard still allows. Its failure mode was verified by disabling the resolver: it denies, exactly reproducing the CI symptom. A regression test that cannot fail proves nothing, so this was checked rather than assumed.

2. **Install-time and doctor detection.** `scripts/lib/integrations/_interpreters.py` probes whether each interpreter hook registrations depend on can actually execute a script, requiring an exact marker on stdout AND exit 0 (an exit-code-only check would accept a shim that swallows the script and returns 0). `runner.py verify` reports an unusable interpreter as a `NEEDS-ACTION` line naming Git Bash and the PATH remedy. It is fail-soft by construction: an unusable interpreter is a host condition the user fixes on PATH, and it must never fail an install that delivered every file correctly.

3. **Local-gate coverage.** A new `interpreters` group runs `scripts/check_interpreter_resolution.py --gate` in the `fast`, `full`, and `platform` profiles. The script is repo-internal and registered in `DEV_ONLY_SCRIPTS`; the user-facing equivalent is the doctor line above. It is a GROUP inside existing profiles rather than a new workflow job, so it introduces no new required status context and cannot reproduce the v3.17.5 pending-check trap.

Six focused tests cover the probe, including both ways a stub can fool a naive check, and the gate's advisory-versus-`--gate` exit contract.

Final local gate with the coverage in place:

```
profile: full   platform: windows
- catalog-parse / hygiene / interpreters / catalog / security / workflows
- platform-contracts / docs / version / tests / extension-tests
PASS: 43 passed, 0 failed, 0 skipped, 0 advisory in 2813.3s
PROFILE_EXIT=0
```

```
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory   (fast, now 13 groups)
```

`tests/integrations/test_copilot_hermes_native.py` plus `tests/validators/test_interpreter_resolution.py`: 71 passed, 2 skipped.

### Push 4 - interpreter coverage

Commit `a004efd5` was pushed after approval. **Every required check is green** (`gh pr checks 146` exit 0):

| Check | Result |
|---|---|
| `ci-required` (aggregate) | pass (2s) |
| `validate` | pass (38s) |
| `shellcheck` | pass (18s) |
| `verify` | pass (1m24s) |
| `colocation` | pass (5s) |
| `tests` | pass (11m44s) |
| `tests-windows` | pass (11m3s) |
| `install-smoke` (ubuntu / macos / windows) | pass |
| `installer-smoke` (ubuntu / macos / windows) | pass |
| `bootstrap` (ubuntu / macos) + `bootstrap-windows` | pass |
| CodeQL, `Analyze` (javascript-typescript / python) | pass |
| `changes`, `detect` | pass |
| `render` | skipping (browser-free pull-request path, by design) |

Four integration rounds were required. That is recorded rather than smoothed over, because the sequence is the evidence that the discipline works: the local gate certified a tree that the integration result then falsified three separate times, each time for a host-dependent reason a single developer machine could not reach. The blind spot itself is now closed and gated (MT-1), so the same class fails locally in future.

| Round | Commit | Outcome |
|---|---|---|
| 1 | `89bf4e40` | red: 3 causes (Linux-only `stat` constant, two stale CI assertions) plus one misdiagnosed |
| 2 | `2248cc6e` | 3 confirmed fixed; `tests-windows` still red, and the round-1 diagnosis proved wrong |
| 3 | `185e8937` | `tests-windows` green (WSL-stub resolver); `tests` red on a defect in that round's own test |
| 4 | `a004efd5` | **all green**, with the host-interpreter blind spot closed and gated |

### Merge and post-merge verification

PR #146 was merged into `develop` with an explicit merge commit (`c6afeed0`, merged 2026-08-31T05:11:50Z), preserving all four commits so the red-then-green integration sequence stays auditable from git alone rather than only from this file.

The post-merge workflow was then checked against the plan's requirement that it perform only its intended smoke, publication, or provenance work:

```
Post-merge | push | completed | success | 2026-08-31T05:11:52Z
  smoke      | success
  provenance | success
```

Two jobs, both green, and no re-run of the validation suite. No other workflow triggered on the merge.

This completes Phase 5. The `/update release` handoff follows, and it owns the version bump, changelog finalization, `develop` -> `main` merge, tag, push, and GitHub Release behind its own confirmation gates.

- Branching model: feature branch into `develop`, then release flow to `main`.
- Remote: `origin`.
- Existing branch: `feat/v4.2.2-guide-cinematic-rebuild`.
- Existing pull request: #146 targeting `develop`.
- Combined delivery: v4.2.2, v4.2.3, and v4.3.0.
- Expected required checks: `validate`, `shellcheck`, `ci-required`, `colocation`, and `verify`.
- Branch-name decision: retain for lower operational risk or rename only with explicit approval.
- First push: requires explicit approval after the final local commit.
- Merge: requires separate approval after every required check is terminal and green.
- Release: `/update release` owns version bump, changelog, tag, push, and GitHub Release after integration.

No branch push, pull-request mutation, repository-setting mutation, merge, tag, or release has occurred in Phase 5.
