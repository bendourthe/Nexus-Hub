"""Tests for the shared permission-merge helper (scripts/merge_permissions.py).

This helper is the ONLY merge implementation both installers use, so its behavior is
the cross-platform parity contract itself. The tests that matter most are the ones
guarding the two properties a union merge does not have:

* **Removal propagation.** An entry a prior Nexus-Hub version shipped and this one no
  longer ships must be retired from an existing config, or the Phase 1.1 hardening
  reaches only fresh installs -- not the already-installed hosts it was written to
  protect.
* **User-entry safety.** The same pass must never touch an entry the user added, which
  is why "previously shipped" comes from a recorded manifest rather than being inferred.

Byte parity with the historical ``jq`` path is asserted by CONSTRUCTING the expected
output (sorted-unique array, 2-space indent, trailing newline) rather than shelling out
to ``jq``, which is absent on the Windows development host. When ``jq`` IS present the
comparison additionally runs against real ``jq`` output.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts" / "merge_permissions.py"
JQ = shutil.which("jq")


def _load():
    spec = importlib.util.spec_from_file_location("merge_permissions", HELPER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mp = _load()

TEMPLATE = {
    "_description": "template documentation, must never reach a live config",
    "permissions": {
        "allow": ["Bash(ls *)", "Read"],
        "_hardening": {"removed": ["Bash(gh api *)"], "why": "admits --method DELETE"},
    },
}


@pytest.fixture
def template(tmp_path: Path) -> Path:
    path = tmp_path / "template.json"
    path.write_text(json.dumps(TEMPLATE, indent=2), encoding="utf-8")
    return path


def _settings(tmp_path: Path, allow: list[str], **extra) -> Path:
    path = tmp_path / "settings.json"
    payload = {"permissions": {"allow": allow}}
    payload.update(extra)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _manifest(tmp_path: Path, shipped: dict[str, list[str]]) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"shipped": shipped}), encoding="utf-8")
    return path


def _allow(path: Path) -> list[str]:
    return json.loads(path.read_text(encoding="utf-8"))["permissions"]["allow"]


# --- Array merge -------------------------------------------------------------


def test_union_adds_new_entries(tmp_path: Path, template: Path) -> None:
    settings = _settings(tmp_path, ["Read"])
    added, removed = mp.merge(template, settings, "permissions.allow")
    assert added == 1 and removed == []
    assert _allow(settings) == ["Bash(ls *)", "Read"]


def test_removal_propagates_for_a_retired_shipped_entry(tmp_path: Path, template: Path) -> None:
    """The A3 bug-2 fix: without this, every mutation-capable entry removed in Phase 1.1
    stays auto-approved forever on every already-installed host."""
    settings = _settings(tmp_path, ["Read", "Bash(gh api *)"])
    manifest = _manifest(tmp_path, {"CLAUDE": ["Read", "Bash(gh api *)"]})

    added, removed = mp.merge(template, settings, "permissions.allow",
                              manifest_path=manifest, platform="CLAUDE")

    assert removed == ["Bash(gh api *)"], "a retired shipped entry must be removed"
    assert "Bash(gh api *)" not in _allow(settings)


def test_a_user_added_entry_is_never_removed(tmp_path: Path, template: Path) -> None:
    """The safety half of removal propagation. The user's entry is not in the manifest,
    so it cannot be mistaken for a stale Nexus-Hub one."""
    settings = _settings(tmp_path, ["Read", "Bash(my-own-tool *)"])
    manifest = _manifest(tmp_path, {"CLAUDE": ["Read", "Bash(gh api *)"]})

    mp.merge(template, settings, "permissions.allow",
             manifest_path=manifest, platform="CLAUDE")

    assert "Bash(my-own-tool *)" in _allow(settings)


def test_absent_manifest_degrades_to_add_only(tmp_path: Path, template: Path) -> None:
    """A missing or damaged manifest disables removals rather than failing the install:
    no removal can be PROVEN safe without it, and a broken bookkeeping file is a worse
    reason to abort an install than to skip one pass of retirement."""
    settings = _settings(tmp_path, ["Read", "Bash(gh api *)"])
    added, removed = mp.merge(template, settings, "permissions.allow",
                              manifest_path=tmp_path / "absent.json", platform="CLAUDE")
    assert removed == []
    assert "Bash(gh api *)" in _allow(settings), "nothing may be removed unprovably"
    assert added == 1


def test_corrupt_manifest_degrades_to_add_only(tmp_path: Path, template: Path) -> None:
    bad = tmp_path / "manifest.json"
    bad.write_text("{not json", encoding="utf-8")
    settings = _settings(tmp_path, ["Read", "Bash(gh api *)"])
    _, removed = mp.merge(template, settings, "permissions.allow",
                          manifest_path=bad, platform="CLAUDE")
    assert removed == []


def test_template_metadata_never_reaches_a_live_config(tmp_path: Path, template: Path) -> None:
    """The old no-jq creation path used a plain `cp` and DID copy these keys."""
    settings = tmp_path / "settings.json"  # absent: exercise the creation path
    mp.merge(template, settings, "permissions.allow")
    blob = settings.read_text(encoding="utf-8")
    assert "_description" not in blob
    assert "_hardening" not in blob
    assert _allow(settings) == ["Bash(ls *)", "Read"]


def test_sibling_keys_and_user_content_survive(tmp_path: Path, template: Path) -> None:
    settings = _settings(tmp_path, ["Read"], someUserKey="preserve-me")
    mp.merge(template, settings, "permissions.allow")
    assert json.loads(settings.read_text(encoding="utf-8"))["someUserKey"] == "preserve-me"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows held handles block replacement")
def test_wn4_transient_held_settings_handle_does_not_abort_merge(
    tmp_path: Path, template: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A temporary reader must not abort a settings merge or discard user keys."""
    import threading

    settings = _settings(tmp_path, ["Read"], someUserKey="preserve-me")
    handle = settings.open("rb")
    release: threading.Timer | None = None
    real_replace = Path.replace

    def replace_while_held(path: Path, target: Path) -> Path:
        nonlocal release
        if target == settings and release is None:
            release = threading.Timer(0.3, handle.close)
            release.start()
        return real_replace(path, target)

    monkeypatch.setattr(Path, "replace", replace_while_held)
    try:
        mp.merge(template, settings, "permissions.allow")
    finally:
        handle.close()
        if release is not None:
            release.join()

    assert json.loads(settings.read_text(encoding="utf-8"))["someUserKey"] == "preserve-me"


def test_wn4_permanent_replacement_denial_preserves_settings(
    tmp_path: Path, template: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A persistent denial must surface and leave no staged settings file."""
    settings = _settings(tmp_path, ["Read"], someUserKey="preserve-me")
    original = settings.read_bytes()
    real_replace = Path.replace

    def deny_settings_replace(path: Path, target: Path) -> Path:
        if target == settings:
            raise PermissionError(13, "Access is denied", str(path))
        return real_replace(path, target)

    monkeypatch.setattr(Path, "replace", deny_settings_replace)
    with pytest.raises(PermissionError):
        mp.merge(template, settings, "permissions.allow")

    assert settings.read_bytes() == original
    assert not list(tmp_path.glob("*.tmp"))


def test_wn4_retry_refuses_a_concurrent_user_edit(
    tmp_path: Path, template: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A retry must not replace settings that changed after the merge read."""
    settings = _settings(tmp_path, ["Read"], someUserKey="preserve-me")
    real_replace = Path.replace
    observed = {"attempts": 0}

    def edit_then_deny(path: Path, target: Path) -> Path:
        if target == settings:
            observed["attempts"] += 1
            if observed["attempts"] == 1:
                settings.write_text('{"someUserKey": "changed by user"}', encoding="utf-8")
                raise PermissionError(13, "Access is denied", str(path))
        return real_replace(path, target)

    monkeypatch.setattr(Path, "replace", edit_then_deny)
    with pytest.raises(ValueError, match="changed"):
        mp.merge(template, settings, "permissions.allow")

    assert observed["attempts"] == 1
    assert json.loads(settings.read_text(encoding="utf-8"))["someUserKey"] == "changed by user"
    assert not list(tmp_path.glob("*.tmp"))


def test_backup_is_taken_before_any_change(tmp_path: Path, template: Path) -> None:
    settings = _settings(tmp_path, ["Read"])
    original = settings.read_text(encoding="utf-8")
    mp.merge(template, settings, "permissions.allow")
    backups = list(tmp_path.glob("settings.json.bak.*"))
    assert len(backups) == 1, f"expected exactly one backup, got {backups}"
    assert backups[0].read_text(encoding="utf-8") == original, (
        "the backup must hold the PRE-merge content"
    )


def test_no_backup_and_no_write_when_already_current(tmp_path: Path, template: Path) -> None:
    """Idempotence: a re-run must not churn the file or litter backups."""
    settings = _settings(tmp_path, ["Read"])
    mp.merge(template, settings, "permissions.allow")
    after_first = settings.read_text(encoding="utf-8")

    added, removed = mp.merge(template, settings, "permissions.allow")

    assert (added, removed) == (0, [])
    assert settings.read_text(encoding="utf-8") == after_first
    assert len(list(tmp_path.glob("settings.json.bak.*"))) == 1


def test_write_leaves_no_temp_residue(tmp_path: Path, template: Path) -> None:
    """The write is temp-file-plus-rename, so a completed merge must leave no .tmp
    behind and the result must be parseable -- a truncated settings.json breaks the
    user's agent entirely."""
    settings = _settings(tmp_path, ["Read"])
    mp.merge(template, settings, "permissions.allow")
    assert not list(tmp_path.glob("*.tmp")), "temp file survived the rename"
    json.loads(settings.read_text(encoding="utf-8"))


def test_unparseable_settings_leaves_the_file_untouched(tmp_path: Path, template: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text("{ not json", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        mp.merge(template, settings, "permissions.allow")
    assert settings.read_text(encoding="utf-8") == "{ not json"


def test_output_is_byte_identical_to_the_jq_shape(tmp_path: Path, template: Path) -> None:
    """jq's `unique` de-duplicates AND sorts, and jq's default output is 2-space
    indented with a trailing newline. The expected bytes are CONSTRUCTED here rather
    than produced by shelling out, because jq is absent on the Windows dev host."""
    settings = _settings(tmp_path, ["Read", "Bash(zzz)"])
    mp.merge(template, settings, "permissions.allow")

    expected = json.dumps(
        {"permissions": {"allow": sorted({"Read", "Bash(zzz)", "Bash(ls *)"})}},
        indent=2, ensure_ascii=False,
    ) + "\n"
    assert settings.read_text(encoding="utf-8") == expected


@pytest.mark.skipif(not JQ, reason="jq not installed (v3.17.0: dev host has no jq)")
def test_output_matches_real_jq_when_available(tmp_path: Path, template: Path) -> None:
    """The same assertion against real jq, for hosts that have it."""
    settings = _settings(tmp_path, ["Read", "Bash(zzz)"])
    mp.merge(template, settings, "permissions.allow")

    jq_out = subprocess.run(
        [JQ, "{permissions: {allow: (.permissions.allow | unique)}}", str(settings)],
        capture_output=True, text=True, check=True,
    ).stdout
    assert settings.read_text(encoding="utf-8") == jq_out


# --- Scalar mode (Copilot) ---------------------------------------------------


def test_set_true_writes_a_literal_dotted_key(tmp_path: Path) -> None:
    """VS Code's settings.json is FLAT: its dotted keys are single literal keys. Writing
    a nested object here would leave the setting silently off."""
    settings = tmp_path / "vscode.json"
    settings.write_text(json.dumps({"editor.fontSize": 12}), encoding="utf-8")
    key = "github.copilot.chat.codeGeneration.useInstructionFiles"

    assert mp.set_true(settings, key) is True

    doc = json.loads(settings.read_text(encoding="utf-8"))
    assert doc[key] is True, "the key must be literal, not a nested path"
    assert "github" not in doc, "a nested object means VS Code never reads the setting"
    assert doc["editor.fontSize"] == 12, "unrelated user settings must survive"


def test_set_true_is_idempotent_and_does_not_rewrite(tmp_path: Path) -> None:
    settings = tmp_path / "vscode.json"
    key = "github.copilot.chat.codeGeneration.useInstructionFiles"
    settings.write_text(json.dumps({key: True}), encoding="utf-8")
    before = settings.read_text(encoding="utf-8")

    assert mp.set_true(settings, key) is False
    assert settings.read_text(encoding="utf-8") == before
    assert not list(tmp_path.glob("*.bak.*")), "a no-op must not create a backup"


def test_set_true_creates_an_absent_settings_file(tmp_path: Path) -> None:
    settings = tmp_path / "vscode.json"
    assert mp.set_true(settings, "some.key") is True
    assert json.loads(settings.read_text(encoding="utf-8")) == {"some.key": True}


# --- CLI output protocol -----------------------------------------------------


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(HELPER), *args],
                          capture_output=True, text=True, check=False)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows held handles block replacement")
def test_cli_wn4_held_settings_handle_merges_after_release(
    tmp_path: Path, template: Path
) -> None:
    """Exercise the installer-facing CLI while a reader briefly holds settings."""
    import threading

    settings = _settings(tmp_path, ["Read"], someUserKey="preserve-me")
    handle = settings.open("rb")
    release = threading.Timer(0.3, handle.close)
    release.start()
    try:
        proc = _cli("--template", str(template), "--settings", str(settings))
    finally:
        handle.close()
        release.join()

    assert proc.returncode == 0, proc.stderr
    assert "added: 1" in proc.stdout
    assert _allow(settings) == ["Bash(ls *)", "Read"]
    assert json.loads(settings.read_text(encoding="utf-8"))["someUserKey"] == "preserve-me"


def test_cli_reports_added_and_removed_on_stdout(tmp_path: Path, template: Path) -> None:
    """Both installers parse stdout and nothing else: in Windows PowerShell 5.1,
    redirecting a native command's stderr wraps each line in an ErrorRecord and flips
    $? to false even on a clean exit, so removals may not be reported there."""
    settings = _settings(tmp_path, ["Read", "Bash(gh api *)"])
    manifest = _manifest(tmp_path, {"CLAUDE": ["Read", "Bash(gh api *)"]})

    proc = _cli("--template", str(template), "--settings", str(settings),
                "--key", "permissions.allow", "--manifest", str(manifest),
                "--platform", "CLAUDE")

    assert proc.returncode == 0, proc.stderr
    assert "added: 1" in proc.stdout
    assert "removed: Bash(gh api *)" in proc.stdout
    assert "removed:" not in proc.stderr, "removals must not be reported on stderr"


def test_cli_set_true_reports_set_on_stdout(tmp_path: Path) -> None:
    settings = tmp_path / "vscode.json"
    settings.write_text("{}", encoding="utf-8")
    proc = _cli("--settings", str(settings), "--set-true", "a.b")
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "set: a.b"


def test_cli_set_true_needs_no_template(tmp_path: Path) -> None:
    """--set-true writes a key rather than copying entries, so requiring --template
    would force callers to pass an unused path."""
    settings = tmp_path / "vscode.json"
    proc = _cli("--settings", str(settings), "--set-true", "a.b")
    assert proc.returncode == 0, proc.stderr


def test_cli_rejects_a_manifest_without_a_platform(tmp_path: Path, template: Path) -> None:
    proc = _cli("--template", str(template), "--settings", str(tmp_path / "s.json"),
                "--manifest", str(tmp_path / "m.json"))
    assert proc.returncode == 2
    assert "--manifest and --platform" in proc.stderr


def test_cli_requires_a_template_for_an_array_merge(tmp_path: Path) -> None:
    proc = _cli("--settings", str(tmp_path / "s.json"), "--key", "permissions.allow")
    assert proc.returncode == 2
    assert "--template is required" in proc.stderr


def test_manifest_records_what_this_version_shipped(tmp_path: Path, template: Path) -> None:
    """Retirement next upgrade depends on this record being written this upgrade."""
    settings = _settings(tmp_path, ["Read"])
    manifest = tmp_path / "manifest.json"
    mp.merge(template, settings, "permissions.allow",
             manifest_path=manifest, platform="CLAUDE")

    shipped = json.loads(manifest.read_text(encoding="utf-8"))["shipped"]["CLAUDE"]
    assert shipped == ["Bash(ls *)", "Read"], "the manifest must record the template set"


# --- UTF-8 BOM tolerance -----------------------------------------------------
#
# PowerShell 5.1's `Set-Content -Encoding utf8` emits a UTF-8 BOM (AGENTS.md
# documents that trap for hook authors). Decoding such a file as plain "utf-8"
# leaves a leading U+FEFF and json.loads fails with "Unexpected UTF-8 BOM".
# That is what made the Gemini permission sync fail on a real Windows install
# while every other platform succeeded, so reads use "utf-8-sig" and writes stay
# plain "utf-8" -- the tool must tolerate a BOM without ever emitting one.

BOM = "\ufeff"


def _with_bom(path: Path) -> Path:
    """Rewrite *path* with a leading UTF-8 BOM, as PowerShell 5.1 would."""
    path.write_text(BOM + path.read_text(encoding="utf-8"), encoding="utf-8")
    return path


def _has_bom(path: Path) -> bool:
    return path.read_bytes().startswith(b"\xef\xbb\xbf")


def test_the_bom_control_actually_breaks_a_naive_reader() -> None:
    """Without this, the tests below could pass for the wrong reason."""
    with pytest.raises(json.JSONDecodeError):
        json.loads(BOM + '{"a": 1}')
    assert json.loads((BOM + '{"a": 1}').encode("utf-8").decode("utf-8-sig")) == {"a": 1}


def test_reads_use_a_bom_tolerant_encoding() -> None:
    assert mp._READ_ENCODING == "utf-8-sig"


def test_settings_with_a_bom_still_merges(tmp_path: Path, template: Path) -> None:
    settings = _with_bom(_settings(tmp_path, ["Read"]))
    assert _has_bom(settings), "fixture did not actually get a BOM"
    added, removed = mp.merge(template, settings, "permissions.allow")
    assert added == 1 and removed == []
    assert _allow(settings) == ["Bash(ls *)", "Read"]


def test_template_with_a_bom_still_merges(tmp_path: Path, template: Path) -> None:
    _with_bom(template)
    settings = _settings(tmp_path, ["Read"])
    added, _ = mp.merge(template, settings, "permissions.allow")
    assert added == 1
    assert _allow(settings) == ["Bash(ls *)", "Read"]


def test_merging_never_leaves_a_bom_behind(tmp_path: Path, template: Path) -> None:
    """Reads tolerate a BOM; writes must not propagate or introduce one."""
    settings = _with_bom(_settings(tmp_path, ["Read"]))
    mp.merge(template, settings, "permissions.allow")
    assert not _has_bom(settings), "merge wrote a BOM back into the config"


def test_manifest_with_a_bom_is_read_not_silently_discarded(
    tmp_path: Path, template: Path
) -> None:
    """A BOM must not make a valid manifest look corrupt.

    _read_manifest degrades to add-only on a decode error, so a BOM would have
    silently disabled removal propagation -- the exact hardening the manifest
    exists to deliver -- with no error surfaced anywhere.
    """
    manifest = _with_bom(_manifest(tmp_path, {"CLAUDE": ["Read", "Bash(gh api *)"]}))
    settings = _settings(tmp_path, ["Read", "Bash(gh api *)"])
    _, removed = mp.merge(
        template, settings, "permissions.allow",
        manifest_path=manifest, platform="CLAUDE",
    )
    assert removed == ["Bash(gh api *)"], (
        "a BOM-prefixed manifest was treated as corrupt, silently degrading to "
        "add-only and leaving the retired entry in place"
    )
