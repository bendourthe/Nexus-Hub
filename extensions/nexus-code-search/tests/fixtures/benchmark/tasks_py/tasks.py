"""Celery task definitions for the worker."""
import os

from celery import shared_task

from db import session_scope
from models import Job, JobEvent, Subscriber

SMTP_URL = os.environ["SMTP_URL"]
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))


@shared_task
def ingest(job_id):
    """Run the ingestion pipeline for a job and record progress events."""
    session = session_scope()
    job = session.query(Job).get(job_id)
    job.status = "running"
    session.add(JobEvent(job_id=job_id, message="ingestion started"))
    session.commit()
    return {"job": job_id, "status": job.status}


@shared_task
def notify(topic):
    """Email every subscriber to a topic that a job completed."""
    session = session_scope()
    subscribers = session.query(Subscriber).filter_by(topic=topic).all()
    for subscriber in subscribers:
        _send_email(subscriber.email, topic)
    return len(subscribers)


def _send_email(address, topic):
    """Pretend to send mail via the configured SMTP relay."""
    return {"to": address, "topic": topic, "relay": SMTP_URL.split("@")[-1]}
