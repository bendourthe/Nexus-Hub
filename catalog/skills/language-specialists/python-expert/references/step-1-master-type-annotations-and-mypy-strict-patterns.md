### Step 1: Master Type Annotations and mypy-Strict Patterns

**Enable Postponed Evaluation and Modern Syntax**:

```python
from __future__ import annotations

from typing import TypeVar, Generic, Protocol

# X | Y union syntax (works at runtime with __future__ annotations)
def fetch_user(user_id: int) -> User | None:
    """Return user or None if not found."""
    row = db.query("SELECT * FROM users WHERE id = %s", (user_id,))
    if row is None:
        return None
    return User.from_row(row)

# Avoid Optional[X] and Union[X, Y] in new code
# Bad:  Optional[str]
# Good: str | None
def parse_header(raw: str) -> str | None:
    parts = raw.split(":", maxsplit=1)
    return parts[1].strip() if len(parts) == 2 else None
```

**TypeVar and Generic Containers**:

```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Stack(Generic[T]):
    """Type-safe generic stack."""

    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek at empty stack")
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)

# Usage: mypy enforces type consistency
stack: Stack[int] = Stack()
stack.push(42)
stack.push("oops")  # mypy error: Argument 1 has incompatible type "str"
```

**Protocol for Structural Subtyping**:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict[str, object]: ...

class User:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "age": self.age}

# User satisfies Serializable without inheriting from it
def serialize(obj: Serializable) -> str:
    import json
    return json.dumps(obj.to_dict())

# Runtime check also works
assert isinstance(User("Alice", 30), Serializable)
```

**mypy Strict Configuration** (pyproject.toml):

```toml
[tool.mypy]
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true
```
