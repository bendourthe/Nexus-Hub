"""Semantic contract tests for v3.15.9 cross-provider plan routing."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VERSION_DIR = ROOT / "docs" / "releases" / "v3" / "v3.15"
PLAN_PATH = (
    VERSION_DIR / "plans" / "v3.15.9-cross-provider-routing-and-cursor-usage-monitor.md"
)
CONTRACT_PATH = VERSION_DIR / "development" / "cross-provider-routing-contract.md"
IMPLEMENTATION_PLAN_PATH = (
    ROOT / "catalog" / "skills" / "workflow" / "implementation-plan" / "SKILL.md"
)
PLAN_COMMAND_PATH = ROOT / "catalog" / "commands" / "plan.md"
IMPLEMENT_COMMAND_PATH = ROOT / "catalog" / "commands" / "implement.md"
ROUTE_COMMAND_PATH = ROOT / "catalog" / "commands" / "route.md"
MODEL_ROUTING_PATH = (
    ROOT / "catalog" / "skills" / "ai-development" / "model-routing" / "SKILL.md"
)
AGENTS_PATH = ROOT / "AGENTS.md"

TIERS = ("frontier", "strong", "standard", "fast")
EFFORTS = ("low", "medium", "high", "max")
PROVIDERS = ("Anthropic", "OpenAI", "Google", "Cursor")
ASSESS_LATER = "assess at implementation time"
MODEL_ID_PATTERN = re.compile(
    r"\b(?:claude|gpt|gemini|composer|cursor-grok)-[a-z0-9][a-z0-9.-]*\b",
    re.IGNORECASE,
)
STATUS_PATTERNS = {
    "fresh": re.compile(
        r"^\*\*Model map status\*\*: fresh as of "
        r"\d{4}-\d{2}-\d{2}; sources cited below\.$",
        re.MULTILINE,
    ),
    "offline": re.compile(
        r"^\*\*Model map status\*\*: offline fallback; stale as of "
        r"\d{4}-\d{2}-\d{2}\.$",
        re.MULTILINE,
    ),
    "unavailable": re.compile(
        r"^\*\*Model map status\*\*: unavailable; "
        r"assess at implementation time\.$",
        re.MULTILINE,
    ),
}
FIXTURE_MODEL_CELL_PATTERN = re.compile(
    rf"`(?:{'|'.join(provider.lower() for provider in PROVIDERS)})-"
    rf"(?:{'|'.join(TIERS)})`"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _table_after_heading(text: str, heading: str) -> list[list[str]]:
    lines = text.splitlines()
    try:
        heading_index = lines.index(heading)
    except ValueError as exc:
        raise ValueError(f"missing heading: {heading}") from exc

    table_lines: list[str] = []
    for line in lines[heading_index + 1 :]:
        if line.startswith("|"):
            table_lines.append(line)
        elif table_lines:
            break
    if len(table_lines) < 3:
        raise ValueError(f"missing table after: {heading}")

    return [
        [cell.strip() for cell in line.strip("|").split("|")]
        for index, line in enumerate(table_lines)
        if index != 1
    ]


def _phase_blocks(text: str) -> list[str]:
    matches = list(re.finditer(r"(?m)^## Phase \d+:", text))
    return [
        text[match.start() : matches[index + 1].start()]
        if index + 1 < len(matches)
        else text[match.start() :]
        for index, match in enumerate(matches)
    ]


def _field(block: str, name: str) -> str:
    match = re.search(rf"(?m)^\*\*{re.escape(name)}\*\*: (.+)$", block)
    if not match:
        raise ValueError(f"missing per-phase field: {name}")
    return match.group(1).strip()


def _strip_code(value: str) -> str:
    return value.strip().strip("`")


def validate_plan(text: str) -> None:
    glance = _table_after_heading(text, "## Phases at a Glance")
    expected_glance_header = [
        "Phase",
        "Title",
        "Outcome",
        "Recommended model tier",
        "Recommended effort level",
    ]
    if glance[0] != expected_glance_header:
        raise ValueError(f"invalid glance header: {glance[0]}")

    for row in glance[1:]:
        if len(row) != 5:
            raise ValueError(f"invalid glance row: {row}")
        if row[3] not in TIERS:
            raise ValueError(f"invalid tier: {row[3]}")
        if row[4] not in EFFORTS:
            raise ValueError(f"invalid effort: {row[4]}")
        if MODEL_ID_PATTERN.search(row[3]) or MODEL_ID_PATTERN.search(row[4]):
            raise ValueError(f"concrete model in glance row: {row}")

    model_map = _table_after_heading(text, "## Current model map")
    if model_map[0] != ["Tier", *PROVIDERS]:
        raise ValueError(f"invalid model-map header: {model_map[0]}")
    if [row[0] for row in model_map[1:]] != list(TIERS):
        raise ValueError("model-map tiers are incomplete or out of order")
    if any(len(row) != 5 or any(not cell for cell in row[1:]) for row in model_map[1:]):
        raise ValueError("model-map provider cell is empty")

    statuses = [
        status for status, pattern in STATUS_PATTERNS.items() if pattern.search(text)
    ]
    if len(statuses) != 1:
        raise ValueError(f"expected one model-map status, found: {statuses}")
    status = statuses[0]
    provider_cells = [_strip_code(cell) for row in model_map[1:] for cell in row[1:]]
    if status == "unavailable":
        if set(provider_cells) != {ASSESS_LATER}:
            raise ValueError("unavailable map must defer every provider cell")
    elif ASSESS_LATER in provider_cells:
        raise ValueError("fresh or dated-snapshot map has deferred provider cells")

    if status in {"fresh", "offline"}:
        sources_start = text.find("### Model map sources")
        glance_start = text.find("## Phases at a Glance")
        if sources_start < 0:
            raise ValueError("missing model-map sources")
        sources = text[
            sources_start : glance_start if glance_start > sources_start else None
        ]
        for provider in PROVIDERS:
            if not re.search(rf"(?m)^- {provider}: .*https?://", sources):
                raise ValueError(f"missing source URL for {provider}")

    blocks = _phase_blocks(text)
    if not blocks:
        raise ValueError("plan has no phases")
    for block in blocks:
        tier = _field(block, "Recommended model tier")
        effort = _field(block, "Recommended effort level")
        rationale = _field(block, "Rationale")
        if tier not in TIERS:
            raise ValueError(f"invalid per-phase tier: {tier}")
        if effort not in EFFORTS:
            raise ValueError(f"invalid per-phase effort: {effort}")
        if not rationale:
            raise ValueError("empty rationale")
        if MODEL_ID_PATTERN.search(f"{tier} {effort} {rationale}"):
            raise ValueError("concrete model in per-phase recommendation")


VALID_OFFLINE_PLAN = """
# Plan - Fixture

## Current model map

**Model map status**: offline fallback; stale as of 2026-08-01.

| Tier | Anthropic | OpenAI | Google | Cursor |
|------|-----------|--------|--------|--------|
| frontier | `anthropic-frontier` | `openai-frontier` | `google-frontier` | `cursor-frontier` |
| strong | `anthropic-strong` | `openai-strong` | `google-strong` | `cursor-strong` |
| standard | `anthropic-standard` | `openai-standard` | `google-standard` | `cursor-standard` |
| fast | `anthropic-fast` | `openai-fast` | `google-fast` | `cursor-fast` |

### Model map sources

- Anthropic: https://example.test/anthropic
- OpenAI: https://example.test/openai
- Google: https://example.test/google
- Cursor: https://example.test/cursor

## Phases at a Glance

| Phase | Title | Outcome | Recommended model tier | Recommended effort level |
|-------|-------|---------|------------------------|--------------------------|
| 1 | Fixture | Validated | strong | high |

## Phase 1: Fixture

**Goal**: Validate the fixture.
**Prerequisites**: None.
**Stability Gate**: Contract passes.
**Recommended model tier**: strong
**Recommended effort level**: high
**Rationale**: The fixture covers several contract branches.
"""

VALID_UNAVAILABLE_PLAN = FIXTURE_MODEL_CELL_PATTERN.sub(
    ASSESS_LATER,
    VALID_OFFLINE_PLAN.replace(
        "**Model map status**: offline fallback; stale as of 2026-08-01.",
        "**Model map status**: unavailable; assess at implementation time.",
    ),
)

LEGACY_HOST_LOCKED_PLAN = """
# Plan - Legacy Fixture

## Phases at a Glance

| Phase | Title | Outcome | Rec. model / effort |
|-------|-------|---------|---------------------|
| 1 | Fixture | Rejected | `gpt-5.5`, xhigh |

## Phase 1: Fixture

**Recommended model**: `gpt-5.5`, xhigh.
"""


def test_repository_plan_passes_cross_provider_contract() -> None:
    validate_plan(_read(PLAN_PATH))


@pytest.mark.parametrize("fixture", (VALID_OFFLINE_PLAN, VALID_UNAVAILABLE_PLAN))
def test_offline_fallback_forms_pass_contract(fixture: str) -> None:
    validate_plan(fixture)


def test_legacy_host_locked_fixture_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_plan(LEGACY_HOST_LOCKED_PLAN)


def test_template_and_plan_command_publish_new_contract() -> None:
    template = _read(IMPLEMENTATION_PLAN_PATH)
    command = _read(PLAN_COMMAND_PATH)
    for text in (template, command):
        assert "Recommended model tier" in text
        assert "Recommended effort level" in text
        assert "## Current model map" in text
        assert "Anthropic" in text
        assert "OpenAI" in text
        assert "Google" in text
        assert "Cursor" in text
        assert "Rec. model / effort" not in text


def test_related_routing_surfaces_preserve_host_native_switching() -> None:
    implement = _read(IMPLEMENT_COMMAND_PATH)
    route = _read(ROUTE_COMMAND_PATH)
    skill = _read(MODEL_ROUTING_PATH)
    agents = _read(AGENTS_PATH)

    assert "**Recommended model tier**" in implement
    assert "**Recommended effort level**" in implement
    assert "historical plans" in implement.lower()
    assert "host-native switching command" in route
    assert "The map never authorizes switching" in route
    assert "Planning contract vs. direct switching" in skill
    assert "model-map.sh" in skill
    assert "last-known-model-map.json" in skill
    assert "`## Current model map`" in agents


def test_contract_defines_exact_enums_and_fallback_markers() -> None:
    text = _read(CONTRACT_PATH)
    for value in (*TIERS, *EFFORTS):
        assert f"`{value}`" in text
    for phrase in (
        "**Model map status**: fresh as of YYYY-MM-DD; sources cited below.",
        "**Model map status**: offline fallback; stale as of YYYY-MM-DD.",
        "**Model map status**: unavailable; assess at implementation time.",
    ):
        assert phrase in text


def test_new_phase_one_markdown_is_ascii() -> None:
    assert _read(CONTRACT_PATH).isascii()
