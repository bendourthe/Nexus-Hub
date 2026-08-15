"""Project-local autonomy state engine for Nexus-Hub.

This module is the single implementation of autonomy enablement, status,
disablement, manual reversion, and TTL expiry. It reads only verified capability
descriptors from the integration registry and refuses every descriptor that is
not project-scoped. The state and append-only audit log live under the current
project's ``.nexus-hub/`` directory and are intended to be gitignored.

Only the Python standard library is used. No environment values, credentials,
config contents, or tier payloads are ever copied into the audit log.
"""

from __future__ import annotations

import argparse
import difflib
import getpass
import json
import os
import re
import subprocess
import sys
import time
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import tomllib

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

from scripts.lib.integrations import get as get_integration

STATE_VERSION = 1
STATE_RELATIVE_PATH = Path(".nexus-hub") / "autonomy-state.json"
AUDIT_RELATIVE_PATH = Path(".nexus-hub") / "autonomy-audit.jsonl"
DEFAULT_TTL_MINUTES = 60
MAX_TTL_MINUTES = 8 * 60
BASE_PROTECTED_BRANCHES = frozenset({"main", "master"})


@dataclass(frozen=True)
class OperationResult:
    """Serializable outcome returned by every mutating operation."""

    operation: str
    platform: str
    outcome: str
    message: str
    changed: bool = False
    gate: str | None = None
    config_path: str | None = None
    backup_path: str | None = None
    expiry: str | None = None
    diff: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime | None) -> datetime:
    current = value or _utc_now()
    if current.tzinfo is None:
        return current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _run_git(directory: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(directory), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _candidate_directory(project_dir: str | os.PathLike[str] | None) -> Path:
    candidate = Path(project_dir) if project_dir is not None else Path.cwd()
    candidate = candidate.expanduser().resolve()
    return candidate.parent if candidate.is_file() else candidate


def _git_root(project_dir: str | os.PathLike[str] | None) -> Path | None:
    candidate = _candidate_directory(project_dir)
    result = _run_git(candidate, "rev-parse", "--show-toplevel")
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip()).resolve()


def _git_value(root: Path, *args: str) -> str | None:
    result = _run_git(root, *args)
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _branch_and_head(root: Path) -> tuple[str | None, str | None]:
    return (
        _git_value(root, "branch", "--show-current"),
        _git_value(root, "rev-parse", "HEAD"),
    )


def _protected_branches(root: Path) -> set[str]:
    """Return conservative defaults plus explicit project declarations."""
    protected = set(BASE_PROTECTED_BRANCHES)
    declared = os.environ.get("NEXUS_PROTECTED_BRANCHES", "")
    protected.update(part for part in re.split(r"[\s,]+", declared) if part)

    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        try:
            for line in agents_path.read_text(encoding="utf-8").splitlines():
                lowered = line.lower()
                if "protected" not in lowered and "never commit" not in lowered:
                    continue
                for token in re.findall(r"`([A-Za-z0-9._/-]+)`", line):
                    if token not in {"git", "commit"} and not token.startswith(
                        ("feat/", "fix/")
                    ):
                        protected.add(token)
        except OSError:
            pass
    return protected


def _worktree_is_clean(root: Path) -> bool:
    result = _run_git(
        root,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        ".",
        ":(exclude).nexus-hub/autonomy-state.json",
        ":(exclude).nexus-hub/autonomy-audit.jsonl",
        ":(exclude).nexus-hub/autonomy-audit.jsonl.lock",
    )
    return result.returncode == 0 and not result.stdout.strip()


def _state_path(root: Path) -> Path:
    return root / STATE_RELATIVE_PATH


def _audit_path(root: Path) -> Path:
    return root / AUDIT_RELATIVE_PATH


def _load_state(root: Path) -> dict[str, Any]:
    path = _state_path(root)
    if not path.exists():
        return {"version": STATE_VERSION, "platforms": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("version") != STATE_VERSION:
        raise ValueError(f"Unsupported autonomy state at {path}")
    platforms = payload.get("platforms")
    if not isinstance(platforms, dict):
        raise TypeError(
            f"Invalid autonomy state at {path}: platforms must be an object"
        )
    return payload


def _atomic_replace(temp_path: Path, target_path: Path) -> None:
    os.replace(temp_path, target_path)


def _atomic_write_bytes(path: Path, content: bytes, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp.{os.getpid()}.{uuid.uuid4().hex}")
    try:
        descriptor = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _atomic_replace(temp_path, path)
        if os.name != "nt":
            os.chmod(path, mode)
    finally:
        temp_path.unlink(missing_ok=True)


def _write_state(root: Path, state: Mapping[str, Any]) -> None:
    path = _state_path(root)
    platforms = state.get("platforms", {})
    if not platforms:
        path.unlink(missing_ok=True)
        return
    body = json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    _atomic_write_bytes(path, body.encode("utf-8"))


def _acquire_lock(lock_path: Path, timeout_seconds: float = 5.0) -> int:
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            return os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"Timed out waiting for audit lock {lock_path}")
            time.sleep(0.01)


def _append_audit(root: Path, record: Mapping[str, Any]) -> None:
    audit_path = _audit_path(root)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = audit_path.with_name(audit_path.name + ".lock")
    lock_descriptor = _acquire_lock(lock_path)
    os.close(lock_descriptor)
    try:
        line = (
            json.dumps(dict(record), sort_keys=True, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        descriptor = os.open(audit_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(descriptor, line)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if os.name != "nt":
            os.chmod(audit_path, 0o600)
    finally:
        lock_path.unlink(missing_ok=True)


def _audit_record(
    root: Path,
    *,
    operation: str,
    platform: str,
    tier: str | None,
    outcome: str,
    config_path: Path | str | None = None,
    backup_path: Path | str | None = None,
    expiry: str | None = None,
    gate: str | None = None,
    now: datetime | None = None,
) -> None:
    branch, head = _branch_and_head(root)
    _append_audit(
        root,
        {
            "timestamp": _iso(now or _utc_now()),
            "operation": operation,
            "platform": platform,
            "tier": tier,
            "config_path": str(config_path) if config_path is not None else None,
            "backup_path": str(backup_path) if backup_path is not None else None,
            "expiry": expiry,
            "git_branch": branch,
            "git_head": head,
            "outcome": outcome,
            "gate": gate,
        },
    )


def _result_with_audit(
    root: Path,
    result: OperationResult,
    *,
    tier: str | None,
    now: datetime | None = None,
) -> OperationResult:
    _audit_record(
        root,
        operation=result.operation,
        platform=result.platform,
        tier=tier,
        outcome=result.outcome,
        config_path=result.config_path,
        backup_path=result.backup_path,
        expiry=result.expiry,
        gate=result.gate,
        now=now,
    )
    return result


def _reject(
    root: Path,
    platform: str,
    tier: str | None,
    gate: str,
    message: str,
    *,
    config_path: Path | str | None = None,
    now: datetime | None = None,
    outcome: str = "rejected",
) -> OperationResult:
    result = OperationResult(
        operation="enable",
        platform=platform,
        outcome=outcome,
        gate=gate,
        message=message,
        config_path=str(config_path) if config_path is not None else None,
    )
    return _result_with_audit(root, result, tier=tier, now=now)


def _descriptor(platform: str) -> dict[str, Any] | None:
    try:
        return get_integration(platform).autonomy_descriptor
    except KeyError:
        return None


def _resolve_project_config(root: Path, descriptor: Mapping[str, Any]) -> Path:
    if descriptor.get("scope") != "project":
        raise ValueError("descriptor is not project-scoped")
    raw_path = descriptor.get("config_file")
    if (
        not isinstance(raw_path, str)
        or not raw_path
        or raw_path.startswith(("~", "/", "\\"))
    ):
        raise ValueError("descriptor config path is not project-relative")
    if len(raw_path) > 1 and raw_path[1] == ":":
        raise ValueError("descriptor config path is absolute")
    target = (root / raw_path).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("descriptor config path escapes the project") from exc
    return target


def _strip_jsonc_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            output.extend((" ", " "))
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                output.append(" ")
                index += 1
            continue
        if char == "/" and next_char == "*":
            output.extend((" ", " "))
            index += 2
            while index < len(text):
                if (
                    text[index] == "*"
                    and index + 1 < len(text)
                    and text[index + 1] == "/"
                ):
                    output.extend((" ", " "))
                    index += 2
                    break
                output.append("\n" if text[index] == "\n" else " ")
                index += 1
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _set_dotted_path(document: dict[str, Any], dotted: str, value: Any) -> None:
    node = document
    parts = dotted.split(".")
    for part in parts[:-1]:
        existing = node.get(part)
        if not isinstance(existing, dict):
            existing = {}
            node[part] = existing
        node = existing
    node[parts[-1]] = value


def _render_json(
    original: str, updates: Mapping[str, Any], *, literal_keys: bool
) -> str:
    source = _strip_jsonc_comments(original) if original.strip() else "{}"
    document = json.loads(source)
    if not isinstance(document, dict):
        raise TypeError("config must contain a JSON object")
    for key, value in updates.items():
        if literal_keys:
            document[key] = value
        else:
            _set_dotted_path(document, key, value)
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _toml_scalar(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    raise ValueError(f"Unsupported TOML autonomy value type: {type(value).__name__}")


def _render_toml(original: str, updates: Mapping[str, Any]) -> str:
    if original.strip():
        tomllib.loads(original)
    remaining = dict(updates)
    lines = original.splitlines()
    rendered: list[str] = []
    in_table = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("["):
            in_table = True
        if not in_table:
            match = re.match(r"^(\s*)([A-Za-z0-9_-]+)\s*=", line)
            if match and match.group(2) in remaining:
                key = match.group(2)
                rendered.append(
                    f"{match.group(1)}{key} = {_toml_scalar(remaining.pop(key))}"
                )
                continue
        rendered.append(line)
    additions = [f"{key} = {_toml_scalar(value)}" for key, value in remaining.items()]
    if additions:
        insertion = next(
            (i for i, line in enumerate(rendered) if line.lstrip().startswith("[")),
            len(rendered),
        )
        prefix = rendered[:insertion]
        suffix = rendered[insertion:]
        if prefix and prefix[-1].strip():
            prefix.append("")
        rendered = prefix + additions
        if suffix:
            rendered.append("")
            rendered.extend(suffix)
    body = "\n".join(rendered).rstrip("\n") + "\n"
    tomllib.loads(body)
    return body


def _render_config(
    original: str, descriptor: Mapping[str, Any], updates: Mapping[str, Any]
) -> str:
    config_format = descriptor.get("format")
    if config_format == "json":
        return _render_json(original, updates, literal_keys=False)
    if config_format == "jsonc":
        return _render_json(original, updates, literal_keys=True)
    if config_format == "toml":
        return _render_toml(original, updates)
    raise ValueError(f"Unsupported autonomy config format: {config_format!r}")


def _unified_diff(config_path: Path, original: str, updated: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=str(config_path),
            tofile=str(config_path),
        )
    )


def _backup_path(config_path: Path, now: datetime) -> Path:
    stamp = _as_utc(now).strftime("%Y%m%d-%H%M%S")
    candidate = config_path.with_name(f"{config_path.name}.bak.{stamp}")
    suffix = 1
    while candidate.exists():
        candidate = config_path.with_name(f"{config_path.name}.bak.{stamp}.{suffix}")
        suffix += 1
    return candidate


def _write_backup(config_path: Path, backup_path: Path, original: bytes) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(backup_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(original)
        handle.flush()
        os.fsync(handle.fileno())


def _restore_original(
    config_path: Path, backup_path: Path, original_exists: bool
) -> None:
    if original_exists:
        _atomic_write_bytes(config_path, backup_path.read_bytes())
    else:
        config_path.unlink(missing_ok=True)


def enable(
    platform: str,
    tier: str,
    ttl: int | None,
    *,
    confirmation: str | None = None,
    project_dir: str | os.PathLike[str] | None = None,
    now: datetime | None = None,
    user: str | None = None,
    process: str | None = None,
) -> OperationResult:
    """Enable one verified project-scoped autonomy tier behind all hard gates."""
    timestamp = _as_utc(now)
    attempt_root = _candidate_directory(project_dir)
    descriptor = _descriptor(platform)
    if descriptor is None:
        return _reject(
            attempt_root,
            platform,
            tier,
            "unsupported-platform",
            f"{platform} has no verified autonomy descriptor; skipped without writing config.",
            now=timestamp,
            outcome="skipped",
        )

    declared_path = descriptor.get("config_file")
    if descriptor.get("scope") != "project":
        return _reject(
            attempt_root,
            platform,
            tier,
            "project-scope",
            f"{platform} exposes only a global autonomy lever; Nexus-Hub never writes global autonomy config.",
            config_path=str(Path(str(declared_path)).expanduser().resolve()),
            now=timestamp,
        )

    root = _git_root(project_dir)
    if root is None:
        return _reject(
            attempt_root,
            platform,
            tier,
            "git-repository",
            "Autonomy requires a project inside a git repository; initialize git or choose a repository directory.",
            now=timestamp,
        )

    try:
        config_path = _resolve_project_config(root, descriptor)
    except ValueError as exc:
        return _reject(root, platform, tier, "project-scope", str(exc), now=timestamp)

    tiers = descriptor.get("tiers", {})
    updates = tiers.get(tier) if isinstance(tiers, dict) else None
    if not isinstance(updates, dict) or not updates:
        return _reject(
            root,
            platform,
            tier,
            "tier",
            f"Tier {tier!r} is not supported for {platform}; choose a tier declared by its verified descriptor.",
            config_path=config_path,
            now=timestamp,
        )
    if ttl is None:
        return _reject(
            root,
            platform,
            tier,
            "ttl",
            f"TTL is required; use {DEFAULT_TTL_MINUTES} minutes unless a shorter window is needed.",
            config_path=config_path,
            now=timestamp,
        )
    if (
        isinstance(ttl, bool)
        or not isinstance(ttl, int)
        or ttl <= 0
        or ttl > MAX_TTL_MINUTES
    ):
        return _reject(
            root,
            platform,
            tier,
            "ttl",
            f"TTL must be an integer from 1 to {MAX_TTL_MINUTES} minutes.",
            config_path=config_path,
            now=timestamp,
        )
    if tier == "full" and confirmation != root.name:
        return _reject(
            root,
            platform,
            tier,
            "typed-confirmation",
            f"Full autonomy requires typing the project directory name exactly: {root.name}",
            config_path=config_path,
            now=timestamp,
        )

    try:
        state = _load_state(root)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return _reject(
            root,
            platform,
            tier,
            "state-file",
            f"Autonomy state is unreadable and must be repaired before enablement: {exc}",
            config_path=config_path,
            now=timestamp,
        )
    if platform in state["platforms"]:
        return _reject(
            root,
            platform,
            tier,
            "already-enabled",
            f"{platform} autonomy is already active; disable or revert it before enabling again.",
            config_path=config_path,
            now=timestamp,
        )
    if not _worktree_is_clean(root):
        return _reject(
            root,
            platform,
            tier,
            "clean-worktree",
            "Autonomy requires a clean git worktree; commit or stash tracked and untracked changes first.",
            config_path=config_path,
            now=timestamp,
        )

    branch, head = _branch_and_head(root)
    if branch is None:
        return _reject(
            root,
            platform,
            tier,
            "git-branch",
            "Autonomy requires an attached git branch; check out a feature branch before enabling it.",
            config_path=config_path,
            now=timestamp,
        )
    if branch in _protected_branches(root):
        return _reject(
            root,
            platform,
            tier,
            "protected-branch",
            f"Autonomy is blocked on protected branch {branch!r}; check out a feature branch first.",
            config_path=config_path,
            now=timestamp,
        )

    try:
        original_exists = config_path.exists()
        original_bytes = config_path.read_bytes() if original_exists else b""
        original_text = original_bytes.decode("utf-8")
        updated_text = _render_config(original_text, descriptor, updates)
    except (
        OSError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
    ) as exc:
        return _reject(
            root,
            platform,
            tier,
            "config-read",
            f"The project config cannot be safely read and updated: {exc}",
            config_path=config_path,
            now=timestamp,
        )

    expiry = timestamp + timedelta(minutes=ttl)
    expiry_text = _iso(expiry)
    backup_path = _backup_path(config_path, timestamp)
    preview = _unified_diff(config_path, original_text, updated_text)
    state_entry = {
        "platform": platform,
        "tier": tier,
        "enabled_at": _iso(timestamp),
        "expiry": expiry_text,
        "config_path": str(config_path),
        "backup_path": str(backup_path),
        "original_exists": original_exists,
        "user": user or getpass.getuser(),
        "process": process or f"{Path(sys.executable).name}:{os.getpid()}",
        "git_branch": branch,
        "git_head": head,
    }

    try:
        _write_backup(config_path, backup_path, original_bytes)
        _atomic_write_bytes(config_path, updated_text.encode("utf-8"))
        state["platforms"][platform] = state_entry
        _write_state(root, state)
    except OSError as exc:
        try:
            if backup_path.exists():
                _restore_original(config_path, backup_path, original_exists)
        except OSError:
            pass
        result = OperationResult(
            operation="enable",
            platform=platform,
            outcome="error",
            gate="atomic-write",
            message=f"Autonomy was not enabled because the atomic write failed: {exc}",
            config_path=str(config_path),
            backup_path=str(backup_path) if backup_path.exists() else None,
            expiry=expiry_text,
            diff=preview,
        )
        return _result_with_audit(root, result, tier=tier, now=timestamp)

    result = OperationResult(
        operation="enable",
        platform=platform,
        outcome="enabled",
        message=f"Enabled {tier} autonomy for {platform} until {expiry_text}.",
        changed=True,
        config_path=str(config_path),
        backup_path=str(backup_path),
        expiry=expiry_text,
        diff=preview,
    )
    return _result_with_audit(root, result, tier=tier, now=timestamp)


def _revert_active(
    root: Path,
    platform: str,
    *,
    operation: str,
    success_outcome: str,
    now: datetime | None = None,
) -> OperationResult:
    timestamp = _as_utc(now)
    try:
        state = _load_state(root)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        result = OperationResult(
            operation,
            platform,
            "error",
            f"Autonomy state is unreadable: {exc}",
            gate="state-file",
        )
        return _result_with_audit(root, result, tier=None, now=timestamp)
    entry = state["platforms"].get(platform)
    if not isinstance(entry, dict):
        return OperationResult(
            operation,
            platform,
            "not-active",
            f"{platform} has no active autonomy state.",
        )

    tier = entry.get("tier") if isinstance(entry.get("tier"), str) else None
    config_path = Path(str(entry.get("config_path", ""))).resolve()
    backup_path = Path(str(entry.get("backup_path", ""))).resolve()
    try:
        config_path.relative_to(root)
        backup_path.relative_to(root)
    except ValueError:
        result = OperationResult(
            operation,
            platform,
            "error",
            "Recorded autonomy paths escape the project; state was preserved for manual recovery.",
            gate="project-scope",
            config_path=str(config_path),
            backup_path=str(backup_path),
            expiry=entry.get("expiry"),
        )
        return _result_with_audit(root, result, tier=tier, now=timestamp)
    if not backup_path.is_file():
        result = OperationResult(
            operation,
            platform,
            "error",
            f"Backup is missing at {backup_path}; config and state were left untouched.",
            gate="missing-backup",
            config_path=str(config_path),
            backup_path=str(backup_path),
            expiry=entry.get("expiry"),
        )
        return _result_with_audit(root, result, tier=tier, now=timestamp)

    try:
        _restore_original(config_path, backup_path, bool(entry.get("original_exists")))
        del state["platforms"][platform]
        _write_state(root, state)
        backup_path.unlink(missing_ok=True)
    except OSError as exc:
        result = OperationResult(
            operation,
            platform,
            "error",
            f"Reversion failed and autonomy state was preserved for retry: {exc}",
            gate="revert-write",
            config_path=str(config_path),
            backup_path=str(backup_path),
            expiry=entry.get("expiry"),
        )
        return _result_with_audit(root, result, tier=tier, now=timestamp)

    result = OperationResult(
        operation,
        platform,
        success_outcome,
        f"Restored {platform} config and cleared its autonomy state.",
        changed=True,
        config_path=str(config_path),
        backup_path=str(backup_path),
        expiry=entry.get("expiry"),
    )
    return _result_with_audit(root, result, tier=tier, now=timestamp)


def disable(
    platform: str,
    *,
    project_dir: str | os.PathLike[str] | None = None,
    now: datetime | None = None,
) -> OperationResult:
    root = _git_root(project_dir)
    if root is None:
        return OperationResult(
            "disable",
            platform,
            "error",
            "Disable requires a git repository.",
            gate="git-repository",
        )
    return _revert_active(
        root, platform, operation="disable", success_outcome="disabled", now=now
    )


def revert(
    platform: str,
    *,
    project_dir: str | os.PathLike[str] | None = None,
    now: datetime | None = None,
) -> OperationResult:
    root = _git_root(project_dir)
    if root is None:
        return OperationResult(
            "revert",
            platform,
            "error",
            "Revert requires a git repository.",
            gate="git-repository",
        )
    return _revert_active(
        root, platform, operation="revert", success_outcome="reverted", now=now
    )


def expire(
    *,
    project_dir: str | os.PathLike[str] | None = None,
    now: datetime | None = None,
) -> list[OperationResult]:
    """Revert every expired entry; return an empty list on the fast no-state path."""
    root = _git_root(project_dir)
    if root is None or not _state_path(root).exists():
        return []
    timestamp = _as_utc(now)
    try:
        state = _load_state(root)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return [
            OperationResult(
                "expire",
                "*",
                "error",
                f"Autonomy state is unreadable: {exc}",
                gate="state-file",
            )
        ]
    results: list[OperationResult] = []
    for platform, entry in list(state["platforms"].items()):
        try:
            expiry = _parse_iso(str(entry["expiry"]))
        except (KeyError, TypeError, ValueError):
            result = OperationResult(
                "expire",
                platform,
                "error",
                "Autonomy expiry is invalid; state was preserved.",
                gate="expiry",
            )
            results.append(
                _result_with_audit(root, result, tier=entry.get("tier"), now=timestamp)
            )
            continue
        if expiry <= timestamp:
            results.append(
                _revert_active(
                    root,
                    platform,
                    operation="expire",
                    success_outcome="expired-reverted",
                    now=timestamp,
                )
            )
    return results


def status(
    *,
    project_dir: str | os.PathLike[str] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = _git_root(project_dir)
    if root is None:
        return {
            "project": None,
            "state_path": None,
            "platforms": [],
            "note": "not a git repository",
        }
    timestamp = _as_utc(now)
    try:
        state = _load_state(root)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return {
            "project": str(root),
            "state_path": str(_state_path(root)),
            "platforms": [],
            "note": f"autonomy state is unreadable: {exc}",
        }
    entries: list[dict[str, Any]] = []
    for platform, entry in sorted(state["platforms"].items()):
        item = dict(entry)
        item["platform"] = platform
        try:
            item["status"] = (
                "expired" if _parse_iso(str(entry["expiry"])) <= timestamp else "active"
            )
        except (KeyError, TypeError, ValueError):
            item["status"] = "invalid"
        entries.append(item)
    return {
        "project": str(root),
        "state_path": str(_state_path(root)),
        "platforms": entries,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Nexus-Hub project-local autonomy engine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    expire_parser = subparsers.add_parser(
        "expire", help="Revert expired project autonomy state"
    )
    expire_parser.add_argument("--project", type=Path, default=Path.cwd())
    status_parser = subparsers.add_parser("status", help="Print project autonomy state")
    status_parser.add_argument("--project", type=Path, default=Path.cwd())
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "status":
        print(json.dumps(status(project_dir=args.project), indent=2, sort_keys=True))
        return 0
    results = expire(project_dir=args.project)
    for result in results:
        stream = sys.stderr if result.outcome == "error" else sys.stdout
        print(json.dumps(result.to_dict(), sort_keys=True), file=stream)
    return 1 if any(result.outcome == "error" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
