"""Unit coverage for runner.py `verify` per-platform read-path checks (v3.11.0 Phase 7.4).

Loads the hyphen-free runner.py by path and exercises the pure `_verify_checks`
helper against fixture HOME / project directories, asserting PASS vs NEEDS-ACTION -
including the Antigravity 2.0 project-only `.agents/` surface (the reported bug).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_RUNNER = (
    Path(__file__).resolve().parents[2]
    / "scripts" / "lib" / "integrations" / "runner.py"
)


def _load_runner():
    spec = importlib.util.spec_from_file_location("nh_runner_verify", _RUNNER)
    assert spec and spec.loader, f"cannot load {_RUNNER}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = _load_runner()


def _by_label(checks):
    return {c[0]: c for c in checks}


def _all_ok(check):
    return all(ok for _, ok in check[1])


def _mk_claude(home: Path, populated: bool) -> None:
    d = home / ".claude"
    (d / "commands").mkdir(parents=True)
    (d / "skills" / "s").mkdir(parents=True)
    if populated:
        (d / "commands" / "x.md").write_text("x", encoding="utf-8")
        (d / "skills" / "s" / "SKILL.md").write_text("s", encoding="utf-8")
        (d / "CLAUDE.md").write_text("# Nexus-Hub Skill Index\n", encoding="utf-8")
    else:
        (d / "CLAUDE.md").write_text("no index here", encoding="utf-8")


def test_claude_pass(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    _mk_claude(home, populated=True)
    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Claude"]
    assert _all_ok(check)


def test_claude_needs_action_when_empty(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    _mk_claude(home, populated=False)
    check = _by_label(runner._verify_checks(home, tmp_path / "proj"))["Claude"]
    assert not _all_ok(check)


def test_antigravity_project_surface_needs_action_then_pass(tmp_path):
    home = tmp_path / "home"
    ag = home / ".gemini" / "antigravity"
    (ag / "skills" / "s").mkdir(parents=True)
    (ag / "workflows").mkdir(parents=True)
    (ag / "workflows" / "c.md").write_text("c", encoding="utf-8")
    proj = tmp_path / "proj"
    proj.mkdir()

    labels = _by_label(runner._verify_checks(home, proj))
    assert _all_ok(labels["Antigravity 2.0 (global)"])
    proj_check = labels["Antigravity 2.0 (this project .agents/)"]
    assert not _all_ok(proj_check)
    assert "nexus-hub init" in (proj_check[2] or "")

    # Seed the project's .agents/workflows -> PASS.
    (proj / ".agents" / "workflows").mkdir(parents=True)
    (proj / ".agents" / "workflows" / "c.md").write_text("c", encoding="utf-8")
    labels2 = _by_label(runner._verify_checks(home, proj))
    assert _all_ok(labels2["Antigravity 2.0 (this project .agents/)"])


def test_no_platforms_detected(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    assert runner._verify_checks(home, tmp_path / "proj") == []
