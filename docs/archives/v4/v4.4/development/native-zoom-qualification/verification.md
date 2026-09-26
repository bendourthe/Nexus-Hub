# Native zoom qualification for the v4.4 guide

**Target**: `guides/website/nexus-hub-guide.html` at `e455ce3b` on `develop`.
**Environment**: Windows 11 build 26200, Playwright-bundled Chromium 151.0.7922.34, 1280 x 800 physical browser viewport, reduced-motion preference, local `file://` guide.
**Status**: Partial evidence for v4.4 MT-446-2. Native browser zoom and layout geometry were exercised; scrolled visual painting and OS occlusion remain unverified. No guide code changed.

## Method and observations

The disposable Manifest V3 [probe extension](extension/manifest.json) used the browser's [`chrome.tabs.setZoom`](https://developer.chrome.com/docs/extensions/reference/api/tabs#method-setZoom) and `getZoom` APIs in an isolated Playwright profile, following [Playwright's extension launch contract](https://playwright.dev/python/docs/chrome-extensions). Unlike viewport resizing, this returned zoom factor `2`, raised `devicePixelRatio` from `1` to `2`, and reduced `innerWidth` from `1280` to `640`. Route changes reset the zoom factor, so the final matrix re-applied and read back factor `2` before every capture. The first unguarded run is not used as evidence.

The final matrix covered Home, the six top-level Foundations scenes currently present in the guide (Tokens, Models, Prompt Engineering, Context Engineering, Agentic Platforms, Harnesses), and Training, in dark and light themes: 16 combinations. Each reported active route and visible scene, browser zoom factor `2`, `devicePixelRatio` approximately `2`, `innerWidth` `640`, document horizontal overflow `0`, and scene horizontal overflow `0`. This is DOM geometry evidence, not proof that every scrolled scene painted correctly. The historical manual exercise's "seven lessons" wording does not match the current six top-level scenes; nested loop and graph material remains inside Harnesses.

| Route or scene | Dark: zoom / document overflow / scene overflow | Light: zoom / document overflow / scene overflow |
|---|---|---|
| Home | 2 / 0 / 0 | 2 / 0 / 0 |
| Foundations: Tokens | 2 / 0 / 0 | 2 / 0 / 0 |
| Foundations: Models | 2 / 0 / 0 | 2 / 0 / 0 |
| Foundations: Prompt Engineering | 2 / 0 / 0 | 2 / 0 / 0 |
| Foundations: Context Engineering | 2 / 0 / 0 | 2 / 0 / 0 |
| Foundations: Agentic Platforms | 2 / 0 / 0 | 2 / 0 / 0 |
| Foundations: Harnesses | 2 / 0 / 0 | 2 / 0 / 0 |
| Training | 2 / 0 / 0 | 2 / 0 / 0 |

At scroll position zero, the inspected [dark Home](screenshots/positioned-dark-home.png), [light Home](screenshots/positioned-light-home.png), [dark Training](screenshots/positioned-dark-training.png), and [light Training](screenshots/positioned-light-training.png) captures show readable headings and body text without horizontal clipping in the initial viewport. The menu replaces desktop navigation at 200% zoom. These four screenshots do not cover the rest of the pages.

Scrolled Playwright screenshots at 200% were blank even when DOM hit targets remained in view: the Models heading had a bounding rectangle within the viewport, its scene had class `reveal in` and computed opacity `1`, and a 100% [Models control](screenshots/model-control-100.png) painted normally. A minimal white HTML page with a black H1 at the same zoom and scroll position also captured as [blank white](screenshots/minimal-control-headless-200.png). Headed and headless Chromium reproduced that control failure. This isolates a screenshot-path limitation; it does not establish that the guide itself is blank, and it prevents a visual pass for scrolled content.

The extension reported the OS browser window moving from `normal` to `minimized` and back, but the page reported `document.visibilityState == "visible"` and emitted no `visibilitychange` event. A same-window tab switch produced the same result. This automated environment therefore did not exercise the hidden/occluded page state the manual gate requires. Animation continuity after true occlusion remains unmeasured.

## Disposition

MT-446-2 remains open. A human or a browser harness that paints scrolled 200% content and delivers real hidden-state transitions must inspect Home, Foundations, and Training in both themes, then record whether text stays readable, content is unclipped, and animations resume without an unexpected restart. This record narrows the missing evidence; it does not replace the technical and non-technical reader exercise in MT-446-1 or qualify the in-progress v4.13.4 Training rebuild.

The documentation gate `python scripts/ci/run.py --profile full --only docs --quiet` passed 8/8 after this evidence was assembled. The report and screenshots are the output of the browser exercise; no runnable guide behavior was changed.
