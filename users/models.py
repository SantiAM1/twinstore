from django.db import models
from django.contrib.auth.models import User
import random
from django.db import models
from django.utils import timezone
from datetime import timedelta

class PerfilUsuario(models.Model):
    FACTURA_CHOICES = [
        ('A', 'Resp Insc.'),
        ('B', 'Consumidor final'),
        ('C', 'Mono'),
    ]

    PROVINCIA_CHOICES = [
        ('A', 'Ciudad Autónoma de Buenos Aires'),
        ('B', 'Buenos Aires'),
        ('C', 'Catamarca'),
        ('D', 'Chaco'),
        ('E', 'Chubut'),
        ('F', 'Córdoba'),
        ('G', 'Corrientes'),
        ('H', 'Entre Ríos'),
        ('I', 'Formosa'),
        ('J', 'Jujuy'),
        ('K', 'La Pampa'),
        ('L', 'La Rioja'),
        ('M', 'Mendoza'),
        ('N', 'Misiones'),
        ('O', 'Neuquén'),
        ('P', 'Río Negro'),
        ('Q', 'Salta'),
        ('R', 'San Juan'),
        ('S', 'San Luis'),
        ('T', 'Santa Cruz'),
        ('U', 'Santa Fe'),
        ('V', 'Santiago del Estero'),
        ('W', 'Tierra del Fuego'),
        ('X', 'Tucumán'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    nombre = models.CharField(max_length=50, blank=True, default="")
    apellido = models.CharField(max_length=50, blank=True, default="")
    razon_social = models.CharField(max_length=255, blank=True, default="")
    dni_cuit = models.CharField(max_length=20, blank=True, default="")
    condicion_iva = models.CharField(max_length=1, choices=FACTURA_CHOICES)
    email_verificado = models.BooleanField(default=False)
    telefono = models.CharField(max_length=20, blank=True, default="")
    codigo_postal = models.CharField(max_length=10, blank=True, default="")
    provincia = models.CharField(max_length=1, choices=PROVINCIA_CHOICES, blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    localidad = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"Perfil de {self.user.username}"

class DatosFacturacion(models.Model):
    FACTURA_CHOICES = [
        ('A', 'Resp Insc.'),
        ('B', 'Consumidor final'),
        ('C', 'Mono'),
    ]

    PROVINCIA_CHOICES = PerfilUsuario.PROVINCIA_CHOICES

    historial = models.OneToOneField("payment.HistorialCompras", on_delete=models.CASCADE, related_name="facturacion")

    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    razon_social = models.CharField(max_length=255, blank=True)
    dni_cuit = models.CharField(max_length=20)
    condicion_iva = models.CharField(max_length=1, choices=FACTURA_CHOICES)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    codigo_postal = models.CharField(max_length=10)
    provincia = models.CharField(max_length=1, choices=PROVINCIA_CHOICES)
    direccion = models.CharField(max_length=255)
    localidad = models.CharField(max_length=255,null=True, blank=True)

    def __str__(self):
        return f"Datos Facturación #{self.id} - {self.nombre} {self.apellido}"

class TokenUsers(models.Model):
    TIPO = [
        ('recuperar', 'Recuperar'),
        ('verificar', 'Verificar'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_usuario')
    codigo = models.CharField(max_length=6, unique=True, editable=False)
    creado = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=30, choices=TIPO)

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo_unico()
        super().save(*args, **kwargs)

    def generar_codigo_unico(self):
        while True:
            codigo = f"{random.randint(0, 999999):06d}"
            if not TokenUsers.objects.filter(codigo=codigo).exists():
                return codigo

    def expirado(self):
        return timezone.now() > self.creado + timedelta(hours=1)

    def __str__(self):
        return f"{self.user.email} - {self.codigo} ({self.tipo})"

class DireccionEnvio(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="direcciones_envio")
    nombre_completo = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=100)
    provincia = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    instrucciones_adicionales = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Dirección de envío de {self.user.username} - {self.calle}, {self.ciudad}"