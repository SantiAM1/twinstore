from django.db import models
from django.contrib.auth.models import User
import uuid

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    nombre = models.CharField(max_length=30, blank=True, default="")
    apellidos = models.CharField(max_length=60, blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    telefono = models.CharField(max_length=20, blank=True, default="")
    fecha_nacimiento = models.DateField(blank=True, null=True)
    razon_social = models.CharField(max_length=255, blank=True, default="")
    cuit = models.CharField(max_length=20, blank=True, default="")  # Validaremos en el form
    email_verificado = models.BooleanField(default=False)  # Evita acceso sin verificación
    token_verificacion = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True)  # Mejor indexado

    def __str__(self):
        return f"Perfil de {self.user.email}"  # Usa email en vez de username para identificación
