"""Tests for the agent-access-policy capability grant broker.

The suite treats denial behavior as the primary contract. It also proves that
the plan-only default cannot execute, the optional execution path stays
list-based and sandbox-gated, and the skill-flattening installer path preserves
the bundled broker script.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.lib.integrations._catalog_adapters import flatten_skills
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.manifest import InstallManifest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "orchestration" / "agent-access-policy"
_BROKER_PATH = _BUNDLE / "scripts" / "capability-grant-broker.py"
_SKILL_PATH = _BUNDLE / "SKILL.md"


def _load_broker():
    spec = importlib.util.spec_from_file_location(
        "capability_grant_broker", _BROKER_PATH
    )
    assert spec and spec.loader, f"cannot load {_BROKER_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


broker = _load_broker()


def _grant(**overrides) -> dict:
    grant = {
        "authorization_source": "human:change-123",
        "capabilities": [],
        "writable_paths": [],
        "network_destinations": [],
    }
    grant.update(overrides)
    return grant


def _request(**overrides) -> dict:
    request = {
        "command": ["python", "-V"],
        "required_capabilities": [],
        "requested_write_paths": [],
        "requested_network_destinations": [],
        "grant": _grant(),
    }
    request.update(overrides)
    return request


def _write_request(tmp_path: Path, payload: object) -> Path:
    path = tmp_path / "request.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_ungranted_capability_is_denied() -> None:
    decision = broker.authorize(
        ["python", "-V"],
        ["use_secret"],
        _grant(),
    )

    assert decision.authorized is False
    assert decision.exit_code == broker.EXIT_DENIED
    assert "ungranted capabilities: use_secret" in decision.reasons


def test_grant_without_authorization_source_is_denied() -> None:
    decision = broker.authorize(
        ["python", "-V"],
        [],
        _grant(authorization_source=""),
    )

    assert decision.authorized is False
    assert "grant has no authorization source" in decision.reasons


def test_write_outside_scope_is_denied(tmp_path: Path) -> None:
    allowed = (tmp_path / "allowed").resolve()
    outside = (tmp_path / "outside" / "result.txt").resolve()
    decision = broker.authorize(
        ["python", "build.py"],
        ["write"],
        _grant(capabilities=["write"], writable_paths=[str(allowed)]),
        requested_write_paths=[str(outside)],
    )

    assert decision.authorized is False
    assert any("outside the grant scope" in reason for reason in decision.reasons)


def test_network_destination_outside_allowlist_is_denied() -> None:
    decision = broker.authorize(
        ["python", "fetch.py"],
        ["network"],
        _grant(
            capabilities=["network"],
            network_destinations=["https://api.example.test"],
        ),
        requested_network_destinations=["https://other.example.test"],
    )

    assert decision.authorized is False
    assert any("outside the grant allowlist" in reason for reason in decision.reasons)


def test_execution_without_reachable_sandbox_is_denied() -> None:
    decision = broker.authorize(["python", "-V"], [], _grant())
    assert decision.plan is not None

    exit_code, payload = broker.execute_in_sandbox(decision.plan, None)

    assert exit_code == broker.EXIT_DENIED
    assert payload["status"] == "denied"
    assert "no sandbox" in payload["reasons"][0]


def test_resource_requests_without_matching_capabilities_are_denied(
    tmp_path: Path,
) -> None:
    requested_file = (tmp_path / "result.txt").resolve()
    decision = broker.authorize(
        ["python", "worker.py"],
        [],
        _grant(
            writable_paths=[str(tmp_path.resolve())],
            network_destinations=["https://api.example.test"],
        ),
        requested_write_paths=[str(requested_file)],
        requested_network_destinations=["https://api.example.test"],
    )

    assert decision.authorized is False
    assert "requested write paths were not declared with the write capability" in (
        decision.reasons
    )
    assert (
        "requested network destinations were not declared with the network capability"
        in decision.reasons
    )


def test_capabilities_without_required_scopes_are_denied() -> None:
    decision = broker.authorize(
        ["python", "worker.py"],
        ["write", "network"],
        _grant(capabilities=["write", "network"]),
    )

    assert decision.authorized is False
    assert (
        "write capability requires at least one requested write path"
        in decision.reasons
    )
    assert "write capability has no writable path scope" in decision.reasons
    assert (
        "network capability requires at least one requested destination"
        in decision.reasons
    )
    assert "network capability has no destination allowlist" in decision.reasons


def test_unreachable_sandbox_command_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = broker.authorize(["python", "-V"], [], _grant())
    assert decision.plan is not None
    monkeypatch.setattr(broker.shutil, "which", lambda _name: None)

    exit_code, payload = broker.execute_in_sandbox(
        decision.plan, ["missing-sandbox-runner", "--"]
    )

    assert exit_code == broker.EXIT_DENIED
    assert "sandbox is not reachable" in payload["reasons"][0]


@pytest.mark.parametrize(
    "payload",
    [
        _request(command="python -V"),
        _request(grant=[]),
        _request(required_capabilities=["unknown"]),
        _request(grant={"authorization_source": "human"}),
        _request(grant={**_grant(), "unexpected": True}),
        _request(grant=_grant(capabilities=["write", "write"])),
        _request(grant=_grant(writable_paths=["relative/path"])),
        _request(
            grant=_grant(
                network_destinations=["https://api.example.test/path with-space"]
            )
        ),
        {**_request(), "execute": True},
    ],
)
def test_malformed_request_returns_usage_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], payload: object
) -> None:
    path = _write_request(tmp_path, payload)

    exit_code = broker.main(["--request", str(path)])

    captured = capsys.readouterr()
    assert exit_code == broker.EXIT_USAGE_ERROR
    assert json.loads(captured.err)["status"] == "usage-error"


def test_fully_granted_action_produces_least_privilege_plan(tmp_path: Path) -> None:
    writable_root = (tmp_path / "workspace").resolve()
    requested_file = writable_root / "reports" / "result.json"
    decision = broker.authorize(
        ["python", "worker.py"],
        ["write", "network"],
        _grant(
            capabilities=["network", "write", "use_secret", "destructive_test"],
            writable_paths=[str(writable_root), str((tmp_path / "unused").resolve())],
            network_destinations=[
                "https://api.example.test",
                "https://unused.example.test",
            ],
        ),
        requested_write_paths=[str(requested_file)],
        requested_network_destinations=["https://api.example.test"],
    )

    assert decision.authorized is True
    assert decision.exit_code == broker.EXIT_AUTHORIZED
    assert decision.plan is not None
    assert decision.plan.mode == "plan-only"
    assert decision.plan.sandbox_required is True
    assert decision.plan.capabilities == ("network", "write")
    assert decision.plan.writable_paths == (
        os.path.normcase(os.path.normpath(str(requested_file))),
    )
    assert decision.plan.network_destinations == ("https://api.example.test",)


def test_cli_defaults_to_plan_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _write_request(tmp_path, _request())

    def fail_if_executed(*_args, **_kwargs):
        raise AssertionError("default authorization path attempted execution")

    monkeypatch.setattr(broker, "execute_in_sandbox", fail_if_executed)
    exit_code = broker.main(["--request", str(path)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == broker.EXIT_AUTHORIZED
    assert payload["status"] == "authorized"
    assert payload["plan"]["mode"] == "plan-only"


def test_execution_uses_list_argv_and_never_a_shell(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = broker.authorize(["python", "-V"], [], _grant())
    assert decision.plan is not None
    observed: dict = {}

    monkeypatch.setattr(broker.shutil, "which", lambda _name: "sandbox-runner")

    def fake_run(argv, **kwargs):
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(broker.subprocess, "run", fake_run)
    exit_code, payload = broker.execute_in_sandbox(
        decision.plan, ["sandbox-runner", "--"]
    )

    assert exit_code == broker.EXIT_AUTHORIZED
    assert payload["status"] == "executed"
    assert observed["argv"] == ["sandbox-runner", "--", "python", "-V"]
    assert observed["kwargs"] == {"shell": False, "check": False}


def test_sandboxed_child_failure_has_distinct_exit_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decision = broker.authorize(["python", "-V"], [], _grant())
    assert decision.plan is not None
    monkeypatch.setattr(broker.shutil, "which", lambda _name: "sandbox-runner")
    monkeypatch.setattr(
        broker.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=9),
    )

    exit_code, payload = broker.execute_in_sandbox(
        decision.plan, ["sandbox-runner", "--"]
    )

    assert exit_code == broker.EXIT_EXECUTION_ERROR
    assert payload["status"] == "execution-error"
    assert payload["child_exit_code"] == 9


def test_broker_imports_only_the_standard_library() -> None:
    tree = ast.parse(_BROKER_PATH.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    assert imports <= (set(sys.stdlib_module_names) | {"__future__"})


def test_bundle_documentation_references_script_and_test() -> None:
    body = _SKILL_PATH.read_text(encoding="utf-8")

    assert "capability-grant-broker.py" in body
    assert "test_capability_grant_broker.py" in body


def test_broker_bundle_distributes_through_flattened_skill_copy(tmp_path: Path) -> None:
    destination = tmp_path / "installed" / "skills"
    context = InstallContext(
        repo_root=_ROOT,
        target_root=tmp_path,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
    )

    actions = flatten_skills(
        context,
        "phase5-test",
        _ROOT / "catalog" / "skills",
        destination,
    )

    installed = destination / "agent-access-policy" / "scripts" / _BROKER_PATH.name
    assert actions
    assert installed.is_file()
    assert installed.read_bytes() == _BROKER_PATH.read_bytes()
