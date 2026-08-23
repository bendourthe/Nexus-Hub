# Deterministic Code-Search Benchmark Methodology

## Purpose

This repository-only harness measures whether tool profiles and compact responses reduce context cost without degrading retrieval quality. It is a preliminary small-sample regression suite, not a claim about performance on all repositories or languages.

## Fixed Inputs

The committed `goldset.json` names a committed corpus, four task shapes, the real MCP tool used for each task, its smallest supported profile, and ranked known-correct answers. The task shapes locate a symbol, find all callers, identify an unused symbol, and trace an impact radius. The runner copies the corpus to a temporary work directory, builds the real local graph index, and dispatches each task through the same server handler used by MCP.

## Cost Metrics

For every task, the runner records UTF-8 JSON response bytes, compact-wire bytes, deterministic standard-library token estimates for both representations, full-profile and active-profile tool-definition token counts, and wall-clock tool latency. The aggregate table compares all-tools versus profiled definitions and JSON versus compact responses. Savings are recomputed from the raw byte totals in the machine-readable report.

## Quality Metrics

Each ranked result is compared with the recorded answer. Precision is the fraction of returned unique answers that are correct, recall is the fraction of expected answers returned, and reciprocal rank is one divided by the position of the first correct result. Empty expected and returned sets score 1.0; an expected answer with no correct result scores 0.0. The report uses macro averages across tasks so a cheap task cannot hide a weak task behind a larger response.

## Regression Gate

`baseline.json` stores only deterministic quality metrics. Run `python benchmarks/harness.py --check` from the extension directory to compare a fresh run with the baseline. The command exits nonzero when precision, recall, or mean reciprocal rank drops beyond the configured tolerance. Latency and byte counts remain visible measurements but are not hard gates because host speed and serialized path length vary.

## Offline Contract

The harness makes no network call, reads no credential, uses no API key, and invokes no model. Token counting uses the existing deterministic standard-library estimator. Tests run the complete path with socket connection attempts blocked and an empty environment, and statically reject HTTP-client imports or credential reads in the harness.

## Installation Boundary

The `benchmarks/` tree is development evidence only. Both installers remove it from the copied `nexus-code-search` tree before installation, and a regression test checks both exclusion commands.

## Known Confounds

- The corpus is deliberately small, Python-only, and hand-authored, so the quality scores are regression evidence rather than ecosystem-wide accuracy estimates.

- Wall-clock latency includes local filesystem and SQLite variation and should be compared only under similar host conditions.

- Tool-definition tokens use the deterministic estimator, not a provider-specific tokenizer.

- Compact-wire savings depend on response shape and size; individual short responses may grow even when the aggregate shrinks.

- The graph extractor currently resolves in-file calls more reliably than cross-file calls, so the callers and impact tasks use a same-file edge while the unused-symbol task independently exercises file-level isolation.

## Reproduction

From `extensions/nexus-code-search/`, run:

```bash
python benchmarks/harness.py --check --json-out benchmarks/report.json --markdown-out benchmarks/report.md
```

The two report files are ignored run outputs and are not committed or installed.
