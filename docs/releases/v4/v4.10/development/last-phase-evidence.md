# Last-phase evidence - v4.10.0 plan-queue continuity

Fail-closed evidence for Phase 6 (T017-T026) of the [v4.10.0 plan-queue continuity plan](../plans/v4.10.0-plan-queue-continuity.md). One section per duty, each quoting its proving command or scan. A missing section, or an unresolved Goal-review or deep-pass finding without a recorded known gap, blocks the `/update release` handoff.

## Architecture refactor

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

## Known-gaps reconciliation

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

## Living docs architecture

Checked the living surfaces against this plan's changes.

- `README.md` - three live catalog counts updated 336 to 337; two counts inside `## What's New in v4.9.0` deliberately left at 336, because they describe what shipped in that release and updating them would falsify a historical claim.
- `AGENTS.md` - two catalog counts updated. Its registration instructions are **not** updated; that gap is recorded as DF-1 rather than fixed silently, because widening it is outside this plan's scope.
- `docs/todos.md` - dashboard rows and the queued-work entry track 16/26 through Phase 5.
- `docs/decisions/` - a decision record for the queue-ordering policy is required by this duty and is written as part of it (see below).
- No `docs/testing/` or `docs/validation/` tree was invented.

## Git-tree hygiene

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

## CI/CD coverage

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

## Tier 3 deep pass

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

## Goal-vs-codebase review

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

## Human/manual testing suggestions

This plan's central axis cannot be verified automatically, because it encodes a judgement.

1. **Does the ranking match your priority intuition?** Read the ranking in the Phase 2 evidence. The rule put v4.10.0 first, v4.11.0 second, v4.13.0 third, v4.12.0 fourth, v4.9.1 last. A wrong answer looks like: a plan you consider urgent sitting at position 4 or 5 with a reason you do not accept. If that happens, the class rule or the impact axis needs revising, not the individual placement.
2. **Would you approve the renumber proposal as written?** Read the renumber procedure in the skill. A wrong answer looks like: a step you would not run unattended, or a missing step you know from experience is needed. Two such gaps were already found by replaying real renumbers; a third would suggest the replay method is too narrow.
3. **Is `--check-residual`'s historical-note exemption too generous?** It exempts any line matching `renumbered|renamed|was swapped|at authoring time|formerly`. A wrong answer looks like: a genuinely stale reference passing because the line happens to contain one of those words. Try it against a line you know is stale.
4. **Run `/compare` or `/plan` once and read the new section.** The wiring was verified by reading and by a one-owner grep, not by an end-to-end command run. The first real invocation is the honest test.

## Full-suite testing and stabilization

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

## Publication and integration

Pending explicit approval.
