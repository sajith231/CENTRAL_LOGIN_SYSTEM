import json
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from MobileApp.models import MobileProject, MobileControl, MobileBillingHistory
from ModuleAndPackage.models import Package
from StoreShop.models import Store, Shop
from branch.models import Branch, CURRENCY_CODES

DEFAULT_USERS = 50
DEFAULT_VALIDITY_DAYS = 30
T_ERP_VALIDITY_DAYS = 14
DEFAULT_BRANCH_NAME = "IMC Developments"


def _error(message, status=400):
    return JsonResponse({"success": False, "error": message}, status=status)


def _resolve_project(name):
    """Resolve a project by its exact name.

    Returns (project, error_response). The project name must be an exact
    spelling, spacing, and capitalization match. If more than one project
    shares the name the request is rejected as ambiguous.
    """
    matches = list(MobileProject.objects.filter(project_name=name)[:2])
    if not matches:
        return None, _error(
            f"Project '{name}' not found. Project name must match exactly "
            "(spelling, spaces & capitalization)."
        )
    if len(matches) > 1:
        return None, _error(
            f"Project name '{name}' is ambiguous — more than one project uses "
            "this name. Please make project names unique."
        )
    return matches[0], None


@csrf_exempt
@require_http_methods(["POST"])
def api_licence_create(request, t_erp_only=False):
    """
    POST API: Creates licences for MULTIPLE projects in one request for the
    SAME company email.

    If the company email is ALREADY registered, the existing company (Shop)
    and its corporate (Store) are REUSED as-is — same branch, same details,
    same client_id — nothing existing is changed. The email decides which
    existing company is reused; the submitted company name is ignored in
    that case.

    For every selected project one licence is created. If the resolved
    company already holds a licence under a selected project, that project
    is skipped (reported as "skipped_existing") and the remaining projects
    are still created.

    Body:
    {
        "corporate": { "name": "Corporate Name", "place": "Optional place" },
        "company": {
            "name": "Company Name",
            "place": "Optional place",
            "email": "company@domain.com",     // required — client_id is set from this
            "contact_no": "Optional",
            "country": "India",
            "is_active": true
        },
        "projects": [
            { "project": "Exact Project Name", "package": "Exact Package Name" },
            { "project": "Another Project", "package": "Another Package" }
        ]
    }

    Rules:
        - Each project name must match exactly (spelling, spaces & capitalization).
        - Each package name must match exactly and must belong to that project.
        - One project = one package. The same project cannot be listed twice.
        - Users         = package.users_count (falls back to 50 when unlimited)
        - Validity      = 14 days for T-ERP requests, otherwise 30 days
        - Billing       = auto-created (Billed / Not Paid)
        - Licence type  = new
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return _error("Invalid JSON body")

    if not isinstance(payload, dict):
        return _error("Invalid JSON body")

    # ---------------- CORPORATE / COMPANY ----------------
    corporate = payload.get("corporate") or {}
    company = payload.get("company") or {}
    if not isinstance(corporate, dict):
        corporate = {}
    if not isinstance(company, dict):
        company = {}

    corporate_name = str(corporate.get("name") or "").strip()
    corporate_place = str(corporate.get("place") or "").strip()
    company_name = str(company.get("name") or "").strip()
    company_place = str(company.get("place") or "").strip()
    company_email = str(company.get("email") or "").strip()
    company_contact = str(company.get("contact_no") or "").strip()
    country = str(company.get("country") or "India").strip()
    is_active = bool(company.get("is_active", True))

    if not corporate_name:
        return _error("corporate.name is required")
    if not company_name:
        return _error("company.name is required")
    if not company_email:
        return _error("company.email is required (client_id is set from it)")
    if len(company_email) > 50:
        return _error("company.email is too long to be used as client_id (max 50 chars)")

    # currency is always auto-derived from the country (no currency_code field accepted)
    currency_code = CURRENCY_CODES.get(country, "INR")

    # ---------------- PROJECTS + PACKAGES (validate everything first) ----------------
    entries = payload.get("projects")
    if not isinstance(entries, list) or not entries:
        return _error(
            "projects is required and must be a non-empty list of "
            '{ "project": "<name>", "package": "<name>" } objects.'
        )

    resolved = []
    seen_projects = set()
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            return _error(f"projects[{index}] must be an object with 'project' and 'package'.")

        # Keep the submitted names unchanged for exact matching. Only use
        # strip() to decide whether a required value is blank; leading or
        # trailing spaces are part of the name and must not be normalized.
        project_name = str(entry.get("project") or "")
        package_name = str(entry.get("package") or "")

        if not project_name.strip():
            return _error(f"projects[{index}].project is required")
        if not package_name.strip():
            return _error(
                f"projects[{index}].package is required. One package per project."
            )

        project_key = project_name
        if project_key in seen_projects:
            return _error(
                f"Project '{project_name}' is listed more than once. "
                "One project can only have one package per request."
            )
        seen_projects.add(project_key)

        project, project_error = _resolve_project(project_name)
        if project_error:
            return project_error

        if t_erp_only and not project.t_erp:
            return _error(
                f"Project '{project.project_name}' is not enabled for the T-ERP "
                "licence create API. Enable the T-ERP option in the project settings."
            )

        package = Package.objects.filter(
            project=project, package_name=package_name
        ).first()
        if package is None:
            available = list(
                Package.objects.filter(project=project)
                .values_list("package_name", flat=True)
                .order_by("package_name")
            )
            available_msg = ", ".join(f"'{p}'" for p in available) if available else "none"
            return _error(
                f"Package '{package_name}' not found for project "
                f"'{project.project_name}'. Package name must match exactly "
                "(spelling, spaces & capitalization). "
                f"Available packages: {available_msg}"
            )

        resolved.append({"project": project, "package": package})

    # ---------------- BRANCH ----------------
    default_branch = Branch.objects.filter(name__iexact=DEFAULT_BRANCH_NAME).first()
    for item in resolved:
        if (item["project"].branch or default_branch) is None:
            return _error(
                f"No branch configured for project '{item['project'].project_name}' "
                f"and default branch '{DEFAULT_BRANCH_NAME}' not found."
            )

    # Branch used when a NEW corporate/company has to be created.
    company_branch = resolved[0]["project"].branch or default_branch

    # ---------------- EXISTING COMPANY (matched by EMAIL) ----------------
    # The email decides which company is reused. The submitted company name
    # is ignored when the email already exists.
    existing_shop = Shop.objects.filter(email=company_email).select_related("store").first()
    reuse_company = existing_shop is not None

    def licence_exists(project):
        """A licence already exists for the resolved company under this project."""
        qs = MobileControl.objects.filter(project=project)
        if existing_shop is not None:
            return qs.filter(
                Q(shop=existing_shop)
                | Q(client_id=existing_shop.client_id)
                | Q(client_id=company_email)
            ).exists()
        return qs.filter(client_id=company_email).exists()

    # ---------------- CREATE (single transaction) ----------------
    store = existing_shop.store if reuse_company else None
    shop = existing_shop
    results = []
    created_count = 0
    skipped_count = 0

    with transaction.atomic():
        for item in resolved:
            project = item["project"]
            package = item["package"]

            if licence_exists(project):
                skipped_count += 1
                results.append({
                    "project": project.project_name,
                    "package": package.package_name,
                    "status": "skipped_existing",
                    "message": "A licence already exists for this company under this project.",
                })
                continue

            # Create the corporate/company once, when the email is new.
            if shop is None:
                store = Store.objects.create(
                    name=corporate_name,
                    branch=company_branch,
                    place=corporate_place,
                    is_demo=False,
                    created_by=request.user if request.user.is_authenticated else None,
                    created_by_name="Licence Create API",
                )
                shop = Shop.objects.create(
                    store=store,
                    branch=company_branch,
                    name=company_name,
                    place=company_place,
                    email=company_email,
                    contact_no=company_contact,
                    country=country,
                    currency_code=currency_code,
                    client_id=company_email,
                    is_active=is_active,
                    is_demo=False,
                    created_by=request.user if request.user.is_authenticated else None,
                    created_by_name="Licence Create API",
                )

            branch = project.branch or default_branch
            users_count = (
                package.users_count
                if package.users_count and package.users_count > 0
                else DEFAULT_USERS
            )
            validity_days = T_ERP_VALIDITY_DAYS if t_erp_only else DEFAULT_VALIDITY_DAYS
            expiry_date = timezone.now() + timedelta(days=validity_days)

            control = MobileControl.objects.create(
                project=project,
                store=store,
                shop=shop,
                customer_name=shop.name,
                client_id=shop.client_id,
                login_limit=users_count,
                licence_type="new",
                package=package,
                active_custom_package=None,
                branch=branch,
                status=True,
                bill_status=True,
                expiry_date=expiry_date,
            )

            MobileBillingHistory.objects.create(
                control=control,
                package=package,
                custom_package=None,
                extended_days=validity_days,
                extended_login_limit=users_count,
                old_expiry_date=None,
                new_expiry_date=control.expiry_date,
                old_login_limit=0,
                new_login_limit=users_count,
                bill_status=True,
                payment_status="Not Paid",
                remark="Licence auto-created via Licence Create API",
                added_by="Licence Create API",
            )

            created_count += 1
            results.append({
                "project": project.project_name,
                "package": package.package_name,
                "status": "created",
                "license_key": control.license_key,
                "users_count": users_count,
                "login_limit": control.login_limit,
                "expiry_date": control.expiry_date.isoformat(),
            })

    corporate_response = (
        {"name": store.name, "place": store.place, "store_id": store.store_id}
        if store else
        {"name": corporate_name, "place": corporate_place, "store_id": None}
    )
    company_response = (
        {
            "name": shop.name,
            "place": shop.place,
            "email": shop.email,
            "contact_no": shop.contact_no,
            "country": shop.country,
            "currency_code": shop.currency_code,
            "client_id": shop.client_id,
        }
        if shop else
        {
            "name": company_name,
            "place": company_place,
            "email": company_email,
            "contact_no": company_contact,
            "country": country,
            "currency_code": currency_code,
            "client_id": company_email,
        }
    )

    return JsonResponse({
        "success": True,
        "message": (
            f"{created_count} licence(s) created, {skipped_count} skipped "
            "(a licence already exists for this company under the project)."
        ),
        "reused_existing_company": reuse_company,
        "created_count": created_count,
        "skipped_count": skipped_count,
        "corporate": corporate_response,
        "company": company_response,
        "results": results,
    }, status=201 if created_count else 200)
