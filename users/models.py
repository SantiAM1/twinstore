from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from django.utils import timezone
from datetime import timedelta
from .managers import CustomUserManager

class User(AbstractUser):
    class CondicionIVA(models.TextChoices):
        RESP_INSC = 'A', 'Responsable Inscripto'
        CONSUMIDOR_FINAL = 'B', 'Consumidor Final'
        MONOTRIBUTO = 'C', 'Monotributo'
        EXENTO = 'E', 'Exento'
        NO_RESPONSABLE = 'N', 'No Responsable'
    
    class Provincia(models.TextChoices):
        CABA = 'A', 'Ciudad Autónoma de Buenos Aires'
        BUENOS_AIRES = 'B', 'Buenos Aires'
        CATAMARCA = 'C', 'Catamarca'
        CHACO = 'H', 'Chaco'
        CHUBUT = 'U', 'Chubut'
        CORDOBA = 'X', 'Córdoba'
        CORRIENTES = 'W', 'Corrientes'
        ENTRE_RIOS = 'E', 'Entre Ríos'
        FORMOSA = 'P', 'Formosa'
        JUJUY = 'Y', 'Jujuy'
        LA_PAMPA = 'L', 'La Pampa'
        LA_RIOJA = 'F', 'La Rioja'
        MENDOZA = 'M', 'Mendoza'
        MISIONES = 'N', 'Misiones'
        NEUQUEN = 'Q', 'Neuquén'
        RIO_NEGRO = 'R', 'Río Negro'
        SALTA = 'I', 'Salta'
        SAN_JUAN = 'J', 'San Juan'
        SAN_LUIS = 'D', 'San Luis'
        SANTA_CRUZ = 'Z', 'Santa Cruz'
        SANTA_FE = 'S', 'Santa Fe'
        SANTIAGO_ESTERO = 'G', 'Santiago del Estero'
        TIERRA_FUEGO = 'V', 'Tierra del Fuego'
        TUCUMAN = 'T', 'Tucumán'


    username = None
    email = models.EmailField("Dirección de email",unique=True)
    razon_social = models.CharField(max_length=255, blank=True, default="")
    dni_cuit = models.CharField(max_length=20, blank=True, default="")
    condicion_iva = models.CharField(max_length=1, choices=CondicionIVA.choices, default=CondicionIVA.CONSUMIDOR_FINAL)
    telefono = models.CharField(max_length=20, blank=True, default="")
    codigo_postal = models.CharField(max_length=10, blank=True, default="")
    provincia = models.CharField(max_length=1, choices=Provincia.choices, blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    localidad = models.CharField(max_length=255, blank=True, default="")
    email_verificado = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        # Muestra el email y, si tiene, la razón social o nombre
        identidad = self.razon_social or f"{self.first_name} {self.last_name}"
        if identidad.strip():
            return f"{self.email} ({identidad})"
        return self.email

    @property
    def nombre_completo(self):
        """Helper para obtener el nombre real o la razón social"""
        if self.razon_social:
            return self.razon_social
        return f"{self.first_name} {self.last_name}".strip()

class DatosFacturacion(models.Model):

    venta = models.OneToOneField("payment.Venta", on_delete=models.CASCADE, related_name="facturacion")

    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    razon_social = models.CharField(max_length=255, blank=True)
    dni_cuit = models.CharField(max_length=20)
    condicion_iva = models.CharField(max_length=1, choices=User.CondicionIVA.choices)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    codigo_postal = models.CharField(max_length=10)
    provincia = models.CharField(max_length=1, choices=User.Provincia.choices)
    direccion = models.CharField(max_length=255)
    localidad = models.CharField(max_length=255,null=True, blank=True)

    class Meta:
        verbose_name = "Facturación"
        verbose_name_plural = "Datos de Facturación"

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