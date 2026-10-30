"""Hermes integration.

Hermes is a skills-native 2026 agent that discovers folder-per-skill ``SKILL.md``
directly from its native ``~/.hermes/skills/<name>/`` (global) and
``.hermes/skills/<name>/`` (project) roots, so it needs no rendered instruction
file. Additional roots such as ``~/.agents/skills`` are read only when the user
adds them to Hermes's ``skills.external_dirs`` setting; Nexus-Hub does not alter
that user-owned setting and therefore does not claim automatic shared-root reach.

Skills-only surface: Hermes has no instruction-file surface (no ``base-hermes.md``),
so this is a ``SkillsIntegration`` (not ``MarkdownIntegration``). Skills are flattened
one level (``skills/<name>/SKILL.md``) and each catalog command additionally surfaces
as a skill, matching the SKILL.md open-standard shape the other flattened platforms
use. Global scope is detection-gated by ``_detection.detect_platform`` (v4.14.7),
like Kimi, Qwen, and Pi; a ``~/.hermes`` holding only Nexus-Hub files is not evidence.

The full read-contract is documented in ``docs/policy/platform-read-contracts.md``.
"""

from __future__ import annotations

from pathlib import Path

from ._completion_plugins import PLUGIN_ID, install_completion_plugin
from ._detection import detect_platform
from .base import InstallContext, SkillsIntegration
from .result import WriteResult


class HermesIntegration(SkillsIntegration):
    key = "hermes"
    display_name = "Hermes"
    config = {
        # v4.14.7: detection evidence (decision D2). `hermes` is collision-prone
        # (Meta's Hermes JavaScript engine ships a `hermes` binary), so a PATH hit
        # counts only from the Hermes Agent install locations. The POSIX installer
        # also places its code at ~/.hermes/hermes-agent, which the root check sees.
        # config.yaml is listed because Nexus-Hub seeds it.
        # Signals: docs/releases/v4/v4.14/development/v4.14.7-detection-signals.md
        "detection": {
            "executables": ["hermes"],
            "corroborate": {"hermes": ["hermes-agent", "/hermes/bin", "\\hermes\\bin"]},
            "root": ".hermes",
            "nexus_entries": ["skills", "config.yaml"],
            # Phase 5: merged or seeded settings, never deleted whole (value: pruner).
            "shared_configs": {".hermes/config.yaml": ""},
            "app_paths": {"win32": ["%LOCALAPPDATA%/hermes/hermes-agent"]},
        },
        # Global skills live under ~/.hermes, written by install_global below
        # (detection-gated), so there is no simple home-relative global_dir.
        "global_dir": None,
        # Project skills mirror under .hermes/ at workspace scope.
        "workspace_dir": ".hermes",
        # Skills flattened one level; each catalog command surfaces as a skill too,
        # matching the SKILL.md open standard Hermes reads.
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write ``~/.hermes/skills`` when Hermes is detected, else skip with a note.

        Detection (v4.14.7): ``detect_platform`` with this class's ``detection``
        spec, so a ``~/.hermes`` holding only Nexus-Hub files is not evidence. When
        Hermes is not detected the global write is skipped (the workspace-scope
        ``.hermes/`` surfaces are unaffected). Nexus-Hub does not add
        ``~/.agents/skills`` to the user-owned ``skills.external_dirs`` list.
        """
        result = WriteResult()
        hermes_root = (ctx.global_root / ".hermes").resolve()
        detection = detect_platform(ctx, self)
        if not detection.detected:
            ctx.manifest.log(self.key, f"not detected ({detection.evidence}); skipping global Hermes surfaces")
            result.mark_not_detected(f"Hermes not detected ({detection.evidence}); global skills skipped", evidence=detection.evidence)
            return result
        result.detected = True
        self._ensure_dir(hermes_root, ctx)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_catalog(hermes_root, ctx))
            # Opt-in completion-gate plugin (NEXUS_HUB_COMPLETION_PLUGINS=1); a
            # default install retires an earlier copy.
            install_completion_plugin(self, ctx, "hermes", hermes_root / "plugins" / PLUGIN_ID, result)
        return result
