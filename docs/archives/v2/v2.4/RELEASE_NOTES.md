# Nexus-Hub v2.4.0 Release Notes

**Release date**: 2026-06-02
**Type**: Minor (SemVer) - additive, local, zero new outbound calls / credentials / third-party data processors
**Plan**: [adoption-compound-engineering-plugin](plans/adoption-compound-engineering-plugin.md)
**Predecessor**: [v2.3.0](../v2.3.0/RELEASE_NOTES.md)

## Overview

v2.4.0 adopts all 13 in-scope capabilities (A1-A13) from the compound-engineering plugin cross-project comparison and resolves the 15 ingested v2.3.0 known-gaps, as local zero-outbound Nexus-Hub content. The compound-engineering plugin (Every Inc) is the closest structural analog to Nexus-Hub compared to date - both are multi-platform AI-assistant harnesses - so the comparison clustered around a closed knowledge loop (capture solved problems, feed planning), a multi-agent persona review pipeline, and a set of internal-build conveniences. Adoption was sequenced strictly by the MCP Registry Policy decision tree (reverse-engineer-first): skill-native items first (Phases 1-4), then `re-full` internal builds (Phase 5), then `re-partial` internal builds (Phase 6), then the ingested catalog-quality remediation (Phase 7) and the live-verification / release-readiness gate (Phase 8). Every adopted item is local catalog content (markdown skills + re-authored generic agents) or a local script reusing the user's own model CLI and local logs. The vendor-integrated CE skills (Gemini image generation, Slack research, Proof, Riffrec, XcodeBuildMCP) fail the MCP Registry Policy and were dropped (out-of-scope appendix N1-N8). This release also folds in the prior unreleased process-discipline (Superpowers) and Hallmark / HTML-output interim additions committed after the v2.3.0 tag.

The catalog grows to **245 skills across 21 categories** (the prior "23 categories" was an artifact of three mis-cased duplicate category keys, reconciled in Phase 1), with 23 reviewer agents (up from 10), 41 commands, and 22 hooks. The release adds zero new third-party data processors, zero new API keys, and only local tree-sitter grammar dependencies (Ruby / PHP / C / C++) under the existing `<0.26` ceiling.

## Highlights by phase

1. **Foundation: knowledge base + scoring discipline** (A1, A4) - a `solution-knowledge-base` capture skill and a `solution-refresh` lifecycle skill that document and maintain a categorized `docs/solutions/` store, a stdlib-only `validate_solution_frontmatter.py` parser-safety checker (registered in both installers, wired into `make validate`), and a confidence-anchored-scoring reference (5 discrete anchors, fingerprint dedup, cross-reviewer promotion, late confidence gate). Also reconciled the three data registries to the on-disk truth and made the secret scanner fenced-code-aware (closes ingested WN-v23-1 / BG-v23-1).
2. **Persona review pipeline** (A2, A3, A8) - a `multi-agent-code-review` skill (per-diff persona selection, bounded parallel dispatch, merge/dedup, cross-reviewer promotion, late confidence gate, independent validation pass, model tiering, four modes) with a thin `review-changes` command, a `plan-review` skill (persona lenses for plans/specs, read-only), and 13 new language-agnostic reviewer agents under `catalog/agents/`.
3. **Close the compound loop** (A5, A7) - a `product-strategy` STRATEGY anchor and a `session-query` skill (local Claude / Codex / Cursor session-JSONL search, script-first, zero outbound), plus planning / learning / known-gaps skills wired to read the `docs/solutions/` knowledge base as grounding.
4. **Remaining skill-native** (A10, A11) - a crash-safe persistence-discipline section in `skill-eval-loop` (write-then-verify, re-read at phase boundaries, append-only log, crash-recovery markers) and a `product-pulse` report skill (time-windowed product-outcome report from user-supplied local telemetry only).
5. **Internal RE builds (re-full)** (A6, A9) - per-platform capability specs under `docs/specs/<platform>.md` reconstructed from the integration registry, and an installer `--branch` / `-Branch` flag that installs from a pushed branch into a deterministic cache without switching the working copy (default behavior unchanged).
6. **Internal RE builds (re-partial)** (A12, A13) - a `demo-capture` skill + `capture-demo.{py,ps1}` scripts (local GIF / terminal / screenshot capture to `docs/demos/`, upload step deliberately dropped, graceful degradation when a tool is absent), and a `generate_release_changelog.py` script (+ `.ps1`) that derives the next semver bump and a Keep-a-Changelog section from conventional commits (no third-party release Action added).
7. **Catalog-quality + hygiene remediation** (9 ingested gaps) - drove the `--quality` warning count from 576 to 0 across all 245 skills, stripped 15 instruction-template BOMs, converted compliance-review punctuation to ASCII, redacted personal paths in a hook test fixture, removed the orphaned `base-gemini-ide.md` template (and dropped the corresponding Makefile / CI exclusions), broadened CI shellcheck to all `catalog/**/*.sh`, added Ruby / PHP / C / C++ code-search extractors (coverage 6 -> 10, each 100% recall/precision), and lifted the `python_app` code-search precision 70% -> 100%.
8. **Live verification + release readiness** (4 ingested gaps) - ran the final catalog-green gate and recorded dated re-deferrals for the four environment-blocked live-verification gaps.

## Phase 8 in detail (live verification + release readiness)

The release-readiness gate (T040) ran clean on the implementation host: `make validate` exit 0 (orphan-bundle 0/0, quality 0/0, all CI validators exit 0), 1056 tests passed / 4 skipped / 0 failed across every suite (skill-server 43, code-search 187, web-fetch 29, repo-level tests/ 382, catalog/hooks/tests 415), the code-search eval at 100% recall / 100% precision, the three data registries reconciled at 245 skills / 21 categories, and zero new outbound primitives in any new script.

Four live-verification gaps were re-deferred with dated reasons (all acceptable for a source release, recorded in [`docs/archives/v2/v2.4/known-gaps.md`](known-gaps.md)):

- **DF-v24-8** (carries DF-v23-7; subsumes DF-v24-1/2/3/4/6) - live `skill-eval-loop` trigger runs for all new and discipline skills. No model CLI (`claude` / `codex` / `gemini` / `opencode`) on PATH; static trigger-surface checks were done for every skill.
- **DF-v24-9** (carries DF-v23-8) - live eval-harness trigger-techniques run. Same constraint; the v2.3.0 dry-run + pure-logic + fixture-stream tests stand.
- **DF-v24-10** (carries DF-v23-6; subsumes DF-v24-5) - macOS / Linux installer smoke + the live `--branch` clone+install. Windows-only host; Windows is empirically green and the Linux Python suite is green via CI.
- **WN-v24-3** (carries WN-v23-5) - Antigravity CLI live-VM probe. The `agy` binary is not installable on the host; the conventions remain docs-verified.

## Known gaps carried forward

All 13 A-items shipped; all 15 ingested v2.3.0 gaps are resolved (11) or dated-deferred (4). Remaining open items in [`docs/archives/v2/v2.4/known-gaps.md`](known-gaps.md) - the four live-verification re-deferrals above, the remaining code-search language extractors (DF-v24-7), a cosmetic dual-heading redundancy in a subset of skills (WN-v24-2), and a deliberate convention decision (NI-v24-1) - are environment-blocked or low-priority and none is a source-release blocker.

## Upgrade notes

This is an additive minor release. Re-run the installer (`scripts/installer.sh` on macOS/Linux, `scripts/installer.ps1` on Windows) to pull the new skills, agents, commands, references, and scripts into your per-platform config locations and `~/.nexus-hub/`. No migration is required; default installer behavior is unchanged (the new `--branch` / `-Branch` flag is opt-in). No new credentials, environment variables, or outbound network access are introduced.
