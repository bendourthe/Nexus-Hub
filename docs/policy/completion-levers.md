# Completion levers by platform

Per-platform levers a full `/implement` run can use to keep working until the completion checker reports a terminal verdict: a native goal command, a turn-end continuation hook or plugin, a headless CLI with resume, and a prompt-submit event for capturing user approvals. The machine-readable source is [`completion-levers.json`](completion-levers.json); this page is its human companion. Read it before changing the completion gate adapters, the `run-plan` runner, or the `approval-capture` hook, and before claiming a platform "continues until done".

Every VERIFIED cell links the first-party vendor page fetched on 2026-09-25. "None documented" is a real result, not a placeholder: it means no first-party page states the lever. `tests/validators/test_completion_levers.py` fails when a registered integration has no row, when a VERIFIED lever lacks a source or date, or when a continuation format is not one the gate implements.

## Summary

| Row | Owner | Native goal | Continuation (format) | Headless | Prompt-submit |
|---|---|---|---|---|---|
| `aider` | `aider` | none documented | none documented | [VERIFIED](https://aider.chat/docs/config/options.html) | none documented |
| `antigravity` | `antigravity` | none documented | none documented | none documented | none documented |
| `antigravity2` | `antigravity2` | [VERIFIED](https://antigravity.google/docs/slash-commands/) | [VERIFIED](https://antigravity.google/docs/hooks/) `antigravity-continue` | none documented | none documented |
| `antigravity2/cli` | `antigravity2` | [VERIFIED](https://antigravity.google/docs/slash-commands/) | [VERIFIED](https://antigravity.google/docs/hooks/) `antigravity-continue` | [VERIFIED](https://antigravity.google/docs/cli/conversations/) | none documented |
| `claude` | `claude` | [VERIFIED](https://code.claude.com/docs/en/goal) | [VERIFIED](https://code.claude.com/docs/en/hooks-guide) `top-level-block` | [VERIFIED](https://code.claude.com/docs/en/headless) | [VERIFIED](https://code.claude.com/docs/en/hooks) `UserPromptSubmit` |
| `codex` | `codex` | [VERIFIED](https://learn.chatgpt.com/use-cases/follow-goals) | [VERIFIED](https://learn.chatgpt.com/docs/hooks) `top-level-block` | [VERIFIED](https://learn.chatgpt.com/docs/cli/reference) | [VERIFIED](https://learn.chatgpt.com/docs/hooks) `UserPromptSubmit` |
| `copilot` | `copilot` | [VERIFIED](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) | [VERIFIED](https://docs.github.com/en/copilot/reference/hooks-reference) `top-level-block` | [VERIFIED](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) | [VERIFIED](https://docs.github.com/en/copilot/reference/hooks-reference) `userPromptSubmitted` / `UserPromptSubmit` |
| `copilot/cli` | `copilot` | [VERIFIED](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) | [VERIFIED](https://docs.github.com/en/copilot/reference/hooks-reference) `top-level-block` | [VERIFIED](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) | [VERIFIED](https://docs.github.com/en/copilot/reference/hooks-reference) `userPromptSubmitted` |
| `copilot/vscode` | `copilot` | [VERIFIED](https://raw.githubusercontent.com/microsoft/vscode-docs/main/docs/agents/run/approvals.md) | [VERIFIED](https://raw.githubusercontent.com/microsoft/vscode-docs/main/docs/agents/reference/hooks-reference.md) `vscode-hook-specific-output` | none documented | [VERIFIED](https://raw.githubusercontent.com/microsoft/vscode-docs/main/docs/agents/reference/hooks-reference.md) `UserPromptSubmit` |
| `cursor` | `cursor` | [VERIFIED](https://cursor.com/docs/cli/changelog) | [VERIFIED](https://cursor.com/docs/agent/hooks) `cursor-followup-message` | [VERIFIED](https://cursor.com/docs/cli/using) | [VERIFIED](https://cursor.com/docs/agent/hooks) `beforeSubmitPrompt` |
| `gemini` | `gemini` | none documented | none documented | none documented | none documented |
| `gemini-cli` | `gemini-cli` | none documented | [VERIFIED](https://geminicli.com/docs/hooks/reference/) `gemini-deny` | [VERIFIED](https://geminicli.com/docs/cli/headless/) | [VERIFIED](https://geminicli.com/docs/hooks/reference/) `BeforeAgent` |
| `hermes` | `hermes` | [VERIFIED](https://hermes-agent.nousresearch.com/docs/user-guide/features/goals) | [VERIFIED](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) `plugin` | [VERIFIED](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) | [VERIFIED](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) `pre_llm_call` |
| `kimi` | `kimi` | [VERIFIED](https://www.kimi.com/help/kimi-code/cli-goals) | [VERIFIED](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html) `exit-2` | [VERIFIED](https://www.kimi.com/code/docs/en/kimi-code-cli/reference/kimi-command.html) | [VERIFIED](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html) `UserPromptSubmit` |
| `nexus-ai` | `nexus-ai` | none documented | none documented | none documented | none documented |
| `openclaw` | `openclaw` | [VERIFIED](https://docs.openclaw.ai/tools/goal) | [VERIFIED](https://docs.openclaw.ai/plugins/hooks/prompt-and-session) `plugin` | [VERIFIED](https://docs.openclaw.ai/cli/agent) | [VERIFIED](https://docs.openclaw.ai/plugins/hooks/reference) `message_received` |
| `opencode` | `opencode` | none documented | [VERIFIED](https://opencode.ai/docs/plugins/) `plugin` | [VERIFIED](https://opencode.ai/docs/cli/) | none documented |
| `pi` | `pi` | none documented | [VERIFIED](https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/coding-agent/docs/extensions.md) `plugin` | [VERIFIED](https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/coding-agent/docs/cli.md) | [VERIFIED](https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/coding-agent/docs/extensions.md) `before_agent_start` |
| `qwen` | `qwen` | [VERIFIED](https://qwenlm.github.io/qwen-code-docs/en/users/features/headless/) | [VERIFIED](https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/) `top-level-block` | [VERIFIED](https://qwenlm.github.io/qwen-code-docs/en/users/features/headless/) | [VERIFIED](https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/) `UserPromptSubmit` |
| `windsurf` | `windsurf` | none documented | none documented | none documented | [VERIFIED](https://docs.devin.ai/desktop/cascade/hooks) `pre_user_prompt` |
| `windsurf/devin-cli` | `windsurf` | none documented | [VERIFIED](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks) `top-level-block` | [VERIFIED](https://docs.devin.ai/cli/reference/commands) | [VERIFIED](https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks) `UserPromptSubmit` |

## Continuation formats

The gate emits exactly one shape per format id. The vendor wording for each row is preserved in the JSON as `vendor_shape`.

| Format id | Output that refuses the stop | Rows |
|---|---|---|
| `top-level-block` | stdout JSON `{"decision": "block", "reason": "<text>"}` | `claude`, `codex`, `copilot`, `copilot/cli`, `qwen`, `windsurf/devin-cli` |
| `vscode-hook-specific-output` | stdout JSON `{"hookSpecificOutput": {"hookEventName": "Stop", "decision": "block", "reason": "<text>"}}` | `copilot/vscode` |
| `cursor-followup-message` | stdout JSON `{"followup_message": "<text>"}` | `cursor` |
| `antigravity-continue` | stdout JSON `{"decision": "continue", "reason": "<text>"}` | `antigravity2`, `antigravity2/cli` |
| `gemini-deny` | stdout JSON `{"decision": "deny", "reason": "<text>"}` | `gemini-cli` |
| `exit-2` | exit code 2 with the reason on stderr | `kimi` |
| `plugin` | a typed plugin return value or SDK call (OpenCode, OpenClaw, Pi, Hermes) | `opencode`, `openclaw`, `pi`, `hermes` |

Copilot CLI and VS Code Copilot both read `~/.copilot/hooks/` but expect different shapes, and exit 2 is only a warning in Copilot CLI. The gate therefore infers the Copilot surface from the payload rather than trusting a single registration format.

## Findings that constrain the design

- **Documented caps end a run the gate cannot extend.** Claude Code, Copilot CLI, and Qwen override a Stop hook after 8 consecutive blocks; Cursor's `loop_limit` defaults to 5; OpenClaw allows at most three revisions; Hermes' `max_verify_nudges` defaults to 3. These are why the `run-plan` runner exists: it resumes the session after a platform ends the turn.
- **Three platforms have no continuation lever.** Windsurf/Devin Desktop's `post_cascade_response` is asynchronous and cannot refuse a stop; Aider has no hooks; Nexus-AI documents none. They receive the completion contract as instructions, plus the runner where a headless CLI is documented (Aider, Devin CLI).
- **Two plugin levers are weaker than the others.** OpenCode documents `session.idle` and `client.session.prompt` separately but never shows them composed into a continuation. Hermes' `pre_verify` fires only on turns where the agent edited code. For both, the runner is the primary layer and the plugin is best-effort.
- **Headless goal entry points are documented only for Claude Code, Qwen, Kimi, and Copilot CLI.** Codex, Cursor, Antigravity CLI, and Hermes document `/goal` interactively but not in a one-shot run, so `run-plan` prints an interactive goal line for them instead of setting one.
- **Antigravity 1.0 remains unverified.** The Antigravity hooks page covers "Antigravity 2.0, Antigravity CLI, and Antigravity IDE" without saying whether that IDE is the 1.0 product; see the v4.13.2 known gaps.
