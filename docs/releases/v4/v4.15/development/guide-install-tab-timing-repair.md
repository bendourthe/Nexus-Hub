# Guide Install-Tab Test Timing Repair

Repair evidence for the guide animation test that blocked planning PR #652. For maintainers reviewing the separate test-only fix; covers the observed failure, controlled reproduction, timer handling, negative control, and qualification limits.

Date: 2026-11-13
Integration baseline: `c3c483d3b47c6e2100ebdff96880ee4ae031c5bb`
Incident: [PR #652 guide-render failure](https://github.com/bendourthe/Nexus-Hub/actions/runs/43512459515/job/132186052853).
Scope: `tests/guides/test_v41310_r44_r45_home.py` and this evidence record only. The guide, production animation, and eight planning-publication files are unchanged by this repair.

## Failure and Diagnosis

The guide-render remainder job reported one failure, 689 passes, and two skips. `test_a_tab_switch_restarts_that_systems_mockup` timed out after 20 seconds while waiting for the Linux mockup's `run` step to be visible.

The original test depends on real browser-timer progress and samples a short-lived prompt after a tab switch. The guide starts/stops its animation through IntersectionObserver and timeout callbacks. A real-time deadline therefore combines browser scheduling with the behavior assertion, although this test's purpose is tab restart state.

The unmodified focused test passed locally in 11.81 seconds. Separate probes also passed at normal CPU speed and 6x throttling. The precise scheduling condition on the CI runner was not reconstructed. The repair removes the demonstrable wall-clock dependency; it does not claim a production animation defect or a confirmed CPU-contention cause.

## Repair

The existing test-page helper accepts an optional clock flag, defaulting to false. Only this test installs and pauses Playwright's clock before navigation, following the pattern already used by the model-learning guide tests. Other tests retain their original clock behavior.

The test clicks Linux, macOS, then Linux again. It waits for each visible mockup to start at the paused prompt, checks that command and output are hidden, and explicitly advances the real callbacks into the run phase. Revisiting Linux verifies reset of a previously running mockup rather than only first entry into a new panel. No DOM animation step is assigned by the test, no retry is added, and no production timer is changed.

## Verification

| Check | Observed result |
|---|---|
| Original test with a deliberately paused clock | Expected Linux run-step timeout; controlled reproduction of timer-progress dependency, not a reconstruction of the CI host |
| Repaired test with the same paused clock | Passed Linux, macOS, Linux visits |
| Repaired test against an isolated guide copy with repeat playback deliberately disabled | Rejected the Linux revisit; recorded clicks were Linux, macOS, Linux, with stale run state, visible command and no live playback |
| Focused repaired test, rendering required | 1 passed in 35.74 seconds |
| Entire affected module, rendering required | 27 passed in 143.95 seconds |
| Repository-native fast profile | 18 passed, zero failures, skips or advisories in 77.6 seconds |
| Unicode and whitespace checks | Passed for the changed test; committed artifacts checked before publication |

The negative-control guide existed only in a temporary diagnostic copy. The tracked guide was never modified. Local browser proof used Playwright 1.64.0 on Windows; the CI lock uses 1.63.0, so remote qualification remains required.

From the repair checkout in Windows PowerShell 5.1, the affected-module check is:

```powershell
$env:NEXUS_REQUIRE_RENDER = '1'
python -m pytest -q tests/guides/test_v41310_r44_r45_home.py
```

Expected result at this snapshot: `27 passed`, with no rendering skip.

## Review and Publication Boundary

The single-file review checked the default-false helper behavior, real callback execution, preserved hidden-command/output assertions, bounded progression, cleanup in the existing finally block, and the deliberate wrong-behavior control. A larger persona fanout was not used for this small diff.

Considered but rejected: the helper changing every test's clock (the flag defaults false); weakened restart coverage (the test now revisits Linux and rejects disabled replay); and a wider timeout or retry masking the problem (the animation clock is explicitly driven instead).

This fix is published separately to preserve PR #652's eight-file planning scope. Merge requires current required checks; after that, the planning branch must incorporate the repair and pass its own current-head checks. No implementation task in the v4.15.12 adoption plan is completed by this maintenance fix.
