# v4.4 CQ-1 current-branch CodeQL rescan

This record closes v4.4 WN-446-2's missing current-head scan. It does not dismiss a historical pull-request alert or claim that the repository has no other CodeQL findings.

## Scan receipt

- Manual [CodeQL run 36106037432](https://github.com/bendourthe/Nexus-Hub/actions/runs/36106037432) analyzed `develop` at `d6477ccf798d24487f3101f2c08049cd6b803c57` on 2026-09-25. Both `Analyze (javascript-typescript)` and `Analyze (python)` completed successfully.
- The scanned guide blob was `532dec2f3d78cfd27b3db10a93848c883740e033`. The current guide contains neither `data-motion-src` nor `initMediaToggles`, the construct named in CQ-1.
- The authenticated, branch-filtered `GET /repos/bendourthe/Nexus-Hub/code-scanning/alerts?ref=refs%2Fheads%2Fdevelop&state=open&per_page=100` was paginated across all results. It returned 184 open alerts, zero at `guides/website/nexus-hub-guide.html`, and two unrelated `js/xss-through-dom` findings in v3.12 worked examples. The nonzero result set is a control against treating an empty or failed query as success.
- `GET /repos/bendourthe/Nexus-Hub/code-scanning/alerts/236/instances` returned one historical open instance on `refs/pull/156/merge` at `835c141b`, in the guide. It returned no `develop` instance. The alert record is retained by GitHub and was not dismissed or deleted.

## Disposition

WN-446-2 is resolved for the current integration branch because a fresh remote analysis of its exact head found no open guide alert. This result does not close the 184 other branch-open findings, change the state of historical PR #156's alert, or replace the separate native-profile and manual guide gates.
