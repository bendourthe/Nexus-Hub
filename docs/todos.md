# Nexus-Hub Progress Dashboard

**Integration branch:** `develop`
**Active work:** The v4.10.1 and v4.11.1 plan closures are integrated through PR #232; the late v4.10 history archive merged through PR #234. Cross-version CI report retention merged through PR #235, the v4.0 gap guards and v4.11 SVG routing correction merged through PR #236, the v4.8 development prerequisite and v4.13 trigger-audit follow-ups merged through PR #237, the CI tool locks merged through PR #238, the pinned v4.13 tool-span contract merged through PR #239, the v4.3 ownership-guard repair merged through PR #240, the CI profile/cache/report follow-up merged through PR #241, the v4.2 Unicode validator repair merged through PR #242, the coverage/SARIF report producers merged through PR #243, and the attribution push-destination repair merged through PR #244, all with green hosted and post-merge checks. The interrupted v4.2 local report archive is green in PR #245. Unprotected GitHub branches and bounded vendor or manual evidence remain open in their known-gaps ledgers. The v4.0 CI plan's 62 unticked historical task boxes require task-level reconciliation before they can be counted as verified completion.
**Last refreshed:** 2026-09-22

This dashboard tracks the work in flight right now. It is deliberately short. Finished versions are not listed here: each one's outcome lives in its own `docs/releases/v*/v*.*/known-gaps.md`, and what shipped lives in [`CHANGELOG.md`](../CHANGELOG.md). Sequencing beyond the active plan lives in [`docs/roadmap-prioritization.md`](roadmap-prioritization.md).

Refreshing this file to the active plan (rather than appending another version's section) keeps the dashboard from drifting to an old feature branch.

- [x] Historical v4.0-v4.13 plan closure is integrated. PR #232 passed the required Linux, Windows, guide-render, host-load, CodeQL, and aggregate checks; post-merge run 35789442554 passed smoke and provenance without rerunning the full suite.
- [x] Published and verified cross-version CI report retention through PR #235: seven jobs upload seven-day bundles, direct guide and Windows native tests emit JUnit, and five report artifacts were visible in hosted run 35799198474. The post-merge smoke and provenance run 35801251735 passed.
- [x] Published and verified the v4.0-v4.13 gap guards and SVG chart correction through PR #236; all hosted checks and post-merge smoke/provenance passed at `3c90d688`.
- [x] Close v4.8 WN-C locally: `make dev` installs all six extension development extras, the README supplies the direct Windows command, pip resolves it in dry-run mode, and the 16-check native fast profile passes.
- [x] Publish and verify the v4.8 WN-C follow-up on merged `develop` through PR #237 and post-merge run 35808379460.
- [x] Mitigate v4.13 WN-5 for future trigger pilots: persist bounded `Skill` selector evidence in normal and timeout rows without retaining prompt payloads; the original 96 calls remain unauditable.
- [x] Close v4.9 MT-2 with named cross-host proof: the nine Windows-skipped filesystem cases all passed on Ubuntu WSL, and the Windows run passed its applicable 90 cases.
- [x] Qualify the v4.12 WN-2 tool-lock candidate locally: a universal all-extras Python lock, pinned npm/apt/Docker inputs, 95 workflow/security checks, constrained pip resolution, and 54 plus 380 no-network Docker passes.
- [x] Publish the tool-lock branch and verify hosted and post-merge results before closing v4.12 WN-2: PR #238 passed the final hosted head and post-merge run 35810094225.
- [x] Verify the v4.13 WN-2 tool-span attributes against the same pinned sibling specification and exercise the trace example: 184 passed, two host skips, docs 8/8, fast 17/17.
- [x] Publish and verify the v4.13 WN-2 span-contract follow-up: PR #239 passed all hosted checks and post-merge run 35813788600.
- [x] Qualify the v4.3 DF-5 ownership-guard repair locally: 668 adapter and installer tests passed, fast 17/17 passed, and a real CLI dry-run refused a linked `.copilot` root with zero external writes.
- [x] Publish and verify the v4.3 DF-5 ownership-guard repair: PR #240 passed all hosted checks and post-merge run 35817524653.
- [x] Qualify the v4.3 CI follow-up locally: general inline validators moved into profiles, guide and Windows pip caches keyed to scoped manifests, and the report profile plus aggregate job passed 256 CI/workflow tests with 17 skips, fast 17/17, and docs 8/8.
- [x] Publish the v4.3 CI follow-up through PR #241: all hosted jobs passed, guide caches had warm key hits, the seven-day aggregate artifact contained five source receipts, and post-merge run 35820761181 passed.
- [x] Observe a warm Windows pip cache hit on PR #242 and close v4.3 DF-1/DF-2 after the hosted profile and cache checks passed.
- [x] Publish the v4.2 Unicode validator gap repair through PR #242; all hosted checks and post-merge run 35822538895 passed.
- [x] Produce local CI-engine coverage XML and catalog-scanner SARIF from the existing profile commands; 107 CI tests passed, the scoped coverage report recorded an 0.8832 line rate, and the scanner emitted 48 below-threshold findings in SARIF 2.1.0.
- [x] Publish and inspect both real report types in PR #243's seven-day hosted aggregate; the replacement run passed 30 checks with one intentional skip, and post-merge run 35826047174 passed.
- [x] Merge PR #244 after its refreshed run passed all 18 jobs; post-merge run 35828234631 passed smoke and provenance.
- [ ] Reconcile the v4.12 BG-2 ledger against PR #244 and its post-merge proof.
- [ ] Merge PR #245 and preserve its interrupted full-profile report before clearing the unregistered Unicode folder; the separate cache-only folder cannot be removed under current tool policy.
- [x] Close v4.4 WN-446-1 against PR #235's hosted `ci-guide-render-report` and seven-day expiry; the rejected v4.4.6 guide remains superseded.

---

## Portable attribution extension

Local feature implementation and qualification are complete: all 47 Linux full-profile commands and 15 Windows fast-profile commands pass, with real Windows and Linux installer verification. Normal integration passed through PR #217 and post-merge run 34925451808; v4.12.0 is published and its downloaded artifacts are verified, recorded in the [portable evidence](archives/v4/v4.12/development/portable-attribution-evidence.md). The public Code contributor display remains open independently.

- [x] Implemented approved v4.12 Phase 5: installable Git attribution guard, both installers, all platform instructions, installed-behavior verification and release preparation. See [the active plan](archives/v4/v4.12/plans/v4.12.0-sole-contributor-attribution.md).

## Scores

| Metric | Current | Target | Delta |
|--------|---------|--------|-------|
| v4.12.0 implementation tasks complete | 27 | 28 | 1 |
| v4.12.0 implementation phases complete | 4 | 5 | 1 |
| v4.11.0 interactive-handbook phases complete | 7 | 7 | 0 |
| v4.11.0 interactive-handbook tasks complete | 31 | 31 | 0 |
| v4.11.0 accepted native authoring families | 2 | 3 | 1 |
| v4.10.0 implementation tasks complete | 26 | 26 | 0 |
| v4.10.1 implementation tasks complete | 34 | 34 | 0 |
| v4.11.1 comparison and plan prepared | 2 | 2 | 0 |
| v4.11.1 implementation tasks complete | 25 | 25 | 0 |
| v4.13.0 comparison and plan prepared | 2 | 2 | 0 |
| v4.17.3 harness-economics comparison and plan prepared | 2 | 2 | 0 |
| v4.13.0 implementation tasks complete | 34 | 34 | 0 |
| v4.4.5 baseline guide/test files restored | 59 | 59 | 0 |
| Exact production-file restorations | 3 | 3 | 0 |
| v4.4.1 guide-visual-and-arcade-rebuild phases complete | 7 | 7 | 0 |
| v4.4.2 guide-production-ready-rebuild phases complete | 8 | 8 | 0 |
| v4.4.2 local phase commits | 8 | 8 | 0 |
| Prior v4.4.2 release blockers (historical) | 0 | 0 | 0 |
| Restored views with page errors or horizontal overflow | 0 | 0 | 0 |
| Catalog skills | 337 | 337 | 0 |
| Canonical guide bytes (strict ceiling 500,000) | 497,896 | < 500,000 | met |
| Platform marks approved with staged hashes | 5 | 5 | 0 |

---

## Current closure - v4.10.1 eval isolation and adaptive compaction

- [x] Published and integrated the completed [v4.10.1 adoption plan](releases/v4/v4.10/plans/v4.10.1-adoption-eval-isolation-and-adaptive-compaction.md) through PR #232, merged to `develop` at `c54dbeb4`. T034 is complete; no retroactive v4.10.1 tag is planned.
- [x] Archive the late Phase 7 history in `docs/archives/v4/v4.10/development/history/` and repair the retention check that missed source files when the destination already existed; 19 focused tests and the link baseline pass.

## Current closure - v4.11.1 cache accounting and diagram quality

- [x] Published and integrated the completed [v4.11.1 adoption plan](releases/v4/v4.11/plans/v4.11.1-adoption-cache-and-diagram-quality.md), seeded by the [completed comparison](releases/v4/v4.11/comparisons/v4.11.1-comparison-cache-and-diagram-quality.md), through PR #232 at `c54dbeb4`. T025 is complete. `MT-10` remains open for authored connector diagrams that use `<path>`; one real bar-chart SVG is now decidable, while the distribution handbook's five path SVGs are icons, not diagrams.

## Current closure - v4.0 inherited gaps

- [x] Locally close agent-communication DF-1 and MT-3 with the 13-template release gate and an actual Python 3.11 grammar check; 127 focused tests and the 17-command native fast profile pass.
- [x] Reconcile BG-6 with the v3.18 withdrawal decision: the deleted drawdown ledger stays deleted by design, and the superseded decision record now gives the exact Git-history recovery command instead of dead links.
- [x] Close v4.0 BG-2 locally: explicit global targets now isolate platform writers, defaults, Copilot, OpenClaw, and organization-knowledge lookup; host cleanup is skipped for redirected installs. A fake-home sentinel regression, 146 affected-suite passes, and the 17-check native fast profile verify the change.
- [ ] Publish the v4.0 gap-guard branch after the CI-report branch is integrated and verify its hosted result. MT-1 remains a bounded prose-compliance limitation.
- [x] Repair the SVG routing false positive found on a real worked-example bar chart: earlier gridlines hidden by later opaque bars are not visible connector crossings. The 94-test visual-QA module passes, and both geometry checks now decide that chart without a high-severity finding.
- [x] Bind v4.9 QG-1 to PR #190's final green Windows, Linux, and aggregate checks; leave MT-2's per-case platform skip question open.

## Queued work - v4.17.3 harness economics and portable engineering systems

- [ ] Implement the approved [v4.17.3 adoption plan](releases/v4/v4.17/plans/v4.17.3-adoption-harness-economics-and-portable-engineering-system.md), seeded by the [completed comparison](releases/v4/v4.17/comparisons/v4.17.3-comparison-harness-economics-and-portable-engineering-system.md). The queued plan defines five phases and 52 tasks for explicit unattended-loop outcomes, a serial repository-local harness evaluator with enforceable live-run gates, and provider-aware shared project instructions with one platform-neutral `base-agents.md` owner. Implementation is 0/5 phases and 0/52 tasks.

## Current work - v4.4.5 visual refinement

- [x] Compact all Models demos, enrich the animated networks, add perspective room navigation and a new game redesign, sweep provider-labeled capability tiers, and compare four reasoning allowances simultaneously; 154 focused guide checks, 24 final Models tests and 40 layout cases pass, with one optional portfolio check skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-compact-comparisons/verification.md).

- [x] Refine Models with training icons and reinforcement learning, a simpler language response, faster photographic diffusion, consistent room framing, voice-plus-UI multimodal input and four distinct architecture illustrations; 153 focused tests and 40 layout cases pass, with one optional portfolio check skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-photographic-examples/verification.md).

- [x] Refine Models with a common prompt/network/output flow, continuous token prediction, furnished-room camera sequence, native multimodal example, provider-labeled capability graphics and reasoning loops; 152 affected checks and 40 layout cases pass after the final source-label retest. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-flow-refinement/verification.md).

- [x] Rebuild Models with four visual demonstrations, capability/effort controls, and finite accessible animations; 150 affected tests pass with one optional skip, 20 final Models tests pass, and 40 layout cases pass. The default section is 29% shorter with 45% fewer visible words. See [verification](releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/verification.md).

- [x] Move the concise shared-plan explanation into the center handoff callout and remove the bottom repetition; 34 focused tests and 12 layout/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/centered-handoff-explanation/verification.md).

- [x] Rename the example plan, emphasize Example:, and add a prominent handoff callout with a fixed centered clock; 34 focused tests and 12 responsive/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/handoff-callout/verification.md).

- [x] Add the phase/model/effort plan table and show the same Phase 1 checklist from interruption through Codex completion; 52 focused checks plus the updated word-budget rerun and 12 layout/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/phase-one-handoff/verification.md).

- [x] Replace the Model network with a colored clustered illustration and show six guardrail pills; 59 focused tests and 12 responsive/theme checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/clustered-model-and-guardrails/verification.md).

- [x] Restore the exact v4.4.5 guide, Training data, README, and related tests.
- [x] Verify baseline file parity and inspect restored desktop/mobile pages.
- [x] Complete the guide-specific regression suite: 340 passed, one optional skip; four inherited warnings.
- [x] Refine the token illustration and harness animation while preserving all 27 sections and 1,150 text fragments.
- [x] Stop idle Training frame scheduling: Foundations samples fell from 61 callbacks per second to zero.
- [x] Verify both themes and responsive layouts; complete the guide suite: 342 passed, one optional skip.
- [x] Rebuild the screenshot-selected Home safety and platform diagrams, enlarge their text, and keep all original content.
- [x] Verify the Home refinements across nine widths and both themes; all 49 final focused regression checks pass. See [evidence](releases/v4/v4.4/development/guide-visual-refinement/screenshot-segments/plan.md).

- [x] Align the safety figure, center the platform source text, remove connector dots, and repair line joins; 45 focused tests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/alignment-correction/verification.md).

- [x] Match all Foundations section headings to Home and align the token and context box pairs; 59 affected tests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/foundations-alignment/verification.md).

- [x] Remove the Home and Foundations Next sections and replace the safety shield with the transparent floating Nexus Hub logo; 56 focused tests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/logo-and-page-endings/verification.md).

- [x] Standardize prompt labels, merge selected attachments into the context prompt, and match the Best Practices heading; 143 tests pass and one is skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/prompt-composer/verification.md).

- [x] Illustrate the Claude Code usage-limit interruption and Codex continuation of the same Nexus Hub plan; 40 verification checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/session-handoff/verification.md).

- [x] Add the checkout repair example with image/PDF attachment previews and an expandable asset-folder explorer; 36 preview checks, 128 focused tests, and 32 final retests pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/context-previews/verification.md).

- [x] Make the Home guardrails and platform handoff accessible to non-developers with platform logos, plain-language safety examples, and an appointment-booking plan; 169 focused tests and 28 layout checks pass, with one test skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/accessible-home-examples/verification.md).

- [x] Move checkout attachments above the prompt, render the image as PNG, add matching Request/Attachments/Goal/Context highlights, and rename Query to Request; 144 focused tests, 12 layout/color cases, and 36 keyboard preview checks pass, with one test skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/prompt-categories/verification.md).

- [x] Widen the safety Model box, add a neural-network illustration, and shorten guardrails into highlighted pills; 59 focused tests and 12 layout checks pass. See [verification](releases/v4/v4.4/development/guide-visual-refinement/model-and-guardrail-pills/verification.md).

- [x] Keep prompt text plain until its matching box activates, slow both annotation sequences, and compact attachment thumbnails beside their labels; 145 focused tests, 12 layout checks, four timing cases, and 36 preview interactions pass, with one test skipped. See [verification](releases/v4/v4.4/development/guide-visual-refinement/prompt-animation-and-attachments/verification.md).

- [x] Fix the pre-existing two-pixel internal overflow in Agentic Platforms at 320 pixels. The current guide passes `test_all_pages_meet_contrast_and_overflow_matrix`; retain the [original baseline evidence](releases/v4/v4.4/development/guide-visual-refinement/context-previews/baseline-overflow.json).

- [x] Improve the pre-existing Home guardrail pill contrast in light mode. The current guide passes `test_all_pages_meet_contrast_and_overflow_matrix`; retain the [original 4.462:1 baseline evidence](releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/baseline-sweep.json).

- [x] Reconcile five pre-existing guide assertions for the approved prompt labels/highlights, Home session dialogue, and the cx-png marker. The current focused guide set passes 126 tests with one expected optional skip; retain the [original failure record](releases/v4/v4.4/development/guide-visual-refinement/models-rebuild/verification.md).

## Plan - v4.4.6 Guide Learning Experience [SUPERSEDED BY USER]

- [x] Review current Home, Foundations, Training, and the two supplied source documents; retain current browser evidence.
- [x] Write the seven-phase implementation plan with continuous visual and performance gates.
- [x] Phase 1 - Baseline and teaching/design contract.
- [x] Phase 2 - Shared layout and motion repair.
- [x] Phase 3 - Home refinement.
- [x] Phase 4 - Foundations: model, tokens, prompt, context.
- [x] Phase 5 - Foundations: harness, loop, graph.
- [x] Phase 6 - Training clarity and state integrity.
- [ ] Phase 7 - Final verification, known gaps, CI/CD, and approval-gated integration.

Historical implementation record only: the user rejected this content/structure rewrite. v4.4.5 has been restored, and the plan above must not resume. Prior test and performance results describe the rejected artifact, not the restored guide.

---

## Plan - v4.4.1 Guide Visual and Arcade Rebuild [MERGED TO DEVELOP 2026-09-02, PR #154; superseded by final v4.4.5 guide state]

- [x] Phase 1 - Contracts, asset provenance, and byte budget
- [x] Phase 2 - Home identity, platform rail, and workflow loop
- [x] Phase 3 - Foundations structure, Tokens, Prompt, and Context
- [x] Phase 4 - Foundations Models, Agentic Platform, comparison, and harnesses
- [x] Phase 5 - Deterministic arcade-shooter engine
- [x] Phase 6 - Training workspace, fullscreen, and integrated loop
- [x] Phase 7 - Architecture refactor, known-gaps, CI/CD, publication, and integration (local duties and integration complete)

## Plan - v4.4.2 Guide Production-Ready Rebuild [MERGED TO DEVELOP 2026-09-02, PR #156; superseded by final v4.4.5 guide state]

Plan: [v4.4.2-guide-production-ready-rebuild.md](releases/v4/v4.4/plans/v4.4.2-guide-production-ready-rebuild.md). Branch cut from `develop` at `46f18986` on 2026-09-02.

- [x] Phase 1 - Contracts, motion system, scale tokens, and rename
- [x] Phase 2 - Home hero and restored sections
- [x] Phase 3 - Foundations title system, layout balance, and annotated prompts
- [x] Phase 4 - Foundations Models, Agentic Platform, and the layered harness animation
- [x] Phase 5 - Arena engine v2
- [x] Phase 6 - Training fullscreen three-pane presentation
- [x] Phase 7 - Integrated verification and documentation
- [x] Phase 8 - Architecture refactor, known-gaps, CI/CD, and publication (local duties, PR, and integration complete)

### What this plan changes, in one paragraph

A corrective visual and teaching pass over the shipped v4.4.0 guide. Home gains a floating Nexus Hub lockup, five integrated platform marks, and readable two-line command pills. Foundations is compacted and reordered into eight professionally titled concepts, with Models and Agentic Platform sharing one visual grammar. Training replaces the Asteroids scenario with a deterministic arcade shooter carrying a seeded lives bug, a falling-asteroid hazard, and a vertical-movement feature, and stays readable in and out of fullscreen.

### Prerequisite status

Met. v4.4.0 is released: integration PR #150 merged at `46518d01`, release PR #151 merged at `39f73a7e`, release PR #152 merged to `main` at `5c4b1346`, tag `v4.4.0` pushed with its GitHub Release published, and the artifact round-trip verified PASS over 1835 files. Back-merge PR #153 merged, and this branch was cut from a refreshed `develop` (`316aba97`) that contains the release merge.

### Earlier checkpoint (retained; superseded by the v4.4.5 local closeout)

Phase 5 complete. `window.NexusShooter` replaces the Asteroids engine: a mulberry32-seeded fixed-step portrait shooter (360x480, 1/60s tick) whose deep-frozen snapshots deep-equal across runs with one seed, with terminal `destroyed` semantics, composable pause reasons, a Click-to-start idle gate, procedural layered art, an authoritative HUD with a change-only live region, and full keyboard, touch, reduced-motion, and no-canvas paths. The seeded bug is now first-enemy-hit-destroys; `/implement` fixes damage to walk lives 3 -> 2 -> 1 -> 0 and `/compare` enables band-clamped vertical movement. Both scene-data copies migrated to the three-field game schema (prose stays v4.4.0 until Phase 6). New 29-test engine suite replaces the 1,094-line Asteroids suite; full guide suite 190 passed, 1 skipped; detector clean on Training both themes. Guide at 284,278 bytes. Three engine defects found and fixed during stabilization (boot-order crash, a fixture that could not demonstrate fixed damage, and reset creating an unstartable game). Next: Phase 6 writes the shooter teaching narrative and the integrated Training workspace.

---

## Maintaining this file

One rule: this dashboard describes the current branch and the active plan. When a plan ships, replace its section rather than appending the next one. History belongs in the per-version known-gaps files and the changelog, both of which are already authoritative and neither of which this file should duplicate. See the `dev-progress-tracker` skill.

## Approved interactive authoring follow-up

Historical command/skill draft: 3/3 local items were completed, then reconciled as candidates into the authoritative [v4.11.0 master plan](releases/v4/v4.11/plans/v4.11.0-interactive-handbooks-and-presentation-default.md). The draft branch is no longer an active implementation owner; the released master plan and its known-gaps ledger govern current status.

- [x] Reconcile the scoped authoring-contract candidates into the master interactive-handbooks plan; v4.11.0 completed 7/7 phases and 31/31 tasks through PR #202.
- [x] Complete the reusable runtime, assembler, and cross-project qualification plan after its move from v4.9 to v4.11.0; the released plan records its bounded qualification limits in the v4.11 known-gaps ledger.
