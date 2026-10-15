## Common Patterns

### Pattern 1: Repository Pattern with Service Layer

```python
# Separate data access (repository) from business logic (service)
class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def find_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def save(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user


class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: UserCreate) -> User:
        existing = await self.repo.find_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")
        user = User(
            email=data.email,
            display_name=data.display_name,
            hashed_password=hash_password(data.password),
        )
        return await self.repo.save(user)
```

### Pattern 2: Pagination Helper

```python
from typing import TypeVar, Generic, Sequence
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: Sequence[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls, data: Sequence[T], total: int, page: int, page_size: int
    ) -> "PaginatedResponse[T]":
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_prev=page > 1,
        )
```
