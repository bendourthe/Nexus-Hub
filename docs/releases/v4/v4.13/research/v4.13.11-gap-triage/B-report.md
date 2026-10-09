# Known-gaps triage, group B (v3.15 and v3.16 inherited items)

Repository checked: `Nexus-Hub-worktrees/v41310` (branch `feat/v4.13.10-training-page-rebuild`). Read-only; no repository file was changed.

**Counts**: RESOLVED 57 | OBSOLETE 7 | QUICK 8 | PLAN 29 | total 101

Abbreviations: `K15` = `docs/archives/v3/v3.15/known-gaps.md`, `K16` = `docs/archives/v3/v3.16/known-gaps.md`, `K413` = `docs/releases/v4/v4.13/known-gaps.md`. Line numbers are the item's heading line. Row order matches `B.txt` (101 rows, same order as `minor_close.py status`).

## Why these 101 items still parse as open

Most of these items were already dispositioned by the 2026-09-29 archive reconciliation, but `scripts/completion_minor.py` cannot read the disposition from the heading, so `gaps.minor` keeps reporting them. Three heading shapes defeat the parser:

1. `- MIGRATED to v4.13 (AR-xx)`: `MIGRATED_RE` (completion_minor.py:1036) requires a full `vX.Y.Z` at the very end of the title. 29 headings carry this shape.
2. `- CLOSED earlier in this file`, `ID RESOLVED - ...` (no leading hyphen), `(RESOLVED)` / `(RESOLVED, Phase 7)` in parentheses mid-title, and bare titles with the verdict only in the body: `_RESOLVED_END_RE` / `_RESOLVED_PREFIX_RE` (completion_minor.py:1040-1043) accept only `- RESOLVED|CLOSED` as prefix, or as suffix optionally followed by a date or one parenthetical.
3. Subsections named `v3.15.1 Resolved` / `v3.15.7 Phase 7 Resolved`: the subsection rule only fires when the subsection starts with `resolved`.

The archive reconciliation tables (`K15` line 2299 onward, `K16` line 1329 onward) also targeted only each patch's authoritative entry, so duplicate re-listings of the same id (HO-5 x4, WN-5 x2, DF-1/DF-2/MT-1 across patches) were never marked. So RESOLVED and OBSOLETE below are substantive verdicts. The minor still will not close until those headings get a parseable marker (see the bookkeeping batch at the end).

## Triage table

| Gap | Source file | One-line summary | Class | Evidence or fix | Files |
|---|---|---|---|---|---|
| v3.15#DC-1 | K15:108 | Decision record: `implementation-plan` chosen as plan layer | RESOLVED | Decision, no action; K15 v3.15.14 Phase 4.3 "Needing no action: DF-1, EN-1, DC-1" (K15:~70) | - |
| v3.15#EN-1 | K15:142 | Extra rationalization row added beyond plan | RESOLVED | Enhancement record; same Phase 4.3 "Needing no action" list | - |
| v3.15#QG-1 | K15:193 | Plan said 269 skills, catalog had 270 | RESOLVED | K15 Phase 4.3 "QG-1 - CLOSED": CHANGELOG states 270 | - |
| v3.15#MT-1 | K15:202 | No check that spec template, checklist and skill agree | RESOLVED | `tests/skills/test_spec_artifact_agreement.py` exists (21 cases, mutation-tested per K15 Phase 4.3) | - |
| v3.15#HO-5 | K15:241 | Cursor wire contract unverified against a live account | RESOLVED | Superseded by HO-7 CLOSED (K15:232); `extensions/cursor-usage-monitor/src/providers/liveTransport.ts:44-45` `wire/v2-rpc-verified`, `verified: true` | - |
| v3.15#WN-5 | K15:250 | Live transport needs Node 22.13+ (`node:sqlite`) in Cursor's host | RESOLVED | K15:575 "WN-5 - RESOLVED": Cursor host is Electron 40.10.3 / Node 24.15.0 with `node:sqlite` available | - |
| v3.15#HO-6 | K15:380 | VS Code session vs billing endpoint needs live probe | OBSOLETE | GitHub usage monitor removed in v3.18.2 (`docs/decisions/implemented/architecture/2026-08-22-withdraw-the-github-usage-monitor.md`; `extensions/github-usage-monitor` absent); also answered at K15:526 | - |
| v3.15#HO-5 | K15:535 | Probe-complete negative result (route returned 403) | RESOLVED | Later retracted and closed by HO-7 (K15:232) with verified Connect RPC; liveTransport.ts:44-45 | - |
| v3.15#HO-5 | K15:581 | "Advanced, still open" probe note | RESOLVED | Self-marked SUPERSEDED; final closure HO-7 (K15:232) | - |
| v3.15#WN-5 | K15:588 | Probe ran on system Node, not Cursor's host | RESOLVED | Answered by K15:575 using `ELECTRON_RUN_AS_NODE=1` on Cursor's own runtime | - |
| v3.15#HO-5 | K15:763 | Authorized Cursor probe needed before session reuse | RESOLVED | Same HO-5; probe done and closed by HO-7 (K15:232), liveTransport.ts:44-45 | - |
| v3.15#WN-4 | K15:796 | `@vscode/vsce` transitive deprecation warnings | PLAN | Migrated as AR-49 (K413:555); upstream-bounded, needs an upstream vsce release | - |
| v3.15#DF-1 | K15:964 | Legacy Cursor global commands path unverified | PLAN | AR-47 (K413:375); needs a Cursor read-contract verification against vendor docs before removing the write | - |
| v3.15#DF-4 | K15:985 | OpenCode hooks out of scope | RESOLVED | Decision recorded in entry; `scripts/lib/integrations/opencode.py:77` `"hooks_supported": False` | - |
| v3.15#DF-3 | K15:1022 | Contextmap ORM/framework detectors deferred | PLAN | AR-52 (K413:561); six new detectors with fixtures, multi-file feature | - |
| v3.15#WN-2 | K15:1041 | Ruff F401/F841 in `graph/affected.py` | QUICK | Still present (`ruff check --select F401,F841` reports 2). Drop unused `EdgeKind` from line 29 import and the unused `frontier` assignment at line 190 | `extensions/nexus-code-search/src/nexus_code_search/graph/affected.py` |
| v3.15#MT-2 | K15:1049 | `benchmark --update-baseline` write path untested | QUICK | No test calls `main(["--update-baseline"])`. Add a test that monkeypatches `benchmark.BASELINE_PATH` to `tmp_path` and asserts the written JSON equals `measured_baseline(report)` | `extensions/nexus-code-search/tests/test_context_map_measurement.py` |
| v3.15#MT-1 | K15:1055 | `nexus-hub map` dispatch has no test | QUICK | `scripts/nexus_hub_cli.py:1273` dispatches to `cmd_map` (631), untested. Add a test injecting a fake `nexus_code_search.contextmap.cli` module via `sys.modules` and asserting argv is forwarded and its return code propagated | new `tests/integrations/test_nexus_hub_map_dispatch.py` (or an existing CLI test module) |
| v3.15#DF-1 | K15:1063 | Overview frameworks line + Most-Imported Files | RESOLVED | Heading and entry say RESOLVED (subsection "v3.15.1 Resolved") | - |
| v3.15#DF-2 | K15:1067 | nexus-code-search package version bump | RESOLVED | Heading says RESOLVED, Phase 7 | - |
| v3.15#QG-1 | K15:1071 | Duplicate extension-test run across workflows | RESOLVED | Heading says RESOLVED by decision, Phase 7 | - |
| v3.15#QG-2 | K15:1075 | Three plans stamped v3.15.0 | RESOLVED | Re-stamped 2026-07-22; K15 top "Scope note (version collision, RESOLVED)" | - |
| v3.15#DF-2 | K15:1121 | Hermes not wired into installers | PLAN | AR-05 (K413:295); installer edits in both scripts plus smoke tests ("ask first" per AGENTS.md) or a maintainer decision to keep registry-only | - |
| v3.15#MT-1 | K15:1139 | Trigger-case coverage is a first tranche | PLAN | AR-09 (K413:431); 88 of 338 skills, catalog-wide authoring effort | - |
| v3.15#DF-1 | K15:1191 | Self-check eval-loop authoring convention | PLAN | AR-53 (K413:497); new convention plus reference template, design work | - |
| v3.15#DF-3 | K15:1257 | Presentify overlay-annotation heuristic over-captures | PLAN | AR-18 (K413:511); extractor redesign | - |
| v3.15#DF-1 | K15:1264 | Presentify builder has no `.gallery` grouping | PLAN | AR-18; builder feature | - |
| v3.15#DF-2 | K15:1271 | PDF raster `page_fraction` null on bbox mismatch | PLAN | AR-18; extractor matching logic plus fixtures | - |
| v3.15#MT-1 | K15:1280 | Rendered-width check skips without headless browser | RESOLVED | Entry appended "CLOSED 2026-08-11 by v3.16.5 Phase 3"; `.github/workflows/presentify-extractor.yml:151` `render:` job | - |
| v3.15#MT-2 | K15:1291 | Consented stock/mix placement is agent behavior | RESOLVED | Entry appended "CLOSED 2026-08-11 by v3.16.5 Phase 5"; `visual_qa_score.py` checks the `IMAGERY PLACEMENTS` record | - |
| v3.15#MT-3 | K15:1300 | Visual-QA agent grading and sample-deck smoke are behavioral | PLAN | AR-19 (K413:517); needs a rendered or agent-vision run | - |
| v3.15#BG-1 | K15:1314 | Builder lost theme colors | RESOLVED | Heading: PRE-EXISTING; RESOLVED in Phase 7 | - |
| v3.15#DF-2 | K15:1411 | Model-specific content in shared bodies unguarded vs hand edits | PLAN | Accepted residual "Carried forward, not closed"; the fix is a new `check_model_specific_leakage.py` validator with an allowlist and triage of 16 existing mentions (new gate needs a decision record) | - |
| v3.15#MT-4 | K15:1435 | `DEFAULT_GUARDS` suite never run end to end | PLAN | AR-08; real guards run five full-repo validators (`apply_prompting_edits.py:92-98`), so an e2e test needs a fixture-repo design and a CI-cost decision | - |
| v3.15#MT-2 | K15:1449 | Subprocess validator tests unmeasured for coverage | PLAN | AR-33 (K413:479); coverage plumbing across CI | - |
| v3.15#DF-3 | K15:1552 | Strict overlay omits `defaultMode` | PLAN | AR-54 (K413:387); needs a permissions-owner decision and enum verification against Claude docs | - |
| v3.15#DF-1 | K15:1559 | `ai-agent-governance` has no SKIP clause | QUICK | Description (SKILL.md:3) still has no SKIP. Append "SKIP: hardening the coding-agent endpoint against config-write escapes (use agentic-endpoint-hardening)." and mirror into `data/skills.json`; run `check_registry_entries.py --check --strict` | `catalog/skills/compliance/ai-agent-governance/SKILL.md`, `data/skills.json` |
| v3.15#DF-2 | K15:1569 | Bare-`bash` hook failure class | RESOLVED | Heading "DF-2 RESOLVED"; PATH repair in `catalog/hooks/tests/conftest.py` per K15 correction notice | - |
| v3.15#BG-5 | K15:1576 | `session-summary.ps1` never parsed | RESOLVED | Heading RESOLVED; `catalog/hooks/tests/test_hook_sibling_parity.py` AST-parses every `.ps1` | - |
| v3.15#QG-1 | K15:1585 | CI hardening diffs plus Windows leg | RESOLVED | Heading RESOLVED; Windows `tests-windows` leg documented in AGENTS.md | - |
| v3.15#HO-2 | K15:1591 | `NEXUS_HUB_INIT=1` export | RESOLVED | `scripts/installer.sh:4258`, `scripts/installer.ps1:3993` | - |
| v3.15#HO-1 | K15:1598 | Hook-test verification route | RESOLVED | Heading RESOLVED; conftest PATH repair | - |
| v3.15#BG-1 | K15:1605 | `escalation-trigger.sh` inert in production | RESOLVED | Heading RESOLVED; `catalog/hooks/tests/test_escalation_trigger.py` parametrized over both siblings | - |
| v3.15#BG-2 | K15:1612 | No-jq fallback did not decode JSON escapes | RESOLVED | Heading RESOLVED | - |
| v3.15#BG-6 | K15:1649 | Description gates failed open without `jq` | RESOLVED | Heading RESOLVED | - |
| v3.15#BG-7 | K15:1656 | `git-guardrails.sh` exited 1 on empty command | RESOLVED | Heading RESOLVED | - |
| v3.15#BG-8 | K15:1662 | Description gates blocked on malformed payload | RESOLVED | Heading RESOLVED | - |
| v3.15#WN-3 | K15:1696 | `test_instruction_merge.py` import-order dependence | RESOLVED | K15:1908 resolution; `tests/installer/test_instruction_merge.py:29` fresh-interpreter import test | - |
| v3.15#DF-6 | K15:1861 | Durable monotonic-scrutiny store deferred | PLAN | AR-37 (K413:627); build-or-decline decision | - |
| v3.15#DF-7 | K15:1868 | External vuln-database recon declined | RESOLVED | Closed by recorded decline under MCP Registry Policy; nothing owed | - |
| v3.15#DF-8 | K15:1875 | Provider-key cross-vendor judging declined | RESOLVED | Closed by recorded decline; `cross-model-orchestrator` covers it | - |
| v3.15#DF-9 | K15:1882 | Additive platform capability drift deferred to v3.15.8 | RESOLVED | Entry "RESOLVED (v3.15.8 Phase 9.2)"; K15 Phase 9.2 table row DF-9 Resolved | - |
| v3.15#BG-1 | K15:1893 | Usage-monitor clean-install workflows | RESOLVED | Subsection "v3.15.7 Phase 7 Resolved" | - |
| v3.15#BG-2 | K15:1898 | Three CI defects on first release PR | RESOLVED | Same Resolved subsection | - |
| v3.15#BG-3 | K15:1903 | Windows push-only gate defects | RESOLVED | Same Resolved subsection | - |
| v3.15#WN-3 | K15:1908 | Import cycle resolved | RESOLVED | Resolution entry itself; test at `tests/installer/test_instruction_merge.py:29` | - |
| v3.15#QG-2 | K15:1952 | CI does not collect `tests/plans` | RESOLVED | `scripts/ci/profiles.py:359` `_pytest("repo-tests-plans", "tests/plans")` | - |
| v3.15#QG-3 | K15:1986 | GitHub Usage Monitor tests not collected | OBSOLETE | Monitor removed in v3.18.2 (decision record above; directory absent) | - |
| v3.15#MT-6 | K15:2115 | Codex agent/hook delivery not observed on a real install | PLAN | AR-57 (K413:399); needs a host with Codex installed | - |
| v3.15#DF-12 | K15:2152 | Gemini CLI extension-packaged hooks unused | PLAN | AR-56 (K413:393); upstream-blocked | - |
| v3.15#MT-7 | K15:2161 | Gemini CLI / Qwen Windows shell dispatch not observed | PLAN | AR-57; needs live installs | - |
| v3.15#DF-13 | K15:2203 | Kimi has no project-scoped hook path | PLAN | AR-56; upstream-blocked | - |
| v3.15#MT-8 | K15:2212 | Kimi agent/hook delivery not observed | PLAN | AR-57; needs a live Kimi install | - |
| v3.16#TR-1 | K16:21 | Spec template A1 example is a Non-Goal phrased as an Assumption | QUICK | `catalog/templates/spec-template.md:171` unchanged; no test pins it. Replace the A1 example with a genuine overridable default (drop "JWT is out of scope"), add the JWT exclusion as a Non-Goal example, and reword the note at line 140 so it no longer points at A1 | `catalog/templates/spec-template.md` |
| v3.16#TR-2 | K16:28 | v3.11 spec-kit items S5, S6, S8 carry no status claim | PLAN | AR-15 (K413:455); needs a fresh spec-kit delta comparison against upstream | - |
| v3.16#CD-1 | K16:54 | Re-entrancy guard for loop-engineering | PLAN | AR-12 (K413:437); no re-entrancy text in `loop-engineering/SKILL.md`; needs an environment-marker contract design that does not forbid legitimate nesting | - |
| v3.16#CD-2 | K16:61 | Extend egress-redaction to local persistence and error surfaces | QUICK | `egress-redaction/SKILL.md` has no local-persistence or error-surface boundary. Add both boundaries to the existing scope list, reusing the existing Credentials BLOCK verdict (no new table), and add a matrix row | `catalog/skills/security/egress-redaction/SKILL.md`, `docs/policy/mcp-reverse-engineering-matrix.md` |
| v3.16#CD-3 | K16:68 | Repair-loop prompt-size cross-link | QUICK | Absent from `loop-engineering/SKILL.md` (256 lines). Add one line naming the failure mode, with `[[context-compression]]` / `[[prompt-token-optimization]]` and inter-round compaction as the mitigation | `catalog/skills/workflow/loop-engineering/SKILL.md` |
| v3.16#DF-1 | K16:97 | No per-job CI path filter for drift check | RESOLVED | K16 v3.16.0 Phase 5 table (K16:~257) "Closed as deliberate" | - |
| v3.16#NI-1 | K16:112 | `configs/` not distributed to installed trees | PLAN | AR-30 (K413:331); installer distribution change, "ask first" | - |
| v3.16#WN-1 | K16:126 | Stale git worktree admin entries | RESOLVED | Phase 5 table "Closed as environmental" | - |
| v3.16#NI-2 | K16:141 | Copilot lever on an unintegrated surface | RESOLVED | K16:181 "NI-2 - RESOLVED: ... deliberate expansion" | - |
| v3.16#NI-3 | K16:148 | `~/.gemini/settings.json` single owner | RESOLVED | Phase 5 table "Closed"; `tests/validators/test_platform_defaults_seeding.py:90` `test_gemini_never_declares_a_write_target` | - |
| v3.16#NI-4 | K16:155 | Four platforms are deliberate non-implementations | RESOLVED | Phase 5 table: closed as deliberate non-implementations | - |
| v3.16#NI-5 | K16:187 | Four verified platforms declared but not writable | RESOLVED | Phase 5 table: closed as deliberate | - |
| v3.16#NI-6 | K16:194 | Hermes seedable but not installed by default | PLAN | AR-05; same installer wiring as v3.15#DF-2 | - |
| v3.16#NI-6 | K16:452 | PowerShell early-exit leaks the staging dir | PLAN | AR-10 (K413:301); residual documented at `scripts/installer.ps1:4163-4173`; try/finally around the post-`Resolve-Selection` flow is an installer edit needing approval and a Windows run | - |
| v3.16#MT-1 | K16:477 | Loop-schema gate types and duplicate `gates` block unasserted | QUICK | Neither assertion is in `tests/validators/test_loop_engineering_bundle.py`. Add (a) Fields-table gate types equal Human-Judgment Gates table types, (b) `ship-pr-until-green` `gates` block identical in `loop-schema.md` and `loop-library.md` | `tests/validators/test_loop_engineering_bundle.py` |
| v3.16#NI-1 | K16:496 | `update.md` references a missing `nexus-hub doctor` | RESOLVED | K16:556 "NI-1 - RESOLVED in Phase 5"; `scripts/installer.sh:3637` `doctor` subcommand | - |
| v3.16#DF-1 | K16:503 | Capability usage gate has no checker | RESOLVED | K16:560; `scripts/check_release_capability_docs.py` exists | - |
| v3.16#BG-2 | K16:521 | `secret-scan.sh` fails open without `jq` | RESOLVED | AR-02 RESOLVED 2026-09-30 (K413:273); `catalog/hooks/secret-scan.sh:68-81` jq, then Python fallback, then fail closed | - |
| v3.16#NI-2 | K16:535 | Two skills over 500-line body target | PLAN | AR-07 (K413:419); body splits into `references/` | - |
| v3.16#MT-1 | K16:670 | GitHub monitor `extension.ts` coverage | OBSOLETE | Monitor removed v3.18.2; also K16:745 RESOLVED in Phase 3 | - |
| v3.16#NI-2 | K16:702 | Billing weight constants to verify | OBSOLETE | Heading "SUPERSEDED 2026-08-22 by v3.18.1"; monitor since removed | - |
| v3.16#NI-3 | K16:713 | Two billing endpoints use different SKU vocabularies | OBSOLETE | K16:808 RESOLVED in Phase 6; monitor removed | - |
| v3.16#NI-5 | K16:751 | First-run resolves owner before session | OBSOLETE | K16:764 RESOLVED in Phase 4; monitor removed | - |
| v3.16#NI-6 | K16:770 | Settings section read-only | OBSOLETE | K16:783 RESOLVED in Phase 5; monitor removed | - |
| v3.16#NI-2 | K16:870 | Presentify contract rules 2-3 have no deterministic check | RESOLVED | Accepted by design in the v3.16.5 Phase 7 terminal table (K16:1006); answered in the render loop | - |
| v3.16#WN-1 | K16:877 | Semantic status colors excluded from contrast set | RESOLVED | Accepted by design, same terminal table | - |
| v3.16#WN-2 | K16:898 | Scorer cannot see runtime-injected palette values | PLAN | AR-19; needs rendered verification | - |
| v3.16#NI-3 | K16:905 | SVG rules 2-3 have no deterministic check | RESOLVED | Accepted by design, terminal table | - |
| v3.16#WN-3 | K16:924 | `em` font sizes render-verified only | RESOLVED | Accepted by design; `max(<relative>, <floor>)` construction checked | - |
| v3.16#NI-4 | K16:954 | Intake questions are agent behavior | RESOLVED | Accepted by design; deterministic half tested | - |
| v3.16#DF-2 | K16:961 | `--images none` changed meaning | RESOLVED | Accepted with decision in terminal table; test asserts disclosure | - |
| v3.16#NI-5 | K16:969 | Placement relevance is a screenshot judgment | RESOLVED | Accepted by design; "Suggested next step: none" | - |
| v3.16#WN-4 | K16:977 | Low-opacity scrim defeats static contrast check | RESOLVED | Accepted by design, terminal table | - |
| v3.16#DF-3 | K16:985 | Local knockout helper not adopted | RESOLVED | Declined for no call site (AGENTS.md scope-fit gate), terminal table | - |
| v3.16#DF-4 | K16:992 | Plan contradicted itself on naming upstream | RESOLVED | CORRECTED; `tests/skills/test_presentify_cinematic.py:116` `test_no_vendor_name_reaches_a_distributed_artifact` | - |
| v3.16#NI-2 | K16:1127 | Presentify Gates A, B, E have no checker | PLAN | AR-19; agent-behavior gates need rendered/vision runs | - |
| v3.16#NI-3 | K16:1134 | Composition probes not implemented in a helper | PLAN | AR-19; new helper implementation | - |
| v3.16#BG-2 | K16:1163 | Original diagnosis: manifest hashed CRLF bytes | RESOLVED | K16:1156 "BG-2 - CLOSED in v3.16.8"; `tests/validators/test_verify_install.py:450` `test_eol_crlf_path_hashes_its_distributed_crlf_form` | - |

## QUICK items, batched by file

1. `extensions/nexus-code-search/src/nexus_code_search/graph/affected.py`: v3.15#WN-2. Remove the unused `EdgeKind` import (line 29) and the unused `frontier` assignment (line 190), then re-run `python -m ruff check --select F401,F841` on the file.
2. `extensions/nexus-code-search/tests/test_context_map_measurement.py`: v3.15#MT-2. Add an `--update-baseline` write test with `BASELINE_PATH` monkeypatched to `tmp_path`.
3. A new or existing CLI test module under `tests/` (for example `tests/integrations/test_nexus_hub_map_dispatch.py`): v3.15#MT-1. Test that `nexus_hub_cli` routes `map` argv to a stubbed `nexus_code_search.contextmap.cli.main` and returns its code.
4. `catalog/skills/compliance/ai-agent-governance/SKILL.md` plus `data/skills.json`: v3.15#DF-1. Add a SKIP clause pointing to `agentic-endpoint-hardening`, sync the description, and run `python scripts/check_registry_entries.py --check --strict`.
5. `catalog/templates/spec-template.md`: v3.16#TR-1. Rewrite the A1 example (line 171), move the JWT exclusion to a Non-Goals example, and update the line-140 note. Then run `tests/skills/test_spec_artifact_agreement.py`.
6. `catalog/skills/workflow/loop-engineering/SKILL.md`: v3.16#CD-3. Add the one-line prompt-size failure-mode cross-link. The body is 256 lines, under the size-norm test's ceiling.
7. `tests/validators/test_loop_engineering_bundle.py`: v3.16#MT-1. Add the gate-type table parity assertion and the byte-identical `ship-pr-until-green` `gates` block assertion.
8. `catalog/skills/security/egress-redaction/SKILL.md` plus `docs/policy/mcp-reverse-engineering-matrix.md`: v3.16#CD-2. Add the local-persistence and error-surface boundaries to the existing scope list, with no parallel table, and add a matrix row.

Items 6 and 7 share the loop-engineering bundle, so do them together; CD-1 stays PLAN.

## Bookkeeping batch (needed for `gaps.minor` to read these as closed)

The RESOLVED and OBSOLETE verdicts above are substantive. The minor still will not close until each heading carries a marker the parser accepts. These edits are mechanical and touch only `K15` and `K16`:

- For each RESOLVED/OBSOLETE row, append ` - CLOSED 2026-10-08` (or ` - RESOLVED 2026-10-08`) to the heading, replacing any trailing ` - CLOSED earlier in this file`. Normalize prefix forms such as `DF-2 RESOLVED - ...` to `DF-2 - RESOLVED: ...`.
- For each `- MIGRATED to v4.13 (AR-xx)` heading, the shape fails `MIGRATED_RE`. Either rewrite it to end in `- MIGRATED to v4.13.0`, after checking what `verify_migration` requires of the `**Migrated from**` lines in K413, or pick a different convention. Duplicate ids inside one ledger (for example v3.15#DF-1 appears in five patches) may make a migration ambiguous. Confirm the verifier's behavior on duplicates before relying on the rewrite. A dry run of `python scripts/minor_close.py status --minor v4.13 --repo .` after the edit shows whether each row clears.
- After this batch, the PLAN items whose substance already lives in a K413 AR entry carry forward through that AR entry rather than as separate v3.x items.
