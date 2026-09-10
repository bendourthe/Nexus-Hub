# Phase 1 evidence - Queue enumeration and baseline

Evidence for Phase 1 (T001-T004) of the [v4.10.0 plan-queue continuity plan](../plans/v4.10.0-plan-queue-continuity.md). Records the real plan inventory before automation, the part of the existing Step 6.5 rule this script makes deterministic, the reconstructed reference-repair surface from the three 2026-09-10 renumbers, and the enumeration script's behaviour against fixtures and the live tree. Read this to confirm D1 before Phase 2 builds the assessment on top of it.

## T001 - Baseline

**Baseline commit**: `45e803b4` on `feat/v4.10.0-plan-queue-continuity`, branched from `develop`.

### The real inventory

A full scan of `docs/releases/*/*/plans/*.md` finds **99 plan files** across v3 and v4. (This evidence first stated 101, an unverified figure; corrected in Phase 6 against the script's own count.) Grouping by unchecked `T###` lines gives a first approximation of the queue, and immediately exposes the central design finding below.

The four plans the maintainer actually considers queued:

| Version | Slug | Open | Done |
|---|---|---:|---:|
| v4.9.1 | interactive-handbooks-and-presentation-default | 31 | 0 |
| v4.10.0 | plan-queue-continuity (this plan) | 26 | 0 |
| v4.11.0 | adoption-cache-and-diagram-quality | 25 | 0 |
| v4.12.0 | sole-contributor-attribution | 23 | 0 |
| v4.13.0 | adoption-evidence-driven-agent-improvement | 34 | 0 |

### Finding: an open task count does not identify the queue

The scan also reports unchecked task lines in plans that are demonstrably finished or abandoned:

| Version | Open | Reading |
|---|---:|---|
| v4.0.0 cost-effective-ci-cd | 62 | Superseded; the CI/CD lifecycle shipped under a different plan |
| v3.16.1 evals-and-selective-installation | 59 | Abandoned |
| v3.0.0 command-consolidation-skill-security | 49 | Shipped in v3.0.0; checkboxes never reconciled |
| v4.3.0 agentic-verification-discipline | 10 | Mostly shipped (16 done); residue |
| v4.4.6, v4.8.0, v4.2.x, v4.1.1 | 1-3 each | Residue on shipped plans |

This is the single most important input to D1. A naive "plans with unchecked tasks" query returns **more than a dozen** false members, three of them larger than any genuinely queued plan. Ranking that set would put a superseded v4.0.0 plan at the top of the queue on task volume alone.

**Consequence for T002**: the script must report a status signal alongside the counts and must not present the open count as the queue membership test. The plan header `**Status**:` line is the available signal; where it is absent or does not parse, the script reports the plan with an explicit unknown status rather than guessing from counts. Membership remains a maintainer judgement that Phase 2 structures; the script's job is to make the inputs to that judgement complete and deterministic.

### What Step 6.5 already does, and what this script changes

`catalog/skills/workflow/cross-project-comparison/SKILL.md` Step 6.5 already walks the tree to find a free slot, and already documents both traps this script must avoid: sorting on parsed integers rather than lexically (`v3.10` must not precede `v3.5`), and scanning the whole tree rather than the current minor.

- **Made deterministic by the script**: the walk itself, the integer sort, the free-slot computation, and the per-plan counts and touched-file surface.
- **Remains a judgement**: whether a plan with unchecked tasks is genuinely queued, and which slot a new comparison should adopt. Step 6.5's rule expresses that judgement; the script only supplies its inputs.

The script therefore replaces the hand-executed walk, not the rule. Phase 3 rewrites Step 6.5 to invoke it while keeping the two documented failure modes as stated rationale, because they explain why the script exists.

## Reconstructed reference-repair surface

Three renumbers were performed by hand on 2026-09-10, recovered from `git log --diff-filter=R`:

| Commit | Operation |
|---|---|
| `de7697b3` | Swapped the cache-and-diagram and attribution slots (v4.12.0 <-> v4.10.0) |
| `d5ca32cb` | Moved the evidence plan out of v4.11.0 to v4.13.0 to free a slot |
| `d492ee84` | Swapped plan-queue continuity ahead of cache-and-diagram (v4.11.0 <-> v4.10.0) |

The third was performed while cache-and-diagram was **mid-implementation**, with three phases committed locally. That is the hardest case, and it required a fourth operation outside the renumber itself: re-applying the committed implementation at the new paths (`c8f18b58` on `feat/v4.11.0-cache-and-diagram`), because the phase commits could not be cherry-picked across the rename without conflict.

### Distinct reference classes that required repair

Every class below was observed at least once across the three operations. This list is the acceptance surface for Phase 5.

1. **Intra-tree version strings** - `**Version**:`, `**Filename**:`, and body prose inside the moved plan and comparison.
2. **Relative plan links** - `[text](../../v4.11/plans/v4.11.0-....md)` from a sibling version tree.
3. **Link-reference definitions** - `[N8]: ../../../../../docs/releases/v4/v4.11/plans/....md`, which a link-text-only scan misses entirely.
4. **Self-referential paths inside a plan's own task lines** - 26 task lines in this plan each name a `docs/releases/v4/v4.10/development/...` output path.
5. **Tracker dashboard rows** - `| v4.11.0 implementation tasks complete | ... |` in `docs/todos.md`.
6. **Tracker prose and section headings** - `## Queued work - v4.11.0 ...` plus the body link and its narrative.
7. **Committed implementation evidence under the moved tree** - `development/*.md` and `development/history/*.md`, each with internal version references.

### Two traps a blanket rewrite hits

Both were hit during these operations and both must be encoded in Phase 5.

- **A bare section number is not a version.** The attribution plan carries a Phase 4 subsection heading `#### 4.10 - Publication and integration`. A `4.10 -> 4.12` substitution corrupts it. Only `v`-prefixed forms may be rewritten.
- **A blanket rewrite cannot distinguish a plan's own version from a reference to another plan.** The third swap corrupted **eleven** cross-references in this very plan, including its sequencing intent, which inverted. Two further statements in the cache-and-diagram artifacts were rewritten into factual falsehoods about what was confirmed on 2026-09-09. Both required hand repair, and the correct fix for a historical claim is a dated note, never a silent restatement.

This is why D6 requires a residual-reference check that fails on a single survivor, and why the procedure is propose-then-apply rather than automatic.

## Limitations

- The inventory is a point-in-time read of the working tree at `45e803b4`. It is not a persisted queue state; this plan deliberately ships no queue database.
- Queue membership for the dozen residue plans above was judged by inspection for this baseline. Phase 2 must structure that judgement rather than inherit these specific calls.

## T002 - The enumeration script

`scripts/enumerate_plan_queue.py`, stdlib only, module docstring and type annotations. It walks `docs/releases/*/*/plans/*.md`, parses each version into integers and sorts on them, and reports version, slug, path, declared status, open and completed `T###` counts, and the deduplicated repository paths named by the task lines. `--json` emits the machine form; the default is a table.

Registered in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py` as maintainer queue tooling, so no installer copy step is required in either installer. The installer-smoke suite passes with the addition (33 tests).

### Design corrections made during implementation

Two decisions changed from the plan's first reading, both recorded here rather than silently absorbed.

**The task-line pattern requires a trailing space after the identifier.** Without it, `- [ ] The phase's observable gate passed.` matches on the leading `T` and inflates every count. This defect was live in the ad-hoc `grep -c` used during T001 and produced 33 tasks for a 26-task plan. A test pins it.

**A missing `Status` line is a note, not an error.** The first implementation returned exit 1 for any plan lacking one. Against the live tree that is **83 of 99 plans**, so every real run would exit 1 and the exit code would carry no signal. Errors are now reserved for a genuinely unreadable plan; an undeclared status is reported as a note and summarised in the table footer. This preserves D1's requirement that a malformed plan is an explicit finding while keeping the exit code meaningful.

## T003 - Fixture tests

`tests/validators/test_enumerate_plan_queue.py`, 18 tests over `tmp_path` fixture trees:

- Numeric ordering where a lexical sort would place `v4.10` before `v4.9`, and the same across majors.
- A plan several minors ahead of the in-flight version being found.
- Task counts parametrized over four open/done combinations.
- The exit-checklist item not being counted as a task.
- Touched-path extraction and deduplication.
- A missing `Status` line producing a note and exit 0.
- A declared status being reported verbatim.
- An unreadable plan appearing in the queue with an error and exit 1.
- A legacy filename with no version prefix staying in the queue.
- An empty tree, an absent releases tree, and a missing root.
- The rendered table carrying the counts-are-not-membership statement.
- Well-formed JSON output.

## T004 - Testing and stabilization

```text
$ python -m pytest tests/validators/test_enumerate_plan_queue.py -q
..................
18 passed in 0.25s

$ python -m pytest catalog/hooks/tests/test_installer_smoke.py -q
.................................
33 passed in 1.17s

$ python -m ruff check scripts/enumerate_plan_queue.py tests/validators/test_enumerate_plan_queue.py
All checks passed!

$ python scripts/ci/run.py --profile fast
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory in 84.5s
```

### Live tree output

```text
v4.9.1      31     0  interactive-handbooks-and-presentation-default
v4.10.0     26     0  plan-queue-continuity
v4.11.0     25     0  adoption-cache-and-diagram-quality
v4.12.0     23     0  sole-contributor-attribution  ?
v4.13.0     34     0  adoption-evidence-driven-agent-improvement

Undeclared status: 83 plan(s) carry no Status line.
```

Exit 0: no plan in the live tree is unreadable. The counts match the T001 baseline exactly once the trailing-space correction is applied; the baseline's ad-hoc grep reported 26 for this plan and the script agrees.

### CI impact

One new test path, `tests/validators/test_enumerate_plan_queue.py`. Confirmed by inspection that `scripts/ci/profiles.py` line 227 defines the `TESTS` group's `repo-tests` step as `pytest tests`, which collects the whole `tests/` tree including `validators/`. No profile edit is proposed and no gap is carried to Phase 6. This closes the v4.9 QG-1 pattern by inspection rather than assumption.

One new script, `scripts/enumerate_plan_queue.py`, declared repo-internal in `DEV_ONLY_SCRIPTS`, so the installer-aware rule requiring a copy step in both installers does not apply. The installer-smoke suite proves that declaration is consistent.

No new dependency, environment variable, or artifact.
