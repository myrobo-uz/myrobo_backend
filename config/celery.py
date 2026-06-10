import os

from celery import Celery
from celery.signals import worker_ready

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=2,
    task_compression="gzip",
    result_compression="gzip",
    result_expires=3600,
    broker_connection_retry_on_startup=True,
    broker_pool_limit=10,
)


@worker_ready.connect
def _on_worker_ready(**_):
    pass
