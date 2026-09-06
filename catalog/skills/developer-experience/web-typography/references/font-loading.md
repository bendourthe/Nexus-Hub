# Font Loading

## Formats

Ship `woff2` as the only modern format unless the project already includes `woff` for an explicitly supported old browser. Do not add TTF/OTF to the `@font-face` `src` for production UI; those are source files.

Self-host when the project already self-hosts. Do not introduce a new font CDN in a codebase that has none (privacy, availability, and CSP). If a CDN is already there, do not rip it out in a typography-only pass unless the user asked.

## `@font-face` skeleton

```css
@font-face {
  font-family: "Source Sans";
  src: url("/fonts/source-sans.woff2") format("woff2");
  font-weight: 400 700; /* variable */
  font-style: normal;
  font-display: swap;
  size-adjust: 100%;
}
```

`size-adjust`, `ascent-override`, `descent-override`, and `line-gap-override` exist to match fallback metrics so swap does not shove the layout. Measure fallback vs web font; adjust `size-adjust` until the body line box is close. If the project has no time to measure, skip the overrides rather than guessing.

## `font-display`

| Value | Use |
|---|---|
| `swap` | Default for UI and body. Text is readable immediately. |
| `optional` | Decorative display face; may never appear on slow links. |
| `fallback` | Short block then swap; rarely better than `swap` for UI. |
| `block` | Avoid for product UI. Invisible text is a functional outage. |
| `auto` | UA choice; do not rely on it for a known policy. |

## Preload

Preload at most the one body face used on first paint (`<link rel="preload" as="font" type="font/woff2" crossorigin>`). Preloading every weight fights the reason you subsetted.

## Fallback stack

Always name a generic family last (`sans-serif`, `serif`, `monospace`). Put a metric-similar system face before it (`ui-sans-serif`, `system-ui`) so swap is less jumpy.
