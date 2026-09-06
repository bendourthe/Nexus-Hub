"""Unit coverage for audit-docs.py version/topic/layout resolution.

The helper ships with a hyphen in its filename, so it is loaded by path via
importlib rather than imported.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "code-cleanup"
    / "docs-layout-refactor"
    / "scripts"
    / "audit-docs.py"
)
_LINK_BASELINE = _MODULE_PATH.with_name("link-baseline.py")


def _load_audit_docs():
    spec = importlib.util.spec_from_file_location("audit_docs", _MODULE_PATH)
    assert spec and spec.loader, f"cannot load {_MODULE_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = _load_audit_docs()

DOCS_ROOT = Path("/repo/docs")


@pytest.mark.parametrize(
    "rel_path, expected_version, expected_topic, expected_layout",
    [
        ("releases/v3/v3.17/plans/foo.md", "v3.17", "plans", "releases"),
        ("v3/v3.17/plans/foo.md", "v3.17", "plans", "v-bucket"),
        ("v3.17.2/plans/foo.md", "v3.17.2", "plans", "flat"),
        ("versions/v3/v3.17.2/plans/foo.md", "v3.17.2", "plans", "versions"),
        ("archives/v3/v3.17/known-gaps.md", "v3.17", None, "releases"),
        ("archive/v3/v3.17/known-gaps.md", "v3.17", None, "v-bucket"),
        ("DEVLOG.md", None, None, None),
        ("policy/matrix.md", None, None, None),
    ],
)
def test_resolve_version_topic(rel_path, expected_version, expected_topic, expected_layout):
    abs_path = DOCS_ROOT / rel_path
    version, topic, layout = audit._resolve_version_topic(abs_path, DOCS_ROOT)
    assert version == expected_version
    assert topic == expected_topic
    assert layout == expected_layout


def test_wrappers_delegate_to_resolver():
    abs_path = DOCS_ROOT / "releases/v3/v3.17/plans/foo.md"
    assert audit._version_dir(abs_path, DOCS_ROOT) == "v3.17"
    assert audit._topic_dir(abs_path, DOCS_ROOT) == "plans"
    # The legacy three-argument call signature still works.
    assert audit._topic_dir(abs_path, DOCS_ROOT, "v3.17") == "plans"


def test_canonicalize_v_bucket_preserves_relative_links(tmp_path):
    docs = tmp_path / "docs"
    source = docs / "v3/v3.17"
    (source / "plans").mkdir(parents=True)
    (source / "reference").mkdir()
    (source / "plans/plan.md").write_text("[reference](../reference/api.md)\n", encoding="utf-8")
    (source / "reference/api.md").write_text("# API\n", encoding="utf-8")

    result = audit.main(["canonicalize-layout", "--root", str(docs)])

    assert result == 0
    destination = docs / "releases/v3/v3.17"
    assert not source.exists()
    assert (destination / "plans/plan.md").read_text(encoding="utf-8") == "[reference](../reference/api.md)\n"
    assert (destination / "reference/api.md").is_file()


def test_canonicalize_layout_introduces_no_new_broken_links(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs"
    source = docs / "v3/v3.17"
    (source / "plans").mkdir(parents=True)
    (source / "reference").mkdir()
    (source / "plans/plan.md").write_text("[reference](../reference/api.md)\n", encoding="utf-8")
    (source / "reference/api.md").write_text("# API\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "docs"], check=True)
    before = tmp_path / "before.ndjson"
    after = tmp_path / "after.ndjson"
    baseline = [sys.executable, str(_LINK_BASELINE), "baseline", "--root", str(repo)]
    subprocess.run([*baseline, "--out", str(before)], check=True, text=True, capture_output=True)

    assert audit.main(["canonicalize-layout", "--root", str(docs)]) == 0
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run([*baseline, "--out", str(after)], check=True, text=True, capture_output=True)
    result = subprocess.run(
        [sys.executable, str(_LINK_BASELINE), "diff", "--before", str(before), "--after", str(after)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["totals"]["newly_broken"] == 0


def test_canonicalize_migrates_the_legacy_archive_container(tmp_path, capsys):
    """The frozen tree renames singular docs/archive/ to plural docs/archives/.

    The inner v<MAJOR>/v<MAJOR>.<MINOR>/ shape is identical on both sides, so
    this is a container rename and every descendant must survive it.
    """
    docs = tmp_path / "docs"
    legacy = docs / "archive"
    (legacy / "v2/v2.1/plans").mkdir(parents=True)
    (legacy / "v2/v2.1/plans/plan.md").write_text("# Plan\n", encoding="utf-8")
    (legacy / "README.md").write_text("# Archive\n", encoding="utf-8")

    assert audit.main(["canonicalize-layout", "--root", str(docs)]) == 0

    assert not legacy.exists()
    assert (docs / "archives/v2/v2.1/plans/plan.md").read_text(encoding="utf-8") == "# Plan\n"
    assert (docs / "archives/README.md").is_file()
    records = json.loads(capsys.readouterr().out)
    assert {"source": "docs/archive", "destination": "docs/archives", "layout": "archive-container"} in records


def test_canonicalize_refuses_when_both_archive_containers_exist(tmp_path, capsys):
    """A pre-existing docs/archives/ is a collision, not a merge target."""
    docs = tmp_path / "docs"
    (docs / "archive/v2/v2.1").mkdir(parents=True)
    (docs / "archive/v2/v2.1/note.md").write_text("# Legacy\n", encoding="utf-8")
    (docs / "archives/v2/v2.1").mkdir(parents=True)
    (docs / "archives/v2/v2.1/note.md").write_text("# Canonical\n", encoding="utf-8")

    assert audit.main(["canonicalize-layout", "--root", str(docs)]) == 2

    # Neither side is touched when the command refuses.
    assert (docs / "archive/v2/v2.1/note.md").read_text(encoding="utf-8") == "# Legacy\n"
    assert (docs / "archives/v2/v2.1/note.md").read_text(encoding="utf-8") == "# Canonical\n"
    assert "destination exists" in capsys.readouterr().err


def test_canonicalize_leaves_an_already_canonical_archive_tree_alone(tmp_path, capsys):
    """Re-running against a migrated tree is a no-op, so the command is idempotent."""
    docs = tmp_path / "docs"
    (docs / "archives/v2/v2.1").mkdir(parents=True)
    (docs / "archives/v2/v2.1/note.md").write_text("# Canonical\n", encoding="utf-8")

    assert audit.main(["canonicalize-layout", "--root", str(docs)]) == 0

    assert (docs / "archives/v2/v2.1/note.md").read_text(encoding="utf-8") == "# Canonical\n"
    assert json.loads(capsys.readouterr().out) == []
