from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import PagoRecibidoMP, HistorialCompras,ComprobanteTransferencia,EstadoPedido
from users.emails import mail_estado_pedido_html,mail_obs_comprobante_html
from django.utils import timezone

@receiver(post_save,sender=EstadoPedido)
def estados_requiere_revision(sender, instance, created, **kwargs):
    if '(Servidor)' not in instance.estado:
        instance.historial.requiere_revision = False
        instance.historial.save(update_fields=["requiere_revision"])

@receiver(post_save, sender=HistorialCompras)
def manejar_actualizaciones_historial(sender, instance, created, **kwargs):
    # * 1 Cuando un pedido es arrepentido, quita la verificacion
    if instance.estado == "arrepentido":
        instance.requiere_revision = True
        instance.save(update_fields=["requiere_revision"])
        EstadoPedido.objects.create(
            historial=instance,
            estado='Arrepentimiento (Servidor)',
            comentario='Arrepentimiento solicitado por el cliente'
        )
    # * 2 Se crea la fecha finalizado de cuando el producto es entregado/recibido
    if instance.estado == "finalizado" and not instance.fecha_finalizado:
        instance.fecha_finalizado = timezone.now()
        instance.save(update_fields=["fecha_finalizado"])
    # * 3 Se envia un mail al actualizar el historial de compras.
    if instance.recibir_mail:
        estado_valido = (
            (instance.forma_de_pago == "transferencia" and instance.estado != "pendiente") or 
            (instance.forma_de_pago == "efectivo" and instance.estado != "confirmado") or 
            (instance.forma_de_pago == "mercado pago" and instance.estado != "pendiente")
        )
        if estado_valido:
            mail_estado_pedido_html(instance, instance.facturacion.email)

@receiver(post_save, sender=ComprobanteTransferencia)
def aprobar_historial_transferencia(sender, instance, created, **kwargs):
    # * 1 Notifica al staff cuando se recibe una transferencia
    historial = instance.historial
    if created:
        historial.requiere_revision = True
        historial.save(update_fields=["requiere_revision"])
        EstadoPedido.objects.create(
            historial=historial,
            estado='Transferencia recibida (Servidor)',
            comentario='Subida por el cliente automáticamente.'
        )
        return
    # * 2 Si el comprobante es aprobado se confirma el historial
    if instance.estado == 'aprobado':
        historial.estado = 'confirmado'
        historial.save(update_fields=["estado"])
    # * 3 Cuando el comprobante se rechaza se envia un mail
    elif instance.estado == 'rechazado':
        if instance.observaciones:
            EstadoPedido.objects.create(
                historial=historial,
                estado='Comprobante rechazado (Servidor)',
                comentario='Esperando que el cliente vuelva a enviarlo'
            )
            mail_obs_comprobante_html(historial, instance.observaciones)
        instance.delete()
