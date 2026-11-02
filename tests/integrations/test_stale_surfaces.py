"""Stale-surface report and verified opt-in removal (v4.14.7 Phase 5).

Each case starts from a real global Kimi install into a temporary home while a
fake `kimi` is on PATH, then takes the fake away, so the platform is genuinely
stale with real manifest records behind it.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import _detection, get, runner  # noqa: E402
from scripts.lib.integrations._stale import GONE, KEEP, REMOVE, STRIP, _classify_dir, apply_platform, find_stale, plan_platform  # noqa: E402
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402


def _install_args(home: Path, keys: str = "kimi") -> argparse.Namespace:
    return argparse.Namespace(
        integrations=keys, target=str(home), scope="global", overwrite=False, dry_run=False,
        quiet=True, project_name=None, var=None, languages=None, instruction_only=False,
        summary_json=None, forced="",
    )


def _prune_args(home: Path, yes: bool = False, unforce: str = "", keys: str = "") -> argparse.Namespace:
    return argparse.Namespace(target=str(home), integrations=keys or None, yes=yes, unforce=unforce)


@pytest.fixture
def stale_kimi(tmp_path: Path, fake_tools, monkeypatch) -> Path:
    """A home with a real Kimi install whose tool has since gone away."""
    home = tmp_path / "home"
    home.mkdir()
    fake_tools("kimi")
    assert runner.cmd_install(_install_args(home)) == 0
    monkeypatch.setattr(_detection, "safe_which", lambda _name: None)
    return home


def _ctx(home: Path):
    manifest = InstallManifest.load(runner._manifest_path(home))
    return runner._stale_ctx(home, manifest, dry_run=True)


def _tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _a_skill_file(home: Path) -> Path:
    return next((home / ".kimi-code" / "skills").rglob("SKILL.md"))


def test_report_lists_the_stale_platform(stale_kimi: Path) -> None:
    stale = find_stale(_ctx(stale_kimi), [get("kimi")])
    assert [s.key for s in stale] == ["kimi"]
    counts = stale[0].counts()
    assert counts[REMOVE] > 0
    assert counts[STRIP] >= 2  # config.toml hook block and the AGENTS.md marker block


def test_dry_run_changes_nothing(stale_kimi: Path, capsys) -> None:
    before = _tree(stale_kimi / ".kimi-code")
    assert runner.cmd_prune_undetected(_prune_args(stale_kimi)) == 0
    assert _tree(stale_kimi / ".kimi-code") == before
    assert "Dry run: nothing was removed" in capsys.readouterr().out


def test_removal_keeps_everything_the_user_owns(stale_kimi: Path) -> None:
    root = stale_kimi / ".kimi-code"
    edited = _a_skill_file(stale_kimi)
    edited.write_text(edited.read_text(encoding="utf-8") + "\nmy note\n", encoding="utf-8")
    added = edited.parent / "my-own-notes.md"
    added.write_text("mine", encoding="utf-8")
    # A real edit lands well after the install; within the same second it would
    # sit inside the mtime slack the folder rule allows.
    later = edited.stat().st_mtime + 3600
    for path in (edited, added):
        os.utime(path, (later, later))
    config = root / "config.toml"
    config.write_text(config.read_text(encoding="utf-8") + '\n[providers.mine]\napi_key = "secret"\n', encoding="utf-8")
    backup = root / "config.toml.nexus-hub.bak"
    backup.write_text("old settings", encoding="utf-8")

    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, yes=True)) == 0

    assert edited.is_file() and "my note" in edited.read_text(encoding="utf-8")
    assert added.is_file()
    assert backup.read_text(encoding="utf-8") == "old settings"
    text = config.read_text(encoding="utf-8")
    assert 'api_key = "secret"' in text
    assert "NEXUS_HUB_HOOKS_START" not in text
    assert not (root / "agents").exists() or not any((root / "agents").rglob("*.md"))
    remaining = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert remaining <= {
        "config.toml", "config.toml.nexus-hub.bak",
        edited.relative_to(root).as_posix(), added.relative_to(root).as_posix(),
    } | {p for p in remaining if p.endswith("AGENTS.md")}
    manifest = InstallManifest.load(runner._manifest_path(stale_kimi))
    assert not any("agents" in Path(p).parts and Path(p).suffix == ".md" for p in manifest.files_for("kimi"))


def test_forced_platform_is_never_offered(stale_kimi: Path) -> None:
    manifest_path = runner._manifest_path(stale_kimi)
    manifest = InstallManifest.load(manifest_path)
    manifest.set_forced("kimi")
    manifest.save(manifest_path)
    assert find_stale(_ctx(stale_kimi), [get("kimi")]) == []
    # --unforce clears the choice, after which the platform is evaluated normally.
    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, unforce="kimi")) == 0
    assert not InstallManifest.load(manifest_path).is_forced("kimi")
    assert [s.key for s in find_stale(_ctx(stale_kimi), [get("kimi")])] == ["kimi"]


def test_redirected_root_is_never_evaluated(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    real = tmp_path / "dotfiles"
    (real / "skills").mkdir(parents=True)
    link = home / ".kimi-code"
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        if os.name != "nt":
            pytest.skip("symlink creation is not permitted on this host")
        import _winapi

        _winapi.CreateJunction(str(real), str(link))
    manifest = InstallManifest()
    manifest.track("kimi", str(link / "skills"))
    manifest.save(runner._manifest_path(home))
    stale = plan_platform(_ctx(home), get("kimi"))
    assert stale is not None
    assert [(e.verdict, e.reason) for e in stale.entries] == [(KEEP, "redirected folder, not evaluated")]
    assert runner.cmd_prune_undetected(_prune_args(home, yes=True)) == 0
    assert (real / "skills").is_dir()


def test_a_tampered_manifest_cannot_reach_outside_the_folder(stale_kimi: Path, tmp_path: Path) -> None:
    outside = tmp_path / "precious.txt"
    outside.write_text("keep me", encoding="utf-8")
    manifest_path = runner._manifest_path(stale_kimi)
    manifest = InstallManifest.load(manifest_path)
    manifest.track("kimi", str(outside))
    manifest.save(manifest_path)
    stale = plan_platform(_ctx(stale_kimi), get("kimi"))
    verdicts = {e.path: (e.verdict, e.reason) for e in stale.entries}
    assert verdicts[str(outside)] == (KEEP, "outside the platform's folder")
    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, yes=True)) == 0
    assert outside.read_text(encoding="utf-8") == "keep me"


def test_hardlinked_file_is_kept(stale_kimi: Path, tmp_path: Path) -> None:
    hook = next((stale_kimi / ".kimi-code" / "hooks").iterdir())
    try:
        os.link(hook, tmp_path / "elsewhere")
    except OSError:
        pytest.skip("hard links are not permitted on this host")
    stale = plan_platform(_ctx(stale_kimi), get("kimi"))
    assert any(e.path == str(hook) and e.verdict == KEEP for e in stale.entries)


def test_a_tool_installed_before_removal_stops_it(stale_kimi: Path, monkeypatch) -> None:
    ctx = _ctx(stale_kimi)
    ctx.dry_run = False
    stale = plan_platform(ctx, get("kimi"))
    monkeypatch.setattr(_detection, "safe_which", lambda name: "/fake-bin/kimi" if name == "kimi" else None)
    result = apply_platform(ctx, get("kimi"), stale)
    assert not any(f.action == "removed" for f in result.files)
    assert any("detected now" in note for note in result.notes)


def test_a_file_changed_after_planning_is_kept(stale_kimi: Path) -> None:
    ctx = _ctx(stale_kimi)
    ctx.dry_run = False
    stale = plan_platform(ctx, get("kimi"))
    target = next(e for e in stale.entries if e.verdict == REMOVE)
    Path(target.path).write_text("edited in between", encoding="utf-8")
    result = apply_platform(ctx, get("kimi"), stale)
    assert Path(target.path).read_text(encoding="utf-8") == "edited in between"
    assert any(f.path == target.path and f.reason == "changed during removal" for f in result.files)


def test_doctor_reports_stale_platforms(stale_kimi: Path, capsys) -> None:
    runner._report_stale(stale_kimi)
    out = capsys.readouterr().out
    assert "stale Nexus-Hub surfaces" in out and "Kimi Code CLI" in out
    assert "nexus-hub prune-undetected" in out


def test_missing_files_are_reported_gone_not_failed(stale_kimi: Path) -> None:
    agents = stale_kimi / ".kimi-code" / "agents"
    for path in agents.glob("*.md"):
        path.unlink()
    stale = plan_platform(_ctx(stale_kimi), get("kimi"))
    assert any(e.verdict == GONE for e in stale.entries)


def test_folder_rule_compares_against_install_time_not_the_copied_folder_mtime(tmp_path: Path) -> None:
    # copytree gives the installed folder its source's mtime, so a source file
    # compiled or edited after checkout is newer than its folder yet unchanged.
    folder = tmp_path / "skills" / "demo"
    folder.mkdir(parents=True)
    copied = folder / "helper.cpython-312.pyc"
    copied.write_bytes(b"compiled")
    stamp = copied.stat().st_mtime
    record = {"mtime": stamp - 1000, "recorded_at": stamp + 1}
    assert [e.verdict for e in _classify_dir(folder, record, [tmp_path])] == [REMOVE]
    # A manifest written before recorded_at existed keeps the conservative rule.
    legacy = {"mtime": stamp - 1000}
    assert [e.verdict for e in _classify_dir(folder, legacy, [tmp_path])] == [KEEP]
    os.utime(copied, (stamp + 3600, stamp + 3600))
    assert [e.verdict for e in _classify_dir(folder, record, [tmp_path])] == [KEEP]

# ---------------------------------------------------------------------------
# Deep-pass findings (v4.14.7 Phase 7, T044): the adversarial pass found two
# ways `prune-undetected --yes` could delete what the user owns.
# ---------------------------------------------------------------------------


def _redirect(link: Path, real: Path) -> None:
    """Make ``link`` a symlink (or, on Windows, a junction) to ``real``."""
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        if os.name != "nt":
            pytest.skip("symlink creation is not permitted on this host")
        import _winapi  # a directory junction needs no privilege

        _winapi.CreateJunction(str(real), str(link))


def test_a_linked_parent_folder_is_never_deleted_through(stale_kimi: Path, tmp_path: Path) -> None:
    # A dotfiles manager moves ~/.kimi-code/skills elsewhere and links it back.
    skills = stale_kimi / ".kimi-code" / "skills"
    elsewhere = tmp_path / "dotfiles" / "kimi-skills"
    elsewhere.parent.mkdir()
    skills.rename(elsewhere)
    _redirect(skills, elsewhere)
    outside = sorted(p for p in elsewhere.rglob("*") if p.is_file())
    assert outside
    stale = plan_platform(_ctx(stale_kimi), get("kimi"))
    through_link = [e for e in stale.entries if "skills" in Path(e.path).parts and e.verdict != GONE]
    assert through_link and all(e.verdict == KEEP for e in through_link)

    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, yes=True)) == 0

    assert all(p.is_file() for p in outside), "files behind the link were deleted"
    assert skills.exists(), "the link itself was removed"


def test_a_copied_in_file_that_kept_an_old_timestamp_is_kept(stale_kimi: Path) -> None:
    import time

    time.sleep(2.5)  # past the two-second timestamp slack the folder rule allows
    mine = _a_skill_file(stale_kimi).parent / "my-own-notes.md"
    mine.write_text("mine", encoding="utf-8")
    os.utime(mine, (1_577_836_800, 1_577_836_800))  # Explorer and `cp -p` keep the source's mtime
    shipped = _a_skill_file(stale_kimi)

    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, yes=True)) == 0

    assert mine.read_text(encoding="utf-8") == "mine"
    assert not shipped.exists(), "an unchanged Nexus-Hub file was not removed"


def test_a_file_the_catalog_does_not_ship_is_kept_even_if_it_predates_the_install(tmp_path: Path, fake_tools, monkeypatch) -> None:
    # A note the user already kept inside a skill folder Nexus-Hub later merged
    # into has an old timestamp of its own, so only the catalog comparison
    # protects it. (A folder the catalog does not ship is never tracked at all.)
    home = tmp_path / "home"
    own = home / ".kimi-code" / "skills" / "adversarial-verifier" / "my-notes.md"
    own.parent.mkdir(parents=True)
    own.write_text("my notes", encoding="utf-8")
    fake_tools("kimi")
    assert runner.cmd_install(_install_args(home)) == 0
    monkeypatch.setattr(_detection, "safe_which", lambda _name: None)
    stale = plan_platform(_ctx(home), get("kimi"))
    mine = [e for e in stale.entries if Path(e.path).name == own.name]  # entries may carry a long-path prefix
    assert [e.verdict for e in mine] == [KEEP] and "catalog ships" in mine[0].reason
    shipped = own.parent / "SKILL.md"

    assert runner.cmd_prune_undetected(_prune_args(home, yes=True)) == 0

    assert own.read_text(encoding="utf-8") == "my notes"
    assert not shipped.exists(), "the file the catalog ships was not removed"


def test_doctor_labels_a_user_forced_platform(stale_kimi: Path, capsys) -> None:
    manifest_path = runner._manifest_path(stale_kimi)
    manifest = InstallManifest.load(manifest_path)
    manifest.set_forced("kimi")
    manifest.save(manifest_path)
    runner._report_stale(stale_kimi)
    out = capsys.readouterr().out
    assert "kimi: user-forced" in out and "--unforce kimi" in out
    assert "stale Nexus-Hub surfaces" not in out


def test_unforce_is_case_insensitive_and_says_when_nothing_was_cleared(stale_kimi: Path, capsys) -> None:
    manifest_path = runner._manifest_path(stale_kimi)
    manifest = InstallManifest.load(manifest_path)
    manifest.set_forced("kimi")
    manifest.save(manifest_path)
    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, unforce="KIMI")) == 0
    out = capsys.readouterr().out
    assert "kimi: the explicit --platforms choice is cleared" in out
    assert not InstallManifest.load(manifest_path).is_forced("kimi")
    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, unforce="qwen")) == 0
    assert "qwen: not named with --platforms, nothing to clear" in capsys.readouterr().out


def test_narrowing_with_integrations_leaves_obsolete_layouts_alone(stale_kimi: Path, monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(runner, "_prune_legacy", lambda home, apply: calls.append(apply) or False)
    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, yes=True, keys="kimi")) == 0
    assert calls == []
    assert runner.cmd_prune_undetected(_prune_args(stale_kimi, yes=True)) == 0
    assert calls == [True]


def test_classifying_many_entries_is_not_quadratic(stale_kimi: Path) -> None:
    import time

    manifest_path = runner._manifest_path(stale_kimi)
    manifest = InstallManifest.load(manifest_path)
    root = stale_kimi / ".kimi-code" / "skills"
    for i in range(6000):
        manifest.track("kimi", str(root / f"gone-{i:05d}"))
    manifest.save(manifest_path)
    started = time.monotonic()
    stale = plan_platform(_ctx(stale_kimi), get("kimi"))
    assert time.monotonic() - started < 20  # about a minute with the old pairwise scan
    assert sum(1 for e in stale.entries if e.verdict == GONE) >= 6000
