# Decision: Require explicit rendered state in the visual gate

Status: implemented - browser verification activates and confirms each requested route, theme, viewport, and interaction state before measuring visible text fragments

## Problem

An HTML file can render successfully while the specific state under review remains untested. A default-route or default-theme screenshot does not prove a hash-routed page, alternate theme, reduced-motion mode, or interaction state. The v4.4 guide adds four routes, two themes, four release widths, and eight Training states, so relying on whatever state appears after page load would allow most of the product surface to escape the visual gate.

Overlap measurement also used whole-element bounding boxes. Those boxes include unpainted space around wrapped inline text and text clipped by scrolling or hidden ancestors, which produced false overlap findings even when no visible glyph fragments collided. Allowlisting those findings would weaken the same gate that must catch real text collisions.

## Decision

Rendered verification explicitly selects every requested fragment, theme, viewport, reduced-motion setting, and interaction state, then confirms that the requested state is visible before collecting evidence. A requested state that cannot be activated is a failed case, not a silent fallback to the default page.

The visual-defect detector measures direct text-node `Range.getClientRects()` fragments for overlap. It clips those painted fragments to `overflow: auto`, `scroll`, `hidden`, or `clip` ancestors that establish clipping boxes. Non-replaced inline and `display: contents` ancestors do not create clipping boxes; zero-sized block clipping ancestors still do. Geometry, runtime errors, outbound requests, contrast, keyboard behavior, reduced motion, and horizontal overflow are evaluated against the activated state.

The guide's release sweep is the proving use: four routes, two themes, and four widths form 32 base cases, while all eight Training states are traversed separately for dynamic content coverage. The detector retains a clean-control path and true-overlap regression fixtures so fewer false positives do not mean weaker detection.

The repository enforces the release sweep in a dedicated `guide-render` CI job for pull requests with relevant changes. The `changes` job supplies the relevance decision, the render job installs and caches Playwright Chromium, and `NEXUS_REQUIRE_RENDER=1` makes unavailable rendering a failure. The `ci-required` aggregate consumes the render-job result so a relevant pull request cannot satisfy the protected required check when the visual gate fails.

## Alternatives considered

- **Measure only the default route and theme.** Rejected because hash-routed pages, light mode, narrow breakpoints, and dynamic Training states can fail independently while the default Home view remains green.
- **Use guide-specific assertions without changing the reusable detector.** Rejected because the false overlap geometry affects any rendered HTML with wrapping or clipping, and the functional-verification tool is the repository's procedure owner for that boundary.
- **Keep whole-element boxes and allowlist the false positives.** Rejected because allowlists would normalize known detector noise and could hide a later real collision at the same selector.
- **Compare screenshots pixel by pixel.** Rejected because pixel baselines are brittle across browser and font environments, do not identify semantic or interaction failures, and still require separate reasoning about which state was captured.
- **Treat an unavailable or unactivated browser state as a clean skip.** Rejected because a fail-open result would certify exactly the state the gate did not observe. Environment-only absence must remain explicit missing coverage.
- **Install Chromium in the existing broad tests job.** Rejected because it would add browser installation time and a visual-testing responsibility to every broad test run, including changes that cannot affect the guide or detector.
- **Retain local-only browser coverage and leave MT-1 open.** Rejected because local evidence cannot prove that a clean CI runner can install Chromium and execute the fail-closed gate.
- **Run an optional render job outside the required-check aggregate.** Rejected because the protected required check could pass while the visual gate failed or never ran for a relevant pull request.

## Consequences

- Visual evidence names and proves the route, theme, viewport, motion preference, and interaction state it claims to cover.
- Wrapped and clipped text no longer generates overlap findings from unpainted element-box space, while true painted-fragment collisions still fail.
- The detector carries additional DOM geometry and clipping logic that needs focused regression fixtures.
- Complete guide verification takes longer because the browser must activate and inspect every declared state rather than sample one default render.
- CI environments that enforce this gate must install a supported browser and run with fail-closed rendering enabled; environments without that setup must report the coverage gap rather than claim a pass.
- Relevant pull requests incur a dedicated browser job, while irrelevant changes avoid that cost; the cache key follows the resolved Playwright version so an incompatible browser bundle is not reused.
