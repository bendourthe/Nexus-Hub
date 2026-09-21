# Last-phase evidence -- v4.13.0

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Phase**: 7 of 7 (T025-T034)
**Revision under review**: `2fd343fb`
**Integration base**: `origin/develop` at `faf83ba8`
**Diff**: 41 files, 7186 insertions, 45 deletions, 7 commits

Every section below quotes the command or scan that produced it. A duty omitted without a recorded known gap is a fail, so an empty finding still quotes its scan.

## Scope rule applied throughout

The plan's own scope interpretation governs each duty: the scans may inspect broad repository state, but changes stay inside this plan's artifact set and its direct references. Unrelated dead code, restructuring, policy drift, and other versions' open gaps are **reported with their existing owner, not fixed opportunistically**. Every such item below names its owner.

## Architecture refactor

### Empty, redundant, and obsolete structure

```
$ find . -type d -empty -not -path "./.git/*" -not -path "*/__pycache__*"
(no output)
```

Two directories look empty but are not findings: `docs/handbooks/markdown/` and `docs/handbooks/html/` each hold a `.gitkeep`. `docs/handbooks/README.md` documents why, stating that "topic layouts and existing Markdown/HTML pairs remain supported without migration". They are a reserved alternate layout, not leftovers.

### Orphan check on this plan's artifacts

Every file this plan added under `docs/releases/v4/v4.13/` was checked for an inbound reference from `docs/`, `tests/`, `scripts/`, `catalog/`, `AGENTS.md`, or `CHANGELOG.md`:

| Artifact | Inbound references |
|---|---|
| `development/trigger-pilot-protocol.md` | 3 |
| `development/trigger-pilot-results.md` | 6 |
| `development/trigger-pilot-results.json` | 5 |
| `development/pilot-prompts.json` | 3 |
| `development/pilot-variant-b.json` | 5 |
| `development/phase-1-evidence.md` .. `phase-6-evidence.md` | 4 to 8 each |
| `known-gaps.md` | 498 |
| `plans/v4.13.0-...md` | 21 |

The six files under `development/history/` show zero inbound references. That is the repository's convention, not a defect: `docs/DEVLOG.md` links the `development/history/` **directory** per release, never the individual files, and every other version behaves identically (`v4.12`'s five history files also show zero).

v4.13 has no `docs/DEVLOG.md` row yet. That is correct at this point in the lifecycle: `catalog/commands/update.md` line 21 assigns the devlog index refresh to `/update release`, which has not run for this version.

### Docs layout

```
$ python scripts/check_doc_colocation.py
Enforcing co-location under every major: docs/releases/v3, docs/releases/v4
OK: no comparison / adoption-plan co-location mismatches
exit 0

$ python scripts/check_docs_retention.py
docs retention: 4 version(s) due for archival (current v4.12, threshold 2 minors). Advisory only
  WARN: docs/releases/v4/v4.7/development/history (8 file(s))  -> docs/archives/v4/v4.7/development/history/
  WARN: docs/releases/v4/v4.8/development/history (5 file(s))  -> docs/archives/v4/v4.8/development/history/
  WARN: docs/releases/v4/v4.9/development/history (9 file(s))  -> docs/archives/v4/v4.9/development/history/
  WARN: docs/releases/v4/v4.10/development/history (6 file(s)) -> docs/archives/v4/v4.10/development/history/
exit 0
```

**Reported, not fixed.** The retention backlog is advisory (exit 0) and covers v4.7 to v4.10, none of which is this plan's artifact set. Owner: `/update refactor` or `[[docs-layout-refactor]]`, per the message the checker itself prints. Archiving four unrelated versions during this plan's final phase would be exactly the opportunistic restructuring the scope rule forbids.

## Known-gaps reconciliation

Every `docs/**/known-gaps.md` was globbed (42 files) and each item's `**Status**` field read. Files whose status is `finalized` or `released` were not re-opened.

### This version

| ID | Disposition at Phase 7 |
|---|---|
| DF-1 Phase 6 pilot deferred as UNMEASURED | **Resolved** in Phase 6. Pilot ran 96/96 at USD 20.6709. |
| QG-1 Phase 6 acceptance criteria unexercised | **Resolved** in Phase 6. All four criteria evaluated per model. |
| WN-1 Pre-existing commit-attribution findings | **Resolved** in Phase 6. `check_commit_attribution.py --all-refs` -> 1740 commits, 0 findings. |
| WN-2 Tool-span attributes unverified at the pinned OTel revision | **Open.** Owner `ai-agent-development`. Untouched by Phase 7; the contract still marks those attributes unverified and invents no requirement level. |
| WN-3 The shipped catalog under-triggers | **Open.** Owner catalog maintainer. Recorded from measured evidence; acting on it needs its own pilot. |
| WN-4 Acceptance criterion 3 unreachable by construction | **Open.** Owner catalog maintainer. A defect in the frozen protocol's assumption. |

### Every other ledger still carrying an open item

Each is given an explicit touched-or-not verdict, following the precedent this repository set in `docs/releases/v4/v4.8/development/last-phase-evidence.md`.

| Ledger | Open item | Touched by this plan? |
|---|---|---|
| `v3/v3.15` | Hand-offs | No. |
| `v4/v4.11` | SEC-1, eight CodeQL alerts visible to `main`, five high | No. This plan adds no application code path; owner remains v4.11. |
| `v4/v4.12` | WN-1 existing CI-profile lint findings | No. |
| `v4/v4.12` | DF-1 Antigravity workflow surface retires 2026-11-01 | No. |

The v4.9 ledger's six items (`MT-1`, two `WN-1`s, `WN-2`, `MT-2`, `QG-1`) carry no `Status: open` marker but were named as carry-forward in this plan's own grounding section. Verdict for each: **not touched**. This plan changed no model-prompting profile, made no family-scoped vendor claim, ran no private verification harness, added no platform-specific filesystem test, and edited no CI matrix selection.

No ledger was marked resolved on this plan's behalf, and no open item was silently inherited.

## Living docs architecture

Self-gated: `docs/testing/` and `docs/validation/` do not exist and were **not** created. The check reports the tree as it is.

| Root | State |
|---|---|
| `docs/handbooks/` | present, 26 files |
| `docs/decisions/` | present, 44 files |
| `docs/policy/` | present, 17 files |
| `docs/guides/` | present, 1 file |
| `docs/README.md`, `docs/DEVLOG.md`, `docs/todos.md` | all present |
| `docs/reference/`, `docs/runbooks/`, `docs/standards/` | absent, and not invented |

### Markdown wins: handbook build receipts verified

`docs/handbooks/handbooks.json` maps each handbook to its editable Markdown under `_sources/`, its design files, and its builder code; `<output>.build.json` records the sha256 of each. Every hash was recomputed from disk and compared:

```
overview:     14 hashes compared, 0 stale, 0 unresolved; output matches receipt: True
distribution: 14 hashes compared, 0 stale, 0 unresolved; output matches receipt: True
```

No regeneration was needed, and the generated HTML is not ahead of or behind its Markdown source.

**A correction worth recording.** The first attempt at this check reported "0 stale" while comparing **nothing**: it looked for receipt keys named `inputs` / `input_hashes`, which do not exist in the receipt (the real keys are `sources` and `build`), so every lookup returned `None` and every comparison was skipped. It produced a clean-looking result with zero evidence behind it. The count of hashes actually compared is printed above for exactly that reason, because "0 stale" and "0 compared" are indistinguishable without it.

## Git-tree hygiene

```
$ python scripts/check_release_preconditions.py --branches --repo-settings
Branch hygiene (merged into origin/develop)
  4 merged branch(es) are cleanup candidates:
    - origin/chore/backmerge-v4.12.1
    - origin/fix/windows-distribution-and-test-robustness
    - origin/fix/windows-long-path-install-cleanup
    - origin/release/v4.12.1-publish
  (2 branch(es) with an open PR were excluded)
  2 branch(es) survive a CLOSED, unmerged PR:
    - origin/feat/guide-foundations-ml-integration
    - origin/fix/target-manifest-git-trust-skip
  delete_branch_on_merge does NOT cover these. Review and delete by hand.
  Reporting only -- nothing was deleted.
Repository settings
  OK: delete_branch_on_merge is enabled
  NOTE: the repository description disagrees with README.md:
    - skills: description says 336, README.md declares 337
exit 0
```

Report only; nothing was deleted, as the duty requires. Two items are named with owners rather than acted on:

- `origin/feat/guide-foundations-ml-integration` is the branch behind the maintainer's in-progress guide work. The maintainer stated it stays separate until they finish and migrate it. It must **not** be deleted here.
- The GitHub repository description drifted to 336 skills against README.md's 337. It is not a version-carrying surface, so `check_version_sync.py` cannot see it. Owner: repository maintainer, by hand, at release time.

## CI/CD coverage

### Detect

Active provider: **GitHub Actions**, 13 workflows under `.github/workflows/`. No `.gitlab-ci.yml`, `.circleci/`, `azure-pipelines.yml`, `Jenkinsfile`, or `.travis.yml` is present. This is a detection result, not an assumption.

### Compare, field by field

| Canonical field | Observed | Verdict |
|---|---|---|
| Repository-native profiles | `ci.yml` jobs call `scripts/ci/run.py`; the step list lives in `scripts/ci/profiles.py`, the same one a developer runs locally | PASS |
| Event separation | `ci.yml` is `pull_request` + `merge_group` + `workflow_dispatch` only; post-merge work in `post-merge.yml`; tag work in `release.yml` | PASS |
| Runner selection | ubuntu, windows (PowerShell 5.1 leg), and macOS legs all run on the pull request, before the merge | PASS |
| Always-resolving aggregate required check | `ci-required` with `if: always()`, ten `needs`, and an explicit refusal to pass vacuously when no job results are present | PASS |
| Permissions | `permissions: contents: read` at workflow level | PASS |
| Immutable action references | every `uses:` across all 13 workflows is pinned to a 40-character sha | PASS |
| Caching | pip cache on three jobs plus a Playwright browser cache keyed to the resolved version | PASS |
| Concurrency | `group: ${{ github.workflow }}-${{ github.ref }}`, `cancel-in-progress: true` | PASS |
| Path scoping | applied per job via the `changes` job, never as a workflow-level `paths:` filter on a required workflow | PASS |
| Artifact retention | `ci.yml` uploads no artifact, so retention does not apply to it. `supply-chain-watch.yml` sets `retention-days: 30`; `cursor-usage-monitor.yml` sets none and takes the 90-day default | PASS for this plan's scope; the missing retention on one unrelated monitor workflow is reported below |
| Structured reports | `ci-required` prints a per-job result table before failing, naming the real hyphenated job name | PASS |
| Deployment boundaries | release and publication live in `release.yml`, gated on tags, never in `ci.yml` | PASS |
| Failure recovery | `ci-required` fails closed on any non-success, non-skipped result, and fails when it received no results at all | PASS |

The required-check contract is machine-verified rather than asserted:

```
$ python scripts/check_required_check_coverage.py
Required-check coverage: OK -- 10 declared context(s) across 2 branch(es), every one produced unconditionally.
exit 0
```

Workflow-level `paths:` filters do exist on `claude-usage-monitor.yml`, `code-search.yml`, and `codeql.yml`. None of those produces a required context (the required set is `validate`, `shellcheck`, `ci-required`, `colocation`, `verify`), so the filters save minutes without any risk of a check sitting Pending forever. That distinction is the whole point of the rule and the checker above confirms it holds.

### Propose and approve

**No pipeline change is proposed.** Every required field has observable evidence and the comparison concludes PASS on its own terms. Nothing was applied, so no approval was required; silence was not treated as approval anywhere.

### Cross-installer parity

This repository ships two installers (`scripts/installer.sh` and `scripts/installer.ps1`), so the parity gate applies rather than being a silent no-op. It is declarative and already in the suite: `catalog/hooks/tests/test_installer_smoke.py` derives the user-facing script list from `scripts/*.py` minus an explicit `DEV_ONLY_SCRIPTS` allowlist and asserts every remaining basename appears in **both** installers; `catalog/hooks/tests/test_hook_sibling_parity.py` asserts every `.sh` hook has a `.ps1` sibling that parses and agrees on exit codes for the same payload.

This plan added one new `scripts/*.py`, which forced that gate:

`scripts/run_trigger_pilot.py` is a maintainer tool that **spends real money and makes network calls**. Copying it into `~/.nexus-hub/scripts/` to satisfy the parity rule would have put a spend-incurring runner on every user's machine. It was added to `DEV_ONLY_SCRIPTS` with that reason recorded inline, which is the allowlist's purpose.

Both suites were run against this revision:

```
$ python -m pytest tests/installer/ catalog/hooks/tests/test_hook_sibling_parity.py catalog/hooks/tests/test_installer_smoke.py -q --no-cov
825 passed, 43 skipped in 459.73s (0:07:39)
exit 0
```

The 43 skips are the platform-gated cases: an installer leg whose target operating system is not this host cannot be proven here, and CI runs the matching legs (`bootstrap-windows`, `tests-windows`, `install-smoke`) on their real runners. That limitation is stated rather than papered over.

### Discovery checked in the same pass

Cross-linked to `[[platform-contract-verification]]`, as the duty requires:

```
$ python scripts/verify_platform_contracts.py
[verify-contracts] OK: 14 platforms match the contract doc.        exit 0

$ python scripts/sync_platform_defaults.py --check
platform-defaults OK -- 14 platform(s), all derived artifacts in sync    exit 0

$ python scripts/check_platform_contract_freshness.py
[contract-freshness] OK: contract verified for v4.12.1 (last_verified 2026-09-16).   exit 0
```

The freshness marker reads `verified_for_version: 4.12.1`, which matches the current `.claude-plugin/plugin.json` version. It will need re-stamping to `4.13.0` at the version bump. That is **deliberately not done here**: the marker records that a live re-verification pass was performed for a version, and stamping it ahead of the bump without running that pass is precisely the dishonest act the skill's own rationalization table warns against. Owner: `/update release` governance step 4.

### Recorded rather than applied

| Difference | Owner | Next step |
|---|---|---|
| `cursor-usage-monitor.yml` uploads a VSIX artifact with no `retention-days`, taking the 90-day default | repository maintainer | Set an explicit retention on that workflow. Unrelated to this plan; not edited here. |

## Human and manual testing suggestions

Last-phase duty. These are the cases automated tests in this repository cannot reach. Nothing below was performed by the agent, and none of it is presented as done.

1. **Confirm the under-triggering finding in real use (WN-3).** The pilot measured selection on 24 synthetic prompts. Over a week of ordinary work, notice whether `plan-before-code`, `html-output-conventions`, `skill-description-authoring`, and `context-engineering` fire when you expected them to. The pilot predicts they mostly will not. A human sense of how often that actually costs something is the input a second pilot needs, and no test can supply it.
2. **Install on a real macOS machine.** CI proves the ubuntu and Windows installer legs; the macOS end-user path is covered only by the bash leg, not by a real install. Run the one-line bootstrap and confirm `~/.nexus-hub/skills/ai-agent-development/scripts/trace-example.py` and `.../references/agent-span-contract.md` arrive, and that `scripts/run_trigger_pilot.py` does **not** (it is dev-only by design).
3. **Confirm discovery inside the actual applications.** `verify_platform_contracts.py` proves the installer writes to the declared paths. It cannot prove Cursor, Antigravity, or Codex then *shows* the content. Open each and check that the skills appear in the picker.
4. **Exercise `trace-example.py` on a case-insensitive or network filesystem.** Its `resolve_output()` refuses existing paths and symlinked parents. Symlink and case semantics differ on macOS and on SMB shares, and the repository has no runner for either.
5. **Read `references/evaluator-validation.md` Step 6 while validating a real judge.** The step asks you to prove a judge notices a controlled loss. Whether the written procedure is followable by someone who did not write it is a question only a first-time reader can answer.

## Tier 3 deep pass

Run per `[[functional-verification]]`'s `references/deep-pass.md`. Its procedure was followed rather than improvised.

### 1. Inputs

| Hard input | State |
|---|---|
| Approved plan with Goal, phases, tasks, exclusions | present |
| Maintainer request | present in the conversation record and the plan header |
| Final diff against the integration base | `git diff origin/develop...HEAD`, 41 files at the time of the blast-radius verdict |
| Exact revision under review | `2fd343fb`, base `faf83ba8` |

No `NOT COVERED: required deep-pass input unavailable` record was needed.

### 2. Blast-radius verdict

- **Verdict**: run
- **Positive triggers**: distributed catalog content changed (nine `catalog/skills/**` files including a bundled executable script and two new references); a public contract statement changed (`agent-span-contract.md`); a new `scripts/*.py` entered the repository, which the installer parity rule governs.
- **Ambiguity check**: none needed; the first trigger is unambiguous.

### 3-4. Feature inventory and exercise

| Feature | Source | Artifact | Real boundary | Observed result |
|---|---|---|---|---|
| Judge sensitivity harness | Phase 1 | `judge-sensitivity.json` + 3 scorers | pytest | reference separates every degraded pair; constant and style-reactive controls fail as required |
| Private trace emitter | Phase 2 | `trace-example.py` | executed the script | 5 metadata-only records, one root, no orphan spans; grep for either sentinel returns 0 |
| Trace refusal paths | Phase 2 | same | executed with hostile paths | existing path, missing parent, NUL byte and symlinked target all refused with exit 2 |
| Span contract | Phase 2 | `agent-span-contract.md` | document check | pinned revision present; `gen_ai.tool.*` still marked unverified rather than invented (WN-2) |
| Reversible improvement loop | Phase 3 | `improvement-lifecycle.json` + oracle | pytest | rejection restores prior bytes exactly; the oracle never reads the declared expectation |
| Representation ladder | Phase 4 | `representation-cases.json` + ladder | pytest | **gap found and closed**, see below |
| Context freshness | Phase 5 | `context-freshness.json` + `derive_freshness` | pytest | all six dispositions derived, stable across a later clock |
| Trigger pilot | Phase 6 | runner + 96 recorded rows | in-process inspection only, no paid call | **five defects found and fixed**, see below |

Direct exercise of the distributed script:

```
$ python catalog/.../scripts/trace-example.py --output <tmp>/trace.jsonl
wrote 5 synthetic records to <tmp>/trace.jsonl
payloads, tool arguments, results, instructions and raw exceptions omitted
exit 0

$ grep -cE "sk-live-SENTINEL|SENTINEL-private-key" <tmp>/trace.jsonl
0
```

### 5. Rendered-surface delegates

**NOT APPLICABLE**, with the artifact reason: the plan produced no HTML, CSS, SVG or generated document. `git diff --name-only origin/develop...HEAD` matches no `.html`, `.css`, `.svg` or image path. The visual-explanation phase changed decision guidance and a JSON fixture only, so `[[browser-testing-with-devtools]]`, `[[accessibility-engineering]]`, `detect_visual_defects.py` and `[[hallmark-design]]` have no surface to act on. Recorded as not applicable with its reason, never as an unavailable check marked not applicable.

### 6. Adversarial pass

`[[adversarial-verifier]]` was invoked against the full inventory, scoped away from any paid model call. It returned one explicit no-finding and fifteen findings by reproduction. The consequential ones, all now fixed with regression tests (BG-1 to BG-6):

| Finding | Why it mattered |
|---|---|
| A Windows junction defeated the trace script's output guard, and a redirected grandparent bypassed it entirely | The script is DISTRIBUTED to end users. Reproduced with `mklink /J`. |
| The pilot scored a selection by substring over the whole serialized tool call | A different skill's invocation that merely mentioned the target would count, inflating the exact number the pilot measures. |
| A budget-truncated run was recorded as a measured non-selection | The run never got the chance to invoke the skill; that is evidence-missing, the distinction the module was built around. |
| `--ceiling` was unclamped and a non-finite value disabled the spend check | Every comparison against `nan` is False, so the branch was dead. Reproduced at USD 1,000,000 spent. |
| A timed-out call was charged zero | A ledger that under-counts spend permits more of it. |
| `stage_variant` could substitute nothing and produce two identical arms | The exact failure caught by hand before the scored run, unguarded for the next one. |
| Seven `*_has_teeth` controls asserted a `str.replace` tautology | Independently found by the Goal reviewer as well. Detailed below. |

The explicit no-finding is worth recording: no input could make either sentinel reach the emitted trace. `--output` is the only input surface, it never enters a record, and `assert_no_payload` runs before the file is opened.

### 7-8. Convergence and Goal-vs-plan sufficiency

| Question | Answer | Evidence | Change made | Owner |
|---|---|---|---|---|
| What did implementing this teach that the plan did not know? | The catalog's problem is under-triggering, and the remedy `AGENTS.md` prescribes for it makes selection worse. The plan anticipated a candidate winning or losing; it did not anticipate the control arm being the finding. | `trigger-pilot-results.md` | Recorded as WN-3, not acted on | catalog maintainer |
| What did the plan assume that turned out false? | Two things. The entry gate assumed no qualified execution path existed, on an inspection that never examined the CLI's structured output. And acceptance criterion 3 assumed a baseline of over-triggering, which made it unsatisfiable by any candidate. | `phase-1-evidence.md`; the criteria table | DF-1 and QG-1 resolved; WN-4 opened | catalog maintainer |
| What would a reader of the Goal expect that no phase delivered? | The Goal says a bounded improvement is "supported by ... reversible regression evidence". Every lifecycle artifact is synthetic and the one real candidate was rejected, so no actual improvement has traversed the loop end to end. | `improvement-lifecycle.json` is a fixture | None. The plan states this ceiling explicitly and the recipe's contract is proven satisfiable. Recorded so the Goal sentence is not read as more than it is. | plan author |
| What did the maintainer ask for that no task line captured? | A decision record for building an adapter, which the plan itself demanded and no task line created. | plan line 115 | **Fixed**: the decision record plus the missing `CHANGELOG.md` entry | this phase |

### 9. Fix cycles

`fix_rerun_cycles_used`: **1** of 3.

Corrections applied, each after reproducing the defect:

1. Seven tautological document controls replaced with `assert_has_teeth`, which asserts the needle IS present before asserting the mutation removes it. The old form was verified to pass for a needle that was never in the file.
2. The promotion control now calls the predicate under test against both real and planted text.
3. `trace-example.py`: reparse-point-aware disclosure, `O_EXCL` write, NUL rejection, and a clean refusal where an exclusive create through a junction fails on Windows.
4. Runner: field-specific selection matching, evidence-missing on an errored result, clamped and finite-checked ceiling, worst-case charging for a timed-out call, hard failure on a no-op variant substitution, and a marker-guarded `rmtree`.
5. `representation-cases.json` gained machine-readable signals and `derive_rung`, the oracle it never had.
6. The constant-scorer control now asserts the verdict pair rather than a property of the constant scorer.

Three of those corrected a false claim in an evidence file, not only code. Those are corrected in place in `phase-6-evidence.md` with the correction stated, rather than silently rewritten.

### The representation gap, found twice independently

`representation-cases.json` declared an `expected_rung` per case that **no code derived**. Phases 3 and 5 each ship an oracle that can contradict their fixture's declared expectation; Phase 4 shipped the fixture without one, so every test was fixture-internal self-consistency and the declared expectation could not disagree with anything. Rotating the `request`, `shape` and `rationale` fields across all seven cases left zero tests failing.

`derive_rung` now transcribes the ladder from `html-output-conventions/SKILL.md` and never reads `expected_rung`. Its teeth were verified by mutation: flipping REP-4 to `table`, REP-1 to `html` or REP-7 to `prose` is caught, and so is stripping REP-4's interaction and state signals.

Writing it immediately found a disagreement. The oracle put REP-5, a two-item comparison across two attributes, on `prose`, because the transcription used a row-count threshold. The ladder's actual rung-1 rule is "one or two facts with no structure to show", and a two-by-two comparison has structure. **The fixture corrected the oracle**, which is the direction that proves the two are independent.

### 10. Residual and disposition

| Item | Disposition |
|---|---|
| WN-5, recorded run not re-auditable for the old selection matcher | Open, bounded. All five `Skill` invocations across 96 calls are exactly the five scored rows; the defect can only inflate a positive, so every count is an upper bound and the `MEASURED_NO_CHANGE` disposition does not turn on it. |
| WN-6, symlink tests skip on this Windows host | Open. They run on the CI Linux and macOS legs. |
| WN-2, WN-3, WN-4 | Open, carried with named owners. |

Gate disposition: **PASS with recorded gaps**. Nothing the deep pass found is both unresolved and unrecorded.

## Full-suite testing and stabilization

**Assertions: green. Profile wrapper: times out on this host.** Both statements are true and the section says so rather than picking the convenient one.

### What the suites actually report

Run individually, to completion:

```
$ python -m pytest catalog/hooks/tests -q
1319 passed, 35 skipped in 1961.49s (0:32:41)

$ python -m pytest tests -q --tb=line
5805 passed, 101 skipped, 2 warnings in 5970.28s (1:39:30)
```

**7124 passed, 136 skipped, 0 failed.** No assertion fails anywhere in the repository at this revision. Combined with the earlier targeted runs (`tests/skills` + `tests/validators` 3772 passed; installer and parity suites 825 passed; `test_evidence_driven_improvement.py` 180 passed, 2 skipped), the refactor changed no behavior.

The other groups of the `full` profile pass:

```
$ python scripts/ci/run.py --profile full --only catalog-parse,hygiene,interpreters,catalog,security,workflows,platform-contracts,docs,version
PASS: 38 passed, 0 failed, 0 skipped, 0 advisory in 19.5s

(extension-tests, from the earlier whole-profile run)
[ok  ] skill-server, code-search, web-fetch, skill-scanner,
       context-compressor, memory, compression-accuracy-gate   -- 7/7
```

### Why the profile nonetheless reports FAIL

`python scripts/ci/run.py --profile full --only tests` reports `FAIL: 0 passed, 2 failed` in **6300.2s**. That number is the diagnosis:

| Step | Cap | Measured | Over by |
|---|---|---|---|
| `hook-tests` | 1800s | 1961.5s | 161.5s |
| `repo-tests` | 4500s | 5970.3s | 1470.3s |
| **Sum of caps** | **6300.0s** | profile reported **6300.2s** | |

Both steps ran to their cap and were killed. Neither failed an assertion. The totals match to two tenths of a second, which is not a coincidence a slower explanation could produce.

This is a **host-speed** result, not a repository defect. `scripts/ci/profiles.py` records a measured Windows baseline of 3341.7s for `repo-tests`; this host took 5970.3s for the same suite, 79 percent above that baseline, while several other workloads were resident. CI runs these legs on dedicated runners with their own budgets.

### The timeout is invisible, which is its own finding

A timed-out step prints **nothing at all**. In `scripts/ci/run.py`, the `subprocess.TimeoutExpired` handler returns at line 100, before the `[ok ] / [FAIL]` rendering block at line 122, so the step contributes to the failed count while naming neither itself nor its reason:

```
profile: full   platform: windows
- tests

FAIL: 0 passed, 2 failed, 0 skipped, 0 advisory in 6300.2s
```

That is the whole output. The runner already carries the information needed to say so, `status="timeout"` and `reason=f"exceeded {cmd.timeout}s"`, and simply never prints it.

This cost real time in this phase. Diagnosing two unnamed failures took two full profile runs plus two standalone suite runs, roughly four hours, to reach a conclusion the runner could have printed in one line. Recorded as `QG-2`; a fix is proposed, not applied, because `scripts/ci/run.py` is pipeline infrastructure and this phase's own rule is that a pipeline change needs explicit approval per change.

### Disposition

| Question | Answer |
|---|---|
| Does any test fail at this revision? | No. 7124 passed, 136 skipped, 0 failed. |
| Did the refactor change behavior? | No. |
| Is the `full` profile green end to end on this host? | No, and it cannot be: two steps exceed their caps here. |
| Is that caused by this plan? | No. This plan added roughly 180 tests to one module that runs in about one second, against a 2600-second overshoot. Pre-existing on this host. |
| Recorded as | `QG-2` (silent timeout rendering) and `QG-3` (profile budget versus this host), both with owners and next steps. |

The local gate is therefore reported as **green on assertions with two recorded quality-gate gaps**, never as an unqualified pass.

## Goal-vs-codebase review

Performed by a reviewer that implemented none of the phases, as the plan requires. It read the Goal and the tree first, and the phase evidence only afterwards.

**Goal**: "Extend existing evaluation, learning, observability, visual-output, context, and skill-authoring owners so a bounded improvement is supported by sensitive-criterion checks, private observable traces, reversible regression evidence, appropriate representations, current facts, and a measured trigger pilot, without a new service, training stack, or automatic instruction mutation."

| Goal element | Verdict | Artifact |
|---|---|---|
| Sensitive-criterion checks | **LANDED** | `judge-sensitivity.json` plus three scorers; both negative controls fail in the required direction |
| Private observable traces | **LANDED** | `trace-example.py` executed; metadata-only records, sentinels absent, refusals exercised as subprocesses |
| Reversible regression evidence | **LANDED** | `improvement-lifecycle.json`; rejection restores prior bytes byte-exactly and the oracle never reads the declared expectation |
| Appropriate representations | **PARTIAL at review, LANDED after the fix** | was fixture-only; `derive_rung` added in this phase |
| Current facts | **LANDED** | `derive_freshness` with an injected clock across six scenarios |
| A measured trigger pilot | **LANDED** | 96 real calls, USD 20.6709, an honest `MEASURED_NO_CHANGE` the catalog respects |

| Exclusion | Verdict | Evidence |
|---|---|---|
| No new service | **HOLDS** | no network, socket, framework, daemon, scheduler or collector in the additive diff; `test_uses_no_network_or_environment_capture` bans the imports |
| No training stack | **HOLDS** | no training or fine-tuning anywhere; `verified-improvement-loop.md` states the artifact is a text change rather than a weight update, and that line is asserted |
| No automatic instruction mutation | **HOLDS** | the only code that writes a `SKILL.md` writes into the disposable fixture, never `catalog/`. Confirmed by outcome: nothing was promoted and `skill-description-authoring` is untouched. The reviewer flagged the unguarded `rmtree` on that fixture path as a latent risk; now fixed as BG-6. |

**Scope creep**: none in the catalog. Every touched skill is named in the plan's ownership table, and `data/skills.json`, `SKILL_INDEX.md` and `marketplace.json` are correctly untouched because no skill was added. The one genuine scope finding was the runner itself, which the plan placed outside its own boundary. That is resolved by the decision record rather than by argument.

The reviewer returned REQUEST_CHANGES on four items. Three are fixed in this phase: the tautological controls, the missing representation oracle, and the missing decision record and CHANGELOG entry. The fourth was that Phase 7 had not yet run, which this document is.
