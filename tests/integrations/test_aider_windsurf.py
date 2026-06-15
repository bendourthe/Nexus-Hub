"""Tests for the Aider and Windsurf integration subclasses (v3.4.0 Phase 2).

These complement the parameterized contract suite (test_contract.py), which
already exercises the five lifecycle invariants for every registered key. Here
we assert the platform-specific behavior:

  - both keys are registered in `_register_builtins()`;
  - both are behavioral-guardrails surfaces (MarkdownIntegration, NOT
    SkillsIntegration -> no catalog file-tree mirror);
  - Aider writes a project-root CONVENTIONS.md at workspace scope and is a
    no-op-with-note at global scope;
  - Windsurf writes a project-root .windsurfrules at workspace scope, and at
    global scope writes ~/.codeium/windsurf/memories/global_rules.md only when
    Windsurf is detected (~/.codeium present), skipping with a note otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import get, list_keys  # noqa: E402
from scripts.lib.integrations.base import (  # noqa: E402
    InstallContext,
    MarkdownIntegration,
    SkillsIntegration,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


def _ctx(target: Path, scope: str = "workspace") -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope=scope,
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test-project"},
    )


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    return home


# ---------------------------------------------------------------------------
# Registration + classification
# ---------------------------------------------------------------------------


def test_aider_and_windsurf_registered() -> None:
    keys = set(list_keys())
    assert {"aider", "windsurf"}.issubset(keys)


@pytest.mark.parametrize("key", ["aider", "windsurf"])
def test_behavioral_guardrails_not_skills_mirror(key: str) -> None:
    """Both are MarkdownIntegration but NOT SkillsIntegration: they embed the
    SKILL_INDEX in the instruction file rather than mirroring the catalog tree.
    """
    integ = get(key)
    assert isinstance(integ, MarkdownIntegration)
    assert not isinstance(integ, SkillsIntegration)
    # No catalog-mirror subdirs configured.
    for cfg_key in ("skills_subdir", "commands_subdir", "agents_subdir", "hooks_subdir"):
        assert cfg_key not in integ.config, f"{key} should not mirror {cfg_key}"


# ---------------------------------------------------------------------------
# Aider
# ---------------------------------------------------------------------------


def test_aider_workspace_writes_root_conventions(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    integ = get("aider")
    result = integ.install(_ctx(target, scope="workspace"))

    conventions = target / "CONVENTIONS.md"
    assert conventions.is_file(), "Aider must write a project-root CONVENTIONS.md"
    body = conventions.read_text(encoding="utf-8")
    # The SKILL_INDEX block is embedded (a known index row proves substitution ran).
    assert "catalog/skills/" in body
    assert "test-project" in body
    assert any(fa.path == str(conventions) for fa in result.files)


def test_aider_global_is_noop_with_note(fake_home: Path, tmp_path: Path) -> None:
    integ = get("aider")
    result = integ.install(_ctx(tmp_path, scope="global"))
    assert result.files == [], "Aider has no global instruction surface"
    assert result.notes, "Aider global install should explain the no-op via a note"


# ---------------------------------------------------------------------------
# Windsurf
# ---------------------------------------------------------------------------


def test_windsurf_workspace_writes_root_windsurfrules(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    integ = get("windsurf")
    integ.install(_ctx(target, scope="workspace"))

    rules = target / ".windsurfrules"
    assert rules.is_file(), "Windsurf must write a project-root .windsurfrules"
    body = rules.read_text(encoding="utf-8")
    assert "catalog/skills/" in body


def test_windsurf_global_writes_when_detected(fake_home: Path) -> None:
    # Simulate Windsurf installed: the ~/.codeium config root exists.
    (fake_home / ".codeium").mkdir()
    integ = get("windsurf")
    result = integ.install(_ctx(fake_home, scope="global"))

    global_rules = fake_home / ".codeium" / "windsurf" / "memories" / "global_rules.md"
    assert global_rules.is_file(), "Windsurf global rules must be written when detected"
    assert any(fa.path == str(global_rules) for fa in result.files)


def test_windsurf_global_skips_when_not_detected(fake_home: Path) -> None:
    # ~/.codeium absent -> Windsurf not installed -> skip with a note.
    integ = get("windsurf")
    result = integ.install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.notes, "Windsurf global install should skip-with-note when undetected"
    assert not (fake_home / ".codeium").exists()
