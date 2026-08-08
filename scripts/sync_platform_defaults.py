#!/usr/bin/env python3
"""Sync (or check) the artifacts derived from ``configs/platform-defaults.json``.

``configs/platform-defaults.json`` is the single place a per-platform install-time
behavioral default is declared. Every consuming artifact is DERIVED from it. This
script is the mechanism that keeps that promise:

``--check``
    Compare every derived artifact against the declared source and exit non-zero
    on any disagreement, naming the artifact, the key, the declared value, and
    the value actually found. Runs in ``make validate`` and in CI, so drift is a
    build failure rather than something a reader has to notice.

``--apply``
    Rewrite the derived artifacts from the source.

Two constraints shape the implementation, and both come from real hazards:

1. ``catalog/hooks/settings.json`` carries the entire hook registration block
   (SessionStart / PreToolUse / PostToolUse / UserPromptSubmit / Notification /
   Stop / PreCompact / SessionEnd) alongside the four core keys this script
   owns. The generator therefore updates only the declared keys IN PLACE and
   leaves everything else byte-identical. It never serializes a fresh object
   over the file.

2. This repository runs ``core.autocrlf=true`` with ``* text=auto``, so the
   working tree materializes CRLF on Windows while git stores LF. Writing a
   fixed ``"\\n"`` would silently rewrite every line ending on a Windows
   checkout. Each artifact's existing dominant newline is detected and
   preserved, which is what makes "an --apply run with no source change
   produces a byte-identical file" true on every platform rather than only in
   CI.

Repo-internal maintainer guard: stdlib only, no outbound call, no meaning on an
end-user install. Listed in ``DEV_ONLY_SCRIPTS`` in
``catalog/hooks/tests/test_installer_smoke.py``; deliberately NOT copied by the
installers.

Exit codes: 0 = in sync (or applied), 1 = drift detected, 2 = usage or source error.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULTS_PATH = REPO_ROOT / "configs" / "platform-defaults.json"

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_ERROR = 2

# Strategies a derived artifact may declare.
STRATEGY_MERGE_KEYS = "merge-keys"
STRATEGY_RUNTIME_READ = "runtime-read"
KNOWN_STRATEGIES = {STRATEGY_MERGE_KEYS, STRATEGY_RUNTIME_READ}


class SourceError(Exception):
    """The defaults file or a derived artifact is malformed or missing."""


# --------------------------------------------------------------------------
# Source loading and dotted-key access
# --------------------------------------------------------------------------


def load_defaults(path: Path = DEFAULTS_PATH) -> dict[str, Any]:
    """Load and minimally validate the defaults source."""
    if not path.is_file():
        raise SourceError(f"defaults source not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SourceError(f"{path} is not valid JSON: {exc}") from exc
    if not isinstance(data.get("platforms"), dict):
        raise SourceError(f"{path} is missing a top-level 'platforms' object")
    return data


def resolve_key(settings: dict[str, Any], dotted: str) -> Any:
    """Resolve a dotted path such as ``env.CLAUDE_CODE_EFFORT_LEVEL``."""
    node: Any = settings
    walked: list[str] = []
    for part in dotted.split("."):
        walked.append(part)
        if not isinstance(node, dict) or part not in node:
            raise SourceError(
                f"declared key {dotted!r} is not present in the platform's "
                f"'settings' object (failed at {'.'.join(walked)!r})"
            )
        node = node[part]
    return node


def set_key(target: dict[str, Any], dotted: str, value: Any) -> None:
    """Set a dotted path in ``target``, creating intermediate dicts as needed."""
    parts = dotted.split(".")
    node = target
    for part in parts[:-1]:
        existing = node.get(part)
        if not isinstance(existing, dict):
            existing = {}
            node[part] = existing
        node = existing
    node[parts[-1]] = value


def get_key_or_missing(target: dict[str, Any], dotted: str) -> Any:
    """Resolve a dotted path, returning the ``MISSING`` sentinel when absent."""
    node: Any = target
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return MISSING
        node = node[part]
    return node


class _Missing:
    def __repr__(self) -> str:  # pragma: no cover - trivial
        return "<absent>"


MISSING = _Missing()


# --------------------------------------------------------------------------
# Byte-preserving text helpers
# --------------------------------------------------------------------------


def read_text_raw(path: Path) -> str:
    """Read text with newline translation disabled.

    ``Path.read_text(newline=...)`` only exists on Python 3.13+, and this repo
    targets 3.12, so the newline argument is passed through ``open`` instead.
    Disabling translation is what lets ``detect_newline`` see the artifact's
    real line endings.
    """
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def detect_newline(text: str) -> str:
    """Return the artifact's dominant newline so a rewrite preserves it.

    A Windows checkout of this repo has CRLF in the working tree while git
    stores LF. Preserving what is actually on disk is what keeps ``--apply``
    byte-identical on both.
    """
    crlf = text.count("\r\n")
    lf = text.count("\n") - crlf
    return "\r\n" if crlf > lf else "\n"


def detect_indent(text: str, default: int = 2) -> int:
    """Detect the indentation width of a JSON artifact."""
    match = re.search(r"^(?P<indent> +)\S", text, re.MULTILINE)
    return len(match.group("indent")) if match else default


def render_json(data: Any, indent: int, newline: str) -> str:
    """Serialize with the artifact's own indentation and newline convention."""
    body = json.dumps(data, indent=indent, ensure_ascii=False) + "\n"
    if newline != "\n":
        body = body.replace("\n", newline)
    return body


def render_python_literal(value: Any, indent: int = 4, level: int = 1) -> str:
    """Render a JSON-ish value as a ruff-formatted Python literal.

    Dicts are rendered expanded with a magic trailing comma, which is exactly
    what ``ruff format`` produces, so an ``--apply`` run does not fight the
    formatter.
    """
    pad = " " * (indent * level)
    closing_pad = " " * (indent * (level - 1))
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for key, inner in value.items():
            rendered = render_python_literal(inner, indent=indent, level=level + 1)
            lines.append(f"{pad}{json.dumps(key)}: {rendered},")
        lines.append(f"{closing_pad}}}")
        return "\n".join(lines)
    if isinstance(value, str):
        return json.dumps(value)
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    return repr(value)


# --------------------------------------------------------------------------
# Drift records
# --------------------------------------------------------------------------


class Drift:
    """One disagreement between the declared source and a derived artifact."""

    def __init__(
        self, platform: str, artifact: str, key: str, declared: Any, found: Any
    ) -> None:
        self.platform = platform
        self.artifact = artifact
        self.key = key
        self.declared = declared
        self.found = found

    def __str__(self) -> str:
        found = "<absent>" if self.found is MISSING else repr(self.found)
        return (
            f"  {self.artifact}\n"
            f"    platform : {self.platform}\n"
            f"    key      : {self.key}\n"
            f"    declared : {self.declared!r}\n"
            f"    found    : {found}"
        )


# --------------------------------------------------------------------------
# Strategy: merge-keys (JSON artifacts)
# --------------------------------------------------------------------------


def _artifact_path(artifact: dict[str, Any], repo_root: Path) -> Path:
    path = repo_root / artifact["path"]
    if not path.is_file():
        raise SourceError(f"derived artifact not found: {path}")
    return path


def check_merge_keys(
    platform: str, settings: dict[str, Any], artifact: dict[str, Any], repo_root: Path
) -> list[Drift]:
    path = _artifact_path(artifact, repo_root)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SourceError(f"{path} is not valid JSON: {exc}") from exc
    drifts: list[Drift] = []
    for key in artifact["keys"]:
        declared = resolve_key(settings, key)
        found = get_key_or_missing(data, key)
        if found != declared:
            drifts.append(Drift(platform, artifact["path"], key, declared, found))
    return drifts


def apply_merge_keys(
    settings: dict[str, Any], artifact: dict[str, Any], repo_root: Path
) -> bool:
    """Update only the declared keys in place. Returns True when bytes changed."""
    path = _artifact_path(artifact, repo_root)
    original = read_text_raw(path)
    newline = detect_newline(original)
    indent = detect_indent(original)
    # json.loads preserves insertion order into the resulting dict (3.7+), so
    # re-dumping keeps the original key order and leaves the hooks block intact.
    data = json.loads(original)
    for key in artifact["keys"]:
        set_key(data, key, resolve_key(settings, key))
    updated = render_json(data, indent=indent, newline=newline)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8", newline="")
    return True


# --------------------------------------------------------------------------
# Strategy: runtime-read (Python artifacts with an offline fallback)
# --------------------------------------------------------------------------


def _find_fallback_assignment(tree: ast.Module, symbol: str) -> ast.Assign:
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == symbol for t in node.targets
        ):
            return node
    raise SourceError(f"fallback symbol {symbol!r} not found as a module-level assignment")


def _read_fallback(path: Path, symbol: str) -> tuple[dict[str, Any], ast.Assign, str]:
    source = read_text_raw(path)
    tree = ast.parse(source.replace("\r\n", "\n"))
    node = _find_fallback_assignment(tree, symbol)
    try:
        literal = ast.literal_eval(node.value)
    except ValueError as exc:
        raise SourceError(
            f"{path}: {symbol!r} must be a plain literal so it can be verified "
            f"without importing the module ({exc})"
        ) from exc
    if not isinstance(literal, dict):
        raise SourceError(f"{path}: {symbol!r} must be a dict literal")
    return literal, node, source


def check_runtime_read(
    platform: str, settings: dict[str, Any], artifact: dict[str, Any], repo_root: Path
) -> list[Drift]:
    """Verify the module's offline fallback still matches the declared values.

    The artifact reads the defaults file at runtime, so there is nothing to
    generate. What CAN drift is the hardcoded fallback it keeps for installed
    trees that do not carry ``configs/``: if it is left behind, it quietly
    states something untrue. Guarding it is the point of this check.
    """
    symbol = artifact.get("fallback_symbol")
    if not symbol:
        return []
    path = _artifact_path(artifact, repo_root)
    fallback, _node, _source = _read_fallback(path, symbol)
    drifts: list[Drift] = []
    for key in artifact["keys"]:
        declared = resolve_key(settings, key)
        found = get_key_or_missing(fallback, key)
        if found != declared:
            drifts.append(
                Drift(platform, f"{artifact['path']}::{symbol}", key, declared, found)
            )
    return drifts


def apply_runtime_read(
    settings: dict[str, Any], artifact: dict[str, Any], repo_root: Path
) -> bool:
    """Rewrite the fallback literal in place so --apply can fix what --check flags."""
    symbol = artifact.get("fallback_symbol")
    if not symbol:
        return False
    path = _artifact_path(artifact, repo_root)
    fallback, node, source = _read_fallback(path, symbol)
    updated_fallback = json.loads(json.dumps(fallback))
    for key in artifact["keys"]:
        set_key(updated_fallback, key, resolve_key(settings, key))
    if updated_fallback == fallback:
        return False
    newline = detect_newline(source)
    lines = source.replace("\r\n", "\n").split("\n")
    rendered = f"{symbol} = {render_python_literal(updated_fallback)}"
    # ast line numbers are 1-based and end_lineno is inclusive.
    new_lines = lines[: node.lineno - 1] + rendered.split("\n") + lines[node.end_lineno :]
    updated = "\n".join(new_lines)
    if newline != "\n":
        updated = updated.replace("\n", newline)
    path.write_text(updated, encoding="utf-8", newline="")
    return True


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

_CHECKERS = {
    STRATEGY_MERGE_KEYS: check_merge_keys,
    STRATEGY_RUNTIME_READ: check_runtime_read,
}
_APPLIERS = {
    STRATEGY_MERGE_KEYS: apply_merge_keys,
    STRATEGY_RUNTIME_READ: apply_runtime_read,
}


def _iter_artifacts(defaults: dict[str, Any]):
    for platform, entry in defaults["platforms"].items():
        settings = entry.get("settings")
        if not isinstance(settings, dict):
            raise SourceError(f"platform {platform!r} is missing a 'settings' object")
        for artifact in entry.get("derived_artifacts", []):
            strategy = artifact.get("strategy")
            if strategy not in KNOWN_STRATEGIES:
                raise SourceError(
                    f"platform {platform!r} artifact {artifact.get('path')!r} declares "
                    f"unknown strategy {strategy!r} (known: {sorted(KNOWN_STRATEGIES)})"
                )
            yield platform, settings, artifact, strategy


def check(defaults: dict[str, Any], repo_root: Path = REPO_ROOT) -> list[Drift]:
    drifts: list[Drift] = []
    for platform, settings, artifact, strategy in _iter_artifacts(defaults):
        drifts.extend(_CHECKERS[strategy](platform, settings, artifact, repo_root))
    return drifts


def apply(defaults: dict[str, Any], repo_root: Path = REPO_ROOT) -> list[str]:
    changed: list[str] = []
    for _platform, settings, artifact, strategy in _iter_artifacts(defaults):
        if _APPLIERS[strategy](settings, artifact, repo_root):
            changed.append(artifact["path"])
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Sync or check the artifacts derived from configs/platform-defaults.json."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="fail (exit 1) when a derived artifact disagrees with the source",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="rewrite the derived artifacts from the source",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULTS_PATH,
        help=f"path to the defaults source (default: {DEFAULTS_PATH})",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="root the derived artifact paths are resolved against",
    )
    args = parser.parse_args(argv)

    try:
        defaults = load_defaults(args.source)
        if args.check:
            drifts = check(defaults, args.repo_root)
            if drifts:
                print(
                    "Derived artifacts have drifted from "
                    f"{args.source.as_posix()}:\n", file=sys.stderr
                )
                for drift in drifts:
                    print(drift, file=sys.stderr)
                print(
                    "\nEdit configs/platform-defaults.json (the source), then run:\n"
                    "  python scripts/sync_platform_defaults.py --apply",
                    file=sys.stderr,
                )
                return EXIT_DRIFT
            platforms = len(defaults["platforms"])
            print(
                f"  platform-defaults OK -- {platforms} platform(s), "
                "all derived artifacts in sync"
            )
            return EXIT_OK

        changed = apply(defaults, args.repo_root)
        if changed:
            print(f"Updated {len(changed)} derived artifact(s) from {args.source.as_posix()}:")
            for path in changed:
                print(f"  {path}")
        else:
            print("Already in sync -- no derived artifact changed.")
        return EXIT_OK
    except SourceError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
