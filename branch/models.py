from django.db import models

COUNTRIES = [
    ("India", "India"),
    ("United Arab Emirates", "UAE"),
    ("Saudi Arabia", "Saudi Arabia"),
    ("Qatar", "Qatar"),
    ("Kuwait", "Kuwait"),
    ("Oman", "Oman"),
    ("Bahrain", "Bahrain"),
    ("United States", "USA"),
    ("United Kingdom", "UK"),
    ("Canada", "Canada"),
    ("Australia", "Australia"),
]

CURRENCY_CODES = {
    "India": "INR",
    "United Arab Emirates": "AED",
    "Saudi Arabia": "SAR",
    "Qatar": "QAR",
    "Kuwait": "KWD",
    "Oman": "OMR",
    "Bahrain": "BHD",
    "United States": "USD",
    "United Kingdom": "GBP",
    "Canada": "CAD",
    "Australia": "AUD",
}

class Branch(models.Model):
    AUTO_CUT_CHOICES = [
        ('disable', 'Disable'),
        ('enable', 'Enable'),
    ]

    name = models.CharField(max_length=200)
    place = models.CharField(max_length=200, default="")
    country = models.CharField(max_length=100, choices=COUNTRIES, default="India")
    currency_code = models.CharField(max_length=10, default="INR")
    auto_cut = models.CharField(max_length=10, choices=AUTO_CUT_CHOICES, default='disable')

    def save(self, *args, **kwargs):
        self.currency_code = CURRENCY_CODES.get(self.country, "INR")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
