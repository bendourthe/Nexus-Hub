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
VERSION_DIR = ROOT / "docs" / "releases" / "v3" / "v3.15"
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
    # v3.15.12 Phase 1: the raw wire shape of the undocumented usage route, kept
    # separate from the normalized fixtures above.
    "wire-contract.json",
    "wire-field-drift.json",
    "wire-unit-drift.json",
    "wire-usage-summary.json",
}
WIRE_FIXTURES = {
    "wire-contract.json",
    "wire-field-drift.json",
    "wire-unit-drift.json",
    "wire-usage-summary.json",
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


# The two fixtures that describe the REAL route, as opposed to the deliberate
# negative cases used to prove the mapper rejects drift.
VERIFIED_WIRE_FIXTURES = {"wire-contract.json", "wire-usage-summary.json"}
NEGATIVE_WIRE_FIXTURES = WIRE_FIXTURES - VERIFIED_WIRE_FIXTURES


@pytest.mark.parametrize("name", sorted(VERIFIED_WIRE_FIXTURES))
def test_real_wire_fixtures_record_a_live_probe(name: str) -> None:
    """The route was a discovery lead through Phase 1; Phase 6 confirmed it.

    This assertion was inverted deliberately. It previously required
    `verified is False`, because an invented field name marked verified would let a
    later reader treat a guess as a contract. That risk is now the other way round:
    the contract IS confirmed (HTTP 200 against a live account, recorded in
    `cursor-usage-auth-probe.md` Phase 6), so the flag guards against a future
    contract edit made WITHOUT a probe. Flipping it back has to be deliberate.
    """
    contract = _load(name)["fixtureContract"]
    assert contract["verified"] is True
    assert contract["sanitized"] is True
    assert contract["source"] == "credential-api"
    # The provenance must name a probe, not merely assert confidence.
    assert "probe" in contract["provenance"]


@pytest.mark.parametrize("name", sorted(NEGATIVE_WIRE_FIXTURES))
def test_drift_fixtures_stay_marked_as_negative_cases(name: str) -> None:
    """A drift fixture is an intentionally wrong shape and must never read verified."""
    contract = _load(name)["fixtureContract"]
    assert contract["verified"] is False
    assert contract["provenance"] == "negative-case"


def test_wire_contract_never_claims_a_public_api() -> None:
    """Undocumented stays undocumented, however well confirmed it is.

    Verifying that the route works says nothing about it being supported, so the
    `credential-api` label survives the Phase 6 confirmation unchanged.
    """
    payload = _load("wire-contract.json")
    structure = {key: value for key, value in payload.items() if key != "fixtureContract"}
    assert "public-api" not in json.dumps(structure)
    assert payload["fixtureContract"]["source"] == "credential-api"
    # Deliberately NOT a substring check over the note: the note earns its keep by
    # saying "labelled credential-api, never public-api", so a blanket search for
    # the string flags the very sentence that states the rule. The machine-readable
    # structure above is what a consumer reads; the note is prose for a human.


def test_wire_contract_targets_the_rpc_host_with_a_post() -> None:
    """The REST assumption is what produced the 405; pin the verb and the host.

    A Connect endpoint is POST-only, so a well-meaning simplification back to a GET
    would break the live path while leaving every stub-based test green.
    """
    payload = _load("wire-contract.json")
    assert payload["origin"] == "https://api2.cursor.sh"
    assert payload["method"] == "POST"
    assert payload["route"] == "/aiserver.v1.DashboardService/GetCurrentPeriodUsage"


def test_wire_field_paths_are_camel_case() -> None:
    """Connect's JSON codec applies the proto3 JSON mapping.

    The protobuf descriptor declares `billing_cycle_start`; the wire delivers
    `billingCycleStart`. A snake_case path here reads undefined for every field, so
    the whole payload would be rejected as a schema mismatch.
    """
    for path in _load("wire-contract.json")["fields"].values():
        assert "_" not in path, path


def test_sample_payload_reproduces_the_percentage_discrepancy() -> None:
    """Percentages must be used as delivered, never derived from spend over limit.

    On the probed account those two disagreed by a factor of ~45, because the
    reported percentage uses a base the payload does not expose. The fixture keeps
    that discrepancy on purpose: any code that derives a percentage instead of
    reading it would render a healthy pool near 1079% and pin every threshold alert.
    """
    plan = _load("wire-usage-summary.json")["planUsage"]
    derived = plan["totalSpend"] / plan["limit"] * 100
    assert derived > 1000
    assert plan["autoPercentUsed"] < 30


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
