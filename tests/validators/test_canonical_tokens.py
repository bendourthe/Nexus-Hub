r"""Scope, code, and id tokens must be canonical ASCII with no trailing newline (ADV-4).

A `$` anchor matches before a trailing newline and `\d` matches any Unicode
digit, so `v4.13\n` or `v4.1` followed by an Arabic-Indic three validated as a
minor and could key a second record for the same minor. Every validator is now
anchored with `\Z` and compiled with `re.ASCII`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import approval_binding  # noqa: E402
import approval_page  # noqa: E402
import check_plan_completion  # noqa: E402
import completion_minor  # noqa: E402

VALIDATORS = [
    ("completion_minor.MINOR_RE", completion_minor.MINOR_RE, "v4.13"),
    ("completion_minor.PLAN_TOKEN_RE", completion_minor.PLAN_TOKEN_RE, "v4.13.6"),
    ("completion_minor.GAP_ID_RE", completion_minor.GAP_ID_RE, "v4.13#WN-3"),
    ("completion_minor.BRANCH_RE", completion_minor.BRANCH_RE, "feat/x"),
    ("approval_page.SCOPE_RE", approval_page.SCOPE_RE, "v4.13"),
    ("approval_page.MINOR_RE", approval_page.MINOR_RE, "v4.13"),
    ("approval_page.CODE_RE", approval_page.CODE_RE, "ABCD2345"),
    ("approval_page.GAP_ID_RE", approval_page.GAP_ID_RE, "v4.13#WN-3"),
    ("approval_page.BRANCH_RE", approval_page.BRANCH_RE, "feat/x"),
    ("approval_binding.SCOPE_RE", approval_binding.SCOPE_RE, "v4.13"),
    ("approval_binding.CODE_RE", approval_binding.CODE_RE, "ABCD2345"),
]


@pytest.mark.parametrize("name,regex,good", VALIDATORS, ids=[v[0] for v in VALIDATORS])
def test_a_trailing_newline_is_not_canonical(name, regex, good) -> None:
    assert regex.match(good), f"{name} must accept {good!r}"
    assert not regex.match(good + "\n"), f"{name} accepted a trailing newline"


@pytest.mark.parametrize("token", ["v4.1\u0663", "v\u0664.13", "v4.13.\u0666"])
def test_non_ascii_digits_are_not_a_version(token: str) -> None:
    with pytest.raises(check_plan_completion.Malformed):
        completion_minor.parse_minor(check_plan_completion, token)
    assert not approval_page.SCOPE_RE.match(token)
    assert not approval_binding.SCOPE_RE.match(token)
    assert not completion_minor.MINOR_RE.match(token)


def test_parse_minor_refuses_a_trailing_newline() -> None:
    with pytest.raises(check_plan_completion.Malformed):
        completion_minor.parse_minor(check_plan_completion, "v4.13\n")
    assert completion_minor.parse_minor(check_plan_completion, "v4.13") == (4, 13)
