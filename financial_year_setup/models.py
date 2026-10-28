from django.db import models


class FinancialYearLock(models.Model):
    """Local audit record for a country financial year locked in the central service."""

    financial_year_id = models.PositiveIntegerField(unique=True)
    country_name = models.CharField(max_length=150, blank=True)
    country_code = models.CharField(max_length=10, blank=True)
    locked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-locked_at",)

    def __str__(self):
        return f"{self.country_code or self.country_name} ({self.financial_year_id})"
