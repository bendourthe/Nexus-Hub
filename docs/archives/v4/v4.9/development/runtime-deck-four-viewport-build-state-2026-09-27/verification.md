# v4.9.2 runtime-deck four-viewport build-state follow-up

This release-scoped record extends the [original two-viewport build-state probe](../runtime-deck-build-state-2026-09-27/verification.md) on the same preserved LVEDP deck. It measures authored fragment completions at two additional sizes without editing the source blob, changing the distributed scorer, or closing [MT-3](../../../../../releases/v4/v4.9/known-gaps.md).

## Input and exercise

- **Nexus-Hub revision**: `ec16eb96` on `develop`.
- **Immutable source**: `bab8523:docs/handbooks/algorithms/lvedp-algorithm.html`, SHA-256 `c59ed271fbbaa23ba366851a7b74446d9a831abc535fd7ac115bed614144728c`, read through the local `algorithms` Git history. The former local `rd-data-dev` checkout no longer contains `bab8523`; this repository does. The [original probe](../runtime-deck-build-state-2026-09-27/probe.py) checks the blob hash before opening it.
- **Browser boundary**: Playwright Chromium loads the blob, blocks all network requests, activates the real deck-open control, navigates every slide using its dot controls, and samples each declared fragment after its finite animation end time. The probe rejects an in-memory zero-index mutation on compliant slide 8.
- **Scope change**: The probe's `VIEWPORTS` constant was overridden in memory to `[(1366, 768), (1024, 768), (768, 1024), (390, 844)]`; no file was modified. The command used the probe's `main()` entry point and the source checkout at `C:/Users/BEDOURTHE/Documents/Supira/software/algorithms`.

From the Nexus-Hub root, the following command prints the complete JSON measurement before summarization:

```powershell
python -c "import importlib.util,sys; p=sys.argv[1]; s=importlib.util.spec_from_file_location('deck_probe',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); m.VIEWPORTS=[(1366,768),(1024,768),(768,1024),(390,844)]; sys.argv=[p,sys.argv[2]]; m.main()" docs/archives/v4/v4.9/development/runtime-deck-build-state-2026-09-27/probe.py C:/Users/BEDOURTHE/Documents/Supira/software/algorithms
```

## Observed result

| Viewport | Slides reached | Timed states sampled | Fragment-budget failures | Active-slide failures | External requests | Zero-index control |
|---|---:|---:|---|---:|---:|---|
| 1366x768 | 15 | 73 | Slides 2 and 6 | 0 | 0 | Rejected |
| 1024x768 | 15 | 73 | Slides 2 and 6 | 0 | 0 | Rejected |
| 768x1024 | 15 | 73 | Slides 2 and 6 | 0 | 0 | Rejected |
| 390x844 | 15 | 73 | Slides 2 and 6 | 0 | 0 | Rejected |

Across the four viewports, 292 declared fragment completions were sampled. Slide 2 still declares nine distinct fragment indices and slide 6 declares sixteen; both exceed the eight-fragment contract. Each sampled state had exactly one active slide. The result reproduces the original non-pass at two additional sizes rather than qualifying the deck as compliant.

## Boundary and next step

The probe's opacity-and-box proxy does not establish semantic build order, actual SVG stroke visibility, all-state rendered typography, or figure re-layout. The historical deck uses `.dkslide`, not `.slide-stage`, so the distributed static checks remain `unchecked`. No visual detector JSON was produced for the runtime build states; that rendered-defect scope is **NOT COVERED** by this follow-up. MT-3 remains open for a qualified runtime path or a preserved compliant static-stage deck with negative controls for those concerns.
