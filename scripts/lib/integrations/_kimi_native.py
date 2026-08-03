"""Kimi Code CLI native agent and hook materialization (v3.15.8 Phase 6/7).

Verified 2026-08-02 against the official Kimi Code CLI
[agents](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/agents.html),
[hooks](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/hooks.html),
[built-in tools](https://www.kimi.com/code/docs/en/kimi-code-cli/reference/tools.html),
and [configuration](https://www.kimi.com/code/docs/en/kimi-code-cli/configuration/config-files)
references. Two surfaces, with very different amounts of work involved.

**Custom agents are a verbatim copy.** Kimi discovers agent files as Markdown
with YAML frontmatter, and it explicitly accepts the Claude Code shape the
catalog already ships: ``description`` is the only required field, ``name``
falls back to the filename, the comma-separated ``tools`` form is supported to
"keep Claude Code-style agent files loadable", and unknown fields are ignored so
newer or foreign fields do not break loading. So unlike Codex -- which needed a
Markdown-to-TOML transform -- Kimi needs no transform at all, and a verbatim copy
means an agent behaves identically on both platforms. Only validation is applied:
a file with no ``description``, no body, or a non-kebab-case name is skipped
rather than shipped for Kimi to reject at load time.

One upstream caveat is deliberately NOT worked around. Kimi notes that a custom
agent delegated as a sub-agent runs without the built-in "your final message is
the entire handoff" framing, and suggests stating that in the body. Injecting a
generated paragraph would make the delivered agent differ from the catalog
source, so the copy stays verbatim and the caveat is documented in the read
contract instead.

**Hooks need a comment-preserving TOML merge.** Kimi's hooks are a ``[[hooks]]``
array of tables in ``~/.kimi-code/config.toml``, the same file that holds the
user's providers, models, permission rules, and tool switches. Three properties
of that schema shape the implementation:

1. **Only four fields are allowed** (``event``, ``matcher``, ``command``,
   ``timeout``), and per the docs "extra fields will cause the config file to
   fail to load". There is therefore no ``name`` slot to carry ownership -- the
   Phase 6 approach for Gemini CLI and Qwen -- and emitting one would break the
   user's entire config.
2. **Each entry holds exactly one command**, where the catalog groups several
   commands under one matcher, so one catalog group expands to several entries.
3. **``timeout`` is in seconds** (1-600, default 30), not the milliseconds the
   Gemini-CLI-class platforms use.

Ownership is solved with a marker-delimited managed block appended to
``config.toml``, mirroring the marker-merge convention Nexus-Hub already uses for
instruction files. Everything outside the block -- every comment, every table,
every formatting choice -- is preserved byte-for-byte, because the merge never
parses and re-emits the user's TOML. It only splices one region. The result is
parsed with ``tomllib`` before it is committed, and a parse failure rolls the
write back, so a merge can never leave Kimi with a config it refuses to load.

This module is stdlib-only and makes no outbound calls.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import tomllib

from ._catalog_adapters import _split_frontmatter
from ._hooks_common import (
    command_for,
    script_basename,
    script_for_host,
    sibling_scripts,
)
from ._owned import write_owned_file
from .base import IntegrationBase
from .result import FileAction

# Kimi hook events, per the official event reference. The catalog's events all
# appear here under the same names, so no translation is needed -- but the set is
# listed explicitly so a future catalog event is rejected rather than emitted
# into a config Kimi would refuse to load.
KIMI_HOOK_EVENTS = frozenset(
    {
        "UserPromptSubmit",
        "PreToolUse",
        "Stop",
        "PostToolUse",
        "PostToolUseFailure",
        "PermissionRequest",
        "PermissionResult",
        "SessionStart",
        "SessionEnd",
        "SubagentStart",
        "SubagentStop",
        "StopFailure",
        "Interrupt",
        "PreCompact",
        "PostCompact",
        "Notification",
    }
)

# Events whose matcher targets a tool name. Everything else matches on a session
# source, a compact trigger, or nothing at all, so a tool matcher there would
# silently never fire.
KIMI_TOOL_EVENTS = frozenset(
    {
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "PermissionRequest",
        "PermissionResult",
    }
)

# Catalog matcher token -> Kimi built-in tool name. Kimi's tool names match
# Claude's exactly for the ones the catalog cares about, which is why this is
# nearly an identity map. `MultiEdit` folds into `Edit` because Kimi's `Edit`
# covers repeated replacement via `replace_all` rather than exposing a second
# tool. `PowerShell` has no entry: Kimi routes every shell call through `Bash` on
# every platform, so the Bash-matched guardrails already cover Windows and
# registering the PowerShell-flavored variants too would double-fire them.
KIMI_TOOL_NAMES = {
    "Bash": "Bash",
    "Write": "Write",
    "Edit": "Edit",
    "MultiEdit": "Edit",
    "Skill": "Skill",
}

# The only four keys a `[[hooks]]` entry may carry. Emitting anything else makes
# Kimi fail to load the whole config file, so this is asserted, not assumed.
KIMI_HOOK_FIELDS = frozenset({"event", "matcher", "command", "timeout"})

# Seconds, within Kimi's documented 1-600 range. Kimi is fail-open on timeout, so
# a wedged guardrail degrades to a warning rather than a block.
KIMI_HOOK_TIMEOUT_S = 15

BLOCK_START = "# >>> NEXUS_HUB_HOOKS_START >>>"
BLOCK_END = "# <<< NEXUS_HUB_HOOKS_END <<<"

_BLOCK_RE = re.compile(
    rf"\n*{re.escape(BLOCK_START)}.*?{re.escape(BLOCK_END)}\n*",
    re.DOTALL,
)

_KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


# ----- custom agents -------------------------------------------------------


def agent_is_loadable(source_name: str, markdown: str) -> str | None:
    """Return a skip reason, or ``None`` when Kimi will load this agent file.

    Kimi requires ``description`` and skips a file whose resolved name is not
    kebab-case. Everything else in the catalog's frontmatter is either supported
    outright or ignored, so validation is all this needs to do.
    """
    meta, body = _split_frontmatter(markdown)
    name = meta.get("name", "").strip() or source_name
    if not _KEBAB_CASE.match(name):
        return f"name {name!r} is not kebab-case"
    if not meta.get("description", "").strip():
        return "no description field"
    if not body.strip():
        return "no body to use as a system prompt"
    return None


def agents_to_kimi(
    ctx, key: str, src_agents_dir: Path, dst_agents_dir: Path
) -> list[FileAction]:
    """Copy ``catalog/agents/*.md`` to Kimi's agents directory, unchanged.

    Kimi reads the catalog's Claude-Code-style frontmatter natively, so this is a
    validated copy rather than a transform. The write goes through
    ``write_owned_file`` rather than ``_copy_file`` because the matrix requires
    manifest-driven repair: a file Nexus-Hub owns must be refreshed when it
    drifts, while one the user wrote must be left exactly as it is. ``_copy_file``
    cannot tell those apart -- it keeps any existing destination.
    """
    if not src_agents_dir.exists():
        ctx.manifest.log(key, f"missing-tree: {src_agents_dir}")
        return [FileAction(path=str(src_agents_dir), action="not-found")]
    IntegrationBase._ensure_dir(dst_agents_dir, ctx)
    actions: list[FileAction] = []
    for md in sorted(src_agents_dir.glob("*.md")):
        content = md.read_bytes()
        reason = agent_is_loadable(md.stem, content.decode("utf-8"))
        if reason is not None:
            ctx.manifest.log(key, f"skip agent ({reason}): {md.name}")
            continue
        actions.append(write_owned_file(ctx, key, dst_agents_dir / md.name, content))
    return actions


# ----- hook entries --------------------------------------------------------


def _matcher_regex(matcher: str) -> str | None:
    """Translate a catalog matcher into a Kimi tool-name regex.

    Returns ``None`` when nothing maps, meaning the group has no Kimi equivalent
    and must be skipped, and ``""`` when the source matcher was already empty.
    """
    tokens = [part.strip() for part in matcher.split("|") if part.strip()]
    if not tokens:
        return ""
    names: list[str] = []
    for token in tokens:
        name = KIMI_TOOL_NAMES.get(token)
        if name and name not in names:
            names.append(name)
    if not names:
        return None
    return f"^({'|'.join(names)})$"


def build_kimi_hooks(
    settings: dict, src_hooks_dir: Path, command_base: str, windows: bool
) -> tuple[list[dict], set[str], list[str]]:
    """Build flat Kimi ``[[hooks]]`` entries from ``catalog/hooks/settings.json``.

    Returns ``(entries, scripts, skipped)``. Each entry carries only the four
    fields Kimi permits. Because Kimi allows one command per entry where the
    catalog groups several under one matcher, a catalog group expands into
    several entries sharing an event and matcher.
    """
    entries: list[dict] = []
    scripts: set[str] = set()
    skipped: list[str] = []
    seen: set[tuple[str, str, str]] = set()

    for event, groups in settings.get("hooks", {}).items():
        if event not in KIMI_HOOK_EVENTS:
            skipped.append(f"{event}: no Kimi event of that name")
            continue
        takes_matcher = event in KIMI_TOOL_EVENTS
        for group in groups:
            source_matcher = group.get("matcher", "")
            matcher = _matcher_regex(source_matcher) if takes_matcher else ""
            if matcher is None:
                skipped.append(f"{event}/{source_matcher}: no Kimi tool of that name")
                continue
            for handler in group.get("hooks", []):
                script = script_basename(handler.get("command", ""))
                if script is None:
                    continue
                host_script = script_for_host(script, windows)
                if not (src_hooks_dir / host_script).exists():
                    skipped.append(f"{event}/{host_script}: absent from catalog/hooks")
                    continue
                scripts.add(host_script)
                # Ship the other sibling too, so re-running the installer on a
                # different OS only has to re-point the command.
                if not script.endswith(".py"):
                    for sibling in sibling_scripts(script):
                        if (src_hooks_dir / sibling).exists():
                            scripts.add(sibling)
                command = command_for(host_script, command_base, windows)
                identity = (event, matcher, command)
                if identity in seen:
                    # Kimi already dedupes identical commands, but emitting the
                    # duplicate would still bloat the user's config for nothing.
                    continue
                seen.add(identity)
                entry = {
                    "event": event,
                    "command": command,
                    "timeout": KIMI_HOOK_TIMEOUT_S,
                }
                if matcher:
                    entry["matcher"] = matcher
                entries.append(entry)

    return entries, scripts, skipped


def _toml_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def render_hooks_block(entries: list[dict]) -> str:
    """Render Nexus-Hub hook entries as a marker-delimited TOML block.

    ``[[hooks]]`` is an absolute array-of-tables header, so appending the block
    at end of file is valid wherever the preceding content leaves off.
    """
    lines = [
        BLOCK_START,
        "# Managed by Nexus-Hub. Edits inside this block are replaced on upgrade;",
        "# everything outside it is preserved untouched. Remove via nexus-hub uninstall.",
    ]
    for entry in entries:
        lines.append("[[hooks]]")
        lines.append(f"event = {_toml_string(entry['event'])}")
        if "matcher" in entry:
            lines.append(f"matcher = {_toml_string(entry['matcher'])}")
        lines.append(f"command = {_toml_string(entry['command'])}")
        lines.append(f"timeout = {entry['timeout']}")
        lines.append("")
    lines.append(BLOCK_END)
    return "\n".join(lines) + "\n"


# ----- config.toml merge ---------------------------------------------------


def _strip_block(text: str) -> str:
    """Remove the managed block, leaving the user's content exactly as it was."""
    stripped = _BLOCK_RE.sub("\n", text, count=1)
    return stripped


def merge_config_hooks(ctx, key: str, config_path: Path, block: str) -> FileAction:
    """Splice the managed hook block into ``config.toml`` without reformatting it.

    The user's TOML is never parsed and re-emitted -- only the marker-delimited
    region is replaced -- so comments, table order, and whitespace outside the
    block survive byte-for-byte. The merged result is validated with ``tomllib``
    before it is committed; on a parse failure nothing is written and the reason
    is logged, because a config Kimi cannot load would take the user's providers,
    models, and permission rules down with it.
    """
    original = config_path.read_text(encoding="utf-8") if config_path.exists() else ""

    if original.strip():
        try:
            tomllib.loads(original)
        except tomllib.TOMLDecodeError as exc:
            # A file that is already invalid is the user's to fix; splicing into
            # it would make our block look like the cause.
            ctx.manifest.log(key, f"skip-malformed-toml: {config_path} ({exc})")
            return FileAction(path=str(config_path), action="kept")

    body = _strip_block(original).rstrip("\n")
    if body:
        updated = f"{body}\n\n{block}"
    else:
        updated = block

    try:
        tomllib.loads(updated)
    except tomllib.TOMLDecodeError as exc:
        ctx.manifest.log(key, f"rollback-invalid-merge: {config_path} ({exc})")
        return FileAction(path=str(config_path), action="kept")

    content = updated.encode("utf-8")
    if config_path.exists() and config_path.read_bytes() == content:
        ctx.manifest.track(key, str(config_path))
        return FileAction(path=str(config_path), action="unchanged")

    existed = config_path.exists()
    if not ctx.dry_run:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if existed:
            backup = config_path.with_suffix(config_path.suffix + ".nexus-hub.bak")
            backup.write_bytes(config_path.read_bytes())
            ctx.manifest.track(key, str(backup))
        tmp = config_path.with_suffix(config_path.suffix + ".nexus-hub.tmp")
        tmp.write_text(updated, encoding="utf-8")
        os.replace(tmp, config_path)
    # Tracked in the regular bucket; the integration's teardown prunes and
    # untracks this path before the manifest sweep, so the user's config file is
    # never deleted.
    ctx.manifest.track(key, str(config_path))
    return FileAction(path=str(config_path), action="updated" if existed else "created")


def prune_config_hooks(config_path: Path, dry_run: bool) -> FileAction:
    """Remove the managed hook block from ``config.toml`` during teardown.

    The file is deleted only when the block was its entire content; otherwise the
    user's configuration is rewritten without our region.
    """
    if not config_path.exists():
        return FileAction(path=str(config_path), action="not-found")
    original = config_path.read_text(encoding="utf-8")
    if BLOCK_START not in original:
        return FileAction(path=str(config_path), action="unchanged")

    remainder = _strip_block(original).strip()
    if not remainder:
        if not dry_run:
            config_path.unlink(missing_ok=True)
        return FileAction(path=str(config_path), action="removed")

    content = remainder + "\n"
    if not dry_run:
        config_path.write_text(content, encoding="utf-8")
    return FileAction(path=str(config_path), action="updated")


def hooks_block_entries(config_path: Path) -> list[dict]:
    """Return the ``[[hooks]]`` entries currently inside the managed block.

    Used by tests and by verification to read back what was registered without
    re-deriving it from the catalog.
    """
    if not config_path.exists():
        return []
    text = config_path.read_text(encoding="utf-8")
    match = re.search(
        rf"{re.escape(BLOCK_START)}(.*?){re.escape(BLOCK_END)}", text, re.DOTALL
    )
    if match is None:
        return []
    parsed = tomllib.loads(match.group(1))
    return list(parsed.get("hooks", []))


__all__ = [
    "BLOCK_END",
    "BLOCK_START",
    "KIMI_HOOK_EVENTS",
    "KIMI_HOOK_FIELDS",
    "KIMI_HOOK_TIMEOUT_S",
    "KIMI_TOOL_EVENTS",
    "KIMI_TOOL_NAMES",
    "agent_is_loadable",
    "agents_to_kimi",
    "build_kimi_hooks",
    "hooks_block_entries",
    "merge_config_hooks",
    "prune_config_hooks",
    "render_hooks_block",
]
