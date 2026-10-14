# Known-gaps triage - group D (102 IDs)

Worktree: `Nexus-Hub-worktrees/v41310` (branch `feat/v4.13.10-training-page-rebuild`), read-only review on 2026-10-08. Ledger paths below are relative to that worktree; `A/` abbreviates `docs/archives/`.

## Counts

- RESOLVED: 60
- OBSOLETE: 18
- QUICK: 2
- PLAN: 22
- Total: 102

## Why so many "open" items are already done

`scripts/completion_minor.py` (`parse_ledger_full`, `_RESOLVED_END_RE`, `_RESOLVED_PREFIX_RE`, lines 1036-1043 and 1150-1215) counts an item as closed only when its heading ends with ` - RESOLVED|CLOSED [date]`, starts its title with ` - RESOLVED|CLOSED`, ends with ` - MIGRATED to vX.Y.Z`, or sits under a `### Resolved...` subsection. Most RESOLVED rows below say "(resolved)", "**Status**: RESOLVED" or "**Resolution, date**" in the body or heading parenthesis, which the parser does not read. Closing them in the tool means a heading-marker edit, not code work (see "Ledger bookkeeping" at the end).

## Triage table

| Gap | Source file | One-line summary | Class | Evidence or fix | Files |
|---|---|---|---|---|---|
| v1.1#DF-001 | A/v1/v1.1/known-gaps.md | No catalog `create-skill-or-command` skill | RESOLVED | Recommended option (a) is in force (AGENTS.md "Adding a New Skill", line 229 onward) and a catalog authoring skill now exists: `catalog/skills/workflow/skill-create/SKILL.md` | - |
| v1.1#DF-002 | A/v1/v1.1/known-gaps.md | Plan assumed a `claude-api` registry row that was already gone | OBSOLETE | No-op verification only; `claude-api` absent from `data/SKILL_INDEX.md` (0 matches); the single `data/skills.json` hit (line 202) is unrelated antigravity prose | - |
| v1.1#DF-003 | A/v1/v1.1/known-gaps.md | Real installer run on macOS/Linux never done | RESOLVED | `.github/workflows/ci.yml:634-671` `installer-smoke` runs the real `bash scripts/installer.sh` on ubuntu-latest and macos-latest and asserts with `scripts/check_installer_smoke.py` (added f7498acc7) | - |
| v1.1#QG-001 | A/v1/v1.1/known-gaps.md | Cross-OS gate ran on one OS only | RESOLVED | Same `installer-smoke` matrix ubuntu/macos/windows, ci.yml:641-644 | - |
| v1.1#DF-004 | A/v1/v1.1/known-gaps.md | No `--dry-run` flag in either installer | OBSOLETE | The ledger's alternative (throwaway-target install) became the standard: CI installs into `$RUNNER_TEMP` homes/workspaces (ci.yml:664-671); `init --dry-run` exists only for `init` (installer.sh:3620) | - |
| v1.1#WN-001 | A/v1/v1.1/known-gaps.md | Four orphan framework-specialist reference files | RESOLVED | Now linked: fastapi-expert/SKILL.md:121, nextjs-expert/SKILL.md:727, react-expert/SKILL.md:120-121 | - |
| v1.1#DF-005 | A/v1/v1.1/known-gaps.md | Bundled skill subdirs not verified landing on macOS/Linux | RESOLVED | `check_installer_smoke.py` EXPECTED_WORKSPACE_ARTIFACTS asserts bundled `scripts/` and `references/` land (lines 21-34), run on macOS/Linux in ci.yml:634 | - |
| v1.1#DF-006 | A/v1/v1.1/known-gaps.md | Eval-loop scripts' install copy not verified on macOS/Linux | QUICK | Real install runs in CI but the three scripts are not asserted; add `aggregate_benchmark.py`, `skill_eval_viewer.py`, `optimize_skill_description.py` (and `generate_report.py`) to `EXPECTED_SCRIPTS` | scripts/check_installer_smoke.py |
| v1.1#MT-001 | A/v1/v1.1/known-gaps.md | Optimizer loop not exercised with a stub CLI | RESOLVED | `catalog/hooks/tests/test_eval_loop.py` `TestOptimizerSplit` stubs `estimate_trigger_rate` and `generate_candidates`, runs `optimize(..., max_iterations=1)` and asserts `best_description` and `selection_metric == "test_trigger_rate"` (`test_two_way_loop_keeps_old_selection`, ~line 1027) | - |
| v1.1#DF-008 | A/v1/v1.1/known-gaps.md | `package_skill.py` install copy not verified on macOS/Linux | QUICK | Add `package_skill.py` to `EXPECTED_SCRIPTS` (copy line installer.sh:2797-2799 already runs inside the CI macOS/Linux smoke) | scripts/check_installer_smoke.py |
| v1.1#DF-007 | A/v1/v1.1/known-gaps.md | mcp-builder scaffolders never run end to end | PLAN | Scaffolders `pip install mcp[cli]` and `npm install` (init-mcp-fastmcp.sh:167-172, init-mcp-ts.sh:178); needs a networked CI job design with Python and Node | - |
| v1.3#WN-001 | A/v1/v1.3/known-gaps.md | Same four orphan warnings carried | RESOLVED | Same evidence as v1.1#WN-001 | - |
| v1.3#WN-002 | A/v1/v1.3/known-gaps.md | No `make`/`shellcheck` on Windows; cp1252 breaks inline `json.load` | RESOLVED | Makefile:8-11 now pass `encoding='utf-8'`; make-free canonical gate `scripts/ci/run.py --profile fast|full` documented in AGENTS.md:509-517 | - |
| v2.0#DF-005 | A/v2/v2.0/known-gaps.md | `README_zh.md` keeps old DevAI-Hub name in v1.0.0 block | RESOLVED | Ledger's own disposition is "no action"; the required rename callout is present at README_zh.md:9 and the historical heading at :13 | - |
| v2.3#DF-v23-9 | A/v2/v2.3/known-gaps.md | Visual brainstorming server deferred | OBSOLETE | Transferred (ledger lines 27, 42) to v3.0 DF-v30-9 (A/v3/v3.0/known-gaps.md:39), now tracked as v4.13 AR-37 | - |
| v2.4#NI-v24-1 | A/v2/v2.4/known-gaps.md | No `.ps1` sibling for `validate_solution_frontmatter` | RESOLVED | Closed won't-do by convention in A/v3/v3.0/known-gaps.md:45 | - |
| v2.4#DF-v24-1 | A/v2/v2.4/known-gaps.md | Live trigger runs for two Phase-1 skills | OBSOLETE | Subsumed by DF-v24-8 -> v3.0 DF-v30-6 (A/v3/v3.0/known-gaps.md:34) -> v4.13 AR-04 | - |
| v2.4#DF-v24-2 | A/v2/v2.4/known-gaps.md | Live trigger runs for two Phase-2 review skills | OBSOLETE | Same chain, now v4.13 AR-04 | - |
| v2.4#DF-v24-3 | A/v2/v2.4/known-gaps.md | Live trigger run for product-pulse | OBSOLETE | Same chain, now v4.13 AR-04 | - |
| v2.4#DF-v24-4 | A/v2/v2.4/known-gaps.md | Live trigger runs for two Phase-3 skills | OBSOLETE | Same chain, now v4.13 AR-04 | - |
| v2.4#DF-v24-5 | A/v2/v2.4/known-gaps.md | Live `--branch` clone+install only dry-run probed | OBSOLETE | Subsumed by DF-v24-10 -> v3.0 DF-v30-8 (:37) -> v4.13 AR-26 | - |
| v2.4#DF-v24-6 | A/v2/v2.4/known-gaps.md | Live trigger run for demo-capture | OBSOLETE | Subsumed by DF-v24-8, now v4.13 AR-04 | - |
| v2.4#DF-v24-7 | A/v2/v2.4/known-gaps.md | Remaining code-search language extractors | OBSOLETE | Swift/Kotlin shipped (A/v3/v3.0/known-gaps.md:46); remainder tracked as v4.13 AR-27 | - |
| v2.4#WN-v24-2 | A/v2/v2.4/known-gaps.md | Skills with both Quality Checklist and Verification | RESOLVED | A/v3/v3.0/known-gaps.md:47; current scan finds 0 SKILL.md files with both headings | - |
| v2.4#WN-v24-1 | A/v2/v2.4/known-gaps.md | Stale catalog-count prose | RESOLVED | Heading already says resolved at v2.4.0; Resolved table row at line 165 (marker format not parser-readable) | - |
| v2.4#DF-v24-8 | A/v2/v2.4/known-gaps.md | Live skill-eval-loop trigger runs re-deferred | OBSOLETE | -> v3.0 DF-v30-6 -> v4.13 AR-04 (harness still builds bad `--skill` flags) | - |
| v2.4#DF-v24-9 | A/v2/v2.4/known-gaps.md | Live eval trigger-techniques run | OBSOLETE | -> v3.0 DF-v30-7 (:35) -> v4.13 AR-04 | - |
| v2.4#DF-v24-10 | A/v2/v2.4/known-gaps.md | macOS/Linux installer smoke plus live `--branch` | OBSOLETE | Installer smoke now in CI (ci.yml:634); live `--branch` and `curl|bash` on a Mac tracked as v4.13 AR-26 | - |
| v2.4#WN-v24-3 | A/v2/v2.4/known-gaps.md | Antigravity CLI live-VM probe | RESOLVED | v3.0 WN-v30-8 marked CLOSED 2026-09-29 (A/v3/v3.0/known-gaps.md:38) | - |
| v4.0#DF-1 (agent-comm) | A/v4/v4.0/known-gaps.md | Non-lockstep templates lacked contract check | RESOLVED | Line 47 "(resolved)"; resolution 2026-09-22 aggregate suite in `make validate` and `platform-contracts` group | - |
| v4.0#WN-2 | A/v4/v4.0/known-gaps.md | Concurrent branch added a 13th template | RESOLVED | Resolution 2026-09-22: `base-pi.md` in substantive roster | - |
| v4.0#MT-1 | A/v4/v4.0/known-gaps.md | No runtime check that a reply follows the contract | PLAN | Rejected as a hook gate in `docs/decisions/implemented/policy/2026-08-18-agent-communication-contract.md`; any partial check is new runtime design (v4.13 inventory keeps it open) | - |
| v4.0#MT-3 | A/v4/v4.0/known-gaps.md | Local gate did not enforce the CI Python floor | RESOLVED | `scripts/check_python_floor.py` exists and runs in fast/full profiles | - |
| v4.0#DF-1 (CI/CD) | A/v4/v4.0/known-gaps.md | Report artifacts not uploaded | RESOLVED | Resolution 2026-09-22: PR #235 and #243 hosted artifacts | - |
| v4.0#DF-2 | A/v4/v4.0/known-gaps.md | `full` profile never run end to end | RESOLVED | Resolution 2026-09-22: Windows full run 59/59 commands in 7,208.2 s | - |
| v4.0#WN-1 | A/v4/v4.0/known-gaps.md | Event topology not exercised on real GitHub | RESOLVED | Resolution 2026-09-22: PR #245, runs 35828718066, 35826047174, 34939156733 | - |
| v4.1#DF-1 (v4.1.0) | A/v4/v4.1/known-gaps.md | Prompting profile vs live Codex roster | PLAN | Needs live Codex host roster and `/tune-prompting` calibration | - |
| v4.1#DF-1 (v4.1.1) | A/v4/v4.1/known-gaps.md | Optional scanners never executed live | PLAN | Needs a host with Semgrep, gitleaks, OSV, Trivy, Checkov and receipts | - |
| v4.2#DF-2 (v4.2.2) | A/v4/v4.2/known-gaps.md | Five-person Training workshop not run | PLAN | Needs five human participants | - |
| v4.2#DF-2 (v4.2.3) | A/v4/v4.2/known-gaps.md | Same workshop, repeated entry | PLAN | Same obligation, counted once in v4.13 inventory | - |
| v4.3#DF-1 | A/v4/v4.3/known-gaps.md | Inline validators outside native profiles | RESOLVED | Resolution 2026-09-22: PR #241, run 35820761181 | - |
| v4.3#DF-2 | A/v4/v4.3/known-gaps.md | Pip caches not keyed by manifests | RESOLVED | Resolution 2026-09-22: PR #241/#242 cache-key hits | - |
| v4.3#DF-3 | A/v4/v4.3/known-gaps.md | Report profile does not aggregate evidence | RESOLVED | Resolution 2026-09-22: PR #243 aggregate with coverage XML and SARIF | - |
| v4.3#DF-4 | A/v4/v4.3/known-gaps.md | OpenClaw tool interception needs a typed plugin | PLAN | Accepted limit; needs a scoped plugin design and OpenClaw host | - |
| v4.3#DF-5 | A/v4/v4.3/known-gaps.md | Ownership guard had no per-write root, silent refusal | RESOLVED | Heading "(resolved post-release)"; `scripts/lib/integrations/_owned.py:109` emits a refusal reason | - |
| v4.3#WN-3 | A/v4/v4.3/known-gaps.md | Optional platform surfaces unverified | PLAN | Needs authenticated Antigravity, Cursor UI, Gemini IDE and Nexus-AI read-backs | - |
| v4.4#DF-1 | A/v4/v4.4/known-gaps.md | Platform text treatments instead of marks | RESOLVED | Heading "(resolved in v4.4.1)"; closure 2026-09-24 with asset-provenance ledger | - |
| v4.4#WN-1 | A/v4/v4.4/known-gaps.md | Phase 1 ran one tier below recommendation | OBSOLETE | Session-delta record, no tree defect; same class the v4.13 inventory dismisses for v4.5 WN-2/v4.7 WN-1 (v4.13 known-gaps.md, note after inventory table) | - |
| v4.4#WN-2 | A/v4/v4.4/known-gaps.md | Phase 1 superseded-assertion register incomplete | OBSOLETE | Advice targeted v4.4.1 Phases 3-7, which closed; later v4.4.6 redesign was rejected by the user | - |
| v4.5#DF-1 | A/v4/v4.5/known-gaps.md | Writing Discipline benefit unverified by a person | PLAN | Needs human comparison of live replies on two platforms | - |
| v4.5#DF-2 | A/v4/v4.5/known-gaps.md | Agent isolation and reachability not applied to own surface | PLAN | Bounded audit 2026-09-24 found the shared checkout fails isolation; needs real isolation design | - |
| v4.5#WN-2 | A/v4/v4.5/known-gaps.md | Phases ran one effort level below plan | OBSOLETE | v4.13 inventory note: "record surfaced model-effort deviations, not present-tree defects" | - |
| v4.5#MT-1 | A/v4/v4.5/known-gaps.md | Four human/manual tests not run | PLAN | Needs throwaway installs on three non-Claude platforms and human judgement | - |
| v4.7#DF-2 | A/v4/v4.7/known-gaps.md | Codex CLI picker lacks `gpt-6-astra` | PLAN | Needs live Codex CLI recheck (still six models on 2026-09-24) | - |
| v4.7#DF-4 | A/v4/v4.7/known-gaps.md | Reusable `workflow_call` CI factoring excluded | PLAN | Maintainer decision: decline record or scoped CI release | - |
| v4.7#DF-5 | A/v4/v4.7/known-gaps.md | Per-skill presentation metadata excluded | PLAN | Maintainer decision; no consumer exists | - |
| v4.7#WN-1 | A/v4/v4.7/known-gaps.md | Phases ran one effort level below plan | OBSOLETE | v4.13 inventory note names v4.7 WN-1 as not a present-tree defect | - |
| v4.7#WN-2 | A/v4/v4.7/known-gaps.md | Scheduled `main` supply-chain audit red | RESOLVED | `--skip-editable` landed (supply-chain-watch.yml:77, commit 2b6e72017); scheduled `main` run 36428351051 succeeded 2026-09-28. Caveat: scheduled run 37322151526 on 2026-10-05 failed with "Found 1 known vulnerability in 1 package"; record that as a NEW gap | - |
| v4.8#WN-A | A/v4/v4.8/known-gaps.md | Guide had 201 bytes size headroom | RESOLVED | Closed 2026-09-23 after PR #267 (`dc439012`); 4,533 bytes headroom under `SIZE_BUDGET_BYTES = 500_000` (tests/guides/test_nexus_hub_guide.py:23) | - |
| v4.8#WN-C | A/v4/v4.8/known-gaps.md | `make test` hidden editable-install prerequisite | RESOLVED | RESOLVED 2026-09-22; Makefile:96 `dev:` target | - |
| v4.8#WN-B | A/v4/v4.8/known-gaps.md | Size test measured checkout bytes | RESOLVED | Heading says "(fixed here)"; test normalizes CRLF | - |
| v4.8#WN-D | A/v4/v4.8/known-gaps.md | `make` absent on dev host | RESOLVED | RESOLVED 2026-09-07; AGENTS.md:509-517 make-free profiles | - |
| v4.8#WN-E | A/v4/v4.8/known-gaps.md | Phase 4 ran below recommended tier | RESOLVED | Body "CLOSED 2026-09-07 (post-merge) as a record" | - |
| v4.8#WN-F | A/v4/v4.8/known-gaps.md | Nothing detects a framework tag losing its body support | RESOLVED | Process resolution 2026-09-23: `security-framework-mapping/SKILL.md:125` "Re-verify declared mappings" per release, invoked by `version-upgrade` (recurring obligation, not an unbuilt gate) | - |
| v4.8#DF-1 | A/v4/v4.8/known-gaps.md | Review skills did not name verifier class | RESOLVED | `multi-agent-code-review/SKILL.md:123` "Name the verifier class per finding" | - |
| v4.8#WN-G | A/v4/v4.8/known-gaps.md | Coverage parser kept trailing comments | RESOLVED | `scripts/build_framework_coverage.py:103` `strip_comment`; test in tests/validators/test_build_framework_coverage.py | - |
| v4.8#WN-H | A/v4/v4.8/known-gaps.md | Coverage parser ignored block sequences | RESOLVED | `build_framework_coverage.py:182` `collect_block_sequence`; same test module | - |
| v4.8#WN-I | A/v4/v4.8/known-gaps.md | Two Windows test failures | RESOLVED | PowerShell half fixed (tests/installer/test_core_settings_seeding.py:94 `_DECODE`); org-CLI half resolved 2026-09-23 via v4.9 follow-up | - |
| v4.8#WN-J | A/v4/v4.8/known-gaps.md | Pre-flight diffed against local develop | RESOLVED | RESOLVED 2026-09-07: runbook step 9F.2 requires `origin/<base>` counts | - |
| v4.8#WN-K | A/v4/v4.8/known-gaps.md | High CodeQL alert in installer; CodeQL not a required context | PLAN | The installer alert is fixed (alert 242 `fixed` on main 2026-09-13; `_owned.py:121 _STAGING_MODE = 0o600`), but the other four named alerts (py/clear-text-logging, py/bad-tag-filter, js/xss-through-dom) are still open on main and the required-context decision needs the maintainer | - |
| v4.8#WN-1 | A/v4/v4.8/known-gaps.md | Pushy descriptions exceed 250-char full-mode check | OBSOLETE | Duplicate of v4.13 AR-06 (description cap vs trigger-rich rule), which owns the decision | - |
| v4.8#WN-3 | A/v4/v4.8/known-gaps.md | Bash hook tests cannot run on Windows host | RESOLVED | Resolution 2026-09-24, 7/7 pass with Git Bash; A/v4/v4.8/development/windows-lint-autofix-qualification.md | - |
| v4.9#MT-1 | A/v4/v4.9/known-gaps.md | Prompting roster freshness incomplete | PLAN | Needs a complete live Claude model-ID enumeration from the account | - |
| v4.9#WN-1 (follow-up) | A/v4/v4.9/known-gaps.md | Cursor/Gemini claims family-scoped | RESOLVED | Closed 2026-09-27 after PR #348 (`44c00615`) with evidence-scope decision record | - |
| v4.9#WN-1 (v4.9.0) | A/v4/v4.9/known-gaps.md | Private harness cleanup was policy-blocked | RESOLVED | Resolution 2026-09-24: directory removed, A/v4/v4.9/development/private-harness-residue-disposition.md | - |
| v4.9#MT-2 | A/v4/v4.9/known-gaps.md | Platform filesystem cases need matching host | RESOLVED | RESOLVED 2026-09-22: Windows 90 pass and Ubuntu WSL 94 pass by name | - |
| v4.9#MT-3 | A/v4/v4.9/known-gaps.md | Real-deck slide-check coverage incomplete | PLAN | Fragment-budget failures, other SVG marks, figure re-layout and static-stage checks remain open; needs a real `.slide-stage` deck or runtime scorer | - |
| v4.9#QG-1 | A/v4/v4.9/known-gaps.md | Windows CI selects new filesystem tests | RESOLVED | Heading "(resolved)"; hosted PR #190 merged `bd2c8968` | - |
| v4.10#EV-1 | A/v4/v4.10/known-gaps.md | Gemini CLI lacks all-config isolation | PLAN | Vendor feature gap; branch stays fail-closed | - |
| v4.10#EV-2 | A/v4/v4.10/known-gaps.md | OpenCode lacks all-config isolation | PLAN | Vendor feature gap; branch stays fail-closed | - |
| v4.10#WN-3 | A/v4/v4.10/known-gaps.md | `test_target_manifest.py` red on develop | RESOLVED | **Status**: RESOLVED 2026-09-12 by PR #199 | - |
| v4.10#DF-1 | A/v4/v4.10/known-gaps.md | Registration documented as three files, five needed | RESOLVED | AGENTS.md:229 "update all five catalog-state files" | - |
| v4.10#WN-1 | A/v4/v4.10/known-gaps.md | Residual-reference check scans Markdown only | RESOLVED | RESOLVED 2026-09-23 by PR #262 (`30ecff7b`) | - |
| v4.10#WN-2 | A/v4/v4.10/known-gaps.md | Fast profile misses registry drift | RESOLVED | scripts/ci/profiles.py:174 runs `check_registry_entries --check --strict` | - |
| v4.10#MT-1 | A/v4/v4.10/known-gaps.md | Repo description states old catalog size | RESOLVED | RESOLVED 2026-09-22 via GitHub setting | - |
| v4.10#WN-4 | A/v4/v4.10/known-gaps.md | Scoped weekly bar never alerts | RESOLVED | RESOLVED 2026-09-24, opt-in `weeklyScoped` with decision record | - |
| v4.10#MT-2 | A/v4/v4.10/known-gaps.md | Weekly bars not exercised in extension host | RESOLVED | RESOLVED 2026-09-24 with packaged VSIX host render | - |
| v4.11#SEC-1 | A/v4/v4.11/known-gaps.md | Eight CodeQL alerts on main | RESOLVED | 2026-09-28 hosted closure: alerts 278-285 `fixed` after run 36412459737 | - |
| v4.11#WN-1 | A/v4/v4.11/known-gaps.md | Every release invalidates the distribution handbook | RESOLVED | Status resolved 2026-09-22; pre-version handbook refresh in catalog/commands/update.md:60, :258 | - |
| v4.11#MT-5 | A/v4/v4.11/known-gaps.md | No coverage for values fabricated mid-animation | RESOLVED | v4.11.2 MT-5 resolved 2026-09-24 within the DOM-text envelope (same ledger, lines 45-58) | - |
| v4.11#MT-9 | A/v4/v4.11/known-gaps.md | Inert control not detected | RESOLVED | Closed 2026-09-25 after PR #298 (`1ae58ad5`) for the declared-control method | - |
| v4.11#MT-10 | A/v4/v4.11/known-gaps.md | No authored connector diagram qualified geometry checks | RESOLVED | Closed 2026-09-24 after PR #269 (`91617927`) | - |
| v4.12#BG-2 | A/v4/v4.12/known-gaps.md | New-branch push trusted another remote | RESOLVED | Resolution 2026-09-22, PR #244 (`07e31f95`); also listed under `### Resolved` | - |
| v4.12#BG-3 | A/v4/v4.12/known-gaps.md | Shared attribution hooks tied to installer worktree | RESOLVED | Resolution 2026-09-23, PR #250 (`4753784d`) | - |
| v4.12#WN-1 | A/v4/v4.12/known-gaps.md | CI-profile lint findings | RESOLVED | scripts/ci/profiles.py:25 `from collections.abc import Mapping, Sequence` | - |
| v4.12#WN-2 | A/v4/v4.12/known-gaps.md | CI reporting and tool-lock differences | RESOLVED | RESOLVED 2026-09-22, PR #238 (`3ee00582`) | - |
| v4.12#WN-3 | A/v4/v4.12/known-gaps.md | Repo description count drift | RESOLVED | RESOLVED 2026-09-22 | - |
| v4.12#QG-1 | A/v4/v4.12/known-gaps.md | GitHub retains read-only PR refs | PLAN | GitHub platform boundary; only a GitHub Support disposition can change it | - |
| v4.12#QG-2 | A/v4/v4.12/known-gaps.md | Public Code sidebar still shows 5 contributors | PLAN | Needs maintainer to file the prepared GitHub Support handoff | - |
| v4.12#QG-3 | A/v4/v4.12/known-gaps.md | Independent adversarial review incomplete | RESOLVED | RESOLVED 2026-09-22; also under `### Resolved` | - |
| v4.12#QG-4 | A/v4/v4.12/known-gaps.md | Windows whole-repo profile timed out | RESOLVED | RESOLVED 2026-09-22, partitioned profile 59/59 | - |
| v4.12#DF-1 | A/v4/v4.12/known-gaps.md | Antigravity workflow surface retires 2026-11-01 | PLAN | Dated: act only after 2026-11-01 with a fresh vendor-date check (today is 2026-10-08) | - |

## QUICK batch

Grouped by file:

1. `scripts/check_installer_smoke.py` (one edit closes v1.1#DF-006 and v1.1#DF-008):
    1. Append `"package_skill.py"`, `"aggregate_benchmark.py"`, `"skill_eval_viewer.py"`, `"optimize_skill_description.py"` and `"generate_report.py"` to the `EXPECTED_SCRIPTS` tuple (lines 14-20).
    2. Verify locally with a throwaway install (`bash scripts/installer.sh --workspace <tmp> --platforms claude --yes` under a redirected `HOME`, then `python scripts/check_installer_smoke.py --home <tmp-home> --workspace <tmp>`). The macOS and Linux proof then comes from the existing `installer-smoke` CI matrix at the plan's final push.

## Ledger bookkeeping (needed to clear RESOLVED and OBSOLETE items from `minor_close.py status`)

This is mechanical work, not gap work. Plan it as one batch:

- Add parser-readable markers. RESOLVED items need ` - RESOLVED <date>` (or ` - CLOSED <date>`) at the end of the heading. OBSOLETE items need ` - CLOSED <date> (superseded by v4.13 AR-NN)`. Transferred v2.4 items can take ` - MIGRATED to v3.0.0`. Files: A/v1/v1.1, A/v1/v1.3, A/v2/v2.0, A/v2/v2.3, A/v2/v2.4, and A/v4/v4.0, v4.3, v4.4, v4.5, v4.7, v4.8, v4.9, v4.10, v4.11, v4.12 `known-gaps.md`.
- `minor_close.py status` also reports `unparsed` rows at A/v2/v2.4/known-gaps.md:147-165. Those Resolved-table rows start like item IDs, which makes that ledger `cannot-verify`. Fix that ledger's table form in the same batch.
- The v4.0-v4.12 ledgers are hash-bound in `docs/releases/v4/v4.13/known-gaps.md`, in the archive-hash table under "Historical carry-forward". Any heading edit requires recomputing those normalized SHA-256 values with a dated re-binding note, as the 2026-09-29 re-binding did.
- New finding to record: the `main` supply-chain watch failed again on 2026-10-05 (run 37322151526, one known vulnerability in one package). It is not v4.7#WN-2's original cause; it needs its own gap entry and triage.
