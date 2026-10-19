# Agent pinning rationale

All shipped agents perform reasoning-sensitive work. Claude receives the stable `opus` alias in each definition before Phase 3 delivers its cheaper unpinned-agent default. No dated model identifier is introduced. This is a classification decision, not a measured quality or savings claim.

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

## Platform compatibility

Reviewed `docs/policy/platform-read-contracts.json` and the actual delivery adapters on 2026-10-16. The contract names discovery paths; it does not establish universal rejection-free handling of `model:`. That Phase 2 assumption is false. Claude supports its model aliases; Codex's native TOML renderer already omits that catalog field. Other Markdown delivery paths must remove this Claude-specific field and preserve the prompt body and the user's native model selection. The existing metadata filter is sufficient; no new dependency, model mapping, credential, or workflow is needed.

- [Claude resolution](https://code.claude.com/docs/en/sub-agents#choose-a-model): definition pins precede the environment default.
- [OpenCode model configuration](https://opencode.ai/docs/agents/#model): requires a provider-qualified identifier.
- [Cursor model configuration](https://cursor.com/docs/subagents#model-configuration): supports inheritance or a specific platform model ID.
- [Antigravity custom agents](https://antigravity.google/docs/subagents): documents native model tiers.

Only discovery/delivery and metadata compatibility are qualified here; no authenticated model call or quality evaluation was run. Phase 3's installer smoke and the terminal parity gate remain required.
