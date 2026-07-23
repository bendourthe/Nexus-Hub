"""Worker entrypoint: configures the queue and schedules periodic work."""
import os

from db import session_scope
from models import Job
from tasks import ingest, notify

BROKER_URL = os.environ["CELERY_BROKER_URL"]
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))


def enqueue_pending():
    """Find pending jobs and dispatch an ingest task for each."""
    session = session_scope()
    pending = session.query(Job).filter_by(status="pending").all()
    for job in pending:
        ingest.delay(job.id)
    return len(pending)


def run_forever():
    """Simple poll loop: enqueue pending jobs, then notify on completion."""
    while True:
        count = enqueue_pending()
        if count:
            notify.delay("jobs.completed")
        _sleep(POLL_SECONDS)


def _sleep(seconds):
    import time

    time.sleep(seconds)
