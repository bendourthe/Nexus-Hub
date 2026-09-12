# Last-Phase Evidence - v4.11.0 Interactive Handbooks

**Project**: Nexus-Hub
**Plan**: [v4.11.0 interactive handbooks and presentation default](../../plans/v4.11.0-interactive-handbooks-and-presentation-default.md)
**Phase**: 7 - Architecture Refactor, Known-Gaps Reconciliation, and CI/CD
**Branch**: `feat/v4.9.1-interactive-handbooks` (the branch name predates the renumber; the plan is v4.11.0)
**Base**: `origin/develop`
**Started**: 2026-09-12
**Status**: in progress

Each duty below records the command that proves it. A duty with no proving
output is recorded as unverified, never as a pass.

## Architecture refactor

**Scope**: only complexity introduced by this feature, and one owner per concern.
Unrelated guide CSS and historical documentation were not swept.

### Scans run

Stale exact-one-mode prohibitions across the active command and skill surfaces:

```
grep -rniE "exactly one (mode|view|output)|only one (mode|view)|must not (also )?(produce|emit) (a )?(deck|presentation)|no presentation mode" \
  catalog/commands/ catalog/skills/specialized-domains/document-to-interactive-html/ \
  catalog/skills/developer-experience/html-output-conventions/
(no matches)
```

Blanket decoration bans, which the dual-view default would contradict:

```
grep -rniE "never use (gradients|shadows|animation)|no decorative|decoration is (banned|forbidden)" \
  catalog/commands/ catalog/skills/
(no matches)
```

Both scans are empty. The empty result is quoted rather than asserted, because
an empty scan and an unrun scan are indistinguishable in a summary.

### Finding: two owners for rendered overlap, and they contradicted each other

The one-owner scan was not empty. Two scripts measure overlap:

- `catalog/skills/testing/functional-verification/scripts/detect_visual_defects.py`, rule `text-overlap`, comparing every painted text fragment against every other in the document.
- `catalog/skills/specialized-domains/document-to-interactive-html/scripts/measure_handbook.py`, comparing an SVG label against the shapes it straddles.

The second is correctly scoped. The first was not: its loop compares text pairs
document-wide, so a sticky or fixed navigation bar drawn over the body text
scrolling beneath it reports as a high-severity defect. That is the feature, not
a defect - covering flow content is what taking an element out of flow is for.

This directly contradicted the declared-position gate added in Phase 6 of this
plan, which fails a build whose navigation declares `position: sticky` and does
not compute as sticky. One gate required the bar to be sticky; the other
reported the consequence of it being sticky. Working navigation was deleted
three times to satisfy both, recorded as WN-5 in the ledger.

**Root cause**: the cluster had no rule-ownership table, which `AGENTS.md`
requires when two skills cover adjacent territory.

**Resolution**, both halves applied:

1. `text-overlap` now skips a pair when exactly one side sits inside an OPAQUE
   out-of-flow layer. Opacity is the whole condition, and it comes from the
   ledger's own suggested step rather than from the first fix attempted here: a
   TRANSPARENT sticky bar does not occlude, so its text and the prose beneath
   genuinely collide and are still reported. Two fragments inside the same
   layer, or both in normal flow, compare exactly as before, so an overlap
   within one header remains a real defect wherever the header sits.
2. A `## Rule ownership` table was added to the handbook skill naming exactly
   one owner per concern across the two skills.

**Negative control**, run in both directions, because an exemption can fail by
being absent OR by being too broad:

```
### CONTROL 1: exemption disabled ###
E       AssertionError: assert 2 == 1
1 failed, 1 passed, 38 deselected in 3.07s

### CONTROL 2: opacity ignored (every layer exempt) ###
E       assert 0 == 1
1 failed, 39 deselected in 1.94s

### RESTORED ###
2 passed, 38 deselected in 2.84s
```

Without the exemption the opaque bar reports a spurious finding against the
paragraph beneath it. With the exemption widened to every sticky element, the
transparent bar's real collision disappears. Only the opacity-conditioned rule
passes both. WN-5 is closed at root cause rather than by suppressing the rule.

### Finding: a committed merge conflict that the repository's own gate missed

`80690ff8` committed the v4.11.0 plan carrying eleven unresolved conflicts while
`check_merge_conflict_markers` reported clean on the same revision. Git widens
the marker run past seven when the two sides disagree about the PATH as well as
the content, so the rename that moved this plan from `v4.9` to `v4.11` wrote
`<<<<<<<< HEAD:old/path` with eight characters, and the check anchored on the
literal seven-character form.

```
new gate on the shipped file: 22 markers
new gate on the resolved file: 0 markers
```

Eight of the eleven hunks had byte-identical sides, which is the signature of a
rename conflict: when only the path differs, git cannot take either side and
emits every hunk. The three whose sides actually differed were resolved on their
merits and recorded in `38e1c717`. The gate now matches seven or more, and the
test that was missing is added with every fixture negative-controlled.

Fixed in `38e1c717`; the overlap work is staged for the Phase 7 commit.

### Not changed, and why

- The two overlap implementations are NOT merged into one. They measure different things (text-vs-text in a layout layer; label-vs-shape inside an SVG) and merging them would give one script two responsibilities to serve a false symmetry.
- No unrelated guide CSS, historical evidence, or v4.9 security-audit documentation was touched.

## Known-gaps reconciliation

### Derived counts

```
grep -o "^#### [A-Z]*-[0-9]* - [A-Z]*" docs/releases/v4/v4.11/known-gaps.md
     13 RESOLVED
      2 CLOSED
      2 open (MT-5, MT-9)
```

Seventeen items, all accounted for. The counts are derived from the ledger
rather than restated from memory, because a hand-kept tally is the first thing
to drift.

### Closed this phase

- **WN-5** - RESOLVED in T022. Full record in the Architecture refactor section above.

### Closed earlier, recorded here so neither reads as a pass

- **WN-3** - CLOSED as authoring guidance. Composition balance cannot be judged without a beauty detector, which this plan forbids. It is guidance, not a gate, and is stated as such.
- **QG-2** - CLOSED AS UNMET and carried forward. Three of three simultaneous single-invocation delivery was not achieved: the best sustained result across six rounds and roughly fifteen hours of qualification runtime was two of three. Recording it here does not waive it. The claim v4.11.0 ships is the narrower true one: each of the three source families has been independently qualified to pass, the tooling that judges them is verified and negative-controlled, and simultaneous delivery across all three within bounded repair is NOT established.

### Carried forward, with owners

- **MT-5** - No automated coverage for values fabricated mid-animation. **Transferred** to [v4.11.2](../../plans/v4.11.2-adoption-document-and-deck-quality.md), whose Phase 5 T014 requires every series to name the computation it came from and fails an unsourced one, and whose Phase 4 T012 measures animation state at the moment it is current. Reason for transfer rather than deferral: v4.11.2 already builds the provenance record this gap needs, so implementing it here would duplicate that machinery.
- **MT-9** - A control that exists but does nothing is not detected. **Remains open, owner unchanged.** The obvious check was built, failed three ways (wired onto a page with JavaScript disabled, no state reset between probes, false positives on idempotent controls while missing the target defect) and was backed out entirely rather than left in reporting noise. Next step is recorded and specific: inert-control detection needs CDP listener-chain inspection, not activate-and-observe. That is a different instrument, not a tuning of this one.

### Other ledgers inspected

Every non-archived `known-gaps.md` was scanned for a dependency on this feature.
All that mention it are finalized or released except `v4.9`, whose reconciliation
line still claimed this plan was queued at 0 of 7 phases and 0 of 31 tasks. That
line is corrected to 6 of 7 and 21 of 31 with a pointer to the moved ledger,
rather than deleted, because it is what a reader of the v4.9 cycle would
otherwise still believe. The v4.11 ledger's own status line still said Phase 6
was incomplete and is corrected the same way, retaining the mid-phase detail as
the record of that round.

No unrelated guide gap was touched. No failed quality gate was turned into a pass.

## Living docs architecture

The self-hosted check was run against Nexus-Hub's own handbooks, and it found
real staleness rather than confirming a pass.

### What the inventory found

`docs/handbooks/` carries two mapped handbooks, `overview` and `distribution`,
with retained sources, a build record and an evidence record each. Ten
`_sources/**` fragments are explicitly excluded as assembled inputs rather than
standalone handbooks, so the map accounts for every HTML file under the tree.

Both were **stale**. Their sources were unchanged and their outputs matched
their own records, but the BUILDER had moved: `dual-view-runtime.js` and
`dual_view.py` both changed in Phase 6 (the BG-2 instant-scroll restore and the
BG-6 directory scroll cap) and the handbooks were last built four commits
earlier, at `a4349d40`. A freshness gate that hashed only inputs and outputs
would have called this clean. Hashing the builder is what makes "the same
source no longer produces these bytes" visible.

### The recorded pass had never faced the gate

Rebuilding was not enough. The rebuilt handbooks failed the rendered pass with
100 errors each, all of them the WN-2 opening-screen opacity floor. The decisive
experiment was to measure the PRE-rebuild bytes with the same gate:

```
OLD BYTES status: fail errors: 100
   reading/purpose/2560x1300: opening-screen content at opacity 0.85 -- 'One catalog, several hosts'
```

The old bytes fail identically, so the rebuild did not cause it. The commit
order explains it:

```
a4349d40  built the handbooks and recorded their rendered evidence as pass
59492077  ADDED the opening-screen opacity gate, four commits later
```

The repository's own handbooks had never been measured by a gate this plan
shipped. Their recorded `pass` was produced by an earlier instrument. This is
precisely the staleness `check_handbooks.py` exists to make visible, and it is
the argument for the self-hosted check: the gate found its own author's
documentation non-compliant.

### The failure was the gate's, and the measurement decided it

The 0.85 was not an animation. It is an authored token in the handbook's own
`design.css`: `.handbook-map span { opacity: .85 }`, a deliberate de-emphasis
of secondary text. Rather than decide by preference whether that is a defect,
the composited contrast was measured:

```
{"measured": 4, "below_wcag": 0,
 "rows": [{"text": "One catalog, several hosts", "alpha": 0.85,
           "raw_ratio": 14.44, "composited_ratio": 10.75, "floor": 4.5}]}
```

10.75:1 against a 4.5:1 floor. The text is plainly legible, so a gate failing it
is reporting a design choice as a defect.

The root cause was a split concern. The contrast pass scored the DECLARED ink,
folding in neither the element's `opacity` nor the ink's own rgba alpha, so
semi-transparent text measured as fully opaque and over-reported passes. WN-2
was patching that hole from the other side with a bare opacity number, which
cannot distinguish 0.85 on near-black (10.75:1, fine) from 0.96 on mid-grey
(below the floor). Two gates, one question, neither answering it.

**Resolution**, which makes the tooling stricter overall:

1. The contrast pass now composites the ink over its backdrop at its effective alpha - the element's own rgba alpha multiplied by every inherited opacity - so contrast is the single owner of legibility for every colour.
2. The opacity floor is narrowed from 0.95 to 0.5 and keeps only what contrast cannot see: content more absent than present, which reads as a reveal that never ran whatever colour it is. The defect WN-2 was built from measured 0.45 and still fails; so does the stacked 0.7 x 0.7 = 0.49 case.

**Negative control, and a test that had to be thrown away.** The first fixture
chosen for the transparency test was `rgba(120,120,120,0.62)`, which scores
4.42:1 on the declared ink - already below the floor. It therefore passed
against the UNFIXED gate and proved nothing:

```
### CONTROL: score the declared ink, as before ###
1 passed, 40 deselected in 2.76s        <- should have failed
```

Replaced with `rgba(85,85,85,0.45)`: 7.46:1 declared, a comfortable pass, and
2.11:1 as rendered. Only the composited measurement separates those.

```
### CONTROL: declared ink, as before ###
E       AssertionError: []
### RESTORED ###
7 passed, 34 deselected in 18.08s
```

A test that cannot fail against the unfixed code is not evidence, and the only
way to learn that is to run it against the unfixed code.

### Final state

```
overview     status: pass  errors: 0
distribution status: pass  errors: 0
check_handbooks exit=0
```

Both handbooks rebuilt, re-measured on their final bytes, and their evidence
records regenerated through the gate's own `snapshot()` function rather than by
hand. The rendered evidence now names the browser and the final output hash of
the bytes actually measured.

### A gate message that cost three round-trips

`check_handbooks.py` reported `stale source, builder, mapping or output
evidence` - four candidates, no indication which fired - sending the reader to
diff snapshots by hand. It now names the drifting key:

```
overview: stale evidence -- inputs: .../assets/dual-view-runtime.js,
  .../scripts/dual_view.py; output_sha256
```

That turned a four-way guess into a two-item list on the next run.

## Git-tree hygiene

**Branch**: `feat/v4.9.1-interactive-handbooks` (the name predates the renumber).
**Base**: `origin/develop`. 21 commits ahead, 338 files changed at phase entry.

```
python scripts/check_release_preconditions.py --branches --repo-settings
  OK: delete_branch_on_merge is enabled
  Reporting only -- nothing was deleted.
  exit=0
```

One NOTE, not a blocker: the GitHub repository description says 336 skills while
`README.md` declares 337. The description is not a version-carrying surface, so
`check_version_sync.py` cannot see it. It is a hand-edited GitHub setting and is
carried to the release handoff.

### Encoding and links, scoped to changed Markdown only

83 changed Markdown files. Unicode safety: clean, no failures. Relative links:
seven dangling, of which three were broken by the v4.9 to v4.11 move and are
repaired here (two in `docs/DEVLOG.md`, one in `docs/todos.md`). Six more
dangling references inside the two handbook `evidence.json` files were repaired
the same way.

The remaining four were each confirmed present on `origin/develop` before this
branch existed and are therefore out of scope under the repository's
changed-lines rule. Two are genuine (`implementation-plan` points at the removed
`generate-plan.md`; `docs-layout-refactor` has a wrong relative depth) and two
are false positives of this scan (a prose placeholder, and a
repository-root-relative target). They are recorded, not swept.

### Nothing private or transient enters the tree

No personal path (`validate_no_personal_paths`, green in every fast profile run
this phase), no private corpus, and no temporary model asset. The retained PNG
and PPTX artifacts under `phase-6-native-attempts/` are qualification evidence
the plan requires to be kept, in their canonical evidence location.

## Terminal CI/CD reconciliation and distribution parity

```
python scripts/check_installer_parity.py             installer parity: PASS   exit=0
python scripts/check_platform_contract_freshness.py  OK for v4.9.0           exit=0
python scripts/validate_skills.py --bundles-only     337 skills, PASS        exit=0
python scripts/sync_platform_defaults.py --check     14 platforms in sync    exit=0
```

### Pipeline change applied, and why it was necessary

`check_handbooks.py` shipped in `788e801f` and was wired into **no CI profile**.
A gate the plan built, that the repository never ran. In that window both
repository handbooks went stale against two Phase 6 builder fixes with nothing
reporting it - the failure this phase had to find by hand.

It is now a hard gate in the `docs` group. Cost: it is read-only and hash-only,
launches no browser, and adds about one second. It runs in `full` only, so the
`fast` pre-commit gate is unchanged at 14 steps. This is the deterministic
handbook check T026 directs, using the existing group rather than a new job - a
new job would need its own required-check context, which
`docs/policy/required-checks.json` and `check_required_check_coverage.py` gate.

No other pipeline file was edited.

### Not performed, and stated as such

A fresh vendor re-verification of the platform read-contract was NOT run this
phase. The freshness gate passes because the contract is verified for v4.9.0 and
is not yet stale, but the contract is re-verified at `/update release` by the
platform-contract-verification step, and that is where it belongs: it fetches
official documentation for 14 platforms and its result must describe the version
being published. Recorded as a release-handoff item, not claimed as done.

## Tier 3 deep pass

Exercised on the FINAL bytes of both repository handbooks, through the real
output boundary rather than a structural score.

```
docs/handbooks/overview.html      33937d67b7041d9e   status: pass   errors: 0
docs/handbooks/distribution.html  7954761932c41257   status: pass   errors: 0
browser: Chromium 151.0.7922.34
rows measured: 200 per handbook (5 sections x 2 views x viewport matrix)
no_js_and_print: pass
verification_scope: rendered geometry, inventory and declared browser behaviors
```

Each handbook is opened from a `file://` URI, which is the offline local-file
exercise: no server, no network. The self-containment claim was checked
independently by scanning the output for any external `src` or `href` - zero
matches, so nothing is fetched at view time.

Both views are present in the delivered file (`data-dv-page` 30, `data-dv-slide`
37, `data-dv-chapter` 4 in the overview), so the page-plus-presentation contract
is met by the artifact and not only by the builder's intent.

### Bad fixtures fail the right gates

The gate changes this phase made are each proven against a fixture carrying the
defect and against the nearest look-alike that must stay silent:

```
tests/skills/test_presentify_measure_handbook.py    7 passed (opacity + contrast)
tests/verification/test_visual_defect_detector.py   2 passed (overlap layers, both new)
tests/validators/test_merge_conflict_markers.py    11 passed
```

Every one was run with its fix disabled first. Three controls fired correctly;
one did not, and that test was rewritten rather than kept (see Living docs
architecture above).

### Not performed, and stated as such

The optional PPTX export was NOT re-exercised through native PowerPoint this
phase. Its Phase 6 evidence stands on Phase 6 bytes, which this phase did not
change: no PPTX generator, template, or helper was touched. Re-running it would
have produced evidence identical to what is already recorded, but the honest
statement is that the native-playback verification in this release dates from
Phase 6 and is not re-stamped with a Phase 7 date.

## Goal-vs-codebase review

Performed against the final tree and the stated goal, independently of the
plan's checkboxes. The reviewer is not independent of the implementer: this is a
single-operator session, and that lack of independence is recorded rather than
implied away.

**The goal**: one self-contained interactive HTML file with a detailed scrolling
page and a title-page presentation mode as the DEFAULT output of presentify and
handbook maintenance, source-faithful, brand-preserving, reproducibly built, and
gated by measured production-readiness checks in both documentation updates and
release handoffs.

| Claim | Verified how | Result |
|---|---|---|
| Presentation mode is the DEFAULT, not opt-in | `catalog/commands/presentify.md` states inclusion by default with explicit opt-out precedence | holds |
| One self-contained file | zero external `src`/`href` in either built handbook | holds |
| Both views in one artifact | reading, slide and chapter markers all present in the delivered bytes | holds |
| Reproducible build | rebuild produced a recorded hash; the freshness gate compares source, builder AND output | holds |
| Gated in the release handoff | `check_handbooks.py` now runs in the `docs` CI group; it did not run anywhere before this phase | holds, newly |
| Measured production-readiness | nine rendered gates, each negative-controlled, on rendered values rather than authored source | holds |

### The one claim that does NOT hold, and is not asserted

Simultaneous single-invocation delivery across all three source families within
a bounded repair budget. Best sustained result: two of three, across six rounds.
Recorded as QG-2, CLOSED AS UNMET and carried forward. The shipped surfaces were
scanned for any claim that would contradict this - "first shot", "one
invocation", "production-ready", "guarantee", "3/3" - and the only matches are
the OFFLINE self-containment guarantee, which is real and mechanically enforced.
No surface overclaims the quality result.

### Blocking findings resolved during this review

1. **`CHANGELOG.md` carried no entry for this feature at all.** The `[Unreleased]` section documented only the plan-queue and usage-monitor work. `AGENTS.md` requires a changelog entry for every change, and a release cut from this state would have shipped the feature silently. Added, covering the feature, the two gate corrections, and the conflict-marker fix.
2. **The capability declaration was false.** It read "This release introduces no new opt-in capability", which stops being true the moment presentify's default changes. Presentation Mode is now documented as a changed DEFAULT with all five required elements, and the gate confirms it:

```
python scripts/check_release_capability_docs.py CHANGELOG.md --surface "Presentation Mode" --strict
  OK Presentation Mode: all five elements present
  exit=0
```

The first attempt at that block failed the gate for a reason worth recording:
`surface_block` binds to the FIRST line naming the surface, which was a feature
bullet several sections earlier, so the five labels were never in scope. The
surface now has its own heading and the earlier mention reads as lowercase
prose.

### Considered but rejected

- **Merging the two overlap implementations into one.** They measure different things (text-versus-text in a layout layer; label-versus-shape inside an SVG). Merging them to serve a symmetry that is not there would give one script two responsibilities. Rejected; the ownership table resolves the conflict instead.
- **Raising the handbooks' own `design.css` to opacity 1 to satisfy the gate.** This would have made the artifact pass by changing the artifact, leaving a gate that fails legible text for every future user. The measurement (10.75:1) said the design was fine and the gate was wrong. Rejected.
- **Exempting every sticky element from `text-overlap`.** Simpler, and wrong: a transparent sticky layer genuinely collides. The negative control proves the difference. Rejected in favour of the opacity condition the ledger itself had proposed.
- **Fixing the four pre-existing dangling links found in changed files.** Real, but present on `origin/develop` before this branch and outside the changed-lines rule. Recorded, not swept.
- **Re-verifying the platform read-contract against vendor documentation.** Belongs to `/update release`, where its result can name the version being published. Deferred with the command recorded.

## Last-phase human testing suggestions

These are suggestions. None has been performed, and none retroactively qualifies
an automated gate. Automated geometry cannot establish that a person understood
the document.

Suggested for a maintainer:

1. Open `docs/handbooks/overview.html` by double-clicking it, with no server running. Expect the reading view, complete, styled, offline.
2. Enter Presentation Mode from the global menu after scrolling deep into the page. Expect it to start at slide 1, not at the section you were reading.
3. Open a chapter link directly. Expect that target to be independent of the global entry above.
4. Press Escape from a slide. Expect the reading position you left, without an animated scroll and with focus back in the document.

Suggested for a reader unfamiliar with the material:

5. Find a specific technical answer (for example, which files the installer copies by explicit name) using only the page. Expect it to be findable without reading linearly.
6. Start the presentation from its title and explain one central figure aloud. Expect the figure to carry enough labelling to support that without the prose.
7. Read the whole thing on a phone. Expect no horizontal scrolling and no hidden essential content.
8. Navigate the reading view by keyboard only. Expect every control reachable and its focus visible.

Expected outcomes are stated so a tester can disagree with them. Status:
**suggested, not performed.**

## Full-suite testing and stabilization

The canonical gate is the repository-native profile, not a transcribed `make`
target. `make` is absent on a stock Windows workstation, and during v4.8.0 a
contributor ran a target's steps individually, saw each pass, and still failed
CI on a step that had last run several phases earlier: the composite claim was
never true at one revision. One command against one list is what prevents that.

```
python scripts/ci/run.py --profile full
PASS: 46 passed, 0 failed, 0 skipped, 0 advisory in 5035.3s
  tests/hook-tests   694.2s
  tests/repo-tests  3972.4s
```

Groups exercised: catalog-parse, hygiene, interpreters, catalog, security,
workflows, platform-contracts, docs, version, tests, extension-tests.

### Three runs were required, and the two failures were both latent

This is recorded because the intermediate runs are the evidence, not noise.

| Run | Result | Why |
|---|---|---|
| 1 | 44 passed, 2 failed, 4957.1s | two genuine failures, neither introduced by this phase |
| 2 | stopped | would have reproduced failure 2; stopped rather than burn 80 minutes proving a known defect |
| 3 | **46 passed, 0 failed, 5035.3s** | green on final bytes |

**Failure 1 - `check_merge_conflict_markers.py` was never classified.** The
installer-parity test requires every `scripts/*.py` to be copied by BOTH
installers or listed in `DEV_ONLY_SCRIPTS` with a reason. This one is a
repo-internal guard: it scans a git worktree, and an installed
`~/.nexus-hub/scripts/` has none. Classified as developer-only alongside the
other repo-only guards.

**Failure 2 - a test asserting behaviour that was deliberately removed.**
`test_print_keeps_semantic_figure_content_and_expands_scroll_regions` required
the READING-view directory to be a scroll region
(`scrollHeight > clientHeight`). BG-6 removed exactly that in `e7ca89d0`,
because a 200px cap plus overlay scrollbars makes a truncated directory and a
complete one visually identical - a reader saw a truncated table with nothing
indicating more existed. The test encoded the pre-fix world and had been failing
since that commit.

Its three obsolete assertions now bind to the current contract: nothing clipped,
on screen and in print. The test keeps its actual purpose, which is that print
never hides reading content. No coverage was duplicated or invented: BG-6's own
two tests already assert both halves directly (the reading view hides at most
two pixels; the slide retains its 200px cap and its stable gutter), and they were
checked before this edit rather than assumed.

### Why both had gone unnoticed

Neither is reachable from the `fast` profile. `hook-tests` and `repo-tests` run
in `full` only, and Phase 6 committed on `fast`. Both defects therefore sat green
on every pre-commit gate while being red on the one that matters.

That is the sixth defect this phase with the same shape: a gate that existed but
had never run against the thing it guards. The others were the conflict-marker
run width, the two skills contradicting each other on overlap, the repository's
own handbooks never measured by a gate this plan shipped, and `check_handbooks`
wired into no profile at all. The pattern is the argument for the v4.11.2 plan's
rule that a gate which has never been observed to fail is not evidence, and it
is the concrete cost of gating a commit on `fast` alone.

### Line endings, caught at staging

Seventeen staged files had drifted LF to CRLF. `pathlib.write_text` translates
newlines on Windows, and the evidence-writing done by this phase used it. The
release gate this file itself records lists "line endings are unchanged from
baseline", so this would have failed a gate written during this phase.

All seventeen are normalized back to their `HEAD` baseline and the comparison
now reports no drift. Two zero-byte `.err` files captured from the measurement
runs were dropped rather than committed: empty stderr is not evidence.

That changed bytes after the green profile. The affected test files were re-run
rather than assuming the earlier result still held:

```
tests/skills/test_presentify_measure_handbook.py
tests/verification/test_visual_defect_detector.py
tests/validators/test_merge_conflict_markers.py
catalog/hooks/tests/test_installer_smoke.py
125 passed in 136.81s

python scripts/ci/run.py --profile fast
PASS: 14 passed, 0 failed, 0 skipped, 0 advisory in 147.6s
```

The full profile was NOT re-run for this change, and that is a judgement rather
than an oversight: the edit altered only line terminators, no test or gate reads
them, and the four suites that touch the changed files all pass. A reader who
disagrees should re-run `--profile full`; it took 5035s on this host.

## Local GO

Every mandatory section of this file is present with a truthful status. No
required gate is unresolved, and no failed gate has been recorded as a pass.

- Architecture refactor: complete; one finding resolved at root cause, one gate corrected.
- Known-gaps reconciliation: 17 items, 13 resolved, 2 closed (one as UNMET), 2 carried with named owners.
- Living documentation: both repository handbooks rebuilt, re-measured on final bytes, passing at 0 errors.
- Git-tree hygiene: clean; three move-induced broken links repaired, four pre-existing ones recorded rather than swept.
- CI/CD and distribution parity: installer parity PASS; one necessary pipeline addition applied and justified.
- Tier 3 deep pass: final bytes, real boundary, 200 rows per handbook, no-JS and print pass.
- Goal review: six claims verified against the tree; two blocking findings resolved; the one claim that does not hold is not asserted anywhere.
- Human testing: suggested, explicitly not performed.
- Full suite: PASS 46/46.

**Local verification is complete. Publication and integration are NOT done and
require explicit approval.** Nothing has been pushed, no pull request exists, no
tag has been created, and no remote CI has run. The plan's `/update release`
handoff begins only after integration is green and merged.

## Publication and integration

**Status: not started. Awaiting explicit approval.**

Recorded for whoever performs it:

- Push `feat/v4.9.1-interactive-handbooks` once, then open its integration pull request against `develop`. The branch name predates the renumber; the plan is v4.11.0.
- That pull request is the plan's FIRST remote validation and runs against the merge result. A red required check reopens this phase and is reproduced locally before any re-push.
- Carried to the release handoff: re-verify the platform read-contract against vendor documentation (it is currently verified for v4.9.0), and correct the GitHub repository description, which says 336 skills where `README.md` declares 337. The description is not a version-carrying surface, so `check_version_sync.py` cannot see it.
