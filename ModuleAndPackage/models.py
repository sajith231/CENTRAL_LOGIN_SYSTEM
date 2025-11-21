from django.db import models


class Module(models.Model):
    project = models.ForeignKey("MobileApp.MobileProject", on_delete=models.CASCADE, related_name="modules")
    module_name = models.CharField(max_length=200)
    module_code = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['module_name']

    def save(self, *args, **kwargs):
        # Auto-generate unique code
        if not self.module_code:
            last = Module.objects.all().order_by("-id").first()
            if last and last.module_code.startswith("MOD"):
                number = int(last.module_code.replace("MOD", "")) + 1
            else:
                number = 1
            self.module_code = f"MOD{number:03d}"  # MOD001, MOD002...
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.module_name} ({self.project.project_name})"




from django.db import models

from .models import Module    # already exists

class Package(models.Model):
    project = models.ForeignKey("MobileApp.MobileProject", on_delete=models.CASCADE)
    modules = models.ManyToManyField(Module)
    package_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.package_name