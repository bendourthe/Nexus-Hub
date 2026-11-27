"""CI summaries expose existing measurements without rerunning validation."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from scripts.ci import reporting


def fixtures(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'coverage-ci.xml').write_text('<coverage line-rate="0.875"/>', encoding='utf-8')
    (root / 'skill-security.sarif').write_text(json.dumps({'version':'2.1.0','runs':[{'results':[{'level':'error'},{'level':'warning'},{'level':'warning'}]}]}), encoding='utf-8')


def test_write_reports_exposes_real_measurements_and_tools(tmp_path):
    fixtures(tmp_path)
    result = reporting.RunResult('full','windows')
    reporting.write_reports(result, tmp_path, tmp_path, {'pytest':'pytest 9.1.1'})
    text = (tmp_path/'summary.md').read_text(encoding='utf-8')
    assert '87.50%' in text
    assert 'error: 1, warning: 2' in text
    assert 'pytest 9.1.1' in text
    assert result.status == 'PASS'


def test_missing_measurements_never_become_zero_findings(tmp_path):
    text = reporting.render_summary(reporting.RunResult('fast','windows'), tmp_path, tmp_path)
    assert text.count('Not measured') >= 2
    assert 'error: 0' not in text


def test_report_uses_existing_indexed_inputs(tmp_path):
    source = tmp_path/'inputs'/'linux'
    fixtures(source)
    (source/'metadata').mkdir()
    (source/'metadata'/'environment.json').write_text(json.dumps({'tools':{'node':'v22.1.0'}}), encoding='utf-8')
    result = reporting.RunResult('full','linux',groups=[reporting.GroupResult('tests',commands=[reporting.CommandResult('test','tests','pass')])])
    (source/'summary.json').write_text(json.dumps(reporting.asdict(result)), encoding='utf-8')
    group = reporting.aggregate_inputs(tmp_path, {'linux':'success'})
    assert group.status == 'pass'
    report = reporting.RunResult('report','windows',groups=[group])
    reporting.write_reports(report, tmp_path, tmp_path)
    text = (tmp_path/'summary.md').read_text(encoding='utf-8')
    assert 'inputs/linux' in text and '87.50%' in text and 'v22.1.0' in text

@pytest.mark.parametrize("raw", [
    b'<coverage/>', b'<coverage line-rate="nan"/>', b'<coverage line-rate="1.01"/>',
    b'<!DOCTYPE coverage [<!ENTITY rate "0.9">]><coverage line-rate="&rate;"/>',
    b'<not-coverage line-rate="0.9"/>', b'<coverage line-rate="true"/>',
])
def test_present_invalid_coverage_is_unavailable(tmp_path, raw):
    (tmp_path/'coverage-ci.xml').write_bytes(raw)
    text = reporting.render_summary(reporting.RunResult('full','windows'), tmp_path, tmp_path)
    assert '| Unavailable (invalid artifact) | Not measured (artifact absent) |' in text


@pytest.mark.parametrize("raw", [
    b'{"version":"2.1.0","runs":[{}]}', b'{"version":"2.1.0","runs":[]}',
    b'{"version":"2.1.0","runs":[{"results":[{"level":"critical"}]}]}',
    b'{"version":"2.1.0","runs":[{"results":[{"level":"error"}],"results":[]}]}',
])
def test_invalid_sarif_never_becomes_zero_findings(tmp_path, raw):
    (tmp_path/'skill-security.sarif').write_bytes(raw)
    text = reporting.render_summary(reporting.RunResult('full','windows'), tmp_path, tmp_path)
    assert 'Unavailable (invalid artifact)' in text and 'error: 0' not in text


def test_oversize_measurement_is_not_read_as_valid(tmp_path):
    (tmp_path/'coverage-ci.xml').write_bytes(b' ' * 8_000_001)
    text = reporting.render_summary(reporting.RunResult('full','windows'), tmp_path, tmp_path)
    assert 'Unavailable (invalid artifact)' in text


def test_indexed_measurement_tampering_is_unavailable(tmp_path):
    source = tmp_path/'inputs'/'linux'
    fixtures(source)
    result = reporting.RunResult('full','linux',groups=[reporting.GroupResult('tests',commands=[reporting.CommandResult('test','tests','pass')])])
    (source/'summary.json').write_text(json.dumps(reporting.asdict(result)), encoding='utf-8')
    reporting.aggregate_inputs(tmp_path, {'linux':'success'})
    (source/'coverage-ci.xml').write_text('<coverage line-rate="1"/>', encoding='utf-8')
    text = reporting.render_summary(reporting.RunResult('report','windows'), tmp_path, tmp_path)
    assert 'Unavailable (invalid artifact)' in text and '100.00%' not in text


def test_tools_are_redacted_and_table_cells_cannot_inject_rows(tmp_path):
    token = 'gh' + 'p_' + 'B' * 30
    reporting.write_reports(reporting.RunResult('full','windows'), tmp_path, tmp_path, {'fake|tool': 'v1\n' + token})
    text = (tmp_path/'summary.md').read_text(encoding='utf-8')
    assert token not in text and '[REDACTED]' in text and 'fake\\|tool' in text


def test_empty_source_tools_are_explicitly_unavailable(tmp_path):
    source = tmp_path/'inputs'/'linux'
    fixtures(source)
    reporting.write_reports(reporting.RunResult('full','linux',groups=[reporting.GroupResult('tests',commands=[reporting.CommandResult('test','tests','pass')])]),source,tmp_path,{})
    reporting.aggregate_inputs(tmp_path, {'linux':'success'})
    text = reporting.render_summary(reporting.RunResult('report','windows'),tmp_path,tmp_path,{'python':'3.12'})
    assert 'Source tool metadata unavailable' in text


def test_failed_run_retains_failure_with_measurement_artifacts(tmp_path):
    fixtures(tmp_path)
    result = reporting.RunResult('full','windows',groups=[reporting.GroupResult('tests',commands=[reporting.CommandResult('test','tests','fail',exit_code=1)])])
    reporting.write_reports(result,tmp_path,tmp_path)
    text = (tmp_path/'summary.md').read_text(encoding='utf-8')
    assert text.startswith('# CI Report - profile `full` - FAIL') and '87.50%' in text


@pytest.mark.parametrize("filename", ['skill-security.sarif','aggregate-index.json'])
def test_deep_json_cannot_destroy_summary(tmp_path, filename):
    (tmp_path/filename).write_bytes(b'[' * 2000 + b'0' + b']' * 2000)
    profile = 'report' if filename == 'aggregate-index.json' else 'full'
    reporting.write_reports(reporting.RunResult(profile,'windows'),tmp_path,tmp_path)
    text = (tmp_path/'summary.md').read_text(encoding='utf-8')
    assert '## Groups' in text and '## Failures' in text
    assert 'Unavailable' in text or 'no valid source index' in text


def test_measurement_check_does_not_require_python312_path_api(tmp_path, monkeypatch):
    fixtures(tmp_path)
    def unsupported(*args):
        raise AttributeError('is_junction is unavailable on Python 3.11')
    monkeypatch.setattr(Path,'is_junction',unsupported,raising=False)
    text = reporting.render_summary(reporting.RunResult('full','windows'),tmp_path,tmp_path)
    assert '87.50%' in text


def test_windows_reparse_attribute_is_refused(tmp_path, monkeypatch):
    from types import SimpleNamespace
    fixtures(tmp_path)
    original = Path.lstat
    def metadata(path):
        if path == tmp_path/'coverage-ci.xml':
            return SimpleNamespace(st_file_attributes=0x400, st_mode=original(path).st_mode)
        return original(path)
    monkeypatch.setattr(Path,'lstat',metadata)
    text = reporting.render_summary(reporting.RunResult('full','windows'),tmp_path,tmp_path)
    assert 'Unavailable (invalid artifact)' in text


def test_hardlinked_measurement_is_refused(tmp_path):
    import os
    outside = tmp_path/'original.xml'
    outside.write_text('<coverage line-rate="1"/>',encoding='utf-8')
    os.link(outside,tmp_path/'coverage-ci.xml')
    text = reporting.render_summary(reporting.RunResult('full','windows'),tmp_path,tmp_path)
    assert 'Unavailable (invalid artifact)' in text and '100.00%' not in text


def test_deep_source_metadata_does_not_destroy_aggregate(tmp_path):
    source = tmp_path/'inputs'/'linux'
    fixtures(source)
    result = reporting.RunResult('full','linux',groups=[reporting.GroupResult('tests',commands=[reporting.CommandResult('test','tests','pass')])])
    reporting.write_reports(result,source,tmp_path)
    (source/'metadata'/'environment.json').write_bytes(b'[' * 2000 + b'0' + b']' * 2000)
    group = reporting.aggregate_inputs(tmp_path, {'linux':'success'})
    reporting.write_reports(reporting.RunResult('report','windows',groups=[group]),tmp_path,tmp_path)
    text = (tmp_path/'summary.md').read_text(encoding='utf-8')
    assert '87.50%' in text and 'Source tool metadata unavailable' in text


def test_real_windows_junction_is_refused(tmp_path):
    import os
    import subprocess
    if os.name != 'nt':
        pytest.skip('Windows junction control')
    target, junction = tmp_path/'target', tmp_path/'junction'
    fixtures(target)
    subprocess.run(['cmd','/d','/c','mklink','/J',str(junction),str(target)],capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    with pytest.raises(ValueError, match='link'):
        reporting._measurement_bytes(junction,junction/'coverage-ci.xml')



def audit_fixture(root, scope="npm-audit-claude-usage-monitor"):
    import hashlib
    from scripts.ci.profiles import AUDIT_SCOPES
    spec = AUDIT_SCOPES[scope]
    identity = "1" * 32
    paths = ["scripts/ci/profiles.py", "scripts/ci/verify_scenarios.py", "scripts/ci/run.py", "scripts/ci/reporting.py",
             ".github/workflows/npm-audit.yml", "extensions/" + spec["package"] + "/package-lock.json"]
    source = {"head": "a" * 40, "tree": "b" * 40, "parents": [], "worktree_dirty": False,
              "files": [{"path": p, "sha256": "d" * 64} for p in paths]}
    digest = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    raw = json.dumps({"auditReportVersion": 2, "metadata": {"vulnerabilities": {"info": 0, "low": 1, "moderate": 0, "high": 0, "critical": 0, "total": 1}}}).encode()
    relative = "security/" + scope + "." + identity + ".json"
    (root / "security").mkdir(parents=True, exist_ok=True)
    (root / relative).write_bytes(raw)
    manifest = {"schema": reporting.AUDIT_SCHEMA, "scope": scope, "invocation_id": identity, "source": source,
                "source_sha256": digest, "status": "complete", "output_valid": True, "scanner_exit_code": 0,
                "tool": {"name": "npm", "version": "synthetic npm"},
                "outputs": [{"role": "primary", "path": relative, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}]}
    for suffix in ("current", "manifest"):
        (root / "security" / (scope + "." + suffix + ".json")).write_text(json.dumps(manifest))
    packet = reporting.AUDIT_PACKET + json.dumps({"scope": scope, "invocation_id": identity}) + chr(10)
    packet += reporting.AUDIT_SOURCE_PACKET + json.dumps({"scope": scope, "invocation_id": identity, "source_sha256": digest})
    return reporting.RunResult("full", "windows", groups=[reporting.GroupResult(scope, commands=[reporting.CommandResult(scope, scope, "pass", output=packet)])]), manifest


def test_named_audit_preserves_f1_measurements_and_scoped_tools(tmp_path):
    fixtures(tmp_path)
    result, manifest = audit_fixture(tmp_path)
    reporting.write_reports(result, tmp_path, tmp_path, {"pytest": "existing pytest"})
    text = (tmp_path / "summary.md").read_text()
    assert "87.50%" in text and "error: 1, warning: 2" in text and "low: 1" in text
    metadata = json.loads((tmp_path / "metadata/environment.json").read_text())
    assert metadata["tools"]["pytest"] == "existing pytest"
    assert metadata["tools"]["npm (" + manifest["scope"] + ")"] == "synthetic npm"
    assert result.status == "PASS"


def test_old_clean_audit_without_current_producer_is_unavailable(tmp_path):
    result, manifest = audit_fixture(tmp_path)
    failed = reporting.RunResult("full", "windows", groups=[reporting.GroupResult(manifest["scope"], commands=[reporting.CommandResult("new invocation", manifest["scope"], "fail", output="failed before marker")])])
    text = reporting.render_summary(failed, tmp_path, tmp_path)
    assert "Unavailable" in text and "low: 1" not in text and failed.status == "FAIL"


def test_indexed_named_audit_retains_digest_and_rejects_later_raw_tampering(tmp_path):
    source = tmp_path / "inputs" / "scanner"
    result, manifest = audit_fixture(source)
    reporting.write_reports(result, source, source)
    group = reporting.aggregate_inputs(tmp_path, {"scanner": "success"})
    report = reporting.RunResult("report", "windows", groups=[group])
    assert "low: 1" in reporting.render_summary(report, tmp_path, tmp_path)
    (source / manifest["outputs"][0]["path"]).write_text("{}")
    assert "Unavailable" in reporting.render_summary(report, tmp_path, tmp_path)


def test_source_binding_cannot_be_replaced_with_a_different_valid_head(tmp_path):
    import hashlib
    result, manifest = audit_fixture(tmp_path)
    manifest["source"]["head"] = "f" * 40
    manifest["source_sha256"] = hashlib.sha256(json.dumps(manifest["source"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    for suffix in ("current", "manifest"):
        (tmp_path / "security" / (manifest["scope"] + "." + suffix + ".json")).write_text(json.dumps(manifest))
    assert "Unavailable" in reporting.render_summary(result, tmp_path, tmp_path)


def codeql_identity_fixture(root):
    import hashlib
    scope, identity = "codeql-python", "f" * 32
    files = ["scripts/ci/" + name for name in ("profiles.py", "verify_scenarios.py", "run.py", "reporting.py", "codeql-config.yml")]
    files.append(".github/workflows/codeql.yml")
    source = {"head": "a" * 40, "tree": "b" * 40, "parents": [], "worktree_dirty": False,
              "files": [{"path": path, "sha256": "d" * 64} for path in files]}
    source["analysis"] = {"schema": "codeql-worktree/1", "sha256": "c" * 64, "files": 6, "clean": True}
    manifest = {"schema": reporting.AUDIT_SCHEMA, "scope": scope, "invocation_id": identity,
                "source": source, "source_sha256": hashlib.sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "status": "complete", "output_valid": True, "scanner_exit_code": 0,
                "language": "python", "category": "/language:python", "config_sha256": "d" * 64,
                "tool": {"name": "CodeQL", "version": "2.23.0-synthetic",
                         "bundle": {"version": "2.23.0-synthetic", "executable_sha256": "e" * 64},
                         "query_packs": [{"name": "codeql/python-queries", "version": "0.0.1", "content_sha256": "c" * 64, "metadata_sha256": "d" * 64}]}, "outputs": []}
    raw = {"primary": ("sarif", json.dumps({"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "CodeQL"}},
           "automationDetails": {"id": "/language:python"}, "versionControlProvenance": [{"revisionId": source["head"]}], "results": []}]}).encode()),
           "version": ("version.json", b'{"version":"2.23.0-synthetic"}'),
           "packs": ("packs.txt", b'codeql/python-queries@0.0.1: (query) C:/synthetic/qlpack.yml')}
    (root / "security").mkdir()
    for role, (suffix, data) in raw.items():
        relative = f"security/{scope}.{identity}.{suffix}"
        (root / relative).write_bytes(data)
        manifest["outputs"].append({"role": role, "path": relative, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    manifest["analysis_after"] = dict(source["analysis"])
    return manifest


@pytest.mark.parametrize("mutation", ["valid", "version", "bundle", "bundle-version", "executable", "packs", "pack-name", "pack-version", "pack-content", "pack-metadata", "version-role", "packs-role", "raw-version", "raw-packs", "duplicate-pack", "analysis-missing", "analysis-after", "analysis-dirty"])
def test_codeql_identity_requires_bound_raw_tool_and_pack_observations(tmp_path, mutation):
    import hashlib
    manifest = codeql_identity_fixture(tmp_path)
    tool = manifest["tool"]
    if mutation == "analysis-missing": manifest["source"].pop("analysis")
    elif mutation == "analysis-after": manifest["analysis_after"]["sha256"] = "e" * 64
    elif mutation == "analysis-dirty": manifest["analysis_after"]["clean"] = False
    elif mutation in {"version", "bundle"}: tool.pop(mutation)
    elif mutation == "bundle-version": tool["bundle"]["version"] = "different"
    elif mutation == "executable": tool["bundle"]["executable_sha256"] = "unknown"
    elif mutation == "packs": tool.pop("query_packs")
    elif mutation.startswith("pack-"):
        key = {"pack-name": "name", "pack-version": "version", "pack-content": "content_sha256", "pack-metadata": "metadata_sha256"}[mutation]
        tool["query_packs"][0][key] = "unknown"
    elif mutation in {"version-role", "packs-role"}:
        manifest["outputs"] = [item for item in manifest["outputs"] if item["role"] != mutation.split("-")[0]]
    elif mutation in {"raw-version", "raw-packs", "duplicate-pack"}:
        role = "version" if mutation == "raw-version" else "packs"
        item = next(item for item in manifest["outputs"] if item["role"] == role)
        data = b'{"version":"different"}' if role == "version" else b'codeql/python-queries@different: (query) C:/synthetic/qlpack.yml'
        if mutation == "duplicate-pack": data = (tmp_path / item["path"]).read_bytes() * 1 + b"\n" + (tmp_path / item["path"]).read_bytes()
        (tmp_path / item["path"]).write_bytes(data)
        item.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    manifest["source_sha256"] = hashlib.sha256(json.dumps(manifest["source"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    for suffix in ("current", "manifest"):
        (tmp_path / "security" / (manifest["scope"] + "." + suffix + ".json")).write_text(json.dumps(manifest))
    if mutation == "valid":
        reporting.audit_evidence(tmp_path, manifest["scope"], manifest["invocation_id"], require_success=True)
    else:
        with pytest.raises(ValueError, match="CodeQL"):
            reporting.audit_evidence(tmp_path, manifest["scope"], manifest["invocation_id"], require_success=True)
