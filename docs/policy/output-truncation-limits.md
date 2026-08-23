# Output Truncation Limits

This is the dated, sourced contract for how much output a single tool call may print before a target CLI truncates it, and which part is dropped. It exists so Nexus-Hub scripts that print agent-consumed text can page their output below every verified surface.

These numbers are **transport limits**, not content limits. They say nothing about how large a report, a catalog, or a memory store may be. They only bound what one tool-call payload may contain if the agent is to see it whole. The shared helper that applies them is `scripts/lib/output_paging.py`.

**Last verified**: 2026-08-23.

**Safe default**: the minimum across all **MATCH** rows. Today that is **20,000 bytes** and **256 lines**. Callers may raise either cap; lowering below the safe default is allowed but is no longer guaranteed to survive every verified surface. A surface that cannot be verified is marked **UNVERIFIED** and is **not** used to compute the default. Guessing a number for an unverified surface is forbidden.

Classification follows `docs/policy/platform-read-contracts.md`: **MATCH** (first-party evidence agrees with the recorded figure), **DRIFT** (first-party evidence exists but disagrees or is incomplete), **UNVERIFIED** (no dated first-party evidence this pass).

## Current pass (2026-08-23)

| Surface | Byte limit | Token limit | Line limit | Truncation position | Evidence | Verified | Class |
|---|---|---|---|---|---|---|---|
| Cursor (Agent / CLI Shell tool) | 20,000 characters inline | none documented | none documented | tail dropped once the inline cap is hit; a spill file is created only above ~40,000 characters | Cursor staff confirmation on the official forum: inline Shell output is cut at 20k and the overflow file is created only above 40k, so the 20k-40k band is lost. [Source](https://forum.cursor.com/t/the-20k-40k-character-loss-zone-for-the-shell-tool/163017) | 2026-08-23 | **MATCH** |
| Claude Code (Bash tool) | 30,000 characters default (`BASH_MAX_OUTPUT_LENGTH`) | none documented | none documented | middle (head and tail retained) | Official settings page documents `BASH_MAX_OUTPUT_LENGTH` as the maximum number of characters in bash outputs before they are middle-truncated. The default of 30,000 is the figure the official docs issue quotes from that table and the figure empirical reports reproduce. The 2026-08-23 fetch of [the settings page](https://code.claude.com/docs/en/settings) is JS-rendered and did not expose the environment-variable table as static Markdown, so the classification rests on the first-party docs issue that quotes the table verbatim. [Source](https://github.com/anthropics/claude-code/issues/19901) | 2026-08-23 | **MATCH** |
| Gemini CLI (and Antigravity CLI, same settings surface) | 40,000 characters (`tools.truncateToolOutputThreshold`) | none documented for the tool-output path | none (line-based truncation was removed) | middle (first 20% and last 80% of the threshold, with an omission marker) | Official settings reference: "Maximum characters to show when truncating large tool outputs. Set to 0 or negative to disable truncation." Default `40000`. [Source](https://geminicli.com/docs/cli/settings/) | 2026-08-23 | **MATCH** |
| Codex CLI | none documented as a current byte cap | 10,000 tokens default (`tool_output_token_limit`) | none documented as current (historical 256-line cap was replaced) | middle (head and tail retained) | Maintainer confirmation on the official repository that v0.60.0 raised the default to 10k tokens and that `tool_output_token_limit` overrides it. The older 10 KiB / 256-line model-format cap is therefore historical, not current. [Source](https://github.com/openai/codex/issues/6426) | 2026-08-23 | **MATCH** (token cap); historical byte/line figures are not used |
| OpenCode | UNVERIFIED | UNVERIFIED for live tool output | UNVERIFIED | UNVERIFIED | Official CLI and compaction pages document `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX` (model-response tokens) and a 2,000-character tool-output bound **during session compaction**, not a live per-tool-call truncation limit. No first-party page states how much a single current tool result may contain. [CLI](https://opencode.ai/docs/cli/) [Compaction](https://opencode.ai/v2/docs/compaction) | 2026-08-23 | **UNVERIFIED** |

### How the safe default was chosen

- **Bytes.** The tightest verified inline cap is Cursor's 20,000 characters. Treating that as a UTF-8 **byte** cap is the safe direction: ASCII output matches the character figure, and multi-byte UTF-8 becomes stricter rather than looser. Claude (30,000 characters), Gemini (40,000 characters), and Codex (10,000 tokens, typically far above 20,000 bytes) are all looser.
- **Lines.** No current MATCH row publishes a live line cap. Codex's historical 256-line model-format cap is the tightest **ever verified** line number on a Nexus-Hub target. It is kept as a conservative transport line cap so a payload of 20,000 short lines cannot blow a surface that still applies a line fuse. It is not claimed as a current official Codex setting.
- **OpenCode** does not move the default. An UNVERIFIED surface is excluded rather than guessed.

### Surfaces deliberately not guessed

The following Nexus-Hub install targets have no dated first-party tool-output truncation page in this pass and are **UNVERIFIED**: OpenCode (live tool path), GitHub Copilot, Qwen Code, Kimi Code CLI, Aider, Windsurf, OpenClaw, and Nexus-AI. They inherit the safe default. A future pass that finds a first-party number must update the table and recompute the default if the new number is tighter.

## Helper contract

`scripts/lib/output_paging.py` reads these defaults. It:

- Caps each part by **both** the byte cap and the line cap.
- Never splits a line.
- Reports (does not silently truncate) a single line that exceeds the byte cap.
- Adds no framing when the whole payload fits in one part.
- When more parts remain, appends exactly one trailing line naming the resolved command that fetches the next part.

A PowerShell sibling is not shipped in this pass: no `.sh` consumer of the helper exists yet. The installer already copies the whole `scripts/lib/` tree, so the Python module reaches every platform without a new named copy step.

## Re-verification rule

Re-verify this file when a target CLI documents a new truncation lever, when a MATCH row's source URL 404s or redirects off-host, or when a release changes a script that prints agent-consumed output. A pass that cannot fetch a source must mark that row UNVERIFIED rather than carrying the old number forward as if it were fresh. The safe default is recomputed only from MATCH rows in the then-current table.
