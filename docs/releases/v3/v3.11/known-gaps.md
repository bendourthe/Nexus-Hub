# Known Gaps - v3.11

**Project**: Nexus-Hub
**Status**: release-ready (pending `/update release` commit / merge / tag / push)
**Last updated**: 2026-07-08

## v3.11.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 6 |
| Deferred (DF) | 6 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 2 | 1 |
| Missing tests / coverage gaps (MT) | 0 | 0 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - Residual live-verification gaps (external platform contracts)

- **Source phase**: Phase 7 (7.1 audit, residual gaps D1-D7)
- **Plan reference**: `docs/v3/v3.11/platform-read-contracts.md` (Residual live-verification gaps)
- **Reason**: These contracts depend on the current external platform's behavior and cannot be confirmed from the repo alone. The 7.4 `verify` and 7.5 CI smoke now REPORT/CATCH the resulting surfacing gaps, but the underlying external contracts still want a live probe.
- **Suggested next step**: Live-probe per platform: Codex prompt read path + format (D1) and skills discovery (D2); Antigravity 2.0 root-vs-`.agents/` instruction file (D3), exact global subpath (D4), `subagents`/`rules` consumption (D5), `.agents` vs `.agent` (D6); Cursor/Copilot global slash surfaces (D7); and whether `nexus-hub init` (the launcher) passes the `init` subcommand through (the on-open hook calls it fail-open). Feed results back into codex.py / antigravity.py.

#### Warnings

##### WN-2 - Windows MAX_PATH risk when seeding Antigravity `.agents/skills/` into a deep target

- **Source phase**: Phase 7 (7.3 auto-seed / 7.4 verify smoke)
- **Plan reference**: 7.3
- **Reason**: The Antigravity `.agents/skills/<name>/references/examples/...` flattened copy can exceed the Windows 260-char MAX_PATH when the target repo lives at a very deep path (observed with the OneDrive + deep-temp scratch dir during the 7.3 smoke; `shutil.copytree` raised WinError 3). A normal-depth repo is well under the limit.
- **Suggested next step**: Consider enabling Windows long-path support in the copytree (prefix `\\?\`) or shortening the deepest bundled skill paths; low severity - most repos are far under 260 chars, and the auto-seed is fail-open.

##### WN-3 - Windows-local verification residuals (full integrations/installer suite + README_zh prose)

- **Source phase**: Phase 8.6 (final verification)
- **Plan reference**: Phase 8.6
- **Reason**: (a) The full `tests/integrations` + `tests/installer` pytest suites are subprocess-heavy and time out on the Windows dev host (the same class as the bash-cannot-run WN-v36-1 constraint); only comment/docstring lines in those trees changed this phase (no behavioral change) and the one functionally-affected test (`test_installer_smoke.py`, 28 tests asserting the migrated `docs/archive/v0/v0.9/opus-4-7-migration.md` path) passes, so behavior is unchanged - but the full cross-suite run is proven on CI (Linux), not locally. (b) `README_zh.md` had its archive path references repaired but its Chinese catalog-count prose was not re-counted to 263 (it is not a `check_version_sync.py` surface and the plan scoped the prose update to `README.md` / `AGENTS.md`).
- **Suggested next step**: (a) Let the CI `tests` job (Ubuntu) run the full integrations/installer suite on the release push; (b) sync `README_zh.md` catalog counts to 263 in a follow-up docs pass.

## Resolved

| ID | Title | Resolved in | Notes |
|---|---|---|---|
| NI-1 | Phase 7.2 Codex delivery fix | Phase 7.2 (commit 3d18564) | codex.py documents that Codex surfaces via AGENTS.md SKILL_INDEX + prompts; agents/rules intentionally not created (no dead dirs). Prompt read-path live probe remains under DF-1. |
| NI-2 | Phase 7.3 project auto-seed + on-open hook (the reported bug) | Phase 7.3 (commit 61a405f) | Global install from inside a repo seeds .agents/{workflows,skills,rules} + Cursor + Claude stub; opt-in on-open hook shipped; smoke-verified. |
| NI-3 | Phase 7.4 post-install doctor/verify | Phase 7.4 (commit 2ed4646) | `runner.py verify` reports PASS / NEEDS-ACTION per platform; wired into both installers; 4 unit tests. Caught the Antigravity project-surface gap on the dev machine. |
| NI-4 | Phase 7.5 cross-platform CI install-smoke | Phase 7.5 (commit 1959688) | `install-smoke` job (ubuntu + gated macOS/Windows) asserts read-paths + auto-seed; workflow concurrency added. |
| NI-5 | Phase 8 remainder: archive normalization + cleanup + CI opt + v3.11.0 release | Phase 8.2-8.6 | 8.2: archive normalized to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/` (164 `git mv` moves, zero collisions, 1028 references repaired; only CHANGELOG retains legacy paths). 8.3: `project-refactor` detectors run - repo already clean (no empty dirs, no genuine dupes/orphans/overcomplication). 8.4: CI optimized (concurrency on both workflows, `paths-ignore: docs/**`, `cache: 'pip'` on validate+tests, expensive OS legs gated). 8.5: version bumped to 3.11.0 across all 6 surfaces (`check_version_sync.py` clean), CHANGELOG `[3.11.0]` entry added, manifest regenerated, catalog prose reconciled to 263 skills. 8.6: full validator set green incl. compression eval. |
| NI-6 | Phase 7 secondary distribution defects (C1/C2/C3/C6/C7) | Phase 7 (commits 3d18564, 2b545d5) | Gemini full-mirror parity (C1/C2); Codex config alignment (C5); Copilot SKILL_INDEX via registry (C6) + spec fix (C7); Antigravity 1.0 deprecation documented (C3). |
| WN-1 | Extension-local compression eval not run in this environment | Phase 8.6 | `cd extensions/nexus-context-compressor && python -m evals --check` ran green in the Phase 8.6 verification (CCR 100.0%, signatures 100.0%, reduction 45.8%). The full validator set now passes locally. |

## Comparison Declines - offensive-meta-harness comparison (2026-07-08)

The adoption-t3mp3st cycle (`docs/v3/v3.11/plans/adoption-t3mp3st.md`, operationalizing [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-t3mp3st.md](comparisons/v3.11.0-comparison-t3mp3st.md)) adopted only three defensive, body-only items (C1 local-agent-hijack recognition, C2 benchmark-receipt discipline, C3 dangerous-action approval gate). The source is an offensive-security meta-harness, so the overwhelming majority is declined by construction, not built. Recorded here so the next planning cycle does not re-propose them; each is described generically by function with the grounds cited by name.

- **Autonomous exploitation runtime / offensive meta-harness** - declined. Grounds: MCP Registry Policy (no shipped runtime or daemon; the v3.10.0 ruflo standalone-loop-runtime precedent), and offensive by construction against this environment's defensive safety posture.
- **Autonomous multi-agent attacker swarm + command-and-control phase** - declined. Grounds: offensive multi-agent exploitation and unauthorized C2 are refused under the safety posture.
- **Arsenal of offensive tooling** - declined. Grounds: weaponized tools carry no per-use authorization context in a distributed catalog (refusal grounds); defensive scanning is already covered by the AppSec skills (`dependency-security-audit`, `security-review`, and peers).
- **Detection-evasion engine and OPSEC evasion controls** - declined. Grounds: detection evasion is explicitly refused; the defensive mirror (detection engineering, threat hunting) already lives in the `security-operations` family.
- **Keyless local-agent-hijack credential mechanism** - declined as a capability. Grounds: it is a confused-deputy credential proxy (MCP Registry Policy hard-no on credential-proxy classes). Adopted here only as the threat modeled defensively in Phase 1 (`prompt-injection-defense` recognition + `agent-access-policy` containment).
- **Runtime service surfaces (multi-provider LLM router, HTTP API server, hosted web dashboard, reconnaissance MCP server)** - declined. Grounds: runtime / daemon / hosted-UI / outbound classes (MCP Registry Policy, ruflo precedent). The routing doctrine is already covered in spirit by the `multi-provider-ai` and `model-routing` skills without a shipped service.

**Deferred optional item (not a decline)**: the pentest report-type taxonomy (executive / technical / findings-only, comparison candidate C5) is adoptable into `pentest-reporting` on explicit maintainer request only; it is neither offensive nor policy-blocked, just out of scope for this defensive cycle.

## adoption-spec-kit third cycle (2026-07-08)

Operationalizes [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-spec-kit.md](comparisons/v3.11.0-comparison-spec-kit.md) (candidates S1-S8). The recommended bucket (S1-S7) shipped; the following are deferred or recorded.

### Deferred

- **DF-v311-speckit-S8 - monorepo member-project targeting for `nexus-hub init`** (Low). The source supports targeting a specific member project inside a monorepo; Nexus-Hub's `nexus-hub init` seeds the current repo root. Deferred for lack of demand while `--workspace` already covers non-root targets. Next step (from the comparison): add an optional path argument to `nexus-hub init` that scopes seeding to a sub-project directory, only if monorepo users request it.
- **DF-v311-kimi-refresh - Kimi Code CLI project-local convention refresh** (Low; from Phase 3). Kimi migrated to Kimi Code CLI (Node.js rewrite); the legacy `~/.kimi/` layout `kimi.py` writes is preserved and coexists (vendor migration guide), so no rewrite was made. Next step: confirm the exact Kimi-Code-CLI project-local convention from vendor docs and refresh `kimi.py` if it diverges, keeping backward compatibility. Evidence: [docs/releases/v3/v3.11/development/roster-verification.md](development/roster-verification.md).

### Carried forward from v3.10.0 (reviewed, remain deferred)

The three open v3.10.0 items were reviewed and neither block nor intersect this cycle; they carry forward unchanged (full text in [docs/releases/v3/v3.10/known-gaps.md](../v3.10/known-gaps.md)):

- **DF-v310-ruflo-A6** (Low) - optional quality-gate-naming note; skipped, the function is already delivered by `/plan` -> `/implement` -> `/spec` + `quality-gate-definitions`.
- **DF-v310-ruflo-P4-extensions** (Low) - `nexus-hub verify` manifest excludes `extensions/` MCP-server sources (their pip install has its own integrity).
- **DF-v310-ruflo-A10-rest** (Low) - the remaining background-worker check ideas were not adopted as always-firing hooks (noise-prone or covered elsewhere).

### Notes

- **Agent-disclosure divergence (deliberate, not a gap)**: upstream spec-kit guidance recommends disclosing agent authorship in commits and PR comments. This directly conflicts with this repo's no-AI-attribution commit convention (global CLAUDE.md), so it is a recorded, deliberate divergence, not an omission.
- **Pre-existing branded-token references**: `catalog/skills/workflow/tasks-to-issues/SKILL.md`, its `data/skills.json` entry, the `cross-artifact-analyzer` entry, and `scripts/installer.{sh,ps1}` carry pre-existing references to the archived `adoption-spec-kit.md` plan filename (they document the strict `T###` task-line format that originated there). These predate this cycle and are internal-provenance path references, not product-name attribution; this cycle added zero new branded tokens to any distributed artifact.

## Comparison Declines - personal skill-pack comparison (2026-07-08)

The adoption-davidondrej-skills cycle (`docs/v3/v3.11/plans/adoption-davidondrej-skills.md`, operationalizing [docs/releases/v3/v3.11/comparisons/v3.11.0-comparison-davidondrej-skills.md](comparisons/v3.11.0-comparison-davidondrej-skills.md)) adopted three items (C2 research-brief technique in `prompt-engineering`, C3 opt-in grill-me mode in `idea-refine`, C1 the `youtube-transcript` skill). The rest of the 28-skill source pack was declined; recorded here so the next cycle does not re-propose them, each described generically by function.

- **Paid scraping-and-email endpoint skill + paid deep-research skill** - declined. Grounds: MCP Registry Policy hard-no on scraping-as-service and research-as-service; the research workflow is already delivered by `/research` and its harness.
- **Model-benchmark-via-third-party-router skill** - declined. Grounds: vendor-bound and niche (tied to a specific external model router); no general Nexus-Hub value.
- **Prompt-rewriting / guardrail-evasion skill** - declined. Grounds: its purpose is to weaken server-side safety classifiers on dual-use topics, contrary to Nexus-Hub's defensive posture and safety refusals.
- **Tool-bound set (a terminal-multiplexer integration, two personal-agent skills, a vendor goal-loop feature doc)** - declined. Grounds: they target external stacks Nexus-Hub does not support; the transferable goal-loop pattern is already covered by `loop-engineering`.

**Deferred optional items (not declines)**: a guided setup walkthrough, a folder-scoped context-file helper, and a read-all-ADRs loader were rated low value; adoptable only on explicit maintainer request. Generic naming per the Reverse-Engineering Attribution Rule (no upstream product or author named).
