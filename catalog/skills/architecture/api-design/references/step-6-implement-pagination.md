### Step 6: Implement Pagination

**Cursor-Based Pagination (recommended for most cases)**:

```python
# Encoding/decoding cursors
import base64, json

def encode_cursor(data: dict) -> str:
    return base64.urlsafe_b64encode(
        json.dumps(data).encode()
    ).decode()

def decode_cursor(cursor: str) -> dict:
    return json.loads(
        base64.urlsafe_b64decode(cursor.encode())
    )

# Query implementation
async def list_orders(
    status: str | None = None,
    cursor: str | None = None,
    limit: int = 20,
) -> dict:
    query = "SELECT * FROM orders"
    params = []
    conditions = []

    if status:
        conditions.append("status = %s")
        params.append(status)

    if cursor:
        decoded = decode_cursor(cursor)
        conditions.append("(created_at, id) < (%s, %s)")
        params.extend([decoded["created_at"], decoded["id"]])

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC, id DESC LIMIT %s"
    params.append(limit + 1)  # Fetch one extra to detect hasMore

    rows = await db.fetch(query, params)
    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = encode_cursor({
            "created_at": last["created_at"].isoformat(),
            "id": str(last["id"]),
        })

    return {
        "data": items,
        "pagination": {
            "nextCursor": next_cursor,
            "hasMore": has_more,
        },
    }
```
