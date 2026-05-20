---
description: Author or amend the project constitution at docs/<version>/constitution.md (or CONSTITUTION.md). Drives the project-constitution skill end-to-end - placeholder collection, draft, propagation check, Sync Impact Report, and write. Use to ratify principles, declare MUST / SHOULD rules, or amend an existing constitution.
---
# Constitution

Author or amend the project's constitution - the versioned governance document that declares the MUST / SHOULD principles every plan, spec, ADR, and implementation in the project must align with. Distinct from CLAUDE.md / AGENTS.md (agent-instructions for AI tools), the constitution is project-governance for humans and machines alike.

This command drives the `project-constitution` skill end-to-end. It collects placeholder values from the user, drafts the constitution content, runs the propagation checklist, emits a Sync Impact Report, validates the file, and writes it.

## How to Run This Command

- `/constitution` - interactive author or amend, depending on whether a constitution file already exists.
- `/constitution amend` - explicit amend mode (skips the "no file found" branch and refuses to start from scratch).
- `/constitution check <plan-path>` - shorthand for running the Constitution Check gate against an existing plan file. Read-only.

If a constitution file already exists at `docs/<version>/constitution.md` (or `CONSTITUTION.md` at the repo root), the command enters amend mode automatically. If neither file exists, the command enters author mode.

---

## Step 1: Resolve Constitution Location

1. Detect the current version from the most recent git tag, `CHANGELOG.md` heading, or root version file. Normalize to the `v` prefix form (e.g., `v2.1.0`).
2. Check for an existing constitution in this priority order:
    1. `docs/<version>/constitution.md`
    2. Any older `docs/v*/constitution.md` (use the most recent version where the file exists).
    3. `CONSTITUTION.md` at the repo root.
3. Report the detected location (or "no constitution file found") and confirm with the user before proceeding.

**Default for new constitutions**: `docs/<version>/constitution.md`. This aligns with Nexus-Hub's versioned-docs convention. Offer `CONSTITUTION.md` at root only if the user prefers one canonical path.

---

## Step 2: Collect or Derive Placeholder Values

### Author mode (no existing file)

Ask the user the following four questions, one at a time:

1. **Project name** - the name that appears in the constitution header. Default: derive from the repo's `README.md` H1 or the root directory name. Confirm with the user.
2. **Principles** - "Name 3-7 principles your project must follow. For each one, give me a one-sentence statement, the rationale (the failure mode it prevents), and what it applies to (which artifacts / scopes are bound by it)."
3. **Governance** - "How should principles be amended? Default: PR with Sync Impact Report at the top; two maintainer reviews for MAJOR, one for MINOR / PATCH. Accept default, or describe your own process."
4. **Enforcement points** - "Which commands or checks should enforce the constitution? Default: `/generate-plan` Constitution Check gate, `/analyze-spec` constitution-alignment pass."

### Amend mode (file exists)

1. Read the existing constitution. Display the current version, principle list (titles only), and last-amended date.
2. Ask the user: "What are you changing? Multi-select: (A) Add a principle. (B) Remove a principle. (C) Redefine an existing principle. (D) Clarify wording without changing meaning. (E) Update the governance section. (F) Update the preamble."
3. For each selected change, collect the specifics (which principle, the new statement / rationale / applies-to, etc.).
4. Classify the overall change per SemVer rules:
    - MAJOR: any removal or redefinition.
    - MINOR: any addition (without removals or redefinitions).
    - PATCH: clarifications only.
5. Compute the new version. Confirm with the user before proceeding.

---

## Step 3: Draft the Constitution

Use the template at `catalog/templates/constitution-template.md` as the skeleton. Replace `[ALL_CAPS_IDENTIFIER]` placeholders with the collected values. For amend mode, edit the existing file in place.

Required content (validated in Step 5):

- Sync Impact Report HTML comment at the top (see Step 4 - written after the propagation check completes).
- `# Project Constitution` H1.
- Header block with `Project`, `Version`, `Ratified`, `Last Amended`.
- `## Preamble`.
- `## Principles` with numbered subsections (`### 1. <Title>`, ...), each having `**Statement**`, `**Rationale**`, `**Applies to**`.
- `## Governance` with amendment process, conflict resolution, enforcement.
- `## Versioning` explaining the MAJOR / MINOR / PATCH rules.

Do NOT write the file yet - the Sync Impact Report is generated in Step 4 after the propagation check.

---

## Step 4: Propagation Check + Sync Impact Report

1. Build the propagation candidate list:
    - `catalog/commands/generate-plan.md` (Constitution Check section template).
    - `catalog/templates/spec-template.md` if it exists (Phase 4 of the adoption-spec-kit plan ships it).
    - `catalog/commands/analyze-spec.md` if it exists (Phase 3).
    - Any plan under `docs/<version>/plans/` that contains the literal string "Constitution Check".
    - Any ADR under `docs/<version>/adr-*.md`.
2. For each candidate file, read it and check whether the constitution changes affect it. Specifically:
    - A removed or redefined principle invalidates any plan / ADR section that cites it by ID.
    - An added principle adds a new line to the Constitution Check gate template (informational only).
    - A wording clarification on a cited principle requires a follow-up edit on the citing file.
3. Compose the Sync Impact Report as an HTML comment with these fields:

    ```html
    <!--
    SYNC IMPACT REPORT (generated YYYY-MM-DD)
    Version change: <old> -> <new> (<MAJOR|MINOR|PATCH>; <one-line summary>)
    Modified principles: <list of titles, or "none">
    Added sections: <list, or "none">
    Removed sections: <list, or "none">
    Templates / commands requiring updates: <list of file paths, or "none">
    -->
    ```

4. Prepend the Sync Impact Report to the draft as the very first content (above the `# Project Constitution` H1).

---

## Step 5: Validate

Before writing, confirm:

- Header block has all four fields populated with non-placeholder values.
- All `Ratified` and `Last Amended` dates are ISO format `YYYY-MM-DD`.
- No `[ALL_CAPS_IDENTIFIER]` template placeholders remain anywhere in the file.
- Every `### <N>. <Title>` principle subsection has all three of `Statement`, `Rationale`, `Applies to`.
- At most 3 `[NEEDS CLARIFICATION: ...]` markers are present, prioritized per `scope > security/privacy > UX > technical`.
- The version increment in the Sync Impact Report matches the change classification (MAJOR / MINOR / PATCH per the SemVer rules in the skill body).

If any check fails, surface the problem to the user and offer to fix it before writing.

---

## Step 6: Write

1. Write the file to the resolved path from Step 1.
2. Confirm the write with the user and print the path.
3. If the Sync Impact Report listed downstream artifacts requiring updates, list them again at the end with the instruction: "These files reference the constitution and may need follow-up edits. Do not auto-edit them in this operation; surface the list so you can review them next."

---

## Step 7: Done

Report:

```
Constitution written to <path>.

Version: <X.Y.Z>
Ratified: <YYYY-MM-DD>
Last Amended: <YYYY-MM-DD>
Principles: N

Downstream artifacts to review:
- <file1>
- <file2>
```

Recommend next command:

- After the first ratification: run `/generate-plan` next - the new plan will emit a Constitution Check gate against this file.
- After an amendment: review each downstream artifact in the Sync Impact Report's "Templates / commands requiring updates" list.

---

## Constitution Check shorthand

`/constitution check <plan-path>` runs the Constitution Check gate from the `project-constitution` skill body against an existing plan or spec file. It is read-only - it does not modify the constitution or the plan. Output is the PASS / FAIL / N/A verdict per MUST principle with a one-sentence justification, plus an overall recommendation (the plan is aligned, the plan has violations that must be justified in a Complexity Tracking table, or the constitution itself may need to be amended to reflect intentional scope expansion).
