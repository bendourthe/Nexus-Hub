# Known-gaps triage, group C (v3.11 to v3.14, v3.17 to v3.21)

Repository: `Nexus-Hub-worktrees/v41310` (branch `feat/v4.13.10-training-page-rebuild`), read-only, 2026-10-08.

**Counts**: RESOLVED 17 | OBSOLETE 3 | QUICK 2 | PLAN 41 | total 63

## Why these 63 still read as open

Every source ledger (`docs/archives/v3/v3.<n>/known-gaps.md`) already states `**Open items**: 0` and ends with an `Archive reconciliation - 2026-09-29` table. `minor_close.py status` still lists the entries because of how their headings are written:

- The parser (`scripts/completion_minor.py:1036-1043`) honors only ` - MIGRATED to vX.Y.Z` or a trailing ` - RESOLVED|CLOSED [date]`.
- Headings such as `- MIGRATED to v4.13 (AR-18)`, `(RESOLVED in Phase 4.3)`, `- CLOSED earlier in this file`, `ACCEPTED ...` and `CHECKED ...` match neither form.

44 of the 63 were folded into `AR-xx` entries in `docs/releases/v4/v4.13/known-gaps.md` (section "Migrated from archived minors"). Each of those is classified below by the current state of its AR obligation, checked against the tree.

## Triage table

| Gap | Source file | One-line summary | Class | Evidence or fix | Files |
|---|---|---|---|---|---|
| v3.11#DF-1 | docs/archives/v3/v3.11/known-gaps.md:28 | Live verification of external platform read contracts (D1-D7, init launcher) | PLAN | The launcher part is resolved (AR-01 RESOLVED 2026-09-30, `tests/installer/test_init_cli.py`). D1-D4 and D6 are covered by `docs/policy/platform-read-contracts.md`. The D5/D7 residuals (AR-36) still need an authenticated live read-back. | docs/policy/platform-read-contracts.md |
| v3.11#WN-2 | docs/archives/v3/v3.11/known-gaps.md:37 | Windows MAX_PATH when seeding Antigravity skills into a deep repo | PLAN | AR-11. `scripts/lib/integrations/base.py:443` still calls plain `shutil.copytree`. Fixing it changes a shared copy helper and needs a deep-path repro on Windows. | scripts/lib/integrations/base.py |
| v3.12#DF-1 | docs/archives/v3/v3.12/known-gaps.md:29 | PDF text/figure interleaving is approximate | PLAN | AR-18. The limit is unchanged. The maintainer must accept it by decision or schedule a fix. | presentify extractor |
| v3.12#DF-2 | docs/archives/v3/v3.12/known-gaps.md:36 | Caption text duplicated in page paragraph text | PLAN | AR-18. Unchanged. Dedup risks dropping content, so it needs a design decision. | extract_content.py |
| v3.12#DF-3 | docs/archives/v3/v3.12/known-gaps.md:43 | OCR table recovery is geometry-only | PLAN | AR-18. Unchanged. Accept-or-schedule decision. | presentify extractor |
| v3.12#DF-4 | docs/archives/v3/v3.12/known-gaps.md:50 | No video/audio embedding | PLAN | AR-18. Out of scope by the offline single-file design; needs an explicit accept decision. | - |
| v3.12#DF-5 | docs/archives/v3/v3.12/known-gaps.md:57 | No brand custom-font embedding | PLAN | AR-18. No `@font-face` embed path exists in `document-to-interactive-html/scripts/`. This is a feature (opt-in base64 embed). | presentify builder |
| v3.13#DF-1 | docs/archives/v3/v3.13/known-gaps.md:44 | `.gitignore` matching is best-effort | PLAN | AR-18. `extract_content.py:2426` still skips `!` negation lines. Accept-or-schedule decision. | extract_content.py |
| v3.13#DF-2 | docs/archives/v3/v3.13/known-gaps.md:50 | Minimal in-house Markdown parser | PLAN | AR-18. Unchanged by design (stdlib only). Accept decision. | extract_content.py |
| v3.13#DF-3 | docs/archives/v3/v3.13/known-gaps.md:56 | No secret redaction on the presentify repo walk | PLAN | AR-03 (security). Still no redaction or egress hook under `document-to-interactive-html/scripts/`. This is a design task: route the walk through egress-redaction rules. | presentify scripts |
| v3.13#DF-4 | docs/archives/v3/v3.13/known-gaps.md:62 | No video/audio embedding (carried) | PLAN | AR-18. Same as v3.12#DF-4. | - |
| v3.13#DF-5 | docs/archives/v3/v3.13/known-gaps.md:67 | No brand web-font embedding (carried) | PLAN | AR-18. Same as v3.12#DF-5. | presentify builder |
| v3.13#DF-6 | docs/archives/v3/v3.13/known-gaps.md:72 | No Coverr/Mixkit fetch; video only via Pexels | PLAN | AR-18. `fetch_stock_media.py:33,91-92` still degrade them. Adding them needs external APIs. | fetch_stock_media.py |
| v3.13#WN-1 | docs/archives/v3/v3.13/known-gaps.md:80 | No browser visual QA of the v3.13 samples | PLAN | AR-19. Needs a browser-capable rendered QA session. | - |
| v3.13#MT-2 | docs/archives/v3/v3.13/known-gaps.md:100 | Live Tier-2 fetch and Tier-3 GPU generation not in CI | PLAN | AR-19. Needs live network, a Pexels key, and a GPU host. | CI workflow |
| v3.14#DF-1 (v3.14.5) | docs/archives/v3/v3.14/known-gaps.md:63 | Workspace-scope install output not grouped like the global install | PLAN | AR-20. `scripts/installer.sh` calls the grouping only in `install_global` (lines 1470, 1640), not in `install_workspace` (1893). Installer edits are ask-first, and the distribution handbook evidence binds the installer bytes (AR-58). | scripts/installer.sh, scripts/installer.ps1 |
| v3.14#DF-3 (v3.14.5) | docs/archives/v3/v3.14/known-gaps.md:77 | Stale "legacy installer copy blocks" framing | QUICK | AR-31. Rewrite the "Original 4" bullet so it says Claude has the one bespoke installer block and every other platform installs through the integration registry. The file is not handbook-bound. | docs/specs/README.md:22 |
| v3.14#MT-1 (v3.14.5) | docs/archives/v3/v3.14/known-gaps.md:102 | Usage-monitor webview UI is host-only | PLAN | AR-32. Needs a `@vscode/test-electron` harness or a live VSIX render. | extensions/*-usage-monitor |
| v3.14#DF-1 (v3.14.4) | docs/archives/v3/v3.14/known-gaps.md:148 | Codex extension `icon.png` is a reconstruction | PLAN | AR-32. Needs the user's original `codex-2048x2048.png`, or a maintainer accept. | extensions/codex-usage-monitor/icon.png |
| v3.14#MT-1 (v3.14.4) | docs/archives/v3/v3.14/known-gaps.md:162 | Claude extension UI orchestration is unit-test-light | PLAN | AR-32. `extension.ts`, `warningView.ts` and `recommendations.ts` still have no tests. This is multi-file test work. | extensions/claude-usage-monitor/test/ |
| v3.14#MT-1 (v3.14.3) | docs/archives/v3/v3.14/known-gaps.md:252 | No direct test for the strict-YAML frontmatter gate | QUICK | AR-08. No test references `validate_frontmatter_strict_yaml` (`scripts/validate_skills.py:170`). Add a test that feeds one good and one broken frontmatter block (an unquoted `description:` containing `: `) and asserts the error list. | tests/validators/test_validate_skills.py |
| v3.14#QG-1 (v3.14.3) | docs/archives/v3/v3.14/known-gaps.md:261 | tests/skills/ was not CI-gated | RESOLVED | The entry body records the fix in Phase 4.3. The current gate is `scripts/ci/profiles.py:290` `_pytest("repo-tests-skills", "tests/skills")`. | - |
| v3.14#WN-1 (v3.14.2) | docs/archives/v3/v3.14/known-gaps.md:300 | 8 skills fail the 250-char description cap | PLAN | AR-06. `scripts/validate_skills.py:58` is still `DESCRIPTION_MAX_CHARS = 250`. The maintainer must decide the cap or the allowlist. | scripts/validate_skills.py, allowlist |
| v3.14#DF-3 (v3.14.0) | docs/archives/v3/v3.14/known-gaps.md:374 | Optional provider failover/settlement reference for multi-provider-ai | PLAN | AR-35. `multi-provider-ai/` has no `references/`. The maintainer decides write or won't-do. | catalog/skills/ai-development/multi-provider-ai/ |
| v3.14#BG-1 (v3.14.0) | docs/archives/v3/v3.14/known-gaps.md:390 | verify_platform_contracts.py not registered in installers | RESOLVED | Added to `DEV_ONLY_SCRIPTS` (`catalog/hooks/tests/test_installer_smoke.py:660`). | - |
| v3.14#MT-1 (v3.14.0) | docs/archives/v3/v3.14/known-gaps.md:399 | Extension UI modules have no automated tests | PLAN | AR-32. Same residual as the other MT-1 rows. | extensions/claude-usage-monitor |
| v3.14#QG-1 (v3.14.0) | docs/archives/v3/v3.14/known-gaps.md:408 | claude-usage-monitor not exercised in CI | RESOLVED | `.github/workflows/claude-usage-monitor.yml` exists (compile plus Vitest). | - |
| v3.14#HO-1 (v3.14.0) | docs/archives/v3/v3.14/known-gaps.md:417 | Flat/nested name collision for review-trapdoors | RESOLVED | The Phase 6.4 dry-run install is recorded in the entry. The installers delete legacy nested category dirs (commit `13f333d9f`). | - |
| v3.17#NI-1 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:66 | ci-required aggregate is a single point of failure | RESOLVED | Accepted by design, with no action named. The mitigation exists: `.github/workflows/ci.yml:827` and `tests/validators/test_ci_required_gate.py`. | - |
| v3.17#MT-2 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:80 | No coverage instrumentation for subprocess validator tests | PLAN | AR-33. Needs coverage plumbing (`COVERAGE_PROCESS_START`) plus a threshold in CI, which is a design change. | tests/validators/conftest.py, CI |
| v3.17#WN-1 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:87 | `make` unavailable on the dev host | OBSOLETE | CI and the local gate now run through `scripts/ci/run.py` and `scripts/ci/profiles.py`, not the Makefile (see the AGENTS.md "Running Validation" section). | - |
| v3.17#QG-3 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:132 | Installer gained a copy step (informational) | RESOLVED | The copy step is present: `scripts/installer.sh:2921-2923` and `scripts/installer.ps1:3042-3044`. | - |
| v3.17#NI-3 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:155 | cd-pipeline-generator audited, null result | RESOLVED | A record of a completed audit; no work requested. | - |
| v3.17#NI-4 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:162 | cicd-integration audited, null result | RESOLVED | A record of a completed audit; no work requested. | - |
| v3.17#MT-5 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:177 | cicd-architect 9 lines from the 800-line cap | RESOLVED | The split happened: `catalog/skills/infrastructure/cicd-architect/SKILL.md` is now 275 lines. | - |
| v3.17#QG-4 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:195 | Decision record names six instances, not seven | RESOLVED | Informational; the entry says "Suggested next step: none". | - |
| v3.17#NI-5 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:202 | Rejected inverse-path design recorded | RESOLVED | "Recorded, not a gap". The record exists at `docs/decisions/rejected/tooling/2026-08-19-inverse-path-no-op-workflows.md`. | - |
| v3.17#QG-6 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:238 | Actions-minute delta measured | RESOLVED | Accepted with "no follow-up". | - |
| v3.17#QG-7 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:252 | Validator added no job or matrix leg | RESOLVED | A confirmation record; no work. | - |
| v3.17#NI-6 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:258 | Two clean CI skills restated | RESOLVED | A restatement of NI-3 and NI-4; no work. | - |
| v3.17#MT-4 (v3.17.6) | docs/archives/v3/v3.17/known-gaps.md:319 | 1042 Ruff warnings resolution | RESOLVED | The parsed heading is the resolution subsection. Its item reads "MT-4 - RESOLVED" (line 321). | - |
| v3.17#NI-1 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:559 | Output redirection under an allow rule is unverified | PLAN | AR-16. Needs a live Claude Code matcher probe. | development/permission-matcher-findings.md |
| v3.17#NI-2 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:568 | Does the Gemini matcher split compound commands | PLAN | AR-16. Needs a live Gemini CLI probe. | configs/permissions/gemini-permissions.json |
| v3.17#NI-3 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:576 | Eight integrations lack an autonomy descriptor | OBSOLETE | Autonomy descriptors were removed from the product contract (v3.17 ledger line 517, v3.17.2 section). | - |
| v3.17#DF-1 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:584 | No PowerShell or cmd.exe read-only set for Gemini | PLAN | AR-16. Blocked on the NI-2 probe. | configs/permissions/gemini-permissions.json |
| v3.17#DF-2 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:592 | No project-scoped permission target for Gemini, Codex, Copilot | PLAN | AR-17. Needs vendor research plus a maintainer decision on the commit-visible Copilot file. | installers |
| v3.17#DF-3 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:599 | Permissions helper is PowerShell-only | PLAN | AR-17. Needs a new `nexus-hub` permissions subcommand (a multi-file feature). | scripts/nexus_hub_cli.py |
| v3.17#DF-4 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:606 | Hermes registered but not installer-wired | PLAN | AR-05. 0 Hermes references in `scripts/installer.sh` and `scripts/installer.ps1`. Needs both installer arms and smoke tests (ask-first), or a registry-only decision. | installers |
| v3.17#DF-5 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:613 | Read-only baseline covers 4 of 16 integrations | PLAN | AR-17. Per-platform permission-contract research. | configs/permissions/ |
| v3.17#WN-2 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:628 | No repository-wide Ruff baseline | PLAN | AR-34. Needs a baseline decision plus batched fixes and a CI gate. | scripts/lib/integrations/, CI |
| v3.17#WN-4 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:642 | Hook independence verified only on Claude Code 2.1.156 | OBSOLETE | Retired in v3.17.2: "Nexus-Hub no longer claims or tests that product boundary" (v3.17 ledger line 518). | - |
| v3.17#MT-1 (v3.17.0) | docs/archives/v3/v3.17/known-gaps.md:650 | Claude usage monitor has no coverage baseline | PLAN | AR-32. `extensions/claude-usage-monitor/vitest.config.mts` still has no coverage or threshold, and the legacy modules are untested. | extensions/claude-usage-monitor |
| v3.18#BG-2 | docs/archives/v3/v3.18/known-gaps.md:226 | Two installer tests flake in long local OneDrive runs | PLAN | AR-40. Closing it needs hosted-CI evidence plus a clean full local installer run. `test_org_cli.py` is not covered by fix `ad768ca9`. | tests/installer/ |
| v3.18#QG-1 | docs/archives/v3/v3.18/known-gaps.md:236 | Verification performed for v3.18.2 | RESOLVED | A verification log, not a gap; it lists passing checks. | - |
| v3.18#WN-1 | docs/archives/v3/v3.18/known-gaps.md:264 | Registry text must be derived, not retyped | RESOLVED | The body records "CLOSED 2026-08-22 (Phase 5)". The guard is `scripts/check_registry_entries.py --check --strict`. | - |
| v3.19#DF-2 | docs/archives/v3/v3.19/known-gaps.md:34 | Docs convention checker scans only the active minor | PLAN | AR-42. The maintainer must record the grandfathering decision. The docstring is still stale (`scripts/check_docs_conventions.py:5`, `docs/v<MAJOR>/...` layout). | scripts/check_docs_conventions.py |
| v3.19#DF-3 | docs/archives/v3/v3.19/known-gaps.md:41 | Semantic reformatters cover a short list | PLAN | AR-24. Handlers should be added on demand when a real fixture misses the reduction bar. | extensions/nexus-context-compressor |
| v3.19#DF-4 | docs/archives/v3/v3.19/known-gaps.md:48 | Signed execution contracts remain a design study | PLAN | AR-43. No decision record exists under `docs/decisions/`. A maintainer decision is needed. | docs/decisions/ |
| v3.20#DF-1 (v3.20.3) | docs/archives/v3/v3.20/known-gaps.md:34 | No invocation-policy lever on five platforms | PLAN | AR-38. Waits on a first-party vendor document naming a field. | docs/policy/skill-invocation-policy-levers.md |
| v3.20#DF-2 (v3.20.3) | docs/archives/v3/v3.20/known-gaps.md:41 | Claude plugin directory listing not submitted | PLAN | AR-39. Needs a maintainer-only manual form submission. | README.md |
| v3.20#WN-2 (v3.20.1) | docs/archives/v3/v3.20/known-gaps.md:190 | 65+ SKILL.md bodies exceed 500 lines | PLAN | AR-07. Incremental work across many skills. | catalog/skills/** |
| v3.20#MT-1 (v3.20.1) | docs/archives/v3/v3.20/known-gaps.md:199 | Most skills lack trigger-case evals | PLAN | AR-09. Incremental work across many skills. | catalog/skills/**/evals/ |
| v3.21#DF-1 | docs/archives/v3/v3.21/known-gaps.md:32 | No product atlas HTML | PLAN | AR-41. The maintainer must decide whether `docs/handbooks/overview.html` counts. `docs/README.md:11` still says "no product atlas HTML yet". | docs/README.md |

## QUICK items, batched by file

1. `docs/specs/README.md`

    1. v3.14#DF-3 (AR-31): replace the "Original 4 (legacy installer copy blocks)" bullet at line 22. The new wording: Claude Code is the one bespoke installer block, and every other platform, including Gemini/Antigravity 1.0, Codex and Copilot, installs through the integration registry (`scripts/lib/integrations/` via `runner.py`). Keep the separate permissions "legacy 4" grouping intact. Then mark AR-31 resolved in `docs/releases/v4/v4.13/known-gaps.md`.

2. `tests/validators/test_validate_skills.py` (or a new `tests/validators/test_validate_frontmatter_strict_yaml.py`)

    1. v3.14#MT-1 v3.14.3 (AR-08, strict-YAML part only): add two tests against `validate_frontmatter_strict_yaml(skill_file, content)` from `scripts/validate_skills.py:170`. A quoted good block must return `[]`. An unquoted `description: ... SKIP: x` block must return one error. The other AR-08 surfaces (`detect-platform.sh`, `benchmark --update-baseline`, `nexus-hub map`, `DEFAULT_GUARDS`) stay open.

## Optional ledger-hygiene batch (not counted above)

These source ledgers already say `**Open items**: 0`. They will keep appearing in `minor_close.py status` until their headings carry a parser-recognized terminal marker. This is the normalization already tracked at `docs/releases/v4/v4.13/known-gaps.md:1107`.

- **The 17 RESOLVED and 3 OBSOLETE rows above:** appending ` - CLOSED 2026-09-29` (or ` - RESOLVED`) to each heading is mechanical and docs-only.
- **The 41 PLAN rows migrated to AR-xx:** they cannot use ` - MIGRATED to vX.Y.Z`, because the target ids differ (AR-xx, not the same gid). Closing their source headings needs a maintainer decision on how a migrated-to-AR item is expressed, so treat that part as PLAN.
