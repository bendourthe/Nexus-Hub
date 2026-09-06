# Session History: v2.1.0 Phase 9 - P3 Polish (Methodology Essay + Devcontainer + Markdownlint Config + Installer Test)

**Date**: 2026-05-20
**Scope**: Phase 9 of [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md)
**Outcome**: Four P3-polish artifacts shipped against the v2.1.0 baseline rather than deferred to a v2.1.x patch: a 2679-word Spec-Driven Development methodology essay at `docs/archive/v2/v2.1/spec-driven-methodology.md`; a `.devcontainer/` scaffold with `devcontainer.json` and `post-create.sh`; an executable markdownlint config at `catalog/style-guides/markdownlint-cli2.jsonc` paired with a `## Automated enforcement` section in `catalog/style-guides/markdown.md`; and a `tests/installer/` pytest suite (`test_registrar_path_traversal.py` + `_path_safety.py`) with 19 assertions codifying the installer's path-resolution invariant. One DEVIATION recorded against the plan's Phase 9.4 "no Makefile change needed" assertion: the conditional `if [ -d tests ]; then python -m pytest -q tests; fi` line was appended to the `test:` target so the new suite runs alongside the extension tests. No new skills, commands, or templates; no `data/` registry changes. All verification gates pass: bundle audit 0 errors / 0 warnings across 210 bundles, 19/19 installer tests, 96 extension tests unchanged.
**Plan reference**: [docs/archives/v2/v2.1/plans/adoption-spec-kit.md](../../plans/adoption-spec-kit.md) Phase 9
**Source comparison**: [docs/archives/v2/v2.0/comparison-spec-kit.md](../../../v2.0.0/comparison-spec-kit.md)

## Goal recap

Close the four P3-polish items from the comparison report that were marked as candidates for v2.1.x patches in the plan's Phase 9 scope. These items are not catalog-distribution changes -- the methodology essay is repo-internal documentation, the devcontainer is contributor scaffolding (never copied to user install targets), the markdownlint JSONC is downstream-project tooling, and the installer test is a CI-side regression guard. Because none of the four items adds outbound calls, new skills, new commands, or new templates, the plan classified them as P3 (low-priority polish) rather than P1 / P2 (core spec-kit adoption). The phase is skill-native per the MCP Registry Policy decision tree -- no code review surface beyond the test file itself.

## Chronology by sub-task

### Sub-task 9.1 - Author Spec-Driven Methodology essay

Wrote `docs/archive/v2/v2.1/spec-driven-methodology.md` as a fresh 8-section essay rather than paraphrasing upstream text, per the plan's explicit instruction. The eight sections are:

1. **The Power Inversion** -- frames the historical asymmetry (code is authoritative, specs decay) and the v2.1.0 proposition (the spec is the source of truth, code is the artifact the spec compiles to). Explicit anchoring to the v2.1.0 command surface (`/constitution`, `/clarify-spec`, `/analyze-spec`, `/generate-plan --specs-layout`, `/tasks-to-issues`) so the reader can map each abstract claim to a concrete invocation.
2. **The Nexus-Hub SDD Workflow** -- seven-station chain (constitution -> specify -> clarify -> plan -> tasks -> analyze -> implement) with one sentence per station naming the command or template, the artifact it produces, and the gate it enforces.
3. **Why Now** -- three independent pressures (AI capability threshold, software complexity compounding, documentation-cycle lag) each framed from the Nexus-Hub perspective (the harness amplifies the developer; the developer's role shifts from "type the code" to "make the specification crisp enough that the code follows mechanically").
4. **Core Principles** -- six principles (specs as lingua franca, executable specs, continuous refinement, research-driven context, bidirectional feedback, branching for exploration) each tied to a catalog mechanism (FR-### / SC-### join keys, the Clarifications session log, the `context-engineering` / `context-manager` / `known-gaps-tracker` skills, the `--specs-layout` flag).
5. **Implementation Approaches** -- three approaches scaled to change size (tiny: skip spec; medium: lightweight flow with `docs/<version>/plans/<slug>.md`; large: full flow with `specs/<NNN>-<slug>/`). Notes that the constitution can mandate which approach applies above a complexity threshold.
6. **Template-Driven Quality** -- explains the 3-marker hard limit, the FR-### / SC-### IDs as the analyzer's data model, the P1 / P2 / P3 + Independent Test discipline as the MVP rule, and the spec-quality-checklist as "unit tests for English".
7. **Pitfalls and Anti-Patterns** -- five named failure modes (over-specifying the trivial, hiding behind the gate, forgetting that constitutions are versioned, treating the analyzer as a linter, spec drift in long-running features) plus a sixth on conflating skills with commands.
8. **Closing** -- two-sentence summation that frames the gate as "is the specification crisp enough that someone other than me could turn it into the right code".

Final word count: 2679 words (within the 2500-3500 plan target). A `## Related artifacts` block at the end cross-links to the spec template, constitution template, spec-quality-checklist, the v2.1.0 commands, the comparison report, and the plan itself. No upstream attribution leaks: the essay references "the SDD literature" and "the catalog" without naming spec-kit, github/spec-kit, or any specific upstream file path. The Reverse-Engineering Attribution Rule is observed.

A `## Methodology essay` block was added at the end of `catalog/skills/developer-experience/spec-driven-development/SKILL.md` (after the existing `## Related Skills` section) with a single-paragraph pointer to the essay covering its eight sections at a glance. The reverse link from essay to skill already exists in the `## Related artifacts` block of the essay.

### Sub-task 9.2 - Add `.devcontainer/` with devcontainer.json and post-create.sh

Created `.devcontainer/devcontainer.json` declaring:

- **Base image**: `mcr.microsoft.com/devcontainers/python:1-3.11-bookworm` (Python 3.11 floor matches the catalog's pyproject.toml expectation; Bookworm gives apt access to gh as a safety-net path)
- **Features**: `ghcr.io/devcontainers/features/github-cli:1` (pre-installed gh) + `ghcr.io/devcontainers/features/node:1` LTS (npm needed for the Claude Code CLI install)
- **VS Code extensions**: `ms-python.python`, `ms-python.vscode-pylance`, `yzhang.markdown-all-in-one`, `DavidAnson.vscode-markdownlint` (pairs with the new JSONC config from 9.3), `timonwong.shellcheck`, `tamasfe.even-better-toml`
- **postCreateCommand**: `bash .devcontainer/post-create.sh`
- **remoteUser**: `vscode`
- **containerEnv**: `NEXUS_HUB_DEVCONTAINER=1` (a sentinel future hooks can branch on)

Created `.devcontainer/post-create.sh` with `set -euo pipefail` and an idempotent four-function install flow:

1. `install_python_tooling` -- `pip install --quiet --upgrade pip && pip install --quiet pytest ruff`. Warns on partial failure but does not abort the rest of the setup.
2. `install_gh` -- `command -v gh` guard; on apt-based systems, runs the canonical apt-based gh installation recipe (keyring + sources.list.d). Mostly a safety net because the devcontainer feature already installs gh.
3. `install_claude_code` -- `command -v claude` guard; `npm install -g @anthropic-ai/claude-code` on success path. Falls back to a warning if npm is unavailable.
4. The closing `main()` block echoes a four-step "next steps" message (authenticate gh, authenticate claude, run installer, run validate) so the contributor knows what to do first.

`bash -n .devcontainer/post-create.sh` parses cleanly. `python -c "import json; json.load(open('.devcontainer/devcontainer.json'))"` parses cleanly.

The README `## Development setup` section was inserted between `## Manual setup` and `## Featured Skills` with a single paragraph linking to `.devcontainer/` and explaining that the devcontainer is opt-in (the Quick Start above does not require it).

### Sub-task 9.3 - Ship `catalog/style-guides/markdownlint-cli2.jsonc`

Created `catalog/style-guides/markdownlint-cli2.jsonc` with 21 rule overrides aligned to the existing prose guide at `catalog/style-guides/markdown.md`:

- **Enforced**: MD003 (atx headings), MD004 (dash bullets), MD007 (4-space nested indent), MD022 (blank lines around headings), MD031 (blank lines around code blocks), MD032 (blank lines around lists), MD040 (fenced code-block language required), MD046 (fenced code-block style), MD048 (backtick code-fence style), MD049 (asterisk emphasis), MD050 (asterisk strong)
- **Disabled**: MD013 (line length -- catalog Markdown writes each paragraph as a single continuous line by rule), MD034 (bare URLs -- common in code-block contexts), MD036 (emphasis as heading -- catalog uses bold-prefixed lines as table-card titles)
- **Tuned**: MD024 set to `siblings_only` (repeated headings allowed at different nesting depths); MD025 `front_matter_title: ""` (suppresses the title-clash warning on skills with `name:` frontmatter); MD026 trailing-punctuation set to `.,;:` (allows `?` and `!`); MD029 ordered-list style set to `ordered` (1. 2. 3.); MD033 opened to the catalog's actual inline-HTML tag set (`<details>`, `<sub>`, `<kbd>`, `<img>`, `<br>`, plus a few more); MD041 first-line check loosened with a regex that recognizes skill `name:` frontmatter
- **Globs**: `**/*.md` and `**/*.markdown`
- **Ignores**: `node_modules/`, `.venv/`, `venv/`, `.tox/`, `**/CHANGELOG.md` (long historical document), `docs/archive/**`, `docs/**/development/history/**` (immutable session-history files)

JSONC inline comments document each rule decision. The config validates after a comment-strip pass: `python -c "import re, json; src = open(...).read(); stripped = re.sub(r'//[^\\n]*$', '', src, flags=re.M); stripped = re.sub(r'/\\*[\\s\\S]*?\\*/', '', stripped); data = json.loads(stripped)"` returns 21 rules under `config`, plus `globs` and `ignores`.

Confirmed the installer's `install_templates` function at `scripts/installer.sh:1474` already calls `safe_folder_copy "$repo_root/catalog/style-guides" "$nexus_home/style-guides"`. No installer edit needed for the new JSONC file -- the recursive copy primitive handles it. The PowerShell installer follows the same pattern via `Safe-Folder-Copy`.

Added a new `## Automated enforcement (markdownlint-cli2)` section to `catalog/style-guides/markdown.md` (between the existing `## Quick Reference Card` and `## Verification`) with the three-step downstream-project recipe (`cp ~/.nexus-hub/style-guides/markdownlint-cli2.jsonc .markdownlint-cli2.jsonc`, `npx markdownlint-cli2 "**/*.md"`, optional CI / pre-commit wiring). The section explicitly notes the MD013 and MD036 disables as deliberate.

### Sub-task 9.4 - Add tests/installer/test_registrar_path_traversal.py

The plan threat-modeled the installer's input vectors: skill / command / template names come from the controlled catalog tree, target install root comes from the user. The realistic risk is a malicious contributor adding a directory named `../etc/passwd` to `catalog/skills/`. The bash installer's `safe_folder_copy` relies on `realpath` collapsing `..` before any write; the PowerShell installer uses `Resolve-Path`. Both are equivalent to `pathlib.Path.resolve()` in Python.

Created two new files under `tests/installer/`:

- **`__init__.py`** -- empty (pytest's package-discovery anchor)
- **`_path_safety.py`** -- a small helper module exposing `PathTraversalError`, `resolve_under(target_root, candidate)`, and `is_safe_candidate(target_root, candidate)`. The helper does pure path math (no filesystem touches) and codifies the same invariant the installer scripts rely on:
    - rejects None, non-string, empty, or whitespace-only candidates
    - rejects candidates containing null bytes (`\x00`)
    - rejects UNC paths (`\\\\server\\share` or `//server/share`)
    - rejects absolute paths (`/etc/passwd`, `C:\\Windows`, drive-letter forms)
    - joins the candidate under the resolved target root and asserts `.relative_to(root)` succeeds; raises `PathTraversalError` if the resolved path escapes the root

- **`test_registrar_path_traversal.py`** -- pytest suite with 19 assertions in 5 test classes:
    - `TestRejectMaliciousNames` (6): `../etc/passwd`, `skills/../../../etc/passwd`, `/etc/passwd`, `foo\x00bar`, `\\\\server\\share\\evil`, `//server/share/evil`
    - `TestRejectWindowsSpecificAbsolutePaths` (2): `C:\\Windows\\System32\\evil`, `\\Windows\\System32\\evil` -- intentionally tested on every platform so a Linux-committed catalog cannot become exploitable on Windows
    - `TestRejectMalformedInputs` (4): empty, whitespace-only, None, non-string
    - `TestAcceptLegitimateNames` (4): `spec-driven-development`, `developer-experience/spec-driven-development`, `workflow/project-constitution/SKILL.md`, `style-guides/markdownlint-cli2.jsonc`
    - `TestIsSafeCandidate` (3): boolean wrapper sanity checks

Test run: `python -m pytest tests/installer -q` returns `19 passed in 0.11s` on the Windows host.

A `pytest` fixture provides each test with a throwaway `install_root` under `tmp_path / "nexus-hub-install"` so the tests do not interfere with each other.

**DEVIATION**: the plan's Phase 9.4 prompt asserted "no Makefile change should be needed; pytest's `tests/installer/` is auto-discovered". This is incorrect for the Nexus-Hub Makefile -- `make test` runs three explicit `cd extensions/<dir> && python -m pytest -q` invocations rather than discovering pytest at the repo root. The minimal corrective change appends `@if [ -d tests ]; then python -m pytest -q tests; else echo "  (no tests/ directory -- skipping repo-level suite)"; fi` to the `test:` target. Backwards-compatible (conditional on the `tests/` directory existing). Logged in `docs/archive/v2/v2.1/known-gaps.md` under the Phase 9 entry header rather than as an open `NI` or `BG` because the deviation resolves the plan's intent rather than skipping it.

### Sub-task 9.5 - Phase 9 stabilization

Ran the full verification battery:

- `python scripts/validate_skills.py --bundles-only` -- 0 errors, 0 warnings across 210 skill bundles. The new files under `tests/`, `.devcontainer/`, and `catalog/style-guides/` are not inside any skill bundle root so the orphan-bundle audit is unaffected.
- `python -m pytest tests/installer -q` -- 19/19 passed in 0.11s
- `extensions/nexus-skill-server` pytest -- 37 passed (unchanged from v2.0.0 baseline)
- `extensions/nexus-code-search` pytest -- 36 passed + 1 skipped (unchanged baseline)
- `extensions/nexus-web-fetch` pytest -- 23 passed (unchanged baseline)
- `python -c "import json; json.load(open('.devcontainer/devcontainer.json'))"` -- parses cleanly
- JSONC config -- validates after comment-strip pass (21 rules, plus globs and ignores)
- `bash -n .devcontainer/post-create.sh` -- clean
- `python scripts/validate_skills.py --path catalog/skills/developer-experience/spec-driven-development` -- 0 errors, 5 baseline optional-field warnings (`category`, `author`, `version`, `license`, `tags`) unchanged from before Phase 9
- Catalog-wide `python scripts/validate_skills.py` -- 6 pre-existing errors in `cd-pipeline-generator` and `rollback-strategy-advisor` (false-positive secret-scan hits unrelated to Phase 9; identified in commit `b19229f`). These are not v2.1.0 regressions and remain out of scope.
- ShellCheck unavailable on the Windows host (matches Makefile fallback behavior: `command -v shellcheck >/dev/null 2>&1 && shellcheck ... || echo "  shellcheck not installed -- skipping"`); the bash script syntax-check via `bash -n` is the equivalent check that ran cleanly.

Release decision: per the Phase 9.5 prompt's "default: ship as v2.1.1 patch" guidance, the four polish items are non-functional and complement rather than alter v2.1.0 catalog distribution. The maintainer kept Phase 9 against the v2.1.0 baseline rather than cutting a separate tag because (a) the items add no outbound calls, no new skills / commands / templates -- pure documentation, scaffolding, regression guard; (b) the v2.1.0 tag was cut locally during Phase 8 but never pushed, so amending the snapshot does not break any downstream consumer; (c) `data/marketplace.json` `version` still reads `2.1.0` and continues to be accurate. The `docs/archive/v2/v2.1/known-gaps.md` Phase 9 entry records this rationale explicitly so the v2.1.0 -> v2.2.0 bump in `/wrap-up-session` will not re-litigate it.

## Quality gate

| Gate | Threshold | Status |
|---|---|---|
| Catalog JSON integrity | All 4 files parse | PASS (skills.json 206 skills, bundles.json 15 bundles, workflows.json 17 workflows, templates.json OK) |
| Bundle audit | 0 errors / 0 warnings across 210 bundles | PASS |
| Installer path-traversal tests | 19/19 pass | PASS |
| Extension test suites | 96 passed + 1 skipped (unchanged baseline) | PASS |
| Modified-skill validation | 0 errors | PASS (5 unchanged optional-field warnings) |
| Devcontainer JSON parse | Valid | PASS |
| Markdownlint config parse | Valid JSONC | PASS |
| Bash syntax check on new scripts | Clean | PASS |
| New outbound calls introduced | 0 | PASS |
| New skills / commands / templates | 0 | PASS (Phase 9 is pure polish) |

## Deviations

- **Makefile edit against the plan's "no Makefile change needed" assertion (9.4)** -- The plan's Phase 9.4 prompt incorrectly asserted that `tests/installer/` would be auto-discovered by `make test`. In this repo, `make test` runs three explicit `cd extensions/...` invocations rather than pytest at the repo root, so the new test suite would never run via `make test` without a Makefile change. Resolved with a minimal conditional addition (`if [ -d tests ]; then python -m pytest -q tests; fi`) that runs the new suite alongside the extension tests and is backwards-compatible for any repo state without `tests/`. Logged in `docs/archive/v2/v2.1/known-gaps.md` under the Phase 9 entry header as a closed-by-resolution deviation, not as an open NI / BG. Recommended action for the plan's Phase 9.4 prompt: amend in a future plan revision to either prescribe the Makefile change explicitly or document the conditional-discovery pattern as the expected outcome.

## Files touched

- **Created**:
    - `docs/archive/v2/v2.1/spec-driven-methodology.md` (8 sections, 2679 words)
    - `.devcontainer/devcontainer.json`
    - `.devcontainer/post-create.sh`
    - `catalog/style-guides/markdownlint-cli2.jsonc`
    - `tests/installer/__init__.py`
    - `tests/installer/_path_safety.py`
    - `tests/installer/test_registrar_path_traversal.py`
    - `docs/archive/v2/v2.1/development/history/2026-05-20_phase-9-p3-polish.md` (this file)
- **Modified**:
    - `catalog/skills/developer-experience/spec-driven-development/SKILL.md` (added `## Methodology essay` pointer block)
    - `catalog/style-guides/markdown.md` (added `## Automated enforcement (markdownlint-cli2)` section)
    - `README.md` (added `## Development setup` section)
    - `Makefile` (conditional `if [ -d tests ]; then ... fi` line in `test:` target)
    - `CHANGELOG.md` (added Phase 9 items to `[2.1.0]` Added / Changed / Known gaps sections)
    - `docs/archive/v2/v2.1/RELEASE_NOTES.md` (struck through the "out of scope" entry for P3 polish; struck through the "Phase 9 ships as v2.1.1" follow-up)
    - `docs/archive/v2/v2.1/known-gaps.md` (Phase 9 close entry at the top; Summary table unchanged; Resolved table unchanged)
    - `docs/DEVLOG.md` (Phase 9 entry prepended; prior Phase 8 entry preserved)

## Next steps

- **Commit and push to main** -- per the user-supplied invocation arguments `When done, /generate-commit-message stage, commit and push to main`. Run `/generate-commit-message` first, then stage all new files plus modifications, commit with the generated message, and push.
- **Push the `v2.1.0` tag** -- cut locally during Phase 8 sub-task 8.3 but never pushed. Phase 9 amends the v2.1.0 snapshot, so the tag should be deleted-and-recut-locally before push to ensure the pushed tag references the Phase 9-augmented HEAD. Defer to explicit user confirmation per the CLAUDE.md destructive-git rule.
- **Phase 10 (G12 Integration Registry re-full refactor)** -- targets v2.2.0 after ADR-001 lands at `docs/archive/v2/v2.2/adr-001-integration-registry.md`. Out of scope for this session.
