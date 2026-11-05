# Minor-Close Handbook Dependency Review

The v4.14 archive moved the existing overview review artifacts into the archive and changed one documented evidence path in an Aider source comment. This review covers those archive dependencies on 2026-11-05. No handbook HTML, model, narrative, CSS, composition, runtime, figure, anchor, or presentation setting changed.

## Dependency Comparison

The native full inventory identifies no changed overview input, entry fingerprint, or output hash. Its existing content, build, and rendered evidence remain byte-identical; only their repository-relative locations need repair. Distribution has the same entry and output fingerprints and exactly one changed input: `scripts/lib/integrations/aider.py`. Comparison against merged develop `2cb37c5b4` proves an identical Python AST. The sole source difference relocates the detection-evidence comment from the active release tree to the archive. Executable detection, the shared CONVENTIONS.md guidance surface, YAML read defaults, attribution settings, and managed-file ownership retain the same implementation and claims.

## Build and Browser Checks

Both retained builder --check commands passed against the current files. Overview retains output SHA-256 `b5c39c8adebebcd8f8ef03016c6a301aaebcab8e15a259838d12a0243a8f671f`; distribution retains `7bea7bd87e5c498c8c36feb7be76cb7aa00a65b1c8834c8c566209c0bb07587c`. The [build receipt](minor-close-handbook-build.json) records the actual commands, exits, fingerprints, and AST comparison.

The retained native-control browser recipe passed 80 presentation states and 16 reading states in Chromium at 2560x1300, 1920x1080, 1366x768, and 390x844 with both forced palettes. Entry/reset, five-slide navigation, disabled final Next, Escape, focus return, and re-entry passed with zero page errors or failed requests. The [fresh smoke receipt](minor-close-handbook-browser.json) retains the actual state and screenshot hashes. Representative desktop overview and compact distribution frames were inspected. This smoke check supplements the original broader rendered evidence; it does not replace or restamp that evidence, whose output bytes and relevant visual inputs remain unchanged.

## Evidence References

The overview receipt keeps its original snapshot, verdicts, and proof hashes while relocating the three proof paths into the archive. The distribution receipt records the current input snapshot and this limited content review plus the fresh retained-build receipt. Its original rendered report is relocated with its existing browser identity, output hash, and evidence hash preserved. Historical reports and native run records are not rewritten. A fresh full handbook check remains the acceptance gate for the updated metadata.
