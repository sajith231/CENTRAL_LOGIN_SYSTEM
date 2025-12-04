from django.db import models
import random
import string
from branch.models import Branch



class Store(models.Model):
    name = models.CharField(max_length=100)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    place = models.CharField(max_length=150, null=True, blank=True)
    store_id = models.CharField(max_length=10, unique=True, editable=False, null=True, blank=True)


    def save(self, *args, **kwargs):
        if not self.store_id:
            import random, string
            characters = string.ascii_uppercase + string.digits
            unique_id = ''.join(random.choices(characters, k=10))

            while Store.objects.filter(store_id=unique_id).exists():
                unique_id = ''.join(random.choices(characters, k=10))

            self.store_id = unique_id

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.store_id})"



class Shop(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    place = models.CharField(max_length=150, null=True, blank=True)
    email = models.EmailField()
    contact_no = models.CharField(max_length=15)

    # 13 characters now
    client_id = models.CharField(max_length=13, unique=True, editable=False)

    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.client_id:
            characters = string.ascii_uppercase + string.digits
            client_id = ''.join(random.choices(characters, k=13))

            while Shop.objects.filter(client_id=client_id).exists():
                client_id = ''.join(random.choices(characters, k=13))

            self.client_id = client_id

        super().save(*args, **kwargs)
