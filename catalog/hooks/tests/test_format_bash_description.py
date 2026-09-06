"""
Comprehensive tests for catalog/hooks/format-bash-description.py

Run from the repo root:
    python -m pytest catalog/hooks/tests/ -v

Integration tests (class TestMainIntegration) require ~/.claude/settings.json
to be installed with the Nexus-Hub permission list so the hook can load allow
patterns.  Unit tests (all other classes) are fully self-contained.
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

# ── Module loading ─────────────────────────────────────────────────────────
# The hyphenated filename cannot be imported with a normal `import` statement.

_HOOK_FILE = Path(__file__).parent.parent / "format-bash-description.py"
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_PERMS_FILE = _REPO_ROOT / "configs" / "permissions" / "claude-permissions.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("fbd", _HOOK_FILE)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


_fbd = _load_module()

split_compound_command = _fbd.split_compound_command
command_is_allowed = _fbd.command_is_allowed
format_description_prefix = _fbd.format_description_prefix
strip_description_box = _fbd.strip_description_box
_PREFIX_MAX_LEN = _fbd._PREFIX_MAX_LEN


# ── Helpers ────────────────────────────────────────────────────────────────


def _load_real_patterns() -> list[str]:
    """Load Bash allow patterns from configs/permissions/claude-permissions.json."""
    data = json.loads(_PERMS_FILE.read_text(encoding="utf-8"))
    patterns: list[str] = []
    for entry in data.get("permissions", {}).get("allow", []):
        if isinstance(entry, str) and entry.startswith("Bash(") and entry.endswith(")"):
            inner = entry[5:-1]
            inner = re.sub(r"^([^:*\s]+):\*$", r"\1 *", inner)
            patterns.append(inner)
    return patterns


REAL_PATTERNS: list[str] = _load_real_patterns()

# Fixed pattern list for tests about the PARSER's structural handling (compound
# commands, if/else, loops, prefix variable assignments) rather than about catalog
# policy.
#
# v3.17.0 Phase 1: these tests used REAL_PATTERNS with `echo` as filler in their loop
# and branch bodies, so the Phase 1.1 hardening -- which removed `Bash(echo *)`,
# `Bash(cat *)`, and `Bash(printf *)` because Claude Code's built-in read-only set
# already covers them with real redirect analysis -- broke 7 parser tests that have
# nothing to do with which commands the catalog ships. Pinning them to a fixed list
# keeps each test measuring the one thing it was written to measure, and stops the next
# catalog-policy change from breaking them again. Tests that ARE about policy keep
# using REAL_PATTERNS.
STRUCTURAL_PATTERNS: list[str] = [
    "echo", "echo *", "ls", "ls *", "cd", "cd *", "wc", "wc *",
    "basename", "basename *", "git status", "git status *",
    # Condition commands used by the if/elif fixtures. Both forms are present in the
    # real baseline, so this list mirrors it rather than inventing an allowance.
    "[ *", "test *",
]


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
        "tool_name": "Bash",
        "tool_input": {"command": command, "description": description},
    }


# ══════════════════════════════════════════════════════════════════════════
# A.  split_compound_command
# ══════════════════════════════════════════════════════════════════════════


class TestSplitCompoundCommand:
    """Verify that the shell splitter correctly identifies top-level operators
    while ignoring operators that appear inside quotes or command substitutions.
    """

    # ── Baseline ──────────────────────────────────────────────────────────

    def test_simple_command_no_operators(self):
        assert split_compound_command("git status") == ["git status"]

    def test_empty_string_returns_empty_list(self):
        assert split_compound_command("") == []

    def test_whitespace_only_returns_empty_list(self):
        assert split_compound_command("   ") == []

    # ── Operator splitting ────────────────────────────────────────────────

    def test_and_and_split(self):
        parts = split_compound_command("cd /tmp && ls")
        assert parts == ["cd /tmp", "ls"]

    def test_or_or_split(self):
        parts = split_compound_command("git describe --tags || echo none")
        assert len(parts) == 2
        assert parts[0] == "git describe --tags"
        assert parts[1] == "echo none"

    def test_pipe_split(self):
        parts = split_compound_command('find . -name "*.py" | head -5')
        assert len(parts) == 2
        assert parts[0] == 'find . -name "*.py"'
        assert parts[1] == "head -5"

    def test_triple_pipeline(self):
        parts = split_compound_command("find . | xargs grep -l foo | head -20")
        assert len(parts) == 3
        assert parts[0] == "find ."
        assert parts[1] == "xargs grep -l foo"
        assert parts[2] == "head -20"

    def test_semicolon_chain(self):
        parts = split_compound_command("cmd1; cmd2; cmd3")
        assert len(parts) == 3

    def test_and_and_then_pipe(self):
        parts = split_compound_command("cd /tmp && find . | head -5")
        assert len(parts) == 3
        assert parts[0] == "cd /tmp"
        assert parts[1] == "find ."
        assert parts[2] == "head -5"

    # ── Quoted strings: operators inside must NOT split ───────────────────

    def test_pipe_inside_double_quotes_no_split(self):
        """| inside "…" must not split the command."""
        parts = split_compound_command('grep "def\\|import" file.py')
        assert len(parts) == 1

    def test_pipe_inside_single_quotes_no_split(self):
        """| inside '…' must not split the command."""
        parts = split_compound_command("grep 'def|import' file.py")
        assert len(parts) == 1

    def test_and_and_inside_double_quotes_no_split(self):
        """&& inside "…" must not split the command."""
        parts = split_compound_command('echo "foo && bar"')
        assert len(parts) == 1

    def test_semicolon_inside_single_quotes_no_split(self):
        """; inside '…' must not split the command."""
        parts = split_compound_command("awk '{print $1; print $2}' file.txt")
        assert len(parts) == 1

    def test_windows_quoted_path_with_spaces(self):
        """Double-quoted Windows path containing spaces must not split."""
        cmd = 'cd "c:\\path\\with spaces" && git status'
        parts = split_compound_command(cmd)
        assert len(parts) == 2
        assert parts[0].startswith("cd ")
        assert parts[1] == "git status"

    def test_format_string_with_space_in_double_quotes(self):
        """--format="%H %s" (space inside quotes) must not split."""
        cmd = 'git log --format="%H %s" 2>/dev/null'
        parts = split_compound_command(cmd)
        assert len(parts) == 1

    # ── Backtick substitution: operators inside must NOT split ────────────

    def test_pipe_inside_backtick_no_split(self):
        """| inside `…` must not be treated as a top-level split."""
        parts = split_compound_command("echo `date | cut -d' ' -f1`")
        assert len(parts) == 1

    def test_and_and_inside_backtick_no_split(self):
        """&& inside `…` must not split."""
        parts = split_compound_command("result=`cmd1 && cmd2`")
        assert len(parts) == 1

    # ── $() command substitution: operators inside must NOT split ─────────

    def test_or_inside_command_substitution_no_split(self):
        """|| inside $(…) must not be treated as a top-level split."""
        cmd = (
            "git log $(git describe --tags --abbrev=0 2>/dev/null"
            " || git rev-list --max-parents=0 HEAD)..HEAD"
        )
        parts = split_compound_command(cmd)
        assert len(parts) == 1

    def test_and_and_inside_command_substitution_no_split(self):
        """&& inside $(…) must not split."""
        parts = split_compound_command("echo $(cmd1 && cmd2)")
        assert len(parts) == 1

    def test_pipe_inside_command_substitution_no_split(self):
        """| inside $(…) must not split."""
        parts = split_compound_command("result=$(find . | head -1)")
        assert len(parts) == 1

    def test_nested_command_substitution_no_split(self):
        """Nested $(…) must all be treated as one word."""
        parts = split_compound_command("echo $(echo $(date))")
        assert len(parts) == 1

    # ── $((…)) arithmetic expansion ───────────────────────────────────────

    def test_or_inside_arithmetic_expansion_no_split(self):
        """|| inside $((…)) is arithmetic, not an operator split."""
        parts = split_compound_command("result=$((a || b)) && echo $result")
        assert len(parts) == 2
        assert parts[0] == "result=$((a || b))"
        assert parts[1] == "echo $result"

    def test_and_inside_arithmetic_expansion_no_split(self):
        """&& inside $((…)) must not split."""
        parts = split_compound_command("echo $((a && b))")
        assert len(parts) == 1

    # ── Shell control constructs: not split on internal operators ─────────

    def test_for_loop_preserved_as_one_part(self):
        parts = split_compound_command("for f in *.py; do echo $f; done")
        assert len(parts) == 1

    def test_if_construct_preserved_as_one_part(self):
        parts = split_compound_command("if [ -f foo ]; then cat foo; fi")
        assert len(parts) == 1

    def test_while_loop_preserved_as_one_part(self):
        parts = split_compound_command("while read line; do echo $line; done")
        assert len(parts) == 1

    # ── Redirection: must NOT split ───────────────────────────────────────

    def test_stderr_redirect_not_a_split(self):
        """2>/dev/null must not split the command."""
        parts = split_compound_command("grep foo file 2>/dev/null")
        assert len(parts) == 1

    def test_stdout_redirect_not_a_split(self):
        """> file must not split — > is not a shell operator the tokenizer tracks."""
        parts = split_compound_command("echo hello >output.txt")
        assert len(parts) == 1

    # ── Real-world user-reported commands ────────────────────────────────

    def test_screenshot1_git_log_with_subshell_or(self):
        """Exact pattern from screenshot 1: cd && git log ... $(… || …)..HEAD.

        Uses a generic Windows path containing spaces and dashes
        (OneDrive-style sync folder) -- the test verifies the splitter
        handles whitespace inside a quoted cd target.
        """
        cmd = (
            'cd "c:\\Users\\testuser\\OneDrive - Acme Corp\\Documents'
            '\\workspace\\demo-repo" && git log --oneline --no-merges '
            "$(git describe --tags --abbrev=0 2>/dev/null"
            " || git rev-list --max-parents=0 HEAD)..HEAD"
            ' --format="%H %s" 2>/dev/null'
        )
        parts = split_compound_command(cmd)
        assert len(parts) == 2
        assert parts[0].startswith("cd ")
        assert parts[1].startswith("git log ")

    def test_screenshot2_find_pipe_xargs_grep_pipe_head(self):
        """Exact pattern from screenshot 2: find | xargs grep | head."""
        cmd = (
            'find "/c/src/core" -name "__init__.py" -type f'
            ' | xargs grep -l "def\\|import" | head -20'
        )
        parts = split_compound_command(cmd)
        assert len(parts) == 3
        assert parts[0].startswith("find ")
        assert parts[1].startswith("xargs grep")
        assert parts[2] == "head -20"

    def test_screenshot3_sed_n_single_command(self):
        """Exact pattern from screenshot 3: sed -n (read-only line extraction)."""
        cmd = "sed -n '162,195p' \"/path/to/file_extraction.py\" 2>/dev/null"
        parts = split_compound_command(cmd)
        assert len(parts) == 1
        assert parts[0].startswith("sed -n")

    def test_git_log_commit_range_with_fallback(self):
        """Common generate-changelog pattern with $() fallback."""
        cmd = (
            "git log --oneline --no-merges "
            "$(git describe --tags --abbrev=0 2>/dev/null"
            " || git rev-list --max-parents=0 HEAD)..HEAD"
            ' --format="%H %s" 2>/dev/null'
        )
        parts = split_compound_command(cmd)
        assert len(parts) == 1
        assert parts[0].startswith("git log")


# ══════════════════════════════════════════════════════════════════════════
# B.  command_is_allowed
# ══════════════════════════════════════════════════════════════════════════


class TestCommandIsAllowed:
    """Verify allow-list matching against the real permission file.

    Positive cases must be True (auto-approved).
    Negative cases must be False (user must approve).
    """

    # ── Positive: commands that must be auto-approved ─────────────────────

    def test_git_status(self):
        assert command_is_allowed("git status", REAL_PATTERNS)

    def test_git_status_with_args(self):
        assert command_is_allowed("git status --short", REAL_PATTERNS)

    def test_git_log_oneline(self):
        assert command_is_allowed("git log --oneline", REAL_PATTERNS)

    def test_git_diff(self):
        assert command_is_allowed("git diff HEAD", REAL_PATTERNS)

    def test_git_show(self):
        assert command_is_allowed("git show HEAD", REAL_PATTERNS)

    def test_git_branch(self):
        assert command_is_allowed("git branch -a", REAL_PATTERNS)

    def test_git_describe(self):
        assert command_is_allowed("git describe --tags --abbrev=0", REAL_PATTERNS)

    def test_git_blame(self):
        assert command_is_allowed("git blame README.md", REAL_PATTERNS)

    def test_git_shortlog(self):
        assert command_is_allowed("git shortlog --summary", REAL_PATTERNS)

    def test_git_stash_list(self):
        assert command_is_allowed("git stash list", REAL_PATTERNS)

    def test_git_worktree_list(self):
        assert command_is_allowed("git worktree list", REAL_PATTERNS)

    def test_git_rev_parse(self):
        assert command_is_allowed("git rev-parse HEAD", REAL_PATTERNS)

    def test_git_ls_files(self):
        assert command_is_allowed("git ls-files --others", REAL_PATTERNS)

    def test_grep_pattern(self):
        assert command_is_allowed("grep -r 'import' src/", REAL_PATTERNS)

    def test_head(self):
        assert command_is_allowed("head -20 file.txt", REAL_PATTERNS)

    def test_tail(self):
        assert command_is_allowed("tail -f log.txt", REAL_PATTERNS)

    def test_ls(self):
        assert command_is_allowed("ls -la", REAL_PATTERNS)

    def test_wc(self):
        assert command_is_allowed("wc -l file.txt", REAL_PATTERNS)

    def test_cd(self):
        assert command_is_allowed("cd /tmp", REAL_PATTERNS)

    def test_pwd(self):
        assert command_is_allowed("pwd", REAL_PATTERNS)

    def test_sed_n_read_only(self):
        """sed -n is strictly read-only (suppressed output, no -i flag)."""
        assert command_is_allowed(
            "sed -n '162,195p' \"/path/to/file.py\" 2>/dev/null",
            REAL_PATTERNS,
        )

    def test_xargs_grep(self):
        assert command_is_allowed("xargs grep -l 'import'", REAL_PATTERNS)

    def test_xargs_grep_with_pattern(self):
        assert command_is_allowed('xargs grep -l "def\\|import"', REAL_PATTERNS)

    def test_xargs_wc(self):
        assert command_is_allowed("xargs wc -l", REAL_PATTERNS)

    def test_xargs_head(self):
        assert command_is_allowed("xargs head -5", REAL_PATTERNS)

    def test_xargs_cat(self):
        assert command_is_allowed("xargs cat", REAL_PATTERNS)

    def test_xargs_ls(self):
        assert command_is_allowed("xargs ls -la", REAL_PATTERNS)

    def test_xargs_file(self):
        assert command_is_allowed("xargs file", REAL_PATTERNS)

    def test_xargs_stat(self):
        assert command_is_allowed("xargs stat", REAL_PATTERNS)

    def test_jq_basic(self):
        assert command_is_allowed("jq '.data[]' file.json", REAL_PATTERNS)

    def test_jq_stdin(self):
        assert command_is_allowed("jq '.'", REAL_PATTERNS)

    def test_cut(self):
        assert command_is_allowed("cut -d',' -f1 file.csv", REAL_PATTERNS)

    def test_tr(self):
        assert command_is_allowed("tr '[:upper:]' '[:lower:]'", REAL_PATTERNS)

    def test_basename(self):
        assert command_is_allowed("basename /path/to/file.py", REAL_PATTERNS)

    def test_dirname(self):
        assert command_is_allowed("dirname /path/to/file.py", REAL_PATTERNS)

    def test_type(self):
        assert command_is_allowed("type python3", REAL_PATTERNS)

    def test_ps(self):
        assert command_is_allowed("ps aux", REAL_PATTERNS)

    def test_df(self):
        assert command_is_allowed("df -h", REAL_PATTERNS)

    # ── Binary inspection ─────────────────────────────────────────────────

    def test_od_basic(self):
        assert command_is_allowed("od -c file.bin", REAL_PATTERNS)

    def test_od_hex(self):
        assert command_is_allowed("od -x data.bin", REAL_PATTERNS)

    def test_hexdump(self):
        assert command_is_allowed("hexdump -C file.bin", REAL_PATTERNS)

    def test_xxd(self):
        assert command_is_allowed("xxd file.bin", REAL_PATTERNS)

    def test_strings(self):
        assert command_is_allowed("strings binary", REAL_PATTERNS)

    # ── Archive inspection ────────────────────────────────────────────────

    def test_tar_list(self):
        assert command_is_allowed("tar -tf archive.tar.gz", REAL_PATTERNS)

    def test_unzip_list(self):
        assert command_is_allowed("unzip -l archive.zip", REAL_PATTERNS)

    # ── Checksums ─────────────────────────────────────────────────────────

    def test_sha256sum(self):
        assert command_is_allowed("sha256sum file.txt", REAL_PATTERNS)

    def test_md5sum(self):
        assert command_is_allowed("md5sum file.txt", REAL_PATTERNS)

    def test_shasum(self):
        assert command_is_allowed("shasum -a 256 file.txt", REAL_PATTERNS)

    def test_cksum(self):
        assert command_is_allowed("cksum file.txt", REAL_PATTERNS)

    # ── Compression read ──────────────────────────────────────────────────

    def test_zcat(self):
        assert command_is_allowed("zcat file.gz", REAL_PATTERNS)

    def test_gzip_list(self):
        assert command_is_allowed("gzip -l archive.gz", REAL_PATTERNS)

    # ── System info ───────────────────────────────────────────────────────

    def test_uptime(self):
        assert command_is_allowed("uptime", REAL_PATTERNS)

    def test_hostname(self):
        assert command_is_allowed("hostname", REAL_PATTERNS)

    def test_id(self):
        assert command_is_allowed("id", REAL_PATTERNS)

    def test_groups(self):
        assert command_is_allowed("groups", REAL_PATTERNS)

    # ── Compound positive cases ───────────────────────────────────────────

    def test_cd_and_git_log(self):
        assert command_is_allowed("cd /tmp && git log --oneline", REAL_PATTERNS)

    def test_screenshot1_full_command(self):
        """cd && git log … $(… || …)..HEAD must be auto-approved."""
        cmd = (
            'cd "c:\\Users\\testuser\\OneDrive - Acme Corp\\Documents'
            '\\workspace\\demo-repo" && git log --oneline --no-merges '
            "$(git describe --tags --abbrev=0 2>/dev/null"
            " || git rev-list --max-parents=0 HEAD)..HEAD"
            ' --format="%H %s" 2>/dev/null'
        )
        assert command_is_allowed(cmd, REAL_PATTERNS)

    def test_screenshot3_sed_n_full_command(self):
        """sed -n full command from screenshot 3 must be auto-approved."""
        cmd = (
            "sed -n '162,195p' "
            '"c:/Users/testuser/OneDrive - Acme Corp/Documents/workspace/'
            'demo-repo/src/core/common/file_extraction.py"'
            " 2>/dev/null"
        )
        assert command_is_allowed(cmd, REAL_PATTERNS)

    def test_cd_then_sed_linux_path_with_spaces(self):
        """Linux-style absolute path with embedded spaces must be auto-approved."""
        cmd = (
            "cd '/home/testuser/Projects - 2026/demo-repo'"
            " && sed -n '20,40p' src/main.py"
        )
        assert command_is_allowed(cmd, REAL_PATTERNS)

    def test_cd_then_git_log_macos_path_with_spaces(self):
        """macOS-style absolute path with spaces (iCloud-Drive convention) must be auto-approved."""
        cmd = (
            "cd '/Users/testuser/Library/Mobile Documents/"
            "com~apple~CloudDocs/Projects/demo-repo'"
            " && git log --oneline -n 20"
        )
        assert command_is_allowed(cmd, REAL_PATTERNS)

    def test_git_log_with_jq(self):
        assert command_is_allowed(
            "git log --format='%H %s' | head -20", REAL_PATTERNS
        )

    def test_od_pipeline_auto_approved(self):
        """Regression: cd && sed -n … | od -c | head must be auto-approved.

        Uses Git-Bash-style escaped-space syntax (`\\ `) to confirm the
        tokenizer handles backslash-escaped whitespace inside an unquoted
        cd target.
        """
        cmd = (
            "cd /c/Users/testuser/OneDrive\\ -\\ Acme\\ Corp/Documents/workspace/demo-repo"
            " && sed -n '309,322p' extensions/example-extension/src/extension.ts"
            " | od -c | head -50"
        )
        assert command_is_allowed(cmd, REAL_PATTERNS)

    # ── Negative: commands that must NOT be auto-approved ─────────────────

    # v3.17.0 Phase 1.1 moved the next four out of the positive section. These commands
    # are not read-only at the side-effect level, so the hardening removed their patterns
    # from the baseline (the I6 invariant: classify by what an invocation CAN do, not by
    # the command's name):
    #   * awk executes its program argument -- awk 'BEGIN{print > "/path"}' writes a file.
    #   * find admits -delete, -exec, -execdir, -fprint and -fprintf, and no prefix
    #     pinning can exclude a flag that appears later in the command.
    #
    # Little real capability is lost, which is why the removal was the right trade:
    # Claude Code auto-approves a BUILT-IN read-only set that already includes find (and
    # echo, cat, head) using real semantic analysis, and prompts on exactly the dangerous
    # forms -- find with -exec or -delete, and unquoted globs for write-capable commands.
    # That analysis is strictly better than the glob it replaced. This hook only stops
    # PRE-approving; it never denies, so the platform's own read-only handling still
    # applies. See docs/releases/v3/v3.17/development/permission-matcher-findings.md, findings 3
    # and 5. The last test guards the blast radius: the rest of the pipeline vocabulary
    # must survive the find removals.

    def test_awk_not_auto_approved(self):
        """awk executes its program argument, so it can write files."""
        assert not command_is_allowed("awk '{print $1}' file.txt", REAL_PATTERNS)

    def test_find_pipe_head_not_auto_approved(self):
        assert not command_is_allowed("find . -name '*.py' | head -10", REAL_PATTERNS)

    def test_find_pipe_xargs_grep_pipe_head_not_auto_approved(self):
        """Exact failing command from screenshot 2 must now be allowed."""
        cmd = (
            'find "/c/src/core" -name "__init__.py" -type f'
            ' | xargs grep -l "def\\|import" | head -20'
        )
        assert not command_is_allowed(cmd, REAL_PATTERNS)

    def test_find_pipe_xargs_wc_not_auto_approved(self):
        assert not command_is_allowed(
            "find . -name '*.py' | xargs wc -l", REAL_PATTERNS
        )

    # Same class, Tier B of the same hardening: find, cat and echo are all in Claude
    # Code's built-in read-only set, which analyzes redirects for real. A glob entry for
    # them could only WIDEN the grant past that analysis (echo * admits `echo x > file`),
    # so removing them is coverage-neutral and security-positive.

    def test_find_basic_not_auto_approved(self):
        assert not command_is_allowed("find . -name '*.py'", REAL_PATTERNS)

    def test_cat_not_auto_approved(self):
        assert not command_is_allowed("cat README.md", REAL_PATTERNS)

    def test_echo_not_auto_approved(self):
        assert not command_is_allowed("echo hello", REAL_PATTERNS)

    def test_head_still_auto_approved_on_its_own(self):
        assert command_is_allowed("head -10 file.py", REAL_PATTERNS)

    def test_npm_install_not_allowed(self):
        assert not command_is_allowed("npm install", REAL_PATTERNS)

    def test_rm_not_allowed(self):
        assert not command_is_allowed("rm -rf /", REAL_PATTERNS)

    def test_sed_without_n_not_allowed(self):
        """sed without -n can be destructive (pipes output, changes content)."""
        assert not command_is_allowed("sed 's/foo/bar/' file.py", REAL_PATTERNS)

    def test_sed_i_not_allowed(self):
        """sed -i modifies files in place — must NOT be auto-approved."""
        assert not command_is_allowed(
            "sed -i 's/foo/bar/' file.py", REAL_PATTERNS
        )

    def test_compound_with_disallowed_part_not_allowed(self):
        assert not command_is_allowed("cd /tmp && npm install", REAL_PATTERNS)

    def test_xargs_rm_not_allowed(self):
        """xargs rm is destructive — must not be auto-approved."""
        assert not command_is_allowed("find . | xargs rm -rf", REAL_PATTERNS)

    def test_xargs_mv_not_allowed(self):
        """xargs mv is destructive — must not be auto-approved."""
        assert not command_is_allowed("find . | xargs mv {} /tmp/", REAL_PATTERNS)

    def test_tee_not_allowed(self):
        """tee writes to files — must not be auto-approved."""
        assert not command_is_allowed("cat file | tee output.txt", REAL_PATTERNS)

    def test_python_script_not_allowed(self):
        """Executing a Python script is not a read-only operation."""
        assert not command_is_allowed("python script.py", REAL_PATTERNS)

    def test_node_script_not_allowed(self):
        assert not command_is_allowed("node server.js", REAL_PATTERNS)

    def test_git_push_not_allowed(self):
        assert not command_is_allowed("git push origin main", REAL_PATTERNS)

    def test_git_commit_not_allowed(self):
        assert not command_is_allowed("git commit -m 'msg'", REAL_PATTERNS)

    def test_git_reset_not_allowed(self):
        assert not command_is_allowed("git reset --hard HEAD", REAL_PATTERNS)

    def test_empty_patterns_never_allows(self):
        assert not command_is_allowed("git status", [])

    def test_empty_command_not_allowed(self):
        """An empty / whitespace-only command should not be auto-approved."""
        assert not command_is_allowed("", REAL_PATTERNS)
        assert not command_is_allowed("   ", REAL_PATTERNS)

    def test_tar_extract_not_allowed(self):
        """tar -xf extracts files — destructive, must not be auto-approved."""
        assert not command_is_allowed("tar -xf archive.tar.gz", REAL_PATTERNS)

    def test_tar_czf_not_allowed(self):
        """tar -czf creates archives — destructive, must not be auto-approved."""
        assert not command_is_allowed("tar -czf out.tar.gz dir/", REAL_PATTERNS)


# ══════════════════════════════════════════════════════════════════════════
# B2.  Edge-case fixes: variable assignments, else/elif, select
# ══════════════════════════════════════════════════════════════════════════


class TestVariableAssignmentAllowance:
    """Variable assignments of the form VAR=$(cmd) must be unwrapped so that
    the embedded command is checked against the allow list, not the raw
    assignment string.  Regression tests for the for-loop false-negative.
    """

    def test_var_assign_with_command_substitution(self):
        """count=$(ls -d */) should be allowed when ls * is in the list."""
        assert command_is_allowed(
            'count=$(ls -d "dir"/*/ 2>/dev/null | wc -l)', REAL_PATTERNS
        )

    def test_var_assign_with_simple_substitution(self):
        """result=$(git log --oneline) should be allowed."""
        assert command_is_allowed("result=$(git log --oneline)", REAL_PATTERNS)

    def test_plain_var_assign_allowed(self):
        """FOO=bar (plain literal assignment, no command) should be allowed."""
        assert command_is_allowed("FOO=bar", REAL_PATTERNS)

    def test_prefix_var_assign_followed_by_command(self):
        """FOO=bar echo hello -- prefix assignment before allowed command."""
        assert command_is_allowed("FOO=bar echo hello", STRUCTURAL_PATTERNS)

    def test_for_loop_with_var_assign_body(self):
        """The exact command that triggered the original false-negative."""
        cmd = (
            "for category in catalog/skills/*/; do "
            'count=$(ls -d "$category"*/ 2>/dev/null | wc -l); '
            'echo "$(basename "$category"): $count"; '
            "done"
        )
        assert command_is_allowed(cmd, STRUCTURAL_PATTERNS)

    def test_cd_then_for_loop_with_var_assign(self):
        """Full compound command from the bug report."""
        cmd = (
            r"cd /c/Users/testuser/OneDrive\ -\ Acme\ Corp/Documents/demo-repo"
            " && for category in catalog/skills/*/; do"
            ' count=$(ls -d "$category"*/ 2>/dev/null | wc -l);'
            ' echo "$(basename "$category"): $count";'
            " done"
        )
        assert command_is_allowed(cmd, STRUCTURAL_PATTERNS)

    def test_var_assign_with_dangerous_inner_cmd_blocked(self):
        """OUT=$(rm -rf /tmp) must still be blocked despite the assignment wrapper."""
        assert not command_is_allowed("OUT=$(rm -rf /tmp)", REAL_PATTERNS)

    def test_var_assign_inner_git_push_blocked(self):
        """Dangerous command inside $() must be blocked."""
        assert not command_is_allowed("RESULT=$(git push origin main)", REAL_PATTERNS)


class TestIfElseAllowance:
    """if/else blocks must be auto-approved when all branches are safe."""

    def test_simple_if_then(self):
        assert command_is_allowed(
            "if [ -f foo.txt ]; then echo yes; fi", STRUCTURAL_PATTERNS
        )

    def test_if_then_else(self):
        """else branch must also be checked and not cause a false negative."""
        assert command_is_allowed(
            "if [ -f foo.txt ]; then echo yes; else echo no; fi", STRUCTURAL_PATTERNS
        )

    def test_if_elif_else(self):
        assert command_is_allowed(
            "if [ -f a ]; then echo a; elif [ -f b ]; then echo b; else echo c; fi",
            STRUCTURAL_PATTERNS,
        )

    def test_if_else_with_dangerous_branch_blocked(self):
        """Dangerous command in else branch must block the whole construct."""
        assert not command_is_allowed(
            "if [ -f foo ]; then echo ok; else rm -rf /tmp/x; fi", REAL_PATTERNS
        )


class TestSelectConstruct:
    """select is a valid bash loop and should be treated as a shell opener."""

    def test_select_loop_allowed(self):
        assert command_is_allowed(
            "select opt in a b c; do echo \"$opt\"; done", STRUCTURAL_PATTERNS
        )

    def test_select_with_dangerous_body_blocked(self):
        assert not command_is_allowed(
            "select opt in a b; do rm -rf /tmp; done", REAL_PATTERNS
        )


# ══════════════════════════════════════════════════════════════════════════
# C.  format_description_prefix
# ══════════════════════════════════════════════════════════════════════════


class TestFormatDescriptionPrefix:
    """The prefix is the single-line replacement for the legacy 4-line box.

    The single-line shape is load-bearing for cross-surface rendering:
    surfaces that show the tool input as raw JSON would otherwise turn
    embedded ``\\n`` into literal escape text. Every assertion below
    guards a property the rendering depends on.
    """

    def test_no_newline_in_prefix(self):
        """A single-line prefix MUST contain no `\\n` so it renders cleanly
        even on surfaces that escape JSON string newlines."""
        out = format_description_prefix("Short description.")
        assert "\n" not in out

    def test_starts_with_desc_marker(self):
        assert format_description_prefix("Anything").startswith("# Description: ")

    def test_empty_input_uses_placeholder(self):
        assert format_description_prefix("") == "# Description: (none provided)"

    def test_whitespace_only_input_uses_placeholder(self):
        assert format_description_prefix("   \t  ") == "# Description: (none provided)"

    def test_content_is_present_in_prefix(self):
        out = format_description_prefix("Read files from disk")
        assert "Read files from disk" in out

    def test_collapses_internal_newlines_to_single_space(self):
        out = format_description_prefix("line one\nline two\nline three")
        assert "\n" not in out
        assert "line one line two line three" in out

    def test_collapses_internal_tabs_and_runs(self):
        out = format_description_prefix("a\t\tb   c\n\nd")
        assert out == "# Description: a b c d"

    def test_long_input_truncates_with_ellipsis(self):
        long_text = "x" * (_PREFIX_MAX_LEN + 50)
        out = format_description_prefix(long_text)
        assert "\n" not in out
        assert out.startswith("# Description: ")
        assert out.endswith("...")
        # Total length: "# Description: " (8 chars) + at most _PREFIX_MAX_LEN
        assert len(out) - len("# Description: ") <= _PREFIX_MAX_LEN

    def test_input_at_max_length_not_truncated(self):
        text = "x" * _PREFIX_MAX_LEN
        out = format_description_prefix(text)
        assert not out.endswith("...")
        assert text in out


# ══════════════════════════════════════════════════════════════════════════
# D.  strip_description_box
# ══════════════════════════════════════════════════════════════════════════


class TestStripDescriptionBox:

    def test_command_without_prefix_unchanged(self):
        cmd = "git status"
        assert strip_description_box(cmd) == cmd

    def test_prefix_removed_leaving_command(self):
        prefix = format_description_prefix("List files")
        full = prefix + "\n" + "git status"
        assert strip_description_box(full) == "git status"

    def test_extra_blank_lines_between_prefix_and_command_stripped(self):
        prefix = format_description_prefix("List files")
        full = prefix + "\n\n\n\ngit status"
        assert strip_description_box(full) == "git status"

    def test_multiline_command_preserved_after_stripping_prefix(self):
        prefix = format_description_prefix("Run two echoes")
        cmd = "echo foo\necho bar"
        result = strip_description_box(prefix + "\n" + cmd)
        assert "echo foo" in result
        assert "echo bar" in result

    def test_roundtrip_prefix_then_strip(self):
        """format then strip must recover the original command."""
        original = "find . -name '*.py' | head -10"
        prefix = format_description_prefix("Find Python files")
        full = prefix + "\n" + original
        assert strip_description_box(full) == original

    def test_strips_legacy_box_format(self):
        """Mid-conversation safety net: a command still carrying the legacy
        four-line `# ===== Description ===== #` box from a previous hook
        version MUST strip cleanly so the new prefix can be applied on top
        without doubling up."""
        legacy = (
            "# ===== Description ===== #\n"
            "# Old box-style description\n"
            "# ======================= #\n"
            "\n"
            "git status"
        )
        assert strip_description_box(legacy) == "git status"

    def test_strips_legacy_box_with_multiline_content(self):
        """Legacy box could wrap descriptions across multiple `# ` lines."""
        legacy = (
            "# ===== Description ===== #\n"
            "# First wrapped line\n"
            "# Second wrapped line\n"
            "# ======================= #\n"
            "\n"
            "echo hello"
        )
        assert strip_description_box(legacy) == "echo hello"

    def test_strips_underscore_separator(self):
        """The legacy `# Description: <text>\\n___\\n<command>` shape must
        still strip cleanly. The underscore-only separator line is dropped
        along with the description comment so retries do not double-wrap."""
        prefix = format_description_prefix("List Python files")
        full = prefix + "\n___\n" + "find . -name '*.py'"
        assert strip_description_box(full) == "find . -name '*.py'"

    def test_strips_commented_underscore_divider(self):
        """The intermediate `# Description: <text>\\n# ___\\n<command>` shape
        (with an underscore divider commented out so bash does not execute it)
        must still strip cleanly. The commented divider line is dropped by
        the leading-`#` rule. Back-compat for sessions formatted before the
        divider switched to dashes."""
        prefix = format_description_prefix("List Python files")
        full = prefix + "\n# ___\n" + "find . -name '*.py'"
        assert strip_description_box(full) == "find . -name '*.py'"

    def test_strips_commented_dash_divider(self):
        """The current `# Description: <text>\\n# ---\\n<command>` shape
        (with a dash divider commented out so bash does not execute it) must
        strip cleanly. The commented divider line is dropped by the
        leading-`#` rule."""
        prefix = format_description_prefix("List Python files")
        full = prefix + "\n# ---\n" + "find . -name '*.py'"
        assert strip_description_box(full) == "find . -name '*.py'"

    def test_strips_full_current_shape_roundtrip(self):
        """Exact round-trip: format the prefix as `main()` does it, prepend
        with `\\n# ---\\n`, then strip. The original command must come back
        byte-identical."""
        original = "find . -name '*.py' | head -10"
        prefix = format_description_prefix("Find Python files")
        full = prefix + "\n# ---\n" + original
        assert strip_description_box(full) == original

    def test_strips_underscore_separator_of_varying_widths(self):
        """The strip rule matches any underscore-only line, not just three
        underscores. This is defensive: if a future hook bumps the divider
        to `_____` (or a user crafts a longer line) the strip still drops it."""
        for divider in ("__", "___", "_____", "_" * 40):
            prefix = format_description_prefix("Show status")
            full = prefix + "\n" + divider + "\n" + "git status"
            assert strip_description_box(full) == "git status", (
                f"Failed to strip divider {divider!r}"
            )


# ══════════════════════════════════════════════════════════════════════════
# E.  main() integration  (subprocess — requires installed settings)
# ══════════════════════════════════════════════════════════════════════════


class TestMainIntegration:
    """End-to-end tests that invoke the hook as a subprocess.

    These tests require ~/.claude/settings.json to be installed with the
    Nexus-Hub permission list.  They will be skipped automatically if that
    file is not found.
    """

    _SETTINGS = Path.home() / ".claude" / "settings.json"

    @pytest.fixture(autouse=True)
    def require_settings(self):
        if not self._SETTINGS.exists():
            pytest.skip("~/.claude/settings.json not installed — skipping integration tests")

    def test_allowed_command_returns_permission_allow(self):
        stdout, rc = _run_hook(_make_payload("git status"))
        assert rc == 0
        data = json.loads(stdout)
        decision = data.get("hookSpecificOutput", {}).get("permissionDecision", "")
        assert decision == "allow"

    def test_allowed_command_has_no_description_prefix(self):
        stdout, rc = _run_hook(_make_payload("git log --oneline"))
        assert rc == 0
        updated_cmd = (
            json.loads(stdout)
            .get("hookSpecificOutput", {})
            .get("updatedInput", {})
            .get("command", "")
        )
        assert not updated_cmd.startswith("# Description:")

    def test_non_allowed_with_description_prepends_prefix(self):
        payload = _make_payload("npm install", description="Install project dependencies")
        stdout, rc = _run_hook(payload)
        assert rc == 0
        updated_cmd = (
            json.loads(stdout)
            .get("hookSpecificOutput", {})
            .get("updatedInput", {})
            .get("command", "")
        )
        assert updated_cmd.startswith("# Description: ")
        assert "Install project dependencies" in updated_cmd
        # Two newlines added by the hook: prefix line + `# ---` separator
        # line + original command body. The command body here is
        # "npm install" with zero newlines, so total newline count = 2.
        assert updated_cmd.count("\n") == 2
        # The commented `# ---` separator line is present between prefix
        # and command; the leading `#` keeps bash from executing it.
        assert "\n# ---\n" in updated_cmd

    def test_non_allowed_without_description_produces_no_json(self):
        """No description → hook exits 0 with no JSON so require-description.sh blocks."""
        stdout, rc = _run_hook(_make_payload("npm install", description=""))
        assert rc == 0
        assert stdout.strip() == ""

    def test_command_already_has_prefix_not_double_wrapped(self):
        prefix = format_description_prefix("Already formatted")
        cmd = prefix + "\n" + "npm install"
        payload = _make_payload(cmd, description="Already formatted")
        stdout, rc = _run_hook(payload)
        assert rc == 0
        if stdout.strip():
            updated_cmd = (
                json.loads(stdout)
                .get("hookSpecificOutput", {})
                .get("updatedInput", {})
                .get("command", cmd)
            )
            assert updated_cmd.count("# Description:") <= 1

    def test_malformed_json_exits_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(_HOOK_FILE)],
            input="not valid json {{{",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_screenshot1_command_auto_approved(self):
        cmd = (
            'cd "c:\\Users\\testuser\\OneDrive - Acme Corp\\Documents'
            '\\workspace\\demo-repo" && git log --oneline --no-merges '
            "$(git describe --tags --abbrev=0 2>/dev/null"
            " || git rev-list --max-parents=0 HEAD)..HEAD"
            ' --format="%H %s" 2>/dev/null'
        )
        stdout, rc = _run_hook(_make_payload(cmd))
        assert rc == 0
        decision = (
            json.loads(stdout)
            .get("hookSpecificOutput", {})
            .get("permissionDecision", "")
        )
        assert decision == "allow"

    def test_screenshot2_command_auto_approved(self):
        cmd = (
            'find "/c/src/core" -name "__init__.py" -type f'
            ' | xargs grep -l "def\\|import" | head -20'
        )
        stdout, rc = _run_hook(_make_payload(cmd))
        assert rc == 0
        decision = (
            json.loads(stdout)
            .get("hookSpecificOutput", {})
            .get("permissionDecision", "")
        )
        assert decision == "allow"

    def test_screenshot3_command_auto_approved(self):
        cmd = (
            "sed -n '162,195p' "
            '"c:/Users/testuser/OneDrive - Acme Corp/Documents/workspace/'
            'demo-repo/src/core/common/file_extraction.py"'
            " 2>/dev/null"
        )
        stdout, rc = _run_hook(_make_payload(cmd))
        assert rc == 0
        decision = (
            json.loads(stdout)
            .get("hookSpecificOutput", {})
            .get("permissionDecision", "")
        )
        assert decision == "allow"
