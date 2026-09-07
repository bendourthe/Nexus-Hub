---
name: multi-agent-code-review
description: Review a code change with a panel of specialized reviewer personas (correctness, security, performance, reliability, testing, maintainability, api-contract, adversarial, project-standards) dispatched in parallel, then merge their findings through a confidence-anchored dedup / cross-reviewer-promotion / gate pipeline. Make sure to use this skill whenever the user says "review my changes", "review this PR", "review the diff", "do a thorough code review", "multi-agent review", "persona review", "review before I merge", or wants more than a single-pass review of a branch, diff, or pull request. SKIP, do NOT use for, reviewing a plan or requirements doc before code (use plan-review), a whole-codebase audit (use review-codebase / run-deep-review), a security-only audit (use run-security-audit / run-penetration-test), or a one-line quick read of a single file.
summary_l0: "Review a diff with parallel reviewer personas and a confidence-gated findings pipeline"
overview_l1: "Runs a multi-agent code review over a diff, branch, or PR. It resolves the review scope, discovers the change's intent, then selects reviewer personas per-diff: four always-on lenses (correctness, maintainability, testing, project-standards) plus conditional lenses (security, performance, api-contract, reliability, adversarial, agent-native) chosen from the diff's content. The selected persona agents are dispatched in bounded parallel, each returning structured JSON findings. Findings are merged with the confidence-anchored-scoring discipline: fingerprint dedup, cross-reviewer agreement promotion, mode-aware demotion of weak advisory findings, and a deliberately-late confidence gate. Externalizing modes add an independent per-finding validation pass, and high-stakes reviewers inherit the session model while advisory reviewers run a cheaper tier. Four modes: interactive, autofix, report-only, headless. Everything is local: no new outbound call. Trigger phrases: review my changes, review this PR, thorough code review, multi-agent review, persona review."
---

# Multi-Agent Code Review

Review a code change the way a strong review board would: several focused reviewers, each looking through one lens, whose findings are then reconciled into one ranked list rather than a pile of overlapping comments. This is the persona-fanout pipeline. It coordinates the reviewer agents under `catalog/agents/` and applies the [confidence-anchored-scoring](../code-quality/references/confidence-anchored-scoring.md) discipline so the output is deduplicated, corroboration-weighted, and gated to what is worth a human's attention.

Everything is local. The pipeline orchestrates the agent's own model over the local diff and local agent definitions; it adds no outbound call and no new credential.

## When to Use This Skill

Use when:

- The user asks to "review my changes", "review this PR", "review the diff", or wants a "thorough" / "multi-agent" / "persona" review of a branch, diff, or PR.
- A change is about to merge and a single-pass review is not enough confidence.
- You want findings ranked by corroboration and evidence, not a flat list.

**When NOT to use:**

- Reviewing a plan, spec, or requirements document *before* code exists - use [[plan-review]] (persona lenses for docs) or [[cross-artifact-analyzer]] / `/spec analyze` (single-agent).
- A whole-codebase health review - use the `/review full` orchestrator.
- A security-only deep dive - use `/review security` (remediation loop) or `/review pentest` (parallel security hunters).
- A trivial one-file glance where fanning out N agents is wasteful - read it directly.
- An over-engineering delete-list - use [[over-engineering-review]] as an optional lens, not a mandatory extra report in this pipeline.

## Modes

Pick the mode from the user's request; default to **interactive**.

| Mode | Human present? | Validation pass | Autofix | Output |
|---|---|---|---|---|
| **interactive** | Yes | No (human triages) | Proposes, applies on approval | Findings in-chat, ranked |
| **autofix** | No (then review) | Yes | Applies `safe` class, proposes `assisted` | Diff of applied fixes + report |
| **report-only** | No | Yes | Never | A written report artifact |
| **headless** | No (CI) | Yes | Never | Machine-readable JSON + exit code |

Mode changes two behaviors downstream: whether [mode-aware demotion](../code-quality/references/confidence-anchored-scoring.md) applies (only in non-interactive modes), and whether the independent validation pass (Stage 6) runs (only in externalizing modes: autofix / report-only / headless).

## Instructions

Run the seven stages in order. Stages 2-4 are where the fanout happens; Stage 5 is where the scoring discipline reconciles it.

### Stage 1 - Determine scope

Resolve exactly what diff is under review. Detect the sub-mode from the request:

- **standalone**: uncommitted work - `git diff` (unstaged) plus `git diff --cached` (staged). If both are empty, ask whether to review a commit range.
- **branch**: the current feature branch vs its merge base - `git merge-base HEAD <default-branch>` then `git diff <base>...HEAD`.
- **PR**: a specified PR - resolve its base and head (via `gh pr diff` when the `gh` CLI is available, else the branch form).
- **base**: an explicit range the user gave (`git diff <ref-a>...<ref-b>`).

Record the resolved base ref; every persona agent receives it so they all review the same lines. If the diff exceeds ~800 changed lines, batch by module/feature area and run the pipeline per batch (note the batching in the report).

### Stage 2 - Intent discovery

Before selecting reviewers, establish what the change is *trying* to do, so reviewers judge against intent, not guesswork. Gather, cheaply: the branch name, the commit messages (`git log <base>...HEAD --oneline`), any linked plan / issue / PR description, and the high-level shape of the diff (`git diff --stat`). Write a 1-3 sentence intent statement. Pass it to every persona - it is what lets `project-standards` and `correctness` judge "does this do what it claims" rather than "is this generically fine".

### Stage 3 - Per-diff persona selection

Select reviewers from the diff's content, not a fixed list. See [references/persona-selection.md](references/persona-selection.md) for the full trigger table and the agent-name mapping. In short:

- **Always-on (every review)**: `correctness` (reuse the `code-reviewer` agent), `maintainability-reviewer`, `testing-reviewer`, `project-standards-reviewer`.
- **Conditional (select when the diff matches)**: `security-reviewer` (input handling, auth, crypto, secrets), `performance-reviewer` (loops over user-sized data, queries, hot paths), `api-contract-reviewer` (changes to a consumed interface/schema), `reliability-reviewer` (new external I/O, multi-step state changes), `adversarial-reviewer` (input parsing, trust boundaries), `agent-native-reviewer` (new user-facing capability - see [[tool-design]]).

Record which personas were selected and why; the report shows this so a human can see what was and was not examined.

### Stage 4 - Bounded parallel dispatch

Dispatch the selected persona agents over the same diff + intent statement. Each returns a JSON array of findings per [references/findings-schema.md](references/findings-schema.md).

- Run them concurrently, but respect the harness active-subagent limit. If the harness rejects a dispatch because the limit is reached, treat it as **backpressure**: queue the persona and dispatch it when a slot frees - do not drop it, and do not silently reduce the persona set.
- Each agent is read-only and returns findings only; no agent edits code in this stage.
- Collect all raw findings into one pool, tagged by persona. Do not gate or dedup yet.

### Stage 5 - Merge findings (the scoring pipeline)

Apply [confidence-anchored-scoring](../code-quality/references/confidence-anchored-scoring.md) in its fixed order - do not reorder:

1. **Fingerprint + dedup**: `normalize(file) + line_bucket(+/-3) + normalize(title)`. Collapse same-fingerprint findings into one.
2. **Cross-reviewer promotion**: when two+ personas independently land on one fingerprint, promote the merged confidence one anchor step (capped at 100). Record which personas agreed.
3. **Mode-aware demotion**: only in non-interactive modes, demote weak advisory (P2/P3 from testing/maintainability) findings one step.
4. **Late confidence gate**: suppress anything below anchor 75, except a P0 at anchor 50+ which always surfaces. Keep suppressed findings in a verbose/appendix tier - never delete them.

### Stage 6 - Independent validation pass (externalizing modes only)

In autofix / report-only / headless modes, every surviving finding with `requires_verification: true` (or `confidence < 100`) gets one independent check by a fresh reviewer that did not produce it, using [references/validator-template.md](references/validator-template.md). The validator tries to *refute* the finding; a refuted finding is moved to the suppressed tier with the refutation recorded. In interactive mode, skip this - the human is the validator.

### Stage 7 - Model tiering and emit

Assign reviewer model tiers to spend budget where stakes are highest:

- **High-stakes reviewers** (correctness, security, reliability, api-contract, adversarial) inherit the session model.
- **Advisory reviewers** (maintainability, testing, project-standards) may run a cheaper/mid tier.
- The Stage 6 validators run at the session model (refutation is high-stakes).

Then emit per the active mode (table above). The headline list is the gate survivors, ranked by severity then confidence; the appendix holds the suppressed tier. In autofix mode, route `autofix_class: safe` findings to the `refactor-cleaner` agent to apply, propose `assisted`, and never auto-apply `manual`.

These two conventions are additive and do not change the confidence-gating pipeline above.

**Depth modes and finding cap.** When the user asks for a quick look, a skim, or a compact pass, treat that as **quick** depth: cover the primary changed path only, report P0/P1 survivors only, and stop at 5 headline findings. The default thorough review is **full** depth: cover the whole resolved scope, report every confidence-gate survivor, and stop at 20 headline findings. Overflow goes to the appendix, ranked, never deleted. Never pad to reach the cap. A short review or a clean result (zero findings plus a non-empty Considered-but-Rejected table) is a valid outcome. The cap exists so a low-signal review cannot bury the finding that mattered under cosmetic padding.

**Considered but Rejected.** Every emitted review MUST include a table of candidates that were inspected and deliberately not reported. Each row names the candidate, the location, and the reason, using one of: the owning rule permits the current implementation; evidence was insufficient; the project convention is intentional; the change would add complexity without user benefit. Rows MUST be real candidates encountered during this review, never invented filler. A genuinely thin scope reports the few that exist and says so. Without this table, a thorough review that found little is indistinguishable from a shallow one.

### Running the fanout as a Dynamic Workflow (optional)

Stages 3-6 are the canonical *dimensions -> find -> adversarially-verify* fanout: personas are the dimensions, Stage 4 is the find, Stage 6 is the refutation. When the harness has the Dynamic Workflows runtime, [scripts/review-fanout-workflow.js](scripts/review-fanout-workflow.js) is a ready-to-adapt scaffold that runs that shape deterministically (parallel persona review, a barrier merge that does the cross-reviewer promotion, per-finding refutation, then the late confidence gate). It binds to the skill's own contracts -- `FINDINGS_SCHEMA` mirrors [findings-schema](references/findings-schema.md) and `VERDICT_SCHEMA` mirrors [validator-template](references/validator-template.md).

It is a **template to adapt, not a script to run verbatim**, and it must **degrade gracefully**: Dynamic Workflows is a plan-gated research-preview capability that may be absent, so fall back to dispatching the personas as isolated subagents (Stage 4 by hand), or a single sequential reviewer. Because a persona fanout plus per-finding verification carries a 5-15x token multiplier, keep the **scope-first** discipline: calibrate on one module first, review the resolved persona set and diff base on the first trigger, and confirm before reviewing the whole change. For whether a fanout is warranted at all and the hard budget controls, see [[agent-orchestration-primitives]] and [[ai-billing-safeguards]] -- this template does not duplicate that guidance.

## Persona-Owned Docs

Each reviewer persona OWNS a doc area and keeps it current as a side effect of reviewing: it reads its own checklist/conventions doc as the standard to judge the diff against, and when a review exposes that the doc is stale or missing a rule the review relied on, it updates that doc in the same pass. Suggested ownership:

- maintainability -> the naming / structure conventions doc
- security -> the security-review checklist (OWASP + supply-chain notes)
- performance -> the performance-budget / hot-path notes
- reliability -> the error-handling and retry/timeout conventions
- testing -> the test-strategy and coverage-expectations doc
- api-contract -> the API versioning / compatibility rules
- project-standards -> AGENTS.md / CLAUDE.md and the project constitution

This binds review to living documentation: the standard a persona enforces and the doc it maintains are the same artifact, so the conventions never drift from what review actually checks. Keep it lightweight - a persona updates its doc only when a review exposes a gap, not as a mandatory per-review edit.

## Round-History Hygiene (Multi-Round Review)

When a review runs more than once over the same change (a re-review after a fix pass, or a later follow-up), carry a sanitized history of which findings were surfaced in earlier passes and which ones the user chose to leave unaddressed. On a follow-up pass, do NOT re-report a finding the user already ignored, unless the code now presents a materially different issue at that location.

This prevents a specific failure mode: without round-history hygiene, an iterative review loop re-surfaces the same rejected finding on every pass. That trains the user to tune out the reviewer entirely, and it buries genuinely new findings under the repeated noise. A finding the user explicitly deferred is a decision (it belongs in the escalate-bucket history described in [[intent-based-review]]), so re-raising it unchanged is just performative re-review.

Keep one distinction precise:

- **The same finding** at a location the user already passed on: do not re-raise it.
- **A materially changed issue** at that location: do raise it, and say what changed since the user last saw it. If the surrounding code was rewritten in a way that revives or worsens the concern, that is a new finding, not a repeat.

See [[loop-engineering]] for the broader loop-control discipline this round-history rule is an instance of.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "One reviewer agent is enough; fanning out is overkill" | A single generalist pass blends lenses and misses what a focused reviewer catches - the testing lens finds the untested branch the correctness lens skimmed past. The fanout exists because one prompt cannot hold every lens at full attention. |
| "Skip the dedup, just show every finding" | Without dedup the human sees the same issue three times and the cross-reviewer promotion signal is lost - you can no longer tell a corroborated finding from a lone hunch. Dedup before gating is what makes the ranking mean something. |
| "Gate the findings as each agent returns them" | Gating early throws away a 50-confidence finding that a second reviewer's agreement would have promoted to 75. The gate runs LAST, after promotion, on purpose. |
| "Run the validation pass in interactive mode too, to be safe" | In interactive mode the human IS the validator; an extra automated refutation pass burns tokens and slows the loop without adding signal. Validation is for unattended (externalizing) modes. |
| "Select every persona every time - more lenses, more coverage" | Irrelevant personas produce noise (a performance reviewer on a docs-only diff invents findings to look useful) and waste the subagent budget. Per-diff selection keeps signal high; record what was skipped so coverage is auditable. |
| "Demote advisory findings in interactive mode to keep it short" | Demotion is a triage tool for when no human is present. With a human in the loop, let them decide - demoting hides P2/P3 findings they might have wanted. |
| "Auto-apply the manual-class fixes, they look fine" | `manual` means the fix needs design judgement the pipeline does not have. Auto-applying it is how a review tool introduces the bug it was supposed to catch. Only `safe` is auto-applied. |
| "Skip Considered-but-Rejected; there is nothing interesting to list" | An empty rejected table is how a shallow review hides. If the pass was thin, say so with the few real candidates; inventing filler is the other failure. |
| "Pad to the cap so the review looks complete" | The cap is a ceiling, not a quota. Padding with cosmetic findings is the exact failure the cap exists to stop. |

## Verification

- [ ] The resolved diff base ref is recorded and every dispatched persona reviewed the same lines.
- [ ] An intent statement was written and passed to the personas.
- [ ] Persona selection is recorded with the trigger reason for each conditional persona (and which were skipped).
- [ ] Every dispatched persona returned findings in the [findings-schema](references/findings-schema.md) JSON shape (or an explicit empty array).
- [ ] The scoring pipeline ran in the fixed order: dedup -> promotion -> demotion -> gate (gate last).
- [ ] In autofix / report-only / headless modes, an independent validation pass ran for `requires_verification` findings; in interactive mode it was correctly skipped.
- [ ] Suppressed findings are retained in a verbose/appendix tier, not deleted.
- [ ] The emitted report includes a Considered-but-Rejected table of real inspected candidates (or an explicit "thin scope, N candidates" note), not invented filler.
- [ ] Depth mode is recorded (quick or full) and the headline list respects that mode's severity filter and finding cap; the list was not padded to reach the cap.
- [ ] No outbound network call or new credential was introduced.

## Related Skills

- [[code-quality]] - owns the [confidence-anchored-scoring](../code-quality/references/confidence-anchored-scoring.md) reference this pipeline depends on; the single-agent quality lens.
- [[security-review]] - the security lens as a standalone skill; this pipeline dispatches the `security-reviewer` agent as one conditional persona.
- [[plan-review]] - the same persona-fanout idea applied to a plan / requirements doc *before* code.
- `/review full` - whole-codebase deep review (8-phase); use that for breadth, this for a specific diff.
- `/review pentest` - parallel security hunters with the same confidence-gated synthesis; security-only.
- [[tool-design]] - defines the agent-native review lens the `agent-native-reviewer` persona applies.
- [[over-engineering-review]] - optional tagged delete-list for extra machinery; not an always-on persona in this pipeline.
