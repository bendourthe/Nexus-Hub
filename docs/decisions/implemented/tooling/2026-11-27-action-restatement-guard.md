# Decision: A message that waits on the user restates the steps under an Action needed heading, and a Stop hook enforces it

Status: implemented - the Communication Contract requires a `## Action needed` section on every platform, and the `action-restatement-guard` Stop hook blocks a final message that asks the user to act and points back to earlier text.
Date: 2026-11-27
Author: Ben Dourthe
Template: Nygard

## Problem

An agent ended a long session with "Waiting on you: the 3 migration-approval steps from earlier. Reply "done" when step 3 prints approved." The maintainer had to scroll through the session to find the steps. A softer rule already existed in the contract ("write each user action in full every time you ask for it, never "as above"") and did not prevent it: the rule had no marker the agent could check itself against, and nothing verified the final message.

## Decision

The rule has two parts.

- **Rule on every platform.** When anything waits on the user (a command, an approval, a decision, or information), the message carries a `## Action needed` heading and restates everything under it in full, even if the previous message had the same text. It never refers back with "from earlier", "above", "previous message", "as before", "the steps I listed", or "scroll up". One Communication Contract bullet carries it, byte-identical in all 14 substantive instruction templates; it absorbs the older "write each user action in full" clause. The worked example and a verification item live in `catalog/style-guides/agent-communication.md` section 3.2, the `agent-communication` skill and its `references/response-contract.md`. The session-start reminder repeats it.
- **Enforcement where the host supports hooks.** `action-restatement-guard` (`.sh` and `.ps1`, both thin wrappers over `catalog/hooks/_action_restatement.py`) runs on `Stop`. It reads the last assistant message and blocks when the text both asks the user to act and contains a back-reference. The block reason tells the agent to rewrite the message under `## Action needed`. It never blocks twice (`stop_hook_active`), fails open on every read or parse error, ignores non-Claude payloads, and honors `NEXUS_DISABLED_HOOKS=action-restatement-guard` and `NEXUS_HOOK_PROFILE=minimal`.

Precision choices:

- Fenced code and inline code are ignored, so a message that quotes a phrase does not trip the guard.
- With an `Action needed` heading present, only the text from the heading on is checked for back-references.
- A missing heading alone does not block. The ask signals ("reply", "choose", "approve") appear in many messages that need no restatement, so that check would block correct messages.

## Alternatives considered

- **Strengthen the wording only.** Rejected: the existing rule was already worded strongly and failed. A rule the agent grades itself against, at the end of a long turn, is the case that fails.
- **Block whenever the ask signals appear without the heading.** Rejected for precision: it would force a heading onto routine questions and approvals that need no restatement. Revisit if back-references keep slipping through in other wording.
- **Warn with `systemMessage` instead of blocking.** Rejected: the warning reaches the user after the unreadable message is already sent, so the user still scrolls.
- **Implement the detection natively in both `.sh` and `.ps1`.** Rejected: two copies of the phrase lists would drift. Both wrappers share one Python helper, as `stuck-turn-notice` and `worktree-policy` do; Python is already required by the Stop chain.
- **Rely on the platform's own instruction file only.** Rejected for hosts that run hooks; kept as the only mechanism for platforms without a hook surface, which receive the rule through the templates.

## Consequences

- The five lockstep template ceilings in `docs/policy/doc-budgets.json` rose by the measured 56 words, with a justification entry.
- The registered hook count rises from 40 to 41.
- The guard matches fixed English phrases, so a back-reference in other words passes. It checks the final message only.
- Tests: `catalog/hooks/tests/test_action_restatement_guard.py` (both wrappers) and `tests/validators/test_communication_contract_rule.py` (rule text on every template, byte-identical).
