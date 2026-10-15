---
name: lint-repair-loop
description: Run the project's linters, formatters, and type-checkers and REPAIR what they flag - not just report it - in a bounded loop that ends with a clean run and a reviewable diff. Make sure to use this skill whenever the user says "fix the lint errors", "clean up the linter output", "make lint pass", "repair the type errors", "auto-fix and fix the rest", "the linter is complaining", or wants flagged issues actually resolved rather than listed. Any judgment repairs beyond the formatters' native --fix are performed by the agent's OWN session model; this skill never shells out to an external repair model. SKIP, do NOT use for, designing or choosing the lint/type config itself, large behavioral refactors (use refactoring-expert), or reducing structural complexity / over-abstraction (use code-simplification).
summary_l0: "Run linters and repair what they flag in a bounded loop, not just report it"
overview_l1: "This skill runs the project's linters, formatters, and type-checkers and REPAIRS what they flag in a bounded loop, rather than only reporting problems. The loop is: run the tools; apply their native --fix / --write autofix first (deterministic and cheapest); re-run; for residual failures the autofixers cannot handle, the agent reads each failure and edits the code to satisfy it, using its OWN session model - never an external repair service; re-run until clean or a max-iteration cap is hit, then stop and surface what remains rather than looping forever. It always leaves a reviewable diff and never force-pushes or bypasses hooks. Per the MCP Registry Policy (hard-no on generation-as-service; reverse-engineer-first), the LLM-judgment half runs on the session model, and only the deterministic native-formatter pass may be automated by the opt-in lint-autofix precommit hook. Trigger phrases: fix the lint errors, make lint pass, repair type errors, auto-fix and fix the rest, clean up the linter output."
---

# Lint Repair Loop

Make the linter, formatter, and type-checker pass by actually fixing what they flag - not by printing the errors and stopping. This skill is a bounded repair loop: cheap deterministic autofix first, the agent's own judgment for the rest, a clean run at the end, and a diff you can review.

## When to Use This Skill

- The lint / type-check / format step is failing and you want it green with real fixes.
- Before a commit, to clean up what the formatters and the agent can safely repair.
- As the repair half of a precommit flow (the deterministic autofix half can run as the opt-in `lint-autofix` hook; this skill is the judgment half).

**Trigger phrases**: "fix the lint errors", "make lint pass", "repair the type errors", "auto-fix and fix the rest", "clean up the linter output", "the linter is complaining".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Choose or design the lint / type-check config | Configure the tool directly; this skill runs an existing config |
| Restructure behavior or extract abstractions | `refactoring-expert` |
| Reduce over-abstraction / dead code | `code-simplification` |
| Set up the precommit gate itself | `pre-commit-checklist` |

## Policy: repair on the session model, never an external vendor

The external-service pattern of "pipe lint failures to a cheaper third-party model to auto-repair" is NOT adopted here. Per the Nexus-Hub MCP Registry Policy (hard-no on generation-as-service; reverse-engineer-first), the judgment repairs run on the agent's OWN session model - the same model already in the loop - with zero new outbound call, dependency, or credential. The only automated piece is the deterministic native-formatter `--fix` pass, which is local tooling.

## Instructions

1. **Detect the tools.** Identify the project's linter / formatter / type-checker and the command that runs them (for example `ruff check . && ruff format --check .`, `eslint . && prettier --check .`, `gofmt -l . && go vet ./...`, `mypy`). Do not invent a config; use what the repo declares.
2. **Apply native autofix first.** Run the tools' own `--fix` / `--write` (`ruff check --fix` + `ruff format`, `eslint --fix` + `prettier --write`, `gofmt -w`). This is deterministic and the cheapest repair; do it before any judgment work.
3. **Re-run and read what remains.** Re-run the tools. For each residual failure, read the rule, the message, and the offending line.
4. **Repair with judgment (own model).** Edit the code to satisfy each residual failure - the narrowest change that fixes the rule without altering behavior. Never suppress a rule inline to silence it unless the suppression is itself the correct, documented decision.
5. **Loop with a cap.** Re-run; if failures dropped, continue; stop as soon as the run is clean. Cap the loop (default 3 judgment iterations). If failures remain at the cap, STOP and surface the remaining list rather than looping forever or making increasingly speculative edits.
6. **Leave a reviewable diff.** Do not amend history, force-push, or bypass hooks (`--no-verify`) to make a check pass. The output is a clean tool run plus a diff a human can review.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just add a `# noqa` / `eslint-disable` to make it pass." | Suppressing a rule is not repairing the defect; it hides it. Suppress only when the suppression is the correct, documented decision, not to turn the run green. |
| "The formatter's --fix left errors, so I'll report them and stop." | Reporting is the failure mode this skill exists to replace. The residual failures are exactly the ones that need the agent's judgment repair. |
| "Let me shell the errors out to a cheaper model to fix in bulk." | The MCP Registry Policy forbids a generation-as-service dependency. The session model does the repair; there is no second vendor. |
| "I'll `--no-verify` this commit and fix lint later." | Bypassing the hook defeats the gate and the debt rarely gets paid. Fix it now, in the loop, and leave a reviewable diff. |
| "It's a huge diff, so let me reformat the whole repo while I'm here." | Scope the loop to the files in play. A repo-wide reformat buries the real change and is a separate, deliberate decision. |

## Verification

- [ ] The lint / format / type-check command exits clean (0 errors) after the loop, or the remaining failures are surfaced with a reason and a stop.
- [ ] Native `--fix` / `--write` was run before any hand repair.
- [ ] No rule was suppressed solely to make the run pass (any suppression has a stated justification).
- [ ] A reviewable diff exists; no `--no-verify`, force-push, or history rewrite was used to pass a check.
- [ ] No external repair model / service was invoked; all judgment repairs ran on the session model.

## Related Skills

- [[pre-commit-checklist]] -- sets up the precommit gate this loop repairs against; the opt-in `lint-autofix` hook is its deterministic autofix half.
- [[code-simplification]] -- reduces structural complexity and over-abstraction (a deliberate change), distinct from making the linter pass.
- [[refactoring-expert]] -- behavior-preserving restructuring beyond what a linter flags.
- [[error-explanation-generator]] -- explains a cryptic lint / type error when the fix is not obvious.

---

**Version**: 1.0.0
**Last Updated**: July 2026
