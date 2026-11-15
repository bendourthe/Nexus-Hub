#!/usr/bin/env python3
"""Run a serial, repository-local harness-pairing evaluation.

Summary: validates a versioned manifest, runs trusted synthetic adapters in
disposable workspaces, scores each trial with a workload-owned evaluator, and
writes immutable, redacted per-trial receipts plus one aggregate receipt and a
Markdown report. Live execution is refused unless an isolation backend proves
containment and a hard pre-spend limit exists; none ships in this MVP.

The contract is `guides/reference/HARNESS_PAIRING_EVALUATION.md`. Structural
instruction-file conformance stays in `scripts/harness_audit.py`.

Repo-internal maintainer tooling: listed in `DEV_ONLY_SCRIPTS` in
`catalog/hooks/tests/test_installer_smoke.py`; no installer copy step.

Usage:
    python scripts/evaluate_harness_pairings.py run --manifest M --workload-root W
        --adapters-dir A --out-dir O [--instruction-root R] [--dry-run] [--probe]
    python scripts/evaluate_harness_pairings.py conformance [--adapters-dir A]

Exit codes: 0 ok; 1 no eligible trial (unless --probe) or a failed conformance
check; 2 preflight or usage failure; 130 interrupted after writing partial
receipts.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTERS = REPO / "configs" / "harness-adapters"

SCHEMA_MANIFEST = "harness-pairing-manifest/1"
SCHEMA_TRIAL = "harness-pairing-trial/1"
SCHEMA_AGGREGATE = "harness-pairing-aggregate/1"
SCHEMA_ADAPTER = "harness-adapter/1"
SENTINEL = ".nexus-pairing-sentinel"
MAX_OUTPUT_BYTES = 64 * 1024
MAX_FIELD_CHARS = 512
EVALUATOR_TIMEOUT_S = 15.0
VERSION_PROBE_TIMEOUT_S = 10.0
BOOTSTRAP_RESAMPLES = 2000
Z95 = 1.959963984540054
MIN_REPEATS = 3
CREDENTIAL_NAME = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)", re.IGNORECASE)
ISOLATION_MODES = ("synthetic", "metered-live", "observational-live")
ORDER_POLICIES = ("alternating", "seeded-random")
TIE_BREAKS = ("lowest-instruction-tokens", "lowest-latency", "highest-success-rate", "lowest-cost-per-success")
ADAPTER_KEYS = {"claimed_success", "cost_usd", "tool_schema_bytes", "organic_skills", "guard_skills", "note"}

_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_SECRET = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{16,}|"
    r"(?i:password|secret|api[_-]?key|token)\s*[=:]\s*\S{6,})"
)
_ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b[@-_]")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class PreflightError(Exception):
    """A typed failure raised before any trial starts."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# ------------------------------------------------------------------ sanitizing


def sanitize_text(value: str, limit: int = MAX_FIELD_CHARS) -> str:
    """Redact, strip, and escape one string before it is persisted."""
    value = _SECRET.sub("[REDACTED:secret]", value)
    value = _ANSI.sub("", value)
    value = _CONTROL.sub(" ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^(#{1,6})(\s)", r"\\\1\2", value)
    value = html.escape(value, quote=False)
    return value[:limit]


def decode_adapter_bytes(raw: bytes) -> str:
    if len(raw) > MAX_OUTPUT_BYTES:
        raise ValueError("oversized adapter output")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid UTF-8") from exc


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate key {key!r}")
        out[key] = value
    return out


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicates,
                          parse_constant=lambda c: (_ for _ in ()).throw(ValueError(f"constant {c}")))
    except (OSError, ValueError) as exc:
        raise PreflightError("manifest-unreadable", f"{path.name}: {exc}") from exc


def tree_hash(root: Path, skip: tuple[str, ...] = ()) -> str:
    """Hash relative paths and bytes under root, in sorted order."""
    digest = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        if any(rel == s or rel.startswith(s + "/") for s in skip) or "__pycache__" in rel:
            continue
        digest.update(rel.encode("utf-8") + b"\0" + path.read_bytes() + b"\0")
    return "sha256:" + digest.hexdigest()


# ------------------------------------------------------------------ validation


def _need(errors: list[str], where: str, node: Any, keys: tuple[str, ...]) -> bool:
    if not isinstance(node, dict):
        errors.append(f"{where}: must be an object")
        return False
    missing = [k for k in keys if k not in node]
    errors.extend(f"{where}.{k}: required" for k in missing)
    return not missing


def validate_manifest(m: Any) -> list[str]:
    errors: list[str] = []
    top = ("schema", "run_id", "workload", "environment", "pairings", "repeats", "seed", "order_policy")
    if not _need(errors, "$", m, top):
        return errors
    if m["schema"] != SCHEMA_MANIFEST:
        errors.append("$.schema: unsupported schema version")
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", str(m["run_id"])):
        errors.append("$.run_id: 1-64 characters from A-Z a-z 0-9 . _ -")
    _validate_workload(errors, m["workload"])
    _validate_environment(errors, m["environment"])
    if not (isinstance(m["repeats"], int) and not isinstance(m["repeats"], bool) and m["repeats"] >= 1):
        errors.append("$.repeats: must be an integer of at least 1")
    if not isinstance(m["seed"], int) or isinstance(m["seed"], bool):
        errors.append("$.seed: must be an integer")
    if m["order_policy"] not in ORDER_POLICIES:
        errors.append("$.order_policy: unknown policy")
    _validate_pairings(errors, m["pairings"])
    return errors


def _validate_workload(errors: list[str], w: Any) -> None:
    keys = ("id", "revision", "hash", "evaluator_revision", "evaluator_hash", "budget_class", "policy")
    if not _need(errors, "$.workload", w, keys):
        return
    for key in ("hash", "evaluator_hash"):
        if not (isinstance(w[key], str) and _HASH.match(w[key])):
            errors.append(f"$.workload.{key}: must be sha256:<64 hex>")
    policy = w["policy"]
    if _need(errors, "$.workload.policy", policy, ("min_success_rate", "max_latency_s", "max_cost_usd", "tie_break")):
        if policy["tie_break"] not in TIE_BREAKS:
            errors.append("$.workload.policy.tie_break: unknown tie-break")


def _validate_environment(errors: list[str], e: Any) -> None:
    keys = ("os", "arch", "repo_revision", "harness_configuration", "model_parameters",
            "cache_policy", "concurrency", "retry_policy", "pricing")
    if not _need(errors, "$.environment", e, keys):
        return
    if not (isinstance(e["repo_revision"], str) and re.fullmatch(r"[0-9a-f]{40}", e["repo_revision"])):
        errors.append("$.environment.repo_revision: must be 40 hex characters")
    pricing = e["pricing"]
    if not (_is_unavailable(pricing) or (isinstance(pricing, dict) and {"basis", "date"} <= set(pricing))):
        errors.append("$.environment.pricing: needs basis and date, or an explicit unavailable object")


def _validate_pairings(errors: list[str], pairings: Any) -> None:
    if not isinstance(pairings, list) or not pairings:
        errors.append("$.pairings: at least one pairing required")
        return
    seen: set[str] = set()
    for i, p in enumerate(pairings):
        where = f"$.pairings[{i}]"
        if not _need(errors, where, p, ("id", "harness", "model", "instruction", "tool_schema_hash", "isolation_mode", "budgets")):
            continue
        if p["id"] in seen:
            errors.append(f"{where}.id: duplicate pairing id {p['id']!r}")
        seen.add(p["id"])
        if p["isolation_mode"] not in ISOLATION_MODES:
            errors.append(f"{where}.isolation_mode: unknown mode")
        _need(errors, f"{where}.harness", p["harness"], ("name", "version", "adapter", "adapter_version"))
        _need(errors, f"{where}.instruction", p["instruction"], ("variant", "skill_index_mode", "hash", "bytes", "tokens_estimated"))
        if _need(errors, f"{where}.budgets", p["budgets"], ("time_s", "turns", "spend_usd", "spend_enforcement")):
            _validate_budget(errors, where, p)


def _validate_budget(errors: list[str], where: str, p: dict[str, Any]) -> None:
    b = p["budgets"]
    if not (isinstance(b["time_s"], (int, float)) and 0 < b["time_s"] <= 3600):
        errors.append(f"{where}.budgets.time_s: must be within 1..3600 seconds")
    if p["isolation_mode"] == "metered-live":
        if b["spend_enforcement"] not in ("provider", "adapter"):
            errors.append(f"{where}.budgets: metered-live requires provider- or adapter-enforced spend control; "
                          "post-hoc or cancellation-only limits are observational")
        if not (isinstance(b["spend_usd"], (int, float)) and b["spend_usd"] > 0):
            errors.append(f"{where}.budgets.spend_usd: metered-live requires a positive hard limit")


def _is_unavailable(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == {"unavailable"} and bool(value["unavailable"])


def unavailable(reason: str) -> dict[str, str]:
    return {"unavailable": reason}


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


# ------------------------------------------------------------- adapters/profiles


@dataclass
class Adapter:
    name: str
    argv: list[str]
    version_argv: list[str] | None
    dry_run_argv: list[str] | None
    timeout_s: float
    env: dict[str, str] = field(default_factory=dict)
    kind: str = "fake"


def base_env() -> dict[str, str]:
    """The explicit minimal environment every child gets; nothing is inherited wholesale."""
    keep = ("SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "LANG") if os.name == "nt" else ("PATH", "LANG")
    return {k: os.environ[k] for k in keep if k in os.environ}


def _expand(argv: list[str]) -> list[str]:
    """Substitute {python} and resolve the executable to a full path (Windows needs the extension)."""
    out = [sys.executable if a == "{python}" else a for a in argv]
    if not Path(out[0]).is_file():
        out[0] = shutil.which(out[0]) or out[0]
    return out


def load_adapter(adapters_dir: Path, name: str) -> Adapter:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", name):
        raise PreflightError("adapter-name", f"unsafe adapter name {name!r}")
    path = adapters_dir / f"{name}.json"
    if not path.is_file():
        raise PreflightError("adapter-missing", f"no adapter profile {name!r} in {adapters_dir.name}")
    prof = load_json(path)
    errors: list[str] = []
    if not _need(errors, name, prof, ("schema", "name", "kind", "argv", "timeout_s")) or prof["schema"] != SCHEMA_ADAPTER:
        raise PreflightError("adapter-schema", "; ".join(errors) or f"{name}: unsupported adapter schema")
    for key in ("argv", "version_argv", "dry_run_argv"):
        value = prof.get(key)
        if value is not None and not (isinstance(value, list) and value and all(isinstance(a, str) for a in value)):
            raise PreflightError("adapter-argv", f"{name}.{key} must be a non-empty argv array of strings (no shell strings)")
    env = dict(prof.get("env_set", {}))
    names = list(env) + list(prof.get("env_allow", []))
    if any(CREDENTIAL_NAME.search(n) for n in names):
        raise PreflightError("adapter-credential-env", f"{name}: credential-named environment is not allowed")
    for n in prof.get("env_allow", []):
        if n in os.environ:
            env[n] = os.environ[n]
    return Adapter(name, prof["argv"], prof.get("version_argv"), prof.get("dry_run_argv"),
                   float(prof["timeout_s"]), env, str(prof["kind"]))


def discover_executable(argv: list[str]) -> str | None:
    first = _expand(argv)[0]
    return first if Path(first).is_file() else None


# ---------------------------------------------------------------- process running


@dataclass
class RunResult:
    returncode: int | None
    stdout: bytes
    stderr: bytes
    timed_out: bool
    overflow: bool
    duration: float


def kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """Terminate the whole process tree, not just the direct child."""
    if proc.poll() is not None and os.name != "nt":
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True,
                       creationflags=subprocess.CREATE_NO_WINDOW, check=False)
    else:
        import signal
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    try:
        proc.kill()
    except OSError:
        pass


def _drain(stream: Any, sink: list[bytes], flag: threading.Event, kill: threading.Event) -> None:
    total = 0
    while True:
        chunk = stream.read(4096)
        if not chunk:
            return
        total += len(chunk)
        if total > MAX_OUTPUT_BYTES:
            flag.set()
            kill.set()
            return
        sink.append(chunk)


def run_bounded(argv: list[str], stdin: bytes, env: dict[str, str], cwd: Path, timeout_s: float) -> RunResult:
    start = time.monotonic()
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=env, cwd=str(cwd), shell=False,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                                start_new_session=(os.name != "nt"))
    except OSError:
        # A launch failure is a typed non-result (return code None), never a crash of the runner.
        return RunResult(None, b"", b"", False, False, time.monotonic() - start)
    out: list[bytes] = []
    err: list[bytes] = []
    overflow, kill = threading.Event(), threading.Event()
    readers = [threading.Thread(target=_drain, args=(proc.stdout, out, overflow, kill), daemon=True),
               threading.Thread(target=_drain, args=(proc.stderr, err, overflow, kill), daemon=True)]
    for t in readers:
        t.start()
    try:
        proc.stdin.write(stdin)
        proc.stdin.close()
    except OSError:
        pass
    timed_out = False
    while proc.poll() is None:
        if kill.is_set():
            break
        if time.monotonic() - start > timeout_s:
            timed_out = True
            break
        time.sleep(0.02)
    if timed_out or kill.is_set():
        kill_tree(proc)
    proc.wait()
    for t in readers:
        t.join(timeout=2)
    return RunResult(proc.returncode, b"".join(out), b"".join(err), timed_out, overflow.is_set(),
                     time.monotonic() - start)


# ------------------------------------------------------------------- preflight


def isolation_backend_proven() -> bool:
    """No isolation backend ships in this MVP, so live execution is always refused."""
    return False


def instruction_figures(path: Path) -> tuple[int, str, int]:
    """Bytes, hash, and estimated tokens, with tokens from the one repository measurer."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from scripts.measure_rendered_context import measure

    data = path.read_bytes()
    report = measure(path, False, None)
    if report.get("status") != "ok":
        raise PreflightError("instruction-unreadable", f"{path.name}: {report.get('reason')}")
    return len(data), "sha256:" + hashlib.sha256(data).hexdigest(), int(report["tokens"])


def preflight(manifest: dict[str, Any], workload_root: Path, adapters_dir: Path, instruction_root: Path,
              out_dir: Path, probe_versions: bool) -> dict[str, Adapter]:
    errors = validate_manifest(manifest)
    if errors:
        raise PreflightError("manifest-invalid", "; ".join(errors[:6]))
    modes = {p["isolation_mode"] for p in manifest["pairings"]}
    if modes - {"synthetic"} and not isolation_backend_proven():
        raise PreflightError("isolation-backend-unavailable",
                             "live execution needs a proven isolation backend (filesystem, process tree, network, "
                             "credential injection, cleanup); none is available, so live trials are rejected and "
                             "the result is needs-live-validation")
    if tree_hash(workload_root, ("evaluator",)) != manifest["workload"]["hash"]:
        raise PreflightError("workload-hash", "workload files do not match the manifest hash")
    if tree_hash(workload_root / "evaluator") != manifest["workload"]["evaluator_hash"]:
        raise PreflightError("evaluator-hash", "evaluator files do not match the manifest hash")
    if (out_dir / manifest["run_id"]).exists():
        raise PreflightError("output-collision", f"run {manifest['run_id']!r} already has receipts; runs never resume")
    adapters: dict[str, Adapter] = {}
    for p in manifest["pairings"]:
        _check_pairing(p, adapters, adapters_dir, instruction_root, probe_versions)
    return adapters


def _check_pairing(p: dict[str, Any], adapters: dict[str, Adapter], adapters_dir: Path,
                   instruction_root: Path, probe_versions: bool) -> None:
    adapter = adapters.get(p["harness"]["adapter"]) or load_adapter(adapters_dir, p["harness"]["adapter"])
    adapters[adapter.name] = adapter
    if discover_executable(adapter.argv) is None:
        raise PreflightError("binary-absent", f"{adapter.name}: executable {adapter.argv[0]!r} not found")
    if probe_versions and adapter.version_argv:
        result = run_bounded(_expand(adapter.version_argv), b"", base_env(), Path.cwd(), VERSION_PROBE_TIMEOUT_S)
        if result.timed_out or result.returncode != 0:
            raise PreflightError("version-probe", f"{adapter.name}: version probe failed or timed out")
    rel = p["instruction"].get("path")
    if rel is not None:
        target = (instruction_root / rel).resolve()
        if not str(target).startswith(str(instruction_root.resolve())) or not target.is_file():
            raise PreflightError("instruction-path", f"{p['id']}: instruction path escapes its root or is missing")
        size, digest, tokens = instruction_figures(target)
        record = p["instruction"]
        if (size, digest, tokens) != (record["bytes"], record["hash"], record["tokens_estimated"]):
            raise PreflightError("instruction-figures", f"{p['id']}: recorded bytes, hash, or tokens differ from the file")


def expected_order(manifest: dict[str, Any]) -> list[str]:
    ids = [p["id"] for p in manifest["pairings"]]
    order: list[str] = []
    for r in range(manifest["repeats"]):
        if manifest["order_policy"] == "alternating":
            order += ids if r % 2 == 0 else ids[::-1]
        else:
            shuffled = list(ids)
            random.Random(f"{manifest['seed']}:{r}").shuffle(shuffled)
            order += shuffled
    return order


# ------------------------------------------------------------------- one trial


def _make_workspace(work_root: Path, token: str, workload_root: Path) -> Path:
    work_root.mkdir(parents=True, exist_ok=True)
    ws = Path(tempfile.mkdtemp(prefix="nexus-pairing-", dir=work_root))
    (ws / SENTINEL).write_text(token, encoding="utf-8")
    spec = load_json(workload_root / "workload.json")
    for rel in spec.get("inputs", []):
        src = (workload_root / "inputs" / rel).resolve()
        if not str(src).startswith(str((workload_root / "inputs").resolve())) or not src.is_file():
            raise PreflightError("workload-input", f"declared input {rel!r} escapes or is missing")
        dest = ws / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
    return ws


def cleanup_workspace(ws: Path, work_root: Path, token: str) -> str:
    """Delete only a sentinel-owned directory inside the work root; otherwise leave it."""
    try:
        real = ws.resolve()
        sentinel = ws / SENTINEL
        inside = real.parent == work_root.resolve() and not ws.is_symlink()
        if inside and sentinel.is_file() and sentinel.read_text(encoding="utf-8") == token:
            shutil.rmtree(ws)
            return "removed"
    except OSError:
        pass
    return "manual-cleanup-needed"


def parse_adapter_output(raw: bytes) -> dict[str, Any]:
    text = decode_adapter_bytes(raw).strip()
    if "\n" in text:
        raise ValueError("adapter must print exactly one JSON object")
    obj = json.loads(text, object_pairs_hook=_reject_duplicates)
    if not isinstance(obj, dict) or not set(obj) <= ADAPTER_KEYS:
        raise ValueError("adapter output has non-allowlisted fields")
    return obj


def run_evaluator(workload_root: Path, ws: Path) -> tuple[bool | None, str]:
    ev = workload_root / "evaluator"
    result = run_bounded([sys.executable, str(ev / "evaluate.py"), str(ws), str(ev)], b"", base_env(), ev,
                         EVALUATOR_TIMEOUT_S)
    if result.timed_out or result.overflow or result.returncode != 0:
        return None, "evaluator-failure"
    try:
        obj = json.loads(decode_adapter_bytes(result.stdout))
        ok = obj["success"]
        if ok not in (True, False):
            raise ValueError("success must be boolean")
        return ok, str(obj.get("fingerprint", ""))
    except (ValueError, KeyError, TypeError):
        return None, "evaluator-failure"


def normalize_fingerprint(raw: str, outcome: str) -> str:
    if outcome == "success":
        return ""
    cleaned = re.sub(r"\d+", "N", sanitize_text(raw or outcome).lower())
    return "fp-" + hashlib.sha256(f"{outcome}:{cleaned}".encode("utf-8")).hexdigest()[:12]


def run_trial(manifest: dict[str, Any], pairing: dict[str, Any], adapter: Adapter, position: int, index: int,
              workload_root: Path, work_root: Path) -> dict[str, Any]:
    token = hashlib.sha256(f"{manifest['run_id']}:{position}".encode()).hexdigest()
    ws = _make_workspace(work_root, token, workload_root)
    root_hash = tree_hash(workload_root)
    started = datetime.now(timezone.utc)
    prompt = load_json(workload_root / "workload.json").get("prompt", "")
    seed = manifest["seed"] + position
    payload = json.dumps({"workspace": str(ws), "prompt": prompt, "trial_index": index, "seed": seed}).encode()
    time_budget = min(float(pairing["budgets"]["time_s"]), adapter.timeout_s)
    env = {**base_env(), **adapter.env}
    result = run_bounded(_expand(adapter.argv), payload, env, ws, time_budget)
    outcome, claim, protocol_fields = _classify_adapter(result, adapter.kind)
    evaluator_success: bool | None = None
    fingerprint_raw = ""
    if tree_hash(workload_root) != root_hash:
        outcome, fingerprint_raw = "containment-failure", "evaluator-tamper"
    elif outcome == "ran":
        evaluator_success, fingerprint_raw = run_evaluator(workload_root, ws)
        outcome = _final_outcome(evaluator_success)
    cleanup_workspace(ws, work_root, token)
    ended = datetime.now(timezone.utc)
    return _receipt(manifest, pairing, position, index, seed, outcome, evaluator_success, claim, result.duration,
                    protocol_fields, fingerprint_raw, started, ended)


def _classify_adapter(result: RunResult, kind: str) -> tuple[str, bool, dict[str, Any]]:
    if result.timed_out:
        return "timeout", False, {}
    if result.overflow:
        return "adapter-protocol-error", False, {}
    if kind == "cli":
        # A real CLI speaks no JSON protocol: exit status is the only harness claim.
        return "ran", result.returncode == 0, {}
    try:
        obj = parse_adapter_output(result.stdout)
        if result.returncode != 0:
            raise ValueError("non-zero exit")
        return "ran", bool(obj.get("claimed_success", False)), obj
    except (ValueError, json.JSONDecodeError):
        return "adapter-protocol-error", False, {}


def _final_outcome(evaluator_success: bool | None) -> str:
    if evaluator_success is None:
        return "evaluator-error"
    return "success" if evaluator_success else "failure"


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [sanitize_text(str(v), 64) for v in value[:32]]


def _receipt(manifest: dict[str, Any], pairing: dict[str, Any], position: int, index: int, seed: int,
             outcome: str, evaluator_success: bool | None, claim: bool, latency: float,
             fields: dict[str, Any], fingerprint_raw: str, started: datetime,
             ended: datetime) -> dict[str, Any]:
    tool_bytes = fields.get("tool_schema_bytes")
    organic = fields.get("organic_skills")
    return {
        "schema": SCHEMA_TRIAL,
        "run_id": manifest["run_id"],
        "workload_hash": manifest["workload"]["hash"],
        "pairing_id": pairing["id"],
        "trial_index": index,
        "order_position": position,
        "seed": seed,
        "isolation_mode": pairing["isolation_mode"],
        "outcome": outcome,
        "evaluator_success": evaluator_success if outcome in ("success", "failure") else
        (False if outcome in ("timeout", "adapter-protocol-error", "containment-failure") else None),
        "harness_claim_success": claim,
        "latency_s": round(latency, 3),
        "cost_usd": unavailable("not-applicable-synthetic") if pairing["isolation_mode"] == "synthetic"
        else (fields["cost_usd"] if _is_num(fields.get("cost_usd")) and fields["cost_usd"] >= 0
              else unavailable("adapter reported no cost")),
        "instruction_bytes": pairing["instruction"]["bytes"],
        "instruction_tokens_estimated": pairing["instruction"]["tokens_estimated"],
        "tool_schema_bytes": tool_bytes if isinstance(tool_bytes, int) and tool_bytes >= 0
        else unavailable("adapter reported no tool-schema size"),
        "organic_skills": _clean_list(organic) if organic is not None else None,
        "guard_skills": _clean_list(fields.get("guard_skills")),
        "failure_fingerprint": normalize_fingerprint(fingerprint_raw, outcome),
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "ended_at": ended.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    }


# ------------------------------------------------------------------ aggregation


def wilson(successes: int, n: int) -> tuple[float, float]:
    p = successes / n
    denom = 1 + Z95 * Z95 / n
    center = (p + Z95 * Z95 / (2 * n)) / denom
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95 * Z95 / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def bootstrap(values: list[float], seed_text: str) -> tuple[float, float]:
    rng = random.Random(seed_text)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOTSTRAP_RESAMPLES))
    return means[math.floor(0.025 * BOOTSTRAP_RESAMPLES)], means[math.ceil(0.975 * BOOTSTRAP_RESAMPLES) - 1]


def _block(values: list[Any], seed_text: str) -> dict[str, Any]:
    if not values:
        return {"mean": unavailable("no trials"), "ci95": unavailable("no trials")}
    if any(not _is_num(v) for v in values):
        return {"mean": unavailable("a trial lacks this value"), "ci95": unavailable("a trial lacks this value")}
    low, high = bootstrap([float(v) for v in values], seed_text)
    return {"mean": round(sum(values) / len(values), 6), "ci95": [round(low, 6), round(high, 6)]}


def environment_identity(manifest: dict[str, Any], pairing: dict[str, Any]) -> tuple[Any, ...]:
    env = {**manifest["environment"], **pairing.get("environment_override", {})}
    w = manifest["workload"]
    return (w["hash"], w["evaluator_hash"], w["budget_class"], env["os"], env["arch"],
            repr(sorted(env["model_parameters"].items())), env["cache_policy"], env["retry_policy"],
            env["concurrency"], repr(env["pricing"]))


def aggregate_pairing(manifest: dict[str, Any], pairing: dict[str, Any], trials: list[dict[str, Any]]) -> dict[str, Any]:
    mine = [t for t in trials if t["pairing_id"] == pairing["id"]]
    rankable = [t for t in mine if t["evaluator_success"] is not None]
    wins = sum(1 for t in rankable if t["evaluator_success"] is True)
    out: dict[str, Any] = {
        "pairing_id": pairing["id"], "isolation_mode": pairing["isolation_mode"], "trials": len(mine),
        "rankable_trials": len(rankable), "non_rankable_trials": len(mine) - len(rankable), "successes": wins,
        "instruction_bytes": pairing["instruction"]["bytes"],
        "instruction_tokens_estimated": pairing["instruction"]["tokens_estimated"],
    }
    if rankable:
        low, high = wilson(wins, len(rankable))
        out["success_rate"] = round(wins / len(rankable), 6)
        out["success_ci95"] = [round(low, 6), round(high, 6)]
    else:
        out["success_rate"] = out["success_ci95"] = unavailable("no rankable trial")
    seed = manifest["seed"]
    out["latency_s"] = _block([t["latency_s"] for t in rankable], f"{seed}:{pairing['id']}:latency")
    costs = [t["cost_usd"] for t in rankable]
    out["cost_usd"] = _block(costs, f"{seed}:{pairing['id']}:cost")
    if not costs or any(not _is_num(c) for c in costs):
        out["cost_per_success_usd"] = unavailable("cost unavailable for at least one trial")
    elif wins == 0:
        out["cost_per_success_usd"] = unavailable("no successful task")
    else:
        out["cost_per_success_usd"] = round(sum(costs) / wins, 6)
    out["failure_fingerprints"] = sorted({t["failure_fingerprint"] for t in mine if t["failure_fingerprint"]})
    out["organic_skills"] = (unavailable("needs-live-validation") if any(t["organic_skills"] is None for t in mine)
                             else sorted({s for t in mine for s in t["organic_skills"]}))
    return out


def qualifies(manifest: dict[str, Any], agg: dict[str, Any]) -> bool:
    policy = manifest["workload"]["policy"]
    if not _is_num(agg["success_rate"]) or agg["success_rate"] < policy["min_success_rate"]:
        return False
    latency = agg["latency_s"]["mean"]
    if not _is_num(latency) or latency > policy["max_latency_s"]:
        return False
    cap = policy["max_cost_usd"]
    if cap is not None:
        cost = agg["cost_per_success_usd"]
        return _is_num(cost) and cost <= cap and agg["isolation_mode"] == "metered-live"
    return True


def _dims(agg: dict[str, Any], with_cost: bool) -> list[float]:
    dims = [agg["success_rate"], -agg["latency_s"]["mean"], -agg["instruction_tokens_estimated"]]
    return dims + ([-agg["cost_per_success_usd"]] if with_cost else [])


def pareto(aggs: list[dict[str, Any]]) -> list[str]:
    with_cost = all(_is_num(a["cost_per_success_usd"]) for a in aggs)
    keep = []
    for a in aggs:
        da = _dims(a, with_cost)
        beaten = any(all(x >= y for x, y in zip(_dims(b, with_cost), da)) and any(x > y for x, y in zip(_dims(b, with_cost), da))
                     for b in aggs if b is not a)
        if not beaten:
            keep.append(a["pairing_id"])
    return sorted(keep)


def _tie(agg: dict[str, Any], tie: str) -> tuple[float, tuple[float, float] | None]:
    if tie == "lowest-instruction-tokens":
        v = float(agg["instruction_tokens_estimated"])
        return v, (v, v)
    if tie == "lowest-latency":
        return agg["latency_s"]["mean"], tuple(agg["latency_s"]["ci95"])
    if tie == "highest-success-rate":
        return -agg["success_rate"], (-agg["success_ci95"][1], -agg["success_ci95"][0])
    ci = agg["cost_usd"]["ci95"]
    return agg["cost_per_success_usd"], (tuple(ci) if isinstance(ci, list) else None)


def _unavailable_identity(manifest: dict[str, Any], p: dict[str, Any]) -> bool:
    return (_is_unavailable(manifest["environment"]["pricing"]) or _is_unavailable(p["tool_schema_hash"])
            or _is_unavailable(p["harness"]["version"]))


def recommend(manifest: dict[str, Any], aggs: list[dict[str, Any]]) -> dict[str, Any]:
    def refuse(reason: str) -> dict[str, Any]:
        return {"state": "no-recommendation", "reason": reason}

    if len({environment_identity(manifest, p) for p in manifest["pairings"]}) != 1:
        return refuse("incomparable comparison groups")
    if any(_unavailable_identity(manifest, p) for p in manifest["pairings"]):
        return refuse("incomparable: unavailable identity or pricing data")
    if any(p["isolation_mode"] != "metered-live" for p in manifest["pairings"]):
        return refuse("evidence mode is not metered-live")
    if any(a["rankable_trials"] < MIN_REPEATS for a in aggs):
        return refuse("fewer than three repeats")
    good = [a for a in aggs if qualifies(manifest, a)]
    if not good:
        return refuse("no pairing meets the predeclared gates")
    frontier = set(pareto(good))
    tie = manifest["workload"]["policy"]["tie_break"]
    best = min((a for a in good if a["pairing_id"] in frontier), key=lambda a: _tie(a, tie)[0])
    for other in good:
        if other is best:
            continue
        mine, theirs = _tie(best, tie)[1], _tie(other, tie)[1]
        if mine is None or theirs is None or not mine[1] < theirs[0]:
            return refuse("95% intervals overlap on the tie-break")
    return {"state": "recommended", "pairing_id": best["pairing_id"]}


def aggregate(manifest: dict[str, Any], trials: list[dict[str, Any]]) -> dict[str, Any]:
    aggs = [aggregate_pairing(manifest, p, trials) for p in manifest["pairings"]]
    good = [a for a in aggs if qualifies(manifest, a)]
    return {
        "schema": SCHEMA_AGGREGATE, "run_id": manifest["run_id"], "workload_hash": manifest["workload"]["hash"],
        "comparison_groups": len({environment_identity(manifest, p) for p in manifest["pairings"]}),
        "pairings": aggs, "qualifying": sorted(a["pairing_id"] for a in good), "pareto_frontier": pareto(good),
        "recommendation": recommend(manifest, aggs),
    }


# -------------------------------------------------------------------- reporting


def _fmt(value: Any) -> str:
    if _is_unavailable(value):
        return f"unavailable ({sanitize_text(value['unavailable'], 80)})"
    if isinstance(value, list):
        return "[" + ", ".join(_fmt(v) for v in value) + "]"
    return sanitize_text(str(value), 80)


def render_report(manifest: dict[str, Any], agg: dict[str, Any], state: str) -> str:
    lines = [f"# Harness Pairing Report {sanitize_text(manifest['run_id'], 64)}", "",
             f"**Run state:** {state}", f"**Workload hash:** {manifest['workload']['hash']}", "",
             "## Pairings", "",
             "| Pairing | Mode | Trials | Success | Success 95% | Latency s | Latency 95% | Cost per success | Instruction tokens |",
             "|---|---|---|---|---|---|---|---|---|"]
    for a in agg["pairings"]:
        lines.append("| " + " | ".join([
            sanitize_text(a["pairing_id"], 64), a["isolation_mode"], f"{a['rankable_trials']}/{a['trials']}",
            _fmt(a["success_rate"]), _fmt(a["success_ci95"]), _fmt(a["latency_s"]["mean"]),
            _fmt(a["latency_s"]["ci95"]), _fmt(a["cost_per_success_usd"]), str(a["instruction_tokens_estimated"])]) + " |")
    lines += ["", "## Decision", "", f"**Qualifying:** {', '.join(agg['qualifying']) or 'none'}",
              f"**Pareto frontier:** {', '.join(agg['pareto_frontier']) or 'none'}",
              f"**Recommendation:** {sanitize_text(json.dumps(agg['recommendation']), 200)}", "",
              "## Evidence Class", ""]
    if any(a["isolation_mode"] == "synthetic" for a in agg["pairings"]):
        lines.append("Synthetic receipts prove the machinery only. Organic skill selection and every live claim are "
                     "`needs-live-validation`.")
    lines += ["", "Instruction and schema payloads are recorded as hashes, never as text.", ""]
    return "\n".join(lines)


def write_new(path: Path, text: str) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


# ----------------------------------------------------------------------- driver


def run_matrix(manifest: dict[str, Any], workload_root: Path, adapters_dir: Path, instruction_root: Path,
               out_dir: Path, work_root: Path, probe_versions: bool = False, dry_run: bool = False,
               stop_after: int | None = None) -> dict[str, Any]:
    adapters = preflight(manifest, workload_root, adapters_dir, instruction_root, out_dir, probe_versions)
    order = expected_order(manifest)
    plan = {"run_id": manifest["run_id"], "trials": len(order), "order": order,
            "modes": sorted({p["isolation_mode"] for p in manifest["pairings"]})}
    if dry_run:
        return {"dry_run": True, "plan": plan}
    run_dir = out_dir / manifest["run_id"]
    run_dir.mkdir(parents=True)
    by_id = {p["id"]: p for p in manifest["pairings"]}
    counts: dict[str, int] = {}
    trials: list[dict[str, Any]] = []
    state = "complete"
    try:
        for position, pid in enumerate(order):
            if stop_after is not None and position >= stop_after:
                raise KeyboardInterrupt
            idx = counts.get(pid, 0)
            counts[pid] = idx + 1
            pairing = by_id[pid]
            trial = run_trial(manifest, pairing, adapters[pairing["harness"]["adapter"]], position, idx,
                              workload_root, work_root)
            write_new(run_dir / f"trial-{position:03d}-{pid}.json", json.dumps(trial, indent=2) + "\n")
            trials.append(trial)
    except KeyboardInterrupt:
        state = "interrupted"
    agg = aggregate(manifest, trials) | {"run_state": state}
    write_new(run_dir / "aggregate.json", json.dumps(agg, indent=2) + "\n")
    write_new(run_dir / "report.md", render_report(manifest, agg, state))
    return {"dry_run": False, "plan": plan, "aggregate": agg, "run_dir": str(run_dir), "state": state}


def conformance(adapters_dir: Path) -> list[dict[str, str]]:
    """Credential-free profile, version, and dry-run conformance for each adapter profile."""
    results = []
    for path in sorted(adapters_dir.glob("*.json")):
        row = {"adapter": path.stem}
        try:
            adapter = load_adapter(adapters_dir, path.stem)
        except PreflightError as exc:
            results.append({**row, "status": "profile-invalid", "detail": exc.code})
            continue
        if discover_executable(adapter.argv) is None:
            results.append({**row, "status": "binary-absent", "detail": adapter.argv[0]})
            continue
        if adapter.version_argv:
            probe = run_bounded(_expand(adapter.version_argv), b"", base_env(), Path.cwd(), VERSION_PROBE_TIMEOUT_S)
            row["version"] = sanitize_text(probe.stdout.decode("utf-8", "replace"), 80) if probe.returncode == 0 else "unavailable"
            row["status"] = "ok" if probe.returncode == 0 and not probe.timed_out else "version-probe-failed"
        else:
            row["status"] = "ok"
        row["dry_run"] = "declared" if adapter.dry_run_argv else "absent"
        results.append(row)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--manifest", type=Path, required=True)
    run.add_argument("--workload-root", type=Path, required=True)
    run.add_argument("--adapters-dir", type=Path, default=DEFAULT_ADAPTERS)
    run.add_argument("--instruction-root", type=Path, default=REPO)
    run.add_argument("--out-dir", type=Path, required=True)
    run.add_argument("--work-root", type=Path, default=Path(tempfile.gettempdir()) / "nexus-pairing-work")
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--probe", action="store_true", help="exit 0 even when no trial was eligible")
    conf = sub.add_parser("conformance")
    conf.add_argument("--adapters-dir", type=Path, default=DEFAULT_ADAPTERS)
    args = parser.parse_args(argv)
    if args.cmd == "conformance":
        rows = conformance(args.adapters_dir)
        print(json.dumps(rows, indent=2))
        return 0 if all(r["status"] in ("ok", "binary-absent") for r in rows) else 1
    try:
        manifest = load_json(args.manifest)
        outcome = run_matrix(manifest, args.workload_root, args.adapters_dir, args.instruction_root,
                             args.out_dir, args.work_root, probe_versions=True, dry_run=args.dry_run)
    except PreflightError as exc:
        print(json.dumps({"preflight": "failed", "code": exc.code, "detail": sanitize_text(exc.detail, 400)}))
        return 2
    if outcome["dry_run"]:
        print(json.dumps(outcome["plan"], indent=2))
        return 0
    eligible = sum(p["rankable_trials"] for p in outcome["aggregate"]["pairings"])
    print(json.dumps({"run_dir": outcome["run_dir"], "state": outcome["state"], "rankable_trials": eligible}))
    if outcome["state"] == "interrupted":
        return 130
    return 0 if eligible or args.probe else 1


if __name__ == "__main__":
    sys.exit(main())
