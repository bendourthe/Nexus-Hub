# Session History - v3.6.0 adoption-spec-kit Phase 4: /skills import hygiene gate (N6)

**Date**: 2026-06-16
**Plan**: [`../../plans/adoption-spec-kit.md`](../../plans/adoption-spec-kit.md) Phase 4 (N6, a Bucket-B `re-partial` local re-build)
**Branch**: `feat/spec-kit-delta-adoption`
**Outcome**: Implementation complete; quality gate GO. Built ahead of Phase 3 at the maintainer's request (Phase 4 prerequisites are "None"). Phase 3 (N1a workflow-phase hook recipe) remains outstanding and is tracked as NI-v36-1; it must land before Phase 5, whose CHANGELOG enumerates N1a. No release work this phase.

## Goal

Harden the existing LOCAL `/skills import` path with the three catalog-hygiene disciplines reverse-engineered from a generic catalog-stack pattern (comparison candidate N6): HTTPS-only source validation, an `install_allowed` discovery-only flag, and hash-on-import (reusing the existing manifest hashing). The hard constraint: introduce NO new outbound call, dependency, or credential, and do NOT accidentally add the remote-credentialed catalog fetch the comparison declined (N5). The hygiene layer must be ADDITIVE to the existing pre-install `skill-security-scan` / `nexus-skill-scanner` gate, never a replacement.

## Branch / sequencing note

The session opened on an unrelated branch (`fix/macos-install-usage-monitor`) with uncommitted macOS-fix WIP. That WIP was stashed (`git stash -u`, recoverable) and the session switched to `feat/spec-kit-delta-adoption`, where Phases 1 and 2 are committed. A cross-ref check across all local and remote refs confirmed Phase 3 (N1a) was never implemented for v3.6.0 (the "Phase 3" commits in the log belong to the older v2.1.0 adoption-spec-kit plan). Phase 4 was implemented first because the plan declares its prerequisites as "None"; the out-of-order build is recorded as NI-v36-1 so Phase 3 is not lost.

## Scope of the import path (sub-task 4.1)

Tracing `catalog/commands/skills.md` showed `import -> import-skills`, an agent-driven retained skill (the agent copies catalog skills into the active project; there is no in-repo import script). Relevant existing pieces: the export counterpart `scripts/package_skill.py` (a distributed CLI), the manifest hasher `scripts/lib/integrations/manifest.py::_hash_path` (chunked SHA-256, distributed under `lib/integrations/`), the pre-install security gate `scripts/scan_skill_security.py` / `nexus-skill-scanner`, and the read-only `nexus-skill-server` (search only, no import tool). An external source (path or URL) enters the flow only for imports from outside the trusted local catalog; local catalog imports have no URL. The phase is LOCAL hygiene only -- remote fetch is out of scope. The chosen home for the testable hygiene is a new distributed helper symmetric to `package_skill.py`, invoked by the import operation.

## What shipped

### N6 - the import-hygiene gate (sub-task 4.2)

- **`scripts/import_skills.py`** (new, ~280 lines, stdlib-only): a CLI (`validate-source` / `check-allowed` / `hash` / `vet`) plus importable pure functions.
  - **HTTPS-only validation** (`validate_https_source`): `https://`, and `http://` to a loopback host (`localhost` / `127.0.0.1` / `[::1]`), are allowed; a plain local filesystem path (no `scheme://`) is allowed; non-loopback `http://`, `file://`, `ftp://`, `git://`, and empty input are refused, each with a human-readable reason. URL-vs-path detection uses a `^scheme://` regex so Windows drive paths (`C:\...`) and POSIX paths are correctly classified as local, not URLs.
  - **Discovery-only flag** (`is_install_allowed` + `read_install_allowed_from_skill`): defaults to installable; an explicit falsey value (`False` or the strings `false`/`no`/`0`/empty), read from a skill's SKILL.md frontmatter or a source-entry dict, marks it listable-but-not-installable.
  - **Hash-on-import** (`hash_on_import` / `hash_tree`): REUSES `manifest._hash_path` (no new hashing code) via a dual-path import that resolves both the in-repo (`scripts.lib.integrations.manifest`) and installed (`lib.integrations.manifest`) layouts.
  - **`vet_import`** orchestrator: runs all three checks, returns a structured record, and records per-artifact SHA-256 only when the gate passes (you hash what you actually import). Exit-code contract: 0 = accepted, 1 = refused, 2 = usage/IO error. Every user-facing message reaffirms the additive relationship to the `skill-security-scan` gate.
- **`scripts/installer.sh`** + **`scripts/installer.ps1`**: registered the script (modeled on the `package_skill.py` copy block) so it lands at `~/.nexus-hub/scripts/import_skills.py`. The bash block uses the file's `[OK]` convention; the PowerShell block uses the file's existing `checkmark` convention.
- **`catalog/commands/skills.md`**: added an "import scope (local hygiene gate)" subsection documenting the three checks, the exact invocations, the no-outbound guarantee, and the additive relationship to the `scan` step.

This is a runtime helper invoked during an import, NOT a catalog validator, so -- unlike the Phase 2 parity guard -- it is correctly absent from `make validate` and the CI `validate` job. Its tests live under `tests/validators/`, which the CI `tests` job already runs.

### Tests (sub-task 4.3)

- **`tests/validators/test_import_skills.py`** (new, 42 cases): every branch -- https/loopback allow (incl. `[::1]`), non-HTTPS / `file://` / `ftp://` / `git://` / empty reject, local-path and Windows-drive-path allow, the `install_allowed` default/false/truthy matrix, SKILL.md frontmatter reads (false / default / missing-md), hash-matches-`hashlib`, the manifest-hasher-reuse identity check (`imp._hash_path is manifest._hash_path`), `hash_tree` multi-file, the `vet` allow-and-hash / discovery-only-block-and-skip-hash / non-https-reject paths, a no-outbound-call regression guard (asserts the module source imports no `urllib.request` / `requests` / `httpx` / `socket` / `urlopen` / `http.client`), and the CLI exit-code contract via subprocess.

All added content is ASCII-only; per the Reverse-Engineering Attribution Rule no upstream repo/product is named in any shipped artifact.

## Key decisions

- **A new distributed helper, not skill prose.** The plan's stability gate demands tests for the reject/allow/hash branches, which agent-prose cannot satisfy. The import being agent-driven, the testable home is a distributed helper symmetric to `package_skill.py` (the export side), reusing the manifest hasher. The plan explicitly accommodates "if a distributed script was added: register copy steps in BOTH installers".
- **Reuse `manifest._hash_path` exactly.** The plan mandates reusing the existing hashing rather than writing new code; a test asserts object identity to lock that in. A dual-path import keeps it working both in-repo and when installed.
- **URL-vs-path by `scheme://` regex.** A naive `urlparse` treats `C:\...` as scheme `c`; the regex avoids false-rejecting Windows local paths while still catching `file://` and other non-HTTPS URL schemes.
- **Hash only on a passing gate.** Hash-on-import records what is actually imported; a blocked import (non-HTTPS or discovery-only) records no hashes, matching the semantics and giving the tests a clean assertion.
- **No CI validate-job entry.** The gate validates an import action, not the repo, so it does not belong in `make validate` / `ci.yml`'s validate job (contrast the Phase 2 parity guard, which validates the catalog). Its 42 tests are covered by the existing `pytest tests/validators` CI step.

## Verification (quality gate: GO)

`make` is not on PATH on this Windows host (WN-v33-1), so the gates were run via the documented direct equivalents:

- **The new gate**: all branches smoke-tested by hand (https accept, http-remote refuse rc=1, http-localhost accept, local-path accept, `vet` on a real skill hashes 3 files); the 42 pytest cases pass.
- **`make validate` (direct chain)**: GREEN. JSON catalog integrity (256 skills / 15 bundles / 17 workflows load), orphan-bundle audit PASS (0 errors, 1 pre-existing WN-v33-2 warning), unicode-safety 0 errors (1051 pre-existing warnings; the new files add none; the PowerShell checkmark glyph is not flagged), no-personal-paths exit 0, supply-chain-iocs exit 0, workflow-security exit 0, version-sync surfaces match 3.5.0, parity guard exit 0.
- **`make test` (repo-level `pytest tests/`)**: 540 passed, 0 failed. The Phase-2 WN-v36-1 bash-path-with-spaces failures do NOT recur on this checkout (its path has no spaces); the 42 new tests are included (498 prior collected + 42).
- **`make lint`**: ShellCheck is not on PATH, so `installer.sh` was verified with `bash -n` (clean) and `installer.ps1` with the `[Parser]::ParseFile` AST (0 errors).
- **Distributed-script dry-run**: staged `import_skills.py` + `lib/integrations/manifest.py` into a throwaway `scripts/` layout with no repo root on the path; the script runs and hashes correctly, proving the installed-layout `lib...` import resolves.
- **Diff isolation**: `git status` shows exactly `scripts/import_skills.py`, `tests/validators/test_import_skills.py`, `catalog/commands/skills.md`, `scripts/installer.sh`, `scripts/installer.ps1`, plus the plan checklist, DEVLOG, known-gaps, and this session history. No scope creep, no `data/` / registry edit.

## Files changed

- `scripts/import_skills.py` (N6, new distributed import-hygiene gate)
- `tests/validators/test_import_skills.py` (new, 42 cases)
- `catalog/commands/skills.md` (new "import scope (local hygiene gate)" subsection)
- `scripts/installer.sh` (install_scripts: +1 copy block)
- `scripts/installer.ps1` (install_scripts: +1 copy block)
- `docs/v3/v3.6/plans/adoption-spec-kit.md` (Phase 4 exit checklist checked off; Phase-3-pending note)
- `docs/v3/v3.6/known-gaps.md` (NI-v36-1 added for pending Phase 3; WN-v33-1 + WN-v36-1 re-confirmed for Phase 4)
- `docs/DEVLOG.md` (Phase 4 entry)
- `docs/archive/v3/v3.6/development/history/2026-06-16_adoption-spec-kit-phase-4-skills-import-hygiene.md` (this file)

## Next

Phase 3: the workflow-phase hook recipe (N1a) -- still outstanding (NI-v36-1). Document how to approximate spec-kit's per-command `before_/after_` lifecycle hooks using ONLY Nexus-Hub's four supported events (SessionStart / PreToolUse / PostToolUse / Stop), honestly documenting the 4-event constraint, with at most one minimal opt-in example hook (registered in `catalog/hooks/settings.json`, an ask-first area) and a pytest. Implement it before Phase 5, whose CHANGELOG enumerates all five adoptions including N1a. The CHANGELOG `[Unreleased]` block and the reverse-engineering-matrix rows for the N5 + N1b declines remain deferred to Phase 5 per the plan.
