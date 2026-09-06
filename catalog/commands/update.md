---
description: Sync a repo to its current state and, at release scope, ship it - documentation, devlog, gitignore, version bump, changelog, refactor, config repair, commit message, and the full release flow. Use to "update the docs", "bump the version", "write the changelog", "sync the devlog", "refactor the project layout", "fix my config", "prepare a release", "commit this", "ship v3.0.0". SKIP - authoring a brand-new doc from scratch (use the relevant generator) or reviewing without changing anything (use /review).
---

# /update Command

Sync a repository to its current state and, at `release` scope, ship it. `/update` consolidates every "bring the repo up to date" action: documentation and README, devlog, gitignore, version bump (atomic across every version-carrying surface), changelog, docs/project refactor, platform-config repair, commit message, and the end-to-end release flow that commits, tags, pushes, and publishes the GitHub Release. Bare invocation asks for a scope.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive logic lives in the retained skills; this file resolves scope and delegates. `/update release` is the flow `/implement` hands off to on a plan's final phase.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `docs`, `devlog`, `gitignore`, `version`, `changelog`, `refactor`, `config`, `commit`, `release`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. release   (recommended) - the full ship flow: docs + gitignore + version + changelog + devlog + refactor, then commit, tag, push, publish GitHub Release
        2. docs      - sync README, API docs, architecture docs, inline guides
        3. devlog    - refresh the DEVLOG index line for the current release
        4. gitignore - audit .gitignore, clean the index, recommend LFS
        5. version   - bump the version atomically across every surface (drift-guarded)
        6. changelog - regenerate / extend CHANGELOG.md from git history
        7. refactor  - reorganize docs/ and project artifacts to conventions
        8. config    - validate and repair installed platform configs (drift repair)
        9. commit    - generate a structured commit message for the staged changes

      Reply with a number or a scope name.

- `release` first verifies the integration gate (below), then runs the focused scopes in order - `docs`, then `gitignore`, then `version`, then `changelog`, then `devlog`, then `refactor` - then reconciles the version's known gaps, RE-CHECKS CI/CD conformance, regenerates the supply-chain manifest, cleans up, commits, tags, pushes, and publishes the GitHub Release as one flow. It keeps every confirmation gate: never create a tag, push, or publish a release without explicit user confirmation.
    - The CI/CD step is a CONFORMANCE RE-CHECK, not an authoring pass. The plan's final phase already ran the terminal reconciliation via `[[cicd-architect]]` before it published; by release time the pipeline is reconciled and this step confirms it still is. If it finds unreconciled drift, that is a finding against the plan's final phase, and the fix belongs there rather than in a release-time rewrite of the pipeline.

## Delegation

Dispatch the resolved scope to the retained skill(s). These targets are skills under `catalog/skills/`, NOT the consolidated-away v3.x commands: the old command names (`/update-documentation`, `/generate-readme`, `/update-devlog`, `/generate-changelog`, ...) were removed in v3.2.0 and no longer resolve, so never delegate to them.

      docs      -> user-documentation (README + guides) + technical-documentation (architecture / ADRs) + documentation-consistency (link / staleness / sync audit); see the docs-sync checklist below
      devlog    -> devlog-generation (ONE index line per release, not a narrative entry; see the devlog scope below)
      gitignore -> built-in (audit .gitignore, clean the tracked index, recommend LFS for large binaries)
      version   -> version-upgrade, gated by scripts/check_version_sync.py (see below)
      changelog -> release-notes-writer (parse git history since the last tag into a CHANGELOG entry)
      refactor  -> docs-layout-refactor + project-refactor (per-version docs structure + archive normalization + empty-dir/duplicate/orphan/structure-complexity detectors; see the refactor scope below)
      config    -> update-config (built-in) + config-consistency-checker / nexus-hub doctor (see below)
      commit    -> code-commit-workflow
      release   -> integration gate (see below) -> docs -> gitignore -> version -> changelog -> devlog -> refactor (docs structure + cleanliness) -> known-gaps reconciliation -> CI/CD conformance re-check -> manifest, then clean up, commit, tag, push, publish GitHub Release (see below)

Pass any remaining arguments through unchanged. Heavy logic stays in the retained skills; this file owns only scope resolution and the release sequencing.

## docs scope (feature-level sync, not just counts)

The `docs` scope MUST refresh documentation CONTENT to the repo's current state, not merely bump version strings and counts (the atomic version bump is the `version` scope's job). Before finishing `docs` -- and therefore before every `release` -- reconcile each item below against the actual catalog and the latest `CHANGELOG.md` entry, and FIX any drift found:

- **Headline counts**: skills / commands / hooks / agents / rule-families in `README.md` and `AGENTS.md` match `data/skills.json` and the registries.
- **Internal MCP server list**: the README's "internal MCP servers" enumeration matches the `nexus-*` servers actually registered in `catalog/mcp-configs/mcp-servers.json` -- both the COUNT and the NAMES (e.g. when `nexus-context-compressor` was added in v3.2.0 the README still read "3 internal MCP servers").
- **"What's New" narrative**: the README has a section summarizing the headline features of the release being shipped. Do NOT leave the latest release undocumented -- a release whose only README change is the version/count bump has skipped this step (the exact failure the v3.2.0 release hit).
- **Removed / renamed surfaces**: no doc still presents a command, skill, flag, or path removed or renamed since the last release as if it were current.
- **Per-version docs structure**: the active version's `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` tree exists with `plans/` and `comparisons/` subdirs per the `[[docs-layout-refactor]]` Version-directory resolution scheme; create or repair it (and relocate any stray comparison reports into `comparisons/`) if not.
- **Handbook markdown against the code**: refresh `docs/handbooks/markdown/` so it describes current `main`, not just README counts. If generated `html/` exists and disagrees, regenerate or record the miss. Do not invent `docs/testing/` or `docs/validation/`.

When the scope is `release`, run this reconciliation as the FIRST step, before the version bump. A release whose only documentation change is the version/count bump has not run `docs`.

## docs and changelog scopes: Unicode hygiene (detect-first)

After writing or editing Markdown in the `docs` or `changelog` scope, check each touched file:

```bash
python scripts/validate_unicode_safety.py --strict --root . --path <file>
```

Detect here rather than fix, because these scopes routinely touch hand-edited prose whose punctuation may be deliberate, and an automatic rewrite would silently overrule the author. Resolve what the report names before finishing the scope: re-run with `--fix` on that file once the findings are confirmed unintentional, or edit by hand when a character is there on purpose (rewording an em-dash clause usually reads better than substituting `--`). The `release` scope is the one place this becomes an automatic fix-and-block gate, because a release artifact has no author left to consult.

Note that a `--path` which does not resolve under `--root` exits 2 rather than reporting a clean scan, so a mistyped path fails loudly instead of passing while checking nothing.

## devlog scope (one index line, never a narrative entry)

`docs/DEVLOG.md` is a bounded per-release **index**, not an append-only log: a short header plus one line per release carrying the date, version, a one-sentence summary, and links to that release's plan, `development/history/` directory, and `known-gaps.md`. `[[devlog-generation]]` owns the format contract; this command only decides when it runs.

Two consequences for the release flow:

- **`devlog` runs after `version` and `changelog`, not before.** The index line is keyed by the released version and dated by its changelog heading, so running it earlier would mean guessing both. This is why the release order changed in v3.18.0; a narrative entry needed neither.
- **An existing line for the version is updated in place.** Re-running the scope on the same release must be idempotent. Two lines for one version is a defect, because a reader cannot tell which is current.

Narrative content never goes here. A phase's story, its troubleshooting trail, and its decisions belong in the per-version `development/history/` file via `[[session-history]]`, and what changed belongs in `CHANGELOG.md`, which stays the authoritative record.

## version scope (atomic, drift-guarded)

The `version` scope MUST use `scripts/check_version_sync.py` so every version-carrying surface is bumped as one atomic set: `.claude-plugin/plugin.json` (canonical), `scripts/installer.sh` (`NEXUS_HUB_VERSION`), `scripts/installer.ps1` (`$script:NexusHubVersion`), `data/marketplace.json`, the latest `CHANGELOG.md` heading, and the README / AGENTS.md catalog-version prose. Run the guard before and after the bump: it must report a clean in-sync tree afterward. This closes the v2.4.0 drift class (installers stuck at one version while `plugin.json` moved to the next) systemically - a mismatch fails the build rather than shipping.

## release scope: supply-chain manifest (regenerate before the commit)

After every version-carrying surface is bumped (`version`) and the docs / changelog / refactor scopes have run, regenerate the supply-chain manifest so it reflects the exact bytes being released, then stage it into the release commit (before the tag is cut). Run `python scripts/generate_manifest.py`, which writes `MANIFEST.sha256` at the repo root over the distributed catalog tree (`catalog/`, `templates/`, `scripts/`, `data/`) in `sha256sum -c` text format. This MUST run after the version bump so the manifest hashes the bumped files, and before the commit so the manifest ships inside the release tag (and therefore inside the `~/.nexus-hub/src` tree the install bootstrap materializes). The manifest is what `nexus-hub verify` later diffs the installed catalog against; a release whose manifest is stale or missing leaves `verify` unable to confirm an install. The generator is strictly local (stdlib `hashlib`, no outbound call) and deterministic (sorted by path), so re-running it on an unchanged tree is a no-op diff.

Two properties of the generator worth knowing at release time, both learned from shipped defects. It hashes a tracked file's GIT BLOB bytes passed through the path's `eol` attribute, which is the DISTRIBUTED form, so the manifest no longer depends on the generating host's `core.autocrlf` (v3.16.7 `WN-1`) and correctly covers a path declared `text eol=crlf` (v3.16.8 `BG-2`). Two consequences: **stage before generating**, because tracked-but-unstaged edits are hashed as their staged form (the tool warns and names the dirty covered paths); and **a `.gitattributes` edit is a manifest-affecting change**, since altering an `eol` attribute alters the distributed bytes for every path it covers, so regenerate after one. The artifact round-trip gate below is what proves the result against the real download.

## release scope: the integration gate (the FIRST check, before any version mutation)

`release` starts only from a GREEN, MERGED integration result. Verify all four before touching a single version-carrying file:

1. **The plan branch is integrated.** Its pull request merged into the integration branch. An unmerged branch means the release would ship a tree that was never reviewed as a whole.
2. **Integration CI is green.** Every required check on that pull request reached success, and the post-merge work (if any) succeeded. A pending check is not a green check.
3. **The working tree is clean** and the local integration branch matches its remote.
4. **Release notes are approved from the ACTUAL diff.** Derive them from the real `<last-tag>..<integration-branch>` range and present them for approval before any mutation. Notes written from the plan rather than the diff describe what was intended, not what shipped.

If any of the four fails, STOP and say which one. Do not bump a version to "get the release moving": a version bump is the point after which every subsequent step assumes the release is happening, and unwinding it is more work than waiting.

This ordering is the release-side half of the plan lifecycle. The plan's final phase owns publication and integration; `/update release` owns everything after the merge lands green. Neither reaches into the other.

## release scope: pre-tag branch assertion (the LAST check before `git tag`)

Immediately before `git tag`, and after nothing else, run:

```bash
python scripts/check_release_preconditions.py --pre-tag [--release-branch main]
```

It exits 1 and prints `BLOCKED` unless HEAD is on the expected release branch AND equal to `origin/<release-branch>`. **Abort the release on a non-zero exit. Do not tag.**

This exists because of a specific failure, and its placement is the whole point. In the v3.17.5 release a `git checkout main` failed on a OneDrive-locked directory, HEAD stayed on an unrelated branch, and the tag was created there and published, shipping an unreleased plan file inside the release tarball. A check placed anywhere earlier in the flow cannot catch that: a checkout that failed silently is exactly the state being guarded against, so the assertion has to read live git state at the last possible moment. Re-running it after any retry is cheap and correct.

The expected branch is configurable rather than hardcoded to `main`, because a gate that blocks a legitimate release from a differently-named release branch is a gate people learn to bypass, which is how the whole v3.17.6 defect class started.

## release scope: post-release back-merge (after the merge to the release branch)

After the release merges into the release branch, merge it back into the integration branch:

```bash
git checkout develop && git merge --no-ff main && git push
```

A PR-based release leaves a merge commit on `main` that `develop` does not have. Under `strict` branch protection ("require branches to be up to date"), that missing commit blocks the NEXT release PR until someone back-merges by hand, which is a self-inflicted delay discovered at the worst moment. Keep the existing confirmation gate: this pushes to a protected branch.

## release scope: branch hygiene and repository settings (advisory, before the commit)

```bash
python scripts/check_release_preconditions.py --branches --repo-settings
```

Advisory only, exit 0 regardless. Three reports:

- **Merged remote branches.** Listed as cleanup candidates using local `git branch -r --merged` only, with no network call. It NEVER deletes anything, and never proposes a protected branch or one with an open PR: a merged branch is sometimes still wanted, and a release flow is the worst moment for a surprise deletion. Delete what you no longer need, by hand.
- **Branches surviving a CLOSED, unmerged PR.** A separate category, and on a repository with `delete_branch_on_merge` enabled it is the only accumulation left. GitHub deletes a branch when its PR MERGES and does nothing when a PR is closed unmerged, so `git branch -r --merged` reports a clean tree while stale refs pile up. Nexus-Hub found this on itself: the merged list was empty while ten stale branches sat on the remote. Needs `gh`; silent without it.
- **`delete_branch_on_merge`.** Reported when `gh` is available and authenticated, with the exact `gh repo edit --delete-branch-on-merge` command to enable it. **Nexus-Hub cannot set this on a user's repository at install time**: the installer holds no credentials, and acquiring any would breach the zero-outbound policy. Note also that the setting does NOT remove a branch whose PR was CLOSED unmerged, so throwaway branches still need manual cleanup.
- **Repository description drift.** The GitHub repository DESCRIPTION is not a version-carrying surface, so `check_version_sync.py` cannot see it and it drifts silently across releases. Nexus-Hub's own read "256 curated skills, 15 commands, 22 hooks" against an actual catalog of 273 skills. Only the skills count is authoritative (`data/skills.json` has exactly one entry per skill); commands and hooks are reported as HEURISTIC file counts that include aliases and helpers, so **confirm the intended figure before editing the description and do not copy the heuristic number**. The check self-gates to a no-op on a repository with no catalog.

## release scope: GitHub Release publishing (final step, after push)

After the tag is pushed, `release` publishes a GitHub Release for the new `vX.Y.Z` tag so the repo's Releases page (and the "latest release" badge / sidebar) tracks the tag. **Pushing a git tag does NOT create a GitHub Release** -- they are separate objects -- so omitting this step silently leaves the Releases page behind the tags (the exact drift that left the page at v3.5.0 while the v3.6.0 and v3.7.0 tags already existed). This step runs last because it requires the tag to be on the remote first.

- **Body = the finalized CHANGELOG section.** Use the `## [X.Y.Z]` block just written to `CHANGELOG.md` as the release notes, and reuse the tag annotation's one-line summary for the title (`vX.Y.Z - <summary>`).
- **Prefer `gh`, degrade gracefully (never fail the release).** If the GitHub CLI is present and authenticated (`gh auth status` succeeds), run `gh release create "vX.Y.Z" --title "vX.Y.Z - <summary>" --notes-file <file-holding-the-changelog-section>`. If `gh` is absent or unauthenticated, do NOT fail or roll back -- the tag and push already succeeded, so the Release can be published at any later time. Print the exact commands for the user to run: the `gh release create ...` form, plus a no-`gh` fallback (`curl -X POST -H "Authorization: Bearer <token>" https://api.github.com/repos/<owner>/<repo>/releases -d '{"tag_name":"vX.Y.Z","name":"vX.Y.Z - <summary>","body":"<notes>"}'`).
- **Idempotent.** If a Release for `vX.Y.Z` already exists, update it in place (`gh release edit "vX.Y.Z" --title ... --notes-file ...`) instead of erroring.
- **Confirmation gate.** Publishing is outward-facing, so follow the active instruction template's `Consequential Decisions` rule before confirming creation or editing of the Release -- the same gate the tag and push already carry. Never publish without explicit user confirmation.
- **Backfill.** When the Releases page is behind the tags (a tag exists with no matching Release), the same step publishes the missing Release(s) from each tag's CHANGELOG section -- run it per missing `vX.Y.Z`.
- **Path trap on a Bash-style shell.** `gh` is a native Windows binary and cannot read a Git-Bash `/tmp/...` path, so `--notes-file` (and `--dir`) need a native Windows path when the release is driven from Bash. A `/tmp` path fails with "The system cannot find the file specified."

## release scope: artifact round-trip (the FINAL gate, after publish)

Verify the release against the artifact a user actually downloads. This is the last gate in the flow and it exists because v3.16.7 passed every other check and still shipped a manifest that made `nexus-hub verify` report FAIL: every earlier check ran against a LOCAL reconstruction of the artifact (the index, the working tree), and each of those shares its assumptions with the generator it was checking. Only the published artifact is independent of them.

```bash
gh release download "vX.Y.Z" --archive=tar.gz --dir <native-path>
tar -xzf <native-path>/<repo>-X.Y.Z.tar.gz -C <native-path>
python scripts/verify_install.py --root <native-path>/<repo>-X.Y.Z
```

Expect `verify: PASS` with 0 modified, 0 missing, 0 extra.

- **It never fails the release.** By this point the tag is pushed and the Release is published, so an unavailable `gh`, no network, or a slow download means printing the commands for the user to run later -- the same degradation posture the publish step already carries.
- **A FAIL here is a known-gaps entry plus a follow-up patch, NEVER a history rewrite.** The release is already public. Record the finding with its measured evidence (which files, which hashes) and fix it in the next patch. Do not retag, force-push, or delete a published Release to hide it.
- **A pre-release local check is possible, but it MUST pin the line-ending config.** To check before publishing, archive the index (`git write-tree` then `git archive <tree>`) rather than trusting the working tree -- but pass `git -c core.autocrlf=false -c core.eol=lf archive ...`. Without those, a Windows host applies CRLF to every `text=auto` file and the check reports mass false mismatches (about 1180 of 1231 on this catalog) that look catastrophic and mean nothing. GitHub generates its tarballs on Linux, so those two settings are what make a local archive comparable to the published one. A path with an EXPLICIT `eol=crlf` attribute is host-independent and converts either way, which is exactly why the manifest generator models the attribute rather than the host.

## config scope (platform-config drift repair)

The `config` scope validates installed platform configs and repairs drift, reusing the `config-consistency-checker` skill / `nexus-hub doctor`. In particular, a Codex `~/.codex/config.toml` that defines `[permissions.*]` profiles MUST set `default_permissions`, or the config fails to load. Repairing an already-broken user config (a `[permissions.*]` table present but `default_permissions` missing) requires TOML-aware insertion of `default_permissions` before the first `[permissions...]` table, and the idempotency guard must NOT skip such a config - it is broken, not already-fixed. When Codex's elevated-sandbox setup fails on Windows, optionally surface the `[windows] sandbox = "unelevated"` recommendation.

## refactor scope (docs structure + project cleanliness)

The `refactor` scope delegates to `[[docs-layout-refactor]]` (the `docs/` tree) and `[[project-refactor]]` (everything else), and enforces the v3.11.0 governance:

- **Whole docs-tree migration (any repo)**: migrate the ENTIRE docs tree - every version directory AND the archive, not just the active version - to the `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/` scheme (with `plans/` and `comparisons/` subdirs). Reshape any flat `docs/<vSEMVER>/` or old three-level `docs/versions/v<MAJOR>/<vSEMVER>/` directory into `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`, merge patch releases into their shared minor dir, relocate stray comparison reports into `comparisons/`, normalize `docs/archives/` to `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/`, and repair every internal reference. This generalizes to ANY repo: `/update refactor` (and, at release, `/update release`) canonicalizes that repo's whole docs tree via the `[[docs-layout-refactor]]` `--canonicalize-layout` path, so a project adopting Nexus-Hub gets the same migration with one command.
- **Living docs canonicalize**: if `docs/handbooks/` or `docs/decisions/` is missing, scaffold the required living tree (detection-first; never overwrite inherited files). Do not invent `docs/testing/` or `docs/validation/`.
- **Project cleanliness**: run the `project-refactor` cleanliness detectors - empty directories (respecting `.gitkeep`), duplicate/redundant files, non-version orphans, and overcomplicated structure - propose-only, with the skill's confirmation gate.

Both delegate skills stay propose-then-apply; this scope surfaces the checks and defers the procedure to them.

## release scope: known-gaps, architecture refactor, and CI/CD (before the commit)

Beyond running the `refactor` scope, a `release` performs these governance steps before the release commit, each keeping its confirmation gate:

Before stopping for any governance confirmation below, follow the active instruction template's `Consequential Decisions` rule and explain what the proposed action changes, the alternatives including doing nothing, and the recommendation.

1. **Known-gaps reconciliation** via `[[known-gaps-tracker]]`: resolve, defer, or transfer each open item for the version and finalize the per-minor `known-gaps.md`.
2. **Full architecture refactor** via `[[project-refactor]]` (the empty-dir / duplicate / orphan / structure-complexity detectors) plus `[[docs-layout-refactor]]`, leaving a clean, intuitive layout.
2a. **Generated-doc regenerate-and-fail-on-stale**: discover every generated documentation surface and run its repository-owned generator in check mode, including `docs/handbooks/html/` from `docs/handbooks/markdown/` via `[[document-to-interactive-html]]` / `/presentify`. Fail the release when generated output is missing or stale. Self-gate to a no-op only when no generated documentation source exists.
2b. **Living-reference snapshot**: snapshot living reference sources, including `docs/handbooks/`, into `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/` at release close, with handbooks under `docs/archives/v<MAJOR>/v<MAJOR>.<MINOR>/handbooks/`. Name every snapshot for the version its content describes, not the release that merely prompted the copy. Require last-phase evidence (`<version_dir>/development/last-phase-evidence.md`) when a plan is in flight.
3. **CI/CD create/update/optimize**: ensure the pipeline covers every change in the release and is optimized to reduce action minutes (path filters, concurrency cancel-in-progress, caching, gating expensive-OS/matrix jobs) while keeping comprehensive testing.
4. **Platform read-contract re-verification** via `[[platform-contract-verification]]`: for a distribution catalog whose installer targets multiple external AI platforms, re-verify each supported platform's CURRENT skill/command/rule/hook discovery format (via targeted web searches) so the next release is guaranteed to surface the catalog everywhere. The skill self-gates: it does real work only in a repo that ships `docs/policy/platform-read-contracts.md` + `scripts/lib/integrations/` (i.e. Nexus-Hub itself) and is a silent no-op in any other project, so the release flow stays generic. On drift it updates the machine-readable `docs/policy/platform-read-contracts.json` (mirrored into the `.md` table), the affected integration adapter, and both installers, adds a CHANGELOG note, and re-runs `scripts/verify_platform_contracts.py`. It then re-stamps the JSON's `meta.verified_for_version` (+ `last_verified`) to the release version. This last step is mandatory, not advisory: `scripts/check_platform_contract_freshness.py` (in `make validate` and CI) fails the release the moment the version is bumped past the stamped value, so the release cannot ship on a stale contract. Degrades gracefully offline (record 'unverified this cycle').

5. **Installer parity hard gate**: when a repository ships more than one installer, run its declarative cross-installer parity checker (for Nexus-Hub: `python scripts/check_installer_parity.py`) in the same governance pass as `[[platform-contract-verification]]`. The platform-contract skill proves where each host reads; installer parity proves every supported operating system delivers the same artifacts, platforms, named capabilities, and documented external-tool fallbacks. This step self-gates to a silent no-op in single-installer repositories. It is a HARD gate: a broken installer makes an entire operating system's release unusable, so parity failure must stop the release rather than ride as an advisory note.

6. **Model-prompting-profile staleness check** via `[[model-prompting-research]]`: report whether the per-model prompting profile layer still matches the live model roster. Like step 4 it self-gates, doing real work only in a repo that ships the profile layer (`catalog/skills/ai-development/model-prompting-research/assets/profiles-index.json`) plus `[[model-routing]]`, and is a silent no-op in any other project. It enumerates the live roster via `model-routing`'s `enumerate-models` helper, passes those ids to `scripts/check_model_prompting_freshness.py --advisory`, and on DRIFTED prints a one-line note naming the added or removed models plus an offer to run `/tune-prompting` before releasing.

    **This step is ADVISORY, and that is the opposite of step 4 by design.** Read the contrast before changing it. The platform read-contract MUST be re-verified for the release being cut, so step 4 hard-gates and a stale contract fails the build. Prompting freshness is different: models ship on the vendor's clock, so gating it would let a model released on a Tuesday wedge every Nexus-Hub release until someone ran a research swarm. Therefore this step:

    - **never blocks the release.** `--advisory` exits 0 on every path, including DRIFTED, a missing bundle, a corrupt index, and no live roster.
    - **never re-stamps a freshness marker to force a pass.** Only a real research run may write `meta.last_verified`; re-stamping it here would fake currency and is the one action that would make the check worthless.
    - **is never wired into `make validate` or CI.** `check_model_prompting_freshness.py` is deliberately absent from both, unlike its structural sibling `verify_model_prompting_profiles.py`, which IS a hard gate on the layer's shape.
    - **degrades to a logged no-op offline.** No web tool means print the reason and continue; the verdict is UNKNOWN, not a failure.

    A future editor who "fixes" this into a blocking gate will couple the release clock to the model-release clock, which is the exact failure this design avoids.

    **Non-blocking is not the same as skippable: ENUMERATE THE ROSTER FIRST.** `check_model_prompting_freshness.py` takes model ids as arguments and reports `UNKNOWN: no live roster supplied, so drift cannot be determined` when it gets none. Run with no arguments it therefore always "passes" while verifying nothing, and recording that UNKNOWN as a satisfied step is indistinguishable from never running it. So:

    - Enumerate the roster BEFORE invoking the check (the `model-routing` `enumerate-models` helper, or the vendor docs directly), and pass the ids: `python scripts/check_model_prompting_freshness.py --advisory <id> <id> ...`.
    - The step's acceptable terminal outcomes are **IN SYNC** or **DRIFTED**. UNKNOWN is acceptable only when web access genuinely failed, and then it must be recorded WITH that reason, not as a clean pass.
    - **Also refresh the model map, which is a DIFFERENT artifact.** This step grades the prompting-profile layer (`profiles-index.json`). The tier-to-id map lives in `catalog/skills/ai-development/model-routing/references/last-known-model-map.json` and is what a future `/plan` reads as its offline fallback. Nothing else in the release flow refreshes it. In v3.16.7 the profile layer was IN SYNC while the map sat 11 days stale across two releases, missing a Gemini release and a Cursor model, so checking one and assuming the other is the observed failure. Refresh both, validate the map with `model-map.py validate <path>`, and record any tier-placement judgment as a judgment.

    Both artifacts stay non-blocking on the release itself; what changed is that the step must now produce a verdict rather than a shrug.

7. **Capability usage gate**: when the release introduces or materially changes an OPT-IN capability, workflow, managed skill, or host surface, the release notes MUST carry five elements for each affected surface. Shipping a switch without teaching the user how to operate it is how an opt-in surface becomes either unused or over-trusted.

    | # | Element | What it must state |
    |---|---|---|
    | 1 | **Activation** | The exact opt-in mechanism, verbatim and copy-pasteable: the env var and its accepted values, the installer flag in both shells, or the file the user must create. |
    | 2 | **Validation** | A minimum runnable command that reads back whether activation actually took effect, so the user confirms rather than assumes. |
    | 3 | **Rollback** | The exact disable / uninstall / revert path, including what activation already wrote and whether turning it off removes those artifacts. |
    | 4 | **Authority boundary** | What activation does NOT grant - the privilege, data access, or scope a user might reasonably infer from the feature's name but that turning it on does not confer. |
    | 5 | **Documentation link** | A canonical versioned link to where the surface is documented in full. |

    **Element 4 is the one most often skipped and the one whose absence does the most damage.** Elements 1 through 3 fail loudly: a user who cannot activate a surface, cannot verify it, or cannot turn it off finds out immediately. An unstated authority boundary fails silently, by letting a user over-trust a surface they enabled - which is the failure mode with no error message.

    Nexus-Hub ships an unusually high density of these surfaces, so the gate is grounded in real ones rather than stated abstractly. Use them as the worked examples:

    - `NEXUS_HUB_COPILOT_SKILLS` - off by default; writing `.github/skills/` is commit-visible, which is exactly the kind of consequence element 4 exists to surface.
    - `--enterprise` / `-Enterprise` - the installer flag gating the Gemini CLI integration, and a case where activation differs per shell, so element 1 must give both forms.
    - `NEXUS_DISABLED_HOOKS` and `NEXUS_HOOK_PROFILE=minimal` - per-session hook suppression, where element 4 must be explicit that suppressing a guardrail hook does not make the underlying action safe.

    **Scope it tightly.** The gate applies ONLY to opt-in surfaces, never to every changed line, and it is not a checklist to run against the diff. A release that changes no opt-in surface satisfies the gate with one explicit declaration in the release notes ("This release changes no opt-in capability, installer flag, or host surface"), which is deliberately one line of work: an already-long release flow earns no ceremony, and an explicit no-change statement is what distinguishes "checked and none applied" from "never checked".

    **Mechanical support is MANDATORY and runs with `--strict` (promoted v3.16.8).** Run `python scripts/check_release_capability_docs.py <notes-file> --strict --surface <name>` (repeat `--surface` per changed opt-in surface), or `python scripts/check_release_capability_docs.py <notes-file> --strict --expect-no-optional-capability-changes` for a release with none. Extract `<notes-file>` from the finalized `## [X.Y.Z]` CHANGELOG section, which is the same text the GitHub Release body uses, so the check grades what actually ships.

    The promotion condition this command file already stated has been met, so it is recorded rather than left implicit. In v3.16.7 the gate was satisfied by a hand-written declaration reading "introduces no NEW opt-in capability, ..." -- semantically exact, and matching none of the checker's patterns, because the word "new" sits between `no` and `opt-in`. The checker was never run, so nothing caught it, and the release shipped in the same evidentiary state as one where the gate had been skipped. That is precisely the false CLEAR the gate exists to prevent, and it is why the checker is no longer optional: a declaration a human accepts and a machine cannot see provides no evidence.

    Wording that satisfies the no-change form: `changes no opt-in capability`, `no opt-in capability`, `no opt-in surface`, `no applicable opt-in`, or `no optional capability changes`. Detection is marker-based rather than prose-inferring: each surface declares its five elements as labelled lines (`Activation:`, `Validation:`, `Rollback:`, `Authority:`, `Docs:`) or as a Markdown table row, because a checker that guessed at free text would produce confident false passes.

7. **Unicode-hygiene gate on release artifacts (BLOCKING)**: sanitize what this release actually ships, before it is committed.

    ```bash
    python scripts/validate_unicode_safety.py --strict --fix --root . --path CHANGELOG.md --path README.md --path docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/
    ```

    Add one `--path <file>` for any `RELEASE_NOTES` file the repo keeps. Five rules govern it:

    - **A residual non-zero exit AFTER the fix BLOCKS the release commit.** Exit 1 means a finding survived automatic repair (a character with no mechanical ASCII replacement); exit 2 means a target was missing, unreadable, or not valid UTF-8. Neither is a warning to note and move past.
    - **Scope it to release-cycle artifacts, never the whole repository.** Archived documentation carries over a thousand grandfathered warnings (the `WN-v23-3` lineage) that a repo-wide `--fix` would mass-rewrite, burying the release's real content in an enormous unrelated diff. The gate covers what this release ships, not what it inherited.
    - **Run it BEFORE the supply-chain manifest regeneration**, so the manifest always hashes post-sanitize bytes. Today's artifact list sits outside the manifest's roots (`catalog/`, `templates/`, `scripts/`, `data/`), which makes the ordering harmless right now; fixing the order anyway makes correctness a property of the flow rather than a coincidence that a future scope change would quietly break.
    - **It composes with CI rather than duplicating it.** CI keeps its repo-wide DETECT pass (warnings allowed, errors fail). This gate is earlier (pre-commit, so nothing ships and gets caught afterwards) and stricter (it promotes punctuation to errors and repairs it) over the narrow set a release publishes.
    - **The one-time historical normalization is already done (v3.16.8).** A changelog is a single file holding both the new entry and all past ones, so file-level scoping cannot spare its history: the gate's first run rewrote 7 non-ASCII dashes in already-released `CHANGELOG.md` sections. That was performed deliberately and once, in the release that introduced this gate, and is recorded in its changelog entry. Every subsequent run is a no-op on history, so a future release seeing a large `CHANGELOG.md` diff from this gate should stop and investigate rather than accept it.

This mirrors the `implement-phase` final-phase gate - `/implement` hands off to `/update release` on a plan's last phase - so the same refactor + known-gaps + CI/CD + platform-contract + installer-parity + prompting-staleness + capability-usage work runs whether the release is reached through `/implement` or invoked directly.

## Release closing output

The message that closes a `release`-scope run uses the Completed / Verified / Open / Next shape from `catalog/style-guides/agent-communication.md`: **Completed** names the version shipped and the surfaces bumped; **Verified** carries the gate results (validate, tests, version-sync, capability-docs, contract freshness) and the published tag and Release URL; **Open** lists any hold condition, deferred gap, or advisory that did not block; **Next** states the follow-on action or that there is none. Link the finalized `## [X.Y.Z]` CHANGELOG section instead of inlining it, since that section is already the Release body. Skill: `[[agent-communication]]`.

## Notes

- This command replaces `/update-documentation`, `/update-devlog`, `/generate-devlog`, `/generate-readme`, `/update-gitignore`, `/update-version`, `/generate-changelog`, `/generate-commit-message`, `/refactor-docs`, and `/refactor-project` (removed in v3.2.0).
- `/commit` is retained as a permanent convenience alias forwarding to `/update commit` (high-frequency mid-dev use).
- Keep this dispatcher thin. The update procedures live in the retained skills; this file owns only scope resolution, the release sequence, and the version-sync / config-repair contracts above.
