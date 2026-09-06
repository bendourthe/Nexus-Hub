# Antigravity CLI install-path probe

**Status**: STATIC PROBE (2026-05-21) + DOCS-VERIFIED UPDATE (2026-05-29). See Section 11 for the v2.3.0 Phase 9 verification against Google's now-public Antigravity CLI documentation.
**Source**: 2026-05-21 Google Developers Blog announcement transitioning Gemini CLI to Antigravity CLI, plus the Antigravity 2.0 desktop installer (already in scope as `antigravity2` since v2.1.0). Updated 2026-05-29 with Google's public Antigravity CLI docs + codelabs.
**Action**: Sub-task 2.2 (T008) reconciles the existing `Antigravity20Integration` against these findings; sub-task 2.6 (T012) confirms the on-disk command file schema. v2.3.0 Phase 9 (T032/T033/T034) re-verifies the `(inferred)` / `(open)` fields below against public docs.

> **2026-05-29 correction summary (v2.3.0 Phase 9, WN-2/WN-3/WN-4)**: The binary name is **`agy`** (installed to `~/.local/bin/agy`), NOT the inferred `antigravity`. The per-project dir is **`.agents/`** (plural) with **`AGENTS.md`** as the project-root instruction file; workflows/skills are **Markdown** under `.agents/workflows/` and `.agents/skills/` (WN-3 confirmed). The global CLI footprint is under **`~/.gemini/antigravity-cli/`**, not the inferred `~/.agent/`. These corrections are applied to `scripts/lib/integrations/antigravity.py`, both installers, the diff-review hooks, and the base templates. Full detail, sources, and the residual live-VM items are in **Section 11** below; do not treat Sections 1/4/6 as canonical where they conflict with Section 11.

This document is the empirical record sub-task 2.1 (T007) of [the codegraph-and-antigravity plan](plans/codegraph-and-antigravity.md) requires before sub-task 2.2 modifies the integration.

Because the Antigravity CLI binary is not available in the authoring environment (it is only being rolled out to users transitioning from Gemini CLI), this probe captures **the documented and inferable conventions** from Google's announcement and from the existing Antigravity 2.0 desktop installer that the CLI shares a backend with. Any inferred field is tagged with `(inferred)`. Any field confirmed by Google's public documentation is tagged `(documented)`. Fields still requiring empirical confirmation on a live VM are tagged `(open)` and tracked in `<version_dir>/known-gaps.md`.

**Update 2026-05-26**: four backend-runtime fields (default model, application data directory, MCP transport, default tool-call policy) are pinned to `(documented, SDK v0.1.1)` in the new Section 7 below, using the Antigravity SDK as the authoritative source for the shared Antigravity backend. See [docs/archives/v2/v2.2/plans/adoption-antigravity-sdk-python.md](plans/adoption-antigravity-sdk-python.md) sub-task 1.4 for the source citations. These four fields were not previously present in this probe (the probe's existing `(inferred)` fields are the binary name, command file format, and auth flow, which the SDK cannot pin and which remain tracked as WN-2 / WN-3 / WN-4); they are added rather than replaced. The binary-name and auth fields stay `(inferred)` / `(open)` pending a live-VM probe.

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

## 7. Backend-runtime details pinned from the Antigravity SDK (documented, v0.1.1)

The Antigravity SDK is the official client for the same Antigravity backend the CLI targets, so its documented runtime defaults are authoritative for the backend the CLI shares. The four fields below are pinned `(documented, SDK v0.1.1)` and de-risk Phase 2 sub-tasks T007 / T008 / T012 of [the codegraph-and-antigravity plan](plans/codegraph-and-antigravity.md). Citations point at the new `google-antigravity-sdk` skill's reference docs (the canonical in-repo record of these facts).

| Field | Value | Source |
|---|---|---|
| Default model | `gemini-3.5-flash` | (documented, SDK v0.1.1) - [google-antigravity-sdk references/agent_configuration.md](../../catalog/skills/ai-development/google-antigravity-sdk/references/agent_configuration.md) "Default model" section: the SDK's default model is `gemini-3.5-flash` |
| Application data directory | `~/.gemini/antigravity/brain/` | (documented, SDK v0.1.1) - [google-antigravity-sdk references/agent_configuration.md](../../catalog/skills/ai-development/google-antigravity-sdk/references/agent_configuration.md) "Application Data Directory Override" section |
| MCP transport | stdio + SSE | (documented, SDK v0.1.1) - [google-antigravity-sdk references/mcp_integration.md](../../catalog/skills/ai-development/google-antigravity-sdk/references/mcp_integration.md): both the stdio (`McpStdioServer`) and SSE transports are supported |
| Default tool-call policy | `confirm_run_command()` (denies `run_command`, allows other tools) | (documented, SDK v0.1.1) - [google-antigravity-sdk references/safety_policies.md](../../catalog/skills/ai-development/google-antigravity-sdk/references/safety_policies.md) "Default Behavior" section |

**Note on scope**: the application data directory (`~/.gemini/antigravity/brain/`) is the agent's working-artifact directory and is distinct from the CLI's config directory (`~/.agent/`, Section 2). Both are correct; they serve different purposes. The default model and default policy describe backend behavior the CLI inherits; they do not change any path in `scripts/lib/integrations/antigravity.py`.

## 8. Divergence summary vs. `scripts/lib/integrations/antigravity.py`

Every documented field above matches the existing `Antigravity20Integration` config dict (lines 36-47). No path divergence detected; the existing integration is the canonical Antigravity CLI integration.

The only update sub-task 2.2 (T008) needs to make is:

1. **Rename the display_name** from "Antigravity 2.0 (Google)" to "Antigravity 2.0 + CLI (Google)" to reflect dual coverage.
2. **Update the class docstring** to confirm the CLI ships with the same on-disk conventions.
3. **No new integration class** is required; the path convergence makes a separate `AntigravityCliIntegration` redundant.

This is the (a) branch of the T008 prompt: "if Antigravity CLI uses the same `~/.agent/` paths as Antigravity 2.0 desktop, update the `Antigravity20Integration` display_name to 'Antigravity 2.0 + CLI (Google)' and add a docstring note confirming dual coverage".

## 9. Open items (tracked in `<version_dir>/known-gaps.md`)

> **Updated 2026-05-29 (v2.3.0 Phase 9)**: items 1-3 below were RESOLVED via Google's public Antigravity CLI documentation (see Section 11). The binary name was corrected (`antigravity` -> `agy`), the command file format was confirmed (Markdown), and the front-matter behavior was documented. A live-VM smoke is still pending for the residual items listed in Section 11.4.

The following empirical confirmations were `(open)` until the Antigravity CLI documentation became public:

1. **Binary name confirmation** - ~~confirm `antigravity` is the canonical PATH name~~ RESOLVED 2026-05-29: the binary is **`agy`** (Section 11.1). Sub-task 2.3 / T009 originally hardcoded `antigravity`; the diff-review hooks now call `agy`.
2. **Command file format** - ~~confirm Markdown vs. TOML~~ RESOLVED 2026-05-29: **Markdown** under `.agents/workflows/` (Section 11.2), confirming the inferred value.
3. **Workflow front-matter schema** - ~~confirm the optional YAML frontmatter fields~~ RESOLVED 2026-05-29: YAML frontmatter is honored and the workflow name derives from the filename (Section 11.3).

These were flagged `WN` (warning, not blocker) in known-gaps.md; the integration shipped unblocked. The v2.3.0 corrections close WN-2/WN-3/WN-4 via documentation; a fresh `WN` records the residual live-VM items (Section 11.4).

## 10. References

- Google Developers Blog, "An important update: transitioning Gemini CLI to Antigravity CLI" (2026-05-21): https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/
- Existing integration: [scripts/lib/integrations/antigravity.py](../../scripts/lib/integrations/antigravity.py)
- Phase 2 plan reference: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) sub-tasks 2.1 (T007), 2.2 (T008), 2.6 (T012)
- v2.3.0 Phase 9 plan reference: [docs/archives/v2/v2.3/plans/adoption-ecc-cybersec-skills.md](../v2.3.0/plans/adoption-ecc-cybersec-skills.md) sub-tasks T032 (WN-2), T033 (WN-3), T034 (WN-4)

## 11. v2.3.0 Phase 9 verification against public Antigravity CLI docs (2026-05-29)

**Method**: The v2.2.0 probe inferred several fields by analogy to Gemini CLI because the Antigravity CLI binary was not yet on a verifiable channel. By 2026-05-29 (cutover is 2026-06-18), Google's Antigravity CLI documentation and codelabs are public, so WN-2/WN-3/WN-4 were verified against those primary sources rather than a live install. A live-install (`agy`) smoke was NOT run -- no `agy` binary is installed on the Windows authoring host -- so the confirmations below are tagged `(docs-verified)`, and a residual live-VM item is recorded in 11.4.

### 11.1 Binary name (WN-2) -- CORRECTED

| Field | v2.2.0 inferred | 2026-05-29 verified | Source |
|---|---|---|---|
| Binary name | `antigravity` | **`agy`** | `(docs-verified)` -- official docs page titled "Using AGY CLI" (`antigravity.google/docs/cli-using`); corroborated by multiple practitioner guides ("the binary drops into `~/.local/bin/` as `agy`") |
| PATH install | `/usr/local/bin/antigravity`, `%LOCALAPPDATA%\...\antigravity.exe` | **`~/.local/bin/agy`** | `(docs-verified)` -- practitioner install guides |
| Invocation | `antigravity -p '<prompt>'` | **`agy -p '<prompt>'`** | `(docs-verified)` |

**Applied**: `catalog/hooks/antigravity-cli-diff-review.sh`/`.ps1` now call `agy` (the binary detection and invocation); `base-antigravity-20.md` / `base-antigravity-cli.md` and the `Antigravity20Integration` docstring updated. The hook filename keeps the product name (`antigravity-cli-diff-review`), consistent with its siblings and its registration in both installers.

### 11.2 Workflow / command file format (WN-3) -- CONFIRMED (inferred value was correct)

| Field | v2.2.0 inferred | 2026-05-29 verified | Source |
|---|---|---|---|
| Per-project dir | `.agent/` (singular) | **`.agents/`** (plural) | `(docs-verified)` -- official Google codelab: `.agents/skills/`, `.agents/workflows/` |
| Workflow format | Markdown `.md` | **Markdown `.md`** | `(docs-verified)` -- codelab `.agents/workflows/startcycle.md` |
| Global dir | `~/.agent/` | **`~/.gemini/antigravity-cli/`** | `(docs-verified)` -- Google Cloud Community config guide; consistent with the SDK-pinned `~/.gemini/antigravity/brain/` (Section 7) |

**Applied**: `Antigravity20Integration` config -> `workspace_dir=.agents`, `global_dir=~/.gemini/antigravity-cli`; both installers' legacy mirror paths updated in lockstep; `test_antigravity_commands.py` Markdown-not-TOML assertion repointed to `.agents/workflows/`. The Markdown-vs-TOML conclusion in [antigravity-cli-commands-schema.md](antigravity-cli-commands-schema.md) is validated, not changed.

### 11.3 Instruction file + frontmatter / name derivation (WN-4) -- DOCUMENTED

| Field | v2.2.0 inferred | 2026-05-29 verified | Source |
|---|---|---|---|
| Instruction file | `AGENT.md` (singular) | **`AGENTS.md`** at project root | `(docs-verified)` -- "AGENTS.md at repo root replaces the old `.gemini/` convention"; codelab `.agents/agents.md` example |
| Frontmatter | optional YAML | **YAML frontmatter honored** | `(docs-verified)` -- skills/workflows use frontmatter + Markdown body |
| Name derivation | filename or first H1 | **filename** (`lint.md` -> `/lint`) | `(docs-verified)` |

**Applied**: `instruction_file` -> `AGENTS.md`. The file is written to `.agents/AGENTS.md` (the integration's own dir), NOT the project root, because `agy` reads a project-root `AGENTS.md` that the `codex` integration already manages via the shared `## Nexus-Hub` marker; pointing two integrations at the same root file with one shared marker would clobber each other (a real install-time regression isolated tests would not catch). Whether `agy` should instead read a Nexus-Hub-written root `AGENTS.md` (requiring a per-integration marker scheme) is a residual decision in 11.4.

### 11.4 Residual items still requiring a live-VM `agy` smoke

These are tracked as a fresh non-blocking `WN` in `docs/archive/v2/v2.3/known-gaps.md`:

1. **`.agent/` vs `.agents/` dissent**: one official Google codelab ("Getting Started with Antigravity Skills") shows a workspace `.agent/` (singular); the weight of evidence favors `.agents/` (plural) but a live `agy` run is the tiebreaker.
2. **Exact global subpath**: sources put the CLI global footprint under the `~/.gemini/` family but vary between `~/.gemini/antigravity-cli/` and a top-level `~/.gemini/`; `~/.gemini/antigravity-cli/` was chosen as best-documented.
3. **`subagents/` / `rules/` subdirs**: the codelabs document `skills/` and `workflows/` under `.agents/`; the `subagents/` and `rules/` subdirs the integration also mirrors are unconfirmed (harmless if `agy` ignores them).
4. **Root vs `.agents/` instruction file**: confirm whether `agy` requires `AGENTS.md` specifically at the project root (vs. also reading `.agents/AGENTS.md`); if root is required, add a per-integration marker scheme so codex + antigravity2 can co-manage the root file.

All four are low-risk: the integration installs and the diff-review hook detects `agy` correctly; the residuals only affect whether `agy` actually consumes every mirrored path. Re-run a live `agy --help` / `agy init` probe once the binary is installed and reconcile.
