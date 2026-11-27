"""Finite audit adapters: synthetic process/report controls, no real scanner calls."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.ci import profiles, reporting, verify_scenarios as scenarios
from tests.fixtures.gh_stub.launcher import make_stub

ROOT = Path(__file__).resolve().parents[2]
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def test_native_audit_groups_are_explicit_and_finite():
    expected = {"npm-audit-" + name for name in ("claude-usage-monitor", "codex-usage-monitor", "cursor-usage-monitor", "gemini-usage-monitor")}
    expected |= {"pip-audit", "codeql-python", "codeql-javascript-typescript"}
    selected = {group.name: group for group in profiles.groups_for("full") if group.name in expected}
    assert set(selected) == expected
    assert all(group.explicit_only for group in selected.values())
    assert all(not command.skip_if_missing for group in selected.values() for command in group.commands)
    for name, group in selected.items():
        assert "scripts/ci/verify_scenarios.py" in group.commands[0].argv
        assert group.commands[0].argv[-1] == name
        if name.startswith("npm-"):
            assert len(group.commands) == 2
            assert group.commands[0].advisory is False
            assert group.commands[1].advisory is True
            assert group.commands[1].argv[-1] == name.replace("npm-audit-", "npm-signatures-", 1)


_STUB = r'''
import json,os,subprocess,sys
from pathlib import Path
args=sys.argv[1:]
tool=Path(sys.argv[0]).stem
if tool not in ('npm','codeql','pip_audit'):
    tool=os.environ.get('AUDIT_STUB_TOOL',tool)
log=Path(os.environ['AUDIT_STUB_LOG'])
with log.open('a',encoding='utf-8') as stream:
    stream.write(json.dumps({'tool':tool,'args':args,'cwd':str(Path.cwd())})+'\n')
mode=os.environ.get('AUDIT_STUB_MODE','clean')
def emit(value,code=0):
    print(json.dumps(value));raise SystemExit(code)
def option(name):
    for index,arg in enumerate(args):
        if arg==name:return args[index+1]
        if arg.startswith(name+'='):return arg.split('=',1)[1]
    raise RuntimeError('missing fixed option '+name)
if tool=='npm':
    if args==['--version']:
        print('22.0.0-synthetic');raise SystemExit(0)
    if args==['audit','signatures']:
        print('synthetic signature evidence');raise SystemExit(9 if mode=='signature-fail' else 0)
    assert args==['audit','--audit-level=high','--json'],args
    if mode=='fail-before':raise SystemExit(17)
    if mode=='partial':print('{');raise SystemExit(13)
    if mode=='transport':emit({'error':{'code':'SYNTHETIC_UNREACHABLE'}},2)
    counts=dict.fromkeys(('info','low','moderate','high','critical','total'),0)
    if mode=='low':counts.update(low=1,total=1)
    if mode=='findings':counts.update(high=1,total=1)
    emit({'auditReportVersion':2,'metadata':{'vulnerabilities':counts}},1 if mode=='findings' else 0)
if tool=='pip_audit':
    if args==['--version']:
        print('pip-audit synthetic');raise SystemExit(0)
    assert args[:5]==['--skip-editable','--progress-spinner','off','--format','json'],args
    if mode=='fail-before':raise SystemExit(17)
    target=Path(option('--output'))
    if mode=='partial':target.write_text('{');raise SystemExit(13)
    vulns=[{'id':'SYNTHETIC-1','fix_versions':['2.0']}] if mode=='findings' else []
    target.write_text(json.dumps({'dependencies':[{'name':'synthetic-package','version':'1.0','vulns':vulns}]}))
    raise SystemExit(1 if vulns else 0)
if tool=='codeql':
    if args==['version','--format=json']:emit({'version':'2.23.0-synthetic'})
    if args==['resolve','packs','--format=text']:
        if mode=='missing-pack':print('no provisioned query pack');raise SystemExit(0)
        for name in ('python','javascript'):
            print('codeql/'+name+'-queries@0.0.1: (query) '+str(Path(os.environ['AUDIT_STUB_PACKS'])/name/'qlpack.yml'))
        raise SystemExit(0)
    assert args[:2] in (['database','create'],['database','analyze']),args
    assert not any(value == 'upload' or value.startswith(('--download','--overwrite','--github-auth','--registries-auth','--auth')) for value in args),args
    database=Path(args[2])
    if args[1]=='create':
        if mode=='create-fail':print('synthetic extraction failed',file=sys.stderr);raise SystemExit(23)
        assert not database.exists()
        database.mkdir()
        source=Path(option('--source-root'))
        if mode in ('drift-py','drift-ts'):
            (source/('analyzed.'+mode.split('-')[1])).write_text('changed during extraction\n')
        revision=subprocess.check_output([os.environ['AUDIT_REAL_GIT'],'-C',str(source),'rev-parse','HEAD'],text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)).strip()
        (database/'source.json').write_text(json.dumps({'revision':revision,'language':option('--language')}))
        raise SystemExit(0)
    if mode=='fail-before':raise SystemExit(17)
    target=Path(option('--output'))
    if mode=='partial':target.write_text('{');raise SystemExit(13)
    source=json.loads((database/'source.json').read_text())
    category=option('--sarif-category')
    if mode=='wrong-category':category='/language:foreign'
    revision='f'*40 if mode=='wrong-source' else source['revision']
    target.write_text(json.dumps({'version':'2.1.0','runs':[{'tool':{'driver':{'name':'CodeQL'}},'automationDetails':{'id':category},'versionControlProvenance':[{'revisionId':revision}],'results':[{'level':'warning'}]}]}))
    raise SystemExit(7 if mode=='analysis-fail' else 0)
raise SystemExit(91)
'''


class AuditCase:
    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.root = tmp / "isolated checkout"
        self.root.mkdir()
        runtime = ("AGENTS.md", "scripts/__init__.py", "scripts/ci/__init__.py", "scripts/nexus_process.py",
                   "scripts/ci/profiles.py", "scripts/ci/change_scope.py", "scripts/ci/run.py", "scripts/ci/reporting.py", "scripts/ci/verify_scenarios.py",
                   "scripts/ci/codeql-config.yml", "scripts/ci/requirements-py311.txt", ".github/workflows/npm-audit.yml",
                   ".github/workflows/supply-chain-watch.yml", ".github/workflows/codeql.yml")
        for relative in runtime:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if relative == "scripts/ci/codeql-config.yml" and not (ROOT / relative).exists():
                destination.write_text("queries:" + chr(10) + "  - uses: security-and-quality" + chr(10) + "paths-ignore:" + chr(10) + "  - .agents/**" + chr(10) + "  - .cursor/commands/**" + chr(10), encoding="utf-8")
            else:
                destination.write_bytes((ROOT / relative).read_bytes())
        # Profile shard discovery reads these file names at import; copy its real inputs without running browser tests.
        for source in sorted((ROOT / "tests/guides").glob("test_training_game_revision*.py")):
            destination = self.root / source.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        for package in ("claude-usage-monitor", "codex-usage-monitor", "cursor-usage-monitor", "gemini-usage-monitor"):
            destination = self.root / "extensions" / package
            destination.mkdir(parents=True)
            (destination / "package-lock.json").write_text('{}', encoding="utf-8")
        (self.root / "pip_audit.py").write_text(_STUB, encoding="utf-8")
        (self.root / "analyzed.py").write_text("answer = 1\n", encoding="utf-8")
        (self.root / "analyzed.ts").write_text("const answer = 1;\n", encoding="utf-8")
        self.bin = tmp / "bin"
        self.bin.mkdir()
        for name in ("npm", "codeql"):
            script = tmp / (name + ".py")
            script.write_text(_STUB, encoding="utf-8")
            executable = make_stub(self.bin, name, script)
            if name == "codeql":
                self.codeql = executable
            if name == "npm" and os.name == "nt":
                (self.bin / "npm.cmd").write_text('@"' + str(executable) + '" %*\n', encoding="ascii")
        packs = tmp / "public-packs"
        for language in ("python", "javascript"):
            folder = packs / language
            folder.mkdir(parents=True)
            (folder / "qlpack.yml").write_text('name: codeql/' + language + '-queries\nversion: 0.0.1\n', encoding="utf-8")
            (folder / "query.ql").write_text('// synthetic query-pack content\n', encoding="utf-8")
        self.git = shutil.which("git")
        assert self.git
        self.env = {key: value for key, value in os.environ.items() if key.upper() in {"SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT"}}
        self.env.update(PATH=str(self.bin) + os.pathsep + str(Path(self.git).parent) + os.pathsep + str(Path(os.environ.get("SystemRoot", "/")) / "System32"),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull, GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
                        HOME=str(tmp / "home"), USERPROFILE=str(tmp / "home"), TEMP=str(tmp), TMP=str(tmp),
                        PYTHONDONTWRITEBYTECODE="1", NEXUS_CI_CODEQL=str(self.codeql), AUDIT_STUB_PACKS=str(packs),
                        AUDIT_STUB_LOG=str(tmp / "tool-calls.jsonl"), AUDIT_REAL_GIT=self.git)
        (tmp / "home").mkdir()
        hooks = tmp / "empty-hooks"
        hooks.mkdir()
        self.invoke([self.git, "init", "-q", str(self.root)])
        self.invoke([self.git, "-C", str(self.root), "add", "."])
        self.invoke([self.git, "-C", str(self.root), "-c", "core.hooksPath=" + str(hooks), "-c", "user.name=Private Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Private synthetic audit fixture"])
        self.reports = tmp / "custom-evidence"

    def invoke(self, argv, **kwargs):
        return subprocess.run(argv, env=self.env, cwd=self.root, capture_output=True, text=True, timeout=90, creationflags=FLAGS, **kwargs)

    def profile(self, group, mode="clean"):
        self.env["AUDIT_STUB_MODE"] = mode
        return self.invoke([sys.executable, "-B", str(self.root / "scripts/ci/run.py"), "--profile", "full", "--only", group, "--reports-dir", str(self.reports), "--quiet"])

    def direct(self, scope, mode="clean"):
        self.env["AUDIT_STUB_MODE"] = mode
        return self.invoke([sys.executable, "-B", str(self.root / "scripts/ci/verify_scenarios.py"), scope, "--reports-dir", str(self.reports)])

    def calls(self):
        path = self.tmp / "tool-calls.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def manifest(self, scope):
        return json.loads((self.reports / "security" / (scope + ".manifest.json")).read_text())


@pytest.fixture
def audit_case(tmp_path):
    return AuditCase(tmp_path)


@pytest.mark.parametrize("scope", ["npm-audit-claude-usage-monitor", "npm-audit-codex-usage-monitor", "npm-audit-cursor-usage-monitor", "npm-audit-gemini-usage-monitor", "pip-audit", "codeql-python", "codeql-javascript-typescript"])
def test_real_profile_scenario_raw_report_and_aggregate_flow(audit_case, scope):
    case = audit_case
    outcome = case.profile(scope)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr
    manifest = case.manifest(scope)
    assert manifest["status"] == "complete" and manifest["output_valid"] is True
    assert manifest["scanner_exit_code"] == 0
    primary = next(item for item in manifest["outputs"] if item["role"] == "primary")
    assert manifest["invocation_id"] in primary["path"]
    raw = (case.reports / primary["path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == primary["sha256"]
    assert reporting.audit_upload_path(case.reports, scope, case.root).is_file()
    text = (case.reports / "summary.md").read_text()
    assert scope in text and "Dependency and CodeQL Audits" in text
    assert (case.reports / "metadata/environment.json").is_file()
    assert list((case.reports / "junit").glob("*.xml"))
    calls = case.calls()
    scans = [row for row in calls if row["args"][:1] == ["audit"] or row["args"][:2] == ["database", "analyze"] or "--skip-editable" in row["args"]]
    assert scans
    aggregate = case.tmp / "aggregate"
    shutil.copytree(case.reports, aggregate / "inputs" / "scanner")
    result = case.invoke([sys.executable, "-B", str(case.root / "scripts/ci/run.py"), "--profile", "report", "--reports-dir", str(aggregate), "--quiet"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert scope in (aggregate / "summary.md").read_text()
    assert primary["sha256"] in (aggregate / "aggregate-index.json").read_text()
    later = [row for row in case.calls() if row["args"][:1] == ["audit"] or row["args"][:2] == ["database", "analyze"] or "--skip-editable" in row["args"]]
    assert later == scans


@pytest.mark.parametrize("mode", ["fail-before", "partial", "transport", "findings"])
def test_required_npm_failure_exports_current_failure_and_skips_signatures(audit_case, mode):
    case = audit_case
    scope = "npm-audit-claude-usage-monitor"
    good = case.profile(scope)
    assert good.returncode == 0
    old = case.manifest(scope)["invocation_id"]
    before = len([row for row in case.calls() if row["args"] == ["audit", "signatures"]])
    failed = case.profile(scope, mode)
    assert failed.returncode != 0
    manifest = case.manifest(scope)
    assert manifest["invocation_id"] != old and manifest["status"] != "complete"
    assert len([row for row in case.calls() if row["args"] == ["audit", "signatures"]]) == before
    summary = (case.reports / "summary.md").read_text()
    assert "FAIL" in summary
    if mode != "findings":
        assert "Unavailable" in summary
    with pytest.raises(ValueError):
        reporting.audit_upload_path(case.reports, scope, case.root)


def test_low_npm_findings_and_signature_advisory_preserve_thresholds(audit_case):
    case = audit_case
    scope = "npm-audit-cursor-usage-monitor"
    low = case.profile(scope, "low")
    assert low.returncode == 0
    assert "low: 1" in (case.reports / "summary.md").read_text()
    advisory = case.profile(scope, "signature-fail")
    assert advisory.returncode == 0
    summary = json.loads((case.reports / "summary.json").read_text())
    commands = summary["groups"][0]["commands"]
    assert commands[0]["status"] == "pass" and commands[1]["status"] == "advisory-fail"


@pytest.mark.parametrize("scope", ["pip-audit", "codeql-python"])
@pytest.mark.parametrize("mode", ["fail-before", "partial"])
def test_direct_invocation_cannot_reuse_previous_clean_output(audit_case, scope, mode):
    case = audit_case
    assert case.profile(scope).returncode == 0
    old = case.manifest(scope)["invocation_id"]
    failed = case.direct(scope, mode)
    assert failed.returncode != 0
    assert case.manifest(scope)["invocation_id"] != old
    with pytest.raises(ValueError):
        reporting.audit_upload_path(case.reports, scope, case.root)


@pytest.mark.parametrize("mode", ["missing-pack", "create-fail", "wrong-category", "wrong-source", "analysis-fail"])
def test_codeql_requires_provisioning_and_valid_source_language_sarif(audit_case, mode):
    case = audit_case
    result = case.profile("codeql-python", mode)
    assert result.returncode != 0
    manifest = case.manifest("codeql-python")
    assert manifest["status"] != "complete"
    if mode in {"missing-pack", "create-fail"}:
        assert not any(row["args"][:2] == ["database", "analyze"] for row in case.calls())
    assert not any(any(value.startswith(("--download", "--github-auth", "--registries-auth")) or value == "upload" for value in row["args"]) for row in case.calls())


@pytest.mark.parametrize("mutation", ["invocation", "source", "config", "digest", "category", "running"])
def test_current_manifest_tampering_refuses_report_and_upload(audit_case, mutation):
    case = audit_case
    scope = "codeql-python"
    assert case.profile(scope).returncode == 0
    path = case.reports / "security" / (scope + ".manifest.json")
    manifest = json.loads(path.read_text())
    if mutation == "invocation":
        manifest["invocation_id"] = "f" * 32
    elif mutation == "source":
        manifest["source"]["head"] = "f" * 40
    elif mutation == "config":
        manifest["config_sha256"] = "f" * 64
    elif mutation == "digest":
        manifest["outputs"][0]["sha256"] = "f" * 64
    elif mutation == "category":
        manifest["category"] = "/language:javascript-typescript"
    else:
        manifest["status"] = "running"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        reporting.audit_upload_path(case.reports, scope, case.root)
    summary = json.loads((case.reports / "summary.json").read_text())
    result = reporting.RunResult("full", "windows", groups=[reporting.GroupResult(g["name"], commands=[reporting.CommandResult(**c) for c in g["commands"]]) for g in summary["groups"]])
    assert "Unavailable" in reporting.render_summary(result, case.reports, case.root)


def test_failed_terminal_publication_is_incomplete_and_restart_is_fresh(audit_case, monkeypatch, capsys):
    case = audit_case
    scope = "npm-audit-claude-usage-monitor"
    assert case.profile(scope).returncode == 0
    old = case.manifest(scope)["invocation_id"]
    original = scenarios._audit_atomic
    def fail_terminal(path, raw, reports):
        if path.name == scope + ".manifest.json" and json.loads(raw).get("status") == "complete":
            raise OSError("synthetic terminal publication interruption")
        return original(path, raw, reports)
    work = case.tmp / "interrupted-work"
    work.mkdir()
    with monkeypatch.context() as patch:
        patch.setattr(scenarios, "_audit_atomic", fail_terminal)
        assert scenarios.audit_scenario(scope, case.root, work, case.env, case.reports) != 0
    interrupted = case.manifest(scope)
    assert interrupted["status"] == "running"
    assert interrupted["invocation_id"] != old
    with pytest.raises(ValueError):
        reporting.audit_upload_path(case.reports, scope, case.root)
    capsys.readouterr()
    assert case.profile(scope).returncode == 0
    current = case.manifest(scope)
    assert current["invocation_id"] not in {old, interrupted["invocation_id"]}
    assert reporting.audit_upload_path(case.reports, scope, case.root).is_file()


def test_concurrent_same_scope_cannot_combine_or_overwrite_current_commit(audit_case, monkeypatch):
    case = audit_case
    scope = "npm-audit-claude-usage-monitor"
    original = scenarios._audit_atomic
    nested, ids = [], []
    work_a, work_b = case.tmp / "work-a", case.tmp / "work-b"
    work_a.mkdir()
    work_b.mkdir()
    def interleave(path, raw, reports):
        if path.name.startswith(scope + ".") and path.suffix == ".json" and not path.name.endswith((".current.json", ".manifest.json")) and not nested:
            nested.append(True)
            assert scenarios.audit_scenario(scope, case.root, work_b, case.env, case.reports) == 0
            ids.append(case.manifest(scope)["invocation_id"])
        return original(path, raw, reports)
    monkeypatch.setattr(scenarios, "_audit_atomic", interleave)
    assert scenarios.audit_scenario(scope, case.root, work_a, case.env, case.reports) != 0
    manifest = case.manifest(scope)
    assert manifest["invocation_id"] == ids[0]
    current = json.loads((case.reports / "security" / (scope + ".current.json")).read_text())
    assert current["invocation_id"] == manifest["invocation_id"]
    reporting.audit_evidence(case.reports, scope, ids[0], expected_source=manifest["source_sha256"])
    assert all(ids[0] in item["path"] for item in manifest["outputs"])


def test_source_observation_failure_invalidates_old_clean_before_scanner(audit_case):
    case = audit_case
    scope = "npm-audit-claude-usage-monitor"
    assert case.profile(scope).returncode == 0
    old = case.manifest(scope)["invocation_id"]
    before = len([row for row in case.calls() if row["args"][:1] == ["audit"]])
    workflow = case.root / ".github/workflows/npm-audit.yml"
    temporary = workflow.with_suffix(".disabled")
    workflow.rename(temporary)
    try:
        failed = case.direct(scope)
        assert failed.returncode != 0
        assert case.manifest(scope)["invocation_id"] != old
        assert len([row for row in case.calls() if row["args"][:1] == ["audit"]]) == before
        with pytest.raises(ValueError):
            reporting.audit_upload_path(case.reports, scope, case.root)
    finally:
        temporary.rename(workflow)


@pytest.mark.parametrize("language,extension", [("python", "py"), ("javascript-typescript", "ts")])
def test_codeql_tracked_source_drift_cannot_be_uploaded(audit_case, language, extension):
    case = audit_case
    before = case.invoke([case.git, "rev-parse", "HEAD", "HEAD^{tree}"]).stdout
    result = case.profile("codeql-" + language, "drift-" + extension)
    assert result.returncode != 0
    assert case.invoke([case.git, "rev-parse", "HEAD", "HEAD^{tree}"]).stdout == before
    manifest = case.manifest("codeql-" + language)
    assert manifest["output_valid"] is False and manifest["status"] != "complete"
    assert "analyzed source changed" in manifest["diagnostic"]
    with pytest.raises(ValueError):
        reporting.audit_upload_path(case.reports, "codeql-" + language, case.root)


@pytest.mark.parametrize("mutation", ["tracked-before", "untracked-in-reports", "tracked-after"])
def test_codeql_upload_requires_current_clean_analyzed_bytes(audit_case, mutation):
    case = audit_case
    scope = "codeql-python"
    if mutation == "tracked-before":
        (case.root / "analyzed.py").write_text("changed before extraction\n")
    if mutation == "untracked-in-reports":
        case.reports = case.root / "reports"
        case.reports.mkdir()
        (case.reports / "hidden.py").write_text("untracked analyzed source\n")
    outcome = case.profile(scope)
    assert outcome.returncode == 0, outcome.stdout + outcome.stderr
    manifest = case.manifest(scope)
    if mutation == "tracked-after":
        (case.root / "analyzed.ts").write_text("changed after extraction\n")
    with pytest.raises(ValueError, match="analyzed|clean"):
        reporting.audit_upload_path(case.reports, scope, case.root)
    if mutation != "tracked-after":
        assert manifest["source"]["analysis"]["clean"] is False
