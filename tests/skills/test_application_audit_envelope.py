"""Summary mode is a deterministic, redacted, bound downstream contract."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "catalog/skills/code-review/security-review/scripts"
sys.path.insert(0,str(SCRIPTS))
import _audit_envelope as envelope

spec = importlib.util.spec_from_file_location("summary_gate", SCRIPTS / "closure-gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def record():
    return json.loads((ROOT / "tests/fixtures/security-audit/application-audit-complete.json").read_text())


def rebind(record):
    p=record["application_audit"]
    p["run_fingerprint"]=gate.profile_fingerprint(p)
    for name in ("stages","surface_receipts","graph_receipts","observed_artifacts"):
        for r in p[name]:
            r["run_fingerprint"]=p["run_fingerprint"]
            if "run_id" in r: r["run_id"]=p["run_id"]
            if name=="graph_receipts": r.update({k:p[k] for k in envelope.BINDINGS})
    for r in p["stages"]+record["scanner_receipts"]+record["remediation_receipts"]+record["verifiers"]: r["binding"]=envelope.binding(p)
    for r in record["scanner_receipts"]:
        if r["state"]=="RAN": r["target_scope"]["fingerprint"]=p["scope_fingerprint"]


def local_record(record,payload=b"local artifact\n"):
    r=copy.deepcopy(record);p=r["application_audit"]
    for k in ("components","review_actions","findings","facts","report_claims","scanner_inventory","scanner_receipts","remediation_receipts","verifiers"): r[k]=[]
    p.update(evaluation_scope="deterministic-local",stages=[],graph_receipts=[],required_stage_identities=[],claimed_health="complete")
    p["observed_artifacts"][0].update(stage_id="closure-gate/evaluate",digest=hashlib.sha256(payload).hexdigest())
    rebind(r)
    return r


def cli(tmp_path,record,*arguments):
    source=tmp_path/'record.json';source.write_text(json.dumps(record),encoding='utf-8')
    return subprocess.run([sys.executable,str(SCRIPTS/'closure-gate.py'),str(source),'--summary',*map(str,arguments)],capture_output=True,check=False)


def test_normalized_findings_and_deterministic_fingerprint(record):
    result=gate.summarize_review_record(record,secrets=[])
    assert result==gate.summarize_review_record(record,secrets=[])
    assert result['schema']==envelope.SCHEMA and result['computed_health']=='degraded'
    assert result['disposition_counts']=={k:1 for k in envelope.DISPOSITIONS}
    fingerprint=result.pop('run_fingerprint');assert fingerprint==envelope.digest(result)
    assert result['input_run_fingerprint']==record['application_audit']['run_fingerprint']
    assert 'Producer title' not in json.dumps(result)
    assert all(r['provenance']=='self_attested' for r in result['receipts'])


def test_observation_cannot_upgrade_host_execution(record,tmp_path):
    data=b'controlled bytes';(tmp_path/'artifact').write_bytes(data)
    record['application_audit']['observed_artifacts'][0]['digest']=hashlib.sha256(data).hexdigest()
    result=cli(tmp_path,record,'--artifact-root',tmp_path,'--observe-artifact','A-envelope=artifact')
    assert result.returncode==0 and not result.stderr
    value=json.loads(result.stdout)
    assert value['computed_health']=='degraded'
    assert value['artifacts'][0]['provenance']=='content_observed'
    assert value['provenance']['execution']=='self_attested'


def test_only_pure_local_evaluation_can_be_complete(record,tmp_path):
    r=local_record(record);(tmp_path/'artifact').write_bytes(b'local artifact\n')
    a=cli(tmp_path,r,'--artifact-root',tmp_path,'--observe-artifact','A-envelope=artifact')
    b=cli(tmp_path,r,'--artifact-root',tmp_path,'--observe-artifact','A-envelope=artifact')
    assert a.returncode==0 and a.stdout==b.stdout and a.stdout.endswith(b'\n')
    value=json.loads(a.stdout);assert value['computed_health']=='complete' and value['evaluation_scope']=='deterministic-local'
    assert value['findings']==[] and value['receipts']==[]


@pytest.mark.parametrize('field',['components','findings','scanner_receipts','remediation_receipts','verifiers'])
def test_local_scope_cannot_hide_host_work(record,field):
    r=local_record(record);r[field]=record[field] or [{'id':'unexpected'}]
    with pytest.raises((ValueError,TypeError,KeyError)): gate.summarize_review_record(r)


@pytest.mark.parametrize('change',[
    lambda r:r['application_audit']['stages'][0].pop('tool_version'),
    lambda r:r['application_audit']['stages'][0].update(duration_ms=-1),
    lambda r:r['application_audit']['stages'][0].update(finished_at='2020-01-01T00:00:00Z'),
    lambda r:r['application_audit']['stages'][0].update(started_at='date'),
    lambda r:r['application_audit']['stages'][0].update(binding={}),
    lambda r:r['application_audit']['stages'][0].update(artifact_ids=['missing']),
    lambda r:r['application_audit']['stages'][0].update(execution_context={}),
    lambda r:r['application_audit']['required_stage_identities'].append('missing-owner'),
    lambda r:r['application_audit']['stages'].append(copy.deepcopy(r['application_audit']['stages'][0])),
    lambda r:r['application_audit']['observed_artifacts'][0].update(run_id='another-run'),
    lambda r:r['application_audit']['target_revalidation'].update(after_digest='f'*64,changed=True),
    lambda r:r['findings'][0].update(release_blocking=False),
    lambda r:r['findings'][0].update(confidence=True),
    lambda r:r['findings'][0].update(evidence_receipt_ids=['missing']),
    lambda r:r['findings'][0].update(source_to_sink='unbound text'),
    lambda r:r['findings'][0].update(location={'path':'../outside','start_line':1,'end_line':2}),
    lambda r:r['findings'][0].update(disposition='maybe'),
    lambda r:r['findings'][0].update(vulnerability_kind='unknown'),
    lambda r:r['scanner_receipts'][0].update(binding={}),
])
def test_invalid_summary_emits_no_partial_envelope(record,tmp_path,change):
    change(record);result=cli(tmp_path,record)
    assert result.returncode==2 and result.stdout==b''
    assert json.loads(result.stderr)['error']=='audit_summary_invalid'


def test_terminal_failure_is_a_failed_envelope(record):
    record['application_audit']['stages'][0].update(state='FAILED',reason_code='FAILED')
    result=gate.summarize_review_record(record)
    assert result['computed_health']=='failed'


def test_artifact_substitution_emits_nothing(record,tmp_path):
    (tmp_path/'bad').write_bytes(b'substituted')
    result=cli(tmp_path,record,'--artifact-root',tmp_path,'--observe-artifact','A-envelope=bad')
    assert result.returncode==2 and not result.stdout


@pytest.mark.parametrize('selection',['A-envelope=../outside','unknown=artifact','malformed','A-envelope='])
def test_invalid_explicit_artifact_selections(record,tmp_path,selection):
    result=cli(tmp_path,record,'--artifact-root',tmp_path,'--observe-artifact',selection)
    assert result.returncode==2 and not result.stdout


def test_record_directed_paths_and_commands_are_not_executed(record,tmp_path):
    marker=tmp_path/'must-not-exist'
    record['application_audit']['observed_artifacts'][0]['path']=str(tmp_path/'must-not-open')
    record['scanner_receipts'][0]['command']=f'create {marker}'
    a=cli(tmp_path,record);b=cli(tmp_path,record)
    assert a.returncode==0 and a.stdout==b.stdout and not marker.exists()
    assert b'must-not' not in a.stdout


def test_secret_values_in_host_metadata_and_properties_are_not_exposed(record):
    marker='private-canary-opaque-value'
    record['application_audit']['stages'][0]['tool_version']=marker
    record['findings'][0].update(title=marker,properties={'secret':marker,'nested':{'prompt':marker}})
    value=gate.summarize_review_record(record,secrets=[marker])
    assert marker not in json.dumps(value)
    assert value['findings'][0]['properties']=={}


def test_redaction_semantics_longest_first():
    assert envelope.redacted('prefix-long prefix ghp_abcdefghijklmnop',['prefix','prefix-long'])=='[REDACTED] [REDACTED] [REDACTED]'


def test_source_to_sink_requires_bound_observed_symbols(record):
    source=envelope.opaque('source');sink=envelope.opaque('sink')
    g=record['application_audit']['graph_receipts'][0]
    g['locations']=[{'path':'src/app.py','symbol':s,'start_line':i+1,'end_line':i+1} for i,s in enumerate([source,sink])]
    finding=record['findings'][0]
    finding.update(evidence_receipt_ids=['G-1'],source_to_sink={'source':{'symbol':source,'receipt_ids':['G-1']},'sink':{'symbol':sink,'receipt_ids':['G-1']}})
    result=gate.summarize_review_record(record)
    f=next(f for f in result['findings'] if f['id']==envelope.opaque(finding['id']))
    assert f['source_to_sink']['source']['symbol']==source
    finding['source_to_sink']['source']['symbol']=envelope.opaque('unobserved')
    with pytest.raises(ValueError): gate.summarize_review_record(record)


def test_legacy_record_rejected_only_by_summary(record,tmp_path):
    record.pop('application_audit')
    assert gate.evaluate_review_record(record)['status']=='clean'
    result=cli(tmp_path,record);assert result.returncode==2 and not result.stdout


@pytest.mark.parametrize('bank',['stages','verifiers'])
def test_host_receipts_cannot_impersonate_qualified_evidence(record,bank):
    receipt=(record['application_audit'] if bank=='stages' else record)[bank][0]
    symbol=envelope.opaque('pretend-symbol');receipt['qualified_symbols']=[symbol]
    endpoint={'symbol':symbol,'receipt_ids':[receipt['id']]}
    record['findings'][0].update(evidence_receipt_ids=[receipt['id']],source_to_sink={'source':endpoint,'sink':endpoint})
    with pytest.raises(ValueError): gate.summarize_review_record(record)


def test_unsupported_metadata_is_not_projected(record):
    marker='private-prompt-canary-command'
    record['application_audit']['stages'][0]['qualified_symbols']=[marker]
    record['scanner_receipts'][0]['required']={'prompt':marker}
    assert marker not in json.dumps(gate.summarize_review_record(record,secrets=[]))


def test_invalid_host_required_is_rejected_even_with_adjusted_required_list(record,tmp_path):
    p=record['application_audit'];p['stages'][0]['required']={'prompt':'private-prompt-canary-command'}
    p['required_stage_identities']=[s['stage_identity'] for s in p['stages'] if s['required'] is True]
    result=cli(tmp_path,record)
    assert result.returncode==2 and not result.stdout and b'private-prompt' not in result.stderr


def test_scanner_locations_cannot_impersonate_qualified_symbols(record):
    receipt=record['scanner_receipts'][0];symbol=envelope.opaque('unobserved-symbol')
    receipt.update(qualified_symbols=[],locations=[{'symbol':symbol}])
    endpoint={'symbol':symbol,'receipt_ids':[receipt['id']]}
    record['findings'][0].update(evidence_receipt_ids=[receipt['id']],source_to_sink={'source':endpoint,'sink':endpoint})
    with pytest.raises(ValueError): gate.summarize_review_record(record)


def test_failed_scanner_fails_aggregate(record):
    scanner=next(r for r in record['scanner_receipts'] if r['scanner_id']=='gitleaks')
    scanner.update(state='FAILED',omission_reason='scanner failed',exit_code=2)
    record['deterministic_coverage']['status']='degraded'
    assert gate.summarize_review_record(record)['computed_health']=='failed'


@pytest.mark.parametrize('change',[
    lambda r:r['application_audit'].update(target_identity='malformed'),
    lambda r:r['scanner_receipts'][0].update(target_scope='malformed'),
    lambda r:r['verifiers'][0].update(state='DECLINED'),
    lambda r:r['verifiers'][0].update(read_only='true'),
    lambda r:r['verifiers'][0].update(identity=r['remediation_receipts'][0]['fixer_identity']),
    lambda r:r['remediation_receipts'][0].update(after_receipt_id='missing'),
    lambda r:next(s for s in r['scanner_receipts'] if s['id']=='SR-semgrep-after')['observed_finding_ids'].append('F-corrected'),
    lambda r:r['application_audit']['stages'][0].update(state='unknown'),
])
def test_review_regressions_fail_without_partial_output(record,tmp_path,change):
    change(record);result=cli(tmp_path,record)
    assert result.returncode==2 and not result.stdout
    assert json.loads(result.stderr)['error']=='audit_summary_invalid'


def test_duplicate_json_keys_are_rejected(tmp_path):
    path=tmp_path/'duplicate.json';path.write_text('{"schema_version":2,"schema_version":2}')
    result=subprocess.run([sys.executable,str(SCRIPTS/'closure-gate.py'),str(path),'--summary'],capture_output=True,check=False)
    assert result.returncode==2 and not result.stdout
    assert json.loads(result.stderr)['error']=='audit_summary_invalid'


def test_new_post_remediation_finding_fails_health(record):
    next(s for s in record['scanner_receipts'] if s['id']=='SR-semgrep-after')['observed_finding_ids'].append('F-new-unresolved')
    result=gate.summarize_review_record(record)
    assert result['computed_health']=='failed' and result['remediation']['closure_state']=='failed'


@pytest.mark.parametrize('change',['unchanged','outside','affected','unknown','reverted'])
def test_mutable_target_summary_decision_table(record,tmp_path,change):
    import _target_manifest

    (tmp_path/'src').mkdir();(tmp_path/'src/app.py').write_text('before');(tmp_path/'notes.txt').write_text('before')
    before=_target_manifest.build_target_manifest(tmp_path)
    if change!='unchanged': (tmp_path/('src/app.py' if change in {'affected','reverted'} else 'notes.txt')).write_text('after')
    if change=='reverted': (tmp_path/'src/app.py').write_text('before')
    after=_target_manifest.build_target_manifest(tmp_path)
    p=record['application_audit'];p.update(scope_paths=['src'],bound_input_paths=[],scope_fingerprint=hashlib.sha256(b'["src"]').hexdigest(),target_root_fingerprint=before['target_root_fingerprint'])
    p['target_identity']['manifest_digest']=before['manifest_digest']
    p['target_revalidation']={'before_digest':before['manifest_digest'],'after_digest':after['manifest_digest'],'changed':before['manifest_digest']!=after['manifest_digest'],'reason_code':'OUT_OF_SCOPE_CHANGE_PROVEN'}
    rebind(record)
    if change in {'affected','unknown'}:
        with pytest.raises(ValueError): gate.summarize_review_record(record,observed_manifests=None if change=='unknown' else (before,after))
    else:
        result=gate.summarize_review_record(record,observed_manifests=(before,after))
        assert result['computed_health']=='degraded'
        assert result['target']['content_manifest_before']==before['manifest_digest']
        assert result['target']['content_manifest_after']==after['manifest_digest']


def test_explicit_artifact_hardlink_rejected(record,tmp_path):
    import os

    source=tmp_path/'source';source.write_bytes(b'bytes');os.link(source,tmp_path/'linked')
    record['application_audit']['observed_artifacts'][0]['digest']=hashlib.sha256(b'bytes').hexdigest()
    result=cli(tmp_path,record,'--artifact-root',tmp_path,'--observe-artifact','A-envelope=linked')
    assert result.returncode==2 and not result.stdout


GOLDENS=ROOT/'tests/fixtures/security-audit/envelopes'


@pytest.mark.parametrize('case',json.loads((GOLDENS/'cases.json').read_text()),ids=lambda c:c['name'])
def test_golden_cli_bytes(case):
    args=[sys.executable,str(SCRIPTS/'closure-gate.py'),str(GOLDENS/(case['name']+'.record.json')),'--summary']
    if case['observe']: args += ['--artifact-root',str(GOLDENS),'--observe-artifact','A-envelope=artifact.txt']
    outputs=[subprocess.run(args,capture_output=True,check=False) for _ in range(2)]
    expected=(GOLDENS/(case['name']+'.expected.json')).read_bytes() if case['exit_code']!=2 else b''
    for result in outputs:
        assert result.returncode==case['exit_code']
        assert result.stdout.replace(b'\r\n',b'\n')==expected
    assert outputs[0].stdout==outputs[1].stdout
