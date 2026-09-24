# Documentation Archive

This directory holds the documentation of **prior major versions** of Nexus-Hub. Content is moved here (not deleted) when a major version is superseded, so the active `docs/` tree stays focused on the current and in-flight releases while the full historical record is preserved.

## Layout convention

```
docs/archives/
  v<MAJOR>/                         # archived major-version bucket (e.g. v0, v1, v2)
    v<MAJOR>.<MINOR>.<PATCH>/       # per-release directory, structure preserved as-shipped
      plans/
      development/history/
      known-gaps.md
      RELEASE_NOTES.md
      ...
```

This mirrors the active version layout. Archived content is **frozen history**: references inside archived files were repaired to point at their archived locations at archival time, but the content is not maintained going forward.

## Index

| Major | Versions archived | Files | Theme |
|---|---|---|---|
| **v0** | v0.8.1, v0.8.2, v0.8.5, v0.8.7, v0.8.8, v0.8.9, v0.9.2, v0.9.4, v0.9.5, v0.9.6, v0.9.7 | 28 | Pre-1.0 DevAI-Hub line: early comparisons, adoption plans, Opus-4.7 migration |
| **v1** | v1.0.0, v1.1.5, v1.3.0 | 24 | Skills-catalog maturation: bundled-resources convention, skill-eval-loop, security hardening |
| **v2** | v2.0.0, v2.1.0, v2.2.0, v2.3.0, v2.4.0 | 112 | Nexus-Hub rename, spec-driven methodology, integration registry, code-graph, antigravity transition, compound-engineering / persona-review pipeline |
| **v3** *(prior major, partial)* | `development/history/` subtrees only, v3.0 through v3.21 | 355 | Per-version session histories aged out under the retention policy, completed for the whole v3 line on 2026-09-06. The v3 line is NOT whole-major archived - its plans, comparisons, and known-gaps stay in the active tree. |
| **v4** *(current major, partial)* | `development/history/` subtrees v4.0-v4.5 and v4.7-v4.12, the v4.1 handbook snapshot, v4.0 CI task reconciliation, bounded v4.3 platform-source evidence, v4.4 Training layout and platform-mark disposition, v4.11 temporal-value evidence, and v4.13 follow-up evidence | 375 | Closed session histories aged out under the one-minor retention threshold; the aborted v4.13 trigger-pilot attempt is frozen separately while its open bug remains in `docs/releases/v4/`. |

## Archival policy

Two distinct rules put content here, and conflating them is the easy mistake:

1. **Whole-major archival** - a prior major is archived once the next major has a released version. The current major (`v4`) and any in-flight version directories are never archived this way.
2. **Per-version `development/` retention** (added v3.18.0) - within the current major, a minor behind the current one has its `development/history/` subtree archived to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/`. Only `history/` ages out: the rest of `development/` holds live CI fixtures and contract documents that shipped code cites by path. Its `plans/`, `comparisons/`, and `known-gaps.md` never age out and stay in the active tree. `scripts/check_docs_retention.py` reports what is due (advisory, always exits 0); the full rule is `docs/policy/docs-retention.md`.

## Incremental archive additions

| Archived path | Source path | Source version | Archived on |
|---|---|---|---|
| `v4/v4.10/development/history/2026-09-22-phase-7-final-qualification.md` | `docs/releases/v4/v4.10/development/history/2026-09-22-phase-7-final-qualification.md` | v4.10.1 | 2026-09-22 |
| `v4/v4.13/development/trigger-pilot-2/protocol.md` | `docs/releases/v4/v4.13/development/trigger-pilot-2/protocol.md` | v4.13.0 follow-up | 2026-09-23 |
| `v4/v4.13/development/trigger-pilot-2/pilot-prompts.json` | `docs/releases/v4/v4.13/development/trigger-pilot-2/pilot-prompts.json` | v4.13.0 follow-up | 2026-09-23 |
| `v4/v4.13/development/trigger-pilot-2/pilot-variant-b.json` | `docs/releases/v4/v4.13/development/trigger-pilot-2/pilot-variant-b.json` | v4.13.0 follow-up | 2026-09-23 |
| `v4/v4.13/development/trigger-pilot-2/attempt.md` | `docs/releases/v4/v4.13/development/trigger-pilot-2/attempt.md` | v4.13.0 follow-up | 2026-09-23 |
| `v4/v4.10/development/weekly-bars-host-render/verification.md` (with two PNGs) | Installed v0.10.0 VSIX in an isolated VS Code profile | v4.10.0 follow-up | 2026-09-24 |
| `v4/v4.10/development/scoped-weekly-alert/verification.md` | Installed v0.10.0 VSIX, isolated scoped-alert host test, and negative controls | v4.10.0 follow-up | 2026-09-24 |
| `v4/v4.7/development/supply-chain-watch-followup/verification.md` | Hosted watch, release assets, and attestation checks | v4.7.0 follow-up | 2026-09-24 |
| `v4/v4.7/development/model-map-followup/verification.md` | Superseded guide citation and current Codex CLI picker | v4.7.0 follow-up | 2026-09-24 |
| `v4/v4.5/development/prose-detector-disposition/verification.md` | False-positive sweep of the proposed stranded-auxiliary lexical rule | v4.5.0 follow-up | 2026-09-24 |
| `v4/v4.5/development/prompting-roster-disposition/verification.md` | Shipped Fable 5.1 profile and original roster-mismatch closure | v4.5.0 follow-up | 2026-09-24 |
| `v4/v4.9/development/verification-boundary-disposition.md` | Opus 5 prompting advice and claim-evidence gate ownership | v4.9.0 follow-up | 2026-09-24 |
| `v4/v4.9/development/private-harness-residue-disposition.md` | Recoverable cleanup and fresh absence check of private synthetic residue | v4.9.0 follow-up | 2026-09-24 |
| `v4/v4.11/development/temporal-source-values/real-artifact-inventory.json` | Independent source-to-DOM mapping for the retained five-slide presentation | v4.11.2 follow-up | 2026-09-24 |
| `v4/v4.11/development/temporal-source-values/real-artifact-verification.md` | Ten-viewport temporal sub-verdict and retained overall failure boundary | v4.11.2 follow-up | 2026-09-24 |
| `v4/v4.4/development/platform-mark-disposition/verification.md` | Five-mark approval, hash, and current browser-matrix reconciliation for v4.4 DF-1 | v4.4.1 follow-up | 2026-09-24 |

Archive moves are performed by `/refactor-docs` (the `docs-layout-refactor` skill) with reference repair; see the most recent `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/docs-cleanup-report.md` for the audit trail of each move. New frozen verification records do not move source files.

The v2 line was archived on 2026-06-04 alongside the v3.0.0 release (audit trail: `docs/releases/v3/v3.1/docs-cleanup-report.md`). The v3.16 `development/history` subtree (39 files) was archived on 2026-08-22 under rule 2 after v3.18.2 released; v3.17 followed with 27 files during the v3.19.0 release pass. v3.18 and v3.19 were archived in the v4 line, and v3.20 (22 files) plus v3.21 (5 files) were archived on 2026-09-06, completing the v3 line. That last pass also repaired the 20 `../../plans/` links the move broke and repointed five `DEVLOG.md` history links; it was the first run after `check_docs_retention.py` was fixed, having reported a clean tree since the layout refactor.
