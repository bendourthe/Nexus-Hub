"""Catalog loader tests (v4.14.6 Phase 2, T012): refuse to start rather than guess."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from scripts.lib.settings_control import catalog as catalog_mod

BUNDLED = json.loads(catalog_mod.CATALOG_PATH.read_text(encoding="utf-8"))


def _write(tmp_path: Path, data: Any) -> Path:
    path = tmp_path / "catalog.json"
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def test_the_bundled_catalog_loads() -> None:
    loaded = catalog_mod.load_catalog()

    assert {c["id"] for c in loaded["controls"]} == {"effort", "model", "posture", "attribution", "git_guardrails"}


@pytest.mark.parametrize(
    ("content", "needle"),
    [
        ("{not json", "is not valid JSON"),
        ({}, "has the wrong shape"),
        ({**BUNDLED, "writes": [{"id": "x"}]}, "missing fields"),
    ],
)
def test_a_bad_catalog_is_refused_and_never_replaced_by_the_bundled_one(tmp_path: Path, content: Any, needle: str) -> None:
    with pytest.raises(catalog_mod.CatalogError) as raised:
        catalog_mod.load_catalog(_write(tmp_path, content))

    assert needle in str(raised.value) and raised.value.findings


def test_a_missing_catalog_is_refused(tmp_path: Path) -> None:
    with pytest.raises(catalog_mod.CatalogError, match="cannot be read"):
        catalog_mod.load_catalog(tmp_path / "absent.json")


def test_the_loader_reports_every_finding_not_only_the_first(tmp_path: Path) -> None:
    broken = copy.deepcopy(BUNDLED)
    broken["writes"][0]["admission"] = "maybe"
    broken["writes"][1]["weakens_safety"] = True
    broken["writes"][1]["weakening_values"] = []

    with pytest.raises(catalog_mod.CatalogError) as raised:
        catalog_mod.load_catalog(_write(tmp_path, broken))

    assert len(raised.value.findings) >= 2


def test_structural_rules_need_nothing_outside_the_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An installed tree has no proof matrix, configs/, or decision records."""
    monkeypatch.chdir(tmp_path)

    assert catalog_mod.validate_structure(copy.deepcopy(BUNDLED)) == []


def test_every_write_belongs_to_exactly_one_group_in_catalog_order() -> None:
    groups = catalog_mod.write_groups(BUNDLED)
    placed = [w["id"] for g in groups for w in g.writes]

    assert sorted(placed) == sorted(w["id"] for w in BUNDLED["writes"]) and len(placed) == len(set(placed))
    assert all(len({(w["tool"], w["surface"]) for w in g.writes}) == 1 for g in groups)


def test_the_bundled_model_ids_load_and_a_bad_list_is_refused(tmp_path: Path) -> None:
    assert catalog_mod.load_claude_model_ids() == json.loads(catalog_mod.CLAUDE_IDS_PATH.read_text(encoding="utf-8"))["ids"]
    bad = tmp_path / "ids.json"
    bad.write_text('{"ids": [1]}', encoding="utf-8")
    with pytest.raises(catalog_mod.CatalogError):
        catalog_mod.load_claude_model_ids(bad)
