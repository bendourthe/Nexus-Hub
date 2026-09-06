"""Tests for the Hermes integration subclass (v3.15.2 Phase 5 / A5).

Hermes is a skills-native agent that reads folder-per-skill SKILL.md directly, so
it needs no instruction file: it is a SkillsIntegration (NOT a MarkdownIntegration).
It writes ONLY its native ~/.hermes/skills (global, detection-gated) and .hermes/skills
(project); it reads but does not write the shared ~/.agents/skills (owned by codex)
or the project .agents/skills (seeded by antigravity2's wire_project_surfaces), to
avoid a teardown conflict with the integration that owns each shared path.

These complement the parameterized contract suite (test_contract.py) which exercises
the five lifecycle invariants for every registered key; here we assert Hermes's
platform-specific behavior, reusing the Kimi/Qwen pattern.
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

def test_hermes_registered() -> None:
    assert "hermes" in set(list_keys())


def test_hermes_is_skills_only_not_markdown() -> None:
    """Hermes reads SKILL.md folders directly, so it is a SkillsIntegration with
    NO instruction-file surface (no base-hermes.md, so not a MarkdownIntegration).
    """
    integ = get("hermes")
    assert isinstance(integ, SkillsIntegration)
    assert not isinstance(integ, MarkdownIntegration)
    assert integ.config.get("skills_subdir") == "skills"
    assert integ.config.get("flatten_skills_layout") is True
    assert "instruction_template" not in integ.config


# ---------------------------------------------------------------------------
# Workspace scope
# ---------------------------------------------------------------------------

def test_hermes_workspace_writes_flattened_skills(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    get("hermes").install(_ctx(target, scope="workspace"))
    skills = target / ".hermes" / "skills"
    assert skills.is_dir(), "Hermes must write a flattened .hermes/skills tree"
    assert not (skills / "workflow").is_dir(), "category layer must be flattened away"
    assert (skills / "react-expert" / "SKILL.md").exists(), "a known skill must be present"
    # Each catalog command surfaces as a skill too.
    assert (skills / "implement" / "SKILL.md").exists(), "command-skill missing"
    implement_md = (skills / "implement" / "SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in implement_md


def test_hermes_does_not_write_shared_or_instruction_surfaces(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    get("hermes").install(_ctx(target, scope="workspace"))
    # Hermes reads but never WRITES the shared .agents/ path (antigravity2 owns
    # the project seed; codex owns the global alias) and writes no instruction file.
    assert not (target / ".agents").exists(), "Hermes must not write the shared .agents/ path"
    assert not (target / "AGENTS.md").exists(), "Hermes writes no instruction file"


# ---------------------------------------------------------------------------
# Global scope (detection-gated on ~/.hermes)
# ---------------------------------------------------------------------------

def test_hermes_global_skips_when_not_detected(fake_home: Path) -> None:
    result = get("hermes").install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.detected is False
    assert result.notes, "Hermes global install should skip-with-note when undetected"
    assert not (fake_home / ".hermes").exists()


def test_hermes_global_writes_when_detected(fake_home: Path) -> None:
    (fake_home / ".hermes").mkdir()
    result = get("hermes").install(_ctx(fake_home, scope="global"))
    assert result.detected is True
    assert (fake_home / ".hermes" / "skills").is_dir(), "global install must mirror ~/.hermes/skills"
    assert (fake_home / ".hermes" / "skills" / "react-expert" / "SKILL.md").exists()
    # Hermes does not write the shared ~/.agents/skills alias (codex owns it).
    assert not (fake_home / ".agents").exists(), "Hermes must not write ~/.agents (codex owns the shared alias)"
