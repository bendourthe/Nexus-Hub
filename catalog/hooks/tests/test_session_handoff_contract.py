"""Contract tests for the session-handoff skill and the /handoff command.

The handoff is a paste-ready prompt printed in the chat. It is read by a
different agent on a different platform, and its header line is parsed by the
next handoff's carry-forward step, so its format is a cross-platform contract
rather than prose. No handoff file is written unless the user explicitly asks
for one in that invocation, and the milestone checkpoint mode is retired.
These tests pin that contract in the skill and command text, and exercise the
two shell procedures the skill tells an agent to run (the exclude rule and the
secret scan, which reads the composed text on standard input) against real
temporary git repositories, including a linked worktree where `.git` is a file.

Run with: pytest catalog/hooks/tests/test_session_handoff_contract.py -q
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SKILL = _REPO_ROOT / "catalog" / "skills" / "workflow" / "session-handoff" / "SKILL.md"
_COMMAND = _REPO_ROOT / "catalog" / "commands" / "handoff.md"

# The ordered section contract from plan sub-task 4.2.
REQUIRED_SECTIONS = [
    "## Goal",
    "## Done and verified",
    "## In progress",
    "## Next steps",
    "## Files touched",
    "## Constraints and decisions the user stated",
    "## Open questions and blockers",
    "## Repository state",
]

# The header grammar carry-forward parses: `# Handoff | TIMESTAMP | PLATFORM | TRIGGER`.
HEADER_RE = re.compile(
    r"^# Handoff \| (?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) \| (?P<platform>[a-z0-9-]+) \| "
    r"(?P<trigger>manual|usage-limit (?:five_hour|weekly|monthly) \d+(?:\.\d+)?)$"
)


def _skill_text() -> str:
    return _SKILL.read_text(encoding="utf-8")


def _format_template() -> str:
    """Return the four-backtick markdown block that defines the file format."""
    match = re.search(r"^````markdown\n(.*?)^````$", _skill_text(), re.S | re.M)
    assert match, "the skill must define the file format in a ````markdown block"
    return match.group(1)


def _fenced_block_containing(needle: str, lang: str) -> str:
    for match in re.finditer(rf"^```{lang}\n(.*?)^```$", _skill_text(), re.S | re.M):
        if needle in match.group(1):
            return match.group(1)
    raise AssertionError(f"no ```{lang} block containing {needle!r}")


def test_the_format_template_lists_every_section_in_order() -> None:
    headings = [line for line in _format_template().splitlines() if line.startswith("## ")]
    assert headings == REQUIRED_SECTIONS


def test_the_verification_checklist_names_the_same_order() -> None:
    text = _skill_text()
    verification = text.split("## Verification", 1)[1].split("## Related Skills", 1)[0]
    positions = [verification.find(f"`{section}`") for section in REQUIRED_SECTIONS]
    assert -1 not in positions, "every section must be named in Verification"
    assert positions == sorted(positions)


def test_the_template_header_line_matches_the_parseable_grammar() -> None:
    first_line = _format_template().splitlines()[0]
    assert HEADER_RE.match(first_line), first_line


@pytest.mark.parametrize(
    "line, ok",
    [
        ("# Handoff | 2026-10-01T14:03:27Z | claude | manual", True),
        ("# Handoff | 2026-10-01T14:03:27Z | codex | checkpoint", False),
        ("# Handoff | 2026-10-01T14:03:27Z | copilot | usage-limit monthly 99", True),
        ("# Handoff | 2026-10-01T14:03:27Z | claude | usage-limit hourly 99", False),
        ("# Handoff | 2026-10-01 14:03 | claude | manual", False),
    ],
)
def test_the_header_grammar_accepts_only_documented_triggers(line: str, ok: bool) -> None:
    assert bool(HEADER_RE.match(line)) is ok


def test_the_skill_documents_the_header_grammar_and_modes() -> None:
    text = _skill_text()
    assert "`# Handoff | TIMESTAMP | PLATFORM | TRIGGER`" in text
    for trigger in ("`manual`", "`usage-limit WINDOW PERCENT`"):
        assert trigger in text


def _modes_table() -> list[str]:
    section = _skill_text().split("### Modes and delivery", 1)[1].split("### Step 0", 1)[0]
    return [line for line in section.splitlines() if line.startswith("| ") and "---" not in line]


def test_checkpoint_mode_is_retired() -> None:
    """No agent writes handoff state after milestones: the modes are manual and
    usage-limit only, and the skill says the checkpoint is gone."""
    rows = _modes_table()
    modes = [row.split("|")[1].strip() for row in rows[1:]]
    assert modes == ["manual", "usage-limit"]
    text = _skill_text()
    assert "there is no rolling checkpoint" in text
    assert "checkpoint mode" not in text
    assert "after a verified milestone" not in text


def test_the_default_delivery_is_the_chat_and_writes_no_file() -> None:
    text = _skill_text()
    assert "**Default: chat only.** Print the prompt in the chat (Step 7). Write no file." in text
    assert "Print one fenced block in the chat" in text
    assert "no file was written" in text
    verification = text.split("## Verification", 1)[1]
    assert "no handoff file was created or changed" in verification


def test_a_file_is_written_only_on_an_explicit_request_in_that_invocation() -> None:
    text = _skill_text()
    assert "**File only on explicit request.**" in text
    assert "`/handoff file`" in text and "`/handoff file PATH`" in text
    assert "never a standing preference" in text
    step8 = text.split("### Step 8", 1)[1].split("### Resuming", 1)[0]
    assert "Skip this step unless the user explicitly asked for a file in this invocation" in step8
    assert "`.nexus-hub/handoff.md`" in step8
    assert "Print the prompt (Step 7) as well" in step8


def test_a_legacy_file_is_carried_forward_and_never_deleted() -> None:
    text = _skill_text()
    step3 = text.split("### Step 3", 1)[1].split("### Step 4", 1)[0]
    assert "A pasted prompt" in step3 and "A legacy file" in step3
    assert "can be deleted" in step3
    assert "Never delete it yourself." in step3


def test_the_skill_prohibits_secrets_and_scans_the_printed_prompt() -> None:
    text = _skill_text()
    assert "Never include secrets, tokens" in text
    assert "egress-redaction" in text
    assert "Before printing the prompt, scan the composed text" in text
    block = _fenced_block_containing("grep -nE", "bash")
    assert "<<'HANDOFF_TEXT'" in block, "the scan reads the text on stdin, not a file"
    assert ".nexus-hub/handoff.md" not in block


def test_the_skill_uses_the_resolved_exclude_path_and_never_gitignore() -> None:
    text = _skill_text()
    assert "git rev-parse --git-path info/exclude" in text
    assert "Never edit `.gitignore`" in text
    for lang in ("bash", "powershell"):
        block = _fenced_block_containing("check-ignore", lang)
        assert "--git-path info/exclude" in block
        assert ".gitignore" not in block


def test_the_skill_carries_forward_unfinished_steps() -> None:
    text = _skill_text()
    assert "Carry forward every unfinished item" in text
    assert "(carried from PLATFORM TIMESTAMP)" in text
    assert "Previous handoffs:" in text
    # A requested file re-reads its target first, so a concurrent writer's steps survive.
    assert "last writer wins" in text


def test_the_prompt_carries_the_handoff_and_tells_the_receiver_to_verify() -> None:
    text = _skill_text()
    for marker in ("--- handoff begins ---", "--- handoff ends ---"):
        assert marker in text
    assert "Verify the Repository state" in text
    assert "Do not redo anything under Done and verified" in text
    # The receiver must not resume the retired checkpoint habit.
    assert "Do not write handoff files as you work." in text
    assert "Keep .nexus-hub/handoff.md current" not in text


def test_a_committed_or_future_dated_handoff_is_never_followed_as_instructions() -> None:
    """A repository can commit a `.nexus-hub/handoff.md` with a far-future header;
    neither the carry-forward step nor the receiving agent may let it outrank the
    pasted prompt or the user."""
    text = _skill_text()
    assert text.count("git ls-files --error-unmatch .nexus-hub/handoff.md") >= 2
    assert "later than the current time" in text
    assert "ask which to follow" in text


def test_the_usage_limit_mode_stops_new_work() -> None:
    assert "start no new work" in _skill_text()


def test_the_command_is_a_thin_dispatcher_to_the_skill() -> None:
    text = _COMMAND.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    assert "description:" in frontmatter and "SKIP" in frontmatter
    assert "(any invocation) -> session-handoff" in text
    assert "Pass any remaining arguments through unchanged" in text


def test_the_command_promises_the_chat_prompt_and_a_file_only_on_request() -> None:
    text = _COMMAND.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    assert "in the chat" in frontmatter and "no file is written unless you ask" in frontmatter
    assert "No file is written." in text
    assert "`/handoff file`" in text
    assert "An earlier request never carries over" in text
    assert "Write .nexus-hub/handoff.md" not in text


# ---------------------------------------------------------------------------
# Procedures exercised against real repositories
# ---------------------------------------------------------------------------

_GIT = shutil.which("git")
needs_git = pytest.mark.skipif(_GIT is None, reason="git is not installed")


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_GIT or "git", *args], cwd=cwd, capture_output=True, text=True, check=False
    )


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "t@example.invalid")
    _git(path, "config", "user.name", "t")
    (path / "a.txt").write_text("a\n", encoding="utf-8")
    _git(path, "add", "a.txt")
    _git(path, "commit", "-q", "-m", "init")
    return path


def _run_exclude_snippet(bash_bin: str, cwd: Path) -> None:
    snippet = _fenced_block_containing("check-ignore", "bash")
    result = subprocess.run(
        [bash_bin, "-c", snippet], cwd=cwd, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


@needs_git
def test_the_exclude_snippet_ignores_the_directory_without_gitignore(
    bash_bin: str, tmp_path: Path
) -> None:
    repo = _init_repo(tmp_path / "repo")
    _run_exclude_snippet(bash_bin, repo)
    _run_exclude_snippet(bash_bin, repo)  # idempotent: second run appends nothing
    assert _git(repo, "check-ignore", "-q", ".nexus-hub/handoff.md").returncode == 0
    assert not (repo / ".gitignore").exists()
    exclude = (repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert exclude.count(".nexus-hub/") == 1


@needs_git
def test_the_exclude_snippet_works_in_a_linked_worktree(
    bash_bin: str, tmp_path: Path
) -> None:
    repo = _init_repo(tmp_path / "repo")
    worktree = tmp_path / "wt"
    assert _git(repo, "worktree", "add", "-q", str(worktree)).returncode == 0
    assert (worktree / ".git").is_file()
    _run_exclude_snippet(bash_bin, worktree)
    assert _git(worktree, "check-ignore", "-q", ".nexus-hub/handoff.md").returncode == 0
    assert not (worktree / ".gitignore").exists()


def _run_secret_scan(bash_bin: str, cwd: Path, text: str) -> subprocess.CompletedProcess[str]:
    """Run the documented scan with the composed handoff on standard input, as the
    skill's here-document does, so the scan needs no file."""
    block = _fenced_block_containing("grep -nE", "bash")
    scan = next(line for line in block.splitlines() if line.startswith("grep -nE"))
    command = scan.split(" <<'HANDOFF_TEXT'", 1)[0]
    assert command != scan, "the scan must read a here-document"
    return subprocess.run(
        [bash_bin, "-c", command], cwd=cwd, input=text, capture_output=True, text=True, check=False
    )


@pytest.mark.parametrize(
    "secret",
    [
        "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8",
        "github_pat_" + "11ABCDEFG0123456789_abcdefghij",
        "sk-" + "proj-abcdefghijklmnopqrstuv",
        "AKIA" + "ABCDEFGHIJKLMNOP",
        "-----BEGIN " + "RSA PRIVATE KEY-----",
        "sk_" + "live_abcdefghijklmnopqrstuvwx",
        "AIza" + "SyA1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q",
        "glpat-" + "abcdefghijklmnopqrst",
        "password" + "=hunter2hunter2",
    ],
)
def test_the_secret_scan_flags_secret_shaped_strings(
    bash_bin: str, tmp_path: Path, secret: str
) -> None:
    result = _run_secret_scan(bash_bin, tmp_path, f"## Goal\n\nDeploy with {secret}\n")
    assert result.returncode == 0 and result.stdout.strip(), "scan must print the match"
    assert not (tmp_path / ".nexus-hub").exists(), "the scan writes no handoff file"


def test_the_secret_scan_is_quiet_on_the_documented_example(
    bash_bin: str, tmp_path: Path
) -> None:
    result = _run_secret_scan(bash_bin, tmp_path, _format_template())
    assert result.stdout == "", result.stdout


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
