"""Tests for the eval-loop behavioral-eval schema converter (scripts/skill_eval_convert.py).

The converter maps the eval-loop's internal evals.json (a bare list of rich
entries) to and from the interoperable behavioral-eval schema
`{skill_name, evals: [{id, prompt, expected_output, expectations[]}]}`. The core
guarantee is a LOSSLESS round-trip in both directions, so grading (which reads the
internal format, unchanged by this phase) is byte-for-byte preserved through an
export/import cycle. Tests import the module by file location (it lives under
scripts/, not on the default path) and add end-to-end CLI subprocess tests.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONVERTER = REPO_ROOT / "scripts" / "skill_eval_convert.py"


def _load():
    spec = importlib.util.spec_from_file_location("skill_eval_convert", CONVERTER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


conv = _load()


# A rich internal set exercising every internal-only field the interop schema
# cannot express, plus a minimal entry and an assertion with a non-`text` key.
_INTERNAL = [
    {"id": "eval-001", "query": "do the thing", "should_trigger": True,
     "assertions": [{"text": "a"}, {"text": "b"}], "tags": ["happy-path"]},
    {"id": "eval-002", "query": "skip this", "should_trigger": False,
     "assertions": [{"text": "c"}]},
    {"id": "eval-003", "query": "multi-turn", "should_trigger": True,
     "assertions": [{"text": "d", "weight": 2}], "turns": ["t1", "t2"],
     "trigger_turn": 2, "model": "haiku"},
]

# A foreign interoperable set (no x_nexus), one with a golden output, one without.
_FOREIGN = {
    "skill_name": "ext-skill",
    "evals": [
        {"id": "e1", "prompt": "p1", "expected_output": "golden", "expectations": ["x", "y"]},
        {"id": "e2", "prompt": "p2", "expected_output": "", "expectations": ["z"]},
    ],
}


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------

def test_query_maps_to_prompt_and_assertions_to_expectations() -> None:
    interop = conv.internal_to_interop(_INTERNAL, "my-skill")
    first = interop["evals"][0]
    assert first["prompt"] == "do the thing"
    assert first["expectations"] == ["a", "b"]
    assert interop["skill_name"] == "my-skill"


def test_internal_only_fields_ride_in_extension_namespace() -> None:
    interop = conv.internal_to_interop(_INTERNAL, "my-skill")
    ext = interop["evals"][0][conv.NEXUS_EXT_KEY]
    assert ext["should_trigger"] is True
    assert ext["tags"] == ["happy-path"]
    # eval-002 carries should_trigger:False (an internal-only field), so it too
    # gets an extension key.
    assert interop["evals"][1][conv.NEXUS_EXT_KEY]["should_trigger"] is False
    # A truly minimal entry (only id/query/assertions) carries NO extension key.
    minimal = conv.internal_to_interop([{"id": "m", "query": "q", "assertions": [{"text": "t"}]}])
    assert conv.NEXUS_EXT_KEY not in minimal["evals"][0]


def test_assertion_extra_keys_are_preserved_in_extension() -> None:
    interop = conv.internal_to_interop(_INTERNAL, "my-skill")
    # eval-003's assertion has a `weight` key beyond `text`, so the full
    # assertion objects are stashed for lossless reconstruction.
    assert interop["evals"][2][conv.NEXUS_EXT_KEY]["assertions"] == [{"text": "d", "weight": 2}]


# ---------------------------------------------------------------------------
# Lossless round-trips (the core guarantee)
# ---------------------------------------------------------------------------

def test_internal_round_trip_is_lossless() -> None:
    skill_name, back = conv.interop_to_internal(conv.internal_to_interop(_INTERNAL, "my-skill"))
    assert back == _INTERNAL
    assert skill_name == "my-skill"


def test_interop_round_trip_is_lossless() -> None:
    skill_name, internal = conv.interop_to_internal(_FOREIGN)
    assert conv.internal_to_interop(internal, skill_name) == _FOREIGN


def test_interop_round_trip_lossless_with_extension_present() -> None:
    # An interop file that already carries x_nexus (e.g. one we exported and shared)
    # must survive interop -> internal -> interop unchanged.
    exported = conv.internal_to_interop(_INTERNAL, "my-skill")
    skill_name, internal = conv.interop_to_internal(exported)
    assert conv.internal_to_interop(internal, skill_name) == exported


def test_expected_output_preserved_only_when_present() -> None:
    _, internal = conv.interop_to_internal(_FOREIGN)
    assert internal[0].get("expected_output") == "golden"   # non-empty -> kept
    assert "expected_output" not in internal[1]              # empty -> not added


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_internal_to_interop_rejects_non_list() -> None:
    try:
        conv.internal_to_interop({"not": "a list"}, "s")
    except ValueError as exc:
        assert "list" in str(exc)
    else:
        raise AssertionError("expected ValueError for a non-list internal input")


def test_interop_to_internal_rejects_missing_evals() -> None:
    try:
        conv.interop_to_internal({"skill_name": "s"})
    except ValueError as exc:
        assert "evals" in str(exc)
    else:
        raise AssertionError("expected ValueError for a missing 'evals' array")


# ---------------------------------------------------------------------------
# End-to-end CLI surface
# ---------------------------------------------------------------------------

def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CONVERTER), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def test_cli_to_interop_then_to_internal_round_trips(tmp_path: Path) -> None:
    internal_file = tmp_path / "evals.json"
    internal_file.write_text(json.dumps(_INTERNAL), encoding="utf-8")
    interop_file = tmp_path / "interop.json"
    back_file = tmp_path / "back.json"

    r1 = _run_cli("--to-interop", str(internal_file), "--skill-name", "my-skill", "-o", str(interop_file))
    assert r1.returncode == 0, r1.stderr
    interop = json.loads(interop_file.read_text(encoding="utf-8"))
    assert interop["skill_name"] == "my-skill"
    assert interop["evals"][0]["prompt"] == "do the thing"

    r2 = _run_cli("--to-internal", str(interop_file), "-o", str(back_file))
    assert r2.returncode == 0, r2.stderr
    assert json.loads(back_file.read_text(encoding="utf-8")) == _INTERNAL


def test_cli_to_interop_stdout(tmp_path: Path) -> None:
    internal_file = tmp_path / "evals.json"
    internal_file.write_text(json.dumps(_INTERNAL), encoding="utf-8")
    result = _run_cli("--to-interop", str(internal_file))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["evals"][0]["prompt"] == "do the thing"


def test_cli_rejects_malformed_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    result = _run_cli("--to-interop", str(bad))
    assert result.returncode == 1
    assert "not valid JSON" in result.stderr


def test_cli_requires_a_direction() -> None:
    # argparse mutually-exclusive group is required -> exit 2 with no direction.
    result = _run_cli()
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# In-process main() surface (fast; covers argparse + I/O branches directly)
# ---------------------------------------------------------------------------

import pytest  # noqa: E402  (kept local to the in-process main() section)


def _main(monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    monkeypatch.setattr(sys, "argv", ["skill_eval_convert.py", *argv])
    return conv.main()


def test_main_to_interop_writes_file(tmp_path, monkeypatch, capsys) -> None:
    internal_file = tmp_path / "evals.json"
    internal_file.write_text(json.dumps(_INTERNAL), encoding="utf-8")
    out = tmp_path / "interop.json"
    rc = _main(monkeypatch, "--to-interop", str(internal_file), "--skill-name", "s", "-o", str(out))
    capsys.readouterr()
    assert rc == 0
    assert json.loads(out.read_text(encoding="utf-8"))["skill_name"] == "s"


def test_main_to_internal_prints_skill_name(tmp_path, monkeypatch, capsys) -> None:
    interop_file = tmp_path / "interop.json"
    interop_file.write_text(json.dumps(_FOREIGN), encoding="utf-8")
    rc = _main(monkeypatch, "--to-internal", str(interop_file))
    captured = capsys.readouterr()
    assert rc == 0
    assert "skill_name: ext-skill" in captured.err
    assert json.loads(captured.out)[0]["query"] == "p1"


def test_main_to_interop_stdout(tmp_path, monkeypatch, capsys) -> None:
    internal_file = tmp_path / "evals.json"
    internal_file.write_text(json.dumps(_INTERNAL), encoding="utf-8")
    rc = _main(monkeypatch, "--to-interop", str(internal_file))
    out = capsys.readouterr().out
    assert rc == 0
    assert json.loads(out)["evals"][0]["prompt"] == "do the thing"


def test_main_malformed_json_returns_one(tmp_path, monkeypatch, capsys) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    rc = _main(monkeypatch, "--to-interop", str(bad))
    err = capsys.readouterr().err
    assert rc == 1
    assert "not valid JSON" in err


def test_main_shape_error_returns_one(tmp_path, monkeypatch, capsys) -> None:
    # A valid-JSON but wrong-shape internal file (a dict, not a list) -> exit 1.
    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"not": "a list"}), encoding="utf-8")
    rc = _main(monkeypatch, "--to-interop", str(wrong))
    err = capsys.readouterr().err
    assert rc == 1
    assert "list" in err
