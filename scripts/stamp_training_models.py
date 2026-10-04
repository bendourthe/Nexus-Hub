#!/usr/bin/env python3
"""Stamp the bundled model map into the Training page so no model id on it is hand-typed.

Repo-internal maintainer tool (v4.13.10). It is listed in ``DEV_ONLY_SCRIPTS`` in
``catalog/hooks/tests/test_installer_smoke.py`` and is deliberately NOT copied by
either installer: it edits ``guides/website/training.html`` in this repository.

The Training page shows, for every agent step, the model tier, the effort, and the
model that tier maps to today for the reader's chosen provider. The ids come only
from ``catalog/skills/ai-development/model-routing/references/last-known-model-map.json``,
copied into the page between two markers::

    <!-- models:nh-training-models -->
    <script type="application/json" id="nh-training-models">{...}</script>
    <!-- /models:nh-training-models -->

The check also reads ``guides/website/src/training-story.json`` and fails when a badge
names a tier the map lacks, or the story lists a provider that is not one of the
map's exact, case-sensitive provider columns.

Usage::

    python scripts/stamp_training_models.py            # rewrite the block from the map
    python scripts/stamp_training_models.py --check    # exit 1 when the page differs from the map
    python scripts/stamp_training_models.py --map PATH [--root PATH]

Exit codes: 0 clean (or written), 1 drift under ``--check``, 2 the map, the story, or
the page is missing or malformed. On exit 2 nothing is written.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAP = Path("catalog/skills/ai-development/model-routing/references/last-known-model-map.json")
PAGE = Path("guides/website/training.html")
STORY = Path("guides/website/src/training-story.json")
OPEN = "<!-- models:nh-training-models -->"
CLOSE = "<!-- /models:nh-training-models -->"
BLOCK = re.compile(re.escape(OPEN) + r"\n(.*?)" + re.escape(CLOSE), re.DOTALL)


class StampError(RuntimeError):
    """The map, the story, or the page is unusable."""


def _json(path: Path, what: str) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StampError(f"{what} {path.as_posix()} is missing or not valid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise StampError(f"{what} {path.as_posix()} is not a JSON object")
    return data


def build_block(model_map: dict) -> str:
    tiers = model_map.get("tiers")
    if not isinstance(tiers, dict) or not tiers:
        raise StampError("the model map has no 'tiers' object")
    providers: list[str] = []
    for tier, row in tiers.items():
        if not isinstance(row, dict) or not row:
            raise StampError(f"the model map's tier {tier} has no provider columns")
        for provider, model in row.items():
            if not isinstance(model, str) or not model:
                raise StampError(f"the model map's {tier}/{provider} cell is empty")
            if provider not in providers:
                providers.append(provider)
    payload = {
        "source": MAP.as_posix(),
        "verified_as_of": model_map.get("verified_as_of", "unknown"),
        "providers": providers,
        "tiers": tiers,
    }
    text = json.dumps(payload, indent=1, ensure_ascii=True)
    if "</" in text:
        raise StampError("the model map contains '</', which cannot sit inside a script block")
    return f'<script type="application/json" id="nh-training-models">\n{text}\n</script>\n'


def check_story(story: dict, model_map: dict) -> None:
    tiers = model_map["tiers"]
    columns = {provider for row in tiers.values() for provider in row}
    for provider in story.get("providers", []):
        if provider not in columns:
            raise StampError(f"story provider {provider!r} is not a model map column (exact, case-sensitive): {sorted(columns)}")
    for stage in story.get("stages", []):
        badge = stage.get("badge")
        if badge and badge.get("tier") not in tiers:
            raise StampError(f"stage {stage.get('id')}: badge tier {badge.get('tier')!r} is not in the model map")


def stamp(root: Path, map_path: Path, check: bool) -> int:
    model_map = _json(map_path, "model map")
    block = build_block(model_map)
    check_story(_json(root / STORY, "story"), model_map)
    page = root / PAGE
    try:
        raw = page.read_bytes().decode("utf-8")
    except OSError as exc:
        raise StampError(f"page {PAGE.as_posix()} is missing ({exc})") from exc
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    found = list(BLOCK.finditer(text))
    if len(found) != 1:
        raise StampError(f"{PAGE.as_posix()}: expected exactly one {OPEN} ... {CLOSE} block, found {len(found)}")
    current = found[0].group(1)
    if check:
        if current != block:
            print("stamp_training_models: drift -- the page's model block differs from the model map", file=sys.stderr)
            return 1
        print(f"stamp_training_models: OK -- the page matches the model map (verified {model_map.get('verified_as_of', 'unknown')})")
        return 0
    text = text[: found[0].start(1)] + block + text[found[0].end(1):]
    page.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
    print("stamp_training_models: stamped the model block" + (" (changed)" if current != block else " (unchanged)"))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="exit 1 when the page differs from the map")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--map", type=Path, default=None, help="model map to use (default: the bundled map)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        return stamp(root, args.map or root / MAP, args.check)
    except StampError as exc:
        print(f"stamp_training_models: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
