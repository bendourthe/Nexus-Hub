"""Tests for the catalog-wide trigger-and-routing eval (scripts/run_trigger_evals.py).

The eval is a deterministic, model-free, stdlib-only detector that flags any two
skill descriptions whose trigger vocabulary overlaps beyond a threshold. These
tests cover the tokenizer/stemmer, the containment-overlap metric, threshold
behavior, allowlist downgrade, and the warning-only-vs-gate exit-code contract,
plus an end-to-end CLI pass over a fixture pair of deliberately colliding
descriptions (must be caught) and a pair of legitimately distinct ones (must
not be).

The module lives under scripts/ (not on the default path), so it is imported
directly by file location, mirroring tests/validators/test_validate_skills.py.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "scripts" / "run_trigger_evals.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_trigger_evals", RUNNER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rte = _load_runner()


def _write_skill(root: Path, category: str, name: str, description: str) -> None:
    """Create root/<category>/<name>/SKILL.md with valid single-line frontmatter."""
    skill_dir = root / category / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        'summary_l0: "A short summary."\n'
        'overview_l1: "A short overview paragraph."\n'
        "---\n\n"
        f"# {name}\n\nBody.\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Tokenizer + stemmer
# ---------------------------------------------------------------------------

def test_tokenize_drops_stopwords_and_short_tokens() -> None:
    # "use"/"the"/"for" are stopwords; "to" is under the 3-char floor.
    assert rte.tokenize("Use the widget dashboard for metrics") == {
        "widget", "dashboard", "metric",
    }


def test_tokenize_is_case_insensitive_and_splits_on_punctuation() -> None:
    # Case is lowered and punctuation splits tokens. "kubernetes" ends in "-es",
    # which the light suffix stemmer strips to "kubernet" -- lossy but
    # deterministic, so it applies equally to both sides of any comparison.
    assert rte.tokenize("Kubernetes/Helm, RBAC!") == {"kubernet", "helm", "rbac"}


def test_stem_normalizes_common_inflections() -> None:
    assert rte._stem("projects") == "project"   # -s
    assert rte._stem("finished") == "finish"     # -ed
    assert rte._stem("classes") == "class"       # -es
    assert rte._stem("reporting") == "report"    # -ing


def test_stem_keeps_stem_at_or_above_floor() -> None:
    # Stripping would drop below 3 chars, so the suffix is NOT stripped.
    assert rte._stem("using") == "using"   # would be "us" (2) -> kept whole
    assert rte._stem("bed") == "bed"        # would be "b" (1) -> kept whole
    # -es blocked (2 chars) but -s applies (3 chars): "uses" -> "use".
    assert rte._stem("uses") == "use"


def test_tokenize_matches_singular_and_plural() -> None:
    assert rte.tokenize("dashboard") == rte.tokenize("dashboards")


# ---------------------------------------------------------------------------
# Overlap metric (containment, not Jaccard)
# ---------------------------------------------------------------------------

def test_overlap_ratio_is_containment_over_smaller_set() -> None:
    # |A intersect B| / min(|A|, |B|): {a,b} fully contained in the larger set.
    assert rte.overlap_ratio({"a", "b"}, {"a", "b", "c", "d"}) == 1.0
    assert rte.overlap_ratio({"a", "b", "c"}, {"a", "x", "y"}) == 1 / 3


def test_overlap_ratio_empty_set_is_zero() -> None:
    assert rte.overlap_ratio(set(), {"a"}) == 0.0
    assert rte.overlap_ratio(set(), set()) == 0.0


# ---------------------------------------------------------------------------
# find_collisions: threshold + allowlist behavior
# ---------------------------------------------------------------------------

def test_find_collisions_reports_pair_at_or_above_threshold() -> None:
    # alpha:{alpha,beta} (2), gamma:{alpha,gamma,delta,epsilon} (4) share {alpha}
    # -> ratio 1/2 = 0.5. Exactly at threshold is reported (meets-or-exceeds).
    descriptions = {
        "alpha-skill": "alpha beta",
        "gamma-skill": "alpha gamma delta epsilon",
        "far-skill": "sonnet haiku rhyme meter",
    }
    at = rte.find_collisions(descriptions, threshold=0.5, allowlist={})
    pairs = {(c["a"], c["b"]) for c in at}
    assert ("alpha-skill", "gamma-skill") in pairs
    # The far skill shares nothing -> never reported.
    assert not any("far-skill" in (c["a"], c["b"]) for c in at)


def test_find_collisions_threshold_is_a_floor() -> None:
    descriptions = {
        "alpha-skill": "alpha beta",
        "gamma-skill": "alpha gamma delta epsilon",
    }
    # Just above 0.5 excludes the 0.5 pair.
    above = rte.find_collisions(descriptions, threshold=0.51, allowlist={})
    assert above == []


def test_find_collisions_marks_allowlisted_pairs() -> None:
    descriptions = {
        "widget-a": "build widget dashboard chart filter internal metric display",
        "widget-b": "build widget dashboard chart filter internal metric report",
    }
    allowlist = {("widget-a", "widget-b"): "matched pair by design"}
    collisions = rte.find_collisions(descriptions, threshold=0.5, allowlist=allowlist)
    assert len(collisions) == 1
    assert collisions[0]["allowlisted"] is True
    assert collisions[0]["reason"] == "matched pair by design"


# ---------------------------------------------------------------------------
# Allowlist loading + canonicalization
# ---------------------------------------------------------------------------

def test_canonical_pair_is_order_independent() -> None:
    assert rte._canonical_pair("b", "a") == ("a", "b")
    assert rte._canonical_pair("a", "b") == ("a", "b")


def test_load_allowlist_reads_list_and_object_entries(tmp_path: Path) -> None:
    p = tmp_path / "allow.json"
    p.write_text(
        json.dumps({
            "allow": [
                ["skill-x", "skill-y"],
                {"pair": ["skill-z", "skill-w"], "reason": "because"},
            ]
        }),
        encoding="utf-8",
    )
    loaded = rte.load_allowlist(p)
    assert loaded[("skill-x", "skill-y")] == ""
    assert loaded[("skill-w", "skill-z")] == "because"  # canonicalized order


def test_load_allowlist_missing_or_malformed_is_empty(tmp_path: Path) -> None:
    assert rte.load_allowlist(tmp_path / "nope.json") == {}
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert rte.load_allowlist(bad) == {}


# ---------------------------------------------------------------------------
# End-to-end CLI surface (warning-only vs gate)
# ---------------------------------------------------------------------------

def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO_ROOT,
    )


def _colliding_catalog(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    _write_skill(
        root, "cat", "widget-alpha",
        "build widget dashboard chart filter internal metric display",
    )
    _write_skill(
        root, "cat", "widget-beta",
        "build widget dashboard chart filter internal metric report",
    )
    return root


def test_cli_warning_only_reports_collision_but_exits_zero(tmp_path: Path) -> None:
    root = _colliding_catalog(tmp_path)
    result = _run_cli("--path", str(root), "--allowlist", str(tmp_path / "none.json"))
    assert result.returncode == 0, result.stdout
    assert "FAIL descriptions near-collide" in result.stdout
    assert "widget-alpha vs widget-beta" in result.stdout


def test_cli_gate_exits_nonzero_on_unallowlisted_collision(tmp_path: Path) -> None:
    root = _colliding_catalog(tmp_path)
    result = _run_cli("--path", str(root), "--allowlist", str(tmp_path / "none.json"), "--gate")
    assert result.returncode == 1, result.stdout
    assert "FAIL descriptions near-collide" in result.stdout


def test_cli_gate_passes_when_pair_is_allowlisted(tmp_path: Path) -> None:
    root = _colliding_catalog(tmp_path)
    allow = tmp_path / "allow.json"
    allow.write_text(
        json.dumps({"allow": [{"pair": ["widget-alpha", "widget-beta"], "reason": "sibling"}]}),
        encoding="utf-8",
    )
    result = _run_cli("--path", str(root), "--allowlist", str(allow), "--gate")
    assert result.returncode == 0, result.stdout
    assert "PASS" in result.stdout


def test_cli_distinct_descriptions_report_no_collision(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "cat", "kube-deploy", "deploy kubernetes clusters with helm and rbac")
    _write_skill(root, "cat", "poem-writer", "write sonnets and haiku with rhyme and meter")
    result = _run_cli("--path", str(root), "--allowlist", str(tmp_path / "none.json"))
    assert result.returncode == 0, result.stdout
    assert "FAIL" not in result.stdout
    assert "PASS" in result.stdout


def test_cli_json_output_is_structured(tmp_path: Path) -> None:
    root = _colliding_catalog(tmp_path)
    result = _run_cli("--path", str(root), "--allowlist", str(tmp_path / "none.json"), "--json")
    payload = json.loads(result.stdout)
    assert payload["scanned"] == 2
    assert payload["unallowlisted_count"] == 1
    assert payload["collisions"][0]["a"] == "widget-alpha"
    assert payload["collisions"][0]["pct"] >= 50


def test_cli_missing_path_errors(tmp_path: Path) -> None:
    result = _run_cli("--path", str(tmp_path / "does-not-exist"))
    assert result.returncode == 1
    assert "does not exist" in result.stderr


# ---------------------------------------------------------------------------
# In-process main() surface (covers argparse + reporting branches directly)
# ---------------------------------------------------------------------------

import pytest  # noqa: E402  (kept local to the in-process main() section)


def _main_with_argv(monkeypatch: pytest.MonkeyPatch, *argv: str) -> int:
    monkeypatch.setattr(sys, "argv", ["run_trigger_evals.py", *argv])
    return rte.main()


def test_main_warning_only_returns_zero(tmp_path, monkeypatch, capsys) -> None:
    root = _colliding_catalog(tmp_path)
    rc = _main_with_argv(monkeypatch, "--path", str(root), "--allowlist", str(tmp_path / "n.json"))
    out = capsys.readouterr().out
    assert rc == 0
    assert "FAIL descriptions near-collide" in out
    assert "warning-only mode" in out


def test_main_gate_returns_one(tmp_path, monkeypatch, capsys) -> None:
    root = _colliding_catalog(tmp_path)
    rc = _main_with_argv(monkeypatch, "--path", str(root), "--allowlist", str(tmp_path / "n.json"), "--gate")
    capsys.readouterr()
    assert rc == 1


def test_main_verbose_prints_allowlisted_info(tmp_path, monkeypatch, capsys) -> None:
    root = _colliding_catalog(tmp_path)
    allow = tmp_path / "allow.json"
    allow.write_text(
        json.dumps({"allow": [{"pair": ["widget-alpha", "widget-beta"], "reason": "sibling"}]}),
        encoding="utf-8",
    )
    rc = _main_with_argv(monkeypatch, "--path", str(root), "--allowlist", str(allow), "--verbose")
    out = capsys.readouterr().out
    assert rc == 0
    assert "INFO (allowlisted)" in out
    assert "sibling" in out
    assert "PASS" in out


def test_main_json_gate_returns_one(tmp_path, monkeypatch, capsys) -> None:
    root = _colliding_catalog(tmp_path)
    rc = _main_with_argv(monkeypatch, "--path", str(root), "--allowlist", str(tmp_path / "n.json"), "--json", "--gate")
    payload = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert payload["gate"] is True
    assert payload["unallowlisted_count"] == 1


def test_main_missing_path_returns_one(tmp_path, monkeypatch, capsys) -> None:
    rc = _main_with_argv(monkeypatch, "--path", str(tmp_path / "nope"))
    err = capsys.readouterr().err
    assert rc == 1
    assert "does not exist" in err


def test_real_catalog_has_zero_unallowlisted_collisions() -> None:
    # Guards the Phase 1 stability gate: with the shipped allowlist in place, the
    # full 267-skill catalog reports zero un-allowlisted near-collisions, so the
    # Phase 6 promotion to --gate will stay green.
    result = _run_cli("--gate")
    assert result.returncode == 0, result.stdout
    assert "0 un-allowlisted collisions" in result.stdout
