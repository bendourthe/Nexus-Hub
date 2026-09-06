## Common Anti-Patterns to Avoid

### Testing Implementation Instead of Behavior
```python
# BAD
def test_uses_hash_map():
    cache = Cache()
    assert isinstance(cache._storage, dict)  # Implementation detail

# GOOD
def test_caches_values():
    cache = Cache()
    cache.set("key", "value")
    assert cache.get("key") == "value"  # Behavior
```

### Multiple Unrelated Assertions
```python
# BAD
def test_user():
    user = User("John", "john@example.com")
    assert user.name == "John"
    assert user.email == "john@example.com"
    assert user.validate_email() is True
    assert user.age is None

# GOOD - Separate tests
def test_user_name_initialization():
    user = User("John", "john@example.com")
    assert user.name == "John"

def test_user_email_validation():
    user = User("John", "john@example.com")
    assert user.validate_email() is True
```

### Slow Tests
```python
# BAD
def test_with_delay():
    time.sleep(5)  # Don't do this
    result = operation()
    assert result is not None

# GOOD
def test_without_delay(mocker):
    mocker.patch("time.sleep")  # Mock the delay
    result = operation()
    assert result is not None
```
