"""Bring-your-own output filters gated by a SHA-256 content-trust store.

Lookup order is project file, then user-global file, then built-in (empty),
then passthrough. An on-disk file is applied only when its SHA-256 matches the
trust store. Editing the file changes the hash, so it is skipped until trusted
again. This is consent plus tamper-evidence, not a sandbox.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

PROJECT_FILTER_NAME = ".nexus-hub/compressor-filters.json"
GLOBAL_FILTER_NAME = "compressor-filters.json"
TRUST_STORE_NAME = "compressor-trust.json"


def _home_root() -> Path:
    return Path.home() / ".nexus-hub"


def trust_store_path() -> Path:
    override = os.environ.get("NEXUS_COMPRESSOR_TRUST_STORE")
    if override:
        return Path(override)
    return _home_root() / TRUST_STORE_NAME


def project_filter_path(cwd: Path | None = None) -> Path:
    return (cwd or Path.cwd()) / PROJECT_FILTER_NAME


def global_filter_path() -> Path:
    override = os.environ.get("NEXUS_COMPRESSOR_GLOBAL_FILTERS")
    if override:
        return Path(override)
    return _home_root() / GLOBAL_FILTER_NAME


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_trust(store: Path | None = None) -> dict[str, str]:
    path = store or trust_store_path()
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    files = raw.get("files", raw) if isinstance(raw, dict) else {}
    if not isinstance(files, dict):
        return {}
    return {str(key): str(value) for key, value in files.items()}


def _save_trust(mapping: dict[str, str], store: Path | None = None) -> None:
    path = store or trust_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"files": mapping}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _key(path: Path) -> str:
    return str(path.resolve())


def is_trusted(path: Path, store: Path | None = None) -> bool:
    if not path.is_file():
        return False
    mapping = _load_trust(store)
    return mapping.get(_key(path)) == file_digest(path)


def trust(path: Path, store: Path | None = None) -> str:
    """Record the current SHA-256 of ``path``. Returns the digest."""
    resolved = path.resolve()
    digest = file_digest(resolved)
    mapping = _load_trust(store)
    mapping[_key(resolved)] = digest
    _save_trust(mapping, store)
    return digest


def untrust(path: Path, store: Path | None = None) -> None:
    mapping = _load_trust(store)
    mapping.pop(_key(path.resolve()), None)
    _save_trust(mapping, store)


def _load_document(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _apply_one(text: str, spec: dict[str, Any]) -> str | None:
    pattern = spec.get("pattern")
    if not isinstance(pattern, str) or not pattern:
        return None
    try:
        compiled = re.compile(pattern)
    except re.error:
        return None
    action = str(spec.get("action") or "drop-line")
    if action == "drop-line":
        lines = text.splitlines(keepends=True)
        kept = [line for line in lines if not compiled.search(line)]
        if len(kept) == len(lines):
            return None
        return "".join(kept)
    if action == "keep-line":
        lines = text.splitlines(keepends=True)
        kept = [line for line in lines if compiled.search(line)]
        if not kept:
            return None
        return "".join(kept)
    if action == "replace":
        if compiled.search(text) is None:
            return None
        return compiled.sub(str(spec.get("replacement", "")), text)
    return None


def apply_trusted_filters(
    text: str,
    *,
    cwd: Path | None = None,
    trust_store: Path | None = None,
) -> str:
    """Return text after the first matching trusted filter, else ``text``."""
    candidates = (project_filter_path(cwd), global_filter_path())
    for path in candidates:
        if not path.is_file() or not is_trusted(path, trust_store):
            continue
        document = _load_document(path)
        if document is None:
            continue
        filters = document.get("filters", [])
        if not isinstance(filters, list):
            continue
        for spec in filters:
            if not isinstance(spec, dict):
                continue
            rewritten = _apply_one(text, spec)
            if rewritten is not None:
                return rewritten
    return text


def run_inline_tests(path: Path) -> list[tuple[str, bool, str]]:
    """Run ``tests`` entries. Returns ``(name, passed, detail)`` rows."""
    document = _load_document(path)
    if document is None:
        return [("load", False, f"could not parse {path}")]
    cases = document.get("tests", [])
    if not isinstance(cases, list):
        return []
    rows: list[tuple[str, bool, str]] = []
    filters = document.get("filters", [])
    if not isinstance(filters, list):
        filters = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            rows.append((f"case-{index}", False, "test entry is not an object"))
            continue
        name = str(case.get("name") or f"case-{index}")
        sample = str(case.get("input") or "")
        expected = str(case.get("expected") or "")
        actual = sample
        for spec in filters:
            if not isinstance(spec, dict):
                continue
            rewritten = _apply_one(actual, spec)
            if rewritten is not None:
                actual = rewritten
                break
        passed = actual == expected
        detail = "ok" if passed else f"expected {expected!r}, got {actual!r}"
        rows.append((name, passed, detail))
    return rows
