# Platform Detection

Summary: the rule the installer, `nexus-hub verify`, and `nexus-hub doctor` use to decide whether a detection-gated AI tool is installed, judged only by evidence Nexus-Hub did not create.
Read this when: adding or changing a platform integration, investigating why a platform was skipped or written, or reviewing the stale-surface report.
Covers: the four evidence kinds, the `--platforms` override, entry classification, the per-integration `detection` spec, evidence strings, and which platforms are gated.

## Rule

A gated platform is **detected** when any of these holds, checked in order:

1. **Forced.** The user named it with `--platforms <key>` on this install or an earlier one. The choice is recorded in the install manifest and kept on later installs.
2. **Root evidence.** The platform's home root (for example `~/.kimi-code`) is a real folder holding at least one top-level entry Nexus-Hub did not write, or one of its vendor-only folders (for example OpenCode's `~/.local/share/opencode`) holds anything outside the names Nexus-Hub is known to write there.
3. **Executable.** One of its commands resolves on `PATH`. Relative and empty `PATH` entries are skipped, the current directory is never searched, and under WSL a hit below `/mnt/<drive>/` is ignored because that Windows install never reads the Linux home. A collision-prone name (Hermes) counts only when the resolved path sits in the tool's own install location.
4. **Application.** One of its declared per-OS installed-application paths exists (Nexus AI Studio, the Windows Hermes install).

Otherwise the platform is **not detected**, and its global install writes nothing.

A folder holding only Nexus-Hub files is not evidence. Before v4.14.7 the folder itself was the test, so one earlier Nexus-Hub write made every later install count the tool as present; the decision record is `docs/decisions/proposed/policy/2026-10-29-platform-detection-evidence-rule.md`.

## Entry Classification

Each top-level entry of a home root is one of:

| Class | Members | Effect |
|---|---|---|
| Nexus-Hub's | Names in the spec's `nexus_entries`; any path the manifest tracks for the platform (regular, shared, organization, or action record) at or below the entry | Not evidence |
| Ignored | OS metadata (`desktop.ini`, `.DS_Store`, `Thumbs.db`, `._*`, `$RECYCLE.BIN`); `*.nexus-hub.tmp`; `*.nexus-hub.bak` | Neither evidence nor Nexus-Hub's |
| Vendor | Everything else | Evidence |

A `*.nexus-hub.bak` backup is neutral rather than evidence because the merge helpers write one whenever the config already existed, including a config Nexus-Hub seeded moments earlier. A config Nexus-Hub merged into is tracked, so it is never evidence either way.

Path comparison is normalized: long-path prefixes are stripped and case and separators follow the OS, so a manifest written with a different spelling of the same home still matches.

A redirected root (symlink or junction, as dotfiles managers create) is never read through. It is reported as "redirected folder (not evaluated)" and detection falls through to `PATH`.

## The `detection` Spec

Each gated integration declares its signals once, in its class-level `config` dict, and every consumer reads the same declaration:

```python
"detection": {
    "executables": ["kimi"],
    "corroborate": {"hermes": ["hermes-agent", "/hermes/bin"]},
    "root": ".kimi-code",
    "nexus_entries": ["AGENTS.md", "skills", "agents", "hooks", "config.toml"],
    "vendor_roots": {".local/share/opencode": []},
    "app_paths": {"win32": ["%LOCALAPPDATA%/Nexus AI Studio"]},
}
```

All keys are optional. `root` and `vendor_roots` are relative to the home folder (or the explicit `--target` for a global install). An `app_paths` template with an undefined variable is skipped rather than guessed. Per-tool values and their first-party sources: `docs/releases/v4/v4.14/development/v4.14.7-detection-signals.md`.

`scripts/lib/integrations/_detection.py` evaluates the spec. It never writes to disk, never creates the root it inspects, and never runs, sources, or version-probes a resolved executable.

## Gated Platforms

| Gated by this rule | Gated by their own vendor-root check | Not gated (`detected=None`) |
|---|---|---|
| Kimi Code CLI, Qwen Code, Hermes, Pi, Aider, OpenCode, Nexus AI Studio | OpenClaw, Devin Desktop / Windsurf, GitHub Copilot | Claude Code, Codex, Cursor, Gemini, Antigravity, Gemini CLI |

Workspace-scope installs are not gated: a workspace install is an explicit request for that folder.

## Evidence Strings

Every verdict carries a one-line reason that the install summary and `doctor` show, for example:

- `kimi found at C:\Users\me\AppData\Roaming\npm\kimi.CMD`
- `~/.kimi-code holds sessions`
- `named with --platforms qwen`
- `qwen not on PATH; ~/.qwen holds only Nexus-Hub files`
- `hermes not on PATH; ~/.hermes is a redirected folder (not evaluated)`

## Consumers

| Consumer | Use |
|---|---|
| Global install (`IntegrationBase` subclasses) | Skip every write, including defaults seeding, when not detected |
| `nexus-hub verify` (`runner._verify_checks`) | Rows carrying an `integration` key in `docs/policy/platform-read-contracts.json` use this rule, so verify never contradicts the installer |
| Install manifest | A not-detected install keeps the platform's previous action record, so its per-file hashes survive for the stale-surface report |
