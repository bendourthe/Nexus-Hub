# rtk: Context Window Compression for Claude Code

## What Is rtk?

`rtk` is a CLI proxy written in Rust. Once wired into Claude Code via a PreToolUse hook, it intercepts every Bash command Claude executes and compresses the command output before it is written into the context window.

**Without rtk:** A 30-minute session can consume 150,000+ tokens, with the majority coming from verbose command output — passing test lines, npm install progress, build logs, and banners.

**With rtk:** The same session is reported to use approximately 45,000 tokens, a roughly 70% reduction.

Run `rtk gain` at any time to see your cumulative token savings.

---

## Platform Support

| Platform | OS | Supported | Method |
|----------|----|-----------|--------|
| Claude Code | macOS / Linux | Yes | Hook in `settings.json` — transparent interception of all Bash commands |
| Claude Code | Windows | Yes | Instructions injected into `CLAUDE.md` — Claude prefixes commands with `rtk` |
| Gemini | Any | No | Use prompt-level output minimization (see below) |
| Codex | Any | No | Use prompt-level output minimization (see below) |
| Copilot | Any | No | Use prompt-level output minimization (see below) |

rtk works on all operating systems for Claude Code, but uses different integration mechanisms depending on the platform (see [Wiring rtk into Claude Code](#wiring-rtk-into-claude-code) below). For Gemini, Codex, and Copilot, see [Output Minimization for Other Platforms](#output-minimization-for-other-platforms).

---

## Prerequisites

`rtk` requires **Rust and Cargo**. If you do not have Rust installed:

**macOS / Linux:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
```

**Windows (PowerShell):**
Download and run `rustup-init.exe` from https://rustup.rs, or install via winget:
```powershell
winget install Rustlang.Rustup
```

Verify your installation:
```bash
cargo --version
rustc --version
```

---

## Installation

Install rtk from source:

```bash
cargo install --git https://github.com/rtk-ai/rtk
```

Cargo compiles and installs the binary to `~/.cargo/bin/`. Ensure this directory is in your PATH:

```bash
# Verify rtk is available
rtk --version
```

If the command is not found after installation, add `~/.cargo/bin` to your PATH:
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.cargo/bin:$PATH"
```

---

## Wiring rtk into Claude Code

Run the initialization command once:

```bash
rtk init --global
```

The behavior differs by OS:

### macOS / Linux

rtk adds a PreToolUse hook to `~/.claude/settings.json`. All Bash commands Claude executes are intercepted transparently — no change to how Claude behaves.

Verify:
```bash
cat ~/.claude/settings.json | grep -A5 rtk
```

You should see an entry in the `PreToolUse` hooks array referencing the `rtk` command.

### Windows

rtk cannot use Claude Code's hook system on Windows (hooks require a Unix shell). Instead, it injects a block of instructions into `~/.claude/CLAUDE.md` (the `<!-- rtk-instructions -->` block). These instructions tell Claude Code to proactively prefix commands with `rtk` — for example, running `rtk npm install` instead of `npm install`. The rtk binary then intercepts the output and compresses it before returning it to the context window.

Verify:
```powershell
Get-Content "$env:USERPROFILE\.claude\CLAUDE.md" | Select-String "rtk-instructions"
```

You should see the `<!-- rtk-instructions -->` marker near the end of your CLAUDE.md.

---

## Verifying It Works

Start a Claude Code session and run a few commands (install a package, run tests, run a build). Then exit the session and check your savings:

```bash
rtk gain
```

Sample output:
```
Total tokens saved: 28,432
Sessions intercepted: 3
Average reduction: 68%
```

---

## Security and Trust Considerations

Before deploying `rtk` in a team or production environment, consider the following:

**Source transparency:** `rtk` is installed directly from a GitHub repository via `cargo install --git`. Unlike packages distributed through crates.io, there is no package registry review. Review the source code before installing in sensitive environments.

**Integration scope:** On macOS/Linux, `rtk init --global` intercepts every Bash command Claude Code runs via a hook. On Windows, the injected CLAUDE.md instructions ask Claude to route commands through rtk voluntarily. In both cases, command output passes through the rtk binary before reaching the context window. If your commands output secrets, credentials, or sensitive data, this output will pass through the rtk proxy.

**Recommendation:** For personal developer machines used for general coding, the convenience typically outweighs the risk. For shared CI environments or machines with production access, audit the source and consider whether the hook scope is acceptable.

---

## Troubleshooting

**`rtk` command not found after install:**
- Ensure `~/.cargo/bin` is on your PATH (see Installation section above)
- On Windows, restart your terminal after installation to refresh PATH

**No savings reported by `rtk gain`:**
- macOS/Linux: Confirm the hook appears in `~/.claude/settings.json`; start a new Claude Code session (hooks load at session start)
- Windows: Confirm the `<!-- rtk-instructions -->` block exists in `~/.claude/CLAUDE.md`; Claude Code must read and follow those instructions in the session
- Run a command that produces substantial output (e.g., `npm install` or `pytest`)

**Hook conflicts with existing settings.json (macOS/Linux only):**
- If your settings.json already has PreToolUse hooks, `rtk init --global` should merge rather than overwrite
- If conflicts occur, manually add the rtk PreToolUse entry to your existing hooks array

**Reverting the integration:**
```bash
# Remove the binary
cargo uninstall rtk

# macOS/Linux: remove the PreToolUse entry from ~/.claude/settings.json
# Windows: remove the <!-- rtk-instructions -->...<!-- /rtk-instructions --> block from ~/.claude/CLAUDE.md
```

---

## Output Minimization for Other Platforms

Gemini, Codex, and Copilot do not support hook-based command interception. The equivalent approach is to add output minimization instructions to your AI instruction file.

Add the following section to your `GEMINI.md`, `AGENTS.md`, or `.github/copilot-instructions.md`:

```markdown
## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log
```

The Nexus-Hub installer automatically includes this section in all generated `GEMINI.md`, `AGENTS.md`, and Copilot instruction files when you run the installer.

---

## Related Resources

- [context-optimization skill](../catalog/skills/developer-experience/context-optimization/SKILL.md) — AI-assisted guidance for applying these optimizations to a project
- [CLAUDE_CODE_SETTINGS_REFERENCE.md](CLAUDE_CODE_SETTINGS_REFERENCE.md) — Full reference for Claude Code settings.json and hooks
- [CLAUDE_CODE_GUIDE.md](CLAUDE_CODE_GUIDE.md) — General Claude Code setup and usage guide
