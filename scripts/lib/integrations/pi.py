"""Pi integration (Pi Agent Harness coding agent).

Pi is a self-extensible coding agent CLI (``@earendil-works/pi-coding-agent``).
Contract verified 2026-08-25 against the project's own published documentation:

  - **Skills**: ``packages/coding-agent/docs/skills.md``. Pi implements the
    `Agent Skills standard <https://agentskills.io/specification>`_ that Nexus-Hub
    already conforms to, so the catalog needs no new emission format. Global:
    ``~/.pi/agent/skills/``. Project: ``.pi/skills/``. Directories containing a
    ``SKILL.md`` are discovered recursively, which the flattened one-level layout
    satisfies. Pi is deliberately lenient about a skill name differing from its
    parent directory, but Nexus-Hub keeps them equal anyway (a hard rule in
    ``scripts/validate_skills.py``).
  - **Commands**: ``packages/coding-agent/docs/prompt-templates.md``. Pi calls
    these *prompt templates*, discovered at ``~/.pi/agent/prompts/*.md`` (global)
    and ``.pi/prompts/*.md`` (project). The filename becomes the command name, so
    ``review.md`` is ``/review``, and frontmatter carries an optional
    ``description`` plus an optional ``argument-hint``. That is the same shape the
    catalog's Markdown command bodies already have, so they are mirrored verbatim
    like Cursor and Qwen rather than converted.
  - **Instruction**: ``packages/coding-agent/docs/usage.md`` documents that pi
    loads ``AGENTS.md`` or ``CLAUDE.md`` from ``~/.pi/agent/AGENTS.md`` (global),
    from the current directory, and from parent directories walking up.

    Only the GLOBAL file is written here, deliberately. Project-root ``AGENTS.md``
    is already owned by the Codex integration, and pi reads that same file from
    the working directory, so pi receives project instructions for free. Writing
    it from two integrations would create two owners of one file for no added
    coverage. ``AGENTS.override.md`` is left alone: it is the user's documented
    escape hatch for replacing what we install.

  - **Agents**: pi documents no agent-definition folder, so none is written.
  - **Rules**: none as a folder; guidance rides in ``AGENTS.md``.
  - **Hooks**: pi has no Claude-style hook registry. Its extension surface is
    TypeScript modules under ``.pi/extensions/``, which is an executable-code
    surface Nexus-Hub deliberately does not write into. ``hooks_supported`` is
    therefore False, and that is a capability statement, not an oversight.

Project-trust caveat (documented in ``packages/coding-agent/docs/settings.md``):
pi loads project-local ``.pi`` resources and project ``.agents/skills`` only after
the user trusts the folder, and non-interactive modes fall back to the global
``defaultProjectTrust`` setting. Workspace-scope writes are therefore inert until
the user answers pi's own trust prompt. Nexus-Hub does not pre-trust anything on
the user's behalf; the global surfaces under ``~/.pi/agent`` are not trust-gated
and carry the catalog regardless.

Global scope is detection-gated on ``~/.pi`` (the Qwen and Windsurf model): a user
who does not have pi installed receives nothing.
"""

from __future__ import annotations

from pathlib import Path

from ._command_surface import mirror_command_surface
from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import WriteResult

#: Pi's global config root. Skills, prompts, settings, and the global AGENTS.md
#: all live under the ``agent`` subdirectory of this root.
PI_ROOT_DIRNAME = ".pi"
PI_AGENT_SUBDIR = "agent"


class PiIntegration(MarkdownIntegration, SkillsIntegration):
    key = "pi"
    display_name = "Pi"
    instruction_mode = "shared"
    config = {
        # Global surfaces live under ~/.pi/agent, written by install_global below
        # (detection-gated), so there is no simple home-relative global_dir.
        "global_dir": None,
        # Project skills/prompts mirror under .pi/; the project instruction file
        # is intentionally NOT claimed here (see the module docstring).
        "workspace_dir": ".pi",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-pi.md",
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        # Pi documents no agent-definition folder and no Claude-style hook registry.
        "agents_subdir": None,
        "hooks_supported": False,
    }

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _global_root() -> Path:
        """Return ``~/.pi/agent``, pi's documented global resource root."""
        return (Path.home() / PI_ROOT_DIRNAME / PI_AGENT_SUBDIR).resolve()

    def _install_prompts(self, root: Path, ctx: InstallContext, result: WriteResult) -> None:
        """Mirror catalog commands into pi's ``prompts/`` surface.

        Pi's prompt templates ARE the slash-command surface: the filename becomes
        the command name and the ``description`` frontmatter key is already what
        the catalog writes, so the bodies are copied verbatim.
        """
        prompts_dst = root / "prompts"
        self._ensure_dir(prompts_dst, ctx)
        result.files.extend(
            mirror_command_surface(ctx, self.key, prompts_dst, suffix=".md")
        )

    # ------------------------------------------------------------------ install

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        """Mirror skills and prompts under the project ``.pi/`` directory.

        The project instruction file is deliberately not written: Codex already
        owns project-root ``AGENTS.md`` and pi reads that same file.

        These writes stay inert until the user trusts the project in pi itself,
        which is pi's decision to prompt for and not ours to pre-empt.
        """
        result = WriteResult()
        if ctx.instruction_only:
            return result
        pi_root = (ctx.target_root / self.config["workspace_dir"]).resolve()
        self._ensure_dir(pi_root, ctx)
        result.files.extend(self._mirror_catalog(pi_root, ctx))
        self._install_prompts(pi_root, ctx, result)
        return result

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write the ``~/.pi/agent`` surfaces when pi is detected, else skip.

        Detection: the pi config root ``~/.pi`` must exist. When it does not, pi is
        not installed for this user and the global write is skipped; workspace
        surfaces are unaffected.
        """
        result = WriteResult()
        pi_home = (Path.home() / PI_ROOT_DIRNAME).resolve()
        if not pi_home.exists():
            ctx.manifest.log(self.key, "~/.pi not found; skipping global Pi surfaces")
            result.mark_not_detected(
                "Pi (~/.pi) not found; global AGENTS.md + skills + prompts skipped"
            )
            return result
        result.detected = True
        agent_root = self._global_root()
        self._ensure_dir(agent_root, ctx)
        action = self._write_instruction(agent_root, ctx)
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_catalog(agent_root, ctx))
            self._install_prompts(agent_root, ctx, result)
        return result
