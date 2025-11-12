from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import string
import secrets
import re
from django.core import signing
from products.models import TokenReseña, Producto,ReseñaProducto

class HistorialCompras(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente🟡'),
        ('confirmado', 'Confirmado🟢'),
        ('rechazado', 'Rechazado🔴'),
        ('listo para retirar','Listo para retirar✔️'),
        ('enviado','Enviado🟣'),
        ('finalizado','Finalizado⚪'),
        ('arrepentido', 'Arrepentido⭕')
    ]

    FORMA_DE_PAGO = [
        ('efectivo','Efectivo'),
        ('mercado_pago','Mercado Pago'),
        ('transferencia','Transferencia'),
        ('mixto','Mixto'),
        ('tarjeta','Tarjeta')
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historial_compras')
    productos = models.JSONField()
    total_compra = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    forma_de_pago = models.CharField(max_length=20,choices=FORMA_DE_PAGO,default='efectivo')
    pagos = models.ManyToManyField("PagoRecibidoMP", blank=True,editable=False)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True,unique=True)
    fecha_finalizado = models.DateTimeField(null=True,blank=True)
    requiere_revision = models.BooleanField(default=True)

    def check_comprobante_subido(self):
        return hasattr(self, 'comprobante')

    def check_historial(self):
        if self.estado == 'confirmado':
            return

        if self.forma_de_pago == 'transferencia':
            self.estado = 'confirmado'

        elif self.forma_de_pago == 'mercado_pago':
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

    def monto_tranferir(self) -> Decimal:
        """
        Retorna el monto a transferir según la forma de pago.
        """
        if self.forma_de_pago == 'transferencia':
            return self.total_compra
        ticket = self.tickets.first()
        return self.total_compra - ticket.monto

    def get_adicional(self) -> Decimal:
        """
        Retorna el monto adicional a pagar en caso de pago mixto o mercado pago.
        """
        if self.forma_de_pago not in ['mixto','mercadopago']:
            return 0
        
        subtotal = sum(Decimal(str(p['subtotal'])) for p in self.productos)
        total = Decimal(str(self.total_compra))
        
        return total - subtotal

    def ticket_mp(self):
        """
        Retorna el ticket de Mercado Pago asociado a la compra.
        """
        ticket = self.tickets.all()
        if ticket:
            return ticket[0]
        return None

    def mp_ticket_id_signed(self) -> "TicketDePago | None":
        """
        Retorna el ID del ticket de Mercado Pago asociado a la compra, firmado.
        """
        ticket = self.ticket_mp()
        if ticket:
            return signing.dumps(ticket.id)
        return None

    def ticket_impago(self) -> bool:
        """
        Verifica si el ticket de Mercado Pago no esta aprobado.
        """
        ticket = self.ticket_mp()
        if ticket:
            if ticket.estado != 'aprobado':
                return True
        return False
    
    def subir_comprobante(self) -> bool:
        """
        Verifica si se debe subir un comprobante de transferencia.
        Se utiliza para habilitar al usuario el boton de subir comprobante.
        Se habilita si el comprobante es rechazado y necesita volver a subirse.
        """
        if self.forma_de_pago in ['transferencia','mixto'] and not self.check_comprobante_subido():
            return True
        return False

    def verificar_arrepentimiento(self) -> bool:
        """
        Verifica si se puede solicitar el arrepentimiento.
        """
        if self.estado == 'finalizado':
            limite_arrepentimiento = self.fecha_finalizado + timedelta(days=10)
            return timezone.now() <= limite_arrepentimiento
        return False

    def manage_buttons(self):
        """
        Gestiona los botones de los productos en la vista de historial de compras.
        Retorna un diccionario con los botones habilitados o deshabilitados.
        """
        buttons = {
            'solicitar_arrepentimiento': False,
            'generar_link_pago': False,
            'subir_comprobante': False
        }

        if self.verificar_arrepentimiento():
            buttons['solicitar_arrepentimiento'] = True

        if self.ticket_impago():
            buttons['generar_link_pago'] = True

        if self.subir_comprobante():
            buttons['subir_comprobante'] = True

        return buttons
    
    def token_reseñas(self):
        """
        Cuando el Historial de Compras está finalizado, crea tokens de reseñas para cada producto comprado.
        """
        for item in self.productos:
            try:
                nombre = item['producto'].split(') ')[1]
            except:
                nombre = item['producto']
            producto = Producto.objects.filter(nombre=nombre).first()

            if ReseñaProducto.objects.filter(usuario=self.usuario.perfil,producto=producto).exists():
                return None
            TokenReseña.objects.get_or_create(
                usuario=self.usuario.perfil,
                producto=producto,
            )

    def __str__(self):
        return f"{self.merchant_order_id} - {self.estado} - {self.usuario}"

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
        ('pendiente','Pendiente')
    ]
    historial = models.ForeignKey(HistorialCompras,on_delete=models.CASCADE,related_name='tickets')
    estado = models.CharField(max_length=20,choices=ESTADOS,default='pendiente')
    monto = models.DecimalField(max_digits=10,decimal_places=2)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True,blank=True,null=True)

    def expirado(self) -> bool:
        """
        Verifica si el ticket ha expirado (1 hora desde su creación).
        """
        return timezone.now() > self.creado + timedelta(hours=1)

    def cancelar_ticket(self):
        """
        Cancela el ticket estableciendo su estado a 'rechazado'.
        """
        self.historial.estado = 'rechazado'
        self.historial.save(update_fields=['estado'])
        self.delete()

    def get_preference_data(self) -> dict:
        """
        Obtiene los datos de preferencia para la integración con Mercado Pago.
        """
        if self.expirado():
            raise ValueError("El ticket ha expirado.")
        data = self.historial.facturacion
        match = re.match(r'^(.*?)(?:\s+(\d+))?$', data.direccion.strip())
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
            'backurl_success':f"usuario/micuenta/?section=orders&compra=exitosa&idcompra={self.historial.merchant_order_id}",
            'backurl_fail':f"usuario/micuenta/?section=orders&compra=fallida&idcompra={self.historial.merchant_order_id}"
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
