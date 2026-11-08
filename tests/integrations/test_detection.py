"""Tests for platform detection, manifest preservation, and verify agreement (v4.14.7 Phase 1).

`_detection.detect_platform` decides whether a gated platform's tool is present
by evidence Nexus-Hub did not create itself. Every test injects `which` and a
temporary home, so no case reads the developer's real PATH or home folder.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import _detection, get  # noqa: E402
from scripts.lib.integrations._detection import (  # noqa: E402
    detect_platform,
    safe_which,
)
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402
from scripts.lib.integrations.result import FileAction, WriteResult  # noqa: E402
from scripts.lib.integrations import runner  # noqa: E402

GATED = ("kimi", "qwen", "hermes", "pi", "nexus-ai", "aider", "opencode")


def _no_path(_name: str):
    return None


class _Fake:
    """A stand-in integration carrying only a detection spec."""

    def __init__(self, spec: dict, key: str = "fake") -> None:
        self.key = key
        self.config = {"detection": spec}


@pytest.fixture
def home(tmp_path: Path) -> Path:
    path = tmp_path / "home"
    path.mkdir()
    return path


def _ctx(home: Path, *, which=_no_path, manifest=None, forced=frozenset()) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=home,
        scope="global",
        explicit_target=True,
        manifest=manifest or InstallManifest(),
        which=which,
        forced_keys=frozenset(forced),
    )


# ---------------------------------------------------------------------------
# Root classification
# ---------------------------------------------------------------------------


def test_absent_root_and_no_executable_is_not_detected(home: Path) -> None:
    verdict = detect_platform(_ctx(home), get("kimi"))
    assert not verdict.detected
    assert "kimi not on PATH" in verdict.evidence


def test_empty_root_is_not_detected(home: Path) -> None:
    (home / ".kimi-code").mkdir()
    verdict = detect_platform(_ctx(home), get("kimi"))
    assert not verdict.detected
    assert "is empty" in verdict.evidence


def test_root_holding_only_tracked_files_is_not_detected(home: Path) -> None:
    root = home / ".qwen"
    (root / "skills" / "demo").mkdir(parents=True)
    (root / "skills" / "demo" / "SKILL.md").write_text("x", encoding="utf-8")
    (root / "notes.txt").write_text("written by an old install", encoding="utf-8")
    manifest = InstallManifest()
    manifest.track("qwen", str(root / "skills" / "demo"))
    manifest.track("qwen", str(root / "notes.txt"))
    verdict = detect_platform(_ctx(home, manifest=manifest), get("qwen"))
    assert not verdict.detected
    assert "only Nexus-Hub files" in verdict.evidence


def test_metadata_backups_and_declared_names_are_not_evidence(home: Path) -> None:
    """The maintainer's 2026-10-29 ~/.kimi-code: every entry was Nexus-Hub's."""
    root = home / ".kimi-code"
    for name in ("skills", "agents", "hooks"):
        (root / name).mkdir(parents=True)
    for name in ("AGENTS.md", "config.toml", "config.toml.nexus-hub.bak",
                 "config.toml.nexus-hub.tmp", "desktop.ini", ".DS_Store", "Thumbs.db"):
        (root / name).write_text("x", encoding="utf-8")
    verdict = detect_platform(_ctx(home), get("kimi"))
    assert not verdict.detected
    assert "only Nexus-Hub files" in verdict.evidence


def test_one_vendor_entry_is_evidence(home: Path) -> None:
    (home / ".kimi-code" / "sessions").mkdir(parents=True)
    verdict = detect_platform(_ctx(home), get("kimi"))
    assert verdict.detected and verdict.kind == "root"
    assert "sessions" in verdict.evidence


def test_pi_root_is_the_agent_folder(home: Path) -> None:
    """~/.pi holds only agent/, which Pi and Nexus-Hub both create."""
    agent = home / ".pi" / "agent"
    (agent / "skills").mkdir(parents=True)
    (agent / "settings.json").write_text("{}", encoding="utf-8")
    assert not detect_platform(_ctx(home), get("pi")).detected
    (agent / "auth.json").write_text("{}", encoding="utf-8")
    assert detect_platform(_ctx(home), get("pi")).detected


def test_manifest_path_spelling_differences_still_match(home: Path) -> None:
    root = home / ".hermes"
    (root / "custom").mkdir(parents=True)
    spelled = str(root / "custom").replace("\\", "/")
    if os.name == "nt":
        spelled = spelled.upper()
    manifest = InstallManifest()
    manifest.track("hermes", spelled)
    assert not detect_platform(_ctx(home, manifest=manifest), get("hermes")).detected


def test_detection_never_creates_the_root(home: Path) -> None:
    for key in GATED:
        detect_platform(_ctx(home), get(key))
    assert list(home.iterdir()) == []


# ---------------------------------------------------------------------------
# Vendor roots and applications
# ---------------------------------------------------------------------------


def test_nexus_session_digest_folder_is_not_nexus_ai_evidence(home: Path) -> None:
    nexus = home / ".nexus"
    (nexus / "context").mkdir(parents=True)
    (nexus / "observations.jsonl").write_text("{}", encoding="utf-8")
    assert not detect_platform(_ctx(home), get("nexus-ai")).detected
    (nexus / "sessions").mkdir()
    verdict = detect_platform(_ctx(home), get("nexus-ai"))
    assert verdict.detected and ".nexus" in verdict.evidence


def test_nexus_ai_catalog_alone_is_not_evidence(home: Path) -> None:
    (home / ".nexus-ai" / "catalog").mkdir(parents=True)
    assert not detect_platform(_ctx(home), get("nexus-ai")).detected


def test_opencode_data_folder_is_evidence(home: Path) -> None:
    (home / ".config" / "opencode" / "skills").mkdir(parents=True)
    assert not detect_platform(_ctx(home), get("opencode")).detected
    data = home / ".local" / "share" / "opencode"
    data.mkdir(parents=True)
    (data / "opencode.db").write_text("x", encoding="utf-8")
    assert detect_platform(_ctx(home), get("opencode")).detected


def test_installed_app_path_is_evidence(home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = tmp_path / "apps" / "Studio.app"
    app.mkdir(parents=True)
    monkeypatch.setenv("FAKE_APPS", str(tmp_path / "apps"))
    monkeypatch.setattr(sys, "platform", "fakeos")
    spec = {"root": ".studio", "app_paths": {"fakeos": ["$FAKE_APPS/Studio.app"]}}
    assert detect_platform(_ctx(home), _Fake(spec)).kind == "app"
    monkeypatch.delenv("FAKE_APPS")
    assert not detect_platform(_ctx(home), _Fake(spec)).detected


# ---------------------------------------------------------------------------
# Executables
# ---------------------------------------------------------------------------


def test_executable_on_path_is_evidence(home: Path) -> None:
    verdict = detect_platform(_ctx(home, which=lambda n: f"/usr/bin/{n}"), get("qwen"))
    assert verdict.detected and verdict.kind == "executable"
    assert "/usr/bin/qwen" in verdict.evidence


def test_collision_prone_name_needs_corroboration(home: Path) -> None:
    js_engine = _ctx(home, which=lambda n: "/opt/facebook/bin/hermes")
    assert not detect_platform(js_engine, get("hermes")).detected
    agent = _ctx(home, which=lambda n: "C:\\Users\\u\\AppData\\Local\\hermes\\bin\\hermes.cmd")
    assert detect_platform(agent, get("hermes")).detected


def test_redirected_root_falls_through_to_path(home: Path, tmp_path: Path) -> None:
    real = tmp_path / "dotfiles" / "kimi"
    (real / "sessions").mkdir(parents=True)
    link = home / ".kimi-code"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        if os.name != "nt":
            pytest.skip("symlink creation is not permitted on this host")
        import _winapi  # a directory junction needs no privilege

        _winapi.CreateJunction(str(real), str(link))
    alone = detect_platform(_ctx(home), get("kimi"))
    assert not alone.detected and "redirected" in alone.evidence
    assert detect_platform(_ctx(home, which=lambda n: "/usr/bin/kimi"), get("kimi")).detected


def test_safe_which_never_searches_the_current_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tool_dir = tmp_path / "tools"
    tool_dir.mkdir()
    name = "faketool"
    target = tool_dir / (name + (".cmd" if os.name == "nt" else ""))
    target.write_text("@echo off\n" if os.name == "nt" else "#!/bin/sh\n", encoding="utf-8")
    target.chmod(0o755)
    monkeypatch.chdir(tool_dir)
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    assert safe_which(name, path=os.pathsep.join(["", ".", "tools"])) is None
    found = safe_which(name, path=str(tool_dir))
    assert found is not None
    assert os.path.normcase(found) == os.path.normcase(os.path.abspath(target))


# ---------------------------------------------------------------------------
# Forcing and ungated platforms
# ---------------------------------------------------------------------------


def test_forced_key_is_detected(home: Path) -> None:
    assert detect_platform(_ctx(home, forced={"qwen"}), get("qwen")).kind == "forced"
    manifest = InstallManifest()
    manifest.set_forced("pi")
    assert detect_platform(_ctx(home, manifest=manifest), get("pi")).kind == "forced"


def test_ungated_platform_is_reported_ungated(home: Path) -> None:
    assert detect_platform(_ctx(home), get("claude")).kind == "ungated"


# ---------------------------------------------------------------------------
# Manifest preservation (1.3)
# ---------------------------------------------------------------------------


class _Toggle:
    key = "kimi"
    display_name = "Toggle"
    config = {"instruction_file": "AGENTS.md"}

    def __init__(self, target: Path) -> None:
        self.present = True
        self.target = target

    def install(self, ctx) -> WriteResult:  # noqa: ANN001 - test double
        result = WriteResult()
        if not self.present:
            result.mark_not_detected("not detected")
            return result
        self.target.write_text("owned", encoding="utf-8")
        result.detected = True
        result.files.append(FileAction(path=str(self.target), action="created"))
        return result


def _args(target: Path) -> argparse.Namespace:
    return argparse.Namespace(
        integrations="kimi", target=str(target), scope="global", overwrite=False,
        dry_run=False, quiet=True, project_name=None, var=None, languages=None,
        instruction_only=False, summary_json=None,
    )


def test_not_detected_install_keeps_previous_hashes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    toggle = _Toggle(target / "owned.txt")
    monkeypatch.setattr(runner, "get", lambda key: toggle)
    assert runner.cmd_install(_args(target)) == 0
    before = InstallManifest.load(runner._manifest_path(target)).actions_for("kimi")
    assert before and before[0]["sha256"]
    toggle.present = False
    assert runner.cmd_install(_args(target)) == 0
    after = InstallManifest.load(runner._manifest_path(target)).actions_for("kimi")
    assert after == before
    from scripts.lib.integrations.manifest import manifest_lock

    with manifest_lock(runner._manifest_path(target), timeout=2) as held:  # released when the install ended
        assert held is True


def test_corrupt_manifest_is_set_aside(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    path = tmp_path / ".nexus-hub" / "install-manifest.json"
    path.parent.mkdir()
    path.write_text("{not json", encoding="utf-8")
    manifest = InstallManifest.load(path)
    assert manifest.all_keys() == []
    assert not path.exists()
    assert len(list(path.parent.glob("install-manifest.json.corrupt-*"))) == 1
    assert "unreadable" in capsys.readouterr().err


def test_save_is_atomic_and_round_trips_forced(tmp_path: Path) -> None:
    path = tmp_path / "m" / "install-manifest.json"
    manifest = InstallManifest()
    manifest.set_forced("qwen")
    manifest.save(path)
    assert [p.name for p in path.parent.iterdir()] == ["install-manifest.json"]
    assert InstallManifest.load(path).is_forced("qwen")
    plain = InstallManifest()
    plain.save(path)
    assert "forced" not in json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Verify agreement (1.4)
# ---------------------------------------------------------------------------

_VERIFY_LABELS = {"kimi": "Kimi Code CLI", "qwen": "Qwen Code", "hermes": "Hermes", "pi": "Pi", "opencode": "OpenCode"}


@pytest.mark.parametrize("key", sorted(_VERIFY_LABELS))
@pytest.mark.parametrize("state", ["absent", "nexus-only", "executable"])
def test_verify_agrees_with_install_gate(key: str, state: str, home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    which = (lambda n: f"/usr/local/bin/{n}") if state == "executable" else _no_path
    if key == "hermes" and state == "executable":
        which = lambda n: "/home/u/.hermes/hermes-agent/bin/hermes"  # noqa: E731
    monkeypatch.setattr(_detection, "safe_which", which)
    spec = get(key).config["detection"]
    if state == "nexus-only":
        root = home / spec["root"]
        (root / spec["nexus_entries"][1]).mkdir(parents=True)
    gate = detect_platform(_ctx(home, which=which), get(key)).detected
    labels = {label for label, _surfaces, _hint in runner._verify_checks(home, tmp_path / "project")}
    assert (_VERIFY_LABELS[key] in labels) is gate


# ---------------------------------------------------------------------------
# Explicit platforms and install-summary messages (Phase 4)
# ---------------------------------------------------------------------------


def _install(target: Path, keys: str, forced: str = "") -> dict:
    summary = target / "summary.json"
    args = _args(target)
    args.integrations = keys
    args.forced = forced
    args.summary_json = str(summary)
    assert runner.cmd_install(args) == 0
    return json.loads(summary.read_text(encoding="utf-8"))


def test_forced_platform_installs_and_is_recorded(tmp_path: Path) -> None:
    target = tmp_path / "home"
    target.mkdir()
    payload = _install(target, "aider", forced="aider")
    assert payload["platforms"][0]["detected"] is True
    assert (target / ".aider.conf.yml").is_file()
    manifest = InstallManifest.load(runner._manifest_path(target))
    assert manifest.is_forced("aider")
    # A later default install keeps the platform without the flag.
    again = _install(target, "aider")
    assert again["platforms"][0]["detected"] is True


def test_forced_ignores_keys_outside_the_run(tmp_path: Path) -> None:
    target = tmp_path / "home"
    target.mkdir()
    _install(target, "aider", forced="qwen")
    manifest = InstallManifest.load(runner._manifest_path(target))
    assert not manifest.is_forced("qwen") and not manifest.is_forced("aider")


def test_summary_carries_evidence_and_remedy_when_not_detected(tmp_path: Path) -> None:
    target = tmp_path / "home"
    target.mkdir()
    platform = _install(target, "aider")["platforms"][0]
    assert platform["detected"] is False
    assert platform["evidence"] == "aider not on PATH"
    assert platform["remedy"] == "Install Aider, then run `nexus-hub upgrade`, or name it with --platforms aider."


# ---------------------------------------------------------------------------
# Real install layouts (v4.14.7 Phase 7, T044)
#
# One acceptance row per gated platform, built from the layout the vendor's own
# installer produces (docs/archives/v4/v4.14/development/v4.14.7-detection-signals.md),
# resolved by the real `safe_which` against real PATH directories. The other
# tests inject a fake `which`; these prove an installed tool is still FOUND.
# ---------------------------------------------------------------------------


def _stub_command(directory: Path, name: str, nt_ext: str) -> Path:
    """Create the file a vendor installer drops: `<name><ext>` on Windows, an
    executable `<name>` elsewhere. It is never executed, only resolved."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (name + nt_ext if os.name == "nt" else name)
    path.write_bytes(b"stub\n")
    path.chmod(0o755)
    return path


def _real_which(*directories: Path):
    search = os.pathsep.join(str(d) for d in directories)
    return lambda name: safe_which(name, path=search)


# (key, directory under the home, command, Windows extension, expected kind).
# A layout that also puts a vendor-owned entry in the platform's root is
# credited to the root check, which runs before the PATH probe.
REAL_EXECUTABLE_LAYOUTS = [
    pytest.param("kimi", ".local/bin", "kimi", ".exe", "executable", id="kimi-install-script-or-uv-tool"),
    pytest.param("qwen", "AppData/Roaming/npm", "qwen", ".cmd", "executable", id="qwen-npm-cmd-shim"),
    pytest.param("pi", "AppData/Roaming/npm", "pi", ".cmd", "executable", id="pi-npm-cmd-shim"),
    pytest.param("aider", ".local/bin", "aider", ".exe", "executable", id="aider-pipx"),
    pytest.param("opencode", "AppData/Roaming/npm", "opencode", ".cmd", "executable", id="opencode-npm-cmd-shim"),
    pytest.param("opencode", ".opencode/bin", "opencode", ".exe", "root", id="opencode-curl-installer"),
    pytest.param("hermes", "AppData/Local/hermes/hermes-agent/venv/Scripts", "hermes", ".exe", "executable", id="hermes-installer-windows"),
    pytest.param("hermes", ".hermes/hermes-agent/venv/bin", "hermes", ".exe", "root", id="hermes-installer-posix"),
]


@pytest.mark.parametrize(("key", "relative", "name", "ext", "kind"), REAL_EXECUTABLE_LAYOUTS)
def test_real_layout_installed_tool_is_found(
    home: Path, monkeypatch: pytest.MonkeyPatch, key: str, relative: str, name: str, ext: str, kind: str
) -> None:
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    directory = home / relative
    _stub_command(directory, name, ext)
    present = detect_platform(_ctx(home, which=_real_which(directory)), get(key))
    assert present.detected and present.kind == kind, present
    # The same machine with the vendor directory off PATH is not detected, so
    # the row proves the layout, not a lucky default.
    if kind == "executable":
        absent = detect_platform(_ctx(home, which=_real_which(home / "elsewhere")), get(key))
        assert not absent.detected and f"{name} not on PATH" in absent.evidence


def test_real_layout_npm_shim_set_is_found_through_the_cmd_shim(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """npm writes a `.cmd`, a `.ps1`, and an extensionless shim side by side."""
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    directory = home / "AppData" / "Roaming" / "npm"
    directory.mkdir(parents=True)
    for suffix in ("", ".cmd", ".ps1"):
        (directory / f"qwen{suffix}").write_bytes(b"stub\n")
    (directory / "qwen").chmod(0o755)
    verdict = detect_platform(_ctx(home, which=_real_which(directory)), get("qwen"))
    assert verdict.detected and verdict.kind == "executable"


def test_real_layout_hermes_javascript_engine_is_not_hermes_agent(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    engine = home / "tools" / "hermes-engine" / "bin"
    _stub_command(engine, "hermes", ".exe")
    verdict = detect_platform(_ctx(home, which=_real_which(engine)), get("hermes"))
    assert not verdict.detected and "hermes not on PATH" in verdict.evidence


def test_real_layout_opencode_curl_install_off_path_is_found_by_its_vendor_folder(home: Path) -> None:
    _stub_command(home / ".opencode" / "bin", "opencode", ".exe")
    verdict = detect_platform(_ctx(home), get("opencode"))
    assert verdict.detected and verdict.kind == "root" and ".opencode" in verdict.evidence


def test_real_layout_opencode_data_folder_is_found(home: Path) -> None:
    data = home / ".local" / "share" / "opencode"
    data.mkdir(parents=True)
    (data / "auth.json").write_text("{}", encoding="utf-8")
    verdict = detect_platform(_ctx(home), get("opencode"))
    assert verdict.detected and verdict.kind == "root"


@pytest.mark.parametrize(
    ("platform", "relative"),
    [
        pytest.param(
            "win32",
            "AppData/Local/Programs/Nexus AI Studio",
            id="nexus-ai-windows-per-user-installer",
            # The spec spells the folder `%LOCALAPPDATA%/...`, which only the Windows
            # `os.path.expandvars` expands. The detector evaluates a win32 entry only on
            # win32, so faking `sys.platform` cannot make another host expand it.
            marks=pytest.mark.skipif(os.name != "nt", reason="`%VAR%` expansion exists only on Windows"),
        ),
        pytest.param("darwin", "Applications/Nexus AI Studio.app", id="nexus-ai-macos-app-bundle"),
    ],
)
def test_real_layout_nexus_ai_installed_never_launched_is_found(
    home: Path, monkeypatch: pytest.MonkeyPatch, platform: str, relative: str
) -> None:
    from types import SimpleNamespace

    monkeypatch.setenv("LOCALAPPDATA", str(home / "AppData" / "Local"))
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setattr(_detection, "sys", SimpleNamespace(platform=platform))
    absent = detect_platform(_ctx(home), get("nexus-ai"))
    assert not absent.detected and "application not installed" in absent.evidence
    (home / relative).mkdir(parents=True)  # the app folder; `~/.nexus-ai` never created
    assert not (home / ".nexus-ai").exists()
    verdict = detect_platform(_ctx(home), get("nexus-ai"))
    assert verdict.detected and verdict.kind == "app", verdict

# ---------------------------------------------------------------------------
# Manifest lock and shape (v4.14.7 Phase 7, T044 adversarial findings)
# ---------------------------------------------------------------------------


def test_a_lock_held_by_a_live_run_times_out_instead_of_continuing(tmp_path: Path) -> None:
    from scripts.lib.integrations.manifest import ManifestLockTimeout, manifest_lock

    manifest_path = tmp_path / "install-manifest.json"
    with manifest_lock(manifest_path) as held:
        assert held is True
        with pytest.raises(ManifestLockTimeout):
            with manifest_lock(manifest_path, timeout=0.6):
                pytest.fail("entered the critical section without the lock")
    with manifest_lock(manifest_path, timeout=5) as again:  # released when the holder left
        assert again is True


def test_a_lock_file_left_by_a_crashed_run_never_blocks(tmp_path: Path) -> None:
    from scripts.lib.integrations.manifest import manifest_lock

    manifest_path = tmp_path / "install-manifest.json"
    (tmp_path / "install-manifest.json.lock").write_text("3999999", encoding="ascii")
    with manifest_lock(manifest_path, timeout=5) as held:  # nobody holds the operating-system lock
        assert held is True


def test_the_runner_reports_a_lock_timeout_without_a_traceback(tmp_path: Path, monkeypatch, capsys) -> None:
    from scripts.lib.integrations import manifest as manifest_module

    real_lock = manifest_module.manifest_lock
    monkeypatch.setattr(runner, "manifest_lock", lambda path, **kw: real_lock(path, timeout=0.4))
    with real_lock(runner._manifest_path(tmp_path)):
        assert runner.main(["prune-undetected", "--target", str(tmp_path)]) == 2
    assert "held by another running Nexus-Hub" in capsys.readouterr().err


@pytest.mark.parametrize(
    "payload",
    [
        {"actions": {"kimi": ["oops"]}},
        {"tracked": {"kimi": "C:/x"}},
        {"tracked": {"kimi": [1, 2]}},
        {"shared": []},
        {"actions": {"kimi": [{"path": 5}]}},
        {"logs": "text"},
    ],
)
def test_a_manifest_with_the_wrong_shape_is_set_aside_not_fatal(tmp_path: Path, payload: dict, capsys) -> None:
    path = tmp_path / "install-manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    manifest = InstallManifest.load(path)
    assert manifest.files_for("kimi") == [] and manifest.actions_for("kimi") == []
    assert not path.exists() and list(tmp_path.glob("install-manifest.json.corrupt-*"))
    assert "unreadable" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# Install-level regression for the circular folder test (plan sub-task 2.3)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "executable", "root"),
    [
        ("kimi", "kimi", ".kimi-code"),
        ("qwen", "qwen", ".qwen"),
        ("hermes", "hermes", ".hermes"),
        ("pi", "pi", ".pi"),
    ],
)
def test_a_root_holding_only_what_the_previous_install_wrote_is_not_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str, executable: str, root: str
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    prefix = "/opt/hermes-agent/bin" if key == "hermes" else "/opt/bin"  # Hermes needs its install path as corroboration
    monkeypatch.setattr(_detection, "safe_which", lambda name: f"{prefix}/{name}" if name == executable else None)
    first = _install(home, key)["platforms"][0]
    assert first["detected"] is True and (home / root).is_dir()
    written = sorted(p.relative_to(home).as_posix() for p in (home / root).rglob("*") if p.is_file())
    assert written, "the first install wrote nothing, so the regression proves nothing"

    monkeypatch.setattr(_detection, "safe_which", lambda name: None)  # the tool is not installed
    second = _install(home, key)["platforms"][0]
    assert second["detected"] is False
    assert "only Nexus-Hub files" in second["evidence"]
    assert sorted(p.relative_to(home).as_posix() for p in (home / root).rglob("*") if p.is_file()) == written
