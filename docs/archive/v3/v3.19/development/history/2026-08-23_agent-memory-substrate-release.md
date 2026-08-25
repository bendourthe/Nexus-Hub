# Session history: v3.19.1 release

**Date**: 2026-08-23
**Plan**: `docs/v3/v3.19/plans/v3.19.1-agent-memory-substrate.md`
**Scope**: Merge PR #96 to develop, PR #97 to main, tag `v3.19.1`, publish the GitHub Release, and run the artifact round-trip.

## What shipped

- Known gaps DF-1, DF-2, DF-3, DF-4, and WN-1 stayed closed.
- PR #96 merged to develop (`818bbda4`). PR #97 merged develop to main (`fc1265d8`).
- Pre-tag assertion passed: HEAD on `main` equal to `origin/main`.
- Annotated tag `v3.19.1` pushed. GitHub Release published: https://github.com/bendourthe/Nexus-Hub/releases/tag/v3.19.1
- GitHub repository description hook count updated from 31 to 32.

## Artifact round-trip

`gh release download v3.19.1 --archive=tar.gz` produced `Nexus-Hub-3.19.1.tar.gz`. `python scripts/verify_install.py` against the extracted tree reported `verify: FAIL (6 modified, 0 missing, 3 extra)`.

The stale `MANIFEST.sha256` predates the gap-closure hook and related file edits. Recorded as **BG-1**. The tag and Release stay as published.

## Advisory release gates

- Platform read-contract: eight MATCH, Codex low non-breaking DRIFT, Nexus-AI UNVERIFIED. Stamp already `3.19.1` / 2026-08-23. No adapter change.
- Prompting-profile layer: **DRIFTED** (advisory). Last verified 2026-07-27. Does not block.
- Model map: valid, `verified_as_of` 2026-08-17. Live ids unchanged (Fable 5, GPT-5.6 sol/terra/luna, Gemini 3.7 Flash, Grok 4.6 / Composer 2.5). No tier change.
