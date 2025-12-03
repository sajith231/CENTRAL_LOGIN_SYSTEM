from django.db import models
import re
from ModuleAndPackage.models import Package

class MobileProject(models.Model):
    project_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
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


class MobileControl(models.Model):
    project = models.ForeignKey('MobileProject', on_delete=models.CASCADE, related_name='controls')
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)

    customer_name = models.CharField(max_length=255)
    client_id = models.CharField(max_length=200)

    # Unique License Key – NOT tied to project or client anymore
    license_key = models.CharField(max_length=10, unique=True, null=True, blank=True, editable=False)

    login_limit = models.PositiveIntegerField(default=1)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status field: True = Active, False = Inactive
    status = models.BooleanField(default=True)

    created_date = models.DateTimeField(auto_now_add=True)   # ✔️ include created date
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        if not self.license_key:
            chars = string.ascii_uppercase + string.digits
            key = ''.join(random.choices(chars, k=10))

            while MobileControl.objects.filter(license_key=key).exists():
                key = ''.join(random.choices(chars, k=10))

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




class ActiveDevice(models.Model):
    control = models.ForeignKey(MobileControl, on_delete=models.CASCADE, related_name='active_devices')
    device_id = models.CharField(max_length=255)
    logged_in_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        unique_together = ['control', 'device_id']

    def __str__(self):
        return f"{self.control.client_id} - {self.device_id}"
