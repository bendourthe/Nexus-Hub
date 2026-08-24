### Step 2: Design Pydantic v2 Schemas

```python
# src/app/schemas/user.py
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, computed_field


class UserBase(BaseModel):
    """Shared fields for user schemas."""
    email: EmailStr
    display_name: Annotated[str, Field(min_length=2, max_length=50)]


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for partial user updates."""
    display_name: str | None = None
    email: EmailStr | None = None


class UserResponse(UserBase):
    """Schema for user responses (excludes password)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    is_active: bool

    @computed_field
    @property
    def member_since_days(self) -> int:
        return (datetime.utcnow() - self.created_at).days


class UserListResponse(BaseModel):
    """Paginated user list."""
    data: list[UserResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
```

**Discriminated union for polymorphic responses**:

```python
from typing import Literal
from pydantic import BaseModel


class TextNotification(BaseModel):
    type: Literal["text"] = "text"
    message: str


class ImageNotification(BaseModel):
    type: Literal["image"] = "image"
    image_url: str
    caption: str | None = None


class ActionNotification(BaseModel):
    type: Literal["action"] = "action"
    message: str
    action_url: str
    action_label: str


# FastAPI automatically generates correct OpenAPI schema
Notification = TextNotification | ImageNotification | ActionNotification
```
