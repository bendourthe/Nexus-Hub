# Decision: Plan filenames track the target version, and are renamed when priority moves

Status: implemented - all 14 unshipped plan filenames were renamed on 2026-08-21 to match their target version, the rot-prone `Filename` header field was removed, and every plan now carries `Target version` plus a `Rank` pointer back to the ranking table. This supersedes the naming half of [2026-08-20-roadmap-ordering-and-v4-reservation](2026-08-20-roadmap-ordering-and-v4-reservation.md); the v4.0.0 reservation half of that record stands unchanged.

## Problem

The 2026-08-20 record made two decisions in one pass. The first (v4.0.0 is reserved for changed-install-behavior, not backlog completion) has held. The second did not survive a day.

That second decision froze existing plan filenames as historical identifiers and named new plans by slug alone. It rested on a cost estimate: renaming would mean "thirteen files plus every cross-reference to them", which "would be the third renumbering pass and would buy nothing that this table does not already buy". Two things then went wrong with it.

**The estimate was wrong, by a lot.** The measured cost is 14 files and 22 references, of which **6 needed repair**. The other 16 sit in frozen historical records that this repository's own precedent already leaves untouched, a rule stated twice in the tree (`docs/v3/v3.16/docs-cleanup-report.md` and `docs/v3/v3.16/known-gaps.md`): live references are repaired, a record of what was true at the time is not. Two of the 22 are the previous decision record arguing *about* a filename, where rewriting the name would destroy the evidence for why the rule changed. So the real price was six link edits, not an open-ended sweep.

**The rule failed its first contact with a reader.** Within one day, the maintainer read the ranking table, saw `code-intelligence-hardening` sitting at rank 4, and asked whether v3.17.7 through v3.17.11 had been skipped. Nothing was skipped; the filenames said `v3.17.x` while the targets said otherwise, exactly as designed. The design was the problem. A filename reading `v3.17.8` on a plan targeting v3.18.2 is not a neutral historical identifier, it is a wrong answer sitting in the most visible place, and "the table is the authority" does not help a reader who has not been told to distrust the filename in front of them.

The `Filename` header field proved the same point independently. Both files that carried it named a file that did not exist (`v3.19.1-adoption-interface-craft-skills.md` and `v3.19.0-adoption-cost-effective-ci-cd.md`), having rotted before this pass began.

## Decision

**A plan's filename carries its target version, and is renamed when the target moves.**

- All 14 unshipped plans were renamed on 2026-08-21. Three shared `v4.0.0-` prefixes, which is correct: they are one bundle shipping together.
- The `Filename` field is removed from plan headers. A file's name is authoritative for itself; a field restating it can only drift, and did.
- Every plan carries `Target version` and `Rank`, the latter linking to `docs/v3/roadmap-prioritization.md` so a reader arriving at a plan file first can still find the ordering authority.
- The ranking table remains the single authority on sequence. Filenames now agree with it rather than contradicting it, which makes the table easier to trust, not redundant.
- **Every plan also moved into the directory matching its target version** (amended later the same day, see below). The six plans coupled to a comparison report moved as pairs, and those reports were renamed and retargeted to match.
- Frozen historical records keep their original filenames in prose, per the existing precedent. Only live pointers were repaired.

The recurring cost is accepted rather than denied: re-prioritizing means a rename plus two field edits per moved plan, and one edit to the table. That price was paid on 2026-08-21 and is expected to be paid again.

## Alternatives considered

**Keep filenames frozen (the 2026-08-20 decision).** Rejected on new evidence. Its own cost estimate was off by roughly 4x on the number that mattered, and the confusion it was meant to prevent is the confusion it caused. Freezing a number does not make it stop being read as true.

**Rename to slug-only, dropping version prefixes entirely.** This was recommended and declined by the maintainer. It is the option that never drifts, because a filename carrying no ordering information cannot contradict the ordering. It was declined in favour of filenames that answer "when does this ship?" directly, which is the question a reader actually arrives with. The trade accepted knowingly: a rename cost on every future reprioritization, in exchange for a filename that is informative rather than inert. Worth revisiting only if reprioritization becomes frequent enough that the rename tax outweighs the readability.

**Add a target-version pointer to each plan and leave filenames alone.** Rejected. It is what the previous decision effectively did, and it does not address the failure mode: a reader who trusts the filename never reaches the pointer.

**Move each plan into the directory matching its target version.** Initially rejected for this pass, then **adopted the same day** after the maintainer pointed out the obvious: renaming files while leaving `docs/v3/v3.17/plans/` holding v3.18, v3.20, and v4.0 plans fixes the filename and moves the contradiction up one level. The original rejection reasoned that moving "collides with rank 14's container restructuring", which was wrong on inspection: rank 14 renames the top-level containers (`docs/releases/`, `docs/archives/`) and would move everything wholesale regardless, so per-version placement does not conflict with it. A flat `docs/plans/` queue remains deferred to rank 14, which does own that decision.

**Rewrite every historical reference to the old filenames.** Rejected. It would revise the record of what was true at the time, and in two cases would leave the previous decision record arguing about a filename that no longer exists, erasing the reasoning this record supersedes.

## Consequences

- A reader can now answer "when does this ship?" from a directory listing, which is how the question is usually asked.
- Eight historical references to old filenames remain, deliberately, and will not resolve as links. They are records, not navigation.
- Two renumbering rules now exist in the tree's history, in opposite directions, thirteen days apart. This record is the current one; the 2026-08-20 record retains its reasoning so the reversal is auditable rather than silent.
- `docs/v3/roadmap-prioritization.md` still must never receive an automated version-string sweep. It names version numbers as data about other documents, and a sweep treating them as its own version corrupts the ranking. That hazard is unchanged by this decision.
- The next reprioritization costs renames. That is now a known and accepted line item, not a surprise.

## Amendment, 2026-08-21: placement followed, and it exposed three gate defects

Renaming without relocating was incoherent, and the maintainer said so within the hour. Every unshipped plan now sits in the directory matching its target version.

The move was not a file shuffle, for two reasons worth recording.

**Comparison reports are coupled to their plans by a required check.** The `colocation` gate enforces two rules at once: a plan must share a version directory with the comparison it cites, and a comparison must sit in the directory its own `Adoption target` names. Moving a plan alone violates the first; moving the pair without updating the target violates the second. Six plans were coupled, so six comparisons moved, were renamed to their new target, and had their `Adoption target` field rewritten.

**Creating `docs/v4/` broke the gate open.** The check computed one `CURRENT_MAJOR` with `sort -n | tail -1` and scanned only that tree, so the four plans retargeted to v4.0.0/v4.1.0 would have silently disabled co-location checking for all of `docs/v3/` while the required check kept reporting green. Investigating that found two more fail-opens in the same block: a `Seeded from` pointing at a nonexistent file passed (the version directory was parsed from the path string, never opened), and a relative `../comparisons/x.md` reference was skipped outright (the regex required a literal `docs/v` prefix). The third defect masked the second: two plans had been citing comparison files under pre-rename slugs, `jcodemunch` and `optmem`, that did not exist.

The implementation moved from an inline `run:` block to `scripts/check_doc_colocation.py` so the fixes could be unit-tested, which the bash version could not be. It now also runs in `make validate`; previously co-location was enforced only in CI, so a local validation pass could not catch a violation. The `colocation` job name and its unfiltered triggers are unchanged, so the required status context still resolves and `check_required_check_coverage.py` still passes.

Not moved: `docs/v3/roadmap-prioritization.md` stays put even though it now ranks v4 plans. Relocating it would pull CHANGELOG, README, and DEVLOG references along for a cosmetic gain, and the four `docs/v4/` plans link it correctly with one extra level.
