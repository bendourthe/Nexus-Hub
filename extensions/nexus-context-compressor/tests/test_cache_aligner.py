"""Tests for the CacheAligner KV-cache prefix stabilizer (Phase 3 T008).

Covers the stability-gate assertion (byte-identical stable prefix across two
inputs differing only in a trailing date) plus volatile-token detection for each
pattern, the no-dynamic identity case, whitespace normalization, line
preservation (nothing is dropped, only reordered), determinism, and graceful
degradation of the optional NER pass.
"""

from __future__ import annotations

from nexus_context_compressor.transforms.cache_aligner import (
    CacheAlignerConfig,
    align,
)

SYSTEM_PROMPT = """You are a helpful assistant.
Follow the project conventions.
Be concise and accurate.
Always cite sources."""


# --- Stability gate -----------------------------------------------------------


def test_stable_prefix_identical_across_trailing_date():
    a = align(SYSTEM_PROMPT + "\nCurrent date: 2026-06-09")
    b = align(SYSTEM_PROMPT + "\nCurrent date: 2026-06-10")
    assert a.stable_prefix == b.stable_prefix
    # The differing date lines went to the (differing) tail.
    assert a.dynamic_tail != b.dynamic_tail
    assert a.had_dynamic and b.had_dynamic


def test_stable_prefix_identical_across_trailing_uuid():
    base = SYSTEM_PROMPT + "\nRequest ID: {}"
    a = align(base.format("550e8400-e29b-41d4-a716-446655440000"))
    b = align(base.format("550e8400-e29b-41d4-a716-446655440999"))
    assert a.stable_prefix == b.stable_prefix


# --- Volatile-token detection -------------------------------------------------


def test_detects_iso_date():
    result = align("Stable line.\nUpdated 2026-06-09 today.")
    assert "Stable line." in result.stable_prefix
    assert "2026-06-09" in result.dynamic_tail


def test_detects_time():
    result = align("Stable line.\nAt 14:03:59 the job ran.")
    assert "14:03:59" in result.dynamic_tail


def test_detects_version():
    result = align("Stable line.\nRunning v3.2.0 of the tool.")
    assert "v3.2.0" in result.dynamic_tail


def test_detects_long_hex_hash():
    result = align("Stable line.\nCommit 0f85cf3f7405abc1234567890abcdef1234.")
    assert "0f85cf3f" in result.dynamic_tail


def test_detects_epoch_timestamp():
    result = align("Stable line.\nSince 1718000000 seconds.")
    assert "1718000000" in result.dynamic_tail


def test_short_hex_word_is_not_dynamic():
    # "cafe" / "deadbeef" are short hex words, not hashes -> stay in the prefix.
    result = align("The cafe served deadbeef stew.")
    assert result.dynamic_tail == ""
    assert "cafe" in result.stable_prefix


# --- No-dynamic identity ------------------------------------------------------


def test_no_dynamic_keeps_prefix_equal_to_normalized_text():
    result = align(SYSTEM_PROMPT)
    assert not result.had_dynamic
    assert result.dynamic_tail == ""
    assert result.stable_prefix == SYSTEM_PROMPT
    assert result.text == SYSTEM_PROMPT


# --- Whitespace normalization -------------------------------------------------


def test_trailing_whitespace_is_stripped():
    result = align("line one   \nline two\t\n")
    assert "line one   " not in result.text
    assert "line one" in result.stable_prefix


def test_blank_runs_are_collapsed():
    result = align("a\n\n\n\nb")
    assert "\n\n\n" not in result.stable_prefix
    assert result.stable_prefix == "a\n\nb"


def test_blank_runs_preserved_when_disabled():
    result = align("a\n\n\n\nb", config=CacheAlignerConfig(collapse_blank_runs=False))
    assert result.stable_prefix == "a\n\n\n\nb"


# --- Line preservation (reorder, never drop) ---------------------------------


def test_all_lines_are_preserved():
    text = "alpha\nbuilt 2026-06-09\nbeta\nid 550e8400-e29b-41d4-a716-446655440000\ngamma"
    result = align(text)
    # Every non-blank original line appears somewhere in the output.
    for line in ("alpha", "beta", "gamma", "2026-06-09", "550e8400"):
        assert line in result.text
    assert result.total_lines == 5
    assert result.moved_lines == 2


def test_stable_lines_keep_relative_order():
    result = align("first\nmid 2026-06-09\nsecond\nthird")
    prefix_lines = result.stable_prefix.splitlines()
    assert prefix_lines.index("first") < prefix_lines.index("second") < prefix_lines.index("third")


# --- Determinism + optional NER ----------------------------------------------


def test_alignment_is_deterministic():
    text = SYSTEM_PROMPT + "\nDate: 2026-06-09\nID: 550e8400-e29b-41d4-a716-446655440000"
    assert align(text).text == align(text).text


def test_ner_flag_degrades_gracefully_and_never_drops_below_regex():
    text = SYSTEM_PROMPT + "\nCurrent date: 2026-06-09"
    regex_only = align(text)
    # NER can only ADD dynamic lines; with spaCy absent it equals the regex result,
    # and either way it must not crash or move fewer lines.
    with_ner = align(text, config=CacheAlignerConfig(use_ner=True))
    assert with_ner.moved_lines >= regex_only.moved_lines


def test_non_string_input_is_coerced():
    result = align(12345)  # type: ignore[arg-type]
    assert isinstance(result.text, str)


def test_ner_pass_flags_entities_the_regex_misses(monkeypatch):
    """With a (fake) spaCy model present, the NER pass moves lines the regex can't.

    Exercises the optional NER seam end-to-end without depending on spaCy or its
    model being installed: a stub model flags any line containing 'tomorrow' as a
    DATE entity (the regex detector has no word-date rule), proving NER detections
    augment the regex ones.
    """
    import sys
    import types

    from nexus_context_compressor.transforms import cache_aligner as ca

    class _Ent:
        def __init__(self, label, start_char):
            self.label_ = label
            self.start_char = start_char

    class _Doc:
        def __init__(self, text):
            self.ents = [
                _Ent("DATE", idx) for idx in _find_all(text, "tomorrow")
            ]

    def _find_all(haystack, needle):
        start = 0
        while (i := haystack.find(needle, start)) != -1:
            yield i
            start = i + 1

    fake_nlp = lambda text: _Doc(text)  # noqa: E731 - test stub
    fake_spacy = types.ModuleType("spacy")
    fake_spacy.load = lambda name: fake_nlp  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "spacy", fake_spacy)

    text = "Stable rule.\nShip it tomorrow please.\nAnother stable rule."
    result = ca.align(text, config=CacheAlignerConfig(use_ner=True))
    assert "tomorrow" in result.dynamic_tail
    assert "Stable rule." in result.stable_prefix


def test_ner_load_failure_degrades_to_regex(monkeypatch):
    """A spaCy present but with no loadable model degrades to regex-only, no crash."""
    import sys
    import types

    from nexus_context_compressor.transforms import cache_aligner as ca

    fake_spacy = types.ModuleType("spacy")

    def _boom(name):
        raise OSError("model 'en_core_web_sm' not found")

    fake_spacy.load = _boom  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "spacy", fake_spacy)

    text = "Stable rule.\nDate: 2026-06-09"
    result = ca.align(text, config=CacheAlignerConfig(use_ner=True))
    assert "2026-06-09" in result.dynamic_tail  # regex still works
