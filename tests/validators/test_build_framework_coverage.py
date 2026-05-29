"""Tests for scripts/build_framework_coverage.py.

The generator is read-only: it reads SKILL.md frontmatter under a root and
emits a coverage matrix (Markdown or JSON). These tests build small fixture
skill trees in tmp_path and assert the matrix reflects the framework tags.
"""

from __future__ import annotations

import json
from pathlib import Path


SCRIPT = "build_framework_coverage.py"


def write_skill(
    root: Path,
    name: str,
    *,
    mitre_attack: str | None = None,
    d3fend: str | None = None,
    nist_csf: str | None = None,
) -> None:
    """Create catalog-style <root>/<name>/SKILL.md with optional tags."""
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    lines = ["---", f"name: {name}", "description: fixture skill"]
    lines.append('summary_l0: "fixture"')
    lines.append('overview_l1: "fixture overview"')
    if mitre_attack is not None:
        lines.append(f"mitre_attack: {mitre_attack}")
    if d3fend is not None:
        lines.append(f"d3fend_techniques: {d3fend}")
    if nist_csf is not None:
        lines.append(f"nist_csf: {nist_csf}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {name}\n\nBody.\n")
    (skill_dir / "SKILL.md").write_text("\n".join(lines), encoding="utf-8")


def test_untagged_tree_is_empty_but_succeeds(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "plain-skill")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "No skills currently tagged" in result.stdout
    assert "Security Framework Coverage Matrix" in result.stdout


def test_tagged_skill_appears_in_matrix(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "hunting-cred-dumping", mitre_attack="[T1003.001]", nist_csf="[DE.CM]")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "T1003.001" in result.stdout
    assert "hunting-cred-dumping" in result.stdout
    assert "DE.CM" in result.stdout


def test_shared_control_lists_both_skills(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "skill-a", mitre_attack="[T1071]")
    write_skill(tmp_path, "skill-b", mitre_attack="[T1071, T1486]")
    result = runner(SCRIPT, tmp_path, ["--format", "json"])
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    attack = payload["coverage"]["mitre_attack"]
    assert sorted(attack["T1071"]) == ["skill-a", "skill-b"]
    assert attack["T1486"] == ["skill-b"]
    assert payload["summary"]["mitre_attack"]["controls"] == 2


def test_multi_id_and_bare_scalar_parse(tmp_path: Path, runner) -> None:
    # Bracketed multi-id and a bare scalar both parse.
    write_skill(tmp_path, "multi", d3fend="[D3-NTA, D3-PA]")
    write_skill(tmp_path, "bare", d3fend="D3-PM")
    result = runner(SCRIPT, tmp_path, ["--format", "json"])
    assert result.returncode == 0, result.stderr
    d3fend = json.loads(result.stdout)["coverage"]["d3fend_techniques"]
    assert d3fend["D3-NTA"] == ["multi"]
    assert d3fend["D3-PA"] == ["multi"]
    assert d3fend["D3-PM"] == ["bare"]


def test_out_flag_writes_file(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "tagged", mitre_attack="[T1071]")
    out = tmp_path / "out" / "coverage.md"
    result = runner(SCRIPT, tmp_path, ["--out", str(out)])
    assert result.returncode == 0, result.stderr
    assert out.exists()
    assert "T1071" in out.read_text(encoding="utf-8")


def test_missing_root_errors(tmp_path: Path, runner) -> None:
    result = runner(SCRIPT, tmp_path / "does-not-exist")
    assert result.returncode == 1
    assert "does not exist" in result.stderr
