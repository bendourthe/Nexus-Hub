"""Tests for scripts/import_skills.py -- the /skills import hygiene gate (v3.6.0 Phase 4, N6).

Covers the three disciplines and their reject/allow/hash branches:

- HTTPS-only source validation (https / http-localhost allowed; non-loopback
  http, file://, ftp://, and empty refused; a local filesystem path allowed).
- the install_allowed discovery-only flag (default installable; explicit false
  blocks; read from a fixture SKILL.md frontmatter).
- hash-on-import (reuses the manifest hasher; digests match hashlib; the full
  vet records hashes only on an import that actually proceeds).

Plus a no-outbound-call regression guard asserting the module pulls in no
network client, and a few subprocess CLI smoke checks of the exit-code contract.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "import_skills.py"

# Make the in-repo `scripts` package importable regardless of pytest rootdir.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import import_skills as imp  # noqa: E402


# --------------------------------------------------------------------------
# HTTPS-only source validation
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "https://example.com/pack.skill",
        "https://raw.githubusercontent.com/org/repo/main/SKILL.md",
        "http://localhost:8080/catalog",
        "http://127.0.0.1/catalog",
        "http://[::1]:9000/catalog",
    ],
)
def test_validate_https_source_allows_https_and_loopback(source: str) -> None:
    ok, _detail = imp.validate_https_source(source)
    assert ok is True


@pytest.mark.parametrize(
    "source",
    [
        "http://example.com/pack.skill",
        "http://evil.example.com",
        "file:///etc/passwd",
        "ftp://mirror.example.com/x",
        "git://example.com/repo",
        "",
    ],
)
def test_validate_https_source_refuses_non_https_urls(source: str) -> None:
    ok, detail = imp.validate_https_source(source)
    assert ok is False
    assert detail  # a human-readable reason is always returned


@pytest.mark.parametrize("source", ["https:///skills/evil", "https://"])
def test_validate_https_source_refuses_host_less_https(source: str) -> None:
    # A host-less https URL (empty netloc) must be refused, not treated as a
    # valid remote source (v3.11.0 adoption-spec-kit Phase 4).
    ok, detail = imp.validate_https_source(source)
    assert ok is False
    assert "host-less" in detail


def test_validate_https_source_allows_https_with_host() -> None:
    ok, _detail = imp.validate_https_source("https://example.com/path")
    assert ok is True


@pytest.mark.parametrize(
    "source",
    [
        "catalog/skills/workflow/loop-engineering",
        "./my-skill",
        "/home/user/skills/my-skill",
        r"C:\Users\me\skills\my-skill",
    ],
)
def test_validate_https_source_allows_local_paths(source: str) -> None:
    # A plain filesystem path (no scheme://) is a local import, always allowed.
    ok, _detail = imp.validate_https_source(source)
    assert ok is True


def test_is_url_distinguishes_urls_from_paths() -> None:
    assert imp.is_url("https://example.com")
    assert imp.is_url("ftp://example.com")
    assert not imp.is_url(r"C:\Users\me\skill")
    assert not imp.is_url("/home/user/skill")
    assert not imp.is_url("./relative/skill")


# --------------------------------------------------------------------------
# install_allowed discovery-only flag
# --------------------------------------------------------------------------


def test_is_install_allowed_defaults_true() -> None:
    assert imp.is_install_allowed({}) is True
    assert imp.is_install_allowed({"name": "x"}) is True


@pytest.mark.parametrize("value", [False, "false", "False", "no", "0", ""])
def test_is_install_allowed_blocks_on_falsey(value: object) -> None:
    assert imp.is_install_allowed({"install_allowed": value}) is False


@pytest.mark.parametrize("value", [True, "true", "yes", "1"])
def test_is_install_allowed_allows_on_truthy(value: object) -> None:
    assert imp.is_install_allowed({"install_allowed": value}) is True


def _write_skill(skill_dir: Path, frontmatter_extra: str = "") -> Path:
    skill_dir.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        "name: fixture-skill\n"
        'description: "A fixture skill for import-hygiene tests."\n'
        f"{frontmatter_extra}"
        "---\n\n"
        "# Fixture Skill\n\nBody.\n"
    )
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(body, encoding="utf-8")
    return skill_md


def test_read_install_allowed_from_skill_default_true(tmp_path: Path) -> None:
    skill_dir = tmp_path / "ok-skill"
    _write_skill(skill_dir)
    assert imp.read_install_allowed_from_skill(skill_dir) is True


def test_read_install_allowed_from_skill_false(tmp_path: Path) -> None:
    skill_dir = tmp_path / "discovery-only"
    _write_skill(skill_dir, frontmatter_extra="install_allowed: false\n")
    assert imp.read_install_allowed_from_skill(skill_dir) is False


def test_read_install_allowed_from_skill_missing_md_is_true(tmp_path: Path) -> None:
    empty = tmp_path / "no-md"
    empty.mkdir()
    assert imp.read_install_allowed_from_skill(empty) is True


# --------------------------------------------------------------------------
# hash-on-import (reuses the manifest hasher)
# --------------------------------------------------------------------------


def test_hash_on_import_matches_hashlib(tmp_path: Path) -> None:
    f = tmp_path / "artifact.txt"
    payload = b"nexus-hub import hygiene\n"
    f.write_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    assert imp.hash_on_import(f) == expected


def test_hash_on_import_reuses_manifest_hasher() -> None:
    # The plan mandates reusing scripts/lib/integrations/manifest._hash_path
    # rather than writing new hashing code: assert it is the same object.
    from scripts.lib.integrations.manifest import _hash_path

    assert imp._hash_path is _hash_path


def test_hash_on_import_returns_none_for_directory(tmp_path: Path) -> None:
    assert imp.hash_on_import(tmp_path) is None


def test_hash_tree_hashes_every_file(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    _write_skill(skill_dir)
    (skill_dir / "references").mkdir()
    (skill_dir / "references" / "notes.md").write_text("notes\n", encoding="utf-8")
    hashes = imp.hash_tree(skill_dir)
    assert set(hashes) == {"SKILL.md", "references/notes.md"}
    assert all(len(h) == 64 for h in hashes.values())


# --------------------------------------------------------------------------
# vet_import orchestrator (full gate)
# --------------------------------------------------------------------------


def test_vet_import_allows_and_records_hashes(tmp_path: Path) -> None:
    skill_dir = tmp_path / "good-skill"
    _write_skill(skill_dir)
    record = imp.vet_import("https://example.com/good.skill", skill_dir=skill_dir)
    assert record["ok"] is True
    assert record["errors"] == []
    assert record["checks"]["install_allowed"] is True
    assert "SKILL.md" in record["hashes"]


def test_vet_import_blocks_discovery_only_and_skips_hashing(tmp_path: Path) -> None:
    skill_dir = tmp_path / "discovery-only"
    _write_skill(skill_dir, frontmatter_extra="install_allowed: false\n")
    record = imp.vet_import("https://example.com/x.skill", skill_dir=skill_dir)
    assert record["ok"] is False
    assert record["checks"]["install_allowed"] is False
    # No hashing on a blocked import (nothing is imported).
    assert record["hashes"] == {}
    assert any("discovery-only" in e for e in record["errors"])


def test_vet_import_rejects_non_https_source(tmp_path: Path) -> None:
    skill_dir = tmp_path / "good-skill"
    _write_skill(skill_dir)
    record = imp.vet_import("http://evil.example.com/x.skill", skill_dir=skill_dir)
    assert record["ok"] is False
    assert record["checks"]["https"]["ok"] is False
    assert record["hashes"] == {}


# --------------------------------------------------------------------------
# no-outbound-call regression guard
# --------------------------------------------------------------------------


def test_module_makes_no_network_imports() -> None:
    # The hygiene gate must add no outbound call: it parses URLs (urllib.parse)
    # but must never import a network client.
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in (
        "urllib.request",
        "import requests",
        "import httpx",
        "import socket",
        "urlopen",
        "http.client",
    ):
        assert forbidden not in source, f"unexpected network surface: {forbidden}"


# --------------------------------------------------------------------------
# CLI exit-code contract (subprocess)
# --------------------------------------------------------------------------


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT),
    )


def test_cli_validate_source_https_exit_0() -> None:
    assert _run("validate-source", "https://example.com/x.skill").returncode == 0


def test_cli_validate_source_http_remote_exit_1() -> None:
    assert _run("validate-source", "http://evil.example.com/x").returncode == 1


def test_cli_vet_allowed_skill_exit_0(tmp_path: Path) -> None:
    skill_dir = tmp_path / "good-skill"
    _write_skill(skill_dir)
    cp = _run("vet", str(skill_dir), "--source", "https://example.com/x.skill", "--json")
    assert cp.returncode == 0
    assert '"ok": true' in cp.stdout


def test_cli_vet_discovery_only_exit_1(tmp_path: Path) -> None:
    skill_dir = tmp_path / "discovery-only"
    _write_skill(skill_dir, frontmatter_extra="install_allowed: false\n")
    cp = _run("vet", str(skill_dir))
    assert cp.returncode == 1
