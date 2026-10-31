"""Legacy identities and corrective authority remain explicit and fail closed."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import completion_minor as cm
import minor_close as mc


def ledger(heading, body="- **Source phase**: Phase 1\n- **Reason**: Still unproved.\n\n"):
    return "# Gaps\n\n## 1. Open Items\n\n### " + heading + "\n\n" + body


@pytest.mark.parametrize("raw, kinds, priority", [
    ("1.P1.A", "DF", "1"), ("1.1-2.P1.NN", "DF, MT", "1"),
    ("1.x.P3.B", "NI", "3"), ("T002.P2.A", "WN", "2"),
    ("11.P1.MMM", "DF", "1"), ("2.1.P2.A", "MT", "2"),
    ("3.P2.R", "DF, MT", "2"), ("5.P3.FF", "DF, BG", "3"),
])
def test_legacy_alias_preserves_raw_identity_and_body(raw, kinds, priority):
    body = "- **Source phase**: Phase 1\r\n- **Reason**: Original unresolved work.\r\n\r\n"
    text = ledger(f"{raw} -- Original title ({kinds}, P{priority})", body)
    items, problems = cm.parse_ledger_full(text)
    assert problems == []
    assert len(items) == 1
    item = items[0]
    assert item.gid == kinds.split(",")[0] + "-" + raw.replace(".", "-")
    assert raw in item.title
    assert item.body == "\n" + body
    assert item.state == "open"


@pytest.mark.parametrize("heading", [
    "1.P1.A -- Work (ZZ, P1)", "1..P1.A -- Work (DF, P1)",
    "1.P1.A -- Work (DF)", "1.P1.A -- Work (DF, P9)",
])
def test_malformed_legacy_records_remain_unreadable(heading):
    assert cm.parse_ledger_full(ledger(heading))[1]


@pytest.mark.parametrize("heading", [
    "6.3.NI.Hub -- Template shipped (NI -- already resolved)",
    "1.5.R1 -- IPC handlers (resolved in Phase 1)",
    "1.5.R2 -- Strict-null errors (resolved in Phase 1)",
    "1.x.P3.D -- Adoption ledger (resolved in Phase 7)",
])
def test_explicit_resolved_legacy_notes_do_not_hide_open_items(heading):
    items, problems = cm.parse_ledger_full(ledger(heading))
    assert problems == []
    assert items == []


def test_closed_feature_word_is_not_a_resolution():
    items, problems = cm.parse_ledger_full(ledger("1.4.P1.B -- Closed-loop runtime missing (DF, P1)"))
    assert problems == []
    assert len(items) == 1 and items[0].state == "open"


@pytest.mark.parametrize("container", ["## 2. Resolved", "## 6. Documented-but-not-implemented items closed in v0.6.0 (audit trail)"])
def test_prose_rows_are_exempt_only_in_explicit_closed_containers(container):
    row = "- **FIFO-vs-LRU mismatch** -- reconciled.\n"
    assert cm.parse_ledger_full("# Gaps\n\n" + container + "\n\n" + row)[1] == []
    assert cm.parse_ledger_full("# Gaps\n\n## Open Items\n\n" + row)[1]


def test_native_and_legacy_alias_collision_is_not_hidden_by_sections():
    text = ledger("1.P1.A -- Work (DF, P1)")
    text += "## v9.0.0\n\n#### DF-1-P1-A - Other obligation\n\n- **Reason**: Still open.\n"
    assert cm.parse_ledger_full(text)[1]


def test_legacy_priority_stays_sensitive_in_a_canonical_destination():
    text = "# Gaps\n\n## v9.0.0\n\n#### DF-1 - 1.P1.A -- Work (DF, P1)\n\n- **Reason**: Open.\n"
    item = cm.parse_ledger(text)[0]
    assert item.sensitive()


def test_next_numeric_destination_id_ignores_existing_named_ids():
    text = "# Gaps\n\n## v9.0.0\n\n#### WN-D - Named record\n\n#### WN-7 - Numbered record\n"
    assert mc._next_gid(text, "WN") == "WN-8"


def test_legacy_copy_uses_visible_canonical_item_level_without_body_changes():
    item = cm.parse_ledger(ledger("1.P1.A -- Work (DF, P1)"))[0]
    target = "# Gaps\n\n## v9.0.0\n\n### Open Items\n\n### Resolved\n\n"
    after = mc._insert_entry(target, "v9.0.0", item, "DF-1", item.body, ["- **Migrated from**: v1.0#DF-1-P1-A"])
    assert "\n#### DF-1 " in after
    copy = cm.parse_ledger(after)[0]
    assert copy.body.startswith(item.body)


def test_legacy_heading_under_explicit_closed_section_stays_resolved():
    text = "# Gaps\n\n## 2. Resolved\n\n### T007.P2.B -- Dependency orphan (WN, P2)\n\n- **Resolved in**: Phase 3\n"
    items, problems = cm.parse_ledger_full(text)
    assert problems == [] and len(items) == 1
    assert items[0].state == 'resolved'


ARCHIVE_SRC = "docs/releases/v0/v0.5"
ARCHIVE_DST = "docs/archives/v0/v0.5"
ARCHIVE_SUFFIX = "archives/v0/v0.4/development/feasibility.md"


def _archive_navigation(root, href, moved=False, destination=ARCHIVE_DST):
    old = ARCHIVE_SRC + "/plans/study.md"
    new = destination + "/plans/study.md"
    read = new if moved else old
    text = "# Study\n\n[Record](" + href + ")\n"
    path = root / read
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    repairs = mc.plan_repairs(root, [(read, old, new)], ARCHIVE_SRC, destination)
    return repairs[0].repaired if repairs else text


def _canonical_feasibility(root, name="feasibility.md"):
    path = root / "docs/archives/v0/v0.4/development" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# Feasibility\n\n## Proof\n", encoding="utf-8")
    return path


@pytest.mark.parametrize("moved", [False, True])
def test_misplaced_archive_navigation_uses_existing_canonical_file(tmp_path, moved):
    _canonical_feasibility(tmp_path)
    repaired = _archive_navigation(tmp_path, "../" + ARCHIVE_SUFFIX, moved)
    assert "(../../v0.4/development/feasibility.md)" in repaired


@pytest.mark.parametrize("moved", [False, True])
def test_valid_nested_archive_navigation_is_not_redirected(tmp_path, moved):
    _canonical_feasibility(tmp_path)
    nested = tmp_path / (ARCHIVE_DST if moved else ARCHIVE_SRC) / ARCHIVE_SUFFIX
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("# Different existing nested record\n", encoding="utf-8")
    repaired = _archive_navigation(tmp_path, "../" + ARCHIVE_SUFFIX, moved)
    assert "(../" + ARCHIVE_SUFFIX + ")" in repaired


@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_archive_navigation_needs_a_regular_canonical_file(tmp_path, kind):
    if kind == "directory":
        (tmp_path / "docs" / ARCHIVE_SUFFIX).mkdir(parents=True)
    repaired = _archive_navigation(tmp_path, "../" + ARCHIVE_SUFFIX)
    assert "(../" + ARCHIVE_SUFFIX + ")" in repaired


@pytest.mark.parametrize("location", ["old", "moved", "canonical"])
@pytest.mark.parametrize("uncertainty", ["reparse", "error"])
def test_uncertain_archive_navigation_keeps_normal_mapping(
    tmp_path, monkeypatch, location, uncertainty
):
    _canonical_feasibility(tmp_path)
    rel = {
        "old": ARCHIVE_SRC + "/" + ARCHIVE_SUFFIX,
        "moved": ARCHIVE_DST + "/" + ARCHIVE_SUFFIX,
        "canonical": "docs/" + ARCHIVE_SUFFIX,
    }[location]
    blocked = tmp_path / rel
    original = mc.ck._private_reparse

    def inspect(path):
        if path == blocked:
            if uncertainty == "error":
                raise PermissionError("inspection unavailable")
            return True
        return original(path)

    monkeypatch.setattr(mc.ck, "_private_reparse", inspect)
    repaired = _archive_navigation(tmp_path, "../" + ARCHIVE_SUFFIX)
    assert "(../" + ARCHIVE_SUFFIX + ")" in repaired


@pytest.mark.parametrize(
    "destination", ["docs/releases/v0/v0.6", "docs/archives/v0/v0.6"]
)
def test_other_tree_moves_do_not_use_archive_navigation_fallback(tmp_path, destination):
    _canonical_feasibility(tmp_path)
    repaired = _archive_navigation(
        tmp_path, "../" + ARCHIVE_SUFFIX, destination=destination
    )
    assert "(../" + ARCHIVE_SUFFIX + ")" in repaired


@pytest.mark.parametrize("href", [
    "https://example.invalid/archives/v0/v0.4/development/feasibility.md",
    r"../archives/v0/v0.4/..\outside.md",
    "../archives/v0/v0.4/C:/outside.md",
    "../archives/v0/v0.4/trailing./outside.md",
])
def test_unsafe_archive_navigation_never_probes_candidates(tmp_path, monkeypatch, href):
    _canonical_feasibility(tmp_path)

    def unexpected(_path):
        raise AssertionError("unsafe path reached filesystem inspection")

    monkeypatch.setattr(mc.ck, "_private_reparse", unexpected)
    _archive_navigation(tmp_path, href)


def test_canonical_archive_navigation_retains_encoding_query_and_fragment(tmp_path):
    _canonical_feasibility(tmp_path, "feasibility record.md")
    repaired = _archive_navigation(
        tmp_path, "../archives/v0/v0.4/development/feasibility%20record.md?view=1#proof"
    )
    assert "(../../v0.4/development/feasibility%20record.md?view=1#proof)" in repaired
