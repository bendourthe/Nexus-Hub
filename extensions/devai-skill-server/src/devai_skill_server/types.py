from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class DetailLevel(str, Enum):
    L0 = "l0"
    L1 = "l1"
    L2 = "l2"


class SkillSummary(BaseModel):
    """L0 response: minimal metadata for ranking and quick display."""
    name: str
    title: str
    category: str
    summary_l0: str
    priority: str
    language: str
    token_estimate: int


class SkillOverview(SkillSummary):
    """L1 response: adds overview, tags, and tool requirements."""
    overview_l1: str
    tags: list[str]
    tools_required: list[str]
    model_hint: str | None = None
    reasoning_effort: str | None = None


class SkillFull(SkillOverview):
    """L2 response: adds full SKILL.md content."""
    content: str
    file_path: str
    size_lines: int
    size_characters: int


class CategoryInfo(BaseModel):
    name: str
    skill_count: int
    skills: list[str]


class BundleInfo(BaseModel):
    id: str
    name: str
    description: str
    skills: list[str]
    skill_count: int


class SearchResult(BaseModel):
    query: str
    total_matches: int
    level: str
    results: list[SkillSummary | SkillOverview | SkillFull]
