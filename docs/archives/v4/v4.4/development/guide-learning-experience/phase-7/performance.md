# Final performance comparison

Guide SHA-256: `6848938156266c2806c734575c963a64ba71a84bf3b357e912e0583b730324fd`. Baseline: `bdd57cee`, SHA-256 `68f017bcac2a7c58278ce3ad7642f5860279784707e3ef4ee5fef15c8d39ec7d`.

Each configuration has one warmup and three measured runs. Each run scrolls Foundations for ten seconds and switches Home/Foundations twenty times. Original, final, and 4x-throttled final runs executed sequentially with no competing guide browser job. The native repository test profile was running in the background, so these are controlled local observations, not a claim of an otherwise idle machine.

| Artifact | Theme / width | Median task time (s) | Worst p95 frame (ms) | Longest observed task (ms) | Maximum navigation feedback (ms) |
|---|---|---:|---:|---:|---:|
| original | light / 1440 | 0.778 | 16.8 | 0.0 | 20.3 |
| original | dark / 1440 | 1.541 | 16.8 | 0.0 | 28.4 |
| original | light / 420 | 0.781 | 16.7 | 0.0 | 26.0 |
| final | light / 1440 | 0.282 | 16.7 | 0.0 | 22.9 |
| final | dark / 1440 | 0.392 | 16.7 | 0.0 | 19.8 |
| final | light / 420 | 0.254 | 16.8 | 0.0 | 19.6 |
| throttled | light / 1440 | 1.593 | 16.8 | 0.0 | 75.4 |
| throttled | dark / 1440 | 2.170 | 16.8 | 0.0 | 85.3 |
| throttled | light / 420 | 1.640 | 16.8 | 0.0 | 92.2 |

The median task duration across the nine unthrottled measured samples falls from 0.805s to 0.284s, about 65% less browser work. Both artifacts have a worst p95 frame of 16.8ms on this machine; the comparison does not claim an FPS improvement. The final artifact meets the proposed <=33ms p95 frame, <=200ms navigation, and no observed >100ms long-task budgets, including the separately labelled 4x run.

The Phase 2 lifecycle regression identified and removed the unconditional hidden Training game frame loop. That root-cause proof is separate from this timing comparison. Long-task observation covers the ten-second scroll window; navigation feedback and Training feedback are measured directly rather than inferred from it.

## Interaction results

| CPU rate | Maximum Training feedback (ms) | Maximum resize first frame (ms) | Result |
|---|---:|---:|---|
| 1x | 16.1 | 37.5 | Eight ordered command completions and 18 resizes passed |
| 4x | 24.1 | 102.7 | Eight ordered command completions and 18 resizes passed |

The interaction audit also passed 88 offline page/theme/width cases and exposed all four reading pages plus seven Foundations lessons with JavaScript disabled. Resize measurements include Playwright viewport round-trip overhead. Effective CSS-width cases are reflow evidence, not native browser zoom proof. Raw results are retained in the adjacent performance and interactions directories.
