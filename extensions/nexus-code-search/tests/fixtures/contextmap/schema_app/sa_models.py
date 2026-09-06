"""Schema accuracy fixture: SQLAlchemy models with relations."""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    posts = relationship("Post", back_populates="user")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="posts")
