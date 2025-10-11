from django.db import models

BRANCH_CHOICES = [
    ("RITS TANZANIA","RITS TANZANIA"),
    ("RITS OMAN","RITS OMAN"),
    ("IMC CHAVAKKAD","IMC CHAVAKKAD"),
    ("SMART","SMART"),
    ("ZENOX","ZENOX"),
    ("WINWAY","WINWAY"),
    ("SYSMAC KTTYADI","SYSMAC KTTYADI"),
    ("RITS UAE","RITS UAE"),
    ("SATHYAM","SATHYAM"),
    ("RUBIX","RUBIX"),
    ("RITS KSA","RITS KSA"),
    ("RITS QATAR","RITS QATAR"),
    ("RITS H.O","RITS H.O"),
    ("IMC MUKKAM","IMC MUKKAM"),
    ("IMC KOOTHUPARAMBA","IMC KOOTHUPARAMBA"),
    ("IMC KOLLAM","IMC KOLLAM"),
    ("IMC PALAKKAD","IMC PALAKKAD"),
    ("IMC","IMC"),
    ("FLASH INNOVATIONS","FLASH INNOVATIONS"),
    ("FINAAX","FINAAX"),
    ("ASTRIC","ASTRIC"),
    ("APEXMAX","APEXMAX"),
    ("ABSY IT SOLUTIONS","ABSY IT SOLUTIONS"),
    ("SYSMAC","SYSMAC"),
]

LEVEL_CHOICES = [
    ("Super Admin", "Super Admin"),
    ("Admin", "Admin"),
    ("User", "User"),
]

class Users(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # store a HASH here
    branch = models.CharField(max_length=100, choices=BRANCH_CHOICES)  # was: role
    user_role = models.CharField(max_length=100)  # NEW: free text, not a dropdown
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"
