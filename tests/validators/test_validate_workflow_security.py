"""Tests for scripts/validate_workflow_security.py."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


SCRIPT = "validate_workflow_security.py"


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_clean_workflow_passes(tmp_path: Path, runner) -> None:
    write(
        tmp_path / ".github" / "workflows" / "ci.yml",
        dedent(
            """\
            name: CI
            on: push
            permissions:
              contents: read
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
                  - uses: actions/setup-python@v5
                    with:
                      python-version: '3.11'
                  - run: pytest
            """
        ),
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0, result.stderr


def test_third_party_floating_ref_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / ".github" / "workflows" / "bad.yml",
        dedent(
            """\
            name: Bad
            on: push
            jobs:
              go:
                runs-on: ubuntu-latest
                steps:
                  - uses: dangerous/action@main
            """
        ),
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "moving ref" in result.stderr


def test_pull_request_target_with_head_checkout_is_flagged(
    tmp_path: Path, runner
) -> None:
    write(
        tmp_path / ".github" / "workflows" / "prtarget.yml",
        dedent(
            """\
            name: PR
            on:
              pull_request_target:
                types: [opened]
            jobs:
              build:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
                    with:
                      ref: ${{ github.event.pull_request.head.ref }}
            """
        ),
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "pull_request_target" in result.stderr


def test_script_injection_via_github_event_is_flagged(
    tmp_path: Path, runner
) -> None:
    write(
        tmp_path / ".github" / "workflows" / "inject.yml",
        dedent(
            """\
            name: Inject
            on: issue_comment
            jobs:
              go:
                runs-on: ubuntu-latest
                steps:
                  - run: |
                      echo "Title: ${{ github.event.issue.title }}"
            """
        ),
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "untrusted github.event" in result.stderr


def test_permissions_write_all_is_flagged(tmp_path: Path, runner) -> None:
    write(
        tmp_path / ".github" / "workflows" / "perms.yml",
        dedent(
            """\
            name: Perms
            on: push
            permissions: write-all
            jobs:
              go:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
            """
        ),
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 1
    assert "write-all" in result.stderr


def test_github_owned_major_tag_is_allowed(tmp_path: Path, runner) -> None:
    write(
        tmp_path / ".github" / "workflows" / "owned.yml",
        dedent(
            """\
            name: Owned
            on: push
            jobs:
              go:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v4
                  - uses: github/codeql-action/init@v3
            """
        ),
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0


def test_third_party_tag_pin_warns_not_errors(tmp_path: Path, runner) -> None:
    write(
        tmp_path / ".github" / "workflows" / "tagpin.yml",
        dedent(
            """\
            name: Tag
            on: push
            jobs:
              go:
                runs-on: ubuntu-latest
                steps:
                  - uses: third-party/action@v2.1.0
            """
        ),
    )
    result = runner(SCRIPT, tmp_path)
    assert result.returncode == 0
    assert "WARN" in result.stdout


def test_third_party_tag_pin_errors_under_strict_sha_pinning(
    tmp_path: Path, runner
) -> None:
    write(
        tmp_path / ".github" / "workflows" / "tagpin.yml",
        dedent(
            """\
            name: Tag
            on: push
            jobs:
              go:
                runs-on: ubuntu-latest
                steps:
                  - uses: third-party/action@v2.1.0
            """
        ),
    )
    result = runner(SCRIPT, tmp_path, ["--strict-sha-pinning"])
    assert result.returncode == 1
