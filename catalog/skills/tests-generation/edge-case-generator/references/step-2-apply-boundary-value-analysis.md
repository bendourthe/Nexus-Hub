### Step 2: Apply Boundary Value Analysis

Generate tests at each boundary for every parameter.

**Python (pytest):**
```python
import pytest
from pagination import paginate_results


class TestPaginateResultsBoundaryValues:
    """Boundary value analysis for paginate_results."""

    # --- page parameter boundaries ---

    def test_page_minimum_valid(self):
        result = paginate_results(list(range(50)), page=1, page_size=10)
        assert result["page"] == 1
        assert result["data"] == list(range(10))

    def test_page_below_minimum_raises(self):
        with pytest.raises(ValueError, match="page must be >= 1"):
            paginate_results(list(range(50)), page=0, page_size=10)

    def test_page_negative_raises(self):
        with pytest.raises(ValueError, match="page must be >= 1"):
            paginate_results(list(range(50)), page=-1, page_size=10)

    def test_page_beyond_last_returns_empty(self):
        result = paginate_results(list(range(10)), page=100, page_size=10)
        assert result["data"] == []

    # --- page_size parameter boundaries ---

    def test_page_size_minimum_valid(self):
        result = paginate_results(list(range(5)), page=1, page_size=1)
        assert result["data"] == [0]
        assert result["total_pages"] == 5

    def test_page_size_maximum_valid(self):
        result = paginate_results(list(range(200)), page=1, page_size=100)
        assert len(result["data"]) == 100

    def test_page_size_below_minimum_raises(self):
        with pytest.raises(ValueError, match="page_size must be between 1 and 100"):
            paginate_results(list(range(10)), page=1, page_size=0)

    def test_page_size_above_maximum_raises(self):
        with pytest.raises(ValueError, match="page_size must be between 1 and 100"):
            paginate_results(list(range(10)), page=1, page_size=101)

    # --- items parameter boundaries ---

    def test_empty_items_list(self):
        result = paginate_results([], page=1, page_size=10)
        assert result["data"] == []
        assert result["total_items"] == 0
        assert result["total_pages"] == 1

    def test_single_item_list(self):
        result = paginate_results(["only"], page=1, page_size=10)
        assert result["data"] == ["only"]
        assert result["total_items"] == 1

    def test_items_exactly_fill_one_page(self):
        result = paginate_results(list(range(10)), page=1, page_size=10)
        assert len(result["data"]) == 10
        assert result["total_pages"] == 1

    def test_items_one_more_than_page_size(self):
        result = paginate_results(list(range(11)), page=2, page_size=10)
        assert result["data"] == [10]
        assert result["total_pages"] == 2
```

**JavaScript (Jest):**
```javascript
const { paginateResults } = require("./pagination");

describe("paginateResults boundary values", () => {
  // --- page parameter boundaries ---

  test("page=1 returns the first page", () => {
    const result = paginateResults(Array.from({ length: 50 }, (_, i) => i), 1, 10);
    expect(result.page).toBe(1);
    expect(result.data).toEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
  });

  test("page=0 throws an error", () => {
    expect(() => paginateResults([1, 2, 3], 0, 10)).toThrow("page must be >= 1");
  });

  test("page=-1 throws an error", () => {
    expect(() => paginateResults([1, 2, 3], -1, 10)).toThrow("page must be >= 1");
  });

  test("page beyond last page returns empty data", () => {
    const result = paginateResults([1, 2, 3], 100, 10);
    expect(result.data).toEqual([]);
  });

  // --- page_size parameter boundaries ---

  test("page_size=1 returns one item per page", () => {
    const result = paginateResults([10, 20, 30], 1, 1);
    expect(result.data).toEqual([10]);
    expect(result.totalPages).toBe(3);
  });

  test("page_size=100 is the maximum allowed", () => {
    const items = Array.from({ length: 200 }, (_, i) => i);
    const result = paginateResults(items, 1, 100);
    expect(result.data).toHaveLength(100);
  });

  test("page_size=0 throws an error", () => {
    expect(() => paginateResults([1], 1, 0)).toThrow();
  });

  test("page_size=101 throws an error", () => {
    expect(() => paginateResults([1], 1, 101)).toThrow();
  });

  // --- items parameter boundaries ---

  test("empty array returns empty data", () => {
    const result = paginateResults([], 1, 10);
    expect(result.data).toEqual([]);
    expect(result.totalItems).toBe(0);
  });

  test("single-element array", () => {
    const result = paginateResults(["only"], 1, 10);
    expect(result.data).toEqual(["only"]);
    expect(result.totalItems).toBe(1);
  });
});
```

**Java (JUnit 5):**
```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import static org.junit.jupiter.api.Assertions.*;

class PaginateResultsBoundaryTest {

    // --- page parameter boundaries ---

    @Test
    void page1ReturnsFirstPage() {
        var items = java.util.stream.IntStream.range(0, 50)
                .boxed().toList();
        var result = Paginator.paginate(items, 1, 10);
        assertEquals(1, result.getPage());
        assertEquals(10, result.getData().size());
    }

    @ParameterizedTest
    @ValueSource(ints = {0, -1, -100, Integer.MIN_VALUE})
    void pageBelowMinimumThrows(int invalidPage) {
        var items = java.util.List.of(1, 2, 3);
        assertThrows(IllegalArgumentException.class,
                () -> Paginator.paginate(items, invalidPage, 10));
    }

    @Test
    void pageBeyondLastReturnsEmptyData() {
        var items = java.util.List.of(1, 2, 3);
        var result = Paginator.paginate(items, 100, 10);
        assertTrue(result.getData().isEmpty());
    }

    // --- page_size parameter boundaries ---

    @Test
    void pageSizeOneReturnsOneItemPerPage() {
        var items = java.util.List.of(10, 20, 30);
        var result = Paginator.paginate(items, 1, 1);
        assertEquals(1, result.getData().size());
        assertEquals(3, result.getTotalPages());
    }

    @ParameterizedTest
    @ValueSource(ints = {0, -1, 101, 1000, Integer.MAX_VALUE})
    void pageSizeOutOfRangeThrows(int invalidSize) {
        var items = java.util.List.of(1, 2, 3);
        assertThrows(IllegalArgumentException.class,
                () -> Paginator.paginate(items, 1, invalidSize));
    }

    // --- items parameter boundaries ---

    @Test
    void emptyListReturnsEmptyData() {
        var result = Paginator.paginate(java.util.List.of(), 1, 10);
        assertTrue(result.getData().isEmpty());
        assertEquals(0, result.getTotalItems());
    }

    @Test
    void singleElementList() {
        var result = Paginator.paginate(java.util.List.of("only"), 1, 10);
        assertEquals(1, result.getData().size());
        assertEquals(1, result.getTotalItems());
    }
}
```
