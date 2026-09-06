# Plan — Adopt Compound Engineering Plugin Capabilities (reverse-engineer-first)

**Project**: Nexus-Hub
**Version**: v2.4.0
**Slug**: adoption-compound-engineering-plugin
**Plan Type**: Feature / Enhancement
**Created**: 2026-05-30
**Goal**: Adopt all 13 in-scope capabilities from the compound-engineering-plugin comparison AND resolve all 15 ingested v2.3.0 known-gaps, as local zero-outbound Nexus-Hub content, with the catalog green.

## Overview

This plan operationalizes [docs/archives/v2/v2.3/comparison-compound-engineering-plugin.md](../../v2.3.0/comparison-compound-engineering-plugin.md). The compound-engineering plugin (Every Inc) is the closest structural analog to Nexus-Hub compared to date: both are multi-platform AI-assistant harnesses. The comparison surfaced 13 adoption candidates (A1-A13) clustered around a closed knowledge loop (capture solved problems -> feed planning), a multi-agent persona review pipeline, and a set of internal-build conveniences. Every adopted item is local catalog content (markdown skills + re-authored generic agents) or a local script reusing the user's own model CLI and local logs: zero new outbound calls, zero new credentials, zero new third-party data processors. CE's vendor-integrated skills (Gemini image generation, Slack, Proof, Riffrec, XcodeBuildMCP) fail the MCP Registry Policy and are listed in the out-of-scope appendix, not adopted.

Phase sequencing follows the MCP Registry Policy decision tree (reverse-engineer-first). See Section 9.4 of the source comparison for the ordering rationale: skill-native items ship first (Phases 1-4), then `re-full` internal builds (Phase 5), then `re-partial` internal builds (Phase 6). The `drop-outright` items do not appear in any phase; they are recorded in the out-of-scope appendix following the N-item convention.

This plan ingests 15 item(s) carried forward from prior known-gaps files: see sub-tasks tagged `[from v2.3.0 known-gaps: <ID>]`. The 15 items are the full open set from [docs/archives/v2/v2.3/known-gaps.md](../../v2.3.0/known-gaps.md) (pre-existing catalog-quality debt plus two live-eval verification deferrals). They are grouped into a catalog-quality/hygiene phase (Phase 7) and a live-verification phase (Phase 8), with two validation-blocking items (the skills.json count drift and the secret-scan false positives) pulled into Phase 1 so new-skill additions validate cleanly. Per the chosen Definition of Done, the version is not release-ready until all A-items ship AND all 15 ingested gaps are resolved AND `make validate` / `make lint` / `make test` are green with the `data/` registries reconciled. Per the chosen testing level, every phase runs the heavier bar (pytest with `.ps1` parity, plus live `skill-eval-loop` trigger runs for new skills and a benchmark pass for the persona review pipeline).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution file found at docs/archive/v2/v2.4/constitution.md - skipping check. Recommend running /constitution to establish project principles. This is informational and non-blocking. The de-facto governing constraints for this plan are the `AGENTS.md` MCP Registry Policy (zero-outbound default, reverse-engineer-first, no search/embeddings/scraping/generation-as-service), the Installer-Aware-Changes cross-platform rule (`.sh` + `.ps1` parity; `scripts/<name>.py` registered in both installers), the three-registry update rule for new skills (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`), and the Markdown / ASCII-only style guide. Every phase below is written to satisfy these.

## Phases at a Glance

| Phase | Title | Outcome |
|-------|-------|---------|
| 1 | Foundation: knowledge base + scoring discipline | Solved-problems knowledge base + capture/refresh skills + confidence-anchor reference; validation clean (A1, A4, WN-v23-1, BG-v23-1) |
| 2 | Persona review pipeline | Persona-fanout code + plan review with confidence/dedup/validation pipeline and a generic persona agent library (A2, A3, A8) |
| 3 | Close the compound loop | STRATEGY anchor + planning skills read the knowledge base + cross-tool session query (A5, A7) |
| 4 | Remaining skill-native | Crash-safe optimization persistence + product-pulse skill template (A10, A11) |
| 5 | Internal RE builds (re-full) | Per-platform capability spec docs + installer `--branch` testing (A6, A9) |
| 6 | Internal RE builds (re-partial) | Local demo-capture skill + conventional-commit release/changelog script (A12, A13) |
| 7 | Catalog-quality + hygiene remediation | Stocktake remediation, BOM/punctuation/path cleanup, CI shellcheck, code-search extractors (9 ingested gaps) |
| 8 | Live verification + release readiness | Live eval runs, Antigravity probe, macOS/Linux smoke, final catalog-green gate (4 ingested gaps) |

---

## Phase 1: Foundation — Knowledge Base + Scoring Discipline

**Goal**: Ship the solved-problems knowledge base and capture/refresh skills (A1) plus the confidence-anchored scoring reference (A4), and clear the two validation-blocking known-gaps so new skills validate cleanly.
**Prerequisites**: None.
**Stability Gate**: The two new skills are registered in all three data files; `python scripts/validate_skills.py` runs with zero errors (strict mode usable); the frontmatter validator passes its pytest suite; live `skill-eval-loop` trigger runs show the two new skills trigger on a positive prompt and not on a fenced negative prompt.

### Sub-tasks

#### 1.1 — Solution knowledge-base capture skill

- [x] T001 Create the capture skill at catalog/skills/workflow/solution-knowledge-base/SKILL.md

**Objective**: Adopt CE's `ce-compound` as a generic, local, zero-outbound skill that documents a recently solved problem into a categorized `docs/solutions/`-style store.

**Prompt**:
> Create `catalog/skills/workflow/solution-knowledge-base/SKILL.md` per the Nexus-Hub SKILL.md contract in AGENTS.md (frontmatter: name, description with trigger phrases + a SKIP clause, summary_l0 <=15 words, overview_l1 <=150 words; body sections: title, When to Use This Skill incl. When NOT to use, Instructions, Common Rationalizations table, binary Verification checklist, Related Skills). The skill documents a recently solved problem into `docs/solutions/<category>/<slug>.md` with a two-track YAML frontmatter (bug track: symptoms / root_cause / resolution_type; knowledge track: applies_when), generic (NON-Rails) component values, parallel research (context analyzer / solution extractor / related-docs finder returning text only; orchestrator writes one file), 5-dimension overlap scoring (update-vs-create), and a Discoverability Check that surfaces the store in AGENTS.md/CLAUDE.md via the canonical `merge_marker_section` marker block (never clobbering managed content). Add `references/schema.md` (the two-track field/enum contract + category mapping + YAML-safety quoting rule) and reference it on demand from the body. Re-author all content from the comparison's description of the pattern; do NOT copy CE text and do NOT name the source repo in the artifact (Reverse-Engineering Attribution Rule). Register the skill in `data/SKILL_INDEX.md`, `data/skills.json`, and `data/marketplace.json` (workflow category). Run `make validate`. Acceptance: skill validates, references/schema.md is referenced (orphan-bundle clean), zero outbound calls.

---

#### 1.2 — Solution knowledge-base refresh skill

- [x] T002 Create the refresh skill at catalog/skills/workflow/solution-refresh/SKILL.md

**Objective**: Adopt CE's `ce-compound-refresh` lifecycle (Keep / Update / Consolidate / Replace / Delete) for maintaining the knowledge base over time.

**Prompt**:
> Create `catalog/skills/workflow/solution-refresh/SKILL.md` following the same contract as T001. The skill audits an existing `docs/solutions/` entry (or a scoped subset: file / module / category) and decides one of five outcomes: Keep / Update / Consolidate / Replace / Delete, with interactive and autofix modes. It reuses `solution-knowledge-base`'s `references/schema.md` for validation (link it; do not duplicate). Add a Common Rationalizations table and a binary Verification checklist. Register in the three data files. Cross-link `[[solution-knowledge-base]]` and `[[known-gaps-tracker]]` and `[[continuous-learning]]` in Related Skills. Run `make validate`. Acceptance: validates clean, zero outbound.

---

#### 1.3 — Frontmatter parser-safety validator

- [x] T003 [P] Add the frontmatter validator at scripts/validate_solution_frontmatter.py (.ps1 sibling intentionally omitted - see NI-v24-1)

**Objective**: Adopt CE's `validate-frontmatter.py` as a stdlib-only parser-safety checker for solution-doc frontmatter (malformed delimiters, unquoted ` #` comment truncation, unquoted `: ` mapping confusion).

**Prompt**:
> Create `scripts/validate_solution_frontmatter.py` (Python 3 stdlib only, no PyYAML) that takes one or more solution-doc paths and exits 0 when parser-safe, 1 with a stderr message naming the offending field(s) otherwise. Detect: malformed `---` delimiter lines, unquoted ` #` in scalar values (silent comment truncation), unquoted `: ` in scalar values (mapping confusion), and array items starting with a YAML reserved indicator that are not quoted. Create the PowerShell sibling `scripts/validate_solution_frontmatter.ps1` with identical behavior (cross-platform parity rule). Register BOTH as explicit-name copy steps in `scripts/installer.sh` AND `scripts/installer.ps1` next to the existing v2.3.0 validator copy block (the installer copies scripts by explicit name). Add pytest coverage at `tests/validators/test_validate_solution_frontmatter.py` (clean-pass + each dirty-fail case). Wire into `make validate`. Acceptance: pytest green, both installers reference the script, `make validate` invokes it.

---

#### 1.4 — Confidence-anchored scoring reference

- [x] T004 [P] Add the scoring discipline reference at catalog/skills/code-review/code-quality/references/confidence-anchored-scoring.md

**Objective**: Adopt CE's discrete 5-anchor confidence scoring (0/25/50/75/100), fingerprint dedup, cross-reviewer promotion, mode-aware demotion, and late confidence gate as a reusable reference the Phase 2 pipeline and existing review skills cite.

**Prompt**:
> Create `catalog/skills/code-review/code-quality/references/confidence-anchored-scoring.md` documenting: the 5 discrete confidence anchors with behavioral definitions; fingerprint dedup (`normalize(file) + line_bucket(±3) + normalize(title)`); cross-reviewer agreement promotion (50->75, 75->100); mode-aware demotion of weak P2/P3 advisory findings from testing/maintainability personas; and the deliberately-late confidence gate (suppress < anchor 75, except P0 at 50+). Re-author generically; do not name the source. Link this reference from `catalog/skills/code-review/code-quality/SKILL.md` and add a forward-reference note in `catalog/skills/code-review/security-review/SKILL.md` so the Phase 2 pipeline (A2) and `run-penetration-test` synthesis can adopt it. Run `make validate` (orphan-bundle audit must stay clean). Acceptance: reference is linked from at least one SKILL.md, validates clean.

---

#### 1.5 — Reconcile skills.json count drift

- [x] T005 [from v2.3.0 known-gaps: WN-v23-1] Reconcile statistics.total_skills with len(skills) in data/skills.json

**Objective**: Resolve the 1-skill drift between `data/skills.json` entry count and `statistics.total_skills`, recomputing per-category counts, so the Phase-1 additions land on a reconciled baseline.

**Prompt**:
> Original reason: at v2.3.0 Phase 1 start the `skills` array contained more entries than `statistics.total_skills` reported; subsequent additions preserved the same 1-skill drift. Suggested next step (from known-gaps): reconcile `statistics.total_skills` against `len(d['skills'])` and re-derive per-category counts. Implement: load `data/skills.json`, set `statistics.total_skills` to the true array length AFTER the T001/T002 additions, recompute `statistics` per-category counts and `data/marketplace.json` category `skill_count` values from the array, and confirm `data/SKILL_INDEX.md` row count matches. Run `make validate` and confirm catalog integrity. Acceptance: count drift is zero, `make validate` passes, the three data files agree.

---

#### 1.6 — Resolve secret-scan false positives in skill docs

- [x] T006 [P] [from v2.3.0 known-gaps: BG-v23-1] Make scripts/validate_skills.py ignore fenced-code secret examples

**Objective**: Eliminate the 7 pre-existing "Generic secret assignment" false positives so the strict validator is usable when adding new skills.

**Prompt**:
> Original reason: `scripts/validate_skills.py` flags 7 lines across `ai-development/google-antigravity-sdk/SKILL.md`, `documentation/user-documentation/SKILL.md` (2), `infrastructure/cd-pipeline-generator/SKILL.md` (2), and `infrastructure/rollback-strategy-advisor/SKILL.md` (2) as generic-secret assignments; each is a documentation example inside a fenced code block, not a real secret. Suggested next step (from known-gaps): refine `SECRET_PATTERNS` matching in `scripts/validate_skills.py` to ignore matches inside fenced code blocks in `.md` files (track fence state while scanning), or add an in-skill suppression mechanism. Implement the fenced-code-aware skip in the secret scan, add a pytest case asserting a fenced `password = "..."` example does not trip the scanner while an unfenced one still does, and re-run the strict validator across the catalog. Acceptance: 0 false positives on the 7 known lines, the unfenced case still fails, pytest green.

---

#### 1.7 — Testing and Stabilization

- [x] T007 Run and stabilize Phase 1 tests, including live skill-eval-loop trigger runs (live run deferred - DF-v24-1)

**Objective**: Verify Phase 1 end-to-end at the heavier testing bar.

**Prompt**:
> Generate and run all tests for Phase 1: pytest for `scripts/validate_solution_frontmatter.py` and the updated `scripts/validate_skills.py` secret-scan; `make validate` (catalog integrity + orphan-bundle audit + the four CI validators) and `make lint`. Then run live `skill-eval-loop` trigger checks for the two new skills (`solution-knowledge-base`, `solution-refresh`): author a minimal `evals.json` per skill with one should-trigger and one should-not-trigger prompt and confirm a 1.0 trigger rate on the positive prompt and 0.0 on the negative; tighten the `description` per `skill-eval-loop/references/improvement-heuristics.md` if under-triggering. Fix all failures and iterate until green. Do not advance to Phase 2 until verified. After all tests pass, run /generate-session-history to document Phase 1.

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed
- [x] All tests passing (pytest + make validate + make lint)
- [~] Live skill-eval-loop trigger runs pass for both new skills (deferred - no model CLI on PATH; static trigger-surface check done; DF-v24-1)
- [x] data/ registries reconciled (count drift zero - all three files agree at 239 skills / 21 categories)
- [x] No known regressions
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 2

---

## Phase 2: Persona Review Pipeline

**Goal**: Adopt CE's multi-agent persona code review (A2), the persona review of plans/requirements (A3), and the agent-native review lens (A8), backed by a re-authored generic persona agent library.
**Prerequisites**: Phase 1 (A4 confidence-anchored scoring reference).
**Stability Gate**: The review command runs end-to-end on a sample diff, selects personas per-diff, returns deduplicated confidence-gated findings, and a benchmark pass shows the pipeline reproduces known seeded findings; new skills pass live trigger checks.

### Sub-tasks

#### 2.1 — Re-authored generic persona agent library

- [x] T008 Add persona reviewer agents under catalog/agents/

**Objective**: Adopt CE's persona-agent concept as a generic, language-agnostic reviewer set that the review pipeline fans out to.

**Prompt**:
> Create generic persona reviewer agents under `catalog/agents/` (following the existing `catalog/agents/code-reviewer.md` / `security-reviewer.md` format). Author a language-agnostic set covering: correctness, maintainability, testing, performance, reliability, api-contract, adversarial, and project-standards (AGENTS.md/CLAUDE.md compliance). Reuse the existing `code-reviewer`, `security-reviewer`, `architect`, and `refactor-cleaner` agents where they map; add only the missing personas. Each agent returns structured JSON findings with the fields from the confidence-anchored-scoring reference (title, severity P0-P3, file, line, confidence anchor, autofix_class, owner, requires_verification, pre_existing, suggested_fix). Do NOT import CE's Rails/Swift-specific personas (julik-frontend-races, swift-ios, dhh-rails-style); keep the set language-agnostic. Do not name the source repo. Acceptance: each new agent has valid frontmatter, the JSON contract matches the scoring reference, `make validate` clean.

---

#### 2.2 — Persona-fanout code review skill + command

- [x] T009 Create the review pipeline at catalog/skills/code-review/multi-agent-code-review/SKILL.md (+ catalog/commands/review-changes.md)

**Objective**: Adopt CE's `ce-code-review` pipeline: per-diff persona selection, parallel dispatch, merge/dedup, cross-reviewer promotion, confidence gate, autofix routing, an independent validation pass, model tiering, and four modes.

**Prompt**:
> Create `catalog/skills/code-review/multi-agent-code-review/SKILL.md` implementing a persona-fanout review pipeline: (1) determine scope (diff base resolution; standalone/branch/PR/base modes); (2) intent discovery; (3) per-diff persona selection (always-on correctness/maintainability/testing/project-standards + conditional security/performance/api-contract/reliability/adversarial); (4) bounded parallel dispatch of the Phase-2.1 agents (respect the harness active-subagent limit; treat limit errors as backpressure); (5) merge findings using `references/confidence-anchored-scoring.md` (fingerprint dedup, cross-reviewer promotion, mode-aware demotion, late confidence gate); (6) an independent per-finding validation pass for externalizing modes; (7) model tiering (high-stakes reviewers inherit the session model, others mid-tier). Support four modes: interactive / autofix / report-only / headless. Add `references/{persona-selection,findings-schema,validator-template}.md`. Create a thin slash entry at `catalog/commands/review-changes.md` that invokes the skill. Register the skill in the three data files. Re-author generically; do not name the source. Run `make validate`. Acceptance: skill + references validate (orphan-bundle clean), command present, registered.

---

#### 2.3 — Persona review of plans and requirements

- [x] T010 Create the plan-review skill at catalog/skills/code-review/plan-review/SKILL.md

**Objective**: Adopt CE's `ce-doc-review`: parallel persona lenses applied to a plan or requirements doc before code.

**Prompt**:
> Create `catalog/skills/code-review/plan-review/SKILL.md` that reviews a requirements/plan/spec document using parallel persona lenses: coherence, feasibility, product-lens, design-lens, security-lens, scope-guardian, and adversarial. Reuse the Phase-2.1 agents where applicable and add plan-specific lens agents under `catalog/agents/` if needed. Output a severity-tagged findings table plus a coverage note, read-only (never modifies the plan). Cross-link `[[cross-artifact-analyzer]]` and `[[analyze-spec]]` (the existing read-only analyzers) and explain when to use this persona-fanout vs the single-agent analyzer. Register in the three data files. Run `make validate`. Acceptance: validates clean, registered, read-only contract stated.

---

#### 2.4 — Agent-native review lens

- [x] T011 Add the agent-native review lens (catalog/agents/agent-native-reviewer.md + extend tool-design)

**Objective**: Adopt CE's `ce-agent-native-reviewer` lens that verifies new features are reachable by an agent (action + context parity).

**Prompt**:
> Create `catalog/agents/agent-native-reviewer.md` that reviews a diff for agent-native design: does every new user-facing capability have an agent-accessible action, and is the context an agent needs to use it present? Add an "Agent-native design" section to `catalog/skills/developer-experience/tool-design/SKILL.md` teaching the action + context parity principle, cross-linking the new agent. Wire the agent in as a conditional persona in the Phase-2.2 pipeline (select when the diff adds user-facing features). Re-author generically. Run `make validate`. Acceptance: agent + skill section validate, pipeline references the persona.

---

#### 2.5 — Testing and Stabilization

- [x] T012 Run and stabilize Phase 2 tests, including a review-pipeline benchmark (live skill-eval-loop deferred - DF-v24-2; seeded-fixture benchmark passed)

**Objective**: Verify the review pipeline at the heavier testing bar.

**Prompt**:
> Run `make validate` and `make lint`. Build a small benchmark: a seeded diff with a known correctness bug, a known security issue, and a clean file; run the `multi-agent-code-review` skill in report-only mode and confirm it selects the right personas, surfaces the seeded findings above the confidence gate, deduplicates cross-reviewer hits, and does not flag the clean file. Run a live `skill-eval-loop` trigger check for `multi-agent-code-review` and `plan-review` (1.0 on positive, 0.0 on fenced negative). Fix all failures and iterate. Do not advance to Phase 3 until verified. After all tests pass, run /generate-session-history to document Phase 2.

---

### Phase 2 Exit Checklist

- [x] All sub-tasks completed
- [x] Review pipeline benchmark passes (seeded findings surfaced, clean file untouched)
- [~] Live trigger checks pass for the new review skills (deferred - no model CLI on PATH; static trigger-surface check done; DF-v24-2)
- [x] make validate + make lint green (validators direct: orphan-bundle 0/0, all CI validators exit 0; lint N/A - no shell scripts; repo tests 331 passed)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 3

---

## Phase 3: Close the Compound Loop

**Goal**: Wire the knowledge base into planning (A5) and add a cross-tool session-history query skill (A7) so captured knowledge feeds future work.
**Prerequisites**: Phase 1 (A1 knowledge base must exist for planning skills to read).
**Stability Gate**: `generate-plan` / `implement-phase` / `continuous-learning` reference the knowledge base as grounding; a STRATEGY anchor exists; the session-query skill extracts from local session logs with zero outbound; trigger checks pass.

### Sub-tasks

#### 3.1 — Product-strategy anchor

- [x] T013 Add the strategy anchor (new catalog/skills/workflow/product-strategy/SKILL.md)

**Objective**: Adopt CE's `ce-strategy` / STRATEGY.md upstream anchor (target problem, approach, persona, key metrics, tracks) read as grounding by ideation/planning.

**Prompt**:
> Decide between extending `project-constitution` with a product-strategy section vs a new `catalog/skills/workflow/product-strategy/SKILL.md`; prefer a new skill since the constitution is governance (MUST/SHOULD) while strategy is product framing (problem/approach/persona/metrics/tracks). Create the skill to author and maintain a durable `STRATEGY.md` (or `docs/<version>/strategy.md`) read as grounding by ideate/brainstorm/plan. If a new skill, register it in the three data files. Cross-link `[[project-constitution]]`, `[[idea-refine]]`, `[[generate-plan]]`. Re-author generically. Run `make validate`. Acceptance: validates clean, registered if new.

---

#### 3.2 — Wire planning skills to read the knowledge base

- [x] T014 Cross-link generate-plan / implement-phase / continuous-learning to read docs/solutions

**Objective**: Close the loop: planning and learning skills read the A1 knowledge base as grounding, with the discoverability surfaced in instruction files.

**Prompt**:
> Edit the relevant skill bodies so the compound loop closes: add a grounding step to `catalog/skills/workflow/implementation-plan/SKILL.md` and the `generate-plan` command instructing the agent to search the `docs/solutions/` knowledge base for prior solutions before designing; add a cross-link from `catalog/skills/workflow/continuous-learning/SKILL.md` to `solution-knowledge-base` distinguishing runtime instincts (`.nexus/instincts/`) from durable solved-problem docs (`docs/solutions/`); and note in `catalog/skills/workflow/known-gaps-tracker/SKILL.md` how resolved gaps can graduate into solution docs. Keep edits minimal and trace each to closing the loop. Run `make validate`. Acceptance: cross-links resolve, validates clean, loop documented (capture -> plan -> review -> capture).

---

#### 3.3 — Cross-tool session-history query skill

- [x] T015 Create the session-query skill at catalog/skills/workflow/session-query/SKILL.md (+ extraction scripts)

**Objective**: Adopt CE's `ce-sessions` cross-tool session query: search local Claude/Codex/Cursor session logs for prior investigation context, script-first.

**Prompt**:
> Create `catalog/skills/workflow/session-query/SKILL.md` plus per-skill bundled scripts `scripts/discover-sessions.{sh,ps1}` and `scripts/extract-session.{py,ps1}` that read LOCAL session JSONL logs (Claude Code / Codex / Cursor) and extract a topic/branch/time-windowed digest of prior investigation context. All processing is local and zero-outbound (script-first architecture: the script does extraction, the skill presents). The `.py`/`.sh` scripts must have `.ps1` siblings (parity rule). Reference every script from SKILL.md (orphan-bundle clean). Distinguish from `[[session-history]]` / `[[generate-session-history]]` (generation) - this is query. Register in the three data files. Run `make validate`. Acceptance: validates clean, scripts referenced, zero outbound, registered.

---

#### 3.4 — Testing and Stabilization

- [x] T016 Run and stabilize Phase 3 tests, including session-query extraction tests (live skill-eval-loop deferred - DF-v24-4; PowerShell parity verified empirically)

**Objective**: Verify the loop wiring and session query at the heavier bar.

**Prompt**:
> Run `make validate` and `make lint`. Add pytest for the session extraction scripts against a small fixture JSONL set (assert digest fields, time-window filtering, zero network calls via static analysis). Run live `skill-eval-loop` trigger checks for `product-strategy` (if new) and `session-query`. Manually confirm the loop: a `docs/solutions/` entry created by `solution-knowledge-base` is discoverable by the planning grounding step added in T014. Fix all failures and iterate. Do not advance to Phase 4 until verified. After all tests pass, run /generate-session-history to document Phase 3.

---

### Phase 3 Exit Checklist

- [x] All sub-tasks completed
- [x] Session-query extraction tests pass; no outbound calls (13 passed; zero-outbound static analysis green on .py/.ps1/.sh)
- [x] Loop verified end-to-end (capture -> grounding read; implementation-plan Phase B.5 + generate-plan Step 2.5 both search docs/solutions and STRATEGY.md)
- [x] make validate + make lint green (validators direct: counts reconciled 244/35, orphan-bundle 0/0, quality 0 errors, 4 CI validators + solution-frontmatter exit 0; lint N/A - no shellcheck on host; repo 344 passed + skill-server 43 passed)
- [~] Live skill-eval-loop trigger checks (deferred - no model CLI on PATH; static trigger-surface check done; DF-v24-4)
- [x] Session history generated
- [x] Ready to advance to Phase 4

---

## Phase 4: Remaining Skill-Native

**Goal**: Adopt CE's crash-safe optimization persistence discipline into skill-eval-loop (A10) and a product-pulse report skill template (A11).
**Prerequisites**: None beyond Phase 1.
**Stability Gate**: skill-eval-loop documents write-then-verify checkpoints; the product-pulse skill validates and triggers correctly; tests green.

### Sub-tasks

#### 4.1 — Crash-safe optimization persistence discipline

- [x] T017 Add persistence-discipline guidance to catalog/skills/workflow/skill-eval-loop/SKILL.md

**Objective**: Adopt CE's `ce-optimize` persistence discipline (write each result to disk immediately, verify the write, re-read at phase boundaries, per-experiment crash-recovery markers) so long-running eval loops survive context compaction and crashes.

**Prompt**:
> Add a "Persistence discipline (crash-safe long runs)" section to `catalog/skills/workflow/skill-eval-loop/SKILL.md` (or a linked `references/persistence-discipline.md` if the body nears its size norm): write each eval/experiment result to disk immediately after measurement, verify the write by reading it back, re-read state from disk at every phase boundary (never trust in-memory state across compaction), keep the log append-only, and write per-experiment crash-recovery markers for resume. Re-author generically; do not name the source. If a reference file is added, link it (orphan-bundle clean). Run `make validate`. Acceptance: guidance present, validates clean.

---

#### 4.2 — Product-pulse report skill template

- [x] T018 [P] Create the product-pulse skill at catalog/skills/business-product/product-pulse/SKILL.md

**Objective**: Adopt CE's `ce-product-pulse`: a time-windowed report on usage / performance / errors / followups read from the user's own local telemetry sources.

**Prompt**:
> Create `catalog/skills/business-product/product-pulse/SKILL.md` that generates a single-page, time-windowed product-outcome report (usage, performance, errors, followups) from USER-SUPPLIED local data sources (log files, exported analytics, local metrics), saved to `docs/pulse-reports/<window>.md` as a browseable timeline. The skill reads only sources the user points it at; it introduces no new outbound call and no new data processor (state this explicitly in the body and the Common Rationalizations table). Include When NOT to use (no telemetry available). Register in the three data files (business-product category; update marketplace skill_count). Re-author generically. Run `make validate`. Acceptance: validates clean, registered, zero outbound asserted.

---

#### 4.3 — Testing and Stabilization

- [x] T019 Run and stabilize Phase 4 tests (live skill-eval-loop deferred - DF-v24-3; static trigger-surface + persistence dry-run passed)

**Objective**: Verify Phase 4 at the heavier bar.

**Prompt**:
> Run `make validate` and `make lint`. Run a live `skill-eval-loop` trigger check for `product-pulse`. Confirm the skill-eval-loop persistence-discipline section renders and is internally consistent (dry-run the documented checkpoint flow on a trivial eval). Fix all failures and iterate. Do not advance to Phase 5 until verified. After all tests pass, run /generate-session-history to document Phase 4.

---

### Phase 4 Exit Checklist

- [x] All sub-tasks completed
- [~] product-pulse trigger check passes (live deferred - no model CLI on PATH; static trigger-surface check done 7/7 + SKIP; DF-v24-3)
- [x] make validate + make lint green (validators direct: orphan-bundle 0/0 across 242 skills, all CI validators exit 0; lint N/A - no shell scripts; MCP skill-server 43 passed; repo tests 331 passed)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 5 (note: Phase 3 remains open - Phase 4 prereq was "None beyond Phase 1")

---

## Phase 5: Internal RE Builds (re-full)

**Goal**: Build the per-platform capability spec docs (A6) and the installer `--branch` testing affordance (A9) as fully local internal artifacts.
**Prerequisites**: None.
**Stability Gate**: One spec doc per supported platform exists and is accurate to the integration registry; the installer `--branch` flag clones and installs from a branch on both bash and PowerShell; installer probes pass.

### Sub-tasks

#### 5.1 — Per-platform capability spec docs

- [x] T020 Author per-platform capability specs under docs/specs/<platform>.md

**Objective**: Adopt CE's `docs/specs/*` per-platform capability references, reconstructed locally from the Nexus-Hub integration registry knowledge.

**Prompt**:
> Create `docs/specs/<platform>.md` for each platform Nexus-Hub targets (claude-code, codex, cursor, gemini, antigravity, opencode, copilot, nexus-ai), each documenting that platform's plugin/skill/command/agent/hook surface, instruction-file location, and known quirks. Derive the content from `scripts/lib/integrations/<platform>.py` and the AGENTS.md platform-coverage table; do not name the source repo. Add a `docs/specs/README.md` index. Keep each spec accurate to the current integration behavior. Run `make validate` (markdown style + no-personal-paths). Acceptance: one spec per integration, index present, validators clean.

---

#### 5.2 — Installer branch-based testing

- [x] T021 Add a --branch / -Branch flag to scripts/installer.sh and scripts/installer.ps1

**Objective**: Adopt CE's branch-based plugin testing: install the catalog from a pushed branch into a deterministic cache path without switching the user's checkout.

**Prompt**:
> Add a `--branch <name>` flag to `scripts/installer.sh` and the `-Branch <name>` parameter to `scripts/installer.ps1` (lockstep) that shallow-clones the repo at the given branch into a deterministic cache directory (e.g. `~/.nexus-hub/branches/<sanitized-branch>/`) and runs the install from that checkout, leaving the user's working copy untouched. Sanitize the branch name for filesystem safety. Document the flag in `--help` / `-Help` and in the installer section of README.md. Add an installer probe (dry-run / `--print-config`) test confirming the flag resolves the cache path. Acceptance: both installers accept the flag, help text updated, probe passes, no change to default behavior when the flag is absent.

---

#### 5.3 — Testing and Stabilization

- [x] T022 Run and stabilize Phase 5 tests

**Objective**: Verify the re-full builds.

**Prompt**:
> Run `make validate`, `make lint`, and the installer test suite. Confirm each `docs/specs/<platform>.md` matches the corresponding integration's actual behavior (spot-check workspace_dir / instruction_file against the subclass). Run the installer `--branch` / `-Branch` probe on both bash and PowerShell (dry-run; confirm cache-path resolution and no checkout switch). Fix all failures and iterate. Do not advance to Phase 6 until verified. After all tests pass, run /generate-session-history to document Phase 5.

---

### Phase 5 Exit Checklist

- [x] All sub-tasks completed
- [x] Per-platform specs accurate to the integration registry (20/20 instruction_file + workspace_dir spot-checks against the live INTEGRATION_REGISTRY config)
- [x] --branch flag works on bash + PowerShell; default behavior unchanged (probe resolves cache path + neutralizes traversal on both; 70/70 installer tests pass incl. the unchanged enterprise/check/init/traversal suites)
- [x] make validate + make lint + installer probes green (validators direct: JSON OK, unicode/no-personal-paths exit 0, orphan-bundle 0/0; bash -n OK both installers, shellcheck N/A on host; 7 new branch-flag probe tests pass)
- [x] Session history generated
- [x] Ready to advance to Phase 6

---

## Phase 6: Internal RE Builds (re-partial)

**Goal**: Build the local demo-capture skill (A12, upload step dropped) and the conventional-commit release/changelog script (A13, local alternative to the release-please Action).
**Prerequisites**: None.
**Stability Gate**: The demo-capture skill drives locally-installed capture tools and writes local artifacts only; the release script generates a changelog/version bump from conventional commits with no GitHub Action dependency; tests green.

### Sub-tasks

#### 6.1 — Local demo-capture skill

- [x] T023 Create the demo-capture skill at catalog/skills/workflow/demo-capture/SKILL.md (+ capture scripts)

**Objective**: Adopt CE's `ce-demo-reel` visual PR evidence, re-partial: keep the local capture (GIF / terminal recording / screenshots), drop the upstream upload/approval vendor surface.

**Prompt**:
> Create `catalog/skills/workflow/demo-capture/SKILL.md` plus `scripts/capture-demo.{py,ps1}` that capture visual PR evidence using LOCALLY-installed tools (asciinema/terminal recorder, ffmpeg for GIF, a headless browser for screenshots), with project-type-aware tier selection, writing artifacts to a local `docs/demos/` directory only. Explicitly DROP any upload/approval/hosting step (that is the dropped vendor surface; state this in the body). Scripts need `.py` + `.ps1` parity and must be referenced from SKILL.md (orphan-bundle clean). The skill degrades gracefully when a capture tool is absent (report which tool to install; never fail hard). Register in the three data files. Re-author generically. Run `make validate`. Acceptance: validates clean, local-only (no upload), scripts referenced, registered.

---

#### 6.2 — Conventional-commit release/changelog script

- [x] T024 Add a local release/changelog script and wire it into update-version / generate-changelog

**Objective**: Adopt CE's release automation as a LOCAL re-partial script (conventional-commit-driven version selection + changelog), avoiding the third-party release-please GitHub Action.

**Prompt**:
> Create `scripts/generate_release_changelog.py` (+ `.ps1` sibling) that parses conventional-commit messages since the last tag to compute the next semver bump (major/minor/patch) and generate a Keep-a-Changelog section, printing to stdout or a `--out` file. Wire it as an optional helper into the `update-version` and `generate-changelog` skills/commands (reference it; do not replace the existing manual flow). Register BOTH scripts as explicit-name copy steps in `scripts/installer.sh` AND `scripts/installer.ps1`. Do NOT add the release-please GitHub Action (that vendor piece is intentionally not adopted per the comparison Section 9.4). Add pytest at `tests/validators/test_generate_release_changelog.py` (bump detection from a fixture commit set; changelog formatting). Acceptance: pytest green, both installers register the scripts, no GitHub Action added.

---

#### 6.3 — Testing and Stabilization

- [x] T025 Run and stabilize Phase 6 tests (live skill-eval-loop deferred - DF-v24-6; static trigger-surface + graceful-degradation verified)

**Objective**: Verify the re-partial builds.

**Prompt**:
> Run `make validate`, `make lint`, and the new pytest. Run a live `skill-eval-loop` trigger check for `demo-capture`. Dry-run `scripts/generate_release_changelog.py` against the real repo history and sanity-check the proposed bump + changelog section against `CHANGELOG.md`. Confirm `demo-capture` degrades gracefully when a capture tool is missing (simulate absence). Fix all failures and iterate. Do not advance to Phase 7 until verified. After all tests pass, run /generate-session-history to document Phase 6.

---

### Phase 6 Exit Checklist

- [x] All sub-tasks completed (T023-T025)
- [x] demo-capture is local-only and degrades gracefully (no upload step; missing-tool capture returns captured=0 + install hint + exit 0 on both .py and .ps1)
- [x] release/changelog script registered in both installers; no GitHub Action added (both .py + .ps1 copy steps in installer.sh/.ps1; release-please Action NOT added; wired as optional helper into update-version + generate-changelog)
- [x] make validate + make lint + pytest green (validators direct: JSON OK at 245/workflow 36, orphan-bundle 0/0, quality 0 errors, 4 CI validators + solution-frontmatter exit 0; ruff check clean; 31 new tests + skill-server 43 + validators/skills 115 pass; lint shellcheck N/A - no new .sh. NOTE: 1 PRE-EXISTING installer test failure BG-v24-1, unrelated to Phase 6, recorded)
- [~] Live skill-eval-loop trigger check (deferred - no model CLI on PATH; static trigger-surface check done + graceful-degradation verified directly; DF-v24-6)
- [x] Session history generated for this phase
- [x] Ready to advance to Phase 7

---

## Phase 7: Catalog-Quality + Hygiene Remediation (ingested known-gaps)

**Goal**: Resolve nine ingested v2.3.0 known-gaps: catalog-quality debt, unicode/BOM/path cleanup, CI lint coverage, and code-search extractor work.
**Prerequisites**: Phase 1 (clean validation baseline).
**Stability Gate**: The four CI validators and the quality-heuristics pass run clean (no NEW warnings beyond accepted debt explicitly tracked); CI lints per-skill scripts; code-search eval recall/precision gates hold.

### Sub-tasks

#### 7.1 — Skill-stocktake remediation pass

- [x] T026 [from v2.3.0 known-gaps: WN-v23-4] Remediate the lowest-scoring skills surfaced by skill-stocktake (full sweep: 576 -> 0 quality warnings across all 245 skills; 218 skills edited)

**Objective**: Reduce the 574 quality-heuristics warnings (missing Common Rationalizations, prose-only Verification, missing Related Skills links) across grandfathered skills.

**Prompt**:
> Original reason: the non-blocking `python scripts/validate_skills.py --quality` pass reports 574 warnings across the catalog (missing Common Rationalizations tables, prose-only Verification sections, missing Related Skills links, a few over-long Tier-1 fields) - pre-existing debt in skills predating the size/section norms. Suggested next step (from known-gaps): run `skill-stocktake` (Full Stocktake) to rank worst-first, then remediate the lowest-scoring skills in batches. Implement: run skill-stocktake, remediate at least the worst batch (add Common Rationalizations tables, convert prose Verification to binary checklists, wire Related Skills links), and reduce the warning count materially; record the new count. Trace every edit to the warning being fixed. Run `make validate`. Acceptance: warning count materially reduced and recorded, no new errors.

---

#### 7.2 — Enrich security-operations skill bodies

- [x] T027 [from v2.3.0 known-gaps: DF-v23-2] Add platform-specific query examples to high-traffic security-operations skills (3 references/query-examples.md added + linked; orphan-bundle clean)

**Objective**: Optionally deepen the highest-traffic defensive skills with platform-specific examples.

**Prompt**:
> Original reason: the 15 v2.3.0 security-operations skills are conformant but concise (below the 160-280-line drafting band); enrichment was deferred. Suggested next step (from known-gaps): deepen the highest-traffic skills (`siem-detection-engineering`, `endpoint-edr-detection`, `cloud-audit-log-detection`) with platform-specific query examples (Splunk SPL / KQL / Sigma snippets) under each skill's `references/` subdir. Implement: add a `references/query-examples.md` to each of those three skills with re-authored, vendor-neutral-where-possible detection query examples, link it from the SKILL.md (orphan-bundle clean), and keep framework-mapping frontmatter intact. Run `make validate`. Acceptance: three references added and linked, validators clean.

---

#### 7.3 — Strip BOMs from instruction templates

- [x] T028 [P] [from v2.3.0 known-gaps: WN-v23-2] Remove UTF-8 BOM from templates/ai-instructions/**/*.md and drop the Makefile exclusion (15 BOMs stripped; Makefile + CI exclusion dropped)

**Objective**: Clear the 15 BOM-flagged Markdown files so the unicode-safety validator runs without the `templates/ai-instructions` exclusion.

**Prompt**:
> Original reason: `validate_unicode_safety.py` flags 15 `.md` files under `templates/ai-instructions/` for a leading UTF-8 BOM; the Makefile excludes the whole subtree to unblock. Suggested next step (from known-gaps): strip the BOMs and drop the `--exclude templates/ai-instructions` from the Makefile unicode call. Implement: remove the leading BOM bytes from each flagged Markdown file (preserve content), remove the `templates/ai-instructions` exclusion from the `make validate` unicode invocation, and re-run. Do not strip BOMs from `.ps1` files (Windows convention, exempt). Acceptance: unicode-safety passes on the subtree with no exclusion, files unchanged except the BOM.

---

#### 7.4 — Replace non-ASCII punctuation in compliance templates

- [x] T029 [P] [from v2.3.0 known-gaps: WN-v23-3] Convert em-dashes/curly quotes to ASCII in templates/development/compliance-review/**/*.md (3 files; --strict now 0 findings in the subtree)

**Objective**: Resolve the ~1034 unicode-safety warnings on English Markdown punctuation in the compliance-review templates.

**Prompt**:
> Original reason: `validate_unicode_safety.py` emits ~1034 WARN findings for em-dashes and curly quotes across English Markdown in `templates/development/compliance-review/` (and elsewhere), violating the ASCII-only English-Markdown rule. Suggested next step (from known-gaps): enumerate with `validate_unicode_safety.py --strict --path templates/development/compliance-review/` then bulk-replace em-dashes with `--` and curly quotes with straight ASCII via a one-shot script. Implement the replacement (em-dash/en-dash -> `--`/`-`, curly quotes -> straight, ellipsis -> `...`, NBSP -> space), scoped to the flagged English-Markdown files, and re-run `--strict` to confirm zero findings in that subtree. Acceptance: zero unicode-safety findings in the compliance-review templates, no semantic content change.

---

#### 7.5 — Redact personal paths in test fixtures

- [x] T030 [from v2.3.0 known-gaps: DF-v23-1] Replace real usernames with a placeholder in catalog/hooks/tests/test_classification_audit.py and drop the exclusion (redacted to `user`; audit 172/172; Makefile + CI exclusion dropped)

**Objective**: Clear the 8 personal-path findings in the test fixtures so `validate_no_personal_paths.py` runs without excluding `catalog/hooks/tests/`.

**Prompt**:
> Original reason: `validate_no_personal_paths.py` flags 8 `/Users/<user>/...` occurrences in `catalog/hooks/tests/test_classification_audit.py` (legitimate user-reported test cases); the Makefile excludes `catalog/hooks/tests/` to unblock. Suggested next step (from known-gaps): replace the real username with a `<user>` placeholder in the fixtures and confirm the classification logic still parses them, then drop the exclusion. Implement: redact the username to `<user>` (or a safe placeholder the classifier accepts), run the test file to confirm the classification assertions still pass, remove the `catalog/hooks/tests/` exclusion from the no-personal-paths `make validate` call, and re-run. Acceptance: no-personal-paths passes with no exclusion, the classification tests still pass.

---

#### 7.6 — Remove or repurpose the orphaned base-gemini-ide template

- [x] T031 [P] [from v2.3.0 known-gaps: DF-v23-3] Delete templates/ai-instructions/base-gemini-ide.md and update its references (deleted; gemini.py + instruction_merge.py comments updated; integration suite green)

**Objective**: Remove the orphaned instruction template no integration renders.

**Prompt**:
> Original reason: Phase 7 of v2.3.0 repointed the `gemini` integration from `base-gemini-ide.md` to the canonical `base-gemini.md`; `base-gemini-ide.md` is now rendered by no integration and referenced only by a code comment in `gemini.py` and the `instruction_merge.py` docstring. Suggested next step (from known-gaps): delete `base-gemini-ide.md` and update the two doc/comment references that name it (or repurpose it). Before deleting, confirm via grep that no integration selects it. Implement the deletion and update the `gemini.py` comment and the `instruction_merge.py` docstring to reference a still-existing example (e.g. point the marker-string example at an inline snippet). Run the integration test suite. Acceptance: file removed, references updated, integration tests green, no template selects a missing file.

---

#### 7.7 — Broaden CI shellcheck to per-skill scripts

- [x] T032 [P] [from v2.3.0 known-gaps: QG-v23-1] Extend the CI shellcheck step in .github/workflows/ci.yml to lint catalog/skills/**/scripts/*.sh (broadened to `find catalog -name '*.sh'`; bash -n clean on all 8 per-skill scripts)

**Objective**: Gate the per-skill helper `.sh` scripts in CI so a future regression is caught.

**Prompt**:
> Original reason: the CI `shellcheck` job lints only `scripts/installer.sh`, `install.sh`, and `catalog/hooks/*.sh`; per-skill helper scripts (e.g. `catalog/skills/security-operations/*/scripts/*.sh`, and the Phase-3/6 scripts this plan adds) are not gated. Suggested next step (from known-gaps): broaden the "Lint hook scripts" step in `.github/workflows/ci.yml` from `find catalog/hooks -name '*.sh'` to `find catalog -name '*.sh'` (or add a dedicated step linting `catalog/skills/**/scripts/*.sh`). Implement the broadening, then run shellcheck locally over the expanded set and fix any newly surfaced findings (the current targets are clean). Per the "never silently rewrite CI/CD configs" rule, make the CI edit explicit and minimal. Acceptance: CI step lints all `catalog/**/*.sh`, local shellcheck clean over the expanded set.

---

#### 7.8 — Next code-search language-extractor batch

- [x] T033 [P] [from v2.3.0 known-gaps: DF-v23-4] Add the next language extractors under extensions/nexus-code-search (Ruby + PHP + C + C++, coverage 6 -> 10; each fixture 100% recall/precision; remaining languages -> DF-v24-7)

**Objective**: Extend code-graph language coverage beyond the current Python/TS/Go/Rust/Java/C# set.

**Prompt**:
> Original reason: only 6 languages have extractors; ~14 remain (Ruby, PHP, C, C++, Swift, Kotlin, etc.), framework extractors and parameter-node parity for the new languages were deferred. Suggested next step (from known-gaps): implement the next demand batch (recommend Ruby + PHP + C/C++) following `extensions/nexus-code-search/.../extraction/languages/go.py`, each with an eval fixture clearing the 80% recall gate; add the matching tree-sitter grammar deps under the shared `<0.26` ceiling. Implement at least one new extractor (Ruby) end-to-end with its eval fixture and unit tests; scope the rest as follow-on if time-bound. Confirm the new grammar dep auto-distributes via the editable `pip install` (no installer copy-step needed). Acceptance: at least one new extractor passes its 80% recall fixture + unit tests, eval suite green, no DeprecationWarnings.

---

#### 7.9 — Code-search import-node precision residual

- [x] T034 [from v2.3.0 known-gaps: DF-v23-5] Resolve the python_app import-site precision residual in code_search (import/export nodes demoted by default; python_app precision 70% -> 100%, recall held 100%)

**Objective**: Lift the `python_app` fixture precision (70%) closer to 100% by handling import-statement nodes under name-scoped queries.

**Prompt**:
> Original reason: after name-scoped FTS (T029 in v2.3.0), aggregate precision is 96.2% but `python_app` sits at 70% because import-statement nodes whose `name` is the dotted import path match a name query (e.g. `make_user` matching `service.make_user`). Recall is unaffected (100%). Suggested next step (from known-gaps): either (a) widen the `python_app` answer keys to accept the legitimate import-site hits, or (b) rank/exclude `import`/`export`-kind nodes from default `code_search` results (they are references, not definitions) while keeping them reachable via `all_fields=true`. Implement option (b): demote or exclude import/export-kind nodes by default in `traverser`/`code_search`, keep them reachable via the existing `all_fields` opt-out, and re-run the eval. Add a `test_traverser.py` case. Acceptance: `python_app` precision improves toward 100% with recall held at 100%, `all_fields=true` still returns import nodes, tests green.

---

#### 7.10 — Testing and Stabilization

- [x] T035 Run and stabilize Phase 7 tests (all suites green: code-search 187, validators 115, hooks 415, integrations+installer 267, skill-server 43; eval recall/precision 100%; BG-v24-1 closed)

**Objective**: Verify all nine ingested cleanup items at the heavier bar.

**Prompt**:
> Run `make validate` (now with the BOM, personal-paths exclusions removed), `make lint`, the integration suite, the validators suite, and the nexus-code-search suite + eval. Confirm: the unicode/BOM/personal-paths validators pass with no exclusions for the remediated subtrees; the quality-warning count is materially reduced and recorded; CI shellcheck covers `catalog/**/*.sh`; the new extractor passes its recall gate; `python_app` precision improved. Fix all failures and iterate. Do not advance to Phase 8 until verified. After all tests pass, run /generate-session-history to document Phase 7.

---

### Phase 7 Exit Checklist

- [x] All nine ingested cleanup items resolved (T026-T034; WN-v23-2/3/4, DF-v23-1/2/3/4/5, QG-v23-1)
- [x] Makefile exclusions removed for the remediated subtrees (templates/ai-instructions unicode + catalog/hooks/tests personal-paths, in both Makefile and ci.yml)
- [x] Quality-warning count reduced and recorded (576 -> 0 across all 245 skills)
- [x] CI shellcheck covers catalog/**/*.sh (find catalog -name '*.sh'; bash -n clean on all 8 per-skill scripts)
- [x] Code-search eval recall/precision gates hold (all 10 fixtures 100%/100%; python_app precision 70% -> 100%; 4 new languages clear the 80% recall gate)
- [x] Session history generated
- [x] Ready to advance to Phase 8 (also closed BG-v24-1, the pre-existing installer.ps1 stale test; full suite green)

---

## Phase 8: Live Verification + Release Readiness (ingested known-gaps)

**Goal**: Close the four live-environment verification gaps and run the final catalog-green release-readiness gate.
**Prerequisites**: Phases 1-7 (the new skills must exist for the live eval runs).
**Stability Gate**: The two live-eval deferrals are run (or re-deferred with a dated reason); the Antigravity and cross-OS smoke gaps are resolved or re-deferred with dated reasons; `make validate` / `make lint` / `make test` are green and the `data/` registries are reconciled across the whole catalog.

### Sub-tasks

#### 8.1 — Live skill-eval-loop run for the three discipline skills

- [~] T036 [from v2.3.0 known-gaps: DF-v23-7] Run the live skill-eval-loop for verification-before-completion, receiving-code-review, using-git-worktrees (re-deferred 2026-06-02 - no model CLI on PATH; static trigger-surface check done; DF-v24-8)

**Objective**: Close the deferred live trigger verification for the three superpowers-adoption discipline skills.

**Prompt**:
> Original reason: v2.3.0 deferred the live `skill-eval-loop` trigger run for `verification-before-completion`, `receiving-code-review`, and `using-git-worktrees` (a heavy token-intensive operation); a static trigger-surface check was done instead. Suggested next step (from known-gaps): run the live `skill-eval-loop`, authoring a minimal `evals.json` per skill, confirming 1.0 trigger rate on a positive prompt and 0.0 on a negative, and tighten any under-triggering description per `skill-eval-loop/references/improvement-heuristics.md`. Implement the live run for all three skills and record the trigger rates. Acceptance: each skill triggers at 1.0 positive / 0.0 negative (or its description is tightened until it does); results recorded.

---

#### 8.2 — Live eval-harness trigger-techniques run

- [~] T037 [from v2.3.0 known-gaps: DF-v23-8] Run the three new eval-harness trigger techniques live (re-deferred 2026-06-02 - no model CLI on PATH; v2.3.0 dry-run + pure-logic + fixture-stream tests stand; DF-v24-9)

**Objective**: Close the deferred live run of premature-action detection, multi-turn replay, and cheap-model fragility in the optimizer.

**Prompt**:
> Original reason: v2.3.0 added premature-action detection, multi-turn replay, and cheap-model fragility modes to `scripts/optimize_skill_description.py`, validated via dry-run + pure-logic + fixture-stream tests only; the live end-to-end run was deferred. Suggested next step (from known-gaps): run each mode live against a real model CLI on a representative skill - confirm `premature_action` flips on a planted pre-Skill tool use, a multi-turn eval triggers at its `trigger_turn`, and a description's trigger rate is compared across the default and a cheaper `--model`. Implement the live runs (a good representative target is one of the Phase-2 review skills or a Phase-1 knowledge-base skill). Acceptance: each of the three modes is exercised live and behaves as designed; results recorded.

---

#### 8.3 — Antigravity CLI live-VM probe

- [~] T038 [from v2.3.0 known-gaps: WN-v23-5] Reconcile the four Antigravity CLI residuals against a live agy install or re-defer with a dated reason (re-deferred 2026-06-02 - agy binary not installable on host; docs-verified conventions stand; WN-v24-3)

**Objective**: Resolve (or dated-defer) the docs-verified-but-not-live-verified Antigravity CLI conventions.

**Prompt**:
> Original reason: v2.3.0 verified the Antigravity CLI conventions (binary `agy`; `.agents/` dir; Markdown workflows; `AGENTS.md`; `~/.gemini/antigravity-cli/` global) against Google's public docs but not a live `agy` install; four residuals remain (the `.agent/` vs `.agents/` codelab dissent, the exact global subpath, the `subagents/`/`rules/` subdirs, and whether `agy` requires a root `AGENTS.md`). Suggested next step (from known-gaps): run a live `agy --help` / `agy init` probe once the binary is installed and reconcile the four residuals; if root `AGENTS.md` is required, add a per-integration marker scheme so codex + antigravity2 can co-manage it. Implement: if `agy` is installable on the host, run the probe and reconcile; otherwise re-defer with a dated reason recorded in the v2.4.0 known-gaps file and `docs/archive/v2/v2.2/antigravity-cli-probe.md`. Acceptance: either the four residuals are reconciled against a live install, or a dated re-deferral is recorded (this is an acceptable outcome for a source release).

---

#### 8.4 — macOS + Linux installer smoke

- [~] T039 [from v2.3.0 known-gaps: DF-v23-6] Run the macOS full smoke and the Linux installer-probe/eval, or re-defer with a dated reason (re-deferred 2026-06-02 - Windows-only host; Windows empirical + CI-Linux green; DF-v24-10)

**Objective**: Close (or dated-defer) the cross-OS installer smoke gap before any packaged-binary release.

**Prompt**:
> Original reason: v2.3.0 closed WN-8 with Windows-empirical + CI-Linux-test-suite evidence, but the full macOS 14 smoke (sub-steps 1a-1l of `docs/archive/v2/v2.3/installer-smoke-post.txt`) and the Linux `installer.sh --print-config`/`--help` probes + `make eval` were not run (no macOS host; not in CI). Suggested next step (from known-gaps): run sub-steps 1a-1l on a macOS 14 host and the installer-probe/eval portion on an Ubuntu host before any packaged-binary release. Implement: if a macOS and/or Linux host is available, run the smokes and record results in a `docs/archive/v2/v2.4/installer-smoke.txt`; otherwise re-defer with a dated reason (v2.4.0 is a source release, so deferral is acceptable). Acceptance: smokes run and recorded, or a dated re-deferral is recorded in the v2.4.0 known-gaps file.

---

#### 8.5 — Final release-readiness gate

- [x] T040 Run the final catalog-green release-readiness gate across the whole repo (make validate exit 0; 1056 passed / 4 skipped / 0 failed across all suites; eval recall 100% / precision 100%; registries reconciled 245/21; zero new outbound verified)

**Objective**: Confirm the Definition of Done: all A-items shipped, all 15 ingested gaps resolved or dated-deferred, catalog green.

**Prompt**:
> Run `make validate`, `make lint`, and `make test` (full suites: catalog/hooks/tests, tests/integrations, tests/installer, tests/validators, nexus-skill-server, nexus-code-search + eval). Reconcile the `data/` registries one final time (skills.json count == array length, marketplace category counts, SKILL_INDEX rows) after all new skills landed. Verify zero new outbound calls / credentials / data processors were introduced anywhere in the plan (grep the new scripts/skills for network calls). Update `CHANGELOG.md` `[Unreleased]` with the v2.4.0 adoption summary. Confirm every A1-A13 item and every ingested known-gap is either resolved or recorded with a dated deferral in `docs/archive/v2/v2.4/known-gaps.md`. Fix all failures and iterate. After all tests pass, run /generate-session-history to document Phase 8 and the release-readiness result.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations to track (no constitution file is in force; all phases are designed to satisfy the de-facto `AGENTS.md` policy constraints). This table is intentionally empty and can be populated if a constitution is later ratified and a phase needs a justified exception.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none) | (n/a) | (n/a) |

---

### Phase 8 Exit Checklist

- [~] Live eval runs for the discipline skills and the eval-harness techniques (re-deferred 2026-06-02 - no model CLI on PATH; DF-v23-7 -> DF-v24-8, DF-v23-8 -> DF-v24-9; static trigger-surface checks stand)
- [x] Antigravity + cross-OS smoke gaps resolved or dated-deferred (dated re-deferrals: WN-v23-5 -> WN-v24-3 no agy binary; DF-v23-6 -> DF-v24-10 Windows-only host; both acceptable for a source release)
- [x] make validate + make lint + make test green across the whole repo (validate exit 0; lint shellcheck N/A on host / CI-Linux; 1056 passed / 4 skipped / 0 failed: skill-server 43, code-search 187, web-fetch 29, tests/ 382, hooks 415)
- [x] data/ registries reconciled; zero new outbound verified (skills.json 245/245, marketplace 21 cats sum 245, SKILL_INDEX 245/21; no network primitives in any new script)
- [x] All A1-A13 items shipped; all 15 ingested gaps resolved (11) or dated-deferred (4)
- [x] CHANGELOG [Unreleased] updated (compound-engineering v2.4.0 adoption summary added; renamed to [2.4.0] at the bump)
- [x] Session history generated

---

## Items explicitly NOT adopted (security / policy reasons)

These map to the comparison's Section 13 N-items. They do not appear in any phase.

- **N1: `ce-gemini-imagegen`** — routes image prompts to Google's Gemini image API. generation-as-service, an explicit Hard-No under the MCP Registry Policy. Covered LLM-natively by the existing `creative-generation` / `ui-component-generation`. Dropped.
- **N2: `ce-slack-research` + `ce-slack-researcher`** — sends query text to the Slack API and requires a Slack token. search-as-service over a vendor; introduces an outbound call and a credential. Defer to a user-supplied Slack MCP rather than ship it. Dropped.
- **N3: `ce-proof`** — integrates the Proof collaborative editor (vendor's own product). vendor-intrinsic, irrelevant to Nexus-Hub users, requires Proof auth. Dropped.
- **N4: `ce-riffrec-feedback-analysis`** — depends on the third-party Riffrec tool/format. Vendor-specific, niche. Dropped.
- **N5: `ce-test-xcode`** — requires the external XcodeBuildMCP server and macOS/Xcode; `ios-development` already exists. Dropped (revisit only if an iOS-testing skill is independently scoped).
- **N6: `ce-dhh-rails-style`** — opinionated Ruby/Rails-in-DHH-style guidance; out of scope for the language-agnostic catalog. Not recommended (scope).
- **N7: `coding-tutor` plugin** — a separate product (teach-me / quiz-me); different domain. Not recommended (scope).
- **N8: CE's minimal-frontmatter + commands-merged-into-skills conventions** — adopting either would regress Nexus-Hub's 3-tier loading (`summary_l0` / `overview_l1`) and the MCP `search_skills` index, and erase the auto-trigger vs explicit-invoke distinction. Not adopted (deliberate divergence).

---

## Source references

- Comparison: [docs/archives/v2/v2.3/comparison-compound-engineering-plugin.md](../../v2.3.0/comparison-compound-engineering-plugin.md) (Adoption Plan Section 11; Security/RE Assessment Section 9).
- Ingested gaps: [docs/archives/v2/v2.3/known-gaps.md](../../v2.3.0/known-gaps.md) (all 15 open items).
- Governing policy: `AGENTS.md` MCP Registry Policy + Installer-Aware-Changes rules.
