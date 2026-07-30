"""Tests for catalog/hooks/provenance-ledger.{sh,ps1} (v3.15.6 AC3).

The hook records which paths the agent wrote (timestamp, content hash, path) and
flags a later command in the same session that references one of them.

The load-bearing assertions here are the NEGATIVE ones. The redaction discipline
is the whole reason this ledger is acceptable to ship, so the tests prove that
file contents never reach it, that correlation cannot cross a session boundary,
and that the hook stays advisory (exit 0) on every path including malformed input.

Every test runs against BOTH implementations via the `run` fixture, so the suite
is also the .sh/.ps1 parity check.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_provenance_ledger.py -v
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "provenance-ledger.sh"
_HOOK_PS1 = _HOOKS_DIR / "provenance-ledger.ps1"

_SEAM_MARKER = "TRUST SEAM"
_SECRET = "hunter2-do-not-log-this-value"


@pytest.fixture(params=["sh", "ps1"])
def run(request, tmp_path: Path):
    """Invoke either implementation with an isolated ledger directory."""
    if request.param == "sh":
        prefix = [request.getfixturevalue("bash_bin"), str(_HOOK_SH)]
    else:
        prefix = [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_HOOK_PS1),
        ]

    ledger_dir = tmp_path / "ledger"

    def _run(
        payload: dict | str, env_extra: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess:
        body = payload if isinstance(payload, str) else json.dumps(payload)
        env = {**os.environ, "NEXUS_PROVENANCE_DIR": str(ledger_dir)}
        for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"):
            env.pop(key, None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            prefix, input=body, text=True, capture_output=True, env=env, timeout=120
        )

    _run.ledger_dir = ledger_dir  # type: ignore[attr-defined]
    return _run


def _write_payload(path: str, session: str = "S1") -> dict:
    return {
        "session_id": session,
        "tool_name": "Write",
        "tool_input": {"file_path": path},
    }


def _bash_payload(command: str, session: str = "S1") -> dict:
    return {
        "session_id": session,
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def _ledger_text(run, session: str = "S1") -> str:
    f = run.ledger_dir / f"{session}.tsv"
    return f.read_text(encoding="utf-8") if f.exists() else ""


# --- Recording ---------------------------------------------------------------


def test_write_is_recorded_with_path_and_hash(run, tmp_path: Path) -> None:
    target = tmp_path / "script.sh"
    target.write_text("echo hello\n", encoding="utf-8")

    proc = run(_write_payload(str(target)))
    assert proc.returncode == 0

    line = _ledger_text(run).strip()
    fields = line.split("\t")
    assert len(fields) == 3, f"expected timestamp/hash/path, got {line!r}"
    assert fields[0].isdigit(), "first field must be an epoch timestamp"
    assert len(fields[1]) == 64, "second field must be a sha256 hex digest"
    assert "script.sh" in fields[2]


def test_hash_is_stable_and_changes_with_content(run, tmp_path: Path) -> None:
    target = tmp_path / "a.sh"
    target.write_text("one\n", encoding="utf-8")
    run(_write_payload(str(target)))
    target.write_text("two\n", encoding="utf-8")
    run(_write_payload(str(target)))

    hashes = [ln.split("\t")[1] for ln in _ledger_text(run).strip().splitlines()]
    assert len(hashes) == 2
    assert hashes[0] != hashes[1], "hash did not change when content changed"


def test_missing_file_records_a_sentinel_not_a_crash(run, tmp_path: Path) -> None:
    proc = run(_write_payload(str(tmp_path / "never-created.sh")))
    assert proc.returncode == 0
    assert "NOFILE" in _ledger_text(run)


# --- Redaction discipline (the reason this is shippable) ---------------------


def test_file_contents_never_reach_the_ledger(run, tmp_path: Path) -> None:
    """The ledger holds paths and hashes only, never bytes."""
    target = tmp_path / "config.env"
    target.write_text(f"API_TOKEN={_SECRET}\n", encoding="utf-8")

    run(_write_payload(str(target)))
    ledger = _ledger_text(run)

    assert _SECRET not in ledger, "SECRET LEAKED into the provenance ledger"
    assert "API_TOKEN" not in ledger, "file content leaked into the provenance ledger"
    assert "config.env" in ledger, "the path itself should still be recorded"


def test_hook_output_never_echoes_file_contents(run, tmp_path: Path) -> None:
    target = tmp_path / "secret.sh"
    target.write_text(f"export TOKEN={_SECRET}\n", encoding="utf-8")

    proc = run(_write_payload(str(target)))
    assert _SECRET not in proc.stdout
    assert _SECRET not in proc.stderr


def test_only_a_hash_prefix_is_surfaced_in_the_advisory(run, tmp_path: Path) -> None:
    """The advisory shows a short hash prefix, not the file and not the full digest
    in a form that invites treating it as content."""
    target = tmp_path / "runme.sh"
    target.write_text("echo hi\n", encoding="utf-8")
    run(_write_payload(str(target)))

    proc = run(_bash_payload(f"bash {target}"))
    assert _SEAM_MARKER in proc.stderr
    assert "echo hi" not in proc.stderr


# --- Correlation -------------------------------------------------------------


def test_command_referencing_a_written_path_is_flagged(run, tmp_path: Path) -> None:
    target = tmp_path / "payload.sh"
    target.write_text("echo x\n", encoding="utf-8")
    run(_write_payload(str(target)))

    proc = run(_bash_payload(f"bash {target}"))
    assert proc.returncode == 0, "the hook must stay advisory"
    assert _SEAM_MARKER in proc.stderr
    assert "payload.sh" in proc.stderr


def test_command_matching_only_the_basename_is_flagged(run, tmp_path: Path) -> None:
    """A relative invocation still correlates."""
    target = tmp_path / "deployer.sh"
    target.write_text("echo x\n", encoding="utf-8")
    run(_write_payload(str(target)))

    assert _SEAM_MARKER in run(_bash_payload("./deployer.sh --now")).stderr


def test_unrelated_command_is_silent(run, tmp_path: Path) -> None:
    target = tmp_path / "thing.sh"
    target.write_text("echo x\n", encoding="utf-8")
    run(_write_payload(str(target)))

    proc = run(_bash_payload("git status"))
    assert proc.returncode == 0
    assert _SEAM_MARKER not in proc.stderr


def test_correlation_does_not_cross_sessions(run, tmp_path: Path) -> None:
    """Correlation is capped to the current session by design."""
    target = tmp_path / "cross.sh"
    target.write_text("echo x\n", encoding="utf-8")
    run(_write_payload(str(target), session="S1"))

    proc = run(_bash_payload(f"bash {target}", session="S2"))
    assert _SEAM_MARKER not in proc.stderr, "ledger correlated across sessions"


def test_command_before_any_write_is_silent(run) -> None:
    """No ledger yet must not error."""
    proc = run(_bash_payload("bash anything.sh"))
    assert proc.returncode == 0
    assert _SEAM_MARKER not in proc.stderr


def test_short_basenames_do_not_cause_false_positives(run, tmp_path: Path) -> None:
    """A 1-3 character basename collides with ordinary words, so it is ignored."""
    target = tmp_path / "a.s"
    target.write_text("x\n", encoding="utf-8")
    run(_write_payload(str(target)))

    proc = run(_bash_payload("echo 'this has a.s inside it somewhere'"))
    assert _SEAM_MARKER not in proc.stderr


# --- Bounding and runtime controls ------------------------------------------


def test_ledger_is_capped(run, tmp_path: Path) -> None:
    target = tmp_path / "loop.sh"
    target.write_text("x\n", encoding="utf-8")
    for _ in range(8):
        run(_write_payload(str(target)), {"NEXUS_PROVENANCE_MAX": "5"})

    lines = [ln for ln in _ledger_text(run).splitlines() if ln.strip()]
    assert len(lines) <= 5, f"ledger grew past the cap: {len(lines)} lines"


def test_large_file_hashing_is_skipped(run, tmp_path: Path) -> None:
    """Per-write overhead is bounded: above the size cap the hash is skipped."""
    target = tmp_path / "big.bin"
    target.write_bytes(b"0" * 4096)
    run(_write_payload(str(target)), {"NEXUS_PROVENANCE_HASH_MAX_BYTES": "100"})
    assert "SKIPPED-LARGE" in _ledger_text(run)


@pytest.mark.parametrize(
    "env_extra",
    [
        {"NEXUS_DISABLED_HOOKS": "provenance-ledger"},
        {"NEXUS_HOOK_PROFILE": "minimal"},
    ],
)
def test_runtime_controls_disable_the_hook(
    run, tmp_path: Path, env_extra: dict[str, str]
) -> None:
    target = tmp_path / "off.sh"
    target.write_text("x\n", encoding="utf-8")
    proc = run(_write_payload(str(target)), env_extra)
    assert proc.returncode == 0
    assert _ledger_text(run) == "", "hook wrote a ledger while disabled"


# --- Advisory-only contract -------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    ["", "not json at all", "{}", '{"tool_input":{}}', '{"tool_name":"Bash"}'],
)
def test_unusable_payload_exits_zero_quietly(run, payload: str) -> None:
    proc = run(payload)
    assert proc.returncode == 0
    assert _SEAM_MARKER not in proc.stderr


def test_hook_never_blocks_even_when_it_flags(run, tmp_path: Path) -> None:
    """PostToolUse runs after the fact, and this hook is advisory: exit 0 always."""
    target = tmp_path / "flagged.sh"
    target.write_text("x\n", encoding="utf-8")
    run(_write_payload(str(target)))
    proc = run(_bash_payload(f"bash {target}"))
    assert proc.returncode == 0
