"""Inert corpus, projection, and deterministic observational scorer contracts."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "catalog/skills/code-review/security-review/scripts"
sys.path.insert(0, str(SCRIPTS))
import _benchmark_corpus as corpus

FIXTURES = ROOT / "tests/fixtures/security-audit-appsec"


@pytest.fixture
def answers():
    return json.loads((FIXTURES / "answers/manifest.json").read_text())


def test_exact_inert_corpus_and_frozen_projection(answers):
    original = corpus.snapshot(FIXTURES / "source", answers)
    with corpus.projection(FIXTURES / "source", answers, "0" * 64) as first:
        mapping = first.mapping
        first_root = first.source_root
        assert len(list(first_root.iterdir())) == 32
        assert first.answer_root not in first_root.parents
    assert not first_root.exists()
    with corpus.projection(FIXTURES / "source", answers, "0" * 64, mapping) as second:
        assert second.mapping == mapping and second.source_root != first_root
    assert corpus.snapshot(FIXTURES / "source", answers) == original


@pytest.mark.parametrize(
    "parameter",
    ["*args: marker()", "**kwargs: marker()", "arg: marker()", "arg=marker()"],
)
def test_python_definition_side_effects_rejected(parameter):
    text = f"def receive({parameter}):\n    return None\ndef handle(ctx, value):\n    return None\n"
    with pytest.raises(ValueError):
        corpus.inert_source("unit.py", text.encode())


@pytest.mark.parametrize(
    "extra",
    [
        "// {\n}\nmarker();\n// }",
        "/* { */\n}\nmarker();\n/* } */",
        "const value = `template`;",
        "const value = /regex/;",
    ],
)
def test_typescript_unsupported_lexical_syntax_rejected(extra):
    text = (
        "function receive(input: any): any { return input; }\nfunction handle(ctx: any): any {\n"
        + extra
        + "\n}"
    )
    with pytest.raises(ValueError):
        corpus.inert_source("unit.ts", text.encode())


@pytest.mark.parametrize(
    "mutation", ["count", "pair", "holdout", "chain", "path", "oracle", "manifest"]
)
def test_corpus_does_not_shrink_denominators(answers, mutation):
    if mutation == "count":
        answers["seeds"].pop()
    if mutation == "pair":
        answers["seeds"][1]["vulnerability_kind"] = answers["seeds"][0][
            "vulnerability_kind"
        ]
    if mutation == "holdout":
        answers["seeds"][0]["holdout"] = True
    if mutation == "chain":
        answers["seeds"][0]["source_to_sink"] = None
    if mutation == "path":
        answers["seeds"][0]["path"] = "../escape.py"
    if mutation == "oracle":
        answers["seeds"][0]["remediation_oracle"]["type"] = "execute"
    if mutation == "manifest":
        answers["source_manifest"].pop()
    with pytest.raises(ValueError):
        corpus.validate_answers(answers)


def test_projection_rejects_substitution_and_cleans_on_failure(answers):
    mapping = corpus.create_map(answers, "1" * 64)
    with pytest.raises(ValueError):
        corpus.validate_map(mapping, answers, "2" * 64)
    changed = copy.deepcopy(mapping)
    changed["entries"][0]["role"] = "other"
    changed["map_digest"] = corpus.audit.digest(
        {k: v for k, v in changed.items() if k != "map_digest"}
    )
    with pytest.raises(ValueError):
        corpus.validate_map(changed, answers, "1" * 64)
    with (
        pytest.raises(RuntimeError),
        corpus.projection(FIXTURES / "source", answers, "1" * 64, mapping) as projected,
    ):
        root = projected.source_root
        raise RuntimeError("injected")
    assert not root.exists()
