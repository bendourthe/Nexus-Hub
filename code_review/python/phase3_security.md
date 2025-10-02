# Phase 3: Security & Error Handling Review

## Objective
Identify security vulnerabilities, assess error handling robustness, and verify safe coding practices.

## Review Checklist

### Input Validation
- [ ] All user inputs validated before processing
- [ ] Type checking performed on external data
- [ ] Range validation for numerical inputs
- [ ] String length limits enforced
- [ ] File path validation to prevent traversal attacks
- [ ] SQL injection prevention (parameterized queries)
- [ ] Command injection prevention

### Error Handling
- [ ] Try-except blocks used appropriately
- [ ] Specific exceptions caught (not bare `except:`)
- [ ] Meaningful error messages provided
- [ ] Error context preserved when re-raising
- [ ] Resources properly cleaned up (try-finally or context managers)
- [ ] Errors logged appropriately
- [ ] Sensitive information not exposed in error messages

### Authentication & Authorization
- [ ] Credentials never hardcoded
- [ ] Environment variables used for secrets
- [ ] Password hashing implemented correctly
- [ ] Session management secure
- [ ] Authorization checks before sensitive operations
- [ ] Principle of least privilege applied

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Secure communication channels (HTTPS/TLS)
- [ ] Personal data handling complies with regulations
- [ ] Data sanitization before logging
- [ ] Temporary files securely deleted
- [ ] Database credentials protected

### Dependency Security
- [ ] Dependencies up to date
- [ ] Known vulnerabilities checked
- [ ] Minimal dependency footprint
- [ ] Dependency versions pinned
- [ ] No deprecated packages used

### Resource Management
- [ ] File handles properly closed
- [ ] Database connections properly managed
- [ ] Memory leaks prevented
- [ ] Context managers used for resources
- [ ] No unbounded resource consumption

## Detailed Review Prompt

```
Please perform a comprehensive security and error handling review:

**Input Validation Assessment:**
1. Identify all entry points accepting external input:
   - User input fields
   - API endpoints
   - File uploads
   - Configuration files
   - Command-line arguments
   - Environment variables

2. For each entry point, verify:
   - Type validation is performed
   - Range/length limits are enforced
   - Special characters are handled safely
   - Path traversal attacks are prevented
   - SQL/Command injection is prevented

3. Check validation patterns:
   ```python
   # Good: Explicit validation
   if not isinstance(user_input, str):
       raise ValueError("Invalid input type")
   if len(user_input) > MAX_LENGTH:
       raise ValueError("Input too long")
   
   # Good: Parameterized queries
   cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
   
   # Bad: String concatenation with user input
   cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
   ```

**Error Handling Evaluation:**
1. Review all try-except blocks:
   - Are specific exceptions caught (avoid bare `except:`)?
   - Are error messages meaningful and actionable?
   - Is error context preserved when re-raising?
   - Are resources cleaned up properly?

2. Check error handling patterns:
   ```python
   # Good: Specific exception handling
   try:
       result = risky_operation()
   except FileNotFoundError as e:
       logger.error(f"File not found: {e}")
       raise
   except PermissionError as e:
       logger.error(f"Permission denied: {e}")
       return None
   finally:
       cleanup_resources()
   
   # Bad: Bare except
   try:
       result = risky_operation()
   except:
       pass
   ```

3. Verify logging practices:
   - Errors are logged with appropriate severity
   - Sensitive data is not logged
   - Sufficient context is included for debugging

**Authentication & Authorization Review:**
1. Check credential management:
   - No hardcoded passwords or API keys
   - Environment variables or secure vaults used
   - Credentials not committed to version control

2. Verify authentication implementation:
   - Password hashing uses strong algorithms (bcrypt, Argon2)
   - Salt is used and unique per user
   - Session tokens are cryptographically secure
   - Session expiration is implemented

3. Review authorization:
   - Access checks before sensitive operations
   - User permissions properly validated
   - Principle of least privilege applied

**Data Protection Assessment:**
1. Check data in transit:
   - HTTPS/TLS used for network communication
   - Certificates properly validated
   - No sensitive data in URLs

2. Check data at rest:
   - Sensitive data encrypted
   - Encryption keys properly managed
   - Temporary files securely deleted

3. Review logging and output:
   - Sensitive data sanitized before logging
   - No credentials in logs
   - PII handling complies with regulations

**Dependency Security Audit:**
1. Review requirements.txt and pyproject.toml:
   - Check for known vulnerabilities (suggest running `pip-audit`)
   - Verify versions are pinned
   - Identify deprecated packages
   - Assess if dependencies are necessary

2. Check for security best practices:
   ```python
   # Good: Pinned versions
   requests==2.28.1
   cryptography>=41.0.0,<42.0.0
   
   # Risky: Unpinned versions
   requests
   cryptography
   ```

**Resource Management Review:**
1. Verify proper resource cleanup:
   - File handles closed (use context managers)
   - Database connections managed properly
   - Network sockets closed
   - Memory released appropriately

2. Check for resource exhaustion risks:
   - Unbounded loops
   - Unlimited file/memory allocations
   - No rate limiting on external calls

**Deliverables:**
Provide a security assessment report with:
- Critical vulnerabilities (require immediate attention)
- High-priority security concerns
- Medium-priority improvements
- Best practice recommendations
- Specific code locations for each finding
- Remediation suggestions with code examples
- Overall security rating (Secure/Needs Attention/Vulnerable)
```

## Expected Outcomes

### Pass Criteria
- No critical security vulnerabilities
- All inputs validated appropriately
- Proper error handling throughout
- Credentials properly managed
- Resources properly cleaned up
- Dependencies up to date without known vulnerabilities

### Critical Issues to Flag (Stop Ship)
- Hardcoded credentials or API keys
- SQL injection vulnerabilities
- Command injection vulnerabilities
- Path traversal vulnerabilities
- Unencrypted sensitive data
- Bare except clauses hiding errors
- Known critical CVEs in dependencies

### High-Priority Issues to Flag
- Missing input validation
- Weak error handling
- Sensitive data in logs
- Missing authentication checks
- Resources not properly closed
- Deprecated dependencies

## Security Patterns Reference

### Safe Input Validation
```python
from typing import Any

def validate_user_input(data: Any, max_length: int = 1000) -> str:
    """Validate and sanitize user input."""
    if not isinstance(data, str):
        raise ValueError("Input must be a string")
    if len(data) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length}")
    # Sanitize special characters if needed
    sanitized = data.strip()
    return sanitized
```

### Safe Error Handling
```python
import logging

logger = logging.getLogger(__name__)

def safe_operation(param: str) -> Optional[dict]:
    """Perform operation with proper error handling."""
    try:
        result = risky_operation(param)
        return result
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}", exc_info=True)
        raise
    except PermissionError as e:
        logger.warning(f"Permission denied, using fallback: {e}")
        return get_fallback_result()
    except Exception as e:
        logger.error(f"Unexpected error in safe_operation: {e}", exc_info=True)
        raise
    finally:
        cleanup_resources()
```

### Safe Credential Management
```python
import os
from typing import Optional

def get_api_key() -> str:
    """Retrieve API key from environment."""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable not set")
    return api_key

# Never do this:
# API_KEY = "hardcoded_secret_key"
```

### Safe Resource Management
```python
from pathlib import Path
from typing import List

def read_file_safely(file_path: Path) -> List[str]:
    """Read file with proper resource management."""
    # Using context manager ensures file is closed
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines
```

## Next Steps
After completing this phase, proceed to Phase 4: Performance & Scalability Review.
