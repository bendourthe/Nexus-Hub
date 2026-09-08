# Local Security Audit

How Nexus-Hub runs a local security audit: optional scanners, receipt states, degraded coverage, remediation consent, same-detector re-scan, and independent verification.

This is the user-facing procedure for the `security-audit` preset. The machine-checked contract lives with `security-review`. Tools are never auto-installed. Cloud review is read-only.

## Prerequisites

- A Nexus-Hub install that includes the security-audit owners: `security-review`, `dependency-security-audit`, `cve-reachability-analyzer`, `cloud-security-posture-detection`, `security-patch-advisor`, `testing-review`, `adversarial-verifier`, and `agent-presets`. The `security-specialist` bundle includes those owners.
- Optional local scanner binaries already present on the machine. Missing tools are recorded; they are not installed.
- User approval before any patch is applied.

## How optional local scanners are selected

The workflow does not run every scanner. Each owner checks whether its scanner applies, then records a receipt:

- Application static analysis and secrets: `security-review` (Semgrep, gitleaks).
- Dependencies: `dependency-security-audit` (OSV-Scanner, npm audit, pip-audit, Trivy vulnerability scan), selected from manifests.
- Infrastructure as code: `cloud-security-posture-detection` (Trivy config, Checkov) when supported files exist.

If the binary is missing, the owner records `UNAVAILABLE` and continues. If a ruleset would fetch over the network, the owner asks first; a declined fetch is `DECLINED`. Cloud posture never applies, deploys, or mutates infrastructure.

## Receipt states

Every considered scanner gets one receipt:

| State | Meaning |
|---|---|
| `RAN` | The scanner executed against the recorded target |
| `NOT_APPLICABLE` | Evidence shows this scanner does not apply |
| `UNAVAILABLE` | The scanner applies, but the tool is not present locally |
| `FAILED` | The scanner was invoked and did not complete successfully |
| `DECLINED` | The scanner applies, but the user declined to run it |

A silent omission (an inventory scanner with no receipt) is a closure failure even when coverage is already marked degraded.

## Why missing scanners degrade completeness

Deterministic coverage is `complete` only when every applicable scanner `RAN`. `UNAVAILABLE`, `FAILED`, or `DECLINED` makes coverage `degraded`.

A degraded audit is still a valid audit. It is not a complete scanner pass. The report must not claim complete scanner coverage while any applicable receipt is not `RAN`.

## When remediation needs user approval

Application-audit summary mode separately computes overall health. A failed scanner makes that health `failed`; unavailable or declined work and self-attested host execution limit it to `degraded`. This does not change the older scanner-coverage vocabulary above. Use `closure-gate.py RECORD --summary` for the normalized output. Explicit artifact observations can verify bytes but cannot prove which tool or model ran. See the [summary contract](../../catalog/skills/code-review/security-review/references/closure-gate-review-record.md#normalized-summary-contract).

Detection and triage run before any patch. A no-fix audit may stop after triage and still close with scanner coverage reported.

Remediation runs only after detection and only with user approval, through `security-patch-advisor`. The context that writes the patch is not the verifier.

## Same-detector re-scan

A scanner-sourced correction must be followed by a re-scan with:

- the same scanner
- the same configuration fingerprint
- the same target-scope fingerprint

A before/after mismatch, a ruleset change, or a corrected finding without that re-scan fails closure. New findings from the after scan stay visible until they have a terminal or explicitly pending disposition.

## Independent verification

After a patch, a read-only reviewer consumes the before and after receipts and the patch diff. It looks for unresolved originals, new findings, and weakened controls. It does not apply patches, approve its own prior fixes, or auto-approve actions.

The fixer may appear as an additional verifier. It cannot be the only verifier.

## What this workflow does not do

- It does not install scanners or add them as project dependencies.
- It does not call a hosted scanning, search, embeddings, or generation service.
- It does not apply infrastructure changes.
- It does not treat a focused one-CVE, one-cloud-posture, patch-only, or ordinary code-review request as a full audit.

## Application-audit workflow

Start with `/work security-audit` on the explicitly authorized target. For an application-audit run, preserve the existing execution-boundary prerequisite introduced in v4.5; a user request to inspect source does not grant permission to execute it. Use the current host's registered tools and credentials only, with no new provider or key. Record offline-only declarations and self-attested host/model/settings context. Missing or unknown-quality graph tools degrade coverage and never trigger an implicit installation.

1. Collect bounded inventory with `collect-security-audit-inventory.py TARGET ROUTING_MANIFEST`, then pass its JSON to the agent-presets `resolve-security-audit-routing.py ROUTING_MANIFEST INVENTORY`. Derive positive and negative surface evidence before selecting specialists. The routing authority owns selection, batches at most four workers, and queues overflow.
2. Follow [code-search seeding](../../catalog/skills/code-review/security-review/references/code-search-seeding.md) on the authorized target and retain actual graph outcomes. Graph reachability guides review; it does not approve remediation or replace scanners.
3. Assemble the schema-v2 record and additive application-audit profile using the [closure contract](../../catalog/skills/code-review/security-review/references/closure-gate-review-record.md). Record every required owner and scanner, including unavailable or declined work. Keep raw records and tool output in an ignored owned temporary root.
4. Run `closure-gate.py RECORD --summary` to produce the normalized envelope, then pipe that envelope to `emit-sarif.py` for local SARIF. Use explicit artifact observations when claiming verified bytes. Health comes from the evaluator; content observation is not process attestation.
5. Before changing application code, obtain separate remediation approval. Use another disposable copy, equivalent scanner version/configuration/scope, functional tests where applicable, and an independent read-only verifier distinct from the fixer. Preserve unresolved findings and clean raw artifacts through validated owned-root cleanup.

Strict JSON rejects recursive duplicate keys, non-finite numbers, invalid Unicode, trailing data, excessive nesting, and oversized inputs. The common ceiling is 8 MiB with depth 32, 10,000 members, and 64 KiB strings; normalized output has tighter field limits. Physical containment checks cover roots, parents, leaves, links, hard links, and identity changes. Unsafe paths or changing artifacts fail closed.

## Repository benchmark commands

The [benchmark contract](../../catalog/skills/code-review/security-review/references/security-audit-benchmark.md) owns exact formulas and the 16-seed/16-benign cut-line. Python and TypeScript each contain the same eight weakness classes and two holdouts. Fixtures are inert syntax, never production tests or executable applications. Recall and location accuracy are separate; all target misses and unavailable host outcomes are reported without a release verdict. Deterministic corpus, scoring, binding, retention, redaction, and installer defects must be fixed.

Prepare a context JSON under the ignored `.nexus/` directory using the exact `context` fields validated by `_benchmark_protocol.py`: reported host, platform, host version, model, settings digest, registration digest, routing digest, timeout seconds, `retries: none`, and `process_attestation: none`. Unknown host facts must be named as unknown rather than invented. A terminal receipt uses the separate genuine closure producer fingerprint and its four-field `producer_context()` mapping; never rewrite a normalized envelope to match the benchmark.

Run these PowerShell steps from the repository root after creating `.nexus/security-audit-context.json` with the observed context:

```powershell
$repo = (Get-Location).Path
$manager = Join-Path $repo 'catalog/skills/code-review/security-review/scripts/manage-security-audit-benchmark.py'
$candidates = Join-Path $repo 'docs/releases/v4/v4.9/development/security-audit-benchmark/candidates'
$answers = Join-Path $repo '.nexus/security-audit-answers'
$context = Join-Path $repo '.nexus/security-audit-context.json'
$prepared = python $manager prepare-candidate --root $repo --candidates $candidates --answer-archive $answers --context $context | ConvertFrom-Json
$candidate = $prepared.candidate_id
```

Preparation freezes one map and the exact sequential/one-worker and concurrent-four/four-worker attempt IDs. In that order, create separately owned source copies using the frozen map, keep their caches/indexes/artifacts separate, and request the registered code-search capability. Record the actual result, even when unavailable. Give each host only its source projection and declared context, never answers, pairings, expected regions, severity, oracles, canaries, scorer, or map. Hash originals before/after and validate cleanup. Populate the terminal schema from `_benchmark_protocol.py`; store each terminal in `.nexus/security-audit-terminal.json` immediately before recording that attempt.

```powershell
$terminal = Join-Path $repo '.nexus/security-audit-terminal.json'
python $manager record-attempt --root $repo --candidates $candidates --answer-archive $answers --candidate-id $candidate --terminal $terminal
```

For a produced envelope/SARIF pair, add `--envelope PATH --sarif PATH`, using their explicitly selected paths under `$repo`. The manager preserves safe normalized bytes or digest-only rejection records; malformed evidence receives an evaluated unscorable outcome instead of disappearing. Repeat the record operation for the second declared attempt only after the first terminal entry exists. No hidden retry is permitted.

After both terminal entries exist:

```powershell
python $manager score-candidate --root $repo --candidates $candidates --answer-archive $answers --candidate-id $candidate
python $manager verify-candidate --root $repo --candidates $candidates --answer-archive $answers --candidate-id $candidate
$report = Join-Path $repo 'docs/releases/v4/v4.9/development/security-audit-benchmark.md'
python $manager render-report --root $repo --candidates $candidates --answer-archive $answers --candidate-id $candidate --output $report
```

The report includes both declared outcomes, exact target states, graph availability, health where scoreable, and local-ledger limitations. Identical artifacts replay byte-for-byte; changing an existing artifact is rejected. A new candidate needs a changed subject, context, or protocol and a documented supersession reason. Keep earlier candidates. Raw host records and temporary source/index roots are removed. The minimal frozen map stays in the separate ignored answer archive so verification remains possible; it never enters tracked host artifacts or installed output. Process-wide answer non-access, real model execution, and absence of omitted launches are not attested. Optional benchmark remediation is structural-only and cannot close a production patch.

All benchmark scripts/references distribute recursively with security-review on supported platforms. Repository fixtures, answers, private maps, and raw benchmark artifacts do not distribute; no installer copy block or top-level CLI is added.

## Related skills

- `security-review` -- receipts, coverage, and the closure gate
- `agent-presets` -- the ordered `security-audit` invocation
- `security-reviewer` -- read-only post-fix diff review
