from django.shortcuts import render, redirect, get_object_or_404
from .models import Store, Shop

# --- Existing Store Views ---
def stores_list(request):
    stores = Store.objects.all()
    return render(request, "stores.html", {"stores": stores})

def add_store(request):
    if request.method == "POST":
        name = request.POST.get("name")
        Store.objects.create(name=name)
        return redirect("stores_list")
    return render(request, "add_store.html")

def edit_store(request, id):
    store = get_object_or_404(Store, id=id)
    if request.method == "POST":
        store.name = request.POST.get("name")
        store.save()
        return redirect("stores_list")
    return render(request, "edit_store.html", {"store": store})

def delete_store(request, id):
    store = get_object_or_404(Store, id=id)
    store.delete()
    return redirect("stores_list")


# --- New Shop Views ---
def shop_list(request):
    shops = Shop.objects.select_related('store').all()
    return render(request, "shops.html", {"shops": shops})

def add_shop(request):
    stores = Store.objects.all()
    if request.method == "POST":
        name = request.POST.get("name")
        store_id = request.POST.get("store")
        email = request.POST.get("email")
        contact_no = request.POST.get("contact_no")

        store = get_object_or_404(Store, id=store_id)
        Shop.objects.create(name=name, store=store, email=email, contact_no=contact_no)
        return redirect("shop_list")

    return render(request, "add_shop.html", {"stores": stores})

def edit_shop(request, id):
    shop = get_object_or_404(Shop, id=id)
    stores = Store.objects.all()

    if request.method == "POST":
        shop.name = request.POST.get("name")
        store_id = request.POST.get("store")
        shop.email = request.POST.get("email")
        shop.contact_no = request.POST.get("contact_no")

        shop.store = get_object_or_404(Store, id=store_id)
        shop.save()
        return redirect("shop_list")

    return render(request, "edit_shop.html", {"shop": shop, "stores": stores})

def delete_shop(request, id):
    shop = get_object_or_404(Shop, id=id)
    shop.delete()
    return redirect("shop_list")
