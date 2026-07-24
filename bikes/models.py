from django.db import models
from django.contrib.auth.models import User
import random, string
from django.utils import timezone


class Bike(models.Model):
    FUEL_CHOICES = [('Petrol', 'Petrol'), ('Electric', 'Electric')]

    bike_name           = models.CharField(max_length=200)
    brand               = models.CharField(max_length=100, db_index=True)
    year                = models.IntegerField(db_index=True)
    fuel_type           = models.CharField(max_length=20, choices=FUEL_CHOICES, db_index=True)
    kms_driven          = models.IntegerField()
    engine_capacity_cc  = models.IntegerField(default=0)
    price_usd           = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-year', 'brand', 'bike_name']

    def __str__(self):
        return f"{self.bike_name} ({self.year}) — ${self.price_usd}"


class EmailVerification(models.Model):
    """Stores one-time email verification codes for signup."""
    email      = models.EmailField()
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    used       = models.BooleanField(default=False)

    @staticmethod
    def generate_code():
        return ''.join(random.choices(string.digits, k=6))

    def is_expired(self):
        from django.conf import settings
        expiry = getattr(settings, 'VERIFICATION_CODE_EXPIRY', 10)
        return (timezone.now() - self.created_at).total_seconds() > expiry * 60

    def __str__(self):
        return f"{self.email} — {self.code}"
