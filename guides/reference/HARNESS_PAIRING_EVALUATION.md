# Harness Pairing Evaluation

Summary: the durable contract for measuring a model x harness x workload pairing locally: versioned manifest, trial and aggregate receipts, objective metrics, comparison eligibility, ranking restraint, and the adapter trust boundary.
Read this when: you add or change a workload, a harness adapter, or the evaluator; you read a pairing receipt; or you decide whether a pairing earns its cost.
Covers: evaluation modes, manifest and receipt schemas, metrics and intervals, eligibility, the adapter and isolation boundary, unavailable values, and where the runner and tests live.
Keywords: harness pairing, receipt, Wilson interval, bootstrap, Pareto, needs-live-validation, NEXUS_HUB_SKILL_INDEX.

This guide is the single owner of the evaluation contract. The evaluator script (`scripts/evaluate_harness_pairings.py`) implements it, the oracle at `tests/fixtures/harness_pairings/oracle.py` restates it independently, and `tests/integrations/test_harness_pairing_contract.py` holds both to it. Structural conformance of a project's instruction files stays with `scripts/harness_audit.py`; this contract owns observed local behavior. The two never overwrite each other's evidence.

## Evaluation modes

Every pairing declares exactly one mode. The mode decides what the evidence can support.

| Mode | Meaning | Cost | Can support a recommendation |
|---|---|---|---|
| `synthetic` | Trusted fake adapters in a workspace-separated temporary root. No provider call. | Not applicable (explicitly unavailable) | No. It proves the machinery, not a real harness. |
| `metered-live` | A real harness run behind a proven isolation backend and a provider- or adapter-enforced hard spend limit that rejects spend before it is incurred. | Observed and bounded | Yes, when every other restraint rule holds. |
| `observational-live` | A real run whose cost is reported by telemetry and bounded only by cancellation. | Reported, with a recorded maximum overshoot | No. It cannot satisfy a hard-cost claim or the recommendation gate. |

A live mode requires an isolation backend that proves filesystem confinement, process-tree containment, network destination policy, credential injection, and cleanup. Without one, live execution is rejected. Time is runner-enforced; turns need a native pre-request limit or adapter events with cancellation; a hard spend ceiling needs a limit that rejects additional requests, tokens, or spend before they are incurred.

When a live run is unavailable, the result is `needs-live-validation`. A synthetic success is never reported as live evidence.

## Manifest

Schema `harness-pairing-manifest/1`. A manifest is validated before any trial starts. All keys below are required; unknown top-level keys are rejected.

| Key | Content |
|---|---|
| `schema`, `run_id` | Schema version and the run identity. A duplicate or reused run identity fails closed. |
| `workload` | `id`, `revision`, `hash`, `evaluator_revision`, `evaluator_hash`, `budget_class`, and a predeclared `policy`. |
| `workload.policy` | `min_success_rate`, `max_latency_s`, `max_cost_usd` (null when no cost gate applies), and a `tie_break` from `lowest-instruction-tokens`, `lowest-latency`, `highest-success-rate`, `lowest-cost-per-success`. |
| `environment` | `os`, `arch`, `repo_revision`, `harness_configuration`, `model_parameters`, `cache_policy`, `concurrency`, `retry_policy`, `pricing` (a `basis` and `date`, or an explicit unavailable object). |
| `pairings` | One entry per harness-and-model pairing: `id`, `harness` (`name`, `version`, `adapter`, `adapter_version`), `model` (`id`, `identity`), `instruction` (`variant`, `skill_index_mode`, `hash`, `bytes`, `tokens_estimated`), `tool_schema_hash`, `isolation_mode`, `budgets` (`time_s`, `turns`, `spend_usd`, `spend_enforcement`). |
| `repeats`, `seed`, `order_policy` | Repeat count (default three repeats per pairing), the trial seed, and `alternating` or `seeded-random` ordering. |

A pairing may carry an `environment_override` that changes comparison identity for that pairing only; it splits the comparison group (see Comparison eligibility).

The first required variant pair is `NEXUS_HUB_SKILL_INDEX=full` against `pointer`, recorded in `instruction.skill_index_mode`, with organic skill selection captured separately from the payload figures.

## Trial receipt

Schema `harness-pairing-trial/1`, one immutable JSON object per trial, written only by the parent runner. Only allowlisted keys exist; an unknown key is rejected, never stored.

Identity and order: `run_id`, `workload_hash`, `pairing_id`, `trial_index`, `order_position`, `seed`, `isolation_mode`.

Result: `outcome` (`success`, `failure`, `timeout`, `budget-exhausted`, `adapter-protocol-error`, `evaluator-error`, `containment-failure`), `evaluator_success` (true, false, or null), `harness_claim_success` (diagnostic only).

Measurements: `latency_s`, `cost_usd`, `instruction_bytes`, `instruction_tokens_estimated`, `tool_schema_bytes`.

Selection and diagnosis: `organic_skills` (null when unobserved), `guard_skills`, `failure_fingerprint`, `started_at`, `ended_at`.

Rules the contract tests enforce:

- `outcome` is `success` only when the workload-owned deterministic evaluator confirmed it. A harness claim never asserts success.
- A trial whose latency exceeds its time budget must be a `timeout`; one whose cost exceeds its spend budget must be `budget-exhausted`.
- `order_position` must match the order the manifest's `order_policy` generates for the seed.
- `workload_hash`, `isolation_mode`, and `instruction_bytes` must match the manifest.
- Every string is bounded to 512 characters and rejected when it holds a control byte, an ANSI escape, a forged Markdown heading, or a secret-shaped value.

## Aggregate receipt

Schema `harness-pairing-aggregate/1`. It carries per-pairing counts (`trials`, `rankable_trials`, `non_rankable_trials`, `successes`), the metrics below with their intervals, the sorted failure fingerprints, organic skill selection, the `qualifying` pairings, the Pareto frontier, and a `recommendation` of state `recommended` or `no-recommendation` with a reason. Every raw trial stays beside the aggregate. A trial the evaluator could not score is non-rankable: it stays in the report and is excluded from the success rate.

## Metrics

- **Task success:** decided by a workload-owned deterministic evaluator, never by harness self-report. When the evaluator and the harness disagree, the evaluator wins and both values are retained.
- **Success rate:** successes over rankable trials, with a 95% Wilson interval.
- **Latency and cost:** the mean with a fixed-seed percentile bootstrap interval (2000 resamples, 95%, seeded from the manifest seed, the pairing id, and the metric name).
- **Cost per successful task:** total observed cost over successes. With no success, or any missing cost, it is unavailable.
- **Initial instruction bytes and estimated tokens:** taken from `scripts/measure_rendered_context.py --json`. The estimator is imported, never redefined; an instruction-token figure that disagrees with the measurer for the same file is a contract failure.
- **Tool-schema bytes:** recorded when observable, otherwise unavailable.
- **Organic skill selection:** the set of skills a trial loads without being named in the prompt. Guard skills such as `security-review` are recorded separately. Selection stays `needs-live-validation` until a live run observes it.
- **Failure fingerprints:** normalized from bounded, redacted evidence. Secrets and full prompts are never stored.

## Comparison eligibility

A direct comparison needs the same workload hash and evaluator hash, environment identity (os, arch, model parameters, cache policy, retry policy, concurrency), budget class, paired seeds, trial-order policy, and pricing basis. Differing price dates or budget classes split comparison groups; they are never normalized silently.

Restraint rules, all of which must hold before one pairing is named:

- Every pairing is `metered-live`. Synthetic and `observational-live` evidence never recommends.
- At least three repeats per pairing.
- Every pairing is comparable: no unavailable pricing snapshot, tool-schema hash, or harness version.
- At least one pairing meets the predeclared gates (success floor, latency ceiling, and the cost ceiling when set).
- The leader on the predeclared tie-break is on the Pareto frontier of qualifying pairings, and its 95% interval does not overlap any other qualifying pairing's interval on that tie-break.

When a rule fails, the report says `no-recommendation` with the reason. A lower-overhead pairing is one measured input, not the decision rule.

## Adapter and isolation boundary

Adapters are an argv array plus a narrow JSON input and output protocol. The contract forbids `shell=True` and any shell string, inline secrets, an inherited environment by default, and capture of credential values in receipts.

- **Hostile bytes:** adapter output is bounded before parsing, decoded as strict UTF-8, and reduced to allowlisted typed fields. Redaction and escaping of control sequences and Markdown or HTML happen in memory before anything is written. Raw stdout and stderr stay ephemeral unless an explicitly protected diagnostic channel is selected.
- **Workspaces:** each trial gets a disposable root, a sentinel checked before cleanup, an environment allowlist, and explicit network and provider permission. Colliding runs cannot share a mutable workspace or receipt path.
- **Paths:** a path that is absolute, drive-qualified, or contains `..` is rejected before process start.
- **Workspace-separated is not isolated:** a synthetic temporary root is labeled `workspace-separated`. Only `[[agent-execution-isolation]]` owns the live containment capability contract.
- **Evaluator trust:** evaluator code, expected results, and workload policy live under a hashed read-only trusted root outside the adapter workspace. An adapter attempt to modify them is a containment failure.

## Unavailable values

A metric is a number or an object `{"unavailable": "<reason>"}`. A gap never becomes zero, infinity, or a guessed value. Missing version or pricing data makes the affected comparison incomparable. Missing provider usage keeps success and latency and marks cost unavailable, which blocks any cost-based recommendation.

## Fixtures and tests

- Fixtures: `tests/fixtures/harness_pairings/` holds the valid, partial, and incomparable manifests, the trial and aggregate receipts, two instruction samples for the `full` against `pointer` pair, and `oracle.py`, an independent recomputation of every aggregate.
- Contract tests: `tests/integrations/test_harness_pairing_contract.py` validates the fixtures, mutates them adversarially, and recomputes the aggregates.
- Audit routing: `[[eval-pipeline-audit]]` recognizes missing behavioral pairing evidence and routes it here; it does not embed these mechanics.
- Runner tests: `tests/integrations/test_harness_pairings.py` drives the runner end to end with fake adapters and compares its output with the oracle.

## Runner

`scripts/evaluate_harness_pairings.py` is the repository-local, serial evaluator. It is maintainer tooling: it is not installed by `scripts/installer.sh` or `scripts/installer.ps1`, and installed distribution is deferred scope until usage evidence shows a downstream need. A request to install it is recorded as deferred, not implemented implicitly.

### Safe synthetic defaults

Check what would run, without launching anything or creating a workspace:

```bash
python scripts/evaluate_harness_pairings.py run --manifest MANIFEST.json --workload-root WORKLOAD_DIR --adapters-dir ADAPTERS_DIR --out-dir OUT_DIR --dry-run
```

Expected output: a JSON plan with the run id, the trial count, the trial order, and the modes. Exit code 0.

Run it for real (synthetic trials only):

```bash
python scripts/evaluate_harness_pairings.py run --manifest MANIFEST.json --workload-root WORKLOAD_DIR --adapters-dir ADAPTERS_DIR --out-dir OUT_DIR
```

Expected output: one JSON line with `run_dir`, `state`, and `rankable_trials`. The run directory holds one immutable `trial-NNN-PAIRING.json` per trial, `aggregate.json`, and `report.md`. Exit codes: 0 when at least one trial was rankable (or with `--probe`), 1 when none was, 2 on a preflight failure (the JSON line names the typed `code`), 130 when interrupted after writing the receipts completed so far. A run id that already has receipts is refused; runs never resume, and a new invocation needs a new run id.

### Workload layout

The workload root is a trusted, read-only input outside the adapter workspace: `workload.json` (id, revision, prompt, declared `inputs`), an `inputs/` folder of declared files, and an `evaluator/` folder holding `evaluate.py` and the expected results. The manifest's `workload.hash` covers everything except `evaluator/`; `workload.evaluator_hash` covers `evaluator/`. Both are checked before any trial and the whole tree is re-hashed after each adapter exits: a change is a `containment-failure` and is never scored as success. Synthetic mode detects tampering after the fact; it does not prevent it, which is why live execution needs an isolation backend.

### Adapter profiles

An adapter profile is a JSON file named `NAME.json` with schema `harness-adapter/1`: `name`, `kind` (`fake` for the JSON stdio protocol, `cli` for a real command line tool whose only claim is its exit status), `argv` (an argv array; `{python}` expands to the running interpreter), optional `version_argv`, `timeout_s`, and optional `env_allow` and `env_set`. A string command, a credential-named variable (names containing KEY, TOKEN, SECRET, PASSWORD, or CREDENTIAL), or an unsafe profile name fails preflight. Children receive only an explicit minimal environment.

Built-in `cli` profiles for Claude Code and Codex live in `configs/harness-adapters/`. Their `argv` is marked `unverified: needs-live-validation` because no live run has confirmed it. Check them without credentials:

```bash
python scripts/evaluate_harness_pairings.py conformance
```

Expected output: a JSON list with one row per profile. `status` is `ok` with the `--version` output, `binary-absent` when the tool is not installed, or a typed failure. Exit code 0 unless a profile is invalid or a version probe failed.

### Live runs

Live trials are opt-in and closed by default. The runner refuses `metered-live` and `observational-live` with the typed code `isolation-backend-unavailable` until an isolation backend proves filesystem, process-tree, network, credential-injection, and cleanup containment, and a `metered-live` pairing also needs a provider- or adapter-enforced hard limit. No such backend ships, so every live claim stays `needs-live-validation`. Blocked external writes and disallowed egress can be proven only by a trial run through that backend; synthetic mode proves neither.

### Cleanup

A trial workspace is a unique directory under the work root with a sentinel file. The runner deletes only a directory that sits directly inside the work root, is not a link, and carries the matching sentinel; anything else is left in place and reported as manual cleanup needed.

### Algorithms

Both the runner and the oracle implement these independently and must agree exactly:

- Wilson: `p = k/n`, `z = 1.959963984540054`, center `(p + z^2/2n) / (1 + z^2/n)`, half-width `z * sqrt(p(1-p)/n + z^2/4n^2) / (1 + z^2/n)`, clamped to 0..1.
- Bootstrap: 2000 resamples of the mean; each resample draws `n` values with `random.Random(seed_text).randrange(n)`, where `seed_text` is `MANIFEST_SEED:PAIRING_ID:METRIC`; the interval is the sorted resample means at index `floor(0.025 * 2000)` and `ceil(0.975 * 2000) - 1`.
- Order: `alternating` runs the pairings forward on even rounds and reversed on odd rounds; `seeded-random` shuffles each round with `random.Random("SEED:ROUND")`.
