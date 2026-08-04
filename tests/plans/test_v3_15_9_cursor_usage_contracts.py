"""Semantic contract tests for v3.15.9 Cursor usage Phase 3 artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from html.parser import HTMLParser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VERSION_DIR = ROOT / "docs" / "v3" / "v3.15"
DEVELOPMENT_DIR = VERSION_DIR / "development"
DATA_CONTRACT = DEVELOPMENT_DIR / "cursor-usage-data-contract.md"
AUTH_PROBE = DEVELOPMENT_DIR / "cursor-usage-auth-probe.md"
VISUAL_CONTRACT = DEVELOPMENT_DIR / "cursor-usage-visual-contract.md"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "cursor-usage"
ICON_DIR = ROOT / "extensions" / "cursor-usage-monitor" / "icons"

EXPECTED_FIXTURES = {
    "empty-period.json",
    "error-401.json",
    "error-403.json",
    "included-usage-healthy.json",
    "on-demand-disabled.json",
    "on-demand-enabled.json",
    "scrape-spending-page.html",
    "scrape-usage-page.html",
    "unknown-denominator.json",
}
ALLOWED_SOURCES = {"credential-api", "html-scrape", "cache", "manual"}
FORBIDDEN_KEYS = {
    "access_token",
    "authorization",
    "cookie",
    "email",
    "personal_id",
    "session",
    "session_token",
    "team_id",
    "token",
    "user_id",
}
SENSITIVE_PATTERNS = (
    re.compile(r"(?i)authorization\s*[:=]"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"(?i)cookie\s*[:=]"),
    re.compile(r"(?i)session(?:id|token)\s*[:=]"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{8,}"),
)
EXPECTED_ICONS = {
    "cursor-ai-480.png": (
        480,
        480,
        "5706468F30FC4BC45C96F8909B94FA110CC5014D4DDB7E1A3F360D51F75CF459",
    ),
    "cursor-ai-48.png": (
        48,
        48,
        "2804DC1CD9720988D3E561114D6C3FA39B554AACED40C92AF1BC848133699DAB",
    ),
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load(name: str) -> dict:
    return json.loads(_read(FIXTURE_DIR / name))


def _collect_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(key.lower())
            keys.update(_collect_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_collect_keys(child))
    return keys


def _png_metadata(path: Path) -> tuple[int, int, int]:
    data = path.read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    width, height = struct.unpack(">II", data[16:24])
    return width, height, data[25]


def test_fixture_inventory_is_exact_and_parseable() -> None:
    actual = {path.name for path in FIXTURE_DIR.iterdir() if path.is_file()}
    assert actual == EXPECTED_FIXTURES
    for path in FIXTURE_DIR.glob("*.json"):
        assert isinstance(json.loads(_read(path)), dict)
    for path in FIXTURE_DIR.glob("*.html"):
        parser = HTMLParser()
        parser.feed(_read(path))


@pytest.mark.parametrize("name", sorted(EXPECTED_FIXTURES))
def test_fixtures_are_sanitized(name: str) -> None:
    path = FIXTURE_DIR / name
    text = _read(path)
    if path.suffix == ".json":
        assert not (FORBIDDEN_KEYS & _collect_keys(json.loads(text)))
    for pattern in SENSITIVE_PATTERNS:
        assert not pattern.search(text), (
            f"sensitive pattern in {name}: {pattern.pattern}"
        )
    assert "BEDOURTHE" not in text
    assert "supira" not in text.lower()


def test_normalized_fixture_sources_are_allowed() -> None:
    sources: set[str] = set()
    for path in FIXTURE_DIR.glob("*.json"):
        payload = json.loads(_read(path))
        if "fixtureContract" in payload:
            sources.add(payload["fixtureContract"]["source"])

    assert sources <= ALLOWED_SOURCES
    assert {"credential-api", "html-scrape", "cache"} <= sources


def test_healthy_included_usage_has_same_unit_math() -> None:
    payload = _load("included-usage-healthy.json")
    for key in ("cursorModels", "otherModels"):
        meter = payload[key]
        assert meter["used"]["unit"] == meter["limit"]["unit"]
        expected = meter["used"]["value"] / meter["limit"]["value"] * 100
        assert math.isclose(meter["percentUsed"], expected)
    assert (
        payload["cursorModels"]["percentUsed"] != payload["otherModels"]["percentUsed"]
    )


def test_unknown_denominator_never_invents_percentages() -> None:
    payload = _load("unknown-denominator.json")
    for key in ("cursorModels", "otherModels"):
        assert payload[key]["used"]["value"] > 0
        assert payload[key]["limit"] is None
        assert payload[key]["percentUsed"] is None
    contract = _read(DATA_CONTRACT)
    assert "An unknown denominator is not zero" in contract
    assert "do not render `0%`, `100%`, or a fabricated maximum" in contract


def test_on_demand_and_team_shared_pool_stay_separate() -> None:
    enabled = _load("on-demand-enabled.json")
    assert enabled["onDemand"]["enabled"] is True
    assert enabled["onDemand"]["personalSpend"]["amount"] == 12.5
    assert enabled["teamContext"]["sharedSpendLimit"]["amount"] == 250
    assert enabled["teamContext"]["personalAllocation"] is None

    disabled = _load("on-demand-disabled.json")
    assert disabled["onDemand"] == {"enabled": False, "personalSpend": None}

    contract = _read(DATA_CONTRACT)
    assert "never derives a personal hard cap" in contract
    assert "`$limit / member_count`" in contract
    assert "Shared team context" in contract


def test_error_fixtures_cover_auth_and_visibility() -> None:
    statuses = {
        _load(name)["fixtureStatus"] for name in ("error-401.json", "error-403.json")
    }
    assert statuses == {401, 403}


def test_html_fixtures_use_semantic_anchors_not_claimed_live_selectors() -> None:
    spending = _read(FIXTURE_DIR / "scrape-spending-page.html")
    usage = _read(FIXTURE_DIR / "scrape-usage-page.html")
    for phrase in (
        "Spending",
        "Cursor Models",
        "Other Models",
        "Included Usage",
        "On-Demand Usage",
    ):
        assert phrase in spending
    for phrase in ("Usage", "Input tokens", "Output tokens", "Billing cycle"):
        assert phrase in usage
    assert "data-fixture-" in spending
    assert "data-fixture-" in usage
    assert "not claimed as live Cursor selectors" in _read(DATA_CONTRACT)


def test_data_contract_locks_sources_routes_units_and_fallbacks() -> None:
    text = _read(DATA_CONTRACT)
    for source in sorted(ALLOWED_SOURCES):
        assert f"`{source}`" in text
    for route in (
        "https://cursor.com/dashboard/spending",
        "https://cursor.com/dashboard/usage",
    ):
        assert route in text
    for unit in ("`tokens`", "`requests`", "`percent`"):
        assert unit in text
    assert "does not publish a personal-usage API contract" in text
    assert "never reads or logs raw browser cookies" in text


def test_auth_probe_bounds_paths_and_secret_access() -> None:
    text = _read(AUTH_PROBE)
    for candidate in (
        "%APPDATA%\\Cursor\\User\\globalStorage\\state.vscdb",
        "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb",
        "~/.config/Cursor/User/globalStorage/state.vscdb",
        "~/.cursor/cli-config.json",
    ):
        assert candidate in text
    assert (
        "No database, configuration file, cookie store, keychain, or credential value was opened"
        in text
    )
    assert "No browser cookie database access" in text
    assert "must never be presented as a documented Cursor API" in text
    assert "C:\\Users\\" not in text


@pytest.mark.parametrize("name", sorted(EXPECTED_ICONS))
def test_cursor_source_assets_have_expected_dimensions_alpha_and_hash(
    name: str,
) -> None:
    expected_width, expected_height, expected_hash = EXPECTED_ICONS[name]
    path = ICON_DIR / name
    assert path.is_file()
    width, height, color_type = _png_metadata(path)
    assert (width, height) == (expected_width, expected_height)
    assert color_type == 6, "expected RGBA PNG"
    assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == expected_hash


def test_visual_contract_locks_brand_pipeline_and_attribution() -> None:
    text = _read(VISUAL_CONTRACT)
    readme = _read(ICON_DIR / "README.md")
    assert "`#4682B4`" in text
    assert 'viewBox="0 0 20 20"' in text
    assert "transparent 256x256" in text
    assert "Icons8" in text
    assert "attribution" in text.lower()
    assert "DiGZkjCzyZXn" in text
    assert "THIRD_PARTY_NOTICES.md" in text
    for _, _, digest in EXPECTED_ICONS.values():
        assert digest in text
        assert digest in readme


@pytest.mark.parametrize(
    "path",
    (DATA_CONTRACT, AUTH_PROBE, VISUAL_CONTRACT, ICON_DIR / "README.md"),
)
def test_phase_three_markdown_is_ascii(path: Path) -> None:
    text = _read(path)
    assert text.isascii(), f"non-ASCII content in {path}"
    assert "\u2014" not in text
    assert "\u2013" not in text
