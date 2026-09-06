### Step 5: Configure Fast Unit Tests

**Run quick smoke tests before committing:**

#### Python - Pytest Configuration

```ini
# pytest.ini
[pytest]
markers =
    quick: marks tests as quick (deselect with '-m "not quick"')
    slow: marks tests as slow

# Run only quick tests in pre-commit
addopts = -m quick --tb=short -x
```

**Mark tests**:

```python
import pytest

@pytest.mark.quick
def test_user_creation():
    """Quick test: user creation works."""
    user = User("test@example.com")
    assert user.email == "test@example.com"

@pytest.mark.slow
def test_database_migration():
    """Slow test: full database migration."""
    # This test takes 30 seconds, skip in pre-commit
    migrate_database()
    assert check_migration_complete()
```

#### JavaScript - Jest Configuration

```json
// package.json
{
  "scripts": {
    "test": "jest",
    "test:quick": "jest --testPathPattern=quick --bail --maxWorkers=2",
    "test:slow": "jest tests/slow/"
  }
}
```
