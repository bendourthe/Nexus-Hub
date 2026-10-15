---
name: org-standards-authoring
description: "Guide an organization through collecting, budgeting, structuring, validating, and distributing a Nexus-Hub organization knowledge bundle. Use whenever the user says \"connect our company standards\", \"organization coding standards\", \"internal conventions\", \"company style guide\", \"org knowledge\", or \"team standards for the AI\". SKIP: single-project constitution authoring (use project-constitution), platform permission policy (use agent-access-policy), or writing the standards content itself from scratch (use writing-editing or technical-writer). Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
summary_l0: "Build distributable organization standards with canonical release records"
overview_l1: "Guides an organization through inventorying existing standards, placing a concise always-on core under 200 lines, separating per-language rules from on-demand references, authoring org.json, validating the bundle, and distributing it from a git repository or shared directory. It reuses project-constitution vocabulary for binding scope, Applies to statements, and conflict resolution, while keeping organization content outside the company-neutral Nexus-Hub catalog. It also explains when to escalate advisory projections to documented platform-native controls without claiming cross-platform enforcement. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Organization Standards Authoring

Turn an organization's existing coding, safety, delivery, testing, naming, documentation, and branching standards into a validated Nexus-Hub organization knowledge bundle. The workflow organizes content the organization already owns; it does not invent policy or treat ordinary agent instructions as enforcement.

The bundle itself is living organization guidance and stays outside release buckets. Version-bound validation or distribution records use `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`; closed snapshots use `docs/archives/`.

## When to Use This Skill

- When a user asks to "connect our company standards" or make existing internal guidance available to AI coding assistants.
- When a team wants to organize organization coding standards, internal conventions, a company style guide, org knowledge, or team standards for the AI.
- When an existing collection of standards is too large or inconsistent to load safely as one always-on document.
- When a team needs a valid `org.json`, a predictable bundle layout, or a git-backed distribution workflow for Nexus-Hub.
- When a connected bundle needs to be reviewed for context budget, precedence clarity, or platform-native enforcement escalation.

Do not use this skill for a single project's constitution; use `[[project-constitution]]`. Do not use it to define platform permissions; use `[[agent-access-policy]]`. Do not write missing company policy from scratch under this workflow; use `[[writing-editing]]` or `[[technical-writer]]` with an authorized policy owner.

## Instructions

1. Inventory the organization's existing documents before creating bundle files.

   Record the owner, current source, intended audience, binding strength, applicable languages or paths, and last review date for each document. Include coding standards, safety rules, CI/CD frameworks, test requirements, naming conventions, documentation style, and branching or release rules. Mark contradictions and missing owners for human resolution; do not reconcile policy by guessing.

2. Classify each document into one of three loading tiers.

   - **Always-on core**: organization-wide rules that every task needs. Keep the combined core below 200 lines because always-loaded content competes with repository instructions and Codex may truncate the combined instruction chain at 32 KiB.
   - **Per-language or path-scoped rules**: guidance that applies only to a language, framework, or path. Mirror the Nexus-Hub convention `catalog/rules/<lang>/<topic>.md` inside the bundle's `rules/` directory, such as `rules/python/testing.md`.
   - **On-demand references**: detailed frameworks, examples, checklists, and explanations that the agent should read only when relevant. Place these under `references/` and link to them from the core or a scoped rule.

   If the proposed core exceeds 200 lines, move examples and domain-specific detail down a tier. Do not compress binding rules until their meaning becomes ambiguous.

3. Create the bundle layout.

   ```text
   organization-standards/
   |-- org.json
   |-- core.md
   |-- rules/
   |   |-- python/
   |   |   `-- testing.md
   |   `-- typescript/
   |       `-- style.md
   `-- references/
       |-- delivery-framework.md
       `-- security-review.md
   ```

   Organization content must remain outside the Nexus-Hub `catalog/`; the connection projects it into supported platform surfaces without making the upstream catalog company-specific.

4. Author the always-on core with explicit authority and conflict language.

   Reuse the vocabulary in `catalog/templates/constitution-template.md`: state the binding scope, give each rule an **Applies to** statement, and define conflict resolution. Identify whether each statement is a MUST, SHOULD, or informational reference. State what happens when organization guidance conflicts with project or platform instructions; do not assume undocumented precedence.

5. Author `org.json` against `configs/org-bundle.schema.json`.

   ```json
   {
     "schema_version": 1,
     "org_name": "Example Company",
     "core": "core.md",
     "rules_dir": "rules/",
     "references_dir": "references/",
     "precedence_statement": "Organization standards take precedence over generic Nexus-Hub guidance; project-specific requirements remain binding where they are more restrictive."
   }
   ```

   Use only relative paths contained by the bundle. `schema_version`, `org_name`, and `core` are required. Keep the precedence statement specific enough that an agent can resolve an actual conflict without inventing a policy hierarchy.

6. Review the bundle before connecting it.

   Confirm every referenced file exists, the core stays below 200 lines, Markdown files are readable independently, rule paths match their intended language or scope, and no secrets or internal credentials are present. Obtain approval from the relevant policy owners for every binding statement.

7. Validate and connect the bundle.

   ```powershell
   nexus-hub org connect C:\path\to\organization-standards
   nexus-hub org status
   ```

   ```bash
   nexus-hub org connect /path/to/organization-standards
   nexus-hub org status
   ```

   `nexus-hub org connect` validates the bundle and refuses an invalid manifest or unsafe path. Treat a refusal as a contract error to fix; do not bypass validation or hand-edit the saved connection state.

8. Choose a distribution channel.

   Prefer a version-controlled git repository so changes are reviewed, attributable, and synchronized through `nexus-hub org sync`. A shared directory is supported when the organization already governs it and every target machine can access the same path. Pin access to the intended repository or directory; Nexus-Hub does not upload organization content.

9. Verify projection and maintenance behavior.

   Run `nexus-hub org status` after connection, synchronization, and Nexus-Hub upgrades. Review the reported posture for each platform. Use `nexus-hub org sync` after the source changes, and keep the core budget and ownership review in the organization's change process.

10. Escalate only when advisory instructions are insufficient.

    Read [`references/enforcement-escalation.md`](references/enforcement-escalation.md) before recommending managed CLAUDE.md, Cursor Team Rules, or GitHub Copilot organization instructions. Those mechanisms are platform-specific and have different precedence semantics. Describe the documented option and its authority boundary; do not claim Nexus-Hub generated or enforced it.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We can put every policy in core.md so the agent always sees it." | Oversized always-on content competes with repository context and can be truncated, leaving later safety or delivery rules silently absent. Keep the core under 200 lines and move scoped detail into rules or references. |
| "The standards are in a shared drive, so ownership is obvious." | Shared storage does not identify who may approve binding changes; an unowned document can project obsolete or contradictory instructions to every connected project. Record an owner and review date during inventory. |
| "Calling a rule MUST makes it enforced on every platform." | Prose remains agent context. Without a documented managed control or blocking hook, the agent can deprioritize or conflict with it; report the posture honestly and use the escalation reference when enforcement is required. |
| "The precedence order is intuitive and does not need to be written." | Claude, Cursor, and Copilot document different precedence behavior; an unstated conflict can produce arbitrary selection. Put explicit conflict resolution in the core and `precedence_statement`. |
| "We should copy the company standards into the Nexus-Hub catalog." | Catalog content is distributed to every user and must remain company-neutral. Keep organization material in its own directory or repository and connect it through the org bundle contract. |

## Verification

- [ ] `org.json` validates through `nexus-hub org connect` without bypassing schema or path checks.
- [ ] The always-on core contains fewer than 200 lines and states binding scope, Applies to language, and conflict resolution.
- [ ] Every per-language or path-scoped rule is under `rules/` and every detailed document intended for on-demand loading is under `references/`.
- [ ] Every binding document has an identified owner and review date, and contradictions have been resolved by an authorized human.
- [ ] `nexus-hub org status` reports the connection and platform postures after connection or synchronization.
- [ ] The selected git repository or shared directory is accessible to intended users and contains no credentials or secrets.
- [ ] Any platform-native enforcement recommendation is supported by `references/enforcement-escalation.md` and is not presented as Nexus-Hub enforcement.

## Related Skills

- `[[project-constitution]]` - authors governance principles for one project; this skill reuses its authority vocabulary for organization-wide source documents.
- `[[agent-access-policy]]` - configures platform permissions and access controls when organization guidance must be backed by an enforcement boundary.
- `[[writing-editing]]` - edits standards content supplied by authorized owners without changing this bundle workflow.
- `[[technical-writer]]` - turns approved policy decisions into audience-appropriate internal documentation.
- `[[using-nexus-hub]]` - explains the broader Nexus-Hub catalog, command, hook, and installation surfaces.

---

**Version**: 1.0.0
**Last Updated**: August 2026
