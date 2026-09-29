# Development Log: v3.17.0 Phase 5 CLI, monitors, and decision walkthrough

**Date**: 2026-08-14 to 2026-08-15
**Operator**: Nexus-Hub maintainer
**Assisted by**: OpenAI Codex
**Objective**: Expose project autonomy through the cross-platform CLI and both usage monitors, document its platform contract, and distribute the consequential-decision walkthrough across every supported instruction surface.
**Outcome**: Phase 5 is complete. The CLI and both monitor surfaces remain thin views over the shared engine, the twelve substantive templates carry one verified decision-guidance block, focused CI covers every new surface, and the branch is ready for Phase 6.

---

## 1. Starting State

- **Branch**: `feat/v3.17.0-agent-autonomy-toggle`
- **Starting commit**: `07464732`
- **Environment**: Windows PowerShell, Python 3.12.10, Node.js 24.13.0, npm 11.6.2
- **Prior session reference**: [Phase 4 deny layer and hook independence](2026-08-14_agent-autonomy-toggle-phase-4-deny-layer-and-hook-independence.md)
- **Plan reference**: [v3.17.0 agent autonomy toggle](../../plans/v3.17.0-agent-autonomy-toggle.md)

Phase 4 had committed the enforcing deny layer locally. Phase 5 began from that clean checkpoint and implemented the remaining user surfaces, documentation, decision guidance, tests, and CI coverage without pushing the feature branch.

---

## 2. Chronological Steps

### 2.1 Cross-platform CLI surface

**Plan specification**: Add `nexus-hub autonomy status|enable|disable|revert`, default enablement to the edits tier, require interactive typed confirmation for full autonomy, and keep policy in the shared engine.

**What happened**: A public `scripts/lib/autonomy_cli.py` feature module now owns argument parsing and presentation while `scripts/nexus_hub_cli.py` performs root registration and dispatch. Status reports the complete 16-platform roster, support state, available tiers, current tier, and remaining TTL. Enablement always previews the core diff, defaults to edits, refuses non-interactive full autonomy, and returns the engine exit code. Automated tests import the real feature module and cover all four verbs plus root CLI dispatch.

**Troubleshooting**:

- The first coverage design loaded the CLI through a test alias, so the production module appeared unexecuted. Extracting the feature into `scripts/lib/autonomy_cli.py` made the test boundary honest and raised combined engine and CLI coverage to 85.14 percent.
- A manual help assertion initially used PowerShell array matching and produced a false negative. Joining the help lines before matching confirmed registration and the 16-platform roster.

### 2.2 Usage-monitor autonomy controls

**Plan specification**: Add persistent tier and TTL status plus CLI-routed toggles to the Claude and Codex VS Code extensions, including expiry refresh and an explicit unavailable state.

**What happened**: Both extensions now own an autonomy status state machine and status-bar controller. They call the CLI for every status or mutation operation, refresh on a timer and window focus, show neutral, warning, or error states for off, edits, or full, render expired state safely, and distinguish a missing CLI from verified-off state. Enable and full-tier flows open a visible terminal so the shared diff and typed-confirmation contract remain intact. Versions advanced to Claude 0.9.7 and Codex 0.2.8.

**Troubleshooting**:

- Claude coverage first failed because `@vitest/coverage-v8` was absent after a lockfile-only transition. A clean `npm ci` restored the declared dependency.
- Extension-wide Claude coverage measured 14.07 percent because legacy provider and UI modules lack tests. The Phase 5 autonomy state module is therefore explicitly enforced at 91.66 percent line coverage, while the broader debt is recorded as MT-1. Codex retains its extension-wide 81.39 percent line coverage gate.

### 2.3 Documentation and consequential-decision guidance

**Plan specification**: Document autonomy across the full platform roster, record the no-new-skill decision, and impose a concise plain-language walkthrough before consequential choices.

**What happened**: `AGENTS.md` now explains the workspace-only grant, tier, consent, TTL, distribution, scope relationship, guidance limits, and existing-skill composition. `docs/permissions-research.md` now covers all 16 platforms and the established PowerShell evidence. No new catalog skill was added because `agent-access-policy`, `ai-billing-safeguards`, and the existing threat-model skill already own the adjacent guidance.

One platform-neutral `Consequential Decisions` block was added byte-identically to all 12 substantive templates, and the parity validator now treats it as an invariant. Single-sentence reminders were added at the owning decision points in implement, planning, refactor, known-gap, and release workflows.

### 2.4 Testing, CI, and completion records

**Plan specification**: Add automated CLI and extension tests, preserve at least 80 percent feature coverage, validate template parity, and extend path-filtered CI after maintainer approval.

**What happened**: The maintainer approved the exact three-workflow diff on 2026-08-15. The autonomy workflow now includes the feature module, root CLI, and dispatch tests in its path filter and coverage command. Both usage-monitor workflows run their coverage scripts instead of test-only scripts. No remote workflow was triggered because Phase 5 is a local-only checkpoint.

The broad repository test command exceeded both a 120-second probe and a 10-minute aggregate window without useful failure isolation. Running the same families in bounded suites produced 4,336 passing tests and 58 expected skips across Python, hooks, integrations, skills, validators, workflows, and TypeScript. The exact Makefile validation recipes were also run directly because GNU Make is unavailable on this Windows host.

---

## 3. Verification Gate

| Check | Result |
|---|---|
| Autonomy engine and CLI coverage workflow command | PASS: 92 passed, 3 skipped, 85.14% coverage |
| Native-shell TTL expiry workflow command | PASS: 6 passed |
| Hook inventory and autonomy parity workflow command | PASS: 19 passed, 261 deselected |
| Claude Usage Monitor coverage workflow command | PASS: 11 passed, autonomy module 91.66% lines |
| Codex Usage Monitor coverage workflow command | PASS: 81 passed, extension 81.39% lines |
| Full bounded local matrix | PASS: 4,336 passed, 58 expected skips |
| Extension compilation | PASS: Claude and Codex |
| Catalog and platform validation recipes | PASS |
| Base-template parity | PASS: 12 templates, 1 unique block |
| Manual CLI smoke | PASS: help registered, 16 platforms, 8 supported, 8 unavailable |
| `git diff --check` | PASS |

---

## 4. Known Issues

| Issue | Severity | Decision |
|---|---|---|
| Both Vitest configs warn that future native loading will reject their current ESM-in-CommonJS form | P3 tooling debt | Track as WN-3 for consistent Phase 6 resolution |
| Claude legacy modules do not yet support an extension-wide 80 percent coverage boundary | P3 test debt | Enforce the new autonomy module at 91.66 percent and track broader work as MT-1 |

Neither issue blocks Phase 5 functionality or release readiness. One concurrent audit test briefly contended on `autonomy-audit.jsonl.lock`; the isolated rerun passed and no product change was warranted.

---

## 5. Plan Discrepancies

- The plan expected explicit installer registration for every new script. Phase 5 added no new top-level installer payload: both installers already copy `scripts/nexus_hub_cli.py` explicitly and recursively copy `scripts/lib`, so editing them would have duplicated existing distribution behavior. Installer and CLI tests verify the existing path.
- The plan named Claude 0.9.6 and Codex 0.2.6 as starting versions. The branch actually started from Codex 0.2.7, so the resulting versions are Claude 0.9.7 and Codex 0.2.8.
- The base-template constitution check originally expected no instruction edit, but Amendment A1 explicitly reversed that decision and required the 12-template lockstep change.
- The full test matrix was partitioned by family after aggregate commands timed out on the OneDrive-backed Windows workspace. Every bounded family passed, and the focused CI commands were rerun exactly after approval.

---

## 6. Assumptions Made

- The CLI remains the single public mutation surface; extension code may translate CLI output into display state but may not reproduce consent, tier, TTL, or policy decisions.
- A missing CLI is not equivalent to verified-off autonomy and must remain visibly unavailable.
- Installer registration is satisfied by the existing explicit root CLI copy and recursive library copy; no file-name list is needed for a library module already inside that tree.
- The consequential-decision rule is contextual guidance, not a tool-blocking enforcement mechanism, and project instructions may override installed guidance by design.

---

## 7. Testing Summary

### Automated Tests

- Exact autonomy CI gates: 117 passed, 3 skipped, plus 261 parity tests deselected by the workflow expression.
- Extension coverage: 92 tests passed across Claude and Codex.
- Full bounded repository matrix: 4,336 passed, 58 expected skips.
- Catalog, workflow-security, permission-baseline, platform-contract, version-sync, template-parity, and context-compression validators passed.

### Manual Testing Performed

- Confirmed `nexus-hub --help` registers autonomy and status renders all 16 platforms, including supported and unavailable groups.
- Confirmed the 12 substantive templates contain one byte-identical consequential-decision block.
- Confirmed neither `data/SKILL_INDEX.md`, `data/skills.json`, nor `data/marketplace.json` changed.

### Manual Testing Still Needed

None for the Phase 5 local checkpoint. Remote CI and installed-package smoke remain final-phase integration work under Phase 6.

---

## 8. TODO Tracker

### Completed This Session

- [x] 5.1 Add the thin cross-platform autonomy CLI and verify existing installer distribution.
- [x] 5.2 Add autonomy status and toggle controls to both usage monitors.
- [x] 5.3 Refresh platform documentation and record the no-new-skill decision.
- [x] 5.4 Add comprehensive automated tests and approved focused CI coverage.
- [x] 5.5 Distribute and validate the consequential-decision walkthrough.

### Remaining

- [ ] Phase 6: architecture refactor, known-gaps reconciliation, CI/CD, and controlled integration.

### Out of Scope

- [ ] Resolve WN-3 and MT-1 through the Phase 6 reconciliation process.
- [ ] Push, merge, release, and run remote CI only at the final lifecycle gate.

---

## 9. Summary and Next Steps

Phase 5 gives users one consistent autonomy surface from the terminal or either usage monitor without weakening the shared consent and expiry engine. It also makes consequential approval requests easier to understand across every supported instruction surface, with parity validation ensuring the rule ships consistently.

**Next session should**:

1. Run Phase 6 architecture and duplication review across the completed autonomy implementation.
2. Reconcile every v3.17.0 known gap, including WN-3 and MT-1, into close, defer, or blocker dispositions.
3. Complete final CI/CD, integration, publication, and release-readiness gates under the approved lifecycle.
