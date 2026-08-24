# Spacing and Sizing

## Scale

If tokens exist, use them (`text-sm`, `--font-size-body`). If not, pick a ratio and a body size and stick to them for the files you touch:

- Body: `1rem` (project root; do not assume 16px if `html` is set otherwise)
- Small / caption: about 0.875rem
- H3: about 1.25rem
- H2: about 1.563rem
- H1: about 1.953rem

These assume a 1.25 ratio. Escape: a marketing display may jump to 2.5rem+; isolate it to that band so the product UI scale stays intact.

Name the roles in comments or tokens (`--text-body`), not in magic numbers scattered across components.

## Heading visual hierarchy

Each rank should be distinguishable by size, weight, or both. Two consecutive ranks that are the same size and weight fail this skill even if the elements are correct `h2`/`h3`. Do not skip a rank in the DOM to get a size (`accessibility-engineering`).

## Line-height by role

| Role | Line-height | Escape |
|---|---|---|
| Body / article | 1.5-1.6 | Very large display body (over ~24px) may go to 1.4 |
| UI compact (tables, menus) | 1.25-1.4 | Must still fit hit areas |
| Display heading | 1.1-1.25 | Single-line hero may use 1.05 |
| Button label | 1-1.25 | Padding on the control carries the rest |

Unitless line-height is required so nested font sizes scale. `line-height: 24px` on body is a fail.

## Letter-spacing by size

| Role | Tracking |
|---|---|
| Body | 0 |
| Small caps / all-caps UI labels | 0.04-0.08em |
| Large display (roughly 2rem+) | 0-0.04em if the face looks tight |
| Tiny legal copy | 0; do not spread it to "look designed" |

`letter-spacing` on `input` can break password managers' overlay alignment; leave inputs at 0 unless the design system already sets it.

## Measure

Target 45-75 characters for reading columns. `max-width: 65ch` on the prose container is the default recipe. `ch` is the width of the face's zero; it is good enough for this limit.

Full-bleed paragraphs, or `width: 100%` text next to no constraint, fail. Escape: dashboards with many short labels; code; tables (those may scroll).
