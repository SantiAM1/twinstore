from .models import DolarConfiguracion
from products.models import Producto
from django.db.models.signals import post_save
from django.dispatch import receiver
from .utils import actualizar_precio_final
from django.core.cache import cache

@receiver(post_save, sender=DolarConfiguracion)
def actualizar_precios(sender, instance, **kwargs):
    cache.delete('valor_dolar_actual')
    for producto in Producto.objects.exclude(precio_dolar__isnull=True):
        actualizar_precio_final(producto, instance.valor)
        producto.save()
