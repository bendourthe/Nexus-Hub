"""Semantic contract tests for the v4.1.0 skill-mechanics adoption plan."""

import re

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
SKILL_CREATE = (
    ROOT / "catalog" / "skills" / "workflow" / "skill-create" / "SKILL.md"
).read_text(encoding="utf-8")
SKILL_STOCKTAKE = (
    ROOT / "catalog" / "skills" / "workflow" / "skill-stocktake" / "SKILL.md"
).read_text(encoding="utf-8")
TYPED_BOUNDARY = (
    ROOT
    / "catalog"
    / "skills"
    / "language-specialists"
    / "typed-boundary-hygiene"
    / "SKILL.md"
).read_text(encoding="utf-8")
TYPESCRIPT_EXPERT = (
    ROOT / "catalog" / "skills" / "language-specialists" / "typescript-expert" / "SKILL.md"
).read_text(encoding="utf-8")
TYPESCRIPT_REFERENCE_DIR = (
    ROOT / "catalog" / "skills" / "language-specialists" / "typescript-expert" / "references"
)
TYPESCRIPT_REFERENCE_FILES = sorted(TYPESCRIPT_REFERENCE_DIR.rglob("*.md"))
TYPESCRIPT_REFERENCES = "\n".join(
    path.read_text(encoding="utf-8") for path in TYPESCRIPT_REFERENCE_FILES
)
JAVASCRIPT_CLEANUP = (
    ROOT / "catalog" / "skills" / "code-cleanup" / "javascript-cleanup" / "SKILL.md"
).read_text(encoding="utf-8")
CONTINUOUS_LEARNING = (
    ROOT / "catalog" / "skills" / "workflow" / "continuous-learning" / "SKILL.md"
).read_text(encoding="utf-8")
SKILL_DESCRIPTION_AUTHORING = (
    ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "skill-description-authoring"
    / "SKILL.md"
).read_text(encoding="utf-8")


def _typescript_assertion_columns(line: str) -> list[int]:
    """Return `as` columns that are assertions rather than other TS syntax."""
    code = line.split("//", 1)[0]
    code = re.sub(
        r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`',
        '""',
        code,
    )
    assertions: list[int] = []
    for match in re.finditer(r"\bas\b", code):
        before = code[: match.start()]
        after = code[match.end() :].lstrip()
        if after.startswith("const"):
            continue
        if after.startswith(("?:", ":", ",", "??", "=")):
            continue
        if re.search(r"\[[^\]]*\bin keyof\b[^\]]*$", before):
            continue
        if re.search(r"\b(?:import|export)\s*\{[^}]*$", before):
            continue
        if re.search(r"\b(?:import|export)(?:\s+type)?\s+\*\s*$", before):
            continue
        if re.search(r"[=(:,?]\s*$", before):
            continue
        assertions.append(match.start())
    return assertions


def test_agents_declares_skill_bodies_are_operational_runbooks():
    assert "Treat every SKILL.md body as an operational runbook" in AGENTS
    assert "supporting knowledge belongs in Tier-3 `references/`" in AGENTS


def test_skill_create_requires_runbook_instructions_and_tier_three_pedagogy():
    assert "Instructions as an operational runbook" in SKILL_CREATE
    assert "This domain needs a tutorial first" in SKILL_CREATE
    assert "supporting pedagogy in Tier-3 `references/`" in SKILL_CREATE


def test_stocktake_reports_expert_tutorials_as_advisory_backlog():
    assert "label it `runbook-backlog` in the report" in SKILL_STOCKTAKE
    assert "do not rewrite the expert skill during the stocktake" in SKILL_STOCKTAKE
    assert "do not turn this advisory label into a `make validate` failure" in SKILL_STOCKTAKE


def test_typed_boundary_skill_declares_single_rule_owner_per_concern():
    assert "## Rule Ownership" in TYPED_BOUNDARY
    assert "Function-contract `unknown` / `object` / unsafe dictionaries" in TYPED_BOUNDARY
    assert "Type-system design, generics, and discriminated unions" in TYPED_BOUNDARY
    assert "Boundary parsing of unknown I/O with Zod or `safeParse`" in TYPED_BOUNDARY


def test_typed_boundary_skill_covers_the_required_low_evidence_patterns():
    for required in (
        "as unknown as",
        "conditional empty object spreads",
        "`vi.mock` or `jest.mock`",
        "`Reflect.get` or `Reflect.apply`",
        "Record<string, unknown>",
        "widen-then-assert",
        "SAFETY:",
    ):
        assert required in TYPED_BOUNDARY


def test_non_owners_hand_contract_hygiene_to_typed_boundary_skill():
    assert "replace with `unknown` and narrow" not in TYPESCRIPT_EXPERT
    assert "hand contract cleanup to [[typed-boundary-hygiene]]" in TYPESCRIPT_EXPERT
    assert "[[typed-boundary-hygiene]] -- owns low-evidence" in JAVASCRIPT_CLEANUP


def test_runtime_narrowing_entrypoints_are_explicit_exceptions():
    for skill in (TYPED_BOUNDARY, TYPESCRIPT_EXPERT):
        assert "runtime parser" in skill
        assert "type predicate" in skill
        assert "assertion function" in skill or "assertion-function" in skill


def test_typescript_reference_bundle_does_not_teach_low_evidence_dictionaries():
    assert TYPESCRIPT_REFERENCE_FILES
    assert "Record<string, unknown>" not in TYPESCRIPT_REFERENCES
    assert "z.unknown()" not in TYPESCRIPT_REFERENCES
    assert "handler as (data: never)" not in TYPESCRIPT_REFERENCES
    assert "data as never" not in TYPESCRIPT_REFERENCES


def test_all_non_const_assertions_name_their_invariant_in_full_reference_bundle():
    for path in TYPESCRIPT_REFERENCE_FILES:
        lines = path.read_text(encoding="utf-8").splitlines()
        in_typescript = False
        for index, line in enumerate(lines):
            if line.startswith("```"):
                in_typescript = line.strip() in {"```ts", "```typescript"}
                continue
            if in_typescript and _typescript_assertion_columns(line):
                assert index > 0 and "SAFETY:" in lines[index - 1], (
                    f"{path}:{index + 1}: assertion lacks an adjacent SAFETY invariant"
                )


def test_assertion_detector_covers_lowercase_unknown_and_object_targets():
    for line in (
        "const text = value as string;",
        "const raw = value as unknown;",
        "const record = value as { id: string };",
    ):
        assert _typescript_assertion_columns(line)
    assert not _typescript_assertion_columns("const literal = value as const;")
    assert not _typescript_assertion_columns("type Getters<T> = { [K in keyof T as `get${K}`]: T[K] };")
    assert not _typescript_assertion_columns('const Component = as ?? "span";')
    assert not _typescript_assertion_columns("as?: E;")
    assert not _typescript_assertion_columns("as,")
    assert not _typescript_assertion_columns('type Props = Omit<Base, "as">;')
    assert not _typescript_assertion_columns('<Text as="label">Label</Text>')
    assert not _typescript_assertion_columns("import * as React from module;")
    assert not _typescript_assertion_columns("export * as api from module;")


def test_distillation_refuses_unlabeled_mixed_evidence():
    for skill in (CONTINUOUS_LEARNING, SKILL_CREATE):
        assert "explicit `success` or `failure` label" in skill
        assert "refuse" in skill
        assert "unlabeled" in skill
        assert "outbound LLM-as-judge" in skill


def test_skill_create_names_git_history_success_bias_and_real_failures():
    assert "Git history is success-biased" in SKILL_CREATE
    assert "revert, a follow-up fix, or a user-supplied counterexample" in SKILL_CREATE


def test_stocktake_confusability_pass_is_bounded_and_advisory():
    assert "### 4c. Audit semantic confusability" in SKILL_STOCKTAKE
    assert "Do not compare every pair in the catalog" in SKILL_STOCKTAKE
    assert "## Confusable clusters" in SKILL_STOCKTAKE
    assert "typed-boundary-hygiene` / `typescript-expert" in SKILL_STOCKTAKE
    assert "never turn this advisory pass into a `validate_skills.py` error" in SKILL_STOCKTAKE


def test_description_authoring_keeps_pushy_fences_and_adds_two_level_triggers():
    assert "### Rule 7: Pair the category with a strict observable" in SKILL_DESCRIPTION_AUTHORING
    assert "Level 1 - category or domain" in SKILL_DESCRIPTION_AUTHORING
    assert "Level 2 - strict observable" in SKILL_DESCRIPTION_AUTHORING
    assert "Exact invocation is neither sufficient nor necessary" in SKILL_DESCRIPTION_AUTHORING
    assert "Synonyms and verbatim user phrases remain required" in SKILL_DESCRIPTION_AUTHORING
    assert "`SKIP` fences are load-bearing" in SKILL_DESCRIPTION_AUTHORING
