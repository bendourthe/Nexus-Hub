# v4.14.0 CI Helper Review

Scope is one wholly new scripts/ci/verify_scenarios.py at base d577e11037b25647aa466da4c01e1ecdadfe6aeb. N=1, K=1; union/cardinality equal scope. Full/report-only, cap 20. Correctness, maintainability, testing and standards were selected, plus security, reliability, performance, adversarial and agent-native lenses for process/input/filesystem/CLI boundaries. API-contract was not selected for a new internal helper. This calibration does not claim persona coverage of the whole 25-file bundle.

Five initial observations represented four roots: two independently proven editor-isolation observations, removal of shared PATH directories, inherited Git routing and surviving descendants after timeout. Proven observations had confidence 100; differently titled fingerprints were not synthetically promoted. The testing-only missing-negative-controls candidate started at 75, was demoted to 50 under report-only advisory scoring, and was retained. Controls were added as implementation work regardless. Fixes prepend inert launchers, preserve PATH, clear Git routing, isolate package paths and terminate process trees. That first recheck at SHA-256 5b95f476cc01614cfcb8df95603995f762f07426cdf3a52f3b639e13311c97a1 was subsequently narrowed by a concrete missing-prerequisite finding: the bootstrap can invoke brew, apt or winget for absent Node, outside HOME/cache containment. Revision 2 requires both node and npm on the isolated child PATH before archive creation or installer execution, and both workflow jobs explicitly provision Node 22. Independent sentinel probes confirmed each absent tool refuses with zero archive or installer calls. The bounded finding is corrected at SHA-256 f91a7cbfb018ed8d84f547b253f0be9779590069028c293fe9aaaeea2e4eda34; no remaining issue was found within that recheck scope. No real package manager was invoked by the probes.

Deterministic rechecks exercised actual PS5.1 cleanup command resolution, redirected-grandchild timeout and a fake Cursor CLI with both private stores. No real editor delivery is claimed. Candidate contracts passed 347 tests with 19 skips, 88 percent CI-package and 81 percent helper coverage. The final suite includes the missing-node, missing-npm and Node-setup ordering controls; lint has zero new diagnostics on 13 Python files. No paid model API call was used.

| Considered but rejected | Reason |
|---|---|
| Bootstrap tolerates installer failure before artifact/version checks | Intentional original acceptance contract; extraction/version still required. |
| Registry aggregate verify can fail | Original checks require the same selected five read paths; unrelated integrations can be absent. |
| Archive traversal | Absolute, parent and resolved out-of-root paths are rejected. |
| Shell injection via root | Fixed choices and argument vectors keep shell=False. |
| Generic abstraction for two OS branches | Adds complexity without user benefit. |
| Existing bootstrap precheck contains Node installation | Rejected: downloader, tar and Python checks do not require Node/npm; revision 2 now does. |
| Redirected package caches isolate host package-manager installation | Rejected: host installation targets are outside redirected caches; revision 2 prevents missing-tool setup. |
| Node/npm guard uses parent PATH or runs after tar creation | Rejected by explicit child PATH and guard ordering, independently probed. |
| Archive performance concern | Interrupted exploratory timing had no baseline and proved no regression; working-tree fidelity is intentional. |
| Agent action/context gap | Discoverable CLI choices and status/assertion messages are available. |
