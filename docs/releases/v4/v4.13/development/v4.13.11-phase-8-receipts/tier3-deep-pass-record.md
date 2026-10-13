# v4.13.11 Tier 3 deep-pass record

**Covers**: the retained Tier 3 functional-verification deep-pass record (steps 1-8) for v4.13.11, written by an independent read-only pass before fix cycle 1. **Read by**: the integration reviewer and `/update release`. **Key topics**: feature inventory, exercises, adversarial and convergence results, Goal-vs-plan sufficiency. Home paths are shown as `~`; the outcome of fix cycle 1 is recorded in the last-phase evidence, not here.

Evidence root: this directory (`scratchpad/deep-pass/`). During the run it was mapped as drive `Q:` with `subst` to stay under Windows MAX_PATH, so `Q:/x` in this record means `scratchpad/deep-pass/x`.

## 1. Inputs, revision and base

- Worktree: `Nexus-Hub-worktrees/v41311-plan`, branch `fix/v4.13.11-known-gaps-sweep-and-minor-close`.
- Revision: HEAD `066235c90b1eb3de346658c8a3ef3fd6b19bced1` plus uncommitted Phase 8 changes. Integration base (merge base with origin/develop): `002b7283a8b839588c8d0e468cbb502f594cb3e6`.
- Plan: `docs/releases/v4/v4.13/plans/v4.13.11-known-gaps-sweep-and-minor-close.md` (Goal in header, phases 1-8, 8.6 scoped note). Maintainer request as relayed by the coordinator. Phase evidence 1-7 and receipts were read.
- **The tree moved during the run.** Other workers added uncommitted changes while this pass ran (WN-8-v41310 opening.css plus re-stamped guide pages, WN-30 installers/README/test_installer_smoke.py, ledger closures of AR-07/AR-09/AR-18/WN-1-v4133/WN-6-v4131, carry-forward contract blocks). Per the coordinator these are out of scope and were not re-exercised. Exercises before about 13:50 local ran against the earlier tree; the installer run (after that time) copied whatever was on disk then.
- `fix_rerun_cycles_used`: 0. No fixes applied; no tree changes made by this pass.

## 2. Blast-radius verdict

- **Verdict**: run.
- **Positive triggers (diff-evidenced)**: hooks (`catalog/hooks/*.sh|ps1|py`, 30 files); generated HTML and guide sources (`guides/website/*.html`, `shared/*.css|js`, `src/sky-sentinel.js`, `docs/handbooks/*.html`); distributed skills, commands, templates, registries (`catalog/skills/**`, `catalog/commands/*.md`, `catalog/templates/spec-template.md`, `data/skills.json`, `data/SKILL_INDEX.md`); installers (`scripts/installer.sh`, `scripts/installer.ps1`); CI workflows and profiles (`.github/workflows/*-usage-monitor.yml`, `.github/dependabot.yml`, `scripts/ci/profiles.py`, `scripts/ci/run.py`); dependency security (`scripts/ci/requirements-py311.txt`, four extension `pyproject.toml` floors); validation/migration boundaries (`scripts/completion_minor.py`, `scripts/minor_close.py`, `scripts/validate_skills.py`); extension manifests and locks (four monitors).

## 3-4. Feature inventory and observed results

Counts: **34 inventory rows; 27 exercised through a real boundary (some by focused real-helper tests); 7 not covered** (listed in section 9).

| # | Feature (phase/task) | Boundary and input | Observed | Status | Evidence |
|---|---|---|---|---|---|
| 1 | Ledger parse on real tree (T005-T008, T028) | `minor_close.py status --minor v4.13 --repo .` | exit 0, `gaps.minor unmet`, 92 open, 0 unparsed; open set equals carry-forward manifest minus 5 planned closures (AR-08, AR-60, WN-32, WN-37, WN-45) | pass | `ledger/status-worktree.txt` |
| 2 | Parser refusal fixtures (T005/T006) | disposable fixture repo, real CLI, 8+3 hostile edits | ACCEPTED, CHECKED, lowercase `resolved` stay open; `MIGRATED to v4.14.0` without target -> `migration-target-missing`; `MIGRATED to v4.13.11` -> `migration-not-forward`; stale header count -> `unparsed (open-items-count)`. **But** a duplicated open ID (count adjusted) lists AR-26 twice with no ambiguity notice, and a heading with its ID removed (count adjusted) silently disappears. Same at base parser (pre-existing). | finding (pre-existing) | `ledger/mut-summary.txt`, `ledger/mut2-summary.txt`, `ledger/mut2-base-summary.txt`, `ledger/mut/`, `ledger/mutbase/` |
| 3 | Destination preflight, stub/truncated/duplicate refusal (T005, BG-15) | `test_gap_migration_and_archive.py -k incomplete_reuse,complete_reconciled_copy,unmatched_ticks,consolidated_owner,active_and_archived_target` (real helpers) | 26 passed | pass | `ledger/pytest-destination-safety.txt` |
| 4 | Migration dry-runs for 92 residuals (T029) | not re-run: record is HMAC-bound to repo root and secret; a fixture record would be a forgery | not re-observed | NOT COVERED | - |
| 5 | session-summary Git-root name (AR-48) | both siblings, current vs base, invoked from `sub/deeper` of disposable repo | current: `Project: alpha-repo`; base: `Project: deeper` (log and digest) | pass | `hk/session-summary-run.txt` |
| 6 | session-summary UTF-8 child output (WN-45, uncommitted) | non-ASCII plan slug | both siblings write byte-identical `Plan:` line; digest is ASCII by design (`plan_status` strips non-ASCII), so the decoding path is not discriminated by this input | pass (weak) | `hk/session-summary-utf8b.txt` |
| 7 | auto-devlog line-1 insertion + subject bound (BG-13, WN-36) | heading on line 1, three 60,000-char subjects, 5 MB stdin | current sh/ps1: entry inserted above line 1, old kept, max line 210, under 2 s. Base sh: no entry; base ps1: 60,025-char line | pass | `hk/devlog-run2.txt` |
| 8 | learning-capture large stdin + bounds (BG-14, WN-36) | 3 MB tool payload, malformed JSON, 8,000-byte cap | current sh/ps1: 5/5 valid JSON records, max line 493. Base sh dropped the large record ("argument list too long"). Malformed payload writes an `unknown` record in current and base. sh and ps1 lines are JSON-equal but not byte-identical (spacing). | pass | `hk/lc-run.txt` |
| 9 | provenance-ledger NUL refusal, path/hash identity, trust seam | both siblings, path with spaces, NUL path, later Bash exec | NUL refused with message, full path + sha256 recorded, TRUST SEAM flagged. `.ps1` epoch is 25,196 s behind `.sh` (PowerShell 5.1 `Get-Date -UFormat %s` local time); same at base | pass + pre-existing finding | `hk/pv-run.txt` |
| 10 | Description hooks keep all tool_input fields (BG-18) | both hooks, current vs base, plus malformed | current keeps `timeout`, `run_in_background`, `dangerouslyDisableSandbox`; base kept only `command`,`description`; malformed -> exit 0, no output | pass | `hk/bg18/` |
| 11 | Actual hook delivery | real `installer.ps1 -Workspace -Platforms claude -Yes`, isolated HOME/USERPROFILE/APPDATA/LOCALAPPDATA | 51 installed hooks byte-identical to catalog; 8 events registered; installed description hook preserves all fields; real `~/.nexus-hub` mtime unchanged (2026-10-03) | pass | `inst3-summary.txt`, `inst/` |
| 12 | Installer smoke EXPECTED_SCRIPTS (DF-006/008) | `check_installer_smoke.py` on that install, then after deleting one script | `installer smoke: PASS`; after removal exit 1 `expected installed script is missing: optimize_skill_description.py` | pass | `inst3-summary.txt` |
| 13 | affected.py lint (v3.15 WN-2) | `uvx ruff@0.6.9 --select F401,F841` current vs base | current clean; base F401 + F841 | pass | console log |
| 14 | Map CLI forwarding / baseline write (MT-1/MT-2, AR-08 registration) | `tests/integrations/test_map_cli.py` with extension src; partition and every-test registration tests | 4, 11 and 4 passed | pass | `tests/summary.txt` |
| 15 | Description limit 1024 (AR-06) | real `validate_skills.py --path` on 250/251/1024/1025-char fixtures | 250, 251, 1024 pass; 1025 exit 1 `description is 1025 characters (max 1024)` | pass | `vs/out-*.txt` |
| 16 | DEFAULT_GUARDS keep/revert (AR-08, BG-19) | `test_model_prompting_edit_routing.py` guard set incl. disposable-clone test | 14 passed (keep/restore byte exact, CRLF, concurrent edit abort, hung guard timeout) | pass | `tests/prompting-guards.log` |
| 17 | Model-routing helpers missing tools (BG-20) | both helpers, PATH without tools, no API key, ids claude-code/codex/cursor/antigravity/unknown | picker sentinel JSON, exit 0, siblings agree; invalid id: `.sh` exit 2, `.ps1` exit 0 (same at base) | pass + pre-existing finding | console log |
| 18 | Routing helper suite | `catalog/hooks/tests/test_model_routing_helpers.py` | 66 passed | pass | `tests/summary.txt` |
| 19 | build-catalog FORCE guard (AR-22) | real Makefile, GNU Make in offline manylinux container, disposable copy | without FORCE exit 2, `data/` hashes unchanged; FORCE=1 passes the guard (generator then failed only because my copy lacked `infrastructure/tools`) | pass (guard) | console log |
| 20 | CI per-platform timeouts (WN-35/38) | `run.py --profile full --list`, `detect_platform()`, `timeout_on` | host `windows`; hook-tests 2400, governance 3600 on windows, 1800/2700 elsewhere | pass | `tests/full-list.txt` |
| 21 | Required-check coverage | `check_required_check_coverage.py` | OK, 10 contexts unconditional | pass | `tests/required.txt` |
| 22 | Dependabot Copilot entry (WN-28) | YAML parse | 4 monitor npm entries incl. copilot with `@types/vscode` ignore | pass | console log |
| 23 | codexUsage.authPath machine scope (WN-29) | package.json parse | `scope=machine` | pass | console log |
| 24 | Monitor exact pins + clean build + package (AR-59) | per-monitor disposable copy, isolated HOME and npm cache: `npm ci --ignore-scripts`, compile, Vitest, `vsce package`, VSIX inspection | all 4: ci/compile/package 0, 0 caret devDeps, `@types/vscode@1.85.0`; tests claude 86, codex 128, cursor 313, copilot 292 passed; VSIX has no node_modules/ts/maps/tests | pass | `monitors/summary.txt`, `monitors/round3.txt`, `monitors/*-verify4.log` |
| 25 | Copilot verify:package + monitor workflows (WN-32, AR-60, uncommitted) | `npm run verify:package` plus planted files; workflow tests | clean VSIX passes; planted `out/auth.json` refused; **planted `out/credentials.json` packaged and passed**; workflow tests 43 passed | pass + finding | `monitors/copilot-verify-neg*.log` |
| 26 | Training hidden-host start/resume (WN-5-v41310) | headless Chromium on generated `training.html`, host `display:none` | start and resume -> `paused`, `pausedBy: stage`, tick 0 after 2 s; re-shown -> `running`, tick 31 | pass | `ui/exercise.json` |
| 27 | Skip link, theme semantics, aria-current (WN-6-v41310) | Tab, Enter, theme click; training and guide; 1280/390; light/dark | first Tab focuses visible "Skip to content" (top 10px); Enter focuses `main#app`, hash unchanged; theme button has action label, no `aria-pressed`; one `aria-current` in `#navLinks`; no page errors, no network requests | pass | `ui/exercise.json`, `ui/cur.py` output |
| 28 | Stamp check | `stamp_guide_shared.py --check` | OK, 21 fragments, 2 pages | pass | console log |
| 29 | Usage-probe isolation, notify helper delivery (WN-33, Phase 7) | focused tests | notify 13 passed; hook UTF-8 test 13 passed | pass (tests only) | `tests/summary.txt` |
| 30 | PyJWT remediation (WN-39) - real dependency audit | isolated uv venvs, payload probe, `pip_audit` (live advisory query) | 2.14.0: `RecursionError` leaks, audit exit 1 (PYSEC-2026-4141, PYSEC-2026-4183). 2.15.1: handled `DecodeError`, audit exit 0. Candidate constraints (144 pkgs) exit 0; base constraints exit 1 on pyjwt 2.14.0. Four `pyjwt>=2.15.0` floors present | pass | `dep/summary.txt`, `dep/audit-*.json` |
| 31 | Handbooks overview/distribution | detector 390/900/1440 | both pass, 0 findings | pass | `ui/det/overview.json`, `ui/det/distribution.json` |
| 32 | Spec template, governance SKIP, reasoning guidance, loop/redaction, skill-create rubric (T015-T018) | text/contract; covered by Phase 4 tests, not re-run here | not re-observed | NOT COVERED | - |
| 33 | Phase 7 fixes: presentify redaction, Windows long paths, attribution footer, Kimi wiring, `/usage` dispatch, cascade compat | not exercised | - | NOT COVERED | - |
| 34 | WN-40 ship-balance runtime; three serial guide legs | not run (full suites excluded by caller) | - | NOT COVERED | - |

## 5. Rendered-surface delegates

- Detector (`detect_visual_defects.py`, 390/900/1440): training 362 findings (base 359), guide home 107 (base 104), guide cheatsheets 8 (base 5): the only new finding on each is `parent-padding-escape` on `body > div > a`, the skip link parked at `top:-60px` until focused (intended; row 27 shows it visible when focused). Guide foundations 51 (base 45): the new ones sit in the in-flight WN-8 phone layout of the Foundations figure (out of scope per coordinator); sampling one 24 s loop showed reply lines revealed at 18-22 s with ellipsis clamp, so the overflow hits are intended clamps. Handbooks: pass. JSON: `ui/det/*.json`; screenshots `ui/foundations-*.png`.
- NOT COVERED: [[accessibility-engineering]] not invoked - guide, Training and handbook pages (time budget ended by coordinator).
- NOT COVERED: [[hallmark-design]] not invoked - same surfaces.
- NOT COVERED: [[browser-testing-with-devtools]] not invoked as a skill; console/pageerror/network listeners were captured in the Playwright exercise only.

## 6. Adversarial pass ([[adversarial-verifier]], applied as written; no code modified)

Attack surface: hook stdin payloads (untrusted), tool `file_path`/`command` strings passed to child processes, ledger Markdown (semi-trusted), VSIX contents, dependency set.

Confirmed findings (observed execution evidence; tests not added to the tree because this pass is find-and-report only):

- **AF-1 (P1)** `lint-on-write.ps1` `Invoke-Utf8Child` (uncommitted WN-45 rewrite) runs `.cmd/.bat` linters via `cmd.exe /d /s /c` and quotes only arguments containing whitespace or quotes. A written file named `x&pwnmarker&.js` with a stub `eslint.cmd` on PATH executed `pwnmarker` (marker file created). Base `& $Exe @Arguments` behaves the same: pre-existing, retained by the rewrite. Evidence `adv/out3-*.txt`.
- **AF-2 (P1)** `rewrite-command.ps1` with a `.bat` Python shim (pyenv-win style) and command `echo a" & pwnmarker & echo "b`: the injected command ran at hook time and the hook emitted `permissionDecision: allow` with the shim's stdout as `updatedInput.command`. Base identical: pre-existing. A plain `&` without quotes (`git status&pwnmarker`) did not inject because the argument is quoted. Evidence: console log in this run (`adv/rw.json`).
- **AF-3 (P2)** Ledger parser: an Open Items heading with its ID removed is silently dropped when the header count is adjusted; a duplicated open ID is accepted with no ambiguity notice. Pre-existing (base identical). Conflicts with Phase 2's verification claim that ambiguous IDs refuse closure (closure is still refused only because the items stay open).
- **AF-4 (P3)** Copilot `verify-package-contents.js` (new, copied from cursor) accepts `out/credentials.json`; pattern list covers `.env`, `auth.json`, `secret*`, `.pem`, `.key` only.
- **AF-5 (P3)** provenance-ledger `.ps1` writes local-time epochs (7 h skew vs `.sh`). Pre-existing.
- **AF-6 (P3)** enumerate-models: invalid id exits 2 in `.sh`, 0 in `.ps1`. Pre-existing.

Rejected (observed refutations): unknown markers ACCEPTED/CHECKED/lowercase `resolved` do not resolve an item (status route; only route is the parser); MIGRATED to a patch target refused; stub/truncated destination reuse refused (26 real-helper fixtures); NUL path refused in jq/Python-free bash and PowerShell routes; malformed JSON to all exercised hooks exits 0 without crash.

Needs live validation: none. Untested: Kimi/Qwen/Gemini CLI live hosts; macOS/Linux sibling runs; concurrent mixed sh/ps1 writers.

**Verdict: CONDITIONAL PASS** - no new regression introduced by the plan was confirmed; two P1 pre-existing injection paths remain in code this plan rewrote.

## 7. Code-vs-plan convergence ([[implementation-convergence]])

Findings table (the skill's append-only write to the plan was NOT performed: the caller forbids modifying the worktree, so this is the presented summary only):

| id | gap type | severity | source-ref | evidence | remaining work |
|---|---|---|---|---|---|
| CV-1 | contradicts | MEDIUM | Plan "Out of scope: Installer changes", T013 "Do not edit either installer", 8.5 "do not edit installers" | `scripts/installer.sh` +108/-?, `installer.ps1` +142 lines in diff vs base (Phase 7 stage leak, workspace output, WN-44 help text) plus further uncommitted WN-30 edits | record explicit maintainer authority for installer edits or revert; not verified here whether such approval exists |
| CV-2 | partial | MEDIUM | Phase 2 Verification Expectation (ambiguous IDs, unknown rows refuse closure) | AF-3 | add duplicate-ID and ID-less-heading refusal or record residual |
| CV-3 | partial | MEDIUM | T040, 8.1-8.10 | T031-T040 unchecked; last-phase evidence in progress | expected; Phase 8 still running |
| CV-4 | partial | LOW | WN-45 scope (uncommitted) | AF-1/AF-2: helper fixed decoding but kept cmd metacharacter exposure | escape cmd metacharacters or avoid cmd for shims |
| CV-5 | unrequested | LOW | none | `README.md`, `guides/...` edits by other workers | review only |

Not converged; summary counts: 0 missing, 3 partial, 1 contradicts, 1 unrequested.

## 8. Goal-vs-plan sufficiency

| Question | Answer | Evidence | Change needed now | Owner |
|---|---|---|---|---|
| 1. What did implementing teach that the plan did not know? | Several fixed "quick" hook defects (BG-18, BG-19, BG-20, BG-21, WN-41..45) were discovered only by exercising real boundaries; the WN-45 helper surfaced a pre-existing cmd-injection class (AF-1/AF-2). Windows MAX_PATH and the edit guard affect disposable fixtures. | phase 4/7 evidence; rows 10, 16, 17; AF-1/2 | record AF-1/AF-2 as owned gaps | hooks owner |
| 2. What did the plan assume that turned out false? | (a) "Destination is the existing `docs/releases/v4/v4.14/known-gaps.md`": no such file on HEAD, base or origin/develop; `migrate` must create it. (b) Phase 2 expectation that ambiguous IDs refuse closure: parser accepts duplicates (AF-3). (c) Installer work out of scope: installers were edited. | `git ls-tree` output; rows 2; CV-1 | correct plan wording; disposition CV-1 | plan owner |
| 3. What would a Goal reader expect that no phase delivered? | Goal requires `MINOR COMPLETE` after release and archive; not yet delivered (92 open, `gaps.minor unmet`, `archive.minor unmet`). Expected at this stage. | row 1 | none now; post-release lifecycle | release owner |
| 4. What did the maintainer ask for that no task captured? | "Keep three serial guide-render legs, no pytest-xdist" is captured only in prose (Additional candidates paragraph, phase CI-impact notes), not as a task or check; no task line verifies it. | plan line 108; no T-line | add a verification line in 8.5/8.9 | CI owner |

## 9. NOT COVERED

- Row 4: migration dry-runs (owner [[known-gaps-tracker]] / minor driver) - requires the HMAC run record; not forgeable in a fixture.
- Rows 32-34: Phase 4 text/contract artifacts, Phase 7 integration fixes, WN-40 runtime and guide-leg shape - time budget ended by coordinator.
- [[accessibility-engineering]], [[hallmark-design]], [[browser-testing-with-devtools]]: not invoked.
- Hosted CI, macOS, Linux, real editors, accounts: unavailable by plan definition.
- Out-of-scope in-flight work per coordinator: WN-8-v41310, WN-30, the newer ledger closures and carry-forward blocks.

## 10. Environment bounds

Windows 11, Git Bash, Windows PowerShell 5.1, Python 3.12.10 (uv venvs 3.12.13), Node 24.13.0, npm 11.6.2, Chromium via Playwright, Docker (manylinux_2_28 offline for make), pip-audit 2.7.3 with live advisory query. All homes redirected to scratch; real `~/.nexus-hub` unchanged. No worktree file was modified by this pass.
