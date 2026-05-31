# Known Gaps - v2.4.0

This file tracks per-version unfinished work, deferred items, deviations from plan, and bugs discovered during phase implementation. The next phase plan and the version-bump checklist read this file to decide what carries forward.

**Plan**: [docs/v2.4.0/plans/adoption-compound-engineering-plugin.md](plans/adoption-compound-engineering-plugin.md)
**Status**: in-progress (Phases 1-5 of 8 closed; latest: Phase 5 - Internal RE builds re-full)
**Last updated**: 2026-05-31 (Phase 5 close)

## Summary

| Category | Open | Resolved this version |
|---|---|---|
| NI -- Not implemented (skipped subtask) | 1 | 0 |
| DF -- Deferred (intentionally) | 5 | 0 |
| BG -- Bug or unresolved test failure | 0 | 1 |
| MT -- Missing tests / coverage gap | 0 | 0 |
| WN -- Warning or suppressed lint rule | 1 | 1 |
| QG -- Quality gate bypassed | 0 | 0 |
| **Total** | **7** | **2** |

_Phase 1 resolved 2 of the 15 ingested v2.3.0 gaps (WN-v23-1 count drift, BG-v23-1 secret-scan false positives). The remaining 13 ingested gaps are tracked as sub-tasks in the plan (Phases 2-8) and are not duplicated here until discovered/closed during their phase. Phase 1 added 3 new gaps; Phase 2 added 1 (DF-v24-2) and extended WN-v24-1 with the agent-count delta. Phase 4 added 1 (DF-v24-3) and extended WN-v24-1 to the 242-skill truth. Phase 3 (run after Phase 4, since Phase 4's prerequisite was "None beyond Phase 1") added 1 (DF-v24-4) and extended WN-v24-1 to the 244-skill truth (added `product-strategy` + `session-query`). Phase 5 added 1 (DF-v24-5, live --branch clone+install deferred); it ships docs-only + installer changes, no new skills, so the registries are unchanged at 244._

## Open Items

### NI-v24-1 -- validate_solution_frontmatter.ps1 PowerShell sibling intentionally not created

- **Source phase**: Phase 1 - Foundation (sub-task T003)
- **Plan reference**: `docs/v2.4.0/plans/adoption-compound-engineering-plugin.md` (sub-task 1.3 / T003)
- **Category**: NI -- Not implemented (deliberate convention-based decision)
- **Reason**: T003's prompt asked for a `scripts/validate_solution_frontmatter.ps1` sibling under the "cross-platform parity rule". That rule (AGENTS.md "Per-skill Bundled Resources" + "Installer-Aware Changes") scopes mandatory `.ps1` siblings to `.sh` scripts (bash is not guaranteed on Windows). A `.py` validator is already cross-platform - it runs via `python` on every OS and is copied to `~/.nexus-hub/scripts/` by BOTH installers. All four existing top-level validators (`validate_no_personal_paths.py`, `validate_unicode_safety.py`, `scan_supply_chain_iocs.py`, `validate_workflow_security.py`) are `.py`-only with no `.ps1` sibling. A hand-maintained PowerShell reimplementation of a stdlib YAML-parser-safety checker would be pure duplication with a real sync/correctness risk and would diverge from the established convention.
- **Suggested next step**: No action required. If a maintainer disagrees, the `.py` logic can be ported to `.ps1`; but the recommendation is to keep the single cross-platform `.py` validator. Confirm at version-bump review.

### DF-v24-1 -- Live skill-eval-loop trigger run deferred for the two new Phase-1 skills

- **Source phase**: Phase 1 - Foundation (sub-task T007)
- **Plan reference**: `docs/v2.4.0/plans/adoption-compound-engineering-plugin.md` (sub-task 1.7 / T007)
- **Category**: DF -- Deferred (intentionally; environment constraint)
- **Reason**: T007 asks for a live `skill-eval-loop` trigger run (1.0 on a positive prompt, 0.0 on a fenced negative) for `solution-knowledge-base` and `solution-refresh`. The harness (`scripts/optimize_skill_description.py`) invokes a model CLI (`claude`/`codex`/`gemini`/`opencode`) as a subprocess; none is available on PATH in the implementation environment, and a live run is token-intensive. A static trigger-surface check was performed instead: both descriptions carry explicit verbatim trigger phrases plus a `SKIP` clause, and the two skills cross-fence each other (capture vs audit) to prevent over-trigger. This mirrors the v2.3.0 DF-v23-7 precedent (live run deferred, static check substituted).
- **Suggested next step**: Run the live `skill-eval-loop` for both skills when a model CLI is available - Phase 8 sub-task T037 already targets a Phase-1 knowledge-base skill for a live run; fold these two in there. Author a minimal `evals.json` per skill (one should-trigger, one should-not-trigger prompt) and confirm 1.0 positive / 0.0 negative; tighten the description per `skill-eval-loop/references/improvement-heuristics.md` if under-triggering.

### DF-v24-2 -- Live skill-eval-loop trigger run + full-pipeline benchmark deferred for the two new Phase-2 review skills

- **Source phase**: Phase 2 - Persona review pipeline (sub-task T012)
- **Plan reference**: `docs/v2.4.0/plans/adoption-compound-engineering-plugin.md` (sub-task 2.5 / T012)
- **Category**: DF -- Deferred (intentionally; environment constraint)
- **Reason**: T012 asks for a live `skill-eval-loop` trigger check (1.0 positive / 0.0 fenced-negative) for `multi-agent-code-review` and `plan-review`, and a review-pipeline benchmark. No model CLI (`claude`/`codex`/`gemini`/`opencode`) is on PATH in the implementation environment (same constraint as DF-v24-1). Two substitutes were performed and recorded: (1) a static trigger-surface check confirming both descriptions carry verbatim trigger phrases plus a SKIP clause and cross-fence each other (code-diff vs plan-doc), and (2) a real persona-dispatch benchmark over a seeded fixture - the correctness and security personas each surfaced their planted defect, stayed in lane, emitted the findings-schema JSON contract, and left the clean control untouched (see `docs/v2.4.0/development/phase-2-benchmark/README.md`). The full end-to-end pipeline run (all conditional personas, the independent validation pass, model tiering, cross-reviewer promotion) was not exercised, because the dedicated `*-reviewer` persona agents ship as catalog templates and are not registered as dispatchable subagent types in the authoring harness; the two reused dispatchable agents (`code-reviewer`, `security-reviewer`) validated the contract and lens discipline.
- **Suggested next step**: When a model CLI is available (fold into Phase 8 T037, which already targets a Phase-2 review skill for a live run), author a minimal `evals.json` per skill and confirm 1.0 positive / 0.0 negative; tighten descriptions per `skill-eval-loop/references/improvement-heuristics.md` if under-triggering. Optionally run the full pipeline with the dedicated persona agents once they are registered as dispatchable subagents in a consuming environment, and confirm cross-reviewer promotion on an overlapping seeded finding.

### DF-v24-3 -- Live skill-eval-loop trigger run deferred for the new Phase-4 product-pulse skill

- **Source phase**: Phase 4 - Remaining skill-native (sub-task T019)
- **Plan reference**: `docs/v2.4.0/plans/adoption-compound-engineering-plugin.md` (sub-task 4.3 / T019)
- **Category**: DF -- Deferred (intentionally; environment constraint)
- **Reason**: T019 asks for a live `skill-eval-loop` trigger check for `product-pulse`. No model CLI (`claude`/`codex`/`gemini`/`opencode`) is on PATH in the implementation environment (same constraint as DF-v24-1 / DF-v24-2). A static trigger-surface check was performed instead and recorded: the description carries 7/7 verbatim positive trigger phrases ("product pulse", "usage report", "how is the product doing", "monthly product report", "error trends", "performance over time", "product metrics summary"), an explicit `SKIP` clause fencing dashboards / real-time monitoring / external-analytics routing / one-off greps, and the zero-outbound assertion ("no outbound call and no new data processor"). All six required body sections are present, the frontmatter parses as YAML with all required keys, and the MCP skill-server suite (43 passed) consumes the new entry. The T017 persistence-discipline section was dry-run-verified separately (write -> verify-read -> done-marker -> resume-skips-completed).
- **Suggested next step**: Run the live `skill-eval-loop` for `product-pulse` when a model CLI is available - fold into Phase 8 T037 alongside DF-v24-1 / DF-v24-2. Author a minimal `evals.json` (one should-trigger usage-report prompt, one should-not-trigger dashboard prompt) and confirm 1.0 positive / 0.0 negative; tighten the description per `skill-eval-loop/references/improvement-heuristics.md` if under-triggering.

### DF-v24-4 -- Live skill-eval-loop trigger run deferred for the two new Phase-3 skills

- **Source phase**: Phase 3 - Close the compound loop (sub-task T016)
- **Plan reference**: `docs/v2.4.0/plans/adoption-compound-engineering-plugin.md` (sub-task 3.4 / T016)
- **Category**: DF -- Deferred (intentionally; environment constraint)
- **Reason**: T016 asks for a live `skill-eval-loop` trigger check for `product-strategy` and `session-query`. No model CLI (`claude`/`codex`/`gemini`/`opencode`) is on PATH in the implementation environment (same constraint as DF-v24-1 / DF-v24-2 / DF-v24-3). A static trigger-surface check was performed instead and recorded: `product-strategy` carries verbatim positive trigger phrases ("write a strategy", "what is our product strategy", "define the target problem", "who is this for", "what metrics matter", "set the product direction", "what are our bets", "what tracks are we working on") plus a `SKIP` clause fencing governance MUST/SHOULD (project-constitution), single-idea refinement (idea-refine), known-gaps logging, and single-feature specs; `session-query` carries verbatim positive trigger phrases ("did we look at this before", "what did we try last time", "find the session where we debugged X", "search my past sessions", "pull up prior context on this branch", "have we hit this error before") plus a `SKIP` clause fencing session-history generation, solution capture, known-gaps logging, and any external upload. Both `summary_l0` are <=15 words and both `overview_l1` are <=150 words; the MCP skill-server suite (43 passed) consumes both new entries. The session-query extractor was additionally proven via 13 pytest cases and an empirical PowerShell-parity smoke (topic / time-window / no-match all match the Python digest).
- **Suggested next step**: Run the live `skill-eval-loop` for `product-strategy` and `session-query` when a model CLI is available - fold into Phase 8 T037 alongside DF-v24-1 / DF-v24-2 / DF-v24-3. Author a minimal `evals.json` per skill (one should-trigger, one should-not-trigger prompt) and confirm 1.0 positive / 0.0 negative; tighten the description per `skill-eval-loop/references/improvement-heuristics.md` if under-triggering.

### DF-v24-5 -- Live --branch clone+install path verified only via the dry-run probe

- **Source phase**: Phase 5 - Internal RE builds re-full (sub-task T022)
- **Plan reference**: `docs/v2.4.0/plans/adoption-compound-engineering-plugin.md` (sub-task 5.2 / T021, 5.3 / T022)
- **Category**: DF -- Deferred (intentionally; environment / scope constraint)
- **Reason**: T021 added the `--branch <name>` / `-Branch <name>` installer flag, which shallow-clones a pushed branch into `~/.nexus-hub/branches/<sanitized>/` and re-execs the install from that checkout. T022's acceptance was satisfied via the clone-free dry-run probe (`--branch <name> --check` / `-Branch <name> -Check`): the probe resolves the cache path, neutralizes path-traversal branch names (`../../etc` -> `---etc`), reads the clone source from `git remote.origin.url`, and exits 0 without cloning, on both bash and PowerShell (7 pytest probes in `tests/installer/test_branch_flag.py`). The actual end-to-end path -- shallow clone of a real pushed branch, `NEXUS_HUB_BRANCH_RESOLVED` re-exec into the cached installer, and a full install from the cached checkout -- was not run, because it requires a real pushed branch and a full (non-dry-run) install into a throwaway target, which is heavier than the phase's probe-level acceptance bar.
- **Suggested next step**: Once a test branch is pushed, run `bash scripts/installer.sh --branch <that-branch>` (and the PowerShell `-Branch` equivalent) into a throwaway global/workspace target and confirm: (1) the cache dir is created and populated from the branch, (2) the re-exec runs with `NEXUS_HUB_BRANCH_RESOLVED=1` and does not re-clone, (3) the install completes from the cached checkout, and (4) the user's working copy is untouched. Fold into the Phase-8 cross-OS smoke (T039) or a maintainer pre-release check.

### WN-v24-1 -- AGENTS.md catalog-count prose is stale after the registry reconciliation

- **Source phase**: Phase 1 - Foundation (sub-task T005)
- **Plan reference**: `docs/v2.4.0/plans/adoption-compound-engineering-plugin.md` (sub-task 1.5 / T005)
- **Category**: WN -- Stale documentation count
- **Reason**: The T005 reconciliation revealed the registries had drifted far beyond the planned "1-skill" estimate: 6 conformant on-disk skills were unregistered in `data/skills.json` (`advanced-attack-patterns`, `business-logic-abuse`, `dev-progress-tracker`, `hallmark-design`, `html-output-conventions`, `implementation-plan`), 3 skills carried mis-cased category values, and `data/marketplace.json` omitted the `research` category. All three registries are now reconciled to the on-disk truth: **239 skills across 21 categories**. AGENTS.md prose still reads "230 skills across 23 categories" (the "23" was inflated by the 3 mis-cased duplicate category keys; the true directory count is 21). The Repository Overview line and the embedded SKILL INDEX in AGENTS.md / the platform instruction templates were not updated in Phase 1 (out of scope for T005, which is data-file-only).
- **Suggested next step**: At the v2.4.0 version bump (Phase 9 / `/update-version`), update the AGENTS.md "Current catalog" line and any platform-template count prose, and regenerate the embedded SKILL INDEX from `data/SKILL_INDEX.md`. As of Phase 4 close the on-disk truth is **242 skills across 21 categories** (Phase 2 added `multi-agent-code-review` + `plan-review`; Phase 4 added `product-pulse`) and the agent count is **23** (AGENTS.md prose still reads "230 skills across 23 categories" and "10 agents"; `README.md` line 113 still reads "208 skills"). The `data/SKILL_INDEX.md` Total line was corrected from a stale "239" to the true **242** during the Phase 4 registration (the 239 was a Phase-2 oversight - rows were added without updating the footer). As of Phase 3 close the on-disk truth is **244 skills across 21 categories** (Phase 3 added `product-strategy` + `session-query`, both workflow); all three registries (`data/skills.json` total + per-category, `data/marketplace.json` workflow `skill_count`, `data/SKILL_INDEX.md` rows + Total line) agree at 244 / workflow 35. AGENTS.md prose still reads "230 skills across 23 categories" and `README.md` still reads "208 skills". Roll in the remaining Phase 5 / 6 additions at bump time.

## Resolved

| ID | Title | Category | Resolved in | Detail |
|---|---|---|---|---|
| WN-v23-1 | `data/skills.json` skill entry count drifted from `statistics.total_skills` | WN | v2.4.0 Phase 1 (T005) | Root-caused as a three-way registry-vs-disk drift, not a simple statistic lag. Reconciled all three registries to the on-disk catalog: registered the 6 pre-existing unregistered skills + the 2 new Phase-1 skills (skills.json 231 -> 239), normalized 3 mis-cased category values to their lowercase directory ids, recomputed `statistics.total_skills` / `categories` / `priorities` / aggregate size stats, rebuilt `data/marketplace.json` per-category `skill_count` and added the missing `research` category, and appended the 6 missing `data/SKILL_INDEX.md` rows with a corrected Total line ("239 skills across 21 categories"). All three files now agree at 239; `make validate` passes; `validate_skills.py --allow-existing` is clean (0 errors). The 2 new skills were added to `scripts/validate_skills.allowlist.json` for consistency with the 137 already-grandfathered pushy descriptions. Residual doc-count staleness recorded as WN-v24-1. |
| BG-v23-1 | `scripts/validate_skills.py` reports 7 pre-existing "Generic secret assignment" false positives | BG | v2.4.0 Phase 1 (T006) | Made the secret scanner fenced-code-aware for Markdown: `scan_text_for_secrets` tracks fenced code blocks with CommonMark semantics (an opening fence may carry an info string; a closing fence must be the same char, at least as long, and carry no info string), so nested examples like a Markdown code block that itself shows a nested shell snippet no longer invert the fence state. Inside a Markdown fence the low-confidence "Generic secret assignment" pattern is suppressed (documentation examples), while high-confidence credential patterns (real API-key / token formats) are still flagged everywhere. Result: 0 generic-secret false positives across the catalog (was 7); the unfenced case still fails; high-confidence keys still flagged even inside fences. Covered by 5 new pytest cases in `tests/validators/test_validate_skills.py` (fenced-ignored, unfenced-flagged, high-confidence-in-fence-flagged, non-markdown-flagged, nested-fence-no-state-inversion). |

---

**File lifecycle**: This file is appended by `/implement-phase` Phase 8 step 8.4 (per-phase append), swept by `/wrap-up-session` Phase 4 (catch-all from live conversation), and finalized by `/update-version` at the v2.4.0 -> next-version bump. After finalization, the next plan run by `/generate-plan` will read this file to decide which items carry forward.
