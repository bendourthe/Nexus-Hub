"""Mirror catalog/commands/ into a tool's *global* slash-command directory.

Some assistants expose a user-global command surface that every project reads
without any per-project install:

  - Cursor scans ``~/.cursor/commands/<name>.md`` (and project ``.cursor/commands/``).
  - VS Code / GitHub Copilot scans user-profile ``prompts/<name>.prompt.md``.

This helper writes one file per catalog command into that directory and prunes
command files a previous install left behind that are no longer in the catalog
(so commands removed/renamed upstream disappear on the next install). Pruning is
manifest-scoped: only files THIS integration previously tracked in THIS
directory are ever removed, so a user's own commands living in the same folder
are never touched.

Used by the Cursor and Copilot integrations, both of which were confirmed
(empirically, on a repo with no local install) to surface these global files as
slash commands.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext
from .result import FileAction


def mirror_command_surface(
    ctx: InstallContext, key: str, dst_dir: Path, *, suffix: str = ".md"
) -> list[FileAction]:
    """Write every ``catalog/commands/*.md`` into ``dst_dir`` as ``<stem><suffix>``.

    Returns one ``FileAction`` per command written (created/updated/unchanged)
    plus one ``removed`` action per pruned stale command. The command bodies are
    copied verbatim -- the Nexus-Hub command frontmatter (``description:``) is
    valid for both Cursor commands and VS Code prompt files.
    """
    actions: list[FileAction] = []
    src_dir = ctx.repo_root / "catalog" / "commands"
    if not src_dir.exists():
        ctx.manifest.log(key, f"missing: {src_dir}")
        return [FileAction(path=str(src_dir), action="not-found")]
    if not ctx.dry_run:
        dst_dir.mkdir(parents=True, exist_ok=True)

    current_names: set[str] = set()
    for md in sorted(src_dir.glob("*.md")):
        out_name = f"{md.stem}{suffix}"
        current_names.add(out_name)
        dst = dst_dir / out_name
        content = md.read_bytes()
        if dst.exists() and dst.read_bytes() == content:
            ctx.manifest.track(key, str(dst))
            actions.append(FileAction(path=str(dst), action="unchanged"))
            continue
        existed = dst.exists()
        if not ctx.dry_run:
            dst.write_bytes(content)
        ctx.manifest.track(key, str(dst))
        actions.append(
            FileAction(path=str(dst), action="updated" if existed else "created")
        )

    # Prune: command files this integration previously installed into dst_dir
    # that are no longer in the catalog. Manifest-scoped so a user's own files
    # in the same directory are never removed.
    try:
        dst_resolved = dst_dir.resolve()
    except OSError:
        dst_resolved = dst_dir
    for tracked in list(ctx.manifest.files_for(key)):
        tp = Path(tracked)
        if not tp.name.endswith(suffix) or tp.name in current_names:
            continue
        try:
            same_dir = tp.parent.resolve() == dst_resolved
        except OSError:
            same_dir = False
        if not same_dir:
            continue
        if tp.exists() and not ctx.dry_run:
            tp.unlink()
        ctx.manifest.untrack(key, tracked)
        actions.append(FileAction(path=str(tp), action="removed"))
    return actions
