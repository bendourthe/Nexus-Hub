# Platform Read-Contracts (living)

This is the durable, sourced source of truth for where every supported platform READS each surface (instruction file, slash commands, skills, agents, rules, hooks) and where the Nexus-Hub installer WRITES it. It supersedes the point-in-time snapshot at `docs/v3/v3.11/platform-read-contracts.md` (which resolved the v3.11.0 Phase 7 audit but left the Codex and Antigravity contracts flagged as unverified).

**Last verified**: 2026-08-04 for v3.15.9. This release changed no platform read path; the only delivery-code change was source-side, in the shared `flatten_skills` adapter, which now skips a `catalog/skills/<category>/<name>/` directory carrying no `SKILL.md` instead of publishing it. Two platforms were re-checked against live documentation because that change affects every skills-bearing platform. **Hermes**: discovery lists every direct subdirectory of the tap path and probes each for `SKILL.md`, confirming the recorded contract and independently validating the fix (it also ignores directories beginning with `.` or `_`, which the current delivery already satisfies). **Cursor**: the project path `.cursor/skills/<name>/SKILL.md` is confirmed, and multiple current sources state Cursor exposes no personal/global skills directory, which corroborates and extends known gap **DF-1** (previously scoped to the unverified global `~/.cursor/commands/`) to the global `~/.cursor/skills/` path. Those are secondary sources, not an official Cursor doc page, so DF-1 stays OPEN and the globally-written Cursor surfaces are retained unchanged pending first-party confirmation in a v3.15.10 follow-on. All other platforms carry forward from the 2026-08-02 / 2026-08-03 audits below and were not re-checked this cycle.

**Prior stamp**: 2026-08-02 for v3.15.7. The full current-documentation audit found no dead delivery path in the surfaces Nexus-Hub already writes, but it found additive agent and hook capabilities that the current adapters do not yet deliver. The maintainer approved an audited-with-known-drift release: the enforced contract remains the currently delivered behavior, the JSON's non-consumed `release_verification_v3_15_7` block records the findings, and adapter implementation is assigned to v3.15.8.

## How this doc is maintained

The machine-readable source of truth is the sibling `docs/policy/platform-read-contracts.json`; this `.md` is the human-readable table plus narrative and mirrors it. The JSON carries three sections: `contract_checks` (per-platform expected read-paths, consumed by `verify_platform_contracts.py`), `install_verify` (post-install surface checks, consumed by `runner.py`'s verify path), and `meta` (`last_verified` + `verified_for_version`, consumed by the release freshness gate). When a platform's row changes, edit the JSON entry first, then mirror it into the table below.

`/update release` runs a Nexus-Hub-specific "Platform read-contract re-verification" step before every version bump (see the `platform-contract-verification` skill). For each platform below it runs targeted web searches for that platform's CURRENT skill/command/rule/hook discovery format, diffs the findings against the JSON, and on any drift updates the JSON entry (mirrored here, plus its source URL and the Last-verified date), the corresponding integration adapter under `scripts/lib/integrations/`, and both installers. Three automated guards keep the release honest:

- `scripts/verify_platform_contracts.py` (run by `make validate`) asserts each integration's config and the installer copy targets match the `contract_checks` paths declared in the JSON (code-vs-contract).
- `nexus-hub verify` (`runner.py cmd_verify`) asserts, after an install, that each detected platform's read-paths (from the JSON's `install_verify`) are actually populated (install-vs-reality).
- `scripts/check_platform_contract_freshness.py` (run by `make validate` and CI) fails the build when the JSON's `meta.verified_for_version` does not match the version being released, so a release cannot ship on a contract that was not re-verified for it (freshness-vs-release).

The catalog itself is never reorganized per platform. Each integration is an adapter that materializes the canonical catalog into the shape below via the shared helpers in `scripts/lib/integrations/_catalog_adapters.py` (`flatten_skills`, `commands_to_skills`, `commands_to_slash`).

## Re-verification log

### 2026-08-02 (v3.15.7 release - full re-verification)

The release audit re-read current official documentation across the supported roster. Existing v3.15.7 write paths remain functional, so no `contract_checks`, `install_verify`, adapter, or installer path changed. The release classification is `RELEASE_WITH_DOCUMENTED_DRIFT`, not an all-MATCH claim.

- **MATCH or functionally aligned**: Claude, Cursor, OpenCode's supported surfaces, Aider, Nexus-AI's local contract, and Hermes's existing flattened skill children. Hermes now documents category-nested skill directories, but its recursive discovery still accepts the delivered flattened layout.
- **DRIFT-ADDITIVE, deferred to v3.15.8**: Codex custom TOML agents and native hooks; Gemini CLI and Qwen native hooks; Kimi custom agents and TOML hooks; Copilot custom agents and hooks. These are new upstream capabilities, not broken v3.15.7 delivery paths.
- **UNVERIFIED or partial**: Antigravity's exact global hook and `agy` workflow paths, Gemini IDE-specific skill discovery, Windsurf, and OpenClaw. Existing detection-gated or best-effort behavior is retained without promoting those rows to MATCH.

Primary sources: [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents), [Codex hooks](https://learn.chatgpt.com/docs/hooks), [Claude features](https://code.claude.com/docs/en/features-overview), [Claude hooks](https://code.claude.com/docs/en/hooks), [Gemini CLI skills](https://geminicli.com/docs/cli/using-agent-skills/), [Gemini CLI context](https://geminicli.com/docs/cli/gemini-md/), [Qwen skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/), [Qwen hooks](https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/), [Kimi skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html), [Kimi agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html), [Kimi hooks](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html), [Copilot skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills), [Copilot agents](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/about-custom-agents), [Copilot hooks](https://docs.github.com/en/copilot/concepts/agents/hooks), [OpenCode skills](https://opencode.ai/docs/skills/), [OpenCode commands](https://opencode.ai/docs/commands/), [OpenCode agents](https://opencode.ai/docs/agents), [Aider conventions](https://aider.chat/docs/usage/conventions.html), [Antigravity skills](https://codelabs.developers.google.com/getting-started-with-antigravity-skills), and [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills).

### 2026-07-21 (v3.15.0 Phase 4 - Qwen + Kimi reclassification)

Direct re-read of both platforms' official docs before reclassifying them from instruction-file-only to skills-bearing integrations (acting on Phase 1's GO verdicts; resolving DF-2 and DF-3).

- **Qwen Code - reclassified.** [qwenlm.github.io/qwen-code-docs](https://qwenlm.github.io/qwen-code-docs/) confirms skills at `~/.qwen/skills/` (global) + `.qwen/skills/` (project, folder-per-skill `SKILL.md`), agents at `~/.qwen/agents/<name>.md`, and commands at `~/.qwen/commands/` where **Markdown is the primary format and TOML is deprecated** (Qwen shows a migration prompt on TOML). So the integration delivers flattened skills + agents + **Markdown** commands (not TOML), preserving `QWEN.md`. **DF-2**: the docs only document "restart to load"; the auto-load bug is GitHub issue #2343 (not documented). Skills are delivered to BOTH scopes (global `~/.qwen/skills/` is the reliable path), which mitigates it. No `~/.agents/skills` alias for Qwen, so only native paths are written.
- **Kimi - reclassified + migrated (resolves DF-3).** [kimi.com/code/docs](https://www.kimi.com/code/docs/) confirms the current product is **Kimi Code CLI** (`MoonshotAI/kimi-code`, data root `~/.kimi-code/`) - a DIFFERENT product from the older "Kimi CLI" (`~/.kimi/`, moonshotai.github.io/kimi-cli) the prior integration targeted. Kimi Code CLI reads skills at `~/.kimi-code/skills/` + `~/.agents/skills/` (each auto-registering as `/skill:<name>`; no separate command format), AGENTS.md at `~/.kimi-code/AGENTS.md`, has no user-definable agents, and takes hooks as `config.toml` `[[hooks]]` (out of scope). Per the maintainer decision, the integration FULLY MIGRATED to `~/.kimi-code/` (AGENTS.md + native `~/.kimi-code/skills`), dropping the old `~/.kimi/` writes and the `.kimi/agent.yaml` companion. Native skills path only (not the shared `~/.agents/skills`), to avoid a teardown conflict with codex.

Source docs read: [Qwen skills](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/), [Qwen commands](https://qwenlm.github.io/qwen-code-docs/en/users/features/commands/), [Kimi Code CLI data-locations](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/data-locations.html), [Kimi Code CLI skills](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html).

### 2026-07-21 (v3.15.0 Phase 3 - OpenCode agents + plugins/hooks decision)

Targeted re-read of OpenCode's official docs to finalize the two Phase 3 items:

- **Agents - DELIVERED.** [opencode.ai/docs/agents](https://opencode.ai/docs/agents/) confirms OpenCode reads custom agents from `~/.config/opencode/agents/` (global) and `.opencode/agents/` (project) as Markdown files with YAML frontmatter, the filename being the agent id. The `mode` field is OPTIONAL and defaults to `all`, so the catalog's `agents/*.md` personas (which carry `name`/`description`/`tools` frontmatter, not `mode`) load as-is - OpenCode uses `description` + the filename and ignores the non-native keys, exactly as Cursor consumes the same files. Delivered via a config-only `agents_subdir: "agents"` addition (the base `_mirror_catalog` does the verbatim tree copy). Contract JSON `contract_checks.opencode` + `install_verify` updated with the agents path.
- **Plugins / hooks - OUT OF SCOPE (documented non-gap, resolves DF-4).** [opencode.ai/docs/plugins](https://opencode.ai/docs/plugins/) confirms plugins are JavaScript/TypeScript modules loaded by Bun, each exporting plugin functions that subscribe to events (`tool.execute.before`, `file.edited`, ...); the docs state a plugin must be a JS/TS module and that a `.sh`/`.py` script cannot be dropped into `plugins/` and run. Nexus-Hub's shell/py hooks therefore cannot be delivered without authoring a JS/TS wrapper per hook, so OpenCode hooks stay out of scope (`hooks_supported: False`).

Source docs read: [Agents | OpenCode Docs](https://opencode.ai/docs/agents/), [Plugins | OpenCode Docs](https://opencode.ai/docs/plugins/).

### 2026-07-21 (v3.15.0 Phase 2 - Cursor DF-1 resolution)

Targeted re-read of Cursor's official docs to close the two Cursor items Phase 1.2 left UNVERIFIED (known-gap DF-1) before finalizing the Cursor integration:

- **`hooks.json` schema - RESOLVED (no code change).** [cursor.com/docs/hooks](https://cursor.com/docs/hooks) confirms the top-level shape `{"version": 1, "hooks": {<event>: [{...}]}}`; each entry's fields `type` / `timeout` / `loop_limit` / `failClosed` / `matcher` are all OPTIONAL (defaults `type="command"`, `failClosed=false`, `loop_limit=5`), so the entry may be the minimal `{"command": "..."}`. `beforeShellExecution` is a documented event; exit code `2` (or `{"permission":"deny"}`) blocks, other non-zero codes fail-open. Cursor reads both `~/.cursor/hooks.json` (user) and `<project>/.cursor/hooks.json` (project). The integration's minimal git-guardrails writer is therefore schema-valid as-is; DF-1(b) resolved.
- **Global `~/.cursor/commands/` path - still UNVERIFIED (kept, tracked).** Project `.cursor/commands/<name>.md` is officially documented (custom slash commands, Cursor 1.6+) and confirmed. The user-global `~/.cursor/commands/` dir has NO reachable official doc (the dedicated commands page 404s / redirects to Skills); [forum.cursor.com](https://forum.cursor.com/t/personal-custom-slash-commands/133386) reports it as an open feature-request, not a built-in. Per plan sub-task 2.3 ("keep the global mirror unchanged") and the contract's negative-only-evidence caution, the global write is RETAINED (harmless if unread; removing a possibly-live path on negative evidence could break delivery) and recorded as the DF-1 residual for a future direct-confirmation cycle. Cursor read-paths that ARE confirmed this cycle: skills (recursive `SKILL.md`), subagents (plain `.md`), rules (`.mdc`), project commands, and the `hooks.json` schema.

Source docs read: [Hooks | Cursor Docs](https://cursor.com/docs/hooks), [Slash commands | Cursor Docs](https://cursor.com/docs/cli/reference/slash-commands), [Rules | Cursor Docs](https://cursor.com/docs/rules), [Cursor community: personal custom slash commands](https://forum.cursor.com/t/personal-custom-slash-commands/133386).

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
- **Codex** gained a hooks system (`~/.codex/hooks.json` / `[hooks]` in `config.toml`). Also: one source reports `~/.codex/skills` is no longer read (only `~/.agents/skills` is); Nexus-Hub still writes both, so skills reach Codex regardless - the redundant `~/.codex/skills` write is kept pending a second confirmation (removing a possibly-live path on single-source evidence could break delivery). **Delivered in v3.15.8 Phase 5** - see the Codex native surfaces section below.
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
| Codex (`codex`) | global | `~/.codex/AGENTS.md` (marker-merged) | `~/.codex/prompts/*.md` (flat, `/prompts:name`, deprecated) + skills below (`$name`) | flattened `~/.codex/skills/<name>/` AND `~/.agents/skills/<name>/` (+ one per command) | `~/.codex/agents/<name>.toml` (transformed from `catalog/agents/*.md`) | not read | `~/.codex/hooks.json` (structured merge) + `~/.codex/hooks/`, gated on `[features] hooks = true` in `~/.codex/config.toml` |
| Codex | workspace | `<project>/AGENTS.md` (root) | `<project>/.codex/prompts/*.md` + skills below | flattened `.codex/skills/<name>/` AND `.agents/skills/<name>/` (+ one per command) | `.codex/agents/<name>.toml` | not read | `.codex/hooks.json` + `.codex/hooks/`; the feature switch stays user-global |
| Antigravity 2.0 IDE (`antigravity2`) | global | `~/.gemini/GEMINI.md` (global rules) | `~/.gemini/config/global_workflows/<name>.md` (slash) + skills below | flattened `~/.gemini/config/skills/<name>/` (+ one per command) | `~/.gemini/config/skills/` (as skills) | `~/.gemini/GEMINI.md` | `hooks/` + `hooks.json` (best-effort) |
| Antigravity `agy` CLI (`antigravity2`) | global | `~/.gemini/antigravity-cli/` instruction | `~/.gemini/antigravity-cli/` workflows (best-effort, unverified) | flattened `~/.gemini/antigravity-cli/skills/<name>/` | (as skills) | (CLI global) | `hooks/` + `hooks.json` |
| Antigravity 2.0 | workspace | `<project>/.agents/` instruction (root `AGENTS.md` may also be read) | `<project>/.agents/workflows/*.md` (slash) + skills below | flattened `.agents/skills/<name>/` (+ one per command) | `.agents/subagents/` | `.agents/rules/` | `.agents/hooks/` + hooks.json |
| Gemini IDE (`gemini`) | global | `~/.gemini/GEMINI.md` | `~/.gemini/workflows/` (see v3.11 defects C1/C2) | flattened `~/.gemini/skills/<name>/` (+ command-skills) | `~/.gemini/agents/` | `~/.gemini/rules/` | not supported |
| Gemini CLI (`gemini-cli`, enterprise) | global | `~/.gemini/GEMINI.md` | `~/.gemini/commands/*.toml` (TOML, slash) | flattened `~/.gemini/skills/<name>/` (also reads `~/.agents/skills`) | `~/.gemini/agents/` | `~/.gemini/rules/` | `~/.gemini/settings.json` `hooks` key (structured merge) + `~/.gemini/hooks/`; renamed events, regex tool matchers |
| Gemini CLI | workspace | `<project>/.gemini/GEMINI.md` | `.gemini/commands/*.toml` (TOML, slash) | flattened `.gemini/skills/<name>/` | `.gemini/agents/` | `.gemini/rules/` | `.gemini/settings.json` `hooks` key + `.gemini/hooks/`; commands resolve via `$GEMINI_PROJECT_DIR` |
| Copilot (`copilot`) | global | none | VS Code `<user>/prompts/<name>.prompt.md` (slash) | opt-in selector writes native skill folders | `~/.copilot/agents/<name>.agent.md` (verbatim catalog Markdown) | none | INHERITED from `~/.claude/settings.json`, a Copilot default hook location |
| Copilot | workspace | `<project>/.github/copilot-instructions.md` | project prompt files are not seeded | opt-in `.github/skills/<name>/SKILL.md` | INHERITED from `.claude/agents/`, a Copilot default agent location | none | INHERITED from `.claude/settings.json`, a Copilot default hook location |
| Cursor (`cursor`) | global | none | `~/.cursor/commands/<name>.md` (slash, any repo) | flattened `~/.cursor/skills/<name>/` (+ command-skills) | `~/.cursor/agents/*.md` | none | `~/.cursor/hooks.json` + `~/.cursor/hooks/` (git-guardrails) |
| Cursor | workspace | `<project>/AGENTS.md` (marker-merged) | `<project>/.cursor/commands/<name>.md` (slash) | flattened `.cursor/skills/<name>/` (+ command-skills) | `.cursor/agents/*.md` | `<project>/.cursor/rules/*.mdc` (flattened) | `.cursor/hooks.json` + `.cursor/hooks/` |
| OpenCode (`opencode`) | global | `~/.config/opencode/AGENTS.md` | `~/.config/opencode/commands/*.md` (slash in the TUI) | flattened `~/.config/opencode/skills/<name>/`; also reads `~/.claude/skills` + `~/.agents/skills` | `~/.config/opencode/agents/*.md` | via AGENTS.md + `instructions[]` | plugins require JS/TS; shell/py hooks incompatible |
| OpenCode | workspace | `<project>/.opencode/AGENTS.md` | `.opencode/commands/` | flattened `.opencode/skills/<name>/` (also `.claude/skills`, `.agents/skills`) | `.opencode/agents/*.md` | via AGENTS.md + `instructions[]` | plugins require JS/TS; shell/py hooks incompatible |
| Aider (`aider`) | workspace | `<project>/CONVENTIONS.md` (root) | none (skills via embedded SKILL_INDEX) | none | none | none | none |
| Windsurf (`windsurf`) | workspace | `<project>/.windsurfrules` (root) | none | none | none | none | none |
| Kimi (`kimi`) | global | `~/.kimi-code/AGENTS.md` | skills register as `/skill:<name>` | flattened `~/.kimi-code/skills/<name>/` (+ command-skills) | `~/.kimi-code/agents/<name>.md` (verbatim catalog Markdown) | via AGENTS.md | `[[hooks]]` in `~/.kimi-code/config.toml` (marker-managed block) + `~/.kimi-code/hooks/` |
| Kimi | workspace | `<project>/.kimi-code/AGENTS.md` | skills register as `/skill:<name>` | flattened `.kimi-code/skills/<name>/` (+ command-skills) | `.kimi-code/agents/<name>.md` (verbatim catalog Markdown) | via AGENTS.md | none - the project config is `local.toml` and documents only `[workspace]`, so no project hook path exists |
| Qwen (`qwen`) | global | `~/.qwen/QWEN.md` | `~/.qwen/commands/*.md` | flattened `~/.qwen/skills/<name>/` (+ command-skills) | `~/.qwen/agents/*.md` | via QWEN.md | `~/.qwen/settings.json` `hooks` key (structured merge) + `~/.qwen/hooks/`; Claude-style events, regex tool matchers, `shell` field |
| Qwen | workspace | `<project>/QWEN.md` | `.qwen/commands/*.md` | flattened `.qwen/skills/<name>/` (+ command-skills) | `.qwen/agents/*.md` | via QWEN.md | `.qwen/settings.json` `hooks` key + `.qwen/hooks/`; commands resolve via `$QWEN_PROJECT_DIR` |
| OpenClaw (`openclaw`) | workspace | `<project>/.openclaw/AGENTS.md` + SOUL/IDENTITY (global detected: `~/.openclaw/workspace/`) | none | none | none | none | none |
| Nexus-AI (`nexus-ai`) | global | `~/.nexus-ai/catalog/NEXUS_AI.md` (dedicated) | `~/.nexus-ai/catalog/commands/` | flattened `~/.nexus-ai/catalog/skills/<name>/` (+ command-skills) | `~/.nexus-ai/catalog/agents/` | `~/.nexus-ai/catalog/rules/` | `~/.nexus-ai/catalog/hooks/` |
| Hermes (`hermes`) | global | none (skills-native; no instruction file) | none (skills are the action surface) | flattened `~/.hermes/skills/<name>/` (+ command-skills); ALSO reads the shared `~/.agents/skills/` written by `codex` | none | none | not supported |
| Hermes | workspace | none | none | flattened `.hermes/skills/<name>/` (+ command-skills); ALSO reads the project `.agents/skills/` seeded by `antigravity2` on `nexus-hub init` | none | none | none |

### Codex native agents and hooks (v3.15.8 Phase 5)

Re-verified 2026-08-02 against the official [subagents](https://developers.openai.com/codex/subagents) and [hooks](https://developers.openai.com/codex/hooks) references. Both surfaces are now delivered; neither is a verbatim catalog copy.

**Custom agents.** Codex reads standalone TOML files from `~/.codex/agents/` (personal) and `<project>/.codex/agents/` (project-scoped, loaded only when the project is trusted). Every file must define `name`, `description`, and `developer_instructions`; `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`, and `skills.config` are optional. Nexus-Hub's catalog agents are Markdown with `name` / `description` / `tools` frontmatter, so the integration transforms each into one TOML file, mapping the body to `developer_instructions`. Codex has no equivalent of the `tools` allowlist; it is preserved as a comment, and an agent whose tools are all non-mutating (`Read`, `Glob`, `Grep`, `LS`, `WebFetch`, `WebSearch`, `NotebookRead`) additionally gets `sandbox_mode = "read-only"`. That inference can only constrain an agent, never widen it. Agent files are manifest-owned: an existing file Nexus-Hub does not own is a user-authored agent and is never overwritten.

**Hooks.** Codex discovers hooks beside an active config layer, as either `hooks.json` or an inline `[hooks]` table in `config.toml`. Nexus-Hub writes `hooks.json` at `~/.codex/` and `<project>/.codex/`, because a single layer holding both representations makes Codex warn at startup, and because `config.toml` already carries the user's own settings. The file is a **structured merge**, not a wholesale write: a handler is Nexus-Hub-owned when its command points into the installed hooks directory, so user handlers survive an install and teardown removes only ours. A malformed `hooks.json` is never rewritten.

Codex event names line up with `catalog/hooks/settings.json` (`SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `PreCompact`, `Stop`), but its matcher vocabulary is narrower: only `Bash`, `apply_patch` (aliases `Edit` / `Write`), MCP tool names, and other local function tools are recognized. Nexus-Hub's `PowerShell`, `MultiEdit`, and `Skill` matchers have no Codex equivalent - Codex routes every shell call through `Bash` - so those groups are dropped rather than mapped onto an approximation Codex would never fire.

Each handler carries `commandWindows`, the official Windows-only command override. This maps directly onto the repo's `.sh` / `.ps1` sibling convention: the POSIX command runs the `.sh` and `commandWindows` runs the `.ps1`, so a Windows user gets the same guardrail from the same registration.

Two upstream behaviors bound what an install can promise:

- The hook engine ships **disabled**. A global install sets `[features] hooks = true` in `~/.codex/config.toml` with a line-level edit that preserves comments and every unrelated table; an explicit `hooks = false` is a deliberate user or administrator choice and is left alone. The deprecated `codex_hooks` alias counts as already enabled. A workspace install does not touch the user-global config and reports the one-line opt-in instead.
- Non-managed hooks are **inert until trusted**. Codex requires each hook to be reviewed via `/hooks` and records trust against the hook's hash, so installing a hook does not arm it. The install summary says so rather than claiming a guardrail the user does not yet have.

Teardown prunes owned handlers from `hooks.json`, deletes the file only when nothing else remained, and removes owned agent and script files. The `[features] hooks` switch is deliberately left enabled, because it is a Codex-wide setting and disabling it would also disable any hook the user registered themselves.

### Gemini CLI and Qwen native hooks (v3.15.8 Phase 6)

Re-verified 2026-08-02 against the upstream [Gemini CLI hooks reference](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/index.md) and the [Qwen Code hooks documentation](https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/). Both platforms read hooks from a `hooks` key inside their main `settings.json` - `~/.gemini/settings.json` and `.gemini/settings.json`, `~/.qwen/settings.json` and `.qwen/settings.json` - using the same nested `{event: [{matcher, hooks: [handler]}]}` shape. Qwen Code is a Gemini CLI fork, so the delivery choreography is shared; three differences are not.

**Event names.** Qwen kept the Claude-style names `catalog/hooks/settings.json` already uses. Gemini CLI renamed all of them, so its mapping is a real translation: `PreToolUse` becomes `BeforeTool`, `PostToolUse` becomes `AfterTool`, `UserPromptSubmit` becomes `BeforeAgent`, `Stop` becomes `AfterAgent`, and `PreCompact` becomes `PreCompress`. Both maps are written out explicitly rather than derived, so an upstream rename shows up as a diff instead of passing through silently.

**Matchers are regular expressions over each platform's own tool ids**, not Claude's tool names and not literals. `Bash` becomes `^(run_shell_command)$`, `Write` becomes `^(write_file)$`, and `Edit` / `MultiEdit` both become `^(replace)$`. `Skill` has no equivalent on either platform and is dropped. Only the tool events (`BeforeTool` / `AfterTool`, `PreToolUse` / `PostToolUse`) carry a matcher; the lifecycle events either always fire or match on something that is not a tool - a session source, a compact trigger - so emitting a tool matcher there would produce a registration that never matches.

**There is no `commandWindows`.** Codex's schema has an explicit Windows override slot; neither of these platforms does, and both funnel every shell call through a single `run_shell_command` tool, which collapses Nexus-Hub's separate `Bash` and `PowerShell` matchers onto one tool id. A registration therefore has to commit to one command string, so the installer picks it from the **installing host**: a Windows install registers the `.ps1` sibling and the PowerShell-flavored guardrails, a POSIX install registers the `.sh` and the Bash-flavored ones. Both siblings are copied either way, so re-running the installer on the other OS re-points the registration without touching the scripts. Qwen additionally accepts a `shell` field (`bash` | `powershell`) and a `statusMessage`, which are emitted there and omitted for Gemini CLI.

**Ownership is the handler `name`.** Both schemas carry an optional `name` for logging, so every Nexus-Hub handler is named `nexus-hub:<script-stem>`. That identity survives a path change, and it is what Gemini CLI fingerprints project hooks on, so a stable name also avoids re-triggering its untrusted-hook warning on every install. The installed hooks directory is checked as a second signal, so a handler the user renamed by hand is still recognized as ours rather than duplicated.

Because `settings.json` holds the user's entire CLI configuration rather than just hooks, the merge is more conservative than Codex's dedicated `hooks.json`: every unrelated key is preserved, the previous content is backed up beside the file, the write goes through a temp file, and a **malformed file is never rewritten**. Losing a user's model, theme, and MCP settings to a transient syntax error would be far worse than skipping the registration and logging why. Workspace-scope commands resolve through the platform's own `$GEMINI_PROJECT_DIR` / `$QWEN_PROJECT_DIR` variable (in PowerShell's `$env:` form on Windows) so a committed project `settings.json` does not carry one developer's absolute path.

Neither platform needs a feature switch - hooks are enabled by default, unlike Codex. What both have is a user-set kill switch (Qwen's top-level `disableAllHooks`, Gemini CLI's `/hooks disable-all`), so the install summary reports when `disableAllHooks` is already on rather than claiming an armed guardrail. Gemini CLI's exit-code contract also makes a broken hook non-fatal: only exit 2 blocks, and any other non-zero exit is a warning that lets the interaction proceed.

Existing gates are inherited unchanged. Gemini CLI remains enterprise-only and opt-in behind `--enterprise` after the 2026-06-18 sunset, and Qwen's global scope stays detection-gated on `~/.qwen`, so hooks ship exactly where each platform already installs. Teardown prunes owned handlers from `settings.json`, untracks the file before the manifest sweep so the user's configuration is never deleted, removes owned scripts, and drops the `hooks/` directory only if it ends up empty.

One documented second read path is deliberately unused: Gemini CLI extensions can carry hooks in `~/.gemini/extensions/<name>/hooks/hooks.json`, with `${extensionPath}` and `${/}` substitution that would solve the absolute-path and separator problems outright. It is recorded as a follow-on rather than adopted because the reference documents only `gemini extensions install` for populating that directory, it has no project scope, and shipping a directly-written extension would be an inferred write path rather than a verified one.

### Kimi custom agents and TOML hooks (v3.15.8 Phase 7)

Re-verified 2026-08-02 against the Kimi Code CLI [agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html), [hooks](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html), [built-in tools](https://www.kimi.com/code/docs/en/kimi-code-cli/reference/tools.html), and [configuration](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/config-files) references. This supersedes the pre-v3.15.8 claim that Kimi had only fixed built-in sub-agents and no reachable hook surface.

**Custom agents are a verbatim copy, not a transform.** Kimi discovers agent files as Markdown with YAML frontmatter, scanning `~/.kimi-code/agents/` (global) and `.kimi-code/agents/` (project) recursively. It explicitly accepts the shape the catalog already ships: `description` is the only required field, `name` falls back to the filename, the comma-separated `tools` form is supported specifically to "keep Claude Code-style agent files loadable", and unknown fields are ignored so foreign or newer fields do not break loading. Nexus-Hub therefore copies each `catalog/agents/*.md` unchanged, which means an agent behaves identically on Kimi and Claude. Only validation is applied: a file with no `description`, no body, or a non-kebab-case resolved name is skipped rather than shipped for Kimi to reject at load time. Files are manifest-owned, so a user-authored agent at the same path is never overwritten.

Kimi also reads the cross-tool shared `~/.agents/agents/` and project `.agents/agents/` directories. Nexus-Hub deliberately does not write either, matching the rule the Kimi integration already follows for skills: no other integration currently claims those paths, and claiming them here would create the teardown conflict the shared-path ownership rule exists to prevent.

One upstream caveat is documented rather than worked around. Kimi notes that a custom agent delegated as a sub-agent runs without the built-in "your final message is the entire handoff" framing, and suggests stating that in the agent body. Injecting a generated paragraph would make the delivered agent diverge from its catalog source, so the copy stays verbatim.

**Hooks need a comment-preserving merge, and are global-scope only.** Kimi's hooks are a `[[hooks]]` array of tables in `~/.kimi-code/config.toml` - the same file that holds the user's providers, models, permission rules, and tool switches. Three schema properties drive the implementation:

- **Only four fields are permitted** (`event`, `matcher`, `command`, `timeout`), and per the docs "extra fields will cause the config file to fail to load". There is consequently no `name` slot to carry ownership the way Gemini CLI and Qwen do, and emitting one would break the user's entire configuration.
- **Each entry holds exactly one command**, where `catalog/hooks/settings.json` groups several commands under one matcher, so one catalog group expands into several entries sharing an event and matcher. Kimi already runs identical commands only once, and the builder additionally suppresses duplicate event-matcher-command triples so the user's config is not padded.
- **`timeout` is in seconds** (1-600, default 30), not the milliseconds the Gemini-CLI-class platforms use.

Ownership is a **marker-delimited managed block** (`# >>> NEXUS_HUB_HOOKS_START >>>` to `# <<< NEXUS_HUB_HOOKS_END <<<`) appended to `config.toml`, reusing the marker-merge convention Nexus-Hub already applies to instruction files. The user's TOML is never parsed and re-emitted - only that region is spliced - so comments, table order, and whitespace outside the block survive byte-for-byte, which is what makes this viable without a non-stdlib TOML round-tripper. The merged result is validated with `tomllib` before it is committed and the write rolls back on a parse failure, and a file that was *already* invalid before the merge is left untouched so our block cannot be mistaken for the cause. `[[hooks]]` is an absolute array-of-tables header, so appending at end of file is valid regardless of what precedes it.

Event names need no translation: every event the catalog registers (`SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`, `PreCompact`) exists in Kimi under the same name. Matchers are regexes over Kimi's built-in tool names, which match Claude's exactly for the ones that matter - `Bash`, `Write`, `Edit`, `Skill` - so the mapping is near-identity. `MultiEdit` folds into `Edit`, because Kimi's `Edit` covers repeated replacement through `replace_all` rather than exposing a second tool, and `PowerShell` is dropped because Kimi routes every shell call through `Bash` on every platform, so the Bash-matched guardrails already cover Windows. As with Gemini CLI and Qwen there is no `commandWindows` slot, so the installing host selects the `.sh` or `.ps1` sibling while both are copied.

**Workspace scope carries agents but not hooks.** Kimi's project-local configuration file is `.kimi-code/local.toml`, and it documents only a `[workspace]` table holding `additional_dir`; the upstream docs place `[[hooks]]` exclusively in `~/.kimi-code/config.toml`. Writing hooks into a project file would therefore be an invented path, so the workspace hook row stays finding-only. Kimi hooks are also **fail-open by design** - a hook that errors or times out allows the action - which the install summary states so the guardrail is not mistaken for a hard barrier.

Teardown splices the managed block out of `config.toml`, untracks the file before the manifest sweep so the user's configuration is never deleted, removes owned agent and script files, and drops the `agents/` and `hooks/` directories only if they end up empty. The deprecated `~/.kimi/` product paths and the Nexus-Hub-invented `.kimi/agent.yaml` companion remain unwritten, as they have been since the v3.15.0 Phase 4 migration.

### Copilot agents and hooks, and why most of it is inherited (v3.15.8 Phase 8)

Re-verified 2026-08-03 against the [GitHub custom-agents reference](https://docs.github.com/en/copilot/reference/custom-agents-configuration), the [VS Code custom-agents doc](https://code.visualstudio.com/docs/copilot/customization/custom-agents), and the [VS Code hooks doc](https://code.visualstudio.com/docs/agent-customization/hooks). The headline finding is that **Copilot reads Claude-format customization files by default**, so most of this surface was already delivered before Phase 8 touched anything.

**Hooks are inherited, not written.** The documented default for `chat.hookFilesLocations` is:

```json
"chat.hookFilesLocations": {
  ".github/hooks": true,
  ".claude/settings.local.json": true,
  ".claude/settings.json": true,
  "~/.claude/settings.json": true
}
```

and the doc states that "VS Code uses the same hook format as Claude Code and Copilot CLI for compatibility". Nexus-Hub already merges `catalog/hooks/settings.json` into `~/.claude/settings.json` (global) and `.claude/settings.json` (workspace), so Copilot already runs those guardrails at both scopes. Six of the eight VS Code hook events (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop`) are ones the catalog registers; `SubagentStart` and `SubagentStop` it does not.

Nexus-Hub therefore writes **no** `.github/hooks/*.json`. A parallel copy would be a redundant, commit-visible duplicate in the user's repository -- the same policy concern that keeps `.github/skills/` opt-in -- for hooks Copilot already loads. `copilot`'s `hooks_supported` stays `false` and no install summary claims a Copilot-owned hook surface, because the accurate statement is that the Claude surface covers it. The dependency runs the other way now, so it is asserted by test: if the `claude` integration stopped writing those paths, Copilot's hook coverage would silently vanish.

**Project agents are inherited too.** The default workspace agent locations are `.github/agents` **and** `.claude/agents`; the `claude` integration already populates `.claude/agents`. Agent files deduplicate across levels by filename minus `.md` / `.agent.md`, with the lowest level winning, so a `.github/agents` copy would add a committed file and change nothing about what Copilot loads. None is written.

**Global agents were the one real gap, and are now delivered.** Copilot's documented user-profile agent location is `~/.copilot/agents` -- `~/.claude/agents` is *not* a Copilot agent path -- so outside a repository Copilot saw no catalog agents at all. A global install now writes `~/.copilot/agents/<name>.agent.md` verbatim, because Copilot accepts the catalog's Claude-style frontmatter as-is: `description` is the only required field, `name` is an optional display name, unrecognized frontmatter is ignored, and Claude's tool names (`Read`, `Edit`, `MultiEdit`, `Write`, `Grep`, `Glob`, `Bash`, `Task`, `WebFetch`, `TodoWrite`) are documented aliases that map onto VS Code tools. The `.agent.md` suffix is the documented extension and the cross-level dedup key, so a project `.claude/agents/planner.md` still overrides the global copy.

Validation is the only processing applied: an agent with no `description`, no body, or a prompt over Copilot's 30,000-character cap is skipped rather than shipped for Copilot to reject. Files are manifest-owned, so a user-authored agent at the same path survives and a drifted owned one is repaired. Detection accepts either a VS Code user-data directory or an existing `~/.copilot`, so a Copilot CLI user without VS Code still gets the agents, and when neither exists the whole global write is skipped with a not-detected note rather than a false claim.

The `NEXUS_HUB_COPILOT_SKILLS` selector is unchanged: still off by default, still bundle-id-or-`all`, still never overwriting a committed `.github/skills/` file.

### Hermes and the shared `.agents/skills/` path (v3.15.2 Phase 5)

Hermes is a skills-native agent: it discovers folder-per-skill `SKILL.md` directly (the open standard) and needs no instruction file. It reads skills from its native `~/.hermes/skills/` (global) / `.hermes/skills/` (project) AND from the cross-tool open-standard alias `~/.agents/skills/` (global) / `.agents/skills/` (project). Per the shared-path ownership rule that Kimi already follows, the `hermes` integration writes ONLY its native `~/.hermes/skills`; it does NOT write the shared `~/.agents/skills` (owned by `codex`) or the project `.agents/skills` (seeded by `antigravity2`'s `wire_project_surfaces` on `nexus-hub init`), so an `uninstall --platforms hermes` never fights the integration that owns each shared path. The shared-project `.agents/skills/` write path is therefore CONFIRMED present (via `antigravity2` on `nexus-hub init`), not newly added.

**Layout compatibility re-verified (v3.15.8 Phase 8).** The upstream skills doc states the discovery rule outright: "Hermes discovers skills by listing every subdirectory of the tap path and probing each for `SKILL.md`", each skill directory's name becomes its install slug, bundled `references/` / `templates/` / `scripts/` / `assets/` subdirectories ride along, and directories whose name starts with `.` or `_` are ignored. That settles the v3.15.2 ambiguity in the opposite direction from what a category-nested upstream *example* suggested: the flattened one-level layout Nexus-Hub already writes is **required**, not merely tolerated, because a category layer would put every `SKILL.md` at depth 2 where Hermes never probes. No migration was performed, and a regression test now asserts both halves -- every direct child of the skills root has a `SKILL.md`, and no `SKILL.md` exists below depth 1.

That test immediately earned its place by catching a pre-existing catalog defect: `catalog/skills/code-review/references/` held four checklist files at the *category* level, so `flatten_skills` presented `references` as a skill (with no `SKILL.md`) on every flattened platform, and the three sibling skills citing `references/<file>.md` had relative paths that did not resolve. The checklists were relocated into each citing skill's own `references/` directory per the per-skill bundling convention, and the category-level directory removed.

Wiring status: the `hermes` integration is registered in `_register_builtins()` and installs on demand via `scripts/lib/integrations/runner.py install --integrations hermes` (detection-gated on `~/.hermes` at global scope), consistent with the extended-platform tier (aider / windsurf / openclaw). It is intentionally NOT in the JSON `contract_checks` block or the installers' default `should_install` / `known_platform_keys` wiring yet; promoting Hermes to a first-class default-installed platform (with a `contract_checks` entry + installer `invoke_registry_platform` blocks) is a tracked follow-on (see the v3.15.2 known-gaps).

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

The 2026-08-02 audit leaves these items open. UNVERIFIED paths require a live probe or newly reachable primary documentation; DRIFT-ADDITIVE surfaces require v3.15.8 adapter design and tests before they enter the enforced contract:

1. The `agy` CLI global workflow directory and Antigravity global hooks path remain best-effort; official codelabs confirm skills and workflows but not those exact global destinations.
2. Antigravity 2.0 project instruction precedence between root `AGENTS.md` and `.agents/` remains unresolved.
3. Gemini IDE-specific skill discovery remains inferred from the open SKILL.md standard and Gemini CLI; confirm Code Assist independently.
4. Windsurf and OpenClaw current discovery formats lacked a reachable primary source in this cycle; retain detection-gated behavior without a MATCH claim.
5. Codex custom TOML agents and native hooks require v3.15.8 delivery, teardown, and contract tests.
6. Gemini CLI and Qwen native hooks require v3.15.8 event mapping and cross-shell parity tests. **Delivered in v3.15.8 Phase 6** - both map into the `hooks` key of their own `settings.json` via an ownership-scoped structured merge, with host-selected `.sh` / `.ps1` commands standing in for the `commandWindows` slot neither platform has. See "Gemini CLI and Qwen native hooks" above.
7. Kimi custom agents and `config.toml` `[[hooks]]` require v3.15.8 config-merge ownership and non-destructive teardown semantics. **Delivered in v3.15.8 Phase 7** - agents are a verbatim copy because Kimi accepts the Claude Code frontmatter shape, and hooks use a marker-delimited managed block in `config.toml` because Kimi's four-field-only schema has no `name` slot for ownership. Hooks are global-scope only; the project `local.toml` documents no hook path. See "Kimi custom agents and TOML hooks" above.
8. Copilot custom agents and hooks remain known additive drift and require an explicit project-file ownership policy before delivery. **Resolved in v3.15.8 Phase 8** - the ownership policy is that Copilot's own defaults already read the Claude-format files Nexus-Hub writes, so hooks (both scopes) and project agents are inherited with no owned write and no committed `.github/` duplicate; only global agents needed a write, at `~/.copilot/agents`. See "Copilot agents and hooks" above.
9. Hermes category-nested discovery was assumed to be recursive. **Resolved in v3.15.8 Phase 8** - discovery is one level ("listing every subdirectory of the tap path and probing each for `SKILL.md`"), so the existing flattened layout is required and no migration was performed.
