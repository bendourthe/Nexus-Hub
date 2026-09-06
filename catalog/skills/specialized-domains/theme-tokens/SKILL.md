---
name: theme-tokens
description: "Apply curated visual themes (palette + typography + spacing + radius + shadow tokens) to slide decks, Word docs, PDFs, web artifacts, and any other generated visual artifact - via 10 generic curated theme JSON files OR a user-supplied custom theme. Use whenever the user asks for \"a theme\", \"a palette\", \"fonts that go together\", \"make this look <adjective> (editorial / brutalist / corporate / mid-century / cyber / etc.)\", \"set up theming\", \"tokenize the look\", or wants consistent styling across multiple generated artifacts. Pairs with pptx-generation, docx-generation, pdf-document-generation, web-artifacts-builder, and brand-styling. SKIP: one-off styling decisions inside a single file (just inline the colors), CSS-only refactors of existing apps (no JSON intermediation needed), and brand-applied work where the user already has tokens (use brand-styling directly with their tokens)."
summary_l0: "Apply curated theme tokens (palette, fonts, spacing) to slides, docs, PDFs, and web artifacts"
overview_l1: "This skill provides 10 generic curated themes plus a token schema so generators (pptx-generation, docx-generation, pdf-document-generation, web-artifacts-builder) consume a single JSON contract instead of inlining colors and font choices. Each theme bundles a palette (primary, secondary, accent, background, foreground, muted), a font triple (heading, body, mono), spacing base + scale, radius, and shadow. The 10 themes span editorial-serif, brutalist-sans, pastel-soft, terminal-mono, corporate-slate, sunset-warm, forest-cool, mid-century-modern, neon-cyber, and newsprint-mono - chosen to cover the range of common asks without overlap. Custom themes follow the same schema. Trigger phrases: theme, palette, color scheme, theming tokens, design tokens, typography pairing, brand-neutral theme, editorial theme, brutalist theme, mid-century theme, cyber theme, newsprint theme, consistent styling, tokenize the look, set up theming."
---

# Theme Tokens

Curated visual themes for generated artifacts. Ten generic theme JSON files plus a stable token schema mean every downstream generator (pptx, docx, pdf, web-artifacts) consumes the same contract instead of each one inlining its own color and font choices. The contract also makes it cheap for the user to drop in a custom theme that matches their brand.

## When to Use This Skill

Use this skill when:

- A slide deck, document, PDF, or web artifact needs a coherent visual identity that is more than ad-hoc choices
- The user names an aesthetic ("editorial", "brutalist", "mid-century", "cyber", "newsprint", "corporate", "warm", "cool") and expects palette + type + spacing to match
- Multiple generated artifacts must share a consistent look (deck + doc + PDF + web preview, all from the same theme)
- The user wants "a palette" or "fonts that go together" without committing to a full brand system
- A downstream generator needs a token JSON to consume rather than free-text styling instructions

**Trigger phrases**: "theme", "palette", "color scheme", "theming tokens", "design tokens", "typography pairing", "fonts that go together", "make this look editorial / brutalist / corporate / mid-century / cyber", "consistent styling across the deck and the doc", "tokenize the look", "set up theming for the project".

**When NOT to use**:

- One-off styling decisions inside a single file (just inline two or three colors; do not introduce a JSON layer)
- CSS / SCSS refactors of an existing app (the app already has a tokenization pattern; use it)
- Brand-applied work where the user already has brand tokens (use `specialized-domains/brand-styling` directly with their tokens; do not re-pick generic ones)
- A request for "just any nice colors" with no aesthetic hint (push back: ask the user which of the 10 themes is closest, or whether they have brand tokens)
- Vendor-specific palettes (Anthropic colors, Google colors, etc.) - those are explicitly out of scope for this skill; the 10 bundled themes are deliberately brand-neutral

If the user has a brand, route through `brand-styling` instead. This skill exists for the case where there is no brand yet (or no brand applies).

## Token Schema

Every theme is a single JSON file matching this schema. Downstream generators read this schema and map the tokens to whatever the underlying engine expects (python-pptx, python-docx, ReportLab, Tailwind CSS variables, raw CSS custom properties, etc.).

```json
{
  "name": "<theme-slug>",
  "label": "<human-readable label>",
  "description": "<one-sentence aesthetic statement>",
  "palette": {
    "primary": "#hex",
    "secondary": "#hex",
    "accent": "#hex",
    "background": "#hex",
    "foreground": "#hex",
    "muted": "#hex"
  },
  "fonts": {
    "heading": "<CSS font stack>",
    "body": "<CSS font stack>",
    "mono": "<CSS font stack>"
  },
  "spacing": {
    "base": <number, px>,
    "scale": [<multipliers>]
  },
  "radius": <number, px>,
  "shadow": "<CSS shadow value or 'none'>"
}
```

Notes on the contract:

1. **Six palette slots**, no more. `primary` and `secondary` carry the heading / lead color; `accent` is the call-to-action / chart highlight; `background` and `foreground` are the page; `muted` is the secondary text or chart ink. More slots invite drift; fewer cannot express an accent.
2. **Three font slots**. `heading` and `body` are the readable pair; `mono` is for code, tables, or any deliberate monospace block. Generators that need only one font collapse heading and body to the same value internally.
3. **Spacing is base + scale**, not 64 hardcoded values. Generators compute concrete spacing as `base * scale[i]`. Default scale is `[0.5, 1, 1.5, 2, 3, 4, 6, 8]`, but each theme picks a scale that fits its density character.
4. **Radius is one number**. Themes either commit to a corner (e.g., 0 for brutalist, 12 for soft pastel) or stay neutral (4-6 px). Per-component radii live in the generator, not in the theme.
5. **Shadow is one value or 'none'**. Brutalist and editorial themes use `none`. Pastel and corporate themes use a soft shadow. Cyber uses a glow.

Custom themes drop into the same `themes/` folder using the same schema. The schema is the contract; the bundled 10 are convenience.

## The 10 Bundled Themes

Each theme ships as `themes/<slug>.json` under this skill directory. The list spans common asks without overlap:

| Slug | Aesthetic statement | Best for |
|---|---|---|
| `editorial-serif` | Long-form magazine layout; serif heading paired with high-contrast body. | Whitepapers, long technical writeups, design-doc PDFs. |
| `brutalist-sans` | Heavy sans, hard corners (radius 0), no shadow, deliberate over-borders. | Manifestos, statement decks, opinion pieces. |
| `pastel-soft` | Low-contrast pastel palette, generous radius, soft shadow. | Wellness, education, kid-facing material, friendly internal docs. |
| `terminal-mono` | All-mono triple, dark background, cyan accent. | Engineering walk-throughs, terminal-flavored content, code-heavy slides. |
| `corporate-slate` | Cool grays, navy primary, restrained accent. | Quarterly reviews, board decks, formal compliance docs. |
| `sunset-warm` | Warm primaries (terracotta, amber), serif heading, cream background. | Storytelling decks, retros, creative-team material. |
| `forest-cool` | Deep green primary, sage accent, parchment background. | Sustainability, nature-adjacent, slow-living content. |
| `mid-century-modern` | Mustard + teal + cream, geometric sans, gentle radius. | Brand-neutral presentations with retro aesthetic. |
| `neon-cyber` | Black background, neon magenta + electric cyan, glow shadow, mono body. | Cyberpunk decks, hacker-aesthetic landing pages, demo-day visuals. |
| `newsprint-mono` | Cream background, ink-black ink, two weights of serif, no accent. | Op-ed style writeups, FAQs, single-column newsletter PDFs. |

The 10 are deliberate generic precedents. Do not extend the bundled list inside this skill - new themes go into `~/.nexus-hub/brand/<name>/tokens.json` (via `specialized-domains/brand-styling`) so user-specific themes do not pollute the curated set.

## Instructions

1. **Pick or ask**. If the user names an aesthetic that maps to one of the 10 slugs, use that file directly. If the aesthetic is unclear, batch a single question: "Which of these 10 is closest, or do you have brand tokens I should use instead?" Show the table. Pick once; iterate later if needed.
2. **Load the theme JSON**. Read the bundled file from `~/.nexus-hub/skills/specialized-domains/theme-tokens/themes/<slug>.json` (post-installer location) or from `catalog/skills/specialized-domains/theme-tokens/themes/<slug>.json` (in-repo location).
3. **Map to the downstream generator**:

    | Generator | Mapping |
    |---|---|
    | `pptx-generation` | Map `palette.primary` to title accent, `secondary` to subtitle, `accent` to CTA / chart highlight, `background` to slide background, `foreground` to body text, `muted` to footer / page number. Set `fonts.heading` for title placeholders, `fonts.body` for content placeholders. Use `spacing.base * scale[1]` (one step) as the default left/right margin. |
    | `docx-generation` | Map `palette.foreground` to default text color, `primary` to H1, `secondary` to H2, `muted` to caption / footnote, `accent` to hyperlink and emphasis. Set `fonts.heading` and `fonts.body` per Word style; map `fonts.mono` to a Code style. |
    | `pdf-document-generation` | Map palette and fonts to a ReportLab `ParagraphStyle` set, OR write a CSS file consumed by an HTML-to-PDF engine (WeasyPrint, Playwright). `radius` maps to `border-radius`; `shadow` maps to `box-shadow`. |
    | `web-artifacts-builder` | Emit the theme as CSS custom properties in `:root` (`--color-primary`, `--font-heading`, `--space-1`, etc.). Tailwind v4 users add to `theme` via `@theme { ... }` in `app.css`. |
    | `generative-art` | Pass `palette.primary` and `accent` to the manifesto's Color section as the starting palette; the philosophy step may then narrow or widen it. |

4. **Honor the spacing scale**. Compute concrete values as `base * scale[i]`; do not hardcode "8px" or "24px" in generator templates.
5. **Do not extend palette / font slots**. If a downstream generator needs a fourth color (highlight, danger, success), derive it from the existing six (e.g., `accent` desaturated 30% for hover state) rather than adding a slot. Slot drift breaks every downstream generator simultaneously.
6. **For user-supplied themes**, validate against the schema before consuming. A missing `palette.muted` should fall back to `foreground` at 60% opacity, not crash the generator.

## Composition Strategies

When a theme override layers on top of a base theme (a brand tweak over a bundled theme, or a per-artifact adjustment over a project theme), four strategies say how the override token set combines with the base. They are a layering vocabulary that avoids forking a whole theme to change a few tokens (the copy that drifts):

- **`replace`** (default) -- the override theme fully replaces the base; downstream generators read only the override. Example: a brand-new bundled theme substituted for the current one.
- **`prepend`** -- the override resolves before the base, so any slot the override defines wins and the base fills the rest. Example: override just `palette.accent` while inheriting every other slot from `corporate-slate`.
- **`append`** -- the base resolves first and the override fills only slots the base left unset. Example: supply a missing `shadow` or `radius` on top of a partial base without disturbing its palette.
- **`wrap`** -- the override is a frame containing a `{CORE_TEMPLATE}` placeholder replaced with the base token object, so the override can add tokens around an embedded base. Example: bolt project-specific extension tokens onto a curated theme in one file.

```json
// brand override, prepend strategy: win on accent, inherit the rest of corporate-slate
{ "extends": "corporate-slate", "strategy": "prepend", "palette": { "accent": "#ff5722" } }
```

Prefer `replace` for a genuinely new look; use `prepend` / `append` / `wrap` to retune a few tokens of a bundled theme without copying all of it. Brand overrides still route through [[brand-styling]]; this vocabulary describes how that override layers onto the base.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just inline the colors in the deck - no need for a theme file" | Inlined colors are fine for one slide. Two artifacts in, you have inconsistencies (deck navy vs doc navy that are 2 hex digits apart). The theme file is 30 lines and locks the look once. |
| "I'll add a fourth font for emphasis / decorative use" | Three is the cap. A fourth font triggers font-loading cost on the web, fights for visual hierarchy, and 90% of the time gets used in one location. Use weight + size variation on the existing three instead. |
| "The 10 themes don't quite match - I'll create theme number 11 in this skill" | The bundled 10 are curated and deliberately do not grow inside the skill. Theme 11 is either the user's brand (route through brand-styling) or a one-off (just inline colors for the one artifact). |
| "I'll add slots like `success`, `warning`, `danger` to support UI components" | Out of scope. This skill is for visual identity, not semantic component states. UI component skills derive semantic colors from accent / muted plus a fixed semantic ramp; do not pollute the theme schema. |
| "Spacing as base + scale is overkill - I'll just hardcode 8px / 16px / 24px" | Themes have different density characters (newsprint-mono uses base 6, neon-cyber uses base 10). Hardcoded values mean spacing fights the type. The base + scale formula is two extra lines of code in any generator. |
| "I'll copy a vendor's color palette as one of the bundled themes (Tailwind, Anthropic, Material)" | Vendor palettes belong in the vendor's brand, not in a generic curated set. Brand-neutral framing is mandatory: every bundled theme is named for its aesthetic, not its source. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] Exactly 10 theme JSON files exist under `themes/` matching the slugs in the table above.
- [ ] Each theme JSON parses (`python -c "import json; [json.load(open(f)) for f in glob.glob('themes/*.json')]"` returns no error).
- [ ] Each theme has all six palette slots, all three font slots, `spacing.base`, `spacing.scale`, `radius`, `shadow`. Missing keys fail validation.
- [ ] Each theme's hex colors are valid `#rrggbb` (regex `^#[0-9a-fA-F]{6}$`); no shorthand, no named colors.
- [ ] No vendor names appear in any theme file or label (`git grep -i 'anthropic\|tailwind\|material' themes/` returns no hits in this skill folder).
- [ ] When a downstream generator consumes a theme, the resulting artifact uses the exact palette and font values - no silent overrides.
- [ ] User-supplied custom theme files validate against the same schema before consumption (missing keys raise a clear error, not a silent fallback that masks the problem).

"The output looks themed" is not a valid verification criterion. The verification is: do all 10 themes parse, are the slots filled, and does the generator round-trip the values without overriding them?

## Bundled Resources

The 10 curated themes ship under `themes/` as JSON files. Each is a self-contained theme; downstream generators consume them by file path.

- `themes/editorial-serif.json`
- `themes/brutalist-sans.json`
- `themes/pastel-soft.json`
- `themes/terminal-mono.json`
- `themes/corporate-slate.json`
- `themes/sunset-warm.json`
- `themes/forest-cool.json`
- `themes/mid-century-modern.json`
- `themes/neon-cyber.json`
- `themes/newsprint-mono.json`

User-supplied themes go under `~/.nexus-hub/brand/<name>/tokens.json` (via `specialized-domains/brand-styling`), not into this skill's `themes/` folder. The bundled set is closed.

## Related Skills

- [[brand-styling]] -- applies user-supplied brand tokens; this skill provides the schema, brand-styling provides the user-specific instances.
- [[pptx-generation]] -- one of the four primary downstream consumers; maps theme tokens to slide masters and placeholders.
- [[docx-generation]] -- downstream consumer for Word styles.
- [[pdf-document-generation]] -- downstream consumer for ReportLab `ParagraphStyle` or HTML-to-PDF CSS.
- [[web-artifacts-builder]] -- downstream consumer; emits theme as CSS custom properties or Tailwind v4 `@theme` block.
- [[generative-art]] -- reads `palette.primary` and `accent` as the starting palette for the philosophy manifesto's Color section.
