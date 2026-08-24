### Step 4: Model Data with Dataclasses and Pydantic

**Dataclass Fundamentals**:

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass(frozen=True)
class Money:
    """Immutable value object for monetary amounts."""
    amount: int  # Store as cents to avoid float issues
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

@dataclass
class Order:
    """Mutable entity with computed defaults."""
    customer_id: int
    items: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    total: Money = field(default_factory=lambda: Money(0))

    def add_item(self, name: str, price: Money) -> None:
        self.items.append(name)
        self.total = self.total + price
```

**Dataclass with Slots (Python 3.10+)**:

```python
@dataclass(slots=True)
class Point:
    """Memory-efficient dataclass using __slots__."""
    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: Point) -> float:
        return (
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        ) ** 0.5
```

**Pydantic BaseModel for Validation and Serialization**:

```python
from pydantic import BaseModel, Field, field_validator, model_validator

class CreateUserRequest(BaseModel):
    """Validated API request model."""
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: str = Field(max_length=255)
    age: int = Field(ge=13, le=150)
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.lower()

    @model_validator(mode="after")
    def check_consistency(self) -> CreateUserRequest:
        if self.age < 18 and "admin" in self.tags:
            raise ValueError("Users under 18 cannot be admins")
        return self

# Parse and validate from dict (e.g., request.json())
user = CreateUserRequest.model_validate({"username": "alice", "email": "ALICE@example.com", "age": 25})
print(user.email)  # alice@example.com (lowercased by validator)

# Serialize to dict or JSON
user.model_dump()
user.model_dump_json()
```

**Pydantic Settings for Configuration**:

```python
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    """Load settings from environment variables."""
    database_url: str
    redis_url: str = "redis://localhost:6379"
    debug: bool = False
    max_connections: int = 10

    model_config = {"env_prefix": "APP_"}

# Reads APP_DATABASE_URL, APP_REDIS_URL, etc. from environment
settings = AppSettings()
```
