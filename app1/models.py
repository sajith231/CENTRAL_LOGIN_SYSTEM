from django.db import models
import os
import uuid

# ----------------- CHOICES -----------------

BRANCH_CHOICES = [
    ("RITS TANZANIA", "RITS TANZANIA"),
    ("RITS OMAN", "RITS OMAN"),
    ("IMC CHAVAKKAD", "IMC CHAVAKKAD"),
    ("SMART", "SMART"),
    ("ZENOX", "ZENOX"),
    ("WINWAY", "WINWAY"),
    ("SYSMAC KTTYADI", "SYSMAC KTTYADI"),
    ("RITS UAE", "RITS UAE"),
    ("SATHYAM", "SATHYAM"),
    ("RUBIX", "RUBIX"),
    ("RITS KSA", "RITS KSA"),
    ("RITS QATAR", "RITS QATAR"),
    ("RITS H.O", "RITS H.O"),
    ("IMC MUKKAM", "IMC MUKKAM"),
    ("IMC KOOTHUPARAMBA", "IMC KOOTHUPARAMBA"),
    ("IMC KOLLAM", "IMC KOLLAM"),
    ("IMC PALAKKAD", "IMC PALAKKAD"),
    ("IMC", "IMC"),
    ("FLASH INNOVATIONS", "FLASH INNOVATIONS"),
    ("FINAAX", "FINAAX"),
    ("ASTRIC", "ASTRIC"),
    ("APEXMAX", "APEXMAX"),
    ("ABSY IT SOLUTIONS", "ABSY IT SOLUTIONS"),
    ("SYSMAC", "SYSMAC"),
]

LEVEL_CHOICES = [
    ("Super Admin", "Super Admin"),
    ("Admin", "Admin"),
    ("User", "User"),
]

# ----------------- HELPERS -----------------

def user_image_upload_to(instance, filename):
    """
    Generate a clean unique filename for uploaded profile pictures.
    Prevents spaces/special characters that could break R2 URLs.
    """
    ext = os.path.splitext(filename)[1].lower()  # keep file extension
    new_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join("profile_pics", new_filename)

# ----------------- MAIN MODEL -----------------

class Users(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # ⚠️ Consider using hashed passwords later
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES)
    user_role = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    profile_image = models.ImageField(
        upload_to=user_image_upload_to, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"
