### Step 3: Apply Special Value Injection

Test with values from the special value catalogue that are relevant to each parameter type.

**Python:**
```python
class TestPaginateResultsSpecialValues:
    """Special value injection for paginate_results."""

    def test_page_max_int(self):
        import sys
        result = paginate_results([1, 2, 3], page=sys.maxsize, page_size=10)
        assert result["data"] == []

    def test_page_size_negative_raises(self):
        with pytest.raises(ValueError):
            paginate_results([1, 2, 3], page=1, page_size=-1)

    def test_items_contain_none_values(self):
        result = paginate_results([None, None, None], page=1, page_size=10)
        assert result["data"] == [None, None, None]

    def test_items_contain_mixed_types(self):
        mixed = [1, "two", 3.0, None, True, [], {}]
        result = paginate_results(mixed, page=1, page_size=10)
        assert result["data"] == mixed

    def test_items_contain_empty_strings(self):
        result = paginate_results(["", "", ""], page=1, page_size=2)
        assert result["data"] == ["", ""]

    def test_very_large_items_list(self):
        large = list(range(100_000))
        result = paginate_results(large, page=1, page_size=100)
        assert len(result["data"]) == 100
        assert result["total_items"] == 100_000

    def test_items_with_unicode(self):
        items = ["\u0000", "\uffff", "\U0001f600", "\u200b", "\u202e"]
        result = paginate_results(items, page=1, page_size=10)
        assert result["data"] == items

    def test_items_with_deeply_nested_structures(self):
        nested = [{"a": {"b": {"c": {"d": [1, 2, 3]}}}}]
        result = paginate_results(nested, page=1, page_size=10)
        assert result["data"] == nested
```

**JavaScript:**
```javascript
describe("paginateResults special values", () => {
  test("page = Number.MAX_SAFE_INTEGER returns empty data", () => {
    const result = paginateResults([1, 2, 3], Number.MAX_SAFE_INTEGER, 10);
    expect(result.data).toEqual([]);
  });

  test("page = NaN throws an error", () => {
    expect(() => paginateResults([1], NaN, 10)).toThrow();
  });

  test("page = Infinity throws an error", () => {
    expect(() => paginateResults([1], Infinity, 10)).toThrow();
  });

  test("page_size = 1.5 (non-integer) throws or truncates", () => {
    expect(() => paginateResults([1, 2, 3], 1, 1.5)).toThrow();
  });

  test("items containing undefined values", () => {
    const result = paginateResults([undefined, undefined], 1, 10);
    expect(result.data).toHaveLength(2);
  });

  test("items containing objects with circular references", () => {
    const obj = { name: "test" };
    obj.self = obj;
    // Should not throw during pagination (only during serialization)
    const result = paginateResults([obj], 1, 10);
    expect(result.data).toHaveLength(1);
  });

  test("string passed as page coercion", () => {
    // Depending on implementation, this should throw or be handled
    expect(() => paginateResults([1], "1", 10)).toThrow();
  });
});
```

**Java:**
```java
class PaginateResultsSpecialValuesTest {

    @Test
    void pageMaxIntReturnsEmptyData() {
        var items = java.util.List.of(1, 2, 3);
        var result = Paginator.paginate(items, Integer.MAX_VALUE, 10);
        assertTrue(result.getData().isEmpty());
    }

    @Test
    void nullItemsListThrowsNullPointerException() {
        assertThrows(NullPointerException.class,
                () -> Paginator.paginate(null, 1, 10));
    }

    @Test
    void itemsContainingNullElements() {
        var items = java.util.Arrays.asList(null, null, null);
        var result = Paginator.paginate(items, 1, 10);
        assertEquals(3, result.getData().size());
    }

    @Test
    void unmodifiableListAsInput() {
        var items = java.util.Collections.unmodifiableList(
                java.util.List.of(1, 2, 3));
        // Should work without attempting to modify the input
        var result = Paginator.paginate(items, 1, 10);
        assertEquals(3, result.getData().size());
    }

    @Test
    void concurrentModificationDuringPagination() {
        var items = new java.util.ArrayList<>(java.util.List.of(1, 2, 3, 4, 5));
        // Simulating concurrent modification risk
        assertDoesNotThrow(() -> Paginator.paginate(items, 1, 2));
    }
}
```
