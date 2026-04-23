# DevAI-Hub v0.9.7 Release Notes

**Release date**: 2026-04-22
**Headline**: Opus 4.7 alignment, security expansion, and a lower-cost installer default. Phase 5 (VS Code extension effort-level integration) partially deferred - see Deferred section.

---

## Highlights

- **Opus 4.7 alignment across the stack.** New `guides/SESSION_LIFECYCLE_DECISIONS.md` codifies when to continue, `/rewind`, `/clear`, `/compact`, or delegate to a subagent. A full `## Effort-Level Strategy` section in `prompt-engineering/SKILL.md` documents all five tiers with a decision table and explicit anti-patterns. The "Opus 4.7 Practices" section captures four prompting habits specific to 4.7 (positive examples, explicit tool-invocation, adaptive thinking without fixed budgets, first-turn specification checklists). The batched clarifying-questions rule replaces the unbounded 4.6-era variant in all 5 platform base templates plus the global `CLAUDE.md`. Installer default `effortLevel` remains `xhigh`.
- **Security expansion: two new skills + a deeper pen-test mode.** `business-logic-abuse` (domain-aware race conditions, TOCTOU, double-spending, workflow bypass, idempotency, check-sequence abuse) and `advanced-attack-patterns` (state desynchronization, cache poisoning, replay attacks, timing side channels) now power an optional 6th hunter in `/run-penetration-test --depth=deep`. Plus a new `file-upload-security` checklist covering polyglot files, archive path traversal, zip-bomb defenses, and safe serving.
- **Context engineering for the 1M window.** The `context-degradation` skill now carries a 1M-token calibration table with action thresholds at 100k / 300k / 500k. `context-compression` documents the proactive `/compact focus on X, drop Y` steering pattern with six directly-usable directives. `session-history` gains a "Summarize from here (mid-session handoff)" mode with a paste-ready template.
- **Consolidated migration guide.** `docs/v0.9.6/opus-4-7-migration.md` is the single document to read when upgrading from a 4.6-era project. TL;DR captures four must-do items; a 13-row cross-reference table indexes every behavioral delta to its canonical catalog location.
- **Planning workflow generalized.** `/generate-implementation-plan` is now `/generate-plan` (legacy alias preserved) with a plan-type selector (Initial / Feature / Refactor / Other) and a generalized `docs/<version>/plans/<slug>.md` output path. `/implement-phase` discovers both the new layout and the legacy `docs/**/implementation-plan.md` pattern.
- **Deep-research compilation toolchain.** New `/compile-deep-research` command + `deep-research-compilation` skill + backing `scripts/compile_deep_research.py` (~1700 lines, 4 sub-commands: extract / dedupe / generate / validate) compiles multiple research reports across 7 input formats (.docx, .md, .pdf, .pptx, .html, raw URLs, .txt) into a single unified document in .docx, .pdf, or .md form. References are deduplicated via DOI -> normalized URL -> rapidfuzz title match; inline [N] citations are renumbered against the canonical list. New bundled `templates/documentation/branded-report-template.docx` provides styled output with teal title, Calibri Light small-caps headings, auto-TOC, and hanging-indent references.
- **Repo-scoped AI agent instruction set.** New `AGENTS.md` section "Installer-Aware Changes (Cross-Platform)" codifies how new `scripts/*.py` must be registered in both installers and how new skills must update the three registry files. Thin pointer files for every agentic platform: `CLAUDE.md` + `GEMINI.md` (both using `@AGENTS.md` import), `.github/copilot-instructions.md` (inline - Copilot cannot import), `.cursor/rules/devai-hub.mdc` (`alwaysApply: true`). All files enforce the platform-agnostic constraint: `templates/ai-instructions/base-*.md` must be edited in lockstep across all five platforms.

---

## What's new

### New skills (3)

- **`business-logic-abuse`** (Security) - identifies business-logic flaws that generic scanners miss because they depend on application-specific invariants. Covers six attack classes with code-trace procedures and architectural remediation.
- **`advanced-attack-patterns`** (Security) - four applicability-gated attack classes beyond the OWASP Top 10 baseline.
- **`deep-research-compilation`** (Specialized Domains) - multi-source research compilation with reference deduplication and citation renumbering; emits .docx / .pdf / .md with anchored References.

### New guides (2)

- **`guides/SESSION_LIFECYCLE_DECISIONS.md`** - five-branch decision tree with ASCII flowchart, trigger criteria, three worked examples, and cross-links from the token-optimization guide and six orchestration / workflow SKILLs.
- **`docs/v0.9.6/opus-4-7-migration.md`** - operator migration guide synthesizing the 4.6 -> 4.7 behavioral deltas (TL;DR + 4 must-do items + 5 what-to-remove items + 13-row cross-reference table + migration checklist).

### New checklist (1)

- **`catalog/checklists/file-upload-security.md`** - five-section defense checklist (file-type validation, path handling, size/resource limits, content scanning, storage/serving).

### New commands

- **`/run-penetration-test --depth=deep`** - optional 6th hunter (Business Logic & Advanced Attacks) gated behind the flag. Adds ~20% aggregate cost; required to populate WSTG-BUSL and the advanced-attack rows of the Coverage Matrix.
- **`/compile-deep-research`** (+ companion `compile-deep-research-style-guide.md`) - 9-phase command that turns multiple research reports into one unified document. Backed by `scripts/compile_deep_research.py` (4 sub-commands: extract, dedupe, generate, validate). Auto-installed to `~/.devai-hub/scripts/` by the installer.

### New supporting artifacts

- **`scripts/compile_deep_research.py`** - multi-format input parser, reference dedup engine, output formatter. Installed to `~/.devai-hub/scripts/`.
- **`templates/documentation/branded-report-template.docx`** - styled Word template (teal title, Calibri Light small-caps headings, auto-TOC, hanging-indent references) that ships alongside the existing generic template.

### New AI agent instructions (repo-scoped)

- **`AGENTS.md` "Installer-Aware Changes (Cross-Platform)" section** - canonical rules for any new `scripts/*.py` / new skill / platform template edit.
- **`CLAUDE.md`, `GEMINI.md`** - thin `@AGENTS.md` pointer files for Claude Code and Gemini CLI / Antigravity.
- **`.github/copilot-instructions.md`** - inline summary for GitHub Copilot (which cannot use `@` imports).
- **`.cursor/rules/devai-hub.mdc`** - Cursor IDE rule with `alwaysApply: true` frontmatter.

### Extended skills (content additions; no new skill entries)

- `prompt-engineering` - `## Effort-Level Strategy` + `## Opus 4.7 Practices` sections.
- `ai-agent-development` - `## Anti-Patterns (Opus 4.7)` table.
- `multi-agent-coordinator` - `### Step 0: Should I delegate to a subagent?` + Pattern A explicit fan-out callout with three worked prompts.
- `context-compression` - proactive `/compact focus on X, drop Y` steering subsection.
- `context-degradation` - 1M-window Lost-in-Middle calibration table.
- `session-history` - "Summarize from here (mid-session handoff)" operating mode with paste-ready template.
- `security-patch-advisor` - new `## Related Resources` footer cross-linking the new security skills and the file-upload checklist.

### Configuration changes (operator-facing)

- Batched clarifying-questions rule applied across all 5 platform base templates plus the global `CLAUDE.md`.
- Installer default `effortLevel` remains `xhigh` (unchanged).

---

## Migration notes

Upgrading from v0.9.6? Read [`docs/v0.9.6/opus-4-7-migration.md`](v0.9.6/opus-4-7-migration.md) - the TL;DR's four must-do items capture most of the value.

- **No breaking API changes.** No data migration.
- **`~/.claude/settings.json` effortLevel**: v0.9.7 keeps `xhigh` as the shipped default, unchanged from v0.9.6. De-escalate to `high` for cost-sensitive concurrent work via `/effort high` or the `CLAUDE_CODE_EFFORT_LEVEL` environment variable.
- **Platform templates**: if you customized any of the `templates/ai-instructions/base-*.md` files locally, re-merge the new batched clarifying-questions rule (replaces the prior "Ask clarifying questions before coding..." variant).
- **Plan file layout**: if you have existing plans at `docs/**/implementation-plan.md`, they still work - `/implement-phase` retains legacy discovery. New plans authored with `/generate-plan` will land at `docs/<version>/plans/<slug>.md`.

---

## Deferred

- **VS Code extension effort-level integration** - originally planned Phase 5 deliverable (hover help + usage-banded auto-switch in `claude-usage-monitor`). Shipped as a documentation roadmap in the extension README rather than a functional integration because two upstream Claude Code primitives are missing: (a) no reliable mechanism for an extension to observe mid-session `/effort` changes (open issue `anthropics/claude-code#31415`); (b) `settings.json` edits do not propagate live to a running session (open issue `anthropics/claude-code#17127`). Will be reconsidered in a future minor release when the upstream primitives exist. See the Phase 5 session history for full context.

---

## Known issues

- Pre-v0.9.6 CHANGELOG entries contain legacy non-ASCII characters (em-dashes, curly quotes) from early releases. v0.9.6 and v0.9.7 entries are ASCII-clean. An older-entries scrub was deferred as non-blocking.
- The `claude-usage-monitor` extension README documents an auto-switch usage-band roadmap that is opt-in and not yet implemented. The top-of-band `xhigh` matches the installed default; the auto-switch de-escalates as usage rises.

---

## Tag and push

The `v0.9.7` annotated tag has NOT been created yet; it must attach to the release commit, which exists only after the pending changes in the working tree are committed.

Recommended sequence after this release note is approved:

```bash
# 1. Review the staged changes and commit the v0.9.7 batch
git status
git diff --stat

# 2. Create a single release commit (or a sequence of conventional commits, one per sub-task, per the session histories' commit-message suggestions)
git add -A
git commit -m "release: v0.9.7 - Opus 4.7 alignment + security expansion + lower-cost default"

# 3. Create the annotated tag pointing to the release commit
git tag -a v0.9.7 -m "Release v0.9.7 - Opus 4.7 alignment + security expansion + lower-cost effort-level default"

# 4. Push main + the tag (only after explicit user approval)
git push origin main
git push origin v0.9.7

# 5. Create the GitHub release (only after explicit user approval)
gh release create v0.9.7 -F docs/v0.9.7/RELEASE_NOTES.md --title "v0.9.7 - Opus 4.7 alignment and security expansion"
```

Do not run steps 4 or 5 until explicitly approved. Step 3 (local tag) is safe to run anytime after step 2.

---

## Further reading

- Full changelog: [CHANGELOG.md](../../CHANGELOG.md) v0.9.7 section
- Migration guide: [docs/v0.9.6/opus-4-7-migration.md](../v0.9.6/opus-4-7-migration.md)
- Session histories (per-phase detail): [docs/v0.9.7/development/history/](development/history/)
- Implementation plan: [docs/v0.9.7/implementation-plan.md](implementation-plan.md)
- Source gap analyses: `docs/v0.9.6/comparison-*.md`
