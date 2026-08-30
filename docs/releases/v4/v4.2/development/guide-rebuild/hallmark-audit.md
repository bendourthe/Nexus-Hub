# Hallmark audit - rebuilt guide (v4.2.2 Phase 6)

**Date**: 2026-08-29
**Scope**: `guides/website/nexus-hub-guide.html` after Phases 1-5.
**Method**: the anti-slop gates from `catalog/skills/developer-experience/hallmark-design/SKILL.md`, applied to the rebuilt file and its rendered captures. Compare with `../guide-redesign-baseline/hallmark-audit.md`, which audited the v4.1.2 guide and found 10 shell-level failures.

## Findings against the v4.1.2 baseline failures

| Gate | v4.1.2 finding | Status now |
|---|---|---|
| 1 - dead-centered hero | Centered logo, gradient headline, centered CTA row, pill stats | **Fixed.** Hero is left-aligned on a shared measure; no centered stack. |
| 2 - equal card grids | `.grid-4` benefits row and eight equal navcards | **Fixed.** No equal-width card grid remains. Home uses a comparison table and a loop strip; Cheatsheets uses full-width command blocks with an internal scope grid (a data table, not decorative cards). |
| 3 - left-aligned reading | Failed (`text-align: center` hero) | **Fixed.** No centered body text anywhere. |
| 5 - competing bands | Every Home band competed; no focal action | **Fixed.** Home is hero -> install (the one action) -> comparison -> loop -> next. Install is the single focal block. |
| 6 - uniform rhythm | `padding: 54px 0` on every band | **Fixed.** `--sec-pad: 32px`, and sections separate by eyebrow + heading rather than by empty space. Foundations scenes use a hairline rule. |
| 7 - unmotivated gradient text | Cyan-to-teal `background-clip: text` on H1, wordmark, buttons | **Fixed.** No `background-clip: text` in the file. Accent is a flat token. |
| 8 - semantic rainbow | `--violet`, `--red`, `--amber`, `--green`, `--cyan`, `--teal`, `--blue` | **Fixed.** `--violet` deleted; the palette is the cyan/teal identity plus one semantic triple (green / amber / red) used only for status. |
| 11 - dark-only tokens | No light theme at all | **Fixed.** Full light theme, WCAG AA verified in both. |
| 20 - pill stats | "252 skills, 14 commands, 22 hooks..." as hero proof | **Fixed.** No counts anywhere on Home; `ONBOARDING_STALE` enforces it. |
| 22 - card as default container | Card wrapped paragraphs, stats, nav, claims | **Largely fixed.** Cards now hold only genuinely card-shaped content (a command entry, an artifact, a gate). Prose is not carded. |
| 25 - decorative animation | Hero mark float, fadeUp on every page, constellation | **Improved, not eliminated.** The hero float is gone and page fade is a short 0.32s state transition. The constellation remains: it is the product's visual identity, dark-only, paused when hidden or in light theme, and fully static under reduced motion. Kept deliberately. |
| 26 - fake click targets | `a[data-go]` with no `href` | **Fixed.** Every navigational anchor carries a real `href`; `data-go` only intercepts. |
| 27 - crushed reduced motion | Durations set to 0.001ms | **Fixed.** Reduced motion renders true static end states, verified in the browser. |
| 28, 30 - marketing cadence | "autonomous team of world experts", restated claims | **Fixed.** Hero states what it is in plain terms. No superlatives; the comparison table cites repository artifacts rather than adjectives. |
| 24 - emoji bullets | None found | Still none. |

## New surfaces introduced by this rebuild

| Surface | Verdict |
|---|---|
| Foundations SVG diagrams | Pass. Hand-authored per concept; no stock diagram shapes, no uniform icon row. Each diagram shows a different mechanism rather than repeating one template. |
| Training booth mockup | Pass. It reproduces a real app's real behavior, including its bugs; nothing decorative. |
| Simulated terminal | Pass. Chrome matches the install terminals, so the page has one terminal language rather than two. |
| Cheatsheets scope grid | Pass. Dense reference data in a scannable grid; dotted row separators rather than card-per-scope, which would have re-introduced gate 2. |
| Loop strip (Home) | Borderline, kept. Six rounded pills in a row is close to gate 20's pill pattern, but these are navigation into Cheatsheets stops with distinct labels, not decorative stat chips. Reviewed and kept deliberately. |

## Consciously kept

Two items were flagged and kept, each with a reason rather than an oversight:

1. **The constellation canvas.** Decorative motion by gate 25's letter, but it is the identity of the dark theme, costs nothing when hidden or reduced, and its removal would make the dark theme generic. Kept.
2. **The Home loop strip's pill shape.** See above.

## Not audited here

Font rendering on non-Windows platforms, and real-device touch behavior. Both belong to last-phase human testing.

---

# v4.2.3 refinement pass

**Date**: 2026-08-29
**Scope**: the surfaces v4.2.3 added or reworked. The v4.2.2 findings above still hold; this section records only what changed.

## New and reworked surfaces

| Surface | Gate risk | Verdict |
|---|---|---|
| Home's animated comparison | 2 (equal card grid), 20 (pill row) | **Pass.** It is a five-row transformation list, not two columns of cards and not a row of chips. Each row is a labelled concern with an unaided statement, a connector that draws, and a harnessed statement. The rows differ in content weight rather than being five identical cells. |
| Fluid full-width body copy | 13 (measure) | **Deliberate deviation, at the maintainer's explicit instruction.** Removing every text cap means long lines at wide viewports, which the classic measure guidance argues against. The maintainer reviewed both options with rendered previews and chose the container-filling one. Recorded here so a future reader sees a decision, not an oversight. |
| Cheatsheets usage terminals | 22 (card as default container), consistency | **Pass.** They reuse the shared `.term` chrome, so the guide has one terminal language across Home, Training, and Cheatsheets rather than a third invented style. |
| Training icon controls | 21 (unlabelled controls), 26 (fake targets) | **Pass.** Three real buttons, each with `aria-label`, `title`, and a visible focus ring; Outline keeps a text label because a glyph does not carry its meaning. Verified keyboard-reachable after the DOM move. |
| Loop-stage progress strip | 20 (pill row) | **Pass.** The segments carry command names and state, so they are navigation with information, not decorative chips. Each is a real button that jumps. |
| Bare copy icons | 21 (control affordance) | **Pass with a caveat checked.** Removing the chip removes a visual affordance boundary, so the bare variant was given an explicit `:focus-visible` ring and a 24px minimum hit area rather than inheriting whatever the borderless default gave it. |

## Regressions checked for and not found

- No `background-clip: text` gradient reappeared.
- No equal-width card grid was introduced by the comparison rework.
- No third terminal style; `.term--mini` and `.term--nht` are variants of one component.
- No new semantic hue: the amber/accent pairing reuses existing tokens.
- Reduced motion still renders a complete static equivalent on all four pages.

## Consciously kept, unchanged from v4.2.2

The constellation canvas and the Home loop strip's pill shape, both with their reasons recorded above.
