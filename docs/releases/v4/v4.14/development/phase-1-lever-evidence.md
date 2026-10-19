# Claude Subagent Lever Evidence

**Scope**: v4.14.0 Phase 1, T001. **Fetched**: 2026-10-16. Only the two Claude pages below were reverified; other platforms retain their existing evidence dates.

## Sources

- [Subagents](https://code.claude.com/docs/en/sub-agents#choose-a-model): canonical URL reached directly; model selection, inheritance, built-in agents, force mode, and API errors.
- [Model configuration](https://code.claude.com/docs/en/model-config#environment-variables): canonical URL reached directly; accepted values and configured fallback chains.

## Resolution

The [subagent reference](https://code.claude.com/docs/en/sub-agents#choose-a-model) documents these facts:

| Concern | Fetched evidence |
|---|---|
| Order | "per-invocation `model` parameter", definition `model`, `CLAUDE_CODE_SUBAGENT_MODEL`, then the session model |
| Inheritance | Environment value `inherit` is the "same as leaving it unset"; frontmatter `model: inherit` instead selects the session model at definition priority |
| Built-ins | The "built-in Explore and Plan subagents" ignore this default alone |
| Force | `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` overrides definitions; Nexus-Hub deliberately will not seed it |

The [environment-variable table](https://code.claude.com/docs/en/model-config#environment-variables) states: "Accepts an alias such as `haiku` or a full model name".

## Unreachable Models

The [subagent API-error section](https://code.claude.com/docs/en/sub-agents#api-errors-in-subagents) covers "such as its model being unavailable" through configured, applicable fallback chains. Exhausted API failures are reported; silent session-model inheritance is not documented.

The [fallback-chain reference](https://code.claude.com/docs/en/model-config#fallback-model-chains) applies configured chains to subagents. Covered availability failures try configured alternatives; authentication, billing, rate-limit, request-size, transport, and organization-policy failures do not trigger that switch. This phase does not configure a chain or assert model availability for a user's account.

## Disposition

T001 evidence is recorded. Phase 2 agent pinning remains a prerequisite for Phase 3 default delivery.

## Validation

- Baseline: `python -m pytest tests/validators/test_platform_defaults_levers.py -q` passed 23 tests.
- RED: the same command, after adding the key-level validator but before the policy key, returned exit 1: 24 passed and the proposed-default case failed for missing exact key-level evidence.
- GREEN: the focused validator passed 25 tests, exit 0.
- Post-phase pass: the validator and model-routing helper suites passed 45 tests, exit 0.
- Fast gate: 17 passed, 0 failed, 0 skipped, 0 advisory.
- Lint: `python -m ruff check --extend-select E402 tests/validators/test_platform_defaults_levers.py` passed.
