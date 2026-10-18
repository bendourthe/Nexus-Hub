"""Parity tests for `nexus-hub doctor` across both installer implementations.

Every behavioral assertion here runs against BOTH `scripts/installer.sh` and
`scripts/installer.ps1` through the `doctor` fixture, so each one doubles as a
parity assertion. That is the durable fix from
`docs/incidents/provenance-ledger-sibling-divergence-20260722.md`, applied as a
requirement rather than a convention: a `.ps1` that parses and runs can still
disagree with its `.sh` sibling, and only a comparison catches it.

The first run of these two implementations against a real machine found exactly
such a divergence (a trailing CR on the last TSV field made every
`file_contains` surface read MISSING in Bash while PowerShell reported it ok),
which is why the parity fixture is the design here and not a separate
end-of-suite comparison someone has to remember to extend.

The PowerShell leg skips when no interpreter is present. A skip emits no signal,
which is the v3.11.0 failure mode, so it is backstopped by
`test_installer_ps1_parses_unconditionally` below and by the unconditional
AST-parse step in CI's `shellcheck` job.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"


def _powershell() -> str | None:
    for exe in ("pwsh", "powershell"):
        if shutil.which(exe):
            return exe
    return None


def _bash() -> str | None:
    return shutil.which("bash")


CONTRACT = {
    "install_verify": [
        {
            "label": "Present Platform",
            "detect": ["~/.present"],
            "remediation": "re-run the installer (present block)",
            "surfaces": [
                {"label": "skills", "kind": "nonempty_dir", "path": "~/.present/skills"},
                {"label": "marker", "kind": "is_file", "path": "~/.present/MARKER.md"},
                {
                    "label": "index",
                    "kind": "file_contains",
                    "path": "~/.present/MARKER.md",
                    "needle": "Skill Index",
                },
            ],
        },
        {
            "label": "Absent Platform",
            "detect": ["~/.absent"],
            "remediation": "install the absent platform first",
            "surfaces": [
                {"label": "skills", "kind": "nonempty_dir", "path": "~/.absent/skills"},
            ],
        },
    ]
}


@pytest.fixture(params=["bash", "powershell"])
def doctor(request, tmp_path):
    """Run `doctor` through one implementation and return (exit_code, output).

    Both legs are driven with the same fake HOME and the same pinned contract,
    so any difference in the result is a genuine behavioral divergence.
    """
    impl = request.param
    if impl == "bash" and not _bash():
        pytest.skip("bash not available")
    if impl == "powershell" and not _powershell():
        pytest.skip("no PowerShell interpreter available")

    def run(home: Path, contract: Path | None, extra_args: list[str] | None = None):
        env = dict(os.environ)
        env["HOME"] = str(home)
        # PowerShell derives $HOME from USERPROFILE in a fresh session.
        env["USERPROFILE"] = str(home)
        env.pop("HOMEDRIVE", None)
        env.pop("HOMEPATH", None)
        if contract is not None:
            env["NEXUS_DOCTOR_CONTRACT"] = str(contract)
        args = extra_args or []
        if impl == "bash":
            cmd = [_bash(), str(INSTALLER_SH), "doctor", *args]
        else:
            cmd = [
                _powershell(),
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(INSTALLER_PS1),
                "doctor",
                *args,
            ]
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(tmp_path))
        return proc.returncode, proc.stdout + proc.stderr

    run.impl = impl  # type: ignore[attr-defined]
    return run


def write_contract(tmp_path: Path, data=CONTRACT) -> Path:
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def make_home(tmp_path: Path, *, complete: bool) -> Path:
    """Build a fake HOME where the 'Present Platform' is installed."""
    home = tmp_path / "home"
    skills = home / ".present" / "skills"
    skills.mkdir(parents=True)
    (skills / "a-skill").mkdir()
    marker = home / ".present" / "MARKER.md"
    marker.write_text(
        "# Marker\n\n## Skill Index\n" if complete else "# Marker\n\nno index here\n",
        encoding="utf-8",
    )
    return home


def test_absent_platform_skips_and_exits_zero(doctor, tmp_path):
    """A platform that is not installed is a SKIP, never a failure."""
    home = tmp_path / "empty-home"
    home.mkdir()
    code, out = doctor(home, write_contract(tmp_path))
    assert code == 0, out
    assert "SKIP" in out
    assert "not installed" in out


def test_complete_platform_passes(doctor, tmp_path):
    code, out = doctor(make_home(tmp_path, complete=True), write_contract(tmp_path))
    assert code == 0, out
    assert "PASS" in out
    assert "Present Platform" in out


def test_missing_surface_fails_nonzero(doctor, tmp_path):
    """A detected platform missing a promised surface must exit non-zero."""
    code, out = doctor(make_home(tmp_path, complete=False), write_contract(tmp_path))
    assert code == 1, out
    assert "FAIL" in out
    assert "MISSING" in out


def test_missing_surface_prints_remediation(doctor, tmp_path):
    code, out = doctor(make_home(tmp_path, complete=False), write_contract(tmp_path))
    assert "re-run the installer (present block)" in out, out


def test_repair_flag_states_it_changed_nothing(doctor, tmp_path):
    """--repair prints remediation and must not mutate anything."""
    home = make_home(tmp_path, complete=False)
    code, out = doctor(home, write_contract(tmp_path), ["--repair"])
    assert code == 1, out
    assert "NOTHING WAS CHANGED" in out
    # Read-only: the incomplete marker is still incomplete.
    assert "Skill Index" not in (home / ".present" / "MARKER.md").read_text(encoding="utf-8")


def test_malformed_contract_fails_loudly(doctor, tmp_path):
    """A checker that cannot read its contract must NOT report a false CLEAR."""
    bad = tmp_path / "bad.json"
    bad.write_text("{ this is not json", encoding="utf-8")
    code, out = doctor(make_home(tmp_path, complete=True), bad)
    assert code == 2, out
    assert "FATAL" in out


def test_missing_contract_fails_loudly(doctor, tmp_path):
    code, out = doctor(make_home(tmp_path, complete=True), tmp_path / "nope.json")
    assert code == 2, out
    assert "FATAL" in out


def test_empty_install_verify_fails_loudly(doctor, tmp_path):
    empty = write_contract(tmp_path, {"install_verify": []})
    code, out = doctor(make_home(tmp_path, complete=True), empty)
    assert code == 2, out
    assert "FATAL" in out


def test_unknown_argument_exits_two(doctor, tmp_path):
    code, out = doctor(make_home(tmp_path, complete=True), write_contract(tmp_path), ["--bogus"])
    assert code == 2, out


def test_unknown_surface_kind_is_not_reported_clear(doctor, tmp_path):
    """A contract kind the doctor does not understand must fail, not pass.

    Otherwise adding a surface kind to the contract would silently widen the set
    of things reported CLEAR on an older installer.
    """
    contract = write_contract(
        tmp_path,
        {
            "install_verify": [
                {
                    "label": "Present Platform",
                    "detect": ["~/.present"],
                    "remediation": "r",
                    "surfaces": [
                        {"label": "future", "kind": "kind_from_the_future", "path": "~/.present"}
                    ],
                }
            ]
        },
    )
    code, out = doctor(make_home(tmp_path, complete=True), contract)
    assert code == 1, out
    assert "MISSING" in out


@pytest.mark.skipif(_powershell() is None, reason="no PowerShell interpreter available")
def test_installer_ps1_parses_unconditionally():
    """Backstop for the v3.11.0 failure mode: a .ps1 that never parses.

    The parity fixture above SKIPS its PowerShell leg when no interpreter is
    present, and a skip emits no signal in a green run. This asserts the file
    parses whenever an interpreter exists at all; CI additionally runs an
    unconditional AST-parse step over scripts/*.ps1.
    """
    exe = _powershell()
    script = (
        "$errs = $null; "
        f"$null = [System.Management.Automation.Language.Parser]::ParseFile('{INSTALLER_PS1}', "
        "[ref]$null, [ref]$errs); "
        "if ($errs -and $errs.Count -gt 0) { $errs | ForEach-Object { Write-Host $_.Message }; exit 1 } "
        "else { exit 0 }"
    )
    proc = subprocess.run(
        [exe, "-NoProfile", "-Command", script], capture_output=True, text=True
    )
    assert proc.returncode == 0, f"installer.ps1 has parse errors:\n{proc.stdout}{proc.stderr}"


def test_bash_and_powershell_agree_on_the_same_state(tmp_path):
    """The explicit cross-implementation comparison.

    The per-test parity above catches a divergence only if both legs actually
    ran. This asserts the two implementations produce the SAME exit code for the
    same machine state, in one place, so the comparison is legible as its own
    guarantee.
    """
    if not _bash() or not _powershell():
        pytest.skip("need both bash and a PowerShell interpreter")
    contract = write_contract(tmp_path)
    results = {}
    for impl, cmd_prefix in (
        ("bash", [_bash(), str(INSTALLER_SH)]),
        (
            "powershell",
            [_powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(INSTALLER_PS1)],
        ),
    ):
        codes = []
        for complete in (True, False):
            home = make_home(tmp_path / impl / str(complete), complete=complete)
            env = dict(os.environ)
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)
            env.pop("HOMEDRIVE", None)
            env.pop("HOMEPATH", None)
            env["NEXUS_DOCTOR_CONTRACT"] = str(contract)
            proc = subprocess.run(
                [*cmd_prefix, "doctor"], capture_output=True, text=True, env=env, cwd=str(tmp_path)
            )
            codes.append(proc.returncode)
        results[impl] = codes
    assert results["bash"] == results["powershell"], results


@pytest.mark.parametrize("level", ["medium", "high"])
def test_doctor_explains_unowned_effort_without_writing(
    doctor, tmp_path: Path, level: str
) -> None:
    home = make_home(tmp_path, complete=True)
    settings = home / ".claude/settings.json"
    settings.parent.mkdir()
    settings.write_text(
        json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": level}, "keep": True}),
        encoding="utf-8",
    )
    before = settings.read_bytes()
    code, output = doctor(home, write_contract(tmp_path))
    assert code == 0, output
    assert f"CLAUDE_CODE_EFFORT_LEVEL={level}" in output
    assert "overrides saved /effort choices" in output
    assert "Remove only env.CLAUDE_CODE_EFFORT_LEVEL" in output
    assert settings.read_bytes() == before
    assert not (home / ".nexus-hub/core-settings-seeds.json").exists()


def test_doctor_does_not_echo_unsupported_effort_values(doctor, tmp_path: Path) -> None:
    home = make_home(tmp_path, complete=True)
    settings = home / ".claude/settings.json"
    settings.parent.mkdir()
    private_value = "PRIVATE_SENTINEL_6543\nforged diagnostic"
    settings.write_text(
        json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": private_value}}),
        encoding="utf-8",
    )
    before = settings.read_bytes()
    code, output = doctor(home, write_contract(tmp_path))
    assert code == 0, output
    assert "an unsupported value" in output
    assert "PRIVATE_SENTINEL_6543" not in output and "forged diagnostic" not in output
    assert settings.read_bytes() == before


@pytest.mark.parametrize("json_mode", [False, True])
def test_installed_cli_routes_read_only_effort_diagnostics(
    tmp_path: Path, json_mode: bool
) -> None:
    home = tmp_path / "home"
    settings = home / ".claude/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}}), encoding="utf-8"
    )
    before = settings.read_bytes()
    install = home / ".nexus-hub"
    (install / "scripts").mkdir(parents=True)
    shutil.copyfile(
        REPO_ROOT / "scripts/nexus_hub_cli.py", install / "scripts/nexus_hub_cli.py"
    )
    env = dict(
        os.environ,
        HOME=str(home),
        USERPROFILE=str(home),
        NEXUS_HUB_HOME=str(install),
        NEXUS_HUB_SRC=str(REPO_ROOT),
    )
    if os.name == "nt":
        command = [str(REPO_ROOT / "scripts/nexus-hub.cmd")]
    else:
        command = [sys.executable, str(install / "scripts/nexus_hub_cli.py")]
    command += ["doctor", "--target", str(home), "--integrations", "claude"]
    if json_mode:
        command += ["--json"]
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=120,
        check=False,
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    if json_mode:
        payload = json.loads(proc.stdout)
        assert payload["error"] == "no manifest"
        assert len(payload["settings_notes"]) == 1
        output = payload["settings_notes"][0]
    else:
        output = proc.stdout
    assert "CLAUDE_CODE_EFFORT_LEVEL=medium" in output
    assert "Remove only env.CLAUDE_CODE_EFFORT_LEVEL" in output
    assert settings.read_bytes() == before
    assert not (install / "core-settings-seeds.json").exists()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("{", "unreadable"),
        ("[]", "unreadable"),
        ('{"env":[]}', "not an object"),
        ('{"env":{}}', None),
    ],
)
def test_effort_diagnostic_handles_invalid_user_settings_read_only(
    tmp_path: Path, raw: str, expected: str | None
) -> None:
    from scripts.lib.integrations.claude import effort_override_note

    path = tmp_path / ".claude/settings.json"
    path.parent.mkdir()
    path.write_text(raw, encoding="utf-8")
    before = path.read_bytes()
    note = effort_override_note(path)
    if expected is None:
        assert note is None
    else:
        assert note and expected in note
    assert path.read_bytes() == before
    assert not (tmp_path / ".nexus-hub").exists()


@pytest.mark.parametrize(
    "case", ["owned", "changed", "wrong-target", "removed", "invalid-schema"]
)
def test_effort_diagnostic_respects_seed_ownership(tmp_path: Path, case: str) -> None:
    from scripts.lib.integrations.claude import effort_override_note

    settings = tmp_path / ".claude/settings.json"
    settings.parent.mkdir()
    settings.write_text(
        json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}}), encoding="utf-8"
    )
    record_path = tmp_path / ".nexus-hub/core-settings-seeds.json"
    record_path.parent.mkdir()
    key = "env.CLAUDE_CODE_EFFORT_LEVEL"
    record = {
        "schema_version": 1,
        "target": ".claude/settings.json",
        "values": {key: "medium"},
        "removed": [],
    }
    if case == "changed":
        record["values"][key] = "high"
    elif case == "wrong-target":
        record["target"] = "another/settings.json"
    elif case == "removed":
        record["removed"] = [key]
    elif case == "invalid-schema":
        record["schema_version"] = True
    record_path.write_text(json.dumps(record), encoding="utf-8")
    before = settings.read_bytes(), record_path.read_bytes()
    note = effort_override_note(settings)
    assert note
    if case == "owned":
        assert "run nexus-hub upgrade" in note
    else:
        assert "Remove only env.CLAUDE_CODE_EFFORT_LEVEL" in note
    assert (settings.read_bytes(), record_path.read_bytes()) == before


@pytest.mark.parametrize("json_mode", [False, True])
@pytest.mark.parametrize("integration", ["claude", "codex"])
def test_checkout_doctor_reports_owned_install_without_writing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    json_mode: bool,
    integration: str,
) -> None:
    from scripts import nexus_hub_cli as cli
    from scripts.lib.integrations.manifest import InstallManifest
    from scripts.lib.integrations.result import FileAction

    home = tmp_path / "home"
    settings = home / ".claude/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(
        json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}}), encoding="utf-8"
    )
    manifest = InstallManifest()
    manifest.track(integration, str(settings))
    manifest.record_actions(integration, [FileAction(str(settings), "created")])
    manifest.save(home / ".nexus-hub/install-manifest.json")
    before = {
        p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()
    }
    for name in ("HOME", "USERPROFILE"):
        monkeypatch.setenv(name, str(home))
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home / ".nexus-hub"))
    monkeypatch.setenv("NEXUS_HUB_SRC", str(REPO_ROOT))
    args = ["--target", str(home), "--integrations", integration]
    if json_mode:
        args.append("--json")
    run_child = subprocess.run
    observed: list[subprocess.CompletedProcess[str]] = []

    def capture_child(
        *child_args: object, **child_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        result = run_child(
            *child_args,
            **child_kwargs,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        observed.append(result)
        return result

    monkeypatch.setattr(cli.subprocess, "run", capture_child)
    assert cli.cmd_doctor(args) == 0
    assert len(observed) == 1
    output = observed[0].stdout
    if json_mode:
        payload = json.loads(output)
        assert payload["counts"]["ok"] == 1
        assert bool(payload.get("settings_notes")) == (integration == "claude")
    else:
        assert "checked 1 integration(s)" in output
    assert ("Remove only env.CLAUDE_CODE_EFFORT_LEVEL" in output) == (
        integration == "claude"
    )
    assert {
        p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()
    } == before


def test_checkout_doctor_missing_source_reports_remediation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import nexus_hub_cli as cli

    monkeypatch.setenv("NEXUS_HUB_SRC", str(tmp_path / "not-a-source-tree"))
    assert cli.cmd_doctor([]) == 2
    assert (
        "set NEXUS_HUB_SRC to a checkout or rerun the installer"
        in capsys.readouterr().err
    )
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("json_mode", [False, True])
@pytest.mark.parametrize("manifest_present", [False, True])
def test_installed_doctor_without_source(
    tmp_path: Path, json_mode: bool, manifest_present: bool
) -> None:
    """The shipped doctor must work with bundled scripts and no source cache."""
    from scripts.lib.integrations.manifest import InstallManifest
    from scripts.lib.integrations.result import FileAction

    home = tmp_path / "home"
    installed = home / ".nexus-hub"
    scripts = installed / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(REPO_ROOT / "scripts/nexus_hub_cli.py", scripts / "nexus_hub_cli.py")
    shutil.copytree(
        REPO_ROOT / "scripts/lib", scripts / "lib",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    settings = home / ".claude/settings.json"
    settings.parent.mkdir()
    settings.write_text(
        json.dumps({"env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}}), encoding="utf-8"
    )
    if manifest_present:
        manifest = InstallManifest()
        manifest.track("claude", str(settings))
        manifest.record_actions("claude", [FileAction(str(settings), "created")])
        manifest.save(installed / "install-manifest.json")
    before = {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()}
    env = dict(
        os.environ, HOME=str(home), USERPROFILE=str(home), NEXUS_HUB_HOME=str(installed),
        PYTHONDONTWRITEBYTECODE="1",
    )
    env.pop("NEXUS_HUB_SRC", None)
    cmd = [sys.executable, str(scripts / "nexus_hub_cli.py"), "doctor", "--target", str(home)]
    if json_mode:
        cmd.append("--json")
    result = subprocess.run(
        cmd, cwd=tmp_path, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60, check=False,
    )
    assert result.returncode == (0 if manifest_present else 1), result.stderr
    assert "Remove only env.CLAUDE_CODE_EFFORT_LEVEL" in result.stdout
    if json_mode:
        payload = json.loads(result.stdout)
        if manifest_present:
            assert payload["counts"]["ok"] == 1
        else:
            assert payload["error"] == "no manifest"
    assert not (installed / "src").exists()
    assert {p.relative_to(home): p.read_bytes() for p in home.rglob("*") if p.is_file()} == before
