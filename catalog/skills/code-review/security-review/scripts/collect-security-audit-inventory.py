#!/usr/bin/env python3
"""Collect bounded metadata-only application-surface receipts without routing."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import shlex
import stat
import sys
import time
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(_HERE))
import _safe_artifact as safe
import _strict_json as strict
import _target_manifest as target_identity

_RESOLVERS = (_HERE.parents[2] / "workflow/agent-presets/scripts/resolve-security-audit-routing.py",
              _HERE.parents[1] / "agent-presets/scripts/resolve-security-audit-routing.py")
for _resolver in _RESOLVERS:
    if _resolver.is_file():
        _spec = importlib.util.spec_from_file_location("_security_audit_policy", _resolver)
        assert _spec and _spec.loader
        policy = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(policy)
        break
else:
    raise ImportError("required agent-presets bundle unavailable")


class InventoryStop(ValueError):
    """Abort observation with a stable metadata-only reason."""


def _stamp(info: os.stat_result) -> tuple[int, ...]:
    return (*safe._identity(info), info.st_size, info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def _matches(name: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name.lower(), pattern.lower()) for pattern in patterns)


def _container_or_binary(prefix: bytes) -> bool:
    return b"\0" in prefix or prefix.startswith((b"MZ", b"\x7fELF", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa\xce",
                                               b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe",
                                               b"\0asm", b"PK\x03\x04", b"PK\x05\x06", b"Rar!", b"7z\xbc\xaf\x27\x1c"))


def _unsupported_shebang(payload: bytes, suffix: str) -> bool:
    if not payload.startswith(b"#!"):
        return False
    try:
        line = payload.split(b"\n", 1)[0]
        if len(line) > 128:
            return True
        words = shlex.split(line[2:].decode("ascii"))
        if words and Path(words[0]).name == "env":
            words = words[1:]
        if len(words) != 1:
            return True
        interpreter = Path(words[0]).name
        return not ((bool(re.fullmatch(r"python(?:3(?:\.\d+)?)?", interpreter)) and suffix in {".py", ".pyi"}) or
                    (interpreter in {"node", "nodejs", "bun", "deno"} and suffix in {".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}))
    except (ValueError, UnicodeError):
        return True


def collect(root: Path, manifest: Any) -> dict[str, Any]:
    """Observe positive/negative predicates; never choose owners or run tools."""
    manifest = policy.validate_manifest(manifest)
    files, budgets = manifest["files"], manifest["budgets"]
    checks = {s["id"]: {"surface": s["id"], "result": "UNKNOWN", "evidence": []} for s in manifest["surfaces"]}
    counts = {"files": 0, "bytes": 0, "existence_only": 0}
    reasons: set[str] = set()
    started = time.monotonic()
    leaves, directories = [], []
    aliases: dict[str, str] = {}
    expressions = {p["id"]: re.compile(r"(?<![A-Za-z0-9_])(?:" + "|".join(re.escape(v) for v in p["values"]) + r")(?![A-Za-z0-9_])", re.IGNORECASE)
                   for s in manifest["surfaces"] for p in s["predicates"] if p["operation"] == "token"}
    root_fingerprint = hashlib.sha256(str(Path(os.path.abspath(root))).encode()).hexdigest()

    def deadline() -> None:
        if time.monotonic() - started > budgets["seconds"]:
            raise InventoryStop("INVENTORY_TRUNCATED")

    def walk_error(_error: OSError) -> None:
        raise InventoryStop("UNSAFE_ARTIFACT")

    try:
        root = safe.assert_no_reparse_in_chain(root, root)
        with safe._directory_guard(root):
            for directory, subdirs, filenames in os.walk(root, followlinks=False, onerror=walk_error):
                deadline()
                here = Path(directory)
                safe.assert_no_reparse_in_chain(root, here)
                directories.append((here, _stamp(here.lstat())))
                if len(here.relative_to(root).parts) > budgets["depth"]:
                    raise InventoryStop("INVENTORY_TRUNCATED")
                subdirs[:] = sorted(name for name in subdirs if name not in files["ignored_directories"])
                if any(safe.is_link_like(here / name) for name in subdirs):
                    raise InventoryStop("UNSAFE_ARTIFACT")
                for name in sorted(filenames):
                    deadline()
                    path = here / name
                    identity = target_identity.canonical_path_identity(path.relative_to(root))
                    previous = aliases.setdefault(identity["normalization_key"], identity["display"])
                    if previous != identity["display"]:
                        raise InventoryStop("UNSAFE_ARTIFACT")
                    info = path.lstat()
                    if safe.is_link_like(path) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                        raise InventoryStop("UNSAFE_ARTIFACT")
                    leaves.append((path, _stamp(info)))
                    counts["files"] += 1
                    if counts["files"] > budgets["files"] or info.st_size > budgets["file_bytes"]:
                        raise InventoryStop("INVENTORY_TRUNCATED")
                    existence = _matches(name, files["credential_names"])
                    readable = path.suffix.lower() in files["read_extensions"] or _matches(name, files["read_names"])
                    payload, text = b"", ""
                    to_read = 0 if existence else (info.st_size if readable else min(info.st_size, 64))
                    if counts["bytes"] + to_read > budgets["total_bytes"]:
                        raise InventoryStop("INVENTORY_TRUNCATED")
                    if existence:
                        counts["existence_only"] += 1
                    elif readable:
                        payload = safe.open_contained_bytes(root, path, min(budgets["file_bytes"], budgets["total_bytes"] - counts["bytes"]))
                        counts["bytes"] += len(payload)
                        if _container_or_binary(payload[:64]) or _unsupported_shebang(payload, path.suffix.lower()):
                            reasons.add("UNSUPPORTED_FILETYPE")
                            if counts["bytes"] > budgets["total_bytes"]:
                                raise InventoryStop("INVENTORY_TRUNCATED")
                            continue
                        try:
                            text = payload.decode("utf-8-sig", errors="strict")
                        except UnicodeError:
                            raise InventoryStop("UNCLASSIFIED_FILETYPE") from None
                    else:
                        prefix = safe.peek_contained_bytes(root, path, budgets["file_bytes"], min(64, budgets["total_bytes"] - counts["bytes"]))
                        counts["bytes"] += len(prefix)
                        executable = bool(info.st_mode & 0o111) if os.name != "nt" else path.suffix.lower() in {".exe", ".com", ".bat", ".cmd", ".ps1"}
                        if executable or _container_or_binary(prefix) or prefix.startswith(b"#!") or path.suffix.lower() in files["source_extensions"]:
                            reasons.add("UNSUPPORTED_FILETYPE")
                        else:
                            reasons.add("UNCLASSIFIED_FILETYPE")
                        if counts["bytes"] > budgets["total_bytes"]:
                            raise InventoryStop("INVENTORY_TRUNCATED")
                        continue
                    if counts["bytes"] > budgets["total_bytes"]:
                        raise InventoryStop("INVENTORY_TRUNCATED")
                    deadline()
                    source_lines = text.splitlines()
                    for surface in manifest["surfaces"]:
                        for predicate in surface["predicates"]:
                            deadline()
                            operation = predicate["operation"]
                            line = None
                            if (operation == "source" and (readable or existence)) or (operation == "filename" and _matches(name, predicate["values"])):
                                line = 0
                            elif operation == "token" and not existence:
                                for number, source_line in enumerate(source_lines, 1):
                                    if number % 128 == 0:
                                        deadline()
                                    if expressions[predicate["id"]].search(source_line):
                                        line = number
                                        break
                            if line is not None:
                                checks[surface["id"]]["evidence"].append({
                                    "path": identity, "predicate": predicate["id"], "line": line,
                                    "file_identity_digest": policy.digest(list(safe._identity(info))),
                                    "content_digest": None if existence else hashlib.sha256(payload).hexdigest(),
                                    "existence_only": existence,
                                })
                    deadline()
            for path, stamp in [*directories, *leaves]:
                deadline()
                safe.assert_no_reparse_in_chain(root, root if path == root else path.parent)
                if safe.is_link_like(path) or _stamp(path.lstat()) != stamp:
                    raise InventoryStop("INVENTORY_CHANGED")
            deadline()
    except InventoryStop as exc:
        reasons.add(str(exc))
    except safe.UnsafeArtifactError as exc:
        reasons.add("INVENTORY_TRUNCATED" if exc.code == "artifact_too_large" else "UNSAFE_ARTIFACT")
    except (target_identity.TargetManifestError, OSError, UnicodeError):
        reasons.add("UNSAFE_ARTIFACT")

    def result() -> dict[str, Any]:
        for check in checks.values():
            check["result"] = "MATCH" if check["evidence"] else ("UNKNOWN" if reasons else "NEGATIVE")
        value = {"schema_version": 1, "manifest_digest": policy.digest(manifest),
                 "root_fingerprint": root_fingerprint, "complete": not reasons,
                 "reason_codes": sorted(reasons), "counters": counts,
                 "checks": [checks[key] for key in sorted(checks)]}
        value["inventory_digest"] = policy.digest(value)
        return value

    output = result()
    try:
        strict.loads(json.dumps(output))
    except strict.StrictJSONError:
        reasons.add("INVENTORY_TRUNCATED")
        for check in checks.values():
            check["evidence"] = []
        output = result()
    return output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        output = collect(args.root, strict.load_path(args.manifest))
    except policy.RoutingError as exc:
        print(json.dumps({"complete": False, "reason_codes": [str(exc)]}))
        return 2
    except (strict.StrictJSONError, TypeError, ValueError, KeyError, OSError):
        print(json.dumps({"complete": False, "reason_codes": ["INVENTORY_INVALID"]}))
        return 2
    print(json.dumps(output, sort_keys=True))
    return 0 if output["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
