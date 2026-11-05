"""Pure resolver: a catalog and a snapshot in, one honest state per control and tool out.

Every cell the catalog lists gets exactly one state (DoD 3). Anything the
resolver cannot verify goes in `caveats`, never in a second state. Behavior is
driven by the catalog: admission, override layers (their `detect` specs), proven
version ranges, and value maps. A change of admission changes the result with no
code change. Fix lines are catalog text only; values read from project files are
display data, truncated to 80 characters.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .catalog import (
    MODEL_ID_SEGMENT,
    USER_FILE_IDS,
    Group,
    load_claude_model_ids,
    write_groups,
)
from .effort import COMMON_CODEX_LEVELS, mapped
from .readers import FILE_INFO, Snapshot, printable, user_file_id

ECHO_LIMIT = 80
STATES = (
    "in-effect", "tool-default", "overridden-by", "not-settable",
    "not-covered", "unverified-for-version", "tool-not-installed", "cannot-detect",
)
_RANK_ENV = 1
_SCOPE_RANK = {"managed": 0, "project": 2, "user": 3}
_EDITOR_REASON = "read from the editor: the CLI cannot read VS Code settings, so the panel supplies them"


@dataclass(frozen=True)
class Hit:
    rank: int
    label: str
    fix: str
    value: str


@dataclass(frozen=True)
class Native:
    """The user's own value for one write: `found` plus the value, or per-model entries."""

    found: bool
    value: Any = None
    entries: dict[str, Any] | None = None
    missing: tuple[str, ...] = ()


def _walk(data: Any, path: list[str]) -> tuple[bool, Any]:
    node = data
    for part in path:
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _echo(value: Any) -> str:
    text = printable(value if isinstance(value, str) else json.dumps(value, ensure_ascii=True, separators=(",", ":")))
    return text if len(text) <= ECHO_LIMIT else text[: ECHO_LIMIT - 3] + "..."


def _user_native(write: dict[str, Any], snap: Snapshot, claude_ids: list[str]) -> Native:
    file_id = user_file_id(write)
    record = snap.files.get(file_id) if file_id else None
    data = record.data if record is not None and record.status == "ok" else None
    path = list(write["key_path"])
    if MODEL_ID_SEGMENT not in path:
        found, value = _walk(data, path) if data is not None else (False, None)
        return Native(found, value if found else None)
    at = path.index(MODEL_ID_SEGMENT)
    present_found, present = _walk(data, path[:at]) if data is not None else (False, None)
    known = list(dict.fromkeys([*claude_ids, *(present if present_found and isinstance(present, dict) else [])]))
    entries: dict[str, Any] = {}
    for model in known:
        found, value = _walk(data, path[:at] + [model] + path[at + 1 :]) if data is not None else (False, None)
        if found:
            entries[model] = value
    return Native(bool(entries), entries or None, entries, tuple(m for m in claude_ids if m not in entries))


def _control_values(write: dict[str, Any], native: Any) -> list[str]:
    return [control for control, mapped in write["value_map"].items() if type(mapped) is type(native) and mapped == native]


def _display(write: dict[str, Any], native: Native) -> str | None:
    if not native.found:
        return None
    if native.entries is not None:
        shown = sorted({"/".join(_control_values(write, v)) or _echo(v) for v in native.entries.values()})
        return shown[0] if len(shown) == 1 else "mixed (" + ", ".join(f"{m}={_echo(v)}" for m, v in native.entries.items()) + ")"
    return "/".join(_control_values(write, native.value)) or _echo(native.value)


def _env_source(record: Any) -> str:
    scope = FILE_INFO[record.file_id][0]
    return record.display.rsplit("/", 1)[-1] if scope == "user" else record.display


def _probe(write: dict[str, Any], layer: dict[str, Any], snap: Snapshot, user_value: Any) -> tuple[list[Hit], list[str], str | None]:
    """Detect one override layer: (hits, caveats, invalid-file detail)."""
    detect = layer["detect"]
    if "skip" in detect:
        return [], [], None
    if "caveat" in detect:
        return [], [detect["caveat"]], None
    hits: list[Hit] = []
    caveats: list[str] = []
    fix = layer["fix"]
    for file_id in dict.fromkeys([*detect.get("files", []), *detect.get("settings_env", [])]):
        record = snap.files[file_id]
        if record.status == "invalid":
            return [], [], record.detail
        if record.status == "skipped":
            caveats.append(f"{record.display} was not read ({record.detail}).")
    for name in detect.get("env", []):
        if snap.env.get(name):
            hits.append(Hit(_RANK_ENV, f"env {name} (shell)", fix, _echo(snap.env[name])))
        for file_id in detect.get("settings_env", []):
            record = snap.files[file_id]
            block = record.data.get("env") if record.status == "ok" else None
            if isinstance(block, dict) and block.get(name) not in (None, ""):
                if detect.get("matching_user_value_is_not_override") and file_id == "claude-user":
                    values = list(user_value.values()) if isinstance(user_value, dict) else [user_value]
                    if values and all(v == block[name] for v in values):
                        continue
                hits.append(Hit(_RANK_ENV, f"env {name} ({_env_source(record)} env block)", fix, _echo(block[name])))
    for file_id in detect.get("files", []):
        record = snap.files[file_id]
        if record.status != "ok":
            continue
        scope = FILE_INFO[file_id][0]
        for key_path in detect["key_paths"]:
            found, value = _walk(record.data, key_path)
            if not found or value in detect.get("ignored_values", []):
                continue
            if "when_value_in" in detect and user_value not in detect["when_value_in"]:
                continue
            if key_path == list(write["key_path"]) and value == user_value:
                continue  # the layer agrees with the user's value, so nothing is overridden
            hits.append(Hit(_SCOPE_RANK[scope], f"file {record.display} ({scope})", fix, _echo(value)))
    if not hits and detect.get("residual"):
        caveats.append(detect["residual"])
    return hits, caveats, None


def _probe_all(writes: list[dict[str, Any]], snap: Snapshot, claude_ids: list[str]) -> tuple[list[Hit], list[str], str | None]:
    hits: list[Hit] = []
    caveats: list[str] = []
    for write in writes:
        user_value = _user_native(write, snap, claude_ids).value
        for layer in write["override_layers"]:
            found, extra, invalid = _probe(write, layer, snap, user_value)
            if invalid:
                return [], [], invalid
            hits += found
            caveats += extra
    # A shared Claude default owns the supported env lever. Lower persistent
    # fallback values may differ (max maps to xhigh there) without being conflicts.
    desired = _requested_effort(snap)
    if desired and any(w["id"] == "claude.effort.existing_env" for w in writes):
        env_write = next(w for w in writes if w["id"] == "claude.effort.existing_env")
        expected = mapped(env_write, desired)
        user = snap.files.get("claude-user")
        found, actual = _walk(user.data, env_write["key_path"]) if user is not None and user.status == "ok" else (False, None)
        if found and actual == expected:
            hits = [h for h in hits if not (h.label.startswith("env CLAUDE_CODE_EFFORT_LEVEL") and h.value == expected)]
            # The settings env value replaces inherited shell effort in normal
            # sessions and outranks project effortLevel/modelSettings keys.
            hits = [h for h in hits if not h.label.endswith("(shell)") and not (h.rank == 2 and "env block" not in h.label)]
    return sorted(dict.fromkeys(hits), key=lambda h: h.rank), caveats, None


def _requested_effort(snap: Snapshot) -> str | None:
    preferences = snap.files.get("nexus-preferences")
    value = preferences.data.get("default_effort") if preferences is not None and preferences.status == "ok" else None
    return value if isinstance(value, str) else None


def _vtuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def _outside(version: str, proven: dict[str, str]) -> bool:
    have = _vtuple(version)
    for bound, below in (("min", True), ("max", False)):
        if bound in proven:
            want = _vtuple(proven[bound])
            width = max(len(have), len(want))
            a, b = have + (0,) * (width - len(have)), want + (0,) * (width - len(want))
            if (a < b) if below else (a > b):
                return True
    return False


def _present_notes(hits: list[Hit]) -> list[str]:
    return [f"Present: {h.label} = {h.value}. {h.fix}" for h in hits]


def _companion_notes(admitted: list[dict[str, Any]], natives: dict[str, Native], snap: Snapshot) -> list[str]:
    notes: list[str] = []
    primary = admitted[0]
    chosen = _control_values(primary, natives[primary["id"]].value) if natives[primary["id"]].found and natives[primary["id"]].entries is None else []
    if len(chosen) == 1:
        for write in admitted[1:]:
            expected = write["value_map"].get(chosen[0])
            actual = natives[write["id"]]
            if write.get("only_when_present") and not actual.found:
                continue
            key = ".".join(str(p) for p in write["key_path"])
            if expected is None and actual.found:
                notes.append(f"{key} is set to {_echo(actual.value)}, which Nexus-Hub does not write for {chosen[0]}.")
            elif expected is not None and (not actual.found or actual.value != expected):
                notes.append(f"{key} is {'not set' if not actual.found else _echo(actual.value)}; Nexus-Hub writes {_echo(expected)} for {chosen[0]}.")
    for write in admitted:
        record = snap.files.get(user_file_id(write) or "")
        for blocker in write.get("applies_only_without", []):
            if record is not None and record.status == "ok" and blocker in record.data:
                notes.append(f"{blocker} is set in {record.display}, so its sandbox_mode is ignored and Nexus-Hub writes no posture.")
    return notes


def _resolve_group(group: Group, snap: Snapshot, claude_ids: list[str]) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "control": group.control["id"], "tool": group.tool, "surface": group.surface, "state": "",
        "value": None, "native": None, "layer": None, "layer_value": None, "fix": None,
        "detail": None, "caveats": [], "writes": [w["id"] for w in group.writes], "removable_override": None,
    }
    caveats: list[str] = []
    admitted = [w for w in group.writes if w["admission"] == "admitted"]
    tool = snap.tools.get(group.tool)
    installed = tool.installed if tool is not None else True

    def done(state: str, detail: str | None = None) -> dict[str, Any]:
        rec.update(state=state, detail=detail, caveats=list(dict.fromkeys(caveats)))
        return rec

    if not admitted:
        hits, extra, invalid = _probe_all([w for w in group.writes if user_file_id(w)], snap, claude_ids)
        caveats += _present_notes(hits) + extra + ([invalid] if invalid else [])
        if not installed:
            caveats.append("The tool is not installed on this machine.")
        return done("not-settable", group.writes[0]["not_settable_reason"])
    if not installed:
        return done("tool-not-installed")
    if group.surface == "vscode-host":
        return done("cannot-detect", _EDITOR_REASON)

    natives = {w["id"]: _user_native(w, snap, claude_ids) for w in admitted}
    for write in admitted:
        record = snap.files[user_file_id(write)]
        if record.status == "invalid":
            return done("cannot-detect", record.detail)
    hits, extra, invalid = _probe_all(admitted, snap, claude_ids)
    if invalid:
        return done("cannot-detect", invalid)
    caveats += extra

    primary = admitted[0]
    requested = _requested_effort(snap) if group.control["id"] == "effort" else None
    if requested and group.tool == "claude":
        env_primary = next((w for w in admitted if w["id"] == "claude.effort.existing_env"), None)
        if env_primary:
            primary = env_primary
    native = natives[primary["id"]]
    rec.update(value=_display(primary, native), native=native.entries if native.entries is not None else native.value)
    if requested:
        expected = mapped(primary, requested, snap.codex_effort_levels if snap.codex_effort_levels is not None else COMMON_CODEX_LEVELS)
        matches = native.found and (all(v == expected for v in native.entries.values()) if native.entries is not None else native.value == expected)
        rec.update(matches_default=bool(matches and not hits), mapped_effort=expected if isinstance(expected, str) else None)
        if matches:
            rec["value"] = requested
    if not native.found and "default" in primary:
        rec.update(value="/".join(_control_values(primary, primary["default"])), native=primary["default"])
        return done("in-effect", "Using the Nexus-Hub default.")
    if "default" in primary and not _control_values(primary, native.value):
        return done("cannot-detect", "The guardrail setting must be a JSON boolean.")
    for write in admitted:
        ranged = write["proven_versions"]
        if "min" in ranged or "max" in ranged:
            if tool is not None and tool.version_error:
                caveats += _present_notes(hits)
                return done("cannot-detect", f"version: {tool.version_error}")
            if tool is not None and tool.version and _outside(tool.version, ranged):
                caveats += _present_notes(hits)
                return done("unverified-for-version", tool.version)
    if native.found and primary["value_map"] and not _control_values(primary, native.value) and native.entries is None:
        caveats.append(f"{'.'.join(str(p) for p in primary['key_path'])} holds {_echo(native.value)}, which is not a value Nexus-Hub writes.")
    if not requested:
        caveats += _companion_notes(admitted, natives, snap)
    if hits:
        winner = hits[0]
        caveats += [f"Also set: {h.label} = {h.value}." for h in hits[1:] if h.label != winner.label]
        rec.update(layer=winner.label, layer_value=winner.value, fix=winner.fix)
        return done("overridden-by")
    if native.entries is not None:  # per-model entries: every current model needs its own
        if not (native.found or any(natives[w["id"]].found for w in admitted[1:])):
            return done("tool-default")
        return done("not-covered", ", ".join(native.missing)) if native.missing else done("in-effect")
    return done("in-effect" if native.found else "tool-default")


def _removable_override(rec: dict[str, Any], catalog: dict[str, Any], snap: Snapshot) -> dict[str, Any] | None:
    """The catalog `removable_overrides` row whose key is present in the user's file, when `remove-override` applies.

    It applies only where the CLI accepts it: the cell has an admitted write on a readable, installed tool. The
    panel offers its "Remove this override" button from this field instead of guessing from the layer text.
    """
    if rec["state"] in ("not-settable", "tool-not-installed", "cannot-detect"):
        return None
    for row in catalog.get("removable_overrides", []):
        if row["control"] != rec["control"] or row["tool"] != rec["tool"]:
            continue
        record = snap.files.get(USER_FILE_IDS[row["file"]] or "")
        if record is None or record.status != "ok":
            continue
        found, value = _walk(record.data, list(row["key_path"]))
        if found and value not in (None, ""):
            return {"id": row["id"], "weakens_safety": row["weakens_safety"], "reason": row["reason"]}
    return None


def resolve(catalog: dict[str, Any], snapshot: Snapshot, claude_ids: list[str] | None = None) -> list[dict[str, Any]]:
    """One record per control, tool, and surface, in catalog order."""
    ids = load_claude_model_ids() if claude_ids is None else claude_ids
    records = [_resolve_group(group, snapshot, ids) for group in write_groups(catalog)]
    for rec in records:
        rec["removable_override"] = _removable_override(rec, catalog, snapshot)
    return records
