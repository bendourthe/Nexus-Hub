"""Devin Desktop / Windsurf compatibility integration.

The current Devin Desktop Cascade contract retains Windsurf's on-disk roots.
User-level customizations live below ``~/.codeium/windsurf``; workspace skills,
workflows, and hooks live below ``.windsurf``. Current rules prefer
``.devin/rules`` and a repository-root ``AGENTS.md``, while legacy
``.windsurfrules`` and ``.windsurf/rules`` remain readable. Nexus-Hub writes the
current surfaces and keeps the single-file legacy rule for existing users.

Cascade hooks use a native JSON schema and Cascade-shaped JSON stdin. The
adapter installs a small compatibility wrapper that translates documented
command/write/prompt/response payloads into the Claude-shaped subset consumed by
the curated catalog hooks. Pre-hook exit code 2 remains a native blocking error.
Hooks that depend on unsupported event or rewrite semantics are not registered.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.lib.installer.instruction_merge import merge_marker_section

from ._catalog_adapters import (
    catalog_skill_names,
    commands_to_skills,
    commands_to_slash,
    flatten_skills,
)
from ._hooks_common import sourced_modules
from ._owned import remove_dir_if_empty
from .base import InstallContext, MarkdownIntegration
from .result import FileAction, WriteResult

_GLOBAL_RULE = """\
# Nexus-Hub

Use the native Nexus-Hub skills installed under `~/.codeium/windsurf/skills/`.
When a repository provides a root `AGENTS.md`, treat it as the authoritative
project instruction file. Verify work before claiming completion, find root
causes, preserve user edits, and keep every changed line within the requested
scope. Use the installed workflow or skill that matches the user's request.
"""

_DEVIN_RULE_STUB = """\
---
trigger: always_on
---

# Nexus-Hub

Follow the repository-root `AGENTS.md` as the authoritative instruction file.
Nexus-Hub skills are available under `.windsurf/skills/` and repeatable manual
workflows under `.windsurf/workflows/`.
"""

# Only catalog hooks whose Cascade event and exit/output contract are compatible
# are registered. Each tuple is (catalog script, translated Claude tool name).
_CASCADE_HOOKS: dict[str, tuple[tuple[str, str], ...]] = {
    "pre_run_command": (
        ("git-guardrails.sh", "Bash"),
        ("memory-store-guard.sh", "Bash"),
    ),
    "pre_write_code": (
        ("secret-scan.sh", "Write"),
        ("html-responsive-guard.sh", "Write"),
        ("large-file-guard.sh", "Write"),
        ("memory-store-guard.sh", "Write"),
        ("escalation-trigger.sh", "Write"),
    ),
    "post_write_code": (
        ("auto-format-on-write.sh", "Write"),
        ("lint-on-write.sh", "Write"),
        ("provenance-ledger.sh", "Write"),
        ("workflow-phase-notice.sh", "Write"),
        ("test-gap-notice.sh", "Write"),
        ("dependency-staleness-notice.sh", "Write"),
    ),
    "post_run_command": (("provenance-ledger.sh", "Bash"),),
    "pre_user_prompt": (
        ("learning-capture.sh", ""),
        ("skill-activation-suggest.py", ""),
    ),
    "post_cascade_response": (
        ("usage-display.sh", ""),
        ("notify-on-complete.sh", ""),
        ("session-summary.sh", ""),
        ("auto-devlog.sh", ""),
        ("learning-capture.sh", ""),
    ),
}


class WindsurfIntegration(MarkdownIntegration):
    key = "windsurf"
    display_name = "Devin Desktop / Windsurf"
    instruction_mode = "shared"
    config = {
        "global_dir": None,
        "workspace_dir": ".windsurf",
        "instruction_workspace_dir": "",
        "instruction_file": ".windsurfrules",
        "instruction_template": "templates/ai-instructions/base-windsurf.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "global_commands_subdir": "global_workflows",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    def _write_explicit_instruction(
        self, dst: Path, ctx: InstallContext, *, legacy_header: str = "## Nexus-Hub"
    ) -> FileAction:
        template = ctx.repo_root / self.config["instruction_template"]
        if not template.exists():
            ctx.manifest.log(self.key, f"missing-template: {template}")
            return FileAction(path=str(template), action="not-found")
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
        action = merge_marker_section(
            dst,
            self._render(template, ctx),
            legacy_header=legacy_header,
            dry_run=ctx.dry_run,
        )
        ctx.manifest.track_shared(self.key, str(dst))
        return action

    def _mirror_native(
        self, root: Path, ctx: InstallContext, *, scope: str
    ) -> list[FileAction]:
        src_skills = ctx.repo_root / "catalog" / "skills"
        src_commands = ctx.repo_root / "catalog" / "commands"
        skills_dst = root / self.config["skills_subdir"]
        actions: list[FileAction] = []
        actions.extend(flatten_skills(ctx, self.key, src_skills, skills_dst))
        actions.extend(
            commands_to_skills(
                ctx,
                self.key,
                src_commands,
                skills_dst,
                catalog_skill_names(src_skills),
            )
        )
        actions.extend(
            commands_to_slash(
                ctx,
                self.key,
                src_commands,
                root
                / (
                    self.config["global_commands_subdir"]
                    if scope == "global"
                    else self.config["commands_subdir"]
                ),
                style="verbatim",
            )
        )
        actions.extend(self._install_hooks(root, ctx, scope=scope))
        return actions

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Install user-level Cascade surfaces when the Codeium root exists."""
        result = WriteResult()
        codeium_root = (Path.home() / ".codeium").resolve()
        if not codeium_root.exists():
            ctx.manifest.log(self.key, "~/.codeium not found; skipping global Devin Desktop surfaces")
            result.mark_not_detected(
                "Devin Desktop (~/.codeium) not found; global rules, skills, workflows, and hooks skipped"
            )
            return result
        result.detected = True
        windsurf_root = (codeium_root / "windsurf").resolve()
        memories_dir = windsurf_root / "memories"
        self._ensure_dir(memories_dir, ctx)
        global_rules = memories_dir / "global_rules.md"
        action = merge_marker_section(
            global_rules,
            _GLOBAL_RULE,
            legacy_header="## Nexus-Hub",
            dry_run=ctx.dry_run,
        )
        ctx.manifest.track_shared(self.key, str(global_rules))
        result.files.append(action)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_native(windsurf_root, ctx, scope="global"))
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        """Install current Devin Desktop surfaces plus legacy `.windsurfrules`."""
        result = WriteResult()
        root = ctx.target_root.resolve()
        self._ensure_dir(root, ctx)
        result.files.append(self._write_instruction(root, ctx))
        result.files.append(self._write_explicit_instruction(root / "AGENTS.md", ctx))
        result.files.append(
            self._write_generated(
                root / ".devin" / "rules" / "nexus-hub.md",
                _DEVIN_RULE_STUB,
                ctx,
                self.key,
            )
        )
        if not ctx.instruction_only:
            windsurf_root = root / self.config["workspace_dir"]
            self._ensure_dir(windsurf_root, ctx)
            result.files.extend(self._mirror_native(windsurf_root, ctx, scope="workspace"))
        return result

    def _hook_base(self, root: Path, scope: str) -> str:
        if scope == "workspace":
            return f"{self.config['workspace_dir']}/{self.config['hooks_subdir']}"
        return (root / self.config["hooks_subdir"]).as_posix()

    @staticmethod
    def _command_pair(base: str, event: str, tool_name: str, script: str) -> tuple[str, str]:
        compat = f'{base}/cascade-hook-compat.py'
        if script.endswith(".py"):
            posix_target = f'python3 "{base}/{script}"'
            windows_target = f'python "{base}/{script}"'
        else:
            posix_target = f'bash "{base}/{script}"'
            windows_script = f"{Path(script).stem}.ps1"
            windows_target = (
                "powershell -NoProfile -ExecutionPolicy Bypass "
                f'-File "{base}/{windows_script}"'
            )
        command = (
            f'python3 "{compat}" {event} "{tool_name}" -- {posix_target}'
        )
        powershell = (
            f'python "{compat}" {event} "{tool_name}" -- {windows_target}'
        )
        return command, powershell

    def _owned_hook_entries(self, base: str) -> dict[str, list[dict[str, object]]]:
        events: dict[str, list[dict[str, object]]] = {}
        for event, hooks in _CASCADE_HOOKS.items():
            for script, tool_name in hooks:
                command, powershell = self._command_pair(base, event, tool_name, script)
                events.setdefault(event, []).append(
                    {
                        "command": command,
                        "powershell": powershell,
                        "show_output": event.startswith("pre_"),
                    }
                )
        return events

    def _install_hooks(
        self, root: Path, ctx: InstallContext, *, scope: str
    ) -> list[FileAction]:
        src_hooks = ctx.repo_root / "catalog" / "hooks"
        if not src_hooks.exists():
            return [FileAction(path=str(src_hooks), action="not-found")]
        hooks_dst = root / self.config["hooks_subdir"]
        self._ensure_dir(hooks_dst, ctx)
        base = self._hook_base(root, scope)
        scripts = {script for hooks in _CASCADE_HOOKS.values() for script, _ in hooks}
        for script in tuple(scripts):
            if script.endswith(".sh"):
                scripts.add(f"{Path(script).stem}.ps1")
        scripts |= sourced_modules(scripts, src_hooks)
        actions = [
            self._copy_file(src_hooks / script, hooks_dst / script, ctx, self.key)
            for script in sorted(scripts)
        ]
        actions.append(
            self._copy_file(
                ctx.repo_root
                / "scripts"
                / "lib"
                / "integrations"
                / "_cascade_hook_compat.py",
                hooks_dst / "cascade-hook-compat.py",
                ctx,
                self.key,
            )
        )
        actions.append(
            self._merge_hooks_json(
                root / "hooks.json", self._owned_hook_entries(base), base, ctx
            )
        )
        return actions

    def _merge_hooks_json(
        self,
        dst: Path,
        owned: dict[str, list[dict[str, object]]],
        owned_base: str,
        ctx: InstallContext,
    ) -> FileAction:
        existing: dict = {}
        if dst.exists():
            try:
                parsed = json.loads(dst.read_text(encoding="utf-8") or "{}")
            except json.JSONDecodeError:
                ctx.manifest.log(self.key, f"keep-malformed-hooks: {dst}")
                return FileAction(path=str(dst), action="kept")
            if not isinstance(parsed, dict):
                return FileAction(path=str(dst), action="kept")
            existing = dict(parsed)
        hooks = dict(existing.get("hooks") or {})
        for event in set(hooks) | set(owned):
            current = hooks.get(event, [])
            survivors = [
                entry
                for entry in current
                if not self._hook_entry_is_owned(entry, owned_base, event)
            ]
            hooks[event] = survivors + list(owned.get(event, []))
        existing["hooks"] = hooks
        content = (json.dumps(existing, indent=2) + "\n").encode("utf-8")
        if dst.exists() and dst.read_bytes() == content:
            ctx.manifest.track(self.key, str(dst))
            return FileAction(path=str(dst), action="unchanged")
        existed = dst.exists()
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content)
        ctx.manifest.track(self.key, str(dst))
        return FileAction(path=str(dst), action="updated" if existed else "created")

    @staticmethod
    def _hook_entry_is_owned(entry: object, owned_base: str, event: str) -> bool:
        """Return whether an entry invokes Nexus's compatibility wrapper.

        User-owned hook commands commonly live under the same native hooks
        directory. Directory membership therefore is not an ownership marker;
        the generated wrapper path and event prefix together are.
        """
        if not isinstance(entry, dict):
            return False
        compat = f'{owned_base.rstrip("/")}/cascade-hook-compat.py'
        prefixes = tuple(
            f'{runner} "{compat}" {event} ' for runner in ("python", "python3")
        )
        return any(
            isinstance(entry.get(field), str)
            and entry[field].startswith(prefixes)
            for field in ("command", "powershell")
        )

    @staticmethod
    def _prune_hooks_json(dst: Path, owned_base: str, dry_run: bool) -> FileAction:
        if not dst.exists():
            return FileAction(path=str(dst), action="not-found")
        try:
            parsed = json.loads(dst.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            return FileAction(path=str(dst), action="kept")
        if not isinstance(parsed, dict):
            return FileAction(path=str(dst), action="kept")
        hooks = dict(parsed.get("hooks") or {})
        for event in list(hooks):
            hooks[event] = [
                entry
                for entry in hooks[event]
                if not WindsurfIntegration._hook_entry_is_owned(
                    entry, owned_base, event
                )
            ]
            if not hooks[event]:
                del hooks[event]
        remainder = {key: value for key, value in parsed.items() if key != "hooks"}
        if not hooks and not remainder:
            if not dry_run:
                dst.unlink(missing_ok=True)
            return FileAction(path=str(dst), action="removed")
        remainder["hooks"] = hooks
        content = (json.dumps(remainder, indent=2) + "\n").encode("utf-8")
        if not dry_run:
            dst.write_bytes(content)
        return FileAction(path=str(dst), action="updated")

    def teardown(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        if ctx.scope == "global":
            roots = [(Path.home() / ".codeium" / "windsurf").resolve()]
        else:
            roots = [(ctx.target_root / self.config["workspace_dir"]).resolve()]
        tracked = set(ctx.manifest.files_for(self.key))
        for root in roots:
            hooks_json = root / "hooks.json"
            if str(hooks_json) in tracked:
                result.files.append(
                    self._prune_hooks_json(
                        hooks_json, self._hook_base(root, ctx.scope), ctx.dry_run
                    )
                )
                ctx.manifest.untrack(self.key, str(hooks_json))
        result.extend(super().teardown(ctx))
        for root in roots:
            remove_dir_if_empty(root / self.config["hooks_subdir"], ctx, result)
        return result


__all__ = ["WindsurfIntegration"]
