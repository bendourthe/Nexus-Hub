# Hallmark re-audit (from markup) - Phase 7

**Date**: 2026-08-29
**Verb**: audit
**Scope**: `guides/website/nexus-hub-guide.html` after Phases 2-6 and dead `.nht` CSS removal.
**Method**: hallmark-from-markup against gates 1-30. Rendered confirmation is still deferred (no browser; DF-1).

Severity: High = first-contact or shell-level slop a workshop attendee sees in the first screenful.

## Findings

| Sev | Gate | Selector / block | Verdict |
|---|---|---|---|
| Closed | 1 | `.hero` | Left-aligned (`text-align: left`). Intro is a product sentence plus two short leads and three destination links, not a dead-centered marketing stack. Class name remains `.hero`. |
| Closed | 2 | Home grids | No `.grid-4` and no `.navcard` on Home. Comparison is a five-row table. Ribbon is six workflow nodes, not identical feature cards. |
| Closed | 20 | `.stat-row` | Absent from Home. No pill catalog counts. |
| Closed | 28, 30 | Home copy | No "autonomous team of world experts" / "world-class expert team". Headline states the experience-layer claim. |
| Closed | 7 (Home) | `.gtext` | Home does not use gradient-clipped H1. `.gtext` is `color: var(--accent)` on later workflow headings. |
| Closed | 25 (float) | `.mark-xl` | No `@keyframes float`. |
| Advisory | 25 | `#constellation` | Dark-mode canvas remains by plan contract. Reduced-motion must keep it static (JS). Rendered proof is DF-1. |
| Advisory | 10 | contrast | Not measurable without a browser. |

No open high-severity markup finding remains from the Phase 1 baseline table. Contrast, focus rings, canvas frame rate, and Lighthouse Accessibility stay in DF-1.
