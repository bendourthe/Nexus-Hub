"""Database plumbing shared by the worker and its tasks (a hot file)."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ["DATABASE_URL"]
STATEMENT_TIMEOUT = int(os.getenv("DB_STATEMENT_TIMEOUT", "30"))

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def session_scope():
    """Return a fresh session; the caller owns its lifecycle."""
    return SessionLocal()
