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

## Forcing and Install Output

Naming a platform explicitly (`--platforms <key>` or `-Platforms <key>`) makes both installers pass `--forced <key>` to `runner.py install` on its global call. The runner sets `InstallContext.forced_keys` (only keys in the same run count) and, when the forced platform installs, records it in the manifest's `forced` map, so later default installs keep it and the stale-surface report never offers its files for removal. Forcing applies to the seven platforms gated by this rule; OpenClaw, Devin Desktop / Windsurf, and Copilot keep their own vendor-root checks.

For a not-detected platform the runner's install summary carries `evidence` and a one-line `remedy` ("Install <tool>, then run `nexus-hub upgrade`, or name it with --platforms <key>."). The bash installer (`render_platform_from_summary`) and the PowerShell installer (`Resolve-UndetectedReason`) print both under NOT DETECTED; `tests/installer/test_detection_messages.py` pins that they print identical lines.

## Stale Surfaces and Removal

A platform is **stale** when it declares a detection spec, is not detected, was not forced, its home folder is not redirected, and the install manifest still lists entries for it. `nexus-hub doctor` lists stale platforms (text output) and the install summary appends a pointer to the one-line remedy. `nexus-hub prune-undetected` previews; `--yes` removes; `--unforce <keys>` first clears an explicit `--platforms` choice; `--integrations <keys>` narrows the run.

The engine is `scripts/lib/integrations/_stale.py`. It never calls `shutil.rmtree`, takes the allowed folders from the integration's spec (never from the manifest), re-runs detection immediately before removing, and re-checks each file's size and modification time immediately before unlinking it.

| Entry | Verdict |
|---|---|
| Tracked file with a recorded hash | Removed only when the current hash matches; otherwise kept ("you changed it after install") |
| File inside a tracked folder (no per-file hash is recorded) | Removed only when not modified after the folder was recorded (two-second slack); files changed or added later are kept |
| Shared instruction file | Only the Nexus-Hub marker block is removed |
| Declared merged settings (`shared_configs` with a pruner: Kimi `config.toml`, Qwen `settings.json`) | Only Nexus-Hub's hook entries are removed; the user's settings stay |
| Declared seeded settings (`shared_configs` without a pruner: Hermes `config.yaml`, Pi `settings.json`, `~/.aider.conf.yml`) | Kept, reported |
| `*.nexus-hub.bak`, links (symlink, junction, hard link), unreadable folders, paths outside the platform's folder | Kept, reported |
| Folder left empty | Removed bottom-up with `rmdir` |

Removed paths are untracked and their action records dropped; records for kept files remain.

### Obsolete Layouts

The same command evaluates two home-folder layouts no installer writes any more: `~/.agent` (Antigravity 1.0, until v2.3.0) and the home-root `~/.opencode` (OpenCode's global folder until v3.14.5). `scripts/lib/integrations/legacy.py` classifies each tree against `scripts/lib/installer/legacy_layout_fingerprints.json`, which `scripts/build_legacy_layout_fingerprints.py` builds from git history (verbatim catalog copies in LF and CRLF form, flattened skill paths, and command-skills reproduced with that period's own generator); a rendered `AGENTS.md` is recognized line by line against `legacy_fingerprints.json`. A tree is removed only when every entry is recognized; an edited file, a foreign folder (for example OpenCode's own `node_modules/`), an empty or unreadable entry, or a link keeps the whole tree, and `doctor` names up to ten unrecognized entries. Removal re-checks each file right before unlinking it, stops on a change, and removes folders with `rmdir` only. Nothing is evaluated when the fingerprint set is missing.

## Consumers

| Consumer | Use |
|---|---|
| Global install (`IntegrationBase` subclasses) | Skip every write, including defaults seeding, when not detected |
| `nexus-hub verify` (`runner._verify_checks`) | Rows carrying an `integration` key in `docs/policy/platform-read-contracts.json` use this rule, so verify never contradicts the installer |
| Install manifest | A not-detected install keeps the platform's previous action record, so its per-file hashes survive for the stale-surface report |
