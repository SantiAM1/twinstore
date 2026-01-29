from django.db import models
from django.conf import settings
from core.models import Tienda

# Create your models here.
class ShippingConfig(models.Model):
    PROVIDER_CHOICES = [
        ('zipnova', 'Zipnova (Argentina)'),
        # > Futuro: ('andreani', 'Andreani'),
        # > ... ('oca', 'OCA'),
    ]

    AUTH_TYPE_CHOICES = [
        ('basic', 'Basic Auth (Legacy/Manual)'),
        ('oauth', 'OAuth 2.0'),
    ]

    provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES, default='zipnova')
    auth_type = models.CharField(max_length=20, choices=AUTH_TYPE_CHOICES, default='basic')
    
    credentials = models.JSONField(default=dict, blank=True)
    defaults = models.JSONField(default=dict, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Configuración {self.provider}"