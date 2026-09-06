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
    (``$name`` in Codex / the new ChatGPT desktop app). The synthesized
    frontmatter carries ``name``, ``description``, and
    ``disable-model-invocation: true`` so slash-command bodies are not
    model-auto-invoked on platforms that honor the field. The command body
    becomes the skill body.
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

    A directory without a ``SKILL.md`` is not a skill (see ``flatten_skills``),
    so it never reserves a name here either -- otherwise an abandoned scaffold
    would suppress a legitimate command wrapper that shares its name.
    """
    names: set = set()
    if src_skills_dir.exists():
        for category in src_skills_dir.iterdir():
            if category.is_dir():
                for skill in category.iterdir():
                    if skill.is_dir() and (skill / "SKILL.md").is_file():
                        names.add(skill.name)
    return names


def flatten_skills(ctx, key: str, src_skills_dir: Path, dst_skills_dir: Path) -> list[FileAction]:
    """Flatten ``catalog/skills/<category>/<name>/`` into ``<dst>/<name>/``.

    Copies each skill folder (with its bundled ``scripts/``/``references/``/
    ``assets/`` subdirs intact) directly under ``dst_skills_dir``, dropping the
    category level. Returns one ``FileAction`` per skill tree copied, or a single
    ``not-found`` action when the source tree is missing.

    A source directory without a ``SKILL.md`` is skipped rather than copied.
    Every target platform discovers skills by reading ``<skills>/<name>/SKILL.md``
    one level deep, so publishing a bare directory would deliver a "skill" no
    platform can load -- and it breaks the depth-1 contract the platform tests
    assert. Skips are recorded in the manifest log so an in-progress scaffold is
    visible rather than silently dropped.
    """
    if not src_skills_dir.exists():
        ctx.manifest.log(key, f"missing-tree: {src_skills_dir}")
        return [FileAction(path=str(src_skills_dir), action="not-found")]
    IntegrationBase._ensure_dir(dst_skills_dir, ctx)
    actions: list[FileAction] = []
    for category in sorted(p for p in src_skills_dir.iterdir() if p.is_dir()):
        for skill in sorted(p for p in category.iterdir() if p.is_dir()):
            if not (skill / "SKILL.md").is_file():
                ctx.manifest.log(key, f"skipped-no-skill-md: {skill}")
                continue
            # v3.16.1 Phase 6.3 -- selection filter. Returns True for everything
            # when no selection is active, so an unfiltered install walks the
            # identical path it always did.
            if not ctx.selects_skill(skill.name):
                ctx.manifest.log(key, f"skipped-not-selected: {skill.name}")
                continue
            actions.append(
                IntegrationBase._copy_tree(skill, dst_skills_dir / skill.name, ctx, key)
            )
    return actions


def _declares_manual_only(skill_md: Path) -> bool:
    """True when a skill's frontmatter sets ``disable-model-invocation: true``.

    Deliberately a narrow line scan rather than a YAML parse: this runs inside
    the installer, which must not acquire a PyYAML dependency, and
    ``validate_skills.py`` has already rejected any non-boolean value before a
    skill can reach a release.
    """
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if not text.startswith("---"):
        return False
    _, _, rest = text.partition("---")
    block, _, _ = rest.partition("\n---")
    for line in block.splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "disable-model-invocation":
            return value.strip().lower() == "true"
    return False


def _selected_skill(ctx, name: str) -> bool:
    fn = getattr(ctx, "selects_skill", None)
    return fn(name) if callable(fn) else True


def _selected_command(ctx, name: str) -> bool:
    fn = getattr(ctx, "selects_command", None)
    return fn(name) if callable(fn) else True


def _manual_only_skill_names(ctx, dst_skills_dir: Path) -> list[str]:
    """Skill names that need a Codex sidecar, without requiring dest files.

    Dest is empty during ``dry_run`` because ``_write_generated`` does not
    materialize SKILL.md. Planning from the source catalog + command list is
    what keeps ``test_dry_run_matches_install[codex]`` honest after command
    skills started declaring ``disable-model-invocation: true``.
    """
    names: set[str] = set()
    if dst_skills_dir.is_dir():
        for skill_dir in dst_skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if skill_md.is_file() and _declares_manual_only(skill_md):
                names.add(skill_dir.name)

    repo = getattr(ctx, "repo_root", None)
    if repo is None:
        return sorted(names)

    src_skills = Path(repo) / "catalog" / "skills"
    src_commands = Path(repo) / "catalog" / "commands"
    if src_skills.is_dir():
        for skill_md in src_skills.rglob("SKILL.md"):
            if not skill_md.is_file():
                continue
            name = skill_md.parent.name
            if not _selected_skill(ctx, name):
                continue
            if _declares_manual_only(skill_md):
                names.add(name)
    if src_commands.is_dir():
        existing = catalog_skill_names(src_skills) if src_skills.is_dir() else set()
        for md in src_commands.glob("*.md"):
            name = md.stem
            if name in existing:
                continue
            if not _selected_command(ctx, name):
                continue
            names.add(name)
    return sorted(names)


def codex_invocation_policy(ctx, key: str, dst_skills_dir: Path) -> list[FileAction]:
    """Emit Codex's ``agents/openai.yaml`` sidecar for manual-only skills.

    Codex expresses the same intent as Claude's ``disable-model-invocation``
    through a different file, a different key, and the OPPOSITE polarity:
    ``policy.allow_implicit_invocation`` in ``<skill>/agents/openai.yaml``,
    default ``true``. So ``disable-model-invocation: true`` maps to
    ``allow_implicit_invocation: false``; the value is inverted, never copied.

    Emits nothing for a skill that does not declare the field, because Codex's
    default already matches Nexus-Hub's default. A skill that ships its own
    ``agents/openai.yaml`` is left alone: an authored sidecar carries interface
    and dependency metadata this function cannot reconstruct, so overwriting it
    to set one policy key would destroy the rest.

    Names come from dest SKILL.md files when those exist, and from the source
    catalog plus command list otherwise, so a dry-run (which does not write
    dest files) still reports the same sidecar FileActions as a real install.

    Verified against OpenAI's own skill-authoring documentation on 2026-08-18
    and re-fetched 2026-08-24; see ``docs/policy/skill-invocation-policy-levers.md``.
    """
    actions: list[FileAction] = []
    for name in _manual_only_skill_names(ctx, dst_skills_dir):
        sidecar = dst_skills_dir / name / "agents" / "openai.yaml"
        if sidecar.exists() and "allow_implicit_invocation" not in sidecar.read_text(
            encoding="utf-8", errors="replace"
        ):
            # An authored sidecar with other metadata. Leave it; say so.
            ctx.manifest.log(key, f"kept-authored-sidecar: {sidecar}")
            continue

        content = (
            "# Generated by Nexus-Hub from this skill's "
            "`disable-model-invocation: true`.\n"
            "# Codex's polarity is inverted: allow_implicit_invocation false "
            "== do not auto-invoke.\n"
            "policy:\n"
            "  allow_implicit_invocation: false\n"
        )
        actions.append(
            IntegrationBase._write_generated(sidecar, content, ctx, key)
        )
    return actions


def nested_skills_selected(ctx, key: str, src_skills_dir: Path, dst_skills_dir: Path) -> list[FileAction]:
    """Mirror ``catalog/skills/<category>/<name>/`` keeping the category level,
    copying only the selected skills.

    This exists ONLY for the filtered case. An unfiltered install still goes
    through the single whole-tree ``_copy_tree`` call it always used, so the
    contract's byte-equivalence requirement does not depend on this function
    reproducing that behavior exactly. Splitting the two paths is deliberate:
    a per-skill walk that must be proven identical to a bulk tree copy is a
    much weaker guarantee than simply not taking it.
    """
    if not src_skills_dir.exists():
        ctx.manifest.log(key, f"missing-tree: {src_skills_dir}")
        return [FileAction(path=str(src_skills_dir), action="not-found")]
    IntegrationBase._ensure_dir(dst_skills_dir, ctx)
    actions: list[FileAction] = []
    for category in sorted(p for p in src_skills_dir.iterdir() if p.is_dir()):
        for skill in sorted(p for p in category.iterdir() if p.is_dir()):
            if not (skill / "SKILL.md").is_file():
                ctx.manifest.log(key, f"skipped-no-skill-md: {skill}")
                continue
            if not ctx.selects_skill(skill.name):
                ctx.manifest.log(key, f"skipped-not-selected: {skill.name}")
                continue
            actions.append(
                IntegrationBase._copy_tree(
                    skill, dst_skills_dir / category.name / skill.name, ctx, key
                )
            )
    return actions


def flat_md_selected(ctx, key: str, src_dir: Path, dst_dir: Path, surface: str) -> list[FileAction]:
    """Copy ``<src>/<name>.md`` files, keeping only the selected ones.

    `surface` is "command" or "agent" and picks which predicate applies. Like
    `nested_skills_selected`, this is the filtered path only.
    """
    if not src_dir.exists():
        ctx.manifest.log(key, f"missing-tree: {src_dir}")
        return [FileAction(path=str(src_dir), action="not-found")]
    predicate = ctx.selects_command if surface == "command" else ctx.selects_agent
    IntegrationBase._ensure_dir(dst_dir, ctx)
    actions: list[FileAction] = []
    for md in sorted(src_dir.glob("*.md")):
        if not predicate(md.stem):
            ctx.manifest.log(key, f"skipped-not-selected: {surface} {md.stem}")
            continue
        actions.append(_write_synced(ctx, key, dst_dir / md.name, md.read_bytes()))
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

    Frontmatter carries ``name``, ``description``, and
    ``disable-model-invocation: true``. Command-derived skills are user-invoked
    slash dispatchers; leaving the flag off would let the model auto-load the
    command body as if it were a catalog skill. Platforms that do not document
    the field ignore it. Codex maps it through ``codex_invocation_policy``
    (inverted sidecar) after this file is written.

    The description gets a "Run the /<name> command." lead-in so the skill
    router understands the skill maps to a slash command, followed by the
    command's own description. The command body becomes the skill body
    verbatim.
    """
    meta, body = _split_frontmatter(command_text)
    source_desc = meta.get("description", "").strip()
    lead_in = f"Run the /{name} command."
    description = f"{lead_in} {source_desc}".strip() if source_desc else lead_in
    front = (
        "---\n"
        f"name: {name}\n"
        f"description: {_yaml_double_quote(description)}\n"
        "disable-model-invocation: true\n"
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
        # v3.16.1 Phase 6.3 -- a command-as-skill wrapper follows its command's
        # eligibility. Emitting a wrapper for a command the selection excluded
        # would reintroduce the surface through the side door.
        if not ctx.selects_command(name):
            ctx.manifest.log(key, f"skipped-not-selected: command-skill {name}")
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
        # v3.16.1 Phase 6.3 -- the slash surface follows command eligibility, so
        # a focused install cannot leave a /command whose skills are absent.
        if not ctx.selects_command(md.stem):
            ctx.manifest.log(key, f"skipped-not-selected: slash {md.stem}")
            continue
        dst = dst_dir / md.name
        actions.append(_write_synced(ctx, key, dst, md.read_bytes()))
    return actions


__all__ = [
    "catalog_skill_names",
    "flatten_skills",
    "commands_to_skills",
    "commands_to_slash",
    "nested_skills_selected",
    "flat_md_selected",
]
