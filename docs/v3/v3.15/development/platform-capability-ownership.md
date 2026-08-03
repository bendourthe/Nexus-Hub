# Platform Capability Ownership Contract

**Version:** v3.15.8
**Plan:** [v3.15.8 Platform Capability Parity and GitHub Usage Monitor](../plans/v3.15.8-platform-parity-and-github-usage-monitor.md)
**Source finding:** [DF-9](../known-gaps.md#df-9---additive-platform-capability-drift-is-deferred-to-v3158)
**Verified:** 2026-08-02

## Decision

This matrix converts the v3.15.7 additive-drift audit into explicit delivery and lifecycle contracts. Phase 1 does not activate any new agent or hook path. A row becomes enforceable only after the named implementation phase supplies its writer, collision behavior, manifest record, repair path, teardown path, and cross-shell tests. Existing skills, commands, instructions, and deny controls remain unchanged.

## Ownership Rules

- Folder-per-file surfaces use manifest ownership. Nexus-Hub creates only absent destinations, records each owned path, repairs missing or drifted owned files, and removes only manifest-owned files.
- Shared JSON or TOML files require structured merge. Nexus-Hub entries need stable identities, backups before mutation, idempotent upgrade, rollback on parse or write failure, and teardown that removes only owned entries.
- User-owned collisions are preserved. An existing destination with no matching Nexus-Hub ownership record is never overwritten or deleted.
- Finding-only rows are documentation, not runtime promises. They must stay out of `contract_checks`, install summaries, and positive verification claims until their implementation and lifecycle tests land.
- Shared aliases keep one writer. Hermes reads `.agents/skills`, but Codex owns the global alias and Antigravity owns the project alias.

## Capability Matrix

| Platform / capability | Scope | Source -> destination | Schema / event | Source artifact | Write mode | Owner | Collision / upgrade | Repair / teardown | Required tests | State / owner phase |
|---|---|---|---|---|---|---|---|---|---|---|
| Codex custom agents | global | `catalog/agents/*.yaml` -> `~/.codex/agents/*.toml` | Official TOML custom-agent schema; exact field mapping pending Phase 5 re-verification | Catalog agent YAML, transformed locally | Per-file generated copy | `codex` | Preserve user files; stable generated names; replace only manifest-owned files after successful validation | Manifest hash drives repair; teardown removes owned TOML files only | Schema, collision, idempotent upgrade, repair, teardown, installer parity | Finding-only; Phase 5 |
| Codex custom agents | workspace | `catalog/agents/*.yaml` -> `.codex/agents/*.toml` | Official TOML custom-agent schema; project discovery pending Phase 5 re-verification | Catalog agent YAML, transformed locally | Per-file generated copy | `codex` | Preserve user files; stable generated names; replace only manifest-owned files after successful validation | Manifest hash drives repair; teardown removes owned TOML files only | Schema, collision, idempotent upgrade, repair, teardown, installer parity | Finding-only; Phase 5 |
| Codex native hooks | global | `catalog/hooks/*` -> `~/.codex/hooks.json` and referenced scripts | Official Codex hook events; event mapping pending Phase 5 | Catalog Bash and PowerShell hook siblings plus generated JSON | Structured JSON merge plus owned script copies | `codex` | Stable Nexus-Hub hook IDs; preserve unknown fields and user hooks; reject malformed JSON | Repair re-merges owned IDs; teardown removes owned IDs and owned scripts only | Event mapping, malformed JSON, duplicate ID, cross-shell parity, rollback, teardown | Finding-only; Phase 5 |
| Codex native hooks | workspace | `catalog/hooks/*` -> `.codex/hooks.json` and referenced scripts | Official Codex hook events; event mapping pending Phase 5 | Catalog Bash and PowerShell hook siblings plus generated JSON | Structured JSON merge plus owned script copies | `codex` | Stable Nexus-Hub hook IDs; preserve unknown fields and user hooks; reject malformed JSON | Repair re-merges owned IDs; teardown removes owned IDs and owned scripts only | Event mapping, malformed JSON, duplicate ID, cross-shell parity, rollback, teardown | Finding-only; Phase 5 |
| Gemini CLI native hooks | global | `catalog/hooks/*` -> `~/.gemini/settings.json` hook entries and referenced scripts | Verified Gemini CLI hook schema and supported event subset, to be fixed in Phase 6 | Catalog Bash and PowerShell hook siblings plus generated JSON | Structured JSON merge plus owned script copies | `gemini-cli` | Preserve settings, extensions, future fields, and user hooks; stable Nexus-Hub IDs | Repair re-merges owned IDs; teardown removes owned IDs and owned scripts only | Missing/malformed settings, future fields, duplicate IDs, cross-shell parity, rollback | Finding-only; Phase 6 |
| Gemini CLI native hooks | workspace | `catalog/hooks/*` -> `.gemini/settings.json` hook entries and referenced scripts | Verified Gemini CLI hook schema and supported event subset, to be fixed in Phase 6 | Catalog Bash and PowerShell hook siblings plus generated JSON | Structured JSON merge plus owned script copies | `gemini-cli` | Preserve settings, extensions, future fields, and user hooks; stable Nexus-Hub IDs | Repair re-merges owned IDs; teardown removes owned IDs and owned scripts only | Missing/malformed settings, future fields, duplicate IDs, cross-shell parity, rollback | Finding-only; Phase 6 |
| Qwen native hooks | global | `catalog/hooks/*` -> `~/.qwen/settings.json` hook entries and referenced scripts | Verified Qwen hook schema and supported event subset, to be fixed in Phase 6 | Catalog Bash and PowerShell hook siblings plus generated JSON | Structured JSON merge plus owned script copies | `qwen` | Preserve Qwen settings and user hooks; stable Nexus-Hub IDs; never emit deprecated TOML commands | Repair re-merges owned IDs; teardown removes owned IDs and owned scripts only | Missing/malformed settings, future fields, duplicate IDs, cross-shell parity, rollback | Finding-only; Phase 6 |
| Qwen native hooks | workspace | `catalog/hooks/*` -> `.qwen/settings.json` hook entries and referenced scripts | Verified Qwen hook schema and supported event subset, to be fixed in Phase 6 | Catalog Bash and PowerShell hook siblings plus generated JSON | Structured JSON merge plus owned script copies | `qwen` | Preserve Qwen settings and user hooks; stable Nexus-Hub IDs; never emit deprecated TOML commands | Repair re-merges owned IDs; teardown removes owned IDs and owned scripts only | Missing/malformed settings, future fields, duplicate IDs, cross-shell parity, rollback | Finding-only; Phase 6 |
| Kimi custom agents | global | `catalog/agents/*` -> `~/.kimi-code/agents/` only if official user-authored agents remain supported | Current Kimi Code CLI agent schema; detection and exact file format require Phase 7 re-verification | Catalog agent definitions, transformed only after schema approval | Per-file generated copy | `kimi` | Preserve user agents; never restore `~/.kimi` or synthesize `.kimi/agent.yaml` | Manifest repair and owned-file teardown only | Official-schema fixture, detection gate, deprecated-path negative, collision, teardown | Finding-only; Phase 7 |
| Kimi custom agents | workspace | `catalog/agents/*` -> `.kimi-code/agents/` only if official user-authored agents remain supported | Current Kimi Code CLI agent schema; exact project scope requires Phase 7 re-verification | Catalog agent definitions, transformed only after schema approval | Per-file generated copy | `kimi` | Preserve user agents; never restore `.kimi/agent.yaml` | Manifest repair and owned-file teardown only | Official-schema fixture, deprecated-path negative, collision, teardown | Finding-only; Phase 7 |
| Kimi native hooks | global | `catalog/hooks/*` -> owned `[[hooks]]` entries in `~/.kimi-code/config.toml` | Current Kimi TOML hook schema and supported events, to be fixed in Phase 7 | Catalog Bash and PowerShell hook siblings plus generated TOML entries | TOML-aware structured merge plus owned script copies | `kimi` | Stable IDs; preserve comments and unrelated entries where parser permits; backup and rollback on failure | Repair re-merges owned entries; teardown removes owned entries and scripts only | Malformed TOML, duplicate, conflict, comment preservation, rollback, cross-shell parity | Finding-only; Phase 7 |
| Kimi native hooks | workspace | `catalog/hooks/*` -> owned `[[hooks]]` entries in `.kimi-code/config.toml` | Current Kimi TOML hook schema and supported events, to be fixed in Phase 7 | Catalog Bash and PowerShell hook siblings plus generated TOML entries | TOML-aware structured merge plus owned script copies | `kimi` | Stable IDs; preserve comments and unrelated entries where parser permits; backup and rollback on failure | Repair re-merges owned entries; teardown removes owned entries and scripts only | Malformed TOML, duplicate, conflict, comment preservation, rollback, cross-shell parity | Finding-only; Phase 7 |
| Copilot custom agents | global | `catalog/agents/*` -> `~/.copilot/agents/*.agent.md` | GitHub custom-agent Markdown frontmatter; supported global scope to be re-verified in Phase 8 | Catalog agent definitions, transformed locally | Per-file generated copy | `copilot` | Detection-gated; preserve user agents; never claim installation when Copilot is absent | Manifest repair and owned-file teardown only | Frontmatter, absence gate, collision, summary, repair, teardown, installer parity | Finding-only; Phase 8 |
| Copilot custom agents | workspace | `catalog/agents/*` -> `.github/agents/*.agent.md` | GitHub custom-agent Markdown frontmatter | Catalog agent definitions, transformed locally | Opt-in, never-overwrite per-file generation | `copilot` | Preserve existing committed files and current skill selector policy; replace only manifest-owned files | Manifest repair and owned-file teardown only | Frontmatter, opt-in, collision, summary, repair, teardown, installer parity | Finding-only; Phase 8 |
| Copilot native hooks | global | No supported Nexus-Hub destination proven | GitHub/VS Code hook schema; global scope is not promised | None until Phase 8 proves an official global contract | No write | None | No mutation of VS Code user settings or organization policy | No repair or teardown because nothing is owned | Negative path and no-false-summary tests | Finding-only; Phase 8 |
| Copilot native hooks | workspace | `catalog/hooks/*` -> `.github/hooks/*.json` and referenced scripts | Verified GitHub/VS Code hook events and JSON schema, to be fixed in Phase 8 | Catalog Bash and PowerShell hook siblings plus generated JSON | Structured or marker-owned JSON plus owned script copies | `copilot` | Preserve user and organization policy; stable Nexus-Hub IDs; unsupported enterprise settings remain finding-only | Repair re-merges owned IDs; teardown removes owned IDs and scripts only | Event schema, malformed JSON, policy collision, absence gate, cross-shell parity, teardown | Finding-only; Phase 8 |
| Hermes skill layout | global | `catalog/skills/<category>/<name>/` -> flattened `~/.hermes/skills/<name>/`; shared `~/.agents/skills/` remains Codex-owned | Folder-per-skill `SKILL.md`; recursive category nesting is upstream-supported but not required | Catalog skill folders and command-as-skill wrappers | Existing flattened folder copy | `hermes` for native path; `codex` for shared alias | Native destination is manifest-owned; shared alias is read-only to Hermes | Existing manifest repair/teardown applies only to `~/.hermes/skills` | Recursive-discovery proof, flattened-layout regression, shared-owner teardown | Enforceable existing flattened delivery; Phase 8 re-verifies nesting claim |
| Hermes skill layout | workspace | `catalog/skills/<category>/<name>/` -> flattened `.hermes/skills/<name>/`; shared `.agents/skills/` remains Antigravity-owned | Folder-per-skill `SKILL.md`; recursive category nesting is upstream-supported but not required | Catalog skill folders and command-as-skill wrappers | Existing flattened folder copy | `hermes` for native path; `antigravity2` for shared alias | Native destination is manifest-owned; shared alias is read-only to Hermes | Existing manifest repair/teardown applies only to `.hermes/skills` | Recursive-discovery proof, flattened-layout regression, shared-owner teardown | Enforceable existing flattened delivery; Phase 8 re-verifies nesting claim |

## Existing Surfaces That Must Not Regress

| Platform | Existing enforceable delivery retained in Phase 1 |
|---|---|
| Codex | Marker-merged `AGENTS.md`, flattened skills and command-skills in native and shared roots, legacy prompts |
| Gemini CLI | Marker-merged `GEMINI.md`, flattened skills, agents, rules, and TOML commands |
| Qwen | Marker-merged `QWEN.md`, flattened skills and command-skills, Markdown commands, and agents |
| Kimi | Marker-merged `AGENTS.md`, flattened native skills and command-skills, no deprecated `~/.kimi` writes |
| Copilot | Global prompt files, marker-merged project instructions, and opt-in never-overwrite project skills |
| Hermes | Detection-gated native flattened skills and command-skills; shared aliases remain read-only |

## Enforcement Gate

A later phase may change a row from finding-only to enforceable only when all of these statements are true:

- The official path and schema have been re-verified for the current platform version.
- Bash and PowerShell installers invoke the same registry behavior.
- Install, upgrade, repair, verify, doctor, and teardown behavior is covered.
- Shared configuration preserves unrelated user data and rolls back after a failed merge.
- The install summary reports the surface only when the platform was detected and the write succeeded.
- `docs/policy/platform-read-contracts.json` and its Markdown mirror are updated together.

## Sources

- [Nexus-Hub platform read contracts](../../../policy/platform-read-contracts.md)
- [OpenAI Codex agents guidance](https://developers.openai.com/codex/guides/agents-md)
- [Gemini CLI hooks](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/index.md)
- [Qwen Code settings](https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/)
- [Kimi Code CLI agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html)
- [Kimi Code CLI hooks](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html)
- [GitHub Copilot custom agents](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [VS Code agent hooks](https://code.visualstudio.com/docs/agent-customization/hooks)
