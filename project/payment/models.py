from django.db import models
from django.contrib.auth.models import User
import uuid

class HistorialCompras(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('confirmado', 'Confirmado'),
        ('rechazado', 'Rechazado'),
        ('preparando pedido','Preparando pedido'),
        ('enviado','Enviado'),
        ('finalizado','Finalizado')
    ]

    FORMA_DE_PAGO = [
        ('efectivo','Efectivo'),
        ('mercado pago','Mercado Pago'),
        ('transferencia','Transferencia')
    ]

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    productos = models.JSONField()
    total_compra = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    forma_de_pago = models.CharField(max_length=20,choices=FORMA_DE_PAGO,default='efectivo')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    pagos = models.ManyToManyField("PagoRecibidoMP", blank=True,editable=False)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)
    token_consulta = models.UUIDField(default=uuid.uuid4, unique=True)

    def __str__(self):
        return f"Compra {self.id} - {self.estado} - {self.usuario if self.usuario else 'Anónimo'}"
    
    def pagos_completos(self):
        return all(p.status == "approved" for p in self.pagos.all())

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