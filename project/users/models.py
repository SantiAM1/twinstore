from django.db import models
from django.contrib.auth.models import User
import uuid

from django.db import models
from django.contrib.auth.models import User
import uuid

from payment.models import HistorialCompras

class PerfilUsuario(models.Model):
    FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('C', 'Factura C'),
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
    tipo_factura = models.CharField(max_length=1, choices=FACTURA_CHOICES)
    email_verificado = models.BooleanField(default=False)
    token_verificacion = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, null=True, blank=True)
    preferencias_promociones = models.BooleanField(default=False)
    preferencias_estado_pedido = models.BooleanField(default=False)
    telefono = models.CharField(max_length=20, blank=True, default="")
    codigo_postal = models.CharField(max_length=10, blank=True, default="")
    provincia = models.CharField(max_length=1, choices=PROVINCIA_CHOICES, blank=True, default="")
    calle = models.CharField(max_length=255, blank=True, default="")
    ciudad = models.CharField(max_length=255, blank=True, default="")
    calle_detail = models.CharField(max_length=255, blank=True, default="")
    guardar_datos = models.BooleanField(default=False)

    def __str__(self):
        return f"Perfil de {self.user.username}"

class DatosFacturacion(models.Model):
    FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('C', 'Factura C'),
    ]

    PROVINCIA_CHOICES = PerfilUsuario.PROVINCIA_CHOICES

    historial = models.OneToOneField("payment.HistorialCompras", on_delete=models.CASCADE, related_name="facturacion")

    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    razon_social = models.CharField(max_length=255, blank=True)
    dni_cuit = models.CharField(max_length=20)
    tipo_factura = models.CharField(max_length=1, choices=FACTURA_CHOICES)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    codigo_postal = models.CharField(max_length=10)
    provincia = models.CharField(max_length=1, choices=PROVINCIA_CHOICES)
    calle = models.CharField(max_length=255)
    ciudad = models.CharField(max_length=255,null=True, blank=True)
    calle_detail = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Datos Facturación #{self.id} - {self.nombre} {self.apellido}"

