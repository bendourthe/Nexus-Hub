from __future__ import annotations

import json
import logging
from pathlib import Path

from devai_skill_server.config import ServerConfig
from devai_skill_server.types import (
    BundleInfo,
    CategoryInfo,
    DetailLevel,
    SkillFull,
    SkillOverview,
    SkillSummary,
)

logger = logging.getLogger("devai-skill-server")


class SkillCatalog:
    """In-memory skill catalog loaded from skills.json and bundles.json."""

    def __init__(self, config: ServerConfig) -> None:
        self._config = config
        self._skills: dict[str, dict] = {}
        self._bundles: list[dict] = []
        self._categories: dict[str, list[str]] = {}
        self.version: str = "unknown"

    def load(self) -> None:
        """Load skills.json and bundles.json into memory."""
        if not self._config.skills_json_path or not self._config.skills_json_path.exists():
            logger.error("skills.json not found. Set DEVAI_HUB_ROOT or run the DevAI-Hub installer.")
            return

        with open(self._config.skills_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.version = data.get("metadata", {}).get("version", "unknown")

        for skill in data.get("skills", []):
            name = skill["name"]
            self._skills[name] = skill
            cat = skill.get("category", "other")
            self._categories.setdefault(cat, []).append(name)

        logger.info("Loaded %d skills across %d categories", len(self._skills), len(self._categories))

        if self._config.bundles_json_path and self._config.bundles_json_path.exists():
            with open(self._config.bundles_json_path, "r", encoding="utf-8") as f:
                bundles_data = json.load(f)
            self._bundles = bundles_data.get("bundles", [])
            logger.info("Loaded %d bundles", len(self._bundles))

    @property
    def is_loaded(self) -> bool:
        return len(self._skills) > 0

    def get_skill(self, name: str, level: DetailLevel = DetailLevel.L2) -> SkillSummary | SkillOverview | SkillFull | None:
        """Retrieve a single skill at the requested detail level."""
        skill = self._skills.get(name)
        if not skill:
            return None

        if level == DetailLevel.L0:
            return self._to_summary(skill)
        if level == DetailLevel.L1:
            return self._to_overview(skill)
        return self._to_full(skill)

    def list_categories(self) -> list[CategoryInfo]:
        return [
            CategoryInfo(name=cat, skill_count=len(skills), skills=sorted(skills))
            for cat, skills in sorted(self._categories.items())
        ]

    def list_bundles(self) -> list[BundleInfo]:
        return [
            BundleInfo(
                id=b["id"],
                name=b["name"],
                description=b.get("description", ""),
                skills=b.get("skills", []),
                skill_count=len(b.get("skills", [])),
            )
            for b in self._bundles
        ]

    def get_bundle(self, bundle_id: str) -> BundleInfo | None:
        for b in self._bundles:
            if b["id"] == bundle_id:
                return BundleInfo(
                    id=b["id"],
                    name=b["name"],
                    description=b.get("description", ""),
                    skills=b.get("skills", []),
                    skill_count=len(b.get("skills", [])),
                )
        return None

    def get_all_skills_metadata(self) -> list[dict]:
        return list(self._skills.values())

    def get_all_skill_names(self) -> list[str]:
        return sorted(self._skills.keys())

    def find_closest_match(self, name: str, max_distance: int = 3) -> str | None:
        """Find closest skill name by Levenshtein distance."""
        best_match = None
        best_dist = max_distance + 1
        for existing in self._skills:
            dist = _levenshtein(name, existing)
            if dist < best_dist:
                best_dist = dist
                best_match = existing
        return best_match if best_dist <= max_distance else None

    def _to_summary(self, skill: dict) -> SkillSummary:
        return SkillSummary(
            name=skill["name"],
            title=skill.get("title", skill["name"]),
            category=skill.get("category", "other"),
            summary_l0=skill.get("summary_l0", skill.get("description", "")),
            priority=skill.get("priority", "MEDIUM"),
            language=skill.get("language", "Multi-language"),
            token_estimate=skill.get("size", {}).get("tokens_estimate", 0),
        )

    def _to_overview(self, skill: dict) -> SkillOverview:
        return SkillOverview(
            name=skill["name"],
            title=skill.get("title", skill["name"]),
            category=skill.get("category", "other"),
            summary_l0=skill.get("summary_l0", skill.get("description", "")),
            priority=skill.get("priority", "MEDIUM"),
            language=skill.get("language", "Multi-language"),
            token_estimate=skill.get("size", {}).get("tokens_estimate", 0),
            overview_l1=skill.get("overview_l1", skill.get("long_description", "")),
            tags=skill.get("tags", []),
            tools_required=skill.get("tools_required", []),
            model_hint=skill.get("model_hint"),
            reasoning_effort=skill.get("reasoning_effort"),
        )

    def _to_full(self, skill: dict) -> SkillFull:
        overview = self._to_overview(skill)
        content = self._read_skill_content(skill.get("file", ""))
        size = skill.get("size", {})

        return SkillFull(
            **overview.model_dump(),
            content=content,
            file_path=skill.get("file", ""),
            size_lines=size.get("lines", 0),
            size_characters=size.get("characters", 0),
        )

    def _read_skill_content(self, file_path: str) -> str:
        """Read full SKILL.md content from disk."""
        if not file_path or not self._config.hub_root:
            return ""

        full_path = self._config.hub_root / file_path
        if not full_path.exists():
            logger.warning("Skill file not found: %s", full_path)
            return f"[Content unavailable: {file_path} not found on disk]"

        try:
            return full_path.read_text(encoding="utf-8")
        except OSError as e:
            logger.error("Error reading %s: %s", full_path, e)
            return f"[Error reading {file_path}: {e}]"


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)

    prev_row = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr_row = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr_row.append(min(
                curr_row[j] + 1,
                prev_row[j + 1] + 1,
                prev_row[j] + cost,
            ))
        prev_row = curr_row

    return prev_row[-1]
