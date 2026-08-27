"""Tests for scripts/build_framework_coverage.py.

The generator is read-only: it reads SKILL.md frontmatter under a root and
emits a coverage matrix (Markdown or JSON). These tests build small fixture
skill trees in tmp_path and assert the matrix reflects the framework tags.
"""

from __future__ import annotations

import json
from pathlib import Path

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py for why greping the
# YAML would be both wrong and dangerous to "fix".
from tests.validators._ci_reachability import assert_wired_into_ci


SCRIPT = "build_framework_coverage.py"


def write_skill(
    root: Path,
    name: str,
    *,
    mitre_attack: str | None = None,
    d3fend: str | None = None,
    nist_csf: str | None = None,
    mitre_f3: str | None = None,
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
    if mitre_f3 is not None:
        lines.append(f"mitre_f3: {mitre_f3}")
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


def test_mitre_f3_list_appears_in_matrix(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "fraud-skill", mitre_f3="[F1005.006]")
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr
    assert "F1005.006" in result.stdout
    assert "fraud-skill" in result.stdout
    assert "MITRE F3" in result.stdout


def test_navigator_layer_is_valid_json_with_required_keys(
    tmp_path: Path, runner
) -> None:
    write_skill(tmp_path, "skill-a", mitre_attack="[T1055, T1071]")
    write_skill(tmp_path, "skill-b", mitre_attack="[T1071]")
    layer_path = tmp_path / "layer.json"
    result = runner(SCRIPT, tmp_path, ["--navigator-layer", str(layer_path)])
    assert result.returncode == 0, result.stderr
    assert layer_path.exists()
    payload = json.loads(layer_path.read_text(encoding="utf-8"))
    assert payload["domain"] == "enterprise-attack"
    assert "layer" in payload["versions"]
    assert "navigator" in payload["versions"]
    assert "attack" in payload["versions"]
    ids = {entry["techniqueID"] for entry in payload["techniques"]}
    assert ids == {"T1055", "T1071"}
    by_id = {entry["techniqueID"]: entry for entry in payload["techniques"]}
    assert by_id["T1071"]["score"] == 2
    assert "skill-a" in by_id["T1071"]["comment"]
    assert "skill-b" in by_id["T1071"]["comment"]
    assert by_id["T1055"]["score"] == 1


def test_navigator_layer_is_byte_identical_across_two_runs(
    tmp_path: Path, runner
) -> None:
    write_skill(tmp_path, "skill-a", mitre_attack="[T1055]")
    first = tmp_path / "layer-a.json"
    second = tmp_path / "layer-b.json"
    result_a = runner(SCRIPT, tmp_path, ["--navigator-layer", str(first)])
    result_b = runner(SCRIPT, tmp_path, ["--navigator-layer", str(second)])
    assert result_a.returncode == 0, result_a.stderr
    assert result_b.returncode == 0, result_b.stderr
    assert first.read_bytes() == second.read_bytes()


def test_navigator_layer_techniques_match_distinct_mitre_attack(
    tmp_path: Path, runner
) -> None:
    write_skill(tmp_path, "multi", mitre_attack="[T1055, T1071, T1486]")
    write_skill(tmp_path, "overlap", mitre_attack="[T1055]")
    layer_path = tmp_path / "layer.json"
    result = runner(SCRIPT, tmp_path, ["--navigator-layer", str(layer_path)])
    assert result.returncode == 0, result.stderr
    payload = json.loads(layer_path.read_text(encoding="utf-8"))
    assert len(payload["techniques"]) == 3


REPO_ROOT = Path(__file__).resolve().parents[2]


def _generate_pair(tmp_path: Path, runner, extra_skills: list[tuple] | None = None) -> tuple[Path, Path]:
    """Write a tagged skill tree and generate both committed-style artifacts."""
    write_skill(tmp_path, "tagged", mitre_attack="[T1055]")
    if extra_skills:
        for args in extra_skills:
            write_skill(tmp_path, *args)
    markdown_path = tmp_path / "framework-coverage.md"
    layer_path = tmp_path / "attack-navigator-layer.json"
    result = runner(
        SCRIPT,
        tmp_path,
        ["--out", str(markdown_path), "--navigator-layer", str(layer_path)],
    )
    assert result.returncode == 0, result.stderr
    return markdown_path, layer_path


def test_markdown_carries_generated_header(tmp_path: Path, runner) -> None:
    markdown_path, _ = _generate_pair(tmp_path, runner)
    text = markdown_path.read_text(encoding="utf-8")
    assert "GENERATED FILE" in text
    assert "Do not edit by hand" in text
    assert "python scripts/build_framework_coverage.py" in text


def test_check_passes_when_artifacts_match(tmp_path: Path, runner) -> None:
    markdown_path, layer_path = _generate_pair(tmp_path, runner)
    result = runner(
        SCRIPT,
        tmp_path,
        ["--check", "--out", str(markdown_path), "--navigator-layer", str(layer_path)],
    )
    assert result.returncode == 0, result.stderr
    assert "in sync" in result.stdout


def test_check_fails_when_markdown_drifts(tmp_path: Path, runner) -> None:
    markdown_path, layer_path = _generate_pair(tmp_path, runner)
    markdown_path.write_text(
        markdown_path.read_text(encoding="utf-8") + "\n<!-- drift -->\n",
        encoding="utf-8",
    )
    result = runner(
        SCRIPT,
        tmp_path,
        ["--check", "--out", str(markdown_path), "--navigator-layer", str(layer_path)],
    )
    assert result.returncode == 1
    assert "stale committed file" in result.stderr
    assert "framework-coverage.md" in result.stderr.replace("\\", "/")


def test_check_fails_when_artifact_missing(tmp_path: Path, runner) -> None:
    write_skill(tmp_path, "tagged", mitre_attack="[T1055]")
    missing_md = tmp_path / "missing-coverage.md"
    missing_layer = tmp_path / "missing-layer.json"
    result = runner(
        SCRIPT,
        tmp_path,
        ["--check", "--out", str(missing_md), "--navigator-layer", str(missing_layer)],
    )
    assert result.returncode == 1
    assert "missing committed file" in result.stderr


def test_check_treats_crlf_as_equal_to_lf(tmp_path: Path, runner) -> None:
    markdown_path, layer_path = _generate_pair(tmp_path, runner)
    markdown_path.write_bytes(markdown_path.read_bytes().replace(b"\n", b"\r\n"))
    layer_path.write_bytes(layer_path.read_bytes().replace(b"\n", b"\r\n"))
    result = runner(
        SCRIPT,
        tmp_path,
        ["--check", "--out", str(markdown_path), "--navigator-layer", str(layer_path)],
    )
    assert result.returncode == 0, result.stderr


def test_check_passes_against_committed_catalog_artifacts(runner) -> None:
    result = runner(
        SCRIPT,
        REPO_ROOT / "catalog" / "skills",
        ["--check"],
    )
    assert result.returncode == 0, result.stderr


def test_check_wired_into_makefile_and_ci() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "python scripts/build_framework_coverage.py --check" in makefile
    assert_wired_into_ci("build_framework_coverage.py")
