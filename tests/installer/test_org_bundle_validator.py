"""Contract and failure-path tests for organization knowledge bundles."""

from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import org_knowledge as org  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "configs" / "org-bundle.schema.json"
EXAMPLE_BUNDLE = REPO_ROOT / "configs" / "examples" / "org-bundle-example"


def _manifest(**overrides: object) -> dict[str, object]:
    manifest: dict[str, object] = {
        "schema_version": 1,
        "org_name": "Test Organization",
        "core": "core.md",
        "rules_dir": "rules/",
        "references_dir": "references/",
    }
    manifest.update(overrides)
    return manifest


def _write_bundle(root: Path, manifest: dict[str, object] | None = None) -> Path:
    root.mkdir(parents=True)
    (root / "rules" / "python").mkdir(parents=True)
    (root / "references").mkdir()
    (root / "org.json").write_text(
        json.dumps(_manifest() if manifest is None else manifest),
        encoding="utf-8",
    )
    (root / "core.md").write_text("# Core\n\nOne binding rule.\n", encoding="utf-8")
    (root / "rules" / "python" / "style.md").write_text(
        "# Python\n\nUse pathlib.\n",
        encoding="utf-8",
    )
    (root / "references" / "delivery.md").write_text(
        "# Delivery\n\nRun tests.\n",
        encoding="utf-8",
    )
    return root


def test_schema_declares_the_phase_one_contract():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["type"] == "object"
    assert schema["required"] == ["schema_version", "org_name", "core"]
    assert schema["properties"]["schema_version"] == {
        "description": "Bundle manifest schema version.",
        "type": "integer",
        "const": 1,
    }
    assert schema["properties"]["core"]["default"] == "core.md"
    assert schema["properties"]["rules_dir"]["default"] == "rules/"
    assert schema["properties"]["references_dir"]["default"] == "references/"
    for key in ("core", "rules_dir", "references_dir"):
        pattern = re.compile(schema["properties"][key]["pattern"])
        assert pattern.fullmatch("nested/file.md")
        assert not pattern.fullmatch("../outside.md")
        assert not pattern.fullmatch("/absolute/path")
        assert not pattern.fullmatch("C:\\absolute\\path")
    assert schema["additionalProperties"] is True


def test_shipped_example_validates_cleanly_and_stays_under_budget():
    report = org.validate_bundle(EXAMPLE_BUNDLE)

    assert report.valid, report.errors
    assert report.errors == []
    assert report.warnings == []
    assert len((EXAMPLE_BUNDLE / "core.md").read_text(encoding="utf-8").splitlines()) < 60
    assert report.summary().startswith("valid:")


@pytest.mark.parametrize("missing", ["schema_version", "org_name", "core"])
def test_each_required_key_omission_names_the_key(tmp_path: Path, missing: str):
    manifest = _manifest()
    del manifest[missing]
    bundle = _write_bundle(tmp_path / "bundle", manifest)

    report = org.validate_bundle(bundle)

    assert not report.valid
    assert any(f"missing required key '{missing}'" in error for error in report.errors)


@pytest.mark.parametrize(
    ("key", "value", "expected"),
    [
        ("schema_version", True, "expected integer 1"),
        ("schema_version", 2, "unsupported value 2"),
        ("org_name", "", "expected a non-empty string"),
        ("core", 42, "expected a non-empty relative path string"),
        ("rules_dir", [], "expected a non-empty relative path string"),
        ("references_dir", None, "expected a non-empty relative path string"),
        ("precedence_statement", " ", "expected a non-empty string"),
    ],
)
def test_manifest_type_errors_are_actionable(
    tmp_path: Path,
    key: str,
    value: object,
    expected: str,
):
    bundle = _write_bundle(tmp_path / "bundle", _manifest(**{key: value}))

    report = org.validate_bundle(bundle)

    assert any(key in error and expected in error for error in report.errors)


def test_unknown_keys_are_forward_compatible_warnings(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle", _manifest(future_policy="enabled"))

    report = org.validate_bundle(bundle)

    assert report.valid
    assert report.errors == []
    assert report.warnings == [
        "org.json: unknown keys accepted for forward compatibility: future_policy"
    ]


def test_optional_directory_defaults_are_applied_to_a_copied_manifest(tmp_path: Path):
    source = _manifest()
    del source["rules_dir"]
    del source["references_dir"]
    bundle = _write_bundle(tmp_path / "bundle", source)

    report = org.validate_bundle(bundle)

    assert report.valid
    assert "rules_dir" not in source and "references_dir" not in source
    assert report.manifest["rules_dir"] == "rules/"
    assert report.manifest["references_dir"] == "references/"


def test_oversized_core_warns_without_failing_or_truncating(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")
    oversized = "\n".join(f"line {number}" for number in range(201)) + "\n"
    (bundle / "core.md").write_text(oversized, encoding="utf-8")

    report = org.validate_bundle(bundle)

    assert report.valid
    assert len(report.warnings) == 1
    assert "201 lines exceeds the 200-line always-on budget" in report.warnings[0]
    assert "Anthropic recommends" in report.warnings[0]
    assert (bundle / "core.md").read_text(encoding="utf-8") == oversized


def test_exactly_200_core_lines_do_not_warn(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")
    (bundle / "core.md").write_text("rule\n" * 200, encoding="utf-8")

    assert org.validate_bundle(bundle).warnings == []


@pytest.mark.parametrize("key", ["rules_dir", "references_dir"])
def test_missing_referenced_directory_is_an_error(tmp_path: Path, key: str):
    bundle = _write_bundle(tmp_path / "bundle", _manifest(**{key: "missing/"}))

    report = org.validate_bundle(bundle)

    assert any(
        error.startswith(f"{key}: referenced directory does not exist:")
        for error in report.errors
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("core", "../outside.md"),
        ("rules_dir", "/absolute/rules"),
        ("references_dir", "C:\\private\\references"),
    ],
)
def test_referenced_paths_must_stay_inside_bundle(
    tmp_path: Path,
    key: str,
    value: str,
):
    bundle = _write_bundle(tmp_path / "bundle", _manifest(**{key: value}))

    report = org.validate_bundle(bundle)

    assert any(key in error and "contained within the bundle" in error for error in report.errors)


def test_malformed_json_reports_line_column_and_position(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")
    (bundle / "org.json").write_text('{\n  "schema_version": 1,\n  nope\n}', encoding="utf-8")

    report = org.validate_bundle(bundle)

    assert not report.valid
    assert len(report.errors) == 1
    error = report.errors[0]
    assert "malformed JSON" in error
    assert "line 3" in error and "column" in error and "position" in error


def test_missing_bundle_returns_a_typed_error_instead_of_raising(tmp_path: Path):
    missing = tmp_path / "not-there"

    report = org.validate_bundle(missing)

    assert isinstance(report, org.BundleReport)
    assert not report.valid
    assert report.errors == [f"bundle directory does not exist: {missing}"]


def test_missing_manifest_is_a_typed_error(tmp_path: Path):
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    report = org.validate_bundle(bundle)

    assert report.errors == [f"org.json: manifest does not exist: {bundle / 'org.json'}"]


def test_manifest_root_must_be_an_object(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")
    (bundle / "org.json").write_text("[]", encoding="utf-8")

    report = org.validate_bundle(bundle)

    assert report.errors == ["org.json: expected a JSON object at the document root"]


def test_manifest_must_be_utf8(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")
    (bundle / "org.json").write_bytes(b"\xff\xfe")

    report = org.validate_bundle(bundle)

    assert len(report.errors) == 1
    assert "org.json: cannot read" in report.errors[0]
    assert "as UTF-8" in report.errors[0]


def test_file_path_is_not_accepted_as_a_bundle_directory(tmp_path: Path):
    path = tmp_path / "bundle.txt"
    path.write_text("not a directory", encoding="utf-8")

    report = org.validate_bundle(path)

    assert report.errors == [f"bundle path is not a directory: {path}"]


@pytest.mark.parametrize(
    ("key", "replacement", "expected"),
    [
        ("core", "missing.md", "referenced file does not exist"),
        ("core", "rules", "referenced path is not a file"),
        ("rules_dir", "core.md", "referenced path is not a directory"),
        ("references_dir", "core.md", "referenced path is not a directory"),
    ],
)
def test_referenced_path_kind_errors_are_named(
    tmp_path: Path,
    key: str,
    replacement: str,
    expected: str,
):
    bundle = _write_bundle(tmp_path / "bundle", _manifest(**{key: replacement}))

    report = org.validate_bundle(bundle)

    assert any(error.startswith(f"{key}:") and expected in error for error in report.errors)


def test_symlinked_core_cannot_escape_the_bundle(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle", _manifest(core="linked.md"))
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")
    try:
        (bundle / "linked.md").symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"file symlinks unavailable: {exc}")

    report = org.validate_bundle(bundle)

    assert any("core:" in error and "cannot be resolved safely" in error for error in report.errors)


def test_unreadable_files_are_reported_individually_and_validation_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    bundle = _write_bundle(tmp_path / "bundle")
    original = Path.read_text

    def selective_failure(path: Path, *args: object, **kwargs: object) -> str:
        if path.name in {"core.md", "style.md"}:
            raise PermissionError("placeholder is not hydrated")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", selective_failure)

    report = org.validate_bundle(bundle)

    assert len(report.errors) == 2
    assert any("core.md" in error and "placeholder is not hydrated" in error for error in report.errors)
    assert any("style.md" in error and "placeholder is not hydrated" in error for error in report.errors)


def test_invalid_utf8_is_a_per_file_error(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")
    (bundle / "references" / "delivery.md").write_bytes(b"\xff\xfe")

    report = org.validate_bundle(bundle)

    assert any("delivery.md" in error and "as UTF-8" in error for error in report.errors)


def test_deliberately_broken_bundle_collects_actionable_errors(tmp_path: Path):
    bundle = _write_bundle(
        tmp_path / "bundle",
        {
            "schema_version": "one",
            "org_name": "",
            "core": "missing.md",
            "rules_dir": "missing-rules/",
            "references_dir": "../outside/",
            "future_key": True,
        },
    )

    report = org.validate_bundle(bundle)

    assert not report.valid
    assert len(report.errors) >= 5
    assert all(":" in error for error in report.errors)
    assert report.warnings == [
        "org.json: unknown keys accepted for forward compatibility: future_key"
    ]


def test_validation_does_not_mutate_bundle_files(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")
    before = {
        path.relative_to(bundle): path.read_bytes()
        for path in bundle.rglob("*")
        if path.is_file()
    }

    report = org.validate_bundle(bundle)

    after = {
        path.relative_to(bundle): path.read_bytes()
        for path in bundle.rglob("*")
        if path.is_file()
    }
    assert report.valid
    assert after == before


def test_tilde_expansion_uses_path_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_home = tmp_path / "home"
    bundle = _write_bundle(fake_home / "bundle")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    report = org.validate_bundle("~/bundle")

    assert report.valid
    assert report.bundle_path == bundle


def test_bare_tilde_expansion_uses_path_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    fake_home = _write_bundle(tmp_path / "home")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: fake_home))

    report = org.validate_bundle("~")

    assert report.valid
    assert report.bundle_path == fake_home


def test_note_is_one_stderr_line(capsys: pytest.CaptureFixture[str]):
    org._note("validation deferred")

    assert capsys.readouterr().err == "note: org-knowledge: validation deferred\n"


def test_concurrent_validation_is_read_only_and_deterministic(tmp_path: Path):
    bundle = _write_bundle(tmp_path / "bundle")

    with ThreadPoolExecutor(max_workers=4) as pool:
        reports = list(pool.map(org.validate_bundle, [bundle] * 12))

    assert all(report.valid for report in reports)
    assert {report.summary() for report in reports} == {
        f"valid: {bundle} (0 errors, 0 warnings)"
    }
