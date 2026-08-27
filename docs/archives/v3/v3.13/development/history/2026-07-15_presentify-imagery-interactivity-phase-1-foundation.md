# Session History -- presentify imagery + interactivity, Phase 1 (foundation)

**Date**: 2026-07-15
**Version**: v3.13.0
**Plan**: `docs/v3/v3.13/plans/v3.13.0-presentify-imagery-and-interactivity.md`
**Phase**: 1 of 5 -- Imagery + interactivity foundation (Tier 1, the design question, interactivity levels, credits convention)
**Branch**: `feat/presentify-imagery-and-interactivity` (off `develop`)

## Goal

Ship the complete DEFAULT experience with zero outbound: the "Imagery and interactivity" design question (after style, after layout), an interactivity spectrum (restrained / balanced / rich) with a scrollytelling pattern catalog, a Tier-1 LLM-native procedural-visual authoring rule, and a visual-provenance / credits convention that the later tiers plug into.

## What was built

### 1.1 The "Imagery and interactivity" design question

- `catalog/commands/presentify.md`: added `--images <procedural|stock|ai|auto|none>` (natural form "using ... images") and `--interactivity <restrained|balanced|rich>` to the Usage synopsis and option list; added a "Choosing imagery and interactivity" section (asked AFTER style + layout); documented the non-interactive fallback (imagery = procedural / Tier 1; interactivity = content-aware); wired the resolution into the delegation flow and added a Notes bullet. Stated plainly that the stock / AI tiers are opt-in and consent-gated for any outbound path, while the default and every non-interactive run stay offline.
- `SKILL.md` Instruction step 4: added a "Resolve imagery and interactivity" bullet after the aspect bullet - a named `--images` / `--interactivity` binds and skips the menu; otherwise the menu is offered; non-interactively it defaults to procedural + a content-aware level; both the tier and level (with any auto-pick note) are recorded in the design-record HTML comment.

### 1.2 Interactivity spectrum + scrollytelling pattern catalog

- `references/interactive-features.md`: extended the "Site-wide interaction layer" section with an "Interactivity spectrum (restrained / balanced / rich)" subsection (observable criteria per level; the explicit reconciliation that BALANCED == the current minimum interaction budget and RESTRAINED is a lower rung that keeps the five budget points but drops scroll-triggered motion) and a "Scrollytelling pattern catalog (RICH level)" with five patterns - pinned/sticky graphic with scroll steps, full-bleed image-to-text transition, parallax layers, progress-driven timeline, before/after slider - each with a short vanilla-JS / CSS sketch and an accessibility note. Parallax is disabled entirely (not merely shortened) under reduced motion.

### 1.3 Tier 1 procedural-visual rule

- `references/interactive-features.md`: added an "## Imagery tiers (procedural / stock / AI)" H2 (the shared home for Phases 2/3), with the absolute offline guarantee across all three tiers, and a "Tier 1 - procedural visuals (default)" subsection: the procedural vocabulary (backgrounds, dividers, editorial devices, textures/illustrations), the safety rules (decorative-not-load-bearing, contrast within the accessibility gate, token coherence, content-relevant-not-cliche), and the statement that Tier 1 is the zero-outbound default. Cross-links `[[generative-art]]` and `[[ui-component-generation]]`.

### 1.4 Visual-provenance and credits convention

- `references/interactive-features.md`: added a "Visual provenance and credits" subsection - per-tier provenance (Tier 1 = "original (generated)"; Tier 2 = source/URL/license/attribution; Tier 3 = model/license/copyright caveat), the TWO recording locations (an adjacent HTML comment + a visible "Image credits" section), the JSON credit-entry data shape the Phase 2/3 helpers emit, and how it sits parallel to (not replacing) the Step 7 coverage-reconciliation ledger.
- `SKILL.md` Verification: added the binary item that every non-original visual appears in the credits with a free-for-commercial-use license and required attribution, and no visual lacks provenance.

### 1.5 Wire into SKILL.md + Tier-1 sample

- `SKILL.md` Instruction step 5: added an "Imagery and interactivity (apply the resolved tier + level)" authoring bullet making Tier-1 procedural visuals + the credits convention + the chosen interactivity level mandatory pipeline behavior (with the restrained/balanced/rich mapping onto the budget points).
- `SKILL.md` Common Rationalizations: three new rows - "the page looks bare without photos", "I'll hotlink a stock image for speed", "richer is always better".
- `SKILL.md` Verification: added items for imagery tier + interactivity level recorded in the design comment, a Tier-1 run having zero external requests, and rich-level effects honoring `prefers-reduced-motion`.
- `docs/v3/v3.13/development/worked-example/tier1-imagery-sample.html`: a hand-authored, self-contained, offline Tier-1 sample from the `mixed-repo` fixture model - a "Warm Editorial Ledger" direction (light editorial, diverges from the dark/mono/amber/card-grid attractor), original procedural visuals (SVG hero gradient + dot-grid texture, duotone divider, a data-motif figure, editorial callout number and pull-quote), a balanced interaction layer (sticky nav with active-state tracking, scroll reveals, hover/focus affordances, an animated counter landing on the exact source total, a pan/zoom lightbox on the procedural figure), an interactive grouped-bar chart on the real CSV values (hover readout, legend series toggle, y-max control, reset), a design-record comment recording the imagery tier + interactivity level, and an "Image credits" section stating all visuals are original (generated).

## Verification

- Bundle audit (`validate_skills.py --bundles-only`, the `make validate` gate): PASS, 0 errors.
- All four edited/created files ASCII-clean (verified byte-by-byte).
- Tier-1 sample: offline-refs grep (`https?://|cdn`) clean; tag balance OK (svg 5/5, section 7/7, html/head/body/style/script/main/nav all 1/1); well-formed.
- SKILL.md body 201 lines (within the 500 size norm); the heavy design content lives in `references/interactive-features.md` (366 lines) per the three-tier loading model.
- The chart is built by assigning an SVG-markup string to `svg.innerHTML` (parsed in the SVG namespace) rather than `createElementNS(...w3.org...)`, so no `http://` namespace literal appears - keeping the offline URL self-check clean.

## Notes / limitations

- No executable source code this phase (Markdown docs + one static HTML sample), so lint / coverage / build / test gates are N/A; the applicable gate is the validator suite (bundle audit + ASCII + offline grep + tag balance), which is green. The pure-function CI verifier (keyword derivation, license filter, credits-manifest shape, consent-default-offline) is a planned Phase 5 deliverable, not a Phase 1 gap.
- `__pycache__/` is already gitignored (`.gitignore:60`); the stray `.pyc` under the skill's `scripts/` is untracked and not part of this diff.
- The Tier-1 sample was reviewed statically; the rendered screenshot / visual-QA pass needs a headless browser (absent on the Windows dev host) - folded into the version's existing WN-1.
- Full-repo `make validate` (unicode-safety / no-personal-paths scans, the compression eval, base-template parity, platform-contracts) times out on this host; the change-relevant validators were run directly. Run the full chain in CI.
- The CHANGELOG `[Unreleased]` entry and the `data/skills.json` / `SKILL_INDEX.md` registry sync are deliberately deferred to Phase 4 (4.3), which also touches the frontmatter description; no registry files were changed this phase.

## Next

Phase 2 -- Tier 2 license-free stock media: `scripts/fetch_stock_media.py` (consent-gated build-time fetch, Openverse-first, license verification + attribution capture, base64 embed, credits manifest, graceful offline degrade), wired into the pipeline behind the consent gate.
