from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .services import log_model_delete, log_model_save

EXCLUDED_APPS = {
    "activity_log",
    "admin",
    "auth",
    "contenttypes",
    "sessions",
    "messages",
}


def _should_log(sender):
    return sender._meta.app_label not in EXCLUDED_APPS


@receiver(post_save, dispatch_uid="activity_log_post_save")
def on_post_save(sender, instance, created, **kwargs):
    if _should_log(sender):
        log_model_save(instance, created)


@receiver(post_delete, dispatch_uid="activity_log_post_delete")
def on_post_delete(sender, instance, **kwargs):
    if _should_log(sender):
        log_model_delete(instance)
