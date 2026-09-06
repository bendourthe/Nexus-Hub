# Session History - v3.16.0 Phase 2: Per-platform lever research and verification

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.0-platform-defaults-config.md](../../plans/v3.16.0-platform-defaults-config.md)
**Phase**: 2 of 5 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/platform-defaults-config`
**Outcome**: Complete. All four quality gates passed. One CI defect found and fixed in-phase.

## Goal

Establish, for each of the sixteen registered integrations, whether an official document names a settable install-time behavioral default lever, and record the answer with evidence.

## Result

**12 VERIFIED, 4 UNVERIFIED, 16 total** - matching the integration registry exactly.

| Class | Platforms |
|---|---|
| VERIFIED | `aider`, `antigravity2`, `claude`, `codex`, `copilot`, `cursor`, `gemini-cli`, `hermes`, `kimi`, `openclaw`, `opencode`, `qwen` |
| UNVERIFIED | `antigravity`, `gemini`, `nexus-ai`, `windsurf` |

Surface alignment (a second axis added during the pass, because a documented lever is not the same as a writable one): 7 Exact, 3 Near, 1 Partial (`aider`), 1 Mismatch (`copilot`).

## Sub-tasks completed

### 2.1 - Research

Each platform was researched against its **own** documentation. Where a search returned only secondary sources, the search result was discarded and the vendor's own page was located and fetched instead. No lever was recorded from a blog, forum, aggregator, issue tracker, or analogy.

### 2.2 - Contract

Wrote `docs/policy/platform-defaults-levers.md`, following the shape of the sibling `platform-read-contracts.md`: a summary table, a per-platform detail section, and a re-verification log. The header states the scope boundary (behavioral defaults here; discovery paths and capabilities in the read contract) and the do-not-invent rule with its `.kimi/agent.yaml` precedent.

A **Surface alignment** column was added beyond the plan's specification, because the research surfaced a case the plan did not anticipate: a platform can have a genuinely documented lever that lives on a product surface Nexus-Hub does not integrate. Without that column, `copilot`'s VERIFIED row would read as permission to write `~/.copilot/settings.json`.

### 2.3 - Completeness test

Added `tests/validators/test_platform_defaults_levers.py` (18 cases). The roster is read from `scripts/lib/integrations.list_keys()`, never hardcoded, so a newly registered platform fails until classified.

## Test results

| Suite | Result |
|-------|--------|
| `tests/validators/test_platform_defaults_levers.py` | 18 passed |
| `tests/validators` (full) | 483 passed |
| `validate` guards (7, run individually) | All pass |
| `sync_platform_defaults.py --check` | In sync (Phase 1 machinery unaffected) |

**The tests were checked for vacuity, not just for green.** The parser was run against the real document and confirmed to see 16 rows with an exact registry match and the expected 12/4 split, and the load-bearing do-not-invent assertion was fed an UNVERIFIED platform to confirm it actually fails. A completeness test that passes because its regex matched nothing would be worse than no test.

## Findings worth carrying

1. **Codex was the rule's first real test.** Every search returned a blog, a cheat sheet, an aggregator, or a GitHub issue, all confidently quoting the same key names. The recorded row instead comes from OpenAI's own configuration reference, reached through two documented 308 redirects.
2. **Three vendor doc hosts had moved.** Claude 301s to `code.claude.com`; OpenAI Codex 308s to `learn.chatgpt.com`; `docs.windsurf.com` 307s to `docs.devin.ai`. The last is first-hand confirmation of the Cognition rebrand that AGENTS.md currently records as third-party reporting. Redirect-following is now written into the contract's re-verification instructions.
3. **`gemini` and `gemini-cli` share `~/.gemini`.** The lever verified for the CLI was deliberately not transferred to `gemini`, and the shared home is logged as a single-owner requirement for Phase 3 (NI-3).
4. **Two platforms document half a lever.** `antigravity2` has an autonomy policy but no model or effort key; `cursor` has `approvalMode` but explicitly no config-file default-model mechanism. Both are recorded as VERIFIED for what they document and silent on the rest.
5. **Kimi closed the loop on its own precedent.** The fabricated `.kimi/agent.yaml` was dropped in v3.15.0; the real documented lever is a TOML config at `~/.kimi-code/`, exactly the path v3.15.0 migrated to. The invented file was wrong and the correct one was findable by reading the vendor's docs.

## Troubleshooting trail

- **A CI hole was found at post-phase step 8.3 and fixed in-phase (QG-1).** `ci.yml`'s `paths-ignore: ['docs/**']` meant a push touching only `docs/policy/` skipped CI, so the completeness test would never run on the edit it exists to guard. The premise in the comment was true when written and had become false once `docs/policy/` became validator input.
- **The first fix drafted for that hole was invalid.** Adding `- '!docs/policy/**'` to the existing `paths-ignore` looks correct and is not: GitHub Actions supports `!` in `paths` only, never in `paths-ignore`, and the two filters cannot both be set for one event. Verified against GitHub's workflow-syntax documentation before applying. The applied fix switches both triggers to `paths: ['**', '!docs/**', 'docs/policy/**']`.
- **A CHANGELOG edit misplaced a section boundary.** Inserting the Phase 2 entry left Phase 1's `Added` bullet sitting under `Fixed`. Caught by re-reading the rendered section rather than trusting the edit, and repaired by reordering.

## Deviations from the plan

- **Added a Surface alignment column** beyond the plan's specified fields (classification, lever keys, URL, statement, date). Justified above: without it, VERIFIED reads as permission to write.
- **Fixed the CI hole in-phase** rather than deferring it to Phase 5's CI/CD pass, at the maintainer's direction. It is pre-existing and affects the read-contract guards too.

## Known gaps appended

QG-1 (closed in-phase), NI-2 (`copilot` surface mismatch), NI-3 (`~/.gemini` shared home), NI-4 (the four UNVERIFIED platforms awaiting a Phase 5.2 disposition), plus five observations. Recorded in [docs/releases/v3/v3.16/known-gaps.md](../../known-gaps.md).

## Next steps

**Phase 3 - Wire the verified levers into the defaults and their consumers.** Declare each VERIFIED lever in `configs/platform-defaults.json` and make its platform's real write surface consume it. Three constraints from this phase gate that work, and all three are recorded in the contract's closing section: a VERIFIED classification is permission to *consider* a platform rather than to write a file (`copilot` is Mismatch); a key the vendor does not document must not be seeded from a sibling platform's shape (`antigravity2` and `cursor` each document only part of a lever); and `~/.gemini/settings.json` must be owned by exactly one platform id.
