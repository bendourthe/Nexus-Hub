# ADR-001: Integration Registry for Per-Platform Installer Logic

**Status**: Accepted
**Date**: 2026-05-20
**Targets**: v2.1.0 (Phase 10 of `docs/archive/v2/v2.1/plans/adoption-spec-kit.md`)
**Supersedes**: Lock-step per-platform `templates/ai-instructions/base-*.md` editing convention documented in `AGENTS.md`.

## Context

Up to and including v2.1.0 Phase 9, Nexus-Hub distributed the harness (skills, commands, agents, hooks, rules, MCP configs, instruction files) to multiple AI coding platforms via two parallel monolithic installer scripts: `scripts/installer.sh` (Bash, macOS / Linux) and `scripts/installer.ps1` (PowerShell, Windows). Adding a new platform required:

1. Authoring a new `templates/ai-instructions/base-<platform>.md` instruction template
2. Editing both `installer.sh` and `installer.ps1` to add a per-platform copy block (skills folder, commands folder, rules folder, instruction file rendering)
3. Editing `Select-Platforms` (PowerShell) and the equivalent Bash function to expose the platform in the interactive menu
4. Editing `configs/permissions/*.json` if the platform supports auto-approve permissions
5. Updating `AGENTS.md` "Distribution channels the installer uses" table
6. Updating `README.md` supported-agents list

That is **6 places to edit per new platform**, with no shared abstraction. The installers had grown to 1821 (Bash) + 2166 (PowerShell) lines, with substantial copy-paste between the two. Each new platform compounded the maintenance burden and the risk of cross-OS drift (a platform's install behavior diverging between Bash and PowerShell because one installer was edited and the other was forgotten).

The catalyst for this ADR is the user's explicit request, as part of Phase 10, to expand supported platforms from the original 5 (Claude Code, Codex, Cursor, Gemini, OpenCode) to 9+ (adding Antigravity 1.0, Antigravity 2.0, Gemini CLI, GitHub Copilot, GitHub CLI's `gh copilot`, Nexus-AI, and Windsurf). Doing this via the lock-step convention would require 54+ file edits and inevitably introduce inconsistencies. A unified registry is the smaller-blast-radius alternative.

## Decision

Introduce a Python class hierarchy under `scripts/lib/integrations/` that owns all per-platform install logic. Each supported platform is **one Python subclass** of one of four base integration types:

```
scripts/lib/integrations/
|-- __init__.py             # INTEGRATION_REGISTRY: dict[str, IntegrationBase]
|-- base.py                 # IntegrationBase + MarkdownIntegration + TomlIntegration + YamlIntegration + SkillsIntegration
|-- manifest.py             # File creation tracking for clean teardown
|-- runner.py               # CLI entry point: install / list / dry-run / teardown
|-- claude.py               # ClaudeIntegration   (Markdown + Skills)
|-- codex.py                # CodexIntegration    (Markdown + Skills)
|-- cursor.py               # CursorIntegration   (Markdown rules only)
|-- gemini.py               # GeminiIntegration   (Markdown + Skills, .gemini/)
|-- opencode.py             # OpenCodeIntegration (Markdown)
|-- windsurf.py             # WindsurfIntegration (Markdown + Workflows)
|-- antigravity.py          # Antigravity10Integration + Antigravity20Integration
|-- gemini_cli.py           # GeminiCliIntegration (TOML commands + GEMINI.md)
|-- copilot.py              # CopilotIntegration   (.github/copilot-instructions.md)
|-- nexus_ai.py             # NexusAiIntegration   (.nexus-ai/ skills + commands + rules)
```

Each subclass declares its config in ~30 lines:

```python
class ClaudeIntegration(MarkdownIntegration, SkillsIntegration):
    key = "claude"
    display_name = "Claude Code (Anthropic)"
    config = {
        "global_dir": "~/.claude",
        "workspace_dir": ".claude",
        "instruction_file": "CLAUDE.md",
        "commands_subdir": "commands",
        "skills_subdir": "skills",
        "rules_subdir": "rules",
        "agents_subdir": "agents",
        "hooks_supported": True,
        "permissions_file": "configs/permissions/claude-permissions.json",
    }
    instruction_template = "templates/ai-instructions/base-claude.md"
```

The base classes (`MarkdownIntegration`, `TomlIntegration`, etc.) implement `install_global()`, `install_workspace()`, and `teardown()` once. Per-platform overrides are rare and explicit.

A single runner CLI (`python scripts/lib/integrations/runner.py install --target <dir> --integrations claude,gemini,...`) is invoked by both `installer.sh` and `installer.ps1`. The existing installer logic for the original 5 platforms remains as the canonical, byte-for-byte stable path; the runner is **additive** for v2.1.0, exposing the **5 new** platforms (Windsurf, Antigravity 1.0, Antigravity 2.0, Gemini CLI, Copilot enhancements, Nexus-AI) via the new code path. A future v2.2.0 release MAY migrate the original 5 to the runner once parity tests prove byte-identical output.

## Consequences

**Positive**:

- Adding a new platform is one Python file (~30 lines) plus one registry import line. The previous 6-place edit becomes 2.
- Cross-OS drift between Bash and PowerShell installers is eliminated for the new platforms (both delegate to the same Python code).
- The registry is introspectable: `python scripts/lib/integrations/runner.py list` enumerates every supported platform with its install paths, instruction template, and capabilities. Documentation surfaces (AGENTS.md, README.md) can be auto-generated from this.
- Per-platform install is now unit-testable in pure Python (`tests/integrations/test_integration_<name>.py`) without invoking a shell.
- The `.specify/init-options.json` convention from Phase 7 (specs layout flag) extends naturally: per-platform overrides land in the integration subclass instead of as conditional branches in shell.

**Negative**:

- New Python dependency on the install path (the standard library only -- no PyPI). Both installers now check for `python3` (or `py.exe` on Windows) before proceeding. Both already require Python for `infrastructure/tools/build_skills_catalog.py` and the bundled `scripts/validate_skills.py`, so this is not a net-new dependency.
- The legacy installer code paths for the original 5 platforms remain until v2.2.0 parity migration -- temporary code duplication.
- The `MarkdownIntegration` / `SkillsIntegration` mixin pattern requires care around method-resolution order (MRO) when a subclass uses both. The base classes are designed so that `install_global()` of the leftmost mixin runs first; subclasses that depend on a different order MUST override `install_global()` explicitly.

**Neutral**:

- The user-facing CLI of both installers is unchanged. Same flags, same prompts, same target paths, same output text for the original 5 platforms. The new platforms appear as additional menu items under their existing parent (Antigravity / Gemini CLI nest under "GEMINI"; Windsurf nests as a standalone option; Nexus-AI nests under its own header).

## Alternatives Considered

1. **Keep lock-step base-*.md editing** -- Rejected. The catalyst above (5+ new platforms) makes this untenable. The cross-OS drift risk is already non-trivial at 5 platforms; at 10+ it becomes nearly certain.

2. **Adopt an upstream CLI wholesale** (such as the spec-kit `specify-cli` referenced in `docs/archive/v2/v2.0/comparison-spec-kit.md`) -- Rejected. Three reasons: (a) wholesale adoption conflicts with Nexus-Hub's installer-as-template-distributor architecture, where the harness is copied into per-platform directories rather than invoked as a Python package; (b) wholesale adoption imports the upstream's design constraints (e.g., spec-kit assumes a single per-feature git branch, which Nexus-Hub does not require); (c) the MCP Registry Policy decision tree in `AGENTS.md` mandates reverse-engineering over wholesale adoption when the logic can run locally with no external dependencies. The class-hierarchy pattern can be reverse-engineered from upstream concepts; the upstream itself is not adopted.

3. **YAML manifest plus a generic shell script** -- Rejected. The per-platform logic is not purely declarative: Cursor needs `.cursor/rules/<name>.mdc` files with embedded YAML frontmatter (different from Claude / Codex / Gemini's flat Markdown); Copilot needs `.github/copilot-instructions.md` merged into an existing file rather than overwritten; Gemini CLI needs TOML files for commands rather than Markdown. A YAML-driven generic script would either omit these cases or grow conditional branches that defeat the simplification goal.

4. **One installer (Python) replacing both Bash and PowerShell** -- Rejected. Bash and PowerShell installers are user-facing artifacts that many users invoke directly without inspecting; replacing them is a breaking change. The Python registrar is invoked **from within** both installers and presents the same user-facing experience. A future ADR (post-v2.2.0) MAY revisit this.

5. **Per-platform installer plugins discovered via entry points** (Python's `importlib.metadata`) -- Rejected for now. The plugin pattern is appropriate once external contributors add platforms, but for the initial 10 platforms maintained by the Nexus-Hub team, the explicit `_register_builtins()` function in `scripts/lib/integrations/__init__.py` is simpler. Revisitable in a future ADR.

## Related ADRs

- (None prior; this is ADR-001.)

## References

- `docs/archive/v2/v2.1/plans/adoption-spec-kit.md` -- the plan that introduced Phase 10
- `AGENTS.md` -- "Installer-Aware Changes (Cross-Platform)" section (the convention being superseded for new platforms)
- `docs/policy/mcp-reverse-engineering-matrix.md` -- the reverse-engineering policy that informed Alternative 2's rejection
