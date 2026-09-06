---
description: Drive test coverage to a standardized threshold across test tiers - unit, integration, e2e, CI/CD - generating and running tests iteratively until the threshold and a 100% pass-rate are met. Use to "add tests", "increase coverage", "write unit tests", "generate integration tests", "do TDD", "test this code", "get to 80% coverage". SKIP - running an existing suite once with no generation (run the test command directly), or reviewing test quality without writing tests (use /review coverage).
---

# /test Command

Drive test coverage to a standardized threshold across test tiers. `/test` analyzes current coverage, then generates and runs tests iteratively until each tier reaches the threshold with a fully green pass-rate, then advances to the next tier. It merges three retained skills - `generate-unit-tests`, `generate-tests`, and `tdd` - behind one iterative coverage loop.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The command owns the per-tier loop and the gate; the test-generation logic lives in the retained skills.

## Standardized thresholds (overridable)

- **Coverage threshold**: 80% line coverage per the repo's global testing rules (default).
- **Pass-rate**: 100% of generated tests green before advancing to the next tier (default).
- Override via args: `/test unit --threshold 90` or `/test all --threshold 85 --pass-rate 100`. When a project config (`pyproject.toml`, `vitest.config`, CI gate) declares a stricter threshold, use the stricter value and say so.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `unit`, `integration`, `e2e`, `ci`, `tdd`, `all`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- Otherwise, present this menu and wait for a selection:

      What scope?
        1. all          (recommended) - unit, then integration, then e2e, then ci, each to threshold
        2. unit         - drive unit-test coverage to threshold
        3. integration  - drive integration-test coverage to threshold
        4. e2e          - drive end-to-end coverage to threshold
        5. ci           - verify the CI/CD test pipeline runs the suite and gates coverage
        6. tdd          - red-green-refactor cycle for a specific feature or bug

      Reply with a number or a scope name.

- `all` runs the tiers in order - `unit`, then `integration`, then `e2e`, then `ci` - applying the iterative coverage loop to each before advancing.
- Scope can be inferred: against an existing failing suite, start at `unit`.

## The iterative coverage loop (per tier)

For each tier the command drives, repeat until both gates pass, then advance:

1. **Analyze** current coverage for the tier and identify uncovered paths in the files in scope.
2. **Generate** tests for the uncovered paths via the tier's delegate skill (below).
3. **Run** the tier's test command and capture pass / fail / coverage.
4. **Check both gates**: coverage at or above the threshold AND a 100% pass-rate on generated tests. Fix failing tests (correct the test when the test is wrong; correct the code only when it is genuinely buggy and in scope) before re-checking.
5. **Repeat** from step 1 if either gate is unmet; **advance** to the next tier when both are met.

Report a per-tier summary (coverage before / after, tests added, pass / fail) as each tier completes.

## Delegation

Dispatch the resolved scope to the retained skill(s):

      unit         -> generate-unit-tests (then the per-tier loop above)
      integration  -> generate-tests (integration-level scenarios)
      e2e          -> generate-tests (end-to-end scenarios)
      ci           -> generate-tests (verify CI wiring) + the project's CI config
      tdd          -> tdd (red-green-refactor, 80% coverage gate)
      all          -> unit -> integration -> e2e -> ci, each via the loop

Generated tests must follow the repo's testing standards (AAA pattern, parametrized data-driven cases, fixtures in `conftest.py` / setup files rather than inline, no `sleep` or fixed delays). Pass any remaining arguments through unchanged.

## Optional fan-out

For very large surfaces ("generate tests for every unit"), offer the dynamic-workflow fan-out path with confirmation and the scope-first token caution: calibrate on a small slice before fanning out across the whole codebase. Fall back to single-agent execution when workflows are unavailable. See [[agent-orchestration-primitives]].

## Notes

- Scope boundary: when `/test` is explicitly invoked, its coverage threshold and pass-rate govern. On any other task the restraint rule owned by `minimal-construction` (step 6) governs: tests are committed only where the task asks or the repository already keeps them for that change class, and scratch checks are not promoted into the suite. Decision: `docs/releases/v4/v4.7/development/test-scope-decision.md`.
- This command replaces `/generate-tests`, `/generate-unit-tests`, and `/tdd` (removed in v3.2.0).
- Keep this dispatcher thin. The test-generation logic lives in the retained skills; this file owns only the tier sequence, the loop, and the gate.
