from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Venta,EstadoPedido,DatosFacturacion
from users.emails import mail_estado_pedido_html,mail_buy_send_html
from products.services import gestionar_stock_venta
from products.models import MovimientoStock
from django.utils import timezone
from core.utils import get_configuracion_tienda

@receiver(post_save, sender=DatosFacturacion)
def enviar_mail_compra(sender, instance:DatosFacturacion, **kwargs):
    mail_buy_send_html(instance.venta)

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
        mail_estado_pedido_html(instance, instance.usuario.email)