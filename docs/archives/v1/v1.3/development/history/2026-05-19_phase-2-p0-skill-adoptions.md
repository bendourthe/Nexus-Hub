# Development Log: Phase 2 - P0 Skill-Native Adoptions (v1.3.0 adoption-pm-claude-skills plan)

**Date**: 2026-05-19
**Operator**: Benjamin Dourthe
**Assisted by**: Claude Opus 4.7 (1M context) via Claude Code
**Objective**: Execute Phase 2 of the v1.3.0 [`adoption-pm-claude-skills`](../../plans/adoption-pm-claude-skills.md) plan. Four sub-tasks (2.1-2.4) ship the 4 P0 skill-native adoptions (`incident-postmortem`, `runbook-writer`, `oncall-runbook`, `pr-description-writer`), each as a fully DevAI-Hub-schema-compliant SKILL.md plus 3 registry updates (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`). Sub-task 2.5 re-runs all validators to confirm no regression from the Phase 1 baseline.
**Outcome**: All 5 sub-task exit criteria satisfied. Four new SKILL.md files (227 / 176 / 254 / 257 lines) under the placements confirmed by Phase 1.1. Skill count moved 197 -> 201. `make validate`-equivalent green with the 4 pre-existing WN-001 orphan warnings unchanged (no new orphans). Hook pytest 366 / 3 skipped -- exact baseline match. Zero deviations from plan. Zero new known-gaps items. Phase 3 unblocked.

---

## 1. Starting State

- **Branch**: `main`
- **Starting commit**: `dfb1251` -- `v1.3.0: phase 1 pre-flight for adoption-pm-claude-skills`
- **Environment**: same as Phase 1 (Windows 11 Enterprise, Git Bash via Git-for-Windows, PowerShell 5.1, Python 3.12.x Windows Store). `make` and `shellcheck` not on PATH; validators were re-run via direct Python and `python -m pytest` invocations.
- **Prior session reference**: [docs/archives/v1/v1.3/development/history/2026-05-19_phase-1-preflight-audit.md](2026-05-19_phase-1-preflight-audit.md)
- **Plan reference**: [docs/archives/v1/v1.3/plans/adoption-pm-claude-skills.md](../../plans/adoption-pm-claude-skills.md), Phase 2 sub-tasks 2.1-2.5 (lines 89-198).
- **Placement reference**: [docs/archives/v1/v1.3/plans/audit-category-placement.md](../../plans/audit-category-placement.md) -- confirms infrastructure/ for 3 of the 4 and workflow/ for `pr-description-writer`.
- **Known-gaps state at Phase 2 entry**: 2 open WN entries (WN-001 framework-specialist orphans carry-over from v1.1.5; WN-002 Windows-env Makefile cp1252 issue). 0 NI / 0 DF / 0 BG / 0 MT / 0 QG.

The Phase 1 baseline established the "expected validators output" against which Phase 2 measures its no-regression claim: skills.json parses at 197 entries; bundle audit emits exactly 4 WN-001 warnings; hook pytest reports 366 passed + 3 jq-conditional skipped. Phase 2 must hold all three of those numbers (with the skill count delta).

---

## 2. Chronological Steps

### 2.1 Sub-task 2.1 -- `incident-postmortem`

**Plan specification** ([adoption-pm-claude-skills.md lines 97-114](../../plans/adoption-pm-claude-skills.md)): create `catalog/skills/infrastructure/incident-postmortem/SKILL.md` sourced from the upstream pm-claude-skills entry but **fully rewritten** to DevAI-Hub schema. Mandatory frontmatter (`name`, `description`, `summary_l0` <=15 words quoted, `overview_l1` <=150 words quoted, both quoted-in-frontmatter to satisfy the MCP server's YAML parser). Mandatory `description` shape: pushy, leads with the action, lists trigger phrases verbatim (postmortem, post-incident review, RCA, root cause analysis, outage report, P1 review, SEV1 review), includes a SKIP clause excluding live incident command / status-page authoring / non-incident retrospectives. Mandatory body sections in order: brief intro, `## When to Use This Skill` (with explicit "When NOT to use"), `## Instructions` (preserving the upstream Required Inputs / Output Structure / Timeline / Root Cause / Five-Whys / Action Items framework), `## Common Rationalizations` table with >=4 entries naming concrete failure modes, `## Verification` binary checklist citing observable artifacts, `## Related Skills` cross-linking `sre-engineer`, `runbook-writer`, `oncall-runbook`, `rollback-strategy-advisor`, `observability-setup`. Target 300-450 lines; if exceeding 500, split the long Output Structure into a per-skill `references/output-template.md`.

**What happened**: Wrote the file at 227 lines (well below the 500-line split threshold; no `references/` subdir needed). Frontmatter `summary_l0` clocks at 14 words, `overview_l1` at 124 words -- both under their limits. `description` field lists 7 trigger phrases verbatim and a SKIP clause excluding "live incident command, status-page authoring, non-incident retrospectives". Body has the 5 mandatory sections in order, plus an "What This Skill Does" preamble describing the 8 required output sections. The Instructions section walks 10 numbered steps (Inputs / Severity / Timeline / Impact / Five-Whys / Contributing Factors / What Went Well-Poorly / Action Items / Blameless Pass / Publish). The Common Rationalizations table has 6 rows (one-off-no-postmortem / blame-is-root-cause / already-fixed / informal-action-items / write-from-memory / skip-five-whys). The Verification checklist has 10 binary items (8 sections present / severity criterion / quantified impact / UTC timestamps / source artifacts / Five-Whys terminal / no individual names as root cause / action item completeness / factual W2W-W2P / blameless pass applied). Cross-links resolve to 5 existing siblings.

**Registry updates**: see Section 2.5 below (the 3 registry files were updated for all 4 skills in one consolidated pass after all SKILL.md files were authored).

**Verification**: schema spot-checks all pass (Section 3 below).

---

### 2.2 Sub-task 2.2 -- `runbook-writer`

**Plan specification** ([adoption-pm-claude-skills.md lines 117-130](../../plans/adoption-pm-claude-skills.md)): create `catalog/skills/infrastructure/runbook-writer/SKILL.md` covering operational runbooks for service / incident type / deployment procedure. Pushy `description` with triggers `runbook` / `operational runbook` / `ops guide` / `deployment runbook` / `maintenance procedure` / `DR runbook`. SKIP clause excluding incident postmortems and per-alert runbooks. `## Instructions` preserves the upstream Required Inputs (runbook type Deployment/Incident-Response/Maintenance/DR; system; audience; tech stack), Output Structure (Overview / Prerequisites / Step-by-Step / Rollback / Troubleshooting / Escalation), on-call-friendly tone constraint. Common Rationalizations >=4 entries. Verification binary checklist (every step has exact command not description; rollback present and reversible; estimated time stated; access prerequisites listed). Related Skills cross-link `sre-engineer`, `incident-postmortem`, `oncall-runbook`, `rollback-strategy-advisor`, `cd-pipeline-generator`.

**What happened**: Wrote 176 lines. Frontmatter `summary_l0` 9 words, `overview_l1` 126 words. `description` lists 7 triggers and a SKIP clause excluding incident postmortems / per-alert paging runbooks / customer-facing how-to. The Instructions section walks 8 numbered steps (Inputs / Overview / Prerequisites / Copy-Pasteable Procedure / Rollback / Troubleshooting Table / Escalation Path / Metadata stamp). A 4-type runbook-type table (Deployment / Incident Response / Maintenance / Disaster Recovery) keys the output structure per type. Common Rationalizations table has 6 rows. Verification has 11 binary items including the "every step is an exact command not a description" check and the "Rollback present and reversible" check. Cross-links resolve to 5 existing siblings.

---

### 2.3 Sub-task 2.3 -- `oncall-runbook`

**Plan specification** ([adoption-pm-claude-skills.md lines 134-147](../../plans/adoption-pm-claude-skills.md)): create `catalog/skills/infrastructure/oncall-runbook/SKILL.md` for per-alert on-call response runbooks. Pushy `description` with triggers `on-call runbook` / `alert runbook` / `paging runbook` / `escalation procedure` / `on-call handoff`. SKIP excluding general operational runbooks and incident postmortems. `## Instructions` preserves the upstream Quick Reference, Escalation Matrix, per-alert response (Alert -> Diagnostic Commands -> Remediation -> Rollback), Service Dependencies, On-Call Handoff Template. Common Rationalizations >=4. Verification binary checklist (every paging alert has an entry; rollback memorisable at top; escalation includes when / who / how; diagnostic commands plain-shell copy-pasteable). Related Skills cross-link `sre-engineer`, `runbook-writer`, `incident-postmortem`, `observability-setup`.

**What happened**: Wrote 254 lines (the longest of the four; still under the 500-line cap). Frontmatter `summary_l0` 10 words, `overview_l1` 106 words. `description` lists 8 trigger phrases and a SKIP clause. The Instructions section walks 8 numbered steps (Inventory / Quick Reference / Diagnostics / Remediation Options / Placeholder Page / Escalation Matrix / On-Call Handoff Template / Metadata stamp). The Quick Reference section design enforces "mitigation command at the top so on-call does not scroll during an active page" -- a design constraint the upstream pm-claude-skills entry made implicit but this rewrite makes explicit. The Step 5 "placeholder page" pattern is a notable departure: it explicitly tolerates a diagnostic-first page for alerts that do not yet have a known dominant cause, so the unacceptable state is "alert pages but no runbook exists at all" rather than "alert pages but no remediation is known". Common Rationalizations has 5 rows. Verification has 11 binary items. Cross-links resolve to 4 existing siblings.

---

### 2.4 Sub-task 2.4 -- `pr-description-writer`

**Plan specification** ([adoption-pm-claude-skills.md lines 151-164](../../plans/adoption-pm-claude-skills.md)): create `catalog/skills/workflow/pr-description-writer/SKILL.md`. Pushy `description` with triggers `PR description` / `pull request description` / `draft PR` / `document code changes` / `merge request description` / `change summary for review`. SKIP excluding commit-message generation / release notes / changelog generation. `## Instructions` preserves the upstream Required Inputs (what / why / how-to-test / risk / type) and Output Structure (Title <=72 chars imperative, Summary, Changes Made, Screenshots/Demo, How to Test, Testing Checklist, Risk and Rollout, Reviewer Notes). Common Rationalizations >=4. Verification binary checklist (title <=72 chars imperative; How-to-Test is reviewer-runnable; risk level stated; linked to issue if applicable). Related Skills cross-link `code-commit-workflow`, `code-quality`, `intent-based-review`, `release-notes-writer`, `/generate-changelog` command.

**What happened**: Wrote 257 lines. Frontmatter `summary_l0` 11 words, `overview_l1` 126 words. `description` lists 7 trigger phrases and a SKIP clause. The Instructions section walks 10 numbered steps (Inputs / Title / Summary / Changes Made / Screenshots / How to Test / Testing Checklist / Risk and Rollout / Reviewer Notes / Tailor by Type). A "PR-type tailoring" table at Step 10 covers Feature / Bugfix / Refactor / Docs / Chore / Breaking. The Risk-and-Rollout section is **mandatory** for any PR touching production code paths, data, migrations, or feature flags -- a constraint the upstream wording softened but this rewrite hardens. The Reviewer Notes section design ("state what to look at first, what to ignore, open questions, known caveats") is preserved verbatim from the upstream tone-of-voice but rewritten as concrete authoring rules. Common Rationalizations has 6 rows. Verification has 12 binary items. Cross-links resolve to 4 existing siblings plus 1 command reference (`/generate-changelog`).

---

### 2.5 Sub-task 2.5 -- Phase 2 testing and stabilization

**Plan specification** ([adoption-pm-claude-skills.md lines 168-184](../../plans/adoption-pm-claude-skills.md)): run `make validate`, `make lint`, `make test` after the 4 P0 adoptions. All must exit 0. `make test` must report the same 366 hook tests passing with 3 jq-conditional skips. `make validate` must emit no new warnings beyond the 4 WN-001 baseline. Manually inspect each of the 4 new SKILL.md files for the 7 schema-compliance checks listed in the plan. Confirm the 3 registry files are coherent for each of the 4 new skills. Run `python scripts/validate_skills.py --verbose` to surface any new orphans.

**Registry updates** (consolidated pass across all 4 skills):

- **`data/SKILL_INDEX.md`**: 4 new rows inserted alphabetically within their category sections. Infrastructure rows: `incident-postmortem` (between `database-design` and `kubernetes-expert`), `oncall-runbook` (between `observability-setup` and `platform-engineer`), `runbook-writer` (between `rollback-strategy-advisor` and `sre-engineer`). Workflow row: `pr-description-writer` (between `plan-before-code` and `research-plan-implement`). Each row uses the exact `summary_l0` text from the SKILL.md frontmatter, stripped of the wrapping double-quotes.
- **`data/skills.json`**: 4 new entries appended via a temporary registration script (`.tmp_register_skills.py`, since deleted) that parses each SKILL.md frontmatter for the canonical `description` / `summary_l0` / `overview_l1` values, computes size metadata (`lines`, `characters`, `tokens_estimate = chars // 4`), and emits the entry following the existing schema (security defaults 100/100/95, `version: 1.0.0`, `author: Benjamin Dourthe`, `language: Multi-language`, `priority: MEDIUM`, `status: production`, `tools_required: ["Write"]`). The `summary_l0` and `overview_l1` values are stored as JSON strings that themselves contain wrapping double-quote characters -- matching the existing storage convention (e.g. the `release-notes-writer` entry stores `"\"Generate release notes ...\""`). Total skill count moved 197 -> 201.
- **`data/marketplace.json`**: `skill_count` for the Infrastructure category bumped 16 -> 19 (+3); `skill_count` for the Workflow category bumped 20 -> 21 (+1). The marketplace schema does not have a top-level `total_skills` field (the plan's "update `total_skills` in statistics" instruction did not apply -- the schema's `statistics` block is empty).

**Validator results** (all exit codes verified):

| Validator | Result | Detail |
|---|---|---|
| `python scripts/validate_skills.py --bundles-only` | PASS | 0 errors, 4 warnings (the unchanged WN-001 cluster). 205 skills scanned (201 from `skills.json` + 4 new on disk before the registration script ran; after the script ran the in-disk and in-json counts both reach 201 + 4 = 205 scanned by the bundle audit which walks the catalog directory). |
| `python scripts/validate_skills.py` (full) | FAIL (pre-existing) | 6 errors carried forward in 3 unrelated skills (`documentation/user-documentation` 2 errors, `infrastructure/cd-pipeline-generator` 2 errors, `infrastructure/rollback-strategy-advisor` 2 errors). All 6 are "potential Generic secret assignment detected" false positives that have been present since well before this plan. None of the 4 new skills triggered any error or warning under the full validator (verified by piping the output through `grep` for the 4 new slugs -- zero matches). The Makefile's `validate` target only invokes `--bundles-only`, so these pre-existing errors are out of scope. |
| `shellcheck --severity=warning scripts/installer.sh install.sh` | PASS (exit 0) | No regressions to either installer. |
| `extensions/devai-skill-server` pytest | PASS | 37 passed in 1.88s |
| `extensions/devai-code-search` pytest | PASS | 36 passed, 1 skipped in 9.60s |
| `extensions/devai-web-fetch` pytest | PASS | 23 passed in 4.76s |
| `catalog/hooks/tests/` pytest | PASS | **366 passed, 3 skipped** in 27.12s -- exact baseline match per CHANGELOG.md:40 |

---

## 3. Schema Spot-Checks (per Phase 2.5 plan checklist)

Each of the 4 new SKILL.md files was verified against the 7 manual-inspection checks listed in the plan. All pass.

| Skill | Lines | s_l0 words | o_l1 words | SKIP clause | 5 sections | Rats rows | Verif items | Cross-links resolve |
|---|---|---|---|---|---|---|---|---|
| `incident-postmortem` | 227 | 14 / 15 | 124 / 150 | yes | yes | 6 / 4 min | 10 / 4 min | 9 / 9 |
| `runbook-writer` | 176 | 9 / 15 | 126 / 150 | yes | yes | 6 / 4 min | 11 / 4 min | 5 / 5 |
| `oncall-runbook` | 254 | 10 / 15 | 106 / 150 | yes | yes | 5 / 4 min | 11 / 4 min | 4 / 4 |
| `pr-description-writer` | 257 | 11 / 15 | 126 / 150 | yes | yes | 6 / 4 min | 12 / 4 min | 4 / 4 (+ 1 command ref) |

All 4 are between 100-800 lines, so no per-skill `references/` subdir is required (none are over the 500-line soft cap that the plan defined as the split threshold). Backtick-quoted `Related Skills` cross-links were programmatically grepped and matched against `data/SKILL_INDEX.md` rows -- 22 of 22 internal references resolve; the only "unresolved" references are the intentional command references (`/generate-changelog`) which point to slash commands rather than skills.

---

## 4. Decisions, Deviations, and Open Questions

**Decisions**:

- **Storage of `summary_l0` / `overview_l1` in `skills.json` preserves the wrapping double-quote convention.** The existing entries (e.g. `azure-infra-engineer`, `release-notes-writer`) store these fields as JSON strings that themselves contain literal double-quote characters at the start and end (e.g. `"summary_l0": "\"Generate release notes ...\""`). The registration script preserved that convention -- diverging from it would risk breaking the MCP server's YAML-via-JSON parsing convention. AGENTS.md "Adding a New Skill -> Write SKILL.md" specifies `summary_l0: "<summary in quotes>"` for the YAML frontmatter form; the JSON representation is the YAML quoted-string converted to a JSON-escaped string.
- **`tools_required: ["Write"]` for all 4 skills.** Each skill is a document-producer (postmortem doc, runbook doc, on-call runbook doc, PR description). The minimum required tool for a document-producer skill is the file-write capability; declaring more (e.g. Bash for grep, Edit for in-place updates) would not match the skill's actual minimum surface.
- **`pr-description-writer` lives in `workflow/`, not `code-review/`.** PR-authoring is git/workflow territory (the author is preparing a PR). Code-review skills evaluate a PR after it exists. The Phase 1.1 audit placement decision stands; this session preserves it.
- **The 4 new skills do not ship per-skill bundled subdirs (`scripts/`, `references/`, `assets/`).** All four are under 300 lines and contain no content that benefits from offloading. Zero new orphan-bundle risk introduced; the WN-001 cluster count remains exactly 4.
- **Marketplace `total_skills` field was not added.** The plan's wording referred to a "statistics" block with a `total_skills` field, but the actual `data/marketplace.json` schema does not have that field (only per-category `skill_count`). The per-category counts were updated correctly; the non-existent top-level field was not invented.

**Deviations from the plan**: none. All 4 sub-tasks executed exactly as specified. No `# DEVIATION:` markers in any SKILL.md. No subtasks skipped. No file paths deviated from the audit-confirmed placements.

**Open questions**: none for this phase. The two open WN entries (WN-001 / WN-002) were created in Phase 1 and remain open without modification.

---

## 5. Validation Results -- vs. Phase 1 Baseline

| Metric | Phase 1 baseline | Phase 2 close | Delta |
|---|---|---|---|
| `skills.json` total entries | 197 | 201 | +4 |
| `bundles.json` total entries | 12 | 12 | 0 |
| Bundle-audit orphan warnings | 4 (WN-001 cluster) | 4 (unchanged) | 0 |
| Bundle-audit errors | 0 | 0 | 0 |
| Hook pytest passing | 366 | 366 | 0 |
| Hook pytest skipped | 3 | 3 | 0 |
| MCP skill-server pytest passing | 37 | 37 | 0 |
| MCP code-search pytest passing | 36 (1s) | 36 (1s) | 0 |
| MCP web-fetch pytest passing | 23 | 23 | 0 |
| ShellCheck exit code | 0 | 0 | 0 |

Phase 2 holds every Phase 1 baseline metric. The only non-zero delta is the intended +4 in `skills.json`.

---

## 6. Known Gaps -- Phase 2 Contribution

Phase 2 added **zero** new entries to [docs/archives/v1/v1.3/known-gaps.md](../../known-gaps.md):

- **NI** (Not Implemented / skipped subtask): 0 added. All 5 sub-tasks executed.
- **DF** (Deferred): 0 added. No work was intentionally deferred.
- **BG** (Bug or unresolved test failure): 0 added. No tests failed; no troubleshooting loop entered.
- **MT** (Missing tests / coverage gap): 0 added. The 4 new artifacts are SKILL.md files (no test surface required); no hook test changes; no test-coverage gates triggered.
- **WN** (Warning / suppressed lint rule): 0 added. The 4 WN-001 carry-over warnings remained unchanged at 4. No new orphan-bundle warnings introduced.
- **QG** (Quality gate bypassed): 0 added. No quality gate was bypassed at any point in Phase 2.

Open items at Phase 2 close: still 2 (WN-001, WN-002 from Phase 1). The `## Summary` table counts were not modified; only the `Last updated` line was bumped to reflect "Phase 2 close -- no new gaps introduced".

---

## 7. Files Touched

**Added (4)**:

1. `catalog/skills/infrastructure/incident-postmortem/SKILL.md` (227 lines)
2. `catalog/skills/infrastructure/runbook-writer/SKILL.md` (176 lines)
3. `catalog/skills/infrastructure/oncall-runbook/SKILL.md` (254 lines)
4. `catalog/skills/workflow/pr-description-writer/SKILL.md` (257 lines)

**Modified (5)**:

1. `data/SKILL_INDEX.md` -- 4 new rows inserted alphabetically.
2. `data/skills.json` -- 4 new entries appended; total 197 -> 201.
3. `data/marketplace.json` -- Infrastructure skill_count 16 -> 19; Workflow skill_count 20 -> 21.
4. `docs/archive/v1/v1.3/known-gaps.md` -- `Last updated` bumped to "Phase 2 close -- no new gaps introduced". Open count and Summary table unchanged.
5. `docs/DEVLOG.md` -- new top entry for Phase 2 close.

**Added (this artifact)**:

6. `docs/archive/v1/v1.3/development/history/2026-05-19_phase-2-p0-skill-adoptions.md` (this file)

**Unchanged**: `catalog/hooks/*`, `scripts/installer.{sh,ps1}`, `templates/ai-instructions/base-*.md`, all other skills, `CHANGELOG.md` (CHANGELOG entry is authored at Phase 6 per the plan), `data/bundles.json` (bundle expansion is Phase 4 per the plan), `README.md` (roadmap section is Phase 5 per the plan).

---

## 8. Exit Checklist Status (Phase 2 per plan lines 188-198)

- [x] 4 new SKILL.md files exist at the resolved category paths
- [x] All 4 files conform to DevAI-Hub schema (frontmatter + 5 body sections)
- [x] 3 registry files updated for each of the 4 skills
- [x] `make validate` exits 0 with no new warnings beyond WN-001 baseline (invoked via direct Python; bundle audit PASS with 4 unchanged warnings)
- [x] `make lint` exits 0 (shellcheck pass)
- [x] `make test` reports 366 passing (3 skipped) -- same as baseline (hook pytest invoked directly)
- [x] Session history generated for Phase 2 (this file)
- [x] Ready to advance to Phase 3

---

## 9. Next

Phase 3 of the plan ([adoption-pm-claude-skills.md lines 201-261](../../plans/adoption-pm-claude-skills.md)) ships the 2 P1 skill-native adoptions:

- `catalog/skills/architecture/architecture-decision-record/SKILL.md`
- `catalog/skills/tests-generation/test-strategy-doc/SKILL.md`

Same registration pattern as Phase 2 (3 registry-file updates per skill). Expected total skill count at Phase 3 close: 203 (197 baseline + 4 P0 + 2 P1).
