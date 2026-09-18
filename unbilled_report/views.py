from django.db.models import OuterRef, Subquery
from django.http import HttpResponseForbidden
from django.shortcuts import render

from branch.models import Branch
from MobileApp.models import MobileBillingHistory, MobileControl
from app1.helpers import get_user_branch_ids


def unbilled_report(request):
    allowed = request.session.get("allowed_menus") or []
    # Superuser, or a custom user granted the 'unbilled_report' menu
    if not (request.user.is_authenticated and request.user.is_superuser) and "unbilled_report" not in allowed:
        return HttpResponseForbidden("Permission denied")

    latest_payment_sub = MobileBillingHistory.objects.filter(
        control=OuterRef('pk'),
        bill_status=False,
    ).order_by('-created_at').values('payment_status')[:1]

    # Custom (non-superuser) users only see their assigned branches
    branch_ids = get_user_branch_ids(request)

    controls = (
        MobileControl.objects
        .filter(bill_status=False, licence_type__in=['new', 'transfer'])
        .annotate(latest_payment_status=Subquery(latest_payment_sub))
        .select_related('project', 'package', 'active_custom_package', 'shop__branch', 'store')
        .order_by('created_date')
    )

    if branch_ids is not None:
        controls = controls.filter(shop__branch_id__in=branch_ids)

    branches = Branch.objects.all().order_by('name')
    if branch_ids is not None:
        branches = branches.filter(id__in=branch_ids)

    licence_types = [
        {'value': 'new', 'label': 'New'},
        {'value': 'transfer', 'label': 'Transfer'},
    ]

    return render(request, "unbilled_report.html", {
        "controls": controls,
        "branches": branches,
        "licence_types": licence_types,
    })