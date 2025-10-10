# Python Test Structure & Infrastructure

## Objective
Design and implement a robust test infrastructure with optimal framework configuration, logical directory organization, efficient fixture management, and reusable test utilities to support comprehensive testing practices.

## Output Directory Structure

All outputs should be saved in organized directories:

```
tests/test_structure/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Directory Setup**:

- Create `tests/test_structure/` directory in repository root if it doesn't exist

- All templates, assets, and exports go in the phase-specific directory

**Expected Outputs**:

- `templates/` - Reusable templates, example configurations, boilerplate scripts

- `assets/` - Images, diagrams, charts, supplementary files

- `exports/` - Final documentation files, reports, release artifacts


## Implementation Checklist

### Test Framework Setup
- [ ] Test framework selected (pytest recommended)
- [ ] Configuration files created (pytest.ini, pyproject.toml)
- [ ] Required plugins installed and configured
- [ ] Test discovery rules established
- [ ] Parallel execution configured

### Directory Structure
- [ ] Standard test layout implemented
- [ ] Test type separation (unit/integration/e2e) organized
- [ ] Naming conventions documented
- [ ] Resource directories created
- [ ] __init__.py files added where needed

### Fixture Infrastructure
- [ ] conftest.py hierarchy established
- [ ] Fixture scopes defined appropriately
- [ ] Fixture factories implemented
- [ ] Fixture documentation added
- [ ] Common fixtures centralized

### Test Utilities
- [ ] Common assertion helpers created
- [ ] Test data generators implemented
- [ ] Custom decorators defined
- [ ] Shared base classes established
- [ ] Helper documentation provided

## Prompt Template

Use the structured prompt below with your coding assistant:

~~~markdown
# Python Test Infrastructure Setup

## CRITICAL: Output Directory Setup

**Before proceeding with any phase, create the output directory structure:**

Set the output directory:
```bash
OUTPUT_DIR="tests/test_structure"
```

Create the required subdirectories:
```bash
mkdir -p ${OUTPUT_DIR}/templates
mkdir -p ${OUTPUT_DIR}/assets
mkdir -p ${OUTPUT_DIR}/exports
```

**Directory Structure:**
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates, example configurations, scripts
├── assets/            # Images, diagrams, charts, supplementary files
└── exports/           # Final reports, documentation, and publishable artifacts
```

**Throughout this prompt:**
- All generated files should be saved with the `${OUTPUT_DIR}/` prefix
- Examples:
  - Reports and documentation → `${OUTPUT_DIR}/exports/report.md`
  - Template files → `${OUTPUT_DIR}/templates/template.yaml`
  - Diagrams and images → `${OUTPUT_DIR}/assets/diagram.png`

Please design and implement a comprehensive test infrastructure for this Python project following this protocol:

## Repository Information

**Note**: Your repository URL is stored in `.git/config`. To find it automatically:

```bash
# Get the remote repository URL
git config --get remote.origin.url
```

Use `<REPO_URL>` as placeholder where repository URLs are needed in this template.

## Phase 1: Framework Selection & Configuration

1. **Test Framework Analysis**
   - **Current State**: Document existing test setup if any
   - **Framework Recommendation**:
     - **pytest** (recommended): Modern, feature-rich, excellent plugin ecosystem
     - **unittest**: Standard library, verbose, class-based
     - **nose2**: Legacy, less maintained
   - **Rationale**: Justify framework choice based on project needs

2. **Install Core Testing Dependencies**
   ```bash
   # Recommended pytest stack
   pip install pytest>=7.4.0
   pip install pytest-cov>=4.1.0        # Coverage integration
   pip install pytest-xdist>=3.3.0      # Parallel execution
   pip install pytest-mock>=3.11.0      # Enhanced mocking
   pip install pytest-timeout>=2.1.0    # Test timeouts
   pip install pytest-asyncio>=0.21.0   # Async test support (if needed)
   ```

3. **Configuration File Setup**

   **Create pytest.ini** (or add to pyproject.toml):
   ```ini
   [pytest]
   # Test discovery
   python_files = test_*.py *_test.py
   python_classes = Test* *Tests
   python_functions = test_*

   # Test paths
   testpaths = tests

   # Output options
   addopts =
       -v                          # Verbose output
       --strict-markers            # Enforce marker registration
       --tb=short                  # Shorter traceback format
       --disable-warnings          # Clean output
       -ra                         # Show summary of all test outcomes
       --cov=src                   # Coverage for src directory
       --cov-report=html           # HTML coverage report
       --cov-report=term-missing   # Terminal coverage with missing lines
       --cov-fail-under=80         # Fail if coverage below 80%

   # Markers (register custom markers)
   markers =
       unit: Unit tests
       integration: Integration tests
       e2e: End-to-end tests
       slow: Tests that take significant time
       smoke: Quick smoke tests for CI
       wip: Work in progress tests

   # Warnings
   filterwarnings =
       error                       # Treat warnings as errors
       ignore::DeprecationWarning  # Except deprecation warnings

   # Coverage options
   [coverage:run]
   source = src
   omit =
       */tests/*
       */test_*.py
       */__init__.py
       */setup.py

   [coverage:report]
   precision = 2
   show_missing = True
   skip_covered = False
   ```

   **Alternative: pyproject.toml configuration**:
   ```toml
   [tool.pytest.ini_options]
   minversion = "7.0"
   testpaths = ["tests"]
   python_files = ["test_*.py", "*_test.py"]
   python_classes = ["Test*", "*Tests"]
   python_functions = ["test_*"]
   addopts = [
       "-v",
       "--strict-markers",
       "--tb=short",
       "--cov=src",
       "--cov-report=html",
       "--cov-report=term-missing",
   ]
   markers = [
       "unit: Unit tests",
       "integration: Integration tests",
       "e2e: End-to-end tests",
       "slow: Tests that take significant time",
   ]
   ```

## Phase 2: Directory Structure Design

1. **Standard Test Layout**

   Implement this recommended structure:
   ```
   project_root/
   ├── src/
   │   └── myapp/
   │       ├── __init__.py
   │       ├── module_a.py
   │       └── module_b.py
   │
   ├── tests/
   │   ├── __init__.py
   │   ├── conftest.py              # Root fixtures (session/global scope)
   │   │
   │   ├── unit/                    # Unit tests (fast, isolated)
   │   │   ├── __init__.py
   │   │   ├── conftest.py          # Unit test fixtures
   │   │   ├── test_module_a.py
   │   │   └── test_module_b.py
   │   │
   │   ├── integration/             # Integration tests (multiple components)
   │   │   ├── __init__.py
   │   │   ├── conftest.py          # Integration fixtures
   │   │   ├── test_api_integration.py
   │   │   └── test_database_integration.py
   │   │
   │   ├── e2e/                     # End-to-end tests (full system)
   │   │   ├── __init__.py
   │   │   ├── conftest.py          # E2E fixtures
   │   │   └── test_user_workflows.py
   │   │
   │   ├── fixtures/                # Shared fixture definitions
   │   │   ├── __init__.py
   │   │   ├── database_fixtures.py
   │   │   ├── api_fixtures.py
   │   │   └── mock_fixtures.py
   │   │
   │   ├── helpers/                 # Test utility functions
   │   │   ├── __init__.py
   │   │   ├── assertions.py        # Custom assertions
   │   │   ├── factories.py         # Test data factories
   │   │   └── builders.py          # Object builders
   │   │
   │   ├── data/                    # Test data files
   │   │   ├── sample_data.json
   │   │   ├── test_config.yaml
   │   │   └── fixtures.csv
   │   │
   │   └── resources/               # Test resources (files, images, etc.)
   │       ├── sample_file.txt
   │       └── test_image.png
   ```

2. **Naming Conventions**

   **File Naming**:
   - Test files: `test_<module_name>.py` or `<module_name>_test.py`
   - Test class: `Test<FeatureName>` or `<FeatureName>Tests`
   - Test function: `test_<what_is_tested>`

   **Examples**:
   ```python
   # tests/unit/test_user_service.py
   class TestUserService:
       def test_create_user_with_valid_data(self):
           pass

       def test_create_user_raises_error_with_invalid_email(self):
           pass

   # tests/integration/test_api_endpoints.py
   class TestUserAPI:
       def test_post_user_creates_database_entry(self):
           pass
   ```

3. **Test Type Organization**

   **Unit Tests** (`tests/unit/`):
   - Test single functions/methods in isolation
   - Fast execution (<1s per test)
   - No external dependencies
   - Extensive mocking

   **Integration Tests** (`tests/integration/`):
   - Test multiple components together
   - Database, API, service interactions
   - Moderate execution time
   - Minimal mocking

   **E2E Tests** (`tests/e2e/`):
   - Test complete user workflows
   - Full system with real dependencies
   - Slowest execution
   - No mocking of core functionality

## Phase 3: Fixture Infrastructure

1. **conftest.py Hierarchy**

   **Root conftest.py** (`tests/conftest.py`):
   ```python
   """
   Root test configuration and fixtures.

   Fixtures defined here are available to all tests.
   Use for truly global, session-scoped fixtures.
   """
   import pytest
   from pathlib import Path

   # Session-scoped fixtures (setup once per test session)
   @pytest.fixture(scope="session")
   def project_root():
       """Return the project root directory."""
       return Path(__file__).parent.parent

   @pytest.fixture(scope="session")
   def test_data_dir(project_root):
       """Return the test data directory."""
       return project_root / "tests" / "data"

   # Configure pytest behavior
   def pytest_configure(config):
       """Configure pytest with custom settings."""
       config.addinivalue_line(
           "markers", "requires_db: mark test as requiring database"
       )

   # Custom command line options
   def pytest_addoption(parser):
       parser.addoption(
           "--run-slow",
           action="store_true",
           default=False,
           help="Run slow tests"
       )

   def pytest_collection_modifyitems(config, items):
       """Skip slow tests unless --run-slow is passed."""
       if not config.getoption("--run-slow"):
           skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
           for item in items:
               if "slow" in item.keywords:
                   item.add_marker(skip_slow)
   ```

   **Unit test conftest.py** (`tests/unit/conftest.py`):
   ```python
   """Unit test fixtures."""
   import pytest
   from unittest.mock import Mock

   @pytest.fixture
   def mock_database():
       """Mock database connection for unit tests."""
       return Mock()

   @pytest.fixture
   def sample_user_data():
       """Sample user data for testing."""
       return {
           "username": "testuser",
           "email": "test@example.com",
           "active": True
       }
   ```

   **Integration test conftest.py** (`tests/integration/conftest.py`):
   ```python
   """Integration test fixtures."""
   import pytest
   from myapp.database import Database

   @pytest.fixture(scope="module")
   def test_database():
       """Real test database for integration tests."""
       db = Database("test_db")
       db.setup()
       yield db
       db.teardown()

   @pytest.fixture
   def clean_database(test_database):
       """Ensure clean database state for each test."""
       test_database.clear_all_tables()
       yield test_database
   ```

2. **Fixture Scopes**

   Choose appropriate scope for efficiency:

   ```python
   # Function scope (default) - setup/teardown per test
   @pytest.fixture
   def user():
       return User("test")

   # Class scope - shared within test class
   @pytest.fixture(scope="class")
   def database_connection():
       conn = Database.connect()
       yield conn
       conn.close()

   # Module scope - shared within test module
   @pytest.fixture(scope="module")
   def api_client():
       client = APIClient()
       client.authenticate()
       yield client
       client.logout()

   # Session scope - setup once per entire test session
   @pytest.fixture(scope="session")
   def docker_services():
       services = DockerCompose.start()
       yield services
       DockerCompose.stop()
   ```

3. **Fixture Factories**

   Create flexible fixture factories for complex objects:

   ```python
   # tests/fixtures/user_fixtures.py
   import pytest
   from myapp.models import User

   @pytest.fixture
   def user_factory():
       """Factory for creating test users with custom attributes."""
       created_users = []

       def _create_user(username=None, email=None, **kwargs):
           user = User(
               username=username or f"user_{len(created_users)}",
               email=email or f"user{len(created_users)}@test.com",
               **kwargs
           )
           created_users.append(user)
           return user

       yield _create_user

       # Cleanup
       for user in created_users:
           user.delete()

   # Usage in tests
   def test_user_creation(user_factory):
       user1 = user_factory(username="alice")
       user2 = user_factory(username="bob", active=False)
       assert user1.username == "alice"
       assert not user2.active
   ```

4. **Fixture Composition**

   Build complex fixtures from simpler ones:

   ```python
   @pytest.fixture
   def database():
       """Database connection."""
       db = Database.connect()
       yield db
       db.close()

   @pytest.fixture
   def user_repository(database):
       """User repository with database."""
       return UserRepository(database)

   @pytest.fixture
   def authenticated_user(user_repository):
       """Create and authenticate a user."""
       user = user_repository.create(username="testuser")
       user.authenticate()
       yield user
       user_repository.delete(user.id)
   ```

## Phase 4: Test Utilities & Helpers

1. **Custom Assertions** (`tests/helpers/assertions.py`):

   ```python
   """Custom assertion helpers for cleaner test code."""
   from typing import Any, Callable

   def assert_valid_email(email: str):
       """Assert that a string is a valid email format."""
       import re
       pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
       assert re.match(pattern, email), f"Invalid email format: {email}"

   def assert_datetime_recent(dt, max_seconds=60):
       """Assert that a datetime is within the last N seconds."""
       from datetime import datetime, timedelta
       now = datetime.now()
       delta = now - dt
       assert delta < timedelta(seconds=max_seconds), \
           f"Datetime {dt} is not recent (more than {max_seconds}s old)"

   def assert_json_matches_schema(data: dict, schema: dict):
       """Assert that JSON data matches a JSON schema."""
       import jsonschema
       try:
           jsonschema.validate(instance=data, schema=schema)
       except jsonschema.ValidationError as e:
           raise AssertionError(f"JSON schema validation failed: {e}")

   def assert_raises_with_message(exception_type, message_pattern, func, *args, **kwargs):
       """Assert that a function raises specific exception with matching message."""
       import re
       try:
           func(*args, **kwargs)
           raise AssertionError(f"Expected {exception_type.__name__} but no exception was raised")
       except exception_type as e:
           if not re.search(message_pattern, str(e)):
               raise AssertionError(
                   f"Exception message '{str(e)}' doesn't match pattern '{message_pattern}'"
               )
   ```

2. **Test Data Factories** (`tests/helpers/factories.py`):

   ```python
   """Test data factories for generating test objects."""
   from datetime import datetime, timedelta
   import random
   import string

   class UserFactory:
       """Factory for creating test user data."""

       _counter = 0

       @classmethod
       def create(cls, **kwargs):
           """Create user with default or custom attributes."""
           cls._counter += 1
           defaults = {
               "id": cls._counter,
               "username": f"user_{cls._counter}",
               "email": f"user{cls._counter}@test.com",
               "created_at": datetime.now(),
               "active": True,
           }
           defaults.update(kwargs)
           return defaults

       @classmethod
       def create_batch(cls, count, **kwargs):
           """Create multiple users."""
           return [cls.create(**kwargs) for _ in range(count)]

       @classmethod
       def reset(cls):
           """Reset counter (useful in fixtures)."""
           cls._counter = 0

   class RandomDataGenerator:
       """Generate random test data."""

       @staticmethod
       def random_string(length=10):
           """Generate random alphanumeric string."""
           return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

       @staticmethod
       def random_email():
           """Generate random email address."""
           username = RandomDataGenerator.random_string(8)
           domain = RandomDataGenerator.random_string(6)
           return f"{username}@{domain}.com"

       @staticmethod
       def random_datetime(days_ago=30):
           """Generate random datetime within last N days."""
           delta = timedelta(days=random.randint(0, days_ago))
           return datetime.now() - delta
   ```

3. **Custom Decorators** (`tests/helpers/decorators.py`):

   ```python
   """Custom test decorators."""
   import functools
   import time
   import pytest

   def retry(max_attempts=3, delay=1):
       """Retry flaky test multiple times before failing."""
       def decorator(func):
           @functools.wraps(func)
           def wrapper(*args, **kwargs):
               for attempt in range(max_attempts):
                   try:
                       return func(*args, **kwargs)
                   except AssertionError:
                       if attempt == max_attempts - 1:
                           raise
                       time.sleep(delay)
           return wrapper
       return decorator

   def skip_if_slow(func):
       """Skip test if --run-slow not provided."""
       return pytest.mark.slow(func)

   def requires_env_var(var_name):
       """Skip test if environment variable not set."""
       import os
       def decorator(func):
           if var_name not in os.environ:
               return pytest.mark.skip(
                   reason=f"Environment variable {var_name} not set"
               )(func)
           return func
       return decorator
   ```

4. **Base Test Classes** (`tests/helpers/base_test.py`):

   ```python
   """Base test classes with common functionality."""
   import pytest
   from abc import ABC

   class BaseUnitTest(ABC):
       """Base class for unit tests."""

       @pytest.fixture(autouse=True)
       def setup_method_fixture(self):
           """Setup run before each test method."""
           self.setup()
           yield
           self.teardown()

       def setup(self):
           """Override in subclasses for setup logic."""
           pass

       def teardown(self):
           """Override in subclasses for teardown logic."""
           pass

   class DatabaseTestCase(BaseUnitTest):
       """Base class for tests requiring database."""

       @pytest.fixture(autouse=True)
       def _setup_database(self, test_database):
           """Automatically inject test database."""
           self.db = test_database

       def setup(self):
           """Clear database before each test."""
           self.db.clear_all_tables()
   ```

## Phase 5: Test Discovery & Execution

1. **Configure Test Discovery**

   Ensure pytest can find all tests:
   ```bash
   # Verify test discovery
   pytest --collect-only

   # Run specific test types
   pytest tests/unit                    # Run only unit tests
   pytest -m "unit"                     # Run tests marked as unit
   pytest -m "unit and not slow"        # Run fast unit tests
   pytest -k "test_user"                # Run tests matching pattern
   ```

2. **Parallel Test Execution**

   Configure parallel execution for faster test runs:
   ```bash
   # Install pytest-xdist
   pip install pytest-xdist

   # Run tests in parallel
   pytest -n auto                       # Auto-detect CPU count
   pytest -n 4                          # Use 4 workers

   # Parallel execution per scope
   pytest -n auto --dist loadscope      # Group by module/class
   ```

3. **Create Test Runner Script** (`tests/run_tests.py`):

   ```python
   """Test runner script with common configurations."""
   import sys
   import pytest

   def run_all_tests():
       """Run complete test suite."""
       args = [
           "tests/",
           "-v",
           "--tb=short",
           "--cov=src",
           "--cov-report=html",
           "--cov-report=term-missing",
       ]
       return pytest.main(args)

   def run_unit_tests():
       """Run only unit tests."""
       args = ["tests/unit/", "-v", "-m", "unit"]
       return pytest.main(args)

   def run_integration_tests():
       """Run only integration tests."""
       args = ["tests/integration/", "-v", "-m", "integration"]
       return pytest.main(args)

   def run_smoke_tests():
       """Run quick smoke tests."""
       args = ["tests/", "-v", "-m", "smoke", "--tb=line"]
       return pytest.main(args)

   if __name__ == "__main__":
       if len(sys.argv) > 1:
           test_type = sys.argv[1]
           if test_type == "unit":
               sys.exit(run_unit_tests())
           elif test_type == "integration":
               sys.exit(run_integration_tests())
           elif test_type == "smoke":
               sys.exit(run_smoke_tests())
       sys.exit(run_all_tests())
   ```

## File Output Instructions

**IMPORTANT**: Save all generated files to the correct directory structure:

```bash
# Create directory structure
mkdir -p tests/{phase_name}/test_files
mkdir -p tests/{phase_name}/test_data
mkdir -p tests/{phase_name}/test_reports
mkdir -p tests/{phase_name}/test_configs
```

**Save files as follows**:

- Test files → `tests/{phase_name}/test_files/`

- Test data → `tests/{phase_name}/test_data/`

- Test reports → `tests/{phase_name}/test_reports/`

- Test configs → `tests/{phase_name}/test_configs/`

Replace `{phase_name}` with the specific phase (test_structure, test_cases, mocks_fixtures, performance_testing, maintenance_cicd, or code_coverage).

## Output Format

Please provide a comprehensive test infrastructure design with the following structure:

### Infrastructure Summary
- **Test Framework**: [pytest/unittest with justification]
- **Total Test Files**: [count]
- **Test Organization**: [structure description]
- **Fixture Count**: [number of fixtures created]
- **Utility Modules**: [list of helper modules]

### Directory Structure
```
[Complete directory tree with all test folders and key files]
```

### Configuration Files Created
- **pytest.ini** or **pyproject.toml**: [Key settings configured]
- **conftest.py locations**: [List with scope descriptions]
- **Custom configurations**: [Any project-specific settings]

### Fixture Infrastructure
**Session-Scoped Fixtures** (setup once):
- [fixture_name]: [description and purpose]

**Module-Scoped Fixtures** (per file):
- [fixture_name]: [description and purpose]

**Function-Scoped Fixtures** (per test):
- [fixture_name]: [description and purpose]

**Fixture Factories**:
- [factory_name]: [description and usage example]

### Test Utilities
**Assertion Helpers** (`tests/helpers/assertions.py`):
- [helper_name]: [purpose]

**Data Factories** (`tests/helpers/factories.py`):
- [factory_name]: [purpose]

**Custom Decorators** (`tests/helpers/decorators.py`):
- [decorator_name]: [purpose]

### Test Execution Commands
```bash
# Run all tests
pytest

# Run specific test types
pytest -m unit
pytest -m integration
pytest tests/unit/test_specific.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run in parallel
pytest -n auto

# Run and stop at first failure
pytest -x

# Run verbose with output
pytest -v -s
```

### Testing Conventions Established
1. **File Naming**: [convention]
2. **Test Naming**: [convention]
3. **Fixture Naming**: [convention]
4. **Marker Usage**: [how to use markers]
5. **Test Data**: [where to store, how to organize]

### Next Steps
- [ ] Implement actual test cases using this infrastructure
- [ ] Add project-specific fixtures
- [ ] Configure CI/CD integration
- [ ] Set up code coverage reporting
- [ ] Document testing guidelines for team
- [ ] Create test templates for common scenarios

### Best Practices Implemented
- Fixtures organized by scope for efficiency
- Clear separation of test types
- Reusable test utilities
- Comprehensive test discovery
- Parallel execution support
- Coverage measurement integrated
- Custom markers for test categorization

### Maintenance Recommendations
- Regularly review and refactor fixtures
- Keep conftest.py files lean and focused
- Document complex fixtures thoroughly
- Monitor test execution time
- Update dependencies regularly
- Review and remove obsolete tests
~~~

## Output Format

The AI assistant should deliver:

1. **Test infrastructure design document** with complete directory structure
2. **Configuration files** (pytest.ini or pyproject.toml configuration)
3. **conftest.py files** at appropriate levels with documented fixtures
4. **Test utility modules** in helpers/ directory
5. **Test runner script** for easy execution
6. **Documentation** of conventions and best practices
7. **Execution commands** for common test scenarios
---

## Verify Directory Structure

After completing all phases, verify the output structure:

```bash
tree ${OUTPUT_DIR}
```

Expected structure:
```
${OUTPUT_DIR}/
├── templates/          # Reusable templates and scripts
├── assets/            # Images, diagrams, supplementary files
└── exports/           # Final publishable artifacts and reports
```

**Verification checklist:**
- [ ] All directories created successfully
- [ ] All files saved in correct subdirectories
- [ ] No files created in repository root
- [ ] Directory structure matches expected layout
