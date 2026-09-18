from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from branch.models import Branch
from MobileApp.models import MobileControl
from app1.helpers import get_user_branch_ids


def expired_key_report_view(request):
    allowed = request.session.get("allowed_menus") or []
    # Superuser, or a custom user granted the 'expired_key_report' menu
    if not (request.user.is_authenticated and request.user.is_superuser) and "expired_key_report" not in allowed:
        return HttpResponseForbidden("Permission denied")

    now = timezone.now()

    branch = request.GET.get("branch", "").strip()

    # Custom (non-superuser) users only see their assigned branches
    branch_ids = get_user_branch_ids(request)

    # Fully expired licences only — New and Transfer types only
    controls = (
        MobileControl.objects
        .filter(
            expiry_date__lt=now,
            licence_type__in=["new", "transfer"],
        )
        .select_related("project", "shop", "shop__store", "shop__branch", "package", "active_custom_package")
        .order_by("-expiry_date")
    )

    if branch_ids is not None:
        controls = controls.filter(shop__branch_id__in=branch_ids)

    if branch:
        controls = controls.filter(shop__branch_id=branch)

    for control in controls:
        control.registered_count = control.active_devices.count()
        control.balance_count = control.login_limit - control.registered_count
        delta = now - control.expiry_date
        control.days_past = delta.days

    branches = Branch.objects.all().order_by("name")
    if branch_ids is not None:
        branches = branches.filter(id__in=branch_ids)

    return render(request, "expired_key_report.html", {
        "controls": controls,
        "total_count": controls.count(),
        "branches": branches,
        "selected_branch": branch,
    })