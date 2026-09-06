---
name: verification-before-completion
description: "Use before stating that any task is done, fixed, working, passing, or ready. Trigger phrases: it works, done, fixed, all tests pass, the build is green, ready to commit, ready for review, should work now, this is complete, that is resolved. Fires whenever you are about to make a completion or success claim, even an implicit one. SKIP only when reporting a verification you literally just ran in this turn and whose full output you are quoting, or when describing a plan you have not executed yet."
summary_l0: "Require fresh verification evidence before making any completion or success claim"
overview_l1: "This skill is an always-on discipline gate that fires immediately before any completion or success claim (it works, done, fixed, tests pass, build green, ready to ship). It forces a strict sequence: identify the one command that would prove the claim, run that command fresh in this turn, read its full output and exit code, confirm the output actually supports the claim, and only then state the result, quoting the evidence. It supplies a claim-to-evidence table mapping each common claim (tests pass, linter clean, build succeeds, bug fixed, requirements met) to the exact proving artifact, plus a rationalization table that rebuts the excuses agents use to skip verification (should work now, I only changed one line, I will run it after). Without this gate, agents report success from memory or inference and ship regressions. Use it as the final step of every task and after every code change."
---

# Verification Before Completion

State nothing as done until a command has proven it. A completion claim is a factual assertion about the current state of the code, and a factual assertion requires fresh evidence gathered in this turn. "It should work", "I fixed it", and "tests pass" are predictions until a command run moments ago says otherwise. This skill is the gate that converts a prediction into a verified statement before it reaches the user.

## When to Use This Skill

Use this skill before you write any sentence that asserts a task is finished or successful, including:

- "Done", "complete", "finished", "ready to commit", "ready for review", "ready to ship".
- "It works", "this works now", "should work", "that is resolved", "the bug is fixed".
- "All tests pass", "the suite is green", "coverage is met".
- "The build succeeds", "it compiles", "the linter is clean".
- "Requirements met", "matches the spec", "implements the acceptance criteria".

It applies even when the claim is implicit. Closing a task summary with "the feature is in place" is a completion claim and triggers the gate.

**When NOT to use:**

- When you are quoting the full output of a verification command you ran in this same turn. At that point the evidence is already on the screen and the gate is satisfied.
- When you are describing future or planned work you have explicitly not executed yet ("next I will add the migration"). A plan is not a completion claim.
- When the user asks a question that is not about task completion (explaining a concept, reading code, proposing an approach). Answering a question is not claiming a task is done.

If you are unsure whether a sentence is a completion claim, treat it as one and run the verification. The cost of an unnecessary command is seconds; the cost of a false "it works" is the user's trust.

## The Gate Function

Run this sequence before any completion claim. Do not reorder it and do not skip steps.

1. **Name the claim.** State to yourself the exact assertion you are about to make ("the test suite passes", "the build compiles", "the endpoint returns 200").
2. **Identify the proving command.** Determine the single command whose output would prove or disprove that claim. If no command can prove it, the claim is unverifiable and must be downgraded to "I believe" with the reason stated. (See the claim-to-evidence table below.)
3. **Run it fresh.** Execute the proving command now, in this turn. Do not reuse output from earlier in the session: the code changed since then, so old output proves nothing about the current state.
4. **Read the full output and the exit code.** Read to the end, not just the first lines. A suite that prints "PASS" for 40 tests and "FAIL" for the 41st has failed. A command that prints warnings and then exits non-zero has failed. The exit code is the authoritative signal; a zero exit with alarming output still warrants a second look.
5. **Confirm the output supports the claim.** Match the evidence to the assertion. "Tests pass" requires a line that says all tests passed and a zero exit, not merely the absence of a visible error.
6. **Only now, claim it, and quote the evidence.** State the result and include the proving artifact (the summary line, the exit code, the count). The user should be able to see why the claim is true without rerunning anything.

If step 5 fails, you do not have a completion. Return to the work, fix the cause, and re-enter the gate from step 1.

## Claim-to-Evidence Table

Every completion claim maps to a specific proving artifact. Never make the claim in the left column without the artifact in the right column gathered this turn.

| Claim | Proving command (example) | Evidence that satisfies the claim |
|---|---|---|
| Tests pass | the project's test command (e.g. `pytest -q`, `npm test`, `go test ./...`) | A summary line reporting 0 failures and 0 errors, plus a zero exit code. A skipped test is not a passing test; account for it. |
| Linter clean | the project's lint command (e.g. `ruff check .`, `eslint .`, `golangci-lint run`) | Zero reported violations and a zero exit code. Auto-fixed issues count only after a clean re-run. |
| Build succeeds | the project's build command (e.g. `npm run build`, `cargo build`, `make`) | Build completes with a zero exit code and produces the expected artifact. |
| Type check passes | the type checker (e.g. `mypy`, `tsc --noEmit`) | Zero type errors and a zero exit code. |
| Bug fixed | the failing reproduction (a regression test, or the exact steps that triggered the bug) | The reproduction now produces the correct result, AND a test that fails without the fix passes with it. A fix with no reproduction is unconfirmed. |
| Requirements met | the acceptance check named in the spec or plan (a test, a script, a manual procedure with observed output) | Each acceptance criterion has a corresponding observed pass. Map criteria to evidence one-to-one. |
| References repaired | `link-baseline.py diff --before <baseline> --after <current>` | Zero `newly_broken` and a zero exit code; a completed search-and-replace is not evidence that links resolve. |
| Behavioral output is correct | invoke `[[functional-verification]]`, the procedure owner for exercising a built artifact through its real boundary | A fresh evidence record from that procedure shows the current artifact produced the expected consumer-visible behavior. |
| Rendered output is correct | invoke `[[functional-verification]]`, the procedure owner for exercising rendered artifacts | A fresh evidence record from that procedure shows the current render produced the expected measured result. |
| Feature works end to end | running the actual flow (start the app, hit the endpoint, drive the UI) | Observed correct behavior in the running system, not just green unit tests. Unit tests prove units; they do not prove integration. |
| File / change is in place | reading the file back, or `git diff` / `git status` | The change is visible in the current file content, not just in your memory of having written it. |
| Loop exit condition met | the loop's `check_command` (e.g. `npm test`, `gh pr checks`, `make validate`) | The `check_command` exits 0 and its output satisfies the loop's `exit_condition`, confirmed by a checker that did not produce the iteration -- not the maker's sense that the loop has converged. |
| Review is clean / PR is mergeable | the authoritative current-head source: the status-check rollup plus the latest review submissions and unresolved threads (e.g. `gh pr checks`, `gh pr view --json statusCheckRollup,reviewDecision,reviews,mergeable`) | The current-head status rollup is all green, `reviewDecision` is APPROVED with no outstanding CHANGES_REQUESTED, there are zero unresolved review threads, and `mergeable` is true. A usage-limit, environment, or missing-review result is MISSING EVIDENCE, not approval. |

A loop's exit condition is itself a completion claim: "the loop is done" asserts something about the current state of the code, so it is bound by this same gate. The evidence is the `check_command` output gathered this turn, not the maker agent's reassurance that it converged. See [[loop-engineering]] for assembling the loop and [[agent-orchestration-primitives]] (Step 8) for why the checker that certifies the exit must not be the agent that produced the work.

If a claim has no proving command, say so explicitly: "I have not verified this; I believe X because Y" is honest and useful. "X works" without evidence is neither.

### PR / CI review state: verify against current-head evidence

A review-state claim ("the review is clean", "CI is green", "this is mergeable") is a completion claim about the PR's CURRENT head, so it demands current-head evidence, not history. The failure mode is asserting approval from a stale signal:

- A top-level "LGTM" comment from three commits ago describes code that no longer exists; a force-push or a new commit since then may have introduced the very problem the review would catch. Read the review submissions and status checks for the current head commit, not the conversation's oldest approving comment.
- A green checkmark you remember from an earlier run is stale the moment a new commit lands. Re-read `gh pr checks` (or the status rollup) for the head commit in this turn.
- An absence of a review is not an approval, and neither is an inconclusive one. A review that could not be produced because of a usage limit, a broken CI environment, or a reviewer who never responded is MISSING EVIDENCE. Report it as "not verified" with the reason; never round it up to "approved".

Verify the four current-head signals together: the status-check rollup is all green, `reviewDecision` is APPROVED (no outstanding CHANGES_REQUESTED), every review thread is resolved, and `mergeable` is true. Anything less is a blocker, not a pass. This is the same discipline the [[review-trapdoors]] pass applies to project-specific gotchas, and [[receiving-code-review]] governs acting on whatever the review returns.

## Smallest Sufficient Evidence Set

The claim-to-evidence table says what proves a claim. This section says which checks to run for the change actually in front of you. The two failure modes here are opposites, and both end in a false completion claim.

**Under-covering** is running a check that does not touch the diff. Green output from an irrelevant suite is not evidence; it is costume rigor with a passing exit code.

**Over-covering** is defaulting to the full suite for every change. This looks conservative and is not. It trains the habit of skipping verification whenever time is short, because the only option on offer is expensive. It also hides which check actually covers the change, so when something breaks later nobody knows which gate should have caught it. CI owns the exhaustive matrix; locally, select.

The rule: **run the narrowest set of checks that covers the outgoing diff.** Narrowest that COVERS, not narrowest available. When the only check covering your change is slow, the slow check is the narrowest sufficient set and you run it.

### Change surface to evidence

| Change surface | Sufficient evidence |
|---|---|
| Catalog skill edit (prose, frontmatter) | The catalog validator plus that skill's trigger evals. A description edit also needs the whole-catalog routing gate, since routing is comparative. |
| Registry or manifest edit | The specific validator for that registry, plus any consistency test that reads it. |
| Hook script edit | That hook's pytest module plus the sibling-parity test, in both implementations. |
| Validator or guard script | Its own test module, run in both directions: prove it passes clean input AND fails the defect it exists to catch. |
| Docs-only edit | Link and style checks, plus any validator that reads the doc as input rather than as prose. |
| Docs-tree move | Set equality of the pre-move inventory against destinations, plus a link-set diff proving zero `newly_broken`. |
| New file in a registered tree | Whatever test asserts registration completeness for that tree. This is the surface most often missed, because the file works fine and only its discoverability is broken. |
| A catalog-wide count or total changes | Every test that asserts that number, including ones in unrelated suites. A count is a global invariant, so a test about one item may still freeze it; grep the old value across the whole test tree rather than reasoning about which suite "should" own it. |
| Installer or packaging edit | The installer smoke tests on every platform the change touches. |

### Report only what ran

State the commands you actually executed and their actual results. Never write a summary that implies a check ran when it did not, and never aggregate an unrun check into a general "all tests pass". If you chose to skip something a reader might reasonably expect, say which and why. An accurate narrow report beats an impressive broad one, because the reader acts on it.

If a check fails to produce a summary line (truncated output, a killed process, a timeout), it produced no evidence. Re-run it rather than reasoning from the fragment.

See [[pre-commit-checklist]] for wiring the narrow set into an automated pre-commit gate, so the selection happens once rather than being re-derived under time pressure.

## Anti-Costume-Rigor Audit

A report can look rigorous while claiming work its evidence does not support. Search actively for the fraud classes below; this is an evidence audit, not a formatting check. For every applicable row, an auditor re-derives the stated comparison from artifacts, receipts, logs, exit codes, or set differences. A row whose tell depends on whether the claim "seems weak" is not mechanical and must be removed or rewritten.

| Fraud class | Mechanical tell an auditor re-derives |
|---|---|
| Fabricated evidence | Compare every claimed observation and evidence identifier with the referenced artifact or logged run; the claim fails when the artifact or run record does not exist or does not contain the observation. |
| Stale evidence | Compare the evidence receipt's commit, build, or artifact digest with the report's target identifier; any mismatch means the evidence was produced against a different target. |
| Overstated outcome | Compare the observed evidence class with the prerequisites of the claimed outcome; for example, a crash receipt without control, impact, or exploitability evidence cannot support a proven-exploitability claim. |
| Untested item listed as tested | Diff the tested-route identifiers against route-specific execution records; every tested entry must have a matching command or request, result, and exit or response receipt. |
| Rationale-free not-applicable | Compare every N/A entry with its recorded applicability rule and reason; an N/A row without both is unsupported. |
| Read-derived coverage | Diff components marked COVERED against the review-action ledger; each needs a component-scoped check and result, and a raw file-open or file-read receipt alone does not satisfy that record. |
| Wrong-instrument sweep | Compare the enumeration claim's required instrument class with the tool and mode in its receipt; a text-search receipt cannot support a semantic, dispatch, or call-graph completeness claim. |
| Completeness-unknown enumeration sold as complete | Compare the claimed denominator with affirmative pagination, limit, and truncation metadata proving the result set is complete; fail closed when completeness metadata is absent because absence of a truncation flag proves nothing. |
| Dropped pending work | Diff the candidate, UNCOVERED, and awaiting-validation sets against terminal dispositions and explicit report caveats; any unmatched item is pending work omitted from the completion claim. |
| Escalation avoidance | Compare each finding's observability boundary with its disposition and severity; a finding whose deciding layer is unobserved but is marked rejected or Low instead of `needs-live-validation` fails the comparison. |
| Repair claimed from substitution rather than resolution | Compare the repair report with the post-move resolution receipt; a replacement count with no `link-baseline.py diff` result cannot support a references-repaired claim. |

Record the result of each applicable comparison. A clean visual layout, detailed prose, or a long tool list is never a substitute for an empty mismatch set.

## Common Rationalizations

Each row is an excuse that precedes a false completion claim, with the concrete failure mode it causes.

| Rationalization | Reality |
|---|---|
| "It should work now." | "Should" is a prediction, not a result. The failure mode is shipping a change whose one edge case you did not anticipate. Run the proving command and turn "should" into "does" or "does not". |
| "I only changed one line, no need to re-run." | One line is exactly how a typo, an inverted condition, or a wrong variable ships. The whole point of a fast test command is that re-running it is cheap. Run it. |
| "The tests passed earlier." | They passed against earlier code. You changed the code since then, so that output describes a state that no longer exists. Stale evidence is not evidence. Re-run in this turn. |
| "I'll run the tests after I report." | Then you are reporting a result you do not have. If the post-report run fails, you have already told the user a falsehood. Run first, report second. |
| "It's obviously correct, verification is overkill." | "Obviously correct" is the precise category of change that fails silently, because obviousness suppresses scrutiny. Even a one-character fix gets the proving command. |
| "Running everything is safer than picking checks." | Full-suite-by-default is the habit that gets abandoned first when time is short, so it trains skipping verification entirely. It also hides which check covers the diff, so a later regression has no owning gate. Select the narrowest set that COVERS the change; if that set is slow, run it anyway. |
| "The error is unrelated to my change." | You do not know that until you have read the full output and traced the error. Many "unrelated" failures are the direct downstream effect of the change. Investigate before dismissing. |
| "Partial output looked fine." | A suite prints passes before it prints the failure. Reading the first screen and stopping is how a red suite gets reported as green. Read to the end and check the exit code. |
| "the screenshots looked fine" | Eyeballing is not evidence; it is the exact mechanism by which every defect in this project reached the maintainer. Invoke `[[functional-verification]]` and require its fresh rendered evidence before claiming the output is correct. |
| "Great, that's done!" / "Perfect!" | Expressions of satisfaction are completion claims in disguise and often arrive before any verification. Catch yourself: before the celebratory sentence, run the gate. |
| "The user is in a hurry, I'll skip the check." | A fast wrong answer costs more than a slightly slower correct one, because the user now has to discover the error and ask again. Speed that ships regressions is not speed. |

## Loop Anti-Patterns

When this gate runs inside an agentic loop (see [[loop-engineering]]), two failure modes attack the human rather than the code. Name them so you can catch them:

- **Cognitive surrender** -- the operator stops forming an independent opinion about loop output because the automation is comfortable and the green checks feel authoritative. The failure mode is a loop that ships work no human actually judged. Mitigation: verification stays a human responsibility. The checker that certifies a loop exit must not be the agent that produced the work (the independent-evaluator rule in [[agent-orchestration-primitives]], Step 8), and the human still reads the evidence at bounded checkpoints rather than trusting the checkmark.
- **Comprehension debt** -- the gap between what the loop has shipped and what the operator actually understands widens with every cycle, until no one can safely change or debug the system. The failure mode is accumulated code the team cannot reason about. Mitigation: close the gap deliberately with [[session-teach-back]], the Socratic mastery-confirmation loop that quizzes the operator on what was built and why until every concept is confirmed.

## Spirit Over Letter

The rule is "no completion claim without fresh proving evidence", not "run a command sometime". Running an unrelated command, running the right command against stale code, or running it and not reading the output all violate the spirit while technically touching a terminal. The gate is satisfied only when the evidence in front of you, gathered this turn, actually supports the specific claim you are about to make.

## Verification

- [ ] The exact completion claim was named before any command was run.
- [ ] The proving command for that claim was identified (or the claim was explicitly downgraded to "unverified" with a reason).
- [ ] The proving command was run fresh in this turn, not reused from earlier output.
- [ ] The chosen check set covers the outgoing diff (every changed surface maps to a check that reads it), and no check was included that does not touch the change.
- [ ] The full output was read to the end and the exit code was checked.
- [ ] The observed evidence matches the specific claim (passing summary line, zero exit, correct observed behavior).
- [ ] Every behavioral or rendered-output claim has fresh evidence produced through `[[functional-verification]]`, not an eyeballed screenshot.
- [ ] The completion statement quotes the proving artifact so the user can see why it is true.
- [ ] Every applicable anti-costume-rigor row was checked through its concrete artifact comparison, with no subjective tell accepted.
- [ ] No celebratory or satisfaction phrase ("done", "perfect", "great") was emitted before the gate completed.

## Related Skills

- [[pre-commit-checklist]] -- wires the smallest sufficient evidence set into an automated pre-commit gate, so the selection is made once rather than re-derived under time pressure.
- [[quality-gate-definitions]] -- defines the GO/NO-GO thresholds (tests, coverage, lint, build) that this gate proves at each checkpoint.
- [[functional-verification]] -- owns the procedures for exercising behavioral and rendered artifacts; this skill owns evidence freshness before a completion claim.
- [[adversarial-verifier]] -- goes beyond "does it pass" to stress-test the change against edge cases and attack inputs once the basic gate is green.
- [[receiving-code-review]] -- applies the same verify-before-claiming discipline when acting on review feedback (verify the suggestion against the codebase before agreeing it is correct).
- [[review-trapdoors]] -- the project-specific counterpart: before a review-ready claim, check the project's curated recurring-blocker list as part of the evidence.
- [[test-driven-development]] -- supplies the failing-then-passing reproduction that the "bug fixed" row of the claim-to-evidence table depends on.
- [[debug-with-logs]] -- when the proving command fails, this skill helps locate why before re-entering the gate.
- [[loop-engineering]] -- assembles goal-terminated loops whose exit condition is the evidence-bearing completion claim this gate enforces.
- [[agent-orchestration-primitives]] -- Step 8 supplies the independent-evaluator rule: the checker that certifies a loop exit must not be the agent that produced the work.
- [[session-teach-back]] -- the comprehension-debt countermeasure: a Socratic loop that confirms the operator understands what a loop shipped, not just that it passed.
- [[pentest-reporting]] -- applies this skill's anti-costume-rigor comparisons to security-report coverage, evidence, rejection, and disposition claims before delivery.
