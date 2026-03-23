from __future__ import annotations

import os
from pathlib import Path

from devai_skill_server.config import ServerConfig, resolve_config


def test_resolve_with_env_var(sample_skills_json: Path, monkeypatch):
    """Hub root resolves from DEVAI_HUB_ROOT env var."""
    monkeypatch.setenv("DEVAI_HUB_ROOT", str(sample_skills_json))
    config = resolve_config()
    assert config.hub_root == sample_skills_json
    assert config.skills_json_path is not None
    assert config.skills_json_path.exists()


def test_resolve_with_invalid_env_var(tmp_path: Path, monkeypatch):
    """Invalid DEVAI_HUB_ROOT falls through to other resolution methods."""
    monkeypatch.setenv("DEVAI_HUB_ROOT", str(tmp_path / "nonexistent"))
    config = resolve_config()
    # hub_root may be None or found via another method, but should not crash
    assert isinstance(config, ServerConfig)


def test_resolve_embedding_provider(monkeypatch):
    """Embedding provider reads from env var."""
    monkeypatch.setenv("DEVAI_EMBEDDING_PROVIDER", "openai")
    monkeypatch.delenv("DEVAI_HUB_ROOT", raising=False)
    config = resolve_config()
    assert config.embedding_provider == "openai"


def test_resolve_default_embedding_provider(monkeypatch):
    """Default embedding provider is 'none'."""
    monkeypatch.delenv("DEVAI_EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("DEVAI_HUB_ROOT", raising=False)
    config = resolve_config()
    assert config.embedding_provider == "none"
