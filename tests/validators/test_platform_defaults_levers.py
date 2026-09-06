"""Completeness and evidence tests for the platform lever contract.

Covers v3.16.0 Phase 2. `docs/policy/platform-defaults-levers.md` records, for
every registered integration, whether an official vendor document names a
settable install-time behavioral default.

The load-bearing assertion in this file is
`test_no_platform_in_defaults_without_a_verified_classification`: it is the
machine form of the do-not-invent rule. Nexus-Hub has shipped a fabricated
platform surface before (the `.kimi/agent.yaml` companion, dropped in v3.15.0),
and prose alone cannot prevent a repeat. A test can.

The roster is read from the integration registry rather than hardcoded, so a
newly registered platform fails these tests until it is classified. That is the
intended behavior: an unclassified platform should block, not slip through.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import list_keys  # noqa: E402

CONTRACT = REPO_ROOT / "docs" / "policy" / "platform-defaults-levers.md"
DEFAULTS = REPO_ROOT / "configs" / "platform-defaults.json"

VALID_CLASSES = {"VERIFIED", "UNVERIFIED"}
VALID_ALIGNMENTS = {"Exact", "Near", "Partial", "Mismatch", "-"}

# A summary-table row: first cell is a backticked registry id.
_ROW = re.compile(r"^\|\s*`(?P<id>[a-z0-9-]+)`\s*\|(?P<rest>.*)\|\s*$", re.MULTILINE)
# A per-platform detail heading: "### <id> ..." possibly with a display name.
_DETAIL = re.compile(r"^### (?P<id>[a-z0-9-]+)\b", re.MULTILINE)
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MD_LINK = re.compile(r"\[[^\]]+\]\((?P<url>https://[^)]+)\)")

COLUMNS = ("platform", "klass", "keys", "config_file", "alignment", "source", "verified")


def _strip_emphasis(cell: str) -> str:
    return cell.replace("**", "").strip()


class Row:
    def __init__(self, platform: str, cells: list[str]) -> None:
        self.platform = platform
        (
            self.klass,
            self.keys,
            self.config_file,
            self.alignment,
            self.source,
            self.verified,
        ) = (_strip_emphasis(c) for c in cells)

    @property
    def is_verified(self) -> bool:
        return self.klass == "VERIFIED"


def _parse_rows() -> dict[str, Row]:
    assert CONTRACT.is_file(), f"Missing lever contract: {CONTRACT}"
    body = CONTRACT.read_text(encoding="utf-8")
    rows: dict[str, Row] = {}
    for match in _ROW.finditer(body):
        platform = match.group("id")
        cells = [c.strip() for c in match.group("rest").split("|")]
        assert len(cells) == len(COLUMNS) - 1, (
            f"row {platform!r} has {len(cells)} cells after the id; expected "
            f"{len(COLUMNS) - 1} ({', '.join(COLUMNS[1:])})"
        )
        assert platform not in rows, f"platform {platform!r} appears more than once"
        rows[platform] = Row(platform, cells)
    return rows


@pytest.fixture(scope="module")
def rows() -> dict[str, Row]:
    return _parse_rows()


@pytest.fixture(scope="module")
def contract_body() -> str:
    return CONTRACT.read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# Coverage: every registered integration, exactly once
# --------------------------------------------------------------------------


def test_contract_covers_every_registered_integration(rows: dict[str, Row]):
    """A newly registered platform must fail here until it is classified."""
    registered = set(list_keys())
    missing = sorted(registered - set(rows))
    assert not missing, (
        f"these registered integrations have no row in the lever contract: {missing}. "
        "Research each against its own official documentation and record VERIFIED "
        "(with a source URL and date) or UNVERIFIED (with a reason)."
    )


def test_contract_declares_no_unknown_platform(rows: dict[str, Row]):
    registered = set(list_keys())
    unknown = sorted(set(rows) - registered)
    assert not unknown, (
        f"the lever contract lists platforms that are not in the integration "
        f"registry: {unknown}"
    )


def test_every_platform_appears_exactly_once(rows: dict[str, Row]):
    """Duplicate detection lives in the parser; this asserts the parsed count."""
    assert len(rows) == len(set(list_keys()))


def test_every_platform_has_a_detail_section(rows: dict[str, Row], contract_body: str):
    documented = {m.group("id") for m in _DETAIL.finditer(contract_body)}
    missing = sorted(set(rows) - documented)
    assert not missing, f"these platforms have a table row but no detail section: {missing}"


# --------------------------------------------------------------------------
# Evidence: VERIFIED rows must carry proof
# --------------------------------------------------------------------------


def test_every_row_has_a_known_classification(rows: dict[str, Row]):
    bad = {p: r.klass for p, r in rows.items() if r.klass not in VALID_CLASSES}
    assert not bad, f"rows with an unrecognized classification: {bad}"


def test_every_verified_row_carries_a_source_url(rows: dict[str, Row]):
    """No lever without a citation. This is the do-not-invent rule, column form."""
    missing = sorted(
        p for p, r in rows.items() if r.is_verified and not _MD_LINK.search(r.source)
    )
    assert not missing, (
        f"VERIFIED rows without an https source link: {missing}. A lever is recorded "
        "only when a specific official vendor document names it."
    )


def test_every_verified_row_carries_an_iso_verification_date(rows: dict[str, Row]):
    bad = {
        p: r.verified
        for p, r in rows.items()
        if r.is_verified and not _ISO_DATE.match(r.verified)
    }
    assert not bad, f"VERIFIED rows without a YYYY-MM-DD verification date: {bad}"


def test_every_row_carries_a_verification_date_even_when_unverified(rows: dict[str, Row]):
    """UNVERIFIED still records WHEN it was checked, so a reader can tell
    'no lever documented' apart from 'not yet researched'."""
    bad = {p: r.verified for p, r in rows.items() if not _ISO_DATE.match(r.verified)}
    assert not bad, f"rows without a YYYY-MM-DD verification date: {bad}"


def test_every_verified_row_names_at_least_one_lever_key(rows: dict[str, Row]):
    empty = sorted(p for p, r in rows.items() if r.is_verified and r.keys in ("", "-"))
    assert not empty, f"VERIFIED rows that name no lever key: {empty}"


def test_every_verified_row_names_a_config_file(rows: dict[str, Row]):
    empty = sorted(
        p for p, r in rows.items() if r.is_verified and r.config_file in ("", "-")
    )
    assert not empty, f"VERIFIED rows that name no config file: {empty}"


def test_every_verified_row_declares_a_surface_alignment(rows: dict[str, Row]):
    """Phase 3's gate: VERIFIED means 'consider it', alignment says whether it
    is writable where Nexus-Hub already installs."""
    bad = {
        p: r.alignment
        for p, r in rows.items()
        if r.is_verified and r.alignment not in VALID_ALIGNMENTS - {"-"}
    }
    assert not bad, (
        f"VERIFIED rows with an unrecognized surface alignment: {bad}. "
        f"Expected one of {sorted(VALID_ALIGNMENTS - {'-'})}"
    )


def test_source_urls_are_https(rows: dict[str, Row]):
    for platform, row in rows.items():
        for match in _MD_LINK.finditer(row.source):
            assert match.group("url").startswith("https://"), (
                f"{platform}: source must be an https vendor document"
            )


# --------------------------------------------------------------------------
# UNVERIFIED rows must explain themselves
# --------------------------------------------------------------------------


def test_every_unverified_platform_records_a_reason(rows: dict[str, Row], contract_body: str):
    """"No lever documented" must be distinguishable from "not yet researched"."""
    sections = _split_detail_sections(contract_body)
    missing = []
    for platform, row in rows.items():
        if row.is_verified:
            continue
        section = sections.get(platform, "")
        if "Reason UNVERIFIED" not in section:
            missing.append(platform)
    assert not missing, (
        f"UNVERIFIED platforms whose detail section states no 'Reason UNVERIFIED': "
        f"{missing}"
    )


def test_unverified_rows_declare_no_lever_keys(rows: dict[str, Row]):
    """An UNVERIFIED platform must not carry a half-recorded lever."""
    leaked = sorted(p for p, r in rows.items() if not r.is_verified and r.keys not in ("", "-"))
    assert not leaked, (
        f"UNVERIFIED rows that name lever keys anyway: {leaked}. If a lever is "
        "documented, classify the platform VERIFIED with its evidence."
    )


def _split_detail_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(_DETAIL.finditer(body))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group("id")] = body[match.start() : end]
    return sections


# --------------------------------------------------------------------------
# The do-not-invent rule, in machine form
# --------------------------------------------------------------------------


def test_no_platform_in_defaults_without_a_verified_classification(rows: dict[str, Row]):
    """The assertion this whole file exists for.

    `configs/platform-defaults.json` may declare a platform ONLY when the lever
    contract classifies it VERIFIED. This is what makes shipping a fabricated
    lever a test failure rather than a discovery made by a user whose platform
    silently ignores a setting Nexus-Hub invented for it.
    """
    declared = set(json.loads(DEFAULTS.read_text(encoding="utf-8"))["platforms"])
    verified = {p for p, r in rows.items() if r.is_verified}
    unbacked = sorted(declared - verified)
    assert not unbacked, (
        f"configs/platform-defaults.json declares platforms with no VERIFIED "
        f"classification in {CONTRACT.name}: {unbacked}. Either verify the lever "
        "against that platform's official documentation, or remove the entry."
    )


def test_defaults_source_urls_agree_with_the_contract(rows: dict[str, Row]):
    """A declared platform must cite the same document the contract verified."""
    declared = json.loads(DEFAULTS.read_text(encoding="utf-8"))["platforms"]
    for platform, entry in declared.items():
        row = rows[platform]
        urls = {m.group("url") for m in _MD_LINK.finditer(row.source)}
        assert entry["source_url"] in urls, (
            f"{platform}: configs/platform-defaults.json cites "
            f"{entry['source_url']!r} but the lever contract cites {sorted(urls)}. "
            "The two must agree so provenance is traceable from either direction."
        )


def test_contract_documents_the_scope_boundary_and_the_rule(contract_body: str):
    """The prose guardrails are themselves load-bearing; assert they survive edits."""
    for expected in (
        "platform-read-contracts",
        "do-not-invent",
        ".kimi/agent.yaml",
        "Re-verification log",
    ):
        assert expected in contract_body, (
            f"the lever contract must retain its {expected!r} material"
        )


VERIFICATION_SKILL = (
    REPO_ROOT / "catalog" / "skills" / "workflow" / "platform-contract-verification" / "SKILL.md"
)


def test_reverification_skill_covers_both_contracts():
    """Phase 4.1 acceptance: one pass re-verifies both documents."""
    body = VERIFICATION_SKILL.read_text(encoding="utf-8")
    for doc in ("platform-read-contracts", "platform-defaults-levers"):
        assert doc in body, f"the re-verification skill must name {doc}"


def test_reverification_skill_states_which_contract_hard_gates():
    """The asymmetry is the design; it must be written down, not inferred."""
    body = VERIFICATION_SKILL.read_text(encoding="utf-8").lower()
    assert "hard-gate" in body, "the skill must say which contract gates a release"
    assert "advisor" in body, "the skill must say which contract is advisory"


def test_no_freshness_gate_was_added_for_the_lever_contract():
    """Phase 4.1 acceptance: reuse the existing mechanism, add no new gate.

    A freshness marker or CI check on the lever contract would let a vendor
    renaming a setting wedge every unrelated release. The read-contract gates
    because a stale one silently empties an install; a stale lever contract at
    worst seeds an outdated default the user can change.
    """
    # Checked against EXECUTED lines only. A comment naming the lever contract is
    # fine and in fact desirable (ci.yml explains why docs/policy/ re-triggers the
    # job); what must not exist is a command that gates on it.
    for name, path, is_command in (
        ("Makefile", REPO_ROOT / "Makefile", lambda ln: ln.startswith(("\t", "\t@"))),
        (
            "ci.yml",
            REPO_ROOT / ".github" / "workflows" / "ci.yml",
            lambda ln: ln.lstrip().startswith(("run:", "- run:")),
        ),
    ):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or not is_command(line):
                continue
            assert "platform-defaults-levers" not in line, (
                f"{name} executes a gate on the lever contract, which is advisory "
                f"by design: {stripped!r}"
            )
    scripts = {p.name for p in (REPO_ROOT / "scripts").glob("*.py")}
    assert "check_platform_defaults_freshness.py" not in scripts, (
        "no freshness-marker script may be added for the lever contract"
    )


def test_agents_md_documents_the_defaults_surface():
    """Phase 4.2 acceptance: a contributor can act without reading the plan."""
    body = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for expected in (
        "configs/platform-defaults.json",
        "sync_platform_defaults.py",
        ".kimi/agent.yaml",
        "do-not-invent",
    ):
        assert expected in body, f"AGENTS.md must document {expected}"


def test_base_templates_were_not_touched_by_the_defaults_work():
    """This release introduces no always-loaded instruction text.

    The five base-*.md templates carry text every agent loads on every session.
    A per-platform install default is maintainer-facing configuration, so it
    belongs in AGENTS.md only, and check_base_template_parity.py stays green.
    """
    templates = sorted((REPO_ROOT / "templates" / "ai-instructions").glob("base-*.md"))
    assert templates, "expected the base-*.md templates to exist"
    for path in templates:
        assert "platform-defaults.json" not in path.read_text(encoding="utf-8"), (
            f"{path.name} must not carry platform-defaults text; it is not "
            "always-loaded instruction content"
        )


def test_recorded_counts_match_the_parsed_table(rows: dict[str, Row], contract_body: str):
    """The stated counts line must not drift from the table it summarizes."""
    verified = sum(1 for r in rows.values() if r.is_verified)
    unverified = len(rows) - verified
    expected = f"{verified} VERIFIED, {unverified} UNVERIFIED, {len(rows)} total"
    assert expected in contract_body, (
        f"the counts line should read {expected!r}; update it when a "
        "classification changes"
    )
