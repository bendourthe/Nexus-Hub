# Native handbook authoring benchmark

This record separates original first-build performance from later repaired-workflow qualification for the v4.9.1 handbook plan. Read it when assessing T020 and R12; a later successful attempt does not erase a failed first build or demonstrate universal reliability. Current acceptance is one of three required input families.

Each model run receives one frozen prompt, unchanged factual inputs and at most three internal correction rounds. Shared-owner fixes are installed only into fresh workspaces; failed output and operator diagnostic repairs are not supplied to subsequent authors. Runtime startup and collection are serialized to preserve Windows read-denial boundaries. Independent host grading opens unchanged collected Office files because native Office automation is unavailable to the sandbox logon account.

| Attempt | Limit / elapsed seconds | Internal corrections | Independent final result |
|---|---|---|---|
| Repository original | 2100 / 2100.75 | No terminal record | Non-pass: time limit. |
| Report original | 2100 / 2100.83 | No terminal record | Non-pass: time limit. |
| Presentation original | 2100 / 2100.94 | No terminal record | Non-pass: time limit; native PowerPoint rejects the package. |
| [Repository repaired](phase-6-native-attempts/repo-repaired/summary.json) | 3600 / 3545.84 | 3 | Non-pass: unresolved print contrast. |
| [Report repaired](phase-6-native-attempts/report-repaired/summary.json) | 3600 / 3162.33 | 3 | Non-pass: native Word table exceeds the page; explicit font loses to theme attributes. |
| [Presentation repaired](phase-6-native-attempts/presentation-repaired/summary.json) | 3600 / 3272.41 | 3 | Non-pass: native process and chart entrance effects absent. |
| [Repository final](phase-6-native-attempts/repo-final/summary.json) | 3600 / 3600.75 | No terminal record | Non-pass: time limit and independently reproduced alternate-panel overflow. |
| [Report final](phase-6-native-attempts/report-final/summary.json) | 3600 / 3247.39 | 3 | Accepted: factual, engineering, rendered design, retained rebuilding and native/static export checks pass. |
| [Presentation final](phase-6-native-attempts/presentation-final/summary.json) | 3600 / 3167.30 | 1 | Non-pass: required native motion works, but an automatic title is black on its dark chart. |
| [Repository extended](phase-6-native-attempts/repo-extended/summary.json) | 5400 / 3770.25 | 3 | Non-pass: left-side slide branding and whole-figure process fade. |
| Presentation readable | 3600 / running | Ceiling 3 | Pending terminal result and independent grading. |
| Repository semantic | 5400 / queued | Ceiling 3 | Starts after presentation terminal status and collection. |

The three original first builds have a 0/3 passing rate. Their [original receipt](phase-6-native-attempts/original-first-build-summary.json) and exact artifacts remain preserved. Two earlier launches failed during native session initialization before model turns; they are runtime failures, not authored first builds. Elapsed durations include the wrapper's shutdown overhead, which can slightly exceed the declared model-run timeout.

Terminal token-usage objects are retained in each completed attempt's execution receipt. Timeouts without a terminal usage event have unknown actual token usage. Monetary costs are unavailable for these runs and are not estimated or reported as zero. This bounded fixture result does not establish a spending cap or production-wide one-request reliability.

Every accepted family must pass independently on its final hashes within its own invocation and correction limits. Diagnostic after-images prove a shared correction only; they never satisfy that gate. Phase 6 stays open until repository, report and presentation all qualify.
