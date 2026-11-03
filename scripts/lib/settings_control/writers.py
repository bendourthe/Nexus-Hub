"""Lossless, atomic writers for the user-level tool configuration files.

`write_json_keys` edits Claude Code and Copilot CLI `settings.json` (and the
Nexus-Hub guardrails file) by changing only the text of the value it touches, so
every other byte (indentation, key order, compact arrays, a trailing newline, a
BOM) stays exactly as found. `write_toml_keys` edits Codex `config.toml` through
`tomlkit`, which round-trips comments and layout. Both share one commit path:

- Keys are addressed only as segment arrays, so a dotted model id is never split.
  A segment must match `SEGMENT`, and anything else is refused.
- A file that does not parse is refused untouched, and the refusal names the line.
  An absent file is created holding only the written key, and the result says so
  (`file_created`) so a later reset can delete it again.
- The target is resolved through symlinks and the temporary file is written beside
  the real file. Its mode bits are copied over (and on Windows its DACL, through
  advapi32, with no child process).
- The target is re-read and its SHA-256 compared with the snapshot immediately
  before the rename, so a file changed between read and write is refused. The
  window that remains between that comparison and the rename is a few
  microseconds and is not closed: no portable compare-and-rename exists.
- The new text is parsed again and compared with the old data plus the requested
  edits before anything is renamed, so an editing defect refuses the write instead
  of corrupting the file. A failed write never leaves a partial file.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .readers import plain_data

SEGMENT = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.:@\[\]/-]{0,127}\Z")
MAX_BYTES = 8_000_000
MAX_DEPTH = 64
_BOM = b"\xef\xbb\xbf"
_WS = " \t\n\r"


class _Absent:
    """Sentinel for "remove this key"."""

    def __repr__(self) -> str:
        return "ABSENT"


ABSENT: Any = _Absent()


class WriterRefusal(Exception):
    """The write was refused and nothing was changed."""


@dataclass(frozen=True)
class Edit:
    """Set `key_path` to `value`, or remove it when `value` is `ABSENT`.

    `created_depth` (removal only) is how many leading segments already existed
    when the key was first written: ancestors below that depth that become empty
    are removed with the key. `restore` (JSON set only) is the `removal` hint a
    previous removal returned: when the key is still absent and its neighbor is
    where it was, the exact removed text is put back, so a removal and its undo
    leave the file byte for byte as it was.
    """

    key_path: tuple[str, ...]
    value: Any
    created_depth: int | None = None
    restore: dict[str, Any] | None = None


@dataclass(frozen=True)
class Change:
    key_path: tuple[str, ...]
    previous_present: bool
    previous: Any
    new_present: bool
    new: Any
    created_depth: int
    removal: dict[str, Any] | None = None


@dataclass(frozen=True)
class Loaded:
    """One file read once: bytes, parsed data, and the facts a commit must preserve."""

    path: Path
    real: Path
    display: str
    fmt: str
    exists: bool
    raw: bytes
    text: str
    data: dict[str, Any]
    sha: str | None
    bom: bool
    newline: str


@dataclass(frozen=True)
class Plan:
    loaded: Loaded
    new_bytes: bytes
    changes: tuple[Change, ...]
    file_created: bool
    delete_file: bool = False

    @property
    def changed(self) -> bool:
        return self.delete_file or self.new_bytes != self.loaded.raw


# --------------------------------------------------------------------------
# Plain-data helpers
# --------------------------------------------------------------------------


def same(left: Any, right: Any) -> bool:
    """Equality that keeps `True` and `1` apart."""
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(same(left[k], right[k]) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(same(a, b) for a, b in zip(left, right))
    return left == right


def lookup(data: Any, key_path: tuple[str, ...] | list[str]) -> tuple[bool, Any]:
    node = data
    for part in key_path:
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def check_segments(key_path: tuple[str, ...] | list[str]) -> None:
    if not key_path:
        raise WriterRefusal("a key path must have at least one segment")
    for part in key_path:
        if not isinstance(part, str) or not SEGMENT.match(part):
            raise WriterRefusal(f"key segment {part!r} is not a valid name")


def _check_value(value: Any) -> None:
    if value is ABSENT:
        return
    try:
        json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise WriterRefusal(f"value {value!r} cannot be written ({exc})") from exc


def _apply_to_data(data: dict[str, Any], edits: list[Edit]) -> dict[str, Any]:
    """The data a correct edit must produce. Pure; used to verify the text edit."""
    out = json.loads(json.dumps(data))
    for edit in edits:
        path = list(edit.key_path)
        if edit.value is ABSENT:
            parents: list[tuple[dict[str, Any], str]] = []
            node: Any = out
            for part in path[:-1]:
                if not isinstance(node, dict) or part not in node:
                    node = None
                    break
                parents.append((node, part))
                node = node[part]
            if isinstance(node, dict):
                node.pop(path[-1], None)
                depth = edit.created_depth if edit.created_depth is not None else len(path)
                for index in range(len(parents) - 1, -1, -1):
                    holder, name = parents[index]
                    if index >= depth and isinstance(holder.get(name), dict) and not holder[name]:
                        del holder[name]
                    else:
                        break
            continue
        node = out
        for part in path[:-1]:
            child = node.get(part) if isinstance(node, dict) else None
            if child is None and part not in node:
                node[part] = {}
            node = node[part]
        node[path[-1]] = json.loads(json.dumps(edit.value))
    return out


def _created_depth(data: dict[str, Any], key_path: tuple[str, ...]) -> int:
    node: Any = data
    for index, part in enumerate(key_path):
        if not isinstance(node, dict) or part not in node:
            return index
        node = node[part]
    return len(key_path)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------


def _detect_newline(text: str) -> str:
    crlf = text.count("\r\n")
    lone = text.count("\n") - crlf
    return "\r\n" if crlf and not lone else "\n"


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, max(index, 0)) + 1


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def _no_constant(name: str) -> Any:
    raise ValueError(f"{name} is not valid JSON")


def _import_tomlkit() -> Any:
    try:
        import tomlkit
    except ImportError as exc:
        raise WriterRefusal("tomlkit is not installed, so this file was not written: run pip install tomlkit") from exc
    return tomlkit


def load(path: Path, fmt: str, display: str | None = None) -> Loaded:
    """Read `path` once. Raises `WriterRefusal` for a file that must not be written."""
    shown = display or str(path)
    real = Path(os.path.realpath(path))
    if fmt == "toml":
        _import_tomlkit()
    if not real.exists():
        return Loaded(Path(path), real, shown, fmt, False, b"", "", {}, None, False, "\n")
    if not real.is_file():
        raise WriterRefusal(f"{shown} is not a regular file")
    try:
        raw = real.read_bytes()
    except OSError as exc:
        raise WriterRefusal(f"{shown} cannot be read ({exc.strerror or exc})") from exc
    if len(raw) > MAX_BYTES:
        raise WriterRefusal(f"{shown} is over {MAX_BYTES // 1_000_000} MB")
    bom = raw.startswith(_BOM)
    try:
        text = (raw[len(_BOM):] if bom else raw).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WriterRefusal(f"{shown} is not valid UTF-8") from exc
    data = _parse_data(text, fmt, shown)
    return Loaded(Path(path), real, shown, fmt, True, raw, text, data, hashlib.sha256(raw).hexdigest(), bom, _detect_newline(text))


def _too_deep(data: Any) -> bool:
    """Whether `data` nests deeper than `MAX_DEPTH`, measured without recursion."""
    stack = [(data, 1)]
    while stack:
        node, depth = stack.pop()
        if depth > MAX_DEPTH:
            return True
        children = node.values() if isinstance(node, dict) else node if isinstance(node, list) else ()
        stack.extend((child, depth + 1) for child in children if isinstance(child, (dict, list)))
    return False


def _parse_data(text: str, fmt: str, shown: str) -> dict[str, Any]:
    try:
        data = _parse_text(text, fmt, shown)
        if fmt == "toml":
            data = plain_data(data)  # dates and times become text, so every later comparison and dump is plain JSON
    except RecursionError as exc:
        raise WriterRefusal(f"{shown} is nested too deeply to edit safely") from exc
    if not isinstance(data, dict):
        raise WriterRefusal(f"{shown} is not a {fmt.upper()} object")
    if _too_deep(data):
        raise WriterRefusal(f"{shown} is nested too deeply to edit safely")
    return data


def _parse_text(text: str, fmt: str, shown: str) -> Any:
    if fmt == "json":
        try:
            data = json.loads(text, object_pairs_hook=_reject_duplicates, parse_constant=_no_constant)
        except json.JSONDecodeError as exc:
            raise WriterRefusal(f"{shown} is not valid JSON (line {exc.lineno})") from exc
        except ValueError as exc:
            raise WriterRefusal(f"{shown} is not valid JSON ({exc})") from exc
    else:
        tomlkit = _import_tomlkit()
        try:
            parsed = tomlkit.parse(text)
        except tomlkit.exceptions.ParseError as exc:
            raise WriterRefusal(f"{shown} is not valid TOML (line {exc.line})") from exc
        data = parsed.unwrap()
    return data


# --------------------------------------------------------------------------
# JSON: surgical text editing
# --------------------------------------------------------------------------


@dataclass
class _Member:
    key: str
    lead_start: int  # index just after the "{" or "," that precedes this member
    kstart: int
    kend: int
    value: "_Node"


@dataclass
class _Node:
    kind: str  # "obj" | "arr" | "scalar"
    start: int
    end: int
    members: list[_Member]


class _Scanner:
    """Records the span of every object member in text that `json.loads` accepted."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.i = 0

    def ws(self) -> None:
        text, n = self.text, len(self.text)
        while self.i < n and text[self.i] in _WS:
            self.i += 1

    def string_end(self) -> int:
        text, i = self.text, self.i + 1
        while text[i] != '"':
            i += 2 if text[i] == "\\" else 1
        return i + 1

    def value(self, depth: int) -> _Node:
        if depth > MAX_DEPTH:
            raise WriterRefusal("the file is nested too deeply to edit safely")
        self.ws()
        text, start = self.text, self.i
        char = text[start]
        if char == "{":
            return self.obj(depth)
        if char == "[":
            self.i += 1
            self.ws()
            if text[self.i] == "]":
                self.i += 1
                return _Node("arr", start, self.i, [])
            while True:
                self.value(depth + 1)
                self.ws()
                if text[self.i] == ",":
                    self.i += 1
                    continue
                self.i += 1  # "]"
                return _Node("arr", start, self.i, [])
        if char == '"':
            self.i = self.string_end()
            return _Node("scalar", start, self.i, [])
        while self.i < len(text) and text[self.i] not in ",}] \t\n\r":
            self.i += 1
        return _Node("scalar", start, self.i, [])

    def obj(self, depth: int) -> _Node:
        text, start = self.text, self.i
        self.i += 1
        members: list[_Member] = []
        lead_start = self.i
        self.ws()
        if text[self.i] == "}":
            self.i += 1
            return _Node("obj", start, self.i, members)
        while True:
            self.ws()
            kstart = self.i
            kend = self.string_end()
            self.i = kend
            self.ws()
            self.i += 1  # ":"
            node = self.value(depth + 1)
            members.append(_Member(json.loads(text[kstart:kend]), lead_start, kstart, kend, node))
            self.ws()
            if text[self.i] == ",":
                self.i += 1
                lead_start = self.i
                continue
            self.i += 1  # "}"
            return _Node("obj", start, self.i, members)


def _scan(text: str) -> _Node:
    scanner = _Scanner(text)
    node = scanner.value(0)
    if node.kind != "obj":
        raise WriterRefusal("the file is not a JSON object")
    return node


def _member(node: _Node, key: str) -> _Member | None:
    found = [m for m in node.members if m.key == key]
    return found[-1] if found else None


@dataclass(frozen=True)
class _Style:
    unit: str
    newline: str
    multiline: bool


def _style(text: str, newline: str) -> _Style:
    match = re.search(r"\n([ \t]+)\S", text)
    return _Style(match.group(1) if match else "  ", newline, "\n" in text)


def _line_indent(text: str, index: int) -> str:
    start = text.rfind("\n", 0, index) + 1
    line = text[start:index]
    return line[: len(line) - len(line.lstrip(" \t"))]


def _dump(value: Any, base: str, style: _Style, multiline: bool, colon: str, inline_sep: str) -> str:
    if isinstance(value, dict) and value:
        pairs = [(json.dumps(k, ensure_ascii=False), v) for k, v in value.items()]
        if multiline:
            inner = base + style.unit
            body = ("," + style.newline).join(inner + k + colon + _dump(v, inner, style, True, colon, inline_sep) for k, v in pairs)
            return "{" + style.newline + body + style.newline + base + "}"
        return "{" + inline_sep.join(k + colon + _dump(v, base, style, False, colon, inline_sep) for k, v in pairs) + "}"
    if isinstance(value, list) and value:
        if multiline:
            inner = base + style.unit
            body = ("," + style.newline).join(inner + _dump(v, inner, style, True, colon, inline_sep) for v in value)
            return "[" + style.newline + body + style.newline + base + "]"
        return "[" + inline_sep.join(_dump(v, base, style, False, colon, inline_sep) for v in value) + "]"
    return json.dumps(value, ensure_ascii=False)


def _nest(path: tuple[str, ...], value: Any) -> Any:
    for part in reversed(path):
        value = {part: value}
    return value


HINT_KINDS = ("whole", "tail", "before")
MAX_HINT = 65536


def valid_hint(hint: Any) -> bool:
    return (
        isinstance(hint, dict) and hint.get("kind") in HINT_KINDS and isinstance(hint.get("text"), str)
        and 0 < len(hint["text"]) <= MAX_HINT and (hint["kind"] == "whole" or isinstance(hint.get("anchor"), str))
    )


def _json_restore(text: str, parent: _Node, key: str, hint: dict[str, Any]) -> str | None:
    """Put back the text a removal took out, when its neighbor is still in place; None otherwise."""
    members = parent.members
    if hint["kind"] == "whole":
        return text[: parent.start] + hint["text"] + text[parent.end :] if not members else None
    if hint["kind"] == "tail":
        if members and members[-1].key == hint["anchor"]:
            return text[: members[-1].value.end] + hint["text"] + text[members[-1].value.end :]
        return None
    anchor = _member(parent, hint["anchor"])
    if anchor is None or any(m.key == key for m in members):
        return None
    return text[: anchor.lead_start] + hint["text"] + text[anchor.lead_start :]


def _json_set(text: str, path: tuple[str, ...], value: Any, newline: str, hint: dict[str, Any] | None = None) -> str:
    root = _scan(text)
    style = _style(text, newline)
    node, depth = root, 0
    while True:
        member = _member(node, path[depth])
        if member is None:
            break
        if depth == len(path) - 1:
            inline = style.multiline and "\n" in text[member.value.start:member.value.end]
            base = _line_indent(text, member.kstart) if inline else ""
            rendered = _dump(value, base, style, style.multiline, ": ", ", ")
            return text[: member.value.start] + rendered + text[member.value.end :]
        if member.value.kind != "obj":
            raise WriterRefusal(f"{'.'.join(path[: depth + 1])} is not an object, so {path[depth + 1]} cannot be added under it")
        node, depth = member.value, depth + 1
    if hint is not None and depth == len(path) - 1:
        restored = _json_restore(text, node, path[depth], hint)
        if restored is not None:
            return restored
    nested = _nest(path[depth + 1 :], value)
    key = json.dumps(path[depth], ensure_ascii=False)
    if node.members:
        last = node.members[-1]
        lead = text[last.lead_start : last.kstart]
        colon = text[last.kend : last.value.start]
        colon = colon if colon.strip() == ":" and "\n" not in colon else ": "
        multiline = "\n" in lead
        base = lead[lead.rfind("\n") + 1 :] if multiline else ""
        inline_sep = ", " if lead.strip() == "" and lead else ","
        rendered = _dump(nested, base, style, multiline, colon, inline_sep or ",")
        return text[: last.value.end] + "," + lead + key + colon + rendered + text[last.value.end :]
    multiline = style.multiline
    base = _line_indent(text, node.start)
    rendered = _dump(nested, base + style.unit, style, multiline, ": ", ", ")
    if multiline:
        body = "{" + style.newline + base + style.unit + key + ": " + rendered + style.newline + base + "}"
    else:
        body = "{" + key + ": " + rendered + "}"
    return text[: node.start] + body + text[node.end :]


def _json_remove_member(text: str, path: tuple[str, ...]) -> tuple[str, bool, dict[str, Any] | None]:
    """Remove the member at `path`: (new text, whether it existed, the hint that undoes it exactly)."""
    root = _scan(text)
    node = root
    for depth, part in enumerate(path):
        member = _member(node, part)
        if member is None:
            return text, False, None
        if depth == len(path) - 1:
            break
        if member.value.kind != "obj":
            return text, False, None
        node = member.value
    members = node.members
    index = members.index(member)
    if len(members) == 1:
        hint = {"kind": "whole", "text": text[node.start : node.end]}
        return text[: node.start] + "{}" + text[node.end :], True, hint
    if index == len(members) - 1:
        before = members[index - 1]
        hint = {"kind": "tail", "text": text[before.value.end : member.value.end], "anchor": before.key}
        return text[: before.value.end] + text[member.value.end :], True, hint
    after = members[index + 1]
    hint = {"kind": "before", "text": text[member.lead_start : after.lead_start], "anchor": after.key}
    return text[: member.lead_start] + text[after.lead_start :], True, hint


def _json_remove(text: str, path: tuple[str, ...], created_depth: int) -> tuple[str, dict[str, Any] | None]:
    text, existed, hint = _json_remove_member(text, path)
    if not existed:
        return text, None
    for length in range(len(path) - 1, 0, -1):
        if length <= created_depth:
            break
        ancestor = _scan(text)
        for part in path[:length]:
            member = _member(ancestor, part)
            ancestor = member.value if member is not None else ancestor
        if ancestor.kind != "obj" or ancestor.members:
            break
        text, _, _ = _json_remove_member(text, path[:length])
    return text, hint


def _edit_json(loaded: Loaded, edits: list[Edit]) -> tuple[str, list[dict[str, Any] | None]]:
    """The new text and, per edit, the hint that would undo a removal exactly."""
    if not loaded.exists:
        data = _apply_to_data({}, edits)
        style = _Style("  ", "\n", True)
        return (_dump(data, "", style, True, ": ", ", ") + "\n" if data else "{}\n"), [None] * len(edits)
    text = loaded.text
    hints: list[dict[str, Any] | None] = []
    for edit in edits:
        hint = None
        if edit.value is ABSENT:
            depth = edit.created_depth if edit.created_depth is not None else len(edit.key_path)
            text, hint = _json_remove(text, edit.key_path, depth)
        else:
            text = _set_with_hint(text, edit, loaded.newline)
        hints.append(hint)
    return text, hints


def _set_with_hint(text: str, edit: Edit, newline: str) -> str:
    """Set a key, putting a removed member back verbatim when its hint still fits and checks out."""
    if valid_hint(edit.restore):
        try:
            hinted = _json_set(text, edit.key_path, edit.value, newline, edit.restore)
            if same(json.loads(hinted), _apply_to_data(json.loads(text), [edit])):
                return hinted
        except (ValueError, WriterRefusal):
            pass  # a hint that does not fit is dropped; the plain insertion below is always correct
    return _json_set(text, edit.key_path, edit.value, newline)


# --------------------------------------------------------------------------
# TOML: tomlkit
# --------------------------------------------------------------------------


def _table_like(node: Any) -> bool:
    return hasattr(node, "keys") and hasattr(node, "__getitem__")


def _toml_remove(doc: Any, path: tuple[str, ...], created_depth: int) -> None:
    parents: list[tuple[Any, str]] = []
    node = doc
    for part in path[:-1]:
        if not _table_like(node) or part not in node:
            return
        parents.append((node, part))
        node = node[part]
    if not _table_like(node) or path[-1] not in node:
        return
    del node[path[-1]]
    for index in range(len(parents) - 1, -1, -1):
        holder, name = parents[index]
        if index >= created_depth and _table_like(holder[name]) and not len(holder[name]):
            del holder[name]
        else:
            break


def _edit_toml(loaded: Loaded, edits: list[Edit]) -> str:
    tomlkit = _import_tomlkit()
    doc = tomlkit.parse(loaded.text)
    for edit in edits:
        if edit.value is ABSENT:
            depth = edit.created_depth if edit.created_depth is not None else len(edit.key_path)
            _toml_remove(doc, edit.key_path, depth)
            continue
        node = doc
        for part in edit.key_path[:-1]:
            if part not in node:
                node[part] = tomlkit.table()
            elif not _table_like(node[part]):
                raise WriterRefusal(f"{'.'.join(edit.key_path[:-1])} is not a table, so {edit.key_path[-1]} cannot be added under it")
            node = node[part]
        node[edit.key_path[-1]] = edit.value
    text = tomlkit.dumps(doc)
    if loaded.newline == "\r\n":
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    return text


# --------------------------------------------------------------------------
# Planning and committing
# --------------------------------------------------------------------------


def plan_edits(loaded: Loaded, edits: list[Edit], *, delete_when_empty: bool = False) -> Plan:
    """Compute the new file bytes and per-key changes without touching the disk."""
    if not edits:
        raise WriterRefusal("nothing to write")
    for edit in edits:
        check_segments(edit.key_path)
        _check_value(edit.value)
    try:
        text, hints = (_edit_toml(loaded, edits), [None] * len(edits)) if loaded.fmt == "toml" else _edit_json(loaded, edits)
    except WriterRefusal:
        raise
    except Exception as exc:  # an editing defect must refuse, never write
        raise WriterRefusal(f"{loaded.display} could not be edited safely ({type(exc).__name__}); it was left untouched") from exc
    changes = []
    for edit, hint in zip(edits, hints):
        present, previous = lookup(loaded.data, edit.key_path)
        removing = edit.value is ABSENT
        changes.append(
            Change(
                edit.key_path, present, previous if present else None, not removing,
                None if removing else edit.value, _created_depth(loaded.data, edit.key_path), hint if present else None,
            )
        )
    try:
        expected = _apply_to_data(loaded.data, edits)
        produced = _parse_data(text, loaded.fmt, loaded.display)
    except WriterRefusal as exc:
        raise WriterRefusal(f"the edit to {loaded.display} did not produce a valid file ({exc}); it was left untouched") from exc
    if not same(produced, expected):
        raise WriterRefusal(f"the edit to {loaded.display} failed its consistency check; it was left untouched")
    payload = (_BOM if loaded.bom else b"") + text.encode("utf-8")
    if loaded.exists and same(produced, loaded.data):
        payload = loaded.raw  # a no-op edit must not reformat the file
    created = not loaded.exists
    # A created JSON file that is now `{}` goes; a TOML file goes only when it holds nothing at all, because
    # comments are not data and a person's notes must survive the reset.
    emptied = not produced and (loaded.fmt == "json" or not text.strip())
    delete = delete_when_empty and loaded.exists and emptied and any(e.value is ABSENT for e in edits)
    return Plan(loaded, payload, tuple(changes), created, delete)


def _windows_acl(src: str, dst: str) -> bool | None:
    """Copy the DACL of `src` to `dst`. None: could not read it. True/False: copied or not."""
    import ctypes
    from ctypes import wintypes

    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    adv.GetFileSecurityW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    adv.GetSecurityDescriptorControl.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.WORD), ctypes.POINTER(wintypes.DWORD)]
    adv.GetSecurityDescriptorDacl.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.BOOL), ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.BOOL)]
    adv.SetNamedSecurityInfoW.argtypes = [wintypes.LPWSTR, ctypes.c_int, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    adv.SetNamedSecurityInfoW.restype = wintypes.DWORD
    dacl_info, protected_info = 0x4, 0x80000000
    needed = wintypes.DWORD(0)
    adv.GetFileSecurityW(src, dacl_info, None, 0, ctypes.byref(needed))
    if not needed.value:
        return None
    buffer = ctypes.create_string_buffer(needed.value)
    if not adv.GetFileSecurityW(src, dacl_info, buffer, needed, ctypes.byref(needed)):
        return None
    control, revision = wintypes.WORD(0), wintypes.DWORD(0)
    if not adv.GetSecurityDescriptorControl(buffer, ctypes.byref(control), ctypes.byref(revision)):
        return None
    protected = bool(control.value & 0x1000)  # SE_DACL_PROTECTED
    present, defaulted, dacl = wintypes.BOOL(0), wintypes.BOOL(0), ctypes.c_void_p()
    if not adv.GetSecurityDescriptorDacl(buffer, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)):
        return None
    info = dacl_info | (protected_info if protected else 0)
    code = adv.SetNamedSecurityInfoW(dst, 1, info, None, None, dacl if present.value else None, None)
    return code == 0 or (None if not protected else False)


def owner_only_windows(path: Path) -> bool:
    """Restrict `path` to its owner (a protected DACL naming OWNER RIGHTS). Best effort."""
    import ctypes
    from ctypes import wintypes

    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p]
    adv.GetSecurityDescriptorDacl.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.BOOL), ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.BOOL)]
    adv.SetNamedSecurityInfoW.argtypes = [wintypes.LPWSTR, ctypes.c_int, wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    adv.SetNamedSecurityInfoW.restype = wintypes.DWORD
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    descriptor = ctypes.c_void_p()
    if not adv.ConvertStringSecurityDescriptorToSecurityDescriptorW("D:P(A;;FA;;;OW)", 1, ctypes.byref(descriptor), None):
        return False
    try:
        present, defaulted, dacl = wintypes.BOOL(0), wintypes.BOOL(0), ctypes.c_void_p()
        if not adv.GetSecurityDescriptorDacl(descriptor, ctypes.byref(present), ctypes.byref(dacl), ctypes.byref(defaulted)):
            return False
        return adv.SetNamedSecurityInfoW(str(path), 1, 0x4 | 0x80000000, None, None, dacl, None) == 0
    finally:
        kernel.LocalFree(descriptor)


def _copy_permissions(src: Path, dst: Path, shown: str) -> None:
    try:
        os.chmod(dst, stat.S_IMODE(os.stat(src).st_mode))
    except OSError:
        pass
    if sys.platform != "win32":
        return
    try:
        copied = _windows_acl(str(src), str(dst))
    except Exception:  # ctypes problems must not lose a file; only a hardened ACL is worth refusing for
        copied = None
    if copied is False:
        raise WriterRefusal(f"the access list of {shown} could not be preserved, so it was left untouched")


def _write_temp(parent: Path, payload: bytes) -> Path:
    handle, name = tempfile.mkstemp(dir=parent, prefix=".nexus-settings-", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        _discard(Path(name))
        raise
    return Path(name)


def _discard(temp: Path) -> None:
    """Remove a temporary file even when it inherited a read-only attribute; never raises."""
    try:
        temp.unlink(missing_ok=True)
    except OSError:
        try:
            os.chmod(temp, stat.S_IWRITE | stat.S_IREAD)
            temp.unlink(missing_ok=True)
        except OSError:
            pass


# Windows can refuse a rename for a moment while another process (typically an
# antivirus or indexing scan of the just-written temp file) holds the file open:
# winerror 5 (access denied) or 32 (sharing violation). A bare write-then-replace
# loop with no Nexus-Hub code hit this 7 times in 1,500 on the maintainer's
# workstation, so a single attempt would fail roughly one settings write in 200.
_TRANSIENT_WINERRORS = (5, 32)
_REPLACE_DELAYS = (0.01, 0.02, 0.04, 0.08, 0.16)


def replace_file(source: Path, target: Path) -> None:
    """`os.replace`, retried briefly on Windows for transient scanner locks only."""
    for delay in (*_REPLACE_DELAYS, None):
        try:
            os.replace(source, target)
            return
        except PermissionError as exc:
            if delay is None or sys.platform != "win32" or getattr(exc, "winerror", None) not in _TRANSIENT_WINERRORS:
                raise
            time.sleep(delay)


def _current_sha(real: Path) -> str | None:
    try:
        return hashlib.sha256(real.read_bytes()).hexdigest() if real.is_file() else None
    except OSError:
        return None


def commit(plan: Plan) -> bool:
    """Write the plan atomically. Returns True when the disk changed."""
    loaded = plan.loaded
    if not plan.changed:
        return False
    real = loaded.real
    if _current_sha(real) != loaded.sha:
        raise WriterRefusal(f"{loaded.display} changed while Nexus-Hub was preparing the edit, so it was left untouched")
    if loaded.exists and not os.access(real, os.W_OK):
        raise WriterRefusal(f"{loaded.display} is read-only, so it was left untouched: make it writable, then run the command again")
    if plan.delete_file:
        try:
            real.unlink()
        except OSError as exc:
            raise WriterRefusal(f"{loaded.display} could not be removed ({exc.strerror or exc})") from exc
        return True
    try:
        real.parent.mkdir(parents=True, exist_ok=True)
        temp = _write_temp(real.parent, plan.new_bytes)
    except OSError as exc:
        raise WriterRefusal(f"{loaded.display} could not be written ({exc.strerror or exc})") from exc
    try:
        if loaded.exists:
            _copy_permissions(real, temp, loaded.display)
        if _current_sha(real) != loaded.sha:
            raise WriterRefusal(f"{loaded.display} changed while Nexus-Hub was writing, so it was left untouched")
        if loaded.exists:
            replace_file(temp, real)
        else:
            os.link(temp, real)  # fails if the file appeared meanwhile
    except FileExistsError as exc:
        raise WriterRefusal(f"{loaded.display} appeared while Nexus-Hub was writing, so it was left untouched") from exc
    except OSError as exc:
        raise WriterRefusal(f"{loaded.display} could not be written ({exc.strerror or exc})") from exc
    finally:
        _discard(temp)
    return True


# --------------------------------------------------------------------------
# Public one-call writers
# --------------------------------------------------------------------------


def write_json_keys(path: Path, edits: list[Edit], display: str | None = None) -> Plan:
    plan = plan_edits(load(path, "json", display), edits)
    commit(plan)
    return plan


def write_toml_keys(path: Path, edits: list[Edit], display: str | None = None) -> Plan:
    plan = plan_edits(load(path, "toml", display), edits)
    commit(plan)
    return plan


def write_json_key(path: Path, key_path: tuple[str, ...] | list[str], value: Any, display: str | None = None) -> Change:
    return write_json_keys(path, [Edit(tuple(key_path), value)], display).changes[0]


def write_toml_key(path: Path, key_path: tuple[str, ...] | list[str], value: Any, display: str | None = None) -> Change:
    return write_toml_keys(path, [Edit(tuple(key_path), value)], display).changes[0]
