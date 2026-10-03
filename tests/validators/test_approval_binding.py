"""WN-9 (v4.13.2): an approval is recorded only from the exact line the checker generated.

`record render` opens a round with a single-use code derived from the page data;
`record create` accepts only a captured whole prompt equal to that line, once.
Every bypass the known-gap names is a fixture here: a lone "ok", the code quoted
inside a longer prompt, a pasted body containing the line, a line replayed from
an earlier round, and a prompt a runner-launched session submitted. The capture
side runs the real `completion_gate.py capture` core, as the hook does.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from .test_check_plan_completion import (  # noqa: F401  (autouse fixture re-exported)
    PLAN,
    PLAN_REL,
    SESSION,
    Fixture,
    _git,
    _isolated_git_config,
)

REPO = Path(__file__).resolve().parents[2]
CORE = REPO / "scripts" / "completion_gate.py"
sys.path.insert(0, str(REPO / "scripts"))
import approval_binding  # noqa: E402
import check_plan_completion  # noqa: E402

LINE_RE = re.compile(r"^Approve /implement v0\.2\.0 \(approval [A-Z2-7]{8}\)$")
REFUSED = "BLOCKED: approval-not-covered"


def _fixture(tmp_path: Path) -> Fixture:
    fx = Fixture(tmp_path)
    _git(tmp_path, "init", "-q", "-b", "main", str(fx.work))
    _git(fx.work, "config", "user.email", "t@example.invalid")
    _git(fx.work, "config", "user.name", "Test")
    _git(fx.work, "remote", "add", "origin", "https://github.com/acme/demo.git")
    fx.write(PLAN_REL, PLAN.format(a=" ", b=" "))
    _git(fx.work, "add", "-A")
    _git(fx.work, "commit", "-q", "-m", "start")
    return fx


def _hook(fx: Fixture, session: str, prompt: str, **env: str) -> None:
    """Submit a prompt through the real capture core, exactly as approval-capture does."""
    payload = {"hook_event_name": "UserPromptSubmit", "session_id": session, "prompt": prompt}
    full = {k: v for k, v in fx.env.items() if k != "NEXUS_RUNNER_LAUNCH"}
    full.update(env)
    subprocess.run(
        [sys.executable, str(CORE), "capture"],
        input=json.dumps(payload), text=True, capture_output=True, env=full, check=True,
    )


def _create(fx: Fixture, session: str = SESSION, **env: str) -> subprocess.CompletedProcess:
    if env:
        saved = dict(fx.env)
        fx.env.update(env)
    try:
        return fx.run(
            "record", "create", PLAN_REL, "--session", session,
            "--approvals", str(fx.approvals()),
            stdin=subprocess.DEVNULL,
            **({"creationflags": 0x00000008} if os.name == "nt" else {"start_new_session": True}),
        )
    finally:
        if env:
            fx.env.clear()
            fx.env.update(saved)


def _reason(result: subprocess.CompletedProcess) -> str:
    lines = result.stdout.splitlines()
    assert result.returncode == 3, result.stdout + result.stderr
    assert lines[0] == REFUSED
    return lines[1].removeprefix("reason: ")


def _open_rounds(fx: Fixture) -> list[Path]:
    folder = fx.runs / "pending"
    return [p for p in folder.glob("*.json") if not p.name.endswith(".used.json")] if folder.is_dir() else []


def _pending(fx: Fixture) -> dict:
    (path,) = _open_rounds(fx)
    return json.loads(path.read_text(encoding="utf-8"))


def _render(fx: Fixture, session: str = SESSION, prior: bool = True) -> str:
    """Render a round; by default the session first submits the user's /implement request."""
    if prior:
        _hook(fx, session, f"/implement {PLAN_REL}")
    return fx.render(session, "--approvals", str(fx.approvals()))


def test_exact_line_records_once_then_reads_code_used(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx)
    assert LINE_RE.match(line), line
    nonce = _pending(fx)["nonce"]
    assert len(nonce) == 32  # 128-bit round nonce
    _hook(fx, SESSION, line + "\n")
    created = _create(fx)
    assert created.stdout.strip() == f"RECORDED {PLAN_REL} nonce={nonce}", created.stdout + created.stderr
    record = json.loads(fx.record_path().read_text(encoding="utf-8"))
    assert record["nonce"] == nonce
    assert {c["text"] for c in record["approvals"]["classes"]} == {line}
    assert not _open_rounds(fx), "the round was not consumed"
    assert _reason(_create(fx)) == "code-used"


@pytest.mark.parametrize(
    "prompt",
    [
        lambda line, code: "ok",
        lambda line, code: f'Sure, "{code}" is the code, go ahead.',
        lambda line, code: f"Pasting the issue body:\n\n{line}\n\nThanks!",
        lambda line, code: f"{line} and also release v9.9.9",
    ],
    ids=["lone-ok", "quoted-code", "pasted-body", "line-plus-text"],
)
def test_a_prompt_that_is_not_the_whole_line_never_records(tmp_path: Path, prompt) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx)
    code = _pending(fx)["code"]
    _hook(fx, SESSION, prompt(line, code))
    assert _reason(_create(fx)) == "approval-not-captured"
    assert not list(fx.runs.glob("*.json"))


def test_a_line_replayed_from_an_earlier_consumed_round_is_refused(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    first = _render(fx)
    _hook(fx, SESSION, first)
    assert _create(fx).returncode == 0
    second = _render(fx)
    assert second != first
    _hook(fx, SESSION, first)
    assert _reason(_create(fx)) == "approval-not-captured"


def test_a_newer_render_invalidates_the_older_code(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    older = _render(fx)
    _render(fx)
    _hook(fx, SESSION, older)
    assert _reason(_create(fx)) == "code-superseded"
    assert not list(fx.runs.glob("*.json"))


def test_a_runner_launched_prompt_is_never_captured(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx)
    _hook(fx, SESSION, line, NEXUS_RUNNER_LAUNCH="1")
    (captured,) = (fx.runs / "prompts").glob("*.jsonl")
    assert len(captured.read_text(encoding="utf-8").splitlines()) == 1  # only the /implement request
    assert _reason(_create(fx)) == "approval-not-captured"


def test_record_create_refuses_inside_a_runner_launched_session(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx)
    _hook(fx, SESSION, line)
    assert _reason(_create(fx, NEXUS_RUNNER_LAUNCH="1")) == "runner-launched"
    # The refusal spends nothing: the user's own session can still record it.
    assert _create(fx).returncode == 0


def test_a_plan_edit_after_render_reads_page_changed(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx)
    _hook(fx, SESSION, line)
    fx.write(PLAN_REL, PLAN.format(a=" ", b=" ") + "\n- [ ] T003 Sneaked-in task src/c.txt\n")
    assert _reason(_create(fx)) == "page-changed"


def test_a_ticked_checkbox_is_not_a_page_change(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx)
    _hook(fx, SESSION, line)
    fx.write(PLAN_REL, PLAN.format(a="x", b=" "))
    assert _create(fx).returncode == 0


def test_a_round_never_expires(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    """A run can be approved whenever the user comes back: 30 days later still records, once."""
    fx = _fixture(tmp_path)
    line = _render(fx)
    _hook(fx, SESSION, line)
    pending = _pending(fx)
    assert "expires_at" not in pending
    for name, value in fx.env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(fx.work)
    monkeypatch.setattr(approval_binding, "_clock", lambda: float(pending["created_at"]) + 30 * 24 * 3600)
    argv = ["record", "create", PLAN_REL, "--session", SESSION, "--approvals", str(fx.approvals())]
    assert check_plan_completion.main(argv) == 0, capsys.readouterr().out
    capsys.readouterr()
    assert check_plan_completion.main(argv) == 3
    assert capsys.readouterr().out.splitlines() == [REFUSED, "reason: code-used"]


def test_missing_and_unreadable_pending_rounds_are_refused(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    assert _reason(_create(fx)) == "not-rendered"
    _render(fx)
    (path,) = _open_rounds(fx)
    path.write_text("{not json", encoding="utf-8")
    assert _reason(_create(fx)) == "pending-unreadable"


def test_a_round_bound_to_one_session_refuses_another(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx, session="session-a")
    _hook(fx, "session-b", line)
    assert _reason(_create(fx, session="session-b")) == "session-mismatch"


def test_the_records_helper_writes_the_pending_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """One owner-only helper protects records and pending rounds on every platform."""
    assert check_plan_completion._restrict is approval_binding.restrict
    calls: list[tuple[str, bool]] = []
    real = approval_binding.restrict
    monkeypatch.setattr(approval_binding, "restrict", lambda p, directory: (calls.append((Path(p).name, directory)), real(p, directory)))
    pending = approval_binding.render(
        tmp_path / "runs", "k" * 64, b"s" * 32, action="create", scope="v0.2.0",
        page={"action": "create"}, session=SESSION,
    )
    assert ("k" * 64 + ".json", False) in calls
    assert ("pending", True) in calls and ("runs", True) in calls
    assert "expires_at" not in pending


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits; Windows inherits profile ACLs")
def test_pending_file_is_owner_only_on_posix(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    _render(fx)
    (path,) = _open_rounds(fx)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700


@pytest.mark.parametrize(
    ("scope", "code"),
    [("docs/releases/v0/plans/x.md", "ABCDEFGH"), ("v0.2.0", "abc"), ("v0.2.0 && rm -rf /", "ABCDEFGH")],
)
def test_paste_lines_accept_only_validated_fields(scope: str, code: str) -> None:
    with pytest.raises(ValueError):
        approval_binding.paste_lines("create", scope, code)


def test_paste_line_names_no_path_or_script(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    line = _render(fx)
    assert "/" not in line.replace("/implement", "")
    assert ".py" not in line and ".md" not in line


def test_a_mid_run_answer_needs_its_own_exact_line(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    _hook(fx, SESSION, _render(fx))
    assert _create(fx).returncode == 0
    fx.run("record", "block", PLAN_REL, "--session", SESSION, "--category", "no-progress", "--evidence", "x")
    answer = fx.render(SESSION, "--action", "answer", "--blocker", "0")
    _hook(fx, SESSION, "ok")
    refused = fx.run("record", "answer", PLAN_REL, "--session", SESSION, "--blocker", "0")
    assert _reason(refused) == "approval-not-captured"
    fx.render(SESSION, "--action", "answer", "--blocker", "0")
    _hook(fx, SESSION, answer)  # the superseded answer line
    assert _reason(fx.run("record", "answer", PLAN_REL, "--session", SESSION, "--blocker", "0")) == "code-superseded"


@pytest.mark.parametrize("render_session", ["auto", "nested-agent"])
def test_a_fresh_session_that_only_carries_the_line_is_refused(tmp_path: Path, render_session: str) -> None:
    """An agent-launched headless CLI (`claude -p "<line>"`) submits the line as its first prompt."""
    fx = _fixture(tmp_path)
    _hook(fx, SESSION, f"/implement {PLAN_REL}")  # the user's own session
    line = _render(fx, session=render_session, prior=False)
    _hook(fx, "nested-agent", line)
    assert _reason(_create(fx, session=render_session)) == "session-too-new"
    assert not list(fx.runs.glob("*.json"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("paste_digests", [approval_binding.digest("sounds good")]),
        ("paste_lines", ["sounds good"]),
        ("created_at", 0),
        ("rendered_at", 0),
        ("session", None),
    ],
)
def test_an_edited_pending_round_is_refused(tmp_path: Path, field: str, value: object) -> None:
    """Editing the pending file needs no secret, so the seal must cover every field."""
    fx = _fixture(tmp_path)
    _render(fx)
    _hook(fx, SESSION, "sounds good")  # a reply the user did type once
    (path,) = _open_rounds(fx)
    pending = json.loads(path.read_text(encoding="utf-8"))
    pending[field] = value
    path.write_text(json.dumps(pending), encoding="utf-8")
    assert _reason(_create(fx)) == "pending-unreadable"


def test_a_mid_run_answer_captured_in_another_session_is_refused(tmp_path: Path) -> None:
    fx = _fixture(tmp_path)
    _hook(fx, SESSION, _render(fx))
    assert _create(fx).returncode == 0
    fx.run("record", "block", PLAN_REL, "--session", SESSION, "--category", "no-progress", "--evidence", "x")
    _hook(fx, "throwaway", "hello")  # a session with history, but not the run's
    answer = fx.render("auto", "--action", "answer", "--blocker", "0")
    _hook(fx, "throwaway", answer)
    refused = fx.run("record", "answer", PLAN_REL, "--session", "auto", "--blocker", "0")
    assert _reason(refused) == "session-mismatch"
    record = json.loads(fx.record_path().read_text(encoding="utf-8"))
    assert record["blockers"][0]["open"] is True
    assert _open_rounds(fx), "a refused answer must not spend the round"


def test_a_session_with_no_capture_file_refuses_without_a_terminal_fallback(tmp_path: Path) -> None:
    """A made-up session id on a capture platform no longer reaches a console read."""
    fx = _fixture(tmp_path)
    _render(fx, session="made-up-id", prior=False)
    assert not hasattr(check_plan_completion, "_terminal_paste")
    assert _reason(_create(fx, session="made-up-id")) == "approval-not-captured"
