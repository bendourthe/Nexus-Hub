"""Turn a run into the report artifacts the lifecycle contract requires.

Section 6 of `docs/policy/ci-cd-lifecycle-contract.md`: a concise
human summary plus machine-readable evidence, produced by the SAME local
execution a developer can reproduce, deterministic, ASCII-safe, and free of
credentials.

The requirement that carries the most weight is this one: **a failing command
must still produce a readable summary and valid partial metadata.** A run that
fails and reports nothing is indistinguishable from a run that never started,
and the second is the one people assume.
"""

from __future__ import annotations

import hashlib
import json
import math
import stat
import os
import platform as platform_mod
import re
import shutil
import sys
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

#: Substrings that mark an environment variable as secret-bearing. Matching on
#: the NAME rather than trying to recognize secret-shaped VALUES: a token format
#: changes without notice, an env var called *_TOKEN does not.
_SECRET_NAME_HINTS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "KEY", "CREDENTIAL")

REDACTED = "[REDACTED]"

#: A generic bearer-token shape, as a backstop for a value that reaches output
#: without ever having been an environment variable.
_INLINE_SECRET = re.compile(
    r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"
)


def secret_values() -> list[str]:
    """Values of every secret-bearing environment variable, longest first.

    Longest first matters: redacting a short value that is a substring of a
    longer one first would leave a recognizable fragment of the longer one.
    """
    values = []
    for name, value in os.environ.items():
        if not value or len(value) < 8:
            continue
        if any(hint in name.upper() for hint in _SECRET_NAME_HINTS):
            values.append(value)
    return sorted(values, key=len, reverse=True)


def redact(text: str, extra: list[str] | None = None) -> str:
    """Remove known secret values and obvious token shapes from captured output.

    The longest-first ordering is applied HERE rather than only in
    `secret_values()`, because a caller supplying its own list has no reason to
    know the ordering matters. It does: redacting a short value that is a prefix
    of a longer one first leaves a recognizable tail of the longer one behind,
    which is a partial disclosure that reads as a successful redaction.
    """
    if not text:
        return text
    values = extra if extra is not None else secret_values()
    for value in sorted((v for v in values if v), key=len, reverse=True):
        text = text.replace(value, REDACTED)
    return _INLINE_SECRET.sub(REDACTED, text)


@dataclass
class CommandResult:
    name: str
    group: str
    status: str  # "pass" | "fail" | "skip" | "timeout" | "missing" | "advisory-fail"
    duration_s: float = 0.0
    exit_code: int | None = None
    output: str = ""
    reason: str = ""

    @property
    def counts_as_failure(self) -> bool:
        return self.status in ("fail", "timeout", "missing")


@dataclass
class GroupResult:
    name: str
    status: str = "pass"
    commands: list[CommandResult] = field(default_factory=list)
    skipped_reason: str = ""


@dataclass
class RunResult:
    profile: str
    platform: str
    groups: list[GroupResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    duration_s: float = 0.0
    scope_reason: str = ""
    scope_conservative: bool = False

    @property
    def all_commands(self) -> list[CommandResult]:
        return [c for g in self.groups for c in g.commands]

    @property
    def status(self) -> str:
        cmds = self.all_commands
        if any(c.counts_as_failure for c in cmds):
            return "FAIL"
        if not cmds:
            return "PASS"
        if any(c.status in ("skip", "advisory-fail") for c in cmds):
            return "PARTIAL"
        return "PASS"

    def tally(self) -> dict[str, int]:
        counts = {"pass": 0, "fail": 0, "skip": 0, "advisory-fail": 0, "timeout": 0, "missing": 0}
        for c in self.all_commands:
            counts[c.status] = counts.get(c.status, 0) + 1
        return counts


def _source_status(path: Path) -> str:
    """Read a bounded native summary without trusting its display text."""
    if path.stat().st_size > 16_000_000:
        raise ValueError("summary exceeds 16 MB")
    source = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(source, dict) or not isinstance(source.get("profile"), str) or source.get("profile") == "report":
        raise ValueError("not a validation summary")
    groups = source.get("groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError("summary has no groups")
    statuses = []
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("commands"), list):
            raise TypeError("summary has an invalid group")
        for command in group["commands"]:
            if not isinstance(command, dict) or command.get("status") not in {
                "pass", "fail", "skip", "timeout", "missing", "advisory-fail"
            }:
                raise ValueError("summary has an invalid command status")
            statuses.append(command["status"])
    if not statuses:
        raise ValueError("summary has no command results")
    if any(status in {"fail", "timeout", "missing"} for status in statuses):
        return "FAIL"
    if any(status in {"skip", "advisory-fail"} for status in statuses):
        return "PARTIAL"
    return "PASS"


def aggregate_inputs(reports_dir: Path, expected_artifacts: Mapping[str, str] | None = None) -> GroupResult:
    """Index existing job receipts; never execute their contents or validation again."""
    group = GroupResult(name="report-inputs")
    inputs = reports_dir / "inputs"
    if expected_artifacts is None:
        discovered = sorted(path.name for path in inputs.iterdir() if path.is_dir()) if inputs.is_dir() else []
        expected_artifacts = {name: "success" for name in discovered}
        previous = reports_dir / "summary.json"
        if not expected_artifacts and previous.is_file() and not previous.is_symlink():
            try:
                local = inputs / "local"
                local.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(previous, local / "summary.json")
                expected_artifacts = {"local": "success"}
            except OSError:
                pass
    index: dict = {"schema_version": 1, "artifacts": []}
    if not expected_artifacts:
        group.commands.append(CommandResult("report inputs", group.name, "missing", reason="no source receipts"))
    for name, job_result in sorted(expected_artifacts.items()):
        command = CommandResult(name, group.name, "missing")
        entry: dict = {"name": name, "job_result": job_result, "files": []}
        index["artifacts"].append(entry)
        group.commands.append(command)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) or name in {".", ".."}:
            command.reason = "invalid artifact name"
            continue
        if job_result == "skipped":
            if (inputs / name).exists():
                command.status = "fail"
                command.reason = "skipped job unexpectedly has an artifact"
                continue
            command.status = "skip"
            command.reason = "upstream job skipped"
            continue
        if job_result not in {"success", "failure", "cancelled"}:
            command.reason = "invalid upstream job result"
            continue
        artifact = inputs / name
        summary = artifact / "summary.json"
        if not summary.is_file():
            command.reason = "source summary missing"
            continue
        try:
            if artifact.is_symlink() or not artifact.resolve().is_relative_to(reports_dir.resolve()):
                raise ValueError("source artifact leaves reports directory")
            source_status = _source_status(summary)
            files = sorted(path for path in artifact.rglob("*") if path.is_file())
            if len(files) > 2000:
                raise ValueError("source artifact exceeds 2000 files")
            for path in files:
                if path.is_symlink() or not path.resolve().is_relative_to(artifact.resolve()):
                    raise ValueError("source file leaves artifact directory")
                digest = hashlib.sha256()
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(chunk)
                kind = "sarif" if path.suffix == ".sarif" else (
                    "coverage" if path.name.startswith("coverage") else (
                        "junit" if "junit" in path.parts else "report"
                    )
                )
                entry["files"].append({
                    "path": path.relative_to(reports_dir).as_posix(),
                    "sha256": digest.hexdigest(),
                    "bytes": path.stat().st_size,
                    "kind": kind,
                })
            entry["source_status"] = source_status
            command.status = (
                "fail" if job_result != "success" or source_status == "FAIL" else
                "advisory-fail" if source_status == "PARTIAL" else "pass"
            )
            command.reason = f"upstream={job_result}; receipt={source_status}"
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            command.status = "fail"
            command.reason = f"invalid source artifact: {type(exc).__name__}"
    try:
        (reports_dir / "aggregate-index.json").write_text(
            json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    except OSError:
        group.commands.append(CommandResult("aggregate index", group.name, "fail", reason="index write failed"))
    group.status = "fail" if any(command.counts_as_failure for command in group.commands) else "pass"
    return group


# ---------------------------------------------------------------------------
# Artifact writers
# ---------------------------------------------------------------------------


def _rel(path: Path, root: Path) -> str:
    """Repository-relative, forward-slashed. Never an absolute path.

    An absolute path in a report leaks a user name on a developer machine and
    is meaningless on any other, so it fails both the determinism rule and the
    credential rule at once.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def environment_metadata(result: RunResult, tools: dict[str, str] | None = None) -> dict:
    return {
        "profile": result.profile,
        "platform": result.platform,
        "host": platform_mod.node(),
        "shell": "none (direct process execution)",
        "os": platform_mod.system(),
        "os_release": platform_mod.release(),
        "python": platform_mod.python_version(),
        "python_implementation": platform_mod.python_implementation(),
        "tools": dict(sorted((tools or {}).items())),
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "duration_s": round(result.duration_s, 2),
        "status": result.status,
        "scope_reason": result.scope_reason,
        "scope_conservative": result.scope_conservative,
    }


def write_metadata(result: RunResult, reports_dir: Path, tools: dict[str, str] | None = None) -> Path:
    meta_dir = reports_dir / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    path = meta_dir / "environment.json"
    values = secret_values()
    def redact_values(value):
        if isinstance(value, str):
            return redact(value, values)
        if isinstance(value, dict):
            return {key: redact_values(item) for key, item in value.items()}
        if isinstance(value, list):
            return [redact_values(item) for item in value]
        return value

    path.write_text(
        json.dumps(redact_values(environment_metadata(result, tools)), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_junit(result: RunResult, reports_dir: Path) -> list[Path]:
    """One JUnit file per group, so a provider renders groups as suites."""
    junit_dir = reports_dir / "junit"
    junit_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for group in result.groups:
        suite = ET.Element(
            "testsuite",
            {
                "name": group.name,
                "tests": str(len(group.commands)),
                "failures": str(sum(1 for c in group.commands if c.counts_as_failure)),
                "skipped": str(sum(1 for c in group.commands if c.status == "skip")),
                "time": f"{sum(c.duration_s for c in group.commands):.2f}",
            },
        )
        for cmd in group.commands:
            case = ET.SubElement(
                suite,
                "testcase",
                {"classname": group.name, "name": cmd.name, "time": f"{cmd.duration_s:.2f}"},
            )
            if cmd.status == "skip":
                ET.SubElement(case, "skipped", {"message": cmd.reason or "skipped"})
            elif cmd.counts_as_failure or cmd.status == "advisory-fail":
                failure = ET.SubElement(
                    case,
                    "failure",
                    {"message": cmd.reason or f"exit {cmd.exit_code}", "type": cmd.status},
                )
                failure.text = cmd.output[-4000:]
        path = junit_dir / f"{group.name}.xml"
        ET.ElementTree(suite).write(path, encoding="utf-8", xml_declaration=True)
        written.append(path)
    return written


_STATUS_MARK = {
    "pass": "PASS",
    "fail": "FAIL",
    "skip": "SKIP",
    "timeout": "TIMEOUT",
    "missing": "MISSING",
    "advisory-fail": "WARN",
}


def _measurement_bytes(root: Path, path: Path, digest: str | None = None) -> bytes:
    """Read only a small regular artifact confined to its own source receipt."""
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("measurement leaves source artifact")
    for part in (path, *path.parents):
        if part.is_symlink() or getattr(part.lstat(), "st_file_attributes", 0) & 0x400:
            raise ValueError("measurement follows a link")
        if part == root:
            break
    with path.open("rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > 8_000_000:
            raise ValueError("measurement is not a bounded regular file")
        value = stream.read(8_000_001)
    if len(value) > 8_000_000 or (digest is not None and hashlib.sha256(value).hexdigest() != digest):
        raise ValueError("measurement changed from indexed receipt")
    return value


def _coverage_measurement(raw: bytes) -> str:
    text = raw.decode("utf-8-sig")
    if "\x00" in text or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("unsupported coverage XML")
    root = ET.fromstring(text)
    if root.tag != "coverage":
        raise ValueError("not a coverage report")
    rate = float(root.get("line-rate"))
    if not math.isfinite(rate) or not 0 <= rate <= 1:
        raise ValueError("invalid line coverage")
    return f"{rate * 100:.2f}% line coverage"


def _measurement_json(raw: bytes) -> object:
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate measurement field")
            value[key] = item
        return value
    def reject_constant(value):
        raise ValueError("invalid JSON constant")
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    except RecursionError as exc:
        raise ValueError("measurement JSON exceeds parser nesting limit") from exc


def _security_measurement(raw: bytes) -> str:
    value = _measurement_json(raw)
    if not isinstance(value, dict) or value.get("version") != "2.1.0" or not isinstance(value.get("runs"), list) or not value["runs"]:
        raise ValueError("not a SARIF report")
    levels = dict.fromkeys(("error", "warning", "note", "none"), 0)
    for run in value["runs"]:
        if not isinstance(run, dict) or not isinstance(run.get("results"), list):
            raise ValueError("SARIF results missing")
        for finding in run["results"]:
            if not isinstance(finding, dict) or finding.get("level", "warning") not in levels:
                raise ValueError("invalid SARIF level")
            levels[finding.get("level", "warning")] += 1
    return ", ".join(f"{level}: {count}" for level, count in levels.items())


def _summary_cell(value: str) -> str:
    return redact(value).replace("|", r"\|").replace("\r", " ").replace("\n", " ")[:256]


# Shared finite audit evidence validation stays in the existing report owner.
AUDIT_PACKET = "NEXUS_CI_AUDIT "
AUDIT_SCHEMA = "ci-audit-invocation/1"
AUDIT_SOURCE_PACKET = "NEXUS_CI_AUDIT_SOURCE "


def audit_expectations(result: object) -> dict[str, str]:
    """Use the actual producer packet, never a stale filename, as current identity."""
    value = asdict(result) if isinstance(result, RunResult) else result
    found: dict[str, str] = {}
    if not isinstance(value, dict):
        return found
    from scripts.ci.profiles import AUDIT_SCOPES
    groups = value.get("groups", [])
    if not isinstance(groups, list):
        return found
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get("commands", []), list):
            continue
        for command in group.get("commands", []):
            if not isinstance(command, dict):
                continue
            output = command.get("output", "")
            if not isinstance(output, str) or len(output) > 8_000_000:
                continue
            for line in output.splitlines():
                if not line.startswith(AUDIT_PACKET):
                    continue
                try:
                    packet = _measurement_json(line[len(AUDIT_PACKET):].encode())
                    scope, identity = packet["scope"], packet["invocation_id"]
                    if scope not in AUDIT_SCOPES or not isinstance(identity, str) or not re.fullmatch(r"[a-f0-9]{32}", identity):
                        raise ValueError("invalid producer packet")
                    found[scope] = identity if scope not in found else "ambiguous"
                except (ValueError, TypeError, KeyError):
                    continue
    return found


def audit_source_expectations(result: object) -> dict[str, dict]:
    value = asdict(result) if isinstance(result, RunResult) else result
    found = {}
    if not isinstance(value, dict) or not isinstance(value.get("groups"), list):
        return found
    for group in value["groups"]:
        if not isinstance(group, dict) or not isinstance(group.get("commands"), list):
            continue
        for command in group["commands"]:
            if not isinstance(command, dict) or not isinstance(command.get("output"), str):
                continue
            for line in command["output"].splitlines():
                if line.startswith(AUDIT_SOURCE_PACKET):
                    try:
                        packet = _measurement_json(line[len(AUDIT_SOURCE_PACKET):].encode())
                        scope = packet["scope"]
                        if scope in found:
                            found[scope] = {}
                        elif re.fullmatch(r"[a-f0-9]{32}", packet["invocation_id"]) and re.fullmatch(r"[a-f0-9]{64}", packet["source_sha256"]):
                            found[scope] = packet
                    except (ValueError, TypeError, KeyError):
                        continue
    return found


def audit_payload(raw: bytes, scope: str, source: dict) -> str:
    from scripts.ci.profiles import AUDIT_SCOPES
    kind = AUDIT_SCOPES[scope]["kind"]
    if kind == "signatures":
        raw.decode("utf-8")
        return "Signature verification (advisory; see command status)"
    value = _measurement_json(raw)
    if kind == "npm":
        if not isinstance(value, dict) or value.get("error") or value.get("auditReportVersion") != 2:
            raise ValueError("invalid npm audit response")
        counts = value["metadata"]["vulnerabilities"]
        levels = ("info", "low", "moderate", "high", "critical", "total")
        if not isinstance(counts, dict) or any(type(counts.get(key)) is not int or counts[key] < 0 for key in levels):
            raise ValueError("npm vulnerability counts unavailable")
        return ", ".join(f"{key}: {counts[key]}" for key in levels)
    if kind == "pip":
        dependencies = value.get("dependencies") if isinstance(value, dict) else None
        if not isinstance(dependencies, list):
            raise ValueError("pip-audit dependency list unavailable")
        count = 0
        for dependency in dependencies:
            if (not isinstance(dependency, dict) or not isinstance(dependency.get("name"), str)
                    or not isinstance(dependency.get("version"), str) or not isinstance(dependency.get("vulns"), list)
                    or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in dependency["vulns"])):
                raise ValueError("invalid pip-audit dependency")
            count += len(dependency["vulns"])
        return f"vulnerability instances: {count}; dependencies: {len(dependencies)}"
    counts = _security_measurement(raw)
    category = "/language:" + AUDIT_SCOPES[scope]["language"]
    for run in value["runs"]:
        tool, automation, provenance = run.get("tool"), run.get("automationDetails"), run.get("versionControlProvenance")
        if (not isinstance(tool, dict) or not isinstance(tool.get("driver"), dict) or tool["driver"].get("name") != "CodeQL"
                or not isinstance(automation, dict) or not isinstance(automation.get("id"), str) or automation["id"].rstrip("/") != category
                # The CodeQL CLI omits versionControlProvenance (hosted run 45914297627); the manifest source
                # binding and the unchanged-analysis check carry the revision then. A stated revision must match.
                or (provenance is not None and (not isinstance(provenance, list)
                    or not any(isinstance(item, dict) and item.get("revisionId") == source["head"] for item in provenance)))):
            raise ValueError("CodeQL language/category/source provenance mismatch")
    return counts


def audit_evidence(root: Path, scope: str, expected: str, *, hashes: dict[str, str] | None = None,
                   index_root: Path | None = None, require_success: bool = False, expected_source: str | None = None) -> tuple[dict, str]:
    """Read one current, terminal, source-bound output from the fixed finite mapping."""
    from scripts.ci.profiles import AUDIT_SCOPES
    spec = AUDIT_SCOPES[scope]
    if not re.fullmatch(r"[a-f0-9]{32}", expected):
        raise ValueError("current producer identity unavailable")
    def read(relative):
        path = root / relative
        digest = None if hashes is None else hashes[path.relative_to(index_root or root).as_posix()]
        return _measurement_bytes(root, path, digest)
    current = _measurement_json(read(f"security/{scope}.current.json"))
    manifest = _measurement_json(read(f"security/{scope}.manifest.json"))
    if (not isinstance(current, dict) or not isinstance(manifest, dict)
            or any(item.get("schema") != AUDIT_SCHEMA or item.get("scope") != scope or item.get("invocation_id") != expected
                   for item in (current, manifest)) or current.get("source") != manifest.get("source")
            or manifest.get("status") not in {"complete", "failed", "unavailable"}
            or manifest.get("output_valid") is not True):
        raise ValueError("current invocation is incomplete, failed before valid output, or mismatched")
    source = manifest["source"]
    source_digest = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if (manifest.get("source_sha256") != source_digest or current.get("source_sha256") != source_digest
            or (expected_source is not None and expected_source != source_digest)):
        raise ValueError("source changed from current producer binding")
    if (not isinstance(source, dict) or any(not isinstance(source.get(key), str) or not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", source[key]) for key in ("head", "tree"))
            or not isinstance(source.get("files"), list)):
        raise ValueError("source identity unavailable")
    runtime = {"scripts/ci/profiles.py", "scripts/ci/verify_scenarios.py", "scripts/ci/run.py", "scripts/ci/reporting.py"}
    expected_files = runtime | ({".github/workflows/codeql.yml", "scripts/ci/codeql-config.yml"} if spec["kind"] == "sarif"
                                else {".github/workflows/npm-audit.yml", "extensions/" + spec["package"] + "/package-lock.json"} if spec["kind"] in {"npm", "signatures"}
                                else {".github/workflows/supply-chain-watch.yml", "scripts/ci/requirements-py311.txt"})
    files = {}
    for item in source["files"]:
        if (not isinstance(item, dict) or item.get("path") not in expected_files or item["path"] in files
                or not re.fullmatch(r"[a-f0-9]{64}", str(item.get("sha256")))):
            raise ValueError("invalid source file identity")
        files[item["path"]] = item["sha256"]
    if set(files) != expected_files or not isinstance(manifest.get("tool"), dict) or manifest["tool"].get("name") != spec["tool"]:
        raise ValueError("incomplete source/tool identity")
    if spec["kind"] == "sarif":
        if (manifest.get("language") != spec["language"] or manifest.get("category") != "/language:" + spec["language"]
                or manifest.get("config_sha256") != files.get("scripts/ci/codeql-config.yml")
                or not re.fullmatch(r"[a-f0-9]{64}", str(manifest.get("config_sha256")))):
            raise ValueError("CodeQL configuration identity mismatch")
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not 1 <= len(outputs) <= 3:
        raise ValueError("output identity unavailable")
    suffix = {"npm": "json", "pip": "json", "signatures": "txt", "sarif": "sarif"}[spec["kind"]]
    allowed = {"primary": f"security/{scope}.{expected}.{suffix}"}
    if spec["kind"] == "sarif":
        allowed.update(version=f"security/{scope}.{expected}.version.json", packs=f"security/{scope}.{expected}.packs.txt")
    primary, seen, observed = None, set(), {}
    for output in outputs:
        if not isinstance(output, dict):
            raise ValueError("invalid audit output member")
        role = output.get("role")
        if role not in allowed or role in seen or output.get("path") != allowed[role] or not re.fullmatch(r"[a-f0-9]{64}", str(output.get("sha256"))):
            raise ValueError("unexpected audit output member")
        raw = read(output["path"])
        if hashlib.sha256(raw).hexdigest() != output["sha256"] or len(raw) != output.get("bytes"):
            raise ValueError("audit output changed")
        seen.add(role)
        observed[role] = raw
        if role == "primary":
            primary = raw
    if primary is None:
        raise ValueError("primary audit output unavailable")
    if spec["kind"] == "sarif":
        analysis = source.get("analysis")
        if (not isinstance(analysis, dict) or analysis.get("schema") != "codeql-worktree/1"
                or not re.fullmatch(r"[a-f0-9]{64}", str(analysis.get("sha256")))
                or type(analysis.get("files")) is not int or not 0 < analysis["files"] <= 20000
                or type(analysis.get("clean")) is not bool or manifest.get("analysis_after") != analysis):
            raise ValueError("CodeQL analyzed source pre/post identity unavailable or changed")
        if require_success and (analysis["clean"] is not True or source.get("worktree_dirty") is not False):
            raise ValueError("CodeQL upload requires clean analyzed source before and after scanning")
        tool = manifest["tool"]
        version, bundle, packs = tool.get("version"), tool.get("bundle"), tool.get("query_packs")
        if (seen != set(allowed) or not isinstance(version, str) or not version.strip()
                or version.lower().startswith("unavailable") or not isinstance(bundle, dict)
                or bundle.get("version") != version
                or not re.fullmatch(r"[a-f0-9]{64}", str(bundle.get("executable_sha256")))
                or not isinstance(packs, list) or len(packs) != 1):
            raise ValueError("CodeQL tool/bundle/query-pack identity unavailable")
        pack = packs[0]
        target = "codeql/python-queries" if spec["language"] == "python" else "codeql/javascript-queries"
        if (not isinstance(pack, dict) or pack.get("name") != target
                or not isinstance(pack.get("version"), str) or not pack["version"].strip()
                or any(not re.fullmatch(r"[a-f0-9]{64}", str(pack.get(key)))
                       for key in ("content_sha256", "metadata_sha256"))):
            raise ValueError("CodeQL resolved query-pack identity unavailable")
        version_raw = _measurement_json(observed["version"])
        pattern = r"^\s*(" + re.escape(target) + r")@([^:\s]+):\s*\(query\)\s+(.+?qlpack\.yml)\s*$"
        matches = [re.fullmatch(pattern, line) for line in observed["packs"].decode("utf-8").splitlines()]
        matches = [item for item in matches if item]
        if (not isinstance(version_raw, dict) or version_raw.get("version") != version
                or len(matches) != 1 or matches[0][1] != pack["name"] or matches[0][2] != pack["version"]):
            raise ValueError("CodeQL raw version/query-pack observations mismatch")
    text = audit_payload(primary, scope, source)
    if require_success and (manifest["status"] != "complete" or manifest.get("scanner_exit_code") != 0):
        raise ValueError("current scanner did not succeed")
    return manifest, text


def audit_upload_path(reports_dir: Path, scope: str, repo_root: Path, *, require_success: bool = True) -> Path:
    """Select only the matching successful producer's exact output for a provider step."""
    source_summary = _measurement_json(_measurement_bytes(reports_dir, reports_dir / "summary.json"))
    expected = audit_expectations(source_summary).get(scope, "")
    binding = audit_source_expectations(source_summary).get(scope, {})
    if binding.get("invocation_id") != expected:
        raise ValueError("current source producer binding unavailable")
    manifest, _ = audit_evidence(reports_dir, scope, expected, require_success=require_success, expected_source=binding.get("source_sha256", ""))
    if scope.startswith("codeql-"):
        from scripts.ci.verify_scenarios import _audit_analysis_source
        observed = _audit_analysis_source(repo_root, reports_dir, dict(os.environ))
        if observed != manifest["source"]["analysis"] or observed["clean"] is not True:
            raise ValueError("CodeQL analyzed source changed before upload or is not clean")
    for item in manifest["source"]["files"]:
        relative, digest = item["path"], item["sha256"]
        if (not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts
                or hashlib.sha256(_measurement_bytes(repo_root, repo_root / relative)).hexdigest() != digest):
            raise ValueError("producer source changed before upload")
    return reports_dir / next(item["path"] for item in manifest["outputs"] if item["role"] == "primary")


def _audit_measurements(result: RunResult, sources: list, reports_dir: Path) -> tuple[list[str], list[tuple[str, str, str]]]:
    from scripts.ci.profiles import AUDIT_SCOPES
    lines = ["", "## Dependency and CodeQL Audits", "", "| Source | Tool and scope | Current evidence |", "|---|---|---|"]
    tools = []
    for root, hashes in sources:
        expected = audit_expectations(result)
        bindings = audit_source_expectations(result)
        if hashes is not None:
            try:
                path = root / "summary.json"
                source_summary = _measurement_json(_measurement_bytes(root, path, hashes[path.relative_to(reports_dir).as_posix()]))
                expected = audit_expectations(source_summary)
                bindings = audit_source_expectations(source_summary)
            except (OSError, ValueError, TypeError, KeyError):
                expected, bindings = {}, {}
        for scope, spec in AUDIT_SCOPES.items():
            if scope not in expected and not (root / f"security/{scope}.current.json").exists():
                continue
            try:
                binding = bindings.get(scope, {})
                if binding.get("invocation_id") != expected.get(scope):
                    raise ValueError("source producer binding unavailable")
                manifest, observation = audit_evidence(root, scope, expected.get(scope, ""), hashes=hashes, index_root=reports_dir, expected_source=binding.get("source_sha256", ""))
                observation = manifest["status"] + "; " + observation + "; " + next(item["path"] for item in manifest["outputs"] if item["role"] == "primary")
                if spec["kind"] == "sarif" and manifest["source"]["analysis"]["clean"] is not True:
                    observation += "; local dirty source; hosted upload ineligible"
                tools.append((root.relative_to(reports_dir).as_posix(), spec["tool"] + " (" + scope + ")", str(manifest.get("tool", {}).get("version", "Unavailable"))))
            except (OSError, ValueError, TypeError, KeyError, UnicodeError):
                observation = "Unavailable (no valid current invocation/output)"
            lines.append("| " + " | ".join(_summary_cell(item) for item in (root.relative_to(reports_dir).as_posix(), spec["tool"] + " / " + scope, observation)) + " |")
    return lines, tools

def _measurement_sections(result: RunResult, reports_dir: Path, tools: dict[str, str] | None) -> list[str]:
    """Display observations, never infer a passing check or execute a source artifact."""
    sources: list[tuple[Path, dict[str, str] | None]] = [(reports_dir, None)]
    if result.profile == "report":
        sources = []
        try:
            index = _measurement_json(_measurement_bytes(reports_dir, reports_dir / "aggregate-index.json"))
            entries = index["artifacts"]
            if not isinstance(entries, list) or len(entries) > 2000:
                raise ValueError("invalid aggregate index")
            for entry in entries:
                name = entry["name"]
                if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) or name in {".", ".."}:
                    raise ValueError("invalid source artifact")
                if "source_status" not in entry:
                    continue
                files = entry["files"]
                if not isinstance(files, list) or len(files) > 2000:
                    raise ValueError("invalid source file index")
                hashes = {}
                for item in files:
                    relative, digest = item["path"], item["sha256"]
                    if not isinstance(relative, str) or not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest) or relative in hashes:
                        raise ValueError("invalid indexed digest")
                    hashes[relative] = digest
                sources.append((reports_dir / "inputs" / name, hashes))
        except (OSError, ValueError, TypeError, KeyError):
            sources = []
    lines = ["## Measurements", "", "| Source | Coverage | Security findings (SARIF levels) |", "|---|---|---|"]
    tool_rows = []
    for root, hashes in sources:
        values = []
        for filename, parser in (("coverage-ci.xml", _coverage_measurement), ("skill-security.sarif", _security_measurement)):
            try:
                path = root / filename
                digest = None if hashes is None else hashes[path.relative_to(reports_dir).as_posix()]
                values.append(parser(_measurement_bytes(root, path, digest)))
            except (FileNotFoundError, KeyError):
                values.append("Not measured (artifact absent)")
            except (OSError, ValueError, TypeError, ET.ParseError):
                values.append("Unavailable (invalid artifact)")
        label = root.relative_to(reports_dir).as_posix()
        lines.append(f"| {_summary_cell(label)} | {values[0]} | {values[1]} |")
        if hashes is not None:
            try:
                path = root / "metadata" / "environment.json"
                metadata = _measurement_json(_measurement_bytes(root, path, hashes[path.relative_to(reports_dir).as_posix()]))
                source_tools = metadata["tools"]
                if not isinstance(source_tools, dict) or not source_tools or len(source_tools) > 256 or any(not isinstance(k, str) or not isinstance(v, str) for k, v in source_tools.items()):
                    raise ValueError("invalid tool metadata")
                tool_rows.extend((label, key, value) for key, value in sorted(source_tools.items()))
            except (OSError, ValueError, TypeError, KeyError):
                tool_rows.append((label, "Not measured", "Source tool metadata unavailable"))
    if not sources:
        lines.append("| Source receipts | Not measured (no valid source index) | Not measured (no valid source index) |")
    audit_lines, audit_tools = _audit_measurements(result, sources, reports_dir)
    lines += audit_lines
    tool_rows.extend(audit_tools)
    lines += ["", "## Tool Versions", "", "| Source | Tool | Version |", "|---|---|---|"]
    tool_rows.extend(("Current process", key, value) for key, value in sorted((tools or {}).items()))
    if not tool_rows:
        tool_rows.append(("Current process", "Not measured", "No tool versions collected"))
    lines.extend("| " + " | ".join(_summary_cell(cell) for cell in row) + " |" for row in tool_rows)
    return [*lines, ""]


def render_summary(result: RunResult, reports_dir: Path, repo_root: Path, tools: dict[str, str] | None = None) -> str:
    counts = result.tally()
    lines: list[str] = [
        f"# CI Report - profile `{result.profile}` - {result.status}",
        "",
        f"**Platform**: {result.platform} ({platform_mod.system()} {platform_mod.release()})",
        f"**Python**: {platform_mod.python_version()}",
        f"**Duration**: {result.duration_s:.1f}s",
        "",
        "| Result | Count |",
        "|---|---|",
        f"| Passed | {counts['pass']} |",
        f"| Failed | {counts['fail'] + counts['timeout'] + counts['missing']} |",
        f"| Skipped | {counts['skip']} |",
        f"| Advisory failures | {counts['advisory-fail']} |",
        "",
    ]

    lines += _measurement_sections(result, reports_dir, tools)

    if result.scope_reason:
        lines += [f"**Change scope**: {result.scope_reason}", ""]

    lines += ["## Groups", "", "| Group | Status | Commands | Duration |", "|---|---|---|---|"]
    for group in result.groups:
        duration = sum(c.duration_s for c in group.commands)
        detail = group.skipped_reason or f"{len(group.commands)} command(s)"
        lines.append(f"| {group.name} | {group.status.upper()} | {detail} | {duration:.1f}s |")
    lines.append("")

    failures = [c for c in result.all_commands if c.counts_as_failure or c.status == "advisory-fail"]
    if failures:
        lines += ["## Failures", ""]
        for cmd in failures:
            lines += [
                f"### {_STATUS_MARK.get(cmd.status, cmd.status.upper())} `{cmd.group}` / {cmd.name}",
                "",
                f"Exit code: `{cmd.exit_code}`. {cmd.reason}".strip(),
                "",
                "```text",
                (cmd.output or "(no output captured)").rstrip()[-2000:],
                "```",
                "",
            ]
    else:
        lines += ["## Failures", "", "None.", ""]

    lines += [
        "## Artifacts",
        "",
        f"- `{_rel(reports_dir / 'summary.md', repo_root)}`",
        f"- `{_rel(reports_dir / 'summary.json', repo_root)}`",
        f"- `{_rel(reports_dir / 'junit', repo_root)}/<group>.xml`",
        f"- `{_rel(reports_dir / 'metadata' / 'environment.json', repo_root)}`",
    ]
    if result.profile == "report":
        lines.append(f"- `{_rel(reports_dir / 'aggregate-index.json', repo_root)}`")
    lines.append("")
    return "\n".join(lines)


def write_reports(
    result: RunResult,
    reports_dir: Path,
    repo_root: Path,
    tools: dict[str, str] | None = None,
) -> dict[str, Path]:
    """Write every artifact. Safe to call after a failure, and after a crash.

    Each writer is attempted independently: one unwritable artifact must not
    cost the others, because the artifact most likely to fail (JUnit, which
    serializes captured output) is the least important of the four.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    tools = dict(tools or {})
    for scope, identity in audit_expectations(result).items():
        try:
            binding = audit_source_expectations(result).get(scope, {})
            if binding.get("invocation_id") != identity:
                raise ValueError("source producer binding unavailable")
            manifest, _ = audit_evidence(reports_dir, scope, identity, expected_source=binding.get("source_sha256", ""))
            tools[manifest["tool"]["name"] + " (" + scope + ")"] = str(manifest["tool"].get("version", "Unavailable"))
        except (OSError, ValueError, TypeError, KeyError, UnicodeError):
            pass
    written: dict[str, Path] = {}

    for label, writer in (
        ("summary.md", lambda: _write_text(reports_dir / "summary.md", render_summary(result, reports_dir, repo_root, tools))),
        ("summary.json", lambda: _write_text(
            reports_dir / "summary.json",
            json.dumps(asdict(result), indent=2, sort_keys=True) + "\n",
        )),
        ("metadata", lambda: write_metadata(result, reports_dir, tools)),
    ):
        try:
            written[label] = writer()
        except Exception as exc:  # noqa: BLE001 - reporting must never mask the run
            print(f"warning: could not write {label}: {exc}", file=sys.stderr)

    try:
        junit = write_junit(result, reports_dir)
        if junit:
            written["junit"] = junit[0].parent
    except Exception as exc:  # noqa: BLE001
        print(f"warning: could not write junit: {exc}", file=sys.stderr)

    return written


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Explicit newline="\n": the summary is compared across hosts and appended
    # to a provider run summary, so CRLF on a Windows leg would make two
    # identical runs differ byte for byte.
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path
