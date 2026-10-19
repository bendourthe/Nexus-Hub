"""Claude alias pins must not become invalid model IDs on other hosts."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import tomllib
import yaml

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext


@pytest.mark.parametrize(
    "key",
    [
        "claude",
        "codex",
        "cursor",
        "opencode",
        "gemini",
        "gemini-cli",
        "qwen",
        "copilot",
        "antigravity2",
    ],
)
@pytest.mark.parametrize("scope", ["workspace", "global"])
def test_catalog_model_alias_is_claude_only(
    install_ctx: InstallContext, monkeypatch: pytest.MonkeyPatch, key: str, scope: str
):
    repo = install_ctx.target_root / "source"
    agents = repo / "catalog/agents"
    agents.mkdir(parents=True)
    body = "A reasoning-sensitive probe.\n\nmodel: body text must remain\n"
    (agents / "pinning-probe.md").write_text(
        "---\nname: pinning-probe\ndescription: Model compatibility probe\nmodel: opus\ntools: Read, Glob\n---\n\n"
        + body,
        encoding="utf-8",
    )
    target = install_ctx.target_root / "destination"
    target.mkdir()
    if scope == "global" and key in {"qwen", "copilot"}:
        (target / f".{key}").mkdir()
    monkeypatch.setenv("NEXUS_HUB_HOME", str(install_ctx.target_root / "nexus-state"))
    monkeypatch.setattr(
        "scripts.lib.integrations.copilot._vscode_user_dir", lambda *args: None
    )
    integ = get(key)
    template = integ.config.get("instruction_template")
    if template:
        path = repo / template
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# Probe project\n", encoding="utf-8")
    ctx = replace(
        install_ctx,
        repo_root=repo,
        target_root=target,
        scope=scope,
        explicit_target=True,
    )
    integ.install(ctx)
    delivered = [p for p in target.rglob("pinning-probe.*") if p.is_file()]
    assert len(delivered) == 1, delivered
    text = delivered[0].read_text(encoding="utf-8")
    if key == "codex":
        meta = tomllib.loads(text)
        assert meta["developer_instructions"] == body
    else:
        _, front, prompt = text.split("---", 2)
        meta = yaml.safe_load(front)
        assert prompt.lstrip("\n") == body
        assert meta["description"] == "Model compatibility probe"
    if key == "claude":
        assert meta["model"] == "opus"
    else:
        assert "model" not in meta, (key, meta)


def test_session_default_is_still_opus():
    root = Path(__file__).resolve().parents[2]
    defaults = json.loads(
        (root / "configs/platform-defaults.json").read_text(encoding="utf-8")
    )
    assert defaults["platforms"]["claude"]["settings"]["model"] == "opus"
