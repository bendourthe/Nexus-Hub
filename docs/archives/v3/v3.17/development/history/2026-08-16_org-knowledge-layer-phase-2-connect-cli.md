# Development Log: Org Knowledge Layer Phase 2 - Connect CLI

**Date**: 2026-08-16
**Operator**: Nexus-Hub maintainer
**Assisted by**: OpenAI Codex
**Objective**: Implement Phase 2 of the v3.17.4 Org Knowledge Layer plan by adding a durable, validated `nexus-hub org` connection lifecycle for local directories and Git repositories.
**Outcome**: All four commands are implemented and covered by focused, installer, local-Git, atomic-write, and Windows launcher tests. The phase is ready for the Phase 3 materialization work, with one non-blocking local integration-suite runtime warning recorded as WN-6.

---

## 1. Starting State

- **Branch**: `feat/v3.17.4-org-knowledge-layer`, one Phase 1 commit ahead of `develop`
- **Starting tag/commit**: `af46880a`
- **Environment**: Windows PowerShell, Python 3.12.10, Git, Ruff, pytest, coverage.py, and ShellCheck; GNU Make unavailable
- **Prior session reference**: `docs/archive/v3/v3.17/development/history/2026-08-16_org-knowledge-layer-phase-1-org-bundle-contract.md`
- **Plan reference**: `docs/v3/v3.17/plans/v3.17.4-org-knowledge-layer.md`

Context: Phase 1 had established the dependency-free bundle validator and example organization bundle. Phase 2 needed to expose that contract through the already-installed CLI without introducing a second executable, installer copy rule, dependency, or network service.

---

## 2. Chronological Steps

### 2.1 Add the organization command lifecycle

**Branch**: `feat/v3.17.4-org-knowledge-layer` | **PR**: N/A | **Merged to**: Not merged

**Plan specification**: Add `connect`, `sync`, `status`, and `disconnect` through the CLI intercept pattern; distinguish URLs from paths; validate before recording; write state atomically; use argument-list Git calls; support confirmation overrides.

**What happened**: `scripts/nexus_hub_cli.py` gained a dedicated nested parser and lifecycle helpers. Directory connections store resolved absolute paths. Git connections shallow-clone into a temporary Nexus-Hub-owned directory, validate the candidate, then replace the cache only after success. `sync` performs `git pull --ff-only` for Git sources or revalidates a local source. `status` reports connection and validation details while degrading cleanly before Phase 3 posture support exists. `disconnect` removes only owned state and cached clone data.

**Key files changed**: `scripts/nexus_hub_cli.py`

**Troubleshooting**:

- **Problem**: The installed CLI could not import the validator through repository package assumptions.
- **Attempted**: Import through the source-tree package path.
- **Root cause**: Both launchers execute the copy at `~/.nexus-hub/scripts/nexus_hub_cli.py`, where the repository root is absent from `sys.path`.
- **Resolution**: Defer import until an org command runs, add only the adjacent `scripts/lib/integrations` directory, and import standalone `org_knowledge`.

**Verification**: Directory and local bare-Git command flows both pass against temporary `NEXUS_HUB_HOME` locations.

---

### 2.2 Build the Phase 2 regression suite

**Branch**: `feat/v3.17.4-org-knowledge-layer` | **PR**: N/A | **Merged to**: Not merged

**Plan specification**: Cover URL detection, branch sanitization, atomic writes, every verb, invalid input, real CLI flows, local bare Git, and Windows launcher reachability.

**What happened**: `tests/installer/test_org_cli.py` added 26 tests. Most lifecycle scenarios call `cmd_org` in-process so changed-line coverage is attributable; subprocess tests remain for top-level help and the actual Windows `.cmd` launcher. The Git fixture creates and pushes a real local bare repository, avoiding mocks and outbound network access.

**Key files changed**: `tests/installer/test_org_cli.py`

**Troubleshooting**:

- **Problem**: Failed clone cleanup encountered read-only Git pack files on Windows.
- **Resolution**: Retry exact owned-path deletion after setting the blocked entry writable.
- **Problem**: A concurrent state-write test produced `PermissionError` during `os.replace` on Windows.
- **Resolution**: Retry the same atomic replacement up to five times with short bounded delays, preserving last-writer-wins semantics.
- **Problem**: Subprocess-only tests left the new CLI code invisible to coverage.py.
- **Resolution**: Keep launcher proofs out-of-process and exercise lifecycle commands in-process at the command boundary.

**Verification**: The focused Phase 1 and Phase 2 suite passes 65 tests with one expected skip. Validator coverage is 90 percent and Phase 2 changed-line CLI coverage is 82.1 percent.

---

### 2.3 Run repository gates and update phase artifacts

**Branch**: `feat/v3.17.4-org-knowledge-layer` | **PR**: N/A | **Merged to**: Not merged

**Plan specification**: Run validation, lint, tests, CI path-filter audit, changelog update, known-gaps reconciliation, docs audit, and phase history.

**What happened**: GNU Make was unavailable, so its exact validation and test commands were invoked directly. Existing CI path filters and Linux/Windows test jobs already cover the changed paths, so no workflow edit was required. The plan, progress tracker, changelog, devlog, known-gaps ledger, and v3.17 docs inventory were updated for the Phase 2 checkpoint.

**Troubleshooting**:

- **Problem**: `make test` failed with `make : The term 'make' is not recognized as the name of a cmdlet, function, script file, or operable program.`
- **Resolution**: Run the Makefile's five extension pytest commands, repository CI groups, 18 validation constituents, JSON parses, and ShellCheck directly.
- **Problem**: The first `nexus-code-search` suite run failed `test_incremental_detects_modification` with `PermissionError: [WinError 5] Access is denied` during `os.replace`.
- **Resolution**: The exact test passed immediately in isolation and the complete suite then passed 294 tests with one expected skip, classifying the event as transient Windows filesystem contention.
- **Problem**: The monolithic repository suite reached 20 minutes and `tests/integrations` reached 10 minutes while responsive, without terminal summaries.
- **Resolution**: Run all other CI groups independently and record the integration-directory runtime as non-blocking WN-6 for protected-branch CI follow-up.

**Verification**: All bounded affected and repository groups passed; see the Verification Gate and Testing Summary.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| Phase 1 plus Phase 2 focused suite | PASS - 65 passed, 1 skipped |
| Phase 2 CLI changed-line coverage | PASS - 82.1 percent |
| Phase 1 validator coverage | PASS - 90 percent |
| Complete installer directory | PASS - 400 passed, 17 skipped |
| Five extension suites | PASS - 670 passed, 1 skipped |
| Validator tests | PASS - 695 passed, 2 skipped |
| Skill tests | PASS - 691 passed |
| Plan and workflow tests | PASS - 182 passed |
| Root regression test | PASS - 5 passed |
| `tests/integrations` on local Windows | NOT COMPLETED - responsive at 10-minute bound, no failure summary |
| Exact `make validate` constituents | PASS - 18 of 18 |
| JSON catalog parsing | PASS - 4 of 4 |
| ShellCheck | PASS |
| Ruff for new test file and new CLI findings | PASS - no new findings; five pre-existing CLI findings remain |
| CI path-filter and job audit | PASS - existing jobs cover changed paths |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| Local Windows `tests/integrations` run exceeds the 10-minute bounded phase runtime while responsive | P2 | Recorded as WN-6; protected-branch CI remains authoritative |

---

## 5. Plan Discrepancies

- GNU Make was unavailable, so every declared target command was executed directly.
- The plan asked to extend CI path filters only if needed. Inspection confirmed the existing filters and Linux/Windows jobs already cover `scripts/nexus_hub_cli.py` and `tests/installer/`, so no CI edit was made.
- The broad local integrations directory did not produce a terminal summary within the bounded Windows runtime. Every Phase 2-specific and affected installer test passed.

---

## 6. Assumptions Made

- **User-selected Git authority**: Git URLs are explicit user input and use the user's installed Git client and credential helper; Nexus-Hub adds no credential storage or third-party processor.
- **Clone timeout boundary**: The phase follows the plan by using a shallow clone and Git's own timeout behavior rather than adding a new watchdog.
- **Local source ownership**: A connected directory remains user-owned and is never deleted by `disconnect`.
- **Concurrent state semantics**: Last-writer-wins is acceptable when each writer atomically publishes one complete validated connection record.

---

## 7. Testing Summary

### Automated Tests

- Focused Phase 1 and Phase 2: 65 passed, 0 failed, 1 skipped.
- Installer: 400 passed, 0 failed, 17 skipped.
- Validators: 695 passed, 0 failed, 2 skipped.
- Skills: 691 passed, 0 failed, 0 skipped.
- Plans and workflows: 182 passed, 0 failed, 0 skipped.
- Root regression: 5 passed, 0 failed, 0 skipped.
- Internal extensions: 670 passed, 0 failed, 1 skipped after one transient Windows file-lock retry.
- Local Windows integrations directory: no terminal result within the 10-minute bound.

### Manual Testing Performed

- Reviewed generated `connection.json` shape and ownership boundary.
- Verified Git commands are argument lists and the CLI source contains no `shell=True`.
- Verified both installer launchers already target the same copied CLI and library tree.

### Manual Testing Still Needed

- [ ] Confirm the protected-branch integration job completes on hosted CI before release integration.

---

## 8. TODO Tracker

### Completed This Session

- [x] Implement `nexus-hub org connect`, `sync`, `status`, and `disconnect`.
- [x] Add defensive path, URL, Git, atomic-state, confirmation, and owned-cache handling.
- [x] Add complete Phase 2 focused and Windows launcher tests.
- [x] Audit installer distribution and CI coverage.
- [x] Update Phase 2 release and tracking artifacts.

### Remaining (Not Started or Partially Done)

- [ ] Phase 3: Materialize connected organization standards across supported platforms.
- [ ] Run protected-branch CI during the final integration phase.

### Out of Scope (Deferred)

- [ ] Phase 3 platform posture reporting and removal of materialized blocks.
- [ ] Broad integration-suite runtime optimization, unless hosted CI confirms a recurring bottleneck.

---

## 9. Summary and Next Steps

Phase 2 now provides one validated, durable, cross-platform organization bundle connection lifecycle through the installed Nexus-Hub CLI. The implementation avoids shell interpolation, external dependencies, and installer duplication, and its affected test and coverage gates pass.

**Next session should**:

1. Begin Phase 3 from the committed Phase 2 checkpoint.
2. Use `connection.json` and the Phase 1 validator as the only source-of-truth seam for platform materialization.
3. Reconfirm protected-branch CI before final release integration.
