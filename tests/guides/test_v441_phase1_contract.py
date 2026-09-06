"""v4.4.1 Phase 1 gates: asset safety, ledger integrity, mark geometry, and the byte budget.

These assertions exist because Phase 1 makes three promises that later phases spend:

1. The five approved platform marks are exactly the reviewed bytes. Phase 2 inlines them,
   so a silent re-fetch, re-minify, or hand edit after approval must fail here rather than
   ship an unreviewed third-party asset into a published page.
2. The oversized embedded Nexus mark is gone and its replacement is real vector geometry.
   A blank or raster-backed mark would satisfy a naive size check while destroying the brand.
3. Later illustration work may spend the headroom reserved by Phase 1, while the
   durable 500,000-byte release ceiling remains enforced. The historical 400,000-byte
   checkpoint remains recorded in the phase contract, not imposed on every later build.

The ledger is parsed rather than duplicated: the hashes live in exactly one place, so this
file cannot drift from the approval record it enforces.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE = REPO_ROOT / "guides" / "website" / "nexus-hub-guide.html"
PHASE_DIR = (
    REPO_ROOT
    / "docs"
    / "releases"
    / "v4"
    / "v4.4"
    / "development"
    / "guide-visual-and-arcade-rebuild"
)
LEDGER = PHASE_DIR / "asset-provenance.md"
CONTRACT = PHASE_DIR / "phase-1-contract.md"
ASSETS = PHASE_DIR / "assets"

RELEASE_CEILING = 500_000

APPROVED_MARKS = ("claude", "chatgpt", "gemini", "cursor", "github-copilot")

# Executable or externally-referencing SVG content. Any hit is a hard failure: these files
# are inlined verbatim into a page shipped to readers, so the review is the only gate.
UNSAFE_SVG = re.compile(
    r"<script\b|\son[a-z]+\s*=|<foreignObject\b|<image\b|@import|xlink:href",
    re.IGNORECASE,
)
XMLNS = 'xmlns="http://www.w3.org/2000/svg"'


@pytest.fixture(scope="module")
def guide_text() -> str:
    return GUIDE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ledger_text() -> str:
    return LEDGER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ledger_hashes(ledger_text: str) -> dict[str, str]:
    """Parse the section 1 staging table into {stem: sha256}.

    Parsed, not hardcoded, so this test enforces the approval record instead of a copy of it.
    Scoped to section 1: the Phase 4 output-media table in section 3 stages .svg files too,
    and those are governed by their own hash tests rather than the mark roster.
    """
    section_one = ledger_text.split("## 2.", 1)[0]
    rows = re.findall(
        r"^\|\s*[^|]+\|\s*`assets/([a-z0-9-]+)\.svg`\s*\|\s*([\d,]+)\s*\|\s*`([0-9a-f]{64})`\s*\|$",
        section_one,
        re.MULTILINE,
    )
    return {stem: sha for stem, _size, sha in rows}


@pytest.fixture(scope="module")
def nexus_symbol(guide_text: str) -> str:
    match = re.search(r'<symbol id="nexus-mark".*?</symbol>', guide_text, re.DOTALL)
    assert match, "the guide must still define a #nexus-mark symbol"
    return match.group(0)


# --------------------------------------------------------------------------- ledger


def test_ledger_and_contract_exist() -> None:
    assert LEDGER.is_file(), f"missing asset ledger: {LEDGER}"
    assert CONTRACT.is_file(), f"missing phase-1 contract: {CONTRACT}"


def test_ledger_records_every_approved_mark(ledger_hashes: dict[str, str]) -> None:
    assert set(ledger_hashes) == set(APPROVED_MARKS), (
        "the ledger staging table must list exactly the five approved marks; "
        f"got {sorted(ledger_hashes)}"
    )


def test_ledger_approval_record_is_complete(ledger_text: str) -> None:
    """An unapproved mark blocks Phase 2, so 'pending' must not survive in the record."""
    approval = ledger_text.split("## 4. Approval record", 1)
    assert len(approval) == 2, "the ledger must carry an approval record section"
    body = approval[1]
    assert "pending" not in body.lower(), (
        "an approval row still reads 'pending'; Phase 2 is blocked until every mark is approved"
    )
    for mark in ("Claude", "ChatGPT", "Gemini", "Cursor", "GitHub Copilot"):
        assert re.search(rf"^\|\s*{re.escape(mark)}\s*\|\s*\*\*yes\*\*", body, re.MULTILINE), (
            f"no approved row for {mark}"
        )


def test_ledger_names_the_attribution_obligation(ledger_text: str) -> None:
    """The Copilot codicon is CC BY 4.0, so attribution is mandatory, not stylistic."""
    assert "CC BY 4.0" in ledger_text
    assert "H12" in ledger_text, "the ledger must tie the licence obligation to requirement H12"


# ----------------------------------------------------------------- staged mark bytes


@pytest.mark.parametrize("stem", APPROVED_MARKS)
def test_staged_mark_matches_its_approved_hash(stem: str, ledger_hashes: dict[str, str]) -> None:
    path = ASSETS / f"{stem}.svg"
    assert path.is_file(), f"missing staged asset: {path}"
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual == ledger_hashes[stem], (
        f"{stem}.svg no longer matches its approved hash.\n"
        f"  approved: {ledger_hashes[stem]}\n"
        f"  actual  : {actual}\n"
        "Re-approval is required; do not update the ledger to match the new bytes."
    )


@pytest.mark.parametrize("stem", APPROVED_MARKS)
def test_staged_mark_carries_no_unsafe_or_external_content(stem: str) -> None:
    text = (ASSETS / f"{stem}.svg").read_text(encoding="utf-8")
    hit = UNSAFE_SVG.search(text)
    assert hit is None, f"{stem}.svg contains unsafe SVG content: {hit.group(0)!r}"
    residual = text.replace(XMLNS, "")
    assert "http" not in residual, (
        f"{stem}.svg references an external URL; the shipped page must make no network call"
    )


@pytest.mark.parametrize("stem", APPROVED_MARKS)
def test_staged_mark_has_real_geometry(stem: str) -> None:
    text = (ASSETS / f"{stem}.svg").read_text(encoding="utf-8")
    assert "base64," not in text, f"{stem}.svg embeds a raster payload"
    assert re.search(r"<(?:path|circle|rect|polygon|ellipse)\b", text), (
        f"{stem}.svg has no drawable geometry"
    )
    assert re.search(r'viewBox="[^"]+"', text), f"{stem}.svg must declare a viewBox so CSS can size it"


def test_gemini_identifiers_are_namespaced() -> None:
    """Gemini is the only mark declaring ids, and its upstream names are collision-prone."""
    text = (ASSETS / "gemini.svg").read_text(encoding="utf-8")
    ids = re.findall(r'id="([^"]+)"', text)
    assert ids, "expected gemini.svg to declare gradient/mask/filter ids"
    assert all(i.startswith("nxp-gm-") for i in ids), (
        f"un-namespaced identifiers survive in gemini.svg: "
        f"{[i for i in ids if not i.startswith('nxp-gm-')]}"
    )
    # Every reference must resolve to a namespaced id defined in the same file.
    for ref in re.findall(r"url\(#([^)]+)\)", text):
        assert ref in ids, f"gemini.svg references undefined id {ref!r}"


# ------------------------------------------------------------------- the Nexus mark


def test_nexus_mark_is_vector_not_raster(nexus_symbol: str) -> None:
    assert "base64," not in nexus_symbol, (
        "the Nexus mark regressed to an embedded raster payload; Phase 1 replaced a 220 KB base64 PNG"
    )
    assert "<image" not in nexus_symbol, "the Nexus mark must not use an <image> element"


def test_nexus_mark_has_nonempty_geometry(nexus_symbol: str) -> None:
    """A blank mark would pass a size check while destroying the brand, so assert the shapes."""
    circles = len(re.findall(r"<circle\b", nexus_symbol))
    paths = len(re.findall(r"<path\b", nexus_symbol))
    assert circles >= 5, f"expected four corner nodes plus a centre hub; found {circles} circles"
    assert paths >= 4, f"expected the diagonals plus four quadrant shapes; found {paths} paths"
    assert re.search(r"<linearGradient\b", nexus_symbol), "the quadrant gradients are missing"


def test_nexus_mark_makes_no_external_reference(nexus_symbol: str) -> None:
    assert "http" not in nexus_symbol, "the Nexus mark must not reference an external resource"


def test_nexus_mark_is_compact(nexus_symbol: str) -> None:
    size = len(nexus_symbol.encode("utf-8"))
    assert size < 8_000, (
        f"the Nexus mark symbol is {size} bytes; Phase 1 reduced it from 220,358 to about 2,118 "
        "and the whole per-phase byte allocation depends on it staying small"
    )


# --------------------------------------------------------------------- byte budget


def test_guide_stays_within_the_release_byte_budget(guide_text: str) -> None:
    size = len(guide_text.encode("utf-8"))
    assert size < RELEASE_CEILING, (
        f"guide is {size:,} bytes; the release ceiling is {RELEASE_CEILING:,}"
    )


def test_release_ceiling_is_unchanged() -> None:
    """Phase 1 buys headroom by shrinking content, never by raising the ceiling."""
    sweep = (REPO_ROOT / "tests" / "guides" / "test_nexus_hub_guide.py").read_text(encoding="utf-8")
    assert "SIZE_BUDGET_BYTES = 500_000" in sweep, (
        "the strict 500,000-byte release assertion must remain exactly as shipped in v4.4.0"
    )


def test_contract_records_the_measured_byte_ledger() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for token in ("220,358", "2,118", "269,441", "-218,240"):
        assert token in text, f"the contract byte ledger is missing the measured value {token}"
    assert "500,000" in text and "400,000" in text


def test_contract_registers_every_superseded_assertion() -> None:
    """A later phase must not change these behaviours without updating the register."""
    text = CONTRACT.read_text(encoding="utf-8")
    for assertion in (
        "test_home_lists_six_platforms_without_invented_marks",
        "test_foundations_phase3_has_eight_title_subtitle_scenes",
        "test_foundations_is_project_generic",
        "WIDTHS",
        "test_asteroids_game.py",
    ):
        assert assertion in text, f"the superseded-assertion register omits {assertion}"
