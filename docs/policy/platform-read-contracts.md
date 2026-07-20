# Platform Read-Contracts (living)

This is the durable, sourced source of truth for where every supported platform READS each surface (instruction file, slash commands, skills, agents, rules, hooks) and where the Nexus-Hub installer WRITES it. It supersedes the point-in-time snapshot at `docs/v3/v3.11/platform-read-contracts.md` (which resolved the v3.11.0 Phase 7 audit but left the Codex and Antigravity contracts flagged as unverified).

**Last verified**: 2026-07-20 (v3.15.0 Phase 1.2 parity re-verification of Cursor, OpenCode, Qwen, Kimi, and Copilot; preceded by the 2026-07-19 full 13-platform re-verification during the v3.14.5 release, reaffirmed unchanged for v3.14.6 and v3.14.7, neither of which touched any platform read-path). All cycles used the `platform-contract-verification` skill; see the Re-verification log below. The JSON's `meta.verified_for_version` is 3.14.7 (the last release); the v3.15.0 parity additions re-stamp it to 3.15.0 at release time (Phase 7 / `/update release`) as each integration lands, so the freshness gate stays green during development.

## How this doc is maintained

The machine-readable source of truth is the sibling `docs/policy/platform-read-contracts.json`; this `.md` is the human-readable table plus narrative and mirrors it. The JSON carries three sections: `contract_checks` (per-platform expected read-paths, consumed by `verify_platform_contracts.py`), `install_verify` (post-install surface checks, consumed by `runner.py`'s verify path), and `meta` (`last_verified` + `verified_for_version`, consumed by the release freshness gate). When a platform's row changes, edit the JSON entry first, then mirror it into the table below.

`/update release` runs a Nexus-Hub-specific "Platform read-contract re-verification" step before every version bump (see the `platform-contract-verification` skill). For each platform below it runs targeted web searches for that platform's CURRENT skill/command/rule/hook discovery format, diffs the findings against the JSON, and on any drift updates the JSON entry (mirrored here, plus its source URL and the Last-verified date), the corresponding integration adapter under `scripts/lib/integrations/`, and both installers. Three automated guards keep the release honest:

- `scripts/verify_platform_contracts.py` (run by `make validate`) asserts each integration's config and the installer copy targets match the `contract_checks` paths declared in the JSON (code-vs-contract).
- `nexus-hub verify` (`runner.py cmd_verify`) asserts, after an install, that each detected platform's read-paths (from the JSON's `install_verify`) are actually populated (install-vs-reality).
- `scripts/check_platform_contract_freshness.py` (run by `make validate` and CI) fails the build when the JSON's `meta.verified_for_version` does not match the version being released, so a release cannot ship on a contract that was not re-verified for it (freshness-vs-release).

The catalog itself is never reorganized per platform. Each integration is an adapter that materializes the canonical catalog into the shape below via the shared helpers in `scripts/lib/integrations/_catalog_adapters.py` (`flatten_skills`, `commands_to_skills`, `commands_to_slash`).

## Re-verification log

### 2026-07-20 (v3.15.0 platform-parity, Phase 1.2)

Web re-verification of the five platforms the v3.14.5 log deferred to v3.15.0 (the additive-surface parity targets), confirming exact read-paths against current official docs before wiring them in Phases 2-6. The findings are also recorded machine-readably in the sibling JSON's `parity_verification_v3_15_0` block. This cycle records READ-paths only; the installer WRITE side, the JSON `contract_checks` / `install_verify` rows, and the surface table below are updated per phase as each integration lands (adding a `contract_checks` row before its integration writes the surface would fail `verify_platform_contracts.py`). Classifications: MATCH (unchanged), DRIFT (gained a surface or the framing is stale), GAINED (a previously-unused surface confirmed), UNVERIFIED (not confirmable from reachable docs).

**Cursor (DRIFT - gained Skills, Subagents, and Hooks in Cursor 2.4):**

- Skills: reads `~/.cursor/skills/`, `~/.agents/skills/`, `~/.claude/skills/` (global) and `.cursor/skills/`, `.agents/skills/`, `.claude/skills/` (project); folder-per-skill `SKILL.md`, and discovery is RECURSIVE (nested and flattened both register).
- Subagents: `~/.cursor/agents/` / `.cursor/agents/` (also reads `.claude/agents/`); plain `.md` with YAML frontmatter, NOT `.agent.md` (correcting the pre-scout guess).
- Hooks: `~/.cursor/hooks.json` / `<project>/.cursor/hooks.json`; schema `{"version":1,"hooks":{<event>:[{"command":...}]}}`; events include `beforeShellExecution`, `afterShellExecution`, `afterFileEdit`, `preToolUse`, `postToolUse`, `sessionStart`, `stop`; exit 0 = ok, 2 = block, any other = fail-open; a `matcher` field is supported. A direct human read of the hooks doc is recommended before Phase 2 emits optional fields, to lock exact spelling.
- Commands: project `.cursor/commands/<name>.md` (flat `.md`, `/name`) CONFIRMED; the baseline global `~/.cursor/commands/` path is UNVERIFIED against reachable docs (kept, not removed, pending a direct check).
- Rules: `.cursor/rules/*.mdc` MATCH (root `AGENTS.md` also read).

**OpenCode (DRIFT - gained an agents folder; a plugins/hooks mechanism exists but on an incompatible runtime):**

- Agents: `~/.config/opencode/agents/` / `.opencode/agents/`; `.md` + YAML frontmatter (filename becomes the agent name).
- Plugins/hooks: `~/.config/opencode/plugins/` / `.opencode/plugins/`; JS/TS modules on a Bun runtime, NOT a Claude-style shell/python hook model. Nexus-Hub's `.sh`/`.py` hooks cannot be dropped in; delivering hooks here would require a JS/TS wrapper. Phase 3.2 recommendation: document as out-of-scope unless a wrapper is warranted.
- Skills and Commands MATCH; Rules MATCH (no `rules/` folder; `AGENTS.md` + an `instructions[]` array).

**Qwen Code (Gemini-CLI-class: YES; Phase 4 decision: GO):**

- Qwen Code is an open-source Gemini CLI fork and reproduces the full surface family under `~/.qwen` / `.qwen`.
- Skills: `~/.qwen/skills/<name>/SKILL.md` (global), `.qwen/skills/<name>/SKILL.md` (project); folder-per-skill one level, `name` + `description` frontmatter.
- Commands: `~/.qwen/commands/<name>.{md,toml}`; Markdown primary, TOML (`description` + `prompt`) deprecated-but-supported and identical to Gemini CLI's format.
- Agents: `~/.qwen/agents/<name>.md`. Rules: `QWEN.md` context file; no `rules/` folder.
- Caveat: open issue #2343 reports project-scoped skills may not auto-load on some builds; Phase 4 should live-smoke-test skill discovery before shipping.

**Kimi Code CLI (Gemini-CLI-class: YES; Phase 4 decision: GO) - with a product disambiguation:**

- The current product is Kimi Code CLI (`MoonshotAI/kimi-code`, data root `~/.kimi-code/`), the Node.js successor to the deprecated Python Kimi CLI (`~/.kimi/`) that the current baseline targets. Migration preserves `~/.kimi/`, so both coexist, but the new product reads `~/.kimi-code/`.
- Skills: `~/.kimi-code/skills/` + `~/.agents/skills/` (global), `.kimi-code/skills/` + `.agents/skills/` (project); folder-per-skill `SKILL.md` (or flat `<name>.md`), one level. The new product does NOT scan `~/.claude/skills`.
- Commands: no standalone command format; every skill auto-registers as `/skill:<name>` (the docs' `commands.html` returns 404). Commands are skills.
- Agents: not a distribution surface (three fixed built-in subagents). The baseline `.kimi/agent.yaml` is unsupported in the new product and should be dropped.
- Hooks: a `[[hooks]]` TOML array in `~/.kimi-code/config.toml` (config-merge, not a folder copy).
- Phase 4 note: resolve the old `~/.kimi/` vs new `~/.kimi-code/` vs the cross-tool `.agents/skills/` path choice before wiring.

**Copilot (DRIFT - skills are now native and default-on; agents and hooks are new):**

- Skills: `.github/skills/<name>/SKILL.md` is the native canonical path (also reads `.claude/skills/`, `.agents/skills/`; global `~/.copilot/skills/`, `~/.agents/skills/`, and in VS Code `~/.claude/skills/`); folder-per-skill one level, now DEFAULT-ON. The `.github/skills` PATH matches the baseline; the "opt-in / env-gated / off-by-default" FRAMING is stale.
- Agents: `.github/agents/*.agent.md` (project), `~/.copilot/agents/` (global).
- Hooks: `.github/hooks/*.json` (Preview), Claude-compat `.claude/settings.json`.
- Instruction: `.github/copilot-instructions.md` MATCH (`AGENTS.md` / `CLAUDE.md` additively supported behind settings). Prompts: `.github/prompts/*.prompt.md` MATCH.
- Phase 5 note: `.github/skills/` is commit-visible, so Nexus-Hub keeps the never-overwrite-existing-file guarantee even though Copilot no longer technically requires opt-in.

**Reclassification go/no-go (the Phase 4 gate, sub-task 1.3):**

- Qwen: GO - reclassify from instruction-file-only to skills + commands (+ agents) at the verified `~/.qwen` / `.qwen` paths.
- Kimi: GO - reclassify to skills + skills-as-commands, resolving the `~/.kimi-code/` (new) vs `.agents/skills/` (cross-tool) path in Phase 4; drop the unsupported `.kimi/agent.yaml`.

**Sources (fetched 2026-07-20):**

- Cursor skills: <https://cursor.com/docs/skills>
- Cursor subagents: <https://cursor.com/docs/subagents>
- Cursor hooks: <https://cursor.com/docs/hooks>
- Cursor rules / commands: <https://cursor.com/docs/rules>, <https://cursor.com/docs/customize-cursor>
- OpenCode agents / plugins / skills / commands / rules: <https://opencode.ai/docs/agents/>, <https://opencode.ai/docs/plugins/>, <https://opencode.ai/docs/skills/>, <https://opencode.ai/docs/commands/>, <https://opencode.ai/docs/rules/>
- Qwen Code skills / commands / sub-agents / settings: <https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/>, <https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/>, <https://qwenlm.github.io/qwen-code-docs/en/users/features/sub-agents/>, <https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/>
- Kimi Code CLI skills / slash-commands / agents / hooks / data-locations / migration: <https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/reference/slash-commands.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/data-locations.html>, <https://www.kimi.com/code/docs/en/kimi-code-cli/guides/migration.html>
- Copilot Agent Skills / custom agents / hooks / instructions / prompts: <https://docs.github.com/en/copilot/concepts/agents/about-agent-skills>, <https://docs.github.com/en/copilot/reference/custom-agents-configuration>, <https://code.visualstudio.com/docs/agent-customization/hooks>, <https://code.visualstudio.com/docs/agent-customization/custom-instructions>, <https://code.visualstudio.com/docs/copilot/customization/prompt-files>

### 2026-07-20 (v3.14.7 release - reaffirmed, no re-verification)

v3.14.7 is a cosmetic usage-monitor fix release: it changed only the two VS Code usage-monitor extensions' status-bar label rendering (an icon-to-text spacing gap), touching no platform read-paths, integration adapters, or installer copy targets. The 2026-07-19 full 13-platform web re-verification therefore still holds, so the contract is reaffirmed and the freshness marker re-stamped to 3.14.7 without a fresh web-search cycle. The additive drift recorded below remains deferred to v3.15.0.

### 2026-07-20 (v3.14.6 release - reaffirmed, no re-verification)

v3.14.6 is a usage-monitor + installer-log fix release: it changed no platform read-paths, integration adapters, or installer copy targets (only the two VS Code usage-monitor extensions and the installer's console output). The 2026-07-19 full 13-platform web re-verification therefore still holds, so the contract is reaffirmed and the freshness marker re-stamped to 3.14.6 without a fresh web-search cycle. The additive drift recorded below remains deferred to v3.15.0.

### 2026-07-19 (v3.14.5 release)

A full web re-verification of all supported platforms against current official docs. Dead-path bugs (our installer wrote where the platform no longer reads) were fixed in this release; additive drift (platforms that GAINED skills/agents/hooks surfaces we do not yet use) is deferred to v3.15.0 (platform parity), tracked in `docs/v3/v3.14/known-gaps.md`.

**Fixed in v3.14.5:**

- **OpenCode** - canonical global dir moved from `~/.opencode/` to `~/.config/opencode/` (XDG). The instruction file + commands were never reaching OpenCode at the old path (skills still did, via the `~/.claude/skills` + `~/.agents/skills` aliases). Adapter + contract + install-verify updated.
- **Kimi** - the instruction file moved from `.kimi/system.md` to `.kimi/AGENTS.md`. Kimi Code CLI auto-injects the merged `AGENTS.md` (including `.kimi/AGENTS.md`); `.kimi/system.md` is only loaded via `--agent-file`, so the old surface never reached Kimi. Resolves the v3.11.0-deferred Kimi known-gap.
- **OpenClaw** - global trio moved from `~/.openclaw/` to `~/.openclaw/workspace/` (the single global workspace dir OpenClaw actually reads).

**Deferred to v3.15.0 (additive - platforms gained surfaces; not breakage):**

- **Copilot** now natively reads Agent Skills (on by default: `.github/skills/`, `~/.copilot/skills/`, and `~/.claude/skills/`), custom agents (`.github/agents/*.agent.md`), and hooks.
- **Cursor** gained Agent Skills (`.cursor/skills/`, `~/.cursor/skills/`, `.agents/skills/`), subagents, and hooks (`hooks.json`).
- **Codex** gained a hooks system (`~/.codex/hooks.json` / `[hooks]` in `config.toml`). Also: one source reports `~/.codex/skills` is no longer read (only `~/.agents/skills` is); Nexus-Hub still writes both, so skills reach Codex regardless - the redundant `~/.codex/skills` write is kept pending a second confirmation (removing a possibly-live path on single-source evidence could break delivery).
- **OpenCode** supports agents (`~/.config/opencode/agents/`) and plugin-based hooks; its commands ARE a TUI slash surface and it has no `rules/` dir (uses `AGENTS.md` + an `instructions[]` array).

**Unverified this cycle (official docs unreachable / undocumented):**

- **Antigravity 2.0** global-workflows dir is community-reported as `~/.gemini/antigravity/global_workflows/` (vs the contract's `~/.gemini/config/global_workflows/`); the official docs are a client-rendered SPA that could not be fetched, so this is NOT changed pending an authoritative source. Its `.agents/subagents/` static dir appears obsolete (subagents are now dynamic).
- **Gemini IDE** per-tool read-paths (`~/.gemini/workflows`, `agents/`, `rules/`) are undocumented in official sources; the IDE was also sunset for free/Pro/Ultra on 2026-06-18 (enterprise-only), like the CLI.

**Notes:** Windsurf rebranded to "Devin Desktop"; the legacy `.windsurfrules` + `~/.codeium/windsurf/memories/global_rules.md` surfaces are still served (a `.devin/rules/` surface is now preferred - optional future adoption). Claude, Aider, Qwen verified clean.

## Read/write surface table

Formats: skills = folder-per-skill `SKILL.md`. "flattened" means one level deep (`skills/<name>/SKILL.md`), which requires dropping the catalog's `<category>/` layer; "nested" means the catalog `<category>/<name>/` tree is copied verbatim. commands = `.md` verbatim unless noted. Every command additionally surfaces as a skill (`skills/<command>/SKILL.md`, invoked `$command`) on platforms whose reusable-action surface is skills.

| Platform (key) | Scope | Instruction file | Commands / slash surface | Skills | Agents | Rules | Hooks |
|---|---|---|---|---|---|---|---|
| Claude (`claude`) | global | `~/.claude/CLAUDE.md` (marker-merged) | `~/.claude/commands/*.md` (slash) | flattened `~/.claude/skills/<name>/` (+ command-skills) | `~/.claude/agents/` | `~/.claude/rules/` | `~/.claude/hooks/` + settings.json |
| Claude | workspace | `<project>/CLAUDE.md` (root) | `<project>/.claude/commands/*.md` | flattened `.claude/skills/<name>/` (+ command-skills) | `.claude/agents/` | `.claude/rules/` | `.claude/hooks/` |
| Codex (`codex`) | global | `~/.codex/AGENTS.md` (marker-merged) | `~/.codex/prompts/*.md` (flat, `/prompts:name`, deprecated) + skills below (`$name`) | flattened `~/.codex/skills/<name>/` AND `~/.agents/skills/<name>/` (+ one per command) | not read | not read | not supported |
| Codex | workspace | `<project>/AGENTS.md` (root) | `<project>/.codex/prompts/*.md` + skills below | flattened `.codex/skills/<name>/` AND `.agents/skills/<name>/` (+ one per command) | not read | not read | none |
| Antigravity 2.0 IDE (`antigravity2`) | global | `~/.gemini/GEMINI.md` (global rules) | `~/.gemini/config/global_workflows/<name>.md` (slash) + skills below | flattened `~/.gemini/config/skills/<name>/` (+ one per command) | `~/.gemini/config/skills/` (as skills) | `~/.gemini/GEMINI.md` | `hooks/` + `hooks.json` (best-effort) |
| Antigravity `agy` CLI (`antigravity2`) | global | `~/.gemini/antigravity-cli/` instruction | `~/.gemini/antigravity-cli/` workflows (best-effort, unverified) | flattened `~/.gemini/antigravity-cli/skills/<name>/` | (as skills) | (CLI global) | `hooks/` + `hooks.json` |
| Antigravity 2.0 | workspace | `<project>/.agents/` instruction (root `AGENTS.md` may also be read) | `<project>/.agents/workflows/*.md` (slash) + skills below | flattened `.agents/skills/<name>/` (+ one per command) | `.agents/subagents/` | `.agents/rules/` | `.agents/hooks/` + hooks.json |
| Gemini IDE (`gemini`) | global | `~/.gemini/GEMINI.md` | `~/.gemini/workflows/` (see v3.11 defects C1/C2) | flattened `~/.gemini/skills/<name>/` (+ command-skills) | `~/.gemini/agents/` | `~/.gemini/rules/` | not supported |
| Gemini CLI (`gemini-cli`, enterprise) | global | `~/.gemini/GEMINI.md` | `~/.gemini/commands/*.toml` (TOML, slash) | flattened `~/.gemini/skills/<name>/` (also reads `~/.agents/skills`) | `~/.gemini/agents/` | `~/.gemini/rules/` | not supported |
| Copilot (`copilot`) | global | none | VS Code `<user>/prompts/<name>.prompt.md` (slash) | none (opt-in `.github/skills/`) | none | none | not supported |
| Copilot | workspace | `<project>/.github/copilot-instructions.md` | none | opt-in `.github/skills/<name>/SKILL.md` | none | none | none |
| Cursor (`cursor`) | global | none | `~/.cursor/commands/<name>.md` (slash, any repo) | flattened `~/.cursor/skills/<name>/` (+ command-skills) | `~/.cursor/agents/*.md` | none | `~/.cursor/hooks.json` + `~/.cursor/hooks/` (git-guardrails) |
| Cursor | workspace | `<project>/AGENTS.md` (marker-merged) | `<project>/.cursor/commands/<name>.md` (slash) | flattened `.cursor/skills/<name>/` (+ command-skills) | `.cursor/agents/*.md` | `<project>/.cursor/rules/*.mdc` (flattened) | `.cursor/hooks.json` + `.cursor/hooks/` |
| OpenCode (`opencode`) | global | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/commands/*.md` (slash in the TUI) | flattened `~/.config/opencode/skills/<name>/`; also reads `~/.claude/skills` + `~/.agents/skills` | none (uses AGENTS.md + `instructions[]`) | via plugins | not a folder surface |
| OpenCode | workspace | `<project>/.opencode/AGENTS.md` | `.opencode/commands/` | flattened `.opencode/skills/<name>/` (also `.claude/skills`, `.agents/skills`) | none | `.opencode/rules/` | none |
| Aider (`aider`) | workspace | `<project>/CONVENTIONS.md` (root) | none (skills via embedded SKILL_INDEX) | none | none | none | none |
| Windsurf (`windsurf`) | workspace | `<project>/.windsurfrules` (root) | none | none | none | none | none |
| Kimi (`kimi`) | workspace | `<project>/.kimi/AGENTS.md` (in Kimi Code CLI's merged-AGENTS.md context) + `.kimi/agent.yaml` | none | none | none | none | none |
| Qwen (`qwen`) | workspace | `<project>/QWEN.md` (root) | none | none | none | none | none |
| OpenClaw (`openclaw`) | workspace | `<project>/.openclaw/AGENTS.md` + SOUL/IDENTITY (global detected: `~/.openclaw/workspace/`) | none | none | none | none | none |
| Nexus-AI (`nexus-ai`) | global | `~/.nexus-ai/catalog/NEXUS_AI.md` (dedicated) | `~/.nexus-ai/catalog/commands/` | flattened `~/.nexus-ai/catalog/skills/<name>/` (+ command-skills) | `~/.nexus-ai/catalog/agents/` | `~/.nexus-ai/catalog/rules/` | `~/.nexus-ai/catalog/hooks/` |

## Sources (corrected rows, verified 2026-07-13)

- Codex skills discovery, one-level-deep `SKILL.md`, `~/.codex/skills` + `~/.agents/skills`, `$name` invocation: <https://learn.chatgpt.com/docs/build-skills>
- Codex custom prompts deprecated, `~/.codex/prompts/*.md` top-level only, `/prompts:name`: <https://learn.chatgpt.com/docs/custom-prompts>
- Codex AGENTS.md (`~/.codex/AGENTS.md` + repo root): <https://developers.openai.com/codex/guides/agents-md>
- New ChatGPT desktop app merges Chat + Work + Codex; skills work in the desktop app, CLI, and IDE extension: <https://openai.com/index/introducing-the-codex-app/>
- Antigravity IDE global skills `~/.gemini/config/skills/`, global workflows `~/.gemini/config/global_workflows/`, global rules `~/.gemini/GEMINI.md`, project `.agents/`: <https://codelabs.developers.google.com/getting-started-agy-ide>
- Antigravity skills format (folder-per-skill `SKILL.md`, one level, name+description frontmatter) and CLI skills at `~/.gemini/antigravity-cli/skills/`: <https://codelabs.developers.google.com/getting-started-with-antigravity-skills>
- Claude Code skills one level deep (`~/.claude/skills/<name>/SKILL.md`, "a directory that contains a SKILL.md file"): <https://code.claude.com/docs/en/skills>
- OpenCode skills one level deep; reads `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` (and `.opencode/skills`, `.claude/skills`, `.agents/skills` per project): <https://opencode.ai/docs/skills/>
- Gemini CLI skills one level deep; reads `~/.gemini/skills` and the `~/.agents/skills` alias: <https://geminicli.com/docs/cli/skills/>

## Defects to resolve in this release (v3.12.0)

- **Codex flattening**: the installer copies `catalog/skills` verbatim to `~/.codex/skills`, preserving the `<category>/<name>/` tree, so skill folders sit two levels deep and Codex discovers none. Fix: `flatten_skills` to `~/.codex/skills` AND `~/.agents/skills` (Phase 2).
- **Codex commands invisible in the desktop app**: commands ship only as deprecated prompts (`/prompts:name`). Fix: also emit `commands_to_skills` so `$name` works, keep prompts for CLI back-compat (Phase 2).
- **Antigravity wrong global paths**: the installer writes global content to `~/.gemini/antigravity/`, which the IDE does not read. Fix: `~/.gemini/config/skills/`, `~/.gemini/config/global_workflows/`, `~/.gemini/GEMINI.md` (Phase 3).

## Residual live-verification gaps

Cannot be confirmed from docs alone; write to all documented candidates (additive) and confirm via the `/update release` re-verification step or a live probe:

1. Whether the new ChatGPT desktop app canonically prefers `~/.codex/skills` or `~/.agents/skills` (we write both).
2. The `agy` CLI global workflow directory (skills confirmed at `~/.gemini/antigravity-cli/skills/`; the workflow path is best-effort).
3. Antigravity 2.0 global hooks path (the codelabs document `skills/` + `workflows/`, not hooks at global scope).
4. Antigravity 2.0 project instruction: root `AGENTS.md` vs `.agents/` (v3.11 defect C4).
5. OpenCode canonical global skills dir: docs cite `~/.config/opencode/skills`, but we flatten to `~/.opencode/skills` and rely on OpenCode also reading `~/.claude/skills` + `~/.agents/skills` (both flattened by the claude/codex integrations on a full install). Confirm the canonical global dir on a live install.
6. Gemini IDE (Code Assist) skill discovery: `~/.gemini/skills` flattening is applied on weight-of-evidence (the SKILL.md open standard, confirmed for Gemini CLI); confirm Code Assist reads `~/.gemini/skills` as well.
