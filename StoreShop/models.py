from django.db import models
import random
import string

class Store(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Shop(models.Model):
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
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
