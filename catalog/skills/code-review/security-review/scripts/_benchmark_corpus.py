"""Inert corpus validation and answer-separated owned source projections."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import _audit_envelope as audit
import _safe_artifact as safe
import _strict_json

ANSWER_SCHEMA = "nexus.application-audit-answers/v1"
MAP_SCHEMA = "nexus.application-audit-projection-map/v1"
LIMIT = 65536


def require(ok: bool) -> None:
    if not ok:
        raise ValueError("BENCHMARK_CORPUS_INVALID")


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def load(root: Path, path: Path) -> dict:
    root, path = filesystem_path(root), filesystem_path(path)
    return _strict_json.loads(
        safe.open_contained_bytes(root, path, _strict_json.MAX_BYTES)
    )


def filesystem_path(path: Path) -> Path:
    """Preserve physical containment while supporting long Windows ledger names."""
    absolute = str(path.absolute())
    if os.name == "nt" and not absolute.startswith("\\\\?\\"):
        absolute = (
            "\\\\?\\UNC\\" + absolute[2:]
            if absolute.startswith("\\\\")
            else "\\\\?\\" + absolute
        )
    return Path(absolute)


def neutral_path(value: object, extension: str | None = None) -> str:
    require(
        isinstance(value, str)
        and re.fullmatch(r"unit_[0-9a-f]{16,32}\.(py|ts)", value) is not None
    )
    require(extension is None or value.endswith("." + extension))
    return value


def validate_answers(value: dict) -> None:
    require(
        isinstance(value, dict)
        and set(value)
        == {
            "schema",
            "answer_canary",
            "seed_count",
            "benign_count",
            "seeds",
            "source_manifest",
        }
    )
    require(
        value["schema"] == ANSWER_SCHEMA
        and type(value["seed_count"]) is int
        and value["seed_count"] == 16
        and type(value["benign_count"]) is int
        and value["benign_count"] == 16
    )
    require(
        isinstance(value["answer_canary"], str)
        and re.fullmatch(r"ANSWER_ONLY_[0-9a-f]{48}", value["answer_canary"])
        is not None
    )
    require(isinstance(value["seeds"], list) and len(value["seeds"]) == 16)
    keys, identities, paths, holdouts = set(), set(), set(), []
    for seed in value["seeds"]:
        require(
            isinstance(seed, dict)
            and set(seed)
            == {
                "id",
                "vulnerability_kind",
                "language",
                "surface",
                "owner",
                "severity",
                "release_blocking",
                "path",
                "region",
                "benign_path",
                "source_to_sink",
                "holdout",
                "remediation_oracle",
            }
        )
        require(
            isinstance(seed["id"], str)
            and re.fullmatch(r"seed-(0[1-9]|1[0-6])", seed["id"]) is not None
            and seed["id"] not in identities
        )
        identities.add(seed["id"])
        require(
            seed["language"] in {"python", "typescript"}
            and seed["vulnerability_kind"] in audit.KINDS
        )
        key = (seed["language"], seed["vulnerability_kind"])
        require(key not in keys)
        keys.add(key)
        require(
            seed["surface"]
            in {
                "application",
                "authentication",
                "api",
                "advanced-web",
                "dependency",
                "cryptography",
                "business-logic",
                "cloud-iac",
                "ai-agent",
            }
        )
        require(
            isinstance(seed["owner"], str)
            and re.fullmatch(r"[a-z][a-z-]{1,80}", seed["owner"]) is not None
        )
        require(
            seed["severity"] in {"critical", "high", "medium", "low", "info"}
            and type(seed["release_blocking"]) is bool
        )
        require(
            seed["severity"] not in {"critical", "high"} or seed["release_blocking"]
        )
        require(type(seed["holdout"]) is bool)
        if seed["holdout"]:
            holdouts.append(
                (
                    seed["language"],
                    "blocking" if seed["release_blocking"] else seed["severity"],
                )
            )
        for field in ("path", "benign_path"):
            path = neutral_path(
                seed[field], "py" if seed["language"] == "python" else "ts"
            )
            require(path not in paths)
            paths.add(path)
        region = seed["region"]
        require(
            isinstance(region, dict)
            and set(region) == {"start_line", "end_line"}
            and type(region["start_line"]) is int
            and type(region["end_line"]) is int
            and 1 <= region["start_line"] <= region["end_line"] <= 1000
        )
        chain = seed["source_to_sink"]
        require(
            chain
            == (
                None
                if seed["vulnerability_kind"]
                in {"insecure-session-cookie", "verbose-error-disclosure"}
                else {"source": "receive", "sink": "handle"}
            )
        )
        oracle = seed["remediation_oracle"]
        require(
            isinstance(oracle, dict)
            and set(oracle) == {"type", "required_text", "forbidden_text"}
            and oracle["type"] == "static-only"
        )
        require(
            all(
                isinstance(oracle[k], str) and 0 < len(oracle[k]) < 500
                for k in ("required_text", "forbidden_text")
            )
        )
    require(
        set(holdouts)
        == {
            (lang, severity)
            for lang in ("python", "typescript")
            for severity in ("blocking", "medium")
        }
        and len(holdouts) == 4
    )
    require(
        isinstance(value["source_manifest"], list)
        and len(value["source_manifest"]) == 32
    )
    manifest_paths = set()
    for entry in value["source_manifest"]:
        require(isinstance(entry, dict) and set(entry) == {"path", "digest", "bytes"})
        neutral_path(entry["path"])
        require(
            entry["path"] not in manifest_paths
            and audit.is_digest(entry["digest"])
            and type(entry["bytes"]) is int
            and 0 < entry["bytes"] <= LIMIT
        )
        manifest_paths.add(entry["path"])
    require(manifest_paths == paths)


def inert_source(name: str, payload: bytes) -> None:
    """Inspect syntax only; never import, compile for execution, or call a fixture."""
    text = payload.decode("utf-8", errors="strict")
    require("ANSWER_ONLY_" not in text and "\x00" not in text)
    require(
        re.search(r"https?://|\b(?:eval|exec|__import__|subprocess|require)\s*\(", text)
        is None
    )
    if name.endswith(".py"):
        tree = ast.parse(text)
        require(
            len(tree.body) == 2
            and all(isinstance(n, ast.FunctionDef) for n in tree.body)
        )
        require({n.name for n in tree.body} == {"receive", "handle"})
        for node in tree.body:
            require(
                not node.decorator_list
                and not node.args.defaults
                and not any(node.args.kw_defaults)
                and node.returns is None
            )
            require(not getattr(node, "type_params", []))
            require(
                all(
                    a is None or a.annotation is None
                    for a in [
                        *node.args.posonlyargs,
                        *node.args.args,
                        *node.args.kwonlyargs,
                        node.args.vararg,
                        node.args.kwarg,
                    ]
                )
            )
        require(
            not any(
                isinstance(
                    n,
                    (
                        ast.Import,
                        ast.ImportFrom,
                        ast.Global,
                        ast.Nonlocal,
                        ast.ClassDef,
                    ),
                )
                for n in ast.walk(tree)
            )
        )
    else:
        # The bounded corpus grammar permits only these two function declarations
        # at module scope. Strip quoted literals before counting nested braces.
        stripped = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', text)
        require(not any(token in stripped for token in ("/", "`", "\\")))
        names = []
        remaining = stripped.strip()
        while remaining:
            match = re.match(
                r"function (receive|handle)\([^{};=]*\): any\s*\{", remaining
            )
            require(match is not None)
            names.append(match.group(1))
            depth = 1
            position = match.end()
            while position < len(remaining) and depth:
                depth += (remaining[position] == "{") - (remaining[position] == "}")
                position += 1
            require(depth == 0)
            remaining = remaining[position:].strip()
        require(names == ["receive", "handle"])


def snapshot(source: Path, answers: dict) -> list[dict]:
    validate_answers(answers)
    safe.assert_no_reparse_in_chain(source, source)
    expected = {e["path"]: e for e in answers["source_manifest"]}
    with safe._directory_guard(source):
        require({p.name for p in source.iterdir()} == set(expected))
        result = []
        for name in sorted(expected):
            path = source / name
            info = path.lstat()
            require(
                stat.S_ISREG(info.st_mode)
                and (os.name == "nt" or not info.st_mode & 0o111)
            )
            payload = safe.open_contained_bytes(source, path, LIMIT)
            inert_source(name, payload)
            result.append(
                {
                    "path": name,
                    "digest": hashlib.sha256(payload).hexdigest(),
                    "bytes": len(payload),
                }
            )
        require(result == sorted(answers["source_manifest"], key=lambda e: e["path"]))
        for seed in answers["seeds"]:
            bad = safe.open_contained_bytes(
                source, source / seed["path"], LIMIT
            ).decode()
            good = safe.open_contained_bytes(
                source, source / seed["benign_path"], LIMIT
            ).decode()
            require(seed["region"]["end_line"] <= len(bad.splitlines()) and bad != good)
            require(seed["remediation_oracle"]["required_text"] in good)
    return result


def validate_map(mapping: dict, answers: dict, candidate_id: str) -> list[dict]:
    validate_answers(answers)
    require(
        isinstance(mapping, dict)
        and set(mapping)
        == {
            "schema",
            "candidate_id",
            "source_digest",
            "answer_digest",
            "entries",
            "projection_digest",
            "map_digest",
        }
    )
    require(
        mapping["schema"] == MAP_SCHEMA
        and mapping["candidate_id"] == candidate_id
        and audit.is_digest(candidate_id)
    )
    require(
        mapping["source_digest"] == audit.digest(answers["source_manifest"])
        and mapping["answer_digest"] == audit.digest(answers)
    )
    require(
        mapping["map_digest"]
        == audit.digest({k: v for k, v in mapping.items() if k != "map_digest"})
    )
    require(isinstance(mapping["entries"], list) and len(mapping["entries"]) == 32)
    source_by_path = {e["path"]: e for e in answers["source_manifest"]}
    identity_by_path = {
        s[field]: (s["id"], role)
        for s in answers["seeds"]
        for field, role in (("path", "seed"), ("benign_path", "benign"))
    }
    seen_sources, seen_paths, public = set(), set(), []
    for entry in mapping["entries"]:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {"projected_path", "source_path", "answer_id", "role", "digest", "bytes"}
        )
        neutral_path(entry["source_path"])
        neutral_path(entry["projected_path"], entry["source_path"].rsplit(".", 1)[1])
        require(
            entry["source_path"] not in seen_sources
            and entry["projected_path"] not in seen_paths
        )
        require(
            entry["source_path"] in source_by_path
            and (entry["answer_id"], entry["role"])
            == identity_by_path[entry["source_path"]]
        )
        require(
            entry["digest"] == source_by_path[entry["source_path"]]["digest"]
            and entry["bytes"] == source_by_path[entry["source_path"]]["bytes"]
        )
        seen_sources.add(entry["source_path"])
        seen_paths.add(entry["projected_path"])
        public.append(
            {
                "path": entry["projected_path"],
                "digest": entry["digest"],
                "bytes": entry["bytes"],
            }
        )
    public.sort(key=lambda e: e["path"])
    require(mapping["projection_digest"] == audit.digest(public))
    return public


def create_map(answers: dict, candidate_id: str) -> dict:
    validate_answers(answers)
    source = {e["path"]: e for e in answers["source_manifest"]}
    entries = []
    for seed in answers["seeds"]:
        for field, role in (("path", "seed"), ("benign_path", "benign")):
            original = seed[field]
            entries.append(
                {
                    "projected_path": "unit_"
                    + uuid.uuid4().hex
                    + "."
                    + original.rsplit(".", 1)[1],
                    "source_path": original,
                    "answer_id": seed["id"],
                    "role": role,
                    "digest": source[original]["digest"],
                    "bytes": source[original]["bytes"],
                }
            )
    entries.sort(key=lambda e: e["projected_path"])
    mapping = {
        "schema": MAP_SCHEMA,
        "candidate_id": candidate_id,
        "source_digest": audit.digest(answers["source_manifest"]),
        "answer_digest": audit.digest(answers),
        "entries": entries,
        "projection_digest": audit.digest(
            [
                {
                    "path": e["projected_path"],
                    "digest": e["digest"],
                    "bytes": e["bytes"],
                }
                for e in entries
            ]
        ),
    }
    mapping["map_digest"] = audit.digest(mapping)
    validate_map(mapping, answers, candidate_id)
    return mapping


@dataclass(frozen=True)
class Projection:
    source_root: Path
    answer_root: Path
    mapping: dict
    public_manifest: list[dict]


@contextmanager
def projection(
    source: Path, answers: dict, candidate_id: str, frozen_map: dict | None = None
):
    """Construct or copy the frozen mapping in two separately owned roots."""
    before = snapshot(source, answers)
    mapping = create_map(answers, candidate_id) if frozen_map is None else frozen_map
    public = validate_map(mapping, answers, candidate_id)
    with (
        safe.owned_temp_root("nexus-benchmark-source-") as source_owner,
        safe.owned_temp_root("nexus-benchmark-answer-") as answer_owner,
    ):
        target = source_owner / "source"
        target.mkdir(mode=0o700)
        for entry in mapping["entries"]:
            digest, count = safe.safe_copy_file(
                source,
                source / entry["source_path"],
                target / entry["projected_path"],
                LIMIT,
            )
            require((digest, count) == (entry["digest"], entry["bytes"]))
        safe.atomic_publish_bytes(
            source_owner, source_owner / "projection-manifest.json", canonical(public)
        )
        safe.atomic_publish_bytes(
            answer_owner,
            answer_owner / "answer-projection-map.json",
            canonical(mapping),
        )
        require({p.name for p in target.iterdir()} == {e["path"] for e in public})
        for path in target.iterdir():
            require(
                answers["answer_canary"].encode()
                not in safe.open_contained_bytes(target, path, LIMIT)
            )
        try:
            yield Projection(target, answer_owner, mapping, public)
        finally:
            require(snapshot(source, answers) == before)
