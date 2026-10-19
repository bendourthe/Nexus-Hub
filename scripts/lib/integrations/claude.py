"""Claude Code (Anthropic) integration."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from .base import InstallContext, MarkdownIntegration, SkillsIntegration, long_path
from .result import FileAction, WriteResult


# Claude's install-time behavioral defaults are DECLARED in
# configs/platform-defaults.json and read here at runtime, so this module holds
# no second copy that can drift out of step with the shipped template. See
# configs/README.md for the schema and the do-not-invent rule.
#
# Candidate locations, in priority order. The installers deliberately do NOT
# copy configs/ into ~/.nexus-hub (they only read configs/permissions/ from a
# checkout), so an installed tree finds the file only when the one-line
# bootstrap materialized a full source tree under ~/.nexus-hub/src.
_DEFAULTS_CANDIDATES = (
    Path(__file__).resolve().parents[3] / "configs" / "platform-defaults.json",
    Path.home() / ".nexus-hub" / "src" / "configs" / "platform-defaults.json",
)

# Offline fallback for installed trees that carry no source checkout. Plain
# absence is the EXPECTED case there, so it degrades silently; only a file that
# exists but cannot be read is worth a note. These literals are kept honest by
# `python scripts/sync_platform_defaults.py --check`, which fails the build when
# they drift away from the declared values.
_FALLBACK_SETTINGS = {
    "attribution": {
        "commit": "",
        "pr": "",
    },
    "effortLevel": "high",
    "model": "opus",
    "env": {
        "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    },
    "modelSettings": {
        "claude-opus-5-5": {
            "effortLevel": "high",
        },
        "claude-sonnet-5-5": {
            "effortLevel": "high",
        },
        "claude-haiku-5-5": {
            "effortLevel": "high",
        },
        "claude-fable-5-1": {
            "effortLevel": "high",
        },
    },
}

_STUB_COMMENT = (
    "Project-local Claude Code settings, generated from configs/platform-defaults.json. "
    "Edit freely; nexus-hub init never overwrites an existing settings.json. "
    "modelSettings supplies High effort for the current canonical model IDs; "
    "effortLevel is the fallback for older models. New IDs require refreshed defaults. "
    "Saved values at this scope are user-owned; higher-priority settings can win. "
    "An existing env.CLAUDE_CODE_EFFORT_LEVEL overrides saved /effort choices; "
    "Nexus-Hub no longer seeds that variable. max is not a settings default. "
    "model selects the Opus session baseline. Remove it to use the account default. "
    "env.CLAUDE_CODE_SUBAGENT_MODEL defaults unpinned custom agents to sonnet; "
    "shipped reasoning-sensitive agents retain opus pins. Explore and Plan need a "
    "separate force flag, which is not seeded. An independent force override can "
    "defeat definition pins. Set the subagent env key to inherit to opt out at this scope."
)


_STUB_PERMISSIONS = {
    "allow": [
        "Read",
        "Glob",
        "Grep",
    ]
}


def _load_declared_settings(candidates=_DEFAULTS_CANDIDATES) -> dict:
    """Return Claude's declared install defaults, degrading to the fallback.

    `nexus-hub init` must never fail because a repo-internal source file is
    absent, so every read problem resolves to the built-in fallback. A file that
    is merely missing is the normal installed-tree case and stays silent; a file
    that exists but cannot be parsed is a real defect and gets one line on
    stderr.
    """
    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            settings = data["platforms"]["claude"]["settings"]
            if not isinstance(settings, dict) or not settings:
                raise ValueError("platforms.claude.settings is empty or not an object")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(
                f"note: {path} is unreadable ({exc}); using built-in Claude defaults.",
                file=sys.stderr,
            )
            break
        return copy.deepcopy(settings)
    return copy.deepcopy(_FALLBACK_SETTINGS)


def build_project_settings_stub(candidates=_DEFAULTS_CANDIDATES) -> dict:
    """Compose the `.claude/settings.json` stub that `nexus-hub init` writes.

    Composed at call time rather than at import time so the declared values are
    read from disk on every run, which is what makes editing
    configs/platform-defaults.json change what init writes with no code edit.
    """
    stub: dict = {"_comment": _STUB_COMMENT}
    stub.update(_load_declared_settings(candidates))
    stub["permissions"] = copy.deepcopy(_STUB_PERMISSIONS)
    return stub


def effort_override_note(settings_file: Path | None = None) -> str | None:
    """Describe a persistent effort override without changing settings or ownership."""
    path = (
        settings_file
        if settings_file is not None
        else Path.home() / ".claude/settings.json"
    )
    if not path.is_file():
        return None
    shown_path = json.dumps(str(path), ensure_ascii=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise TypeError("settings root is not an object")
    except (OSError, ValueError, TypeError):
        return f"[doctor] Claude effort settings are unreadable at {shown_path}; no file was changed."
    env = data.get("env", {})
    if not isinstance(env, dict):
        return f"[doctor] Claude env is not an object at {shown_path}; no file was changed."
    if "CLAUDE_CODE_EFFORT_LEVEL" not in env:
        return None
    value = env["CLAUDE_CODE_EFFORT_LEVEL"]
    # An arbitrary user value may contain secrets or control characters.
    shown = (
        value
        if isinstance(value, str)
        and value in {"low", "medium", "high", "xhigh", "max", "auto"}
        else "an unsupported value"
    )
    owned = False
    record_path = path.parent.parent / ".nexus-hub/core-settings-seeds.json"
    try:
        if record_path.is_symlink():
            raise ValueError("linked record")
        record = json.loads(record_path.read_text(encoding="utf-8-sig"))
        values = record.get("values") if isinstance(record, dict) else None
        removed = record.get("removed", []) if isinstance(record, dict) else None
        valid = (
            isinstance(record, dict)
            and isinstance(record.get("schema_version"), (int, float))
            and not isinstance(record["schema_version"], bool)
            and record["schema_version"] == 1
            and record.get("target") == path.parent.name + "/settings.json"
            and isinstance(values, dict)
            and isinstance(removed, list)
            and all(isinstance(key, str) for key in removed)
        )
        if (
            valid
            and "env.CLAUDE_CODE_EFFORT_LEVEL" in values
            and "env.CLAUDE_CODE_EFFORT_LEVEL" not in removed
        ):
            prior = values["env.CLAUDE_CODE_EFFORT_LEVEL"]
            owned = type(prior) is type(value) and prior == value
    except (OSError, ValueError):
        pass
    if owned:
        return f"[doctor] Nexus-Hub-seeded effort override {shown} overrides saved /effort choices; run nexus-hub upgrade to retire the recorded seed."
    return f"[doctor] env.CLAUDE_CODE_EFFORT_LEVEL={shown} overrides saved /effort choices; Remove only env.CLAUDE_CODE_EFFORT_LEVEL from {shown_path} to use saved per-model effort."


class ClaudeIntegration(MarkdownIntegration, SkillsIntegration):
    key = "claude"
    display_name = "Claude Code (Anthropic)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.claude",
        "workspace_dir": ".claude",
        # Workspace CLAUDE.md lands at the project root (where Claude Code reads
        # it), not under .claude/; skills/commands/agents/rules still mirror
        # under .claude/. Matches the legacy bash installer (DF-001).
        "instruction_workspace_dir": "",
        "instruction_file": "CLAUDE.md",
        "instruction_template": "templates/ai-instructions/base-claude.md",
        # Claude Code discovers skills one level deep (~/.claude/skills/<name>/
        # SKILL.md), so flatten the catalog's <category>/ layer and surface each
        # command as a skill too (v3.12.0 Phase 4).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "commands_subdir": "commands",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    def wire_project_surfaces(self, ctx: InstallContext) -> WriteResult:
        """Write a `.claude/settings.json` stub when none exists.

        `nexus-hub init` calls this to bootstrap a Claude project surface from
        a global install. The stub never overwrites an existing settings.json;
        it returns `kept` so the user's customizations survive.
        """
        result = WriteResult()
        claude_dir = (ctx.target_root / self.config["workspace_dir"]).resolve()
        if not ctx.dry_run:
            long_path(claude_dir).mkdir(parents=True, exist_ok=True)
        dst = claude_dir / "settings.json"
        dst_io = long_path(dst)  # AR-11: a deep project root passes MAX_PATH
        if dst_io.exists():
            ctx.manifest.log(self.key, f"skip-existing: {dst}")
            result.files.append(FileAction(path=str(dst), action="kept"))
            return result
        body = json.dumps(build_project_settings_stub(), indent=2) + "\n"
        if not ctx.dry_run:
            dst_io.write_text(body, encoding="utf-8")
        ctx.manifest.track(self.key, str(dst))
        result.files.append(FileAction(path=str(dst), action="created"))
        return result
