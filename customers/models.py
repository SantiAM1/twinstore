from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

# Create your models here.
class Client(TenantMixin):
    class Plan(models.TextChoices):
        BASIC = 'basic', 'Basico'
        PREMIUM = 'premium', 'Premium'

    name = models.CharField(max_length=100)
    created_on = models.DateField(auto_now_add=True)
    plan = models.CharField(max_length=7, choices=Plan.choices, default=Plan.BASIC)

    def __str__(self):
        return self.name

class Domain(DomainMixin):
    def __str__(self):
        return self.domain