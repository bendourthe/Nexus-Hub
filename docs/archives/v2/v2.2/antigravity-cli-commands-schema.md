# Antigravity CLI commands schema vs. Gemini CLI commands schema

**Status**: STATIC ANALYSIS (no live Antigravity CLI install available at authoring time on 2026-05-21)
**Companion to**: [`docs/archives/v2/v2.2/antigravity-cli-probe.md`](antigravity-cli-probe.md)
**Action**: Sub-task 2.6 (T012) of [the codegraph-and-antigravity plan](plans/codegraph-and-antigravity.md). Confirms whether `scripts/lib/integrations/gemini_cli.py::_write_toml_commands` applies as-is to Antigravity CLI or whether a `_write_antigravity_commands` variant is required.

## 1. Gemini CLI command file schema (current, since v2.1.0)

`scripts/lib/integrations/gemini_cli.py` and the `TomlIntegration._write_toml_commands` helper in `scripts/lib/integrations/base.py:386-420` render every `catalog/commands/*.md` source as one `~/.gemini/commands/<name>.toml` file. The TOML schema is:

```toml
description = "<first heading from the source Markdown, with leading `#` stripped>"
prompt = """
<verbatim Markdown body, with `\\` escaped to `\\\\` and `"""` escaped to `\\"\\"\\"`>
"""
```

- File location: `~/.gemini/commands/<command-name>.toml` (global) or `<project>/.gemini/commands/<command-name>.toml` (workspace).
- File extension: `.toml`.
- Required fields: `description` (string, single line) and `prompt` (string, triple-quoted multi-line).
- Optional fields: none used by Nexus-Hub today. Gemini CLI also accepts `arguments`, `temperature`, `model`, but Nexus-Hub does not write them.

## 2. Antigravity CLI command file schema

### 2.1. Antigravity 2.0 desktop precedent

`scripts/lib/integrations/antigravity.py::Antigravity20Integration` sets `commands_subdir = "workflows"`, and the `SkillsIntegration._mirror_catalog` helper (in `scripts/lib/integrations/base.py:440-456`) copies `catalog/commands/` verbatim into `~/.agent/workflows/`. Source files keep their `.md` extension; no conversion happens.

This is the documented Antigravity 2.0 desktop behavior since v2.1.0. The 2026-05-21 Google Developers Blog announcement transitioning Gemini CLI to Antigravity CLI confirmed the CLI shares the desktop backend.

### 2.2. Inference for the Antigravity CLI surface

Therefore the Antigravity CLI commands schema is:

- File location: `~/.agent/workflows/<command-name>.md` (global) or `<project>/.agent/workflows/<command-name>.md` (workspace).
- File extension: **`.md`** (Markdown, not TOML).
- Required fields: none. The full Markdown body is the workflow body; the first H1 (or first non-blank line) is treated as the workflow name.
- Optional fields: YAML frontmatter is accepted for description / parameters but Nexus-Hub does not emit it.

## 3. Schema diff vs. Gemini CLI

| Aspect | Gemini CLI | Antigravity 2.0 + CLI |
|---|---|---|
| Directory | `~/.gemini/commands/` | `~/.agent/workflows/` |
| File extension | `.toml` | `.md` |
| Wrapping | `description = "..."`, `prompt = """..."""` block | Verbatim Markdown |
| Escaping | `\\` and `"""` escaped | None (Markdown is verbatim) |
| Frontmatter | not used | accepted (optional) |
| Nexus-Hub helper | `TomlIntegration._write_toml_commands` | `SkillsIntegration._mirror_catalog` |

The two surfaces use **different file formats**, **different directories**, and **different helpers**. Antigravity CLI does NOT inherit Gemini CLI's TOML schema; it inherits the Antigravity 2.0 desktop's Markdown schema.

## 4. Sample files

### 4.1. Gemini CLI -- `~/.gemini/commands/clarify-spec.toml`

```toml
description = "Clarify Spec Command"
prompt = """
# Clarify Spec Command

Sequential 5-question clarification loop for an existing spec.md...

(verbatim Markdown body of catalog/commands/clarify-spec.md)
"""
```

### 4.2. Antigravity CLI -- `~/.agent/workflows/clarify-spec.md`

```markdown
# Clarify Spec Command

Sequential 5-question clarification loop for an existing spec.md...

(verbatim Markdown body of catalog/commands/clarify-spec.md)
```

The Antigravity CLI form is the Gemini CLI form's `prompt = """..."""` body, served as a standalone Markdown file at a different path.

## 5. Decision: do we need a separate `_write_antigravity_commands` helper?

**No.** The existing `SkillsIntegration._mirror_catalog` helper already does the right thing for Antigravity 2.0 + CLI: it copies `catalog/commands/*.md` verbatim into `~/.agent/workflows/`. The `Antigravity20Integration` config dict at `scripts/lib/integrations/antigravity.py:36-49` already declares `commands_subdir = "workflows"`, so the existing install path is correct.

No code change is required in sub-task 2.6 (T012). The `_write_toml_commands` helper at `scripts/lib/integrations/base.py:386-420` is **Gemini-CLI-specific** (and remains so post-2026-06-18, for enterprise users running the legacy Gemini CLI).

## 6. Open items

The following remain `(open)` until a live Antigravity CLI install is available for empirical verification (tracked as `WN` warnings in `<version_dir>/known-gaps.md`):

1. **Verify the Markdown file is the canonical Antigravity CLI workflow format**. If Google diverges the CLI from the desktop and ships a different file format (e.g., custom JSON manifest), sub-task 2.6 (T012) re-opens and a `_write_antigravity_commands` helper variant is added.
2. **Verify the workflow name is derived from the first H1**. If Antigravity CLI uses a different name-derivation rule (e.g., filename only, ignoring H1), Nexus-Hub command file naming may need to align.
3. **Verify YAML frontmatter, if present, is honored by Antigravity CLI**. Some Nexus-Hub commands carry frontmatter for human-readable metadata; if the CLI rejects unknown keys, those commands may need a strip pass before mirroring.

All three are warnings, not blockers; the Antigravity 2.0 desktop behavior is documented and the CLI inherits it.

## 7. References

- Probe: [docs/archives/v2/v2.2/antigravity-cli-probe.md](antigravity-cli-probe.md)
- Phase 2 plan reference: [docs/archives/v2/v2.2/plans/codegraph-and-antigravity.md](plans/codegraph-and-antigravity.md) sub-task 2.6 (T012)
- Gemini CLI helper: [scripts/lib/integrations/base.py](../../scripts/lib/integrations/base.py) `_write_toml_commands`, lines 386-420
- Antigravity 2.0 + CLI helper: [scripts/lib/integrations/base.py](../../scripts/lib/integrations/base.py) `_mirror_catalog`, lines 440-456
- Antigravity 2.0 + CLI integration: [scripts/lib/integrations/antigravity.py](../../scripts/lib/integrations/antigravity.py) `Antigravity20Integration`, lines 41-67
