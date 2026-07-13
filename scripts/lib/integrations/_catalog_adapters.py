"""Catalog-to-platform materialization adapters.

Nexus-Hub keeps ONE canonical catalog (``catalog/skills/<category>/<name>/``,
``catalog/commands/<name>.md``, ...). Each platform, however, reads skills and
commands in its own shape and location. Rather than reorganize the catalog per
platform, every integration translates the canonical catalog into the target
platform's native form via the three adapters here. This is the operational core
of the "adapter pattern" documented in ``docs/policy/platform-read-contracts.md``.

The three adapters:

  - ``flatten_skills`` -- ``catalog/skills/<category>/<name>/`` -> ``<dst>/<name>/``.
    Both Codex and the Antigravity IDE discover skills exactly one level under
    their skills directory (``skills/<name>/SKILL.md``), so the catalog's category
    layer MUST be dropped or nothing registers. Skill folder names are globally
    unique across categories (enforced by the catalog), so flattening never
    collides.
  - ``commands_to_skills`` -- synthesize ``<dst>/<name>/SKILL.md`` from each
    ``catalog/commands/<name>.md`` so a command surfaces as a reusable skill
    (``$name`` in Codex / the new ChatGPT desktop app). The synthesized frontmatter
    carries only ``name`` + ``description`` -- exactly what Codex and Antigravity
    require -- and the command body becomes the skill body.
  - ``commands_to_slash`` -- emit slash-command files (verbatim ``.md`` for
    Claude / Antigravity workflows; top-level ``.md`` for the legacy Codex prompts
    surface).

All three return ``list[FileAction]``, honor ``ctx.dry_run`` / ``ctx.overwrite``,
and track written paths in ``ctx.manifest`` so the default teardown removes them.
Generated files are Nexus-Hub-owned derived artifacts, so (like
``_command_surface.mirror_command_surface``) they sync on byte-difference rather
than preserving stale copies. This module is stdlib-only and makes no outbound
calls.
"""

from __future__ import annotations

from pathlib import Path

from .base import IntegrationBase
from .result import FileAction

_VALID_SLASH_STYLES = frozenset({"verbatim", "codex_prompts"})


def _write_synced(
    ctx, key: str, dst: Path, content: bytes
) -> FileAction:
    """Write ``content`` to ``dst``, syncing on byte-difference.

    Matches the derived-artifact semantics of ``mirror_command_surface``: the
    file is Nexus-Hub-owned, so it is (re)written whenever the bytes differ,
    independent of ``ctx.overwrite``. Returns ``unchanged`` / ``created`` /
    ``updated`` and always tracks the path in the manifest.
    """
    if dst.exists() and dst.read_bytes() == content:
        ctx.manifest.track(key, str(dst))
        return FileAction(path=str(dst), action="unchanged")
    existed = dst.exists()
    if not ctx.dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(content)
    ctx.manifest.track(key, str(dst))
    return FileAction(path=str(dst), action="updated" if existed else "created")


def catalog_skill_names(src_skills_dir: Path) -> set:
    """Return the set of skill folder names under ``catalog/skills/<category>/``.

    Used to guard ``commands_to_skills`` against a command whose name collides
    with a real catalog skill (so the command wrapper never shadows a skill).
    """
    names: set = set()
    if src_skills_dir.exists():
        for category in src_skills_dir.iterdir():
            if category.is_dir():
                for skill in category.iterdir():
                    if skill.is_dir():
                        names.add(skill.name)
    return names


def flatten_skills(ctx, key: str, src_skills_dir: Path, dst_skills_dir: Path) -> list[FileAction]:
    """Flatten ``catalog/skills/<category>/<name>/`` into ``<dst>/<name>/``.

    Copies each skill folder (with its bundled ``scripts/``/``references/``/
    ``assets/`` subdirs intact) directly under ``dst_skills_dir``, dropping the
    category level. Returns one ``FileAction`` per skill tree copied, or a single
    ``not-found`` action when the source tree is missing.
    """
    if not src_skills_dir.exists():
        ctx.manifest.log(key, f"missing-tree: {src_skills_dir}")
        return [FileAction(path=str(src_skills_dir), action="not-found")]
    IntegrationBase._ensure_dir(dst_skills_dir, ctx)
    actions: list[FileAction] = []
    for category in sorted(p for p in src_skills_dir.iterdir() if p.is_dir()):
        for skill in sorted(p for p in category.iterdir() if p.is_dir()):
            actions.append(
                IntegrationBase._copy_tree(skill, dst_skills_dir / skill.name, ctx, key)
            )
    return actions


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Split a Markdown doc into its simple ``key: value`` frontmatter and body.

    Only the flat single-line ``key: value`` shape used by Nexus-Hub command
    files is parsed (no nested or multi-line YAML values -- commands do not use
    them). Returns ``({}, text)`` when no ``---``-delimited frontmatter is present.
    """
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines(keepends=True)
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    meta: dict[str, str] = {}
    for raw in lines[1:end]:
        if ":" in raw:
            k, _, v = raw.partition(":")
            meta[k.strip()] = v.strip()
    body = "".join(lines[end + 1:]).lstrip("\n")
    return meta, body


def _yaml_double_quote(value: str) -> str:
    """Return ``value`` as a safe YAML double-quoted scalar on a single line."""
    collapsed = " ".join(value.split())
    escaped = collapsed.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _synthesize_skill(name: str, command_text: str) -> bytes:
    """Build a SKILL.md body from a command file's frontmatter + body.

    Frontmatter carries only ``name`` + ``description`` (the required-and-
    sufficient set for Codex and Antigravity). The description gets a
    "Run the /<name> command." lead-in so the skill router understands the skill
    maps to a slash command, followed by the command's own description. The
    command body becomes the skill body verbatim.
    """
    meta, body = _split_frontmatter(command_text)
    source_desc = meta.get("description", "").strip()
    lead_in = f"Run the /{name} command."
    description = f"{lead_in} {source_desc}".strip() if source_desc else lead_in
    front = (
        "---\n"
        f"name: {name}\n"
        f"description: {_yaml_double_quote(description)}\n"
        "---\n\n"
    )
    return (front + body).encode("utf-8")


def commands_to_skills(
    ctx,
    key: str,
    src_commands_dir: Path,
    dst_skills_dir: Path,
    existing_skill_names: set[str] | None = None,
) -> list[FileAction]:
    """Materialize every ``catalog/commands/<name>.md`` as ``<dst>/<name>/SKILL.md``.

    A command whose name collides with a real catalog skill folder (passed via
    ``existing_skill_names``) is skipped and logged, so a genuine skill is never
    shadowed by a command wrapper. Returns one ``FileAction`` per command written
    (or a single ``not-found`` action when the commands tree is missing).
    """
    if not src_commands_dir.exists():
        ctx.manifest.log(key, f"missing-tree: {src_commands_dir}")
        return [FileAction(path=str(src_commands_dir), action="not-found")]
    IntegrationBase._ensure_dir(dst_skills_dir, ctx)
    existing = existing_skill_names or set()
    actions: list[FileAction] = []
    for md in sorted(src_commands_dir.glob("*.md")):
        name = md.stem
        if name in existing:
            ctx.manifest.log(
                key, f"skip command-skill (name collides with catalog skill): {name}"
            )
            continue
        content = _synthesize_skill(name, md.read_text(encoding="utf-8"))
        dst = dst_skills_dir / name / "SKILL.md"
        actions.append(_write_synced(ctx, key, dst, content))
    return actions


def commands_to_slash(
    ctx,
    key: str,
    src_commands_dir: Path,
    dst_dir: Path,
    style: str = "verbatim",
) -> list[FileAction]:
    """Emit each ``catalog/commands/<name>.md`` as a flat slash-command file.

    ``style="verbatim"`` (Claude / Antigravity workflows) and
    ``style="codex_prompts"`` (the legacy Codex ``~/.codex/prompts`` surface, which
    reads top-level ``.md`` only) both write ``<dst>/<name>.md`` with the command
    body unchanged; the parameter is retained so callers are explicit and a future
    format that needs transformation can branch here. Returns one ``FileAction``
    per command (or a single ``not-found`` action when the tree is missing).
    """
    if style not in _VALID_SLASH_STYLES:
        raise ValueError(
            f"Unknown slash style {style!r}; must be one of {sorted(_VALID_SLASH_STYLES)}"
        )
    if not src_commands_dir.exists():
        ctx.manifest.log(key, f"missing-tree: {src_commands_dir}")
        return [FileAction(path=str(src_commands_dir), action="not-found")]
    IntegrationBase._ensure_dir(dst_dir, ctx)
    actions: list[FileAction] = []
    for md in sorted(src_commands_dir.glob("*.md")):
        dst = dst_dir / md.name
        actions.append(_write_synced(ctx, key, dst, md.read_bytes()))
    return actions


__all__ = [
    "catalog_skill_names",
    "flatten_skills",
    "commands_to_skills",
    "commands_to_slash",
]
