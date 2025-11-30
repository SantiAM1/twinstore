from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import Venta,ComprobanteTransferencia,EstadoPedido,TicketDePago
from users.emails import mail_estado_pedido_html
from products.services import gestionar_stock_venta
from products.models import MovimientoStock
from django.utils import timezone
from core.utils import get_configuracion_tienda

@receiver(post_save,sender=EstadoPedido)
def estados_requiere_revision(sender, instance, created, **kwargs):
    if '(Servidor)' not in instance.estado:
        instance.venta.requiere_revision = False
        instance.venta.save(update_fields=["requiere_revision"])

@receiver(post_save, sender=Venta)
def manejar_actualizaciones_venta(sender: Venta, instance: Venta, created, **kwargs):
    estado_actual = instance.estado

    if estado_actual == "confirmado":
        config = get_configuracion_tienda()
        if config['modo_stock'] == 'libre':
            return

        if not MovimientoStock.objects.filter(venta=instance).exists():
            success = gestionar_stock_venta(instance)
            if not success:
                # Si falló el descuento (falta stock), revertimos a pendiente
                Venta.objects.filter(pk=instance.pk).update(
                    estado=Venta.Estado.PENDIENTE,
                    requiere_revision=True
                )
                EstadoPedido.objects.create(
                    venta=instance,
                    estado='Falta de Stock (Servidor)',
                    comentario='La venta no se pudo confirmar por falta de stock. Se generó un ajuste.'
                )
                return

    if estado_actual == "finalizado":
        if not instance.fecha_finalizado:
            instance.fecha_finalizado = timezone.now()
            instance.token_reseñas()
            instance.save(update_fields=["fecha_finalizado"])

    if estado_actual != "pendiente":
        mail_estado_pedido_html(instance, instance.facturacion.email)

@receiver(post_save, sender=ComprobanteTransferencia)
def aprobar_venta_transferencia(sender, instance: ComprobanteTransferencia, created, **kwargs):
    # * 1 Notifica al staff cuando se recibe una transferencia
    venta: Venta = instance.venta
    if created:
        venta.requiere_revision = True
        venta.save(update_fields=["requiere_revision"])
        EstadoPedido.objects.create(
            venta=venta,
            estado='Transferencia recibida (Servidor)',
            comentario='Subida por el cliente automáticamente.'
        )
        return
    # * 2 Cuando el comprobante se rechaza se envia un mail
    if instance.estado == 'rechazado':
        if instance.observaciones:
            EstadoPedido.objects.create(
                venta=venta,
                estado='Comprobante rechazado (Servidor)',
                comentario='Esperando que el cliente vuelva a enviarlo'
            )
            # mail_obs_comprobante_html(venta, instance.observaciones)
        instance.delete()

    # * 3 Si el comprobante es aprobado se verifica la venta
    if instance.estado == 'aprobado':
        venta.check_venta()

@receiver(post_save,sender=TicketDePago)
def actualizar_venta(sender, instance:TicketDePago, created, **kwargs):
    if instance.estado == "aprobado":
        instance.venta.check_venta()
