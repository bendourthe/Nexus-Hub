"""Causal approval-flow regressions using private temporary capture and run state."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

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

    # Whole-second seed models a coarse host clock; clock reads order fixture events.
    now = [float(int(time.time()))]

    def clock():
        now[0] += 1.0
        return now[0]

    monkeypatch.setattr(binding, "_clock", clock)
    monkeypatch.setattr(gate, "time", SimpleNamespace(time=clock))

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


def test_same_render_keeps_pending_code_nonce_and_capture(captures, monkeypatch):
    runs, capture = captures
    initial = binding.capture_events(runs, SESSION)[-1]
    now = [initial["at"] + 1.0]
    monkeypatch.setattr(binding, "_clock", lambda: now[0])
    monkeypatch.setattr(gate, "time", SimpleNamespace(time=lambda: now[0]))
    first = render(runs)
    now[0] += 1.0
    capture("Approve")
    reply = binding.capture_events(runs, SESSION)[-1]
    assert initial["at"] < first["rendered_at"] < reply["at"]
    assert reply["question"] == {"key": "fixture", "nonce": first["nonce"]}
    now[0] += 1.0
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
    with pytest.raises(ValueError, match="genuine whole"):
        binding.adopt_policy(runs, record, "agent-generated replacement", policy)


def test_policy_adoption_selects_unused_earlier_instruction_and_preserves_authority(captures):
    runs, capture = captures
    record = approved_record()
    before = json.loads(json.dumps(record))
    instruction = "Continue the approved full goal, including its scoped CI compatibility repair."
    capture(instruction, permission_mode="bypassPermissions")
    selected = binding.capture_events(runs, SESSION)[-1]
    capture("Continue the same work.", permission_mode="bypassPermissions")
    latest = binding.capture_events(runs, SESSION)[-1]
    binding.adopt_policy(runs, record, instruction, {})
    adoption = record["approvals"]["policy_adoptions"][-1]
    assert adoption["event_id"] == selected["event_id"]
    assert adoption["current_host_context"]["prompt_sha256"] == latest["prompt"]
    assert not binding.event_available(runs, SESSION, selected)
    assert binding.event_available(runs, SESSION, latest)
    assert {key: value for key, value in record.items() if key != "approvals"} == {
        key: value for key, value in before.items() if key != "approvals"
    }
    for key in ("classes", "repo", "source_branch", "target_branch"):
        assert record["approvals"][key] == before["approvals"][key]


@pytest.mark.parametrize("other_record", [False, True])
def test_policy_adoption_cannot_reuse_consumed_instruction_for_changed_or_other_policy(captures, other_record):
    runs, capture = captures
    instruction = "Apply the reviewed same-goal policy."
    capture(instruction, permission_mode="bypassPermissions")
    record = approved_record()
    binding.adopt_policy(runs, record, instruction, {})
    target = approved_record() if other_record else record
    if other_record:
        target["nonce"] = "another-record"
    before = json.loads(json.dumps(target))
    policy = {} if other_record else {"corrections": "within-approved-scope"}
    with pytest.raises(binding.Refusal) as refused:
        binding.adopt_policy(runs, target, instruction, policy)
    assert refused.value.reason == "code-used"
    assert target == before


def test_identical_policy_retry_rechecks_latest_mode_before_return(captures):
    runs, capture = captures
    instruction = "Use this approved policy."
    capture(instruction, permission_mode="bypassPermissions")
    record = approved_record()
    binding.adopt_policy(runs, record, instruction, {})
    capture("Continue.", permission_mode="bypassPermissions")
    before = json.loads(json.dumps(record))
    binding.adopt_policy(runs, record, instruction, {})
    assert record == before
    capture("Require manual decisions now.", permission_mode="default")
    with pytest.raises(ValueError, match="manual"):
        binding.adopt_policy(runs, record, instruction, {})
    assert record == before


@pytest.mark.parametrize("fields", [
    {"permission_mode": "default"}, {}, {"permission_mode": "unknown"},
    {"tool_input": {"permission_mode": "bypassPermissions"}},
])
def test_earlier_instruction_does_not_borrow_mode_after_followup(captures, fields):
    runs, capture = captures
    instruction = "Continue the approved goal."
    capture(instruction, permission_mode="bypassPermissions")
    selected = binding.capture_events(runs, SESSION)[-1]
    capture("Latest actual host context.", **fields)
    record = approved_record()
    before = json.loads(json.dumps(record))
    with pytest.raises(ValueError, match="manual|unavailable"):
        binding.adopt_policy(runs, record, instruction, {})
    assert record == before
    assert binding.event_available(runs, SESSION, selected)


def test_policy_lookup_refuses_precreation_ambiguous_or_spoofed_instruction(captures):
    runs, capture = captures
    instruction = "Apply this scoped approved goal."
    capture(instruction, permission_mode="bypassPermissions")
    first = binding.capture_events(runs, SESSION)[-1]
    record = approved_record()
    record["created"] = first["at"] + 1
    before = json.loads(json.dumps(record))
    with pytest.raises(ValueError, match="after run creation"):
        binding.adopt_policy(runs, record, instruction, {})
    assert record == before
    record = approved_record()
    capture(instruction, permission_mode="bypassPermissions")
    before = json.loads(json.dumps(record))
    with pytest.raises(ValueError, match="multiple eligible"):
        binding.adopt_policy(runs, record, instruction, {})
    with pytest.raises(ValueError, match="genuine whole"):
        binding.adopt_policy(runs, record, "agent-supplied replacement", {})
    assert record == before
    assert binding.event_available(runs, SESSION, first)


def test_policy_lookup_does_not_repurpose_manual_instruction(captures):
    runs, capture = captures
    instruction = "Now require manual decisions."
    capture(instruction, permission_mode="default")
    selected = binding.capture_events(runs, SESSION)[-1]
    capture("Later work.", permission_mode="bypassPermissions")
    record = approved_record()
    before = json.loads(json.dumps(record))
    with pytest.raises(ValueError, match="permission evidence"):
        binding.adopt_policy(runs, record, instruction, {})
    assert record == before
    assert binding.event_available(runs, SESSION, selected)


def test_policy_lookup_respects_newer_sealed_current_context(captures):
    runs, capture = captures
    instruction = "Continue this approved goal."
    capture(instruction, permission_mode="bypassPermissions")
    selected = binding.capture_events(runs, SESSION)[-1]
    observed = {"origin": "host-hook-capture", "session_id": SESSION,
                "permission_mode": "default", "at": selected["at"] + 1}
    observed["mac"] = binding._seal(SECRET, observed)
    path = runs / "host-context" / f"{hashlib.sha256(SESSION.encode()).hexdigest()}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(observed), encoding="utf-8")
    record = approved_record()
    before = json.loads(json.dumps(record))
    with pytest.raises(ValueError, match="manual"):
        binding.adopt_policy(runs, record, instruction, {})
    assert record == before
    assert binding.event_available(runs, SESSION, selected)


@pytest.mark.parametrize("same_policy", [False, True])
def test_consumed_historical_adoption_cannot_report_success_after_another_instruction(captures, same_policy):
    runs, capture = captures
    record = approved_record()
    first_instruction = "Instruction A: continue this approved goal."
    second_instruction = "Instruction B: continue this same approved goal."
    first_policy = {}
    second_policy = {} if same_policy else {"corrections": "within-approved-scope"}
    capture(first_instruction, permission_mode="bypassPermissions")
    first_event = binding.capture_events(runs, SESSION)[-1]
    binding.adopt_policy(runs, record, first_instruction, first_policy)
    capture(second_instruction, permission_mode="bypassPermissions")
    second_event = binding.capture_events(runs, SESSION)[-1]
    binding.adopt_policy(runs, record, second_instruction, second_policy)
    before = json.loads(json.dumps(record))
    consumed_before = sorted(path.name for path in (runs / "consumed-prompts").iterdir())
    with pytest.raises(binding.Refusal) as refused:
        binding.adopt_policy(runs, record, first_instruction, first_policy)
    assert refused.value.reason == "code-used"
    assert record == before
    assert record["approvals"]["autonomy_policy"] == binding.validate_policy(second_policy)
    assert record["approvals"]["policy_adoptions"][-1]["event_id"] == second_event["event_id"]
    assert not binding.event_available(runs, SESSION, first_event)
    assert not binding.event_available(runs, SESSION, second_event)
    assert sorted(path.name for path in (runs / "consumed-prompts").iterdir()) == consumed_before
    binding.adopt_policy(runs, record, second_instruction, second_policy)
    assert record == before


def test_consumed_retry_requires_current_policy_not_only_matching_adoption(captures):
    runs, capture = captures
    instruction = "Continue the approved policy."
    capture(instruction, permission_mode="bypassPermissions")
    record = approved_record()
    binding.adopt_policy(runs, record, instruction, {})
    # An inconsistent current policy must not be masked by an older matching receipt.
    record["approvals"]["autonomy_policy"] = binding.validate_policy({"corrections": "within-approved-scope"})
    before = json.loads(json.dumps(record))
    with pytest.raises(binding.Refusal) as refused:
        binding.adopt_policy(runs, record, instruction, {})
    assert refused.value.reason == "code-used"
    assert record == before


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
    followup = 'Continue the same approved work.'
    capture(followup)
    followup_event = binding.capture_events(runs, SESSION)[-1]
    log = home / '.codex' / 'sessions' / '2026' / '10' / '19' / f'rollout-date-{SESSION}.jsonl'
    log.parent.mkdir(parents=True)
    at = datetime.datetime.fromtimestamp(event['at'], datetime.UTC).isoformat()
    rows = [
        {'type': 'session_meta', 'payload': {'id': SESSION, 'originator': 'codex_vscode', 'source': 'vscode'}},
        {'type': 'turn_context', 'payload': {'approval_policy': 'never', 'sandbox_policy': {'type': 'danger-full-access'}, 'cwd': str(cwd)}},
        {'type': 'event_msg', 'timestamp': at, 'payload': {'type': 'user_message', 'message': instruction}},
        {'type': 'turn_context', 'payload': {'approval_policy': 'never',
            'sandbox_policy': {'type': 'danger-full-access'}, 'cwd': str(cwd)}},
        {'type': 'event_msg',
            'timestamp': datetime.datetime.fromtimestamp(followup_event['at'], datetime.UTC).isoformat(),
            'payload': {'type': 'user_message', 'message': followup}},
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

    # Model the old hook's exact commandless entry, retaining the genuine signed run.
    path = fx.record_path()
    before = json.loads(path.read_text(encoding='utf-8'))
    legacy = {'at': time.time(), 'category': 'no-progress', 'open': True,
        'evidence': 'progress score unchanged over 3 refusals: task.T001 member.gate'}
    before['blockers'].append(legacy)
    path.write_text(json.dumps(before), encoding='utf-8')
    index = len(before['blockers']) - 1
    fingerprint = binding.blocker_fingerprint(legacy)
    capture('Continue')
    resolve_args = ('record', 'resolve', PLAN_REL, '--session', CLI_SESSION,
        '--blocker', str(index), '--fingerprint', fingerprint)
    resolved = fx.run(*resolve_args)
    assert resolved.returncode == 0, resolved.stdout + resolved.stderr
    after = json.loads(path.read_text(encoding='utf-8'))
    assert after['blockers'][:-1] == before['blockers'][:-1]
    assert after['blockers'][-1]['open'] is False
    audit = after['approvals']['resolutions'][-1]
    assert audit['origin'] == 'existing-approved-plan-user-continuation'
    assert audit['fingerprint'] == fingerprint
    assert audit['technical_repair_claimed'] is False
    for key in ('nonce', 'start_head', 'plan_sha256', 'session_id', 'created'):
        assert after[key] == before[key]
    for key in ('classes', 'autonomy_policy', 'authorization_context'):
        assert after['approvals'][key] == before['approvals'][key]
    assert after['approvals_hmac'] == checker._sign(after, (fx.runs / '.secret').read_bytes())
    assert fx.run(*resolve_args).returncode == 3
    assert fx.check().returncode != 0  # Continuation cannot complete unfinished implementation.


def test_repeated_genuine_exact_paste_uses_one_fresh_event(captures):
    runs, capture = captures
    initial = binding.capture_events(runs, SESSION)[-1]
    pending = render(runs, question=False)
    capture(pending['paste_lines'][0])
    first_reply = binding.capture_events(runs, SESSION)[-1]
    assert render(runs, question=False)['nonce'] == pending['nonce']
    capture(pending['paste_lines'][0])
    second_reply = binding.capture_events(runs, SESSION)[-1]
    assert initial['at'] < pending['rendered_at'] < first_reply['at'] < second_reply['at']
    assert first_reply['event_id'] != second_reply['event_id']
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



def test_historical_corroboration_never_authorizes_historical_current_cwd(captures, tmp_path, monkeypatch):
    import datetime
    runs, capture = captures
    home = tmp_path / 'fixture-home'
    old = tmp_path / 'removed-controller'
    current = tmp_path / 'permanent-controller'
    current.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    capture('Continue the already approved full minor')
    event = binding.capture_events(runs, SESSION)[-1]
    log = home / '.codex/sessions/2026/10/19' / f'rollout-fixture-{SESSION}.jsonl'
    log.parent.mkdir(parents=True)
    timestamp = datetime.datetime.fromtimestamp(event['at'], datetime.timezone.utc).isoformat()
    full = {'approval_policy': 'never', 'sandbox_policy': {'type': 'danger-full-access'}}
    rows = [
        {'type': 'session_meta', 'payload': {'id': SESSION, 'originator': 'codex_vscode', 'source': 'vscode'}},
        {'type': 'turn_context', 'payload': {**full, 'cwd': str(old)}},
        {'type': 'event_msg', 'timestamp': timestamp, 'payload': {'type': 'user_message', 'message': 'Continue the already approved full minor'}},
        {'type': 'turn_context', 'payload': {**full, 'cwd': str(current)}},
    ]
    log.write_text('\n'.join(json.dumps(row) for row in rows) + '\n', encoding='utf-8')
    live, history = {str(current.resolve())}, {str(old.resolve())}
    assert binding.codex_transcript_context(log, SESSION, event, live, historical_cwds=history)['permission_mode'] == 'bypassPermissions'
    with pytest.raises(ValueError):
        binding.codex_transcript_context(log, SESSION, event, live)
    for context in ({**full, 'cwd': str(old)}, {'approval_policy': 'on-request', 'sandbox_policy': {'type': 'danger-full-access'}, 'cwd': str(current)}):
        with log.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps({'type': 'turn_context', 'payload': context}) + '\n')
        result = binding.codex_transcript_context(log, SESSION, event, live, historical_cwds=history)
        assert result['permission_mode'] == 'manual'
        assert not binding.full_access_authorization({'session_id': SESSION}, result)


def _legacy_hook_record():
    record = approved_record()
    record['blockers'] = [{'at': binding._clock(), 'category': 'no-progress',
        'evidence': 'progress score unchanged over 3 refusals: task.T001 member.gate', 'open': True}]
    return record


def _continue_legacy(runs, record, index=0, fingerprint=None, roots=None):
    return binding.user_continuation(runs, record, index,
        fingerprint or binding.blocker_fingerprint(record['blockers'][index]),
        roots or {str(runs.parent.resolve())})


def test_legacy_hook_continue_resumes_authority_without_claiming_repair(captures):
    runs, capture = captures
    record = _legacy_hook_record()
    before = json.loads(json.dumps(record))
    capture(' \tContinue\n ', permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    result = _continue_legacy(runs, record)
    assert result['origin'] == 'existing-approved-plan-user-continuation'
    assert result['event_id'] == event['event_id']
    assert result['prompt_sha256'] == binding.digest('Continue')
    assert result['fingerprint'] == binding.blocker_fingerprint(record['blockers'][0])
    assert result['policy'] == before['approvals']['autonomy_policy']
    assert result['current_host_context']['permission_mode'] == 'bypassPermissions'
    assert result['native_predicates_changed'] is False
    assert result['technical_repair_claimed'] is False
    assert record == before  # Only the verified native caller may close and sign the target.
    assert not binding.event_available(runs, SESSION, event)
    with pytest.raises(binding.Refusal, match='code-used'):
        _continue_legacy(runs, json.loads(json.dumps(before)))
    other = json.loads(json.dumps(before))
    other['nonce'] = 'another-record'
    with pytest.raises(binding.Refusal, match='code-used'):
        _continue_legacy(runs, other)


@pytest.mark.parametrize('reply', ['Continue.', 'Yes', 'Approve', 'Decline', 'Do not Continue', '"Continue"'])
def test_legacy_hook_continue_requires_exact_latest_whole_reply(captures, reply):
    runs, capture = captures
    record = _legacy_hook_record()
    capture(reply, permission_mode='bypassPermissions')
    with pytest.raises(ValueError, match='latest whole user capture'):
        _continue_legacy(runs, record)


@pytest.mark.parametrize('failure', ['pause', 'second-blocker', 'closed', 'generic', 'probe',
    'modern', 'policy', 'session', 'stale-fingerprint', 'before-blocker', 'future', 'duplicate-id', 'duplicate-legacy'])
def test_legacy_hook_continue_refuses_unrelated_or_stale_conditions(captures, failure):
    runs, capture = captures
    record = _legacy_hook_record()
    capture('Continue', permission_mode='bypassPermissions')
    fingerprint = binding.blocker_fingerprint(record['blockers'][0])
    if failure == 'pause':
        record['pause'] = {'at': record['created']}
    elif failure == 'second-blocker':
        record['blockers'].append({'category': 'user-edit-guard', 'open': True})
    elif failure == 'closed':
        record['blockers'][0]['open'] = False
    elif failure == 'generic':
        record['blockers'][0]['evidence'] = 'A dependency is missing'
    elif failure == 'probe':
        record['blockers'][0]['request'] = {'verification': {'command': ['python', 'real-check.py']}}
    elif failure == 'modern':
        record['blockers'][0]['purpose'] = 'A separate concrete decision'
    elif failure == 'policy':
        record['approvals']['autonomy_policy'] = {}
    elif failure == 'session':
        record['session_id'] = 'another-session'
    elif failure == 'stale-fingerprint':
        fingerprint = '0' * 64
    elif failure == 'before-blocker':
        record['blockers'][0]['at'] = binding._clock()
    else:
        # Deliberately corrupt only private fixture capture data for refusal controls.
        path = runs / 'prompts' / f'{hashlib.sha256(SESSION.encode()).hexdigest()}.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        if failure == 'future':
            rows[-1]['at'] = binding._clock() + 1000
        elif failure == 'duplicate-id':
            rows.append(dict(rows[-1]))
        else:
            rows[-1].pop('event_id')
            rows.append(dict(rows[-1]))
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    if failure != 'stale-fingerprint':
        fingerprint = binding.blocker_fingerprint(record['blockers'][0])
    before = json.loads(json.dumps(record))
    with pytest.raises(ValueError):
        _continue_legacy(runs, record, fingerprint=fingerprint)
    assert record == before
    assert not list((runs / 'consumed-prompts').glob('*.json'))


@pytest.mark.parametrize('fields', [{}, {'permission_mode': 'default'},
    {'permission_mode': 'unknown'}, {'nested': {'permission_mode': 'bypassPermissions'}}])
def test_legacy_hook_continue_never_borrows_initial_full_access(captures, fields):
    runs, capture = captures
    record = _legacy_hook_record()
    capture('Continue', **fields)
    event = binding.capture_events(runs, SESSION)[-1]
    with pytest.raises(ValueError):
        _continue_legacy(runs, record)
    assert binding.event_available(runs, SESSION, event)


@pytest.mark.parametrize('remove_marker', [False, True])
def test_legacy_hook_continue_does_not_consume_a_manual_question_reply(captures, remove_marker):
    runs, capture = captures
    record = _legacy_hook_record()
    render(runs)
    capture('Continue', permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    if remove_marker:
        binding.question_path(runs, SESSION).unlink()
    with pytest.raises(ValueError, match='pending manual question'):
        _continue_legacy(runs, record)
    assert binding.event_available(runs, SESSION, event)


def test_legacy_hook_continue_does_not_use_an_older_reply_or_a_new_manual_mode(captures):
    runs, capture = captures
    record = _legacy_hook_record()
    capture('Continue', permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    capture('Wait, inspect the failure first', permission_mode='bypassPermissions')
    with pytest.raises(ValueError, match='latest whole user capture'):
        _continue_legacy(runs, record)
    assert binding.event_available(runs, SESSION, event)
    capture('Continue', permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    observed = {'origin': 'host-hook-capture', 'session_id': SESSION,
        'permission_mode': 'default', 'at': binding._clock()}
    observed['mac'] = binding._seal(SECRET, observed)
    binding._write_private(runs / 'host-context' / f'{hashlib.sha256(SESSION.encode()).hexdigest()}.json', observed)
    with pytest.raises(ValueError, match='current host mode'):
        _continue_legacy(runs, record)
    assert binding.event_available(runs, SESSION, event)


@pytest.mark.parametrize('wrong_root', [False, True])
@pytest.mark.parametrize('legacy', [False, True])
def test_legacy_hook_continue_corroborates_its_own_canonical_host_turn(captures, tmp_path, monkeypatch, wrong_root, legacy):
    import datetime
    runs, capture = captures
    initial = binding.capture_events(runs, SESSION)[-1]
    home, root = tmp_path / 'home', tmp_path / 'repo'
    root.mkdir()
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: home))
    record = _legacy_hook_record()
    capture('Continue')  # Old native captures omitted permission_mode.
    if legacy:
        # Model the older hook format, retaining the actual captured digest/time/session.
        path = runs / 'prompts' / f'{hashlib.sha256(SESSION.encode()).hexdigest()}.jsonl'
        captured = [json.loads(line) for line in path.read_text().splitlines()]
        captured[-1].pop('event_id')
        path.write_text(''.join(json.dumps(row) + '\n' for row in captured), encoding='utf-8')
    event = binding.capture_events(runs, SESSION)[-1]
    log = home / '.codex' / 'sessions' / '2026' / '10' / '19' / f'rollout-date-{SESSION}.jsonl'
    log.parent.mkdir(parents=True)
    rows = [{'type': 'session_meta', 'payload': {'id': SESSION, 'originator': 'codex_vscode', 'source': 'vscode'}},
        {'type': 'turn_context', 'payload': {'approval_policy': 'never',
            'sandbox_policy': {'type': 'danger-full-access'}, 'cwd': str(root)}},
        {'type': 'event_msg', 'timestamp': datetime.datetime.fromtimestamp(initial['at'], datetime.UTC).isoformat(),
            'payload': {'type': 'user_message', 'message': '/implement v0.2.0'}},
        {'type': 'event_msg', 'timestamp': datetime.datetime.fromtimestamp(event['at'], datetime.UTC).isoformat(),
            'payload': {'type': 'user_message', 'message': 'Continue'}}]
    log.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
    record['approvals']['authorization_context'].update(origin='codex-host-transcript', transcript_path=str(log),
        prompt_sha256=initial['prompt'], at=initial['at'])
    roots = {str((tmp_path / 'foreign').resolve())} if wrong_root else {str(root.resolve())}
    if wrong_root:
        with pytest.raises(ValueError, match='full-access context'):
            _continue_legacy(runs, record, roots=roots)
        assert binding.event_available(runs, SESSION, event)
    else:
        result = _continue_legacy(runs, record, roots=roots)
        assert result['capture_context']['origin'] == 'codex-host-transcript'
        assert result['capture_context']['prompt_sha256'] == event['prompt']
        assert result['event_id'] == event.get('event_id')
        assert result['event_identity_sha256'] == binding.digest(json.dumps(
            [SESSION, event.get('event_id'), event['at'], event['prompt']]))
        assert not binding.event_available(runs, SESSION, event)
        with pytest.raises(binding.Refusal, match='code-used'):
            _continue_legacy(runs, json.loads(json.dumps(record)), roots=roots)


def _whole_minor_route_record():
    record = approved_record()
    record.update(schema=checker.SCHEMA_MINOR, scope='minor', minor='v0.2', repo='acme/demo', members=[
        {'version': 'v0.2.0', 'source_branch': 'feat/v0.2.0-alpha', 'approvals': {'classes': []}},
        {'version': 'v0.2.1', 'source_branch': 'feat/v0.2.1-omega', 'approvals': {'classes': []}}])
    record['approvals'].pop('source_branch')
    record['approvals']['push_remote_url'] = 'https://github.com/acme/demo.git'
    return record


@pytest.mark.parametrize(('last_status', 'last_repo', 'expected'), [
    ('met', 'acme/demo', 'met'), ('unmet', None, 'unmet'),
    ('cannot-verify', None, 'cannot-verify'), ('met', 'evil/fork', 'unmet')])
def test_whole_minor_remote_checks_every_projected_member(tmp_path, monkeypatch, last_status, last_repo, expected):
    record = _whole_minor_route_record()
    calls = []

    def verify(root, url, *, git, run, branch):
        calls.append(branch)
        return (last_status, last_repo, 'controlled-route') if branch.endswith('omega') else ('met', 'acme/demo', 'ok')

    monkeypatch.setattr(checker.repo_host, 'verify_push_route', verify)
    ctx = SimpleNamespace(root=tmp_path, push_remote_url=record['approvals']['push_remote_url'],
        git='private-unit-git', run=lambda *args: pytest.fail('unit route must not spawn'), notices=[])
    assert not hasattr(ctx, 'version') and not hasattr(ctx, 'slug')
    assert checker._approved_remote_status(ctx, record) == expected
    assert calls == [member['source_branch'] for member in record['members']]


@pytest.mark.parametrize('invalid', ['empty', 'mapping', 'nondict', 'unknown-version', 'duplicate', 'missing-branch', 'blank-branch'])
def test_whole_minor_remote_never_accepts_empty_or_ambiguous_members(tmp_path, monkeypatch, invalid):
    record = _whole_minor_route_record()
    if invalid == 'empty':
        record['members'] = []
    elif invalid == 'mapping':
        record['members'] = {}
    elif invalid == 'nondict':
        record['members'][1] = None
    elif invalid == 'unknown-version':
        record['members'][1]['version'] = 'not-a-member-version'
    elif invalid == 'duplicate':
        record['members'][1]['version'] = record['members'][0]['version']
    elif invalid == 'missing-branch':
        record['members'][1].pop('source_branch')
    else:
        record['members'][1]['source_branch'] = ' '
    monkeypatch.setattr(checker.repo_host, 'verify_push_route', lambda *args, **kwargs: pytest.fail('invalid parent must refuse before probing'))
    ctx = SimpleNamespace(root=tmp_path, push_remote_url=record['approvals']['push_remote_url'])
    assert checker._approved_remote_status(ctx, record) == 'cannot-verify'


def test_whole_minor_remote_checks_later_members_after_an_earlier_refusal(tmp_path, monkeypatch):
    record = _whole_minor_route_record()
    calls = []

    def verify(root, url, *, git, run, branch):
        calls.append(branch)
        return ('unmet', None, 'redirected') if branch.endswith('alpha') else ('cannot-verify', None, 'unknown')

    monkeypatch.setattr(checker.repo_host, 'verify_push_route', verify)
    ctx = SimpleNamespace(root=tmp_path, push_remote_url=record['approvals']['push_remote_url'],
        git='private-unit-git', run=lambda *args: pytest.fail('unit route must not spawn'), notices=[])
    assert checker._approved_remote_status(ctx, record) == 'cannot-verify'
    assert calls == [member['source_branch'] for member in record['members']]


def test_real_whole_minor_resolve_checks_all_routes_and_retains_the_genuine_continue(tmp_path, monkeypatch):
    from tests.validators.test_check_plan_completion import TRANSPORT_OVERRIDE_ENV, _git
    home = tmp_path / 'home'
    home.mkdir()
    for key in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA'):
        monkeypatch.setenv(key, str(home))
    monkeypatch.setenv('NEXUS_HUB_HOME', str(home / '.nexus-hub'))
    for key in (*TRANSPORT_OVERRIDE_ENV, 'GH_HOST', 'NEXUS_RUNNER_LAUNCH'):
        monkeypatch.delenv(key, raising=False)
    empty = tmp_path / 'empty.gitconfig'
    empty.write_text('', encoding='utf-8')
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', str(empty))
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    from tests.validators.test_completion_minor_record import SESSION as MINOR_SESSION
    from tests.validators.test_completion_minor_record import Minor
    minor = Minor(tmp_path, monkeypatch)

    def capture(prompt):
        result = subprocess.run([sys.executable, str(Path(gate.__file__)), 'capture'],
            input=json.dumps({'session_id': MINOR_SESSION, 'prompt': prompt, 'permission_mode': 'bypassPermissions'}),
            text=True, capture_output=True, cwd=minor.work, env=minor.env, check=False)
        assert result.returncode == 0, result.stdout + result.stderr

    approvals = minor.approvals()
    spec = json.loads(approvals.read_text(encoding='utf-8'))
    spec['autonomy'] = {'corrections': 'within-approved-scope'}
    approvals.write_text(json.dumps(spec), encoding='utf-8')
    capture('/implement v0.5')
    page = minor.render(MINOR_SESSION, '--approvals', str(approvals))
    assert page.returncode == 0, page.stdout + page.stderr
    capture(page.stdout.splitlines()[0])
    created = minor.run('record', 'create', '--minor', 'v0.5', '--session', MINOR_SESSION, '--approvals', str(approvals))
    assert created.returncode == 0, created.stdout + created.stderr
    before = minor.record()
    assert 'source_branch' not in before['approvals']
    assert len(before['members']) == 2
    legacy = {'at': time.time(), 'category': 'no-progress', 'open': True,
        'evidence': 'progress score unchanged over 3 refusals: member.gate task.T001'}
    before['blockers'] = [legacy]
    minor.write_record(before, resign=False)  # Exact old hook shape; signed authority is untouched.
    capture('Continue')
    args = ('record', 'resolve', '--minor', 'v0.5', '--session', MINOR_SESSION, '--blocker', '0',
        '--fingerprint', binding.blocker_fingerprint(legacy))
    result = minor.run(*args)
    assert result.returncode == 0, result.stdout + result.stderr
    after = minor.record()
    assert after['blockers'][0]['open'] is False
    assert after['approvals']['resolutions'][-1]['origin'] == 'existing-approved-plan-user-continuation'
    assert after['approvals_hmac'] == checker._sign(after, (minor.runs / '.secret').read_bytes())
    for key in ('nonce', 'created', 'start_head', 'members', 'session_id', 'minor', 'scope'):
        assert after[key] == before[key]
    assert {key: value for key, value in after['approvals'].items() if key != 'resolutions'} == before['approvals']
    assert minor.run('check-minor', 'v0.5', '--session', MINOR_SESSION).returncode != 0

    # The second member's redirected route must not be hidden by the first member's valid route.
    second = json.loads(json.dumps(after))
    second['blockers'].append({**legacy, 'at': time.time(), 'open': True})
    minor.write_record(second, resign=False)
    capture('Continue')
    event = binding.capture_events(minor.runs, MINOR_SESSION)[-1]
    branch = second['members'][-1]['source_branch']
    _git(minor.work, 'remote', 'add', 'fork', 'https://github.com/evil/fork.git')
    key = f'branch.{branch}.pushRemote'
    _git(minor.work, 'config', key, 'fork')
    args = ('record', 'resolve', '--minor', 'v0.5', '--session', MINOR_SESSION, '--blocker', '1',
        '--fingerprint', binding.blocker_fingerprint(second['blockers'][1]))
    raw = minor.record_path().read_bytes()
    refused = minor.run(*args)
    assert refused.returncode == 3, refused.stdout + refused.stderr
    assert minor.record_path().read_bytes() == raw
    assert binding.event_available(minor.runs, MINOR_SESSION, event)
    _git(minor.work, 'config', '--unset', key)
    repaired = minor.run(*args)
    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    assert not binding.event_available(minor.runs, MINOR_SESSION, event)
