"""Tests for the session-query extraction script.

Exercises catalog/skills/workflow/session-query/scripts/extract-session.py
against a small fixture JSONL set: digest field shape, topic filtering,
time-window filtering, branch filtering, malformed-line resilience, and a
static-analysis assertion that the extractor (and its discovery sibling) make
zero outbound network calls.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "catalog" / "skills" / "workflow" / "session-query" / "scripts"
EXTRACT_PY = SCRIPTS_DIR / "extract-session.py"
EXTRACT_PS1 = SCRIPTS_DIR / "extract-session.ps1"
DISCOVER_SH = SCRIPTS_DIR / "discover-sessions.sh"
DISCOVER_PS1 = SCRIPTS_DIR / "discover-sessions.ps1"


SESSION_A = [
    {"ts": "2026-05-02T09:00:00Z", "role": "user", "prompt_sample": "debug the auth token refresh race"},
    {"ts": "2026-05-02T09:05:00Z", "role": "assistant", "text": "found the token refresh race condition", "branch": "feature/login"},
    {"ts": "2026-05-02T09:10:00Z", "role": "assistant", "text": "unrelated note about styling"},
]

SESSION_B = [
    {"timestamp": "2026-04-01T12:00:00Z", "event": "user", "prompt": "set up the deploy pipeline"},
    {"timestamp": "2026-04-01T12:30:00Z", "event": "assistant", "content": "configured the deploy workflow"},
]


def write_jsonl(path: Path, records: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
    return path


def run_extract(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(EXTRACT_PY), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_scripts_and_siblings_exist() -> None:
    # Cross-platform parity rule: every .py/.sh ships a .ps1 sibling.
    for path in (EXTRACT_PY, EXTRACT_PS1, DISCOVER_SH, DISCOVER_PS1):
        assert path.is_file(), f"missing bundled script: {path}"


def test_digest_field_shape(tmp_path: Path) -> None:
    f = write_jsonl(tmp_path / "a.jsonl", SESSION_A)
    digest = run_extract(str(f), "--topic", "auth,token refresh", "--tool", "claude")

    assert set(digest) == {"query", "sessions", "summary"}
    assert set(digest["summary"]) == {"files_scanned", "files_matched", "snippets_total"}
    assert digest["summary"]["files_scanned"] == 1
    assert digest["summary"]["files_matched"] == 1

    session = digest["sessions"][0]
    for field in (
        "tool",
        "path",
        "first_ts",
        "last_ts",
        "records_total",
        "records_matched",
        "branches",
        "snippets",
    ):
        assert field in session, f"missing session field: {field}"
    assert session["tool"] == "claude"
    assert session["records_total"] == 3
    # Two records match the topic OR ("auth" in record 0, "token refresh" in record 1).
    assert session["records_matched"] == 2
    assert "feature/login" in session["branches"]
    assert session["snippets"], "expected at least one matched snippet"


def test_time_window_filtering(tmp_path: Path) -> None:
    f = write_jsonl(tmp_path / "a.jsonl", SESSION_A)
    # Window excludes the 09:10 record; topic broadened to all three.
    digest = run_extract(
        str(f),
        "--since",
        "2026-05-02T09:00:00Z",
        "--until",
        "2026-05-02T09:06:00Z",
    )
    session = digest["sessions"][0]
    # records_total counts all lines; matched honors the window (2 of 3).
    assert session["records_total"] == 3
    assert session["records_matched"] == 2


def test_since_excludes_older_session(tmp_path: Path) -> None:
    write_jsonl(tmp_path / "a.jsonl", SESSION_A)  # May
    write_jsonl(tmp_path / "b.jsonl", SESSION_B)  # April
    digest = run_extract("--root", str(tmp_path), "--since", "2026-05-01T00:00:00Z")
    matched_paths = [Path(s["path"]).name for s in digest["sessions"]]
    assert "a.jsonl" in matched_paths
    assert "b.jsonl" not in matched_paths  # entirely before the window


def test_topic_no_match_drops_session(tmp_path: Path) -> None:
    f = write_jsonl(tmp_path / "a.jsonl", SESSION_A)
    digest = run_extract(str(f), "--topic", "kubernetes-helm-chart")
    assert digest["summary"]["files_matched"] == 0
    assert digest["sessions"] == []


def test_branch_filter(tmp_path: Path) -> None:
    f = write_jsonl(tmp_path / "a.jsonl", SESSION_A)
    digest = run_extract(str(f), "--branch", "feature/login")
    assert digest["summary"]["files_matched"] == 1
    # The branch appears on one record (field) and matches there.
    assert digest["sessions"][0]["records_matched"] >= 1


def test_malformed_lines_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "messy.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"ts": "2026-05-02T09:00:00Z", "text": "auth token work"}),
                "this is not json {",
                "",
                json.dumps({"ts": "2026-05-02T09:01:00Z", "text": "more auth work"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    digest = run_extract(str(path), "--topic", "auth")
    session = digest["sessions"][0]
    # Two valid records parsed and matched; the malformed and blank lines skipped.
    assert session["records_total"] == 2
    assert session["records_matched"] == 2


def test_no_filter_reports_every_session(tmp_path: Path) -> None:
    write_jsonl(tmp_path / "a.jsonl", SESSION_A)
    write_jsonl(tmp_path / "b.jsonl", SESSION_B)
    digest = run_extract("--root", str(tmp_path))
    assert digest["summary"]["files_scanned"] == 2
    assert digest["summary"]["files_matched"] == 2


def test_invalid_since_errors(tmp_path: Path) -> None:
    f = write_jsonl(tmp_path / "a.jsonl", SESSION_A)
    proc = subprocess.run(
        [sys.executable, str(EXTRACT_PY), str(f), "--since", "not-a-date"],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )
    assert proc.returncode != 0
    assert "since" in proc.stderr.lower()


@pytest.mark.parametrize(
    "script,banned",
    [
        # Import-statement-precise tokens: the docstrings legitimately name the
        # modules they avoid ("imports no socket / urllib / http / requests"),
        # so bare substrings would false-positive. Match the executable form.
        (EXTRACT_PY, ["import socket", "import urllib", "import http", "import ssl", "import requests", "import ftplib", "import smtplib", "urlopen(", "socket.socket"]),
        (EXTRACT_PS1, ["Invoke-WebRequest", "Invoke-RestMethod", "System.Net", "WebClient", "curl", "wget"]),
        (DISCOVER_SH, ["curl", "wget", "/dev/tcp", "ncat"]),
        (DISCOVER_PS1, ["Invoke-WebRequest", "Invoke-RestMethod", "System.Net", "WebClient", "curl", "wget"]),
    ],
)
def test_zero_outbound_static_analysis(script: Path, banned: list[str]) -> None:
    """Static guard: the extractor and discovery scripts make no network call."""
    text = script.read_text(encoding="utf-8")
    for token in banned:
        assert token not in text, f"{script.name} references network token {token!r}"
