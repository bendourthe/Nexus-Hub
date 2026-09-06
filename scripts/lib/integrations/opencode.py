"""OpenCode integration.

OpenCode consumes AGENTS.md as its instruction surface (open standard) and a
``.opencode/`` workspace folder (plus the ``~/.config/opencode/`` global dir) for
the skills / commands / agents mirroring.

Surfaces (re-verified 2026-07-21, v3.15.0 Phase 3, against https://opencode.ai/docs):

  - **Skills**: folder-per-skill ``SKILL.md`` discovered one level deep, at
    ``~/.config/opencode/skills`` and ``.opencode/skills`` (OpenCode also reads the
    shared ``~/.claude/skills`` and ``~/.agents/skills`` aliases). Flattened.
  - **Commands**: ``~/.config/opencode/commands`` and ``.opencode/commands``.
  - **Agents**: ``~/.config/opencode/agents`` (global) and ``.opencode/agents``
    (project) -- Markdown files with YAML frontmatter, the filename being the agent
    id; ``mode`` is OPTIONAL and defaults to ``all``. The catalog's ``agents/*.md``
    files (``name`` / ``description`` / ``tools`` frontmatter) therefore load as-is:
    OpenCode uses ``description`` + the filename, defaults ``mode: all`` since it is
    absent, and ignores the non-native ``name`` / ``tools`` keys (it applies its own
    ``permission`` model), so the agent PROMPT body is delivered verbatim. This is
    the same ``.md`` + frontmatter format Cursor consumes. Added v3.15.0 Phase 3.
  - **Hooks**: NOT delivered (``hooks_supported: False``). OpenCode's hook mechanism
    is a ``plugins/`` directory of JavaScript/TypeScript modules loaded by Bun, each
    exporting plugin functions that subscribe to events (``tool.execute.before``,
    ``file.edited``, ...); a plain ``.sh`` / ``.py`` hook cannot be dropped in and
    run. Nexus-Hub's shell/py hooks do not translate without authoring a JS/TS
    wrapper, so hooks are out of scope for this platform. See known-gap DF-4.
"""

from __future__ import annotations

from .base import MarkdownIntegration, SkillsIntegration


class OpenCodeIntegration(MarkdownIntegration, SkillsIntegration):
    key = "opencode"
    display_name = "OpenCode"
    instruction_mode = "shared"
    config = {
        # v3.14.5: OpenCode's canonical GLOBAL config dir is ~/.config/opencode
        # (XDG), not ~/.opencode -- the latter was a dead global path (the
        # instruction file + commands never reached OpenCode there). Re-verified
        # 2026-07-19 against https://opencode.ai/docs/config/ + /rules/ + /commands/.
        # Skills still reached OpenCode via its ~/.claude/skills + ~/.agents/skills
        # aliases even before this fix; the instruction file + commands did not.
        "global_dir": "~/.config/opencode",
        "workspace_dir": ".opencode",
        # OpenCode walks from the working directory to the repository root and
        # reads ambient AGENTS.md files. The catalog mirror remains namespaced
        # under .opencode/, but the instruction file belongs at the project root.
        "instruction_workspace_dir": "",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-opencode.md",
        # OpenCode discovers skills one level deep (skills/<name>/SKILL.md) and
        # also reads the ~/.claude/skills and ~/.agents/skills aliases; flatten the
        # <category>/ layer and add command-skills (v3.12.0 Phase 4).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "commands_subdir": "commands",
        # Agents: catalog/agents/*.md copied verbatim to <root>/agents/ by the base
        # _mirror_catalog tree copy. OpenCode reads .md + YAML frontmatter here with
        # `mode` defaulting to `all`, so the catalog personas load as-is (v3.15.0
        # Phase 3; format verified 2026-07-21 against https://opencode.ai/docs/agents/).
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        # Hooks NOT supported: OpenCode's plugins/ mechanism is a JS/TS Bun runtime,
        # not a shell/py hook model, so catalog/hooks/*.{sh,py} cannot run there
        # (known-gap DF-4; the base _mirror_catalog gates the hook copy on this flag).
        "hooks_supported": False,
    }
