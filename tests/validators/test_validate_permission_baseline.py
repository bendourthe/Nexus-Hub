"""Tests for the read-only permission-baseline validator (scripts/validate_permission_baseline.py).

The validator classifies allowlist entries by INVOCATION SHAPE rather than by command
name, which is the `I6` invariant: `Bash(gh api *)` looks read-only and admits
`--method DELETE`. These tests cover each detected shape for BOTH the `Bash(...)` and
the `PowerShell(...)` prefix, with a negative case per shape so the validator cannot
pass by simply rejecting everything.

Three tests here are load-bearing beyond ordinary coverage:

* `test_shipped_configs_are_clean` is the regression guard -- it fails the moment a
  mutation-capable entry re-enters a shipped baseline, which is the whole point of the
  validator existing.
* `test_powershell_syntax_set_matches_the_hook` asserts, in BOTH directions, that the
  validator's PowerShell syntax-rejection classes match what
  `catalog/hooks/format-powershell-description.py` rejects. The native matcher path and
  the hook path must not drift apart about what "read-only" means; a drift there means
  one layer auto-approves what the other blocks.
* `test_both_prefixes_are_checked_in_one_file` guards the shadowing bug a
  prefix-dispatching validator invites: a bash-only denylist silently passes every
  PowerShell regression, and the PowerShell block is the larger unaudited surface.

The module lives under scripts/ (not on the default path), so it is imported by file
location, mirroring tests/validators/test_run_trigger_evals.py.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate_permission_baseline.py"
PS_HOOK = REPO_ROOT / "catalog" / "hooks" / "format-powershell-description.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vpb = _load(VALIDATOR, "validate_permission_baseline")


def _check(entry: str, match_mode: str = "glob") -> list[str]:
    """Run the checker over one entry, returning the rule names that fired."""
    body = entry[entry.index("(") + 1 : -1]
    prefix = entry[: entry.index("(")]
    if vpb.RULE_PREFIXES[prefix] == "powershell":
        found = vpb._check_powershell_entry("t", entry, body)
    else:
        found = vpb._check_posix_entry("t", entry, body, match_mode)
    return [v.rule for v in found]


# --- POSIX shapes: each detected class, with a read-only counterpart ----------


@pytest.mark.parametrize(
    ("entry", "rule"),
    [
        # 1. literal redirection operator: `> file` truncates regardless of output
        ("Bash(echo * > *)", "redirect"),
        ("Bash(tee *)", None),  # control: no redirect operator present
        # 2. literal mutating flag or subcommand on a dual-mode tool
        ("Bash(gh api --method DELETE *)", "mutating-token"),
        ("Bash(find . -delete)", "mutating-token"),
        ("Bash(sed -i *)", "mutating-token"),
        ("Bash(sort -o *)", "mutating-token"),
        ("Bash(sysctl -w *)", "mutating-token"),
        ("Bash(ip link set *)", "mutating-token"),
        ("Bash(git push *)", "mutating-token"),
        # 3. unpinned trailing wildcard directly after a dual-mode tool name
        ("Bash(git *)", "unpinned-dual-mode-tool"),
        ("Bash(gh *)", "unpinned-dual-mode-tool"),
        ("Bash(docker *)", "unpinned-dual-mode-tool"),
        # 3b. wildcard after a dual-mode SUBCOMMAND: pinning depth 1 rescues nothing
        ("Bash(gh repo *)", "unpinned-dual-mode-subcommand"),
        ("Bash(git branch *)", "unpinned-dual-mode-subcommand"),
        ("Bash(docker volume *)", "unpinned-dual-mode-subcommand"),
        # 3b. subcommands no depth of pinning rescues, because the mutating switch is
        # a flag rather than a verb
        ("Bash(gh api *)", "unsafe-subcommand"),
        ("Bash(gh api repos/owner/repo *)", "unsafe-subcommand"),
        # 4. tools whose first argument is itself an arbitrary program
        ("Bash(awk *)", "always-unsafe-tool"),
    ],
)
def test_posix_shape_is_detected(entry: str, rule: str | None) -> None:
    rules = _check(entry)
    if rule is None:
        assert not rules, f"{entry} should be clean, got {rules}"
    else:
        assert rule in rules, f"{entry} should trip [{rule}], got {rules}"


@pytest.mark.parametrize(
    "entry",
    [
        "Bash(git log *)",        # pinned subcommand on a dual-mode tool
        "Bash(git status)",       # bare exact match: glob mode is not a prefix
        "Bash(sed -n *)",         # the reference scoping pattern for the Bash block
        "Bash(ls *)",
        "Bash(pwd)",
        "Bash(rg *)",
        "Bash(git branch --show-current)",
        # depth-2 pinning on a dual-mode subcommand: the shape every shipped entry uses
        "Bash(gh pr view *)",
        "Bash(git branch --list *)",
        "Bash(docker compose config *)",
        "Bash(git stash list)",
    ],
)
def test_genuinely_read_only_posix_entries_pass(entry: str) -> None:
    """Without these the validator could pass by rejecting everything, and the
    hardening would have to delete useful coverage to stay green."""
    assert _check(entry) == [], f"false positive on a read-only entry: {entry}"


def test_prefix_matcher_is_stricter_than_glob_matcher() -> None:
    """Gemini treats every entry as a PREFIX, so a bare tool name is NOT safe there
    even though the identical pattern is an exact match (and safe) for Claude Code.
    Getting this backwards is how `run_shell_command(find)` becomes `find . -delete`."""
    assert _check("run_shell_command(find)", "prefix"), (
        "a bare dual-mode tool name must be flagged under prefix semantics"
    )
    assert _check("Bash(find)", "glob") == [], (
        "the same pattern is an exact match under glob semantics and is safe"
    )


# --- PowerShell shapes -------------------------------------------------------


@pytest.mark.parametrize(
    ("entry", "rule"),
    [
        # outright-mutating cmdlets
        ("PowerShell(Set-Content *)", "powershell-mutating-cmdlet"),
        ("PowerShell(Invoke-Expression *)", "powershell-mutating-cmdlet"),
        ("PowerShell(Remove-Item *)", "powershell-mutating-cmdlet"),
        ("PowerShell(Start-Process *)", "powershell-mutating-cmdlet"),
        # ...reached through their aliases, because Claude Code canonicalizes
        # aliases BEFORE matching, so a cmdlet-name-only denylist misses these
        ("PowerShell(sc *)", "powershell-mutating-cmdlet"),
        ("PowerShell(iex *)", "powershell-mutating-cmdlet"),
        ("PowerShell(iwr *)", "powershell-mutating-cmdlet"),
        ("PowerShell(rm *)", "powershell-mutating-cmdlet"),
        # dual-mode getters whose returned objects expose mutating methods
        ("PowerShell(Get-CimInstance *)", "powershell-unpinned-dual-mode"),
        ("PowerShell(Get-WmiObject *)", "powershell-unpinned-dual-mode"),
        # remote retargeting turns a local read into a remote one
        ("PowerShell(Get-Process -ComputerName *)", "powershell-remote-target"),
        # syntax classes the hook path rejects
        ("PowerShell(Get-ChildItem; Remove-Item x)", "powershell-syntax"),
        ("PowerShell(Get-Content * > *)", "powershell-syntax"),
        ("PowerShell(& Get-Item *)", "powershell-syntax"),
    ],
)
def test_powershell_shape_is_detected(entry: str, rule: str) -> None:
    assert rule in _check(entry), f"{entry} should trip [{rule}], got {_check(entry)}"


@pytest.mark.parametrize(
    "entry",
    [
        "PowerShell(Get-ChildItem *)",
        "PowerShell(Get-Content *)",
        "PowerShell(Get-Location)",
        "PowerShell(Select-String *)",
        "PowerShell(Get-CimInstance -ClassName Win32_OperatingSystem)",  # class pinned
        "PowerShell(sl *)",  # Set-Location, NOT Set-Content: a known false-positive trap
    ],
)
def test_genuinely_read_only_powershell_entries_pass(entry: str) -> None:
    assert _check(entry) == [], f"false positive on a read-only entry: {entry}"


def test_alias_table_does_not_confuse_set_location_with_set_content() -> None:
    """`sl` is Set-Location (harmless, and present in the shipped baseline). Mapping it
    to Set-Content would fail the shipped config on a legitimate entry."""
    assert vpb._canonical_cmdlet("sl") != "set-content"
    assert vpb._canonical_cmdlet("sc") == "set-content"


# --- Cross-layer consistency: validator vs. the hook path --------------------


def test_powershell_syntax_set_matches_the_hook() -> None:
    """Asserted BEHAVIORALLY and in both directions.

    Forward: every class the validator rejects, the hook also rejects -- otherwise the
    validator forbids a pattern the hook would happily auto-approve.
    Reverse: a control set of characters the validator does NOT list must be accepted
    by the hook -- otherwise the hook is stricter than the validator and a pattern that
    passes `make validate` is dead on the hook path.
    """
    hook = _load(PS_HOOK, "format_powershell_description")

    for syntax in vpb.PS_DISALLOWED_SYNTAX:
        assert hook._has_disallowed_syntax(f"Get-Item {syntax}"), (
            f"validator rejects `{syntax}` but the hook accepts it; the native path "
            f"and the hook path disagree about what read-only means"
        )

    # Not in the validator's set, and must not be in the hook's either. `|` is a real
    # pipeline the hook splits and checks per-subcommand rather than rejecting.
    for allowed in ("|", "-Path", "'quoted'", '"double"', "$var"):
        assert not hook._has_disallowed_syntax(f"Get-Item {allowed}"), (
            f"the hook rejects `{allowed}` but the validator does not list it"
        )


# --- End-to-end CLI ----------------------------------------------------------


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        capture_output=True, text=True, check=False, cwd=REPO_ROOT,
    )


def test_shipped_configs_are_clean() -> None:
    """The regression guard: the hardened baselines must pass with no arguments."""
    proc = _run()
    assert proc.returncode == 0, (
        f"shipped permission baseline is not read-only:\n{proc.stdout}\n{proc.stderr}"
    )


def _fixture(tmp_path: Path, entries: list[str]) -> Path:
    path = tmp_path / "perms.json"
    path.write_text(json.dumps({"permissions": {"allow": entries}}), encoding="utf-8")
    return path


def test_cli_fails_and_names_the_offending_entry(tmp_path: Path) -> None:
    path = _fixture(tmp_path, ["Read", "Bash(gh api *)"])
    proc = _run(str(path))
    assert proc.returncode == 1
    assert "Bash(gh api *)" in proc.stderr, "the failure must name the entry"


@pytest.mark.parametrize(
    "entry",
    ["PowerShell(Set-Content *)", "PowerShell(Invoke-Expression *)",
     "PowerShell(Get-WmiObject *)"],
)
def test_cli_fails_on_each_powershell_fixture(tmp_path: Path, entry: str) -> None:
    proc = _run(str(_fixture(tmp_path, [entry])))
    assert proc.returncode == 1, f"{entry} passed the CLI"
    assert entry in proc.stderr


def test_both_prefixes_are_checked_in_one_file(tmp_path: Path) -> None:
    """Neither prefix may shadow the other: a bash-only denylist silently passes every
    future PowerShell regression."""
    path = _fixture(tmp_path, ["Bash(gh api *)", "PowerShell(Set-Content *)"])
    proc = _run(str(path))
    assert proc.returncode == 1
    assert "Bash(gh api *)" in proc.stderr
    assert "PowerShell(Set-Content *)" in proc.stderr


def test_metadata_block_is_not_mistaken_for_a_rule(tmp_path: Path) -> None:
    """The `_hardening` audit block documents REMOVED entries, so treating its strings
    as rules would fail the very file that records the fix."""
    path = tmp_path / "perms.json"
    path.write_text(
        json.dumps({
            "_hardening": {"removed": ["Bash(gh api *)", "PowerShell(Set-Content *)"]},
            "permissions": {"allow": ["Read"]},
        }),
        encoding="utf-8",
    )
    assert _run(str(path)).returncode == 0


def test_cli_reports_usage_error_for_a_missing_file(tmp_path: Path) -> None:
    proc = _run(str(tmp_path / "absent.json"))
    assert proc.returncode == 2, "a missing file is a usage error, not a violation"


def test_gemini_config_is_checked_under_prefix_semantics() -> None:
    """Gemini's matcher is a prefix matcher, and the default target list must say so;
    checking it as a glob matcher would miss the bare-tool-name class entirely."""
    modes = dict(vpb.DEFAULT_TARGETS)
    assert modes["configs/permissions/gemini-permissions.json"] == "prefix"
    assert modes["configs/permissions/claude-permissions.json"] == "glob"
