---
description: Orchestrate a comprehensive pre-release deep review by chaining known-gaps collection, health gates, dependency scan, docs/git hygiene, project validators, /analyze-codebase, /run-security-audit, /run-penetration-test --depth=deep, /review-codebase, a synthesis report, and /generate-plan. Centralizes every artifact under docs/<next-version>/review/.
---

# Run Deep Review

Run a comprehensive pre-release deep review of the current codebase. This is the command to run before a major or minor version jump: it chains the existing review, audit, and pentest commands together, layers in pre-release readiness checks (health gates, dependency CVEs, docs/git hygiene, project validators), synthesizes every finding into a single severity-ranked report, and ends by generating a remediation plan.

**This command vs the individual review commands**: `/analyze-codebase`, `/run-security-audit`, `/run-penetration-test`, and `/review-codebase` each cover one slice of code health. `/run-deep-review` runs all of them, plus the surrounding release-readiness checks, plus a deduplicated cross-phase synthesis with a GO / GO-WITH-CONDITIONS / NO-GO verdict. Use the individual commands during day-to-day development. Use this command before cutting a release.

**Scope**: Static analysis and command execution only. Tests are run, scanners are invoked, but no code is modified — `/run-security-audit` runs in report-only mode, and remediation goes into the generated plan rather than into the working tree.

**Expected runtime**: 30–90 minutes depending on codebase size and scanner availability. Print the full phase plan in Phase 0 so the user can interrupt before the long sub-command runs start.

---

## Phase 0: Resolve Scope, Version, and Output Directory

### 0.1 Parse Flags

Check whether the user supplied any of these optional flags:

- **`--scope <path>`**: Restrict every analysis-only sub-command (`/analyze-codebase`, `/run-security-audit`, `/run-penetration-test`, `/review-codebase`) to the specified path or glob. Note the restriction in `INDEX.md`. Health gates, dependency scan, and project validators always cover the whole repo regardless of `--scope`.
- **`--target-version <vX.Y.Z>`**: Override the auto-computed next-minor version. Useful when bumping major or patch instead of minor.
- **`--current-version <vX.Y.Z>`**: Override the auto-detected current version (rare; use only if version detection fails).
- **`--skip <phase-number>`**: Comma-separated list of phase numbers to skip (e.g. `--skip 3,4` skips dependency-scan and docs/git-hygiene). Phases 0, 10, 11, 12 (setup, synthesis, plan, index) cannot be skipped.

### 0.2 Detect Current Version

Try in this order, stop at the first that succeeds:

1. Most recent version heading in `CHANGELOG.md` (`## [1.0.0]` → `v1.0.0`). Skip `## [Unreleased]`.
2. Latest git tag: `git tag --sort=-v:refname | head -n 1`.
3. `package.json` `"version"`, `pyproject.toml` `[project] version`, `Cargo.toml` `[package] version`, or a root `VERSION` file.
4. Fallback `vUnknown` only on explicit user confirmation.

Show the detected version and the source it came from.

### 0.3 Compute Next Version

Default: bump **MINOR**, reset **PATCH** to 0.

| Current | Next (MINOR bump) |
|---|---|
| `v0.9.10` | `v0.10.0` |
| `v1.0.0` | `v1.1.0` |
| `v2.3.4` | `v2.4.0` |

If `--target-version` was supplied, use it verbatim (normalize to `v` prefix).

### 0.4 Confirm Output Directory

Show the user:

```
Detected current = vX.Y.Z (from CHANGELOG.md)
Computed next   = vX.(Y+1).0
Output dir      = docs/vX.(Y+1).0/review/

Press Enter to accept, or supply --target-version <vA.B.C> to override.
```

Create `docs/<next-version>/review/` if it does not already exist. If it exists and is non-empty, ask whether to overwrite, append-with-timestamp-suffix, or abort.

### 0.5 Print the Phase Plan

Before starting any phase, print the full ordered run plan and where each artifact will land. This is the user's last chance to interrupt before the long sub-command runs begin. Format:

```
Deep review plan for docs/<next-version>/review/:

  Phase 1  Known gaps           -> 00-known-gaps.md
  Phase 2  Health gates         -> 01-health-gates.md
  Phase 3  Dependency scan      -> 02-dependency-scan.md
  Phase 4  Docs + git hygiene   -> 03-docs-and-git-hygiene.md
  Phase 5  Project validators   -> 04-project-validators.md
  Phase 6  /analyze-codebase    -> 05-analysis.md
  Phase 7  /run-security-audit  -> 06-security-audit.md         [report-only]
  Phase 8  /run-penetration-test-> 07-penetration-test.md       [--depth=deep]
  Phase 9  /review-codebase     -> 08-code-review.md
  Phase 10 Synthesis            -> SYNTHESIS.md
  Phase 11 /generate-plan       -> ../plans/pre-release-deep-review-remediation.md
  Phase 12 Index                -> INDEX.md

Estimated runtime: 30-90 min. Press Enter to start, Ctrl-C to abort.
```

### 0.6 Always-Exclude List

Every phase that scans files must exclude:

- `node_modules/`, `vendor/`, `.venv/`, `.tox/`, `dist/`, `build/`, `out/`, `target/`
- Generated files (headers `// generated`, `# auto-generated`, `// Code generated by`)
- Lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `poetry.lock`, `Cargo.lock`, `go.sum`)
- Binary files
- The `docs/` directory itself (except for the known-gaps phase, which reads it)

---

## Severity Classification

All phases use the same P0–P3 scale, identical to `/review-codebase` and `/run-security-audit`, so findings compose cleanly in the synthesis.

| Level | Alias | Meaning | Required Action |
|-------|-------|---------|-----------------|
| P0 | CRITICAL | Ship-blocker. Security vulnerability with public exploit, data-loss bug, build failure, failing tests on main, exposed secret. | Fix before release. Becomes a release-blocker condition in `SYNTHESIS.md`. |
| P1 | HIGH | Logic error, missing critical test coverage, missing input validation, weak crypto, deferred phase that was supposed to ship this version, unaddressed P0/P1 from prior comparison report. | Fix before release or document as known limitation. |
| P2 | MEDIUM | Code smell, maintainability concern, missing security header, unpinned dependency, stale documentation, minor coverage gap. | Fix in current sprint or create a tracked follow-up. |
| P3 | LOW | Style, naming, opportunistic improvement, advisory finding. | Optional. |

---

## Phase 1: Known-Gaps Collection → `00-known-gaps.md`

Aggregate everything the project already knows about its own gaps. Each finding must cite a source (file path, line number or section, commit hash, issue number) so a reader can verify and act.

### 1.1 Sources to Scan

- **`CHANGELOG.md` `[Unreleased]` section**: extract everything between `## [Unreleased]` and the next `## [<version>]` heading. Empty or missing section is itself a P2 finding ("no Unreleased work documented since last release").
- **`docs/DEVLOG.md`** (if present): grep for "Lessons Learned", "Deferred", "Blocked", "Known Issue", "Workaround", "TODO". Capture the date, entry title, and the relevant paragraph.
- **`docs/<current-version>/plans/*.md`**: scan every plan file for phases marked `Deferred`, `Blocked`, `Pending`, prerequisites flagged as not met, and exit-checklist items still unchecked. Report the plan name, phase number, and why it is open.
- **`docs/<current-version>/comparison-*.md`** (if present): Section 9 (Security and Risk Assessment) and Section 10 (Adoption Plan) rows still tagged P0 or P1 and not yet shipped. Match against `[Unreleased]` and recent commits to determine "shipped".
- **`docs/v*/mcp-reverse-engineering-matrix.md`** (if present): rows whose status is not `done` or `shipped`. These are explicit architectural debt items.
- **Code annotations**: run `git grep -nE 'TODO|FIXME|HACK|XXX|BUG'` (or platform equivalent) excluding the always-exclude list. Bucket by file area. Cap at 50 most recent additions to keep the report readable; spill the rest into a collapsed appendix.
- **Project memory** (Claude Code only): scan `~/.claude/projects/<project-slug>/memory/*.md` for entries tagged `project` or `feedback` whose body mentions deferred work, blockers, or known issues. Cite the memory file name. Skip user-private entries.
- **GitHub issues** (only if `gh` CLI is authenticated and the repo has a remote): `gh issue list --label bug --label security --label tech-debt --label deferred --state open --limit 50`. Capture issue number, title, label, age.

### 1.2 Output Format

Write `docs/<next-version>/review/00-known-gaps.md` with:

```markdown
# Known Gaps — Pre-release deep review for <next-version>

**Generated**: <ISO 8601 timestamp>
**Current version**: <current>
**Source coverage**: CHANGELOG | DEVLOG | plans | comparisons | RE matrix | code annotations | memory | GitHub issues

## Summary
| Severity | Count |
|---|---|
| P0 | <n> |
| P1 | <n> |
| P2 | <n> |
| P3 | <n> |

## Findings
| # | Source | Location | Item | Why it's a gap | Severity |
|---|---|---|---|---|---|
| 1 | CHANGELOG.md `[Unreleased]` | line 12 | "Phase 5 deferred pending upstream blockers" | Phase 5 was scoped for v0.9.7 but was not shipped; upstream blockers (#31415, #17127) still open | P1 |
| 2 | docs/v1.0.0/plans/security-hardening-v100.md | Phase 11 exit checklist | Two items unchecked | Phase 11 marked complete in commit 66e3f86 but exit checklist incomplete | P2 |
| ... |

## Appendix: Full TODO/FIXME/HACK inventory
<collapsed list of all annotations beyond the top 50>
```

---

## Phase 2: Health Gates → `01-health-gates.md`

Run the project's standard CI gates and record outcomes. The goal is a binary pass/fail per gate, with enough detail to triage failures without re-running.

### 2.1 Stack Detection

Detect the stack from manifest presence:

- `pyproject.toml` or `requirements.txt` → Python
- `package.json` → Node (Bun / pnpm / npm / yarn — pick whichever lockfile is present)
- `go.mod` → Go
- `Cargo.toml` → Rust
- `pom.xml` / `build.gradle` → Java
- `*.csproj` / `*.sln` → C#

Multi-stack repos: run gates for every detected stack and label results clearly.

### 2.2 Gates to Run (per stack)

| Gate | Python | Node | Go | Rust |
|---|---|---|---|---|
| Tests + coverage | `pytest --cov=. --cov-report=term-missing -q` | `npm test -- --coverage` (or `pnpm`/`yarn`) | `go test -race -cover ./...` | `cargo test` (+ `cargo tarpaulin` if installed) |
| Lint | `ruff check .` | `eslint .` | `golangci-lint run` | `cargo clippy --all-targets -- -D warnings` |
| Format check | `ruff format --check .` | `prettier --check .` | `gofmt -l .` (any output = failure) | `cargo fmt --check` |
| Build | `python -m build` (if `pyproject.toml` declares a backend) | `npm run build` (only if script defined) | `go build ./...` | `cargo build --release` |

Skip a gate if the tool is not installed, but record the skip explicitly.

### 2.3 Coverage Threshold

Default threshold: **80%** line coverage (matches the project's testing rules in `~/.claude/rules/<lang>/testing.md`). If actual coverage is below threshold, mark P1. If coverage cannot be measured, mark P2.

### 2.4 Output Format

```markdown
# Health Gates — Pre-release deep review for <next-version>

| Gate | Stack | Command | Result | Duration | Severity |
|---|---|---|---|---|---|
| Tests | Python | pytest --cov=. ... | PASS (88/88, coverage 87%) | 12.3s | OK |
| Lint  | Python | ruff check . | FAIL (3 errors) | 0.8s | P1 |
| Build | Python | python -m build | PASS | 4.2s | OK |
| ... |

## Failure detail
### ruff check (P1)
<excerpted error output, capped at ~40 lines per failing gate>

## Coverage detail
<per-file coverage table sorted ascending>
```

---

## Phase 3: Dependency Vulnerability Scan → `02-dependency-scan.md`

Run language-native CVE scanners against the resolved dependency graph. This complements `/run-security-audit` (which audits source code) by surfacing transitive CVEs that static source review cannot see.

### 3.1 Scanners (run only what applies)

| Stack | Primary | Fallback |
|---|---|---|
| Python | `pip-audit -r requirements.txt` (or `pip-audit` against installed env) | `safety check --json` |
| Node | `npm audit --json` (or `pnpm audit --json` / `yarn audit --json`) | `osv-scanner -r .` |
| Go | `govulncheck ./...` | — |
| Rust | `cargo audit --json` | — |
| Container | `trivy fs .` if Dockerfile/Containerfile present | `docker scan` |
| Generic | `osv-scanner -r .` (covers all of the above as a cross-check) | — |

Skip scanners whose binary is not installed; record the skip.

### 3.2 Output Format

```markdown
# Dependency Vulnerability Scan — Pre-release deep review for <next-version>

| Severity | Count | Direct | Transitive |
|---|---|---|---|
| Critical | <n> | <n> | <n> |
| High     | <n> | <n> | <n> |
| Medium   | <n> | <n> | <n> |
| Low      | <n> | <n> | <n> |

## Findings
| Package | Installed | Fixed in | CVE | CVSS | Direct? | Exploit? | Advisory |
|---|---|---|---|---|---|---|---|
| ... |

## Skipped scanners
<list with reason: "binary not installed", "stack not present", etc.>
```

Map CVSS to project severity scale: 9.0+ → P0, 7.0–8.9 → P1, 4.0–6.9 → P2, < 4.0 → P3.

---

## Phase 4: Documentation + Git Hygiene → `03-docs-and-git-hygiene.md`

### 4.1 Broken Links

Extract every Markdown link from `README.md`, `CONTRIBUTING.md`, and `docs/**/*.md`. For each:

- Local link (`./foo.md`, `../bar.md`, `path/to/file.md`): verify the target file exists.
- Anchor link (`#section`): verify the target file contains a heading or anchor that matches.
- HTTP(S) link: HEAD request with 5s timeout; record non-200 responses but do not fail the phase on transient timeouts (mark P3 advisory).

### 4.2 CHANGELOG vs Commits

- `git log --oneline <last-tag>..HEAD` — list every commit since the last release tag.
- Compare each commit subject to the body of `## [Unreleased]` in `CHANGELOG.md`.
- Report commits that are **not** represented in `[Unreleased]` (potential missing release notes). Mark P1 if any commit since last tag is missing from `[Unreleased]`.

### 4.3 Working Tree State

- `git status --porcelain` — uncommitted changes (P0 if any are present at release time).
- Untracked files outside `.gitignore`'d paths (P2).
- `git branch --no-merged main` — local branches not merged into main (P3 advisory; user may have intentional WIP).
- Branches with no upstream (`git for-each-ref --format='%(refname:short) %(upstream)' refs/heads/`) — stale local branches (P3).

### 4.4 API Doc Staleness

Scan public function/class signatures for missing or `TBD`/`TODO` docstrings. Per-language patterns:

- Python: public functions/classes (no leading underscore) without `"""docstring"""`.
- TypeScript/JavaScript: exported symbols without preceding JSDoc block.
- Go: exported identifiers without preceding `// Comment`.
- Rust: `pub` items without `///` doc comment.

Cap at 50 most-affected files; spill the rest into an appendix.

### 4.5 Release Notes Preview

Generate a Keep-a-Changelog formatted preview of `[Unreleased]` (Added / Changed / Deprecated / Removed / Fixed / Security buckets). Embed it in the report.

### 4.6 Output Format

```markdown
# Documentation + Git Hygiene — Pre-release deep review for <next-version>

## Summary
| Check | Status | Severity |
|---|---|---|
| Broken local links | <n found> | P1/P2 |
| Broken external links | <n found> | P3 |
| Commits not in CHANGELOG | <n> | P1 |
| Uncommitted changes | <n files> | P0 |
| Stale branches | <n> | P3 |
| Missing docstrings | <n public symbols> | P2 |

## Findings (detail per check)
...

## Release Notes Preview
### Added
- ...
### Changed
- ...
```

---

## Phase 5: Project-Specific Validators → `04-project-validators.md`

Auto-detect and execute repo-defined validators. Capture stdout, stderr, exit code, and duration.

### 5.1 Detection

- **Makefile**: parse with `make -pn 2>/dev/null | grep -E '^(validate|lint|test|check|ci):'` and run the matching targets in order: `validate`, `lint`, `test`, `check`, `ci`. **For DevAI-Hub specifically: run `make validate`, `make lint`, `make test` regardless of detection.**
- **`package.json` scripts**: parse `"scripts"` and run `validate`, `lint`, `test`, `check`, `ci` if defined.
- **`tox.ini`**: run `tox` (all envs) if present.
- **Pre-commit**: run `pre-commit run --all-files` if `.pre-commit-config.yaml` is present.

### 5.2 Failure Handling

Each validator runs independently. A failure does not stop subsequent validators; record all results.

### 5.3 Output Format

```markdown
# Project-Specific Validators — Pre-release deep review for <next-version>

| Validator | Command | Exit | Duration | Severity |
|---|---|---|---|---|
| make validate | make validate | 0 | 1.2s | OK |
| make lint     | make lint     | 1 | 3.4s | P1 |
| make test     | make test     | 0 | 8.7s | OK |
| pre-commit    | pre-commit run --all-files | 0 | 6.1s | OK |

## Failure detail
### make lint (P1)
<excerpted output, ~40 lines>
```

Map exit codes: 0 → OK, non-zero → P1 (or P0 if stderr indicates a security or build-blocker issue).

---

## Phase 6: `/analyze-codebase` → `05-analysis.md`

Invoke `/analyze-codebase`. The sub-command writes to `docs/<current-version>/analysis.md` based on its own version detection.

After the sub-command completes:

```bash
mv docs/<current-version>/analysis.md docs/<next-version>/review/05-analysis.md
```

If `docs/<current-version>/analysis.md` already existed and was overwritten, note this in `INDEX.md` under "regenerated artifacts".

If `--scope` was passed to `/run-deep-review`, propagate it into the prompt to `/analyze-codebase` (e.g. "Analyze only `extensions/devai-code-search/` per the supplied scope").

---

## Phase 7: `/run-security-audit` → `06-security-audit.md`

Invoke with explicit output redirect and **no** `--fix`:

```
/run-security-audit --output docs/<next-version>/review/06-security-audit.md
```

If `--scope` was passed to `/run-deep-review`, append `--scope <path>` to the sub-command invocation.

**Why no `--fix`**: this is a pre-release snapshot, not a remediation loop. Findings flow into the synthesis and into the `/generate-plan` output, where the user can review them before any code is touched.

---

## Phase 8: `/run-penetration-test --depth=deep` → `07-penetration-test.md`

Invoke with deep coverage:

```
/run-penetration-test --depth=deep --output docs/<next-version>/review/07-penetration-test.md
```

If `--scope` was passed, append `--scope <path>`.

**Why `--depth=deep`**: this is a pre-release review, so the ~20% additional cost is justified to populate the WSTG-BUSL row (business-logic vulnerabilities) and the advanced-attack rows of the WSTG Coverage Matrix. A standard 5-hunter run leaves those rows marked "Not covered".

After completion, verify the WSTG-BUSL row is populated in the output. If it is empty, flag a P2 finding ("pentest deep mode produced no business-logic findings — confirm the 6th hunter actually ran") and note it in `SYNTHESIS.md`.

---

## Phase 9: `/review-codebase` → `08-code-review.md`

Invoke `/review-codebase` (full-codebase mode, not git-changes mode). The sub-command writes to `docs/<current-version>/review.md`.

After the sub-command completes:

```bash
mv docs/<current-version>/review.md docs/<next-version>/review/08-code-review.md
```

If `--scope` was passed to `/run-deep-review`, propagate it into the prompt.

---

## Phase 10: Synthesis → `SYNTHESIS.md`

Aggregate every artifact produced in Phases 1–9 into a single deduplicated report. Read each artifact in turn, extract findings into a working set, deduplicate, then write `SYNTHESIS.md` in one pass.

### 10.1 Pre-Synthesis Collection

Read every artifact under `docs/<next-version>/review/00-*.md` through `08-*.md`. Build an internal working set of findings, each with:

- **id**: deterministic hash of (file_or_location + short_description), so the same finding from two phases collapses to one row
- **phase_origin(s)**: which artifact(s) reported it
- **severity**: P0/P1/P2/P3 (use the **highest** severity if multiple phases reported the same finding at different levels)
- **location**: file path + line range, or section reference for non-code findings
- **description**: one-sentence summary
- **recommended_fix**: one-sentence proposed action
- **effort_estimate**: S / M / L (small <1 day, medium 1–3 days, large >3 days)
- **cross-references**: links back to the originating artifact(s)

### 10.2 Synthesis Structure

Write `docs/<next-version>/review/SYNTHESIS.md` with these sections in order:

```markdown
# Pre-release Deep Review Synthesis — <next-version>

**Generated**: <ISO 8601 timestamp>
**Current version**: <current>
**Target version**: <next>
**Scope**: <full | path/glob>
**Sub-command runs**: <list of which phases ran successfully and which were skipped>

---

## 1. Executive Summary

| Severity | Count |
|---|---|
| P0 | <n> |
| P1 | <n> |
| P2 | <n> |
| P3 | <n> |
| **Total** | <n> |

**Release-readiness verdict**: GO | GO-WITH-CONDITIONS | NO-GO

**Verdict rationale**: <2-4 sentences>

**Top 10 most critical findings**: <numbered list with one-line summary + link to the row in section 3>

**Ship-blockers (all P0 findings)**: <numbered list>

---

## 2. Risk Overlay (STRIDE)

Roll up findings from `06-security-audit.md` and `07-penetration-test.md` into a STRIDE table:

| STRIDE category | Count | Highest severity | Top examples |
|---|---|---|---|
| Spoofing | ... |
| Tampering | ... |
| Repudiation | ... |
| Information Disclosure | ... |
| Denial of Service | ... |
| Elevation of Privilege | ... |

---

## 3. Cross-Phase Finding Matrix

The deduplicated working set, sorted by severity descending then by phase origin:

| # | Severity | Phase(s) | Location | Description | Recommended fix | Effort | Source |
|---|---|---|---|---|---|---|---|
| 1 | P0 | known-gaps + security-audit | extensions/devai-code-search/server.py:142 | Hardcoded fallback API key in error path | Move to env var with required-at-startup check | S | [00](00-known-gaps.md), [06](06-security-audit.md) |
| 2 | P1 | dependency-scan | requirements.txt: cryptography==41.0.0 | CVE-2024-XXXX (CVSS 8.1, exploit available) | Bump to >=42.0.4 | S | [02](02-dependency-scan.md) |
| ... |

---

## 4. Coverage Gaps

Coverage findings from Phase 2 (health gates) cross-referenced against architecture findings from Phase 6 (`/analyze-codebase`) and review findings from Phase 9 (`/review-codebase`). Highlights modules with both low coverage and high architectural significance.

| Module | Coverage % | Significance | Suggested tests |
|---|---|---|---|

---

## 5. Known-Gap Resolution Status

For every finding from `00-known-gaps.md`, indicate whether subsequent phases confirmed it still exists, partially addressed it, or proved it resolved.

| Original gap | Status | Evidence |
|---|---|---|
| Phase 5 deferred (CHANGELOG) | Still open | No commits referencing the upstream blocker issues since v1.0.0 |
| ... |

---

## 6. Release-Readiness Conditions

If verdict is GO-WITH-CONDITIONS or NO-GO, list the explicit conditions that must be met before release. Each condition cites the finding rows in section 3.

1. **All P0 findings closed**: rows 1, 4, 7
2. **Coverage >= 80% in `extensions/devai-code-search/`**: rows 12, 13
3. ...
```

### 10.3 Quality Checks Before Writing

Before writing `SYNTHESIS.md`:

- Verify every artifact in `docs/<next-version>/review/` was actually read (no silent skips).
- Verify no finding was double-counted (the dedup step actually ran).
- Verify the verdict logic: NO-GO requires at least one P0; GO-WITH-CONDITIONS requires at least one P1; otherwise GO.
- Verify every cross-reference link in the matrix points to an existing artifact.

---

## Phase 11: `/generate-plan` from Synthesis

Invoke `/generate-plan` with the synthesis as input:

```
/generate-plan docs/<next-version>/review/SYNTHESIS.md
```

`/generate-plan` Step 0.5 (From-comparison mode) currently triggers on `comparison-*.md` filenames. Since `SYNTHESIS.md` is not a comparison report, expect Step 0.5 to skip and the standard discovery interview to begin. Pre-seed the answers from the synthesis content rather than asking the user from scratch:

| Discovery question | Pre-seeded answer |
|---|---|
| Plan type | Refactor or technical-debt reduction |
| Target version | `<next-version>` |
| One-sentence scope | "Address findings from the pre-release deep review for `<next-version>`." |
| Slug | `pre-release-deep-review-remediation` |
| Phases | One phase per severity bucket: P0 first, P1 second, P2 third, P3 last (or skipped if user wants minimal scope) |
| Sub-tasks per phase | One sub-task per row of the cross-phase finding matrix at that severity |

If `/generate-plan` insists on the interactive interview, walk through it answering with the pre-seeded values. Final output: `docs/<next-version>/plans/pre-release-deep-review-remediation.md`.

---

## Phase 12: Index → `INDEX.md`

Write the entry-point document last so it can include final counts and the verdict.

### 12.1 Structure

```markdown
# Pre-release Deep Review — <next-version>

**Generated**: <ISO 8601 timestamp>
**Current version**: <current>
**Target version**: <next>
**Scope**: <full | path/glob>
**Verdict**: GO | GO-WITH-CONDITIONS | NO-GO  *(from SYNTHESIS.md section 1)*

## Artifacts

| # | Phase | Artifact | Findings (P0/P1/P2/P3) |
|---|---|---|---|
| 0 | Known gaps | [00-known-gaps.md](00-known-gaps.md) | 0/2/3/1 |
| 1 | Health gates | [01-health-gates.md](01-health-gates.md) | 0/1/0/0 |
| 2 | Dependency scan | [02-dependency-scan.md](02-dependency-scan.md) | 1/3/4/0 |
| 3 | Docs + git hygiene | [03-docs-and-git-hygiene.md](03-docs-and-git-hygiene.md) | 0/1/2/5 |
| 4 | Project validators | [04-project-validators.md](04-project-validators.md) | 0/0/1/0 |
| 5 | /analyze-codebase | [05-analysis.md](05-analysis.md) | n/a (informational) |
| 6 | /run-security-audit | [06-security-audit.md](06-security-audit.md) | 1/2/3/0 |
| 7 | /run-penetration-test | [07-penetration-test.md](07-penetration-test.md) | 0/4/2/1 |
| 8 | /review-codebase | [08-code-review.md](08-code-review.md) | 0/3/8/12 |
| - | Synthesis | [SYNTHESIS.md](SYNTHESIS.md) | 2/16/23/19 (deduplicated) |
| - | Remediation plan | [../plans/pre-release-deep-review-remediation.md](../plans/pre-release-deep-review-remediation.md) | — |

## Skipped Phases

<list any phases skipped via --skip flag, or any sub-command that errored, with reason>

## Regenerated Artifacts

<list any pre-existing files that were overwritten by Phase 6 or Phase 9>

## Next Steps

1. Begin executing Phase 1 (P0) of the remediation plan.
2. View the synthesis report (`SYNTHESIS.md`).
3. Re-run a specific sub-phase (1-9). Provide the phase number.
4. Bump the version now (`/update-version`).
5. Exit.
```

### 12.2 Print Summary to Terminal

After writing `INDEX.md`, print a one-screen summary to the terminal:

```
Deep review complete for <next-version>.
  Verdict: <verdict>
  P0 findings: <n>  (ship-blockers)
  P1 findings: <n>
  P2 findings: <n>
  P3 findings: <n>

  Synthesis:        docs/<next>/review/SYNTHESIS.md
  Remediation plan: docs/<next>/plans/pre-release-deep-review-remediation.md
  Full bundle:      docs/<next>/review/

Next steps:
  1. Begin Phase 1 of remediation plan
  2. View synthesis
  3. Re-run a sub-phase
  4. Bump version (/update-version)
  5. Exit
```

---

## Exit Checklist

Before considering the deep review complete:

- [ ] `docs/<next-version>/review/` exists and contains `INDEX.md`, `SYNTHESIS.md`, and at least the artifacts for every phase that was not skipped (`00-known-gaps.md` through `08-code-review.md`).
- [ ] `docs/<next-version>/plans/pre-release-deep-review-remediation.md` exists.
- [ ] `INDEX.md` finding counts sum correctly when deduplicated against `SYNTHESIS.md`.
- [ ] No source files were modified during the run (`git status --porcelain` shows only the new `docs/` artifacts).
- [ ] `SYNTHESIS.md` verdict is consistent with finding counts (NO-GO requires ≥1 P0, GO-WITH-CONDITIONS requires ≥1 P1, GO otherwise).
- [ ] Every cross-reference link in `SYNTHESIS.md` and `INDEX.md` resolves.
- [ ] If a sub-command failed, the failure is documented in `INDEX.md` "Skipped Phases" with a reason.

---

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We can skip the known-gaps phase, the team knows the open items" | Tribal knowledge does not survive a release window. The known-gaps file makes the gaps citable and reviewable by anyone, not just the people in the room. |
| "Health gates are already green in CI, we don't need to re-run them" | CI runs against the merge target, not the working tree. A pre-release deep review must verify the actual release artifact, including any uncommitted local changes. |
| "We just ran a security audit last week, skip it" | Dependency CVE databases update daily and the codebase has likely changed since. The 5-minute audit re-run is cheap compared to shipping a known CVE. |
| "Pentest --depth=deep is too expensive for routine use" | This is not routine — it runs once per minor/major release. The 20% additional cost buys business-logic and advanced-attack coverage that the standard pentest skips, which is exactly the coverage you need before shipping. |
| "The synthesis is redundant with the individual reports" | The synthesis is where deduplication happens. The same CVE will appear in both `02-dependency-scan.md` and `06-security-audit.md`; without the synthesis, the user double-counts findings and over-estimates risk. |
| "We can generate the remediation plan manually from the synthesis" | `/generate-plan` produces self-contained executable prompts for each sub-task that can be run in future sessions. Hand-rolling the plan loses that property. |

---

## Notes for Multi-Platform Distribution

This command is distributed by `scripts/installer.sh` and `scripts/installer.ps1` to:

- Claude Code: `~/.claude/commands/run-deep-review.md` (slash command)
- Gemini / Antigravity: `~/.gemini/workflows/run-deep-review.md` (workflow)
- Codex: `~/.codex/prompts/run-deep-review.md` (prompt)

Cursor, OpenCode, and Copilot users see `/run-deep-review` only via the shared `AGENTS.md` surface; they invoke the orchestration manually by referencing this file or the underlying sub-commands. Document this caveat in any release notes that mention the new command.
