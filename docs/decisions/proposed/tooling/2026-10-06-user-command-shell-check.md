# Decision: Warn the user, at turn end, when a reply hands them a command Windows PowerShell 5.1 cannot parse

Status: proposed - a default-on, warn-only `user-command-shell-check` Stop hook reads the final assistant message on Claude Code and shows the user one `systemMessage` warning when a PowerShell-bound code block uses `&&`, `||`, a heredoc, a leading `VAR=value` prefix, or `export`; it never blocks and is silent on every other platform.

## Problem

The communication contract (`catalog/style-guides/agent-communication.md`, section 3.3) says a command handed to a Windows user must parse in Windows PowerShell 5.1. Agents still emit Bash idioms such as `a && b` inside blocks the user is told to paste into PowerShell, and 5.1 rejects them with a parser error. The rule lives only in instruction text, so nothing tells the user when it was missed until the paste fails.

## Proposal

Ship `catalog/hooks/user-command-shell-check.py`, registered on `Stop` after `usage-guard` with a 10-second timeout. It reads `last_assistant_message` from the Stop payload, which the Claude Code hooks reference recommends over reading the transcript, and falls back to the tail of `transcript_path`. It checks blocks labelled `powershell`, `ps1`, `pwsh`, or `ps`, plus unlabelled blocks on a Windows host, and flags the five Bash-only forms per line with comments and quoted strings ignored. Findings produce one `systemMessage`, documented by Claude Code as a "Warning message shown to the user", naming only the tokens and line numbers. Every failure path exits 0 silently. `NEXUS_DISABLED_HOOKS=user-command-shell-check` or `NEXUS_HOOK_PROFILE=minimal` turns it off.

## Alternatives considered

- **Block the turn (`decision: "block"`) so the agent rewrites the command.** Declined. A false positive would force an extra model turn on every affected reply and interact with the completion gate, which also answers `Stop`. A warning gives the user the information at no cost to the session.
- **Run on every platform that receives the Stop chain.** Declined for now. Cursor, Codex, GitHub Copilot, Kimi, Gemini CLI, and Qwen Code each have a different turn-end output channel, and none is verified in this repository for a user-visible warning. The hook detects those payloads by their documented keys and stays silent rather than emit output a host may misread.
- **Check unlabelled blocks on every host.** Declined. On macOS and Linux an unlabelled block is usually Bash, where `&&` is correct, so the check would be noise there.
- **Parse the whole transcript.** Declined. Transcripts grow without bound; the payload field carries the final text directly, and the fallback reads only the last 512 KiB.

## Acceptance criteria

- `python -m pytest -q catalog/hooks/tests/test_user_command_shell_check.py` passes, covering each flagged form, the clean PowerShell forms (`A; if ($?) { B }`, `$env:X = "1"`), labelled non-PowerShell blocks, the platform override, `stop_hook_active`, other-platform payloads, both disable switches, malformed stdin, a missing transcript, and a BOM-prefixed UTF-8 payload.
- The hook exits 0 on every input and writes nothing to stderr.

## Risks

- A PowerShell line that legitimately contains `&&` outside quotes (rare; it is a parse error in 5.1 but valid in PowerShell 7) produces a warning. The cost is one advisory line.
- If Claude Code renames `last_assistant_message`, the transcript fallback keeps the hook working; if both change, the hook goes silent rather than wrong.
