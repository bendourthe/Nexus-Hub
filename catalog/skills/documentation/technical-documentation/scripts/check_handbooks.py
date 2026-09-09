#!/usr/bin/env python3
"""Read-only handbook inventory and evidence freshness gate; never runs a generator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any


def local(root: Path, name: str) -> Path:
    """Reject ambiguous paths and links before reading project-owned inputs."""
    if not isinstance(name, str) or not name or "\\" in name or ":" in name:
        raise ValueError(f"invalid relative path: {name!r}")
    parts = name.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"invalid relative path: {name!r}")
    path = root
    for part in PurePosixPath(name).parts:
        path /= part
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise ValueError(f"linked input: {name}")
    if path.is_file() and path.stat().st_nlink > 1:
        raise ValueError(f"hard-linked input: {name}")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"object required: {path.name}")
    return value


def discover(root: Path) -> set[str]:
    """Inventory topic and legacy HTML, excluding explicit cache/archive directories."""
    base = local(root, "docs/handbooks")
    if not base.is_dir():
        raise ValueError(
            "missing docs/handbooks: bootstrap from actual repository evidence"
        )
    found = set()
    for directory, dirs, files in os.walk(base, followlinks=False):
        dirs[:] = [
            d
            for d in dirs
            if d not in {"archives", "archive", ".cache", "node_modules", "__pycache__"}
        ]
        for name in dirs + files:
            local(root, (Path(directory) / name).relative_to(root).as_posix())
        for name in files:
            if Path(name).suffix.lower() in {".html", ".htm"}:
                found.add((Path(directory) / name).relative_to(root).as_posix())
    return found


def snapshot(root: Path, entry: dict[str, Any]) -> dict[str, Any]:
    """Compute inputs for a review receipt; this does not grant a passing verdict."""
    inputs = entry.get("inputs")
    claims = entry.get("code_inputs")
    builder = entry.get("builder")
    if not isinstance(inputs, list) or not inputs or len(set(inputs)) != len(inputs):
        raise ValueError("nonempty unique inputs required")
    if not isinstance(claims, list) or not claims or not set(claims) <= set(inputs):
        raise ValueError("code_inputs must name reviewed inputs")
    if (
        not isinstance(builder, dict)
        or not builder.get("identity")
        or not builder.get("inputs")
    ):
        raise ValueError("builder identity and inputs required")
    if not set(builder["inputs"]) <= set(inputs):
        raise ValueError("builder inputs must be tracked")
    if type(entry.get("presentation")) is not bool:
        raise ValueError("explicit presentation boolean required")
    if entry["presentation"] is False and not entry.get("opt_out_reason"):
        raise ValueError("presentation opt-out needs its approved reason")
    output = entry["output"]
    if not output.startswith("docs/handbooks/") or Path(output).suffix.lower() not in {
        ".html",
        ".htm",
    }:
        raise ValueError("output must be handbook HTML")
    if output in inputs or entry["evidence"] in inputs:
        raise ValueError("output/evidence cannot be their own source")
    return {
        "entry_sha256": hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest(),
        "inputs": {name: digest(local(root, name)) for name in inputs},
        "output_sha256": digest(local(root, output)),
    }


class Contract(HTMLParser):
    """Inspect actual elements, never selector strings in source prose."""

    def __init__(self):
        super().__init__()
        self.counts = dict.fromkeys(
            ("data-dv-page", "data-dv-deck", "data-dv-slide", "data-dv-open"), 0
        )

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            return
        for name, _value in attrs:
            if name in self.counts:
                self.counts[name] += 1


def contract(path: Path, enabled: bool) -> None:
    parser = Contract()
    parser.feed(path.read_text(encoding="utf-8"))
    counts = parser.counts
    if counts["data-dv-page"] != 1:
        raise ValueError("one complete reading root required")
    if enabled:
        if (
            counts["data-dv-deck"] != 1
            or counts["data-dv-slide"] < 1
            or counts["data-dv-open"] < 2
        ):
            raise ValueError("declared presentation lacks deck, slides or both entries")
    elif any(counts[key] for key in ("data-dv-deck", "data-dv-slide", "data-dv-open")):
        raise ValueError("presentation opt-out still contains deck or entry elements")


def candidate(root: Path) -> dict[str, Any]:
    def git(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else "unavailable"

    revision = git("rev-parse", "HEAD")
    status = git("status", "--porcelain", "--untracked-files=all")
    return {"revision": revision, "working_tree": "uncommitted" if status else "clean"}


def check(
    root: Path,
    manifest: str = "docs/handbooks/handbooks.json",
    scope: set[str] | None = None,
    inventory: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    result: dict[str, Any] = {
        "candidate": candidate(root),
        "scope": sorted(scope) if scope else "full",
        "documents": [],
        "errors": [],
    }
    try:
        found = discover(root)
        config = read_json(local(root, manifest))
        if config.get("schema_version") != 1 or not isinstance(
            config.get("handbooks"), list
        ):
            raise ValueError("schema_version 1 and handbooks list required")
        entries = config["handbooks"]
        excluded = config.get("excluded", {})
        if not isinstance(excluded, dict) or any(
            not isinstance(v, str) or not v.strip() for v in excluded.values()
        ):
            raise ValueError("exclusions need explicit reasons")
        outputs = [entry["output"] for entry in entries]
        ids = [entry["id"] for entry in entries]
        if len(set(outputs)) != len(outputs) or len(set(ids)) != len(ids):
            raise ValueError("duplicate handbook id or output")
        if set(outputs) & set(excluded):
            raise ValueError("mapped output cannot also be excluded")
        if not entries:
            raise ValueError(
                "empty handbook map: bootstrap or document an explicit project scope decision"
            )
        if scope and not scope <= set(ids):
            raise ValueError("scope contains unknown handbook id")
        if not scope and found - set(outputs) - set(excluded):
            raise ValueError(
                "unmapped HTML: "
                + ", ".join(sorted(found - set(outputs) - set(excluded)))
            )
        for entry in entries:
            if scope and entry["id"] not in scope:
                continue
            row = {"id": entry["id"], "output": entry["output"], "status": "incomplete"}
            result["documents"].append(row)
            try:
                expected = snapshot(root, entry)
                row["snapshot"] = expected
                if inventory:
                    row["status"] = "inventoried-not-verified"
                    continue
                contract(local(root, entry["output"]), entry["presentation"])
                evidence = read_json(local(root, entry["evidence"]))
                if evidence.get("snapshot") != expected:
                    raise ValueError(
                        "stale source, builder, mapping or output evidence"
                    )
                for kind in ("content", "build", "rendered"):
                    review = evidence.get("checks", {}).get(kind, {})
                    if review.get("status") != "pass" or not review.get("evidence"):
                        raise ValueError(f"missing {kind} verification")
                rendered = evidence["checks"]["rendered"]
                if (
                    not rendered.get("browser")
                    or rendered.get("output_sha256") != expected["output_sha256"]
                ):
                    raise ValueError(
                        "rendered evidence must name browser and final output hash"
                    )
                for kind in ("content", "build", "rendered"):
                    artifact = local(root, evidence["checks"][kind]["evidence"])
                    if digest(artifact) != evidence["checks"][kind].get(
                        "evidence_sha256"
                    ):
                        raise ValueError(f"changed {kind} review evidence")
                if snapshot(root, entry) != expected:
                    raise ValueError("inputs changed during check")
                row["status"] = (
                    "verified" if entry["presentation"] else "verified-opt-out"
                )
            except (ValueError, OSError, KeyError, TypeError) as exc:
                row["error"] = str(exc)
                result["errors"].append(f"{entry['id']}: {exc}")
        result["excluded"] = excluded
    except (ValueError, OSError, KeyError, TypeError) as exc:
        result["errors"].append(str(exc))
    result["status"] = (
        "incomplete"
        if result["errors"]
        else ("inventory-only" if inventory else "pass")
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--manifest", default="docs/handbooks/handbooks.json")
    parser.add_argument(
        "--scope",
        action="append",
        help="explicit handbook id; cannot qualify a full release",
    )
    parser.add_argument(
        "--inventory",
        action="store_true",
        help="emit snapshots without claiming verification",
    )
    args = parser.parse_args()
    result = check(
        args.root,
        args.manifest,
        set(args.scope) if args.scope else None,
        args.inventory,
    )
    print(json.dumps(result, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
