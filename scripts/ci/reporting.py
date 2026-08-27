"""Turn a run into the report artifacts the lifecycle contract requires.

Section 6 of `docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md`: a concise
human summary plus machine-readable evidence, produced by the SAME local
execution a developer can reproduce, deterministic, ASCII-safe, and free of
credentials.

The requirement that carries the most weight is this one: **a failing command
must still produce a readable summary and valid partial metadata.** A run that
fails and reports nothing is indistinguishable from a run that never started,
and the second is the one people assume.
"""

from __future__ import annotations

import json
import os
import platform as platform_mod
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

#: Substrings that mark an environment variable as secret-bearing. Matching on
#: the NAME rather than trying to recognize secret-shaped VALUES: a token format
#: changes without notice, an env var called *_TOKEN does not.
_SECRET_NAME_HINTS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "APIKEY", "API_KEY", "CREDENTIAL")

REDACTED = "[REDACTED]"

#: A generic bearer-token shape, as a backstop for a value that reaches output
#: without ever having been an environment variable.
_INLINE_SECRET = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"
)


def secret_values() -> list[str]:
    """Values of every secret-bearing environment variable, longest first.

    Longest first matters: redacting a short value that is a substring of a
    longer one first would leave a recognizable fragment of the longer one.
    """
    values = []
    for name, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        if any(hint in name.upper() for hint in _SECRET_NAME_HINTS):
            values.append(value)
    return sorted(values, key=len, reverse=True)


def redact(text: str, extra: list[str] | None = None) -> str:
    """Remove known secret values and obvious token shapes from captured output.

    The longest-first ordering is applied HERE rather than only in
    `secret_values()`, because a caller supplying its own list has no reason to
    know the ordering matters. It does: redacting a short value that is a prefix
    of a longer one first leaves a recognizable tail of the longer one behind,
    which is a partial disclosure that reads as a successful redaction.
    """
    if not text:
        return text
    values = extra if extra is not None else secret_values()
    for value in sorted((v for v in values if v), key=len, reverse=True):
        text = text.replace(value, REDACTED)
    return _INLINE_SECRET.sub(REDACTED, text)


@dataclass
class CommandResult:
    name: str
    group: str
    status: str  # "pass" | "fail" | "skip" | "timeout" | "missing" | "advisory-fail"
    duration_s: float = 0.0
    exit_code: int | None = None
    output: str = ""
    reason: str = ""

    @property
    def counts_as_failure(self) -> bool:
        return self.status in ("fail", "timeout", "missing")


@dataclass
class GroupResult:
    name: str
    status: str = "pass"
    commands: list[CommandResult] = field(default_factory=list)
    skipped_reason: str = ""


@dataclass
class RunResult:
    profile: str
    platform: str
    groups: list[GroupResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    duration_s: float = 0.0
    scope_reason: str = ""
    scope_conservative: bool = False

    @property
    def all_commands(self) -> list[CommandResult]:
        return [c for g in self.groups for c in g.commands]

    @property
    def status(self) -> str:
        cmds = self.all_commands
        if any(c.counts_as_failure for c in cmds):
            return "FAIL"
        if not cmds:
            return "PASS"
        if any(c.status in ("skip", "advisory-fail") for c in cmds):
            return "PARTIAL"
        return "PASS"

    def tally(self) -> dict[str, int]:
        counts = {"pass": 0, "fail": 0, "skip": 0, "advisory-fail": 0, "timeout": 0, "missing": 0}
        for c in self.all_commands:
            counts[c.status] = counts.get(c.status, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------


def _rel(path: Path, root: Path) -> str:
    """Repository-relative, forward-slashed. Never an absolute path.

    An absolute path in a report leaks a user name on a developer machine and
    is meaningless on any other, so it fails both the determinism rule and the
    credential rule at once.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def environment_metadata(result: RunResult, tools: dict[str, str] | None = None) -> dict:
    return {
        "profile": result.profile,
        "platform": result.platform,
        "os": platform_mod.system(),
        "os_release": platform_mod.release(),
        "python": platform_mod.python_version(),
        "python_implementation": platform_mod.python_implementation(),
        "tools": dict(sorted((tools or {}).items())),
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "duration_s": round(result.duration_s, 2),
        "status": result.status,
        "scope_reason": result.scope_reason,
        "scope_conservative": result.scope_conservative,
    }


def write_metadata(result: RunResult, reports_dir: Path, tools: dict[str, str] | None = None) -> Path:
    meta_dir = reports_dir / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    path = meta_dir / "environment.json"
    path.write_text(
        json.dumps(environment_metadata(result, tools), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_junit(result: RunResult, reports_dir: Path) -> list[Path]:
    """One JUnit file per group, so a provider renders groups as suites."""
    junit_dir = reports_dir / "junit"
    junit_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for group in result.groups:
        suite = ET.Element(
            "testsuite",
            {
                "name": group.name,
                "tests": str(len(group.commands)),
                "failures": str(sum(1 for c in group.commands if c.counts_as_failure)),
                "skipped": str(sum(1 for c in group.commands if c.status == "skip")),
                "time": f"{sum(c.duration_s for c in group.commands):.2f}",
            },
        )
        for cmd in group.commands:
            case = ET.SubElement(
                suite,
                "testcase",
                {"classname": group.name, "name": cmd.name, "time": f"{cmd.duration_s:.2f}"},
            )
            if cmd.status == "skip":
                ET.SubElement(case, "skipped", {"message": cmd.reason or "skipped"})
            elif cmd.counts_as_failure or cmd.status == "advisory-fail":
                failure = ET.SubElement(
                    case,
                    "failure",
                    {"message": cmd.reason or f"exit {cmd.exit_code}", "type": cmd.status},
                )
                failure.text = cmd.output[-4000:]
        path = junit_dir / f"{group.name}.xml"
        ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)
        written.append(path)
    return written


_STATUS_MARK = {
    "pass": "PASS",
    "fail": "FAIL",
    "skip": "SKIP",
    "timeout": "TIMEOUT",
    "missing": "MISSING",
    "advisory-fail": "WARN",
}


def render_summary(result: RunResult, reports_dir: Path, repo_root: Path) -> str:
    counts = result.tally()
    lines: list[str] = [
        f"# CI Report - profile `{result.profile}` - {result.status}",
        "",
        f"**Platform**: {result.platform} ({platform_mod.system()} {platform_mod.release()})",
        f"**Python**: {platform_mod.python_version()}",
        f"**Duration**: {result.duration_s:.1f}s",
        "",
        "| Result | Count |",
        "|---|---|",
        f"| Passed | {counts['pass']} |",
        f"| Failed | {counts['fail'] + counts['timeout'] + counts['missing']} |",
        f"| Skipped | {counts['skip']} |",
        f"| Advisory failures | {counts['advisory-fail']} |",
        "",
    ]

    if result.scope_reason:
        lines += [f"**Change scope**: {result.scope_reason}", ""]

    lines += ["## Groups", "", "| Group | Status | Commands | Duration |", "|---|---|---|---|"]
    for group in result.groups:
        duration = sum(c.duration_s for c in group.commands)
        detail = group.skipped_reason or f"{len(group.commands)} command(s)"
        lines.append(f"| {group.name} | {group.status.upper()} | {detail} | {duration:.1f}s |")
    lines.append("")

    failures = [c for c in result.all_commands if c.counts_as_failure or c.status == "advisory-fail"]
    if failures:
        lines += ["## Failures", ""]
        for cmd in failures:
            lines += [
                f"### {_STATUS_MARK.get(cmd.status, cmd.status.upper())} `{cmd.group}` / {cmd.name}",
                "",
                f"Exit code: `{cmd.exit_code}`. {cmd.reason}".strip(),
                "",
                "```text",
                (cmd.output or "(no output captured)").rstrip()[-2000:],
                "```",
                "",
            ]
    else:
        lines += ["## Failures", "", "None.", ""]

    lines += [
        "## Artifacts",
        "",
        f"- `{_rel(reports_dir / 'summary.md', repo_root)}`",
        f"- `{_rel(reports_dir / 'summary.json', repo_root)}`",
        f"- `{_rel(reports_dir / 'junit', repo_root)}/<group>.xml`",
        f"- `{_rel(reports_dir / 'metadata' / 'environment.json', repo_root)}`",
        "",
    ]
    return "\n".join(lines)


def write_reports(
    result: RunResult,
    reports_dir: Path,
    repo_root: Path,
    tools: dict[str, str] | None = None,
) -> dict[str, Path]:
    """Write every artifact. Safe to call after a failure, and after a crash.

    Each writer is attempted independently: one unwritable artifact must not
    cost the others, because the artifact most likely to fail (JUnit, which
    serializes captured output) is the least important of the four.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    for label, writer in (
        ("summary.md", lambda: _write_text(reports_dir / "summary.md", render_summary(result, reports_dir, repo_root))),
        ("summary.json", lambda: _write_text(
            reports_dir / "summary.json",
            json.dumps(asdict(result), indent=2, sort_keys=True) + "\n",
        )),
        ("metadata", lambda: write_metadata(result, reports_dir, tools)),
    ):
        try:
            written[label] = writer()
        except Exception as exc:  # noqa: BLE001 - reporting must never mask the run
            print(f"warning: could not write {label}: {exc}", file=sys.stderr)

    try:
        junit = write_junit(result, reports_dir)
        if junit:
            written["junit"] = junit[0].parent
    except Exception as exc:  # noqa: BLE001
        print(f"warning: could not write junit: {exc}", file=sys.stderr)

    return written


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Explicit newline="\n": the summary is compared across hosts and appended
    # to a provider run summary, so CRLF on a Windows leg would make two
    # identical runs differ byte for byte.
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path
