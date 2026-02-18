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
        branches = Branch.objects.all()
    else:
        # 👤 Normal user → branch-based
        user_branches = request.session.get("custom_user_branches", [])

        branches = Branch.objects.filter(name__in=user_branches)
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
        branches = Branch.objects.all()
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches)

    if request.method == "POST":
        name = request.POST.get("name")
        branch_id = request.POST.get("branch")
        place = request.POST.get("place")

        branch = get_object_or_404(Branch, id=branch_id)

        Store.objects.create(
            name=name,
            branch=branch,
            place=place,
            created_by=request.user
        )
        return redirect("stores_list")

    return render(request, "add_store.html", {
        "branches": branches
    })


def edit_store(request, id):
    store = get_object_or_404(Store, id=id)

    # 🔑 Branch filtering
    if is_super_level_user(request):
        branches = Branch.objects.all()
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches)

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
        branches = Branch.objects.all()
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches)
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
        stores = Store.objects.all()
        branches = Branch.objects.all()
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches)
        stores = Store.objects.filter(branch__name__in=user_branches)

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

        Shop.objects.create(
            name=name,
            store=store,
            branch=branch,
            place=place,
            email=email,
            contact_no=contact_no,
            is_active=is_active,
            created_by=request.user
        )
        return redirect("shop_list")

    return render(request, "add_shop.html", {
        "stores": stores,
        "branches": branches
    })


def edit_shop(request, id):
    shop = get_object_or_404(Shop, id=id)

    if is_super_level_user(request):
        stores = Store.objects.all()
        branches = Branch.objects.all()
    else:
        user_branches = request.session.get("custom_user_branches", [])
        branches = Branch.objects.filter(name__in=user_branches)
        stores = Store.objects.filter(branch__name__in=user_branches)

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
