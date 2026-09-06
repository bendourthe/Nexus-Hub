# Models rebuild verification

The explicitly authorized Models-only rebuild replaces the eight-stage explanation with a learned-capability illustration, four selectable generation demonstrations, and separate model-capability and reasoning-effort controls. All markup outside Models matches the starting revision, `50d92065`. Home, the other Foundations sections, and Training retain their content and structure.

## Readability and visual evidence

| Measurement | Before | After |
|---|---|---|
| Default desktop section height | 2,320 px | 1,654 px |
| Default visible words | 653 | 359 |
| Canonical guide bytes | 399,921 | 397,110 |

The default view is 29% shorter with 45% fewer visible words. Both the inherited 400,000-byte gate and the 500,000-byte release ceiling remain unchanged.

- [Dark desktop preview](section-dark-1440.png) and [light desktop preview](section-light-1440.png).
- [Mobile language example](demo-light-320-language.png), [mobile world example](demo-dark-320-world.png), and [mobile multimodal example](demo-dark-320-omni.png).
- Diffusion progresses from [noise](animation-diffusion-0.png), through [emerging shapes](animation-diffusion-2.png), to the [finished illustration](animation-diffusion-5.png).
- [Layout matrix](layout-matrix.json): 40 cases, covering four demonstrations at 320, 420, 768, 1024, and 1440 pixels in both themes. No page overflow, clipped demo text, or page errors. Illustrations retain a stable stage height across tabs.
- Screenshots were inspected during the first draft and after corrections. The subtitle now uses the shared Foundations heading structure; comparison captions align; replay resets immediately to the initial illustration.

## Interactions and content

Language demonstrates successive token choices with clearly labeled illustrative scores. Diffusion demonstrates repeated noise removal. The world-model example shows a scene plus an action producing a predicted next view. Multimodal/omni combines text, a photo illustration, and voice, while distinguishing input support from generation support. These are local educational illustrations, not live model calls or private reasoning transcripts.

The model groups are approximate roles, not cross-provider benchmark equivalences. Opus/Sol is the stated assumption for the duplicated Luna in the request. Model names and conceptual sources were checked against the official links in [the plan](plan.md). Effort is a relative processing allowance, not a fixed loop count or a guarantee of correctness.

Animations are finite, replayable, stop offscreen and on route changes, and show their completed state with reduced motion. Arrow keys, Home, and End operate the tabs without changing guide pages. With JavaScript disabled, all four explanations remain available as static content, accompanied by a controls notice.

## Verification results

- [Affected guide suite](affected-tests.txt): **150 passed, one optional portfolio-copy skip**. This includes the new Models behavior suite, main guide contracts, byte gate, and neighboring Agentic Platforms and Harness contracts.
- [Final Models retest](final-models-tests.txt): **20 passed**, including the immediate noise reset on replay.
- [Retained neighboring contracts](retained-tests.txt): **9 passed** after retiring obsolete Models fixtures.
- [Runtime capture](runtime.json): all 12 start/intermediate/end states captured; JavaScript syntax passed; zero page errors and external requests; no Models animation remained active after completion.
- [Assertion migration](assertion-migration.json): replaces 24 obsolete Models assertions with current behavior coverage. Home keyboard checks now select tabs from the active page. Unrelated comparisons and harness coverage remain.
- [Scope evidence](scope.json): unchanged markup outside Models, no new dependency, no pipeline changes. Retired Models-only styles, GIF initialization, and connector initialization were removed.

Reproduce the focused checks from the repository root:

```powershell
$env:NEXUS_REQUIRE_RENDER = '1'
python -m pytest tests/guides/test_models_learning_lab.py tests/guides/test_nexus_hub_guide.py tests/guides/test_v441_phase1_contract.py tests/guides/test_v441_phase4_foundations.py tests/guides/test_v442_phase4_media.py -q
python docs/releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/capture-layout.py
python docs/releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/capture-animation.py
```

## Existing failures outside Models

The broad guide suite is not fully green. The [initial full run](initial-full-suite.txt) stopped at its four-failure limit; the [remaining tests](remaining-suite.txt) were then run, and affected tests were rerun after Models fixes. Seven remaining failures were reproduced against the unchanged starting guide:

| Existing issue or stale assertion | Baseline evidence |
|---|---|
| Home light-theme guardrail pills measure 4.462:1 contrast against the 4.5:1 threshold | [Full-page baseline sweep](baseline-sweep.json) |
| Agentic Platforms has two pixels of internal overflow at 320 pixels | [Baseline checks](baseline-other.json) |
| The class-declaration test rejects the existing `cx-png` marker | [Baseline checks](baseline-other.json) |
| The direct-address test no longer excludes the approved Home session dialogue | [Baseline prompt checks](baseline-prompt-checks.json) |
| Three prompt tests expect the old Query label, category name, and box-shadow marker | [Baseline prompt checks](baseline-prompt-checks.json) |

These are two existing visual issues and five stale test expectations. They remain outside this Models-only change. No remote publication was performed.
