"""Events accuracy fixture: a Celery task + a decoy plain function."""
from celery import shared_task


@shared_task
def send_email(to):
    return to


def not_a_task():
    return 0
