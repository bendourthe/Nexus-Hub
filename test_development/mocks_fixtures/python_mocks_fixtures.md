# Phase 3: Mock & Fixture Management

## Objective
Establish robust mocking strategies and test data fixtures for isolated, repeatable testing.

## Mock Management Checklist

### Mock Strategy
- [ ] External dependencies identified
- [ ] Mock objects for databases
- [ ] Mock objects for API clients
- [ ] Mock objects for file systems
- [ ] Mock objects for network services
- [ ] Mock return values configured
- [ ] Mock call verification implemented
- [ ] Mock reset in tearDown

### Fixture Management
- [ ] Test data directory created
- [ ] JSON fixtures for common data
- [ ] CSV fixtures for tabular data
- [ ] Binary fixtures for files
- [ ] Fixture loading utilities
- [ ] Fixture generation functions
- [ ] Dynamic fixture creation
- [ ] Fixture cleanup procedures

### Test Data Patterns
- [ ] Valid input samples
- [ ] Invalid input samples
- [ ] Edge case data sets
- [ ] Large data sets for performance
- [ ] Minimal data sets for speed
- [ ] Representative production data
- [ ] Anonymized real data (if applicable)

### Isolation Techniques
- [ ] Database transactions rolled back
- [ ] Temporary file cleanup
- [ ] Environment variable restoration
- [ ] Global state reset
- [ ] Cache clearing
- [ ] Connection pool cleanup

## Detailed Mock & Fixture Development Prompt

```
Please help me implement comprehensive mocking and fixture management for my test suite.

**Testing Context:**
- External dependencies: [LIST]
- Data sources: [LIST]
- File operations: [YES/NO]
- API integrations: [LIST]
- Database type: [DATABASE]

**Mock Implementation:**

### 1. Mock Setup Patterns

#### Database Mocking
```python
from unittest.mock import Mock, MagicMock, patch

def _setup_database_mocks(self) -> Mock:
    """Setup database mock with common operations."""
    db_mock = Mock()
    
    # Configure query responses
    db_mock.query.return_value = [
        {'id': 1, 'name': 'Test Item 1', 'value': 100},
        {'id': 2, 'name': 'Test Item 2', 'value': 200}
    ]
    
    # Configure single record fetch
    db_mock.get.return_value = {'id': 1, 'name': 'Test Item', 'value': 100}
    
    # Configure insert operation
    db_mock.insert.return_value = {'id': 3, 'status': 'success'}
    
    # Configure update operation
    db_mock.update.return_value = {'rows_affected': 1}
    
    # Configure delete operation
    db_mock.delete.return_value = {'rows_affected': 1}
    
    # Configure transaction management
    db_mock.begin_transaction.return_value = None
    db_mock.commit.return_value = None
    db_mock.rollback.return_value = None
    
    # Configure connection status
    db_mock.is_connected.return_value = True
    
    return db_mock
```

#### API Client Mocking
```python
def _setup_api_mocks(self) -> Mock:
    """Setup API client mock with common endpoints."""
    api_mock = Mock()
    
    # Configure GET requests
    api_mock.get.return_value = {
        'status': 200,
        'data': {'key': 'value'},
        'headers': {'Content-Type': 'application/json'}
    }
    
    # Configure POST requests
    api_mock.post.return_value = {
        'status': 201,
        'data': {'id': 'new_id', 'created': True},
        'headers': {'Location': '/api/resource/new_id'}
    }
    
    # Configure PUT requests
    api_mock.put.return_value = {
        'status': 200,
        'data': {'updated': True}
    }
    
    # Configure DELETE requests
    api_mock.delete.return_value = {
        'status': 204,
        'data': None
    }
    
    # Configure authentication
    api_mock.authenticate.return_value = {
        'token': 'test_token_12345',
        'expires_in': 3600
    }
    
    # Configure rate limiting
    api_mock.get_rate_limit.return_value = {
        'remaining': 100,
        'limit': 1000,
        'reset_time': 1234567890
    }
    
    return api_mock
```

#### File System Mocking
```python
def _setup_filesystem_mocks(self) -> Mock:
    """Setup file system mock."""
    fs_mock = Mock()
    
    # Configure file reading
    fs_mock.read_file.return_value = "test file contents"
    
    # Configure file writing
    fs_mock.write_file.return_value = True
    
    # Configure file existence check
    fs_mock.file_exists.return_value = True
    
    # Configure directory listing
    fs_mock.list_directory.return_value = [
        'file1.txt', 'file2.txt', 'subdir/'
    ]
    
    # Configure file deletion
    fs_mock.delete_file.return_value = True
    
    # Configure directory creation
    fs_mock.create_directory.return_value = True
    
    return fs_mock
```

#### Advanced Mock Patterns
```python
def _setup_advanced_mocks(self) -> Dict[str, Mock]:
    """Setup advanced mocking patterns."""
    
    # Mock with side effects
    database_mock = Mock()
    call_count = [0]
    
    def query_side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return [{'id': 1}]
        elif call_count[0] == 2:
            return []
        else:
            raise Exception("Database error")
    
    database_mock.query.side_effect = query_side_effect
    
    # Mock with multiple return values
    api_mock = Mock()
    api_mock.fetch.side_effect = [
        {'status': 'pending'},
        {'status': 'processing'},
        {'status': 'complete'}
    ]
    
    # Mock with exception
    error_mock = Mock()
    error_mock.operation.side_effect = ValueError("Invalid input")
    
    # Context manager mock
    file_mock = MagicMock()
    file_mock.__enter__.return_value = file_mock
    file_mock.read.return_value = "file contents"
    
    return {
        'database': database_mock,
        'api': api_mock,
        'error_service': error_mock,
        'file': file_mock
    }
```

### 2. Test Fixture Creation

#### JSON Fixtures
Create `test_data/sample_data.json`:
```json
{
    "valid_users": [
        {
            "id": 1,
            "username": "testuser1",
            "email": "test1@example.com",
            "active": true
        },
        {
            "id": 2,
            "username": "testuser2",
            "email": "test2@example.com",
            "active": false
        }
    ],
    "valid_products": [
        {
            "id": 101,
            "name": "Product A",
            "price": 29.99,
            "stock": 100
        },
        {
            "id": 102,
            "name": "Product B",
            "price": 49.99,
            "stock": 50
        }
    ],
    "edge_cases": {
        "empty_string": "",
        "null_value": null,
        "zero": 0,
        "negative": -1,
        "very_large": 999999999,
        "unicode": "Hello 世界 🌍",
        "special_chars": "!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
    }
}
```

#### Fixture Loading Utilities
```python
import json
import csv
from pathlib import Path
from typing import Any, Dict, List

class FixtureLoader:
    """Load test fixtures from various sources."""
    
    def __init__(self, test_data_dir: str = "test_data"):
        """Initialize fixture loader."""
        self.test_data_dir = Path(test_data_dir)
    
    def load_json_fixture(self, filename: str) -> Dict[str, Any]:
        """Load JSON fixture file."""
        filepath = self.test_data_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_csv_fixture(self, filename: str) -> List[Dict[str, Any]]:
        """Load CSV fixture file."""
        filepath = self.test_data_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    
    def load_text_fixture(self, filename: str) -> str:
        """Load text fixture file."""
        filepath = self.test_data_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_binary_fixture(self, filename: str) -> bytes:
        """Load binary fixture file."""
        filepath = self.test_data_dir / filename
        with open(filepath, 'rb') as f:
            return f.read()
```

#### Dynamic Fixture Generation
```python
class FixtureGenerator:
    """Generate test fixtures dynamically."""
    
    @staticmethod
    def generate_users(count: int = 10) -> List[Dict[str, Any]]:
        """Generate test user data."""
        return [
            {
                'id': i,
                'username': f'testuser{i}',
                'email': f'test{i}@example.com',
                'active': i % 2 == 0,
                'created_at': f'2024-01-{(i % 30) + 1:02d}'
            }
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def generate_products(count: int = 20) -> List[Dict[str, Any]]:
        """Generate test product data."""
        categories = ['Electronics', 'Clothing', 'Food', 'Books']
        return [
            {
                'id': 100 + i,
                'name': f'Product {i}',
                'price': round(10.0 + (i * 5.5), 2),
                'stock': (i * 10) % 200,
                'category': categories[i % len(categories)]
            }
            for i in range(1, count + 1)
        ]
    
    @staticmethod
    def generate_transactions(
        count: int = 100,
        user_ids: List[int] = None,
        product_ids: List[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate test transaction data."""
        import random
        from datetime import datetime, timedelta
        
        if user_ids is None:
            user_ids = list(range(1, 11))
        if product_ids is None:
            product_ids = list(range(101, 121))
        
        base_date = datetime(2024, 1, 1)
        
        return [
            {
                'id': 1000 + i,
                'user_id': random.choice(user_ids),
                'product_id': random.choice(product_ids),
                'quantity': random.randint(1, 5),
                'total': round(random.uniform(10.0, 500.0), 2),
                'timestamp': (base_date + timedelta(hours=i)).isoformat(),
                'status': random.choice(['completed', 'pending', 'cancelled'])
            }
            for i in range(count)
        ]
    
    @staticmethod
    def generate_large_dataset(
        size: int = 10000,
        complexity: str = 'simple'
    ) -> List[Dict[str, Any]]:
        """Generate large dataset for performance testing."""
        if complexity == 'simple':
            return [
                {'id': i, 'value': i * 2}
                for i in range(size)
            ]
        elif complexity == 'medium':
            return [
                {
                    'id': i,
                    'data': f'item_{i}',
                    'value': i * 2,
                    'category': f'cat_{i % 10}',
                    'active': i % 2 == 0
                }
                for i in range(size)
            ]
        else:  # complex
            return [
                {
                    'id': i,
                    'data': f'item_{i}',
                    'value': i * 2,
                    'category': f'cat_{i % 10}',
                    'active': i % 2 == 0,
                    'metadata': {
                        'created': f'2024-01-{(i % 30) + 1:02d}',
                        'tags': [f'tag{j}' for j in range(i % 5)],
                        'nested': {'level': i % 3, 'data': f'nested_{i}'}
                    }
                }
                for i in range(size)
            ]
```

### 3. Test Isolation Patterns

#### Database Test Isolation
```python
class DatabaseTestMixin:
    """Mixin for database test isolation."""
    
    def setUp(self):
        """Setup test database transaction."""
        super().setUp()
        # Begin transaction
        self.db_transaction = self.database.begin_transaction()
        # Create test tables if needed
        self._create_test_tables()
        # Insert test data
        self._insert_test_data()
    
    def tearDown(self):
        """Rollback test database transaction."""
        # Rollback transaction (undo all changes)
        if hasattr(self, 'db_transaction'):
            self.database.rollback(self.db_transaction)
        super().tearDown()
    
    def _create_test_tables(self):
        """Create temporary test tables."""
        # Create tables in test transaction
        pass
    
    def _insert_test_data(self):
        """Insert test data into database."""
        # Insert test records
        pass
```

#### File System Test Isolation
```python
class FileSystemTestMixin:
    """Mixin for file system test isolation."""
    
    def setUp(self):
        """Setup temporary test directory."""
        super().setUp()
        import tempfile
        # Create temporary directory
        self.test_dir = tempfile.mkdtemp(prefix='test_')
        # Track created files
        self.created_files = []
    
    def tearDown(self):
        """Clean up temporary test files."""
        import shutil
        # Remove all created files
        for filepath in self.created_files:
            if os.path.exists(filepath):
                os.remove(filepath)
        # Remove temporary directory
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        super().tearDown()
    
    def create_test_file(self, filename: str, content: str) -> str:
        """Create test file and track for cleanup."""
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        self.created_files.append(filepath)
        return filepath
```

#### Environment Isolation
```python
class EnvironmentTestMixin:
    """Mixin for environment variable isolation."""
    
    def setUp(self):
        """Save current environment state."""
        super().setUp()
        # Save original environment
        self.original_env = os.environ.copy()
        # Set test environment variables
        os.environ['TEST_MODE'] = 'true'
        os.environ['DATABASE_URL'] = 'test://localhost/testdb'
    
    def tearDown(self):
        """Restore original environment."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        super().tearDown()
```

### 4. Mock Verification Patterns

#### Verify Mock Calls
```python
# Verify method was called
mock_object.method.assert_called()

# Verify method was called once
mock_object.method.assert_called_once()

# Verify method was called with specific arguments
mock_object.method.assert_called_with(arg1, arg2, kwarg=value)

# Verify method was called once with specific arguments
mock_object.method.assert_called_once_with(arg1, arg2)

# Verify method was not called
mock_object.method.assert_not_called()

# Verify call count
self.assertEqual(mock_object.method.call_count, 3)

# Verify all calls
expected_calls = [
    call(arg1, arg2),
    call(arg3, arg4),
    call(arg5, arg6)
]
mock_object.method.assert_has_calls(expected_calls)
```

**Deliverables:**
1. Comprehensive mock setup for all external dependencies
2. Test fixture files with representative data
3. Fixture loading and generation utilities
4. Test isolation mixins for databases, files, and environment
5. Mock verification patterns documented
6. Cleanup procedures implemented

**Success Criteria:**
- All external dependencies properly mocked
- Test data fixtures comprehensive and realistic
- Tests run in complete isolation
- No test pollution between test runs
- Mock calls verified correctly
- Fixtures load without errors
```

## Expected Outcomes

### Mock Coverage
- Database operations fully mocked
- API clients completely isolated
- File system operations controlled
- Network services simulated
- External services never actually called

### Fixture Library
- JSON fixtures for common data types
- CSV fixtures for tabular data
- Text fixtures for documents
- Binary fixtures for files
- Dynamic generation for large datasets

### Test Isolation
- Database transactions rolled back
- Temporary files cleaned up
- Environment restored
- Global state reset
- No cross-test contamination

## Common Mocking Patterns

### Patch Decorator Pattern
```python
@patch('module.external_service')
def test_with_patch(self, mock_service):
    """Test with patched external service."""
    mock_service.return_value = {'result': 'success'}
    result = function_using_service()
    self.assertEqual(result, 'success')
```

### Context Manager Pattern
```python
def test_with_context_manager(self):
    """Test with context manager mock."""
    with patch('module.external_service') as mock_service:
        mock_service.return_value = {'result': 'success'}
        result = function_using_service()
        self.assertEqual(result, 'success')
```

### Multiple Patches Pattern
```python
@patch('module.service_b')
@patch('module.service_a')
def test_multiple_patches(self, mock_a, mock_b):
    """Test with multiple patched services."""
    # Note: patches applied in reverse order
    mock_a.return_value = 'a'
    mock_b.return_value = 'b'
    # Test code
```

## Next Steps
After completing mock and fixture setup, proceed to Phase 4: Performance & Load Testing.
