# Known Gaps - v4.0

**Project**: Nexus-Hub
**Status**: finalized
**Last updated**: 2026-08-25

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
| Deferred (DF) | 0 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 0 | 0 |
| Missing tests / coverage gaps (MT) | 1 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Missing Tests / Coverage Gaps

##### MT-1 - Lifecycle assertions are expected-red until their owning phase lands

- **Source phase**: Phase 1 - Canonical lifecycle contract and baseline audit
- **Plan reference**: `docs/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md` (T004)
- **Reason**: `tests/skills/test_cicd_lifecycle_contract.py` encodes the contract's seven non-negotiable statements in full, but the surfaces that satisfy statements 4 and 6 do not exist until Phases 2 and 5. The plan asked for failing-first tests and explicitly forbade weakening them. Leaving them plainly red would make every intermediate phase commit ship a red suite, which trains the reader to ignore red.
- **Mitigation in place**: each not-yet-true assertion carries `pytest.mark.xfail(strict=True)` naming its owning phase. Strict xfail is self-closing: when the owning phase lands, the test passes, pytest reports an unexpected pass, and the run FAILS until the marker is removed. The assertion is therefore neither weakened nor silently satisfied.
- **Marker count by phase**: 23 at the end of Phase 1. Phase 2 removed 9 (four marker lines covering nine parametrized cases), leaving 14, all owned by Phase 5.
- **Suggested next step**: none. This entry closes when the last xfail marker is removed in Phase 5; Phase 8 verifies that zero `xfail` markers remain in the file.
