---
name: context-optimization
description: Optimize AI coding session context window usage by compressing command output, minimizing verbose logs, and avoiding context bloat. Use when sessions are hitting token limits, commands produce excessive output, you want to maximize effective session length, or you notice the context window filling up quickly. Covers the internal nexus-context-compressor engine for Claude Code and prompt-level output reduction for Gemini, Codex, and Copilot.
summary_l0: "Optimize AI session context windows by compressing output and reducing token bloat"
overview_l1: "This skill provides techniques for controlling context window consumption in AI coding sessions through automated output compression and prompt-level output minimization. Use it when a session consumes excessive tokens from command output, tests or builds dump full logs into context, you want to extend session length before hitting limits, you are configuring a new environment for context efficiency, or verbose output like progress bars fills the window. Key capabilities include automated compression via the internal nexus-context-compressor engine (a local-first, reversible PreToolUse compressor for Claude Code that Nexus-Hub owns and audits, replacing the external rtk binary), prompt-level minimization with quiet flags, progress bar suppression, long output summarization, and cross-platform strategies for Claude Code, Gemini, Codex, and Copilot. The expected output is a configured environment with reduced context consumption. Trigger phrases: context window, token limit, context bloat, compress output, reduce tokens, session length, verbose output, compressor setup, rtk migration, context optimization."
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

1. **Automated output compression (Claude Code only)** using `nexus-context-compressor`, Nexus-Hub's internal, local-first compression engine. A PreToolUse hook pipes a Bash command's output through the engine before it reaches the context window. The engine is owned and audited in-repo, pure Python (no Rust toolchain), makes zero new outbound calls, and is *reversible* (a dropped span is fetched back on demand). It is the programmatic counterpart to the orchestration-level methodology in [[context-compression]] and [[prompt-token-optimization]].

2. **Prompt-level output minimization (all platforms)** by instructing the AI to use quiet flags, suppress progress bars, and summarize long output rather than echoing it verbatim.

---

## Claude Code: nexus-context-compressor (internal engine)

Nexus-Hub ships its own context-compression engine, `nexus-context-compressor` (`extensions/nexus-context-compressor/`), an owned and audited replacement for the external `rtk` Rust binary this skill previously recommended. It is local-first, requires no Rust toolchain, makes zero new outbound calls, and makes compression *reversible*. The full setup, platform matrix, and architecture live in the guide [`RTK_CONTEXT_COMPRESSION.md`](../../../../guides/reference/RTK_CONTEXT_COMPRESSION.md); this section is the short version.

### Prerequisites

Python 3.10+ (which Nexus-Hub already requires) -- no Rust, no Cargo. The package ships with Nexus-Hub and is distributed by the installer. For accurate (rather than estimated) token metrics, install its default dependency once:

```bash
pip install -e "extensions/nexus-context-compressor"
```

The engine still runs without `tiktoken` (it falls back to a deterministic stdlib estimate), so this step is optional.

### Enable the compression hook (macOS / Linux)

The PreToolUse hook (`compress-output.sh`) is installed and registered in `settings.json` by Nexus-Hub. It is **opt-in and default-off** so it never rewrites a command unless you ask it to. Enable it by exporting an environment variable in your shell profile, then start a new session (hooks load at session start):

```bash
export NEXUS_CONTEXT_COMPRESS=1
```

From then on, each Bash command's stdout is piped through the engine before reaching the context window; the original exit status is preserved and stderr is untouched. Disable it for a single command with `NEXUS_CONTEXT_COMPRESS=0 <command>`.

On Windows, hooks need a Unix shell, so Claude Code uses CLAUDE.md-injected instructions instead (it pipes noisy structured output through `python -m nexus_context_compressor compress` explicitly) -- the same mechanism the old `rtk` integration used.

### What it compresses (and what it does not)

- **JSON arrays** (record dumps, `--json` output): deduplicated, keeping informative records and collapsing low-variance runs. This is where the largest savings come from.
- **Code**: function/method bodies are elided AST-aware, while imports, signatures, and structure are preserved.
- **Logs and free-form prose**: passed through unchanged. Free-text token dropping is an optional, default-off ML module; the engine deliberately does not guess at prose.

It reaches parity with `rtk` on *structured* command output today and is conservative (never expands, never loses output) on everything else.

### Reversibility (the key difference from rtk)

`rtk` compression was lossy. This engine is **non-lossy**: when a strategy drops a span it leaves a `<<ccr:HASH N_rows>>` marker and persists the originals in a local content-hashed SQLite store under `~/.nexus-hub/cache/`. An agent that needs the dropped data back resolves the marker:

```bash
python -m nexus_context_compressor retrieve "<<ccr:HASH N_rows>>"
```

It prints the exact dropped records (or a not-found note if the span was evicted). Compression never destroys information; it defers it.

### Migrating from rtk

If you previously ran `rtk init --global`:

1. **Remove the rtk hook.** On macOS/Linux, delete the `PreToolUse` entry referencing `rtk` from `~/.claude/settings.json`. On Windows, remove the `<!-- rtk-instructions -->...<!-- /rtk-instructions -->` block from `~/.claude/CLAUDE.md`.
2. **Uninstall the binary** (optional): `cargo uninstall rtk`.
3. **Enable the internal engine** with `export NEXUS_CONTEXT_COMPRESS=1` (or adopt the Windows CLAUDE.md instruction above).

Do not run both at once -- remove the rtk hook before enabling the internal one so output is not piped through two compressors.

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
| "I'll deal with context limits when the session actually fills up" | By the time the window is full the early context is already evicted; enabling the compression hook or quiet flags up front is what prevents the truncation that loses earlier decisions. |
| "Dumping the full test log is fine, the model can read it" | A passing-test log of 500 lines costs thousands of tokens for zero signal; summarizing to counts plus failures leaves room for the actual debugging work. |
| "The compression engine is one more thing to install, too much hassle for one session" | It ships with Nexus-Hub -- no Rust, no `cargo install`, just `export NEXUS_CONTEXT_COMPRESS=1` once. The payoff is per-session and the engine is reversible (a `<<ccr:...>>` marker resolves back to the originals), so enabling it cannot lose output. |
| "Advisory prompt instructions are enough, I don't need the engine" | Prompt-level minimization depends on the model obeying; the PreToolUse hook enforces compression at the tool boundary regardless of how chatty the command is, and unlike the old rtk proxy it never loses the dropped data. |

## Verification

- [ ] For Claude Code: `NEXUS_CONTEXT_COMPRESS=1` is exported and `settings.json` contains the `compress-output.sh` PreToolUse hook
- [ ] For Claude Code: a command emitting a large JSON array returns a few representative records plus a `<<ccr:...>>` marker, and `python -m nexus_context_compressor retrieve "<<ccr:...>>"` resolves it back to the exact originals
- [ ] For Gemini/Codex/Copilot: an Output Minimization section was added to the relevant instruction file
- [ ] Build, test, and package-manager commands use `--quiet`/`-q`/`--silent` where the tool supports it
- [ ] Long-running commands summarize counts and errors rather than dumping the full log

## Related Skills

- [[context-engineering]] -- shapes what belongs in context, complementing this skill's focus on shrinking what leaks in
- [[context-compression]] -- the orchestration-level techniques for minimizing tokens per task
- [[prompt-token-optimization]] -- reduces token consumption through programmatic tool calling, the functions-over-data principle (compute over large structured context instead of reading it token by token), and context hygiene
- [[using-nexus-hub]] -- orients a new session, a good point to apply these output-minimization defaults
- **`nexus-context-compressor` engine** (`extensions/nexus-context-compressor/`) -- the programmatic compressor this skill configures; the deterministic strategies and reversible CCR store the prose above describes. Full setup, platform matrix, and architecture: [`guides/reference/RTK_CONTEXT_COMPRESSION.md`](../../../../guides/reference/RTK_CONTEXT_COMPRESSION.md) and the [engine README](../../../../extensions/nexus-context-compressor/README.md).

---

*Version: 1.0.0 | Last Updated: 2026-03-06 | Author: Benjamin Dourthe*
