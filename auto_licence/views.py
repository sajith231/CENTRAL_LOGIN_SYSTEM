import json
from datetime import timedelta

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from MobileApp.models import MobileProject, MobileControl, MobileBillingHistory
from StoreShop.models import Store, Shop
from branch.models import Branch, CURRENCY_CODES

DEFAULT_USERS = 50
DEFAULT_VALIDITY_DAYS = 30


def _is_super_level_user(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return True
    if request.session.get("custom_user_level") == "Super User":
        return True
    return False


@csrf_exempt
@require_http_methods(["POST"])
def api_licence_create(request, endpoint):
    """
    POST API: Creates a DEMO licence along with its Corporate (Store) and
    Company (Shop) automatically — all in a single request.

    Body:
    {
        "branch": "<optional: branch id or name>",   // else project.branch, else first branch
        "corporate": { "name": "Corporate Name", "place": "Optional place" },
        "company": {
            "name": "Company Name",
            "place": "Optional place",
            "email": "company@domain.com",     // required — client_id is set from this
            "contact_no": "Optional",
            "country": "India",
            "currency_code": "Optional"
        }
    }

    Defaults applied automatically:
        - client_id   = company email
        - users       = 50
        - validity    = 30 days
        - package     = None (no package selected)
        - billing     = auto-created (Billed / Not Paid)
        - type        = DEMO
        - once per company per project (duplicates rejected)
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"success": False, "error": "Invalid JSON body"}, status=400)

    # ---------------- PROJECT ----------------
    try:
        project = MobileProject.objects.get(api_endpoint=endpoint)
    except MobileProject.DoesNotExist:
        return JsonResponse({"success": False, "error": "Project not found"}, status=404)

    # ---------------- CORPORATE / COMPANY ----------------
    corporate = payload.get("corporate") or {}
    company = payload.get("company") or {}

    corporate_name = str(corporate.get("name") or "").strip()
    corporate_place = str(corporate.get("place") or "").strip()
    company_name = str(company.get("name") or "").strip()
    company_place = str(company.get("place") or "").strip()
    company_email = str(company.get("email") or "").strip()
    company_contact = str(company.get("contact_no") or "").strip()
    country = str(company.get("country") or "India").strip()
    currency_code = str(company.get("currency_code") or "").strip()
    is_active = bool(company.get("is_active", True))

    if not corporate_name:
        return JsonResponse({"success": False, "error": "corporate.name is required"}, status=400)
    if not company_name:
        return JsonResponse({"success": False, "error": "company.name is required"}, status=400)

    # client_id is automatically set from the company email (this API only)
    if not company_email:
        return JsonResponse({"success": False, "error": "company.email is required (client_id is set from it)"}, status=400)
    if len(company_email) > 50:
        return JsonResponse({"success": False, "error": "company.email is too long to be used as client_id (max 50 chars)"}, status=400)

    if not currency_code:
        currency_code = CURRENCY_CODES.get(country, "INR")

    # ---------------- BRANCH (always "IMC Developments") ----------------
    branch = Branch.objects.filter(name__iexact="IMC Developments").first()
    if branch is None:
        return JsonResponse({"success": False, "error": "Default branch 'IMC Developments' not found."}, status=400)

    # ---------------- DUPLICATE CHECKS ----------------
    if company_email and Shop.objects.filter(email=company_email).exists():
        return JsonResponse({"success": False, "error": f"The email '{company_email}' is already used by another company"}, status=400)

    already_exists = MobileControl.objects.filter(
        project=project
    ).filter(
        Q(customer_name__iexact=company_name) |
        Q(client_id=company_email)
    ).exists()

    if already_exists:
        return JsonResponse({
            "success": False,
            "error": f"A licence already exists for the company '{company_name}' under the project '{project.project_name}'"
        }, status=409)

    # ---------------- CREATE CORPORATE (Store) ----------------
    store = Store.objects.create(
        name=corporate_name,
        branch=branch,
        place=corporate_place,
        is_demo=True,
        created_by=request.user if request.user.is_authenticated else None,
        created_by_name="Licence Create API",
    )

    # ---------------- CREATE COMPANY (Shop) ----------------
    shop = Shop.objects.create(
        store=store,
        branch=branch,
        name=company_name,
        place=company_place,
        email=company_email,
        contact_no=company_contact,
        country=country,
        currency_code=currency_code,
        client_id=company_email,
        is_active=is_active,
        is_demo=True,
        created_by=request.user if request.user.is_authenticated else None,
        created_by_name="Licence Create API",
    )

    # ---------------- CREATE DEMO LICENCE (MobileControl) ----------------
    expiry_date = timezone.now() + timedelta(days=DEFAULT_VALIDITY_DAYS)

    control = MobileControl.objects.create(
        project=project,
        store=store,
        shop=shop,
        customer_name=company_name,
        client_id=shop.client_id,
        login_limit=DEFAULT_USERS,
        licence_type="demo",
        package=None,
        active_custom_package=None,
        branch=branch,
        status=True,
        bill_status=True,
        expiry_date=expiry_date,
    )

    # ---------------- AUTO BILLING ----------------
    MobileBillingHistory.objects.create(
        control=control,
        package=None,
        custom_package=None,
        extended_days=DEFAULT_VALIDITY_DAYS,
        extended_login_limit=DEFAULT_USERS,
        old_expiry_date=None,
        new_expiry_date=control.expiry_date,
        old_login_limit=0,
        new_login_limit=DEFAULT_USERS,
        bill_status=True,
        payment_status="Not Paid",
        remark="Demo licence auto-created via Licence Create API",
        added_by="Licence Create API",
    )

    return JsonResponse({
        "success": True,
        "message": "Demo licence created successfully",
        "licence_type": control.licence_type,
        "customer_name": control.customer_name,
        "client_id": control.client_id,
        "license_key": control.license_key,
        "login_limit": control.login_limit,
        "expiry_date": control.expiry_date.isoformat(),
        "branch": branch.name,
        "corporate": {"name": store.name, "place": store.place, "store_id": store.store_id},
        "company": {
            "name": shop.name,
            "place": shop.place,
            "email": shop.email,
            "contact_no": shop.contact_no,
            "country": shop.country,
            "currency_code": shop.currency_code,
            "client_id": shop.client_id,
        },
        "billing": {
            "bill_status": True,
            "payment_status": "Not Paid",
            "extended_days": DEFAULT_VALIDITY_DAYS,
            "new_expiry_date": control.expiry_date.isoformat(),
            "new_login_limit": DEFAULT_USERS,
        },
    }, status=201)


@require_POST
def convert_demo_to_main(request, pk):
    """Super User only: converts a DEMO licence to a Main licence.
    The linked Corporate (Store) and Company (Shop) become visible in the
    Corporate / Company tables after conversion."""
    if not _is_super_level_user(request):
        messages.error(request, "Permission denied. Only Super Users can convert a Demo licence to Main.")
        return redirect("MobileApp:mobile_control")

    control = get_object_or_404(MobileControl, pk=pk)

    if control.licence_type != "demo":
        messages.error(request, f"Licence '{control.license_key}' is not a Demo licence.")
        return redirect("MobileApp:mobile_control")

    control.licence_type = "new"
    control.save()

    if control.shop and control.shop.is_demo:
        control.shop.is_demo = False
        control.shop.save()

    if control.store and control.store.is_demo:
        control.store.is_demo = False
        control.store.save()

    messages.success(request, f"Demo licence '{control.license_key}' converted to Main licence. Company now appears in Corporate/Company tables.")
    return redirect("MobileApp:mobile_control")