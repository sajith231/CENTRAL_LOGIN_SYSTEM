from django.db import models
from MobileApp.models import MobileControl, MobileProject
from ModuleAndPackage.models import Package
import random, string


class DemoMobileLicense(models.Model):
    # OG based demo
    original_license = models.ForeignKey(
        MobileControl,
        on_delete=models.CASCADE,
        related_name="demo_licenses",
        null=True,
        blank=True
    )

    # MANUAL DEMO FIELDS
    company_name = models.CharField(max_length=255, null=True, blank=True)
    project = models.ForeignKey(
        MobileProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    demo_license = models.CharField(max_length=30, unique=True)
    demo_login_limit = models.PositiveIntegerField(default=1)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def _generate_demo_key(self):
        raw = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"DEMO-{raw}"

    def save(self, *args, **kwargs):
        if not self.demo_license:
            key = self._generate_demo_key()
            while DemoMobileLicense.objects.filter(demo_license=key).exists():
                key = self._generate_demo_key()
            self.demo_license = key

        super().save(*args, **kwargs)

    def __str__(self):
        if self.original_license:
            return f"{self.demo_license} (OG)"
        return f"{self.demo_license} (Manual)"
