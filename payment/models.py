from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import string
import secrets
import re
from django.core import signing
from products.models import TokenReseña, Producto,ReseñaProducto,ColorProducto

class Venta(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente🟡"
        CONFIRMADO = "confirmado", "Confirmado🟢"
        RECHAZADO = "rechazado", "Rechazado🔴"
        FINALIZADO = "finalizado", "Finalizado⚪"
        ARREPENTIDO = "arrepentido", "Arrepentido⭕"
        LISTO_PARA_RETIRAR = "listo para retirar", "Listo para retirar✔️"
        ENVIADO = "enviado", "Enviado🟣"

    class FormaPago(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        MP = "mercado_pago", "Mercado Pago"
        TRANSFERENCIA = "transferencia", "Transferencia"
        MIXTO = "mixto", "Mixto"
        TARJETA = "tarjeta", "Tarjeta"

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ventas')
    total_compra = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    forma_de_pago = models.CharField(max_length=20,choices=FormaPago.choices,default=FormaPago.EFECTIVO)
    pagos = models.ManyToManyField("PagoRecibidoMP", blank=True,editable=False)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True,unique=True)
    fecha_finalizado = models.DateTimeField(null=True,blank=True)
    requiere_revision = models.BooleanField(default=True)

    def detalle_productos(self) -> list[dict[str, str | Decimal | int]]:
        """
        Retorna una lista con los detalles de los productos en la venta.
        """
        detalle = []
        for venta in self.detalles.all():
            detalle.append({
                'producto': venta.producto.nombre if not venta.color else f"({venta.color.nombre}) {venta.producto.nombre}",
                'cantidad': venta.cantidad,
                'precio_unitario': venta.precio_unitario,
                'subtotal': venta.subtotal,
                'imagen': venta.imagen_url
            })
        return detalle

    def check_comprobante_subido(self) -> bool:
        """
        Verifica si se ha subido un comprobante de transferencia.
        """
        return hasattr(self, 'comprobante')

    def check_venta(self) -> None:
        """
        Verifica y actualiza el estado de la venta según la forma de pago y el estado de los tickets asociados.
        """
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

    def ticket_mp(self) -> "TicketDePago | None":
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

    def manage_buttons(self) -> dict[str, bool]:
        """
        Gestiona los botones de los productos en la vista de la Venta.
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

    def token_reseñas(self) -> None:
        """
        Cuando la Venta está finalizada, crea tokens de reseñas para cada producto comprado.
        """
        for detalle in self.detalles.all():
            producto = detalle.producto
            if ReseñaProducto.objects.filter(usuario=self.usuario.perfil,producto=producto).exists():
                return None
            TokenReseña.objects.get_or_create(
                usuario=self.usuario.perfil,
                producto=producto,
            )

    def __str__(self):
        return f"{self.merchant_order_id} - {self.estado} - {self.usuario}"

class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    color = models.ForeignKey(ColorProducto, on_delete=models.PROTECT, blank=True, null=True)
    imagen_url = models.URLField(blank=True, null=True)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    def get_range(self):
        return range(self.cantidad)

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} - {self.venta.merchant_order_id}"

class EstadoPedido(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='estados')
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
    class Estado(models.TextChoices):
        APROBADO = 'aprobado', 'Aprobado'
        RECHAZADO = 'rechazado', 'Rechazado'
        PENDIENTE = 'pendiente', 'Pendiente'

    venta = models.ForeignKey(Venta,on_delete=models.CASCADE,related_name='tickets')
    estado = models.CharField(max_length=20,choices=Estado.choices,default=Estado.PENDIENTE)
    monto = models.DecimalField(max_digits=10,decimal_places=2)
    merchant_order_id = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True,blank=True,null=True)

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
            'email':data.email,
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
        return f"Monto a depositar: {self.monto}"

class ComprobanteTransferencia(models.Model):
    ESTADOS = [
        ('aprobado','Aprobado'),
        ('rechazado','Rechazado'),
        ('no verificado','No verificado')
    ]

    venta = models.OneToOneField("Venta", on_delete=models.CASCADE, related_name="comprobante")
    file = models.FileField(upload_to="comprobantes/")
    fecha_subida = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20,choices=ESTADOS,default='no verificado')
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Comprobante de {self.venta.merchant_order_id}"

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
