# Session History - v3.9.0 adoption-no-mistakes Phase 1: Review and escalation doctrine

**Date**: 2026-06-25
**Plan**: [`../../plans/adoption-no-mistakes.md`](../../plans/adoption-no-mistakes.md) Phase 1 (N1 finding-action taxonomy + receiver-half escalation rule, N3 intent oracle, N4 round-history hygiene; skill-native)
**Branch**: `develop`
**Outcome**: Complete. All Phase 1 exit-checklist items satisfied; quality gate GO. Phase 1 of 3; not the final phase, so no release-readiness run.

## Goal

Import the headline doctrine from the source tool's agent skill into Nexus-Hub's review skills, as local Markdown enrichment only (no new skill, command, hook, outbound call, dependency, or credential): a three-way classification of every review finding by the action it implies (N1, the P0 headline), the rule that an intent-challenging finding is relayed to the human verbatim and never resolved by the agent (N1, receiver half), intent captured as a verbatim, tradeoff-rich review oracle rather than a diff summary (N3), and round-history hygiene so an iterative review loop does not re-raise a finding the user already chose to ignore (N4).

## What shipped

- **`catalog/skills/code-review/intent-based-review/SKILL.md`** (body now 275 lines): two additive sections inserted after "What This Skill Does", before "Instructions".
  - **Capturing Intent as the Review Oracle (1.2, N3)**: teaches that the intent is what the user set out to accomplish in their own terms, not a description of the diff; lists the nuance to capture (the goal as an outcome, the decisions and tradeoffs made, the approaches deliberately ruled in or out, anything explicitly requested that would look surprising in the diff); states the thin-intent failure mode (false escalations) and the preference for live-conversation intent over after-the-fact transcript reconstruction. Cross-links `[[verification-before-completion]]`.
  - **Classifying Findings by Action (1.1, N1)**: the three-way taxonomy with all three buckets defined (Mechanical-fix, Escalate-to-human, Informational), the sharp mechanical-vs-escalate boundary rule (routine correctness/reliability/security fixes stay mechanical even when the smallest fix reintroduces a little deleted logic; the escalate bucket is reserved for findings that genuinely contest intent or product behavior), and the "tell a decision from a mistake" rationale (a reviewer that cannot either rubber-stamps real defects or flags the user's own choices). Cross-links `[[receiving-code-review]]`.
- **`catalog/skills/code-review/receiving-code-review/SKILL.md`** (body now 118 lines): one new section "Escalating Intent-Touching Findings to the Human" after "Implementation Ordering". The agent must not approve, fix, or skip an escalate-bucket finding on its own; it relays the finding verbatim (location and full description), does not pre-judge, then translates the user's decision into the action. Names the standing-consent exception (explicit consent to drive unattended permits auto-resolution) and ties the rule to the skill's existing anti-performative-agreement stance. Cross-links `[[intent-based-review]]` and `[[verification-before-completion]]`.
- **`catalog/skills/code-review/multi-agent-code-review/SKILL.md`** (body now 150 lines): one new section "Round-History Hygiene (Multi-Round Review)" after the optional Dynamic-Workflow section. Carry a sanitized history of earlier-pass findings and user-deferred ones; do not re-report a finding the user already ignored unless the code now presents a materially different issue at that location; states the re-surface-noise failure mode and distinguishes "the same finding" (do not re-raise) from "a materially changed issue at the same location" (do raise, say what changed). Cross-links `[[intent-based-review]]` and `[[loop-engineering]]`.

## Key decisions / troubleshooting

- **Section placement chosen for causal reading order.** In `intent-based-review` the two new sections were ordered oracle-then-taxonomy (1.2 before 1.1, the reverse of the sub-task numbering) because you capture intent first and then classify findings against it. They were placed before "Instructions" so the doctrine frames the methodology rather than trailing it.
- **Generic labels for the taxonomy.** Per the Reverse-Engineering Attribution Rule, the buckets use self-chosen generic words (Mechanical-fix / Escalate-to-human / Informational) instead of the source's schema tokens. The forbidden-token grep (`no-mistakes`, `kunchenguid`, `axi`, `TOON`, `auto-fix`, `ask-user`, `no-op`, `--intent`) returns zero matches in the diff.
- **Shared vocabulary verified across the three files.** The taxonomy in `intent-based-review` is the single definition; `receiving-code-review` ("the escalate bucket in [[intent-based-review]]") and `multi-agent-code-review` ("escalate-bucket history described in [[intent-based-review]]") both defer to it, so the escalate bucket, the relay-verbatim rule, and the do-not-re-raise rule all reference the same notion of an intent-touching finding.
- **Frontmatter deliberately untouched.** Per the plan, the registry/summary-edit decision is deferred to Phase 3 sub-task 3.4; Phase 1 changes only the bodies. The pre-existing `description`-length heuristic flags on these skills (318 / 599 / 865 chars) are therefore unchanged by this phase.

## Verification (quality gate: GO)

- `make` is not on PATH, so the gate ran via its documented Windows equivalents:
  - **Orphan-bundle audit** (`python scripts/validate_skills.py --bundles-only`, the canonical `make validate` gate): PASS, 0 errors, 257 skills scanned. No new bundle files were added.
  - **Unicode / ASCII safety** (`python scripts/validate_unicode_safety.py`): 0 errors; a Python scan of all added (`+`) diff lines found zero non-ASCII characters. The two em-dash warnings reported in `intent-based-review` are on pre-existing Common Rationalizations rows (lines 247, 251), not added content.
  - **Dangling-wikilink audit**: all four added cross-link targets resolve to real skills (`verification-before-completion` and `loop-engineering` under `catalog/skills/workflow/`; `intent-based-review` and `receiving-code-review` under `catalog/skills/code-review/`).
  - **Body size**: 275 / 118 / 150 lines, all under the 500-line norm.
  - **Attribution grep**: zero matches in the diff for the forbidden upstream names and schema tokens.
- The strict `validate_skills.py --path catalog/skills/code-review --verbose` run reports `description`-length errors across the whole category (including untouched sibling skills such as `code-quality`, `plan-review`, `security-review`), which are the project's intentionally long "pushy" descriptions; none were introduced by this phase, and the canonical `make validate` gate (`--bundles-only`) does not block on them.

## Files changed

- `catalog/skills/code-review/intent-based-review/SKILL.md`
- `catalog/skills/code-review/receiving-code-review/SKILL.md`
- `catalog/skills/code-review/multi-agent-code-review/SKILL.md`
- `docs/v3/v3.9/plans/adoption-no-mistakes.md` (Phase 1 exit checklist checked off)
- `docs/archive/v3/v3.9/development/history/2026-06-25_adoption-no-mistakes-phase-1-review-and-escalation-doctrine.md` (this file)

## Next

Phase 2: Pre-merge gate and stop-at-boundary doctrine. Add to `shipping-and-launch` a canonical pre-merge verification gate (a fixed, justified sequence of checks, N2) that cross-links the per-step skills established here, plus the stop-at-the-human-decision-boundary doctrine (N6); add the loop-side no-busy-poll note to `loop-engineering`. CHANGELOG `## [Unreleased]` and `docs/v3/v3.9/known-gaps.md` updates are consolidated in Phase 3 sub-task 3.4, per the plan's phasing.
