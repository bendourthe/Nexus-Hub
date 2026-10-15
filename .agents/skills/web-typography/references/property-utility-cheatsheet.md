# Property to Utility Cheat Sheet

Map the CSS this skill names to common utilities. Use the project's names when they differ. This is a lookup, not a requirement to adopt Tailwind.

| CSS | Tailwind-style utility (if the project uses it) |
|---|---|
| `font-display` (in `@font-face`) | not a utility; stays in CSS |
| `font-weight: 500` | `font-medium` |
| `font-stretch: condensed` | no guaranteed utility; use CSS |
| `font-variant-numeric: tabular-nums` | `tabular-nums` |
| `font-kerning: none` | rare; use CSS |
| `line-height: 1.5` | `leading-normal` / `leading-6` (check the mapping) |
| `letter-spacing: 0.05em` | `tracking-wide` |
| `max-width: 65ch` | `max-w-prose` if configured to ~65ch |
| `overflow-wrap: anywhere` | `break-words` / `wrap-anywhere` (version-dependent) |
| `text-overflow: ellipsis` | `truncate` / `text-ellipsis` |
| `line-clamp: 2` | `line-clamp-2` |
| `text-wrap: pretty` | `text-pretty` |
| `text-wrap: balance` | `text-balance` |
| `hyphens: auto` | `hyphens-auto` |
| `dir="rtl"` | `rtl:` variant on the subtree, or HTML `dir` |

If the project is plain CSS or CSS Modules, write the properties. Do not add Tailwind to satisfy this table.
