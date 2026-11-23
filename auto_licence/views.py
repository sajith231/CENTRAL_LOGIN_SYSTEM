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


@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def api_t_erp_projects(request):
    """Return the current T-ERP projects and their packages.

    This endpoint intentionally reads the project/package records on every
    request. Changes made in the project or package screens are therefore
    reflected immediately without maintaining a second API-specific list.
    """
    if request.method == "OPTIONS":
        response = JsonResponse({"status": "ok"})
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Accept"
        return response

    projects = (
        MobileProject.objects.filter(t_erp=True)
        .prefetch_related("package_set")
        .order_by("project_name")
    )

    response = JsonResponse({
        "success": True,
        "projects": [
            {
                "project": project.project_name,
                "api_endpoint": project.api_endpoint,
                "packages": [
                    {
                        "package": package.package_name,
                        "days_limit": package.days_limit,
                        "users_count": package.users_count or 0,
                    }
                    for package in project.package_set.all().order_by("package_name")
                ],
            }
            for project in projects
        ],
    })
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Accept"
    return response


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
        - Licence type  = trial for T-ERP requests (promoted to new on the
                          first billing), otherwise new
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
    requested = []
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

        requested.append((project_name, package_name))

    # Resolve all project names with one query and all packages with a second
    # query, instead of two lookups per project.
    matches_by_name = {}
    for project in (
        MobileProject.objects.filter(project_name__in=list({p for p, _ in requested}))
        .select_related("branch")
    ):
        matches_by_name.setdefault(project.project_name, []).append(project)

    project_ids = [p.id for matches in matches_by_name.values() for p in matches]
    packages_by_key = {}
    package_names_by_project = {}
    for package in Package.objects.filter(project_id__in=project_ids):
        packages_by_key[(package.project_id, package.package_name)] = package
        package_names_by_project.setdefault(package.project_id, []).append(
            package.package_name
        )

    seen_projects = set()
    for project_name, package_name in requested:
        if project_name in seen_projects:
            return _error(
                f"Project '{project_name}' is listed more than once. "
                "One project can only have one package per request."
            )
        seen_projects.add(project_name)

        matches = matches_by_name.get(project_name) or []
        if not matches:
            return _error(
                f"Project '{project_name}' not found. Project name must match exactly "
                "(spelling, spaces & capitalization)."
            )
        if len(matches) > 1:
            return _error(
                f"Project name '{project_name}' is ambiguous — more than one project "
                "uses this name. Please make project names unique."
            )

        project = matches[0]
        if t_erp_only and not project.t_erp:
            return _error(
                f"Project '{project.project_name}' is not enabled for the T-ERP "
                "licence create API. Enable the T-ERP option in the project settings."
            )

        package = packages_by_key.get((project.id, package_name))
        if package is None:
            available = sorted(package_names_by_project.get(project.id, []))
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

    # One query for every selected project instead of one query per project.
    licence_qs = MobileControl.objects.filter(
        project_id__in=[item["project"].id for item in resolved]
    )
    if existing_shop is not None:
        licence_qs = licence_qs.filter(
            Q(shop=existing_shop)
            | Q(client_id=existing_shop.client_id)
            | Q(client_id=company_email)
        )
    else:
        licence_qs = licence_qs.filter(client_id=company_email)
    licensed_project_ids = set(licence_qs.values_list("project_id", flat=True))

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

            if project.id in licensed_project_ids:
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

            # T-ERP licences start as a Trial Licence and are promoted to a
            # New Licence on the first billing. Every other endpoint creates a
            # New Licence directly.
            licence_type = "trial" if t_erp_only else "new"

            control = MobileControl.objects.create(
                project=project,
                store=store,
                shop=shop,
                customer_name=shop.name,
                client_id=shop.client_id,
                login_limit=users_count,
                licence_type=licence_type,
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
