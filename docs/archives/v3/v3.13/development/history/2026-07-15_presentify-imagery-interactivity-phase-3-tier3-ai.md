# Session History -- presentify imagery + interactivity, Phase 3 (Tier 3 local AI-generated images)

**Date**: 2026-07-15
**Version**: v3.13.0
**Plan**: `docs/v3/v3.13/plans/v3.13.0-presentify-imagery-and-interactivity.md`
**Phase**: 3 of 5 -- Tier 3: local AI-generated images (opt-in, local-only)
**Branch**: `feat/presentify-imagery-and-interactivity` (off `develop`)

## Goal

When the user opts in, generate original, content-and-style-relevant images with a LOCAL, commercially-clean model runtime, base64-embed them, record the model license and the copyright caveat, and degrade gracefully to Tier 1 when no local runtime is present. Never call a third-party generation service.

## What was built

### 3.1 The local AI-image helper

- `catalog/skills/specialized-domains/document-to-interactive-html/scripts/generate_local_image.py` (new). Lazy-imports `diffusers` + `torch`, or shells out to a user-configured LOCAL CLI (`NEXUS_LOCAL_IMAGE_CMD`, run via subprocess with no shell); imports NO network / hosted-API client.
- CLI: `--prompt`, `--model flux-schnell|sdxl`, `--size WxH`, `--steps`, `--max-bytes`, `-o`.
- LOCAL-ONLY, zero-network: forces `HF_HUB_OFFLINE=1` / `TRANSFORMERS_OFFLINE=1` / `DIFFUSERS_OFFLINE=1` BEFORE importing the runtime and loads with `local_files_only=True`, so a missing weight degrades instead of triggering a download (the script never downloads weights; the user obtains them out-of-band).
- Commercially-clean models only: FLUX.1 schnell (Apache-2.0, default) and SDXL base (CreativeML Open RAIL++-M); a model whose license is not free-for-commercial-use is rejected.
- On success emits the same manifest shape as Tier 2 (`{"assets": [{data_uri, alt, width, height, provenance{tier: ai, model, license, note: "AI-generated; may not be copyrightable", prompt}}], ...}`); on any missing runtime / weights / failure it prints a setup hint, writes an empty degraded manifest, and exits 3 - never raises, never falls back to a hosted API.

### 3.2 Pipeline wiring + local-only constraint

- `references/interactive-features.md`: new "Tier 3 - local AI-generated images (opt-in, local-only)" subsection - the local-only hard constraint (hosted generation-as-service is out of scope), the models + runtimes, the offline weight-loading discipline, and the copyright caveat; it feeds the same credits-manifest convention.
- `SKILL.md`: authoring step 5 now builds a prompt from content + committed style tokens and runs `generate_local_image.py` for the `ai` tier, recording model + license + caveat; added the Bundled Resources entry, a Common Rationalizations row ("I'll just call a hosted image API"), and a Tier-3 Verification item (model + license + caveat in credits; no hosted-API call; output offline; degrade when no runtime).
- `presentify.md`: corrected the imagery Notes bullet to distinguish Tier 2 (build-time fetch, consent-gated) from Tier 3 (LOCAL-only, no hosted service, degrades to Tier 1) - the earlier bullet imprecisely lumped Tier 3 under the network-consent gate.

## Verification

- ruff: clean on both `generate_local_image.py` and `fetch_stock_media.py`.
- Degrade path: with no `diffusers`/`torch` and no `NEXUS_LOCAL_IMAGE_CMD`, the helper degrades (exit 3) with a clear two-part hint (diffusers then CLI) and makes no network call; bad `--size` returns usage exit 2.
- Static policy check: the script imports NONE of {requests, urllib, httpx, http.client, aiohttp, socket, websocket, openai, replicate, boto3, google.cloud, anthropic} or any hosted hostname; `subprocess` is present only for the local CLI. This is the "imports no network / hosted-API client" acceptance for 3.1.
- Bundle audit (`--bundles-only`, the `make validate` gate): PASS, 0 errors (the only presentify-skill warnings are the gitignored `__pycache__/*.pyc`; `generate_local_image.py` is referenced, not an orphan).
- All four Phase 3 files ASCII-clean.

## Notes / limitations

- The live generation path was NOT run locally (no `diffusers` / `torch` / GPU / weights on the Windows dev host); only the degrade path and the static no-hosted-client check were exercised. Recorded by broadening MT-2 to cover both Tier 2 and Tier 3 helpers; the live Tier-3 generation stays a documented manual step on a GPU-capable host, and the committed pure-function verifier (license registry / degrade / no-network-import) is the Phase 5 (5.3) deliverable.
- No `--consent` flag on the Tier-3 helper by design: it makes no network call, so there is no build-time network use to consent to - it is opt-in purely via the `ai` tier choice (a heavy optional dependency).
- CI: `presentify-extractor.yml` path-filters `scripts/**` and already lints the new script with ruff; it does not (and should not) install `diffusers`/`torch` - only the offline pure-function logic is CI-testable.
- Registry (`data/skills.json` / `SKILL_INDEX.md`) and CHANGELOG updates remain deferred to Phase 4 (the frontmatter description did not change this phase).

## Next

Phase 4 -- command surface, worked examples, registration sync, validation: document the imagery tiers / interactivity levels / `--images` / `--interactivity` / consent gate in `presentify.md` + the SKILL.md frontmatter (`description` / `summary_l0` / `overview_l1`); a Tier-1 worked example (offline) and a Tier-2 example (live if consent + network, else documented); mirror the frontmatter into `data/skills.json` + `SKILL_INDEX.md` (hand-edited); add the CHANGELOG `[Unreleased]` entry; run the change-relevant validators.
