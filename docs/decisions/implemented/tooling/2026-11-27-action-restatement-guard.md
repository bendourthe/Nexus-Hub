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


## Addendum 2026-11-27: decision format, question box, and per-platform coverage

Status: implemented in v4.15.10 (branch `feat/decision-table-format`).

### Problem

The first version fixed where an action is restated, not how a decision reads. The maintainer received an `Action needed` message with a long bullet list, each option a dense paragraph with command names (`member-start`), internal terms (`MINOR COMPLETE`), version lists, and the recommendation on option B. The request: a compact table, option A always the recommendation, the issue and each option in plain words, and enforcement on every supported platform. A second request: a user who steps away must not lose the question, so a native multiple-choice box should stay open while work continues.

### Decision

- **Shape.** A decision is a bold title, a one- or two-sentence plain issue, a table `Option | What happens | Trade-off` with 2 to 4 rows, option A the recommendation labeled "(recommended)", no jargon in the issue or the cells, technical detail after the table, the reply instruction last.
- **Native box first.** Where the host exposes a native question or selection tool, every decision goes through it, with option A labeled "(Recommended)" and plain-word descriptions. The agent keeps background work (agents, CI watches) running and starts no further user-facing action until the answer arrives. The table is the fallback. An answer the user must type (for example an approval line that must be the whole message) still gets the box or table first, with the exact text to type stated in it.
- **Persistence.** A text-only host cannot keep a box open, so a still-unanswered decision is repeated in full under `## Action needed` in every later message.
- **Platform-agnostic wording.** The rule line is byte-identical in all 14 substantive templates and names no product. Tool names are not guessed: the session-handoff skill already says platform names do not establish API availability, so the agent inspects the tools it actually has.
- **Enforcement.** `_action_restatement.py` gains a decision check that runs on the text from the last `Action needed` heading to the next heading of the same or higher level, fenced code removed. It applies only when two or more lettered options (A to D, as list lines or table rows) appear. It blocks when any of these holds:
    1. The options are not table rows.
    2. Option A has no "recommended" marker, or another option has one.
    3. The text before the first option or table row (title plus issue) exceeds 60 words.
    4. A table line holds inline code or a hex string of 7 to 40 characters with a digit and a letter a to f (a commit-hash proxy).

  The block reason names each failed rule, shows the required shape in one compact paragraph and says to ask through the host's question tool when one exists. A numbered-steps section has no lettered options and is never a decision. Existing fail-open behavior, `stop_hook_active` and the opt-outs are unchanged.
- **Hosts.** The old host check silently disabled the guard on any payload with a foreign key. It now also accepts a Codex payload (`turn_id` plus `model`, the signature `usage-guard` uses), because Codex documents `last_assistant_message` on `Stop` and a matching block output ([Codex hooks](https://learn.chatgpt.com/docs/hooks), fetched 2026-11-27). Fixture-backed tests cover a blocked and an allowed Codex payload and an unchanged Cursor payload.

### Alternatives considered

- **Table rule in prose only, no hook change.** Rejected: the first rule shows prose without a check fails at the end of a long turn.
- **Require the native question box and drop the table.** Rejected: most hosts the catalog supports give the agent no verified question tool, and a typed approval flow needs visible text; the table is the fallback and the typed-answer companion.
- **Name each platform's question tool in its template.** Rejected: the lockstep five must stay byte-identical, and a wrong tool name is the fabrication class AGENTS.md forbids. Only Claude Code's `AskUserQuestion` is recorded from vendor documentation (`docs/policy/settings-control-contract.md`); `usage-guard` also recognizes `request_user_input` and `ask_question` answer shapes, which is capture-code evidence, not a vendor document.
- **A new hook for the decision check.** Rejected: one Stop guard, one wrapper pair and one helper already own "final message shape"; a second hook doubles the registrations and the parity tests.
- **Parse Cursor, Copilot, Gemini CLI, Qwen and Kimi transcripts to extend enforcement.** Rejected for now: their Stop payloads carry no final message, the vendors call the transcript format unstable, and no fixture exists. Guessing a format would fail open at best and block wrongly at worst.

### Coverage matrix

| Platform | Rule delivered (template) | Native question tool | Hook enforcement | Gap |
|---|---|---|---|---|
| Claude Code | `base-claude.md` | `AskUserQuestion` (vendor docs, `settings-control-contract.md`) | Yes: `catalog/hooks/settings.json` `Stop` | None |
| Codex | `base-codex.md` | None verified by vendor document; `usage-guard` recognizes `request_user_input` | Yes: derived from `settings.json` into `hooks.json` `Stop` by `_codex_native.py`; the user trusts the hook once through `/hooks` | A hook not yet trusted is skipped by Codex |
| Cursor | `base-cursor.md` | None verified; `usage-guard` recognizes `ask_question` | No: `cursor.py` curated `stop` list omits the guard; the `stop` payload has no message and its output is `followup_message` | Rule-only; needs a transcript fixture |
| GitHub Copilot | `base-codex.md` (the Copilot adapter renders it) | None verified | No: registered by derivation through `copilot-hook-compat.py` but inert (no message in the payload; VS Code calls the transcript format unstable) | Rule-only |
| Antigravity 1.0 / 2.0 / CLI | `base-google-shared.md`, included by `base-antigravity-10.md`, `base-antigravity-20.md` and `base-antigravity-cli.md` | None verified | No: `antigravity.py` registers only `implementation-state.sh` on `Stop`; the wrapper payload has no message | Rule-only |
| Gemini CLI | `base-google-shared.md`, included by `base-gemini-cli.md` | None verified | No: registered on `AfterAgent` by derivation, inert (payload keys differ, no fixture) | Rule-only |
| Qwen Code | `base-qwen.md` | None verified | No: registered on `Stop` by derivation, inert (foreign payload) | Rule-only |
| Kimi Code CLI | `base-kimi.md` | None verified | No: registered on `Stop` by derivation, inert (`session_title` payload) | Rule-only |
| OpenCode | `base-opencode.md` | None verified | No shell-hook surface | Rule-only |
| Windsurf / Devin Desktop | `base-windsurf.md` | None verified | No: curated hook list | Rule-only |
| Aider, Pi, OpenClaw | `base-aider.md`, `base-pi.md`, `base-openclaw.md` | None verified | No shell-hook surface | Rule-only |
| Any other host | `base-agents.md`, `generic-instructions.md` | None verified | No | Rule-only |

### Consequences

- Five lockstep template ceilings rose by 110 words each, with a justification entry in `docs/policy/doc-budgets.json`.
- Where no question tool is verified, the rule reads "when one exists" and the agent inspects its own tools, so a platform that gains a tool needs no template edit.
- Tests: `catalog/hooks/tests/test_action_restatement_guard.py` (decision cases over both wrappers, Codex and Cursor payloads) and `tests/validators/test_communication_contract_rule.py` (rule text on every template found in the directory, so a new template fails until it carries the rule).
