# Session History - v2.3.0 Phase 9: Live-environment verification

**Date**: 2026-05-29
**Plan**: [docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md](../../plans/adoption-ecc-cybersec-skills.md)
**Phase**: 9 of 9 (FINAL) - Live-environment verification
**Sub-tasks**: T032 (WN-2), T033 (WN-3), T034 (WN-4), T035 (WN-8), T036 (stabilization)
**Outcome**: All four ingested v2.2.0 carryover gaps closed; release-readiness workflow triggered.

## Goal

Verify the four deferred v2.2.0 assumptions that required a live environment: the Antigravity CLI binary name (WN-2), workflow file format (WN-3), and workflow frontmatter / name derivation (WN-4), plus a cross-OS installer smoke on macOS and Linux (WN-8). The plan's T036 explicitly allowed resolving these with live evidence OR re-deferring with a dated reason if Google had not yet shipped a verifiable channel.

## Steps taken

1. **Plan + context resolution**: confirmed Phase 9 is the final phase (numerically last, prior phases 1-8 all `[x]`, session-history present for each), so `is_final_phase = true` and the release-readiness workflow runs after the post-phase sequence. Read the v2.3.0 + v2.2.0 known-gaps, the antigravity-cli-probe, and the v2.2.0 installer-smoke-post to scope WN-2/3/4/8.

2. **Environment probe**: confirmed this host is Windows 11 (no macOS/Linux host), Python 3.12.10, on `main`, working tree clean (Phases 1-8 committed at 6b946ce). Probed for the `antigravity` binary -- NOT FOUND on this host (no live Antigravity CLI install available).

3. **Antigravity CLI documentation verification (WN-2/3/4)**: since no live install was available, verified against Google's now-public Antigravity CLI documentation + official codelabs (the binary is on a verifiable channel ahead of the 2026-06-18 cutover). Cross-checked the official `antigravity.google/docs` pages (SPA, content via search extraction), two official Google Codelabs (server-rendered, verbatim quotes), and several practitioner guides.

4. **Findings + scope decision**: the docs CORRECTED several v2.2.0 INFERRED values -- binary `agy` (not `antigravity`), `.agents/` per-project dir (not `.agent/`), `AGENTS.md` instruction file (not `AGENT.md`), `~/.gemini/antigravity-cli/` global (not `~/.agent/`). Because this rewrites a working, smoke-tested integration on docs-only (not live-install) evidence and touches the installer scripts (an AGENTS.md "ask first" item), the scope was taken to the user, who chose the full rewrite including the global-dir restructure, the CI-Linux + defer-macOS handling for WN-8, and a full release including tag creation.

5. **Applied the corrections**: `scripts/lib/integrations/antigravity.py` (config + docstrings), `catalog/hooks/antigravity-cli-diff-review.sh`/`.ps1` (binary `agy`), `templates/ai-instructions/base-antigravity-20.md` + `base-antigravity-cli.md`, `scripts/installer.sh` + `scripts/installer.ps1` (legacy mirror paths, lockstep), `AGENTS.md`, `README.md`, and the three antigravity integration test files.

6. **WN-8 cross-OS smoke**: ran the Windows smoke (installer -Help/-PrintConfig probes + the full pytest suite + eval) and recorded CI's ubuntu-latest run as empirical Linux test-suite evidence; re-deferred macOS + the Linux installer-probe/eval portion with a dated reason. Wrote `docs/archive/v2/v2.3/installer-smoke-post.txt`.

7. **Documentation**: updated `docs/archive/v2/v2.2/antigravity-cli-probe.md` (new Section 11 verification record, WN-2/3/4 marked resolved-via-docs with residuals), `docs/archive/v2/v2.3/known-gaps.md` (WN-2/3/4/8 -> Resolved, two new residual gaps), DEVLOG, README.

## Troubleshooting

- **SPA docs not readable by WebFetch**: the official `antigravity.google/docs/cli-using` page is JavaScript-rendered and returned only a header shell. Worked around by using the search engine's content extraction and the server-rendered Google Codelabs for verbatim quotes.
- **Conflicting official sources**: one codelab ("Getting Started with Antigravity Skills") showed `.agent/` (singular) while the pipelines codelab + practitioner guides showed `.agents/` (plural). Resolved by weight of evidence (`.agents/`) and recorded the dissent as a live-VM residual (WN-v23-5) rather than treating it as settled.
- **codex/antigravity2 root-AGENTS.md collision**: the docs say `agy` reads a project-root `AGENTS.md`, but that file is already managed by the `codex` integration via the single shared `## Nexus-Hub` marker. Pointing antigravity2 at the root file too would clobber the block (a real install-time regression). Kept antigravity2's instruction file at `.agents/AGENTS.md` and recorded the root-vs-subdir question as a residual.
- **nexus-web-fetch collection errors**: 3 errors on first run were a `ModuleNotFoundError` (the extension was not `pip install -e`'d in this shell), not a regression; after the same editable install CI performs, all 29 tests pass.

## Assumptions

- The Antigravity CLI on-disk conventions documented publicly on 2026-05-29 match the shipping binary's behavior (docs-verified, not live-VM-verified). Four residuals (WN-v23-5) await a live `agy` probe.
- v2.3.0 ships as a source release, so the macOS full smoke and Linux installer-probe/eval portion (DF-v23-6) are acceptable deferrals until a packaged-binary release.

## Testing results

- Windows: 936 pytest cases pass (catalog/hooks 392+3 skipped, integrations+installer 260, validators 44, skill-server 43, code-search 168+1 skipped, web-fetch 29); eval recall 100% / precision 96.2% (reproduces `docs/archive/v2/v2.3/eval-baseline.md`); installer -Help/-PrintConfig probes exit 0 (negative case exits 1).
- Linux: Python test suite empirically green via CI (`.github/workflows/ci.yml`, ubuntu-latest).
- `make validate` equivalent: green (skills.json 227, bundle audit 0/0, 4 CI validators rc=0).
- Lint: shellcheck `--severity=warning` clean on the edited hook + installer.sh; `bash -n` clean; PowerShell `Parser::ParseFile` clean on installer.ps1 + the .ps1 hook.
- Antigravity integration tests: 20 pass (the 3 updated files).

## Next steps

- Run the v2.3.0 release-readiness workflow (9A-9E): resolve/record gaps, verify tests/CI, run docs/project refactor audits + update-* checks, bump the version to v2.3.0, draft release notes, and create the annotated `v2.3.0` tag.
- Before any v2.3.0-tagged packaged-binary release: run the macOS full smoke + the Linux installer-probe/eval portion (DF-v23-6).
- When the `agy` binary is broadly installed (around the 2026-06-18 cutover): run a live probe and reconcile the four Antigravity residuals (WN-v23-5).
