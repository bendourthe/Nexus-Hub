# Session History -- presentify universal ingestion, Phase 3 (spacing/density + output aspect)

**Date**: 2026-07-13
**Version**: v3.13.0
**Plan**: `docs/v3/v3.13/plans/v3.13.0-presentify-universal-ingestion.md`
**Phase**: 3 of 5 -- Spacing / density discipline + output-aspect control
**Branch**: `feat/presentify-robustness` (off `develop`)

## Goal

Eliminate dead, half-empty screens in the output, and let the user choose the overall canvas aspect (full-width for a 16:9 screen, standard webpage width, portrait, or a custom description) through a menu asked exactly like the style menu, bindable up front with `--layout`.

## What was built (docs/instructions only; no extractor code)

### Reference (`references/interactive-features.md`)

- **"Spacing and density"** subsection: size sections to content (no fixed one-screen stretch that leaves half a viewport empty); consistent vertical rhythm from the committed spacing token; compact or pair sparse sections instead of floating them in whitespace; reserve generous whitespace for intentional emphasis only. Framed as the vertical partner to the existing "use the viewport width on purpose" rule.
- **"Output aspect (the canvas)"** subsection: the four aspects and their concrete CSS-canvas mappings - Full-width (fills 16:9; wide container, full-bleed bands, multi-column), Standard (centered ~72-90rem column), Portrait (~40-52rem single column, scroll charts/tables), Other (interpret the description). The aspect composes with (never overrides) the per-element width discipline and design tokens; content-aware non-interactive fallback (deck / `deck_like` PDF -> full-width; report/repo/text -> standard); resolved aspect recorded in the design comment.

### Skill (`SKILL.md`)

- Design step: a "Resolve the output aspect" bullet (named `--layout` binds; else the aspect menu; else content-aware auto-pick), placed after the style/entropy resolution.
- Authoring step: a "Spacing, density, and aspect" bullet (build to the resolved aspect; hold the density rule).
- Verification: two new binary items (spacing/density holds; built to the resolved aspect and recorded).
- Visual-QA: the assess step now also flags dead / half-empty vertical space and a canvas that does not match the resolved aspect.

### Command (`presentify.md`)

- Usage line + a `--layout <full|standard|portrait|description>` option (natural form `using the layout <...>`).
- A "Choosing the output aspect (when no layout is given)" section mirroring the style-menu section (four options + content-aware fallback + how the aspect maps to the canvas).
- Intro sentence, a Notes bullet (aspect + density, plus a prominence note carried from Phase 2), and the delegation paragraph updated to resolve the aspect and build to it.

## Verification

- SKILL.md body: 192 lines (within the 500 norm).
- ASCII-clean: `interactive-features.md`, `SKILL.md`, `presentify.md`.
- Aspect vocabulary (full-width / standard / portrait) present and consistent across the command, the skill, and the reference.
- Bundle audit: 0 errors.

## Notes / limitations

- Phase 3 is instructions/rules plus a command option; the rendered per-aspect demonstration (authoring one page per aspect and confirming each fills its intended canvas) needs a headless browser and belongs to the Phase 5 worked example.
- The broader `presentify.md` update for the new input formats and directory/repository inputs is Phase 4 (this phase only added the `--layout` / aspect surface).

## Next

Phase 4 -- command-doc update for the new formats + directory/repository inputs, a worked example over a mixed repository, registration sync (`data/`), CHANGELOG, and the full validator chain.
