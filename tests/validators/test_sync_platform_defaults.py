"""Tests for the platform install-defaults source, generator, and drift guard.

Covers v3.16.0 Phase 1: `configs/platform-defaults.json` is the single place a
per-platform install-time behavioral default is declared, and every consuming
artifact is derived from it.

Two properties get the most attention here because they are the ones that would
fail silently:

1. **The hooks block must survive.** `catalog/hooks/settings.json` carries the
   full hook registration chains alongside the four core keys the generator
   owns. A naive re-serialization would destroy them, so `--apply` is asserted
   byte-identical outside the declared keys.
2. **Line endings must be preserved.** This repo runs `core.autocrlf=true`, so a
   Windows working tree holds CRLF while git stores LF. A generator that wrote a
   fixed "\\n" would rewrite every line on a Windows checkout while looking
   clean in CI, so both conventions are exercised explicitly.

Most tests build an isolated fake repo tree under `tmp_path` so they never
mutate the real catalog; a small set asserts against the real tree.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync_platform_defaults as sync  # noqa: E402
from scripts.lib.integrations import list_keys  # noqa: E402
from scripts.lib.integrations import claude as claude_integration  # noqa: E402

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py for why greping the
# YAML would be both wrong and dangerous to "fix".
from tests.validators._ci_reachability import assert_wired_into_ci

SCRIPT = REPO_ROOT / "scripts" / "sync_platform_defaults.py"
REAL_SOURCE = REPO_ROOT / "configs" / "platform-defaults.json"
REAL_TEMPLATE = REPO_ROOT / "catalog" / "hooks" / "settings.json"

# A miniature stand-in for catalog/hooks/settings.json: the four core keys the
# generator owns, plus an unrelated block standing in for the hook chains.
FAKE_TEMPLATE = {
    "effortLevel": "medium",
    "model": "opus",
    "env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"},
    "hooks": {
        "SessionStart": [
            {"matcher": "", "hooks": [{"type": "command", "command": "echo start"}]}
        ],
        "Stop": [{"matcher": "", "hooks": [{"type": "command", "command": "echo stop"}]}],
    },
}

FAKE_CLAUDE_PY = '''"""Stand-in for scripts/lib/integrations/claude.py."""

SOMETHING_BEFORE = 1

_FALLBACK_SETTINGS = {
    "effortLevel": "medium",
    "model": "opus",
    "env": {
        "CLAUDE_CODE_EFFORT_LEVEL": "medium",
    },
}

SOMETHING_AFTER = 2
'''


def _source_doc(effort: str = "medium", model: str = "opus") -> dict:
    return {
        "schema_version": 1,
        "meta": {"last_updated": "2026-08-08"},
        "platforms": {
            "claude": {
                "display_name": "Claude Code",
                "source_url": "https://code.claude.com/docs/en/settings",
                "verified": "2026-08-08",
                "doc_statement": "settings.json documents effortLevel, model, env.",
                "settings": {
                    "effortLevel": effort,
                    "model": model,
                    "env": {"CLAUDE_CODE_EFFORT_LEVEL": effort},
                },
                "rationale": {"effortLevel": "test fixture"},
                "derived_artifacts": [
                    {
                        "path": "catalog/hooks/settings.json",
                        "format": "json",
                        "strategy": "merge-keys",
                        "keys": ["effortLevel", "model", "env.CLAUDE_CODE_EFFORT_LEVEL"],
                        "note": "fixture",
                    },
                    {
                        "path": "scripts/lib/integrations/claude.py",
                        "format": "python",
                        "strategy": "runtime-read",
                        "keys": ["effortLevel", "model", "env.CLAUDE_CODE_EFFORT_LEVEL"],
                        "fallback_symbol": "_FALLBACK_SETTINGS",
                        "note": "fixture",
                    },
                ],
            }
        },
    }


def _write(path: Path, text: str, newline: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("\n", newline))


@pytest.fixture
def tree(tmp_path: Path):
    """Build an isolated fake repo tree and return (root, source_path)."""

    def _build(effort: str = "medium", newline: str = "\n") -> tuple[Path, Path]:
        root = tmp_path / "repo"
        source = root / "configs" / "platform-defaults.json"
        _write(source, json.dumps(_source_doc(effort), indent=2) + "\n", newline)
        _write(
            root / "catalog" / "hooks" / "settings.json",
            json.dumps(FAKE_TEMPLATE, indent=2) + "\n",
            newline,
        )
        _write(root / "scripts" / "lib" / "integrations" / "claude.py", FAKE_CLAUDE_PY, newline)
        return root, source

    return _build


# --------------------------------------------------------------------------
# Schema of the real source
# --------------------------------------------------------------------------


def test_real_source_parses_and_declares_required_top_level_keys():
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for key in ("schema_version", "meta", "platforms"):
        assert key in data, f"configs/platform-defaults.json is missing {key!r}"
    assert isinstance(data["platforms"], dict) and data["platforms"]


def test_every_declared_platform_has_an_install_target_mode():
    """Phase 3 widened the file past Claude; every entry must say what happens to it.

    Phase 1's assertion here was `== ["claude"]`, which was correct then and is
    obsolete now. It is replaced rather than deleted so the file still asserts
    something about the declared set: a platform may be written, already
    delivered by an existing installer path, or deliberately not written, but it
    may never be declared without saying which.
    """
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    valid = {"write", "already-delivered", "not-writable"}
    for name, entry in data["platforms"].items():
        target = entry.get("install_target")
        assert isinstance(target, dict), f"{name}: missing an install_target block"
        assert target.get("mode") in valid, (
            f"{name}: install_target.mode={target.get('mode')!r}; expected one of {sorted(valid)}"
        )


def test_not_writable_platforms_declare_no_settings_and_state_a_reason():
    """A declared-but-not-writable platform must not carry a half-seeded value."""
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        if entry["install_target"]["mode"] != "not-writable":
            continue
        assert entry["settings"] == {}, (
            f"{name} is not-writable but declares settings {entry['settings']!r}"
        )
        assert entry["install_target"].get("reason"), f"{name}: not-writable needs a reason"


def test_writable_platforms_declare_settings_a_path_and_a_format():
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        target = entry["install_target"]
        if target["mode"] != "write":
            continue
        assert entry["settings"], f"{name} is writable but declares no settings"
        assert target.get("path"), f"{name}: writable target needs a path"
        assert target.get("format") in {"json", "toml", "yaml"}, (
            f"{name}: unsupported target format {target.get('format')!r}"
        )
        assert target.get("merge") == "seed-if-absent", (
            f"{name}: seeding must never overwrite a value the user already set"
        )


def test_every_platform_id_matches_the_integration_registry():
    """Keys must be registry ids so an entry maps to its integration directly."""
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    known = set(list_keys())
    unknown = sorted(set(data["platforms"]) - known)
    assert not unknown, (
        f"platform-defaults.json declares ids not in the integration registry: "
        f"{unknown}. Known ids: {sorted(known)}"
    )


@pytest.mark.parametrize("field", ["source_url", "verified", "doc_statement"])
def test_every_platform_entry_carries_provenance(field: str):
    """The do-not-invent rule in machine form: no lever without evidence.

    `settings` is deliberately NOT in this list. A declared-but-not-writable
    platform carries an empty settings object on purpose (its emptiness is the
    point), so its presence is asserted separately by shape rather than by
    truthiness.
    """
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        assert entry.get(field), f"platform {name!r} is missing required {field!r}"


def test_every_platform_entry_declares_a_settings_object():
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        assert isinstance(entry.get("settings"), dict), (
            f"platform {name!r} must declare a settings object, even if empty"
        )


def test_omitted_keys_state_why_they_were_not_seeded():
    """Where a lever exists but no safe value is documented, the gap is explained.

    This is the counterpart to the do-not-invent rule: refusing to seed is
    correct, but refusing silently would leave a reader unable to tell a
    deliberate omission from an oversight.
    """
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        for key, reason in entry.get("omitted", {}).items():
            assert isinstance(reason, str) and len(reason) > 20, (
                f"{name}: omitted key {key!r} needs a substantive reason, got {reason!r}"
            )


def test_verified_dates_are_iso_formatted():
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", entry["verified"]), (
            f"platform {name!r} has verified={entry['verified']!r}; expected YYYY-MM-DD"
        )


def test_source_urls_are_official_https_documents():
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        assert entry["source_url"].startswith("https://"), (
            f"platform {name!r} source_url must be an https vendor document"
        )


def test_declared_keys_resolve_within_settings():
    """Every derived artifact's declared keys must exist in that platform's settings."""
    data = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))
    for name, entry in data["platforms"].items():
        for artifact in entry["derived_artifacts"]:
            for key in artifact["keys"]:
                assert sync.resolve_key(entry["settings"], key) is not None, (
                    f"{name}: declared key {key!r} does not resolve"
                )


# --------------------------------------------------------------------------
# The real tree stays in sync
# --------------------------------------------------------------------------


def test_real_tree_is_in_sync():
    """`make validate` runs this; failing here means an artifact was hand-edited."""
    drifts = sync.check(sync.load_defaults(REAL_SOURCE), REPO_ROOT)
    assert not drifts, "\n".join(str(d) for d in drifts)


# --------------------------------------------------------------------------
# --apply: idempotence and byte preservation
# --------------------------------------------------------------------------


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_apply_is_a_byte_identical_noop_on_a_synced_tree(tree, newline: str):
    """The core guarantee, exercised for BOTH line-ending conventions.

    A Windows checkout materializes CRLF; CI holds LF. A generator that assumed
    one would silently rewrite the other.
    """
    root, source = tree(newline=newline)
    template = root / "catalog" / "hooks" / "settings.json"
    module = root / "scripts" / "lib" / "integrations" / "claude.py"
    before_template, before_module = template.read_bytes(), module.read_bytes()

    changed = sync.apply(sync.load_defaults(source), root)

    assert changed == [], f"a synced tree should need no write, got {changed}"
    assert template.read_bytes() == before_template
    assert module.read_bytes() == before_module


def test_apply_preserves_the_hooks_block_byte_for_byte(tree):
    """The named hazard: the template also carries the hook registrations."""
    root, source = tree()
    template = root / "catalog" / "hooks" / "settings.json"
    hooks_before = json.loads(template.read_text(encoding="utf-8"))["hooks"]

    doc = _source_doc(effort="xhigh")
    source.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    sync.apply(sync.load_defaults(source), root)

    data = json.loads(template.read_text(encoding="utf-8"))
    assert data["hooks"] == hooks_before, "the hooks block must survive a rewrite"
    assert data["effortLevel"] == "xhigh"


def test_apply_preserves_key_order(tree):
    root, source = tree()
    template = root / "catalog" / "hooks" / "settings.json"
    order_before = list(json.loads(template.read_text(encoding="utf-8")))

    source.write_text(json.dumps(_source_doc(effort="high"), indent=2) + "\n", encoding="utf-8")
    sync.apply(sync.load_defaults(source), root)

    assert list(json.loads(template.read_text(encoding="utf-8"))) == order_before


def test_apply_is_idempotent_after_a_real_change(tree):
    root, source = tree()
    source.write_text(json.dumps(_source_doc(effort="low"), indent=2) + "\n", encoding="utf-8")

    first = sync.apply(sync.load_defaults(source), root)
    snapshot = (root / "catalog" / "hooks" / "settings.json").read_bytes()
    second = sync.apply(sync.load_defaults(source), root)

    assert first, "the first apply should have written something"
    assert second == [], "a second apply must be a no-op"
    assert (root / "catalog" / "hooks" / "settings.json").read_bytes() == snapshot


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_apply_preserves_the_existing_newline_convention(tree, newline: str):
    root, source = tree(newline=newline)
    template = root / "catalog" / "hooks" / "settings.json"
    source.write_text(json.dumps(_source_doc(effort="high"), indent=2) + "\n", encoding="utf-8")

    sync.apply(sync.load_defaults(source), root)

    raw = template.read_bytes()
    if newline == "\r\n":
        assert b"\r\n" in raw and raw.count(b"\r\n") == raw.count(b"\n")
    else:
        assert b"\r\n" not in raw


# --------------------------------------------------------------------------
# --check: drift detection, per artifact
# --------------------------------------------------------------------------


def test_check_is_green_on_a_synced_tree(tree):
    root, source = tree()
    assert sync.check(sync.load_defaults(source), root) == []


def test_check_detects_drift_in_the_json_artifact(tree):
    root, source = tree()
    template = root / "catalog" / "hooks" / "settings.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    data["model"] = "haiku"
    template.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    drifts = sync.check(sync.load_defaults(source), root)

    assert len(drifts) == 1
    assert drifts[0].key == "model"
    assert drifts[0].declared == "opus"
    assert drifts[0].found == "haiku"
    assert "catalog/hooks/settings.json" in drifts[0].artifact


def test_check_detects_drift_in_a_nested_env_key(tree):
    root, source = tree()
    template = root / "catalog" / "hooks" / "settings.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    data["env"]["CLAUDE_CODE_EFFORT_LEVEL"] = "xhigh"
    template.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    drifts = sync.check(sync.load_defaults(source), root)

    assert [d.key for d in drifts] == ["env.CLAUDE_CODE_EFFORT_LEVEL"]


def test_check_reports_an_absent_key_rather_than_crashing(tree):
    root, source = tree()
    template = root / "catalog" / "hooks" / "settings.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    del data["model"]
    template.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    drifts = sync.check(sync.load_defaults(source), root)

    assert len(drifts) == 1
    assert drifts[0].found is sync.MISSING
    assert "<absent>" in str(drifts[0])


def test_check_detects_drift_in_the_python_fallback(tree):
    """The runtime-read artifact keeps a fallback literal that can also rot."""
    root, source = tree()
    module = root / "scripts" / "lib" / "integrations" / "claude.py"
    module.write_text(
        module.read_text(encoding="utf-8").replace('"model": "opus"', '"model": "sonnet"'),
        encoding="utf-8",
    )

    drifts = sync.check(sync.load_defaults(source), root)

    assert len(drifts) == 1
    assert drifts[0].key == "model"
    assert "_FALLBACK_SETTINGS" in drifts[0].artifact


def test_apply_repairs_a_drifted_python_fallback(tree):
    root, source = tree()
    module = root / "scripts" / "lib" / "integrations" / "claude.py"
    module.write_text(
        module.read_text(encoding="utf-8").replace('"model": "opus"', '"model": "sonnet"'),
        encoding="utf-8",
    )

    sync.apply(sync.load_defaults(source), root)

    assert sync.check(sync.load_defaults(source), root) == []
    body = module.read_text(encoding="utf-8")
    assert "SOMETHING_BEFORE = 1" in body and "SOMETHING_AFTER = 2" in body


# --------------------------------------------------------------------------
# End-to-end: one edit propagates everywhere
# --------------------------------------------------------------------------


def test_one_edit_propagates_to_every_derived_artifact(tree):
    """The whole point of the release, asserted end to end."""
    root, source = tree()
    source.write_text(json.dumps(_source_doc(effort="xhigh"), indent=2) + "\n", encoding="utf-8")

    changed = sync.apply(sync.load_defaults(source), root)

    assert sorted(changed) == [
        "catalog/hooks/settings.json",
        "scripts/lib/integrations/claude.py",
    ]
    template = json.loads(
        (root / "catalog" / "hooks" / "settings.json").read_text(encoding="utf-8")
    )
    assert template["effortLevel"] == "xhigh"
    assert template["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == "xhigh"
    module_body = (root / "scripts" / "lib" / "integrations" / "claude.py").read_text(
        encoding="utf-8"
    )
    assert '"effortLevel": "xhigh"' in module_body


# --------------------------------------------------------------------------
# Malformed input
# --------------------------------------------------------------------------


def test_unknown_strategy_is_a_source_error(tree):
    root, source = tree()
    doc = _source_doc()
    doc["platforms"]["claude"]["derived_artifacts"][0]["strategy"] = "telepathy"
    source.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(sync.SourceError, match="unknown strategy"):
        sync.check(sync.load_defaults(source), root)


def test_missing_source_is_a_source_error(tmp_path: Path):
    with pytest.raises(sync.SourceError, match="not found"):
        sync.load_defaults(tmp_path / "absent.json")


def test_missing_derived_artifact_is_a_source_error(tree):
    root, source = tree()
    (root / "catalog" / "hooks" / "settings.json").unlink()
    with pytest.raises(sync.SourceError, match="derived artifact not found"):
        sync.check(sync.load_defaults(source), root)


# --------------------------------------------------------------------------
# CLI surface and exit codes
# --------------------------------------------------------------------------


def _run_cli(root: Path, source: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--source", str(source), "--repo-root", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_check_exits_zero_when_in_sync(tree):
    root, source = tree()
    result = _run_cli(root, source, "--check")
    assert result.returncode == sync.EXIT_OK, result.stderr
    assert "in sync" in result.stdout


def test_cli_check_exits_one_on_drift_and_names_the_details(tree):
    root, source = tree()
    template = root / "catalog" / "hooks" / "settings.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    data["effortLevel"] = "low"
    template.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    result = _run_cli(root, source, "--check")

    assert result.returncode == sync.EXIT_DRIFT
    for expected in ("catalog/hooks/settings.json", "effortLevel", "medium", "low", "--apply"):
        assert expected in result.stderr, f"stderr should name {expected!r}"


def test_cli_requires_a_mode(tree):
    root, source = tree()
    result = _run_cli(root, source)
    assert result.returncode != 0


def test_cli_apply_then_check_is_green(tree):
    root, source = tree()
    source.write_text(json.dumps(_source_doc(effort="high"), indent=2) + "\n", encoding="utf-8")
    assert _run_cli(root, source, "--apply").returncode == sync.EXIT_OK
    assert _run_cli(root, source, "--check").returncode == sync.EXIT_OK


# --------------------------------------------------------------------------
# main() in-process
#
# The subprocess tests above prove the real CLI contract, but they run in a
# separate interpreter so coverage cannot see the reporting code. These call
# main() directly to exercise the same paths in-process.
# --------------------------------------------------------------------------


def _main(root: Path, source: Path, *args: str) -> int:
    return sync.main(["--source", str(source), "--repo-root", str(root), *args])


def test_main_check_returns_ok_and_reports_the_platform_count(tree, capsys):
    root, source = tree()
    assert _main(root, source, "--check") == sync.EXIT_OK
    assert "1 platform(s)" in capsys.readouterr().out


def test_main_check_returns_drift_and_prints_the_repair_command(tree, capsys):
    root, source = tree()
    template = root / "catalog" / "hooks" / "settings.json"
    data = json.loads(template.read_text(encoding="utf-8"))
    data["effortLevel"] = "low"
    template.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    assert _main(root, source, "--check") == sync.EXIT_DRIFT
    err = capsys.readouterr().err
    assert "drifted" in err and "sync_platform_defaults.py --apply" in err


def test_main_apply_lists_what_it_changed(tree, capsys):
    root, source = tree()
    source.write_text(json.dumps(_source_doc(effort="high"), indent=2) + "\n", encoding="utf-8")

    assert _main(root, source, "--apply") == sync.EXIT_OK
    out = capsys.readouterr().out
    assert "catalog/hooks/settings.json" in out


def test_main_apply_reports_a_noop(tree, capsys):
    root, source = tree()
    assert _main(root, source, "--apply") == sync.EXIT_OK
    assert "Already in sync" in capsys.readouterr().out


def test_main_returns_error_exit_code_on_a_bad_source(tree, capsys):
    root, source = tree()
    source.write_text("{ not json", encoding="utf-8")
    assert _main(root, source, "--check") == sync.EXIT_ERROR
    assert "Error:" in capsys.readouterr().err


# --------------------------------------------------------------------------
# Helper-level error branches
# --------------------------------------------------------------------------


def test_load_defaults_rejects_malformed_json(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text("{ nope", encoding="utf-8")
    with pytest.raises(sync.SourceError, match="not valid JSON"):
        sync.load_defaults(path)


def test_load_defaults_rejects_a_source_without_platforms(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    with pytest.raises(sync.SourceError, match="platforms"):
        sync.load_defaults(path)


def test_resolve_key_names_the_failing_segment():
    with pytest.raises(sync.SourceError, match="env.MISSING"):
        sync.resolve_key({"env": {}}, "env.MISSING")


def test_set_key_creates_missing_intermediate_objects():
    target: dict = {}
    sync.set_key(target, "env.NESTED.VALUE", "x")
    assert target == {"env": {"NESTED": {"VALUE": "x"}}}


def test_set_key_replaces_a_non_dict_intermediate():
    target: dict = {"env": "not-an-object"}
    sync.set_key(target, "env.KEY", "x")
    assert target == {"env": {"KEY": "x"}}


@pytest.mark.parametrize(
    ("value", "expected"),
    [({}, "{}"), (None, "None"), (True, "True"), (False, "False"), (3, "3"), ("s", '"s"')],
)
def test_render_python_literal_handles_scalar_shapes(value, expected):
    assert sync.render_python_literal(value) == expected


def test_detect_newline_prefers_the_dominant_convention():
    assert sync.detect_newline("a\r\nb\r\n") == "\r\n"
    assert sync.detect_newline("a\nb\n") == "\n"


def test_detect_indent_falls_back_when_nothing_is_indented():
    assert sync.detect_indent("{}") == 2
    assert sync.detect_indent('{\n    "a": 1\n}') == 4


def test_check_rejects_a_json_artifact_that_is_not_json(tree):
    root, source = tree()
    (root / "catalog" / "hooks" / "settings.json").write_text("{ nope", encoding="utf-8")
    with pytest.raises(sync.SourceError, match="not valid JSON"):
        sync.check(sync.load_defaults(source), root)


def test_check_rejects_a_missing_fallback_symbol(tree):
    root, source = tree()
    module = root / "scripts" / "lib" / "integrations" / "claude.py"
    module.write_text("OTHER = 1\n", encoding="utf-8")
    with pytest.raises(sync.SourceError, match="not found as a module-level assignment"):
        sync.check(sync.load_defaults(source), root)


def test_check_rejects_a_non_literal_fallback(tree):
    root, source = tree()
    module = root / "scripts" / "lib" / "integrations" / "claude.py"
    module.write_text("_FALLBACK_SETTINGS = dict(a=1)\n", encoding="utf-8")
    with pytest.raises(sync.SourceError, match="plain literal"):
        sync.check(sync.load_defaults(source), root)


def test_check_rejects_a_non_dict_fallback(tree):
    root, source = tree()
    module = root / "scripts" / "lib" / "integrations" / "claude.py"
    module.write_text('_FALLBACK_SETTINGS = "nope"\n', encoding="utf-8")
    with pytest.raises(sync.SourceError, match="must be a dict literal"):
        sync.check(sync.load_defaults(source), root)


def test_runtime_read_artifact_without_a_fallback_symbol_is_skipped(tree):
    """A runtime-read artifact may legitimately carry no fallback to verify."""
    root, source = tree()
    doc = _source_doc()
    del doc["platforms"]["claude"]["derived_artifacts"][1]["fallback_symbol"]
    source.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    assert sync.check(sync.load_defaults(source), root) == []
    assert sync.apply(sync.load_defaults(source), root) == []


def test_platform_without_settings_is_a_source_error(tree):
    root, source = tree()
    doc = _source_doc()
    del doc["platforms"]["claude"]["settings"]
    source.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(sync.SourceError, match="missing a 'settings' object"):
        sync.check(sync.load_defaults(source), root)


# --------------------------------------------------------------------------
# The nexus-hub init stub reads the declared source
# --------------------------------------------------------------------------


def test_stub_reads_the_declared_values(tmp_path: Path):
    source = tmp_path / "platform-defaults.json"
    source.write_text(json.dumps(_source_doc(effort="xhigh", model="sonnet")), encoding="utf-8")

    stub = claude_integration.build_project_settings_stub((source,))

    assert stub["effortLevel"] == "xhigh"
    assert stub["model"] == "sonnet"
    assert stub["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == "xhigh"


def test_stub_preserves_its_key_order_and_static_parts(tmp_path: Path):
    source = tmp_path / "platform-defaults.json"
    source.write_text(json.dumps(_source_doc()), encoding="utf-8")

    stub = claude_integration.build_project_settings_stub((source,))

    assert list(stub) == ["_comment", "effortLevel", "model", "env", "permissions"]
    assert stub["permissions"]["allow"] == ["Read", "Glob", "Grep"]
    assert "platform-defaults.json" in stub["_comment"]


def test_stub_falls_back_silently_when_the_source_is_absent(tmp_path: Path, capsys):
    """Absence is the NORMAL installed-tree case, so it must not print a note.

    The installers deliberately do not copy configs/ into ~/.nexus-hub, so a
    note on absence would fire on every `nexus-hub init` for installed users.
    """
    stub = claude_integration.build_project_settings_stub((tmp_path / "absent.json",))

    assert stub["effortLevel"] == claude_integration._FALLBACK_SETTINGS["effortLevel"]
    assert stub["model"] == claude_integration._FALLBACK_SETTINGS["model"]
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_stub_notes_once_when_the_source_is_malformed(tmp_path: Path, capsys):
    """A file that exists but cannot be parsed IS worth surfacing."""
    source = tmp_path / "platform-defaults.json"
    source.write_text("{ not json", encoding="utf-8")

    stub = claude_integration.build_project_settings_stub((source,))

    assert stub["effortLevel"] == claude_integration._FALLBACK_SETTINGS["effortLevel"]
    captured = capsys.readouterr()
    assert "unreadable" in captured.err
    assert captured.err.count("\n") == 1, "the degradation note must be one line"


def test_stub_never_raises_on_a_structurally_wrong_source(tmp_path: Path):
    source = tmp_path / "platform-defaults.json"
    source.write_text(json.dumps({"platforms": {}}), encoding="utf-8")

    stub = claude_integration.build_project_settings_stub((source,))

    assert stub["effortLevel"] == claude_integration._FALLBACK_SETTINGS["effortLevel"]


def test_stub_prefers_the_first_existing_candidate(tmp_path: Path):
    """Candidate order is priority order: a checkout wins over the bootstrap copy."""
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps(_source_doc(effort="high")), encoding="utf-8")
    second.write_text(json.dumps(_source_doc(effort="low")), encoding="utf-8")

    stub = claude_integration.build_project_settings_stub((first, second))

    assert stub["effortLevel"] == "high"


def test_stub_skips_a_missing_candidate_and_uses_the_next(tmp_path: Path):
    second = tmp_path / "second.json"
    second.write_text(json.dumps(_source_doc(effort="low")), encoding="utf-8")

    stub = claude_integration.build_project_settings_stub((tmp_path / "absent.json", second))

    assert stub["effortLevel"] == "low"


def test_module_holds_no_hardcoded_stub_constant():
    """The old `_PROJECT_SETTINGS_STUB` literal must be gone, not merely unused."""
    body = (REPO_ROOT / "scripts" / "lib" / "integrations" / "claude.py").read_text(
        encoding="utf-8"
    )
    assert "_PROJECT_SETTINGS_STUB" not in body


def test_drift_check_is_wired_into_make_validate():
    """Plan 1.4 acceptance: drift must be a build failure, not a discovery.

    Asserted structurally because a guard nobody runs is not a guard.
    """
    body = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "sync_platform_defaults.py --check" in body, (
        "the `validate` target must run the defaults drift check"
    )


def test_drift_check_is_wired_into_ci():
    assert_wired_into_ci("sync_platform_defaults.py")


def test_script_is_classified_as_a_repo_internal_guard():
    """It needs no installer copy step, which is what keeps both installers untouched."""
    body = (REPO_ROOT / "catalog" / "hooks" / "tests" / "test_installer_smoke.py").read_text(
        encoding="utf-8"
    )
    assert '"sync_platform_defaults.py",' in body, (
        "sync_platform_defaults.py must be in DEV_ONLY_SCRIPTS; it is a repo-internal "
        "guard with no meaning on an end-user install"
    )


def test_configs_readme_documents_the_source():
    readme = REPO_ROOT / "configs" / "README.md"
    assert readme.is_file(), "configs/README.md must document the defaults schema"
    body = readme.read_text(encoding="utf-8")
    for expected in ("platform-defaults.json", "sync_platform_defaults.py", "schema_version"):
        assert expected in body, f"configs/README.md should document {expected}"


def test_real_fallback_matches_the_real_declared_values():
    """The offline fallback must not quietly state something untrue."""
    declared = json.loads(REAL_SOURCE.read_text(encoding="utf-8"))["platforms"]["claude"][
        "settings"
    ]
    assert claude_integration._FALLBACK_SETTINGS == declared
