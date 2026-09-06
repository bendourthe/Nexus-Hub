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


def _write_cases(root: Path, category: str, name: str, data: dict) -> None:
    """Write a skill's evals/trigger-cases.json fixture."""
    evals_dir = root / category / name / "evals"
    evals_dir.mkdir(parents=True, exist_ok=True)
    (evals_dir / "trigger-cases.json").write_text(json.dumps(data), encoding="utf-8")


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


# ---------------------------------------------------------------------------
# Routing assertions (Phase 3)
# ---------------------------------------------------------------------------

def _cases(*case_dicts: dict) -> dict:
    return {"skill": "s", "purpose": "p", "cases": list(case_dicts)}


def test_assert_routing_positive_ranks_own_skill_first() -> None:
    tokens = {"alpha": {"alpha", "widget", "dashboard"}, "beta": {"beta", "report", "export"}}
    by_skill = {"alpha": _cases({"id": "p1", "prompt": "alpha widget", "should_trigger": True})}
    failures, stats = rte.assert_routing(tokens, by_skill, margin=1.15)
    assert failures == []
    assert stats["cases_evaluated"] == 1


def test_assert_routing_misroute_is_flagged() -> None:
    tokens = {"alpha": {"alpha", "common"}, "beta": {"beta", "common", "widget", "dashboard"}}
    by_skill = {"alpha": _cases({"id": "p1", "prompt": "widget dashboard common", "should_trigger": True})}
    failures, _ = rte.assert_routing(tokens, by_skill, margin=1.15)
    assert len(failures) == 1
    assert failures[0]["kind"] == "misroute"
    assert failures[0]["mis_routed_to"] == "beta"


def test_assert_routing_margin_failure_is_flagged() -> None:
    # Positive scores 1.0 against alpha; near-miss negative also scores 1.0, so the
    # weakest positive does not clear the strongest negative by 1.15x. Tokens are
    # stemmer-stable words (no ing/es/ed/s suffix) so a prompt tokenizes to them
    # verbatim, matching how real token sets are built from tokenize(description).
    tokens = {"alpha": {"alpha", "common", "widget"}, "beta": {"beta"}}
    by_skill = {"alpha": _cases(
        {"id": "pos", "prompt": "alpha", "should_trigger": True},
        {"id": "neg", "prompt": "common widget", "should_trigger": False},
    )}
    failures, _ = rte.assert_routing(tokens, by_skill, margin=1.15)
    assert len(failures) == 1
    assert failures[0]["kind"] == "margin"


def test_assert_routing_skips_non_lexical_cases() -> None:
    tokens = {"alpha": {"alpha"}, "beta": {"beta", "widget", "dashboard"}}
    # A lexical:false positive that WOULD mis-route is skipped, so no failure.
    by_skill = {"alpha": _cases(
        {"id": "nl", "prompt": "widget dashboard", "should_trigger": True, "lexical": False},
    )}
    failures, stats = rte.assert_routing(tokens, by_skill, margin=1.15)
    assert failures == []
    assert stats["cases_evaluated"] == 0
    assert stats["skipped_nonlexical"] == 1


def test_assert_routing_malformed_file_is_flagged() -> None:
    failures, _ = rte.assert_routing({"alpha": {"alpha"}}, {"alpha": {"_error": "bad json"}}, margin=1.15)
    assert len(failures) == 1
    assert failures[0]["kind"] == "malformed"


def test_assert_routing_margin_needs_both_positive_and_negative() -> None:
    # Only positives (no negatives) -> the margin check is not run.
    tokens = {"alpha": {"alpha", "shared"}, "beta": {"beta"}}
    by_skill = {"alpha": _cases({"id": "pos", "prompt": "alpha shared", "should_trigger": True})}
    failures, _ = rte.assert_routing(tokens, by_skill, margin=1.15)
    assert failures == []


def test_find_trigger_cases_discovers_evals_file(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "cat", "widget-skill", "widget dashboard chart filter")
    _write_cases(root, "cat", "widget-skill", _cases(
        {"id": "p1", "prompt": "widget dashboard", "should_trigger": True},
    ))
    found = rte.find_trigger_cases(root)
    assert "widget-skill" in found
    assert found["widget-skill"]["cases"][0]["id"] == "p1"


def test_find_trigger_cases_carries_malformed_file_as_error(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "cat", "broken-skill", "widget dashboard chart")
    (root / "cat" / "broken-skill" / "evals").mkdir(parents=True, exist_ok=True)
    (root / "cat" / "broken-skill" / "evals" / "trigger-cases.json").write_text("{not json", encoding="utf-8")
    found = rte.find_trigger_cases(root)
    assert "_error" in found["broken-skill"]
    # ... and assert_routing surfaces it as a malformed failure.
    failures, _ = rte.assert_routing({"broken-skill": {"widget"}}, found, margin=1.15)
    assert any(f["kind"] == "malformed" for f in failures)


# --- Routing via the CLI ---

def _routing_catalog(tmp_path: Path) -> Path:
    """Two distinct skills; widget-skill ships a positive that mis-routes to report-skill."""
    root = tmp_path / "skills"
    _write_skill(root, "cat", "widget-skill", "widget dashboard chart filter panel")
    _write_skill(root, "cat", "report-skill", "report export widget dashboard chart data table")
    _write_cases(root, "cat", "widget-skill", _cases(
        {"id": "misroute", "prompt": "report export data table", "should_trigger": True},
    ))
    return root


def test_cli_gate_fails_on_routing_misroute(tmp_path: Path) -> None:
    root = _routing_catalog(tmp_path)
    result = _run_cli("--path", str(root), "--allowlist", str(tmp_path / "none.json"), "--gate")
    assert result.returncode == 1, result.stdout
    assert "FAIL routing" in result.stdout


def test_cli_warning_only_no_cases_warns_and_passes(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    _write_skill(root, "cat", "lonely-skill", "deploy kubernetes clusters with helm and rbac")
    result = _run_cli("--path", str(root), "--allowlist", str(tmp_path / "none.json"))
    assert result.returncode == 0, result.stdout
    assert "no trigger-cases.json" in result.stdout


def test_cli_json_reports_routing_block(tmp_path: Path) -> None:
    root = _routing_catalog(tmp_path)
    result = _run_cli("--path", str(root), "--allowlist", str(tmp_path / "none.json"), "--json")
    payload = json.loads(result.stdout)
    assert payload["routing"]["skills_with_cases"] == 1
    assert payload["routing"]["skills_without_cases"] == 1
    assert len(payload["routing"]["failures"]) == 1


def test_real_catalog_routing_tranche_passes() -> None:
    # Phase 3 stability gate: the authored first tranche routes cleanly (zero
    # routing failures) so the Phase 6 promotion to --gate stays green, while the
    # rest of the catalog stays on the WARN path.
    result = _run_cli("--json")
    payload = json.loads(result.stdout)
    routing = payload["routing"]
    assert routing["failures"] == [], routing["failures"]
    assert routing["skills_with_cases"] >= 6
    assert routing["skills_without_cases"] > 0  # incremental coverage, not the whole catalog


# ---------------------------------------------------------------------------
# SKIP-clause stripping (v3.18.0 gap DF-2)
# ---------------------------------------------------------------------------
#
# A description's SKIP clause states what the skill is NOT for. Tokenizing it
# counted that fenced-off vocabulary as POSITIVE trigger evidence, which is
# backwards, and it penalised authors for following the AGENTS.md rule that says
# to write a SKIP clause at all. Two real cases from v3.18.0: "generate the
# changelog entry for this release" scored a perfect 1.00 against
# devlog-generation, and so did "what work is still open or deferred for this
# version" -- both purely on SKIP-clause text.


def test_strip_skip_clause_removes_uppercase_marker() -> None:
    module = _load_runner()
    text = "Maintain the index. SKIP: the changelog (use release-notes-writer)."
    assert module.strip_skip_clause(text) == "Maintain the index. "


def test_strip_skip_clause_removes_dashed_marker() -> None:
    module = _load_runner()
    text = "Maintain the index. SKIP - the changelog (use release-notes-writer)."
    assert module.strip_skip_clause(text) == "Maintain the index. "


def test_strip_skip_clause_removes_do_not_use_for_marker() -> None:
    module = _load_runner()
    text = "Build a chart. Do NOT use for dashboards."
    assert module.strip_skip_clause(text) == "Build a chart. "


def test_strip_skip_clause_leaves_a_description_without_one_alone() -> None:
    module = _load_runner()
    text = "Maintain the index, one line per release."
    assert module.strip_skip_clause(text) == text


def test_skip_clause_vocabulary_is_not_positive_trigger_evidence() -> None:
    """The defect this closes, stated as a behavior rather than a helper call."""
    module = _load_runner()
    description = (
        "Maintain the DEVLOG index. Use when the user says update the devlog. "
        "SKIP: the authoritative record of what changed in a release "
        "(use release-notes-writer)."
    )
    tokens = module.tokenize(module.strip_skip_clause(description))
    assert "devlog" in tokens, "the positive trigger vocabulary must survive"
    for fenced in ("release", "record", "changed"):
        assert fenced not in tokens, (
            f"'{fenced}' appears only in the SKIP clause and must not count as "
            "evidence for triggering this skill"
        )


def test_skip_marker_pattern_contains_no_control_characters() -> None:
    """Guards a real authoring accident, not a hypothetical one.

    The first cut of this pattern was written with escaped word boundaries that
    reached the file as literal backspace bytes (0x08). The regex silently
    matched nothing, the stripper became a no-op, and `grep` rendered the
    corruption as invisible whitespace.
    """
    module = _load_runner()
    pattern = module._SKIP_MARKER.pattern
    control = [c for c in pattern if ord(c) < 0x20]
    assert not control, f"control characters in the SKIP marker: {[hex(ord(c)) for c in control]}"
