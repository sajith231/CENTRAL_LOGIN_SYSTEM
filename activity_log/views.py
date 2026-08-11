import datetime

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from .models import ActivityLog
from .services import delete_month, log_activity

MODULE_MENU_NAMES = {
    "branch": "Branch",
    "module": "Module",
    "package": "Package",
    "custompackage": "Package",
    "custompackagemodule": "Module",
    "store": "Corporate",
    "shop": "Company",
    "user": "Users",
    "users": "Users",
    "mobileproject": "Project List",
    "webproject": "Web App List",
    "webcontrol": "Web Licensing",
    "mobilecontrol": "Licensing",
    "demomobilelicense": "Demo Licensing",
    "mobilebillinghistory": "Billing Report",
    "loginlog": "Login Log",
    "activedevice": "Active Device",
}


def menu_name(model_name):
    """Map a stored model name to its exact sidebar menu name."""
    if not model_name:
        return "-"
    key = "".join(model_name.lower().split())
    return MODULE_MENU_NAMES.get(key, model_name)


def is_django_superuser(request):
    return request.user.is_authenticated and request.user.is_superuser


def activity_log_view(request):
    if not is_django_superuser(request):
        return HttpResponseForbidden("Permission denied")

    logs = ActivityLog.objects.all()
    users = (
        ActivityLog.objects.values_list("user_name", flat=True)
        .order_by("user_name")
        .distinct()
    )

    user = request.GET.get("user", "").strip()
    month = request.GET.get("month", "").strip()

    if not month:
        month = datetime.date.today().strftime("%Y-%m")

    if user:
        logs = logs.filter(user_name=user)
    if month:
        try:
            year, mon = month.split("-")
            logs = logs.filter(created_at__year=int(year), created_at__month=int(mon))
        except (ValueError, AttributeError):
            month = datetime.date.today().strftime("%Y-%m")

    page_obj = Paginator(logs, 50).get_page(request.GET.get("page"))

    for log in page_obj:
        log.module_display = menu_name(log.model_name)

    return render(request, "activity_log.html", {
        "page_obj": page_obj,
        "users": users,
        "selected_user": user,
        "selected_month": month,
    })


def activity_log_delete_month(request):
    if not is_django_superuser(request):
        return HttpResponseForbidden("Permission denied")

    if request.method == "POST":
        month = request.POST.get("month", "").strip()
        try:
            year, mon = (int(part) for part in month.split("-"))
            datetime.date(year, mon, 1)
        except (ValueError, AttributeError):
            messages.error(request, "Please select a valid month.")
            return redirect("activity_log:activity_log")

        deleted = delete_month(year, mon)
        label = f"{mon:02d}-{year}"
        messages.success(request, f"Deleted {deleted} activity log record(s) for {label}.")
        log_activity(
            request,
            "Delete Activity Log Month",
            url=request.path,
            details=f"Deleted {deleted} record(s) for {label}",
        )

    return redirect("activity_log:activity_log")
