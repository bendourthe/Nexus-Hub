# Training walkthrough script (v4.2.2 Phase 4)

**Consumers**: sub-tasks 4.2 (booth mockup), 4.3 (simulated terminal), 4.4 (sequencer + slide mode). The redesigned `guides/website/example/training-scenes.json` is the single source of truth at runtime; this file explains the design behind it.

## Shape of the experience

Training is a numbered walkthrough of eight steps, one per taught command, over one example app. Each step composes four things on screen:

1. **What you are trying to do** - the step's `intent` prose, written in second person.
2. **The interactive Glow Booth mockup** - driven by the step's `booth` state; the learner can also click it freely. This is where the learner SEES the bug and later sees it fixed.
3. **The simulated terminal** - the step's `command` pre-filled; pressing Run types out the step's `output` line by line, exactly as the real assistant would report it.
4. **What it left behind** - the `artifact` card plus the `gate` verdict, so the durable-output lesson lands every step.

The same eight steps play in place (scroll page) or as fullscreen slides (Present). One data model, two presentations.

## Why Glow Booth

`guides/website/example/glow-booth/` is a five-pose instant-camera app with two deliberately frozen bugs in `logic.js`:

- `computeStamps` loops `i < captured.length - 1`, so a perfect set of five poses awards **4 / 5**.
- `restartState(prev)` returns `lastPose: prev.lastPose`, so **Restart leaves the last pose on stage**.

`glow-booth-shuffle-reference/` is the sibling used by `/compare`: it has no off-by-one, adds `shuffle()`, and sparkles on a full meter. The mockup reproduces all of this faithfully, so the guide never misteaches what the downloadable example actually does.

## Booth mockup contract

State comes from `scene.booth`: `captured[]`, `fixed` (bugs patched or not), `shuffle`, `sparkle`, `highlight` (`meter` | `stage` | null), `note`.

- **Stage**: shows the last captured pose as a tinted gradient card with its label. When `fixed` is false and Restart is pressed, the stage keeps the last pose (the bug, visible). When `fixed` is true, Restart clears it.
- **Pose strip**: five buttons (Dawn, Neon, Forest, Studio, Spark). `shuffle: true` renders them in the scene's shuffled order. Clicking captures that pose.
- **Meter**: five pills + the stamp count. The count uses the buggy formula when `fixed` is false (`captured.length - 1` when a pose was captured, floor 0) and the correct one when true. A full fixed meter with `sparkle: true` draws the sparkle overlay.
- **Note line**: the scene's `note`, telling the learner exactly what to try.
- Interactions are real buttons, keyboard operable, with visible focus. Nothing loads the real app; this is a self-contained simulation.

## Terminal contract

- Chrome matches the install terminals (traffic lights, label, body).
- Prompt line is pre-filled with `scene.command`, has a slim copy button, and a Run affordance (click or Enter while focused).
- Run types the command, then reveals `scene.output` lines with a short stagger. Reduced motion prints instantly.
- Running again while a run is in flight completes the previous output immediately, then starts the new one (no interleaving).
- Free-typed input is not supported; the input is read-only and a hint names the runnable command. Every line is written with `textContent`, so the hostile fixture strings in scene 1 (`<img onerror>`, `</script>`) render as literal text and can never execute.

## Step sequencer and slide mode

- Steps: Previous / Next / Restart, a step counter, and an Outline popover listing all eight with their stage labels.
- Deep links keep the existing grammar: `#training/<scene-id>?beat=<n>`; unknown scene or out-of-range beat clamps to the nearest valid step.
- **Present** requests fullscreen on the training root; if the Fullscreen API is unavailable or denied, it falls back to a fixed viewport overlay with identical keyboard control. Esc, browser back, and `fullscreenchange` all restore normal flow and the learner's position.
- Keyboard inside training: Left/Right or Space advance steps, `f` toggles present mode, Esc exits. Page-level arrow paging already yields to Training (`current === "training"` guard in the router).

## Scene-by-scene summary

| # | Command | Booth state shown | The lesson |
|---|---|---|---|
| 1 | `/describe full` | empty, buggy | Start with a map, not a guess |
| 2 | `/review` | five captured, meter reads 4/5, `highlight: meter` | The bug is visible before any fix |
| 3 | `/plan feature` | unchanged, buggy | A gated phase with a written DoD |
| 4 | `/implement ... phase-1` | five captured, `fixed: true`, meter reads 5/5 | The fix is observable, tests prove it, commit stays local |
| 5 | `/compare ../glow-booth-shuffle-reference` | empty, fixed, no shuffle yet | Reverse-engineer the idea, never import wholesale |
| 6 | `/test unit` | shuffled order, fixed | Coverage is a gate, not a screenshot |
| 7 | `/update changelog` | shuffled, sparkle on | The record is real; the tag is not automatic |
| 8 | `/presentify ...` | final state | Every command left a file behind |

## Parity contracts preserved

- Inline `<script type="application/json" id="nh-training-scenes">` must equal `example/training-scenes.json` after parse (`test_inline_scenes_match_example_json`).
- Every catalog command is trained here, listed on Cheatsheets, or documented as declined (`test_every_catalog_command_is_training_cheatsheets_or_declined`).
- Hostile fixture strings survive as text (`test_hostile_fixture_strings_are_rendered_via_textcontent`, un-xfailed by this phase).
