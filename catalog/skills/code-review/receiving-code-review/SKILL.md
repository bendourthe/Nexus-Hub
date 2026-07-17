---
name: receiving-code-review
description: "Use when responding to code review feedback, a reviewer's comments, PR suggestions, or critique of code you wrote, and before you implement any requested change. Trigger phrases: the reviewer said, address this comment, they want me to change, PR feedback, review comments, you should refactor this, please fix, can you also handle, the review suggests. Especially when a suggestion is unclear, debatable, or expands scope. SKIP when you are the one authoring or producing a review of someone else's code (use the code-review producing skills instead), or when there is no review feedback to act on."
summary_l0: "Act on code review feedback with technical rigor and no performative agreement"
overview_l1: "This skill governs how to respond to code review feedback so that changes are correct, scoped, and free of reflexive agreement. It forces a per-comment pattern: read the comment in full, restate the requirement in your own words, verify the claim against the actual codebase before accepting it, evaluate whether the suggestion fits THIS codebase, then respond with either a technical acknowledgment or reasoned push-back, implementing one item at a time and testing each. It forbids performative responses (no You're absolutely right, no gratitude filler) in favor of stating the concrete fix. It adds a YAGNI check for implement-properly suggestions (grep for real usage first) and an ordering rule (clarify unclear items before touching code, then blocking, then simple, then complex). Use it whenever a reviewer, teammate, or automated reviewer leaves feedback on code you produced. Do NOT use it when you are the one writing the review."
---

# Receiving Code Review

Review feedback is input to evaluate, not orders to obey and not praise to absorb. A good response to a review is technical: you confirm the reviewer's claim against the real code, decide whether the suggestion improves THIS codebase, and then either implement it precisely or explain with evidence why you will not. Reflexive agreement ("You're absolutely right, fixing now") and reflexive defensiveness are both failures; the goal is a correct change and a clear reason.

## When to Use This Skill

Use this skill when:

- A human reviewer, teammate, or automated reviewer has left comments on code you wrote.
- You are about to implement a change a reviewer requested, especially before the first edit.
- A suggestion is unclear, debatable, or would expand the scope of the change.
- A reviewer asserts a fact about the code ("this leaks a connection", "this is O(n^2)") that you have not yet confirmed.

**When NOT to use:**

- When you are the one producing a review of someone else's code. That is the job of the review-producing skills (`code-quality`, `security-review`, `performance-review`, `testing-review`, and the rest of the `code-review/*` family). This skill is strictly about receiving.
- When there is no review feedback in play (a fresh implementation task with no comments to act on).

## The Response Pattern (per comment)

Process review comments one at a time. For each comment, run this sequence:

1. **Read it fully.** Read the entire comment, including any code suggestion and linked context, before reacting. Half-read comments produce half-right changes.
2. **Restate the requirement.** Put the reviewer's request in your own words: "You are asking me to move the validation into the constructor so an invalid object cannot be created." Restating surfaces misunderstandings before they become wrong edits.
3. **Verify the claim against the codebase.** If the comment asserts a fact ("this is never awaited", "this duplicates `parseConfig`"), confirm it by reading the actual code. Reviewers are sometimes wrong, working from an older version, or missing context. Do not implement a fix for a problem you have not confirmed exists.
4. **Evaluate for THIS codebase.** A correct-in-general suggestion can be wrong here. Check it against the project's conventions, existing patterns, and constraints. "Use a factory" is not an improvement if every sibling class is constructed directly.
5. **Respond technically.** Either:
   - **Acknowledge with the concrete fix:** state what you will change and why it is correct. "Moving validation into the constructor; this makes the invalid state unrepresentable."
   - **Push back with reasoning:** if the suggestion is wrong, out of scope, or worse for this codebase, say so with evidence. "Holding off on the factory: the other three loaders construct directly, so a factory here would be inconsistent. Open to it as a separate refactor if you want all four converted."
6. **Implement one item, then test it.** Make the single change, run the proving command for it (see `[[verification-before-completion]]`), and confirm it works before moving to the next comment. Do not batch ten changes and test once at the end.

## Forbidden Responses

These responses add no information and signal compliance instead of correctness. Do not use them.

- **Performative agreement.** "You're absolutely right!", "Great catch!", "Excellent point!" State the fix instead: "Yes - the lock is released before the await, so the guarantee is lost. Moving the await inside the locked section."
- **Gratitude filler as a substitute for a response.** "Thanks so much for the thorough review!" before doing the work is noise. If you must acknowledge, do it in one clause and then get to the technical content.
- **Blanket acceptance.** Agreeing to every comment without evaluating any of them. A review where you push back on nothing usually means you evaluated nothing.
- **Silent partial compliance.** Implementing the easy half of a comment and not mentioning the half you skipped. If you are deferring part of a request, say which part and why.

The test for a good response: remove every adjective and pleasantry. If a concrete technical statement (what changes, or why it should not) remains, the response is sound. If nothing remains, it was performative.

## YAGNI Check for "Do It Properly" Suggestions

Reviewers often suggest generalizing, abstracting, or "doing it properly" (add an interface, make it configurable, handle the other cases). Before implementing, check whether the generality is actually needed:

1. **Grep for real usage.** Search the codebase for actual call sites or requirements that need the generalization. If only one caller exists and no requirement names a second, the abstraction is speculative.
2. **Ask for the concrete driver.** If you cannot find the need, push back: "There is one caller and no requirement for a second; adding the interface now is speculative. I will keep it concrete and add the interface when the second consumer appears."
3. **Implement generality only against a real, present need.** "Might need it later" is a reason to leave a clear seam, not to build the abstraction today.

This is not an excuse to dodge real design feedback; it is a filter that distinguishes "this design is wrong" (implement the fix) from "this could be more general" (defer until needed).

## Implementation Ordering

When a review has multiple comments, do not implement in the order they appear. Order by dependency and risk:

1. **Clarify unclear items first.** Resolve every ambiguous comment with the reviewer before touching code. Implementing a guess and being wrong wastes the change and the re-review.
2. **Blocking / correctness items next.** Bugs, security issues, and broken behavior the reviewer flagged. These gate the merge.
3. **Simple items next.** Renames, small extractions, comment fixes. Cheap and low risk.
4. **Complex / structural items last.** Larger refactors, where a clean baseline (the simple items already done and tested) makes the bigger change safer.

Test after each item. A clean intermediate state means that if a later, riskier change breaks something, you know exactly which change did it.

## Escalating Intent-Touching Findings to the Human

Not every finding is yours to resolve. When acting on review feedback, a finding that challenges the user's deliberate intent or changes product behavior (the escalate bucket in [[intent-based-review]]) is a decision that belongs to the user, not the agent. Do NOT approve it, fix it, or skip it on your own judgment.

Instead, stop and bring it to the user before you respond:

- Relay the finding as written: its location and its full description, verbatim. Do not paraphrase it, and do not summarize away the detail that makes it a judgment call.
- Do not pre-judge the answer. Present the decision, not your preferred outcome dressed up as a recommendation.
- Then translate the user's decision into the action: fix it with their guidance, accept it as written, or skip it.

Contrast this with mechanical-fix findings (objective, low-risk defects), which you may resolve on your own without asking. The escalation rule applies only to findings that genuinely contest intent or product behavior.

There is one standing exception: when the user has given explicit standing consent to drive the work unattended, you may resolve escalate-bucket findings automatically under that mandate. Absent that consent, stop and ask.

This is the same discipline this skill already applies to performative agreement, pointed at intent-touching findings. Relaying a finding verbatim and refusing to silently resolve it is the no-performative-compliance rule again: you do not paper over a real decision with a quiet edit any more than you paper over a real disagreement with "You're absolutely right". See [[verification-before-completion]] for proving whatever fix the user does choose.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The reviewer is senior, they must be right." | Seniority raises the prior, it does not remove the need to verify. Senior reviewers work from stale checkouts and miss local context too. Confirm the claim against the code, then agree or push back with evidence. |
| "Agreeing fast keeps the review friendly." | Friendliness that ships a wrong change is not friendly; it costs a second review cycle. A precise technical response is more respectful of the reviewer's time than a cheerful "fixing now" that fixes the wrong thing. |
| "I'll just implement everything they asked." | Blanket implementation ships speculative abstractions and unconfirmed fixes. Evaluate each comment for THIS codebase; some suggestions are wrong here even when right in general. |
| "Pushing back will seem defensive." | Reasoned push-back with evidence is collaboration, not defense. "Here is why this is inconsistent with the other loaders" is a technical argument the reviewer can accept or counter. Silence is what hides disagreement. |
| "This 'do it properly' comment is obviously good practice." | Good practice against a real need is good; good practice against an imagined need is over-engineering. Grep for the second caller first. If it does not exist, defer the abstraction. |
| "I'll batch all the changes and test once at the end." | A batched failure hides which change caused it. One change, one test, one confirmed-good state. Then the next. |
| "The comment is unclear but I think I know what they mean." | "I think" before a code change is a guess. Ask the one clarifying question now; it is cheaper than implementing the wrong interpretation and re-reviewing. |

## Spirit Over Letter

The rule is "evaluate feedback technically and respond with substance", not "avoid the phrase you're absolutely right". Replacing one performative phrase with another, agreeing to everything while skipping the verification step, or pushing back without evidence all violate the spirit. The skill is satisfied only when each comment was checked against the real code, evaluated for this codebase, and answered with a concrete change or a reasoned, evidence-backed decision not to change.

## Verification

- [ ] Each review comment was read in full and restated in your own words before any edit.
- [ ] Every factual claim in the review was confirmed against the actual codebase before being acted on.
- [ ] Each suggestion was evaluated for THIS codebase's conventions and constraints, not accepted in the abstract.
- [ ] No performative agreement or gratitude filler appears in the responses; each response states a concrete fix or a reasoned push-back.
- [ ] "Do it properly" suggestions were YAGNI-checked (grep for real usage) before any abstraction was added.
- [ ] Unclear comments were clarified before code was changed; remaining items were implemented blocking-first, then simple, then complex.
- [ ] Each change was implemented and tested individually before the next was started.

## Related Skills

- [[code-quality]], [[security-review]], [[performance-review]], [[testing-review]], [[code-smell-detector]], [[final-report]] -- the review-producing side; this skill is their counterpart for the engineer receiving the review.
- [[verification-before-completion]] -- verify each implemented review item with a fresh proving command before claiming it is addressed.
- [[intent-based-review]] -- shares the principle of evaluating against acceptance criteria rather than line-by-line reflex.
- [[refactoring-expert]] -- when a review's structural suggestion is sound, this skill guides the behavior-preserving change.
