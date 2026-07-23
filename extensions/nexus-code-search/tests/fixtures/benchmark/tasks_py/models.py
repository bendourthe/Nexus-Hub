"""ORM models for the ingestion / notification worker."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from db import Base


class Job(Base):
    """A unit of background work with a status and result."""

    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    kind = Column(String)
    status = Column(String)
    created_at = Column(DateTime)
    events = relationship("JobEvent", back_populates="job")


class JobEvent(Base):
    """An audit event recorded as a job progresses."""

    __tablename__ = "job_events"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    message = Column(String)
    job = relationship("Job", back_populates="events")


class Subscriber(Base):
    """A recipient notified when a job of interest completes."""

    __tablename__ = "subscribers"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    topic = Column(String)
