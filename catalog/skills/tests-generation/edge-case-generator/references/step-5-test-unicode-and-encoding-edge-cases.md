### Step 5: Test Unicode and Encoding Edge Cases

**Python:**
```python
class TestUnicodeEdgeCases:
    """Unicode and encoding edge cases in string-processing functions."""

    def test_empty_string(self):
        assert normalize_name("") == ""

    def test_null_character_in_string(self):
        result = normalize_name("hello\x00world")
        assert "\x00" not in result

    def test_zero_width_space(self):
        result = normalize_name("hello\u200bworld")
        # Zero-width space should be stripped or handled
        assert result in ("helloworld", "hello world")

    def test_combining_characters(self):
        # e followed by combining acute accent vs precomposed e-acute
        assert normalize_name("e\u0301") == normalize_name("\u00e9")

    def test_surrogate_pairs(self):
        # Emoji that requires surrogate pairs in UTF-16
        result = normalize_name("\U0001f600")  # grinning face
        assert isinstance(result, str)

    def test_right_to_left_override(self):
        result = normalize_name("\u202ehello")
        # RTL override character should be stripped
        assert "\u202e" not in result

    def test_very_long_unicode_string(self):
        long_str = "\u00e9" * 10_000
        result = normalize_name(long_str)
        assert len(result) <= 10_000

    def test_mixed_scripts(self):
        result = normalize_name("Hello\u4e16\u754c\u041f\u0440\u0438\u0432\u0435\u0442")
        assert isinstance(result, str)
```

**JavaScript:**
```javascript
describe("Unicode edge cases", () => {
  test("empty string input", () => {
    expect(normalizeName("")).toBe("");
  });

  test("null character in string", () => {
    const result = normalizeName("hello\x00world");
    expect(result).not.toContain("\x00");
  });

  test("emoji input (surrogate pair in UTF-16)", () => {
    const result = normalizeName("\uD83D\uDE00");
    expect(typeof result).toBe("string");
  });

  test("zero-width joiner sequences", () => {
    // Family emoji: multiple code points joined with ZWJ
    const family = "\u{1F468}\u200D\u{1F469}\u200D\u{1F467}";
    const result = normalizeName(family);
    expect(typeof result).toBe("string");
  });

  test("string with only whitespace variants", () => {
    const whitespace = "\t \n \r \u00A0 \u2003";
    const result = normalizeName(whitespace);
    expect(result.trim()).toBe("");
  });
});
```

**Java:**
```java
class UnicodeEdgeCasesTest {

    @Test
    void emptyStringInput() {
        assertEquals("", NameNormalizer.normalize(""));
    }

    @Test
    void nullCharacterInString() {
        String result = NameNormalizer.normalize("hello\0world");
        assertFalse(result.contains("\0"));
    }

    @Test
    void supplementaryPlaneCharacter() {
        // Emoji U+1F600 requires two chars in Java's UTF-16
        String emoji = "\uD83D\uDE00";
        String result = NameNormalizer.normalize(emoji);
        assertNotNull(result);
    }

    @Test
    void combiningCharacterNormalization() {
        // e + combining acute vs precomposed e-acute
        String decomposed = "e\u0301";
        String precomposed = "\u00E9";
        assertEquals(
                NameNormalizer.normalize(precomposed),
                NameNormalizer.normalize(decomposed)
        );
    }

    @Test
    void mixedScriptsInput() {
        String mixed = "Hello\u4E16\u754C\u041F\u0440\u0438\u0432\u0435\u0442";
        assertDoesNotThrow(() -> NameNormalizer.normalize(mixed));
    }
}
```
