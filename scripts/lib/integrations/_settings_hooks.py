"""Native hook registration for the Gemini-CLI-class settings.json (v3.15.8 Phase 6).

Gemini CLI and Qwen Code (a Gemini CLI fork) both read hooks from a ``hooks``
key inside their main ``settings.json`` -- ``~/.gemini/settings.json`` and
``.gemini/settings.json``, ``~/.qwen/settings.json`` and ``.qwen/settings.json``
-- using the same nested shape::

    {"hooks": {"<Event>": [{"matcher": "<regex>", "hooks": [{...handler}]}]}}

Verified 2026-08-02 against the upstream Gemini CLI hooks reference and the Qwen
Code hooks documentation. Three differences between the two platforms are what
this module abstracts, via :class:`SettingsHookSpec`:

1. **Event names.** Qwen kept the Claude-style names Nexus-Hub already uses
   (``PreToolUse``, ``Stop``, ...). Gemini CLI renamed them (``BeforeTool``,
   ``AfterAgent``, ...), so its map is a genuine translation.
2. **Matcher vocabulary.** Both match on *their own* tool ids, not Claude's, and
   both treat the matcher as a REGULAR EXPRESSION rather than a literal. So
   ``Bash`` becomes ``^(run_shell_command)$``, and Nexus-Hub matchers with no
   tool of that kind are dropped rather than approximated.
3. **Handler fields.** Qwen accepts ``shell`` and ``statusMessage``; Gemini CLI
   does not, and ignores unknown keys, so they are emitted only where declared.

Two design consequences are worth stating plainly, because they differ from the
Codex integration next door.

**There is no ``commandWindows``.** Codex's schema has an explicit Windows
override slot; neither of these platforms does, and both funnel every shell call
through a single ``run_shell_command`` tool, which collapses Nexus-Hub's separate
``Bash`` and ``PowerShell`` matchers into one. A registration therefore has to
pick one command string, so this module picks it from the INSTALLING HOST: a
Windows install registers the ``.ps1`` sibling and the PowerShell-flavored
guardrails, a POSIX install registers the ``.sh`` and the Bash-flavored ones.
Both siblings are copied either way, so re-running the installer on the other OS
re-points the registration without touching the scripts.

The low-level pieces this shares with the other native-hook adapters -- host
command construction, the script-basename split, and the ownership predicate --
live in ``_hooks_common`` since v3.15.8 Phase 9. What stays here is what is
genuinely specific to these two platforms: the event maps, the tool-id matcher
vocabulary, and the settings.json merge.

**Ownership is the handler ``name``.** Both schemas carry an optional ``name``
for logging, which makes it the natural stable identity: every Nexus-Hub handler
is named ``nexus-hub:<script-stem>``. That survives a path change, and it is
what Gemini CLI fingerprints project hooks on, so a stable name also avoids
re-triggering its untrusted-hook warning on every install. The installed hooks
directory is checked as a second signal so a handler a user renamed by hand is
still recognized as ours rather than duplicated.

This module is stdlib-only and makes no outbound calls.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from ._hooks_common import (
    OWNED_NAME_PREFIX,
    command_for,
    host_shell,
    is_windows_host,
    script_basename,
    script_for_host,
    sibling_scripts,
    strip_owned_handlers,
)
from .result import FileAction

# Nexus-Hub matcher token -> the tool id its platform actually exposes. Both
# platforms inherit Gemini CLI's tool names. `Bash` and `PowerShell` collapse
# onto the same tool because neither CLI distinguishes the shell it launches --
# which is precisely why only the host's flavor is registered (see module docs).
_TOOL_IDS = {
    "Bash": "run_shell_command",
    "PowerShell": "run_shell_command",
    "Write": "write_file",
    "Edit": "replace",
    "MultiEdit": "replace",
}

# Matchers with no tool of that kind on either platform. `Skill` has no
# equivalent because neither CLI surfaces skill invocation as a tool call.
_UNMAPPABLE_MATCHERS = frozenset({"Skill"})

# Milliseconds. Both platforms default to 60000 and run hooks synchronously, so
# an explicit, shorter budget keeps a wedged guardrail from stalling the agent
# loop for a full minute.
_HOOK_TIMEOUT_MS = 15000


@dataclass(frozen=True)
class SettingsHookSpec:
    """Per-platform differences in the shared settings.json hook shape."""

    key: str
    #: Nexus-Hub event name -> this platform's event name. An event absent from
    #: the map has no equivalent and is skipped.
    event_map: dict[str, str]
    #: Events that take a tool-id matcher. Every other event either always fires
    #: or matches on something that is not a tool (a session source, a compact
    #: trigger), so emitting a tool matcher there would silently never match.
    tool_events: frozenset[str]
    #: Environment variable naming the project root, used for workspace-scope
    #: command paths so a committed project settings.json stays portable.
    project_dir_var: str
    #: Handler fields this platform documents beyond the shared core.
    supports_shell_field: bool = False
    supports_status_message: bool = False
    extra_notes: tuple[str, ...] = field(default_factory=tuple)


GEMINI_CLI_SPEC = SettingsHookSpec(
    key="gemini-cli",
    # Gemini CLI renamed every lifecycle event. `PreCompact` -> `PreCompress`,
    # and the agent-loop boundaries are Before/AfterAgent rather than
    # UserPromptSubmit/Stop. Nexus-Hub events with no counterpart are omitted.
    event_map={
        "SessionStart": "SessionStart",
        "SessionEnd": "SessionEnd",
        "UserPromptSubmit": "BeforeAgent",
        "PreToolUse": "BeforeTool",
        "PostToolUse": "AfterTool",
        "Stop": "AfterAgent",
        "PreCompact": "PreCompress",
    },
    tool_events=frozenset({"BeforeTool", "AfterTool"}),
    project_dir_var="GEMINI_PROJECT_DIR",
    extra_notes=(
        (
            "Gemini CLI hooks: inspect them with /hooks panel; project hooks are "
            "fingerprinted, so a changed command prompts for trust before it runs."
        ),
    ),
)

QWEN_SPEC = SettingsHookSpec(
    key="qwen",
    # Qwen kept the Claude-style event names, so this map is identity for every
    # event Nexus-Hub registers. It is written out rather than derived so an
    # upstream rename shows up as a diff here instead of silently passing
    # through.
    event_map={
        "SessionStart": "SessionStart",
        "SessionEnd": "SessionEnd",
        "UserPromptSubmit": "UserPromptSubmit",
        "PreToolUse": "PreToolUse",
        "PostToolUse": "PostToolUse",
        "Stop": "Stop",
        "PreCompact": "PreCompact",
    },
    tool_events=frozenset({"PreToolUse", "PostToolUse"}),
    project_dir_var="QWEN_PROJECT_DIR",
    supports_shell_field=True,
    supports_status_message=True,
    extra_notes=(
        (
            "Qwen hooks are enabled by default; they stay inert while "
            '"disableAllHooks": true is set in settings.json.'
        ),
    ),
)


# ----- command paths -------------------------------------------------------


def command_base(
    spec: SettingsHookSpec, root: Path, scope: str, hooks_subdir: str, windows: bool
) -> str:
    """Return the path prefix hook commands resolve against.

    Global scope uses the absolute installed path, which is machine-specific
    regardless because it sits under the user's home directory. Workspace scope
    uses the platform's own project-root variable so a committed project
    settings.json does not carry one developer's absolute path. On Windows the
    variable is written in PowerShell's ``$env:`` form, matching the PowerShell
    command this module emits there.
    """
    if scope != "workspace":
        return (root / hooks_subdir).as_posix()
    var = spec.project_dir_var
    reference = f"$env:{var}" if windows else f"${var}"
    # `root` is `<project>/.gemini` or `<project>/.qwen`, so its final component
    # is the config dir the variable has to be joined with.
    return f"{reference}/{root.name}/{hooks_subdir}"


# ----- entry construction --------------------------------------------------


def _matcher_regex(matcher: str, windows: bool) -> str | None:
    """Translate a Nexus-Hub matcher into a platform tool-id regex.

    Returns ``None`` when nothing in the matcher maps, meaning the group has no
    equivalent and must be skipped. The host decides between the two shell
    flavors: registering both would fire the Bash and PowerShell variants of the
    same guardrail on one ``run_shell_command`` call.
    """
    tokens = [part.strip() for part in matcher.split("|") if part.strip()]
    if not tokens:
        return ""
    wanted_shell = "PowerShell" if windows else "Bash"
    tool_ids: list[str] = []
    for token in tokens:
        if token in _UNMAPPABLE_MATCHERS:
            continue
        if token in ("Bash", "PowerShell") and token != wanted_shell:
            continue
        tool_id = _TOOL_IDS.get(token)
        if tool_id and tool_id not in tool_ids:
            tool_ids.append(tool_id)
    if not tool_ids:
        return None
    return f"^({'|'.join(tool_ids)})$"


def build_settings_hooks(
    spec: SettingsHookSpec,
    settings: dict,
    src_hooks_dir: Path,
    base: str,
    windows: bool,
) -> tuple[dict, set[str], list[str]]:
    """Build platform hook groups from ``catalog/hooks/settings.json``.

    Returns ``(events, scripts, skipped)``: the ``hooks`` mapping to merge into
    the platform's settings.json, every catalog script that must be copied
    alongside it, and a human-readable reason for each group dropped for want of
    an equivalent.
    """
    events: dict[str, list] = {}
    scripts: set[str] = set()
    skipped: list[str] = []

    for source_event, groups in settings.get("hooks", {}).items():
        target_event = spec.event_map.get(source_event)
        if target_event is None:
            skipped.append(f"{source_event}: no {spec.key} event of that kind")
            continue
        takes_matcher = target_event in spec.tool_events
        for group in groups:
            source_matcher = group.get("matcher", "")
            matcher = _matcher_regex(source_matcher, windows) if takes_matcher else ""
            if matcher is None:
                skipped.append(
                    f"{source_event}/{source_matcher}: no {spec.key} tool matches it"
                )
                continue
            handlers: list[dict] = []
            for handler in group.get("hooks", []):
                script = script_basename(handler.get("command", ""))
                if script is None:
                    continue
                host_script = script_for_host(script, windows)
                if not (src_hooks_dir / host_script).exists():
                    skipped.append(
                        f"{source_event}/{host_script}: absent from catalog/hooks"
                    )
                    continue
                scripts.add(host_script)
                # The other sibling ships too, so re-running the installer on a
                # different OS only has to re-point the registration.
                if not script.endswith(".py"):
                    for sibling in sibling_scripts(script):
                        if (src_hooks_dir / sibling).exists():
                            scripts.add(sibling)
                stem = Path(script).stem
                entry: dict[str, object] = {
                    "type": "command",
                    "name": f"{OWNED_NAME_PREFIX}{stem}",
                    "description": f"Nexus-Hub {stem} guardrail",
                    "command": command_for(host_script, base, windows),
                    "timeout": _HOOK_TIMEOUT_MS,
                }
                if spec.supports_shell_field and not host_script.endswith(".py"):
                    # Declared alongside the fully-explicit interpreter command
                    # rather than instead of it: the platform's own field states
                    # the intent, and the explicit command still runs correctly
                    # if the field is ignored or defaulted.
                    entry["shell"] = host_shell(windows)
                if spec.supports_status_message:
                    entry["statusMessage"] = f"Nexus-Hub {stem}"
                handlers.append(entry)
            if not handlers:
                continue
            emitted: dict[str, object] = {}
            if matcher:
                emitted["matcher"] = matcher
            emitted["hooks"] = handlers
            events.setdefault(target_event, []).append(emitted)

    return events, scripts, skipped


# ----- ownership-scoped merge ---------------------------------------------


def _load_settings(path: Path, log) -> dict | None:
    """Parse an existing settings.json, or return ``None`` if it must be left alone."""
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        log(f"skip-malformed-json: {path} ({exc})")
        return None
    if not isinstance(parsed, dict):
        log(f"skip-non-object-json: {path}")
        return None
    return parsed


def merge_settings_hooks(
    ctx, key: str, dst: Path, owned_events: dict, owned_base: str
) -> FileAction:
    """Merge Nexus-Hub hook groups into a platform settings.json.

    Unlike Codex's dedicated ``hooks.json``, this file holds the user's entire
    CLI configuration, so every unrelated key is preserved untouched and a
    malformed file is never rewritten -- losing a user's model, theme, and MCP
    settings to a transient syntax error would be far worse than skipping the
    hook registration and saying so. A successful merge backs the previous
    content up beside the file and writes through a temp file, so an interrupted
    write leaves the original intact.
    """
    existing = _load_settings(dst, lambda message: ctx.manifest.log(key, message))
    if existing is None:
        return FileAction(path=str(dst), action="kept")

    merged = dict(existing)
    hooks = dict(merged.get("hooks") or {})
    for event in list(hooks):
        hooks[event] = strip_owned_handlers(list(hooks[event] or []), owned_base)
    for event, groups in owned_events.items():
        hooks[event] = list(hooks.get(event) or []) + list(groups)
    surviving = {event: groups for event, groups in hooks.items() if groups}
    if surviving:
        merged["hooks"] = surviving
    else:
        merged.pop("hooks", None)

    content = (json.dumps(merged, indent=2) + "\n").encode("utf-8")
    if dst.exists() and dst.read_bytes() == content:
        ctx.manifest.track(key, str(dst))
        return FileAction(path=str(dst), action="unchanged")

    existed = dst.exists()
    if not ctx.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if existed:
            backup = dst.with_suffix(dst.suffix + ".nexus-hub.bak")
            backup.write_bytes(dst.read_bytes())
            ctx.manifest.track(key, str(backup))
        tmp = dst.with_suffix(dst.suffix + ".nexus-hub.tmp")
        tmp.write_bytes(content)
        os.replace(tmp, dst)
    # Tracked in the regular bucket, matching the Codex hooks.json precedent.
    # The integration's teardown prunes and untracks this path BEFORE the
    # manifest teardown runs, so the user's configuration file is never deleted.
    ctx.manifest.track(key, str(dst))
    return FileAction(path=str(dst), action="updated" if existed else "created")


def prune_settings_hooks(dst: Path, owned_base: str, dry_run: bool) -> FileAction:
    """Remove Nexus-Hub hook entries from a platform settings.json during teardown.

    The file itself is deleted only in the degenerate case where it held nothing
    but our hooks; normally it is rewritten without them.
    """
    if not dst.exists():
        return FileAction(path=str(dst), action="not-found")
    parsed = _load_settings(dst, lambda _message: None)
    if parsed is None:
        return FileAction(path=str(dst), action="kept")

    hooks = dict(parsed.get("hooks") or {})
    for event in list(hooks):
        survivors = strip_owned_handlers(list(hooks[event] or []), owned_base)
        if survivors:
            hooks[event] = survivors
        else:
            del hooks[event]

    remainder = {k: v for k, v in parsed.items() if k != "hooks"}
    if not hooks and not remainder:
        if not dry_run:
            dst.unlink(missing_ok=True)
        return FileAction(path=str(dst), action="removed")

    if hooks:
        remainder["hooks"] = hooks
    content = (json.dumps(remainder, indent=2) + "\n").encode("utf-8")
    if dst.read_bytes() == content:
        return FileAction(path=str(dst), action="unchanged")
    if not dry_run:
        dst.write_bytes(content)
    return FileAction(path=str(dst), action="updated")


def hooks_disabled_note(dst: Path) -> str | None:
    """Return a warning when the platform's kill switch would keep hooks inert.

    Both platforms enable hooks by default, so there is no flag to set the way
    Codex needs one. What there is, is a user-set kill switch: reporting an
    installed guardrail while ``disableAllHooks`` is on would be a false claim.
    """
    if not dst.exists():
        return None
    parsed = _load_settings(dst, lambda _message: None)
    if parsed is None:
        return None
    if parsed.get("disableAllHooks") is True:
        return (
            'Hooks installed but inert: "disableAllHooks": true is set in '
            f"{dst}. Remove it to arm them."
        )
    return None


# `OWNED_NAME_PREFIX` and the host-command helpers are re-exported from
# `_hooks_common` so existing importers (and the Phase 6 tests) keep working
# after the Phase 9 consolidation.
__all__ = [
    "GEMINI_CLI_SPEC",
    "OWNED_NAME_PREFIX",
    "QWEN_SPEC",
    "SettingsHookSpec",
    "build_settings_hooks",
    "command_base",
    "command_for",
    "hooks_disabled_note",
    "host_shell",
    "is_windows_host",
    "merge_settings_hooks",
    "prune_settings_hooks",
    "script_for_host",
]
