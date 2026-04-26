
from django.db import models
from django.utils import timezone
from datetime import timedelta
import string
import secrets
import re

class PagoRecibidoMP(models.Model):
    payment_id = models.CharField(max_length=100, unique=True)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20)
    payer_email = models.EmailField(blank=True,null=True)
    transaction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=50)
    external_reference = models.CharField(max_length=100, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago {self.payment_id} - {self.status}"

class TicketDePago(models.Model):
    class Estado(models.TextChoices):
        APROBADO = 'aprobado', 'Aprobado'
        RECHAZADO = 'rechazado', 'Rechazado'
        PENDIENTE = 'pendiente', 'Pendiente'

    class Tipo(models.TextChoices):
        MPAGO = 'mercado_pago', 'Mercado Pago'
        TRANS = 'transferencia', 'Transferencia'

    venta = models.ForeignKey("orders.Venta",on_delete=models.CASCADE,related_name='tickets')
    estado = models.CharField(max_length=20,choices=Estado.choices,default=Estado.PENDIENTE)
    tipo = models.CharField(max_length=20,choices=Tipo.choices,default=Tipo.MPAGO)
    monto = models.DecimalField(max_digits=10,decimal_places=2)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True,blank=True,null=True)

    class Meta:
        verbose_name = "Ticket"
        verbose_name_plural = "Tickets"

    def expirado(self) -> bool:
        """
        Verifica si el ticket ha expirado (30 minutos desde su creación).
        """
        return timezone.now() > self.creado + timedelta(minutes=30)

    def cancelar_ticket(self) -> None:
        """
        Cancela el ticket estableciendo su estado a 'rechazado'.
        """
        self.venta.estado = 'rechazado'
        self.venta.save(update_fields=['estado'])
        self.delete()

    def get_preference_data(self) -> dict:
        """
        Obtiene los datos de preferencia para la integración con Mercado Pago.
        """
        if self.expirado():
            raise ValueError("El ticket ha expirado.")
        data = self.venta.facturacion
        match = re.match(r'^(.*?)(?:\s+(\d+))?$', data.direccion.strip())
        if match:
            calle_nombre = match.group(1).strip()
            calle_altura = match.group(2) if match.group(2) else ''
        metadata = {
            'nombre':data.nombre,
            'apellido':data.apellido,
            'dni_cuit':data.dni_cuit,
            'ident_type':'DNI' if data.condicion_iva == 'B' else 'CUIT',
            'email':self.venta.usuario.email,
            'codigo_postal':data.codigo_postal,
            'ticket_id':self.id,
            'numero':self.monto,
            'metadata':{'ticket':self.id},
            'calle_nombre':calle_nombre,
            'calle_altura':calle_altura,
            'backurl_success':f"usuario/micuenta/?section=orders&compra=exitosa&idcompra={self.venta.merchant_order_id}",
            'backurl_fail':f"usuario/micuenta/?section=orders&compra=fallida&idcompra={self.venta.merchant_order_id}"
        }
        return metadata

    def __str__(self):
        return f"#{self.id} Tipo: {self.tipo} - Monto: {self.monto}"

class Cupon(models.Model):
    codigo = models.CharField(unique=True,max_length=6,blank=True)
    descuento = models.DecimalField(max_digits=5,decimal_places=2)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cupón"
        verbose_name_plural = "Cupones"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self.generar_codigo()
        else:
            self.codigo = self.codigo.upper()
        super().save(*args, **kwargs)

    def generar_codigo(self,longitud=6):
        letras = string.ascii_uppercase
        while True:
            nuevo_codigo = ''.join(secrets.choice(letras) for _ in range(longitud))
            if not Cupon.objects.filter(codigo=nuevo_codigo).exists():
                return nuevo_codigo

    def __str__(self):
        return f"{self.codigo} - %{self.descuento}"

class DatosBancarios(models.Model):
    """
    Información bancaria para pagos.
    """
    banco = models.CharField(max_length=100,default="")
    titular_cuenta = models.CharField(max_length=100,default="")
    numero_cuenta = models.CharField(max_length=50,default="")
    cbu = models.CharField(max_length=50,default="")
    alias = models.CharField(max_length=50,default="")
    imagen_banco = models.ImageField(upload_to='bancos_logos/', help_text="Logo del banco. (Opcional)", null=True, blank=True)

    class Meta:
        verbose_name = "Dato Bancario"
        verbose_name_plural = "Datos Bancarios"

    def __str__(self):
        return f"{self.banco} - {self.titular_cuenta}"

class MercadoPagoConfig(models.Model):
    """
    Configuración de MercadoPago.
    """
    public_key = models.CharField(max_length=200, default="", help_text="Clave pública de MercadoPago.")
    access_token = models.CharField(max_length=200, default="", help_text="Token de acceso de MercadoPago.")
    webhook_key = models.CharField(max_length=200, default="", help_text="Clave para poder recibir pagos.")

    class Meta:
        verbose_name = "Configuración de MercadoPago"
        verbose_name_plural = "Configuraciones de MercadoPago"

    def __str__(self):
        return "MercadoPago"