"""Exercise the local SARIF boundary with valid and adversarial envelopes."""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "catalog/skills/code-review/security-review/scripts"
sys.path.insert(0, str(SCRIPTS))
import _audit_envelope as contract
import _normalized_audit as normalized

spec = importlib.util.spec_from_file_location(
    "application_sarif", SCRIPTS / "emit-sarif.py"
)
sarif = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sarif)
GOLDENS = ROOT / "tests/fixtures/security-audit/envelopes"


@pytest.fixture
def envelope():
    return json.loads((GOLDENS / "degraded.expected.json").read_text())


def seal(value):
    value["run_fingerprint"] = contract.digest(
        {k: v for k, v in value.items() if k != "run_fingerprint"}
    )
    return value


def invoke(value):
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "emit-sarif.py")],
        input=raw,
        capture_output=True,
        check=False,
    )


def test_active_mapping_and_run_binding(envelope):
    result = sarif.emit(envelope, secrets=[])
    run = result["runs"][0]
    assert result["version"] == "2.1.0" and len(run["results"]) == 2
    assert {f["properties"]["disposition"] for f in run["results"]} == {
        "confirmed",
        "needs-live-validation",
    }
    assert run["properties"]["run_fingerprint"] == envelope["run_fingerprint"]
    assert run["properties"]["computed_health"] == "degraded"
    assert run["properties"]["disposition_counts"] == envelope["disposition_counts"]
    assert len(run["properties"]["finding_ledger"]) == 4
    assert all(
        f["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "src/app.py"
        for f in run["results"]
    )


@pytest.mark.parametrize("severity,level", list(sarif.LEVELS.items()))
def test_severity_mapping(envelope, severity, level):
    for finding in envelope["findings"]:
        finding.update(
            severity=severity, release_blocking=severity in {"critical", "high"}
        )
    results = sarif.emit(seal(envelope))["runs"][0]["results"]
    assert all(
        r["level"] == level
        and r["properties"]["release_blocking"] == (severity in {"critical", "high"})
        for r in results
    )


def test_resolved_and_rejected_stay_in_accounting(envelope):
    for finding in envelope["findings"]:
        finding["disposition"] = "rejected"
    envelope["disposition_counts"] = {
        k: 4 if k == "rejected" else 0 for k in contract.DISPOSITIONS
    }
    run = sarif.emit(seal(envelope))["runs"][0]
    assert run["results"] == [] and run["tool"]["driver"]["rules"] == []
    assert run["properties"]["disposition_counts"]["rejected"] == 4


@pytest.mark.parametrize("health", ["complete", "degraded", "failed"])
def test_health_is_preserved_not_readjudicated(envelope, health):
    envelope["computed_health"] = health
    assert (
        sarif.emit(seal(envelope))["runs"][0]["properties"]["computed_health"] == health
    )


@pytest.mark.parametrize(
    "value",
    [
        "../outside",
        "src/../outside",
        "./src/app.py",
        "/etc/passwd",
        "C:/secret",
        "C:secret",
        "C:\\secret",
        "\\\\server\\share",
        "//server/share",
        "\\\\?\\C:\\secret",
        "file:src/app.py",
        "https://example.org/a",
        "src/%2e%2e/a",
        "src/%252e%252e/a",
        "src//app.py",
        "src/./app.py",
        "src/app.py\x00",
        "src/app.py\n",
        "src/\u202eevil.py",
        "src/e\u0301.py",
        "src/app.py.",
        "src/CON.py",
    ],
)
def test_unsafe_locations_emit_no_partial_sarif(envelope, value):
    envelope["findings"][0]["location"]["path"] = value
    result = invoke(seal(envelope))
    assert result.returncode == 2 and not result.stdout
    assert json.loads(result.stderr) == {"error": "application_sarif_invalid"}


@pytest.mark.parametrize(
    "value,uri",
    [
        ("src/with space.py", "src/with%20space.py"),
        ("src/caf\u00e9.py", "src/caf%C3%A9.py"),
        ("src/app.ts", "src/app.ts"),
    ],
)
def test_portable_paths_encode_once(envelope, value, uri):
    for finding in envelope["findings"]:
        finding["location"]["path"] = value
    output = sarif.emit(seal(envelope))
    assert all(
        r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == uri
        for r in output["runs"][0]["results"]
    )


def test_locationless_is_explicit(envelope):
    for finding in envelope["findings"]:
        finding["location"] = {"locationless": True}
    assert all(
        "locations" not in r for r in sarif.emit(seal(envelope))["runs"][0]["results"]
    )


@pytest.mark.parametrize(
    "change",
    [
        lambda e: e.update(schema="raw-schema-v2"),
        lambda e: e.update(schema_version=True),
        lambda e: e.update(decoder="unqualified"),
        lambda e: e.update(run_fingerprint="f" * 64),
        lambda e: e["findings"].append(copy.deepcopy(e["findings"][0])),
        lambda e: e["findings"][0].update(title="conflicting rule title"),
        lambda e: e["findings"][0].update(release_blocking=False, severity="critical"),
        lambda e: e["findings"][0].update(confidence=True),
        lambda e: e["findings"][0].update(properties={"prompt": "private text"}),
        lambda e: e["findings"][0].update(
            evidence_receipt_ids=[contract.opaque("missing")]
        ),
        lambda e: e["artifacts"][0].update(stage_id=contract.opaque("missing")),
        lambda e: e["receipts"][0].update(unknown="private text"),
        lambda e: e["disposition_counts"].update(confirmed=9),
        lambda e: e["routing"]["surface_receipts"][0].update(result="not-checked"),
        lambda e: e["target"].update(root_fingerprint="bad"),
        lambda e: e["target"].update(revision="1" * 41),
        lambda e: e.update(provenance={"execution": "process_observed"}),
    ],
)
def test_malformed_envelopes_are_rejected(envelope, change):
    change(envelope)
    if envelope["run_fingerprint"] != "f" * 64:
        seal(envelope)
    result = invoke(envelope)
    assert result.returncode == 2 and not result.stdout
    assert json.loads(result.stderr) == {"error": "application_sarif_invalid"}


@pytest.mark.parametrize(
    "raw", [b"", b"null", b"{}", b'{"schema":1,"schema":2}', b"NaN", b"{}{}"]
)
def test_strict_stdin_errors(raw):
    result = invoke(raw)
    assert (
        result.returncode == 2
        and not result.stdout
        and b"Traceback" not in result.stderr
    )


def test_alias_collision_rejected(envelope):
    envelope["findings"][0]["location"]["path"] = "src/App.py"
    with pytest.raises(ValueError):
        sarif.emit(seal(envelope))


@pytest.mark.parametrize("name", ["COM\u00b9.py", "LPT\u00b2.py", "COM1 .py", "CON .txt", "NUL .py"])
def test_windows_device_aliases_are_rejected(envelope, name):
    envelope["findings"][0]["location"]["path"] = "src/" + name
    result = invoke(seal(envelope))
    assert result.returncode == 2 and not result.stdout


def test_secret_environment_value_rejected(envelope, monkeypatch):
    monkeypatch.setenv("SARIF_TEST_SECRET", "src/app.py")
    result = invoke(envelope)
    assert (
        result.returncode == 2
        and not result.stdout
        and b"src/app.py" not in result.stderr
    )


def test_recursive_secret_marker_rejected(envelope):
    envelope["findings"][0]["properties"] = {
        "nested": {"secret": "ghp_abcdefghijklmnop"}
    }
    result = invoke(seal(envelope))
    assert result.returncode == 2 and not result.stdout and b"ghp_" not in result.stderr


def test_referenced_paths_are_never_opened(envelope, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected source read")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr(Path, "open", forbidden)
    assert sarif.emit(envelope)["runs"][0]["results"]


def test_qualified_flow_survives(envelope):
    scanner = next(
        r
        for r in envelope["receipts"]
        if r["type"] == "scanner" and r["state"] == "RAN"
    )
    scanner["qualified_symbols"] = [contract.opaque("source"), contract.opaque("sink")]
    finding = next(f for f in envelope["findings"] if f["disposition"] == "confirmed")
    finding.update(
        evidence_receipt_ids=[scanner["id"]],
        source_to_sink={
            name: {
                "symbol": scanner["qualified_symbols"][i],
                "receipt_ids": [scanner["id"]],
            }
            for i, name in enumerate(("source", "sink"))
        },
    )
    result = sarif.emit(seal(envelope))
    assert any(
        r["properties"].get("source_to_sink") == finding["source_to_sink"]
        for r in result["runs"][0]["results"]
    )
    scanner["qualified_symbols"] = []
    with pytest.raises(ValueError):
        sarif.emit(seal(envelope))


def test_real_closure_to_emitter_pipe():
    producer = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "closure-gate.py"),
            str(ROOT / "tests/fixtures/security-audit/application-audit-complete.json"),
            "--summary",
        ],
        capture_output=True,
        check=False,
    )
    assert producer.returncode == 0 and not producer.stderr
    first, second = invoke(producer.stdout), invoke(producer.stdout)
    assert first.returncode == 0 and not first.stderr and first.stdout == second.stdout
    assert json.loads(first.stdout)["version"] == "2.1.0"


def test_empty_local_envelope():
    value = json.loads((GOLDENS / "complete-local.expected.json").read_text())
    assert sarif.emit(value)["runs"][0]["results"] == []


def test_normalized_validation_is_read_only(envelope):
    before = copy.deepcopy(envelope)
    assert normalized.validate(envelope) is envelope
    assert envelope == before


@pytest.mark.parametrize(
    "name",
    [
        "complete-local",
        "degraded",
        "failed",
        "self-attested",
        "content-observed",
        "declined",
        "timed-out",
    ],
)
def test_sarif_goldens(name):
    raw = (GOLDENS / (name + ".expected.json")).read_bytes()
    expected = (
        ROOT / "tests/fixtures/security-audit/sarif" / (name + ".sarif.json")
    ).read_bytes()
    first, second = invoke(raw), invoke(raw)
    assert (
        first.returncode == second.returncode == 0
        and not first.stderr
        and not second.stderr
    )
    assert first.stdout == second.stdout
    assert first.stdout.replace(b"\r\n", b"\n") == expected


def test_order_is_stable_and_rules_are_deduplicated(envelope):
    original = sarif.emit(envelope)["runs"][0]["results"]
    envelope["findings"].reverse()
    seal(envelope)
    assert sarif.emit(envelope)["runs"][0]["results"] == original


@pytest.mark.parametrize("valid", [True, False])
def test_main_stdout_and_error_boundary(envelope, valid, monkeypatch, capsys):
    raw = json.dumps(envelope).encode() if valid else b"{}"
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw)))
    assert sarif.main() == (0 if valid else 2)
    captured = capsys.readouterr()
    if valid:
        assert json.loads(captured.out)["version"] == "2.1.0" and not captured.err
    else:
        assert not captured.out and json.loads(captured.err)["error"] == "application_sarif_invalid"
