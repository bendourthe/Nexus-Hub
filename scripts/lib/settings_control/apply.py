"""Write side of the Nexus-Hub Settings engine: set, reset, remove-override, the ownership record.

Every write is planned from catalog rows, never from built-in guesses: a control's
writes, their value maps, admission, and weakening values all come from
`catalog.json`, so a catalog edit changes behavior with no code change. A write
whose catalog row is Not-Settable is reported as skipped with the catalog's reason.

The ownership record `~/.nexus-hub/settings-control.json` is the only record of
user choices. It holds, per tool, file, and key path (a segment array), the first
previous value and the value Nexus-Hub wrote. `reset` restores a key only while its
current value still equals what was written; otherwise it refuses, names both
values, and drops the entry as user-owned. Entries whose tool, file, and key path do
not match a catalog row exactly are ignored and reported, and no file path is ever
taken from the record.

Safety-weakening writes need a person: an interactive terminal (stdin and stdout
are both a TTY and the person types `yes`) or a one-time panel confirmation. The
same holds for every `remove-override` and for a `reset` that would put back a
weaker value than the one Nexus-Hub wrote. All of them are refused when an
agent-session marker named in the catalog is in the environment. There is no flag
that bypasses this.

The panel confirmation is a file holding only the SHA-256 of a nonce, plus the exact
action, control, value, and tool. The panel hands the nonce itself to the one process
it starts, through that process's environment, so reading the file yields nothing
usable. A same-user process that sets the environment itself can still forge a
confirmation, so the agent-marker refusal and the terminal test are the barriers that
matter, and an agent-call hook rule (DF-25) is the planned second layer.

Every read-modify-write of the record runs under an exclusive lock file
(`settings-control.lock`), so two commands at once never lose an entry.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import json
import os
import re
import shutil
import sys
import tempfile
import time
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from . import readers, resolve, writers
from .catalog import MODEL_ID_SEGMENT, USER_FILE_IDS, WEAKENING_NATIVE, joined_key, load_claude_model_ids, write_groups

SCHEMA_VERSION = 1
RECORD_NAME = "settings-control.json"
LOCK_NAME = "settings-control.lock"
LOCK_SECONDS = 30
TOKEN_NAME = "settings-panel-token.json"
TOKEN_SECONDS = 30
NONCE_ENV = "NEXUS_SETTINGS_PANEL_NONCE"
NONCE_MIN = 32
MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@\[\]-]{0,127}\Z")
MODEL_VALUE_LIMIT = 200
EXIT_OK, EXIT_PARTIAL, EXIT_USAGE, EXIT_REFUSED, EXIT_NOTHING = 0, 1, 2, 3, 4


class UsageError(Exception):
    """A bad control, value, or option. Exit 2."""


class RecordError(Exception):
    """The ownership record cannot be read or written. Exit 2."""


class Refusal(Exception):
    """A safety-weakening change without a person present. Exit 3."""


def _now_text() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_tty() -> bool:
    try:
        return bool(sys.stdin.isatty() and sys.stdout.isatty())
    except (AttributeError, ValueError, OSError):
        return False  # a test that cannot be performed means no person is present


def _ask(prompt: str) -> str:
    print(prompt, end="", file=sys.stderr, flush=True)
    return sys.stdin.readline()


@dataclass
class Context:
    """Everything one invocation needs. Tests replace the seams; the CLI passes none."""

    catalog: dict[str, Any]
    home: Path = field(default_factory=Path.home)
    env: Mapping[str, str] = field(default_factory=lambda: dict(os.environ))
    project: Path | None = None
    platform: str = field(default_factory=readers.platform_name)
    claude_ids: list[str] | None = None
    which: Callable[[str], str | None] | None = None
    version_runner: Callable[[list[str]], tuple[str | None, str | None]] = readers.run_version
    is_tty: Callable[[], bool] = _is_tty
    ask: Callable[[str], str] = _ask
    clock: Callable[[], float] = time.time
    say: Callable[[str], None] = lambda text: print(text, file=sys.stderr)

    def ids(self) -> list[str]:
        return load_claude_model_ids() if self.claude_ids is None else list(self.claude_ids)


# --------------------------------------------------------------------------
# Catalog lookups
# --------------------------------------------------------------------------


def _fmt(file: str) -> str:
    return "toml" if file.endswith(".toml") else "json"


def _user_path(ctx: Context, file: str) -> Path:
    file_id = USER_FILE_IDS[file]
    assert file_id is not None
    path = readers.file_path(file_id, ctx.home, ctx.env, ctx.project, ctx.platform)
    assert path is not None
    return path


def _display(ctx: Context, path: Path) -> str:
    return readers.display_path(path, ctx.home, ctx.project)


def _control(catalog: dict[str, Any], control_id: str) -> dict[str, Any]:
    for control in catalog["controls"]:
        if control["id"] == control_id:
            return control
    raise UsageError(f"unknown control {control_id!r}; known controls: " + ", ".join(c["id"] for c in catalog["controls"]))


def _check_tool(catalog: dict[str, Any], tool: str | None) -> None:
    known = set(catalog["tools"]) | {"internal"}
    if tool is not None and tool not in known:
        raise UsageError(f"unknown tool {tool!r}; known tools: " + ", ".join(sorted(known)))


def _printable_ascii(text: str) -> bool:
    return all(" " <= char <= "~" for char in text)


def validate_value(control: dict[str, Any], value: str) -> None:
    """Refuse a value the control does not accept, with the catalog's list in the message."""
    if value in control.get("never_written", []):
        raise UsageError(f"{value!r} is never written as a default for {control['id']}: no vendor documents it as a user-level setting")
    allowed = control["values"]
    if isinstance(allowed, list):
        if value not in allowed:
            raise UsageError(f"{value!r} is not a value for {control['id']}; use one of: " + ", ".join(allowed))
        return
    if not value or len(value) > MODEL_VALUE_LIMIT or not _printable_ascii(value) or value != value.strip() or value.startswith("-"):
        raise UsageError(
            f"{value!r} is not a usable {control['id']} value (1 to {MODEL_VALUE_LIMIT} printable ASCII characters, "
            "no space at either end, and not starting with a hyphen)"
        )


def _native_for(write: dict[str, Any], value: str) -> tuple[bool, Any, str]:
    """(mappable, native value, reason). A control value with no faithful mapping is Not-Settable."""
    if write["value_map"]:
        if value in write["value_map"]:
            return True, write["value_map"][value], ""
        return False, None, f"no faithful {write['tool']} setting for {value!r}"
    return True, value, ""


def _weakens(write: dict[str, Any], value: str, native: Any) -> bool:
    if write["weakens_safety"] and value in write["weakening_values"]:
        return True
    return isinstance(native, (str, bool)) and (write["tool"], joined_key(write), native) in WEAKENING_NATIVE


def _omitted_reason(catalog: dict[str, Any], write: dict[str, Any]) -> str | None:
    joined = joined_key(write)
    exceptions = catalog.get("omitted_user_choice_exceptions", {}).get(write["tool"], [])
    for name in catalog["omitted_keys"].get(write["tool"], []):
        if (joined == name or joined.startswith(name + ".")) and joined not in exceptions:
            return f"{joined} is an omitted key that Nexus-Hub never writes"
    return None


def check_write_allowed(catalog: dict[str, Any], write: dict[str, Any], native: Any) -> str | None:
    """Re-run the catalog's own rules for one concrete write at run time; a reason, or None."""
    joined = joined_key(write)
    omitted = _omitted_reason(catalog, write)
    if omitted:
        return omitted
    if write["tool"] == "codex" and write["key_path"] == ["approval_policy"] and native == "untrusted":
        return "untrusted is retired and never written"
    if write["key_path"][-1] == "effortLevel" and native == "max":
        return "max is never written as a default effort"
    if isinstance(write["values"], list) and not isinstance(native, dict) and native not in write["values"]:
        return f"{native!r} is not a value the catalog lists for {joined}"
    return None


def _leaves(key_path: tuple[str, ...], native: Any) -> list[tuple[tuple[str, ...], Any]]:
    """A dict value is written leaf by leaf so unrelated sub-keys the user holds survive."""
    if isinstance(native, dict) and native:
        return [leaf for key, child in native.items() for leaf in _leaves((*key_path, key), child)]
    return [(key_path, native)]


# --------------------------------------------------------------------------
# Ownership record
# --------------------------------------------------------------------------


def record_path(home: Path) -> Path:
    return home / ".nexus-hub" / RECORD_NAME


def _record_hint(home: Path) -> str:
    return f"repair or delete {record_path(home)} (it holds the previous values `reset` restores), then run the command again"


def load_record(home: Path) -> dict[str, Any]:
    """The record, or an empty one when it is absent. An unreadable record raises `RecordError`."""
    path = record_path(home)
    try:
        if not path.exists():
            return {"schema_version": SCHEMA_VERSION, "entries": []}
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise RecordError(f"the ownership record cannot be read ({exc}); {_record_hint(home)}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION or not isinstance(data.get("entries"), list):
        raise RecordError(f"the ownership record is not a version {SCHEMA_VERSION} record; {_record_hint(home)}")
    return data


def save_record(home: Path, record: dict[str, Any]) -> None:
    """Atomic, owner-only. Never called on a record that could not be read."""
    path = record_path(home)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle, name = tempfile.mkstemp(dir=path.parent, prefix=".settings-control-", suffix=".tmp")
        temp = Path(name)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write((json.dumps(record, indent=2, ensure_ascii=True) + "\n").encode("ascii"))
                stream.flush()
                os.fsync(stream.fileno())
            if sys.platform == "win32":
                writers.owner_only_windows(temp)
            else:
                os.chmod(temp, 0o600)
            writers.replace_file(temp, path)
        finally:
            temp.unlink(missing_ok=True)
    except OSError as exc:
        raise RecordError(f"the ownership record cannot be written ({exc.strerror or exc}); {_record_hint(home)}") from exc


def _try_lock(fd: int) -> bool:
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(fd: int) -> None:
    if os.name == "nt":
        import msvcrt

        os.lseek(fd, 0, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        fcntl.flock(fd, fcntl.LOCK_UN)


@contextmanager
def record_lock(home: Path, timeout: float | None = None) -> Iterator[None]:
    """Hold the exclusive cross-process lock that guards every change to the record and the files it describes.

    It is an operating system advisory lock on `settings-control.lock` (fcntl or msvcrt, the same
    pattern the installer uses), so a process that dies releases it. A command that cannot get the
    lock in `LOCK_SECONDS` stops with a message and has written nothing.
    """
    limit = LOCK_SECONDS if timeout is None else timeout
    path = record_path(home).with_name(LOCK_NAME)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o600)
    except OSError as exc:
        raise RecordError(f"the ownership record lock cannot be opened ({exc.strerror or exc}); {_record_hint(home)}") from exc
    deadline = time.monotonic() + limit
    try:
        while not _try_lock(fd):
            if time.monotonic() >= deadline:
                raise RecordError("another nexus-hub settings command is updating the record; wait for it to finish, then run this command again")
            time.sleep(0.05)
        try:
            yield
        finally:
            _unlock(fd)
    finally:
        os.close(fd)


@dataclass(frozen=True)
class Matched:
    kind: str  # "file" | "editor" | "override-removal"
    row: dict[str, Any]
    control: str
    tool: str
    file: str


def _entry_shape_ok(entry: Any) -> bool:
    def state(node: Any) -> bool:
        return isinstance(node, dict) and isinstance(node.get("present"), bool) and ("value" in node or not node["present"])

    return (
        isinstance(entry, dict) and isinstance(entry.get("tool"), str) and isinstance(entry.get("file"), str)
        and isinstance(entry.get("key_path"), list) and bool(entry["key_path"]) and all(isinstance(p, str) for p in entry["key_path"])
        and state(entry.get("previous")) and state(entry.get("new"))
    )


def _path_matches(row_path: list[str], entry_path: list[str]) -> bool:
    if len(row_path) != len(entry_path):
        return False
    return all(
        (MODEL_ID.match(got) is not None) if want == MODEL_ID_SEGMENT else want == got
        for want, got in zip(row_path, entry_path)
    )


def _leaf_allowed(write: dict[str, Any], tail: list[str]) -> bool:
    def inside(node: Any, path: list[str]) -> bool:
        if not path:
            return True
        return isinstance(node, dict) and path[0] in node and inside(node[path[0]], path[1:])

    return any(inside(v, tail) for v in write["value_map"].values() if isinstance(v, dict))


def _control_map(catalog: dict[str, Any]) -> dict[str, str]:
    return {wid: control["id"] for control in catalog["controls"] for wid in control["writes"]}


def match_entry(catalog: dict[str, Any], entry: Any, controls: dict[str, str] | None = None) -> Matched | None:
    """The admitted catalog row an entry belongs to, by exact tool, file, and key path; None otherwise.

    A row that is Not-Settable, or that names an omitted key, never matches: the record is a user file,
    and an entry for such a key can only be forged or left over from an older catalog.
    """
    if not _entry_shape_ok(entry):
        return None
    tool, file, path = entry["tool"], entry["file"], entry["key_path"]
    controls = _control_map(catalog) if controls is None else controls
    for write in catalog["writes"]:
        if write["tool"] != tool or write["file"] != file:
            continue
        if write["admission"] != "admitted" or _omitted_reason(catalog, write):
            continue
        base = write["key_path"]
        head, tail = path[: len(base)], path[len(base):]
        if len(path) < len(base) or not _path_matches(base, head):
            continue
        if tail and not _leaf_allowed(write, tail):
            continue
        kind = "editor" if file == "vscode-config" else "file"
        if entry.get("kind", kind) == kind:
            return Matched(kind, write, controls[write["id"]], tool, file)
    for row in catalog.get("removable_overrides", []):
        if row["tool"] == tool and row["file"] == file and row["key_path"] == path and entry.get("kind") == "override-removal":
            return Matched("override-removal", row, row["control"], tool, file)
    return None


def _split_record(ctx: Context, record: dict[str, Any]) -> tuple[list[tuple[dict[str, Any], Matched]], list[str]]:
    good: list[tuple[dict[str, Any], Matched]] = []
    ignored: list[str] = []
    controls = _control_map(ctx.catalog)
    for entry in record["entries"]:
        matched = match_entry(ctx.catalog, entry, controls)
        if matched is None:
            shown = ".".join(str(p) for p in entry["key_path"]) if isinstance(entry, dict) and isinstance(entry.get("key_path"), list) else "?"
            tool = entry.get("tool") if isinstance(entry, dict) else "?"
            ignored.append(f"ignored a record entry that matches no catalog write ({tool} {shown})")
        else:
            good.append((entry, matched))
    return good, ignored


def owned_keys(ctx: Context) -> dict[str, Any]:
    """Key paths of every valid record entry, grouped by catalog file, for the installers."""
    good, ignored = _split_record(ctx, load_record(ctx.home))
    files: dict[str, list[list[str]]] = {}
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for entry, matched in good:
        key = (matched.file, tuple(entry["key_path"]))
        if key not in seen:
            seen.add(key)
            files.setdefault(matched.file, []).append(list(entry["key_path"]))
    dotted = {file: [".".join(path) for path in paths] for file, paths in files.items()}  # for jq and PowerShell, which join no arrays
    return {"schema_version": SCHEMA_VERSION, "files": files, "dotted": dotted, "ignored": ignored}


def _find(entries: list[dict[str, Any]], tool: str, file: str, key_path: list[str]) -> dict[str, Any] | None:
    for entry in entries:
        if isinstance(entry, dict) and (entry.get("tool"), entry.get("file"), entry.get("key_path")) == (tool, file, key_path):
            return entry
    return None


def _state(present: bool, value: Any) -> dict[str, Any]:
    return {"present": True, "value": value} if present else {"present": False}


def _upsert(record: dict[str, Any], base: dict[str, Any], change: writers.Change, *, file_created: bool) -> None:
    """Add or update one entry, keeping the first previous value of a repeated set."""
    path = list(change.key_path)
    existing = _find(record["entries"], base["tool"], base["file"], path)
    now = _now_text()
    if existing is not None:
        existing["new"] = _state(change.new_present, change.new)
        existing["at"] = now
        return
    entry: dict[str, Any] = {
        "kind": base["kind"], "tool": base["tool"], "file": base["file"], "key_path": path,
        "previous": _state(change.previous_present, change.previous), "new": _state(change.new_present, change.new),
        "created_depth": change.created_depth, "file_created": file_created, "at": now,
    }
    if change.removal and not change.new_present:
        entry["restore_hint"] = change.removal  # the exact text taken out, so reset can put it back in place
    record["entries"].append(entry)


# --------------------------------------------------------------------------
# Human presence
# --------------------------------------------------------------------------


def agent_markers(catalog: dict[str, Any]) -> list[str]:
    """Every agent-session marker variable the catalog names, for any tool."""
    return sorted({name for info in catalog["tools"].values() for name in info.get("agent_session_markers", [])})


def _token_path(home: Path) -> Path:
    return home / ".nexus-hub" / TOKEN_NAME


def _nonce_matches(ctx: Context, digest: Any) -> bool:
    """True when the nonce this process was started with hashes to the digest in the token file."""
    nonce = ctx.env.get(NONCE_ENV, "")
    if not isinstance(digest, str) or len(digest) != 64 or len(nonce) < NONCE_MIN:
        return False
    return hmac.compare_digest(hashlib.sha256(nonce.encode("utf-8")).hexdigest().encode("ascii"), digest.lower().encode("ascii", "replace"))


def _consume_token(ctx: Context, action: str, control: str, value: str | None, tool: str | None) -> bool:
    """Read and delete the panel token; True only when it is fresh, names this exact change, and fits this process's nonce."""
    path = _token_path(ctx.home)
    if not path.exists():
        return False
    try:
        info = os.stat(path)
        text = path.read_text(encoding="utf-8")
        owner_ok = True
        if hasattr(os, "getuid"):
            owner_ok = info.st_uid == os.getuid() and (info.st_mode & 0o077) == 0
        path.unlink()  # consumed whether or not it is valid, so it can never be replayed
        token = json.loads(text)
    except (OSError, ValueError):
        return False
    if not owner_ok or not isinstance(token, dict):
        return False
    issued = token.get("issued_at")
    age = ctx.clock() - issued if isinstance(issued, (int, float)) and not isinstance(issued, bool) else None
    return (
        age is not None and -5 <= age <= TOKEN_SECONDS
        and token.get("action") == action and token.get("control") == control
        and token.get("value") == value and token.get("tool") == tool
        and _nonce_matches(ctx, token.get("token_sha256"))
    )


def _printout(ctx: Context, lines: list[str], tools: list[str]) -> None:
    ctx.say("This change lowers a safety barrier for NEW sessions. Nexus-Hub will write:")
    for line in lines:
        ctx.say(f"  {line}")
    for tool in tools:
        info = ctx.catalog["tools"].get(tool)
        if info:
            ctx.say(f"Still prompts or blocks ({info['label']}):")
            for item in info["cannot_remove"]:
                ctx.say(f"  - {item}")


def require_presence(
    ctx: Context, *, action: str, control: str, value: str | None, tool: str | None,
    lines: list[str], tools: list[str], weakens: bool,
) -> None:
    """Gate a write on a person. Raises `Refusal` (exit 3) with nothing written."""
    markers = [name for name in agent_markers(ctx.catalog) if ctx.env.get(name)]
    needs_person = weakens or action == "remove-override"
    if needs_person and markers:
        what = "A change that lowers a safety barrier" if weakens else "Removing a setting you did not choose"
        raise Refusal(
            f"refused: {', '.join(markers)} is set, so an agent session is running this command. "
            f"{what} must be run by a person in an interactive terminal or the Nexus-Hub Settings panel."
        )
    if _consume_token(ctx, action, control, value, tool):
        return
    if not needs_person:
        return
    if not ctx.is_tty():
        what = "lowers a safety barrier" if weakens else "removes a setting you did not choose"
        raise Refusal(
            f"refused: this change {what} and needs a person: run it in an interactive terminal "
            "(stdin and stdout must be a terminal) or confirm it in the Nexus-Hub Settings panel."
        )
    _printout(ctx, lines, tools)
    if ctx.ask("Type yes to continue: ").strip() != "yes":
        raise Refusal("refused: the confirmation was not 'yes', so nothing was written.")


# --------------------------------------------------------------------------
# set
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Target:
    write: dict[str, Any]
    tool: str
    file: str
    key_path: tuple[str, ...]
    native: Any
    weakens: bool


def _result(tool: str, write_id: str, file: str, key_path: Any, status: str, detail: str = "", **extra: Any) -> dict[str, Any]:
    return {"tool": tool, "write": write_id, "file": file, "key_path": list(key_path) if key_path else None, "status": status, "detail": detail, **extra}


def _expand_models(path: tuple[str, ...] | list[str], ids: list[str]) -> list[tuple[str, ...]]:
    at = list(path).index(MODEL_ID_SEGMENT)
    return [(*path[:at], model, *path[at + 1:]) for model in ids]


def _installed(ctx: Context, tool: str, cache: dict[str, bool]) -> bool:
    if tool == "internal":
        return True
    if tool not in cache:
        find = ctx.which or (lambda command: shutil.which(command, path=ctx.env.get("PATH")))
        info = ctx.catalog["tools"][tool]["detect"]
        dir_id = info.get("config_dir")
        has_dir = dir_id is not None and readers.dir_path(dir_id, ctx.home, ctx.env).is_dir()
        cache[tool] = bool(find(info["command"])) or has_dir
    return cache[tool]


def _plan_set(ctx: Context, control: dict[str, Any], value: str, tool: str | None) -> tuple[list[Target], list[dict[str, Any]], list[dict[str, Any]]]:
    """Targets to write, editor writes for the panel, and skipped cells with reasons."""
    targets: list[Target] = []
    editor: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    installed: dict[str, bool] = {}
    for group in (g for g in write_groups(ctx.catalog) if g.control["id"] == control["id"] and tool in (None, g.tool)):
        for write in group.writes:
            where = (group.tool, write["id"], write["file"], write["key_path"])
            if write["admission"] != "admitted":
                skipped.append(_result(*where[:3], where[3], "not-settable", write["not_settable_reason"]))
                continue
            if not _installed(ctx, group.tool, installed):
                skipped.append(_result(*where[:3], where[3], "tool-not-installed", f"{ctx.catalog['tools'][group.tool]['label']} is not installed on this machine"))
                continue
            mappable, native, reason = _native_for(write, value)
            if not mappable:
                skipped.append(_result(*where[:3], where[3], "not-settable", reason))
                continue
            refusal = check_write_allowed(ctx.catalog, write, native)
            if refusal:
                skipped.append(_result(*where[:3], where[3], "refused", refusal))
                continue
            weakens = _weakens(write, value, native)
            if write["surface"] == "vscode-host":
                editor.append(
                    {
                        "tool": group.tool, "write": write["id"], "key": joined_key(write), "key_path": list(write["key_path"]),
                        "value": native, "weakens_safety": weakens, "takes_effect": write["takes_effect"],
                    }
                )
                continue
            targets.append(Target(write, group.tool, write["file"], tuple(write["key_path"]), native, weakens))
    return targets, editor, skipped


def _expand_target(ctx: Context, target: Target, loaded: writers.Loaded) -> list[tuple[tuple[str, ...], Any]]:
    """Concrete (key path, value) pairs for a target: model ids and dict leaves expanded."""
    if MODEL_ID_SEGMENT in target.key_path:
        at = list(target.key_path).index(MODEL_ID_SEGMENT)
        present = writers.lookup(loaded.data, target.key_path[:at])[1]
        extra = list(present) if isinstance(present, dict) else []
        ids = [m for m in dict.fromkeys([*ctx.ids(), *extra]) if MODEL_ID.match(m)]
        paths = _expand_models(target.key_path, ids)
    else:
        paths = [target.key_path]
    return [leaf for path in paths for leaf in _leaves(path, target.native)]


def _commit_group(
    ctx: Context, loaded: writers.Loaded, plan: writers.Plan, bases: list[dict[str, Any]],
) -> None:
    """Record first, then write; a failed write puts the record back."""
    original = load_record(ctx.home)
    updated = copy.deepcopy(original)
    for base, change in zip(bases, plan.changes):
        _upsert(updated, base, change, file_created=plan.file_created)
    if updated != original:
        save_record(ctx.home, updated)
    try:
        writers.commit(plan)
    except writers.WriterRefusal:
        if updated != original:
            save_record(ctx.home, original)
        raise


def _apply_group(ctx: Context, file: str, group: list[Target], dry_run: bool) -> list[dict[str, Any]]:
    """Load one file, plan every edit for it, and commit; under the record lock when it writes."""
    results: list[dict[str, Any]] = []
    path = _user_path(ctx, file)
    shown = _display(ctx, path)
    tool = group[0].tool
    try:
        loaded = writers.load(path, _fmt(file), shown)
    except writers.WriterRefusal as exc:
        return [_result(t.tool, t.write["id"], shown, t.key_path, "refused", str(exc)) for t in group]
    edits: list[writers.Edit] = []
    bases: list[dict[str, Any]] = []
    owners: dict[tuple[str, ...], Target] = {}
    for target in group:
        blockers = [b for b in target.write.get("applies_only_without", []) if b in loaded.data]
        if blockers:
            results.append(_result(tool, target.write["id"], shown, target.key_path, "skipped", f"{shown} sets {blockers[0]}, which outranks this key, so no posture is written"))
            continue
        for key_path, native in _expand_target(ctx, target, loaded):
            edits.append(writers.Edit(key_path, native))
            bases.append({"kind": "file", "tool": tool, "file": file, "key_path": list(key_path)})
            owners[key_path] = target
    if not edits:
        return results
    try:
        plan = writers.plan_edits(loaded, edits)
        if not dry_run:
            _commit_group(ctx, loaded, plan, bases)
    except writers.WriterRefusal as exc:
        return results + [_result(tool, owners[e.key_path].write["id"], shown, e.key_path, "refused", str(exc)) for e in edits]
    for change in plan.changes:
        owner = owners[change.key_path]
        noop = change.previous_present and writers.same(change.previous, change.new)
        if dry_run:
            status = "would-keep" if noop else "would-write"
        else:
            status = "unchanged" if noop else "written"
        results.append(
            _result(
                tool, owner.write["id"], shown, change.key_path, status,
                previous=_state(change.previous_present, change.previous), new=_state(change.new_present, change.new),
                weakens_safety=owner.weakens, file_created=plan.file_created,
            )
        )
    return results


def _apply_targets(ctx: Context, targets: list[Target], value: str, dry_run: bool) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    by_file: dict[str, list[Target]] = {}
    for target in targets:
        by_file.setdefault(target.file, []).append(target)
    for file, group in by_file.items():
        # The lock spans the read of the file, the record update, and the write, so a second command
        # waits and then reads what the first one left instead of racing it.
        with nullcontext() if dry_run else record_lock(ctx.home):
            results += _apply_group(ctx, file, group, dry_run)
    return results


def _after(ctx: Context, control_id: str, tool: str | None) -> list[dict[str, Any]]:
    snapshot = readers.take_snapshot(
        ctx.catalog, home=ctx.home, env=ctx.env, project=ctx.project, platform=ctx.platform,
        which=ctx.which, version_runner=ctx.version_runner,
    )
    found = resolve.resolve(ctx.catalog, snapshot, ctx.ids())
    return [r for r in found if r["control"] == control_id and tool in (None, r["tool"])]


def _exit_code(results: list[dict[str, Any]], editor: list[dict[str, Any]]) -> int:
    statuses = {r["status"] for r in results}
    if statuses & {"refused", "failed"}:
        return EXIT_PARTIAL
    if statuses & {"written", "unchanged", "would-write", "would-keep"} or editor:
        return EXIT_OK
    return EXIT_NOTHING


def _target_lines(ctx: Context, targets: list[Target], editor: list[dict[str, Any]]) -> list[str]:
    lines = [f"{t.tool}: {t.file}  {'.'.join(t.key_path)} = {json.dumps(t.native)}" for t in targets]
    lines += [f"{e['tool']}: VS Code user settings  {e['key']} = {json.dumps(e['value'])}" for e in editor]
    return lines


def set_control(ctx: Context, control_id: str, value: str, tool: str | None = None, *, dry_run: bool = False) -> dict[str, Any]:
    """Write one control for every admitted tool (or one). Returns the result document."""
    control = _control(ctx.catalog, control_id)
    _check_tool(ctx.catalog, tool)
    if control.get("per_tool") and tool is None:
        raise UsageError(f"{control_id} is chosen per tool: add --tool ({', '.join(sorted({g.tool for g in write_groups(ctx.catalog) if g.control['id'] == control_id}))})")
    validate_value(control, value)
    targets, editor, skipped = _plan_set(ctx, control, value, tool)
    weakens = any(t.weakens for t in targets) or any(e["weakens_safety"] for e in editor)
    tools = sorted({t.tool for t in targets} | {e["tool"] for e in editor})
    confirmation = {"required": weakens, "kind": None}
    if weakens and not dry_run:
        require_presence(ctx, action="set", control=control_id, value=value, tool=tool, lines=_target_lines(ctx, targets, editor), tools=tools, weakens=True)
        confirmation["kind"] = "confirmed"
    results = _apply_targets(ctx, targets, value, dry_run) + skipped
    code = _exit_code(results, editor)
    after = [] if dry_run else _safe_after(ctx, control_id, tool)
    return {
        "schema_version": SCHEMA_VERSION, "action": "set", "control": control_id, "value": value, "tool": tool,
        "dry_run": dry_run, "confirmation": confirmation, "results": results, "editor_writes": editor,
        "after": after, "exit_code": code,
    }


def _safe_after(ctx: Context, control_id: str, tool: str | None) -> list[dict[str, Any]]:
    try:
        return _after(ctx, control_id, tool)
    except Exception as exc:  # the writes are done; a reporting failure must not hide them
        ctx.say(f"note: the resulting state could not be read ({type(exc).__name__})")
        return []


# --------------------------------------------------------------------------
# reset
# --------------------------------------------------------------------------


def _current(loaded: writers.Loaded, key_path: list[str]) -> dict[str, Any]:
    present, value = writers.lookup(loaded.data, key_path)
    return _state(present, value)


def _entry_matches_current(entry: dict[str, Any], current: dict[str, Any]) -> bool:
    new = entry["new"]
    return current["present"] == new["present"] and (not new["present"] or writers.same(current["value"], new["value"]))


def _describe(state: dict[str, Any]) -> str:
    return json.dumps(state["value"]) if state["present"] else "(not set)"


def _restores_weaker(entry: dict[str, Any]) -> bool:
    """True when putting back this entry's previous value would lower a safety barrier."""
    previous = entry["previous"]
    value = previous.get("value") if previous["present"] else None
    return isinstance(value, (str, bool)) and (entry["tool"], ".".join(entry["key_path"]), value) in WEAKENING_NATIVE


def _weak_restores(ctx: Context, record: dict[str, Any], control_id: str, tool: str | None) -> list[dict[str, Any]]:
    good, _ = _split_record(ctx, record)
    return [e for e, m in good if m.control == control_id and tool in (None, m.tool) and _restores_weaker(e)]


def reset_control(ctx: Context, control_id: str, tool: str | None = None, *, dry_run: bool = False) -> dict[str, Any]:
    """Restore every key Nexus-Hub wrote for a control, unless it changed since.

    A reset is a write like any other: putting back a weaker value than the one Nexus-Hub wrote (for
    example `bypassPermissions` that a person had before choosing Ask) needs a person, exactly as a
    `set` to that value would. A reset that restores a safe value or removes a key stays open to an agent.
    """
    _control(ctx.catalog, control_id)
    _check_tool(ctx.catalog, tool)
    weak = _weak_restores(ctx, load_record(ctx.home), control_id, tool)
    confirmation = {"required": bool(weak), "kind": None}
    if weak and not dry_run:
        lines = [f"{e['tool']}: {e['file']}  {'.'.join(e['key_path'])} = {json.dumps(e['previous']['value'])}  (restores what was there before)" for e in weak]
        require_presence(ctx, action="reset", control=control_id, value=None, tool=tool, lines=lines, tools=sorted({e["tool"] for e in weak}), weakens=True)
        confirmation["kind"] = "confirmed"
    with nullcontext() if dry_run else record_lock(ctx.home):
        record = load_record(ctx.home)
        if weak and not dry_run and any(e not in weak for e in _weak_restores(ctx, record, control_id, tool)):
            raise Refusal("refused: the record changed while you were confirming, so nothing was restored; run the command again.")
        doc = _reset_recorded(ctx, control_id, tool, record, dry_run)
    doc["confirmation"] = confirmation
    return doc


def _reset_recorded(ctx: Context, control_id: str, tool: str | None, record: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    good, ignored = _split_record(ctx, record)
    chosen = [(e, m) for e, m in good if m.control == control_id and tool in (None, m.tool)]
    results: list[dict[str, Any]] = []
    editor_restores: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    handovers: list[str] = []
    by_file: dict[str, list[tuple[dict[str, Any], Matched]]] = {}
    for entry, matched in chosen:
        if matched.kind == "editor":
            row = matched.row
            editor_restores.append(
                {"tool": matched.tool, "write": row["id"], "key": ".".join(entry["key_path"]), "key_path": entry["key_path"],
                 "restore": entry["previous"], "was": entry["new"], "profile": entry.get("profile")}
            )
            results.append(_result(matched.tool, row["id"], "vscode-config", entry["key_path"], "would-editor-restore" if dry_run else "editor-restore", "the panel restores this editor setting"))
            dropped.append(entry)
            continue
        by_file.setdefault(matched.file, []).append((entry, matched))
    for file, items in by_file.items():
        results += _reset_file(ctx, file, items, dropped, dry_run, handovers)
    if (dropped or handovers) and not dry_run:
        updated = copy.deepcopy(record)
        updated["entries"] = [e for e in updated["entries"] if not any(e == d for d in dropped)]
        for file in handovers:  # the file survived, so an entry that remains inherits "created it"
            heir = next((e for e in updated["entries"] if isinstance(e, dict) and e.get("file") == file), None)
            if heir is not None:
                heir["file_created"] = True
        save_record(ctx.home, updated)
    done = {r["status"] for r in results}
    code = EXIT_PARTIAL if done & {"refused", "failed"} else (EXIT_OK if results else EXIT_NOTHING)
    return {
        "schema_version": SCHEMA_VERSION, "action": "reset", "control": control_id, "tool": tool, "dry_run": dry_run, "results": results,
        "editor_restores": editor_restores, "ignored": ignored, "exit_code": code,
    }


def _reset_file(
    ctx: Context, file: str, items: list[tuple[dict[str, Any], Matched]], dropped: list[dict[str, Any]], dry_run: bool, handovers: list[str],
) -> list[dict[str, Any]]:
    path = _user_path(ctx, file)
    shown = _display(ctx, path)
    out: list[dict[str, Any]] = []
    try:
        loaded = writers.load(path, _fmt(file), shown)
    except writers.WriterRefusal as exc:
        return [_result(m.tool, m.row["id"], shown, e["key_path"], "refused", f"{exc}; the record entry is kept") for e, m in items]
    edits: list[writers.Edit] = []
    restoring: list[tuple[dict[str, Any], Matched]] = []
    for entry, matched in items:
        current = _current(loaded, entry["key_path"])
        if not _entry_matches_current(entry, current):
            out.append(
                _result(
                    matched.tool, matched.row["id"], shown, entry["key_path"], "drifted",
                    f"changed since Nexus-Hub wrote it: it was {_describe(entry['new'])} and is now {_describe(current)}; "
                    "left as you have it and no longer tracked",
                )
            )
            dropped.append(entry)
            continue
        previous = entry["previous"]
        if previous["present"]:
            edits.append(writers.Edit(tuple(entry["key_path"]), previous["value"], restore=entry.get("restore_hint")))
        else:
            edits.append(writers.Edit(tuple(entry["key_path"]), writers.ABSENT, created_depth=int(entry.get("created_depth", len(entry["key_path"])))))
        restoring.append((entry, matched))
    if not edits:
        return out
    created = any(e.get("file_created") for e, _ in restoring)
    try:
        plan = writers.plan_edits(loaded, edits, delete_when_empty=created)
        if not dry_run:
            writers.commit(plan)
    except writers.WriterRefusal as exc:
        return out + [_result(m.tool, m.row["id"], shown, e["key_path"], "refused", f"{exc}; the record entry is kept") for e, m in restoring]
    for entry, matched in restoring:
        out.append(_result(matched.tool, matched.row["id"], shown, entry["key_path"], "would-restore" if dry_run else "restored", previous=entry["previous"], new=entry["new"]))
        dropped.append(entry)
    if created and not plan.delete_file and not dry_run:
        handovers.append(file)
    return out


# --------------------------------------------------------------------------
# remove-override
# --------------------------------------------------------------------------


def _removable(ctx: Context, control_id: str, tool: str) -> list[dict[str, Any]]:
    rows = [r for r in ctx.catalog.get("removable_overrides", []) if r["control"] == control_id and r["tool"] == tool]
    if not rows:
        raise UsageError(f"{control_id} has no removable override for {tool}")
    return rows


def remove_override(ctx: Context, control_id: str, tool: str, *, dry_run: bool = False) -> dict[str, Any]:
    """Remove a catalog-listed override key after a person confirms, and record it so `reset` restores it."""
    _control(ctx.catalog, control_id)
    _check_tool(ctx.catalog, tool)
    rows = _removable(ctx, control_id, tool)
    admitted = [
        w for g in write_groups(ctx.catalog) if g.control["id"] == control_id and g.tool == tool
        for w in g.writes if w["admission"] == "admitted"
    ]
    results: list[dict[str, Any]] = []
    if not admitted:
        reasons = sorted({w["not_settable_reason"] for g in write_groups(ctx.catalog) if g.control["id"] == control_id and g.tool == tool for w in g.writes if w["admission"] != "admitted"})
        detail = f"{control_id} is not settable for {tool} yet, so removing its override would serve no admitted control: " + (reasons[0] if reasons else "no catalog write")
        results = [_result(tool, r["id"], r["file"], r["key_path"], "not-settable", detail) for r in rows]
        return _override_doc(control_id, tool, dry_run, results, {"required": False, "kind": None}, [])
    present: list[tuple[dict[str, Any], writers.Loaded, str]] = []
    for row in rows:
        path = _user_path(ctx, row["file"])
        shown = _display(ctx, path)
        try:
            loaded = writers.load(path, _fmt(row["file"]), shown)
        except writers.WriterRefusal as exc:
            results.append(_result(tool, row["id"], shown, row["key_path"], "refused", str(exc)))
            continue
        if writers.lookup(loaded.data, row["key_path"])[0]:
            present.append((row, loaded, shown))
        else:
            results.append(_result(tool, row["id"], shown, row["key_path"], "absent", "the key is not set, so there is nothing to remove"))
    weakens = any(row["weakens_safety"] for row, _, _ in present)
    confirmation = {"required": bool(present), "kind": None}
    if present and not dry_run:
        lines = [f"{tool}: {shown}  remove {'.'.join(row['key_path'])}" for row, _, shown in present]
        require_presence(ctx, action="remove-override", control=control_id, value=None, tool=tool, lines=lines, tools=[tool], weakens=weakens)
        confirmation["kind"] = "confirmed"
    for row, loaded, shown in present:
        edit = writers.Edit(tuple(row["key_path"]), writers.ABSENT)
        try:
            with nullcontext() if dry_run else record_lock(ctx.home):
                if not dry_run:  # read again under the lock: another command may have changed the file while a person confirmed
                    loaded = writers.load(_user_path(ctx, row["file"]), _fmt(row["file"]), shown)
                plan = writers.plan_edits(loaded, [edit])
                if not dry_run:
                    base = {"kind": "override-removal", "tool": tool, "file": row["file"], "key_path": list(row["key_path"])}
                    _commit_group(ctx, loaded, plan, [base])
        except writers.WriterRefusal as exc:
            results.append(_result(tool, row["id"], shown, row["key_path"], "refused", str(exc)))
            continue
        change = plan.changes[0]
        results.append(
            _result(tool, row["id"], shown, row["key_path"], "would-remove" if dry_run else "removed",
                    previous=_state(change.previous_present, change.previous), weakens_safety=row["weakens_safety"])
        )
    return _override_doc(control_id, tool, dry_run, results, confirmation, [] if dry_run else _safe_after(ctx, control_id, tool))


def _override_doc(control_id: str, tool: str, dry_run: bool, results: list[dict[str, Any]], confirmation: dict[str, Any], after: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = {r["status"] for r in results}
    if statuses & {"refused", "failed"}:
        code = EXIT_PARTIAL
    elif statuses & {"removed", "would-remove", "absent"}:
        code = EXIT_OK
    else:
        code = EXIT_NOTHING
    return {
        "schema_version": SCHEMA_VERSION, "action": "remove-override", "control": control_id, "tool": tool, "dry_run": dry_run,
        "confirmation": confirmation, "results": results, "editor_writes": [], "after": after, "exit_code": code,
    }


# --------------------------------------------------------------------------
# record-editor-write
# --------------------------------------------------------------------------


def record_editor_write(ctx: Context, payload: str) -> dict[str, Any]:
    """Record a VS Code setting the panel just wrote, so `reset` can return its restore."""
    if len(payload) > 4096:
        raise UsageError("record-editor-write payload is too large")
    try:
        data = json.loads(payload)
    except ValueError as exc:
        raise UsageError(f"record-editor-write needs a JSON object ({exc})") from exc
    if not isinstance(data, dict) or not isinstance(data.get("write"), str) or not isinstance(data.get("previous"), dict):
        raise UsageError('record-editor-write needs {"write": <catalog write id>, "previous": {"present": bool, "value": ...}, "new": ...}')
    write = next((w for w in ctx.catalog["writes"] if w["id"] == data["write"] and w["surface"] == "vscode-host"), None)
    if write is None:
        raise UsageError(f"{data['write']!r} is not a VS Code write in the catalog")
    if write["admission"] != "admitted":
        raise UsageError(f"{write['id']} is not settable: {write['not_settable_reason']}")
    previous = data["previous"]
    if not isinstance(previous.get("present"), bool) or (previous["present"] and "value" not in previous):
        raise UsageError('"previous" must be {"present": false} or {"present": true, "value": ...}')
    if "new" not in data:
        raise UsageError('record-editor-write needs a "new" value')
    key_path = tuple(write["key_path"])
    change = writers.Change(key_path, previous["present"], previous.get("value"), True, data["new"], len(key_path))
    with record_lock(ctx.home):
        record = load_record(ctx.home)
        _upsert(record, {"kind": "editor", "tool": write["tool"], "file": write["file"]}, change, file_created=False)
        profile = data.get("profile")
        if isinstance(profile, str) and profile and _printable_ascii(profile) and len(profile) <= 100:
            _find(record["entries"], write["tool"], write["file"], list(key_path))["profile"] = profile  # type: ignore[index]
        save_record(ctx.home, record)
    return {"schema_version": SCHEMA_VERSION, "action": "record-editor-write", "write": write["id"], "recorded": True, "exit_code": EXIT_OK}


# --------------------------------------------------------------------------
# Plain-text rendering
# --------------------------------------------------------------------------


def _shorten(state: Any) -> str:
    if not isinstance(state, dict):
        return ""
    return json.dumps(state["value"]) if state.get("present") else "(not set)"


def render_text(doc: dict[str, Any]) -> str:
    """ASCII text for a set, reset, or remove-override result."""
    lines: list[str] = []
    for r in doc["results"]:
        key = ".".join(r["key_path"]) if r["key_path"] else "-"
        head = f"{r['tool']:<12} {r['status']:<13} {r['file']}  {key}"
        if r.get("new") is not None and r.get("previous") is not None:
            head += f"  {_shorten(r['previous'])} -> {_shorten(r['new'])}"
        elif r.get("previous") is not None:
            head += f"  was {_shorten(r['previous'])}"
        lines.append(head)
        if r["detail"]:
            lines.append(f"    {r['detail']}")
    for e in doc.get("editor_writes", []):
        lines.append(f"{e['tool']:<12} set in VS Code  {e['key']} = {json.dumps(e['value'])}")
    for e in doc.get("editor_restores", []):
        lines.append(f"{e['tool']:<12} restore in VS Code  {e['key']} -> {_shorten(e['restore'])}")
    for note in doc.get("ignored", []):
        lines.append(f"note: {note}")
    if doc.get("after"):
        from .report import render_table

        lines += ["", "Now (every control is a default for NEW sessions only):", render_table({"records": doc["after"]})]
    return "\n".join(lines)
