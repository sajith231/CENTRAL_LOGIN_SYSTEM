from datetime import timedelta

from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from branch.models import Branch
from MobileApp.models import MobileControl, MobileProject
from app1.helpers import get_user_branch_ids

# Projects that have their own dedicated report menu and must not appear here
EXCLUDED_PROJECT_NAMES = ["TASK MST"]


def upcoming_expiry_view(request):
    """Upcoming Expiry – licences expiring soon for non T-ERP projects."""
    return render_upcoming_report(request, terp_only=False)


def terp_upcoming_expiry_view(request):
    """TERP Upcoming Expiry – licences expiring soon for T-ERP enabled projects."""
    return render_upcoming_report(request, terp_only=True)


def render_upcoming_report(request, terp_only=False):
    menu_id = "terp_upcoming_expiry" if terp_only else "upcoming_expiry"
    allowed = request.session.get("allowed_menus") or []
    # Superuser, or a custom user granted the matching report menu
    if not (request.user.is_authenticated and request.user.is_superuser) and menu_id not in allowed:
        return HttpResponseForbidden("Permission denied")

    now = timezone.now()

    branch = request.GET.get("branch", "").strip()
    project = request.GET.get("project", "").strip()

    # Custom (non-superuser) users only see their assigned branches
    branch_ids = get_user_branch_ids(request)

    # Upcoming expiries inside the next 30 days (NULL expiry dates are excluded by __gte),
    # scoped to the menu they belong to: the TERP report shows T-ERP projects
    # (Developer/Trial licences), the main report shows only non T-ERP projects
    licence_types = ["new", "trial", "transfer", "developer"] if terp_only else ["new", "trial", "transfer"]
    controls = (
        MobileControl.objects
        .filter(
            expiry_date__gte=now,
            expiry_date__lte=now + timedelta(days=30),
            licence_type__in=licence_types,
            project__t_erp=terp_only,
        )
        .select_related("project", "shop", "shop__store", "shop__branch", "package", "active_custom_package")
        .order_by("expiry_date")
    )

    # Projects with their own dedicated report (e.g. TASK MST) are not listed here
    excluded_project_ids = list(
        MobileProject.objects.filter(project_name__in=EXCLUDED_PROJECT_NAMES).values_list("id", flat=True)
    )
    if excluded_project_ids:
        controls = controls.exclude(project_id__in=excluded_project_ids)

    if branch_ids is not None:
        controls = controls.filter(shop__branch_id__in=branch_ids)

    if branch:
        controls = controls.filter(shop__branch_id=branch)

    projects = MobileProject.objects.filter(
        controls__in=controls,
    ).distinct().order_by("project_name")

    if project:
        controls = controls.filter(project_id=project)

    for control in controls:
        control.registered_count = control.active_devices.count()
        control.balance_count = control.login_limit - control.registered_count
        delta = control.expiry_date - now
        control.remaining_days = delta.days
        control.is_expired = delta.total_seconds() <= 0

    branches = Branch.objects.all().order_by("name")
    if branch_ids is not None:
        branches = branches.filter(id__in=branch_ids)

    return render(request, "upcoming_expiry.html", {
        "controls": controls,
        "total_count": controls.count(),
        "branches": branches,
        "selected_branch": branch,
        "projects": projects,
        "selected_project": project,
        "terp_mode": terp_only,
    })
