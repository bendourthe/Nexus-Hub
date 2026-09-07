---
name: helper-script-authoring
description: Author and grow small, well-documented helper scripts in a project tools/ or bin/ folder so the agent stops re-typing fragile multi-step incantations. Make sure to use this skill whenever the user says "write a helper script", "make a bin script for this", "automate this repetitive command", "build a CLI wrapper for the agent", "I keep running the same commands", or when the agent notices it is repeating a multi-command sequence it could encapsulate. SKIP, do NOT use for, authoring a slash command (use create-custom-command), building an MCP server (use mcp-builder), or a genuinely one-off command that will not recur.
summary_l0: "Author and grow project helper scripts so the agent stops re-typing incantations"
overview_l1: "This skill teaches the agent to identify a recurring multi-step incantation and encapsulate it as a small, robust, well-documented helper script in a project tools/ or bin/ folder, then keep growing that collection over time. It covers when a helper is worth writing (a sequence run more than a few times, or one whose exact flags are easy to get wrong), how to make it robust (safety flags, argument validation, clear errors, per the bash / python code-style rules), how to make it DISCOVERABLE so future sessions find and reuse it (a header comment, a --help, and a one-line entry in a tools README), and the discipline of building the collection out continuously rather than re-deriving commands each session. The worked example is an agent_review-style wrapper that kicks off cross-agent reviews without the agent memorizing each tool's flags. Trigger phrases: write a helper script, automate this repetitive command, build a CLI wrapper for the agent, I keep running the same commands."
---

# Helper-Script Authoring

Stop re-typing the same fragile multi-command incantation. When the agent finds itself running a sequence more than a few times, or a command whose exact flags are easy to get wrong, the fix is a small, documented helper script in the project's `tools/` or `bin/` folder - written once, discoverable forever, and grown over time.

## When to Use This Skill

- The agent (or the user) keeps running the same multi-step command sequence and it is slow or error-prone to retype.
- A command's exact flags are easy to get wrong, so wrapping them in a named script removes a whole class of mistakes.
- Building out a project's `tools/` collection so common operations become one memorable command.

**Trigger phrases**: "write a helper script", "make a bin script", "automate this repetitive command", "build a CLI wrapper", "I keep running the same commands".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Add an agent slash command | `create-custom-command` |
| Build an MCP server | `mcp-builder` |
| Run a genuinely one-off command | Just run it |
| Add a bundled tier-3 script INSIDE a skill | The skill's own `scripts/` bundle |

## Instructions

1. **Spot the recurring incantation.** Notice a multi-step sequence run more than a few times, or one with error-prone flags. That is the candidate to encapsulate. A single command run once is not.
2. **Encapsulate it as a robust script** in the project's `tools/` or `bin/` folder. Follow the language's code-style and safety rules (`catalog/rules/bash/*` for shell: `set -euo pipefail`, quote expansions, validate args, clear error messages; the Python rules for `.py`). Accept arguments rather than hardcoding; fail loudly with a helpful message, not silently.
3. **Make it discoverable** so a future session finds and reuses it instead of re-deriving the commands: a top-of-file header comment stating what it does and how to run it, a `--help`/`-h` usage, and a one-line entry in a `tools/README.md` (name -> what it does). Discoverability is what turns a script into leverage; an undiscovered script is re-written next week.
4. **Keep building the collection out.** Each time a new repetitive operation appears, add a script (or a subcommand). Over time the `tools/` folder becomes the project's operational vocabulary - the agent invokes `tools/<name>` instead of remembering incantations.
5. **Worked example - an `agent_review` wrapper.** A script that kicks off cross-agent reviews (`agent_review <path>`) so the agent does not need to remember each reviewer tool's particular invocation. It resolves the diff, dispatches to the configured reviewers, and prints a consolidated result - one command replacing several tool-specific ones.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just run the commands each time." | Re-typing a fragile sequence re-introduces the same mistakes and burns time every session; a named script pays for itself after the third run. |
| "The script is obvious, it doesn't need docs." | An undiscovered or unexplained script gets re-written by the next session instead of reused. The header comment, `--help`, and README line are what make it leverage rather than dead code. |
| "This should be a slash command / an MCP server." | Slash commands (`create-custom-command`) drive the agent's prompt flow; MCP servers (`mcp-builder`) expose tools over a protocol. A helper script is a local CLI the agent shells out to - a different, lighter tool. |
| "One big script for everything." | A grab-bag script is as hard to remember as the raw commands. Prefer small, single-purpose scripts (or clear subcommands) with obvious names. |

## Verification

- [ ] The script lives in the project's `tools/` or `bin/` folder and runs from a clean checkout.
- [ ] It follows the language safety rules (shell: `set -euo pipefail`, quoted expansions, arg validation; Python: type hints, clear errors).
- [ ] It is discoverable: a header comment, a `--help` usage, and a one-line entry in `tools/README.md`.
- [ ] It accepts arguments (no hardcoded paths/values) and fails loudly with a helpful message on bad input.
- [ ] A genuinely one-off task was NOT turned into a script.

## Related Skills

- [[create-custom-command]] -- authors agent slash commands (prompt-flow), distinct from a shelled-out helper script.
- [[mcp-builder]] -- builds MCP servers that expose tools over a protocol, distinct from a local CLI helper.
- [[powershell-expert]] -- for robust `.ps1` helper scripts on Windows; pair a `.ps1` with a `.sh` when the helper must run cross-platform.
- [[filesystem-context-patterns]] -- using the filesystem (scratch pads, tools) as durable agent context.

---

**Version**: 1.0.0
**Last Updated**: July 2026
