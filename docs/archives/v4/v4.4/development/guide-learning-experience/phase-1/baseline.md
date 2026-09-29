# Baseline

Source SHA-256: `68f017bcac2a7c58278ce3ad7642f5860279784707e3ef4ee5fef15c8d39ec7d`; 396,424 bytes. Raw measurements: [audit.json](../baseline/audit.json). Captured browser views and inspected findings: [design review](../design-review.md).

| Page | Main-path words | Total words | Height at 1440x900 | Height at 420x900 |
|---|---|---|---|---|
| Home | 1,036 | 1,150 | 5,390px | 10,313px |
| Foundations | 2,459 | 2,459 | 8,648px | 15,292px |
| Training | 416 | 416 | 2,148px | 3,374px |

The shared audit clones each page's DOM and excludes navigation, scripts/styles, code, and closed details from the main-path count. Total words includes closed details. Diagram labels and examples count. Hidden sequence content is included so animation cannot artificially improve the result. Targets: Home <=777 main-path words; Foundations <=1,598.

The 72-case matrix covered four pages, both themes, and widths 320/420/719/720/721/768/1024/1440/1920. No document overflow, JavaScript error, or runtime external request was observed. Cold-load Foundations had 17 transparent sequence nodes. The tall mobile harness still had hidden steps after ordinary scrolling in the retained review evidence. Ancestor inspection found no clip-path or containment boundary; the 40% observer threshold alone is not proven as the cause because the callback checks isIntersecting. The design fix removes opacity as a content gate and observes only bounded optional effects.

Performance includes one warmup and three samples per light desktop, dark desktop, and light mobile. Scroll lasts ten seconds, followed by twenty route changes. Sample p95 frames were 16.7-16.8ms; maximum navigation feedback was below 31ms. Median dark task time was 1.717s versus light desktop 0.935s and mobile 0.818s. Desktop had about 611 layouts and 2,313 style recalculations per sample; mobile about 785 layouts and 2,487 recalculations. These are optimization targets, not proof of a particular cause.

Limitations: the broad baseline suite overlapped the early audit samples; light desktop had isolated 384/463ms long tasks that cannot be attributed to the guide alone. Final comparisons must record this confound and use clean repeated runs before concluding a latency regression or improvement. Training/resize and CPU-throttled diagnostics remain part of later functional verification.
