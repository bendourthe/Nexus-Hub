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
| **v3** *(current major, partial)* | `development/` subtrees only, v3.0 through v3.17 | 282 | Per-version session histories aged out under the retention policy. The v3 line is NOT whole-major archived - its plans, comparisons, and known-gaps stay in the active tree. |
| **v4** *(current major, snapshot)* | v4.1 handbook snapshot | 1 | Living handbook source captured as shipped with v4.1.0; active release evidence remains under `docs/releases/v4/v4.1/`. |

## Archival policy

Two distinct rules put content here, and conflating them is the easy mistake:

1. **Whole-major archival** - a prior major is archived once the next major has a released version. The current major (`v3`) and any in-flight version directories are never archived this way.
2. **Per-version `development/` retention** (added v3.18.0) - within the CURRENT major, a minor two or more behind current has its `development/` subtree archived to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/development/`. Its `plans/`, `comparisons/`, and `known-gaps.md` never age out and stay in the active tree. `scripts/check_docs_retention.py` reports what is due (advisory, always exits 0); the full rule is `docs/policy/docs-retention.md`.

Both are performed by `/refactor-docs` (the `docs-layout-refactor` skill) with reference repair; see the most recent `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/docs-cleanup-report.md` for the audit trail of each run.

The v2 line was archived on 2026-06-04 alongside the v3.0.0 release (audit trail: `docs/v3/v3.1/docs-cleanup-report.md`). The v3.16 `development/history` subtree (39 files) was archived on 2026-08-22 under rule 2 after v3.18.2 released; v3.17 followed with 27 files during the v3.19.0 release pass.
