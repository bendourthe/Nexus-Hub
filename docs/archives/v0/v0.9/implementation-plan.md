# Implementation Plan - v0.9.7

**Project**: DevAI-Hub
**Version**: 0.9.7 (patch/minor release)
**Created**: 2026-04-21
**Goal**: Close all 22 gaps surfaced by the three v0.9.6 comparison documents (session management, Opus 4.7 best practices, red-team audit), bringing DevAI-Hub into alignment with current Anthropic guidance and expanding security coverage.

---

## Context

Three gap analyses were produced during v0.9.6 and saved to [docs/v0.9.6/](docs/v0.9.6/):

1. [comparison-claude-code-session-management-1m-context.md](docs/v0.9.6/comparison-claude-code-session-management-1m-context.md) - gaps against Anthropic's session-management / 1M-context guidance.
2. [comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md](docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md) - gaps against the Opus 4.7 best-practices blog post.
3. [comparison-x-post-security-audit-prompt.md](docs/v0.9.6/comparison-x-post-security-audit-prompt.md) - red-team mindset gaps versus the current `/run-penetration-test` command.

Together the three documents produced **22 deduplicated recommendations** spanning P0 reconciliation fixes, P1 behavioral adaptations for Opus 4.7, P1/P2 new security skills, P2/P3 skill extensions, and a P3 VS Code extension UI improvement. The most important issues are a **factual inconsistency** between [catalog/hooks/settings.json](catalog/hooks/settings.json) (`xhigh`) and [CHANGELOG.md](CHANGELOG.md) line 27 (claims `high`), and the **absence of any codified guidance** on Opus 4.7's effort-level hierarchy and reasoning-over-tools posture - both of which materially affect how every operator configures the harness.

This plan targets a **v0.9.7 patch release** that delivers all 22 recommendations in six sequenced phases. Each phase has an explicit Stability Gate and an exit checklist. All SKILL.md, command, and guide artifacts are platform-neutral (shared via `catalog/`); only the five platform base templates in [templates/ai-instructions/](templates/ai-instructions/) require mirrored edits (Phase 1.5 specifically).

**Final destination for this plan after approval**: `docs/v0.9.7/implementation-plan.md`

---

## Phases at a Glance

| Phase | Title | Priority Mix | Sub-tasks | Outcome |
|-------|-------|--------------|-----------|---------|
| 1 | Reconciliation & Anchor Documents | P0 x6 | 7 | Effort-level drift resolved; Session Lifecycle guide, Effort-level guide, and clarifying-questions rule live across all 5 platform templates |
| 2 | Opus 4.7 Behavioral Skill Extensions | P1 x5 | 6 | Prompt-engineering, ai-agent-development, multi-agent-coordinator, context-compression aligned with Opus 4.7 reasoning-first behavior |
| 3 | Security Expansion (Business Logic + Advanced Attacks) | P1 x1, P2 x2, P3 x3 | 5 | Two new security skills, `/run-penetration-test` 6th-hunter slot, terminology polish, file-upload checklist |
| 4 | Context Calibrations & Migration Notes | P2 x2, P3 x1 | 4 | 1M-window calibration in context-degradation, "summarize from here" session-history mode, Opus 4.6->4.7 migration notes |
| 5 | VS Code Extension Settings Panel | P3 x1 | 3 | Effort-level hover help surfaces definitions inside the extension UI |
| 6 | Documentation Sync & v0.9.7 Release | Release | 6 | CATALOG-COVERAGE, CHANGELOG, version bump, DEVLOG, platform-parity audit, release tag |

Total: **31 sub-tasks** (including testing/stabilization checkpoints). VS Code extension work in Phase 5 is the only phase with externally visible UI changes; all others are catalog and docs.

---

## Phase 1: Reconciliation & Anchor Documents

**Goal**: Fix the factual drift between `settings.json` and `CHANGELOG`, and publish the two anchor documents (Session Lifecycle Decisions guide, Effort-Level Decision guide) that later phases cross-link to.

**Prerequisites**: None.

**Stability Gate**: `catalog/hooks/settings.json` and `CHANGELOG.md` agree on the canonical effort-level default. `guides/SESSION_LIFECYCLE_DECISIONS.md` exists and is cross-linked from `TOKEN_OPTIMIZATION.md` and at least three relevant orchestration/workflow skills. All five platform templates contain the updated "batch clarifying questions" rule. `ruff`/`shellcheck`/platform-specific lints green. Manual spot-read of each new document passes.

### Sub-tasks

#### 1.1 - Reconcile effort-level drift (settings.json vs CHANGELOG)

**Objective**: Eliminate the factual inconsistency flagged in comparison-doc-2 where [catalog/hooks/settings.json](catalog/hooks/settings.json) declares `"effortLevel": "xhigh"` while [CHANGELOG.md](CHANGELOG.md) v0.9.6 line 27 claims the installer default was changed to `high`.

**Prompt**:
> Fix the factual inconsistency between `catalog/hooks/settings.json` (`effortLevel: xhigh`) and `CHANGELOG.md` line 27 (claims v0.9.6 installer default changed to `high`) identified in `docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md` under P0.1.
>
> Steps:
> 1. Open `catalog/hooks/settings.json` and confirm the current `effortLevel` value.
> 2. Open `CHANGELOG.md` and read the v0.9.6 entry around line 27.
> 3. Open `install.sh` and `install.bat` to find where `effortLevel` is written into generated settings during install.
> 4. Decide the canonical value. **Default recommendation**: keep `xhigh` as the shipped default since it reflects current Opus 4.7 best-practice guidance (per the Anthropic blog post referenced in the comparison doc). Update the CHANGELOG v0.9.6 entry to accurately describe what was shipped.
> 5. Alternative path: if the team prefers `high` as a lower-cost safer default, update `catalog/hooks/settings.json` and both installer scripts to write `high` and keep the CHANGELOG entry as-is.
> 6. Add a short "Correction" note at the top of the v0.9.7 CHANGELOG section explaining the reconciliation.
> 7. Search `docs/` and `guides/` for any other mention of `effortLevel` values and align them.
>
> Acceptance:
> - `catalog/hooks/settings.json`, `install.sh`, `install.bat`, and the CHANGELOG all reference the same canonical value.
> - No guide or skill contradicts the canonical value.
> - Commit message: `fix(settings): reconcile effort-level default between hooks and changelog`.

---

#### 1.2 - Create Session Lifecycle Decisions guide

**Objective**: Publish the P0 anchor guide codifying the five-branch session-lifecycle decision tree (continue / rewind / clear / compact / subagent) that all downstream session-management guidance references.

**Prompt**:
> Create `guides/SESSION_LIFECYCLE_DECISIONS.md` codifying the five-branch decision tree from Anthropic's session-management / 1M-context guidance summarized in `docs/v0.9.6/comparison-claude-code-session-management-1m-context.md` (insight 5, 6, 7).
>
> Sections to include (in this order):
> 1. **When to start a new session**: default is "new task = new session". Exception: documentation-after-implementation (preserve context from the work being documented).
> 2. **When to `/rewind`**: after a bad turn, before re-approaching the same problem with new context. Include the "summarize from here" handoff pattern (generate a summary message just before `/rewind`, paste it as first message of the rewound session).
> 3. **When to `/clear`**: full context reset; use when switching to an unrelated task in the same repo.
> 4. **When to `/compact`**: proactive context management when approaching 70-80% capacity or when the conversation is long but still on-topic. Include the steerable variant: `/compact focus on X, drop Y`.
> 5. **When to delegate to a subagent**: apply the "will I need this tool output again, or just the conclusion?" mental test. If only the conclusion is needed, delegate.
>
> Include a decision flowchart (ASCII or mermaid). Include three worked examples:
> - Finished feature, now writing docs -> keep context (exception).
> - Debugging went off-rails 6 turns ago -> summarize-then-`/rewind`.
> - Large codebase exploration to answer one question -> delegate to subagent.
>
> Cross-link from the top of `guides/TOKEN_OPTIMIZATION.md` and from the Instructions section of these skills: `catalog/skills/orchestration/context-manager/SKILL.md`, `catalog/skills/orchestration/context-compression/SKILL.md`, `catalog/skills/workflow/session-history/SKILL.md`.
>
> Cite the Anthropic blog post as the source (no canonical URL available; note it in a "Sources" footer).
>
> Acceptance: guide is <= 400 lines, every branch has a worked example, flowchart renders correctly.

---

#### 1.3 - Create Effort-Level Decision guide (extend prompt-engineering skill)

**Objective**: Publish the P0 effort-level hierarchy covering all five tiers (xhigh / high / max / medium / low) with decision rules, as a new section inside the existing prompt-engineering skill.

**Prompt**:
> Extend `catalog/skills/ai-development/prompt-engineering/SKILL.md` with a new top-level section titled **"Effort-Level Strategy"** synthesizing insights 1-4 and 13 from `docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md`.
>
> Structure:
> 1. **The five tiers**: `xhigh`, `high`, `max`, `medium`, `low` - one-line description of what each does and typical token/latency cost.
> 2. **Default**: `xhigh` is the DevAI-Hub shipped default (reference the canonical value reconciled in 1.1).
> 3. **When to escalate to `max`**: hard problems, one-shot deep analysis, off-peak when cost is not sensitive. **Never** use `max` on extended agentic runs or loops.
> 4. **When to de-escalate to `high`**: cost-sensitive concurrent work, multi-agent fan-out.
> 5. **When to use `medium` or `low`**: latency-sensitive interactive work, tightly scoped tasks where reasoning overhead is wasted.
> 6. **Anti-patterns**: defaulting to `max`, leaving `max` on for loop-operator / temporal runs, mixing effort levels within a single session without reason.
> 7. **Decision table**: task type x effort tier with recommended setting.
>
> Cross-link from:
> - `catalog/skills/ai-development/ai-agent-development/SKILL.md` (new Anti-Patterns section in 2.2)
> - `catalog/agents/loop-operator.md` (add a note: "default to `high`, never `max` for multi-iteration runs")
> - `catalog/skills/orchestration/temporal-orchestration/SKILL.md` (same note)
>
> Do NOT create a separate `effort-level-strategy` skill - keep it as a section in `prompt-engineering` to avoid fragmentation.
>
> Acceptance: section is <= 150 lines, decision table is machine-readable markdown, all cross-links resolve.

---

#### 1.4 - Extend TOKEN_OPTIMIZATION.md with "When NOT to compact" subsection

**Objective**: Add the P0 subsection to [guides/TOKEN_OPTIMIZATION.md](guides/TOKEN_OPTIMIZATION.md) that names the "bad compact" failure mode and prescribes proactive steering.

**Prompt**:
> Add a new subsection titled **"When NOT to compact"** under the existing "Auto-Compaction" heading in `guides/TOKEN_OPTIMIZATION.md`, covering insights 10, 12, and 13 from `docs/v0.9.6/comparison-claude-code-session-management-1m-context.md`.
>
> Content:
> 1. **The bad-compact failure mode**: autocompact fires mid-reasoning, dropping context Claude was about to use. Symptoms: sudden drop in response quality, repeated re-analysis of files, "what were we working on" style recovery turns.
> 2. **Three recognition signals** that you're about to hit a bad compact: (a) approaching 70-80% capacity with a long-running complex task, (b) mid-tool-use-chain, (c) recently loaded large files or web fetches you still need.
> 3. **Proactive remedy**: use `/compact focus on <current-work>, drop <closed-threads>` *before* hitting the auto-threshold. Example: `/compact focus on the auth refactor, drop the DB schema discussion from earlier`.
> 4. **When to just `/clear` instead**: if the current task is complete and the next task is unrelated.
>
> Cross-link to `guides/SESSION_LIFECYCLE_DECISIONS.md` (created in 1.2) at the top of the new subsection.
>
> Acceptance: subsection is 30-50 lines, one concrete example per recognition signal, cross-link resolves.

---

#### 1.5 - Apply "batch clarifying questions" rule across 5 platform templates

**Objective**: Update all five platform base templates so the "ask clarifying questions" rule batches questions into the first turn (Opus 4.7 best-practice) rather than permitting unbounded per-question round-trips.

**Prompt**:
> Update the **Critical Rules** section in each of the five platform base templates to replace the current unbounded clarifying-questions rule with a batched variant, per insight 8 from `docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md`.
>
> Files to update (all in `templates/ai-instructions/`):
> - `base-claude.md`
> - `base-gemini.md`
> - `base-codex.md`
> - `base-cursor.md`
> - `base-opencode.md`
>
> Find the existing rule that resembles: *"Ask clarifying questions before coding if requirements are ambiguous; state assumptions explicitly..."*
>
> Replace with:
> > "If requirements are ambiguous, **batch all clarifying questions into the first turn** rather than asking one question per turn. Surface multiple interpretations and acceptance criteria together so the user can answer them in a single round-trip. State any assumptions explicitly before acting. Avoid unbounded per-question ping-pong - it wastes context and Opus 4.7's reasoning budget."
>
> Preserve the intent of "surface multiple interpretations" and "state assumptions explicitly" from the original rule.
>
> Also update the global `C:\Users\BEDOURTHE\.claude\CLAUDE.md` (user's global instructions) if the same rule appears there - coordinate with the user before modifying the global file.
>
> Acceptance: `grep -rn "clarifying questions" templates/ai-instructions/` shows the new rule wording in all 5 files. No template still contains the unbounded variant.

---

#### 1.6 - Cross-link anchor documents from related skills

**Objective**: Ensure every orchestration/workflow skill that touches session management links to `SESSION_LIFECYCLE_DECISIONS.md` and the new effort-level section.

**Prompt**:
> Audit the following skills and guides for references to session management, compaction, context reset, or effort-level choices, and add cross-links to the newly created anchor documents from 1.2 and 1.3. Do not restructure the skills - just add "See also" links in relevant sections.
>
> Files to audit:
> - `catalog/skills/orchestration/context-manager/SKILL.md`
> - `catalog/skills/orchestration/context-compression/SKILL.md`
> - `catalog/skills/orchestration/context-degradation/SKILL.md`
> - `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md`
> - `catalog/skills/workflow/session-history/SKILL.md`
> - `catalog/skills/workflow/continue-session/SKILL.md` (if it exists)
> - `guides/TOKEN_OPTIMIZATION.md`
> - `guides/CLAUDE_CODE_GUIDE.md`
> - `guides/SUBAGENTS_GUIDE.md`
>
> Add at most one "See also: [SESSION_LIFECYCLE_DECISIONS](../../../guides/SESSION_LIFECYCLE_DECISIONS.md)" line per file in the most relevant section.
>
> Acceptance: each file has at most one cross-link added, links resolve relative to the file location.

---

#### 1.7 - Testing and Stabilization (Phase 1)

**Objective**: Verify Phase 1 artifacts are internally consistent and platform-parity holds.

**Prompt**:
> Verify Phase 1 deliverables:
> 1. Run `grep -rn "effortLevel" catalog/ install.sh install.bat CHANGELOG.md docs/ guides/` and confirm every hit references the same canonical value decided in 1.1.
> 2. Confirm `guides/SESSION_LIFECYCLE_DECISIONS.md` exists and the flowchart renders (if mermaid, validate via a markdown preview).
> 3. Confirm the "Effort-Level Strategy" section of `catalog/skills/ai-development/prompt-engineering/SKILL.md` includes all five tiers and the decision table.
> 4. Confirm `guides/TOKEN_OPTIMIZATION.md` contains the "When NOT to compact" subsection with all three signals.
> 5. Confirm all 5 platform templates in `templates/ai-instructions/` contain the batched clarifying-questions rule (grep for "batch").
> 6. Run any project lint: `shellcheck install.sh`, `ruff check .` if Python scripts were touched, markdown-lint on guides if configured.
> 7. Verify all cross-links resolve (use a link-checker or manual spot-check).
> 8. Commit each sub-task as a separate commit with conventional-commit prefix.
> 9. After all Phase 1 work passes, run `/generate-session-history` to document Phase 1.
>
> Do not advance to Phase 2 until every item above is green.

---

### Phase 1 Exit Checklist

- [ ] 1.1 - Effort-level drift reconciled; settings.json, installers, and CHANGELOG align
- [ ] 1.2 - `guides/SESSION_LIFECYCLE_DECISIONS.md` created with all five branches and worked examples
- [ ] 1.3 - Effort-Level Strategy section added to `prompt-engineering` skill
- [ ] 1.4 - "When NOT to compact" subsection added to `TOKEN_OPTIMIZATION.md`
- [ ] 1.5 - Batched clarifying-questions rule applied to all 5 platform templates
- [ ] 1.6 - Cross-links added from relevant skills/guides to anchor documents
- [ ] 1.7 - Phase 1 session history generated
- [ ] No lint failures, all cross-links resolve
- [ ] Ready to advance to Phase 2

---

## Phase 2: Opus 4.7 Behavioral Skill Extensions

**Goal**: Align the prompt-engineering, ai-agent-development, multi-agent-coordinator, and context-compression skills with Opus 4.7's reasoning-first posture and explicit-fan-out requirement.

**Prerequisites**: Phase 1 complete (effort-level guide exists and is referenced from these skills).

**Stability Gate**: Each of the four target skills has new content with the correct tone, cross-links to 1.3 Effort-Level Strategy section, and does not contradict Phase 1 anchor documents. Skill metadata validates against the DevAI-Hub SKILL.md schema.

### Sub-tasks

#### 2.1 - Extend prompt-engineering with four Opus 4.7 practice areas

**Objective**: Add four practice areas to `prompt-engineering` covering positive-example framing, explicit tool-invocation prompting, adaptive thinking (no fixed budgets), and first-turn specification checklists.

**Prompt**:
> Extend `catalog/skills/ai-development/prompt-engineering/SKILL.md` with four new practice sections, per insights 5, 6, 7, and 10 of `docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md`.
>
> Sections to add (under a new **"Opus 4.7 Practices"** heading, placed after the "Effort-Level Strategy" section from 1.3):
>
> 1. **Positive examples over negative instructions**
>    - Rule: tell the model what *to* do, not what *not* to do.
>    - Example pair: bad ("don't use class components") vs good ("use function components with hooks").
>
> 2. **Explicit tool-invocation prompts**
>    - Rule: Opus 4.7 no longer infers tool use as readily as 4.6; name the tool or action explicitly when you want it invoked.
>    - Example pair: bad ("check for issues") vs good ("run `ruff check .` and report violations").
>
> 3. **Adaptive thinking without fixed budgets**
>    - Rule: do NOT set fixed thinking-budget tokens; let the model scale reasoning to the task.
>    - Prompting pattern: "think through this carefully" rather than "use 20k thinking tokens".
>
> 4. **First-turn specification checklists**
>    - Rule: put goal, constraints, acceptance criteria, and out-of-scope items in the first turn. Link to `catalog/skills/workflow/plan-before-code/SKILL.md` and `catalog/skills/developer-experience/spec-driven-development/SKILL.md`.
>    - Template: a 5-bullet first-turn skeleton users can copy.
>
> Each section should be 25-40 lines including examples.
>
> Acceptance: four sections present, each with at least one before/after example, cross-links to plan-before-code and spec-driven-development resolve.

---

#### 2.2 - Add Anti-Patterns section to ai-agent-development

**Objective**: Document three Opus 4.7 anti-patterns in `ai-agent-development` using the existing "Common Rationalizations" table pattern.

**Prompt**:
> Add a new **"Anti-Patterns (Opus 4.7)"** section to `catalog/skills/ai-development/ai-agent-development/SKILL.md` per insights 10, 11, 13 of `docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md`.
>
> Use the existing "Common Rationalizations" table pattern already present in the skill. Three rows:
>
> | Anti-pattern | Why it feels right | Why it's wrong in Opus 4.7 | What to do instead |
> |---|---|---|---|
> | Fixed thinking budgets | "Predictable cost" | Model scales thinking adaptively; fixed budgets truncate reasoning | Omit thinking-budget params; set `effortLevel` instead |
> | Excessive tool-calling | "Thorough investigation" | Opus 4.7 prefers reasoning; too many tool calls burn tokens without adding signal | Reason first; invoke tools only when external state is needed |
> | `max` effort on extended runs | "Best results always" | `max` across a long loop compounds cost and rarely outperforms `xhigh` | Default `xhigh` for runs; reserve `max` for single hard analyses |
>
> Cross-link to:
> - Effort-Level Strategy section from 1.3
> - `catalog/skills/orchestration/prompt-token-optimization/SKILL.md` (which focuses on output compression, not tool frequency)
>
> Acceptance: table renders, all three rows present, cross-links resolve.

---

#### 2.3 - Update multi-agent-coordinator for Opus 4.7 explicit fan-out

**Objective**: Rewrite the parallelism section of `multi-agent-coordinator` to reflect Opus 4.7's requirement for explicit fan-out prompting.

**Prompt**:
> Update `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` per insight 12 of `docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md`.
>
> Find the existing section on parallel subagents and add a prominent note (callout or "Opus 4.7 behavior" subsection):
>
> > "**Opus 4.7 requires explicit parallel fan-out.** Unlike 4.6, Opus 4.7 does not volunteer concurrent subagent spawning. If you want N agents to work in parallel, prompt explicitly: 'Spawn 3 subagents in parallel: one to do X, one to do Y, one to do Z. Send them in a single message.'"
>
> Add three concrete example prompt patterns:
> 1. **Research fan-out**: "Spawn 3 Explore agents in parallel: A searches for X, B searches for Y, C searches for Z."
> 2. **Code generation fan-out**: "Run 2 implementation agents in parallel on branches A and B."
> 3. **Verification fan-out**: "Run an adversarial-verifier agent and a code-reviewer agent in parallel on the pending diff."
>
> Cross-link to:
> - Effort-Level Strategy section (1.3) with note: "for parallel fan-out, default to `high` not `xhigh` to control aggregate cost".
> - `catalog/skills/orchestration/competitive-generation/SKILL.md`.
>
> Acceptance: explicit-fan-out callout present, three example patterns documented, cross-links resolve.

---

#### 2.4 - Add subagent reuse-test to multi-agent-coordinator

**Objective**: Add the "will I need this tool output again?" decision gate (Doc 1, insight 14).

**Prompt**:
> In `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md`, add a new section at the top of the Instructions body (before the existing patterns) titled **"Should I delegate to a subagent?"** per insight 14 of `docs/v0.9.6/comparison-claude-code-session-management-1m-context.md`.
>
> Content:
> 1. **The reuse test**: "Will I need this tool output again later in the session, or just the conclusion?" If only the conclusion is needed -> delegate. If the raw output will be re-referenced -> run it in the main session.
> 2. **Three delegation patterns as worked examples**:
>    - *Verify with subagent*: "Have an agent run tests and report pass/fail. I keep only the conclusion."
>    - *Summarize other codebase*: "Agent explores a large external repo and returns a 1-page summary. I keep the summary."
>    - *Write docs from diff*: "Agent reads the full diff, writes the CHANGELOG entry, and returns only the entry."
>
> Note: this sub-task is adjacent to 2.3 (both edit the same file). Apply 2.3 first, then 2.4, to avoid merge noise.
>
> Acceptance: section is 30-50 lines, three worked examples present.

---

#### 2.5 - Extend context-compression with proactive steering

**Objective**: Extend Step 2 of `context-compression` to teach the `/compact focus on X, drop Y` pattern.

**Prompt**:
> Extend Step 2 ("Select Compression Approach") of `catalog/skills/orchestration/context-compression/SKILL.md` with a new subsection titled **"Proactive steering with `/compact focus on X, drop Y`"** per insights 10 and 13 of `docs/v0.9.6/comparison-claude-code-session-management-1m-context.md`.
>
> Content:
> 1. **When to steer proactively**: before hitting 70-80% context capacity on a long-running task - do not wait for autocompact.
> 2. **Syntax**: `/compact focus on <current work>, drop <closed threads>`.
> 3. **Common pre-compaction directives** (bulleted list of 5-8 examples):
>    - `/compact focus on the auth refactor, drop the DB schema discussion`
>    - `/compact focus on the failing tests, drop the exploration phase`
>    - `/compact focus on the latest 3 files touched, drop earlier unrelated analysis`
>    - `/compact focus on the plan, drop the research outputs I no longer need`
>    - etc.
> 4. **Cross-link to `guides/SESSION_LIFECYCLE_DECISIONS.md`** at the top of the subsection.
>
> Acceptance: subsection is 40-60 lines, directives list has at least 5 concrete examples, cross-link to Phase 1 anchor resolves.

---

#### 2.6 - Testing and Stabilization (Phase 2)

**Objective**: Verify Phase 2 skills are coherent, consistent with Phase 1 anchors, and do not duplicate or contradict each other.

**Prompt**:
> Verify Phase 2:
> 1. Run the project SKILL.md validator (if one exists) or manually spot-check frontmatter (`name`, `description`, `category`) for each modified skill.
> 2. Confirm every new section has at least one worked example.
> 3. Confirm no section contradicts the Effort-Level Strategy (1.3) or the Session Lifecycle Decisions guide (1.2).
> 4. Run `grep -rn "thinking budget\|fixed thinking" catalog/skills/` - the only references should be in 2.2 Anti-Patterns context.
> 5. Confirm cross-links from the four modified skills all resolve.
> 6. Commit each sub-task separately.
> 7. Run `/generate-session-history` to document Phase 2.

---

### Phase 2 Exit Checklist

- [ ] 2.1 - Four Opus 4.7 practice sections added to prompt-engineering
- [ ] 2.2 - Anti-Patterns table added to ai-agent-development
- [ ] 2.3 - Explicit fan-out callout added to multi-agent-coordinator
- [ ] 2.4 - Subagent reuse-test section added to multi-agent-coordinator
- [ ] 2.5 - Proactive-steering subsection added to context-compression
- [ ] 2.6 - Phase 2 session history generated
- [ ] All cross-links resolve, SKILL.md frontmatter validates
- [ ] Ready to advance to Phase 3

---

## Phase 3: Security Expansion (Business Logic + Advanced Attacks)

**Goal**: Ship two new security skills (business-logic-abuse, advanced-attack-patterns), extend `/run-penetration-test` with a 6th hunter slot plus terminology polish, and publish a file-upload security checklist.

**Prerequisites**: Phase 1 complete (effort-level guidance is needed because the pen-test hunter fan-out should default to `high` not `xhigh` for cost reasons).

**Stability Gate**: Both new skills exist with complete SKILL.md frontmatter and are listed in `docs/CATALOG-COVERAGE.md` (updated in Phase 6). `/run-penetration-test` Phase 2 fan-out includes the 6th hunter slot gated behind `--depth=deep`. WSTG Coverage Matrix in the command includes new entries for business-logic-abuse and advanced-attack-patterns.

### Sub-tasks

#### 3.1 - Create business-logic-abuse skill

**Objective**: New P1 skill covering race conditions, TOCTOU, double-spending, workflow-state bypass, idempotency violations, and check-sequence abuse (Doc 3, insight 22).

**Prompt**:
> Create `catalog/skills/security/business-logic-abuse/SKILL.md` per the P1 recommendation in `docs/v0.9.6/comparison-x-post-security-audit-prompt.md` (gap: item 22).
>
> Frontmatter:
> - `name: business-logic-abuse`
> - `category: security`
> - `description: "Identify business-logic vulnerabilities: race conditions, TOCTOU, double-spending, workflow bypass, and idempotency violations - requires domain knowledge"`
>
> Instructions structure:
> 1. **Scope and caveat**: this skill requires domain knowledge of the application's business rules. Start by asking the user for (a) high-value workflows, (b) critical invariants (e.g., "balance cannot go negative"), (c) idempotency guarantees.
> 2. **Attack classes** (one subsection each, 20-30 lines):
>    - Race conditions (concurrent request ordering)
>    - TOCTOU (time-of-check-time-of-use)
>    - Double-spending / replay-within-window
>    - Workflow-state bypass (skip required step via direct endpoint)
>    - Idempotency violations (same request produces different results)
>    - Check-sequence abuse (validate X then act on Y)
> 3. **Review procedure**: for each elicited business rule, trace the code path; identify atomicity boundaries; flag missing locks, missing idempotency keys, missing state-machine guards.
> 4. **Output format**: findings table with severity, rule violated, code reference, reproduction sketch, remediation.
>
> Follow the same SKILL.md structural conventions as existing security skills (e.g., `catalog/skills/security/authentication-patterns/SKILL.md`). Match the house style.
>
> Add a WSTG Coverage Matrix entry row in `catalog/commands/run-penetration-test.md` mapping this skill to WSTG-BUSL-* test cases.
>
> Acceptance: SKILL.md parses as valid markdown with valid frontmatter, has all 6 attack classes, links into the pen-test command.

---

#### 3.2 - Create advanced-attack-patterns skill

**Objective**: New P2 skill covering state desynchronization, cache poisoning, replay attacks, and expanded timing-attack surfaces (Doc 3, insights 32-35).

**Prompt**:
> Create `catalog/skills/security/advanced-attack-patterns/SKILL.md` covering P2 items 32-35 from `docs/v0.9.6/comparison-x-post-security-audit-prompt.md`.
>
> Frontmatter:
> - `name: advanced-attack-patterns`
> - `category: security`
> - `description: "Advanced attack classes: state desynchronization, cache poisoning, replay attacks, and timing-attack side channels beyond password comparison"`
>
> Instructions: four sections, ~30 lines each, each gated on an applicability check.
>
> 1. **State desynchronization** (insight 32)
>    - Applicability: distributed systems, multi-step workflows, eventual-consistency stores.
>    - Patterns: client/server state divergence, cache vs DB divergence, step-skip via direct endpoint.
>    - Remediation: transactional boundaries, server-authoritative state.
>
> 2. **Cache poisoning** (insight 33)
>    - Applicability: any HTTP caching layer (CDN, reverse proxy, application cache).
>    - Patterns: unkeyed inputs in cache key, incorrect `Vary` headers, cache-injection via header manipulation, cache-deception.
>    - Remediation: cache-key hygiene, strict `Vary` lists, normalize inputs.
>
> 3. **Replay attacks** (insight 34)
>    - Applicability: any request carrying auth or state-changing semantics.
>    - Patterns: missing nonces, missing idempotency keys, no timestamp window, token-binding absent.
>    - Remediation: idempotency keys, nonce stores with TTL, timestamp + max-skew validation.
>
> 4. **Timing attack surfaces** (insight 35)
>    - Applicability: any comparison of user input to a secret; any branch whose duration depends on input validity.
>    - Patterns beyond password comparison: user-enumeration via login-response timing, token-lookup timing, crypto side channels (RSA decryption variance, etc.).
>    - Remediation: constant-time comparators, uniform response times for enumeration-sensitive endpoints.
>
> Add WSTG Coverage Matrix row in `catalog/commands/run-penetration-test.md`.
>
> Acceptance: SKILL.md has 4 sections, each with applicability/patterns/remediation, each gated.

---

#### 3.3 - Extend /run-penetration-test with 6th hunter, matrix, terminology, design-rec section

**Objective**: Wire the two new skills into `/run-penetration-test` and apply P3 polish in the same pass.

**Prompt**:
> Extend `catalog/commands/run-penetration-test.md` with the following changes from `docs/v0.9.6/comparison-x-post-security-audit-prompt.md` (insights 22, 32-35, 37):
>
> 1. **Add 6th hunter slot** (P2, insight 22+32-35): extend the Phase 2 fan-out to optionally spawn a "Business Logic & Advanced Attacks" hunter that invokes both `business-logic-abuse` (3.1) and `advanced-attack-patterns` (3.2) skills. Gate behind `--depth=deep` CLI flag to control token cost (~20% increase). Document the flag in the command's Usage section.
>
> 2. **Update WSTG Coverage Matrix**: add rows for WSTG-BUSL-* (business-logic) and for cache-poisoning / replay / timing-attack categories, each referencing the new skills.
>
> 3. **Rename "Attack Paths" to "Attack Paths / Chains"** (P3, insight 37) in the report-output template around line 690 (verify line number).
>
> 4. **Add "Secure Design Recommendations" subsection** (P3, insight 37) to the report-output template, separate from per-finding remediation and the project-wide Roadmap. Scope: architectural-pattern recommendations (e.g., "centralize authorization in a policy middleware"). Place after the per-finding remediation block, before the Roadmap.
>
> 5. **Set default `effortLevel` for hunter agents to `high`** (not `xhigh`) because fan-out cost compounds. Cross-reference the Effort-Level Strategy section (1.3).
>
> Acceptance: `--depth=deep` documented, both new skills invoked when flag is set, WSTG matrix includes new rows, terminology renamed, Secure Design Recommendations subsection renders in report, effort-level default justified.

---

#### 3.4 - File-upload security checklist

**Objective**: P3 file-upload checklist (Doc 3, insight 14) covering polyglot files, MIME confusion, archive path traversal, content-length limits, AV scanning.

**Prompt**:
> Create `catalog/checklists/file-upload-security.md` (create `catalog/checklists/` directory if it does not exist) per P3 item 14 of `docs/v0.9.6/comparison-x-post-security-audit-prompt.md`.
>
> Frontmatter (match DevAI-Hub checklist conventions if any exist; otherwise use the SKILL.md frontmatter style minus `category`):
> - `name: file-upload-security`
> - `description: "Checklist of defenses against file-upload-specific exploits"`
>
> Content: bulleted checklist grouped by attack class.
>
> 1. **File-type validation**
>    - [ ] Validate MIME by content sniffing, not trust `Content-Type` header
>    - [ ] Reject polyglot files (e.g., JPG that is also valid HTML)
>    - [ ] Normalize extension; reject double-extensions (`file.jpg.php`)
>
> 2. **Path handling**
>    - [ ] Generate server-side filenames; never trust user-supplied names
>    - [ ] For archives (zip/tar): detect path-traversal entries before extraction
>    - [ ] Extract into chroot or equivalent isolated root
>
> 3. **Size & resource limits**
>    - [ ] Enforce content-length limit at reverse proxy AND application
>    - [ ] Enforce per-user quota
>    - [ ] Reject zip-bomb signatures (nested compression, extreme ratios)
>
> 4. **Content scanning**
>    - [ ] AV scan all uploads in a sandboxed pipeline
>    - [ ] Re-encode images via trusted library to strip exploits / metadata
>
> 5. **Storage & serving**
>    - [ ] Store outside web root; serve via auth-gated endpoint
>    - [ ] Set `Content-Disposition: attachment` for non-image types
>    - [ ] `X-Content-Type-Options: nosniff` on downloads
>
> Link from `catalog/skills/security/security-patch-advisor/SKILL.md` "Related resources" section.
>
> Acceptance: checklist is under 80 lines, five groups present, link from security-patch-advisor resolves.

---

#### 3.5 - Testing and Stabilization (Phase 3)

**Objective**: Verify security additions work end-to-end.

**Prompt**:
> Verify Phase 3:
> 1. Confirm `business-logic-abuse` and `advanced-attack-patterns` SKILL.md files parse; frontmatter includes required fields.
> 2. Smoke-test `/run-penetration-test --depth=deep` on a sample repo (or simulate via dry-run if no test harness exists). Confirm the 6th hunter slot fires and invokes both skills.
> 3. Verify WSTG Coverage Matrix rows render.
> 4. Confirm "Attack Paths / Chains" rename is consistent throughout `run-penetration-test.md` (grep for "Attack Paths").
> 5. Confirm Secure Design Recommendations subsection appears in the report template.
> 6. Confirm `catalog/checklists/file-upload-security.md` renders and is linked from `security-patch-advisor`.
> 7. Commit each sub-task separately.
> 8. Run `/generate-session-history` to document Phase 3.

---

### Phase 3 Exit Checklist

- [ ] 3.1 - business-logic-abuse skill created
- [ ] 3.2 - advanced-attack-patterns skill created
- [ ] 3.3 - `/run-penetration-test` extended with 6th hunter, --depth=deep flag, WSTG matrix, terminology polish, design-rec section
- [ ] 3.4 - File-upload security checklist published and linked
- [ ] 3.5 - Phase 3 session history generated
- [ ] Smoke-test run, no parse errors
- [ ] Ready to advance to Phase 4

---

## Phase 4: Context Calibrations & Migration Notes

**Goal**: Add the 1M-token-window calibration anchor, the "summarize from here" session-history mode, and the comprehensive Opus 4.6 -> 4.7 migration notes.

**Prerequisites**: Phase 1 complete (migration notes reference effort-level guide and session-lifecycle guide); Phase 2 complete (migration notes reference new multi-agent and anti-pattern content).

**Stability Gate**: `context-degradation` references the 300-400k threshold explicitly; session-history supports the new "summarize from here" invocation; migration notes enumerate every behavioral delta and cross-link to the canonical source for each.

### Sub-tasks

#### 4.1 - 1M-window calibration note in context-degradation

**Objective**: Anchor the Lost-in-Middle pattern to the 300-400k range specific to the 1M model (Doc 1, insights 2-3).

**Prompt**:
> Extend Step 1 ("Recognize Degradation Signals") and Step 2 ("Apply Mitigation") of `catalog/skills/orchestration/context-degradation/SKILL.md` per insights 2 and 3 of `docs/v0.9.6/comparison-claude-code-session-management-1m-context.md`.
>
> Step 1 addition:
> > "**1M-window calibration (Opus 4.7 / Sonnet 4.6+):** Lost-in-Middle degradation becomes noticeable around **300-400k tokens** of conversation history, and accelerates past 500k. Below 100k, degradation is usually task-related rather than window-related. This is task-dependent and model-dependent; use the table below as guidance, not a hard threshold."
>
> Add a table:
>
> | Session size | Degradation risk | Recommended action |
> |---|---|---|
> | < 100k tokens | Green - low risk | Continue normally |
> | 100-300k | Yellow - monitor | Watch for repeat clarifications, dropped references |
> | 300-500k | Orange - mitigate | Proactive `/compact focus on X`, consider handoff |
> | 500k+ | Red - high risk | `/compact` or `/rewind` with handoff; delegate subagents for new subtasks |
>
> Caveat line: "Tasks with dense context (many files, long tool outputs) hit Orange earlier; tasks with mostly conversational context hit Orange later."
>
> Step 2 addition: cross-link to the proactive-steering subsection added in 2.5 and to `guides/SESSION_LIFECYCLE_DECISIONS.md` (1.2).
>
> Acceptance: table renders, caveat present, cross-links resolve.

---

#### 4.2 - "Summarize from here" mode in session-history

**Objective**: Document the P3 mid-session handoff pattern (Doc 1, insights 8-9).

**Prompt**:
> Add a new operating mode titled **"Summarize from here (mid-session handoff)"** to `catalog/skills/workflow/session-history/SKILL.md` per insights 8 and 9 of `docs/v0.9.6/comparison-claude-code-session-management-1m-context.md`.
>
> Content:
> 1. **Purpose**: generate a compact hand-off message *just before* invoking `/rewind` or `/clear` so the next session starts with Claude's learnings as its opening context.
> 2. **Trigger**: user says "summarize from here" or "/session-history --handoff" (if command supports flags).
> 3. **Output**: a 5-10 bullet message capturing: current task goal, decisions made, files touched, known blockers, next concrete step.
> 4. **Usage pattern**:
>    - Step 1: user asks Claude to summarize from here.
>    - Step 2: Claude outputs the handoff message.
>    - Step 3: user runs `/rewind` (or starts a new session).
>    - Step 4: user pastes the handoff message as the first turn of the new session.
> 5. Cross-link to `guides/SESSION_LIFECYCLE_DECISIONS.md` (1.2).
>
> Acceptance: new mode section is 30-40 lines, usage pattern spelled out, cross-link resolves.

---

#### 4.3 - Opus 4.6 -> 4.7 migration notes

**Objective**: P2 migration guide tying together all Opus 4.7 behavioral deltas introduced in Phases 1-2.

**Prompt**:
> Create `docs/v0.9.6/opus-4-7-migration.md` (filed under v0.9.6 to match the comparison doc's home) per P2 in `docs/v0.9.6/comparison-best-practices-for-using-claude-opus-4-7-with-claude-code.md`.
>
> Structure:
> 1. **Audience**: operators running DevAI-Hub on Opus 4.7 who were previously on 4.6.
> 2. **Operator must-do** (actions required):
>    - Reconfirm `effortLevel` default (see 1.1 reconciliation).
>    - Adopt explicit parallel-fan-out prompting (see 2.3).
>    - Remove any fixed thinking-budget params (see 2.2).
>    - Update clarifying-questions habit to batch into first turn (see 1.5).
> 3. **Informational (model-side, no action needed)**:
>    - Auto-calibrated response length - no rule needed; do not fight it.
>    - Reasoning-first posture - prompts should default to reasoning over tool invocation.
> 4. **What to remove**: any guide / rule / prompt in your project that codifies 4.6-specific behavior (e.g., "always prefer tools over reasoning").
> 5. **Cross-reference table**: each behavioral delta -> canonical location in the DevAI-Hub catalog.
>
> | Delta | Doc/Skill reference |
> |---|---|
> | Effort-level hierarchy | `catalog/skills/ai-development/prompt-engineering/SKILL.md` - Effort-Level Strategy |
> | Reasoning > tools | `catalog/skills/ai-development/ai-agent-development/SKILL.md` - Anti-Patterns |
> | Explicit fan-out | `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` |
> | No fixed thinking budgets | Anti-Patterns table |
> | Batch clarifying questions | `templates/ai-instructions/base-*.md` Critical Rules |
> | Session lifecycle | `guides/SESSION_LIFECYCLE_DECISIONS.md` |
>
> Cite https://claude.com/blog/best-practices-for-using-claude-opus-4-7-with-claude-code as the canonical source.
>
> Acceptance: document is 200-350 lines, all cross-links resolve, table is complete.

---

#### 4.4 - Testing and Stabilization (Phase 4)

**Objective**: Verify the three additions cohere with Phases 1-3.

**Prompt**:
> Verify Phase 4:
> 1. Confirm `context-degradation` Step 1 table renders and is technically consistent with proactive-steering in 2.5.
> 2. Confirm `session-history` new mode does not duplicate content in existing modes.
> 3. Confirm `opus-4-7-migration.md` cross-reference table has valid links for every row.
> 4. Grep for any stale "Opus 4.6" or "fixed thinking budget" references: `grep -rn "fixed thinking\|Opus 4\\.6" catalog/ guides/ docs/` - all remaining hits should be deliberate (e.g., migration notes).
> 5. Commit each sub-task separately.
> 6. Run `/generate-session-history` to document Phase 4.

---

### Phase 4 Exit Checklist

- [ ] 4.1 - 1M-window calibration note added to context-degradation
- [ ] 4.2 - "Summarize from here" mode added to session-history
- [ ] 4.3 - Opus 4.6 -> 4.7 migration notes published
- [ ] 4.4 - Phase 4 session history generated
- [ ] All cross-reference tables complete
- [ ] Ready to advance to Phase 5

---

## Phase 5: VS Code Extension Settings Panel

**Goal**: Surface the effort-level guide content as hover help next to the `effortLevel` control in the VS Code extension settings panel (Doc 2, P3 item 20). This is the only phase with user-visible UI changes.

**Prerequisites**: Phase 1 complete (Effort-Level Strategy section exists and will be the hover-help source of truth).

**Stability Gate**: Hovering the `effortLevel` setting in the extension shows definitions for all five tiers, matching the text in the prompt-engineering skill.

### Sub-tasks

#### 5.1 - Locate extension settings schema and identify hover-help mechanism

**Objective**: Understand where the extension exposes configuration and how descriptions are surfaced.

**Prompt**:
> Explore the DevAI-Hub VS Code extension to locate:
> 1. The `package.json` `contributes.configuration` block declaring the `effortLevel` setting.
> 2. The extension's webview (if any) rendering settings, and where it pulls description text.
> 3. Any existing hover / markdown-description patterns for other settings.
>
> Report findings: file paths, schema structure, rendering mechanism.
>
> Do not modify code yet.
>
> Acceptance: short report identifying the schema file(s) and the mechanism for rich markdown descriptions (VS Code supports `markdownDescription` in settings schema).

---

#### 5.2 - Add markdownDescription for effortLevel setting

**Objective**: Add concise hover help covering all five tiers with a link to the Effort-Level Strategy section.

**Prompt**:
> In the VS Code extension settings schema located in 5.1, update the `effortLevel` property to include a `markdownDescription` that summarizes all five tiers in a scannable format, with a link to `catalog/skills/ai-development/prompt-engineering/SKILL.md#effort-level-strategy`.
>
> Keep the description under 500 characters (VS Code settings editor truncates long descriptions). Use a 5-row markdown table or a bulleted list.
>
> If the extension has a custom settings webview (not the built-in editor), update the webview component to render the same content.
>
> Acceptance: hovering `effortLevel` in VS Code settings editor shows the table / list; link to the skill opens the correct section.

---

#### 5.3 - Testing and Stabilization (Phase 5)

**Objective**: Visual QA the extension UI in a clean VS Code workspace.

**Prompt**:
> Verify Phase 5:
> 1. Install the extension in a clean VS Code profile (`code --user-data-dir=/tmp/vscode-test --extensions-dir=/tmp/ext`).
> 2. Open Settings, search for "effortLevel", confirm the hover / description renders all five tiers.
> 3. Click the link in the description and confirm it opens the prompt-engineering skill at the right anchor.
> 4. Confirm no new console errors in the extension host.
> 5. Commit as a single logical unit.
> 6. Run `/generate-session-history` for Phase 5.

---

### Phase 5 Exit Checklist

- [ ] 5.1 - Schema and rendering mechanism identified
- [ ] 5.2 - `markdownDescription` added; webview updated if applicable
- [ ] 5.3 - Visual QA passed in clean VS Code profile
- [ ] Ready to advance to Phase 6

---

## Phase 6: Documentation Sync & v0.9.7 Release

**Goal**: Produce the release artifacts - updated `CATALOG-COVERAGE.md`, complete `CHANGELOG.md` entry, version bumps everywhere, DEVLOG entry, platform-parity audit, and release tag.

**Prerequisites**: Phases 1-5 complete.

**Stability Gate**: All 22 recommendations are listed as shipped in `CATALOG-COVERAGE.md`, `CHANGELOG.md` has a complete v0.9.7 entry following Keep a Changelog, version strings agree across every file, DEVLOG v0.9.7 entry exists, and the platform-parity audit reports zero drift.

### Sub-tasks

#### 6.1 - Update docs/CATALOG-COVERAGE.md

**Objective**: Reflect all new skills, commands, guides, and checklists shipped in v0.9.7.

**Prompt**:
> Update `docs/CATALOG-COVERAGE.md` with:
> 1. New skills: `business-logic-abuse`, `advanced-attack-patterns`.
> 2. New guides: `SESSION_LIFECYCLE_DECISIONS.md`, `opus-4-7-migration.md`.
> 3. New checklists: `file-upload-security.md`.
> 4. Extended skills (list each): prompt-engineering (Effort-Level Strategy + Opus 4.7 Practices), ai-agent-development (Anti-Patterns), multi-agent-coordinator (explicit fan-out + reuse test), context-compression (proactive steering), context-degradation (1M-window calibration), session-history (summarize-from-here), security-patch-advisor (file-upload checklist link).
> 5. Update any "Total skills" / "Total commands" counts in the index.
> 6. Update the DevAI-Hub Skill Index in `C:\Users\BEDOURTHE\.claude\CLAUDE.md` global file with the two new skills if the project owns that file - coordinate with user before editing global config.
>
> Acceptance: CATALOG-COVERAGE lists every new and extended artifact, totals reconcile.

---

#### 6.2 - Update CHANGELOG.md with v0.9.7 entry

**Objective**: Complete Keep-a-Changelog entry for v0.9.7.

**Prompt**:
> Add a v0.9.7 entry to `CHANGELOG.md` following Keep a Changelog 1.1.0 format. Use ASCII-only punctuation (no em-dashes, no curly quotes, no ellipsis characters).
>
> Sections to include:
> - **Added**: new skills (business-logic-abuse, advanced-attack-patterns), new guides (SESSION_LIFECYCLE_DECISIONS, opus-4-7-migration), file-upload-security checklist, 6th pen-test hunter with --depth=deep flag, VS Code extension effortLevel hover help.
> - **Changed**: batched clarifying-questions rule across all 5 platform templates, Opus 4.7 behavioral adaptations in prompt-engineering / ai-agent-development / multi-agent-coordinator / context-compression / context-degradation, /run-penetration-test WSTG matrix expansion, Attack Paths renamed to Attack Paths / Chains, Secure Design Recommendations subsection added to report template.
> - **Fixed**: effort-level drift between catalog/hooks/settings.json and v0.9.6 CHANGELOG (canonical value is now consistent).
> - **Docs**: session-history "summarize from here" mode, CATALOG-COVERAGE refresh.
>
> If the v0.9.6 section still contains the incorrect "installer effortLevel now defaults to high" line, leave a "Correction" note under v0.9.7 (consistent with 1.1's decision).
>
> Acceptance: entry parses as valid Keep a Changelog, ASCII-only.

---

#### 6.3 - Version bump across the repo

**Objective**: Update every file that encodes a version string.

**Prompt**:
> Bump the version from 0.9.6 to 0.9.7 everywhere it is encoded. Search with:
>
> `grep -rn "0\.9\.6\|v0\.9\.6" --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=docs/v0.9.6 .`
>
> Candidate files (verify each hit):
> - `install.sh`
> - `install.bat`
> - VS Code extension `package.json`
> - Any `pyproject.toml` / `Cargo.toml` / `package.json` at repo root
> - `README.md` badges
> - `llms.txt`
> - `scripts/` that reference version
> - `AGENTS.md` / `CLAUDE.md` if they state version
>
> Leave `docs/v0.9.6/` contents untouched (those are historical).
>
> After bump, update `docs/todos.md` dashboard metrics if applicable.
>
> Acceptance: no remaining references to 0.9.6 outside `docs/v0.9.6/` and historical CHANGELOG entries.

---

#### 6.4 - Generate v0.9.7 DEVLOG entry

**Objective**: Produce a consolidated DEVLOG entry from Phase 1-5 session histories.

**Prompt**:
> Run `/update-devlog` (or manually author a DEVLOG entry in `docs/DEVLOG.md` if the file does not exist; otherwise create it).
>
> Consolidate the five per-phase session histories generated in 1.7, 2.6, 3.5, 4.4, 5.3 into a single v0.9.7 DEVLOG entry structured as:
> - **Release context**: link to the three comparison documents that drove this work.
> - **Phase-by-phase summary**: one paragraph per phase listing shipped artifacts.
> - **Migration impact**: point operators at `docs/v0.9.6/opus-4-7-migration.md`.
> - **Known issues / follow-ups**: anything deferred (e.g., VS Code extension work if it slipped).
>
> Acceptance: DEVLOG entry is 300-500 lines, all links resolve, phase-by-phase summary matches the 22-item master list.

---

#### 6.5 - Platform-parity audit

**Objective**: Verify the 5-platform template parity rule was honored per [memory/project_platform_agnostic.md](memory/project_platform_agnostic.md).

**Prompt**:
> Run a platform-parity audit:
> 1. Confirm all 5 base templates in `templates/ai-instructions/` have the batched clarifying-questions rule (1.5).
> 2. Confirm no rule, skill, command, or hook change introduced in this release is platform-specific without an equivalent in the other four templates.
> 3. Run `diff -r` style comparisons on the five base templates and confirm only intentional deltas remain.
> 4. Check the memory note `~/.claude/projects/<project-key>/memory/project_platform_agnostic.md` (the auto-memory directory for this project) and confirm the guidance is still accurate; update if the parity model has evolved.
>
> Acceptance: zero unintended drift across the 5 base templates.

---

#### 6.6 - Tag and release

**Objective**: Create the v0.9.7 git tag and prepare the GitHub release notes.

**Prompt**:
> Final release steps:
> 1. Confirm working tree is clean and all phase commits landed on main.
> 2. Create annotated tag: `git tag -a v0.9.7 -m "Release v0.9.7 - session management, Opus 4.7 adaptations, security expansion"`.
> 3. Do NOT push the tag automatically - wait for user confirmation.
> 4. Draft the GitHub release body in a local file (`docs/v0.9.7/RELEASE_NOTES.md` or similar) mirroring the CHANGELOG v0.9.7 entry plus a "Highlights" header section.
> 5. Present the draft to the user and request approval before `git push --tags` and `gh release create`.
>
> Acceptance: tag created locally; release notes drafted; awaiting explicit user approval to push.

---

### Phase 6 Exit Checklist

- [ ] 6.1 - CATALOG-COVERAGE.md updated
- [ ] 6.2 - CHANGELOG v0.9.7 entry complete, ASCII-only
- [ ] 6.3 - Version bumped across all relevant files
- [ ] 6.4 - DEVLOG v0.9.7 entry generated
- [ ] 6.5 - Platform-parity audit reports zero drift
- [ ] 6.6 - Tag created locally, release notes drafted, awaiting user push approval
- [ ] Ready for user to publish v0.9.7

---

## Critical Files to Be Modified

### New files
- `guides/SESSION_LIFECYCLE_DECISIONS.md` (1.2)
- `catalog/skills/security/business-logic-abuse/SKILL.md` (3.1)
- `catalog/skills/security/advanced-attack-patterns/SKILL.md` (3.2)
- `catalog/checklists/file-upload-security.md` (3.4)
- `docs/v0.9.6/opus-4-7-migration.md` (4.3)
- `docs/v0.9.7/implementation-plan.md` (this plan, copied here after approval)
- `docs/v0.9.7/RELEASE_NOTES.md` (6.6)

### Modified files
- `catalog/hooks/settings.json` (1.1)
- `CHANGELOG.md` (1.1, 6.2)
- `install.sh`, `install.bat` (1.1, 6.3)
- `guides/TOKEN_OPTIMIZATION.md` (1.4, cross-links)
- `templates/ai-instructions/base-{claude,gemini,codex,cursor,opencode}.md` (1.5)
- `catalog/skills/ai-development/prompt-engineering/SKILL.md` (1.3, 2.1)
- `catalog/skills/ai-development/ai-agent-development/SKILL.md` (2.2)
- `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` (2.3, 2.4)
- `catalog/skills/orchestration/context-compression/SKILL.md` (2.5, cross-links)
- `catalog/skills/orchestration/context-degradation/SKILL.md` (4.1)
- `catalog/skills/orchestration/context-manager/SKILL.md` (cross-links from 1.6)
- `catalog/skills/workflow/session-history/SKILL.md` (4.2, cross-links)
- `catalog/skills/security/security-patch-advisor/SKILL.md` (3.4 link)
- `catalog/commands/run-penetration-test.md` (3.1, 3.2, 3.3)
- `catalog/agents/loop-operator.md` (1.3 cross-link note)
- `docs/CATALOG-COVERAGE.md` (6.1)
- `docs/DEVLOG.md` (6.4)
- VS Code extension `package.json` and webview files (5.1, 5.2)

---

## Existing Utilities Referenced

- `/generate-session-history` - runs at each phase exit (1.7, 2.6, 3.5, 4.4, 5.3).
- `/update-devlog` - runs in 6.4.
- `/run-penetration-test` - extended in 3.3; referenced as the integration target for new security skills.
- `docs/todos.md` - updated in 6.3 with dashboard metrics per CLAUDE.md convention.
- `memory/project_platform_agnostic.md` - the source of the 5-platform parity rule enforced in 1.5 and audited in 6.5.

---

## Verification (End-to-End)

After Phase 6 completes:

1. **Content audit**: `grep -c "^#### " docs/v0.9.7/implementation-plan.md` returns 31 (sub-task count).
2. **Cross-link integrity**: run a markdown link-checker across `catalog/`, `guides/`, `docs/` - zero broken links.
3. **Platform parity**: `diff` the 5 base templates, confirm no unintended drift.
4. **Effort-level consistency**: `grep -rn "effortLevel" --exclude-dir=docs/v0.9.6` - all hits reference the canonical value.
5. **Pen-test smoke**: run `/run-penetration-test --depth=deep` on a small sample repo (or the DevAI-Hub repo itself) and confirm the 6th hunter slot fires.
6. **VS Code extension**: install in a clean profile, confirm effortLevel hover help renders.
7. **Version strings**: `grep -rn "0\\.9\\.6" --exclude-dir=docs/v0.9.6 --exclude-dir=.git` - no hits outside historical CHANGELOG entries.
8. **Release tag**: `git show v0.9.7` - tag exists with correct message.
9. **CHANGELOG ASCII check**: `LC_ALL=C grep -P "[^\x00-\x7F]" CHANGELOG.md` - no non-ASCII characters in v0.9.7 entry.

Once all nine checks pass, push the tag (`git push --tags`) and create the GitHub release (`gh release create v0.9.7 -F docs/v0.9.7/RELEASE_NOTES.md`) - with explicit user approval first.

---

## Out of Scope / Deferred

Per the three comparison documents, the following were explicitly rejected as non-recommendations and are **not** in this plan:

- New `/rewind`, `/compact`, or `/clear` slash commands (would duplicate native Claude Code).
- Dedicated "bad compact" detection skill (subsection in TOKEN_OPTIMIZATION.md is sufficient).
- Session health scorecard as standalone skill (context-degradation probes already serve this).
- Dedicated "paranoid mindset" preamble skill (adversarial framing already embedded in pen-test hunters).
- Adopting the X-post security prompt verbatim as a slash command.
- Dynamic-analysis features (open-port enumeration, cloud misconfig, runtime file-upload exploits) - static-audit-only scope.
- New slash commands for effort levels (config concern, not interaction concern).

If any of these become in-scope later, they belong in a subsequent v0.10.0 plan, not v0.9.7.
