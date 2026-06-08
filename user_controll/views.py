from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from app1.models import Users


def is_superuser_or_logged(request):
    """
    Helper: allow Django superuser OR any logged custom user.
    We'll restrict menu configuration itself to superuser only.
    """
    return request.user.is_authenticated or ('custom_user_id' in request.session)


# 🔴 COMMON MENU STRUCTURE – IDs must match what we check in base.html
def get_all_menus():
    return [
        {
            "name": "Web App",
            "icon": "fa-solid fa-globe",
            "submenus": [
                {"id": "web_control", "name": "Web Licensing", "icon": "fa-solid fa-sliders"},
                {"id": "webapp_list", "name": "Web App List", "icon": "fa-solid fa-list-check"},
            ],
        },
        {
            "name": "Mobile App",
            "icon": "fa-solid fa-mobile-screen-button",
            "submenus": [
                {"id": "mobile_control", "name": "Mobile Licensing", "icon": "fa-solid fa-sliders"},
                {"id": "mobile_control_status","name": "Mobile Status Control","icon": "fa-solid fa-toggle-on"},
                {"id": "mobile_billing","name": "Mobile Billing","icon": "fa-solid fa-file-invoice-dollar"},
                {"id": "mobile_payment_status", "name": "Mobile Payment Status", "icon": "fa-solid fa-money-check-dollar"},


                {"id": "mobile_device_remove","name": "Mobile Device Remove","icon": "fa-solid fa-trash"},
                {"id": "mobileapp_list", "name": "Mobile App List", "icon": "fa-solid fa-list-check"},
                {"id": "module_list", "name": "Module", "icon": "fa-solid fa-puzzle-piece"},
                {"id": "package_list", "name": "Package", "icon": "fa-solid fa-box-open"},
                {"id": "mobile_demo", "name": "Mobile Demo Licensing", "icon": "fa-solid fa-mobile-screen"},
            ],
        },
        {
            "name": "Clients",
            "icon": "fa-solid fa-building-user",
            "submenus": [
                {"id": "stores_list", "name": "Corporate", "icon": "fa-solid fa-store"},
                {"id": "shop_list", "name": "Company", "icon": "fa-solid fa-shop"},
            ],
        },
        {
            "name": "User Management",
            "icon": "fa-solid fa-users-gear",
            "submenus": [
                {"id": "users_table", "name": "Users", "icon": "fa-solid fa-users"},
                {"id": "user_menu_control", "name": "User Menu Control", "icon": "fa-solid fa-user-gear"},
            ],
        },
        {
            "name": "Downloads",
            "icon": "fa-solid fa-cloud-arrow-down",
            "submenus": [
                {"id": "downloads_upload", "name": "Upload", "icon": "fa-solid fa-upload"},
                {"id": "downloads_download", "name": "Download", "icon": "fa-solid fa-download"},
            ],
        },
        {
            "name": "Master",
            "icon": "fa-solid fa-layer-group",
            "submenus": [
                {"id": "branch_list", "name": "Branch", "icon": "fa-solid fa-code-branch"},
            ],
        },
    ]



# ---------- 1) LIST USERS FOR MENU CONTROL ----------

def user_menu_user_list(request):
    if not is_superuser_or_logged(request):
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    # Only Django superuser OR custom level "Super Admin" can see this page
    if not (request.user.is_authenticated and request.user.is_superuser):
        # if using custom Users levels, you can also check here:
        # if request.session.get("custom_user_level") != "Super Admin":
        #     return HttpResponseForbidden("Not allowed.")
        pass  # for now, allow any logged in; you can restrict later

    users = Users.objects.all().order_by("name")
    return render(request, "user_menu_user_list.html", {
        "users": users,
    })


# ---------- 2) CONFIGURE ONE USER MENUS ----------

@login_required
def configure_user_menu(request, user_id):
    from MobileApp.models import MobileProject
    
    # only Django superuser can configure
    if not request.user.is_superuser:
        messages.error(request, "Only superuser can configure user menus.")
        return redirect("admin_dashboard")

    user = get_object_or_404(Users, id=user_id)
    menus = get_all_menus()
    app_types = MobileProject.APP_TYPE_CHOICES

    # current menus from DB
    allowed = user.allowed_menus or []
    allowed_app_types = user.allowed_app_types or []

    if request.method == "POST":
        selected_menus = []
        selected_app_types = []
        
        for key in request.POST:
            if key.startswith("menu_"):
                selected_menus.append(key.replace("menu_", ""))
            elif key.startswith("app_type_"):
                selected_app_types.append(key.replace("app_type_", ""))

        user.allowed_menus = selected_menus
        user.allowed_app_types = selected_app_types
        user.save()

        # if editing your own permissions, update session
        custom_id = request.session.get("custom_user_id")
        if custom_id and int(custom_id) == user.id:
            request.session["allowed_menus"] = selected_menus
            request.session["allowed_app_types"] = selected_app_types

        messages.success(request, f"Menu permissions for {user.name} have been updated.")
        return redirect("user_controll:user_menu_user_list")

    return render(request, "configure_user_menu.html", {
        "u": user,
        "menus": menus,
        "allowed": allowed,
        "app_types": app_types,
        "allowed_app_types": allowed_app_types,
    })
