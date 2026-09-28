# Hallmark audit (from markup) - nexus-hub-guide.html

**Date**: 2026-08-29
**Verb**: audit
**Scope**: current guide only. No redesign in this file.
**Method**: hallmark-from-markup against `catalog/skills/developer-experience/hallmark-design/SKILL.md` gates 1-30. Rendered confirmation is deferred (no browser).

Severity: High = first-contact or shell-level slop a workshop attendee sees in the first screenful. Medium = repeated pattern that Phase 2-3 must clear. Low = local, not blocking the shell.

## Findings

| Sev | Gate | Selector / block | Why it reads as generic |
|---|---|---|---|
| High | 1 | `.hero` (`#page-home .hero`) | Dead-centered hero: logo, gradient headline, lead, centered `.btn-row`, then pill stats. This is the entire above-the-fold. |
| High | 7 | `h1 .gtext`, `.brand .wordmark span`, `.btn--primary`, `.nav-links a.active` | Unmotivated cyan-to-teal gradient on the H1 (`background-clip: text`), the wordmark Hub, primary buttons, and active nav. `--grad` is a purple-adjacent blue-cyan-teal stripe used as the default accent. |
| High | 2 | `#page-home .grid.grid-4` (Consistency / Depth / Safety / Governance) | Row of four identical-width feature cards as a primary Home block. |
| High | 2 | `#page-home .card.navcard` (eight cells) | Equal card grid for Installation, Explore, Plan, Implement, Harden, Ship, Document, Reference. |
| High | 20 | `.hero .stat-row .stat` | Pill stats: 252 skills, 14 commands, 22 hooks, 23 agents, 6+ platforms. Rounded-full chips as the hero proof. |
| High | 25 | `.hero .mark-xl` `@keyframes float`; `.page` `@keyframes fadeUp`; `#constellation` loop | Decorative float on the hero mark, entrance fade on every page, continuous canvas animation on Home. Not a state transition. |
| High | 28, 30 | `h1` in `.hero`; `.ts-title.ts-h1` slide 1 | Marketing cadence: "autonomous team of world experts", Training cover "world-class expert team". Headline, lead, and later sections restate "catalog + installer + workflows". |
| Medium | 2 | `#page-home .grid.grid-2` "The difference" | Two equal comparison cards (Raw prompting vs Nexus-Hub) as the difference section. |
| Medium | 2 | `#page-setup .grid.grid-3.choice-cards` | Three identical OS cards (macOS / Windows / Linux). |
| Medium | 22 | `.card` globally | Card is the default container for paragraphs, stats, nav destinations, and feature claims. |
| Medium | 6 | `.section { padding: 54px 0 }` | Uniform vertical rhythm on every Home band. |
| Medium | 5 | Home from hero through "Get started" | Every band competes: stats, four benefits, two-column comparison, loop, three pillars, eight nav cards. No single focal action after the hero. |
| Medium | 11 | `:root` dark-only tokens; `body` background `#04141a` to `#02090c` | Dark is softened (not #000 on #fff). There is no light theme, so the portfolio light path cannot be audited yet. |
| Medium | 26 | `a[data-go]` without `href`; `.nav-links a` | Click targets are not real links. Focus-visible exists on `.copy-btn` but nav links rely on browser default and a hover background. Keyboard users can tab the brand (`tabindex="0"`) but hash links are not in the tab order as links. |
| Medium | 8 | `--violet`, `--red`, `--amber`, `--green`, `--cyan`, `--teal`, `--blue` | Wide semantic rainbow in tokens; comparison cards add per-card border colors. |
| Medium | 24 | none as bullets | No emoji bullets found. Pass. |
| Low | 12-16 | `h1` clamp 2.1-3.3rem; `h2` clamp 1.5-2.05rem; `h3` 1.18rem | A type scale exists. Hierarchy collapses where mock artifacts also use H1. |
| Low | 13 | `.lead { max-width: 100% }` | Hero lead is full container width (1120px), past a 45-85 character measure. |
| Low | 21 | theme / install controls | No theme control yet. Install copy buttons have labels after JS injects them; no-JS users still see the command text. |
| Low | 27 | `@media (prefers-reduced-motion: reduce)` | Durations are crushed to 0.001ms rather than a static equivalent. Constellation still paints. |

## Gates called out by the plan for the Phase 2 shell

Phase 2 acceptance names gates 1-6, 20, 22, 25-30 for the shell. Current shell failures against that set: 1, 2, 5, 6, 20, 22, 25, 26, 28, 30. Gate 3 (left-aligned reading) fails on `.hero { text-align: center }`. Gate 4 fails because Home is a stack of full-width centered sections, not an asymmetric field-guide grid.

## What this audit cannot prove

Without a browser: contrast ratios, actual focus rings, canvas frame rate, reduced-motion computed styles, and whether GitHub is the only network request at runtime. Those belong in Phase 7 human testing.
