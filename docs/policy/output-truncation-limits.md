# Output Truncation Limits

This is the dated, sourced contract for how much output a single tool call may print before a target CLI truncates it, and which part is dropped. It exists so Nexus-Hub scripts that print agent-consumed text can page their output below every verified surface.

These numbers are **transport limits**, not content limits. They say nothing about how large a report, a catalog, or a memory store may be. They only bound what one tool-call payload may contain if the agent is to see it whole. The shared helper that applies them is `scripts/lib/output_paging.py`.

**Last verified**: 2026-08-23 (second pass; closed the Phase 1 UNVERIFIED rows that had first-party evidence).

**Safe default**: the minimum across all **MATCH** rows. Today that is **16,000 bytes** and **256 lines**. Callers may raise either cap; lowering below the safe default is allowed but is no longer guaranteed to survive every verified surface. A surface that cannot be verified is marked **UNVERIFIED** and is **not** used to compute the default. Guessing a number for an unverified surface is forbidden.

Classification follows `docs/policy/platform-read-contracts.md`: **MATCH** (first-party evidence agrees with the recorded figure), **DRIFT** (first-party evidence exists but disagrees or is incomplete), **UNVERIFIED** (no dated first-party evidence this pass).

## Current pass (2026-08-23, second pass)

| Surface | Byte limit | Token limit | Line limit | Truncation position | Evidence | Verified | Class |
|---|---|---|---|---|---|---|---|
| Cursor (Agent / CLI Shell tool) | 20,000 characters inline | none documented | none documented | tail dropped once the inline cap is hit; a spill file is created only above ~40,000 characters | Cursor staff confirmation on the official forum: inline Shell output is cut at 20k and the overflow file is created only above 40k, so the 20k-40k band is lost. [Source](https://forum.cursor.com/t/the-20k-40k-character-loss-zone-for-the-shell-tool/163017) | 2026-08-23 | **MATCH** |
| Claude Code (Bash tool) | 30,000 characters default (`BASH_MAX_OUTPUT_LENGTH`) | none documented | none documented | valid results over ~30,000 characters arrive as a file path plus preview; failing results are a head-and-tail excerpt | Official environment-variable table and tools-reference Output limits section. `BASH_MAX_OUTPUT_LENGTH` default 30000, hard ceiling 150000. [env-vars](https://code.claude.com/docs/en/env-vars) [tools-reference](https://code.claude.com/docs/en/tools-reference) | 2026-08-23 | **MATCH** |
| Gemini CLI (and Antigravity CLI, same settings surface) | 40,000 characters (`tools.truncateToolOutputThreshold`) | none documented for the tool-output path | none (line-based truncation was removed) | middle (first 20% and last 80% of the threshold, with an omission marker) | Official settings reference: "Maximum characters to show when truncating large tool outputs. Set to 0 or negative to disable truncation." Default `40000`. [Source](https://geminicli.com/docs/cli/settings/) | 2026-08-23 | **MATCH** |
| Codex CLI | none documented as a current byte cap | 10,000 tokens default (`tool_output_token_limit`) | none documented as current (historical 256-line cap was replaced) | middle (head and tail retained) | Maintainer confirmation on the official repository that v0.60.0 raised the default to 10k tokens and that `tool_output_token_limit` overrides it. The older 10 KiB / 256-line model-format cap is therefore historical, not current. [Source](https://github.com/openai/codex/issues/6426) | 2026-08-23 | **MATCH** (token cap); historical byte/line figures are not used |
| OpenCode | 51,200 bytes default (`tool_output.max_bytes`, 50 KiB) | none documented for live tool output | 2,000 lines default (`tool_output.max_lines`) | head kept by default; full output spilled to a truncation file | First-party source on the official repository documents live per-tool defaults `MAX_LINES = 2000` and `MAX_BYTES = 50 * 1024`, overridable via `tool_output` in config. Official product docs still describe only the 2,000-character compaction bound and the model-response token cap; those are not this row. [Source](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/tool/truncate.ts) | 2026-08-23 | **MATCH** |
| GitHub Copilot CLI | 20,480 UTF-8 bytes default (`COPILOT_LARGE_OUTPUT_THRESHOLD_BYTES`) | none documented | none documented | overflow saved to a temporary file; the model receives a path and a preview | Official Copilot CLI context-management page and command reference. [context-management](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/context-management) [command reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference) | 2026-08-23 | **MATCH** |
| Qwen Code | 25,000 characters (`tools.truncateToolOutputThreshold`) | none documented | 1,000 lines (`tools.truncateToolOutputLines`) | applies to Shell, Grep, Glob, ReadFile, and ReadManyFiles | Official Qwen Code settings reference. [Source](https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/) | 2026-08-23 | **MATCH** |
| Kimi Code CLI | 100,000 characters for MCP tool output | none documented | none documented | truncation notice appended; oversized media parts dropped | Official Kimi Code CLI changelog. Built-in tools are described as a separate 50,000-character budget only in a GitHub issue, which is not used for this row. [Source](https://www.kimi.com/code/docs/en/kimi-code-cli/release-notes/changelog.html) | 2026-08-23 | **MATCH** (MCP path) |
| OpenClaw | 16,000 characters default for models below 100K context | none documented as a live byte cap | none documented | live tool-result cap scales with the model window (32,000 at 100K+ tokens, 64,000 at 200K+), still bounded by a 30% context-share guard | Official token-use reference. The tightest documented default is 16,000 characters. [Source](https://docs.openclaw.ai/reference/token-use) | 2026-08-23 | **MATCH** |
| Aider | no silent live cap | none documented | none documented | `/run` output is added only after an interactive confirm that shows the token count | Official maintainer confirmation: Aider asks `Add Nk tokens of command output to the chat?` rather than silently truncating. [Source](https://github.com/Aider-AI/aider/issues/2517) | 2026-08-23 | **MATCH** (no silent cap; inherits the safe default) |
| Windsurf (Cascade) | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | Official Cascade pages document a per-prompt tool-call count, not a live per-tool-output byte or line cap. [Source](https://docs.windsurf.com/plugins/cascade/cascade-overview) | 2026-08-23 | **UNVERIFIED** |
| Nexus-AI | UNVERIFIED | UNVERIFIED | UNVERIFIED | UNVERIFIED | The public Nexus-AI repository and Nexus-Hub's own integration notes document catalog layout, not a first-party live tool-output truncation page. | 2026-08-23 | **UNVERIFIED** |

### How the safe default was chosen

- **Bytes.** The tightest verified live cap is OpenClaw's 16,000-character default for models below a 100K-token window. Treating that as a UTF-8 **byte** cap is the safe direction: ASCII output matches the character figure, and multi-byte UTF-8 becomes stricter rather than looser. Cursor (20,000), Copilot (20,480), Qwen (25,000), Claude (30,000), Gemini (40,000), OpenCode (51,200), and Kimi MCP (100,000) are all looser. Codex is token-capped and typically far above 16,000 bytes. Aider has no silent cap.
- **Lines.** No current MATCH row publishes a live line cap tighter than 1,000 (Qwen). Codex's historical 256-line model-format cap remains the tightest **ever verified** line number on a Nexus-Hub target. It is kept as a conservative transport line cap so a payload of 16,000 short lines cannot blow a surface that still applies a line fuse. It is not claimed as a current official Codex setting.
- **UNVERIFIED** surfaces do not move the default. Windsurf and Nexus-AI inherit 16,000 / 256.

### Surfaces deliberately not guessed

Windsurf and Nexus-AI have no dated first-party live tool-output truncation page after this pass. They inherit the safe default. A future pass that finds a first-party number must update the table and recompute the default if the new number is tighter.

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
