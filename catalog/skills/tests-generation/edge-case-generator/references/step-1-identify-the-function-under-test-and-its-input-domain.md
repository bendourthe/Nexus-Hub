### Step 1: Identify the Function Under Test and Its Input Domain

Examine the function signature, documentation, and implementation to catalogue every parameter, its type, its valid range, and any implicit constraints.

**Python example (target function):**
```python
def paginate_results(items: list, page: int, page_size: int) -> dict:
    """Return a page of results with metadata.

    Args:
        items: The full list of items to paginate.
        page: 1-based page number.
        page_size: Number of items per page (1-100).

    Returns:
        Dict with keys: 'data', 'page', 'page_size', 'total_pages', 'total_items'.

    Raises:
        ValueError: If page < 1 or page_size not in [1, 100].
    """
    if page < 1:
        raise ValueError("page must be >= 1")
    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")
    start = (page - 1) * page_size
    end = start + page_size
    total_pages = max(1, -(-len(items) // page_size))
    return {
        "data": items[start:end],
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "total_items": len(items),
    }
```
