"""Verified per-platform, per-scope skill read paths, and the Skill-Index Pointer.

The facts live in the `skill_read_paths` section of
`docs/policy/platform-read-contracts.json`: for each platform and scope, the
directories the vendor's own documentation says are scanned for skills, each
with a `status`, a first-party `source`, and a `verified` date. Only a VERIFIED
path counts, and only when a skills tree was actually installed there, which is
what Native Skill Enumeration means for this repository. Anything missing,
unreadable, or of unknown status fails closed to the full skill index.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONTRACT_REL = Path("docs") / "policy" / "platform-read-contracts.json"
SCOPES = ("global", "workspace")
STATUSES = ("VERIFIED", "UNVERIFIED")
POINTER_MODE = "pointer"


def index_mode(raw: str | None) -> str:
    """`NEXUS_HUB_SKILL_INDEX` value to a mode; anything but `pointer` is `full`."""
    return POINTER_MODE if (raw or "").strip().lower() == POINTER_MODE else "full"


def load_facts(repo_root: Path) -> dict:
    """The `skill_read_paths` section, or {} when the contract is missing or malformed."""
    try:
        data = json.loads((repo_root / CONTRACT_REL).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    facts = data.get("skill_read_paths")
    return facts if isinstance(facts, dict) else {}


def _resolve(spec: str, ctx: Any) -> Path:
    if spec.startswith("~/"):
        return Path(ctx.global_root) / spec[2:]
    return Path(ctx.target_root) / spec


def verified_dirs(key: str, ctx: Any) -> list[Path]:
    """Resolved VERIFIED skill read paths for `key` at `ctx.scope`, in contract order."""
    entries = load_facts(Path(ctx.repo_root)).get(key, {})
    if not isinstance(entries, dict):
        return []
    out: list[Path] = []
    for entry in entries.get(getattr(ctx, "scope", ""), []) or []:
        if isinstance(entry, dict) and entry.get("status") == "VERIFIED" and isinstance(entry.get("path"), str):
            out.append(_resolve(entry["path"], ctx))
    return out


def enumerated_skill_dir(key: str, ctx: Any) -> Path | None:
    """The first VERIFIED read path that holds an installed skills tree, else None."""
    for path in verified_dirs(key, ctx):
        try:
            if path.is_dir() and any(path.glob("*/SKILL.md")):
                return path
        except OSError:
            continue
    return None


def render_pointer(skill_dir: Path, full_index: Path | None) -> str:
    """The Skill-Index Pointer that replaces the full table on an eligible platform."""
    lines = [
        "# Nexus-Hub Skill Index",
        "",
        "This platform discovers installed skills by itself, so the full skill table is not repeated here.",
        (f"The installed skills for this scope are in `{skill_dir.as_posix()}`: each skill is a folder with a "
        "`SKILL.md` file whose frontmatter `description` says when to use it."),
    ]
    if full_index is not None:
        lines.append(f"The complete table of every skill is in `{full_index.as_posix()}`.")
    return "\n".join(lines) + "\n"


def validate(facts: Any, doc: str) -> list[str]:
    """Schema and doc-agreement problems in a `skill_read_paths` section."""
    problems: list[str] = []
    if not isinstance(facts, dict):
        return ["skill_read_paths: missing or not an object"]
    for key, scopes in facts.items():
        if key.startswith("_"):
            continue
        if not isinstance(scopes, dict):
            problems.append(f"skill_read_paths.{key}: not an object")
            continue
        for scope, entries in scopes.items():
            if scope not in SCOPES or not isinstance(entries, list):
                problems.append(f"skill_read_paths.{key}.{scope}: unknown scope or not a list")
                continue
            for entry in entries:
                where = f"skill_read_paths.{key}.{scope}"
                if not isinstance(entry, dict):
                    problems.append(f"{where}: entry is not an object")
                    continue
                path, status = entry.get("path"), entry.get("status")
                if not isinstance(path, str) or not path:
                    problems.append(f"{where}: missing path")
                    continue
                if status not in STATUSES:
                    problems.append(f"{where} {path}: status must be one of {STATUSES}")
                if (scope == "global") != path.startswith("~/"):
                    problems.append(f"{where} {path}: global paths start with ~/, workspace paths are relative")
                if status == "VERIFIED":
                    source, verified = entry.get("source", ""), entry.get("verified", "")
                    if not (isinstance(source, str) and source.startswith("https://")):
                        problems.append(f"{where} {path}: VERIFIED needs an https source")
                    if not (isinstance(verified, str) and len(verified) == 10 and verified[4] == "-"):
                        problems.append(f"{where} {path}: VERIFIED needs an ISO verified date")
                    if path.rstrip("/") not in doc:
                        problems.append(f"{where} {path}: not documented in platform-read-contracts.md")
    return problems
