"""Wire the composite gate into presentify and the skill's pipeline."""

import pathlib

ROOT = pathlib.Path("C:/Users/BEDOURTHE/nh-412")

# ---- presentify: register the helpers and make the gate mandatory ----------
cmd = ROOT / "catalog/commands/presentify.md"
text = cmd.read_text(encoding="utf-8")

old_row = "| Retained assembly or legacy plain draft | `scripts/build_presentation.py` |"
assert text.count(old_row) == 1
new_rows = (
    old_row
    + "\n| Rendered geometry audit | `scripts/geometric_audit.py` |"
    + "\n| Attestation completeness | `scripts/check_attestation.py` |"
)
text = text.replace(old_row, new_rows)

anchor = "## Output\n"
assert text.count(anchor) == 1

GATE = """## Post-generation gate (mandatory)

Generation is not finished when the file is written. Run the
`rendered-artifact-verified` gate from `[[quality-gate-definitions]]` against
the artifact just produced, and treat a finding as a defect to fix rather than a
note to report:

```
python <skill>/scripts/geometric_audit.py <output.html>
python <skill>/scripts/check_attestation.py <attestation.json>
```

Both exit 0 on a pass, 1 on findings, and 2 when they could not verify. **Exit 2
is not a pass.** An unavailable renderer means the artifact is unverified, which
is the state the whole gate exists to make visible.

Then render the artifact and LOOK at the region you produced. The rule is
`catalog/rules/html/visual-self-verification.md`: a document is a visual
artifact, its correctness lives in rendered geometry rather than in source text,
and re-reading the markup you just wrote confirms the markup, not the render.
Never ask the user for a screenshot you can render yourself.

"""

text = text.replace(anchor, GATE + anchor)
cmd.write_text(text, encoding="utf-8", newline="\n")
print(f"  presentify.md -> {len(cmd.read_text(encoding='utf-8').splitlines())} lines")

# ---- the skill's own pipeline gets the same step ---------------------------
skill = ROOT / "catalog/skills/specialized-domains/document-to-interactive-html/SKILL.md"
text = skill.read_text(encoding="utf-8")

marker = "## Rule ownership\n"
assert text.count(marker) == 1

STEP = """## Post-generation gate

Every route that writes an artifact finishes with the same two commands, and a
finding is a defect to fix rather than a note to pass along:

```
python scripts/geometric_audit.py <output.html>      # 0 pass, 1 findings, 2 unverified
python scripts/check_attestation.py <attestation>    # 0 complete, 1 incomplete, 2 unreadable
```

Exit 2 never counts as a pass. An unavailable renderer means unverified, and
reporting unverified as success is the failure this whole gate exists to
prevent.

The rendered-region capture that closes the loop is owned by
`catalog/rules/html/visual-self-verification.md`, which binds every HTML
artifact this harness produces rather than this skill alone.

"""

skill.write_text(text.replace(marker, STEP + marker), encoding="utf-8", newline="\n")
print(f"  SKILL.md -> {len(skill.read_text(encoding='utf-8').splitlines())} lines")

# ---- /update docs and /update release ---------------------------------------
upd = ROOT / "catalog/commands/update.md"
text = upd.read_text(encoding="utf-8")

docs_anchor = "- **Handbook markdown against the code**"
assert text.count(docs_anchor) == 1
DOCS_LINE = (
    "- **Rendered artifacts pass their gate**: every generated `.html` the docs scope "
    "touches passes `geometric_audit.py` (exit 0) and, where the build records one, "
    "`check_attestation.py`. Exit 2 is unverified, not a pass. Rule: "
    "`catalog/rules/html/visual-self-verification.md`.\n"
)
text = text.replace(docs_anchor, DOCS_LINE + docs_anchor)

rel_anchor = "7. **Unicode-hygiene gate on release artifacts (BLOCKING)**"
assert text.count(rel_anchor) == 1
REL = """7. **Rendered-artifact and generated-source gate**: every generated `.html` this release ships passes `geometric_audit.py`, and two properties are asserted that a content check cannot see.

    - **Generated regions have a single source of truth.** A fix patched into rendered output is reverted by the next regeneration from an unedited generator, silently and with no failing check in between. Edit the generator.
    - **Line endings are unchanged from baseline.** Compare each changed file against its committed blob. A whitespace pass during v4.11.2 silently rewrote eight files of a byte-frozen qualification corpus, invalidating the manifest that made the benchmark meaningful; nothing else in the release flow would have caught it.

"""
text = text.replace(rel_anchor, REL + rel_anchor)
upd.write_text(text, encoding="utf-8", newline="\n")
print(f"  update.md -> {len(upd.read_text(encoding='utf-8').splitlines())} lines")
