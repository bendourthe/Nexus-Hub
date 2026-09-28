"""Tests for the rendered-context measurement script (v4.13.3 Phase 3.3)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import measure_rendered_context as mrc
from scripts.check_memory_integration_budget import estimate_tokens

START, END = "<!-- NEXUS_HUB_START -->", "<!-- NEXUS_HUB_END -->"
INDEX = (REPO_ROOT / "data" / "SKILL_INDEX.md").read_text(encoding="utf-8")
TOTAL = next(line for line in INDEX.splitlines() if line.startswith("**Total:"))


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, dict, str]:
    code = mrc.main([*argv, "--json"])
    out = capsys.readouterr()
    return code, json.loads(out.out), out.err


def _file(tmp_path: Path, text: str, name: str = "CLAUDE.md") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_json_shape_and_estimator(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    text = f"# Mine\n\nHello there.\n\n{START}\n## Tech Stack\nbody\n{END}\n"
    code, report, _ = _run(capsys, "--path", str(_file(tmp_path, text)))
    assert code == 0
    assert report["estimator"].startswith("estimated")
    target = report["targets"][0]
    assert set(target) == {"path", "status", "tokens", "words", "sections", "duplicate_headings",
                           "skill_index_rows", "skill_index_totals", "legacy"}
    assert target["tokens"] == estimate_tokens(text)
    assert [s["heading"] for s in target["sections"]] == ["Mine", "Tech Stack"]
    assert set(target["sections"][0]) == {"heading", "level", "line", "tokens", "words"}
    assert set(target["legacy"]) == {"status", "spans", "kept_lines"}


def test_headings_inside_code_fences_are_not_sections(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    text = "# Real\n```\n# not a heading\n## nor this\n```\n## Also real\n## Also real\n"
    _, report, _ = _run(capsys, "--path", str(_file(tmp_path, text)))
    target = report["targets"][0]
    assert [s["heading"] for s in target["sections"]] == ["Real", "Also real", "Also real"]
    assert target["duplicate_headings"] == ["Also real"]


def test_only_missing_targets_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, report, err = _run(capsys, "--path", str(tmp_path / "nope.md"))
    assert code == 2
    assert report["targets"][0]["status"] == "missing"
    assert "no such file" in err


def test_non_utf8_target_is_unreadable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"\xff\xfe\x00junk")
    code, report, err = _run(capsys, "--path", str(bad))
    assert (code, report["targets"][0]["status"]) == (2, "unreadable")
    assert "not UTF-8" in err


def test_one_readable_target_is_enough(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, report, err = _run(capsys, "--path", str(tmp_path / "nope.md"), "--path", str(_file(tmp_path, "# a\n")))
    assert code == 0
    assert [t["status"] for t in report["targets"]] == ["missing", "ok"]
    assert "nope.md" in err


def test_check_passes_on_a_clean_managed_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _file(tmp_path, f"# Mine\n{START}\n{INDEX}\n{END}\n")
    code, report, _ = _run(capsys, "--path", str(path), "--check")
    assert code == 0
    assert report["targets"][0]["skill_index_totals"] == 1
    assert report["targets"][0]["skill_index_rows"] > 300


def test_check_fails_on_a_legacy_span(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _file(tmp_path, f"# Mine\n{INDEX}\n{START}\nmanaged\n{END}\n")
    code, report, _ = _run(capsys, "--path", str(path), "--check")
    legacy = report["targets"][0]["legacy"]
    assert code == 1
    assert len(legacy["spans"]) == 1
    assert legacy["spans"][0]["tokens"] > 0
    assert legacy["kept_lines"] == 1


def test_check_fails_on_two_total_lines(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _file(tmp_path, f"{START}\n{TOTAL}\nx\n{TOTAL}\n{END}\n")
    code, report, _ = _run(capsys, "--path", str(path), "--check")
    assert (code, report["targets"][0]["skill_index_totals"], report["targets"][0]["legacy"]["spans"]) == (1, 2, [])


def test_without_check_findings_exit_0(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = _file(tmp_path, f"{INDEX}\n{START}\n{END}\n")
    assert _run(capsys, "--path", str(path))[0] == 0


def test_redact_hides_home_and_user_headings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(mrc.Path, "home", classmethod(lambda cls: tmp_path))
    path = _file(tmp_path, "## My Private Notes\nsecret-ish\n## Tech Stack\n- x\n## Another Mine\n")
    for flag in ("--json", None):
        argv = ["--path", str(path), "--redact"] + ([flag] if flag else [])
        assert mrc.main(argv) == 0
        out = capsys.readouterr().out
        assert "My Private Notes" not in out and "Another Mine" not in out
        assert str(tmp_path) not in out and tmp_path.as_posix() not in out
    _, report, _ = _run(capsys, "--path", str(path), "--redact")
    target = report["targets"][0]
    assert target["path"] == "~/CLAUDE.md"
    assert [s["heading"] for s in target["sections"]] == ["user section #1", "Tech Stack", "user section #2"]


def test_text_output_labels_counts_as_estimated(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert mrc.main(["--path", str(_file(tmp_path, f"{INDEX}\n{START}\n{END}\n"))]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Token counts: estimated")
    assert "legacy spans: 1" in out
