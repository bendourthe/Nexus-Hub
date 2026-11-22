"""Claude-only agent keys (model alias, effort ceiling) must reach Claude alone."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import tomllib
import yaml

from scripts.lib.integrations import get, list_keys
from scripts.lib.integrations._catalog_adapters import CLAUDE_ONLY_AGENT_KEYS
from scripts.lib.integrations._kimi_native import KIMI_DROPPED_AGENT_KEYS
from scripts.lib.integrations.base import InstallContext


def _agent_receiving_keys() -> list[str]:
    """Every registered integration that delivers catalog agents.

    Declared ``agents_subdir`` covers the base mirror; an ``_install_agents``
    method covers adapters that write agents themselves (Kimi, Copilot).
    """
    return sorted(
        key
        for key in list_keys()
        if get(key).config.get("agents_subdir")
        or callable(getattr(get(key), "_install_agents", None))
    )


AGENT_RECEIVING_KEYS = _agent_receiving_keys()


@pytest.mark.parametrize("key", AGENT_RECEIVING_KEYS)
@pytest.mark.parametrize("scope", ["workspace", "global"])
def test_claude_only_agent_keys_reach_claude_alone(
    install_ctx: InstallContext, monkeypatch: pytest.MonkeyPatch, key: str, scope: str, fake_tools
):
    repo = install_ctx.target_root / "source"
    agents = repo / "catalog/agents"
    agents.mkdir(parents=True)
    body = (
        "A reasoning-sensitive probe.\n\nmodel: body text must remain\n"
        "effort: body text must remain\n"
    )
    (agents / "pinning-probe.md").write_text(
        "---\nname: pinning-probe\ndescription: Model compatibility probe\nmodel: opus\neffort: high\ntools: Read, Glob\n---\n\n"
        + body,
        encoding="utf-8",
    )
    target = install_ctx.target_root / "destination"
    target.mkdir()
    if scope == "global" and key in {"qwen", "copilot"}:
        (target / f".{key}").mkdir()
    if scope == "global" and key == "nexus-ai":
        (target / ".nexus" / "sessions").mkdir(parents=True)  # vendor-root evidence
    if scope == "global":
        fake_tools(key)  # v4.14.7: gated platforms need detection evidence
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
        assert meta["effort"] == "high"
        return
    for claude_key in CLAUDE_ONLY_AGENT_KEYS:
        if key == "kimi" and claude_key not in KIMI_DROPPED_AGENT_KEYS:
            # Recorded decision: Kimi documents ignoring Claude Code's model.
            continue
        assert claude_key not in meta, (key, claude_key, meta)


def test_roster_covers_every_agent_receiving_integration():
    assert {"claude", "kimi", "nexus-ai", "copilot"} <= set(AGENT_RECEIVING_KEYS)


def test_kimi_strips_every_claude_only_key_it_does_not_document():
    assert set(KIMI_DROPPED_AGENT_KEYS) == set(CLAUDE_ONLY_AGENT_KEYS) - {"model"}


def test_session_default_is_still_opus():
    root = Path(__file__).resolve().parents[2]
    defaults = json.loads(
        (root / "configs/platform-defaults.json").read_text(encoding="utf-8")
    )
    assert defaults["platforms"]["claude"]["settings"]["model"] == "opus"
