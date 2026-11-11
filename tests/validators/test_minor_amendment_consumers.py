"""Real captured amendments reach consumers and refuse incompatible helper bundles."""

from __future__ import annotations

import copy
import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from .test_minor_scope_amendment import amend_fixture
from .test_completion_minor_record import (
    SESSION, REPO_ROOT, SCRIPTS, ck, cm, minor,
    _isolated_git_config, _no_transport_overrides,
)

import cleanup_merged as cleanup
import run_plan as runner

BASELINE = "73efff30b2ddec00c69b3d45abb3c1cd5d57ad63"
EXPECTED_MEMBERS = ["v0.5.2", "v0.5.10", "v0.5.11"]


@pytest.fixture(autouse=True)
def _private_native_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """All helper generations inherit only this test's disposable native home."""
    home = tmp_path / "private-home"
    for key, suffix in (("HOME", ""), ("USERPROFILE", ""), ("APPDATA", "appdata"),
                        ("LOCALAPPDATA", "localappdata"), ("NEXUS_HUB_HOME", ".nexus-hub"),
                        ("CODEX_HOME", ".codex")):
        target = home / suffix
        target.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(key, str(target))
    monkeypatch.delenv("NEXUS_RUNNER_CHECKER", raising=False)


@pytest.fixture(scope="module")
def baseline_scripts(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Use complete historical siblings, preserving their real imports and APIs."""
    found = subprocess.run(["git", "cat-file", "-e", f"{BASELINE}:scripts/check_plan_completion.py"],
                           cwd=REPO_ROOT, capture_output=True, check=False)
    if found.returncode:
        pytest.skip(f"historical helper compatibility requires Git object {BASELINE}")
    exported = subprocess.run(["git", "archive", "--format=zip", BASELINE, "scripts"],
                              cwd=REPO_ROOT, capture_output=True, check=True)
    destination = tmp_path_factory.mktemp("baseline-native-helpers")
    with zipfile.ZipFile(io.BytesIO(exported.stdout)) as archive:
        archive.extractall(destination)
    scripts = destination / "scripts"
    for name in ("check_plan_completion.py", "completion_minor.py", "minor_close.py",
                 "approval_binding.py", "approval_page.py", "nexus_process.py"):
        assert (scripts / name).is_file(), f"incomplete historical helper bundle: {name}"
    return scripts


def _bytes_under(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def _unchanged_snapshot(fx) -> tuple[bytes, dict[str, bytes], dict[str, bytes]]:
    """Include raw refs, index, objects, reflogs, documents and the bare remote."""
    return fx.record_path().read_bytes(), _bytes_under(fx.work), _bytes_under(fx.remote)


def _command(fx, scripts: Path, script: str, *args: str) -> subprocess.CompletedProcess:
    env = {**fx.env, "PYTHONDONTWRITEBYTECODE": "1"}
    # Each child must discover siblings in the chosen complete bundle, never the
    # current source directory through a host PYTHONPATH setting.
    env.pop("PYTHONPATH", None)
    return subprocess.run([sys.executable, str(scripts / script), *args], cwd=fx.work,
                          env=env, capture_output=True, text=True, check=False, timeout=90)


READ_BUNDLE = """
import json, sys
from pathlib import Path
import check_plan_completion as ck
import completion_minor as cm
ctx, record = ck.resolve_minor_controller(Path(sys.argv[1]), sys.argv[2], minor_protocol=1)
assert cm._verified(ck, ctx, 'v0.5', record, minor_protocol=1)
print(json.dumps({'members': [m['version'] for m in cm.effective_members(ck, record)],
                  'history': record['minor_amendments'], 'root': str(ctx.root)}))
"""


def _new_bundle(tmp_path: Path) -> Path:
    scripts = tmp_path / "new-helpers"
    shutil.copytree(SCRIPTS, scripts, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return scripts


def _positive_bundle_read(fx, scripts: Path, accepted: dict) -> None:
    probe = scripts / "read_amended_fixture.py"
    probe.write_text(READ_BUNDLE, encoding="utf-8")
    before = _unchanged_snapshot(fx)
    observed = _command(fx, scripts, probe.name, str(fx.record_path()), SESSION)
    assert observed.returncode == 0, observed.stdout + observed.stderr
    result = json.loads(observed.stdout)
    assert result["members"] == EXPECTED_MEMBERS
    assert result["history"] == accepted["minor_amendments"]
    assert Path(result["root"]) == fx.work
    assert _unchanged_snapshot(fx) == before


def test_runner_and_cleanup_read_complete_captured_membership(minor, monkeypatch) -> None:
    _, accepted = amend_fixture(minor)
    before = _unchanged_snapshot(minor)
    monkeypatch.chdir(minor.work)
    monkeypatch.setitem(sys.modules, "check_plan_completion", ck)
    monkeypatch.setattr(cleanup, "_checker", lambda: ck)
    ctx, record = runner._verified_runner_minor(minor.record_path(), accepted)
    assert ctx.root == minor.work
    assert [m["version"] for m in cm.effective_members(ck, record)] == EXPECTED_MEMBERS
    host = cleanup.Host(minor.work, "develop")
    args = cleanup.build_parser().parse_args(["--minor", "v0.5", "--session", SESSION])
    receipt = cleanup._record_for_receipt(args, host)
    assert isinstance(receipt, tuple)
    path, cleanup_record, scope = receipt
    assert path == minor.record_path() and scope == "minor:v0.5"
    assert cleanup_record["minor_amendments"] == accepted["minor_amendments"]
    assert [m["version"] for m in cm.effective_members(ck, cleanup_record)] == EXPECTED_MEMBERS
    owned_branches, _paths, readable = cleanup.owned_names(host, [], None)
    assert readable and "feat/v0.5.11-added" in owned_branches
    assert cleanup._own_record(args, host) == minor.record_path()
    # A public compatibility number cannot authenticate changed permissions.
    tampered = copy.deepcopy(accepted)
    tampered["minor_amendment_members"][0]["approvals"]["classes"].append({"class": "cleanup-merged"})
    assert not cm._verified(ck, minor.rctx(), "v0.5", tampered, minor_protocol=1)
    assert _unchanged_snapshot(minor) == before


@pytest.mark.parametrize("combination,diagnostic", [
    ("coherent-old", "record-tampered"),
    ("new-signer-old-membership", "minor-amendment"),
    ("new-signature-membership-old-archive", "minor-amendment-protocol-required"),
    ("old-signer-new-membership", "minor-amendment-consumer-incompatible"),
])
def test_historical_and_mixed_helpers_refuse_before_native_or_git_writes(
    minor, tmp_path: Path, baseline_scripts: Path, combination: str, diagnostic: str,
) -> None:
    _, accepted = amend_fixture(minor)
    current = _new_bundle(tmp_path)
    _positive_bundle_read(minor, current, accepted)
    mixed = tmp_path / combination
    shutil.copytree(baseline_scripts, mixed)
    if combination == "new-signer-old-membership":
        shutil.copyfile(current / "check_plan_completion.py", mixed / "check_plan_completion.py")
    elif combination == "new-signature-membership-old-archive":
        for name in ("check_plan_completion.py", "completion_minor.py", "approval_binding.py", "approval_page.py"):
            shutil.copyfile(current / name, mixed / name)
    elif combination == "old-signer-new-membership":
        shutil.copyfile(current / "completion_minor.py", mixed / "completion_minor.py")
    before = _unchanged_snapshot(minor)
    if combination == "new-signature-membership-old-archive":
        refused = _command(minor, mixed, "minor_close.py", "archive", "--minor", "v0.5",
                           "--session", SESSION, "--apply", "--repo", str(minor.work))
    else:
        refused = _command(minor, mixed, "check_plan_completion.py", "record", "pause",
                           "--minor", "v0.5", "--session", SESSION)
    assert refused.returncode != 0, refused.stdout + refused.stderr
    output = refused.stdout + refused.stderr
    assert diagnostic in output, output
    assert "approval-not-captured" not in output, output
    assert "ModuleNotFoundError" not in output and "SyntaxError" not in output, output
    assert _unchanged_snapshot(minor) == before
