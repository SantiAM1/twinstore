from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from datetime import timedelta
import string
import secrets
import re
from django.core import signing

class HistorialCompras(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente🟡'),
        ('confirmado', 'Confirmado🟢'),
        ('rechazado', 'Rechazado🔴'),
        ('preparando pedido','Preparando pedido🔵'),
        ('listo para retirar','Listo para retirar✔️'),
        ('enviado','Enviado🟣'),
        ('finalizado','Finalizado⚪'),
        ('arrepentido', 'Arrepentido⭕')
    ]

    FORMA_DE_PAGO = [
        ('efectivo','Efectivo'),
        ('mercadopago','Mercado Pago'),
        ('transferencia','Transferencia'),
        ('mixto','Mixto')
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    productos = models.JSONField()
    total_compra = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    forma_de_pago = models.CharField(max_length=20,choices=FORMA_DE_PAGO,default='efectivo')
    pagos = models.ManyToManyField("PagoRecibidoMP", blank=True,editable=False)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True,unique=True)
    token_consulta = models.UUIDField(default=uuid.uuid4, unique=True)
    recibir_mail = models.BooleanField(default=False)
    fecha_finalizado = models.DateTimeField(null=True,blank=True)
    requiere_revision = models.BooleanField(default=True)

    def check_comprobante_subido(self):
        return hasattr(self, 'comprobante')

    def check_historial(self):
        if self.estado == 'confirmado':
            return

        if self.forma_de_pago == 'transferencia':
            self.estado = 'confirmado'

        elif self.forma_de_pago == 'mercadopago':
            ticket = self.tickets.first()
            if ticket and ticket.estado == 'aprobado':
                self.estado = 'confirmado'

        elif self.forma_de_pago == 'mixto':
            ticket = self.tickets.first()
            if self.check_comprobante_subido() and ticket:
                if self.comprobante.estado == 'aprobado' and ticket.estado == 'aprobado':
                    self.estado = 'confirmado'
        
        if self.estado == 'confirmado':
            self.save(update_fields=["estado"])

    def check_link_pago(self):
        return True if self.forma_de_pago in ['mixto','mercadopago']  else False
    
    def check_ticket_mp(self):
        ticket = self.tickets.first()
        if ticket:
            if ticket.merchant_order_id:
                return True
        return False

    def ticket_mp(self):
        return self.tickets.first()

    def mp_ticket_id_signed(self):
        mercadopago = self.tickets.first()
        if mercadopago:
            return signing.dumps(mercadopago.id)
        return None

    def monto_tranferir(self):
        if self.forma_de_pago == 'transferencia':
            return self.total_compra
        ticket = self.tickets.first()
        return self.total_compra - ticket.monto

    def __str__(self):
        if self.usuario:
            nombre = self.usuario
        elif hasattr(self, "facturacion"):
            nombre = f"{self.facturacion.nombre} {self.facturacion.apellido} ({self.facturacion.dni_cuit})"
        else:
            nombre = "Anónimo"

        return f"{self.merchant_order_id} - {self.estado} - {nombre}"

    def get_adicional(self):
        if self.forma_de_pago not in ['mixto','mercadopago']:
            return 0
        
        subtotal = sum(Decimal(str(p['subtotal'])) for p in self.productos)
        total = Decimal(str(self.total_compra))
        
        return total - subtotal

    def check_notificacion(self):
        return True if not self.estado in ['arrepentido','finalizado','rechazado'] else False

    def check_comprobante(self):
        return True if (self.forma_de_pago in ['transferencia','mixto']  and not self.estado in ['finalizado','arrepentido']) else False

    def check_arrepentimiento(self):
        if self.fecha_finalizado and self.estado == 'finalizado':
            limite = self.fecha_finalizado + timedelta(days=10)
            return timezone.now() <= limite
        return False

class EstadoPedido(models.Model):
    historial = models.ForeignKey(HistorialCompras, on_delete=models.CASCADE, related_name='estados')
    estado = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)
    comentario = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"_____________{self.estado}"
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
    ESTADOS = [
        ('aprobado','Aprobado'),
        ('rechazado','Rechazado'),
    ]
    historial = models.ForeignKey(HistorialCompras,on_delete=models.CASCADE,related_name='tickets')
    estado = models.CharField(max_length=20,choices=ESTADOS,default='pendiente')
    monto = models.DecimalField(max_digits=10,decimal_places=2)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)

    def get_preference_data(self) -> dict:
        data = self.historial.facturacion
        match = re.match(r'^(.*?)(?:\s+(\d+))?$', data.calle.strip())
        if match:
            calle_nombre = match.group(1).strip()
            calle_altura = match.group(2) if match.group(2) else ''
        metadata = {
            'nombre':data.nombre,
            'apellido':data.apellido,
            'dni_cuit':data.dni_cuit,
            'ident_type':'DNI' if data.condicion_iva == 'B' else 'CUIT',
            'email':data.email,
            'codigo_postal':data.codigo_postal,
            'ticket_id':self.id,
            'numero':self.monto,
            'metadata':{'ticket':self.id},
            'calle_nombre':calle_nombre,
            'calle_altura':calle_altura,
            'backurl_success':f"usuario/ver_pedido/{self.historial.token_consulta}",
            'backurl_fail':f"usuario/ver_pedido/{self.historial.token_consulta}?compra=fallida"
        }
        return metadata

    def __str__(self):
        return f"Monto a depositar: {self.monto}"

class ComprobanteTransferencia(models.Model):
    ESTADOS = [
        ('aprobado','Aprobado'),
        ('rechazado','Rechazado'),
        ('no verificado','No verificado')
    ]

    historial = models.OneToOneField("HistorialCompras", on_delete=models.CASCADE, related_name="comprobante")
    file = models.FileField(upload_to="comprobantes/")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20,choices=ESTADOS,default='no verificado')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Comprobante de {self.historial.merchant_order_id}"

class Cupon(models.Model):
    codigo = models.CharField(unique=True,max_length=6,blank=True)
    descuento = models.DecimalField(max_digits=5,decimal_places=2)
    creado = models.DateTimeField(auto_now_add=True)

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
