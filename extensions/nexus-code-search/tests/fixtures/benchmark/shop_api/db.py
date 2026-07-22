"""Database session + engine plumbing shared across the shop service.

This module is imported by almost every other module, which is what makes it a
hot file. It sets up the SQLAlchemy engine, a scoped session factory, and a
declarative base that the models inherit from.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))

engine = create_engine(DATABASE_URL, pool_size=POOL_SIZE, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def get_session():
    """Yield a scoped session and always close it afterwards."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def healthcheck() -> bool:
    """Return True when the database answers a trivial query."""
    with engine.connect() as connection:
        return connection.execute("SELECT 1").scalar() == 1
