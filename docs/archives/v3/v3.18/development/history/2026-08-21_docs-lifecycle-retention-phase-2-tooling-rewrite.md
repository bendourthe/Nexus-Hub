# Session History - Docs Lifecycle and Retention Phase 2: Tooling Rewrite for the Index Format

**Date**: 2026-08-21
**Branch**: `feat/docs-lifecycle-retention`
**Plan**: [`docs/releases/v3/v3.18/plans/v3.18.0-docs-lifecycle-retention.md`](../../plans/v3.18.0-docs-lifecycle-retention.md)
**Phase**: 2 - Tooling rewrite for the index format
**Environment**: Windows 11, Git Bash and PowerShell, Python 3.12, pytest, ShellCheck; GNU Make unavailable, so `make` targets were executed as their constituent commands
**Outcome**: Every writer of `docs/DEVLOG.md` now produces the index format, and the format is held mechanically rather than only by prose. Two defects outside the plan's sub-task list were found and fixed, one of which explains the anomalous DEVLOG growth the plan had recorded without a cause.

## 1. Starting State

- **Starting commit**: `f2241a07` (Phase 1: DEVLOG index conversion and archive)
- **Worktree**: clean
- **The open risk Phase 1 left**: `docs/DEVLOG.md` was an index, but every writer still emitted the narrative format. The format was held only by the decision record and by whoever read it.

The plan recorded `frontier / high` for this phase. Implementation ran on Opus 5 (`strong`). The delta was surfaced with the exact switch keystroke rather than silently accepted, and the pre-flight is advisory by design, so it did not block. No downgrade was applied mid-phase.

## 2. Scope Read Before Implementing

The plan's sub-tasks name four writers: the `devlog-generation` skill, `/update` at release and docs scope, and `setup-project`. A grep for every DEVLOG writer found two more that the sub-task list does not mention:

- `catalog/agents/doc-updater.md`, which instructed the agent to add a DEVLOG entry "always" for every session.
- `catalog/hooks/auto-devlog.{sh,ps1}`, which mechanically prepends a narrative entry above the first `## [` heading.

Both were brought into scope. The phase's stated goal is "every writer of DEVLOG produces the index format, so the file can never regrow into a log", and a writer left un-aligned defeats that goal regardless of whether the sub-task list enumerated it. The hook in particular is the single largest regrowth vector, since it runs unattended.

## 3. Chronological Steps

### 3.1 The devlog-generation skill (sub-task 2.1)

Rewritten to v2.0.0 around an explicit **Output Contract** section: the whole file is a header plus one table, with a per-column source-and-rule table so there is no ambiguity about what goes in a cell. The discovery logic is preserved (git tags, `CHANGELOG.md` headings, the per-version docs tree); only the destination changed.

Four things the rewrite adds beyond a format description:

- **Link resolution before writing**, with three ordered fallbacks: multiple version-prefixed plans link all of them; no version-prefixed plan links the minor's `plans/` directory rather than guessing which slug-named plan belongs to the patch; a genuinely absent target gets a literal `-`. The rule is stated as "never emit a link to a path that does not exist", because a broken link in a pure-navigation file is the one defect that makes the file worthless.
- **Insert-or-update, never append blindly**, with the grep that checks first. Idempotence on re-run is a stated requirement, not an implied one.
- **A conversion procedure** for a project whose DEVLOG is still narrative, carrying forward what Phase 1 learned: archive first, prove preservation by hash rather than by a successful copy, and collapse the pre-canonical era by minor version so the ceiling keeps holding instead of merely starting out satisfied.
- **A failure-mode table** covering all seven cases the plan named, plus the "user asks to record a phase, not a release" case, which routes to `[[session-history]]` and adds nothing.

Frontmatter: `summary_l0` at 11 words, `overview_l1` trimmed from 156 to 144 against the 150-word cap, description rewritten pushy with a SKIP clause (see section 4 for what that cost). Registry entries in `data/skills.json` and `data/SKILL_INDEX.md` were hand-edited via a targeted JSON round-trip with matching indent, producing a 5-line diff; `build_skills_catalog.py` was deliberately not run, since it rewrites the whole tree.

### 3.2 The update and setup flows (sub-task 2.2)

`catalog/commands/update.md`: the menu entry, the delegation target annotation, the release-order prose, and the release delegation chain, plus a new **devlog scope** section stating the one-line contract and the in-place-update rule.

That section also records an ordering change. The release flow ran `docs -> devlog -> gitignore -> version -> changelog -> refactor`. An index line is keyed by the released version and dated by its changelog heading, so running `devlog` before either would mean guessing both. The order is now `docs -> gitignore -> version -> changelog -> devlog -> refactor`. A narrative entry needed neither input, which is exactly why the old ordering was harmless until now.

`setup-project`: scaffolds the index-format header rather than "a dated first entry recording the bootstrap", and explicitly declines to convert an existing narrative DEVLOG in place, offering the conversion procedure instead.

`doc-updater`: the always-update target moved from `docs/DEVLOG.md` to the per-version `development/history/` directory; the DEVLOG entry template became a session-history template; DEVLOG is now touched only when a release is cut, and then by exactly one line. Its success metrics and rules were updated in lockstep, including the frontmatter description.

### 3.3 The auto-devlog hook, and two defects

Both siblings gained an index-format guard: detect the index table header, print where narrative belongs, exit 0. The guard is deliberately narrow, and the test suite asserts both directions, because a guard that fired on every DEVLOG would silently disable the hook for consuming projects that kept the narrative format, and that failure is indistinguishable from the hook working.

Writing the parity test then surfaced a defect nobody had reviewed for:

**`auto-devlog.ps1` had no opt-in gate at all.** The `.sh` sibling has gated on `AUTO_DEVLOG=1` since it shipped; the PowerShell implementation checked only `NEXUS_DISABLED_HOOKS` and `NEXUS_HOOK_PROFILE`, so on PowerShell the hook was effectively **opt-out** and wrote to `docs/DEVLOG.md` at every session end for users who never asked for it.

This is the most plausible explanation for the growth anomaly Phase 1 recorded without a cause: the plan measured DEVLOG at 3,149 lines on 2026-08-18 and Phase 1 found 5,615 on 2026-08-21, a gain of 2,466 lines in three days that no release accounts for. The gate is now present in both, with a comment stating the divergence so the fix is not mistaken for a stylistic addition.

This is precisely the case AGENTS.md makes for parametrizing every behavioral assertion over both implementations. A POSIX-only test could not have reached it, and review had not.

### 3.4 Tests (sub-task 2.3)

The plan asks for a pytest that feeds a fixture repo through "the devlog index-line generation". That generation is agent-driven prose, not an executable, so there is no function to call. Rather than build a fixture harness around a script that does not exist, the sub-task's intent (prove the flow is self-sustaining) was met with two suites that assert real behavior:

- `catalog/hooks/tests/test_auto_devlog_index_guard.py`, 10 assertions across both implementations: an index comes back byte-identical, the skip explains itself, a narrative DEVLOG still receives an entry, an absent DEVLOG is silent and is not created, and the opt-in gate governs. The double-run guard was a trap worth noting: a DEVLOG created by a test is modified *now*, so without backdating its mtime past the 300-second window every test would have exited 0 for the wrong reason and asserted nothing.
- `tests/validators/test_devlog_index_format.py`, 10 gates on the index itself. This is the mechanical half of the contract, and the more important suite: the 150-line ceiling as a hard failure, no narrative headings or `<details>` blocks, no duplicate version line, ISO dates, summary cells under 200 characters, every link resolving, no root-relative links, and every released 3.x version in `CHANGELOG.md` having a line.

Every gate in the second suite was verified to **fail on an injected violation**, not merely to pass on the current file. A gate that has only ever been observed passing is not known to work.

### 3.5 Dry-run

Per the plan, the devlog step was dry-run against this repo. v3.18.0 is unreleased, so the correct behavior is to add nothing, and `docs/DEVLOG.md` is unchanged by this phase at 99 lines with no v3.18.0 row. For the eventual release, the plan and history links resolve and `known-gaps.md` is absent, so that cell would be a literal `-`: the failure-mode path is exercised by the real next release, not only by a fixture.

## 4. A General Trap Found While Authoring Routing Cases

The trigger-eval gate reported `devlog-generation` had no `evals/trigger-cases.json`, and since the phase rewrote its entire trigger surface, cases were added: four positive phrasings and four near-miss negatives drawn from the skill's own SKIP clause.

The gate then failed, twice, on the negatives:

1. "generate the changelog entry for this release" scored a perfect **1.00** against `devlog-generation`.
2. After fixing that, "what work is still open or deferred for this version" also scored **1.00**.

The cause is structural. `scripts/run_trigger_evals.py` tokenizes the entire `description` field and has no notion of negation, so a SKIP clause that names what it fences off imports that vocabulary as **positive** trigger words. The phrases "open or deferred work" and "CHANGELOG.md" appeared in the description only to say *do not use this skill for those*, and the scorer read them as evidence to use it.

The local fix was to word every SKIP clause to name its target skill without reusing the target's own vocabulary ("unfinished or carried-over items (use known-gaps-tracker)" rather than "open or deferred work"). Two of the three edits were semantic improvements regardless: "generate ... an entry" is narrative-log vocabulary this skill abolished, so removing it made the description more accurate as well as better-routing.

The general problem is not fixed and is not in this phase's scope. AGENTS.md instructs every skill author to add a SKIP clause; the routing gate penalises doing so. The 40 allowlisted collisions are worth re-examining under that lens. Carried to Phase 5's known-gaps reconciliation.

## 5. Verification

| Check | Result |
|---|---|
| `pytest tests catalog/hooks/tests --ignore=tests/installer` | **3,471 passed, 48 skipped, 0 failed** |
| `test_auto_devlog_index_guard.py` | 10 passed across both `.sh` and `.ps1` |
| `test_devlog_index_format.py` | 10 passed; each gate separately verified to fail on an injected violation |
| `shellcheck --severity=warning auto-devlog.sh` | clean |
| `auto-devlog.ps1` AST parse | OK |
| `run_trigger_evals.py --gate` | PASS, 0 routing failures across 13 skills with cases |
| `validate_skills.py --bundles-only` | PASS, 273 skills, 0 errors, 0 warnings |
| `check_registry_entries.py --check --strict` | PASS |
| `validate_unicode_safety.py --strict` | PASS repo-wide |
| `validate_doc_budgets.py` | PASS, 8 budgeted docs within ceiling |
| `validate_decision_records.py` | PASS, 11 records |
| `check_doc_colocation.py`, `check_version_sync.py`, `check_base_template_parity.py`, `validate_no_personal_paths.py` | PASS |
| `docs/DEVLOG.md` | unchanged at 99 lines, correctly, since no release was cut |
| CI | no change needed; the suite is auto-discovered, both new test files are collected, and no workflow references DEVLOG |

`tests/installer` was excluded from this run. It is unaffected by a documentation-and-hook diff and contains the pre-existing `test_ps_standalone_extracts_and_hands_off` PATH failure recorded in the Phase 1 history; the full suite including it was run in Phase 1.

## 6. Ending State

- **Files added**: `catalog/hooks/tests/test_auto_devlog_index_guard.py`, `tests/validators/test_devlog_index_format.py`, `catalog/skills/workflow/devlog-generation/evals/trigger-cases.json`, this history file
- **Files modified**: `catalog/skills/workflow/devlog-generation/SKILL.md` (rewritten to v2.0.0), its `agents/openai.yaml`, `catalog/commands/update.md`, `catalog/skills/project-setup/setup-project/SKILL.md`, `catalog/agents/doc-updater.md`, `catalog/hooks/auto-devlog.sh`, `catalog/hooks/auto-devlog.ps1`, `data/skills.json`, `data/SKILL_INDEX.md`, `CHANGELOG.md`
- **Catalog counts**: unchanged at 273 skills, 18 commands, 31 hooks, 23 agents. No skill added or removed; one rewritten in place.
- **Stability gate**: met. All four writers the plan named specify the index format, plus the two it did not; the dry-run edits only the current release's line; validators and tests pass.

## 7. Next Steps

1. **Phase 3 (AGENTS.md MT-1 ratchet-down)** is independent of Phases 1 and 2 and is the natural next step.
2. **Phase 4 (retention policy)** depends on Phase 1 and can follow either.
3. Carry to Phase 5's known-gaps reconciliation:
   - The SKIP-clause / routing-scorer tension from section 4, including a re-examination of the 40 allowlisted collisions.
   - The `test_ps_standalone_extracts_and_hands_off` bare-`tar` PATH failure and the stray `Microsoft/` directory, both from Phase 1.
   - Whether `docs/policy/doc-budgets.json` should gain a `docs/DEVLOG.md` ceiling, so the line limit lives beside the other ratchets instead of only in a test constant.
