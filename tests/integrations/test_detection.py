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
    assert not (runner._manifest_path(target).parent / "install-manifest.json.lock").exists()


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
