---
name: verification-before-completion
description: Use before stating that any task is done, fixed, working, passing, or ready. Trigger phrases: it works, done, fixed, all tests pass, the build is green, ready to commit, ready for review, should work now, this is complete, that is resolved. Fires whenever you are about to make a completion or success claim, even an implicit one. SKIP only when reporting a verification you literally just ran in this turn and whose full output you are quoting, or when describing a plan you have not executed yet.
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
| Feature works end to end | running the actual flow (start the app, hit the endpoint, drive the UI) | Observed correct behavior in the running system, not just green unit tests. Unit tests prove units; they do not prove integration. |
| File / change is in place | reading the file back, or `git diff` / `git status` | The change is visible in the current file content, not just in your memory of having written it. |
| Loop exit condition met | the loop's `check_command` (e.g. `npm test`, `gh pr checks`, `make validate`) | The `check_command` exits 0 and its output satisfies the loop's `exit_condition`, confirmed by a checker that did not produce the iteration -- not the maker's sense that the loop has converged. |

A loop's exit condition is itself a completion claim: "the loop is done" asserts something about the current state of the code, so it is bound by this same gate. The evidence is the `check_command` output gathered this turn, not the maker agent's reassurance that it converged. See [[loop-engineering]] for assembling the loop and [[agent-orchestration-primitives]] (Step 8) for why the checker that certifies the exit must not be the agent that produced the work.

If a claim has no proving command, say so explicitly: "I have not verified this; I believe X because Y" is honest and useful. "X works" without evidence is neither.

## Common Rationalizations

Each row is an excuse that precedes a false completion claim, with the concrete failure mode it causes.

| Rationalization | Reality |
|---|---|
| "It should work now." | "Should" is a prediction, not a result. The failure mode is shipping a change whose one edge case you did not anticipate. Run the proving command and turn "should" into "does" or "does not". |
| "I only changed one line, no need to re-run." | One line is exactly how a typo, an inverted condition, or a wrong variable ships. The whole point of a fast test command is that re-running it is cheap. Run it. |
| "The tests passed earlier." | They passed against earlier code. You changed the code since then, so that output describes a state that no longer exists. Stale evidence is not evidence. Re-run in this turn. |
| "I'll run the tests after I report." | Then you are reporting a result you do not have. If the post-report run fails, you have already told the user a falsehood. Run first, report second. |
| "It's obviously correct, verification is overkill." | "Obviously correct" is the precise category of change that fails silently, because obviousness suppresses scrutiny. Even a one-character fix gets the proving command. |
| "The error is unrelated to my change." | You do not know that until you have read the full output and traced the error. Many "unrelated" failures are the direct downstream effect of the change. Investigate before dismissing. |
| "Partial output looked fine." | A suite prints passes before it prints the failure. Reading the first screen and stopping is how a red suite gets reported as green. Read to the end and check the exit code. |
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
- [ ] The full output was read to the end and the exit code was checked.
- [ ] The observed evidence matches the specific claim (passing summary line, zero exit, correct observed behavior).
- [ ] The completion statement quotes the proving artifact so the user can see why it is true.
- [ ] No celebratory or satisfaction phrase ("done", "perfect", "great") was emitted before the gate completed.

## Related Skills

- [[quality-gate-definitions]] -- defines the GO/NO-GO thresholds (tests, coverage, lint, build) that this gate proves at each checkpoint.
- [[adversarial-verifier]] -- goes beyond "does it pass" to stress-test the change against edge cases and attack inputs once the basic gate is green.
- [[receiving-code-review]] -- applies the same verify-before-claiming discipline when acting on review feedback (verify the suggestion against the codebase before agreeing it is correct).
- [[test-driven-development]] -- supplies the failing-then-passing reproduction that the "bug fixed" row of the claim-to-evidence table depends on.
- [[debug-with-logs]] -- when the proving command fails, this skill helps locate why before re-entering the gate.
- [[loop-engineering]] -- assembles goal-terminated loops whose exit condition is the evidence-bearing completion claim this gate enforces.
- [[agent-orchestration-primitives]] -- Step 8 supplies the independent-evaluator rule: the checker that certifies a loop exit must not be the agent that produced the work.
- [[session-teach-back]] -- the comprehension-debt countermeasure: a Socratic loop that confirms the operator understands what a loop shipped, not just that it passed.
