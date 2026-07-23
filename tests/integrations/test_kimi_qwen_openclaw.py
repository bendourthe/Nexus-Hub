"""Tests for the Kimi, Qwen, and OpenClaw integration subclasses (v3.4.0 Phase 4).

These complement the parameterized contract suite (test_contract.py), which
already exercises the five lifecycle invariants for every registered key. Here
we assert the platform-specific behavior the three A3-ext integrations add,
reusing the Aider/Windsurf pattern proven in Phase 2:

  - all three keys are registered in `_register_builtins()`;
  - OpenClaw remains a behavioral-guardrails surface (MarkdownIntegration, NOT
    SkillsIntegration -> no catalog file-tree mirror);
  - Qwen (reclassified v3.15.0 Phase 4) is now a full skills+commands+agents
    mirror: project-root QWEN.md + .qwen/{skills,agents,commands} at workspace
    scope; ~/.qwen/{QWEN.md,skills,agents,commands} at global scope when ~/.qwen
    is detected, skipping with a note otherwise;
  - Kimi (reclassified v3.15.0 Phase 4) migrated to the current Kimi Code CLI
    product (~/.kimi-code): .kimi-code/{AGENTS.md,skills} at workspace scope;
    ~/.kimi-code/{AGENTS.md,skills} at global scope when ~/.kimi-code is detected.
    The old ~/.kimi/ writes and the .kimi/agent.yaml companion are gone;
  - OpenClaw writes the .openclaw/{AGENTS,SOUL,IDENTITY}.md split at workspace
    scope; global behavior detects ~/.openclaw and writes the trio under
    ~/.openclaw/workspace/ (v3.14.5, the path OpenClaw actually reads).
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


def test_openclaw_behavioral_guardrails_not_skills_mirror() -> None:
    """OpenClaw remains a MarkdownIntegration but NOT SkillsIntegration: it embeds
    the SKILL_INDEX in the instruction file rather than mirroring the catalog tree.
    """
    integ = get("openclaw")
    assert isinstance(integ, MarkdownIntegration)
    assert not isinstance(integ, SkillsIntegration)
    for cfg_key in ("skills_subdir", "commands_subdir", "agents_subdir", "hooks_subdir"):
        assert cfg_key not in integ.config, f"openclaw should not mirror {cfg_key}"


@pytest.mark.parametrize("key", ["qwen", "kimi"])
def test_qwen_kimi_reclassified_to_skills(key: str) -> None:
    """v3.15.0 Phase 4: Qwen and Kimi are now SkillsIntegration (flattened skills
    mirror), reclassified from the old instruction-file-only guardrails surface.
    """
    integ = get(key)
    assert isinstance(integ, MarkdownIntegration)
    assert isinstance(integ, SkillsIntegration)
    assert integ.config.get("skills_subdir") == "skills"
    assert integ.config.get("flatten_skills_layout") is True


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


def test_qwen_workspace_writes_skills_agents_and_markdown_commands(fake_home: Path, tmp_path: Path) -> None:
    """v3.15.0 Phase 4: workspace install also writes flattened .qwen/skills,
    .qwen/agents, and MARKDOWN .qwen/commands (never the deprecated TOML).
    """
    target = tmp_path / "ws"
    target.mkdir()
    get("qwen").install(_ctx(target, scope="workspace"))
    qwen = target / ".qwen"

    skills = qwen / "skills"
    assert skills.is_dir(), "Qwen must write flattened .qwen/skills"
    assert not (skills / "workflow").is_dir(), "category layer must be flattened away"
    assert (qwen / "agents").is_dir() and list((qwen / "agents").glob("*.md")), "agents missing"

    cmds = qwen / "commands"
    assert (cmds / "presentify.md").exists(), "Markdown command mirror missing"
    assert not list(cmds.glob("*.toml")), "Qwen commands must be Markdown, not deprecated TOML"


def test_qwen_global_writes_when_detected(fake_home: Path) -> None:
    (fake_home / ".qwen").mkdir()
    result = get("qwen").install(_ctx(fake_home, scope="global"))

    global_md = fake_home / ".qwen" / "QWEN.md"
    assert global_md.is_file(), "Qwen global QWEN.md must be written when detected"
    assert any(fa.path == str(global_md) for fa in result.files)
    # v3.15.0 Phase 4: global scope also mirrors skills at ~/.qwen/skills.
    assert (fake_home / ".qwen" / "skills").is_dir(), "global install must mirror ~/.qwen/skills"


def test_qwen_global_skips_when_not_detected(fake_home: Path) -> None:
    result = get("qwen").install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.notes, "Qwen global install should skip-with-note when undetected"
    assert not (fake_home / ".qwen").exists()


# ---------------------------------------------------------------------------
# Kimi
# ---------------------------------------------------------------------------


def test_kimi_workspace_writes_agents_md_and_skills(fake_home: Path, tmp_path: Path) -> None:
    # v3.15.0 Phase 4: migrated to Kimi Code CLI (~/.kimi-code). Workspace scope
    # writes .kimi-code/AGENTS.md + a flattened .kimi-code/skills tree; the old
    # .kimi/ writes and the .kimi/agent.yaml companion are gone.
    target = tmp_path / "ws"
    target.mkdir()
    get("kimi").install(_ctx(target, scope="workspace"))

    agents_md = target / ".kimi-code" / "AGENTS.md"
    assert agents_md.is_file(), "Kimi must write .kimi-code/AGENTS.md"
    assert "catalog/skills/" in agents_md.read_text(encoding="utf-8")

    skills = target / ".kimi-code" / "skills"
    assert skills.is_dir(), "Kimi must write a flattened .kimi-code/skills tree"
    assert not (skills / "workflow").is_dir(), "category layer must be flattened away"
    # command-skills reach Kimi as /skill:<name>
    assert (skills / "presentify" / "SKILL.md").exists(), "command-skill missing"

    # The old product surfaces are gone, and .kimi-code/ never clobbers the
    # project-root AGENTS.md that codex/cursor/opencode manage.
    assert not (target / ".kimi").exists(), "old .kimi/ surface must not be written"
    assert not (target / ".kimi-code" / "agent.yaml").exists(), "agent.yaml is dropped"
    assert not (target / "AGENTS.md").exists()


def test_kimi_global_skips_when_not_detected(fake_home: Path) -> None:
    result = get("kimi").install(_ctx(fake_home, scope="global"))
    assert result.files == []
    assert result.notes, "Kimi global install should skip-with-note when undetected"
    assert not (fake_home / ".kimi-code").exists()


def test_kimi_global_writes_when_detected(fake_home: Path) -> None:
    (fake_home / ".kimi-code").mkdir()
    get("kimi").install(_ctx(fake_home, scope="global"))
    assert (fake_home / ".kimi-code" / "AGENTS.md").is_file()
    assert (fake_home / ".kimi-code" / "skills").is_dir()


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


def test_openclaw_global_writes_to_workspace_when_detected(fake_home: Path) -> None:
    # v3.14.5: OpenClaw reads ~/.openclaw/workspace/, not ~/.openclaw/ directly.
    (fake_home / ".openclaw").mkdir()
    get("openclaw").install(_ctx(fake_home, scope="global"))
    ws = fake_home / ".openclaw" / "workspace"
    assert (ws / "AGENTS.md").is_file(), "OpenClaw global must write ~/.openclaw/workspace/AGENTS.md"
    assert (ws / "SOUL.md").is_file()
    assert (ws / "IDENTITY.md").is_file()
    # The trio must NOT land directly under ~/.openclaw/ (the dead path).
    assert not (fake_home / ".openclaw" / "AGENTS.md").exists()
