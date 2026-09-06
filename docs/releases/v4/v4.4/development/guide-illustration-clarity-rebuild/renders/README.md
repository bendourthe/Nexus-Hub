# v4.4.3 Render Evidence

`phase-9-browser-summary.json` is the authoritative record of the declared browser matrix run: the
declared case count, the executed count, per-case results, the fullscreen geometry readings, and the
runtime and evidence budgets. It is committed.

The 138 PNG screenshots from that run are NOT committed. The v4.4.2 phase-7 set is 28 MB in this
repository, and committing a second full set for every visual iteration would grow the repository
faster than the evidence is read. Regenerate them at any time with:

```bash
python tests/guides/tools/browser_matrix.py --label phase-9
```

The summary JSON records what each case asserted, so a reviewer can tell from the committed file
which cases ran and whether any failed. If a future review wants the images committed, that is a
deliberate choice to make rather than a default.
