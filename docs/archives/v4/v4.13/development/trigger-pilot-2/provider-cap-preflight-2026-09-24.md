# Trigger Pilot 2 Provider-Cap Preflight - 2026-09-24

This record tests whether the current Claude Code authentication can enforce the approved USD 35 aggregate limit for the v4.13 trigger pilot. It is for the maintainer before any new paid call; it does not qualify a candidate or change the aborted attempt.

## Observed Local State

- `claude --version` reported `2.1.280 (Claude Code)`.
- `claude auth status --json` reported `loggedIn: true`, `authMethod: claude.ai`, `apiProvider: firstParty`, and `subscriptionType: team`. Email, organization identifiers, and credentials were not retained in this record.
- `scripts/run_trigger_pilot.py` invokes non-interactive `claude -p` with `--max-budget-usd 0.50` per call and reserves USD 0.50 in its aggregate ledger. The aborted attempt reported USD 0.6540 and USD 0.6292 for its first two calls, so that reservation is not a proven hard bound.
- No browser session was available for a read-only account-setting check. No credential scope, account setting, or billing limit was changed, and no paid pilot call was made during this preflight.

## Provider Contract and Limit

[Anthropic's Team-plan guidance](https://support.claude.com/en/articles/11845131-use-claude-code-with-your-team-or-enterprise-plan) describes subscription access and optional usage credits. [Its usage-credit guidance](https://support.claude.com/en/articles/12005970-manage-usage-credits-for-team-and-seat-based-enterprise-plans) describes monthly organization and member limits on usage credits after included usage is exhausted. Those controls are not evidence of an isolated USD 35 limit on this pilot's reported `total_cost_usd`.

[Anthropic's Claude Console workspace documentation](https://platform.claude.com/docs/en/manage-claude/workspaces) describes separate API-key workspaces with monthly spend limits, while its [API error documentation](https://platform.claude.com/docs/en/api/errors) describes a limit-reached response. This is a candidate provider boundary only if the pilot uses a key bound to a dedicated, non-default workspace, its period-to-date spend and cap are read back, and no other workload can spend from it. The current `claude.ai` Team login does not establish those conditions. The [Enterprise Spend Limits API](https://platform.claude.com/docs/en/manage-claude/spend-limits-api) is Enterprise-only and is not evidence for this Team account.

[Anthropic's Agent SDK plan article](https://support.claude.com/en/articles/15036540-use-the-claude-agent-sdk-with-your-claude-plan) currently opens with a June 15 pause notice. Its preserved older text about moving `claude -p` off subscription usage must not be treated as a live billing rule.

## Decision Gate

The second pilot remains `UNMEASURED`. Before a rerun, obtain the maintainer's choice to use separately billed Console API traffic; verify the dedicated workspace's effective USD 35 monthly cap, period-to-date spend, key binding, and lack of competing usage; then demonstrate that the chosen provider boundary actually refuses further spend at the limit. If any of those facts cannot be proved, keep the runner stopped and the gap open. The existing in-flight receipts and observed-cost stop are useful partial-evidence controls, not substitutes for a hard provider ceiling.
