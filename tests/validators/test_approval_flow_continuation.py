"""Causal approval-flow regressions using private temporary capture and run state."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import approval_binding as binding
import check_plan_completion as checker
import completion_gate as gate

SESSION = "01a14365-125e-7213-b5e9-9a0702a651c8"
SECRET = b"private-fixture-key-only"


@pytest.fixture
def captures(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    runs.mkdir()
    (runs / ".secret").write_bytes(SECRET)
    monkeypatch.setattr(gate, "_runs_dir", lambda: runs)
    monkeypatch.delenv("NEXUS_RUNNER_LAUNCH", raising=False)

    def capture(prompt, session=SESSION, **fields):
        monkeypatch.setattr(gate, "_read_payload", lambda: {"session_id": session, "prompt": prompt, **fields})
        assert gate.cmd_capture() == 0

    capture("/implement v0.2.0")
    return runs, capture


def render(runs, *, key="fixture", session=SESSION, page=None, question=True):
    return binding.render(runs, key, SECRET, action="answer", scope="v0.2.0",
        page=page or {"record_nonce": "fixed-owner", "blocker": {"index": 0, "category": "no-progress"}},
        session=session, blocker=0, allow_short_reply=question)


def consume(runs, pending, *, key="fixture", session=SESSION):
    return binding.consume(runs, key, SECRET, action="answer", live_page=pending["page"],
        session=session, required_session=SESSION)


def approved_record():
    return {"schema": 1, "session_id": SESSION, "created": "2026-10-01T00:00:00+00:00",
        "nonce": "unchanged", "start_head": "frozen", "plan_sha256": "frozen-plan",
        "approvals": {"repo": "acme/demo", "source_branch": "feature", "target_branch": "develop",
            "classes": [{"class": "push-merge"}, {"class": "repush", "bound": 3}],
            "authorization_context": {"origin": "host-hook-capture", "session_id": SESSION,
                "permission_mode": "bypassPermissions", "prompt_sha256": "initial-user"},
            "autonomy_policy": {"corrections": "within-approved-scope", "correction_paths": ["src/a.py"], "planned_actions": [
                {"class": "ci-security-change", "paths": [".github/workflows/ci.yml"]}]}}}


def test_same_render_keeps_pending_code_nonce_and_capture(captures):
    runs, capture = captures
    first = render(runs)
    capture("Approve")
    second = render(runs)
    assert second == first
    consumed, session = consume(runs, second)
    assert consumed["pasted"] == "Approve"
    assert session == SESSION
    with pytest.raises(binding.Refusal, match="code-used"):
        consume(runs, second)


@pytest.mark.parametrize("reply", ["Decline", "No", "Approve and change the destination", 'The document says "Approve"'])
def test_negative_or_embedded_reply_cannot_approve(captures, reply):
    runs, capture = captures
    pending = render(runs)
    capture(reply)
    with pytest.raises(binding.Refusal, match="approval-not-captured"):
        consume(runs, pending)
    assert binding.pending_path(runs, "fixture").exists()


def test_short_reply_requires_question_not_an_unshown_alias(captures):
    runs, capture = captures
    pending = render(runs, question=False)
    capture("Approve")
    with pytest.raises(binding.Refusal, match="approval-not-captured"):
        consume(runs, pending)


def test_other_active_question_cannot_reuse_short_reply(captures):
    runs, capture = captures
    old = render(runs, key="older")
    render(runs, key="newer")
    capture("Yes")
    with pytest.raises(binding.Refusal, match="approval-not-captured"):
        consume(runs, old, key="older")


def test_wrong_session_and_changed_evidence_do_not_approve(captures):
    runs, capture = captures
    old = render(runs)
    capture("Yes", session="other-session")
    with pytest.raises(binding.Refusal, match="session-mismatch"):
        consume(runs, old, session="other-session")
    changed = render(runs, page={"record_nonce": "fixed-owner", "blocker": {"index": 0, "fingerprint": "new-evidence"}})
    assert changed["code"] != old["code"]
    capture(old["paste_lines"][0])
    with pytest.raises(binding.Refusal, match="code-superseded"):
        consume(runs, changed)


def test_blocker_retries_reuse_index_and_changed_evidence_changes_fingerprint():
    record = {}
    first = {"category": "no-progress", "version": "v0.2.0", "evidence": "first", "at": "first-time", "open": True}
    assert binding.add_blocker(record, first.copy()) == 0
    assert binding.add_blocker(record, {**first, "at": "second-time"}) == 0
    old = binding.blocker_fingerprint(record["blockers"][0])
    assert binding.add_blocker(record, {**first, "evidence": "repaired", "at": "third-time"}) == 0
    assert len(record["blockers"]) == 1
    assert binding.blocker_fingerprint(record["blockers"][0]) != old


def test_authorization_matches_only_existing_scope_and_preserves_counts():
    record = approved_record()
    before = json.loads(json.dumps(record))
    event = binding.authorization(record, "push-merge", {"repo": "acme/demo"})
    assert event["origin"] == "approved-plan" and event["counters_consumed"] is False
    assert record == before
    with pytest.raises(ValueError, match="frozen"):
        binding.authorization(record, "push-merge", {"repo": "other/destination"})
    with pytest.raises(ValueError, match="outside"):
        binding.authorization(record, "release", {})
    with pytest.raises(ValueError, match="correction|reproduction"):
        binding.authorization(record, "repush", {})
    assert binding.authorization(record, "ci-security-change", {"paths": [".github/workflows/ci.yml"]})
    with pytest.raises(ValueError, match="paths"):
        binding.authorization(record, "ci-security-change", {"paths": ["secrets.env"]})


def test_policy_adoption_uses_real_capture_not_generated_renderer_text(captures):
    runs, capture = captures
    record = approved_record()
    record["approvals"].pop("authorization_context")
    original = {key: record[key] for key in ("nonce", "start_head", "plan_sha256")}
    classes = list(record["approvals"]["classes"])
    instruction = "Continue the existing approved plan using full access and the reviewed policy."
    capture(instruction, permission_mode="bypassPermissions")
    policy = {"corrections": "within-approved-scope", "planned_actions": []}
    binding.adopt_policy(runs, record, instruction, policy)
    assert {key: record[key] for key in original} == original
    assert record["approvals"]["classes"] == classes
    assert record["approvals"]["policy_adoptions"][0]["origin"] == "captured-user-instruction"
    binding.adopt_policy(runs, record, instruction, policy)  # exact retry remains idempotent
    with pytest.raises(ValueError, match="latest genuine"):
        binding.adopt_policy(runs, record, "agent-generated replacement", policy)


@pytest.mark.parametrize("fields", [{}, {"permission_mode": "default"}, {"tool_input": {"permission_mode": "bypassPermissions"}}])
def test_absent_manual_or_nested_permission_never_grants_policy(captures, fields):
    runs, capture = captures
    capture("Continue this plan", **fields)
    with pytest.raises(ValueError, match="permission evidence"):
        binding.adopt_policy(runs, approved_record(), "Continue this plan", {})


def test_resolution_needs_fresh_successful_actual_output(tmp_path):
    record = approved_record()
    entry = {"category": "unreproducible-red-check", "evidence": "failure", "open": True, "at": time.time() - 2,
             "request": {"verification": {"command": ["python", "probe.py"]}}}
    record["blockers"] = [entry]
    condition = binding.blocker_fingerprint(entry)
    output = tmp_path / "actual-probe.log"
    output.write_text("unchanged: current file\n", encoding="utf-8")
    receipt = tmp_path / "repair.json"
    proof = {"condition": condition, "exit_code": 0, "command": ["python", "probe.py"],
        "completed_at": time.time(), "output_path": str(output), "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    receipt.write_text(json.dumps(proof), encoding="utf-8")
    result = binding.resolution(record, 0, condition, receipt)
    assert result["origin"] == "agent-verification-receipt"
    assert result["native_predicates_changed"] is False
    assert entry["open"] is True  # the pure verifier does not mutate a blocker or any predicate
    for field, value in [("exit_code", 1), ("completed_at", entry["at"] - 10), ("output_sha256", "wrong"), ("command", ["python", "-c", "print(1)"])]:
        receipt.write_text(json.dumps({**proof, field: value}), encoding="utf-8")
        with pytest.raises(ValueError):
            binding.resolution(record, 0, condition, receipt)


def test_resolution_never_treats_authorization_as_failed_test_success(tmp_path):
    record = approved_record()
    record["blockers"] = [{"category": "record-tampered", "open": True, "evidence": "signature", "at": time.time()}]
    with pytest.raises(ValueError, match="manual"):
        binding.resolution(record, 0, binding.blocker_fingerprint(record["blockers"][0]), None)



def test_current_mode_downgrade_unknown_mode_and_env_spoof_are_conservative(captures, monkeypatch):
    runs, capture = captures
    record = approved_record()
    capture('Work in full access', permission_mode='bypassPermissions')
    current = binding.current_host_context(runs, record, set())
    assert binding.authorization(record, 'push-merge', {}, current)
    capture('Now require manual decisions', permission_mode='default')
    with pytest.raises(ValueError, match='manual'):
        binding.current_host_context(runs, record, set())
    monkeypatch.setenv('NEXUS_PERMISSION_MODE', 'bypassPermissions')
    capture('An unknown host mode', tool_input={'permission_mode': 'bypassPermissions'})
    with pytest.raises(ValueError, match='unavailable'):
        binding.current_host_context(runs, record, set())


def test_malformed_request_paths_and_surfaces_fail_visibly():
    record = approved_record()
    for paths in [[{}], [None], 'src/file.py']:
        with pytest.raises(ValueError, match='paths'):
            binding.authorization(record, 'ci-security-change', {'paths': paths})
    for surface in ['ask-first:', 'ask-first:../escape', 'ask-first:two words']:
        with pytest.raises(ValueError, match='class'):
            binding.validate_policy({'planned_actions': [{'class': surface, 'paths': ['src/a.py']}]})


def test_correction_policy_removes_duplicate_consent_without_consuming_budget():
    record = approved_record()
    classes = list(record['approvals']['classes'])
    request = {'paths': ['src/a.py'], 'locally_reproduced': True, 'verified': True}
    for _ in range(5):
        result = binding.authorization(record, 'repush', request)
        assert result['bounds'] == [3]
        assert result['consent_bound'] is None
        assert result['counters_consumed'] is False
        assert result['verification_and_spend_limits_unchanged'] is True
    assert record['approvals']['classes'] == classes
    with pytest.raises(ValueError, match='scope'):
        binding.authorization(record, 'repush', {**request, 'paths': ['outside.py']})


def test_actual_link_escape_is_refused(tmp_path):
    root, outside = tmp_path / 'repo', tmp_path / 'outside'
    root.mkdir()
    outside.mkdir()
    link = root / 'linked'
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        if sys.platform != 'win32':
            pytest.skip('host cannot create a directory link')
        result = subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)],
                                capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
    with pytest.raises(ValueError, match='escapes'):
        checker._validate_scoped_paths(root, ['linked/file.py'])
    with pytest.raises(ValueError, match='escapes'):
        checker._validate_policy_paths(root, {'planned_actions': [
            {'class': 'ci-security-change', 'paths': ['linked/file.py']}]})


def test_existing_codex_transcript_adapter_corroborates_capture_and_current_mode(captures, tmp_path, monkeypatch):
    import datetime
    runs, capture = captures
    home = tmp_path / 'home'
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    cwd = tmp_path / 'repo'
    cwd.mkdir()
    instruction = 'Use the reviewed policy for the existing approved run.'
    capture(instruction)
    event = binding.capture_events(runs, SESSION)[-1]
    log = home / '.codex' / 'sessions' / '2026' / '10' / '19' / f'rollout-date-{SESSION}.jsonl'
    log.parent.mkdir(parents=True)
    at = datetime.datetime.fromtimestamp(event['at'], datetime.UTC).isoformat()
    rows = [
        {'type': 'session_meta', 'payload': {'id': SESSION, 'originator': 'codex_vscode', 'source': 'vscode'}},
        {'type': 'turn_context', 'payload': {'approval_policy': 'never', 'sandbox_policy': {'type': 'danger-full-access'}, 'cwd': str(cwd)}},
        {'type': 'event_msg', 'timestamp': at, 'payload': {'type': 'user_message', 'message': instruction}},
    ]
    log.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    record = approved_record()
    binding.adopt_policy(runs, record, instruction, {}, log, {str(cwd.resolve())})
    assert record['approvals']['authorization_context']['origin'] == 'codex-host-transcript'
    assert binding.current_host_context(runs, record, {str(cwd.resolve())})['permission_mode'] == 'bypassPermissions'
    with log.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({'type': 'turn_context', 'payload': {'approval_policy': 'on-request',
            'sandbox_policy': {'type': 'workspace-write'}, 'cwd': str(cwd)}}) + '\n')
    with pytest.raises(ValueError, match='unavailable'):
        binding.current_host_context(runs, record, {str(cwd.resolve())})
    forged = tmp_path / f'rollout-date-{SESSION}.jsonl'
    forged.write_text(log.read_text(encoding='utf-8'), encoding='utf-8')
    with pytest.raises(ValueError, match='canonical'):
        binding.codex_transcript_context(forged, SESSION, event, {str(cwd.resolve())})


def test_policy_adoption_preserves_legacy_signature_algorithm(captures):
    import hmac
    runs, capture = captures
    record = approved_record()
    capture('Adopt this narrow approved-plan policy', permission_mode='bypassPermissions')
    binding.adopt_policy(runs, record, 'Adopt this narrow approved-plan policy', {})
    legacy_fields = ('approvals', 'plan_sha256', 'session_id', 'repo', 'deferrable_gap_types',
                     'start_head', 'nonce', 'created')
    legacy_payload = {key: record.get(key) for key in legacy_fields}
    expected = hmac.new(SECRET, checker._canonical(legacy_payload), hashlib.sha256).hexdigest()
    assert checker._sign(record, SECRET) == expected
    assert {entry['class'] for entry in record['approvals']['classes']} == {'push-merge', 'repush'}


def test_real_cli_capture_create_authorize_decline_answer_and_mode_change(tmp_path, monkeypatch):
    from tests.validators.test_approval_binding import _fixture
    from tests.validators.test_check_plan_completion import PLAN_REL
    from tests.validators.test_check_plan_completion import SESSION as CLI_SESSION
    empty = tmp_path / 'empty.gitconfig'
    empty.write_text('', encoding='utf-8')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', str(empty))
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    fx = _fixture(tmp_path)
    core = Path(gate.__file__)

    def capture(prompt, mode='bypassPermissions'):
        result = subprocess.run([sys.executable, str(core), 'capture'],
            input=json.dumps({'session_id': CLI_SESSION, 'prompt': prompt, 'permission_mode': mode}),
            text=True, capture_output=True, env=fx.env, check=False)
        assert result.returncode == 0, result.stderr

    approvals = fx.approvals()
    spec = json.loads(approvals.read_text(encoding='utf-8'))
    spec['autonomy'] = {'corrections': 'within-approved-scope', 'correction_paths': ['src/a.py'],
        'planned_actions': [{'class': 'ci-security-change', 'paths': ['.github/workflows/ci.yml']}]}
    approvals.write_text(json.dumps(spec), encoding='utf-8')
    capture('/implement v0.2.0')
    args = ('record', 'render', PLAN_REL, '--session', CLI_SESSION, '--approvals', str(approvals), '--question')
    first = fx.run(*args)
    assert first.returncode == 0, first.stdout + first.stderr
    question = json.loads(first.stdout)
    assert question['capture']['direct_question_callback_supported'] is False
    assert json.loads(fx.run(*args).stdout)['challenge'] == question['challenge']
    capture('Approve')
    created = fx.run('record', 'create', PLAN_REL, '--session', CLI_SESSION, '--approvals', str(approvals))
    assert created.returncode == 0, created.stdout + created.stderr
    authorized = fx.run('record', 'authorize', PLAN_REL, '--session', CLI_SESSION, '--approval-class', 'push-merge')
    assert authorized.returncode == 0, authorized.stdout + authorized.stderr
    assert 'approved-plan' in authorized.stdout
    blocked = ('record', 'block', PLAN_REL, '--session', CLI_SESSION, '--category', 'no-progress',
               '--evidence', 'A real progress issue', '--purpose', 'Continue the scoped build', '--why', 'The dependency is now available')
    assert fx.run(*blocked).returncode == 3
    assert fx.run(*blocked).returncode == 3
    record = json.loads(fx.record_path().read_text(encoding='utf-8'))
    assert len(record['blockers']) == 1
    answer_args = ('record', 'render', PLAN_REL, '--session', CLI_SESSION, '--action', 'answer', '--blocker', '0', '--question')
    answer = fx.run(*answer_args)
    assert answer.returncode == 0, answer.stdout + answer.stderr
    assert 'Continue the scoped build' in json.loads(answer.stdout)['review_page']
    capture('Decline')
    consume_args = ('record', 'answer', PLAN_REL, '--session', CLI_SESSION, '--blocker', '0')
    assert fx.run(*consume_args).returncode == 3
    capture('Approve')
    assert fx.run(*consume_args).returncode == 0
    assert fx.run(*consume_args).returncode != 0
    assert fx.check().returncode != 0  # an authorization or answer cannot complete unfinished implementation
    capture('Now use manual approval mode', mode='default')
    assert fx.run('record', 'authorize', PLAN_REL, '--session', CLI_SESSION, '--approval-class', 'push-merge').returncode == 3


def test_repeated_genuine_exact_paste_uses_one_fresh_event(captures):
    runs, capture = captures
    pending = render(runs, question=False)
    capture(pending['paste_lines'][0])
    assert render(runs, question=False)['nonce'] == pending['nonce']
    capture(pending['paste_lines'][0])
    assert consume(runs, pending)[0]['pasted'] == pending['paste_lines'][0]
    with pytest.raises(binding.Refusal, match='code-used'):
        consume(runs, pending)


def test_changed_purpose_or_reason_invalidates_stable_blocker_challenge(captures):
    runs, _capture = captures
    record = {}
    entry = {'category': 'ci-security-change', 'approval_class': 'ci-security-change',
             'request': {'paths': ['ci.yml']}, 'evidence': 'same', 'purpose': 'First change',
             'why': 'First reason', 'open': True, 'at': time.time()}
    binding.add_blocker(record, entry.copy())
    old = binding.blocker_fingerprint(record['blockers'][0])
    pending = render(runs, page={'fingerprint': old})
    for field in ('purpose', 'why'):
        binding.add_blocker(record, {**entry, field: 'Updated meaning', 'at': time.time()})
        assert binding.blocker_fingerprint(record['blockers'][0]) != old
        assert render(runs, page={'fingerprint': binding.blocker_fingerprint(record['blockers'][0])})['nonce'] != pending['nonce']


def test_native_user_edit_resolution_checks_real_guard_state(tmp_path, monkeypatch):
    import argparse
    import runpy
    import shutil
    from types import SimpleNamespace
    root, home = tmp_path / 'repo', tmp_path / 'home'
    root.mkdir()
    target = root / 'file.md'
    target.write_text('current user bytes', encoding='utf-8')
    installed = home / '.agents/skills/user-edit-preservation/scripts/edit_guard.py'
    installed.parent.mkdir(parents=True)
    source = Path(__file__).resolve().parents[2] / 'catalog/skills/workflow/user-edit-preservation/scripts/edit_guard.py'
    shutil.copyfile(source, installed)
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    monkeypatch.delenv('NEXUS_EDIT_GUARD_DIR', raising=False)
    record = approved_record()
    record['approvals']['autonomy_policy']['planned_actions'].append({'class': 'ask-first:user-edit-baseline', 'paths': ['file.md']})
    context = record['approvals']['authorization_context']
    ctx = SimpleNamespace(root=root, _git_out=lambda *args: '')
    entry = {'category': 'user-edit-guard', 'evidence': 'real mismatch', 'request': {}, 'open': True, 'at': time.time()}
    with pytest.raises(ValueError, match='unresolved'):
        checker._native_user_edit_probe(ctx, record, entry, context)
    guard = runpy.run_path(str(installed))
    args = argparse.Namespace(path=str(target), source='read', session=SESSION)
    assert guard['cmd_record'](args, guard['store_dir']()) == 0
    result = checker._native_user_edit_probe(ctx, record, entry, context)
    assert result['origin'] == 'native-user-edit-check'
    assert result['checks'] == [{'path': 'file.md', 'exit_code': 0}]
    target.write_text('a later real user edit', encoding='utf-8')
    with pytest.raises(ValueError, match='unresolved'):
        checker._native_user_edit_probe(ctx, record, entry, context)
