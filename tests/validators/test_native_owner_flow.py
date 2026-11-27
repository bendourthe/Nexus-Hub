"""Private native CLI -> Stop -> measured report -> captured reply -> owner flow.

Uses the existing local Git/GitHub-stand-in fixture. It is source enforcement
evidence, not an installed client, external approval or real provider trial.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .test_completion_minor_record import SESSION, minor, ck, _isolated_git_config  # noqa: F401

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import approval_page
import completion_gate
import run_plan


def test_native_cli_capture_retirement_and_bounded_controller_resume(minor, monkeypatch, capsys):
    home = minor.tmp / 'private-home'
    home.mkdir()
    minor.env.update(HOME=str(home), USERPROFILE=str(home), PYTHONDONTWRITEBYTECODE='1')
    monkeypatch.setenv('HOME', str(home))
    monkeypatch.setenv('USERPROFILE', str(home))
    created = minor.create()
    assert created.returncode == 0, created.stdout + created.stderr
    rendered = minor.render(SESSION, '--action', 'add-class', '--class', 'archive-member', '--page')
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    path = minor.record_path()
    context, record = ck.resolve_minor_controller(path, SESSION, minor_protocol=1, execution_protocol=1)
    original_bytes = path.read_bytes()
    assert not run_plan.continuation_path(path).exists()
    completion_gate._reconcile_stop({'session_id': SESSION, 'hook_event_name': 'Stop',
        'last_assistant_message': rendered.stdout}, path, record, context.root,
        1, 'INCOMPLETE: fixture native tasks remain', [])
    correction = capsys.readouterr()
    assert 'Waiting for you' in correction.out and 'Required actions' in correction.out
    assert path.read_bytes() == original_bytes
    frame = json.loads(run_plan.continuation_path(path).read_text(encoding='utf-8'))
    assert len(frame['disposition']['requests']) == 1
    assert frame['observation']['objective_complete'] is False

    # The test-only wrapper applies the same fixture member declarations used
    # by Minor.run; the production snapshot parser and projection run unchanged.
    driver = minor.tmp / 'snapshot-cli.py'
    driver.write_text(
        'import runpy, sys\n'
        f'sys.path.insert(0, {str(ROOT)!r})\n'
        'from tests.validators.member_declarations import install\n'
        'class Patch:\n'
        '    def setattr(self, obj, key, value): setattr(obj, key, value)\n'
        'install(Patch())\n'
        f'sys.argv[0] = {str(ROOT / "catalog/skills/workflow/implement-phase/scripts/status_snapshot.py")!r}\n'
        'runpy.run_path(sys.argv[0], run_name="__main__")\n', encoding='utf-8')
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    snapshot = subprocess.run([sys.executable, '-B', str(driver), '--repo', str(minor.work),
        '--scope', 'v0.5', '--record', str(path), '--runs-dir', str(minor.runs)],
        cwd=minor.work, env=minor.env, capture_output=True, text=True, timeout=90, **flags)
    assert snapshot.returncode == 0, snapshot.stdout + snapshot.stderr
    data = json.loads(snapshot.stdout)
    assert data['continuation']['state'] == 'waiting_decision'
    snapshot_path = minor.tmp / 'snapshot.json'
    snapshot_path.write_text(snapshot.stdout, encoding='utf-8')
    report = subprocess.run([sys.executable, '-B', str(ROOT / 'catalog/skills/workflow/implement-phase/scripts/status_report.py'),
        '--input', str(snapshot_path), '--json'], cwd=minor.work, env=minor.env,
        capture_output=True, text=True, timeout=30, **flags)
    assert report.returncode == 0, report.stdout + report.stderr
    full = json.loads(report.stdout)['report']
    compact = run_plan.reporting_module('status_report').render(data, 'compact')
    for output in (full, compact):
        assert output.startswith('Waiting for you')
        assert output.index('Required actions') < output.index('### ' + run_plan.reporting_module('status_report').GOALS_ICON + ' Goals')
        assert 'Prerequisites:' in output and 'Acknowledgment:' in output

    pending = json.loads((minor.runs / 'pending' / (path.stem + '.json')).read_text(encoding='utf-8'))
    capture = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/completion_gate.py'), 'capture'],
        input=json.dumps({'session_id': SESSION, 'prompt': pending['paste_lines'][0]}),
        cwd=minor.work, env=minor.env, capture_output=True, text=True, timeout=30, **flags)
    assert capture.returncode == 0, capture.stderr
    operation = minor.run('record', 'add-class', '--minor', 'v0.5', '--session', SESSION, '--class', 'archive-member')
    assert operation.returncode == 0, operation.stdout + operation.stderr
    context, record = ck.resolve_minor_controller(path, SESSION, minor_protocol=1, execution_protocol=1)
    scope = SimpleNamespace(minor=True, label='v0.5', repo_root=context.root)
    first = run_plan.continuation_for_run(scope, path, record, 1, 'INCOMPLETE: fixture native tasks remain', claim_refresh=True)
    assert first['state'] == 'reconciliation_required' and first['directive'] == 'continue'
    second = run_plan.continuation_for_run(scope, path, record, 1, 'INCOMPLETE: fixture native tasks remain', claim_refresh=True)
    assert second['directive'] == 'wait' and 'No owner reply or duplicate capture' in second['reason']

    # Reconcile the actual next approved member task. No request or resolution is
    # supplied by this input: those are recovered and retired by the native owner.
    approved = ck._minor_module().effective_members(ck, record)[0]
    observations = minor.tmp / 'actual-next-task.json'
    observations.write_text(json.dumps({'objective': frame['observation']['objective'],
        'objective_complete': False, 'objective_source': frame['observation']['objective_source'],
        'remaining_tasks': frame['observation']['remaining_tasks'],
        'work': [{'id': 'fixture-approved-next-task', 'title': 'Implement the next approved member task',
                  'authorized': True, 'feasible': True,
                  'evidence': 'Verified native member ' + approved['version'] + ' at ' + approved['plan_path']}]}), encoding='utf-8')
    observed = []
    def checker_run(args):
        result = minor.run(*args)
        observed.append({'args': args, 'exit_code': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        (minor.tmp / 'controller-check-observations.json').write_text(json.dumps(observed, indent=2), encoding='utf-8')
        return result.returncode, result.stdout
    monkeypatch.setattr(run_plan, '_checker_run', checker_run)
    monkeypatch.chdir(minor.work)
    try:
        assert run_plan.cmd_reconcile('v0.5', str(observations)) == 0
    except run_plan.RunnerError as error:
        raise AssertionError(str(error) + '\n' + json.dumps(observed[-1], indent=2)[:5000]) from error
    final = json.loads(capsys.readouterr().out)
    assert final['disposition']['state'] == 'working'
    assert final['disposition']['requests'] == []
    assert len(final['disposition']['resolved_requests']) == 1
    assert path.read_bytes() != original_bytes


@pytest.mark.parametrize('historical',[False,True])
def test_native_resume_discovery_report_and_saved_result_preserve_original_objective(minor, monkeypatch, capsys,historical):
    import time
    import approval_binding as binding
    from .test_codex_transcript_approval import Transcript, SESSION as NEXT_SESSION
    assert minor.create().returncode == 0
    path = minor.record_path()
    context, before = ck.resolve_minor_controller(path, SESSION, minor_protocol=1, execution_protocol=1)
    scope = SimpleNamespace(minor=True,label='v0.5',repo_root=context.root,observer_session=SESSION)
    reporter = run_plan.reporting_module('status_snapshot')
    from datetime import datetime, timezone
    repository = reporter.Repo(context.root,'develop')
    members = ck._minor_module().effective_members(ck,before)
    remaining = sum(reporter.measure_row(repository,member['version'],context.root/member['plan_path'],
        datetime.now(timezone.utc),None,{})['_open'] for member in members)
    objective = 'Implement all approved v0.5 members, preserve the approved consent, and verify the native minor closure.'
    facts = {'objective':objective,'remaining_tasks':remaining,'work':[{'id':'next-approved-task',
        'title':'Implement the next approved member task','authorized':True,'feasible':True,
        'evidence':'Native approved member '+members[0]['version']+' at '+members[0]['plan_path']}],
        'requests':[],'jobs':[],'external_conditions':[]}
    frame = run_plan.reconcile_observation(scope,path,before,facts,1,'INCOMPLETE: approved tasks remain',readonly=True)
    run_plan.save_continuation(path,frame)
    original_frame = run_plan.continuation_path(path).read_bytes()
    old_line=None
    if historical:
        old_render=minor.render(SESSION,'--action','add-class','--class','archive-member','--page')
        assert old_render.returncode==0,old_render.stdout+old_render.stderr
        assert binding.observe_issued_request(minor.runs,path.stem,ck._secret(create=False),before,old_render.stdout)
        old_pending=json.loads((minor.runs/'pending'/(path.stem+'.json')).read_text(encoding='utf-8'))
        old_line=old_pending['paste_lines'][0]
    home = minor.tmp/'private-resume-home'
    home.mkdir()
    log = Transcript(home,minor.work,time.time()-10)
    for name in ('HOME','USERPROFILE'):
        minor.env[name] = str(home)
        monkeypatch.setenv(name,str(home))
    monkeypatch.setattr(Path,'home',classmethod(lambda cls:home))
    rendered = minor.render(NEXT_SESSION,'--action','resume','--question','--host-transcript',str(log.path))
    assert rendered.returncode == 0, rendered.stdout+rendered.stderr
    pending = json.loads((minor.runs/'pending'/(path.stem+'.json')).read_text(encoding='utf-8'))
    delivered_page = approval_page.render_page(approval_page.render_data(pending,scope='v0.5',blocker=None,display=None))
    found = completion_gate.find_record(NEXT_SESSION)
    assert found is not None and found[0] == path
    signed_before = path.read_bytes()
    completion_gate._reconcile_stop({'session_id':NEXT_SESSION,'hook_event_name':'Stop',
        'last_assistant_message':delivered_page},path,before,context.root,1,'INCOMPLETE: approved tasks remain',[])
    correction = capsys.readouterr()
    assert 'Waiting for you' in correction.out and 'Required actions' in correction.out
    assert 'Prerequisites:' in correction.out and 'Acknowledgment:' in correction.out
    assert path.read_bytes() == signed_before
    assert run_plan.continuation_path(path).read_bytes() == original_frame
    observed = run_plan.native_owner_observation(SimpleNamespace(minor=True,label='v0.5',
        repo_root=context.root,observer_session=NEXT_SESSION),path,before,frame)
    assert observed['objective'] == objective
    assert not any(work['authorized'] for work in observed['work'])
    log.now = time.time()-1
    log.user('Approve')
    result = minor.run('record','resume','--minor','v0.5','--session',NEXT_SESSION)
    assert result.returncode == 0, result.stdout+result.stderr
    context, after = ck.resolve_minor_controller(path,NEXT_SESSION,minor_protocol=1,execution_protocol=1)
    assert after['session_id'] == NEXT_SESSION and after['nonce'] == before['nonce']
    assert after['approvals'] == before['approvals']
    scope.observer_session = NEXT_SESSION
    migrated = run_plan.read_continuation(scope,path,after)
    assert migrated['observation']['objective'] == objective
    assert migrated['binding']['session_id'] == NEXT_SESSION
    rounds = binding.issued_requests(minor.runs,path.stem,ck._secret(create=False),
                                     after,observer_session=NEXT_SESSION)
    assert len(ck._minor_module().continuation_owner_results(ck,after,rounds)) == 1
    final = run_plan.continuation_for_run(scope,path,after,1,'INCOMPLETE: approved tasks remain',claim_refresh=True)
    assert final['state'] == 'working'
    if historical:
        assert len(final['requests'])==1 and final['requests'][0]['native_reconciliation']['outcome']=='owner-session-changed'
        sections='\n'.join(run_plan.reporting_module('status_report').required_parts(final))
        assert 'Controller reconciliation' in sections and old_line not in sections
    else:
        assert final['requests']==[]
    saved = json.loads(run_plan.continuation_path(path).read_text(encoding='utf-8'))
    assert saved['observation']['objective'] == objective
    assert saved['binding']['session_id'] == NEXT_SESSION
    assert saved['previous_capture_sources'] == migrated['previous_capture_sources']


def test_native_sibling_report_preserves_controller_root_and_rejects_foreign_repo(minor,capsys):
    import pytest
    from datetime import datetime,timezone
    from .test_completion_minor_record import _git
    assert minor.create().returncode == 0
    rendered=minor.render(SESSION,'--action','add-class','--class','archive-member','--page')
    assert rendered.returncode == 0,rendered.stdout+rendered.stderr
    path=minor.record_path()
    context,record=ck.resolve_minor_controller(path,SESSION,minor_protocol=1,execution_protocol=1)
    completion_gate._reconcile_stop({'session_id':SESSION,'hook_event_name':'Stop','last_assistant_message':rendered.stdout},
        path,record,context.root,1,'INCOMPLETE: fixture native tasks remain',[])
    capsys.readouterr()
    sidecar=run_plan.continuation_path(path)
    original=sidecar.read_bytes()
    sibling=minor.tmp/'private-report-sibling'
    _git(minor.work,'worktree','add','-q','--detach',str(sibling),'HEAD')
    reporter=run_plan.reporting_module('status_snapshot')
    notes=reporter.continuation_overlay(sidecar,sibling,'v0.5',path)
    snapshot=reporter.build(sibling,'v0.5',notes,'develop',datetime.now(timezone.utc),record_path=path,
        observer_session=SESSION)
    for mode in ('compact','full'):
        text=run_plan.reporting_module('status_report').render(snapshot,mode)
        assert text.startswith('Waiting for you') and 'Required actions' in text
    assert sidecar.read_bytes()==original
    assert json.loads(original)['binding']['repo_root']==str(minor.work.resolve())
    foreign=minor.tmp/'private-unrelated-repository'
    foreign.mkdir()
    _git(foreign,'init','-q')
    with pytest.raises(ValueError,match='Git common directory'):
        reporter.continuation_overlay(sidecar,foreign,'v0.5',path)
    assert sidecar.read_bytes()==original
