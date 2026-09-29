"""Unit tests for scripts/repo_host.py: remote parsing, host verification, cross-check.

Every external process is replaced by an in-process runner, so no case needs ssh,
gh, git, or the network.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("repo_host", REPO_ROOT / "scripts" / "repo_host.py")
assert SPEC and SPEC.loader
repo_host = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repo_host)


@pytest.fixture(autouse=True)
def _no_gh_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GH_HOST", raising=False)


def _runner(answers: dict[str, tuple[int, str]]):
    """A runner answering by the command's first two words; records every call."""
    calls: list[list[str]] = []

    def run(argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
        calls.append(argv)
        key = " ".join(Path(argv[0]).stem.split()[:1] + argv[1:2])
        return answers.get(key, (1, ""))

    run.calls = calls  # type: ignore[attr-defined]
    return run


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/acme/demo.git", ("github.com", "acme/demo", False)),
        ("https://github.com/acme/demo", ("github.com", "acme/demo", False)),
        ("https://github.com/acme/demo/", ("github.com", "acme/demo", False)),
        ("https://x-access-token:secret@github.com/acme/demo.git", ("github.com", "acme/demo", False)),
        ("https://GitHub.com:443/Acme/Demo.git", ("github.com", "Acme/Demo", False)),
        ("ssh://git@github.com/acme/demo.git", ("github.com", "acme/demo", True)),
        ("ssh://git@github.com:22/acme/demo.git", ("github.com", "acme/demo", True)),
        ("git@github.com:acme/demo.git", ("github.com", "acme/demo", True)),
        ("git@github-work:acme/demo.git", ("github-work", "acme/demo", True)),
        ("github-work:acme/demo", ("github-work", "acme/demo", True)),
    ],
)
def test_parse_remote_accepts_each_form(url: str, expected: tuple[str, str, bool]) -> None:
    assert repo_host.parse_remote(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        "/srv/git/demo.git",
        r"C:\repos\demo.git",
        "file:///srv/git/demo.git",
        "https://github.com/acme",
        "https://github.com/acme/demo/extra",
        "git@github.com:/acme/demo.git",
        "https://github.com/acme/demo.git\nhttps://github.com/evil/fork.git",
        "ssh://git@github.com:evil.com/acme/demo.git",
        "git@github.com:acme/demo/../../evil/fork.git",
        "C:owner/repo",
        "c:acme/demo.git",
    ],
)
def test_parse_remote_rejects_unparseable_urls(url: str) -> None:
    assert repo_host.parse_remote(url) is None


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.com#@github.com/acme/demo.git",
        "https://evil.com?@github.com/acme/demo.git",
        "https://evil.com\\@github.com/acme/demo.git",
        "ssh://git@evil.com#@github.com/acme/demo.git",
    ],
)
def test_an_authority_trick_never_reads_as_github(url: str) -> None:
    # git and curl end the authority at `#` or `?`, so the regex's "github.com" is not the host contacted.
    assert repo_host.parse_remote(url) is None


@pytest.mark.parametrize(
    "url",
    ["https://github.com@evil.com/acme/demo.git", "https://GITHUB.COM./acme/demo.git"],
)
def test_look_alike_hosts_stay_unverified(url: str) -> None:
    assert repo_host.repo_from_url(url, run=_runner({}), ssh="ssh") == (None, "unverified-host")


def test_literal_github_hosts_need_no_ssh() -> None:
    run = _runner({})
    for url in ("https://github.com/acme/demo.git", "git@github.com:acme/demo.git"):
        assert repo_host.repo_from_url(url, run=run, ssh="ssh") == ("acme/demo", "remote")
    assert run.calls == []


def test_a_github_alias_resolves_through_ssh_config() -> None:
    run = _runner({"ssh -G": (0, "user git\nhostname github.com\nport 22\n")})
    got = repo_host.repo_from_url("git@github-work:acme/demo.git", run=run, ssh="ssh")
    assert got == ("acme/demo", "remote-alias")
    assert run.calls == [["ssh", "-G", "github-work"]]


def test_an_ssh_url_alias_resolves_through_ssh_config() -> None:
    run = _runner({"ssh -G": (0, "hostname github.com\n")})
    got = repo_host.repo_from_url("ssh://git@github-work/acme/demo.git", run=run, ssh="ssh")
    assert got == ("acme/demo", "remote-alias")


def test_a_non_github_alias_is_never_looked_up() -> None:
    run = _runner({"ssh -G": (0, "hostname gitlab.com\n")})
    got = repo_host.repo_from_url("git@gitlab-work:acme/tool.git", run=run, ssh="ssh")
    assert got == (None, "unverified-host")


def test_an_https_host_other_than_github_is_unverified_without_ssh() -> None:
    run = _runner({"ssh -G": (0, "hostname github.com\n")})
    got = repo_host.repo_from_url("https://evilgithub.com/acme/demo.git", run=run, ssh="ssh")
    assert got == (None, "unverified-host")
    assert run.calls == []


@pytest.mark.parametrize("answer", [(1, ""), (-1, ""), (0, "user git\n")])
def test_a_failed_or_empty_ssh_answer_leaves_the_alias_unverified(answer: tuple[int, str]) -> None:
    run = _runner({"ssh -G": answer})
    got = repo_host.repo_from_url("git@github-work:acme/demo.git", run=run, ssh="ssh")
    assert got == (None, "ssh-unavailable")


def test_missing_ssh_leaves_the_alias_unverified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "")
    run = _runner({"ssh -G": (0, "hostname github.com\n")})
    assert repo_host.repo_from_url("git@github-work:acme/demo.git", run=run) == (None, "ssh-unavailable")
    assert run.calls == []


def test_an_alias_that_looks_like_an_option_is_refused() -> None:
    run = _runner({"ssh -G": (0, "hostname github.com\n")})
    got = repo_host.repo_from_url("-oProxyCommand=x:acme/demo", run=run, ssh="ssh")
    assert got[0] is None
    assert run.calls == []


def test_gh_host_is_accepted_directly_and_through_an_alias(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GH_HOST", "https://ghe.example.com/")
    run = _runner({"ssh -G": (0, "hostname ghe.example.com\n")})
    assert repo_host.repo_from_url("https://ghe.example.com/acme/demo.git", run=run, ssh="ssh")[0] == "acme/demo"
    assert repo_host.repo_from_url("git@ghe-work:acme/demo.git", run=run, ssh="ssh")[0] == "acme/demo"


def test_with_gh_host_set_a_github_com_remote_is_unverified(monkeypatch: pytest.MonkeyPatch) -> None:
    # `gh --repo acme/demo` would query GH_HOST, not the github.com repository the remote pushes to.
    monkeypatch.setenv("GH_HOST", "ghe.example.com")
    got = repo_host.repo_from_url("https://github.com/acme/demo.git", run=_runner({}), ssh="ssh")
    assert got == (None, "unverified-host")


@pytest.mark.parametrize(
    "answer",
    [
        "hostname github.com\nproxycommand nc evil.example 22\n",
        "hostname github.com\nproxyjump evil.example\n",
    ],
)
def test_an_alias_routed_through_a_proxy_is_unverified(answer: str) -> None:
    run = _runner({"ssh -G": (0, answer)})
    got = repo_host.repo_from_url("git@gh:acme/demo.git", run=run, ssh="ssh")
    assert got == (None, "ssh-unavailable")


def test_an_alias_with_proxy_set_to_none_is_accepted() -> None:
    run = _runner({"ssh -G": (0, "hostname github.com\nproxycommand none\nproxyjump none\n")})
    assert repo_host.repo_from_url("git@gh:acme/demo.git", run=run, ssh="ssh") == ("acme/demo", "remote-alias")


def _repo_answers(url: str, gh: tuple[int, str] | None) -> dict[str, tuple[int, str]]:
    answers = {"git -C": (0, url + "\n"), "ssh -G": (0, "hostname github.com\n")}
    if gh is not None:
        answers["gh repo"] = gh
    return answers


def test_resolve_repo_prefers_a_frozen_record_repo(tmp_path: Path) -> None:
    run = _runner({})
    assert repo_host.resolve_repo(tmp_path, record_repo="acme/demo", run=run) == ("acme/demo", "record")
    assert run.calls == []


def test_resolve_repo_cross_checks_with_gh(tmp_path: Path) -> None:
    run = _runner(_repo_answers("git@github.com:acme/demo.git", (0, "acme/demo\n")))
    got = repo_host.resolve_repo(tmp_path, git="git", gh="gh", run=run)
    assert got == ("acme/demo", "remote+gh")


def test_resolve_repo_refuses_when_gh_disagrees(tmp_path: Path) -> None:
    # `gh repo set-default` lives in .git/config, which an agent can write.
    run = _runner(_repo_answers("git@github.com:acme/demo.git", (0, "evil/fork\n")))
    assert repo_host.resolve_repo(tmp_path, git="git", gh="gh", run=run) == (None, "gh-disagrees")


@pytest.mark.parametrize("gh", [(1, ""), (0, ""), None])
def test_resolve_repo_keeps_the_verified_url_when_gh_cannot_answer(
    tmp_path: Path, gh: tuple[int, str] | None
) -> None:
    run = _runner(_repo_answers("git@github-work:acme/demo.git", gh))
    got = repo_host.resolve_repo(tmp_path, git="git", gh="gh" if gh else "", run=run)
    assert got == ("acme/demo", "remote-alias")


def test_resolve_repo_reports_a_missing_remote(tmp_path: Path) -> None:
    run = _runner({"git -C": (2, "")})
    assert repo_host.resolve_repo(tmp_path, git="git", gh="", run=run) == (None, "no-remote")


def test_both_installers_copy_the_resolver_beside_the_checker() -> None:
    sh = (REPO_ROOT / "scripts" / "installer.sh").read_text(encoding="utf-8")
    ps1 = (REPO_ROOT / "scripts" / "installer.ps1").read_text(encoding="utf-8")
    assert '"$scripts_dest/repo_host.py"' in sh
    assert '(Join-Path $scriptsDest "repo_host.py")' in ps1


def test_no_other_script_or_hook_parses_github_remotes_itself() -> None:
    offenders = []
    for base in (REPO_ROOT / "scripts", REPO_ROOT / "catalog" / "hooks"):
        for path in base.rglob("*"):
            if path.suffix not in {".py", ".sh", ".ps1"} or "tests" in path.parts or path.name == "repo_host.py":
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if "git@github\\.com" in text or "github\\.com[:/]" in text or "github\\.com/|" in text:
                offenders.append(path.relative_to(REPO_ROOT).as_posix())
    assert offenders == []
