# Documentation Archive

This directory holds the documentation of **prior major versions** of Nexus-Hub. Content is moved here (not deleted) when a major version is superseded, so the active `docs/` tree stays focused on the current and in-flight releases while the full historical record is preserved.

## Layout convention

```
docs/archive/
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

## Archival policy

A prior major is archived once the next major has a released version. The current major (`v3`) and any in-flight version directories are never archived. Whole-major archival is performed by `/refactor-docs` (the `docs-layout-refactor` skill); see the most recent `docs/<active-version>/docs-cleanup-report.md` for the audit trail of each archival run.

The v2 line was archived on 2026-06-04 alongside the v3.0.0 release (audit trail: `docs/v3.1.0/docs-cleanup-report.md`).
