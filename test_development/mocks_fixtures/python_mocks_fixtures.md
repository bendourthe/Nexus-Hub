# Python Mocks & Fixtures

## Objective
Design and implement effective mocking strategies and fixture management to isolate components, manage test data efficiently, control external dependencies, and create maintainable, fast-running tests.

## Output Directory Structure

All test outputs should be saved in organized directories:

```
tests/
└── mocks_fixtures/
    ├── test_files/
    ├── test_data/
    ├── test_reports/
    └── test_configs/
```

**Directory Setup**:
- Create `tests/` directory in repository root if it doesn't exist
- Create `tests/mocks_fixtures/` subdirectory for this testing phase
- All test files, data, reports, and configurations go in the phase-specific directory

**Expected Outputs**:
- `test_files/` - Actual test implementation files
- `test_data/` - Test fixtures, mock data, sample inputs
- `test_reports/` - Test execution reports, coverage reports, performance results
- `test_configs/` - Framework configurations, test runner settings

## Implementation Checklist

### Fixture Setup
- [ ] Fixture scopes defined appropriately (function/class/module/session)
- [ ] Fixture dependencies organized logically
- [ ] Fixture factories created for flexible data generation
- [ ] Teardown and cleanup implemented
- [ ] Fixtures documented with clear purposes

### Mocking Strategy
- [ ] External dependencies identified for mocking
- [ ] Mocking approach chosen (mock vs stub vs fake)
- [ ] Mock objects configured correctly
- [ ] Assertion methods used appropriately
- [ ] Over-mocking avoided

### Test Data Management
- [ ] Test data factories implemented
- [ ] Realistic test data patterns established
- [ ] Data builders for complex objects created
- [ ] Test data isolated per test
- [ ] Data cleanup automated

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Mocks & Fixtures Implementation

Please implement comprehensive mocking and fixture strategies for this Python project following this protocol:

## Phase 1: Fixture Architecture Design

### Understanding Pytest Fixtures

Fixtures provide test data, setup, and teardown in a reusable way:

**Basic Fixture**:
```python
import pytest

@pytest.fixture
def user_data():
    """Provide sample user data for tests."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "age": 25
    }

# Usage in test
def test_user_creation(user_data):
    """Test user creation with fixture data."""
    user = create_user(**user_data)
    assert user.username == user_data["username"]
```

### Fixture Scopes

Choose appropriate scope for efficiency and isolation:

**1. Function Scope (Default)** - New fixture per test:
```python
@pytest.fixture  # scope="function" is default
def clean_database():
    """Fresh database for each test."""
    db = Database()
    db.create_tables()
    yield db
    db.drop_tables()

# Each test gets fresh database
def test_create_user(clean_database):
    clean_database.insert_user("alice")
    assert clean_database.count_users() == 1

def test_delete_user(clean_database):
    # Fresh database, no users from previous test
    assert clean_database.count_users() == 0
```

**2. Class Scope** - Shared within test class:
```python
@pytest.fixture(scope="class")
def database_connection():
    """Database connection shared by class tests."""
    conn = Database.connect()
    yield conn
    conn.close()

class TestUserOperations:
    """Tests sharing database connection."""

    def test_create_user(self, database_connection):
        # Uses same connection as other tests in class
        database_connection.execute("INSERT INTO users ...")

    def test_query_user(self, database_connection):
        # Same connection, can see data from test_create_user
        result = database_connection.execute("SELECT * FROM users")
```

**3. Module Scope** - Shared within test file:
```python
@pytest.fixture(scope="module")
def api_client():
    """API client for entire test module."""
    client = APIClient()
    client.authenticate()
    yield client
    client.logout()

# All tests in file share same client
def test_get_users(api_client):
    response = api_client.get("/users")

def test_create_user(api_client):
    response = api_client.post("/users", data={"name": "alice"})
```

**4. Session Scope** - Once per entire test session:
```python
@pytest.fixture(scope="session")
def docker_services():
    """Start Docker containers once for all tests."""
    containers = DockerCompose.start()
    yield containers
    DockerCompose.stop()

@pytest.fixture(scope="session")
def database_schema():
    """Create schema once, used by all tests."""
    db = Database()
    db.create_schema()
    yield db
    # Schema persists for all tests, cleanup at end
```

### Fixture Composition

Build complex fixtures from simpler ones:

```python
@pytest.fixture
def database():
    """Base database connection."""
    db = Database.connect("test_db")
    yield db
    db.close()

@pytest.fixture
def database_with_schema(database):
    """Database with schema created."""
    database.create_schema()
    yield database
    database.drop_schema()

@pytest.fixture
def database_with_test_data(database_with_schema):
    """Database with schema and test data."""
    database_with_schema.insert_test_data()
    yield database_with_schema
    database_with_schema.clear_data()

# Use the most appropriate fixture
def test_query_users(database_with_test_data):
    """Test with full database setup."""
    users = database_with_test_data.query("SELECT * FROM users")
    assert len(users) > 0
```

### Fixture Factories

Create factories for flexible test data generation:

```python
@pytest.fixture
def user_factory(database):
    """Factory for creating test users."""
    created_users = []

    def _create_user(username=None, email=None, **kwargs):
        """Create user with custom or default values."""
        user_id = len(created_users) + 1
        user = {
            "id": user_id,
            "username": username or f"user_{user_id}",
            "email": email or f"user{user_id}@test.com",
            **kwargs
        }
        database.insert_user(user)
        created_users.append(user)
        return user

    yield _create_user

    # Cleanup - delete all created users
    for user in created_users:
        database.delete_user(user["id"])

# Usage - create users with custom data
def test_user_relationships(user_factory):
    alice = user_factory(username="alice", age=25)
    bob = user_factory(username="bob", age=30)
    charlie = user_factory()  # Uses defaults

    assert alice["username"] == "alice"
    assert bob["age"] == 30
    assert charlie["username"] == "user_3"
```

### Parametrized Fixtures

Create multiple fixture variations:

```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def database(request):
    """Test with multiple database backends."""
    db_type = request.param
    db = Database.connect(db_type)
    yield db
    db.close()

# This test runs 3 times, once for each database type
def test_user_creation(database):
    database.create_user("alice")
    assert database.get_user("alice") is not None
```

### Auto-Use Fixtures

Fixtures that run automatically without explicit parameter:

```python
@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment before each test."""
    os.environ.clear()
    os.environ["ENV"] = "test"
    yield
    # Cleanup after test

# No need to pass fixture as parameter
def test_environment_variable():
    assert os.environ["ENV"] == "test"
```

## Phase 2: Mocking Strategies

### Understanding unittest.mock

Python's unittest.mock provides tools for replacing parts of your system during tests:

**Mock Objects**:
```python
from unittest.mock import Mock, MagicMock, patch

# Create a mock object
mock_database = Mock()

# Configure return value
mock_database.get_user.return_value = {"id": 1, "name": "alice"}

# Use in test
result = mock_database.get_user(1)
assert result["name"] == "alice"

# Verify it was called
mock_database.get_user.assert_called_once_with(1)
```

### When to Mock vs Use Real Objects

**Use Mocks For**:
- External APIs and services
- Slow operations (file I/O, network calls)
- Non-deterministic behavior (random, time)
- Testing error conditions
- Isolating unit tests

**Use Real Objects For**:
- Pure functions and simple logic
- Integration tests
- Critical paths requiring confidence
- When mocking adds more complexity than value

```python
# GOOD - Mock external API
def test_fetch_user_data(mock_api):
    """Mock external API for fast, reliable test."""
    mock_api.get.return_value = {"id": 1, "name": "alice"}
    result = fetch_user_from_api(1)
    assert result["name"] == "alice"

# GOOD - Use real object for simple logic
def test_calculate_total():
    """No mocking needed for pure function."""
    items = [10, 20, 30]
    assert calculate_total(items) == 60

# BAD - Over-mocking simple logic
def test_calculate_total(mock_sum):
    """Unnecessary mock adds complexity."""
    mock_sum.return_value = 60
    items = [10, 20, 30]
    assert calculate_total(items) == mock_sum.return_value
```

### Mock Configuration

**Return Values**:
```python
# Simple return value
mock_db.get_user.return_value = {"id": 1, "name": "alice"}

# Side effects - different returns per call
mock_api.fetch.side_effect = [
    {"status": "pending"},
    {"status": "complete"}
]
assert mock_api.fetch()["status"] == "pending"
assert mock_api.fetch()["status"] == "complete"

# Raise exception
mock_db.connect.side_effect = ConnectionError("Database unavailable")
with pytest.raises(ConnectionError):
    mock_db.connect()

# Callable side effect for complex logic
def custom_behavior(user_id):
    if user_id == 1:
        return {"name": "alice"}
    raise ValueError("User not found")

mock_db.get_user.side_effect = custom_behavior
```

**Spec and Spec_set**:
```python
from myapp.database import Database

# Mock with spec - only allows actual methods
mock_db = Mock(spec=Database)
mock_db.get_user()  # OK - real method
mock_db.fake_method()  # Raises AttributeError

# Spec_set - prevents setting non-existent attributes
mock_db = Mock(spec_set=Database)
mock_db.real_attribute = "value"  # OK
mock_db.fake_attribute = "value"  # Raises AttributeError
```

### Patching

Replace objects during test execution:

**Function Patching**:
```python
# myapp/service.py
import requests

def get_weather(city):
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()

# tests/test_service.py
from unittest.mock import patch
import myapp.service

@patch('myapp.service.requests.get')
def test_get_weather(mock_get):
    """Patch requests.get in service module."""
    mock_get.return_value.json.return_value = {"temp": 72}

    result = myapp.service.get_weather("Boston")

    assert result["temp"] == 72
    mock_get.assert_called_once_with("https://api.weather.com/Boston")
```

**Class Patching**:
```python
# myapp/repository.py
from myapp.database import Database

class UserRepository:
    def __init__(self):
        self.db = Database()

    def get_user(self, user_id):
        return self.db.query(f"SELECT * FROM users WHERE id={user_id}")

# tests/test_repository.py
from unittest.mock import patch, Mock

@patch('myapp.repository.Database')
def test_user_repository(mock_database_class):
    """Patch Database class."""
    # Configure the mock instance
    mock_db_instance = Mock()
    mock_db_instance.query.return_value = {"id": 1, "name": "alice"}
    mock_database_class.return_value = mock_db_instance

    repo = UserRepository()
    user = repo.get_user(1)

    assert user["name"] == "alice"
    mock_db_instance.query.assert_called_once()
```

**Context Manager Patching**:
```python
def test_with_patch_context():
    """Patch within context manager."""
    with patch('myapp.service.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {"temp": 72}
        result = get_weather("Boston")
        assert result["temp"] == 72
    # Patch removed after context
```

**Patch Object**:
```python
import myapp.service

def test_patch_object():
    """Patch specific object attribute."""
    with patch.object(myapp.service, 'API_KEY', 'test_key'):
        # API_KEY is temporarily 'test_key'
        assert myapp.service.API_KEY == 'test_key'
    # Original value restored
```

**Multiple Patches**:
```python
@patch('myapp.email.send_email')
@patch('myapp.database.Database')
def test_user_registration(mock_database, mock_send_email):
    """Multiple patches applied in reverse order."""
    mock_db_instance = Mock()
    mock_database.return_value = mock_db_instance

    register_user("alice", "alice@example.com")

    mock_db_instance.insert_user.assert_called_once()
    mock_send_email.assert_called_once()
```

### Pytest-Mock Plugin

Simpler syntax with pytest-mock:

```bash
pip install pytest-mock
```

```python
def test_with_mocker(mocker):
    """Use mocker fixture from pytest-mock."""
    # Patch with mocker
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.json.return_value = {"temp": 72}

    result = get_weather("Boston")
    assert result["temp"] == 72

    # Spy - wrap real function
    spy = mocker.spy(math, 'sqrt')
    result = math.sqrt(16)
    assert result == 4
    spy.assert_called_once_with(16)
```

### Mock Assertions

Verify mock interactions:

```python
mock_db = Mock()

# Call mock
mock_db.get_user(1)
mock_db.get_user(2)
mock_db.delete_user(3)

# Assertion methods
mock_db.get_user.assert_called()  # Called at least once
mock_db.get_user.assert_called_once()  # Called exactly once (FAILS - called twice)
mock_db.get_user.assert_called_with(2)  # Last call was with arg 2
mock_db.get_user.assert_called_once_with(1)  # Called once with arg 1 (FAILS)
mock_db.update_user.assert_not_called()  # Never called

# Check call count
assert mock_db.get_user.call_count == 2

# Check call arguments
calls = mock_db.get_user.call_args_list
assert calls[0][0][0] == 1  # First call, first arg
assert calls[1][0][0] == 2  # Second call, first arg

# Any call with argument
mock_db.get_user.assert_any_call(1)  # Was called with 1 at some point
```

## Phase 3: Mocking External Dependencies

### Mocking APIs and HTTP Requests

**Using responses library**:
```bash
pip install responses
```

```python
import responses
import requests

@responses.activate
def test_api_call():
    """Mock HTTP responses."""
    # Register mock response
    responses.add(
        responses.GET,
        "https://api.example.com/users/1",
        json={"id": 1, "name": "alice"},
        status=200
    )

    # Make real request - gets mocked response
    response = requests.get("https://api.example.com/users/1")

    assert response.json()["name"] == "alice"
    assert len(responses.calls) == 1
```

**Using requests-mock**:
```bash
pip install requests-mock
```

```python
import requests_mock

def test_api_with_requests_mock():
    """Alternative HTTP mocking library."""
    with requests_mock.Mocker() as m:
        m.get("https://api.example.com/users/1", json={"name": "alice"})

        response = requests.get("https://api.example.com/users/1")
        assert response.json()["name"] == "alice"
```

### Mocking Databases

**Option 1: In-Memory SQLite**:
```python
@pytest.fixture
def in_memory_db():
    """Use SQLite in-memory for fast tests."""
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    # Create schema
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

def test_user_creation(in_memory_db):
    """Test with real database, but in-memory."""
    session = Session(in_memory_db)
    user = User(name="alice")
    session.add(user)
    session.commit()
    assert session.query(User).count() == 1
```

**Option 2: Mock Database Connections**:
```python
def test_user_query(mocker):
    """Mock database for unit test."""
    mock_db = mocker.patch('myapp.database.get_connection')
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = [
        (1, "alice", "alice@example.com"),
        (2, "bob", "bob@example.com")
    ]
    mock_db.return_value.cursor.return_value = mock_cursor

    users = get_all_users()
    assert len(users) == 2
```

### Mocking File System

```python
from unittest.mock import mock_open, patch

def test_read_config(mocker):
    """Mock file reading."""
    mock_file_content = "setting=value\n"
    mocker.patch('builtins.open', mock_open(read_data=mock_file_content))

    config = read_config("config.txt")
    assert config["setting"] == "value"

def test_write_log(mocker):
    """Mock file writing."""
    mock_file = mock_open()
    mocker.patch('builtins.open', mock_file)

    write_log("test message")

    mock_file.assert_called_once_with("app.log", "a")
    mock_file().write.assert_called_once_with("test message\n")
```

### Mocking Time and Dates

```python
from unittest.mock import patch
from datetime import datetime

@patch('myapp.utils.datetime')
def test_timestamp_generation(mock_datetime):
    """Mock datetime for consistent testing."""
    mock_now = datetime(2024, 1, 15, 12, 0, 0)
    mock_datetime.now.return_value = mock_now

    timestamp = generate_timestamp()
    assert timestamp == "2024-01-15T12:00:00"

# Using freezegun library
from freezegun import freeze_time

@freeze_time("2024-01-15 12:00:00")
def test_with_frozen_time():
    """Time is frozen during test."""
    assert datetime.now().hour == 12
    # Time doesn't advance
```

### Mocking Environment Variables

```python
def test_with_env_var(mocker):
    """Mock environment variables."""
    mocker.patch.dict('os.environ', {'API_KEY': 'test_key_123'})

    api_key = get_api_key_from_env()
    assert api_key == 'test_key_123'
```

## Phase 4: Test Data Factories

### Factory Pattern for Test Data

```python
# tests/factories.py
"""Test data factories."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UserFactory:
    """Factory for creating test users."""

    _id_counter = 0

    @classmethod
    def create(
        cls,
        username: Optional[str] = None,
        email: Optional[str] = None,
        age: Optional[int] = None,
        **kwargs
    ):
        """Create user with default or custom values."""
        cls._id_counter += 1
        return {
            "id": cls._id_counter,
            "username": username or f"user_{cls._id_counter}",
            "email": email or f"user{cls._id_counter}@test.com",
            "age": age or 25,
            "created_at": datetime.now(),
            **kwargs
        }

    @classmethod
    def create_batch(cls, count: int, **kwargs):
        """Create multiple users."""
        return [cls.create(**kwargs) for _ in range(count)]

    @classmethod
    def reset(cls):
        """Reset ID counter."""
        cls._id_counter = 0

# Usage
def test_user_creation():
    user = UserFactory.create(username="alice")
    assert user["username"] == "alice"
    assert user["email"] == "user1@test.com"

def test_multiple_users():
    users = UserFactory.create_batch(5)
    assert len(users) == 5
    assert users[0]["username"] == "user_1"
```

### Builder Pattern for Complex Objects

```python
class OrderBuilder:
    """Builder for creating test orders."""

    def __init__(self):
        self._order = {
            "id": None,
            "user_id": None,
            "items": [],
            "status": "pending",
            "total": 0.0
        }

    def with_id(self, order_id):
        """Set order ID."""
        self._order["id"] = order_id
        return self

    def for_user(self, user_id):
        """Set user ID."""
        self._order["user_id"] = user_id
        return self

    def add_item(self, product_id, quantity, price):
        """Add item to order."""
        self._order["items"].append({
            "product_id": product_id,
            "quantity": quantity,
            "price": price
        })
        self._order["total"] += quantity * price
        return self

    def with_status(self, status):
        """Set order status."""
        self._order["status"] = status
        return self

    def build(self):
        """Return built order."""
        return self._order

# Usage
def test_order_processing():
    order = (OrderBuilder()
             .with_id(1)
             .for_user(100)
             .add_item(product_id=1, quantity=2, price=10.0)
             .add_item(product_id=2, quantity=1, price=15.0)
             .with_status("confirmed")
             .build())

    assert order["total"] == 35.0
    assert len(order["items"]) == 2
```

### Using factory_boy Library

```bash
pip install factory-boy
```

```python
import factory
from myapp.models import User

class UserFactory(factory.Factory):
    """Factory for User model."""

    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    age = 25
    is_active = True
    created_at = factory.LazyFunction(datetime.now)

# Usage
def test_user_factory():
    user1 = UserFactory()
    user2 = UserFactory(username="alice")
    users = UserFactory.create_batch(5)

    assert user1.username == "user_0"
    assert user2.username == "alice"
    assert len(users) == 5
```

## Output Format

Please provide a comprehensive mocks and fixtures implementation with the following structure:

### Fixture Architecture
**Session-Scoped Fixtures** (tests/conftest.py):
- [fixture_name]: [purpose, setup, teardown]

**Module-Scoped Fixtures**:
- [fixture_name]: [purpose, when to use]

**Function-Scoped Fixtures**:
- [fixture_name]: [purpose, frequency of use]

**Fixture Factories**:
- [factory_name]: [creates what, customization options]

### Mocking Strategy
**External Dependencies to Mock**:
| Dependency | Mocking Approach | Reason |
|------------|------------------|--------|
| [API/Service] | [mock/stub/fake] | [justification] |

**Mock Configurations**:
```python
# Example mock setup
@pytest.fixture
def mock_api_client(mocker):
    mock = mocker.patch('myapp.api.Client')
    mock.return_value.get.return_value = {"status": "ok"}
    return mock
```

### Test Data Factories
**Factory Classes**:
- UserFactory: [customization options]
- OrderFactory: [customization options]
- ProductFactory: [customization options]

**Builder Classes**:
- [builder_name]: [purpose, fluent interface methods]

### Usage Examples
```python
# Example test using fixtures and mocks
def test_user_registration(user_factory, mock_email_service):
    # Arrange
    user_data = user_factory(username="alice")
    mock_email_service.send.return_value = True

    # Act
    result = register_user(user_data)

    # Assert
    assert result.success
    mock_email_service.send.assert_called_once()
```

### Best Practices Implemented
- [ ] Fixtures use appropriate scopes for efficiency
- [ ] Mocks are used for external dependencies only
- [ ] Test data factories provide flexible data creation
- [ ] Fixture composition follows logical hierarchy
- [ ] Mock assertions verify behavior, not implementation
- [ ] Teardown ensures clean state between tests

### Common Pitfalls Avoided
- Over-mocking simple logic
- Fixture scope too broad (causing test coupling)
- Mock leaking between tests
- Complex fixture dependencies
- Testing mock behavior instead of real code

### Next Steps
- [ ] Implement remaining fixtures for integration tests
- [ ] Add factories for all domain models
- [ ] Document fixture usage for team
- [ ] Review and optimize fixture scopes
- [ ] Set up shared mock configurations
~~~

## Output Format

The AI assistant should deliver:

1. **Comprehensive fixture library** organized by scope
2. **Mock configurations** for external dependencies
3. **Test data factories** for domain objects
4. **Builder patterns** for complex test data
5. **Usage documentation** with examples
6. **Best practices guide** for the team
7. **Fixture and mock catalog** for easy reference
