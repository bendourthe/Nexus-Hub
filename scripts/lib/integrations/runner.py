"""Runner CLI for Nexus-Hub integrations.

Invoked from `scripts/installer.sh` and `scripts/installer.ps1` (and usable
standalone). Walks the integration registry and dispatches install / list /
teardown actions per platform.

Usage:
    python scripts/lib/integrations/runner.py list
    python scripts/lib/integrations/runner.py install \\
        --scope workspace --target /path/to/project \\
        --integrations claude,gemini,windsurf
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
            print(f"[install:{args.scope}] {integ.display_name}")
            integ.install(ctx)
        except Exception as exc:  # noqa: BLE001
            print(f"[error:{key}] {exc}", file=sys.stderr)
            failures.append(key)
    if not args.dry_run:
        manifest.save(manifest_path)
        print(f"Manifest written to: {manifest_path}")
    else:
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
            integ.teardown(ctx)
        except KeyError:
            print(f"[skip:{key}] not in registry", file=sys.stderr)
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
    p_install.set_defaults(func=cmd_install)

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
