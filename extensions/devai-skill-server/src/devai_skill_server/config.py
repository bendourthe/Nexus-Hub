from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("devai-skill-server")


@dataclass(frozen=True)
class ServerConfig:
    hub_root: Path | None
    skills_json_path: Path | None
    bundles_json_path: Path | None
    catalog_skills_dir: Path | None
    embedding_provider: str = "none"
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".devai-hub" / "cache")


def _find_hub_root() -> Path | None:
    """Three-tier resolution for the DevAI-Hub root directory."""

    # 1. Explicit env var
    env_root = os.environ.get("DEVAI_HUB_ROOT")
    if env_root:
        candidate = Path(env_root)
        if (candidate / "data" / "skills.json").exists():
            logger.info("Hub root from DEVAI_HUB_ROOT: %s", candidate)
            return candidate
        logger.warning("DEVAI_HUB_ROOT set to %s but data/skills.json not found", candidate)

    # 2. Auto-detect from server location (extensions/devai-skill-server/src/...)
    server_dir = Path(__file__).resolve().parent
    for _ in range(5):
        server_dir = server_dir.parent
        if (server_dir / "data" / "skills.json").exists():
            logger.info("Hub root auto-detected: %s", server_dir)
            return server_dir

    # 3. Global install path
    global_path = Path.home() / ".devai-hub"
    if (global_path / "data" / "skills.json").exists():
        logger.info("Hub root from global install: %s", global_path)
        return global_path

    return None


def resolve_config() -> ServerConfig:
    """Resolve server configuration from environment and filesystem."""
    hub_root = _find_hub_root()

    skills_json = None
    bundles_json = None
    catalog_dir = None

    if hub_root:
        skills_json = hub_root / "data" / "skills.json"
        bundles_path = hub_root / "data" / "bundles.json"
        bundles_json = bundles_path if bundles_path.exists() else None
        cat_dir = hub_root / "catalog" / "skills"
        catalog_dir = cat_dir if cat_dir.exists() else None

    embedding_provider = os.environ.get("DEVAI_EMBEDDING_PROVIDER", "none")
    cache_dir_env = os.environ.get("DEVAI_CACHE_DIR")
    cache_dir = Path(cache_dir_env) if cache_dir_env else Path.home() / ".devai-hub" / "cache"

    return ServerConfig(
        hub_root=hub_root,
        skills_json_path=skills_json,
        bundles_json_path=bundles_json,
        catalog_skills_dir=catalog_dir,
        embedding_provider=embedding_provider,
        cache_dir=cache_dir,
    )
