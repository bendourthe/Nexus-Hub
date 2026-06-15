"""Tests for the Kimi, Qwen, and OpenClaw integration subclasses (v3.4.0 Phase 4).

These complement the parameterized contract suite (test_contract.py), which
already exercises the five lifecycle invariants for every registered key. Here
we assert the platform-specific behavior the three A3-ext integrations add,
reusing the Aider/Windsurf pattern proven in Phase 2:

  - all three keys are registered in `_register_builtins()`;
  - all three are behavioral-guardrails surfaces (MarkdownIntegration, NOT
    SkillsIntegration -> no catalog file-tree mirror);
  - Qwen writes a project-root QWEN.md at workspace scope; at global scope it
    writes ~/.qwen/QWEN.md only when Qwen is detected (~/.qwen present),
    skipping with a note otherwise;
  - Kimi writes a .kimi/system.md (marker-merged) + .kimi/agent.yaml companion
    at workspace scope; global behavior detects ~/.kimi;
  - OpenClaw writes the .openclaw/{AGENTS,SOUL,IDENTITY}.md split at workspace
    scope; global behavior detects ~/.openclaw.
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


def test_kimi_qwen_openclaw_registered() -> None:
    keys = set(list_keys())
    assert {"kimi", "qwen", "openclaw"}.issubset(keys)


@pytest.mark.parametrize("key", ["kimi", "qwen", "openclaw"])
def test_behavioral_guardrails_not_skills_mirror(key: str) -> None:
    """All three are MarkdownIntegration but NOT SkillsIntegration: they embed
    the SKILL_INDEX in the instruction file rather than mirroring the catalog
    tree.
    """
    integ = get(key)
    assert isinstance(integ, MarkdownIntegration)
    assert not isinstance(integ, SkillsIntegration)
    for cfg_key in ("skills_subdir", "commands_subdir", "agents_subdir", "hooks_subdir"):
        assert cfg_key not in integ.config, f"{key} should not mirror {cfg_key}"


# ---------------------------------------------------------------------------
# Qwen
# ---------------------------------------------------------------------------


def test_qwen_workspace_writes_root_qwen_md(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    result = get("qwen").install(_ctx(target, scope="workspace"))

    qwen_md = target / "QWEN.md"
    assert qwen_md.is_file(), "Qwen must write a project-root QWEN.md"
    body = qwen_md.read_text(encoding="utf-8")
    assert "catalog/skills/" in body  # SKILL_INDEX substituted
    assert "test-project" in body
    assert any(fa.path == str(qwen_md) for fa in result.files)


def test_qwen_global_writes_when_detected(fake_home: Path) -> None:
    (fake_home / ".qwen").mkdir()
    result = get("qwen").install(_ctx(fake_home, scope="global"))

    global_md = fake_home / ".qwen" / "QWEN.md"
    assert global_md.is_file(), "Qwen global QWEN.md must be written when detected"
    assert any(fa.path == str(global_md) for fa in result.files)


def test_qwen_global_skips_when_not_detected(fake_home: Path) -> None:
    result = get("qwen").install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.notes, "Qwen global install should skip-with-note when undetected"
    assert not (fake_home / ".qwen").exists()


# ---------------------------------------------------------------------------
# Kimi
# ---------------------------------------------------------------------------


def test_kimi_workspace_writes_system_and_agent_yaml(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    get("kimi").install(_ctx(target, scope="workspace"))

    system_md = target / ".kimi" / "system.md"
    agent_yaml = target / ".kimi" / "agent.yaml"
    assert system_md.is_file(), "Kimi must write .kimi/system.md"
    assert agent_yaml.is_file(), "Kimi must write .kimi/agent.yaml"
    assert "catalog/skills/" in system_md.read_text(encoding="utf-8")
    assert "system_prompt_file: system.md" in agent_yaml.read_text(encoding="utf-8")


def test_kimi_global_skips_when_not_detected(fake_home: Path) -> None:
    result = get("kimi").install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.notes, "Kimi global install should skip-with-note when undetected"
    assert not (fake_home / ".kimi").exists()


def test_kimi_global_writes_when_detected(fake_home: Path) -> None:
    (fake_home / ".kimi").mkdir()
    get("kimi").install(_ctx(fake_home, scope="global"))
    assert (fake_home / ".kimi" / "system.md").is_file()
    assert (fake_home / ".kimi" / "agent.yaml").is_file()


# ---------------------------------------------------------------------------
# OpenClaw
# ---------------------------------------------------------------------------


def test_openclaw_workspace_writes_three_file_split(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    get("openclaw").install(_ctx(target, scope="workspace"))

    oc = target / ".openclaw"
    assert (oc / "AGENTS.md").is_file(), "OpenClaw must write .openclaw/AGENTS.md"
    assert (oc / "SOUL.md").is_file(), "OpenClaw must write .openclaw/SOUL.md"
    assert (oc / "IDENTITY.md").is_file(), "OpenClaw must write .openclaw/IDENTITY.md"
    # The instruction content (with SKILL_INDEX) lives in AGENTS.md; companions
    # point at it.
    assert "catalog/skills/" in (oc / "AGENTS.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in (oc / "SOUL.md").read_text(encoding="utf-8")


def test_openclaw_namespaced_dir_does_not_touch_root_agents(fake_home: Path, tmp_path: Path) -> None:
    """OpenClaw writes under .openclaw/ so it never clobbers a project-root
    AGENTS.md (which other integrations such as opencode/cursor manage).
    """
    target = tmp_path / "ws"
    target.mkdir()
    get("openclaw").install(_ctx(target, scope="workspace"))
    assert not (target / "AGENTS.md").exists()


def test_openclaw_global_skips_when_not_detected(fake_home: Path) -> None:
    result = get("openclaw").install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.notes, "OpenClaw global install should skip-with-note when undetected"
    assert not (fake_home / ".openclaw").exists()
