---
name: project-constitution
description: "Author and maintain a versioned project constitution - a governance document declaring the MUST / SHOULD principles that every plan, spec, and implementation MUST align with. Use whenever the user wants to ratify project principles, write a constitution, define non-negotiable rules, set governance for a codebase, declare architectural invariants, or amend an existing constitution. Trigger phrases include \"draft a constitution\", \"ratify principles\", \"project governance\", \"MUST rules\", \"set the ground rules\", \"amend the constitution\", \"what are our non-negotiables\", \"principle 4 says...\", \"constitution check\". Cross-links to `[[spec-driven-development]]`, `[[architecture-decision-record]]`, `[[implementation-plan]]`, and `[[known-gaps-tracker]]`. SKIP: CLAUDE.md / AGENTS.md agent-instructions edits (those are tool-facing, not project-principle-facing), single-feature READMEs, ADRs that record one decision (use `[[architecture-decision-record]]`), or commit-message conventions (use `[[code-commit-workflow]]`)."
summary_l0: "Author and maintain a versioned constitution declaring MUST / SHOULD principles for every artifact"
overview_l1: "This skill produces and amends a project constitution at `docs/<version>/constitution.md` or `CONSTITUTION.md` at the repo root. A constitution is distinct from CLAUDE.md / AGENTS.md (agent-instructions for AI tools): it is project-governance for humans and machines alike, listing the MUST and SHOULD principles every downstream artifact (specs, plans, ADRs, code) must align with. The skill defines the structure (preamble, numbered principles, governance section, ratified / last-amended date line), the SemVer amendment workflow (MAJOR for principle removals / redefinitions, MINOR for additions, PATCH for clarifications), and the Sync Impact Report emitted as an HTML comment at the top. It pairs with the `/constitution` command and the `constitution-template.md` skeleton. Use it to establish principles for the first time, amend an existing constitution, or run a propagation check after edits. Trigger phrases: draft a constitution, ratify principles, project governance, MUST rules, amend the constitution, set the ground rules, constitution check, what are our non-negotiables."
---

# Project Constitution

Author and maintain a versioned governance document that declares the MUST / SHOULD principles every plan, spec, ADR, and implementation in the project must align with. The constitution is the project's highest-authority rulebook - downstream artifacts cite it, and the Constitution Check gate in `/generate-plan` enforces alignment before any phase begins.

## When to Use This Skill

- When the user asks to **draft, ratify, or write a constitution** for a new or existing project.
- When the user wants to **amend an existing constitution** (add, remove, redefine, or clarify a principle).
- When the user wants to **declare non-negotiables, ground rules, project invariants, or MUST principles** that downstream specs and plans must align with.
- When a Constitution Check in a plan FAILS and the constitution itself needs to be updated rather than the plan.
- When the user wants to **propagate a constitution change** across templates, command files, and downstream plans.

**When NOT to use**:

- For CLAUDE.md / AGENTS.md (tool-facing agent-instructions) - those describe how AI assistants should behave in this repo, not what the project itself must be.
- For one-off decisions (use `[[architecture-decision-record]]`).
- For sprint-level todos or roadmap items (use `[[dev-progress-tracker]]`).
- For commit-message conventions or per-file style guides (use `[[code-commit-workflow]]` or `catalog/style-guides/`).

### Marking uncertainty with `[NEEDS CLARIFICATION]`

When drafting or amending a constitution, the `[NEEDS CLARIFICATION: <specific question>]` marker is the standard channel for surfacing uncertainty rather than guessing. Maximum 3 markers total per constitution; if a draft would carry more than 3, prioritize by `scope > security/privacy > UX > technical` and demote the rest to assumptions with informed defaults (documented in an `## Assumptions` subsection of the relevant principle). Rationale: a constitution that surfaces every minor uncertainty is unreadable; one that hides every uncertainty is unsafe. The cap forces the author to triage.

## File Location

**Recommended**: `docs/<version>/constitution.md` - aligns with Nexus-Hub's versioned-docs convention and lets the file evolve in the same version folder as the plans that cite it.

**Acceptable**: `CONSTITUTION.md` at the repo root - acceptable when the constitution is stable across many versions and you prefer one canonical path.

The `/constitution` command writes to `docs/<version>/constitution.md` by default. If the file already exists at the root, the command edits it in place.

## File Format

```markdown
<!--
SYNC IMPACT REPORT (generated YYYY-MM-DD)
Version change: 1.2.0 -> 1.3.0 (MINOR; principle added)
Modified principles: <list, or "none">
Added sections: <list, or "none">
Removed sections: <list, or "none">
Templates / commands requiring updates: <list of files that reference the affected principles>
-->

# Project Constitution

**Project**: <name>
**Version**: <X.Y.Z>
**Ratified**: <YYYY-MM-DD>
**Last Amended**: <YYYY-MM-DD>

## Preamble

<One paragraph stating the constitution's purpose and authority. Cite which downstream artifacts are bound by it (plans, specs, ADRs, code reviews, releases).>

## Principles

### 1. <Principle title>

**Statement**: <One-sentence MUST or SHOULD declaration.>

**Rationale**: <Why this principle exists - the failure mode it prevents.>

**Applies to**: <The downstream artifacts this principle constrains - e.g., "all plans under docs/<version>/plans/", "all PRs touching extensions/", "every commit to main".>

### 2. <Principle title>

...

## Governance

- **Amendment process**: <How principles get added, removed, or redefined. Typically requires a PR with a Sync Impact Report.>
- **Conflict resolution**: <What happens when two principles appear to conflict.>
- **Enforcement**: <Which commands or checks enforce the constitution - e.g., "/generate-plan emits a Constitution Check section that must pass before Phase 0 research", "code review checklist references principle IDs".>

## Versioning

Version increments follow SemVer applied to principles:

- **MAJOR**: a principle is removed or its meaning is redefined in a backwards-incompatible way.
- **MINOR**: a principle is added or a section grows non-incompatibly.
- **PATCH**: wording is clarified; no semantic change.
```

## Instructions

### Drafting a new constitution

1. Confirm the file location (default `docs/<version>/constitution.md`).
2. Ask the user to name 3-5 principles. For each, capture the **Statement** (MUST or SHOULD), the **Rationale** (the failure mode it prevents), and the **Applies to** scope.
3. Draft the Governance section: amendment process, conflict resolution, enforcement points. Default amendment process: "Open a PR that edits `<constitution path>` and includes a Sync Impact Report at the top. Two maintainer reviews required for MAJOR; one for MINOR / PATCH."
4. Emit the Sync Impact Report HTML comment with `Version change: (new) -> 1.0.0`, ratified date = today, list of new principles, list of templates requiring updates (typically `catalog/templates/spec-template.md`, `catalog/commands/plan.md`).
5. Write the file. Validate: ISO dates, no leftover `[ALL_CAPS_IDENTIFIER]` placeholders, principle IDs are unique and monotonic.

### Amending an existing constitution

1. Read the existing constitution. Identify which principles, sections, or governance rules are changing.
2. Classify the change per SemVer rules:
    - Removed or redefined principle -> MAJOR.
    - Added principle or grown section -> MINOR.
    - Wording clarification -> PATCH.
3. Increment the version per the classification. Update `Last Amended` to today; do NOT change `Ratified`.
4. Apply the edits in place.
5. **Propagation check**: read every file that references the constitution and verify it is still consistent with the amended content. The default propagation list is:
    - `catalog/commands/plan.md` (Constitution Check section template).
    - `catalog/templates/spec-template.md` once Phase 4 of the adoption-spec-kit plan ships it.
    - Any plan under `docs/<version>/plans/` that explicitly cites a principle ID.
    - Any ADR under `docs/<version>/adr-*.md` that cites a principle ID.
6. Emit the Sync Impact Report at the top of the constitution file. List which downstream artifacts need a follow-up edit (do not auto-edit them in this same operation - surface the list and let the user decide).
7. Write the file.

### Running a Constitution Check on a plan

This is invoked from `/generate-plan` and from `/analyze-spec`; it is not a standalone interactive flow. Inputs: a plan or spec path. Outputs: a PASS / FAIL / N/A verdict per MUST principle, with a one-sentence justification per principle. Behavior:

- For each MUST principle in `docs/<version>/constitution.md`, scan the plan or spec for explicit or implicit violations.
- A principle PASSES when the plan / spec is silent about it (no violation surfaces) or explicitly aligns with it.
- A principle FAILS when the plan / spec explicitly violates it or proposes work the principle prohibits.
- A principle is N/A when it does not apply to the scope of this plan / spec (e.g., a UX principle on a backend-only refactor).
- If the constitution file does not exist, emit: "No constitution file found at `docs/<version>/constitution.md` - skipping check. Recommend running `/constitution` to establish project principles." This is informational, not blocking.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We already have CLAUDE.md / AGENTS.md - we don't need a constitution" | Those files instruct AI tools how to behave inside the repo. A constitution declares what the project itself must be - principles that bind humans, AIs, and downstream automation alike. The two coexist; they are not substitutes. |
| "Principles are obvious - we don't need to write them down" | Obvious-to-you is not the same as obvious-to-the-next-contributor or to an AI agent reading the repo cold. The Constitution Check gate in `/generate-plan` can only enforce written rules. Unwritten principles drift. |
| "This is too formal - we're a small project" | A 5-principle constitution with a one-line statement per principle fits on half a page. The formality is in the discipline of forcing yourself to name what is non-negotiable, not in the document length. |
| "We can amend it any time, so version-tagging is overkill" | Without versioning, downstream plans that cite principles cannot tell whether they are aligned with the current version or a stale one. The Sync Impact Report makes amendment side-effects visible. |
| "Just add the rule to CLAUDE.md instead" | CLAUDE.md grows monotonically with operational guidance for AI tools. A constitutional principle is a different shape: it is enforceable, citable, and version-tracked. Mixing them buries the project's invariants in instructions for one specific tool. |
| "I'll just write 8 principles instead of triaging - more is better" | Long lists of principles dilute each one. The constitution loses force as a gate when every plan trivially passes. Aim for 3-7 principles; everything else belongs in skills, rules, or ADRs. |

## Verification

- [ ] `docs/<version>/constitution.md` (or `CONSTITUTION.md` at root) exists and parses as valid Markdown.
- [ ] Header block contains all four fields: `Project`, `Version`, `Ratified`, `Last Amended`.
- [ ] Sync Impact Report HTML comment is the very first content in the file (above the `# Project Constitution` H1).
- [ ] Sync Impact Report fields are populated: `Version change`, `Modified principles`, `Added sections`, `Removed sections`, `Templates / commands requiring updates`.
- [ ] Each principle has all three subsections: `Statement`, `Rationale`, `Applies to`.
- [ ] Ratified and Last Amended dates are ISO format `YYYY-MM-DD`.
- [ ] No `[ALL_CAPS_IDENTIFIER]` template placeholders remain in the file.
- [ ] At most 3 `[NEEDS CLARIFICATION: ...]` markers are present; markers are prioritized per `scope > security/privacy > UX > technical`.
- [ ] Version increment matches the change classification (MAJOR / MINOR / PATCH per the SemVer rules above).
- [ ] The propagation check has been run; downstream artifacts requiring follow-up are listed in the Sync Impact Report.

## Related Skills

- `[[spec-driven-development]]` - specs cite the constitution; the Constitution Check gate in `/generate-plan` aligns plans with the constitution.
- `[[architecture-decision-record]]` - ADRs record one decision; the constitution records principles that bind all decisions.
- `[[implementation-plan]]` - emits the Constitution Check + Complexity Tracking sections that reference this skill's output.
- `[[ambiguity-detector]]` - flags ambiguity in principle statements and in spec text that should align with principles.
- `[[idea-refine]]` - refining a vague idea into a concrete problem statement is the precursor to writing principles that bound it.
- `[[known-gaps-tracker]]` - constitution violations that the user opts to bypass with "Proceed anyway" land in `known-gaps.md` as `QG-*` items.
