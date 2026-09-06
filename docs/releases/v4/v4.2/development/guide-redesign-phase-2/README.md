# Phase 2 shell evidence

**Date**: 2026-08-29
**Method**: source verification. No browser tools in this session (see v4.2.0 DF-1). Last-phase human testing covers viewports, both themes, keyboard, reduced motion, and `file://`.

## What landed

- Semantic light/dark tokens on `html[data-theme]`, applied before first paint via an allowlisted `portfolio-theme` initializer (`light` or `dark` only, try/catch around storage).
- Primary nav: Home, Foundations, Training, Workflows, Reference, GitHub, theme control. Installation removed from chrome.
- Page hash uses the first segment (`#training/<scene>` stays on Training). Unknown page ids rewrite to `#home`.
- Constellation: dark mode only, paused when `document.hidden`, one static frame under `prefers-reduced-motion`.
- Shell hallmark: left-aligned hero, solid (not gradient) accent, no float/fade entrance, visible `:focus-visible`.

## Still later

- Home copy, install commands, and the six-node ribbon (Phase 3).
- Scene/beat URLs (Phase 5).
