from django.db import models
import re
from ModuleAndPackage.models import Package
from branch.models import Branch

class MobileProject(models.Model):
    project_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    customized_package = models.BooleanField(default=False)  # ← ADD THIS
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # API endpoint (auto-generated from project_name)
    api_endpoint = models.CharField(max_length=250, unique=True, editable=False)

    class Meta:
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        # Auto-generate API endpoint from project_name
        # Remove spaces, convert to lowercase
        self.api_endpoint = re.sub(r'\s+', '', self.project_name).lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.project_name
    
    def get_api_url(self):
        """Returns the full GET API URL"""
        return f"/api/project/{self.api_endpoint}/"
    
    def post_api_url(self):
        """Returns the full POST API URL"""
        return f"/api/project/{self.api_endpoint}/login/"


from StoreShop.models import Store, Shop

from django.utils import timezone

from django.db import models
from StoreShop.models import Store, Shop
from ModuleAndPackage.models import Package
import random, string


import random, string

class MobileControl(models.Model):
    project = models.ForeignKey('MobileProject', on_delete=models.CASCADE, related_name='controls')
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)

    customer_name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=200)

    # 16 chars + 3 hyphens = 19
    license_key = models.CharField(max_length=19, unique=True, null=True, blank=True, editable=False)

    login_limit = models.PositiveIntegerField(default=0)

    LICENCE_TYPE_CHOICES = [
        ('new', 'New Licence'),
        ('transfer', 'Transfer Licence'),
        ('developer', 'Developer Licence'),
    ]
    licence_type = models.CharField(
        max_length=20,
        choices=LICENCE_TYPE_CHOICES,
        default='new',
    )

    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)
    # When billing uses a custom (one-off) package, this is set; standard package field is cleared
    active_custom_package = models.ForeignKey(
        'CustomPackage', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='active_controls'
    )
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)

    status = models.BooleanField(default=False)
    bill_status = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    expiry_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_date']

    def _generate_license_key(self):
        chars = string.ascii_uppercase + string.digits
        raw = ''.join(random.choices(chars, k=16))      # 16 chars total
        # group into 4-4-4-4 with '-'
        return '-'.join(raw[i:i+4] for i in range(0, 16, 4))

    def save(self, *args, **kwargs):
        if not self.license_key:
            key = self._generate_license_key()
            # ensure unique
            while MobileControl.objects.filter(license_key=key).exists():
                key = self._generate_license_key()
            self.license_key = key

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer_name} - {self.license_key}"


    
    


class LoginLog(models.Model):
    """Tracks login attempts for each client"""
    control = models.ForeignKey(MobileControl, on_delete=models.CASCADE, related_name='login_logs')
    client_id = models.CharField(max_length=200)
    logged_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-logged_at']
    
    def __str__(self):
        return f"{self.client_id} logged at {self.logged_at}"




from mobile_demo_licencing.models import DemoMobileLicense

class ActiveDevice(models.Model):
    control = models.ForeignKey(
        MobileControl,
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="active_devices"
    )
    demo_license = models.ForeignKey(
        DemoMobileLicense,
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="active_devices"
    )

    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    logged_in_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.device_id






class MobileBillingHistory(models.Model):
    control = models.ForeignKey(
        MobileControl,
        on_delete=models.CASCADE,
        related_name="billing_history"
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    custom_package = models.ForeignKey(
        'CustomPackage',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # allow + / - values
    extended_days = models.IntegerField(default=0)
    extended_login_limit = models.IntegerField(default=0)

    old_expiry_date = models.DateTimeField(null=True, blank=True)
    new_expiry_date = models.DateTimeField(null=True, blank=True)

    old_login_limit = models.PositiveIntegerField()
    new_login_limit = models.PositiveIntegerField()

    bill_status = models.BooleanField(default=False)
    PAYMENT_STATUS_CHOICES = [
        ('Paid', 'Paid'),
        ('Partially Paid', 'Partially Paid'),
        ('Not Paid', 'Not Paid'),
        ('Not Applicable', 'Not Applicable'),
    ]
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='Not Paid'
    )
    invoice_number = models.CharField(max_length=100, null=True, blank=True)
    invoice_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    remark = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.control.client_id} | {self.created_at}"

    @property
    def license_age_days(self):
        """Returns the age of the license in days at the time this record was created."""
        if not self.control.created_date:
            return 0
        delta = self.created_at - self.control.created_date
        return max(0, delta.days)


# ── Custom (one-off) packages — per MobileControl, hidden from global Package tables ──

class CustomPackage(models.Model):
    """A one-off package created directly from the billing page for a specific client.
    Not related to the global ModuleAndPackage.Package model."""
    control = models.ForeignKey(
        MobileControl,
        on_delete=models.CASCADE,
        related_name='custom_packages'
    )
    package_name = models.CharField(max_length=200)
    days_limit = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[Custom] {self.package_name} ({self.control.customer_name})"


class CustomPackageModule(models.Model):
    """A module that belongs to a CustomPackage."""
    package = models.ForeignKey(
        CustomPackage,
        on_delete=models.CASCADE,
        related_name='modules'
    )
    module_name = models.CharField(max_length=200)
    module_code = models.CharField(max_length=255, blank=True, null=True)  # ← ADD THIS

    def __str__(self):
        return self.module_name