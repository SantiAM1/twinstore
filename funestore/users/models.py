from django.db import models
from django.contrib.auth.models import User
import uuid

class PerfilUsuario(models.Model):
    FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('C', 'Factura C'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    razon_social = models.CharField(max_length=255, blank=True, default="")
    dni_cuit = models.CharField(max_length=20,blank=True,default="")
    tipo_factura = models.CharField(max_length=1, choices=FACTURA_CHOICES, default='B')
    email_verificado = models.BooleanField(default=False)
    token_verificacion = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)

    def __str__(self):
        return f"Perfil de {self.user}"
