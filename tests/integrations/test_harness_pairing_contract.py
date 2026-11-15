"""Contract tests for harness-pairing evaluation (v4.15.2, Phase 2).

These tests hold the durable contract in guides/reference/HARNESS_PAIRING_EVALUATION.md
against frozen local fixtures and an independent oracle
(tests/fixtures/harness_pairings/oracle.py). They need no network, provider
credential, or harness binary. Every mutation test names the contract rule it
violates; a mutation that passes validation is a test failure.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "harness_pairings"
GUIDE = ROOT / "guides" / "reference" / "HARNESS_PAIRING_EVALUATION.md"
AUDIT_SKILL = ROOT / "catalog" / "skills" / "ai-development" / "eval-pipeline-audit" / "SKILL.md"

_spec = importlib.util.spec_from_file_location("harness_pairing_oracle", FIXTURES / "oracle.py")
oracle = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(oracle)


def _canary_key() -> str:
    """A secret-shaped canary assembled at runtime so no literal sits in source."""
    return "api_key=" + "s" + "k-" + "abcdefghijklmnopqrstuvwxyz"


def _canary_bearer() -> str:
    return "Authorization " + "Bear" + "er " + "abcdefghijklmnopqrstu"


def _load(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


@pytest.fixture()
def manifest() -> dict:
    return _load("manifest.valid.json")


@pytest.fixture()
def trials() -> list[dict]:
    return _load("trials.valid.json")


# ------------------------------------------------------------------ manifests


def test_valid_manifest_passes_and_binds_every_identity_field(manifest: dict) -> None:
    assert oracle.validate_manifest(manifest) == []
    for key in ("os", "arch", "repo_revision", "harness_configuration", "model_parameters",
                "cache_policy", "concurrency", "retry_policy", "pricing"):
        assert key in manifest["environment"]
    for pairing in manifest["pairings"]:
        assert pairing["instruction"]["skill_index_mode"] in ("full", "pointer")
        assert {"version", "adapter", "adapter_version"} <= set(pairing["harness"])
    assert manifest["repeats"] >= 3
    assert manifest["order_policy"] in oracle.ORDER_POLICIES


@pytest.mark.parametrize("path", [
    ("workload",), ("environment",), ("pairings",), ("repeats",), ("seed",), ("order_policy",),
    ("workload", "hash"), ("workload", "policy"), ("environment", "pricing"),
    ("environment", "repo_revision"), ("environment", "cache_policy"),
])
def test_missing_identity_or_budget_field_rejects_the_manifest(manifest: dict, path: tuple) -> None:
    node = manifest
    for key in path[:-1]:
        node = node[key]
    del node[path[-1]]
    errors = oracle.validate_manifest(manifest)
    assert errors, f"removing {'.'.join(path)} must reject the manifest"
    assert any(path[-1] in e for e in errors), errors


def test_missing_budget_fields_reject_a_pairing(manifest: dict) -> None:
    del manifest["pairings"][0]["budgets"]["time_s"]
    assert any("budgets" in e for e in oracle.validate_manifest(manifest))


def test_partial_manifest_is_valid_but_marks_the_affected_pairings_incomparable() -> None:
    partial = _load("manifest.partial.json")
    assert oracle.validate_manifest(partial) == []
    reasons = [oracle.pairing_incomparable_reasons(partial, p) for p in partial["pairings"]]
    assert "pricing snapshot unavailable" in reasons[0]
    assert "tool-schema hash unavailable" in reasons[0]
    assert "harness version unavailable" in reasons[1]


def test_incomparable_manifest_splits_into_separate_comparison_groups() -> None:
    incomparable = _load("manifest.incomparable.json")
    assert oracle.validate_manifest(incomparable) == []
    assert len(oracle.comparison_groups(incomparable)) == 2
    result = oracle.aggregate(incomparable, [])
    assert result["recommendation"]["reason"] == "incomparable comparison groups"


def test_conflicting_pairing_ids_and_schema_versions_are_rejected_not_merged(manifest: dict) -> None:
    clone = copy.deepcopy(manifest)
    clone["pairings"][1]["id"] = clone["pairings"][0]["id"]
    assert any("duplicate pairing id" in e for e in oracle.validate_manifest(clone))
    clone = copy.deepcopy(manifest)
    clone["schema"] = "harness-pairing-manifest/2"
    assert any("unsupported schema" in e for e in oracle.validate_manifest(clone))


def test_metered_live_requires_a_pre_spend_limit_not_a_post_hoc_one(manifest: dict) -> None:
    live = copy.deepcopy(manifest)
    live["pairings"][0]["isolation_mode"] = "metered-live"
    live["pairings"][0]["budgets"].update(spend_usd=5.0, spend_enforcement="none")
    assert any("provider- or adapter-enforced" in e for e in oracle.validate_manifest(live))
    live["pairings"][0]["budgets"]["spend_enforcement"] = "provider"
    assert oracle.validate_manifest(live) == []


# --------------------------------------------------- instruction payload and measurer


def _instruction_disagreements(manifest: dict) -> list[str]:
    problems = []
    for pairing in manifest["pairings"]:
        # Fixtures are LF in the repository; a Windows checkout may convert them.
        raw = (FIXTURES / "instructions" / f"{pairing['instruction']['variant']}.md").read_bytes()
        text = raw.replace(b"\r\n", b"\n")
        record = pairing["instruction"]
        if record["bytes"] != len(text):
            problems.append(f"{pairing['id']}: bytes {record['bytes']} != {len(text)}")
        if record["hash"] != "sha256:" + hashlib.sha256(text).hexdigest():
            problems.append(f"{pairing['id']}: hash differs from the file")
        measured = oracle.measurer_tokens(text.decode("utf-8"))
        if record["tokens_estimated"] != measured:
            problems.append(f"{pairing['id']}: tokens {record['tokens_estimated']} != measurer {measured}")
    return problems


def test_instruction_figures_agree_with_the_files_and_the_one_measurer(manifest: dict) -> None:
    assert _instruction_disagreements(manifest) == []


def test_a_figure_that_disagrees_with_the_measurer_is_detected(manifest: dict) -> None:
    manifest["pairings"][0]["instruction"]["tokens_estimated"] += 1
    manifest["pairings"][1]["instruction"]["bytes"] += 1
    problems = _instruction_disagreements(manifest)
    assert any("measurer" in p for p in problems)
    assert any("bytes" in p for p in problems)


def test_first_variant_pair_is_full_against_pointer_with_distinct_payloads(manifest: dict) -> None:
    modes = [p["instruction"]["skill_index_mode"] for p in manifest["pairings"]]
    assert modes == ["full", "pointer"]
    full, pointer = (p["instruction"] for p in manifest["pairings"])
    assert full["hash"] != pointer["hash"]
    assert full["tokens_estimated"] > pointer["tokens_estimated"]


# ------------------------------------------------------------------- trial receipts


def test_valid_trials_pass_against_the_manifest(manifest: dict, trials: list[dict]) -> None:
    for trial in trials:
        assert oracle.validate_trial(trial, manifest) == []
    assert [t["pairing_id"] for t in trials] == oracle.expected_order(manifest)


def _mutate(path: str, value):
    def apply(trial: dict) -> dict:
        trial[path] = value
        return trial
    return apply


def _delete(path: str):
    def apply(trial: dict) -> dict:
        del trial[path]
        return trial
    return apply


MUTATIONS = {
    "absent value": (_delete("latency_s"), "latency_s"),
    "forged success": (lambda t: {**t, "outcome": "success", "evaluator_success": False}, "forged success"),
    "harness claim cannot assert success": (lambda t: {**t, "outcome": "failure", "evaluator_success": True}, "evaluator_success"),
    "secret-shaped field": (lambda t: {**t, "failure_fingerprint": _canary_key()}, "secret-shaped"),
    "secret in bearer form": (lambda t: {**t, "failure_fingerprint": _canary_bearer()}, "secret-shaped"),
    "NUL byte": (_mutate("failure_fingerprint", "fp\x00hidden"), "control byte"),
    "ANSI escape": (_mutate("failure_fingerprint", "fp\x1b[31mred"), "ANSI escape"),
    "forged Markdown heading": (_mutate("failure_fingerprint", "ok\n## Recommendation"), "forged Markdown heading"),
    "oversized field": (_mutate("failure_fingerprint", "x" * 600), "oversized field"),
    "non-allowlisted key": (_mutate("raw_stdout", "everything the adapter printed"), "non-allowlisted"),
    "negative cost": (_mutate("cost_usd", -1.0), "cost_usd"),
    "budget overrun": (lambda t: {**t, "latency_s": 31.0}, "time budget"),
    "mixed comparison group": (_mutate("workload_hash", "sha256:" + "0" * 64), "mixed comparison group"),
    "trial order drift": (_mutate("order_position", 1), "order"),
    "instruction byte drift": (lambda t: {**t, "instruction_bytes": t["instruction_bytes"] + 1}, "instruction_bytes"),
    "unknown pairing": (_mutate("pairing_id", "pair-ghost"), "unknown pairing"),
    "synthetic cost must be unavailable": (_mutate("cost_usd", 0.0), "synthetic cost"),
}


@pytest.mark.parametrize("name", sorted(MUTATIONS))
def test_every_hostile_or_inconsistent_trial_mutation_is_rejected(
    manifest: dict, trials: list[dict], name: str
) -> None:
    mutate, expected = MUTATIONS[name]
    errors = oracle.validate_trial(mutate(copy.deepcopy(trials[0])), manifest)
    assert errors, f"mutation {name!r} passed validation"
    assert any(expected in e for e in errors), (name, errors)


def test_invalid_utf8_and_oversized_adapter_bytes_are_rejected_before_parsing() -> None:
    with pytest.raises(ValueError, match="invalid UTF-8"):
        oracle.decode_adapter_bytes(b"\xff\xfe not text")
    with pytest.raises(ValueError, match="oversized"):
        oracle.decode_adapter_bytes(b"a" * (64 * 1024 + 1))
    assert oracle.decode_adapter_bytes("caf\u00e9".encode()) == "caf\u00e9"


@pytest.mark.parametrize("value,escapes", [
    ("workspace/out.txt", False),
    ("../outside", True),
    ("a/../../b", True),
    ("/etc/passwd", True),
    ("C:\\Windows\\system32", True),
    ("sub\\dir\\file", False),
])
def test_path_escape_detection(value: str, escapes: bool) -> None:
    assert oracle.path_escapes(value) is escapes


# ------------------------------------------------------------ aggregates and oracle


def test_frozen_aggregates_equal_an_independent_recomputation(manifest: dict) -> None:
    assert oracle.aggregate(manifest, _load("trials.valid.json")) == _load("aggregate.valid.json")
    assert oracle.aggregate(manifest, _load("trials.partial.json")) == _load("aggregate.partial.json")


def test_wilson_interval_matches_closed_form_values() -> None:
    low, high = oracle.wilson_interval(2, 3)
    assert (round(low, 4), round(high, 4)) == (0.2077, 0.9385)
    low, high = oracle.wilson_interval(3, 3)
    assert (round(low, 4), round(high, 4)) == (0.4385, 1.0)
    low, high = oracle.wilson_interval(0, 3)
    assert (round(low, 4), round(high, 4)) == (0.0, 0.5615)


def test_bootstrap_interval_is_deterministic_and_bounded_by_the_sample() -> None:
    values = [10.0, 12.0, 14.0]
    first = oracle.bootstrap_mean_interval(values, "seed")
    assert first == oracle.bootstrap_mean_interval(values, "seed")
    assert 10.0 <= first[0] <= first[1] <= 14.0


def test_pairing_metrics_in_the_frozen_receipt_match_hand_arithmetic(manifest: dict, trials: list[dict]) -> None:
    agg = {p["pairing_id"]: p for p in oracle.aggregate(manifest, trials)["pairings"]}
    full, pointer = agg["pair-full"], agg["pair-pointer"]
    assert (full["successes"], full["rankable_trials"]) == (2, 3)
    assert full["success_rate"] == round(2 / 3, 6)
    assert full["latency_s"]["mean"] == round((12.5 + 14.0 + 13.0) / 3, 6)
    assert (pointer["successes"], pointer["success_rate"]) == (3, 1.0)
    assert pointer["latency_s"]["mean"] == round((11.0 + 11.5 + 12.0) / 3, 6)
    assert full["failure_fingerprints"] == ["fp-assert-mismatch-01"]


def test_missing_data_stays_unavailable_and_never_becomes_zero(manifest: dict, trials: list[dict]) -> None:
    result = oracle.aggregate(manifest, trials)
    for pairing in result["pairings"]:
        assert oracle.is_unavailable(pairing["cost_per_success_usd"])
        assert oracle.is_unavailable(pairing["cost_usd"]["mean"])
        assert oracle.is_unavailable(pairing["organic_skills"])
        assert pairing["organic_skills"]["unavailable"] == "needs-live-validation"


def _trial(live: dict, pid: str, position: int, index: int, **over) -> dict:
    pairing = next(p for p in live["pairings"] if p["id"] == pid)
    base = {
        "schema": oracle.SCHEMAS["trial"], "run_id": live["run_id"],
        "workload_hash": live["workload"]["hash"], "pairing_id": pid,
        "trial_index": index, "order_position": position, "seed": position,
        "isolation_mode": "metered-live", "outcome": "success",
        "evaluator_success": True, "harness_claim_success": True,
        "latency_s": 10.0, "cost_usd": 0.25,
        "instruction_bytes": pairing["instruction"]["bytes"],
        "instruction_tokens_estimated": pairing["instruction"]["tokens_estimated"],
        "tool_schema_bytes": 100, "organic_skills": [], "guard_skills": [],
        "failure_fingerprint": "", "started_at": "t", "ended_at": "t",
    }
    base.update(over)
    return base


def _live_manifest(manifest: dict, tie_break: str = "lowest-cost-per-success") -> dict:
    live = copy.deepcopy(manifest)
    live["workload"]["policy"]["tie_break"] = tie_break
    for p in live["pairings"]:
        p["isolation_mode"] = "metered-live"
        p["budgets"].update(spend_usd=5.0, spend_enforcement="provider")
    return live


def _live_trials(live: dict, costs: dict[str, list[float]], **over) -> list[dict]:
    counters = {pid: 0 for pid in costs}
    out = []
    for position, pid in enumerate(oracle.expected_order(live)):
        index = counters[pid]
        counters[pid] += 1
        out.append(_trial(live, pid, position, index, cost_usd=costs[pid][index], **over))
    return out


def test_no_successful_task_makes_cost_per_success_unavailable_not_zero_or_infinite(manifest: dict) -> None:
    live = _live_manifest(manifest)
    failing = _live_trials(
        live,
        {"pair-full": [0.25] * 3, "pair-pointer": [0.25] * 3},
        outcome="failure", evaluator_success=False, failure_fingerprint="fp-x",
    )
    for pairing in oracle.aggregate(live, failing)["pairings"]:
        value = pairing["cost_per_success_usd"]
        assert oracle.is_unavailable(value) and value["unavailable"] == "no successful task"


def test_evaluator_gap_makes_a_trial_non_rankable_and_a_timeout_stays_in_the_report(manifest: dict) -> None:
    partial = oracle.aggregate(manifest, _load("trials.partial.json"))
    by_id = {p["pairing_id"]: p for p in partial["pairings"]}
    assert sum(p["non_rankable_trials"] for p in by_id.values()) == 1
    assert sum(p["trials"] for p in by_id.values()) == 5
    assert (by_id["pair-full"]["successes"], by_id["pair-pointer"]["successes"]) == (1, 2)
    timeouts = [t for t in _load("trials.partial.json") if t["outcome"] == "timeout"]
    assert len(timeouts) == 1 and by_id["pair-full"]["trials"] == 3


def _aggregate_consistency_errors(agg: dict) -> list[str]:
    errors = []
    for p in agg["pairings"]:
        if p["successes"] > p["rankable_trials"]:
            errors.append(f"{p['pairing_id']}: successes exceed rankable trials")
        if p["rankable_trials"] + p["non_rankable_trials"] != p["trials"]:
            errors.append(f"{p['pairing_id']}: trial totals do not add up")
    return errors


def test_inconsistent_aggregate_totals_are_detected(manifest: dict, trials: list[dict]) -> None:
    good = oracle.aggregate(manifest, trials)
    assert _aggregate_consistency_errors(good) == []
    bad = copy.deepcopy(good)
    bad["pairings"][0]["successes"] = 9
    bad["pairings"][1]["non_rankable_trials"] = 2
    assert len(_aggregate_consistency_errors(bad)) == 2


# ------------------------------------------------- eligibility and ranking restraint


def test_synthetic_evidence_never_yields_a_recommendation(manifest: dict, trials: list[dict]) -> None:
    result = oracle.aggregate(manifest, trials)
    assert result["recommendation"] == {
        "state": "no-recommendation", "reason": "evidence mode is not metered-live"}
    assert result["pareto_frontier"] == ["pair-pointer"]
    assert result["qualifying"] == ["pair-full", "pair-pointer"]


def test_a_recommendation_requires_non_overlapping_intervals_on_the_tie_break(manifest: dict) -> None:
    live = _live_manifest(manifest)
    assert oracle.validate_manifest(live) == []
    separated = _live_trials(live, {"pair-full": [0.10] * 3, "pair-pointer": [0.50] * 3})
    for t in separated:
        assert oracle.validate_trial(t, live) == [], oracle.validate_trial(t, live)
    chosen = oracle.aggregate(live, separated)["recommendation"]
    assert chosen == {"state": "recommended", "pairing_id": "pair-full"}
    overlapping = _live_trials(live, {"pair-full": [0.10, 0.30, 0.20], "pair-pointer": [0.15, 0.25, 0.35]})
    assert oracle.aggregate(live, overlapping)["recommendation"]["reason"] == (
        "95% intervals overlap on the tie-break")


def test_fewer_than_three_repeats_cannot_yield_a_recommendation(manifest: dict) -> None:
    live = _live_manifest(manifest)
    live["repeats"] = 2
    trials = _live_trials(live, {"pair-full": [0.1, 0.1], "pair-pointer": [0.5, 0.5]})
    assert oracle.aggregate(live, trials)["recommendation"] == {
        "state": "no-recommendation", "reason": "fewer than three repeats"}


def test_observational_live_cannot_satisfy_the_recommendation_gate(manifest: dict) -> None:
    live = _live_manifest(manifest)
    live["pairings"][0]["isolation_mode"] = "observational-live"
    live["pairings"][0]["budgets"].update(spend_enforcement="none")
    trials = _live_trials(live, {"pair-full": [0.1] * 3, "pair-pointer": [0.5] * 3})
    assert oracle.aggregate(live, trials)["recommendation"]["reason"] == "evidence mode is not metered-live"


def test_a_pairing_below_the_predeclared_gate_does_not_qualify(manifest: dict, trials: list[dict]) -> None:
    strict = copy.deepcopy(manifest)
    strict["workload"]["policy"]["min_success_rate"] = 0.9
    assert oracle.aggregate(strict, trials)["qualifying"] == ["pair-pointer"]


def test_price_date_and_budget_class_split_comparison_groups(manifest: dict) -> None:
    for key, value in (("pricing", {"basis": "other", "date": "2026-12-01"}), ("cache_policy", "warm"),
                       ("retry_policy", "twice"), ("concurrency", 2)):
        split = copy.deepcopy(manifest)
        split["pairings"][1]["environment_override"] = {key: value}
        assert len(oracle.comparison_groups(split)) == 2, key
    assert len(oracle.comparison_groups(manifest)) == 1


def test_seeded_random_order_is_reproducible_and_a_permutation_per_round(manifest: dict) -> None:
    seeded = copy.deepcopy(manifest)
    seeded["order_policy"] = "seeded-random"
    order = oracle.expected_order(seeded)
    assert order == oracle.expected_order(seeded)
    for round_index in range(seeded["repeats"]):
        chunk = order[round_index * 2:(round_index + 1) * 2]
        assert sorted(chunk) == ["pair-full", "pair-pointer"]


def test_distributable_manifest_view_carries_hashes_not_instruction_payloads(manifest: dict) -> None:
    view = oracle.strip_private(manifest)
    assert "pairings" not in view
    assert "Skill Index" not in json.dumps(view)


# ----------------------------------------------------------------- documents


GUIDE_REQUIRED_HEADINGS = (
    "## Evaluation modes",
    "## Manifest",
    "## Trial receipt",
    "## Aggregate receipt",
    "## Metrics",
    "## Comparison eligibility",
    "## Adapter and isolation boundary",
    "## Unavailable values",
)


def test_guide_has_a_dense_header_summary_and_every_contract_section() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    head = "\n".join(text.splitlines()[:12])
    assert "Summary:" in head and "Read this when:" in head and "Covers:" in head
    for heading in GUIDE_REQUIRED_HEADINGS:
        assert heading in text, f"guide lacks section {heading!r}"


def test_guide_states_the_hard_rules_the_oracle_enforces() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    for needle in (
        "shell=True",
        "argv array",
        "95% Wilson interval",
        "fixed-seed percentile bootstrap",
        "three repeats",
        "workload-owned deterministic evaluator",
        "scripts/measure_rendered_context.py --json",
        "NEXUS_HUB_SKILL_INDEX=full",
        "needs-live-validation",
        "observational-live",
        "never becomes zero",
        "scripts/harness_audit.py",
    ):
        assert needle in text, f"guide does not state: {needle}"


def test_audit_skill_routes_behavioral_pairing_evidence_without_embedding_mechanics() -> None:
    text = AUDIT_SKILL.read_text(encoding="utf-8")
    assert "guides/reference/HARNESS_PAIRING_EVALUATION.md" in text
    assert "scripts/evaluate_harness_pairings.py" in text
    assert "scripts/harness_audit.py" in text
    assert "Wilson" not in text and "bootstrap" not in text, (
        "the audit skill routes; interval mechanics belong to the guide"
    )
    assert "not covered" in text


def test_guide_links_resolve() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    for needle in ("tests/fixtures/harness_pairings/", "tests/integrations/test_harness_pairing_contract.py"):
        assert needle in text
        assert (ROOT / needle).exists(), needle
