# Scrolled native-zoom capture qualification for the v4.4 guide

**Target**: `guides/website/nexus-hub-guide.html` at blob `532dec2f3d78cfd27b3db10a93848c883740e033` on `develop` commit `46f2d93d`.
**Environment**: Windows 11, Playwright-bundled Chromium, 1280 x 800 physical viewport, reduced-motion preference, isolated browser profile, local guide file.
**Status**: Partial evidence for MT-446-2. Scrolled 200% captures now paint through Chrome DevTools Protocol (CDP), but the real OS occlusion and manual-reader gates remain open. No guide behavior changed.

## Method

The earlier [native-zoom qualification](../native-zoom-qualification/verification.md) established browser zoom factor `2`, `devicePixelRatio` `2`, and zero measured horizontal overflow across the guide, but Playwright's screenshot path returned blank images after scrolling. The repeatable [capture script](capture.py) uses the same local zoom extension and applies `chrome.tabs.setZoom` after each route change. It reads the zoom, theme, device pixel ratio, active scene, visibility, and overflow before capturing both the beginning and end of each target through `Page.captureScreenshot` with `captureBeyondViewport: false`.

The [minimal scrolled control](method-control.json) held zoom `2`, device pixel ratio `2`, and scroll position `840`: Playwright's [screenshot](screenshots/control-playwright.png) contained `0` black-text pixels, while direct CDP [capture](screenshots/control-cdp.png) contained `5,391`. Thus the prior blank images identify a Playwright capture-path limitation, not evidence that the scrolled guide is blank.

The [full capture metrics](metrics.json) record 16 route/theme states and 32 guide images: Home, six top-level Foundations scenes, and Training, each in dark and light themes at top and end positions. All states reported zoom `2`, device pixel ratio `2`, CSS viewport width `640`, visible target, and zero document and target horizontal overflow. Every image was 1280 x 800 with nonzero RGB variation. The `screenshots/` directory contains the full image matrix.

Representative direct visual inspection covered [dark Models top](screenshots/dark-models-top.png) and [end](screenshots/dark-models-end.png), [light Agentic Platforms top](screenshots/light-agentic-platforms-top.png), [dark Harnesses end](screenshots/dark-harnesses-end.png), [light Training end](screenshots/light-training-end.png), [light Tokens top](screenshots/light-tokens-top.png), [dark Context Engineering top](screenshots/dark-context-engineering-top.png), [light Harnesses top](screenshots/light-harnesses-top.png), and [dark Home end](screenshots/dark-home-end.png). These sampled viewports painted readable content without observed horizontal clipping. Top and end captures do not constitute inspection of every intervening scroll position or interactive state.

## Disposition

MT-446-2 remains open. A real browser session must still verify animation continuity after actual OS occlusion or tab hiding, and complete the manual 200% scroll/interaction inspection across both themes. MT-446-1's technical and non-technical reader exercise is separate. This evidence applies to the recorded guide blob and does not qualify the concurrent v4.13.4 Training rebuild.

The script is a disposable evidence generator, not part of the shipped guide. The local documentation and hygiene gates are recorded with the PR; this document does not revise the earlier failed screenshot evidence.
