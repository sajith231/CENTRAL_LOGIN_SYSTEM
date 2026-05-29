from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from MobileApp.models import MobileControl, ActiveDevice
from ModuleAndPackage.models import Package
from .models import DemoMobileLicense
from django.utils import timezone


def _is_super_level_user(request):
    """Returns True if the logged-in user is a Django superuser or a custom Super User."""
    if request.user.is_authenticated and request.user.is_superuser:
        return True
    if request.session.get("custom_user_level") == "Super User":
        return True
    return False


def demo_license_list(request):
    from StoreShop.models import Shop
    from django.db.models import Q

    demos = DemoMobileLicense.objects.select_related(
        "original_license",
        "original_license__project",
        "original_license__shop",
        "original_license__shop__branch",
        "project"
    ).prefetch_related(
        "original_license__active_devices",
        "active_devices"
    )

    # ── Branch-based filtering for non-superusers ──
    if not _is_super_level_user(request):
        user_branch_names = request.session.get("custom_user_branches", [])
        if user_branch_names:
            # OG-linked demos: filter via shop → branch name
            # Manual demos: filter via client_id → shop → branch name
            manual_client_ids_in_branch = Shop.objects.filter(
                branch__name__in=user_branch_names
            ).values_list("client_id", flat=True)

            demos = demos.filter(
                Q(original_license__shop__branch__name__in=user_branch_names) |
                Q(original_license__isnull=True, client_id__in=manual_client_ids_in_branch)
            )
        else:
            demos = demos.none()

    now = timezone.now()

    # Build a client_id → branch name map for manual demos in one query
    manual_client_ids = [
        d.client_id for d in demos
        if d.original_license is None and d.client_id
    ]
    shop_branch_map = {}
    if manual_client_ids:
        shops = Shop.objects.filter(
            client_id__in=manual_client_ids
        ).select_related('branch').values('client_id', 'branch__name')
        shop_branch_map = {s['client_id']: s['branch__name'] for s in shops}

    for d in demos:
        # auto expire demo after 5 days
        if d.expires_at and d.expires_at < now and d.status:
            d.status = False
            d.save(update_fields=["status"])

        # stats/devices
        d.total_lic = d.demo_login_limit
        d.devices = d.active_devices.all()
        d.reg_dev = d.devices.count()
        d.bal_lic = d.total_lic - d.reg_dev

        # branch name
        if d.original_license and d.original_license.shop and d.original_license.shop.branch:
            d.branch_name = d.original_license.shop.branch.name
        elif d.client_id and d.client_id in shop_branch_map:
            d.branch_name = shop_branch_map[d.client_id]
        else:
            d.branch_name = None

    return render(request, "demo_mobile_licensing.html", {"demos": demos})


def add_mobile_demo_licencing(request):
    from branch.models import Branch
    og_licenses = MobileControl.objects.select_related('shop', 'project').all()

    # Restrict branches for non-superusers
    if _is_super_level_user(request):
        branches = Branch.objects.all().order_by('name')
    else:
        user_branch_names = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branch_names).order_by('name')

    if request.method == "POST":
        og_id = request.POST.get("og_license")
        demo_limit = request.POST.get("demo_login_limit", 1)

        og = get_object_or_404(MobileControl, id=og_id)
        demo_key = f"DEMO-{og.license_key}"

        if DemoMobileLicense.objects.filter(demo_license=demo_key).exists():
            messages.error(request, "Demo license already exists!")
            return redirect("DemoLicensing:demo_add")

        DemoMobileLicense.objects.create(
            original_license=og,
            demo_login_limit=demo_limit
        )

        messages.success(request, f"Demo License {demo_key} created")
        return redirect("DemoLicensing:demo_list")

    return render(request, "add_demo_license.html", {"og_licenses": og_licenses, "branches": branches})


def edit_demo_license(request, pk):
    demo = get_object_or_404(DemoMobileLicense, pk=pk)

    if request.method == "POST":
        demo.demo_login_limit = request.POST.get("demo_login_limit")
        demo.status = True if request.POST.get("status") == "on" else False
        demo.save()
        messages.success(request, "Demo license updated")
        return redirect("DemoLicensing:demo_list")

    return render(request, "edit_demo_license.html", {"demo": demo})


def delete_demo_license(request, pk):
    demo = get_object_or_404(DemoMobileLicense, pk=pk)
    demo.delete()
    messages.success(request, "Demo license deleted")
    return redirect("DemoLicensing:demo_list")



from MobileApp.models import MobileProject
from ModuleAndPackage.models import Package

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from MobileApp.models import MobileProject
from ModuleAndPackage.models import Package
from StoreShop.models import Shop
from .models import DemoMobileLicense


def add_manual_demo_license(request):
    from branch.models import Branch as BranchModel
    projects = MobileProject.objects.all()

    # Pass allowed branches to template so JS can pre-filter on page load
    if _is_super_level_user(request):
        allowed_branches = list(BranchModel.objects.values("id", "name").order_by("name"))
    else:
        user_branch_names = request.session.get("custom_user_branches", [])
        allowed_branches = list(
            BranchModel.objects.filter(name__in=user_branch_names)
            .values("id", "name")
            .order_by("name")
        )

    if request.method == "POST":
        # 🔹 company = SHOP ID (from dropdown)
        shop_id = request.POST.get("company")
        project_id = request.POST.get("project")
        package_id = request.POST.get("package")
        demo_limit = request.POST.get("demo_login_limit", 1)

        # 🔹 validations
        if not shop_id or not project_id or not package_id:
            messages.error(request, "All fields are required")
            return redirect("DemoLicensing:demo_add_manual")

        # 🔹 fetch objects
        shop = get_object_or_404(Shop, id=shop_id)
        project = get_object_or_404(MobileProject, id=project_id)
        package = get_object_or_404(Package, id=package_id)

        # 🔹 create manual demo license
        DemoMobileLicense.objects.create(
            company_name=shop.name,        # ✅ company name
            client_id=shop.client_id,      # ✅ IMPORTANT (FIX)
            project=project,
            package=package,
            demo_login_limit=demo_limit
        )

        messages.success(request, "Manual demo license created successfully")
        return redirect("DemoLicensing:demo_list")

    return render(
        request,
        "add_manual_demo_license.html",
        {
            "projects": projects,
            "allowed_branches": allowed_branches,
            "is_super": _is_super_level_user(request),
        }
    )





def get_packages(request, project_id):
    packages = Package.objects.filter(project_id=project_id).values("id", "package_name")
    return JsonResponse(list(packages), safe=False)


def delete_demo_device(request, pk):
    device = get_object_or_404(ActiveDevice, pk=pk)
    device.delete()
    messages.success(request, "Device removed successfully")
    return redirect("DemoLicensing:demo_list")


# -----------------------------------------------------
# AJAX views for Manual Demo License (Dependent Dropdowns)
# -----------------------------------------------------

from branch.models import Branch
from StoreShop.models import Store, Shop

def get_all_branches(request):
    """Return branches as JSON — filtered to user's allowed branches for non-superusers."""
    if _is_super_level_user(request):
        branches = Branch.objects.values("id", "name").order_by("name")
    else:
        user_branch_names = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branch_names).values("id", "name").order_by("name")
    return JsonResponse(list(branches), safe=False)

def get_licenses_by_branch(request, branch_id):
    """Return OG MobileControl licenses filtered by branch via shop__branch — restricted to user's allowed branches."""
    from MobileApp.models import MobileControl
    # Security: non-superusers can only query their own branches
    if not _is_super_level_user(request):
        user_branch_names = request.session.get("custom_user_branches", [])
        if not Branch.objects.filter(id=branch_id, name__in=user_branch_names).exists():
            return JsonResponse([], safe=False)
    licenses = MobileControl.objects.filter(
        shop__branch_id=branch_id
    ).select_related('shop', 'project').values(
        "id", "customer_name", "license_key", "project__project_name", "shop__place"
    )
    data = [
        {
            "id": lic["id"],
            "label": f"{lic['customer_name']} ({lic['shop__place'] or ''}) — {lic['project__project_name']} ({lic['license_key']})"
        }
        for lic in licenses
    ]
    return JsonResponse(data, safe=False)

def get_corporates_by_branch(request, branch_id):
    """Return Stores (Corporates) for a given Branch — restricted to user's allowed branches."""
    if not _is_super_level_user(request):
        user_branch_names = request.session.get("custom_user_branches", [])
        # Verify the requested branch is in the user's allowed list
        if not Branch.objects.filter(id=branch_id, name__in=user_branch_names).exists():
            return JsonResponse([], safe=False)
    stores = Store.objects.filter(branch_id=branch_id).values("id", "name")
    return JsonResponse(list(stores), safe=False)

def get_shops_by_corporate(request, corporate_id):
    """Return Shops (Companies) for a given Store (Corporate)."""
    # Note: We return 'name' because the frontend will use the name as value
    shops = Shop.objects.filter(store_id=corporate_id).values("id", "name")
    return JsonResponse(list(shops), safe=False)
