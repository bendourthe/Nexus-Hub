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
- Files were **not** moved between version directories. Rank 14 (`docs-lifespan-tree-and-enforcement`) restructures the docs containers, so moving them now would collide with queued work.
- Frozen historical records keep their original filenames in prose, per the existing precedent. Only live pointers were repaired.

The recurring cost is accepted rather than denied: re-prioritizing means a rename plus two field edits per moved plan, and one edit to the table. That price was paid on 2026-08-21 and is expected to be paid again.

## Alternatives considered

**Keep filenames frozen (the 2026-08-20 decision).** Rejected on new evidence. Its own cost estimate was off by roughly 4x on the number that mattered, and the confusion it was meant to prevent is the confusion it caused. Freezing a number does not make it stop being read as true.

**Rename to slug-only, dropping version prefixes entirely.** This was recommended and declined by the maintainer. It is the option that never drifts, because a filename carrying no ordering information cannot contradict the ordering. It was declined in favour of filenames that answer "when does this ship?" directly, which is the question a reader actually arrives with. The trade accepted knowingly: a rename cost on every future reprioritization, in exchange for a filename that is informative rather than inert. Worth revisiting only if reprioritization becomes frequent enough that the rename tax outweighs the readability.

**Add a target-version pointer to each plan and leave filenames alone.** Rejected. It is what the previous decision effectively did, and it does not address the failure mode: a reader who trusts the filename never reaches the pointer.

**Move each plan into the directory matching its target version.** Rejected for this pass. It would drift on exactly the same schedule as the filenames, and it collides with rank 14's container restructuring. Deferred to that plan rather than pre-empted here.

**Rewrite every historical reference to the old filenames.** Rejected. It would revise the record of what was true at the time, and in two cases would leave the previous decision record arguing about a filename that no longer exists, erasing the reasoning this record supersedes.

## Consequences

- A reader can now answer "when does this ship?" from a directory listing, which is how the question is usually asked.
- Eight historical references to old filenames remain, deliberately, and will not resolve as links. They are records, not navigation.
- Two renumbering rules now exist in the tree's history, in opposite directions, thirteen days apart. This record is the current one; the 2026-08-20 record retains its reasoning so the reversal is auditable rather than silent.
- `docs/v3/roadmap-prioritization.md` still must never receive an automated version-string sweep. It names version numbers as data about other documents, and a sweep treating them as its own version corrupts the ranking. That hazard is unchanged by this decision.
- The next reprioritization costs renames. That is now a known and accepted line item, not a surprise.
