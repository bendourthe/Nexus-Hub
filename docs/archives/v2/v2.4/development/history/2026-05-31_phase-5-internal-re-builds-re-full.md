# Session History - v2.4.0 (adoption-compound-engineering-plugin) Phase 5: Internal RE Builds (re-full)

**Date**: 2026-05-31
**Plan**: [docs/archives/v2/v2.4/plans/adoption-compound-engineering-plugin.md](../../plans/adoption-compound-engineering-plugin.md)
**Phase**: 5 of 8 - Internal RE builds, re-full (A6 per-platform capability specs, A9 installer branch-based testing)
**Sub-tasks**: T020 (per-platform specs under docs/specs/), T021 (installer --branch / -Branch flag), T022 (testing + stabilization)
**Outcome**: Authored a `docs/specs/` index plus 8 per-platform capability specs derived from the live integration registry; added a `--branch <name>` (Bash) / `-Branch <name>` (PowerShell) installer flag that installs from a shallow clone of a pushed branch in a deterministic cache dir, leaving the user's working copy untouched. Both installers parse-clean; 70/70 installer tests pass (incl. 7 new branch-flag probes and the unchanged enterprise/check/init/traversal suites); specs match the live config 20/20. Live --branch clone+install deferred (DF-v24-5). No new skills; registries unchanged at 244.

---

## Goal

Build the two re-full internal artifacts: per-platform capability reference docs reconstructed from Nexus-Hub's own integration registry (A6), and a branch-based installer testing affordance that clones and installs from a pushed branch without switching the user's checkout (A9). Both are fully local; no new outbound call, no new credential, no new dependency.

## Steps taken

1. **Phase 0 - resolve plan / phase**: parsed `5 of docs/archive/v2/v2.4/plans/adoption-compound-engineering-plugin.md`; legacy flat layout. Phase 5's prerequisite is "None". Phases 1-4 closed (Phase 3 finalized + committed `cd72280` immediately before this run). Final-phase detection: false (5 of 8; Phases 6-8 open).

2. **Phase 1 - pre-implementation review**: read `scripts/lib/integrations/base.py` to learn the `config` contract (`global_dir`, `workspace_dir`, `instruction_workspace_dir`, `instruction_file`, `instruction_template`, `instruction_mode`, the `*_subdir` keys, `hooks_supported`, `permissions_file`), then dumped every registered integration's `describe()` config from `INTEGRATION_REGISTRY` (10 keys). Read the `installer.sh` flag-parsing loop + main entry (REPO_ROOT from `BASH_SOURCE`, read-only dispatch for init/print-config/check) and the matching `installer.ps1` param block + main dispatch (`$repoRoot = Resolve-Path "$PSScriptRoot\.."`). Reviewed `tests/installer/` (test_enterprise_flag static checks, test_check_flag subprocess/runner patterns) for the test convention.

3. **T020 - per-platform specs**: wrote `docs/specs/README.md` (index + distribution-tier explainer) plus 8 specs (`claude-code`, `codex`, `gemini`, `antigravity`, `copilot`, `cursor`, `opencode`, `nexus-ai`). Each documents the install surface (global + workspace dirs), the distributed content (which catalog subtree maps to which subdir), the instruction file + template + merge mode (`shared` marker-merge vs `nexus-ai`'s `dedicated`), and platform quirks (slash surface, hooks support, the Gemini CLI 2026-06-18 sunset, the Antigravity `agy` CLI + four doc-verified residuals, Copilot/Cursor guardrails-only). Content derived directly from the live config dump (not from the upstream comparison source).

4. **T021 - installer --branch flag (lockstep)**: added `--branch <name>` / `--branch=<name>` to `installer.sh` and `[string]$Branch` to `installer.ps1`, plus a shared sanitizer (`sanitize_branch_name` / `Get-SanitizedBranchName`) that maps a branch name to a filesystem-safe token (non-`[A-Za-z0-9._-]` -> `-`, parent-dir tokens neutralized, leading dot/dash stripped). When `--branch` is set and `NEXUS_HUB_BRANCH_RESOLVED != 1`, the installer resolves the cache dir (`~/.nexus-hub/branches/<token>/`) and the clone source (`git remote.origin.url`, falling back to the local repo path); with `--check` / `-Check` it prints the resolution and exits 0 (a clone-free probe); otherwise it shallow-clones (or fetches into an existing cache), then re-execs the cached installer with `NEXUS_HUB_BRANCH_RESOLVED=1` (passing through `--enterprise` / `-Enterprise`). Documented in `--help` / `-Help`, in `README.md` (a Branch-based install paragraph + a `docs/specs/` pointer), and covered by `tests/installer/test_branch_flag.py` (7 probes: static surface for both installers, bash + PowerShell cache-path resolution, traversal neutralization, empty-value error).

5. **T022 - stabilization**: ran the validators directly (make unavailable on host), the full installer test suite, and a programmatic spec-vs-config spot-check; recorded the live-clone deferral (DF-v24-5); ran the post-phase documentation sequence.

## Troubleshooting

- **Bash `set -e` only (no `-u`)**: confirmed before using `${PASSTHRU_ARGS[@]+"${PASSTHRU_ARGS[@]}"}` for the re-exec passthrough; the safe-expansion form is harmless and future-proofs against a later `set -u`.
- **Probe output carries a terminal-title escape**: the installer emits a `]0;Nexus-Hub Installer` title sequence at load; the branch tests assert on substrings (`branches/feature-login`, `sanitized:`) so the escape does not affect them.
- No functional bugs surfaced this phase; the bash probe and PowerShell probe both produced identical resolutions on the first run.

## Assumptions

- T020's 8 specs map the plan's 8 platform names; the two multi-key platforms group their keys (antigravity covers `antigravity` 1.0 + `antigravity2` 2.0/CLI; gemini covers `gemini` + `gemini-cli` enterprise). Content is derived from the live `INTEGRATION_REGISTRY` config rather than the upstream comparison, satisfying the reverse-engineer-from-our-own-knowledge intent.
- The `--branch` probe (`--check`) is the operative T022 acceptance bar; the live clone+install path is deferred to DF-v24-5 (heavier; needs a pushed branch).
- The new `test_branch_flag.py` lives in `tests/installer/`, which CI already runs (`pytest tests/installer`), so no CI config edit is needed; the modified `installer.sh` is already covered by the CI shellcheck job.
- `make` / shellcheck are unavailable on the Windows host, so validators ran directly and shellcheck is N/A (CI lints `installer.sh`); `bash -n` and PowerShell `PSParser` both pass.

## Testing results

- `make validate` equivalent (direct): JSON catalogs OK (skills.json unchanged at 244), unicode-safety 0 errors / 1085 warnings (pre-existing compliance-template debt; the 9 new spec docs are ASCII-clean and added zero), no-personal-paths exit 0 (specs use `~` not real usernames), orphan-bundle PASS 0/0.
- `make lint`: `bash -n scripts/installer.sh` OK; PowerShell `PSParser` parse OK on `installer.ps1`; shellcheck not installed on host (CI lints `installer.sh`).
- Installer suite (`tests/installer`): 70 passed, including 7 new `test_branch_flag.py` probes and the unchanged enterprise / check / print-config / init / path-traversal suites (confirms default behavior is unchanged when `--branch` is absent).
- **Spec-vs-config spot-check (PASS)**: for all 10 integration keys, the documented `instruction_file` and `workspace_dir` appear in the matching spec doc (20/20).
- **Branch probe (PASS, bash + PowerShell)**: `--branch feature/login --check` -> `~/.nexus-hub/branches/feature-login`; `--branch ../../etc --check` -> sanitized `---etc` (no `..`); `--branch` with no value -> exit 2.

## Deviations

- **DF-v24-5**: the live `--branch` clone + re-exec + install path was verified only via the clone-free dry-run probe; the end-to-end run (real pushed branch, cache populate, re-exec without re-clone, full install, working copy untouched) is deferred. Foldable into the Phase-8 cross-OS smoke (T039) or a maintainer pre-release check.
- No new skills, so no `data/` registry edits; the registries stay reconciled at 244 / workflow 35. No README / AGENTS.md count-prose edited (deferred to bump per WN-v24-1).
- No `# DEVIATION:` markers were left in any artifact; the plan was followed as written.

## Next steps

- Phase 6 (internal RE builds - re-partial) follows: a local demo-capture skill (A12, upload step dropped) and a conventional-commit release/changelog script (A13).
- Phase 8 T039 should fold in the live `--branch` clone+install verification (DF-v24-5) alongside the cross-OS installer smoke.
- At the version bump, update the AGENTS.md / README.md count prose and regenerate the embedded SKILL INDEX (WN-v24-1).
