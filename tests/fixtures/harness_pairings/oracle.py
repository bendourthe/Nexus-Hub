"""Independent contract oracle for harness-pairing evaluation (v4.15.2).

This module is test infrastructure. It restates the contract in
``guides/reference/HARNESS_PAIRING_EVALUATION.md`` as small pure functions so
that fixtures and, in Phase 3, the evaluator's output can be recomputed without
sharing code with the producer. It imports nothing from ``scripts/`` except in
``measurer_tokens``, which deliberately calls the repository's one token
estimator (v4.13 DF-4) so an instruction-token figure cannot disagree with it.

Unavailable values are explicit: a metric is either a number or an object
``{"unavailable": "<reason>"}``. A gap never becomes zero.
"""

from __future__ import annotations

import math
import random
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SCHEMAS = {
    "manifest": "harness-pairing-manifest/1",
    "trial": "harness-pairing-trial/1",
    "aggregate": "harness-pairing-aggregate/1",
}
ISOLATION_MODES = ("synthetic", "metered-live", "observational-live")
ORDER_POLICIES = ("alternating", "seeded-random")
OUTCOMES = (
    "success",
    "failure",
    "timeout",
    "budget-exhausted",
    "adapter-protocol-error",
    "evaluator-error",
    "containment-failure",
)
SPEND_ENFORCEMENT = ("none", "provider", "adapter")
MIN_REPEATS_FOR_RECOMMENDATION = 3
Z95 = 1.959963984540054
BOOTSTRAP_RESAMPLES = 2000
MAX_FIELD_CHARS = 512

_HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
_REV = re.compile(r"^[0-9a-f]{40}$")
_SECRET = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{16,}|"
    r"(?i:password|secret|api[_-]?key|token)\s*[=:]\s*\S{6,})"
)
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_FORGED_HEADING = re.compile(r"(^|\n)\s{0,3}#{1,6}\s")

MANIFEST_KEYS = ("schema", "run_id", "workload", "environment", "pairings", "repeats", "seed", "order_policy")
WORKLOAD_KEYS = ("id", "revision", "hash", "evaluator_revision", "evaluator_hash", "budget_class", "policy")
POLICY_KEYS = ("min_success_rate", "max_latency_s", "max_cost_usd", "tie_break")
ENV_KEYS = (
    "os",
    "arch",
    "repo_revision",
    "harness_configuration",
    "model_parameters",
    "cache_policy",
    "concurrency",
    "retry_policy",
    "pricing",
)
PAIRING_KEYS = (
    "id",
    "harness",
    "model",
    "instruction",
    "tool_schema_hash",
    "isolation_mode",
    "budgets",
)
TRIAL_KEYS = (
    "schema",
    "run_id",
    "workload_hash",
    "pairing_id",
    "trial_index",
    "order_position",
    "seed",
    "isolation_mode",
    "outcome",
    "evaluator_success",
    "harness_claim_success",
    "latency_s",
    "cost_usd",
    "instruction_bytes",
    "instruction_tokens_estimated",
    "tool_schema_bytes",
    "organic_skills",
    "guard_skills",
    "failure_fingerprint",
    "started_at",
    "ended_at",
)
TIE_BREAKS = (
    "lowest-instruction-tokens",
    "lowest-latency",
    "highest-success-rate",
    "lowest-cost-per-success",
)


def unavailable(reason: str) -> dict[str, str]:
    return {"unavailable": reason}


def is_unavailable(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == {"unavailable"} and bool(value["unavailable"])


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _num_or_unavailable(value: Any) -> bool:
    return (is_number(value) and value >= 0) or is_unavailable(value)


# --------------------------------------------------------------------- hostile text


def text_problem(value: Any) -> str | None:
    """Return why a persisted string field is unsafe, or None."""
    if not isinstance(value, str):
        return None
    if len(value) > MAX_FIELD_CHARS:
        return "oversized field"
    if "\x1b" in value:
        return "ANSI escape"
    if _CONTROL.search(value):
        return "control byte"
    if _FORGED_HEADING.search(value):
        return "forged Markdown heading"
    if _SECRET.search(value):
        return "secret-shaped value"
    return None


def decode_adapter_bytes(raw: bytes) -> str:
    """Adapter output is hostile: strict UTF-8 only, bounded before parsing."""
    if len(raw) > 64 * 1024:
        raise ValueError("oversized adapter output")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValueError("invalid UTF-8") from exc


def path_escapes(value: str) -> bool:
    norm = value.replace("\\", "/")
    return (
        norm.startswith("/")
        or re.match(r"^[A-Za-z]:", norm) is not None
        or ".." in norm.split("/")
    )


def _walk_strings(node: Any, trail: str = ""):
    if isinstance(node, str):
        yield trail, node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield from _walk_strings(key, f"{trail}.<key>")
            yield from _walk_strings(value, f"{trail}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _walk_strings(value, f"{trail}[{index}]")


def _text_errors(doc: Any) -> list[str]:
    errors = []
    for trail, value in _walk_strings(doc):
        problem = text_problem(value)
        if problem:
            errors.append(f"{trail}: {problem}")
    return errors


# -------------------------------------------------------------------- manifest rules


def validate_manifest(m: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(m, dict):
        return ["$: manifest must be an object"]
    for key in MANIFEST_KEYS:
        if key not in m:
            errors.append(f"$.{key}: required")
    extra = sorted(set(m) - set(MANIFEST_KEYS))
    if extra:
        errors.append(f"$: unknown keys {extra}")
    if errors:
        return errors
    if m["schema"] != SCHEMAS["manifest"]:
        errors.append("$.schema: unsupported schema version")
    errors += _text_errors(m)
    errors += _workload_errors(m["workload"])
    errors += _env_errors(m["environment"])
    if not (isinstance(m["repeats"], int) and not isinstance(m["repeats"], bool) and m["repeats"] >= 1):
        errors.append("$.repeats: must be an integer of at least 1")
    if not isinstance(m["seed"], int) or isinstance(m["seed"], bool):
        errors.append("$.seed: must be an integer")
    if m["order_policy"] not in ORDER_POLICIES:
        errors.append("$.order_policy: unknown policy")
    errors += _pairing_errors(m["pairings"])
    return errors


def _workload_errors(w: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(w, dict):
        return ["$.workload: must be an object"]
    for key in WORKLOAD_KEYS:
        if key not in w:
            errors.append(f"$.workload.{key}: required")
    if errors:
        return errors
    for key in ("hash", "evaluator_hash"):
        if not (isinstance(w[key], str) and _HASH.match(w[key])):
            errors.append(f"$.workload.{key}: must be sha256:<64 hex>")
    policy = w["policy"]
    if not isinstance(policy, dict) or any(k not in policy for k in POLICY_KEYS):
        errors.append("$.workload.policy: min_success_rate, max_latency_s, max_cost_usd, tie_break required")
    else:
        if not (is_number(policy["min_success_rate"]) and 0 <= policy["min_success_rate"] <= 1):
            errors.append("$.workload.policy.min_success_rate: must be within 0..1")
        if policy["tie_break"] not in TIE_BREAKS:
            errors.append("$.workload.policy.tie_break: unknown tie-break")
    return errors


def _env_errors(e: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(e, dict):
        return ["$.environment: must be an object"]
    for key in ENV_KEYS:
        if key not in e:
            errors.append(f"$.environment.{key}: required")
    if errors:
        return errors
    if not (isinstance(e["repo_revision"], str) and _REV.match(e["repo_revision"])):
        errors.append("$.environment.repo_revision: must be 40 hex characters")
    if not (isinstance(e["concurrency"], int) and e["concurrency"] >= 1):
        errors.append("$.environment.concurrency: must be a positive integer")
    pricing = e["pricing"]
    if not (is_unavailable(pricing) or (isinstance(pricing, dict) and {"basis", "date"} <= set(pricing))):
        errors.append("$.environment.pricing: needs basis and date, or an explicit unavailable object")
    return errors


def _pairing_errors(pairings: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(pairings, list) or len(pairings) < 1:
        return ["$.pairings: at least one pairing required"]
    seen: set[str] = set()
    for index, p in enumerate(pairings):
        where = f"$.pairings[{index}]"
        if not isinstance(p, dict):
            errors.append(f"{where}: must be an object")
            continue
        for key in PAIRING_KEYS:
            if key not in p:
                errors.append(f"{where}.{key}: required")
        if any(k not in p for k in PAIRING_KEYS):
            continue
        if p["id"] in seen:
            errors.append(f"{where}.id: duplicate pairing id {p['id']!r}")
        seen.add(p["id"])
        if p["isolation_mode"] not in ISOLATION_MODES:
            errors.append(f"{where}.isolation_mode: unknown mode")
        errors += _budget_errors(where, p)
        instruction = p["instruction"]
        if not isinstance(instruction, dict) or any(
            k not in instruction for k in ("variant", "skill_index_mode", "hash", "bytes", "tokens_estimated")
        ):
            errors.append(f"{where}.instruction: variant, skill_index_mode, hash, bytes, tokens_estimated required")
        elif not (isinstance(instruction["hash"], str) and _HASH.match(instruction["hash"])):
            errors.append(f"{where}.instruction.hash: must be sha256:<64 hex>")
        if not (is_unavailable(p["tool_schema_hash"]) or (isinstance(p["tool_schema_hash"], str) and _HASH.match(p["tool_schema_hash"]))):
            errors.append(f"{where}.tool_schema_hash: hash or explicit unavailable object")
        errors += _harness_errors(where, p["harness"])
    return errors


def _harness_errors(where: str, harness: Any) -> list[str]:
    if not isinstance(harness, dict) or any(k not in harness for k in ("name", "version", "adapter", "adapter_version")):
        return [f"{where}.harness: name, version, adapter, adapter_version required"]
    return []


def _budget_errors(where: str, p: dict) -> list[str]:
    budgets = p["budgets"]
    if not isinstance(budgets, dict) or any(k not in budgets for k in ("time_s", "turns", "spend_usd", "spend_enforcement")):
        return [f"{where}.budgets: time_s, turns, spend_usd, spend_enforcement required"]
    errors = []
    if budgets["spend_enforcement"] not in SPEND_ENFORCEMENT:
        errors.append(f"{where}.budgets.spend_enforcement: unknown value")
    if p["isolation_mode"] == "metered-live" and budgets["spend_enforcement"] not in ("provider", "adapter"):
        errors.append(f"{where}.budgets: metered-live requires provider- or adapter-enforced spend control")
    if p["isolation_mode"] == "metered-live" and not (is_number(budgets["spend_usd"]) and budgets["spend_usd"] > 0):
        errors.append(f"{where}.budgets.spend_usd: metered-live requires a positive hard limit")
    return errors


# ---------------------------------------------------------------- comparison groups


def environment_identity(manifest: dict, pairing: dict) -> tuple:
    """Everything that must match for a direct comparison."""
    env = dict(manifest["environment"])
    env.update(pairing.get("environment_override", {}))
    workload = manifest["workload"]
    return (
        workload["hash"],
        workload["evaluator_hash"],
        workload["budget_class"],
        env["os"],
        env["arch"],
        repr(sorted(env["model_parameters"].items())),
        env["cache_policy"],
        env["retry_policy"],
        env["concurrency"],
        repr(env["pricing"]),
    )


def comparison_groups(manifest: dict) -> dict[tuple, list[str]]:
    groups: dict[tuple, list[str]] = {}
    for p in manifest["pairings"]:
        groups.setdefault(environment_identity(manifest, p), []).append(p["id"])
    return groups


def pairing_incomparable_reasons(manifest: dict, pairing: dict) -> list[str]:
    reasons = []
    if is_unavailable(manifest["environment"]["pricing"]):
        reasons.append("pricing snapshot unavailable")
    if is_unavailable(pairing["tool_schema_hash"]):
        reasons.append("tool-schema hash unavailable")
    if is_unavailable(pairing["harness"]["version"]):
        reasons.append("harness version unavailable")
    return reasons


def expected_order(manifest: dict) -> list[str]:
    """Pairing id for each order_position, per the manifest's order policy."""
    ids = [p["id"] for p in manifest["pairings"]]
    order: list[str] = []
    for round_index in range(manifest["repeats"]):
        if manifest["order_policy"] == "alternating":
            order += ids if round_index % 2 == 0 else list(reversed(ids))
        else:
            shuffled = list(ids)
            random.Random(f"{manifest['seed']}:{round_index}").shuffle(shuffled)
            order += shuffled
    return order


# ------------------------------------------------------------------------ trials


def validate_trial(t: Any, manifest: dict | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(t, dict):
        return ["$: trial must be an object"]
    for key in TRIAL_KEYS:
        if key not in t:
            errors.append(f"$.{key}: required")
    extra = sorted(set(t) - set(TRIAL_KEYS))
    if extra:
        errors.append(f"$: non-allowlisted keys {extra}")
    if errors:
        return errors
    if t["schema"] != SCHEMAS["trial"]:
        errors.append("$.schema: unsupported schema version")
    errors += _text_errors(t)
    if t["outcome"] not in OUTCOMES:
        errors.append("$.outcome: unknown outcome")
    if t["isolation_mode"] not in ISOLATION_MODES:
        errors.append("$.isolation_mode: unknown mode")
    if t["evaluator_success"] not in (True, False, None):
        errors.append("$.evaluator_success: true, false, or null")
    if t["outcome"] == "success" and t["evaluator_success"] is not True:
        errors.append("$.outcome: success without evaluator confirmation (forged success)")
    if t["outcome"] != "success" and t["evaluator_success"] is True:
        errors.append("$.evaluator_success: true while outcome is not success")
    for key in ("latency_s", "cost_usd", "tool_schema_bytes"):
        if not _num_or_unavailable(t[key]):
            errors.append(f"$.{key}: non-negative number or explicit unavailable object")
    for key in ("instruction_bytes", "instruction_tokens_estimated"):
        if not (isinstance(t[key], int) and t[key] >= 0):
            errors.append(f"$.{key}: non-negative integer")
    if t["isolation_mode"] == "synthetic" and not is_unavailable(t["cost_usd"]):
        errors.append("$.cost_usd: synthetic cost is not applicable and must be unavailable")
    if manifest is not None:
        errors += _trial_vs_manifest(t, manifest)
    return errors


def _trial_vs_manifest(t: dict, manifest: dict) -> list[str]:
    errors = []
    pairing = next((p for p in manifest["pairings"] if p["id"] == t["pairing_id"]), None)
    if pairing is None:
        return [f"$.pairing_id: unknown pairing {t['pairing_id']!r}"]
    if t["workload_hash"] != manifest["workload"]["hash"]:
        errors.append("$.workload_hash: differs from the manifest (mixed comparison group)")
    if t["isolation_mode"] != pairing["isolation_mode"]:
        errors.append("$.isolation_mode: differs from the manifest pairing")
    order = expected_order(manifest)
    position = t["order_position"]
    if not (isinstance(position, int) and 0 <= position < len(order)) or order[position] != t["pairing_id"]:
        errors.append("$.order_position: trial order drifts from the manifest order policy")
    budgets = pairing["budgets"]
    if is_number(t["latency_s"]) and t["latency_s"] > budgets["time_s"] and t["outcome"] != "timeout":
        errors.append("$.latency_s: exceeds the time budget but outcome is not timeout")
    spend = budgets["spend_usd"]
    if is_number(t["cost_usd"]) and is_number(spend) and t["cost_usd"] > spend and t["outcome"] != "budget-exhausted":
        errors.append("$.cost_usd: exceeds the spend budget but outcome is not budget-exhausted")
    if t["instruction_bytes"] != pairing["instruction"]["bytes"]:
        errors.append("$.instruction_bytes: differs from the manifest instruction record")
    return errors


# ------------------------------------------------------------------ statistics


def wilson_interval(successes: int, n: int, z: float = Z95) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("n must be positive")
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def bootstrap_mean_interval(values: list[float], seed_text: str) -> tuple[float, float]:
    """Fixed-seed percentile bootstrap of the mean (2000 resamples, 95%)."""
    rng = random.Random(seed_text)
    n = len(values)
    means = sorted(
        sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOTSTRAP_RESAMPLES)
    )
    low = means[math.floor(0.025 * BOOTSTRAP_RESAMPLES)]
    high = means[math.ceil(0.975 * BOOTSTRAP_RESAMPLES) - 1]
    return low, high


def _r(x: float) -> float:
    return round(x, 6)


def _metric_block(values: list[Any], seed_text: str) -> dict[str, Any]:
    """Mean and bootstrap interval, or unavailable if any value is missing."""
    if not values:
        return {"mean": unavailable("no trials"), "ci95": unavailable("no trials")}
    if any(not is_number(v) for v in values):
        return {"mean": unavailable("a trial lacks this value"), "ci95": unavailable("a trial lacks this value")}
    low, high = bootstrap_mean_interval([float(v) for v in values], seed_text)
    return {"mean": _r(sum(values) / len(values)), "ci95": [_r(low), _r(high)]}


def aggregate_pairing(manifest: dict, pairing: dict, trials: list[dict]) -> dict[str, Any]:
    mine = [t for t in trials if t["pairing_id"] == pairing["id"]]
    rankable = [t for t in mine if t["evaluator_success"] is not None]
    successes = sum(1 for t in rankable if t["evaluator_success"] is True)
    out: dict[str, Any] = {
        "pairing_id": pairing["id"],
        "isolation_mode": pairing["isolation_mode"],
        "trials": len(mine),
        "rankable_trials": len(rankable),
        "non_rankable_trials": len(mine) - len(rankable),
        "successes": successes,
        "instruction_bytes": pairing["instruction"]["bytes"],
        "instruction_tokens_estimated": pairing["instruction"]["tokens_estimated"],
    }
    if rankable:
        low, high = wilson_interval(successes, len(rankable))
        out["success_rate"] = _r(successes / len(rankable))
        out["success_ci95"] = [_r(low), _r(high)]
    else:
        out["success_rate"] = unavailable("no rankable trial")
        out["success_ci95"] = unavailable("no rankable trial")
    out["latency_s"] = _metric_block([t["latency_s"] for t in rankable], f"{manifest['seed']}:{pairing['id']}:latency")
    costs = [t["cost_usd"] for t in rankable]
    out["cost_usd"] = _metric_block(costs, f"{manifest['seed']}:{pairing['id']}:cost")
    out["cost_per_success_usd"] = _cost_per_success(costs, successes)
    out["failure_fingerprints"] = sorted({t["failure_fingerprint"] for t in mine if t["failure_fingerprint"]})
    out["organic_skills"] = _organic(mine)
    return out


def _cost_per_success(costs: list[Any], successes: int) -> Any:
    if not costs or any(not is_number(c) for c in costs):
        return unavailable("cost unavailable for at least one trial")
    if successes == 0:
        return unavailable("no successful task")
    return _r(sum(costs) / successes)


def _organic(trials: list[dict]) -> Any:
    if any(t["organic_skills"] is None for t in trials):
        return unavailable("needs-live-validation")
    return sorted({s for t in trials for s in t["organic_skills"]})


# -------------------------------------------------------------- eligibility and rank


def qualifies(manifest: dict, agg: dict) -> bool:
    policy = manifest["workload"]["policy"]
    if not is_number(agg["success_rate"]) or agg["success_rate"] < policy["min_success_rate"]:
        return False
    latency = agg["latency_s"]["mean"]
    if not is_number(latency) or latency > policy["max_latency_s"]:
        return False
    cap = policy["max_cost_usd"]
    if cap is not None:
        cost = agg["cost_per_success_usd"]
        if not is_number(cost) or cost > cap or agg["isolation_mode"] != "metered-live":
            return False
    return True


def _dims(agg: dict, with_cost: bool) -> list[float]:
    dims = [agg["success_rate"], -agg["latency_s"]["mean"], -agg["instruction_tokens_estimated"]]
    if with_cost:
        dims.append(-agg["cost_per_success_usd"])
    return dims


def pareto_frontier(aggs: list[dict]) -> list[str]:
    with_cost = all(is_number(a["cost_per_success_usd"]) for a in aggs)
    frontier = []
    for a in aggs:
        da = _dims(a, with_cost)
        dominated = any(
            all(x >= y for x, y in zip(_dims(b, with_cost), da))
            and any(x > y for x, y in zip(_dims(b, with_cost), da))
            for b in aggs
            if b is not a
        )
        if not dominated:
            frontier.append(a["pairing_id"])
    return sorted(frontier)


def _tie_value(agg: dict, tie_break: str) -> tuple[float, tuple[float, float] | None]:
    if tie_break == "lowest-instruction-tokens":
        v = float(agg["instruction_tokens_estimated"])
        return v, (v, v)
    if tie_break == "lowest-latency":
        return agg["latency_s"]["mean"], tuple(agg["latency_s"]["ci95"])
    if tie_break == "highest-success-rate":
        return -agg["success_rate"], (-agg["success_ci95"][1], -agg["success_ci95"][0])
    cost = agg["cost_usd"]["ci95"]
    return agg["cost_per_success_usd"], tuple(cost) if isinstance(cost, list) else None


def recommend(manifest: dict, aggs: list[dict]) -> dict[str, Any]:
    """A recommendation exists only when every restraint rule is satisfied."""
    repeats_ok = all(a["rankable_trials"] >= MIN_REPEATS_FOR_RECOMMENDATION for a in aggs)
    if len(comparison_groups(manifest)) != 1:
        return {"state": "no-recommendation", "reason": "incomparable comparison groups"}
    if any(pairing_incomparable_reasons(manifest, p) for p in manifest["pairings"]):
        return {"state": "no-recommendation", "reason": "incomparable: unavailable identity or pricing data"}
    if any(p["isolation_mode"] != "metered-live" for p in manifest["pairings"]):
        return {"state": "no-recommendation", "reason": "evidence mode is not metered-live"}
    if not repeats_ok:
        return {"state": "no-recommendation", "reason": "fewer than three repeats"}
    good = [a for a in aggs if qualifies(manifest, a)]
    if not good:
        return {"state": "no-recommendation", "reason": "no pairing meets the predeclared gates"}
    frontier = set(pareto_frontier(good))
    tie = manifest["workload"]["policy"]["tie_break"]
    candidates = [a for a in good if a["pairing_id"] in frontier]
    best = min(candidates, key=lambda a: _tie_value(a, tie)[0])
    for other in good:
        if other is best:
            continue
        b_ci, o_ci = _tie_value(best, tie)[1], _tie_value(other, tie)[1]
        if b_ci is None or o_ci is None or not (b_ci[1] < o_ci[0]):
            return {"state": "no-recommendation", "reason": "95% intervals overlap on the tie-break"}
    return {"state": "recommended", "pairing_id": best["pairing_id"]}


def aggregate(manifest: dict, trials: list[dict]) -> dict[str, Any]:
    aggs = [aggregate_pairing(manifest, p, trials) for p in manifest["pairings"]]
    return {
        "schema": SCHEMAS["aggregate"],
        "run_id": manifest["run_id"],
        "workload_hash": manifest["workload"]["hash"],
        "comparison_groups": len(comparison_groups(manifest)),
        "pairings": aggs,
        "qualifying": sorted(a["pairing_id"] for a in aggs if qualifies(manifest, a)),
        "pareto_frontier": pareto_frontier([a for a in aggs if qualifies(manifest, a)]),
        "recommendation": recommend(manifest, aggs),
    }


def strip_private(manifest: dict) -> dict:
    """Manifest fields the distributable report may carry (hashes, never payloads)."""
    return {k: manifest[k] for k in ("run_id", "workload", "environment")}


# ------------------------------------------------------------ measurer consistency


def measurer_tokens(text: str) -> int:
    """Estimated tokens for ``text`` using scripts/measure_rendered_context.py."""
    repo = Path(__file__).resolve().parents[3]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from scripts.measure_rendered_context import measure

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "instruction.md"
        target.write_bytes(text.encode("utf-8"))
        report = measure(target, False, None)
    if report.get("status") != "ok":
        raise ValueError(f"measurer could not read the file: {report}")
    return int(report["tokens"])
