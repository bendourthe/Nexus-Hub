# Plan -- Pre-Merge Verification + Finding-Escalation Doctrine (no-mistakes adoption)

**Project**: Nexus-Hub
**Version**: v3.9.0
**Slug**: adoption-no-mistakes
**Plan Type**: Feature / Enhancement (skill-native catalog enrichment; no new skill, command, hook, outbound call, dependency, or credential)
**Created**: 2026-06-25
**Goal**: Enrich the review, shipping, loop, and PR skills with the agent-facing verification doctrine that a local git-proxy verification gate (no-mistakes) encodes, leading with a three-way finding-action taxonomy and a verbatim human-escalation rule for intent-touching findings, and decline the Go runtime and its default-on telemetry, with zero new skill, command, hook, outbound call, dependency, or credential.

## Overview

This plan operationalizes the prioritized Adoption Plan in [docs/releases/v3/v3.9/comparisons/v3.9.0-comparison-no-mistakes.md](../comparison-no-mistakes.md). The source, `no-mistakes`, is a compiled Go control plane (a local bare-repo git proxy plus a daemon, TUI, and SQLite state machine) that runs an opinionated verification pipeline in a disposable worktree before a branch reaches the real remote. That is a host-side runtime, and Nexus-Hub has a standing decision (the v3.1.0 host-command decision, the v3.8.0 standalone-loop-runtime decline) that runtimes are referenced but never reimplemented in the catalog. The adoptable substance therefore lives almost entirely in the one agent-facing artifact the tool ships: its skill. This plan imports that doctrine as local Markdown enrichment of skills Nexus-Hub already owns.

Every recommended item is `skill-native` (the comparison placed N1 through N6 in the skill-native bucket; N7 is the single `re-partial` item, marked optional because the source itself deprioritizes it). With `reverse-engineer-first=true`, the skill-native bucket comes first, sequenced so the highest-value file leads: `intent-based-review` carries the P0 headline (the finding-action taxonomy), so it opens Phase 1, even though a P1 item (the canonical pre-merge gate) lands in Phase 2. The phasing principle is target-skill cohesion, so each SKILL.md is opened in exactly one phase, ordered by the value of the item it carries. The two declines (the Go gate runtime, pre-adjudicated `drop-outright`; and the default-on telemetry, an MCP Registry Policy hard-no on egress-by-default analytics) are recorded as declines, not built.

Delivery is local Markdown enrichment of seven existing skills across three phases:

- **Phase 1 (review doctrine, code-review category, highest value)**: `catalog/skills/code-review/intent-based-review/SKILL.md` (the finding-action taxonomy N1 and intent-as-review-oracle N3), `catalog/skills/code-review/receiving-code-review/SKILL.md` (the verbatim human-escalation rule N1), and `catalog/skills/code-review/multi-agent-code-review/SKILL.md` (round-history hygiene N4); cross-linking `catalog/skills/workflow/verification-before-completion/SKILL.md`.
- **Phase 2 (gate and loop doctrine, workflow category)**: `catalog/skills/workflow/shipping-and-launch/SKILL.md` (the canonical pre-merge gate N2 and the stop-at-the-human-boundary doctrine N6) and `catalog/skills/workflow/loop-engineering/SKILL.md` (the loop-side half of N6).
- **Phase 3 (PR body, optional session matching, consolidation)**: `catalog/skills/workflow/pr-description-writer/SKILL.md` (deterministic PR body from a review/fix audit trail N5), an explicit decision on `catalog/skills/workflow/session-query/SKILL.md` (the optional diff-to-session matching N7), the RE-matrix decline records, the registry-edit decision, CHANGELOG, and known-gaps.

Success looks like: the three-way finding-action taxonomy and the verbatim-escalation rule present in the review skills; intent captured as a verbatim, tradeoff-rich review oracle; round-history hygiene that stops an iterative review loop from re-raising user-ignored findings; a canonical pre-merge gate with a justified order in `shipping-and-launch`; the stop-at-the-human-boundary doctrine in `shipping-and-launch` and `loop-engineering`; an optional deterministic-PR-body pattern in `pr-description-writer`; an explicit, recorded decision on N7 (build now or defer to known-gaps); the runtime and telemetry declines recorded in `docs/policy/mcp-reverse-engineering-matrix.md`; every cross-link resolving; every edited SKILL.md body still under the 500-line norm; all content ASCII-only and conformant to the Markdown style guide; generic naming with no upstream attribution in any distributed artifact (no "no-mistakes", "kunchenguid", and no literal tokens such as `axi`, `TOON`, `auto-fix`, `ask-user`, `no-op`, `checks-passed`, `NO_MISTAKES_TELEMETRY`, or `a.kunchenguid.com`); the registry-edit decision made and validated; and the full validator chain green.

## Constitution Check

*GATE: Must pass before Phase 1. Re-check after Phase 1 design.*

No constitution file found at `docs/v3/v3.9/constitution.md` - skipping the formal check. Recommend running `/constitution` to establish project principles; this is informational, not blocking. The plan is nonetheless aligned with the standing governance that functions as Nexus-Hub's de-facto constitution (the `AGENTS.md` MCP Registry Policy and the Reverse-Engineering Attribution Rule): every recommended item is `skill-native` over an owned skill, introduces no outbound call, dependency, or credential, and uses generic artifact naming with no upstream attribution in the distributed content. The two declines are dropped precisely because they would violate that governance (a host-side runtime reverses the v3.1.0 / v3.8.0 runtime decisions; default-on telemetry is the egress-by-default analytics posture the policy classifies as a hard-no), and they are recorded as declines rather than smuggled into the plan.

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Review and escalation doctrine | `intent-based-review` gains the three-way finding-action taxonomy (N1, P0) and the intent-as-verbatim-review-oracle guidance (N3, P2); `receiving-code-review` gains the verbatim human-escalation rule for intent-touching findings (N1, P0); `multi-agent-code-review` gains round-history hygiene (N4, P2); `verification-before-completion` cross-linked | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 2 | Pre-merge gate and stop-at-boundary doctrine | `shipping-and-launch` gains a canonical pre-merge gate with a justified order (N2, P1) and the stop-at-the-human-decision-boundary doctrine (N6, P3); `loop-engineering` gains the loop-side stop-at-boundary / no-busy-poll note (N6, P3) | Strong reasoning tier, high effort (Claude Code: Opus 4.8, high) |
| 3 | PR body, optional session matching, consolidation | `pr-description-writer` gains an optional deterministic-PR-body-from-audit-trail pattern (N5, P3); an explicit build-or-defer decision is made on the diff-to-session matching enrichment of `session-query` (N7, re-partial, optional); the runtime and telemetry declines are recorded in the RE matrix; the registry-edit decision is made; CHANGELOG and known-gaps updated | Strong reasoning tier, medium effort (Claude Code: Opus 4.8, medium) |

The "Rec. model / effort" column is a best-effort planning-time assessment, recorded as platform-agnostic tier intent plus the concretely-enumerated Claude Code model. Live model enumeration was not available at plan time, so the concrete name follows the v3.8.0 / v3.9.0 precedent (Opus 4.8); `/implement` re-confirms each phase's recommendation against the then-current live model set before building.

## Phase 1: Review and escalation doctrine

**Goal**: Import the headline doctrine from the source's agent skill into the review skills: a three-way classification of every review finding (objective and mechanical, intent-challenging, or informational), the rule that an intent-challenging finding must be relayed to the human verbatim and never resolved by the agent (N1, the P0 headline), intent captured as a verbatim, tradeoff-rich review oracle rather than a diff summary (N3), and round-history hygiene so an iterative review loop does not re-raise a finding the user already chose to ignore (N4).
**Prerequisites**: None.
**Stability Gate**: `intent-based-review/SKILL.md` contains the three-way finding-action taxonomy and the intent-as-verbatim-oracle guidance; `receiving-code-review/SKILL.md` contains the verbatim human-escalation rule for intent-touching findings; `multi-agent-code-review/SKILL.md` contains the round-history hygiene rule; `verification-before-completion` is cross-linked; all cross-links resolve; every edited body remains under 500 lines; validators green; no upstream name or literal token in any distributed artifact.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: this phase authors the plan's highest-value doctrine (a finding taxonomy and a human-escalation rule) that must integrate cleanly with three existing review skills without contradicting them, and the escalation rule has a real safety dimension (an agent silently overriding deliberate user intent is the failure mode it prevents). Doctrine drift and an over-broad escalation rule that stalls routine fixes are the high-risk failure modes. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 1.1 -- Add the three-way finding-action taxonomy (N1)

**Objective**: Teach `intent-based-review` to classify every review finding by the action it implies (objective mechanical fix, intent-challenging escalation, or informational), so the review output routes findings correctly instead of treating all findings the same.

**Prompt**:
> In `catalog/skills/code-review/intent-based-review/SKILL.md`, add a section (aim for 16-24 lines) that teaches a three-way classification of every review finding by the action it implies, not just by severity. Use generic labels and define each: (1) a mechanical-fix finding is objective and low-risk (an ignored error return, a missing null check, a clear correctness, reliability, or security defect) that an agent may resolve on its own judgment; (2) an escalate-to-human finding challenges the user's deliberate intent or changes product behavior (it argues an intentional addition, removal, or guard should be undone, or questions a deliberate design or product choice) and is a decision only the user can make; (3) an informational finding is a note that needs no fix. State the sharp boundary rule explicitly: routine correctness, reliability, or security fixes stay in the mechanical-fix bucket even when the smallest correct fix reintroduces a little previously-deleted logic; the escalate bucket is reserved for findings that genuinely contest intent or product behavior, not for any change that touches deleted code. Note that the classification is what makes intent-based review actionable: a reviewer that cannot tell a deliberate decision from a mistake either rubber-stamps real defects or flags the user's own choices. Cross-link `[[receiving-code-review]]` (which carries the escalation discipline for the escalate bucket) and `[[verification-before-completion]]`. Apply the Reverse-Engineering Attribution Rule: describe the taxonomy generically and choose your own label words; do NOT name "no-mistakes" or "kunchenguid" and do NOT use the literal schema tokens `auto-fix`, `ask-user`, or `no-op`. Constraints: ASCII-only; follow `catalog/style-guides/markdown.md` (blank line before and after the heading and any list); do NOT modify the YAML frontmatter in this sub-task; keep the body under the 500-line norm. Acceptance: the three-way taxonomy is present with all three buckets defined, the mechanical-vs-escalate boundary rule is stated, the "tell a decision from a mistake" rationale is given, both cross-links resolve, and no upstream name or literal schema token appears.

---

#### 1.2 -- Add the intent-as-verbatim-review-oracle guidance (N3)

**Objective**: Sharpen `intent-based-review` so the intent used as the review oracle is the user's goal captured verbatim and enriched with decisions and tradeoffs, not a summary of the diff, with the failure mode of a thin intent stated explicitly.

**Prompt**:
> In `catalog/skills/code-review/intent-based-review/SKILL.md`, add or sharpen guidance (aim for 12-18 lines) on what the review's intent oracle should contain. Teach: the intent is what the user set out to accomplish (the goal or request behind the work, in the user's terms), NOT a description of the diff or the files changed; capture the nuance a reviewer reading only the diff would not know -- the user's goal, the specific decisions and tradeoffs they made along the way, any constraints or approaches they ruled in or out, and anything they explicitly asked for that would otherwise look surprising in the diff; err on the side of completeness, not brevity (a few sentences to a short paragraph is normal). State the failure mode plainly: a thin one-line intent makes the review flag things the user already deliberately chose, producing false escalations under the taxonomy from sub-task 1.1. Note that intent known directly from the live conversation is more reliable than intent reconstructed after the fact from session transcripts (faster and less error-prone), which is why the agent should pass what it learned from the conversation rather than mine logs when it already knows the goal. Tie this to the taxonomy: a rich intent is what lets the reviewer place a finding in the mechanical-fix bucket rather than the escalate bucket. Apply the Reverse-Engineering Attribution Rule (generic; no upstream names; no `--intent` literal flag token). Constraints: ASCII-only; Markdown style guide; no frontmatter change in this sub-task; body under 500 lines. Acceptance: the guidance states intent is the goal not the diff, lists the decisions/tradeoffs/ruled-out content to capture, states the thin-intent failure mode, prefers live-conversation intent over transcript reconstruction, and ties back to the taxonomy.

---

#### 1.3 -- Add the verbatim human-escalation rule (N1, receiver half)

**Objective**: Teach `receiving-code-review` that when the agent encounters a finding that challenges deliberate intent or product behavior, it must relay the finding to the user verbatim and never approve, fix, or skip it on its own.

**Prompt**:
> In `catalog/skills/code-review/receiving-code-review/SKILL.md`, add a section (aim for 12-18 lines) on escalating intent-touching findings to the human. Teach: when acting on review feedback, a finding that challenges the user's deliberate intent or changes product behavior (per the taxonomy in `[[intent-based-review]]`) is a decision that belongs to the user, not the agent; the agent must NOT approve, fix, or skip it on its own judgment. Instead, stop and bring it to the user before responding: relay the finding as written (its location and full description, verbatim), do not paraphrase, do not summarize away the detail, and do not pre-judge the answer; then translate the user's decision into the action (fix with the user's guidance, accept, or skip). Contrast this with mechanical-fix findings, which the agent may resolve on its own. State the one standing exception: when the user has given explicit standing consent to drive the work unattended, the agent may resolve escalate-bucket findings automatically; absent that consent, it stops and asks. Tie this to the skill's existing anti-performative-agreement stance: relaying a finding verbatim and refusing to silently resolve it is the same discipline (no performative compliance) applied to intent-touching findings. Cross-link `[[intent-based-review]]` (the taxonomy) and `[[verification-before-completion]]`. Apply the Reverse-Engineering Attribution Rule: generic description; no upstream names; no literal `--yes`, `axi`, or `ask-user` tokens. Constraints: ASCII-only; Markdown style guide; no frontmatter change in this sub-task; body under 500 lines. Acceptance: the verbatim-escalation rule is present, names the no-self-resolution rule and the relay-verbatim discipline, states the standing-consent exception, ties to the anti-performative-agreement stance, and both cross-links resolve.

---

#### 1.4 -- Add round-history hygiene to iterative review (N4)

**Objective**: Teach `multi-agent-code-review` (or the iterative-review loop guidance) not to re-report a finding the user previously left unaddressed, unless the code now presents a materially different issue.

**Prompt**:
> In `catalog/skills/code-review/multi-agent-code-review/SKILL.md`, add a short rule (aim for 8-14 lines) on round-history hygiene for multi-round review. Teach: when a review runs more than once over the same change (a re-review after a fix round, or a follow-up pass), carry a sanitized history of which findings were surfaced in earlier rounds and which the user chose to leave unaddressed; on a follow-up pass, do NOT re-report a finding the user already ignored unless the code now presents a materially different issue at that location. State the failure mode this prevents: without round-history hygiene, an iterative review loop re-surfaces the same rejected finding every round, which trains the user to ignore the reviewer and buries genuinely new findings in repeated noise. Note that a finding the user explicitly deferred is a decision (it belongs in the escalate-bucket history from `[[intent-based-review]]`), so re-raising it unchanged is a form of performative re-review. Distinguish "the same finding" (do not re-raise) from "a materially changed issue at the same location" (do raise, and say what changed). Cross-link `[[intent-based-review]]` and `[[loop-engineering]]`. Apply the Reverse-Engineering Attribution Rule (generic; no upstream names; no literal `round`, `step rounds`, or `user_fix` tokens). Constraints: ASCII-only; Markdown style guide; no frontmatter change in this sub-task; body under 500 lines. Acceptance: the round-history hygiene rule is present, states the re-surface-noise failure mode, distinguishes unchanged from materially-changed findings, and both cross-links resolve.

---

#### 1.5 -- Testing and Stabilization

**Objective**: Validate the Phase 1 edits and iterate until stable before advancing.

**Prompt**:
> Validate the Phase 1 edits to `catalog/skills/code-review/intent-based-review/SKILL.md`, `catalog/skills/code-review/receiving-code-review/SKILL.md`, and `catalog/skills/code-review/multi-agent-code-review/SKILL.md`. Run `make validate` if `make` is on PATH; otherwise run the documented Windows fallback directly: `python scripts/validate_skills.py --verbose` (JSON catalog integrity plus the orphan-bundle audit) and the catalog dangling-wikilink audit. Confirm: (1) validators exit 0; (2) no new orphan bundles; (3) no dangling wikilinks (`[[intent-based-review]]`, `[[receiving-code-review]]`, `[[verification-before-completion]]`, `[[loop-engineering]]` all resolve); (4) every added line is ASCII-only (no em-dashes, en-dashes, curly quotes, or ellipsis characters); (5) each edited SKILL.md body is under 500 lines (if one would exceed, move the longest new subsection into a `references/` file linked from SKILL.md and re-run the orphan-bundle audit); (6) grep the diff for "no-mistakes", "kunchenguid", "axi", "TOON", "auto-fix", "ask-user", "no-op", and "--intent" and expect zero matches in the distributed artifacts (Reverse-Engineering Attribution Rule); (7) confirm the taxonomy in `intent-based-review`, the escalation rule in `receiving-code-review`, and the round-history hygiene in `multi-agent-code-review` are mutually consistent (the escalate bucket, the relay-verbatim rule, and the do-not-re-raise rule all reference the same notion of an intent-touching finding). Fix any failure and re-run until all checks pass. Then run `/session history` to document Phase 1.

---

## Phase 2: Pre-merge gate and stop-at-boundary doctrine

**Goal**: Add to `shipping-and-launch` a canonical pre-merge verification gate (a fixed, justified sequence of checks so that "passed the gate" means the same thing every time, N2) and the doctrine to return control at a human-owned decision point rather than blocking or busy-polling (N6), with the loop-side half of the stop-at-boundary doctrine added to `loop-engineering`.
**Prerequisites**: Phase 1 complete (the gate's review step references the finding taxonomy and escalation rule established in Phase 1).
**Stability Gate**: `shipping-and-launch/SKILL.md` contains a canonical pre-merge gate section (an ordered sequence with the one-line rationale for each ordering decision, cross-linking the per-step skills) and the stop-at-the-human-decision-boundary doctrine; `loop-engineering/SKILL.md` contains the loop-side no-busy-poll note; all cross-links resolve; every edited body remains under 500 lines; validators green; no upstream name or literal token in any distributed artifact.
**Recommended model**: Strong reasoning tier, high effort. Concrete (Claude Code): Opus 4.8, high effort. Rationale: the canonical gate must reconcile with the checks already taught across `pre-commit-checklist`, `code-commit-workflow`, `verification-before-completion`, and `/review` without duplicating or contradicting them, and the ordering rationale must be correct (a wrong order is worse than no doctrine). Reconciliation drift across several existing skills is the failure mode. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 2.1 -- Add the canonical pre-merge verification gate (N2)

**Objective**: Add to `shipping-and-launch` a single canonical pre-merge gate: a fixed, ordered sequence of checks run before a change is shared, with a one-line rationale for each ordering decision, so the meaning of "passed the gate" is stable across repos.

**Prompt**:
> In `catalog/skills/workflow/shipping-and-launch/SKILL.md`, add a section titled "## Canonical Pre-Merge Gate" (aim for 20-30 lines). Teach a fixed, ordered sequence of pre-merge checks and the reason for the order, framing it as: an opinionated, stable gate exists so that "this change passed the gate" means the same thing every time, instead of each change inventing its own ad hoc checklist. State the sequence and the one-line rationale per step: review the diff first (the reviewer reads fresh code before any fix churns it); run tests next and gather verification evidence; update documentation after tests (so docs are written against code known to work); run lint and static analysis last among local checks (so it does not churn over code that may still change); only after all local checks pass, commit and push, open or update the PR, and watch CI. Make clear which existing skills own each step and cross-link them: `[[intent-based-review]]` and `[[multi-agent-code-review]]` (review), `[[verification-before-completion]]` and `[[demo-capture]]` (test evidence), `[[pre-commit-checklist]]` (the local lint/secret/test gate), `[[code-commit-workflow]]` (commit and push), `[[pr-description-writer]]` (the PR), and `[[git-branching-workflow]]` for the rebase-onto-fresh-upstream step. State that the order is opinionated on purpose and that per-run skips are a deliberate exception, not a reason to reorder. Apply the Reverse-Engineering Attribution Rule: describe the gate generically; do NOT name "no-mistakes" or use the literal pipeline-step token string or the product's exact step names as a branded sequence. Constraints: ASCII-only; Markdown style guide (blank line before and after the heading and any list); no frontmatter change in this sub-task; body under 500 lines (push the per-step detail into a `references/` file linked from SKILL.md if it would exceed). Acceptance: the canonical gate section names the ordered sequence with a per-step ordering rationale, states the "stable meaning" payoff, cross-links the per-step skills (all wikilinks resolve), and notes per-run skips as the deliberate exception.

---

#### 2.2 -- Add the stop-at-the-human-decision-boundary doctrine (N6, shipping half)

**Objective**: Teach `shipping-and-launch` to return control to the human at a human-owned decision point (for example, a PR validated and CI-green but not yet merged) rather than blocking or busy-polling for the human action.

**Prompt**:
> In `catalog/skills/workflow/shipping-and-launch/SKILL.md`, add a short subsection (aim for 8-12 lines) on stopping at the human-decision boundary. Teach: distinguish "validated and ready for a human decision" from "the human decision was made". When an agent reaches a point that is gated on a human-owned action (most commonly: the change is validated, CI is green, and the PR is open, but the merge is the human's call), the agent should stop driving, tell the user what is ready and what decision is theirs (with the link they need), and NOT block, poll, or re-run waiting for the human to act. State the failure mode: an agent that busy-waits for a human merge wastes a turn loop and can re-trigger work; the correct behavior is to hand back control with a crisp summary and the specific decision requested. Note this generalizes beyond merges to any human-owned gate. Cross-link `[[loop-engineering]]` (which carries the loop-side half of this rule) and `[[verification-before-completion]]`. Apply the Reverse-Engineering Attribution Rule: generic; no upstream names; do NOT use the literal outcome tokens `checks-passed` or `passed`. Constraints: ASCII-only; Markdown style guide; no frontmatter change in this sub-task; body under 500 lines. Acceptance: the subsection distinguishes ready-for-human-decision from decision-made, states the no-busy-poll rule and its failure mode, generalizes beyond merges, and both cross-links resolve.

---

#### 2.3 -- Add the loop-side no-busy-poll note (N6, loop half)

**Objective**: Add to `loop-engineering` a one-to-three-line note that a loop must terminate or hand back at a human-owned decision point rather than spinning iterations waiting for a human action.

**Prompt**:
> In `catalog/skills/workflow/loop-engineering/SKILL.md`, where the loop's exit and control conditions are discussed (the Exit-Signal Protocol or the Workflow-Control Patterns section), add a short note (3-5 lines): a loop must not spend iterations busy-polling for a human-owned action (an approval, a merge, an external signoff); when the loop reaches a point gated on a human decision, it should hand control back with a crisp summary of what is ready and what decision is requested, and treat the human action as an external resume signal rather than a condition to spin on. Tie this to the existing exit-signal and stall-detection material (a loop that re-runs waiting for a human is a no-progress signature). Cross-link `[[shipping-and-launch]]` (which carries the shipping-side half of this rule). Apply the Reverse-Engineering Attribution Rule (generic; no upstream names; no literal outcome tokens). Constraints: ASCII-only; Markdown style guide; no frontmatter change in this sub-task; `[[shipping-and-launch]]` must resolve; body under 500 lines. Acceptance: the no-busy-poll-for-a-human note is present, tied to the existing exit-signal/stall material, and the cross-link resolves.

---

#### 2.4 -- Testing and Stabilization

**Objective**: Validate the Phase 2 edits and iterate until stable before advancing.

**Prompt**:
> Validate the Phase 2 edits to `catalog/skills/workflow/shipping-and-launch/SKILL.md` and `catalog/skills/workflow/loop-engineering/SKILL.md` (and any new `references/` file under shipping-and-launch). Run `make validate` (or the fallback: `python scripts/validate_skills.py --verbose` plus the dangling-wikilink audit). Confirm: (1) validators exit 0; (2) orphan-bundle audit clean (any new reference file is linked from SKILL.md; existing reference files remain linked); (3) no dangling wikilinks (`[[intent-based-review]]`, `[[multi-agent-code-review]]`, `[[verification-before-completion]]`, `[[demo-capture]]`, `[[pre-commit-checklist]]`, `[[code-commit-workflow]]`, `[[pr-description-writer]]`, `[[git-branching-workflow]]`, `[[loop-engineering]]`, `[[shipping-and-launch]]` all resolve); (4) all added lines ASCII-only; (5) each edited body is under 500 lines (if not, move the per-step gate detail into a reference file and re-validate); (6) grep the diff for "no-mistakes", "kunchenguid", "checks-passed", and the literal product step-sequence string and expect zero matches in the distributed artifacts; (7) confirm the canonical gate does not contradict the checks already taught in `pre-commit-checklist`, `code-commit-workflow`, or `verification-before-completion` (it should cross-link and order them, not redefine them). Fix any failure and re-run until green. Then run `/session history` to document Phase 2.

---

## Phase 3: PR body, optional session matching, and consolidation

**Goal**: Add an optional deterministic-PR-body-from-audit-trail pattern to `pr-description-writer` (N5), make and record an explicit build-or-defer decision on the optional diff-to-session matching enrichment of `session-query` (N7), record the runtime and telemetry declines in the RE matrix, make the registry-edit decision, and update CHANGELOG and known-gaps.
**Prerequisites**: Phases 1 and 2 complete (the registry-edit decision depends on the final state of the edited skills; the PR-body pattern references the review/fix audit trail shaped by the Phase 1 review doctrine).
**Stability Gate**: `pr-description-writer/SKILL.md` carries the optional deterministic-PR-body-from-audit-trail pattern; an explicit, recorded decision exists on N7 (built in `session-query` with a matrix row, or deferred to known-gaps); the RE matrix records the runtime decline (with the v3.1.0 / v3.8.0 precedent) and the telemetry cautionary; the registry-edit decision is made and validated; CHANGELOG `## [Unreleased]` and `docs/v3/v3.9/known-gaps.md` updated; validators green; no upstream name or literal token in any distributed artifact.
**Recommended model**: Strong reasoning tier, medium effort. Concrete (Claude Code): Opus 4.8, medium effort. Rationale: the PR-body pattern is a low-complexity articulation over an existing skill, and the rest is a bounded decision (N7) plus bookkeeping (matrix rows, registry decision, changelog); lower risk than Phases 1 and 2. Strong tier per the no-degradation default; medium effort because the work is articulation and recording rather than new doctrine design. `/implement` re-confirms against the then-current models.

### Sub-tasks

#### 3.1 -- Add the deterministic-PR-body-from-audit-trail pattern (N5)

**Objective**: Add to `pr-description-writer` an optional pattern that builds the risk and testing sections of a PR body deterministically from a recorded review-and-fix audit trail, rendered as an issue-then-fix-then-verification narrative, rather than as free-authored prose.

**Prompt**:
> In `catalog/skills/workflow/pr-description-writer/SKILL.md`, add an optional pattern (aim for 12-18 lines) titled along the lines of "Building the risk and testing sections from an audit trail". Teach: when the change went through a recorded review-and-fix process (review findings, the fixes applied, and the re-check results are available as a trail), the PR body's risk-assessment and testing sections can be built deterministically from that trail instead of written freehand. Render the fix history as an issue-then-fix-then-verification narrative: for each finding that was fixed, state the issue, the fix applied, and then either the successful re-check or the findings still open after that fix; this gives a reviewer visibility into what was found, what was changed, and how many attempts it took. State the benefit: a PR body derived from a real audit trail is harder to inflate and easier to trust than authored prose, and it surfaces the fixes the original change missed. Frame this as an optional enrichment for when a trail exists, not a replacement for the skill's existing summary / how-to-test / risk / reviewer-notes structure. Cross-link `[[intent-based-review]]` and `[[multi-agent-code-review]]` (the review process that produces the trail) and `[[verification-before-completion]]`. Apply the Reverse-Engineering Attribution Rule: generic; no upstream names; do NOT use literal tokens such as `step rounds`, `rounds`, or `prsummary`. Constraints: ASCII-only; Markdown style guide; no frontmatter change unless 3.4 decides otherwise; body under 500 lines. Acceptance: the optional pattern is present, describes building risk/testing sections from an audit trail as an issue-then-fix-then-verification narrative, states the trust/anti-inflation benefit, is framed as optional and additive, and the cross-links resolve.

---

#### 3.2 -- Decide and record: optional diff-to-session matching for session-query (N7)

**Objective**: Make and record an explicit decision on the one reverse-engineerable item (N7): either enrich `session-query` with a diff-to-session matching heuristic now, or defer it to known-gaps with a reason. Default to defer, because the source itself prefers verbatim live intent over transcript reconstruction (the lesson behind N3).

**Prompt**:
> Decide whether to build N7 now or defer it, and record the decision. Context: N7 would enrich `catalog/skills/workflow/session-query/SKILL.md` with a heuristic that matches a code diff to the local agent session that produced it (discover candidate sessions in the commit time window, score each by file-overlap against the diff, then summarize the chosen session into intent). This is the only `re-partial` item in the comparison; it is a local, read-only heuristic over session logs already in `session-query`'s scope, and it requires a row in `docs/policy/mcp-reverse-engineering-matrix.md` because it reads transcript content. It is marked optional because the source tool itself deprioritizes transcript inference in favor of intent passed verbatim from the live conversation (which is exactly the N3 guidance delivered in Phase 1), so its value is low when the agent already knows the intent. RECOMMENDED DEFAULT: defer. If deferring, add an entry to `docs/v3/v3.9/known-gaps.md` recording N7 as a deferred, optional, reverse-engineerable enrichment of `session-query` (diff-overlap-plus-time-window matching), with the reason (verbatim live intent is preferred and already delivered via N3; build only if a concrete need for after-the-fact intent recovery appears), and stop. If instead there is a clear appetite to build it now: add a short section to `session-query/SKILL.md` describing the diff-overlap-plus-time-window matching heuristic and the redaction posture that already governs session reads, add the required RE-matrix row classifying it `re-partial` with the comparison report cited, and confirm the existing redaction discipline in `session-query` covers transcript content. Apply the Reverse-Engineering Attribution Rule either way (generic; no upstream names; no literal `internal/intent`, `Discover`, or `Summarize` tokens in any distributed artifact). Constraints: ASCII-only; Markdown style guide. Acceptance: a decision is made and recorded (deferred to known-gaps with a reason, OR built in `session-query` with an RE-matrix row and redaction confirmation); the choice is internally consistent with the N3 guidance from Phase 1.

---

#### 3.3 -- Record the runtime and telemetry declines in the RE matrix

**Objective**: Add durable matrix rows so a future comparison recognizes the declined Go runtime as already-adjudicated and records the default-on-telemetry posture as a cautionary anti-pattern.

**Prompt**:
> In `docs/policy/mcp-reverse-engineering-matrix.md`, add a new dated section (modeled on the existing declined-item sections) recording the v3.9.0 adoption-cycle decisions for this comparison. Record as `drop-outright` (citing the v3.1.0 host-command decision and the v3.8.0 standalone-loop-runtime row as precedent): a compiled, host-side verification-gate runtime (a local git-proxy daemon plus a terminal UI and a local state database). State that it reverses no decision: the catalog references host runtimes and never reimplements them, and the doctrine the runtime encodes was imported as the skill-native items in this cycle. Record as a cautionary not-recommended item (a security anti-pattern, not an adoption): default-on usage telemetry that posts to a third-party-owned analytics endpoint with opt-out only; note that this is the egress-by-default analytics posture the MCP Registry Policy classifies as a hard-no, and that it is the principal reason the comparison recommends importing the doctrine but not the tool. Reference [docs/releases/v3/v3.9/comparisons/v3.9.0-comparison-no-mistakes.md](../comparison-no-mistakes.md) as the full analysis. Apply the Reverse-Engineering Attribution Rule in the distributed-artifact sense: the comparison report file name already exists and may be cited; do NOT introduce the upstream product name into any skill body, and in the matrix prose prefer a generic description (a "local git-proxy verification-gate runtime") with the product name used only as the report's subject if at all. Constraints: ASCII-only; Markdown style guide; do not alter existing matrix rows. Acceptance: the new dated section records the runtime as `drop-outright` with the precedent citation and the telemetry as a cautionary not-recommended item with the MCP Registry Policy named, both referencing the comparison report.

---

#### 3.4 -- Registry-edit decision, CHANGELOG, known-gaps, and full consolidation

**Objective**: Decide whether any enriched skill's frontmatter summary changed enough to require the three-registry update, then finalize cross-file consistency, CHANGELOG, and known-gaps.

**Prompt**:
> Make the registry-edit decision and finalize. (1) Read the final `summary_l0` and `overview_l1` of every skill edited in this plan (`intent-based-review`, `receiving-code-review`, `multi-agent-code-review`, `shipping-and-launch`, `loop-engineering`, `pr-description-writer`, and `session-query` if N7 was built). If a new headline capability materially changes a one-line summary (the most likely candidate is `intent-based-review` gaining the finding-action taxonomy and human-escalation routing as a headline capability), update that skill's `summary_l0` / `overview_l1` AND the three registries (`data/SKILL_INDEX.md`, `data/skills.json`, `data/marketplace.json`) per the AGENTS.md registration rules, and bump the skill's footer version where the skill carries one. If the summaries still accurately describe the enriched skills, leave them and the registries unchanged and record that no registry edit was needed (the v3.8.0 / v3.9.0 precedent: doctrine refinements within existing scope do not require a registry edit). (2) Run `make validate` (or the fallback validators) after any registry edit and confirm green. (3) Do a full read-through across all edited skills for cross-file consistency: the finding taxonomy (1.1), the escalation rule (1.3), the round-history hygiene (1.4), the canonical gate (2.1), the stop-at-boundary doctrine (2.2 / 2.3), and the PR-body-from-trail pattern (3.1) all reference the same notion of an intent-touching finding and do not contradict each other or the existing review, shipping, commit, or loop material. (4) Grep the full diff across all three phases for "no-mistakes", "kunchenguid", "axi", "TOON", "auto-fix", "ask-user", "no-op", "checks-passed", "passed" (as an outcome token), "NO_MISTAKES_TELEMETRY", "a.kunchenguid.com", "--intent", and the literal product step-sequence string, and expect zero matches in any distributed artifact. (5) Add a `## [Unreleased]` entry to `CHANGELOG.md` describing the pre-merge-verification and finding-escalation doctrine enrichment, the optional PR-body-from-trail pattern, the N7 decision, and the recorded runtime and telemetry declines; note the catalog counts are unchanged (no new skill/command/hook). (6) Update `docs/v3/v3.9/known-gaps.md` with any deferred items (including N7 if deferred). Fix any failure and re-run until green. Then run `/session history` to document Phase 3.

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none - no constitution file; all recommended items are skill-native over owned skills with no policy violations; the two declines are dropped because they would violate governance, not adopted) | | |

---

### Phase 1 Exit Checklist

- [x] All sub-tasks completed (1.1, 1.2, 1.3, 1.4)
- [x] Three-way finding-action taxonomy present in `intent-based-review` with all three buckets and the mechanical-vs-escalate boundary rule
- [x] Intent-as-verbatim-review-oracle guidance present in `intent-based-review`, including the thin-intent failure mode and the live-conversation-over-transcript preference
- [x] Verbatim human-escalation rule present in `receiving-code-review`, with the no-self-resolution rule, the relay-verbatim discipline, and the standing-consent exception
- [x] Round-history hygiene rule present in `multi-agent-code-review`, distinguishing unchanged from materially-changed findings
- [x] No upstream product name or literal schema token in any distributed artifact (grep clean)
- [x] Every edited body under 500 lines; frontmatter unchanged in this phase
- [x] Validators green (JSON integrity; orphan-bundle audit; wikilinks resolve)
- [x] Session history generated for Phase 1
- [x] Ready to advance to Phase 2

### Phase 2 Exit Checklist

- [x] All sub-tasks completed (2.1, 2.2, 2.3)
- [x] Canonical pre-merge gate present in `shipping-and-launch`: ordered sequence, per-step rationale, "stable meaning" payoff, per-step cross-links, per-run-skip exception
- [x] Stop-at-the-human-decision-boundary doctrine present in `shipping-and-launch`, with the no-busy-poll rule and its failure mode
- [x] Loop-side no-busy-poll note present in `loop-engineering`, tied to the exit-signal / stall material
- [x] Canonical gate cross-links (not redefines) the existing per-step skills; no contradiction with `pre-commit-checklist`, `code-commit-workflow`, or `verification-before-completion`
- [x] No upstream product name or literal token in any distributed artifact (grep clean)
- [x] Every edited body under 500 lines; any new reference file linked from SKILL.md
- [x] Validators green
- [x] Session history generated for Phase 2
- [x] Ready to advance to Phase 3

### Phase 3 Exit Checklist

- [x] All sub-tasks completed (3.1, 3.2, 3.3, 3.4)
- [x] Optional deterministic-PR-body-from-audit-trail pattern present in `pr-description-writer`, framed as optional and additive
- [x] N7 decision made and recorded (deferred to known-gaps with a reason -- DF-v39-nomistakes-1); consistent with the N3 guidance (verbatim live intent preferred, already delivered in Phase 1)
- [x] RE matrix records the host-side runtime as `drop-outright` (with v3.1.0 / v3.8.0 precedent) and the default-on telemetry as a cautionary not-recommended item (MCP Registry Policy named), both referencing the comparison report
- [x] Registry-edit decision made and validated (no edit needed; recorded in known-gaps Notes -- all six enriched skills' summaries still accurate within existing scope)
- [x] Full cross-file consistency read-through passed; nothing implies a shipped runtime, a new dependency, or any telemetry
- [x] No upstream product name or literal token in any distributed artifact (grep clean across the full diff)
- [x] Validators green; all edited bodies under 500 lines (pr-description-writer 272, session-query 149 unchanged)
- [x] CHANGELOG `## [Unreleased]` entry added; `docs/v3/v3.9/known-gaps.md` updated
- [ ] Session history generated for Phase 3

---

## Definition of Done

- All three phases complete with their Exit Checklists satisfied.
- The P0 headline (N1: the finding-action taxonomy plus the verbatim human-escalation rule) and the P1 item (N2: the canonical pre-merge gate) are both delivered.
- The two P2 items (N3 intent-as-verbatim-oracle, N4 round-history hygiene) and the P3 items (N5 deterministic PR body, N6 stop-at-boundary) are delivered.
- N7 (the optional `re-partial` diff-to-session matching) has an explicit, recorded decision (built with an RE-matrix row, or deferred to known-gaps with a reason).
- The host-side runtime decline and the default-on-telemetry cautionary are recorded in the RE matrix, referencing the comparison report.
- Every recommended change is local Markdown over owned skills; no new skill, command, hook, outbound call, dependency, or credential was introduced.
- No upstream attribution appears in any distributed artifact; all content is ASCII-only and conformant to the Markdown style guide; the full validator chain is green.
