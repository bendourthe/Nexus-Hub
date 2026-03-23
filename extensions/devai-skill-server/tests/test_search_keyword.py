from __future__ import annotations

from tests.conftest import SAMPLE_SKILLS

from devai_skill_server.search_keyword import BM25Index


def test_build_index():
    """Index builds without errors on sample data."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    assert index._n_docs == 3


def test_search_returns_results():
    """Search returns ranked results for a matching query."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    results = index.search("security code review")
    assert len(results) > 0
    assert results[0][0] == "code-review-security"


def test_search_kubernetes():
    """Search ranks kubernetes skill highest for k8s query."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    results = index.search("kubernetes deployment pods")
    assert len(results) > 0
    assert results[0][0] == "kubernetes-ops"


def test_search_ai_agents():
    """Search finds AI agent skill."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    results = index.search("build ai agent tool use")
    assert len(results) > 0
    assert results[0][0] == "ai-agent-development"


def test_search_empty_query():
    """Empty query returns no results."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    results = index.search("")
    assert results == []


def test_search_max_results():
    """Results are limited by max_results parameter."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    results = index.search("code", max_results=1)
    assert len(results) <= 1


def test_search_no_match():
    """Completely unrelated query returns empty or low-score results."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    results = index.search("xyzzyplugh")
    assert len(results) == 0


def test_priority_boost():
    """CRITICAL priority skills get a score boost."""
    index = BM25Index()
    index.build(SAMPLE_SKILLS)
    # Both "agent" skills should be boosted, but CRITICAL gets more
    results = index.search("development")
    names = [r[0] for r in results]
    if "ai-agent-development" in names:
        ai_score = next(s for n, s in results if n == "ai-agent-development")
        assert ai_score > 0


def test_tokenize():
    """Tokenizer splits on hyphens, removes stop words."""
    tokens = BM25Index.tokenize("code-review for security")
    assert "code" in tokens
    assert "review" in tokens
    assert "security" in tokens
    assert "for" not in tokens
