"""Single-plan and pre-create native owner observation with private Git fixtures."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from .test_approval_binding import _fixture
from .test_check_plan_completion import PLAN_REL, SESSION, _isolated_git_config  # noqa: F401
import approval_binding
import check_plan_completion as ck
import run_plan
import completion_gate

NO_WINDOW = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}


def _hook(fx, session, prompt, **host_fields):
    result = subprocess.run([sys.executable, '-B', str(run_plan.SCRIPT_DIR / 'completion_gate.py'), 'capture'],
        input=json.dumps({'session_id': session, 'hook_event_name': 'UserPromptSubmit', 'prompt': prompt, **host_fields}),
        env=fx.env, cwd=fx.work, capture_output=True, text=True, timeout=30, **NO_WINDOW)
    assert result.returncode == 0, result.stdout + result.stderr


def prepare(tmp_path, monkeypatch):
    fx = _fixture(tmp_path)
    monkeypatch.setenv('NEXUS_HUB_RUNS_DIR', str(fx.runs))
    for name in ('PATH', 'GH_STUB_STATE', 'GH_STUB_PYTHON'):
        monkeypatch.setenv(name, fx.env[name])
    spec = fx.approvals()
    fx.capture(SESSION, '/implement ' + PLAN_REL, at=0)
    rendered = fx.run('record', 'render', PLAN_REL, '--session', SESSION,
        '--approvals', str(spec), '--question', **NO_WINDOW)
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    return fx, spec, SimpleNamespace(stdout=json.loads(rendered.stdout)['review_page'])


def test_precreate_descriptor_and_delivered_owner_request(tmp_path, monkeypatch):
    fx, _spec, rendered = prepare(tmp_path, monkeypatch)
    ctx, path, metadata = ck.precreate_owner_context(SESSION)
    assert path == ctx.record_path() and not path.exists()
    assert metadata['nonce'] is None
    assert approval_binding.observe_issued_request(path.parent, path.stem, ck._secret(False), metadata, rendered.stdout)
    scope = SimpleNamespace(minor=False, label=str(ctx.plan), repo_root=ctx.root)
    facts = run_plan.precreate_owner_observation(scope, path, metadata, None)
    assert facts['requests'] and facts['remaining_tasks'] == 2
    assert facts['work'] == [] and facts['objective_complete'] is False
    assert not path.exists()


def test_precreate_foreign_session_and_changed_plan_refuse(tmp_path, monkeypatch):
    fx, _spec, _rendered = prepare(tmp_path, monkeypatch)
    assert ck.precreate_owner_context('foreign-session') is None
    plan = fx.work / PLAN_REL
    plan.write_text(plan.read_text(encoding='utf-8') + '\nChanged scope.\n', encoding='utf-8')
    with pytest.raises(ck.Malformed):
        ck.precreate_owner_context(SESSION)


def test_schema1_native_create_result_requires_real_persisted_effect(tmp_path, monkeypatch):
    fx, spec, rendered = prepare(tmp_path, monkeypatch)
    ctx, path, metadata = ck.precreate_owner_context(SESSION)
    secret = ck._secret(False)
    assert approval_binding.observe_issued_request(path.parent, path.stem, secret, metadata, rendered.stdout)
    completion_gate._precreate_stop({'session_id': SESSION, 'last_assistant_message': rendered.stdout}, SESSION)
    original = json.loads(run_plan.continuation_path(path).read_text(encoding='utf-8'))
    pending = approval_binding._read_pending(approval_binding.pending_path(path.parent, path.stem), secret)
    assert ck.plan_owner_results(ctx, {}, [pending]) == []
    _hook(fx, SESSION, pending['paste_lines'][0])
    created = fx.run('record', 'create', PLAN_REL, '--session', SESSION, '--approvals', str(spec), **NO_WINDOW)
    assert created.returncode == 0, created.stdout + created.stderr
    verified_ctx, record = ck.resolve_plan_controller(path, SESSION)
    issued = ck.plan_issued_requests(verified_ctx, record)
    assert len(ck.plan_owner_results(verified_ctx, record, issued)) == 1
    assert ck.plan_owner_results(verified_ctx, record, [dict(issued[0], session='foreign-session')]) == []
    scope = SimpleNamespace(minor=False, label=str(ctx.plan), repo_root=ctx.root)
    migrated = run_plan.read_continuation(scope, path, record)
    assert migrated['binding']['run_nonce'] == record['nonce']
    assert migrated['observation']['objective'] == original['observation']['objective']
    facts = run_plan.native_owner_observation(scope, path, record, migrated)
    assert facts['resolutions']
    changed = dict(record, plan_sha256='0' * 64)
    path.write_text(json.dumps(changed), encoding='utf-8')
    with pytest.raises(ck.Malformed):
        ck.resolve_plan_controller(path, SESSION)


def test_default_stop_before_create_exposes_manual_decision(tmp_path, monkeypatch, capsys):
    fx, _spec, rendered = prepare(tmp_path, monkeypatch)
    monkeypatch.setattr(completion_gate, '_read_payload', lambda: {
        'session_id': SESSION, 'hook_event_name': 'Stop', 'last_assistant_message': rendered.stdout})
    assert completion_gate.cmd_stop(reconcile_only=True) in (0, 2)
    output = capsys.readouterr().out
    assert 'Waiting for you' in output and 'Required actions' in output
    assert 'Approve' in output and 'Decline' in output and 'Prerequisites:' in output
    ctx, path, metadata = ck.precreate_owner_context(SESSION)
    assert not path.exists()
    saved = json.loads(run_plan.continuation_path(path).read_text(encoding='utf-8'))
    reporter = run_plan.reporting_module('status_report')
    state = saved['disposition']
    assert reporter.state_heading(state).startswith('Waiting for you')
    assert state['objective_complete'] is False and state['work'] == []


@pytest.mark.parametrize('field', ['nonce', 'descriptor'])
def test_precreate_invalid_identity_stays_unresolved(tmp_path, monkeypatch, field):
    fx, _spec, _rendered = prepare(tmp_path, monkeypatch)
    secret = ck._secret(False)
    marker_path = approval_binding.question_path(fx.runs, SESSION)
    marker = approval_binding._question_marker(fx.runs, secret, SESSION)
    if field == 'nonce':
        marker['nonce'] = '0' * 32
        marker['mac'] = approval_binding._seal(secret, marker)
        approval_binding._write_private(marker_path, marker)
    else:
        path = approval_binding.pending_path(fx.runs, marker['key'])
        pending = approval_binding._read_pending(path, secret)
        pending['page']['native_context']['repo_root'] = str(tmp_path)
        pending['mac'] = approval_binding._seal(secret, pending)
        approval_binding._write_private(path, pending)
    with pytest.raises(ck.Malformed):
        ck.precreate_owner_context(SESSION)


def create_owned(tmp_path, monkeypatch):
    fx, spec, rendered = prepare(tmp_path, monkeypatch)
    ctx, path, metadata = ck.precreate_owner_context(SESSION)
    assert approval_binding.observe_issued_request(path.parent, path.stem, ck._secret(False), metadata, rendered.stdout)
    pending = approval_binding._read_pending(approval_binding.pending_path(fx.runs, path.stem), ck._secret(False))
    _hook(fx, SESSION, pending['paste_lines'][0], permission_mode='bypassPermissions')
    result = fx.run('record', 'create', PLAN_REL, '--session', SESSION, '--approvals', str(spec), **NO_WINDOW)
    assert result.returncode == 0, result.stdout + result.stderr
    return fx, ctx, path


def test_schema1_pause_then_resume_preserves_historical_result(tmp_path, monkeypatch, capsys):
    fx, ctx, path = create_owned(tmp_path, monkeypatch)
    paused_page = fx.run('record', 'render', PLAN_REL, '--session', SESSION, '--action', 'pause', '--page', **NO_WINDOW)
    assert paused_page.returncode == 0, paused_page.stdout + paused_page.stderr
    _ctx, record = ck.resolve_plan_controller(path, SESSION)
    assert approval_binding.observe_issued_request(fx.runs, path.stem, ck._secret(False), record, paused_page.stdout)
    pending = approval_binding._read_pending(approval_binding.pending_path(fx.runs, path.stem), ck._secret(False))
    _hook(fx, SESSION, pending['paste_lines'][0])
    paused = fx.run('record', 'pause', PLAN_REL, '--session', SESSION, **NO_WINDOW)
    assert paused.returncode == 0, paused.stdout + paused.stderr
    _ctx, record = ck.resolve_plan_controller(path, SESSION)
    issued = ck.plan_issued_requests(ctx, record)
    assert any(row['request_id'].endswith(pending['nonce']) for row in ck.plan_owner_results(ctx, record, issued))
    scope = SimpleNamespace(minor=False, label=str(ctx.plan), repo_root=ctx.root)
    facts = run_plan.native_owner_observation(scope, path, record, None)
    assert facts['paused'] is True
    completion_gate._reconcile_stop({'session_id': SESSION, 'last_assistant_message': paused_page.stdout},
        path, record, ctx.root, 4, 'PAUSED', [])
    capsys.readouterr()
    original_frame = json.loads(run_plan.continuation_path(path).read_text(encoding='utf-8'))
    original_frame['observation']['work'] = [{'id': 'native-approved-next-task',
        'title': 'Continue the existing approved plan integration', 'authorized': True, 'feasible': True,
        'evidence': 'The private native create approved this exact repository integration scope.',
        'authorization': {'class': 'push-merge', 'request': {'repo': 'acme/demo'}}}]
    original_frame['disposition']['work'] = original_frame['observation']['work']
    original_frame['observation']['completion'] = {'verified': True, 'evidence': 'Stale descriptive fixture observation.'}
    run_plan.save_continuation(path, original_frame)
    _hook(fx, 'second-owner', 'Resume the paused approved plan in this session.', permission_mode='bypassPermissions')
    resume_page = fx.run('record', 'render', PLAN_REL, '--session', 'second-owner', '--action', 'resume', '--question', **NO_WINDOW)
    assert resume_page.returncode == 0, resume_page.stdout + resume_page.stderr
    resume = approval_binding._read_pending(approval_binding.pending_path(fx.runs, path.stem), ck._secret(False))
    before = path.read_bytes()
    observer_scope = SimpleNamespace(minor=False, label=str(ctx.plan), repo_root=ctx.root, observer_session='second-owner')
    assert approval_binding.observe_issued_request(fx.runs, path.stem, ck._secret(False), record,
        json.loads(resume_page.stdout)['review_page'], observer_session='second-owner')
    projected = run_plan.native_owner_observation(observer_scope, path, record, original_frame)
    assert projected['work'][0]['id'] == 'native-approved-next-task'
    assert projected['work'][0]['authorized'] is False and projected['completion']['verified'] is False
    observer_state = run_plan.continuation_module().reconcile(projected, original_frame['disposition'])
    assert observer_state['work'][0]['authorized'] is False
    sidecar_before = run_plan.continuation_path(path).read_bytes()
    completion_gate._precreate_stop({'session_id': 'second-owner',
        'last_assistant_message': json.loads(resume_page.stdout)['review_page']}, 'second-owner')
    capsys.readouterr()
    assert path.read_bytes() == before
    assert ck.resolve_plan_controller(path)[1]['session_id'] == SESSION
    assert run_plan.continuation_path(path).read_bytes() == sidecar_before
    assert projected['objective'] == original_frame['observation']['objective']
    assert any(row['native_round']['nonce'] == resume['nonce'] for row in observer_state['requests'])
    _hook(fx, 'second-owner', resume['paste_lines'][0], permission_mode='bypassPermissions')
    resumed = fx.run('record', 'resume', PLAN_REL, '--session', 'second-owner', **NO_WINDOW)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    _ctx, record = ck.resolve_plan_controller(path, 'second-owner')
    assert record['continuations'][-1]['from_session'] == SESSION
    assert approval_binding.completed_resume_pointer(fx.runs, path.stem, ck._secret(False))['round_nonce'] == resume['nonce']
    issued = ck.plan_issued_requests(ctx, record)
    results = ck.plan_owner_results(ctx, record, issued)
    assert any(row['request_id'].endswith(pending['nonce']) for row in results)
    facts = run_plan.native_owner_observation(scope, path, record, None)
    assert facts['paused'] is False
    scope.observer_session = 'second-owner'
    migrated = run_plan.read_continuation(scope, path, record)
    assert migrated['binding']['session_id'] == 'second-owner'
    assert migrated['observation']['objective'] == original_frame['observation']['objective']
    before_probe = path.read_bytes()
    probe = ck.authorization_probe(SimpleNamespace(minor=None, repo=str(ctx.root), plan=str(ctx.plan),
        session='second-owner', member=None, approval_class='push-merge', request=json.dumps({'repo': 'acme/demo'})))
    assert not isinstance(probe, int), capsys.readouterr()
    assert path.read_bytes() == before_probe
    first = run_plan.continuation_for_run(scope, path, record, 1, 'INCOMPLETE: actual remaining plan tasks', claim_refresh=True)
    assert first['state'] == 'working' and first['directive'] == 'continue'
    assert first['work'][0]['authorized'] is True


def test_precreate_source_fact_reply_cannot_create_authority(tmp_path, monkeypatch):
    fx, spec, _rendered = prepare(tmp_path, monkeypatch)
    ctx, path, metadata = ck.precreate_owner_context(SESSION)
    payload = {'session_id': SESSION, 'hook_event_name': 'PreToolUse', 'tool_name': 'request_user_input',
        'tool_call_id': 'source-fact', 'tool_input': {'questions': [{'header': 'Color', 'id': 'color',
        'question': 'Which color describes the source?', 'options': [{'label': 'Blue', 'description': 'Blue source.'},
            {'label': 'Green', 'description': 'Green source.'}]}]}}
    assert completion_gate._observe_question_event(payload) == 0
    _hook(fx, SESSION, 'Blue')
    result = fx.run('record', 'create', PLAN_REL, '--session', SESSION, '--approvals', str(spec), **NO_WINDOW)
    assert result.returncode != 0 and not path.exists()


def test_precreate_measured_snapshot_and_full_compact_report(tmp_path, monkeypatch, capsys):
    fx, _spec, rendered = prepare(tmp_path, monkeypatch)
    completion_gate._precreate_stop({'session_id': SESSION, 'last_assistant_message': rendered.stdout}, SESSION)
    capsys.readouterr()
    snapshot_tool = run_plan.SCRIPT_DIR.parent / 'catalog/skills/workflow/implement-phase/scripts/status_snapshot.py'
    result = subprocess.run([sys.executable, '-B', str(snapshot_tool), '--repo', str(fx.work),
        '--scope', 'v0.2.0', '--session', SESSION, '--runs-dir', str(fx.runs)], env=fx.env,
        cwd=fx.work, capture_output=True, text=True, timeout=60, **NO_WINDOW)
    assert result.returncode == 0, result.stdout + result.stderr
    snapshot = json.loads(result.stdout)
    reporter = run_plan.reporting_module('status_report')
    for mode in ('full', 'compact'):
        report = reporter.render(snapshot, mode)
        assert report.startswith('Waiting for you') and 'Required actions' in report
        assert 'Approve' in report and 'Decline' in report


def test_failed_create_write_retains_consumed_owner_obligation(tmp_path, monkeypatch, capsys):
    fx, spec, rendered = prepare(tmp_path, monkeypatch)
    completion_gate._precreate_stop({'session_id': SESSION, 'last_assistant_message': rendered.stdout}, SESSION)
    capsys.readouterr()
    ctx, path, metadata = ck.precreate_owner_context(SESSION)
    pending = approval_binding._read_pending(approval_binding.pending_path(fx.runs, path.stem), ck._secret(False))
    _hook(fx, SESSION, pending['paste_lines'][0])
    args = ck.build_parser().parse_args(['record', 'create', str(ctx.plan), '--session', SESSION, '--approvals', str(spec)])
    def fail_write(*_args):
        raise OSError('private injected atomic record write failure')
    monkeypatch.setattr(ck, '_write_record', fail_write)
    with pytest.raises(OSError, match='private injected'):
        ck.cmd_record_create(args)
    assert not path.exists()
    assert ck.precreate_owner_context(SESSION) is not None
    facts = run_plan.precreate_owner_observation(SimpleNamespace(minor=False, label=str(ctx.plan), repo_root=ctx.root),
        path, metadata, None)
    assert facts['owner_recovery'] and not facts['resolutions']
    assert 'do not submit the approval again' in facts['owner_recovery'][0]['reason'].lower()
