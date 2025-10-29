"""Django project package initialization."""

from .celery import app as celery_app  # pragma: no cover

__all__ = ('celery_app',)
