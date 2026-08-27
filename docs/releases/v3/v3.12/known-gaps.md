# Known Gaps - v3.12

**Project**: Nexus-Hub
**Status**: release-ready (pending `/update release` commit / merge / tag / push)
**v3.12.1 note**: the cross-platform-install-adapters patch appends its `## v3.12.1` gaps below; the `## v3.12.0` presentify sections are retained unchanged.
**Last updated**: 2026-07-11 (Phase 6 final reconciliation: WN-2 and MT-1 resolved this phase; DF-v39-presentify-1/-2/-3 marked resolved in the v3.9 ledger; DF-v39-presentify-4/-5 carried in as DF-4/DF-5)

## v3.12.0

### Summary

| Category | Open | Resolved |
|---|---|---|
| Not implemented (NI) | 0 | 0 |
| Deferred (DF) | 5 | 0 |
| Bugs / regressions (BG) | 0 | 0 |
| Warnings (WN) | 1 | 2 |
| Missing tests / coverage gaps (MT) | 0 | 1 |
| Quality-gate gaps (QG) | 0 | 0 |

### Open Items

#### Deferred

##### DF-1 - PDF text/figure interleaving is approximate

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: `docs/v3/v3.12/plans/v3.12.0-presentify-fidelity-and-variety.md` sub-task 1.2
- **Reason**: Within a PDF page section, extracted figure images are placed after the page's text and tables (ordered among themselves by vertical position) rather than interleaved at their exact in-flow position; true interleaving would require full layout reflow, which is out of scope. Documented as a runbook gotcha.
- **Suggested next step**: The `page` + `caption` metadata is sufficient for the authoring stage to place figures sensibly (proven in the Phase 5 worked example); revisit only if authoring proves to need exact in-flow positions.

##### DF-2 - Caption text remains duplicated in page paragraph text

- **Source phase**: Phase 1 (1.2)
- **Plan reference**: sub-task 1.2 (caption pairing)
- **Reason**: A detected caption is ATTACHED to its figure block, not moved: the same line also remains inside the page's paragraph text. Removing it from the text flow risks dropping content on false-positive matches, so the extractor keeps both. Documented as a runbook gotcha.
- **Suggested next step**: The authoring stage should prefer the block `caption` and drop the duplicate line; consider extractor-side dedup once caption matching has real-world mileage.

##### DF-3 - OCR table recovery is geometry-based; pytesseract path recovers paragraphs only

- **Source phase**: Phase 1 (1.5)
- **Plan reference**: sub-task 1.5 (two-tier OCR path)
- **Reason**: Tier-A table reconstruction clusters OCR boxes into aligned multi-cell rows, which works on well-separated columns (fixture-verified) but not on dense or borderless tables; the `pytesseract` fallback emits paragraphs only. The tier-B scanned-page image plus the figure-reconstruction protocol's transcription/verification pass are the accuracy backstop in all cases.
- **Suggested next step**: Revisit only if real scans show tier-A table recovery failing where it matters; the mandatory numeric verification already guards correctness.

##### DF-4 - Video / audio media embedding (carried from v3.9, DF-v39-presentify-4)

- **Source phase**: v3.9 presentify-interactive-html Phase 1; re-affirmed by v3.12 Phase 6
- **Plan reference**: v3.12 plan Phase 6 (6.2)
- **Reason**: Media in any source format is ignored: the output is a single self-contained offline HTML file, and embedded media would break the offline / size guarantee.
- **Suggested next step**: Revisit only if embedded media becomes a stated requirement; would need a size + offline strategy.

##### DF-5 - Brand custom-font embedding in the baseline builder (carried from v3.9, DF-v39-presentify-5)

- **Source phase**: v3.9 presentify-interactive-html Phase 2; re-affirmed by v3.12 Phase 6
- **Plan reference**: v3.12 plan Phase 6 (6.2)
- **Reason**: A theme / brand override supplies CSS font stacks; a non-system custom font would need an opt-in base64 `@font-face` embed to stay self-contained. System stacks and brand palettes are fully supported.
- **Suggested next step**: Add the opt-in base64 `@font-face` embed path (read the font file from the brand `assets_dir`, inline it) if a brand custom font becomes a requirement.

#### Warnings

##### WN-1 - Pre-existing local test failures on the Windows dev host (unrelated to this version)

- **Source phase**: Phase 1 (1.6 validation)
- **Plan reference**: sub-task 1.6
- **Reason**: The full pytest sweep shows failures that reproduce identically on a clean HEAD with this version's changes stashed: 99 bash-invoking hook tests and 4 installer/branch-flag repo tests (`bash -n` fails with empty stderr on this host - the WN-v33/WN-v36 environment family), plus two pre-existing local failures in untouched domains (`nexus-context-compressor::test_small_input_never_expands_under_store`, `validators::test_discover_obsidian_vault_marker`). All suites touching this version's surface are green.
- **Suggested next step**: CI (ubuntu/macOS) remains the authoritative gate for the bash suites; confirm green on the release run. The two non-bash local failures predate this version and should be triaged in their own domains.

### Resolved

##### WN-2 - build_presentation.py `ruff format` debt (RESOLVED in Phase 6)

- **Source phase**: Phase 1 (1.6 lint); resolved by Phase 6 (6.1)
- **Resolution**: The builder was ruff-format-normalized in the Phase 6 refactor pass; behavior-neutrality proven by re-running the 45-check extraction-fidelity suite (which builds v1 and v2 models through the reformatted builder) - all green.

##### WN-3 - Interaction-budget demo verified by static structural review only (RESOLVED in Phase 5)

- **Source phase**: Phase 3 (3.3); resolved by Phase 5 (5.2)
- **Resolution**: Headless Edge (present on the Windows host) rendered the worked example's runs at desktop and mobile widths (`docs/v3/v3.12/development/worked-example/*.png`); the visual-QA pass read the screenshots back (one defect found and fixed: a dangling caption dash on caption-less figures). The rendered-pass checkpoint this warning deferred to Phase 5 has been exercised.

##### MT-1 - No CI coverage for the extractor's fixture suites (RESOLVED in Phase 6)

- **Source phase**: Phase 1 (1.6); resolved by Phase 6 (6.3)
- **Resolution**: New path-filtered workflow `.github/workflows/presentify-extractor.yml` (ubuntu-only, pip-cached, concurrency-cancelled) runs ruff + `gen_fixtures.py` + the 45-check `verify_phase1.py` + the `enrich_models.py` round-trip + the 10-check `verify_design_seed.py` whenever the skill's bundled scripts or the suite itself change. The scanned-fixture generator gained a cross-platform font resolver (Arial on Windows, DejaVu on Ubuntu CI) so the OCR checks hold on the runner. The budget-demo and worked-example verifiers stay manual by design: they verify committed authored evidence, not the parsing surface.

### Resolved from prior versions

- **DF-v39-presentify-1** (scanned-PDF OCR), **DF-v39-presentify-2** (PDF image extraction), and **DF-v39-presentify-3** (native chart objects) are RESOLVED by this version's Phases 1-5; the v3.9 ledger rows are annotated with pointers back here.

## v3.12.1

Cross-platform install adapters + per-release format verification (the cross-platform-install-adapters patch). Fixes that Nexus-Hub skills/commands were not discoverable in the new ChatGPT desktop app (Codex) or the Antigravity IDE, and adds a three-layer verification gate. Plan: `docs/v3/v3.12/plans/v3.12.1-cross-platform-install-adapters.md`.

### Summary

| Category | Open | Resolved |
|---|---|---|
| NI | 0 | 0 |
| DF | 6 | 0 |
| BG | 0 | 0 |
| MT | 0 | 0 |
| WN | 1 | 0 |
| QG | 0 | 0 |

### Open Items (Deferred)

| ID | Source | Reason | Severity |
|---|---|---|---|
| DF-v3121-codex-skills-alias | Phase 2 (Codex) | The new ChatGPT desktop app reads skills, but docs do not state whether it prefers `~/.codex/skills` or the cross-tool `~/.agents/skills`; we write BOTH (additive), so discovery works either way. Confirm the canonical root on a live desktop-app install. | Low |
| DF-v3121-agy-cli-workflows | Phase 3 (Antigravity) | The `agy` CLI global SKILLS path is confirmed (`~/.gemini/antigravity-cli/skills/`); the CLI global WORKFLOW dir is undocumented and written best-effort. IDE global slash works via `~/.gemini/config/global_workflows/`. | Low |
| DF-v3121-antigravity-global-hooks | Phase 3 (Antigravity) | Global hooks path not documented by the codelabs; hooks + hooks.json are written under each surface root best-effort (the hook scripts are fail-open). | Low |
| DF-v3121-opencode-global-dir | Phase 4 (sweep) | OpenCode docs cite `~/.config/opencode/skills` as the canonical global dir; we flatten to `~/.opencode/skills`. Mitigated: OpenCode also reads `~/.claude/skills` + `~/.agents/skills`, both flattened on a full install. | Low |
| DF-v3121-gemini-ide-skill-dir | Phase 4 (sweep) | `~/.gemini/skills` flattening is confirmed for Gemini CLI; the Gemini IDE (Code Assist) skill dir is applied on weight-of-evidence. The SKILL_INDEX in GEMINI.md covers Code Assist regardless. | Low |
| DF-v3121-antigravity-project-instruction | Phase 3 (carried from v3.11 C4) | Project instruction is written to `.agents/AGENTS.md`; the platform may also read a project-root `AGENTS.md`. The global `~/.gemini/GEMINI.md` + project `.agents/` surfaces carry the instruction. | Low |

### Warnings

| ID | Source | Reason | Severity |
|---|---|---|---|
| WN-v3121-skill-description-length | Phase 5 (new skill) | `validate_skills.py` full mode flags `platform-contract-verification`'s frontmatter `description` as >250 chars (683) - the catalog-wide pushy-description vs 250-char tension (164 skills already carry it; full mode is not part of `make validate`, which is clean). | Low |

### Notes

- Each DF item maps 1:1 to a "Residual live-verification gaps" entry in [docs/policy/platform-read-contracts.md](../../../policy/platform-read-contracts.md); the `/update release` `platform-contract-verification` step closes them over successive releases as live confirmation arrives.
- Native skill injection is intended, not a gap: the flattened platforms expose ~284 native skills (265 catalog + 19 command-skills) alongside the `{{SKILL_INDEX}}` in each instruction file - a user-approved decision.
- The `~/.agents/skills` shared location (written by Codex, read by OpenCode and Gemini CLI) mitigates DF-v3121-opencode-global-dir.

### Resolved

_None resolved in v3.12.1 yet._
