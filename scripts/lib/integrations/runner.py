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
import sys
from pathlib import Path
from typing import List

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


def cmd_install(args: argparse.Namespace) -> int:
    keys = _resolve_integration_keys(args.integrations)
    target_root = _resolve_target_root(args)
    manifest_path = _manifest_path(target_root)
    manifest = InstallManifest.load(manifest_path)
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
    )
    failures = []
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
            _render_write_result(key, result, args.quiet)
        except Exception as exc:  # noqa: BLE001
            print(f"[error:{key}] {exc}", file=sys.stderr)
            failures.append(key)
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
        print(f"  {prefix}{f.integration_key:<14} {f.path}")
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
    return 1 if report.has_issues() else 0


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
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope=args.scope,
        overwrite=True,
        dry_run=args.dry_run,
        manifest=manifest,
        template_vars={"PROJECT_NAME": args.project_name or target_root.name},
    )
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
    if args.json:
        print(json.dumps(data, indent=2, default=str))
        return 0
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


def _verify_checks(home: Path, target_root: Path) -> list:
    """Build the per-platform read-path checks (v3.11.0 Phase 7.4).

    Each entry is ``(platform_label, [(surface, ok_bool), ...], remediation_or_None)``.
    Only platforms whose config dir is present are included, so the report reflects
    what the user actually has installed. Asserts the surfaces the platform actually
    READS (per docs/policy/platform-read-contracts.md), not what the installer wrote.
    """
    checks: list = []
    # Claude
    d = home / ".claude"
    if d.exists():
        checks.append(("Claude", [
            ("commands", _nonempty_dir(d / "commands")),
            ("skills", _nonempty_dir(d / "skills")),
            ("CLAUDE.md SKILL_INDEX", _file_contains(d / "CLAUDE.md", "Skill Index")),
        ], "re-run the installer (Claude block)"))
    # Codex / new ChatGPT desktop app - flattened skills (~/.codex/skills +
    # ~/.agents/skills), legacy prompts, and the AGENTS.md SKILL_INDEX.
    d = home / ".codex"
    if d.exists():
        checks.append(("Codex / ChatGPT", [
            ("skills", _nonempty_dir(d / "skills")),
            ("~/.agents/skills", _nonempty_dir(home / ".agents" / "skills")),
            ("prompts", _nonempty_dir(d / "prompts")),
            ("AGENTS.md SKILL_INDEX", _file_contains(d / "AGENTS.md", "Skill Index")),
        ], "re-run the installer with --platforms codex"))
    # Gemini IDE (full mirror as of v3.11.0)
    d = home / ".gemini"
    if d.exists():
        checks.append(("Gemini IDE", [
            ("skills", _nonempty_dir(d / "skills")),
            ("workflows", _nonempty_dir(d / "workflows")),
            ("GEMINI.md", (d / "GEMINI.md").is_file()),
        ], "re-run the installer with --platforms gemini"))
    # Antigravity 2.0 - IDE global (~/.gemini/config) + CLI (~/.gemini/antigravity-cli)
    # + the project .agents/ surface. Detected on our own write targets.
    cfg = home / ".gemini" / "config"
    cli = home / ".gemini" / "antigravity-cli"
    if cfg.exists() or cli.exists():
        checks.append(("Antigravity 2.0 IDE (global)", [
            ("skills", _nonempty_dir(cfg / "skills")),
            ("global_workflows", _nonempty_dir(cfg / "global_workflows")),
            ("GEMINI.md", (home / ".gemini" / "GEMINI.md").is_file()),
        ], "re-run the installer with --platforms antigravity2"))
        checks.append(("Antigravity 2.0 CLI (agy)", [
            ("skills", _nonempty_dir(cli / "skills")),
        ], "re-run the installer with --platforms antigravity2"))
        checks.append(("Antigravity 2.0 (this project .agents/)", [
            ("workflows", _nonempty_dir(target_root / ".agents" / "workflows")),
        ], "run `nexus-hub init` in this project for project-scoped .agents/ workflows"))
    # Cursor - global slash surface
    d = home / ".cursor"
    if d.exists():
        checks.append(("Cursor", [
            ("commands", _nonempty_dir(d / "commands")),
        ], "re-run the installer with --platforms cursor"))
    # OpenCode
    d = home / ".opencode"
    if d.exists():
        checks.append(("OpenCode", [
            ("skills", _nonempty_dir(d / "skills")),
            ("AGENTS.md", (d / "AGENTS.md").is_file()),
        ], "re-run the installer with --platforms opencode"))
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

    p_list = sub.add_parser("list", help="List registered integrations.")
    p_list.add_argument("--json", action="store_true", help="Emit JSON output.")
    p_list.set_defaults(func=cmd_list)

    p_install = sub.add_parser("install", help="Install one or more integrations.")
    p_install.add_argument("--scope", choices=["global", "workspace"], default="workspace")
    p_install.add_argument("--target", help="Workspace root. Defaults to CWD for workspace scope; for global scope defaults to the user home (~/.nexus-hub lands under it).")
    p_install.add_argument("--integrations", required=True, help="Comma-separated keys, or 'all'.")
    p_install.add_argument("--overwrite", action="store_true")
    p_install.add_argument("--dry-run", action="store_true")
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
