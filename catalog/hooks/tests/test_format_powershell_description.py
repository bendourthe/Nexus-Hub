"""
Tests for catalog/hooks/format-powershell-description.py

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_format_powershell_description.py -v
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# Module loading: hyphenated filename can't be imported normally.
_HOOK_FILE = Path(__file__).parent.parent / "format-powershell-description.py"
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_PERMS_FILE = _REPO_ROOT / "configs" / "permissions" / "claude-permissions.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("fpd", _HOOK_FILE)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_fpd = _load_module()

split_powershell_pipeline = _fpd.split_powershell_pipeline
command_is_allowed = _fpd.command_is_allowed
_has_disallowed_syntax = _fpd._has_disallowed_syntax
format_description_box = _fpd.format_description_box
strip_description_box = _fpd.strip_description_box
_BOX_HEADER = _fpd._BOX_HEADER
_BOX_FOOTER = _fpd._BOX_FOOTER


def _load_real_patterns() -> list[str]:
    """Load PowerShell allow patterns from the canonical permissions file."""
    data = json.loads(_PERMS_FILE.read_text(encoding="utf-8"))
    patterns: list[str] = []
    for entry in data.get("permissions", {}).get("allow", []):
        if isinstance(entry, str) and entry.startswith("PowerShell(") and entry.endswith(")"):
            inner = entry[len("PowerShell("):-1]
            inner = re.sub(r"^([^:*\s]+):\*$", r"\1 *", inner)
            patterns.append(inner)
    return patterns


REAL_PATTERNS: list[str] = _load_real_patterns()


def _run_hook(payload: dict[str, Any]) -> tuple[str, int]:
    """Run the hook script as a subprocess, returning (stdout, returncode)."""
    result = subprocess.run(
        [sys.executable, str(_HOOK_FILE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    return result.stdout, result.returncode


def _make_payload(command: str, description: str = "") -> dict[str, Any]:
    return {
        "tool_name": "PowerShell",
        "tool_input": {"command": command, "description": description},
    }


# ── Pipeline splitter ──────────────────────────────────────────────────────


class TestSplitPowershellPipeline:
    def test_simple_no_pipe(self):
        assert split_powershell_pipeline("Get-Process") == ["Get-Process"]

    def test_basic_pipe(self):
        assert split_powershell_pipeline("Get-Process | Select-Object Name") == [
            "Get-Process",
            "Select-Object Name",
        ]

    def test_three_segments(self):
        assert split_powershell_pipeline(
            "Get-Process | Where-Object Name -eq foo | Select-Object Id"
        ) == [
            "Get-Process",
            "Where-Object Name -eq foo",
            "Select-Object Id",
        ]

    def test_pipe_inside_single_quotes(self):
        assert split_powershell_pipeline("Get-Content -Path 'a|b.txt'") == [
            "Get-Content -Path 'a|b.txt'"
        ]

    def test_pipe_inside_double_quotes(self):
        assert split_powershell_pipeline('Get-Content -Path "a|b.txt"') == [
            'Get-Content -Path "a|b.txt"'
        ]

    def test_double_pipe_treated_as_split(self):
        # PS7 || pipeline-chain operator: collapse the second | into the same split.
        assert split_powershell_pipeline("Test-Path foo || Get-Content bar") == [
            "Test-Path foo",
            "Get-Content bar",
        ]

    def test_empty_string_returns_empty_list(self):
        assert split_powershell_pipeline("") == []

    def test_strips_whitespace(self):
        assert split_powershell_pipeline("  Get-Process  |  Select-Object Name  ") == [
            "Get-Process",
            "Select-Object Name",
        ]


# ── Disallowed-syntax scanner ──────────────────────────────────────────────


class TestHasDisallowedSyntax:
    @pytest.mark.parametrize(
        "cmd",
        [
            "Get-Process",
            "Get-Process -Name explorer",
            "Get-Process | Select-Object Name",
            "Get-Content -Path 'C:\\path\\file.txt'",
            "Get-Content -Path \"C:\\path\\file.txt\"",
            "Where-Object Name -eq foo",
            "Get-ChildItem -Filter *.txt -Recurse",
        ],
    )
    def test_safe_commands_pass(self, cmd):
        assert _has_disallowed_syntax(cmd) is False

    @pytest.mark.parametrize(
        "cmd",
        [
            "Get-Process; Stop-Process -Name explorer",
            "Get-Process | Where-Object {$_.Name -eq 'foo'}",
            "Get-ChildItem | ForEach-Object { Remove-Item $_ }",
            "Get-Content file.txt > out.txt",
            "Get-Content file.txt >> out.txt",
            "Get-Content < input.txt",
            'echo "hello" | Out-File "$(whoami).txt"',
            "& 'C:\\path\\to\\script.ps1'",
            "$x = $(Get-Date)",
            "@(Get-Process)",
            "Get-Process `; Stop-Process",
        ],
    )
    def test_unsafe_commands_blocked(self, cmd):
        assert _has_disallowed_syntax(cmd) is True

    def test_semicolon_inside_single_quotes_is_safe(self):
        assert _has_disallowed_syntax("Select-String -Pattern 'a;b' file.txt") is False

    def test_brace_inside_double_quotes_is_safe(self):
        assert _has_disallowed_syntax('Write-Output "literal {brace}"') is False

    def test_dollar_paren_inside_quotes_is_safe(self):
        # Inside single quotes, $(...) is literal.
        assert _has_disallowed_syntax("Write-Output 'literal $(notexec)'") is False


# ── Allow-list matcher ─────────────────────────────────────────────────────


class TestCommandIsAllowed:
    def test_empty_patterns_blocks_everything(self):
        assert command_is_allowed("Get-Process", []) is False

    def test_single_cmdlet_match(self):
        assert command_is_allowed("Get-Process", ["Get-Process", "Get-Process *"]) is True

    def test_single_cmdlet_with_args(self):
        assert (
            command_is_allowed(
                "Get-ChildItem -Path C:\\Users",
                ["Get-ChildItem", "Get-ChildItem *"],
            )
            is True
        )

    def test_pipeline_all_segments_must_match(self):
        patterns = ["Get-Process", "Get-Process *", "Select-Object", "Select-Object *"]
        assert (
            command_is_allowed("Get-Process | Select-Object Name", patterns) is True
        )

    def test_pipeline_one_segment_unmatched_blocks(self):
        patterns = ["Get-Process", "Get-Process *"]
        assert (
            command_is_allowed("Get-Process | Stop-Process -Name foo", patterns)
            is False
        )

    def test_multiline_always_blocked(self):
        patterns = ["Get-Process", "Get-Process *"]
        assert command_is_allowed("Get-Process\nGet-Process", patterns) is False

    def test_script_block_blocks_match(self):
        # Even if every cmdlet name matches, a { in the command disqualifies.
        patterns = ["Get-Process", "Where-Object *"]
        cmd = "Get-Process | Where-Object {$_.Name -eq 'foo'}"
        assert command_is_allowed(cmd, patterns) is False

    def test_redirection_blocks_match(self):
        patterns = ["Get-Content *"]
        assert command_is_allowed("Get-Content a.txt > b.txt", patterns) is False

    def test_call_operator_blocks_match(self):
        patterns = ["Get-Process"]
        assert command_is_allowed("& 'C:\\bad.exe'", patterns) is False


# ── Real-config integration: every blessed cmdlet is auto-approvable ──────


class TestRealConfigIntegration:
    """Smoke-test that the canonical allow-list in claude-permissions.json
    actually auto-approves the kinds of commands it advertises."""

    def test_at_least_one_powershell_pattern_is_configured(self):
        assert len(REAL_PATTERNS) > 0, "claude-permissions.json should have PowerShell patterns"

    @pytest.mark.parametrize(
        "cmd",
        [
            "Get-Process",
            "Get-Process -Name explorer",
            "Get-ChildItem",
            "Get-ChildItem -Path C:\\",
            "Get-ChildItem -Path C:\\ -Recurse -Filter *.txt",
            "Test-Path C:\\Users",
            "Get-Content C:\\file.txt",
            "Get-Date",
            "Get-Location",
            "$PSVersionTable",
            "Get-Process | Select-Object Name",
            "Get-Process | Where-Object Name -eq explorer",
            "Get-Process | Sort-Object CPU | Select-Object -First 5",
            "Get-ChildItem | Measure-Object",
            "ls",
            "dir C:\\",
            "cat foo.txt",
            "pwd",
            "Get-Service | Where-Object Status -eq Running | Sort-Object Name",
        ],
    )
    def test_safe_commands_auto_approve(self, cmd):
        assert command_is_allowed(cmd, REAL_PATTERNS), (
            f"Expected '{cmd}' to be auto-approved against real config"
        )

    @pytest.mark.parametrize(
        "cmd",
        [
            # script blocks must never auto-approve
            "Get-Process | Where-Object {$_.Name -eq 'foo'}",
            "Get-ChildItem | ForEach-Object { Remove-Item $_ }",
            # multi-line scripts must never auto-approve
            "Get-Process\nStop-Process -Name foo",
            # write/destructive cmdlets not in allowlist
            "Stop-Process -Name explorer",
            "Remove-Item C:\\file.txt",
            "Set-Content C:\\file.txt 'data'",
            # call operator
            "& 'C:\\path\\to\\script.ps1'",
            # subexpression
            "Write-Output $(Get-Date)",
            # statement separator
            "Get-Process; Stop-Process -Name foo",
            # I/O redirection
            "Get-Content a.txt > b.txt",
            # iex / Invoke-Expression
            "iex 'Get-Process'",
            "Invoke-WebRequest http://example.com",
            "Start-Process notepad.exe",
        ],
    )
    def test_unsafe_commands_blocked(self, cmd):
        assert not command_is_allowed(cmd, REAL_PATTERNS), (
            f"Expected '{cmd}' to be BLOCKED but was auto-approved"
        )


# ── Description box ────────────────────────────────────────────────────────


class TestFormatDescriptionBox:
    def test_basic_box_shape(self):
        out = format_description_box("Hello world", width=40)
        lines = out.split("\n")
        assert lines[0] == _BOX_HEADER
        assert lines[-1] == _BOX_FOOTER
        assert any("Hello world" in line for line in lines)
        # Each content line starts with "# "
        for line in lines[1:-1]:
            assert line.startswith("# ")

    def test_empty_text_uses_placeholder(self):
        out = format_description_box("", width=40)
        assert "(no description)" in out

    def test_long_text_wraps(self):
        long_text = "word " * 50
        out = format_description_box(long_text, width=40)
        for line in out.split("\n")[1:-1]:
            assert len(line) <= 42  # "# " + 40-col content


class TestStripDescriptionBox:
    def test_strips_top_comments(self):
        cmd = (
            f"{_BOX_HEADER}\n"
            "# This explains the command\n"
            f"{_BOX_FOOTER}\n"
            "\n"
            "Get-Process"
        )
        assert strip_description_box(cmd).strip() == "Get-Process"

    def test_no_box_returns_unchanged(self):
        assert strip_description_box("Get-Process").strip() == "Get-Process"

    def test_preserves_command_with_trailing_comments(self):
        cmd = "Get-Process  # inline comment"
        assert strip_description_box(cmd).strip() == "Get-Process  # inline comment"


# ── End-to-end subprocess tests ────────────────────────────────────────────


class TestMainIntegration:
    def test_missing_description_exits_silently(self):
        """When no description is supplied AND the command is not allowed,
        the formatter should exit silently so that
        require-powershell-description.sh blocks the call."""
        stdout, rc = _run_hook(_make_payload("Stop-Process -Name foo", description=""))
        assert rc == 0
        assert stdout.strip() == ""

    def test_with_description_renders_box_and_asks(self):
        """A description-bearing non-allowlisted command must (a) render
        the comment-block envelope into the script body, (b) explicitly
        return permissionDecision='ask' so Claude Code's PowerShell tool
        falls through to a user-approval dialog instead of executing
        silently, and (c) set permissionDecisionReason to the description
        so the dialog body surfaces it without forcing the user to
        expand the collapsible Details panel."""
        stdout, rc = _run_hook(
            _make_payload(
                "Stop-Process -Name explorer",
                description="Stops the Explorer process",
            )
        )
        assert rc == 0
        assert stdout, "expected JSON output"
        out = json.loads(stdout)
        hso = out["hookSpecificOutput"]
        updated = hso["updatedInput"]
        assert "Stop-Process -Name explorer" in updated["command"]
        assert _BOX_HEADER in updated["command"]
        assert "Stops the Explorer process" in updated["command"]
        assert hso.get("permissionDecision") == "ask", (
            "Non-allowlisted commands MUST set permissionDecision='ask' "
            "or Claude Code's PowerShell tool will auto-execute them"
        )
        assert hso.get("permissionDecisionReason") == "Stops the Explorer process", (
            "permissionDecisionReason MUST carry the description verbatim "
            "so the PowerShell approval dialog renders it under the header "
            "(the dialog hides updatedInput.command behind a collapsed "
            "Details panel, so reason is the only reliably-visible surface)"
        )

    def test_description_already_boxed_still_asks(self):
        """If the model passes a description that already starts with '#',
        we don't re-box, but we still force user approval and surface a
        useful permissionDecisionReason."""
        boxed_desc = "# already preformatted description"
        stdout, rc = _run_hook(
            _make_payload(
                "Stop-Process -Name explorer",
                description=boxed_desc,
            )
        )
        assert rc == 0
        assert stdout, "expected JSON output"
        out = json.loads(stdout)
        hso = out["hookSpecificOutput"]
        assert hso.get("permissionDecision") == "ask"
        # Strips leading '#' but still surfaces the description text
        reason = hso.get("permissionDecisionReason", "")
        assert "already preformatted description" in reason

    def test_safe_command_auto_approves(self):
        # Only meaningful when the test environment has the project
        # claude-permissions.json on-tree (it does, via load_allow_patterns
        # walking up to the repo's .claude). The hook reads from the user's
        # ~/.claude/settings.json plus the project's .claude/settings.json
        # if present.  In a clean checkout there's no .claude/settings.json
        # in the project, so the hook will fall back to the user's global.
        # We assert the matcher logic directly instead, which is independent
        # of installed user state.
        assert command_is_allowed("Get-Process | Select-Object Name", REAL_PATTERNS)
