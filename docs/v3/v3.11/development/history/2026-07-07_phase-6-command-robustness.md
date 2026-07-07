# Session History - v3.11.0 Phase 6: Command robustness (compare source-security + presentify visual-QA)

**Date**: 2026-07-07
**Plan**: `docs/v3/v3.11/plans/v3.11.0-workflow-governance-refinements.md`
**Phase**: 6 of 8 - Command robustness
**Status**: Complete (stability gate PASS)

## Goal

`/compare` scans every source for prompt injection, malicious instructions, and supply-chain risk BEFORE ingesting it, and writes reports to `docs/<version>/comparisons/`; `/presentify` opens its generated HTML, visually assesses it for graphic defects, and iterates until the output is clean and shareable.

## What changed

### 6.1 - Mandatory source-security scan in `/compare`

- `cross-project-comparison/SKILL.md`: added a new MANDATORY "Step 1.5: Source Security Scan" before Step 2 (Inventory). It scans the source (cloned/fetched repo, article HTML, or local path) BEFORE ingestion for prompt injection / embedded agent-directed instructions (delegating to `[[prompt-injection-defense]]`), malicious or destructive code, and supply-chain risk (reusing `[[skill-security-scan]]` / `nexus-skill-scanner` when the source is a skill, and `[[egress-redaction]]`), emitting a CLEAR / PROCEED-WITH-CAUTION / BLOCK verdict; BLOCK stops before ingesting. Added a Verification checkbox and made explicit that Step 1.5 (pre-ingest) does not overlap Step 5 (post-ingest adoption assessment).
- `compare.md`: documented the mandatory pre-ingest source-security scan alongside the existing Security / Reverse-Engineering assessment note, and in the intro paragraph.

### 6.2 - Comparison output under `comparisons/` (release-prefixed)

- `compare.md`: comparison report path is now `docs/v<MAJOR>/v<MAJOR>.<MINOR>/comparisons/v<MAJOR>.<MINOR>.<PATCH>-comparison-<name>.md` (release-prefixed; create the `comparisons/` subdir if missing).
- `implementation-plan/SKILL.md`: the from-comparison ingest reads from `<version_dir>/comparisons/` (glob `*-comparison-<name>.md`) and writes the release-prefixed `<version_dir>/plans/v<MAJOR>.<MINOR>.<PATCH>-adoption-<name>.md`.
- `markdown.md`: the comparison-reports example path aligned to the release-prefixed `comparisons/v<MAJOR>.<MINOR>.<PATCH>-comparison-*.md` glob.
- `plan.md` line 17 (bare `*.md` comparison-report routing) still resolves - a release-prefixed comparison report is a `*.md` path - so no change needed there.

### 6.3 - Visual-QA loop in `/presentify`

- `document-to-interactive-html/SKILL.md`: added Step 7 "Visual-QA loop (render, screenshot, assess, iterate)" after the static Step 6 verify - render in a headless browser, screenshot key states (chart, table, navigated section, mobile viewport), read the screenshots back to catch graphic defects (overflowing tables, broken animations, unreadable text, clipped/misaligned elements, charts that fail to draw, layout breakage), fix and re-render up to 3 passes, then report issues fixed. Delegates render/screenshot to `[[browser-testing-with-devtools]]`, stays offline, and degrades gracefully to a static structural review when no headless browser is available (never hard-fails). Added a matching Verification checkbox.
- `presentify.md`: the Delegation note now ends with the post-generation visual-QA loop and its graceful-degradation path.

## Verification

- Source-security detection dogfooded on a fixture: a dirty repo with a planted prompt-injection string in a README (inside an HTML comment) yielded BLOCK with the exact finding; a clean repo yielded CLEAR - proving the Step 1.5 pattern-based pre-ingest scan is implementable.
- Comparison-path consistency confirmed across `compare.md`, `implementation-plan/SKILL.md`, and `markdown.md` (all now `comparisons/` + release-prefixed).
- `validate_skills.py --bundles-only`: PASS (0 errors). `--quality`: PASS (0 errors). `validate_unicode_safety.py`: 0 errors. `check_version_sync.py`: clean at 3.10.3.

## Notes and environment caveats

- `document-to-interactive-html` "fails" a naive `yaml.safe_load` of its frontmatter on a PRE-EXISTING `SKIP:` colon-space in its `description` (line 3, not touched this phase) - the same lenient-real-validator situation seen earlier with `git-branching-workflow`. The real gate (`validate_skills.py`, run by `make validate`) extracts the description leniently and passes; my Phase 6 edits were to the body (Step 7 + Verification), not the frontmatter.
- The `/presentify` visual-QA loop and the `/compare` full run are skill procedures; full "run it" verification of the headless render is environment-dependent (a browser may be absent, which is exactly the graceful-degradation path). The detection mechanics (source-security scan) are proven on the fixture; the visual loop's presence, delegation, and degradation are verified in the skill text.
- `make` unavailable on this Windows host; gates run individually. Extension-local compression eval not run (untouched by Phase 6).

## Next steps

- Phase 7: Cross-platform distribution robustness - the Codex/Antigravity fix that motivated this whole cycle (per-platform read-contract table, Codex delivery fix, project-surface auto-seed + on-open hook, post-install `nexus-hub doctor`, cross-platform CI install-smoke). Edits both installers, so it will pause at the AGENTS.md "ask first" gate.
- Phase 8: Nexus-Hub self-application (dogfood) + the v3.11.0 version bump.
