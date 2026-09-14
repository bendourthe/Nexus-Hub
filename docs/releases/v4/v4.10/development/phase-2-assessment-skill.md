# Phase 2 evidence - Assessment and ranking skill

Evidence for Phase 2 (T005-T007) of the [v4.10.0 plan-queue continuity plan](../plans/v4.10.0-plan-queue-continuity.md). Records the skill authored as the single owner of the staleness and ranking rules, its registration, and its first application to the real five-plan queue. Read this to confirm D2 and the ranking half of D6 before Phase 3 wires the authoring surfaces.

**This is authoring evidence, not a measured outcome.** It demonstrates that the rules produce a defensible ranking on real inputs. It does not demonstrate that following the ranking improves anything, which would need measurement this plan does not perform.

## T005 - The skill

`catalog/skills/workflow/plan-queue-assessment/SKILL.md`, 190 lines, within the 500-line target.

| Budget | Value | Limit |
|---|---:|---:|
| `summary_l0` | 12 words | 15 |
| `overview_l1` | 121 words | 150 |
| `description` | 902 chars | 1024 |
| Body | 190 lines | 500 soft / 800 hard |

Contents: a rule-ownership table naming six owners so nothing is restated; a seven-step procedure; the renumber procedure with its seven reference classes and two traps; nine Common Rationalizations each citing a concrete failure mode; a nine-item binary Verification checklist; and Related Skills with the relationship stated per entry.

Key rules stated once, here, and nowhere else:

- **Verdicts require named evidence.** No impact, content impact, ordering impact, or unknown. A verdict without evidence is indistinguishable from not having looked.
- **An open task count is not queue membership.** Membership comes from declared status or an explicit maintainer statement.
- **Unreadable or undeclared is an explicit unknown**, never a silent no-impact.
- **Impact on the harness is a structured maintainer judgement**, recorded with reasoning, never presented as computed.
- **Documentation, interactive-guide and refactor classes rank last**, and a last-placed plan carries a real content-refresh task.
- **Re-sequencing is never claimed to improve delivery speed.**
- **Every check writes an artifact.** An unwritten no-op is indistinguishable from a skipped check. This is the v4.9 WN-2 constraint applied to this plan's own four new steps.

## T006 - Registration

Added to `data/SKILL_INDEX.md` (one row), `data/skills.json` (one entry, security 100/100/95), and `data/marketplace.json` (workflow `skill_count` 47 to 48).

Four prose counts that the new skill invalidated were updated from 336 to 337: `.claude-plugin/plugin.json`, `data/marketplace.json`, `README.md` (three live statements), and `AGENTS.md` (two statements). This is the drift trap the v4.0 known-gaps file records, where a count in prose went stale in one file and was caught only by grep.

Two README statements were deliberately **left at 336**: both sit inside `## What's New in v4.9.0` release-note sections and describe what shipped in that release. Updating them would make a historical claim false. This is the same rule the renumber procedure states for dated statements.

```text
$ python scripts/validate_skills.py --bundles-only
Scanned 337 skills under catalog\skills (bundle audit)
RESULT: PASS (0 errors, 64 warnings)

$ python scripts/check_agentskills_conformance.py
RESULT: PASS (0 errors, 337 skills scanned)
```

## T007 - First application to the real queue

### Inventory

```text
v4.9.1      31 open   23 touched paths   Master plan consolidated 2026-09-05; implementation pending
v4.10.0     26 open   16 touched paths   In implementation; Phase 1 complete
v4.11.0     25 open   13 touched paths   Reviewed, authorized for publication; implementation not started
v4.12.0     23 open    8 touched paths   unknown (no parseable Status line)
v4.13.0     34 open   24 touched paths   READY for publication; implementation entry NOT QUALIFIED
```

`v4.11.0` reads as not started here because this branch is cut from `develop`; its phases 1-3 are committed on `feat/v4.11.0-cache-and-diagram` and unpublished. The inventory reads the tree it is given and does not consult unmerged branches. That is correct behaviour and a stated limitation, not a defect.

### Defect found and fixed by running against real data

The first extractor read only backtick-quoted paths. Three of the five live plans use bare trailing paths instead, and reported **zero** touched paths. Every overlap check involving them would have returned a false "no impact" with no signal that anything was wrong.

The extractor now reads both conventions. Path counts moved from 0 to 23, 8, and 24 for the three affected plans. Three tests pin the behaviour, including one asserting that prose containing a slash (`read/write`) is not mistaken for a path.

This is exactly why the skill requires a verdict to name its evidence. A "no impact" verdict citing an empty overlap list is visibly weaker than one citing two disjoint 20-path surfaces, and the requirement to show the evidence is what would have exposed the bug even before the fix.

### Pairwise overlap, excluding each plan's own documentation tree

| Pair | Overlap |
|---|---|
| v4.9.1 x v4.11.0 | `document-to-interactive-html/references/figure-reconstruction.md`, `.../scripts/visual_qa_score.py` |
| v4.9.1 x v4.10.0 | `catalog/commands/update.md` |
| v4.12.0 x v4.13.0 | `.github/workflows/ci.yml` |
| all other pairs | disjoint |

The v4.9.1 / v4.11.0 overlap independently confirms something the v4.11.0 plan already knew: its Grounding section instructs Phase 4 to reconcile the handbook plan's figure coverage at entry. The assessment found the same coupling from file surfaces alone, without reading that prose.

### Verdicts for the subject plan (v4.10.0)

| Queued plan | Verdict | Evidence |
|---|---|---|
| v4.9.1 | Ordering impact | Shares `catalog/commands/update.md`, which this plan's T013 modifies |
| v4.11.0 | No impact | Surfaces disjoint outside doc trees; no stated dependency either way |
| v4.12.0 | Ordering impact (non-file) | See the finding below |
| v4.13.0 | No impact | Surfaces disjoint; its evaluation scope is explicitly excluded from this plan |

### Finding: disjoint file surfaces are not sufficient for parallel work

`v4.12.0` is a git-history rewrite that force-pushes every ref. It is incompatible with **any** concurrent branch regardless of file overlap, because the rewrite invalidates the commits every other branch is based on. The pairwise surface check reports it as disjoint from three of the four other plans.

The skill already states that an empty intersection is "a necessary but not sufficient condition for parallel work". This is the first concrete instance, and it is recorded here so Phase 5's release-time review does not present surface-disjointness as a parallel-work green light.

### Ranking

Applying the two axes and then the class rule:

| Position | Plan | Reason |
|---:|---|---|
| 1 | v4.10.0 plan-queue continuity | Disjoint from everything except one command file; produces the capability that sequences the rest. Already in implementation. |
| 2 | v4.11.0 cache and diagram quality | Product improvement, 9/25 tasks already committed on its own branch, disjoint from this plan. Parallel-compatible with position 1. |
| 3 | v4.13.0 evidence-driven improvement | Real capability, but implementation entry is NOT QUALIFIED pending a native-runner prerequisite. Ranks here when unblocked. |
| 4 | v4.12.0 sole-contributor attribution | Refactor class. Also serialising: its force-push invalidates concurrent branches, so it wants an otherwise-quiet queue. |
| 5 | v4.9.1 interactive handbooks | Documentation and interactive-guide class. **Carries a refresh requirement** against positions 1-4, and specifically against v4.11.0, with which it shares two files. |

**Does the ranking place v4.9.1 last?** Yes, and by the class rule rather than by any adjustment made to produce that answer. v4.9.1 is not the smallest plan (31 open tasks, second largest) and not the least valuable; it ranks last because it documents and re-presents what the other plans build, so running it first guarantees rework.

`v4.12.0` also lands late, and it is the plan the maintainer named as the refactor case. Two independent reasons put it there: the class rule, and the serialising force-push. Either alone would be sufficient.

**Impact-on-harness is a judgement.** Positions 1 and 2 above are argued from capability and sunk work, not computed. A maintainer who values the cache correction over the ordering capability could defensibly swap them; the surfaces are disjoint so nothing breaks either way. Recording that is the point.

### Parallel-compatible groups

- **{v4.10.0, v4.11.0}** - disjoint surfaces, no dependency, both already have branches. This is the live case and it is currently true.
- **{v4.10.0, v4.13.0}** and **{v4.11.0, v4.13.0}** - disjoint, but v4.13.0 is blocked, so the grouping is theoretical.
- Nothing groups with **v4.12.0** for the force-push reason above.

## Checks run

```text
$ python -m pytest tests/validators/test_enumerate_plan_queue.py -q
.....................
21 passed in 0.51s

$ python scripts/ci/run.py --profile fast
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory
```

## Limitations

- The touched-path list is a lower bound. A plan that modifies a file without naming it in a task line is under-reported, and the skill says so.
- The ranking is authoring evidence. No claim is made that following it is faster, cheaper, or produces less rework in measured terms.
- Queue membership for `v4.12.0` rests on the maintainer's statement, because its plan carries no parseable `Status` line. That is reported as undeclared rather than assumed.

## CI impact

Registry files and one new skill directory, covered by the existing catalog-parse and bundle-audit groups. Three new tests on the existing `tests/` path. No new command, dependency, environment variable, or artifact. Nothing carried to Phase 6.
