# Plan -- Adopt mattpocock/skills (selective)

**Project**: DevAI-Hub
**Version**: v1.0.0
**Slug**: adoption-mattpocock-skills
**Plan Type**: Feature/Enhancement
**Created**: 2026-04-27
**Goal**: Adopt all 14 candidates (P0+P1+P2+P3) from `docs/archive/v1/v1.0/comparison-mattpocock-skills.md`, registered and validated, with `make validate` / `make lint` / `make test` clean and a `CHANGELOG.md` entry under `[Unreleased]`.

## Overview

This plan operationalizes the comparison report at [`docs/archives/v1/v1.0/comparison-mattpocock-skills.md`](../comparison-mattpocock-skills.md). It ports 9 net-new skills (6 to a brand-new `github-workflow/` category, 2 to `developer-experience/`, 1 to `architecture/`) plus 4 in-place edits to existing skills (Ousterhout deep-modules vocabulary into `component-boundary-identifier` + `refactoring-expert`, the "no horizontal slicing" TDD anti-pattern into `test-driven-development`, the "information is a DAG" rule into `writing-editing`, and a Husky quick-start into `pre-commit-checklist`).

Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale: every adoption candidate is `skill-native` except item A12 (`re-partial`), which lands in the final Husky-scaffold phase per policy.

Two pieces of foundation work precede the ports: (1) creating the `github-workflow/` skill category and registering it in `data/marketplace.json`; (2) extending the internal MCP skill server (`extensions/devai-skill-server/`) to honor mattpocock's `disable-model-invocation: true` frontmatter, since two of the ported skills (`zoom-out`, `caveman-mode`) rely on it. Both land in Phase 1.

Success is observable: 9 new SKILL.md files exist with progressive-disclosure frontmatter, 4 existing skills have the absorbed sections, `data/SKILL_INDEX.md` / `data/skills.json` / `data/marketplace.json` are updated and validated, the MCP server's pytest suite passes including the new `disable-model-invocation` test, and `CHANGELOG.md` records the adoption under `[Unreleased]`.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1     | Foundation: `github-workflow/` category + `disable-model-invocation` MCP support | Category exists; MCP skill server honors the new frontmatter; pytest covers the behavior |
| 2     | P0 skill-native quick wins | `zoom-out`, `grill-me`, `plan-to-github-issues` ported, registered, validated |
| 3     | P1 GitHub-issue-driven workflows | `synthesize-prd-from-context`, `bug-to-github-issue`, `qa-session-to-issues`, `refactor-rfc` in `github-workflow/` |
| 4     | P1 maintainer-side: GitHub issue triage state machine | `github-issue-triage` + `references/agent-brief.md` + `references/out-of-scope.md` |
| 5     | P2 niche-but-good | `design-it-twice` (architecture/) and `caveman-mode` (developer-experience/, with `disable-model-invocation: true`) |
| 6     | P3 pattern absorption into existing skills | Ousterhout vocabulary, TDD anti-pattern, article-DAG rule absorbed -- no new skills |
| 7     | re-partial: Husky quick-start in `pre-commit-checklist` | Husky/lint-staged/Prettier scaffold section added |
| 8     | Final validation, multi-platform sync, changelog, commit | All gates green; `{{SKILL_INDEX}}` propagates; `[Unreleased]` entry; user-confirmed commit |

---

## Phase 1: Foundation -- `github-workflow/` Category and `disable-model-invocation` Support

**Goal**: Land the two pieces of infrastructure that every subsequent phase depends on -- a new skill category and an MCP-server-level feature flag.

**Prerequisites**: None.

**Stability Gate**: `data/marketplace.json` validates (`make validate`); the MCP skill server pytest suite passes including a new test that verifies `disable-model-invocation: true` skills are not surfaced for auto-invocation.

### Sub-tasks

#### 1.1 -- Create the `github-workflow/` skill category

**Objective**: Add a new top-level skill category at `catalog/skills/github-workflow/` with a README and register it in the catalog metadata.

**Prompt**:

> You are working in DevAI-Hub. Create a new skill category called `github-workflow/`. Steps:
>
> 1. Create directory `catalog/skills/github-workflow/`.
> 2. Create `catalog/skills/github-workflow/README.md` describing the category's purpose: "Skills that drive GitHub-issue-creation and GitHub-issue-management workflows -- bridging conversation context, plans, bug investigations, and refactor proposals into durable, agent-grabbable GitHub issues. Every skill in this category uses the `gh` CLI against the user's own repos." Match the format and length of the README in another category (e.g. `catalog/skills/bug-fixing/README.md`).
> 3. Update `data/marketplace.json` to add a new category entry for `github-workflow` with `skill_count: 0` (the count will increment as Phase 2-4 lands skills). Mirror the JSON shape of an existing category like `bug-fixing` or `workflow`. Update `total_skills` only when skills are actually added (leave it untouched in this sub-task).
> 4. Run `make validate` -- the JSON catalog must remain valid.
>
> Acceptance: `catalog/skills/github-workflow/README.md` exists; `data/marketplace.json` lists `github-workflow` as a category with `skill_count: 0`; `make validate` exits 0; no other registry files are modified in this sub-task.

#### 1.2 -- Add `disable-model-invocation` frontmatter support to `devai-skill-server`

**Objective**: Extend `extensions/devai-skill-server/` so that skills with `disable-model-invocation: true` in their YAML frontmatter are loaded into the catalog but are NOT surfaced for auto-invocation by the MCP client. They remain manually callable by name.

**Prompt**:

> You are extending `extensions/devai-skill-server/` (the internal MCP server that serves DevAI-Hub skills to AI clients). Your task is to honor a new YAML frontmatter field, `disable-model-invocation: true`, used by skills that should never auto-trigger but must remain manually invokable.
>
> Steps:
>
> 1. Read the current implementation of `extensions/devai-skill-server/`. Identify (a) the YAML frontmatter parser, (b) the function that decides which skills are surfaced for auto-invocation (the "discoverable" or "indexable" filter), and (c) the function that resolves a skill by name for explicit invocation.
> 2. Add support for the `disable-model-invocation` boolean frontmatter field. When `true`:
>    - The skill is still loaded into the in-memory catalog.
>    - The skill is NOT included in the auto-invocation discovery output (the list returned to the MCP client when it asks "what skills are available for autonomous selection?").
>    - The skill IS still resolvable when the client asks for it by exact name.
>    - The field defaults to `false` if absent.
> 3. Add a pytest test in the MCP server's test directory that:
>    - Creates a fixture skill with `disable-model-invocation: true` and another without the field.
>    - Asserts the disabled skill is absent from the discovery list.
>    - Asserts the disabled skill is still resolvable by exact name.
>    - Asserts the default-false behavior for skills without the field.
> 4. Update any user-facing docs in the `extensions/devai-skill-server/` directory (e.g. README) to mention the new field.
> 5. Run the MCP server's pytest suite. All tests must pass.
>
> Acceptance: pytest passes including the new test cases; the field is parsed and respected; legacy skills without the field continue to work unchanged; no breaking change to the MCP wire protocol.

#### 1.3 -- Document the new frontmatter field in skill-authoring guides

**Objective**: Update `AGENTS.md` and any skill-authoring documentation to mention the `disable-model-invocation: true` option.

**Prompt**:

> Update DevAI-Hub's skill-authoring documentation to mention the new `disable-model-invocation: true` frontmatter field added in sub-task 1.2.
>
> Steps:
>
> 1. Read `AGENTS.md` -- specifically the "Adding a New Skill" section's frontmatter list ("Required YAML frontmatter fields"). Add an "Optional" subsection beneath it that documents `disable-model-invocation: true` with a one-paragraph description of the use case (skills that should never auto-trigger -- e.g. response-style modes like `caveman-mode`, or stop-and-think prompts like `zoom-out`).
> 2. Search the rest of the repo for skill-authoring guides that list frontmatter fields (`catalog/skills/workflow/create-custom-command/SKILL.md`, the `create-skill-or-command` command at `catalog/commands/create-skill-or-command.md`, and anywhere else `summary_l0` is enumerated). Add the same `disable-model-invocation` mention to each.
> 3. Run `make validate` and `make lint`.
>
> Acceptance: `AGENTS.md` documents the field; every skill-authoring guide mentions it; no validation regression.

#### 1.X -- Testing and Stabilization

**Objective**: Verify Phase 1 foundations are stable before any skills are ported.

**Prompt**:

> Run all Phase 1 verification gates:
>
> 1. `make validate` -- JSON catalog integrity.
> 2. `make lint` -- ShellCheck.
> 3. `make test` -- pytest hook suite.
> 4. Run the `extensions/devai-skill-server/` pytest suite specifically.
> 5. Manually verify `data/marketplace.json` shows `github-workflow` as a category with `skill_count: 0`.
> 6. Generate a session history: `/generate-session-history`.
>
> Fix any failures. Do not advance to Phase 2 until every gate is green.

### Phase 1 Exit Checklist

- [ ] `catalog/skills/github-workflow/` directory and README exist
- [ ] `data/marketplace.json` lists the new category
- [ ] MCP skill server honors `disable-model-invocation: true`
- [ ] New pytest tests pass
- [ ] `AGENTS.md` and skill-authoring guides reference the new field
- [ ] All `make` gates green
- [ ] Session history generated

---

## Phase 2: P0 Skill-Native Quick Wins

**Goal**: Ship the three lowest-effort, highest-value mattpocock skills. Establishes the porting workflow that Phases 3-5 reuse.

**Prerequisites**: Phase 1 complete.

**Stability Gate**: All three skills are loadable by the MCP server, registered in the three index files, and pass `make validate`.

### Sub-tasks

#### 2.1 -- Port `zoom-out` skill (with `disable-model-invocation: true`)

**Objective**: Create `catalog/skills/developer-experience/zoom-out/SKILL.md` -- a tiny one-line skill that asks the agent to "go up a layer of abstraction" and map the modules and callers.

**Prompt**:

> Create a new skill at `catalog/skills/developer-experience/zoom-out/SKILL.md` based on the pattern from mattpocock/skills/zoom-out (do not credit the source in the file -- use generic descriptive content per the reverse-engineering attribution rule).
>
> Frontmatter requirements (from `AGENTS.md`):
>
> ```yaml
> ---
> name: zoom-out
> description: <one sentence + "Use when [triggers]">
> summary_l0: "<<=15 words>"
> overview_l1: "<<=150 words>"
> disable-model-invocation: true
> ---
> ```
>
> Body sections (per the SKILL.md template in `AGENTS.md`):
>
> 1. Brief intro paragraph -- the skill instructs the agent to step back from the current detail level and produce a map of relevant modules and their callers.
> 2. "When to Use This Skill" with explicit "When NOT to use" guidance.
> 3. "Instructions" -- 3-5 numbered steps. The output should be a module map (callers, callees, the boundary the user is currently working inside, and one level up).
> 4. "Common Rationalizations" table.
> 5. "Verification" checklist with observable artifacts.
> 6. "Related Skills" section linking to `component-boundary-identifier` and `context-manager`.
>
> Keep the file under 80 lines. Follow `catalog/style-guides/markdown.md` strictly (blank lines around lists, code blocks, headings; ATX `#` headings; one H1; ASCII-only English).
>
> Then register the skill:
>
> 1. Add a row to `data/SKILL_INDEX.md` under the developer-experience category section.
> 2. Add a JSON entry to `data/skills.json` `"skills"` array (security: `structural: 100`, `integrity: 100`, `semantic: 95` defaults).
> 3. Increment `data/marketplace.json` developer-experience `skill_count` and bump `total_skills` by 1.
>
> Run `make validate`. Acceptance: skill exists, registers cleanly, validation passes.

#### 2.2 -- Port `grill-me` skill

**Objective**: Create `catalog/skills/developer-experience/grill-me/SKILL.md` -- the relentless one-question-at-a-time interview primitive that walks the design tree.

**Prompt**:

> Create `catalog/skills/developer-experience/grill-me/SKILL.md` based on mattpocock's `grill-me` pattern (do not name-credit the source). The skill instructs the agent to interview the user relentlessly about a plan or design, walking each branch of the decision tree and asking one question at a time, with the agent providing its recommended answer alongside each question.
>
> Required frontmatter: `name`, `description` (with "Use when..."), `summary_l0` (<=15 words), `overview_l1` (<=150 words). Do NOT use `disable-model-invocation` -- this skill SHOULD auto-trigger when the user says "grill me", "stress-test this plan", etc.
>
> Body sections:
>
> 1. Intro paragraph.
> 2. "When to Use This Skill" -- include a clear distinction from `idea-refine` (early ideation) and `spec-driven-development` Phase 1 (assumption surfacing): `grill-me` is the *interview loop primitive*, callable inside either of the larger skills or standalone.
> 3. "Instructions" -- the loop: (a) ask one question with a recommended answer; (b) wait for response; (c) walk to the next branch; (d) when a question can be answered by exploring the codebase, explore instead of asking.
> 4. "Common Rationalizations" table.
> 5. "Verification" checklist.
> 6. "Related Skills" linking to `idea-refine`, `spec-driven-development`, `ambiguity-detector`.
>
> Keep under 100 lines. Follow `catalog/style-guides/markdown.md`.
>
> Register: add row to `data/SKILL_INDEX.md`; add entry to `data/skills.json`; bump developer-experience `skill_count` and `total_skills`.
>
> Run `make validate`. Acceptance: registered cleanly, validation passes.

#### 2.3 -- Port `plan-to-github-issues` skill (was `to-issues`)

**Objective**: Create `catalog/skills/github-workflow/plan-to-github-issues/SKILL.md` -- breaks any plan, spec, or PRD into independently-grabbable GitHub issues using vertical-slice (tracer-bullet) decomposition.

**Prompt**:

> Create `catalog/skills/github-workflow/plan-to-github-issues/SKILL.md`. The skill takes a plan, spec, or PRD that already exists (in conversation context, in a Markdown file, or in a parent GitHub issue) and decomposes it into a set of GitHub issues, each delivering a vertical slice of behavior end-to-end.
>
> Required frontmatter: `name`, `description` (trigger phrases include "break plan into issues", "create tickets from plan", "vertical slices"), `summary_l0`, `overview_l1`.
>
> Body sections:
>
> 1. Intro -- the value proposition: turn one plan into N grabbable, parallelizable issues, each demoable on its own.
> 2. "When to Use This Skill" -- include "When NOT to use" guidance: do not use for single-step tasks; do not use when the plan itself is unwritten (use `spec-driven-development` or `generate-plan` first).
> 3. "Instructions" -- 5 numbered steps: (1) gather context -- read the plan, the source GitHub issue if any, and the codebase; (2) draft vertical slices with HITL/AFK markers (Human-In-The-Loop vs. AFK); (3) quiz the user on granularity, dependencies, and HITL/AFK assignment; (4) iterate until approved; (5) create issues in dependency order with `gh issue create`, populating "Blocked by" with real issue numbers as they are minted. Embed a complete issue-body template (Parent / What to build / Acceptance criteria / Blocked by) inline.
> 4. "Common Rationalizations" table -- include the failure mode of horizontal slicing (creating one issue per layer instead of per behavior).
> 5. "Verification" checklist -- includes "every issue is independently demoable", "blocking relationships are honest", "issues created in dependency order".
> 6. "Related Skills" -- link to `synthesize-prd-from-context`, `generate-plan` (command), `bug-to-github-issue`.
>
> Keep under 200 lines. Reference the AI-disclaimer convention (every issue body opens with `> *This was generated by AI during triage.*`) -- match the convention used by `github-issue-triage` (Phase 4).
>
> Register in `github-workflow` category. Increment `github-workflow.skill_count` to 1 in `data/marketplace.json`. Add to `data/SKILL_INDEX.md` under a new "GitHub Workflow" section if one does not exist.
>
> Run `make validate`. Acceptance: skill exists, category gains its first skill, validation passes.

#### 2.X -- Testing and Stabilization

**Objective**: Verify Phase 2 skills load and register cleanly.

**Prompt**:

> Run Phase 2 verification:
>
> 1. `make validate` -- registry integrity.
> 2. `make lint`.
> 3. Restart or reload the MCP skill server. Verify `zoom-out` is NOT in the auto-invocation discovery list (because of `disable-model-invocation: true`) but IS resolvable by exact name. Verify `grill-me` and `plan-to-github-issues` ARE in the discovery list.
> 4. Spot-check Markdown style for all 3 new SKILL.md files against `catalog/style-guides/markdown.md`.
> 5. Generate a session history.
>
> Fix any failures. Do not advance to Phase 3 until every gate is green.

### Phase 2 Exit Checklist

- [ ] All 3 skills exist with correct frontmatter (incl. `disable-model-invocation: true` on `zoom-out`)
- [ ] All 3 skills registered in `SKILL_INDEX.md`, `skills.json`, `marketplace.json`
- [ ] `make validate` / `make lint` clean
- [ ] MCP server discovery list behavior verified
- [ ] Session history generated

---

## Phase 3: P1 GitHub-Issue-Driven Workflows

**Goal**: Land the four substantive GitHub-issue-creation skills that share the `gh issue create` surface introduced in Phase 2.

**Prerequisites**: Phase 2 complete (`plan-to-github-issues` exists; the cross-link target works).

**Stability Gate**: All four skills register cleanly; `github-workflow` category `skill_count` is 5; cross-links to existing skills (`bug-localization`, `plan-to-github-issues`) resolve.

### Sub-tasks

#### 3.1 -- Port `synthesize-prd-from-context` skill (was `to-prd`)

**Objective**: Create `catalog/skills/github-workflow/synthesize-prd-from-context/SKILL.md` -- synthesizes the current conversation context into a PRD and submits as a GitHub issue. No interview -- just synthesizes what is already known.

**Prompt**:

> Create `catalog/skills/github-workflow/synthesize-prd-from-context/SKILL.md`. The skill is the inverse of `idea-refine` -- the user has already had the conversation; this skill captures what is in context and files it as a PRD GitHub issue. Do NOT interview.
>
> Required frontmatter (`name`, `description` with triggers like "turn this into a PRD", "file as PRD", "PRD from context"; `summary_l0`; `overview_l1`).
>
> Body sections:
>
> 1. Intro -- the skill explicitly does NOT interview the user. It synthesizes from the existing conversation + a quick codebase exploration.
> 2. "When to Use This Skill" + "When NOT to use" (use `idea-refine` or `spec-driven-development` if the conversation has not happened yet).
> 3. "Instructions" -- numbered steps: (1) explore the repo for context if not already done; (2) sketch the major modules to build/modify, looking for deep-module extraction opportunities; (3) confirm modules with the user; (4) write the PRD using the embedded template (Problem Statement / Solution / User Stories / Implementation Decisions / Testing Decisions / Out of Scope / Further Notes); (5) submit via `gh issue create`. Do NOT include file paths or code snippets in the PRD body (they go stale).
> 4. "Common Rationalizations" table.
> 5. "Verification" checklist.
> 6. "Related Skills" -- link to `plan-to-github-issues` (natural follow-up), `idea-refine`, `spec-driven-development`, `ddd-strategic-design` (deep-module concept).
>
> Embed the PRD template inline. Keep under 200 lines. Markdown-style-guide compliant.
>
> Register: add to `SKILL_INDEX.md`, `skills.json`, increment `github-workflow.skill_count` to 2, bump `total_skills`.
>
> Acceptance: `make validate` clean.

#### 3.2 -- Port `bug-to-github-issue` skill (was `triage-issue`)

**Objective**: Create `catalog/skills/github-workflow/bug-to-github-issue/SKILL.md` -- investigates a reported bug, finds root cause, and creates a GitHub issue with a TDD-based fix plan. Cross-links to existing `bug-localization` skill.

**Prompt**:

> Create `catalog/skills/github-workflow/bug-to-github-issue/SKILL.md`. This skill is the GitHub-issue-creation companion to the existing `bug-localization` skill: where `bug-localization` finds the fault, this one files it with a TDD-based fix plan.
>
> Required frontmatter (triggers: "triage this bug", "file an issue for this bug", "investigate and file", "TDD fix plan").
>
> Body sections:
>
> 1. Intro -- mostly hands-off workflow; minimize questions to the user.
> 2. "When to Use" + "When NOT to use" (do not use without a reproducible bug; use `bug-localization` first if root cause is unclear).
> 3. "Instructions" -- 5 steps: (1) capture the problem -- ONE clarifying question max if needed; (2) explore and diagnose with the `Explore` subagent (where bug manifests, code path, why it fails, related code, existing tests, recent commits to affected files); (3) identify the minimal fix approach; (4) design a TDD fix plan as a numbered list of RED-GREEN cycles -- each cycle pairs a behavior-level test with the minimal code change; include a final REFACTOR step if needed; (5) `gh issue create` with the embedded template (Problem / Root Cause Analysis / TDD Fix Plan / Acceptance Criteria). Issue body must NOT include file paths or line numbers (they go stale); describe modules, behaviors, and contracts.
> 4. "Common Rationalizations" table -- include the temptation to skip TDD and the temptation to dump file paths into the issue.
> 5. "Verification" checklist -- includes "issue is durable across refactors", "tests assert observable outcomes not internal state".
> 6. "Related Skills" -- `bug-localization` (cross-link prominently), `bug-reproduction-test-generator`, `bug-to-patch-generator`, `regression-root-cause-analyzer`, `plan-to-github-issues`, `test-driven-development`.
>
> Keep under 250 lines. Markdown-style-guide compliant.
>
> Register: add to `SKILL_INDEX.md`, `skills.json`, increment `github-workflow.skill_count` to 3, bump `total_skills`.
>
> Acceptance: `make validate` clean; cross-link to `bug-localization` resolves.

#### 3.3 -- Port `qa-session-to-issues` skill (was `qa`)

**Objective**: Create `catalog/skills/github-workflow/qa-session-to-issues/SKILL.md` -- conversational QA session where the user reports problems and the agent files durable GitHub issues using the project's domain language.

**Prompt**:

> Create `catalog/skills/github-workflow/qa-session-to-issues/SKILL.md`. The skill turns an informal QA conversation into a stream of well-formed GitHub issues, with the agent doing background codebase exploration to learn the project's domain language for each report.
>
> Required frontmatter (triggers: "QA session", "report bugs", "file issues conversationally").
>
> Body sections:
>
> 1. Intro -- per-issue loop, not a one-shot. Each issue is filed independently before the next is taken.
> 2. "When to Use" + "When NOT to use" (do not use for already-investigated single bugs -- use `bug-to-github-issue` instead).
> 3. "Instructions" -- per-issue loop with 5 steps: (1) listen and lightly clarify -- max 2-3 short clarifying questions; (2) explore the codebase in the background with an `Explore` subagent to learn the relevant area's domain language (check `UBIQUITOUS_LANGUAGE.md` if it exists) but do NOT cite files or line numbers in the eventual issue; (3) assess scope -- single issue vs. breakdown into multiple issues using vertical-slice rules; (4) file the issue(s) with `gh issue create` using the embedded templates -- do not ask the user to review first; (5) continue until the user says they are done. Embed both single-issue and breakdown templates inline. Reference the AI-disclaimer banner.
> 4. "Common Rationalizations" table -- include the temptation to over-interview.
> 5. "Verification" checklist.
> 6. "Related Skills" -- `bug-to-github-issue`, `plan-to-github-issues`, `ddd-strategic-design` (ubiquitous language angle), `github-issue-triage`.
>
> Keep under 250 lines. Markdown-style-guide compliant.
>
> Register: add to `SKILL_INDEX.md`, `skills.json`, increment `github-workflow.skill_count` to 4, bump `total_skills`.
>
> Acceptance: `make validate` clean.

#### 3.4 -- Port `refactor-rfc` skill (was `request-refactor-plan`)

**Objective**: Create `catalog/skills/github-workflow/refactor-rfc/SKILL.md` -- interview-driven refactor plan with tiny commits, filed as a GitHub issue.

**Prompt**:

> Create `catalog/skills/github-workflow/refactor-rfc/SKILL.md`. The skill turns a refactor proposal into a detailed, scoped GitHub issue, with the implementation broken into tiny commits per Martin Fowler's "make each refactoring step as small as possible, so that you can always see the program working" rule.
>
> Required frontmatter (triggers: "refactor RFC", "refactor plan as issue", "request a refactor", "scope a refactor").
>
> Body sections:
>
> 1. Intro -- this is a *planning* skill that produces a durable refactor RFC, not an implementation skill.
> 2. "When to Use" + "When NOT to use" (small refactors, single-file renames -- just do them).
> 3. "Instructions" -- numbered steps adapted from mattpocock's pattern: (1) gather a long, detailed problem description from the user; (2) explore the repo to verify their assertions; (3) ask whether other options have been considered; present alternatives; (4) interview the user about implementation in detail; (5) hammer out scope -- what changes, what does not; (6) check test coverage in the affected area; ask about test plans; (7) break implementation into tiny-commit plan, each commit leaving the codebase in a working state; (8) `gh issue create` with the embedded template (Problem Statement / Solution / Commits / Decision Document / Testing Decisions / Out of Scope / Further Notes). Do NOT include file paths or code snippets in the issue body.
> 4. "Common Rationalizations" table.
> 5. "Verification" checklist.
> 6. "Related Skills" -- `refactoring-expert`, `legacy-modernizer`, `component-boundary-identifier`, `incremental-implementation` (the implementation companion), `plan-to-github-issues`.
>
> Keep under 200 lines. Markdown-style-guide compliant.
>
> Register: add to `SKILL_INDEX.md`, `skills.json`, increment `github-workflow.skill_count` to 5, bump `total_skills`.
>
> Acceptance: `make validate` clean.

#### 3.X -- Testing and Stabilization

**Objective**: Verify Phase 3 skills load, register, and cross-link cleanly.

**Prompt**:

> Run Phase 3 verification:
>
> 1. `make validate` and `make lint`.
> 2. Reload the MCP skill server. Verify all 4 new skills are discoverable by their trigger phrases.
> 3. Verify cross-links from `bug-to-github-issue` to `bug-localization` resolve.
> 4. Spot-check that every issue-creation skill (3.1, 3.2, 3.3, 3.4) explicitly references the AI-disclaimer banner convention.
> 5. Generate session history.
>
> Fix any failures. Do not advance to Phase 4 until every gate is green.

### Phase 3 Exit Checklist

- [ ] All 4 new skills exist with progressive-disclosure frontmatter
- [ ] All registered; `github-workflow.skill_count` is 5; `total_skills` updated
- [ ] Cross-links resolve
- [ ] AI-disclaimer convention referenced consistently
- [ ] All gates green

---

## Phase 4: P1 Maintainer-Side -- GitHub Issue Triage State Machine

**Goal**: Land the larger label-state-machine skill that closes the loop on the maintainer side.

**Prerequisites**: Phase 3 complete (the issue-creation half exists).

**Stability Gate**: `github-issue-triage` registers; both reference docs (`agent-brief.md`, `out-of-scope.md`) are present and linked from the SKILL.md.

### Sub-tasks

#### 4.1 -- Port `github-issue-triage` skill

**Objective**: Create `catalog/skills/github-workflow/github-issue-triage/SKILL.md` -- a label-based GitHub issue triage state machine with `needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix` states.

**Prompt**:

> Create `catalog/skills/github-workflow/github-issue-triage/SKILL.md`. The skill triages issues in the current repo using a label-based state machine. It infers the repo from `git remote` and uses `gh` for all GitHub operations.
>
> Required frontmatter (triggers: "triage GitHub issues", "review incoming bugs", "label issues", "ready-for-agent").
>
> Body sections:
>
> 1. Intro + AI-disclaimer banner rule (every comment posted to GitHub during triage opens with `> *This was generated by AI during triage.*`).
> 2. Reference document links: `references/agent-brief.md` (covered in sub-task 4.2) and `references/out-of-scope.md` (covered in sub-task 4.3).
> 3. "Labels" table: `bug` / `enhancement` (categories); `needs-triage` / `needs-info` / `ready-for-agent` / `ready-for-human` / `wontfix` (states). Every issue must have exactly one state label and one category label.
> 4. "State Machine" table covering legal transitions, who triggers them, and what happens. Match mattpocock's transition matrix: `unlabeled` -> `needs-triage` / `ready-for-agent` / `ready-for-human` / `wontfix`; `needs-triage` -> any of the latter three or `needs-info`; `needs-info` -> `needs-triage` (when reporter replies).
> 5. "Workflows": (a) Show What Needs Attention -- query and bucket unlabeled / needs-triage / needs-info-with-new-activity issues; (b) Triage a Specific Issue -- gather context, present recommendation, attempt bug reproduction for bugs, drop into `domain-model`-style grilling if needed (cross-link to `grill-me` / `idea-refine`), apply the outcome with the appropriate comment template; (c) Quick State Override -- maintainer-driven direct label move with confirmation.
> 6. "Needs Info Output" template (Triage Notes / What we have established / What we still need from you). "Resuming Previous Sessions" rules.
> 7. "Common Rationalizations" table.
> 8. "Verification" checklist.
> 9. "Related Skills" -- `qa-session-to-issues`, `bug-to-github-issue`, `plan-to-github-issues`, `grill-me`, `bug-localization`.
>
> Keep under 350 lines (this is the largest of the ported skills; do not exceed). Markdown-style-guide compliant.
>
> Register: add to `SKILL_INDEX.md`, `skills.json`, increment `github-workflow.skill_count` to 6, bump `total_skills`.
>
> Acceptance: `make validate` clean; both reference docs present (sub-tasks 4.2 / 4.3 land them).

#### 4.2 -- Create `references/agent-brief.md` for `github-issue-triage`

**Objective**: Write the reference doc that defines what a durable agent brief looks like, used when a triaged issue moves to `ready-for-agent`.

**Prompt**:

> Create `catalog/skills/github-workflow/github-issue-triage/references/agent-brief.md`. The doc defines the standard for an agent-brief comment posted to GitHub when an issue moves to `ready-for-agent` state.
>
> Content requirements (adapt from mattpocock's `github-triage/AGENT-BRIEF.md`, do not name-credit):
>
> - The agent brief must survive radical refactors -- describe behaviors and contracts, not file paths or internal module names.
> - Required sections in the brief: What to build (vertical slice description); Acceptance criteria (observable outcomes); Domain language used (point at `UBIQUITOUS_LANGUAGE.md` or `CONTEXT.md` if present); Test guidance (what makes a good test for this work); Blocked by (if any).
> - Examples of a good vs. bad agent brief, illustrating the durability point.
> - Embed the AI-disclaimer banner rule.
>
> Keep under 100 lines. Markdown-style-guide compliant.
>
> Acceptance: file exists; cross-linked from `SKILL.md`; `make validate` clean.

#### 4.3 -- Create `references/out-of-scope.md` for `github-issue-triage`

**Objective**: Write the reference doc that defines how the `.out-of-scope/` knowledge base is maintained when an enhancement is rejected.

**Prompt**:

> Create `catalog/skills/github-workflow/github-issue-triage/references/out-of-scope.md`. The doc defines the convention for capturing rejected enhancement proposals so that future triage sessions can recognize and surface prior rejections.
>
> Content requirements (adapt from mattpocock's `github-triage/OUT-OF-SCOPE.md`):
>
> - Location: `.out-of-scope/` at the repo root, one Markdown file per rejected concept.
> - Filename: `concept-name.md` -- short, descriptive, kebab-case.
> - Required sections per file: What was proposed; Why it was rejected (the load-bearing reason); When (date); Who decided; Pointer to the original issue (if any).
> - Triage workflow: when triaging a new issue, the skill checks `.out-of-scope/*.md` for matches and surfaces any prior rejection to the maintainer ("This is similar to `.out-of-scope/<name>.md`. Do you still feel the same way?").
> - This is for *enhancements* only -- bugs marked `wontfix` are closed with a comment but do not write to `.out-of-scope/`.
>
> Keep under 100 lines. Markdown-style-guide compliant.
>
> Acceptance: file exists; cross-linked from `SKILL.md`; `make validate` clean.

#### 4.X -- Testing and Stabilization

**Objective**: Verify Phase 4 skill and reference docs are stable.

**Prompt**:

> Run Phase 4 verification:
>
> 1. `make validate` and `make lint`.
> 2. Reload MCP server. Verify `github-issue-triage` is discoverable.
> 3. Verify both reference docs are present and linked from the SKILL.md.
> 4. Markdown-style-guide compliance check on all 3 new files.
> 5. Generate session history.
>
> Fix any failures. Do not advance to Phase 5 until every gate is green.

### Phase 4 Exit Checklist

- [ ] `github-issue-triage/SKILL.md` exists, registered, validated
- [ ] `references/agent-brief.md` exists and is linked
- [ ] `references/out-of-scope.md` exists and is linked
- [ ] AI-disclaimer convention applied consistently across the github-workflow category
- [ ] All gates green

---

## Phase 5: P2 Niche-but-Good

**Goal**: Land two specialized skills that are smaller-audience but high-quality additions.

**Prerequisites**: Phase 4 complete.

**Stability Gate**: Both skills register; `caveman-mode` is correctly handled by the MCP server's `disable-model-invocation` filter; cross-link from `design-it-twice` to `competitive-generation` resolves.

### Sub-tasks

#### 5.1 -- Port `design-it-twice` skill (was `design-an-interface`)

**Objective**: Create `catalog/skills/architecture/design-it-twice/SKILL.md` -- generates multiple radically different interface designs for a module using parallel sub-agents, then compares.

**Prompt**:

> Create `catalog/skills/architecture/design-it-twice/SKILL.md`. The skill is a specialized sibling of `competitive-generation` -- where `competitive-generation` runs parallel agents on the same task and scores by rubric, `design-it-twice` is specifically about *interface* design, draws on Ousterhout's "A Philosophy of Software Design" principle that the first idea is unlikely to be the best, and forces *radical* difference between sub-agents.
>
> Required frontmatter (triggers: "design it twice", "design an interface", "compare module shapes", "interface options").
>
> Body sections:
>
> 1. Intro -- attribute the principle to Ousterhout's "Design It Twice" without crediting the source mattpocock skill (per the reverse-engineering attribution rule). Differentiate from `competitive-generation` (general scoring) and `api-design` (single-shot design).
> 2. "When to Use" + "When NOT to use" (single-method modules; trivial interfaces; cases where there is already a strong constraint forcing one shape).
> 3. "Instructions" -- 5 numbered steps: (1) gather requirements (problem, callers, key operations, constraints, what to hide); (2) generate designs in parallel sub-agents (the `Task` tool, 3-4 agents minimum) with explicitly different constraints assigned per agent (minimize method count; maximize flexibility; optimize for the most common case; specific paradigm/library inspiration) -- include a sub-agent prompt template; (3) present designs sequentially with interface signatures, usage examples, and "what it hides"; (4) compare on Ousterhout's criteria (interface simplicity, general-purpose vs specialized, implementation efficiency, depth, ease of correct use vs misuse) -- prose, not tables; (5) synthesize -- the best design often combines insights.
> 4. "Anti-Patterns" sub-section -- enforce radical difference between sub-agents; do not skip comparison; this is interface shape only, not implementation.
> 5. "Common Rationalizations" table.
> 6. "Verification" checklist.
> 7. "Related Skills" -- `competitive-generation` (cross-link prominently as the general sibling), `api-design`, `architecture-design`, `component-boundary-identifier`.
>
> Keep under 200 lines. Markdown-style-guide compliant.
>
> Register: add to `SKILL_INDEX.md` under architecture; add to `skills.json`; bump architecture `skill_count` and `total_skills`.
>
> Acceptance: `make validate` clean; cross-link to `competitive-generation` resolves.

#### 5.2 -- Port `caveman-mode` skill (with `disable-model-invocation: true`)

**Objective**: Create `catalog/skills/developer-experience/caveman-mode/SKILL.md` -- ultra-compressed agent response style (~75% token reduction) with an explicit auto-clarity exception for security warnings, irreversible actions, and multi-step sequences.

**Prompt**:

> Create `catalog/skills/developer-experience/caveman-mode/SKILL.md`. The skill is an *agent response style* mode -- the agent compresses its responses by dropping articles, filler, pleasantries, and hedging while preserving full technical accuracy. It is distinct from `context-compression` and `prompt-token-optimization` (which operate on session context, not response style).
>
> Required frontmatter -- include `disable-model-invocation: true` (this skill must NEVER auto-trigger; it activates only on explicit user request like "caveman mode", "talk like caveman", "less tokens", "be brief", or `/caveman`).
>
> Body sections:
>
> 1. Intro -- the value proposition (~75% token reduction); explicit on/off semantics.
> 2. "When to Use" + "When NOT to use" (security warnings; irreversible action confirmations -- handled by the auto-clarity exception, see below).
> 3. "Persistence" -- once triggered, active every response until the user says "stop caveman" or "normal mode". Do not drift back to verbose style mid-session.
> 4. "Rules" -- explicit: drop articles (a/an/the), filler (just/really/basically/actually/simply), pleasantries (sure/certainly/of course/happy to), hedging. Fragments OK. Short synonyms (big not extensive, fix not "implement a solution for"). Common abbreviations (DB/auth/config/req/res/fn/impl). Strip conjunctions. Use arrows for causality (X -> Y). One word when one word enough. Technical terms stay exact. Code blocks unchanged. Errors quoted exact.
> 5. "Pattern" -- show the canonical sentence pattern (`[thing] [action] [reason]. [next step].`) with a not / yes pair of examples.
> 6. **"Auto-Clarity Exception"** -- this section is load-bearing. Drop caveman temporarily for: security warnings, irreversible action confirmations, multi-step sequences where fragment order risks misread, when the user asks to clarify or repeats a question. Resume caveman after the clear part is done. Include an example of a destructive-operation warning written in normal English with caveman resume after. **PORT THIS SECTION VERBATIM** from the source pattern -- the safety semantics depend on it.
> 7. "Examples" -- 2-3 input/output pairs showing compressed-but-clear answers to technical questions.
> 8. "Common Rationalizations" table -- include the failure mode of compressing a destructive-op confirmation.
> 9. "Verification" checklist.
> 10. "Related Skills" -- `context-compression`, `prompt-token-optimization`.
>
> Keep under 150 lines. Markdown-style-guide compliant.
>
> Register: add to `SKILL_INDEX.md`, `skills.json`, bump developer-experience `skill_count` and `total_skills`.
>
> Acceptance: `make validate` clean; verify the MCP server's discovery list does NOT include `caveman-mode` (because of `disable-model-invocation: true`) but the skill IS resolvable by exact name.

#### 5.X -- Testing and Stabilization

**Objective**: Verify Phase 5 skills and the `disable-model-invocation` behavior at the catalog level.

**Prompt**:

> Run Phase 5 verification:
>
> 1. `make validate` and `make lint`.
> 2. Reload MCP server. Verify `design-it-twice` IS in the discovery list. Verify `caveman-mode` is NOT in the discovery list but IS resolvable by exact name.
> 3. Read `caveman-mode/SKILL.md` and confirm the auto-clarity exception section is present and intact.
> 4. Generate session history.
>
> Fix any failures. Do not advance to Phase 6 until every gate is green.

### Phase 5 Exit Checklist

- [ ] `design-it-twice` ported, registered, validated
- [ ] `caveman-mode` ported with `disable-model-invocation: true` and intact auto-clarity exception
- [ ] MCP server discovery filtering verified for both
- [ ] All gates green

---

## Phase 6: P3 Pattern Absorption into Existing Skills

**Goal**: Absorb three small-but-valuable patterns into existing skills with no new skill files.

**Prerequisites**: Phase 5 complete.

**Stability Gate**: Three existing SKILL.md files are updated; no registry changes (no new skills); `make validate` and Markdown-style-guide compliance hold.

### Sub-tasks

#### 6.1 -- Add Ousterhout deep-modules vocabulary + deletion test to architecture skills

**Objective**: Edit `catalog/skills/architecture/component-boundary-identifier/SKILL.md` and `catalog/skills/developer-experience/refactoring-expert/SKILL.md` to add a "Depth, Leverage, Locality, Seam" reference subsection plus the deletion test.

**Prompt**:

> Edit two existing SKILL.md files to absorb the Ousterhout deep-modules vocabulary and the deletion test.
>
> Files:
>
> - `catalog/skills/architecture/component-boundary-identifier/SKILL.md`
> - `catalog/skills/developer-experience/refactoring-expert/SKILL.md`
>
> In each file, add a new section titled "Reference: Depth, Leverage, Locality, Seam" placed after the existing "Instructions" section but before "Common Rationalizations". The section must define these terms (adapted from Ousterhout's "A Philosophy of Software Design", do not name-credit mattpocock):
>
> - **Module** -- anything with an interface and an implementation (function, class, package, slice).
> - **Interface** -- everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
> - **Implementation** -- the code inside.
> - **Depth** -- leverage at the interface: a lot of behavior behind a small interface. Deep = high leverage. Shallow = interface nearly as complex as the implementation.
> - **Seam** -- where an interface lives; a place behavior can be altered without editing in place. (Use this term, not "boundary".)
> - **Adapter** -- a concrete thing satisfying an interface at a seam.
> - **Leverage** -- what callers get from depth.
> - **Locality** -- what maintainers get from depth: change, bugs, knowledge concentrated in one place.
>
> Then add a "Deletion test" subsection: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep. Use this test when evaluating whether a refactor candidate is genuinely deepening or just rearranging.
>
> Add "One adapter = hypothetical seam. Two adapters = real seam." as a final rule of thumb.
>
> Update the existing "Boundary Quality Indicators" / equivalent section in `component-boundary-identifier` to use the new vocabulary consistently.
>
> Do NOT create a new skill. Do NOT modify the frontmatter (this is a body-content addition only). Do NOT change the registry.
>
> Run `make validate` and `make lint` -- both must remain clean. Verify Markdown-style-guide compliance (blank lines around new headings, lists, and tables).
>
> Acceptance: both files updated; vocabulary used consistently; gates green.

#### 6.2 -- Add "no horizontal slicing" anti-pattern to test-driven-development skill

**Objective**: Edit `catalog/skills/workflow/test-driven-development/SKILL.md` to add the explicit anti-pattern callout against writing all tests first then all implementation ("horizontal slicing").

**Prompt**:

> Edit `catalog/skills/workflow/test-driven-development/SKILL.md` to add an "Anti-Pattern: Horizontal Slices" section.
>
> Place the new section directly after the "What This Skill Does" / RED-GREEN-REFACTOR overview table, before "Step 1" of the existing instructions.
>
> Section content (adapted from mattpocock's `tdd/SKILL.md`, do not name-credit):
>
> 1. Open with the rule: "DO NOT write all tests first, then all implementation. This is horizontal slicing -- treating RED as 'write all tests' and GREEN as 'write all code'."
> 2. Explain the failure mode in 2-3 sentences: tests written in bulk test *imagined* behavior, not *actual* behavior; tests become insensitive to real changes; you outrun your headlights and commit to test structure before understanding the implementation.
> 3. Show the wrong vs. right pattern in a code-block diagram:
>
>     ```
>     WRONG (horizontal):
>       RED:   test1, test2, test3, test4, test5
>       GREEN: impl1, impl2, impl3, impl4, impl5
>
>     RIGHT (vertical):
>       RED->GREEN: test1->impl1
>       RED->GREEN: test2->impl2
>       RED->GREEN: test3->impl3
>       ...
>     ```
>
> 4. Close with: "Vertical slices via tracer bullets. One test -> one implementation -> repeat. Each test responds to what you learned from the previous cycle. Because you just wrote the code, you know exactly what behavior matters and how to verify it."
>
> Do NOT modify the frontmatter or any other section. Do NOT create new files.
>
> Run `make validate` and `make lint`. Markdown-style-guide compliance is mandatory (blank lines around the new heading, the explanatory list, and the code block).
>
> Acceptance: section present; gates green.

#### 6.3 -- Add "information is a DAG" + 240-char paragraph rule to writing-editing skill

**Objective**: Edit `catalog/skills/developer-experience/writing-editing/SKILL.md` to absorb two specific writing rules from mattpocock's `edit-article`.

**Prompt**:

> Edit `catalog/skills/developer-experience/writing-editing/SKILL.md` to add two rules.
>
> 1. **"Information is a DAG"** -- add a sub-section under the existing "Structure" heading. Content: "Information has dependencies. A reader cannot understand concept B if it depends on concept A and you have not explained A yet. When restructuring an article, list the major points, identify the dependency graph between them, and order sections so that every concept's prerequisites have already been introduced. Avoid forward references." Include one short example contrasting a topologically-broken section order with a fixed one.
>
> 2. **"240-character paragraph maximum"** -- add to a "Concision" or equivalent existing section. Rule: "When restructuring article-length content, cap each paragraph at 240 characters. Longer paragraphs are a smell -- they usually contain a topic shift, an unjustified aside, or a sentence that should have been its own paragraph." Note this is a heuristic for *article writing* specifically, not for every writing context (technical docs and code comments have different rules; the agent should not apply 240 chars to all output universally).
>
> Do NOT modify the frontmatter. Do NOT create new files. Do NOT change the registry.
>
> Run `make validate` and `make lint`. Markdown-style-guide compliance is mandatory.
>
> Acceptance: both rules present in the right sections; gates green.

#### 6.X -- Testing and Stabilization

**Objective**: Verify Phase 6 in-place edits are clean and do not regress catalog integrity.

**Prompt**:

> Run Phase 6 verification:
>
> 1. `make validate` and `make lint`.
> 2. Diff each of the 4 modified files against pre-phase HEAD to confirm changes are scoped (no inadvertent edits to frontmatter, no edits outside the targeted sections).
> 3. Markdown-style-guide compliance pass on each modified file.
> 4. Generate session history.
>
> Fix any failures. Do not advance to Phase 7 until every gate is green.

### Phase 6 Exit Checklist

- [ ] `component-boundary-identifier` and `refactoring-expert` updated with Ousterhout vocabulary
- [ ] `test-driven-development` updated with horizontal-slicing anti-pattern
- [ ] `writing-editing` updated with information-DAG and 240-char rules
- [ ] No frontmatter changes; no registry changes
- [ ] All gates green

---

## Phase 7: re-partial -- Husky Quick-Start in `pre-commit-checklist`

**Goal**: Add a concrete Husky + lint-staged + Prettier scaffold quick-start section to the existing security-focused `pre-commit-checklist` skill.

**Prerequisites**: Phase 6 complete.

**Stability Gate**: `pre-commit-checklist/SKILL.md` is updated with a new section; no new skill is created; `make validate` clean.

### Sub-tasks

#### 7.1 -- Add "Husky Quick-Start (TypeScript / Node)" section to `pre-commit-checklist`

**Objective**: Edit `catalog/skills/security/pre-commit-checklist/SKILL.md` to add a concrete scaffolder for the Husky + lint-staged + Prettier stack -- the gap that mattpocock's `setup-pre-commit` filled separately.

**Prompt**:

> Edit `catalog/skills/security/pre-commit-checklist/SKILL.md` to add a new section titled "Husky Quick-Start (TypeScript / Node)". Place it as a sibling section to any existing tool-specific quick-start (e.g. if the skill has a "pre-commit framework / Python" section, add this one alongside).
>
> Content (adapted from mattpocock's `setup-pre-commit/SKILL.md`, do not name-credit):
>
> 1. **Detect package manager** -- check for `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`. Default to npm if unclear.
> 2. **Install** -- `npm install --save-dev husky lint-staged prettier` (with the detected package manager substituted).
> 3. **Initialize Husky** -- `npx husky init`. Confirm `.husky/` is created and `prepare: "husky"` is added to `package.json`.
> 4. **Create `.husky/pre-commit`** -- contents (Husky v9+, no shebang needed):
>
>     ```
>     npx lint-staged
>     npm run typecheck
>     npm run test
>     ```
>
>     Substitute `npm` with the detected package manager. If `typecheck` or `test` scripts do not exist in `package.json`, omit those lines and tell the user.
> 5. **Create `.lintstagedrc`**:
>
>     ```json
>     {
>       "*": "prettier --ignore-unknown --write"
>     }
>     ```
>
> 6. **Create `.prettierrc`** (only if no Prettier config exists). Use sensible defaults: `useTabs: false`, `tabWidth: 2`, `printWidth: 80`, `singleQuote: false`, `trailingComma: "es5"`, `semi: true`, `arrowParens: "always"`.
> 7. **Verify** -- `.husky/pre-commit` exists and is executable; `.lintstagedrc` exists; `prepare` script in `package.json` is `"husky"`; Prettier config exists; `npx lint-staged` runs cleanly.
> 8. **Commit** -- the smoke test: stage all changed files and commit, which exercises the new pre-commit hook.
>
> Notes to include:
>
> - Husky v9+ does not need shebangs in hook files.
> - `prettier --ignore-unknown` skips files Prettier cannot parse (images, etc.).
> - The pre-commit runs `lint-staged` first (fast, staged-only), then full typecheck and tests.
>
> Cross-link this new section to the existing "Secret Scanning" and "Commit Message Validation" sections of the same skill -- the Husky quick-start is the *bootstrap*; the security-focused checks layer on top.
>
> Do NOT modify the frontmatter. Do NOT create new files. Do NOT change the registry.
>
> Run `make validate` and `make lint`. Markdown-style-guide compliance is mandatory (note the 4-space indent for code blocks inside list items per the style guide).
>
> Acceptance: section present; cross-links resolve; gates green.

#### 7.X -- Testing and Stabilization

**Objective**: Verify Phase 7 edit.

**Prompt**:

> Run Phase 7 verification:
>
> 1. `make validate` and `make lint`.
> 2. Diff `pre-commit-checklist/SKILL.md` against pre-phase HEAD to confirm scope.
> 3. Markdown-style-guide compliance pass -- pay special attention to the code blocks inside list items (4-space indent).
> 4. Generate session history.
>
> Fix any failures. Do not advance to Phase 8 until every gate is green.

### Phase 7 Exit Checklist

- [ ] Husky Quick-Start section present in `pre-commit-checklist/SKILL.md`
- [ ] No frontmatter or registry changes
- [ ] Markdown-style-guide compliance verified (especially indented code blocks)
- [ ] All gates green

---

## Phase 8: Final Validation, Multi-Platform Sync, Changelog, Commit

**Goal**: All gates green; `{{SKILL_INDEX}}` propagates correctly across all 5 platform templates; `CHANGELOG.md` records the adoption; one user-confirmed commit captures the entire adoption.

**Prerequisites**: Phases 1-7 complete.

**Stability Gate**: Full validation matrix (`make validate`, `make lint`, `make test`); end-to-end skill auto-invocation test on at least 3 of the new skills; `CHANGELOG.md` `[Unreleased]` entry; clean git status modulo the staged adoption changes.

### Sub-tasks

#### 8.1 -- Full validation gauntlet

**Objective**: Confirm every gate passes after all phases land.

**Prompt**:

> Run the full DevAI-Hub validation matrix in this order:
>
> 1. `make validate` -- JSON catalog integrity (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`, `data/bundles.json`).
> 2. `make lint` -- ShellCheck on all hook scripts.
> 3. `make test` -- pytest hook test suite, must pass including the new `disable-model-invocation` test from Phase 1.
> 4. Run the `extensions/devai-skill-server/` pytest suite specifically.
> 5. Run any benchmark target if applicable: `make benchmark` (skip if unchanged scope; the adoption does not introduce new MCPs, so the benchmark surface is unchanged).
>
> Fix any failure at the root cause. Do not patch around test failures.
>
> Acceptance: every gate exits 0.

#### 8.2 -- Multi-platform `{{SKILL_INDEX}}` propagation check

**Objective**: Verify the new skills appear correctly when the installer renders `{{SKILL_INDEX}}` across all 5 platform templates.

**Prompt**:

> Verify that the new skills propagate correctly to all 5 platform templates via the installer's `{{SKILL_INDEX}}` placeholder.
>
> Steps:
>
> 1. Read each of `templates/ai-instructions/base-claude.md`, `base-codex.md`, `base-cursor.md`, `base-gemini.md`, `base-opencode.md`. Confirm each has the `{{SKILL_INDEX}}` placeholder.
> 2. Do a dry-run install into a throwaway temp directory: copy `scripts/installer.sh` (or `installer.ps1` on Windows) to a sandbox and run it pointing at the temp dir. Verify the rendered output for each platform:
>     - Claude (`~/.claude/CLAUDE.md` equivalent): the new skills appear in the SKILL INDEX section.
>     - Codex, Gemini: same.
>     - Cursor (`.cursor/rules/devai-hub.mdc`) and OpenCode (`AGENTS.md`): the SKILL INDEX section is updated even though Cursor/OpenCode/Copilot do not get a per-file copy of the SKILL.md content.
> 3. Spot-check that the 9 new skills (zoom-out, grill-me, plan-to-github-issues, synthesize-prd-from-context, bug-to-github-issue, qa-session-to-issues, refactor-rfc, github-issue-triage, design-it-twice, caveman-mode) all appear in the rendered Claude index.
> 4. Spot-check that `caveman-mode` is correctly tagged as not-auto-invocable (the rendered index entry should reflect the `disable-model-invocation: true` semantic, even if just by ordering or annotation -- align with the convention chosen in Phase 1).
>
> Clean up the throwaway directory.
>
> Acceptance: all 5 platform renders include the new skills; no missing entries; no platform skipped.

#### 8.3 -- End-to-end auto-invocation spot check

**Objective**: Verify at least 3 of the new skills can be discovered and invoked by an MCP-connected agent on a sample task.

**Prompt**:

> Verify end-to-end auto-invocation for 3 of the new skills.
>
> Pick:
>
> - One small (`grill-me`)
> - One GitHub-issue-driven (`plan-to-github-issues` or `bug-to-github-issue`)
> - One `disable-model-invocation`-tagged (`caveman-mode` or `zoom-out`) -- this one verifies the *negative* case
>
> For each:
>
> 1. Start a fresh agent session with the MCP skill server connected.
> 2. For the auto-invokable skills: phrase a user request that should trigger the skill (e.g. "grill me on this plan", "break this plan into GitHub issues") and confirm the agent loads the skill at L1.
> 3. For the `disable-model-invocation`-tagged skill: phrase a user request that would *otherwise* trigger it (e.g. "explain this in fewer tokens" for `caveman-mode`) and confirm the agent does NOT auto-load it. Then explicitly invoke by name and confirm it loads.
> 4. Document each test outcome in the session history.
>
> Acceptance: 3 skills tested; auto-invocation behavior matches the frontmatter declaration; the negative test passes.

#### 8.4 -- `CHANGELOG.md` `[Unreleased]` entry

**Objective**: Document the adoption under the existing `[Unreleased]` heading.

**Prompt**:

> Add an entry to `CHANGELOG.md` under the `## [Unreleased]` heading describing this adoption.
>
> Group the entry under `### Added` (and `### Changed` for the in-place edits in Phases 6-7). Write the entries in the same style as the existing `## [1.0.0] - 2026-04-24` section -- one bullet per significant landing, with file paths cited where relevant.
>
> Suggested entries:
>
> - **Added**: `github-workflow/` skill category with 6 skills (plan-to-github-issues, synthesize-prd-from-context, bug-to-github-issue, qa-session-to-issues, refactor-rfc, github-issue-triage). Bridges DevAI-Hub planning and bug-investigation skills to durable GitHub issues.
> - **Added**: `zoom-out` and `grill-me` skills (`catalog/skills/developer-experience/`) -- short prompt primitives for zooming out and for relentless one-question-at-a-time interview loops.
> - **Added**: `design-it-twice` skill (`catalog/skills/architecture/`) -- specialized sibling of `competitive-generation` focused on parallel-sub-agent interface design per Ousterhout's "Design It Twice" principle.
> - **Added**: `caveman-mode` skill (`catalog/skills/developer-experience/`) with `disable-model-invocation: true` -- ultra-compressed agent response style with auto-clarity exception for security warnings and irreversible operations.
> - **Added**: `disable-model-invocation: true` frontmatter support in `extensions/devai-skill-server/`. Skills with this flag are loaded but not surfaced for auto-invocation; remain manually callable by name.
> - **Changed**: `component-boundary-identifier` and `refactoring-expert` -- absorbed Ousterhout deep-modules vocabulary (Depth, Leverage, Locality, Seam) and the deletion test as a refactoring lens.
> - **Changed**: `test-driven-development` -- added explicit "Anti-Pattern: Horizontal Slices" callout against writing all tests first then all implementation.
> - **Changed**: `writing-editing` -- added "information is a DAG" section-ordering rule and the 240-character paragraph cap for article-length content.
> - **Changed**: `pre-commit-checklist` -- added "Husky Quick-Start (TypeScript / Node)" scaffolder section.
>
> Cite the source comparison report at `docs/archive/v1/v1.0/comparison-mattpocock-skills.md` and the plan at `docs/archive/v1/v1.0/plans/adoption-mattpocock-skills.md`.
>
> ASCII-only (no em-dashes, en-dashes, curly quotes, or ellipsis characters) per the project rules.
>
> Run `make lint` to ensure no Markdown-style-guide regressions.
>
> Acceptance: entry present under `[Unreleased]`; ASCII-clean; no regressions.

#### 8.5 -- User-confirmed commit

**Objective**: Stage the adoption and commit with a message that captures the scope.

**Prompt**:

> Stage and commit the adoption.
>
> Steps:
>
> 1. Run `git status` to review what changed across all phases. Expected categories of change:
>     - 9 new SKILL.md files (in github-workflow/, developer-experience/, architecture/)
>     - 2 new reference docs (`agent-brief.md`, `out-of-scope.md` under github-issue-triage/)
>     - 4 modified existing skills (component-boundary-identifier, refactoring-expert, test-driven-development, writing-editing, pre-commit-checklist -- 5 actually, but counting absorption pairs as one logical change)
>     - Updated `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`
>     - Updated `extensions/devai-skill-server/` (new field support + tests)
>     - Updated `AGENTS.md` and skill-authoring guides
>     - Updated 5 platform templates if any direct change was needed (likely none -- the `{{SKILL_INDEX}}` placeholder handles propagation)
>     - Updated `CHANGELOG.md`
> 2. Run `git diff --stat` to confirm the change set is bounded as expected. Investigate any unexpected files.
> 3. **Confirm with the user** before staging and committing. The user must explicitly approve the commit per the global rule "NEVER commit changes unless the user explicitly asks you to."
> 4. Once confirmed, stage by explicit file names (do not use `git add -A` or `git add .`).
> 5. Commit with this message body (single ASCII-only message, no Co-Authored-By footer per the global rule):
>
>     ```
>     feat(skills): adopt 9 new skills + 4 absorbed patterns from comparison-mattpocock-skills
>
>     Add github-workflow/ skill category (6 skills): plan-to-github-issues,
>     synthesize-prd-from-context, bug-to-github-issue, qa-session-to-issues,
>     refactor-rfc, github-issue-triage. Add zoom-out, grill-me, design-it-twice,
>     and caveman-mode skills. Add disable-model-invocation: true frontmatter
>     support to devai-skill-server.
>
>     Absorb Ousterhout deep-modules vocabulary into component-boundary-identifier
>     and refactoring-expert. Add horizontal-slicing anti-pattern to TDD skill.
>     Add information-DAG and 240-char rules to writing-editing. Add Husky
>     quick-start to pre-commit-checklist.
>
>     See docs/archive/v1/v1.0/comparison-mattpocock-skills.md and
>     docs/archive/v1/v1.0/plans/adoption-mattpocock-skills.md.
>     ```
>
> 6. Run `git status` post-commit to confirm clean tree.
>
> Acceptance: commit lands with the user's explicit confirmation; tree is clean; CHANGELOG.md `[Unreleased]` entry is part of the commit.

#### 8.X -- Final stabilization

**Objective**: Confirm the adoption is fully stable.

**Prompt**:

> Run the final stabilization gate:
>
> 1. `make validate`, `make lint`, `make test` -- all green.
> 2. `git status` -- clean.
> 3. `git log -1` -- the adoption commit is the most recent.
> 4. Generate a final session history covering the full adoption: `/generate-session-history`.
> 5. Update `docs/todos.md` if it tracks the adoption -- check off completed items, add any newly identified follow-ups (e.g. observed gaps in the new skills that did not warrant blocking the adoption).
>
> Acceptance: all gates green; clean tree; session history captured; todos.md current.

### Phase 8 Exit Checklist

- [ ] All `make` gates green
- [ ] `{{SKILL_INDEX}}` propagation verified across all 5 platform templates
- [ ] End-to-end auto-invocation tested on 3 skills (incl. one negative `disable-model-invocation` test)
- [ ] `CHANGELOG.md` `[Unreleased]` entry landed
- [ ] User-confirmed commit landed
- [ ] Session history generated
- [ ] `docs/todos.md` updated (if applicable)

---

## Items Explicitly Out of Scope

These were rejected in Section 13 of the source comparison (`docs/archive/v1/v1.0/comparison-mattpocock-skills.md`) and remain out of scope for this plan. They are not adoptions failed by the MCP Registry Policy -- they are scope, duplication, or environmental-coupling rejections.

| # | mattpocock Skill | Why not adopted |
|---|---|---|
| N1 | `migrate-to-shoehorn` | Hyper-specific to a single TypeScript library. Out of scope for a multi-language catalog. |
| N2 | `obsidian-vault` | Personal note-management workflow against a hardcoded `/mnt/d/Obsidian Vault/` path. Not generalizable. |
| N3 | `scaffold-exercises` | Course-platform specific (`pnpm ai-hero-cli internal lint`). Not applicable. |
| N4 | `write-a-skill` | Functionally duplicated by `create-skill-or-command` and `create-custom-command`. |
| N5 | `git-guardrails-claude-code` | Already shipped as a registered PreToolUse hook (`catalog/hooks/git-guardrails.sh`) covering all of mattpocock's patterns and 2 more. |
| N6 | `ubiquitous-language` | Glossary extraction is fully covered by `ddd-strategic-design`. The interactive `domain-model` flavor is partially absorbed by `idea-refine` and `spec-driven-development` Phase 1. |
| N7 | `edit-article` (full skill) | The two specific rules worth absorbing are landed in sub-task 6.3; the rest of the skill is duplicative of `writing-editing`. |
