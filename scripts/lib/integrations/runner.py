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
    target_root = Path(args.target).expanduser().resolve() if args.target else Path.cwd().resolve()
    manifest_path = _manifest_path(target_root)
    manifest = InstallManifest.load(manifest_path)
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope=args.scope,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        manifest=manifest,
        template_vars={"PROJECT_NAME": args.project_name or target_root.name},
    )
    failures = []
    for key in keys:
        try:
            integ = get(key)
            if not args.quiet:
                print(f"[install:{args.scope}] {integ.display_name}")
            result = integ.install(ctx)
            _render_write_result(key, result, args.quiet)
        except Exception as exc:  # noqa: BLE001
            print(f"[error:{key}] {exc}", file=sys.stderr)
            failures.append(key)
    if not args.dry_run:
        manifest.save(manifest_path)
        if not args.quiet:
            print(f"Manifest written to: {manifest_path}")
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
        manifest.save(manifest_path)
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
    target_root = Path(args.target).expanduser().resolve() if args.target else Path.cwd().resolve()
    ctx = InstallContext(
        repo_root=REPO_ROOT,
        target_root=target_root,
        scope=args.scope,
        overwrite=False,
        dry_run=True,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": args.project_name or target_root.name},
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
    target_root = Path(args.target).expanduser().resolve() if args.target else Path.cwd().resolve()
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
    target_root = Path(args.target).expanduser().resolve() if args.target else Path.cwd().resolve()
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexus-hub-integrations")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List registered integrations.")
    p_list.add_argument("--json", action="store_true", help="Emit JSON output.")
    p_list.set_defaults(func=cmd_list)

    p_install = sub.add_parser("install", help="Install one or more integrations.")
    p_install.add_argument("--scope", choices=["global", "workspace"], default="workspace")
    p_install.add_argument("--target", help="Workspace root (defaults to CWD for workspace scope; ignored for global).")
    p_install.add_argument("--integrations", required=True, help="Comma-separated keys, or 'all'.")
    p_install.add_argument("--overwrite", action="store_true")
    p_install.add_argument("--dry-run", action="store_true")
    p_install.add_argument("--project-name", help="Template token PROJECT_NAME.")
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

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
