# Loop Library

This library is a local, service-free registry of loop definitions. It has no install counts, no remote fetch, and no third-party processor; each entry is a declarative pattern an operator adapts to the current repository and host harness.

To add a loop, copy the fields from [loop-schema.md](loop-schema.md), keep the `check_command` project-specific, set `maturity: experimental` until repeated local use hardens it, and add a note when an existing Nexus-Hub command already owns the shape.

## ship-pr-until-green

```yaml
name: ship-pr-until-green
goal: The pull request has no failing required checks.
iteration_cap: 10
check_command: gh pr checks
exit_condition: check_command exits 0 and reports no failing required checks.
driver: /loop, with manual re-invocation fallback when the host lacks /loop.
maturity: experimental
agents:
  - Claude Code
  - Codex manual fallback
  - Cursor manual fallback
  - Gemini/Antigravity manual fallback
tags:
  - ci
  - pr
  - checks
```

Use this only when GitHub is already the repository's intrinsic PR destination. If the project uses another CI surface, replace `gh pr checks` with that project's own check command.

## build-until-green

```yaml
name: build-until-green
goal: The project build completes successfully.
iteration_cap: 10
check_command: <project build>
exit_condition: check_command exits 0.
driver: /goal for a hard completion requirement, or /loop for interval re-runs with manual fallback.
maturity: experimental
agents:
  - Claude Code
  - Codex manual fallback
  - Cursor manual fallback
  - OpenCode manual fallback
tags:
  - build
  - validation
  - stabilization
```

Replace `<project build>` with the repository's real build command, such as `npm run build`, `cargo build`, `dotnet build`, or `make`.

## e2e-until-green

```yaml
name: e2e-until-green
goal: The end-to-end suite exits successfully.
iteration_cap: 10
check_command: <project e2e>
exit_condition: check_command exits 0 with no failed end-to-end tests.
driver: /goal for a hard completion requirement, or /loop for interval re-runs with manual fallback.
maturity: experimental
agents:
  - Claude Code
  - Codex manual fallback
  - Cursor manual fallback
  - OpenCode manual fallback
tags:
  - e2e
  - tests
  - stabilization
```

Replace `<project e2e>` with the repository's real E2E command, such as `npm run test:e2e`, `npx playwright test`, or a Makefile target.

## coverage-until-threshold

```yaml
name: coverage-until-threshold
goal: Coverage reaches the project threshold and the test suite passes.
iteration_cap: 10
check_command: <project coverage command selected by catalog/commands/test.md>
exit_condition: check_command exits 0, tests pass, and coverage is greater than or equal to the configured threshold.
driver: Prefer /test through catalog/commands/test.md; use /goal only when the host is driving the same command manually.
maturity: hardened
agents:
  - Claude Code
  - Codex
  - Cursor
  - Gemini/Antigravity
  - OpenCode
tags:
  - coverage
  - tests
  - first-class-command
```

Pointer: prefer the `/test` command in `catalog/commands/test.md`, which already owns test selection, coverage checks, and stabilization behavior. Do not duplicate that command's policy in a custom loop unless the host lacks the command surface.

## pr-self-review

```yaml
name: pr-self-review
goal: The current change has no unresolved high-confidence review findings and required validation is green.
iteration_cap: 5
check_command: <project validation command plus review findings from catalog/commands/review.md>
exit_condition: validation exits 0 and /review changes reports no unresolved P1/P2 findings.
driver: Prefer /review changes through catalog/commands/review.md; use /goal only when manually driving the same review contract.
maturity: hardened
agents:
  - Claude Code
  - Codex
  - Cursor
  - Gemini/Antigravity
  - OpenCode
tags:
  - review
  - pr
  - multi-agent
  - first-class-command
```

Pointer: prefer `/review changes` in `catalog/commands/review.md` and [[multi-agent-code-review]] for the reviewer personas and confidence-gated findings pipeline. The loop definition only records the reusable shape.
