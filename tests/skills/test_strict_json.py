"""The strict JSON decoder must reject unsafe input before semantic validation.

Every ceiling is exercised at its EXACT value and at one unit beyond it. An
off-by-one in a limit check is the defect class these tests exist for: a guard
that rejects at the limit instead of past it breaks valid input, and one that
accepts one past the limit is not a guard.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_MODULE_PATH = (
    _ROOT
    / "catalog"
    / "skills"
    / "code-review"
    / "security-review"
    / "scripts"
    / "_strict_json.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("_strict_json_under_test", _MODULE_PATH)
    assert spec and spec.loader, f"cannot load {_MODULE_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


sj = _load()


def test_duplicate_key_diagnostic_does_not_expose_input() -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"TEST_SECRET_CANARY":1,"TEST_SECRET_CANARY":2}')
    assert exc.value.code == "duplicate_object_member"
    assert "TEST_SECRET_CANARY" not in str(exc.value)


def test_integer_conversion_failure_has_a_stable_error() -> None:
    limit = sys.get_int_max_str_digits()
    if not limit:
        pytest.skip("runtime integer conversion limit is disabled")
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"x":' + "1" * (limit + 1) + "}")
    assert exc.value.code == "malformed_json"


def _codes(excinfo) -> str:
    return excinfo.value.code


# --------------------------------------------------------------------------
# Baseline, so a later rejection is attributable to the guard and not the setup
# --------------------------------------------------------------------------


def test_a_valid_document_round_trips() -> None:
    assert sj.loads('{"a": [1, 2, {"b": "text"}], "c": null}') == {
        "a": [1, 2, {"b": "text"}],
        "c": None,
    }


def test_bytes_and_str_inputs_agree() -> None:
    assert sj.loads(b'{"a": 1}') == sj.loads('{"a": 1}')


def test_leading_and_trailing_whitespace_is_accepted() -> None:
    assert sj.loads('  \n {"a": 1} \t\n ') == {"a": 1}


# --------------------------------------------------------------------------
# Duplicate members: the silent-last-wins class
# --------------------------------------------------------------------------


def test_duplicate_member_at_top_level_is_rejected() -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"computed_health": "failed", "computed_health": "complete"}')
    assert _codes(exc) == "duplicate_object_member"


def test_duplicate_member_nested_deeply_is_rejected() -> None:
    """The bypass only matters if it is caught at EVERY level, not just the top."""
    payload = '{"a": {"b": {"c": {"health": "failed", "health": "complete"}}}}'
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads(payload)
    assert _codes(exc) == "duplicate_object_member"


def test_duplicate_member_inside_an_array_element_is_rejected() -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"items": [{"id": "x", "id": "y"}]}')
    assert _codes(exc) == "duplicate_object_member"


# --------------------------------------------------------------------------
# Non-finite numbers, via both routes
# --------------------------------------------------------------------------


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_literals_are_rejected(literal: str) -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"score": ' + literal + "}")
    assert _codes(exc) == "non_finite_number"


def test_overflowing_numeric_literal_is_rejected() -> None:
    """1e400 becomes inf WITHOUT passing through the constant hook.

    This is the case the constant hook alone would miss, which is why the
    decoder also re-checks finiteness over the decoded value.
    """
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"score": 1e400}')
    assert _codes(exc) == "non_finite_number"


# --------------------------------------------------------------------------
# Framing
# --------------------------------------------------------------------------


def test_trailing_data_is_rejected() -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"a": 1} {"b": 2}')
    assert _codes(exc) == "trailing_data"


def test_empty_input_is_rejected() -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads("   \n  ")
    assert _codes(exc) == "empty_input"


def test_malformed_json_is_rejected() -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"a": }')
    assert _codes(exc) == "malformed_json"


def test_invalid_utf8_bytes_are_rejected() -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads(b'{"a": "\xff\xfe"}')
    assert _codes(exc) == "invalid_unicode"


def test_lone_surrogate_escape_is_rejected() -> None:
    """Accepted by the stdlib, unencodable afterwards.

    Catching it here keeps the failure attributable to the input instead of to
    some later write or digest that cannot explain where the bad text came from.
    """
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"a": "\\ud800"}')
    assert _codes(exc) == "invalid_unicode"


# --------------------------------------------------------------------------
# Ceilings: exact value accepted, one beyond rejected
# --------------------------------------------------------------------------


def test_depth_at_the_exact_limit_is_accepted() -> None:
    payload = "[" * sj.MAX_DEPTH + "1" + "]" * sj.MAX_DEPTH
    assert sj.loads(payload) is not None


def test_depth_one_beyond_the_limit_is_rejected() -> None:
    over = sj.MAX_DEPTH + 1
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads("[" * over + "1" + "]" * over)
    assert _codes(exc) == "depth_exceeded"


def test_a_deep_nesting_bomb_fails_closed() -> None:
    """Far past the parser's own recursion limit, so the parser trips first."""
    depth = 20_000
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads("[" * depth + "1" + "]" * depth)
    assert _codes(exc) == "depth_exceeded"


def test_object_members_at_the_exact_limit_are_accepted() -> None:
    members = ",".join(f'"k{i}":{i}' for i in range(sj.MAX_MEMBERS))
    assert len(sj.loads("{" + members + "}")) == sj.MAX_MEMBERS


def test_object_members_one_beyond_the_limit_are_rejected() -> None:
    members = ",".join(f'"k{i}":{i}' for i in range(sj.MAX_MEMBERS + 1))
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads("{" + members + "}")
    assert _codes(exc) == "object_too_large"


def test_array_members_at_the_exact_limit_are_accepted() -> None:
    assert len(sj.loads("[" + ",".join("1" * 1 for _ in range(sj.MAX_MEMBERS)) + "]")) == (
        sj.MAX_MEMBERS
    )


def test_array_members_one_beyond_the_limit_are_rejected() -> None:
    payload = "[" + ",".join("1" for _ in range(sj.MAX_MEMBERS + 1)) + "]"
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads(payload)
    assert _codes(exc) == "array_too_large"


def test_string_at_the_exact_byte_limit_is_accepted() -> None:
    value = "a" * sj.MAX_STRING_BYTES
    assert sj.loads('{"a": "' + value + '"}')["a"] == value


def test_string_one_byte_beyond_the_limit_is_rejected() -> None:
    value = "a" * (sj.MAX_STRING_BYTES + 1)
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"a": "' + value + '"}')
    assert _codes(exc) == "string_too_large"


def test_the_string_limit_counts_bytes_not_characters() -> None:
    """A multi-byte character must not buy extra room past the byte ceiling."""
    value = "e" * (sj.MAX_STRING_BYTES - 2) + "éé"  # 2 chars, 4 bytes
    assert len(value.encode("utf-8")) == sj.MAX_STRING_BYTES + 2
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads('{"a": "' + value + '"}')
    assert _codes(exc) == "string_too_large"


def _document_padded_to(total_bytes: int) -> bytes:
    """A valid document padded with trailing whitespace to an exact byte count.

    Trailing whitespace is legal framing, so this isolates the SIZE ceiling from
    every other guard: the only thing changing between the accept and reject
    cases is one byte of padding.
    """
    base = b'{"a": 1}'
    assert total_bytes >= len(base)
    return base + b" " * (total_bytes - len(base))


def test_input_at_the_exact_byte_limit_is_accepted() -> None:
    payload = _document_padded_to(sj.MAX_BYTES)
    assert len(payload) == sj.MAX_BYTES
    assert sj.loads(payload) == {"a": 1}


def test_input_one_byte_beyond_the_limit_is_rejected() -> None:
    payload = _document_padded_to(sj.MAX_BYTES + 1)
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.loads(payload)
    assert _codes(exc) == "input_too_large"


# --------------------------------------------------------------------------
# Path entry point
# --------------------------------------------------------------------------


def test_load_path_reads_and_validates(tmp_path: Path) -> None:
    target = tmp_path / "record.json"
    target.write_text('{"a": 1}', encoding="utf-8")
    assert sj.load_path(target) == {"a": 1}


def test_load_path_on_a_missing_file_reports_a_stable_code(tmp_path: Path) -> None:
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.load_path(tmp_path / "absent.json")
    assert _codes(exc) == "unreadable_input"


def test_load_path_still_applies_every_content_guard(tmp_path: Path) -> None:
    target = tmp_path / "dupe.json"
    target.write_text('{"h": 1, "h": 2}', encoding="utf-8")
    with pytest.raises(sj.StrictJSONError) as exc:
        sj.load_path(target)
    assert _codes(exc) == "duplicate_object_member"


def test_no_partial_value_is_returned_on_rejection() -> None:
    """A rejection must raise rather than return a half-checked value."""
    with pytest.raises(sj.StrictJSONError):
        result = sj.loads('{"ok": 1, "bad": NaN}')
        assert result is None, "decoder returned a value for rejected input"
