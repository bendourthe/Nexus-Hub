# Plan - Nessie + agency-agents adoption (v-next slice)

**Project**: Nexus-Hub
**Version**: v3.4.0
**Slug**: adoption-nessie-and-agency-agents
**Plan Type**: Feature / Enhancement
**Created**: 2026-06-12
**Source report**: [`../comparison-nessie-and-agency-agents.md`](../comparison-nessie-and-agency-agents.md)
**Goal**: Ship the two highest-value, zero-outbound adoptions from the comparison - a local session-distillation "context pack" skill (A1) and Aider + Windsurf platform integrations (A3) - with no new outbound call, dependency, or credential.

## Overview

This plan operationalizes the reverse-engineer-first Adoption Plan from the comparison report. It is deliberately scoped to the v-next slice: **A1** (a new `workflow` skill that distills prior-session digests and solved-problem records into a reusable, deduped, topic-organized context pack the next session, a teammate, and an agent all load) and **A3** (two new `IntegrationBase` subclasses extending Nexus-Hub's platform reach to Aider and Windsurf). Both are `skill-native` / `re-full` per the report's Step 5.4: they introduce zero new outbound calls, dependencies, credentials, or third-party processors. A1 sequences first (skill-native before re-full).

Delivery follows the AGENTS.md installer-aware contract. A1 is auto-distributed (a new skill folder is copied recursively by both installers) but must be registered in the three catalog registries. A3 requires no installer copy-block edit but each subclass must be registered in `scripts/lib/integrations/__init__.py::_register_builtins()`, and the AGENTS.md platform-coverage section + CHANGELOG must be updated. The Reverse-Engineering Attribution Rule applies throughout: implement generically, never name the upstream `agency-agents` repo or `nessielabs.com` in any shipped artifact; provenance lives only in `docs/policy/mcp-reverse-engineering-matrix.md`.

Success is observable: `make validate`, `make lint`, and `make test` are green; the new skill passes the skill-security scan and the orphan-bundle audit; and a dry-run installer run shows the Aider and Windsurf artifacts landing at their expected per-platform paths. Explicitly out of scope and deferred to backlog: A4 (extend `session-query` to Obsidian / exported ChatGPT-Gemini history), A5 (canonical-source -> per-platform transform refactor), and the optional Kimi / Qwen / OpenClaw integrations.

## Constitution Check

*GATE: Must pass before Phase 1 work. Re-check after Phase 1 design.*

No constitution file found at `docs/v3.4.0/constitution.md` - skipping check. Recommend running `/constitution` to establish project principles. This is informational, not blocking. As a proxy, this plan was checked against the AGENTS.md governing rules it must satisfy (MCP Registry Policy reverse-engineer-first, installer-aware distribution, three-registry skill registration, `.ps1` cross-platform parity, ASCII-only Markdown, pushy-description + binary-Verification authoring): all PASS - no rule is violated by either adoption, since both are local and zero-outbound.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Context-pack distillation skill (A1, skill-native) | A new `workflow` skill that turns prior-session digests + solved-problem records into a reusable, deduped, topic-organized context pack; registered in all 3 registries; validated and security-scanned |
| 2 | Aider + Windsurf integrations (A3, re-full) | Two new `IntegrationBase` subclasses registered in `_register_builtins()`; AGENTS.md platform docs + CHANGELOG updated; installer dry-run confirms artifacts land |

---

## Phase 1: Context-pack distillation skill (A1, skill-native)

**Goal**: Add a local, zero-outbound `workflow` skill that distills prior-session context into a persisted, deduped, topic-organized "context pack" artifact that the next session, a teammate, and an agent can all load.
**Prerequisites**: None.
**Stability Gate**: The new `SKILL.md` exists with valid YAML frontmatter; it is registered in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json`; `make validate` passes (JSON integrity + orphan-bundle audit clean); and the skill-security scan returns an install-OK verdict.

### Sub-tasks

#### 1.1 - Design the context-pack artifact and skill scope

**Objective**: Decide the shape of the persisted context pack and the skill's exact boundary against the adjacent skills, before writing prose.

**Prompt**:
> In the Nexus-Hub repo, design (do not yet implement) a new `workflow` skill, working name `context-pack-builder`, that distills prior-session context into a reusable artifact. Read these existing skills first to fix the boundary and avoid overlap: `catalog/skills/workflow/session-query/SKILL.md` (queries local session logs - this skill CONSUMES its digests), `catalog/skills/workflow/session-history/SKILL.md` (writes the current session), `catalog/skills/workflow/solution-knowledge-base/SKILL.md` (captures solved problems), `catalog/skills/ai-development/continuous-learning/SKILL.md` (mints instincts), and `catalog/skills/ai-development/context-engineering/SKILL.md`. Produce: (1) the exact name (confirm `context-pack-builder` or propose better kebab-case), (2) a one-paragraph scope statement that names what it does and what it explicitly does NOT do (it does not query logs - it distills already-gathered digests; it does not upload anything), (3) the on-disk format of the context pack it produces - propose a single committed Markdown artifact (e.g. `docs/context/<topic>.md` or `.nexus/context-pack-<topic>.md`) with a deduped, topic-organized structure (topic, source sessions + timestamps, distilled facts, open questions, links to solutions), and (4) whether a thin deterministic Tier-3 dedupe/merge helper is warranted or whether distillation is purely LLM-driven. Output the design as a short note; make no file edits yet. Constraint: zero new outbound calls, dependencies, or credentials.

---

#### 1.2 - Write SKILL.md (Tier 1 + Tier 2)

**Objective**: Author the skill body following the AGENTS.md SKILL.md contract and three-tier model.

**Prompt**:
> Create `catalog/skills/workflow/context-pack-builder/SKILL.md` (use the name confirmed in 1.1). Follow the AGENTS.md SKILL.md contract exactly: required frontmatter (`name`, `description`, `summary_l0` <=15 words quoted, `overview_l1` <=150 words quoted); a pushy, SKIP-claused `description` listing trigger phrases verbatim ("build a context pack", "distill our sessions", "carry context forward", "give the next session a head start", "shared project context") AND a SKIP clause fencing off look-alikes (SKIP: querying past sessions -> use session-query; capturing one solved problem -> use solution-knowledge-base; writing the current session -> use session-history). Required body sections in order: title + intro, "When to Use This Skill" (with explicit "When NOT to use"), "Instructions" (numbered steps: gather digests from session-query / solutions, distill + dedupe by topic, write the persisted context pack, link related artifacts), "Common Rationalizations" (>=3 rows, each citing a concrete failure mode), "Verification" (binary checklist - observable artifacts: the pack file exists at <path>, topics are deduped, every fact cites a source session + timestamp), "Related Skills" (bidirectional `[[wikilink]]` cross-links to `session-query`, `solution-knowledge-base`, `continuous-learning`, `context-engineering`, `loop-engineering`). Keep the body <=500 lines. ASCII-only Markdown (hyphens, straight quotes, `...`), blank line before/after every list, table, code block, and heading, 4-space nested-list indent. Constraint: the skill instructs the agent to do everything locally - it must NOT introduce any outbound call, dependency, or credential, and it must state that explicitly.

---

#### 1.3 - (Conditional) Add the Tier-3 dedupe/merge helper

**Objective**: If 1.1 concluded a deterministic helper is warranted, ship it under the skill's `scripts/` with `.sh`/`.py` + `.ps1` parity; otherwise skip this sub-task and note why.

**Prompt**:
> Only if sub-task 1.1 decided a deterministic dedupe/merge helper earns its place: add it under `catalog/skills/workflow/context-pack-builder/scripts/` as a stdlib-only, zero-outbound script (e.g. `merge-context-pack.py`) that merges new distilled entries into an existing context pack, deduping by topic + source-session key. Per the AGENTS.md `.ps1` parity rule, ship a `merge-context-pack.ps1` sibling with identical behavior. Reference the script from SKILL.md (the orphan-bundle audit requires every bundled file to be referenced). The script must import no network module and open no connection. If 1.1 decided distillation is purely LLM-driven, skip this sub-task and record one sentence in the plan's session history explaining why no script was added.

---

#### 1.4 - Register the skill in all three catalog registries

**Objective**: Make the skill discoverable per AGENTS.md (a new skill MUST update the three registries).

**Prompt**:
> Register the new `context-pack-builder` skill in the three catalog registries, modeled on an existing `workflow` skill entry (e.g. `loop-engineering`). (1) `data/SKILL_INDEX.md`: add one table row `| context-pack-builder | Workflow | "<summary_l0>" | catalog/skills/workflow/context-pack-builder/SKILL.md |`. (2) `data/skills.json`: add one entry to the `skills` array following the existing schema (name, title, description, long_description, summary_l0, overview_l1, version, author, category=workflow, language, tags, priority, based_on, tools_required, path, file, size, downloads, status, security with structural/integrity/semantic defaults 100/100/95). (3) `data/marketplace.json`: increment the `workflow` category `skill_count`, and increment `total_skills` in `statistics` (and any headline count-prose surface that tracks the catalog total: README, AGENTS.md, the `data/SKILL_INDEX.md` Total label, `data/marketplace.json` plugin description, `.claude-plugin/plugin.json` description - mirror exactly what the v3.3.0 release did for 251 -> 252, now 252 -> 253). Do not hand-edit any other `data/` file. After editing, run `make validate` and confirm JSON integrity passes and `check_version_sync.py` (if it covers counts) is green.

---

#### 1.5 - Testing and Stabilization

**Objective**: Validate and security-scan the new skill; iterate until stable before Phase 2.

**Prompt**:
> Validate the new skill end to end. Run `make validate` (JSON catalog integrity + per-skill orphan-bundle audit - confirm no unreferenced files under the skill's `scripts/`/`references/`/`assets/`), `make lint` (ShellCheck, if a `.sh` helper was added), and `make test` (pytest hook suite). Run the skill-security scan on the new skill and confirm an install-OK verdict. If `make` is not on PATH (a known v3.3.0 local-Windows gap, WN-v33-1), invoke the underlying validators and the scanner directly and note that in the session history. Confirm: frontmatter parses as YAML (the MCP server depends on it), `summary_l0` and `overview_l1` are quoted strings, all `[[wikilink]]` cross-links resolve to real skills (0 dangling), and the description either fits the length norm or is added to `scripts/validate_skills.allowlist.json` per the pushy-description mandate (do NOT shorten a pushy description to pass). Fix any failure and re-run until green. Add an `## [Unreleased]` entry to `CHANGELOG.md` describing the new skill (note: skill-native, zero new outbound call / dependency / credential). Then run `/session` to document Phase 1.

---

### Phase 1 Exit Checklist

- [ ] All sub-tasks completed (1.3 either done with `.ps1` parity or explicitly skipped with a reason)
- [ ] `make validate`, `make lint`, `make test` green (or direct-validator equivalents green, per WN-v33-1)
- [ ] Skill registered in all three registries; catalog total count updated consistently across every prose surface
- [ ] Skill-security scan returns install-OK; orphan-bundle audit clean; 0 dangling wikilinks
- [ ] CHANGELOG `[Unreleased]` entry added
- [ ] No known regressions; session history generated
- [ ] Ready to advance to Phase 2

---

## Phase 2: Aider + Windsurf integrations (A3, re-full)

**Goal**: Extend Nexus-Hub's platform reach to Aider (`CONVENTIONS.md`) and Windsurf (`.windsurfrules`) by adding two `IntegrationBase` subclasses, registered and dry-run-verified.
**Prerequisites**: None (independent of Phase 1; sequenced second per the report's RE-first ordering - skill-native A1 before re-full A3).
**Stability Gate**: Both subclasses are registered in `_register_builtins()`; a dry-run install (`scripts/installer.sh --check` / `--dry-run` and `installer.ps1 -Check`) reports the Aider and Windsurf artifacts at their expected paths with no error; `make lint` and the integration pytest suite are green; AGENTS.md platform-coverage section and CHANGELOG are updated.

### Sub-tasks

#### 2.1 - Study the integration-registry pattern and define the two transforms

**Objective**: Learn the existing subclass pattern and pin down the exact output each new platform needs, before writing code.

**Prompt**:
> In the Nexus-Hub repo, read `scripts/lib/integrations/__init__.py` (specifically `_register_builtins()`), `scripts/lib/integrations/runner.py`, `scripts/lib/integrations/result.py` (the `WriteResult` contract), and two representative existing subclasses - `scripts/lib/integrations/cursor.py` (does a format transform to `.mdc` + writes `.cursor/rules`) and `scripts/lib/integrations/opencode.py` (behavioral-guardrails via `AGENTS.md`). Then define, as a short design note (no code yet), the transform for each new platform: (1) Aider -> a single consolidated `CONVENTIONS.md` (project-root behavioral-guidance file) carrying the Nexus-Hub instruction content + `{{SKILL_INDEX}}` block; (2) Windsurf -> a `.windsurfrules` file with the same content adapted to Windsurf's rules format. For each, specify: global vs project-local target path, what content is emitted, and which existing subclass is the closest model to copy. Constraint: pure local file emission, zero outbound calls or credentials. Apply the Reverse-Engineering Attribution Rule - do not name any upstream repo in the code, comments, or docs; use generic descriptive names.

---

#### 2.2 - Implement and register the Aider integration

**Objective**: Add `aider.py` and wire it into the registry.

**Prompt**:
> Create `scripts/lib/integrations/aider.py` as an `IntegrationBase` subclass modeled on the closest existing subclass identified in 2.1, emitting a consolidated `CONVENTIONS.md` with the Nexus-Hub instruction content and the `{{SKILL_INDEX}}` block. Then register it in `scripts/lib/integrations/__init__.py::_register_builtins()` (this is the MANDATORY registration step - the file copy alone does nothing without it). Follow the existing subclasses' conventions for path resolution, skip-with-note behavior when the tool is not detected, and the `WriteResult` return contract. ASCII-only; do not name any upstream project in code or comments. Do a quick local dry-run (`scripts/installer.sh --check`) and confirm the Aider integration runs without error.

---

#### 2.3 - Implement and register the Windsurf integration

**Objective**: Add `windsurf.py` and wire it into the registry.

**Prompt**:
> Create `scripts/lib/integrations/windsurf.py` as an `IntegrationBase` subclass emitting a `.windsurfrules` file with the Nexus-Hub instruction content adapted to Windsurf's rules format, modeled on the closest existing subclass from 2.1. Register it in `scripts/lib/integrations/__init__.py::_register_builtins()`. Match existing conventions for path resolution, not-detected skip-with-note, and the `WriteResult` contract. ASCII-only; no upstream attribution in code or comments. Dry-run (`scripts/installer.sh --check`) and confirm it runs without error.

---

#### 2.4 - Update platform-coverage docs, the RE matrix, and the CHANGELOG

**Objective**: Keep the documented platform coverage and the reverse-engineering provenance in sync with the new integrations.

**Prompt**:
> Update the documentation surfaces for the two new integrations. (1) `AGENTS.md`: in the "Platform coverage caveats" / distribution-channels section, add Aider and Windsurf to the extended-platform set and note the surface each gets (Aider `CONVENTIONS.md`, Windsurf `.windsurfrules` - behavioral-guardrails surfaces, not slash-command surfaces). (2) `docs/policy/mcp-reverse-engineering-matrix.md`: add a row for this adoption recording the provenance and the decision-tree classification (`re-full`, local file transform, zero outbound) - this matrix row is the ONLY place the upstream source may be named, per the Reverse-Engineering Attribution Rule. (3) `CHANGELOG.md` `[Unreleased]`: add an "Added" entry for the Aider and Windsurf integrations, explicitly noting zero new outbound call / dependency / credential. ASCII-only across all three.

---

#### 2.5 - Testing and Stabilization

**Objective**: Verify both integrations via dry-run and the test suite; iterate until stable.

**Prompt**:
> Validate both new integrations. (1) Run a dry-run install into a throwaway directory using both installers (`scripts/installer.sh --check` and `--dry-run`; `scripts/installer.ps1 -Check`) and confirm the Aider `CONVENTIONS.md` and Windsurf `.windsurfrules` artifacts land at their expected paths with no error and that not-detected tools skip cleanly with a note. (2) Run `make lint` (ShellCheck) and the integration pytest suite (`make test`); add or extend tests under `catalog/hooks/tests/` (or the integration test module) asserting each new subclass is registered in `_register_builtins()` and produces its expected output - model on the existing installer-smoke / integration tests. (3) Re-confirm the carried-forward v3.3.0 gap WN-v33-1: ensure CI `validate` and `scan` are green on the ubuntu runner (no code change expected). If `make` is not on PATH locally, invoke the validators directly and note it. Fix any failure and re-run until green. Then run `/session` to document Phase 2. As this is the plan's final phase, `/implement` will trigger release-readiness on completion.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - Constitution Check has no FAIL bullets) | | |

---

### Phase 2 Exit Checklist

- [ ] Both subclasses implemented and registered in `_register_builtins()`
- [ ] Dry-run install confirms Aider + Windsurf artifacts land at expected paths; not-detected tools skip cleanly
- [ ] `make lint` and integration pytest suite green (or direct equivalents, per WN-v33-1); CI `validate`/`scan` green on ubuntu runner
- [ ] AGENTS.md platform-coverage section, RE matrix row, and CHANGELOG `[Unreleased]` updated
- [ ] No upstream repo named in any shipped artifact (attribution only in the RE matrix)
- [ ] No known regressions; session history generated
- [ ] Release readiness run (final phase)

---

## Out of Scope / Deferred (backlog)

Carried from the comparison report's Adoption Plan; not in this version's slice. The next `/plan` ingests these via the known-gaps file.

| ID | Item | RE class | Why deferred |
|---|---|---|---|
| A4 (N-A) | Extend `session-query` discovery to Obsidian vaults + exported ChatGPT/Gemini history (local) | `re-full` | Valuable but independent; A1 delivers the higher-value distillation capability first. Edits the existing zero-outbound extractor - schedule after A1 proves the context-pack format. |
| A3-ext | Optional Kimi / Qwen / OpenClaw integrations | `re-full` | Lower-adoption platforms than Aider/Windsurf; same subclass pattern, add once the two primary ones are proven. |
| A5 (C2) | Generalize bespoke per-subclass transforms into a declarative canonical -> per-platform table | `re-full` | High-effort architectural refactor with no standalone user value; only worth it if platform count keeps growing. |
| A2 (C3) | Add "Success Metrics" / "Deliverable Template" sections to select `catalog/agents/` definitions | `skill-native` | Low-medium value authoring; do opportunistically, not as a dedicated phase. |

Permanently excluded (from the report's NOT-recommended list, with grounds): Nessie the product / any Nessie API (`drop-outright` - closed-source vendor + data egress; MCP Registry Policy Hard-No), personality/vibe theater + business-division breadth (out of scope - identity conflict), multilingual catalog (style-guide conflict).

## Carried-forward known gaps (from v3.3.0)

- **WN-v33-1** (Low): confirm CI `validate` and `scan` are green on the ubuntu runner; locally, `make` may not be on PATH, so invoke validators/scanner directly. Folded into 1.5 and 2.5.
- **WN-v33-2** (Low): two benign pre-existing global-audit warnings (the `demo-capture` orphan `.pyc` is local-only/gitignored; `git-branching-workflow` has a 169-word `overview_l1` soft warning). Optional one-line reword of that overview can be picked up opportunistically; no gate impact.
