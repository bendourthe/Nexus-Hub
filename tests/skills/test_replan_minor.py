"""The minor re-plan helper is read-only and reports overlap, redundancy, order and schedule."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "catalog/skills/workflow/plan-queue-assessment/scripts/replan_minor.py"


@pytest.fixture(scope="module")
def rp():
    spec = importlib.util.spec_from_file_location("replan_minor_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_plan(folder: Path, version: str, slug: str, tasks, *, status="queued", claims=None, extra="") -> Path:
    """tasks: list of (phase, text, done). Task text ends with its target path."""
    lines = [f"# Plan - {slug}", "", f"**Version**: {version}", f"**Slug**: {slug}", f"**Status**: {status}", ""]
    if extra:
        lines += [extra, ""]
    if claims:
        lines += ["```json", json.dumps(claims), "```", ""]
    phase_seen = set()
    for n, (phase, text, done) in enumerate(tasks, 1):
        if phase not in phase_seen:
            phase_seen.add(phase)
            lines += [f"## Phase {phase}: Work {phase}", ""]
        lines.append(f"- [{'x' if done else ' '}] T{n:03d} {text}")
    path = folder / f"{version}-{slug}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def run(rp, folder: Path, lanes: int = 3, **kw) -> dict:
    return rp.analyze(folder, lanes, kw.get("similarity", 0.8), kw.get("include_all", False),
                      kw.get("include_boilerplate", False), kw.get("claims_deps_only", False))


def digest(folder: Path) -> dict:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(folder.iterdir())}


def test_write_write_overlap_is_hard_and_coordinator_paths_are_ignored(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "alpha", [(1, "Edit parser scripts/parser.py", False), (1, "Log CHANGELOG.md", False)])
    write_plan(tmp_path, "v1.0.2", "beta", [(1, "Rework parser scripts/parser.py", False), (1, "Log CHANGELOG.md", False)])
    report = run(rp, tmp_path)
    assert len(report["overlaps"]) == 1
    pair = report["overlaps"][0]
    assert pair["hard"] and pair["write_write"] == ["scripts/parser.py"]
    assert report["hot_files"][0]["path"] == "scripts/parser.py"
    assert all("CHANGELOG" not in h["path"] for h in report["hot_files"])


def test_write_against_directory_read_is_narrowable_not_hard(rp, tmp_path):
    claims_a = {"depends_on": [], "read_paths": ["docs/guides/"], "write_paths": ["src/a.py"]}
    claims_b = {"depends_on": [], "read_paths": [], "write_paths": ["docs/guides/one.md"]}
    write_plan(tmp_path, "v1.0.1", "alpha", [(1, "Do a src/a.py", False)], claims=claims_a)
    write_plan(tmp_path, "v1.0.2", "beta", [(1, "Do b docs/guides/one.md", False)], claims=claims_b)
    report = run(rp, tmp_path)
    pair = report["overlaps"][0]
    assert pair["hard"] is False and pair["write_read"]
    assert report["narrowable_pairs"] == 1
    assert report["schedule"]["proposed_wave_count"] == 1
    assert report["schedule"]["strict_wave_count"] == 2


def test_redundant_tasks_found_and_template_tasks_suppressed(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "alpha", [(1, "Add the approvals control with derives settings catalog lib/catalog.py", False),
                                             (2, "Commit Phase 1 locally docs/history/a.md", False)])
    write_plan(tmp_path, "v1.0.2", "beta", [(1, "Add the approvals control with derives settings catalog lib/catalog2.py", False),
                                            (2, "Commit Phase 1 locally docs/history/b.md", False)])
    report = run(rp, tmp_path)
    assert [(t["a_task"], t["b_task"]) for t in report["redundant_tasks"]] == [("T001", "T001")]
    assert report["boilerplate_pairs_suppressed"] >= 1


def test_dependency_chain_critical_path_and_cycle(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A one src/a1.py", False)])
    write_plan(tmp_path, "v1.0.2", "b", [(1, "B one src/b1.py", False), (1, "B two src/b2.py", False)],
               claims={"depends_on": ["v1.0.1"], "read_paths": [], "write_paths": ["src/b1.py", "src/b2.py"]})
    write_plan(tmp_path, "v1.0.3", "c", [(1, "C one src/c1.py", False)],
               claims={"depends_on": ["v1.0.2"], "read_paths": [], "write_paths": ["src/c1.py"]})
    deps = run(rp, tmp_path)["dependencies"]
    assert deps["edges"] == [("v1.0.1", "v1.0.2"), ("v1.0.2", "v1.0.3")]
    assert deps["critical_path"] == ["v1.0.1", "v1.0.2", "v1.0.3"] and deps["critical_weight"] == 4
    assert deps["cycle"] == []
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A one src/a1.py", False)],
               claims={"depends_on": ["v1.0.3"], "read_paths": [], "write_paths": ["src/a1.py"]})
    report = run(rp, tmp_path)
    assert set(report["dependencies"]["cycle"]) == {"v1.0.1", "v1.0.2", "v1.0.3"}
    assert report["proposed_renumber"] == []


def test_prose_dependency_is_a_hint_and_claims_only_flag_drops_it(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A src/a.py", False)])
    write_plan(tmp_path, "v1.0.2", "b", [(1, "B src/b.py", False)], extra="This plan depends on v1.0.1 landing first.")
    report = run(rp, tmp_path)
    assert report["dependencies"]["prose_only_edges"] == [("v1.0.1", "v1.0.2")]
    assert run(rp, tmp_path, claims_deps_only=True)["dependencies"]["edges"] == []
    write_plan(tmp_path, "v1.0.2", "b", [(1, "B src/b.py", False)], extra="No implementation prerequisite on v1.0.1.")
    assert run(rp, tmp_path)["dependencies"]["edges"] == []


def test_lane_cap_limits_wave_width_and_conflicts_force_separate_waves(rp, tmp_path):
    for n in range(1, 5):
        write_plan(tmp_path, f"v1.0.{n}", f"p{n}", [(1, f"Work src/p{n}.py", False)])
    assert run(rp, tmp_path, lanes=2)["schedule"]["proposed_wave_count"] == 2
    assert run(rp, tmp_path, lanes=4)["schedule"]["proposed_wave_count"] == 1
    write_plan(tmp_path, "v1.0.4", "p4", [(1, "Work src/p1.py", False)])
    waves = run(rp, tmp_path, lanes=4)["schedule"]["proposed_waves"]
    assert len(waves) == 2 and not any({"v1.0.1", "v1.0.4"} <= set(w) for w in waves)


def test_renumber_proposed_only_when_it_saves_waves_and_respects_dependencies(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A src/a.py", False)])
    write_plan(tmp_path, "v1.0.2", "b", [(1, "B src/b.py", False)])
    write_plan(tmp_path, "v1.0.3", "c", [(1, "C src/c.py", False)])
    write_plan(tmp_path, "v1.0.4", "d", [(1, "D src/d.py", False)],
               claims={"depends_on": ["v1.0.3"], "read_paths": [], "write_paths": ["src/d.py"]})
    report = run(rp, tmp_path, lanes=2)
    assert report["schedule"]["baseline_wave_count"] == 3 and report["schedule"]["proposed_wave_count"] == 2
    assert {(m["from"], m["to"]) for m in report["proposed_renumber"]} == {("v1.0.3", "v1.0.2"), ("v1.0.2", "v1.0.3")}
    versions = report["proposed_order"]
    assert versions.index("v1.0.3") < versions.index("v1.0.4")


def test_pinned_plan_keeps_its_version(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A src/a.py", False)])
    write_plan(tmp_path, "v1.0.2", "b", [(1, "B src/b.py", True), (1, "B2 src/b2.py", False)])
    write_plan(tmp_path, "v1.0.3", "c", [(1, "C src/c.py", False)])
    write_plan(tmp_path, "v1.0.4", "d", [(1, "D src/d.py", False)],
               claims={"depends_on": ["v1.0.3"], "read_paths": [], "write_paths": ["src/d.py"]})
    report = run(rp, tmp_path, lanes=2)
    assert next(p for p in report["plans"] if p["version"] == "v1.0.2")["pinned"]
    assert all(m["from"] != "v1.0.2" and m["to"] != "v1.0.2" for m in report["proposed_renumber"])


def test_shipped_and_fully_checked_plans_are_excluded_unless_requested(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A src/a.py", False)])
    write_plan(tmp_path, "v1.0.2", "b", [(1, "B src/b.py", False)], status="shipped")
    write_plan(tmp_path, "v1.0.3", "c", [(1, "C src/c.py", True)])
    report = run(rp, tmp_path)
    assert [p["version"] for p in report["plans"]] == ["v1.0.1"] and len(report["excluded"]) == 2
    assert len(run(rp, tmp_path, include_all=True)["plans"]) == 3


def test_split_candidate_when_phases_share_no_files(rp, tmp_path):
    tasks = [(1, f"One {n} src/one/f{n}.py", False) for n in range(16)] + [(2, f"Two {n} src/two/g{n}.py", False) for n in range(16)]
    write_plan(tmp_path, "v1.0.1", "big", tasks)
    split = run(rp, tmp_path)["split_candidates"]
    assert len(split) == 1 and len(split[0]["independent_phase_groups"]) == 2


def test_merge_candidate_for_heavily_overlapping_small_plans(rp, tmp_path):
    files = [f"src/shared/f{n}.py" for n in range(4)]
    write_plan(tmp_path, "v1.0.1", "a", [(1, f"Change {f}", False) for f in files])
    write_plan(tmp_path, "v1.0.2", "b", [(1, f"Adjust {f}", False) for f in files])
    merges = run(rp, tmp_path)["merge_candidates"]
    assert merges and merges[0]["plans"] == ["v1.0.1", "v1.0.2"]


def test_unreadable_plan_is_reported_and_exit_code_is_one(rp, tmp_path, capsys):
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A src/a.py", False)])
    (tmp_path / "v1.0.2-bad.md").write_bytes(b"\xff\xfe\x00\x80bad")
    assert rp.main([str(tmp_path)]) == 1
    assert "unreadable: 1" in capsys.readouterr().out


def test_analysis_never_edits_plans_and_json_mode_is_valid(rp, tmp_path, capsys):
    write_plan(tmp_path, "v1.0.1", "a", [(1, "A src/a.py", False)])
    write_plan(tmp_path, "v1.0.2", "b", [(1, "B src/a.py", False)])
    before = digest(tmp_path)
    assert rp.main([str(tmp_path), "--json", "-", "--lanes", "2"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["lanes"] == 2 and data["overlaps"]
    assert digest(tmp_path) == before
    assert rp.main([str(tmp_path / "missing")]) == 2


def test_default_lanes_honors_override_and_cap(rp, monkeypatch):
    monkeypatch.setenv("NEXUS_IMPLEMENT_LANES", "9")
    assert rp.default_lanes() == 9
    monkeypatch.delenv("NEXUS_IMPLEMENT_LANES")
    monkeypatch.setattr(rp.os, "cpu_count", lambda: 64)
    assert rp.default_lanes() == 6
    monkeypatch.setattr(rp.os, "cpu_count", lambda: 1)
    assert rp.default_lanes() == 1


def test_overlap_matches_native_checker_semantics(rp):
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import completion_minor as native
    finally:
        sys.path.remove(str(ROOT / "scripts"))
    paths = ["docs/", "docs/a.md", "DOCS/A.md", "docs", "docs/decisions/", "docs/decisions/x.md", "src/a.py", "src/"]
    for left in paths:
        for right in paths:
            assert rp.overlap(left, right) == native._overlap(left, right), (left, right)


def test_unrelated_tasks_made_of_names_and_paths_are_not_redundant(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "alpha", [(1, "Add the `approvals` control with `derives` lib/settings_control/catalog.json", False),
                                             (2, "Move the decision record to implemented docs/decisions/implemented/policy/2026-11-11-approval-modes.md", False)])
    write_plan(tmp_path, "v1.0.2", "beta", [(1, "Add the claude-fable-5-2 profile test tests/skills/test_prompting_profile.py", False),
                                            (2, "Write the decision record docs/decisions/implemented/policy/", False)])
    assert run(rp, tmp_path)["redundant_tasks"] == []


def test_true_duplicate_with_same_file_target_is_still_flagged(rp, tmp_path):
    text = "Register the watchdog hook on PostToolUse and PostToolUseFailure catalog/hooks/settings.json"
    write_plan(tmp_path, "v1.0.1", "alpha", [(1, text, False)])
    write_plan(tmp_path, "v1.0.2", "beta", [(1, text, False)])
    pairs = run(rp, tmp_path)["redundant_tasks"]
    assert len(pairs) == 1 and pairs[0]["shared_target"] == "catalog/hooks/settings.json"


def test_run_record_claims_replace_prose_for_admitted_members_only(rp, tmp_path):
    plans = tmp_path / "docs" / "v9.9" / "plans"
    plans.mkdir(parents=True)
    wide = {"depends_on": [], "read_paths": [], "write_paths": ["shared/a.py"]}
    write_plan(plans, "v9.9.1", "alpha", [(1, "Do alpha work shared/a.py", False)], claims=wide)
    write_plan(plans, "v9.9.2", "beta", [(1, "Do beta work shared/a.py", False)], claims=wide)
    write_plan(plans, "v9.9.3", "gamma", [(1, "Do gamma work other/g.py", False)])
    record = {"schema": 2, "minor": "v9.9", "created": "2026-01-01", "members": [
        {"version": "v9.9.1", "implementation": {"read_paths": [], "write_paths": ["shared/a.py"]}},
        {"version": "v9.9.2", "implementation": {"read_paths": [], "write_paths": ["narrowed/b.py"]}}],
        "minor_amendments": [{"nested": [{"version": "v9.9.3", "implementation": {"read_paths": [], "write_paths": ["amended/c.py"]}}]}]}
    rec_path = tmp_path / "record.json"
    rec_path.write_text(json.dumps(record), encoding="utf-8")
    before = rec_path.read_bytes()
    claims, name = rp.load_record_claims(plans, str(rec_path))
    assert name == "record.json" and set(claims) == {"v9.9.1", "v9.9.2", "v9.9.3"}
    prose = rp.analyze(plans, 3, 0.8, False, False)
    recorded = rp.analyze(plans, 3, 0.8, False, False, False, claims, name)
    assert len(prose["overlaps"]) == 1 and recorded["overlaps"] == []
    assert {p["version"]: p["path_source"] for p in recorded["plans"]} == {v: "run record" for v in claims}
    assert "run record record.json" in rp.render_markdown(recorded)
    assert rec_path.read_bytes() == before


def test_record_lookup_falls_back_to_prose_without_a_record(rp, tmp_path, monkeypatch):
    plans = tmp_path / "v9.9" / "plans"
    plans.mkdir(parents=True)
    runs = tmp_path / "runs"
    runs.mkdir()
    monkeypatch.setenv("NEXUS_HUB_RUNS_DIR", str(runs))
    claims, note = rp.load_record_claims(plans, None)
    assert claims == {} and "no schema 2 run record" in note


def test_claim_blockers_name_directory_claims_and_shared_files_with_a_fix(rp, tmp_path):
    claims_a = {"depends_on": [], "write_paths": ["docs/history/", "scripts/shared.py"], "read_paths": []}
    claims_b = {"depends_on": [], "write_paths": ["docs/history/b.md", "scripts/shared.py"], "read_paths": []}
    write_plan(tmp_path, "v1.0.1", "alpha", [(1, "Edit docs/history/a.md", False)], claims=claims_a)
    write_plan(tmp_path, "v1.0.2", "beta", [(1, "Edit docs/history/b.md", False)], claims=claims_b)
    report = run(rp, tmp_path)
    blockers = {b["path"]: b for b in report["claim_blockers"]}
    assert blockers["docs/history/"]["plans"] == ["v1.0.1", "v1.0.2"]
    assert "narrow" in blockers["docs/history/"]["fix"]
    assert "owns this file" in blockers["scripts/shared.py"]["fix"]
    text = rp.render_markdown(report)
    assert "Claims that block parallel lanes" in text and "Dispatch now" in text


def test_dispatch_now_lists_the_first_conflict_free_wave(rp, tmp_path):
    write_plan(tmp_path, "v1.0.1", "alpha", [(1, "Edit scripts/a.py", False)])
    write_plan(tmp_path, "v1.0.2", "beta", [(1, "Edit scripts/b.py", False)])
    assert run(rp, tmp_path)["dispatch_now"] == ["v1.0.1", "v1.0.2"]
