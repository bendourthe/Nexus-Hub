"""Shared install/teardown wiring for settings.json-based hook platforms.

Gemini CLI and Qwen Code differ in event names, matcher vocabulary, and a couple
of handler fields -- all captured by a :class:`SettingsHookSpec` in
``_settings_hooks`` -- but the install and teardown *choreography* around that
spec is identical: copy the host's hook scripts into a ``hooks/`` subdirectory,
merge ownership-scoped entries into the platform's settings.json, warn when the
platform's kill switch would keep them inert, and on teardown prune only our own
entries before the manifest sweep runs.

That choreography lives here rather than being written twice, so the two
platforms cannot drift apart in ownership or teardown behavior -- which is the
class of bug the v3.15.6 hook-sibling work was created to stop.
"""

from __future__ import annotations

import json
from pathlib import Path

from ._settings_hooks import (
    SettingsHookSpec,
    build_settings_hooks,
    command_base,
    hooks_disabled_note,
    is_windows_host,
    merge_settings_hooks,
    prune_settings_hooks,
)
from .base import InstallContext
from .result import FileAction, WriteResult

SETTINGS_FILE = "settings.json"
HOOKS_SUBDIR = "hooks"


class SettingsHooksMixin:
    """Install and tear down native hooks in a Gemini-CLI-class settings.json.

    Expects the host class to define ``key`` and a ``hook_spec`` class attribute.
    """

    hook_spec: SettingsHookSpec

    def _install_settings_hooks(
        self, root: Path, ctx: InstallContext, scope: str
    ) -> WriteResult:
        """Copy the hook scripts this host can run and register them.

        Only groups whose event AND matcher have an equivalent on this platform
        are registered; the rest are logged as skipped rather than mapped onto a
        matcher the platform would never fire.
        """
        result = WriteResult()
        src_hooks = ctx.repo_root / "catalog" / "hooks"
        settings_template = src_hooks / SETTINGS_FILE
        if not settings_template.exists():
            ctx.manifest.log(self.key, f"missing-file: {settings_template}")
            result.files.append(
                FileAction(path=str(settings_template), action="not-found")
            )
            return result

        windows = is_windows_host()
        base = command_base(self.hook_spec, root, scope, HOOKS_SUBDIR, windows)
        events, scripts, skipped = build_settings_hooks(
            self.hook_spec,
            json.loads(settings_template.read_text(encoding="utf-8")),
            src_hooks,
            base,
            windows,
        )
        for reason in skipped:
            ctx.manifest.log(self.key, f"skip-hook {reason}")

        hooks_dst = root / HOOKS_SUBDIR
        self._ensure_dir(hooks_dst, ctx)
        for script in sorted(scripts):
            result.files.append(
                self._copy_file(src_hooks / script, hooks_dst / script, ctx, self.key)
            )

        settings_dst = root / SETTINGS_FILE
        result.files.append(
            merge_settings_hooks(ctx, self.key, settings_dst, events, base)
        )
        disabled = hooks_disabled_note(settings_dst)
        if disabled:
            result.notes.append(disabled)
        result.notes.extend(self.hook_spec.extra_notes)
        return result

    def _teardown_settings_hooks(
        self, roots: list[Path], ctx: InstallContext
    ) -> WriteResult:
        """Prune our hook entries, then drop the hooks dir if nothing remains.

        settings.json holds the user's entire CLI configuration, so it is pruned
        and untracked here rather than left to the manifest sweep, which would
        delete the whole file.
        """
        result = WriteResult()
        tracked = set(ctx.manifest.files_for(self.key))
        for root in roots:
            settings_dst = root / SETTINGS_FILE
            if str(settings_dst) not in tracked:
                continue
            base = command_base(
                self.hook_spec, root, ctx.scope, HOOKS_SUBDIR, is_windows_host()
            )
            result.files.append(prune_settings_hooks(settings_dst, base, ctx.dry_run))
            ctx.manifest.untrack(self.key, str(settings_dst))
        return result

    # Directory cleanup is `_owned.remove_dir_if_empty`, called directly by each
    # integration's teardown. The Phase 6 wrapper that used to sit here was
    # removed in Phase 9 once the shared helper existed.


__all__ = ["HOOKS_SUBDIR", "SETTINGS_FILE", "SettingsHooksMixin"]
