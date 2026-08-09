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
        1. release   (recommended) - the full ship flow: docs + devlog + gitignore + version + changelog + refactor, then commit, tag, push, publish GitHub Release
        2. docs      - sync README, API docs, architecture docs, inline guides
        3. devlog    - append a DEVLOG entry for recent changes
        4. gitignore - audit .gitignore, clean the index, recommend LFS
        5. version   - bump the version atomically across every surface (drift-guarded)
        6. changelog - regenerate / extend CHANGELOG.md from git history
        7. refactor  - reorganize docs/ and project artifacts to conventions
        8. config    - validate and repair installed platform configs (drift repair)
        9. commit    - generate a structured commit message for the staged changes

      Reply with a number or a scope name.

- `release` runs the focused scopes in order - `docs`, then `devlog`, then `gitignore`, then `version`, then `changelog`, then `refactor` - then reconciles the version's known gaps and creates/updates/optimizes CI/CD, regenerates the supply-chain manifest, cleans up, commits, tags, pushes, and publishes the GitHub Release as one flow. It keeps every confirmation gate: never create a tag, push, or publish a release without explicit user confirmation.

## Delegation

Dispatch the resolved scope to the retained skill(s). These targets are skills under `catalog/skills/`, NOT the consolidated-away v3.x commands: the old command names (`/update-documentation`, `/generate-readme`, `/update-devlog`, `/generate-changelog`, ...) were removed in v3.2.0 and no longer resolve, so never delegate to them.

      docs      -> user-documentation (README + guides) + technical-documentation (architecture / ADRs) + documentation-consistency (link / staleness / sync audit); see the docs-sync checklist below
      devlog    -> devlog-generation
      gitignore -> built-in (audit .gitignore, clean the tracked index, recommend LFS for large binaries)
      version   -> version-upgrade, gated by scripts/check_version_sync.py (see below)
      changelog -> release-notes-writer (parse git history since the last tag into a CHANGELOG entry)
      refactor  -> docs-layout-refactor + project-refactor (per-version docs structure + archive normalization + empty-dir/duplicate/orphan/structure-complexity detectors; see the refactor scope below)
      config    -> update-config (built-in) + config-consistency-checker / nexus-hub doctor (see below)
      commit    -> code-commit-workflow
      release   -> docs -> devlog -> gitignore -> version -> changelog -> refactor (docs structure + cleanliness) -> known-gaps reconciliation -> CI/CD create/update/optimize -> manifest, then clean up, commit, tag, push, publish GitHub Release (see below)

Pass any remaining arguments through unchanged. Heavy logic stays in the retained skills; this file owns only scope resolution and the release sequencing.

## docs scope (feature-level sync, not just counts)

The `docs` scope MUST refresh documentation CONTENT to the repo's current state, not merely bump version strings and counts (the atomic version bump is the `version` scope's job). Before finishing `docs` -- and therefore before every `release` -- reconcile each item below against the actual catalog and the latest `CHANGELOG.md` entry, and FIX any drift found:

- **Headline counts**: skills / commands / hooks / agents / rule-families in `README.md` and `AGENTS.md` match `data/skills.json` and the registries.
- **Internal MCP server list**: the README's "internal MCP servers" enumeration matches the `nexus-*` servers actually registered in `catalog/mcp-configs/mcp-servers.json` -- both the COUNT and the NAMES (e.g. when `nexus-context-compressor` was added in v3.2.0 the README still read "3 internal MCP servers").
- **"What's New" narrative**: the README has a section summarizing the headline features of the release being shipped. Do NOT leave the latest release undocumented -- a release whose only README change is the version/count bump has skipped this step (the exact failure the v3.2.0 release hit).
- **Removed / renamed surfaces**: no doc still presents a command, skill, flag, or path removed or renamed since the last release as if it were current.
- **Per-version docs structure**: the active version's `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` tree exists with `plans/` and `comparisons/` subdirs per the `[[docs-layout-refactor]]` Version-directory resolution scheme; create or repair it (and relocate any stray comparison reports into `comparisons/`) if not.

When the scope is `release`, run this reconciliation as the FIRST step, before the version bump. A release whose only documentation change is the version/count bump has not run `docs`.

## version scope (atomic, drift-guarded)

The `version` scope MUST use `scripts/check_version_sync.py` so every version-carrying surface is bumped as one atomic set: `.claude-plugin/plugin.json` (canonical), `scripts/installer.sh` (`NEXUS_HUB_VERSION`), `scripts/installer.ps1` (`$script:NexusHubVersion`), `data/marketplace.json`, the latest `CHANGELOG.md` heading, and the README / AGENTS.md catalog-version prose. Run the guard before and after the bump: it must report a clean in-sync tree afterward. This closes the v2.4.0 drift class (installers stuck at one version while `plugin.json` moved to the next) systemically - a mismatch fails the build rather than shipping.

## release scope: supply-chain manifest (regenerate before the commit)

After every version-carrying surface is bumped (`version`) and the docs / changelog / refactor scopes have run, regenerate the supply-chain manifest so it reflects the exact bytes being released, then stage it into the release commit (before the tag is cut). Run `python scripts/generate_manifest.py`, which writes `MANIFEST.sha256` at the repo root over the distributed catalog tree (`catalog/`, `templates/`, `scripts/`, `data/`) in `sha256sum -c` text format. This MUST run after the version bump so the manifest hashes the bumped files, and before the commit so the manifest ships inside the release tag (and therefore inside the `~/.nexus-hub/src` tree the install bootstrap materializes). The manifest is what `nexus-hub verify` later diffs the installed catalog against; a release whose manifest is stale or missing leaves `verify` unable to confirm an install. The generator is strictly local (stdlib `hashlib`, no outbound call) and deterministic (sorted by path), so re-running it on an unchanged tree is a no-op diff.

## release scope: GitHub Release publishing (final step, after push)

After the tag is pushed, `release` publishes a GitHub Release for the new `vX.Y.Z` tag so the repo's Releases page (and the "latest release" badge / sidebar) tracks the tag. **Pushing a git tag does NOT create a GitHub Release** -- they are separate objects -- so omitting this step silently leaves the Releases page behind the tags (the exact drift that left the page at v3.5.0 while the v3.6.0 and v3.7.0 tags already existed). This step runs last because it requires the tag to be on the remote first.

- **Body = the finalized CHANGELOG section.** Use the `## [X.Y.Z]` block just written to `CHANGELOG.md` as the release notes, and reuse the tag annotation's one-line summary for the title (`vX.Y.Z - <summary>`).
- **Prefer `gh`, degrade gracefully (never fail the release).** If the GitHub CLI is present and authenticated (`gh auth status` succeeds), run `gh release create "vX.Y.Z" --title "vX.Y.Z - <summary>" --notes-file <file-holding-the-changelog-section>`. If `gh` is absent or unauthenticated, do NOT fail or roll back -- the tag and push already succeeded, so the Release can be published at any later time. Print the exact commands for the user to run: the `gh release create ...` form, plus a no-`gh` fallback (`curl -X POST -H "Authorization: Bearer <token>" https://api.github.com/repos/<owner>/<repo>/releases -d '{"tag_name":"vX.Y.Z","name":"vX.Y.Z - <summary>","body":"<notes>"}'`).
- **Idempotent.** If a Release for `vX.Y.Z` already exists, update it in place (`gh release edit "vX.Y.Z" --title ... --notes-file ...`) instead of erroring.
- **Confirmation gate.** Publishing is outward-facing, so confirm before creating/editing the Release -- the same gate the tag and push already carry. Never publish without explicit user confirmation.
- **Backfill.** When the Releases page is behind the tags (a tag exists with no matching Release), the same step publishes the missing Release(s) from each tag's CHANGELOG section -- run it per missing `vX.Y.Z`.

## config scope (platform-config drift repair)

The `config` scope validates installed platform configs and repairs drift, reusing the `config-consistency-checker` skill / `nexus-hub doctor`. In particular, a Codex `~/.codex/config.toml` that defines `[permissions.*]` profiles MUST set `default_permissions`, or the config fails to load. Repairing an already-broken user config (a `[permissions.*]` table present but `default_permissions` missing) requires TOML-aware insertion of `default_permissions` before the first `[permissions...]` table, and the idempotency guard must NOT skip such a config - it is broken, not already-fixed. When Codex's elevated-sandbox setup fails on Windows, optionally surface the `[windows] sandbox = "unelevated"` recommendation.

## refactor scope (docs structure + project cleanliness)

The `refactor` scope delegates to `[[docs-layout-refactor]]` (the `docs/` tree) and `[[project-refactor]]` (everything else), and enforces the v3.11.0 governance:

- **Whole docs-tree migration (any repo)**: migrate the ENTIRE docs tree - every version directory AND the archive, not just the active version - to the `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` scheme (with `plans/` and `comparisons/` subdirs). Reshape any flat `docs/<vSEMVER>/` or old three-level `docs/versions/v<MAJOR>/<vSEMVER>/` directory into `docs/v<MAJOR>/v<MAJOR>.<MINOR>/`, merge patch releases into their shared minor dir, relocate stray comparison reports into `comparisons/`, normalize `docs/archive/` to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/`, and repair every internal reference. This generalizes to ANY repo: `/update refactor` (and, at release, `/update release`) canonicalizes that repo's whole docs tree via the `[[docs-layout-refactor]]` `--canonicalize-layout` path, so a project adopting Nexus-Hub gets the same migration with one command.
- **Project cleanliness**: run the `project-refactor` cleanliness detectors - empty directories (respecting `.gitkeep`), duplicate/redundant files, non-version orphans, and overcomplicated structure - propose-only, with the skill's confirmation gate.

Both delegate skills stay propose-then-apply; this scope surfaces the checks and defers the procedure to them.

## release scope: known-gaps, architecture refactor, and CI/CD (before the commit)

Beyond running the `refactor` scope, a `release` performs these governance steps before the release commit, each keeping its confirmation gate:

1. **Known-gaps reconciliation** via `[[known-gaps-tracker]]`: resolve, defer, or transfer each open item for the version and finalize the per-minor `known-gaps.md`.
2. **Full architecture refactor** via `[[project-refactor]]` (the empty-dir / duplicate / orphan / structure-complexity detectors) plus `[[docs-layout-refactor]]`, leaving a clean, intuitive layout.
3. **CI/CD create/update/optimize**: ensure the pipeline covers every change in the release and is optimized to reduce action minutes (path filters, concurrency cancel-in-progress, caching, gating expensive-OS/matrix jobs) while keeping comprehensive testing.
4. **Platform read-contract re-verification** via `[[platform-contract-verification]]`: for a distribution catalog whose installer targets multiple external AI platforms, re-verify each supported platform's CURRENT skill/command/rule/hook discovery format (via targeted web searches) so the next release is guaranteed to surface the catalog everywhere. The skill self-gates: it does real work only in a repo that ships `docs/policy/platform-read-contracts.md` + `scripts/lib/integrations/` (i.e. Nexus-Hub itself) and is a silent no-op in any other project, so the release flow stays generic. On drift it updates the machine-readable `docs/policy/platform-read-contracts.json` (mirrored into the `.md` table), the affected integration adapter, and both installers, adds a CHANGELOG note, and re-runs `scripts/verify_platform_contracts.py`. It then re-stamps the JSON's `meta.verified_for_version` (+ `last_verified`) to the release version. This last step is mandatory, not advisory: `scripts/check_platform_contract_freshness.py` (in `make validate` and CI) fails the release the moment the version is bumped past the stamped value, so the release cannot ship on a stale contract. Degrades gracefully offline (record 'unverified this cycle').

5. **Model-prompting-profile staleness check** via `[[model-prompting-research]]`: report whether the per-model prompting profile layer still matches the live model roster. Like step 4 it self-gates, doing real work only in a repo that ships the profile layer (`catalog/skills/ai-development/model-prompting-research/assets/profiles-index.json`) plus `[[model-routing]]`, and is a silent no-op in any other project. It enumerates the live roster via `model-routing`'s `enumerate-models` helper, passes those ids to `scripts/check_model_prompting_freshness.py --advisory`, and on DRIFTED prints a one-line note naming the added or removed models plus an offer to run `/tune-prompting` before releasing.

    **This step is ADVISORY, and that is the opposite of step 4 by design.** Read the contrast before changing it. The platform read-contract MUST be re-verified for the release being cut, so step 4 hard-gates and a stale contract fails the build. Prompting freshness is different: models ship on the vendor's clock, so gating it would let a model released on a Tuesday wedge every Nexus-Hub release until someone ran a research swarm. Therefore this step:

    - **never blocks the release.** `--advisory` exits 0 on every path, including DRIFTED, a missing bundle, a corrupt index, and no live roster.
    - **never re-stamps a freshness marker to force a pass.** Only a real research run may write `meta.last_verified`; re-stamping it here would fake currency and is the one action that would make the check worthless.
    - **is never wired into `make validate` or CI.** `check_model_prompting_freshness.py` is deliberately absent from both, unlike its structural sibling `verify_model_prompting_profiles.py`, which IS a hard gate on the layer's shape.
    - **degrades to a logged no-op offline.** No web tool or no enumerable roster means print the reason and continue; the verdict is UNKNOWN, not a failure.

    A future editor who "fixes" this into a blocking gate will couple the release clock to the model-release clock, which is the exact failure this design avoids.

6. **Capability usage gate**: when the release introduces or materially changes an OPT-IN capability, workflow, managed skill, or host surface, the release notes MUST carry five elements for each affected surface. Shipping a switch without teaching the user how to operate it is how an opt-in surface becomes either unused or over-trusted.

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

    The gate is currently a human read of the release notes. A mechanical checker that asserts the five elements per named surface is planned; when it lands it runs ADVISORY - it surfaces its output and a maintainer decides - and is promoted to a hard gate only after it has caught a real omission.

This mirrors the `implement-phase` final-phase gate - `/implement` hands off to `/update release` on a plan's last phase - so the same refactor + known-gaps + CI/CD + platform-contract + prompting-staleness + capability-usage work runs whether the release is reached through `/implement` or invoked directly.

## Notes

- This command replaces `/update-documentation`, `/update-devlog`, `/generate-devlog`, `/generate-readme`, `/update-gitignore`, `/update-version`, `/generate-changelog`, `/generate-commit-message`, `/refactor-docs`, and `/refactor-project` (removed in v3.2.0).
- `/commit` is retained as a permanent convenience alias forwarding to `/update commit` (high-frequency mid-dev use).
- Keep this dispatcher thin. The update procedures live in the retained skills; this file owns only scope resolution, the release sequence, and the version-sync / config-repair contracts above.
