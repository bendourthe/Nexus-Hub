"""Exact native-owner retries use private captures, never live approval authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import time

import pytest

from .test_completion_minor_record import SESSION, minor, ck, cm, _isolated_git_config  # noqa: F401
from .test_minor_execution_permission import ExecutionMinor, TOKEN, _declared_execution_members, _private_native_home, _no_transport_overrides  # noqa: F401
import approval_binding as binding
from .test_codex_transcript_approval import Transcript, SESSION as CODEX_SESSION


@pytest.fixture
def round_case(tmp_path, monkeypatch):
    runs = tmp_path / 'runs'
    runs.mkdir()
    monkeypatch.delenv('NEXUS_RUNNER_LAUNCH', raising=False)
    secret = b'private recovery fixture key'.ljust(32, b'!')
    session = 'private-owner'
    page = {'scope': {'kind': 'minor', 'minor': 'v4.15'}, 'record_nonce': 'private-record',
            'action': 'add-class', 'class': 'archive-member'}
    pending = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page, session=session)
    prompts = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    prompts.parent.mkdir()
    prompts.write_text(''.join(json.dumps(event) + '\n' for event in [
        {'session': session, 'prompt': binding.digest('Begin private fixture'), 'at': pending['rendered_at'] - 1, 'event_id': 'before'},
        {'session': session, 'prompt': pending['paste_digests'][0], 'at': pending['rendered_at'] + .01, 'event_id': 'reply'},
    ]), encoding='utf-8')
    return runs, secret, session, page, pending


def test_claimed_round_can_finish_same_operation_without_replaying_consumption(typed_round_case):
    runs, secret, session, page, pending = typed_round_case
    consumed, _ = binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    claims = _all_claims(runs)
    recovered = binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page,
                                               session=session, required_session=session)
    assert recovered[0]['nonce'] == pending['nonce'] and recovered[0]['capture'] == consumed['capture']
    assert claims == _all_claims(runs)
    with pytest.raises(binding.Refusal, match='code-used'):
        binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)


@pytest.mark.parametrize('change', ['page', 'session', 'required_session', 'newer_round'])
def test_recovery_cannot_expand_scope_or_replace_newer_pending_round(round_case, change):
    runs, secret, session, page, _pending = round_case
    binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    kwargs = dict(action='add-class', live_page=page, session=session, required_session=session)
    if change == 'page':
        kwargs['live_page'] = dict(page, **{'class': 'release-notes'})
    elif change in ('session', 'required_session'):
        kwargs[change] = 'foreign-owner'
    else:
        binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page, session=session)
        assert binding.recover_consumed_round(runs, 'private', secret, **kwargs) is None
        return
    with pytest.raises(binding.Refusal):
        binding.recover_consumed_round(runs, 'private', secret, **kwargs)


def test_prepared_marker_without_a_claim_is_not_recovery_authority(round_case):
    runs, secret, session, page, pending = round_case
    events = binding.capture_events(runs, session)
    pending['capture'] = binding.host_capture_context(events[-1], session)
    binding._retain_used_round(runs, 'private', secret, pending)
    assert binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page, session=session) is None


def test_private_size_matches_physical_serializer_and_refuses_unreadable_recovery(round_case):
    runs, secret, session, page, pending = round_case
    payload = {'unicode': 'caf\u00e9', 'rows': ['one', 'two']}
    path = runs / 'size-control.json'
    binding._write_private(path, payload)
    assert path.stat().st_size == binding.private_serialized_size(payload)
    pending['private_size_control'] = [''] * 150000
    with pytest.raises(binding.Refusal, match='recovery-capacity'):
        binding._retain_used_round(runs, 'private', secret, pending)
    assert not binding.used_path(runs, 'private').exists()
    assert not (runs / 'consumed-prompts').exists()


def test_ancestor_probe_refuses_unsupported_native_signing_instead_of_throwing(tmp_path, monkeypatch):
    runs = tmp_path / 'runs'
    runs.mkdir()
    monkeypatch.setenv('NEXUS_HUB_RUNS_DIR', str(runs))
    monkeypatch.setattr(ck, '_secret', lambda **kwargs: b'private key')
    monkeypatch.setattr(ck, '_sign', lambda *args, **kwargs: (_ for _ in ()).throw(ck.Malformed('private unsupported format')))
    assert not binding.continuation_ancestor_valid(runs, {'schema': 2, 'session_id': 'B'}, 'A', 'B')


def test_real_add_class_retry_preserves_old_capture_across_verified_codex_resume(minor, monkeypatch):
    assert minor.create().returncode == 0
    rendered = _typed_native_paste(monkeypatch, minor, SESSION, '--action', 'add-class', '--class', 'archive-member')
    monkeypatch.chdir(minor.work)
    argv = ['record', 'add-class', '--minor', 'v0.5', '--session', SESSION, '--class', 'archive-member']
    _ctx, original = ck.resolve_minor_controller(minor.record_path(), SESSION, minor_protocol=1, execution_protocol=1)
    secret = ck._secret(create=False)
    key = minor.record_path().stem
    assert binding.observe_issued_request(minor.runs, key, secret, original, rendered.stdout)
    issued = binding.issued_requests(minor.runs, key, secret, original)
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', lambda *args: (_ for _ in ()).throw(OSError('private pre-handoff write failure')))
        with pytest.raises(OSError):
            ck.main(argv)
    old = next(row for row in binding.used_recovery_rounds(minor.runs, key, secret) if row['action'] == 'add-class')
    home = minor.tmp / 'codex-handoff-home'
    home.mkdir()
    log = Transcript(home, minor.work, time.time() - 10)
    for name in ('HOME', 'USERPROFILE'):
        minor.env[name] = str(home)
        monkeypatch.setenv(name, str(home))
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    rendered = minor.render(CODEX_SESSION, '--action', 'resume', '--question', '--host-transcript', str(log.path))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    log.now = time.time() - 1
    log.user('Approve')
    resumed = minor.run('record', 'resume', '--minor', 'v0.5', '--session', CODEX_SESSION)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    _ctx, current = ck.resolve_minor_controller(minor.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    assert binding.continuation_ancestor_valid(minor.runs, current, SESSION, CODEX_SESSION)
    assert not binding.continuation_ancestor_valid(minor.runs, current, 'foreign-owner', CODEX_SESSION)
    receipt = binding._receipt_path(minor.runs, current['continuations'][-1]['capture'])
    held = receipt.with_suffix('.private-held')
    receipt.replace(held)
    try:
        assert not binding.continuation_ancestor_valid(minor.runs, current, SESSION, CODEX_SESSION)
    finally:
        held.replace(receipt)
    before = minor.record_path().read_bytes()
    used_before = binding.used_path(minor.runs, key).read_bytes()
    log.context(policy='on-request')
    new_argv = ['record', 'add-class', '--minor', 'v0.5', '--session', CODEX_SESSION, '--class', 'archive-member']
    assert ck.main(new_argv) != 0
    assert minor.record_path().read_bytes() == before
    assert binding.used_path(minor.runs, key).read_bytes() == used_before
    log.context()
    claims = {p.relative_to(minor.runs).as_posix(): p.read_bytes()
              for folder in ('consumed-prompts', 'transcript-receipts')
              if (minor.runs / folder).exists() for p in (minor.runs / folder).iterdir() if p.is_file()}
    assert ck.main(new_argv) == 0
    assert ck.main(new_argv) == 0
    _ctx, saved = ck.resolve_minor_controller(minor.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    added = next(entry for entry in saved['approvals']['classes'] if entry['class'] == 'archive-member')
    assert saved['session_id'] == CODEX_SESSION
    assert added['added']['authorization_context'] == old['capture']
    assert len(cm.continuation_owner_results(ck, saved, issued)) == 1
    assert not any(row['action'] == 'add-class' for row in binding.used_recovery_rounds(minor.runs, key, secret))
    assert claims == {p.relative_to(minor.runs).as_posix(): p.read_bytes()
                      for folder in ('consumed-prompts', 'transcript-receipts')
                      if (minor.runs / folder).exists() for p in (minor.runs / folder).iterdir() if p.is_file()}


@pytest.mark.parametrize('when', ['before_replace', 'during_replace', 'after_replace'])
def test_real_add_class_retry_finishes_once_after_native_write_failure(minor, monkeypatch, when):
    assert minor.create().returncode == 0
    minor.paste(SESSION, '--action', 'add-class', '--class', 'archive-member')
    monkeypatch.chdir(minor.work)
    argv = ['record', 'add-class', '--minor', 'v0.5', '--session', SESSION, '--class', 'archive-member']
    writer = ck._write_record
    def fail(path, record):
        if when == 'during_replace':
            replace = ck.os.replace
            def fail_replace(source, target):
                if str(target) == str(path):
                    raise OSError('private injected native write failure')
                return replace(source, target)
            with monkeypatch.context() as patch:
                patch.setattr(ck.os, 'replace', fail_replace)
                writer(path, record)
        if when == 'after_replace':
            writer(path, record)
        raise OSError('private injected native write failure')
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', fail)
        with pytest.raises(OSError, match='private injected'):
            ck.main(argv)
    claim_root = minor.runs / 'consumed-prompts'
    claims = {p.name: p.read_bytes() for p in claim_root.iterdir()}
    if when != 'after_replace':
        before = minor.record_path().read_bytes()
        assert ck.main(argv) != 0
        assert minor.record_path().read_bytes() == before
        assert claims == {p.name: p.read_bytes() for p in claim_root.iterdir()}
        return
    assert ck.main(argv) == 0
    assert ck.main(argv) == 0
    _ctx, verified = ck.resolve_minor_controller(minor.record_path(), SESSION, minor_protocol=1, execution_protocol=1)
    assert len([entry for entry in verified['approvals']['classes'] if entry['class'] == 'archive-member']) == 1
    assert claims == {p.name: p.read_bytes() for p in claim_root.iterdir()}


def test_prepared_and_claimed_crash_positions_keep_single_consumption(typed_round_case, monkeypatch):
    runs, secret, session, page, pending = typed_round_case
    with monkeypatch.context() as patch:
        patch.setattr(binding, '_claim_transcript', lambda *args: (_ for _ in ()).throw(OSError('before claim')))
        with pytest.raises(binding.Refusal, match='approval-not-captured'):
            binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    assert binding.pending_path(runs, 'private').exists()
    assert binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page, session=session) is None
    original_unlink = type(binding.pending_path(runs, 'private')).unlink
    target = binding.pending_path(runs, 'private')
    def fail_unlink(path, *args, **kwargs):
        if path == target:
            raise OSError('after claim')
        return original_unlink(path, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(type(target), 'unlink', fail_unlink)
        with pytest.raises(binding.Refusal, match='approval-not-captured'):
            binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    assert target.exists()
    recovered = binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page, session=session)
    assert recovered[0]['nonce'] == pending['nonce'] and not target.exists()
    assert len(list((runs / 'transcript-receipts').iterdir())) == 1


def test_capacity_refuses_before_the_next_capture_is_claimed(round_case):
    runs, secret, session, page, pending = round_case
    prompt_path = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    for index in range(65):
        if index == 64:
            before = {p.name for p in (runs / 'consumed-prompts').iterdir()}
            with pytest.raises(binding.Refusal, match='recovery-capacity'):
                binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page, session=session)
            assert before == {p.name for p in (runs / 'consumed-prompts').iterdir()}
            assert not binding.pending_path(runs, 'private').exists()
            break
        if index:
            pending = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page, session=session)
            with prompt_path.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps({'session': session, 'prompt': pending['paste_digests'][0],
                    'at': pending['rendered_at'] + .01, 'event_id': f'reply-{index}'}) + '\n')
        binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)


def test_changed_owner_cannot_reuse_or_erase_the_old_consumed_capture(round_case):
    runs, secret, session, page, pending = round_case
    first, _ = binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    before = binding.used_path(runs, 'private').read_bytes()
    with pytest.raises(binding.Refusal, match='session-mismatch'):
        binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page,
                                      session='new-owner-after-supported-handoff', required_session='new-owner-after-supported-handoff')
    assert binding.used_path(runs, 'private').read_bytes() == before
    assert binding.consumed_issued_request(runs, 'private', secret, pending) == first['capture']


def test_current_permission_must_match_every_page_field_even_if_another_round_granted_it(monkeypatch):
    page = {'member': 'v4.15.6', 'write_paths': ['catalog/hooks/settings.json'], 'worker_identity': {'head': 'private'}}
    entry = {'page': page, 'accepted': {'round_nonce': 'different-genuine-round'}}
    calls = []
    def verified_history(_ck, _record, *, capture=False):
        calls.append(capture)
        return [entry]
    monkeypatch.setattr(cm, 'execution_permission_history', verified_history)
    assert cm._exact_execution_owner_result(ck, {}, page) is entry
    assert cm._exact_execution_owner_result(ck, {}, dict(page, write_paths=['other'])) is None
    assert calls == [True, True]


def test_supersession_does_not_resurrect_a_verified_completed_permission(monkeypatch):
    page = {'member': 'v4.15.6', 'write_paths': ['original']}
    completed = {'page': page, 'accepted': {'round_nonce': 'completed-private-round'}}
    newer = {'page': dict(page, write_paths=['newer']), 'accepted': {'round_nonce': 'later-private-round'}}
    monkeypatch.setattr(cm, 'execution_permission_history', lambda *args, **kwargs: [completed, newer])
    assert cm._exact_execution_owner_result(ck, {}, page, 'completed-private-round') is completed
    assert cm._exact_execution_owner_result(ck, {}, page) is None


def test_real_later_capture_does_not_destroy_failed_operation_provenance(minor, monkeypatch):
    assert minor.create().returncode == 0
    minor.paste(SESSION, '--action', 'add-class', '--class', 'archive-member')
    monkeypatch.chdir(minor.work)
    argv = ['record', 'add-class', '--minor', 'v0.5', '--session', SESSION, '--class', 'archive-member']
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', lambda *args: (_ for _ in ()).throw(OSError('private first write failure')))
        with pytest.raises(OSError):
            ck.main(argv)
    key = minor.record_path().stem
    secret = ck._secret(create=False)
    earlier = next(row for row in binding.used_recovery_rounds(minor.runs, key, secret) if row['action'] == 'add-class')
    minor.paste(SESSION, '--action', 'add-class', '--class', 'archive-member')
    assert binding.consumed_issued_request(minor.runs, key, secret, earlier) == earlier['capture']
    assert ck.main(argv) == 0
    assert ck.main(argv) == 0
    _ctx, saved = ck.resolve_minor_controller(minor.record_path(), SESSION, minor_protocol=1, execution_protocol=1)
    assert len([row for row in saved['approvals']['classes'] if row['class'] == 'archive-member']) == 1
    assert binding.used_recovery_rounds(minor.runs, key, secret) == []


@pytest.mark.parametrize('when', ['before_replace', 'after_replace'])
def test_real_execution_permission_retry_is_exact_and_does_not_duplicate_history(tmp_path, monkeypatch, when):
    fixture = ExecutionMinor(tmp_path, monkeypatch)
    assert fixture.create().returncode == 0
    fixture.add_members(('v4.15.6',))
    fixture.worker('v4.15.6')
    request = fixture.request('v4.15.6')
    rendered = _typed_native_paste(monkeypatch, fixture, SESSION, '--action', 'permit-member-execution-paths',
                                  '--member', 'v4.15.6', '--execution', str(request))
    _ctx, original = ck.resolve_minor_controller(fixture.record_path(), SESSION, minor_protocol=1, execution_protocol=1)
    secret = ck._secret(create=False)
    key = fixture.record_path().stem
    assert binding.observe_issued_request(fixture.runs, key, secret, original, rendered.stdout)
    issued = binding.issued_requests(fixture.runs, key, secret, original)
    monkeypatch.chdir(fixture.work)
    argv = ['record', 'permit-member-execution-paths', '--minor', TOKEN, '--session', SESSION,
            '--member', 'v4.15.6', '--execution', str(request)]
    writer = ck._write_record
    def fail(path, record):
        if when == 'after_replace':
            writer(path, record)
        raise OSError('private execution write failure')
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', fail)
        with pytest.raises(OSError, match='private execution'):
            ck.main(argv)
    claims = _all_claims(fixture.runs)
    assert ck.main(argv) == 0
    assert ck.main(argv) == 0
    _ctx, saved = ck.resolve_minor_controller(fixture.record_path(), SESSION, minor_protocol=1, execution_protocol=1)
    assert len(cm.execution_permission_history(ck, saved, capture=True)) == 1
    assert claims == _all_claims(fixture.runs)
    if when == 'after_replace':
        home = fixture.tmp / 'permission-resume-home'
        home.mkdir()
        log = Transcript(home, fixture.work, time.time() - 10)
        for name in ('HOME', 'USERPROFILE'):
            fixture.env[name] = str(home)
            monkeypatch.setenv(name, str(home))
        monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
        rendered = fixture.render(CODEX_SESSION, '--action', 'resume', '--question', '--host-transcript', str(log.path))
        assert rendered.returncode == 0, rendered.stdout + rendered.stderr
        log.now = time.time() - 1
        log.user('Approve')
        resumed = fixture.run('record', 'resume', '--minor', TOKEN, '--session', CODEX_SESSION)
        assert resumed.returncode == 0, resumed.stdout + resumed.stderr
        _ctx, after_resume = ck.resolve_minor_controller(fixture.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
        assert len(cm.continuation_owner_results(ck, after_resume, issued)) == 1


def test_later_render_and_capture_preserve_an_earlier_unfinished_claim(typed_round_case):
    runs, secret, session, page, pending = typed_round_case
    first, _ = binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    second_page = dict(page, **{'class': 'other-private-class'})
    second = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=second_page, session=session)
    assert binding.consumed_issued_request(runs, 'private', secret, pending) == first['capture']
    prompt_path = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    with prompt_path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'session': session, 'prompt': second['paste_digests'][0],
                                'at': second['rendered_at'] + .01, 'event_id': 'second'}) + '\n')
    assert binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=second_page, session=session) is None
    binding.consume(runs, 'private', secret, action='add-class', live_page=second_page, session=session)
    recovered, _ = binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page, session=session)
    assert recovered['nonce'] == pending['nonce'] and recovered['capture'] == first['capture']



def _resume_round(round_case):
    runs, secret, session, _page, _old = round_case
    page = {'action': 'resume', 'scope': {'kind': 'minor', 'minor': 'v4.15'}, 'record_nonce': 'private-record'}
    condition = binding.resume_condition({'session_id': 'original-owner', 'pause': None})
    pending = binding.render(runs, 'private', secret, action='resume', scope='v4.15', page=page,
                             session=session, recovery_condition=condition)
    prompts = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    with prompts.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'session': session, 'prompt': pending['paste_digests'][0],
            'at': pending['rendered_at'] + .01, 'event_id': 'resume-reply'}) + '\n')
    return runs, secret, session, page, pending, condition


def test_resume_render_condition_is_sealed_before_first_claim_and_reuse(round_case):
    runs, secret, session, page, pending, condition = _resume_round(round_case)
    with pytest.raises(binding.Refusal, match='pending-unreadable'):
        binding.consume(runs, 'private', secret, action='resume', live_page=page, session=session)
    changed = binding.resume_condition({'session_id': 'original-owner', 'pause': {'at': 'later'}})
    with pytest.raises(binding.Refusal, match='recovery-condition-changed'):
        binding.consume(runs, 'private', secret, action='resume', live_page=page,
                        session=session, recovery_condition=changed)
    assert not (runs / 'consumed-prompts').exists()
    same = binding.render(runs, 'private', secret, action='resume', scope='v4.15', page=page,
                          session=session, recovery_condition=condition)
    assert same['nonce'] == pending['nonce']
    newer = binding.render(runs, 'private', secret, action='resume', scope='v4.15', page=page,
                           session=session, recovery_condition=changed)
    assert newer['nonce'] != pending['nonce']
    legacy = dict(newer)
    legacy.pop('recovery_condition')
    legacy['mac'] = binding._seal(secret, legacy)
    binding._write_private(binding.pending_path(runs, 'private'), legacy)
    with pytest.raises(binding.Refusal, match='recovery-condition-changed'):
        binding.consume(runs, 'private', secret, action='resume', live_page=page,
                        session=session, recovery_condition=changed)
    assert not (runs / 'consumed-prompts').exists()


def test_sealed_render_context_changes_round_without_changing_canonical_page(round_case):
    runs, secret, session, page, _pending = round_case
    first = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page,
                           session=session, render_context={'display': {'label': 'first'}})
    same = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page,
                          session=session, render_context={'display': {'label': 'first'}})
    second = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page,
                            session=session, render_context={'display': {'label': 'second'}})
    assert same['nonce'] == first['nonce'] and second['nonce'] != first['nonce']
    assert first['page'] == second['page']


def test_unknown_hook_resume_retry_requires_exact_latest_event_and_never_auto_authorizes(round_case):
    runs, secret, session, page, pending, condition = _resume_round(round_case)
    consumed, _ = binding.consume(runs, 'private', secret, action='resume', live_page=page,
                                 session=session, recovery_condition=condition)
    assert consumed['capture']['permission_mode'] is None
    assert not binding.full_access_authorization({'session_id': session, 'approvals': {}}, consumed['capture'])
    with pytest.raises(binding.Refusal, match='recovery-claim-owner-unavailable'):
        binding.recover_consumed_round(runs, 'private', secret, action='resume', live_page=page,
            session=session, recovery_condition=condition)
    prompts = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    with prompts.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'session': session, 'prompt': binding.digest('different later event'),
            'at': pending['rendered_at'] + 1, 'event_id': 'later'}) + '\n')
    with pytest.raises(binding.Refusal, match='recovery-context-changed'):
        binding.recover_consumed_round(runs, 'private', secret, action='resume', live_page=page,
            session=session, recovery_condition=condition)


def test_render_cannot_replace_prepared_round_before_irreversible_claim(round_case, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    runs, secret, session, page, pending = round_case
    entered, rendered = Event(), Event()
    original = binding._claim_event
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = None
        def claim(*args):
            nonlocal future
            def replacement():
                entered.set()
                value = binding.render(runs, 'private', secret, action='add-class', scope='v4.15',
                                       page=page, session=session)
                rendered.set()
                return value
            future = executor.submit(replacement)
            assert entered.wait(1)
            assert not rendered.wait(.15), 'render replaced the prepared marker before claim'
            original(*args)
        monkeypatch.setattr(binding, '_claim_event', claim)
        consumed, _ = binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
        replacement = future.result(timeout=5)
    assert replacement['nonce'] != pending['nonce']
    assert binding._read_pending(binding.pending_path(runs, 'private'), secret)['nonce'] == replacement['nonce']
    assert binding.consumed_issued_request(runs, 'private', secret, pending) == consumed['capture']


def _hook_capture(monkeypatch, fixture, session, text, mode):
    import completion_gate as gate
    payload = {'session_id': session, 'prompt': text, 'cwd': str(fixture.work)}
    if mode is not None:
        payload['permission_mode'] = mode
    with monkeypatch.context() as patch:
        patch.setattr(gate, '_read_payload', lambda: payload)
        assert gate.cmd_capture() == 0


@pytest.mark.parametrize('when,mode', [('before_replace', None), ('after_replace', None),
                                      ('before_replace', 'bypassPermissions'), ('after_replace', 'bypassPermissions')])
def test_real_resume_retry_preserves_single_hook_claim_and_later_pause(minor, monkeypatch, when, mode):
    assert minor.create().returncode == 0
    monkeypatch.chdir(minor.work)
    target = 'private-resume-owner'
    _hook_capture(monkeypatch, minor, target, 'Begin genuine private resume fixture', mode)
    rendered = minor.render(target, '--action', 'resume')
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    key, secret = minor.record_path().stem, ck._secret(create=False)
    pending = binding._read_pending(binding.pending_path(minor.runs, key), secret)
    assert pending['recovery_condition'] == binding.resume_condition(minor.record())
    _hook_capture(monkeypatch, minor, target, pending['paste_lines'][0], mode)
    argv = ['record', 'resume', '--minor', 'v0.5', '--session', target]
    writer = ck._write_record
    def fail(path, record):
        if when == 'after_replace':
            writer(path, record)
        raise OSError('private resume save failure')
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', fail)
        with pytest.raises(OSError, match='private resume save failure'):
            ck.main(argv)
    assert minor.record()['session_id'] == (target if when == 'after_replace' else SESSION)
    paused_before_retry = None
    if when == 'after_replace':
        minor.paste(target, '--action', 'pause')
        assert ck.main(['record', 'pause', '--minor', 'v0.5', '--session', target]) == 0
        paused_before_retry = minor.record_path().read_bytes()
    claims = {p.name: p.read_bytes() for p in (minor.runs / 'consumed-prompts').iterdir()}
    if when == 'before_replace':
        before = minor.record_path().read_bytes()
        assert ck.main(argv) != 0
        assert minor.record_path().read_bytes() == before
        assert claims == {p.name: p.read_bytes() for p in (minor.runs / 'consumed-prompts').iterdir()}
        return
    assert ck.main(argv) == 0
    _ctx, saved = ck.resolve_minor_controller(minor.record_path(), target, minor_protocol=1, execution_protocol=1)
    assert len(saved['continuations']) == 1
    if paused_before_retry is not None:
        assert minor.record_path().read_bytes() == paused_before_retry
    assert binding.continuation_ancestor_valid(minor.runs, saved, SESSION, target)
    assert saved['continuations'][0]['capture']['permission_mode'] == mode
    assert binding.full_access_authorization(saved, saved['continuations'][0]['capture']) is (mode == 'bypassPermissions')
    assert claims == {p.name: p.read_bytes() for p in (minor.runs / 'consumed-prompts').iterdir()}
    # A genuinely later pause survives repeated acknowledgment of the saved resume.
    if paused_before_retry is None:
        minor.paste(target, '--action', 'pause')
        assert ck.main(['record', 'pause', '--minor', 'v0.5', '--session', target]) == 0
    paused = minor.record_path().read_bytes()
    assert ck.main(argv) == 0
    assert minor.record_path().read_bytes() == paused
    if when == 'after_replace' and mode is None:
        # B1's completed pointer must not mask B2's failed, genuinely new resume.
        rendered = minor.render(target, '--action', 'resume')
        assert rendered.returncode == 0
        newer = binding._read_pending(binding.pending_path(minor.runs, key), secret)
        _hook_capture(monkeypatch, minor, target, newer['paste_lines'][0], mode)
        with monkeypatch.context() as patch:
            patch.setattr(ck, '_write_record', lambda *args: (_ for _ in ()).throw(OSError('private second resume')))
            with pytest.raises(OSError, match='private second resume'):
                ck.main(argv)
        assert minor.record_path().read_bytes() == paused
        second_claims = {p.name: p.read_bytes() for p in (minor.runs / 'consumed-prompts').iterdir()}
        assert ck.main(argv) != 0
        assert minor.record_path().read_bytes() == paused and len(minor.record()['continuations']) == 1
        assert second_claims == {p.name: p.read_bytes() for p in (minor.runs / 'consumed-prompts').iterdir()}


def test_real_resume_failed_claim_cannot_clear_newer_native_pause(minor, monkeypatch):
    assert minor.create().returncode == 0
    monkeypatch.chdir(minor.work)
    target = 'private-owner-before-new-pause'
    minor.paste(target, '--action', 'resume')
    argv = ['record', 'resume', '--minor', 'v0.5', '--session', target]
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', lambda *args: (_ for _ in ()).throw(OSError('private prewrite')))
        with pytest.raises(OSError, match='private prewrite'):
            ck.main(argv)
    minor.paste(SESSION, '--action', 'pause')
    assert ck.main(['record', 'pause', '--minor', 'v0.5', '--session', SESSION]) == 0
    before = minor.record_path().read_bytes()
    assert ck.main(argv) != 0
    assert minor.record_path().read_bytes() == before


def test_unclaimed_or_malformed_hook_cannot_create_operational_continuation(round_case):
    import copy
    runs, secret, session, page, pending, condition = _resume_round(round_case)
    pending['capture'] = binding.host_capture_context(binding.capture_events(runs, session)[-1], session)
    previous = {'nonce': 'private-record', 'session_id': 'original-owner', 'approvals': {}}
    prepared = copy.deepcopy(previous)
    binding.append_continuation(prepared, pending, session, retain_hook=True)
    prepared['session_id'] = session
    with pytest.raises(ValueError, match='genuine consumed'):
        binding.check_continuation_write(runs, previous, prepared)
    malformed = copy.deepcopy(pending)
    malformed['capture']['origin'] = 'unknown-origin'
    with pytest.raises(ValueError, match='provenance'):
        binding.append_continuation(copy.deepcopy(previous), malformed, session, retain_hook=True)
    consumed, _ = binding.consume(runs, 'private', secret, action='resume', live_page=page,
                                 session=session, recovery_condition=condition)
    saved = copy.deepcopy(previous)
    binding.append_continuation(saved, consumed, session, retain_hook=True)
    saved['session_id'] = session
    binding.check_continuation_write(runs, previous, saved)
    assert not binding.full_access_authorization(saved)



@pytest.mark.parametrize('reader', ['rounds', 'pointer', 'retire'])
def test_retained_marker_growth_is_bounded_after_size_observation(round_case, monkeypatch, reader):
    runs, secret, session, page, pending = round_case
    consumed, _ = binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    target = binding.used_path(runs, 'private')
    original_open = Path.open
    requests = []
    class GrowingFile:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, limit=-1):
            requests.append(limit)
            assert limit == 1_048_577, 'retained owner data was read without a byte limit'
            return b' ' * limit
    def grow_after_stat(path, *args, **kwargs):
        return GrowingFile() if path == target else original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', grow_after_stat)
    with pytest.raises(binding.Refusal, match='recovery-unreadable'):
        if reader == 'rounds':
            binding.used_recovery_rounds(runs, 'private', secret)
        elif reader == 'pointer':
            binding.completed_resume_pointer(runs, 'private', secret)
        else:
            binding.retire_used_recovery(runs, 'private', secret, consumed)
    assert requests == [1_048_577]


def test_render_refuses_byte_capacity_before_superseding_recoverable_claim(typed_round_case):
    runs, secret, session, page, pending = typed_round_case
    consumed, _ = binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    before = binding.used_path(runs, 'private').read_bytes()
    claims = _all_claims(runs)
    # The page alone fits; a supported bounded future capture cannot be reserved.
    large_page = dict(page, private_capacity_control='x' * 1_000_000)
    assert len(binding.canonical(large_page)) < 1_048_576
    with pytest.raises(binding.Refusal, match='recovery-capacity'):
        binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=large_page, session=session)
    assert binding.used_path(runs, 'private').read_bytes() == before
    assert not binding.pending_path(runs, 'private').exists()
    recovered, _ = binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page,
                                                 session=session, required_session=session)
    assert recovered['nonce'] == consumed['nonce'] == pending['nonce']
    assert claims == _all_claims(runs)


def test_capture_growth_cap_refuses_before_claim_without_truncating_metadata(round_case):
    runs, secret, session, page, pending = round_case
    prompts = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    with prompts.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'session': session, 'prompt': pending['paste_digests'][0],
            'at': pending['rendered_at'] + .02, 'event_id': 'oversize-capture',
            'permission_mode': 'x' * 65_536}) + '\n')
    before = binding.pending_path(runs, 'private').read_bytes()
    with pytest.raises(binding.Refusal, match='recovery-capacity'):
        binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    assert binding.pending_path(runs, 'private').read_bytes() == before
    assert not binding.used_path(runs, 'private').exists()
    assert not (runs / 'consumed-prompts').exists()


def test_auto_session_binds_only_the_genuinely_matched_capture(round_case):
    runs, secret, session, page, _old = round_case
    pending = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page, session=None)
    prompts = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    with prompts.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'session': session, 'prompt': pending['paste_digests'][0],
            'at': pending['rendered_at'] + .01, 'event_id': 'auto-reply'}) + '\n')
    before = binding.pending_path(runs, 'private').read_bytes()
    with pytest.raises(binding.Refusal, match='session-mismatch'):
        binding.consume(runs, 'private', secret, action='add-class', live_page=page,
                        session='foreign-owner', required_session=session)
    assert binding.pending_path(runs, 'private').read_bytes() == before
    assert not binding.used_path(runs, 'private').exists()
    assert not (runs / 'consumed-prompts').exists()
    consumed, actual = binding.consume(runs, 'private', secret, action='add-class', live_page=page,
                                      session='auto', required_session=session)
    assert actual == session and consumed['capture']['session_id'] == session
    rows = binding.used_recovery_rounds(runs, 'private', secret)
    assert len(rows) == 1 and rows[0]['session'] == session and rows[0]['nonce'] == pending['nonce']
    with pytest.raises(binding.Refusal, match='recovery-claim-owner-unavailable'):
        binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page,
                                       session=session, required_session=session)



@pytest.fixture
def typed_round_case(round_case, monkeypatch):
    runs, secret, session, page, _old = round_case
    home, work = runs.parent / 'typed-home', runs.parent / 'typed-work'
    home.mkdir()
    work.mkdir()
    (runs / '.secret').write_bytes(secret)
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    log = Transcript(home, work, time.time() - 10, session=session)
    pending = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page,
        session=session, host_transcript=log.path, allowed_cwds={str(work.resolve())})
    log.now = time.time() - 1
    log.user(pending['paste_lines'][0])
    return runs, secret, session, page, pending


def _all_claims(runs):
    return {p.relative_to(runs).as_posix(): p.read_bytes()
            for name in ('consumed-prompts', 'transcript-receipts') if (runs / name).exists()
            for p in (runs / name).iterdir() if p.is_file()}


def _typed_native_paste(monkeypatch, fixture, session, *args):
    home = fixture.tmp / 'typed-exact-owner-home'
    home.mkdir(exist_ok=True)
    for name in ('HOME', 'USERPROFILE'):
        fixture.env[name] = str(home)
        monkeypatch.setenv(name, str(home))
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    logs = getattr(fixture, '_typed_owner_logs', {})
    if session not in logs:
        logs[session] = Transcript(home, fixture.work, time.time() - 10, session=session)
        fixture._typed_owner_logs = logs
    log = logs[session]
    log.now = time.time() - 2
    log.user('Continue this private exact native owner operation.')
    rendered = fixture.render(session, *args, '--page', '--host-transcript', str(log.path))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    pending = binding._read_pending(binding.pending_path(fixture.runs, fixture.record_path().stem), ck._secret(create=False))
    log.now = time.time() - 1
    log.user(pending['paste_lines'][0])
    return rendered


def test_prepared_hook_round_cannot_infer_another_operations_global_claim(round_case, monkeypatch):
    runs, secret, session, page, _old = round_case
    pending = binding.render(runs, 'private', secret, action='add-class', scope='v4.15', page=page,
                             session=session, allow_short_reply=True)
    prompts = runs / 'prompts' / (hashlib.sha256(session.encode()).hexdigest() + '.jsonl')
    with prompts.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'session': session, 'prompt': binding.digest('Approve'), 'at': time.time(),
            'event_id': 'one-genuine-short-reply', 'permission_mode': 'bypassPermissions',
            'question': {'key': 'private', 'nonce': pending['nonce']}}) + '\n')
    original_claim = binding._claim_event
    def competing_claim(*args):
        original_claim(*args)  # A competing owner wins this global event claim.
        original_claim(*args)  # B's own claim therefore fails before its write.
    with monkeypatch.context() as patch:
        patch.setattr(binding, '_claim_event', competing_claim)
        with pytest.raises(binding.Refusal, match='code-used'):
            binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    before = binding.pending_path(runs, 'private').read_bytes()
    claims = _all_claims(runs)
    with pytest.raises(binding.Refusal, match='recovery-claim-owner-unavailable'):
        binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page,
                                       session=session, required_session=session)
    assert binding.pending_path(runs, 'private').read_bytes() == before and claims == _all_claims(runs)


def test_exact_typed_round_owns_its_unique_claim_without_a_second_consumption(typed_round_case):
    runs, secret, session, page, pending = typed_round_case
    consumed, _ = binding.consume(runs, 'private', secret, action='add-class', live_page=page, session=session)
    claims = _all_claims(runs)
    recovered, _ = binding.recover_consumed_round(runs, 'private', secret, action='add-class', live_page=page,
                                                 session=session, required_session=session)
    proof = recovered['capture']['transcript_proof']
    assert proof['key'] == 'private' and proof['round_nonce'] == pending['nonce']
    assert proof['page_sha256'] == hashlib.sha256(binding.canonical(page)).hexdigest()
    assert recovered['capture'] == consumed['capture'] and claims == _all_claims(runs)


@pytest.mark.parametrize('when', ['before_replace', 'after_replace'])
def test_real_typed_resume_retry_owns_claim_and_preserves_later_pause(minor, monkeypatch, when):
    assert minor.create().returncode == 0
    monkeypatch.chdir(minor.work)
    _typed_native_paste(monkeypatch, minor, CODEX_SESSION, '--action', 'resume')
    argv = ['record', 'resume', '--minor', 'v0.5', '--session', CODEX_SESSION]
    writer = ck._write_record
    def fail(path, record):
        if when == 'after_replace':
            writer(path, record)
        raise OSError('private typed resume save failure')
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', fail)
        with pytest.raises(OSError, match='private typed resume'):
            ck.main(argv)
    if when == 'after_replace':
        minor.paste(CODEX_SESSION, '--action', 'pause')
        assert ck.main(['record', 'pause', '--minor', 'v0.5', '--session', CODEX_SESSION]) == 0
    before = minor.record_path().read_bytes()
    claims = _all_claims(minor.runs)
    assert ck.main(argv) == 0
    _ctx, saved = ck.resolve_minor_controller(minor.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    assert len(saved['continuations']) == 1 and saved['continuations'][0]['capture']['origin'] == 'codex-host-transcript'
    if when == 'after_replace':
        assert minor.record_path().read_bytes() == before
    assert claims == _all_claims(minor.runs)
    if when == 'before_replace':
        minor.paste(CODEX_SESSION, '--action', 'pause')
        assert ck.main(['record', 'pause', '--minor', 'v0.5', '--session', CODEX_SESSION]) == 0
    paused = minor.record_path().read_bytes()
    assert ck.main(argv) == 0 and minor.record_path().read_bytes() == paused
    _typed_native_paste(monkeypatch, minor, CODEX_SESSION, '--action', 'resume')
    with monkeypatch.context() as patch:
        patch.setattr(ck, '_write_record', lambda *args: (_ for _ in ()).throw(OSError('private second typed resume')))
        with pytest.raises(OSError, match='private second typed resume'):
            ck.main(argv)
    assert minor.record_path().read_bytes() == paused
    newer_claims = _all_claims(minor.runs)
    assert ck.main(argv) == 0
    assert len(minor.record()['continuations']) == 2 and minor.record()['pause'] is None
    assert newer_claims == _all_claims(minor.runs)


@pytest.mark.parametrize('mode,reason', [('head-unknown', 'minor-execution-worker-head-unverifiable'),
    ('ancestry-unknown', 'minor-execution-worker-base-unverifiable'),
    ('unmet', 'minor-execution-worker-base-not-integrated'), ('met', None)])
def test_worker_observation_unknown_is_not_reported_as_nonintegration(tmp_path, monkeypatch, mode, reason):
    head = '' if mode == 'head-unknown' else 'a' * 40
    class Worker:
        git, root = 'git', tmp_path
        def _git_out(self, *args):
            return head
        def run(self, args):
            assert args == ['git', '-C', str(tmp_path), 'rev-parse', 'HEAD']
            return (-1, '') if mode == 'head-unknown' else (0, head + '\n')
    status = 'cannot-verify' if mode == 'ancestry-unknown' else 'unmet' if mode == 'unmet' else 'met'
    monkeypatch.setattr(cm, '_ancestor', lambda *args: status)
    if reason is None:
        assert cm._execution_worker_base(ck, object(), Worker(), 'b' * 40, 'c' * 40) == head
    else:
        with pytest.raises(ck.Malformed, match='^' + reason + '$'):
            cm._execution_worker_base(ck, object(), Worker(), 'b' * 40, 'c' * 40)
