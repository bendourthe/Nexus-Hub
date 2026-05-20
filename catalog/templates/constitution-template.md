<!--
SYNC IMPACT REPORT (generated [YYYY-MM-DD])
Version change: [(new) or X.Y.Z] -> [X.Y.Z] ([MAJOR|MINOR|PATCH]; [one-line summary])
Modified principles: [list of titles, or "none"]
Added sections: [list, or "none"]
Removed sections: [list, or "none"]
Templates / commands requiring updates: [list of file paths, or "none"]
-->

# Project Constitution

**Project**: [PROJECT_NAME]
**Version**: [X.Y.Z]
**Ratified**: [YYYY-MM-DD]
**Last Amended**: [YYYY-MM-DD]

## Preamble

[One paragraph stating the constitution's purpose and authority. Cite which downstream artifacts are bound by it - typically: every plan under `docs/<version>/plans/`, every spec under `docs/<version>/specs/` or `specs/<NNN>-*/`, every ADR, every code review, every release. Make the binding scope explicit so downstream tooling (Constitution Check gates, propagation checks) can be unambiguous about which artifacts it must inspect.]

## Principles

### 1. [PRINCIPLE_1_TITLE]

**Statement**: [One-sentence MUST or SHOULD declaration. Lead with the modal verb so the binding strength is unambiguous. Example: "All code merged to main MUST pass the project's lint, unit-test, and integration-test gates before merge."]

**Rationale**: [Why this principle exists - the concrete failure mode it prevents. Cite a past incident or class of incident when possible.]

**Applies to**: [The downstream artifacts this principle constrains - e.g., "every PR to main", "every plan under docs/<version>/plans/", "every release tagged in CHANGELOG.md".]

### 2. [PRINCIPLE_2_TITLE]

**Statement**: [...]

**Rationale**: [...]

**Applies to**: [...]

### 3. [PRINCIPLE_3_TITLE]

**Statement**: [...]

**Rationale**: [...]

**Applies to**: [...]

<!-- Add or remove principle sections as needed. Target 3-7 principles. Beyond 7, principles dilute and the constitution loses force as a gate. -->

## Section 2: Operational Standards (Optional)

[Use this section for operationally-binding rules that are not high enough abstraction to be principles, but that should still be ratified at the constitutional level. Examples: required code-review approvers, mandatory CI gates, observability standards. Remove this section entirely if not used - do not leave it as "N/A".]

## Section 3: Quality Bars (Optional)

[Use this section for measurable quality bars that bind releases - e.g., "minimum 80% line coverage on `src/`", "zero known criticals in dependency CVE scan", "P95 latency below 200ms in staging benchmarks". Remove this section entirely if not used.]

## Governance

- **Amendment process**: [How principles get added, removed, or redefined. Default: open a PR that edits this file and includes a Sync Impact Report at the top. Two maintainer reviews required for MAJOR; one for MINOR / PATCH.]
- **Conflict resolution**: [What happens when two principles appear to conflict. Default: the lower-numbered principle takes precedence; if that is intolerable, an amendment must redefine or remove one of them.]
- **Enforcement**: [Which commands or checks enforce the constitution. Default: `/generate-plan` emits a Constitution Check section that must pass before Phase 0 research and re-check after Phase 1 design; `/analyze-spec` runs a constitution-alignment pass; code-review checklists reference principle IDs.]

## Versioning

Version increments follow SemVer applied to principles:

- **MAJOR**: a principle is removed or its meaning is redefined in a backwards-incompatible way. Downstream plans that cited the principle by ID must be reviewed and possibly amended.
- **MINOR**: a principle is added or a section grows non-incompatibly. Downstream plans that did not cite the new principle continue to apply unchanged.
- **PATCH**: wording is clarified; no semantic change. Downstream plans are unaffected.

`Ratified` is set once at first adoption and never changes. `Last Amended` updates on every edit.
