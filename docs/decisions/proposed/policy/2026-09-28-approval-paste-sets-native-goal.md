# Decision: One approval paste sets the native goal only where a probe shows the hook sees it verbatim

Status: proposed - no platform is `verbatim` yet: Claude Code passed a headless probe and gets a single `/goal` approval line only once a typed probe is logged; until then every platform keeps a plain approval line, with the goal line second or printed separately

## Problem

A full `/implement` run records the user's approval only when the submitted prompt equals, as a whole, the checker-generated paste line (v4.13.6 Definition of Done 3). Phase 6 wants that same paste to also set the platform's native goal, so the user pastes once and the session keeps working until the checker's verdict. That works only if the platform's prompt-submit hook fires for a slash-command prompt and receives its text unchanged. If the hook never fires, the approval is never recorded. If the platform rewrites the text (for example, sends only the objective), the whole-prompt match fails. This record settles, per goal platform, which of those holds, and so which paste layout the approval page may use. It unblocks sub-task 6.2.

## Proposal

Each row of `docs/policy/completion-levers.json` carries a `goal_capture` object with `value`, `source_url`, `verified` (ISO date), and `evidence`. The value is one of four:

| Value | Meaning | Approval page behavior |
|---|---|---|
| `verbatim` | A recorded probe showed the hook receives the `/goal` line unchanged. | One paste line starting with `/goal`; it approves the run and sets the native goal. |
| `not-captured` | A goal command exists, but no hook can see the typed line. | The plain approval line first, then the `/goal` line second. |
| `no-goal` | First-party docs list the commands and none is a goal command. | The plain approval line only. |
| `unverified` | The docs do not settle it. | The plain approval line, plus the printed goal line where a goal command exists. |

`verbatim` is accepted only from a recorded probe of a typed `/goal` line (`"probe": true` and `"probe_mode": "interactive"`, citing this record), never by analogy and never from a headless `-p` probe, because the approval is a typed paste. No vendor page checked on 2026-09-29 states that a typed slash command reaches its prompt-submit hook verbatim, and the Claude Code probe below was headless, so no row is `verbatim` yet.

### Claude Code probe

Run 2026-09-29 on Claude Code 2.1.283, Windows 11. A scratch project had a project-level `UserPromptSubmit` hook that logged its stdin. From PowerShell: `claude -p "/goal test condition" --max-turns 1`.

- The hook fired once. The payload had `hook_event_name` `"UserPromptSubmit"` and a `prompt` field of exactly `"/goal test condition"`.
- The session transcript shows the command ran as the native goal: a `goal_status` attachment `{met: false, condition: "test condition"}`, a `<command-name>/goal</command-name>` user entry, and local command stdout `Goal set: test condition`.
- A control prompt `reply with the single word PONG` was also captured verbatim.

Caveats, stated plainly:

- **Interactive path not exercised.** A human typing `/goal` in the terminal UI was not tested separately. The headless prompt goes through the same prompt queue (a `queue-operation` transcript entry), which suggests the typed path behaves the same, but a suggestion is analogy, so the row is `unverified` (`"probe_mode": "headless"`) until a typed probe is logged.
- **MSYS path conversion.** The first attempt through Git Bash reached Claude Code as `C:/Program Files/Git/goal test condition`, because MSYS rewrites a leading `/word` argument into a Windows path. This is a host shell artifact, not Claude Code behavior. Run the headless form from PowerShell, or set `MSYS_NO_PATHCONV=1` in Git Bash. A mangled line would fail the whole-prompt match and be refused, not mis-recorded.

### Per-platform values (checked 2026-09-29)

| Row | Value | Source | Why |
|---|---|---|---|
| `claude` | `unverified` | this record's probe; hook reference https://code.claude.com/docs/en/hooks | Headless probe above showed verbatim capture; the typed path is not yet probed. |
| `antigravity2` | `not-captured` | https://antigravity.google/docs/hooks/ | `/goal` exists, but the hooks page lists only PreToolUse, PostToolUse, PreInvocation, PostInvocation, and Stop, with no prompt-submit event. Judgement call: no page says slash commands skip a hook. |
| `antigravity2/cli` | `not-captured` | https://antigravity.google/docs/hooks/ | Same five-event hooks page; `/goal` is listed for the CLI, and headless `/goal` is undocumented. |
| `codex` | `unverified` | https://learn.chatgpt.com/docs/hooks | `UserPromptSubmit` receives the prompt about to be sent; the docs never say whether a typed slash command reaches it. |
| `copilot/cli` | `unverified` | https://docs.github.com/en/copilot/reference/hooks-reference | `/goal [OBJECTIVE]` starts autopilot; `userPromptSubmitted` carries `prompt`, but slash-command behavior is not stated. |
| `cursor` | `unverified` | https://cursor.com/docs/agent/hooks | `/goal` is in the CLI changelog; `beforeSubmitPrompt` docs say nothing about slash commands or the CLI. |
| `kimi` | `unverified` | https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html | The goals page says Kimi sends the objective as the next user message, so the hook may see altered text; the hooks page does not say. |
| `qwen` | `unverified` | https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/ | Locally acting commands fire no hook, and a separate `UserPromptExpansion` fires for commands that expand into a prompt; `/goal` is never named. |
| `openclaw` | `unverified` | https://docs.openclaw.ai/plugins/hooks/reference | `message_received` observes inbound content; slash-command behavior is not stated. |
| `hermes` | `unverified` | https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks | `pre_llm_call` carries the user's original message; whether `/goal` is that message is not stated. |
| `aider` | `no-goal` | https://aider.chat/docs/usage/modes.html | Modes are code, ask, architect, and help only. |
| `gemini-cli` | `no-goal` | https://geminicli.com/docs/reference/commands/ | No `/goal`; closest is the read-only `/plan`. |
| `opencode` | `no-goal` | https://opencode.ai/docs/tui/ | TUI slash-command list has no `/goal`. |
| `windsurf/devin-cli` | `no-goal` | https://docs.devin.ai/cli/reference/commands | Commands include `/loop <prompt>` but no goal command. |
| `antigravity`, `gemini` | `unverified` | https://antigravity.google/docs/slash-commands/ | No page scopes `/goal` or a prompt-submit event to Antigravity 1.0. |
| `copilot`, `copilot/vscode` | `unverified` | https://docs.github.com/en/copilot/reference/hooks-reference and the VS Code hooks reference | Umbrella row and a mode-picker Autopilot; not assessed for typed goal capture. |
| `nexus-ai`, `pi`, `windsurf` | `unverified` | https://github.com/bendourthe/Nexus-AI, the Pi CLI docs, https://docs.devin.ai/desktop/cascade/hooks | No first-party command reference was found, so absence of a goal command is not settled. |

Third-party issue threads seen during research were not used, because they are not vendor documentation.

## Alternatives considered

- **The agent types `/goal` itself after recording the approval.** Impossible: native `/goal` is a user-typed slash command, and an agent's own output never enters the prompt queue as a user prompt. It would also let the agent set its own stopping condition, which is the thing the approval exists to control.
- **Separate approval and goal pastes on every platform.** Safe everywhere, but it doubles the user's paste work on Claude Code, where the probe shows one line is enough, and a second paste is a second chance to paste the wrong line. Kept as the layout for `not-captured` rows only.
- **Headless-only goals (`claude -p "/goal ..."` launched by `run-plan`).** A prompt the runner launches is not a user approval (Definition of Done 3 refuses runner-launched prompts), so it can set a goal but cannot carry the approval. It remains the automatic path, not the approval path.
- **No native goal at all; rely on the continuation hook and the runner.** Loses the platform's own after-each-turn goal check on the platforms that have one, and documented continuation caps (for example 8 consecutive Stop blocks on Claude Code) end runs the gate cannot extend.
- **Classify by analogy (every platform with `/goal` and a prompt-submit hook is `verbatim`).** Rejected: Kimi documents that it sends only the objective, and Qwen routes some commands to a different event, so analogy would bind approvals to text the hook never sees and every approval would be refused.

## Acceptance criteria

- Every row of `docs/policy/completion-levers.json` carries `goal_capture` with a value from the closed set, a `source_url`, an ISO `verified` date, and evidence; `tests/validators/test_completion_levers.py` enforces this, requires an https source for settled values on non-probe rows, and accepts `verbatim` only with `"probe": true` and `"probe_mode": "interactive"`.
- `docs/policy/completion-levers.md` documents the four values and the page behavior per value.
- Phase 6.2 renders the paste layout from this field and nothing else.
- The Claude Code row moves to `verbatim` only after a typed `/goal` probe log is recorded here; until then it stays `unverified`.

## Risks

- **Interactive divergence.** If typed `/goal` in the terminal UI reaches the hook differently from `-p`, the single line would be refused on Claude Code. This is why the row waits for a typed probe before it becomes `verbatim`.
- **Vendor drift.** Hook payloads and slash-command handling change between releases. Rows must be re-probed or re-checked before a release relies on them.
- **Antigravity judgement call.** `not-captured` for Antigravity 2.0 rests on the absence of any prompt-submit event, not on an explicit vendor statement. If Antigravity adds such an event, the row becomes `unverified` until probed.
