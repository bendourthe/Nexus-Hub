# Per-skill Bundled Resources

How a skill ships heavy capability without inflating its always-loaded metadata or its SKILL.md body: the optional `scripts/`, `references/`, `assets/`, and `evals/` subdirectories, their naming rules, how the installer distributes them, and the orphan-bundle audit that keeps them referenced.

Relocated verbatim from `AGENTS.md` during the v3.18.0 ratchet-down (MT-1), which moved per-topic reference depth out of the always-loaded instruction file. `AGENTS.md` keeps a pointer here, and the three-tier loading model it depends on stays there.

---

A skill folder MAY (not MUST) contain three bundled subdirectories alongside `SKILL.md`:

```
catalog/skills/<category>/<skill-name>/
├── SKILL.md
├── scripts/         # optional - executable code for tier-3 deterministic operations
├── references/      # optional - Markdown docs the agent reads on demand
├── assets/          # optional - templates, icons, fonts, fixtures used by scripts or referenced from SKILL.md
└── evals/           # optional - trigger-cases.json routing assertions (consumed by run_trigger_evals.py; see below)
```

This convention is the operational expression of Tier 3 in the [Three-Tier Loading Model](../../AGENTS.md#three-tier-loading-model) above. It allows a skill to ship heavy capability (long runbooks, large generator scripts, design templates) without inflating the SKILL.md body or the always-loaded Tier 1 metadata.

**File naming**:

- `scripts/<name>.{py,sh,js,ps1}` - kebab-case, descriptive (e.g., `init-mcp-fastmcp.sh`, `package_skill.py`). PowerShell siblings (`.ps1`) MUST accompany every `.sh` script that ships under `scripts/` so Windows users get the same capability.
- `references/<topic>.md` - kebab-case, scoped by topic (e.g., `references/fastmcp-runbook.md`, `references/schemas.md`). Each reference file should be self-contained -- the agent reads it cold without the rest of the skill bundle in context.
- `assets/<descriptive-name>.<ext>` - any extension. Examples: `assets/flow-field.html`, `assets/themes/editorial-serif.json`, `assets/fonts/Inter.woff2`.

**Reference rule**: every file under `scripts/`, `references/`, `assets/` MUST be referenced at least once from the parent SKILL.md (or from another file in the bundle that is itself referenced). The validator enforces this -- see "Orphan-bundle detection" below. Empty subdirectories are tolerated only when they hold a single `.gitkeep` placeholder for a future expansion.

**Installer behavior**: both `scripts/installer.sh` and `scripts/installer.ps1` recursively copy the entire skill directory tree (`safe_folder_copy` / `Safe-Folder-Copy` use `rsync -a` / `cp -R` / `robocopy /MIR` respectively). Per-skill `scripts/`, `references/`, `assets/` subdirectories therefore land at the platform target alongside SKILL.md without any installer edit. This is the auto-distribution path called out in row 1 of the [Distribution channels the installer uses](../../AGENTS.md#distribution-channels-the-installer-uses) table; it explicitly does NOT require the explicit-name copy step that repo-level `scripts/<name>.py` artifacts require.

**Orphan-bundle detection**: `make validate` runs `scripts/validate_skills.py`, which now performs a per-skill bundle audit:

1. List every file under `scripts/`, `references/`, `assets/` for each skill.
2. Search the parent SKILL.md (and each `references/*.md`) for the file's basename.
3. Emit a warning for each unreferenced file, with the suggestion: "either reference this file from SKILL.md or remove it." `.gitkeep` is the only filename exempt from the reference check.

The check is a warning (not error) by default so that work-in-progress branches do not break CI. Orphan reports surface in the verbose output (`make validate` prints them at the end of the run when `--verbose` is passed, and pytest's `test_skill_bundles.py` asserts the validator detects an injected orphan in a fixture skill).

**Unfilled-placeholder lint** (v3.15.2): `validate_skills.py` also flags unfilled multi-word angle-bracket template placeholders, so a scaffolded-but-unfinished skill cannot pass validation silently. A placeholder is two or more single-space-separated lowercase words inside angle brackets (for example `<what this skill does>`); it is a HARD ERROR in both the `description` frontmatter field and the SKILL.md body prose, and it runs in the `--bundles-only` mode that `make validate` and CI invoke. Single-word CLI notation (`<path>`, `<name>`), uppercase template tokens (`<MAJOR>`), and HTML tags are NOT flagged (they lack a lowercase-words-with-only-spaces interior), and examples inside fenced code blocks or inline-code spans are exempt (wrap a literal placeholder in backticks to show it as documentation).

**Optional routing evals** (`evals/trigger-cases.json`, v3.15.2): a skill MAY ship a `evals/trigger-cases.json` file declaring how prompts should route to it. `scripts/run_trigger_evals.py` consumes these to assert, for each skill that has cases, that (a) every `should_trigger: true` prompt ranks its own skill first among all skills (else it names the skill it mis-routed to) and (b) the weakest positive clears the strongest near-miss negative by a configurable margin (default 1.15x). Skills WITHOUT a file are reported as a WARN, never a FAIL, so the catalog never blocks on incomplete coverage; the file is entirely optional and authored incrementally. Schema (all keys lowercase):

```json
{
  "skill": "<skill-name>",
  "purpose": "one-line purpose",
  "cases": [
    {"id": "pos-1", "prompt": "real user phrasing", "should_trigger": true,  "assert": "routes to <skill> first", "lexical": true},
    {"id": "neg-1", "prompt": "look-alike request", "should_trigger": false, "assert": "routes to <other>, not here", "lexical": true}
  ]
}
```

Each file needs at least three positive cases (real phrasings a user would type) and three near-miss negatives (look-alike requests drawn from the skill's own SKIP clause). `lexical` is optional (default true); a `lexical: false` case triggers via agent reasoning rather than description vocabulary, so the deterministic runner SKIPS it (it is left for behavioral evals). The `evals/` subdir is consumed by the runner, NOT referenced from SKILL.md, so it is exempt from the orphan-bundle audit above.

**Cross-links**: see [Three-Tier Loading Model](../../AGENTS.md#three-tier-loading-model) for the loading-cost rationale, the [SKILL.md size norm](../../AGENTS.md#skill-md-size-norm) for when to push body content into `references/`, and the v1.1.3 four-hook precedent (`catalog/hooks/{claude,gemini,codex,opencode}-diff-review.sh`) for the parity invariant that applies when a `scripts/` directory ships per-CLI variants.

**Workflow templates (Dynamic Workflows)**: a skill MAY ship a Dynamic-Workflow JavaScript file (under its `scripts/` or `assets/` directory) and reference it from SKILL.md **as a template to adapt, not a verbatim script to run**. This is the workflow-as-skill-bundle distribution pattern: it lets a skill ship a ready-made fan-out harness (e.g. the dimensions -> find -> adversarially-verify review shape, or a fan-out -> fetch -> verify -> synthesize research shape) without inflating the SKILL.md body. Three rules are mandatory:

1. **Graceful degradation.** Dynamic Workflows is a plan-gated research-preview capability that may be absent in the user's harness. The template MUST fall back to isolated subagents (small surface) or a single sequential agent (smallest surface), and the skill MUST NOT hard-depend on the workflow runtime being present.
2. **Scope-first token caution.** Because a fan-out carries a 5-15x token multiplier, the template MUST carry the scope-first discipline inline: calibrate on one folder first, review the execution plan on the first trigger, and confirm before going full-scale. Cross-link `[[ai-billing-safeguards]]` for the hard budget controls.
3. **Skill-native.** The template introduces no outbound call, no dependency, and no credential; the subagents it spawns use only the harness's own tools.

Use `agent-orchestration-primitives` as the decision guide for whether a fan-out is warranted at all, and see its `assets/example-fanout-workflow.js` for the reference template. The orphan-bundle audit (below) applies unchanged: the `.js` file MUST be referenced from SKILL.md like any other bundled resource.
