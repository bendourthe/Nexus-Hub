# Context Window Compression for Claude Code

> **What changed (v3.2.0):** Nexus-Hub now ships its own context-compression engine, `nexus-context-compressor`, an owned and audited replacement for the external `rtk` Rust binary this guide previously recommended. The internal engine is local-first, requires no Rust toolchain, makes zero new outbound calls, and makes compression *reversible* (a dropped span can be fetched back). If you wired up `rtk` previously, see [Migrating from rtk](#migrating-from-rtk) below.

## What Is nexus-context-compressor?

`nexus-context-compressor` is a local-first compression engine that lives inside Nexus-Hub (`extensions/nexus-context-compressor/`). Wired into Claude Code via a PreToolUse hook, it compresses a Bash command's output before that output is written into the context window.

It is deterministic and self-contained: standard-library compression strategies, a single optional dependency (`tiktoken`, for token accounting, with an offline fallback), zero outbound calls, no bundled LLM client, and no API key.

**Why it exists:** the prior recommendation, `rtk`, was an external Rust binary installed via `cargo install --git` from a raw GitHub repository. That is a "trust an unaudited third-party binary that sees every command's output" posture. The internal engine eliminates that trust surface: Nexus-Hub owns and audits the code, it is pure Python, and it adds no new data flow.

## What It Compresses

The engine routes each blob of output to the strategy that fits, and is honest about what it does and does not touch:

- **JSON arrays** (record dumps, `--json` command output): deduplicated, keeping the informative records and collapsing low-variance runs. This is where the largest savings come from.
- **Code**: function and method bodies are elided while imports, signatures, and structure are preserved (AST-aware).
- **Logs and free-form prose**: passed through unchanged in v3.2.0. Free-text token dropping is an optional, default-off ML module arriving in a later phase. The engine deliberately does not guess at prose.

Because of this, the engine reaches parity with `rtk` on *structured* command output today, and is conservative (never expands, never loses output) on everything else. A command whose output is mostly free-text logs will see little change until the optional ML module ships.

## Reversibility (the key difference from rtk)

`rtk` compression was lossy: dropped output was gone. This engine is **non-lossy**. When a strategy drops a span of records it leaves a marker like `<<ccr:HASH N_rows>>` and persists the originals in a local content-hashed SQLite store (under `~/.nexus-hub/cache/`). An agent that needs the dropped data back calls the `context_retrieve` MCP tool (or `python -m nexus_context_compressor retrieve "<<ccr:...>>"`) and gets the exact original records. Compression never destroys information; it defers it.

## Platform Support

| Platform | OS | Supported | Method |
|----------|----|-----------|--------|
| Claude Code | macOS / Linux | Yes | PreToolUse hook (`compress-output.sh`) - transparent interception of Bash output |
| Claude Code | Windows | Yes | Instructions injected into `CLAUDE.md` - Claude pipes noisy output through the CLI |
| Gemini | Any | No | Use prompt-level output minimization (see below) |
| Codex | Any | No | Use prompt-level output minimization (see below) |
| Copilot | Any | No | Use prompt-level output minimization (see below) |

The engine works on all operating systems for Claude Code, but uses different integration mechanisms by platform (hooks need a Unix shell; Windows uses CLAUDE.md-injected instructions). For Gemini, Codex, and Copilot, see [Output Minimization for Other Platforms](#output-minimization-for-other-platforms).

## Prerequisites

Python 3.10+ (which Nexus-Hub already requires). No Rust, no Cargo. The package ships with Nexus-Hub and is distributed by the installer.

For accurate (rather than estimated) token metrics, install the package with its default dependency:

```bash
pip install -e "extensions/nexus-context-compressor"
```

The engine still runs without `tiktoken` (it falls back to a deterministic stdlib token estimate), so this step is optional.

## Wiring Into Claude Code (macOS / Linux)

The compression hook (`compress-output.sh`) is installed by Nexus-Hub into your hooks directory and registered in `settings.json`. It is **opt-in and default-off** so it never rewrites a command unless you ask it to. Enable it by exporting an environment variable in your shell profile:

```bash
export NEXUS_CONTEXT_COMPRESS=1
```

Start a new Claude Code session (hooks load at session start). From then on, each Bash command's stdout is piped through the engine before reaching the context window; the original exit status is preserved and stderr is left untouched. Disable it for a single command with:

```bash
NEXUS_CONTEXT_COMPRESS=0 <command>
```

## Wiring Into Claude Code (Windows)

Hooks require a Unix shell, so on Windows Claude Code uses CLAUDE.md-injected instructions instead (the same mechanism the old `rtk` integration used). The instructions tell Claude to pipe noisy *structured* command output through the engine explicitly, for example:

```powershell
gh issue list --json number,title,state | python -m nexus_context_compressor compress
```

The CLI reads the command's output on stdin and writes the compressed text to stdout; compression metrics go to stderr.

## Verifying It Works

Run a command that emits a large JSON array (for example a `--json` listing or a row dump) inside a session with the hook enabled. The output that reaches the context window should be a handful of representative records plus a `<<ccr:...>>` marker. To confirm reversibility, resolve a marker:

```bash
python -m nexus_context_compressor retrieve "<<ccr:HASH N_rows>>"
```

It prints the exact dropped records as JSON (or a not-found note if the span was evicted).

## Security and Trust Considerations

This is a strict improvement over the external-binary posture:

- **Owned and audited.** The compression code is part of Nexus-Hub, reviewed in-repo, not pulled from a raw GitHub URL at install time.
- **Local-first, zero new outbound.** Deterministic strategies are pure standard library; payloads are compressed in process; the CCR store is a local SQLite file. No command output is routed through any third party.
- **Sensitive output still passes through the engine in-process.** As with any output filter, if your commands emit secrets, that text is processed locally by the engine. Nothing leaves the machine, but the data is read in process; keep the hook disabled for commands you do not want filtered at all.

## Migrating from rtk

If you previously ran `rtk init --global`:

1. **Remove the rtk hook.** On macOS/Linux, edit `~/.claude/settings.json` and delete the `PreToolUse` entry that references the `rtk` command. On Windows, remove the `<!-- rtk-instructions -->...<!-- /rtk-instructions -->` block from `~/.claude/CLAUDE.md`.
2. **Uninstall the binary** (optional): `cargo uninstall rtk`.
3. **Enable the internal engine** with `export NEXUS_CONTEXT_COMPRESS=1` (macOS/Linux) or by adopting the Windows CLAUDE.md instruction above.

The internal hook and `rtk` should not run at the same time; remove the rtk hook before enabling the internal one so output is not piped through two compressors.

## Output Minimization for Other Platforms

Gemini, Codex, and Copilot do not support hook-based command interception. The equivalent approach is to add output-minimization instructions to your AI instruction file.

Add the following section to your `GEMINI.md`, `AGENTS.md`, or `.github/copilot-instructions.md`:

```markdown
## Output Minimization
- Suppress verbose progress bars, banners, and informational logs from commands unless they indicate an error
- Prefer `--quiet`, `--silent`, or `-q` flags when running package managers, build tools, and test runners
- Summarize long command output rather than echoing it in full; report only counts, errors, and key results
- When a command produces more than ~20 lines of output, summarize what happened rather than quoting the full log
```

The Nexus-Hub installer automatically includes this section in all generated `GEMINI.md`, `AGENTS.md`, and Copilot instruction files when you run the installer.

## Related Resources

- [context-optimization skill](../../catalog/skills/developer-experience/context-optimization/SKILL.md) - AI-assisted guidance for applying these optimizations to a project
- [nexus-context-compressor README](../../extensions/nexus-context-compressor/README.md) - the engine's architecture, strategies, and reversible CCR store
- [CLAUDE_CODE_SETTINGS_REFERENCE.md](CLAUDE_CODE_SETTINGS_REFERENCE.md) - full reference for Claude Code settings.json and hooks
- [CLAUDE_CODE_GUIDE.md](CLAUDE_CODE_GUIDE.md) - general Claude Code setup and usage guide
