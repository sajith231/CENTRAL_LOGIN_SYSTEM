from django.db import models
from MobileApp.models import MobileControl

class DemoMobileLicense(models.Model):
    original_license = models.ForeignKey(
        MobileControl,
        on_delete=models.CASCADE,
        related_name="demo_licenses"
    )

    demo_license = models.CharField(max_length=30, unique=True)
    demo_login_limit = models.PositiveIntegerField(default=1)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.demo_license:
            self.demo_license = f"DEMO-{self.original_license.license_key}"
        super().save(*args, **kwargs)

