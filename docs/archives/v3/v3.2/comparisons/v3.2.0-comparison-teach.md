# Source Analysis: Nexus-Hub vs. "the /teach skill" (alexknowshtml/claude-skills)

**Version**: 3.2.0 (in development)
**Generated**: 2026-06-05
**Analyzer**: Claude Code -- compare-project command
**External Source**: https://github.com/alexknowshtml/claude-skills/blob/main/teach/SKILL.md
**Source Type**: Skill document (single GitHub blob, analyzed via the article flow)

---

## Section 1: Executive Summary

This analysis compares Nexus-Hub against the viral `/teach` skill: a Socratic mastery-confirmation loop that quizzes the human operator on what actually happened in a Claude Code session, item by item, and refuses to finish until every concept is confirmed. Fifteen actionable insights were extracted from the single `SKILL.md`. Eleven are already implemented in Nexus-Hub (often better) or are partial overlaps with existing session tooling; the genuinely novel cluster is four insights: the interactive Socratic quiz targeting the human, the "restate your understanding first" calibration move, the multiple-choice discipline, and the teach-someone-else mode. A catalog-wide grep for `socratic|quiz|confirm mastery` returned only an incidental hit in `spec-driven-development`, confirming Nexus-Hub has no human-knowledge-retention capability today.

The headline finding is a clean one: `/teach` is a real net-new capability, but it is `skill-native` under the MCP Registry Policy. Its two hardest pieces already exist in the catalog as separate skills (`session-query` ships a script-first, cross-platform, zero-outbound session extractor that is strictly better than `/teach`'s inline `grep`; `dev-progress-tracker` is the persistent dated-checklist pattern). The recommendation is to **selectively adopt**: build one new `workflow` skill (`session-teach-back`) that composes the existing extractor and checklist patterns with a new Socratic loop. Zero new dependency, credential, or outbound call. The one thing NOT to copy verbatim is `/teach`'s auto-commit-and-push-by-default behavior, which must be adapted to opt-in to respect the `git-guardrails` hook.

---

## Section 2: Source Overview

- **Artifact**: `teach/SKILL.md` in `alexknowshtml/claude-skills` ("battle-tested skills from a real production setup").
- **Author**: Alex Hillman (alexknowshtml).
- **Publication**: GitHub repository; the `teach` skill is one of seven (`reflect`, `pause`, `upskill`, `create-skill`, `pretty-page`, `teach`, `publish-oss`).
- **Topic**: Knowledge retention from AI coding sessions via Socratic questioning.
- **Key thesis**: After an AI session produces work, the human's understanding of *what was built and why* silently degrades. The fix is an explicit, item-by-item quiz against a persistent checklist sourced from the actual session transcript, with a hard gate: do not declare the debrief complete until every concept is confirmed by a correct answer.

**Scope note on the sibling skills.** The user pointed specifically at `teach`, and that focus is correct: of the seven skills in the repo, `teach` is the only one without a strong Nexus-Hub analog. The other six map cleanly onto existing catalog skills and are therefore **current-only strengths to preserve, not adoption candidates**:

| Sibling skill | Nexus-Hub analog (no adoption needed) |
|---|---|
| `/reflect` (session retrospective + quick wins) | `skill-eval-loop`, `session-history`, `continuous-learning` |
| `/pause` (save state, return prompt) | `session-history` "summarize from here" handoff + `continue-session` |
| `/upskill` (refresh existing skills) | `skill-eval-loop`, `create-skill-or-command` |
| `/create-skill` (session to skill) | `create-skill-or-command`, `create-custom-command` |
| `/pretty-page` (markdown to styled HTML) | `web-artifacts-builder`, `theme-tokens`, `generate-report` |
| `/publish-oss` (OSS publishing) | `shipping-and-launch` |

This is why the rest of this report concentrates entirely on `teach`.

---

## Section 3: Key Insights Extracted

Each insight is numbered and tagged with its source section in `teach/SKILL.md`.

1. **Socratic mastery-confirmation loop on the human.** The agent quizzes the *user* on each concept and marks it confirmed only after a correct answer. (Overview, Solo Mode Loop)
2. **Pushy one-line description.** "Quiz yourself on what actually happened... don't finish until everything's locked in." (Frontmatter)
3. **Three invocation modes plus a no-arg picker.** Topic-keyword search, direct file path (JSONL/markdown), `--student <name>` teach-others, and a "list 10 recent sessions" selector when no argument is given. (Usage Modes)
4. **Session source resolution.** Grep `~/.claude/projects` JSONL, rank by recency, extract assistant findings and user direction while skipping tool-call noise, disambiguate the top 3, then synthesize a 500-1000 word narrative as the teaching source. (Step 1)
5. **Dated, slugged, persistent checklist file.** `sessions/teaching/YYYY-MM-DD-<slug>.md` with YAML frontmatter (`mode`, `student`, `source`, `started`), semantic sections (The Problem / The Solution / Broader Context), `[ ]`/`[x]` checkboxes, and `n/total confirmed` progress at the top. (Step 2, Checklist Structure)
6. **Commit and push the checklist** with the conventional message `data(teaching): add <slug> teaching checklist`. (Step 2)
7. **Concrete-not-generic items.** Checklist items must be specific to the actual session (the real problem, why it existed, alternatives considered, design decisions, edge cases), never placeholder concepts. (Checklist Structure)
8. **Drill into WHY.** Surface the motivation behind each decision, not just what was done; ask follow-up why-questions before advancing. (Solo Mode Loop)
9. **Calibration opening move.** Ask the user to restate their understanding of the session in their own words first, then fill gaps without re-covering known material. (Solo Mode Loop)
10. **Immediate incremental state updates.** Re-read the checklist before each exchange; mark `[x]` immediately after each correct answer (never batch); show progress every 3-4 exchanges. (Solo Mode Loop, Rules)
11. **Hard completion gate.** Never offer to wrap up until 100% of items are `[x]`. (Rules)
12. **One question per exchange, concise (<2000 chars), adjustable depth.** Responses can be eli5 / eli14 / intern-level on request. (Rules)
13. **Multiple-choice discipline.** Vary the correct-answer position; do not reveal the answer until after the user responds. (Solo Mode Loop)
14. **Teach-someone-else mode.** Reframe the same checklist as a guide for explaining to a named student, tracking what the user has covered and confirmed the student understood. (Teaching Mode Loop)
15. **Internal source synthesis.** Do not narrate the grep/extract process; begin teaching directly. (Rules)

---

## Section 4: Relevance Analysis

| # | Insight | Status | Evidence / Notes |
|---|---------|--------|-----------------|
| 1 | Socratic mastery loop on the human | Missing | No catalog skill quizzes the human operator. Grep for `socratic\|quiz\|confirm mastery` across `catalog/` hit only `developer-experience/spec-driven-development/SKILL.md` incidentally. This is the core net-new capability. |
| 2 | Pushy one-line description | Already implemented | `AGENTS.md` "Description style: combat undertriggering" mandates pushy descriptions with trigger + SKIP phrases; `catalog/skills/workflow/create-custom-command/SKILL.md` applies it to commands. |
| 3 | Three modes + no-arg picker | Partially | `catalog/skills/workflow/session-query/SKILL.md` supports topic / branch / time-window / file query modes. The `--student` teach-others mode and the recent-session picker are absent. |
| 4 | Session source resolution | Already implemented (better) | `session-query` ships `scripts/discover-sessions.{sh,ps1}` + `scripts/extract-session.{py,ps1}`: a script-first, cross-platform (Claude/Codex/Cursor), zero-outbound JSONL extractor that does not pull raw transcripts into context. `/teach`'s inline `grep` is Claude-Code-only and noisier. |
| 5 | Dated persistent checklist file | Partially | `catalog/skills/workflow/dev-progress-tracker/SKILL.md` (docs/todos.md) and `session-history` both use `[ ]`/`[x]` checkbox files with progress metrics. A dated `mastery` checklist with `mode`/`student`/`source` frontmatter is a new variant of an established pattern. |
| 6 | Commit-and-push the checklist | Partially / adapt | `catalog/skills/workflow/code-commit-workflow/SKILL.md` supplies conventional-commit conventions, but auto-push by default conflicts with the `git-guardrails` hook and the global "destructive/outward git requires confirmation" rule. Adapt to opt-in. |
| 7 | Concrete-not-generic items | Already implemented | `session-history` content rules ("Never fabricate", "include actual errors"); `dev-progress-tracker` "specific, actionable, one sentence" task rule. |
| 8 | Drill into WHY | Partially | `catalog/skills/documentation/strategic-comments/SKILL.md` ("why, not what") and `architecture-decision-record` capture rationale, but never as an interactive quiz mechanic. |
| 9 | Calibration opening move | Missing | No catalog skill opens with "restate your understanding, then fill gaps." Part of the new loop. |
| 10 | Immediate incremental state updates | Already implemented | `dev-progress-tracker` rationalization "I will update todos.md at the end" -> rebutted; `session-history` iterative-refinement loop. |
| 11 | Hard completion gate | Already implemented (pattern) | `catalog/skills/orchestration/quality-gate-definitions/SKILL.md` is the reusable GO/NO-GO gate. Applying a gate to *human mastery* (not artifact state) is the new twist. |
| 12 | One-question / concise / adjustable depth | Partially | The active `learning` output style requests focused contributions; note the deliberate tension with the global CLAUDE.md rule to *batch* clarifying questions (that rule governs requirements gathering, not a teaching loop, so both can coexist). eli5/eli14/intern depth levels are new. |
| 13 | Multiple-choice discipline | Missing | No analog. |
| 14 | Teach-someone-else mode | Missing | Closest are `technical-writer` / `user-documentation` (produce docs), but neither is interactive coaching of a named student. |
| 15 | Internal source synthesis | Already implemented | "Do not narrate" appears across the catalog; `session-query` "presents the digest"; CLAUDE.md "Do not mention the skill lookup." |

**Tally**: Missing 4 (I1, I9, I13, I14) | Partial 5 (I3, I5, I6, I8, I12) | Already implemented 6 (I2, I4, I7, I10, I11, I15) | Not applicable 0.

---

## Section 5: Adoption Plan (preliminary)

The novel cluster (I1, I9, I13, I14) plus the new artifact variant (I5) and mechanic (I8) collapse into **one new skill**. The partials (I3, I12) become enhancements to that skill. The "already implemented" insights need no work; they are reused, not rebuilt. Ordering is finalized in Section 6 after the security assessment, but since every item is `skill-native` or reuses existing local infrastructure, the preliminary and final orderings coincide.

Proposed skill: **`session-teach-back`** (category `workflow`). "Teach-back" is the established pedagogy term for confirming understanding by having the learner restate, which is exactly insight I9. It slots into the existing `session-*` family.

### P0 (Immediate -- High value, Low effort)

| What | Source | Target | Effort | Dependencies | Risk |
|---|---|---|---|---|---|
| New `session-teach-back` SKILL.md: Socratic mastery loop (I1) + calibration opening (I9) + dated mastery checklist (I5) + drill-into-why (I8) + hard completion gate (I11 pattern). Source the session via the existing `session-query` extractor rather than inline grep (I4). | `teach/SKILL.md` Overview, Step 1-2, Solo Mode Loop, Rules | `catalog/skills/workflow/session-teach-back/SKILL.md` | Low | `session-query` (reuse), `quality-gate-definitions` (gate pattern) | None |
| Register the skill in the three catalog registries. | `AGENTS.md` "Register the skill" | `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` | Low | P0 skill written | Low (registry drift if skipped; `make validate` catches it) |

### P1 (Short-term -- High value, Medium effort)

| What | Source | Target | Effort | Dependencies | Risk |
|---|---|---|---|---|---|
| Add the `teach-someone-else` mode (I14) and eli5/eli14/intern depth levels (I12) to the same skill body. | `teach/SKILL.md` Teaching Mode Loop, Rules | `session-teach-back/SKILL.md` | Medium | P0 skill | Low |
| Add multiple-choice discipline (I13): vary answer position, reveal only after response. | `teach/SKILL.md` Solo Mode Loop | `session-teach-back/SKILL.md` | Low | P0 skill | None |

### P2 (Medium-term -- cross-linking and discoverability)

| What | Source | Target | Effort | Dependencies | Risk |
|---|---|---|---|---|---|
| Wire `[[session-teach-back]]` Related-Skills links bidirectionally. | n/a (catalog convention) | `session-query`, `session-history`, `dev-progress-tracker` Related Skills sections; mention in `using-nexus-hub` | Low | P0 skill | None |

### P3 (Backlog / explicitly deferred)

| What | Source | Target | Effort | Dependencies | Risk |
|---|---|---|---|---|---|
| Optional `sessions/teaching/`-style checklist auto-commit. | `teach/SKILL.md` Step 2 | `session-teach-back/SKILL.md` (opt-in only) | Low | P0 skill | See Section 8 N1 -- adapt, do not adopt the default |

---

## Section 6: Security and Risk Assessment (MANDATORY)

Every insight evaluated against the `AGENTS.md` MCP Registry Policy decision tree. The capability touches local session logs and (optionally) git, so data-flow is the relevant axis.

| # | Insight | RE Classification | Internal deliverable | Risk tier | Rationale |
|---|---------|-------------------|----------------------|-----------|-----------|
| 1 | Socratic mastery loop | `skill-native` | `session-teach-back` skill | None | Achieved entirely by instructing the agent's own LLM; no MCP, no outbound call (Policy tier 2). |
| 3 | Three modes | `skill-native` | skill modes | None | Pure prompt logic. |
| 4 | Session source resolution | `re-full` (already built) | reuse `session-query` scripts | Low | Reads local `~/.claude/projects` JSONL only; `session-query`'s extractor "imports no network module and opens no connection." Low only because it reads session transcripts that may contain sensitive content -- but strictly on-device. |
| 5 | Mastery checklist file | `skill-native` | local Markdown file | Low | Writes a local file; no egress. Low because it persists session content to disk (mitigated: keep under `docs/` or `.nexus/`, which are already git-aware). |
| 6 | Commit-and-push checklist | `skill-native` (adapt) | opt-in commit step | Low | Auto-push is an outward-facing git action; the global rule and `git-guardrails` hook require confirmation. Adapt to opt-in (see N1). |
| 8 | Drill into WHY | `skill-native` | skill prompt | None | Pure prompt logic. |
| 9 | Calibration opening | `skill-native` | skill prompt | None | Pure prompt logic. |
| 11 | Completion gate | `skill-native` | reuse `quality-gate-definitions` | None | Pure prompt logic. |
| 12 | One-question / depth | `skill-native` | skill prompt | None | Pure prompt logic. |
| 13 | Multiple-choice discipline | `skill-native` | skill prompt | None | Pure prompt logic. |
| 14 | Teach-someone-else mode | `skill-native` | skill mode | None | Pure prompt logic. |

**Threat-model delta.** Adopting `session-teach-back` introduces: zero new runtime dependencies, zero outbound-call destinations, zero credentials/API keys, zero source-code-or-prompt egress, and zero new commercial third-party relationships. It reads local session logs (already governed by `session-query`) and writes one local Markdown file. The only outward-facing action anywhere in the design is the optional checklist commit/push, which is gated on the existing `git-guardrails` confirmation hook.

**MCP Registry Policy verdict.** The entire capability lands at **tier 2 (LLM-native skill)** of the decision tree: it is achievable by instructing the agent directly, so it ships as a skill, not an MCP and not an external integration. The one piece that reads the filesystem (session sourcing) is **tier 3 / `re-full`** and is already satisfied by `session-query`'s local extractor. No registry entry, no `mcp-servers.json` change, no matrix row required.

**Recommendation ordering (Section 9.4-equivalent).** All adoption items are `skill-native` or reuse an existing `re-full` internal artifact, so they ship first and together. There are no `vendor-intrinsic` items (none) and no `drop-outright` capabilities (none); the only "drop" is a *default behavior* (auto-push), addressed as an adaptation in Section 8.

---

## Section 7: Implementation Sequence

Because everything is `skill-native` / reuse, this is a single-phase build with no RE backlog ahead of it.

1. **Confirm the reuse contract.** Verify `session-query`'s `scripts/extract-session.{py,ps1}` output (matched files, timestamps, branch mentions, snippets) is sufficient to synthesize the teaching narrative; if a longer narrative is needed, extend `session-query` rather than re-implementing extraction in the new skill. (Reuses I4.)
2. **Write `catalog/skills/workflow/session-teach-back/SKILL.md`** with the required section order (Title, When to Use incl. When NOT to use, Instructions, Common Rationalizations, Verification, Related Skills) and pushy frontmatter (trigger phrases: "teach me what we built", "quiz me on this session", "teach-back", "did I understand X"; SKIP: generating a session record -> `session-history`; querying past sessions -> `session-query`; task tracking -> `dev-progress-tracker`). Implements P0 insights I1, I5, I8, I9, I11. Keep the body <=500 lines per the size norm.
3. **Register** in `data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json` (increment `skill_count` for `workflow` and `total_skills`). Default security scores 100/100/95.
4. **Validate**: `make validate` (JSON integrity + skill-security scanner gate) and `make lint`. Confirm the catalog still passes the HIGH/CRITICAL gate (it will -- zero new scripts, zero outbound).
5. **Enhance** (P1): add teach-someone-else mode (I14), depth levels (I12), multiple-choice discipline (I13) to the same body.
6. **Cross-link** (P2): bidirectional `[[session-teach-back]]` links in `session-query`, `session-history`, `dev-progress-tracker`; one line in `using-nexus-hub`.
7. **Changelog**: add an entry under `## [Unreleased]` in `CHANGELOG.md`.

No installer edit is required: the skill folder is auto-copied recursively by both installers (it adds no top-level `scripts/<name>.py` artifact).

---

## Section 8: Risks and Considerations

- **Conflict with the global "batch clarifying questions" rule.** The user's CLAUDE.md mandates batching clarifying questions into one turn to conserve reasoning budget; `teach`'s one-question-per-exchange is the deliberate opposite. These do not actually collide -- the global rule governs *requirements gathering before acting*, whereas the teach-back loop's whole pedagogical value is the slow, one-at-a-time confirmation. The skill body MUST scope this explicitly ("this is a teaching loop, not requirements intake") so the agent does not mistakenly batch quiz questions.
- **Persisting session content to disk.** The mastery checklist captures what a session did. Keep it under a git-aware path (`docs/` or `.nexus/`), never write secrets into it, and let the `secret-scan` hook cover the write.
- **Scope discipline.** Resist re-implementing session extraction inside the new skill. The catalog already has `session-query`; duplicating its `grep` logic would create two divergent extractors and violate the reuse contract.
- **Do not add a 15th slash command.** v3.0.0 deliberately consolidated 41 commands into 14 verb-first commands. `/teach` as a standalone command would regress that consolidation. The capability must trigger by phrase as a skill, or (if a command surface is ever wanted) dispatch from an existing verb (e.g. `/session teach-back`), never as a new top-level command.

### Items explicitly NOT recommended for adoption (security / policy reasons)

- **N1 -- `/teach`'s auto-commit-and-push-by-default of the checklist (Step 2, `data(teaching): add <slug>` + push).** Not adopted as a default. Rationale: an unconditional `git push` is an outward-facing action that the global "destructive/outward-facing git requires confirmation" rule and the `git-guardrails` hook both forbid without explicit user authorization. Adapt to opt-in: the skill writes the local checklist and *offers* to commit/push; it never pushes unprompted. This is the only `teach` behavior reclassified from adopt to adapt -- the capability survives, the default does not.
- **N2 -- the hard-coded `sessions/teaching/` path and `TZ="America/New_York" date` invocation.** Not adopted verbatim. Rationale: Nexus-Hub is cross-platform (Windows-first for this user) and timezone-agnostic; the path convention should follow the catalog's existing `docs/`/`.nexus/` placement and use a platform-neutral date command. Pure form, not function -- adapt to convention.

No insight was classified `drop-outright`; the capability is sound and policy-clean. Only two of `teach`'s specific *defaults* (auto-push, hard-coded path/timezone) are rejected, both adapted rather than dropped.

---

## Appendix: Verification of This Report

- [x] Source acquired (the `teach/SKILL.md` content was fetched and its mechanics extracted section by section).
- [x] Current project analyzed before comparison (read `session-history`, `dev-progress-tracker`, `session-query`, `continuous-learning`, `intent-based-review`; grep-confirmed the socratic/quiz gap).
- [x] Every insight extracted and evaluated against the current project with file-path evidence.
- [x] Adoption items have concrete target locations (`catalog/skills/workflow/session-teach-back/SKILL.md` + three registries).
- [x] Section 6 Security and Risk Assessment present; every candidate has a risk tier and an RE classification.
- [x] MCP Registry Policy cited by name (tier 2 LLM-native; tier 3 `re-full` reuse).
- [x] Section 8 N-item block lists every reclassified item with a policy-grounded reason.
