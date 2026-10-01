from datetime import timedelta

from django.core.paginator import Paginator
from django.db.models import Case, Count, F, IntegerField, Prefetch, Q, Value, When
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone

from branch.models import Branch
from MobileApp.models import MobileBillingHistory, MobileControl, MobileProject
from app1.helpers import get_user_branch_ids

MENU_ID = "new_licence_report"

# Every row in this report is a "New Licence" — the field is pinned, never a user filter.
LICENCE_TYPE = "new"

ROWS_PER_PAGE_OPTIONS = ["10", "25", "50", "100", "all"]
DEFAULT_ROWS_PER_PAGE = "25"

# Ordering buckets. Already-expired licences are sunk to the bottom; within the live
# band the licence expiring soonest is first. NULL expiry ("Unlimited") is the least
# urgent, so it trails the live band but still sits above the expired ones.
BUCKET_UNLIMITED = 2
BUCKET_EXPIRED = 3

# Allowlist: GET param -> relative-day window. "expired" is handled separately.
EXPIRY_OPTIONS = {
    "10": 10,
    "30": 30,
    "60": 60,
    "90": 90,
}

PAYMENT_STATUS_OPTIONS = [
    {"value": "Paid", "label": "Paid"},
    {"value": "Partially Paid", "label": "Partially Paid"},
    {"value": "Not Paid", "label": "Not Paid"},
    {"value": "Not Applicable", "label": "Not Applicable"},
]

MODULE_PREVIEW_LIMIT = 6


def _id_param(value):
    """Return a positive int, or None when the param is absent or not a valid pk.

    Guards the id-based filters: passing raw GET strings straight into
    .filter(project_id=...) makes a non-numeric value raise ValueError -> HTTP 500.
    """
    if not value or not value.isdigit():
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


def new_licence_report_view(request):
    allowed = request.session.get("allowed_menus") or []
    if not (request.user.is_authenticated and request.user.is_superuser) and MENU_ID not in allowed:
        return HttpResponseForbidden("Permission denied")

    now = timezone.now()

    # -------------------- QUERY PARAMS --------------------
    q             = request.GET.get("q", "").strip()
    project       = request.GET.get("project", "").strip()
    branch        = request.GET.get("branch", "").strip()
    store         = request.GET.get("store", "").strip()
    shop          = request.GET.get("shop", "").strip()
    package       = request.GET.get("package", "").strip()
    status        = request.GET.get("status", "").strip()
    bill_status   = request.GET.get("bill_status", "").strip()
    expiry        = request.GET.get("expiry", "").strip()
    payment       = request.GET.get("payment", "").strip()
    per_page      = request.GET.get("rows", "").strip() or DEFAULT_ROWS_PER_PAGE

    if per_page not in ROWS_PER_PAGE_OPTIONS:
        per_page = DEFAULT_ROWS_PER_PAGE
    if expiry not in EXPIRY_OPTIONS and expiry != "expired":
        expiry = ""
    if payment not in {p["value"] for p in PAYMENT_STATUS_OPTIONS}:
        payment = ""

    # Validate the id-based params once, but keep the original strings for the
    # template (the dropdowns compare against id|stringformat:"s").
    project_id = _id_param(project)
    branch_id = _id_param(branch)
    store_id = _id_param(store)
    shop_id = _id_param(shop)

    # -------------------- BASE QUERYSET --------------------
    # New licences across EVERY project (no project allow-list).
    controls = (
        MobileControl.objects
        .filter(licence_type=LICENCE_TYPE)
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
    if project_id:
        controls = controls.filter(project_id=project_id)
    if q:
        # Module-name search is resolved to control IDs in a separate query: joining
        # the reverse CustomPackageModule FK inside this filter would fan out rows and
        # force a SELECT DISTINCT that ORDER BY (a non-selected column) cannot satisfy.
        module_control_ids = (
            MobileControl.objects
            .filter(
                licence_type=LICENCE_TYPE,
                active_custom_package__modules__module_name__icontains=q,
            )
            .values_list("id", flat=True)
            .distinct()
        )
        controls = controls.filter(
            Q(customer_name__icontains=q)
            | Q(client_id__icontains=q)
            | Q(license_key__icontains=q)
            | Q(shop__name__icontains=q)
            | Q(shop__place__icontains=q)
            | Q(shop__email__icontains=q)
            | Q(shop__contact_no__icontains=q)
            | Q(shop__country__icontains=q)
            | Q(shop__client_id__icontains=q)
            | Q(store__name__icontains=q)
            | Q(store__store_id__icontains=q)
            | Q(active_custom_package__package_name__icontains=q)
            | Q(id__in=module_control_ids)
        )
    if branch_id:
        controls = controls.filter(shop__branch_id=branch_id)
    if store_id:
        controls = controls.filter(store_id=store_id)
    if shop_id:
        controls = controls.filter(shop_id=shop_id)
    if package:
        ptype, _, pid = package.partition("_")
        if ptype == "custom" and pid.isdigit():
            controls = controls.filter(active_custom_package_id=pid)
        elif ptype == "std" and pid.isdigit():
            controls = controls.filter(package_id=pid)
    if status:
        controls = controls.filter(status=(status == "active"))
    if bill_status:
        controls = controls.filter(bill_status=(bill_status == "billed"))
    if expiry == "expired":
        controls = controls.filter(expiry_date__lt=now)
    elif expiry:
        controls = controls.filter(
            expiry_date__gte=now,
            expiry_date__lte=now + timedelta(days=EXPIRY_OPTIONS[expiry]),
        )

    # -------------------- SORTING --------------------
    # Live licences first (soonest expiry leading), unlimited next, already expired
    # sunk to the bottom. customer_name is a stable tiebreaker so pagination does not
    # reshuffle rows that share a bucket and an expiry date.
    controls = (
        controls
        .annotate(
            expiry_bucket=Case(
                When(expiry_date__isnull=True, then=Value(BUCKET_UNLIMITED)),
                When(expiry_date__lt=now, then=Value(BUCKET_EXPIRED)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        .order_by("expiry_bucket", F("expiry_date").asc(nulls_last=True), "customer_name")
    )

    # -------------------- LATEST BILLING RECORD PER CONTROL --------------------
    control_ids = list(controls.values_list("id", flat=True))
    latest_bills = {}
    if control_ids:
        bills = MobileBillingHistory.objects.filter(control_id__in=control_ids).order_by("control_id", "-created_at")
        for bh in bills:
            if bh.control_id not in latest_bills:
                latest_bills[bh.control_id] = bh

    # Payment-status filter applies to the latest billing record only, so it is
    # evaluated in Python after the per-control lookup.
    if payment:
        kept = [cid for cid, bh in latest_bills.items() if bh.payment_status == payment]
        controls = controls.filter(id__in=kept)

    # -------------------- BUILD ROW DATA --------------------
    rows = []
    total_registered = 0
    total_balance = 0
    expiring_soon = 0
    expired_count = 0
    soon_cutoff = now + timedelta(days=30)

    for c in controls:
        balance = max(0, c.login_limit - c.registered_count)
        total_registered += c.registered_count
        total_balance += balance
        delta = (c.expiry_date - now) if c.expiry_date else None
        is_expired = (delta is not None and delta.total_seconds() <= 0)
        if is_expired:
            expired_count += 1
        elif c.expiry_date and c.expiry_date <= soon_cutoff:
            expiring_soon += 1

        module_names = (
            [m.module_name for m in c.active_custom_package.modules.all()]
            if c.active_custom_package else []
        )

        rows.append({
            "control": c,
            "reg_count": c.registered_count,
            "balance": balance,
            "remaining_days": delta.days if delta is not None else None,
            "is_expired": is_expired,
            "has_expiry": c.expiry_date is not None,
            "latest_bill": latest_bills.get(c.id),
            "package_name": (
                f"[Custom] {c.active_custom_package.package_name}"
                if c.active_custom_package
                else (c.package.package_name if c.package else None)
            ),
            "is_custom_package": bool(c.active_custom_package),
            "module_names": module_names,
            "module_preview": module_names[:MODULE_PREVIEW_LIMIT],
            "module_overflow": max(0, len(module_names) - MODULE_PREVIEW_LIMIT),
            "device_names": [
                (d.device_name or d.device_id) for d in c.active_devices.all()
            ],
            "branch_name": (
                c.shop.branch.name if c.shop and c.shop.branch
                else (c.branch.name if c.branch else None)
            ),
            "branch_place": (
                c.shop.branch.place if c.shop and c.shop.branch
                else (c.branch.place if c.branch else None)
            ),
            "contact_email": c.shop.email if c.shop else None,
            "contact_no": c.shop.contact_no if c.shop else None,
            "contact_country": c.shop.country if c.shop else None,
            "contact_place": c.shop.place if c.shop else None,
        })

    # -------------------- FILTER DROPDOWNS --------------------
    projects = (
        MobileProject.objects
        .filter(controls__licence_type=LICENCE_TYPE)
        .order_by("project_name")
        .distinct()
    )

    branches = Branch.objects.all().order_by("name")
    if branch_ids is not None:
        branches = branches.filter(id__in=branch_ids)

    new_controls = MobileControl.objects.filter(licence_type=LICENCE_TYPE)
    if branch_ids is not None:
        new_controls = new_controls.filter(shop__branch_id__in=branch_ids)

    stores = (
        new_controls
        .filter(store__isnull=False)
        .order_by("store__name")
        .values("store_id", "store__name")
        .distinct()
    )

    shops = (
        new_controls
        .filter(shop__isnull=False)
        .order_by("shop__name")
        .values("shop_id", "shop__name", "shop__place")
        .distinct()
    )

    package_rows = new_controls.prefetch_related("package", "active_custom_package")
    package_options = {}
    for c in package_rows:
        if c.active_custom_package and c.active_custom_package_id:
            package_options.setdefault(
                f"custom_{c.active_custom_package.id}",
                f"[Custom] {c.active_custom_package.package_name}",
            )
        elif c.package_id:
            package_options.setdefault(f"std_{c.package.id}", c.package.package_name)
    package_choices = sorted(package_options.items(), key=lambda kv: kv[1].lower())

    stats = {
        "total": len(rows),
        "active": sum(1 for r in rows if r["control"].status),
        "inactive": sum(1 for r in rows if not r["control"].status),
        "billed": sum(1 for r in rows if r["control"].bill_status),
        "unbilled": sum(1 for r in rows if not r["control"].bill_status),
        "expiring_soon": expiring_soon,
        "expired": expired_count,
        "registered": total_registered,
        "balance": total_balance,
    }

    # -------------------- PAGINATION --------------------
    if per_page == "all":
        paginator = Paginator(rows, max(1, len(rows)))
    else:
        paginator = Paginator(rows, int(per_page))

    page_obj = paginator.get_page(request.GET.get("page", "1"))

    base_query = request.GET.copy()
    base_query.pop("page", None)

    return render(request, "new_licence_report.html", {
        "projects": projects,
        "page_obj": page_obj,
        "base_query": base_query,
        "sel_rows": per_page,
        "stats": stats,
        "branches": branches,
        "stores": stores,
        "shops": shops,
        "package_choices": package_choices,
        "expiry_options": sorted(EXPIRY_OPTIONS.keys(), key=int),
        "payment_options": PAYMENT_STATUS_OPTIONS,
        "sel": {
            "q": q, "project": project, "branch": branch, "store": store,
            "shop": shop, "package": package, "status": status,
            "bill_status": bill_status, "expiry": expiry,
            "payment": payment,
        },
    })
