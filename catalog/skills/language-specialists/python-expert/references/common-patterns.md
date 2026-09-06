## Common Patterns

### Pattern 1: Repository Pattern with Protocol

```python
from __future__ import annotations

from typing import Protocol

class UserRepository(Protocol):
    def get(self, user_id: int) -> User | None: ...
    def save(self, user: User) -> User: ...
    def delete(self, user_id: int) -> bool: ...

class PostgresUserRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def get(self, user_id: int) -> User | None:
        row = await self._conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return User(**dict(row)) if row else None

    async def save(self, user: User) -> User:
        row = await self._conn.fetchrow(
            "INSERT INTO users (name, email) VALUES ($1, $2) RETURNING *",
            user.name,
            user.email,
        )
        return User(**dict(row))

    async def delete(self, user_id: int) -> bool:
        result = await self._conn.execute(
            "DELETE FROM users WHERE id = $1", user_id
        )
        return result == "DELETE 1"

class InMemoryUserRepository:
    """Test double that satisfies the same Protocol."""

    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._next_id = 1

    def get(self, user_id: int) -> User | None:
        return self._store.get(user_id)

    def save(self, user: User) -> User:
        user.id = self._next_id
        self._store[self._next_id] = user
        self._next_id += 1
        return user

    def delete(self, user_id: int) -> bool:
        return self._store.pop(user_id, None) is not None
```

### Pattern 2: Retry with Exponential Backoff

```python
from __future__ import annotations

import asyncio
import logging
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)

async def retry(
    func,
    *args,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable: tuple[type[Exception], ...] = (ConnectionError, TimeoutError),
) -> T:
    """Retry an async callable with exponential backoff."""
    last_exc: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await func(*args)
        except retryable as exc:
            last_exc = exc
            if attempt == max_attempts:
                break
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                "Attempt %d/%d failed (%s), retrying in %.1fs",
                attempt,
                max_attempts,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]

# Usage
result = await retry(fetch_url, session, url, max_attempts=5)
```
