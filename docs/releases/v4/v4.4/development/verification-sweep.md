# v4.4.0 Guide Verification Sweep

**Date**: 2026-08-31
**Scope**: `guides/website/nexus-hub-guide.html`, all four pages, dark and light themes, and 320 / 420 / 900 / 1440 px viewports.
**Outcome**: PASS. The final tree has zero visual-detector findings, zero WCAG AA contrast failures, zero horizontal-overflow cases, zero browser runtime errors, zero outbound requests, complete named keyboard paths, and a true static reduced-motion path.

## Rendered Matrix

The fail-closed browser sweep ran the 32 base cases (four pages x two themes x four widths), then traversed the seven additional Training states in both themes at every width for 56 more page-state cases. A DOM TreeWalker selected each unique parent of a nonblank text node under the header or active page, excluded hidden, `aria-hidden`, and non-rendered nodes, and required a nonempty text Range rectangle. The same pipeline sampled nonempty computed `::before` and `::after` text, excluding `none`, `normal`, empty content, and URL values. Foregrounds came from computed CSS color or SVG fill. Backgrounds were walked to the painted ancestor and alpha-composited, including normalized `color(srgb ...)` values. WCAG 2 relative luminance used a 4.5:1 threshold for normal text and 3:1 for large text.

| Page | Samples per theme at 320 / 420 / 900 / 1440 | Both-theme total |
|---|---:|---:|
| Home | 116 / 116 / 111 / 111 | 908 |
| Foundations | 188 / 188 / 194 / 194 | 1,528 |
| Training default state | 81 / 81 / 84 / 84 | 660 |
| Cheatsheets | 353 / 353 / 356 / 356 | 2,836 |
| **Base-matrix total** | **2,966 per theme** | **5,932** |

The seven additional Training states contributed 5,076 samples beyond the default state:

| Training state | Samples per theme at 320 / 420 / 900 / 1440 | Both-theme total |
|---|---:|---:|
| `/describe` | 81 / 81 / 84 / 84 | 660 |
| `/review` | 82 / 82 / 85 / 85 | 668 |
| `/plan` | 84 / 84 / 87 / 87 | 684 |
| `/implement` | 85 / 85 / 88 / 88 | 692 |
| `/compare` | 93 / 93 / 96 / 96 | 756 |
| `/test` | 94 / 94 / 97 / 97 | 764 |
| `/update` | 93 / 93 / 96 / 96 | 756 |
| `/presentify` | 93 / 93 / 96 / 96 | 756 |
| **All-state Training total** | **2,868 per theme** | **5,736** |

Across the base matrix and every Training state, the audit measured 11,008 visible text samples, including 552 generated pseudo-text samples, and represented 265 unique computed styles across both themes, above the v4.2.3 baseline of 242. No sample fell below its WCAG AA threshold, and no computed foreground or background color was unsupported by the audit.

## Visual Detector

The functional-verification detector ran separately for Home, Foundations, Training, and Cheatsheets in dark and light themes, each at 320 / 420 / 900 / 1440 px. All eight route/theme runs reported 0 gate findings and 0 allowlisted findings.

Rule 3 was corrected during this sweep because whole-element bounding boxes treated wrapped inline text and horizontally clipped command text as painted overlaps. It now compares direct text-node `Range.getClientRects()` fragments clipped to `overflow: auto|scroll|hidden|clip` ancestors that establish clipping boxes. Non-replaced `display: inline` and `display: contents` ancestors do not clip fragments; zero-sized block clipping ancestors still do. The 36-test detector suite proves multiline, clipped, non-clipping-inline, and zero-sized-block cases while retaining the true absolute-position overlap. The final guide matrix covered 32 route/theme/viewport combinations with 0 findings and 0 allowlisted exceptions.

## Keyboard and Semantics

- Home's six platform marks are a labelled native list of static compatibility information and do not pollute the Tab order.
- The install `role=tab` controls use roving `tabindex`; ArrowLeft, ArrowRight, Home, and End select and focus the expected tab. Every tab has `aria-controls`, every panel has reciprocal `aria-labelledby`, and the inactive panel is natively hidden.
- Every page-progress dot is a real labelled anchor with an `href`; the current dot exposes `aria-current="page"`. Each target is at least 24 x 24 px, and every active and inactive visual dot maintains at least 3:1 non-text contrast in both themes.
- Active page navigation is Tab reachable and activates with Enter. Disabled end-state links expose `aria-disabled="true"` and remain readable at full token contrast.
- The Asteroids game is Tab reachable. Left / Right or A / D rotate, Up or W thrusts, and Space fires; the browser sweep proves Tab plus Space changes the bullet state.
- The file explorer is a labelled tree of native buttons. ArrowUp, ArrowDown, Home, and End move focus; Enter and Space select the focused file.
- No visible pointer navigation action is absent from the Tab order.

## Reduced Motion

The browser loaded every page with `prefers-reduced-motion: reduce`, sampled immediately and after settlement, and found zero running animations in both states. Visible text-bearing descendant counts were Home 195, Foundations 297, Training 122, and Cheatsheets 695. The dark-theme constellation pixels remained unchanged; its opacity transition is disabled. Foundations reveals and paths rendered at their final state with no travelling pulses. Asteroids remained paused for `reduced-motion`; Advance one step incremented the frame exactly once and the loop stayed paused. Training terminal output used its immediate path.

## Runtime, Offline, and Performance Contracts

- Every HTTP and HTTPS request was aborted and recorded; the matrix observed zero outbound requests.
- Every case reported zero console errors and zero page errors.
- Every case kept document width within viewport width.
- Existing Asteroids tests retain the 0.05-second maximum delta, document-hidden pause, offscreen pause, deterministic seeded state, and static-step behavior.
- The final Windows working file is 490,106 bytes, below the strict 500,000-byte gate by 9,894 bytes.

## Size Reckoning

The guide entered the plan as a 397,397-byte normalized Git blob. The final normalized content is 487,893 bytes, a 90,496-byte increase. The literal Windows working file is larger because of CRLF line endings; the enforced 490,106-byte value still passes the same 500,000-byte limit.

| Component phase | Normalized bytes after phase | Increment |
|---|---:|---:|
| Starting guide | 397,397 | - |
| Phase 1: Home identity, platform rail, and installation | 407,851 | 10,454 |
| Phase 2: Foundations model, token, and prompt lessons | 426,651 | 18,800 |
| Phase 3: Foundations agent, context, harness, and practice lessons | 457,474 | 30,823 |
| Phase 4: playable Asteroids engine | 479,244 | 21,770 |
| Phase 5: terminal, cumulative explorer, and eight-command state loop | 486,388 | 7,144 |
| Phase 6: typography, navigation, detector, and reduced-motion corrections | 487,893 | 1,505 |

The offline guarantee remains non-negotiable and no asset was externalized. Because both the normalized content and the actual Windows file remain below budget, no cap change or user approval was required.

## Fixes Produced by the Sweep

1. Raised the mini-terminal label and Cheatsheets teaching-code typography to the 12 px detector floor.
2. Replaced detector whole-element overlap geometry with clipped painted text fragments and preserved the non-clipping inline-element boundary.
3. Removed 40 percent whole-component opacity from disabled page links and retained visual de-emphasis through full-contrast tokens and transparent background.
4. Disabled the constellation opacity transition under reduced motion.
5. Replaced fake clickable progress dots with 24 x 24 px native labelled anchors and gave both dot states at least 3:1 non-text contrast.
6. Added roving keyboard behavior and reciprocal tab-panel relationships to the Home install tabs.
7. Removed opacity from Training's generated slash labels so all pseudo-text meets WCAG AA, then added generated-text and all-scene coverage to the browser audit.

## Render Evidence

`docs/releases/v4/v4.4/development/guide-rebuild/renders/phase-6/` contains 32 final PNG captures, one for every route/theme/width case, totaling 12,449,986 bytes. Representative mobile and desktop endpoints for all four pages were visually inspected during implementation; no clipping, broken hierarchy, inconsistent chrome, or unintended horizontal layout was observed.

No human or manual testing suggestions are emitted for this non-final phase. The browser automation and screenshot inspection above are implementation evidence.
