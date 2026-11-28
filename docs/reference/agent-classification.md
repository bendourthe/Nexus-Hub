# Agent Classification

This living reference records, for every agent in `catalog/agents/`, which model tier it is pinned to and why, and the effort declaration policy. Read it when adding or changing an agent, reviewing a model or effort pin, or editing the delivery adapters that withhold Claude-only keys. It covers the pinned and unpinned lists, the fast-tier agents, the effort policy, and platform compatibility. `tests/validators/test_agent_model_pinning.py` reads the membership tables below; the agent frontmatter is the only place a model or effort value lives.

Carried over from the archived v4.14 rationale (`docs/archives/v4/v4.14/development/agent-pinning-rationale.md`, left unchanged).

All shipped agents perform reasoning-sensitive work. Claude receives the stable `opus` alias in each definition. No dated model identifier is introduced. This is a classification decision, not a measured quality or savings claim.

## Pinned agents

| Agent | Reason |
|---|---|
| `adversarial-reviewer` | Find abuse paths and assumptions an attacker can violate. |
| `agent-native-reviewer` | Judge whether agents can discover and use new capabilities. |
| `api-contract-reviewer` | Reason about compatibility and serialized contracts. |
| `architect` | Choose system boundaries and architectural tradeoffs. |
| `build-error-resolver` | Find root causes across cascading build failures. |
| `code-reviewer` | Find correctness and design defects across a diff. |
| `coherence-reviewer` | Detect contradictions and missing requirements. |
| `design-lens-reviewer` | Evaluate architectural consequences before implementation. |
| `doc-updater` | Infer documented behavior from changing source code. |
| `feasibility-reviewer` | Evaluate hidden complexity and sequencing risks. |
| `harness-optimizer` | Diagnose flaky coverage and harness bottlenecks. |
| `loop-operator` | Choose safe fixes across autonomous verification cycles. |
| `maintainability-reviewer` | Judge abstraction, cohesion, and long-term change cost. |
| `performance-reviewer` | Infer scaling and resource consequences from code. |
| `planner` | Derive a complete dependency-aware implementation sequence. |
| `product-lens-reviewer` | Judge whether scope meets the actual user problem. |
| `project-standards-reviewer` | Apply project-specific rules to changed behavior. |
| `refactor-cleaner` | Preserve behavior across structural code changes. |
| `reliability-reviewer` | Find failure paths, partial updates, and cleanup defects. |
| `scope-guardian-reviewer` | Detect unbounded scope and missing cut lines. |
| `security-reviewer` | Find exploitable vulnerabilities and assess remediation. |
| `tdd-guide` | Select tests that expose incorrect behavior and enforce the cycle. |
| `testing-reviewer` | Judge whether tests detect regressions and missing branches. |

## Deliberately unpinned

None. No current role is tier-indifferent; ambiguous roles fail toward quality. Add a table row with the agent name in backticks and a concrete reason here only after establishing tier independence. The partition test rejects overlaps, stale entries, omissions, and non-alias pins; counts follow the live roster rather than a fixed total.

## Fast-tier agents

Add a table row with the agent name in backticks and a concrete reason only for an agent that reads and reports and never edits or runs anything; the pinning test accepts a fast-tier model only for an agent listed here.

| Agent | Reason |
|---|---|
| `log-reader` | Reads output it is handed and reports each failure; it has no edit or shell tool and never chooses a fix. Model `haiku`. Effort: none. Haiku 5.5 accepts effort, but a subagent on a model other than the main conversation's never inherits the session level ([model configuration](https://code.claude.com/docs/en/model-config), fetched 2026-11-21), so no session cost can spread to it and it runs at its model default. |

## Effort

Decision D1 of `docs/releases/v4/v4.15/plans/v4.15.9-adoption-agent-cost-and-delegation.md`: every opus-pinned agent declares `effort: high`. A subagent on the main conversation's model otherwise runs at the session's effort, so a session raised to `xhigh` or `max` would spread that cost to every helper. `high` is the level Nexus-Hub already seeds, so a user at the default sees no change. Status: applied 2026-11-21. Every opus-pinned agent declares `effort: high` directly after `model: opus`. A per-invocation effort outranks the field and `CLAUDE_CODE_EFFORT_LEVEL` outranks both ([sub-agents](https://code.claude.com/docs/en/sub-agents#choose-an-effort-level), fetched 2026-11-21), so a user who wants a helper at `max` asks for it per call. `CLAUDE_ONLY_AGENT_KEYS` in `scripts/lib/integrations/_catalog_adapters.py` (`model`, `effort`) is the one list every non-Claude delivery path strips. `tests/validators/test_agent_effort_ceiling.py` enforces the declaration.

## Platform compatibility

Reviewed `docs/policy/platform-read-contracts.json` and the actual delivery adapters on 2026-10-16. The contract names discovery paths; it does not establish universal rejection-free handling of `model:`. That Phase 2 assumption is false. Claude supports its model aliases; Codex's native TOML renderer already omits that catalog field. Other Markdown delivery paths must remove this Claude-specific field and preserve the prompt body and the user's native model selection. The existing metadata filter is sufficient; no new dependency, model mapping, credential, or workflow is needed.

- [Claude resolution](https://code.claude.com/docs/en/sub-agents#choose-a-model): definition pins precede the environment default.
- [OpenCode model configuration](https://opencode.ai/docs/agents/#model): requires a provider-qualified identifier.
- [Cursor model configuration](https://cursor.com/docs/subagents#model-configuration): supports inheritance or a specific platform model ID.
- [Antigravity custom agents](https://antigravity.google/docs/subagents): documents native model tiers.
- [Kimi custom agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html) (fetched 2026-11-21): documents `name`, `description`, `whenToUse`, `override`, `tools`, `disallowedTools`, and `subagents`; states that Claude Code's `model` is ignored and that unknown fields are ignored. Decision: Kimi strips `effort` (`KIMI_DROPPED_AGENT_KEYS` in `scripts/lib/integrations/_kimi_native.py`) because the page does not document it, and keeps the verbatim `model` line because the page documents ignoring it.

Only discovery/delivery and metadata compatibility are qualified here; no authenticated model call or quality evaluation was run. Phase 3's installer smoke and the terminal parity gate remain required.
