---
name: analyze-codebase
description: Produce a clear, structured description of any project directory (software or not) - project type, layout, key modules, dependencies, architecture with diagrams, entry points, testing, and a fast-start onboarding guide - plus a read-only "Project health" block that reports whether git, a version, a branch model, and the baseline docs are in place and offers a /setup handoff when they are not. This is the generic delegate behind /describe. Use whenever the user says "describe this project", "analyze the codebase", "what is this repo", "map this codebase", "help me understand this directory", "give me an overview", "onboard me to this code", or "is this repo set up properly". Read-only by default - it reports and offers, it never mutates. SKIP - explaining a single file or function (answer directly), generating a README (use /update docs), or actually performing the setup it recommends (use /setup). Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Describe project architecture and report canonical release-docs health"
overview_l1: "The generic delegate behind /describe. It produces a structured, twelve-section description of any directory - software or not - covering project type and purpose, directory layout, key modules, dependencies and external services, architecture and data flow (with Mermaid diagrams), entry points and how to run, configuration, testing and quality, a fast-start onboarding guide, and open questions. Immediately after the Executive Summary it emits a read-only Project health block: a binary checklist of whether git is initialized, a version is set (and which), a develop+main branch model is present, and the baseline README/CHANGELOG/DEVLOG and per-version docs tree exist - and when any check fails it offers to hand off to /setup rather than fixing anything itself. The full scope writes docs/<version>/analysis.md; focused scopes (structure/deps/architecture/onboarding) emit just their section. Trigger phrases: describe this project, analyze the codebase, what is this repo, map this codebase, onboard me to this code, is this repo set up properly. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Analyze Codebase

Produce a clear, well-structured description of a project directory so someone who did not write it can understand and be productive in it fast. Works on any directory - a codebase, a documents folder, mixed content - and adapts its sections to what it finds. This is the generic delegate behind `/describe`.

The skill is **read-only**: it reports what it finds and, when governance surfaces are missing, offers a `/setup` handoff. It never creates, moves, or edits project files.

## When to Use This Skill

Use this skill when you need to:

- Understand an unfamiliar or inherited project quickly.
- Map a large codebase's structure, dependencies, and architecture.
- Produce an onboarding guide ("what do I read first, how do I run it").
- Check, without changing anything, whether a repo is set up to Nexus-Hub's governance baseline (git, version, branches, docs).

**Trigger phrases**: "describe this project", "analyze the codebase", "what is this repo", "map this codebase", "help me understand this directory", "give me an overview", "onboard me to this code", "is this repo set up properly".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Explain a single file, function, or error | Answer directly - no full analysis needed |
| Generate or refresh a README | `/update docs` |
| Actually perform the setup this skill recommends | `/setup` (this skill only reports and offers) |
| Deep code review for quality/security | `/review` |

## Detect the project mode first

Before analyzing, detect whether the target is a **software project** (a manifest, source files, or version control present) or a **non-software project** (documents, data, mixed content). State the detected mode. For non-software projects, adapt the sections: replace "dependencies" with "external references / inputs", "architecture" with "how the material is organized and how the parts relate", and "how to run it" with "how to use or navigate it". Skip sections that do not apply rather than inventing them.

## Instructions

### Step 1: Resolve scope and target

Resolve the scope (`full`, `structure`, `deps`, `architecture`, `onboarding`) and the target directory (default: the current directory). `full` runs every section and writes the report file; a focused scope emits only its section(s) inline.

### Step 2: Gather the facts (read-only)

Walk the tree; read the manifest(s), README, CHANGELOG, CI config, and entry points; run read-only git queries (`git rev-parse`, `git tag`, `git branch --list`, `git log -1`). Do not modify anything.

### Step 3: Produce the report

For `full`, produce the twelve-section report below and write it to `docs/<version>/analysis.md` (resolve `<version>` per the `[[docs-layout-refactor]]` Version-directory resolution - canonically `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/analysis.md`). For a focused scope, emit only the mapped section(s) inline and offer to append them to the report file.

### Output Template (full scope - twelve sections)

```markdown
# Project Description - <name> - <YYYY-MM-DD>

**Mode**: software | non-software
**Target**: <path>

## 1. Executive Summary

<2-4 sentences: what this project is, who it is for, current maturity.>

## 2. Project Health

<The read-only checklist below. See "Project health block".>

## 3. Project Type and Purpose

## 4. Directory Structure and Layout

## 5. Key Modules and Components

## 6. Dependencies and External Services

## 7. Architecture and Data Flow

<Include a Mermaid diagram of the main components and their relationships.>

## 8. Entry Points and How to Run

## 9. Configuration and Environment

## 10. Testing and Quality

## 11. Onboarding - Read This First

<Ordered "read these files first, then run this" fast-start path.>

## 12. Open Questions and Risks
```

### Project health block

Immediately after the Executive Summary (section 2), emit this binary checklist. Each item is detect-and-report only:

```markdown
## 2. Project Health

| Surface | Status | Detail |
|---|---|---|
| Git version control | OK / MISSING | repo present? at least one commit? |
| Version number | OK / MISSING | resolved version (tag / CHANGELOG / manifest), or none found |
| Branch model | OK / MISSING | develop + main present? or which model is in use? |
| Baseline docs | OK / MISSING | README / CHANGELOG / DEVLOG present with real content? |
| Per-version docs tree | OK / MISSING | docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/ with plans/ + comparisons/? |
```

When every surface is OK, state "Project health: all governance surfaces present." When ANY surface is MISSING, end the block with an explicit handoff offer, naming the specific gaps:

> Setup needed: <list the MISSING surfaces>. Run `/setup project` to bootstrap them (git init, set v0.1.0, create a develop branch, scaffold the per-version docs tree, and write the baseline docs). This skill is read-only and will not make those changes itself.

Use the same wording for the health block in `/review` so the two commands stay consistent (see `[[git-branching-workflow]]` for the branch-model semantics and `[[setup-project]]` for what the handoff performs).

### Focused-scope mapping

| Scope | Sections emitted |
|---|---|
| `structure` | 4 (layout) + 5 (key modules) |
| `deps` | 6 (dependencies and external services) |
| `architecture` | 7 (architecture and data flow, with the Mermaid diagram) |
| `onboarding` | 8 (entry points and how to run) + 11 (read this first) |

Every scope still emits the Project health block (section 2) - a quick, always-useful signal.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The repo is clearly missing git/version, so I will just initialize it while I am here." | This skill is read-only. Mutating the repo during a description surprises the user and blurs the describe/setup boundary. Report the gap and offer the `/setup` handoff; let the user decide. |
| "The Project health block is redundant with the rest of the description." | It is the one section that gives an at-a-glance go/no-go on whether the project follows the governance baseline, with an actionable next step. The prose sections describe; the health block decides. |
| "I will skip the Mermaid diagram and just describe the architecture in prose." | A diagram makes component relationships graspable in seconds; prose alone forces the reader to reconstruct the graph. Include at least one diagram for the architecture section. |
| "It is a non-software folder, so a code-style analysis does not apply - I will refuse." | Adapt, do not refuse. Map documents/data with the analogous sections (inputs, organization, how to navigate). The goal is always a clear description of an inherited directory. |

## Verification

- [ ] The detected mode (software / non-software) is stated before the description.
- [ ] For `full` scope, the report is written to the resolved `docs/<version>/analysis.md` and contains all twelve sections.
- [ ] The Project health block is present immediately after the Executive Summary and reports every surface as OK or MISSING.
- [ ] When any surface is MISSING, the block ends with the explicit `/setup project` handoff offer naming the specific gaps.
- [ ] No project file was created, moved, or edited (the skill is read-only) - only `docs/<version>/analysis.md` is written, and only in `full` scope.
- [ ] The architecture section includes a Mermaid diagram (software mode).

## Related Skills

- [[setup-project]] -- performs the bootstrap this skill's health block recommends; the two share the same governance surfaces (git, version, branches, docs).
- [[git-branching-workflow]] -- defines the branch-model semantics the health block reports against (develop+main, trunk-based, etc.).
- [[docs-layout-refactor]] -- the Version-directory resolution scheme that determines where `analysis.md` is written.
- `context-analysis` -- the code-review Phase 1 analyzer; `analyze-codebase` is the describe-oriented sibling (onboarding and health), that one is review-oriented (risk and dependency mapping).
- `/update docs` -- turns this read-only description into maintained project documentation.

---

**Version**: 1.0.0
**Last Updated**: July 2026
