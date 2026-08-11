from django.db import models


class ActivityLog(models.Model):
    user_name = models.CharField(max_length=150, db_index=True)
    user_email = models.EmailField(blank=True, null=True)
    user_type = models.CharField(max_length=50, blank=True, default="")
    action = models.CharField(max_length=255)
    details = models.CharField(max_length=255, blank=True, default="")
    model_name = models.CharField(max_length=100, blank=True, default="")
    object_id = models.CharField(max_length=100, blank=True, default="")
    method = models.CharField(max_length=10, blank=True, default="")
    url = models.CharField(max_length=500, blank=True, default="")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"

    def __str__(self):
        return f"{self.user_name} - {self.action} ({self.created_at:%Y-%m-%d %H:%M})"
