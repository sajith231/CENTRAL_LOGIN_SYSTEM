from django.contrib import messages
from django.shortcuts import redirect


class MenuPermissionMiddleware:
    """
    Blocks access to menus that the logged-in custom user does not have permission for.
    Uses the menu IDs stored in request.session['allowed_menus'].
    """

    MENU_PERMISSIONS = {
        # WebApp
        "WebApp:web_control": "web_control",
        "WebApp:add_web_control": "web_control",
        "WebApp:edit_web_control": "web_control",
        "WebApp:delete_web_control": "web_control",
        "WebApp:webapp_list": "webapp_list",
        "WebApp:webproject_create": "webapp_list",
        "WebApp:webproject_edit": "webapp_list",
        "WebApp:webproject_delete": "webapp_list",
        # MobileApp licensing
        "MobileApp:mobile_control": "mobile_control",
        "MobileApp:add_mobile_control": "mobile_control",
        "MobileApp:edit_mobile_control": "mobile_control",
        "MobileApp:delete_mobile_control": "mobile_control",
        "MobileApp:mobileapp_list": "mobileapp_list",
        "MobileApp:mobileproject_create": "mobileapp_list",
        "MobileApp:mobileproject_edit": "mobileapp_list",
        "MobileApp:mobileproject_delete": "mobileapp_list",
        # Module & Package
        "ModuleAndPackage:module_list": "module_list",
        "ModuleAndPackage:add_module_page": "module_list",
        "ModuleAndPackage:add_module": "module_list",
        "ModuleAndPackage:edit_module": "module_list",
        "ModuleAndPackage:delete_module": "module_list",
        "ModuleAndPackage:package_list": "package_list",
        "ModuleAndPackage:add_package_page": "package_list",
        "ModuleAndPackage:save_package": "package_list",
        "ModuleAndPackage:edit_package": "package_list",
        "ModuleAndPackage:delete_package": "package_list",
        # ModuleAndPackage:get_modules & get_packages removed to allow dropdown usage by all users
        # Store / Shop
        "stores_list": "stores_list",
        "add_store": "stores_list",
        "edit_store": "stores_list",
        "delete_store": "stores_list",
        "shop_list": "shop_list",
        "add_shop": "shop_list",
        "edit_shop": "shop_list",
        "delete_shop": "shop_list",
        # Users table
        "users_table": "users_table",
        "add_user": "users_table",
        "edit_user": "users_table",
        "delete_user": "users_table",
        # Branch
        "branch_list": "branch_list",
        "add_branch": "branch_list",
        "edit_branch": "branch_list",
        "delete_branch": "branch_list",
        # Menu control
        "user_controll:user_menu_user_list": "user_menu_control",
        "user_controll:configure_user_menu": "user_menu_control",
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = getattr(request, "resolver_match", None)
        if not match:
            return None

        view_name = match.view_name
        required_menu = self.MENU_PERMISSIONS.get(view_name)

        if not required_menu:
            return None

        # Superusers can access everything
        if request.user.is_authenticated and request.user.is_superuser:
            return None

        allowed_menus = request.session.get("allowed_menus") or []
        is_custom_logged = request.session.get("custom_user_id")
        is_django_logged = request.user.is_authenticated

        if not (is_custom_logged or is_django_logged):
            messages.error(request, "Please log in to access this page.")
            return redirect("login")

        if required_menu not in allowed_menus:
            messages.error(request, "You do not have permission to access that page.")
            return redirect("admin_dashboard")

        return None

