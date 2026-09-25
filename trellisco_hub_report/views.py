from django.db.models import Count, Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from branch.models import Branch
from MobileApp.models import MobileBillingHistory, MobileControl, MobileProject
from app1.helpers import get_user_branch_ids

PROJECT_NAMES = [
    "TRELLISCO",
    "VenueKart",
    "Melone",
    "Melone Stay",
    "Melone Lite Pro",
    "Melone Lite",
    "Cluadius",
]


def trellisco_hub_report_view(request):
    allowed = request.session.get("allowed_menus") or []
    if not (request.user.is_authenticated and request.user.is_superuser) and "trellisco_hub_report" not in allowed:
        return HttpResponseForbidden("Permission denied")

    now = timezone.now()

    # -------------------- QUERY PARAMS --------------------
    q            = request.GET.get("q", "").strip()
    project      = request.GET.get("project", "").strip()
    branch       = request.GET.get("branch", "").strip()
    store        = request.GET.get("store", "").strip()
    licence_type = request.GET.get("licence_type", "").strip()
    status       = request.GET.get("status", "").strip()
    bill_status  = request.GET.get("bill_status", "").strip()
    package      = request.GET.get("package", "").strip()

    # -------------------- BASE QUERYSET --------------------
    controls = (
        MobileControl.objects
        .filter(
            project__project_name__in=PROJECT_NAMES,
            licence_type__in=["new", "transfer"],
        )
        .select_related(
            "project",
            "store",
            "shop",
            "shop__store",
            "shop__branch",
            "package",
            "active_custom_package",
        )
        .prefetch_related(Prefetch("active_custom_package__modules"), "active_devices")
        .annotate(registered_count=Count("active_devices", distinct=True))
    )

    # Branch restriction for non-superuser custom users
    branch_ids = get_user_branch_ids(request)
    if branch_ids is not None:
        controls = controls.filter(shop__branch_id__in=branch_ids)

    # -------------------- APPLY FILTERS --------------------
    if project:
        controls = controls.filter(project_id=project)
    if q:
        controls = controls.filter(
            Q(customer_name__icontains=q)
            | Q(client_id__icontains=q)
            | Q(license_key__icontains=q)
            | Q(shop__name__icontains=q)
            | Q(shop__place__icontains=q)
            | Q(store__name__icontains=q)
        )
    if branch:
        controls = controls.filter(shop__branch_id=branch)
    if store:
        controls = controls.filter(store_id=store)
    if licence_type:
        controls = controls.filter(licence_type=licence_type)
    if status:
        controls = controls.filter(status=(status == "active"))
    if bill_status:
        controls = controls.filter(bill_status=(bill_status == "billed"))
    if package:
        controls = controls.filter(Q(package_id=package) | Q(active_custom_package_id=package))

    # -------------------- LATEST BILLING RECORD PER CONTROL --------------------
    control_ids = list(controls.values_list("id", flat=True))
    latest_bills = {}
    if control_ids:
        bills = MobileBillingHistory.objects.filter(control_id__in=control_ids).order_by("control_id", "-created_at")
        for bh in bills:
            if bh.control_id not in latest_bills:
                latest_bills[bh.control_id] = bh

    # -------------------- SORTING --------------------
    controls = controls.order_by("project__project_name", "customer_name")

    # -------------------- BUILD ROW DATA --------------------
    rows = []
    total_registered = 0
    total_balance = 0
    for c in controls:
        balance = max(0, c.login_limit - c.registered_count)
        total_registered += c.registered_count
        total_balance += balance
        delta = (c.expiry_date - now) if c.expiry_date else None
        rows.append({
            "control": c,
            "reg_count": c.registered_count,
            "balance": balance,
            "remaining_days": delta.days if delta is not None else None,
            "is_expired": (delta is not None and delta.total_seconds() <= 0),
            "has_expiry": c.expiry_date is not None,
            "latest_bill": latest_bills.get(c.id),
            "package_name": (
                f"[Custom] {c.active_custom_package.package_name}"
                if c.active_custom_package
                else (c.package.package_name if c.package else None)
            ),
            "module_names": [
                m.module_name for m in c.active_custom_package.modules.all()
            ] if c.active_custom_package else [],
            "device_names": [
                (d.device_name or d.device_id) for d in c.active_devices.all()
            ],
        })

    # -------------------- FILTER DROPDOWNS --------------------
    projects = (
        MobileProject.objects
        .filter(project_name__in=PROJECT_NAMES)
        .order_by("project_name")
    )

    branches = Branch.objects.all().order_by("name")
    if branch_ids is not None:
        branches = branches.filter(id__in=branch_ids)

    stores = (
        MobileControl.objects
        .filter(
            project__project_name__in=PROJECT_NAMES,
            licence_type__in=["new", "transfer"],
            store__isnull=False,
        )
        .order_by("store__name")
        .values("store_id", "store__name")
        .distinct()
    )
    if branch_ids is not None:
        stores = stores.filter(shop__branch_id__in=branch_ids)

    package_rows = (
        MobileControl.objects
        .filter(
            project__project_name__in=PROJECT_NAMES,
            licence_type__in=["new", "transfer"],
        )
        .prefetch_related("package", "active_custom_package")
    )
    package_options = {}
    for c in package_rows:
        if c.active_custom_package and c.active_custom_package_id:
            package_options.setdefault(f"custom_{c.active_custom_package.id}", f"[Custom] {c.active_custom_package.package_name}")
        elif c.package_id:
            package_options.setdefault(f"std_{c.package.id}", c.package.package_name)
    package_choices = sorted(package_options.items(), key=lambda kv: kv[1].lower())

    licence_types = [
        {"value": "new", "label": "New Licence"},
        {"value": "transfer", "label": "Transfer Licence"},
    ]

    stats = {
        "total": len(rows),
        "active": sum(1 for r in rows if r["control"].status),
        "inactive": sum(1 for r in rows if not r["control"].status),
        "billed": sum(1 for r in rows if r["control"].bill_status),
        "unbilled": sum(1 for r in rows if not r["control"].bill_status),
        "registered": total_registered,
        "balance": total_balance,
    }

    return render(request, "trellisco_hub_report.html", {
        "projects": projects,
        "rows": rows,
        "stats": stats,
        "branches": branches,
        "stores": stores,
        "licence_types": licence_types,
        "package_choices": package_choices,
        "sel": {
            "q": q, "project": project, "branch": branch,
            "store": store, "licence_type": licence_type,
            "status": status, "bill_status": bill_status,
            "package": package,
        },
    })