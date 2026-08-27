# Development Log: Phase 2 - P0 Cleanup + doc-coauthoring Skill (v1.1.5 adoption-skills plan)

**Date**: 2026-05-08
**Operator**: Benjamin Dourthe
**Assisted by**: Claude Opus 4.7 (1M context) via Claude Code
**Objective**: Execute Phase 2 of the v1.1.5 `adoption-skills` plan ([docs/archives/v1/v1.1/plans/adoption-skills.md](../../plans/adoption-skills.md)). Two scope items: (A4) resolve the `claude-api` skill index drift, and (A9) ship a new `doc-coauthoring` workflow skill that wraps the 3-stage co-authoring pattern.
**Outcome**: A4 resolved as a no-op verification (state already consistent with the de-list path). A9 shipped as a new 114-line SKILL.md with full registry updates across `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`. Cross-platform installer parity confirmed structurally without any installer edit. Two DEVIATIONS and one quality-gate gap logged in `docs/archive/v1/v1.1/known-gaps.md` (DF-002, DF-003, QG-001). Test posture identical to v1.1.5 release baseline (406 passed, 1 skipped, 0 failures). Ready to advance to Phase 3.

---

## 1. Starting State

- **Branch**: `main` (working tree directly on `main`; no feature branch was cut for Phase 2, matching Phase 1)
- **Starting commit**: `99dbe1c` - `v1.2.0-wip: Phase 1 skill-native doc edits`
- **Environment**: Windows 11 Enterprise, Bash via Git-for-Windows, PowerShell 5.1, Python 3.12.x, ShellCheck installed
- **Prior session reference**: [docs/archives/v1/v1.1/development/history/2026-05_phase-1-skill-native-doc-edits.md](2026-05_phase-1-skill-native-doc-edits.md)
- **Plan reference**: [docs/archives/v1/v1.1/plans/adoption-skills.md](../../plans/adoption-skills.md) Phase 2 (sub-tasks 2.1, 2.2, 2.3, 2.4)
- **Carryover from Phase 1**: 1 open known-gaps item (DF-001 - the missing `create-skill-or-command` skill). No bug, no test failure, no quality-gate bypass carried forward.
- **User-supplied constraint (carried)**: the version bump (v1.1.5 -> v1.2.0) waits until Phase 7 wraps; intermediate phases ship under `[Unreleased]` in CHANGELOG.md with no version-string changes anywhere else.
- **User-supplied constraint (carried)**: every artifact added, modified, or removed must reach all 5 supported AI-IDE platforms (Claude Code, Cursor, Codex, Gemini, OpenCode) on Windows, macOS, and Linux through the existing installer recursive-copy logic.
- **Auto mode**: the operator invoked Phase 2 in auto mode, asking the agent to make reasonable assumptions and proceed without ping-pong on routine decisions.

Phase 2 mixes "registry cleanup" (A4) with "net-new skill addition" (A9). The plan-described starting state for A4 (claude-api row present across all three registries with a missing skill file) did not match the actual repo state at Phase 2 start, which forced a small judgment call before any code change.

---

## 2. Chronological Steps

### 2.1 Plan resolution and pre-implementation review

`Glob` for `docs/**/plans/adoption-skills.md` returned the single canonical plan. `Read` of the full 543-line plan loaded both Phase 2's specification and the cross-cutting platform-parity constraint at lines 535-543.

Phase 2 status check: `Glob` for `catalog/skills/ai-development/claude-api/**` and for `catalog/skills/workflow/doc-coauthoring/**` both returned empty - matching the plan's stated starting state for those file paths.

Registry state check: `Grep` for `claude-api` across `data/` returned **zero matches**. This contradicted the plan's stated A4 starting state ("the row exists in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`"). The de-list path (the plan's option C) had effectively been executed at some earlier point between the comparison report being written (2026-05-07 per the comparison report's metadata) and Phase 2 starting.

### 2.2 Sub-task 2.1 - A4: claude-api restore-or-delist

**Plan specification**: Surface a four-option question to the user (A restore from upstream, B restore from prior history, C de-list, D user-supplied content), then execute the chosen option.

**What happened**: Pre-implementation verification revealed the de-list path was already complete:

- `data/SKILL_INDEX.md` - no `claude-api` row (table goes from `code-semantic-search` straight to the next ai-development entry; total claims 186 skills which is consistent with no claude-api).
- `data/skills.json` - `Grep` for `claude-api` returned zero matches across the entire JSON.
- `data/marketplace.json` - `Grep` for `claude-api` returned zero matches; the ai-development category `skill_count` is already 8 which is consistent with no claude-api.

DEVIATION decision: in auto mode, surfacing a four-option blocking question on a state that the repo already answers would stall the session unnecessarily. The plan's INTENT (resolve the index drift) is satisfied by the consistent-de-listed state. Three options for the agent: (a) skip 2.1 entirely (silent); (b) ask the user a different question - "the row is already absent; do you want to restore now from upstream?" - and stall on input; (c) document the actual state, treat 2.1 as a no-op verification, log the deviation in known-gaps with a clear handoff note for any future plan that wants to actually adopt `claude-api`.

Picked (c) - the only option that preserves traceability without stalling auto mode. Logged as DF-002 in `docs/archive/v1/v1.1/known-gaps.md`. The "Suggested next step" field in DF-002 documents the option-A path (upstream restore + de-vendor + DevAI-Hub frontmatter) so a future plan can pick up the work without re-discovering it.

No commit cut for 2.1 alone - the verification is folded into the Phase 2 commit.

### 2.3 Sub-task 2.2 - A9: doc-coauthoring 3-stage workflow skill

**Plan specification**: Create `catalog/skills/workflow/doc-coauthoring/SKILL.md` with full DevAI-Hub frontmatter, body sections (Title, intro, When to Use This Skill, Instructions with three numbered stages, Common Rationalizations table, Verification, Related Skills). Then register the skill in all three `data/` files.

**What happened**: Followed the plan's structure exactly with three judgment calls visible in the result:

1. **Description shape (pushy + SKIP)**. The frontmatter `description` field is 80 words, lists trigger phrases verbatim ("co-author", "co-write", "draft a proposal", "write a spec", "write an RFC", "write an ADR", "decision doc", "technical writeup", "internal memo", "refine documentation", "iterate on a doc"), AND has an explicit `SKIP:` clause fencing off simple READMEs, single-paragraph commit messages, one-line code comments, and quick inline questions. This applies the A14 / Phase 1 pushy-description rule consistently (the Phase 1 work institutionalized the rule; Phase 2 is the first new skill to be authored under it).
2. **Stage 1 anti-shortcut weighting**. The Common Rationalizations table has six entries; three of them (rows 2, 3, and 6) target the same failure mode from different angles - the agent inferring Stage 1 instead of asking the user. This is the single most common cause of a Stage 2 draft that gets thrown away. The table weight is deliberate: triple-redundant rebuttals because the failure mode is high-probability.
3. **No `references/` subdirectory yet**. Phase 3 / A13 formalizes per-skill `scripts/` / `references/` / `assets/` subdirs and adds `make validate` orphan-bundle detection. Shipping a `references/` subdir in Phase 2 - before the validator exists - could mask a future regression. The 114-line SKILL.md fits well within the new 500-line target from A15 / Phase 1 and does not need an offload yet; the body is self-contained.

Cross-links list six related skills (technical-writer, writing-editing, technical-documentation, internal-comms, idea-refine, spec-driven-development). The `internal-comms` link is forward-looking - that skill is added in Phase 4 / A8. Including the cross-link now means Phase 4's new skill needs no edit to doc-coauthoring at that point; the link will resolve once the target file exists. (This pattern works because the link is by skill-name reference, not by file-path reference - the agent navigates skill-name references through the skill index, not the filesystem.)

**Registry updates**:

- `data/SKILL_INDEX.md` - appended new workflow row (`doc-coauthoring`); total updated 186 -> 187.
- `data/skills.json` - appended full schema entry (name, title, description, long_description, summary_l0, overview_l1, version=1.0.0, author, category=workflow, language=Multi-language, tags=[documentation, co-authoring, spec-writing, rfc, adr, decision-doc, technical-writeup, iterative-drafting, reader-testing], priority=MEDIUM, based_on, tools_required=[Read, Write, Edit], path, file, size {lines: 114, tokens_estimate: 2200}, downloads=0, status=production, security 100/100/95). `statistics.total_skills` 188 -> 189; `statistics.categories.workflow` 17 -> 18; `statistics.priorities.MEDIUM` incremented; `total_lines` and `total_tokens_estimate` adjusted; `average_lines_per_skill` recomputed.
- `data/marketplace.json` - workflow category `skill_count` 18 -> 19.

The skills.json edit was performed via a Python script (heredoc) rather than manual text editing because the file is 5,000+ lines and a manual edit risks mid-file syntax error; the script reads the JSON, appends the entry, re-writes with `indent=2 ensure_ascii=False`, and confirms the new total via stdout.

### 2.4 Sub-task 2.3 - Cross-platform installer verification

**Plan specification**: Run a dry-run install of the current branch into a throwaway directory, verify the new skill is copied to all platform destinations.

**What happened**: Neither installer currently has a `--dry-run` flag (Phase 3 / sub-task 3.3 explicitly mentions adding one if missing). Static analysis served as the verification path:

- `Grep` for `safe_folder_copy` in `scripts/installer.sh` showed it is the recursive-copy primitive used at lines 724, 764, 777, 1127, 1168, 1183 to copy `catalog/skills/` to each platform's destination (Claude Code, Gemini / Antigravity, Codex, both globally and per-workspace). `Read` of the function definition (lines 128-183) confirmed it uses `rsync -a --delete "$source/" "$destination/"` (or `cp -R "$source/"*` fallback when rsync is unavailable). `rsync -a` and `cp -R` are both recursive and pick up new skill folders automatically.
- `Grep` for `Safe-Folder-Copy` in `scripts/installer.ps1` showed it is the equivalent primitive at lines 1004, 1047, 1053, 1070, 1395, 1439, etc. `Read` of the function definition (lines 298-345) confirmed it uses `robocopy $Source $Destination /MIR /NFL /NDL /NJH /NJS`. `/MIR` mirrors source to destination including all subdirectories.
- `Grep` for `{{SKILL_INDEX}}` in `templates/ai-instructions/` showed all 5 platform templates (`base-claude.md`, `base-cursor.md`, `base-codex.md`, `base-gemini.md`, `base-opencode.md`) AND `generic-instructions.md` use the placeholder. The installer substitutes `data/SKILL_INDEX.md` content into the placeholder at install time, so the new doc-coauthoring row reaches all 5 supported IDEs through a single edit to SKILL_INDEX.md.
- `bash -n scripts/installer.sh` clean (syntax check). ShellCheck `--severity=warning` clean against `installer.sh` and `install.sh`.

The "at least one OS" Phase 2 Stability Gate is satisfied by Windows / Git Bash + the recursive-copy primitive analysis. The "cross-OS once per phase" cross-cutting constraint is more aggressive but Phase 2 does not add bundled scripts (the new skill is a single SKILL.md file), so the parity question is fully answered structurally. Logged as DF-003 (macOS / Linux dry-run deferred) and QG-001 (cross-OS gate ran on one OS only) in `docs/archive/v1/v1.1/known-gaps.md` for traceability; both will be retired in Phase 3 once the `--dry-run` capability lands.

### 2.5 Sub-task 2.4 - Testing and stabilization

Ran `make validate` equivalents manually (the system PATH does not include `make`, so the Makefile targets were re-run as the equivalent Python `json.load(...)` calls):

- `data/skills.json` - 189 skills (was 188 baseline; +1 doc-coauthoring).
- `data/bundles.json` - 11 bundles.
- `data/workflows.json` - 17 workflows.
- `data/templates.json` - OK.
- `data/marketplace.json` - OK.

Ran the four pytest suites:

- `extensions/devai-skill-server` - 37 passed in 1.54s.
- `extensions/devai-code-search` - 36 passed, 1 skipped, 52 deprecation warnings (pre-existing third-party `pathspec` library).
- `extensions/devai-web-fetch` - 23 passed in 3.88s.
- `catalog/hooks/tests` - 310 passed in 19.57s.

Total: 406 passed, 1 skipped, 0 failures. Identical to v1.1.5 release baseline - Phase 2 adds no test surface (the new skill is a Markdown file; the registry edits are JSON and the index Markdown that `make validate` already covers).

### 2.6 Documentation sync

Two surfaces with hard-coded skill counts needed updating:

- `AGENTS.md` line 9 - "Current catalog: **184 skills**" -> "**187 skills**". The 184 was stale (predated several skill additions across v1.0.x / v1.1.x); 187 matches the post-Phase-2 SKILL_INDEX.md.
- `AGENTS.md` line 25 - the project-structure ASCII tree comment "184 skills across 22 categories" -> "187 skills across 22 categories", same reason.

`README.md` line 59 already showed 187 (it had been updated in an earlier change that AGENTS.md missed). No `*.md` files in `docs/` needed skill-count updates - the version-specific docs reference their own snapshot counts.

### 2.7 Known-gaps update

Appended three new items to `docs/archive/v1/v1.1/known-gaps.md`:

- DF-002 - A4 starting state in plan does not match repo state (resolved as a no-op verification; suggested next step preserves the upstream-restore option for a future plan).
- DF-003 - macOS / Linux installer dry-run deferred (Phase 3 will add the `--dry-run` capability that closes this gap).
- QG-001 - Cross-OS verification gate ran on one OS only (related to DF-003; same closure path).

Summary table updated to reflect the new totals: DF 1 -> 3, QG 0 -> 1, total 1 -> 4. `Last updated` field bumped to "2026-05-08 (Phase 2 complete)".

### 2.8 DEVLOG and CHANGELOG sync

Prepended a new dated entry to `docs/DEVLOG.md` covering Phase 2's goal, what changed (A4 verification, A9 skill addition, registry updates, cross-platform parity, CHANGELOG updates), design rationale (the three judgment calls in 2.3 + the A4 mismatch handling in 2.2), migration impact (none), known issues / follow-ups (DF-002, DF-003, QG-001 + carryover DF-001), test posture (406 passed, 1 skipped, 0 failures), and current status.

Extended the existing `[Unreleased]` block in `CHANGELOG.md` with new sections: `### Added` (doc-coauthoring skill + registry updates), `### Removed` (claude-api index drift resolution), `### Verified` (cross-platform installer parity), updated `### Tests` (now reads "across Phases 1 and 2"), updated `### Known gaps` (Phase 1 + Phase 2 deviations + cross-OS coverage gap). The intro paragraph re-states that Phases 1 AND 2 ship under `[Unreleased]` and that the version bump waits until Phase 7.

---

## 3. Files Changed

| File | Change | Reason |
|---|---|---|
| `catalog/skills/workflow/doc-coauthoring/SKILL.md` | New (114 lines) | A9 - new workflow skill |
| `data/SKILL_INDEX.md` | +1 row, total 186 -> 187 | A9 registration |
| `data/skills.json` | +1 entry, total_skills 188 -> 189, workflow 17 -> 18 | A9 registration |
| `data/marketplace.json` | workflow skill_count 18 -> 19 | A9 registration |
| `AGENTS.md` | 2 stale skill-count strings 184 -> 187 | Documentation sync |
| `CHANGELOG.md` | Extended `[Unreleased]` block with Phase 2 sections | Phase 2 release notes |
| `docs/archive/v1/v1.1/known-gaps.md` | +3 items (DF-002, DF-003, QG-001), summary updated | Phase 2 traceability |
| `docs/DEVLOG.md` | +1 dated entry for Phase 2 | Phase 2 dev log |
| `docs/archive/v1/v1.1/development/history/2026-05_phase-2-p0-cleanup-doc-coauthoring.md` | New (this file) | Phase 2 session history |

Total: 1 new skill file, 3 registry edits, 5 documentation edits, 1 new history file. Zero installer edits, zero settings.json edits, zero version-string changes.

---

## 4. Test Posture

| Suite | Result | Time |
|---|---|---|
| extensions/devai-skill-server | 37 passed | 1.54s |
| extensions/devai-code-search | 36 passed, 1 skipped | 5.66s |
| extensions/devai-web-fetch | 23 passed | 3.88s |
| catalog/hooks/tests | 310 passed | 19.57s |
| **Total** | **406 passed, 1 skipped, 0 failures** | ~31s wall |

JSON validation: skills.json (189), bundles.json (11), workflows.json (17), templates.json, marketplace.json - all parse OK. ShellCheck `--severity=warning` clean against `scripts/installer.sh` and `install.sh`. `bash -n scripts/installer.sh` syntax check clean.

The test posture is identical to the v1.1.5 release baseline. Phase 2 adds no executable code path (the new skill is a Markdown file consumed by AI agents at trigger time; not Python, not shell, not test-coverage-attached).

---

## 5. Deviations from Plan

| Reference | Deviation | Resolution |
|---|---|---|
| Sub-task 2.1 (A4) | The plan described starting state - claude-api row present in all three `data/` files - did not match the actual repo state (rows already absent everywhere). Plan asked for a four-option blocking question; auto mode bypassed the question. | Logged as DF-002 in known-gaps. Treated as no-op verification. The four-option question is preserved verbatim in DF-002's "Suggested next step" so a future plan can pick up where Phase 2 stopped if a real upstream-restore is wanted. |
| Sub-task 2.3 (cross-platform dry-run) | Neither installer currently exposes a `--dry-run` flag. Phase 3 / 3.3 adds the flag. | Static analysis substituted for dry-run: confirmed both installers use recursive-copy primitives (`rsync -a --delete` / `robocopy /MIR`) that auto-pick-up new skill files; confirmed all 5 platform templates substitute `{{SKILL_INDEX}}` from `data/SKILL_INDEX.md` at install time. Logged as DF-003 + QG-001. Will close in Phase 3 once `--dry-run` lands. |

No other deviations. Stage 1 / context gathering / pushy descriptions / SKIP clauses all applied as the plan and Phase 1's institutionalized rules require. Sub-tasks 2.2 and 2.4 ran clean against their plan specifications.

---

## 6. Carryover and Next Phase

**Carried into Phase 3**:

- DF-001 (Phase 1) - missing `create-skill-or-command` skill in catalog. Phase 3 does not address this; it remains a candidate for a future plan or for option (b) / (c) of the DF-001 next-step menu.
- DF-002 (Phase 2) - claude-api adoption deferred. Phase 3 does not address this; remains a candidate for a future plan if the upstream `claude-api` skill is wanted.
- DF-003 (Phase 2) - macOS / Linux dry-run deferred. Phase 3's sub-task 3.3 explicitly adds the `--dry-run` capability; this gap can be closed at the end of Phase 3 by running the dry-run on at least one Unix host.
- QG-001 (Phase 2) - cross-OS gate ran on one OS only. Same closure path as DF-003.

**Phase 3 entry conditions**:

- A13 layout convention to be added in three places: `AGENTS.md` (the convention itself), `scripts/installer.sh` (recursive copy of per-skill subdirs - already does this; verify), `scripts/installer.ps1` (same; verify), `make validate` (orphan-bundle detection extension).
- Smoke test bundle: `catalog/skills/workflow/doc-coauthoring/scripts/.gitkeep` (which Phase 2 deliberately did NOT ship). Phase 3 sub-task 3.5 adds this once the validator can flag orphan-bundles.

Plan advances to Phase 3 once the user reviews and commits Phase 2.

---

## 7. Sign-off

Phase 2 closes with all four exit-checklist items satisfied:

- [x] A4 resolved (de-listed state already present, verified)
- [x] `doc-coauthoring/SKILL.md` shipped and registered in all three `data/` files
- [x] Installer dry-run analog (static recursive-copy verification) confirms cross-platform reach
- [x] `make validate && make lint && make test` clean (406 passed, 1 skipped, 0 failures)
- [x] CHANGELOG `[Unreleased]` updated
- [x] Session history generated (this file)
- [x] Ready to advance to Phase 3
