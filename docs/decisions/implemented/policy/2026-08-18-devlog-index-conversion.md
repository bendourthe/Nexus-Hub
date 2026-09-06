# Decision: DEVLOG becomes a per-release index, and its narrative body is archived

Status: implemented - `docs/DEVLOG.md` is a bounded navigation table with one line per release; the 5,615-line narrative body is archived verbatim at `docs/archive/DEVLOG-v0-v3.17.md`

## Problem

`docs/DEVLOG.md` was an append-only narrative log. By 2026-08-21 it had reached 5,615 lines and roughly 208,000 words, which is past the point where any agent can load it. A document nobody reads is not a record; it is write-only overhead paid on every release.

Worse, it had become redundant. DEVLOG was invented before the per-version documentation tree existed. Everything it was created to hold now has a canonical home that is smaller, closer to the work, and already maintained: `docs/v*/v*.*/plans/` holds intent, `development/history/` holds per-phase session narrative, `known-gaps.md` holds open items, `docs/decisions/` holds settled reasoning, `docs/solutions/` holds closed problems, and `CHANGELOG.md` holds the authoritative change record. DEVLOG duplicated all six in one unbounded file.

What DEVLOG uniquely provided was a single-glance whole-project chronology: 91 tags and 134 releases in one place, in order. That is a navigation problem, not a narrative one.

## Decision

`docs/DEVLOG.md` is a per-release index, not a log. It carries a short header explaining the format and one line per release, newest first, with:

- the release date and version,
- a one-sentence summary,
- links to that release's plan file (or its version's `plans/` directory where plan filenames predate the version-prefixed convention), its `development/history/` directory, and its `known-gaps.md`.

Every release from v3.0.0 onward gets its own line. Releases before v3.0.0 predate the canonical per-version layout, so they collapse to one line per minor version pointing at the archive and the CHANGELOG. That is what holds the file bounded: the index grows by one line per release, and the pre-canonical era is fixed at 19 lines forever.

The prior body is archived verbatim at `docs/archive/DEVLOG-v0-v3.17.md`, byte-identical below a short provenance header. Nothing is deleted.

**What the index does not grant.** It is a navigation surface, not a change record. `CHANGELOG.md` remains the authoritative record of what changed in each release, and the index never restates it. An index line that starts explaining a release has regressed into a log.

## Alternatives considered

- **Keep DEVLOG as an append-only log.** Rejected: at 5,615 lines and ~208k words it is unloadable by any agent, so its content is effectively unreachable, and every one of its sections duplicates a per-version file that is already maintained. The cost is paid at write time and the value is never collected.
- **Delete DEVLOG outright.** Rejected: it is the only surface that shows the whole project's release chronology at a glance. The per-version tree answers "what happened in v3.15" well and "what has this project done" not at all, because that answer is spread across 21 minor-version directories.
- **Split into per-version DEVLOGs.** Rejected: that is precisely what `docs/v*/v*.*/development/history/` already is. A second per-version narrative surface would be a duplicate with no rule for which one to write to, and the ambiguity resolves the wrong way under deadline.
- **Truncate to the last N releases and drop the rest.** Rejected: it loses the pre-canonical chronology permanently for a bound that a collapsed pre-canonical era achieves without loss.
- **One line per release for all 134 releases including pre-v3.** Rejected on the numbers: 134 rows plus header lands at roughly 148 lines against a 150-line gate, leaving no headroom on the very first release after the conversion. Collapsing the pre-canonical era buys 45 lines of headroom and costs nothing, because those releases have no per-version tree to link to anyway.

## Consequences

- The index is bounded but not self-bounding. It grows one line per release, which is a slow enough rate that a 150-line ceiling holds for years, but nothing mechanically prevents an agent from writing a paragraph into a cell. The format contract lives here and in the `devlog-generation` skill; the tooling that enforces it is a separate phase of this plan, and until that ships the format depends on the writer reading this record.
- Summaries in the index are authored, not derived. The CHANGELOG carries no one-line summary per release, so mechanical extraction produces noise (the lead bullet of five releases is the literal word "Activation:"). Every summary is a human-reviewed judgment, which means a wrong one is possible and cheap to fix.
- Pre-v3 releases are reachable only through the archive and the CHANGELOG. That is a deliberate asymmetry: those releases have no plan file, no history directory, and no known-gaps file to link, so a per-release line would carry a date, a version, and three dead columns.
- Anything that described DEVLOG as a narrative log is now wrong and had to be corrected in the same change. The skill and command internals that *write* it are a separate phase, so between the two there is a window where the tooling's instructions and the file's actual format disagree.
- The archived body is frozen. It will never be appended to again, so a reader looking for v3.18 detail in `DEVLOG-v0-v3.17.md` finds nothing and must follow the index. The archive filename states its own range to make that boundary visible.
