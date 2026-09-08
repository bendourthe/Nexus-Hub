"""Tests for scripts/build_framework_coverage.py.

The generator is read-only: it reads SKILL.md frontmatter under a root and
emits a coverage matrix (Markdown or JSON). These tests build small fixture
skill trees in tmp_path and assert the matrix reflects the framework tags.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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


# --- v4.8.0 WN-G / WN-H: parser defects found by the Tier 3 adversarial pass --
#
# Both were PRE-EXISTING and applied to all seven framework fields, so both are
# covered by a matrix over the whole field set rather than by a case for the one
# field that exposed them. WN-G: a trailing YAML comment was parsed as part of
# the identifier. WN-H: a block-sequence value produced nothing, so the skill
# was silently ABSENT from the matrix while validate_skills.py accepted the same
# shape. Silent under-coverage is the worse of the two, because nothing reports
# it.

import importlib.util as _importlib_util

_spec = _importlib_util.spec_from_file_location(
    "_bfc", Path(__file__).resolve().parents[2] / "scripts" / "build_framework_coverage.py"
)
_bfc = _importlib_util.module_from_spec(_spec)
_spec.loader.exec_module(_bfc)

FRAMEWORK_FIELD_SAMPLES = [
    ("mitre_attack", "T1071", "T1003.001"),
    ("atlas_techniques", "AML.T0047", "AML.T0049"),
    ("mitre_f3", "F1005.006", "F1010"),
    ("d3fend_techniques", "D3-NTA", "D3-PA"),
    ("nist_csf", "DE.CM", "RS.AN"),
    ("nist_ai_rmf", "MEASURE-2.6", "GOVERN-1.1"),
    ("owasp_agentic", "ASI01", "ASI06"),
]


def _frontmatter(body: str) -> str:
    return (
        "---\n"
        "name: fixture-skill\n"
        "description: A fixture used to exercise the framework-tag parser.\n"
        f"{body}"
        "---\n\n# Fixture\n"
    )


@pytest.mark.parametrize(
    "field,first,second", FRAMEWORK_FIELD_SAMPLES, ids=lambda v: v if isinstance(v, str) else ""
)
def test_trailing_comment_is_not_part_of_the_identifier(
    field: str, first: str, second: str
) -> None:
    """WN-G. A comment is legal YAML and an obvious place to record a
    verification date."""
    tags = _bfc.parse_framework_tags(
        _frontmatter(f"{field}: [{first}] # verified 2026-09-07\n")
    )
    assert tags[field] == [first], f"{field} absorbed the comment: {tags.get(field)}"


@pytest.mark.parametrize(
    "field,first,second", FRAMEWORK_FIELD_SAMPLES, ids=lambda v: v if isinstance(v, str) else ""
)
def test_block_sequence_reaches_the_matrix(field: str, first: str, second: str) -> None:
    """WN-H. validate_skills.py accepts this shape and AGENTS.md documents it,
    so the matrix must not silently drop it."""
    tags = _bfc.parse_framework_tags(
        _frontmatter(f"{field}:\n  - {first}\n  - {second}\n")
    )
    assert tags[field] == [first, second], f"{field} block sequence lost: {tags.get(field)}"


@pytest.mark.parametrize(
    "field,first,second", FRAMEWORK_FIELD_SAMPLES, ids=lambda v: v if isinstance(v, str) else ""
)
def test_block_sequence_stops_at_the_next_key(
    field: str, first: str, second: str
) -> None:
    """The look-ahead must not absorb the following field's values."""
    other = "nist_csf" if field != "nist_csf" else "mitre_attack"
    other_id = "DE.CM" if field != "nist_csf" else "T1071"
    tags = _bfc.parse_framework_tags(
        _frontmatter(f"{field}:\n  - {first}\n{other}: [{other_id}]\n")
    )
    assert tags[field] == [first]
    assert tags[other] == [other_id]


@pytest.mark.parametrize(
    "field,first,second", FRAMEWORK_FIELD_SAMPLES, ids=lambda v: v if isinstance(v, str) else ""
)
def test_block_sequence_item_comment_is_stripped(
    field: str, first: str, second: str
) -> None:
    tags = _bfc.parse_framework_tags(
        _frontmatter(f"{field}:\n  - {first}  # why this one\n")
    )
    assert tags[field] == [first]


@pytest.mark.parametrize(
    "field,first,second", FRAMEWORK_FIELD_SAMPLES, ids=lambda v: v if isinstance(v, str) else ""
)
def test_flow_list_still_parses(field: str, first: str, second: str) -> None:
    """Regression guard: the common shape every shipped skill uses."""
    tags = _bfc.parse_framework_tags(_frontmatter(f"{field}: [{first}, {second}]\n"))
    assert tags[field] == [first, second]


def test_hash_inside_a_flow_list_is_not_treated_as_a_comment() -> None:
    """Splitting on a bracketed `#` would truncate the list instead of the
    comment. No framework uses `#` today, so this pins the intent rather than a
    current need."""
    assert _bfc.strip_comment("[A#1, B] # note").strip() == "[A#1, B]"


def test_absent_field_stays_absent() -> None:
    assert _bfc.parse_framework_tags(_frontmatter("")) == {}
