# Hallmark Audit: v4.4.0 Guide Depth and Training Rebuild

**Date**: 2026-08-31
**Scope**: the v4.4.0 platform rail, five new Foundations lessons, playable Asteroids surface, cumulative file explorer, and cross-page navigation in `guides/website/nexus-hub-guide.html`.
**Method**: the anti-slop gates in `catalog/skills/developer-experience/hallmark-design/SKILL.md`, applied to the final HTML and the 32 Phase 6 rendered captures. The [v4.2 audit](../../../v4.2/development/guide-rebuild/hallmark-audit.md) is a historical baseline and was not modified.
**Verdict**: PASS. No new hallmark blocker remains.

## New and Rebuilt Surfaces

| Surface | Gate risk | Verdict |
|---|---|---|
| Home identity and platform rail | 1, dead-centered hero; 2, equal card grid; 20, pill row | **Pass with one conscious retention.** The product mark and one-line outcome remain centered because this is the identity lockup requested for Home, but the rest of the page returns to left-aligned reading and a clear install-first sequence. The platform rail is an unboxed compatibility list between two rules, not six equal cards or six decorative pills. Marks use official SVG geometry where approved; three text treatments remain under DF-1 rather than fabricated logos. |
| Five new Foundations lessons | 2, repeated cards; 22, card as default container; 25, decorative animation | **Pass.** Model, token, agent-platform, chatbot-versus-agent, and practice lessons each use a different mechanism-specific diagram. They do not repeat one card template. Motion explains flow or state, runs only while visible, and becomes a complete static result under reduced motion. |
| Foundations eight-scene sequence | 5, competing bands; 6, uniform rhythm | **Pass.** Scenes share typography and rules but vary composition, density, and diagram geometry. A single mental-model close gives the sequence an intentional ending instead of eight equal feature bands. |
| Asteroids game chrome | 20, pill decoration; 22, card as default container; 25, decorative animation | **Pass.** Score, lives, state, controls, seeded-defect cue, and actions are functional game instrumentation. Animation is the behavior being taught, pauses offscreen or hidden, clamps frame delta, and exposes a static one-step path under reduced motion. |
| Training terminal and evidence panels | 2, dashboard card grid; 22, card as default container | **Pass.** The terminal reuses the guide's established terminal language. Artifact and gate panels separate two different outputs; they are not a generic marketing grid. Their hierarchy is subordinate to the runnable command. |
| Cumulative file explorer | 22, card as default container; 26, fake click target | **Pass.** The two-pane tree and file view reproduce a real work surface and accumulate command artifacts. Tree items are native buttons with selected state, visible focus, directional navigation, and text-only safe rendering. |
| Cross-page progress | 20, decorative dots; 26, fake click target | **Fixed.** The initial `<i data-go>` dots accepted pointer clicks but were absent from the keyboard and accessibility tree. They are now labelled anchors with real `href` values, `aria-current="page"`, 24 x 24 px targets, and active and inactive visual-dot contrast of at least 3:1 in both themes. |
| Home install tabs | 26, fake click target; accessibility relationships | **Fixed.** Native tab roles use roving keyboard selection plus stable `aria-controls` and reciprocal `aria-labelledby` relationships. The inactive panel is natively hidden, so only the selected installation path is exposed. |
| Disabled page ends | accessibility and visual hierarchy | **Fixed.** Whole-component opacity made the labels fail contrast in both themes. Full-opacity faint-ink tokens and a transparent background now communicate disabled state without making the words unreadable. |

## Consciously Kept

1. **Centered Home identity lockup.** Gate 1 normally rejects a dead-centered hero stack. Here the centered region is limited to the product mark, outcome, compatibility rail, and three explicitly ranked destinations. Installation and every explanatory section return to the shared left-aligned reading structure. The composition is a deliberate identity exception, not the default page template.
2. **Dark-theme constellation.** It remains the product's established visual identity. It is behind content, receives no input, stops when hidden or in light theme, remains pixel-static under reduced motion, and now has no reduced-motion opacity transition.
3. **Panel boundaries inside Training.** The game, terminal, artifact verdict, and explorer remain bordered because each is an operational surface with its own interaction or output contract. Removing those boundaries would merge unrelated states and reduce comprehension; this is functional grouping, not card decoration.
4. **Semantic status chips.** The seeded bug, fixed state, file status, and gate result retain compact badges because their color and text communicate runtime state. No chip is used as decorative proof or a substitute for prose.

## Regressions Checked and Not Found

- No gradient headline or `background-clip: text` returned.
- No equal-width marketing card grid was introduced.
- No third terminal style was invented.
- No icon-only control lacks a programmatic name and visible focus.
- No pointer-only navigation action remains.
- No generated pseudo-text or visible control state falls below its applicable contrast threshold.
- No continuous motion survives the reduced-motion preference.
- No new marketing superlative or generic feature-card cadence was introduced.
- No reader-facing download dependency returned.

## Remaining Non-Blocking Item

DF-1 remains explicit: ChatGPT, Gemini, and GitHub Copilot use restrained text treatments until approved standalone vendor geometry is available. The audit rejects inventing substitute marks merely to make the rail visually uniform.
