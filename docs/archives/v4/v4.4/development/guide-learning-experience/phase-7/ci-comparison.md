# Terminal CI comparison

Provider: GitHub Actions, detected from .github/workflows. Scope: read-only comparison; no pipeline files changed. Integration model is develop/main. Remote is origin, repository bendourthe/Nexus-Hub; current branch is feat/v4.4.3-guide-illustration-rebuild and integration target is develop. The local integration base is bdd57cee4eb776304a09e862c1d956534db59e1e.

## Field evidence

| Field | Observed evidence | Disposition |
|---|---|---|
| Native profiles | scripts/ci/run.py exposes fast, full, platform, report, release; command inventory retained | Present; actual executed profile results are recorded separately, not inferred from --list. |
| Events | ci.yml: pull_request main/develop, merge_group, dispatch; post-merge.yml: protected branch pushes; release.yml: version tags/dispatch | Validation, smoke, and release are separated. |
| Runners | Hosted Ubuntu, Windows, macOS matrices in ci.yml | No persistent self-hosted fork runner found in the inspected primary lifecycle. |
| Required aggregate | ci-required needs all ten primary jobs, uses always(), permits only success/skipped and fails on unknown/missing results | check_required_check_coverage.py reports 10 contexts across two branches, all unconditionally produced. |
| Permissions | Primary lifecycle declares contents: read; workflow security validator executed | Read-only validation; no privileged publication added. |
| Action pinning | Full immutable action SHAs in primary lifecycle; workflow security validator executed | No new unpinned action introduced. |
| Caching | pip cache keyed by workflow dependency definition; Chromium cache keyed by OS and resolved Playwright version | Cold installer smoke uses isolated roots. |
| Concurrency | PR workflow cancels superseded runs; post-merge/release do not | Existing separation matches lifecycle. |
| Path scoping | changes job controls jobs; required workflow is not filtered by paths | Fail-closed job-level scoping and aggregate retained. |
| Reports and retention | Native profiles accept reports directories; primary ci.yml has no upload-artifact action; guide-render runs pytest without retained report artifacts | Existing gap WN-446-1: structured browser/JUnit evidence and unconditional upload/short retention should be added in a reviewed CI change. |
| Deployment boundary | post-merge is smoke/provenance; release readiness is a distinct tag/dispatch workflow | No deployment, push, merge, or release executed by this plan. |
| Failure recovery | Native runner records command statuses/timeouts; final plan requires local reproduction before retrying a red remote check | Actual local profile outcome remains authoritative; no remote run was started. |
| Installer delivery | check_installer_parity.py PASS; verify_platform_contracts.py verifies 13 platforms; real Windows PowerShell and Ubuntu Bash installers run with identical check_installer_smoke.py postconditions | Both real isolated smoke runs PASS. This does not modify or certify the user's existing installation. |

## Six-step outcome

1. Detected GitHub Actions.
2. Compared all required fields above against files and executed validators.
3. Proposed the smallest report gap closure: have guide-render emit JUnit/summary artifacts and upload them on every result with seven-day retention. Cost is small artifact storage; benefit is inspectable failed-run evidence; risk is limited to reporting configuration.
4. No additional CI change was approved. The plan's scope guard permits recording this existing difference without expanding implementation.
5. No pipeline change was applied.
6. Record WN-446-1 with maintainer ownership and a next step to approve and implement the reporting change. The comparison is partial with an owned existing gap, not a blanket CI conformance pass.

Branch hygiene and repository settings are quoted in git-preconditions.txt. They are observations of the current remote metadata, not authorization to delete branches or change protection. Expected remote gates will be refreshed against the actual PR head only after publication is approved.
