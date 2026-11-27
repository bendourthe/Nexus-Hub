"""Policy intent ownership regressions using only private fixture captures."""

import copy

import pytest

from .test_approval_flow_continuation import (
    SESSION, SECRET, approved_record, captures, consume, render, binding, checker,
    _historical_policy_adoption,
)

from .test_check_plan_completion import _isolated_git_config  # noqa: F401


@pytest.mark.parametrize('instruction', ['Approve', 'The source contains a workflow file.', 'Continue the approved work.'])
def test_unrelated_user_message_cannot_grant_sensitive_policy(captures, instruction):
    runs, capture = captures
    record = approved_record()
    record['approvals']['autonomy_policy'] = binding.validate_policy({})
    pending = render(runs) if instruction == 'Approve' else None
    capture(instruction, permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    policy = {'planned_actions': [{'class': 'ci-security-change', 'paths': ['.github/workflows/ci.yml']}]}
    before = copy.deepcopy(record)
    with pytest.raises(ValueError, match='declaration|question'):
        binding.adopt_policy(runs, record, instruction, policy)
    assert record == before
    assert binding.event_available(runs, SESSION, event)
    if pending is not None:
        assert consume(runs, pending)[0]['pasted'] == 'Approve'


@pytest.mark.parametrize('mutation', ['nonce', 'path', 'corrections', 'format', 'envelope'])
def test_declaration_cannot_select_another_run_or_policy(captures, mutation):
    runs, capture = captures
    record = approved_record()
    policy = {'planned_actions': [{'class': 'ci-security-change', 'paths': ['.github/workflows/ci.yml']}]}
    instruction = binding.policy_adoption_declaration(record, policy)
    if mutation == 'nonce':
        instruction = instruction.replace('run unchanged:', 'run another-run:')
    elif mutation == 'path':
        instruction = instruction.replace('ci.yml', 'other.yml')
    elif mutation == 'corrections':
        instruction = instruction.replace('"corrections":null', '"corrections":"within-approved-scope"')
    elif mutation == 'format':
        instruction = instruction.replace('"corrections":', '"corrections": ')
    else:
        instruction = '<send_user_message_question_reply>' + instruction + '</send_user_message_question_reply>'
    capture(instruction, permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    before = copy.deepcopy(record)
    with pytest.raises(ValueError, match='declaration'):
        binding.adopt_policy(runs, record, instruction, policy)
    assert record == before
    assert binding.event_available(runs, SESSION, event)


def test_exact_declaration_bound_to_a_question_cannot_be_repurposed(captures):
    runs, capture = captures
    record = approved_record()
    instruction = binding.policy_adoption_declaration(record, {})
    pending = render(runs)
    capture(instruction, permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    before = copy.deepcopy(record)
    with pytest.raises(ValueError, match='question'):
        binding.adopt_policy(runs, record, instruction, {})
    assert record == before and binding.event_available(runs, SESSION, event)
    assert binding.pending_path(runs, 'fixture').exists()
    capture('Approve', permission_mode='bypassPermissions')
    assert consume(runs, pending)[0]['pasted'] == 'Approve'


def test_exact_run_and_policy_declaration_adopts_once(captures):
    runs, capture = captures
    record = approved_record()
    record['approvals']['autonomy_policy'] = binding.validate_policy({})
    policy = {'planned_actions': [{'class': 'ci-security-change', 'paths': ['.github/workflows/ci.yml']}]}
    instruction = binding.policy_adoption_declaration(record, policy)
    assert instruction == 'Adopt autonomy policy for run unchanged: ' + binding.canonical(binding.validate_policy(policy)).decode('utf-8')
    capture(instruction, permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    binding.adopt_policy(runs, record, instruction, policy)
    assert record['approvals']['autonomy_policy'] == binding.validate_policy(policy)
    assert len(record['approvals']['policy_adoptions']) == 1
    assert not binding.event_available(runs, SESSION, event)
    before = copy.deepcopy(record)
    claims = {path.name: path.read_bytes() for path in (runs / 'consumed-prompts').iterdir()}
    binding.adopt_policy(runs, record, instruction, policy)
    assert record == before
    assert {path.name: path.read_bytes() for path in (runs / 'consumed-prompts').iterdir()} == claims


def test_historical_signed_natural_language_latest_retry_is_unchanged(captures):
    runs, capture = captures
    record = approved_record()
    instruction = 'Continue this reviewed historical policy.'
    capture(instruction, permission_mode='bypassPermissions')
    _historical_policy_adoption(runs, record, instruction, {})
    before = copy.deepcopy(record)
    claims = {path.name: path.read_bytes() for path in (runs / 'consumed-prompts').iterdir()}
    assert checker._sign(record, SECRET) == record['approvals_hmac']
    binding.adopt_policy(runs, record, instruction, {})
    assert record == before
    assert checker._sign(record, SECRET) == record['approvals_hmac']
    assert {path.name: path.read_bytes() for path in (runs / 'consumed-prompts').iterdir()} == claims


def test_cli_render_reviews_policy_without_instruction_or_authority_mutation(tmp_path):
    import json
    from .test_approval_binding import _create, _fixture, _hook, _render
    from .test_check_plan_completion import PLAN_REL, SESSION as OWNER
    fx = _fixture(tmp_path)
    line = _render(fx)
    _hook(fx, OWNER, line)
    created = _create(fx)
    assert created.returncode == 0, created.stdout + created.stderr
    record = json.loads(fx.record_path().read_text(encoding='utf-8'))
    policy = {'planned_actions': [{'class': 'ci-security-change', 'paths': ['.github/workflows/ci  review.yml']}]}
    policy_file = tmp_path / 'reviewed-policy.json'
    policy_file.write_text(json.dumps(policy), encoding='utf-8')
    before = {path.relative_to(fx.runs): path.read_bytes() for path in fx.runs.rglob('*') if path.is_file()}
    args = ('record', 'adopt-policy', PLAN_REL, '--session', OWNER, '--policy', str(policy_file))
    result = fx.run(*args, '--render')
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.splitlines()[-1] == binding.policy_adoption_declaration(record, policy)
    assert 'Reviewed autonomy policy:' in result.stdout and 'Exact declaration:' in result.stdout
    assert '.github/workflows/ci  review.yml' in result.stdout
    assert r'ci\u0020\u0020review.yml' in result.stdout.splitlines()[-1]
    missing = fx.run(*args)
    assert missing.returncode != 0 and '--instruction-file' in missing.stderr
    assert {path.relative_to(fx.runs): path.read_bytes() for path in fx.runs.rglob('*') if path.is_file()} == before


@pytest.mark.parametrize('captured_path,requested_path', [
    ('src/a b.py', 'src/a  b.py'), ('src/a  b.py', 'src/a b.py'),
])
def test_policy_paths_with_different_whitespace_cannot_share_intent(captures, captured_path, requested_path):
    import json
    runs, capture = captures
    record = approved_record()
    captured_policy = {'planned_actions': [{'class': 'ci-security-change', 'paths': [captured_path]}]}
    requested_policy = {'planned_actions': [{'class': 'ci-security-change', 'paths': [requested_path]}]}
    captured = binding.policy_adoption_declaration(record, captured_policy)
    requested = binding.policy_adoption_declaration(record, requested_policy)
    # Control: the old raw-JSON declarations collide in the hook digest.
    assert binding.digest(binding.canonical(captured_policy).decode()) == binding.digest(binding.canonical(requested_policy).decode())
    assert binding.digest(captured) != binding.digest(requested)
    assert json.loads(captured.split(': ', 1)[1]) == binding.validate_policy(captured_policy)
    capture(captured, permission_mode='bypassPermissions')
    event = binding.capture_events(runs, SESSION)[-1]
    before = copy.deepcopy(record)
    with pytest.raises(ValueError, match='genuine whole'):
        binding.adopt_policy(runs, record, requested, requested_policy)
    assert record == before and binding.event_available(runs, SESSION, event)
    binding.adopt_policy(runs, record, captured, captured_policy)
    assert record['approvals']['autonomy_policy']['planned_actions'][0]['paths'] == [captured_path]
    assert not binding.event_available(runs, SESSION, event)
