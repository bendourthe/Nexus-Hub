# Permission-mode contract for Nexus-Hub hooks

Summary: how Nexus-Hub hooks behave under each host approval mode (Claude Code default, acceptEdits, plan, auto, dontAsk, bypassPermissions; Codex, Cursor, GitHub Copilot, and Google Antigravity equivalents). Read it before adding or changing any hook that blocks a tool call or returns a permission decision. Key topics: full access means no Nexus-Hub gate, auto mode keeps the deterministic guards but never forces a prompt, the mode signal each platform exposes, and the platforms where full access cannot be detected.

## Rule

The user's chosen host mode decides how much friction a session has. Nexus-Hub adds guards on top of the prompting modes; it never adds prompts or blocks to a mode the user picked to remove them.

| Host mode (`permission_mode`) | Prompt-forcing hooks (`ask`) | Security guards (block / exit 2) |
|---|---|---|
| absent, `default`, `acceptEdits`, `plan` | force `ask` as before | block as before |
| `auto` | never force `ask`; the classifier decides | block as before |
| `dontAsk` | never force `ask`; the pre-approval list decides | block as before |
| `bypassPermissions` (full access) | silent | step aside (user-edit-guard and escalation-trigger downgrade to a warning) |

Prompt-forcing hooks: `format-powershell-description.py`, `rewrite-command.{sh,ps1}` (its `ask` branch only; a `deny` mirrors the host's own deny rules and stays).

Security guards: `git-guardrails`, `secret-scan`, `memory-store-guard`, `user-edit-guard`, and `escalation-trigger` when `ESCALATION_MODE=block`.

Not covered, by design: advisory hooks that only warn (`large-file-guard`, `escalation-trigger` in its default `warn` mode), and workflow and authoring rules the user configured independently of approvals (`require-description`, `require-powershell-description`, `attribution-guard`, `html-responsive-guard`, `old-version-docs-guard`, `code-search-routing`, `usage-guard`, `completion-gate`, and the opt-in `skill-guard`). They never raise an approval prompt; they reject a malformed or policy-breaking call so the agent can correct it.

## Auto mode

Auto mode runs a safety classifier and prompts only for risky or out-of-scope actions. A hook `ask` forces a prompt even there (Claude Code hooks reference), so a hook that asks for every unlisted command turns auto mode back into manual mode. The prompt-forcing hooks therefore stay silent on the decision in `auto` and `dontAsk`. The security guards keep blocking: they are deterministic checks for irreversible actions (history rewrites, committed secrets, overwritten user edits), which is the same class of action auto mode exists to stop, and a deterministic check complements a model classifier rather than duplicating it.

## Detection per platform

Each guard reads only the top-level `permission_mode` string from parsed JSON. A nested field inside `tool_input`, JSON-escaped file content, or a non-string mode cannot switch a guard off. Bash uses jq or Python; if neither parser is available, it retains the normal guard behavior rather than inferring full access from text.

| Platform | Mode signal | Full-access value | Status |
|---|---|---|---|
| Claude Code | `permission_mode` in every tool-hook payload | `bypassPermissions` | detected |
| Codex | `permission_mode` in hook payloads | not documented; `bypassPermissions` assumed | detected when Codex sends `bypassPermissions`; any other value keeps the guards on |
| Antigravity | none in the payload | "Always Proceed" / CLI `toolPermission: always-proceed` | silent hooks now return `allow` ("delegating to the next hook or default policy"), so Always Proceed is honored; a guard block still applies |
| Cursor | none (`sandbox` describes where a command runs, not approval) | "Run Everything" | not detectable; guard blocks still apply |
| GitHub Copilot | none | CLI `--yolo` / `--allow-all`, VS Code "Allow all" | not detectable; silent hooks already return no decision, guard blocks still apply |

Sources (fetched 2026-10-13): code.claude.com/docs/en/hooks.md, code.claude.com/docs/en/permission-modes.md, learn.chatgpt.com/docs/hooks, antigravity.google/docs/hooks, cursor.com/docs/agent/hooks, docs.github.com/en/copilot/reference/hooks-configuration, code.visualstudio.com/docs/agents/reference/hooks-reference.

## Known gaps

- Cursor, Copilot, and Antigravity expose no mode to hooks, so a guard block (for example `git reset --hard`) still stops a full-access session there. Per-session override: `NEXUS_DISABLED_HOOKS=<guard>`.
- Codex's full-access `permission_mode` value is undocumented. If it is not `bypassPermissions`, Codex guards stay on (the safe direction).
- Cursor's adapter answers `{"permission": "allow"}` for a silent hook on shell events. Cursor does not document whether that overrides an "Ask every time" run mode; unverified, unchanged here.

## Adding a hook

A new hook that returns `ask`, returns `deny`, or exits 2 must place itself in the table above and carry a test that runs it with `permission_mode` set to `default`, `auto`, and `bypassPermissions`. The aggregate test is `catalog/hooks/tests/test_permission_mode_contract.py`.
