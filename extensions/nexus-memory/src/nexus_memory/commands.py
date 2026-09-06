"""Read / record / merge / search / zoom / drop over the store and tree."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .changelog import append_event
from .record import display_body, format_record, parse_record
from .store import MemoryStore
from .tiling import tile
from .tree import MissingChildError, TreeStore


def _tree(store: MemoryStore) -> TreeStore:
    return TreeStore(
        store.root,
        record_width=store.config.record_width,
        log_count=store.count(),
    )


def _self_cmd(store: MemoryStore, extra: list[str]) -> str:
    try:
        lib = Path(__file__).resolve().parents[4] / "scripts" / "lib"
        if lib.is_dir() and str(lib) not in sys.path:
            sys.path.insert(0, str(lib))
        from self_naming import runnable_self_command

        return runnable_self_command(
            ["--root", str(store.root), *extra],
            script_path=Path(sys.argv[0]) if sys.argv else None,
        )
    except Exception:
        joined = " ".join(extra)
        return f"python -m nexus_memory --root {store.root} {joined}"


def _page(text: str, store: MemoryStore, part: int) -> str:
    try:
        lib = Path(__file__).resolve().parents[4] / "scripts" / "lib"
        if lib.is_dir() and str(lib) not in sys.path:
            sys.path.insert(0, str(lib))
        from output_paging import emit_paged

        return emit_paged(
            text,
            part=part,
            max_bytes=store.config.page_max_bytes,
            max_lines=store.config.page_max_lines,
            extra_args=["--root", str(store.root), "read"],
            script_path=Path(sys.argv[0]) if sys.argv else None,
        )
    except Exception:
        return text


def render_read(store: MemoryStore) -> str:
    n = store.count()
    if n == 0:
        return ""
    budget = store.config.read_budget
    ranges = tile(n, budget)
    tree = _tree(store)
    lines: list[str] = []
    for lo, hi in ranges:
        if hi - lo == 1:
            lines.append(display_body(store.get(lo)))
            continue
        summary = tree.get(lo, hi)
        if summary:
            lines.append(summary)
        else:
            lines.append(f"[{lo}:{hi} pending merge]")
    return "\n".join(lines) + ("\n" if lines else "")


def cmd_read(store: MemoryStore, part: int = 1) -> str:
    return _page(render_read(store), store, part)


def _merge_request(store: MemoryStore, lo: int, hi: int) -> str:
    tree = _tree(store)
    max_chars = store.config.max_entry_length
    size = hi - lo
    if size == 2:
        content = display_body(store.get(lo)) + "\n" + display_body(store.get(lo + 1))
    else:
        try:
            left, right = tree.child_contents(lo, hi)
        except MissingChildError as exc:
            return str(exc) + "\n"
        content = left + "\n" + right
    ret = _self_cmd(store, ["merge", "--lo", str(lo), "--hi", str(hi), "--text"])
    return (
        f"# merge [{lo}, {hi})\n"
        f"# keep what has lasting effect; invent nothing\n"
        f"# max_chars: {max_chars}\n"
        f"# return: {ret} \"SUMMARY\"\n"
        f"{content}\n"
    )


def cmd_record(
    store: MemoryStore,
    text: str,
    *,
    source: str | None = None,
    tier: str = "working",
    derived_from: tuple[str, ...] = (),
    supersedes: int | None = None,
) -> str:
    """Append one lasting entry. Rejects a write with no source."""
    if source is None:
        parsed = parse_record(text, strict=True)
        payload = text
        origin = parsed.source
    else:
        payload = format_record(
            text,
            source=source,
            tier=tier,
            derived_from=derived_from,
            supersedes=supersedes,
        )
        origin = source
    index = store.append(payload)
    append_event(store.root, "added", index, origin)
    if supersedes is not None:
        append_event(
            store.root,
            "superseded",
            supersedes,
            origin,
            reason=f"replaced-by:{index}",
        )
    tree = _tree(store)
    pending = tree.pending()
    if not pending:
        return ""
    lo, hi = pending[0]
    return _merge_request(store, lo, hi)


def cmd_merge(store: MemoryStore, lo: int, hi: int, text: str) -> str:
    tree = _tree(store)
    if hi - lo > 2:
        tree.child_contents(lo, hi)
    if not text.strip():
        raise MissingChildError(
            f"refusing a blank summary for [{lo}, {hi}). Recover with: "
            + _self_cmd(store, ["drop", "--lo", str(lo), "--hi", str(hi)])
        )
    tree.put(lo, hi, text.strip())
    return ""


def cmd_search(store: MemoryStore, pattern: str) -> str:
    compiled = re.compile(pattern)
    hits: list[str] = []
    for i in range(store.count()):
        entry = store.get(i)
        if compiled.search(entry):
            hits.append(f"{i}: {entry}")
    return "\n".join(hits) + ("\n" if hits else "")


def cmd_zoom(store: MemoryStore, lo: int, hi: int) -> str:
    mid = lo + (hi - lo) // 2
    tree = _tree(store)
    lines: list[str] = []
    for a, b in ((lo, mid), (mid, hi)):
        if b - a == 1:
            lines.append(display_body(store.get(a)))
        else:
            summary = tree.get(a, b)
            lines.append(summary if summary else f"[{a}:{b} pending merge]")
    return "\n".join(lines) + "\n"


def cmd_drop(store: MemoryStore, lo: int, hi: int) -> str:
    _tree(store).drop(lo, hi)
    return ""
