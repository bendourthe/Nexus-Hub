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
