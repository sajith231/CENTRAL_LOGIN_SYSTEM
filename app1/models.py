from django.db import models
import os
import uuid

# ----------------- CHOICES -----------------

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
    branch = models.ForeignKey('branch.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    user_role = models.CharField(max_length=100)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    profile_image = models.ImageField(
        upload_to=user_image_upload_to, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"





