"""Tests for the legacy-instruction fingerprint builder (v4.13.3 Phase 3.1).

The committed set must equal a fresh build, every line the current templates
and skill index ship must hash into it, and a line typed only by a user must
not. Generation fails loudly rather than writing a partial set.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import build_legacy_fingerprints as blf


@pytest.fixture(scope="module")
def built() -> dict:
    """A fresh build, or a skip in a shallow checkout.

    The set needs full history. CI's `tests` job clones at depth 1, so the
    drift check itself runs in the `validate` job (fetch-depth 0), pinned by
    test_ci_validate_job_runs_the_drift_check below.
    """
    try:
        return blf.build()
    except blf.BuildError as exc:
        if "shallow clone" in str(exc):
            pytest.skip(str(exc))
        raise


def test_shallow_clone_is_refused_rather_than_built_partially(monkeypatch: pytest.MonkeyPatch,
                                                               tmp_path: Path) -> None:
    real_git = blf._git
    monkeypatch.setattr(blf, "_git", lambda *a: "true\n" if a[:2] == ("rev-parse", "--is-shallow-repository")
                        else real_git(*a))
    target = tmp_path / "legacy_fingerprints.json"
    monkeypatch.setattr(blf, "OUTPUT", target)
    with pytest.raises(blf.BuildError, match="shallow clone"):
        blf.build()
    assert blf.main([]) == 2
    assert not target.exists()


def test_committed_set_matches_a_fresh_build(built: dict) -> None:
    assert blf.OUTPUT.read_text(encoding="utf-8") == blf._serialize(built)


def test_generation_is_deterministic(built: dict) -> None:
    assert blf._serialize(blf.build()) == blf._serialize(built)


def test_schema_and_count(built: dict) -> None:
    assert built["schema"] == blf.SCHEMA
    assert built["count"] == len(built["hashes"]) == len(set(built["hashes"]))
    assert built["hashes"] == sorted(built["hashes"])


@pytest.mark.parametrize("source", ["data/SKILL_INDEX.md", "templates/ai-instructions/base-claude.md"])
def test_every_current_shipped_line_is_in_the_set(built: dict, source: str) -> None:
    hashes = set(built["hashes"])
    lines = (REPO_ROOT / source).read_text(encoding="utf-8").splitlines()
    missing = [line for line in lines if line.strip() and blf.digest(line) not in hashes]
    assert missing == []


def test_a_user_only_line_is_not_in_the_set(built: dict) -> None:
    assert blf.digest("- My team deploys from the blue-green cluster every Thursday.") not in set(built["hashes"])


def test_trailing_whitespace_is_normalized() -> None:
    assert blf.digest("## Tech Stack   ") == blf.digest("## Tech Stack")


def test_placeholder_lines_render_each_historical_default() -> None:
    variants = blf._variants("Run {{BUILD_CMD}} now", {"BUILD_CMD": {"# specify build command"}})
    assert variants == {"Run {{BUILD_CMD}} now", "Run # specify build command now"}


def test_check_reports_drift_and_current(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, built: dict,
                                        capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "legacy_fingerprints.json"
    monkeypatch.setattr(blf, "OUTPUT", target)
    monkeypatch.setattr(blf, "build", lambda: built)
    assert blf.main(["--check"]) == 1  # absent counts as drift
    target.write_text(blf._serialize(built).replace(built["hashes"][0], "0" * 64), encoding="utf-8")
    assert blf.main(["--check"]) == 1
    assert "stale" in capsys.readouterr().err
    target.write_text(blf._serialize(built), encoding="utf-8")
    assert blf.main(["--check"]) == 0


def test_generation_writes_atomically(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, built: dict) -> None:
    target = tmp_path / "legacy_fingerprints.json"
    monkeypatch.setattr(blf, "OUTPUT", target)
    monkeypatch.setattr(blf, "REPO", tmp_path)
    monkeypatch.setattr(blf, "build", lambda: built)
    assert blf.main([]) == 0
    assert target.read_text(encoding="utf-8") == blf._serialize(built)
    assert list(tmp_path.iterdir()) == [target]


def test_empty_history_fails_loudly_and_writes_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "legacy_fingerprints.json"
    monkeypatch.setattr(blf, "OUTPUT", target)
    monkeypatch.setattr(blf, "_revisions", lambda paths: [])
    assert blf.main([]) == 2
    assert not target.exists()


def test_non_utf8_revision_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Proc:
        returncode = 0
        stdout = b"abc blob 2\n\xff\xfe\n"

    monkeypatch.setattr(blf.subprocess, "run", lambda *a, **k: _Proc())
    with pytest.raises(blf.BuildError, match="non-UTF-8"):
        blf._read_blobs([("a" * 40, "templates/ai-instructions/base-claude.md")])


def test_ci_validate_job_runs_the_drift_check() -> None:
    """The group is unscoped in the full profile, but CI selects groups by name."""
    import yaml

    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["validate"]["steps"]
    profile = next(step for step in steps if step.get("name") == "Repository-native validation profile")
    selected = profile["run"].split("--only", 1)[1].split()[0].split(",")
    assert "legacy-fingerprints" in selected
    checkout = next(step for step in steps if "actions/checkout" in str(step.get("uses", "")))
    assert checkout["with"]["fetch-depth"] == 0  # the builder walks full history
