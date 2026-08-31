# Guide rebuild design brief (v4.2.2)

**Date**: 2026-08-29
**Inputs**: the live pre-redesign guide (3,684 lines; recover with `git show v4.1.2:guides/website/nexus-hub-guide.html`), the rejected v4.2.x guide (2,906 lines at branch point), the 2026-08-29 maintainer screenshot review, and the existing baseline audits (`../guide-redesign-baseline/`).
**Consumers**: Phases 2-5 of `../../plans/v4.2.2-guide-cinematic-rebuild.md`. Every page phase designs against this file; a deviation from it is logged as `# DEVIATION:` in the phase session history.

## Verdict per reference

### v4.1.2 (live site) - what it did right, what it got wrong

Right: confident dense Home with a clear story arc (hero, difference, loop, get started); Training as a real 16:9 slide deck with outline, prev/next, and fullscreen (the maintainer explicitly wants the slide experience back); terminal mockups with typewriter output that FEEL like using the product; workflow pages with rich mock artifacts (analysis, review, plan, pentest, changelog) that show real outputs; constellation background giving the dark theme identity.

Wrong (per its own hallmark audit): dead-centered marketing hero with pill stats and hardcoded catalog counts; equal-card grids everywhere; marketing cadence ("autonomous team of world experts"); no light theme; whole-hash routing bug; decorative float animations.

### v4.2.x (rejected) - what it broke

- Home: hero subtitle wrapped at a different measure than the title; GitHub octocat icon cropped/misplaced in its button; copy button too tall for its terminal row; a permanent amber warning box (its origin allowlist never included the production host); macOS-first install tabs on a Windows-majority audience; verify commands (`/skills list`, `/commands`) as plain prose, not copyable; inter-section gaps so large the page reads empty (screenshot 3).
- Foundations: three persistent stacked overlay boxes (Model / Platform / Harness) that sit over the content at all times; a "Model alone vs Model with Nexus-Hub" toggle that is pure noise because both states are already visible; carousel dots with no context; examples ("app.js only", "One-off chat") that teach nothing on their own.
- Training: the Glow Booth slideshow lost the narrative; beats show a stage screenshot-like mock plus one caption line with no explanation of what the command did, why, or what to look at; the command strip (describe review plan ...) is unexplained.
- Cheatsheets: "Band 1" / "Band 2" section labels mean nothing; scopes are listed as bare tokens with no per-scope explanation.
- Light mode: the glow-styled logo mark floats on the light ground with no backdrop.
- Cross-cutting: none of it was ever rendered in a browser before review (known-gap DF-1), which is why all of the above shipped.

### Target (v4.2.2)

Sit between v4.1.2's structure and a stronger, calmer visual ambition: keep v4.1.2's density, narrative arc, terminal typewriters, and slide-capable Training; keep v4.2.x's light theme, theme toggle, four-page IA (Home / Foundations / Training / Cheatsheets), routing grammar, and data-driven scenes; add scroll-driven animated SVG diagrams (Foundations), an interactive app mockup + simulated terminal (Training), and per-scope command documentation (Cheatsheets). Modern, cinematic, compact, self-explanatory.

## Design language decisions (binding)

### Typography

- System stacks unchanged (`--sans`, `--mono`). Base 16px, line-height 1.6 body / 1.15 headings.
- Scale: H1 `clamp(2rem, 4.5vw, 2.9rem)`; H2 `clamp(1.35rem, 2.6vw, 1.7rem)`; H3 `1.1rem`; eyebrow `11px` uppercase tracked.
- **Shared measure**: one token `--measure: 62ch`. The hero H1 and its lead paragraphs BOTH use it (this fixes the screenshot-1 wrap complaint). Body copy elsewhere caps at `--measure`.

### Spacing (compact by construction)

- 4px base scale as tokens: `--sp-1: 4px` through `--sp-8: 48px`.
- Section rhythm: `--sec-pad: 32px` desktop, 22px under 720px (v4.2.x used 54px+; roughly half).
- Section separators are eyebrow + heading, not empty air; the `.divider` element is dropped.
- Card padding 18-20px. Grid gap 14px.

### Color and theming

- Keep the v4.2.x token architecture verbatim (`:root` + `html[data-theme=dark|light]` blocks, `portfolio-theme` localStorage key, dark default, anti-FOUC bootstrap). It is proven and the portfolio host depends on the key.
- Trim the accent rainbow: cyan/teal identity plus ONE semantic triple (green / amber / red) for status. `--violet` is deleted.
- Light-mode brand chip: in light theme, `.brand .mark` and any hero mark sit on a rounded (10px) `#07141a` chip with 3px padding so the glow raster reads. No new image embed; the existing `#nexus-mark` symbol is reused (embedding `assets/nexus-hub-primary.png` raw is banned: 1.59 MB).

### Motion vocabulary

- `.reveal` elements start `opacity: 0; translateY(14px)` and gain `.in` from one shared IntersectionObserver (threshold 0.15). CSS transition 500ms cubic-bezier(.22,.9,.3,1), staggered via `--reveal-delay`.
- Continuous animation only inside on-screen, observer-gated components (constellation, diagram loops, typewriters). Nothing animates off screen.
- `prefers-reduced-motion`: `.reveal` is fully visible, diagrams show final state, typewriters print instantly, constellation draws one static frame. Never crush durations to 0.001ms as a substitute for a static design.
- Transform/opacity only; no layout-property animation.

### Diagram style (Foundations and beyond)

- Inline SVG, stroke-first (1.5-2px), rounded caps, colors via CSS custom properties so both themes work from one markup.
- Labels are real `<text>` at >= 12px effective size; below 420px diagrams stack vertically rather than shrink.
- Animation via CSS on SVG elements (stroke-dashoffset draws, transform pulses) triggered by the shared observer; small rAF loops only where CSS cannot express it (e.g., packet-along-path).

### Components (shared)

- Terminal chrome: keep the v4.1.2/v4.2.x `.term` pattern (traffic-light bar, label, body) and the typewriter engine (cancelable token, click-to-skip, REDUCE-aware). It is the strongest asset in both references.
- Copy button: slim variant everywhere -- height 24px, padding 2px 8px, 11px label, vertically centered via the `.cmd-line` flex row. Injected as a sibling (never inside the `data-copy` code element).
- Tabs: keep `[data-tabs]` pattern; Windows panel FIRST and default-active.
- Callouts: neutral info style only; the amber untrusted-origin warning and `isDocumentedGuideOrigin()` are DELETED (maintainer decision 2026-08-29).

### Hard contracts (unchanged)

Single self-contained file; zero runtime network references; base64 favicons + `#nexus-mark` symbol preserved verbatim; `portfolio-theme` allowlist bootstrap; hash grammar `#<page>`, `#training/<scene>?beat=n`, `#cheatsheets/<stop>` with legacy `HASH_REWRITES`; icon-only GitHub link (`.nav-gh`, aria-label "Nexus-Hub on GitHub"); install commands verbatim (`INSTALL_SH` / `INSTALL_PS` in the test file); no hardcoded catalog counts (`ONBOARDING_STALE`); hostile fixture strings rendered via textContent; file under 500 KB.

## Per-page requirements

- **Home (Phase 2)**: hero on the shared measure; comparison table kept but tightened; install section per the component decisions with copyable `/skills list` and `/commands` verify cells; a compact "the loop" overview linking into Training/Cheatsheets; closing next-steps band. No pill stats, no counts.
- **Foundations (Phase 3)**: scrollytelling scenes per `foundations-script.md` (written in Phase 3.1). No persistent overlays, no compare toggle, no carousel dots.
- **Training (Phase 4)**: walkthrough per `training-script.md` (Phase 4.1): interactive Glow Booth mockup + simulated terminal + fullscreen slide mode, all driven by the redesigned `training-scenes.json`.
- **Cheatsheets (Phase 5)**: intent-named sections ("The daily loop", "Understand a repo", "Ship and govern", "Utilities and aliases" -- final wording may be tuned in-phase); every command shows each scope with a one-line description derived from its command file; copyable cells; deep-link stops preserved.

## Verification hooks

Phases verify against this brief via: the shared-measure token on hero title AND lead; `--sec-pad` <= 32px; no `--violet` token; slim copy button height <= 26px; Windows tab first; no `#untrustedCopyWarning`; render-harness screenshots reviewed per phase (`tests/guides/tools/render_guide.py`).
