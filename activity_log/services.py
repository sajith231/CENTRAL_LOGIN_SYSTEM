from django.utils import timezone


def get_actor(request):
    """Return (user_name, user_email, user_type) for the current request actor,
    or None when the request is anonymous."""
    if request.user.is_authenticated and request.user.is_superuser:
        return (request.user.username, request.user.email or "", "Super Admin")
    if request.session.get("custom_user_id"):
        return (
            request.session.get("custom_user_name") or "",
            request.session.get("custom_user_email") or "",
            request.session.get("custom_user_level") or "User",
        )
    return None


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def create_log(actor, action, method="", url="", ip_address=None, details="",
               model_name="", object_id=""):
    """Persist one activity log row using a pre-built actor tuple."""
    from .models import ActivityLog

    if not actor:
        return None

    user_name, user_email, user_type = actor
    return ActivityLog.objects.create(
        user_name=user_name,
        user_email=user_email or None,
        user_type=user_type,
        action=action,
        details=details,
        model_name=model_name,
        object_id=str(object_id or ""),
        method=method.upper(),
        url=url,
        ip_address=ip_address,
    )


def log_activity(request, action, method=None, url=None, ip_address=None, details=""):
    """Log an activity row derived from the current request's actor."""
    return create_log(
        get_actor(request),
        action=action,
        method=method or request.method,
        url=url or request.path,
        ip_address=ip_address or get_client_ip(request),
        details=details,
    )


def _model_label(model):
    """Friendly model name, e.g. 'Mobile Control' for MobileControl."""
    verbose = getattr(model._meta, "verbose_name", "") or model._meta.model_name
    return str(verbose).title()


def _object_details(instance):
    """Short human-readable identifier for a saved/deleted instance."""
    text = str(instance)
    if len(text) > 250:
        text = text[:250] + "..."
    return text


def log_model_save(instance, created):
    """Called from post_save signal. Returns the log row or None."""
    from .context import get_current_actor

    actor = get_current_actor()
    if not actor:
        return None

    action = "Added" if created else "Updated"
    return create_log(
        actor,
        action=action,
        url="/",
        details=_object_details(instance),
        model_name=_model_label(instance),
        object_id=instance.pk,
    )


def log_model_delete(instance):
    """Called from post_delete signal. Returns the log row or None."""
    from .context import get_current_actor

    actor = get_current_actor()
    if not actor:
        return None

    return create_log(
        actor,
        action="Deleted",
        url="/",
        details=_object_details(instance),
        model_name=_model_label(instance),
        object_id=instance.pk,
    )


def get_all_activity_users():
    """Distinct usernames present in the log, ordered by name."""
    from .models import ActivityLog

    return list(
        ActivityLog.objects.values_list("user_name", flat=True)
        .order_by("user_name")
        .distinct()
    )


def delete_month(year, month):
    """Delete every log row belonging to the given month. Returns row count."""
    from .models import ActivityLog

    queryset = ActivityLog.objects.filter(created_at__year=year, created_at__month=month)
    deleted, _ = queryset.delete()
    return deleted
