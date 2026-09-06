"""Deterministic install-selection resolver (v3.16.1 Phase 5.4).

Implements the normative contract in
`docs/releases/v3/v3.16/development/install-selection-contract.md`. That document is the
authority; where this module and the contract disagree, the contract is right.

Three properties matter more than anything else here, and each is load-bearing
for a different reason:

**Purity.** `resolve()` reads its inputs and returns a value. It opens no file,
writes nothing, and touches no install target. That is what makes the
fail-before-write rule structurally true rather than a discipline callers have to
remember: a caller physically cannot have written anything by the time resolution
raises.

**Determinism.** Every collection in the returned plan is sorted, and the plan
hash covers the resolved outcome rather than the request. Two ways of asking for
the same install (`--modules a,b` versus `--modules a --modules b`, or the
reverse order) therefore produce the same hash. This is not tidiness: the hash is
how Phase 6 proves that the Bash, PowerShell, and Python implementations agree,
so any nondeterminism here would silently weaken that check into nothing.

**Traversal-scoped validation.** Missing skills and dependency cycles are
detected over the subgraph the selection actually reaches, not by a global
catalog scan. A data defect in a corner of the catalog nobody selected must not
block an unrelated install; failing globally would make one bad row everyone's
problem.

The legacy Bash and PowerShell installers deliberately do NOT call this module -
they cannot depend on Python being present. They re-implement the same contract
natively and are held to it by the shared fixture matrix in
`tests/fixtures/install-selection/cases.json`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

__all__ = [
    "EXIT_USER_ERROR",
    "EXIT_CATALOG_ERROR",
    "FULL_PROFILE",
    "ALWAYS_PRESENT",
    "SelectionError",
    "UserSelectionError",
    "CatalogSelectionError",
    "Available",
    "SelectionRequest",
    "SelectionPlan",
    "resolve",
    "load_catalog",
    "available_from_catalog",
]

# Exit codes. The split is meaningful: a user can fix their own selector, and
# cannot fix a broken catalog. Collapsing them into one code would tell a user to
# check their spelling when the actual fault is in data/bundles.json.
EXIT_USER_ERROR = 2
EXIT_CATALOG_ERROR = 3

FULL_PROFILE = "full"

# Policy infrastructure. Present under every selection, including the narrowest.
# A user narrowing their skill set is asking for fewer capabilities, never for
# fewer guardrails; filtering the secret-scan hook out of a focused install would
# make the focused path less safe than the default one.
ALWAYS_PRESENT: tuple[str, ...] = (
    "context",
    "hooks",
    "indexes",
    "memory",
    "rules",
    "settings",
    "templates",
)


class SelectionError(Exception):
    """Base for selection failures. Carries the process exit code."""

    exit_code = EXIT_USER_ERROR

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class UserSelectionError(SelectionError):
    """The selector the user supplied is wrong. Exit 2."""

    exit_code = EXIT_USER_ERROR


class CatalogSelectionError(SelectionError):
    """The catalog is wrong. Exit 3; the user cannot fix this."""

    exit_code = EXIT_CATALOG_ERROR


@dataclass(frozen=True)
class Available:
    """What exists on disk (or, in tests, in the fixture catalog)."""

    skills: frozenset
    commands: frozenset = frozenset()
    agents: frozenset = frozenset()


@dataclass(frozen=True)
class SelectionRequest:
    """A parsed, validated-in-shape selector request. Ids are not checked here."""

    profile: Optional[str] = None
    modules: tuple = ()
    bundles: tuple = ()

    @property
    def is_empty(self) -> bool:
        return self.profile is None and not self.modules and not self.bundles

    @classmethod
    def from_args(
        cls,
        profiles: Optional[Sequence[str]] = None,
        modules: Optional[Sequence[str]] = None,
        bundles: Optional[Sequence[str]] = None,
    ) -> "SelectionRequest":
        """Build from raw CLI arguments.

        Each sequence element may itself be a comma-separated list, so the
        repeatable form (`--modules a --modules b`) and the CSV form
        (`--modules a,b`) collapse to the same request. The contract requires
        those to be indistinguishable.
        """
        parsed_profiles = _split_all(profiles, "profile")
        if len(parsed_profiles) > 1:
            raise UserSelectionError(
                "At most one profile may be selected, got "
                f"{len(parsed_profiles)}: {', '.join(parsed_profiles)}. "
                "Profiles are alternatives, not layers; combine a profile with "
                "--modules or --bundles instead."
            )
        return cls(
            profile=parsed_profiles[0] if parsed_profiles else None,
            modules=tuple(_split_all(modules, "module")),
            bundles=tuple(_split_all(bundles, "bundle")),
        )


@dataclass
class SelectionPlan:
    """The resolved outcome. Every collection is sorted."""

    requested: Dict[str, Any]
    skills: List[str]
    commands: List[str]
    agents: List[str]
    reasons: Dict[str, str]
    excluded_commands: Dict[str, str] = field(default_factory=dict)
    excluded_agents: Dict[str, str] = field(default_factory=dict)
    always_present: List[str] = field(default_factory=lambda: list(ALWAYS_PRESENT))
    catalog: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_full(self) -> bool:
        """True when this plan selects the entire catalog."""
        return bool(self.catalog.get("skill_count")) and len(self.skills) == self.catalog["skill_count"]

    def canonical(self) -> str:
        """The exact string the hash is computed over.

        Deliberately excludes `requested` and `warnings`. Two different ways of
        asking for the same install must hash the same, and advisory wording must
        not move the hash, or the cross-implementation parity check in Phase 6
        would fail on differences that do not affect a single installed byte.
        """
        return json.dumps(
            {
                "resolved": {
                    "agents": self.agents,
                    "commands": self.commands,
                    "skills": self.skills,
                },
                "always_present": self.always_present,
                "catalog": self.catalog,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )

    def hash(self) -> str:
        return "sha256:" + hashlib.sha256(self.canonical().encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested": self.requested,
            "resolved": {
                "skills": self.skills,
                "commands": self.commands,
                "agents": self.agents,
            },
            "reasons": self.reasons,
            "excluded": {
                "commands": self.excluded_commands,
                "agents": self.excluded_agents,
            },
            "always_present": self.always_present,
            "catalog": self.catalog,
            "warnings": self.warnings,
            "hash": self.hash(),
        }


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #

def _split_all(values: Optional[Sequence[str]], kind: str) -> List[str]:
    """Expand a repeatable/CSV argument list into individual ids, order-preserving.

    An empty element is an error rather than a dropped item: `--modules a,,b` is
    a typo, and silently accepting it would install something the user did not
    ask for while looking like it worked.
    """
    out: List[str] = []
    for raw in values or ():
        for part in str(raw).split(","):
            stripped = part.strip()
            if not stripped:
                raise UserSelectionError(
                    f"Empty {kind} in selector {raw!r}. Remove the stray comma or "
                    "the surrounding whitespace."
                )
            out.append(stripped)
    return out


# --------------------------------------------------------------------------- #
# Catalog access
# --------------------------------------------------------------------------- #

def load_catalog(path: Path) -> Dict[str, Any]:
    """Load a bundles.json-shaped document."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CatalogSelectionError(f"Selection catalog not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogSelectionError(f"Selection catalog is not valid JSON ({path}): {exc}") from exc


def available_from_catalog(catalog: Mapping[str, Any], repo_root: Optional[Path] = None) -> Available:
    """Determine what exists.

    Fixture catalogs declare `_available_skills` / `_available_commands` /
    `_available_agents` directly. For the real catalog those keys are absent and
    the filesystem under `repo_root` is the source of truth.
    """
    if "_available_skills" in catalog:
        return Available(
            skills=frozenset(catalog.get("_available_skills", ())),
            commands=frozenset(catalog.get("_available_commands", ())),
            agents=frozenset(catalog.get("_available_agents", ())),
        )
    if repo_root is None:
        raise CatalogSelectionError(
            "Catalog declares no _available_* keys and no repo_root was given, "
            "so what exists on disk cannot be determined."
        )
    root = Path(repo_root)
    skills = {p.parent.name for p in (root / "catalog" / "skills").glob("*/*/SKILL.md")}
    commands = {p.stem for p in (root / "catalog" / "commands").glob("*.md")}
    agents = {p.stem for p in (root / "catalog" / "agents").glob("*.md")}
    return Available(frozenset(skills), frozenset(commands), frozenset(agents))


def _index(entries: Iterable[Mapping[str, Any]]) -> Dict[str, Mapping[str, Any]]:
    return {e["id"]: e for e in entries if "id" in e}


# --------------------------------------------------------------------------- #
# Resolution
# --------------------------------------------------------------------------- #

def resolve(
    catalog: Mapping[str, Any],
    request: SelectionRequest,
    available: Available,
) -> SelectionPlan:
    """Resolve selectors into a deterministic selection plan.

    Raises UserSelectionError (exit 2) or CatalogSelectionError (exit 3). Never
    writes anything, which is what makes the fail-before-write rule structural.
    """
    profiles = _index(catalog.get("profiles", ()))
    modules = _index(catalog.get("modules", ()))
    bundles = _index(catalog.get("bundles", ()))
    dependencies: Mapping[str, Sequence[str]] = catalog.get("skill_dependencies", {}) or {}
    requirements = catalog.get("surface_requirements", {}) or {}
    command_reqs: Mapping[str, Sequence[str]] = requirements.get("commands", {}) or {}
    agent_reqs: Mapping[str, Sequence[str]] = requirements.get("agents", {}) or {}

    # --- 1-3. Validate ids and profile exclusivity ------------------------- #
    _require_known(request.profile, profiles, "profile")
    for mid in request.modules:
        _require_known(mid, modules, "module")
    for bid in request.bundles:
        _require_known(bid, bundles, "bundle")

    explicit_full = request.profile is not None and _is_full(profiles[request.profile], request.profile)
    if explicit_full and (request.modules or request.bundles):
        others = ", ".join(list(request.modules) + list(request.bundles))
        raise UserSelectionError(
            f"Profile '{FULL_PROFILE}' cannot be combined with other selectors "
            f"(got: {others}). '{FULL_PROFILE}' already means the entire catalog, "
            "so combining them means one of the two was misunderstood: drop "
            f"'{FULL_PROFILE}' to narrow the install, or drop the others to widen it."
        )

    # --- 4-5. Expand and union, recording why each skill entered ----------- #
    reasons: Dict[str, str] = {}

    if request.is_empty or explicit_full:
        # The no-selector default and explicit `full` are the same install.
        for name in sorted(available.skills):
            reasons.setdefault(name, "selector:profile:full")
        selected: Set[str] = set(available.skills)
    else:
        selected = set()
        # Fixed iteration order (profile, then sorted modules, then sorted
        # bundles) so the first-reason-wins rule is deterministic rather than
        # dependent on argument order.
        sources: List[tuple] = []
        if request.profile:
            sources.append(("profile", request.profile, profiles[request.profile]))
        for mid in sorted(set(request.modules)):
            sources.append(("module", mid, modules[mid]))
        for bid in sorted(set(request.bundles)):
            sources.append(("bundle", bid, bundles[bid]))

        for kind, sid, entry in sources:
            for name in _expand_entry(entry, kind, sid, modules, bundles, available):
                selected.add(name)
                # The reason names the selector the USER supplied, not the
                # intermediate bundle a profile happened to compose from. "You
                # asked for profile core" is actionable; "core's qa-engineer
                # bundle's testing module" is trivia.
                reasons.setdefault(name, f"selector:{kind}:{sid}")

    # --- 6. Transitive closure over the reached subgraph ------------------- #
    selected = _close(selected, dependencies, available, reasons)

    if not selected:
        requested_desc = _describe(request)
        raise UserSelectionError(
            f"Selection resolved to no skills ({requested_desc}). An empty install "
            "is never a useful end state; widen the selection or drop the selectors "
            "to get the default full install."
        )

    # --- 7. Surface eligibility -------------------------------------------- #
    commands, excluded_commands = _eligible(available.commands, command_reqs, selected)
    agents, excluded_agents = _eligible(available.agents, agent_reqs, selected)

    # --- 8-9. Assemble, sort, warn ----------------------------------------- #
    warnings: List[str] = []
    if not (request.is_empty or explicit_full) and selected == set(available.skills):
        # Resolved legitimately, so not an error - but an accidental full install
        # is a real outcome and must not be silent.
        warnings.append("full-catalog")

    return SelectionPlan(
        requested={
            "profile": request.profile,
            "modules": sorted(set(request.modules)),
            "bundles": sorted(set(request.bundles)),
        },
        skills=sorted(selected),
        commands=commands,
        agents=agents,
        reasons={k: reasons[k] for k in sorted(reasons) if k in selected},
        excluded_commands=excluded_commands,
        excluded_agents=excluded_agents,
        always_present=list(ALWAYS_PRESENT),
        catalog={
            "skill_count": len(available.skills),
            "bundles_version": str(catalog.get("metadata", {}).get("version", "")),
        },
        warnings=warnings,
    )


def _is_full(entry: Mapping[str, Any], entry_id: str) -> bool:
    """True for the catch-everything profile.

    `data/bundles.json` marks it with `"all": true` rather than by listing the
    catalog, so the marker is authoritative. The id check is a fallback for a
    catalog that names the profile `full` without the marker.
    """
    return bool(entry.get("all")) or entry_id == FULL_PROFILE


def _expand_entry(
    entry: Mapping[str, Any],
    kind: str,
    sid: str,
    modules: Mapping[str, Mapping[str, Any]],
    bundles: Mapping[str, Mapping[str, Any]],
    available: Available,
    _seen: Optional[Set[str]] = None,
) -> Set[str]:
    """Expand one selection entry to its skill set.

    Selection entries are NOT uniform, and assuming they were is a real mistake
    this function exists to prevent repeating. Modules and role bundles carry a
    flat `skills` list. Profiles carry no skills at all: they COMPOSE, via
    `bundles`, `modules`, and `extra_skills`. A resolver that reads only `skills`
    silently resolves every real profile to the empty set, which then surfaces as
    "empty selection" rather than as the modeling error it is.

    All four keys are unioned, so an entry may use any combination. References
    are followed one level with cycle protection, which costs nothing today (no
    profile references another profile) and prevents a non-terminating expansion
    if the schema ever grows one.
    """
    seen = _seen if _seen is not None else set()
    token = f"{kind}:{sid}"
    if token in seen:
        return set()
    seen.add(token)

    out: Set[str] = set()

    for name in list(entry.get("skills", ()) or ()) + list(entry.get("extra_skills", ()) or ()):
        if name not in available.skills:
            raise CatalogSelectionError(
                f"Selection {kind} '{sid}' references skill '{name}', which has no "
                "catalog directory. Fix data/bundles.json; a focused install "
                "cannot resolve it."
            )
        out.add(name)

    for ref in entry.get("modules", ()) or ():
        if ref not in modules:
            raise CatalogSelectionError(
                f"Selection {kind} '{sid}' references module '{ref}', which is not defined."
            )
        out |= _expand_entry(modules[ref], "module", ref, modules, bundles, available, seen)

    for ref in entry.get("bundles", ()) or ():
        if ref not in bundles:
            raise CatalogSelectionError(
                f"Selection {kind} '{sid}' references bundle '{ref}', which is not defined."
            )
        out |= _expand_entry(bundles[ref], "bundle", ref, modules, bundles, available, seen)

    return out


def _require_known(value: Optional[str], index: Mapping[str, Any], kind: str) -> None:
    if value is None:
        return
    if value not in index:
        known = ", ".join(sorted(index)) or "(none defined)"
        raise UserSelectionError(
            f"Unknown {kind}: '{value}'. Known {kind}s: {known}."
        )


def _close(
    seed: Set[str],
    dependencies: Mapping[str, Sequence[str]],
    available: Available,
    reasons: Dict[str, str],
) -> Set[str]:
    """Breadth-first dependency closure with traversal-scoped cycle detection.

    Cycles are detected over the reached subgraph only. A cycle elsewhere in the
    catalog is somebody else's problem and must not block this install.
    """
    if not dependencies:
        return set(seed)

    resolved: Set[str] = set(seed)
    queue: List[str] = sorted(seed)
    while queue:
        current = queue.pop(0)
        for dep in sorted(dependencies.get(current, ()) or ()):
            if dep not in available.skills:
                raise CatalogSelectionError(
                    f"Skill '{current}' declares a dependency on '{dep}', which has "
                    "no catalog directory."
                )
            if dep not in resolved:
                resolved.add(dep)
                reasons.setdefault(dep, f"dependency:{current}")
                queue.append(dep)

    cycle = _find_cycle(resolved, dependencies)
    if cycle:
        raise CatalogSelectionError(
            "Dependency cycle in the selected skills: " + " -> ".join(cycle) + ". "
            "Break the cycle in data/bundles.json `skill_dependencies`."
        )
    return resolved


def _find_cycle(nodes: Set[str], dependencies: Mapping[str, Sequence[str]]) -> List[str]:
    """Return one cycle as a node list, or [] when the subgraph is acyclic."""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}

    def visit(node: str, stack: List[str]) -> List[str]:
        color[node] = GREY
        stack.append(node)
        for dep in sorted(dependencies.get(node, ()) or ()):
            if dep not in color:
                continue
            if color[dep] == GREY:
                return stack[stack.index(dep):] + [dep]
            if color[dep] == WHITE:
                found = visit(dep, stack)
                if found:
                    return found
        stack.pop()
        color[node] = BLACK
        return []

    for node in sorted(nodes):
        if color[node] == WHITE:
            found = visit(node, [])
            if found:
                return found
    return []


def _eligible(
    surfaces: frozenset,
    requirements: Mapping[str, Sequence[str]],
    selected: Set[str],
) -> tuple:
    """Split surfaces into included and excluded-with-reason.

    A surface with NO declared requirement always installs. That default is
    deliberate: excluding undeclared surfaces would silently shrink every install
    the moment selection shipped, before a single declaration existed. Including
    them preserves current behavior exactly and lets declarations be added
    incrementally, each narrowing the surface by a known amount.
    """
    included: List[str] = []
    excluded: Dict[str, str] = {}
    for name in sorted(surfaces):
        required = requirements.get(name)
        if not required:
            included.append(name)
            continue
        missing = sorted(set(required) - selected)
        if missing:
            excluded[name] = "excluded:missing-skills:" + ",".join(missing)
        else:
            included.append(name)
    return included, excluded


def _describe(request: SelectionRequest) -> str:
    parts: List[str] = []
    if request.profile:
        parts.append(f"profile={request.profile}")
    if request.modules:
        parts.append("modules=" + ",".join(sorted(set(request.modules))))
    if request.bundles:
        parts.append("bundles=" + ",".join(sorted(set(request.bundles))))
    return "; ".join(parts) or "no selectors"


# --------------------------------------------------------------------------- #
# CLI (v3.16.1 Phase 6.1)
#
# `scripts/installer.sh` and `scripts/installer.ps1` shell out to this instead of
# reimplementing the contract. That is a deliberate reversal of the plan's
# "implement natively in each installer" wording, made after finding that the jq
# implementation could not be tested on the development host: two
# implementations of a hashed contract where one is unverifiable is worse than
# one implementation both callers share.
#
# What the plan's wording actually protects is preserved: a NO-SELECTOR full
# install still requires neither Python nor jq, because the installers only reach
# this CLI when a selector was supplied. A Python-less host already skips every
# registry-backed platform, so requiring Python for selectors specifically adds
# no new constraint that host was not already under.
# --------------------------------------------------------------------------- #

def _emit_lines(plan: "SelectionPlan") -> str:
    """Tab-separated records, for callers without a JSON parser.

    Bash reads this with a plain `while IFS=$'\\t' read -r kind value` loop, so
    the installer needs no jq and no second Python call to pick fields out.
    """
    out: List[str] = [f"HASH\t{plan.hash()}"]
    out.extend(f"SKILL\t{name}" for name in plan.skills)
    out.extend(f"COMMAND\t{name}" for name in plan.commands)
    out.extend(f"AGENT\t{name}" for name in plan.agents)
    out.extend(f"WARN\t{w}" for w in plan.warnings)
    return "\n".join(out)


def main(argv: Optional[Sequence[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="selection.py",
        description="Resolve a Nexus-Hub install selection. Writes nothing.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--catalog", help="Path to bundles.json (default: <repo-root>/data/bundles.json).")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--modules", action="append", default=[])
    parser.add_argument("--bundles", action="append", default=[])
    parser.add_argument(
        "--emit", choices=["json", "lines"], default="json",
        help="json: the full plan. lines: tab-separated records for shell callers.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    repo_root = Path(args.repo_root).resolve()
    catalog_path = Path(args.catalog) if args.catalog else repo_root / "data" / "bundles.json"
    try:
        catalog = load_catalog(catalog_path)
        available = available_from_catalog(catalog, repo_root=repo_root)
        request = SelectionRequest.from_args(
            profiles=[args.profile] if args.profile else [],
            modules=args.modules,
            bundles=args.bundles,
        )
        plan = resolve(catalog, request, available)
    except SelectionError as exc:
        print(f"selection: {exc}", file=__import__("sys").stderr)
        return exc.exit_code
    if args.emit == "lines":
        print(_emit_lines(plan))
    else:
        print(json.dumps(plan.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
