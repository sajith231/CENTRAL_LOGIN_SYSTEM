from django.db.models import OuterRef, Subquery
from django.http import HttpResponseForbidden
from django.shortcuts import render

from branch.models import Branch
from MobileApp.models import MobileBillingHistory, MobileControl, MobileProject
from app1.helpers import get_user_branch_ids


def unbilled_report(request):
    """Unbilled Report – unbilled licences of non T-ERP projects."""
    return render_unbilled_report(request, terp_only=False)


def terp_unbilled_report(request):
    """TERP Unbilled Report – unbilled licences of T-ERP enabled projects."""
    return render_unbilled_report(request, terp_only=True)


def render_unbilled_report(request, terp_only=False):
    menu_id = "terp_unbilled_report" if terp_only else "unbilled_report"
    allowed = request.session.get("allowed_menus") or []
    # Superuser, or a custom user granted the matching report menu
    if not (request.user.is_authenticated and request.user.is_superuser) and menu_id not in allowed:
        return HttpResponseForbidden("Permission denied")

    latest_payment_sub = MobileBillingHistory.objects.filter(
        control=OuterRef('pk'),
        bill_status=False,
    ).order_by('-created_at').values('payment_status')[:1]

    # Custom (non-superuser) users only see their assigned branches
    branch_ids = get_user_branch_ids(request)

    # Scoped to the menu they belong to: the TERP report shows T-ERP projects
    # (Developer/Trial licences), the main report shows only non T-ERP projects
    licence_type_values = ['new', 'trial', 'transfer', 'developer'] if terp_only else ['new', 'trial', 'transfer']
    controls = (
        MobileControl.objects
        .filter(bill_status=False, licence_type__in=licence_type_values, project__t_erp=terp_only)
        .annotate(latest_payment_status=Subquery(latest_payment_sub))
        .select_related('project', 'package', 'active_custom_package', 'shop__branch', 'store')
        .order_by('created_date')
    )

    if branch_ids is not None:
        controls = controls.filter(shop__branch_id__in=branch_ids)

    branches = Branch.objects.all().order_by('name')
    if branch_ids is not None:
        branches = branches.filter(id__in=branch_ids)

    projects = MobileProject.objects.filter(
        controls__in=controls,
    ).distinct().order_by('project_name')

    licence_types = [
        {'value': 'new', 'label': 'New'},
        {'value': 'trial', 'label': 'Trial'},
        {'value': 'transfer', 'label': 'Transfer'},
    ]
    if terp_only:
        licence_types.append({'value': 'developer', 'label': 'Developer'})

    return render(request, "unbilled_report.html", {
        "controls": controls,
        "branches": branches,
        "projects": projects,
        "licence_types": licence_types,
        "terp_mode": terp_only,
    })
