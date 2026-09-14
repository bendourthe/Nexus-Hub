"""Exercise attribution enforcement using isolated Git repositories and messages."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/check_commit_attribution.py"
SPEC = importlib.util.spec_from_file_location("check_commit_attribution", SCRIPT)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
TARGET = checker.TARGET
CURSOR = ("Cursor Agent", "cursoragent@cursor.com")


def git(root: Path, *args: str, **kwargs) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, **kwargs
    ).strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Never inherit the maintainer's hooks, signing settings or identity overrides.
    for key in list(os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.name", TARGET[0])
    git(root, "config", "user.email", TARGET[1])
    return root


def commit(root: Path, author=TARGET, committer=TARGET, message="Fixture") -> str:
    env = os.environ | {
        "GIT_AUTHOR_NAME": author[0],
        "GIT_AUTHOR_EMAIL": author[1],
        "GIT_COMMITTER_NAME": committer[0],
        "GIT_COMMITTER_EMAIL": committer[1],
    }
    git(
        root,
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        message,
        env=env,
    )
    return git(root, "rev-parse", "HEAD")


def scan(root: Path, *args: str) -> int:
    return checker.main(["--all-refs", "--root", str(root), *args])


@pytest.mark.parametrize(
    "author,committer,expected",
    [
        (TARGET, TARGET, 0),
        (CURSOR, TARGET, 1),
        (TARGET, CURSOR, 1),
        (TARGET, checker.GITHUB, 0),
        (checker.GITHUB, TARGET, 1),
        (("Unknown", "unknown@example.test"), TARGET, 1),
        (("Ben Dourthe", "benjamin.dourthe@gmail.com"), TARGET, 1),
        ((TARGET[0], TARGET[1].upper()), TARGET, 0),
        (("Wrong name", TARGET[1]), TARGET, 1),
    ],
)
def test_identities(repo: Path, author, committer, expected: int) -> None:
    commit(repo, author, committer)
    assert scan(repo) == expected


@pytest.mark.parametrize(
    "trailer,expected",
    [
        ("Co-authored-by: Cursor Agent <cursoragent@cursor.com>", 1),
        ("co-AUTHORED-by: Claude <noreply@anthropic.com>", 1),
        ("Made-with: Cursor", 1),
        ("Made-with: Unknown <unknown@example.test>", 1),
        ("Co-authored-by:\n Cursor Agent <cursoragent@cursor.com>", 1),
        ("Co-authored-by: Ben Dourthe <" + TARGET[1] + ">", 0),
        ("Co-authored-by: Ben Dourthe <" + TARGET[1] + ">\n injected extra author", 1),
        ("Co-authored-by:", 1),
        ("Explain how cursoragent trailers are rejected.", 0),
        ("Co-authored-by: Ben Dourthe <" + TARGET[1] + ">\n\n Indented prose", 0),
    ],
)
def test_trailers(repo: Path, tmp_path: Path, trailer: str, expected: int) -> None:
    message = "Fixture\n\n" + trailer
    commit(repo, message=message)
    path = tmp_path / "message"
    path.write_text(message, encoding="utf-8")
    assert scan(repo) == expected
    assert checker.main(["--message-file", str(path)]) == expected


@pytest.mark.parametrize("ref_type", ["branch", "tag", "annotated-tag"])
def test_unmerged_refs_are_scanned(repo: Path, ref_type: str) -> None:
    commit(repo)
    git(repo, "checkout", "-q", "-b", "side")
    commit(repo, author=CURSOR)
    if ref_type == "tag":
        git(repo, "tag", "historical")
    elif ref_type == "annotated-tag":
        git(repo, "tag", "-a", "historical", "-m", "Fixture tag")
    git(repo, "checkout", "-q", "main")
    if ref_type != "branch":
        git(repo, "branch", "-D", "side")
    assert scan(repo) == 1


def test_shallow_clone_is_error(repo: Path, tmp_path: Path, capsys) -> None:
    commit(repo)
    commit(repo)
    clone = tmp_path / "shallow"
    git(tmp_path, "clone", "-q", "--depth=1", repo.as_uri(), str(clone))
    assert scan(clone) == 2
    assert "shallow" in capsys.readouterr().err


def test_bare_clone_is_scanned(repo: Path, tmp_path: Path) -> None:
    commit(repo)
    clone = tmp_path / "mirror.git"
    git(tmp_path, "clone", "-q", "--mirror", str(repo), str(clone))
    assert scan(clone) == 0


def test_replacement_and_mailmap_cannot_hide_author(repo: Path) -> None:
    bad = commit(repo, author=CURSOR)
    clean = commit(repo)
    git(repo, "replace", bad, clean)
    (repo / ".mailmap").write_text(
        f"{TARGET[0]} <{TARGET[1]}> <{CURSOR[1]}>\n", encoding="utf-8"
    )
    assert scan(repo) == 1


def test_grafts_fail_closed(repo: Path) -> None:
    sha = commit(repo)
    (repo / ".git/info/grafts").write_text(sha + "\n", encoding="ascii")
    assert scan(repo) == 2


@pytest.mark.parametrize(
    "dirty_history,dirty_message", [(True, False), (False, True), (True, True)]
)
def test_both_modes_report_findings(
    repo: Path, tmp_path: Path, capsys, dirty_history, dirty_message
) -> None:
    commit(repo, author=CURSOR if dirty_history else TARGET)
    message = tmp_path / "message"
    message.write_text(
        "Co-authored-by: Agent <agent@example.test>" if dirty_message else "Clean",
        encoding="utf-8",
    )
    assert scan(repo, "--message-file", str(message)) == 1
    output = capsys.readouterr().out
    assert ("cursoragent@cursor.com" in output) == dirty_history
    assert ("agent@example.test" in output) == dirty_message


def test_error_does_not_hide_other_mode_findings(tmp_path: Path, capsys) -> None:
    message = tmp_path / "message"
    message.write_text("Made-with: Cursor", encoding="utf-8")
    assert scan(tmp_path, "--message-file", str(message)) == 2
    output = capsys.readouterr()
    assert "Cursor" in output.out and "incomplete" in output.err


def test_missing_git(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    commit(repo)
    monkeypatch.setenv("PATH", "")
    assert scan(repo) == 2


@pytest.mark.parametrize("kind", ["missing", "directory", "invalid-utf8"])
def test_unreadable_message(tmp_path: Path, kind: str) -> None:
    message = tmp_path / "message"
    if kind == "directory":
        message.mkdir()
    elif kind == "invalid-utf8":
        message.write_bytes(b"\xff")
    assert checker.main(["--message-file", str(message)]) == 2


def test_empty_repo_is_not_history_proof(repo: Path) -> None:
    assert scan(repo) == 2


@pytest.mark.parametrize(
    "raw", [b"", b"unterminated", b"too\0few\0", b"invalid\0a\0b\0c\0d\0msg\0"]
)
def test_malformed_git_output(
    repo: Path, monkeypatch: pytest.MonkeyPatch, raw: bytes
) -> None:
    def output(root, *args):
        if args == ("rev-parse", "--is-shallow-repository"):
            return b"false\n"
        if args == ("rev-parse", "--git-path", "info/grafts"):
            return b".git/info/grafts\n"
        return raw

    monkeypatch.setattr(checker, "git", output)
    assert scan(repo) == 2


def test_cli_and_usage(repo: Path) -> None:
    commit(repo)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--all-refs", "--root", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        result.returncode == 0
        and "1 commits scanned; 0 findings; 0 errors" in result.stdout
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 2 and "specify" in result.stderr


def test_bounded_diagnostics_keep_total(repo: Path, capsys) -> None:
    for index in range(11):
        commit(repo, author=CURSOR, committer=CURSOR, message=str(index))
    assert scan(repo) == 1
    output = capsys.readouterr().out
    assert "22 findings" in output and "2 additional findings" in output
