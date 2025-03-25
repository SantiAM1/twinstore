from django.db import models
from django.contrib.auth.models import User

class DatosEnvio(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='direcciones_envio')
    calle = models.CharField(max_length=50)
    altura = models.PositiveIntegerField(null=True, blank=True)
    ciudad = models.CharField(max_length=50)
    provincia = models.CharField(max_length=50, null=True, blank=True)
    codigo_postal = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.calle} {self.altura or ''}, {self.ciudad}"
    