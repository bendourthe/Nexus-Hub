"""Tests for the Kimi, Qwen, and OpenClaw integration subclasses (v3.4.0 Phase 4).

These complement the parameterized contract suite (test_contract.py), which
already exercises the five lifecycle invariants for every registered key. Here
we assert the platform-specific behavior the three A3-ext integrations add,
reusing the Aider/Windsurf pattern proven in Phase 2:

  - all three keys are registered in `_register_builtins()`;
  - OpenClaw writes its configured workspace-root instruction trio and native
    flattened skills; lifecycle-hook discovery is documented but tool-gating
    remains unsupported without a typed plugin;
  - Qwen (reclassified v3.15.0 Phase 4) is now a full skills+commands+agents
    mirror: project-root QWEN.md + .qwen/{skills,agents,commands} at workspace
    scope; ~/.qwen/{QWEN.md,skills,agents,commands} at global scope when ~/.qwen
    is detected, skipping with a note otherwise;
  - Kimi (reclassified v3.15.0 Phase 4) migrated to the current Kimi Code CLI
    product (~/.kimi-code): .kimi-code/{AGENTS.md,skills} at workspace scope;
    ~/.kimi-code/{AGENTS.md,skills} at global scope when ~/.kimi-code is detected.
    The old ~/.kimi/ writes and the .kimi/agent.yaml companion are gone;
  - global behavior detects ~/.openclaw and honors agents.defaults.workspace.
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
from scripts.lib.integrations.openclaw import (  # noqa: E402
    OpenClawConfigError,
    _read_openclaw_config,
)


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
    for name in (
        "OPENCLAW_HOME",
        "OPENCLAW_STATE_DIR",
        "OPENCLAW_CONFIG_PATH",
        "OPENCLAW_WORKSPACE_DIR",
        "OPENCLAW_INCLUDE_ROOTS",
    ):
        monkeypatch.delenv(name, raising=False)
    return home


# ---------------------------------------------------------------------------
# Registration + classification
# ---------------------------------------------------------------------------


def test_kimi_qwen_openclaw_registered() -> None:
    keys = set(list_keys())
    assert {"kimi", "qwen", "openclaw"}.issubset(keys)


def test_openclaw_uses_native_skills_without_claiming_tool_hooks() -> None:
    integ = get("openclaw")
    assert isinstance(integ, MarkdownIntegration)
    assert isinstance(integ, SkillsIntegration)
    assert integ.config["skills_subdir"] == "skills"
    assert integ.config["flatten_skills_layout"] is True
    assert integ.config["hooks_supported"] is False


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
    qwen_cmd_skill = skills / "presentify" / "SKILL.md"
    assert qwen_cmd_skill.is_file(), "Qwen command-skill missing"
    assert "disable-model-invocation: true" in qwen_cmd_skill.read_text(encoding="utf-8")


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
    kimi_cmd = (skills / "presentify" / "SKILL.md").read_text(encoding="utf-8")
    assert "disable-model-invocation: true" in kimi_cmd

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

    assert (target / "AGENTS.md").is_file()
    assert (target / "SOUL.md").is_file()
    assert (target / "IDENTITY.md").is_file()
    assert "catalog/skills/" in (target / "AGENTS.md").read_text(encoding="utf-8")
    assert "AGENTS.md" in (target / "SOUL.md").read_text(encoding="utf-8")
    skills = target / "skills"
    assert skills.is_dir()
    assert (skills / "presentify" / "SKILL.md").is_file()
    assert not (target / ".openclaw").exists()


def test_openclaw_reports_typed_plugin_hook_gap(fake_home: Path, tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    result = get("openclaw").install(_ctx(target, scope="workspace"))
    assert any("typed plugin" in note for note in result.notes)
    assert not (target / "hooks").exists()


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
    assert (ws / "skills").is_dir()
    # The trio must NOT land directly under ~/.openclaw/ (the dead path).
    assert not (fake_home / ".openclaw" / "AGENTS.md").exists()


def test_openclaw_global_honors_documented_json5_workspace(fake_home: Path) -> None:
    oc = fake_home / ".openclaw"
    oc.mkdir()
    configured = fake_home / "custom-openclaw-workspace"
    (oc / "openclaw.json").write_text(
        "{\n  // documented JSON5 syntax\n  agents: {defaults: {workspace: 'custom-openclaw-workspace',},},\n}",
        encoding="utf-8",
    )
    get("openclaw").install(_ctx(fake_home, scope="global"))
    assert (configured / "AGENTS.md").is_file()
    assert (configured / "skills").is_dir()


def test_openclaw_global_resolves_single_file_workspace_include(
    fake_home: Path,
) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    (state_dir / "agents.json5").write_text(
        "{defaults: {workspace: 'included-workspace'}}",
        encoding="utf-8",
    )
    (state_dir / "openclaw.json").write_text(
        "{agents: {$include: './agents.json5'}}",
        encoding="utf-8",
    )

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    workspace = fake_home / "included-workspace"
    assert result.detected is True
    assert (workspace / "AGENTS.md").is_file()
    assert not (state_dir / "workspace").exists()


def test_openclaw_nested_include_is_relative_to_including_file(
    fake_home: Path,
) -> None:
    state_dir = fake_home / ".openclaw"
    fragments = state_dir / "fragments"
    fragments.mkdir(parents=True)
    (fragments / "defaults.json5").write_text(
        "{workspace: 'nested-workspace'}",
        encoding="utf-8",
    )
    (fragments / "agents.json5").write_text(
        "{defaults: {$include: './defaults.json5'}}",
        encoding="utf-8",
    )
    (state_dir / "openclaw.json").write_text(
        "{agents: {$include: './fragments/agents.json5'}}",
        encoding="utf-8",
    )

    get("openclaw").install(_ctx(fake_home, scope="global"))

    assert (fake_home / "nested-workspace" / "AGENTS.md").is_file()
    assert not (state_dir / "workspace").exists()


def test_openclaw_include_array_deep_merges_in_order(fake_home: Path) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    (state_dir / "base.json5").write_text(
        "{defaults: {workspace: 'base-workspace', model: 'base'}}",
        encoding="utf-8",
    )
    (state_dir / "override.json5").write_text(
        "{defaults: {workspace: 'array-workspace'}}",
        encoding="utf-8",
    )
    (state_dir / "openclaw.json").write_text(
        "{agents: {$include: ['./base.json5', './override.json5']}}",
        encoding="utf-8",
    )

    get("openclaw").install(_ctx(fake_home, scope="global"))

    assert (fake_home / "array-workspace" / "AGENTS.md").is_file()
    assert not (fake_home / "base-workspace").exists()


def test_openclaw_direct_sibling_workspace_overrides_included_workspace(
    fake_home: Path,
) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    (state_dir / "agents.json5").write_text(
        "{defaults: {workspace: 'included-workspace'}}",
        encoding="utf-8",
    )
    (state_dir / "openclaw.json").write_text(
        "{agents: {$include: './agents.json5', defaults: {workspace: 'direct-workspace'}}}",
        encoding="utf-8",
    )

    get("openclaw").install(_ctx(fake_home, scope="global"))

    assert (fake_home / "direct-workspace" / "AGENTS.md").is_file()
    assert not (fake_home / "included-workspace").exists()


def test_openclaw_include_roots_explicitly_allow_external_fragment(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    shared = fake_home / "shared-config"
    shared.mkdir()
    included = shared / "agents.json5"
    included.write_text(
        "{defaults: {workspace: 'include-root-workspace'}}",
        encoding="utf-8",
    )
    (state_dir / "openclaw.json").write_text(
        f"{{agents: {{$include: {str(included)!r}}}}}",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENCLAW_INCLUDE_ROOTS", str(shared))

    get("openclaw").install(_ctx(fake_home, scope="global"))

    assert (fake_home / "include-root-workspace" / "AGENTS.md").is_file()


@pytest.mark.parametrize("failure", ["missing", "malformed", "escape", "cycle"])
def test_openclaw_unsafe_include_never_writes_fallback_workspace(
    fake_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    config_path = state_dir / "openclaw.json"
    external = fake_home / "external-agents.json5"
    external_bytes = b"{defaults: {workspace: 'external-workspace'}}\n"
    external.write_bytes(external_bytes)
    if failure == "missing":
        config_path.write_text(
            "{agents: {$include: './missing.json5'}}", encoding="utf-8"
        )
    elif failure == "malformed":
        (state_dir / "agents.json5").write_text("{defaults: [}", encoding="utf-8")
        config_path.write_text(
            "{agents: {$include: './agents.json5'}}", encoding="utf-8"
        )
    elif failure == "escape":
        config_path.write_text(
            "{agents: {$include: '../external-agents.json5'}}", encoding="utf-8"
        )
    else:
        (state_dir / "agents.json5").write_text(
            "{$include: './openclaw.json'}", encoding="utf-8"
        )
        config_path.write_text(
            "{agents: {$include: './agents.json5'}}", encoding="utf-8"
        )
    trap_workspace = fake_home / "must-not-be-written"
    monkeypatch.setenv("OPENCLAW_WORKSPACE_DIR", str(trap_workspace))

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    assert result.files == []
    assert result.detected is False
    assert any("config" in note.lower() and "skipped" in note.lower() for note in result.notes)
    assert not trap_workspace.exists()
    assert not (state_dir / "workspace").exists()
    assert external.read_bytes() == external_bytes


def test_openclaw_include_depth_is_bounded(tmp_path: Path) -> None:
    for index in range(11):
        next_name = f"layer-{index + 1}.json5"
        (tmp_path / f"layer-{index}.json5").write_text(
            f"{{$include: './{next_name}'}}",
            encoding="utf-8",
        )
    (tmp_path / "layer-11.json5").write_text("{}", encoding="utf-8")

    with pytest.raises(OpenClawConfigError, match="depth"):
        _read_openclaw_config(tmp_path / "layer-0.json5", required=True)


def test_openclaw_include_total_size_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "openclaw.json"
    included = tmp_path / "agents.json5"
    config_path.write_text("{$include: './agents.json5'}", encoding="utf-8")
    included.write_text("{padding: '0123456789'}", encoding="utf-8")
    monkeypatch.setattr(
        "scripts.lib.integrations.openclaw._MAX_CONFIG_TOTAL_BYTES",
        config_path.stat().st_size + included.stat().st_size - 1,
    )

    with pytest.raises(OpenClawConfigError, match="size"):
        _read_openclaw_config(config_path, required=True)


def _openclaw_workspace_config_with_size(size: int, workspace: str) -> str:
    prefix = f"{{defaults: {{workspace: '{workspace}'}}, padding: '"
    suffix = "'}"
    padding_size = size - len((prefix + suffix).encode("utf-8"))
    assert padding_size >= 0
    payload = prefix + ("x" * padding_size) + suffix
    assert len(payload.encode("utf-8")) == size
    return payload


def test_openclaw_include_file_size_accepts_exactly_two_mib(fake_home: Path) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    included = state_dir / "agents.json5"
    included.write_text(
        _openclaw_workspace_config_with_size(
            2 * 1024 * 1024, "exact-limit-workspace"
        ),
        encoding="utf-8",
    )
    (state_dir / "openclaw.json").write_text(
        "{agents: {$include: './agents.json5'}}", encoding="utf-8"
    )

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    assert result.detected is True
    assert (fake_home / "exact-limit-workspace" / "AGENTS.md").is_file()
    assert not (state_dir / "workspace").exists()


def test_openclaw_include_file_size_rejects_two_mib_plus_one_without_writes(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    included = state_dir / "agents.json5"
    included.write_text(
        _openclaw_workspace_config_with_size(
            (2 * 1024 * 1024) + 1, "oversized-include-workspace"
        ),
        encoding="utf-8",
    )
    (state_dir / "openclaw.json").write_text(
        "{agents: {$include: './agents.json5'}}", encoding="utf-8"
    )
    fallback = fake_home / "must-not-be-written"
    monkeypatch.setenv("OPENCLAW_WORKSPACE_DIR", str(fallback))

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    assert result.detected is False
    assert result.files == []
    assert any("size limit" in note for note in result.notes)
    assert not fallback.exists()
    assert not (state_dir / "workspace").exists()
    assert not (fake_home / "oversized-include-workspace").exists()


def test_openclaw_json5_rejects_unterminated_block_comment(tmp_path: Path) -> None:
    config_path = tmp_path / "openclaw.json"
    config_path.write_text("{agents: {defaults: {}}} /* unterminated", encoding="utf-8")

    with pytest.raises(OpenClawConfigError, match="unterminated block comment"):
        _read_openclaw_config(config_path)


def test_openclaw_explicit_unterminated_comment_config_makes_zero_writes(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = fake_home / "service-config" / "openclaw.json5"
    config_path.parent.mkdir()
    trap_workspace = fake_home / "must-not-be-written"
    config_path.write_text(
        "{agents: {defaults: {workspace: 'must-not-be-written'}}} /* unterminated",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(config_path))

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    assert result.files == []
    assert result.detected is False
    assert any("config" in note.lower() and "skipped" in note.lower() for note in result.notes)
    assert not trap_workspace.exists()


def test_openclaw_global_resolves_tilde_through_configured_home(fake_home: Path) -> None:
    oc = fake_home / ".openclaw"
    oc.mkdir()
    (oc / "openclaw.json").write_text(
        '{"agents": {"defaults": {"workspace": "~/custom-openclaw-workspace"}}}',
        encoding="utf-8",
    )

    get("openclaw").install(_ctx(fake_home, scope="global"))

    configured = fake_home / "custom-openclaw-workspace"
    assert (configured / "AGENTS.md").is_file()
    assert (configured / "skills").is_dir()


def test_openclaw_config_workspace_wins_over_workspace_env(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    oc = fake_home / ".openclaw"
    oc.mkdir()
    configured = fake_home / "configured-workspace"
    env_workspace = fake_home / "environment-workspace"
    (oc / "openclaw.json").write_text(
        "{agents: {defaults: {workspace: 'configured-workspace'}}}",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENCLAW_WORKSPACE_DIR", str(env_workspace))

    get("openclaw").install(_ctx(fake_home, scope="global"))

    assert (configured / "AGENTS.md").is_file()
    assert not env_workspace.exists()


def test_openclaw_global_honors_explicit_config_path(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = fake_home / "service-config" / "gateway.json5"
    config_path.parent.mkdir()
    configured = fake_home / "configured-from-override"
    config_path.write_text(
        "{agents: {defaults: {workspace: 'configured-from-override'}}}",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(config_path))

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    assert result.detected is True
    assert (configured / "AGENTS.md").is_file()
    assert not (fake_home / ".openclaw").exists()


def test_openclaw_global_honors_state_dir_fallback(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state_dir = fake_home / "service-state"
    monkeypatch.setenv("OPENCLAW_STATE_DIR", str(state_dir))

    get("openclaw").install(_ctx(fake_home, scope="global"))

    assert (state_dir / "workspace" / "AGENTS.md").is_file()
    assert not (fake_home / ".openclaw").exists()


def test_openclaw_global_honors_openclaw_home_default(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    openclaw_home = fake_home / "service-home"
    monkeypatch.setenv("OPENCLAW_HOME", str(openclaw_home))

    get("openclaw").install(_ctx(fake_home, scope="global"))

    assert (openclaw_home / ".openclaw" / "workspace" / "AGENTS.md").is_file()
    assert not (fake_home / ".openclaw").exists()


def test_openclaw_global_honors_workspace_env_without_default_root(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    configured = fake_home / "workspace-from-environment"
    monkeypatch.setenv("OPENCLAW_WORKSPACE_DIR", str(configured))

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    assert result.detected is True
    assert (configured / "AGENTS.md").is_file()
    assert not (fake_home / ".openclaw").exists()


@pytest.mark.parametrize(
    ("config_body", "explicit_config"),
    [
        ("{agents: {defaults: {workspace: 'unterminated}}}", False),
        ("{agents: {defaults: {workspace: []}}}", False),
        (None, True),
    ],
)
def test_openclaw_invalid_selected_config_never_writes_fallback_workspace(
    fake_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    config_body: str | None,
    explicit_config: bool,
) -> None:
    state_dir = fake_home / ".openclaw"
    state_dir.mkdir()
    config_path = state_dir / "openclaw.json"
    if config_body is not None:
        config_path.write_text(config_body, encoding="utf-8")
    if explicit_config:
        config_path = fake_home / "missing-config.json5"
        monkeypatch.setenv("OPENCLAW_CONFIG_PATH", str(config_path))
    trap_workspace = fake_home / "must-not-be-written"
    monkeypatch.setenv("OPENCLAW_WORKSPACE_DIR", str(trap_workspace))

    result = get("openclaw").install(_ctx(fake_home, scope="global"))

    assert result.files == []
    assert result.detected is False
    assert any("config" in note.lower() and "skipped" in note.lower() for note in result.notes)
    assert not trap_workspace.exists()
    assert not (state_dir / "workspace").exists()
