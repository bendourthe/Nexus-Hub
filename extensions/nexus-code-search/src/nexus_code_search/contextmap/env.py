"""Environment-variable audit.

Scans indexed source files for environment-variable references and merges in the
NAMES declared in `.env.example`-style files (never the real `.env`, and never a
value - name only). Each variable is classified `required` (accessed with no
default anywhere and not documented in an example file) or has-default.

Deterministic and local-only. Patterns are specific to real env-access forms so
a look-alike dictionary access does not produce a false positive.
"""

from __future__ import annotations

import re
from pathlib import Path

from nexus_code_search.contextmap.model import EnvVar

# Example-style env files we read for NAMES only. The real `.env` is never read
# (it holds secrets); only *.example / *.sample / *.template / *.defaults.
_ENV_EXAMPLE_GLOBS = (
    ".env.example",
    ".env.sample",
    ".env.template",
    ".env.defaults",
    "*.env.example",
)

# Python env access. Each pattern captures the variable name in group 1.
_PY_PATTERNS = (
    re.compile(r"""(?:os\.)?environ\.get\(\s*["']([A-Za-z_]\w*)["']\s*(,)?"""),
    re.compile(r"""os\.getenv\(\s*["']([A-Za-z_]\w*)["']\s*(,)?"""),
    re.compile(r"""(?:os\.)?environ\[\s*["']([A-Za-z_]\w*)["']\s*\]"""),
)
# JS / TS env access.
_JS_DOT = re.compile(r"""(?:process\.env|import\.meta\.env)\.([A-Za-z_]\w*)""")
_JS_INDEX = re.compile(r"""process\.env\[\s*["']([A-Za-z_]\w*)["']\s*\]""")
# A default follows a JS access when `||` or `??` comes next.
_JS_DEFAULT_SUFFIX = re.compile(r"""^\s*(?:\|\||\?\?)""")

# `KEY=...` / `KEY =` lines in an example env file (name only; value ignored).
_ENV_LINE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_]\w*)\s*=")

_PY_LANGS = frozenset({"python"})
_JS_LANGS = frozenset({"typescript", "tsx", "javascript", "jsx"})


def audit_env_vars(root: Path, code_files: list[tuple[str, str]]) -> list[EnvVar]:
    """Audit env-var usage across ``code_files`` (list of (rel_path, language)).

    Also merges NAMES from any `.env.example`-style files under ``root``. Returns
    a sorted list of :class:`EnvVar`.
    """
    # name -> [appears_in_code, any_default, best_source]
    seen: dict[str, dict] = {}

    def record(name: str, has_default: bool, source: str, in_code: bool) -> None:
        entry = seen.setdefault(
            name,
            {"in_code": False, "has_default": False, "example": False, "source": None},
        )
        if in_code:
            entry["in_code"] = True
            if has_default:
                entry["has_default"] = True
        else:
            entry["example"] = True
        # Prefer the lexicographically-first code source; fall back to any source.
        if entry["source"] is None or (in_code and (entry["source"] is None)):
            entry["source"] = source
        elif in_code and source < entry["source"]:
            entry["source"] = source

    for rel_path, language in sorted(code_files):
        text = _read(root / rel_path)
        if not text:
            continue
        if language in _PY_LANGS:
            _scan_python(text, rel_path, record)
        elif language in _JS_LANGS:
            _scan_js(text, rel_path, record)

    for env_file in _find_env_example_files(root):
        rel = _relpath(root, env_file)
        for name in _scan_env_example(env_file):
            record(name, has_default=True, source=rel, in_code=False)

    results: list[EnvVar] = []
    for name in sorted(seen):
        entry = seen[name]
        required = not (entry["has_default"] or entry["example"])
        results.append(
            EnvVar(name=name, required=required, source_file=entry["source"] or "")
        )
    return results


def _scan_python(text: str, rel_path: str, record) -> None:
    for pattern in _PY_PATTERNS:
        for match in pattern.finditer(text):
            has_default = (
                match.lastindex is not None and match.group(match.lastindex) == ","
            )
            record(match.group(1), has_default, rel_path, in_code=True)


def _scan_js(text: str, rel_path: str, record) -> None:
    for pattern in (_JS_DOT, _JS_INDEX):
        for match in pattern.finditer(text):
            tail = text[match.end() : match.end() + 8]
            has_default = bool(_JS_DEFAULT_SUFFIX.match(tail))
            record(match.group(1), has_default, rel_path, in_code=True)


def _scan_env_example(path: Path) -> list[str]:
    names: list[str] = []
    text = _read(path)
    if not text:
        return names
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        match = _ENV_LINE.match(line)
        if match:
            names.append(match.group(1))
    return names


def _find_env_example_files(root: Path) -> list[Path]:
    found: list[Path] = []
    for glob in _ENV_EXAMPLE_GLOBS:
        found.extend(root.glob(glob))
        found.extend(root.glob(f"*/{glob}"))
    # Deduplicate while staying deterministic.
    unique = sorted({p.resolve() for p in found if p.is_file()})
    return unique


def env_example_fingerprint_files(root: Path) -> list[Path]:
    """Public: the example env files that feed the audit (for the map's
    source fingerprint, so a change to one invalidates the compiled map)."""
    return _find_env_example_files(root)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _relpath(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name
