"""High-frequency semantic reformatters for command output.

These parse-and-restructure a short named list of tool outputs. They are not
line-strippers and they do not attempt parity with a dedicated ~60-handler
command-output compressor. Unrecognized text returns None so the ContentRouter
can still run.
"""

from __future__ import annotations

import re
from collections import defaultdict

_GIT_STATUS_HINTS = (
    "changes not staged for commit:",
    "changes to be committed:",
    "untracked files:",
    "your branch is",
)
_PYTEST_HINTS = ("===", "failed", "error", "passed")
_VITEST_HINTS = ("failing tests", "test files", "✓", "×", "fail ")
_JEST_HINTS = ("test suites:", "tests:", "snapshots:")
_RUFF_RE = re.compile(r"^(.+?):(\d+):(?:\d+:)?\s+(\w+)\s+(.*)$")
_ESLINT_RE = re.compile(r"^(.+?):(\d+):(\d+):\s+(error|warning)\s+(.*)$")
_TSC_RE = re.compile(r"^(.+?)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.*)$")


def try_reformat(text: str) -> str | None:
    """Return reformatted text, or None when no handler claims the blob."""
    if not text or not text.strip():
        return None
    lowered = text.lower()
    if _looks_like_git_status(text, lowered):
        return _reformat_git_status(text)
    if _looks_like_pytest(text, lowered):
        return _reformat_pytest(text)
    if _looks_like_vitest_or_jest(text, lowered):
        return _reformat_test_runner(text)
    if _looks_like_ruff(text):
        return _reformat_diagnostics(text, _RUFF_RE, kind="ruff")
    if _looks_like_eslint(text):
        return _reformat_diagnostics(text, _ESLINT_RE, kind="eslint")
    if _looks_like_tsc(text):
        return _reformat_tsc(text)
    return None


def _looks_like_git_status(text: str, lowered: str) -> bool:
    if "on branch " in lowered:
        return True
    return any(hint in lowered for hint in _GIT_STATUS_HINTS)


def _looks_like_pytest(text: str, lowered: str) -> bool:
    return _PYTEST_HINTS[0] in text and any(token in lowered for token in _PYTEST_HINTS[1:])


def _looks_like_vitest_or_jest(text: str, lowered: str) -> bool:
    return any(hint in lowered for hint in _VITEST_HINTS + _JEST_HINTS)


def _looks_like_ruff(text: str) -> bool:
    hits = sum(1 for line in text.splitlines() if _RUFF_RE.match(line.strip()))
    return hits >= 2


def _looks_like_eslint(text: str) -> bool:
    hits = sum(1 for line in text.splitlines() if _ESLINT_RE.match(line.strip()))
    return hits >= 2


def _looks_like_tsc(text: str) -> bool:
    hits = sum(1 for line in text.splitlines() if _TSC_RE.match(line.strip()))
    return hits >= 2


def _reformat_git_status(text: str) -> str:
    branch = ""
    staged: list[str] = []
    modified: list[str] = []
    untracked: list[str] = []
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if lower.startswith("on branch "):
            branch = line[10:].strip()
            continue
        if lower.startswith("changes to be committed"):
            section = "staged"
            continue
        if lower.startswith("changes not staged"):
            section = "modified"
            continue
        if lower.startswith("untracked files"):
            section = "untracked"
            continue
        if not line:
            continue
        if (
            lower.startswith(("use ", "(", "no changes added", "nothing added to commit"))
            or "use \"git" in lower
        ):
            continue
        name = line
        for prefix in ("modified:", "new file:", "deleted:", "renamed:"):
            if lower.startswith(prefix):
                name = line.split(":", 1)[1].strip()
                break
        if section == "staged":
            staged.append(name)
        elif section == "modified":
            modified.append(name)
        elif section == "untracked":
            untracked.append(name)
    lines = ["git status"]
    if branch:
        lines.append(f"branch: {branch}")
    if staged:
        lines.append(f"staged ({len(staged)}):")
        lines.extend(f"- {item}" for item in staged)
    if modified:
        lines.append(f"modified ({len(modified)}):")
        lines.extend(f"- {item}" for item in modified)
    if untracked:
        lines.append(f"untracked ({len(untracked)}):")
        lines.extend(f"- {item}" for item in untracked)
    return "\n".join(lines) + "\n"


def _reformat_pytest(text: str) -> str:
    failed: list[str] = []
    summary = ""
    in_failures = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("====") and "FAILURES" in line:
            in_failures = True
            continue
        if line.startswith("====") and "FAILURES" not in line:
            in_failures = False
        if in_failures and line.startswith("____"):
            name = line.strip(" _")
            if name:
                failed.append(name)
        if re.search(r"\d+ failed", line) or re.search(r"\d+ passed", line):
            summary = line.strip()
    lines = ["pytest (failures only)"]
    if summary:
        lines.append(summary)
    if failed:
        lines.append(f"failed ({len(failed)}):")
        lines.extend(f"- {item}" for item in failed)
    elif not summary:
        return text
    return "\n".join(lines) + "\n"


def _reformat_test_runner(text: str) -> str:
    failed: list[str] = []
    summary_lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        lower = line.lower()
        if lower.startswith("fail ") or line.startswith("FAIL "):
            failed.append(line.split(None, 1)[-1] if " " in line else line)
        if "failed" in lower and ("test" in lower or "suite" in lower):
            summary_lines.append(line)
        if line.startswith(("Test Suites:", "Tests:")):
            summary_lines.append(line)
    if not failed and not summary_lines:
        return text
    lines = ["test runner (failures only)"]
    lines.extend(summary_lines)
    if failed:
        lines.append(f"failed ({len(failed)}):")
        lines.extend(f"- {item}" for item in failed)
    return "\n".join(lines) + "\n"


def _reformat_diagnostics(text: str, pattern: re.Pattern[str], *, kind: str) -> str:
    grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
    total = 0
    for raw in text.splitlines():
        match = pattern.match(raw.strip())
        if not match:
            continue
        path = match.group(1)
        grouped[path].append(_issue_key(match, kind))
        total += 1
    if not grouped:
        return text
    lines = [f"{kind} (grouped by file, {total} issue(s))"]
    for path in sorted(grouped):
        lines.append(f"{path}:")
        collapsed: dict[tuple[str, str], int] = {}
        order: list[tuple[str, str]] = []
        for code, msg in grouped[path]:
            key = (code, msg)
            if key not in collapsed:
                collapsed[key] = 0
                order.append(key)
            collapsed[key] += 1
        for code, msg in order:
            count = collapsed[(code, msg)]
            prefix = f"{code} x{count}" if count > 1 else code
            lines.append(f"- {prefix} {msg}")
    return "\n".join(lines) + "\n"


def _issue_key(match: re.Match[str], kind: str) -> tuple[str, str]:
    groups = match.groups()
    if kind == "ruff":
        return groups[2], groups[3]
    if kind == "eslint":
        return groups[3], groups[4]
    return groups[-2], groups[-1]


def _reformat_tsc(text: str) -> str:
    grouped: dict[str, list[str]] = defaultdict(list)
    for raw in text.splitlines():
        match = _TSC_RE.match(raw.strip())
        if not match:
            continue
        path, line_no, col, level, code, msg = match.groups()
        grouped[path].append(f"{line_no}:{col} {level} {code} {msg}")
    if not grouped:
        return text
    lines = [f"tsc (grouped by file, {sum(len(v) for v in grouped.values())} issue(s))"]
    for path in sorted(grouped):
        lines.append(f"{path}:")
        lines.extend(f"- {item}" for item in grouped[path])
    return "\n".join(lines) + "\n"
