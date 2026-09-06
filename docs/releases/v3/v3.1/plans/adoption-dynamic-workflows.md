# Plan -- Adopt the Dynamic Workflows residual gap (workflow-as-skill-bundle)

**Project**: Nexus-Hub
**Version**: v3.1.0
**Slug**: adoption-dynamic-workflows
**Plan Type**: Feature / Enhancement
**Created**: 2026-06-04
**Goal**: Establish a workflow-as-skill-bundle convention (ship gracefully-degrading `.js` Dynamic-Workflow templates inside skill bundles, referenced from SKILL.md) and pilot it on high-value read-only fan-out skills, plus two minor orchestration enrichments.

## Overview

This plan operationalizes [`../comparison-a-harness-for-every-task-dynamic-workflows-in-claude-code.md`](../comparison-a-harness-for-every-task-dynamic-workflows-in-claude-code.md) at full scope (P0-P3). The article's orchestration theory was already adopted today in v3.0.0 as `agent-orchestration-primitives` (+ `references/five-patterns.md`) and the `multi-agent-coordinator` enrichment; 10 of 11 insights are Already Implemented (see the comparison's Section 4 for file-path evidence). This plan therefore covers only the genuine residuals: (1) the **workflow-as-skill-bundle distribution pattern** -- the article's "place JavaScript workflow files in a skill folder and reference them in SKILL.md as templates" guidance, which Nexus-Hub's Tier-3 bundled-resources convention already makes possible but which no skill uses; and (2) two minor enrichments (pairwise-tournament ranking-at-scale; `/loop`+`/goal` cross-reference).

**Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 6 of the source comparison for the ordering rationale.** Every item is `skill-native` (catalog markdown + a local `.js` template that runs via the platform's own Dynamic Workflows runtime; no client, key, dependency, or outbound call), so all phases sit in the single skill-native bucket, ordered by dependency. There are no `re-full`, `re-partial`, `vendor-intrinsic`, or `drop-outright` items.

This plan is single-source and forward-looking; it intentionally does NOT ingest the v2.4.0 / v3.0.0 general known-gaps backlog.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/v3/v3.1/constitution.md - skipping check. Recommend running /constitution to establish project principles.

This plan aligns with the `AGENTS.md` MCP Registry Policy by construction: all content is LLM-native catalog material; the bundled workflow template introduces no outbound call, credential, or dependency and must degrade gracefully when Dynamic Workflows is unavailable.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Workflow-bundle convention (skill-native) | Documented convention in AGENTS.md + one reference graceful-degrading `.js` workflow template |
| 2 | Pilot on high-value read-only skills (skill-native) | Two pilot skills carry a referenced workflow template with scope-first token framing |
| 3 | Minor orchestration enrichments (skill-native) | Tournament ranking-at-scale shape + `/loop`/`/goal` cross-reference added |

---

## Phase 1: Workflow-bundle convention (skill-native)

**Goal**: Define and document how a skill ships a Dynamic-Workflow `.js` template as a Tier-3 bundled resource, and author one reference template.
**Prerequisites**: None (rides the existing `agent-orchestration-primitives` skill and the bundled-resources convention).
**Stability Gate**: AGENTS.md documents the convention; a reference `.js` workflow template exists with mandatory graceful-degradation framing; `make validate` green (no orphan-bundle warning).

### Sub-tasks

#### 1.1 -- Document the workflow-bundle convention

- [x] T001 Document the workflow-as-skill-bundle convention in AGENTS.md (Per-skill Bundled Resources section)

**Objective**: Add the article's distribution pattern to the canonical bundled-resources rules.

**Prompt**:
> In `AGENTS.md`, extend the "Per-skill Bundled Resources" subsection to document workflow templates: a skill MAY ship a Dynamic-Workflow `.js` file under its `scripts/` (or `assets/`) directory, referenced from SKILL.md AS A TEMPLATE to adapt (not a verbatim script to run). State the mandatory rules: (a) the template must degrade gracefully -- fall back to subagents / single-agent when Dynamic Workflows is unavailable (a plan-gated research-preview feature); (b) it must carry the scope-first token caution (calibrate on one folder, review the plan on first trigger, confirm before full scale) and cross-link `[[ai-billing-safeguards]]`; (c) it is `skill-native` (no outbound, no dependency). Reference `agent-orchestration-primitives` as the decision guide. Note that the orphan-bundle audit requires the `.js` file be referenced from SKILL.md.

---

#### 1.2 -- Author a reference workflow template

- [x] T002 Author a reference graceful-degrading Dynamic-Workflow template in catalog/skills/orchestration/agent-orchestration-primitives/assets/example-fanout-workflow.js

**Objective**: Provide a canonical, copy-adaptable template the convention can point to.

**Prompt**:
> Author a reference Dynamic-Workflow `.js` template (a read-only fan-out-and-synthesize example, e.g. "audit every file under a directory and synthesize findings") at `catalog/skills/orchestration/agent-orchestration-primitives/assets/example-fanout-workflow.js`. Begin with the required `export const meta = {...}` literal. Include inline comments marking it a TEMPLATE TO ADAPT, the scope-first token caution, and a graceful-degradation note. Reference the asset from the `agent-orchestration-primitives` SKILL.md (Step 7 / Related section) so it is not an orphan bundle. Keep it illustrative, not a production script.

---

#### 1.3 -- Testing and Stabilization

- [x] T003 Validate the convention and reference template via make validate

**Objective**: Confirm the new bundle is referenced and the catalog stays clean.

**Prompt**:
> Run `make validate` and confirm the orphan-bundle audit does not flag `example-fanout-workflow.js` (it must be referenced from SKILL.md). Confirm the skill stays within the size norm and the registries are unchanged (no new skill, so no `data/` edits needed -- verify this). Fix any issues and iterate. After passing, run `/generate-session-history` to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: Pilot on high-value read-only skills (skill-native)

**Goal**: Apply the convention to two skills whose work is large-surface, read-only, and embarrassingly parallel -- exactly the article's canonical fan-out use case.
**Prerequisites**: Phase 1 (convention + reference template).
**Stability Gate**: two pilot skills each reference an adapted workflow template with graceful degradation + token caution; `make validate` green.

### Sub-tasks

#### 2.1 -- Pilot bundle: multi-agent code review

- [x] T004 Add an adapted fan-out workflow template to catalog/skills/code-review/multi-agent-code-review/

**Objective**: Give the large-surface review skill a ready-made (adaptable) fan-out harness.

**Prompt**:
> Add an adapted Dynamic-Workflow template under `catalog/skills/code-review/multi-agent-code-review/scripts/` implementing the dimensions -> find -> adversarially-verify pattern (per-dimension review fanned out, each finding verified by an independent agent). Reference it from that skill's SKILL.md as a template, with the graceful-degradation + scope-first token framing from Phase 1. Do not duplicate the agent-orchestration-primitives guidance -- cross-link it.

---

#### 2.2 -- Pilot bundle: deep research compilation

- [x] T005 Add an adapted fan-out workflow template to catalog/skills/specialized-domains/deep-research-compilation/

**Objective**: Mirror the article's published `/deep-research` fan-out -> fetch -> verify -> synthesize shape in the catalog's research skill.

**Prompt**:
> Add an adapted Dynamic-Workflow template under `catalog/skills/specialized-domains/deep-research-compilation/scripts/` implementing fan-out searches -> fetch sources -> adversarial verification -> synthesize a cited report. Reference it from the skill's SKILL.md as an adaptable template with graceful degradation and the token caution. Keep the skill body within the size norm; push detail into the bundled file.

---

#### 2.3 -- Testing and Stabilization

- [x] T006 Validate both pilot bundles via make validate

**Objective**: Confirm both templates are referenced and the catalog stays clean.

**Prompt**:
> Run `make validate`; confirm neither bundled template is flagged as an orphan and both skills stay within the size norm. Verify no `data/` registry edits are needed (no new skills). Fix and iterate. After passing, run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Minor orchestration enrichments (skill-native)

**Goal**: Close the two minor residual gaps -- the pairwise-tournament ranking-at-scale shape and the `/loop`+`/goal` cross-reference.
**Prerequisites**: None (independent of Phases 1-2; grouped last as P3 polish).
**Stability Gate**: the tournament ranking-at-scale shape is cataloged distinctly from best-of-N; `agent-orchestration-primitives` cross-references `/loop` and `/goal`; `make validate` green.

### Sub-tasks

#### 3.1 -- Add the tournament ranking-at-scale shape

- [x] T007 Add the pairwise-tournament ranking-at-scale shape to catalog/skills/orchestration/agent-orchestration-primitives/references/five-patterns.md

**Objective**: Catalog ranking/sorting many items by repeated pairwise comparison, distinct from competitive-generation's best-of-N.

**Prompt**:
> In `references/five-patterns.md` (and/or `competitive-generation` SKILL.md), add the pairwise-tournament ranking-at-scale shape: ranking/sorting N items (rank 80 resumes, sort 1000 tickets by severity) via repeated pairwise comparison or bucket-rank-then-merge, where each comparison is an isolated agent and a deterministic loop holds the bracket. Distinguish it explicitly from best-of-N selection (which `competitive-generation` already covers). Keep within the size norm.

---

#### 3.2 -- Cross-reference /loop and /goal

- [x] T008 Cross-reference the /loop and /goal platform commands in catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md

**Objective**: Point users to the built-in commands for continuous/durable operation without shipping them.

**Prompt**:
> Add a short note to `agent-orchestration-primitives` SKILL.md that pairs workflows with the platform `/loop` (scheduled/continuous runs) and `/goal` (hard completion requirements) commands. Frame these as Claude Code built-ins to reference, NOT catalog artifacts Nexus-Hub ships. One or two sentences plus the existing cross-link style.

---

#### 3.3 -- Testing and Stabilization

- [x] T009 Final validation via make validate

**Objective**: Confirm the enrichments keep the catalog clean.

**Prompt**:
> Run `make validate`; confirm all touched skills stay within the size norm and no orphan bundles or registry drift were introduced. Add a CHANGELOG `## [Unreleased]` entry summarizing the workflow-bundle convention + pilots + enrichments. Fix and iterate. After passing, run `/generate-session-history` to document Phase 3.

---

## Complexity Tracking

> Fill ONLY if Constitution Check has violations that must be justified.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | -- | All Constitution Check items are N/A (no constitution file); no violations to justify. |

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing
- [x] No known regressions from prior phases
- [x] Session history generated for this phase
- [x] Adoption complete; CHANGELOG updated

---

## Items explicitly NOT adopted (security / policy reasons)

- **None.** No insight in the source article implies an outbound call, a new dependency, a credential, or a third-party data processor, so there is no `drop-outright` item. The `/loop` and `/goal` commands are Claude Code built-ins that Nexus-Hub references but does not (and should not) ship -- this is a scope boundary, not a security drop.
