from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy

from .models import Users, BRANCH_CHOICES, LEVEL_CHOICES

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

        # First, try Django superuser authentication
        user = authenticate(request, username=username_or_email, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")
        
        # Then, try custom Users model authentication (email + plain password)
        try:
            custom_user = Users.objects.get(email=username_or_email.lower())
            # ⚠️ PLAIN TEXT PASSWORD COMPARISON - INSECURE!
            if custom_user.password == password:
                # Store user info in session
                request.session['custom_user_id'] = custom_user.id
                request.session['custom_user_name'] = custom_user.name
                request.session['custom_user_email'] = custom_user.email
                request.session['custom_user_branch'] = custom_user.branch
                request.session['custom_user_role'] = custom_user.user_role
                request.session['custom_user_level'] = custom_user.level
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
def users_table(request):
    is_logged_in = request.user.is_authenticated or ('custom_user_id' in request.session)
    if not is_logged_in:
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    rows = [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "branch": u.branch,
            "user_role": u.user_role,
            "level": u.level,
            "password": u.password,  # Plain text password
        }
        for u in Users.objects.all().order_by("-id")
    ]
    return render(request, "users_table.html", {"rows": rows})

# Keep CREATE/UPDATE/DELETE restricted to Django superusers
@login_required(login_url=reverse_lazy('login'))
@user_passes_test(is_superuser, login_url=reverse_lazy('login'))
def add_user(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        branch = request.POST.get("branch", "")
        user_role = request.POST.get("user_role", "").strip()
        level = request.POST.get("level", "")

        if not all([name, email, password, branch, user_role, level]):
            messages.error(request, "Please fill in all fields.")
            return redirect("add_user")

        if Users.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("add_user")

        # ⚠️ STORING PLAIN TEXT PASSWORD - INSECURE!
        Users.objects.create(
            name=name,
            email=email,
            password=password,
            branch=branch,
            user_role=user_role,
            level=level,
        )
        messages.success(request, f"User '{name}' saved.")
        return redirect("users_table")

    branches = [b[0] for b in BRANCH_CHOICES]
    levels = [l[0] for l in LEVEL_CHOICES]
    return render(request, "add_user.html", {"branches": branches, "levels": levels})

@login_required(login_url=reverse_lazy('login'))
@user_passes_test(is_superuser, login_url=reverse_lazy('login'))
def edit_user(request, pk):
    u = get_object_or_404(Users, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        branch = request.POST.get("branch", "")
        user_role = request.POST.get("user_role", "").strip()
        level = request.POST.get("level", "")

        if not all([name, email, branch, user_role, level]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("edit_user", pk=pk)

        if Users.objects.exclude(pk=pk).filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("edit_user", pk=pk)

        u.name = name
        u.email = email
        u.branch = branch
        u.user_role = user_role
        u.level = level
        if password:
            u.password = password  # Plain text
        u.save()

        messages.success(request, "User updated.")
        return redirect("users_table")

    branches = [b[0] for b in BRANCH_CHOICES]
    levels = [l[0] for l in LEVEL_CHOICES]
    return render(request, "edit_user.html", {"u": u, "branches": branches, "levels": levels})

@login_required(login_url=reverse_lazy('login'))
@user_passes_test(is_superuser, login_url=reverse_lazy('login'))
def delete_user(request, pk):
    u = get_object_or_404(Users, pk=pk)
    if request.method == "POST":
        name = u.name
        u.delete()
        messages.success(request, f"Deleted '{name}'.")
        return redirect("users_table")
    return redirect("users_table")
