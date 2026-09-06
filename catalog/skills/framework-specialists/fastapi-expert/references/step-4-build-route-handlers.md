### Step 4: Build Route Handlers

```python
# src/app/routers/users.py
from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentUser, AdminUser, DbSession
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = Query(default=None, max_length=100),
):
    """List users with pagination and optional search."""
    service = UserService(db)
    users, total = await service.list_users(
        page=page, page_size=page_size, search=search
    )
    return UserListResponse(
        data=users,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(user: CurrentUser):
    """Get the authenticated user's profile."""
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: DbSession):
    """Get a user by ID."""
    service = UserService(db)
    user = await service.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, db: DbSession):
    """Create a new user account."""
    service = UserService(db)
    existing = await service.get_by_email(data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    return await service.create(data)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, user: CurrentUser, db: DbSession):
    """Update a user (self or admin)."""
    if user.id != user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    service = UserService(db)
    updated = await service.update(user_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, admin: AdminUser, db: DbSession):
    """Delete a user (admin only)."""
    service = UserService(db)
    deleted = await service.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
```
