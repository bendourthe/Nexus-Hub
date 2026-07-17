---
name: brand-styling
description: "Apply user-supplied brand tokens (palette, typography, logo, voice) to generated artifacts (slides, docs, PDFs, web artifacts) via a per-brand token JSON at ~/.nexus-hub/brand/<brand-name>/. Use whenever the user mentions \"our brand\", \"company colors\", \"brand guidelines\", \"brand kit\", \"house style\", \"match the brand\", \"use our typography\", \"apply our logo\", \"stay on-brand\", or wants generated artifacts (decks, reports, PDFs, web pages, internal comms) to reflect their organization's visual identity. ALWAYS ask the user for their brand tokens before picking colors or fonts; offer to scaffold an empty ~/.nexus-hub/brand/default/tokens.json if the user has no brand yet. SKIP: brand-neutral / agnostic artifacts (use theme-tokens directly with one of the 10 curated themes), one-off styling decisions inside a single file, vendor-specific brands the user does NOT own (this skill ships ZERO vendor assets - no Anthropic / OpenAI / Google / Tailwind / Material colors, fonts, or logos)."
summary_l0: "Apply user-supplied brand tokens (palette, fonts, logo) to generated artifacts via a per-brand token JSON"
overview_l1: "This skill applies the user's own brand tokens to any artifact a generator emits (pptx, docx, pdf, web). It extends the theme-tokens schema with brand-specific fields (logo, voice rules, asset paths) and stores each brand under ~/.nexus-hub/brand/<brand-name>/{tokens.json, fonts/, logo.{svg,png}}. The skill SHIPS WITH ZERO vendor-specific colors, fonts, or logos - the bundled template is empty placeholders, and the user MUST supply their own brand. If the user has no brand yet, the skill offers to scaffold an empty default brand at ~/.nexus-hub/brand/default/tokens.json for them to fill. Downstream consumers (pptx-generation, docx-generation, pdf-document-generation, web-artifacts-builder) read the brand JSON and map the tokens to whatever the underlying engine expects. Trigger phrases: brand, brand kit, brand guidelines, company colors, our brand, house style, match the brand, on-brand, brand tokens, apply our logo, our typography, brand consistency."
---

# Brand Styling

Apply the user's own brand tokens to generated artifacts. The skill is a TOKEN PATTERN, not a brand library: it ships with empty placeholders and explicitly NO vendor-specific palette, fonts, or logos. The user supplies their own brand under `~/.nexus-hub/brand/<brand-name>/`, and downstream generators consume the tokens through a single JSON contract.

## When to Use This Skill

Use this skill when:

- The user names their brand and wants generated artifacts (decks, docs, PDFs, web pages, internal comms) to reflect it
- The user has brand guidelines (PDF, web page, internal doc) that name colors, fonts, logo placement rules, and voice constraints
- Multiple generated artifacts must stay visually consistent under the same brand identity
- The user asks to "stay on-brand", "match the brand", "use our colors", "use our typography", or "apply our logo"
- An organization has brand assets the user wants to surface to the agent without re-pasting them every session

**Trigger phrases**: "our brand", "company colors", "brand guidelines", "brand kit", "house style", "match the brand", "use our typography", "apply our logo", "stay on-brand", "brand tokens", "brand consistency", "make it look like our brand", "use the company palette".

**When NOT to use**:

- Brand-neutral or agnostic artifacts (use `specialized-domains/theme-tokens` directly with one of the 10 curated themes)
- One-off styling decisions inside a single file (just inline the colors; do not introduce a brand layer)
- Vendor-specific brands the user does NOT own (Anthropic, OpenAI, Google, Tailwind, Material - Nexus-Hub policy is brand-neutral; the user must own the brand they apply)
- Open-source projects that intentionally have no brand identity (use `theme-tokens`)
- Marketing automation against another company's brand (out of scope; this skill is for the user's own brand only)

If the user does not yet have a brand, this skill is still applicable: scaffold an empty default brand at `~/.nexus-hub/brand/default/tokens.json` and have the user fill it as they make brand decisions. Do NOT silently invent brand tokens (a "professional navy and gray" is not a brand decision the agent makes for the user).

## The Brand Token Schema

The brand JSON extends the `theme-tokens` schema with brand-specific fields. Required fields are marked R; optional are O.

```json
{
  "name": "<brand-slug>",                    // R - matches the directory name
  "label": "<human-readable name>",          // R - e.g., "Acme Corp"
  "description": "<one-sentence brand statement>",  // O

  "palette": {                                // R - inherits from theme-tokens
    "primary": "#hex",                        // R
    "secondary": "#hex",                      // R
    "accent": "#hex",                         // R
    "background": "#hex",                     // R
    "foreground": "#hex",                     // R
    "muted": "#hex"                           // R
  },

  "fonts": {                                  // R - inherits from theme-tokens
    "heading": "<CSS font stack>",            // R
    "body": "<CSS font stack>",               // R
    "mono": "<CSS font stack>"                // R
  },

  "spacing": {                                // R - inherits from theme-tokens
    "base": <number, px>,                     // R
    "scale": [<multipliers>]                  // R
  },

  "radius": <number, px>,                     // R
  "shadow": "<CSS shadow value or 'none'>",   // R

  "logo": {                                   // O - brand-specific extension
    "primary": "logo.svg",                    // O - relative path under the brand dir
    "secondary": "logo-mono.svg",             // O - mono / icon-only variant
    "wordmark": "wordmark.svg",               // O - text-only variant
    "min_height_px": 24,                      // O - minimum render size
    "clear_space_factor": 1.0                 // O - whitespace as multiple of logo height
  },

  "voice": {                                  // O - brand-specific extension
    "tone": "<one-line tone descriptor>",     // O - e.g., "warm but precise"
    "do": ["<rule>", "<rule>"],               // O - DO list for copy
    "dont": ["<rule>", "<rule>"]              // O - DON'T list for copy
  },

  "assets_dir": "fonts/"                      // O - relative path to bundled fonts/icons
}
```

Notes on the contract:

1. **Palette + fonts + spacing inherit from `theme-tokens`** so the same downstream-generator mappings apply. A brand IS a theme plus brand-only extensions; the schema reflects that hierarchy.
2. **Logo is OPTIONAL because not every brand has multiple variants**. A startup may have one SVG; a mature brand has primary, mono, wordmark, and icon-only versions. The schema accepts what the user has.
3. **Voice is OPTIONAL but RECOMMENDED**. Voice rules ("warm but precise", "no buzzwords", "active voice") propagate to writing-editing, technical-writer, and internal-comms outputs. Without voice, those generators default to a neutral register that is correct but never on-brand.
4. **`assets_dir` lets users co-locate fonts and icons** with their brand JSON. The downstream generators resolve relative paths from the brand directory, not the project working directory.

## Filesystem Layout

A brand lives entirely under `~/.nexus-hub/brand/<brand-slug>/` after the user scaffolds it. Example layout for a brand named `acme`:

```
~/.nexus-hub/brand/acme/
├── tokens.json            # the schema above
├── fonts/                 # optional - self-hosted brand fonts
│   ├── AcmeSans-Regular.woff2
│   ├── AcmeSans-Bold.woff2
│   └── AcmeSerif-Regular.woff2
├── logo.svg               # primary logo (path matches tokens.logo.primary)
├── logo-mono.svg          # optional mono variant
└── wordmark.svg           # optional wordmark variant
```

The skill ships ONLY the empty template at `templates/tokens.template.json`. The user copies it into their brand directory and fills the values. The skill never ships fonts, logos, or palette values - those are the user's brand assets.

## Instructions

1. **Detect the user's brand state first**. Before picking any colors or fonts, ask the user (in one consolidated turn):
    1. Do they have a brand identity already? If yes, where (PDF, URL, internal doc, brand kit folder)?
    2. If yes, do they want to scaffold a tokens.json now, or paste the values inline for this session and persist later?
    3. If no brand exists, do they want to scaffold an empty default brand at `~/.nexus-hub/brand/default/tokens.json` for them to fill?
    4. What is the artifact target? (deck / doc / pdf / web / multiple)
2. **Scaffold the brand directory**. Create `~/.nexus-hub/brand/<brand-slug>/` and copy `templates/tokens.template.json` into it as `tokens.json`. If the user supplied brand values inline, fill them; otherwise leave the placeholders and tell the user which fields to fill in.
3. **Validate the tokens before consuming**. Required fields must all be present; hex colors must match `^#[0-9a-fA-F]{6}$`; font stacks must be non-empty strings; `spacing.base` must be a positive integer; `spacing.scale` must be an array of positive numbers. Missing required fields fail the load with a clear error: "Brand `<name>` is missing required field `palette.muted` - please add it to ~/.nexus-hub/brand/<name>/tokens.json before continuing."
4. **Map to the downstream generator**. Use the same mappings as `theme-tokens`, plus brand-only extensions:

    | Generator | Extra brand mapping (beyond theme-tokens) |
    |---|---|
    | `pptx-generation` | Logo: place `logo.primary` on the slide master at top-left with `clear_space_factor` margin; use `voice.tone` to bias the title-and-body wording. |
    | `docx-generation` | Logo: insert `logo.primary` in the header (left) at `min_height_px`; apply `voice.do` / `voice.dont` to the writing-editing pass over body copy. |
    | `pdf-document-generation` | Logo: footer-left at every page; cover page uses `logo.primary` centered at 4x `min_height_px`. |
    | `web-artifacts-builder` | Logo: emit `logo.primary` SVG inline in the header component; apply `voice.tone` to copy in the scaffolded sections. |
    | `business-product/internal-comms` | Apply `voice.do` / `voice.dont` to the chosen template's body before emitting. |
    | `developer-experience/writing-editing` | Apply `voice.tone` and the do/don't lists to the editing pass. |

5. **Honor `clear_space_factor`** when placing the logo. A clear-space factor of 1.0 means the empty space around the logo equals the logo's height. Generators that ignore clear-space produce cluttered slides and pages.
6. **Never invent or substitute brand values**. If the user's brand JSON is missing a key, fail loudly. Do not "tasteful default" your way past missing brand data - silent substitution is the failure mode that ships off-brand artifacts to clients.
7. **Pair with theme-tokens for fallback aesthetic**. If the user wants "our brand on a brutalist layout", load the user's brand tokens for palette/fonts/logo and the `brutalist-sans` theme tokens for the spacing/radius/shadow character.
8. **For multiple brands, scope at the artifact level**. A user may have multiple brands (parent company + subsidiary, employer + side project). Each gets its own directory under `~/.nexus-hub/brand/<slug>/`. The artifact selects which brand by name; the agent never mixes brand assets across artifacts.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user wants 'professional' colors - I'll just pick navy and gray" | No. ASK the user for their brand tokens. If they have none, OFFER to scaffold an empty `~/.nexus-hub/brand/default/tokens.json` for them to fill. The agent inventing brand decisions is the failure mode this skill exists to prevent. |
| "I'll copy the colors from the user's website screenshot - that's their brand" | A screenshot is not a brand kit. Ask for the canonical brand source (PDF brand guidelines, brand kit URL, design tokens repo). Approximate colors from a screenshot drift across artifacts because PNG compression eats the exact hex values. |
| "I'll just use Anthropic's brand colors / Tailwind palette / Material defaults as a placeholder" | No. This skill ships ZERO vendor assets per project policy. Vendor placeholders propagate to user artifacts and ship off-brand visuals. Use `theme-tokens` (10 curated brand-NEUTRAL themes) as the placeholder, not a vendor brand. |
| "Voice rules are too soft - I'll skip the voice section" | Voice is optional but propagates to every downstream copy generator. Skipping it means the agent's default register (neutral, mildly verbose) overrides the brand's actual register (e.g., terse, opinionated, warm). Voice is the cheapest brand field to fill and the most visible in output. |
| "I'll inline the brand colors in this session and not persist them" | Inline-only brand decisions are session-bounded - the next session re-asks the user for the same values, or worse, the agent re-invents them. Persist to `~/.nexus-hub/brand/<slug>/tokens.json` so the brand survives the conversation. |
| "Multiple logos is overengineering - one logo is enough" | One logo is enough until the cover page wants the wordmark, the email signature wants the icon-only mark, and the dark-mode artifact wants the mono variant. Scaffolding all four slots empty costs nothing; the user fills them as the artifact list grows. |
| "If the brand JSON is missing a field, I'll just default it" | Silent defaults ship off-brand artifacts. Fail loudly with the exact missing field path - that costs 30 seconds of the user's time and saves a re-export of the artifact. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] `templates/tokens.template.json` exists and contains all required keys with empty / placeholder string / `null` values (NOT vendor-specific values).
- [ ] `git grep -i 'anthropic\|openai\|tailwind.*palette\|material.*color\|google.*brand'` against this skill folder returns no hits.
- [ ] When invoked, the skill ALWAYS asks the user for brand tokens before generating any styled artifact (never assumes or substitutes).
- [ ] User-scaffolded brand JSON validates against the schema before consumption (missing required fields raise a clear error referencing the exact missing key path).
- [ ] If the user has no brand, the skill offers to scaffold `~/.nexus-hub/brand/default/tokens.json` (does not invent values).
- [ ] Logo paths in tokens.json resolve relative to the brand directory (not the project working directory).
- [ ] Downstream generators (pptx, docx, pdf, web) consume the brand JSON via the same field names as theme-tokens for shared fields, plus the brand-only extensions (logo, voice, assets_dir).
- [ ] Voice rules (when present) propagate to writing-editing, technical-writer, and internal-comms outputs - not silently dropped.
- [ ] Multiple brands coexist under `~/.nexus-hub/brand/<slug>/` without cross-pollution; each artifact selects exactly one brand.

"The output looks branded" is not a valid verification criterion. The verification is: did the user supply the brand tokens, did the schema validate, did the generator round-trip the values, and is the logo placed with the declared clear-space?

## Bundled Resources

The skill ships exactly one bundled file: an empty template the user copies into their brand directory.

- `templates/tokens.template.json` - schema-shaped placeholder with `null` and empty-string values for every field. The user copies this into `~/.nexus-hub/brand/<brand-slug>/tokens.json` and fills the values.

The skill ships NO palette values, NO font URLs, NO logo files, NO voice rules. Anything else under `~/.nexus-hub/brand/` comes from the user's own brand kit.

## Related Skills

- [[theme-tokens]] -- the brand-neutral counterpart; provides 10 curated themes plus the schema this skill extends. Use theme-tokens when the user has no brand or wants brand-agnostic styling.
- [[pptx-generation]] -- downstream consumer; maps brand tokens (palette, fonts, logo) to slide master and placeholders.
- [[docx-generation]] -- downstream consumer; maps brand tokens to Word styles, header logo, and voice-driven copy.
- [[pdf-document-generation]] -- downstream consumer; maps brand tokens to ReportLab styles, footer logo, and cover page.
- [[web-artifacts-builder]] -- downstream consumer; emits brand tokens as CSS custom properties + inline-SVG logo in the scaffold's header component.
- [[internal-comms]] -- applies `voice.do` / `voice.dont` to the chosen comms template's body.
- [[writing-editing]] -- applies `voice.tone` and do/don't rules to editing passes.
- [[technical-writer]] -- applies voice rules to long-form documentation produced under the brand.
