---
name: hallmark-design
description: Generate and audit human-facing UI that does not look AI-generated, using anti-slop gates and four verbs (build / audit / redesign / study) - adapted from Hallmark with the multi-theme catalog deliberately excluded
summary_l0: "Produce and audit UI that avoids the 'AI-generated' look using anti-slop gates"
overview_l1: "This skill instructs the agent to design, audit, and redesign human-facing UI so it does not exhibit the generic 'AI slop' signature (centered hero, gradient buttons, evenly-spaced everything, emoji bullets, lorem-ipsum rhythm). It carries a catalog of anti-pattern gates spanning layout, color, typography, spacing, components, motion, and content, plus four verbs: build generates UI that passes the gates from the start; audit reviews existing markup and reports gate violations; redesign rewrites existing UI to clear the gates; study extracts design principles from a reference the user supplies. Use it whenever the Coding pillar renders human-facing surfaces (review diffs, dashboards, the session replay timeline, generated component previews). It is adapted from Hallmark but deliberately drops the 22-theme catalog because Nexus is a single product with one shell theme. Compose it with the html-output-conventions skill, which decides when an artifact should be HTML at all."
version: 1.0.0
author: Benjamin Dourthe
license: MIT
attribution: "Adapted from Hallmark (https://github.com/Nutlope/hallmark), MIT-licensed, by Together AI. Anti-slop gates and the four-verb model are derived from Hallmark; the 22-theme catalog is intentionally excluded."
category: developer-experience
language: Multi-language
tags: [ui, design, anti-slop, css, html, accessibility, audit, redesign, frontend]
tools_required: [Read, Write, Edit]
---

# Hallmark Design (anti-slop gates)

Generate, audit, and redesign human-facing UI so it does not look AI-generated. The most common failure mode of agent-produced interfaces is a recognizable "slop" signature: a centered hero with a gradient call-to-action, three feature cards of identical width, emoji bullets, uniform spacing with no rhythm, and a purple-to-blue gradient somewhere. This skill codifies the antidote as a catalog of anti-pattern gates plus four verbs the agent can invoke.

This skill is adapted from Hallmark (https://github.com/Nutlope/hallmark), MIT-licensed, by Together AI. The anti-slop gate list and the four-verb model come from Hallmark; the upstream project's 22-theme catalog is deliberately excluded (see "Scope excluded" below).

## When to Use This Skill

Use this skill when:

- The Coding pillar is generating a human-facing surface: a review diff display, a dashboard, the session replay timeline, an operator-actions panel, or a preview of a generated component.
- The user asks to review existing UI for quality ("does this look generic?", "audit this page") -> use the `audit` verb.
- The user asks to improve existing UI without changing its function ("make this not look AI-generated", "redesign this") -> use the `redesign` verb.
- The user points at a reference design and wants its principles extracted ("study this and tell me what makes it work") -> use the `study` verb.

**When NOT to use**:

- For the component contract / prop-and-variant generation problem, use `ui-component-generation` first, then run this skill's `audit` verb over the result.
- For multi-component architecture, routing, and page-level state, use `frontend-ui-engineering`.
- For the decision of whether an artifact should be HTML at all (versus Markdown), use `html-output-conventions`.
- For WCAG requirements (names, keyboard, focus visibility, reduced-motion *musts*, contrast *severity*): `accessibility-engineering`. This skill may still fail a build that looks generic.
- For spatial structure: `layout-and-spacing`. For type loading and truncation: `web-typography`. For palette construction: `color-systems`. For in-product wording: `interface-copy`.
- For a holistic review across those domains: `interface-review`.

## The Four Verbs

The skill is invoked with one of four verbs. The default (no verb) is `build`.

| Verb | Intent | Output |
|---|---|---|
| `build` (default) | Generate new UI that passes every anti-slop gate from the start. | New markup / styles plus a gate-pass checklist. |
| `audit` | Review existing UI against the gates without changing it. | A severity-ranked findings table: each violated gate, where it occurs, and why it reads as generic. |
| `redesign` | Rewrite existing UI to clear the gates while preserving function and content. | A diff plus a before/after note for each gate that was failing. |
| `study` | Extract the design principles from a reference the user supplies. | A principles brief (layout system, type scale, color logic, spacing rhythm) the agent can reuse on later `build` calls. |

`audit` must be invokable from the Coding pillar over any rendered surface: pass it the HTML/JSX and it returns the findings table without mutating the source.

## Anti-Slop Gate Catalog

Every `build` output must pass these gates; `audit` reports each one it fails; `redesign` clears them. Gates are grouped by concern.

### Layout

1. No dead-centered hero with a single centered headline + subhead + centered button stack as the entire above-the-fold.
2. No row of three (or four) identical-width feature cards as the primary content block.
3. Asymmetry is allowed and encouraged: not every section is center-aligned; left-aligned text blocks are the default for reading.
4. Use a real layout system (grid with intentional column spans), not a stack of full-width centered `<div>`s.
5. Content has a clear focal hierarchy; not every element competes for equal attention.
6. Whitespace is intentional and uneven, following content grouping, not a uniform gap applied everywhere.

### Color

7. No unmotivated gradient (especially purple-to-blue / indigo-to-violet) on buttons, headings, or backgrounds.
8. A constrained palette: one or two accent colors with a neutral base, not a rainbow of semantic colors.
9. Accent color is used sparingly for emphasis, not painted across every interactive element.
10. Sufficient contrast: unreadable text is a slop fail *and* an accessibility fail. `accessibility-engineering` decides when contrast is required and how severe a miss is; `color-systems` measures the rendered pair. Do not keep a second severity table here.
11. No pure-black (#000) text on pure-white (#fff) for long-form body copy; use a softened near-black on an off-white when the design calls for reduced glare.

### Typography

12. A real type scale (modular, e.g. 1.2-1.333 ratio), not three arbitrary font sizes.
13. Line length for body copy stays in the 45-85 character measure; full-viewport-width paragraphs are a violation.
14. Line height is set deliberately (1.4-1.6 for body); default browser leading on dense text is a smell.
15. No more than two typeface families; weights carry hierarchy instead.
16. Headings do not all use the same size + weight; the hierarchy is visible at a glance.

### Spacing and rhythm

17. Spacing follows a scale (e.g. 4/8px base), not arbitrary pixel values.
18. Vertical rhythm groups related elements tighter and separates unrelated ones; uniform margins everywhere is a smell.
19. Padding inside interactive elements is proportionate to their text, not a fixed value pasted onto every button.

### Components

20. Buttons look pressable and distinct by role (primary vs secondary vs destructive); not every button is the same pill.
21. Form inputs have visible labels (not placeholder-as-label), visible focus states, and real error affordances.
22. Cards have a reason to be cards (grouping), not a default container for every paragraph.
23. Icons, when used, are consistent in stroke weight and size; mixed icon sets are a smell.
24. No emoji used as bullet points or section markers in a professional surface.

### Motion and interaction

25. Motion is purposeful (state transitions, focus), not decorative entrance animations on every element.
26. Hover and focus states exist and are distinct; focus is never removed without a visible replacement.
27. Reduced-motion preference (`prefers-reduced-motion`) is honored as a **requirement** owned by `accessibility-engineering`. Optional durations, easing, and transforms in the recipe layer apply only after that requirement is met.

### Content

28. No lorem-ipsum-rhythm filler: copy is specific to the actual content, not generic marketing cadence.
29. Microcopy is concrete ("Save changes", "Delete 3 files") rather than vague ("Submit", "Click here").
30. No redundant restating of the same idea in headline, subhead, and body.

(The catalog above is the working subset most relevant to Nexus's Coding-pillar surfaces; Hallmark's full upstream gate list runs to 65+ entries. Extend this catalog as new generic-looking patterns are observed in practice, recording each new gate with a one-line rationale.)

## Recipe layer (values after judgment)

The gates above are **judgment**: they decide whether an effect belongs. Once it does, use a recipe so the value is not the browser default or a one-off guess.

| Topic | File |
|---|---|
| Surfaces, elevation, hairline borders | `references/surfaces-and-elevation.md` |
| Radius scale, icon stroke, optical size | `references/radius-and-icons.md` |
| Durations, easing, deliberate transforms | `references/motion-recipes.md` |

Short defaults when the project has no tokens yet:

- Elevation: page is flat; a justified card may use `0 1px 2px rgb(0 0 0 / 0.06), 0 8px 24px rgb(0 0 0 / 0.08)`; overlays add a `rgb(0 0 0 / 0.4)` scrim.
- Radius: 6px controls, 10px cards, 16px sheets, pill only for chips and avatars. Nested inner radius = outer minus padding.
- Icons: one stroke (1.5px or 2px at 24px optical size); 16px inline, 20-24px in buttons.
- Motion: 150ms color/opacity, 200ms press, ~300ms overlay enter; `cubic-bezier(0.2, 0, 0, 1)` enter, faster exit. Press may `translateY(1px)` or `scale(0.98)`. No scroll-triggered bounce on every card.

If the project already publishes `--shadow-*`, `--radius-*`, or motion tokens, use those names. The recipe is a fallback, not a second design system.

## Instructions

### build (default)

1. Confirm the surface and its content (what is being displayed, to whom, and where it renders).
2. Choose a layout system appropriate to the content (grid spans, reading column for text, asymmetry where it aids hierarchy).
3. Generate the markup and styles.
4. Run the gate catalog over your own output before returning; fix any failures.
5. Return the markup plus a short gate-pass checklist noting any gate that required a deliberate trade-off.

### audit

1. Read the supplied markup (HTML / JSX / component source). Do not mutate it.
2. Walk the gate catalog. For each violated gate, record: gate number + name, the element / selector where it occurs, severity (high = the surface reads as generic at a glance; medium = a noticeable smell; low = a refinement), and a one-line "why it reads as generic".
3. Return a severity-ranked findings table. End with a one-line verdict (does the surface read as AI-generated, yes/no, and the top three fixes).

### redesign

1. Run `audit` internally to get the failing gates.
2. Rewrite the markup and styles to clear each failing gate, preserving function, content, and accessibility.
3. Return a diff. For each gate that was failing, add a before/after note so the change is reviewable.

### study

1. Read the reference the user supplies (URL content the user pasted, a screenshot description, or source).
2. Extract: the layout system, the type scale, the color logic, the spacing rhythm, and the one or two moves that make it feel designed rather than defaulted.
3. Return a principles brief the agent can reuse on later `build` calls.

## Scope Excluded

- **Hallmark's 22-theme catalog is intentionally NOT imported.** Nexus is a single product with one shell theme (Tauri + React 19 + Tailwind v4). Theme variation is irrelevant inside the app, so the multi-theme selector, theme tokens, and per-theme reference files from upstream Hallmark are out of scope. This exclusion is recorded in the v1.2.0 adoption comparison (Section 9.4, item N6). Do not reintroduce a theme catalog via scope creep.
- This skill governs design quality, not component contracts (`ui-component-generation`), page architecture (`frontend-ui-engineering`), or the HTML-vs-Markdown artifact decision (`html-output-conventions`).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Centered hero with a gradient button is the standard landing pattern." | It is the standard AI-generated pattern. Real product surfaces inside Nexus are tools, not landing pages; left-aligned, hierarchy-driven layouts read as designed. |
| "Three feature cards is just clean." | Three identical-width cards is the single most recognizable slop tell. If the content is genuinely three peers, vary their emphasis or use a different grouping. |
| "Emoji bullets make it friendly." | In a developer tool they read as generated. Use real list markup with restrained styling. |
| "We need all 22 themes for flexibility." | Nexus has one shell theme. Themes are upstream Hallmark scope that does not apply here; see Scope Excluded. |
| "I already picked colors; motion can stay the CSS default." | Default `ease` over 400ms on every property is the generic look. If motion belongs (gate 25), use the recipe durations; if it does not, use none. |

## Verification

- [ ] The chosen verb was applied (build / audit / redesign / study) and its output shape matches the table above.
- [ ] For `build` and `redesign`: every gate in the catalog passes, or any deliberate exception is noted with a rationale.
- [ ] For `audit`: the findings table is severity-ranked and ends with a verdict; the source was not mutated.
- [ ] Accessibility gates (11, 21, 26) plus the handoffs on 10 and 27 are satisfied, not traded away for aesthetics. Contrast severity stays with `accessibility-engineering`; reduced-motion requirements stay there too.
- [ ] Recipe-layer values (elevation, radius, icon stroke, motion) were taken from the project's tokens or from the defaults in `references/`, not invented per component.
- [ ] No theme-catalog artifact was introduced (Scope Excluded honored).
- [ ] Attribution to Hallmark + Together AI is preserved in this skill's front matter.

## Related Skills

- [[html-output-conventions]] -- decides when a surface should be HTML at all; compose with this skill so the artifact is both well-chosen and well-designed.
- [[ui-component-generation]] -- generate the component contract first, then audit the result here.
- [[frontend-ui-engineering]] -- page-level architecture, state, and accessibility.
- [[creative-generation]] -- design direction and ideation when the brief is open-ended.
- `accessibility-engineering` -- reduced-motion *requirements*, names, keyboard, contrast *severity*
- `layout-and-spacing` -- grouping and breakpoints; this skill owns whether the grouping looks generic
- `web-typography` -- loading, measure, truncation
- `color-systems` -- OKLCH palettes and measured pairs
- `interface-copy` -- source strings
- `interface-review` -- coordinating review that may load this skill as the polish delegate
