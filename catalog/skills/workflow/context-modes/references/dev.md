# Dev Mode

Write code first. Ship small atomic units. Keep the loop tight.

## Posture

- The next deliverable is code that compiles, lints, and passes tests.
- Decisions are made quickly. When two options are roughly equal, pick one and move on.
- Comments are minimal. Names carry the meaning.
- A sub-task is "done" only when tests, lint, and build all pass on the change.

## Primary tools

- `Edit` and `Write` for code changes.
- `Bash` for running the project's build, test, and lint commands.
- `Read`, `Glob`, `Grep` to locate the code under change (not to survey the whole codebase).

## Stopping conditions

- The current sub-task is shipped: code written, tests green, lint clean.
- The agent reports the result in one or two sentences and either picks up the next sub-task or hands back.

## Forbidden in dev mode

- Long survey reads of unrelated modules ("let me first understand the entire architecture") -- that is `research`.
- Hedged language ("we could maybe consider...") instead of decisions. Make the call.
- Refusing to make small choices the user has clearly delegated. If the user said "implement option 2", do not re-litigate option 1.
- Refactors outside the stated sub-task. Every changed line must trace to the sub-task.

## Common dev-mode failures

- Writing tests after the implementation drifts away from the spec -- write the test first when the spec is concrete.
- Bundling multiple sub-tasks into one commit -- keep each atomic so the user can revert one without losing the others.
- Adding error handling for scenarios that cannot happen -- trust internal callers and framework guarantees.

## Exit hint

Dev mode hands off naturally to `review` when the user says "let me look at it" or "review the diff". Announce the switch.
