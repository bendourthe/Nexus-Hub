---
name: review-trapdoors
description: "Use before reviewing a change or before declaring your own change review-ready, to pre-empt the project's known recurring review blockers. Trigger phrases: review trapdoors, recurring review blockers, what usually gets flagged, what gets sent back in review, pre-empt review issues, PR readiness gotchas, is this review-ready, common review failures, project-specific review checks. Reads the project's curated trapdoors artifact and applies each entry as a gate, and appends a new trapdoor when a review surfaces a recurring class of blocker. SKIP for a one-off full review with no trapdoors artifact in play (use /review or the code-review producing skills), and for authoring durable project principles (use project-constitution)."
summary_l0: "Pre-empt a project's recurring review blockers from a curated trapdoors list before review"
overview_l1: "This skill applies a project's curated review-trapdoors artifact (a short, project-specific list of recurring review blockers, each phrased as a check) as a gate, both before reviewing someone else's change and before declaring your own change review-ready. It forces a sequence: locate the trapdoors artifact (a review-trapdoors.md or a Review Trapdoors section in AGENTS.md / CONTRIBUTING.md / the constitution), read every entry, and for each one whose trigger the diff matches, confirm the required evidence is present or flag it as a blocker. It also closes the loop: when a review surfaces a blocker that is a recurring class rather than a one-off, append a new one-line trapdoor so the next review catches it deterministically. It complements model-judgment review (which catches general issues but under-triggers on narrow project-specific gotchas) rather than replacing it, and it draws its new entries from continuous-learning instincts. Use it as a fast pre-review and pre-ready pass; do not use it as a substitute for a full review or for authoring governing principles."
---

# Review Trapdoors

A review trapdoor is a concrete, project-specific failure mode that keeps getting a change sent back in review. This skill applies the project's curated list of them as a gate, so the narrow gotchas that model judgment reliably misses (because nothing in the diff signals the missing step) are caught deterministically. It runs on both sides of a review: before you review someone else's change, and before you declare your own change review-ready.

The convention that defines the artifact (format, where it lives, how it is maintained) is documented in the [review-trapdoors style guide](../../../style-guides/review-trapdoors.md), installed at `~/.nexus-hub/style-guides/review-trapdoors.md`.

## When to Use This Skill

Use this skill when:

- You are about to review a change (a diff, a PR, a branch) in a project that maintains a review-trapdoors artifact.
- You are about to claim your own change is review-ready, done, or ready to open as a PR.
- A review just surfaced a blocker and you need to decide whether it is a recurring class worth recording as a new trapdoor.

**When NOT to use:**

- For a full, first-principles review of a change. This skill is a targeted pass over known recurring blockers, not a replacement for [[multi-agent-code-review]] or the `/review` producing skills. Run it alongside them, not instead of them.
- When the project has no trapdoors artifact and you are not creating one. There is nothing to apply; do a normal review. (You may still propose starting a trapdoors file if you notice a recurring blocker.)
- For authoring durable, governing project principles (MUST/SHOULD rules that shape all work). That is [[project-constitution]]. Trapdoors are narrower: operational, review-time gotchas.

## Instructions

### Step 1: Locate the trapdoors artifact

Look, in order, for:

1. A `review-trapdoors.md` at the repo root or under `docs/`.
2. A `## Review Trapdoors` (or "PR Readiness") section in `AGENTS.md`, `CONTRIBUTING.md`, or the project constitution.

If none exists, this skill has nothing to apply. Do a normal review; if a recurring blocker is evident, offer to start a trapdoors file per the style guide, then stop.

### Step 2: Read every entry

Read the whole list, not a sample. It is short by design (roughly 5-15 entries); reading all of it is the point. Each entry names a trigger (what kind of change it applies to) and the evidence it demands.

### Step 3: Match triggers against the change

For each trapdoor, decide whether the change under review matches its trigger. Ignore trapdoors whose trigger the diff does not touch (a "new outbound network call" trapdoor is irrelevant to a docs-only change). For every trapdoor that DOES match, move to Step 4.

### Step 4: Confirm the evidence, or flag a blocker

For each matched trapdoor, confirm the required evidence is actually present in the change:

- **Reviewing someone else's change:** verify against the real diff and codebase, not the PR description's claims. If the evidence is missing, record it as a review blocker with the trapdoor it violates and the specific missing artifact.
- **Declaring your own change ready:** if the evidence is missing, the change is not review-ready. Fix it (add the registry update, set the header, write the test) before you make the ready/done claim. This is the same discipline as [[verification-before-completion]], pointed at the project's known trapdoors.

A matched trapdoor with confirmed evidence passes silently. A matched trapdoor with missing evidence is a blocker, every time.

### Step 5: Append a new trapdoor on a recurring blocker

When a review (this one or a recent one) surfaces a blocker that is a recurring *class* rather than a one-off, add a one-line trapdoor for it, following the style guide's format ("X changes must prove Y"). Sources and rules:

- A single one-off does not earn an entry; a pattern does.
- [[continuous-learning]] instincts are the upstream feed: a minted instinct about a recurring review blocker is the signal to promote it into the trapdoors list.
- Prune an obsolete trapdoor in the same pass if its underlying cause is gone.
- If the list grows past ~15 entries, propose promoting the lowest-frequency ones into an automated check (a hook or CI gate is stronger than a read-me reminder).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I do thorough reviews; I do not need a checklist." | Thorough general review still under-triggers on project-specific gotchas, because nothing in the diff signals the missing lockstep file or the unset header. The trapdoors list exists precisely for the class of blocker that thoroughness alone keeps missing. |
| "The PR description says it handled the registry update." | The description is a claim, not evidence. The trapdoor is satisfied by the diff, not the summary. Verify against the actual change, or the "handled" that was forgotten ships anyway. |
| "This trapdoor probably does not apply here." | "Probably" is where matched triggers get skipped. If the change touches the trigger, confirm the evidence; do not wave it through on a hunch. |
| "This blocker is annoying but it is a one-off, not worth recording." | If it has recurred, it is not a one-off, and the next author will hit it too. A one-line trapdoor is cheap; a fourth re-review of the same mistake is not. |
| "The list is getting long, but every entry feels useful." | A list too long to read every review protects nothing. Long lists are a signal to promote the mechanical entries into hooks or CI gates and keep the human-read list short. |
| "I will add the trapdoor later." | Later is when the context is gone and the entry never gets written. Add the one line while the blocker is in front of you. |

## Verification

- [ ] The project's trapdoors artifact was located (or its absence was confirmed and a normal review was done instead).
- [ ] Every entry in the list was read, not a sample.
- [ ] Each trapdoor whose trigger the change matches was checked, and its required evidence was confirmed against the real diff/codebase.
- [ ] Every matched trapdoor with missing evidence was recorded as a blocker (when reviewing) or fixed before the ready claim (when authoring).
- [ ] Any recurring-class blocker surfaced this pass was added as a one-line trapdoor in the artifact's format; obsolete entries were pruned.
- [ ] This pass was run in addition to, not instead of, a normal review.

## Related Skills

- [[continuous-learning]] -- mints local instincts from observed mistakes; a recurring review-blocker instinct is the upstream signal for a new trapdoor.
- [[project-constitution]] -- holds durable MUST/SHOULD governing principles; trapdoors are the narrower, operational, review-time counterpart.
- [[multi-agent-code-review]] -- the full first-principles review this skill runs alongside; trapdoors cover the project-specific gotchas that a general review under-triggers on.
- [[receiving-code-review]] -- the receiving side; when a review flags a trapdoor violation, this governs acting on it without performative agreement.
- [[verification-before-completion]] -- the same verify-before-claiming discipline; declaring a change review-ready is a completion claim bound by that gate, with the trapdoors as the project-specific checks.
- [[quality-gate-definitions]] -- its merge-readiness contract treats "the project's review trapdoors were checked" as one condition of a mergeable change.
