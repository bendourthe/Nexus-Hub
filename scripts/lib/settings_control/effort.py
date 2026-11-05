"""Portable effort mappings and bounded reads of Codex's advertised model capabilities.

Claude's persistent effort keys stop at xhigh; its environment lever accepts max.
Ultra maps to max on Claude without enabling its separate workflow setting.
Codex levels are model-specific. Shared defaults use the common client vocabulary
low/medium/high/xhigh because the installed CLI rejects max and ultra even when
its model cache advertises them. Model metadata may lower that ceiling further.
"""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

LEVELS = ("low", "medium", "high", "xhigh", "max", "ultra")
COMMON_CODEX_LEVELS = LEVELS[:4]
MAX_CACHE_BYTES = 4_000_000


def codex_levels(home: Path, env: Mapping[str, str], data: dict[str, Any], *, model: str | None = None) -> tuple[str, ...]:
    """Return levels advertised for the selected model, or the portable baseline.

    This reads local metadata only. A missing, malformed, oversized or unrecognized
    cache cannot grant a level that the current model may not support.
    """
    selected = model or data.get("model")
    profile = data.get("profiles", {}).get(data.get("profile"), {}) if isinstance(data.get("profiles"), dict) else {}
    if not model and isinstance(profile, dict):
        selected = profile.get("model", selected)
    if not isinstance(selected, str):
        return COMMON_CODEX_LEVELS
    root = Path(env["CODEX_HOME"]) if env.get("CODEX_HOME", "").strip() else home / ".codex"
    try:
        path = root / "models_cache.json"
        if path.stat().st_size > MAX_CACHE_BYTES:
            return COMMON_CODEX_LEVELS
        with path.open("rb") as stream:
            raw = stream.read(MAX_CACHE_BYTES + 1)
        if len(raw) > MAX_CACHE_BYTES:
            return COMMON_CODEX_LEVELS
        cache = json.loads(raw.decode("utf-8-sig"))
        for entry in cache.get("models", []):
            if isinstance(entry, dict) and entry.get("slug") == selected:
                advertised = entry.get("supported_reasoning_levels", [])
                if not isinstance(advertised, list):
                    return COMMON_CODEX_LEVELS
                levels = tuple(level for level in LEVELS if any(isinstance(item, dict) and item.get("effort") == level for item in advertised))
                return levels
    except (OSError, ValueError, TypeError, AttributeError, RecursionError):
        pass
    return COMMON_CODEX_LEVELS


def mapped(write: dict[str, Any], requested: str, levels: tuple[str, ...] = COMMON_CODEX_LEVELS) -> Any:
    """Map one catalog write; Codex clamps to its selected model's supported scale."""
    native = write["value_map"].get(requested)
    if write["tool"] != "codex" or write["key_path"][-1] != "model_reasoning_effort" or requested not in LEVELS:
        return native
    # The installed 0.136.0 CLI rejects Max/Ultra, while the IDE excludes Max.
    # The shared config must parse in both clients, regardless of cached metadata.
    ceiling = min(LEVELS.index(requested), LEVELS.index("xhigh"))
    allowed = [level for level in LEVELS[: ceiling + 1] if level in levels]
    compatible = [level for level in COMMON_CODEX_LEVELS if level in levels]
    return allowed[-1] if allowed else (compatible[0] if compatible else None)
