---
name: context-optimization
description: Optimize AI coding session context window usage by compressing command output, minimizing verbose logs, and avoiding context bloat. Use when sessions are hitting token limits, commands produce excessive output, you want to maximize effective session length, or you notice the context window filling up quickly. Covers rtk proxy setup for Claude Code and prompt-level output reduction for Gemini, Codex, and Copilot.
summary_l0: "Optimize AI session context windows by compressing output and reducing token bloat"
overview_l1: "This skill provides techniques for controlling context window consumption in AI coding sessions through automated output compression and prompt-level output minimization. Use it when a session consumes excessive tokens from command output, tests or builds dump full logs into context, you want to extend session length before hitting limits, you are configuring a new environment for context efficiency, or verbose output like progress bars fills the window. Key capabilities include automated compression via rtk (a Rust-based CLI proxy for Claude Code that reduces tokens from 150K to 45K per session), prompt-level minimization with quiet flags, progress bar suppression, long output summarization, and cross-platform strategies for Claude Code, Gemini, Codex, and Copilot. The expected output is a configured environment with reduced context consumption. Trigger phrases: context window, token limit, context bloat, compress output, reduce tokens, session length, verbose output, rtk setup, context optimization."
---

# Context Window Optimization

## When to Use This Skill

Use this skill when:
- A 30-minute Claude Code session is consuming 100K+ tokens from command output alone
- Tests, builds, or package manager commands are dumping full logs into the context window
- You want to extend session length before hitting context limits
- You are configuring a new development environment and want context efficiency from the start
- You notice repeated verbose output (progress bars, banners, passing test lines) consuming context

## What This Skill Does

This skill provides two complementary approaches to controlling context window consumption:

1. **Automated output compression (Claude Code only)** using `rtk`, a Rust-based CLI proxy that intercepts every command Claude executes and compresses its output before it reaches the context window. Reported reduction: ~150K tokens per session down to ~45K.

2. **Prompt-level output minimization (all platforms)** by instructing the AI to use quiet flags, suppress progress bars, and summarize long output rather than echoing it verbatim.

---

## Claude Code: rtk Proxy Setup

### Prerequisites

`rtk` requires Rust and Cargo. Install Rust if you do not already have it:

```bash
# Install Rust via rustup (https://rustup.rs)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# Restart your shell or run: source "$HOME/.cargo/env"
```

Verify installation:
```bash
cargo --version
```

### Install rtk

```bash
cargo install --git https://github.com/rtk-ai/rtk
```

This compiles and installs `rtk` into `~/.cargo/bin/`. Ensure that directory is on your PATH.

### Wire rtk into Claude Code

```bash
rtk init --global
```

This modifies `~/.claude/settings.json` to add a PreToolUse hook that routes all Bash commands through `rtk` before their output reaches the context window.

Verify the hook was added:
```bash
cat ~/.claude/settings.json | grep -A3 rtk
```

### Verify Savings

After one or more Claude Code sessions, run:

```bash
rtk gain
```

This reports total tokens saved across all intercepted sessions.

### Security Note

`rtk` installs from a raw GitHub repository and intercepts every command Claude Code executes. Before deploying in a team or production environment:
- Review the source code at the repository
- Inspect what `~/.claude/settings.json` looks like after `rtk init --global` to confirm the hook scope
- Consider whether command output contains sensitive data you do not want routed through a third-party proxy

### Uninstall

To remove rtk from Claude Code:
1. Edit `~/.claude/settings.json` and remove the hook entries referencing `rtk`
2. Run `cargo uninstall rtk` to remove the binary

---

## Claude Code: Manual Output Reduction

Even without rtk, you can significantly reduce context consumption by instructing Claude to run commands with quiet flags:

**Package managers:**
```bash
npm install --silent
pip install -q package-name
yarn --silent
```

**Test runners:**
```bash
pytest -q                    # suppress individual test lines
pytest --tb=short            # shorter tracebacks
go test ./... 2>/dev/null    # suppress build noise
```

**Build tools:**
```bash
make -s                      # silent make
gradle -q build              # quiet gradle
mvn -q install               # quiet maven
```

**General principle:** Redirect informational output to `/dev/null` when the exit code is the only information you need:
```bash
npm install > /dev/null 2>&1 && echo "Install succeeded"
```

---

## Gemini, Codex, and Copilot: Prompt-Level Output Minimization

These platforms do not have a hook system equivalent to Claude Code's, so output compression must be instructed at the prompt level. Add the following to your `GEMINI.md`, `AGENTS.md`, or `copilot-instructions.md`:

```markdown
## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log
```

These instructions reduce the amount of command output the AI includes in its responses and therefore in the conversation history, but they are advisory rather than enforced. The actual reduction depends on how well the model follows instructions.

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll deal with context limits when the session actually fills up" | By the time the window is full the early context is already evicted; configuring rtk or quiet flags up front is what prevents the truncation that loses earlier decisions. |
| "Dumping the full test log is fine, the model can read it" | A passing-test log of 500 lines costs thousands of tokens for zero signal; summarizing to counts plus failures leaves room for the actual debugging work. |
| "rtk is a Rust install, too much hassle for one session" | The one-time `rtk init --global` pays back as ~150K-to-45K reduction every session afterward; the hassle is amortized across the whole project, not one session. |
| "Advisory prompt instructions are enough, I don't need the proxy" | Prompt-level minimization depends on the model obeying; rtk enforces compression at the tool boundary regardless of how chatty the command is. |

## Verification

- [ ] For Claude Code: `rtk init --global` has run and `settings.json` contains the rtk hook
- [ ] For Claude Code: `rtk gain` reports non-zero savings after the first session
- [ ] For Gemini/Codex/Copilot: an Output Minimization section was added to the relevant instruction file
- [ ] Build, test, and package-manager commands use `--quiet`/`-q`/`--silent` where the tool supports it
- [ ] Long-running commands summarize counts and errors rather than dumping the full log

## Related Skills

- [[context-engineering]] -- shapes what belongs in context, complementing this skill's focus on shrinking what leaks in
- [[context-compression]] -- the orchestration-level techniques for minimizing tokens per task
- [[prompt-token-optimization]] -- reduces token consumption through programmatic tool calling and context hygiene
- [[using-nexus-hub]] -- orients a new session, a good point to apply these output-minimization defaults

---

*Version: 1.0.0 | Last Updated: 2026-03-06 | Author: Benjamin Dourthe*
