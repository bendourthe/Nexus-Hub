"""check-minor names the next action for idle members without changing its verdict (v4.15.6).

The verdict line, exit code and predicate lines stay exactly as before so existing parsers keep
working; `ACTION:` lines come last in text mode and as an `actions` list in JSON mode.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_plan_completion as ck  # noqa: E402
import completion_minor as cm  # noqa: E402

IDLE = [
    {
        "member": "v4.15.7",
        "kind": "needs-user",
        "detail": "blocked 90 min on coordinator-and-sensitive-deltas",
    },
    {
        "member": "v4.15.8",
        "kind": "unadmitted",
        "detail": "in the minor record with no worker lane",
    },
    {
        "member": "v4.15.9",
        "kind": "resumable",
        "detail": "v4.15.5 released; blocker is stale",
    },
]


def test_action_lines_name_dispatch_and_decision():
    assert cm.action_lines(IDLE) == [
        "ACTION: dispatch-required (v4.15.8, v4.15.9)",
        "ACTION: decision-required (v4.15.7: blocked 90 min on coordinator-and-sensitive-deltas)",
    ]
    assert cm.action_lines([]) == []


def test_checker_reuses_the_skill_classifier():
    module = cm._lane_health()
    assert module is not None
    assert Path(module.__file__).name == "lane_health.py"
    assert not hasattr(cm, "classify_idle")  # reused, never copied


def _run(monkeypatch, capsys, line, *, json_mode=False):
    verdict = cm.MinorVerdict(
        line,
        ck.EXIT_INCOMPLETE if line.startswith("INCOMPLETE") else ck.EXIT_COMPLETE,
        minor=[("record.minor", "met")],
        record={"minor": "v4.15"},
    )
    monkeypatch.setattr(
        cm,
        "minor_context",
        lambda _ck, _repo: argparse.Namespace(notices=[], _git_out=lambda *a: "abc"),
    )
    monkeypatch.setattr(cm, "check_minor", lambda *_a: verdict)
    monkeypatch.setattr(cm, "idle_actions", lambda *_a: cm.action_lines(IDLE))
    args = argparse.Namespace(
        detail=False, repo=".", minor="v4.15", session=None, json=json_mode
    )
    code = cm.cmd_check_minor(ck, args)
    return code, capsys.readouterr().out.splitlines()


def test_incomplete_text_output_keeps_verdict_and_appends_actions(monkeypatch, capsys):
    code, lines = _run(monkeypatch, capsys, "INCOMPLETE: member.v4.15.6")
    assert code == ck.EXIT_INCOMPLETE
    assert lines[0] == "INCOMPLETE: member.v4.15.6"
    assert lines[1] == "record.minor met"
    assert lines[2:] == cm.action_lines(IDLE)


def test_json_output_carries_actions_without_extra_lines(monkeypatch, capsys):
    code, lines = _run(
        monkeypatch, capsys, "INCOMPLETE: member.v4.15.6", json_mode=True
    )
    assert code == ck.EXIT_INCOMPLETE and len(lines) == 2
    assert json.loads(lines[1])["actions"] == cm.action_lines(IDLE)


@pytest.mark.parametrize("line", ["MINOR COMPLETE", "BLOCKED: approval-not-covered"])
def test_no_action_lines_unless_incomplete(monkeypatch, capsys, line):
    _code, lines = _run(monkeypatch, capsys, line)
    assert not any(text.startswith("ACTION:") for text in lines)
