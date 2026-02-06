from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden

from .models import Users, LEVEL_CHOICES
from branch.models import Branch


# ================= SUPER LEVEL CHECK =================
def is_super_level_user(request):
    # Django superuser
    if request.user.is_authenticated and request.user.is_superuser:
        return True

    # Custom user with level = Super User
    if request.session.get("custom_user_level") == "Super User":
        return True

    return False


# ================= LOGIN =================
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect("admin_dashboard")

    if 'custom_user_id' in request.session:
        return redirect("admin_dashboard")

    if request.method == "POST":
        username_or_email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username_or_email, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("admin_dashboard")

        try:
            custom_user = Users.objects.get(email=username_or_email.lower())
            if custom_user.password == password:
                request.session['custom_user_id'] = custom_user.id
                request.session['custom_user_name'] = custom_user.name
                request.session['custom_user_email'] = custom_user.email
                request.session['custom_user_branches'] = [b.name for b in custom_user.branches.all()]
                request.session['custom_user_branch'] = ", ".join(
                    [b.name for b in custom_user.branches.all()]
                )
                request.session['custom_user_role'] = custom_user.user_role
                request.session['custom_user_level'] = custom_user.level
                request.session['allowed_menus'] = custom_user.allowed_menus or []

                messages.success(request, f"Welcome, {custom_user.name}!")
                return redirect("admin_dashboard")
        except Users.DoesNotExist:
            pass

        messages.error(request, "Invalid credentials.")

    return render(request, "login.html")


# ================= DASHBOARD =================
def admin_dashboard(request):
    if not (
        (request.user.is_authenticated and request.user.is_superuser)
        or ('custom_user_id' in request.session)
    ):
        messages.error(request, "Please log in to access this page.")
        return redirect("login")

    return render(request, "admin_dashboard.html")


# ================= LOGOUT =================
def logout_view(request):
    for key in [
        'custom_user_id',
        'custom_user_name',
        'custom_user_email',
        'custom_user_branch',
        'custom_user_role',
        'custom_user_level',
    ]:
        request.session.pop(key, None)

    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


# ================= USERS TABLE (SUPER ONLY) =================
def users_table(request):
    if not is_super_level_user(request):
        return HttpResponseForbidden("Permission denied")

    rows = Users.objects.all().order_by("-id")
    return render(request, "users_table.html", {"rows": rows})


# ================= ADD USER (SUPER ONLY) =================
def add_user(request):
    if not is_super_level_user(request):
        return HttpResponseForbidden("Permission denied")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        branch_ids = request.POST.getlist("branch")
        user_role = request.POST.get("user_role", "").strip()
        level = request.POST.get("level", "")
        image_file = request.FILES.get("profile_image")

        if not all([name, email, password, branch_ids, user_role, level]):
            messages.error(request, "Please fill in all fields.")
            return redirect("add_user")

        if Users.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return redirect("add_user")

        u = Users(
            name=name,
            email=email,
            password=password,
            user_role=user_role,
            level=level,
        )
        if image_file:
            u.profile_image = image_file
        u.save()

        u.branches.set(Branch.objects.filter(id__in=branch_ids))

        messages.success(request, "User saved successfully.")
        return redirect("users_table")

    return render(request, "add_user.html", {
        "branches": Branch.objects.all().order_by("name"),
        "levels": [l[0] for l in LEVEL_CHOICES],
    })


# ================= EDIT USER (SUPER ONLY) =================
def edit_user(request, pk):
    if not is_super_level_user(request):
        return HttpResponseForbidden("Permission denied")

    u = get_object_or_404(Users, pk=pk)

    if request.method == "POST":
        u.name = request.POST.get("name", "").strip()
        u.email = request.POST.get("email", "").strip().lower()
        u.user_role = request.POST.get("user_role", "").strip()
        u.level = request.POST.get("level", "")
        password = request.POST.get("password", "")
        branch_ids = request.POST.getlist("branch")
        image_file = request.FILES.get("profile_image")

        u.branches.set(Branch.objects.filter(id__in=branch_ids))

        if password:
            u.password = password

        if image_file:
            if u.profile_image:
                u.profile_image.delete(save=False)
            u.profile_image = image_file

        u.save()
        messages.success(request, "User updated successfully.")
        return redirect("users_table")

    return render(request, "edit_user.html", {
        "u": u,
        "branches": Branch.objects.all().order_by("name"),
        "levels": [l[0] for l in LEVEL_CHOICES],
    })


# ================= DELETE USER (SUPER ONLY) =================
def delete_user(request, pk):
    if not is_super_level_user(request):
        return HttpResponseForbidden("Permission denied")

    u = get_object_or_404(Users, pk=pk)

    if request.method == "POST":
        if u.profile_image:
            u.profile_image.delete(save=False)
        u.delete()
        messages.success(request, "User deleted successfully.")

    return redirect("users_table")
