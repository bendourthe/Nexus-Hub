# Session History -- presentify imagery + interactivity, Phase 2 (Tier 2 license-free stock)

**Date**: 2026-07-15
**Version**: v3.13.0
**Plan**: `docs/v3/v3.13/plans/v3.13.0-presentify-imagery-and-interactivity.md`
**Phase**: 2 of 5 -- Tier 2: license-free stock media (opt-in, consent-gated)
**Branch**: `feat/presentify-imagery-and-interactivity` (off `develop`)

## Goal

When the user opts in and consents, fetch highly-relevant, free-for-commercial-use images / video from openly-licensed sources at build time, verify the license, capture attribution, base64-embed them (output stays offline), and record credits - degrading gracefully to Tier 1 when offline, un-consented, or a source is unavailable.

## What was built

### 2.1 The stock-media fetch helper

- `catalog/skills/specialized-domains/document-to-interactive-html/scripts/fetch_stock_media.py` (new). Lazy-imports `requests` with a stdlib `urllib` fallback; NO other dependency; network modules are imported only inside the fetch path (reached after the consent check).
- CLI: `--query`, `--kind image|video`, `--count`, `--license cc0|commercial`, `--source openverse|wikimedia|pexels|coverr|mixkit`, `--max-bytes`, `--consent`, `-o`.
- CONSENT GATE (structural): with no `--consent`, `main()` returns the degrade path before any network import/call - prints a notice, writes `{"assets": [], "degraded": true, ...}`, exits 3. So "no consent => no network" holds by construction.
- Sources: Openverse (default, keyless) and Wikimedia Commons (keyless) fully implemented for images; Pexels supported when `PEXELS_API_KEY` is set (absent key => skipped); Coverr / Mixkit accepted on the CLI for parity but degrade with a note (no keyless search API).
- License gate: an allow-list (`cc0`, `pdm`, `by`, `by-sa` + blanket-license sources); any `nc`/`nd` token is rejected; unknown codes fail safe. Downloads are capped at `--max-bytes`, base64-embedded into `data:` URIs. Every fetch failure (missing lib/key, network error, oversize, zero results) degrades - never raises.

### 2.2 Attribution correctness + Tier 2 reference

- `references/interactive-features.md`: new "Tier 2 - license-free stock (opt-in, consent-gated)" subsection under "Imagery tiers" - the consent gate, the source matrix, the per-source license rules (Openverse/Wikimedia per-file CC/PD with built CC-BY attribution; Pexels/Coverr/Mixkit blanket license, credited by source), the allow-list commercial-use gate, the compiling-content trap (Unsplash/Pexels/Pixabay custom-license restriction; prefer CC0/PD; never a stock-media service), and the offline-clean attribution rule (human attribution text in the visible credits, raw URLs only in the adjacent comment / manifest).

### 2.3 Pipeline wiring + consent gate

- `SKILL.md`: authoring step 5 now derives keywords and runs `fetch_stock_media.py --consent` for the `stock` tier (or `auto` with consent), placing base64 assets per the prominence + spacing rules; a run without both the stock/ai choice AND consent (and every non-interactive run) stays on Tier 1. Added the Bundled Resources entry, a Common Rationalizations row ("the fetch is convenient, I'll skip the consent"), and a Verification item (stock assets base64-embedded + license-verified + credited; no-consent => no network; output greps clean even with stock images).
- `catalog/commands/presentify.md`: the `--images` option and the "Choosing imagery and interactivity" section now describe the active consent confirmation before any build-time fetch (replacing the Phase 1 "wired in a later phase" placeholders).

## Verification

- ruff: clean on `fetch_stock_media.py` (default rules, 88-col).
- Consent gate: no-`--consent` run exits 3 with a degraded manifest and makes no network call; `--count 0` returns usage exit 2.
- Live Openverse smoke fetch (`--consent`, count 1): embedded a CC-BY-SA 2.0 image (73 KB JPEG) with a correctly-built attribution string and a base64 `data:` URI - the full Tier 2 path proven end-to-end.
- License-filter unit check: `cc0/pdm/by/by-sa` accepted; every `nc`/`nd`/empty/unknown rejected; `cc_requires_attribution` correct (by=True, cc0=False); blanket Pexels accepted; `by-nc` rejected with a reason.
- Bundle audit (`--bundles-only`, the `make validate` gate): PASS, 0 errors (the only presentify-skill warnings are the two gitignored `__pycache__/*.pyc` from local test runs; the new script is referenced, not an orphan).
- All four Phase 2 files ASCII-clean.

## Notes / limitations

- No committed automated verifier yet for the helper's pure-function logic - recorded as MT-2; the committed `verify_imagery.py` + its CI wiring is the Phase 5 (5.3) deliverable. Only Openverse was live-exercised (Wikimedia/Pexels implemented per docs; Pexels needs a key).
- Coverr / Mixkit and general video fetch are not implemented (no keyless search API) - recorded as DF-6; accepted on the CLI for interface parity, degrade with a note.
- `__pycache__/` is already gitignored (`.gitignore:60`); the stray `.pyc` files are untracked and not in this diff.
- CI: `presentify-extractor.yml` path-filters on `scripts/**` and already lints the new script with ruff; the pure-function verifier is added and wired in Phase 5.
- Registry (`data/skills.json` / `SKILL_INDEX.md`) and CHANGELOG updates remain deferred to Phase 4 (the frontmatter description did not change this phase).

## Next

Phase 3 -- Tier 3 local AI-generated images: `scripts/generate_local_image.py` (drives a LOCAL Apache-2.0 / Open-RAIL-M model when present, records model + license + the copyright caveat, never calls a hosted service, degrades to Tier 1 when no runtime/weights are present), wired into the pipeline as opt-in local-only.
