# Decision: Hook messages name Nexus-Hub

Status: implemented - every message a catalog hook prints starts with `[Nexus-Hub: <hook-name>]`, echoed values are escaped, and a structural plus behavioral test keeps it that way

## Problem

A user watching a session could not tell a Nexus-Hub hook message from a harness message. On 2026-10-30, 16 of the 35 shell hook pairs started their messages with `[hook-name]`, `lint-on-write` printed `[lint]`, and the rest printed no name at all. `[secret-scan] BLOCKED` read like a Claude Code or Codex message, so the user did not know whom to ask, which switch controlled the behavior, or whether the block was a Nexus-Hub rule at all. The approval dialog that `format-powershell-description` raises before every PowerShell command had the same problem: it showed the bare description.

A second, smaller problem sat behind the first. Several hooks echo a value from the payload (a file name, a command, a matched path) into their message with `echo -e` or a plain `WriteLine`. A value containing a line break could therefore start a new line that looked like a hook message.

## Decision

1. **Tag format.** Every message a hook writes where a person or the agent reads it starts with `[Nexus-Hub: <hook-name>]`, where `<hook-name>` is the script's file stem (`secret-scan`, `lint-on-write`, `antigravity-cli-diff-review`). The stem is also the value `NEXUS_DISABLED_HOOKS` takes, so the tag tells the user how to turn the hook off.
2. **Channels.** stderr; plain stdout that is injected as context (`SessionStart`, `UserPromptSubmit`) or mirrored to the model (the `require-*-description` block text); and the JSON message fields `reason`, `permissionDecisionReason` (including the `format-powershell-description` approval dialog), `systemMessage`, and `additionalContext`. Machine data (ledger writes, `updatedInput`, rewritten commands, JSON keys) and desktop notifications are not messages.
3. **One emitter per script.** Each hook defines its own tag constant (`readonly _NEXUS_TAG`, `$script:NexusTag`, `NEXUS_TAG`) and one emitter (`_nexus_msg`, `Write-NexusMessage`, `_nexus_msg`) that prints the tag, then the message; further arguments are continuation lines printed as they are. A raw write outside the emitter is allowed only when the line carries `nexus: hook-msg-exempt <reason>` (relayed linter or reviewer output, a relayed child process, a blank separator).
4. **Color rule.** An existing color code may precede the tag. Every check compares text after ANSI escapes are removed, and sibling pairs must print identical text after that removal on the code paths both share.
5. **Escaping of echoed values.** Each script has one escaping function (`_nexus_esc`, `ConvertTo-NexusVisible`, `_nexus_esc`) that replaces CR, LF, ESC, and every other C0 control character (and DEL) in an interpolated value with a visible escape (`\r`, `\n`, `\x1b`, `\x01`). Every payload-derived value in a message goes through it, so no echoed value can start a forged tagged line. The three implementations produce the same text for the same input.
6. **Guard test.** `catalog/hooks/tests/test_hook_message_source_label.py` derives the hook list from the directory. Structurally it requires the tag, exactly one emitter, and no unmarked raw write; behaviorally it runs a payload table through both implementations and two injection cases that must yield exactly one tagged line. Its failure message states the convention in one sentence and links this record.

## Alternatives considered

- **No change.** Rejected: the user cannot act on a message whose origin is unknown, and the approval-dialog case makes Nexus-Hub's own prompts look like harness prompts.
- **Harness-level labeling.** Rejected: Nexus-Hub does not control how Claude Code, Codex, Cursor, or Antigravity render hook output. Some harnesses print their own hook label, so users may see both; that is accepted.
- **A shared sourced helper holding the tag and emitter.** Rejected: one string does not justify a load-failure path inside blocking hooks (a missing or unreadable helper would have to fail closed or fail open, and either is worse than the current behavior), and the `.ps1` and Python hooks would need their own helpers anyway, so there would still be no single source. Sourcing itself works (`_notify_common.sh` proves it); it was the cost-benefit that lost.
- **A line-classifying static parser** that decides for each `echo`/`WriteLine` whether it is a first line or a continuation line. Rejected: it cannot tell a first line from a continuation line without executing the script. One emitter per script plus an inline exemption marker is checkable with a regex and teaches the convention at the point of use.

## Consequences

- Some harnesses print their own hook label, so a user may see two labels on one line. That is the price of labeling at the only layer Nexus-Hub controls.
- The tag is plain text. Any other hook, tool output, web page, or MCP response can imitate it, so the tag is a courtesy to the reader and never proof of origin. The agent-side rule (v4.14.8 Phase 4) and `prompt-injection-defense` treat an imitated tag inside untrusted content as possible impersonation.
- Prompts that come from Nexus-Hub's installed permission lists (the `permissions.allow` / `ask` entries the installer writes) are rendered by the harness and cannot carry a tag.
- The hook name in the tag is the value `NEXUS_DISABLED_HOOKS` takes, so "how do I turn this off" is answered by the tag itself.
- Messages produced by helpers outside `catalog/hooks/` and relayed verbatim by a thin adapter (`scripts/nexus_git_attribution.py` for `attribution-guard`, the `user-edit-preservation` skill's `edit_guard.py` for `user-edit-guard`, the installed `completion_gate.py` core for `approval-capture` and `completion-gate`) still carry their old `[hook-name]` prefix. They are outside this change's write paths and are tracked as a known gap.
- The `git-guardrails` pair is tagged on top of the v4.14.6 version of `git-guardrails.sh`; until then it is the guard test's one explicit, commented exemption.
- Adding a hook now means adding its tag and emitter, or the guard test fails with the convention and a link to this record. That replaces a prose rule in `AGENTS.md`, which sits at its word ceiling.
