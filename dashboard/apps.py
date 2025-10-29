from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'

    def ready(self):  # pragma: no cover - side effects only
        from . import signals  # noqa: F401
        from .dash_apps import real_time  # noqa: F401
