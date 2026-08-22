# Session History - v3.10.0 adoption-ruflo Phase 4: nexus-hub verify supply-chain command + release manifest

**Date**: 2026-06-30
**Plan**: [`../../plans/adoption-ruflo.md`](../../plans/adoption-ruflo.md) Phase 4 (A1: `nexus-hub verify` supply-chain command + release manifest; re-full, P1 - the highest-value item in the cycle)
**Branch**: `develop`
**Outcome**: Complete. All Phase 4 exit-checklist items satisfied; quality gate GO. Phase 4 of 6; not the final phase, so no release-readiness run.

## Goal

Build a local `nexus-hub verify` subcommand that recomputes SHA-256 of the installed catalog tree and diffs it against a release-published `MANIFEST.sha256`, so a user can prove their on-disk install matches the published catalog - with zero new outbound call, no new dependency, no credential, and no paid code-signing. Reuse the existing `scripts/lib/integrations/manifest.py` hashing rather than reinvent it; register the new scripts by explicit name in both installers (an AGENTS.md "ask first" surface); wire manifest generation into the release flow; reason the manifest's trust boundary correctly.

## What shipped

- **`scripts/generate_manifest.py`** (new): deterministic manifest generator. Writes `MANIFEST.sha256` at the repo root in `sha256sum -c` text format (`<sha256><space><space><relative-posix-path>`, LF lines, sorted by path so re-runs are byte-identical; forward-slash paths so the manifest is identical regardless of writing OS). Reuses `scripts/lib/integrations/manifest.py::_hash_path` via the same dual-location import shim as `import_skills.py` (in-repo `from scripts.lib...` / installed `from lib...`), so there is no second hashing implementation. Owns the single source of truth for manifest scope, which the verifier imports: `COVERED_ROOTS = (catalog, templates, scripts, data)`, the exclusion predicate (`.git`, caches, `node_modules`, venvs, `dist`/`build`, `*.pyc`/`*.pyo`/`*.egg-info`, the manifest file itself), `iter_catalog_files`, and `parse_manifest` (tolerant of blank lines and both `sha256sum` text/binary markers). CLI: `--root`, `--output`, `--print`; exit 2 if the root is missing.
- **`scripts/verify_install.py`** (new): read-only, strictly-local verifier behind `nexus-hub verify`. Recomputes SHA-256 for each manifest entry against the installed tree and classifies each path **OK** (match), **MODIFIED** (hash differs), **MISSING** (manifest path absent on disk), **EXTRA** (present under a covered root but absent from the manifest). Prints non-OK entries plus an OK count (Output Minimization rule), then a single `verify: PASS` or `verify: FAIL (<n> modified, <n> missing, <n> extra)` line; exit 0 on PASS, 1 on FAIL, 2 when no catalog root or manifest is found. `--ignore-extra` reports EXTRA but does not let it cause FAIL. stdlib `hashlib` only; no network, no credential, no third-party dependency.
- **`scripts/nexus_hub_cli.py`** (edited): wired the `verify` subcommand into the `nexus-hub` CLI core - a lazy-import dispatcher (`cmd_verify`) plus a help-only subparser, and an argv-slice interception in `main()` that forwards everything after `verify` verbatim. Docstring subcommand list updated.
- **`scripts/installer.sh`** + **`scripts/installer.ps1`** (edited): explicit-name copy lines for `generate_manifest.py` and `verify_install.py` (to `~/.nexus-hub/scripts/`) and `MANIFEST.sha256` (to the install root), modeled exactly on the `nexus_hub_cli.py` block, in each installer's own convention (`safe_copy` + `[OK]` for bash, `Safe-Copy` + the file's checkmark for PowerShell).
- **`catalog/commands/update.md`** (edited): a new "release scope: supply-chain manifest (regenerate before the commit)" subsection plus the release-ordering lines now reading `... -> refactor -> manifest, then ... commit, tag, push, publish`, so `/update release` regenerates and stages `MANIFEST.sha256` after the version bump and before the commit.
- **`tests/validators/test_verify_install.py`** (new): 22-case pytest suite.
- **`README.md`** (edited): a "Verifying your install" subsection documenting `nexus-hub verify` and its local-only threat-model boundary.
- **`docs/v3/v3.10/known-gaps.md`** (edited): status advanced to Phase 4 complete; recorded `DF-v310-ruflo-P4-extensions` (the `extensions/` MCP-server sources are an intentional out-of-scope manifest boundary) and a note that the manifest is a release-time artifact, not committed mid-cycle.

## Key decisions / troubleshooting

- **Threat-model boundary = which tree `verify` checks (the plan's named failure mode).** The install root (`~/.nexus-hub`) does NOT mirror the repo layout - the installer fans the catalog out to per-platform locations - so verifying against it would report every `catalog/...` manifest entry as MISSING. The only coherent target is `~/.nexus-hub/src`, the 1:1 repo mirror the one-line bootstrap materializes (the same tree `nexus_hub_cli.read_installed_version` already reads `src/.claude-plugin/plugin.json` from). `resolve_catalog_root` therefore resolves to `<home>/src` (or an explicit `--root`) and deliberately does NOT fall back to the bare install root: being honest (exit 2 "no catalog root found, pass --root <checkout>") beats a wall of false MISSING that would train users to ignore the tool. The manifest rides inside the release tag (committed at the repo root, so it lands at `src/MANIFEST.sha256`); verify prefers that co-located copy and falls back to the installer-dropped `<home>/MANIFEST.sha256`.
- **Single source of truth for scope.** Rather than letting the generator and verifier each define "what is covered" and risk drift, `COVERED_ROOTS` + the exclusion predicate + `iter_catalog_files` + `parse_manifest` live in `generate_manifest.py` and the verifier imports them - the same discipline that makes both reuse `manifest._hash_path` instead of re-hashing.
- **No `.ps1` sibling (NI-v24-1).** Both new scripts are stdlib-only single `.py` files, and the existing `nexus-hub.cmd` Windows launcher already dispatches to the shared CLI core, so `nexus-hub verify` works on Windows for free. Adding a `.ps1` would duplicate logic against the convention; the parity rule (a `.ps1` per `.sh`) does not apply to a `.py`.
- **`argparse.REMAINDER` bug -> argv slicing.** A `verify` subparser using `nargs=REMAINDER` dropped a leading `--ignore-extra` (argparse matches it against the parent parser first). Fixed by intercepting `raw[0] == "verify"` in `main()` before argparse runs and forwarding `raw[1:]` verbatim to the verifier; the subparser is kept only so `nexus-hub --help` lists `verify`.
- **Lazy import keeps the outbound invariant intact.** `cmd_verify` imports `verify_install` lazily inside the function (after putting the CLI dir on `sys.path`), so importing the network-capable `nexus_hub_cli` module does not pull in the verifier, and the existing test that scans the CLI source for "only the project's own GitHub" outbound calls stays valid.
- **Manifest is a release-time artifact, not committed mid-cycle.** Generating and committing it on `develop` would leave it stale after the next phase edits a covered file. So it is wired into `/update release` (regenerated after the version bump, before the commit) and is NOT committed in this phase; `develop` checkouts have no manifest and `verify` cleanly reports exit 2 until a release produces one. Recorded in known-gaps. `.gitignore` does not match `MANIFEST.sha256` at the repo root (no `*.sha256` pattern; the `.nexus-hub/` patterns match only that directory), so the release-time commit will succeed.
- **`extensions/` out of manifest scope.** The MCP-server sources are pip-installed into a venv at install time, and including their trees would pull in venv/build churn that destabilizes the deterministic manifest. Recorded as `DF-v310-ruflo-P4-extensions` (severity Low; the highest-value tamper surface - skills, commands, hooks, scripts - is covered).
- **CHANGELOG and catalog-count reconciliation deferred to Phase 6** per the plan's phasing (Phase 4 adds no skills; counts unchanged).

## Verification (quality gate: GO)

`make` is not on PATH (WN-v33-1), so the gate ran via its documented Windows equivalents.

- **Manifest determinism**: `generate_manifest.py` run twice produced byte-identical output (1100 entries); `sha256sum -c MANIFEST.sha256` from the repo root reports ALL OK (exit 0). Format confirmed: 64-hex digest, two-space text-mode separator, relative POSIX path.
- **Verify classification + exit codes**: clean tree -> `verify: PASS` exit 0; one modified file -> `MODIFIED <path>` + `verify: FAIL` exit 1; one deleted file -> `MISSING <path>` + FAIL; one added file -> `EXTRA <path>` + FAIL; `--ignore-extra` clears the EXTRA-only FAIL -> PASS exit 0; no manifest / no `src` root -> exit 2. Exercised both directly and through the `nexus-hub` CLI (`nexus_hub_cli.py verify ...`).
- **Dry-run install (installed-layout path)**: simulated the documented installer copy step into a throwaway `~/.nexus-hub` (scripts to `scripts/`, `lib/` beside them, launcher to `bin/`, manifest at the install root), then ran `nexus-hub verify --root <repo>` through the installed launcher -> `verify: PASS` exit 0, confirming the installed-layout imports (`from lib.integrations.manifest`, `from generate_manifest`), the launcher dispatch, and the home-level manifest read all work. (The full installer is not run on the Windows dev host per WN-v36-1 and would mutate global state; the copy lines themselves are asserted statically by pytest, matching the repo's existing `test_upgrade_cli.py` convention for installer wiring.)
- **No-outbound invariant**: grep of both new scripts for `curl`/`wget`/`requests`/`urllib`/`socket`/`http`/`urlopen`/`httpx`/`aiohttp` -> zero matches; stdlib `hashlib` only; no new pip/npm dependency.
- **ShellCheck**: `scripts/installer.sh` + `install.sh` clean at `--severity=warning`.
- **CI validators**: `validate_unicode_safety`, `validate_no_personal_paths`, `scan_supply_chain_iocs`, `check_version_sync` all exit 0; zero findings in any Phase 4 file (root `README.md`, both new scripts, the CLI core, both installers, `update.md`, the test are all ASCII-clean); no version surface touched.
- **pytest**: the new `tests/validators/test_verify_install.py` (22 cases) all pass; the existing `tests/installer/test_upgrade_cli.py` (24 cases) still passes (the `main()` change is backward-compatible). Full repo suite (`pytest tests`): 598 passed, 15 skipped, 1 pre-existing environmental failure (see below).
- **Attribution grep**: zero matches in distributed artifacts for `ruflo` / `AIDefence` / `AgentDB` / `RuVector` / `SONA` / `ReasoningBank` / `MetaHarness` / `rvf` / `rvagent` / `ruv.io`. (`ruflo` appears in `docs/v3/v3.10/known-gaps.md` and the DEVLOG only as the cycle/plan identifier, which the attribution rule permits for internal docs.)
- **Changed-file scope**: `git status --short` shows exactly the Phase 4 surface (5 modified, 3 new) and no stray `MANIFEST.sha256` in the tree.

### Pre-existing, out-of-scope finding (not introduced by and not fixed in this phase)

`tests/installer/test_bootstrap.py::test_ps_standalone_extracts_and_hands_off` FAILS with a Windows `tar: unexpected end of file` / `status 128` extraction error. That test stubs out `installer.ps1` entirely and exercises the root `install.ps1` bootstrap (which Phase 4 does not touch); the failure reproduces identically with the Phase 4 edits stashed, confirming it is a pre-existing environmental issue on the Windows dev host (the WN-v36-1 class), not a regression.

## Files changed

- `scripts/generate_manifest.py` (new)
- `scripts/verify_install.py` (new)
- `scripts/nexus_hub_cli.py` (verify subcommand wired in)
- `scripts/installer.sh` (copy lines for the two scripts + the manifest)
- `scripts/installer.ps1` (mirror copy lines)
- `catalog/commands/update.md` (release-flow manifest sub-step)
- `README.md` ("Verifying your install" section)
- `tests/validators/test_verify_install.py` (new; 22 cases)
- `docs/v3/v3.10/known-gaps.md` (Phase 4 status; DF-v310-ruflo-P4-extensions; release-artifact note)
- `docs/v3/v3.10/plans/adoption-ruflo.md` (Phase 4 exit checklist checked off)
- `docs/DEVLOG.md` (Phase 4 entry)
- `docs/archive/v3/v3.10/development/history/2026-06-30_adoption-ruflo-phase-4-nexus-hub-verify-supply-chain.md` (this file)

## Next

Phase 5: agent-setup grade + regression diff (re-partial, P2). Extend `scripts/harness_audit.py` with a single explainable 1-100 setup grade (presence/freshness of instruction files, skill/command/hook coverage, registry consistency, security hooks, validator health) and a cross-snapshot regression diff (`--snapshot` / `--diff`, advisory by default, `--fail-on-regression` to gate), surfaced through the `skill-stocktake` skill. The manifest-style local-file conventions established here (a deterministic, documented local store) can inform the snapshot format. CHANGELOG `## [Unreleased]` and the catalog-count reconciliation remain consolidated in Phase 6 per the plan's phasing.
