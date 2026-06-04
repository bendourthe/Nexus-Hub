"""Optional dependency-vulnerability analyzer (detection class 4, supply chain).

This is the live portion of class 4, deliberately kept off the default path. It
extracts pinned dependency coordinates -- ``(ecosystem, package, version)`` --
from a skill's manifests (``requirements.txt``, ``pyproject.toml``,
``package.json``) and checks each against known vulnerabilities.

It is **offline-first**: a small bundled advisory database
(``data/osv_offline.json``) is always consulted, so the scanner flags the most
common vulnerable pins with zero network access (air-gapped). When ``--osv`` is
passed, the OSV.dev API supplements the offline set; on any network failure the
scanner degrades gracefully to the offline list and records itself skipped.

Privacy surface: the live lookup sends ONLY the coordinate tuple
``{ecosystem, package, version}`` to OSV.dev -- never source, prompts, or query
text. It is the single opt-in outbound call in the whole scanner; default scans
(no ``--osv``) make no network call at all. This is a public, free
vulnerability database queried by package coordinate, not a search/scraping
service.
"""

from __future__ import annotations

import importlib.resources as resources
import json
import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from ..types import Finding, Severity
from .base import FileUnit, make_finding

# A fetcher takes a coordinate and returns raw OSV vulnerability records.
OsvFetcher = Callable[[str, str, str], list[dict]]

_OSV_API_URL = "https://api.osv.dev/v1/query"
_DEFAULT_TIMEOUT = 6.0


# ---------------------------------------------------------------------------
# Advisory model + severity mapping
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Advisory:
    """One vulnerability affecting a coordinate."""

    id: str
    summary: str
    severity: Severity
    aliases: tuple[str, ...] = ()

    def label(self) -> str:
        ids = ", ".join((self.id, *self.aliases)).strip(", ")
        return ids or "advisory"


_SEVERITY_BY_LABEL = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "moderate": Severity.MEDIUM,
    "low": Severity.LOW,
}


def _severity_from(label: str | None) -> Severity:
    return _SEVERITY_BY_LABEL.get((label or "").strip().lower(), Severity.MEDIUM)


# ---------------------------------------------------------------------------
# Version-constraint matching (minimal, stdlib-only)
# ---------------------------------------------------------------------------

_CONSTRAINT_RE = re.compile(r"(<=|>=|==|<|>|~=)\s*([0-9][0-9A-Za-z.\-+_]*)")


def _version_key(version: str) -> tuple[int, ...]:
    """Numeric release tuple of a version, stopping at the first pre-release part."""
    nums: list[int] = []
    for part in re.split(r"[._\-+]", version.strip()):
        if part.isdigit():
            nums.append(int(part))
            continue
        lead = re.match(r"\d+", part)
        if lead:
            nums.append(int(lead.group()))
        break
    return tuple(nums)


def _compare(a: tuple[int, ...], b: tuple[int, ...], op: str) -> bool:
    size = max(len(a), len(b))
    a = a + (0,) * (size - len(a))
    b = b + (0,) * (size - len(b))
    if op == "==":
        return a == b
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == ">":
        return a > b
    if op in (">=", "~="):
        return a >= b
    return False


def version_in_range(version: str, constraint: str) -> bool:
    """True if ``version`` satisfies every constraint in ``constraint``.

    ``constraint`` is a comma-separated set of constraints, all of which must
    hold (e.g. ``>=1.0.0,<1.24.2``). ``*`` (or empty) matches every version.
    A constraint with no recognizable operators matches nothing -- safer to
    miss than to flag every version of a package.
    """
    spec = constraint.strip()
    if spec in ("*", ""):
        return True
    parsed = _CONSTRAINT_RE.findall(spec)
    if not parsed:
        return False
    vk = _version_key(version)
    return all(_compare(vk, _version_key(ver), op) for op, ver in parsed)


# ---------------------------------------------------------------------------
# Coordinate extraction from manifests
# ---------------------------------------------------------------------------

# (ecosystem, package, version, line)
Coordinate = tuple[str, str, str, int]

_REQ_PIN_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==\s*([A-Za-z0-9][A-Za-z0-9.\-+_]*)"
)
_PYPROJECT_PIN_RE = re.compile(
    r"""["']([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==\s*([A-Za-z0-9][A-Za-z0-9.\-+_]*)["']"""
)
_EXACT_NPM_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.\-]+)?$")


def _extract_requirements(text: str) -> list[Coordinate]:
    out: list[Coordinate] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].split(";", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        m = _REQ_PIN_RE.match(line)
        if m:
            out.append(("PyPI", m.group(1), m.group(2), line_no))
    return out


def _extract_pyproject(text: str) -> list[Coordinate]:
    out: list[Coordinate] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        for m in _PYPROJECT_PIN_RE.finditer(raw):
            out.append(("PyPI", m.group(1), m.group(2), line_no))
    return out


def _find_line(lines: list[str], name: str) -> int:
    needle = f'"{name}"'
    for i, line in enumerate(lines, start=1):
        if needle in line:
            return i
    return 0


def _exact_npm_version(spec: str) -> str | None:
    spec = spec.strip()
    if spec.startswith("="):
        spec = spec[1:].strip()
    return spec if _EXACT_NPM_RE.match(spec) else None


def _extract_package_json(text: str) -> list[Coordinate]:
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    if not isinstance(data, dict):
        return []
    lines = text.splitlines()
    out: list[Coordinate] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
        deps = data.get(section)
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            if not isinstance(spec, str):
                continue
            version = _exact_npm_version(spec)
            if version:
                out.append(("npm", name, version, _find_line(lines, name)))
    return out


def extract_coordinates(unit: FileUnit) -> list[Coordinate]:
    """Return pinned ``(ecosystem, package, version, line)`` from a manifest unit."""
    fname = unit.path.name.lower()
    if fname == "package.json":
        return _extract_package_json(unit.text)
    if fname == "pyproject.toml":
        return _extract_pyproject(unit.text)
    if fname.endswith("requirements.txt") or (fname.startswith("requirements") and fname.endswith(".txt")):
        return _extract_requirements(unit.text)
    return []


# ---------------------------------------------------------------------------
# OSV client (offline DB + optional live lookup)
# ---------------------------------------------------------------------------


def load_offline_db() -> list[dict]:
    """Load the bundled offline advisory list; ``[]`` if it cannot be read."""
    try:
        resource = resources.files("nexus_skill_scanner") / "data" / "osv_offline.json"
        data = json.loads(resource.read_text(encoding="utf-8"))
    except (FileNotFoundError, ModuleNotFoundError, OSError, json.JSONDecodeError, ValueError):
        return []
    advisories = data.get("advisories", []) if isinstance(data, dict) else []
    return [a for a in advisories if isinstance(a, dict)]


class OSVClient:
    """Resolves advisories for a coordinate, offline-first with optional live lookup.

    The offline advisory DB is always consulted. When ``online`` is true the
    injected ``fetcher`` (defaulting to a stdlib-urllib OSV.dev query) is also
    called; any failure sets ``network_degraded`` and the offline result stands.
    Tests inject a fetcher and never set ``online`` against the real network.
    """

    def __init__(
        self,
        *,
        online: bool = False,
        fetcher: OsvFetcher | None = None,
        offline_db: list[dict] | None = None,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._online = online
        self._fetcher = fetcher
        self._offline = offline_db if offline_db is not None else load_offline_db()
        self._timeout = timeout
        self.network_degraded = False
        self.network_used = False

    def _offline_matches(self, ecosystem: str, package: str, version: str) -> Iterator[Advisory]:
        for entry in self._offline:
            if entry.get("ecosystem", "").lower() != ecosystem.lower():
                continue
            if entry.get("package", "").lower() != package.lower():
                continue
            if version_in_range(version, entry.get("vulnerable", "")):
                yield Advisory(
                    id=entry.get("id", ""),
                    summary=entry.get("summary", ""),
                    severity=_severity_from(entry.get("severity")),
                    aliases=tuple(entry.get("aliases", []) or ()),
                )

    def _default_fetch(self, ecosystem: str, package: str, version: str) -> list[dict]:
        import urllib.request

        payload = json.dumps(
            {"version": version, "package": {"name": package, "ecosystem": ecosystem}}
        ).encode("utf-8")
        request = urllib.request.Request(
            _OSV_API_URL,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "nexus-skill-scanner"},
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310 - fixed OSV.dev host
            body = json.loads(response.read().decode("utf-8"))
        return body.get("vulns", []) if isinstance(body, dict) else []

    @staticmethod
    def _parse_osv_records(records: list[dict]) -> Iterator[Advisory]:
        for record in records:
            if not isinstance(record, dict):
                continue
            severity = "medium"
            db = record.get("database_specific")
            if isinstance(db, dict) and db.get("severity"):
                severity = str(db["severity"])
            yield Advisory(
                id=str(record.get("id", "")),
                summary=str(record.get("summary") or record.get("details") or "").strip()[:300],
                severity=_severity_from(severity),
                aliases=tuple(str(a) for a in record.get("aliases", []) if a),
            )

    def query(self, ecosystem: str, package: str, version: str) -> list[Advisory]:
        """Return de-duplicated advisories for a coordinate (offline-first)."""
        found: dict[str, Advisory] = {}
        for advisory in self._offline_matches(ecosystem, package, version):
            found[advisory.id or advisory.summary] = advisory
        if self._online:
            fetcher = self._fetcher or self._default_fetch
            try:
                for advisory in self._parse_osv_records(fetcher(ecosystem, package, version)):
                    self.network_used = True
                    found.setdefault(advisory.id or advisory.summary, advisory)
            except Exception:  # noqa: BLE001 - any network/parse failure degrades to offline
                self.network_degraded = True
        return list(found.values())


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------


@dataclass
class DependencyVulnerabilityAnalyzer:
    """Flags pinned dependencies with known vulnerabilities (opt-in, class 4).

    Only instantiated when ``--osv`` is passed, so default scans never read a
    manifest or touch the network. Exposes ``skipped`` so the scanner can
    surface a graceful-degrade note when the live lookup was unavailable.
    """

    name: str = "dependencies"
    client: OSVClient | None = None
    online: bool = False
    skipped: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.client is None:
            self.client = OSVClient(online=self.online)
        self._noted_degraded = False

    def analyze(self, unit: FileUnit) -> list[Finding]:
        coordinates = extract_coordinates(unit)
        if not coordinates:
            return []
        findings: list[Finding] = []
        for ecosystem, package, version, line in coordinates:
            for advisory in self.client.query(ecosystem, package, version):
                findings.append(
                    make_finding(
                        detection_class=4,
                        severity=advisory.severity,
                        title=f"Vulnerable dependency: {package} {version} ({ecosystem})",
                        message=f"{advisory.label()}: {advisory.summary}",
                        unit=unit,
                        line=line,
                        snippet=f"{package}=={version}",
                        analyzer=self.name,
                    )
                )
        if self.client.network_degraded and not self._noted_degraded:
            self.skipped.append("osv (live lookup unavailable; used offline advisory DB)")
            self._noted_degraded = True
        return findings
