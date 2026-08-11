from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user_name", "user_type", "action", "model_name", "details", "ip_address")
    list_filter = ("user_name", "user_type", "action", "created_at")
    search_fields = ("user_name", "action", "details", "model_name")
    ordering = ("-created_at",)
    readonly_fields = (
        "user_name",
        "user_email",
        "user_type",
        "action",
        "details",
        "model_name",
        "object_id",
        "method",
        "url",
        "ip_address",
        "created_at",
    )
