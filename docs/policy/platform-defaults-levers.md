# Platform Defaults Levers (living)

This is the durable, sourced record of whether each supported platform documents a settable install-time **behavioral default** that Nexus-Hub could legitimately seed, and the evidence for that answer. It is the companion to `configs/platform-defaults.json`: a platform may appear in that file ONLY if it carries a VERIFIED row here.

**Last verified**: 2026-08-30 for v4.1.2. All sixteen registered integrations were checked in this full correction pass.

## Scope boundary

This document covers **behavioral defaults only**: a reasoning-effort or thinking-budget setting, a default-model pin, an approval or autonomy policy, or an equivalent runtime behavior lever.

File-discovery paths and platform capabilities (where a platform reads skills, commands, rules, and hooks) belong to `docs/policy/platform-read-contracts.md` and its sibling `.json`. Neither document should grow into the other. A platform can have a fully-mapped read contract and still be UNVERIFIED here, and that is a normal, expected state rather than an inconsistency.

## The do-not-invent rule

A lever is recorded as VERIFIED only when a **specific official vendor document**, fetched and read, names the setting. Never a blog post, a forum thread, an aggregator, an issue tracker, or an analogy to another platform that happens to look similar.

This rule exists because Nexus-Hub has already made the mistake it prevents. The `.kimi/agent.yaml` companion file was **fabricated** rather than found in Kimi's documentation, shipped, and had to be dropped in v3.15.0 along with the whole legacy `~/.kimi/` layout. A plausible-sounding lever that a platform does not support is worse than no lever: it ships a broken default to every user of that platform, and it looks authoritative while doing so.

Two corollaries applied throughout this pass:

- **"No lever documented" is a valid and expected result.** UNVERIFIED is a finding, not a failure to search hard enough. Three of the sixteen platforms landed there and belong there.
- **A secondary source is a reason to go read the first-party page, not a finding.** The `platform-read-contracts.md` correction of 2026-08-04 records the same lesson from the Cursor global-skills claim. During this pass, every search for OpenAI Codex returned only blogs, an issue tracker, and aggregators; the recorded row comes instead from OpenAI's own configuration reference, reached by following the documented redirect chain.

## Summary table

Classification is about whether a documented lever EXISTS. Whether Nexus-Hub can actually write it is a separate question, captured in the Surface alignment column and decided in Phase 3.

| Platform (registry id) | Class | Lever keys | Config file | Surface alignment | Source | Verified |
|---|---|---|---|---|---|---|
| `aider` | VERIFIED | `model`, `reasoning-effort`, `thinking-tokens`, `yes-always`, `auto-commits` | `.aider.conf.yml` | Partial | [aider.chat](https://aider.chat/docs/config/aider_conf.html) | 2026-08-30 |
| `antigravity` | UNVERIFIED | - | - | - | [antigravity.google](https://antigravity.google/docs/ide/settings) | 2026-08-30 |
| `antigravity2` | VERIFIED | `agentMode` | `~/.gemini/antigravity-cli/settings.json` | Near | [antigravity.google](https://www.antigravity.google/docs/cli/modes/) | 2026-08-30 |
| `claude` | VERIFIED | `effortLevel`, `model`, `env.CLAUDE_CODE_EFFORT_LEVEL` (plus per-model `modelSettings`, not seeded) | `~/.claude/settings.json`, `.claude/settings.json` | Exact | [code.claude.com](https://code.claude.com/docs/en/settings), [model-config](https://code.claude.com/docs/en/model-config) | 2026-09-04 |
| `codex` | VERIFIED | `model`, `model_reasoning_effort`, `approval_policy`, `sandbox_mode` | `~/.codex/config.toml` | Exact | [learn.chatgpt.com](https://learn.chatgpt.com/docs/config-file/config-reference) | 2026-08-30 |
| `copilot` | VERIFIED | `model`, `permissions.disableBypassPermissionsMode`, `sandbox.enabled`, `sandbox.allowBypass` | `~/.copilot/settings.json` | Exact | [docs.github.com](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-config-dir-reference) | 2026-08-30 |
| `cursor` | VERIFIED | `approvalMode`, `sandbox.mode`, `sandbox.networkAccess` | `~/.cursor/cli-config.json` | Near | [cursor.com](https://cursor.com/docs/cli/reference/configuration) | 2026-08-30 |
| `gemini` | VERIFIED | `geminicodeassist.agentYoloMode` | VS Code user settings JSON | **Mismatch** | [docs.cloud.google.com](https://docs.cloud.google.com/gemini/docs/codeassist/use-agentic-chat-pair-programmer) | 2026-08-30 |
| `gemini-cli` | VERIFIED | `model.name`, `general.defaultApprovalMode` | `~/.gemini/settings.json`, `.gemini/settings.json` | Exact | [geminicli.com](https://geminicli.com/docs/cli/settings/) | 2026-08-30 |
| `hermes` | VERIFIED | `model.default`, `model.provider`, `agent.reasoning_effort`, `skills.write_approval`, `memory.write_approval` | `~/.hermes/config.yaml` | Exact | [hermes-agent.nousresearch.com](https://hermes-agent.nousresearch.com/docs/user-guide/configuration/) | 2026-08-30 |
| `kimi` | VERIFIED | `default_model`, `thinking.effort`, `default_permission_mode`, `permission.rules` | `~/.kimi-code/config.toml` | Exact | [kimi.com](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/config-files.html) | 2026-08-30 |
| `nexus-ai` | UNVERIFIED | - | - | - | see detail | 2026-08-30 |
| `openclaw` | VERIFIED | `agents.defaults.model.primary`, `agents.defaults.model.fallbacks` | `~/.openclaw/openclaw.json` | Exact | [docs.openclaw.ai](https://docs.openclaw.ai/gateway/configuration) | 2026-08-30 |
| `opencode` | VERIFIED | `model`, `small_model`, `permission`, `default_agent` | `~/.config/opencode/opencode.json`, `opencode.json` | Exact | [opencode.ai](https://opencode.ai/docs/config/) | 2026-08-30 |
| `qwen` | VERIFIED | `model.name`, `model.reasoningEffort`, `tools.approvalMode` | `~/.qwen/settings.json`, `.qwen/settings.json` | Exact | [qwenlm.github.io](https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/) | 2026-08-30 |
| `windsurf` | UNVERIFIED | - | - | - | [docs.devin.ai](https://docs.devin.ai/desktop/cascade/modes) | 2026-08-30 |
| `pi` | VERIFIED | `defaultProvider`, `defaultModel`, `defaultThinkingLevel` | `~/.pi/agent/settings.json`, `.pi/settings.json` | Exact | [github.com/earendil-works/pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/settings.md) | 2026-08-25 |

**Counts**: 14 VERIFIED, 3 UNVERIFIED, 17 total (matching the registry exactly).

**Surface alignment** answers "does the documented config file sit where Nexus-Hub already installs for this platform?"

- **Exact** - the lever's file lives in the same home directory the integration already targets.
- **Near** - same vendor home, different subdirectory or a sibling CLI config within the platform's known surface.
- **Mismatch** - the lever belongs to a different product surface than the one Nexus-Hub integrates. Phase 3 must not write it without a deliberate decision.

## Per-platform detail

### aider - VERIFIED

`.aider.conf.yml` documents `model` ("Specify the model to use for the main chat"), `reasoning-effort` ("Set the reasoning_effort API parameter"), `thinking-tokens` ("Set the thinking token budget for models that support it"), plus automation gates `yes-always`, `auto-commits`, `auto-accept-architect`, `auto-lint`, and `auto-test`. The file is searched in the home directory, then the git repo root, then the current directory, with later files taking priority.

Surface alignment is **Partial**: Nexus-Hub installs Aider at workspace scope only (project-root `CONVENTIONS.md`, no global surface), while the lever file is most naturally a home-directory or git-root file. Writing a project-root `.aider.conf.yml` is possible but would place a new file type in a user's repo, which Phase 3 should weigh deliberately.

### antigravity (Antigravity 1.0) - UNVERIFIED

Antigravity's IDE settings documentation describes only in-app configuration: it covers how the agent "interacts with your environment, executes commands, and secures your workspace" through toggles such as "Enable Terminal Sandboxing", and names **no configuration file path**, no default-model setting, and no reasoning-effort setting.

**Reason UNVERIFIED**: the vendor documents these as in-app settings-panel controls, not as a disk file a third party could seed. This is a genuine "no lever documented" result, not an incomplete search. Note that the separately-registered `antigravity2` DOES have a documented CLI settings file; the two must not be conflated.

### antigravity2 (Antigravity 2.0 + CLI) - VERIFIED

`~/.gemini/antigravity-cli/settings.json` is documented as a plain JSON settings file. The current modes reference documents `agentMode` with values `default`, `accept-edits`, and `plan`: `default` asks for confirmation before tool execution, `accept-edits` automatically approves edit tools, and `plan` disables tool use. Nexus-Hub seeds `{"agentMode": "default"}` only when the key is absent.

**Important limitation, recorded explicitly**: the page documents **no default-model key and no reasoning-effort key**. The verified lever here is an autonomy policy only. The separate settings reference names `toolPermission`, `artifactReviewPolicy`, `enableTerminalSandbox`, and `allowNonWorkspaceAccess`, but does not provide a stable, safe value domain for automatic seeding, so those keys are deliberately omitted.

Surface alignment is **Near**: the integration's `global_dir` is `~/.gemini/config`, while the lever file is `~/.gemini/antigravity-cli/settings.json`. Both sit inside the `~/.gemini` home the read contract already records for this platform.

### claude - VERIFIED

Seeded in Phase 1 and re-stated here for completeness. `settings.json` documents `effortLevel` ("Set a default effort level for models without a saved level of their own"; the settings page now delegates the definition to `settings-reference` and the accepted values to `model-config`, which on 2026-09-05 lists `low`, `medium`, `high`, or `xhigh` for `effortLevel` and states that `max` "isn't accepted in either key", meaning `effortLevel` or `modelSettings`). The same page documents `CLAUDE_CODE_EFFORT_LEVEL` as taking precedence over settings and `/effort`, accepting a level name or `auto`, and as the one persistent way to set `max`: "Unless you set it through the `CLAUDE_CODE_EFFORT_LEVEL` environment variable, Claude Code applies `max` to the current session only." So the two levers do not share one value set (four levels in the settings keys, five in the environment variable); Nexus-Hub seeds `high` on both, which every documented surface accepts. Corrected 2026-09-05 for v4.7.0: the 2026-09-04 statement had the two surfaces the other way round (`max` in the settings key, not in the variable), which is what the vendor page said the opposite of; the decision note is `docs/releases/v4/v4.7/development/effort-level-contract.md`. A new per-model `modelSettings` key stores the level `/effort` writes and is not seeded. Re-verified 2026-09-04 (the 2026-08-30 statement quoted "Accepts low, medium, high, or xhigh", which is no longer what the vendor page says), `model` (read once at session start), and `env` ("Environment variables applied to every session and to subprocesses Claude Code spawns from it"). The same page states that `CLAUDE_CODE_EFFORT_LEVEL` **overrides** `effortLevel` for a session, which is why `configs/platform-defaults.json` declares both together. Documented scopes: `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`.

**Provenance note worth keeping**: the obvious URL (`docs.claude.com/en/docs/claude-code/settings`) returns a 301 to a different host. The canonical location is `code.claude.com/docs/en/settings`. Recording the redirecting URL would have baked provenance rot into the file on its first day, which is the concrete argument for fetching every URL rather than citing one from memory.

### codex - VERIFIED

`~/.codex/config.toml` (user-level) or `.codex/config.toml` (project-scoped) documents `model`, `model_reasoning_effort` (`minimal | low | medium | high | xhigh`), `approval_policy` (`untrusted | on-request | never`, or a granular object), and `sandbox_mode` (`read-only | workspace-write | danger-full-access`).

**Constraint that matters for Phase 3**: the documentation states that `approval_policy`, `sandbox_mode`, and related keys **cannot be overridden from a project-scoped config file** and must be set at user level. A project-scoped write of those keys would be silently inert.

This row is the pass's clearest illustration of the do-not-invent rule in action. Every search result for these keys was a blog, a cheat sheet, an aggregator, or a GitHub issue. The values above come from OpenAI's own configuration reference, reached by following two documented 308 redirects from `developers.openai.com/codex/config-reference`.

### copilot - VERIFIED

The GitHub Copilot **CLI** configuration directory reference documents `~/.copilot/settings.json` (or `$COPILOT_HOME/settings.json`) with a `model` key ("AI model to use. Set to 'auto' to let Copilot pick the best available model automatically"), plus `permissions.disableBypassPermissionsMode`, `sandbox.enabled`, and `sandbox.allowBypass`.

Surface alignment is **Exact** after the 2026-08-30 contract correction. The Copilot integration now owns native personal instructions, agents, and hooks under `~/.copilot`, while the defaults writer seed-merges `~/.copilot/settings.json`. Existing user keys remain authoritative.

### cursor - VERIFIED

The Cursor CLI configuration reference documents a JSON schema whose keys include `approvalMode` (`"allowlist" | "auto-review" | "unrestricted"`), `sandbox.mode`, `sandbox.networkAccess`, `editor.vimMode`, `permissions.allow`, and `permissions.deny`. Paths: `~/.cursor/cli-config.json` globally (`$env:USERPROFILE\.cursor\cli-config.json` on Windows) and `<project>/.cursor/cli.json` for **permissions only**.

**Two limitations recorded deliberately.** First, the documentation states there is **no default-model mechanism in the config file**; a `model` field exists as "Selected model configuration" but model selection happens through the `/model` slash command at runtime. Do not seed a Cursor default model on the strength of that field name alone. Second, only permissions are configurable at project level, so any behavioral default Nexus-Hub seeds for Cursor must go to the global file.

### gemini - VERIFIED (with a surface mismatch)

Gemini Code Assist now documents `geminicodeassist.agentYoloMode` in the VS Code user settings JSON. Setting it to `true` enables automatic approval for agent actions in trusted workspaces. This is a real persistent lever for the legacy IDE surface and replaces the prior UNVERIFIED finding.

**Surface alignment is Mismatch.** The key belongs to VS Code's OS-specific user-settings file, not `~/.gemini/settings.json` and not a documented project `.vscode/settings.json` contract. Nexus-Hub's `gemini` integration owns the shared `~/.gemini` content surface, not the editor's user profile. `configs/platform-defaults.json` therefore records the lever as verified but `not-writable`.

**Collision warning for Phase 3**: because both integrations resolve to the same `~/.gemini` home, a `~/.gemini/settings.json` default written on behalf of `gemini-cli` **will also be read by anything else using that home**. Phase 3 must treat the `~/.gemini/settings.json` write as belonging to exactly one platform id to avoid two integrations racing to own one file.

### gemini-cli - VERIFIED

Google's own configuration reference documents `model.name` ("The Gemini model to use for conversations", default `undefined`) and `general.defaultApprovalMode` (enum `"default" | "auto_edit" | "plan"`, default `"default"`; the docs note YOLO mode is command-line only). A thinking budget exists but is nested per model alias at `modelConfigs.aliases[*].modelConfig.generateContentConfig.thinkingConfig.thinkingBudget` rather than as a top-level setting, so it is **not** a clean top-level lever and is recorded but not recommended for seeding. Paths: `~/.gemini/settings.json` (user), `.gemini/settings.json` (project), plus documented system-wide paths per OS.

Note that this platform is **enterprise-only** in Nexus-Hub post-2026-06-18 and installs only under the `--enterprise` flag. The lever is real; its audience is narrow.

### hermes - VERIFIED

`~/.hermes/config.yaml` is documented as the primary config file, with resolution order CLI arguments, then `config.yaml`, then `.env`, then built-in defaults. Documented keys include `model.default`, `model.provider`, `agent.reasoning_effort` (`none | minimal | low | medium | high | xhigh | max | ultra`), and the approval gates `skills.write_approval`, `skills.guard_agent_created`, and `memory.write_approval`.

**Drift corrected in v3.17.0.** The 2026-08-08 record and seeded default used top-level `reasoning_effort`. The current first-party page nests the global default under `agent.reasoning_effort` and states that `/reasoning <level> --global` persists to that path. The source manifest and regression test now enforce the nested shape.

Surface alignment is **Exact**: `~/.hermes` is precisely the home Nexus-Hub already detection-gates this integration on.

### kimi - VERIFIED

`~/.kimi-code/config.toml` (or `$KIMI_CODE_HOME/config.toml`) documents `default_model` ("Default model alias; must be defined in models"), a `[thinking]` table with `effort` ("Thinking effort level (for example low, medium, high, xhigh, max)") plus `enabled` and `keep`, `default_permission_mode` (`manual | yolo | auto`), and `[[permission.rules]]` array tables with required `decision` and `pattern` fields.

**This row is the redemption of the precedent that motivates this whole document.** The fabricated `.kimi/agent.yaml` was dropped in v3.15.0; the real, documented Kimi lever is a TOML config at `~/.kimi-code/`, which is exactly the path v3.15.0 migrated the integration to. The lesson holds in both directions: the invented file was wrong, and the correct one was findable by reading the vendor's documentation.

### nexus-ai - UNVERIFIED

**Reason UNVERIFIED**: the project's repository (`github.com/bendourthe/Nexus-AI`) is **private**, so no publicly-citable first-party document exists. An authenticated inspection of the repository found no user-facing behavioral-default configuration surface: the `configs/` directory contains build tooling only (dependency-cruiser, stryker, vitest), a code search for documentation of a `.nexus-ai` home config returned zero results, and no VS Code `contributes.configuration` block was found.

This is recorded as UNVERIFIED rather than "not applicable" so a future reader can tell that it **was** checked. Should Nexus-AI later document a settings surface, this row becomes verifiable; note that a private-repo citation is auditable only by the maintainer, which is a legitimate but weaker form of evidence than a public vendor page.

### openclaw - VERIFIED

`~/.openclaw/openclaw.json` (JSON5, so comments and trailing commas are permitted) documents `agents.defaults.model.primary` and `agents.defaults.model.fallbacks`, with `agents.defaults` described as holding agent-loop behavior.

Surface alignment is **Exact**: the adapter reads `~/.openclaw/openclaw.json` to resolve `agents.defaults.workspace`, then installs `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, and native skills at that configured workspace. It falls back to `~/.openclaw/workspace` only when no environment or config override exists.

**Source-selection note**: searches for this platform surfaced several community documentation mirrors (`clawdocs.org`, `getopenclaw.ai`, `open-claw.bot`). Only `docs.openclaw.ai` was used, and only it should be used in future re-verification.

### opencode - VERIFIED

`opencode.json` documents `model` (primary model selection), `small_model` ("lightweight model for tasks like title generation"), `permission` (controls approval requirements; accepts values such as `"ask"`), `default_agent`, and `subagent_depth`. Global path `~/.config/opencode/opencode.json`, project path `opencode.json` in the project root, and the documentation states configurations **merge** rather than replace, with project settings overriding global defaults.

Surface alignment is **Exact**: `~/.config/opencode` is precisely the integration's `global_dir`. The documented merge semantics are also the friendliest of any platform in this table for a non-clobbering write.

### pi - VERIFIED

Added to the registry on 2026-08-25 and classified in the same change, so it carries no status from the v3.19.0 pass above.

`~/.pi/agent/settings.json` (global) and `.pi/settings.json` (project) are documented as JSON settings files where "project settings override global settings". The Model & Thinking table documents `defaultProvider` ("Default provider (e.g., `\"anthropic\"`, `\"openai\"`)"), `defaultModel` ("Default model ID"), and `defaultThinkingLevel` with the enumerated values `off | minimal | low | medium | high | xhigh | max`. Also documented: `thinkingBudgets` (per-level token budgets) and `hideThinkingBlock`.

`defaultThinkingLevel` is the closest analogue in the table to Claude's `effortLevel` and Qwen's `model.reasoningEffort`: a first-class top-level effort scalar, in a JSON file at a path the integration already targets, with `medium` among its documented values. Surface alignment is Exact.

Two keys are deliberately NOT seeded. `defaultModel` is a bare model ID with no documented default and no vendor-documented safe self-selecting value, and `defaultProvider` scopes it; pinning either would hand a fresh install a provider and model the user's credentials may not reach. That is precisely the failure the do-not-invent rule exists to prevent, so both are recorded under `omitted` rather than guessed.

One caveat belongs on the record because it changes when a seeded value takes effect: pi gates project-local `.pi` resources behind its own project-trust prompt, and non-interactive runs fall back to the global `defaultProjectTrust`. A value seeded into the GLOBAL settings file is unaffected; a project-scoped one is inert until the user trusts the folder. Nexus-Hub seeds the global file only and never pre-trusts a folder on the user's behalf.

### qwen - VERIFIED

`~/.qwen/settings.json` (user) and `.qwen/settings.json` (project) document `model.name` ("The Qwen model to use for conversations"), `model.reasoningEffort` ("How hard reasoning-capable models think, applied across all providers", values `low | medium | high | xhigh | max`), and `tools.approvalMode` (`plan | default | auto-edit | auto | yolo`, documented default `"auto"`). Also documented: `model.maxToolCalls`, `model.maxWallTimeSeconds`, and `fastModel`.

Qwen is the closest structural analogue to Claude in this table: a first-class, top-level reasoning-effort scalar plus a model pin, both in a JSON settings file at a path Nexus-Hub already targets.

### windsurf - UNVERIFIED

**Reason UNVERIFIED**: mode, model, and approval behavior are documented as in-app controls only. The current documentation states modes are switched "using the mode selector below the input box, or by using the keyboard shortcut", names no configuration file path, and points to a permissions page rather than a disk-based setting. Administrator-set default models are described as a team-admin dashboard control, not a file a third-party installer could write.

**Rebrand finding, recorded because it is load-bearing**: `docs.windsurf.com` now issues a **307 redirect to `docs.devin.ai/desktop/...`**. This is first-hand confirmation of the Cognition rebrand that `AGENTS.md` flags as reported-but-unconfirmed in its dated 2026-07-08 roster-verification note. The integration is already marked deprecated-but-served and detection-gated; this finding does not change that posture, but the AGENTS.md note can now cite a first-party observation rather than third-party reporting.

## What this means for the defaults file

Phase 3 declares the VERIFIED levers in `configs/platform-defaults.json`. Three constraints from this pass carry into that work:

1. **A VERIFIED classification is permission to consider a platform, not permission to write a file.** The Surface alignment column remains the gate. Copilot became Exact only after the integration deliberately adopted native `~/.copilot` surfaces.
2. **Do not seed a key the vendor does not document just because a sibling platform has one.** `antigravity2` documents `agentMode` but no model or effort key, and `cursor` has no config-file default-model mechanism. Both are VERIFIED only for the levers their current sources name.
3. **`~/.gemini/settings.json` must be owned by exactly one platform id.** `gemini` and `gemini-cli` share a home; two integrations writing one file is a collision, not a convenience.

## Re-verification log

Lever re-verification rides along with the existing `platform-contract-verification` remit (wired in Phase 4). The read-contract's `meta.verified_for_version` marker **hard-gates** a release; this document's freshness does **not**, and that asymmetry is deliberate: a vendor renaming a setting should surface promptly, but it should not wedge an unrelated release.

| Date | Version | Scope | Outcome |
|---|---|---|---|
| 2026-09-01 | v4.4.0 | Ride-along on the FULL read-contract re-verification (claude, cursor, codex, copilot, antigravity, gemini-cli, opencode, openclaw, qwen, kimi, windsurf re-fetched) | No lever drift signal on any vendor page visited: no key rename, no config-path move, and one already-recorded redirect (OpenAI Codex 308 to `learn.chatgpt.com`). SCOPE LIMIT, stated plainly: this pass targeted READ-PATHS. Lever rows were re-checked only incidentally while those pages were open, so the remaining integrations were NOT re-fetched and carry no status claim from this cycle; their rows are carried forward from the 2026-08-30 full correction pass. ONE INSTALLER DEFAULT DID CHANGE THIS RELEASE, and it is the only entry in this log's history to say so: Claude Code's `effortLevel` and `env.CLAUDE_CODE_EFFORT_LEVEL` were raised from `medium` to `high` in `configs/platform-defaults.json`. That was a deliberate Nexus-Hub product decision, NOT vendor drift -- both key names and the `~/.claude/settings.json` write path are unchanged and re-confirmed. `sync_platform_defaults.py --check` reports 13 platforms with all derived artifacts in sync. |
| 2026-08-30 | v4.1.2 | All sixteen registered integrations, full correction pass | 13 VERIFIED, 3 UNVERIFIED. Antigravity CLI now seeds the documented `agentMode: default` value. Copilot alignment is Exact after adopting native `~/.copilot` surfaces. OpenClaw alignment is Exact because the adapter reads `openclaw.json` to resolve the configured workspace. Nexus-AI remains UNVERIFIED. |
| 2026-08-28 | v4.1.2 | Ride-along on the read-contract targeted re-fetch (claude, cursor, codex) | No lever drift signal on the pages visited for read-paths: no key rename, no config-path move, no new cross-host redirect. SCOPE LIMIT: the other thirteen integrations were NOT re-fetched and carry no status claim from this cycle. No installer default changed. |
| 2026-08-28 | v4.1.1 | Ride-along on the read-contract targeted re-fetch (claude, cursor, codex) | No lever drift signal on the pages visited for read-paths: no key rename, no config-path move, no new cross-host redirect. SCOPE LIMIT: the other thirteen integrations were NOT re-fetched and carry no status claim from this cycle. No installer default changed. |
| 2026-08-28 | v4.1.0 | All sixteen registered integrations, full pass | 13 VERIFIED, 3 UNVERIFIED. All thirteen public first-party sources retained their documented key names and config paths, with no new cross-host redirect. Antigravity IDE and Windsurf/Devin still expose UI-only behavior without a seedable file; Nexus-AI remains privately auditable only. No installer default changed. |
| 2026-08-23 | v3.19.2 | Ride-along on the read-contract re-fetch (claude, codex, cursor, antigravity, gemini-cli, opencode, qwen, kimi) | No lever drift signal on the pages visited for read-paths: no key rename, no config-path move, no new cross-host redirect. SCOPE LIMIT: the other eight integrations were NOT re-fetched and carry no status claim from this cycle. No installer default changed. |
| 2026-08-22 | v3.19.0 | All sixteen registered integrations, full pass | 13 VERIFIED, 3 UNVERIFIED. All public first-party sources retained their documented key names and config paths. Antigravity IDE and Windsurf/Devin still document only UI behavior without a seedable file; Nexus-AI remains privately auditable only. No installer default changed. |
| 2026-08-17 | v3.17.4 | All sixteen registered integrations, full pass | 13 VERIFIED, 3 UNVERIFIED. Every public first-party source returned HTTP 200 and retained the expected key or documented UI-only posture. OpenClaw still documents `agents.defaults`, model fallbacks, and `openclaw.json`; Nexus-AI remains privately auditable only. No installer default changed. |
| 2026-08-16 | v3.17.3 | All sixteen registered integrations, full pass | 13 VERIFIED, 3 UNVERIFIED. All documented keys and config paths remain valid. Cursor still documents `approvalMode` and sandbox controls separately from hook responses; Antigravity IDE and Windsurf still expose UI behavior without a seedable config file, and Nexus-AI remains privately auditable only. No installer default changed. |
| 2026-08-15 | v3.17.2 | All sixteen registered integrations, full pass | 13 VERIFIED, 3 UNVERIFIED. Existing seeded keys and write paths remain valid. Additive documentation drift clarifies Codex granular approvals, Cursor `approvalMode`, Antigravity CLI `toolPermission` and `artifactReviewPolicy`, Hermes `approvals.mode`, and Copilot's separate editable-settings and saved-approvals files. No installer default changed, and the retired autonomy controller is not replaced. |
| 2026-08-15 | v3.17.0 | All sixteen registered integrations, full pass | 13 VERIFIED, 3 UNVERIFIED. Gemini Code Assist moved from UNVERIFIED to VERIFIED with a surface mismatch after its docs added `geminicodeassist.agentYoloMode`. Hermes remained VERIFIED but its reasoning key drifted from top-level `reasoning_effort` to `agent.reasoning_effort`; the source manifest and test were corrected. All other key names, paths, and source hosts remained aligned. |
| 2026-08-08 | v3.16.0 | All sixteen registered integrations, first pass | 12 VERIFIED, 4 UNVERIFIED. Two doc-host redirects discovered and followed (Claude 301 to `code.claude.com`; OpenAI Codex 308 chain to `learn.chatgpt.com`). One rebrand confirmed first-hand (`docs.windsurf.com` 307 to `docs.devin.ai`). |
| 2026-08-12 | v3.16.6 | Targeted ride-along on the read-contract pass (claude, codex only) | No drift signal observed on either vendor's docs during the read-contract fetches: no key rename, no config-path move, no new redirect. The other fourteen integrations were not re-fetched (targeted patch pass); the full lever re-verification rides with the full read-contract pass owed at v3.17.0. |

| 2026-08-14 | v3.16.8 | Targeted ride-along on the read-contract pass (claude, codex only) | No drift signal on either vendor's docs during the read-contract fetches: no key rename, no config-path move, and both source URLs resolved directly with no cross-host redirect. The other fourteen integrations were NOT re-fetched (targeted patch pass) and carry no status claim from this cycle. The full lever re-verification still rides with the full read-contract pass owed at v3.17.0. |

| 2026-08-21 | v3.18.0 | Ride-along on the FULL read-contract pass (claude, codex, cursor, antigravity, gemini-cli, opencode, qwen, kimi) | No lever drift signal on any vendor page visited: no key rename, no config-path move, and one already-recorded redirect (OpenAI Codex 308 to `learn.chatgpt.com`). SCOPE LIMIT, stated plainly: lever rows were re-checked only incidentally while those pages were open for read-path verification, and the eight remaining integrations were NOT re-fetched, so they carry no status claim from this cycle. Two vendor doc URLs on record returned 404 (qwen skills, kimi skills) and their current pages were located by search; both documented the same paths. No installer default changed. |

| 2026-08-22 | v3.18.1 | Ride-along on the FULL read-contract pass (claude, codex, cursor, antigravity, gemini-cli, opencode, qwen, kimi) | No lever drift signal on any vendor page visited: no key rename, no config-path move, and no new cross-host redirect. SCOPE LIMIT, stated plainly: this release's pass targeted READ-PATHS. Lever rows were re-checked only incidentally while those pages were open, and the eight remaining integrations were NOT re-fetched, so they carry no status claim from this cycle. One positive documentation finding, recorded here because it affects a Cursor row's evidence base rather than its keys: `cursor.com/docs/skills` now documents the user-global `~/.cursor/skills/` and `~/.agents/skills/` paths outright, where the rules page previously documented no user-global filesystem path at all. No installer default changed. |
| 2026-08-22 | v3.18.3 | Ride-along on the DELTA read-contract pass (claude, opencode, kimi re-fetched) | No BEHAVIORAL-lever drift signal on the three vendor pages visited: no key rename, no config-path move, no new cross-host redirect. SCOPE LIMIT, stated plainly: this pass targeted read-paths for three platforms, so the other thirteen integrations were NOT re-fetched and carry no status claim from this cycle - their rows are carried forward from the 2026-08-21 full pass. Separately and NOT to be confused with this table: four platforms (opencode, kimi, hermes, nexus-ai) were surveyed this cycle for INVOCATION-POLICY levers, a different contract living in skill-invocation-policy-levers.md, closing v3.17 DF-1. That survey says nothing about the behavioral defaults this table tracks. No installer default changed. |
| 2026-09-04 | v4.4.5 | Ride-along on the FULL read-contract pass (13 platforms enumerated, 12 re-fetched); Claude lever pages fetched directly (settings, settings-reference, model-config) | DRIFT on claude: `effortLevel` now documents `max` and the definition moved to `settings-reference` / `model-config`; `CLAUDE_CODE_EFFORT_LEVEL` does NOT accept `max`; new `modelSettings` per-model key. Seeded `high` values remain valid on both keys, so `configs/platform-defaults.json` changes only its `doc_statement`, `source_url`, and `verified` date. No other vendor page visited showed a key rename, config-path move, or host redirect. |
| 2026-09-05 | v4.7.0 | Targeted re-fetch of the Claude Code model-config and settings pages for the effort-level contract (Phase 1 sub-task 1.1); other platforms not re-fetched this pass | CORRECTED a recorded-statement inversion: the settings keys (`effortLevel`, `modelSettings`) accept `low`, `medium`, `high`, `xhigh` and reject `max`; `CLAUDE_CODE_EFFORT_LEVEL` accepts a level name or `auto` and is the persistent path to `max`. Seeded value `high` is valid on both, so no seeded value changed. `sync_platform_defaults.py --check` clean after `--apply`. |

When re-verifying, check three things per platform: that the documented key names are unchanged, that the config file path is unchanged, and that the source URL still resolves without a redirect to a new host. A redirect is not cosmetic; it is the earliest signal that a vendor has reorganized or renamed a product.
