# Known Gaps - v4.8

**Project**: Nexus-Hub
**Status**: open; seeded when the agentic-setup work landed on develop after the v4.7.0 release. The v4.8.0 adoption plan (agentic loops) is complete locally on `feat/v4.8.0-agentic-loops`, four commits, awaiting the approved single push and integration PR into `develop`
**Last updated**: 2026-09-07

## Open Items - found 2026-09-06 while verifying this session's work

### Warnings (WN)

#### WN-A - The interactive guide has 201 bytes of headroom under its size budget

- **Source**: found running the full suite to verify the documentation-gate repairs.
- **What was observed**: `tests/guides/test_nexus_hub_guide.py::test_file_size_budget` asserts the guide is under 500000 bytes. The artifact measures 499799, leaving **201 bytes**, or 0.04 percent. The next content addition of any size breaks the build.
- **Why it is not just a number to raise**: the budget exists because the guide is a single self-contained offline HTML document that a browser downloads in full. Raising the ceiling to clear a red test would spend the constraint rather than honor it. The v4.4.x guide cycle already fought for bytes (`docs/releases/v4/v4.4/` history), so the compaction levers are documented.
- **Suggested next step**: decide deliberately, ahead of the next guide edit, between compacting existing content and raising the budget with a recorded rationale. Do not decide it inside a phase that merely needs the test green.

#### WN-C - `make test` has an undocumented prerequisite, so three extension suites fail on a fresh clone

- **Source**: found running the six extension suites to verify this session's work.
- **What was observed**: `make test` runs `cd extensions/<name> && python -m pytest` for six extensions with no install step. On a workstation that has not editable-installed them, three of the six cannot pass: `nexus-code-search` dies at conftest import (`ModuleNotFoundError: No module named 'nexus_code_search.config'`, because the package uses a `src/` layout), `nexus-web-fetch` reports 3 collection errors, and `nexus-context-compressor` reports 3 failures asserting `'regex' == 'ast'`.
- **None of these is a product defect.** CI runs `pip install -e "extensions/<name>/[dev]"` for all six (`.github/workflows/ci.yml` lines 245-250), and `nexus-code-search` carries `tree-sitter` in its core dependencies, which is what makes the context-compressor's AST path available. The compressor's own docstring states that the regex path is used "when the AST infra is absent (sibling not installed, tree-sitter missing)", so the fallback is behaving as designed and the three tests are simply asserting the AST path they cannot reach.
- **Why it is worth recording**: the prerequisite is named only in the individual extension READMEs, and there is no `make install` or `make dev` target. A contributor running the repository's own documented test command on a fresh clone gets three broken suites and three unrelated-looking error shapes, none of which points at the missing install.
- **Suggested next step**: either add a `make dev` target that performs the six editable installs and reference it from the `test` target's help text, or have those three suites skip with an explanatory reason when their package or the AST backend is not importable (`pytest.importorskip`). The second option keeps `make test` honest on any machine; the first keeps coverage. They are not exclusive.
- **Not changed here**: the tests are correct given the documented install, so silencing them would trade a confusing failure for silent non-coverage. This is a deliberate design choice for a maintainer, not a repair.

#### WN-B - `test_file_size_budget` measured the checkout, not the artifact (fixed here)

- **Source**: same run. The test failed on this Windows workstation and passed in CI.
- **Cause**: it used `Path.stat().st_size`, the size on disk. With `core.autocrlf=true` a Windows checkout holds CRLF while the committed blob and every served copy hold LF, so the working-tree file is one byte per line larger: 504222 on disk against a 499799 blob, a difference of 4423, exactly the file's 4423 line count. `git status` reported the file clean throughout, which is what made the failure read as a real budget breach.
- **Resolution**: the test now normalizes CRLF to LF before measuring, so the number is platform-independent and equals what a browser downloads. Verified to equal the committed blob byte for byte, and negative-controlled against a simulated over-budget artifact.
- **Class**: the same defect as v3.15 BG-16, a test whose verdict depended on the environment that launched it rather than on the product. Worth remembering as a pattern: any assertion over `st_size`, line counts, or file bytes in this repository must normalize line endings first, or it is a coin flip on the contributor's platform.

## Open Items - found 2026-09-07 during the v4.8.0 adoption plan

### Warnings (WN)

#### WN-D - The `make` binary is absent on the development host, so the documented gate commands cannot be invoked as written

- **Source phase**: v4.8.0 Phase 1 (loop intake and run contract).
- **Plan reference**: Phase 1 Stability Gate and sub-task 1.4 both instruct `make validate`; every phase of this plan repeats it.
- **What was observed**: `make validate` fails with `bash: line 5: make: command not found`. `AGENTS.md`, `CLAUDE.md`, and every plan phase name `make validate`, `make lint`, and `make test` as the repository's gate commands, and none of the three can be invoked on this Windows workstation.
- **Why it is not the same as WN-C**: `WN-C` is about a missing editable-install prerequisite that makes three extension suites fail *once `make test` runs*. This is one level earlier: the task runner itself is not present, so no target runs at all.
- **What was done instead**: every step of the `validate` target was extracted from the `Makefile` and executed directly, each checked for a zero exit: 28 `python scripts/<name>.py` guards, the 4 inline JSON parse checks, and the `nexus-context-compressor` accuracy-regression gate (33 in total). This is faithful but manual, and it silently drops any future step a maintainer adds to the target.
- **Suggested next step**: ship a `scripts/gate.py` (or a `nexus-hub gate` subcommand) that runs the same ordered step list the `Makefile` targets run, and have the `Makefile` delegate to it. That makes one list authoritative for both a Unix host with `make` and a Windows host without it, instead of a contributor transcribing targets by hand. A thinner alternative is to document `winget install GnuWin32.Make` as a prerequisite, which fixes the host but leaves the two lists able to drift.
- **Not changed here**: adding a task-runner shim is repository tooling, well outside a doctrine phase's scope, and choosing between the two options above changes what every contributor runs.

#### WN-E - Phase 4 ran a tier below the plan's recommendation, surfaced rather than absorbed

- **Source phase**: v4.8.0 Phase 4 (OWASP agentic framework mapping).
- **Plan reference**: Phase 4 `**Recommended model tier**: frontier`, `**Recommended effort level**: high`.
- **What was observed**: the session ran `claude-opus-5`, which the plan's own model map places at `strong`, not `frontier` (`claude-fable-5-1`). Claude Code exposes no scriptable model switch, so the pre-flight surfaced the exact keystrokes (`/model claude-fable-5-1`, then `/effort high`) at the phase boundary and proceeded at strong under the `full` driver, which by contract never blocks implementation.
- **Why it is recorded rather than treated as a failure**: the no-degradation rule forbids SILENTLY substituting a lower tier, not proceeding after surfacing the delta. This is the same condition v4.7.0 recorded as its own `WN-1`, and the same handling.
- **What actually mitigated the phase's risk**: not the tier. The phase's named risk was a mistranscribed framework identifier misleading a compliance reader, and the control was executing the plan's re-fetch instruction rather than transcribing from the plan's text. That caught two wrong official titles (ASI03 and ASI06 use ampersands) and one source URL that does not enumerate the ten entries.
- **Suggested next step**: nothing for this release. If a future plan phase's risk genuinely depends on tier rather than on procedure, consider making the `full` driver pause once at that phase boundary instead of surfacing and continuing. That is a change to `implement-phase`, not to this plan.

#### WN-F - Nothing detects a framework tag whose supporting sentence is later deleted

- **Source phase**: v4.8.0 Phase 4.
- **Plan reference**: sub-task 4.4 ("tag only IDs whose control the body actually teaches; a tag with no supporting sentence is a mistranscription, not coverage").
- **What was observed**: the test suite asserts that every declared `owasp_agentic` identifier is EXPLAINED in that skill's `references/standards.md`. It does not and cannot assert that the skill's body still teaches the control the explanation describes. An editor who removes the taught control from a `SKILL.md` body leaves the tag, the standards paragraph, and the coverage-matrix row all intact and all now false.
- **Why it is not fixable by a stronger regex**: the mapping is a judgment, and this is the same class as the `agent-execution-isolation` ASI02 near-miss recorded in the Phase 4 history, where a keyword grep found no evidence that a careful reading found immediately. A body-content check would produce false rejections on exactly the skills whose vocabulary differs from the framework's.
- **Suggested next step**: treat framework-tag re-verification as periodic human work owned by [[platform-contract-verification]], which already re-verifies external contracts before a release, rather than as a gate. The same step covers the related exposure that OWASP will version the framework and can renumber or retitle an entry, making every tag stale at once with no local signal.
- **Recorded in**: the decision record's `## Consequences` section states this residual gap; this entry is its ledger counterpart so the next plan ingests it.

### Deferred (DF)

#### DF-1 - The Goal's "every review deliverable names its verifier class" reached the evaluation skill but no review skill

- **Source phase**: v4.8.0 Phase 5 (independent Goal-vs-codebase review).
- **Plan reference**: plan header Goal, clause 3: "every review and research deliverable names the verifier class that grades it".
- **What was observed**: `references/verifier-taxonomy.md` exists and is cited from Step 1 of `ai-output-evaluation`, and the research half of the clause landed on both research surfaces. The REVIEW half did not: no task line (T011 to T017) wired the taxonomy into `multi-agent-code-review`, `plan-review`, `code-quality`, `testing-review`, or any other review skill, so a review deliverable still does not name the class of verifier that graded it. A reader of the Goal would expect it to.
- **Why it was not fixed inside the phase**: the Goal clause is broader than every task line the plan wrote for it. Wiring a citation into the review pipeline touches skills no phase declared in scope, and choosing WHICH review surfaces should carry it (the orchestrating skill only, or each persona) is a design decision, not a mechanical edit. Fixing it silently here would expand the plan's scope after its review.
- **Suggested next step**: add one sentence to `multi-agent-code-review` (the coordinating skill for the review cluster) requiring each finding's grading class to be named from the taxonomy, and let the single-lens personas inherit it rather than restating it. That keeps the rule-ownership discipline the same cluster already follows. One task line, next plan.
- **Not a pass**: recorded as a Goal miss rather than reported as delivered.

### Warnings (WN), continued

#### WN-G - The coverage builder's frontmatter parser mis-parses a trailing comment on any framework field

- **Source phase**: v4.8.0 Phase 5 (Tier 3 deep pass, adversarial finding AF-6).
- **What was observed**: `scripts/build_framework_coverage.py::parse_id_list` does not strip a trailing YAML comment. Given `owasp_agentic: [ASI01] # fine`, it yields the single identifier `'[ASI01] # fine'`, which would appear verbatim as a control row in `docs/framework-coverage.md`. `validate_skills.py` parses the same line correctly, so the validator passes and the generated document is wrong.
- **Scope**: PRE-EXISTING and applies to all seven framework fields, not only the one added in v4.8.0. No shipped skill carries a comment on a framework line, so the committed matrix is correct today.
- **Why it was not fixed here**: the fix is one line in a parser shared by all seven fields, and a change to shared parsing behavior should land with a test matrix covering all seven rather than riding along in a mapping phase. The v4.8.0 field's own bypass routes (AF-1, AF-2) WERE fixed, because those defeated the membership guarantee this release introduced.
- **Suggested next step**: strip `#` and everything after it in `parse_id_list`, and add one parametrized test over all seven field names asserting a trailing comment is ignored.

#### WN-H - The coverage builder silently ignores a framework field written as a YAML block sequence

- **Source phase**: v4.8.0 Phase 5 (Tier 3 deep pass, adversarial finding AF-7).
- **What was observed**: `parse_id_list` reads only the text after the colon, so a block-sequence tag (`owasp_agentic:` followed by indented `- ASI02` lines) yields nothing and the skill is absent from the coverage matrix. `validate_skills.py` accepts that shape as valid, and `AGENTS.md` documents block sequences as an accepted shape, so a maintainer can write a tag that validates cleanly and never appears in the matrix. This is silent UNDER-coverage, which is harder to notice than an error.
- **Scope**: PRE-EXISTING and applies to all seven fields. All 15 skills tagged in v4.8.0 use the flow-list form, so the committed matrix is complete today; verified by the matrix showing all ten identifiers covered.
- **Suggested next step**: teach `parse_id_list`'s caller to read a following block sequence, exactly as `validate_skills.py::_owasp_agentic_values` already does, and add a parametrized test over all seven fields asserting both YAML shapes reach the matrix. Until then, prefer the flow-list form when tagging.

#### WN-I - `test_org_cli.py::test_disconnect_requires_confirmation_and_yes_removes_state_and_cache` is flaky

- **Source phase**: v4.8.0 Phase 5 (full local gate).
- **What was observed**: `python -m pytest tests/workflows tests/installer tests/ci -q` reported `1 failed, 670 passed, 60 skipped`, failing at `tests/installer/test_org_cli.py:300`. The identical command on the identical tree then reported `671 passed, 60 skipped`. The test also passes alone and passes with its whole file. Not reproducible; nothing in the v4.8.0 diff touches the org CLI, `nexus-hub org disconnect`, or its state and cache handling.
- **One observation worth keeping**: the failing traceback resolved its repository root through `C:\Users\BEDOURTHE\OneDrive - Supira\Documents\...` while the passing runs resolve through `C:\Users\BEDOURTHE\Documents\...`. This host has OneDrive folder redirection, so the same logical path can present under two roots. A test that removes state and cache directories and then asserts their absence is exactly the shape that a redirected or lazily-synced path can break intermittently, and `WN-B` in this same ledger already records one Windows path-semantics defect (CRLF versus LF) of the same family.
- **Suggested next step**: run the file under `pytest -p no:randomly` and with `--basetemp` pinned outside the OneDrive tree to confirm or eliminate the redirection hypothesis, then apply the `flaky-test-detector` procedure. Do NOT mark it skipped: a flake that removes and re-checks filesystem state is a candidate real defect on a redirected home, which is a configuration many Windows users have.
- **Why it did not block this phase**: the definitive full-suite run for this release is recorded in the last-phase evidence file, and this test passed in it.

## Ledger condition measured for T023, 2026-09-06

T023 of `v4.8.0-adoption-visa-vulnerability-agentic-harness.md` reconciles every reachable open
known-gap ledger. This section records what that task will find, measured rather than estimated, so
it starts from a number instead of re-deriving one.

**Three counts of the same thing disagree.**

| Count | Value |
|---|---|
| Summary-table `Open` column, summed across all 20 ledgers | 175 |
| Entries physically under an `Open Items` heading | 157 |
| Of those, entries whose own heading says `RESOLVED` | 16 |
| Remainder not self-declared resolved | 141 |

By category the remainder is 77 Deferred, 28 Warnings, 22 Missing-tests, 6 Quality-gate, 5
Not-implemented, and 3 Bugs.

**The true figure is below 141, because some remaining entries are resolved in the tree without
saying so.** Two were spot-verified on 2026-09-06:

- `docs/releases/v3/v3.14/known-gaps.md` **BG-1** (`verify_platform_contracts.py` registered in
  neither installer) carries its own `Resolution (Phase 6.3): RESOLVED` line while sitting under
  `Open Items`. Confirmed: the script is in `DEV_ONLY_SCRIPTS` in
  `catalog/hooks/tests/test_installer_smoke.py`.
- `docs/releases/v3/v3.15/known-gaps.md` **BG-16** (a bootstrap test whose verdict depended on the
  launching shell, because GNU `tar` from Git Bash shadowed `System32	ar.exe`) still reads
  `Status: Open`. It is fixed: `install.ps1` has a `Resolve-TarExe` helper that prefers
  `System32	ar.exe` explicitly, added in commit `69924673` ("fix: close every open v3.18 known
  gap"). The named test was re-run from Git Bash on 2026-09-06 and passed.

`docs/releases/v4/v4.0/known-gaps.md` shows the disagreement structurally: its
`docs-lifespan-tree-and-enforcement` summary reports `BG: Open 0, Resolved 5`, and all five of those
entries sit under `### Open Items` with `RESOLVED` in their headings. The table is right and the
placement is stale. One entry in the same block, `BG-2`, is genuinely open and still carries a
`Suggested next step`, so the block cannot be swept wholesale.

**Why this was not reconciled ahead of T023.** It is T023's stated job, scheduled for that plan's
final phase, and a reconciliation run before the implementation it reconciles would be redone. What
is recorded here is the measurement, not the fix.

**How to reconcile, given the above.** Do not trust the Summary tables; they are derived and drift
silently, which is the same defect class as the plan exit-checklists (see
`docs/decisions/implemented/process/2026-09-06-plan-checkboxes-are-not-completion-evidence.md`) and
as the two documentation gates that scanned a retired root. Read each entry's own annotation, verify
its claim against the tree, then move the settled ones into that ledger's `Resolved Items` section
and recompute the Summary from the entries rather than editing it by hand.

## Carried in from v4.6.0, which was never cut

The `v4.6.0-adoption-visa-vulnerability-agentic-harness` plan was approved on 2026-09-01 and never
implemented: 0 of its 31 sub-tasks, no session history, no `last-phase-evidence.md`, no tag, and no
CHANGELOG entry. The v4.7.0 changelog recorded the situation at the time ("v4.6.0 was never cut; its
plan is unimplemented and carries forward").

It cannot ship under its original number. v4.7.0 is tagged and published and `plugin.json` reads
`4.7.0`, so a `v4.6.0` tag would sort behind the current release and be invisible to anything
resolving latest. On 2026-09-06 the plan and its comparison were retargeted into this version as
`v4.8.0-adoption-visa-vulnerability-agentic-harness.md`, and `docs/releases/v4/v4.6/` no longer
exists. The plan's own `**Retargeted**` header line carries the same statement.

The Release Sequencing Gate that plan declares is satisfied: v4.5.0 is complete, tagged, merged, and
back-merged. Its remaining scope is therefore ordinary v4.8.0 implementation work, not a blocked item.

## Carried in from the v3.14 agentic-setup adoption

That branch shipped its own v3.14 ledger, written 2026-07-13 while the release was still held. It is
superseded: v3.14.0 released on 2026-07-16 and develop's v3.14 ledger has been maintained through
v3.14.6. Rather than merge a stale ledger over a released one, its still-open items are carried here,
where the work is actually landing. WN-2 (stale marketplace skill-count prose) is dropped as resolved:
the counts were recomputed from the merged catalog in this landing and now sum to 336.

### Warnings (WN)

#### WN-1 - New pushy skill descriptions exceed the 250-char full-mode length check

- **Source phase**: Phase 1 (1.1, 1.2), Phase 2 (2.1)
- **Plan reference**: `docs/releases/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md` sub-tasks 1.1-1.2, 2.1
- **Reason**: `false-confidence-test-audit`, `commit-sweep`, and `lint-repair-loop` carry pushy descriptions (verbatim trigger phrases plus a SKIP clause) well over 250 characters, so `validate_skills.py` FULL mode would flag them. This is the known catalog-wide pushy-description-vs-250-char tension (the WN-v3121 family); `make validate` does not run full mode and is clean. Intentional per the AGENTS.md description-style rule (combat under-triggering).
- **Suggested next step**: None required. Track with the catalog-wide description-length decision; do not shorten at the cost of trigger coverage.

#### WN-3 - Bash hook tests cannot run on the Windows dev host

- **Source phase**: Phase 2 (2.3)
- **Plan reference**: sub-task 2.3
- **Reason**: `pytest catalog/hooks/tests/test_lint_autofix.py` fails locally because `shutil.which("bash")` resolves to the Windows `system32\bash.EXE` (WSL), which cannot read a Windows-path `.sh` (exit 127). This is the WN-1 environment family from v3.12. The hook's six behaviors were instead verified end-to-end through Git Bash (opt-in gate, fail-open, non-commit no-op, disabled-env opt-out, skip-unstaged, and format + re-stage with ruff on PATH), ShellCheck is clean, the `.ps1` AST parses, and the test collects cleanly (7 tests).
- **Suggested next step**: None required. CI (ubuntu) is the authoritative gate for the bash hook suites; `pip install pytest ruff` was added to the CI tests job this phase so the ruff-gated formatting cases also run there (ubuntu-latest ships jq).

### Missing tests / coverage gaps (MT)

#### MT-1 - capture_screenshot.py is not unit-tested

- **Source phase**: Phase 4 (4.2)
- **Plan reference**: `docs/releases/v3/v3.14/plans/v3.14.0-agentic-setup-adoption.md` sub-task 4.2
- **Reason**: `capture_screenshot.py` drives a headless Chromium-family browser, which is not reliably present in CI or on the dev host, so it is documented and degrades gracefully (exit 3 with an install hint) rather than unit-tested. The perceptual-diff core (`perceptual_diff.py`) IS fully tested (7 cases, Pillow-gated), and `Pillow` was added to the CI tests job so those run.
- **Suggested next step**: Add a browser-gated smoke test in a CI job that installs a headless browser, or exercise it in the Phase 7 end-of-shift orchestrator's visual-regression step when a browser is available.
