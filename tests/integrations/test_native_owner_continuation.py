"""Private native-format owner controls, without live sessions or provider calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import approval_binding as binding
import approval_page
import check_plan_completion as checker
import completion_minor
import run_plan


@pytest.fixture
def owner(tmp_path, monkeypatch):
    runs = tmp_path / 'runs'
    runs.mkdir()
    secret = b'private fixture key only'.ljust(32, b'!')
    (runs / '.secret').write_bytes(secret)
    monkeypatch.setenv('NEXUS_HUB_RUNS_DIR', str(runs))
    monkeypatch.delenv('NEXUS_RUNNER_LAUNCH', raising=False)
    record = {'schema': 2, 'scope': 'minor', 'minor': 'v4.15', 'nonce': 'fixture-record',
              'session_id': 'fixture-owner', 'approvals': {'classes': []}}
    page = completion_minor.action_page('v4.15', 'add-class', record['nonce'])
    page['class'] = 'archive-member'
    pending = binding.render(runs, 'fixture', secret, action='add-class', scope='v4.15',
                             page=page, session=record['session_id'])
    display = approval_page.render_page(approval_page.render_data(pending, scope='v4.15', blocker=None, display=None))
    record['approvals_hmac'] = checker._sign(record, secret)
    (runs / 'fixture.json').write_text(json.dumps(record), encoding='utf-8')
    # Unit controls isolate the operational repository reader; the separate
    # native CLI flow exercises the actual full reader and persisted writer.
    monkeypatch.setattr(checker, 'resolve_minor_controller', lambda path, session, **kw:
        (SimpleNamespace(root=tmp_path), json.loads(path.read_text(encoding='utf-8'))))
    return SimpleNamespace(runs=runs, secret=secret, record=record, page=page, pending=pending,
                           display=display, path=runs / 'fixture.json')


def test_render_is_not_issuance_and_partial_or_foreign_stop_does_not_register(owner):
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record) == []
    assert not binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record,
                                            owner.pending['paste_lines'][0])
    foreign = dict(owner.record, session_id='other-session')
    assert not binding.observe_issued_request(owner.runs, 'fixture', owner.secret, foreign, owner.display)
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record) == []


def test_delivered_native_page_is_recovered_without_model_observations(owner):
    assert binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record, owner.display)
    issued = binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record)
    assert len(issued) == 1 and issued[0]['nonce'] == owner.pending['nonce']
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    frame = run_plan.native_owner_observation(scope, owner.path, owner.record, None,
                                             remaining_tasks=7)
    assert frame['remaining_tasks'] == 7
    assert frame['requests'][0]['kind'] == 'decision' and frame['requests'][0]['manual_capture'] is True
    assert frame['requests'][0]['steps'][-1].endswith(owner.pending['paste_lines'][0])
    assert frame['jobs'] == []


def test_consumption_alone_retains_request_and_signed_exact_owner_result_retires_it(owner):
    binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record, owner.display)
    session = owner.record['session_id']
    prompt_path = owner.runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    prompt_path.parent.mkdir()
    events = [{'session': session, 'prompt': binding.digest('Begin private fixture'),
               'event_id': 'before', 'at': owner.pending['rendered_at'] - 1},
              {'session': session, 'prompt': owner.pending['paste_digests'][0],
               'event_id': 'reply', 'at': owner.pending['rendered_at'] + 0.01}]
    prompt_path.write_text(''.join(json.dumps(event) + '\n' for event in events), encoding='utf-8')
    consumed, _ = binding.consume(owner.runs, 'fixture', owner.secret, action='add-class',
                                  live_page=owner.page, session=session)
    record = owner.record
    record['approvals_hmac'] = checker._sign(record, owner.secret)
    issued = binding.issued_requests(owner.runs, 'fixture', owner.secret, record)
    assert completion_minor.continuation_owner_results(checker, record, issued) == []
    record['approvals']['classes'].append({'class': 'archive-member', 'text': binding.pasted(consumed),
        'added': {'at': '2026-11-25T00:00:00+00:00',
                  'page_sha256': hashlib.sha256(binding.canonical(owner.page)).hexdigest(),
                  'authorization_context': consumed['capture']}})
    record['approvals_hmac'] = checker._sign(record, owner.secret)
    resolutions = completion_minor.continuation_owner_results(checker, record, issued)
    assert len(resolutions) == 1 and resolutions[0]['verified'] is True
    changed = dict(record, nonce='foreign-record')
    changed['approvals_hmac'] = checker._sign(changed, owner.secret)
    assert completion_minor.continuation_owner_results(checker, changed, issued) == []
    record['approvals']['classes'][0]['added']['page_sha256'] = '0' * 64
    assert completion_minor.continuation_owner_results(checker, record, issued) == []


def test_default_stop_discovers_and_corrects_hidden_native_action_then_verified_result_resumes(owner, monkeypatch, capsys):
    import completion_gate
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    projection = run_plan.native_owner_observation
    # Task measurement is isolated here; this control exercises the actual owner,
    # controller, Stop and report functions rather than a model observation file.
    monkeypatch.setattr(run_plan, 'native_owner_observation', lambda s, p, r, prior, **kw:
        projection(s, p, r, prior, remaining_tasks=kw.get('remaining_tasks', 7)))
    payload = {'session_id': 'fixture-owner', 'last_assistant_message': owner.display,
               'hook_event_name': 'Stop'}
    assert not run_plan.continuation_path(owner.path).exists()
    completion_gate._reconcile_stop(payload, owner.path, owner.record, scope.repo_root,
                                   3, 'BLOCKED: captured-decision-required', [])
    correction = capsys.readouterr()
    assert 'Waiting for you' in correction.out and 'Required actions' in correction.out
    assert 'Prerequisites:' in correction.out and 'Acknowledgment:' in correction.out
    frame = json.loads(run_plan.continuation_path(owner.path).read_text())
    assert frame['disposition']['state'] == 'waiting_decision'
    assert len(frame['disposition']['requests']) == 1
    reporter = run_plan.reporting_module('status_report')
    state = frame['disposition']
    honest_parts = [reporter.state_heading(state), *reporter.required_parts(state)]
    for decision in reporter.pending_decisions(state):
        honest_parts.extend(reporter.decision_parts(decision, True))
    honest = '\n\n'.join(honest_parts)
    payload['last_assistant_message'] = honest
    completion_gate._reconcile_stop(payload, owner.path, owner.record, scope.repo_root,
                                   3, 'BLOCKED: captured-decision-required', [])
    assert capsys.readouterr().out == ''
    # A report with all the words but its action buried in Goals must be corrected.
    payload['last_assistant_message'] = reporter.state_heading(state) + '\n### Goals\n' + honest
    completion_gate._reconcile_stop(payload, owner.path, owner.record, scope.repo_root,
                                   3, 'BLOCKED: captured-decision-required', [])
    assert 'Correct the waiting report' in capsys.readouterr().out
    assert len(binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record)) == 1


def test_observation_never_runs_mutating_authorize_and_explicit_reconciliation_can(owner, monkeypatch):
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    calls = []
    monkeypatch.setattr(run_plan, '_checker_run', lambda args: (calls.append(args) or (0, 'AUTHORIZED {}')))
    item = {'authorization': {'class': 'release', 'request': {'release_version': 'v4.15.6'}}}
    assert run_plan._authorization(scope, owner.record, item, readonly=True) is False
    assert calls == []
    assert run_plan._authorization(scope, owner.record, item) is True
    assert calls[0][:2] == ['record', 'authorize']


def _captured_consumption(owner, key='fixture', pending=None):
    pending = pending or owner.pending
    session = owner.record['session_id']
    prompt_path = owner.runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    prompt_path.parent.mkdir(exist_ok=True)
    with prompt_path.open('a', encoding='utf-8') as stream:
        for event in [{'session': session, 'prompt': binding.digest('Begin private fixture'),
                       'event_id': 'before-' + key, 'at': pending['rendered_at'] - 1},
                      {'session': session, 'prompt': pending['paste_digests'][0],
                       'event_id': 'reply-' + pending['nonce'], 'at': pending['rendered_at'] + 0.01}]:
            stream.write(json.dumps(event) + '\n')
    return binding.consume(owner.runs, key, owner.secret, action=pending['action'],
                           live_page=pending['page'], session=session)[0]


def test_prepared_recovery_grants_nothing_before_claim_and_survives_claim_failure(owner, monkeypatch):
    binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record, owner.display)
    original = binding._claim_event
    def before_claim(*args):
        assert binding.used_path(owner.runs, 'fixture').exists()
        assert binding.pending_path(owner.runs, 'fixture').exists()
        assert binding.consumed_issued_request(owner.runs, 'fixture', owner.secret, owner.pending) is None
        raise OSError('private fixture claim failed')
    monkeypatch.setattr(binding, '_claim_event', before_claim)
    with pytest.raises(OSError, match='claim failed'):
        _captured_consumption(owner)
    assert binding.consumed_issued_request(owner.runs, 'fixture', owner.secret, owner.pending) is None
    monkeypatch.setattr(binding, '_claim_event', original)
    # Finish exactly the still-unclaimed fixture event. Prepared data alone did
    # not authorize recovery or remove the pending challenge.
    consumed, _ = binding.consume(owner.runs, 'fixture', owner.secret, action='add-class',
                                  live_page=owner.page, session=owner.record['session_id'])
    assert binding.consumed_issued_request(owner.runs, 'fixture', owner.secret, owner.pending) == consumed['capture']
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    projected = run_plan.native_owner_observation(scope, owner.path, owner.record, None, remaining_tasks=7)
    assert projected['owner_recovery'] and projected['resolutions'] == []
    reporter = run_plan.reporting_module('status_snapshot')
    with pytest.raises(ValueError, match='do not submit the approval again'):
        reporter.native_owner_projection(owner.path, scope.repo_root, scope.label,
            {'objective': 'Retain the complete approved fixture objective', 'remaining_tasks': 7}, None, 7)


def test_shared_session_marker_serializes_render_and_stop_without_lost_issuance(owner, monkeypatch):
    from contextlib import contextmanager
    from concurrent.futures import ThreadPoolExecutor
    import threading
    original_lock = checker._minor_os_lock
    original_read = binding._question_marker
    first_read = threading.Event()
    release = threading.Event()
    second_attempt = threading.Event()
    paths = []
    @contextmanager
    def lock(path, budget):
        paths.append(path)
        if threading.current_thread().name.startswith('render'):
            second_attempt.set()
        with original_lock(path, budget):
            yield
    def read(runs, secret, session):
        value = original_read(runs, secret, session)
        if threading.current_thread().name.startswith('stop'):
            first_read.set()
            assert release.wait(2)
        return value
    monkeypatch.setattr(checker, '_minor_os_lock', lock)
    monkeypatch.setattr(binding, '_question_marker', read)
    pending = dict(owner.pending, allow_short_reply=True)
    pending['mac'] = binding._seal(owner.secret, pending)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix='stop') as stop_pool:
        first = stop_pool.submit(binding.observe_issued_request, owner.runs, 'fixture', owner.secret, owner.record, owner.display)
        assert first_read.wait(2)
        with ThreadPoolExecutor(max_workers=1, thread_name_prefix='render') as render_pool:
            second = render_pool.submit(binding.activate_question, owner.runs, 'next-key', owner.secret, pending)
            assert second_attempt.wait(2)
            release.set()
            assert first.result(timeout=4) is True
            second.result(timeout=4)
    marker = original_read(owner.runs, owner.secret, owner.record['session_id'])
    assert marker['key'] == 'next-key'
    assert len(marker['issued_rounds']) == 1
    assert marker['issued_rounds'][0]['nonce'] == owner.pending['nonce']
    assert len(paths) == 2 and paths[0] == paths[1]


def test_more_than_64_fulfilled_rounds_do_not_erase_one_unresolved_request(owner):
    binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record, owner.display)
    for number in range(65):
        key = 'fulfilled-' + str(number)
        record = dict(owner.record, nonce=key, approvals={'classes': []})
        page = dict(owner.page, record_nonce=key)
        pending = binding.render(owner.runs, key, owner.secret, action='add-class', scope='v4.15',
                                 page=page, session=record['session_id'])
        record['approvals_hmac'] = checker._sign(record, owner.secret)
        record_path = owner.runs / (key + '.json')
        record_path.write_text(json.dumps(record), encoding='utf-8')
        display = approval_page.render_page(approval_page.render_data(pending, scope='v4.15', blocker=None, display=None))
        binding.observe_issued_request(owner.runs, key, owner.secret, record, display)
        consumed = _captured_consumption(owner, key, pending)
        record['approvals']['classes'].append({'class': 'archive-member', 'text': binding.pasted(consumed),
            'added': {'page_sha256': hashlib.sha256(binding.canonical(page)).hexdigest(),
                      'authorization_context': consumed['capture']}})
        record['approvals_hmac'] = checker._sign(record, owner.secret)
        record_path.write_text(json.dumps(record), encoding='utf-8')
    marker = binding._question_marker(owner.runs, owner.secret, owner.record['session_id'])
    assert len(marker['issued_rounds']) <= 2
    assert len(binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record)) == 1


@pytest.mark.parametrize('row', [
    'v4.15.6:approval.remote cannot-verify',
    'v4.15.6:plan.identity cannot-verify',
    'v4.15.9:integration.checks cannot-verify',
    'v4.15.6:integration.checks cannot-verify extra',
    'v4.15.6:release.main cannot-verify\nchecker.observation cannot-verify',
])
def test_external_unknown_exception_rejects_authority_foreign_member_and_malformed_rows(owner, row):
    owner.record['members'] = [{'version': 'v4.15.6', 'plan_path': 'docs/fixture.md'}]
    owner.record['approvals_hmac'] = checker._sign(owner.record, owner.secret)
    owner.path.write_text(json.dumps(owner.record), encoding='utf-8')
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    assert run_plan._external_predicate_unknowns(scope, owner.path, owner.record, row) is False


def test_only_exact_approved_external_unknowns_can_coexist_with_available_work(owner):
    owner.record['members'] = [{'version': 'v4.15.6', 'plan_path': 'docs/fixture.md'}]
    owner.record['approvals_hmac'] = checker._sign(owner.record, owner.secret)
    owner.path.write_text(json.dumps(owner.record), encoding='utf-8')
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    output = 'INCOMPLETE: task.T001\nv4.15.6:integration.checks cannot-verify\nv4.15.6:release.main cannot-verify\n'
    assert run_plan._external_predicate_unknowns(scope, owner.path, owner.record, output) is True
    scope.minor = False
    assert run_plan._external_predicate_unknowns(scope, owner.path, owner.record, output) is False


def test_native_result_refresh_is_claimed_once_without_any_prior_sidecar(owner, monkeypatch):
    binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record, owner.display)
    consumed = _captured_consumption(owner)
    owner.record['approvals']['classes'].append({'class': 'archive-member', 'text': binding.pasted(consumed),
        'added': {'page_sha256': hashlib.sha256(binding.canonical(owner.page)).hexdigest(),
                  'authorization_context': consumed['capture']}})
    owner.record['approvals_hmac'] = checker._sign(owner.record, owner.secret)
    owner.path.write_text(json.dumps(owner.record), encoding='utf-8')
    projection = run_plan.native_owner_observation
    monkeypatch.setattr(run_plan, 'native_owner_observation', lambda s, p, r, prior, **kw:
        projection(s, p, r, prior, remaining_tasks=kw.get('remaining_tasks', 7)))
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    assert not run_plan.continuation_path(owner.path).exists()
    first = run_plan.continuation_for_run(scope, owner.path, owner.record, 1, 'INCOMPLETE: task.T001', claim_refresh=True)
    second = run_plan.continuation_for_run(scope, owner.path, owner.record, 1, 'INCOMPLETE: task.T001', claim_refresh=True)
    assert first['directive'] == 'continue'
    assert second['directive'] == 'wait'
    assert not run_plan.continuation_path(owner.path).exists()  # No invented feasible work frame.


def _native_question(owner):
    data = approval_page.render_data(owner.pending, scope='v4.15', blocker=None, display=None)
    question = approval_page.question_data(data)
    return {'title': question['review_page'] + '\n\n' + question['question'],
            'options': ['Approve', 'Decline']}


def _question_event(owner, event='PreToolUse', **changes):
    value = {'hook_event_name': event, 'session_id': owner.record['session_id'],
        'tool_name': 'functions.request_user_input_async', 'tool_use_id': 'fixture-question-call',
        'tool_input': {'questions': [_native_question(owner)]}}
    value.update(changes)
    return value


def _question_envelope(owner, answer='Approve', call='fixture-question-call'):
    return '<send_user_message_question_reply>\n' + json.dumps([{
        'questionItemId': json.dumps(['request_user_input_async', call, 0]),
        'question': _native_question(owner)['title'], 'answer': answer}]) + '\n</send_user_message_question_reply>'


def _real_prompt_capture(owner, prompt):
    import os
    import subprocess
    environment = dict(os.environ, HOME=str(owner.runs.parent), USERPROFILE=str(owner.runs.parent),
                       NEXUS_HUB_RUNS_DIR=str(owner.runs))
    environment.pop('NEXUS_RUNNER_LAUNCH', None)
    flags = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {}
    result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/completion_gate.py'), 'capture'],
        input=json.dumps({'session_id': owner.record['session_id'], 'prompt': prompt}),
        cwd=owner.runs.parent, env=environment, capture_output=True, text=True, timeout=30, **flags)
    assert result.returncode == 0, result.stderr
    return binding.capture_events(owner.runs, owner.record['session_id'])[-1]


def test_async_attempt_alone_never_establishes_delivery_or_approval(owner):
    assert binding.observe_question_attempt(owner.runs, 'fixture', owner.secret, owner.record,
                                            _question_event(owner)) is True
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record) == []
    assert not binding.used_path(owner.runs, 'fixture').exists()


def test_genuine_bound_async_owner_answer_becomes_manual_capture_not_another_decision(owner):
    before = owner.path.read_bytes()
    binding.observe_question_attempt(owner.runs, 'fixture', owner.secret, owner.record, _question_event(owner))
    prompt = _question_envelope(owner)
    event = _real_prompt_capture(owner, prompt)
    assert event['prompt'] == binding.digest(prompt)
    assert event['prompt'] != binding.digest('Approve')
    issued = binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record)
    assert len(issued) == 1 and issued[0]['decision_answer']['choice'] == 'Approve'
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    facts = run_plan.native_owner_observation(scope, owner.path, owner.record, None, remaining_tasks=7)
    frame = run_plan.reconcile_observation(scope, owner.path, owner.record, facts, 3, 'BLOCKED: native-capture-required')
    assert frame['disposition']['state'] == 'waiting_owner_action'
    assert all(request['kind'] == 'action' for request in frame['disposition']['requests'])
    report = run_plan.reporting_module('status_report')
    required = '\n'.join(report.required_parts(frame['disposition']))
    assert 'Prerequisites:' in required and '1. ' in required and 'Expected result:' in required and 'Acknowledgment:' in required
    assert owner.pending['paste_lines'][0] in required
    assert owner.path.read_bytes() == before
    assert not binding.used_path(owner.runs, 'fixture').exists()
    assert owner.record['approvals']['classes'] == []


def test_genuine_bound_decline_retires_question_without_authorizing_or_repeating_capture(owner):
    before = owner.path.read_bytes()
    binding.observe_question_attempt(owner.runs, 'fixture', owner.secret, owner.record, _question_event(owner))
    _real_prompt_capture(owner, _question_envelope(owner, answer='Decline'))
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent)
    facts = run_plan.native_owner_observation(scope, owner.path, owner.record, None, remaining_tasks=7)
    frame = run_plan.reconcile_observation(scope, owner.path, owner.record, facts, 3, 'BLOCKED: native-capture-required')
    state = frame['disposition']
    assert state['requests'] == [] and state['state'] == 'blocked_external'
    assert 'declined' in state['external_conditions'][0]['evidence'].lower()
    required = '\n'.join(run_plan.reporting_module('status_report').required_parts(state))
    assert 'Required actions' not in required and owner.pending['paste_lines'][0] not in required
    assert owner.path.read_bytes() == before and owner.record['approvals']['classes'] == []


@pytest.mark.parametrize('change', ['no-call-id', 'unreviewed', 'foreign-session', 'wrong-call', 'altered-question'])
def test_async_reply_missing_call_round_or_review_binding_never_becomes_consent(owner, change):
    event = _question_event(owner)
    if change == 'no-call-id':
        event.pop('tool_use_id')
    elif change == 'unreviewed':
        event['tool_input']['questions'][0]['title'] = 'Approve this operation?'
    elif change == 'foreign-session':
        event['session_id'] = 'foreign-owner'
    accepted = binding.observe_question_attempt(owner.runs, 'fixture', owner.secret, owner.record, event)
    prompt = _question_envelope(owner, call='wrong-call' if change == 'wrong-call' else 'fixture-question-call')
    if change == 'altered-question':
        prompt = prompt.replace('Nothing else changes.', 'Different review text.')
    _real_prompt_capture(owner, prompt)
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record) == []
    assert not binding.used_path(owner.runs, 'fixture').exists()
    if change in {'no-call-id', 'unreviewed', 'foreign-session'}:
        assert accepted is False


def test_answered_post_tool_question_proves_decision_without_forging_native_capture(owner):
    event = _question_event(owner, event='PostToolUse', tool_name='AskUserQuestion')
    question = event['tool_input']['questions'][0]
    event['tool_response'] = {'answers': {question['title']: 'Approve'}}
    assert binding.observe_question_result(owner.runs, 'fixture', owner.secret, owner.record, event) is True
    issued = binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record)
    assert len(issued) == 1 and issued[0]['decision_answer']['choice'] == 'Approve'
    assert binding.capture_events(owner.runs, owner.record['session_id']) == []
    assert not binding.used_path(owner.runs, 'fixture').exists()


def test_question_marker_preflights_actual_pretty_native_serialization(owner):
    binding.observe_question_attempt(owner.runs, 'fixture', owner.secret, owner.record, _question_event(owner))
    path = binding.question_path(owner.runs, owner.record['session_id'])
    before = path.read_bytes()
    marker = binding._question_marker(owner.runs, owner.secret, owner.record['session_id'])
    marker['retained_fixture'] = ['x'] * 180000
    assert len(binding.canonical(marker)) < 1_048_576
    assert binding.private_serialized_size(marker) > 1_048_576
    with pytest.raises(binding.Refusal, match='pending-unreadable'):
        binding._write_question_marker(owner.runs, owner.secret, owner.record['session_id'], marker)
    assert path.read_bytes() == before


def test_malformed_async_reply_never_breaks_or_rewrites_the_whole_prompt_capture(owner):
    binding.observe_question_attempt(owner.runs, 'fixture', owner.secret, owner.record, _question_event(owner))
    prompt = _question_envelope(owner).replace('"answer": "Approve"', '"answer": ["Approve"]')
    event = _real_prompt_capture(owner, prompt)
    assert event['prompt'] == binding.digest(prompt)
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record) == []
    assert not binding.used_path(owner.runs, 'fixture').exists()


def test_question_default_ingress_is_registered_before_and_after_ui_calls():
    settings = json.loads((ROOT / 'catalog/hooks/settings.json').read_text(encoding='utf-8'))
    for event in ('PreToolUse', 'PostToolUse', 'Stop'):
        commands = [hook['command'] for group in settings['hooks'][event] for hook in group['hooks']]
        assert sum('implementation-state.sh' in command for command in commands) == 1
    from scripts.lib.integrations import get
    from scripts.lib.integrations._codex_native import build_hook_entries
    cursor = get('cursor')._hook_registration(lambda script: script)['hooks']
    for event in ('preToolUse', 'postToolUse', 'stop'):
        assert sum('implementation-state' in entry['command'] for entry in cursor[event]) == 1
    codex, _scripts, _skipped = build_hook_entries(settings, ROOT / 'catalog/hooks', '/private-fixture/hooks')
    for event in ('PreToolUse', 'PostToolUse', 'Stop'):
        entries = [entry for group in codex[event] for entry in group['hooks']]
        assert sum('implementation-state' in entry['command'] for entry in entries) == 1


def test_cross_session_resume_is_visible_without_borrowing_old_owner_authority(owner, monkeypatch):
    page = completion_minor.action_page('v4.15', 'resume', owner.record['nonce'])
    pending = binding.render(owner.runs, 'fixture', owner.secret, action='resume', scope='v4.15',
                             page=page, session='target-session')
    display = approval_page.render_page(approval_page.render_data(pending, scope='v4.15', blocker=None, display=None))
    assert binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record, display,
                                          observer_session='target-session')
    rounds = binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record,
                                     observer_session='target-session')
    assert [row['nonce'] for row in rounds] == [pending['nonce']]
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record,
                                   observer_session='unrelated') == []
    scope = SimpleNamespace(minor=True, label='v4.15', repo_root=owner.runs.parent,
                            observer_session='target-session')
    facts = run_plan.project_owner_rounds(record_path=owner.path, scope_label='v4.15', rounds=rounds,
        results=[], previous=None, observation={'objective':'Original full objective','remaining_tasks':7,
        'work':[{'id':'old-owner-work','title':'Prior authorized work','authorized':True,'feasible':True,'evidence':'Retained A task observation'}],
        'requests':[],'jobs':[],'external_conditions':[]},secret=owner.secret,owner_session=owner.record['session_id'])
    monkeypatch.setattr(run_plan, 'native_owner_observation', lambda *args, **kwargs: facts)
    monkeypatch.setattr(run_plan, '_authorization', lambda *args, **kwargs: pytest.fail('B borrowed A authority'))
    frame = run_plan.reconcile_observation(scope, owner.path, owner.record, facts, 1, 'INCOMPLETE: tasks', readonly=True)
    assert frame['disposition']['state'] == 'waiting_owner_action'
    assert frame['disposition']['work'][0]['authorized'] is False
    assert not run_plan.continuation_path(owner.path).exists()


def test_resume_target_discovery_is_draft_only_and_exact(owner):
    import completion_gate
    page = completion_minor.action_page('v4.15', 'resume', owner.record['nonce'])
    pending = binding.render(owner.runs, 'fixture', owner.secret, action='resume', scope='v4.15',
                             page=page, session='target-session')
    assert completion_gate.find_record('target-session')[0] == owner.path
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record,
                                   observer_session='target-session') == []
    tampered = dict(owner.record, nonce='wrong-run')
    owner.path.write_text(json.dumps(tampered),encoding='utf-8')
    assert completion_gate.find_record('target-session') is None


def test_verified_session_migration_preserves_whole_unsigned_frame(owner, monkeypatch):
    scope = SimpleNamespace(minor=True,label='v4.15',repo_root=owner.runs.parent)
    old = {'contract':'implementation-continuation-v1','binding':run_plan.continuation_binding(scope,owner.path,owner.record),
           'observation':{'objective':'Complete approved objective including every clause','remaining_tasks':7,
              'jobs':[{'id':'actual','handle':'live-123'}]},'disposition':{'requests':[{'id':'old-request'}]},
           'capture_watermark':'old-source'}
    run_plan.continuation_path(owner.path).write_text(json.dumps(old),encoding='utf-8')
    current = dict(owner.record,session_id='target-session')
    current['approvals_hmac'] = checker._sign(current,owner.secret)
    owner.path.write_text(json.dumps(current),encoding='utf-8')
    monkeypatch.setattr(binding,'continuation_ancestor_valid',lambda runs,record,a,b: a=='fixture-owner' and b=='target-session')
    migrated = run_plan.read_continuation(scope,owner.path,current)
    assert migrated['binding']['session_id'] == 'target-session'
    assert migrated['observation'] == old['observation']
    assert migrated['disposition'] == old['disposition']
    assert migrated['capture_watermark'] != 'old-source'
    assert json.loads(run_plan.continuation_path(owner.path).read_text()) == old
    monkeypatch.setattr(binding,'continuation_ancestor_valid',lambda *args: False)
    with pytest.raises(run_plan.RunnerError,match='different run or session'):
        run_plan.read_continuation(scope,owner.path,current)


def test_async_reply_waits_for_inflight_attempt_without_losing_original_capture(owner, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    import time
    entered, release = Event(), Event()
    original = binding._write_private
    def writing(path, value):
        if path == binding.question_path(owner.runs, owner.record['session_id']) and value.get('question_attempts'):
            entered.set()
            assert release.wait(10)
        return original(path, value)
    monkeypatch.setattr(binding, '_write_private', writing)
    with ThreadPoolExecutor(max_workers=2) as pool:
        attempt = pool.submit(binding.observe_question_attempt, owner.runs, 'fixture', owner.secret,
                              owner.record, _question_event(owner))
        assert entered.wait(10)
        reply = pool.submit(_real_prompt_capture, owner, _question_envelope(owner))
        deadline = time.monotonic() + 10
        try:
            while not binding.capture_events(owner.runs, owner.record['session_id']):
                assert time.monotonic() < deadline
                release.wait(0.01)
        finally:
            release.set()
        assert attempt.result(timeout=10) is True
        event = reply.result(timeout=10)
    issued = binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record)
    assert len(issued) == 1 and issued[0]['decision_answer']['choice'] == 'Approve'
    assert event['prompt'] == binding.digest(_question_envelope(owner))
    assert not binding.used_path(owner.runs,'fixture').exists()


def test_omitted_observer_cannot_assume_old_owner_when_transfer_is_pending(owner):
    page = completion_minor.action_page('v4.15','resume',owner.record['nonce'])
    binding.render(owner.runs,'fixture',owner.secret,action='resume',scope='v4.15',page=page,session='target-session')
    with pytest.raises(binding.Refusal,match='observer-session-required'):
        binding.issued_requests(owner.runs,'fixture',owner.secret,owner.record)


def test_historical_unconsumed_round_becomes_internal_reconciliation_while_real_work_continues(owner,monkeypatch):
    binding.observe_issued_request(owner.runs,'fixture',owner.secret,owner.record,owner.display)
    scope=SimpleNamespace(minor=True,label='v4.15',repo_root=owner.runs.parent,observer_session='fixture-owner')
    oldfacts=run_plan.native_owner_observation(scope,owner.path,owner.record,None,remaining_tasks=7)
    previous=run_plan.reconcile_observation(scope,owner.path,owner.record,oldfacts,1,'INCOMPLETE: tasks',readonly=True)
    current=dict(owner.record,session_id='target-session')
    current['approvals_hmac']=checker._sign(current,owner.secret)
    owner.path.write_text(json.dumps(current),encoding='utf-8')
    monkeypatch.setattr(binding,'continuation_ancestor_valid',lambda *args:True)
    read_rounds=binding.issued_requests
    monkeypatch.setattr(binding,'issued_requests',lambda runs,key,secret,record,**kw:
        read_rounds(runs,key,secret,owner.record,observer_session='fixture-owner'))
    scope.observer_session='target-session'
    caller=dict(previous['observation'],work=[{'id':'actual-approved','title':'Implement the next approved task',
        'authorized':True,'feasible':True,'evidence':'Native approved task still available'}])
    frame=run_plan.reconcile_observation(scope,owner.path,current,caller,1,'INCOMPLETE: tasks',previous,readonly=True)
    assert frame['disposition']['state']=='working'
    assert frame['disposition']['requests'] and frame['disposition']['resolved_requests']==[]
    assert frame['disposition']['requests'][0]['native_reconciliation']['outcome']=='owner-session-changed'
    assert frame['observation']['owner_recovery']
    report=run_plan.reporting_module('status_report')
    assert report.pending_decisions(frame['disposition'])==[]
    for mode in ('compact','full'):
        data=json.loads((ROOT/'catalog/skills/workflow/implement-phase/references/status-snapshot.json').read_text(encoding='utf-8'))
        data.update(continuation=frame['observation'],decisions=[],running=[])
        output=report.render(data,mode)
        assert 'Controller reconciliation' in output and 'No permission was granted' in output
        assert owner.pending['paste_lines'][0] not in output
        assert 'Required actions' not in output


def test_explicit_reconcile_propagates_consumed_native_recovery_without_replaying_manual_steps(owner):
    binding.observe_issued_request(owner.runs,'fixture',owner.secret,owner.record,owner.display)
    scope=SimpleNamespace(minor=True,label='v4.15',repo_root=owner.runs.parent)
    old=run_plan.native_owner_observation(scope,owner.path,owner.record,None,remaining_tasks=7)
    previous=run_plan.reconcile_observation(scope,owner.path,owner.record,old,1,'INCOMPLETE: tasks',readonly=True)
    _captured_consumption(owner)
    caller=dict(previous['observation'],work=[{'id':'actual-approved','title':'Implement another approved task',
        'authorized':True,'feasible':True,'evidence':'Independent approved task'}])
    frame=run_plan.reconcile_observation(scope,owner.path,owner.record,caller,1,'INCOMPLETE: tasks',previous,readonly=True)
    assert frame['observation']['owner_recovery']
    assert frame['disposition']['requests'][0]['native_reconciliation']['outcome']=='capture-consumed-effect-unverified'
    assert 'Required actions' not in '\n'.join(run_plan.reporting_module('status_report').required_parts(frame['disposition']))
    assert frame['disposition']['state']=='working'


@pytest.mark.parametrize('same_effect',[True,False])
def test_identical_replacement_round_preserves_verified_prior_ui_choice_without_native_grant(owner,same_effect):
    binding.observe_question_attempt(owner.runs,'fixture',owner.secret,owner.record,_question_event(owner))
    _real_prompt_capture(owner,_question_envelope(owner))
    old=binding.issued_requests(owner.runs,'fixture',owner.secret,owner.record)
    current=dict(owner.record,session_id='target-session')
    page_scope=owner.page if same_effect else dict(owner.page,record_nonce='different-native-run')
    if not same_effect:
        current['nonce']='different-native-run'
    pending=binding.render(owner.runs,'fixture',owner.secret,action='add-class',scope='v4.15',
        page=page_scope,session='target-session')
    page=approval_page.render_page(approval_page.render_data(pending,scope='v4.15',blocker=None,display=None))
    binding.observe_issued_request(owner.runs,'fixture',owner.secret,current,page,observer_session='target-session')
    replacement=binding.issued_requests(owner.runs,'fixture',owner.secret,current,observer_session='target-session')
    facts=run_plan.project_owner_rounds(record_path=owner.path,scope_label='v4.15',rounds=old+replacement,
        results=[],previous=None,observation={'objective':'Original full objective','remaining_tasks':7,
            'requests':[],'jobs':[],'external_conditions':[],'work':[]},secret=owner.secret,owner_session='target-session')
    state=run_plan.continuation_module().reconcile(facts)
    report=run_plan.reporting_module('status_report')
    assert len(report.pending_decisions(state))==(0 if same_effect else 1)
    required='\n'.join(report.required_parts(state))
    assert pending['paste_lines'][0] in required and owner.pending['paste_lines'][0] not in required
    assert not binding.used_path(owner.runs,'fixture').exists()
    assert current['approvals']['classes']==[]


def test_question_lock_holders_never_take_round_lock_or_invoke_native_mutations(owner,monkeypatch):
    from contextlib import contextmanager
    lock=checker._minor_os_lock
    def forbidden(*args,**kwargs):
        pytest.fail('A question observer invoked native mutation')
    for function in ('_write_record','cmd_record_authorize'):
        monkeypatch.setattr(checker,function,forbidden)
    for function in ('render','consume','_claim_event','_claim_transcript'):
        monkeypatch.setattr(binding,function,forbidden)
    expected=binding.question_path(owner.runs,owner.record['session_id']).with_suffix('.mutation.lock')
    @contextmanager
    def observed(path,budget):
        assert path==expected,'Question-lock holder attempted a different native lock'
        with lock(path,budget):yield
    monkeypatch.setattr(checker,'_minor_os_lock',observed)
    binding.activate_question(owner.runs,'fixture',owner.secret,dict(owner.pending,allow_short_reply=True))
    assert binding.observe_issued_request(owner.runs,'fixture',owner.secret,owner.record,owner.display)
    assert binding.observe_question_attempt(owner.runs,'fixture',owner.secret,owner.record,_question_event(owner))


def test_observer_session_cannot_borrow_owner_authority_through_any_probe(owner,monkeypatch):
    scope=SimpleNamespace(minor=True,label='v4.15',repo_root=owner.runs.parent,observer_session='target-session')
    def forbidden(*args,**kwargs):pytest.fail('B invoked A native authorization')
    monkeypatch.setattr(checker,'authorization_probe',forbidden)
    monkeypatch.setattr(run_plan,'_checker_run',forbidden)
    item={'authorization':{'class':'release','request':{'release_version':'v4.15.6'}}}
    assert run_plan._authorization(scope,owner.record,item,readonly=True) is False
    assert run_plan._authorization(scope,owner.record,item,readonly=False) is False


def _recovery_with_real_wait(owner,kind):
    binding.observe_issued_request(owner.runs,'fixture',owner.secret,owner.record,owner.display)
    _captured_consumption(owner)
    scope=SimpleNamespace(minor=True,label='v4.15',repo_root=owner.runs.parent)
    facts=run_plan.native_owner_observation(scope,owner.path,owner.record,None,remaining_tasks=7)
    if kind=='action':
        facts['requests'].append({'id':'private-required-proof','kind':'action','title':'Provide the required installed-version proof',
            'prerequisites':['Install the qualified private fixture package'],
            'steps':['Open the private fixture application','Send its version receipt'],
            'expected_result':'The owner publishes the required version receipt','acknowledgment':'Reply with the exact receipt path'})
    else:
        facts['jobs']=[{'id':'private-existing-job','name':'Existing private tool process','handle':'existing-private-handle-42',
            'status':'running','observed_at':'2026-11-25T12:00:00Z','evidence':'Private unit fixture tool observation',
            'resume_when':'The same observed handle returns its terminal result'}]
    frame=run_plan.reconcile_observation(scope,owner.path,owner.record,facts,1,'INCOMPLETE: tasks',readonly=True)
    run_plan.save_continuation(owner.path,frame)
    return scope,frame


@pytest.mark.parametrize('kind',['action','job'])
def test_controller_recovery_does_not_conceal_an_existing_real_wait(owner,kind):
    scope,frame=_recovery_with_real_wait(owner,kind)
    disposition=run_plan.continuation_for_run(scope,owner.path,owner.record,1,'INCOMPLETE: tasks',claim_refresh=True)
    assert disposition['state']==('waiting_owner_action' if kind=='action' else 'waiting_job')
    assert disposition['directive']=='wait'
    if kind=='job':
        assert disposition['jobs'][0]['handle']=='existing-private-handle-42'
    else:
        assert any(request['id']=='private-required-proof' for request in disposition['requests'])
    required='\n'.join(run_plan.reporting_module('status_report').required_parts(disposition))
    assert owner.pending['paste_lines'][0] not in required
    assert 'Controller reconciliation' in required


def test_snapshot_recovery_does_not_hide_an_existing_owner_action(owner):
    scope,frame=_recovery_with_real_wait(owner,'action')
    snapshot=run_plan.reporting_module('status_snapshot')
    facts=snapshot.native_owner_projection(owner.path,scope.repo_root,scope.label,
        frame['observation'],frame['disposition'],7)
    disposition=run_plan.continuation_module().reconcile(facts,frame['disposition'])
    assert disposition['state']=='waiting_owner_action'
    required='\n'.join(run_plan.reporting_module('status_report').required_parts(disposition))
    assert 'Provide the required installed-version proof' in required
    assert owner.pending['paste_lines'][0] not in required


@pytest.mark.parametrize('route', ['run', 'precreate'])
def test_stop_decision_ordinals_preserve_stable_requests_and_resume(owner, monkeypatch, capsys, route):
    """Exercise real Stop consumers; typed-fact seams grant no native authority."""
    import completion_gate
    reporter = run_plan.reporting_module('status_report')
    state_module = run_plan.continuation_module()
    requests = [{'id': key, 'kind': 'decision', 'title': 'Choose ' + key,
                 'detail': 'Keep the original authorization boundary', 'reply': 'Reply A or B',
                 'options': [{'option': 'A', 'meaning': 'Continue bounded work', 'effect': 'Original scope only'},
                             {'option': 'B', 'meaning': 'Wait', 'effect': 'No new authority'}]}
                for key in ('source-expansion', '9')]
    facts = {'objective': 'Complete the entire approved minor and release', 'remaining_tasks': 7,
             'requests': requests}
    disposition = state_module.reconcile(facts)
    original = json.loads(json.dumps(owner.record))
    binding.observe_issued_request(owner.runs, 'fixture', owner.secret, owner.record, owner.display)
    issued = binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record)
    payload = {'session_id': owner.record['session_id'], 'hook_event_name': 'Stop',
               'last_assistant_message': 'No decisions waiting'}
    if route == 'run':
        monkeypatch.setattr(run_plan, 'continuation_for_run', lambda *args, **kwargs: disposition)
        invoke = lambda: completion_gate._reconcile_stop(payload, owner.path, owner.record,
            owner.runs.parent, 1, 'INCOMPLETE: task.T001', [])
    else:
        metadata = dict(owner.record, schema=0)
        monkeypatch.setattr(checker, 'precreate_owner_context', lambda *args, **kwargs:
            (SimpleNamespace(root=owner.runs.parent, plan='private-plan'), owner.path, metadata))
        monkeypatch.setattr(run_plan, 'precreate_owner_observation', lambda *args, **kwargs: facts)
        invoke = lambda: completion_gate._precreate_stop(payload, owner.record['session_id'])
    invoke()
    correction = capsys.readouterr().out
    assert 'Decision #1: Choose source-expansion' in correction
    assert 'Decision #2: Choose 9' in correction
    assert 'requires reconciliation' not in correction
    assert disposition['requests'] == requests
    assert 'Decision #1:' in '\n'.join(reporter.decision_parts(requests[0], True))
    honest = [reporter.state_heading(disposition), *reporter.required_parts(disposition)]
    for number, decision in enumerate(reporter.pending_decisions(disposition), 1):
        honest.extend(reporter.decision_parts(decision, True, number=number))
    payload['last_assistant_message'] = '\n\n'.join(honest)
    invoke()
    assert capsys.readouterr().out == ''
    # A verified typed owner result advances the real state engine; it is not
    # a native approval capture, and the signed fixture authority stays intact.
    facts = {'objective': facts['objective'], 'remaining_tasks': 7,
             'work': [{'id': 'original-work', 'title': 'Continue approved work',
                       'authorized': True, 'feasible': True, 'evidence': 'Original approved scope'}],
             'resolutions': [{'request_id': item['id'], 'verified': True,
                              'evidence': 'Typed owner fixture result', 'authority_receipt': 'unit-owner-result-' + item['id']} for item in requests]}
    disposition = state_module.reconcile(facts, disposition)
    assert disposition['state'] == 'working' and disposition['directive'] == 'continue'
    assert disposition['requests'] == []
    invoke()
    output = capsys.readouterr().out
    if route == 'run':
        assert 'Continue approved work' in output
    else:
        saved = json.loads(run_plan.continuation_path(owner.path).read_text())['disposition']
        assert saved['state'] == 'working' and saved['directive'] == 'continue'
        assert saved['requests'] == [] and saved['resolved_requests'] == disposition['resolved_requests']
    assert owner.record == original
    assert binding.issued_requests(owner.runs, 'fixture', owner.secret, owner.record) == issued
