

from django.db import models
from django.utils import timezone
from datetime import timedelta
from MobileApp.models import MobileControl, MobileProject
from ModuleAndPackage.models import Package
import random, string


class DemoMobileLicense(models.Model):
    original_license = models.ForeignKey(
        MobileControl,
        on_delete=models.CASCADE,
        related_name="demo_licenses",
        null=True,
        blank=True
    )

    company_name = models.CharField(max_length=255, null=True, blank=True)
    project = models.ForeignKey(MobileProject, on_delete=models.SET_NULL, null=True, blank=True)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)

    demo_license = models.CharField(max_length=30, unique=True)
    demo_login_limit = models.PositiveIntegerField(default=1)

    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 🔹 NEW
    expires_at = models.DateTimeField(null=True, blank=True)

    def _generate_demo_key(self):
        raw = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"DEMO-{raw}"

    def save(self, *args, **kwargs):
        if not self.demo_license:
            key = self._generate_demo_key()
            while DemoMobileLicense.objects.filter(demo_license=key).exists():
                key = self._generate_demo_key()
            self.demo_license = key

        # 🔹 auto set expiry = created + 5 days
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=5)

        super().save(*args, **kwargs)

    def is_expired(self):
        return self.expires_at and timezone.now() > self.expires_at
