### Step 5: Implement Tiered Test Execution in CI

**Python (pytest markers for tiered execution):**
```python
# conftest.py
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "tier0: lint and type checks")
    config.addinivalue_line("markers", "tier1: smoke tests (critical paths)")
    config.addinivalue_line("markers", "tier2: unit tests")
    config.addinivalue_line("markers", "tier3: integration tests")
    config.addinivalue_line("markers", "tier4: e2e tests")


# Usage in tests:
@pytest.mark.tier1
def test_health_check(client):
    """Smoke test: API is running and responding."""
    response = client.get("/health")
    assert response.status_code == 200


@pytest.mark.tier1
def test_login_basic(client):
    """Smoke test: basic login flow works."""
    response = client.post("/login", json={"email": "admin@test.com", "password": "test"})
    assert response.status_code == 200


@pytest.mark.tier2
def test_password_hashing():
    """Unit test: password hashing produces correct output."""
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)


@pytest.mark.tier3
def test_order_placement_with_database(db_session, client):
    """Integration test: full order placement flow."""
    response = client.post("/orders", json={"product_id": 1, "quantity": 2})
    assert response.status_code == 201
    order = db_session.query(Order).first()
    assert order is not None
```

**CI pipeline configuration (GitHub Actions):**
```yaml
# .github/workflows/test.yml
name: Tiered Tests
on: [push, pull_request]

jobs:
  tier0-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy src/

  tier1-smoke:
    needs: tier0-lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: pytest -m tier1 --timeout=30

  tier2-unit:
    needs: tier1-smoke
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: pytest -m tier2 --timeout=300

  tier3-integration:
    needs: tier2-unit
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
    steps:
      - uses: actions/checkout@v4
      - run: pip install -e ".[test]"
      - run: pytest -m tier3 --timeout=900
```

**JavaScript (Jest projects for tiered execution):**
```javascript
// jest.config.js
module.exports = {
  projects: [
    {
      displayName: "tier1-smoke",
      testMatch: ["<rootDir>/tests/smoke/**/*.test.js"],
      testTimeout: 10000,
    },
    {
      displayName: "tier2-unit",
      testMatch: ["<rootDir>/tests/unit/**/*.test.js"],
      testTimeout: 30000,
    },
    {
      displayName: "tier3-integration",
      testMatch: ["<rootDir>/tests/integration/**/*.test.js"],
      testTimeout: 60000,
    },
  ],
};

// Run specific tiers:
// npx jest --selectProjects tier1-smoke
// npx jest --selectProjects tier2-unit
```
