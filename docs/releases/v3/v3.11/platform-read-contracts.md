# Platform Read-Contracts (v3.11.0 Phase 7.1)

The authoritative, sourced map of where every supported platform READS each surface, and where the Nexus-Hub installer WRITES it. Built by auditing `scripts/lib/integrations/*.py`, `scripts/installer.sh`, `scripts/installer.ps1`, `docs/specs/*.md`, and `docs/archive/v2/v2.2/antigravity-cli-probe.md`. This table is the contract the Phase 7 fixes (7.2-7.3), the post-install verification (7.4), and the CI install-smoke (7.5) assert against. Findings only - 7.1 changes no installer behavior.

Source basis: repo code/config/spec (cited `file:line`). Contracts that depend on the current external platform's behavior and cannot be confirmed from the repo are flagged in "Residual live-verification gaps".

## Read/write surface table

Formats: skills = folder-per-skill `SKILL.md`, nested `<category>/<name>/` verbatim unless "flattened"; commands = `.md` verbatim unless noted. "reads" reflects the integration config / spec / docstring; the Defects section flags where the installer's actual writes diverge.

| Platform (key) | Scope | Instruction file | Commands / slash surface | Skills | Agents | Rules | Hooks |
|---|---|---|---|---|---|---|---|
| Claude (`claude`) | global | `~/.claude/CLAUDE.md` (marker-merged) | `~/.claude/commands/*.md` (slash) | `~/.claude/skills/` nested | `~/.claude/agents/` | `~/.claude/rules/` | `~/.claude/hooks/` + settings.json |
| Claude | workspace | `<project>/CLAUDE.md` (root) | `<project>/.claude/commands/*.md` | `.claude/skills/` | `.claude/agents/` | `.claude/rules/` | `.claude/hooks/` |
| Codex (`codex`) | global | `~/.codex/AGENTS.md` (marker-merged) | `~/.codex/prompts/*.md` (slash) | `~/.codex/skills/` nested | declared not installed (C5) | declared not installed (C5) | not supported |
| Codex | workspace | `<project>/AGENTS.md` (root) | `<project>/.codex/prompts/*.md` | `<project>/.codex/skills/` | not installed (C5) | not installed (C5) | none |
| Gemini IDE (`gemini`) | global | `~/.gemini/GEMINI.md` | spec `~/.gemini/workflows/` (bash: none; PS: `antigravity/global_workflows`) (C1) | spec `~/.gemini/skills/` (bash: none; PS only) (C1/C2) | spec `~/.gemini/agents/` never delivered (C2) | spec `~/.gemini/rules/` never delivered (C2) | not supported |
| Gemini IDE | workspace | `<project>/.gemini/GEMINI.md` | spec `.gemini/workflows/` never delivered (C2) | spec `.gemini/skills/` never delivered (C2) | never delivered (C2) | never delivered (C2) | none |
| Gemini CLI (`gemini-cli`, enterprise) | global | `~/.gemini/GEMINI.md` | `~/.gemini/commands/*.toml` (TOML, slash) | `~/.gemini/skills/` | `~/.gemini/agents/` | `~/.gemini/rules/` | not supported |
| Antigravity 1.0 (`antigravity`) | (unreachable) | spec `rules.md` under `~/.gemini/antigravity/` | spec `global_workflows/` | spec `skills/` | none | `rules_library/` | not supported |
| Antigravity 2.0 + CLI (`antigravity2`) | global | `~/.gemini/antigravity/AGENTS.md` AND `~/.gemini/antigravity-cli/AGENTS.md` | `workflows/<name>.md` (slash) both roots | flattened `skills/<name>/SKILL.md` | `subagents/` | `rules/` | `hooks/` + `hooks.json` |
| Antigravity 2.0 | workspace | `<project>/.agents/AGENTS.md` (but platform may read project-root `AGENTS.md`) (C4) | `<project>/.agents/workflows/*.md` (slash; PROJECT-ONLY) | `.agents/skills/<name>/` flattened | `.agents/subagents/` | `.agents/rules/` | `.agents/hooks/` + hooks.json |
| Copilot (`copilot`) | global | none | VS Code `<user>/prompts/<name>.prompt.md` (slash) | none | none | none | not supported |
| Copilot | workspace | `<project>/.github/copilot-instructions.md` (installer hand-builds, no SKILL_INDEX) (C6) | none | none | none | none | none |
| Cursor (`cursor`) | global | none | `~/.cursor/commands/<name>.md` (slash, any repo) | none | none | none | not supported |
| Cursor | workspace | `<project>/AGENTS.md` (marker-merged) | (Cursor-native project cmds) | none | none | `<project>/.cursor/rules/*.mdc` (flattened) | none |
| OpenCode (`opencode`) | global | `~/.opencode/AGENTS.md` | `~/.opencode/commands/*.md` (body-only, NOT slash) | `~/.opencode/skills/` | none | `~/.opencode/rules/` | not supported |
| OpenCode | workspace | `<project>/.opencode/AGENTS.md` | `.opencode/commands/` | `.opencode/skills/` | none | `.opencode/rules/` | none |
| Aider (`aider`) | global | none (no-op) | none | none | none | none | none |
| Aider | workspace | `<project>/CONVENTIONS.md` (root) | none (skills via embedded SKILL_INDEX) | none | none | none | none |
| Windsurf (`windsurf`) | global | `~/.codeium/windsurf/memories/global_rules.md` (only if `~/.codeium` exists) | none | none | none | none | none |
| Windsurf | workspace | `<project>/.windsurfrules` (root) | none | none | none | none | none |
| Kimi (`kimi`) | global | `~/.kimi/system.md` + `agent.yaml` (only if `~/.kimi` exists) | none | none | none | none | none |
| Kimi | workspace | `<project>/.kimi/system.md` + `.kimi/agent.yaml` | none | none | none | none | none |
| Qwen (`qwen`) | global | `~/.qwen/QWEN.md` (only if `~/.qwen` exists) | none | none | none | none | none |
| Qwen | workspace | `<project>/QWEN.md` (root) | none | none | none | none | none |
| OpenClaw (`openclaw`) | global | `~/.openclaw/{AGENTS,SOUL,IDENTITY}.md` (only if `~/.openclaw` exists) | none | none | none | none | none |
| OpenClaw | workspace | `<project>/.openclaw/AGENTS.md` + SOUL/IDENTITY | none | none | none | none | none |
| Nexus-AI (`nexus-ai`) | global | `~/.nexus-ai/catalog/NEXUS_AI.md` (dedicated) | `~/.nexus-ai/catalog/commands/` | `~/.nexus-ai/catalog/skills/` | `~/.nexus-ai/catalog/agents/` | `~/.nexus-ai/catalog/rules/` | `~/.nexus-ai/catalog/hooks/` |
| Nexus-AI | workspace | `<project>/.nexus-ai/catalog/NEXUS_AI.md` | `.nexus-ai/catalog/commands/` | `.nexus-ai/catalog/skills/` | `.nexus-ai/catalog/agents/` | `.nexus-ai/catalog/rules/` | `.nexus-ai/catalog/hooks/` |

Generic mirror: `SkillsIntegration._mirror_catalog` maps the `*_subdir` config keys to `catalog/{skills,commands,agents,rules,hooks}` (`base.py:686-702`); the mirror is SKIPPED when `ctx.instruction_only` is set (`base.py:709-710,721-722`), which is how the installer's DF-001 split works (legacy block copies the catalog tree, registry renders only the instruction file).

Nexus-AI isolation: `NexusAiIntegration` writes the entire catalog into an isolated `~/.nexus-ai/catalog/` subtree (not the `~/.nexus-ai/` root, which is the app's own data home), so a catalog refresh can wholesale wipe-and-refetch `catalog/` without touching app data. Beyond the generic mirror it also writes `mcp-configs/` and `templates/` (global scope only) and a `nexus-hub-version.json` manifest at the catalog root at both scopes (`nexus_ai.py`). The manifest is the desktop app's update-detection contract (installed `version` from `.claude-plugin/plugin.json` + `latest_release_api` + a `layout` map relative to the catalog root); see `docs/specs/nexus-ai.md`.

## Project-only surfaces (read ONLY from an open project, no global scan)

1. **Antigravity 2.0 IDE - `.agents/` (workflows, skills, rules).** The IDE reads slash commands, skills, and rules ONLY from the open project's `.agents/`; a global install is not scanned for slash commands (`antigravity.py:174-183`; installer warnings `installer.sh:949`, `installer.ps1:1319`). This is the primary bug the user reported: a global-only install seeds nothing usable in an arbitrary opened project. `nexus-hub init` seeds `.agents/` per-repo (`antigravity.py:174-189`).
2. **Aider** - project-root `CONVENTIONS.md`; global install is an explicit no-op (`aider.py:35-46`).
3. **Cursor** - only global surface is `~/.cursor/commands/` (slash); rules + `AGENTS.md` are per-project (`cursor.py:37-102`).
4. **Copilot** - only global surface is VS Code `prompts/*.prompt.md`; instructions are per-project (`copilot.py:65-90`).
5. Behavioral-only project-root files, global write gated on detecting the tool's config dir: Windsurf, Qwen, Kimi, OpenClaw.

## Defects and mismatches

Repo-provable (traceable to installer/integration/spec text):

- **C1 - bash/PowerShell parity break, Gemini IDE global.** `installer.ps1:1310,1312-1314` copies `catalog/skills` and `catalog/commands` for the Gemini IDE at global scope; `installer.sh:931-937` does neither (instruction-only). Same install, different result per OS.
- **C2 - Gemini mainline catalog mirror never fully delivered.** Both installers call gemini `--instruction-only` (skips the mirror, `base.py:709-710`) and no legacy block copies gemini `agents/`/`rules/`; net, Gemini agents/rules are never delivered on any OS, and skills/workflows only via the PS hardcode (C1).
- **C3 - `antigravity` (1.0) integration registered but unreachable.** Registered (`__init__.py:47`) but not in the installer's valid `--platforms` keys (`installer.sh:2464-2467`, `installer.ps1:304-315`); no block invokes it. Its surfaces are never produced by the integration.
- **C5 - Codex `agents/`/`rules/` declared+spec'd but never installed.** `codex.py:30-31` + `docs/specs/codex.md:26-27` declare them, but the installer calls codex `--instruction-only` and the legacy block copies only `skills` + `prompts` (`installer.sh:921-922,1317-1318`).
- **C6 - Copilot workspace instruction body diverges.** The `CopilotIntegration` renders `base-codex.md` with `{{SKILL_INDEX}}` marker-merged (`copilot.py:98-111`), but the installer hand-builds a short body WITHOUT the skill index and full-overwrites it (`installer.sh:1354-1393`). The registry path is effectively dead; the shipped file lacks the skill index the spec promises.
- **C7 - `docs/specs/copilot.md` global-scope claim stale.** Says Copilot has no global install, but the integration now mirrors a global VS Code `prompts/` slash surface (`copilot.py:73-90`; `installer.sh:963`).

External-dependent / needs live verification:

- **C4 - Antigravity 2.0 instruction file location.** Written to `<project>/.agents/AGENTS.md` (`antigravity.py:163-169`), but the platform may read a project-ROOT `AGENTS.md` (which the `codex` integration owns). The code comment concedes it writes under `.agents/` to avoid clobbering codex's root marker block.
- **C8 - Codex project-level `.codex/prompts`/`.codex/skills` may be dead** relative to Codex's actual read paths (its documented custom-prompt dir is global `~/.codex/prompts/`; project-level and skills-dir discovery are unverified in-repo).

## Residual live-verification gaps

These cannot be confirmed from the repo alone; flag rather than assert, and confirm with a live probe before hard-relying:

1. Codex prompt read path + format: does the current Codex read `~/.codex/prompts/*.md` as `/`-invocable prompts, and any project-level `.codex/prompts/`?
2. Codex skills discovery: does Codex consume a `skills/` dir at all? If not, the skills copies are dead (skills should surface via the AGENTS.md `SKILL_INDEX`).
3. Antigravity 2.0 root-vs-`.agents/` instruction file (C4) - residual item in `antigravity-cli-probe.md:157`.
4. Antigravity 2.0 exact global subpath (`~/.gemini/antigravity/` config vs `~/.gemini/antigravity/brain/` app-data; `~/.gemini/antigravity-cli/`).
5. Antigravity 2.0 `subagents/`/`rules/` consumption (codelabs document only `skills/` + `workflows/`).
6. `.agents/` vs `.agent/` (plural/singular) - one codelab shows singular; integration uses plural on weight-of-evidence.
7. Cursor / Copilot global slash surfaces - documented empirically in docstrings; can drift with editor updates.

## Implications for the Phase 7 fixes

- The user-reported bug maps to: **Antigravity 2.0 project-only `.agents/`** (fixed by 7.3 auto-seed + on-open hook) and **Codex delivery** (7.2, informed by gaps D1-D2; skills reliably surface via the AGENTS.md `SKILL_INDEX`).
- The audit surfaced adjacent surfacing defects the plan did not enumerate (C1/C2 Gemini parity + mirror, C3 dead Antigravity 1.0, C5 Codex agents/rules, C6/C7 Copilot). The post-install verification (7.4) and CI install-smoke (7.5) will REPORT/CATCH these; whether to FIX all of them in Phase 7 vs. record them as known gaps for a follow-up is a scope decision (see the Phase 7 fix plan).
