"""Compression accuracy-regression harness for nexus-context-compressor.

This is the Phase 5 benchmark gate (adoption-headroom T016/T017). It proves that
the engine's compression *preserves answer quality* so aggressive ratios can ship
safely. headroom's own ``eval.yml`` measures accuracy by running GSM8K / SQuAD /
BFCL through a live model; we deliberately do NOT do that. A live LLM call is
non-deterministic, slow, and -- for this repo -- an outbound call we refuse to
add. Instead the harness leans on a property the engine *guarantees* and checks
it exactly, offline, and reproducibly:

* **CCR round-trip completeness.** Every dropped span is reversible. For a JSON
  array, ``reconstruct(compress(x)) == x``; for an elided code body, the CCR
  marker resolves back to the exact original lines. A compressor that drops data
  irreversibly fails here.
* **Signature-preservation rate.** The CodeCompressor keeps every import,
  decorator, class header, and function/method signature in its skeleton. A
  compressor that mangles structure fails here.
* **Compression effectiveness.** A character-length reduction (tokenizer-free, so
  it is identical on every machine) confirms the engine still actually compresses
  -- a no-op "compressor" that preserves fidelity trivially is caught by the
  effectiveness floor.

The gate (:func:`check_baseline`) compares a run against the committed
``baseline.json`` and fails CI on any regression: fidelity must stay exact
(1.0), and effectiveness must stay above a documented floor. To update a baseline
intentionally after a legitimate behavior change, run with ``--update-baseline``
and review the diff.

Run it:

    cd extensions/nexus-context-compressor && python -m evals --check
    cd extensions/nexus-context-compressor && python -m evals --out report.md
    cd extensions/nexus-context-compressor && python -m evals --json
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# The harness lives at extensions/nexus-context-compressor/evals/; the engine
# package lives one level up under src/. Bootstrap that onto sys.path so the
# harness runs from a bare checkout (no install, no PYTHONPATH) exactly like the
# test conftest does. A real install simply finds the package first.
_PKG_SRC = Path(__file__).resolve().parents[1] / "src"
if _PKG_SRC.is_dir() and str(_PKG_SRC) not in sys.path:
    sys.path.insert(0, str(_PKG_SRC))

from nexus_context_compressor.ccr.marker import DROPPED_KEY  # noqa: E402
from nexus_context_compressor.ccr.retrieve import NOT_FOUND, retrieve  # noqa: E402
from nexus_context_compressor.ccr.store import CCRStore, CCRWriter  # noqa: E402
from nexus_context_compressor.tokens import count_tokens  # noqa: E402
from nexus_context_compressor.transforms.code_compressor import compress_code  # noqa: E402
from nexus_context_compressor.transforms.smart_crusher import smart_crush  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
BASELINE_PATH = Path(__file__).resolve().parent / "baseline.json"

# Effectiveness margin used by --update-baseline: the recorded floor sits this
# far below the measured reduction so a re-baseline never produces a floor that a
# trivial future improvement would trip. Fidelity has no margin -- it must be 1.0.
_EFFECTIVENESS_MARGIN = 0.10


# ---------------------------------------------------------------------------
# Per-fixture scoring
# ---------------------------------------------------------------------------


@dataclass
class FixtureScore:
    """Fidelity + effectiveness metrics for one fixture.

    A score separates *fidelity* (did compression stay reversible / preserve
    structure -- the accuracy proxy) from *effectiveness* (did it actually
    shrink the payload). The gate treats them independently: fidelity must be
    exact, effectiveness must clear a floor.

    Attributes:
        name: fixture name (from the manifest).
        kind: ``"json_array"`` or ``"code"``.
        original_units / kept_units: records (JSON) or lines (code), before/after.
        char_before / char_after: serialized character length, before/after. The
            effectiveness metric is tokenizer-independent and so identical across
            machines (unlike token counts, which depend on tiktoken availability).
        tokens_before / tokens_after: token counts (informational only; the gate
            never depends on these because the backend may fall back offline).
        ccr_checks_total / ccr_checks_ok: reversibility checks performed and
            passed (per dropped span, plus a whole-array reconstruction for JSON).
        signature_total / signature_ok: structural substrings the code skeleton
            had to keep, and how many it kept (0 for JSON fixtures).
        notes: human-readable detail lines for the report.
    """

    name: str
    kind: str
    original_units: int = 0
    kept_units: int = 0
    char_before: int = 0
    char_after: int = 0
    tokens_before: int = 0
    tokens_after: int = 0
    ccr_checks_total: int = 0
    ccr_checks_ok: int = 0
    signature_total: int = 0
    signature_ok: int = 0
    notes: list[str] = field(default_factory=list)

    @property
    def char_reduction(self) -> float:
        """Fraction of characters removed (``1 - after/before``; higher = smaller)."""
        if self.char_before <= 0:
            return 0.0
        return 1.0 - (self.char_after / self.char_before)

    @property
    def token_ratio(self) -> float:
        """Tokens retained (``after/before``); informational, never gated."""
        if self.tokens_before <= 0:
            return 1.0
        return self.tokens_after / self.tokens_before

    @property
    def ccr_roundtrip(self) -> float:
        """Reversibility score: passed checks over total. 1.0 when nothing dropped."""
        if self.ccr_checks_total == 0:
            return 1.0
        return self.ccr_checks_ok / self.ccr_checks_total

    @property
    def signature_preservation(self) -> float:
        """Structure score: kept structural lines over total. 1.0 when N/A (JSON)."""
        if self.signature_total == 0:
            return 1.0
        return self.signature_ok / self.signature_total


def _score_json_array(name: str, records: list, store: CCRWriter) -> FixtureScore:
    """Crush a JSON array and verify it reconstructs to the exact original.

    Fidelity = (every dropped span retrieves to its exact records) AND (splicing
    the retrieved spans back into the kept records reproduces the input array,
    in order). Effectiveness = character reduction of the (re-serialized) array.
    """
    score = FixtureScore(name=name, kind="json_array")
    result = smart_crush(records, store=store)

    before_text = json.dumps(records, indent=2, ensure_ascii=False)
    after_text = json.dumps(result.records, indent=2, ensure_ascii=False)
    score.original_units = result.original_count
    score.kept_units = result.kept_count
    score.char_before = len(before_text)
    score.char_after = len(after_text)
    score.tokens_before = count_tokens(before_text)
    score.tokens_after = count_tokens(after_text)

    # One reversibility check per dropped span: it must retrieve byte-identically.
    for span in result.dropped:
        score.ccr_checks_total += 1
        if retrieve(span.hash, store=store) == span.records:
            score.ccr_checks_ok += 1

    # One whole-array reconstruction check: kept records + retrieved spans, in
    # order, must equal the original input exactly.
    score.ccr_checks_total += 1
    reconstructed: list = []
    reconstruction_ok = True
    for item in result.records:
        if isinstance(item, dict) and DROPPED_KEY in item:
            restored = retrieve(item, store=store)
            if restored is NOT_FOUND:
                reconstruction_ok = False
                break
            reconstructed.extend(restored)
        else:
            reconstructed.append(item)
    if reconstruction_ok and reconstructed == records:
        score.ccr_checks_ok += 1

    score.notes.append(
        f"{result.original_count} records -> {result.kept_count} kept "
        f"+ {len(result.dropped)} CCR marker(s)"
    )
    return score


def _score_code(
    name: str, source: str, language: str, must_preserve: list[str], store: CCRWriter
) -> FixtureScore:
    """Compress code and verify structure survives and elided bodies reverse.

    Fidelity has two parts: signature-preservation (every ``must_preserve``
    substring still appears in the skeleton) and CCR body round-trip (every
    elided body retrieves to its exact original lines). Effectiveness =
    character reduction of the source.
    """
    score = FixtureScore(name=name, kind="code")
    result = compress_code(source, language, store=store)

    score.original_units = result.original_lines
    score.kept_units = result.kept_lines
    score.char_before = len(source)
    score.char_after = len(result.code)
    score.tokens_before = count_tokens(source)
    score.tokens_after = count_tokens(result.code)

    # Signature preservation: each structural substring must survive verbatim.
    missing: list[str] = []
    for needle in must_preserve:
        score.signature_total += 1
        if needle in result.code:
            score.signature_ok += 1
        else:
            missing.append(needle)

    # CCR body round-trip: each reversibly-elided body retrieves exactly.
    for body in result.dropped:
        score.ccr_checks_total += 1
        if retrieve(body.hash, store=store) == body.lines:
            score.ccr_checks_ok += 1

    score.notes.append(
        f"strategy={result.strategy}, {result.original_lines} -> {result.kept_lines} "
        f"lines, {len(result.dropped)} CCR-elided bod(y/ies)"
    )
    if missing:
        score.notes.append("MISSING signatures: " + "; ".join(missing))
    return score


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


@dataclass
class EvalReport:
    """Aggregate result of one harness run across all fixtures."""

    fixtures: list[FixtureScore] = field(default_factory=list)

    @property
    def ccr_roundtrip(self) -> float:
        """Pooled reversibility: total passed checks over total checks."""
        total = sum(f.ccr_checks_total for f in self.fixtures)
        ok = sum(f.ccr_checks_ok for f in self.fixtures)
        return 1.0 if total == 0 else ok / total

    @property
    def signature_preservation(self) -> float:
        """Pooled structure score across code fixtures."""
        total = sum(f.signature_total for f in self.fixtures)
        ok = sum(f.signature_ok for f in self.fixtures)
        return 1.0 if total == 0 else ok / total

    @property
    def mean_char_reduction(self) -> float:
        """Mean per-fixture character reduction (the gated effectiveness metric)."""
        if not self.fixtures:
            return 0.0
        return sum(f.char_reduction for f in self.fixtures) / len(self.fixtures)

    @property
    def mean_token_ratio(self) -> float:
        """Mean per-fixture token ratio (informational only)."""
        if not self.fixtures:
            return 1.0
        return sum(f.token_ratio for f in self.fixtures) / len(self.fixtures)


def _load_manifest(fixtures_dir: Path) -> list[dict[str, Any]]:
    """Load the fixture manifest (the fixed dataset description)."""
    manifest = json.loads((fixtures_dir / "manifest.json").read_text(encoding="utf-8"))
    return list(manifest.get("fixtures", []))


def run_eval(
    fixtures_dir: Path = FIXTURES_DIR, store: CCRWriter | None = None
) -> EvalReport:
    """Score every fixture and return the aggregate report.

    Args:
        fixtures_dir: the fixed-dataset directory (defaults to the bundled one).
        store: the CCR store to persist/resolve drops through. ``None`` (the
            default) opens a throwaway SQLite store in a temp directory, so a run
            never touches the real ``~/.nexus-hub`` cache. A test may inject a
            deliberately broken store (e.g. one whose ``put`` is a no-op) to prove
            the gate catches an irreversible compressor.

    Returns:
        An :class:`EvalReport` aggregating per-fixture fidelity + effectiveness.
    """
    specs = _load_manifest(fixtures_dir)
    report = EvalReport()

    own_store: CCRStore | None = None
    tmpdir: tempfile.TemporaryDirectory | None = None
    if store is None:
        tmpdir = tempfile.TemporaryDirectory(prefix="nexus-compress-eval-")
        own_store = CCRStore(Path(tmpdir.name) / "ccr-eval.db")
        store = own_store
    try:
        for spec in specs:
            name = spec["name"]
            path = fixtures_dir / spec["file"]
            if spec["kind"] == "json_array":
                records = json.loads(path.read_text(encoding="utf-8"))
                report.fixtures.append(_score_json_array(name, records, store))
            elif spec["kind"] == "code":
                source = path.read_text(encoding="utf-8")
                report.fixtures.append(
                    _score_code(
                        name,
                        source,
                        spec.get("language", ""),
                        list(spec.get("must_preserve", [])),
                        store,
                    )
                )
    finally:
        if own_store is not None:
            own_store.close()
        if tmpdir is not None:
            tmpdir.cleanup()
    return report


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, Any]:
    """Load the committed gate thresholds."""
    return json.loads(path.read_text(encoding="utf-8"))


def check_baseline(report: EvalReport, baseline: dict[str, Any]) -> list[str]:
    """Compare a run to the baseline; return a list of regression messages.

    An empty list means PASS. Fidelity is checked with zero tolerance (a single
    mismatch is a real regression in a deterministic engine); effectiveness is
    checked against a documented floor (so a compressor that silently stops
    compressing is caught even though its fidelity is trivially perfect).
    """
    failures: list[str] = []
    fidelity = baseline.get("fidelity", {})
    effectiveness = baseline.get("effectiveness", {})

    ccr_floor = float(fidelity.get("ccr_roundtrip", 1.0))
    if report.ccr_roundtrip < ccr_floor:
        failures.append(
            f"CCR round-trip fidelity regressed: {report.ccr_roundtrip:.4f} "
            f"< baseline {ccr_floor:.4f} (a dropped span did not reverse exactly)"
        )

    sig_floor = float(fidelity.get("signature_preservation", 1.0))
    if report.signature_preservation < sig_floor:
        failures.append(
            f"Signature preservation regressed: {report.signature_preservation:.4f} "
            f"< baseline {sig_floor:.4f} (a structural line was dropped)"
        )

    red_floor = float(effectiveness.get("min_aggregate_char_reduction", 0.0))
    if report.mean_char_reduction < red_floor:
        failures.append(
            f"Compression effectiveness regressed: mean char reduction "
            f"{report.mean_char_reduction:.4f} < floor {red_floor:.4f} "
            f"(the engine compressed less than the baseline allows)"
        )

    # Per-slice floors: an aggregate that still clears the mean must not hide a
    # fixture that stopped compressing (or stopped reversing). Missing fixtures
    # are also a fail -- deleting a slice to dodge its floor is the same cheat.
    by_name = {fx.name: fx for fx in report.fixtures}
    for slice_name, floors in (baseline.get("per_slice") or {}).items():
        fx = by_name.get(slice_name)
        if fx is None:
            failures.append(
                f"per-slice floor '{slice_name}' has no matching fixture "
                f"(removing a slice to dodge its floor is a regression)"
            )
            continue
        min_red = floors.get("min_char_reduction")
        if min_red is not None and fx.char_reduction < float(min_red):
            failures.append(
                f"per-slice {slice_name} char reduction "
                f"{fx.char_reduction:.4f} < floor {float(min_red):.4f} "
                f"(aggregate may still pass)"
            )
        min_ccr = floors.get("min_ccr_roundtrip")
        if min_ccr is not None and fx.ccr_roundtrip < float(min_ccr):
            failures.append(
                f"per-slice {slice_name} CCR round-trip "
                f"{fx.ccr_roundtrip:.4f} < floor {float(min_ccr):.4f}"
            )
    return failures


def _measured_baseline(report: EvalReport) -> dict[str, Any]:
    """Build a baseline dict from a healthy run (for ``--update-baseline``)."""
    floor = max(0.0, round(report.mean_char_reduction - _EFFECTIVENESS_MARGIN, 2))
    return {
        "_comment": (
            "Compression accuracy-regression baseline (adoption-headroom Phase 5). "
            "Fidelity metrics are deterministic structural invariants and must stay "
            "at 1.0 -- a value below means a dropped span did not reverse exactly or "
            "a code signature was lost. 'min_aggregate_char_reduction' is an "
            "effectiveness floor that catches a compressor which silently stops "
            "compressing; it sits a safety margin below the measured reduction. To "
            "re-baseline intentionally after a legitimate behavior change, run "
            "'python -m evals --update-baseline' and review the diff."
        ),
        "fidelity": {
            "ccr_roundtrip": round(report.ccr_roundtrip, 4),
            "signature_preservation": round(report.signature_preservation, 4),
        },
        "effectiveness": {
            "min_aggregate_char_reduction": floor,
        },
        "corpus_version": 1,
        "per_slice": {
            fx.name: {
                "min_char_reduction": max(
                    0.0, round(fx.char_reduction - _EFFECTIVENESS_MARGIN, 2)
                ),
                "min_ccr_roundtrip": 1.0,
            }
            for fx in report.fixtures
        },
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_report(report: EvalReport, baseline: dict[str, Any] | None = None) -> str:
    """Render the run as a Markdown report (follows the repo Markdown style)."""
    lines: list[str] = []
    lines.append("# Compression accuracy-regression report")
    lines.append("")
    lines.append(
        f"- CCR round-trip fidelity: **{report.ccr_roundtrip:.1%}**"
    )
    lines.append(
        f"- Signature preservation: **{report.signature_preservation:.1%}**"
    )
    lines.append(
        f"- Mean character reduction: **{report.mean_char_reduction:.1%}** "
        f"(gated effectiveness metric, tokenizer-independent)"
    )
    lines.append(
        f"- Mean token ratio: **{report.mean_token_ratio:.1%}** retained "
        f"(informational)"
    )
    lines.append("")
    lines.append("## Per-fixture")
    lines.append("")
    lines.append(
        "| Fixture | Kind | Units (before -> after) | Char reduction | "
        "CCR round-trip | Signatures |"
    )
    lines.append(
        "|---------|------|-------------------------|----------------|"
        "----------------|------------|"
    )
    for f in report.fixtures:
        sig = "n/a" if f.kind == "json_array" else f"{f.signature_ok}/{f.signature_total}"
        ccr = "n/a" if f.ccr_checks_total == 0 else f"{f.ccr_checks_ok}/{f.ccr_checks_total}"
        lines.append(
            f"| {f.name} | {f.kind} | {f.original_units} -> {f.kept_units} | "
            f"{f.char_reduction:.1%} | {ccr} | {sig} |"
        )
    lines.append("")
    lines.append("## Detail")
    lines.append("")
    for f in report.fixtures:
        lines.append(f"### {f.name}")
        lines.append("")
        for note in f.notes:
            lines.append(f"- {note}")
        lines.append("")

    if baseline is not None:
        failures = check_baseline(report, baseline)
        lines.append("## Gate")
        lines.append("")
        if not failures:
            lines.append("PASS -- no fidelity or effectiveness regression against the baseline.")
        else:
            lines.append("FAIL -- regressions detected:")
            lines.append("")
            for failure in failures:
                lines.append(f"- {failure}")
        lines.append("")
    return "\n".join(lines)


def render_json(report: EvalReport) -> dict[str, Any]:
    """Render the run as a JSON-serializable dict."""
    return {
        "ccr_roundtrip": report.ccr_roundtrip,
        "signature_preservation": report.signature_preservation,
        "mean_char_reduction": report.mean_char_reduction,
        "mean_token_ratio": report.mean_token_ratio,
        "fixtures": [
            {
                "name": f.name,
                "kind": f.kind,
                "original_units": f.original_units,
                "kept_units": f.kept_units,
                "char_before": f.char_before,
                "char_after": f.char_after,
                "char_reduction": f.char_reduction,
                "token_ratio": f.token_ratio,
                "ccr_checks_ok": f.ccr_checks_ok,
                "ccr_checks_total": f.ccr_checks_total,
                "ccr_roundtrip": f.ccr_roundtrip,
                "signature_ok": f.signature_ok,
                "signature_total": f.signature_total,
                "signature_preservation": f.signature_preservation,
                "notes": f.notes,
            }
            for f in report.fixtures
        ],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code (0 = pass, 1 = regression)."""
    parser = argparse.ArgumentParser(
        prog="python -m evals",
        description="Compression accuracy-regression harness + CI gate.",
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=FIXTURES_DIR,
        help=f"Fixture directory (default: {FIXTURES_DIR}).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write the Markdown report to this path (default: stdout).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of Markdown.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Gate mode: exit non-zero on any fidelity/effectiveness regression.",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Overwrite baseline.json from this (assumed-healthy) run, then exit.",
    )
    args = parser.parse_args(argv)

    if not args.fixtures.exists():
        print(f"error: fixtures dir {args.fixtures} not found", file=sys.stderr)
        return 2

    report = run_eval(args.fixtures)

    if args.update_baseline:
        baseline = _measured_baseline(report)
        BASELINE_PATH.write_text(
            json.dumps(baseline, indent=2) + "\n", encoding="utf-8"
        )
        print(f"wrote baseline {BASELINE_PATH}", file=sys.stderr)
        return 0

    baseline = load_baseline() if BASELINE_PATH.exists() else None

    # In pure-gate mode (--check with no --out/--json) stay quiet: emit only the
    # one-line PASS/FAIL summary to stderr below, so `make validate` output stays
    # small (the repo's output-minimization convention).
    quiet_gate = args.check and args.out is None and not args.json
    if not quiet_gate:
        if args.json:
            body = json.dumps(render_json(report), indent=2)
        else:
            body = render_report(report, baseline)
        if args.out is not None:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(body, encoding="utf-8")
            print(f"wrote {args.out}", file=sys.stderr)
        else:
            print(body)

    if args.check:
        if baseline is None:
            print("error: --check requires baseline.json", file=sys.stderr)
            return 2
        failures = check_baseline(report, baseline)
        if failures:
            print("", file=sys.stderr)
            print("Compression accuracy gate FAILED:", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print(
            f"Compression accuracy gate PASSED "
            f"(CCR {report.ccr_roundtrip:.1%}, signatures "
            f"{report.signature_preservation:.1%}, "
            f"reduction {report.mean_char_reduction:.1%}).",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
