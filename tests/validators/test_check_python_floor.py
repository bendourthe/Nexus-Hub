"""Regression tests for the local Python CI-floor grammar gate."""

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_python_floor.py"
SPEC = importlib.util.spec_from_file_location("check_python_floor", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_python_311_source_passes(tmp_path: Path) -> None:
    source = tmp_path / "compatible.py"
    source.write_text('value = f"{1 + 2}"\n', encoding="utf-8")
    assert MODULE.check_paths([source]) == []


def test_python_312_fstring_expression_fails(tmp_path: Path) -> None:
    source = tmp_path / "too_new.py"
    source.write_text('value = f"{1\n+ 2}"\n', encoding="utf-8")
    failures = MODULE.check_paths([source])
    assert len(failures) == 1
    assert str(source) in failures[0]


def test_invalid_utf8_fails(tmp_path: Path) -> None:
    source = tmp_path / "invalid.py"
    source.write_bytes(b"value = '\xff'\n")
    assert len(MODULE.check_paths([source])) == 1
