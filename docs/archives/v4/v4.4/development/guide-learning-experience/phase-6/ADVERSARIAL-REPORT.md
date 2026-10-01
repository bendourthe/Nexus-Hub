# Adversarial Verification Report

Date: 2026-09-04. Scope: current Nexus-Hub v4.4.6 guide, embedded Training scenes, and browser interaction boundaries. Audit is read-only; only TEMP evidence was written. Observed guide SHA-256: 381007724d5d5ca6256fbabcefc05ca9a04beb794cc1a79cf7edb54de5435f38. The parent is actively correcting findings, so this is a pre-correction record, not final-tree approval.

## Attack surface

| Entry | Input and trust | Executed boundary |
|---|---|---|
| E1 | URL hash and legacy beat query, untrusted | Seven malformed routes, encoded markup, prototype property names, oversized and negative beat |
| E2 | Embedded Training JSON, repository-authored teaching fixture | Seeded literal closing-script and image-handler strings in terminal output |
| E3 | Public Training file-selection API and generated file buttons | Markup-like unknown file path remains text; no DOM image or handler execution |
| E4 | Training Run, progress, next, previous, restart, route exit | Skipped prerequisites, ten rapid sequences, cancellation, run state, failure injection |
| E5 | Graph branch and join buttons | Fail after successful join, retry, reset, missing branch |
| E6 | Loop scenario and next/reset controls | Thirty clicks for each of three stop conditions |
| E7 | Keyboard, fullscreen fallback, live reduced-motion preference | Enter, file arrows, focus trap, Escape restoration, mid-run preference change |

## Confirmed findings

### AF-1: Skipped Training steps fabricate a fixed game and passing tests (P2)

Reproduction: load a fresh guide at `#training/test`; click Run (reduced motion gives the same final state); inspect `src/damage.js`; click Show first hit. Completed scenes contain only `test`, and the source still returns `destroyed: true` without decrementing lives. Nevertheless the gate reports pass, the terminal reports six passed tests, the game switches to fixed damage and vertical movement, and the first-hit proof says two lives remain. This is a contradictory educational result, not execution of real project code or an external security breach.

Observed execution evidence: `observations.json`, case `skip directly to test then Run`. Root cause: `applySceneState` selects the absolute game config of the highest completed scene while `projectStateThrough` applies only completed file changes. Suggested correction: enforce declared prerequisites and invalidate downstream evidence on reset, or supply clearly identified coherent scene snapshots. Parent has acknowledged and is correcting this case.

### AF-2: Keyboard scene activation loses focus to BODY (P2)

Reproduction: fresh Training page; focus the second progress button; press Enter. Scene changes to review, but the focused button is removed during progress reconstruction and `document.activeElement` becomes BODY. This disrupts keyboard continuation and loses the visible focus indication. Preserve focus on the replacement active progress control or move it intentionally to the new scene heading.

Proof: `test_adversarial_focus.py::test_adversarial_progress_activation_preserves_keyboard_focus`; `focus-proof.txt` records the expected-preservation assertion failing. The run also emitted unrelated pytest cache-permission warnings; the assertion failure is explicit and independent of those warnings.

## Considered but rejected with observed evidence

| Candidate | Counter-hypothesis and actual routes | Per-route result |
|---|---|---|
| Delayed run completes after cancellation | Timed output is canceled by navigation/reset; sources are Run, progress/next/previous/restart, and hash exit | Ten rapid Run/next/restart/previous cycles finish not-run with no completed scenes. Exiting to Home during Run remains not-run after 2.2 seconds. |
| Markup executes in teaching output | Rendered strings use textContent; sources are authored scene output, file paths/content, and public selectFile | Seeded `<img onerror>` and closing-script text render literally. A public selectFile path containing an executable-looking image handler creates zero images and no handler flag. Seven malformed hashes neither execute nor emit page errors. HTTP body/cookie/header routes are not applicable: standalone HTML has no server input handler. Arbitrary replacement of trusted authoring JSON was not claimed covered. |
| Graph retains stale successful join | All branch mutations invalidate joined state; source is graph action buttons | Fail dates after join disables Combine and clears review readiness. Retrying dates permits a fresh join; reset/fail/decisions leaves join blocked. |
| Loop can run beyond its limit | Disabled button plus step bounds stop all paths; source is the fixed scenario select and next button | Thirty native DOM clicks per scenario end at its exact success/missing/budget stop state and disabled button. DOM mutation to inject unsupported option values is outside the user input surface. |
| Completion failure leaves false success | Completion catch removes the completion record and renders failed | Injected explorer appendChild failure at completion yields failed/Gate fail, initial files only, and no uncaught page error. |
| Mid-run reduced motion continues animation | Live preference change completes the run | At the audited SHA, enable reduced motion during Run; final output is complete after 120 ms and remains unchanged after 600 ms. |
| Fullscreen fallback strands keyboard focus | Isolation, focus trap, and Escape teardown cover fallback | Shift+Tab remains inside Training; Escape restores nhtPresent focus and leaves zero inert elements. File ArrowDown focuses src/game.js. Run Enter triggers one running state. |

## Non-blocking hardening observation

Artificially making explorer appendChild throw before Run enters its running state emits an uncaught injected error and leaves Gate pending, rather than the explicit failed state. Restoring the primitive and clicking Run recovers successfully. This requires mutation of a browser DOM primitive in the audit, not ordinary user input; it is not classified as an exploitable vulnerability. Evidence: `additional.json`, first two cases. Parent was informed so the same error boundary can be made consistent if desired.

## Untested limits

This bounded audit used installed headless Chromium on Windows and the actual local HTML. Native fullscreen is delegated to the parent's browser matrix; this audit injected native rejection to exercise fallback. Screen-reader speech, actual mobile hardware, Linux rendering, huge hostile authoring documents, and live human comprehension were not tested. No upstream service, real model, external sharing, or installer action exists in these simulated interaction paths, so no claims about those systems are made. No verifier panel was used; this was one independent breaker review.

## Assessment

FAIL at the recorded pre-correction state: two P2 findings require correction and fresh targeted reruns. No confirmed security vulnerability or external data write was observed. Parent owns correction and final-tree verification.

## Correction retest and final bounded verdict

Retested guide SHA-256: d5673b540efc9313ce1e83bd5424d443c2107317595cfe675183c13433db9635. Fresh evidence: `correction-retest.json` and `focus-retest.txt`. The historical failures above are retained as reproduction evidence; both are now resolved at this SHA.

- AF-1 resolved: fresh direct `#training/test` is blocked through both the native Run button and public NexusTraining.run API. Gate hold explains that `/describe full` must run first; no completed scenes, no output, no generated files, and no game fix are introduced.
- AF-2 resolved: keyboard Enter on the progress control leaves focus on the newly rendered active progress button. The original failing assertion now passes (1 passed). Selecting a command from Outline returns focus to its trigger.
- Dependency invalidation verified: all eight scenes completed in order through native controls; restarting implement retains only describe/review/plan, removes downstream files/proof, and restores the buggy game. Attempting test afterward is blocked and produces no output.
- Hidden-document boundary verified with an explicit limitation: bringing another headless Chromium tab forward left the original document visible, so that action did not exercise actual browser occlusion. Setting an instrumented document.hidden getter and dispatching visibilitychange exercised the production listener. An active run became not-run with empty output and no completion after 2.4 seconds; restoring visibility did not resume it. Source inspection confirms the listener calls cancelRun when document.hidden is true. Real desktop minimize/occlusion delivery remains untested by this headless audit.
- All correction checks completed without page errors. No production or repository files were edited by this audit.

Final verdict: CONDITIONAL PASS for this bounded independent audit at the retested SHA. Both confirmed findings are resolved; no confirmed blocking finding remains. Conditions are the explicitly untested environment/native-visibility limits above and the parent's full final-tree verification, not an unresolved reproduced defect. The non-blocking synthetic Run-entry DOM-primitive hardening observation remains unchanged.
