"""Celery application configuration for the Django project."""

import os
from datetime import timedelta

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject.settings')

app = Celery('DjangoProject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.on_after_configure.connect  # pragma: no cover - runtime hook
def setup_periodic_tasks(sender, **kwargs):
    from dashboard import tasks

    sender.add_periodic_task(
        timedelta(seconds=30),
        tasks.fetch_weather.s(),
        name='fetch weather',
    )
    sender.add_periodic_task(
        timedelta(seconds=20),
        tasks.fetch_finance_quotes.s(),
        name='fetch finance',
    )
    sender.add_periodic_task(
        timedelta(seconds=15),
        tasks.fetch_public_transport_data.s(),
        name='fetch traffic',
    )
