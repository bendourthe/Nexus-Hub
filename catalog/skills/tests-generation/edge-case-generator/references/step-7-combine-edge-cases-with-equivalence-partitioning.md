### Step 7: Combine Edge Cases with Equivalence Partitioning

Use the category-partition method to generate meaningful combinations without testing every permutation.

**Python:**
```python
import pytest


class TestPaginateResultsCombinations:
    """Category-partition combinations for paginate_results."""

    @pytest.mark.parametrize(
        "items, page, page_size, expected_len",
        [
            # empty items + valid pagination
            ([], 1, 10, 0),
            # single item + first page + size=1
            ([42], 1, 1, 1),
            # many items + last page + size=1
            (list(range(100)), 100, 1, 1),
            # many items + first page + max size
            (list(range(200)), 1, 100, 100),
            # items exactly fill page
            (list(range(10)), 1, 10, 10),
            # items one short of filling second page
            (list(range(11)), 2, 10, 1),
        ],
    )
    def test_partition_combinations(self, items, page, page_size, expected_len):
        result = paginate_results(items, page, page_size)
        assert len(result["data"]) == expected_len

    @pytest.mark.parametrize(
        "page, page_size",
        [
            (0, 10),     # page below min
            (-1, 10),    # page negative
            (1, 0),      # size below min
            (1, 101),    # size above max
            (0, 0),      # both invalid
            (-1, 101),   # both invalid, opposite extremes
        ],
    )
    def test_invalid_combinations_raise(self, page, page_size):
        with pytest.raises(ValueError):
            paginate_results([1, 2, 3], page, page_size)
```
