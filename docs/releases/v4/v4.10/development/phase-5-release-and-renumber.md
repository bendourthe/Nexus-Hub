# Phase 5 evidence - Release review and assisted renumber

Evidence for Phase 5 (T013-T016) of the [v4.10.0 plan-queue continuity plan](../plans/v4.10.0-plan-queue-continuity.md). Records the release-time queue review, the completed renumber procedure, the residual-reference check and its proving tests, and the replay of all three 2026-09-10 renumbers against the real tree. Read this to confirm D5 and the renumber half of D6 before Phase 6.

## T013 - Release-time queue review

Added to `catalog/commands/update.md` as governance step **5a**, between the installer-parity hard gate and the model-prompting staleness check.

It evaluates the state a release establishes against every still-open queued plan and reports which the release changed, naming the affected task lines. It **reports; it does not edit a queued plan** - the finding is recorded so that plan's own next `/implement` re-assessment inherits it. An unaffected queue produces an explicit statement rather than an omitted section. It self-gates to a no-op in a repository with no plans tree, and it names `[[plan-queue-assessment]]` as owner rather than restating the rules.

A second paragraph states that a re-ordering recommendation may surface but that acting on one is a separate, explicitly confirmed operation: **a release must never silently renumber a queued plan**, because that rewrites version identity that merged pull requests and published documentation already reference.

### Numbering: two corrections during implementation

The step was first inserted as **6**, renumbering the model-prompting check to 7. Two problems surfaced immediately:

1. `tests/skills/test_release_staleness_step.py::test_update_md_stays_a_thin_dispatcher` failed. It scans the window from "Model-prompting-profile staleness check" to "This mirrors the" and allows at most two numbered steps as a proxy for "did someone paste the runbook in here". The insertion made three.
2. The file already contains multiple later steps numbered 7, and `AGENTS.md` cites "governance step 6" by number. Renumbering an established, externally-referenced step is exactly the kind of gratuitous churn a queue-continuity plan should not cause.

Resolved by using the file's existing lettered-insert convention (`2a`, `2b`) and placing it as **5a**, outside the test's scan window, with nothing renumbered. All 41 tests in the two affected modules pass.

## T014 - The renumber procedure

Completed in `catalog/skills/workflow/plan-queue-assessment/SKILL.md`. Five steps: propose and wait for explicit confirmation; move the tree via `[[docs-layout-refactor]]`; rename the plan and comparison files; repair all seven reference classes via `[[project-refactor]]`; prove the repair.

Step 5 now names the concrete command:

```bash
python scripts/enumerate_plan_queue.py --root . --check-residual v<OLD_VERSION>
```

The two traps are stated with their consequences, and the mid-implementation case carries the extra step it requires: re-applying committed work at the new paths, because cherry-picking across the rename conflicts.

## T015 - The residual-reference check and its tests

`--check-residual OLD_VERSION` was added to the existing enumeration script rather than as a second script, per the plan's construction ceiling ("a helper is allowed only as a small internal extraction inside the enumeration script"). Exit 0 when nothing survives; exit 1 listing every survivor with file, line, and text.

Two behaviours are load-bearing and both are pinned by tests:

- **Only `v`-prefixed forms match.** A heading such as `#### 4.10 - Publication and integration` is a Phase 4 subsection number, not a version. A `4.10` substitution corrupts it. Verified: `v4.10` matches `docs/releases/v4/v4.10/plans/x.md` and `v4.10.0 adoption plan`, and does not match `#### 4.10 - Publication` or `v4.100`.
- **A dated renumber note earns an exemption.** A line recording what was confirmed on a date keeps its original claim plus a note. A line making the same stale claim *without* a note still fails, so the exemption is earned by the note rather than by age.

`tests/validators/test_plan_renumber_references.py`, 12 tests: a clean renumber; a single survivor failing (the check is not a threshold); a surviving relative link; a surviving link-reference definition, which a link-text-only scan misses entirely; a surviving tracker row; the bare-section-number trap; the historical-note exemption and its negative case; a longer version not producing a false positive; the minor-checks-patch prefix behaviour; skip prefixes; and dot-directories being ignored.

## T016 - Replay of all three renumbers

Replayed against the real tree as a read-only check. **No tracked file was moved by this task.**

| Renumber | Old plan path | Residual references in tracked files |
|---|---|---:|
| Cache-and-diagram out of v4.12 | `v4.12/plans/v4.12.0-adoption-cache-and-diagram-quality.md` | 0 |
| Evidence plan out of v4.11 | `v4.11/plans/v4.11.0-adoption-evidence-driven-agent-improvement.md` | 0 |
| Queue plan out of v4.11 | `v4.11/plans/v4.11.0-plan-queue-continuity.md` | 0 |
| Cache-and-diagram out of v4.10 | `v4.10/plans/v4.10.0-adoption-cache-and-diagram-quality.md` | 0 |
| Attribution out of v4.10 | `v4.10/plans/v4.10.0-sole-contributor-attribution.md` | **1** |

### The one survivor, and why it is correct

`docs/releases/v4/v4.9/development/qualification/v4.9-layout-public.json` still names the pre-swap attribution path. It is a **frozen v4.9 evidence artifact**: a point-in-time inventory recording what the tree contained when that qualification ran. Repairing it would falsify the record it exists to preserve.

This is the historical-claim rule applied to a machine-readable artifact rather than prose, and it produced a real finding about the checker's scope:

**Finding: `--check-residual` scans `*.md` only.** It would not have caught this JSON either way. That is defensible for the current purpose (every reference class in the T001 acceptance surface is Markdown) but it means the check is not a complete guarantee across the repository. Recorded as a limitation rather than fixed, because widening it to all file types would sweep in generated inventories, lockfiles, and evidence snapshots whose whole purpose is to record a past state.

### Procedure proposal versus what was done by hand

| Step | Procedure says | What actually happened | Difference |
|---|---|---|---|
| Propose and confirm | Present the order, wait | The maintainer directed each swap explicitly | None |
| Move the tree | Delegate to `[[docs-layout-refactor]]` | `git mv` through a temp name | **Difference**: the move was done directly. The temp-name step is not in the procedure and should be, because a direct A-to-B swap collides. |
| Rename files | Rename plan and comparison | Done | None |
| Repair references | Seven classes | All seven hit at least once | None |
| Prove the repair | Residual check, fails on one | Done by ad-hoc grep at the time | **Difference**: no reusable check existed. That is what T015 adds. |

**Two differences found, both about the procedure rather than the history.**

1. **The temp-name step is missing.** Swapping two trees cannot go A to B directly; it needs A to temp, B to A, temp to B. Every one of the three renumbers used it and the written procedure does not mention it.
2. **The mid-implementation case understates the cost.** The procedure says committed work must be re-applied at the new paths. In practice that also required reconstructing the branch from `develop` rather than cherry-picking, collapsing three per-phase commits into one, and stating in the commit message where the per-phase record survives. The procedure mentions the first and not the rest.

Both are recorded here and carried into Phase 6 as procedure corrections rather than fixed silently mid-phase, because T016 is a verification task and rewriting the artifact under test inside it would remove the finding.

## Defect from Phase 2, caught here

Running the **full** `tests/validators/` suite (1520 tests, 3m24s) surfaced three failures that the fast profile and the bundle audit both passed:

```text
FAILED test_registry_consistency.py::test_statistics_total_matches_the_entry_count
FAILED test_registry_consistency.py::test_statistics_per_category_counts_match_the_entries
FAILED test_registry_consistency.py::test_marketplace_per_category_counts_match_skills_json
```

Phase 2's T006 registered the new skill in the three files AGENTS.md names, but `data/skills.json` carries a **fourth** count surface inside it: a `statistics` block with `total_skills` and a per-category map. It still read 336 and `workflow: 47`, so the catalog disagreed with itself and with `marketplace.json`.

Fixed here by deriving both from the entry list rather than incrementing by hand, which is what should have been done in T006.

**Why it was missed**: `make validate` / the fast profile does not run `tests/validators/`, and the bundle audit only checks per-skill structure. Nothing in the Phase 2 gate reached this assertion. This is the same class as the v4.0 known-gaps entry about prose counts drifting in a file no gate asserted.

**Consequence recorded for Phase 6**: the registration instructions in AGENTS.md name three files, and there are four count surfaces. That mismatch is a documentation gap independent of this plan, and Phase 6's known-gaps reconciliation should record it rather than this plan silently widening AGENTS.md.

## Checks run

```text
$ python -m pytest tests/validators/test_plan_renumber_references.py -q
............
12 passed in 0.42s

$ python -m pytest tests/skills/test_release_staleness_step.py tests/validators/test_check_release_capability_docs.py -q
41 passed in 2.81s

$ python -m pytest tests/validators/test_enumerate_plan_queue.py -q
21 passed
```

## CI impact

One new test path, `tests/validators/test_plan_renumber_references.py`, already collected by the existing `TESTS` group. No new script (the check extends the existing one), dependency, environment variable, or artifact. Nothing carried to Phase 6 beyond the two procedure corrections above.
