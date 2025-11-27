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
    client_id = models.CharField(max_length=50, unique=True, editable=False)

    def save(self, *args, **kwargs):
        # Generate Client ID only when creating a new shop
        if not self.client_id:
            base_name = ''.join(e for e in self.name.upper() if e.isalnum())  # remove spaces/symbols
            random_number = ''.join(random.choices(string.digits, k=3))
            generated_id = f"{base_name}{random_number}"

            # Ensure it's unique (avoid duplicate random numbers)
            while Shop.objects.filter(client_id=generated_id).exists():
                random_number = ''.join(random.choices(string.digits, k=3))
                generated_id = f"{base_name}{random_number}"

            self.client_id = generated_id

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.client_id})"
