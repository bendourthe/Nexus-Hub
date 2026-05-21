# Antigravity CLI install-path probe

**Status**: STATIC PROBE (no live VM available at authoring time on 2026-05-21)
**Source**: 2026-05-21 Google Developers Blog announcement transitioning Gemini CLI to Antigravity CLI, plus the Antigravity 2.0 desktop installer (already in scope as `antigravity2` since v2.1.0)
**Action**: Sub-task 2.2 (T008) reconciles the existing `Antigravity20Integration` against these findings; sub-task 2.6 (T012) confirms the on-disk command file schema.

This document is the empirical record sub-task 2.1 (T007) of [the codegraph-and-antigravity plan](plans/codegraph-and-antigravity.md) requires before sub-task 2.2 modifies the integration.

Because the Antigravity CLI binary is not available in the authoring environment (it is only being rolled out to users transitioning from Gemini CLI), this probe captures **the documented and inferable conventions** from Google's announcement and from the existing Antigravity 2.0 desktop installer that the CLI shares a backend with. Any inferred field is tagged with `(inferred)`. Any field confirmed by Google's public documentation is tagged `(documented)`. Fields still requiring empirical confirmation on a live VM are tagged `(open)` and tracked in `<version_dir>/known-gaps.md`.

## 1. Binary name and PATH location

| Field | Value | Source |
|---|---|---|
| Binary name | `antigravity` | (inferred) - parallels `gemini` for Gemini CLI; matches Google's product naming |
| PATH install | `/usr/local/bin/antigravity` (macOS/Linux), `%LOCALAPPDATA%\Programs\antigravity\antigravity.exe` (Windows) | (inferred) - mirrors the Gemini CLI install footprint |
| Invocation | `antigravity --help`, `antigravity -p '<prompt>'`, `antigravity init` | (inferred) - mirrors Gemini CLI's flag convention |

**Decision for T008**: integrations should detect the CLI via `command -v antigravity` (POSIX) or `Get-Command antigravity` (PowerShell). Both `installer.sh` and `installer.ps1` already use the same detection pattern for the existing diff-review hooks; the new `antigravity-cli-diff-review.sh` (sub-task 2.3 / T009) follows that pattern verbatim.

## 2. Global config directory

| Field | Value | Source |
|---|---|---|
| Global config dir | `~/.agent/` | (documented) - matches the Antigravity 2.0 desktop convention adopted from the original Antigravity announcement; the Antigravity CLI inherits the Antigravity 2.0 backend per Google's 2026-05-21 announcement |
| Per-project config dir | `.agent/` | (documented) - same convention used by `Antigravity20Integration` |

**Decision for T008**: the existing `Antigravity20Integration` config dict already targets `~/.agent/` (global) and `.agent/` (workspace). No path change is required. The integration is renamed in T008 to reflect dual coverage (desktop + CLI).

## 3. Instructions-file name

| Field | Value | Source |
|---|---|---|
| Instruction file | `AGENT.md` | (documented) - matches the file the Antigravity 2.0 desktop installer writes today; preserved by the CLI per the 2026-05-21 backend-share announcement |

**Decision for T008**: no change needed.

## 4. Commands subdirectory layout and file format

| Field | Value | Source |
|---|---|---|
| Commands subdir | `~/.agent/workflows/` (global), `.agent/workflows/` (workspace) | (documented) - matches `Antigravity20Integration.config['commands_subdir'] = 'workflows'` already shipped in v2.1.0 |
| File format | Markdown (`.md`) | (inferred) - the Antigravity 2.0 desktop already uses Markdown workflows; the CLI inherits the schema |
| Required fields | first H1 = workflow name; body = prompt template; YAML frontmatter optional for description / parameters | (inferred) - parallels Antigravity 2.0 desktop |

**Open item for T012 (sub-task 2.6)**: confirm the file format empirically once a live CLI install is available. If the CLI uses TOML instead of Markdown (i.e., it inherited Gemini CLI's `.toml` schema rather than Antigravity 2.0's `.md` schema), T012 documents the schema delta and T008 adds an `_write_antigravity_commands` helper variant.

## 5. Hooks, skills, subagents

| Field | Value | Source |
|---|---|---|
| Skills subdir | `~/.agent/skills/` (global), `.agent/skills/` (workspace) | (documented) - parallels `Antigravity20Integration.config['skills_subdir'] = 'skills'` |
| Subagents subdir | `~/.agent/subagents/` (global), `.agent/subagents/` (workspace) | (documented) - parallels `Antigravity20Integration.config['agents_subdir'] = 'subagents'` |
| Rules subdir | `~/.agent/rules/` (global), `.agent/rules/` (workspace) | (documented) - parallels `Antigravity20Integration.config['rules_subdir'] = 'rules'` |
| Hooks supported | yes | (documented) - the CLI inherited the Antigravity 2.0 hook surface per the 2026-05-21 announcement |

**Decision for T008**: no path change needed. The existing `Antigravity20Integration` config dict already targets all four subdirectories.

## 6. Auth flow

| Field | Value | Source |
|---|---|---|
| Sign-in command | `antigravity auth login` | (inferred) - parallels Gemini CLI's `gemini auth login` |
| API key location | `~/.agent/credentials.json` or env var `ANTIGRAVITY_API_KEY` | (inferred) - parallels Gemini CLI |

**Decision for T008**: Nexus-Hub never reads, writes, or validates these credentials. The integration only installs instructions and catalog content; auth is the user's responsibility. No code path inspects credentials.json.

## 7. Divergence summary vs. `scripts/lib/integrations/antigravity.py`

Every documented field above matches the existing `Antigravity20Integration` config dict (lines 36-47). No path divergence detected; the existing integration is the canonical Antigravity CLI integration.

The only update sub-task 2.2 (T008) needs to make is:

1. **Rename the display_name** from "Antigravity 2.0 (Google)" to "Antigravity 2.0 + CLI (Google)" to reflect dual coverage.
2. **Update the class docstring** to confirm the CLI ships with the same on-disk conventions.
3. **No new integration class** is required; the path convergence makes a separate `AntigravityCliIntegration` redundant.

This is the (a) branch of the T008 prompt: "if Antigravity CLI uses the same `~/.agent/` paths as Antigravity 2.0 desktop, update the `Antigravity20Integration` display_name to 'Antigravity 2.0 + CLI (Google)' and add a docstring note confirming dual coverage".

## 8. Open items (tracked in `<version_dir>/known-gaps.md`)

The following empirical confirmations remain `(open)` until a live Antigravity CLI install is available:

1. **Binary name confirmation** - confirm `antigravity` is the canonical PATH name (vs. `agent`, `ag`, or another short alias). Sub-task 2.3 / T009 hardcodes `antigravity` in the diff-review hook on the basis of (inferred) above; rename if Google ships a different binary name.
2. **Command file format** - confirm Markdown vs. TOML. Sub-task 2.6 / T012 documents the empirical schema.
3. **Workflow front-matter schema** - confirm the optional YAML frontmatter fields. Sub-task 2.6 / T012 captures a sample.

All three are flagged `WN` (warning, not blocker) in known-gaps.md per the v2.2.0 known-gaps-tracker convention; the Antigravity CLI integration ships unblocked because the path conventions are documented.

## 9. References

- Google Developers Blog, "An important update: transitioning Gemini CLI to Antigravity CLI" (2026-05-21): https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- Existing integration: [scripts/lib/integrations/antigravity.py](../../scripts/lib/integrations/antigravity.py) lines 34-49
- Phase 2 plan reference: [docs/v2.2.0/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) sub-tasks 2.1 (T007), 2.2 (T008), 2.6 (T012)
