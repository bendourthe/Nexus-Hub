### Step 2: Handle Exceptions Idiomatically

**Custom Exception Hierarchy**:

```python
class AppError(Exception):
    """Base exception for the application."""

    def __init__(self, message: str, code: str = "UNKNOWN") -> None:
        super().__init__(message)
        self.code = code

class NotFoundError(AppError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: object) -> None:
        super().__init__(
            f"{resource} with id {identifier!r} not found",
            code="NOT_FOUND",
        )
        self.resource = resource
        self.identifier = identifier

class ValidationError(AppError):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(
            f"Validation failed for {field!r}: {reason}",
            code="VALIDATION_ERROR",
        )
        self.field = field
        self.reason = reason
```

**Error Chaining with raise-from**:

```python
import logging

logger = logging.getLogger(__name__)

def load_config(path: str) -> dict[str, object]:
    try:
        with open(path) as f:
            import json
            return json.load(f)
    except FileNotFoundError as exc:
        raise AppError(f"Config file missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise AppError(f"Invalid JSON in {path}: line {exc.lineno}") from exc

# The original exception is preserved in __cause__
# Tracebacks show: "The above exception was the direct cause of..."
```

**Context Managers for Resource Cleanup**:

```python
from contextlib import contextmanager
from typing import Iterator

@contextmanager
def temporary_directory(prefix: str = "tmp") -> Iterator[str]:
    """Create a temp directory and clean it up on exit."""
    import tempfile
    import shutil

    path = tempfile.mkdtemp(prefix=prefix)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)

# Usage
with temporary_directory("build_") as build_dir:
    compile_assets(build_dir)
    # Directory is cleaned up even if an exception occurs

# Class-based context manager for database transactions
class Transaction:
    def __init__(self, conn: Connection) -> None:
        self._conn = conn

    def __enter__(self) -> Transaction:
        self._conn.begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> bool:
        if exc_type is not None:
            self._conn.rollback()
            logger.error("Transaction rolled back: %s", exc_val)
            return False  # Re-raise the exception
        self._conn.commit()
        return False
```
