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

## Related skills

- `security-review` -- receipts, coverage, and the closure gate
- `agent-presets` -- the ordered `security-audit` invocation
- `security-reviewer` -- read-only post-fix diff review
