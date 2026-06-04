"""Tests for the optional OSV dependency-vulnerability module (class 4).

Covers version-constraint matching, manifest coordinate extraction, the
offline-first advisory lookup, the opt-in live merge (with an injected fetcher
-- never a real network call), graceful degradation, the privacy guarantee
(only the coordinate tuple is sent), and the default-OFF wiring.
"""

from __future__ import annotations

from pathlib import Path

from nexus_skill_scanner.analyzers.base import FileUnit
from nexus_skill_scanner.analyzers.dependencies import (
    DependencyVulnerabilityAnalyzer,
    OSVClient,
    extract_coordinates,
    load_offline_db,
    version_in_range,
)
from nexus_skill_scanner.scanner import Scanner
from nexus_skill_scanner.types import Severity


def _unit(src: str, name: str) -> FileUnit:
    return FileUnit.from_path(Path(name), name, src)


# ---- Version-constraint matching -----------------------------------------

def test_version_in_range_basic() -> None:
    assert version_in_range("2.18.0", "<2.20.0") is True
    assert version_in_range("2.20.0", "<2.20.0") is False
    assert version_in_range("1.24.1", ">=1.0.0,<1.24.2") is True
    assert version_in_range("1.24.2", ">=1.0.0,<1.24.2") is False


def test_version_in_range_wildcard_and_unparseable() -> None:
    assert version_in_range("9.9.9", "*") is True
    # A constraint with no operators matches nothing (safer to miss).
    assert version_in_range("1.0.0", "garbage") is False


def test_version_key_ignores_prerelease() -> None:
    # A pre-release suffix is dropped to the numeric release for comparison.
    assert version_in_range("2.0.0rc1", "<2.1.0") is True


# ---- Coordinate extraction -----------------------------------------------

def test_extract_requirements_only_pinned() -> None:
    text = "requests==2.18.0\nflask>=2.0\nurllib3==1.24.1  # comment\n-r other.txt\n"
    coords = extract_coordinates(_unit(text, "requirements.txt"))
    assert coords == [("PyPI", "requests", "2.18.0", 1), ("PyPI", "urllib3", "1.24.1", 3)]


def test_extract_package_json_only_exact() -> None:
    text = '{"dependencies": {"lodash": "4.17.5", "react": "^18.0.0"}, "devDependencies": {"minimist": "1.2.5"}}'
    coords = extract_coordinates(_unit(text, "package.json"))
    pkgs = {(eco, pkg, ver) for eco, pkg, ver, _ in coords}
    assert ("npm", "lodash", "4.17.5") in pkgs
    assert ("npm", "minimist", "1.2.5") in pkgs
    # A caret range is not an exact pin and is skipped.
    assert not any(pkg == "react" for _, pkg, _, _ in coords)


def test_extract_pyproject_pinned() -> None:
    text = '[project]\ndependencies = [\n    "requests==2.18.0",\n    "flask>=2.0",\n]\n'
    coords = extract_coordinates(_unit(text, "pyproject.toml"))
    assert ("PyPI", "requests", "2.18.0") in {(e, p, v) for e, p, v, _ in coords}
    assert not any(p == "flask" for _, p, _, _ in coords)


def test_non_manifest_yields_no_coordinates() -> None:
    assert extract_coordinates(_unit("print('hi')\n", "script.py")) == []


# ---- Offline-first lookup ------------------------------------------------

def test_offline_db_loads() -> None:
    db = load_offline_db()
    assert db and all("package" in entry for entry in db)


def test_offline_match_flags_vulnerable_pin() -> None:
    unit = _unit("requests==2.18.0\nurllib3==1.24.1\n", "requirements.txt")
    findings = DependencyVulnerabilityAnalyzer(online=False).analyze(unit)
    pkgs = {f.title for f in findings}
    assert any("requests" in t for t in pkgs)
    assert any("urllib3" in t for t in pkgs)
    # urllib3 advisory is HIGH per the offline DB.
    assert any(f.severity is Severity.HIGH for f in findings)


def test_safe_version_not_flagged() -> None:
    unit = _unit("requests==2.31.0\n", "requirements.txt")
    assert DependencyVulnerabilityAnalyzer(online=False).analyze(unit) == []


# ---- Opt-in live merge (injected fetcher; never a real network call) -----

def test_online_merge_with_injected_fetcher() -> None:
    def fake_fetch(eco: str, pkg: str, ver: str) -> list[dict]:
        return [{
            "id": "OSV-FAKE-1",
            "summary": "injected advisory",
            "database_specific": {"severity": "HIGH"},
            "aliases": ["CVE-9999-0001"],
        }]

    client = OSVClient(online=True, fetcher=fake_fetch, offline_db=[])
    advisories = client.query("PyPI", "somepkg", "1.0.0")
    assert [a.id for a in advisories] == ["OSV-FAKE-1"]
    assert client.network_used is True
    assert client.network_degraded is False


def test_only_coordinate_tuple_is_sent() -> None:
    captured: list[tuple[str, str, str]] = []

    def recording_fetch(eco: str, pkg: str, ver: str) -> list[dict]:
        captured.append((eco, pkg, ver))
        return []

    client = OSVClient(online=True, fetcher=recording_fetch, offline_db=[])
    client.query("npm", "left-pad", "1.0.0")
    # The fetcher can only ever receive the coordinate tuple -- no source, no
    # prompt, no query text crosses the boundary.
    assert captured == [("npm", "left-pad", "1.0.0")]


def test_network_failure_degrades_to_offline() -> None:
    def boom(eco: str, pkg: str, ver: str) -> list[dict]:
        raise OSError("no network")

    client = OSVClient(online=True, fetcher=boom)
    advisories = client.query("PyPI", "requests", "2.18.0")
    # The offline DB still produced the requests advisory.
    assert any("requests" in (a.summary or "") or a.id for a in advisories)
    assert client.network_degraded is True


def test_analyzer_surfaces_degrade_note() -> None:
    def boom(eco: str, pkg: str, ver: str) -> list[dict]:
        raise OSError("no network")

    client = OSVClient(online=True, fetcher=boom)
    analyzer = DependencyVulnerabilityAnalyzer(client=client)
    analyzer.analyze(_unit("requests==2.18.0\n", "requirements.txt"))
    assert any("osv" in note for note in analyzer.skipped)


# ---- Default-off + scanner integration -----------------------------------

def test_osv_module_is_off_by_default(tmp_path: Path) -> None:
    manifest = tmp_path / "requirements.txt"
    manifest.write_text("requests==2.18.0\n", encoding="utf-8")
    default = Scanner().scan([manifest])
    assert not any("Vulnerable dependency" in f.title for f in default.findings)


def test_osv_scanner_integration_offline(tmp_path: Path) -> None:
    manifest = tmp_path / "requirements.txt"
    manifest.write_text("requests==2.18.0\n", encoding="utf-8")
    # offline-only client keeps the network out of this integration test.
    client = OSVClient(online=False)
    result = Scanner(enable_osv=True, osv_client=client).scan([manifest])
    assert any("Vulnerable dependency: requests" in f.title for f in result.findings)
