"""Tests for catalog/hooks/action-restatement-guard.{sh,ps1} and _action_restatement.py.

The Stop hook blocks a final assistant message that asks the user to act AND points
back to earlier text, and asks the agent to rewrite it under a `## Action needed`
heading. Every behavioral test runs through both wrappers via the `run` fixture, so
the suite is also the .sh/.ps1 parity check.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_action_restatement_guard.py -q
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_SH = _HOOKS_DIR / "action-restatement-guard.sh"
_PS1 = _HOOKS_DIR / "action-restatement-guard.ps1"
_HIDE = {"creationflags": 0x08000000} if os.name == "nt" else {}  # CREATE_NO_WINDOW
_SWITCHES = ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "QWEN_PROJECT_DIR")

FAILING = 'Waiting on you: the 3 migration-approval steps from earlier. Reply "done" when step 3 prints approved.'
RESTATED = (
    "## Action needed\n\n"
    "1. On the staging host (SSH session), run `./migrate.sh --dry-run`. You should see: `plan ok`.\n"
    "2. Run `./migrate.sh --apply`. You should see: `applied 3 changes`.\n"
    '3. Run `./migrate.sh --status`. You should see: `approved`. Reply "done" when it does.\n'
)


@pytest.fixture(params=["sh", "ps1"])
def run(request, tmp_path: Path):
    if request.param == "sh":
        prefix = [request.getfixturevalue("bash_bin"), str(_SH)]
    else:
        prefix = [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_PS1),
        ]

    def _run(
        payload: str, env_extra: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess:
        env = {k: v for k, v in os.environ.items() if k not in _SWITCHES}
        env.update(HOME=str(tmp_path), USERPROFILE=str(tmp_path))
        env.update(env_extra or {})
        return subprocess.run(
            prefix,
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            timeout=120,
            **_HIDE,
        )

    return _run


def _transcript(tmp_path: Path, final_text: str, *, tail_user: bool = False) -> Path:
    entries = [
        {"type": "user", "message": {"role": "user", "content": "go"}},
        {
            "type": "assistant",
            "message": {
                "id": "m1",
                "content": [{"type": "text", "text": "earlier narrative"}],
            },
        },
        {"type": "user", "message": {"role": "user", "content": "continue"}},
        {
            "type": "assistant",
            "message": {
                "id": "m2",
                "content": [
                    {"type": "text", "text": final_text},
                ],
            },
        },
    ]
    if tail_user:
        entries.append({"type": "user", "message": {"role": "user", "content": "ok"}})
    path = tmp_path / "transcript.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    return path


def _stop(path: Path, **extra: object) -> str:
    return json.dumps({"session_id": "s", "transcript_path": str(path), **extra})


def _blocked(proc: subprocess.CompletedProcess) -> dict:
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["decision"] == "block"
    return data


def test_blocks_the_exact_failing_message(run, tmp_path: Path) -> None:
    data = _blocked(run(_stop(_transcript(tmp_path, FAILING))))
    assert data["reason"].startswith("[Nexus-Hub: action-restatement-guard] ")
    assert "## Action needed" in data["reason"]
    assert "from earlier" in data["reason"]


def test_reads_last_assistant_message_field_when_present(run) -> None:
    payload = json.dumps({"session_id": "s", "last_assistant_message": FAILING})
    _blocked(run(payload))


@pytest.mark.parametrize(
    "text",
    [
        "Please run the command as above and paste the output.",
        "Your turn: see above for the exact command.",
        "Choose A or B, listed above.",
        "A. Keep the branch\nB. Delete the branch\nSee my earlier message for the trade-offs.",
        "Run these, as before, and reply when you have the result.",
        "I posted earlier the steps; approve them when ready.",
    ],
)
def test_blocks_other_ask_plus_backreference_pairs(
    run, tmp_path: Path, text: str
) -> None:
    _blocked(run(_stop(_transcript(tmp_path, text))))


def test_allows_a_message_with_action_needed_and_full_steps(
    run, tmp_path: Path
) -> None:
    proc = run(_stop(_transcript(tmp_path, "Status: migration staged.\n\n" + RESTATED)))
    assert proc.returncode == 0 and proc.stdout == ""


def test_allows_a_message_with_no_user_action(run, tmp_path: Path) -> None:
    text = "Completed: the refactor from earlier is merged. Verified: tests pass. Next: nothing."
    proc = run(_stop(_transcript(tmp_path, text)))
    assert proc.returncode == 0 and proc.stdout == ""


def test_allows_an_ask_without_a_backreference(run, tmp_path: Path) -> None:
    proc = run(_stop(_transcript(tmp_path, "Reply with the branch name you want.")))
    assert proc.returncode == 0 and proc.stdout == ""


def test_narrative_backreference_above_the_heading_is_not_blocked(
    run, tmp_path: Path
) -> None:
    text = "As mentioned earlier, the build passed.\n\n" + RESTATED
    proc = run(_stop(_transcript(tmp_path, text)))
    assert proc.returncode == 0 and proc.stdout == ""


def test_backreference_inside_the_action_section_is_blocked(
    run, tmp_path: Path
) -> None:
    text = "## Action needed\n\n1. Run the steps I listed and reply when done.\n"
    _blocked(run(_stop(_transcript(tmp_path, text))))


def test_code_spans_and_fences_are_ignored(run, tmp_path: Path) -> None:
    text = "Reply when done. The guard looks for `from earlier` and:\n\n```text\nas above\n```\n"
    proc = run(_stop(_transcript(tmp_path, text)))
    assert proc.returncode == 0 and proc.stdout == ""


def test_stop_hook_active_exits_zero_silently(run, tmp_path: Path) -> None:
    proc = run(_stop(_transcript(tmp_path, FAILING), stop_hook_active=True))
    assert proc.returncode == 0 and proc.stdout == ""


@pytest.mark.parametrize(
    "payload", ["", "not json", "[1, 2]", "{}", '{"transcript_path": 5}']
)
def test_fails_open_on_bad_payloads(run, payload: str) -> None:
    proc = run(payload)
    assert proc.returncode == 0 and proc.stdout == ""


def test_fails_open_on_missing_transcript(run, tmp_path: Path) -> None:
    proc = run(_stop(tmp_path / "does-not-exist.jsonl"))
    assert proc.returncode == 0 and proc.stdout == ""


def test_non_claude_payload_is_ignored(run, tmp_path: Path) -> None:
    payload = json.dumps(
        {
            "transcript_path": str(_transcript(tmp_path, FAILING)),
            "cursor_version": "1.0",
        }
    )
    proc = run(payload)
    assert proc.returncode == 0 and proc.stdout == ""


@pytest.mark.parametrize(
    "env",
    [
        {"NEXUS_DISABLED_HOOKS": "action-restatement-guard"},
        {"NEXUS_HOOK_PROFILE": "minimal"},
    ],
)
def test_opt_outs_silence_the_hook(run, tmp_path: Path, env: dict[str, str]) -> None:
    proc = run(_stop(_transcript(tmp_path, FAILING)), env)
    assert proc.returncode == 0 and proc.stdout == ""


def test_only_the_last_assistant_message_counts(run, tmp_path: Path) -> None:
    """A back-reference in an older message must not block a clean final message."""
    entries = [
        {
            "type": "assistant",
            "message": {"id": "m1", "content": [{"type": "text", "text": FAILING}]},
        },
        {"type": "user", "message": {"role": "user", "content": "ok"}},
        {
            "type": "assistant",
            "message": {"id": "m2", "content": [{"type": "text", "text": RESTATED}]},
        },
    ]
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    proc = run(_stop(path))
    assert proc.returncode == 0 and proc.stdout == ""


def test_large_transcript_is_read_by_tail_only(run, tmp_path: Path) -> None:
    filler = json.dumps(
        {"type": "user", "message": {"role": "user", "content": "x" * 4000}}
    )
    final = {
        "type": "assistant",
        "message": {"id": "z", "content": [{"type": "text", "text": FAILING}]},
    }
    path = tmp_path / "big.jsonl"
    path.write_text(
        "\n".join([filler] * 600 + [json.dumps(final)]) + "\n", encoding="utf-8"
    )
    _blocked(run(_stop(path)))
