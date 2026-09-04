# Decision: Keep platform-mark attribution in a site footer, not a Home disclosure

Status: implemented - v4.4.2 Phase 2 (`guide-production-ready-rebuild`, sub-task 2.1).

## Problem

The v4.4.1 guide showed a collapsed `Trademarks and credits` disclosure under the Home platform rail. The operator's visual review asked for that text to be removed from Home.

Removing it is not only a styling change. `docs/releases/v4/v4.4/development/guide-visual-and-arcade-rebuild/asset-provenance.md` records the GitHub Copilot mark as taken from Microsoft's Codicons icon set under CC BY 4.0, which requires attribution reasonably visible to the audience for as long as the mark is used. The other four marks are trademark-use notices; they carry no licence obligation, but the sentence stating that they identify supported assistants and imply no affiliation is the standard fair-use framing and is worth keeping wherever the marks appear.

## Decision

Attribution moves to a shared `site-footer` rendered below `main` on every page, in small muted text: the trademark sentence, then `The GitHub Copilot mark is from the Codicons icon set by Microsoft Corporation, used under CC BY 4.0` with the licence link. The Home disclosure element is deleted. A browser test asserts the footer text is present and visible on all four routes and that no `platform-credits` element exists inside Home.

The footer is the correct home for this text because it is the conventional place readers look for licence and trademark notices, it is present on every page that shows the marks (the rail is on Home, but the footer is global by construction so a future rail elsewhere is covered), and it is out of the Home reading flow, which is what the review objected to.

## Alternatives considered

**Delete the credits outright.** Fails the CC BY 4.0 attribution condition for the Copilot mark. Rejected unless the operator later replaces that mark with one under a licence that needs no attribution, in which case only the trademark sentence would remain.

**Keep a collapsed disclosure on Home.** This is the v4.4.1 state the operator explicitly asked to remove. Rejected.

**Attribution in an HTML comment or `aria-hidden` element.** Not "reasonably visible to the audience"; invisible attribution does not satisfy the licence. Rejected.

**Attribution only in `guides/website/README.md`.** The README is a maintainer document, not something the guide's audience sees. The guide is one offline file that travels alone, so attribution has to travel inside it. Rejected.

## Consequences

- Every page gains a short footer; the byte cost is under 1 KB and is charged to Phase 2's ledger allocation.
- `tests/guides/test_v441_phase2_home.py` gains an assertion that the footer attribution is visible on all four pages and that Home carries no credits disclosure.
- If a platform mark is ever replaced, `asset-provenance.md` and this footer must change together; the provenance ledger's hash test already forces the ledger edit, and the footer test names the licence text so a mismatch is visible.
