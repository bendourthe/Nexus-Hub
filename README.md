<p align="center"><a href="https://github.com/bendourthe/Nexus-Hub"><img src="assets/nexus-hub-banner.png" alt="Nexus-Hub" width="640" /></a></p>

<p align="center"><em>The Skill Harness for Every AI Coding Assistant.</em></p>

# Nexus-Hub

<!-- nexus-hub-version: 3.17.6 -->

Nexus-Hub is the upstream skill catalog for AI coding assistants: 273 skills, 18 commands, 31 hooks, 23 agents, and 4 language rule families. It installs in one step on Windows, macOS, and Linux, and it works the same across Claude Code, OpenAI Codex, Gemini (via Antigravity), GitHub Copilot, Cursor, GitHub CLI, and the sibling Nexus desktop app and VS Code extension. The catalog is reverse-engineering-first by policy: zero third-party data processors, zero outbound calls from skills / commands / hooks, zero telemetry.

## Interactive Guide -- start here

**New to Nexus-Hub? [Open the interactive guide](guides/website/nexus-hub-guide.html).** It is a self-contained, click-through walkthrough of the entire workflow -- install, onboard an unfamiliar codebase, plan, implement, harden, and ship -- with simulated VS Code / terminal sessions and the artifact each command produces. It is the fastest way to get a teammate productive, and it doubles as a live-demo-quality presentation.

- **File:** [`guides/website/nexus-hub-guide.html`](guides/website/nexus-hub-guide.html) -- one HTML file, fully offline, no server or install required.
- **To view it:** GitHub does not render HTML inline. Open the file above and click **Download raw file** (top-right of the file view), then open the downloaded `.html` in any browser. Or clone the repo and double-click it.
- **To share it:** send that single file to anyone on the team. See [guides/website/README.md](guides/website/README.md) for maintainer notes.

> **Renamed from DevAI-Hub at v2.0.0** to align with the sibling project [Nexus](https://github.com/bendourthe/Nexus-AI), a local-first desktop AI Studio that consumes Nexus-Hub as its upstream skill feed. Existing `~/.devai-hub/` installs are migrated in place by the v2.0.0 installer on first run; see [docs/archive/v2/v2.0/RELEASE_NOTES.md](docs/archive/v2/v2.0/RELEASE_NOTES.md) for the full migration story.

---

## How Nexus-Hub fits with Nexus

<p align="center">
<a href="https://github.com/bendourthe/Nexus-Hub"><img src="assets/nexus-hub-banner.png" alt="Nexus-Hub" width="360" align="middle" /></a>
<img src="assets/sibling_arrow.svg" alt="↔" width="80" align="middle" />
<a href="https://github.com/bendourthe/Nexus-AI"><img src="assets/nexus-ai-banner.png" alt="Nexus" width="360" align="middle" /></a>
</p>

Nexus-Hub and [Nexus](https://github.com/bendourthe/Nexus-AI) are two halves of the same idea, split along a deliberate seam.

- **Nexus-Hub (this repo)** is the catalog: 273 curated skills, 18 commands, 31 hooks, 23 agents, 4 rule families, plus 4 internal MCP servers (`nexus-skill-server`, `nexus-code-search`, `nexus-web-fetch`, `nexus-context-compressor`). It is content-only, platform-agnostic, and shipped via an installer that writes to `~/.nexus-hub/` and into each AI assistant's per-platform config locations.
- **Nexus** is a local-first desktop AI Studio that consumes Nexus-Hub as its skill feed. Nexus's `AGENTS.md` names this repo as "the only external project we deliberately link to" -- the upstream feed for its skill harness.

The two projects are designed to be useful independently: you can install Nexus-Hub into any supported agent platform without touching Nexus, and Nexus can run with or without the upstream catalog wired in. The combination is what gives a single curated skill set to every agent surface a developer touches: terminal, IDE, desktop app, and CLI.

---

## What's New in v3.17.6

**Every required status check is now satisfiable from any pull request shape.** Shipping v3.17.5 took six administrator bypasses in one day, all from one mechanism: GitHub leaves a check from an *untriggered* workflow Pending forever, while a job *skipped* by an `if:` reports Success. Workflow-level `paths:` filtering and a job-level `if:` therefore look like the same Actions-minute optimization and behave in opposite ways. `ci.yml` excluded `docs/**` and `doc-colocation.yml` included only `docs/**`, so the required set was unsatisfiable in both directions and no pull request shape could clear all ten checks.

**The rule is enforced, not just documented.** `scripts/check_required_check_coverage.py` reads the declared contexts in [`docs/policy/required-checks.json`](docs/policy/required-checks.json), resolves each to its producing job, and fails when that job's workflow is path- or branch-filtered. It reports `UNPRODUCED`, `CONDITIONAL`, and `BAD` separately because the remedies differ, and runs inside CI's existing `validate` job. `--sync` prints live protection state via your own `gh` and never writes.

**The required-check set shrank from ten contexts to five.** A job-level `if:` is evaluated *before* matrix expansion, so a skipped matrix job publishes only its bare job name and never `installer-smoke (ubuntu-latest)`. Requiring per-leg contexts reproduced the original defect in a new form, and the docs-only proof pull request found it. One `ci-required` aggregate (`if: always()`, allowlist verdict) now stands in for `ci.yml`'s nine, so matrix jobs may skip freely and per-leg names stop being load-bearing.

**Proven by measurement, not assertion.** A docs-only pull request and a code-only pull request each reached `CLEAN` with zero administrator bypass. Measured cost: a docs-only pull request went from 0.30 to 1.38 billed minutes (+1.08) and a code-only one from 15.47 to 16.15 (+0.68), and both were previously unmergeable.

**Releases refuse to tag the wrong commit.** `scripts/check_release_preconditions.py --pre-tag` asserts HEAD is the expected release branch *and* equal to its remote, read immediately before `git tag` because a checkout that failed silently is exactly the state it guards. In the v3.17.5 release a `git checkout main` failed on a locked directory and the tag was created on the wrong commit, shipping an unreleased plan file. The same script reports merged branches, branches surviving a closed-unmerged pull request, `delete_branch_on_merge`, and repository-description drift; it deletes nothing.

**The harness no longer teaches the antipattern.** `cicd-architect` recommended workflow-level `paths:` in one section and required a status check in another, without connecting them. Both are corrected, with the mechanism, the fail-closed detector, and the matrix caveat in that skill's `references/required-status-checks.md`. `cd-pipeline-generator` and `cicd-integration` were audited, found clean, and deliberately left unchanged.

**Plan order moved out of filenames.** [`docs/v3/roadmap-prioritization.md`](docs/v3/roadmap-prioritization.md) now ranks all 14 unshipped plans and is the single authority on sequence; new plans are named by slug with a `Target version` field inside. **v4.0.0 is reserved for the changed-install-behavior bundle**, not for backlog completion, because installing from `main` makes the major bump your only advance warning.

Catalog counts are unchanged at **273 skills**, **18 commands**, **31 hooks**, and **23 agents**. This release adds three repo-internal guards, one distributed release-preconditions script, and planning documents; it adds no outbound call, credential, dependency, or opt-in capability, and changes nothing about what an existing install does at runtime.

## What's New in v3.17.5

**Nexus-Hub now measures the things it previously only asserted.** This release adopts nine items from a comparison against DeepSeek Harness, and every one of them is a local guard, a convention, or a skill. No outbound call, no credential, and no dependency beyond the Python standard library was added.

**Always-loaded instruction docs have a word budget.** `AGENTS.md`, `CLAUDE.md`, the five lockstep platform templates, and the Markdown style guide now carry declared ceilings in `docs/policy/doc-budgets.json`, enforced by `make validate` and CI. The policy is a ratchet: lowering a ceiling is free, raising one requires justification in the pull request. Inspect usage with `python scripts/validate_doc_budgets.py --list`; the contract is in [`docs/policy/doc-budgets.md`](docs/policy/doc-budgets.md).

**Decisions are recorded with what they beat.** `docs/decisions/` holds records under `proposed` / `implemented` / `rejected`, gated by `scripts/validate_decision_records.py`, with `## Alternatives considered` mandatory in every lifecycle. The `rejected/` folder is the point: it ships seeded with two real declined designs so a future proposer can check before re-proposing one. The three-surface split against known-gaps and solutions is defined in [`docs/decisions/README.md`](docs/decisions/README.md).

**Registry entries are checked against their source, not just counted.** `scripts/check_registry_entries.py` renders each skill's expected `SKILL_INDEX.md` row and `skills.json` entry from its own frontmatter and diffs the committed bytes, and also verifies every skill is reachable from a capability module. On its first run it found a schema violation, an index category typo, and 156 drifted text fields including six carrying encoding corruption. All are repaired, and the gate now runs `--strict`. Use `--emit <skill>` for a paste-ready entry; it never writes.

**Skills can declare who may invoke them.** Two optional frontmatter booleans, `disable-model-invocation` and `user-invocable`, are validated for type and for the combination that would leave a skill invocable by nobody. Which platforms document which lever, with source URLs and verified dates, is recorded in [`docs/policy/skill-invocation-policy-levers.md`](docs/policy/skill-invocation-policy-levers.md). Claude, Copilot, and Cursor read the fields straight from `SKILL.md`; Codex uses an `agents/openai.yaml` sidecar with inverted polarity, and the installer maps it correctly.

**One new skill and three sharpened ones.** `deepseek-harness` joins `claude-agent-sdk` and `google-antigravity-sdk` as a vendor-SDK skill. `anti-slop-editing` gains a chain-of-thought-leakage pattern family, `verification-before-completion` gains smallest-sufficient-evidence-set selection, and `incident-postmortem` gains admission criteria and guardrail linking.

Catalog counts are **273 skills**, **18 commands**, **31 hooks**, and **23 agents**. Every addition is opt-in or a repo-internal guard; nothing changes what an existing install does at runtime.

## What's New in v3.17.4

**Organization standards can now be layered over Nexus-Hub without forking the catalog.** Connect a validated local directory or Git bundle with `nexus-hub org connect <path-or-url>`, then install or upgrade normally. Nexus-Hub projects the bundle's core guidance and rule files into all 16 platform integrations after its own managed block, keeps the two layers independently replaceable, and reports default or advisory precedence without claiming vendor enforcement. The new `/org` command and `org-standards-authoring` skill guide connection, synchronization, status, authoring, and platform-native escalation.

This is an opt-in local capability. Validate it with `nexus-hub org status`; remove its projected content with `nexus-hub org disconnect` followed by `nexus-hub repair`. Connecting a bundle grants no platform enforcement authority, transmits no content, and does not let organization content suppress the generic catalog. See the [Organization Knowledge Layer guide](guides/ORG_KNOWLEDGE_LAYER.md) for the bundle contract, precedence model, lifecycle, and rollback procedure.

**The usage monitors are more resilient and more precise.** GitHub Usage Monitor 0.3.3 retries only transient billing-service failures, coalesces overlapping refreshes, honors long server retry deadlines, cancels retry backoff immediately, and preserves the existing last-known-good view after exhausted retries. Codex Usage Monitor 0.2.11 renders Extra Credits usage and reset information on separate lines with full-width bars, rounds displayed credit counts to whole numbers, and shows paired live USD amounts only when the API provides both values.

The temporary provider-state restoration migration introduced in v3.17.2 has completed its one-release compatibility window and is removed from the hook catalog and both installers. Catalog counts are **272 skills**, **18 commands**, **31 hooks**, and **23 agents**.

## What's New in v3.17.3

**Cursor hooks now install and run natively on every supported operating system.** Windows installations register the PowerShell hook siblings already shipped by Nexus-Hub, while macOS and Linux retain native Bash hooks. A compatibility launcher converts Claude-imported hook results into Cursor's required JSON response without weakening deny decisions, and upgrades repair stale Windows Bash registrations and incomplete hook copies automatically.

**The Codex and Claude usage monitors are more reliable.** Codex now maps the live `spend_control.individual_limit` payload into detailed Extra Credits usage, and low or critical refresh ticks in either monitor no longer overwrite an active High warning color. The packaged extension versions advance to Codex Usage Monitor 0.2.10 and Claude Usage Monitor 0.9.9.

To verify the Cursor repair on Windows, start a new Cursor agent chat after reinstalling and run a write-producing command such as `/implement`; the Hooks output should contain one valid allow-or-deny JSON object and no Bash lookup error. On macOS or Linux, confirm the generated hook commands still invoke Bash. No opt-in capability is introduced or materially changed by this release.

The temporary v3.17.2 provider-state restoration migration remains for this expedited patch so delayed upgrades from v3.17.0 or v3.17.1 remain recoverable. Its removal is deferred to v3.17.4. Catalog counts remain **271 skills**, **17 commands**, **32 hooks**, and **23 agents**.

## What's New in v3.17.2

**The Nexus-Hub autonomy controller has been retired.** A VS Code extension cannot use a supported public API to override another provider extension's safety decisions, so the controller could only mirror each provider's existing approval mode. Nexus-Hub now leaves approval-mode selection to Claude Code, Codex, and other provider-owned surfaces instead of presenting a universal bypass it cannot guarantee.

The shared CLI command, provider descriptors, status-bar controls, expiry and guard hooks, and feature-specific CI have been removed. The Claude and Codex usage monitors continue to report usage without an autonomy indicator. During upgrade, a temporary SessionStart migration restores each recorded pre-controller provider configuration byte-for-byte, removes stale controller hook registrations, and preserves unresolved state when a required backup is missing or unsafe. It never enables a provider mode or broadens authority.

To verify retirement after reinstalling, run `nexus-hub --help` and confirm there is no `autonomy` command, then reload VS Code and confirm the usage monitors show usage only. Provider approval modes remain controlled in each provider's own extension or CLI. Catalog counts are **271 skills**, **17 commands**, **32 hooks**, and **23 agents**; the added hook is the temporary retirement migration.

## What's New in v3.17.1

**The release-only Windows installer smoke now reaches the installer.** The v3.17.0 tag workflow assigned `$home` inside Windows PowerShell 5.1; variable names are case-insensitive there, so the assignment collided with the read-only `$HOME` variable and exited before the installer ran. The workflow now uses `$smokeHome`, and a regression test rejects any future case-insensitive `$home` assignment in CI.

The v3.17.0 Windows bootstrap and ordinary install-smoke jobs were already green, so this patch changes only the release-tag CI harness. It adds no skill, command, hook, opt-in capability, outbound service, API key, telemetry, or third-party data processor.

## What's New in v3.17.0 (historical)

v3.17.0 originally introduced a time-bounded workspace autonomy controller. That capability is retired in v3.17.2; its original release record remains in the [changelog](CHANGELOG.md#3170---2026-08-15).

**Permission and installer parity remain materially stronger.** Twenty-five mutation-capable entries were removed from the read-only auto-approve baseline, retired Nexus-Hub entries propagate safely to existing installs, both installers use the same jq-free merge path, and Claude workspace installs target `.claude/settings.local.json`. A manifest-driven parity gate and real-install smoke tests protect both installer entry points.

Catalog counts were unchanged at **271 skills**, **17 commands**, **31 hooks**, and **23 agents**. The release added no outbound service, API key, telemetry, or third-party data processor.

## What's New in v3.16.8

**Invisible characters are now removed automatically, not just reported.** `scripts/validate_unicode_safety.py` already found zero-width characters and Trojan-Source bidi controls, but a detector with no repair path means every finding becomes a manual edit, and a detector nobody invokes at the moment content is written finds things only after they ship. A new opt-in `--fix` removes unsafe characters and, with `--strict`, applies the ASCII punctuation replacements, then re-scans every file it wrote and still exits 1 on any residual. Detect-only remains the default, byte-for-byte, so `make validate`, CI, and both installers are untouched.

**Three smuggling channels are now covered.** Unicode tag characters (`U+E0001` and the `U+E0020`-`U+E007F` block) mirror printable ASCII and render as nothing, so they join the hard-error set, and each finding reports the character it mirrors, letting you read a smuggled message straight off the report. Space homoglyphs, soft hyphen, and the variation selectors (including the 240-value `U+E0100`-`U+E01EF` supplement, which encodes one byte per selector) join the strict-mode set.

**Emoji survive, because the rule was measured rather than assumed.** A blanket variation-selector rule would have flagged 90 legitimate characters in this repository (warning signs, world maps, hearts) and caught nothing, then silently rewritten emoji in shipped documentation. A `U+FE0F` immediately following a symbol or keycap base is emoji presentation and is exempt; a stray one is still caught.

**`/plan` and `/update` now run the check for you.** Every plan file `/plan` writes is sanitized immediately after it is written, and again if feedback rewrites it. `/update docs` and `/update changelog` detect on each touched Markdown file, deliberately without auto-fixing, because hand-edited prose has an author whose punctuation may be intentional. `/update release` gains a blocking gate over release-cycle artifacts only, so a release cannot ship an invisible character, while the thousand-plus grandfathered warnings in archived documentation are never mass-rewritten.

**Two silent failures were fixed along the way**, both found by running the new commands rather than by testing the code. A `--path` that did not resolve under `--root` exited 0 reporting a clean scan of nothing, which would have made any gate wired to it report success forever without checking anything; it now exits 2 and names the path. An unreadable or undecodable file was silently skipped and is now reported.

Catalog counts are unchanged at **271 skills**, **17 commands**, **31 hooks**, and **23 agents**. This release extends one existing script and three instruction files, and adds no new catalog content or opt-in capability.

## What's New in v3.16.7

**`/presentify` now asks what the page is FOR, before it authors anything.** A real session produced a page that was offline, responsive, browser-verified, and structurally clean, and was still the wrong artifact: it critiqued a draft the audience had never seen, estimated a reusable commercial platform when a bounded pilot was requested, argued against an assumption the reader had already granted, and led with a visual that explained nothing. Every existing gate passed, because every existing gate asks whether the page *works*. A new content brief closes that gap: a **source relationship** (defaulting to `standalone`, which forbids referring to the source at all), the **decision the reader must be able to make**, an **assumption ledger** whose accepted premises no heading may argue with, and a **scope class** so a bounded pilot never inherits a platform-scale timeline.

**Visuals must now state their job before they are built.** Each major visual records a contract (question, message, encoding, states, trigger, fallback, evidence) and faces a subtractive test: remove it, and if the section loses no explanatory value, redesign it or *omit* it. Omission is explicitly allowed, because a gate that can only demand more visual work is a cost generator. Scrollytelling sections additionally declare a state table, so scroll motion has to match the narrative's own transitions rather than merely accompany them.

**Layout composition became measurable.** The typography contract gained the inverse of its old failure: text that is correctly sized and correctly measured while using half its track, and sections that are viewport-tall for no reason. Wrap plans for display text, measure assigned by text *role* (long-form prose is the only default recipient of the reading measure), a 70%-of-track utilization floor, and binary earned section height - that last one needed its own rule because a universal `min-height: 82svh` is viewport-relative, so it passed the fluid-spacing check while being exactly the defect. The render loop gained matching probes (line counts, width utilization, one-word orphans, text-graphic collision, per-section density deltas) inside the `page.evaluate()` it already ran.

**QA has four named layers now, and three of them can fail a page a green build cannot.** Content, semantic-visual, structural, and behavioral - with Gate A running before authoring (so a mismatch costs an outline revision, not a rebuild), Gate B before detailed styling (and it may *remove* a visual), and an optional reader-level decision-readiness check at the end. A document cannot receive a final pass on the structural and behavioral layers alone.

**Supply-chain fix: `MANIFEST.sha256` now describes what is distributed.** The generator hashed working-tree bytes, so a manifest built on Windows (where autocrlf materializes every text file as CRLF) disagreed with the released tarball on essentially every text file - v3.16.5 shipped exactly that, and `nexus-hub verify` would have reported roughly 520 spurious mismatches. Tracked files are now hashed over their git blob bytes, which *are* the tarball's bytes, making the manifest correct by construction from any OS with any line-ending configuration.

Catalog counts are unchanged at **271 skills**, **17 commands**, **31 hooks**, and **23 agents**. This release deepens one existing skill (`document-to-interactive-html`) and its command surface, fixes release tooling, and adds no new catalog content or opt-in capability.

## What's New in v3.16.6

**`/presentify` now asks how much of your source material should survive onto the page.** Style, aspect, interactivity, and imagery never answered that question, so the agent decided content depth silently - pages either reproduced everything or over-summarized with no user say. The intake's second round (the post-extraction round that already derives color schemes from the content) now also asks the coverage depth: **Distilled** (one narrative arc, key findings only), **Balanced** (every major topic, details summarized), or **Comprehensive** (full section-by-section coverage including appendix-grade material) - and because it is asked after extraction, each option carries an approximate section count for *your* source set rather than a meaningless low/medium/high.

**A `--verbosity <distilled|balanced|comprehensive>` flag presets the answer** for scripted runs (natural-language forms bind too: "just the highlights" is `distilled`). It is deliberately distinct from `--qa-depth`, which bounds how thoroughly the visual-QA loop inspects whatever was built; `--verbosity` decides how much content the page carries. A malformed value degrades with a usage note instead of blocking, and non-interactive runs resolve to `balanced`, so unattended behavior does not change character.

**The answer is enforced, not decorative.** The resolved level, its provenance (flag-preset / asked / defaulted), and a derived section-count target are written into the page's design record; the authoring step carries three per-level depth rules (with per-source attribution winning over distillation in compile mode); and the visual-QA rubric gained criterion 10, which grades the built page's section structure against the declared level - by agent vision at page level, deliberately with no word-count heuristic, because a long section is a style property, not a depth violation.

Catalog counts are unchanged at **271 skills**, **17 commands**, **31 hooks**, and **23 agents**. This release deepens one existing skill (`document-to-interactive-html`) and its command surface, and adds no new catalog content or opt-in capability.

## What's New in v3.16.5

**`/presentify` was producing pages that passed every check and still read badly on a large display.** One mechanical cause explains almost all of it: the generated CSS scaled `body` with `clamp()` while child elements sized themselves in `rem`, and `rem` resolves against the **root**, not against `body`. Every nested element therefore ignored the scaling entirely. The contract now scales `html`, which is a one-line change that fixes the whole cascade, and a deterministic checker enforces it along with twelve other structural criteria (fluid spacing, per-role font floors, WCAG contrast, full-width band fraction, image caps, SVG marker integrity, viewport fit).

**The release's centerpiece is that the page is now actually looked at.** Prior cycles graded output by parsing markup, which answers a different question than rendering it does. A gated CI job installs a real browser, renders the calibration fixture, and enforces the rendered checks with `NEXUS_REQUIRE_RENDER=1`, which converts a browser-dependent skip into a **failure**. That distinction matters: a broken browser install previously presented as three quiet skips inside a green run, which is exactly how the gap went unnoticed for four minor versions. The job is gated to merges plus a weekly cron so a pull request never pays for a 130 MB browser download.

**Rendering immediately found five defects that eleven deterministic checks had passed, and two of the five were bugs in the checker rather than in the page.** A 12.48px brand label misclassified as interactive, 12.2px emphasis tokens the checker declined to judge, an 11.52px inline style it could not see, and a horizontal overflow introduced by an earlier fix of our own. The most instructive single finding was that the font-floor check silently skipped every `var()` value, so *tokenizing* a stylesheet dropped its verified font count from 40 to 17. A linter that inspects the non-compliant form more thoroughly than the compliant one rewards the wrong behavior, and only running it before and after the fix surfaced that.

**Diagrams, intake, and one new opt-in level.** SVG diagrams get an explicit quality contract: arrowheads that actually land on their endpoint (`refX` with `markerUnits="strokeWidth"`), labels kept horizontal rather than rotated, and a viewport that fits its content. The design intake asks about imagery up front and derives color schemes from the document's own content instead of rolling them blindly, while keeping the anti-convergence rejection axis that stops every deck looking alike. A new opt-in `cinematic` interactivity level ships a dependency-free scroll-scrub engine that creates no video element at all under `prefers-reduced-motion: reduce`.

**The lesson worth carrying out of this cycle is an asymmetry.** A false PASS costs far more than a false FAIL. Sixteen false failures appeared in one afternoon, were obviously wrong, and were fixed within the hour. One false pass, a band fraction the checker inflated from 0.947 to 0.954 across its own 0.95 threshold, sat inside a green run for two phases and would have shipped. Gates are worth building in the direction that fails loudly.

Catalog counts are unchanged at **271 skills**, **17 commands**, **31 hooks**, and **23 agents**. This release deepens one existing skill (`document-to-interactive-html`) and adds no new catalog content.

## What's New in v3.16.4

**The GitHub Usage Monitor was reporting the wrong account's billing, and sometimes none at all.** The cause was one line: `getSession("github", ["user"], ...)`. A scope list identifies a *permission grant*, not an *identity*, so an editor with two GitHub accounts signed in answered with either one, and not stably. The panel alternated between a correct reading and a 404 for the *same* configured owner, because `/users/<login>/settings/billing/...` succeeds with that user's token and 404s with another's. Every session request is now **pinned to the account you chose** - except when you are explicitly switching, which is the one call that must not be pinned.

**That single non-determinism was the source of a lot of weather.** A reconciler that rewrote the billing owner toward whichever account answered; a notification loop; the wrong account after a reload; an "insufficient-role" warning that came and went. Five fixes went in downstream of it and none could hold, because the input was the cause rather than a trigger. Three structural changes now make the class impossible rather than unlikely: owner corrections are classified by whether their result can re-trigger another rule (the one that can is **offered**, never applied unattended), reconciliation moved out of the refresh loop to activation and sign-in, and the two settings that form the owner pair are written behind a guard so no observer can judge a half-written pair.

**A sixth participant was in another window.** VS Code loads extension code at activation and never swaps it, so installing a build and reloading one window leaves every other window running its old code - and because global configuration writes reach *every* window while `globalState` does not, a stale window keeps writing while a fresh one reacts. All four usage monitors now **prompt for a restart** when a build lands underneath them, and the GitHub monitor **defers** - stops writing, keeps displaying - when it detects it is the stale one.

**Copilot AI credits finally have a denominator.** No GitHub endpoint serves an entitlement, but the pooled figure is composable: assigned Copilot seats times GitHub's published per-seat allowance, resolved against the billing period so the promotional rate ending **2026-09-01** (Business 3,000 -> 1,900) needs no code change. Verified against a live organization - 7 seats x 3,000 = the 21,000 its own billing page shows. Reading it needs `read:org`, the narrower of the two scopes GitHub documents for that endpoint; `admin:org` stays behind an explicit escalation.

**Smaller things that were quietly wrong.** The plan denominator asked `GET /user` regardless of who was being billed, so an organization's usage was measured against your personal plan. A Copilot allowance you typed into Settings was discarded while the panel told you to set one. A month with no Actions runs showed "could not be reconstructed" instead of 0%. Log out did not stick, because the editor's GitHub session is shared with Copilot and deliberately cannot be ended - so "signed out" is now recorded rather than inferred. Account identity moved out of Settings into the panel header, where it belongs: it is the caption for every number on the panel. And the monitor now installs into **Cursor** as well as VS Code, because GitHub billing is not tied to the editor you happen to use.

Catalog counts are unchanged at **271 skills**, **17 commands**, **31 hooks**, and **23 agents** - this release touches one VS Code extension, the two installers, and no catalog content.

## What's New in v3.16.3

**The GitHub Usage Monitor shows real percentages, and they are honest ones.** The extension previously reported 1,287 Actions minutes for a month in which GitHub counted about **121** against the allowance - almost all of that usage was in a public repository, which is free and never draws down. Supplying a denominator without fixing that numerator would have rendered 64% where the truth was 6%. The monitor now reconstructs the drawdown (private-repository, GitHub-hosted, standard-runner minutes, weighted per runner OS), derives the denominator automatically from your plan, and labels the result as reconstructed rather than presenting it as GitHub's own figure.

**That reconstruction is the release's real work, and it was measured rather than reasoned.** No documented GitHub endpoint serves an entitlement - every field of `/settings/billing/usage`, `/usage/summary`, the AI-credit and premium-request endpoints, and the Budgets API was checked, and the endpoints that once returned `included_minutes` closed down in September 2025. Neither does any endpoint serve the drawdown: `/usage/summary` reports `discountQuantity == grossQuantity` on every row. A live probe against a real account then **falsified the leading candidate**: counting private minutes 1:1 predicted 1,584 for a month where GitHub's own panel showed a saturated 2,000, which proved non-Linux minutes draw down faster even though GitHub has withdrawn the page that published the multipliers. One candidate "reconciled" at 0.6% and was arithmetically impossible; a bound check caught what a tolerance check had passed. All of it, including three superseded conclusions and their corrections, is recorded in [`docs/v3/v3.16/development/github-entitlement-probe.md`](docs/v3/v3.16/development/github-entitlement-probe.md).

**The rest is the UX the extension always needed.** It is named **GitHub Usage Monitor** again, matching its Claude, Codex, and Cursor siblings, with a one-time migration so no threshold, color, owner, or allowance is lost to the rename. It connects itself on install - silently if you are already signed in to GitHub in the editor, otherwise with exactly one prompt that never returns if you dismiss it. The panel is one window with three controls (Refresh Now, Open GitHub Billing Page, and a gear) and settings that expand in place and are editable there. Storage percentages work for the first time, using GitHub's documented GB-hours conversion, verified in both directions against a real account.

**Three crashes from one root cause**, all found and fixed during the cycle: a `NaN` rendered in the panel, a status-bar hover that threw outright, and a filter that guarded `!== null` and then threw on `undefined.length`. Each came from a snapshot cached by the previous extension version lacking a field the new code assumed. **Cached state outlives the version that wrote it**, and a regression fixture now pins the whole pipeline against a 0.1.0-shaped snapshot. Catalog counts are unchanged at **271 skills**, **17 commands**, **31 hooks**, and **23 agents** - this release touches one VS Code extension and no catalog content.

## What's New in v3.16.2

One thing you could not do before: ask whether your install actually landed where the contract promised.

**`nexus-hub doctor`.** A read-only preflight in both installers. It reads the platform read-contract, detects which of the fourteen platforms are present on your machine, and verifies that every surface the contract promises actually exists -- skills, commands, agents, rules, hooks, and the instruction file, per platform. It keeps three states apart, because collapsing them is what makes a diagnostic untrustworthy: a platform you have not installed **skips** (not a failure), a complete one **passes**, and a present one missing a surface **fails** with the exact remediation command. Exit **0** clean, **1** drift, **2** the contract itself could not be read -- it refuses to report CLEAR on evidence it does not have.

```bash
bash scripts/installer.sh doctor          # macOS / Linux
pwsh scripts/installer.ps1 doctor         # Windows
```

**Loop definitions can now express three things a static schema could not.** Typed human-judgment `gates` pause a running loop to ask one concrete question (an owner call, an action beyond the loop's authority, anything externally visible, anything touching private context) and resume on the answer -- distinct from `handoff`, which only catches work after the cap. `evidence_freshness` declares how long a check stays authoritative, so a long-horizon loop stops trusting a result that passed twenty iterations ago. And a documented instance-state pattern lets a cold start resume rather than re-derive. All three are optional, so every existing loop definition stays valid.

**A release can no longer ship an opt-in surface it does not teach.** `/update release` now requires five things per opt-in capability: activation, a validation command, the rollback path, the authority boundary activation does *not* grant, and a documentation link. The fourth is the one most often skipped and the only one that fails silently, by letting you over-trust something you enabled. Dry-run against the two prior releases: one would have failed, one was out of scope.

**An incident archive that cannot become a graveyard.** `docs/incidents/` ships with two real backfilled failures and one rule enforced by a validator in CI: an incident is closed by a *change*, not an explanation, so a note whose "durable fix" carries no link fails the build. The shape those two notes describe -- a cross-platform sibling that is silently non-functional -- caught two live defects in the same cycle it was written, including one where the two `doctor` implementations disagreed on four platforms while both returned the same exit code.

## What's New in v3.16.1

Two things you could not do before: evaluate an AI pipeline with a shared vocabulary, and install part of the catalog instead of all of it.

**Selective installation.** `--profile`, `--modules`, and `--bundles` now work identically across the Bash installer, the PowerShell installer, and the Python integration registry. Selectors union rather than intersect, dependencies close transitively, and a selector that names nothing fails **before** the first file is written rather than half-way through. Exit **2** means your selector was wrong; exit **3** means the catalog is inconsistent. Hooks, rules, templates, and settings are never filtered, so a focused install is never a less safe one.

**Evaluation methodology.** A shared artifact contract fixes the names for the nine things an evaluation pipeline passes around, with provenance and redaction status as **required embedded blocks** rather than optional peers, so an artifact cannot be well-formed without recording where it came from. Around it: retrieval metrics with worked numbers (Recall@k, MRR, NDCG@k), error-analysis exclusion criteria, evaluator calibration with a confusion matrix that shows precision collapsing from 0.600 to 0.156 as prevalence falls, synthetic-data coverage, and a blind human-review contract. The new `eval-pipeline-audit` skill routes between them, taking the catalog to **271 skills**.

**Two pre-existing catalog defects surfaced by the work.** Four bundles referenced skills that do not exist, and **166 of 271 skills were unreachable** through any module -- the modules covered six categories out of twenty-one. Modules are now category-complete, and every skill in the catalog is reachable. Neither defect was visible until something tried to resolve a selection against the whole catalog.

**Defects found and fixed, each by the check that could actually see it.** A resolver bug passed 89 of 90 assertions while no real profile resolved: profiles *compose* other selectors rather than carrying a flat skill list, and the fixtures encoded the same wrong assumption as the code, so only the real-catalog test caught it. `Get-FileHash` raised CommandNotFoundException inside the PowerShell installer on a Windows CI image, hidden for four releases because that line is only reachable on a **second** install into the same home. A CI path filter used `*` where it needed `*/`, so an entire documentation tree was never triggering CI. And a test that "still passed" on Windows was in fact failing while building its own error message, masking the result it was meant to report.

## What's New in v3.16.0

A per-platform install default lived in two places and was copy-pasted into a third. Changing one value in v3.15.5 meant editing four declarations across two files and correcting four documentation surfaces that restated it as prose. This release gives that value a single home and makes every other copy derived from it.

**One file is now the only place a per-platform default is edited.** `configs/platform-defaults.json` declares the reasoning effort, model pin, and approval policy each platform should ship with. `catalog/hooks/settings.json`'s core keys are **generated** from it, and the `nexus-hub init` project stub reads it at runtime -- the hardcoded `_PROJECT_SETTINGS_STUB` is gone. `python scripts/sync_platform_defaults.py --check` fails `make validate` and CI when any derived artifact drifts, so the duplication cannot silently return. The generator updates only the declared keys **in place**, because that template also carries the full hook registration chains, and it preserves each file's key order, indentation, and line-ending convention -- the repo runs `core.autocrlf=true`, so a naive write would have looked clean in CI while rewriting every line on a Windows checkout.

**Every platform was checked against its own documentation before anything was seeded.** All sixteen registered integrations are now classified in `docs/policy/platform-defaults-levers.md`: **12 VERIFIED** with a fetched vendor URL, a quoted statement, and a date; **4 UNVERIFIED** with reasons. "No lever documented" is a valid result, and four platforms earned it. The rule exists because Nexus-Hub once shipped a `.kimi/agent.yaml` companion that was *invented* rather than found, and had to drop it in v3.15.0. It earned its keep immediately: every search for Codex's config keys returned blogs and aggregators quoting the right names, and the recorded row instead comes from OpenAI's own reference reached through two redirects. Three vendor doc hosts had moved, one of them a full product rebrand -- confirmed first-hand rather than from reporting.

**Defaults now reach each platform's own config, without stepping on anything.** Seven platforms are seeded at install time (Codex, Copilot, Cursor, Gemini CLI, Hermes, Kimi, Qwen), one is already delivered by the existing installer copy (Claude), and four are declared-but-not-writable with recorded reasons. Writes are **seed-if-absent** -- a value you already set is never overwritten on reinstall -- and never destroy what they did not write: TOML is edited through `tomlkit` so your comments and layout survive, and existing YAML is only ever appended to, because a round-trip would silently strip every comment. A platform you do not have installed receives nothing.

**What is deliberately NOT seeded is recorded as carefully as what is.** A model pin ships only where a vendor documents a self-selecting value; exactly one does. Every other model key is listed under `omitted` with its reason, because pinning a provider-scoped id your account cannot reach breaks the tool rather than configuring it.

Two defects worth naming, both caught by the full test suite rather than by review: the seeding code resolved `~` through `os.path.expanduser`, which escapes the fake home the suite installs into, and the install hook ran before the detection gate, so a platform you do not have would still have received a config file. A third was a test that asserted the *key* `paths-ignore` as a proxy for the property it meant (the repo-wide CI gate must not narrow to an allowlist), and so failed a change that widened coverage. Catalog counts are unchanged at **270 skills**, **17 commands**, **31 hooks**, and **23 agents**.

## What's New in v3.15.14

Three surfaces were checking specs for something the spec template could not express, and the skill's own completion gate was validating the wrong document. This release makes the spec artifact say what everything already assumed it said.

**The spec template can now express a scope boundary.** `spec-quality-checklist.md` asked whether "Scope is clearly bounded", the `scope-guardian-reviewer` agent flagged a missing out-of-scope section, and `idea-refine` gated on scope being explicitly bounded - but no section in `spec-template.md` held that content. Every reviewer run on a perfectly template-conformant spec therefore raised a finding the template itself caused, and the reviewer's complaint was unsatisfiable in one direction and unfalsifiable in the other. The template gains a mandatory `## Non-Goals` section requiring a **reason per entry**, plus `## Problem Statement` and `## Invariants`. Each states its boundary against its neighbour at the point of use, because the Non-Goal / Assumption and Non-Goal / Invariant distinctions are the two authors actually get wrong.

**The completion gate now checks the artifact the workflow produces.** `spec-driven-development` told authors to start from `spec-template.md`, then presented a *different* template inline further down, and its Verification checklist validated the inline one's areas ("Objective, Commands, Structure, Style, Testing, Boundaries"). "Spec complete" was being checked against a document nothing produces. The skill now declares one canonical skeleton, the rival is gone in both its code-block and prose forms, and its genuinely useful content (commands, directory layout, code style, tech stack, the three-tier boundaries) is relocated to a labelled "Project-level context" section that says where it really belongs: your `AGENTS.md` or `CLAUDE.md`, written once, not restated per feature.

**Spec depth is now proportional to blast radius, and the approval gate is not.** How much spec a change needs scales with how far a wrong assumption propagates: an internal single-file change needs a problem statement, acceptance criteria, and non-goals; a multi-file change adds user scenarios and requirements; a change to behavior, a public API, a data schema, or a CLI surface needs the full template. Depth is explicitly *not* keyed on effort or line count - three lines touching a public API outrank three hundred in a private helper. **The hard gate is untouched and stays unconditional.** The rule was placed *inside* the gate's own section rather than after it, so it can never be read detached from the constraint it refines, and two new rationalization rows rebut the misreadings it invites. Its integrity is provable rather than asserted: across that change the file has exactly two deleted lines, neither inside the gate.

**Plans must now say what breaks.** Error handling had no mandatory home in either artifact - the spec names the user-visible edge case by design and says nothing about the handling. `implementation-plan` now requires, per component, what happens on malformed or absent input, on an unreachable or slow dependency, and when two operations conflict. Three named situations rather than "handle errors well", which is satisfiable by any behavior including a silent swallow. Plans also carry a one-line `scaffolding` versus `load-bearing` label, so a reviewer never has to guess whether a hardcoded value is a shortcut awaiting replacement or the intended implementation.

**The fix defends itself now.** A 21-case guard test asserts the three artifacts stay in agreement, because prose has no compiler: a schema reference to a missing column errors, but a checklist item referencing a missing heading just fails forever in silence. The test was mutation-checked against three reproductions of the original defect - and **its first draft passed one of them**, because it asserted that the words "Non-Goals" appeared somewhere in the file rather than that the binding held. Rewritten to check the relationship, all three mutations now fail. Without that pass, the gap would have closed on a false guarantee.

Two of the plan's own factual claims had gone stale between writing and execution: a catalog count and a CI action pin that had since been fixed. Both were caught by checking the assertion against the tree rather than transcribing it, which is the release's quiet lesson - a plan is a decision record, not a data source. Everything here is prose in files this repo already owns: no new skill, no MCP, no outbound call, no credential, no dependency. Catalog counts are unchanged at **270 skills**, **17 commands**, **31 hooks**, and **23 agents**.

## What's New in v3.15.13

Both usage monitors work now, and the version's most instructive moment was retracting a claim it had already shipped.

**The Cursor monitor reads your real usage automatically.** It previously fell back to figures typed in by hand, and its live transport called a REST path that does not exist. The route was recovered by reading Cursor's own installed client: personal usage is a unary Connect RPC, `GetCurrentPeriodUsage` on `aiserver.v1.DashboardService`, reached with an empty body. This is the same shape the sibling monitors already use - the Claude monitor reads `~/.claude/.credentials.json` and calls Anthropic's OAuth usage route; the Codex monitor reads `~/.codex/auth.json` and calls ChatGPT's backend usage route - and the credential half needed no change: one allowlisted key, read **read-only**, behind a one-time consent prompt. Nothing is read before you agree, and refusal stays a first-class path.

**An earlier claim in this same release was wrong, and is retracted.** This section previously said the goal was "not achievable" because Cursor documents no personal-usage API. That inferred the absence of a surface from its absence in the public docs - the identical reasoning error the version had already corrected once, for GitHub billing authorization. The public docs are accurate; they simply do not cover the route Cursor's own client uses.

**Three properties of that payload are pinned by tests, because each is a trap.** Field names are camelCase, not the protobuf descriptor's snake_case, because Connect applies the proto3 JSON mapping - building from the descriptor alone reads `undefined` for every field. Percentages are used **exactly as delivered and never recomputed**: on a live account, spend over limit came to 1078.70 while the reported figure was 23.97, so deriving it would render a healthy pool as 1079% and pin every threshold alert on. Money is minor units and cycle bounds are epoch-millisecond strings, so spend divides by 100 and a cycle read as seconds would date to 1970.

**The GitHub monitor is now `GitHub Billing Usage`**, and it connects on its own. The per-target authorization model shipped complete but inert - wired to the settings panel and the diagnostic while the refresh path still read SecretStorage directly, so a user already signed in saw "No billing data available" indefinitely. The data path now resolves a credential explicitly: an explicitly stored token first, otherwise the editor's GitHub session, always **silently** so a background refresh can never raise a sign-in dialog. Authorization resolves **per billing target**, because OAuth-app restrictions and SSO are per-organization settings. `Log Out of This Monitor` clears only this extension's binding and **cannot** sign you out of the editor's GitHub session, so Copilot is unaffected - enforced by giving the log-out path no capability that could.

**All three monitors now look and behave alike.** The Cursor dashboard, its inline settings form, the status-bar hover, and the warning panel match the Claude and Codex monitors component for component: pill-shaped bars in the product's own accent, one narrow centred column, settings under the progress bars behind a gear, and a usage ring on the warning. The settings CSS and script were copied from the Claude monitor byte-for-byte rather than reimplemented, because "looks the same" is a property two parallel implementations lose on the first divergent tweak. One thing was deliberately **not** copied: the siblings' inline event handlers, which a nonce Content-Security-Policy blocks outright - a verbatim copy would have rendered a settings form that looked perfect and did nothing.

**On-demand spend is measured against the pool it draws from, not against personal spend.** On a real account, personal spend of $157.32 against a $200.00 limit rendered as a comfortable 79% bar while the pool itself was fully drawn with nothing left. Both figures are now shown, with the bar on the one that decides whether the next request is billable.

Defects found and fixed during the release, every one by a test written alongside the code rather than by the happy path passing. The most instructive: the production HTTP client hardcoded `method: "GET"` while every test passed against a stub that only recorded intent, so a POST-only endpoint would have returned 405 in production with a green suite; and adding two optional fields broke every snapshot already cached on disk, because the parser accepted `null` but not `undefined` - the strictness that correctly rejects wire drift is exactly wrong applied to your own persisted data. Catalog counts are unchanged at **270 skills**, **17 commands**, **31 hooks**, and **23 agents**.

Still open and honestly recorded: `Current Model` is absent from the Cursor dashboard because that API reports pools, not the editor's selected model, and reading it would mean widening a credential allowlist for a cosmetic section; and one bootstrap test passes or fails depending on which shell launched the suite, because it inherits `PATH` and resolves GNU tar instead of the bundled bsdtar.

## What's New in v3.15.12

The planned scope: a consent gate and a usage UI for the Cursor monitor, and a rename plus per-target authorization for the GitHub monitor. What the plan *concluded* about Cursor turned out to be wrong, and correcting it became v3.15.13 above.

**The Cursor monitor gained a consent-gated transport.** One modal prompt states exactly what will be read (Cursor's own application state database, opened **read-only**, for **one** allowlisted key, then a single JSON request) and what never will (browser cookies, `Login Data`, OS keychain, process memory, shell history, any HTML billing page, any filesystem search for credentials). Only the decision is stored, never a credential. Refusal is a first-class path with no repeated prompting, and a widened disclosure invalidates a prior grant rather than inheriting it. The dashboard renders both included-usage pools plus on-demand spend as **currency against its limit**, annotated that the limit is shared across your team, with the reset date taken from the payload rather than a hardcoded day. Percentages carry one decimal, so a 1.7% pool is no longer reported as 2%.

**The GitHub monitor became `GitHub Billing Usage`**, because the old name read as Copilot-only to some and Actions-only to others. It is neither: it reports Actions minutes and storage **plus** Copilot billing for one billing owner you configure. The extension **id deliberately did not change** - an id is `publisher.name`, so renaming it would mint a second extension and leave an existing install orphaned with two status-bar items. Authorization resolves **per billing target** rather than by one global default, because OAuth-app restrictions and SSO are per-organization settings: you can legitimately be connected via the editor's GitHub session for one organization and need a pasted token for another. `Log Out of This Monitor` clears only this extension's binding and **cannot** sign you out of the editor's GitHub session, so Copilot is unaffected - a guarantee enforced by giving the log-out path no capability that could. `Diagnose Authorization` answers "why is my billing panel empty" for one target and writes a sanitized, credential-free record you can paste into an issue.

Six defects were found and fixed during this release, every one by a test written alongside the code or by a deliberate check rather than by the happy path passing. The most instructive: a rename would have failed CI through `catalog/hooks/tests`, a tree the phase gate did not run, because `ci.yml` collects it separately from `tests/`; and a guard test asserted the developer's real `~/.copilot/agents` was empty, so it failed permanently for anyone who had **actually installed Nexus-Hub** - punishing exactly the people most likely to run the suite. Catalog counts are unchanged at **270 skills**, **17 commands**, **31 hooks**, and **23 agents**.

Recorded as open at the time, and **both resolved in v3.15.13**: the Cursor wire contract was unverified against a live account, and the editor's own OAuth app was unproven against the billing endpoints.

## What's New in v3.15.11

A follow-on patch to v3.15.10, cut because settling one open question exposed a regression v3.15.10 had already shipped.

**Codex now receives both notification triggers**, making it the only platform besides Claude Code able to say "I am blocked on you". Its `PermissionRequest` event carries that trigger and `Stop` carries completion. Settling it meant auditing the Codex **implementation** rather than its documentation: `openai/codex` ships no `docs/hooks.md`, so the evidence is `codex-rs/hooks/src/events/permission_request.rs` (a dedicated event module) plus the serde wire names in `codex-rs/hooks/src/lib.rs`. v3.15.10 had recorded this event as unverified and deliberately shipped nothing for it, which was the right call on the evidence available then.

**Two defects fixed, both of the shape this release line exists to prevent: a hook that is registered, executable, and permanently silent.** v3.15.10 delivered `notify-on-complete.sh` to Codex but not `_notify_common.sh`, so the hook sourced nothing and exited on every run. Shared modules are deliberately unregistered in `settings.json` (that is what makes them modules), so the settings-driven collection never saw it; the mapper now resolves `_`-prefixed siblings from the delivered script bodies. Separately the Notification chain was dropped for want of a same-named Codex event, which an alias now resolves. Both are asserted by test, including that the alias target actually exists in the verified event set.

Still open and honestly recorded: the Cursor live visual smoke, the light/dark/high-contrast smoke, and the Extension Development Host activation check all require a human observing rendered UI. The automated surface is green (Cursor extension 132 tests, GitHub extension 103), but the rendered result on a live host is not something an automated release can confirm.

## What's New in v3.15.10

v3.15.10 makes the end of a task deliberate in both directions: when you get told, and what the agent says.

**Notifications now fire only when your attention is actually required.** Before this release a single hook rode the `Stop` event, which fires at the end of *every* conversational turn, so a session driven by background work produced a burst of toasts carrying no signal. There are now two purposeful triggers: **`Notification`** for "the agent is blocked on you" (a permission request, or idle waiting for input) and **`Stop`** for "the agent finished". `SubagentStop` is never wired, and that absence is asserted by test, because a sub-task milestone is not a reason to interrupt a human.

Two smaller defects went with it. Labels came from `basename "$(pwd)"`, so they named whatever directory the hook happened to run in (one real toast read `Task complete in work`); they are now `<repo> (<branch>)` resolved from the git root, with the branch included because worktrees of one repository are routinely open at once. And the only kill switch was an environment variable, which **cannot** silence a hook inside a running editor: a child process inherits its parent's environment block rather than the registry, so a newly-set variable never reaches a process tree that was already launched. Suppression now also checks `~/.nexus-hub/notifications-disabled`, stat-ed on every invocation, so `touch` takes effect on the next notification with no restart.

**Every agent now closes a completed task with a summary.** A six-bullet `## End-of-Task Summary` rule ships in all 12 substantive instruction templates: what changed, the concrete next step or an explicit "nothing outstanding", and blocked or skipped work stated rather than omitted. It is instruction text by necessity rather than preference. A `Stop` hook fires *after* the agent has finished generating, so a hook can only print its own text and can never cause a summary; and a skill would under-trigger against an "always" requirement. The heading is now in both `REQUIRED_HEADINGS` and `INVARIANT_SECTIONS` of the base-template parity guard, so a platform cannot quietly drop or reword it.

**Notification coverage is verified rather than assumed, and the verdicts are uneven.** A trigger ships only when its event name is confirmed against first-party documentation, because an unverified name produces a hook that is registered, executable, and permanently inert. Claude Code gets both triggers; **Cursor** gets the completion trigger on its documented `stop` event. Cursor's documented 21-event set has nothing meaning "blocked on the human", so that trigger was omitted rather than approximated with `beforeShellExecution` (which fires before every shell command and would have recreated the storm). **Gemini CLI renamed every event** -- its completion event is `AfterAgent`, so writing `Stop` there would have shipped a silently dead hook. Codex's promising `PermissionRequest` appears only in secondary sources, so nothing was delivered for it. GitHub Copilot (no hook surface) and OpenCode (a JS/TS Bun plugin runtime) are recorded as permanent non-coverage for notifications -- and both are fully covered by the summary rule, which needs only an instruction file. That asymmetry is why this release has two deliverables instead of one.

Also settled: a v3.15.9 finding of our own was **wrong and is withdrawn**. First-party Cursor documentation confirms `~/.cursor/skills/` and `~/.agents/skills/` as user-level read-paths with recursive discovery, so Nexus-Hub's global skills write is correct and load-bearing. The v3.15.9 note that extended known gap DF-1 to that path was based on secondary sources; the original text stays in place with a superseded notice, because a verification log should record what was believed when. Catalog counts are **270 skills**, **17 commands**, **31 hooks** (+1: `notify-attention-required`), and **23 agents**.

## What's New in v3.15.9

v3.15.9 makes `/plan`'s model recommendations portable, and adds a fifth usage monitor.

**Plan routing is no longer locked to the host provider or frozen at authoring time.** A plan phase now records a generic `Recommended model tier` (`frontier` / `strong` / `standard` / `fast`) and a separate `Recommended effort level`, with concrete model ids moved out into a dated, source-cited **Current model map** covering Anthropic, OpenAI, Google, and Cursor. `/plan` refreshes that map from each vendor's own public documentation on every full invocation; `/implement` re-confirms the phase's cell before building, so a plan written before a model release picks up the newer equivalent without changing its stated intent. When web access is unavailable the map degrades to a visibly dated snapshot or an explicit `assess at implementation time`, never a silent collapse to whichever provider you happen to be on. `/route` stays host-native by design: the plan map describes what a phase needs, it does not grant cross-provider switching.

**The new Cursor Usage Monitor** tracks personal Cursor Models and Other Models included-usage meters with on-demand spend context in steel-blue `#4682B4`. It ships with **live fetch disabled entirely**: cached or manually-entered dashboard values drive the UI until a bounded, authorized session-reuse probe verifies a safe live path. Teams spend is kept strictly separate from personal caps and never rendered as a per-member allowance. Installer host isolation is now enforced rather than assumed: the Claude, Codex, and GitHub monitors install only through the VS Code CLI, and the Cursor monitor only through the Cursor CLI, with cross-host installs blocked and asserted by test.

One defect found in the terminal phase is worth stating, because two gates had been hiding it from each other. `flatten_skills` published every `catalog/skills/<category>/<name>/` directory to every platform, while `validate_skills.py --bundles-only` silently skipped the ones carrying no `SKILL.md`. A malformed directory therefore passed every gate and surfaced only as an integration-test failure, and because git cannot represent an empty directory it never reproduced on a clean CI checkout. **A skill directory is now defined by its `SKILL.md`** in both places, fixed once in the shared adapter so Hermes, Cursor, Codex, Antigravity, Qwen, Kimi, and OpenCode are all corrected together. Catalog counts are unchanged at **270 skills**, **17 commands**, **30 hooks**, and **23 agents**.

Shipping caveat recorded rather than glossed: the Cursor monitor's **live visual smoke on a real Cursor host was not executed** for this release (tracked as QG-5). Its automated surface is proven (132 extension tests green, packaging verified in CI, host isolation asserted), but the rendered result on a live host is not.

## What's New in v3.15.8

v3.15.8 closes the platform-capability gap the v3.15.7 audit opened, and adds a fourth usage monitor. Every one of the 18 rows in the platform ownership matrix is now enforceable rather than finding-only: **Codex** receives custom agents as native TOML plus hooks merged into `hooks.json` with a PowerShell command beside every shell one; **Gemini CLI** and **Qwen** receive hooks merged into their own `settings.json`; **Kimi Code CLI** receives agents and a marker-managed `[[hooks]]` block in `config.toml` that preserves the user's comments and tables byte-for-byte; and **Copilot** receives custom agents at `~/.copilot/agents`.

Two of those results are worth stating plainly, because they are the opposite of what the plan assumed. Copilot already reads Nexus-Hub's hooks and project agents through its own default Claude-format read paths, so those surfaces are documented as **inherited** rather than duplicated into commit-visible `.github/` copies. And Hermes discovery probes only direct subdirectories, so the existing flattened skill layout is required rather than merely tolerated - a category-nested migration would have broken it. Where a platform genuinely does not support something, that is recorded instead of inferred: Kimi documents no project-scoped hook path, and Gemini CLI's extension-packaged hooks have no documented direct-write path.

The new **GitHub Usage Monitor** VS Code extension tracks Copilot premium requests and Actions minutes and storage across user, organization, and enterprise scopes. It stores its fine-grained token only in `ExtensionContext.secrets`, never invents a denominator for a quota GitHub does not report, scrapes nothing, and both installers build and install it alongside the Claude and Codex monitors.

Repository hygiene improved alongside the features: every workflow now declares least-privilege permissions and a bounded job timeout, enforced by repo-wide policy tests; a shared `_hooks_common` module replaced the duplication four platform adapters had accumulated; and the GitHub monitor's lockfile is now platform-portable after a native build-time dependency that made it Linux-incomplete was removed. Catalog counts are **270 skills**, **17 commands**, **30 hooks**, and **23 agents**.

## What's New in v3.15.7

v3.15.7 makes security-review conclusions evidence-closed instead of confidence-shaped. Findings now move through four explicit dispositions, rejected findings carry a concrete refutation burden, and `/review` reports exact N-of-M component coverage across multiple traversal altitudes plus proven-dirty sink sweeps. An anti-costume-rigor audit detects claims that sound rigorous without the required comparison evidence, while a deterministic closure gate blocks unresolved claim-to-evidence mismatches.

The release also adds a typed, standard-library-only capability-grant broker above the v3.15.6 endpoint controls. It authorizes one bounded model-emitted action without weakening the sandbox, permission overlay, or provenance controls beneath it. Durable monotonic-scrutiny storage remains intentionally deferred until its invalidation and poisoning-resistance rules are designed and tested.

Two independent fixes are included. Codex Usage Monitor 0.2.7 adds the Extra Credits monthly progress bar, used-versus-limit counts, and reset time while preserving balance-only responses. The installer instruction-merge helper no longer enters an isolated import cycle when loaded in a fresh interpreter. Catalog counts remain **270 skills**, **17 commands**, **29 hooks**, and **23 agents**.

## What's New in v3.15.6

v3.15.6 hardens the seam where a coding agent's file writes become some other program's execution. The threat is rarely a direct sandbox break: the agent writes a workspace file that is legal and in scope, a trusted component outside the sandbox later reads it as its own configuration, and that component runs it at host privilege once nobody is watching. This release matters to Nexus-Hub specifically because one of the disclosed advisories it is built on (CVE-2026-48124) names **workspace-controlled agent-harness hook configuration** as the attack surface, which is exactly the artifact class this installer ships.

The centerpiece is the new **`agentic-endpoint-hardening`** skill: a six-form escape taxonomy, nine control layers each marked enforced / advisory / guidance-only, a privileged-local-daemon enumeration, and a seven-question checklist to put to any agent platform. It defines the **normative execution-trigger surface list** once, split into three groups by what each is matched against (file paths, shell commands, interpreter paths), and every guardrail in the release consumes that one list rather than carrying its own copy. Enforcement ships in three layers: **`escalation-trigger`** now warns on those surfaces (advisory by default, so the catalog never self-blocks its own `nexus-hub init` writes), **`git-guardrails`** blocks the `core.hooksPath` / `core.fsmonitor` execution-indirection commands including the interleaved-option form a glob cannot express, and an **opt-in `--strict-permissions` / `-StrictPermissions`** overlay adds `deny` and `ask` entries on top of the read-only allow list. **Without that flag the install is unchanged**: allow-only and no-prompt. That split is deliberate, convenience by default and hardened on request, not an oversight. A new **`provenance-ledger`** hook records a path and content hash for each agent write and flags a later same-session command that references one, recording paths and hashes only, never file contents.

Every claim above is bounded by something the release states plainly rather than glossing: a pattern denylist is defense-in-depth, not a boundary; a local hook cannot instrument executors in other processes, so full cross-executor seam monitoring is explicitly out of scope; and two of the nine control layers are marked guidance-only because whether a vendor's language extension runs sandboxed is that vendor's architecture, not something a permission file can change.

**Also in this release, beyond that plan: full PowerShell hook parity.** Every `catalog/hooks/*.sh` now ships a `.ps1` sibling, taking coverage from 8 of 25 to **25 of 25**, so Windows users who run hooks through PowerShell get every guardrail instead of two thirds of them. A generic parity harness enforces the invariant in both directions, a syntax floor per file, and exit-code agreement per pair, so hooks nobody has written yet are protected too.

**Six real defects were found and fixed, four of them only because assertions run against both implementations.** `escalation-trigger.sh` had never fired in production (it read an environment variable Claude Code does not set). `session-summary.ps1` had not parsed since v3.11.0, so that hook was dead on Windows for four minor versions. The two description gates silently failed to **block** on any host without `jq`, because a `grep` matching nothing aborts a `set -e` script before it reaches its refusal. Plus a UTF-8 BOM and a `sha256sum` filename-escaping bug that no POSIX-only test could reach. A long-standing note claiming "bash cannot be fully exercised on the Windows dev host" was also disproven: it was PATH shadowing, and 103 test failures carried across several releases are now structurally fixed. Catalog: **270 skills** (+1: `agentic-endpoint-hardening`), **17 commands**, **29 hooks** (+1: `provenance-ledger`), 25 of 25 with PowerShell siblings.

## What's New in v3.15.5

v3.15.5 gives Nexus-Hub a way to keep pace with new model releases instead of drifting behind them, and lowers what a fresh install costs per turn. The centerpiece is **`model-prompting-research`** plus the **`/tune-prompting`** command: run it the day a model ships and it enumerates the live model roster from whatever platform you are on (never a hardcoded list), reads each model vendor's OWN prompting documentation, cookbook, model card, and changelog, and records only the claims that survive an adversarial refutation pass backed by a primary source. Verified guidance lands in a **per-model profile layer** bundled with the skill, schema-valid by construction and hard-gated in validation, with a deterministic planner and writer owning the two ends of the pipeline that an LLM does inconsistently. **The safety story is a hard rail**: guidance that is true of one model can only ever reach that profile layer, and the apply engine blocks any edit that would introduce a model identifier into a shared body regardless of what the finding claims. Only genuinely model-agnostic authoring improvements are eligible to touch a `SKILL.md`, a command, or a `base-*.md`, and those are applied one edit at a time behind the full guard suite on an isolated branch that auto-reverts anything a guard rejects and always stops for human merge. Building it disproved the design's own premise: `check_base_template_parity.py` does NOT prevent model-specific content from reaching a shared body (it compares the five templates to each other, so the same model-named line in all five is perfect lockstep and passes), so the rail was moved into the engine and a paired test now pins the guard's real behaviour so the false premise cannot return. `/update release` gains an **advisory** staleness check that reports roster drift and offers to refresh, deliberately never blocking a release, because models ship on the vendor's clock. Separately, the **installed default reasoning effort drops from `xhigh` to `medium`**, so the deeper tiers become a deliberate per-task escalation rather than a standing cost on every turn (raise it any time with `/effort`). Also fixed: pre-existing catalog count drift in `data/` that no gate was checking, now guarded by a registry-consistency test. Catalog: **269 skills** (+1: `model-prompting-research`), **17 commands** (+1: `/tune-prompting`), **28 hooks**.

## What's New in v3.15.4

v3.15.4 makes the **`/presentify`** skill's output visually faithful and self-correcting, fixing four defects observed on a real board-deck run. **Full-width is now a concrete, measurable canvas contract** (the shell spans the viewport via gutters, not a centered column; the widest band reaches at least ~95% of a 1920px viewport, with no global zoom), honored in both the LLM-native path and the deterministic baseline builder (a new `--layout {full|standard|portrait}`). **Images are sized with discipline**: a hero is capped at ~80vh, a low-prominence secondary can no longer balloon past a hero, `object-fit: contain` prevents meaningful-content crops, and a dead-space ceiling keeps bands tight. **Annotated figures keep their annotations**: a map's author-added regions and labels are recreated as a registered, interactive overlay on the base image (confidence-gated, with a view-original toggle) instead of being dropped to a textual list. **Stock/mix imagery reliably integrates**: consent is captured up front, image-starved sections are detected, and a gate fails a consented run that silently added nothing. All of this is enforced by a new **iterative multi-agent visual-QA self-critique loop** that renders the page, grades each segment against its source and a measurable rubric, adversarially verifies, synthesizes fixes, and re-renders until a page-level bar passes, degrading gracefully to a deterministic structural scorer when no headless browser is present. A `--qa-depth {light|standard|deep}` knob bounds the loop's cost. Entirely inside the existing skill bundle and command: no new distribution channel and no new outbound call, dependency, or credential. Catalog unchanged: **268 skills**, **16 commands**, **28 hooks**.

## What's New in v3.15.3

v3.15.3 adds **`anti-slop-editing`**, a dedicated prose de-slop skill, reverse-engineered skill-native from an MIT-licensed external skill (no new code, outbound call, dependency, or credential). It removes 20+ named AI-slop patterns (binary contrasts, throat-clearing openers, importance puffery, robotic rhythm, fake-profound kickers, formatting slop, and more), each with a quoted smell and a concrete before/after fix, while preserving the writer's voice. It runs in two modes: **Edit** (default) makes the minimum effective edit and reports what changed; **Detect** names each pattern with a quoted line and a short fix without rewriting, scoring, or guessing AI authorship. It ships two on-demand reference files (a banned-word / empty-phrase list applied with judgment, and a pass/fail self-check rubric the skill grades its own output against before returning) plus a routing-eval file, and adopts the project em-dash ceiling (no em-dashes, no clause-joining spaced hyphens). The single-line description was lexically co-engineered against the trigger-and-routing gate so a de-slop request routes to it ahead of the generic `writing-editing` and the UI-focused `hallmark-design` skills. Catalog: **268 skills** (+1: `anti-slop-editing`), **16 commands**, **28 hooks**.

## What's New in v3.15.2

v3.15.2 gives the 267-skill catalog its first deterministic, model-free skill-quality gate and extends the platform roster. The headline is a **trigger-and-routing eval** (`scripts/run_trigger_evals.py`, Python stdlib only, zero outbound): it flags any two skill descriptions whose trigger vocabulary near-collides (a containment metric over stopword-filtered, lightly-stemmed tokens) and, for skills that ship an optional `evals/trigger-cases.json`, asserts that real prompts route to the intended skill first and clear near-miss look-alikes by a margin. First-run triage over all 267 skills fixed one genuine collision (the broad `technical-documentation` skill now defers to `architecture-decision-record` and `project-constitution` via a SKIP clause) and allowlisted 39 by-design category siblings; the eval is now a **hard CI + `make validate` gate**. A companion **unfilled-placeholder lint** in `validate_skills.py` fails any skill shipping an unfilled `<multi word placeholder>` in its description or body (single-word CLI notation like `<path>`, `<MAJOR>` tokens, HTML tags, and fenced examples are exempt). On the tooling side, `skill-eval-loop` gains a **behavioral-eval schema converter** (`skill_eval_convert.py`) that losslessly round-trips its internal `evals.json` to and from an interoperable schema for external skill-eval tools, and a new **Hermes** platform integration (registry-registered, runner-installable, detection-gated) mirrors flattened skills to `~/.hermes/skills/` while reading the shared `~/.agents/skills/`. Everything is local-first (no new outbound call, dependency, or credential); catalog counts unchanged: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.15.1

v3.15.1 adds a **CodeSight context-map** to the `nexus-code-search` extension: a deterministic, committed map compiled from the extension's existing tree-sitter AST graph, so an AI reads a cheap cold-start map once (`<root>/.nexus/CONTEXT-MAP.md` plus a `.nexus/context/` article set) instead of re-exploring files every session. It is exposed as a `nexus-hub map` CLI verb and a `generate_context_map` MCP tool, with framework-aware extraction (HTTP routes, ORM schema with relations, React components, env-var audit, middleware, background events) gated by a per-section recall + zero-false-positive accuracy harness. Companion surfaces: `nexus-hub map --since <ref>` (a git-scoped change map), `nexus-hub map --lint` (`map_health`: orphan articles / missing backlinks / staleness), `nexus-hub map --knowledge` (`generate_knowledge_map`: a `.nexus/KNOWLEDGE.md` from Markdown notes), and a regression-guarded token-savings benchmark (~44-55% reduction on the sample corpus, ~99% on Nexus-Hub itself). Entirely extension-local (no new outbound call, dependency, or credential; no catalog registry, installer, or `base-*.md` change); the extension package moves 2.0.0 -> 2.1.0. Catalog counts unchanged: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.15.0

v3.15.0 brings every supported platform to full surface parity: each platform now receives all the Nexus-Hub surfaces it can actually consume (skills, commands, agents, rules, hooks), re-verified against each platform's current official docs. **Cursor** reaches full parity (flattened skills, every command as a skill and a project `.cursor/commands/` file, subagents, and a Cursor-schema `hooks.json` carrying `git-guardrails`). **OpenCode** gains the subagents surface (`~/.config/opencode/agents/`). **Qwen Code** and **Kimi** are reclassified from instruction-file-only guardrails to full skills-bearing integrations (Qwen ships Markdown commands since its TOML path is deprecated; Kimi is migrated to the current Kimi Code CLI product at `~/.kimi-code/`). **GitHub Copilot**'s opt-in skill seeding is widened from an on/off toggle to a bundle-or-all selector (`NEXUS_HUB_COPILOT_SKILLS`). Under the hood, `hooks_supported` becomes the single load-bearing hook-capability signal (the dead `permissions_file` config key is removed), and the platform read-contract is re-verified for all parity targets and re-stamped for this release. No catalog change; counts unchanged: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.7

v3.14.7 is a cosmetic fix for both usage-monitor VS Code extensions (no catalog change; counts unchanged). The status-bar items rendered the icon glued to the usage text (`icon47% (current)...`) because VS Code collapses consecutive plain spaces in a status-bar label. Both extensions now place a non-collapsing en-space (U+2002) between the icon and the label, so the icon reads with a small, consistent gap before the numbers. Extension versions bumped **Claude Usage Monitor 0.9.3** and **Codex Usage Monitor 0.2.4**. Catalog: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.6

v3.14.6 fixes the Codex Usage Monitor's auto-fetch, unifies both usage monitors' settings UX, and modernizes the installer's console output (no catalog change; counts unchanged). The **Codex Usage Monitor** now pulls your real usage automatically like the Claude monitor does: the root cause was a schema mismatch (the mapper read `rate_limits`/`primary`/`secondary`, but the live endpoint nests the windows under `rate_limit`/`primary_window`/`secondary_window`), so a weekly-only plan came up empty. The mapper now reads the verified schema and classifies each window by its real duration, and the manual-entry fallback is removed (auto-fetch is the path; a genuine failure shows an honest diagnostic). **Both monitors** drop the status-bar gear icon and render **Settings inline under the dashboard** (toggled by the dashboard gear, state-persisted, fonts unified with the dashboard) instead of opening a separate panel, and the status-bar items stay grouped (Copilot no longer wedges between them). The **installer log** is flattened to single-level `UPPERCASE` sections, "Usage Monitors" is renamed **VS CODE EXTENSIONS**, skill discovery + git hook + report templates are grouped under **CROSS-PLATFORM TOOLS**, project seeding is folded under **INSTALL VERIFICATION**, and the stray blank-line spacing is cleaned up. Catalog: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.5

v3.14.5 modernizes the installer output, fixes the Codex Usage Monitor, and makes per-release platform-contract verification a hard gate (no catalog change; counts unchanged). The **installer** now prints a per-platform checklist in a fixed surface order (Core Files / Skills / Commands / Agents / Rules / Hooks / Core Settings) with real install paths, groups undetected platforms into one "NOT DETECTED (skipped)" section instead of reporting them as installed, colors every vendor, tightens end-of-run spacing, and splits the VS Code utilities into Anthropic (Claude Usage Monitor) and OpenAI (Codex Usage Monitor) sections. The **Codex Usage Monitor** gains a manual-entry fallback (so it is useful even when the undocumented usage endpoint can't be read), an honest and actionable empty state, a theme-adaptive dashboard tab icon, correct status-bar ordering across both extensions ([Claude usage][Claude gear][Codex usage][Codex gear]), and a `compactStatusBar` toggle. A new **mandatory contract-verification gate** consolidates the "expected read-paths per platform" data into one machine-readable `docs/policy/platform-read-contracts.json` (consumed by both the code-vs-contract checker and the runtime `nexus-hub verify` pass) and adds `check_platform_contract_freshness.py`, which fails `make validate` and CI unless the contract was re-verified for the release being cut. That release-time re-verification web-checked all 13 platforms and fixed three dead-path installer bugs (**OpenCode** `~/.config/opencode/`, **Kimi** `.kimi/AGENTS.md`, **OpenClaw** `~/.openclaw/workspace/`); the additive drift it surfaced (Copilot / Cursor / Codex / OpenCode have gained native skills / agents / hooks surfaces) is routed to the v3.15.0 platform-parity release. Catalog: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.3

v3.14.3 fixes `/presentify` end-to-end and reworks its design intake (no catalog change; counts unchanged). First, it restores skill loading: `document-to-interactive-html` (and 46 other skills) carried an unquoted `description` frontmatter value containing a `: ` sequence that broke strict YAML parsing, so the skill silently failed to load with "Unknown skill" - the values are now quoted, a strict-YAML gate in `validate_skills.py` prevents regression, and both installers now flatten skills for Claude to the discoverable `~/.claude/skills/<name>/` layout instead of an undiscoverable category-nested copy. On top of that, `/presentify` now asks its four high-level design questions - style, layout, interactivity, imagery - in a single batched round UP FRONT before any document is read (instead of one menu at a time mid-pipeline), and never pre-answers a choice from a recalled memory or saved preference. The imagery choice now prefers real license-free stock and minimizes AI, and offers gated license-free stock video (Pexels key + consent, degrading to images-only otherwise), reconciling the old "video out of scope" wording so source-embedded media stays ignored while output-side stock video is supported. And a new guided `nexus-hub setup-media` bring-your-own-key flow stores a free Pexels key securely under `~/.nexus-hub/` (hidden prompt, mode 0600) so stock video "just works" - stock images still need no setup.

## What's New in v3.14.2

v3.14.2 is an internal convention fix (no catalog change; counts unchanged). It closes a systemic flaw where a `/compare` report and the `/plan from-comparison` plan it seeds could land in different version directories. A comparison now declares an `Adoption target: vX.Y.Z` and is versioned and placed by the release that will ADOPT it rather than the authoring cycle (Fix A); `/plan from-comparison` reads that field and co-locates the generated plan in the same version tree, degrading gracefully for comparisons authored before the convention (Fix B); and the `documentation-consistency` audit plus a dedicated CI workflow flag any comparison/plan version-directory drift so the misplacement cannot silently recur (Fix C). All edits are instruction-level (command and skill-body changes that auto-distribute via folder copy), with `docs/archive/**` and prior-major trees grandfathered.

## What's New in v3.14.4

v3.14.4 splits the usage monitor into two separate VS Code extensions. The v3.14.0 build had folded Codex monitoring into the Claude extension behind a provider switch (renaming it "Claude & Codex Usage Monitor"), which mislabeled the Claude monitor and buried Codex behind a setting. It is now two independently-installable, branded extensions that run side by side: the **Claude Usage Monitor** (`nexus-hub.claude-usage-monitor`, reverted to Claude Code only) and a new **Codex Usage Monitor** (`nexus-hub.codex-usage-monitor`) with its own identity, icon, status-bar glyph, and periwinkle `#5244BB` progress bars, tracking what Codex exposes (the plan tier in place of a model, extra rate-limit windows, a credits line) with throttle / pace / wait / rotate recommendations. The two share no extension id, command, storage key, or view, so installing one never affects the other. Both installers build and install both; each has its own path-filtered CI workflow and dependabot entry. Catalog counts unchanged: **267 skills**, **16 commands**, **28 hooks**.

## What's New in v3.14.1

v3.14.1 is an installer hotfix (no catalog change; counts unchanged). A global install run from an arbitrary working directory (including an elevated `C:\Windows\System32` prompt) no longer emits a `PermissionError [WinError 5]` traceback for each integration and now writes its install manifest under `~/.nexus-hub/` regardless of the working directory, with a manifest-write failure degrading to a warning instead of aborting the run. And re-running the installer (or `nexus-hub upgrade`) now unregisters the orphaned DevAI-Hub "Claude Code Auth Monitor" Windows scheduled task and sweeps its leftover `run-auth-monitor.vbs` launcher, stopping the recurring "Can not find script file" popup. Users who cannot re-run yet can remove the task manually with `Unregister-ScheduledTask -TaskName "Claude Code Auth Monitor" -Confirm:$false`. Both fixes are installer-side only (in `scripts/lib/integrations/`), so they auto-distribute with no installer copy-step edit and no platform-template change.

## What's New in v3.14.0

v3.14.0 is the codex-lb adoption release: it brings a directly-requested product build plus four skill-native agentic-review disciplines reverse-engineered from an external Codex workflow, with zero new outbound calls, dependencies, or credentials in the catalog. The headline build is the **Codex Usage Monitor**: the `claude-usage-monitor` VS Code extension (independently bumped to 0.7.0) is generalized behind a `UsageProvider` interface and gains a second provider for Codex (ChatGPT / OpenAI) that reads the local Codex app OAuth token and renders account usage in the same status-bar, tooltip, dashboard, and warning UI as Claude, with its single outbound call going only to the user's own account endpoint. On the catalog side, a **skill-native review and verification cluster** adds a `review-trapdoors` skill and convention (a project's curated list of recurring, project-specific review blockers, each applied as a gate) and a machine-checkable **merge-readiness contract** in `quality-gate-definitions`, and folds a PR/CI-state evidence discipline into `verification-before-completion`. A **spec/context split** convention extends `spec-driven-development` with a normative `spec.md` (testable requirements only) separated from free-form context, plus a spec-as-merge-gate rule. A **declarative skill-activation ruleset** (`skill-rules.json`) with three opt-in, fail-open hooks gives the model-judgment triggering a deterministic, suggest-by-default backstop. And a **cross-model review loop** recipe in `cross-model-orchestrator` documents a vendor-neutral, loop-until-clean review flow. Catalog: **267 skills** (+1: `review-trapdoors`), **16 commands**, **28 hooks**.

## What's New in v3.13.0

v3.13.0 is the presentify reach-and-voice release: `/presentify` and its `document-to-interactive-html` skill now ingest almost anything and give the output a professional, journalistic visual voice - without ever breaking the single-file, offline, zero-external-request guarantee. **Universal ingestion**: beyond the four document formats, the extractor now reads source code and config, Markdown / plain text, CSV / TSV, and standalone images, and can take a whole directory or repository (walked recursively, with ignore rules, a best-effort `.gitignore` matcher, a binary sniff, and file / byte caps) - a repo becomes a synthesized overview, a navigable file tree, README-first ordering, and code grouped by directory. Dominant source visuals keep their **prominence** (a hero stays a hero, never flattened into a thumbnail grid), and a new `--layout` control picks the output **aspect** (full-width / standard / portrait). **Tiered imagery** gives the output its designed look: Tier 1 (the always-on, zero-outbound default) authors original procedural visuals as inline SVG / CSS (color fields, editorial devices, generative textures); Tier 2 (opt-in, consent-gated) fetches license-free, free-for-commercial-use stock images from Openverse / Wikimedia / Pexels at build time; and Tier 3 (opt-in, LOCAL-only) generates images with a local commercially-clean model (a hosted generation API is a policy hard-no). Every fetched or generated asset is license-verified, base64-embedded so the page still opens offline, and recorded in a visible credits block. A new **interactivity level** (restrained / balanced / rich scrollytelling) tunes how the page responds, always reduced-motion-guarded. Everything stays local-only with zero telemetry; catalog counts unchanged: **266 skills**, **16 commands**, **25 hooks**.

## What's New in v3.12.1

v3.12.1 makes every Nexus-Hub skill and command actually discoverable in the new ChatGPT desktop app (Chat + Work + Codex) and the Antigravity IDE, and hardens the install against future platform format drift. Codex and the desktop app discover skills one level deep, but the installer was copying the catalog two levels deep (buried under a category folder), so nothing registered; skills are now flattened into `~/.codex/skills/` and the cross-tool `~/.agents/skills/`, and every command surfaces both as a slash command and as a reusable skill (`$presentify`, `$implement`, ...). Antigravity's global content now lands where the IDE actually reads it (`~/.gemini/config/skills/`, `~/.gemini/config/global_workflows/`, `~/.gemini/GEMINI.md`) instead of an unread path. The same one-level flattening plus command-skills fix extends to Claude, Gemini, Gemini CLI, OpenCode, and Nexus-AI, whose native skill folders were silently broken by the nested layout. A new living read-contract (`docs/policy/platform-read-contracts.md`) plus a three-layer verification gate keeps it correct: a deterministic code-vs-contract check in `make validate`, a corrected `nexus-hub verify`, and a new `/update release` step that re-verifies each platform's current discovery format via web search every release. Catalog: **266 skills** (+1: `platform-contract-verification`), **16 commands**, **25 hooks**.

## What's New in v3.12.0

v3.12.0 is the presentify fidelity-and-variety overhaul: `/presentify` and its `document-to-interactive-html` skill no longer drop source visuals, no longer guess at figures, no longer ship static-feeling pages, and no longer converge to one look. The extractor now captures PDF embedded images (with repeated-asset dedup and caption pairing), detects and rasterizes vector-figure regions (plots, maps, diagrams - the norm in decks exported to PDF), reads scanned / image-only PDFs through a two-tier path (local OCR via optional `rapidocr-onnxruntime`/`pytesseract` with per-block confidence, plus an always-on full-page image for agent-vision reading - zero installed OCR engines still means zero content loss), recurses PPTX grouped shapes, extracts native PPTX/DOCX chart objects with their real series values, and emits a per-source coverage manifest that the new COVERAGE RECONCILIATION gate audits: every visual must end rendered, reconstructed, or explicitly skipped with a reason. Data-bearing figures go through a new figure-reconstruction protocol - classification, an auditable read-the-figure worksheet, fidelity cross-checks, and a three-tier confidence gate under which low-confidence figures ship as pan/zoom originals, never invented numbers. Every run now carries a five-point minimum interaction budget (active-state nav, scroll reveals, hover/focus affordances, lightboxes on every non-decorative image, one signature interaction), and a new stdlib design-entropy engine (`design_seed.py`: 12 hue families x light/dark, preset-constrained pools, seeded rolls, a persisted run history with a 2-of-3-axes rejection rule) makes same-preset reruns provably different. A committed worked example replays the original failing case (a PDF saved from PowerPoint) twice with the same preset: ground-truth-exact reconstruction, 0 unaccounted visuals, and two unmistakably different designs. A path-filtered CI workflow now guards the extractor. Catalog counts unchanged: **265 skills**, **16 commands**, **25 hooks**.

v3.11.4 is a small catalog patch bundling two changes. The Nexus-AI integration now installs the entire catalog under `~/.nexus-ai/catalog/` instead of the `~/.nexus-ai/` root - reserving the root for the Nexus-AI app's own data home (settings, MCP config, model weights, sessions, credentials) so a catalog refresh can wipe-and-refetch its own subtree without risking app data - and writes a timestamp-free `nexus-hub-version.json` at the catalog root that gives the desktop app a first-class update-detection contract (installed version plus the public releases endpoints). Separately, the `docs-layout-refactor` skill (1.2.0 -> 1.3.0) gains universal handling for cross-cutting, non-versioned documentation subtrees: it now recognizes the widely-adopted standards (architecture decision records, RFCs, specifications, governance policy, the Diataxis content quartet, runbooks, and static-site-generator output) as one conservative disposition class that is never version-archived or reclassified by semantic content, giving `/plan` and `/implement` a canonical rule instead of inventing one. No catalog change; the v3.11.0 feature set below ships unchanged.

v3.11.3 is an extension-only patch: it relabels the Claude Usage Monitor usage-warning's primary dismiss button from "Cancel" to "OK", which reads correctly as acknowledging and closing the warning. The warning itself (added in v3.11.2) is a compact WebviewView in its own narrow activity-bar container that reveals automatically when a usage threshold is crossed - polling tightens to about once a minute as usage nears a threshold, so the warning is timely - and dismisses cleanly, rather than a notification toast or a full editor tab. Extension 0.6.1 -> 0.6.2. No catalog change; the v3.11.0 feature set below ships unchanged.

v3.11.0 turns a set of implicit good practices into command-enforced workflow defaults across the catalog. It standardizes the per-version docs layout on a canonical `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` scheme, adds project-bootstrap governance, makes every generated plan end with a mandatory architecture-refactor + known-gaps + CI/CD phase, hardens `/compare` and `/presentify`, verifies that every install actually surfaces the catalog on every platform, and migrates the Nexus-Hub repo itself to follow all of it. It also lands four reverse-engineer-first skill-pack adoptions (six new skills plus several skill-native enrichments). Catalog: **265 skills**, **16 commands**, **25 hooks**.

Highlights:

- **Command-enforced workflow governance** (v3.11.0): `/setup` detects and bootstraps git, a `vX.Y.Z` version, a `develop` + feat/fix/refactor>develop>main branch model, and the per-version docs tree; `/describe` and `/review` report a Project-health block and offer a `/setup` handoff. Backed by two reconstituted delegate skills (`setup-project`, `analyze-codebase`) and the reconstituted `implement-phase` skill.
- **Mandatory final refactor phase** (v3.11.0): every plan `/plan` generates now ends with an architecture-refactor + known-gaps-reconciliation + CI/CD-optimize phase, which `/implement` runs on a plan's final phase (even for plans that predate the rule) and `/update release` enforces. `project-refactor` gains empty-dir, duplicate, orphan, and structure-complexity detection.
- **Canonical docs-layout scheme** (v3.11.0): active docs at `docs/v<MAJOR>/v<MAJOR>.<MINOR>/` and archive at `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/`, each with `plans/` and `comparisons/` subdirs; patch releases share their minor dir with release-prefixed artifact filenames.
- **Command robustness** (v3.11.0): `/compare` runs a source-security scan (prompt-injection / malicious-instruction / supply-chain) before ingesting any external source and files reports under `comparisons/`; `/presentify` renders, screenshots, and visually assesses its own output, iterating on graphic defects.
- **Cross-platform distribution robustness** (v3.11.0): every install is verified against each platform's real read-path (not assumed from a successful copy), project-only surfaces auto-seed, a post-install `nexus-hub doctor` reports PASS / NEEDS-ACTION per platform, and a cross-OS CI `install-smoke` job fails a PR if any read-path would go empty.
- **Skill-pack adoptions** (v3.11.0): four reverse-engineer-first adoptions land six new skills and several enrichments - `implementation-convergence` (post-implementation code-vs-plan gap check behind a new `/spec converge` scope) and `label-gated-agent-pipelines` (human-gated CI agent pipeline) from the spec-kit adoption; `youtube-transcript` (local `yt-dlp` captions) plus a portable research-brief technique and an opt-in grill-me mode from the davidondrej adoption; local-agent-hijack recognition across `prompt-injection-defense` / `agent-access-policy` / `ai-attack-patterns` and a reproducible-benchmark-receipt discipline from the t3mp3st adoption; and an optical / image-token compression doctrine from the pxpipe adoption. GitHub Copilot also gains an opt-in native `.github/skills/` project surface.
- **Claude Usage Monitor v0.5.5 -- Extra Credits in the hover tooltip** (v3.10.3): the status-bar hover tooltip shows an Extra Credits section in the same order as the dashboard. When extra credit is available it renders a utilization bar plus "$X / $Y used this month" and the monthly reset date; when the account has no extra-credit limit it reads "No extra credit available on your account".
- **`egress-redaction` defensive skill**: a typed sensitive-data / PII taxonomy with a per-category policy action (BLOCK / REDACT / HASH / PASS) applied before any artifact crosses a trust boundary (a cross-model handoff, a context pack, a log, an external send), with a default-policy table and a per-egress-event rule.
- **`prompt-injection-defense` defensive skill**: the recognition-and-posture counterpart to `ai-attack-patterns` -- instruction-origin discipline, untrusted-content fencing, tool-output skepticism, indirect-injection recognition cues, and a safe-response rule.
- **`nexus-hub verify` supply-chain command**: recomputes installed-file SHA-256 and diffs against a release-published `MANIFEST.sha256`, reporting OK / MODIFIED / MISSING / EXTRA per file with a single PASS / FAIL. Strictly local and read-only (stdlib only) -- no network call, no credential, no new dependency.
- **Agent-setup grade + regression diff**: `harness_audit.py` gains an explainable 1-100 setup grade across six weighted dimensions and a cross-snapshot regression diff (advisory by default; gates only with `--fail-on-regression`), surfaced through `skill-stocktake`.
- **Iterative competitive-generation**: `competitive-generation` gains a hill-climbing / co-evolution section -- run the competition over multiple rounds seeded by the previous winner, with a no-progress stopping rule and a token caution.
- **Two advisory worker-check hooks**: `test-gap-notice` (flags source edits with no companion test) and `dependency-staleness-notice` (flags dependency-manifest edits with the matching audit command) -- event-driven, advisory-only, disableable, never a daemon.

See [CHANGELOG.md](CHANGELOG.md) for the full v3.11.0 entry and the complete release history.

---

## Supported Agentic Platforms

| Platform | Install target | Path | Per-platform surface |
|---|---|---|---|
| Claude Code (Anthropic) | `~/.claude/` + project `.claude/` | legacy + registry | Full: skills, commands, hooks, agents, rules, MCP configs |
| OpenAI Codex CLI | `~/.codex/` + project `.codex/` + `AGENTS.md` | legacy + registry | Full: skills (under `skills/`), commands (under `prompts/`), agents, rules |
| Gemini (IDE / Antigravity 1.0) | `~/.gemini/` + project `.gemini/GEMINI.md` | legacy + registry | Full: skills, commands (under `workflows/`), agents, rules |
| **Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)** | `~/.gemini/commands/*.toml` + project `.gemini/commands/*.toml` | **registry (new in v2.1.0; gated behind `--enterprise` / `-Enterprise` flag in v2.2.0)** | TOML-format custom commands generated from `catalog/commands/*.md`. Non-enterprise users transition to Antigravity CLI before 2026-06-18 per the 2026-05-21 Google announcement. |
| **Antigravity 2.0 + CLI (Google)** | `~/.gemini/antigravity-cli/` + project `.agents/` | **registry (new in v2.1.0, CLI coverage added v2.2.0; paths verified v2.3.0)** | Full: skills, commands (under `workflows/`), subagents, rules. Single integration covers both the desktop IDE and the standalone Antigravity CLI (`agy` binary), verified 2026-05-29 against Google's public Antigravity CLI docs. |
| GitHub Copilot (VS Code) | project `.github/copilot-instructions.md` | legacy + registry | Behavioral guardrails (skill index embedded as text); merge semantics if the file already exists |
| Cursor | project `.cursor/rules/*.mdc` + `AGENTS.md` | registry | Per-rule `.mdc` files + behavioral guardrails (skill index embedded as text) |
| OpenCode | project `AGENTS.md` + `.opencode/` | registry | Behavioral guardrails + skills mirror |
| **Nexus-AI (Local Studio)** | `~/.nexus-ai/catalog/` + project `.nexus-ai/catalog/` | **registry (new in v2.1.0)** | Full mirror: skills, commands, agents, rules, hooks, MCP configs, templates, plus a `nexus-hub-version.json` manifest. Isolated under `catalog/` so the app's own data at the `~/.nexus-ai/` root stays outside a catalog refresh. |
| GitHub CLI (`gh`) | via `gh copilot` extension | indirect | Skill / command references via `AGENTS.md` open standard |
| Nexus desktop app | upstream consumer | indirect | Reads the same catalog as its skill feed |
| Nexus VS Code extension | upstream consumer | indirect | Reads the same catalog as its skill feed |

**Coverage caveat**: the **registry** path (introduced in v2.1.0 Phase 10) dispatches install / teardown through `scripts/lib/integrations/runner.py` and supports a `--dry-run` mode. The **legacy** path (the long-standing in-installer copy blocks) continues to be the canonical install for Claude / Gemini / Codex / Copilot until v2.2.0 parity migration (tracked as DF-001 in `docs/archive/v2/v2.1/known-gaps.md`). Both paths produce the same end-state on disk for those platforms; the per-platform installer logic lives in [`scripts/installer.sh`](scripts/installer.sh), [`scripts/installer.ps1`](scripts/installer.ps1), and the per-platform subclasses under [`scripts/lib/integrations/`](scripts/lib/integrations/). Per-platform capability specs (install surface, distributed content, instruction file, quirks) are documented under [`docs/specs/`](docs/specs/).

**Branch-based install** (v2.4.0): pass `--branch <name>` (Bash) or `-Branch <name>` (PowerShell) to install the catalog from a pushed branch instead of the current checkout. The installer shallow-clones the repo at `<name>` into a deterministic cache directory (`~/.nexus-hub/branches/<sanitized-name>/`) and runs the install from that checkout, so the user's working copy is never touched. The branch name is sanitized for filesystem safety (path-traversal sequences are neutralized). Combine with `--check` / `-Check` for a clone-free probe that prints the resolved cache path and clone source.

---

## Quick Start (one command)

Open a terminal and paste the line for your system. It downloads the catalog from this repo and runs the installer -- no clone, no unzip, no `cd`.

**macOS / Linux** (paste into Terminal):

```bash
curl -fsSL https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

No `curl` on the box? Use `wget`:

```bash
wget -qO- https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.sh | bash
```

**Windows** (paste into PowerShell):

```powershell
irm https://raw.githubusercontent.com/bendourthe/Nexus-Hub/main/install.ps1 | iex
```

That is the whole setup -- no prompts. The installer prechecks its dependencies (and tells you exactly what to install if one is missing), then performs a global install across every supported assistant it detects; assistants you do not have are skipped with a note, never an error. Your customizations are preserved (marker-merge), and on a re-install it asks once only if it finds a managed file you changed that it would overwrite, naming the file.

**Done.** The installer writes to `~/.nexus-hub/` (the user-global catalog) and into each supported assistant's per-platform config locations. If a legacy `~/.devai-hub/` install is detected, you will see a single migration prompt at the top of the run -- answer `Y` (default) to migrate in place.

After the installer completes:

- **Globally**: your user profile has all 273 skills, 18 commands, 31 hooks, 23 agents, plus Gemini and Codex instructions.
- **Locally**: your project has `copilot-instructions.md` and `AGENTS.md` tailored to your language.

**Power-user flags**: `--workspace <path>` installs into a single repo instead of globally; `--platforms <comma-list>` limits the install to a subset of assistants; `--yes` runs fully unattended (refreshes managed files with no prompt -- ideal for CI). Prefer to clone first? `git clone` the repo and run `./install.sh` (macOS / Linux) or `install.bat` (Windows) -- the in-repo path still works exactly as before.

### Installing a subset (selective installation)

By default you get the whole catalog. If you want a smaller install, pick a **profile**, one or more **capability modules**, or one or more **role bundles**. Selectors combine by union.

```bash
# macOS / Linux
bash scripts/installer.sh --profile core
bash scripts/installer.sh --modules ai-engineering,testing
bash scripts/installer.sh --bundles ai-engineer
bash scripts/installer.sh --profile core --modules security-operations   # union
```

```powershell
# Windows
.\scripts\installer.ps1 -Profile core
.\scripts\installer.ps1 -Modules ai-engineering,testing
.\scripts\installer.ps1 -Bundles ai-engineer
```

Profiles are `minimal`, `core`, and `full`. Modules group skills by capability (one per catalog category, so every skill is reachable through at least one). Role bundles are curated cross-category sets like `ai-engineer` or `devops-engineer`. List what is available with `python scripts/lib/installer/selection.py --repo-root . --profile core` , which prints the resolved plan without installing anything.

Three things worth knowing before you narrow an install:

- **Hooks, rules, templates, and settings always install**, under every selection including `minimal`. Narrowing your skill set asks for fewer capabilities, never for fewer guardrails.
- **Commands and agents follow their skills.** A command that is a thin pointer over one skill (for example `/implement` over `implement-phase`) installs only when that skill is selected; everything else installs regardless. So a focused install stays coherent instead of leaving commands that cannot do anything.
- **No selector means the full catalog**, byte-for-byte identical to what you would have got before selective installation existed.

`nexus-hub upgrade` re-applies whatever you selected, so an upgrade never quietly widens a focused install back to everything. To change scope, pass a new selector; to go back to everything, pass `--profile full`.

Selectors need Python to resolve. A full install does not.

### Keeping it current

Run `nexus-hub upgrade` -- it reports your installed version against the latest, shows a short what's-new summary, and updates in place on confirmation. Re-running the install command above works too; the installer is idempotent.

### Verifying your install

Run `nexus-hub verify` to confirm your installed catalog matches the published release. It recomputes the SHA-256 of every file in the catalog tree and diffs the result against the `MANIFEST.sha256` that ships with each release, reporting any file that is modified, missing, or unexpected, then a single `verify: PASS` or `verify: FAIL` line. It is strictly local: it reads only local files, makes no network call, needs no credential, and adds no dependency.

What this does and does not prove: `verify` detects on-disk tampering or corruption AFTER install, relative to the published catalog. It is trustworthy to the extent the manifest itself came from the release you trust (it rides inside the same signed release tag the installer pulls from). It is NOT a code signature and NOT a substitute for verifying the download channel -- an attacker who can rewrite both a file and the manifest in the same tree defeats it. Use it to catch accidental corruption and post-install drift, not to establish first-trust in the bytes.

### Add organization standards

Connect a validated local-directory or Git bundle with `nexus-hub org connect <path-or-url>`, inspect it with `nexus-hub org status`, and then reinstall or repair the target workspace. Nexus-Hub projects the organization's concise core and rule files into existing platform surfaces without uploading the bundle or claiming policy enforcement. See the [Organization Knowledge Layer guide](guides/ORG_KNOWLEDGE_LAYER.md) for the bundle contract, lifecycle commands, precedence model, authoring workflow, and rollback procedure.

---

## What is Nexus-Hub?

Most AI assistants are generic by default: they know a lot but specialize in nothing. Nexus-Hub is the layer that turns a generic assistant into a specialist for the work you actually do.

It does three things:

1. **Behavioral rules** -- per-language code-style and security rules that tell the assistant how to write code in your project (not just whether the code compiles).
2. **Autonomous skills** -- 208 curated capability prompts grouped into 22 categories. Each skill has a 3-tier loading model (always-loaded summary, body on trigger, deeper references on demand) so context cost stays proportional to what the agent actually needs.
3. **Workflow awareness** -- 36 slash commands that chain skills into multi-step processes (plan generation, phase implementation, deep review, version bump, release notes, session history).

The catalog itself is content; the harness around it is the per-platform installer plus a small set of local MCP servers that surface the catalog to any agent that speaks MCP.

---

## Recommended Workflows

Nexus-Hub provides two opinionated end-to-end workflows. Use these as a starting point and adapt to your project.

### New Project Workflow (5 phases)

Build from scratch with an AI coding agent as your primary partner.

#### 1. Planning

Open an AI chatbot (Claude.ai or ChatGPT) and brainstorm: problem, users, core features, tech stack, constraints. End the session by asking the chatbot to produce a structured Markdown implementation plan -- phases with subtasks, each subtask carrying a self-contained prompt the agent can execute.

#### 2. Project setup

1. Create the Git repo with a three-tier branching model: `main` / `develop` / `feature/*`.
2. Install the Nexus-Hub toolkit -- paste the one-line install command for your OS (see [Quick Start](#quick-start-one-command)).
3. In Claude Code, run `/setup project` -- bootstraps `CLAUDE.md`, the directory structure, `.gitignore`, `README.md`, `DEVLOG.md`, and `CHANGELOG.md` in 8 guided phases.
4. Save the implementation plan from step 1 to `docs/<version>/plans/<slug>.md`.
5. Commit with `/commit`.

#### 3. Development (core loop)

For each plan phase:

1. Create a feature branch: `feature/phase-N-short-description`.
2. Open a fresh Claude Code session.
3. Run `/implement <slug> <phase>` -- walks every subtask, generates and runs tests, applies fixes, runs `/update gitignore` + `/update docs`, generates a session-history file, and produces a commit message.
4. Commit and push the feature branch.
5. Merge into `develop`. Repeat for the next phase.

Each `/implement` phase runs a best-effort model-routing pre-flight before building: it re-confirms the model and reasoning effort `/plan` recorded for the phase, re-assessing against the currently-available models so a plan built before a new release picks up the newer or cheaper option. It is platform-agnostic and never blocks (it degrades to the plan's recommendation when routing is unavailable). Run `/route` to route any task or phase on demand.

#### 4. Quality assurance (pre-release)

1. Run `/review full` -- a 12-phase orchestrator that chains known-gaps collection, health gates, dependency scan, docs / git hygiene, project validators, codebase description (`/describe full`), and the `security`, `pentest`, and full codebase-review scopes.
2. Read the synthesis report -- it produces a P0 / P1 / P2 / P3 ranked list of findings with a GO / GO-WITH-CONDITIONS / NO-GO verdict.
3. Address all P0 and P1 findings before release. P2 findings can be deferred to a follow-up patch release; P3 findings are advisory.
4. Run `/review sbom` for compliance documentation.

#### 5. Release

1. Run `/update release` -- orchestrates version detection, layout cleanup, `.gitignore` audit, version-bump across all configuration files, CHANGELOG migration, doc sync, and DEVLOG entry.
2. Merge `develop` into `main`, tag the release, and push.

### Inherited Project Workflow (2 phases)

For projects you have inherited or need to audit.

#### 1. Primary analysis and deep review

1. Clone the repo, open it in VS Code, start a Claude Code session.
2. Run `/review full` -- the same 12-phase orchestrator from Phase 4 of the New Project Workflow. The synthesis report's prioritized roadmap (P0 / P1 / P2 / P3) becomes your initial backlog.
3. If documentation is sparse, backfill it: `/update docs` (README, if missing), `/update changelog` (from git history), `/update devlog`, `/update refactor` (only when the repo has structural issues).
4. Establish the `develop` branch if not already present.
5. Commit the analysis artifacts.

#### 2. Making changes

For each change:

1. Brainstorm in a chatbot, then run `/plan` to produce a structured implementation plan saved to `docs/<version>/plans/<slug>.md`.
2. Run `/implement <slug> <phase>` per phase -- identical to the New Project Workflow's development loop.
3. (Optional) Use git worktrees for parallel work:

    ```bash
    git worktree add ../project-fix feature/security-fix
    # work in a separate Claude Code session, then:
    git worktree remove ../project-fix
    ```

4. After all changes land on `develop`, run `/review full` again to verify nothing regressed, then `/update release` and merge to `main`.

The QA and release steps are identical to the New Project Workflow.

---

## Manual setup (if you do not want to run the installer)

If you prefer to copy things yourself, here is how the repo is organized.

### Claude Code (Anthropic)

The most powerful integration -- adds **autonomous agent capabilities**.

- **CLAUDE.md**: the "brain". Copy `catalog/CLAUDE.md` to your project root and customize.
- **Skills**: the "hands". Copy folders from `catalog/skills/` to your project's `.claude/skills/` folder.

    *Example*: copy `catalog/skills/research/trend-research` to enable the trend-research skill.

### Gemini (Google) and Antigravity

Optimized instructions for Google's Gemini models, including the Antigravity workspace layout.

- **Gemini instructions**: copy `templates/ai-instructions/base-gemini.md` (or `templates/ai-instructions/generic-instructions.md` for the legacy template) to `.gemini/GEMINI.md` in your project or user profile.
- **Skills and workflows**: the installer mirrors these to `.gemini/skills/` and `.gemini/antigravity/global_workflows/` so they appear globally in Antigravity.

### GitHub Copilot (Microsoft)

Instructions for VS Code's Copilot Chat.

- Copy `templates/ai-instructions/coding-instructions/{language}.md` to `.github/copilot-instructions.md`.

### Codex (OpenAI)

OpenAI Codex CLI integration. Codex reads `AGENTS.md` at the project root (the open standard, also honored by Cursor / Aider / Jules) plus its user-level config in `~/.codex/`.

- **AGENTS.md**: copy `templates/ai-instructions/base-codex.md` content into your project's `AGENTS.md`.
- **Skills and prompts**: the installer mirrors `catalog/skills/` to `~/.codex/skills/` and `catalog/commands/` to `~/.codex/prompts/`. For manual setup, copy each tree to those destinations.

### Cursor

Cursor IDE integration.

- **Project rules**: copy `templates/ai-instructions/base-cursor.md` content into `.cursor/rules/nexus-hub.mdc` at your project root. Use `alwaysApply: true` in the frontmatter so Cursor applies the rule on every prompt.
- **Open-standard `AGENTS.md`**: Cursor also reads `AGENTS.md` at the project root, so the Codex setup above covers Cursor too.

### OpenCode

OpenCode IDE integration. OpenCode reads `AGENTS.md` per the open standard.

- Copy `templates/ai-instructions/base-opencode.md` content into your project's `AGENTS.md`.

---

## Development setup

For contributors working *on* Nexus-Hub (not consumers of the installer), the repo ships a [`.devcontainer/`](.devcontainer/) at the root. Open the repo in VS Code with the Dev Containers extension installed (or click "Reopen in Container" when prompted) and the post-create hook will install Python tooling (`pytest`, `ruff`), the GitHub CLI (`gh`), and the Claude Code CLI (`claude`). Authenticate `gh` and `claude` once the container is up, then run `make validate` to confirm the catalog is clean.

The devcontainer is opt-in -- the standard Quick Start above does not require it. It exists for first-touch contributor onboarding and for reproducing the maintainer's environment across machines.

---

## Featured Skills

| Skill | What it does |
|-------|--------------|
| **Architecture Design** | System decomposition, ADRs, C4 diagrams, and fitness functions. |
| **AI Agent Development** | Build agents with tool use, memory systems, and multi-agent orchestration. |
| **RAG Implementation** | End-to-end RAG pipelines with chunking, embeddings, and evaluation. |
| **API Design** | REST, GraphQL, and gRPC design with versioning and error handling. |
| **Code Review** | A 6-step deep dive (security, performance, logic) before you merge. |
| **Test Gen** | Writes comprehensive unit tests using AAA pattern and mocks. |
| **E2E Testing** | Playwright / Cypress automation with page objects and CI integration. |
| **Compliance** | Checks code against SOC2, GDPR, and ISO standards. |
| **Trend Research** | Researches Reddit / X for the last 30 days to find trends and write prompts. |

The full catalog is at [data/SKILL_INDEX.md](data/SKILL_INDEX.md). Per-category landing pages live under [catalog/skills/](catalog/skills/).

---

## Usage Monitoring

Three complementary ways to track your AI coding usage limits.

### CLI Usage Display (Automatic)

A Stop hook that shows your usage limits directly in the terminal after each Claude Code response. Color-coded and silent when usage is healthy (below 50%).

```
Usage: Session 72% | Weekly 15% | Sonnet 3%  (Session resets in 28m)
```

Installed automatically by the Nexus-Hub installer. Requires `curl` and `jq`.

### VS Code and Cursor Extensions

Monitor your AI coding usage from the editor status bar with a full dashboard. Four separate, independently-installable extensions - one per tool - that install and run side by side:

- **Claude Usage Monitor** (`nexus-hub.claude-usage-monitor`): Claude Code (Anthropic) session and weekly limits, with model and effort recommendations. See [extensions/claude-usage-monitor/](extensions/claude-usage-monitor/).
- **Codex Usage Monitor** (`nexus-hub.codex-usage-monitor`): Codex (ChatGPT / OpenAI) usage, with the plan tier, extra rate-limit windows, a credits line, and throttle / pacing recommendations (periwinkle `#5244BB` progress bars). See [extensions/codex-usage-monitor/](extensions/codex-usage-monitor/).
- **GitHub Billing Usage** (`nexus-hub.github-usage-monitor`): GitHub Actions minutes and storage plus current-month Copilot billing, read from documented GitHub billing APIs for the one billing owner you configure (teal `#008080` progress bars). Renamed from "GitHub Usage Monitor" in v3.15.12 because the old name read as Copilot-only; the extension id is deliberately unchanged so an existing install updates in place rather than being orphaned. See [extensions/github-usage-monitor/](extensions/github-usage-monitor/).
- **Cursor Usage Monitor** (`nexus-hub.cursor-usage-monitor`): personal Cursor Models and Other Models included-usage meters with on-demand spend context (steel-blue `#4682B4` progress bars), for the Cursor IDE only. This release ships with live fetch disabled entirely - cached or manually-entered dashboard values drive the UI until a bounded, authorized session-reuse probe verifies a safe live path. See [extensions/cursor-usage-monitor/](extensions/cursor-usage-monitor/).

Each shows usage in the status bar with a theme-aware hover and a full dashboard, and makes at most a single outbound call only to your own account. The Claude and Codex monitors read your local OAuth token; the GitHub monitor uses a fine-grained token you supply explicitly, stored only in VS Code SecretStorage, and shows absolute usage rather than inventing a percentage when GitHub exposes no allowance. None of them scrape a billing website or read browser cookies. The installer isolates extensions by editor host: the Claude, Codex, and GitHub monitors install only through the VS Code CLI, and the Cursor monitor installs only through the Cursor CLI - never cross-installed. Install any one alone by pointing `code --install-extension` (or `cursor --install-extension`) at its VSIX.

### `/usage` Command

On-demand detailed usage report with model-switching recommendations. Auto-fetches from the API (falls back to manual entry if credentials are unavailable).

---

## Safety and Use in Regulated Industries

Nexus-Hub is built on a **reverse-engineering-first** principle: the catalog ships zero third-party data processors, zero outbound calls from skills / commands / hooks, and zero telemetry. The full threat-model breakdown, industry compatibility matrix, and reporting policy is in [SECURITY.md](SECURITY.md).

Short version:

- **Open-source / hobby / internal commercial software**: green. No restrictions.
- **Regulated industries (healthcare, finance, government, life sciences, automotive, industrial)**: green WITH caveats. Nexus-Hub itself is safe; the caveat is that your chosen LLM provider is where prompts go (use a regulated-cloud option like AWS Bedrock, GCP Vertex AI, Azure OpenAI, or a self-hosted model consistent with your data-protection obligations).
- **Defense / classified / air-gapped**: outside Nexus-Hub's threat model. Do your own assessment.

What Nexus-Hub does NOT do: telemetry, analytics, phone-home, third-party data processors, model downloads, API-key requirements. The MCP Registry Policy in [AGENTS.md](AGENTS.md) categorically rejects search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service. The authoritative classification of every MCP server ever shipped or considered is at [docs/policy/mcp-reverse-engineering-matrix.md](docs/policy/mcp-reverse-engineering-matrix.md).

What is OUT of Nexus-Hub's control: your chosen LLM provider, any MCP server you add outside the Nexus-Hub registry, user-initiated outbound calls (`gh`, `git push`, `curl`), and your own user-authored hooks and rules. See [SECURITY.md](SECURITY.md) section 3 for the full caveats.

To report a security issue: email [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com) or open a private security advisory at [github.com/bendourthe/Nexus-Hub/security](https://github.com/bendourthe/Nexus-Hub/security).

---

## Roadmap

Nexus-Hub evolves in versioned slices. Each upcoming line item below traces to a concrete plan file under `docs/<version>/plans/` (the durable source) and resolves once its `[<version>]` block lands in [CHANGELOG.md](CHANGELOG.md). No star gates, no sponsor tiers, no paid features -- the catalog is reverse-engineering-first and stays that way.

| Focus | Target | Status | Source |
|-------|--------|--------|--------|
| Rename DevAI-Hub to Nexus-Hub, modernize installer with ASCII banner, integrate Nexus brand linkage | v2.0.0 | In progress | [docs/archive/v2/v2.0/plans/nexus-hub-rename.md](docs/archive/v2/v2.0/plans/nexus-hub-rename.md) |
| Cross-OS CI matrix for installer smoke tests (closes the cumulative DF-003 / DF-005 / DF-006 / DF-007 / DF-008 cluster from v1.1.5 known-gaps) | v2.1.0 | Planned | [docs/archive/v1/v1.1/](docs/archive/v1/v1.1/) known-gaps cluster |
| Skill-eval-loop integration into pre-commit (assertion-graded regression guard for high-traffic skills before they ship) | v2.1.0 | Planned | [catalog/skills/workflow/skill-eval-loop/SKILL.md](catalog/skills/workflow/skill-eval-loop/SKILL.md) |
| MCP registry expansion under the existing 5-step policy (reverse-engineer-first; hard-no on search / embeddings / scraping / generation as a service) | continuous | In progress | [docs/policy/mcp-reverse-engineering-matrix.md](docs/policy/mcp-reverse-engineering-matrix.md) |

For narrative-style updates on what changed and why, see [docs/DEVLOG.md](docs/DEVLOG.md). For the formal Keep-a-Changelog log of every release, see [CHANGELOG.md](CHANGELOG.md). For the per-version unfinished-work tracker that the next plan reads to decide what carries forward, see `docs/<version>/known-gaps.md`.

---

## Collaboration

Nexus-Hub is a curated open-source project. While pull requests are typically not accepted from outside contributors, suggestions, feedback, and recommendations are more than welcomed. If you have a better prompt, a smarter rule, or a pattern you would like to see in the catalog, please reach out directly:

- **Email**: [benjamin.dourthe@gmail.com](mailto:benjamin.dourthe@gmail.com)
- **GitHub**: [@bendourthe](https://github.com/bendourthe)

I am happy to discuss skill / command / hook proposals, integration ideas for new platforms, or specific use cases -- especially when the proposal aligns with the policy direction of this project (reverse-engineering-first, no third-party data leaks).

---

## License

See [LICENSE](LICENSE).
