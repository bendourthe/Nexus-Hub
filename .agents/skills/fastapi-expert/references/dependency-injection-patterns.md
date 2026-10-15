# FastAPI Dependency Injection Patterns Reference

Quick-lookup guide for FastAPI dependency injection, including database sessions, auth, pagination, and testing. Use alongside the main fastapi-expert skill when designing API dependencies.

## Dependency Scoping Guide

| Scope | Lifetime | Use When | Example |
|-------|----------|----------|---------|
| Function (default) | Per request | Most dependencies; DB sessions, auth | `Depends(get_db)` |
| `use_cache=False` | Per injection point | Need fresh instance each time | `Depends(get_timestamp, use_cache=False)` |
| App-level (lifespan) | Application lifetime | Connection pools, ML models | `app.state.pool` |

## Database Session Dependency

```python
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## Authentication Dependencies (Layered)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = verify_jwt(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = await db.get(User, payload["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def require_role(*roles: str):
    """Factory that returns a dependency checking for specific roles."""
    async def check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return user
    return check_role


# Usage
@app.get("/admin/users")
async def list_users(user: User = Depends(require_role("admin", "superadmin"))):
    ...
```

## Pagination Dependency

```python
from dataclasses import dataclass
from fastapi import Query


@dataclass
class Pagination:
    page: int
    per_page: int
    offset: int


def get_pagination(
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> Pagination:
    return Pagination(page=page, per_page=per_page, offset=(page - 1) * per_page)


@app.get("/items")
async def list_items(
    pagination: Pagination = Depends(get_pagination),
    db: AsyncSession = Depends(get_db),
):
    query = select(Item).offset(pagination.offset).limit(pagination.per_page)
    result = await db.execute(query)
    return result.scalars().all()
```

## Testing with Dependency Overrides

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_db, get_current_user


@pytest.fixture
async def client():
    """Create test client with overridden dependencies."""

    async def override_db():
        async with test_session() as session:
            yield session

    async def override_auth():
        return User(id="test-user", role="admin")

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_auth

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_list_items(client: AsyncClient):
    response = await client.get("/items?page=1&per_page=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Common Patterns Quick Reference

| Pattern | Implementation | Notes |
|---------|---------------|-------|
| Shared config | `Depends(get_settings)` with `@lru_cache` | Cached across requests |
| Rate limiting | Class-based dependency with `__call__` | Use Redis for distributed |
| Request ID | Middleware + `ContextVar` | Propagate to logs |
| Feature flags | `Depends(get_feature_flags)` | Cache with TTL |
| Tenant isolation | Extract tenant from JWT/header | Filter all queries |
