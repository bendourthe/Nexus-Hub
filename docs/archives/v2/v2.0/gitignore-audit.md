# Gitignore Audit -- v2.0.0 Phase 7.4

**Date**: 2026-05-20
**Phase**: 7.4 (run `/update-gitignore` audit for the rename)
**Plan**: [`docs/archives/v2/v2.0/plans/nexus-hub-rename.md`](plans/nexus-hub-rename.md)

## Audit summary

| Item | Status |
|---|---|
| `devai-hub` patterns in `.gitignore` | None to remove. The file never carried a `devai-hub` pattern (the rename is scoped to repo-internal paths, plugin metadata, env vars, and MCP server names -- none of which are gitignored). |
| `.devai/` -> `.nexus/` index path patterns | Already handled. Lines 77-82 of `.gitignore` document the v2.0.0 rename explicitly: `.nexus/` and `.nexusignore` are the active patterns; `.devai/` and `.devaiignore` are retained as legacy patterns for users still mid-upgrade, with a comment marking them "safe to remove after v2.1.0". |
| `assets/*.png` accidentally ignored | Not ignored. `git check-ignore -v assets/*.png` returns nothing. The hero / brand PNGs will be tracked when added. |
| Tracked cache directories (`__pycache__`, `.pytest_cache`, `.mypy_cache`, `.ruff_cache`) | Clean. None of the four are tracked; the existing `.gitignore` entries cover them. |
| Tracked Python `*.pyc` files | Clean. Covered by the existing `*.py[cod]` glob. |
| Tracked Node `node_modules/` | Clean. Existing `node_modules/` entry covers it. |
| Tracked VS Code extension build artifacts (`*.vsix`, `extensions/**/out/`) | Clean. Existing entries cover them. |
| Tracked benchmark output (`data/benchmarks/`) | Clean. Existing entry covers it. |
| Tracked `.skill` archives (output of `scripts/package_skill.py`) | Clean. Existing `*.skill` entry covers it. |
| Tracked workspace dirs (`*-workspace/`) | Clean. Existing entry covers it. |
| Local `.claude/settings.local.json` | Clean. Existing entries cover both. |

## Changes applied to `.gitignore`

None. The file is already in the correct state for v2.0.0: the legacy `.devai/` retention was added in an earlier phase (likely Phase 4 when the extension storage paths were renamed), and no other Phase 7 gitignore action is required.

## Notes on v2.0.0 artifacts intentionally tracked

| Path | Reason tracked |
|---|---|
| `docs/archive/v2/v2.0/baselines/*.txt` | Pre- and post-rename validator baselines. Tracked so the diff between them is reproducible at the v2.0.0 tag for auditors. They are small text files; size is not a concern. |
| `docs/archive/v2/v2.0/installer-smoke-pre.txt` and `installer-smoke-post.txt` | Installer dry-run captures. Same rationale. |
| `docs/archive/v2/v2.0/rename-manifest.txt` | Per-file change manifest from `scripts/apply_rename.py`. Tracked for audit traceability. |
| `assets/*.png` (when added) | Brand assets shipped with the README and any future documentation. Tracked because GitHub renders them inline. The two PNG files in scope (`nexus_primary.png`, `nexus_monochrome.png`) are ~10-100 KB each -- well below the soft 1 MB threshold beyond which Git LFS would be considered. |

## Recommended Git LFS candidates

None. The repo currently ships no binary files larger than ~1 MB. The Word / PowerPoint / Excel templates under `templates/documentation/` are the largest binaries (a few hundred KB each) and are intentionally tracked in standard Git because they ship via the installer to user homes; their churn rate is very low. If future v2.x work adds large media (video, design source files), revisit LFS at that point.

## Cross-references

- The `assets/*.png` files referenced by the new README hero (`assets/nexus_primary.png`, `assets/nexus_monochrome.png`) are NOT YET in this repo as of Phase 7. The Phase 6 commit `b85425c` rebranded the README but did not include the asset copy because the source files live on the sibling Nexus repo's filesystem path (`C:\Users\bdour\...`) which is not present on this maintainer's machine. The current README hero uses a plain `<p>` text block; the planned `<img src="assets/nexus_primary.png">` swap is deferred until the asset transfer is performed. Tracked in [`docs/archives/v2/v2.0/known-gaps.md`](known-gaps.md) for Phase 8 cleanup.
- The `.devai/` legacy gitignore retention will be removed at v2.1.0 once enough release time has elapsed that in-flight upgrades are rare.
