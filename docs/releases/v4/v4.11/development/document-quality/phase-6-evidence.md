# Phase 6 Evidence - Wiring, Rule File, and Cross-Surface Consistency

**Project**: Nexus-Hub
**Plan**: [v4.11.2 document and deck quality](../../../../../archives/v4/v4.11/plans/v4.11.2-adoption-document-and-deck-quality.md)
**Phase**: 6 of 7
**Branch**: `feat/v4.11.2-document-deck-quality`
**Date**: 2026-09-13
**Status**: complete

## Model routing

Plan recommends frontier at high effort; ran on Opus 5 (strong tier), delta recorded.

## Why this phase exists

Every gate built in Phases 1 to 5 was opt-in until now. A gate nothing invokes
is decorative, and this repository has already paid for that: `check_handbooks.py`
was written in v4.11.0, wired into no CI profile, and therefore never ran against
the repository's own handbooks until Phase 7 of that plan noticed - by which
point they had been stale for four commits.

## Delivered

- `catalog/rules/html/visual-self-verification.md`, a global rule beside `responsive-layout.md`.
- The `rendered-artifact-verified` gate in `[[quality-gate-definitions]]`, seven criteria.
- A claim-to-evidence row in `[[verification-before-completion]]`: re-reading the source you just wrote confirms the source, not the render.
- Reorder consistency and generated-region fences in `[[technical-documentation]]`.
- The gate wired into `presentify`, the skill's own pipeline, `/update docs`, and `/update release`.
- `tests/skills/test_rendered_gate_wiring.py`, which asserts the wiring itself.

## The gate

| # | Criterion |
|---|---|
| R1 | renders with zero page errors |
| R2 | the geometric audit returns zero findings |
| R3 | nothing overflows its designed container |
| R4 | every figure and table reference resolves |
| R5 | line endings unchanged from baseline |
| R6 | the unmeasurable decisions are recorded |
| R7 | the edited region was captured and inspected |

R5 is there because a whitespace pass during THIS plan silently rewrote eight
files of a byte-frozen qualification corpus, invalidating the manifest that made
the benchmark meaningful. Nothing else in the release flow would have caught it.

R7 is the only criterion a machine cannot fully settle, and it is the one the
source project's failures traced to most often.

## Exit 2 is not a pass

Both gate scripts exit 0 on a pass, 1 on findings, 2 when they could not verify.
Every calling surface states that exit 2 means unverified, and
`test_exit_two_is_documented_as_unverified_on_every_calling_surface` asserts the
statement is present. Reporting unverified as success is the precise failure the
whole gate exists to prevent.

## Wiring is asserted, not assumed

`test_rendered_gate_wiring.py` maps each surface to the references it must
carry, so a refactor that drops one fails here rather than silently unwiring the
gate while the documentation keeps claiming otherwise.

Negative-controlled:

```
# geometric_audit.py replaced with a placeholder in presentify.md
E  AssertionError: catalog/commands/presentify.md no longer references
   'geometric_audit.py'; the gate is unwired on that surface
1 failed, 8 passed

# restored
9 passed
```

## Verification

```
python -m pytest tests/skills/test_rendered_gate_wiring.py -q
  9 passed in 0.07s

python scripts/ci/run.py --profile fast
  PASS: 14 passed, 0 failed, 0 skipped, 0 advisory in 8.5s
```

## An anchor assertion caught a real ambiguity

The first wiring script asserted `"## Gate: docs-complete"` appeared exactly
once. It appeared twice, because `## Gate:` is a substring of `#### Gate:` and
the file carries both a section heading and a fenced definition. The assertion
failed rather than inserting in the wrong place.

That is the rule the new global file states in its own text - assert the anchor
is present and unique before replacing - demonstrated on the commit that
introduced it.

## CI impact

Recorded against `cicd-architect`; no pipeline file edited.

- **New test path**: `tests/skills/test_rendered_gate_wiring.py`, covered by the existing `repo-tests` glob. Stdlib-only, no browser, 0.07s.
- **New rule file**: `catalog/rules/html/visual-self-verification.md`. Auto-copied by both installers with the rest of `catalog/rules/`; no installer edit needed.
- **Behaviour change for consumers**: `presentify`, `/update docs` and `/update release` now carry a mandatory post-generation gate. A generated artifact with findings fails where it previously passed silently.

## Phase 6 exit checklist

- [x] The composite gate is callable from every wired command and can fail.
- [x] A stale navigation entry or cross-reference fails after a reorder.
- [x] Every gate negative-controlled.
- [x] Exactly one scoped local commit; no push.
