from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy

from .models import Users, LEVEL_CHOICES

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from .models import Users, LEVEL_CHOICES

def login_view(request):
    # If already logged in
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")
    # Check if custom user is in session
    if 'custom_user_id' in request.session:
        return redirect("admin_dashboard")

    if request.method == "POST":
        username_or_email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # 1) Try Django superuser auth
        user = authenticate(request, username=username_or_email, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            # superuser can see all menus (no restriction)
            return redirect("admin_dashboard")
        
        # 2) Try custom Users auth
        try:
            custom_user = Users.objects.get(email=username_or_email.lower())
            if custom_user.password == password:
                # Store user info in session
                request.session['custom_user_id'] = custom_user.id
                request.session['custom_user_name'] = custom_user.name
                request.session['custom_user_email'] = custom_user.email
                request.session['custom_user_branch'] = custom_user.branch.name if custom_user.branch else None
                request.session['custom_user_role'] = custom_user.user_role
                request.session['custom_user_level'] = custom_user.level

                # 🔴 IMPORTANT: put allowed menus into session
                request.session['allowed_menus'] = custom_user.allowed_menus or []

                messages.success(request, f"Welcome, {custom_user.name}!")
                return redirect("admin_dashboard")
        except Users.DoesNotExist:
            pass
        
        messages.error(request, "Invalid credentials.")

    return render(request, "login.html")


# Middleware-style decorator for custom users
def custom_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'custom_user_id' not in request.session:
            messages.error(request, "Please log in to access this page.")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper

# Only allow superusers to view the admin dashboard
def is_superuser(user):
    return user.is_superuser

def admin_dashboard(request):
    # Allow both superusers and custom users
    is_superuser_logged = request.user.is_authenticated and request.user.is_superuser
    is_custom_user_logged = 'custom_user_id' in request.session
    
    if not is_superuser_logged and not is_custom_user_logged:
        messages.error(request, "Please log in to access this page.")
        return redirect("login")
    
    ctx = {"user": request.user}
    return render(request, "admin_dashboard.html", ctx)

def logout_view(request):
    # Clear custom user session
    for key in [
        'custom_user_id',
        'custom_user_name',
        'custom_user_email',
        'custom_user_branch',
        'custom_user_role',
        'custom_user_level',
    ]:
        if key in request.session:
            del request.session[key]
    
    # Logout Django user
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")

# --------- ADMIN ONLY: USER MANAGEMENT ----------
# Make the LIST visible to ALL logged-in users (Django-auth OR custom session)
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Users


def users_table(request):
    """Display all users with profile images and details."""
    # Check if the user is logged in (works for both Django auth and custom session)
    is_logged_in = request.user.is_authenticated or ('custom_user_id' in request.session)
    if not is_logged_in:
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    # Fetch all users ordered by newest first
    rows = Users.objects.all().order_by("-id")

    # Pass model instances directly to the template
    # so {{ r.profile_image.url }} works automatically
    return render(request, "users_table.html", {"rows": rows})





from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy

from .models import Users, LEVEL_CHOICES
from branch.models import Branch

# Helper to check whether either Django user or custom session user is logged in
def is_any_user_logged_in(request):
    return request.user.is_authenticated or ('custom_user_id' in request.session)

# ----------------- ALLOW ALL LOGGED-IN USERS TO CREATE / UPDATE / DELETE -----------------

def add_user(request):
    if not is_any_user_logged_in(request):
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        branch_id = request.POST.get("branch", "")
        user_role = request.POST.get("user_role", "").strip()
        level = request.POST.get("level", "")
        image_file = request.FILES.get("profile_image")  # NEW

        if not all([name, email, password, branch_id, user_role, level]):
            messages.error(request, "Please fill in all fields.")
            return redirect("add_user")

        if Users.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("add_user")

        try:
            branch_obj = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            messages.error(request, "Invalid branch selected.")
            return redirect("add_user")

        u = Users(
            name=name,
            email=email,
            password=password,  # NOTE: still plain text in your schema
            branch=branch_obj,
            user_role=user_role,
            level=level,
        )
        if image_file:
            u.profile_image = image_file   # this triggers R2 upload on save
        u.save()

        messages.success(request, f"User '{name}' saved.")
        return redirect("users_table")

    branches = Branch.objects.all().order_by('name')
    levels = [l[0] for l in LEVEL_CHOICES]
    return render(request, "add_user.html", {"branches": branches, "levels": levels})


def edit_user(request, pk):
    """Edit an existing user, with optional profile image update (R2 compatible)."""
    # Only allow access to logged-in users (Django-auth OR custom session)
    if not is_any_user_logged_in(request):
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    u = get_object_or_404(Users, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        branch_id = request.POST.get("branch", "")
        user_role = request.POST.get("user_role", "").strip()
        level = request.POST.get("level", "")
        image_file = request.FILES.get("profile_image")  # ✅ handle image update

        if not all([name, email, branch_id, user_role, level]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("edit_user", pk=pk)

        if Users.objects.exclude(pk=pk).filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("edit_user", pk=pk)

        try:
            branch_obj = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            messages.error(request, "Invalid branch selected.")
            return redirect("edit_user", pk=pk)

        # Update fields
        u.name = name
        u.email = email
        u.branch = branch_obj
        u.user_role = user_role
        u.level = level
        if password:
            u.password = password  # (still plain text — consider hashing later)

        # ✅ Handle new image upload (optional)
        if image_file:
            # Delete old image from R2 (or local storage) if exists
            if u.profile_image:
                u.profile_image.delete(save=False)
            # Save new one
            u.profile_image = image_file

        u.save()

        messages.success(request, "User updated successfully.")
        return redirect("users_table")

    branches = Branch.objects.all().order_by('name')
    levels = [l[0] for l in LEVEL_CHOICES]
    return render(request, "edit_user.html", {"u": u, "branches": branches, "levels": levels})


def delete_user(request, pk):
    """
    Delete a user and remove their profile image from Cloudflare R2 (or local media).
    """
    # Only allow access to logged-in users (Django-auth OR custom session)
    if not is_any_user_logged_in(request):
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    u = get_object_or_404(Users, pk=pk)

    if request.method == "POST":
        name = u.name

        # ✅ Delete profile image from R2 (or local) before deleting the user
        if u.profile_image:
            try:
                u.profile_image.delete(save=False)
            except Exception as e:
                print(f"[WARN] Failed to delete image for {u.name}: {e}")

        # ✅ Delete the user record
        u.delete()

        messages.success(request, f"Deleted '{name}' successfully.")
        return redirect("users_table")

    # Fallback redirect if method isn’t POST
    return redirect("users_table")
