import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

app = Celery("server")


app.conf.broker_url = "redis://localhost:6379/0"
app.conf.result_backend = "redis://localhost:6379/0"


app.autodiscover_tasks()


app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
)
