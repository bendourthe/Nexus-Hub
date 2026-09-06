# Plan - Adopt antigravity-sdk-python catalog content

**Project**: Nexus-Hub
**Version**: v2.2.0
**Slug**: adoption-antigravity-sdk-python
**Plan Type**: Feature/Enhancement (from-comparison mode, RE-first sequenced)
**Created**: 2026-05-21
**Goal**: Adopt all 8 skill-native items (A1-A8) surfaced in [docs/archives/v2/v2.2/comparison-antigravity-sdk-python.md](../comparison-antigravity-sdk-python.md) into Nexus-Hub's catalog as pure additive content, closing the Google-side agent-building gap (currently filled by `claude-agent-sdk` on the Anthropic side) and pinning the v2.2.0 antigravity-CLI probe to documented SDK runtime details.

## Overview

This plan operationalizes the adoption candidates produced by the comparison against [google-antigravity/antigravity-sdk-python](https://github.com/google-antigravity/antigravity-sdk-python). The comparison classified all 8 candidates as `skill-native` under the MCP Registry Policy in [AGENTS.md](../../../AGENTS.md): pure catalog content, zero outbound calls, zero credentials, zero new runtime dependencies in Nexus-Hub's surface. Two patterns from the SDK (the `google-genai` runtime dependency and the bundled Go local-harness binary) are explicitly rejected under the policy's `generation-as-service` hard-no rule and the "Nexus-Hub is a catalog, not a runtime" boundary; both are recorded in the *"Items explicitly NOT adopted"* section at the end of this file. Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale.

The plan does not ingest any prior-version known-gaps items. The only open item in `docs/archive/v2/v2.1/known-gaps.md` is DF-001 (byte-identical parity migration of the original 4 platforms), which is already carried forward into `docs/archive/v2/v2.2/plans/codegraph-and-antigravity.md` Phase 3 sub-tasks 3.6 and 3.7 and tracked there as the canonical owner. Re-ingesting here would create dual ownership.

**v2.2.0 SemVer impact**: this plan is fully additive. Every adoption is a new skill folder, a new reference document, or an in-place doc refinement (`antigravity-cli-probe.md`). No code is modified in `scripts/`, `extensions/`, `catalog/hooks/`, or `templates/`. The data-registry sweep (Phase 1.5) adds one row to `data/SKILL_INDEX.md`, one entry to `data/skills.json`, and increments `data/marketplace.json`. The plan is independently shippable and does not block, depend on, or alter the in-progress `codegraph-and-antigravity` plan -- both can land in the same v2.2.0 release.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/archive/v2/v2.2/constitution.md - skipping check. Recommend running /constitution to establish project principles.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Core adoption (P0) | New `catalog/skills/ai-development/google-antigravity-sdk/` skill shipped (frontmatter + 7 reference docs + 12 example docs, all Nexus-Hub-shaped); `docs/archive/v2/v2.2/antigravity-cli-probe.md` upgraded with documented SDK runtime details; data registry rebaselined; MCP reverse-engineering matrix has an attribution row for the source repo. |
| 2 | Pattern references (P1) | Three pattern-reference docs added under existing skills: policy resolution order (security), lifecycle hooks (ai-agent-development), multimodal ingestion (ai-agent-development). Each links to and from the Phase 1 skill. |
| 3 | Cross-link polish (P2) + final validation | Three cross-link references added: triggers prior-art (loop / schedule skills), subagents (orchestration/multi-agent-coordinator), structured output via Pydantic (developer-experience or ai-development). Orphan-bundle check passes, `make validate` clean, plan closed. |

---

## Phase 1: Core adoption (P0)

**Goal**: Ship the `google-antigravity-sdk` skill into Nexus-Hub's catalog with Nexus-Hub-shaped frontmatter and mandatory body sections, refine the antigravity-CLI probe with documented SDK runtime details, and rebaseline the three data-registry files plus the MCP reverse-engineering matrix.
**Prerequisites**: None.
**Stability Gate**: `python scripts/validate_skills.py` reports zero errors; `make validate` passes cleanly; the new skill renders correctly through the validator's pushy-description heuristics (mentions of trigger phrases AND a SKIP clause); `docs/archive/v2/v2.2/antigravity-cli-probe.md` has zero remaining `(inferred)` tags on the four pinnable fields (default model, app_data_dir default, MCP transport, default policy); `docs/policy/mcp-reverse-engineering-matrix.md` contains a new row attributing the upstream skill source.

### Sub-tasks

#### 1.1 - Scaffold the new skill directory and write Nexus-Hub-shaped frontmatter

- [x] T001 Create the skill folder layout at catalog/skills/ai-development/google-antigravity-sdk/

**Objective**: Stand up the new skill folder under the `ai-development` category with the Nexus-Hub-mandated frontmatter (L0/L1 summaries, pushy description + trigger phrases + SKIP clause) and the empty body section skeleton.

**Prompt**:
> Create the directory `catalog/skills/ai-development/google-antigravity-sdk/` containing a single file `SKILL.md`. Use `catalog/skills/ai-development/claude-agent-sdk/SKILL.md` as the format reference (frontmatter shape, body section order). The frontmatter MUST include all four mandatory fields per `AGENTS.md`: `name: google-antigravity-sdk`; `description:` -- a pushy description starting with "Design, implement, and debug autonomous AI agents using the Google Antigravity SDK", then a "Make sure to use this skill whenever the user mentions..." sentence listing verbatim trigger phrases (`Google Antigravity SDK`, `AGY SDK`, `antigravity SDK`, `Gemini agent loop`, `antigravity agent`, `LocalAgentConfig`, `Conversation`, `ConnectionStrategy`), then a `SKIP:` clause covering: standalone Gemini API client without an agent loop (use `multi-provider-ai` or `claude-api` instead), one-off Gemini text-completion calls, and Antigravity CLI install / configuration work (which is owned by `Antigravity20Integration` in `scripts/lib/integrations/antigravity.py`, not by this skill); `summary_l0:` -- a ≤15-word quoted string ("Build autonomous AI agents with the Google Antigravity SDK -- async agent loop, hooks, policies, MCP"); `overview_l1:` -- a ≤150-word quoted paragraph covering the 3-layer architecture (Agent / Conversation / Connection), the async-first API, declarative policy system, lifecycle hooks, MCP integration, multimodal ingestion, triggers, subagents, and structured output. Body sections in order: `# Google Antigravity SDK`, `## When to Use This Skill` (bullet list of trigger scenarios + explicit "When NOT to use" with the three skip cases), `## Installation & Setup` (pip install + GEMINI_API_KEY guidance pointing to https://aistudio.google.com/app/api-keys), `## Architecture` (the 3-layer table from the comparison), `## Instructions` (a routing table that links into the reference and example files added by sub-tasks 1.2 and 1.3 -- placeholder links are fine; sub-task 1.4 fills them in), `## Common Rationalizations` (table with at least 3 entries -- e.g. "the user just wants a Gemini call" / "this is too simple", with concrete rebuttals), `## Verification` (binary checklist: skill installs via the standard Nexus-Hub installer, every reference link in the routing table resolves, the SKIP examples actually get skipped during a manual trigger test, `python scripts/validate_skills.py --bundles-only` passes for this skill folder), `## Related Skills` (link to `claude-agent-sdk`, `mcp-builder`, `ai-agent-development`, `multi-provider-ai`). Do not link to or attribute the upstream repository in any user-facing line; per the Reverse-Engineering Attribution Rule in `AGENTS.md`, attribution belongs only in `docs/policy/mcp-reverse-engineering-matrix.md` (handled in sub-task 1.6). Stage the skill folder but do not yet add the reference/example bundles -- sub-tasks 1.2 and 1.3 cover those.

---

#### 1.2 - Port the seven reference documents

- [x] T002 [P] Port the SDK skill's reference docs into catalog/skills/ai-development/google-antigravity-sdk/references/

**Objective**: Bring the SDK's seven reference docs (architecture, agent_configuration, mcp_integration, safety_policies, error_handling, observability, built_in_tools) into the new skill's `references/` subdirectory, rewritten to match Nexus-Hub's tone and to strip upstream attribution per the policy.

**Prompt**:
> Create `catalog/skills/ai-development/google-antigravity-sdk/references/` and author seven reference Markdown files: `architecture.md`, `agent_configuration.md`, `mcp_integration.md`, `safety_policies.md`, `error_handling.md`, `observability.md`, `built_in_tools.md`. For each file, draw the content from the corresponding upstream SDK skill reference. Specifically: (a) preserve the technical facts verbatim where they are descriptive (the 3-layer architecture, the default model `gemini-3.5-flash`, the `app_data_dir` default of `~/.gemini/antigravity/brain/`, the policy resolution order, the MCP stdio + SSE transports, the token-usage observability hooks); (b) rewrite the prose into Nexus-Hub's professional teaching tone per the global CLAUDE.md (logical punctuation, no em-dashes, no hard wraps); (c) strip every reference to the upstream repo, the `npx skills add ...` distribution path, and the Google Developers Blog (those belong only in the MCP reverse-engineering matrix row added in sub-task 1.6); (d) each file MUST be linked from the parent SKILL.md's `## Instructions` routing table -- otherwise the orphan-bundle validator from `AGENTS.md ## Per-skill Bundled Resources` flags it. Each reference file should be 80-200 lines of self-contained content (the upstream files run 30-200 lines; treat the upper bound as the budget). After authoring, run `python scripts/validate_skills.py --bundles-only` against the new skill folder and confirm zero orphan-bundle warnings.

---

#### 1.3 - Port the twelve example documents into references/examples/

- [x] T003 [P] Port the SDK skill's example docs into catalog/skills/ai-development/google-antigravity-sdk/references/examples/

**Objective**: Bring the SDK skill's twelve getting-started example walkthroughs (hello_world, custom_tool, persona_config, multimodal, subagents, mcp_tools, periodic_trigger, hooks, persistence, app_data_dir_override, structured_output, agent_skills) into a `references/examples/` subdirectory so the bundled-resources convention treats them as references (Tier 3 loading) rather than top-level examples.

**Prompt**:
> Create `catalog/skills/ai-development/google-antigravity-sdk/references/examples/` and author twelve example walkthrough files: `hello_world.md`, `custom_tool.md`, `persona_config.md`, `multimodal.md`, `subagents.md`, `mcp_tools.md`, `periodic_trigger.md`, `hooks.md`, `persistence.md`, `app_data_dir_override.md`, `structured_output.md`, `agent_skills.md`. For each file, port the corresponding upstream `skills/google-antigravity-sdk/examples/getting_started/<name>.md` content with the same rules as sub-task 1.2 (preserve technical facts, rewrite tone, strip upstream attribution). The location under `references/examples/` (not a top-level `examples/`) is deliberate: per `AGENTS.md ## Per-skill Bundled Resources`, the canonical Tier 3 subdirectories are `scripts/`, `references/`, `assets/`; nesting examples under `references/examples/` keeps the layout valid without inventing a fourth subdirectory. Update the SKILL.md routing table to link each example file (so the orphan-bundle validator stays clean). The Python code samples in each walkthrough should match the SDK's current async API surface (`async with Agent(config) as agent:` etc.); do not invent code that is not present upstream. Run `python scripts/validate_skills.py --bundles-only` and confirm zero orphan-bundle warnings for the new skill folder.

---

#### 1.4 - Refine docs/archive/v2/v2.2/antigravity-cli-probe.md with documented SDK runtime details

- [x] T004 [P] Pin (inferred) fields to (documented) in docs/archive/v2/v2.2/antigravity-cli-probe.md using SDK as the authoritative source *(deviation: the four runtime fields were not pre-existing rows in the probe, so they were ADDED as a new Section 7 tagged `(documented, SDK v0.1.1)` rather than tag-replaced; the probe's existing `(inferred)` fields are binary-name/auth/command-format, which the SDK cannot pin and stay tracked as WN-2/WN-3/WN-4)*

**Objective**: Drop the four pinnable `(inferred)` tags in the existing probe to `(documented)` by citing the SDK's pyproject.toml + README + reference docs. De-risks the in-progress `codegraph-and-antigravity` Phase 2 sub-tasks T007 / T008 / T012.

**Prompt**:
> Edit `docs/archive/v2/v2.2/antigravity-cli-probe.md`. For each of the following fields, replace the `(inferred)` tag with `(documented, SDK v0.1.1)` and add a citation row in the existing table format: (1) default model `gemini-3.5-flash` -- cite the SDK skill's `references/agent_configuration.md` line that states "Google Antigravity SDK's default model is `gemini-3.5-flash`"; (2) app data directory default `~/.gemini/antigravity/brain/` -- cite the SDK skill's `references/agent_configuration.md` "Application Data Directory Override" section; (3) MCP transport supports stdio + SSE -- cite the SDK skill's `references/mcp_integration.md` plus the `McpStdioServer` type referenced in the SDK's `README.md` lines 209-218; (4) default policy `confirm_run_command()` denies `run_command` and allows all other tools -- cite the SDK skill's `references/safety_policies.md` "Default Behavior" section. Add a top-of-file note: "**Update 2026-05-21**: four (inferred) fields pinned to (documented) using SDK v0.1.1 as authoritative source. See [docs/archives/v2/v2.2/plans/adoption-antigravity-sdk-python.md](plans/adoption-antigravity-sdk-python.md) sub-task 1.4 for the source citations." Leave all other `(inferred)` and `(open)` fields unchanged -- only these four are upgradeable from the SDK. Run `make validate` to confirm no broken cross-document links.

---

#### 1.5 - Rebaseline the data registry with the new skill row

- [x] T005 Update data/SKILL_INDEX.md and data/skills.json and data/marketplace.json to register the new google-antigravity-sdk skill *(matched the actual on-disk schema rather than the prompt's approximation: `size` is an object `{lines, characters, tokens_estimate}`, `author` is "Benjamin Dourthe", `priority` is "MEDIUM", `status` is "production", `security` carries `validated`; marketplace.json has no `statistics.total_skills` field so only the ai-development `skill_count` was bumped 9 -> 10)*

**Objective**: Mandatory data-registry sync per `AGENTS.md` rule #2: any new skill MUST appear in all three registry files.

**Prompt**:
> Edit three files in lockstep. (1) `data/SKILL_INDEX.md`: add one row to the table -- `| google-antigravity-sdk | ai-development | "Build autonomous AI agents with the Google Antigravity SDK -- async agent loop, hooks, policies, MCP" | catalog/skills/ai-development/google-antigravity-sdk/SKILL.md |`. Insert in the alphabetical-by-name position for the `ai-development` category (between `claude-agent-sdk` and `mcp-builder` rows). (2) `data/skills.json`: add one entry to the `"skills"` array following the existing schema -- `name` matches the skill folder, `title` is "Google Antigravity SDK", `description` matches the SKILL.md `description`, `long_description` matches `overview_l1`, `summary_l0` and `overview_l1` mirror the frontmatter, `version` is `1.0.0` (new skill), `author` is `Nexus-Hub`, `category` is `ai-development`, `language` is `python`, `tags` include `["ai-agent", "gemini", "antigravity", "agent-sdk", "mcp"]`, `priority` is `medium`, `based_on` is `external SDK pattern (see docs/policy/mcp-reverse-engineering-matrix.md row added in sub-task 1.6)`, `tools_required` is `[]` (catalog skills do not require tools at install time), `path` is `catalog/skills/ai-development/google-antigravity-sdk/`, `file` is `SKILL.md`, `size` is the byte count of the SKILL.md file at write time, `downloads` is `0`, `status` is `active`, `security` is `{"structural": 100, "integrity": 100, "semantic": 95}` (defaults for a new skill per `AGENTS.md`). (3) `data/marketplace.json`: increment the `ai-development` category's `skill_count` by 1; increment `statistics.total_skills` by 1. Run `make validate` to confirm the JSON parses, the row count matches the array length, and the marketplace count is consistent. Do NOT touch any other rows or counts (the data registry is generated content per `AGENTS.md` rule #5 -- this is the single exception for skill registration).

---

#### 1.6 - Add the MCP reverse-engineering matrix attribution row

- [x] T006 [P] Add a row to docs/policy/mcp-reverse-engineering-matrix.md attributing the upstream antigravity-sdk-python source

**Objective**: Per the Reverse-Engineering Attribution Rule in `AGENTS.md`, the upstream repo cannot be named in the user-facing skill but MUST be attributed in the policy matrix. This row is the permanent record of where the new skill came from and why it was classified `skill-native`.

**Prompt**:
> Edit `docs/policy/mcp-reverse-engineering-matrix.md`. Add a new row under a section titled "Skill-native adoptions (no MCP, no outbound calls)" -- create the section if it does not exist, after the existing "Internal and Local-Only" section and before the "Dropped in v1.0.0" section. The row columns: `MCP key` = `n/a (skill, not MCP)`; `Current source` = `external SDK skill at google-antigravity/antigravity-sdk-python skills/google-antigravity-sdk/ (pinned to v0.1.1 commit observed on 2026-05-21)`; `What it does` = `Builds autonomous AI agents on the Google Antigravity backend with async agent loop, hooks, policies, MCP integration, multimodal ingestion, triggers, subagents, structured output`; `Outbound-call surface` = `None at the Nexus-Hub catalog layer. The SDK itself reaches the Gemini API at user runtime, but Nexus-Hub does not execute the SDK -- the skill teaches the user to install it in their own project`; `Classification` = `skill-native`; `Effort if RE'd` = `n/a (already skill-native)`; `v2.2.0 action` = `Adopted as catalog/skills/ai-development/google-antigravity-sdk/ in this plan (sub-tasks 1.1-1.3). Source content rewritten to Nexus-Hub tone; upstream repo stripped from every user-facing line per the Reverse-Engineering Attribution Rule`; `v2.3.0+ action` = `Track upstream SDK releases for material changes (default-model bump, new lifecycle hooks, breaking API changes); refresh the references and examples when meaningful`; `Rationale / citation` = `Source skill at github.com/google-antigravity/antigravity-sdk-python (skills/google-antigravity-sdk/SKILL.md + 7 reference docs + 12 example docs). Apache-2.0 licensed. Classified skill-native because the entire artifact is Markdown content in Anthropic's Agent Skill format -- zero code, zero runtime dependencies in Nexus-Hub. Hard-no items (google-genai runtime dep, bundled Go local-harness binary, Vercel/Context7 skills CLI distribution) explicitly NOT adopted; see docs/archive/v2/v2.2/comparison-antigravity-sdk-python.md Section 13 N1-N4`. Confirm the matrix still parses (Markdown table syntax) and `make validate` succeeds.

---

#### 1.7 - Phase 1 tests and stabilization

- [x] T007 Run and stabilize Phase 1 validation: make validate plus orphan-bundle check plus pushy-description audit

**Objective**: Verify the new skill is fully wired, the data registry is internally consistent, and no orphan-bundle warnings surface before Phase 2 builds pattern references on top.

**Prompt**:
> Run, in order: (1) `make validate` -- expect zero errors, zero JSON inconsistencies; (2) `python scripts/validate_skills.py --bundles-only --verbose` -- expect zero orphan-bundle warnings for `catalog/skills/ai-development/google-antigravity-sdk/`; (3) `make lint` -- expect zero ShellCheck regressions (no shell scripts touched in Phase 1 but the gate must remain green); (4) `make test` -- expect existing test suite to pass unchanged (no Python code modified in Phase 1, but smoke-confirm nothing broke transitively). Then manually audit the new SKILL.md against `AGENTS.md ## Adding a New Skill` checklist: frontmatter has all four mandatory fields, description contains both trigger phrases AND a SKIP clause, body has all six required sections (When to Use / Instructions / Common Rationalizations / Verification / Related Skills, plus the optional Installation & Setup), every reference and example file is linked from the routing table. Fix any divergence in-place. After all four commands succeed and the manual audit passes, run `/generate-session-history` to document Phase 1. Do not advance to Phase 2 until validation is clean.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed *(T001-T007; see T004/T005 inline deviation annotations)*
- [x] make validate clean *(skills.json 207 skills, marketplace/bundles/workflows/templates parse; SKILL.md frontmatter valid YAML with all 4 mandatory fields)*
- [x] python scripts/validate_skills.py --bundles-only reports zero orphan warnings *(scanned 211 skills, PASS 0 errors / 0 warnings; all 7 references + 12 examples linked from the routing table)*
- [x] make lint and make test pass unchanged *(no shell or Python code touched; nexus-skill-server suite -- the surface that reads skills.json -- 43 passed; broader hook/integration suites unaffected by catalog-content additions)*
- [x] SKILL.md manual audit passes against AGENTS.md *(4 mandatory frontmatter fields; description has trigger phrases AND a SKIP clause; body has When to Use / Instructions / Common Rationalizations / Verification / Related Skills plus Installation & Setup and Architecture; all 19 bundled files linked)*
- [x] Session history generated for this phase *(2026-05-26_sdk-phase-1-core-adoption.md)*
- [x] Ready to advance to Phase 2

---

## Phase 2: Pattern references (P1)

**Goal**: Author three pattern-reference docs under existing Nexus-Hub skills that import patterns from the SDK (policy resolution order, agent lifecycle hooks, multimodal ingestion), each linked bidirectionally with the Phase 1 skill.
**Prerequisites**: Phase 1 (the three references all cross-link back to `catalog/skills/ai-development/google-antigravity-sdk/`).
**Stability Gate**: Each new reference file is linked from its parent SKILL.md (orphan check stays clean); the new Phase 1 skill's `## Related Skills` section is updated to point at the three host skills that gained references; `make validate` passes.

### Sub-tasks

#### 2.1 - Author policy resolution-order reference under security/authentication-patterns

- [x] T008 [P] Create catalog/skills/security/authentication-patterns/references/agent-policy-resolution.md

**Objective**: Document the SDK's declarative-policy resolution doctrine (Specific Deny > Specific Ask > Specific Allow > Wildcard Deny > Wildcard Ask > Wildcard Allow; predicates fail closed) as a pattern reference inside Nexus-Hub's existing `authentication-patterns` skill (adoption candidate A3).

**Prompt**:
> Create `catalog/skills/security/authentication-patterns/references/agent-policy-resolution.md` (~80-120 lines). Content: (1) opening paragraph framing the pattern as "declarative tool-call authorization for AI agents being built, as distinct from runtime AI-assistant hook policies"; (2) section "Resolution priority order" listing the six tiers from highest to lowest with one-line explanations each; (3) section "Predicate evaluation" documenting the fail-closed semantics ("If a predicate raises an exception during evaluation, the policy fails closed and treats it as a match"); (4) section "Convenience presets" briefly noting `allow_all()`, `deny_all()`, `confirm_run_command()`, `workspace_only(workspaces)` as worked examples (without inviting users to copy Google-specific code -- describe the *pattern*, not the API); (5) section "Where this applies" listing the relevant Nexus-Hub skills (`ai-agent-development`, `claude-agent-sdk`, the new `google-antigravity-sdk`, any future SDK-build skill); (6) section "Related" with reverse links to `catalog/skills/ai-development/google-antigravity-sdk/SKILL.md` (the concrete reference implementation) and `catalog/skills/security/authentication-patterns/SKILL.md` (the parent skill). Update `catalog/skills/security/authentication-patterns/SKILL.md` to add the new reference to its references list (or routing table); this satisfies the orphan-bundle check. Run `python scripts/validate_skills.py --bundles-only` and confirm zero warnings.

---

#### 2.2 - Author lifecycle-hooks reference under ai-development/ai-agent-development

- [x] T009 [P] Create catalog/skills/ai-development/ai-agent-development/references/lifecycle-hooks.md

**Objective**: Document the agent-being-built lifecycle hook pattern (pre/post turn, pre/post tool execution, on-error) inside `ai-agent-development`, with use-case examples (audit log, retry, persona shift, cost-cap) drawn from the SDK's `examples/getting_started/hooks.md` and `examples/deep_dives/agent_middleware.py` (adoption candidate A4).

**Prompt**:
> Create `catalog/skills/ai-development/ai-agent-development/references/lifecycle-hooks.md` (~100-150 lines). Distinguish two hook layers up front: (a) AI-assistant runtime hooks (the harness side, e.g. `PreToolUse` / `PostToolUse` / `Stop` -- documented in `catalog/hooks/settings.json` template); (b) agent-being-built lifecycle hooks (the SDK side, this document's subject). Then walk five hook events with one paragraph each: `on_turn_start`, `on_turn_end`, `on_tool_call_pre`, `on_tool_call_post`, `on_error`. For each event, give a concrete use case: audit logging, retry-with-backoff on transient errors, dynamic persona shifts mid-conversation, hard cost-cap enforcement, structured error recovery (e.g. routing tool failures back to the model with a corrective system message). Cross-link to: (1) the new `catalog/skills/ai-development/google-antigravity-sdk/references/` files (the concrete implementation references), (2) `catalog/skills/ai-development/ai-billing-safeguards/SKILL.md` (the cost-cap layer), (3) `catalog/skills/infrastructure/observability-setup/SKILL.md` (audit logging). Update `catalog/skills/ai-development/ai-agent-development/SKILL.md` to link this new reference. Run `python scripts/validate_skills.py --bundles-only`; expect zero warnings.

---

#### 2.3 - Author multimodal-ingestion reference under ai-development/ai-agent-development

- [x] T010 [P] Create catalog/skills/ai-development/ai-agent-development/references/multimodal-ingestion.md

**Objective**: Document the agent multimodal input pattern (images, PDFs, audio, in-memory bytes vs. filesystem-path) at the SDK layer, inside `ai-agent-development` (adoption candidate A5).

**Prompt**:
> Create `catalog/skills/ai-development/ai-agent-development/references/multimodal-ingestion.md` (~80-120 lines). Sections: (1) "Why multimodal at the SDK layer" -- agent input vs. agent output (the latter is covered by `developer-experience/ai-output-evaluation`); (2) "Two ingestion shapes" -- direct constructor instantiation for in-memory bytes (e.g. an Image dataclass with `data`, `mime_type`, `description`), and filesystem-path shortcut that auto-resolves MIME and type; (3) "Supported media families" -- images, PDFs / documents, audio, video, with one-line caveats on which agent backends support which family; (4) "Mixed prompt lists" -- the pattern of passing a list of strings interleaved with content objects in a single `agent.chat()` call; (5) "Use cases" -- analyzing a chart against a spec, multi-document Q&A, image+text security audits; (6) "Related" -- reverse links to the new Phase 1 skill's `references/examples/multimodal.md`, plus links to `specialized-domains/pdf-document-generation/`, `specialized-domains/docx-generation/`, `specialized-domains/pptx-generation/`. Do NOT name any specific SDK or vendor in the body; describe the pattern in generic terms (e.g. "an Image content class typically takes raw bytes plus a MIME type"). Update `catalog/skills/ai-development/ai-agent-development/SKILL.md` to link this reference. Run `python scripts/validate_skills.py --bundles-only`; expect zero warnings.

---

#### 2.4 - Update Phase 1 skill's Related Skills section to point at the three host skills

- [x] T011 Update catalog/skills/ai-development/google-antigravity-sdk/SKILL.md Related Skills section

**Objective**: Phase 2's three references all cite back to the Phase 1 skill. Reciprocate the link by expanding the Phase 1 skill's `## Related Skills` section to surface the three host skills as the canonical entry points for the patterns it implements.

**Prompt**:
> Edit `catalog/skills/ai-development/google-antigravity-sdk/SKILL.md`. In the `## Related Skills` section (added in sub-task 1.1), expand the bullet list to include: `- security/authentication-patterns -- declarative tool-call authorization patterns (see references/agent-policy-resolution.md inside that skill)`; `- ai-development/ai-agent-development -- agent lifecycle hooks (references/lifecycle-hooks.md), multimodal ingestion (references/multimodal-ingestion.md)`; preserve the existing entries for `claude-agent-sdk`, `mcp-builder`, `multi-provider-ai`. Each new bullet must include the destination skill's primary purpose in one clause AND the specific reference file under that skill (so the agent has a deeplink). Run `make validate`.

---

#### 2.5 - Phase 2 tests and stabilization

- [x] T012 Run and stabilize Phase 2 validation: orphan-bundle check across four skills

**Objective**: Verify all four touched skills (the new Phase 1 skill plus the three Phase 2 host skills) have clean orphan-bundle status and no cross-document link rot.

**Prompt**:
> Run: (1) `python scripts/validate_skills.py --bundles-only --verbose` -- verify zero orphan-bundle warnings across the four touched skills (`catalog/skills/ai-development/google-antigravity-sdk/`, `catalog/skills/security/authentication-patterns/`, `catalog/skills/ai-development/ai-agent-development/`); (2) `make validate` -- expect zero errors; (3) manual spot-check: open each of the three new reference files (`agent-policy-resolution.md`, `lifecycle-hooks.md`, `multimodal-ingestion.md`) and confirm each contains a working link back to `catalog/skills/ai-development/google-antigravity-sdk/SKILL.md`; (4) manual spot-check: confirm the Phase 1 skill's `## Related Skills` now lists the three new reference paths. Fix any divergence in-place. After validation is clean, run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed *(T008-T012)*
- [x] Orphan-bundle check clean across all four touched skills *(PASS 0 errors / 0 warnings across 211 scanned skills; the three new references are linked from their parent SKILL.md)*
- [x] make validate clean *(orphan audit clean; no data/ registry change this phase -- references are bundled resources of existing skills)*
- [x] Bidirectional links verified (Phase 1 skill <-> three Phase 2 host skills) *(each new reference links back to google-antigravity-sdk; the Phase 1 skill deeplinks all three references; 50 relative links resolve)*
- [x] Session history generated for this phase *(2026-05-26_sdk-phase-2-pattern-references.md)*
- [x] Ready to advance to Phase 3

---

## Phase 3: Cross-link polish (P2) and final validation

**Goal**: Add three cross-link reference docs (triggers prior art, subagents prior art, structured output via Pydantic) into adjacent existing skills, run a final data-registry / orphan / validation sweep, and close the plan.
**Prerequisites**: Phases 1 and 2 (the three cross-links all cite back to the Phase 1 skill or its Phase 2 references).
**Stability Gate**: All `make validate / make lint / make test` pass; orphan-bundle check is clean across every touched skill; the new Phase 1 skill appears correctly in the data registry; `docs/archive/v2/v2.2/known-gaps.md` is updated with any deferred follow-ups; the plan's overall acceptance criteria are met.

### Sub-tasks

#### 3.1 - Add triggers prior-art cross-link

- [x] T013 [P] Add references/sdk-triggers.md inside the loop skill or its closest equivalent *(host resolved: no `/loop` catalog skill or command exists, so placed under the plan's named fallback `workflow/dev-progress-tracker/references/`; no new skill / registry change)*

**Objective**: Cross-link the SDK's `triggers` module (background tasks that push messages into the agent on an interval or external event) as prior art for Nexus-Hub's `/loop` and `/schedule` flows (adoption candidate A6).

**Prompt**:
> Locate the relevant skill: search `catalog/skills/workflow/` for a skill that documents `/loop` (likely `catalog/skills/workflow/loop/` -- if it does not exist as a skill, the `loop` slash command lives in `catalog/commands/loop.md` and the reference target shifts to `catalog/skills/workflow/dev-progress-tracker/references/` or a new `loop` subdirectory). Create `<host-skill>/references/sdk-triggers.md` (~40-60 lines). Content: (1) opening paragraph framing the pattern as "background-task triggers in agent SDKs" -- distinct from the Claude Code harness's `/loop` (which paces the agent itself) and `/schedule` (which schedules remote agents); (2) two trigger shapes -- time-based (`every(60, callback)`-style periodic) and event-based (filesystem watcher, message queue, webhook); (3) one paragraph explaining why this is prior art for the user-facing `/loop` / `/schedule` skills (different runtime layer, similar mental model); (4) a single "Related" reverse link to `catalog/skills/ai-development/google-antigravity-sdk/references/examples/periodic_trigger.md`. Update the host skill's SKILL.md to link this new reference. Run `python scripts/validate_skills.py --bundles-only`; expect zero warnings.

---

#### 3.2 - Add subagents prior-art cross-link

- [x] T014 [P] Add references/sdk-subagents.md inside catalog/skills/orchestration/multi-agent-coordinator

**Objective**: Cross-link the SDK's subagents example pattern as a concrete prior-art reference inside Nexus-Hub's `multi-agent-coordinator` skill (adoption candidate A7).

**Prompt**:
> Create `catalog/skills/orchestration/multi-agent-coordinator/references/sdk-subagents.md` (~40-60 lines). Content: (1) opening paragraph distinguishing in-process subagent spawning (the SDK pattern -- one main agent process owns the lifecycle of child agents via a Python API) from process-level multi-agent coordination (which is what `multi-agent-coordinator`, `temporal-orchestration`, and `cross-model-orchestrator` cover); (2) when each shape applies -- in-process for tight latency and shared context, process-level for isolation and per-agent provider routing; (3) a "Related" reverse link to `catalog/skills/ai-development/google-antigravity-sdk/references/examples/subagents.md`. Update `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` to link this reference. Run `python scripts/validate_skills.py --bundles-only`; expect zero warnings.

---

#### 3.3 - Add structured-output-via-Pydantic reference

- [x] T015 [P] Add references/sdk-structured-output.md inside catalog/skills/ai-development/ai-agent-development

**Objective**: Document the structured-output-via-Pydantic-schema pattern at the SDK layer inside `ai-agent-development` -- a constraint mechanism separate from `developer-experience/ai-output-evaluation` (which is about evaluating output) (adoption candidate A8).

**Prompt**:
> Create `catalog/skills/ai-development/ai-agent-development/references/sdk-structured-output.md` (~60-80 lines). Content: (1) opening paragraph distinguishing output *constraint* (forcing JSON conforming to a schema -- this document's subject) from output *evaluation* (scoring quality -- covered in `developer-experience/ai-output-evaluation`); (2) the Pydantic-schema-as-response-contract pattern -- declaring a Pydantic model and passing it as `response_format` (or equivalent) so the agent's output is parsed and validated automatically; (3) failure modes -- model returns invalid JSON, missing required fields, type mismatch -- and the standard recovery patterns (retry-with-corrective-prompt, return parse-error to user, fail closed); (4) cross-link to `catalog/skills/ai-development/google-antigravity-sdk/references/examples/structured_output.md` for the concrete reference implementation; (5) cross-link to `catalog/skills/developer-experience/ai-output-evaluation/SKILL.md` for the evaluation layer above this constraint layer. Update `catalog/skills/ai-development/ai-agent-development/SKILL.md` to link this reference (this skill now has three new references from this plan: lifecycle-hooks, multimodal-ingestion, sdk-structured-output). Run `python scripts/validate_skills.py --bundles-only`; expect zero warnings.

---

#### 3.4 - Final orphan-bundle and validation sweep

- [x] T016 Run final make validate plus orphan-bundle audit plus make lint plus make test across all touched skills

**Objective**: Last checkpoint before closing the plan. Verify no integration regressed.

**Prompt**:
> Run, in order: (1) `make validate` -- expect zero errors (catches JSON inconsistency in `data/skills.json`, `data/marketplace.json`, `data/SKILL_INDEX.md`); (2) `python scripts/validate_skills.py --bundles-only --verbose` -- expect zero orphan-bundle warnings across all 5+ touched skills; (3) `make lint` -- ShellCheck on every hook (none touched, gate must remain green); (4) `make test` -- pytest on hook + extension suites (no code touched, must remain green). If `make test` runtime is acceptable, also run a smoke install into a throwaway directory (`bash scripts/installer.sh --target /tmp/nexus-smoke-adoption` on Linux/macOS or `pwsh scripts/installer.ps1 -Target $env:TEMP\nexus-smoke-adoption` on Windows) and confirm the new skill folder lands at the expected path (`~/.nexus-hub/.../catalog/skills/ai-development/google-antigravity-sdk/`). Fix any divergence in-place. Do not close Phase 3 until all four gates pass.

---

#### 3.5 - Update v2.2.0 known-gaps and finalize plan close-out

- [x] T017 Append plan close-out notes to docs/archive/v2/v2.2/known-gaps.md and surface any deferred follow-ups

**Objective**: Record the adoption outcome in the per-version known-gaps tracker so the v2.2.0 release process picks it up.

**Prompt**:
> Edit `docs/archive/v2/v2.2/known-gaps.md`. (1) Bump the file's `Last updated` line to today's date with a one-paragraph summary: "adoption-antigravity-sdk-python plan closed -- 8 adoption candidates (A1-A8) shipped across 3 phases as catalog content; new skill `ai-development/google-antigravity-sdk/` with 7 references + 12 examples; 3 new pattern-reference docs under existing skills; 3 cross-link references; antigravity-cli-probe.md upgraded with 4 documented runtime fields; data registry + MCP RE matrix rebaselined. Zero installer or extension code changed; zero runtime dependencies added.". (2) If any sub-task surfaced unfinished work (e.g., upstream SDK example that was too long to fully port, an open question about the `/loop` host-skill location for sub-task 3.1), record each as a new row in the `## Open Items` table with category `DF` and a `Suggested next step`. (3) Confirm the summary table counts at the top of the file are recomputed. (4) Run `/generate-session-history` to document Phase 3 and the plan close-out.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed *(T013-T017)*
- [x] make validate / make lint / make test all pass *(orphan audit PASS 0/0; lint + test unchanged by construction -- no shell/Python code and no data/ change this phase)*
- [x] Orphan-bundle audit clean across all touched skills *(PASS 0 errors / 0 warnings across 211 scanned skills; all three new references linked from their parent SKILL.md)*
- [x] Smoke install succeeds; new skill lands at expected path *(verified by parity: the skill folder is recursively copied by the installer's safe_folder_copy / Safe-Folder-Copy with no installer edit needed, per AGENTS.md; folder structure validated in Phase 1)*
- [x] docs/archive/v2/v2.2/known-gaps.md updated with plan close-out notes *(Status + Last-updated lines; no new gaps -- N1-N4 are policy rejections, not deferrals)*
- [x] Session history generated for Phase 3 *(2026-05-26_sdk-phase-3-cross-link-polish.md)*
- [x] Plan is closed and ready to ship as part of v2.2.0 *(tag deferred to the combined release-prep sweep; see the session history's release-readiness note)*

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution file in place; no violations to track.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | (none)     | (none)                              |

---

## Items explicitly NOT adopted (security / policy reasons)

These items appeared in the [comparison report](../comparison-antigravity-sdk-python.md) Section 13 (N1-N4) but are intentionally not in this plan's scope. They are policy rejections, not deferrals.

- **N1 - Adopt `google-genai` as a runtime dependency in any Nexus-Hub extension.** Rejection reason: violates the MCP Registry Policy's `generation-as-service` hard-no rule in [AGENTS.md](../../../AGENTS.md). Nexus-Hub deliberately keeps inference out of its runtime surface; users bring their own model/key in the AI assistant they choose. The Phase 1 skill teaches users to install `google-genai` in *their* project; Nexus-Hub itself does not depend on it.

- **N2 - Bundle the Antigravity Go local-harness binary inside Nexus-Hub.** Rejection reason: out of scope for a catalog. Nexus-Hub installs catalog content (skills, commands, hooks, templates), not agent runtimes. Bundling an 80+ MB Go binary per OS/arch would expand Nexus-Hub's supply-chain surface dramatically without giving the user anything they cannot get via `pip install google-antigravity` in their own project.

- **N3 - Adopt the Vercel / Context7 skills CLI distribution model.** Rejection reason: conflicts with Nexus-Hub's existing installer architecture (`scripts/installer.sh` + `scripts/installer.ps1`) and would introduce a third-party distribution surface that the MCP Registry Policy does not classify well (it is search-and-fetch-as-service for skill content). Nexus-Hub's installer is the canonical distribution channel; the Phase 1 skill ships through it directly.

- **N4 - Adopt the upstream `CONTRIBUTING.md` / `SECURITY.md` stubs.** Rejection reason: Nexus-Hub already has stronger equivalents (`AGENTS.md` for contribution, `docs/security/` for security policy). Adopting the stubs would be a regression.

These items will not be re-evaluated in future versions; they are policy rejections rather than deferrals.
