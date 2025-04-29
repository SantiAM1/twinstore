from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import PagoRecibidoMP, HistorialCompras,ComprobanteTransferencia
from users.emails import mail_estado_pedido_html,mail_obs_comprobante_html
from django.utils import timezone

@receiver(post_save, sender=HistorialCompras)
def enviar_actualizacion_compra(sender, instance, created, **kwargs):
    """
    Se envia un mail al actualizar el historial de compras.
    """
    if instance.recibir_mail and (instance.forma_de_pago == "transferencia" and instance.estado != "pendiente") or (instance.forma_de_pago == "efectivo" and instance.estado != "confirmado") or (instance.forma_de_pago == "mercado pago" and instance.estado != "pendiente"):
        mail_estado_pedido_html(instance, instance.facturacion.email)

@receiver(post_save, sender=HistorialCompras)
def fecha_finalizacion_historial(sender, instance, created, **kwargs):
    """
    Se crea la fecha de cuando el producto es entregado/recibido
    """
    if instance.estado == "finalizado" and not instance.fecha_finalizado:
        HistorialCompras.objects.filter(pk=instance.pk).update(fecha_finalizado=timezone.now())

@receiver(post_save, sender=HistorialCompras)
def estado_arrepentido_staff(sender, instance, created, **kwargs):
    """
    Cuando un pedido es arrepentido, quita la verificacion
    """
    if instance.estado == "arrepentido" and instance.estado_staff != 'no verificado':
        HistorialCompras.objects.filter(pk=instance.pk).update(estado_staff='no verificado')

@receiver(post_save, sender=ComprobanteTransferencia)
def aprobar_historial_transferencia(sender, instance, created, **kwargs):
    """
    Actualiza el estado del Historial cuando se cambia el estado del comprobante
    """
    if instance.estado == 'aprobado':
        HistorialCompras.objects.filter(pk=instance.historial.pk).update(estado='confirmado')
    elif instance.estado == 'rechazado':
        instance.delete()

@receiver(post_save, sender=ComprobanteTransferencia)
def aprobar_historial_transferencia(sender, instance, created, **kwargs):
    """
    Enviar un mail con las observaciones si el comprobante fue rechazado
    """
    mail_obs_comprobante_html(instance.historial,instance.observaciones)

@receiver(post_save, sender=ComprobanteTransferencia)
def actualizar_verificacion_transferencia(sender, instance, created, **kwargs):
    """
    Cambia el ESTADO STAFF cuando se recibe una transferencia
    """
    historial = instance.historial
    if created:
        HistorialCompras.objects.filter(pk=historial.pk).update(estado_staff='transferencia recibida')

@receiver(post_save, sender=PagoRecibidoMP)
def asociar_pago_y_actualizar_estado(sender, instance, created, **kwargs):
    """
    Cada vez que se guarda un PagoRecibidoMP, se asocia al historial correspondiente
    y se verifica si se debe cambiar el estado de la compra.
    """
    merchant_order_id = instance.merchant_order_id

    if not merchant_order_id:
        return  # No se puede asociar si no hay merchant_order_id

    try:
        historial = HistorialCompras.objects.get(merchant_order_id=merchant_order_id)

        # Asociamos el pago si aún no está
        if not historial.pagos.filter(pk=instance.pk).exists():
            historial.pagos.add(instance)
            print(f"🔗 Asociado pago {instance.payment_id} al historial {historial.id}")

        # Recalculamos estado en base a todos los pagos
        pagos = historial.pagos.all()

        if all(p.status == "approved" for p in pagos):
            historial.estado = "confirmado"
        elif any(p.status == "rejected" for p in pagos):
            historial.estado = "rechazado"
        else:
            historial.estado = "pendiente"

        historial.save()
        print(f"🔄 Estado del historial {historial.id} actualizado a: {historial.estado}")

    except HistorialCompras.DoesNotExist:
        print(f"⚠️ No se encontró historial con merchant_order_id {merchant_order_id}, se asociará más tarde.")
