### Step 1: Structure a FastAPI Project

**Recommended project layout**:

```
src/
  app/
    __init__.py
    main.py               # Application factory
    config.py             # Settings with Pydantic
    dependencies.py       # Shared dependencies
    middleware.py          # Custom middleware
    models/
      __init__.py
      user.py             # SQLAlchemy models
      post.py
    schemas/
      __init__.py
      user.py             # Pydantic request/response schemas
      post.py
      common.py           # Shared schemas (pagination, errors)
    routers/
      __init__.py
      users.py            # /users endpoints
      posts.py            # /posts endpoints
      auth.py             # /auth endpoints
    services/
      __init__.py
      user_service.py     # Business logic
      auth_service.py
    db/
      __init__.py
      session.py          # Database session management
      base.py             # SQLAlchemy Base
tests/
  conftest.py             # Shared fixtures
  test_users.py
  test_auth.py
  factories.py            # Test data factories
```

**Application factory**:

```python
# src/app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import engine
from app.db.base import Base
from app.middleware import TimingMiddleware
from app.routers import users, posts, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: create tables (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Middleware (order matters: last added = first executed)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(auth.router, prefix="/auth", tags=["auth"])
    app.include_router(users.router, prefix="/users", tags=["users"])
    app.include_router(posts.router, prefix="/posts", tags=["posts"])

    return app


app = create_app()
```

**Settings with Pydantic**:

```python
# src/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "My API"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/mydb"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
```
