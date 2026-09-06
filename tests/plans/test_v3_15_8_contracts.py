"""Semantic contract tests for v3.15.8 Phase 1 artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
VERSION_DIR = ROOT / "docs" / "releases" / "v3" / "v3.15"
DEVELOPMENT_DIR = VERSION_DIR / "development"
OWNERSHIP_PATH = DEVELOPMENT_DIR / "platform-capability-ownership.md"
DATA_CONTRACT_PATH = DEVELOPMENT_DIR / "github-usage-data-contract.md"
VISUAL_CONTRACT_PATH = DEVELOPMENT_DIR / "github-usage-visual-contract.md"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "github-usage"

EXPECTED_FIXTURES = {
    "actions-minutes-storage.json",
    "additive-fields.json",
    "current-ai-credits.json",
    "empty-month.json",
    "error-401.json",
    "error-403.json",
    "error-404.json",
    "error-429.json",
    "legacy-premium-requests.json",
    "managed-copilot.json",
    "unknown-allowance.json",
}

EXPECTED_CAPABILITIES = {
    "Codex custom agents",
    "Codex native hooks",
    "Gemini CLI native hooks",
    "Qwen native hooks",
    "Kimi custom agents",
    "Kimi native hooks",
    "Copilot custom agents",
    "Copilot native hooks",
    "Hermes skill layout",
}

# A capability+scope may claim enforcement only once its implementation phase has
# shipped owned writes and lifecycle tests. Hermes was already enforceable at
# Phase 1. Keys are (capability, scope) rather than capability alone, because a
# capability can be deliverable at one scope and undocumented at the other --
# Kimi hooks exist only in the user-level config.toml, so the workspace row must
# stay finding-only. Add an entry here in the same commit that implements it,
# never ahead of it.
IMPLEMENTED_CAPABILITIES = {
    ("Codex custom agents", "global"): "Phase 5",
    ("Codex custom agents", "workspace"): "Phase 5",
    ("Codex native hooks", "global"): "Phase 5",
    ("Codex native hooks", "workspace"): "Phase 5",
    ("Gemini CLI native hooks", "global"): "Phase 6",
    ("Gemini CLI native hooks", "workspace"): "Phase 6",
    ("Qwen native hooks", "global"): "Phase 6",
    ("Qwen native hooks", "workspace"): "Phase 6",
    ("Kimi custom agents", "global"): "Phase 7",
    ("Kimi custom agents", "workspace"): "Phase 7",
    ("Kimi native hooks", "global"): "Phase 7",
    # ("Kimi native hooks", "workspace") is intentionally absent: Kimi documents
    # no project-scoped hook path, so that row must still read finding-only.
    ("Copilot custom agents", "global"): "Phase 8",
    ("Copilot custom agents", "workspace"): "Phase 8",
    ("Copilot native hooks", "global"): "Phase 8",
    ("Copilot native hooks", "workspace"): "Phase 8",
    # Hermes was already delivering the flattened layout at Phase 1; Phase 8
    # re-verified the discovery rule and confirmed no migration was warranted,
    # so its rows now carry a phase like every other enforceable row.
    ("Hermes skill layout", "global"): "Phase 8",
    ("Hermes skill layout", "workspace"): "Phase 8",
}

# Rows that are enforceable WITHOUT Nexus-Hub owning a write, because the
# platform's own default read paths already point at files another integration
# produces. Recorded explicitly so "no write" can never be confused with
# "not delivered" -- and so a future phase cannot quietly add a duplicate write
# without updating this list.
INHERITED_ROWS = {
    ("Copilot custom agents", "workspace"),
    ("Copilot native hooks", "global"),
    ("Copilot native hooks", "workspace"),
}

SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{8,}"),
    re.compile(r"(?i)authorization\s*[:=]"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_fixture(name: str) -> dict:
    return json.loads(_read(FIXTURE_DIR / name))


def _ownership_rows() -> list[list[str]]:
    rows: list[list[str]] = []
    for line in _read(OWNERSHIP_PATH).splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) == 11 and cells[0] in EXPECTED_CAPABILITIES:
            rows.append(cells)
    return rows


def test_every_capability_has_global_and_workspace_decisions() -> None:
    rows = _ownership_rows()
    assert len(rows) == len(EXPECTED_CAPABILITIES) * 2
    for capability in EXPECTED_CAPABILITIES:
        scopes = {row[1] for row in rows if row[0] == capability}
        assert scopes == {"global", "workspace"}, capability


def test_every_ownership_row_covers_lifecycle_and_tests() -> None:
    for row in _ownership_rows():
        capability, scope = row[0], row[1]
        assert row[2], f"{capability} {scope} has no source/destination"
        assert row[5], f"{capability} {scope} has no write mode"
        assert row[6], f"{capability} {scope} has no owner decision"
        assert "repair" in row[8].lower(), (
            f"{capability} {scope} has no repair decision"
        )
        assert "teardown" in row[8].lower(), (
            f"{capability} {scope} has no teardown decision"
        )
        assert "test" in row[9].lower() or "," in row[9], (
            f"{capability} {scope} has no test decision"
        )


def test_unimplemented_surfaces_are_finding_only() -> None:
    for row in _ownership_rows():
        capability, scope, status = row[0], row[1], row[10]
        if (capability, scope) in IMPLEMENTED_CAPABILITIES:
            phase = IMPLEMENTED_CAPABILITIES[(capability, scope)]
            assert "Enforceable" in status and phase in status, (
                f"implemented but not marked enforceable in {phase}: "
                f"{capability} {scope}"
            )
        else:
            assert "Finding-only" in status, (
                f"premature enforcement: {capability} {scope}"
            )


def test_inherited_rows_say_so_and_claim_no_owned_write() -> None:
    """An inherited row must name its source and disclaim ownership.

    "Enforceable" on a row Nexus-Hub does not write is only honest if the row
    says where the delivery actually comes from, so a reader does not go looking
    for a writer that is deliberately absent.
    """
    for row in _ownership_rows():
        key = (row[0], row[1])
        if key not in INHERITED_ROWS:
            continue
        source, write_mode, status = row[2], row[5], row[10]
        assert "INHERITED" in source, f"{key} does not name its inherited source"
        assert write_mode.strip().lower() == "no write", f"{key} claims a write mode"
        assert "inherited" in status.lower(), f"{key} status hides the inheritance"


def test_undelivered_rows_state_why_not_just_that_they_are_pending() -> None:
    """A finding-only row must name its blocker or its owning phase.

    Once a capability's phase has run, "Finding-only; Phase N" is no longer an
    honest status for a row that phase deliberately did not deliver -- it reads
    as pending work rather than a documented absence. This forces the reason
    into the row.
    """
    for row in _ownership_rows():
        capability, scope, status = row[0], row[1], row[10]
        if "Finding-only" not in status:
            continue
        implemented_phases = {
            phase
            for (cap, _scope), phase in IMPLEMENTED_CAPABILITIES.items()
            if cap == capability
        }
        if not implemented_phases:
            continue
        assert "no documented" in status.lower() or "re-verified" in status.lower(), (
            f"{capability} {scope} was not delivered by its phase but does not "
            f"say why: {status!r}"
        )


def test_shared_alias_ownership_is_unambiguous() -> None:
    text = _read(OWNERSHIP_PATH)
    assert "Codex owns the global alias" in text
    assert "Antigravity owns the project alias" in text
    assert "Shared aliases keep one writer" in text


def test_fixture_inventory_is_exact_and_json_valid() -> None:
    actual = {path.name for path in FIXTURE_DIR.glob("*.json")}
    assert actual == EXPECTED_FIXTURES
    for name in actual:
        assert isinstance(_load_fixture(name), dict)


@pytest.mark.parametrize("name", sorted(EXPECTED_FIXTURES))
def test_fixtures_contain_no_credentials_or_personal_records(name: str) -> None:
    text = _read(FIXTURE_DIR / name)
    lowered_keys: set[str] = set()

    def collect_keys(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                lowered_keys.add(key.lower())
                collect_keys(child)
        elif isinstance(value, list):
            for child in value:
                collect_keys(child)

    collect_keys(json.loads(text))
    assert not (
        {"token", "access_token", "email", "personal_id", "authorization"}
        & lowered_keys
    )
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(text), (
            f"sensitive pattern in {name}: {pattern.pattern}"
        )
    assert "monalisa" not in text.lower()
    assert "octocat" not in text.lower()


def test_current_and_legacy_copilot_units_are_distinct() -> None:
    current = _load_fixture("current-ai-credits.json")["usageItems"][0]
    legacy = _load_fixture("legacy-premium-requests.json")["usageItems"][0]
    assert current["unitType"] == "ai-credits"
    assert legacy["unitType"] == "requests"
    assert current["sku"] != legacy["sku"]


def test_actions_fixture_preserves_minutes_storage_costs_and_discounts() -> None:
    items = _load_fixture("actions-minutes-storage.json")["usageItems"]
    assert {item["unitType"] for item in items} == {"minutes", "gigabyte-hours"}
    for item in items:
        assert {
            "grossQuantity",
            "grossAmount",
            "discountAmount",
            "netAmount",
        } <= item.keys()


def test_managed_copilot_is_not_a_personal_response() -> None:
    payload = _load_fixture("managed-copilot.json")
    assert "organization" in payload
    assert "user" not in payload
    assert payload["organization"].startswith("fixture-")


def test_unknown_allowance_never_invents_a_percentage() -> None:
    contract = _load_fixture("unknown-allowance.json")["fixtureContract"]
    assert contract["allowance"] is None
    assert contract["percentage"] is None
    text = _read(DATA_CONTRACT_PATH)
    assert "An unknown allowance is not zero" in text
    assert "does not render `0%`, `100%`, or an invented reset date" in text


def test_error_fixtures_cover_required_statuses() -> None:
    statuses = {
        _load_fixture(name)["fixtureStatus"]
        for name in EXPECTED_FIXTURES
        if name.startswith("error-")
    }
    assert statuses == {401, 403, 404, 429}


def test_additive_fields_fixture_exercises_forward_compatibility() -> None:
    payload = _load_fixture("additive-fields.json")
    assert "futureEnvelope" in payload
    assert "futureItemField" in payload["usageItems"][0]
    assert "fields not named below as additive" in _read(DATA_CONTRACT_PATH)


def test_billing_contract_covers_scopes_permissions_and_endpoints() -> None:
    text = _read(DATA_CONTRACT_PATH)
    for endpoint in (
        "/users/{username}/settings/billing",
        "/organizations/{org}/settings/billing",
        "/enterprises/{enterprise}/settings/billing",
        "/ai_credit/usage",
        "/premium_request/usage",
        "/usage/summary",
    ):
        assert endpoint in text
    assert "`Plan: read`" in text
    assert "`Administration: read`" in text
    assert "public preview" in text.lower()
    assert "never scrapes GitHub.com" in text
    assert "No authorized billing credential or account scope was supplied" in text


def test_visual_contract_locks_brand_dimensions_and_resolved_assets() -> None:
    text = _read(VISUAL_CONTRACT_PATH)
    assert "`#008080`" in text
    assert 'viewBox="0 0 20 20"' in text
    assert "`14x14`" in text
    assert "`256x256` rgba png" in text.lower()
    assert "is not used as the package-icon source" in text
    assert "DE9D1B04630AB8FC29B6E40D85B6018A6E0BD0F621BDC1BE2608663F9DFD90D8" in text
    assert "76B15E4712E3B279E0A063A1E21794DC4E665FFC54B261A014E73F9A78D72B05" in text
    assert "CC0" in text
    assert "one visible path" in text


@pytest.mark.parametrize(
    "path",
    (OWNERSHIP_PATH, DATA_CONTRACT_PATH, VISUAL_CONTRACT_PATH),
)
def test_phase_one_markdown_is_ascii(path: Path) -> None:
    text = _read(path)
    assert text.isascii(), f"non-ASCII content in {path}"
    assert "\u2014" not in text
    assert "\u2013" not in text
