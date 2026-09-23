# v4.3 CI profile follow-up reconciliation

**Reviewed on:** 2026-09-22
**Scope:** v4.3 DF-1, DF-2, and DF-3 after the v4.3 ownership repair merged through PR #240.
**Publication state:** Local candidate; hosted pull request and cache/artifact inspection pending.

## Inline validation ownership

The general validator bodies formerly inline in `ci.yml` now have one profile owner: catalog shell lint and Windows native integration tests live in `platform`; browser-backed guide and visual detector tests plus standard pre-commit hooks are explicit-only groups in `full`. The validate, test, shell, Windows, and browser jobs select these groups through `scripts/ci/run.py`. Ordinary `full` still does not require pre-commit or Chromium. Remaining inline `run` steps classify changed paths, install tools, publish receipts, assert required job outcomes, or exercise real bootstrap, installer, and Claude host smoke flows; they are workflow orchestration or host-specific end-to-end actions, not duplicate general validator lists. DF-1 needs hosted parity before closure.

## Cache ownership

The guide-render and Windows test jobs now install from scoped `requirements-*.in` manifests under the universal Python 3.11 constraints and key their pip caches to both files. The validate job already keys on `.pre-commit-config.yaml` and the lock; the test job already keys on extension project manifests and the lock. Static workflow tests guard the two corrected jobs. DF-2 still needs observed cold and warm cache behavior on the supported hosted runners before closure.

## Report ownership

The `report` profile now fails when required source receipts are missing or malformed, preserves a prior local summary for repeatable aggregation, distinguishes skipped upstream jobs, and writes an artifact hash/type index without rerunning validation. A final pull request job downloads the validation, shell, test, browser, and Windows reports, publishes one aggregate package after success or failure, and retains it for seven days. The aggregate required check includes that job. Local report, workflow, and policy tests passed; the first hosted artifact must still be downloaded and inspected. The current pull request workflow produces security-group results in its validation receipt but does not produce coverage or SARIF files, so the index cannot prove those report types. DF-3 remains open for producer design and hosted package inspection.

## Local qualification

The CI and workflow suites passed 256 tests with 17 environment skips before this branch was rebased; the rebased inventory and report checks passed 16/16. The explicit browser profile ran end to end on Windows and passed in 506.7 seconds. The Windows native selection passed 251 tests with 2 skips. The fast profile passed 17/17 and docs passed 8/8. The Linux/macOS shell command, hosted pre-commit group, cold/warm caches, and aggregate artifact remain publication gates rather than local claims.
