#!/usr/bin/env python3
"""Read-only minor re-plan analysis: overlap, redundancy, dependencies, schedule.

Summary: parses every member plan of one minor's plans folder and reports file
overlap between plans, redundant tasks, the dependency graph and critical path,
merge and split candidates, and a conflict-aware schedule with a proposed order
and version numbering that maximizes how many plans can run at once.

Audience: the `plan-queue-assessment` skill (owner), called from `/implement vX.Y`
Phase 0 today and from `/compare` and `/plan` later. It never edits a plan.

Usage:
    python replan_minor.py <plans-folder> [--json PATH|-] [--lanes N]
        [--similarity 0.8] [--include-all] [--include-boilerplate]
        [--record PATH | --no-record]

Exit codes: 0 analysis written; 1 a plan was unreadable (still reported);
2 usage error. Standard library only; no subprocess; nothing is written except
the optional --json file.

Structural limits (stated in the report): path sets come from the signed minor run
record's recorded claims for admitted members (when a schema 2 record for the minor
exists under NEXUS_HUB_RUNS_DIR or ~/.nexus-hub/runs, or --record), else from the
plan's fenced claims JSON, else from task lines, which is a lower bound. The record
is only read, never written. Wave
counts are a structural measure of how many plans can be in flight at once, never
a measured delivery time.
"""

from __future__ import annotations

import argparse
import difflib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"v(\d+)\.(\d+)\.(\d+)")
TASK_RE = re.compile(r"^\s*- \[( |x|X)\] (T\d+[A-Za-z0-9.]*)\s+(.*\S)\s*$")
PHASE_RE = re.compile(r"^##\s+Phase\s+(\d+)\s*[:\-]?\s*(.*)$")
FIELD_RE = re.compile(r"^\*\*(Version|Status|Slug|Plan Type)\*\*:\s*(.*)$")
FENCE_RE = re.compile(r"```json\s*\n(.*?)\n```", re.S)
PATHISH_RE = re.compile(r"^[\w.\-/{}*]+(?:\.[A-Za-z0-9]{1,8}|/)$")
DEP_RE = re.compile(r"(depends on|requires?|blocked by|real prerequisites?|must follow|builds on)", re.I)
DEP_WINDOW = 110
MIN_SHARED_WORDS = 3
SLUG_PREFIX = re.compile(r"^v\d+\.\d+\.\d+-")
NOT_DEP_RE = re.compile(r"\bno\b[^.\n]{0,60}prerequisite|not an? (implementation )?(prerequisite|dependency)|release successor", re.I)
DONE_STATUS = ("shipped", "released", "complete", "completed", "merged", "abandoned", "superseded", "archived")
STOP = {"the", "and", "for", "with", "that", "this", "from", "into", "are", "all", "each", "any", "its", "not",
        "per", "via", "has", "have", "use", "using", "when", "then", "than", "only", "plan", "task"}
# Per-phase template tasks repeat across plans by design; they are not redundancy.
BOILERPLATE_RE = re.compile(
    r"commit phase|locally|known-gaps|architecture refactor|terminal ci|tier 3|goal-vs-codebase|"
    r"manual testing suggestion|publication and integration|testing and stabilization|"
    r"session history|queue refresh|living docs|last-phase-evidence|hygiene|reconcile the pipeline|local gate|human testing", re.I)
# Mirrors the minor checker's coordinator-owned set: workers propose deltas, so
# these paths never create a worker conflict (completion_minor._coordinator_paths).
COORDINATOR_FIXED = (".nexus-hub/", "docs/todos.md", "changelog.md", "release_notes.md", "devlog.md", "version",
                     "version.txt", "package.json", "package-lock.json", "pyproject.toml", ".bumpversion.cfg",
                     "readme.md", "agents.md", "claude.md", "docs/readme.md", "docs/devlog.md",
                     "data/skills.json", "data/skill_index.md", "data/marketplace.json", "data/bundles.json",
                     ".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "manifest.sha256")


def overlap(left: str, right: str) -> bool:
    """Same semantics as completion_minor._overlap (casefold, directory prefix)."""
    a, b = left.casefold(), right.casefold()
    return a.rstrip("/") == b.rstrip("/") or (a.endswith("/") and b.startswith(a)) or (b.endswith("/") and a.startswith(b))


def is_coordinator(path: str) -> bool:
    low = path.casefold().rstrip("/")
    name = low.rsplit("/", 1)[-1]
    if "known-gaps" in name or name in {"changelog.md", "release_notes.md", "release-notes.md", "version", "version.txt"}:
        return True
    return any(overlap(low + ("/" if path.endswith("/") else ""), c) for c in COORDINATOR_FIXED)


def vkey(version: str) -> tuple[int, int, int]:
    m = VERSION_RE.search(version or "")
    return tuple(int(x) for x in m.groups()) if m else (10**6, 0, 0)  # type: ignore[return-value]


def default_lanes() -> int:
    """Lane cap: NEXUS_IMPLEMENT_LANES override, else min(cores // 2, 6), floor 1."""
    raw = os.environ.get("NEXUS_IMPLEMENT_LANES", "").strip()
    if raw.isdigit() and int(raw) >= 1:
        return int(raw)
    return max(1, min((os.cpu_count() or 2) // 2, 6))


def clean_path(token: str) -> str | None:
    token = token.strip().strip("`").rstrip(".,;:)").lstrip("(")
    if not token or token.startswith(("http", "-", "~")) or "<" in token or " " in token:
        return None
    if re.fullmatch(r"\d+(\.\d+)+", token) or token.lower() in {"e.g.", "i.e.", "etc."}:
        return None
    if "/" not in token and not re.search(r"\.[A-Za-z]{1,5}$", token):
        return None
    return token if PATHISH_RE.match(token) else None


def parse_plan(path: Path) -> dict:
    plan = {"file": path.name, "version": None, "slug": path.stem, "status": "undeclared", "title": "",
            "tasks": [], "phases": {}, "claims": None, "depends_hints": [], "readable": True, "error": None}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        plan.update(readable=False, error=str(exc))
        return plan
    m = VERSION_RE.match(path.name)
    plan["version"] = m.group(0) if m else None
    phase = 0
    for line in text.splitlines():
        if line.startswith("# ") and not plan["title"]:
            plan["title"] = line[2:].strip()
        f = FIELD_RE.match(line)
        if f:
            key, value = f.group(1), f.group(2).strip()
            if key == "Status":
                plan["status"] = (value.split()[0].lower().strip(".,;:") if value else "undeclared")
            elif key == "Version" and VERSION_RE.search(value):
                plan["version"] = VERSION_RE.search(value).group(0)
            elif key == "Slug":
                plan["slug"] = value
        p = PHASE_RE.match(line)
        if p:
            phase = int(p.group(1))
            plan["phases"][phase] = p.group(2).strip()
        t = TASK_RE.match(line)
        if t:
            plan["tasks"].append(parse_task(t, phase))
        elif DEP_RE.search(line) and not NOT_DEP_RE.search(line) and not line.lstrip().startswith("|"):
            for kw in DEP_RE.finditer(line):
                for v in VERSION_RE.finditer(line[kw.end():kw.end() + DEP_WINDOW]):
                    plan["depends_hints"].append({"version": v.group(0), "line": line.strip()[:200]})
    for block in FENCE_RE.findall(text):
        try:
            data = json.loads(block)
        except ValueError:
            continue
        if isinstance(data, dict) and {"depends_on", "read_paths", "write_paths"} <= set(data):
            plan["claims"] = {k: [str(x) for x in data[k]] for k in ("depends_on", "read_paths", "write_paths")}
            break
    return plan


def parse_task(match: re.Match, phase: int) -> dict:
    text = match.group(3)
    tokens = text.split()
    target = clean_path(tokens[-1]) if tokens else None
    mentions = [c for c in (clean_path(t) for t in re.findall(r"`([^`]+)`", text)) if c and c != target]
    stripped = re.sub(r"`[^`]*`", " ", text)
    words = [w for w in re.findall(r"[a-z0-9]+", stripped.lower()) if len(w) > 2 and w not in STOP]
    if target and tokens:
        words = [w for w in words if w not in re.findall(r"[a-z0-9]+", tokens[-1].lower())]
    return {"id": match.group(2), "done": match.group(1) != " ", "phase": phase, "text": text,
            "target": target, "mentions": mentions, "words": sorted({w.rstrip("s") for w in words}),
            "full_words": sorted({w.rstrip("s") for w in re.findall(r"[a-z0-9]+", text.lower())
                                  if len(w) > 2 and w not in STOP}),
            "boilerplate": bool(BOILERPLATE_RE.search(text)) or bool(target and "/development/" in target)}


def path_sets(plan: dict) -> dict:
    """Write/read path sets; claims JSON wins, task lines are a stated lower bound."""
    open_tasks = [t for t in plan["tasks"] if not t["done"]]
    derived_w = sorted({t["target"] for t in open_tasks if t["target"]})
    derived_r = sorted({m for t in open_tasks for m in t["mentions"]} - set(derived_w))
    if plan["claims"]:
        writes, reads, source = plan["claims"]["write_paths"], plan["claims"]["read_paths"], "claims"
    else:
        writes, reads, source = derived_w, derived_r, "tasks-derived (lower bound)"
    return {"source": source, "write": sorted(set(writes)), "read": sorted(set(reads)),
            "coordinator": sorted(p for p in set(writes) | set(reads) if is_coordinator(p))}


def member_state(plan: dict, include_all: bool) -> str:
    if not plan["readable"]:
        return "unreadable"
    if include_all:
        return "member"
    if plan["status"] in DONE_STATUS:
        return "excluded"
    if plan["tasks"] and all(t["done"] for t in plan["tasks"]):
        plan["status"] = plan["status"] + " (all tasks checked)"
        return "excluded"
    return "member"


def pairwise_overlaps(members: list[dict]) -> list[dict]:
    """Conflicting pairs. `hard` is False when every conflict is a write against a directory
    READ claim, which narrowing that read claim to exact files removes."""
    out = []
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            ww = sorted({f"{x} <> {y}" if x != y else x for x in a["paths"]["write"] for y in b["paths"]["write"]
                         if overlap(x, y) and not is_coordinator(x) and not is_coordinator(y)})
            wr_items = []
            for writer, reader in ((a, b), (b, a)):
                for x in writer["paths"]["write"]:
                    for y in reader["paths"]["read"]:
                        if overlap(x, y) and not is_coordinator(x):
                            wr_items.append((f"{x} (writes {writer['version']}) <> {y} (reads {reader['version']})",
                                             y.endswith("/") and not x.endswith("/")))
            wr = sorted({t for t, _ in wr_items})
            if ww or wr:
                hard = bool(ww) or any(not narrowable for _, narrowable in wr_items)
                out.append({"a": a["version"], "b": b["version"], "hard": hard, "write_write": ww, "write_read": wr})
    return out


def redundant_tasks(members: list[dict], threshold: float, include_boilerplate: bool) -> tuple[list[dict], int]:
    pairs, suppressed = [], 0
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            for ta in a["tasks"]:
                for tb in b["tasks"]:
                    if ta["done"] or tb["done"]:
                        continue
                    if not include_boilerplate and (ta["boilerplate"] or tb["boilerplate"]):
                        suppressed += 1
                        continue
                    # Compare the FULL task text, backticked names and path tokens included. The
                    # earlier prose-only word set collapsed to the lead verb for tasks that are
                    # mostly names and paths ("Add the `x` control ... path"), so unrelated tasks
                    # scored 1.0. Require several shared content words as well as high similarity.
                    sa, sb = set(ta["full_words"]), set(tb["full_words"])
                    shared = sa & sb
                    if len(shared) < MIN_SHARED_WORDS or len(shared) / len(sa | sb) < 0.35:
                        continue
                    sim = difflib.SequenceMatcher(None, " ".join(ta["full_words"]), " ".join(tb["full_words"])).ratio()
                    dir_target = bool((ta["target"] or "").endswith("/") or (tb["target"] or "").endswith("/"))
                    # A directory target prefix-overlaps every file under it, so it is not a file match.
                    same = bool(ta["target"] and tb["target"] and not dir_target and overlap(ta["target"], tb["target"]))
                    if ta["target"] and tb["target"] and not same and not dir_target and sim < max(threshold, 0.9):
                        continue  # two distinct files: the text alone must be near-identical
                    if sim >= threshold or (same and sim >= 0.55):
                        pairs.append({"a": a["version"], "a_task": ta["id"], "b": b["version"], "b_task": tb["id"],
                                      "similarity": round(sim, 2), "shared_target": ta["target"] if same else None,
                                      "a_text": ta["text"][:140], "b_text": tb["text"][:140]})
    pairs.sort(key=lambda p: (-p["similarity"], p["a"], p["b"]))
    return pairs, suppressed


def dependency_graph(members: list[dict], claims_only: bool = False) -> dict:
    versions = {m["version"] for m in members}
    edges, evidence, prose_only = set(), {}, set()
    for m in members:
        declared = set()
        if m["claims"]:
            for d in m["claims"]["depends_on"]:
                declared |= {v.group(0) for v in VERSION_RE.finditer(d)}
        hinted = {h["version"] for h in m["depends_hints"]}
        for dep in (declared | (set() if claims_only else hinted)) & versions:
            if dep != m["version"]:
                edges.add((dep, m["version"]))
                if dep not in declared:
                    prose_only.add((dep, m["version"]))
                evidence[f"{dep}->{m['version']}"] = ("claims.depends_on" if dep in declared else
                                                      next(h["line"] for h in m["depends_hints"] if h["version"] == dep))
    weight = {m["version"]: max(1, m["open_tasks"]) for m in members}
    order, cycle = topo_order(versions, edges)
    longest, prev = {}, {}
    for v in order:
        best = max(((longest[d], d) for d, t in edges if t == v), default=(0, None))
        longest[v], prev[v] = best[0] + weight[v], best[1]
    downstream: dict[str, int] = {}
    for v in reversed(order):
        downstream[v] = weight[v] + max((downstream[t] for d, t in edges if d == v), default=0)
    path, node = [], max(longest, key=longest.get) if longest else None
    while node:
        path.append(node)
        node = prev.get(node)
    return {"edges": sorted(edges), "prose_only_edges": sorted(prose_only), "evidence": evidence, "cycle": cycle, "critical_path": path[::-1],
            "critical_weight": max(longest.values(), default=0), "tail": downstream}


def topo_order(nodes: set[str], edges: set[tuple[str, str]]) -> tuple[list[str], list[str]]:
    remaining, order = set(nodes), []
    while remaining:
        ready = sorted((n for n in remaining if all(d not in remaining for d, t in edges if t == n)), key=vkey)
        if not ready:
            return order, sorted(remaining, key=vkey)
        order += ready
        remaining -= set(ready)
    return order, []


def claim_blockers(members: list[dict]) -> list[dict]:
    """The claims that serialize plans, broadest first, each with the fix that frees parallel lanes.

    A directory claim, or one exact file shared by several writers, is what turns independent plans
    into a queue. Each entry names the claim, the plans it blocks and the narrowing to apply.
    """
    found: dict[str, dict] = {}
    for i, a in enumerate(members):
        for b in members[i + 1:]:
            for writer, other in ((a, b), (b, a)):
                for x in writer["paths"]["write"]:
                    if is_coordinator(x):
                        continue
                    for y in other["paths"]["write"] + other["paths"]["read"]:
                        if not overlap(x, y) or is_coordinator(y):
                            continue
                        broad = x if x.endswith("/") or not y.endswith("/") else y
                        entry = found.setdefault(broad, {"path": broad, "plans": set()})
                        entry["plans"].update({a["version"], b["version"]})
    out = []
    for entry in found.values():
        plans = sorted(entry["plans"], key=vkey)
        if entry["path"].endswith("/"):
            fix = "narrow to the exact files each plan edits; claim a directory only when one plan creates and owns it"
        else:
            fix = "one plan owns this file; the others propose a delta or run after it"
        out.append({"path": entry["path"], "plans": plans, "fix": fix})
    return sorted(out, key=lambda e: (-len(e["plans"]), e["path"]))


def conflict_map(members: list[dict], overlaps: list[dict], hard_only: bool = True) -> dict[str, set[str]]:
    conflicts = {m["version"]: set() for m in members}
    for o in overlaps:
        if hard_only and not o["hard"]:
            continue
        conflicts[o["a"]].add(o["b"])
        conflicts[o["b"]].add(o["a"])
    return conflicts


def dsatur(conflicts: dict[str, set[str]]) -> dict[str, int]:
    """Greedy DSatur coloring: each color class is a set that can run concurrently."""
    color: dict[str, int] = {}
    while len(color) < len(conflicts):
        def key(v: str) -> tuple:
            seen = {color[n] for n in conflicts[v] if n in color}
            return (-len(seen), -len(conflicts[v]), vkey(v))
        v = min((n for n in conflicts if n not in color), key=key)
        used = {color[n] for n in conflicts[v] if n in color}
        color[v] = next(c for c in range(len(conflicts) + 1) if c not in used)
    return color


def schedule(versions: list[str], edges: set[tuple[str, str]], conflicts: dict[str, set[str]], lanes: int,
             priority: dict[str, tuple]) -> tuple[list[list[str]], list[str]]:
    """Wave schedule: each wave is a conflict-free ready set up to the lane cap."""
    done: set[str] = set()
    remaining, waves = set(versions), []
    while remaining:
        ready = sorted((v for v in remaining if all(d in done for d, t in edges if t == v)), key=lambda v: priority[v])
        if not ready:
            return waves, sorted(remaining, key=vkey)
        chosen: list[str] = []
        for v in ready:
            if len(chosen) < lanes and not any(v in conflicts[c] for c in chosen):
                chosen.append(v)
        waves.append(chosen)
        done |= set(chosen)
        remaining -= set(chosen)
    return waves, []


def merge_candidates(members: list[dict], overlaps: list[dict], redundant: list[dict], cap: int) -> list[dict]:
    by_pair: dict[tuple[str, str], int] = {}
    for r in redundant:
        by_pair[(r["a"], r["b"])] = by_pair.get((r["a"], r["b"]), 0) + 1
    info = {m["version"]: m for m in members}
    out = []
    for o in overlaps:
        a, b = info[o["a"]], info[o["b"]]
        wa, wb = set(a["paths"]["write"]), set(b["paths"]["write"])
        shared = {x for x in wa for y in wb if overlap(x, y) and not is_coordinator(x)}
        jac = len(shared) / max(1, len(wa | wb))
        dup = by_pair.get((o["a"], o["b"]), 0)
        total = a["open_tasks"] + b["open_tasks"]
        if (jac >= 0.4 or dup >= 3) and total <= cap and not a["pinned"] and not b["pinned"]:
            out.append({"plans": [o["a"], o["b"]], "write_overlap_ratio": round(jac, 2), "redundant_task_pairs": dup,
                        "combined_open_tasks": total, "shared_writes": sorted(shared)[:8],
                        "reason": "same files and repeated work; one plan removes the serialization and the duplicates"})
    return out


def split_candidates(members: list[dict], conflicts: dict[str, set[str]], threshold: int) -> list[dict]:
    out = []
    for m in members:
        if m["open_tasks"] < threshold or m["pinned"]:
            continue
        phases: dict[int, set[str]] = {}
        for t in m["tasks"]:
            if not t["done"] and t["target"] and not is_coordinator(t["target"]):
                phases.setdefault(t["phase"], set()).add(t["target"])
        comps: list[tuple[set[int], set[str]]] = []
        for n, files in sorted(phases.items()):
            joined = [c for c in comps if any(overlap(x, y) for x in files for y in c[1])]
            merged = ({n}, set(files))
            for c in joined:
                comps.remove(c)
                merged = (merged[0] | c[0], merged[1] | c[1])
            comps.append(merged)
        if len(comps) >= 2:
            out.append({"plan": m["version"], "open_tasks": m["open_tasks"], "conflicts_with": sorted(conflicts[m["version"]], key=vkey),
                        "independent_phase_groups": [{"phases": sorted(c[0]), "files": sorted(c[1])[:6]} for c in sorted(comps, key=lambda c: min(c[0]))],
                        "reason": "phase groups share no files; each could be its own plan with fewer conflicts"})
    return out


def load_record_claims(folder: Path, record: str | None) -> tuple[dict[str, dict], str]:
    """Recorded claims per admitted member from the minor's schema 2 run record (read-only).

    Reuses claims_precheck.find_members (recursive, includes amended members). Returns ({}, reason)
    when no record applies; the caller then falls back to plan prose."""
    helper = Path(__file__).resolve().parents[2] / "implement-phase" / "scripts" / "claims_precheck.py"
    if not helper.is_file():
        return {}, "claims_precheck.py not found"
    spec = importlib.util.spec_from_file_location("claims_precheck_for_replan", helper)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if record:
        chosen = Path(record)
    else:
        minor = None
        for part in reversed(folder.resolve().parts):
            m = re.fullmatch(r"v(\d+)\.(\d+)", part)
            if m:
                minor = part
                break
        if not minor:
            return {}, "minor not derivable from the folder"
        override = os.environ.get("NEXUS_HUB_RUNS_DIR")
        runs = Path(override) if override else Path.home() / ".nexus-hub" / "runs"
        found = []
        for f in sorted(runs.glob("*.json")) if runs.is_dir() else []:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(data, dict) and data.get("schema") == 2 and data.get("minor") == minor:
                found.append((str(data.get("created", "")), f))
        if not found:
            return {}, f"no schema 2 run record for {minor}"
        chosen = sorted(found)[-1][1]
    try:
        data = json.loads(chosen.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {}, f"run record unreadable ({exc})"
    return mod.find_members(data), chosen.name


def analyze(folder: Path, lanes: int, similarity: float, include_all: bool, include_boilerplate: bool,
            claims_deps_only: bool = False, record_claims: dict[str, dict] | None = None,
            record_name: str | None = None, record_note: str = "") -> dict:
    files = sorted(p for p in folder.glob("*.md") if VERSION_RE.match(p.name))
    parsed = [parse_plan(p) for p in files]
    members, excluded, unreadable = [], [], []
    for p in parsed:
        state = member_state(p, include_all)
        (members if state == "member" else excluded if state == "excluded" else unreadable).append(p)
    for p in members:
        p["paths"] = path_sets(p)
        rec = (record_claims or {}).get(p["version"])
        if rec and rec["write"]:
            writes, reads = set(rec["write"]), set(rec["read"])
            p["paths"] = {"source": "run record", "write": sorted(writes), "read": sorted(reads),
                          "coordinator": sorted(x for x in writes | reads if is_coordinator(x))}
        p["open_tasks"] = sum(1 for t in p["tasks"] if not t["done"])
        p["pinned"] = any(t["done"] for t in p["tasks"]) or p["status"] in ("in-progress", "implementing", "active")
    members.sort(key=lambda m: vkey(m["version"]))
    overlaps = pairwise_overlaps(members)
    redundant, suppressed = redundant_tasks(members, similarity, include_boilerplate)
    deps = dependency_graph(members, claims_deps_only)
    conflicts = conflict_map(members, overlaps)
    strict = conflict_map(members, overlaps, hard_only=False)
    edges = set(map(tuple, deps["edges"]))
    versions = [m["version"] for m in members]
    crit = deps["tail"]
    baseline_waves, base_cycle = schedule(versions, edges, conflicts, lanes, {v: (vkey(v),) for v in versions})
    weight = {m["version"]: m["open_tasks"] for m in members}
    strategies = {
        "version-order": {v: (vkey(v),) for v in versions},
        "critical-path-first": {v: (-crit.get(v, 0), len(conflicts[v]), vkey(v)) for v in versions},
        "fewest-conflicts-first": {v: (len(conflicts[v]), -crit.get(v, 0), vkey(v)) for v in versions},
        "most-conflicts-first": {v: (-len(conflicts[v]), -crit.get(v, 0), vkey(v)) for v in versions},
        "largest-first": {v: (-weight[v], len(conflicts[v]), vkey(v)) for v in versions},
    }
    results = {name: schedule(versions, edges, conflicts, lanes, pr) for name, pr in strategies.items()}
    best = min(strategies, key=lambda n: (len(results[n][0]), list(strategies).index(n)))
    proposed_waves, cycle = results[best]
    strict_waves, _ = schedule(versions, edges, strict, lanes, strategies[best])
    colors = dsatur(conflicts)
    groups = {}
    for v, c in colors.items():
        groups.setdefault(c, []).append(v)
    moves, renumber_note = propose_moves(members, proposed_waves, baseline_waves, edges, cycle or base_cycle)
    peak = max((len(w) for w in proposed_waves), default=0)
    hot: dict[str, set[str]] = {}
    for m in members:
        for x in m["paths"]["write"]:
            if not is_coordinator(x):
                hot.setdefault(x, set()).add(m["version"])
    return {
        "folder": str(folder), "lanes": lanes, "record": record_name, "record_note": record_note,
        "plans": [{"version": m["version"], "slug": SLUG_PREFIX.sub("", m["slug"]), "status": m["status"], "open_tasks": m["open_tasks"],
                   "total_tasks": len(m["tasks"]), "phases": len(m["phases"]), "pinned": m["pinned"],
                   "path_source": m["paths"]["source"], "writes": len(m["paths"]["write"]),
                   "reads": len(m["paths"]["read"]), "coordinator_paths": m["paths"]["coordinator"]} for m in members],
        "excluded": [{"version": p["version"], "status": p["status"]} for p in excluded],
        "narrowable_pairs": sum(1 for o in overlaps if not o["hard"]),
        "unreadable": [{"file": p["file"], "error": p["error"]} for p in unreadable],
        "overlaps": overlaps,
        "claim_blockers": claim_blockers(members)[:15],
        "dispatch_now": sorted(proposed_waves[0], key=vkey) if proposed_waves else [],
        "hot_files": sorted(({"path": k, "plans": sorted(v, key=vkey)} for k, v in hot.items() if len(v) > 1),
                            key=lambda h: (-len(h["plans"]), h["path"]))[:15],
        "redundant_tasks": redundant, "boilerplate_pairs_suppressed": suppressed,
        "dependencies": {k: v for k, v in deps.items() if k != "tail"},
        "merge_candidates": merge_candidates(members, overlaps, redundant, 40),
        "split_candidates": split_candidates(members, conflicts, 30),
        "concurrency_groups": [sorted(g, key=vkey) for _, g in sorted(groups.items())],
        "schedule": {"baseline_waves": baseline_waves, "proposed_waves": proposed_waves, "peak_parallel": peak,
                     "baseline_wave_count": len(baseline_waves), "proposed_wave_count": len(proposed_waves),
                     "strategy": best, "strategy_wave_counts": {n: len(r[0]) for n, r in results.items()},
                     "strict_waves": strict_waves, "strict_wave_count": len(strict_waves),
                     "cycle": cycle or base_cycle},
        "proposed_order": [v for w in proposed_waves for v in sorted(w, key=vkey)],
        "proposed_renumber": moves, "renumber_note": renumber_note,
        "limits": ["Path sets come from claims JSON when a plan has it, else from task lines (a lower bound).",
                   "Wave counts are structural (plans in flight at once), not measured delivery time.",
                   "Dependency edges from prose hints are evidence lines to verify, not facts.",
                   "Coordinator-owned paths (CHANGELOG, docs/todos.md, known-gaps, data/ registries) never create a worker conflict."],
    }


def propose_moves(members: list[dict], proposed: list[list[str]], baseline: list[list[str]],
                  edges: set[tuple[str, str]], cycle: list[str]) -> tuple[list[dict], str]:
    if cycle:
        return [], "dependency cycle among " + ", ".join(cycle) + "; resolve the cycle before renumbering"
    if len(proposed) >= len(baseline):
        return [], "current version order already reaches the best wave count found; no renumber proposed"
    info = {m["version"]: m for m in members}
    movable = [v for w in proposed for v in sorted(w, key=vkey) if not info[v]["pinned"]]
    slots = sorted(movable, key=vkey)
    new = {v: v for v in info}
    new.update(dict(zip(movable, slots)))
    for dep, target in edges:
        if vkey(new[dep]) >= vkey(new[target]):
            return [], f"renumbering would put {dep} at or after its dependent {target}; kept current versions"
    wave_of = {v: i + 1 for i, w in enumerate(proposed) for v in w}
    moves = [{"slug": SLUG_PREFIX.sub("", info[v]["slug"]), "from": v, "to": new[v], "wave": wave_of[v],
              "reason": f"runs in wave {wave_of[v]} of {len(proposed)}; version order must equal release order"}
             for v in movable if new[v] != v]
    return moves, (f"{len(moves)} renumbers (each repairs seven reference classes) would save {len(baseline) - len(proposed)} "
                   "structural wave(s); weigh that cost. Proposals only; apply through the renumber procedure after approval")


def render_markdown(r: dict) -> str:
    s = r["schedule"]
    lines = [f"# Minor re-plan analysis: {r['folder']}", "",
             f"Read-only report. Nothing was edited. Lane cap: {r['lanes']}. Plans analyzed: {len(r['plans'])}"
             f" (excluded: {len(r['excluded'])}, unreadable: {len(r['unreadable'])}).",
             (f"Claims source: run record {r['record']} for admitted members, plan prose for the rest."
              if r.get("record") else f"Claims source: plan prose only ({r.get('record_note') or 'no record'})."), "",
             "| Plan | Status | Open/Total | Writes | Reads | Path source |", "|---|---|---|---|---|---|"]
    for p in r["plans"]:
        lines.append(f"| {p['version']} {p['slug']} | {p['status']}{' (pinned)' if p['pinned'] else ''} | "
                     f"{p['open_tasks']}/{p['total_tasks']} | {p['writes']} | {p['reads']} | {p['path_source']} |")
    lines += ["", f"## Overlap ({len(r['overlaps'])} conflicting pairs, {r['narrowable_pairs']} removable by narrowing a directory read claim to exact files)"]
    for o in sorted(r["overlaps"], key=lambda o: (not o["hard"], o["a"], o["b"]))[:12]:
        sample = (o["write_write"] + o["write_read"])[:3]
        lines.append(f"- {o['a']} vs {o['b']}{'' if o['hard'] else ' [narrowable]'}: {len(o['write_write'])} write/write, {len(o['write_read'])} write/read. "
                     f"e.g. {'; '.join(sample)}")
    lines += ["", "## Claims that block parallel lanes (narrow these first)"]
    lines += [f"- {b['path']} blocks {', '.join(b['plans'])}: {b['fix']}" for b in r["claim_blockers"]] or ["- none"]
    lines += ["", "## Redundancy"]
    lines += [f"- {t['a']} {t['a_task']} ~ {t['b']} {t['b_task']} (similarity {t['similarity']}"
              f"{', target ' + t['shared_target'] if t['shared_target'] else ''}): {t['a_text'][:80]}"
              for t in r["redundant_tasks"][:10]] or ["- none above threshold"]
    d = r["dependencies"]
    lines += ["", "## Dependencies",
              f"- Claims-declared edges: {', '.join(f'{a}->{b}' for a, b in d['edges'] if (a, b) not in set(map(tuple, d['prose_only_edges']))) or 'none'}",
              f"- Prose hints to verify (treated as edges): {', '.join(f'{a}->{b}' for a, b in d['prose_only_edges']) or 'none'}",
              f"- Critical path ({d['critical_weight']} open tasks): {' -> '.join(d['critical_path']) or 'n/a'}"]
    if d["cycle"]:
        lines.append(f"- CYCLE: {', '.join(d['cycle'])}")
    lines += ["", "## Merge and split candidates"]
    lines += [f"- Merge {' + '.join(m['plans'])}: overlap {m['write_overlap_ratio']}, {m['redundant_task_pairs']} duplicate pairs"
              for m in r["merge_candidates"]]
    lines += [f"- Split {c['plan']}: {len(c['independent_phase_groups'])} independent phase groups" for c in r["split_candidates"]]
    if not r["merge_candidates"] and not r["split_candidates"]:
        lines.append("- none")
    lines += ["", "## Schedule (structural waves, not time)",
              f"- Current version order: {s['baseline_wave_count']} waves. Best ({s['strategy']}): {s['proposed_wave_count']} waves, peak {s['peak_parallel']} in parallel (assumes narrowable read claims are narrowed).",
              f"- If every claim stays as written: {s['strict_wave_count']} waves."]
    lines += [f"- Wave {i + 1}: {', '.join(sorted(w, key=vkey))}" for i, w in enumerate(s["proposed_waves"])]
    lines += [f"- Dispatch now (every eligible member, up to the lane cap of {r['lanes']}): {', '.join(r['dispatch_now']) or 'none'}"]
    lines += ["", "## Proposed renumber", f"- {r['renumber_note']}"]
    lines += [f"- {m['from']} -> {m['to']} ({m['slug']}): {m['reason']}" for m in r["proposed_renumber"]]
    lines += ["", "## Limits"] + [f"- {x}" for x in r["limits"]]
    lines += ["", "Proposals need user approval before any plan file changes."]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Read-only minor re-plan analysis.")
    ap.add_argument("folder", help="a minor's plans folder, for example docs/releases/v4/v4.15/plans")
    ap.add_argument("--json", metavar="PATH", help="write JSON here, or '-' for JSON on stdout instead of Markdown")
    ap.add_argument("--lanes", type=int, default=default_lanes(), help="concurrent lane cap (default min(cores/2, 6))")
    ap.add_argument("--similarity", type=float, default=0.8, help="task similarity threshold (default 0.8)")
    ap.add_argument("--include-all", action="store_true", help="also analyze shipped, abandoned or superseded plans")
    ap.add_argument("--include-boilerplate", action="store_true", help="do not suppress per-phase template tasks")
    ap.add_argument("--record", metavar="PATH", help="minor run record to read recorded claims from (default: discover)")
    ap.add_argument("--no-record", action="store_true", help="use plan prose only; skip the run record")
    ap.add_argument("--claims-deps-only", action="store_true", help="ignore dependency hints found in plan prose")
    args = ap.parse_args(argv)
    folder = Path(args.folder)
    if not folder.is_dir() or args.lanes < 1:
        print(f"usage error: {folder} is not a folder or --lanes < 1", file=sys.stderr)
        return 2
    rec_claims, rec_name = ({}, "--no-record given") if args.no_record else load_record_claims(folder, args.record)
    named = rec_name if rec_claims else None
    report = analyze(folder, args.lanes, args.similarity, args.include_all, args.include_boilerplate,
                     args.claims_deps_only, rec_claims, named, "" if named else rec_name)
    if args.json == "-":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        sys.stdout.write(render_markdown(report))
        if args.json:
            Path(args.json).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if report["unreadable"] else 0


if __name__ == "__main__":
    sys.exit(main())
