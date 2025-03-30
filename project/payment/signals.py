from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PagoRecibidoMP, HistorialCompras

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
