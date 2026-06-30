"""Tests for the v3.10.0 supply-chain verify tooling.

Covers the two new stdlib-only scripts and their `nexus-hub verify` wiring:

- scripts/generate_manifest.py: deterministic, sorted, sha256sum-compatible
  manifest over the covered catalog roots; scope inclusion/exclusion; a
  format <-> parse round-trip.
- scripts/verify_install.py: the OK / MODIFIED / MISSING / EXTRA classification,
  the PASS/FAIL summary and exit codes, the --ignore-extra opt-out, and the
  honest "no catalog root / no manifest" exit-2 paths.
- scripts/nexus_hub_cli.py: `verify` dispatches to verify_install with the right
  exit codes (driven by NEXUS_HUB_HOME against a fixture install tree).

Plus invariants: a no-outbound-call regression guard on both new scripts, and a
both-installers-wire-it-up check (the scripts + MANIFEST.sha256 copy lines and
the release-flow manifest step).

Everything runs on the Python interpreter directly (no bash), so the Windows dev
host runs the full suite.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
GEN_PY = SCRIPTS / "generate_manifest.py"
VERIFY_PY = SCRIPTS / "verify_install.py"
CLI_PY = SCRIPTS / "nexus_hub_cli.py"
INSTALL_SH = SCRIPTS / "installer.sh"
INSTALL_PS1 = SCRIPTS / "installer.ps1"
UPDATE_CMD = REPO_ROOT / "catalog" / "commands" / "update.md"

# Make the in-repo `scripts` package importable regardless of pytest rootdir.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import generate_manifest as gm  # noqa: E402
from scripts import verify_install as vi  # noqa: E402

_RUN_KW = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")


# --------------------------------------------------------------------------
# Fixture helpers
# --------------------------------------------------------------------------


def _build_tree(root: Path) -> None:
    """Lay out a small catalog tree under `root` spanning two covered roots."""
    (root / "catalog" / "skills" / "demo").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)  # outside covered roots
    (root / "catalog" / "skills" / "demo" / "SKILL.md").write_text(
        "alpha\n", encoding="utf-8"
    )
    (root / "catalog" / "skills" / "demo" / "notes.md").write_text(
        "gamma\n", encoding="utf-8"
    )
    (root / "data" / "skills.json").write_text("beta\n", encoding="utf-8")
    # Noise that must be excluded / ignored:
    (root / "catalog" / "skills" / "demo" / "__pycache__").mkdir(exist_ok=True)
    (root / "catalog" / "skills" / "demo" / "__pycache__" / "x.pyc").write_text(
        "bytecode\n", encoding="utf-8"
    )
    (root / "docs" / "outside.md").write_text("ignored\n", encoding="utf-8")


def _build_install(home: Path) -> Path:
    """Build a fixture install tree at <home>/src with a co-located manifest."""
    src = home / "src"
    _build_tree(src)
    gm.write_manifest(src, src / "MANIFEST.sha256")
    return src


# --------------------------------------------------------------------------
# generate_manifest: determinism, scope, format
# --------------------------------------------------------------------------


def test_compute_manifest_is_deterministic_and_sorted(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    first = gm.compute_manifest(tmp_path)
    second = gm.compute_manifest(tmp_path)
    assert first == second
    paths = [p for p, _ in first]
    assert paths == sorted(paths)


def test_manifest_scope_includes_covered_and_excludes_the_rest(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    paths = {p for p, _ in gm.compute_manifest(tmp_path)}
    assert "catalog/skills/demo/SKILL.md" in paths
    assert "data/skills.json" in paths
    # Excluded: bytecode under __pycache__, and anything outside covered roots.
    assert not any(p.endswith(".pyc") for p in paths)
    assert not any("__pycache__" in p for p in paths)
    assert not any(p.startswith("docs/") for p in paths)


def test_format_is_sha256sum_text_format_with_lf(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    text = gm.format_manifest(gm.compute_manifest(tmp_path))
    assert "\r" not in text  # LF-only regardless of OS
    line = text.splitlines()[0]
    digest, sep, path = line[:64], line[64:66], line[66:]
    assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
    assert sep == "  "  # two-space text-mode separator
    assert path  # a relative path follows


def test_write_manifest_is_byte_identical_across_runs(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    out1 = tmp_path / "m1.sha256"
    out2 = tmp_path / "m2.sha256"
    gm.write_manifest(tmp_path, out1)
    gm.write_manifest(tmp_path, out2)
    assert out1.read_bytes() == out2.read_bytes()


def test_parse_round_trips_and_tolerates_binary_marker(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    entries = gm.compute_manifest(tmp_path)
    parsed = gm.parse_manifest(gm.format_manifest(entries))
    assert parsed == dict(entries)
    # Binary-mode marker ("<hash> *path") and blank lines are tolerated.
    sample = entries[0]
    text = f"\n{sample[1]} *{sample[0]}\n\n"
    assert gm.parse_manifest(text) == {sample[0]: sample[1]}


# --------------------------------------------------------------------------
# verify_install: classification
# --------------------------------------------------------------------------


def test_classify_clean_tree_is_all_ok(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    manifest = gm.format_manifest(gm.compute_manifest(tmp_path))
    result = vi.classify(tmp_path, manifest)
    assert result.ok == 3
    assert result.modified == [] and result.missing == [] and result.extra == []
    assert result.failed(ignore_extra=False) is False


def test_classify_detects_modified(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    manifest = gm.format_manifest(gm.compute_manifest(tmp_path))
    (tmp_path / "data" / "skills.json").write_text("tampered\n", encoding="utf-8")
    result = vi.classify(tmp_path, manifest)
    assert result.modified == ["data/skills.json"]
    assert result.failed(ignore_extra=False) is True


def test_classify_detects_missing(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    manifest = gm.format_manifest(gm.compute_manifest(tmp_path))
    (tmp_path / "data" / "skills.json").unlink()
    result = vi.classify(tmp_path, manifest)
    assert result.missing == ["data/skills.json"]
    assert result.failed(ignore_extra=False) is True


def test_classify_detects_extra_and_ignore_extra_opt_out(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    manifest = gm.format_manifest(gm.compute_manifest(tmp_path))
    (tmp_path / "catalog" / "skills" / "demo" / "surprise.md").write_text(
        "new\n", encoding="utf-8"
    )
    result = vi.classify(tmp_path, manifest)
    assert result.extra == ["catalog/skills/demo/surprise.md"]
    assert result.failed(ignore_extra=False) is True
    assert result.failed(ignore_extra=True) is False  # opt-out clears the FAIL


def test_format_report_summary_lines(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    manifest = gm.format_manifest(gm.compute_manifest(tmp_path))
    (tmp_path / "data" / "skills.json").write_text("tampered\n", encoding="utf-8")
    report, passed = vi.format_report(vi.classify(tmp_path, manifest), ignore_extra=False)
    assert passed is False
    assert "verify: FAIL (1 modified, 0 missing, 0 extra)" in report
    assert "MODIFIED  data/skills.json" in report


# --------------------------------------------------------------------------
# verify_install.main: resolution + exit codes
# --------------------------------------------------------------------------


def test_main_pass_with_explicit_root_and_manifest(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    manifest = tmp_path / "MANIFEST.sha256"
    gm.write_manifest(tmp_path, manifest)
    rc = vi.main(["--root", str(tmp_path), "--manifest", str(manifest)])
    assert rc == 0


def test_main_fail_on_modified(tmp_path: Path) -> None:
    _build_tree(tmp_path)
    manifest = tmp_path / "MANIFEST.sha256"
    gm.write_manifest(tmp_path, manifest)
    (tmp_path / "data" / "skills.json").write_text("tampered\n", encoding="utf-8")
    rc = vi.main(["--root", str(tmp_path), "--manifest", str(manifest)])
    assert rc == 1


def test_main_exit_2_when_no_manifest(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    (home / "src").mkdir(parents=True)
    monkeypatch.setenv("NEXUS_HUB_HOME", str(home))
    rc = vi.main([])  # src exists but holds no MANIFEST.sha256
    assert rc == 2


def test_main_exit_2_when_no_src_root(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path / "empty"))
    rc = vi.main([])  # no <home>/src at all
    assert rc == 2


# --------------------------------------------------------------------------
# nexus-hub CLI: `verify` dispatch + exit codes
# --------------------------------------------------------------------------


def _cli(args: list[str], home: Path) -> subprocess.CompletedProcess:
    env = {**_subprocess_env(), "NEXUS_HUB_HOME": str(home)}
    return subprocess.run([sys.executable, str(CLI_PY), *args], env=env, **_RUN_KW)


def _subprocess_env() -> dict:
    import os

    return dict(os.environ)


def test_cli_verify_pass_on_clean_install(tmp_path: Path) -> None:
    _build_install(tmp_path)
    proc = _cli(["verify"], tmp_path)
    assert proc.returncode == 0
    assert "verify: PASS" in proc.stdout


def test_cli_verify_fail_on_modified_install(tmp_path: Path) -> None:
    src = _build_install(tmp_path)
    (src / "data" / "skills.json").write_text("tampered\n", encoding="utf-8")
    proc = _cli(["verify"], tmp_path)
    assert proc.returncode == 1
    assert "MODIFIED  data/skills.json" in proc.stdout
    assert "verify: FAIL" in proc.stdout


def test_cli_verify_forwards_ignore_extra_flag(tmp_path: Path) -> None:
    src = _build_install(tmp_path)
    (src / "catalog" / "skills" / "demo" / "surprise.md").write_text(
        "new\n", encoding="utf-8"
    )
    fail = _cli(["verify"], tmp_path)
    assert fail.returncode == 1
    ok = _cli(["verify", "--ignore-extra"], tmp_path)
    assert ok.returncode == 0
    assert "verify: PASS" in ok.stdout


def test_cli_help_lists_verify() -> None:
    proc = subprocess.run([sys.executable, str(CLI_PY), "--help"], **_RUN_KW)
    assert proc.returncode == 0
    assert "verify" in proc.stdout


# --------------------------------------------------------------------------
# Invariants: no outbound call, both installers + release flow wire it up
# --------------------------------------------------------------------------


@pytest.mark.parametrize("script", [GEN_PY, VERIFY_PY])
def test_no_outbound_network_primitives(script: Path) -> None:
    source = script.read_text(encoding="utf-8")
    for token in ("requests", "urllib", "httpx", "aiohttp", "socket.", "urlopen"):
        assert token not in source, f"{script.name} unexpectedly references {token!r}"
    # The shell-out downloaders curl/wget must not appear either.
    for token in ("curl", "wget"):
        assert token not in source, f"{script.name} unexpectedly references {token!r}"


def test_both_installers_copy_the_new_artifacts() -> None:
    sh = INSTALL_SH.read_text(encoding="utf-8")
    ps1 = INSTALL_PS1.read_text(encoding="utf-8")
    for needle in ("generate_manifest.py", "verify_install.py", "MANIFEST.sha256"):
        assert needle in sh, f"installer.sh missing {needle}"
        assert needle in ps1, f"installer.ps1 missing {needle}"


def test_release_flow_regenerates_manifest() -> None:
    update = UPDATE_CMD.read_text(encoding="utf-8")
    assert "generate_manifest.py" in update
    assert "MANIFEST.sha256" in update
