"""Phase 5 (T018): the compression accuracy-regression harness and its gate.

These tests prove the harness measures the engine's fidelity (CCR round-trip +
signature preservation) and effectiveness, that the committed baseline passes on
the healthy engine, and -- the load-bearing test -- that the gate CATCHES a
broken, irreversible compressor instead of silently shipping it. No live LLM call
is involved; every check is deterministic and offline.
"""

from __future__ import annotations

import json

from evals.runner import (
    EvalReport,
    FixtureScore,
    check_baseline,
    load_baseline,
    main,
    render_json,
    render_report,
    run_eval,
)

_FIXTURE_NAMES = {"json_logs", "search_hits", "python_module", "typescript_module"}


def test_harness_runs_all_fixtures():
    report = run_eval()
    assert {f.name for f in report.fixtures} == _FIXTURE_NAMES


def test_healthy_engine_has_perfect_fidelity():
    report = run_eval()
    assert report.ccr_roundtrip == 1.0
    assert report.signature_preservation == 1.0


def test_every_fixture_actually_compressed_and_exercised_ccr():
    # Guards against a fixture going vacuous: if nothing were dropped the
    # round-trip metric would be trivially 1.0 while testing nothing. Pin that
    # each fixture really shrank and really exercised a reversibility check.
    report = run_eval()
    for f in report.fixtures:
        assert f.kept_units < f.original_units, f"{f.name} did not compress"
        assert f.ccr_checks_total > 0, f"{f.name} dropped nothing reversible"
    for f in (f for f in report.fixtures if f.kind == "code"):
        assert f.signature_total > 0, f"{f.name} declared no signatures to preserve"


def test_committed_baseline_passes_on_healthy_engine():
    assert check_baseline(run_eval(), load_baseline()) == []


def test_baseline_pins_fidelity_at_one():
    baseline = load_baseline()
    assert baseline["fidelity"]["ccr_roundtrip"] == 1.0
    assert baseline["fidelity"]["signature_preservation"] == 1.0
    floor = baseline["effectiveness"]["min_aggregate_char_reduction"]
    assert 0.0 < floor <= 1.0


class _NoOpStore:
    """A broken store that discards every ``put`` -- an irreversible compressor.

    The engine still drops spans (compression appears to "work"), but the
    originals are gone, so no marker can be resolved. This is exactly the
    silent-data-loss regression the accuracy gate exists to catch.
    """

    def put(self, span_hash: str, original: list) -> None:
        return None

    def get(self, span_hash: str) -> list | None:
        return None


def test_gate_catches_an_irreversible_compressor():
    report = run_eval(store=_NoOpStore())
    assert report.ccr_roundtrip < 1.0
    failures = check_baseline(report, load_baseline())
    assert failures, "an irreversible compressor must fail the gate"
    assert any("round-trip" in f for f in failures)


def test_gate_catches_a_below_floor_compressor():
    # A synthetic report whose effectiveness sits below the floor must be flagged
    # even though its fidelity is (trivially) perfect.
    weak = EvalReport(
        fixtures=[
            FixtureScore(
                name="noop",
                kind="json_array",
                original_units=10,
                kept_units=10,
                char_before=100,
                char_after=99,
                ccr_checks_total=1,
                ccr_checks_ok=1,
            )
        ]
    )
    failures = check_baseline(weak, load_baseline())
    assert any("effectiveness" in f for f in failures)


def test_per_slice_floor_fails_when_aggregate_still_passes():
    # Four fixtures whose mean still clears the 0.36 aggregate floor, but one
    # named slice sits under its per-slice floor. The gate must fail on the
    # slice, not let the mean hide it.
    healthy = FixtureScore(
        name="json_logs",
        kind="json_array",
        original_units=10,
        kept_units=2,
        char_before=1000,
        char_after=200,
        ccr_checks_total=1,
        ccr_checks_ok=1,
    )
    weak = FixtureScore(
        name="typescript_module",
        kind="code",
        original_units=10,
        kept_units=9,
        char_before=1000,
        char_after=950,
        ccr_checks_total=1,
        ccr_checks_ok=1,
        signature_total=1,
        signature_ok=1,
    )
    filler = FixtureScore(
        name="search_hits",
        kind="json_array",
        original_units=10,
        kept_units=2,
        char_before=1000,
        char_after=200,
        ccr_checks_total=1,
        ccr_checks_ok=1,
    )
    filler2 = FixtureScore(
        name="python_module",
        kind="code",
        original_units=10,
        kept_units=2,
        char_before=1000,
        char_after=200,
        ccr_checks_total=1,
        ccr_checks_ok=1,
        signature_total=1,
        signature_ok=1,
    )
    report = EvalReport(fixtures=[healthy, weak, filler, filler2])
    assert report.mean_char_reduction > 0.36
    failures = check_baseline(report, load_baseline())
    assert any("per-slice typescript_module" in f for f in failures)
    assert any("aggregate may still pass" in f for f in failures)


def test_baseline_declares_per_slice_floors():
    baseline = load_baseline()
    assert baseline["corpus_version"] == 1
    slices = baseline["per_slice"]
    assert set(slices) == _FIXTURE_NAMES
    for floors in slices.values():
        assert 0.0 < floors["min_char_reduction"] <= 1.0
        assert floors["min_ccr_roundtrip"] == 1.0


def test_signature_failure_is_detected():
    # If a code fixture loses a structural line, signature preservation drops and
    # the gate flags it. Simulate the degraded score directly.
    degraded = EvalReport(
        fixtures=[
            FixtureScore(
                name="broken_code",
                kind="code",
                char_before=100,
                char_after=20,
                signature_total=10,
                signature_ok=9,
                ccr_checks_total=1,
                ccr_checks_ok=1,
            )
        ]
    )
    failures = check_baseline(degraded, load_baseline())
    assert any("Signature preservation" in f for f in failures)


def test_cli_check_passes_on_healthy_engine():
    assert main(["--check"]) == 0


def test_cli_json_mode_emits_metrics(capsys):
    assert main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ccr_roundtrip"] == 1.0
    assert payload["signature_preservation"] == 1.0
    assert len(payload["fixtures"]) == len(_FIXTURE_NAMES)


def test_rendered_report_is_ascii_and_states_the_verdict():
    text = render_report(run_eval(), load_baseline())
    assert text.isascii(), "the Markdown report must be ASCII per the repo style"
    assert "PASS" in text


def test_render_json_is_serializable():
    payload = render_json(run_eval())
    json.dumps(payload)  # must not raise
    assert payload["mean_char_reduction"] > 0.0
