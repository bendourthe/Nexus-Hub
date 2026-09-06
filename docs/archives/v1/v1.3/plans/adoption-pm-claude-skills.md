# Plan -- Adoption of pm-claude-skills (engineering subset + marketing patterns)

**Project**: DevAI-Hub
**Version**: v1.3.0 (plan lives under v1.3.0; resulting work targets v1.4.0)
**Slug**: adoption-pm-claude-skills
**Plan Type**: Feature / Enhancement (additive adoptions; no refactor of existing skills)
**Created**: 2026-05-19
**Goal**: Ship 6 new document-template engineering skills and 1 bundle-expansion + 2 marketing patterns sourced from `pm-claude-skills` v10.0.0, while explicitly dropping the 5 disallowed adoptions in the out-of-scope appendix.

## Overview

This plan implements the adoption set produced by `/compare-project` against `mohitagw15856/pm-claude-skills`, recorded in [docs/archives/v1/v1.3/comparison-pm-claude-skills.md](../comparison-pm-claude-skills.md). The source comparison report scored 9 in-scope items across four reverse-engineering buckets (8 `skill-native`, 1 `re-full`, 0 `re-partial`, 0 `vendor-intrinsic`) and 5 `drop-outright` items that go to the out-of-scope appendix.

**Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first).** See Section 9.4 of the source comparison for the ordering rationale. Phases 2 and 3 ship the 6 skill-native engineering doc-template skills first because they close capability gaps with zero code and zero outbound calls. Phase 4 then performs the single `re-full` adoption (expanding `data/bundles.json` with engineering-themed bundles), which depends on Phases 2 and 3 skills existing. Phase 5 captures the two `skill-native` marketing patterns. Phase 1 is a defensive pre-flight; Phase 6 is the validation / changelog / wrap-up gate.

The cumulative work delivered by this plan: **6 new SKILL.md files** under `catalog/skills/infrastructure/`, `catalog/skills/workflow/`, `catalog/skills/architecture/`, and `catalog/skills/tests-generation/`, **all rewritten to DevAI-Hub schema** (mandatory `summary_l0`, `overview_l1`, Common Rationalizations, Verification, Related Skills sections, pushy descriptions with SKIP clauses); **3 registry updates** per skill (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`); **bundle expansion** in `data/bundles.json`; **README roadmap section**; **DEVLOG narrative entry**; **CHANGELOG `[1.4.0]` entry**; and an **out-of-scope appendix** in the plan itself listing N1-N5 drops with policy-grounded rejection reasons.

This plan does NOT ingest prior-version known-gaps. The v1.1.5 `known-gaps.md` is `finalized` and v1.2.x is the immediately prior version (no `docs/v1.2.x/known-gaps.md` exists), so per Step 0.6b the file is skipped. Note also that the 11 open items in v1.1.5 known-gaps are dominated by the cumulative cross-OS installer smoke-run cluster (DF-003/005/006/007/008/QG-001), which does not extend to this adoption because every artifact shipped here is a pure SKILL.md file -- no new repo-level scripts, no new bundled subdir scaffolders, no installer-aware copy lines.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Pre-flight: schema and naming audit | Category placements confirmed; slug uniqueness verified; baseline `make validate` / `make lint` / `make test` all green |
| 2 | P0 skill-native adoptions (4 skills) | `incident-postmortem`, `runbook-writer`, `oncall-runbook`, `pr-description-writer` landed, registered, validated |
| 3 | P1 skill-native adoptions (2 skills) | `architecture-decision-record`, `test-strategy-doc` landed, registered, validated |
| 4 | re-full: engineering bundle expansion | `data/bundles.json` gains 2-3 engineering-themed bundles grouping new + existing skills |
| 5 | Marketing pattern adoption | README "Roadmap" section added; DEVLOG narrative-style entry written for this adoption |
| 6 | Final validation, CHANGELOG, version bump | Full validators green; CHANGELOG `[1.4.0]` block authored; `/wrap-up-session` ready |

---

## Phase 1: Pre-flight -- Schema and Naming Audit

**Goal**: Lock in category placement and slug uniqueness for all 6 new skills, and confirm baseline DevAI-Hub validators are green before adding any new content.
**Prerequisites**: None.
**Stability Gate**: `make validate`, `make lint`, and `make test` all pass on the current `main` with zero new warnings vs. the v1.3.0 baseline.

### Sub-tasks

#### 1.1 -- Confirm category placements for all 6 new skills

**Objective**: Pick the final `catalog/skills/<category>/<slug>/` location for each adoption candidate and record the decision in a short audit note.

**Prompt**:
> Read [docs/archives/v1/v1.3/comparison-pm-claude-skills.md](../comparison-pm-claude-skills.md) Section 11 (Adoption Plan). For each of the 6 skill-native adoption candidates -- `incident-postmortem`, `runbook-writer`, `oncall-runbook`, `pr-description-writer`, `architecture-decision-record`, `test-strategy-doc` -- the comparison report proposes a target category. Verify each proposal against the existing 22 catalog categories listed in [AGENTS.md](../../../AGENTS.md) "Adding a New Skill -> Choose the right category". Confirm or override as follows:
>
> | Skill | Proposed | Verify against |
> |---|---|---|
> | incident-postmortem | infrastructure | catalog/skills/infrastructure/ siblings (sre-engineer, rollback-strategy-advisor, observability-setup) |
> | runbook-writer | infrastructure | same |
> | oncall-runbook | infrastructure | same |
> | pr-description-writer | workflow | catalog/skills/workflow/ siblings (code-commit-workflow, debug-with-logs) |
> | architecture-decision-record | architecture | catalog/skills/architecture/ siblings (architecture-design, api-design) -- ADR is architecture-recording so this fits |
> | test-strategy-doc | tests-generation | catalog/skills/tests-generation/ siblings (test-cases, test-structure, code-coverage, testing-review) |
>
> For each row, Grep the proposed category directory for the slug to confirm no collision. If any collision is found, propose a `-doc` or `-template` suffix and document the rename. Output a short markdown table with columns: `Skill | Final category | Final slug | Collision check` and append it to this plan file as an inline comment block (or a small note file at `docs/archive/v1/v1.3/plans/audit-category-placement.md`). Do NOT create any SKILL.md files yet -- this sub-task only resolves placement decisions.

---

#### 1.2 -- Baseline validators must be green

**Objective**: Confirm that `make validate`, `make lint`, and `make test` all pass on the current `main` so that subsequent phases can assert "no new warnings vs. baseline".

**Prompt**:
> Run the three baseline validators and capture the output. From the repo root, run sequentially:
>
> ```
> make validate
> make lint
> make test
> ```
>
> Each must exit 0. Record the test count for `make test` (expected: 366 hook tests with 3 jq-conditional skips, per v1.3.0 CHANGELOG line 38). If `make validate` emits the 4 pre-existing per-skill bundled-resources orphan warnings (the WN-001 cluster from v1.1.5 known-gaps), record them as baseline -- they will be tolerated as carry-over and NOT regressed by this plan. If any validator fails or any new warning appears that is not already documented in v1.1.5 known-gaps WN-001, halt and report the regression before continuing to Phase 2.

---

### Phase 1 Exit Checklist

- [ ] Category placement table for all 6 skills produced and recorded
- [ ] No slug collisions
- [ ] `make validate` exits 0 (with the 4 known WN-001 orphan warnings tolerated)
- [ ] `make lint` exits 0
- [ ] `make test` exits 0 with the expected 366 / 3-skip baseline
- [ ] Ready to advance to Phase 2

---

## Phase 2: P0 Skill-Native Adoptions

**Goal**: Ship the 4 P0 engineering document-template skills as new DevAI-Hub catalog entries, fully rewritten to DevAI-Hub schema.
**Prerequisites**: Phase 1 complete.
**Stability Gate**: All 4 new skills exist with full DevAI-Hub schema; `make validate` passes; the 3 registry files have been updated; no new orphan warnings; no regression of the 366 hook tests.

### Sub-tasks

#### 2.1 -- Adopt `incident-postmortem`

**Objective**: Create a new DevAI-Hub skill at `catalog/skills/infrastructure/incident-postmortem/SKILL.md` whose body is sourced from pm-claude-skills' `skills/incident-postmortem/SKILL.md` but fully rewritten to DevAI-Hub schema.

**Prompt**:
> Create a new skill at `catalog/skills/infrastructure/incident-postmortem/SKILL.md` that produces a complete, blameless incident postmortem document. Source the body content from pm-claude-skills' upstream skill (the content is summarized in [docs/archives/v1/v1.3/comparison-pm-claude-skills.md](../comparison-pm-claude-skills.md) and can be re-fetched from `https://github.com/mohitagw15856/pm-claude-skills/blob/main/skills/incident-postmortem/SKILL.md` if needed). Rewrite the skill to full DevAI-Hub schema per [AGENTS.md](../../../AGENTS.md) "Adding a New Skill -> Write SKILL.md". The file MUST include:
>
> 1. Frontmatter with `name`, `description`, `summary_l0` (<=15 words, quoted), `overview_l1` (<=150 words, quoted). The `description` MUST be pushy per AGENTS.md guidance: lead with the action, list trigger phrases verbatim (`postmortem`, `post-incident review`, `RCA`, `root cause analysis`, `outage report`, `P1 review`, `SEV1 review`), and include a SKIP clause excluding live incident command, status-page authoring, and non-incident retrospectives.
> 2. Body sections in order: brief intro paragraph, `## When to Use This Skill` (with explicit "When NOT to use"), `## Instructions` (numbered steps -- preserve the upstream's Required Inputs / Output Structure / Timeline / Root Cause / Five-Whys / Action Items framework), `## Common Rationalizations` table with at least 4 entries naming concrete failure modes (e.g. "It was a one-off so no postmortem is needed", "The on-call engineer just messed up so blame is the root cause", "We already fixed it, so writing it up wastes time", "Action items can stay informal"), `## Verification` binary checklist citing observable artifacts (e.g. "[ ] The output document contains all 8 required sections", "[ ] No individual name appears as a root cause; only systems and processes", "[ ] Every action item has an owner and a due date"), `## Related Skills` cross-linking `sre-engineer`, `runbook-writer` (Phase 2.2), `oncall-runbook` (Phase 2.3), `rollback-strategy-advisor`, `observability-setup`.
> 3. Target body length: ~300-450 lines. If you would exceed 500 lines, split the long Output Structure section into a per-skill `references/output-template.md` and reference it from the body (Tier-3 pattern). Do NOT inline external-project naming (no "this is from pm-claude-skills"); use generic descriptive language per the AGENTS.md "Reverse-Engineering Attribution Rule".
>
> After creating the file, update the 3 registry files:
> - `data/SKILL_INDEX.md`: add a row in the infrastructure section.
> - `data/skills.json`: add a full entry following the existing schema (security defaults: 100/100/95).
> - `data/marketplace.json`: increment `skill_count` for the `infrastructure` category and `total_skills` in `statistics`.
>
> Run `make validate` and confirm exit 0 with no new warnings beyond the WN-001 baseline. Do NOT update CHANGELOG yet -- that happens in Phase 6.

---

#### 2.2 -- Adopt `runbook-writer`

**Objective**: Create a new DevAI-Hub skill at `catalog/skills/infrastructure/runbook-writer/SKILL.md` that produces an operational runbook for a service, incident type, or deployment procedure.

**Prompt**:
> Create a new skill at `catalog/skills/infrastructure/runbook-writer/SKILL.md`. Source the body content from pm-claude-skills' `skills/runbook-writer/SKILL.md`. Rewrite to full DevAI-Hub schema (frontmatter + 5 mandatory body sections) following the same shape as 2.1. Specifically:
>
> 1. `description`: pushy, with trigger phrases `runbook`, `operational runbook`, `ops guide`, `deployment runbook`, `maintenance procedure`, `disaster recovery runbook`. SKIP clause: incident postmortems (use `incident-postmortem`), per-alert response runbooks (use `oncall-runbook`).
> 2. `## Instructions` preserves the upstream's Required Inputs (runbook type: Deployment / Incident Response / Maintenance / DR; system/service; audience; tech stack), Output Structure (Overview, Prerequisites, Step-by-Step Procedures, Rollback Steps, Troubleshooting Table, Escalation Paths), and the on-call-friendly tone constraint.
> 3. `## Common Rationalizations`: at least 4 entries (e.g. "The team already knows how to do this", "It will go stale anyway", "We can write it after the next incident", "The script comments are enough").
> 4. `## Verification`: binary checklist (e.g. "[ ] Every step has an exact command, not a description", "[ ] Rollback steps are present and reversible", "[ ] Estimated time to complete is stated", "[ ] All access prerequisites are listed").
> 5. `## Related Skills`: cross-link `sre-engineer`, `incident-postmortem`, `oncall-runbook`, `rollback-strategy-advisor`, `cd-pipeline-generator`.
>
> Update the 3 registry files (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`). Run `make validate` to confirm exit 0.

---

#### 2.3 -- Adopt `oncall-runbook`

**Objective**: Create a new DevAI-Hub skill at `catalog/skills/infrastructure/oncall-runbook/SKILL.md` that produces a per-alert on-call response runbook.

**Prompt**:
> Create a new skill at `catalog/skills/infrastructure/oncall-runbook/SKILL.md`. Source from pm-claude-skills' `skills/oncall-runbook/SKILL.md`. Rewrite to full DevAI-Hub schema. Specifics:
>
> 1. `description`: pushy, with triggers `on-call runbook`, `on-call guide`, `alert runbook`, `paging runbook`, `escalation procedure`, `on-call handoff`. SKIP clause: general operational runbooks (use `runbook-writer`), incident postmortems (use `incident-postmortem`).
> 2. `## Instructions` preserves the upstream's Quick Reference, Escalation Matrix, per-alert response procedures (Alert -> Diagnostic Commands -> Remediation -> Rollback), Service Dependencies, On-Call Handoff Template.
> 3. `## Common Rationalizations`: at least 4 (e.g. "We can figure it out at 3am from the dashboard", "The previous on-call left notes in Slack, that's enough", "Most alerts auto-resolve so a runbook is overkill").
> 4. `## Verification`: binary checklist (e.g. "[ ] Every alert that pages has a corresponding entry", "[ ] Rollback command is memorisable and given at the top", "[ ] Escalation path includes when-to-escalate, who-to-escalate-to, and how", "[ ] Diagnostic command list is plain shell, copy-pasteable").
> 5. `## Related Skills`: `sre-engineer`, `runbook-writer`, `incident-postmortem`, `observability-setup`.
>
> Update the 3 registry files. Run `make validate` to confirm exit 0.

---

#### 2.4 -- Adopt `pr-description-writer`

**Objective**: Create a new DevAI-Hub skill at `catalog/skills/workflow/pr-description-writer/SKILL.md` that produces reviewer-friendly PR descriptions.

**Prompt**:
> Create a new skill at `catalog/skills/workflow/pr-description-writer/SKILL.md`. Source from pm-claude-skills' `skills/pr-description-writer/SKILL.md`. Rewrite to full DevAI-Hub schema. Specifics:
>
> 1. `description`: pushy, with triggers `PR description`, `pull request description`, `draft PR`, `document code changes`, `merge request description`, `change summary for review`. SKIP clause: commit message generation (use `code-commit-workflow`), release notes (use `release-notes-writer`), changelog generation (use `/generate-changelog`).
> 2. `## Instructions` preserves the upstream's Required Inputs (what changed, why, how to test, risk level, PR type), Output Structure (Title <=72 chars imperative, Summary, Changes Made, Screenshots/Demo, How to Test, Testing Checklist, Risk and Rollout, Reviewer Notes).
> 3. `## Common Rationalizations`: at least 4 (e.g. "The diff explains itself", "Reviewers can just run the tests", "It's a tiny change, no description needed", "The commit message has everything").
> 4. `## Verification`: binary checklist (e.g. "[ ] Title is imperative mood and <=72 characters", "[ ] How-to-Test section has step-by-step reviewer instructions", "[ ] Risk level is stated", "[ ] Linked to issue/ticket if applicable").
> 5. `## Related Skills`: `code-commit-workflow`, `code-quality`, `intent-based-review`, `release-notes-writer`, `/generate-changelog` command.
>
> Update the 3 registry files. Run `make validate` to confirm exit 0.

---

#### 2.5 -- Phase 2 testing and stabilization

**Objective**: Run all validators after the 4 P0 adoptions; confirm no regression of the 366-test hook suite; confirm no new orphan warnings beyond the WN-001 baseline.

**Prompt**:
> Run `make validate`, `make lint`, and `make test` in sequence. All three must exit 0. `make test` must report the same 366 hook tests passing with 3 jq-conditional skips. `make validate` must emit no new warnings beyond the 4 WN-001 orphan warnings carried forward from v1.1.5. Manually inspect each of the 4 new SKILL.md files for:
>
> - YAML frontmatter parses cleanly (no missing required fields, no malformed quoting)
> - `summary_l0` is <=15 words and `overview_l1` is <=150 words
> - `description` field contains explicit trigger phrases AND a SKIP clause
> - Body has all 5 mandatory sections present (When to Use, Instructions, Common Rationalizations, Verification, Related Skills) in the correct order
> - Body length is between 100 and 800 lines (soft cap) -- if over 500, a `references/` subdirectory should exist and be linked
> - Common Rationalizations table has at least 4 rows
> - Verification section has at least 4 binary checklist items, each describing an observable artifact
> - Related Skills cross-links resolve to skills that actually exist in `data/SKILL_INDEX.md`
>
> Also confirm the 3 registry files are coherent: each of the 4 new skills appears exactly once in each of `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`. Run `python scripts/validate_skills.py --verbose` to surface any new orphans. After all checks pass, run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [ ] 4 new SKILL.md files exist at the resolved category paths
- [ ] All 4 files conform to DevAI-Hub schema (frontmatter + 5 body sections)
- [ ] 3 registry files updated for each of the 4 skills
- [ ] `make validate` exits 0 with no new warnings beyond WN-001 baseline
- [ ] `make lint` exits 0
- [ ] `make test` reports 366 passing (3 skipped) -- same as baseline
- [ ] Session history generated for Phase 2
- [ ] Ready to advance to Phase 3

---

## Phase 3: P1 Skill-Native Adoptions

**Goal**: Ship the 2 P1 engineering document-template skills.
**Prerequisites**: Phase 2 complete.
**Stability Gate**: 2 new skills exist with full DevAI-Hub schema; `make validate` passes; the 3 registry files have been updated; no new orphan warnings.

### Sub-tasks

#### 3.1 -- Adopt `architecture-decision-record`

**Objective**: Create a new DevAI-Hub skill at `catalog/skills/architecture/architecture-decision-record/SKILL.md` (placement confirmed in Phase 1.1) that produces a single ADR document.

**Prompt**:
> Create a new skill at `catalog/skills/architecture/architecture-decision-record/SKILL.md`. Source from pm-claude-skills' `skills/architecture-decision-record/SKILL.md`. Rewrite to full DevAI-Hub schema. Specifics:
>
> 1. `description`: pushy, with triggers `ADR`, `architecture decision record`, `architecture decision`, `record this decision`, `document this decision`, `MADR`. SKIP clause: full architecture design from scratch (use `architecture-design`), general technical documentation (use `technical-documentation`), API design decisions narrower than architecture-level (use `api-design`).
> 2. `## Instructions` preserves the upstream's Required Inputs (decision title, context, options considered, decision, consequences, risks, status) and Output Structure (MADR-style or Nygard-style template, the agent picks one and states which). Include a short table comparing MADR vs. Nygard so the user can choose. Status field follows the standard lifecycle: Proposed -> Accepted -> Deprecated -> Superseded.
> 3. `## Common Rationalizations`: at least 4 (e.g. "We already discussed it in the meeting, that's enough", "The PR description has the rationale", "It's reversible, so no ADR needed", "We'll write it after the implementation lands").
> 4. `## Verification`: binary checklist (e.g. "[ ] Status field is set", "[ ] At least 2 alternative options are documented with rejection rationale", "[ ] Consequences section covers both positive and negative", "[ ] Decision is dated and authored").
> 5. `## Related Skills`: `architecture-design`, `technical-documentation`, `api-design`, `ddd-strategic-design`.
>
> Update the 3 registry files. Run `make validate` to confirm exit 0.

---

#### 3.2 -- Adopt `test-strategy-doc`

**Objective**: Create a new DevAI-Hub skill at `catalog/skills/tests-generation/test-strategy-doc/SKILL.md` that produces a full test strategy document.

**Prompt**:
> Create a new skill at `catalog/skills/tests-generation/test-strategy-doc/SKILL.md`. Source from pm-claude-skills' `skills/test-strategy-doc/SKILL.md`. Rewrite to full DevAI-Hub schema. Specifics:
>
> 1. `description`: pushy, with triggers `test strategy`, `test plan`, `testing strategy doc`, `QA strategy`, `test approach document`, `risk-based testing plan`. SKIP clause: writing specific test cases (use `test-cases`), generating unit tests (use `unit-tests` or `generate-unit-tests`), reviewing existing test coverage (use `testing-review`).
> 2. `## Instructions` preserves the upstream's Required Inputs (scope, risk assessment, test types in play, coverage targets, P0/P1 cases, test data strategy, environment plan, entry/exit criteria) and Output Structure (Scope, Risk Assessment matrix, Test Types matrix, Coverage Targets, P0/P1 Test Case index, Tooling, Schedule, Entry/Exit Criteria, Sign-off).
> 3. `## Common Rationalizations`: at least 4 (e.g. "We have unit tests, that's the strategy", "QA will figure it out", "We'll do exploratory testing", "Coverage targets are arbitrary").
> 4. `## Verification`: binary checklist (e.g. "[ ] Risk assessment matrix has at least 5 rows with likelihood x impact scoring", "[ ] Coverage targets are explicit numbers, not 'high'", "[ ] Entry and exit criteria are listed", "[ ] P0 test cases are named and traceable to requirements").
> 5. `## Related Skills`: `test-structure`, `test-cases`, `code-coverage`, `testing-review`, `integration-test-generator`, `e2e-testing-automation`.
>
> Update the 3 registry files. Run `make validate` to confirm exit 0.

---

#### 3.3 -- Phase 3 testing and stabilization

**Objective**: Validate Phase 3 outputs and confirm no regressions.

**Prompt**:
> Run `make validate`, `make lint`, and `make test`. All three must exit 0 with the same baseline as Phase 2 (366 tests / 3 skips / 4 carry-over WN-001 orphan warnings, plus no new orphans introduced by the 2 new Phase 3 skills). Manually inspect each of the 2 new SKILL.md files for the same schema compliance checks as Phase 2.5. Confirm the cumulative count: `data/marketplace.json` `total_skills` should now equal the v1.3.0 baseline (197) plus 6 (Phase 2 added 4, Phase 3 added 2) = 203. Run `/generate-session-history` to document Phase 3.

---

### Phase 3 Exit Checklist

- [ ] 2 new SKILL.md files exist at the resolved category paths
- [ ] Both files conform to DevAI-Hub schema
- [ ] 3 registry files updated for each
- [ ] `make validate` / `make lint` / `make test` all exit 0
- [ ] `total_skills` in `data/marketplace.json` is 203
- [ ] Session history generated for Phase 3
- [ ] Ready to advance to Phase 4

---

## Phase 4: Re-Full -- Engineering Bundle Expansion

**Goal**: Expand `data/bundles.json` with 2-3 engineering-themed bundles modeled on the existing `release-prep` bundle, grouping the 6 new skills with related existing skills.
**Prerequisites**: Phases 2 and 3 complete (all 6 new skills must exist before they can be referenced from a bundle).
**Stability Gate**: `data/bundles.json` is well-formed; `make validate` exits 0; every bundle's skill list resolves to existing entries in `data/SKILL_INDEX.md`.

### Sub-tasks

#### 4.1 -- Author the new bundles

**Objective**: Add 2-3 new bundle entries to `data/bundles.json`.

**Prompt**:
> Read `data/bundles.json` to learn the bundle schema (modeled on the existing `release-prep` bundle). Add the following new bundles after `release-prep`:
>
> 1. **`incident-response`** -- grouping: `sre-engineer`, `incident-postmortem` (new in Phase 2.1), `runbook-writer` (new in Phase 2.2), `oncall-runbook` (new in Phase 2.3), `rollback-strategy-advisor`, `observability-setup`, `debug-with-logs`. Description: "One-click skill set for incident response: SRE patterns, postmortems, operational runbooks, on-call runbooks, rollback strategy, observability, and log-based debugging."
> 2. **`pr-workflow`** -- grouping: `code-commit-workflow`, `pr-description-writer` (new in Phase 2.4), `code-quality`, `intent-based-review`, `testing-review`, `security-review`. Description: "Pull request authoring and review: commit hygiene, PR description authoring, multi-axis code review (quality / intent / testing / security)."
> 3. **`architecture-docs`** (optional 3rd bundle) -- grouping: `architecture-design`, `architecture-decision-record` (new in Phase 3.1), `technical-documentation`, `api-design`, `ddd-strategic-design`, `component-boundary-identifier`. Description: "Architecture decision-making and documentation: design, ADRs, technical docs, API contracts, domain-driven design, component boundaries."
>
> Validate the JSON: every skill name in every bundle's `skills` array must exist in `data/SKILL_INDEX.md` (verify by grepping). Run `make validate` to confirm `data/bundles.json` parses and exits 0. Do NOT touch `data/SKILL_INDEX.md`, `data/skills.json`, or `data/marketplace.json` in this sub-task -- only `data/bundles.json`.

---

#### 4.2 -- Phase 4 stabilization

**Objective**: Validate bundle expansion.

**Prompt**:
> Run `make validate` and confirm exit 0 with no new warnings. Grep `data/bundles.json` for each bundle's skill list and cross-check against `data/SKILL_INDEX.md` -- every named skill must exist. Confirm bundle JSON is well-formed (`python -c "import json; json.load(open('data/bundles.json'))"`). Run `/generate-session-history` to document Phase 4.

---

### Phase 4 Exit Checklist

- [ ] 2-3 new bundles in `data/bundles.json`
- [ ] Every bundle skill name resolves in `data/SKILL_INDEX.md`
- [ ] `make validate` exits 0
- [ ] Session history generated for Phase 4
- [ ] Ready to advance to Phase 5

---

## Phase 5: Marketing Pattern Adoption

**Goal**: Adopt the 2 P3 marketing patterns: a roadmap section in README and a narrative-style DEVLOG entry for this adoption.
**Prerequisites**: Phases 2, 3, 4 complete.
**Stability Gate**: README and DEVLOG render correctly in Markdown preview; no broken internal links.

### Sub-tasks

#### 5.1 -- Add a "Roadmap" section to README.md

**Objective**: Add a community-facing roadmap section to the project README, inspired by pm-claude-skills' star-milestone roadmap but stripped of star gating and sponsor framing per user memory ("DevAI-Hub stays company-neutral / personal project").

**Prompt**:
> Add a new `## Roadmap` section to `README.md`, placed before the "Contributing" section (or wherever fits the existing structure). The section should:
>
> - Be ~30-60 lines.
> - List 3-5 near-term focus areas as bullets with a one-sentence description each (e.g. "Engineering doc-template skills (v1.4.0 -- shipped)", "Cross-OS CI matrix for installer smoke tests (v1.5.0 -- planned, addresses the cumulative DF-003/005/006/007/008 cluster from v1.1.5 known-gaps)", "MCP registry expansion under the existing 5-step policy", "Skill-eval-loop integration into pre-commit", etc.).
> - Use a simple "Planned / In progress / Shipped" status column or inline tag -- NO star milestones, NO sponsor tiers (these are out of scope per user memory).
> - Reference the most recent `docs/<version>/plans/` files as the durable source for upcoming work.
> - End with a sentence pointing readers to `docs/DEVLOG.md` for narrative-style updates and `CHANGELOG.md` for the formal Keep-a-Changelog log.
>
> Do NOT use emojis. Do NOT add any "Sponsor" or "Sustaining sponsor" framing. Run `make validate` (if it touches Markdown) and visually confirm the section renders correctly.

---

#### 5.2 -- Write a narrative-style DEVLOG entry for the adoption

**Objective**: Add a single narrative-style entry to `docs/DEVLOG.md` covering this adoption -- the rationale, the comparison report, the 6 new skills, the dropped 5, and the cross-cutting decisions.

**Prompt**:
> Append a new entry to `docs/DEVLOG.md` (or create the file under that path if it does not exist) dated today. The entry should be 200-400 words, written in narrative style inspired by pm-claude-skills' Medium-article voice but kept terse and developer-facing. Cover:
>
> 1. What happened: `/compare-project` was run against `mohitagw15856/pm-claude-skills`, surfacing 9 in-scope adoptions and 5 explicit drops.
> 2. The adoption philosophy: skill-native first per the MCP Registry Policy decision tree; 6 new engineering document-template skills filling the "advisor vs. document-producer" gap that pm-claude-skills exposed (DevAI-Hub had advisor skills like `sre-engineer` that conceptually covered postmortems / runbooks / on-call, but no dedicated artifact-producing skill for each).
> 3. What was dropped and why: 4-template vendor-connector pattern (violates MCP Registry Policy hard-no list); flat directory layout (regressive vs. 22-category nested); ~108 non-engineering skills (out of scope); `system-design-interview` (out of scope); sponsor-tier README framing (project is company-neutral).
> 4. Cross-cutting note: cumulative cross-OS installer smoke run from v1.1.5 known-gaps remains the durable fix and is NOT extended by this adoption (all artifacts are pure SKILL.md).
> 5. Where this went: `docs/archive/v1/v1.3/comparison-pm-claude-skills.md` and `docs/archive/v1/v1.3/plans/adoption-pm-claude-skills.md`, with v1.4.0 as the target release.
>
> Do NOT include emojis. Do NOT include AI-attribution language. Treat this as a developer note, not a Medium article.

---

#### 5.3 -- Phase 5 stabilization

**Objective**: Validate Phase 5 outputs.

**Prompt**:
> Render-check `README.md` and `docs/DEVLOG.md` in Markdown preview (any tool that produces an HTML or rendered output -- the user's IDE or `pandoc README.md` if available). Confirm no broken internal links to `docs/`, `data/`, or `catalog/`. Run `/generate-session-history` to document Phase 5.

---

### Phase 5 Exit Checklist

- [ ] `README.md` has a new `## Roadmap` section
- [ ] `docs/DEVLOG.md` has a new narrative-style entry for this adoption
- [ ] No broken Markdown links
- [ ] No emojis introduced, no sponsor / company framing
- [ ] Session history generated for Phase 5
- [ ] Ready to advance to Phase 6

---

## Phase 6: Final Validation, CHANGELOG, Version Bump Prep

**Goal**: Compose the v1.4.0 CHANGELOG entry, confirm all validators pass cumulatively, and prepare for `/wrap-up-session` to bump the version.
**Prerequisites**: Phases 1-5 complete.
**Stability Gate**: Full validator suite green; CHANGELOG `[1.4.0]` block well-formed and complete; the 14 canonical version-bump files (per user memory `project_release_v097.md`) identified for the eventual bump.

### Sub-tasks

#### 6.1 -- Author CHANGELOG `[1.4.0]` entry

**Objective**: Write a complete Keep-a-Changelog-formatted `[1.4.0]` block in `CHANGELOG.md` covering all of this plan's work.

**Prompt**:
> Read `CHANGELOG.md` and study the v1.3.0 entry structure (Added / Changed / Tests / etc. subsections). Add a new `## [1.4.0] - <today's date>` block above v1.3.0. The block must include:
>
> **Added**:
> - 6 new SKILL.md entries with full DevAI-Hub schema. Name each: `incident-postmortem` (infrastructure), `runbook-writer` (infrastructure), `oncall-runbook` (infrastructure), `pr-description-writer` (workflow), `architecture-decision-record` (architecture), `test-strategy-doc` (tests-generation).
> - 2-3 new bundles in `data/bundles.json`: `incident-response`, `pr-workflow`, `architecture-docs` (whichever were created in Phase 4).
> - A new `## Roadmap` section in `README.md`.
> - A new narrative-style DEVLOG entry under `docs/DEVLOG.md`.
>
> **Changed**:
> - `data/marketplace.json` `total_skills` from 197 to 203.
> - `data/marketplace.json` per-category `skill_count` for `infrastructure` (+3), `workflow` (+1), `architecture` (+1), `tests-generation` (+1).
> - Installer banner version from `1.3.0` to `1.4.0` (in `scripts/installer.sh` and `scripts/installer.ps1`) -- to be done at version-bump time in `/wrap-up-session`, NOT in this CHANGELOG draft.
>
> **Tests**:
> - 366 hook pytest tests still pass (no regression). No new hook tests required (this adoption ships no hooks).
> - `make validate` exits 0; orphan warnings stable at the 4 pre-existing WN-001 carry-overs.
>
> Use ASCII-only punctuation (no em-dashes, en-dashes, curly quotes, ellipsis chars) per user global rule. Use logical punctuation (period outside quotes). Single continuous lines per bullet (no hard-wrap). Reference the source comparison report and this plan as the durable rationale.

---

#### 6.2 -- Cumulative validator pass

**Objective**: Final green-build check before handoff to `/wrap-up-session`.

**Prompt**:
> Run all three validators sequentially:
>
> ```
> make validate
> make lint
> make test
> ```
>
> All must exit 0. `make test` must still report 366 passing with 3 skipped (no regression from baseline). `make validate` must still emit only the 4 WN-001 carry-over orphan warnings (no new orphans). If any validator regresses, halt and report -- do NOT proceed to version-bump prep.
>
> Also verify cumulative counts:
> - `data/marketplace.json` `total_skills`: 203 (was 197 at v1.3.0)
> - `data/SKILL_INDEX.md`: 6 new rows added since v1.3.0 (count the diff vs. last commit on `main`)
> - `data/skills.json`: 6 new entries
> - `data/bundles.json`: 2-3 new bundle entries
> - `README.md`: 1 new `## Roadmap` section
> - `docs/DEVLOG.md`: 1 new narrative entry
> - `CHANGELOG.md`: 1 new `[1.4.0]` block
>
> Output a single-line cumulative summary suitable for pasting into the next `/wrap-up-session` invocation.

---

#### 6.3 -- Identify version-bump surface (do NOT bump)

**Objective**: List the 14 canonical version-bump files (per user memory `project_release_v097.md`) and confirm each is touched (or skipped intentionally) by the v1.4.0 bump that `/wrap-up-session` will perform.

**Prompt**:
> Per user memory `project_release_v097.md`, the version-bump surface is 14 canonical files. Identify each by grepping for the v1.3.0 string and confirm the list. Common locations:
>
> - `scripts/installer.sh` (banner version)
> - `scripts/installer.ps1` (banner version)
> - `.claude-plugin/plugin.json`
> - `.claude-plugin/marketplace.json`
> - `data/marketplace.json` (version field if present)
> - `CHANGELOG.md` (new version heading -- already done in 6.1)
> - `AGENTS.md` (skill total references)
> - `README.md` (skill total references)
> - others as memory indicates
>
> Produce a checklist. Do NOT edit any of these files -- the actual version bump is performed by `/wrap-up-session` -> `/update-version`. This sub-task only confirms the surface is well-understood and ready.

---

#### 6.4 -- Phase 6 stabilization and handoff

**Objective**: Final session history and clear handoff to `/wrap-up-session`.

**Prompt**:
> Run `/generate-session-history` for Phase 6. The session history should summarize all 6 phases at a high level. Then announce to the user: "Plan execution complete. Cumulative summary: 6 new skills, N new bundles, 1 README roadmap section, 1 DEVLOG entry, 1 CHANGELOG [1.4.0] block. All validators green. Ready to invoke `/wrap-up-session` to bump v1.3.0 -> v1.4.0 and produce the release commit."

---

### Phase 6 Exit Checklist

- [ ] CHANGELOG `[1.4.0]` block authored and formatted correctly
- [ ] `make validate` / `make lint` / `make test` all exit 0
- [ ] Cumulative skill count = 203
- [ ] Version-bump surface identified for `/wrap-up-session`
- [ ] Session history generated for Phase 6
- [ ] Ready for `/wrap-up-session`

---

## Items explicitly NOT adopted (security / policy reasons)

The following 5 items appeared in the source comparison report but are dropped per the MCP Registry Policy in [AGENTS.md](../../../AGENTS.md). They do NOT appear in any phase of this plan and must NOT be silently re-introduced.

**N1. Agent template pattern with vendor connectors.** Source: pm-claude-skills' 4 "agent templates" (`pm-sprint-agent`, `pm-discovery-agent`, `pm-stakeholder-comms-agent`, `pm-launch-agent`) bundling skills + subagents + named third-party SaaS connectors (Linear, Jira, Salesforce, Gong, Notion, Slack, Workday, NetSuite, HubSpot, Google Drive). Classification: `drop-outright`. Rationale: adopting the pattern would require shipping MCP wrappers for vendor SaaS that DevAI-Hub's MCP Registry Policy explicitly excludes via its hard-no list ("search-as-service, embeddings-as-service, scraping-as-service, generation-as-service") and via its trusted-vendor decision-tree gate ("acceptable only when all three conditions hold ... feature is extremely worth it ... `_comment` must explicitly justify each of the three conditions"). The orchestration-level idea (multi-skill workflows) is already addressed by existing DevAI-Hub commands like `/run-deep-review`, `/implement-phase`, `/wrap-up-session` without any vendor coupling.

**N2. Flat `skills/<name>/` directory layout.** Classification: `drop-outright`. DevAI-Hub's 22-category nested layout under `catalog/skills/<category>/<name>/` is required by `make validate`, by the registry generators, and by `data/SKILL_INDEX.md` schema. Collapsing to flat would break `make build-catalog` and remove a primary discovery axis with no upside. No security implication, but a structural regression that violates the existing `AGENTS.md` "category placement" guidance.

**N3. All non-engineering skills (~108 of 114) from PM, Marketing, Legal, Finance, HR, Sales, Operations, Design/UX, Healthcare/Research, Cross-Profession, Figma bundles.** Classification: `drop-outright`. Out of scope per `AGENTS.md` repository overview ("DevAI-Hub is a production-grade skill catalog for AI coding assistants"). Adopting them would dilute the catalog's identity and conflict with the documented scope. The scope statement is the primary defense against scope creep.

**N4. `system-design-interview` skill.** Classification: `drop-outright`. Interview prep is not "AI coding assistant" territory. Out of scope per `AGENTS.md` repository overview.

**N5. Sponsor / financial-tier README framing.** Classification: `drop-outright`. Per user memory (`user_role.md`, `feedback_no_employer_refs.md`), DevAI-Hub is a personal project and stays company-neutral. Sponsor tiers, sustaining-sponsor logo placement, "$5/month coffee tier" framing, and similar monetization patterns are not appropriate for this project. This decision is reviewable by the maintainer at any time but is not in scope for this adoption.

---

## How to begin

Run `/implement-phase adoption-pm-claude-skills` (or paste the prompt from sub-task 1.1 into a fresh Claude Code session). Phase 1 has no prerequisites and the entire plan is dependency-ordered after that.
