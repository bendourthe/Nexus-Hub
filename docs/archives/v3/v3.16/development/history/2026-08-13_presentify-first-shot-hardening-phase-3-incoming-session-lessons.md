# Session History - v3.16.7 Phase 3: Incoming session lessons

**Date**: 2026-08-13
**Plan**: [plans/v3.16.7-presentify-first-shot-hardening.md](../../plans/v3.16.7-presentify-first-shot-hardening.md)
**Phase**: 3 of 4 (Phase 4, the terminal refactor and release-readiness phase, remains)
**Branch**: `feat/v3.16.7-presentify-first-shot-hardening`
**Status**: COMPLETE

## What this phase was for

Phase 3 existed as an OPEN INTAKE. The maintainer was running `/presentify` on another project and expected further first-shot lessons, so the plan deliberately held the release open rather than shipping half a batch. The intake closed on 2026-08-13 when the VectorCAST decision-brief session delivered 26 numbered backlog items (`PRES-01` through `PRES-26`) plus five proposed QA gates.

## The lesson behind the batch

The session's page was offline, responsive, browser-verified, and structurally clean, and it was the wrong artifact on first delivery. It carried a section critiquing a draft the audience had never seen; it estimated a reusable commercial platform when the request was a bounded agent-led pilot; it opened its regulatory section by arguing that uploading documents is insufficient, rebutting a position the user had never taken; and its lead visual was an orbit diagram that rendered, sized, contrasted, and painted correctly while explaining nothing.

Every one of those passed every gate, because the gates ask whether the page WORKS. That is a different failure class from Phase 1's, whose five defects were invisible to the checks; these were invisible to the CATEGORY of check.

## Coverage assessment before building

Assessed by reading `SKILL.md`, all eight references, and `catalog/commands/presentify.md`. The seam was sharp: rendering discipline is mature (11 rubric criteria, four viewports, computed probes, a degradation contract) and content-intent discipline did not exist.

- `PRES-15` (deterministic browser helpers) was already DONE, shipped by the v3.16.5 errata after the same mid-animation false-defect.
- Six items were PARTIAL: sticky-layer collision, text-role measure, section height, the probe set, the QA layering, and credits.
- The remaining sixteen were entirely absent.

Roughly two thirds of the backlog was genuinely new, which is why this was a substantial phase rather than a polish pass.

## What was built

| Sub-task | Artifact |
|---|---|
| 3.1 | `references/content-intent.md` part 1 (the content brief), the Step 5 round-2 intake extension, the `content_intent` design-record block, Gate A |
| 3.2 | `references/content-intent.md` part 2 (seven decision-brief authoring rules, four BINARY), the Step 6 rule |
| 3.3 | `references/content-intent.md` part 3 (visual contracts, the subtractive test, scrollytelling state tables), Gate B |
| 3.4 | `references/responsive-typography.md` rules 8-11, the Step 6 BINARY halves |
| 3.5 | The Step 9 composition probes, per-section evidence, the sticky-layer inventory, the extended criterion 6 |
| 3.6 | The four named QA layers, Gate E, the runtime helper manifest in `catalog/commands/presentify.md` |

Plus 12 new Common Rationalizations rows, 12 new Verification items, the pipeline-diagram gate markers, and 24 new prose/behavior tests.

## Decisions worth recording

**Criterion 6 was extended rather than a criterion 12 minted.** The composition defects (wrapping, utilization, section height) belong to the defect family criterion 6 already owns ("wrapping serves the viewport"). A twelfth criterion would have cost a schema enum value, a count-contract test bump, and a rubric section for a family already covered. The `AGENTS.md` scope-fit gate declines structure a smaller change satisfies.

**The bulk went to a new Tier-3 reference, not into `SKILL.md`.** About 20 new authoring rules would have pushed the body well past its 500-line target and made every session pay for doctrine most runs never use. `SKILL.md` carries the BINARY one-liners and a pointer; it ended at 354 lines. This is the three-tier loading model behaving as designed.

**Gate E was kept OPTIONAL and non-blocking.** Decision readiness is a judgment about persuasion and comprehension. Putting it on the blocking path would make the release gate unfalsifiable, so the checkable half is enforced by Gates A and B and Gate E stays a reader-level confidence check.

**The source document's metrics section was DROPPED, with the reason recorded.** First-review acceptance rate, intent defect rate, visual replacement rate, and estimate correction rate all need a measurement pipeline across many sessions that this repository does not have. Shipping the definitions without the pipeline would have documented an intention rather than built a capability.

**Deviation from the plan text**: the plan specified "rules 8, 9, and 10" for `references/responsive-typography.md`. Four rules shipped (8 through 11), because section height and the coordinated density pass are separate rules with separate observable criteria and collapsing them would have buried the density-pass variable list inside a rule about heights. The file's stale "Six rules" header (already wrong at seven) was corrected to eleven as a necessary consequence.

## Results

- **Tests**: 685 passed, 0 failed in `tests/skills/` (34 in the v3.16.7 module, up from 12). Two failures during development were TEST-class (assertion strings not matching the shipped prose) and were fixed in the tests, not the implementation.
- **Validators**: `validate_skills.py --bundles-only` PASS (0 errors, 0 warnings, 271 skills, orphan-bundle audit clean for the new reference); `validate_unicode_safety.py` 0 errors with no finding in any changed file; `run_trigger_evals.py --gate` PASS; `check_version_sync.py` all surfaces match 3.16.6; `skills.json` integrity OK.
- **Lint**: `ruff check` reports 2 findings in the test module, verified PRE-EXISTING by stashing the phase's changes and re-running against the Phase 1 baseline. Left in place per the scope rule and logged as `WN-2`.
- **CI/CD**: no change needed. All three touched surfaces already match the `presentify-extractor.yml` path filters, and the workflow already carries path filters, concurrency cancel-in-progress, pip caching, and a gated render job.
- **`make`**: unavailable on this host, so the validators `make validate` wraps were run directly.

## Known gaps opened

- `NI-2` - Gates A, B, and E are agent behavior with no deterministic checker, by the same reasoning the maintainer applied to rubric criterion 10.
- `NI-3` - the composition probes are specified inline rather than bundled in a helper, consistent with the existing probes; extract the whole set at once if they are ever found skipped.
- `WN-2` - the two pre-existing ruff findings, routed to Phase 4 where a cleanliness pass is in scope.
- `NI-1` CLOSED - the intake received its lessons and they are built.

## Next steps

Phase 4 (terminal): the `[[project-refactor]]` and `[[docs-layout-refactor]]` audit, known-gaps reconciliation including the carried `WN-1` manifest-generator decision and the `WN-2` ruff fix, CI/CD verification, and the handoff to `/update release`. Do not tag or push from the plan.
