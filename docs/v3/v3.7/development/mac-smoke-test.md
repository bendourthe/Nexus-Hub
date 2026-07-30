# Mac Smoke Test -- v3.7.0 One-Command Bootstrap

**Purpose**: a recorded manual checklist for verifying the v3.7.0 one-line install bootstrap on a real macOS machine. CI exercises the bash bootstrap on `ubuntu-latest` and `macos-latest` runners against a local tarball (zero network), but it cannot exercise the real `curl | bash` path against live GitHub. This checklist closes that gap and is the manual half of the Phase 5 cross-platform proof (a real Mac is the only place the network one-liner is hand-verified, because CI uses a local tarball with zero network). This used to cite WN-v36-1 as "bash cannot be fully run on the Windows dev host"; that framing was DISPROVEN in v3.15.6 Phase 4 (the cause was PATH shadowing by the WSL launcher stub, not host incapability). The reason for a Mac hand-check is unchanged and stands on its own: it is about exercising the live-network `curl | bash` path, not about which hosts can run bash.

**Scope**: a clean machine with no prior Nexus-Hub clone. The test proves the network fetch, dependency precheck, no-prompt install, the `nexus-hub` CLI on PATH, and the `nexus-hub upgrade` checker.

## Preconditions

- A macOS machine (Apple Silicon or Intel) with no `~/.nexus-hub` directory (move any existing one aside first: `mv ~/.nexus-hub ~/.nexus-hub.bak`).
- `curl`, `tar`, and a Python 3 interpreter (`python3`) on PATH. These ship with macOS / Xcode Command Line Tools; the precheck reports any that are missing.
- Network access to `github.com` and `raw.githubusercontent.com`.

## Checklist

Run each step in order and record the observed result in the table below.

1. **One-command install (curl variant)**. In a fresh Terminal, run:

       curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash

    Expected: the bootstrap downloads the `main` catalog tarball, extracts it to `~/.nexus-hub/src`, runs the core installer with no scope / platform / overwrite prompts, configures every detected assistant (absent ones skip-with-note), and prints the `Nexus-Hub v3.7.0 installed (Global scope).` banner plus a PATH hint for `~/.nexus-hub/bin`.

2. **`nexus-hub --version`**. Open a new shell (or add `~/.nexus-hub/bin` to PATH per the printed hint), then run:

       nexus-hub --version

    Expected: prints `nexus-hub 3.7.0`.

3. **`nexus-hub upgrade` (already up to date)**. Run:

       nexus-hub upgrade

    Expected: reports `Installed: 3.7.0` and `Latest: 3.7.0` and `You are already on the latest version. Nothing to do.` (the only outbound call is to the project's own GitHub).

4. **Re-install is idempotent and preserves edits**. Add a sentinel line outside the Nexus-Hub markers in a managed instruction file (e.g. `~/.claude/CLAUDE.md`), then re-run the one-liner from step 1. Expected: the install completes with no prompt (no real conflict), and the sentinel line survives.

5. **wget fallback (optional)**. On a box without `curl` but with `wget`, confirm the documented fallback installs the same way:

       wget -qO- https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash

    Expected: identical outcome to step 1.

6. **Missing-tool message (optional)**. Temporarily shadow the downloader (`PATH='' bash install.sh` from a saved copy, or rename `curl`/`wget`) and confirm the precheck exits non-zero with a clear "missing X -- install with Y" message naming `curl`/`wget`.

## Results

| Step | Run on (macOS version / arch) | Date | Result | Notes |
|---|---|---|---|---|
| 1 - curl install | | | pending | |
| 2 - --version | | | pending | |
| 3 - upgrade up-to-date | | | pending | |
| 4 - idempotent re-install | | | pending | |
| 5 - wget fallback (optional) | | | pending | |
| 6 - missing-tool message (optional) | | | pending | |

**Status**: pending a manual run on a real Mac. Until a maintainer records results here, the Mac smoke test is tracked as an open item in [known-gaps.md](../known-gaps.md) (the automated `macos-latest` CI bootstrap job covers the local-tarball path in the meantime). Note: steps 1-3 require the v3.7.0 tag to be live on `main`; before release they can be rehearsed against a feature branch by exporting `NEXUS_HUB_REF=<branch>` ahead of the one-liner.
