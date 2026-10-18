# v4.14.0 CI Comparison

GitHub Actions is compared against the canonical lifecycle contract. Proposed items are unapplied. Full final-tree local and remote qualification remain pending after approval.

| Field | Evidence and disposition |
|---|---|
| 1 Provider | GitHub Actions workflow tree and live repository API. |
| 2 Profiles | Actual candidate CLI resolves all five unchanged names; profile-resolution.json retains outputs. |
| 3 Validator ownership | Proposed native groups for existing monitor, offline-container, colocation, bootstrap, registry, workspace, optional Cursor and Presentify checks. Provider setup/detection/aggregation/publication remain orchestration. |
| 4 Feature push | Existing validation does not trigger on ordinary feature pushes. |
| 5 Integration coverage | Proposed required current-7 boundary job alongside unchanged complete 5.1 installer job; existing full suite and host matrices stay. |
| 6 Duplicate suite | Existing protected post-merge flow does not repeat the complete suite. |
| 7 Post-merge | Existing fast smoke and provenance remain. |
| 8 Release | Existing tag/dispatch release-profile separation remains. |
| 9 Aggregates | Preserve ci-required and verify names; verify includes render; proposed memory-required and cursor-required fail closed. Single-job workflows aggregate native commands directly. |
| 10 Required legs | Both protected branches require ci-required, validate, shellcheck, colocation and verify, with no matrix-leg names. Runbook explains deliberate validate/shellcheck redundancy. |
| 11 Scoping | Required-producing workflows remain event-unfiltered; heavy selection stays in jobs. Optional monitors additionally watch scripts/ci. |
| 12 Runners | Existing standard hosted Linux/macOS/Windows classes; no self-hosted runner. |
| 13 Expensive legs | Existing native matrices stay pre-merge; proposed deterministic render moves from schedule to selected pre-merge validation. |
| 14 Pins | Full action SHAs/version comments retained; new job reuses current checkout/setup pins; bootstrap jobs reuse the existing pinned setup-node v4 action for Node 22. Offline image digests and constraints retained. |
| 15 Permissions | Existing explicit read permissions remain; no permission, secret or authentication change. |
| 16 Caches | Existing manifest/lockfile keys retained, cold-install targets disposable, new package prefixes/caches private; both bootstrap jobs explicitly set up Node 22 without a cache. |
| 17 Concurrency | Superseded validation cancellation retained; release behavior unchanged. |
| 18 Forks | No privileged trigger, extra credential or self-hosted execution; documented human restrictions remain. |
| 19 Reports | Proposed host/direct-execution metadata, more tool versions, generic KEY redaction including JSON-escaped values. JUnit/coverage/SARIF remain with producing groups. |
| 20 Publication | Proposed always-run summaries/seven-day report uploads, main aggregation extended to newly reporting jobs. |
| 21 Deployment | Existing protected-event deployment boundary unchanged. |
| 22 Recovery | Runbook still requires local reproduction before stabilization repush; no blind rerun. |
| 23 External settings | Runbook retained; fresh API reads verify both protected branches. No settings mutated. UI-only/billing observations remain unclaimed. |

## Cost and limits

Adds one focused Windows job and three short aggregate jobs. Linux rendering moves from schedule to path-selected pull requests. Existing Node, container and native host work is reorganized. Two existing bootstrap jobs explicitly provision Node 22 and the helper refuses missing node or npm before any archive or installer work; it cannot invoke a host package manager through that missing-tool path. Local current-7 qualification took 335.5 seconds, registry 91.0 seconds and workspace 12.0 seconds. Incremental hosted dollars and Linux render runtime are unmeasured. No paid model API call or new vendor service is used. Actual macOS, offline Docker, all Node/VSIX groups, optional live Cursor and final complete local/remote gates remain required. Both final fast profiles passed all 17 commands after identified user-path components were redacted from public receipts. Raw local originals are preserved separately with hashes. The earlier fast run with personal paths remains a failed run, never a pass.
