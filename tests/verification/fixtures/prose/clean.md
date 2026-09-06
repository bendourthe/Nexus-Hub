# Clean fixture

This file is deliberately tricky human prose. The detector must return zero findings on it.

Did the release ship on Friday? No. Was it tested on Thursday? No. It shipped the following Tuesday after the index was rebuilt, and the rebuild is the crucial step: without it, every lookup on the orders table becomes a full scan.

Why did the cache miss? Because the key included a timestamp. One question is enough here, and the answer follows it directly.

The first attempt failed. It was slow. It cost a week. Three short sentences in a row are a rhythm the writer chose, and none of them shares a skeleton with its neighbour or opens on the same content word.

We said no to the vendor, no to the consultant, and yes to the intern's prototype. That is a list with two negatives and a reversal, not a chain.

Tests catch bugs. Compilers catch type errors. Reviews catch design mistakes. The three openers differ, so this is parallel structure that stays under the repeated-opener threshold.

It is important that the on-call engineer can read this page at three in the morning, so every command below runs as pasted.

| Column | Meaning |
|---|---|
| no | this table row must be skipped, not scanned |

```text
Honestly, code blocks are skipped too. Turns out, this line never counts.
```

A dash inside a compound word like well-tested or a hyphenated range like 2024-2026 is not a clause-joining connector.

Consecutive list items are parallel by design and must not count as a run of same-opener sentences:

- Tests catch the regressions the compiler cannot see.
- Tests document the behavior the author meant.
- Tests slow a change down just enough to read it.
- Tests are the only artifact here that runs.

Paragraph breaks reset the rhythm rules. Tests catch bugs.

Tests document intent. A new paragraph between two same-opener sentences means they were never consecutive.
