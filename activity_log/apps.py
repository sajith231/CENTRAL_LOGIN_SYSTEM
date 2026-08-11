from django.apps import AppConfig


class ActivityLogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'activity_log'
    verbose_name = 'Activity Log'

    def ready(self):
        from . import signals  # noqa: F401
