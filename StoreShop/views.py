from django.shortcuts import render, redirect, get_object_or_404
from .models import Store, Shop
from django.db.models import Exists, OuterRef
from MobileApp.models import MobileControl

def is_super_level_user(request):
    # Django superuser
    if request.user.is_authenticated and request.user.is_superuser:
        return True

    # Custom user with level = Super User
    if request.session.get("custom_user_level") == "Super User":
        return True

    return False

# --- Existing Store Views ---
def stores_list(request):
    # Subquery to check if any MobileControl linked to this Store has active devices
    has_devices_subquery = MobileControl.objects.filter(
        store=OuterRef('pk'),
        active_devices__isnull=False
    )

    # 🔑 Superuser → see all
    if is_super_level_user(request):
        stores = Store.objects.annotate(
            has_active_devices=Exists(has_devices_subquery)
        ).order_by('-created_at')
        branches = Branch.objects.all().order_by('name')
    else:
        # 👤 Normal user → branch-based
        user_branches = request.session.get("custom_user_branches", [])

        branches = Branch.objects.filter(name__in=user_branches).order_by('name')
        stores = Store.objects.filter(
            branch__name__in=user_branches
        ).annotate(
            has_active_devices=Exists(has_devices_subquery)
        ).order_by('-created_at')

    return render(request, "stores.html", {
        "stores": stores,
        "branches": branches
    })


from branch.models import Branch

def add_store(request):
    # 🔑 Branch filtering
    if is_super_level_user(request):
        branches = Branch.objects.all().order_by('name')
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches).order_by('name')

    if request.method == "POST":
        name = request.POST.get("name")
        branch_id = request.POST.get("branch")
        place = request.POST.get("place")

        branch = get_object_or_404(Branch, id=branch_id)

        Store.objects.create(
            name=name,
            branch=branch,
            place=place,
            created_by=request.user if request.user.is_authenticated else None,
            created_by_name=request.user.username if request.user.is_authenticated else request.session.get("custom_user_name", "Unknown")
        )
        return redirect("stores_list")

    return render(request, "add_store.html", {
        "branches": branches
    })


def edit_store(request, id):
    store = get_object_or_404(Store, id=id)

    # 🔑 Branch filtering
    if is_super_level_user(request):
        branches = Branch.objects.all().order_by('name')
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches).order_by('name')

    if request.method == "POST":
        store.name = request.POST.get("name")
        branch_id = request.POST.get("branch")
        store.place = request.POST.get("place")

        store.branch = get_object_or_404(Branch, id=branch_id)
        store.save()
        return redirect("stores_list")

    return render(request, "edit_store.html", {
        "store": store,
        "branches": branches
    })



def delete_store(request, id):
    store = get_object_or_404(Store, id=id)
    store.delete()
    return redirect("stores_list")


# --- New Shop Views ---
def shop_list(request):
    # Subquery to check if any MobileControl linked to this Shop has active devices
    has_devices_subquery = MobileControl.objects.filter(
        shop=OuterRef('pk'),
        active_devices__isnull=False
    )

    if is_super_level_user(request):
        shops = Shop.objects.annotate(
            has_active_devices=Exists(has_devices_subquery)
        ).select_related('store', 'branch').order_by('-created_at')
        branches = Branch.objects.all().order_by('name')
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches).order_by('name')
        shops = Shop.objects.filter(
            branch__name__in=user_branches
        ).annotate(
            has_active_devices=Exists(has_devices_subquery)
        ).select_related('store', 'branch').order_by('-created_at')

    return render(request, "shops.html", {
        "shops": shops,
        "branches": branches
    })

from branch.models import Branch

def add_shop(request):
    if is_super_level_user(request):
        stores = Store.objects.all().order_by('name')
        branches = Branch.objects.all().order_by('name')
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches).order_by('name')
        stores = Store.objects.filter(branch__name__in=user_branches).order_by('name')

    if request.method == "POST":
        name = request.POST.get("name")
        store_id = request.POST.get("store")
        branch_id = request.POST.get("branch")
        place = request.POST.get("place")
        email = request.POST.get("email")
        contact_no = request.POST.get("contact_no")
        is_active = bool(request.POST.get("is_active"))

        store = get_object_or_404(Store, id=store_id)
        branch = get_object_or_404(Branch, id=branch_id)

        # ── Client ID: auto-generate or custom entry ──
        client_id_mode = request.POST.get("client_id_mode", "auto")
        custom_client_id = request.POST.get("custom_client_id", "").strip()

        if client_id_mode == "custom":
            if not custom_client_id:
                from django.contrib import messages
                messages.error(request, "Custom Client ID cannot be empty.")
                return render(request, "add_shop.html", {"stores": stores, "branches": branches})
            if Shop.objects.filter(client_id=custom_client_id).exists():
                from django.contrib import messages
                messages.error(request, f"Client ID '{custom_client_id}' is already taken. Please choose another.")
                return render(request, "add_shop.html", {"stores": stores, "branches": branches})

        create_kwargs = dict(
            name=name,
            store=store,
            branch=branch,
            place=place,
            email=email,
            contact_no=contact_no,
            is_active=is_active,
            created_by=request.user if request.user.is_authenticated else None,
            created_by_name=request.user.username if request.user.is_authenticated else request.session.get("custom_user_name", "Unknown")
        )
        if client_id_mode == "custom":
            create_kwargs["client_id"] = custom_client_id

        Shop.objects.create(**create_kwargs)
        return redirect("shop_list")

    return render(request, "add_shop.html", {
        "stores": stores,
        "branches": branches
    })


def edit_shop(request, id):
    shop = get_object_or_404(Shop, id=id)

    if is_super_level_user(request):
        stores = Store.objects.all().order_by('name')
        branches = Branch.objects.all().order_by('name')
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches).order_by('name')
        stores = Store.objects.filter(branch__name__in=user_branches).order_by('name')

    if request.method == "POST":
        shop.name = request.POST.get("name")
        store_id = request.POST.get("store")
        branch_id = request.POST.get("branch")
        shop.place = request.POST.get("place")
        shop.email = request.POST.get("email")
        shop.contact_no = request.POST.get("contact_no")
        shop.is_active = bool(request.POST.get("is_active"))

        shop.store = get_object_or_404(Store, id=store_id)
        shop.branch = get_object_or_404(Branch, id=branch_id)
        shop.save()
        return redirect("shop_list")

    return render(request, "edit_shop.html", {
        "shop": shop,
        "stores": stores,
        "branches": branches
    })



def delete_shop(request, id):
    shop = get_object_or_404(Shop, id=id)
    shop.delete()
    return redirect("shop_list")


from django.http import JsonResponse

def check_client_id(request):
    """AJAX: check if a client_id is already taken. Returns {available: true/false}."""
    client_id = request.GET.get("client_id", "").strip()
    if not client_id:
        return JsonResponse({"available": False, "error": "Empty"})
    taken = Shop.objects.filter(client_id=client_id).exists()
    return JsonResponse({"available": not taken})
