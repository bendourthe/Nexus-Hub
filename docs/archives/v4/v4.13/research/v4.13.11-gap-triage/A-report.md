# Known-gaps triage, group A (146 entries)

Repository: `%USERPROFILE%\Documents\Benjamin\nexus\Nexus-Hub-worktrees\v41310` (branch `feat/v4.13.10-training-page-rebuild`). Every entry lives in `docs/releases/v4/v4.13/known-gaps.md`, so "Source file" below gives `KG:<line>` for that file. The 146 IDs in `A.txt` follow the ledger's Open Items order section by section, so repeated IDs such as `v4.13#WN-1` are separate items in different patch sections. Each row names its section (`4.13.0`, `AR` for the migrated block, `4.13.1` to `4.13.10`).

Counts: RESOLVED 4 | OBSOLETE 2 | QUICK 19 | PLAN 121 | total 146

Notes:

- Installer edits (AR-10, AR-20, AR-58 and similar) are classed PLAN even when the code change is small. AGENTS.md lists installer changes as "ask first", and AR-58 records that any byte change to either installer makes `check_handbooks.py` report stale distribution-handbook evidence until a review is re-run.
- Four entries are already closed in their own text but still count as open, because the heading has no terminal marker the parser accepts (v4.13.0 WN-6, v4.13.3 WN-2) or because the remaining part cannot be recovered (v4.13.0 WN-5). Closing them is a ledger-only edit.
- The QUICK fixes in the Training sources (v4.13.10 WN-5, WN-6) touch files another process is editing in this worktree right now. Do them after that work lands.

| Gap | Source file | One-line summary | Class | Evidence or fix | Files |
|---|---|---|---|---|---|
| 4.13.0 BG-7 | KG:25 | Second trigger pilot's per-call budget did not bound reported cost | PLAN | Needs a provider-enforced spend cap (Console workspace) and a new paid protocol | - |
| 4.13.0 WN-3 | KG:41 | Shipped catalog under-triggers on its own positive prompts | PLAN | Needs a new frozen paid pilot before guidance changes | - |
| 4.13.0 WN-5 | KG:49 | Recorded pilot run cannot be re-audited for the loose matcher | RESOLVED | The forward-looking step is done: `scripts/run_trigger_pilot.py` retains `skill_selectors` (7 references; follow-up of 2026-09-22 at KG:57). The 96 historical payloads cannot be recovered, so close as resolved-with-unrecoverable-residual | - |
| 4.13.0 WN-6 | KG:59 | Symlink refusal unproven on Windows without developer mode | RESOLVED | Body already reads "RESOLVED 2026-09-22" (KG:61, KG:65), proven by Linux CI and WSL2; only the heading lacks the marker | - |
| AR-03 | KG:280 | Presentify repository walk has no secret redaction | PLAN | Feature work: route the extractor through egress-redaction rules, with tests | - |
| AR-05 | KG:295 | Hermes registered but not wired into either installer | PLAN | Still zero `hermes` matches in `scripts/installer.sh` and `scripts/installer.ps1`; needs installer work in both or a decision | - |
| AR-10 | KG:301 | PowerShell early exit leaks the selection staging directory | PLAN | Residual still documented at `scripts/installer.ps1:4161-4178`; installer edit plus handbook evidence refresh | - |
| AR-11 | KG:307 | Antigravity skill seeding can exceed the Windows path limit | PLAN | `scripts/lib/integrations/base.py:443` is still plain `shutil.copytree`; needs Windows long-path design and testing | - |
| AR-20 | KG:313 | Workspace install output not grouped like global | PLAN | `install_workspace` (`scripts/installer.sh:1893-2088`) never calls `write_undetected_group`; installer edit in both scripts | - |
| AR-21 | KG:319 | `nexus-hub verify` does not cover `extensions/` | PLAN | `scripts/generate_manifest.py:125` `COVERED_ROOTS` unchanged; needs a manifest change or a decision | - |
| AR-26 | KG:325 | No live macOS installer smoke recorded | PLAN | Needs a maintainer macOS host | - |
| AR-30 | KG:331 | `configs/` not distributed to installed trees | PLAN | No decision record found under `docs/decisions/`; maintainer decision | - |
| AR-40 | KG:337 | Two installer tests fail intermittently in long runs | PLAN | Depends on v4.13.1 BG-2 being verified in hosted CI and a clean full local run | - |
| AR-16 | KG:345 | Permission-matcher behaviors unprobed | PLAN | Needs live probes against current Gemini and Claude builds | - |
| AR-17 | KG:351 | Permission distribution covers few platforms and scopes | PLAN | Multi-platform research plus a new command | - |
| AR-36 | KG:357 | Unverified platform read-path residuals | PLAN | Needs an authenticated vendor read-back | - |
| AR-38 | KG:363 | No invocation-policy lever on five platforms | PLAN | Vendor-dependent | - |
| AR-45 | KG:369 | Completion notification unverified on Qwen, Gemini CLI, Kimi | PLAN | Needs platform delivery work and live verification | - |
| AR-47 | KG:375 | Legacy Cursor global commands write is unverified and redundant | PLAN | `scripts/lib/integrations/cursor.py:9-12,172` still writes and labels it UNVERIFIED; needs a Cursor contract pass | - |
| AR-51 | KG:381 | OpenCode writes a `rules` folder the contract does not record | PLAN | `scripts/lib/integrations/opencode.py:73` still sets `rules_subdir`; needs a vendor-doc review | - |
| AR-54 | KG:387 | Strict Claude permissions overlay has no `defaultMode` decision | PLAN | No `defaultMode` in `configs/permissions/*.json`; needs a permissions decision (security posture) | - |
| AR-56 | KG:393 | Upstream-blocked hook surfaces (Gemini CLI, Kimi) | PLAN | Vendor-dependent | - |
| AR-57 | KG:399 | Agent and hook delivery never observed on real Codex, Gemini CLI, Qwen, Kimi | PLAN | Needs a host with those tools installed | - |
| AR-04 | KG:407 | Skill-description eval harness builds CLI flags that do not exist | PLAN | `scripts/optimize_skill_description.py:305,321` still adds `--skill` and `--prompt`; port plus live checks need a CLI re-verification (shared with 4.13.9 WN-24) | - |
| AR-06 | KG:413 | 250-char description cap conflicts with the trigger-rich rule | PLAN | `scripts/validate_skills.py:58` is still 250, and 223 skill descriptions exceed it; maintainer decision on the cap | - |
| AR-07 | KG:419 | Many SKILL.md bodies exceed 500 lines | PLAN | 68-skill refactor done incrementally | - |
| AR-08 | KG:425 | Missing direct tests on five surfaces | PLAN | Still no test for `validate_frontmatter_strict_yaml`, `detect-platform`, or `--update-baseline`; five separate tests across owners | - |
| AR-09 | KG:431 | Most skills lack trigger-case evals | PLAN | Incremental catalog work | - |
| AR-12 | KG:437 | loop-engineering lacks a re-entrancy guard and schema assertions | PLAN | No guard or cross-link text in `catalog/skills/workflow/loop-engineering/SKILL.md`; several assertions plus skill design | - |
| AR-13 | KG:443 | egress-redaction covers only the egress boundary | PLAN | Skill scope extension (design) | - |
| AR-14 | KG:449 | Spec template A1 example phrases a Non-Goal as an Assumption | QUICK | Rewrite A1 at `catalog/templates/spec-template.md:171` as a real HOW-default, move the JWT clause into the Non-Goals example, and drop the self-referencing sentence at line 140 | catalog/templates/spec-template.md |
| AR-15 | KG:455 | spec-kit S5, S6, S8 carry no status claim | PLAN | Needs a spec-kit delta re-verification against upstream | - |
| AR-22 | KG:461 | `make build-catalog` would overwrite hand-curated registries | QUICK | Guard the `build-catalog` target (`Makefile:90`) so it refuses without an explicit `FORCE=1` and points to `check_registry_entries.py`; update the `AGENTS.md:506` line to match | Makefile, AGENTS.md |
| AR-23 | KG:467 | Hook rewrite field `updatedInput` undocumented | QUICK | No `guides/` file mentions it. Add a short `updatedInput` subsection (PreToolUse `hookSpecificOutput`) to the settings reference, with the official hooks-doc URL and fetch date | guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md |
| AR-28 | KG:473 | Retired slash-command names remain in skill bodies | PLAN | Down from 134 to 59 mentions of `/generate-plan` and `/tasks-to-issues`, but a catalog-wide sweep with registry text sync | - |
| AR-33 | KG:479 | Subprocess-driven validator tests have no coverage measurement | PLAN | No `COVERAGE_PROCESS_START` anywhere; CI infrastructure work | - |
| AR-34 | KG:485 | No repository-wide Ruff baseline | PLAN | Ruff still runs only in `.github/workflows/presentify-extractor.yml`; baseline plus CI gate | - |
| AR-50 | KG:491 | Template parity guard covers only the lockstep five | PLAN | Extend the guard or record a decision | - |
| AR-53 | KG:497 | No reusable self-check eval-loop authoring convention | PLAN | New convention document (design) | - |
| AR-55 | KG:503 | `ai-agent-governance` has no reciprocal SKIP clause | QUICK | Description (242 chars) has no SKIP. Tighten it and add "SKIP - coding-agent endpoint and sandbox-escape hardening (use agentic-endpoint-hardening)", then mirror it in the registry and run `check_registry_entries.py --check --strict` | catalog/skills/compliance/ai-agent-governance/SKILL.md, data/skills.json |
| AR-18 | KG:511 | Presentify builder and extractor limits | PLAN | Bundle of accept-or-build decisions | - |
| AR-19 | KG:517 | Presentify verification residuals | PLAN | Rendered QA, media-fetch smoke and new checkers | - |
| AR-24 | KG:525 | nexus-context-compressor deferred refinements | PLAN | Benchmark-driven, on demand | - |
| AR-25 | KG:531 | Skill-scanner coverage limits | PLAN | Expand or accept by decision | - |
| AR-27 | KG:537 | Code-search covers 12 languages | PLAN | On demand | - |
| AR-32 | KG:543 | Usage-monitor extension test coverage | PLAN | Several tests, a threshold, and a live render check | - |
| AR-44 | KG:549 | Cursor usage-monitor live visual smoke never run | PLAN | Needs a live Cursor host | - |
| AR-49 | KG:555 | `@vscode/vsce` transitive deprecation warnings | PLAN | Upstream-bounded; re-check at the next toolchain bump | - |
| AR-52 | KG:561 | contextmap detectors deferred | PLAN | On demand | - |
| AR-58 | KG:567 | Installers cite the pre-archive path of the install-selection contract | PLAN | Still at `scripts/installer.sh:2103` and `scripts/installer.ps1:33,2248`; repointing needs a distribution-handbook evidence refresh | - |
| AR-59 | KG:573 | Extension devDependencies declared as caret ranges | PLAN | Still 11/11/11/7 caret ranges (four monitors now, copilot included); each pin needs an npm build and Vitest run | - |
| AR-60 | KG:579 | Extension build workflows install with lifecycle scripts enabled | PLAN | All four monitor workflows still run plain `npm ci`; needs a VSIX byte comparison and a CI change | - |
| AR-46 | KG:587 | Windows notification linger never measured | PLAN | Needs a live Windows desktop measurement | - |
| AR-48 | KG:593 | `session-summary` labels projects by working directory | QUICK | `catalog/hooks/session-summary.sh:50` uses `basename "$(pwd)"` and `.ps1:49` `Split-Path (Get-Location) -Leaf`, while both already compute the git top-level later (sh:86-92, ps1:92-96). Compute the top-level first and derive the name from it in both siblings, plus a parity test from a subdirectory | catalog/hooks/session-summary.sh, catalog/hooks/session-summary.ps1, catalog/hooks/tests (new case) |
| AR-29 | KG:601 | `README_zh.md` needs a full re-translation | PLAN | Large translation | - |
| AR-31 | KG:607 | `docs/specs/README.md` describes "legacy installer copy blocks" | QUICK | Rewrite `docs/specs/README.md:22`: Claude has the one custom installer block, and every other platform goes through the integration registry | docs/specs/README.md |
| AR-35 | KG:613 | Optional failover/settlement reference for `multi-provider-ai` | PLAN | Maintainer decision: write it or close as won't-do | - |
| AR-39 | KG:619 | Official Claude plugin directory submission never made | PLAN | Maintainer manual form | - |
| AR-37 | KG:627 | Conditional adoption candidates awaiting build-or-decline | PLAN | Maintainer decisions | - |
| AR-41 | KG:633 | Product atlas | PLAN | `docs/README.md:11` still says no atlas exists; maintainer must confirm the overview handbook counts | - |
| AR-42 | KG:639 | Docs-convention checker scans only the active minor | PLAN | Docstring (`scripts/check_docs_conventions.py:5-6`) still names the old `docs/v<MAJOR>/` tree; needs the grandfathering decision first | - |
| AR-43 | KG:645 | Signed execution contracts remain a design study | PLAN | No decision record under `docs/decisions/`; maintainer promotes it | - |
| 4.13.1 BG-2 | KG:666 | Full-profile tests write into the real `~/.nexus-hub` | PLAN | Needs a group-by-group audit in a disposable account and a real-home guard | - |
| 4.13.1 WN-7 | KG:674 | Generated-with footer plus a long clause passes the attribution hook | PLAN | Needs a corpus of real footers to tune the clause limit | - |
| 4.13.1 WN-1 | KG:678 | User edit between sessions preserved but not reported | PLAN | Needs a paid replay re-measurement | - |
| 4.13.1 WN-2 | KG:682 | Moved picture never named in the agent's report | PLAN | Needs a paid replay re-measurement | - |
| 4.13.1 WN-3 | KG:686 | Codex replays can see the machine's real user skills | PLAN | Needs a separate Windows user or a container | - |
| 4.13.1 WN-4 | KG:690 | Antigravity 2.0 and Windsurf lack the guard hooks | PLAN | Needs vendor payload verification | - |
| 4.13.1 WN-5 | KG:694 | Scenario D not re-measured on Claude after fixes | PLAN | Paid re-measurement | - |
| 4.13.1 WN-6 | KG:698 | Accepted blind spots of `user-edit-guard` | PLAN | Accepted risk; the next step needs a false-block-rate measurement | - |
| 4.13.1 MT-1 | KG:702 | No paid measurement on a platform other than Claude and Codex | PLAN | Paid replay | - |
| 4.13.2 WN-4 | KG:731 | Headless OpenCode cannot create a run record | PLAN | Needs an interactive measurement or a vendor event | - |
| 4.13.2 WN-7 | KG:737 | OpenCode full run proceeds without a run record | PLAN | Needs an OpenCode plugin enforcement design | - |
| 4.13.2 MT-1 | KG:743 | Condition B (Codex) has one passing run | PLAN | Needs the OpenAI pilot key and quota | - |
| 4.13.2 WN-8 | KG:749 | Run-record signature does not cover `pause` or `blockers` | PLAN | `_SIGNED_FIELDS` (`scripts/check_plan_completion.py:441-452`) still omits both; needs one re-signing path across several writers (security-relevant) | - |
| 4.13.2 WN-9 | KG:755 | Approval capture: agent-originated capture still undetected | PLAN | Needs a platform-authenticated user-turn signal | - |
| 4.13.2 WN-11 | KG:767 | `run-plan` checks only global settings for an approval bypass | PLAN | `bypass_configured` (`scripts/run_plan.py:254-279`) is still regex over global files; needs per-platform confirmation of project-level bypass | - |
| 4.13.2 WN-12 | KG:773 | `integration.checks` and `release.version-sync` read the working tree | PLAN | `scripts/check_plan_completion.py:973,1037` still read `ctx.root`; design choice between origin/start_head reads | - |
| 4.13.2 WN-13 | KG:779 | Record lifetime and environment edge cases | PLAN | Remaining part needs a live capture of `gh` stderr on a fresh PR | - |
| 4.13.2 DF-5 | KG:785 | Approval capture missing on Pi, OpenClaw, Hermes, Windsurf | PLAN | Four platform adapters plus parity tests | - |
| 4.13.2 DF-6 | KG:791 | Copilot CLI gets no goal at all | RESOLVED | `scripts/run_plan.py:165-167` puts `copilot/cli` in `INTERACTIVE_GOAL_ROWS` with the documented reason, and lines 436-438 print the goal line for the user to type (commit `b148c2c92`, v4.13.6). The headless remainder is tracked as 4.13.6 DF-1 | - |
| 4.13.2 DF-7 | KG:797 | Recorded design deltas from Phases 2, 4, 6 | PLAN | Accepted; revisit only when a platform documents per-run spend | - |
| 4.13.2 MT-2 | KG:803 | No real CLI run exercised a gate refusal or a runner resume | PLAN | Paid session plus a render-step harness change | - |
| 4.13.2 DF-1 | KG:809 | Devin Desktop reads `.devin/hooks.json` | PLAN | Vendor re-verification at a contract pass | - |
| 4.13.2 DF-2 | KG:815 | Antigravity 1.0 hook support unconfirmed | PLAN | Vendor evidence or a live 1.0 install | - |
| 4.13.2 DF-3 | KG:821 | Devin CLI reads Claude Code hook files | PLAN | Contract row plus Devin payload parity cases (vendor verification) | - |
| 4.13.2 DF-4 | KG:827 | OpenClaw and Hermes completion plugins need a manual enable | PLAN | Vendor config-path verification | - |
| 4.13.3 DF-1 | KG:941 | Flip the skill-index pointer on by default | PLAN | Owned by v4.17.3, which needs evaluator evidence | - |
| 4.13.3 DF-2 | KG:945 | Pilot variant mode for instruction-file comparisons | PLAN | Owned by v4.16.0 feature work | - |
| 4.13.3 DF-3 | KG:949 | Plan state in the session digest | PLAN | Blocked on a future plan-status contract | - |
| 4.13.3 DF-4 | KG:953 | Static-measurement ownership split for v4.17.3 | PLAN | Handoff to v4.17.3 | - |
| 4.13.3 DF-5 | KG:957 | Shared cleanup-aware merge requirement for v4.17.3 | PLAN | Handoff to v4.17.3 | - |
| 4.13.3 DF-6 | KG:961 | Pointer consumer installed before its provider across runner calls | PLAN | Residual is conditional on a future shared path; pinned today by `test_installers_run_the_shared_path_provider_before_copilot` | - |
| 4.13.3 DF-8 | KG:969 | Per-agent `omitClaudeMd` for catalog agents | PLAN | Owned by v4.16.2; needs a pairing receipt | - |
| 4.13.3 WN-1 | KG:973 | Uncooperative writer can race the final hash check | PLAN | Accepted risk with no portable primitive; candidate to close by decision | - |
| 4.13.3 WN-2 | KG:977 | Copilot host-scope mismatch | RESOLVED | Heading reads "RESOLVED 2026-09-28 UTC"; PR #361 merged as `6d9e4c39` (KG:983). The parser seems not to accept the trailing "UTC", so it still counts as open; drop "UTC" from the heading | - |
| 4.13.3 MT-1 | KG:985 | Full installers not run end to end on a disposable machine | PLAN | Needs a disposable machine | - |
| 4.13.3 WN-5 | KG:989 | Read-path drift found by the release contract pass | PLAN | Adapter plus contract lockstep with vendor confirmation | - |
| 4.13.3 WN-6 | KG:995 | Behavioral-lever drift found by the release contract pass | PLAN | `configs/platform-defaults.json` still seeds no `modelSettings` effort; needs a vendor re-check of the Claude, Codex and Antigravity rows | - |
| 4.13.4 WN-1 | KG:1031 | Header nav overflows under the matrix's 200% CSS zoom | PLAN | `tests/guides/tools/browser_matrix.py:137,199` still emulates zoom with `style.zoom`; needs a native-zoom measurement on a real browser | - |
| 4.13.4 WN-2 | KG:1035 | Idle game labels its toggle "Pause game" | OBSOLETE | The arcade game and `syncHud` are gone: `tests/guides/test_arcade_shooter_game.py` was deleted in `f3b3ceed3` (Training cut over to `training.html`), and the new SkySentinel engine labels the idle control "Start game" (`guides/website/src/sky-sentinel.js:1437,5279`). No "Pause game" string remains in either page | - |
| 4.13.6 WN-1 | KG:1101 | Claude Code interactive `/goal` capture observed only headless | PLAN | Needs a human-typed interactive probe | - |
| 4.13.6 WN-2 | KG:1105 | Older known-gaps ledgers read cannot-verify | PLAN | Large docs normalization across about 30 ledgers, including unique ids per minor file | - |
| 4.13.6 MT-1 | KG:1109 | Guide scope-matching test checks no scope | QUICK | `tests/guides/test_nexus_hub_guide.py:1457` matches `<code>` while all 86 rendered scopes are `<code data-ty="code">`. Change the regex to `<code[^>]*>`, assert at least one scope was compared, confirm it fails on a deliberately stale scope, and fix any card the corrected test exposes | tests/guides/test_nexus_hub_guide.py (possibly guides/website/nexus-hub-guide.html) |
| 4.13.6 WN-4 | KG:1113 | Whole website guide reports 100 detector findings | PLAN | 100 findings to fix or allowlist one view at a time, plus a render-gate change | - |
| 4.13.6 WN-5 | KG:1117 | v4.13.2 WN-9 only partly closed | PLAN | Pointer that duplicates 4.13.2 WN-9; could close as a duplicate at migration | - |
| 4.13.6 DF-1 | KG:1121 | Copilot CLI sets no native goal headlessly | PLAN | Vendor-dependent | - |
| 4.13.6 QG-1 | KG:1125 | Non-engineer read-back of the approval page pending | PLAN | Human read-back | - |
| 4.13.6 QG-2 | KG:1129 | Edited guide card had no full accessibility or design audit | PLAN | Two full skill-driven audits with rendered review; likely to surface fixes | - |
| 4.13.6 WN-6 | KG:1133 | Unusual branch, surface and vendor names reach the approval page | PLAN | `OUTCOME_BANNED_RE` (`scripts/approval_page.py:96`) would reject legitimate names such as `feat/approval-*`; changing the page data also changes the HMAC-derived code, so it needs a design choice | - |
| 4.13.9 WN-1 | KG:1225 | GPT-6.1 Sol announcement could not be read | PLAN | External page access (HTTP 403) | - |
| 4.13.9 WN-2 | KG:1231 | Cursor's `/visualize` primary docs not read | PLAN | Vendor-dependent | - |
| 4.13.9 DF-1 | KG:1237 | Codex `doctor` advisory cut from the plan | PLAN | Conditional reopen trigger (two primary sources plus a second hazard) | - |
| 4.13.9 DF-9 | KG:1243 | Claude Haiku 5.5 announced but no profile or map cell | PLAN | Waits on the vendor models overview | - |
| 4.13.9 DF-11 | KG:1251 | Nine newly rostered Claude models lack prompting profiles | PLAN | Research per model (v4.17.6 and later) | - |
| 4.13.9 WN-21 | KG:1259 | Reasoning example asks the model to write its analysis into the reply | QUICK | Lines 92-101 still ask for "Think through this step-by-step" and a `<thinking>` block. Relabel the example as written for models without native extended thinking and add a model-agnostic note to prefer the model's own thinking; keep it free of model names | catalog/skills/ai-development/prompt-engineering/references/step-2-apply-reasoning-techniques.md |
| 4.13.9 WN-22 | KG:1267 | Self-consistency example asks for written-out reasoning | QUICK | Line 127 still says "Think step-by-step, then provide your final answer". Same edit as WN-21, done in the same change | catalog/skills/ai-development/prompt-engineering/references/step-2-apply-reasoning-techniques.md |
| 4.13.9 WN-23 | KG:1275 | Primary roster mixes vendors, so freshness always reads DRIFTED | PLAN | Schema migration of profiles onto per-platform entries plus an alias decision | - |
| 4.13.9 DF-12 | KG:1283 | First-principles pilot stopped at the smoke run | PLAN | Waits on a Claude Code release and a paid re-run | - |
| 4.13.9 WN-24 | KG:1291 | skill-eval-loop Claude adapter command no longer matches the CLI | PLAN | Adapter and optimizer still use `--skill`; needs a re-verification against the current official CLI reference (shared with AR-04) | - |
| 4.13.9 WN-25 | KG:1299 | Profiling-harness test flaky under host load | QUICK | `tests/skills/test_profiling_harness.py:64,70` checks `work` within `--top 10`. Raise `--top` (for example to 200) for that run, or assert against the full function list, so timing rank cannot evict `work` | tests/skills/test_profiling_harness.py |
| 4.13.9 WN-26 | KG:1307 | Open Dependabot branches make the all-refs attribution check fail | PLAN | CI security policy change needing explicit approval (`scripts/check_commit_attribution.py:91` still uses `--all`) | - |
| 4.13.9 BG-12 | KG:1316 | `/usage` dispatches to a nonexistent `check-usage` skill | PLAN | `catalog/commands/usage.md` still delegates to `check-usage`, which does not exist, and no skill calls `_usage_probe.py`. Needs a new skill (registry, index, bundles) or a redesign | - |
| 4.13.9 WN-27 | KG:1324 | All-refs attribution scan fails on fetched Dependabot branches | PLAN | Same CI security decision as WN-26 (duplicate) | - |
| 4.13.9 WN-28 | KG:1332 | Dependabot does not track the Copilot monitor's npm deps | QUICK | `.github/dependabot.yml` has only claude, codex and cursor. Add a `/extensions/copilot-usage-monitor` npm entry that ignores `@types/vscode` like its siblings, and change the expected count from three to four in `test_dependabot_tracks_the_new_extension`. CI config change; get the maintainer's one-line approval first | .github/dependabot.yml, tests/workflows/test_cursor_usage_monitor_workflow.py |
| 4.13.9 WN-29 | KG:1340 | `codexUsage.authPath` can be set by a workspace | QUICK | `extensions/codex-usage-monitor/package.json:93-97` declares no scope. Add `"scope": "machine"`, add the key to the scope assertion in `test/review-regressions.test.ts`, and note in the README that a workspace value is ignored | extensions/codex-usage-monitor/package.json, extensions/codex-usage-monitor/test/review-regressions.test.ts, extensions/codex-usage-monitor/README.md |
| 4.13.9 WN-30 | KG:1348 | DoD says VS Code and Cursor, but the Copilot monitor installs into VS Code only | PLAN | Maintainer decision (supported surface), then installer edits | - |
| 4.13.9 WN-31 | KG:1356 | DoD 7 asks for a reset expiry; Codex serves only a count | PLAN | Needs a live reset to capture | - |
| 4.13.9 WN-32 | KG:1364 | Monitor workflows differ in packaging checks and self-triggers | PLAN | New `verify:package` script plus three workflow edits; pipeline change needing approval | - |
| 4.13.9 WN-33 | KG:1372 | Redirecting HOME does not isolate the usage probe's Cursor reader on Windows | QUICK | `docs/guides/usage-limit-handoff.md` has no `APPDATA` note. Add one sentence: an isolated probe run must also redirect `APPDATA`, or exclude Cursor through `NEXUS_USAGE_PROBE_PROVIDERS` | docs/guides/usage-limit-handoff.md |
| 4.13.9 QG-7 | KG:1380 | Real-editor and live-limit checks pending | PLAN | Maintainer manual checks | - |
| 4.13.9 QG-8 | KG:1388 | Run record never captured for v4.13.8 | OBSOLETE | The user chose on 2026-10-02 to release on the chat approval, tag `v4.13.8` exists, and the entry's own next step is "None for v4.13.8" (KG:1393). The optional recovery-path idea can become a new DF if wanted | - |
| 4.13.9 WN-35 | KG:1397 | Governance test group outgrows its 2700 s local cap | QUICK | Raise the `repo-tests-governance` timeout at `scripts/ci/profiles.py:376` from 2700 to 3600, citing the recorded 3325.7 s measurement in a comment, and update any pinned value in `tests/workflows/test_ci_precommit_profile.py` | scripts/ci/profiles.py, tests/workflows/test_ci_precommit_profile.py |
| 4.13.9 BG-13 | KG:1407 | `auto-devlog.sh` drops every entry after a heading reaches line 1 | QUICK | `catalog/hooks/auto-devlog.sh:151-155` computes `INSERT_LINE = FIRST_H2_LINE - 1`, which is 0 for a line-1 heading and never matches `NR == 0`. Insert before the heading itself (or clamp to 1), match the `.ps1` placement, add a parity case, and remove the `("auto-devlog","sh",_DL,"liveness")` entry from `KNOWN_BREACHES` | catalog/hooks/auto-devlog.sh, catalog/hooks/tests/test_hook_size_bound.py |
| 4.13.9 BG-14 | KG:1413 | `learning-capture.sh` drops events over 128 KiB on Linux | QUICK | `catalog/hooks/learning-capture.sh:64,73` passes the payload in `NEXUS_LC_PAYLOAD`. Feed it on stdin (`"$PY" -c '...' <<<"$INPUT"`, read `sys.stdin`), truncate `hook_event_name` and `tool_name` the way the prompt sample is truncated, mirror the truncation in `.ps1`, and remove the two `learning-capture` `KNOWN_BREACHES` entries | catalog/hooks/learning-capture.sh, catalog/hooks/learning-capture.ps1, catalog/hooks/tests/test_hook_size_bound.py |
| 4.13.9 WN-36 | KG:1419 | Five file-writing hooks copy a field without truncation | PLAN | Five hooks across sh, ps1 and py plus byte-bounded ledger rotation; the learning-capture part is folded into BG-14 | - |
| 4.13.9 WN-37 | KG:1425 | Multi-byte text grows in hook output on Windows | PLAN | Encoding change across many PowerShell and Python hooks, plus a re-measurement | - |
| 4.13.9 WN-38 | KG:1431 | Hook test step outgrows its 1800 s local cap | QUICK | Raise the `hook-tests` timeout at `scripts/ci/profiles.py:285` from 1800 to 2400, citing the recorded 2096.9 s measurement, and check the Windows hook-tests step at line 515 and `tests/workflows/test_ci_precommit_profile.py` for pinned values | scripts/ci/profiles.py, tests/workflows/test_ci_precommit_profile.py |
| 4.13.10 WN-1 | KG:1461 | Missing-file notice verified in Chromium only | PLAN | Needs real Firefox and Safari | - |
| 4.13.10 WN-5 | KG:1467 | Game started through the API on a hidden stage runs unseen | QUICK | In `start()` and `resume()` (`guides/website/src/sky-sentinel.js:5315,5339`), after `wake()`, call `pause("stage")` when `host.offsetParent === null`; regenerate `training.html` and add an engine test that starts on a hidden stage | guides/website/src/sky-sentinel.js, guides/website/training.html, tests/guides (engine test) |
| 4.13.10 WN-6 | KG:1473 | Three minor accessibility findings in shared markup | QUICK | Drop `aria-pressed` from `#themeToggle` (`guides/website/shared/header.html:14`), add `aria-current="page"` to the active `#navLinks` link in the guide router (it currently sets it only on outline links and dots), add a "Skip to content" link to the shared header, then re-stamp both pages with `stamp_guide_shared.py` | guides/website/shared/header.html, guides/website/nexus-hub-guide.html, guides/website/training.html |
| 4.13.10 WN-8 | KG:1479 | Foundations opening figure taller than a phone screen | PLAN | Narrow-layout figure redesign needing visual review | - |
| 4.13.10 WN-9 | KG:1485 | Nexus AI Studio trailer shows no app screens | PLAN | Maintainer decision plus screenshots | - |
| 4.13.10 WN-11 | KG:1491 | WebGL game frame rate unverified on a real GPU | PLAN | Needs real hardware | - |
| 4.13.10 WN-12 | KG:1497 | Minor visual nits from the revision 2 review | PLAN | Six separate visual tweaks, each needing rendered review | - |
| 4.13.10 QG-2 | KG:1503 | Learner check not run | PLAN | Human testers | - |

## QUICK batches, grouped by files touched

1. Hooks (`catalog/hooks/`):
    1. BG-13 (4.13.9): `auto-devlog.sh` insert line, plus `tests/test_hook_size_bound.py` breach entry.
    2. BG-14 (4.13.9): `learning-capture.sh` and `.ps1` stdin payload and field truncation, plus `tests/test_hook_size_bound.py` breach entries.
    3. AR-48: `session-summary.sh` and `.ps1` project name from the git top-level, plus a new parity case.

2. CI profile (`scripts/ci/profiles.py`, `tests/workflows/test_ci_precommit_profile.py`):
    1. WN-35 (4.13.9): governance timeout 2700 to 3600.
    2. WN-38 (4.13.9): hook-tests timeout 1800 to 2400.

3. Dependabot and extensions (get approval first for the CI config line):
    1. WN-28 (4.13.9): `.github/dependabot.yml` plus `tests/workflows/test_cursor_usage_monitor_workflow.py`.
    2. WN-29 (4.13.9): `extensions/codex-usage-monitor/package.json`, `test/review-regressions.test.ts`, `README.md`.

4. Website guide (after the active v4.13.10 work lands):
    1. WN-5 (4.13.10): `guides/website/src/sky-sentinel.js`, then rebuild `training.html`, plus an engine test.
    2. WN-6 (4.13.10): `guides/website/shared/header.html` and the guide router, then re-stamp both pages.
    3. MT-1 (4.13.6): `tests/guides/test_nexus_hub_guide.py` regex fix (may expose a stale card in `nexus-hub-guide.html`).

5. Tests only:
    1. WN-25 (4.13.9): `tests/skills/test_profiling_harness.py`.

6. Catalog content:
    1. WN-21 and WN-22 (4.13.9): `catalog/skills/ai-development/prompt-engineering/references/step-2-apply-reasoning-techniques.md` (one change).
    2. AR-14: `catalog/templates/spec-template.md`.
    3. AR-55: `catalog/skills/compliance/ai-agent-governance/SKILL.md` plus `data/skills.json` (run the strict registry check).

7. Documentation and build tooling:
    1. AR-23: `guides/reference/CLAUDE_CODE_SETTINGS_REFERENCE.md` (`updatedInput`, cite the official hooks page).
    2. AR-31: `docs/specs/README.md` line 22.
    3. WN-33 (4.13.9): `docs/guides/usage-limit-handoff.md`.
    4. AR-22: `Makefile` `build-catalog` guard plus `AGENTS.md` line 506.

8. Ledger-only closures (no code), in `docs/releases/v4/v4.13/known-gaps.md`:
    1. Mark RESOLVED: 4.13.0 WN-5, 4.13.0 WN-6, 4.13.2 DF-6, 4.13.3 WN-2 (drop "UTC" from the heading).
    2. Mark OBSOLETE or CLOSED: 4.13.4 WN-2, 4.13.9 QG-8.
    3. Then update the section summary tables and the header `**Open items**` count.
