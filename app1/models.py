from django.db import models
import os
import uuid

LEVEL_CHOICES = [
    ("Super Admin", "Super Admin"),
    ("Admin", "Admin"),
    ("User", "User"),
]

def user_image_upload_to(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    new_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join("profile_pics", new_filename)

class Users(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    branch = models.ForeignKey('branch.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    user_role = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    profile_image = models.ImageField(
        upload_to=user_image_upload_to, blank=True, null=True
    )
    # 🔴 NEW FIELD – will store list of allowed submenu IDs
    allowed_menus = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"






