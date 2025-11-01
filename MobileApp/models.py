from django.db import models

# Create your models here.
from django.db import models

class MobileProject(models.Model):
    project_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.project_name
