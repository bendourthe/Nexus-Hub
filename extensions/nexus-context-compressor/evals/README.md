# Compression accuracy-regression harness

This harness proves that `nexus-context-compressor` preserves answer quality so aggressive compression ratios can ship safely, and it gates that property in CI (adoption-headroom Phase 5, tasks T016-T018).

## Why structural fidelity, not a live-LLM benchmark

headroom's upstream `eval.yml` measures accuracy by running GSM8K / TruthfulQA / SQuAD / BFCL through a live model and comparing answers. We deliberately do not do that. A live LLM call is non-deterministic, slow, and (for this repo) an outbound call we refuse to add. Instead the harness checks a property the engine *guarantees* and verifies it exactly, offline, and reproducibly.

| Metric | What it proves | How it is measured |
|--------|----------------|--------------------|
| CCR round-trip fidelity | Compression is non-lossy: every dropped span is reversible | For each JSON array, `reconstruct(compress(x)) == x`; for each elided code body, the CCR marker resolves back to the exact original lines |
| Signature preservation | Code skeletons keep their structure | Every import, decorator, class header, and function/method signature listed in the fixture manifest still appears in the compressed skeleton |
| Compression effectiveness | The engine still actually compresses | Mean character-length reduction across fixtures (tokenizer-independent, so identical on every machine) |

The token ratio is reported too, but only as information: token counts depend on whether `tiktoken` is available offline, so the gate never depends on them.

## The fixed dataset

`fixtures/manifest.json` describes a small, committed dataset:

- `json_logs.json` and `search_hits.json` - JSON arrays with duplicate runs that `SmartCrusher` collapses behind reversible CCR markers.
- `sample_python.py` and `sample_typescript.ts` - modules whose multi-line bodies the `CodeCompressor` elides while preserving structure. Each code fixture lists the `must_preserve` structural substrings the skeleton must keep verbatim.

The code fixtures are clean enough that the AST strategy (tree-sitter, when present) and the dependency-free regex fallback find the same body spans, so the measured reduction is identical whether or not `tree-sitter` is installed.

## Running it

From the package root (`extensions/nexus-context-compressor/`):

```bash
python -m evals                 # Markdown report + gate verdict to stdout
python -m evals --json          # machine-readable metrics
python -m evals --out report.md # write the Markdown report to a file
python -m evals --check         # gate mode: exit non-zero on any regression
```

Repo-level shortcuts (from the repo root):

```bash
make compress-eval              # write a report to docs/releases/v3/v3.2/ and run the gate
make validate                   # runs the gate alongside the other catalog gates
```

The gate also runs in CI in the `validate` job (`.github/workflows/ci.yml`), alongside the skill-security gate.

## The threshold and how to update it

The committed thresholds live in `baseline.json`:

- `fidelity.ccr_roundtrip` and `fidelity.signature_preservation` are deterministic structural invariants and are pinned at `1.0`. The gate checks them with zero tolerance: a single mismatch means a dropped span did not reverse exactly, or a code signature was lost - a real regression.
- `effectiveness.min_aggregate_char_reduction` is a floor (currently `0.36`) that catches a compressor which silently stops compressing. It sits a 10-point safety margin below the measured reduction, so a normal improvement never trips it.

If a legitimate behavior change moves the numbers (for example, a new strategy that compresses more, or a fixture added to the dataset), re-baseline intentionally and review the diff before committing:

```bash
cd extensions/nexus-context-compressor && python -m evals --update-baseline
git diff evals/baseline.json
```

Never lower a fidelity threshold below `1.0` to make a failing gate pass - a fidelity failure is a correctness bug in the engine, not a baseline that needs loosening.

## Corpus versioning and per-slice floors

`baseline.json` also carries:

- `corpus_version` - integer identity of the fixture set. Bump it in the same change that rewrites or replaces fixtures. Examples are append-only within a version; deleting or silently rewriting a fixture to dodge a miss is a regression.
- `per_slice` - a hard floor per fixture (`min_char_reduction`, `min_ccr_roundtrip`). A run that holds the aggregate mean but drops one fixture below its floor fails `--check`. That is deliberate: the mean is not a hiding place.

Lowering a per-slice floor or the aggregate floor requires its own change whose message shows the historical series and names the behavior change that justifies the new number. Do not lower a floor in the same commit that would otherwise fail. `--update-baseline` is for raising floors after a real improvement, or for recording a new corpus version, not for painting a red gate green.

## Corpus versioning and per-slice floors

`baseline.json` also carries:

- `corpus_version` - integer identity of the fixture set. Bump it in the same change that rewrites or replaces fixtures. Examples are append-only within a version; deleting or silently rewriting a fixture to dodge a miss is a regression.
- `per_slice` - a hard floor per fixture (`min_char_reduction`, `min_ccr_roundtrip`). A run that holds the aggregate mean but drops one fixture below its floor fails `--check`. That is deliberate: the mean is not a hiding place.

Lowering a per-slice floor or the aggregate floor requires its own change whose message shows the historical series and names the behavior change that justifies the new number. Do not lower a floor in the same commit that would otherwise fail. `--update-baseline` is for raising floors after a real improvement, or for recording a new corpus version, not for painting a red gate green.
