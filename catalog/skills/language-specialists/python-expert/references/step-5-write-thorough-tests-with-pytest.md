### Step 5: Write Thorough Tests with pytest

**Basic Test Structure and Parametrize**:

```python
import pytest
from myapp.calculator import add, divide

def test_add_positive_numbers() -> None:
    assert add(2, 3) == 5

def test_divide_by_zero_raises() -> None:
    with pytest.raises(ZeroDivisionError, match="division by zero"):
        divide(10, 0)

@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 5),
        (-1, -1, -2),
        (0, 0, 0),
        (-1, 1, 0),
        (100, 200, 300),
    ],
    ids=["positive", "negative", "zeros", "mixed", "large"],
)
def test_add_parametrized(a: int, b: int, expected: int) -> None:
    assert add(a, b) == expected
```

**Fixtures and conftest.py**:

```python
# conftest.py
import pytest
from myapp.database import Database

@pytest.fixture
def db(tmp_path: object) -> Database:
    """Create a fresh test database for each test."""
    db = Database(f"sqlite:///{tmp_path}/test.db")
    db.create_tables()
    yield db
    db.close()

@pytest.fixture
def sample_user(db: Database) -> User:
    """Insert and return a sample user."""
    return db.create_user(name="Alice", email="alice@example.com")

# test_users.py
def test_user_creation(db: Database) -> None:
    user = db.create_user(name="Bob", email="bob@example.com")
    assert user.name == "Bob"
    assert user.id is not None

def test_user_lookup(db: Database, sample_user: User) -> None:
    found = db.get_user(sample_user.id)
    assert found is not None
    assert found.email == "alice@example.com"
```

**Monkeypatch for Isolation**:

```python
def test_config_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("APP_DEBUG", "true")

    settings = AppSettings()
    assert settings.database_url == "sqlite:///test.db"
    assert settings.debug is True

def test_fetch_retries_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    def mock_get(url: str, timeout: int = 30) -> object:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("network error")
        return MockResponse(status_code=200, body="ok")

    monkeypatch.setattr("myapp.client.requests.get", mock_get)

    result = fetch_with_retry("https://api.example.com/data")
    assert result == "ok"
    assert call_count == 3
```

**Async Test Support**:

```python
import pytest

@pytest.mark.asyncio
async def test_async_fetch() -> None:
    async with aiohttp.ClientSession() as session:
        result = await fetch_url(session, "https://httpbin.org/get")
        assert len(result) > 0

# pytest.ini or pyproject.toml:
# [tool.pytest.ini_options]
# asyncio_mode = "auto"
```

**Coverage Configuration** (pyproject.toml):

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--strict-markers -q"

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__",
]
```
