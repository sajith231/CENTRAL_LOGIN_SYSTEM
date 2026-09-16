from datetime import timedelta

from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from MobileApp.models import MobileControl


def upcoming_expiry_view(request):
    allowed = request.session.get("allowed_menus") or []
    # Superuser, or a custom user granted the 'upcoming_expiry' menu
    if not (request.user.is_authenticated and request.user.is_superuser) and "upcoming_expiry" not in allowed:
        return HttpResponseForbidden("Permission denied")

    now = timezone.now()

    # Upcoming expiries inside the next 30 days (NULL expiry dates are excluded by __gte)
    # Only New and Transfer licences — no Developer licences
    controls = (
        MobileControl.objects
        .filter(
            expiry_date__gte=now,
            expiry_date__lte=now + timedelta(days=30),
            licence_type__in=["new", "transfer"],
        )
        .select_related("project", "shop", "shop__store", "shop__branch", "package", "active_custom_package")
        .order_by("expiry_date")
    )

    for control in controls:
        control.registered_count = control.active_devices.count()
        control.balance_count = control.login_limit - control.registered_count
        delta = control.expiry_date - now
        control.remaining_days = delta.days
        control.is_expired = delta.total_seconds() <= 0

    return render(request, "upcoming_expiry.html", {
        "controls": controls,
        "total_count": controls.count(),
    })