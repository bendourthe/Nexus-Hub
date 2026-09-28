# v4.12 Attribution Push-Destination Boundary Repair

**Scope**: Post-release attribution guard repair and independent adversarial follow-up. This record preserves the original v4.12 review gap and the later regression's provenance.

The independent reviewer reproduced a push bypass in the current tree. A pre-guard commit with a forbidden `Co-Authored-By` trailer was published to one remote, then an installed guard allowed the same commit to be pushed to a different empty remote. The cause was the later `8e9bb9d9` change that excluded `--remotes` for a new destination ref, treating every local remote-tracking ref as proof that the push destination held the commit. Deleting tracking refs made the same control push block. This is a post-v4.12 regression, not a claim that the original v4.12 release introduced it.

The repair uses the actual destination URL supplied to Git's `pre-push` hook, excludes only locally available commits advertised by that destination, and sends revisions through standard input so a large ref set does not overflow the Windows command line. Missing or unverifiable destination data blocks or broadens the scan. The existing-ref old-object range remains unchanged.

## Evidence

- The new two-remote regression failed against the previous guard because the forbidden commit reached the empty destination; it passes with the repair.
- A second regression proves a stale tracking ref for the same destination cannot excuse a commit after the destination deletes that ref. It passes with the repair.
- The existing new-branch control still permits a clean branch on top of history genuinely held by its destination and blocks a newly added forbidden trailer.
- The combined `tests/test_git_attribution.py` and `tests/skills/test_presentify_measure_handbook.py` run passed 94 tests with 1 host skip in 660.10 seconds after the stale-ref and rendered-typography changes. The three targeted new-branch cases also passed before that complete run. Ruff passed for the changed guard and attribution tests; the scorer test file has one pre-existing import-order finding outside the changed lines.
- The rebuilt distribution handbook was deterministic at SHA-256 `4d2a4ae4f52b2511c62e98475bc7d14ed32928111bccf71ebba78ecd7d360716`. Chromium 151.0.7922.34 measured 200 reading and presentation states with zero errors, including no-JavaScript print and fullscreen fallback. Both handbook freshness checks and the docs profile passed (8/8).
- The independent reviewer exercised a destination advertising 821 branch refs and observed a successful clean new-branch push after the standard-input change. On the original tree, its broader attribution, installer, and manifest suite passed 182 tests with 3 host skips, and the local all-ref scan found zero findings across 1,828 commits and 140 refs. Those clean baseline results did not detect the reproduced push bypass.

## Publication boundary

This candidate requires hosted CI, merge, and post-merge verification before BG-2 closes. It does not alter GitHub's retained pull-request refs, the public contributor display, or direct API writes outside Git hooks. The independent review is complete with this finding; it is not a global clean verdict.
