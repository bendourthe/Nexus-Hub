# Session History -- presentify imagery + interactivity, Phase 4 (command surface, worked examples, registration)

**Date**: 2026-07-15
**Version**: v3.13.0
**Plan**: `docs/v3/v3.13/plans/v3.13.0-presentify-imagery-and-interactivity.md`
**Phase**: 4 of 5 -- Command surface, worked examples, registration sync, validation
**Branch**: `feat/presentify-imagery-and-interactivity` (off `develop`)

## Goal

Document the imagery + interactivity capability, prove it end to end (Tier 1 offline; Tier 2 live), and keep the catalog metadata truthful.

## What was built

### 4.1 Trigger surface

- `SKILL.md` frontmatter: `description` broadened with tiered commercial-use-safe imagery (procedural default; opt-in stock; opt-in local AI) and the interactivity level, and the SKIP clause extended (standalone stock-photo search / AI-image generation with no site to build); `summary_l0` now names "tiered imagery" (15 words, at the cap); `overview_l1` gains an imagery-tiers + interactivity sentence.
- `presentify.md`: the Usage synopsis, `--images` / `--interactivity` options, the "Choosing imagery and interactivity" menu, the delegation flow, and the Notes were built across Phases 1-3 and were confirmed coherent this phase (no further change needed).

### 4.2 Worked examples (`docs/v3/v3.13/development/worked-example/`)

- Tier 1: `tier1-imagery-sample.html` (authored Phase 1) - procedural visuals, a balanced interaction layer, an interactive chart on the real CSV values, a design-record comment, and an all-original credits section; offline-clean.
- Tier 2 (LIVE): ran `fetch_stock_media.py --query "laboratory microscope science" --count 2 --consent` against Openverse (2026-07-15), returning two CC-BY-2.0 assets; built `tier2-stock-sample.html` from the manifest (each asset base64-embedded, an adjacent machine-readable credit comment, a visible attribution-only credits section) and kept `tier2-credits-manifest.json`.
- `imagery-worked-example.md`: documents both examples, the static offline reviews, and the Tier-3 documented (GPU-host) path, with a coverage summary table.

### 4.3 Registration + CHANGELOG

- `data/skills.json`: `description` / `summary_l0` / `overview_l1` mirrored from the frontmatter and `size` recomputed (208 lines / 45674 chars / ~6698 tokens) via a targeted, byte-preserving JSON round-trip (`indent=2, ensure_ascii=False` reproduces the file exactly, so only the four intended fields changed - not `build_skills_catalog.py`). `data/SKILL_INDEX.md` row summary updated. `data/marketplace.json` counts unchanged (no new skill / command).
- `CHANGELOG.md`: a second block under the existing `## [Unreleased]` (same v3.13.0 release) describing the imagery tiers, interactivity spectrum + scrollytelling, the credits convention, the consent gate, the offline / commercial-use guarantees, and the new opt-in lazy dependencies (`requests`; `diffusers` + `torch`).

## Verification

- `skills.json` valid JSON (273 skills); `marketplace.json` unchanged; the skills.json diff is confined to the four intended fields of the presentify entry (verified against the changed hunks).
- Bundle audit (`--bundles-only`): PASS, 0 errors. ruff: clean on both bundled scripts. version-sync: all surfaces match 3.12.1 (no bump; version bumps at release time).
- Both worked-example pages are offline-clean (comments + base64 stripped, then `https?://` / `cdn` grep -> NONE outside comments).
- Hosted-client policy grep: `fetch_stock_media.py` references only allowed license-free / vendor endpoints (Openverse, Wikimedia, Pexels-your-own-key, creativecommons.org license URLs); `generate_local_image.py` references zero URLs. The only forbidden-token hit is the Tier-3 docstring line that PROHIBITS hosted APIs (a policy statement, not a client).
- All files I edited/created are ASCII-clean. (`data/skills.json:90` carries pre-existing non-ASCII bytes in the unrelated `ai-billing-safeguards` entry, outside my diff and preserved verbatim by the byte-identical round-trip; the CHANGELOG's pre-existing non-ASCII lines are prior-release entries - both out of scope.)

## Notes / limitations

- Full-repo `validate_unicode_safety.py` / `validate_no_personal_paths.py` time out on the Windows dev host (WN-1); run the full chain in CI. Neither the SKILL.md body nor the frontmatter change touched the body-size norm (SKILL.md ~211 lines, well within 500).
- `long_description` in `skills.json` was left as-is (the plan mirrors `description` / `summary_l0` / `overview_l1` / `size`; `long_description` is out of scope).
- The live Tier-2 example is non-reproducible (Openverse results vary run to run); it is committed as dated evidence, not a fixture.

## Next

Phase 5 (final) -- architecture refactor + docs-layout cleanup, known-gaps reconciliation for the version, a CI verifier (`verify_imagery.py`: keyword derivation, license filter / rejection, credits-manifest shape, CC-BY attribution builder, the consent-default-offline invariant, and the Tier-3 license-registry / degrade / no-network-import invariants) wired into `presentify-extractor.yml`, then the release-readiness handoff to `/update release` (never tagging or pushing automatically). Phase 5 is terminal, so `/implement` runs the mandatory final-phase refactor + known-gaps + CI/CD gate.
