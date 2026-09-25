from django.core.paginator import Paginator
from django.db.models import Count, Prefetch, Q
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from branch.models import Branch
from MobileApp.models import MobileBillingHistory, MobileControl, MobileProject
from app1.helpers import get_user_branch_ids

PROJECT_NAME = "TASK MST"

PAYMENT_STATUS_CHOICES = [choice[0] for choice in MobileBillingHistory.PAYMENT_STATUS_CHOICES]

ROWS_PER_PAGE_OPTIONS = ["10", "25", "50", "100", "all"]
DEFAULT_ROWS_PER_PAGE = "25"


def task_mst_report_view(request):
    allowed = request.session.get("allowed_menus") or []
    if not (request.user.is_authenticated and request.user.is_superuser) and "task_mst_report" not in allowed:
        return HttpResponseForbidden("Permission denied")

    now = timezone.now()

    # -------------------- QUERY PARAMS --------------------
    q            = request.GET.get("q", "").strip()
    branch       = request.GET.get("branch", "").strip()
    store        = request.GET.get("store", "").strip()
    licence_type = request.GET.get("licence_type", "").strip()
    status       = request.GET.get("status", "").strip()
    bill_status  = request.GET.get("bill_status", "").strip()
    payment      = request.GET.get("payment_status", "").strip()
    package      = request.GET.get("package", "").strip()
    date_from    = request.GET.get("date_from", "").strip()
    date_to      = request.GET.get("date_to", "").strip()
    expiry_from  = request.GET.get("expiry_from", "").strip()
    expiry_to    = request.GET.get("expiry_to", "").strip()
    sort         = request.GET.get("sort", "").strip()

    # -------------------- BASE QUERYSET --------------------
    project = MobileProject.objects.filter(project_name__iexact=PROJECT_NAME).first()

    controls = (
        MobileControl.objects
        .filter(project__project_name__iexact=PROJECT_NAME, licence_type__in=["new", "transfer"])
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
    if date_from:
        controls = controls.filter(created_date__date__gte=date_from)
    if date_to:
        controls = controls.filter(created_date__date__lte=date_to)
    if expiry_from:
        controls = controls.filter(expiry_date__date__gte=expiry_from)
    if expiry_to:
        controls = controls.filter(expiry_date__date__lte=expiry_to)

    # -------------------- LATEST BILLING RECORD PER CONTROL --------------------
    control_ids = list(controls.values_list("id", flat=True))
    latest_bills = {}
    if control_ids:
        bills = MobileBillingHistory.objects.filter(control_id__in=control_ids).order_by("control_id", "-created_at")
        for bh in bills:
            if bh.control_id not in latest_bills:
                latest_bills[bh.control_id] = bh

    if payment:
        matched_ids = [
            cid for cid, bh in latest_bills.items()
            if bh.payment_status == payment
        ]
        controls = controls.filter(id__in=matched_ids)

    # -------------------- SORTING --------------------
    controls = controls.order_by("expiry_date")

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
    branches = Branch.objects.all().order_by("name")
    if branch_ids is not None:
        branches = branches.filter(id__in=branch_ids)

    stores = (
        MobileControl.objects
        .filter(project__project_name__iexact=PROJECT_NAME, licence_type__in=["new", "transfer"], store__isnull=False)
        .order_by("store__name")
        .values("store_id", "store__name")
        .distinct()
    )
    if branch_ids is not None:
        stores = stores.filter(shop__branch_id__in=branch_ids)

    package_rows = (
        MobileControl.objects
        .filter(project__project_name__iexact=PROJECT_NAME, licence_type__in=["new", "transfer"])
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

    # -------------------- PAGINATION --------------------
    per_page = request.GET.get("rows", "").strip() or DEFAULT_ROWS_PER_PAGE
    if per_page not in ROWS_PER_PAGE_OPTIONS:
        per_page = DEFAULT_ROWS_PER_PAGE

    if per_page == "all":
        paginator = Paginator(rows, max(1, len(rows)))
    else:
        paginator = Paginator(rows, int(per_page))

    page_obj = paginator.get_page(request.GET.get("page", "1"))

    base_query = request.GET.copy()
    base_query.pop("page", None)

    return render(request, "task_mst_report.html", {
        "project": project,
        "page_obj": page_obj,
        "base_query": base_query,
        "sel_rows": per_page,
        "stats": stats,
        "branches": branches,
        "stores": stores,
        "licence_types": licence_types,
        "package_choices": package_choices,
        "payment_statuses": PAYMENT_STATUS_CHOICES,
        # Preserve selections
        "sel": {
            "q": q, "branch": branch, "store": store,
            "licence_type": licence_type, "status": status,
            "bill_status": bill_status, "payment_status": payment,
            "package": package, "date_from": date_from,
            "date_to": date_to, "expiry_from": expiry_from,
            "expiry_to": expiry_to, "sort": sort,
        },
    })