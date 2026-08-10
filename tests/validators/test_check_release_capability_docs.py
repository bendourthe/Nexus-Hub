"""Tests for scripts/check_release_capability_docs.py.

The guard backs the capability usage gate (governance step 6 in
`catalog/commands/update.md`). It ships ADVISORY, so these tests assert both
postures explicitly: advisory always exits 0 while still reporting, and --strict
exits non-zero. A future promotion to a hard gate flips the default and these
tests are what prove the flip did what was intended.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_release_capability_docs.py"

COMPLETE = """# Release v9.9.9

### NEXUS_HUB_COPILOT_SKILLS

- Activation: set `NEXUS_HUB_COPILOT_SKILLS=1` before running the installer
- Validation: `ls .github/skills` lists one directory per bundled skill
- Rollback: unset the variable and delete `.github/skills/`
- Authority: does NOT grant Copilot any permission it lacked
- Docs: https://example.invalid/docs/copilot-skills
"""


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def notes(tmp_path: Path, body: str, name: str = "notes.md") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_all_five_elements_present_passes(tmp_path):
    p = notes(tmp_path, COMPLETE)
    r = run(str(p), "--surface", "NEXUS_HUB_COPILOT_SKILLS", "--strict")
    assert r.returncode == 0, r.stderr
    assert "all five elements present" in r.stdout


@pytest.mark.parametrize(
    "drop,expected",
    [
        ("- Authority:", "Authority"),
        ("- Rollback:", "Rollback"),
        ("- Validation:", "Validation"),
        ("- Activation:", "Activation"),
        ("- Docs:", "Docs"),
    ],
)
def test_each_missing_element_is_detected(tmp_path, drop, expected):
    body = "\n".join(l for l in COMPLETE.splitlines() if not l.startswith(drop))
    p = notes(tmp_path, body)
    r = run(str(p), "--surface", "NEXUS_HUB_COPILOT_SKILLS", "--strict")
    assert r.returncode == 1, r.stdout
    assert expected in r.stderr


def test_missing_authority_gets_the_silent_failure_hint(tmp_path):
    """Element 4 is the one that fails silently, so it earns an explicit hint."""
    body = "\n".join(l for l in COMPLETE.splitlines() if not l.startswith("- Authority:"))
    r = run(str(notes(tmp_path, body)), "--surface", "NEXUS_HUB_COPILOT_SKILLS", "--strict")
    assert "fails SILENTLY" in r.stderr


def test_advisory_is_the_default_and_never_fails(tmp_path):
    body = "\n".join(l for l in COMPLETE.splitlines() if not l.startswith("- Authority:"))
    r = run(str(notes(tmp_path, body)), "--surface", "NEXUS_HUB_COPILOT_SKILLS")
    assert r.returncode == 0
    assert "Authority" in r.stderr
    assert "advisory" in r.stderr


def test_surface_never_mentioned_is_reported(tmp_path):
    r = run(str(notes(tmp_path, COMPLETE)), "--surface", "SOME_OTHER_FLAG", "--strict")
    assert r.returncode == 1
    assert "never mentioned" in r.stderr


def test_no_change_declaration_passes(tmp_path):
    p = notes(tmp_path, "# Release\n\nThis release changes no opt-in capability.\n")
    r = run(str(p), "--expect-no-optional-capability-changes", "--strict")
    assert r.returncode == 0, r.stderr


def test_silence_is_not_a_no_change_declaration(tmp_path):
    """'Checked and none applied' must be distinguishable from 'never checked'."""
    p = notes(tmp_path, "# Release\n\nSome unrelated changes.\n")
    r = run(str(p), "--expect-no-optional-capability-changes", "--strict")
    assert r.returncode == 1
    assert "must SAY so" in r.stderr


def test_surface_and_no_change_are_mutually_exclusive(tmp_path):
    r = run(
        str(notes(tmp_path, COMPLETE)),
        "--surface",
        "X",
        "--expect-no-optional-capability-changes",
    )
    assert r.returncode == 2


def test_no_arguments_is_a_usage_error(tmp_path):
    r = run(str(notes(tmp_path, COMPLETE)))
    assert r.returncode == 2


def test_unreadable_notes_file_is_an_error(tmp_path):
    r = run(str(tmp_path / "nope.md"), "--surface", "X", "--strict")
    assert r.returncode == 2


TABLE_FORM = """# Release v9.9.9

### nexus-hub doctor

| Element | Detail |
|---|---|
| **Activation** | run `installer.sh doctor` |
| **Validation** | `installer.sh doctor; echo $?` |
| **Rollback** | read-only, nothing to undo |
| **Authority boundary** | grants nothing; makes no network call |
| **Documentation** | docs/policy/platform-read-contracts.md |
"""


def test_markdown_table_labels_are_recognized(tmp_path):
    """A table is a valid way to present five parallel elements.

    Added after the checker failed on the very release notes that introduced it.
    Rejecting the table form would push authors toward looser prose the checker
    cannot verify at all, which is the opposite of the intended effect.
    """
    r = run(str(notes(tmp_path, TABLE_FORM)), "--surface", "nexus-hub doctor", "--strict")
    assert r.returncode == 0, r.stderr + r.stdout


def test_prose_mentioning_a_synonym_is_not_a_marker(tmp_path):
    """Regression: detection must be marker-based, never substring-in-prose.

    An earlier revision also matched a bare `<synonym>:` anywhere in the block,
    so "its own readback: ..." in a sentence satisfied the Validation element by
    accident. A checker that passes on incidental prose produces confident false
    CLEARs, which is worse than having no checker.
    """
    body = """# Release

### SOME_FLAG

- Activation: set it
- Rollback: unset it
- Authority: grants nothing
- Docs: https://example.invalid

The command is its own readback: run it and check the exit code.
"""
    r = run(str(notes(tmp_path, body)), "--surface", "SOME_FLAG", "--strict")
    assert r.returncode == 1
    assert "Validation" in r.stderr


def test_multiple_surfaces_all_checked(tmp_path):
    body = COMPLETE + """
### NEXUS_HOOK_PROFILE

- Activation: set `NEXUS_HOOK_PROFILE=minimal`
"""
    r = run(
        str(notes(tmp_path, body)),
        "--surface",
        "NEXUS_HUB_COPILOT_SKILLS",
        "--surface",
        "NEXUS_HOOK_PROFILE",
        "--strict",
    )
    assert r.returncode == 1
    assert "NEXUS_HOOK_PROFILE" in r.stderr
    assert "all five elements present" in r.stdout
