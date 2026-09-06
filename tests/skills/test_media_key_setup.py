"""Unit coverage for the v3.14.3 bring-your-own-key media setup.

Covers `_resolve_pexels_key` (env-then-file resolution + the video degrade path)
in the stock fetcher, and the `setup_media_keys` helper (no-echo capture, 0600
perms, upsert-preserving-other-lines, masked output, empty rejection). The
load-bearing secret-hygiene assertion: the full key NEVER reaches stdout/stderr.

Both scripts are loaded by path via importlib (they live outside the test tree),
matching the pattern in test_audit_docs_version_topic.py.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_FETCH_PATH = (
    _ROOT
    / "catalog"
    / "skills"
    / "specialized-domains"
    / "document-to-interactive-html"
    / "scripts"
    / "fetch_stock_media.py"
)
_SETUP_PATH = _ROOT / "scripts" / "setup_media_keys.py"

# A plausible key: >= MIN_KEY_LEN and no whitespace, so it passes sanity_check.
SENTINEL_KEY = "PEXELSKEY0123456789abcdef0123456789abcdef0123456789abcd"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fetch = _load(_FETCH_PATH, "fetch_stock_media")
setup = _load(_SETUP_PATH, "setup_media_keys")


# --- _resolve_pexels_key ----------------------------------------------------

def test_resolve_key_env_wins(monkeypatch):
    monkeypatch.setenv("PEXELS_API_KEY", "envkey1234567890")
    assert fetch._resolve_pexels_key() == "envkey1234567890"


def test_resolve_key_from_file_when_env_unset(monkeypatch, tmp_path):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    cfg = tmp_path / ".nexus-hub" / "config"
    cfg.mkdir(parents=True)
    (cfg / "media.env").write_text(
        "# media keys\nOTHER=x\nPEXELS_API_KEY=filekey987654321\n", encoding="utf-8"
    )
    assert fetch._resolve_pexels_key() == "filekey987654321"


def test_resolve_key_none_and_video_degrades_without_network(monkeypatch, tmp_path):
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))  # empty home, no media.env
    assert fetch._resolve_pexels_key() is None

    # The video / Pexels path must degrade (no key => LookupError => degrade),
    # writing an empty manifest and returning EXIT_DEGRADE, with no network call
    # (query_pexels is never reached because the key check fails first).
    out = tmp_path / "manifest.json"
    rc = fetch.main(
        ["--query", "cooling towers", "--kind", "video", "--source", "pexels", "--consent", "-o", str(out)]
    )
    assert rc == fetch.EXIT_DEGRADE
    manifest = json.loads(out.read_text(encoding="utf-8"))
    assert manifest["degraded"] is True
    assert manifest["assets"] == []


# --- setup_media_keys helpers ----------------------------------------------

def test_upsert_preserves_other_lines_and_replaces_key():
    existing = "# header\nOTHER=keep\nPEXELS_API_KEY=old\nTRAILING=z\n"
    result = setup.upsert_env_line(existing, "PEXELS_API_KEY", "new")
    assert "OTHER=keep" in result
    assert "TRAILING=z" in result
    assert "PEXELS_API_KEY=new" in result
    assert "PEXELS_API_KEY=old" not in result
    # exactly one PEXELS_API_KEY line
    assert sum(1 for ln in result.splitlines() if ln.startswith("PEXELS_API_KEY=")) == 1


def test_upsert_appends_when_absent():
    result = setup.upsert_env_line("OTHER=keep\n", "PEXELS_API_KEY", "new")
    assert "OTHER=keep" in result
    assert "PEXELS_API_KEY=new" in result


def test_mask_key_shows_only_last_four():
    assert setup.mask_key(SENTINEL_KEY) == "..." + SENTINEL_KEY[-4:]
    assert SENTINEL_KEY not in setup.mask_key(SENTINEL_KEY)


def test_sanity_check_rejects_empty_and_whitespace_and_short():
    assert setup.sanity_check("") is not None
    assert setup.sanity_check("has space") is not None
    assert setup.sanity_check("short") is not None
    assert setup.sanity_check(SENTINEL_KEY) is None


def test_setup_writes_upserts_and_never_prints_full_key(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("NEXUS_HUB_HOME", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    cfg = tmp_path / ".nexus-hub" / "config"
    cfg.mkdir(parents=True)
    (cfg / "media.env").write_text("OTHER_KEY=keep-me\n", encoding="utf-8")  # pre-existing line

    monkeypatch.setattr(setup.getpass, "getpass", lambda *a, **k: SENTINEL_KEY)
    rc = setup.main([])
    assert rc == 0

    text = (cfg / "media.env").read_text(encoding="utf-8")
    assert "OTHER_KEY=keep-me" in text  # other line preserved
    assert f"PEXELS_API_KEY={SENTINEL_KEY}" in text  # key stored in the file

    if os.name == "posix":  # Windows has no exact 0600 equivalent
        assert (cfg / "media.env").stat().st_mode & 0o777 == 0o600

    captured = capsys.readouterr()
    # Secret hygiene: the FULL key must never reach stdout or stderr.
    assert SENTINEL_KEY not in captured.out
    assert SENTINEL_KEY not in captured.err
    # Only the masked form is surfaced.
    assert "..." + SENTINEL_KEY[-4:] in captured.out


def test_setup_refuses_empty_key(monkeypatch, tmp_path, capsys):
    monkeypatch.delenv("NEXUS_HUB_HOME", raising=False)
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setattr(setup.getpass, "getpass", lambda *a, **k: "   ")  # empty after strip
    rc = setup.main([])
    assert rc == 1
    # Nothing stored.
    assert not (tmp_path / ".nexus-hub" / "config" / "media.env").exists()
    captured = capsys.readouterr()
    assert "Not stored" in captured.err
