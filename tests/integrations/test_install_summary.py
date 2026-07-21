"""Tests for the structured per-platform install summary (v3.14.5 Phase 1).

The installer runs `runner.py install --quiet` and needs a structured,
per-surface view of what each platform installed so it can render a checklist
(and group undetected platforms) instead of an unconditional "Installed" line.
This suite covers:

* `WriteResult.mark_not_detected` / `.detected` and its propagation through
  `.extend`;
* `_classify_surface` path -> canonical-surface mapping (including the
  load-bearing `.agents/skills` -> skills and instruction-file-first rules);
* `_common_path` representative-path selection;
* `_build_platform_summary` shaping a WriteResult into the summary dict;
* `cmd_install --summary-json`: a detected platform reports `installed`
  surfaces with real paths; an undetected platform (absent `~/.kimi-code`) reports
  `detected: false` with no surfaces; and `--quiet` stdout stays free of the
  per-file action lines while the summary file is still written.

Follows the import + fake_home monkeypatch conventions in
test_runner_target_root.py and test_kimi_qwen_openclaw.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import runner  # noqa: E402
from scripts.lib.integrations.result import WriteResult  # noqa: E402


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


def _install_args(**overrides) -> argparse.Namespace:
    """Build a fully-populated Namespace for cmd_install (all attrs it reads)."""
    base = dict(
        integrations="kimi",
        target=None,
        scope="global",
        overwrite=False,
        dry_run=True,
        quiet=True,
        project_name=None,
        var=None,
        languages=None,
        instruction_only=False,
        summary_json=None,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


class _StubInteg:
    """A stub integration returning a hand-built WriteResult, so the summary
    plumbing is exercised deterministically without walking the real catalog."""

    key = "codex"  # a registered key so _resolve_integration_keys accepts it
    display_name = "Stub"
    config = {"instruction_file": "AGENTS.md"}

    def __init__(self, result: WriteResult) -> None:
        self._result = result

    def install(self, ctx) -> WriteResult:  # noqa: ANN001 - test double
        return self._result


# ---------------------------------------------------------------------------
# WriteResult.detected / mark_not_detected
# ---------------------------------------------------------------------------


def test_mark_not_detected_sets_flag_and_appends_note() -> None:
    wr = WriteResult()
    assert wr.detected is None
    wr.mark_not_detected("tool not found; skipped")
    assert wr.detected is False
    assert "tool not found; skipped" in wr.notes


def test_extend_carries_detection_when_self_undecided() -> None:
    a, b = WriteResult(), WriteResult()
    b.detected = False
    a.extend(b)
    assert a.detected is False


def test_extend_keeps_explicit_self_detection() -> None:
    a, b = WriteResult(), WriteResult()
    a.detected = True
    b.detected = False
    a.extend(b)
    assert a.detected is True  # an explicit value on self always wins


# ---------------------------------------------------------------------------
# _classify_surface
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path, instruction_file, expected",
    [
        ("/home/u/.claude/CLAUDE.md", "CLAUDE.md", "instruction"),
        ("/home/u/.claude/skills/foo", None, "skills"),
        # .agents/skills MUST classify as skills, not agents (order is load-bearing).
        ("/home/u/.agents/skills/bar", "AGENTS.md", "skills"),
        ("/home/u/.gemini/workflows/x.md", None, "commands"),
        ("/home/u/.codex/prompts/y.md", None, "commands"),
        ("/home/u/.gemini/commands/z.toml", None, "commands"),
        ("/home/u/prompts/p.prompt.md", None, "commands"),
        ("/home/u/.claude/agents/a.md", None, "agents"),
        ("/home/u/.gemini/subagents/s.md", None, "agents"),
        ("/home/u/.cursor/rules/r.mdc", None, "rules"),
        ("/home/u/.claude/settings.json", None, "settings"),
        ("/home/u/.cursor/hooks.json", None, "hooks"),
        ("/home/u/.claude/hooks/git.sh", None, "hooks"),
        # instruction-file match wins over the .windsurfrules rules heuristic.
        ("/home/u/proj/.windsurfrules", ".windsurfrules", "instruction"),
        ("/home/u/proj/.windsurfrules", None, "rules"),
        ("/home/u/random/thing.txt", None, None),
    ],
)
def test_classify_surface(path: str, instruction_file, expected) -> None:
    assert runner._classify_surface(path, instruction_file) == expected


# ---------------------------------------------------------------------------
# _common_path
# ---------------------------------------------------------------------------


def test_surface_root_trims_to_surface_dir() -> None:
    # A deep command-skill file and a flattened skill dir both trim to the
    # surface directory, so the distinct-roots set stays meaningful.
    deep = os.path.join("h", ".codex", "skills", "commit", "SKILL.md")
    shallow = os.path.join("h", ".codex", "skills", "foo")
    assert runner._surface_root(deep, "skills") == os.path.join("h", ".codex", "skills")
    assert runner._surface_root(shallow, "skills") == os.path.join("h", ".codex", "skills")
    # File surfaces (instruction, settings) return the path unchanged.
    inst = os.path.join("h", ".codex", "AGENTS.md")
    assert runner._surface_root(inst, "instruction") == inst


def test_join_distinct_multi_root() -> None:
    # A surface spanning two roots (Codex skills) lists both, deduped.
    a = os.path.join("h", ".codex", "skills")
    b = os.path.join("h", ".agents", "skills")
    assert runner._join_distinct([a, a, b]) == a + ", " + b
    assert runner._join_distinct([]) == ""
    assert runner._join_distinct(["/only"]) == "/only"


# ---------------------------------------------------------------------------
# _build_platform_summary
# ---------------------------------------------------------------------------


def test_build_platform_summary_groups_surfaces() -> None:
    skills_dir = os.path.join("home", ".codex", "skills")
    wr = WriteResult()
    wr.add(os.path.join("home", ".codex", "AGENTS.md"), "created")
    wr.add(os.path.join(skills_dir, "a"), "created")
    wr.add(os.path.join(skills_dir, "b"), "unchanged")
    wr.add(os.path.join("home", ".codex", "workflows", "w.md"), "created")

    summary = runner._build_platform_summary("codex", _StubInteg(wr), wr)

    assert summary["platform"] == "codex"
    assert summary["detected"] is None
    assert summary["surfaces"]["instruction"]["status"] == "installed"
    assert summary["surfaces"]["skills"]["status"] == "installed"
    assert summary["surfaces"]["skills"]["path"] == skills_dir
    assert summary["surfaces"]["commands"]["status"] == "installed"


def test_build_platform_summary_carries_not_detected() -> None:
    wr = WriteResult()
    wr.mark_not_detected("skipped")
    summary = runner._build_platform_summary("codex", _StubInteg(wr), wr)
    assert summary["detected"] is False
    assert summary["surfaces"] == {}  # nothing written -> no surface rows


# ---------------------------------------------------------------------------
# cmd_install --summary-json
# ---------------------------------------------------------------------------


def test_summary_json_reports_installed_surfaces(
    fake_home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A detected platform (stub with real FileActions) reports installed
    surfaces with paths in the summary file."""
    wr = WriteResult()
    wr.add(str(fake_home / ".codex" / "AGENTS.md"), "created")
    wr.add(str(fake_home / ".codex" / "skills" / "s"), "created")
    monkeypatch.setattr(runner, "get", lambda key: _StubInteg(wr))

    summary_path = tmp_path / "summary.json"
    rc = runner.cmd_install(
        _install_args(integrations="codex", summary_json=str(summary_path))
    )

    assert rc == 0
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["scope"] == "global"
    codex = next(p for p in data["platforms"] if p["platform"] == "codex")
    assert codex["surfaces"]["skills"]["status"] == "installed"
    # The skill leaf (~/.codex/skills/s) trims to the surface directory.
    assert codex["surfaces"]["skills"]["path"] == str(fake_home / ".codex" / "skills")
    assert codex["surfaces"]["instruction"]["status"] == "installed"


def test_summary_json_marks_undetected_platform(
    fake_home: Path, tmp_path: Path
) -> None:
    """A real detection-gated platform with its config root absent reports
    detected: false and no surfaces (the group-me-as-skipped signal)."""
    summary_path = tmp_path / "summary.json"
    # v3.15.0 Phase 4: Kimi migrated to Kimi Code CLI; detection is gated on
    # ~/.kimi-code (not the old ~/.kimi).
    assert not (fake_home / ".kimi-code").exists()

    rc = runner.cmd_install(
        _install_args(integrations="kimi", summary_json=str(summary_path))
    )

    assert rc == 0
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    kimi = next(p for p in data["platforms"] if p["platform"] == "kimi")
    assert kimi["detected"] is False
    assert kimi["surfaces"] == {}


# ---------------------------------------------------------------------------
# Newly-parity checklist surfaces (v3.15.0 Phase 6)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key, expected_surfaces",
    [
        ("cursor", {"skills", "commands", "agents", "hooks", "rules", "instruction"}),
        ("opencode", {"skills", "commands", "agents", "rules", "instruction"}),
        ("qwen", {"skills", "commands", "agents", "instruction"}),
        ("kimi", {"skills", "instruction"}),
    ],
)
def test_newly_parity_summary_surfaces(key, expected_surfaces, tmp_path: Path) -> None:
    """v3.15.0 Phase 6: the summary-driven checklist captures the parity surfaces
    added in Phases 2-4 for each newly-parity platform (dry-run, real integrations)."""
    from scripts.lib.integrations import get
    from scripts.lib.integrations.base import InstallContext
    from scripts.lib.integrations.manifest import InstallManifest

    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=tmp_path,
        scope="workspace",
        dry_run=True,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "t"},
    )
    integ = get(key)
    summary = runner._build_platform_summary(key, integ, integ.install(ctx))
    got = set(summary.get("surfaces", {}).keys())
    assert expected_surfaces <= got, f"{key}: missing surfaces {expected_surfaces - got}"
    for surf, info in summary["surfaces"].items():
        assert info["status"] == "installed", f"{key}: {surf} status={info['status']!r}"


def test_quiet_output_unchanged_but_summary_written(
    fake_home: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--quiet suppresses the per-file action lines (unchanged behavior) while
    the summary file is still written from the WriteResult."""
    wr = WriteResult()
    wr.add(str(fake_home / ".codex" / "AGENTS.md"), "created")
    monkeypatch.setattr(runner, "get", lambda key: _StubInteg(wr))

    summary_path = tmp_path / "summary.json"
    runner.cmd_install(
        _install_args(integrations="codex", quiet=True, summary_json=str(summary_path))
    )

    out = capsys.readouterr().out
    # None of the per-file action prefixes leak to stdout under --quiet.
    for prefix in ("[+]", "[~]", "[=]", "[install:", "(note)"):
        assert prefix not in out
    assert summary_path.is_file()
