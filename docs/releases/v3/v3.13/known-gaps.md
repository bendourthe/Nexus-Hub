# Known Gaps - v3.13

**Project**: Nexus-Hub
**Status**: release-ready - both the universal-ingestion overhaul and the imagery-and-interactivity follow-on (all 5 phases) are complete; pending `/update release` (version bump / merge / tag / push)
**Last updated**: 2026-07-15 (Phase 5 reconciliation for the presentify imagery-and-interactivity follow-on)

## v3.13.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 6 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 0 |
| Missing tests / coverage gaps (MT) | 2 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |
| Hand-offs (HO) | 1 | 0 |

### Capabilities added this version

- Universal ingestion: source code / config, Markdown / plain text, CSV / TSV, standalone images, and a recursive directory / repository walk with ignore rules, a best-effort `.gitignore` matcher, a binary sniff, and `--max-files` / `--max-text-bytes` caps; repository assembly (synthesized overview + file tree + README-first + code grouped by directory).
- Image prominence signals (`width` / `height` / `page_fraction`) and a prominence-preservation authoring rule (a dominant source visual stays a hero, never flattened into a uniform thumbnail grid).
- Spacing / vertical-density discipline and an output-aspect control (`--layout` + a full-width / standard / portrait / other menu, content-aware non-interactive fallback).
- Imagery + interactivity foundation (imagery-and-interactivity follow-on, Phase 1): the "Imagery and interactivity" design question (`--images` / `--interactivity`, asked after style + layout, non-interactive fallback = procedural + content-aware, both recorded in the design-record comment); the interactivity spectrum (restrained / balanced / rich) + a scrollytelling pattern catalog (pinned graphics, image-to-text, parallax, timeline, before/after slider - all inline / reduced-motion-guarded / keyboard-accessible); the Tier-1 LLM-native procedural-visual rule (zero-outbound default); and the visual-provenance / credits convention shared by all three tiers.
- Tier 2 license-free stock media (imagery-and-interactivity follow-on, Phase 2): `scripts/fetch_stock_media.py`, an opt-in, consent-gated build-time fetcher (NO network without `--consent`) that queries Openverse (default, keyless) / Wikimedia (keyless) / Pexels (key-gated), enforces a free-for-commercial-use license allow-list (CC0 / PDM / CC-BY / CC-BY-SA plus blanket-license sources; any nc/nd term rejected), builds CC-BY attribution strings, base64-embeds each asset (output stays offline), and emits a credits manifest feeding the Phase 1 credits convention; graceful degrade to Tier 1 on any missing library / key / network error / zero results. Wired into SKILL.md + `presentify.md` behind the consent gate. Live-verified end-to-end against Openverse (a CC-BY-SA asset fetched, verified, and embedded).
- Tier 3 local AI-generated images (imagery-and-interactivity follow-on, Phase 3): `scripts/generate_local_image.py`, an opt-in, LOCAL-ONLY generator that makes NO network call and imports no hosted-API client (a third-party generation API is a generation-as-service hard-no). It runs `diffusers` + `torch` (forced offline with `local_files_only=True` + `HF_HUB_OFFLINE=1` so it never downloads weights) or a user-configured local CLI (`NEXUS_LOCAL_IMAGE_CMD`), uses a commercially-clean default model (FLUX.1 schnell, Apache-2.0; or SDXL, CreativeML Open RAIL++-M), records model + license + the "AI-generated; may not be copyrightable" caveat, base64-embeds the PNG, and degrades to Tier 1 when no local runtime / weights are present. Wired into SKILL.md + `presentify.md` + a "Tier 3" reference subsection. Verified: the degrade path (no runtime => exit 3, no network) and a static check confirming zero network / hosted-API imports.
- Command surface + worked examples + registration (imagery-and-interactivity follow-on, Phase 4): the SKILL.md `description` / `summary_l0` / `overview_l1` document the imagery tiers, interactivity levels, `--images` / `--interactivity`, the consent gate, and the offline / commercial-use guarantees, mirrored into `data/skills.json` (+ recomputed `size`) and the `data/SKILL_INDEX.md` row (hand-edited; `marketplace.json` counts unchanged); a CHANGELOG `[Unreleased]` block added. Worked evidence under `development/worked-example/`: the Tier-1 sample (Phase 1) plus a LIVE Tier-2 example (`tier2-stock-sample.html` + `tier2-credits-manifest.json`, two CC-BY-2.0 Openverse assets fetched, verified, base64-embedded, credited) and `imagery-worked-example.md`. Change-relevant validators green; both example pages offline-clean; no hosted-service client in the diff.
- Refactor + CI verifier + reconciliation (imagery-and-interactivity follow-on, Phase 5): a scoped refactor audit (clean - no sprawl / duplicates / orphans in the plan's footprint; two pre-existing v3.9.0 skill-internal empty dirs flagged, out of scope, untracked); an offline, deterministic CI verifier `docs/v3/v3.13/development/fixtures/verify_imagery.py` (34 checks: the license filter incl. nc/nd rejection, the CC-BY attribution builder, `accept_candidate`, the credits-manifest / asset shape via a stubbed download, the consent-default-offline invariant via a stubbed transport, the Tier-3 model-license registry / `parse_size` / degrade path, and the no-network-import static invariant), wired into `.github/workflows/presentify-extractor.yml` (path filters + a run step, no new CI dependency).

### Advisory

- Purely AI-generated images (Tier 3) may not be copyrightable in some jurisdictions; the tool records the caveat `AI-generated; may not be copyrightable` in each asset's provenance and the credits section. This is an inherent legal advisory surfaced to the user, not a defect.

### Open Items

#### Deferred

##### DF-1 - `.gitignore` matching is best-effort

- **Source phase**: Phase 1 (1.2)
- **Reason**: The walk reads the root `.gitignore` and supports leading-`/` anchoring plus basename / path globs via `fnmatch`, but does NOT implement negation (`!pattern`) or git's full `**` semantics. Documented as a runbook limit.
- **Suggested next step**: Adopt a vetted local `.gitignore`-spec library only if real repos show meaningful mismatch; the current matcher plus the ignore-dir list covers the common cases.

##### DF-2 - Markdown parser is intentionally minimal

- **Source phase**: Phase 1 (1.3)
- **Reason**: The in-house Markdown parser handles ATX / setext headings, fenced code, bullets, pipe tables, and standalone local images; it is not a full CommonMark implementation (reference-style links, footnotes, and HTML blocks pass through as prose). Standard-library-only by design (no Markdown dependency).
- **Suggested next step**: Revisit only if richer Markdown fidelity is needed; a lazy-imported CommonMark parser could be added behind the same lazy-import discipline.

##### DF-3 - No secret redaction on the repository walk

- **Source phase**: Phase 1 (1.2)
- **Reason**: The walk ingests text / config files by extension; dotfiles with no recognized extension (`.env`) are not ingested, but a file such as `secrets.yaml` would be. There is no content-based secret detection.
- **Suggested next step**: Users should not point `/presentify` at a repository holding plaintext secrets; a future pass could integrate the `egress-redaction` skill's typed policy before ingestion.

##### DF-4 - Video / audio media embedding (carried from v3.9 / v3.12)

- **Reason**: Media in any source format is ignored; embedded media would break the single-file offline / size guarantee. Unchanged by this version.
- **Suggested next step**: Out of scope for the self-contained-HTML deliverable.

##### DF-5 - Brand web-font embedding (carried from v3.9 / v3.12)

- **Reason**: Fonts stay as system stacks or base64 `@font-face`; fetching a brand web font would break the offline guarantee. Unchanged by this version.
- **Suggested next step**: A base64 `@font-face` embed path could be added; never an external fetch.

##### DF-6 - Tier 2 stock: Coverr / Mixkit sources and general video fetch not implemented

- **Source phase**: Phase 2 (2.1)
- **Reason**: `fetch_stock_media.py` implements Openverse (default, keyless), Wikimedia Commons (keyless), and Pexels (API-key-gated) for images. Coverr / Mixkit are accepted on the CLI for interface parity but have no keyless search API in this helper, so they degrade with a note; video is supported only via a Pexels key. This keeps the helper honest rather than shipping unverified API integrations. Video also inherits the base64 size ceiling: any fetched asset is base64-embedded and rejected past `--max-bytes`, so a large video degrades rather than bloating the single-file output (video embedding at scale remains constrained by the offline single-file guarantee, per DF-4).
- **Suggested next step**: Add a Coverr / Mixkit (or a generic configured-endpoint) source and a broader video path only if a real need appears; document them as configured sources, and keep video within a sensible `--max-bytes` cap.

#### Warnings

##### WN-1 - Full-repo validators and browser visual-QA unavailable on the Windows dev host

- **Source phase**: Phases 1-5
- **Reason**: `validate_unicode_safety.py` / `validate_no_personal_paths.py` (full-repo scans) and the compression eval time out on the dev host, and no headless browser is installed, so the rendered visual-QA loop (screenshots) and the per-aspect / hero-vs-gallery rendered demonstrations could not run locally. Change-relevant validators were run directly (bundle audit, JSON integrity, version-sync, ASCII, ruff); edited files are ASCII-verified. The imagery-and-interactivity Phase 1 Tier-1 sample (`development/worked-example/tier1-imagery-sample.html`) was likewise reviewed statically (offline-refs grep clean, tag-balance and ASCII checked), not browser-rendered.
- **Suggested next step**: Rely on CI for the full validator chain; run the rendered visual-QA of the Tier-1 sample and the universal-ingestion worked example in a browser-capable session.

##### WN-2 - Deck-PDF prominence path not exercised end-to-end locally

- **Source phase**: Phase 2
- **Reason**: `pdfplumber` / `python-pptx` are not installed on the dev host, so the PDF path falls back to `pypdf` (no bbox geometry) and the PPTX path was not run; the PDF/PPTX `page_fraction` geometry was validated by code review plus the common-sink unit-check (rounding / clamp / absence). CI installs `pdfplumber` / `python-pptx`.
- **Suggested next step**: Covered by MT-1.

#### Missing tests / coverage gaps

##### MT-1 - No automated verifier check for PDF / PPTX `page_fraction` geometry

- **Source phase**: Phase 2 / Phase 5
- **Reason**: `verify_universal_ingestion.py` (28 checks) covers the text / code / CSV / image walk, repository assembly, determinism, caps, and the prominence sink (rounding / clamp / absence / native dims), but not the PDF-bbox / PPTX-shape `page_fraction` computation end-to-end. The v3.12 `verify_phase1.py` exercises PDF/PPTX extraction but predates `page_fraction`.
- **Suggested next step**: Add a `page_fraction` assertion to `verify_phase1.py` (it already generates a PDF/PPTX fixture with `reportlab` / `python-pptx` in CI), or a small dedicated fixture check, in a follow-up.

##### MT-2 - Live Tier-2 fetch paths and Tier-3 generation not exercised in CI (residual)

- **Source phase**: Phase 2 (2.1-2.3), Phase 3 (3.1-3.2), Phase 5 (5.3)
- **Status**: the committed automated verifier is DELIVERED - `docs/v3/v3.13/development/fixtures/verify_imagery.py` (34 offline checks: license filter incl. nc/nd rejection, CC-BY attribution builder, `accept_candidate`, the credits-manifest / asset shape via a stubbed download, the consent-default-offline invariant via a stubbed transport, and the Tier-3 model-license registry / `parse_size` / degrade / no-network-import invariants), wired into `presentify-extractor.yml`. It runs on a plain ubuntu runner with no extra dependency, network, or GPU.
- **Residual gap**: only the LIVE network / GPU paths remain un-CI'd - the Wikimedia and Pexels source paths were not live-exercised (Openverse was, returning verified CC-BY assets; Pexels needs a key), and the Tier-3 diffusers generation path needs a local GPU runtime + weights absent from the dev host and CI.
- **Suggested next step**: Optionally gate a live Openverse smoke test behind a manual / scheduled CI job; keep the Tier-3 GPU generation a documented manual step on a GPU-capable host. Neither blocks release (both degrade cleanly and the pure-function logic is CI-covered).

#### Hand-offs

##### HO-1 - Stale-duplicate-install / skill-name collision (belongs to the flattening migration)

- **Source phase**: Discovered during the investigation that motivated this plan
- **Reason**: Under `~/.claude/skills/` (and `~/.gemini/...`) a flat skill directory and a category-nested directory can both declare the same `name`, so they collide, and a stale flat copy can shadow the correct one (the original reported bad `/presentify` output came from a stale pre-fidelity flat copy shadowing the v3.12.0 one). Three stale copies were removed manually during this session. The ROOT cause is the skill-flattening install migration (the v3.12.1 cross-platform-adapters work), not this presentify skill.
- **Owner**: the `cross-platform-install-adapters` / flattening migration.
- **Suggested next step**: On install, prune stale / duplicate skill directories (or detect same-`name` collisions across flat and nested layouts) so a re-install cannot leave two same-named skills side by side.

### Deferred to the Phase 5 release-readiness / a browser-capable run

- The rendered visual-QA screenshots for the worked example (WN-1) and the deck-PDF prominence demonstration (WN-2 / MT-1).
