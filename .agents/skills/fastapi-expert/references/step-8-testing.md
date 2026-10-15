### Step 8: Testing

**Shared fixtures**:

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.db.base import Base
from app.dependencies import get_db
from app.main import create_app

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """Provide an async test client with overridden DB dependency."""
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
```

**Route tests**:

```python
# tests/test_users.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    response = await client.post("/users", json={
        "email": "test@example.com",
        "display_name": "Test User",
        "password": "Str0ngPass!",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "hashed_password" not in data     # Verify password is excluded
    assert "id" in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dupe@example.com",
        "display_name": "User One",
        "password": "Str0ngPass!",
    }
    await client.post("/users", json=payload)
    response = await client.post("/users", json={**payload, "display_name": "User Two"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_user_weak_password(client: AsyncClient):
    response = await client.post("/users", json={
        "email": "weak@example.com",
        "display_name": "Weak User",
        "password": "nodigits",
    })
    assert response.status_code == 422       # Validation error


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient):
    # Create 3 users
    for i in range(3):
        await client.post("/users", json={
            "email": f"user{i}@example.com",
            "display_name": f"User {i}",
            "password": "Str0ngPass!",
        })

    response = await client.get("/users", params={"page": 1, "page_size": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["total"] == 3
    assert data["has_next"] is True
```
