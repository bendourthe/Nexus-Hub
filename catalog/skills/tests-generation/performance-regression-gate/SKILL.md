---
name: performance-regression-gate
description: Catch performance regressions automatically by committing a benchmark baseline and failing when a metric degrades beyond a threshold. Make sure to use this skill whenever the user says "catch performance regressions", "benchmark gate", "fail the build if it got slower", "performance baseline", "perf CI check", "alert when latency or throughput or bundle size degrades", or wants automated detection of performance drift over time rather than a one-off measurement. SKIP, do NOT use for, one-off profiling or optimizing a specific function (use code-optimizer), writing the benchmarks themselves or load/stress testing (use performance-testing), or correctness testing (use unit-tests / integration-test-generator).
summary_l0: "Commit a benchmark baseline and fail CI when a metric regresses beyond a threshold"
overview_l1: "This skill adds the CI-facing half of performance testing: commit a benchmark BASELINE and fail (or flag) when a metric degrades beyond a threshold, so performance drift is caught automatically instead of noticed in production. It teaches which hot-path metrics to gate (latency, throughput, allocations, bundle size), how to capture and commit a baseline, how to compare current-vs-baseline with a per-metric direction (lower-is-better for latency and size, higher-is-better for throughput) and a noise-tolerant threshold, how to wire the check into CI, and when to deliberately re-baseline. The bundled scripts/perf_baseline.py records and checks the baseline deterministically (stdlib-only, zero-network) and exits non-zero on a regression. It complements performance-testing (which writes the benchmarks) and code-optimizer (one-off profiling). Trigger phrases: catch performance regressions, benchmark gate, fail the build if it got slower, performance baseline, perf CI check."
---

# Performance Regression Gate

Stop performance from degrading silently. `performance-testing` teaches you to measure; this skill adds the missing half - commit a baseline and fail the build when a metric regresses beyond a threshold, so a slowdown is caught in CI rather than in production.

## When to Use This Skill

- You have benchmarks (latency, throughput, allocations, bundle size) and want to catch regressions automatically over time.
- Setting up a CI gate that fails a PR when it makes a hot path measurably slower or larger.
- After optimizing something, to lock in the gain with a baseline so it cannot silently erode.

**Trigger phrases**: "catch performance regressions", "benchmark gate", "fail the build if it got slower", "performance baseline", "perf CI check", "alert when latency degrades".

### When NOT to Use

| Want to ... | Use this instead |
|---|---|
| Write the benchmarks / do load or stress testing | `performance-testing` |
| Profile and optimize a specific function once | `code-optimizer` |
| Test correctness | `unit-tests` / `integration-test-generator` |

## How this differs from performance-testing

`performance-testing` produces the measurements (how to benchmark, load-test, and profile). This skill consumes a measurement and turns it into a gate: a committed baseline plus a pass/fail comparison with a per-metric direction and threshold. Use `performance-testing` to generate the numbers, then this skill to defend them.

## Instructions

1. **Choose the metrics to gate.** Pick a small set of hot-path numbers that matter and are stable enough to compare run to run (for example p95 latency, requests/sec, peak allocations, gzipped bundle size). Gating noisy micro-metrics produces flaky failures; prefer aggregates and medians of repeated runs.
2. **Record a baseline and commit it.** Produce a metrics JSON (`{"name": number, ...}`) from your benchmark, then record it next to the benchmarks and commit it:

    ```bash
    python scripts/perf_baseline.py --record perf-baseline.json --metrics current.json \
        --threshold 0.10 --higher-is-better throughput_rps
    ```

3. **Check current against the baseline in the gate.** On each run, produce the current metrics the same way and compare. The script exits non-zero when any metric regresses beyond the threshold (lower-is-better metrics fail when they rise; higher-is-better metrics fail when they fall):

    ```bash
    python scripts/perf_baseline.py --check perf-baseline.json --metrics current.json
    ```

4. **Wire it into CI.** Run the benchmark, emit the current metrics JSON, and run the `--check`. A non-zero exit fails the job. Path-filter the job to the code and benchmarks it covers so it only spends minutes when relevant.
5. **Re-baseline deliberately.** When a change intentionally shifts performance (a rewrite, a dependency bump), re-run `--record` and commit the new baseline in the same reviewed change - never auto-update the baseline to make a red gate green.

The deterministic record/compare logic lives in the bundled `scripts/perf_baseline.py` (stdlib-only, zero-network); the skill body stays thin and the script runs on demand without being read into context.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We benchmark in CI already, that is enough." | Measuring is not gating. Without a committed baseline and a fail condition, a 30 percent slowdown just scrolls past in the logs and ships. |
| "I will just eyeball the numbers each release." | Manual comparison misses gradual drift - five 4 percent regressions are a 20 percent loss no one flagged. The gate is what makes drift visible. |
| "The gate went red, I will bump the baseline." | Re-baselining to silence a red gate hides the regression. Re-baseline only for an intended, reviewed performance change, in the same commit. |
| "One threshold for everything is fine." | Latency and throughput move in opposite directions; a single-direction gate silently passes a throughput drop. Mark higher-is-better metrics so the comparison is correct. |
| "Micro-benchmark every function." | Noisy micro-metrics cause flaky failures and alert fatigue. Gate a few stable, meaningful aggregates. |

## Verification

- [ ] A baseline JSON exists and is committed alongside the benchmarks.
- [ ] `perf_baseline.py --check` exits non-zero on a seeded over-threshold regression and zero within threshold (proven, not assumed).
- [ ] Each gated metric has the correct direction (higher-is-better metrics are listed).
- [ ] The check is wired into CI and fails the job on a non-zero exit.
- [ ] Re-baselining happens only in a reviewed change that intentionally alters performance.

## Related Skills

- [[performance-testing]] -- writes the benchmarks and load tests whose output this gate defends.
- [[code-optimizer]] -- one-off profiling and optimization; this skill locks in the gains it produces.
- [[performance-review]] -- reviews code for performance issues; the gate catches regressions the review missed.
- [[cicd-integration]] -- wiring the gate into the CI pipeline.

---

**Version**: 1.0.0
**Last Updated**: July 2026
