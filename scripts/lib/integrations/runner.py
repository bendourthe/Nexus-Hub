"""Runner CLI for Nexus-Hub integrations.

Invoked from `scripts/installer.sh` and `scripts/installer.ps1` (and usable
standalone). Walks the integration registry and dispatches install / list /
teardown actions per platform.

Usage:
    python scripts/lib/integrations/runner.py list
    python scripts/lib/integrations/runner.py install \\
        --scope workspace --target /path/to/project \\
        --integrations claude,gemini,cursor
    python scripts/lib/integrations/runner.py install \\
        --scope global --integrations all
    python scripts/lib/integrations/runner.py teardown --target /path/to/project

Exit codes:
    0 success, 1 user error, 2 internal error.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path, PurePath
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.integrations import INTEGRATION_REGISTRY, get, list_keys  # noqa: E402
from scripts.lib.integrations.base import InstallContext  # noqa: E402
from scripts.lib.integrations.lifecycle import (  # noqa: E402
    DIAGNOSTIC_DRIFTED,
    DIAGNOSTIC_MISSING,
    DIAGNOSTIC_OK,
    DIAGNOSTIC_UNKNOWN,
    DoctorReport,
    doctor as lifecycle_doctor,
    list_installed as lifecycle_list_installed,
    repair as lifecycle_repair,
)
from scripts.lib.integrations.manifest import InstallManifest  # noqa: E402
from scripts.lib.integrations.result import WriteResult  # noqa: E402


_ACTION_PREFIX = {
    "created": "[+]",
    "updated": "[~]",
    "unchanged": "[=]",
    "removed": "[-]",
    "not-found": "[!]",
    "kept": "[k]",
}


def _render_write_result(integration_key: str, result: WriteResult, quiet: bool) -> None:
    """Print one summary line per FileAction, plus any notes.

    Suppressed entirely when `quiet=True` (the installer uses its own headers).
    """
    if quiet:
        return
    for fa in result.files:
        prefix = _ACTION_PREFIX.get(fa.action, "[?]")
        print(f"  {prefix} {fa.action:<10} {fa.path}")
    for note in result.notes:
        print(f"  (note) {note}")


# --- Per-platform install summary (v3.14.5 Phase 1) -------------------------
# The installer runs the runner with --quiet and needs a structured, per-surface
# view of what each platform installed so it can render a checklist (and group
# undetected platforms) instead of an unconditional "Installed" line. The summary
# is built directly from each integration's WriteResult, so it is populated even
# under --quiet; _render_write_result's quiet early-return only suppresses the
# per-file PRINTING, not the data captured here.

# Canonical surface order used by the installer checklist.
_CANONICAL_SURFACES = (
    "instruction",
    "skills",
    "commands",
    "agents",
    "rules",
    "hooks",
    "settings",
)

# Path segments (lowercased) that identify the commands and agents surfaces.
_COMMANDS_SEGMENTS = frozenset({"commands", "workflows", "global_workflows", "prompts"})
_AGENTS_SEGMENTS = frozenset({"agents", "subagents"})

# FileAction actions that mean the surface is present on disk after the install.
_PRESENT_ACTIONS = frozenset({"created", "updated", "unchanged", "kept"})


def _classify_surface(path_str: str, instruction_file: Optional[str]) -> Optional[str]:
    """Map one FileAction path to a canonical surface, or None if uncategorized.

    Classification is by path shape (basename / suffix / segment names) rather
    than a FileAction field, so it works uniformly regardless of how each
    integration computed the path. Order is load-bearing: the instruction file
    is matched by exact basename first, and ``skills`` is checked before
    ``agents`` so a shared ``~/.agents/skills`` path classifies as skills (its
    ``.agents`` container segment is deliberately not treated as the agents
    surface).
    """
    pure = PurePath(path_str)
    name = pure.name
    lower_name = name.lower()
    suffix = pure.suffix.lower()
    segments = {part.lower() for part in pure.parts}

    if instruction_file and name == instruction_file:
        return "instruction"
    if lower_name == "settings.json":
        return "settings"
    if lower_name == "hooks.json":
        return "hooks"
    if "skills" in segments:
        return "skills"
    if segments & _COMMANDS_SEGMENTS or suffix == ".toml" or lower_name.endswith(".prompt.md"):
        return "commands"
    if segments & _AGENTS_SEGMENTS:
        return "agents"
    if "rules" in segments or suffix == ".mdc" or lower_name == ".windsurfrules":
        return "rules"
    if "hooks" in segments:
        return "hooks"
    return None


# Path segments that identify each directory surface, used to trim a FileAction
# path down to its surface directory for display.
_SURFACE_SEGMENTS = {
    "skills": frozenset({"skills"}),
    "commands": _COMMANDS_SEGMENTS,
    "agents": _AGENTS_SEGMENTS,
    "rules": frozenset({"rules"}),
    "hooks": frozenset({"hooks"}),
}


def _surface_root(path_str: str, surface: str) -> str:
    """Return the surface's directory for one FileAction path.

    FileActions within a surface land at inconsistent depths (a flattened skill
    dir ``~/.codex/skills/foo`` vs a command-skill file
    ``~/.codex/skills/bar/SKILL.md``), so trimming each path to the ancestor
    ending at the surface segment (``~/.codex/skills``) is what makes the
    distinct-directory set meaningful. File surfaces (instruction, settings) and
    unmatched paths return the path unchanged.
    """
    segs = _SURFACE_SEGMENTS.get(surface)
    if not segs:
        return path_str
    parts = PurePath(path_str).parts
    for i, part in enumerate(parts):
        if part.lower() in segs:
            return str(PurePath(*parts[: i + 1]))
    return path_str


def _join_distinct(values: List[str]) -> str:
    """Join distinct non-empty values in first-seen order with ', '.

    A surface can span more than one root (Codex writes skills to BOTH
    ``~/.codex/skills`` and ``~/.agents/skills``), so the checklist shows every
    distinct surface directory rather than collapsing to their shared parent.
    """
    seen: List[str] = []
    for v in values:
        if v and v not in seen:
            seen.append(v)
    return ", ".join(seen)


def _build_platform_summary(key: str, integ, result: WriteResult) -> dict:
    """Build the structured per-surface summary for one integration's result.

    ``key`` is the registry key the runner is iterating (the authoritative
    platform identity); ``integ`` supplies the display name and instruction-file
    config. Reading the key from the caller rather than ``integ.key`` keeps this
    robust to minimal integration objects (e.g. test doubles).

    Groups the WriteResult's FileActions by classified surface and reports, per
    surface, a status (``installed`` when any action left the surface present on
    disk, else ``error``) and a representative path. Carries the detection-gate
    outcome (``result.detected``) so the installer can group undetected
    platforms. Surfaces with no FileAction are omitted (the installer renders
    the fixed canonical order, filling absent surfaces itself).
    """
    instruction_file = None
    config = getattr(integ, "config", None)
    if isinstance(config, dict):
        instruction_file = config.get("instruction_file")

    grouped: dict[str, dict] = {}
    for fa in result.files:
        surface = _classify_surface(fa.path, instruction_file)
        if surface is None:
            continue
        entry = grouped.setdefault(surface, {"roots": [], "present": False})
        entry["roots"].append(_surface_root(fa.path, surface))
        if fa.action in _PRESENT_ACTIONS:
            entry["present"] = True

    surfaces = {
        surface: {
            "status": "installed" if entry["present"] else "error",
            "path": _join_distinct(entry["roots"]),
        }
        for surface, entry in grouped.items()
    }
    return {
        "platform": key,
        "display_name": getattr(integ, "display_name", key),
        "detected": result.detected,
        "surfaces": surfaces,
        "notes": list(result.notes),
    }


def _resolve_integration_keys(arg: str) -> List[str]:
    if arg == "all":
        return list_keys()
    keys = [k.strip() for k in arg.split(",") if k.strip()]
    bad = [k for k in keys if k not in INTEGRATION_REGISTRY]
    if bad:
        print(f"Unknown integrations: {bad}. Known: {list_keys()}", file=sys.stderr)
        raise SystemExit(1)
    return keys


def _manifest_path(target_root: Path) -> Path:
    return target_root / ".nexus-hub" / "install-manifest.json"


def _resolve_target_root(args: argparse.Namespace) -> Path:
    """Resolve the target root (and therefore the manifest path) for a command.

    Precedence:
        1. An explicit ``--target`` always wins (workspace installs pass it).
        2. Otherwise a ``--scope global`` invocation resolves to the user home,
           so the manifest lands under ``~/.nexus-hub/`` regardless of the
           process CWD. This fixes the ``PermissionError [WinError 5]`` traceback
           that fired when the one-line bootstrap was run from an elevated
           ``C:\\Windows\\System32`` prompt and the manifest write resolved to
           ``C:\\Windows\\System32\\.nexus-hub\\``.
        3. Otherwise fall back to the CWD (standalone workspace CLI use, and any
           subcommand that has no ``--scope`` flag, e.g. init / doctor / repair /
           list-installed -- their behavior is unchanged).
    """
    target = getattr(args, "target", None)
    if target:
        return Path(target).expanduser().resolve()
    if getattr(args, "scope", None) == "global":
        return Path.home().resolve()
    return Path.cwd().resolve()


def _template_vars_from_args(args: argparse.Namespace) -> dict:
    """Build the template-var map from --project-name plus repeated --var pairs.

    --var accepts ``KEY=VALUE`` (value may contain ``=``; only the first ``=``
    splits). The installer threads its detected placeholders (PRIMARY_LANGUAGE,
    BUILD_CMD, OS_CONTEXT, ...) through these so the registry renders the same
    instruction body the legacy bash `render_template` produced (DF-001).
    """
    target_root = _resolve_target_root(args)
    vars_map = {"PROJECT_NAME": args.project_name or target_root.name}
    for pair in getattr(args, "var", None) or []:
        key, sep, value = pair.partition("=")
        if not sep:
            print(f"Ignoring malformed --var (expected KEY=VALUE): {pair!r}", file=sys.stderr)
            continue
        vars_map[key.strip()] = value
    return vars_map


def _languages_from_args(args: argparse.Namespace) -> List[str]:
    """Split the optional --languages CSV into a clean list."""
    raw = getattr(args, "languages", None)
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def cmd_list(args: argparse.Namespace) -> int:
    descriptions = [INTEGRATION_REGISTRY[k].describe() for k in list_keys()]
    if args.json:
        print(json.dumps(descriptions, indent=2, default=str))
    else:
        for d in descriptions:
            print(f"{d['key']:<18} {d['display_name']:<35} {d['class']}")
    return 0


def _selection_from_args(args: argparse.Namespace, manifest: InstallManifest, reuse_recorded: bool):
    """Resolve this invocation's selection, or None for a full install.

    `reuse_recorded` is the difference between `install` and `repair`/`upgrade`:
    an install with no selector means FULL (the compatibility default), while a
    repair with no selector must reinstall the scope the user already chose. A
    repair that silently widened to the full catalog would be the most annoying
    possible way to lose a focused install.
    """
    profile = getattr(args, "profile", None)
    modules = list(getattr(args, "modules", None) or [])
    bundles = list(getattr(args, "bundles", None) or [])

    if not profile and not modules and not bundles:
        if reuse_recorded:
            recorded = manifest.selection()
            if recorded:
                return recorded  # a plain dict; InstallContext accepts either
        return None

    from scripts.lib.installer.selection import (
        SelectionRequest,
        available_from_catalog,
        load_catalog,
        resolve,
    )

    catalog = load_catalog(REPO_ROOT / "data" / "bundles.json")
    available = available_from_catalog(catalog, repo_root=REPO_ROOT)
    request = SelectionRequest.from_args(
        profiles=[profile] if profile else [], modules=modules, bundles=bundles
    )
    return resolve(catalog, request, available)


def _selection_payload(selection) -> Optional[dict]:
    """Serialize a plan (or pass through a recorded dict) for the manifest."""
    if selection is None:
        return None
    return selection.to_dict() if hasattr(selection, "to_dict") else dict(selection)


def cmd_install(args: argparse.Namespace) -> int:
    keys = _resolve_integration_keys(args.integrations)
    target_root = _resolve_target_root(args)
    manifest_path = _manifest_path(target_root)
    manifest = InstallManifest.load(manifest_path)
    from scripts.lib.installer.selection import SelectionError

    try:
        selection = _selection_from_args(args, manifest, reuse_recorded=False)
    except SelectionError as exc:
        # Fail before any write. Exit 2 is a bad selector, 3 a bad catalog.
        print(f"[error:selection] {exc}", file=sys.stderr)
        return exc.exit_code
    if selection is not None and not args.quiet:
        payload = _selection_payload(selection)
        resolved = payload["resolved"]
        print(
            f"[selection] {len(resolved['skills'])} skills, "
            f"{len(resolved['commands'])} commands, {len(resolved['agents'])} agents "
            f"({payload['hash'][:19]}...)"
        )
        for warning in payload.get("warnings", []):
            print(f"[selection:warn] {warning}", file=sys.stderr)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope=args.scope,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        manifest=manifest,
        template_vars=_template_vars_from_args(args),
        languages=_languages_from_args(args),
        instruction_only=args.instruction_only,
        verbose=not args.quiet,
        selection=selection,
    )
    # Recorded before the copy loop so a run that fails partway still leaves the
    # scope it was installing, which is what repair and doctor read.
    if not args.dry_run:
        manifest.set_selection(_selection_payload(selection))
    failures = []
    summaries: List[dict] = []
    for key in keys:
        try:
            integ = get(key)
            if not args.quiet:
                print(f"[install:{args.scope}] {integ.display_name}")
            result = integ.install(ctx)
            # v2.3.0 / Phase 4 / T010 -- record the per-file actions for
            # doctor / repair / list-installed. Skipped on dry-run since
            # the manifest is not saved in that case.
            if not args.dry_run:
                manifest.record_actions(key, result.files)
            # v3.14.5 Phase 1 -- capture the structured per-surface summary from
            # the WriteResult directly (not via _render_write_result, which is
            # print-only and suppressed under --quiet), so the installer can
            # render its per-platform checklist even when it runs us quietly.
            summaries.append(_build_platform_summary(key, integ, result))
            _render_write_result(key, result, args.quiet)
        except Exception as exc:  # noqa: BLE001
            print(f"[error:{key}] {exc}", file=sys.stderr)
            failures.append(key)
    # Opt-in structured summary channel (v3.14.5 Phase 1). Written regardless of
    # --quiet and of --dry-run (a dry-run summary reflects what WOULD install).
    summary_path = getattr(args, "summary_json", None)
    if summary_path:
        payload = {"scope": args.scope, "platforms": summaries}
        # v3.16.1 Phase 6.3 -- the installers read this file to render their
        # per-platform checklist, so the selection has to travel with it or the
        # legacy summary would describe a full install that did not happen.
        selection_payload = _selection_payload(selection)
        if selection_payload is not None:
            payload["selection"] = selection_payload
        try:
            Path(summary_path).expanduser().write_text(
                json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
            )
        except OSError as exc:
            print(
                f"[warn] could not write install summary to {summary_path}: {exc}",
                file=sys.stderr,
            )
    if not args.dry_run:
        try:
            manifest.save(manifest_path)
            if not args.quiet:
                print(f"Manifest written to: {manifest_path}")
        except OSError as exc:
            # The manifest is bookkeeping for upgrade / doctor / repair; a write
            # failure (e.g. a read-only or privileged CWD) must not mask an
            # otherwise-successful install nor emit a scary traceback.
            print(
                f"[warn] could not write install manifest to {manifest_path}: {exc}; "
                "install content is unaffected",
                file=sys.stderr,
            )
    elif not args.quiet:
        print("(dry-run: manifest not written)")
    if failures:
        print(f"Failed integrations: {failures}", file=sys.stderr)
        return 2
    return 0


def cmd_teardown(args: argparse.Namespace) -> int:
    target_root = Path(args.target).expanduser().resolve()
    manifest_path = _manifest_path(target_root)
    manifest = InstallManifest.load(manifest_path)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope="workspace",
        overwrite=True,
        dry_run=args.dry_run,
        manifest=manifest,
    )
    keys = args.integrations and _resolve_integration_keys(args.integrations) or manifest.all_keys()
    for key in keys:
        try:
            integ = get(key)
            print(f"[teardown] {integ.display_name}")
            result = integ.teardown(ctx)
            _render_write_result(key, result, quiet=False)
        except KeyError:
            print(f"[skip:{key}] not in registry", file=sys.stderr)
    if not args.dry_run:
        try:
            manifest.save(manifest_path)
        except OSError as exc:
            print(
                f"[warn] could not write install manifest to {manifest_path}: {exc}; "
                "teardown content is unaffected",
                file=sys.stderr,
            )
    return 0


def cmd_print_config(args: argparse.Namespace) -> int:
    """Dump the Markdown readout of what one integration would install.

    Calls ``integration.print_config(ctx)`` against a dry-run context so no
    disk writes occur. Exit codes: 0 success, 1 unknown key.
    """
    try:
        integ = get(args.integration)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    target_root = _resolve_target_root(args)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope=args.scope,
        overwrite=False,
        dry_run=True,
        manifest=InstallManifest(),
        template_vars=_template_vars_from_args(args),
        languages=_languages_from_args(args),
    )
    sys.stdout.write(integ.print_config(ctx))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Run every integration's dry_run() and exit non-zero on drift.

    Walks ``list_keys()`` (or ``--integrations``) and accumulates the
    ``FileAction`` records each ``dry_run`` returns. Exit 0 if every action
    is ``unchanged`` or ``kept``; exit 1 if any action would create / update
    / remove. Always prints a per-integration summary unless ``--quiet``.
    """
    keys = _resolve_integration_keys(args.integrations) if args.integrations else list_keys()
    target_root = _resolve_target_root(args)
    manifest_path = _manifest_path(target_root)
    manifest = InstallManifest.load(manifest_path)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope=args.scope,
        overwrite=False,
        dry_run=True,
        manifest=manifest,
        template_vars={"PROJECT_NAME": args.project_name or target_root.name},
    )
    drift_actions = {"created", "updated", "removed", "not-found"}
    drift_found = False
    for key in keys:
        try:
            integ = get(key)
            result = integ.dry_run(ctx)
        except Exception as exc:  # noqa: BLE001
            print(f"[error:{key}] {exc}", file=sys.stderr)
            drift_found = True
            continue
        kinds = result.actions_by_kind()
        if any(k in drift_actions for k in kinds):
            drift_found = True
        if not args.quiet:
            label = ", ".join(f"{k}:{v}" for k, v in sorted(kinds.items())) or "(empty)"
            print(f"[check:{key}] {integ.display_name} -> {label}")
            for fa in result.files:
                if fa.action in drift_actions:
                    print(f"  [drift] {fa.action:<10} {fa.path}")
    if drift_found:
        if not args.quiet:
            print("drift detected", file=sys.stderr)
        return 1
    if not args.quiet:
        print("no drift; install matches catalog.")
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    """Walk every registered integration and call wire_project_surfaces(ctx).

    Used by `nexus-hub init` to bootstrap project-local surfaces (Cursor's
    .cursor/rules/nexus-hub.mdc, Claude's .claude/settings.json stub, etc.)
    from a *global* install without re-running the full workspace install.
    """
    target_root = _resolve_target_root(args)
    manifest_path = _manifest_path(target_root)
    manifest = InstallManifest.load(manifest_path)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope="workspace",
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        manifest=manifest,
        template_vars={"PROJECT_NAME": args.project_name or target_root.name},
    )
    any_surfaces = False
    for key in list_keys():
        integ = get(key)
        result = integ.wire_project_surfaces(ctx)
        if result is None:
            continue
        any_surfaces = True
        if not args.quiet:
            print(f"[init] {integ.display_name}")
        _render_write_result(key, result, args.quiet)
    if not any_surfaces and not args.quiet:
        print("No integration provides a project-local surface.")
    if not args.dry_run:
        manifest.save(manifest_path)
    return 0


_DIAGNOSTIC_PREFIX = {
    DIAGNOSTIC_OK: "[ok]      ",
    DIAGNOSTIC_MISSING: "[missing] ",
    DIAGNOSTIC_DRIFTED: "[drifted] ",
    DIAGNOSTIC_UNKNOWN: "[unknown] ",
}


def _render_doctor_report(report: DoctorReport, json_mode: bool, quiet: bool) -> None:
    if json_mode:
        payload = {
            "integrations_checked": report.integrations_checked,
            "integrations_unknown": report.integrations_unknown,
            "counts": report.counts(),
            "findings": [
                {
                    "integration": f.integration_key,
                    "path": f.path,
                    "recorded_action": f.recorded_action,
                    "diagnostic": f.diagnostic,
                    "recorded_sha256": f.recorded_sha256,
                    "current_sha256": f.current_sha256,
                    "detail": f.detail,
                }
                for f in report.findings
            ],
        }
        print(json.dumps(payload, indent=2, default=str))
        return
    if quiet:
        return
    counts = report.counts()
    summary = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())) or "(no records)"
    print(f"[doctor] checked {len(report.integrations_checked)} integration(s) -> {summary}")
    for f in report.findings:
        if f.diagnostic == DIAGNOSTIC_OK:
            continue
        prefix = _DIAGNOSTIC_PREFIX.get(f.diagnostic, "[?]")
        detail = f" - {f.detail}" if f.detail else ""
        print(f"  {prefix}{f.integration_key:<14} {f.path}{detail}")
    if report.integrations_unknown:
        print(
            "[doctor] requested but unknown to manifest: "
            + ", ".join(report.integrations_unknown),
            file=sys.stderr,
        )


def cmd_doctor(args: argparse.Namespace) -> int:
    """Diagnose drift / missing managed files against the recorded manifest.

    Exits 0 when everything is `ok` (or `unknown` -- the latter being tree
    summaries that lack a content hash). Exits 1 on any `missing` or
    `drifted` finding so CI can gate on the result.
    """
    target_root = _resolve_target_root(args)
    manifest_path = _manifest_path(target_root)
    if not manifest_path.exists():
        if args.json:
            print(json.dumps({"error": "no manifest", "manifest_path": str(manifest_path)}))
        else:
            print(
                f"[doctor] no manifest at {manifest_path} -- run install first",
                file=sys.stderr,
            )
        return 1
    manifest = InstallManifest.load(manifest_path)
    requested = (
        [k.strip() for k in args.integrations.split(",") if k.strip()]
        if args.integrations
        else None
    )
    report = lifecycle_doctor(manifest, requested)
    _render_doctor_report(report, args.json, args.quiet)
    _report_selector_drift(manifest, args)
    return 1 if report.has_issues() else 0


def _report_selector_drift(manifest: InstallManifest, args: argparse.Namespace) -> None:
    """Report selector drift separately from content drift, and never as an error.

    Selector drift is when the recorded selectors still resolve, but now resolve
    to a DIFFERENT set than when they were recorded, because the catalog changed
    underneath. A skill added to a module the user selected is not corruption and
    must not be reported as such: nothing is damaged, the user simply has a
    choice to make about whether to pull the new skills in.

    Conflating the two would train users to ignore doctor output, because a
    routine catalog update would start reporting their install as broken.
    """
    recorded = manifest.selection()
    if not recorded:
        return
    requested = recorded.get("requested") or {}
    if not any(requested.get(k) for k in ("profile", "modules", "bundles")):
        return
    try:
        from scripts.lib.installer.selection import (
            SelectionRequest,
            available_from_catalog,
            load_catalog,
            resolve,
        )

        catalog = load_catalog(REPO_ROOT / "data" / "bundles.json")
        available = available_from_catalog(catalog, repo_root=REPO_ROOT)
        fresh = resolve(
            catalog,
            SelectionRequest.from_args(
                profiles=[requested["profile"]] if requested.get("profile") else [],
                modules=requested.get("modules") or [],
                bundles=requested.get("bundles") or [],
            ),
            available,
        )
    except Exception as exc:  # noqa: BLE001
        # Advisory only. A resolver problem must not turn `doctor` into a
        # failure about something the user did not ask it to check.
        if not args.quiet:
            print(f"[doctor:selection] could not re-resolve recorded selectors: {exc}")
        return

    if fresh.hash() == recorded.get("hash"):
        return
    was = set(recorded.get("resolved", {}).get("skills", []))
    now = set(fresh.skills)
    added, removed = sorted(now - was), sorted(was - now)
    if args.json:
        print(json.dumps({
            "selector_drift": True,
            "added": added,
            "removed": removed,
            "recorded_hash": recorded.get("hash"),
            "current_hash": fresh.hash(),
        }))
    elif not args.quiet:
        print(
            "[doctor:selection] the recorded selectors now resolve differently "
            "(catalog changed, not content drift)."
        )
        if added:
            print(f"  would add   : {', '.join(added)}")
        if removed:
            print(f"  would remove: {', '.join(removed)}")
        print("  run `repair` to install into the current resolution.")


def cmd_repair(args: argparse.Namespace) -> int:
    """Re-run install for every integration the manifest reports as drifted
    or missing. Files marked `ok` are left untouched (`unchanged` action).
    """
    target_root = _resolve_target_root(args)
    manifest_path = _manifest_path(target_root)
    if not manifest_path.exists():
        print(
            f"[repair] no manifest at {manifest_path} -- run install first",
            file=sys.stderr,
        )
        return 1
    manifest = InstallManifest.load(manifest_path)
    from scripts.lib.installer.selection import SelectionError

    try:
        # reuse_recorded=True: a repair with no selector must restore the scope
        # the user already chose. Widening to the full catalog here would be the
        # most annoying possible way to lose a focused install, and it would
        # happen at exactly the moment the user was trying to fix something.
        selection = _selection_from_args(args, manifest, reuse_recorded=True)
    except SelectionError as exc:
        print(f"[error:selection] {exc}", file=sys.stderr)
        return exc.exit_code
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope=args.scope,
        overwrite=True,
        dry_run=args.dry_run,
        manifest=manifest,
        template_vars={"PROJECT_NAME": args.project_name or target_root.name},
        verbose=not args.quiet,
        selection=selection,
    )
    if not args.dry_run and _selection_payload(selection) != manifest.selection():
        # An explicit selector on repair replaces the recorded request.
        manifest.set_selection(_selection_payload(selection))
    requested = (
        [k.strip() for k in args.integrations.split(",") if k.strip()]
        if args.integrations
        else None
    )
    result = lifecycle_repair(ctx, requested)
    if not args.quiet:
        if not result.files and not result.notes:
            print("[repair] no integrations needed repair")
        else:
            print(f"[repair] {len(result.files)} action(s)")
            for fa in result.files:
                prefix = _ACTION_PREFIX.get(fa.action, "[?]")
                print(f"  {prefix} {fa.action:<10} {fa.path}")
            for note in result.notes:
                print(f"  (note) {note}")
    if not args.dry_run:
        manifest.save(manifest_path)
    return 0


def cmd_list_installed(args: argparse.Namespace) -> int:
    """Enumerate what every integration wrote according to the manifest.

    JSON mode dumps the raw `{integration_key: [action_record, ...]}` map;
    text mode prints one line per recorded file.
    """
    target_root = _resolve_target_root(args)
    manifest_path = _manifest_path(target_root)
    if not manifest_path.exists():
        if args.json:
            print(json.dumps({}, indent=2))
        else:
            print(f"(no manifest at {manifest_path})")
        return 0
    manifest = InstallManifest.load(manifest_path)
    data = lifecycle_list_installed(manifest)
    recorded = manifest.selection()
    if args.json:
        # Nested under a key rather than merged, so an existing consumer that
        # iterates the top level as `{key: actions}` does not suddenly find a
        # "selection" entry among the integration keys.
        payload = {"integrations": data, "selection": recorded} if recorded else data
        print(json.dumps(payload, indent=2, default=str))
        return 0
    if recorded:
        req = recorded.get("requested") or {}
        parts = [f"profile={req['profile']}"] if req.get("profile") else []
        if req.get("modules"):
            parts.append("modules=" + ",".join(req["modules"]))
        if req.get("bundles"):
            parts.append("bundles=" + ",".join(req["bundles"]))
        resolved = recorded.get("resolved", {})
        print(
            f"[selection] {'; '.join(parts) or 'full'} -> "
            f"{len(resolved.get('skills', []))} skills, "
            f"{len(resolved.get('commands', []))} commands, "
            f"{len(resolved.get('agents', []))} agents"
        )
    if not data:
        print("(manifest contains no recorded actions)")
        return 0
    for key in sorted(data):
        records = data[key]
        print(f"[{key}] {len(records)} file(s)")
        for rec in records:
            action = str(rec.get("action", "?"))
            prefix = _ACTION_PREFIX.get(action, "[?]")
            print(f"  {prefix} {action:<10} {rec.get('path', '')}")
    return 0


def _nonempty_dir(p: Path) -> bool:
    """True when `p` is a directory containing at least one entry."""
    try:
        return p.is_dir() and any(p.iterdir())
    except OSError:
        return False


def _file_contains(p: Path, needle: str) -> bool:
    """True when file `p` exists and contains `needle`."""
    try:
        return p.is_file() and needle in p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


# The machine-readable single source shared with scripts/verify_platform_contracts.py
# (its `contract_checks`) and the release freshness guard (its `meta`). This
# function reads the `install_verify` block, so the runtime `[verify]` pass and
# the code-vs-contract guard cannot drift apart.
_CONTRACT_JSON = REPO_ROOT / "docs" / "policy" / "platform-read-contracts.json"


def _resolve_contract_path(spec: str, home: Path, target_root: Path) -> Path:
    """Resolve home, project, and configured OpenClaw workspace path tokens."""
    if spec.startswith("~/"):
        return home / spec[2:]
    if spec.startswith("{project}/"):
        return target_root / spec[len("{project}/"):]
    if spec.startswith("{openclaw_workspace}/"):
        from scripts.lib.integrations.openclaw import _configured_workspace

        workspace = _configured_workspace(home / ".openclaw")
        return workspace / spec[len("{openclaw_workspace}/"):]
    return Path(spec)


def _evaluate_surface(surface: dict, home: Path, target_root: Path) -> tuple:
    """Evaluate one JSON surface check into ``(label, ok_bool)``."""
    label = str(surface.get("label", "?"))
    try:
        path = _resolve_contract_path(
            str(surface.get("path", "")), home, target_root
        )
    except (OSError, ValueError):
        return (label, False)
    kind = surface.get("kind")
    if kind == "nonempty_dir":
        ok = _nonempty_dir(path)
    elif kind == "is_file":
        ok = path.is_file()
    elif kind == "file_contains":
        ok = _file_contains(path, str(surface.get("needle", "")))
    else:
        ok = False
    return (label, ok)


def _verify_checks(home: Path, target_root: Path) -> list:
    """Build the per-platform read-path checks from the machine-readable single
    source (docs/policy/platform-read-contracts.json, `install_verify`).

    Each entry is ``(platform_label, [(surface, ok_bool), ...], remediation_or_None)``.
    Only platforms whose detect path(s) are present are included, so the report
    reflects what the user actually has installed. Reading the same JSON that the
    code-vs-contract guard (scripts/verify_platform_contracts.py) uses keeps the
    two verifiers from drifting apart. Fail-soft: an unreadable/absent JSON yields
    no checks (the advisory verify then reports no detected platforms).
    """
    try:
        data = json.loads(_CONTRACT_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    entries = data.get("install_verify")
    if not isinstance(entries, list):
        return []
    checks: list = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("label") == "OpenClaw":
            from scripts.lib.integrations.openclaw import _openclaw_is_active

            try:
                detected = _openclaw_is_active(home / ".openclaw")
            except (OSError, ValueError):
                detected = True
        else:
            detected = any(
                _resolve_contract_path(str(d), home, target_root).exists()
                for d in entry.get("detect", [])
                if isinstance(d, str)
            )
        if not detected:
            continue
        surfaces = [
            _evaluate_surface(s, home, target_root)
            for s in entry.get("surfaces", [])
            if isinstance(s, dict)
        ]
        checks.append((str(entry.get("label", "?")), surfaces, entry.get("remediation")))
    return checks


def cmd_verify(args: argparse.Namespace) -> int:
    """Post-install per-platform read-path verification (advisory; always exit 0).

    For each detected platform, assert the surfaces it actually reads are populated
    and print PASS / NEEDS-ACTION with a remediation hint. This is what turns a
    silent no-op install (wrong path, or a project-only surface like Antigravity's
    .agents/) into a visible, actionable line. Never fails the install.
    """
    home = Path.home()
    target_root = _resolve_target_root(args)

    # v3.16.1 Phase 7.4 -- report the recorded scope first, so a PASS on a
    # focused install is interpretable. The checks themselves need no change:
    # they assert each read path is POPULATED, not that the whole catalog is
    # present, so an intentional exclusion was never going to be penalized.
    # Stating that here is what stops a future editor from "fixing" verify into
    # a completeness check, which would report every focused install as broken.
    try:
        recorded = InstallManifest.load(_manifest_path(target_root)).selection()
    except Exception:  # noqa: BLE001
        recorded = None
    if recorded and not args.quiet:
        req = recorded.get("requested") or {}
        parts = [f"profile={req['profile']}"] if req.get("profile") else []
        if req.get("modules"):
            parts.append("modules=" + ",".join(req["modules"]))
        if req.get("bundles"):
            parts.append("bundles=" + ",".join(req["bundles"]))
        resolved = recorded.get("resolved", {})
        print(
            f"[verify] focused install ({'; '.join(parts) or 'full'}): "
            f"{len(resolved.get('skills', []))} skills, "
            f"{len(resolved.get('commands', []))} commands, "
            f"{len(resolved.get('agents', []))} agents. "
            "Read-path checks below assert each surface is populated, not that "
            "the full catalog is present."
        )

    checks = _verify_checks(home, target_root)
    if not checks:
        if not args.quiet:
            print("[verify] no supported platform config dirs detected under home.")
        return 0
    any_action = False
    for platform, surfaces, remediation in checks:
        ok = all(s_ok for _, s_ok in surfaces)
        if not ok:
            any_action = True
        if args.quiet and ok:
            continue
        status = "PASS        " if ok else "NEEDS-ACTION"
        detail = ", ".join(f"{name}:{'ok' if s_ok else 'MISSING'}" for name, s_ok in surfaces)
        print(f"[verify] {status} {platform} -- {detail}")
        if not ok and remediation:
            print(f"             -> {remediation}")
    # Host interpreter check (v4.3.0). Every surface above can be present and
    # correct while the hooks are still inert, because the HOST launches them as
    # `bash <script>` and Nexus-Hub does not control that resolution. A Windows
    # host whose PATH `bash` is the WSL launcher stub exits non-zero with an empty
    # stderr, so the failure is silent at exactly the moment it matters. Reported
    # here rather than raised: an unusable interpreter is a host condition the
    # user fixes on PATH, not an install error, and it must never fail an install
    # that otherwise delivered every file correctly.
    try:
        from scripts.lib.integrations._interpreters import check_all as _check_interpreters

        for status in _check_interpreters():
            if status.usable:
                if not args.quiet:
                    print(f"[verify] PASS         interpreter {status.name} -- {status.resolved}")
                continue
            any_action = True
            print(f"[verify] NEEDS-ACTION interpreter {status.name} -- cannot run a script")
            print(f"             -> {status.detail}")
    except Exception as exc:  # never let a diagnostic break an otherwise good install
        if not args.quiet:
            print(f"[verify] interpreter check skipped: {exc}")

    if not args.quiet:
        print(
            "[verify] all detected platforms surface the catalog."
            if not any_action
            else "[verify] some platforms need action (see the -> hints above)."
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexus-hub-integrations")
    sub = parser.add_subparsers(dest="cmd", required=True)

    _SELECTION_HELP = (
        "Install-selection selector (v3.16.1). Repeatable and comma-separated "
        "forms are equivalent. No selector installs the full catalog."
    )

    def _add_selection_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--profile", help=f"Profile id. {_SELECTION_HELP}")
        parser.add_argument(
            "--modules", action="append", default=[],
            help=f"Capability module id(s). {_SELECTION_HELP}",
        )
        parser.add_argument(
            "--bundles", action="append", default=[],
            help=f"Role bundle id(s). {_SELECTION_HELP}",
        )

    p_list = sub.add_parser("list", help="List registered integrations.")
    p_list.add_argument("--json", action="store_true", help="Emit JSON output.")
    p_list.set_defaults(func=cmd_list)

    p_install = sub.add_parser("install", help="Install one or more integrations.")
    p_install.add_argument("--scope", choices=["global", "workspace"], default="workspace")
    p_install.add_argument("--target", help="Workspace root. Defaults to CWD for workspace scope; for global scope defaults to the user home (~/.nexus-hub lands under it).")
    p_install.add_argument("--integrations", required=True, help="Comma-separated keys, or 'all'.")
    p_install.add_argument("--overwrite", action="store_true")
    p_install.add_argument("--dry-run", action="store_true")
    _add_selection_args(p_install)
    p_install.add_argument("--project-name", help="Template token PROJECT_NAME.")
    p_install.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Instruction-template placeholder (repeatable). The installer threads detected values (PRIMARY_LANGUAGE, BUILD_CMD, OS_CONTEXT, ...) this way.",
    )
    p_install.add_argument(
        "--languages",
        help="Comma-separated language list; appends the matching coding-snippet fragment to the instruction file.",
    )
    p_install.add_argument(
        "--instruction-only",
        action="store_true",
        help="Render only the instruction file; skip the catalog tree mirror (the installer copies catalog/ via its own block).",
    )
    p_install.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational output. The installer uses this so it can print its own per-platform headers; errors still go to stderr.",
    )
    p_install.add_argument(
        "--summary-json",
        metavar="PATH",
        help="Write a structured per-platform, per-surface install summary (JSON) to PATH. Populated regardless of --quiet; the installer consumes it to render the per-platform checklist and to group undetected platforms.",
    )
    p_install.set_defaults(func=cmd_install)

    p_print = sub.add_parser(
        "print-config",
        help="Dump the Markdown readout of what one integration would install.",
    )
    p_print.add_argument("integration", help="Integration key (e.g., claude).")
    p_print.add_argument("--scope", choices=["global", "workspace"], default="workspace")
    p_print.add_argument("--target", help="Workspace root (defaults to CWD).")
    p_print.add_argument("--project-name", help="Template token PROJECT_NAME.")
    p_print.add_argument(
        "--var",
        action="append",
        metavar="KEY=VALUE",
        help="Instruction-template placeholder (repeatable).",
    )
    p_print.add_argument(
        "--languages",
        help="Comma-separated language list for coding-snippet append.",
    )
    p_print.set_defaults(func=cmd_print_config)

    p_check = sub.add_parser(
        "check",
        help="Dry-run every integration; exit non-zero if anything would change.",
    )
    p_check.add_argument("--scope", choices=["global", "workspace"], default="workspace")
    p_check.add_argument("--target", help="Workspace root (defaults to CWD).")
    p_check.add_argument("--integrations", help="Comma-separated keys, or 'all'. Default: all.")
    p_check.add_argument("--project-name", help="Template token PROJECT_NAME.")
    p_check.add_argument("--quiet", action="store_true")
    p_check.set_defaults(func=cmd_check)

    p_init = sub.add_parser(
        "init",
        help="Bootstrap project-local surfaces (Cursor rules, Claude settings stub, ...).",
    )
    p_init.add_argument(
        "--target",
        help="Project root (defaults to CWD).",
    )
    p_init.add_argument("--overwrite", action="store_true")
    p_init.add_argument("--dry-run", action="store_true")
    p_init.add_argument("--project-name", help="Template token PROJECT_NAME.")
    p_init.add_argument("--quiet", action="store_true")
    p_init.set_defaults(func=cmd_init)

    p_teardown = sub.add_parser("teardown", help="Remove integration files based on the manifest.")
    p_teardown.add_argument("--target", required=True)
    p_teardown.add_argument("--integrations", help="Comma-separated keys; default: all tracked.")
    p_teardown.add_argument("--dry-run", action="store_true")
    p_teardown.set_defaults(func=cmd_teardown)

    # v2.3.0 / Phase 4 / T010 lifecycle subcommands.
    p_doctor = sub.add_parser(
        "doctor",
        help="Diagnose drift / missing managed files against the install manifest.",
    )
    p_doctor.add_argument("--target", help="Workspace root (defaults to CWD).")
    p_doctor.add_argument(
        "--integrations",
        help="Comma-separated keys; default: every integration in the manifest.",
    )
    p_doctor.add_argument("--json", action="store_true", help="Emit JSON output.")
    p_doctor.add_argument("--quiet", action="store_true")
    p_doctor.set_defaults(func=cmd_doctor)

    p_repair = sub.add_parser(
        "repair",
        help="Re-install integrations that doctor reports as drifted or missing.",
    )
    p_repair.add_argument("--scope", choices=["global", "workspace"], default="workspace")
    p_repair.add_argument("--target", help="Workspace root (defaults to CWD).")
    p_repair.add_argument(
        "--integrations",
        help="Comma-separated keys; default: every integration in the manifest.",
    )
    p_repair.add_argument("--project-name", help="Template token PROJECT_NAME.")
    p_repair.add_argument("--dry-run", action="store_true")
    _add_selection_args(p_repair)
    p_repair.add_argument("--quiet", action="store_true")
    p_repair.set_defaults(func=cmd_repair)

    p_list_installed = sub.add_parser(
        "list-installed",
        help="Enumerate the files recorded in the install manifest.",
    )
    p_list_installed.add_argument("--target", help="Workspace root (defaults to CWD).")
    p_list_installed.add_argument("--json", action="store_true", help="Emit JSON output.")
    p_list_installed.set_defaults(func=cmd_list_installed)

    p_verify = sub.add_parser(
        "verify",
        help="Post-install per-platform read-path check: PASS / NEEDS-ACTION (advisory).",
    )
    p_verify.add_argument("--target", help="Project root for the .agents/ project-surface check (defaults to CWD).")
    p_verify.add_argument("--quiet", action="store_true", help="Print only NEEDS-ACTION lines.")
    p_verify.set_defaults(func=cmd_verify)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
