# Plan - Nessie + agency-agents adoption (expanded slice)

**Project**: Nexus-Hub
**Version**: v3.4.0
**Slug**: adoption-nessie-and-agency-agents
**Plan Type**: Feature / Enhancement
**Created**: 2026-06-12
**Source report**: [`../comparison-nessie-and-agency-agents.md`](../comparison-nessie-and-agency-agents.md)
**Goal**: Ship the zero-outbound adoptions from the comparison - a local session-distillation "context pack" skill (A1), Aider + Windsurf platform integrations (A3), extended `session-query` discovery (A4), the optional Kimi / Qwen / OpenClaw integrations (A3-ext), and selective agent-body enrichment (A2) - with no new outbound call, dependency, or credential.

## Overview

This plan operationalizes the reverse-engineer-first Adoption Plan from the comparison report across five phases: **A1** (a new `workflow` skill that distills prior-session digests and solved-problem records into a reusable, deduped, topic-organized context pack the next session, a teammate, and an agent all load), **A3** (two new `IntegrationBase` subclasses extending Nexus-Hub's platform reach to Aider and Windsurf), **A4** (extend `session-query` discovery to Obsidian vaults and exported ChatGPT/Gemini history, locally), **A3-ext** (three further integration subclasses for Kimi, Qwen, and OpenClaw, extending the Phase 2 pattern), and **A2** (selective "Success Metrics" / "Deliverable Template" enrichment of existing agent definitions). Every item is `skill-native` or `re-full` per the report's Step 5.4: each introduces zero new outbound calls, dependencies, credentials, or third-party processors. Ordering keeps the highest-value, lowest-risk work first - the skill-native A1, then the re-full integration and extractor work (A3, A4, A3-ext) - with the opportunistic skill-native A2 sequenced last (a deliberate deviation from strict skill-native-first ordering) because it is the lowest-value, edits-existing-files item.

Delivery follows the AGENTS.md installer-aware contract. A1 is auto-distributed (a new skill folder is copied recursively by both installers) but must be registered in the three catalog registries. A3 requires no installer copy-block edit but each subclass must be registered in `scripts/lib/integrations/__init__.py::_register_builtins()`, and the AGENTS.md platform-coverage section + CHANGELOG must be updated. The Reverse-Engineering Attribution Rule applies throughout: implement generically, never name the upstream `agency-agents` repo or `nessielabs.com` in any shipped artifact; provenance lives only in `docs/policy/mcp-reverse-engineering-matrix.md`.

Success is observable: `make validate`, `make lint`, and `make test` are green; the new skill passes the skill-security scan and the orphan-bundle audit; and a dry-run installer run shows the Aider, Windsurf, Kimi, Qwen, and OpenClaw artifacts landing at their expected per-platform paths. Explicitly out of scope and deferred to backlog: A5 (canonical-source -> per-platform transform refactor), which remains a high-effort architectural refactor with no standalone user value.

## Constitution Check

*GATE: Must pass before Phase 1 work. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.4/constitution.md` - skipping check. Recommend running `/constitution` to establish project principles. This is informational, not blocking. As a proxy, this plan was checked against the AGENTS.md governing rules it must satisfy (MCP Registry Policy reverse-engineer-first, installer-aware distribution, three-registry skill registration, `.ps1` cross-platform parity, ASCII-only Markdown, pushy-description + binary-Verification authoring): all PASS - no rule is violated by either adoption, since both are local and zero-outbound.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Context-pack distillation skill (A1, skill-native) | A new `workflow` skill that turns prior-session digests + solved-problem records into a reusable, deduped, topic-organized context pack; registered in all 3 registries; validated and security-scanned |
| 2 | Aider + Windsurf integrations (A3, re-full) | Two new `IntegrationBase` subclasses registered in `_register_builtins()`; AGENTS.md platform docs + CHANGELOG updated; installer dry-run confirms artifacts land |
| 3 | Extend session-query to Obsidian + exported history (A4, re-full) | `session-query` discovers and parses Obsidian vaults and exported ChatGPT/Gemini history locally; zero-outbound invariant preserved; `.ps1` parity |
| 4 | Optional Kimi / Qwen / OpenClaw integrations (A3-ext, re-full) | Three more `IntegrationBase` subclasses registered and dry-run-verified, extending the Phase 2 pattern |
| 5 | Selective agent-body enrichment (A2, skill-native) | Concise "Success Metrics" / "Deliverable Template" sections added to select `catalog/agents/` definitions where they earn their length |

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
> Validate both new integrations. (1) Run a dry-run install into a throwaway directory using both installers (`scripts/installer.sh --check` and `--dry-run`; `scripts/installer.ps1 -Check`) and confirm the Aider `CONVENTIONS.md` and Windsurf `.windsurfrules` artifacts land at their expected paths with no error and that not-detected tools skip cleanly with a note. (2) Run `make lint` (ShellCheck) and the integration pytest suite (`make test`); add or extend tests under `catalog/hooks/tests/` (or the integration test module) asserting each new subclass is registered in `_register_builtins()` and produces its expected output - model on the existing installer-smoke / integration tests. (3) Re-confirm the carried-forward v3.3.0 gap WN-v33-1: ensure CI `validate` and `scan` are green on the ubuntu runner (no code change expected). If `make` is not on PATH locally, invoke the validators directly and note it. Fix any failure and re-run until green. Then run `/session` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] Both subclasses implemented and registered in `_register_builtins()` (`aider`, `windsurf`)
- [x] Dry-run install confirms Aider + Windsurf artifacts land at expected paths (project-root `CONVENTIONS.md` / `.windsurfrules`); not-detected tools skip cleanly (Windsurf global skip-with-note when `~/.codeium` absent; Aider global no-op-with-note)
- [x] Integration pytest suite green (231 passed; new `test_aider_windsurf.py` 8 passed; contract suite +10 for the two keys) and the dry-run check is clean (direct equivalents per WN-v33-1: `make` not on PATH locally, validators invoked directly; ShellCheck not installed locally, `bash -n` + PowerShell AST parse both clean; CI `validate`/`scan`/ShellCheck run on the ubuntu runner)
- [x] AGENTS.md platform-coverage section, RE matrix row, and CHANGELOG `[Unreleased]` updated
- [x] No upstream repo named in any shipped artifact (attribution only in the RE matrix `re-full` platform-integration row)
- [x] No known regressions (hook suite 439 passed / 7 skipped; catalog unchanged at 256 skills, orphan-bundle audit clean); session history generated
- [x] Ready to advance to Phase 3

---

## Phase 3: Extend session-query to Obsidian + exported history (A4, re-full)

**Goal**: Extend the `session-query` skill's local discovery and extraction to two additional zero-outbound sources - Obsidian vaults and exported ChatGPT/Gemini history - so the context-pack and session-query flows see more of the user's prior context without breaking the zero-outbound invariant.
**Prerequisites**: None (independent; benefits from A1's context-pack format but is not blocked by it).
**Stability Gate**: `session-query`'s bundled discovery and extraction helpers parse Obsidian vaults and exported ChatGPT/Gemini history locally; the zero-outbound invariant holds (no network module imported); every `.sh`/`.py` helper has a `.ps1` sibling; `make validate`, `make lint`, and `make test` are green; the orphan-bundle audit is clean.

### Sub-tasks

#### 3.1 - Map the extractor and define the new source formats

**Objective**: Learn the existing zero-outbound discovery/extraction helpers and pin down the parse format for each new source before editing.

**Prompt**:
> Read `catalog/skills/workflow/session-query/SKILL.md` and its bundled `scripts/` (the discovery and extraction helpers, e.g. `discover-sessions.{sh,ps1}` and `extract-session.{py,ps1}`). Confirm the current zero-outbound invariant (no network module; reads local JSONL logs only). Then define, as a short design note (no edits yet): (1) where Obsidian vaults live and how to discover them locally (the vault root, `.md` notes, the `.obsidian/` marker), and what to extract (note title, headings, body, backlinks); (2) the on-disk shape of exported ChatGPT and Gemini history (the JSON/Markdown export formats) and how to parse them into the same digest structure session-query already emits. Specify exactly which helper each new source plugs into and the normalized digest fields. Constraint: zero new outbound calls, dependencies, or credentials - everything reads local files only.

---

#### 3.2 - Extend discovery and extraction (with `.ps1` parity)

**Objective**: Implement the new local sources in the session-query helpers, preserving parity and the zero-outbound invariant.

**Prompt**:
> Extend `catalog/skills/workflow/session-query/scripts/` per the 3.1 design: add Obsidian-vault and exported-ChatGPT/Gemini-history discovery roots to the discovery helper, and add parsers for those formats to the extraction helper, normalizing into session-query's existing digest structure. Per the AGENTS.md `.ps1` parity rule, every `.sh`/`.py` change must have an identical `.ps1` sibling. Import no network module; open no connection; require no new credential. Keep additions behind the existing source-selection mechanism so default behavior is unchanged when the new sources are absent. Run ShellCheck on the `.sh` helpers.

---

#### 3.3 - Update SKILL.md and CHANGELOG

**Objective**: Document the new sources and keep the bundle reference-clean.

**Prompt**:
> Update `catalog/skills/workflow/session-query/SKILL.md` to document the new Obsidian and exported-history sources (in "When to Use" / "Instructions" / "Verification"), keeping the zero-outbound statement explicit and ensuring every bundled file remains referenced (orphan-bundle audit). Add a `## [Unreleased]` CHANGELOG entry (note: re-full, local-only, zero new outbound call / dependency / credential). ASCII-only; follow the Markdown style guide.

---

#### 3.4 - Testing and Stabilization

**Objective**: Validate the new sources and parity; iterate until stable.

**Prompt**:
> Validate the extended session-query. (1) On sample fixtures (a tiny Obsidian vault and a small exported ChatGPT/Gemini history file), confirm discovery finds them and extraction normalizes them into the expected digest structure, with default behavior unchanged when the sources are absent. (2) Confirm both the `.sh`/`.py` helpers and their `.ps1` siblings behave identically on the fixtures. (3) Run `make validate`, `make lint`, and `make test` (or direct equivalents per WN-v33-1); confirm the orphan-bundle audit is clean. Fix and re-run until green. Add/extend the CHANGELOG entry. Then run `/session` to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] Obsidian vaults and exported ChatGPT/Gemini history discovered + parsed locally; default behavior unchanged when absent (no-`--tool` scan still covers only Claude/Codex/Cursor JSONL; `test_default_root_scan_ignores_md` asserts this)
- [x] Zero-outbound invariant preserved (no network module imported; static-analysis guard over all four scripts green; grep for banned tokens clean)
- [x] `.sh`/`.py` helpers all have `.ps1` siblings with identical behavior (verified across all four sources + topic/time-window filtering; PS `ConvertFrom-Json` single-element-array unrolling handled so ChatGPT `parts` parse matches Python)
- [x] `make validate` / `make lint` / `make test` green via direct equivalents per WN-v33-1 (orphan-bundle PASS 0 errors; unicode/personal-paths/supply-chain/workflow-security clean; version-sync match; `bash -n` + PowerShell AST parse clean; repo suite 452 passed; hook suite 439 passed / 7 skipped; `test_session_query_extract.py` 26 passed; skill-security scan install-OK)
- [x] SKILL.md + CHANGELOG updated (149-line SKILL.md, ASCII-only; `[Unreleased]` "Added" entry recording re-full / zero-outbound)
- [x] No known regressions; session history generated (`docs/archive/v3/v3.4/development/history/2026-06-15_adoption-nessie-and-agency-agents-phase-3-session-query-obsidian-chatgpt-gemini.md`)
- [x] Ready to advance to Phase 4

---

## Phase 4: Optional Kimi / Qwen / OpenClaw integrations (A3-ext, re-full)

**Goal**: Extend Nexus-Hub's platform reach with three further `IntegrationBase` subclasses - Kimi, Qwen, and OpenClaw - reusing the Aider/Windsurf pattern proven in Phase 2.
**Prerequisites**: Phase 2 (these subclasses copy its integration pattern).
**Stability Gate**: three subclasses registered in `_register_builtins()`; a dry-run install reports the Kimi, Qwen, and OpenClaw artifacts at their expected paths with no error; `make lint` and the integration pytest suite are green; AGENTS.md platform-coverage section, the RE matrix, and the CHANGELOG are updated; no upstream repo named in any shipped artifact.

### Sub-tasks

#### 4.1 - Define the three transforms

**Objective**: Pin the output each new platform needs, reusing the Phase 2 design approach.

**Prompt**:
> Reusing the integration-registry pattern studied in Phase 2 (sub-task 2.1), define as a short design note (no code yet) the transform for each new platform: (1) Kimi -> `agent.yaml` + `system.md`; (2) Qwen -> a `.md` instruction file with an optional `tools` section; (3) OpenClaw -> the SOUL / AGENTS / IDENTITY split. For each, specify the global vs. project-local target path, the content emitted (Nexus-Hub instruction content + `{{SKILL_INDEX}}` block as appropriate), and which existing subclass is the closest model to copy. Constraint: pure local file emission, zero outbound calls or credentials. Apply the Reverse-Engineering Attribution Rule - do not name any upstream repo in code, comments, or docs; use generic descriptive names.

---

#### 4.2 - Implement and register the three subclasses

**Objective**: Add `kimi.py`, `qwen.py`, `openclaw.py` and wire them into the registry.

**Prompt**:
> Create `scripts/lib/integrations/kimi.py`, `scripts/lib/integrations/qwen.py`, and `scripts/lib/integrations/openclaw.py` as `IntegrationBase` subclasses per the 4.1 design, each modeled on the closest existing subclass. Register all three in `scripts/lib/integrations/__init__.py::_register_builtins()` (the MANDATORY step - the file alone does nothing without registration). Follow existing conventions for path resolution, not-detected skip-with-note behavior, and the `WriteResult` contract. ASCII-only; name no upstream project in code or comments. Dry-run (`scripts/installer.sh --check`) and confirm each runs without error.

---

#### 4.3 - Update platform-coverage docs, the RE matrix, and the CHANGELOG

**Objective**: Keep documented coverage and provenance in sync.

**Prompt**:
> Update (1) `AGENTS.md` platform-coverage section to add Kimi, Qwen, and OpenClaw to the extended-platform set with the surface each gets; (2) `docs/policy/mcp-reverse-engineering-matrix.md` with a row recording provenance + the `re-full` decision-tree classification (the only place the upstream source may be named); (3) `CHANGELOG.md` `[Unreleased]` with an "Added" entry noting zero new outbound call / dependency / credential. ASCII-only across all three.

---

#### 4.4 - Testing and Stabilization

**Objective**: Verify the three integrations via dry-run and tests; iterate until stable.

**Prompt**:
> Validate the three new integrations. (1) Dry-run install into a throwaway directory with both installers and confirm the Kimi, Qwen, and OpenClaw artifacts land at expected paths with no error and that not-detected tools skip cleanly. (2) Run `make lint` and the integration pytest suite; extend the integration tests to assert each new subclass is registered and produces its expected output. (3) Re-confirm WN-v33-1 (CI validate/scan green on the ubuntu runner; invoke validators directly if `make` is absent). Fix and re-run until green. Then run `/session` to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] Three subclasses implemented and registered in `_register_builtins()` (`kimi`, `qwen`, `openclaw`; alphabetical, registry now 15 keys)
- [x] Dry-run install confirms Kimi + Qwen + OpenClaw artifacts land (runner workspace dry-run rc=0: `.kimi/system.md` + `.kimi/agent.yaml`, `QWEN.md`, `.openclaw/{AGENTS,SOUL,IDENTITY}.md`); not-detected tools skip cleanly (global scope skips-with-note unless `~/.kimi` / `~/.qwen` / `~/.openclaw` present, asserted by the new test module)
- [x] `make lint` + integration tests green via direct equivalents per WN-v33-1: `make`/ShellCheck not on PATH locally, so `bash -n` (installer.sh clean) + PowerShell `[Parser]::ParseFile` AST (installer.ps1 clean); integration pytest `tests/integrations/` 265 passed (incl. new `test_kimi_qwen_openclaw.py` and the contract suite auto-covering all 13 keys); `test_installer_smoke.py` 28 passed. CI `validate`/`scan`/ShellCheck run on the ubuntu runner (no code change expected)
- [x] AGENTS.md platform-coverage section, a new RE matrix `re-full` row, and CHANGELOG `[Unreleased]` "Added" entry updated
- [x] No upstream repo named in any shipped artifact (kimi/qwen/openclaw `.py`, base-*.md templates, both installers, AGENTS.md all clean per grep; attribution only in the RE matrix row + internal planning docs)
- [x] No known regressions (catalog unchanged at 256 skills; no skill/data registry edit needed for integrations); session history generated
- [x] Ready to advance to Phase 5

---

## Phase 5: Selective agent-body enrichment (A2, skill-native)

**Goal**: Where a Nexus-Hub agent definition genuinely benefits, add concise "Success Metrics" / "Deliverable Template" sections - keeping the terse, verification-first style and importing none of the source's persona/vibe narration.
**Prerequisites**: None. Sequenced last (a deliberate deviation from strict skill-native-first ordering) because it is the lowest-value, opportunistic, edits-existing-files item. Final phase of this plan, so it triggers release readiness on completion.
**Stability Gate**: a small, justified set of agent files under `catalog/agents/` carry the new sections where they earn their length; no persona/vibe content is introduced; `make validate` is green; the change is scoped (no agent edited "just because").

### Sub-tasks

#### 5.1 - Select the agents that benefit

**Objective**: Decide which agents earn the new sections, before editing any.

**Prompt**:
> Survey `catalog/agents/` and identify the small set of agent definitions where a concise "Success Metrics" or "Deliverable Template" section would measurably improve the agent's output contract (favor deliverable-producing agents over read-only reviewers). Produce a short list with one-line justifications. Do NOT edit any agent yet. Constraint: this is opportunistic enrichment - if an agent's existing structure already conveys success criteria, leave it alone. Import no persona/vibe framing from the comparison source.

---

#### 5.2 - Add the sections to the selected agents

**Objective**: Add terse, verification-first sections to the chosen agents only.

**Prompt**:
> For each agent selected in 5.1, add a concise "Success Metrics" and/or "Deliverable Template" section in the repo's terse, verification-first style (observable outcomes, not vibe narration). Match the existing agent file structure and tone exactly. ASCII-only; follow the Markdown style guide. Change only the selected agents - every changed line must trace to the enrichment rationale from 5.1.

---

#### 5.3 - Testing and Stabilization

**Objective**: Validate the agent edits and run release readiness as the final phase.

**Prompt**:
> Validate the agent enrichment. (1) Run `make validate` (and any agent-definition validators) and confirm green; (2) confirm no persona/vibe content was introduced and only the selected agents changed. Add a `## [Unreleased]` CHANGELOG entry (skill-native authoring; zero new outbound call / dependency / credential). Then run `/session` to document Phase 5. As this is the plan's final phase, `/implement` then triggers release readiness; route the version bump / changelog / tag / push through `/update release` per the implement-phase final-phase contract.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - Constitution Check has no FAIL bullets) | | |

---

### Phase 5 Exit Checklist

- [x] Only the justified set of agents edited; selection rationale recorded (3 agents: `build-error-resolver`, `harness-optimizer`, `doc-updater`; the 13 JSON-contracted reviewers and the 6 Output-Format-bearing working agents left untouched)
- [x] "Success Metrics" / "Deliverable Template" sections added in the terse verification-first style; no persona/vibe content (all added lines are observable metrics or a literal report template; ASCII-only)
- [x] `make validate` green (or direct equivalents per WN-v33-1: unicode-safety/no-personal-paths/workflow-security/supply-chain all exit 0; JSON integrity 256 skills / 15 bundles; orphan-bundle PASS; version-sync match 3.3.4; the three edited files ASCII-clean, all 14 `--strict` em-dash flags pre-existing)
- [x] CHANGELOG updated (`[Unreleased]` "Changed" entry; skill-native, zero new outbound call / dependency / credential)
- [x] No known regressions; session history generated (`docs/archive/v3/v3.4/development/history/2026-06-15_adoption-nessie-and-agency-agents-phase-5-agent-body-enrichment.md`)
- [ ] Release readiness run via `/update release` (final phase)

---

## Out of Scope / Deferred (backlog)

The next `/plan` ingests these via the known-gaps file.

| ID | Item | RE class | Why deferred |
|---|---|---|---|
| A5 (C2) | Generalize bespoke per-subclass transforms into a declarative canonical -> per-platform table | `re-full` | High-effort architectural refactor with no standalone user value; only worth it if platform count keeps growing. |

Permanently excluded (from the report's NOT-recommended list, with grounds): Nessie the product / any Nessie API (`drop-outright` - closed-source vendor + data egress; MCP Registry Policy Hard-No), personality/vibe theater + business-division breadth (out of scope - identity conflict), multilingual catalog (style-guide conflict).

## Carried-forward known gaps (from v3.3.0)

- **WN-v33-1** (Low): confirm CI `validate` and `scan` are green on the ubuntu runner; locally, `make` may not be on PATH, so invoke validators/scanner directly. Folded into 1.5, 2.5, 3.4, 4.4, and 5.3.
- **WN-v33-2** (Low): two benign pre-existing global-audit warnings (the `demo-capture` orphan `.pyc` is local-only/gitignored; `git-branching-workflow` has a 169-word `overview_l1` soft warning). Optional one-line reword of that overview can be picked up opportunistically; no gate impact.
